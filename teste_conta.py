"""
Testes da conta da empresa (conta.py): consentimento TCPA e revogação, regra da
fila automática, suporte do dono (código de uso único, validade, faixa, gestor
oculto), exportação em ZIP (conteúdo e acesso), encerramento e exclusão definitiva,
e isolamento entre empresas.

Roda numa pasta temporária com banco próprio. Nenhum e-mail sai da máquina.
Uso:  python3 teste_conta.py
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="conta-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)
os.environ["VOZ_FILA_DESLIGADA"] = "1"

import conta  # noqa: E402
import empresas  # noqa: E402
import entrada  # noqa: E402
import planos  # noqa: E402
import server  # noqa: E402

TRACOS = re.compile("[\u2013\u2014]")
EMAILS = []


def _gravar_email(conn, para, assunto, corpo, *a, **k):
    EMAILS.append({"para": para, "assunto": assunto, "corpo": corpo})
    return True, "ok"


server.enviar_email = _gravar_email


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not hasattr(Base, "_pronto"):
            if os.path.exists(server.DB_PATH):
                os.remove(server.DB_PATH)
            server.init_db()
            conn = server.db()
            Base.ea, Base.slug_a = empresas.criar_empresa(conn, "Empresa A")
            Base.eb, Base.slug_b = empresas.criar_empresa(conn, "Empresa B")
            for login, admin, eid in (("admin.a", 1, Base.ea), ("gestor.a", 0, Base.ea), ("admin2.a", 1, Base.ea),
                                      ("admin.b", 1, Base.eb)):
                conn.execute("INSERT INTO gestores (login, senha, nome, is_admin, aprovado, empresa_id) VALUES (?,?,?,?,1,?)",
                             (login, server.hash_senha("senha-123"), login.title(), admin, eid))
            for eid, nome in ((Base.ea, "A"), (Base.eb, "B")):
                cargo = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES (?, ?)", ("Tech " + nome, eid)).lastrowid
                vaga = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, ?, 'aberta', ?)",
                                    (cargo, "Vaga " + nome, eid)).lastrowid
                setattr(Base, "vaga_" + nome.lower(), vaga)
            conn.execute("INSERT INTO sessoes_dono (token) VALUES ('dono-tok')")
            server.config_set(conn, "dono_email", "dono@plataforma.test")
            conn.commit()
            conn.close()
            Base.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
            Base.base = "http://127.0.0.1:%d" % Base.httpd.server_address[1]
            threading.Thread(target=Base.httpd.serve_forever, daemon=True).start()
            Base._pronto = True

    # ---------------------------------------------------------------- ajudas
    def req(self, metodo, caminho, dados=None, cab=None, bruto=False):
        corpo = json.dumps(dados).encode() if dados is not None else None
        h = {"Content-Type": "application/json"}
        h.update(cab or {})
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                conteudo = resp.read()
                return resp.status, (conteudo if bruto else json.loads(conteudo or b"{}"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def token(self, login):
        s, d = self.req("POST", "/api/gestor/login", {"login": login, "senha": "senha-123"})
        self.assertEqual(s, 200, d)
        return {"X-Gestor-Token": d["token"]}

    DONO = {"X-Dono-Token": "dono-tok"}

    def cadastrar(self, nome, email, slug, vaga=None, contato=None, idioma="en"):
        corpo = {"nome": nome, "email": email, "telefone": "+1 860 555 %04d" % (abs(hash(email)) % 10000),
                 "local": "Hartford", "empresa": slug, "consentimento": True, "idioma": idioma}
        if vaga:
            corpo["vaga_id"] = vaga
        if contato is not None:
            corpo["consentimento_contato"] = contato
        s, d = self.req("POST", "/api/candidato/cadastro", corpo)
        self.assertEqual(s, 200, d)
        conn = server.db()
        cand = conn.execute("SELECT * FROM candidatos WHERE token=?", (d["token"],)).fetchone()
        conn.close()
        return cand

    def linha(self, sql, params=()):
        conn = server.db()
        try:
            return conn.execute(sql, params).fetchone()
        finally:
            conn.close()

    def executar(self, sql, params=()):
        conn = server.db()
        conn.execute(sql, params)
        conn.commit()
        conn.close()

    def codigo_suporte(self, eid):
        s, d = self.req("POST", "/api/dono/conta/suporte/%d" % eid, {}, self.DONO)
        self.assertEqual(s, 200, d)
        return d["codigo"]

    def entrar_suporte(self, eid):
        s, d = self.req("POST", "/api/gestor/suporte/entrar", {"codigo": self.codigo_suporte(eid)})
        self.assertEqual(s, 200, d)
        return d, {"X-Gestor-Token": d["token"]}


# =================================================================== 1. consentimento
class TestConsentimento(Base):
    def test_caixa_marcada_guarda_data_texto_ip_e_origem(self):
        c = self.cadastrar("Ana Sim", "ana.sim@x.com", self.slug_a, self.vaga_a, contato=True)
        self.assertTrue(c["consentimento_contato_em"])
        self.assertEqual(c["origem_consentimento"], "formulario")
        self.assertEqual(c["consentimento_contato_ip"], "127.0.0.1")
        self.assertIn("Empresa A", c["consentimento_contato_texto"])
        self.assertIn("Consent is not a condition of employment", c["consentimento_contato_texto"])
        ev = self.linha("SELECT texto FROM eventos WHERE candidato_id=? AND texto LIKE 'Autorizou%'", (c["id"],))
        self.assertIsNotNone(ev)

    def test_texto_no_idioma_do_candidato(self):
        c = self.cadastrar("Bea Es", "bea.es@x.com", self.slug_a, contato=True, idioma="es")
        self.assertIn("El consentimiento no es una condición para el empleo", c["consentimento_contato_texto"])
        self.assertEqual(c["consentimento_contato_texto"], conta.texto_consentimento("Empresa A", "es"))

    def test_caixa_desmarcada_ou_ausente_nao_consente(self):
        for email, contato in (("cai.nao@x.com", False), ("dan.ausente@x.com", None), ("eva.str@x.com", "true")):
            c = self.cadastrar("Sem " + email, email, self.slug_a, contato=contato)
            self.assertEqual(c["consentimento_contato_em"], "", email)
            self.assertEqual(c["origem_consentimento"], "formulario")
            self.assertEqual(c["consentimento_contato_texto"], "")

    def test_importado_sem_consentimento(self):
        conn = server.db()
        st, cid = entrada.criar_candidato(conn, self.ea, {"nome": "Ivo Importado", "email": "ivo.imp@x.com",
                                                          "telefone": "+1 860 555 4242"}, self.vaga_a, "csv")
        conn.commit()
        conn.close()
        self.assertEqual(st, "criado")
        c = self.linha("SELECT * FROM candidatos WHERE id=?", (cid,))
        self.assertEqual((c["origem_consentimento"], c["consentimento_contato_em"]), ("importado", ""))
        self.assertEqual(conta.resumo_consentimento(c)["estado"], "importado")

    def test_selo_na_ficha_e_isolamento(self):
        c = self.cadastrar("Gil Selo", "gil.selo@x.com", self.slug_a, contato=True)
        s, d = self.req("GET", "/api/gestor/candidato/%d" % c["id"], cab=self.token("admin.a"))
        self.assertEqual(s, 200, d)
        self.assertEqual(d["consentimento_contato"]["estado"], "consentiu")
        self.assertTrue(d["consentimento_contato"]["em"])
        self.assertEqual(self.req("GET", "/api/gestor/candidato/%d" % c["id"], cab=self.token("admin.b"))[0], 404)

    def test_revogacao_pelo_candidato(self):
        c = self.cadastrar("Rui Revoga", "rui.rev@x.com", self.slug_a, self.vaga_a, contato=True)
        self.executar("UPDATE candidaturas SET voz_status='para_ligar' WHERE candidato_id=?", (c["id"],))
        cab = {"X-Token": c["token"]}
        s, d = self.req("GET", "/api/candidato/me", cab=cab)
        self.assertEqual(d["contato"]["estado"], "consentiu")
        self.assertEqual(self.req("POST", "/api/candidato/contato/revogar", {}, {"X-Token": "errado"})[0], 401)
        s, d = self.req("POST", "/api/candidato/contato/revogar", {}, cab)
        self.assertEqual((s, d["contato"]["estado"]), (200, "revogado"))
        self.assertEqual(self.linha("SELECT voz_status FROM candidaturas WHERE candidato_id=?", (c["id"],))[0], "nao_ligar")
        self.assertIsNotNone(self.linha("SELECT 1 FROM eventos WHERE candidato_id=? AND texto=?",
                                        (c["id"], "Pediu para não receber ligações nem mensagens automáticas")))
        self.assertEqual(self.req("GET", "/api/candidato/me", cab=cab)[1]["contato"]["estado"], "revogado")
        self.assertFalse(conta.pode_ligar_automatico(server.db(), {"candidato_id": c["id"]}))
        # o gestor vê o selo e a tradução do evento
        s, d = self.req("GET", "/api/gestor/candidato/%d" % c["id"], cab=dict(self.token("admin.a"), **{"X-Idioma": "en"}))
        self.assertEqual(d["consentimento_contato"]["estado"], "revogado")
        self.assertIn("Asked to stop automated calls and texts", [e["texto"] for e in d["eventos"]])


# =================================================================== fila automática
class TestFila(Base):
    def test_regra_da_fila(self):
        sim = self.cadastrar("Fila Sim", "fila.sim@x.com", self.slug_b, self.vaga_b, contato=True)
        nao = self.cadastrar("Fila Nao", "fila.nao@x.com", self.slug_b, self.vaga_b, contato=False)
        conn = server.db()
        ca_nao = conn.execute("SELECT * FROM candidaturas WHERE candidato_id=?", (nao["id"],)).fetchone()
        # padrão desligado: comportamento de antes (liga para todos)
        self.assertFalse(conta.config(conn, self.eb)["so_com_consentimento"])
        self.assertTrue(conta.pode_ligar_automatico(conn, nao))
        self.assertTrue(conta.pode_ligar_automatico(conn, ca_nao))
        conn.close()
        # só o admin liga a regra
        self.assertEqual(self.req("POST", "/api/gestor/conta/config", {"so_com_consentimento": True},
                                  self.token("admin.a"))[0], 200)  # empresa A: não afeta a B
        conn = server.db()
        self.assertTrue(conta.pode_ligar_automatico(conn, nao))
        conn.close()
        s, d = self.req("POST", "/api/gestor/conta/config", {"so_com_consentimento": True}, self.token("admin.b"))
        self.assertEqual((s, d["config"]["so_com_consentimento"]), (200, True))
        conn = server.db()
        self.assertFalse(conta.pode_ligar_automatico(conn, nao))
        self.assertFalse(conta.pode_ligar_automatico(conn, ca_nao))
        self.assertTrue(conta.pode_ligar_automatico(conn, sim))
        self.assertFalse(conta.pode_ligar_automatico(conn, {"candidato_id": 999999}))
        conn.close()
        s, d = self.req("GET", "/api/gestor/conta", cab=self.token("admin.b"))
        self.assertTrue(d["config"]["so_com_consentimento"])
        self.assertIn("Empresa B", d["anuncio"]["en"])
        self.assertTrue(d["anuncio"]["pt"] and d["anuncio"]["es"])
        self.executar("DELETE FROM config WHERE chave IN (?, ?)", (conta._chave(self.ea), conta._chave(self.eb)))

    def test_gestor_comum_nao_altera(self):
        self.assertEqual(self.req("POST", "/api/gestor/conta/config", {"so_com_consentimento": True},
                                  self.token("gestor.a"))[0], 403)


# =================================================================== 2. suporte do dono
class TestSuporte(Base):
    def test_codigo_uso_unico_sessao_e_faixa(self):
        self.assertEqual(self.req("POST", "/api/dono/conta/suporte/%d" % self.ea, {})[0], 401)  # sem dono
        self.assertEqual(self.req("POST", "/api/dono/conta/suporte/999999", {}, self.DONO)[0], 404)
        codigo = self.codigo_suporte(self.ea)
        s, d = self.req("POST", "/api/gestor/suporte/entrar", {"codigo": codigo})
        self.assertEqual(s, 200, d)
        self.assertTrue(d["suporte"]["ativo"])
        self.assertEqual(d["suporte"]["empresa"], "Empresa A")
        self.assertEqual(d["empresa"]["slug"], self.slug_a)
        self.assertTrue(d["admin"])
        cab = {"X-Gestor-Token": d["token"]}
        # o código não vale duas vezes
        self.assertEqual(self.req("POST", "/api/gestor/suporte/entrar", {"codigo": codigo})[0], 401)
        self.assertEqual(self.req("POST", "/api/gestor/suporte/entrar", {"codigo": "x" * 43})[0], 401)
        # sessão funciona, só na empresa A, e o painel sabe que é suporte
        self.assertEqual(self.req("GET", "/api/gestor/cargos", cab=cab)[0], 200)
        s, d2 = self.req("GET", "/api/gestor/conta/sessao", cab=cab)
        self.assertEqual((d2["suporte"], d2["empresa"]), (True, "Empresa A"))
        self.assertTrue(d2["expira_em"])
        s, d3 = self.req("GET", "/api/gestor/conta/sessao", cab=self.token("admin.a"))
        self.assertFalse(d3["suporte"])
        b = self.cadastrar("Bia B", "bia.b.sup@x.com", self.slug_b)
        self.assertEqual(self.req("GET", "/api/gestor/candidato/%d" % b["id"], cab=cab)[0], 404)
        # sem exportar nem encerrar no modo suporte
        self.assertEqual(self.req("POST", "/api/gestor/conta/exportar", {}, cab)[0], 403)
        self.assertEqual(self.req("POST", "/api/gestor/conta/encerrar", {"confirmacao": "Empresa A"}, cab)[0], 403)
        # validade de 2 horas no servidor
        expira = self.linha("SELECT expira_em FROM sessoes_gestor WHERE token=?", (d["token"],))[0]
        self.assertGreater(expira, conta._agora_sql(conta.timedelta(minutes=110)))
        self.assertLess(expira, conta._agora_sql(conta.timedelta(minutes=130)))
        # encerrar pela faixa
        self.assertEqual(self.req("POST", "/api/gestor/suporte/encerrar", {}, self.token("admin.a"))[0], 403)
        self.assertEqual(self.req("POST", "/api/gestor/suporte/encerrar", {}, cab)[0], 200)
        self.assertEqual(self.req("GET", "/api/gestor/cargos", cab=cab)[0], 401)

    def test_codigo_vencido_e_sessao_vencida(self):
        codigo = self.codigo_suporte(self.ea)
        self.executar("UPDATE suporte_codigos SET expira_em=? WHERE codigo_hash=?",
                      (conta._agora_sql(conta.timedelta(seconds=-1)), conta._hash(codigo)))
        self.assertEqual(self.req("POST", "/api/gestor/suporte/entrar", {"codigo": codigo})[0], 401)
        d, cab = self.entrar_suporte(self.ea)
        self.assertEqual(self.req("GET", "/api/gestor/cargos", cab=cab)[0], 200)
        self.executar("UPDATE sessoes_gestor SET expira_em=? WHERE token=?",
                      (conta._agora_sql(conta.timedelta(seconds=-5)), d["token"]))
        self.assertEqual(self.req("GET", "/api/gestor/cargos", cab=cab)[0], 401)
        conta.rodar_rotina()
        self.assertIsNone(self.linha("SELECT 1 FROM sessoes_gestor WHERE token=?", (d["token"],)))

    def test_gestor_oculto_fora_das_listas_e_limites(self):
        self.entrar_suporte(self.ea)
        g = self.linha("SELECT * FROM gestores WHERE empresa_id=? AND suporte=1", (self.ea,))
        self.assertEqual((g["is_admin"], g["aprovado"], g["nome"]), (1, 1, "Suporte (dono)"))
        self.entrar_suporte(self.ea)  # reaproveita a mesma linha
        self.assertEqual(self.linha("SELECT COUNT(*) FROM gestores WHERE empresa_id=? AND suporte=1", (self.ea,))[0], 1)
        logins = [x["login"] for x in self.req("GET", "/api/gestor/gestores", cab=self.token("admin.a"))[1]["gestores"]]
        self.assertNotIn(g["login"], logins)
        self.assertIn("admin.a", logins)
        s, d = self.req("GET", "/api/dono/empresa/%d" % self.ea, cab=self.DONO)
        self.assertNotIn(g["login"], [x["login"] for x in d["gestores_lista"]])
        self.assertEqual(d["empresa"]["gestores"], 3)
        s, d = self.req("GET", "/api/dono/visao", cab=self.DONO)
        self.assertNotIn(g["login"], [x["login"] for x in d["gestores"]])
        conn = server.db()
        self.assertEqual(planos.limite_gestores(conn, self.ea)[1], 3)
        conn.close()
        # a empresa não edita nem apaga o suporte
        adm = self.token("admin.a")
        self.assertEqual(self.req("DELETE", "/api/gestor/gestores/%d" % g["id"], cab=adm)[0], 200)
        self.assertIsNotNone(self.linha("SELECT 1 FROM gestores WHERE id=?", (g["id"],)))
        self.assertEqual(self.req("POST", "/api/gestor/gestores", {"id": g["id"], "nome": "X"}, adm)[0], 404)
        # nunca entra com senha (nem com a senha guardada)
        for senha in ("", "!suporte-sem-senha", "senha-123"):
            self.assertEqual(self.req("POST", "/api/gestor/login", {"login": g["login"], "senha": senha})[0], 401)

    def test_auditoria_visivel_para_o_admin(self):
        d, cab = self.entrar_suporte(self.ea)
        self.req("POST", "/api/gestor/idioma", {"idioma": "en"}, cab)
        self.req("POST", "/api/gestor/conta/config", {"so_com_consentimento": False}, cab)
        regs = self.req("GET", "/api/gestor/auditoria", cab=self.token("admin.a"))[1]["registros"]
        acoes = {(r["quem"], r["acao"]) for r in regs}
        self.assertIn(("Suporte (dono)", "suporte_iniciado"), acoes)
        self.assertIn(("Suporte (dono)", "suporte_entrou"), acoes)
        self.assertIn(("Suporte (dono)", "post conta/config"), acoes)
        # a empresa B não vê nada do suporte da A
        regs_b = self.req("GET", "/api/gestor/auditoria", cab=self.token("admin.b"))[1]["registros"]
        self.assertFalse([r for r in regs_b if r["quem"] == "Suporte (dono)"])

    def test_empresa_suspensa_nao_gera_codigo(self):
        conn = server.db()
        ec, _ = empresas.criar_empresa(conn, "Empresa Suspensa", "suspensa")
        conn.commit()
        conn.close()
        self.assertEqual(self.req("POST", "/api/dono/conta/suporte/%d" % ec, {}, self.DONO)[0], 403)


# =================================================================== 3. exportação
class TestExportacao(Base):
    def esperar(self, cab, exp_id, limite=15):
        fim = time.time() + limite
        while time.time() < fim:
            s, d = self.req("GET", "/api/gestor/conta", cab=cab)
            x = [e for e in d["exportacoes"] if e["id"] == exp_id]
            if x and x[0]["status"] != "preparando":
                return x[0]
            time.sleep(0.2)
        self.fail("exportação não ficou pronta")

    def baixar(self, cab, exp_id):
        return self.req("GET", "/api/gestor/conta/exportacao/%d/baixar" % exp_id, cab=cab, bruto=True)

    def preparar_dados(self):
        if getattr(TestExportacao, "_dados", None):
            return TestExportacao._dados
        c = self.cadastrar("Exp Ana", "exp.ana@x.com", self.slug_a, self.vaga_a, contato=True)
        b = self.cadastrar("Exp Bruno B", "exp.bruno@x.com", self.slug_b, self.vaga_b)
        nome_cv = "cand%d_cv.pdf" % c["id"]
        with open(os.path.join(server.UPLOAD_DIR, nome_cv), "wb") as f:
            f.write(b"%PDF-1.4 curriculo da Ana")
        conn = server.db()
        conn.execute("UPDATE candidatos SET curriculo_arquivo=? WHERE id=?", (nome_cv, c["id"]))
        conn.execute("INSERT INTO resultados_teste (candidato_id, tipo, payload) VALUES (?, 'disc', '{\"perfil\": \"D\"}')",
                     (c["id"],))
        ca = conn.execute("SELECT id FROM candidaturas WHERE candidato_id=?", (c["id"],)).fetchone()["id"]
        conn.execute("INSERT INTO voz_chamadas (candidatura_id, candidato_id, conversation_id, status, transcricao)"
                     " VALUES (?,?,?,?,?)", (ca, c["id"], "conv-exp-1", "concluida",
                                            json.dumps([{"role": "agent", "message": "Hola Ana, transcricao secreta"}])))
        conn.execute("INSERT INTO onboardings (empresa_id, candidato_id, token, pagamento, sensiveis, dados)"
                     " VALUES (?,?,?,?,?,?)",
                     (self.ea, c["id"], "ob-tok-exp", json.dumps({"metodo": "zelle", "zelle": "ana.zelle@banco.com"}),
                      "gAAAA-cifrado", json.dumps({"endereco": "1 Main St"})))
        conn.commit()
        conn.close()
        TestExportacao._dados = (c, b)
        return c, b

    def test_zip_conteudo_acesso_e_validade(self):
        c, b = self.preparar_dados()
        adm = self.token("admin.a")
        self.assertEqual(self.req("POST", "/api/gestor/conta/exportar", {}, self.token("gestor.a"))[0], 403)
        s, d = self.req("POST", "/api/gestor/conta/exportar", {}, adm)
        self.assertEqual(s, 200, d)
        exp = self.esperar(adm, d["id"])
        self.assertEqual(exp["status"], "pronto", exp)
        self.assertFalse(exp["sensivel"])
        # só quem pediu baixa: outro admin da A e o admin da B recebem 404
        self.assertEqual(self.baixar(self.token("admin2.a"), d["id"])[0], 404)
        self.assertEqual(self.baixar(self.token("admin.b"), d["id"])[0], 404)
        self.assertEqual(self.baixar(self.token("gestor.a"), d["id"])[0], 403)
        self.assertEqual(self.req("GET", "/api/gestor/conta", cab=self.token("admin2.a"))[1]["exportacoes"], [])
        s, conteudo = self.baixar(adm, d["id"])
        self.assertEqual(s, 200)
        z = zipfile.ZipFile(io.BytesIO(conteudo))
        nomes = set(z.namelist())
        for arq in ("candidatos.json", "candidatos.csv", "candidaturas.json", "eventos.json", "resultados_testes.json",
                    "entrevistas_notas.json", "entrevistas_agenda.json", "ligacoes_voz.json", "onboardings.json",
                    "onboarding_documentos.json", "LEIA-ME_README.txt"):
            self.assertIn(arq, nomes)
        self.assertIn("curriculos/%d_cand%d_cv.pdf" % (c["id"], c["id"]), nomes)
        cands = json.loads(z.read("candidatos.json"))
        emails = {x["email"] for x in cands}
        self.assertIn("exp.ana@x.com", emails)
        self.assertNotIn("exp.bruno@x.com", emails)  # isolamento
        self.assertFalse([x for x in cands if "token" in x or "agenda_token" in x])
        self.assertFalse([x for x in cands if "consentimento_contato_ip" in x])
        self.assertTrue(any(x["consentimento_contato_em"] for x in cands))
        ligs = json.loads(z.read("ligacoes_voz.json"))
        self.assertIn("transcricao secreta", json.dumps(ligs))
        obs = json.loads(z.read("onboardings.json"))
        self.assertEqual(len(obs), 1)
        self.assertNotIn("pagamento", obs[0])
        self.assertNotIn("sensiveis", obs[0])
        self.assertNotIn("ana.zelle@banco.com", z.read("onboardings.json").decode())
        self.assertNotIn("ob-tok-exp", z.read("onboardings.json").decode())
        self.assertNotIn("senha", json.dumps(json.loads(z.read("gestores.json"))))
        self.assertNotIn("Exp Bruno", z.read("eventos.json").decode())
        # auditoria do pedido e do download
        acoes = [r["acao"] for r in self.req("GET", "/api/gestor/auditoria", cab=adm)[1]["registros"]]
        self.assertIn("exportacao_pedida", acoes)
        self.assertIn("exportacao_baixada", acoes)
        # validade de 24 horas
        self.executar("UPDATE exportacoes SET expira_em=? WHERE id=?",
                      (conta._agora_sql(conta.timedelta(seconds=-1)), d["id"]))
        arquivo = self.linha("SELECT arquivo FROM exportacoes WHERE id=?", (d["id"],))[0]
        self.assertEqual(self.baixar(adm, d["id"])[0], 410)
        self.assertFalse(os.path.exists(os.path.join(server.BASE_DIR, arquivo)))

    def test_sensivel_pede_senha_e_sai_mascarado(self):
        self.preparar_dados()
        adm = self.token("admin.a")
        self.assertEqual(self.req("POST", "/api/gestor/conta/exportar", {"sensivel": True, "senha": "errada"}, adm)[0], 400)
        s, d = self.req("POST", "/api/gestor/conta/exportar", {"sensivel": True, "senha": "senha-123"}, adm)
        self.assertEqual(s, 200, d)
        exp = self.esperar(adm, d["id"])
        self.assertTrue(exp["sensivel"])
        z = zipfile.ZipFile(io.BytesIO(self.baixar(adm, d["id"])[1]))
        texto = z.read("onboardings.json").decode()
        ob = json.loads(texto)[0]
        self.assertEqual(ob["pagamento_mascarado"]["metodo"], "zelle")
        self.assertTrue(ob["pagamento_mascarado"]["zelle"].endswith(".com"))
        self.assertTrue(ob["pagamento_mascarado"]["zelle"].startswith("••••"))
        self.assertTrue(ob["dados_sensiveis"])
        self.assertNotIn("ana.zelle", texto)
        self.assertNotIn("gAAAA", texto)
        self.assertIn("consentimento_contato_ip", z.read("candidatos.json").decode())
        self.assertNotIn("127.0.0.1", z.read("candidatos.json").decode())
        self.assertNotIn('"token"', z.read("candidatos.json").decode())


# =================================================================== encerramento e exclusão
class TestEncerramento(Base):
    def criar_empresa_c(self):
        conn = server.db()
        ec, slug = empresas.criar_empresa(conn, "Empresa C Ltda")
        conn.execute("INSERT INTO gestores (login, senha, nome, is_admin, aprovado, empresa_id) VALUES (?,?,?,1,1,?)",
                     ("admin.c%d" % ec, server.hash_senha("senha-123"), "Carla C", ec))
        cargo = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Tech C', ?)", (ec,)).lastrowid
        conn.execute("INSERT INTO competencias (cargo_id, nome) VALUES (?, 'Limpeza')", (cargo,))
        vaga = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Vaga C', 'aberta', ?)",
                            (cargo, ec)).lastrowid
        server.config_set(conn, "indicacoes:%d" % ec, "{}")
        conn.commit()
        conn.close()
        c = self.cadastrar("Cid C", "cid.c%d@x.com" % ec, slug, vaga, contato=True)
        nome_cv = "cand%d_c.pdf" % c["id"]
        with open(os.path.join(server.UPLOAD_DIR, nome_cv), "wb") as f:
            f.write(b"%PDF-1.4 C")
        conn = server.db()
        conn.execute("UPDATE candidatos SET curriculo_arquivo=? WHERE id=?", (nome_cv, c["id"]))
        ob = conn.execute("INSERT INTO onboardings (empresa_id, candidato_id, token) VALUES (?,?,?)",
                          (ec, c["id"], "ob-c-%d" % ec)).lastrowid
        conn.commit()
        conn.close()
        pasta_ob = os.path.join(server.UPLOAD_DIR, "onboarding", str(ob))
        os.makedirs(pasta_ob, exist_ok=True)
        with open(os.path.join(pasta_ob, "x.bin"), "wb") as f:
            f.write(b"cifrado")
        return ec, c, nome_cv, pasta_ob

    def test_encerrar_cancelar_e_excluir(self):
        ec, c, nome_cv, pasta_ob = self.criar_empresa_c()
        adm = self.token("admin.c%d" % ec)
        self.assertEqual(self.req("POST", "/api/gestor/conta/encerrar", {"confirmacao": "Empresa C"}, adm)[0], 400)
        EMAILS.clear()
        s, d = self.req("POST", "/api/gestor/conta/encerrar", {"confirmacao": "  empresa c ltda "}, adm)
        self.assertEqual(s, 200, d)
        e = self.linha("SELECT * FROM empresas WHERE id=?", (ec,))
        self.assertEqual((e["status"], e["status_anterior"]), ("cancelada", "ativa"))
        self.assertGreater(e["exclusao_em"], conta._agora_sql(conta.timedelta(days=29)))
        self.assertLess(e["exclusao_em"], conta._agora_sql(conta.timedelta(days=31)))
        self.assertEqual([m["para"] for m in EMAILS], ["dono@plataforma.test"])
        self.assertIn("Empresa C Ltda", EMAILS[0]["assunto"])
        self.assertEqual(self.req("GET", "/api/gestor/cargos", cab=adm)[0], 401)  # sessão derrubada
        s, d = self.req("GET", "/api/dono/conta/exclusoes", cab=self.DONO)
        self.assertIn(ec, [x["id"] for x in d["exclusoes"]])
        # rotina antes da data não apaga
        self.assertEqual(conta.rodar_rotina(), [])
        # dono cancela a exclusão
        self.assertEqual(self.req("POST", "/api/dono/conta/exclusao/%d/cancelar" % ec, {}, self.DONO)[0], 200)
        e = self.linha("SELECT status, exclusao_em FROM empresas WHERE id=?", (ec,))
        self.assertEqual((e["status"], e["exclusao_em"]), ("ativa", ""))
        self.assertNotIn(ec, [x["id"] for x in self.req("GET", "/api/dono/conta/exclusoes", cab=self.DONO)[1]["exclusoes"]])
        # encerra de novo e a data passa: exclusão definitiva
        adm = self.token("admin.c%d" % ec)
        self.assertEqual(self.req("POST", "/api/gestor/conta/encerrar", {"confirmacao": "Empresa C Ltda"}, adm)[0], 200)
        self.executar("UPDATE empresas SET exclusao_em=? WHERE id=?", (conta._agora_sql(conta.timedelta(seconds=-1)), ec))
        antes_a = self.linha("SELECT COUNT(*) FROM candidatos WHERE empresa_id=?", (self.ea,))[0]
        self.assertEqual(conta.rodar_rotina(), [ec])
        conn = server.db()
        try:
            self.assertIsNone(conn.execute("SELECT 1 FROM empresas WHERE id=?", (ec,)).fetchone())
            for (tabela,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                cols = {r[1] for r in conn.execute("PRAGMA table_info(%s)" % tabela).fetchall()}
                if "empresa_id" in cols and tabela != "exclusoes_empresa":
                    n = conn.execute("SELECT COUNT(*) FROM %s WHERE empresa_id=?" % tabela, (ec,)).fetchone()[0]
                    self.assertEqual(n, 0, tabela)
                if "candidato_id" in cols:
                    n = conn.execute("SELECT COUNT(*) FROM %s WHERE candidato_id=?" % tabela, (c["id"],)).fetchone()[0]
                    self.assertEqual(n, 0, tabela)
            self.assertIsNone(conn.execute("SELECT 1 FROM config WHERE chave=?", ("indicacoes:%d" % ec,)).fetchone())
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM competencias c LEFT JOIN cargos g ON g.id=c.cargo_id"
                                          " WHERE g.id IS NULL").fetchone()[0], 0)
            reg = conn.execute("SELECT * FROM exclusoes_empresa WHERE empresa_id=?", (ec,)).fetchone()
            self.assertEqual(reg["nome"], "Empresa C Ltda")
            self.assertIn("candidatos", json.loads(reg["resumo"]))
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM candidatos WHERE empresa_id=?", (self.ea,)).fetchone()[0],
                             antes_a)  # as outras empresas ficam intactas
            self.assertIsNotNone(conn.execute("SELECT 1 FROM empresas WHERE id=?", (self.ea,)).fetchone())
        finally:
            conn.close()
        self.assertFalse(os.path.exists(os.path.join(server.UPLOAD_DIR, nome_cv)))
        self.assertFalse(os.path.exists(pasta_ob))

    def test_so_admin_e_nao_cancela_inexistente(self):
        self.assertEqual(self.req("POST", "/api/gestor/conta/encerrar", {"confirmacao": "Empresa A"},
                                  self.token("gestor.a"))[0], 403)
        self.assertEqual(self.req("POST", "/api/dono/conta/exclusao/%d/cancelar" % self.ea, {}, self.DONO)[0], 404)
        self.assertEqual(self.req("GET", "/api/dono/conta/exclusoes")[0], 401)


# =================================================================== arquivos
class TestArquivos(unittest.TestCase):
    def test_sem_travessoes_e_trilingue(self):
        for arq in ("conta.py", "teste_conta.py", "public/js/gestor-conta.js", "public/js/dono-suporte.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)
        for arq in ("public/js/gestor-conta.js", "public/js/dono-suporte.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                texto = f.read()
            blocos = re.findall(r"Object\.assign\(I18N_\w+\.(pt|en|es), \{(.*?)\n\}\);", texto, re.S)
            chaves = {lang: set(re.findall(r'(?m)(?:^\s*|,\s+)(\w+): "', corpo)) for lang, corpo in blocos}
            self.assertEqual(set(chaves), {"pt", "en", "es"}, arq)
            self.assertEqual(chaves["pt"], chaves["en"], arq)
            self.assertEqual(chaves["pt"], chaves["es"], arq)

    def test_texto_do_consentimento_igual_no_navegador(self):
        with open(os.path.join(AQUI, "public", "js", "i18n-candidato.js"), encoding="utf-8") as f:
            js = f.read()
        for lang in ("pt", "en", "es"):
            esperado = conta.TEXTO_CONSENTIMENTO[lang].replace("{empresa}", "{empresa}")
            self.assertIn('cad_contato: "%s"' % esperado, js, lang)


if __name__ == "__main__":
    unittest.main(verbosity=1)
