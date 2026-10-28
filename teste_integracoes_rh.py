"""
Testes das integrações de RH (integracoes_rh.py): exportação para a folha
(colunas do Gusto, do QuickBooks e do CSV genérico, mapa de colunas, dados
sensíveis só com a senha e auditados, arquivo de prestadores 1099 com o W-9) e
verificação de antecedentes pela Checkr (corpo do pedido de candidato e de
convite, assinatura do webhook válida e inválida, mudanças de status, aviso aos
administradores, aviso ao contratar) e isolamento entre empresas.

Uso:  python3 teste_integracoes_rh.py

Tudo numa pasta temporária. Nenhuma chamada real: o urllib é simulado para a
Checkr e os e-mails são gravados na memória.
"""
import base64
import csv
import hashlib
import hmac
import io
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
PASTA = tempfile.mkdtemp(prefix="integracoes-rh-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)
os.environ.pop("BUSSOLA_CHAVE_DADOS", None)

import empresas  # noqa: E402
import integracoes_rh  # noqa: E402
import onboarding  # noqa: E402
import server  # noqa: E402

integracoes_rh.ENVIO_EM_SEGUNDO_PLANO = False
onboarding.ENVIO_EM_SEGUNDO_PLANO = False
server.Handler.log_message = lambda *a: None
TRACOS = re.compile("[\u2013\u2014]")
SENHA = "Segredo-123"
CHAVE_A = "ckr_test_aaaaaaaaaaaaaaaaaaaa1111"
CHAVE_B = "ckr_test_bbbbbbbbbbbbbbbbbbbb2222"

_URLOPEN_REAL = urllib.request.urlopen


class Checkr:
    """Simula a API da Checkr: grava os pedidos e devolve respostas prontas."""

    def __init__(self):
        self.pedidos = []
        self.falhar = None
        self.n = 0

    def __call__(self, req, *a, **kw):
        url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
        if "checkr" not in url:
            return _URLOPEN_REAL(req, *a, **kw)
        corpo = json.loads(req.data.decode()) if req.data else None
        self.pedidos.append({"url": url, "metodo": req.get_method(), "corpo": corpo,
                             "auth": req.get_header("Authorization")})
        if self.falhar:
            raise urllib.error.HTTPError(url, self.falhar, "erro", {}, io.BytesIO(b'{"error":"Package not found"}'))
        self.n += 1
        if url.endswith("/candidates"):
            dados = {"id": "cand_%d" % self.n, "object": "candidate"}
        elif url.endswith("/invitations"):
            dados = {"id": "inv_%d" % self.n, "status": "pending",
                     "invitation_url": "https://apply.checkr.com/invite/x%d" % self.n}
        elif url.endswith("/packages"):
            dados = {"data": [{"slug": "tasker_standard", "name": "Tasker Standard"}]}
        else:
            dados = {}
        return io.BytesIO(json.dumps(dados).encode())


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
        chave = os.path.join(server.BASE_DIR, "chave_dados.key")
        if os.path.exists(chave):
            os.remove(chave)
        onboarding.esquecer_chave()
        integracoes_rh.zerar_limites()
        server.init_db()
        self.conn = c = server.db()
        self.ea, _ = empresas.criar_empresa(c, "Belleza's Home Services CT")
        self.eb, _ = empresas.criar_empresa(c, "Outra Empresa")
        cargo_a = c.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Cleaning Tech', ?)", (self.ea,)).lastrowid
        cargo_b = c.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Cleaner', ?)", (self.eb,)).lastrowid
        self.vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Cleaning Tech',"
                              " 'aberta', ?)", (cargo_a, self.ea)).lastrowid
        self.vaga_b = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Cleaner',"
                                " 'aberta', ?)", (cargo_b, self.eb)).lastrowid
        hash_ = server.hash_senha(SENHA)
        for login, idioma, empresa, admin in (("tony", "pt", self.ea, 1), ("carine", "en", self.ea, 1),
                                              ("ana", "es", self.ea, 1), ("joao", "pt", self.ea, 0),
                                              ("intruso", "pt", self.eb, 1)):
            gid = c.execute("INSERT INTO gestores (nome, login, senha, email, is_admin, aprovado, empresa_id, idioma)"
                            " VALUES (?,?,?,?,?,1,?,?)", (login.title(), login, hash_, login + "@example.com", admin,
                                                          empresa, idioma)).lastrowid
            c.execute("INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)", ("sess-" + login, gid))
        server.config_set(c, "smtp_host", "smtp.teste")
        server.config_set(c, "url_publica", "https://rh.exemplo.com")
        c.commit()
        onboarding.salvar_config(c, self.ea, dict(onboarding.config(c, self.ea),
                                                  empregador_cidade_estado_cep="Hartford, CT 06103"))
        self.enviados = []
        self._original = server.enviar_email

        def gravar(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt"):
            self.enviados.append({"para": para, "assunto": assunto, "corpo": corpo})
            return True, "enviado"

        server.enviar_email = gravar
        self.checkr = Checkr()
        urllib.request.urlopen = self.checkr

    def tearDown(self):
        urllib.request.urlopen = _URLOPEN_REAL
        server.enviar_email = self._original
        self.conn.close()

    # ---------------------------------------------------------- ajudantes
    def req(self, metodo, caminho, dados=None, gestor=None, idioma=None, bruto=None, cab_extra=None):
        cab = {"Content-Type": "application/json"}
        if gestor:
            cab["X-Gestor-Token"] = "sess-" + gestor
        if idioma:
            cab["X-Idioma"] = idioma
        cab.update(cab_extra or {})
        corpo = bruto if bruto is not None else (json.dumps(dados).encode() if dados is not None else None)
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=cab)
        try:
            with _URLOPEN_REAL(r) as resp:
                conteudo = resp.read()
                if resp.headers.get("Content-Type", "").startswith("application/json"):
                    return resp.status, json.loads(conteudo or b"{}")
                return resp.status, (conteudo, dict(resp.headers))
        except urllib.error.HTTPError as e:
            conteudo = e.read()
            try:
                return e.code, json.loads(conteudo or b"{}")
            except ValueError:
                return e.code, conteudo

    def candidato(self, nome="Maria Lopez", email="maria@example.com", empresa=None, etapa="proposta"):
        c = self.conn
        empresa = empresa or self.ea
        cid = c.execute("INSERT INTO candidatos (token, nome, email, local, telefone, idioma, empresa_id)"
                        " VALUES (?,?,?,?,?,?,?)", ("tok-" + email, nome, email, "", "+18605550101", "es",
                                                    empresa)).lastrowid
        c.execute("INSERT INTO candidaturas (candidato_id, vaga_id, etapa) VALUES (?,?,?)",
                  (cid, self.vaga if empresa == self.ea else self.vaga_b, etapa))
        c.commit()
        return cid

    def contratado(self, tipo="w2", nome="Maria Lopez", email="maria@example.com", empresa=None, inicio="2026-11-09",
                   status="concluido", unidade="hora", valor=22):
        c = self.conn
        empresa = empresa or self.ea
        cid = self.candidato(nome, email, empresa)
        oferta = {"tipo": tipo, "cargo": "House Cleaning Technician", "data_inicio": inicio, "valor": valor,
                  "unidade": unidade}
        dados = {"nome_legal": nome, "endereco": "10 Main St", "apto": "2B", "cidade": "Hartford", "estado": "CT",
                 "cep": "06103", "telefone": "8605550101", "email": email}
        pag = {"metodo": "deposito", "banco": "Chase", "tipo_conta": "corrente"}
        sens = {"nascimento": "1990-04-12", "routing": "011000015", "conta": "123456789"}
        if tipo == "w2":
            sens["ssn"] = "212-55-1234"
        else:
            sens["ein"] = "12-3456789"
        ob = c.execute("INSERT INTO onboardings (empresa_id, candidato_id, token, tipo, oferta, status, dados, pagamento,"
                       " sensiveis) VALUES (?,?,?,?,?,?,?,?,?)",
                       (empresa, cid, "t-" + email, tipo, json.dumps(oferta), status, json.dumps(dados),
                        json.dumps(pag), onboarding.cifrar_dict(c, sens))).lastrowid
        if tipo == "w2":
            form = {"primeiro_nome": nome.split()[0], "sobrenome": nome.split()[-1], "ssn": "212-55-1234"}
            chave = "w4"
        else:
            form = {"nome": nome, "nome_empresa": "Lopez Cleaning LLC", "classificacao": "llc", "llc_classificacao": "S",
                    "tipo_tin": "ein", "ein": "12-3456789", "endereco": "10 Main St", "cidade": "Hartford",
                    "estado": "CT", "cep": "06103"}
            chave = "w9"
        c.execute("INSERT INTO onboarding_docs (onboarding_id, empresa_id, tipo, chave, titulo, dados_cifrados)"
                  " VALUES (?,?,'formulario',?,?,?)", (ob, empresa, chave, chave, onboarding.cifrar_dict(c, form)))
        c.commit()
        return ob, cid

    def exportar(self, gestor="tony", **d):
        corpo = {"provedor": "gusto", "tipo": "w2"}
        corpo.update(d)
        return self.req("POST", "/api/gestor/integracoes-rh/folha/exportar", corpo, gestor=gestor)

    def csv_de(self, resp):
        st, r = resp
        self.assertEqual(st, 200, r)
        conteudo, cab = r
        self.assertIn("text/csv", cab["Content-Type"])
        self.assertIn("no-store", cab["Cache-Control"])
        return list(csv.reader(io.StringIO(conteudo.decode("utf-8"))))

    def configurar_checkr(self, empresa=None, chave=CHAVE_A, gestor="tony", **extra):
        d = {"chave": chave, "pacote": "tasker_standard", "estado": "CT", "cidade": "Hartford"}
        d.update(extra)
        st, r = self.req("POST", "/api/gestor/integracoes-rh/config", {"checkr": d}, gestor=gestor)
        self.assertEqual(st, 200, r)
        return r

    def webhook(self, evento, chave=CHAVE_A, assinatura=None):
        corpo = json.dumps(evento, separators=(",", ":")).encode()
        sig = assinatura if assinatura is not None else hmac.new(chave.encode(), corpo, hashlib.sha256).hexdigest()
        return self.req("POST", "/api/integracoes/checkr/webhook", bruto=corpo, cab_extra={"X-Checkr-Signature": sig})


