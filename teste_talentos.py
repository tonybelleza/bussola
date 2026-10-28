"""
Testes do banco de talentos (talentos.py): linhas do resumo da ligação a partir
dos fatos, dados de voz da lista (filtros e comparação), lembretes "Lembrar em"
no quadro "Ligar hoje" (no dia e depois, nunca antes) e isolamento entre empresas.

Uso:  python3 teste_talentos.py

Banco isolado numa pasta temporária. Nada sai da máquina.
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="talentos-teste-")
for arquivo in ("server.py", "voz.py", "empresas.py", "mensagens.py", "erros_i18n.py", "entrada.py", "agenda.py",
                "talentos.py", "seguranca.py", "planos.py", "indicacoes.py",
                "onboarding.py", "formularios.py"):
    if os.path.exists(os.path.join(AQUI, arquivo)):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import entrada  # noqa: E402
import server  # noqa: E402
import talentos  # noqa: E402
import voz  # noqa: E402

server.Handler.log_message = lambda *a: None

FATOS_BONS = {
    "outcome": "QUALIFIED", "license": "yes", "own_car": "yes", "city": "New Britain", "weekdays_available": 5,
    "experience_level": "two_plus_years", "works_alone": "yes", "has_smartphone": True,
    "start_timeframe": "within_1_week", "pets": "comfortable", "standards": "accepted",
}


def codigos(itens):
    return [i["c"] for i in itens]


class TestLinhasDoResumo(unittest.TestCase):
    def info(self, fatos, tier="STRONG", outcome="QUALIFIED", faixa="25mi", motivos=None, **extra):
        d = {"fatos": fatos, "tier": tier, "outcome": outcome, "faixa": faixa, "motivos": motivos or [],
             "status": "concluida", "encerrado": False}
        d.update(extra)
        return d

    def test_candidata_forte_com_testes_marca_entrevista(self):
        r = talentos.linhas_resumo(self.info(FATOS_BONS), testes_ok=True)
        self.assertEqual(codigos(r["fortes"]), ["dias", "experiencia", "perto", "carro_carteira", "sozinho", "inicio"])
        self.assertEqual(r["fortes"][2], {"c": "perto", "raio": 25, "cidade": "New Britain"})
        self.assertEqual(r["alertas"], [])
        self.assertEqual(r["proximo"]["c"], "agendar_entrevista")

    def test_forte_sem_testes_aguarda(self):
        self.assertEqual(talentos.linhas_resumo(self.info(FATOS_BONS))["proximo"]["c"], "aguardar_testes")
        self.assertEqual(talentos.linhas_resumo(self.info(FATOS_BONS, tier="GOOD"))["proximo"]["c"], "aguardar_testes")

    def test_alertas_tipicos_e_revisao(self):
        fatos = dict(FATOS_BONS, license="unclear", own_car="no", weekdays_available=2, has_smartphone=False,
                     standards="hesitant_or_objects", works_alone="hesitant", city="Boston")
        motivos = ["outcome_corrected", "license_unclear", "outside_area", "missing:pets", "missing:start_date"]
        r = talentos.linhas_resumo(self.info(fatos, tier="REVIEW", outcome="NEEDS_REVIEW", faixa="outside", motivos=motivos))
        a = codigos(r["alertas"])
        for c in ("poucos_dias", "fora_area", "sozinho_hesita", "carteira_incerto", "carro_nao", "padroes",
                  "sem_smartphone", "desligou", "faltam"):
            self.assertIn(c, a)
        self.assertEqual(next(i for i in r["alertas"] if i["c"] == "faltam")["n"], 2)
        self.assertNotIn("carro_carteira", codigos(r["fortes"]))
        self.assertEqual(r["proximo"]["c"], "ouvir_ligacao")

    def test_low_e_encerrado_e_etapas(self):
        self.assertEqual(talentos.linhas_resumo(self.info(FATOS_BONS, tier="LOW"))["proximo"]["c"], "considerar_reprovar")
        sem_gate = talentos.linhas_resumo(self.info(dict(FATOS_BONS, license="no"), tier="", outcome="NOT_QUALIFIED", faixa=""))
        self.assertEqual(sem_gate["proximo"]["c"], "considerar_reprovar")
        self.assertIn("carteira_nao", codigos(sem_gate["alertas"]))
        fechado = talentos.linhas_resumo(self.info({}, tier="", outcome="WRONG_NUMBER", faixa="", encerrado=True))
        self.assertEqual((fechado["proximo"]["c"], fechado["alertas"]), ("encerrado", []))
        self.assertEqual(talentos.linhas_resumo(self.info(FATOS_BONS), True, etapa_avancada=True)["proximo"]["c"], "acompanhar")
        self.assertEqual(talentos.linhas_resumo(self.info(FATOS_BONS), True, entrevista_marcada=True)["proximo"]["c"],
                         "entrevista_marcada")

    def test_sem_resposta_nao_inventa_alertas(self):
        r = talentos.linhas_resumo(self.info({"outcome": "VOICEMAIL"}, tier="", outcome="VOICEMAIL", faixa="",
                                             status="para_ligar"))
        self.assertEqual((r["fortes"], r["alertas"], r["proximo"]["c"]), ([], [], "aguardar_ligacao"))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        self.conn = c = server.db()
        self.ea, _ = empresas.criar_empresa(c, "BHS CT")
        self.eb, _ = empresas.criar_empresa(c, "Outra Empresa")
        c.execute("UPDATE empresas SET modulos='[\"voz\"]' WHERE id IN (?,?)", (self.ea, self.eb))
        self.cargo = c.execute("INSERT INTO cargos (nome, voz_ativa, empresa_id) VALUES ('Cleaning Tech', 1, ?)",
                               (self.ea,)).lastrowid
        self.vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'House Cleaning Technician', 'aberta', ?)",
                              (self.cargo, self.ea)).lastrowid
        cargo_b = c.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Outro', ?)", (self.eb,)).lastrowid
        self.vaga_b = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Outra vaga', 'aberta', ?)",
                                (cargo_b, self.eb)).lastrowid
        self.gestores = {}
        for login, empresa in (("tony", self.ea), ("intruso", self.eb)):
            gid = c.execute("INSERT INTO gestores (nome, login, senha, is_admin, aprovado, empresa_id) VALUES (?,?,?,1,1,?)",
                            (login, login, "x", empresa)).lastrowid
            c.execute("INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)", ("sess-" + login, gid))
            self.gestores[login] = gid
        c.commit()

    def tearDown(self):
        self.conn.close()

    def g(self, login="tony"):
        return self.conn.execute("SELECT g.*, e.modulos AS empresa_modulos FROM gestores g JOIN empresas e ON e.id=g.empresa_id WHERE g.id=?",
                                 (self.gestores[login],)).fetchone()

    def candidato(self, nome, empresa=None, vaga=None, fatos=None, tier="", score=None, status="", outcome="",
                  etapa="inscrito", faixa="25mi", na_chamada=True):
        c = self.conn
        empresa = empresa or self.ea
        cid = c.execute("INSERT INTO candidatos (token, nome, email, telefone, local, empresa_id) VALUES (?,?,?,?,?,?)",
                        ("tok-" + nome, nome, nome.lower() + "@x.com", "+18605550100", "Hartford, CT", empresa)).lastrowid
        resultado = json.dumps({"fatos": fatos or {}, "faixa": faixa, "motivos": [], "tier": tier, "score": score}) if tier else ""
        caid = c.execute("INSERT INTO candidaturas (candidato_id, vaga_id, etapa, voz_status, voz_tier, voz_score, voz_outcome,"
                         " voz_resultado) VALUES (?,?,?,?,?,?,?,?)",
                         (cid, vaga or self.vaga, etapa, status, tier, score, outcome, resultado)).lastrowid
        if fatos and na_chamada:
            c.execute("INSERT INTO voz_chamadas (candidatura_id, candidato_id, conversation_id, status, fatos) VALUES (?,?,?,?,?)",
                      (caid, cid, "conv-" + nome, "concluida", json.dumps(fatos)))
        c.commit()
        return cid

    def req(self, metodo, caminho, dados=None, gestor="tony", idioma=None):
        cab = {"Content-Type": "application/json", "X-Gestor-Token": "sess-" + gestor}
        if idioma:
            cab["X-Idioma"] = idioma
        corpo = json.dumps(dados).encode() if dados is not None else None
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=cab)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def hoje(self, empresa=None):
        cfg = voz.config_empresa(self.conn, empresa or self.ea)
        return datetime.now(voz._zona(cfg)).date()


class TestEndpoints(Base):
    def test_resumo_da_ficha(self):
        cid = self.candidato("Maria", fatos=FATOS_BONS, tier="STRONG", score=90, status="concluida", outcome="QUALIFIED")
        st, d = self.req("GET", "/api/gestor/talentos/resumo/%d" % cid)
        self.assertEqual(st, 200, d)
        self.assertTrue(d["tem_voz"])
        self.assertEqual((d["tier"], d["score"], d["outcome"], d["testes_ok"]), ("STRONG", 90, "QUALIFIED", False))
        self.assertEqual(d["linhas"]["proximo"]["c"], "aguardar_testes")
        self.assertIn("carro_carteira", codigos(d["linhas"]["fortes"]))
        # com DISC e B.A.S.E. feitos: marcar entrevista
        for tipo in ("disc", "base"):
            self.conn.execute("INSERT INTO resultados_teste (candidato_id, tipo, payload) VALUES (?,?,?)", (cid, tipo, "{}"))
        self.conn.commit()
        self.assertEqual(self.req("GET", "/api/gestor/talentos/resumo/%d" % cid)[1]["linhas"]["proximo"]["c"], "agendar_entrevista")
        # sem triagem: só o lembrete
        sem = self.candidato("Sem Voz")
        st, d = self.req("GET", "/api/gestor/talentos/resumo/%d" % sem)
        self.assertEqual((st, d["tem_voz"], d["lembrete"]), (200, False, None))
        self.assertNotIn("linhas", d)

    def test_fatos_da_ultima_ligacao_valem_mais(self):
        # resultado pontuado antigo + ligação mais nova sem pontuação (carro "no"): usa os fatos novos
        cid = self.candidato("Ana", fatos=FATOS_BONS, tier="GOOD", score=60, status="concluida", na_chamada=False)
        ca = self.conn.execute("SELECT id FROM candidaturas WHERE candidato_id=?", (cid,)).fetchone()[0]
        self.conn.execute("INSERT INTO voz_chamadas (candidatura_id, candidato_id, conversation_id, status, fatos) VALUES (?,?,?,?,?)",
                          (ca, cid, "conv-nova", "concluida", json.dumps(dict(FATOS_BONS, own_car="no"))))
        self.conn.commit()
        self.assertEqual(talentos.voz_do_candidato(self.conn, cid)["fatos"]["own_car"], "no")

    def test_dados_da_lista_para_filtros(self):
        forte = self.candidato("Forte", fatos=FATOS_BONS, tier="STRONG", score=88, status="concluida", outcome="QUALIFIED")
        incerto = self.candidato("Incerto", fatos=dict(FATOS_BONS, license="unclear", own_car=None, city="Bristol"),
                                 tier="REVIEW", score=45, status="revisar", outcome="NEEDS_REVIEW")
        fechado = self.candidato("Fechado", status="numero_errado", outcome="WRONG_NUMBER")
        nada = self.candidato("Nada")
        st, d = self.req("GET", "/api/gestor/talentos/voz")
        self.assertEqual(st, 200)
        v = d["candidatos"]
        self.assertEqual(set(v), {str(forte), str(incerto), str(fechado), str(nada)})
        f = v[str(forte)]
        self.assertEqual((f["tier"], f["score"], f["city"], f["own_car"], f["license"], f["weekdays_available"],
                          f["experience_level"], f["encerrado"]),
                         ("STRONG", 88, "New Britain", "yes", "yes", 5, "two_plus_years", False))
        self.assertEqual((v[str(incerto)]["tier"], v[str(incerto)]["license"], v[str(incerto)]["own_car"], v[str(incerto)]["city"]),
                         ("REVIEW", "unclear", None, "Bristol"))
        self.assertEqual((v[str(fechado)]["tier"], v[str(fechado)]["encerrado"]), ("", True))
        self.assertEqual((v[str(nada)]["tier"], v[str(nada)]["encerrado"], v[str(nada)]["city"]), ("", False, None))

    def test_lembrete_salvar_limpar_e_linha_do_tempo(self):
        cid = self.candidato("Lia")
        st, d = self.req("POST", "/api/gestor/talentos/lembrete/%d" % cid, {"data": "2026-13-01"}, idioma="en")
        self.assertEqual((st, d["erro"]), (400, "Invalid reminder date (use YYYY-MM-DD)"))
        st, d = self.req("POST", "/api/gestor/talentos/lembrete/%d" % cid, {"data": "2026-11-03", "nota": "ligar depois das 17h"})
        self.assertEqual(st, 200, d)
        self.assertEqual((d["lembrete"]["data"], d["lembrete"]["nota"]), ("2026-11-03", "ligar depois das 17h"))
        # atualiza no lugar (um lembrete por candidato)
        self.req("POST", "/api/gestor/talentos/lembrete/%d" % cid, {"data": "2026-11-04"})
        self.assertEqual(self.conn.execute("SELECT COUNT(*), MAX(data) FROM lembretes_talentos").fetchone()[:], (1, "2026-11-04"))
        eventos = [r["texto"] for r in self.conn.execute("SELECT texto FROM eventos WHERE candidato_id=? AND tipo='lembrete'", (cid,))]
        self.assertIn("Lembrete para 2026-11-03: ligar depois das 17h", eventos)
        self.assertEqual(self.req("GET", "/api/gestor/talentos/resumo/%d" % cid)[1]["lembrete"]["data"], "2026-11-04")
        self.assertEqual(self.req("GET", "/api/gestor/talentos/voz")[1]["candidatos"][str(cid)]["lembrete"]["data"], "2026-11-04")
        st, d = self.req("DELETE", "/api/gestor/talentos/lembrete/%d" % cid)
        self.assertEqual((st, d["lembrete"]), (200, None))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM lembretes_talentos").fetchone()[0], 0)

    def test_isolamento_entre_empresas(self):
        cid = self.candidato("Maria", fatos=FATOS_BONS, tier="STRONG", score=90, status="concluida")
        outro = self.candidato("Bruno", empresa=self.eb, vaga=self.vaga_b, fatos=FATOS_BONS, tier="GOOD", score=60)
        for metodo, caminho, dados in (("GET", "/api/gestor/talentos/resumo/%d" % cid, None),
                                       ("POST", "/api/gestor/talentos/lembrete/%d" % cid, {"data": "2026-11-03"}),
                                       ("DELETE", "/api/gestor/talentos/lembrete/%d" % cid, None)):
            self.assertEqual(self.req(metodo, caminho, dados, gestor="intruso")[0], 404)
        self.assertEqual(set(self.req("GET", "/api/gestor/talentos/voz", gestor="intruso")[1]["candidatos"]), {str(outro)})
        self.assertEqual(set(self.req("GET", "/api/gestor/talentos/voz")[1]["candidatos"]), {str(cid)})
        # lembrete da empresa A não aparece no quadro da empresa B
        self.req("POST", "/api/gestor/talentos/lembrete/%d" % cid, {"data": self.hoje().isoformat()})
        p = entrada.prioridades(self.conn, self.g("intruso"))
        self.assertEqual(p["ligar_hoje"]["itens"], [])
        self.assertEqual(self.req("GET", "/api/gestor/talentos/voz")[0], 200)
        # sem sessão
        r = urllib.request.Request(self.base + "/api/gestor/talentos/voz")
        with self.assertRaises(urllib.error.HTTPError) as erro:
            urllib.request.urlopen(r)
        self.assertEqual(erro.exception.code, 401)


class TestLembretesNoQuadro(Base):
    def nomes(self):
        return [i["nome"] for i in entrada.prioridades(self.conn, self.g())["ligar_hoje"]["itens"]]

    def test_aparece_no_dia_e_depois_nunca_antes(self):
        hoje = self.hoje()
        a = self.candidato("Hoje", etapa="avaliacoes")
        b = self.candidato("Amanha")
        c = self.candidato("Ontem", etapa="contratado")
        for cid, dia in ((a, hoje), (b, hoje + timedelta(days=1)), (c, hoje - timedelta(days=3))):
            talentos.salvar_lembrete(self.conn, self.g(), cid, dia.isoformat(), "nota " + str(cid))
        itens = entrada.prioridades(self.conn, self.g())["ligar_hoje"]["itens"]
        self.assertEqual([i["nome"] for i in itens], ["Ontem", "Hoje"])
        hoje_item = next(i for i in itens if i["nome"] == "Hoje")
        self.assertTrue(hoje_item["lembrete"])
        self.assertEqual((hoje_item["lembrete_nota"], hoje_item["lembrete_data"], hoje_item["vaga"]),
                         ("nota %d" % a, hoje.isoformat(), "House Cleaning Technician"))

    def test_nao_duplica_quem_ja_esta_para_ligar_e_mantem_os_outros_grupos(self):
        cid = self.candidato("Fila", status="para_ligar")
        self.candidato("Outro", status="para_ligar")
        self.assertEqual(sorted(self.nomes()), ["Fila", "Outro"])
        talentos.salvar_lembrete(self.conn, self.g(), cid, self.hoje().isoformat(), "")
        itens = entrada.prioridades(self.conn, self.g())["ligar_hoje"]
        self.assertEqual(itens["total"], 2)
        self.assertEqual(itens["itens"][0]["nome"], "Fila")
        self.assertTrue(itens["itens"][0]["lembrete"])
        self.assertEqual(itens["itens"][0]["status"], "para_ligar")
        self.assertNotIn("lembrete", itens["itens"][1])

    def test_anonimizado_nao_aparece(self):
        cid = self.candidato("Anon")
        talentos.salvar_lembrete(self.conn, self.g(), cid, self.hoje().isoformat(), "")
        self.conn.execute("UPDATE candidatos SET anonimizado=1 WHERE id=?", (cid,))
        self.conn.commit()
        self.assertEqual(self.nomes(), [])


class TestSemTravessoes(unittest.TestCase):
    def test_arquivos_sem_travessao(self):
        for arq in ("talentos.py", "teste_talentos.py", "public/js/gestor-talentos.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                texto = f.read()
            self.assertNotIn(chr(0x2014), texto, arq)
            self.assertNotIn(chr(0x2013), texto, arq)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
