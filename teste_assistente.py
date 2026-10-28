"""
Testes do assistente de configuração e da página Meu plano (assistente.py).

Uso:  python3 teste_assistente.py
"""
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="assistente-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)

import assistente  # noqa: E402
import empresas  # noqa: E402
import mensagens  # noqa: E402
import planos  # noqa: E402
import server  # noqa: E402

TRACOS = re.compile(r"[\u2013\u2014]")
ENVIADOS = []


def enviar_falso(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt"):
    ENVIADOS.append({"para": para, "assunto": assunto, "corpo": corpo})
    return True, "ok"


class TestAssistente(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server.enviar_email = enviar_falso
        assistente.ENVIO_EM_SEGUNDO_PLANO = False
        planos.ENVIO_EM_SEGUNDO_PLANO = False
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        conn = server.db()
        cls.ea, _ = empresas.criar_empresa(conn, "Empresa A")
        cls.eb, _ = empresas.criar_empresa(conn, "Empresa B")
        cls.ec, _ = empresas.criar_empresa(conn, "Empresa C")
        conn.execute("UPDATE empresas SET plano='voz100' WHERE id IN (?,?)", (cls.ea, cls.eb))
        conn.execute("UPDATE empresas SET plano='essencial' WHERE id=?", (cls.ec,))
        for login, admin, eid in (("admin.a", 1, cls.ea), ("gestor.a", 0, cls.ea), ("admin.b", 1, cls.eb),
                                  ("admin.c", 1, cls.ec)):
            conn.execute("INSERT INTO gestores (login, senha, nome, email, is_admin, aprovado, empresa_id)"
                         " VALUES (?,?,?,?,?,1,?)",
                         (login, server.hash_senha("senha-123"), login.title(), login + "@x.com", admin, eid))
        conn.commit()
        conn.close()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        del ENVIADOS[:]

    def req(self, metodo, caminho, dados=None, cab=None):
        corpo = json.dumps(dados).encode() if dados is not None else None
        h = {"Content-Type": "application/json"}
        h.update(cab or {})
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def token(self, login):
        s, d = self.req("POST", "/api/gestor/login", {"login": login, "senha": "senha-123"})
        self.assertEqual(s, 200, d)
        return {"X-Gestor-Token": d["token"]}

    @staticmethod
    def passos(d):
        return {p["id"]: p for p in d["passos"]}

    # ------------------------------------------------------------ assistente

    def test_empresa_nova_tudo_pendente(self):
        s, d = self.req("GET", "/api/gestor/assistente", cab=self.token("admin.c"))
        self.assertEqual(s, 200, d)
        p = self.passos(d)
        self.assertNotIn("voz", p)  # plano Essencial não tem minutos de voz
        for pid in ("logo", "equipe", "cargos", "agenda", "entrada", "vaga", "onboarding", "indicacoes"):
            self.assertFalse(p[pid]["feito"], pid)
        self.assertTrue(p["indicacoes"]["opcional"])
        self.assertEqual((p["logo"]["aba"], p["logo"]["ancora"]), ("config", "cfg-marca"))
        self.assertEqual(p["vaga"]["aba"], "vagas")
        self.assertEqual((d["feitos"], d["total"], d["pct"]), (0, 7, 0))
        self.assertTrue(d["mostrar"])
        self.assertFalse(d["completo"])

    def test_passos_concluidos_pelos_dados(self):
        admin = self.token("admin.a")
        s, d = self.req("GET", "/api/gestor/assistente", cab=admin)
        p = self.passos(d)
        self.assertIn("voz", p)  # Voz 100 tem minutos de voz
        self.assertTrue(p["equipe"]["feito"])  # admin.a e gestor.a aprovados
        self.assertFalse(p["cargos"]["feito"])
        conn = server.db()
        eid = self.ea
        # logo
        os.makedirs(mensagens.pasta_logos(), exist_ok=True)
        with open(mensagens.caminho_logo("logo_a.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"0" * 32)
        conn.execute("UPDATE empresas SET logo='logo_a.png' WHERE id=?", (eid,))
        # cargo sem competência ainda não conta
        cargo = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Tech', ?)", (eid,)).lastrowid
        conn.commit()
        _, d = self.req("GET", "/api/gestor/assistente", cab=admin)
        self.assertTrue(self.passos(d)["logo"]["feito"])
        self.assertFalse(self.passos(d)["cargos"]["feito"])
        conn.execute("INSERT INTO competencias (cargo_id, nome) VALUES (?, 'Elétrica')", (cargo,))
        # voz ligada sem roteiro revisado ainda não conta
        conn.execute("UPDATE cargos SET voz_ativa=1, roteiro_voz='{}' WHERE id=?", (cargo,))
        conn.commit()
        _, d = self.req("GET", "/api/gestor/assistente", cab=admin)
        self.assertTrue(self.passos(d)["cargos"]["feito"])
        self.assertFalse(self.passos(d)["voz"]["feito"])
        conn.execute("UPDATE cargos SET roteiro_voz=? WHERE id=?", (json.dumps({"revisado_em": "2026-10-01"}), cargo))
        server.config_set(conn, "agenda:%d" % eid, json.dumps({"ativo": True}))
        conn.execute("INSERT INTO candidatos (token, nome, email, empresa_id, tags) VALUES ('tk-a','Ana','a@x.com',?,?)",
                     (eid, json.dumps(["csv"])))
        conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Tech', 'aberta', ?)",
                     (cargo, eid))
        server.config_set(conn, "onboarding:%d" % eid, json.dumps({"empregador_nome": "Empresa A LLC"}))
        conn.commit()
        _, d = self.req("GET", "/api/gestor/assistente", cab=admin)
        p = self.passos(d)
        for pid in ("voz", "agenda", "entrada", "vaga"):
            self.assertTrue(p[pid]["feito"], pid)
        self.assertFalse(p["onboarding"]["feito"])  # falta o EIN
        self.assertFalse(d["completo"])
        server.config_set(conn, "onboarding:%d" % eid,
                          json.dumps({"empregador_nome": "Empresa A LLC", "empregador_ein": "12-3456789"}))
        conn.commit()
        _, d = self.req("GET", "/api/gestor/assistente", cab=admin)
        self.assertTrue(d["completo"])  # o opcional (indicação) não impede
        self.assertFalse(d["mostrar"])
        self.assertEqual((d["feitos"], d["total"], d["pct"]), (8, 8, 100))
        self.assertFalse(self.passos(d)["indicacoes"]["feito"])
        server.config_set(conn, "indicacoes:%d" % eid, json.dumps({"ativo": True}))
        conn.commit()
        conn.close()
        _, d = self.req("GET", "/api/gestor/assistente", cab=admin)
        self.assertTrue(self.passos(d)["indicacoes"]["feito"])
        # nada disso vaza para a empresa B
        _, d = self.req("GET", "/api/gestor/assistente", cab=self.token("admin.b"))
        pb = self.passos(d)
        for pid in ("logo", "cargos", "voz", "agenda", "onboarding", "indicacoes"):
            self.assertFalse(pb[pid]["feito"], pid)
        self.assertTrue(d["mostrar"])

    def test_entrada_pela_configuracao_do_indeed(self):
        conn = server.db()
        server.config_set(conn, "entrada:%d" % self.eb, json.dumps({"ativo": True}))
        conn.commit()
        _, d = self.req("GET", "/api/gestor/assistente", cab=self.token("admin.b"))
        self.assertTrue(self.passos(d)["entrada"]["feito"])
        server.config_set(conn, "entrada:%d" % self.eb, json.dumps({"ativo": False}))
        conn.commit()
        conn.close()
        _, d = self.req("GET", "/api/gestor/assistente", cab=self.token("admin.b"))
        self.assertFalse(self.passos(d)["entrada"]["feito"])

    def test_dispensar_e_reabrir(self):
        admin = self.token("admin.c")
        s, d = self.req("POST", "/api/gestor/assistente/dispensar", {"dispensado": True}, admin)
        self.assertEqual(s, 200, d)
        self.assertTrue(d["dispensado"])
        self.assertFalse(d["mostrar"])
        _, d = self.req("GET", "/api/gestor/assistente", cab=admin)
        self.assertTrue(d["dispensado"])
        # guardado por empresa: a B continua vendo
        _, db_ = self.req("GET", "/api/gestor/assistente", cab=self.token("admin.b"))
        self.assertFalse(db_["dispensado"])
        _, d = self.req("POST", "/api/gestor/assistente/dispensar", {"dispensado": False}, admin)
        self.assertFalse(d["dispensado"])
        self.assertTrue(d["mostrar"])

    def test_so_administrador(self):
        g = self.token("gestor.a")
        for metodo, caminho, corpo in (("GET", "/api/gestor/assistente", None),
                                       ("POST", "/api/gestor/assistente/dispensar", {"dispensado": True}),
                                       ("GET", "/api/gestor/assistente/plano", None),
                                       ("POST", "/api/gestor/assistente/pedido", {"tipo": "cancelar"})):
            s, d = self.req(metodo, caminho, corpo, g)
            self.assertEqual(s, 403, caminho)
        s, d = self.req("GET", "/api/gestor/assistente", cab=dict(g, **{"X-Idioma": "en"}))
        self.assertEqual(d["erro"], "Only the company admin can access this area")
        self.assertEqual(self.req("GET", "/api/gestor/assistente")[0], 401)

    # ------------------------------------------------------------ meu plano

    def test_meu_plano(self):
        conn = server.db()
        cand = conn.execute("INSERT INTO candidatos (token, nome, email, empresa_id) VALUES ('tk-p','Pedro','p@x.com',?)",
                            (self.eb,)).lastrowid
        cargo = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Ops', ?)", (self.eb,)).lastrowid
        vaga = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Ops', 'aberta', ?)",
                            (cargo, self.eb)).lastrowid
        cand_id = conn.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cand, vaga)).lastrowid
        conn.execute("INSERT INTO voz_chamadas (candidatura_id, candidato_id, conversation_id, duracao, iniciada_em)"
                     " VALUES (?,?,?,?,datetime('now'))", (cand_id, cand, "conv-b-1", 125))
        conn.commit()
        conn.close()
        s, d = self.req("GET", "/api/gestor/assistente/plano", cab=self.token("admin.b"))
        self.assertEqual(s, 200, d)
        self.assertEqual(d["plano_codigo"], "voz100")
        self.assertEqual(d["status_conta"], "ativa")
        self.assertEqual(len(d["historico"]), 6)
        self.assertEqual(d["historico"][-1]["minutos"], 3)  # 125 s arredondam para 3 min
        self.assertEqual(d["historico"][-1]["mes"], planos.mes_de())
        self.assertEqual(d["info"]["uso"]["minutos"], 3)
        self.assertEqual(d["limite_minutos"], 100)
        atuais = [p for p in d["planos"] if p["atual"]]
        self.assertEqual([p["codigo"] for p in atuais], ["voz100"])
        self.assertIn("caro", d["motivos"])
        self.assertFalse(d["stripe_ativo"])
        # a empresa A não enxerga os minutos da B
        _, da = self.req("GET", "/api/gestor/assistente/plano", cab=self.token("admin.a"))
        self.assertEqual(da["historico"][-1]["minutos"], 0)
        # nomes no idioma do painel
        _, de = self.req("GET", "/api/gestor/assistente/plano", cab=dict(self.token("admin.b"), **{"X-Idioma": "en"}))
        self.assertIn("Voice 100", [p["nome"] for p in de["planos"]])

    def test_status_pagamento_recusado(self):
        conn = server.db()
        conn.execute("UPDATE empresas SET pagamento_status='falhou' WHERE id=?", (self.ec,))
        conn.commit()
        _, d = self.req("GET", "/api/gestor/assistente/plano", cab=self.token("admin.c"))
        self.assertEqual(d["status_conta"], "pagamento_falhou")
        conn.execute("UPDATE empresas SET pagamento_status='', status='teste', trial_fim=date('now','+5 day')"
                     " WHERE id=?", (self.ec,))
        conn.commit()
        conn.close()
        _, d = self.req("GET", "/api/gestor/assistente/plano", cab=self.token("admin.c"))
        self.assertEqual(d["status_conta"], "teste")
        self.assertTrue(d["info"]["em_teste"])
        conn = server.db()
        conn.execute("UPDATE empresas SET status='ativa', trial_fim='' WHERE id=?", (self.ec,))
        conn.commit()
        conn.close()

    def test_pedido_avisa_o_dono_e_registra(self):
        conn = server.db()
        server.config_set(conn, "dono_email", "dono@bussola.test")
        conn.commit()
        conn.close()
        admin = self.token("admin.a")
        s, d = self.req("POST", "/api/gestor/assistente/pedido",
                        {"tipo": "trocar_plano", "plano": "voz300", "ciclo": "anual", "mensagem": "Precisamos de SMS"}, admin)
        self.assertEqual(s, 200, d)
        self.assertTrue(d["dono_avisado"])
        self.assertEqual(len(ENVIADOS), 1)
        email = ENVIADOS[0]
        self.assertEqual(email["para"], "dono@bussola.test")
        self.assertIn("Empresa A", email["assunto"])
        for trecho in ("Voz 300", "anual", "Voz 100", "Precisamos de SMS", "Admin.A"):
            self.assertIn(trecho, email["corpo"])
        s, d2 = self.req("POST", "/api/gestor/assistente/pedido",
                         {"tipo": "cancelar", "motivo": "caro", "mensagem": "Orçamento cortado"}, admin)
        self.assertEqual(s, 200, d2)
        self.assertIn("Preço alto", ENVIADOS[-1]["corpo"])
        self.assertIn("pedido de cancelamento", ENVIADOS[-1]["assunto"])
        # o dono escolheu receber em inglês (config dono_idioma)
        conn = server.db()
        server.config_set(conn, "dono_idioma", "en")
        conn.commit()
        conn.close()
        try:
            s, d3 = self.req("POST", "/api/gestor/assistente/pedido",
                             {"tipo": "trocar_plano", "plano": "voz300", "ciclo": "mensal", "mensagem": "SMS"}, admin)
            self.assertEqual(s, 200, d3)
            en = ENVIADOS[-1]
            self.assertEqual(en["assunto"], "Bússola: plan change request (Empresa A)")
            for trecho in ("New plan change request.", "Requested plan: Voice 300 (monthly)", "Current plan: Voice 100",
                           "Requested by: Admin.A"):
                self.assertIn(trecho, en["corpo"])
            self.assertIsNone(TRACOS.search(en["corpo"] + en["assunto"]))
        finally:
            conn = server.db()
            server.config_set(conn, "dono_idioma", "")
            conn.execute("DELETE FROM pedidos_plano WHERE empresa_id=? AND ciclo='mensal'", (self.ea,))
            conn.commit()
            conn.close()
        conn = server.db()
        linhas = conn.execute("SELECT * FROM pedidos_plano WHERE empresa_id=? ORDER BY id", (self.ea,)).fetchall()
        conn.close()
        self.assertEqual([(r["tipo"], r["plano"], r["ciclo"], r["motivo"], r["email_enviado"]) for r in linhas],
                         [("trocar_plano", "voz300", "anual", "", 1), ("cancelar", "", "", "caro", 1)])
        self.assertEqual(linhas[0]["plano_atual"], "voz100")
        # aparece na página da A, não na da B
        _, pa = self.req("GET", "/api/gestor/assistente/plano", cab=admin)
        self.assertEqual(len(pa["pedidos"]), 2)
        _, pb = self.req("GET", "/api/gestor/assistente/plano", cab=self.token("admin.b"))
        self.assertEqual(pb["pedidos"], [])
        # validação
        self.assertEqual(self.req("POST", "/api/gestor/assistente/pedido", {"tipo": "apagar"}, admin)[0], 400)
        s, d = self.req("POST", "/api/gestor/assistente/pedido", {"tipo": "trocar_plano", "plano": "nao-existe"},
                        dict(admin, **{"X-Idioma": "es"}))
        self.assertEqual((s, d["erro"]), (400, "Plan inválido"))
        s, d = self.req("POST", "/api/gestor/assistente/pedido",
                        {"tipo": "trocar_plano", "plano": "voz300", "ciclo": "semanal"}, admin)
        self.assertEqual(s, 400)
        # motivo desconhecido vira "outro"
        s, _ = self.req("POST", "/api/gestor/assistente/pedido", {"tipo": "cancelar", "motivo": "xyz"}, admin)
        self.assertEqual(s, 200)
        conn = server.db()
        self.assertEqual(conn.execute("SELECT motivo FROM pedidos_plano WHERE empresa_id=? ORDER BY id DESC",
                                      (self.ea,)).fetchone()[0], "outro")
        conn.close()

    def test_pedido_sem_email_do_dono_e_limite_diario(self):
        conn = server.db()
        server.config_set(conn, "dono_email", "")
        conn.commit()
        conn.close()
        admin = self.token("admin.c")
        for _ in range(assistente.PEDIDOS_POR_DIA):
            s, d = self.req("POST", "/api/gestor/assistente/pedido", {"tipo": "trocar_plano", "plano": "voz100"}, admin)
            self.assertEqual(s, 200, d)
            self.assertFalse(d["dono_avisado"])
        self.assertEqual(ENVIADOS, [])
        s, d = self.req("POST", "/api/gestor/assistente/pedido", {"tipo": "cancelar"}, admin)
        self.assertEqual(s, 429, d)
        conn = server.db()
        n = conn.execute("SELECT COUNT(*) FROM pedidos_plano WHERE empresa_id=?", (self.ec,)).fetchone()[0]
        conn.close()
        self.assertEqual(n, assistente.PEDIDOS_POR_DIA)