# ============================================================ A. folha
class TestFolha(Base):
    def test_colunas_gusto_sem_sensiveis(self):
        self.contratado()
        linhas = self.csv_de(self.exportar())
        cab = linhas[0]
        for col in ("Member type", "Legal first name", "Last name", "Personal email", "Start date", "Work state",
                    "Job title", "Employee type", "Compensation amount", "Compensation unit", "Home address street 1",
                    "Home address city", "Home address state", "Home address ZIP", "Bank name", "Bank account type"):
            self.assertIn(col, cab)
        for col in ("SSN", "Date of birth", "Routing number", "Account number"):
            self.assertNotIn(col, cab)
        lin = dict(zip(cab, linhas[1]))
        self.assertEqual(lin["Member type"], "Employee")
        self.assertEqual(lin["Legal first name"], "Maria")
        self.assertEqual(lin["Last name"], "Lopez")
        self.assertEqual(lin["Start date"], "11/09/2026")
        self.assertEqual(lin["Work state"], "CT")
        self.assertEqual(lin["Compensation amount"], "22.00")
        self.assertEqual(lin["Compensation unit"], "Hour")
        self.assertEqual(lin["Bank account type"], "Checking")
        self.assertNotIn("212-55-1234", "\n".join(",".join(l) for l in linhas))
        self.assertNotIn("123456789", "\n".join(",".join(l) for l in linhas))

    def test_colunas_quickbooks_e_generico(self):
        self.contratado(unidade="salario", valor=52000)
        cab = self.csv_de(self.exportar(provedor="quickbooks"))
        self.assertEqual(cab[0][:3], ["Worker type", "First name", "Middle initial"])
        lin = dict(zip(cab[0], cab[1]))
        self.assertEqual(lin["Hire date"], "11/09/2026")
        self.assertEqual(lin["Pay type"], "Salary")
        self.assertEqual(lin["Pay rate unit"], "Per year")
        gen = self.csv_de(self.exportar(provedor="generico"))
        lin = dict(zip(gen[0], gen[1]))
        self.assertEqual(lin["start_date"], "2026-11-09")
        self.assertEqual(lin["worker_type"], "employee")
        self.assertEqual(lin["pay_rate"], "52000.00")
        st, r = self.exportar(provedor="adp")
        self.assertEqual(st, 400)

    def test_sensiveis_exigem_senha_e_sao_auditados(self):
        self.contratado()
        st, r = self.exportar(incluir_sensiveis=True)
        self.assertEqual(st, 403)
        st, r = self.exportar(incluir_sensiveis=True, senha="errada")
        self.assertEqual(st, 403)
        self.assertEqual(r["erro"], "Senha incorreta")
        n_falha = self.conn.execute("SELECT COUNT(*) FROM auditoria WHERE acao='exportar_folha_senha_incorreta'").fetchone()[0]
        self.assertEqual(n_falha, 2)
        linhas = self.csv_de(self.exportar(incluir_sensiveis=True, senha=SENHA))
        lin = dict(zip(linhas[0], linhas[1]))
        self.assertEqual(lin["SSN"], "212-55-1234")
        self.assertEqual(lin["Date of birth"], "04/12/1990")
        self.assertEqual(lin["Routing number"], "011000015")
        self.assertEqual(lin["Account number"], "123456789")
        aud = self.conn.execute("SELECT alvo FROM auditoria WHERE acao='exportar_folha'").fetchall()
        self.assertEqual(len(aud), 1)
        self.assertIn("sensiveis:sim", aud[0]["alvo"])
        self.assertIn("registros:1", aud[0]["alvo"])
        tudo = " ".join(str(tuple(r)) for r in self.conn.execute("SELECT * FROM auditoria").fetchall())
        for valor in ("212-55-1234", "212551234", "011000015", "123456789", "1990-04-12", SENHA):
            self.assertNotIn(valor, tudo)
        # o arquivo não fica gravado em lugar nenhum
        csvs = [os.path.join(r, f) for r, _, fs in os.walk(PASTA) for f in fs if f.endswith(".csv")]
        self.assertEqual(csvs, [])

    def test_limite_de_senha_errada(self):
        self.contratado()
        for _ in range(5):
            self.assertEqual(self.exportar(incluir_sensiveis=True, senha="x")[0], 403)
        st, _ = self.exportar(incluir_sensiveis=True, senha=SENHA)
        self.assertEqual(st, 429)

    def test_so_admin_exporta(self):
        self.contratado()
        self.assertEqual(self.exportar(gestor="joao")[0], 403)
        st, _ = self.req("GET", "/api/gestor/integracoes-rh/folha/contratacoes", gestor="joao")
        self.assertEqual(st, 403)

    def test_prestador_1099_em_arquivo_separado_com_w9(self):
        self.contratado()
        self.contratado(tipo="1099", nome="Jose Silva", email="jose@example.com")
        w2 = self.csv_de(self.exportar())
        self.assertEqual(len(w2), 2)
        self.assertNotIn("Jose", ",".join(w2[1]))
        c = self.csv_de(self.exportar(tipo="1099", incluir_sensiveis=True, senha=SENHA))
        self.assertEqual(len(c), 2)
        lin = dict(zip(c[0], c[1]))
        self.assertEqual(lin["Member type"], "Contractor (business)")
        self.assertEqual(lin["Legal name (W-9)"], "Jose Silva")
        self.assertEqual(lin["Business name"], "Lopez Cleaning LLC")
        self.assertEqual(lin["Federal tax classification"], "LLC (S)")
        self.assertEqual(lin["TIN type"], "EIN")
        self.assertEqual(lin["TIN"], "12-3456789")
        self.assertEqual(lin["Home address street 1"], "10 Main St")
        self.assertNotIn("SSN", c[0])
        self.assertNotIn("Date of birth", c[0])
        sem = self.csv_de(self.exportar(tipo="1099"))
        self.assertNotIn("TIN", sem[0])
        self.assertNotIn("12-3456789", ",".join(sem[1]))

    def test_filtros_previa_e_selecao(self):
        a, _ = self.contratado(inicio="2026-11-09")
        b, _ = self.contratado(nome="Ana Souza", email="ana@example.com", inicio="2026-12-15")
        self.contratado(nome="Lia Reis", email="lia@example.com", status="cancelado")
        st, r = self.req("GET", "/api/gestor/integracoes-rh/folha/contratacoes?de=2026-12-01", gestor="tony")
        self.assertEqual([x["id"] for x in r["contratacoes"]], [b])
        st, r = self.req("POST", "/api/gestor/integracoes-rh/folha/previa", {"provedor": "gusto", "ids": [a]},
                         gestor="tony")
        self.assertEqual(st, 200, r)
        self.assertEqual(r["w2"]["total"], 1)
        self.assertNotIn("SSN", r["w2"]["colunas"])
        self.assertIn("SSN", r["w2"]["sensiveis"])
        self.assertNotIn("212-55-1234", json.dumps(r))
        linhas = self.csv_de(self.exportar(ids=[b]))
        self.assertEqual(len(linhas), 2)
        self.assertIn("Ana", linhas[1])

    def test_mapa_de_colunas(self):
        self.contratado()
        st, r = self.req("POST", "/api/gestor/integracoes-rh/config", {"folha": {"mapas": {"gusto": {
            "ssn": "Social Security Number", "telefone": ""}}}}, gestor="tony")
        self.assertEqual(st, 200, r)
        self.assertEqual(r["folha"]["mapas"]["gusto"]["ssn"], "Social Security Number")
        cab = self.csv_de(self.exportar(incluir_sensiveis=True, senha=SENHA))[0]
        self.assertIn("Social Security Number", cab)
        self.assertNotIn("SSN", cab)
        self.assertNotIn("Phone number", cab)

    def test_injecao_de_formula_neutralizada(self):
        ob, cid = self.contratado()
        self.conn.execute("UPDATE onboardings SET oferta=? WHERE id=?", (json.dumps(
            {"tipo": "w2", "cargo": "=HYPERLINK(\"x\")", "data_inicio": "2026-11-09", "valor": 20, "unidade": "hora"}), ob))
        self.conn.commit()
        lin = self.csv_de(self.exportar())
        self.assertTrue(dict(zip(lin[0], lin[1]))["Job title"].startswith("'="))

    def test_isolamento_da_exportacao(self):
        self.contratado()
        self.contratado(nome="Bia Lima", email="bia@example.com", empresa=self.eb)
        linhas = self.csv_de(self.exportar(gestor="intruso"))
        self.assertEqual(len(linhas), 2)
        self.assertIn("Bia", linhas[1])
        self.assertNotIn("Maria", ",".join(linhas[1]))


