"""
Testes do relatório de contratação (relatorios.py).

Uso:  python3 teste_relatorios.py
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
PASTA = tempfile.mkdtemp(prefix="rel-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import relatorios  # noqa: E402
import server  # noqa: E402

HOJE = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)


def quando(dias, horas=0):
    """Data SQL (UTC) de 'dias' atrás, ao meio-dia, mais 'horas'."""
    return (HOJE - timedelta(days=dias) + timedelta(hours=horas)).strftime("%Y-%m-%d %H:%M:%S")


FALOU = json.dumps([{"papel": "agent", "texto": "Hola"}, {"papel": "user", "texto": "Sí"}])


class TestRelatorios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        conn = server.db()
        cls.ea, _ = empresas.criar_empresa(conn, "Empresa A")
        cls.eb, _ = empresas.criar_empresa(conn, "Empresa B")
        for login, admin, eid, local in (("admin.a", 1, cls.ea, ""), ("norte.a", 0, cls.ea, "Norte"),
                                         ("admin.b", 1, cls.eb, "")):
            conn.execute("INSERT INTO gestores (login, senha, nome, is_admin, aprovado, empresa_id, local)"
                         " VALUES (?,?,?,?,1,?,?)",
                         (login, server.hash_senha("senha-123"), login.title(), admin, eid, local))
        cls.c1 = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Limpeza', ?)", (cls.ea,)).lastrowid
        cls.c2 = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Motorista', ?)", (cls.ea,)).lastrowid
        cb = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Outro', ?)", (cls.eb,)).lastrowid
        cls.v1 = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Faxina', 'aberta', ?)",
                              (cls.c1, cls.ea)).lastrowid
        cls.v2 = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Entregas', 'aberta', ?)",
                              (cls.c2, cls.ea)).lastrowid
        cls.vb = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Vaga B', 'aberta', ?)",
                              (cb, cls.eb)).lastrowid

        def cand(nome, tags, empresa, local=""):
            return conn.execute(
                "INSERT INTO candidatos (token, nome, email, empresa_id, tags, local) VALUES (?,?,?,?,?,?)",
                ("tk-" + nome, nome, nome + "@x.com", empresa, json.dumps(tags), local)).lastrowid

        def candidatura(cid, vaga, criado, etapa="inscrito", atualizado=None, **extra):
            cols = ["candidato_id", "vaga_id", "etapa", "criado_em", "atualizado_em"] + list(extra)
            vals = [cid, vaga, etapa, criado, atualizado or criado] + list(extra.values())
            return conn.execute("INSERT INTO candidaturas (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))),
                                vals).lastrowid

        def chamada(ca, cid, iniciada, duracao, falou=True):
            conn.execute("INSERT INTO voz_chamadas (candidatura_id, candidato_id, conversation_id, status, iniciada_em,"
                         " duracao, transcricao) VALUES (?,?,?,?,?,?,?)",
                         (ca, cid, "conv-%d-%s" % (ca, iniciada), "concluida", iniciada, duracao,
                          FALOU if falou else "[]"))

        def evento(cid, texto, criado):
            conn.execute("INSERT INTO eventos (candidato_id, tipo, texto, criado_em) VALUES (?, 'etapa', ?, ?)",
                         (cid, texto, criado))

        # 1. Indeed, STRONG, testes completos, entrevista realizada, contratado em 10 dias
        k1 = cand("ana", ["indeed"], cls.ea)
        ca1 = candidatura(k1, cls.v1, quando(20), "contratado", quando(10), voz_tier="STRONG",
                          voz_outcome="QUALIFIED", voz_status="concluida")
        chamada(ca1, k1, quando(20, 2), 125)
        for tipo in ("disc", "base"):
            conn.execute("INSERT INTO resultados_teste (candidato_id, tipo, payload) VALUES (?,?,'{}')", (k1, tipo))
        conn.execute("INSERT INTO entrevistas_agenda (empresa_id, candidato_id, candidatura_id, inicio_utc, fim_utc,"
                     " status, token) VALUES (?,?,?,?,?, 'realizada', 'ag1')",
                     (cls.ea, k1, ca1, (HOJE - timedelta(days=17) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      (HOJE - timedelta(days=17) + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")))
        evento(k1, "Vaga Faxina: movido para Avaliações (triagem por voz)", quando(20, 3))
        evento(k1, "Vaga Faxina: movido para Proposta", quando(12))
        evento(k1, "Vaga Faxina: movido para Contratado", quando(10))
        # 2. Facebook, GOOD, entrevista (pelo evento), reprovado manualmente
        k2 = cand("bia", ["facebook"], cls.ea)
        ca2 = candidatura(k2, cls.v1, quando(15), "reprovado", quando(11), voz_tier="GOOD",
                          voz_outcome="QUALIFIED", voz_status="concluida", motivo_reprovacao="Salário")
        chamada(ca2, k2, quando(15, 4), 60)
        evento(k2, "Vaga Faxina: movido para Entrevista", quando(13, 4))
        evento(k2, "Vaga Faxina: movido para Reprovado (Salário)", quando(11))
        # 3. CSV, ligação sem resposta, tentativas esgotadas
        k3 = cand("caio", ["csv"], cls.ea)
        ca3 = candidatura(k3, cls.v1, quando(10), voz_status="correio_voz")
        chamada(ca3, k3, quando(10, 6), 0, falou=False)
        # 4. Indicação (sem tag), número errado
        k4 = cand("davi", [], cls.ea)
        ca4 = candidatura(k4, cls.v2, quando(8), "reprovado", voz_outcome="WRONG_NUMBER", voz_status="numero_errado",
                          motivo_reprovacao="Número errado (triagem por voz)")
        chamada(ca4, k4, quando(8, 2), 30)
        ind = conn.execute("INSERT INTO indicadores (empresa_id, candidato_id, codigo) VALUES (?,?,'abc')",
                           (cls.ea, k1)).lastrowid
        conn.execute("INSERT INTO indicacoes (empresa_id, indicador_id, indicado_id) VALUES (?,?,?)", (cls.ea, ind, k4))
        # 5. Site (sem tags), contratado direto pela etapa, 21 dias
        k5 = cand("eva", [], cls.ea)
        candidatura(k5, cls.v2, quando(25), "contratado", quando(4))
        # 6. Notion, fora dos últimos 30 dias, contratado há 80 dias
        k6 = cand("fabio", ["notion"], cls.ea)
        candidatura(k6, cls.v1, quando(100), "contratado", quando(80))
        # 7. Empresa B: nunca aparece para a empresa A
        k7 = cand("gil", ["indeed"], cls.eb)
        ca7 = candidatura(k7, cls.vb, quando(3), "contratado", quando(1))
        chamada(ca7, k7, quando(3, 1), 600)
        # 8. Unidade Norte (só ele aparece para o gestor da unidade Norte)
        k8 = cand("hugo", ["indeed"], cls.ea, "Norte")
        candidatura(k8, cls.v1, quando(5))
        conn.commit()
        conn.close()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def req(self, caminho, cab=None):
        r = urllib.request.Request(self.base + caminho, headers=cab or {})
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def token(self, login):
        corpo = json.dumps({"login": login, "senha": "senha-123"}).encode()
        r = urllib.request.Request(self.base + "/api/gestor/login", data=corpo, method="POST",
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r) as resp:
            return {"X-Gestor-Token": json.loads(resp.read())["token"]}

    def rel(self, login="admin.a", qs=""):
        s, d = self.req("/api/gestor/relatorios/contratacao" + qs, self.token(login))
        self.assertEqual(s, 200, d)
        return d

    # ------------------------------------------------------------ funil
    def test_funil(self):
        d = self.rel()
        funil = {f["etapa"]: f for f in d["funil"]}
        self.assertEqual([f["etapa"] for f in d["funil"]], list(relatorios.ETAPAS_FUNIL))
        esperado = {"inscritos": 6, "triados": 3, "qualificados": 2, "testes": 1, "entrevista_marcada": 3,
                    "entrevista_realizada": 2, "proposta": 2, "contratados": 2}
        self.assertEqual({k: funil[k]["n"] for k in esperado}, esperado)
        self.assertIsNone(funil["inscritos"]["conversao_pct"])
        self.assertEqual(funil["triados"]["conversao_pct"], 50.0)
        self.assertEqual(funil["qualificados"]["conversao_pct"], 66.7)
        self.assertEqual(funil["testes"]["conversao_pct"], 50.0)
        # conversão entre vizinhas conta só quem passou pela anterior: nunca acima de 100%
        self.assertEqual(funil["entrevista_marcada"]["conversao_pct"], 100.0)
        self.assertEqual(funil["entrevista_realizada"]["conversao_pct"], 66.7)
        self.assertEqual(funil["proposta"]["conversao_pct"], 100.0)
        self.assertEqual(funil["contratados"]["conversao_pct"], 100.0)
        self.assertTrue(all(f["conversao_pct"] is None or f["conversao_pct"] <= 100 for f in d["funil"]))
        self.assertEqual(funil["contratados"]["do_total_pct"], 33.3)
        self.assertEqual(d["reprovados"], 2)
        k = d["kpis"]
        self.assertEqual((k["inscritos"], k["qualificados"], k["contratados"]), (6, 2, 2))
        self.assertEqual(k["taxa_contratacao_pct"], 33.3)

    def test_fontes(self):
        d = self.rel()
        fontes = {f["fonte"]: f for f in d["fontes"]}
        self.assertEqual(set(fontes), {"indeed", "facebook", "csv", "indicacao", "site"})
        self.assertEqual((fontes["indeed"]["inscritos"], fontes["indeed"]["qualificados"],
                          fontes["indeed"]["contratados"], fontes["indeed"]["conversao_pct"]), (2, 1, 1, 50.0))
        self.assertEqual((fontes["facebook"]["qualificados"], fontes["facebook"]["contratados"]), (1, 0))
        self.assertEqual(fontes["indicacao"]["inscritos"], 1)
        self.assertEqual((fontes["site"]["contratados"], fontes["site"]["conversao_pct"]), (1, 100.0))
        self.assertEqual(sum(f["inscritos"] for f in d["fontes"]), 6)
        self.assertEqual(relatorios.fonte_de(["notion", "indeed"]), "notion")
        self.assertEqual(relatorios.fonte_de(["indeed"], indicado=True), "indicacao")
        self.assertEqual(relatorios.fonte_de(["referral"]), "indicacao")
        self.assertEqual(relatorios.fonte_de(["java"]), "site")

    def test_tempos(self):
        t = self.rel()["tempos"]
        self.assertEqual(t["contratacao_dias"], {"n": 2, "mediana": 15.5, "media": 15.5})
        self.assertEqual(t["primeira_ligacao_horas"], {"n": 4, "mediana": 3.0, "media": 3.5})
        self.assertEqual(t["ligacao_entrevista_dias"], {"n": 2, "mediana": 2.5, "media": 2.5})
        self.assertEqual(relatorios.mediana([5, 1, 3]), 3.0)
        self.assertIsNone(relatorios.mediana([]))

    def test_custo(self):
        d = self.rel()
        c = d["custo_voz"]
        self.assertEqual((c["ligacoes"], c["minutos"]), (4, 5))  # 125s=3, 60s=1, 0s=0, 30s=1
        self.assertEqual((c["custo_min_voz"], c["custo_min_tel"]), (0.09, 0.014))
        self.assertEqual(c["custo_total"], 0.52)
        self.assertEqual((c["por_qualificado"], c["por_contratacao"]), (0.26, 0.26))
        conn = server.db()
        try:
            server.config_set(conn, "planos_premissas", json.dumps({"custo_min_voz": 0.1, "custo_min_tel": 0.02}))
            conn.commit()
            c = relatorios.relatorio(conn, conn.execute("SELECT * FROM gestores WHERE login='admin.a'").fetchone(),
                                     (HOJE - timedelta(days=29)).date(), HOJE.date())["custo_voz"]
            self.assertEqual((c["custo_minuto"], c["custo_total"], c["por_contratacao"]), (0.12, 0.6, 0.3))
        finally:
            conn.execute("DELETE FROM config WHERE chave='planos_premissas'")
            conn.commit()
            conn.close()
        self.assertEqual(relatorios.minutos_cobrados(61), 2)
        self.assertEqual(relatorios.minutos_cobrados(None), 0)

    def test_tabelas_tendencia_encerramentos(self):
        d = self.rel()
        vagas = {v["titulo"]: v for v in d["por_vaga"]}
        self.assertEqual((vagas["Faxina"]["inscritos"], vagas["Faxina"]["contratados"], vagas["Faxina"]["cargo"]),
                         (4, 1, "Limpeza"))
        self.assertEqual((vagas["Entregas"]["inscritos"], vagas["Entregas"]["mediana_dias_contratacao"]), (2, 21.0))
        self.assertEqual(vagas["Faxina"]["custo_voz"], 0.42)  # 4 minutos
        self.assertEqual({c["nome"]: c["inscritos"] for c in d["por_cargo"]}, {"Limpeza": 4, "Motorista": 2})
        self.assertEqual(sum(w["inscritos"] for w in d["tendencia"]), 6)
        self.assertEqual(sum(w["contratados"] for w in d["tendencia"]), 2)
        self.assertTrue(all(w["semana"].count("-W") == 1 for w in d["tendencia"]))
        e = d["encerramentos"]
        self.assertEqual((e["numero_errado"], e["sem_resposta"], e["reprovacao_manual"], e["sem_interesse"]),
                         (1, 1, 1, 0))
        self.assertEqual(d["motivos_manuais"], [{"motivo": "Salário", "n": 1}])
        self.assertEqual({v["titulo"] for v in d["opcoes"]["vagas"]}, {"Faxina", "Entregas"})

    def test_filtros_e_periodo(self):
        self.assertEqual(self.rel(qs="?vaga_id=%d" % self.v2)["kpis"]["inscritos"], 2)
        self.assertEqual(self.rel(qs="?cargo_id=%d" % self.c1)["kpis"]["inscritos"], 4)
        de = (HOJE - timedelta(days=120)).strftime("%Y-%m-%d")
        d = self.rel(qs="?de=%s&ate=%s" % (de, HOJE.strftime("%Y-%m-%d")))
        self.assertEqual(d["kpis"]["inscritos"], 7)
        self.assertIn("notion", {f["fonte"] for f in d["fontes"]})
        self.assertEqual(d["periodo"]["de"], de)
        cab = self.token("admin.a")
        s, r = self.req("/api/gestor/relatorios/contratacao?de=2026-13-01", dict(cab, **{"X-Idioma": "en"}))
        self.assertEqual((s, r["erro"]), (400, "Invalid period"))
        s, _ = self.req("/api/gestor/relatorios/contratacao?de=2026-05-02&ate=2026-05-01", cab)
        self.assertEqual(s, 400)
        s, r = self.req("/api/gestor/relatorios/contratacao?vaga_id=abc", dict(cab, **{"X-Idioma": "es"}))
        self.assertEqual((s, r["erro"]), (400, "Filtro inválido"))
        self.assertEqual(self.req("/api/gestor/relatorios/contratacao?de=2020-01-01&ate=2026-01-01", cab)[0], 400)

    def test_isolamento(self):
        cab = self.token("admin.a")
        # vaga e cargo de outra empresa não podem ser usados como filtro
        self.assertEqual(self.req("/api/gestor/relatorios/contratacao?vaga_id=%d" % self.vb, cab)[0], 404)
        b = self.rel("admin.b")
        self.assertEqual((b["kpis"]["inscritos"], b["kpis"]["contratados"]), (1, 1))
        self.assertEqual(b["custo_voz"]["minutos"], 10)
        self.assertEqual({v["titulo"] for v in b["opcoes"]["vagas"]}, {"Vaga B"})
        a = self.rel("admin.a")
        self.assertNotIn("Vaga B", {v["titulo"] for v in a["por_vaga"]})
        norte = self.rel("norte.a")
        self.assertEqual(norte["kpis"]["inscritos"], 1)
        self.assertEqual(norte["custo_voz"]["minutos"], 0)
        self.assertEqual(self.req("/api/gestor/relatorios/contratacao")[0], 401)

    def test_etapas_dos_eventos(self):
        ev = [("Vaga X: movido para Proposta", "2026-01-05 10:00:00"),
              ("Vaga Y: movido para Contratado", "2026-01-06 10:00:00"),
              ("Vaga X: movido para Reprovado (Sem perfil)", "2026-01-07 10:00:00")]
        achadas = relatorios.etapas_dos_eventos(ev, "X")
        self.assertEqual(set(achadas), {"proposta", "reprovado"})
        self.assertEqual(relatorios.ler_data("2026-01-05T10:00:00Z"), datetime(2026, 1, 5, 10))

    def test_sem_travessoes(self):
        for arq in ("relatorios.py", "teste_relatorios.py", "public/js/gestor-relatorios.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                texto = f.read()
            self.assertNotIn(chr(0x2014), texto, arq)
            self.assertNotIn(chr(0x2013), texto, arq)


if __name__ == "__main__":
    unittest.main(verbosity=2)