class TestArquivos(unittest.TestCase):
    def test_sem_travessoes(self):
        for arq in ("assistente.py", "teste_assistente.py", "public/js/gestor-assistente.js",
                    "public/js/gestor-faturamento.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)

    def test_textos_nos_tres_idiomas(self):
        for arq, prefixo in (("public/js/gestor-assistente.js", "as_"), ("public/js/gestor-faturamento.js", "fa_")):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                js = f.read()
            chaves = set(re.findall(r"^\s+(%s[a-z_]+):" % prefixo, js, re.M))
            self.assertTrue(chaves)
            for chave in chaves:
                self.assertEqual(len(re.findall(r"^\s+%s:" % chave, js, re.M)), 3, chave)

    def test_gestor_html_carrega_os_scripts(self):
        with open(os.path.join(AQUI, "public", "gestor.html"), encoding="utf-8") as f:
            html = f.read()
        for js in ("js/gestor-assistente.js", "js/gestor-faturamento.js"):
            self.assertIn(js, html)

    def test_erros_traduzidos(self):
        import erros_i18n
        for m in ("Apenas o administrador da empresa acessa esta área", "Tipo de pedido inválido",
                  "Muitos pedidos hoje. Tente de novo amanhã."):
            self.assertNotEqual(erros_i18n.traduzir(m, "en"), m)
            self.assertNotEqual(erros_i18n.traduzir(m, "es"), m)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