# ============================================================ B. Checkr
class TestCheckr(Base):
    def test_config_mascarada_e_so_admin(self):
        r = self.configurar_checkr()
        self.assertEqual(r["checkr"]["chave_mascara"], "•••1111")
        self.assertNotIn(CHAVE_A, json.dumps(r))
        bruto = server.config_get(self.conn, "integracoes_rh:%d" % self.ea)
        self.assertNotIn(CHAVE_A, bruto)
        st, r = self.req("GET", "/api/gestor/integracoes-rh/config", gestor="tony")
        self.assertNotIn(CHAVE_A, json.dumps(r))
        self.assertTrue(r["checkr"]["webhook_url"].endswith("/api/integracoes/checkr/webhook"))
        self.assertEqual(self.req("GET", "/api/gestor/integracoes-rh/config", gestor="joao")[0], 403)
        st, r = self.req("POST", "/api/gestor/integracoes-rh/config", {"checkr": {"estado": "Connecticut"}},
                         gestor="tony", idioma="en")
        self.assertEqual(st, 400)
        self.assertEqual(r["erro"], "Invalid state: use the 2-letter code")
        # salvar de novo sem digitar a chave mantém a chave
        self.configurar_checkr(chave="")
        self.assertEqual(integracoes_rh.chave_checkr(self.conn, self.ea), CHAVE_A)
        st, r = self.req("POST", "/api/gestor/integracoes-rh/checkr/testar", {}, gestor="tony")
        self.assertEqual(r["pacotes"][0]["slug"], "tasker_standard")

    def test_pedido_cria_candidato_e_convite(self):
        self.configurar_checkr()
        cid = self.candidato()
        st, r = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="tony")
        self.assertEqual(st, 200, r)
        self.assertEqual(len(self.checkr.pedidos), 2)
        p1, p2 = self.checkr.pedidos
        self.assertEqual(p1["url"], "https://api.checkr.com/v1/candidates")
        self.assertEqual(p1["metodo"], "POST")
        self.assertEqual(p1["corpo"]["email"], "maria@example.com")
        self.assertEqual(p1["corpo"]["first_name"], "Maria")
        self.assertEqual(p1["corpo"]["last_name"], "Lopez")
        self.assertEqual(p1["corpo"]["custom_id"], "bussola-%d-%d" % (self.ea, cid))
        self.assertEqual(p1["auth"], "Basic " + base64.b64encode((CHAVE_A + ":").encode()).decode())
        self.assertEqual(p2["url"], "https://api.checkr.com/v1/invitations")
        self.assertEqual(p2["corpo"], {"candidate_id": "cand_1", "package": "tasker_standard",
                                       "work_locations": [{"country": "US", "state": "CT", "city": "Hartford"}]})
        self.assertEqual(r["status_atual"], "convite_enviado")
        self.assertEqual(r["verificacoes"][0]["link"], "https://dashboard.checkr.com/candidates/cand_1")
        ev = self.conn.execute("SELECT texto FROM eventos WHERE candidato_id=? ORDER BY id DESC", (cid,)).fetchone()
        self.assertEqual(ev["texto"], "Verificação de antecedentes solicitada (Checkr, pacote tasker_standard)")
        # um pedido aberto por vez
        st, r = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="tony")
        self.assertEqual(st, 409)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM auditoria WHERE acao='checkr_pedido'").fetchone()[0], 1)

    def test_pedido_exige_proposta_config_e_admin(self):
        cid = self.candidato(etapa="entrevista")
        st, r = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="tony",
                         idioma="en")
        self.assertEqual(st, 400)
        self.assertEqual(r["erro"], "Set up Checkr in Settings before ordering a background check")
        self.configurar_checkr()
        st, r = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="tony",
                         idioma="es")
        self.assertEqual(st, 400)
        self.assertEqual(r["erro"], "Envía la oferta antes de solicitar la verificación de antecedentes")
        st, _ = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="joao")
        self.assertEqual(st, 403)
        self.assertEqual(self.checkr.pedidos, [])

    def test_erro_da_checkr_traduzido(self):
        self.configurar_checkr()
        cid = self.candidato()
        self.checkr.falhar = 422
        st, r = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="tony",
                         idioma="en")
        self.assertEqual(st, 502)
        self.assertEqual(r["erro"], "Checkr error: Package not found")
        self.checkr.falhar = 401
        st, r = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="tony",
                         idioma="en")
        self.assertEqual(r["erro"], "Checkr rejected the API key. Check it in Settings.")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM checkr_verificacoes").fetchone()[0], 0)

    def test_staging(self):
        self.configurar_checkr(ambiente="staging")
        cid = self.candidato()
        st, r = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="tony")
        self.assertTrue(self.checkr.pedidos[0]["url"].startswith("https://api.checkr-staging.com/v1/"))
        self.assertTrue(r["verificacoes"][0]["link"].startswith("https://dashboard.checkr-staging.com/"))

    def _pedir(self, cid=None, gestor="tony"):
        cid = cid or self.candidato()
        st, r = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor=gestor)
        self.assertEqual(st, 200, r)
        v = self.conn.execute("SELECT * FROM checkr_verificacoes WHERE candidato_id=?", (cid,)).fetchone()
        return cid, v

    def test_webhook_assinatura_valida_e_status(self):
        self.configurar_checkr(exigir=True)
        cid, v = self._pedir()
        cand_ck = v["checkr_candidato_id"]
        st, r = self.req("GET", "/api/gestor/integracoes-rh/checkr/aviso?candidato=%d" % cid, gestor="tony")
        self.assertTrue(r["avisar"])
        st, r = self.webhook({"id": "ev1", "type": "invitation.completed",
                              "data": {"object": {"id": v["convite_id"], "candidate_id": cand_ck, "status": "completed"}}})
        self.assertEqual(st, 200, r)
        self.assertEqual(self.conn.execute("SELECT status FROM checkr_verificacoes").fetchone()[0], "pendente")
        st, r = self.webhook({"id": "ev2", "type": "report.completed",
                              "data": {"object": {"id": "rep_1", "object": "report", "candidate_id": cand_ck,
                                                  "status": "complete", "result": "clear"}}})
        self.assertEqual(st, 200, r)
        linha = self.conn.execute("SELECT * FROM checkr_verificacoes").fetchone()
        self.assertEqual((linha["status"], linha["resultado"], linha["relatorio_id"]), ("clear", "clear", "rep_1"))
        self.assertTrue(linha["concluido_em"])
        textos = [e["texto"] for e in self.conn.execute("SELECT texto FROM eventos WHERE candidato_id=?", (cid,))]
        self.assertIn("Verificação de antecedentes (Checkr): em andamento", textos)
        self.assertIn("Verificação de antecedentes (Checkr): clear (sem apontamentos)", textos)
        self.assertIn("Verificação de antecedentes concluída: aviso a 3 administrador(es)", textos)
        assuntos = {e["para"]: e["assunto"] for e in self.enviados}
        self.assertEqual(set(assuntos), {"tony@example.com", "carine@example.com", "ana@example.com"})
        self.assertEqual(assuntos["carine@example.com"], "Background check complete: Maria Lopez")
        self.assertEqual(assuntos["ana@example.com"], "Verificación de antecedentes completada: Maria Lopez")
        self.assertEqual(assuntos["tony@example.com"], "Verificação de antecedentes concluída: Maria Lopez")
        self.assertIn("https://dashboard.checkr.com/candidates/" + cand_ck,
                      [e for e in self.enviados if e["para"] == "carine@example.com"][0]["corpo"])
        st, r = self.req("GET", "/api/gestor/integracoes-rh/checkr/aviso?candidato=%d" % cid, gestor="tony")
        self.assertFalse(r["avisar"])
        # evento repetido não processa de novo
        n = len(self.enviados)
        st, r = self.webhook({"id": "ev2", "type": "report.completed",
                              "data": {"object": {"id": "rep_1", "candidate_id": cand_ck, "status": "complete",
                                                  "result": "clear"}}})
        self.assertEqual(st, 200)
        self.assertTrue(r.get("repetido"))
        self.assertEqual(len(self.enviados), n)

    def test_consider_suspenso_cancelado(self):
        self.configurar_checkr()
        cid, v = self._pedir()
        ck = v["checkr_candidato_id"]
        self.webhook({"id": "a", "type": "report.suspended", "data": {"object": {"candidate_id": ck, "status": "suspended"}}})
        self.assertEqual(self.conn.execute("SELECT status FROM checkr_verificacoes").fetchone()[0], "suspenso")
        self.webhook({"id": "b", "type": "report.completed",
                      "data": {"object": {"candidate_id": ck, "status": "complete", "result": "consider"}}})
        self.assertEqual(self.conn.execute("SELECT status FROM checkr_verificacoes").fetchone()[0], "consider")
        corpo = [e for e in self.enviados if e["para"] == "carine@example.com"][0]["corpo"]
        self.assertIn("adverse action", corpo)
        self.assertIn(integracoes_rh.FCRA_URL, corpo)
        self.webhook({"id": "c", "type": "report.canceled", "data": {"object": {"candidate_id": ck, "status": "canceled"}}})
        self.assertEqual(self.conn.execute("SELECT status FROM checkr_verificacoes").fetchone()[0], "cancelado")
        # depois de cancelada, pode pedir de novo
        st, _ = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="tony")
        self.assertEqual(st, 200)

    def test_webhook_assinatura_invalida(self):
        self.configurar_checkr()
        cid, v = self._pedir()
        ev = {"id": "x1", "type": "report.completed",
              "data": {"object": {"candidate_id": v["checkr_candidato_id"], "status": "complete", "result": "clear"}}}
        st, _ = self.webhook(ev, assinatura="0" * 64)
        self.assertEqual(st, 401)
        st, _ = self.webhook(ev, assinatura="")
        self.assertEqual(st, 401)
        st, _ = self.webhook(ev, chave=CHAVE_B)
        self.assertEqual(st, 401)
        self.assertEqual(self.conn.execute("SELECT status FROM checkr_verificacoes").fetchone()[0], "convite_enviado")
        self.assertEqual(self.enviados, [])
        st, _ = self.webhook({"id": "x2", "type": "report.completed", "data": {"object": {"candidate_id": "desconhecido"}}})
        self.assertEqual(st, 404)
        st, _ = self.req("POST", "/api/integracoes/checkr/webhook", bruto=b"nao e json",
                         cab_extra={"X-Checkr-Signature": "x"})
        self.assertEqual(st, 400)

    def test_isolamento_checkr(self):
        self.configurar_checkr()
        self.configurar_checkr(chave=CHAVE_B, gestor="intruso")
        cid, v = self._pedir()
        st, _ = self.req("GET", "/api/gestor/integracoes-rh/checkr/candidato/%d" % cid, gestor="intruso")
        self.assertEqual(st, 404)
        st, _ = self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid, {}, gestor="intruso")
        self.assertEqual(st, 404)
        st, _ = self.req("GET", "/api/gestor/integracoes-rh/checkr/aviso?candidato=%d" % cid, gestor="intruso")
        self.assertEqual(st, 404)
        # webhook assinado com a chave de outra empresa não altera a verificação desta
        st, _ = self.webhook({"id": "i1", "type": "report.completed", "data": {"object": {
            "candidate_id": v["checkr_candidato_id"], "status": "complete", "result": "clear"}}}, chave=CHAVE_B)
        self.assertEqual(st, 401)
        st, r = self.req("GET", "/api/gestor/integracoes-rh/config", gestor="intruso")
        self.assertEqual(r["checkr"]["chave_mascara"], "•••2222")
        # o pedido usa a chave da própria empresa
        cid_b = self.candidato(nome="Bia Lima", email="bia@example.com", empresa=self.eb)
        self.req("POST", "/api/gestor/integracoes-rh/checkr/candidato/%d/pedir" % cid_b, {}, gestor="intruso")
        self.assertEqual(self.checkr.pedidos[-1]["auth"], "Basic " + base64.b64encode((CHAVE_B + ":").encode()).decode())

    def test_ficha_mostra_everify_para_w2(self):
        self.configurar_checkr()
        _, cid = self.contratado()
        st, r = self.req("GET", "/api/gestor/integracoes-rh/checkr/candidato/%d" % cid, gestor="joao")
        self.assertEqual(st, 200)
        self.assertTrue(r["tem_w2"])
        self.assertEqual(r["everify_url"], "https://www.e-verify.gov/")
        self.assertFalse(r["pode_pedir"])  # não é administrador


class TestTextos(unittest.TestCase):
    def test_sem_travessoes(self):
        for arq in ("integracoes_rh.py", "teste_integracoes_rh.py", "public/js/gestor-integracoes-rh.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)

    def test_js_trilingue(self):
        with open(os.path.join(AQUI, "public", "js", "gestor-integracoes-rh.js"), encoding="utf-8") as f:
            js = f.read()
        blocos = re.split(r"Object\.assign\(I18N_GESTOR\.(pt|en|es), \{", js)
        chaves = {}
        for i in range(1, len(blocos), 2):
            chaves[blocos[i]] = set(re.findall(r"\b(irh_\w+):", blocos[i + 1].split("\n});")[0]))
        self.assertEqual(set(chaves), {"pt", "en", "es"})
        self.assertEqual(chaves["pt"], chaves["en"])
        self.assertEqual(chaves["pt"], chaves["es"])

    def test_erros_traduzidos(self):
        import erros_i18n
        with open(os.path.join(AQUI, "integracoes_rh.py"), encoding="utf-8") as f:
            codigo = f.read()
        msgs = set(re.findall(r'ErroIntegracao\(\d+, "([^"%]+)"\)', codigo))
        msgs |= set(re.findall(r'\{"erro": "([^"%]+)"\}', codigo))
        self.assertGreater(len(msgs), 10)
        for m in msgs:
            self.assertNotEqual(erros_i18n.traduzir(m, "en"), m, "%s sem tradução en" % m)
            self.assertTrue(erros_i18n.ERROS.get(m, {}).get("es") or erros_i18n.traduzir(m, "es") != m, "%s sem tradução es" % m)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=2)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
