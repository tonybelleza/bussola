"""
Testes do onboarding de novos contratados (onboarding.py): proposta e idioma do
e-mail, etapas do portal, PDF de assinatura com certificado e hash, criptografia
dos dados sensíveis e máscara, "revelar" só do administrador e auditado, acesso
aos arquivos (outra empresa e anônimo não baixam), routing number (ABA),
formulários oficiais (formularios.py), conclusão com aviso aos gestores,
lembretes (no máximo um por dia), isolamento entre empresas e trava da chave.

Uso:  python3 teste_onboarding.py

Banco, chave e arquivos numa pasta temporária. Nenhum e-mail sai da máquina: o
envio SMTP é substituído por um gravador. Usa o formularios.py real; se ele não
existir, um módulo falso com a mesma API.
"""
import base64
import glob
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import types
import unittest
import urllib.error
import urllib.request
import zlib
from datetime import date, datetime, timedelta, timezone
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="onboarding-teste-")
for arquivo in glob.glob(os.path.join(AQUI, "*.py")):
    if not os.path.basename(arquivo).startswith("teste_"):
        shutil.copy(arquivo, PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs", "forms")):
    shutil.copytree(os.path.join(AQUI, "docs", "forms"), os.path.join(PASTA, "docs", "forms"))
sys.path.insert(0, PASTA)
os.environ.pop("BUSSOLA_CHAVE_DADOS", None)

FORMULARIOS_REAIS = os.path.exists(os.path.join(PASTA, "formularios.py")) and os.path.isdir(os.path.join(PASTA, "docs", "forms"))
if not FORMULARIOS_REAIS:
    # módulo falso com a mesma API (só quando o formularios.py não está disponível)
    falso = types.ModuleType("formularios")

    class ErroFormulario(ValueError):
        def __init__(self, erros):
            self.erros = list(erros)
            ValueError.__init__(self, ",".join(self.erros))

    def _c(chave, tipo="text", obrig=True):
        return {"chave": chave, "tipo": tipo, "obrigatorio": obrig, "opcoes": [],
                "rotulo": {"pt": chave, "en": chave, "es": chave}, "ajuda": {"pt": "", "en": "", "es": ""}}

    base = [_c("primeiro_nome"), _c("sobrenome"), _c("endereco"), _c("cidade"), _c("estado"), _c("cep"), _c("ssn", "ssn")]
    falso.CAMPOS = {"w4": base + [_c("estado_civil")], "ctw4": base + [_c("codigo_retencao")],
                    "i9": base + [_c("data_nascimento", "date"), _c("status_cidadania")], "w9": [_c("nome"), _c("ssn", "ssn")]}
    falso.CAMPOS_EMPREGADOR = {"w4": [_c("ein_empregador", "ein", False)]}
    falso.CAMPOS_I9_SECAO2 = [_c("lista"), _c("primeiro_dia", "date"), _c("representante_nome"), _c("empresa_nome"),
                              _c("empresa_endereco")]
    falso.MENSAGENS_ERRO = {"obrigatorio": {"pt": "Campo obrigatório.", "en": "This field is required.", "es": "Obligatorio."},
                            "formato": {"pt": "Formato inválido.", "en": "Invalid format.", "es": "Formato no válido."}}
    falso.ErroFormulario = ErroFormulario

    def validar(tipo, dados):
        campos = falso.CAMPOS_I9_SECAO2 if tipo == "i9_secao2" else falso.CAMPOS[tipo]
        erros = ["%s:obrigatorio" % c["chave"] for c in campos if c["obrigatorio"] and not dados.get(c["chave"])]
        if dados.get("ssn") and len(re.sub(r"\D", "", dados["ssn"])) != 9:
            erros.append("ssn:formato")
        return erros

    def preencher(tipo, dados, assinatura_png=None, data_assinatura=None, nome_assinatura=None):
        if validar(tipo, dados):
            raise ErroFormulario(validar(tipo, dados))
        return b"%PDF-1.4 fake " + tipo.encode()

    def preencher_i9_secao2(pdf_bytes, dados, assinatura_png=None):
        return pdf_bytes + b" secao2"

    falso.validar = validar
    falso.preencher = preencher
    falso.preencher_i9_secao2 = preencher_i9_secao2
    falso.mascarar_ssn = lambda s: "***-**-" + re.sub(r"\D", "", s)[-4:]
    sys.modules["formularios"] = falso

import empresas  # noqa: E402
import onboarding  # noqa: E402
import server  # noqa: E402

onboarding.ENVIO_EM_SEGUNDO_PLANO = False
server.Handler.log_message = lambda *a: None
TRACOS = re.compile("[\u2013\u2014]")

# PNG 1x1 válido, repetido em tamanho suficiente para passar no mínimo de bytes
_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def png_assinatura():
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (300, 100), (255, 255, 255, 0))
        d = ImageDraw.Draw(img)
        d.line([(10, 80), (80, 20), (150, 70), (290, 30)], fill=(16, 27, 55, 255), width=4)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        dados = buf.getvalue()
    except ImportError:
        dados = _PNG + b"\x00" * 300
    return "data:image/png;base64," + base64.b64encode(dados).decode()


ASSINATURA = png_assinatura()
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 2000
W4_OK = {"primeiro_nome": "Maria", "sobrenome": "Lopez", "endereco": "10 Main St", "cidade": "Hartford", "estado": "CT",
         "cep": "06103", "ssn": "212-55-1234", "estado_civil": "solteiro", "codigo_retencao": "A",
         "filhos_menores_17": "1", "outros_dependentes": "0"}
I9_OK = {"primeiro_nome": "Maria", "sobrenome": "Lopez", "endereco": "10 Main St", "cidade": "Hartford", "estado": "CT",
         "cep": "06103", "ssn": "212-55-1234", "data_nascimento": "1990-04-12", "status_cidadania": "cidadao",
         "email": "maria@example.com", "telefone": "8605550101"}


def texto_pdf(dados):
    """Texto de um PDF (pypdf quando existe; senão, os fluxos descomprimidos)."""
    try:
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(dados)).pages)
    except ImportError:
        partes = []
        for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", dados, re.S):
            try:
                partes.append(zlib.decompress(m.group(1)).decode("latin-1"))
            except zlib.error:
                pass
        return "\n".join(partes)


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
        shutil.rmtree(os.path.join(server.UPLOAD_DIR, "onboarding"), ignore_errors=True)
        chave = os.path.join(server.BASE_DIR, "chave_dados.key")
        if os.path.exists(chave):
            os.remove(chave)
        onboarding.esquecer_chave()
        onboarding.zerar_limites()
        server.init_db()
        self.conn = c = server.db()
        self.ea, _ = empresas.criar_empresa(c, "Belleza's Home Services CT")
        self.eb, _ = empresas.criar_empresa(c, "Outra Empresa")
        self.cargo = c.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Cleaning Tech', ?)", (self.ea,)).lastrowid
        self.vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'House Cleaning Technician',"
                              " 'aberta', ?)", (self.cargo, self.ea)).lastrowid
        self.gestores = {}
        for login, idioma, empresa, admin in (("tony", "pt", self.ea, 1), ("carine", "en", self.ea, 1),
                                              ("ana", "es", self.ea, 1), ("joao", "pt", self.ea, 0),
                                              ("intruso", "pt", self.eb, 1)):
            gid = c.execute("INSERT INTO gestores (nome, login, senha, email, is_admin, aprovado, empresa_id, idioma)"
                            " VALUES (?,?,?,?,?,1,?,?)", (login.title(), login, "x", login + "@example.com", admin,
                                                          empresa, idioma)).lastrowid
            c.execute("INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)", ("sess-" + login, gid))
            self.gestores[login] = gid
        server.config_set(c, "smtp_host", "smtp.teste")
        server.config_set(c, "url_publica", "https://rh.exemplo.com")
        c.commit()
        onboarding.salvar_config(c, self.ea, dict(onboarding.config(c, self.ea), empregador_nome="Belleza's Home Services LLC",
                                                  empregador_endereco="100 Main St", empregador_cidade_estado_cep="Hartford, CT 06103",
                                                  empregador_ein="12-3456789", empregador_contato="Carine",
                                                  empregador_telefone="8605550100"))
        self.enviados = []
        self._original = server.enviar_email

        def gravar(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt"):
            self.enviados.append({"para": para, "assunto": assunto, "corpo": corpo, "html": html or ""})
            return True, "enviado"

        server.enviar_email = gravar

    def tearDown(self):
        server.enviar_email = self._original
        self.conn.close()

    def candidato(self, idioma="es", empresa=None, email="maria@example.com", nome="Maria Lopez"):
        c = self.conn
        empresa = empresa or self.ea
        cid = c.execute("INSERT INTO candidatos (token, nome, email, local, telefone, idioma, empresa_id)"
                        " VALUES (?,?,?,?,?,?,?)", ("tok-" + email, nome, email, "", "+18605550101", idioma, empresa)).lastrowid
        if empresa == self.ea:
            c.execute("INSERT INTO candidaturas (candidato_id, vaga_id, etapa) VALUES (?,?,'entrevista')", (cid, self.vaga))
        c.commit()
        return c.execute("SELECT * FROM candidatos WHERE id=?", (cid,)).fetchone()

    def req(self, metodo, caminho, dados=None, gestor=None, idioma=None, bruto=None):
        cab = {"Content-Type": "application/json", "User-Agent": "TesteOnboarding/1.0"}
        if gestor:
            cab["X-Gestor-Token"] = "sess-" + gestor
        if idioma:
            cab["X-Idioma"] = idioma
        corpo = bruto if bruto is not None else (json.dumps(dados).encode() if dados is not None else None)
        if bruto is not None:
            cab["Content-Type"] = "application/octet-stream"
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=cab)
        try:
            with urllib.request.urlopen(r) as resp:
                conteudo = resp.read()
                if resp.headers.get("Content-Type", "").startswith("application/json"):
                    return resp.status, json.loads(conteudo or b"{}")
                return resp.status, conteudo
        except urllib.error.HTTPError as e:
            conteudo = e.read()
            try:
                return e.code, json.loads(conteudo or b"{}")
            except ValueError:
                return e.code, conteudo

    def oferta(self, cand, tipo="w2", gestor="tony", **extra):
        d = {"candidato_id": cand["id"], "tipo": tipo, "cargo": "House Cleaning Technician", "data_inicio": "2026-11-09",
             "valor": "22", "unidade": "hora", "horario": "Mon to Fri, 8am to 4pm",
             "prazo": (date.today() + timedelta(days=7)).isoformat(), "dirige": False}
        d.update(extra)
        st, r = self.req("POST", "/api/gestor/onboarding/oferta", d, gestor=gestor)
        self.assertEqual(st, 200, r)
        return self.conn.execute("SELECT * FROM onboardings WHERE id=?", (r["id"],)).fetchone()

    def portal(self, ob, acao="", metodo="GET", dados=None, bruto=None, idioma=None):
        return self.req(metodo, "/api/onboarding/" + ob["token"] + (("/" + acao) if acao else ""), dados, idioma=idioma,
                        bruto=bruto)

    def consentir(self, ob):
        st, d = self.portal(ob, "consentimento", "POST", {"aceito": True, "idioma": "es"})
        self.assertEqual(st, 200, d)
        return d

    def assinar(self, ob, modelo_id, **extra):
        corpo = {"modelo_id": modelo_id, "nome": "Maria Lopez", "assinatura": ASSINATURA, "aceite": True,
                 "leu_tudo": True, "idioma": "es"}
        corpo.update(extra)
        return self.portal(ob, "assinar", "POST", corpo)

    def dados_pessoais(self, ob, **extra):
        corpo = {"nome_legal": "Maria Lopez", "endereco": "10 Main St", "cidade": "Hartford", "estado": "CT",
                 "cep": "06103", "telefone": "8605550101", "email": "maria@example.com", "nascimento": "1990-04-12",
                 "contato_nome": "Jose Lopez", "contato_relacao": "Brother", "contato_telefone": "8605550102",
                 "tamanho": "M"}
        corpo.update(extra)
        return self.portal(ob, "dados", "POST", corpo)

    def completar(self, ob):
        """Faz todas as etapas (menos a revisão) de um onboarding W-2."""
        d = self.consentir(ob)
        st, d = self.assinar(ob, d["modelo_oferta"]["id"])
        self.assertEqual(st, 200, d)
        for doc in d["documentos"]:
            extra = {"declaracao": "I will treat every home with care and respect."} if doc["requer_declaracao"] else {}
            st, d = self.assinar(ob, doc["id"], **extra)
            self.assertEqual(st, 200, d)
        st, d = self.dados_pessoais(ob)
        self.assertEqual(st, 200, d)
        for f in d["formularios"]:
            dados = {c["chave"]: (I9_OK if f["tipo"] == "i9" else W4_OK).get(c["chave"]) for c in f["campos"]}
            dados = {k: v for k, v in dados.items() if v is not None}
            st, r = self.portal(ob, "formulario/" + f["tipo"], "POST",
                                {"dados": dados, "nome": "Maria Lopez", "assinatura": ASSINATURA, "aceite": True})
            self.assertEqual(st, 200, (f["tipo"], r))
        for cat in ("id_frente", "i9_lista_a"):
            st, d = self.portal(ob, "arquivo?categoria=%s&nome=foto.jpg" % cat, "POST", bruto=JPEG)
            self.assertEqual(st, 200, d)
        st, d = self.portal(ob, "pagamento", "POST", {"metodo": "deposito", "banco": "Chase", "tipo_conta": "corrente",
                                                      "routing": "011000015", "conta": "123456789",
                                                      "conta_confirmacao": "123456789"})
        self.assertEqual(st, 200, d)
        return d


class TestOferta(Base):
    def test_cria_envia_no_idioma_e_move_para_proposta(self):
        cand = self.candidato("es")
        ob = self.oferta(cand)
        self.assertEqual(ob["status"], "enviado")
        self.assertGreaterEqual(len(ob["token"]), 40)
        e = [x for x in self.enviados if x["para"] == "maria@example.com"]
        self.assertEqual(len(e), 1)
        self.assertIn("tu oferta de trabajo", e[0]["assunto"])
        self.assertIn("/onboarding?t=" + ob["token"], e[0]["corpo"])
        self.assertIn("House Cleaning Technician", e[0]["corpo"])
        etapa = self.conn.execute("SELECT etapa FROM candidaturas WHERE candidato_id=?", (cand["id"],)).fetchone()[0]
        self.assertEqual(etapa, "proposta")
        audit = self.conn.execute("SELECT acao FROM auditoria WHERE acao='onboarding_enviado'").fetchall()
        self.assertEqual(len(audit), 1)
        # um onboarding ativo por candidato
        st, r = self.req("POST", "/api/gestor/onboarding/oferta", {"candidato_id": cand["id"], "tipo": "w2", "cargo": "X",
                                                                  "data_inicio": "2026-11-09", "valor": 20, "unidade": "hora",
                                                                  "prazo": date.today().isoformat()}, gestor="tony")
        self.assertEqual(st, 409)

    def test_email_em_ingles_e_portugues(self):
        self.oferta(self.candidato("en", email="a@example.com"))
        self.oferta(self.candidato("pt", email="b@example.com"))
        self.assertIn("your job offer", [x for x in self.enviados if x["para"] == "a@example.com"][0]["assunto"])
        self.assertIn("sua proposta", [x for x in self.enviados if x["para"] == "b@example.com"][0]["assunto"])

    def test_so_admin_envia_e_valida(self):
        cand = self.candidato()
        st, _ = self.req("POST", "/api/gestor/onboarding/oferta", {"candidato_id": cand["id"]}, gestor="joao")
        self.assertEqual(st, 403)
        st, r = self.req("POST", "/api/gestor/onboarding/oferta", {"candidato_id": cand["id"], "tipo": "w2", "cargo": "X",
                                                                  "data_inicio": "2026-11-09", "valor": 0, "unidade": "hora",
                                                                  "prazo": date.today().isoformat()}, gestor="tony", idioma="en")
        self.assertEqual(st, 400)
        self.assertEqual(r["erro"], "Invalid pay amount")

    def test_documentos_padrao_por_tipo(self):
        w2 = self.oferta(self.candidato(email="w2@example.com"))
        c1099 = self.oferta(self.candidato(email="c@example.com"), tipo="1099")
        p1 = onboarding.plano(self.conn, w2)
        p2 = onboarding.plano(self.conn, c1099)
        self.assertEqual(p1["modelo_oferta"]["chave"], "offer_letter")
        self.assertEqual(p2["modelo_oferta"]["chave"], "engagement_offer")
        self.assertEqual([m["chave"] for m in p1["documentos"]],
                         ["interest_agreement", "employee_handbook", "core_values", "employment_contract"])
        self.assertEqual([m["chave"] for m in p2["documentos"]], ["core_values", "contractor_agreement"])
        self.assertEqual(p1["formularios"], ["w4", "i9", "ctw4"])
        self.assertEqual(p2["formularios"], ["w9"])


class TestPortal(Base):
    def test_consentimento_antes_de_tudo(self):
        ob = self.oferta(self.candidato())
        st, d = self.portal(ob)
        self.assertEqual(st, 200)
        self.assertFalse(d["consentimento"])
        self.assertIn("ESIGN", d["textos_consentimento"]["en"])
        st, r = self.dados_pessoais(ob)
        self.assertEqual(st, 400)
        d = self.consentir(ob)
        self.assertTrue(d["consentimento"])
        cons = json.loads(self.conn.execute("SELECT consentimento FROM onboardings WHERE id=?", (ob["id"],)).fetchone()[0])
        self.assertEqual(cons["ip"], "127.0.0.1")
        self.assertEqual(cons["ua"], "TesteOnboarding/1.0")
        self.assertIn("UETA", cons["texto"])

    def test_token_invalido_e_limite(self):
        st, _ = self.req("GET", "/api/onboarding/" + "x" * 43)
        self.assertEqual(st, 404)
        for _ in range(25):
            self.req("GET", "/api/onboarding/" + "y" * 43)
        st, _ = self.req("GET", "/api/onboarding/" + "z" * 43)
        self.assertEqual(st, 429)

    def test_assinatura_gera_pdf_com_certificado_e_hash(self):
        cand = self.candidato()
        ob = self.oferta(cand)
        d = self.consentir(ob)
        mid = d["modelo_oferta"]["id"]
        st, r = self.assinar(ob, mid, leu_tudo=False)
        self.assertEqual(st, 400)
        st, r = self.assinar(ob, mid, assinatura="data:image/png;base64,AAAA")
        self.assertEqual(st, 400)
        st, d = self.assinar(ob, mid)
        self.assertEqual(st, 200, d)
        self.assertTrue(d["modelo_oferta"]["assinado"])
        doc = self.conn.execute("SELECT * FROM onboarding_docs WHERE onboarding_id=? AND tipo='assinatura'", (ob["id"],)).fetchone()
        caminho = os.path.join(server.UPLOAD_DIR, doc["arquivo"])
        self.assertTrue(caminho.startswith(os.path.join(server.UPLOAD_DIR, "onboarding", str(ob["id"]))))
        with open(caminho, "rb") as f:
            self.assertFalse(f.read().startswith(b"%PDF"))           # cifrado em disco
        pdf = onboarding.ler_arquivo(self.conn, doc["arquivo"])
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertEqual(hashlib.sha256(pdf).hexdigest(), doc["sha256"])
        texto = texto_pdf(pdf).replace("\n", " ")
        self.assertIn("Electronic Signature Certificate", texto)
        self.assertIn(doc["sha256_texto"][:16], texto.replace(" ", ""))
        self.assertIn("127.0.0.1", texto)
        self.assertIn("maria@example.com", texto)
        # a carta de proposta assinada move para Contratado
        etapa = self.conn.execute("SELECT etapa FROM candidaturas WHERE candidato_id=?", (cand["id"],)).fetchone()[0]
        self.assertEqual(etapa, "contratado")
        # o dono do token baixa o próprio PDF
        st, corpo = self.portal(ob, "arquivo/%d" % doc["id"])
        self.assertEqual(st, 200)
        self.assertTrue(corpo.startswith(b"%PDF"))

    def test_declaracao_obrigatoria_nos_valores(self):
        ob = self.oferta(self.candidato())
        d = self.consentir(ob)
        valores = [x for x in d["documentos"] if x["requer_declaracao"]][0]
        st, r = self.assinar(ob, valores["id"])
        self.assertEqual(st, 400)
        st, r = self.assinar(ob, valores["id"], declaracao="I will be reliable and careful in every home.")
        self.assertEqual(st, 200, r)
        self.assertIn("Tu declaración", valores["textos"]["es"])

    def test_variaveis_preenchidas(self):
        ob = self.oferta(self.candidato())
        d = self.consentir(ob)
        txt = d["modelo_oferta"]["textos"]["en"]
        self.assertIn("House Cleaning Technician", txt)
        self.assertIn("November 9, 2026", txt)
        self.assertIn("$22.00 per hour", txt)
        self.assertNotIn("{{", txt)
        self.assertIn("Template provided by Bússola", txt)

    def test_dados_validacao_e_criptografia(self):
        ob = self.oferta(self.candidato(), dirige=True)
        self.consentir(ob)
        st, r = self.dados_pessoais(ob, cep="abc", nascimento="")
        self.assertEqual(st, 400)
        self.assertIn("cep", r["campos"])
        self.assertIn("nascimento", r["campos"])
        self.assertIn("cnh_numero", r["campos"])
        st, d = self.dados_pessoais(ob, cnh_numero="123456789", cnh_estado="ct")
        self.assertEqual(st, 200, d)
        bruto = self.conn.execute("SELECT * FROM onboardings WHERE id=?", (ob["id"],)).fetchone()
        tudo = json.dumps(dict(bruto))
        self.assertNotIn("1990-04-12", tudo)
        self.assertNotIn("123456789", tudo)
        sens = onboarding.sensiveis(self.conn, bruto)
        self.assertEqual(sens["nascimento"], "1990-04-12")
        self.assertEqual(sens["cnh_numero"], "123456789")
        self.assertEqual(d["dados"]["cnh_numero_mascara"], "•••6789")
        self.assertEqual(d["dados"]["nascimento_mascara"], "••/••/••••")
        self.assertNotIn("1990-04-12", json.dumps(d))
        # editar sem reenviar os sensíveis mantém os valores
        st, d = self.portal(ob, "dados", "POST", {"telefone": "8605559999"})
        self.assertEqual(st, 200, d)
        self.assertEqual(onboarding.sensiveis(self.conn, self.conn.execute("SELECT * FROM onboardings WHERE id=?", (ob["id"],)).fetchone())["cnh_numero"], "123456789")

    def test_routing_aba(self):
        self.assertTrue(onboarding.aba_valido("011000015"))
        self.assertTrue(onboarding.aba_valido("021000021"))
        self.assertFalse(onboarding.aba_valido("123456789"))
        self.assertFalse(onboarding.aba_valido("01100001"))
        self.assertFalse(onboarding.aba_valido("000000000"))
        ob = self.oferta(self.candidato())
        self.consentir(ob)
        st, r = self.portal(ob, "pagamento", "POST", {"metodo": "deposito", "banco": "Chase", "tipo_conta": "corrente",
                                                      "routing": "123456789", "conta": "1234", "conta_confirmacao": "1234"},
                            idioma="en")
        self.assertEqual(st, 400)
        self.assertEqual(r["campos"], ["routing"])
        self.assertIn("routing", r["erro"].lower())
        st, r = self.portal(ob, "pagamento", "POST", {"metodo": "deposito", "banco": "Chase", "tipo_conta": "corrente",
                                                      "routing": "011000015", "conta": "12345678", "conta_confirmacao": "1234"})
        self.assertEqual(r["campos"], ["conta_confirmacao"])
        st, d = self.portal(ob, "pagamento", "POST", {"metodo": "deposito", "banco": "Chase", "tipo_conta": "corrente",
                                                      "routing": "011000015", "conta": "12345678", "conta_confirmacao": "12345678"})
        self.assertEqual(st, 200, d)
        self.assertEqual(d["pagamento"]["conta_mascara"], "•••5678")
        self.assertNotIn("12345678", json.dumps(dict(self.conn.execute("SELECT * FROM onboardings WHERE id=?", (ob["id"],)).fetchone())))
        st, r = self.portal(ob, "pagamento", "POST", {"metodo": "provedor"})
        self.assertEqual(st, 400)   # método não aceito nesta proposta

    def test_upload_tipos_e_tamanho(self):
        ob = self.oferta(self.candidato())
        self.consentir(ob)
        st, r = self.portal(ob, "arquivo?categoria=id_frente&nome=a.exe", "POST", bruto=b"MZ" + b"0" * 100)
        self.assertEqual(st, 400)
        st, r = self.portal(ob, "arquivo?categoria=qualquer&nome=a.jpg", "POST", bruto=JPEG)
        self.assertEqual(st, 400)
        heic = b"\x00\x00\x00\x18ftypheic" + b"0" * 100
        st, d = self.portal(ob, "arquivo?categoria=id_frente&nome=a.heic", "POST", bruto=heic)
        self.assertEqual(st, 200, d)
        self.assertEqual(d["arquivos"][0]["mime"], "image/heic")
        doc_id = d["arquivos"][0]["id"]
        st, d = self.portal(ob, "arquivo/%d" % doc_id, "DELETE")
        self.assertEqual(st, 200)
        self.assertEqual(d["arquivos"], [])

    def test_formularios_oficiais(self):
        ob = self.oferta(self.candidato())
        d = self.consentir(ob)
        f = [x for x in d["formularios"] if x["tipo"] == "w4"][0]
        self.assertTrue(f["campos"])
        st, r = self.portal(ob, "formulario/w4", "POST", {"dados": {"primeiro_nome": "Maria"}, "nome": "Maria Lopez",
                                                          "assinatura": ASSINATURA, "aceite": True})
        self.assertEqual(st, 400)
        self.assertIn("ssn", r["campos"])
        self.assertIn("ssn", r["mensagens"])
        dados = {c["chave"]: W4_OK[c["chave"]] for c in f["campos"] if c["chave"] in W4_OK}
        st, d = self.portal(ob, "formulario/w4", "POST", {"dados": dados, "nome": "Maria Lopez", "assinatura": ASSINATURA,
                                                          "aceite": True})
        self.assertEqual(st, 200, d)
        doc = self.conn.execute("SELECT * FROM onboarding_docs WHERE onboarding_id=? AND chave='w4' AND ativo=1",
                                (ob["id"],)).fetchone()
        self.assertTrue(onboarding.ler_arquivo(self.conn, doc["arquivo"]).startswith(b"%PDF"))
        self.assertNotIn("212-55-1234", doc["dados_cifrados"])
        # dados anteriores voltam sem o SSN
        w4 = [x for x in d["formularios"] if x["tipo"] == "w4"][0]
        self.assertEqual(w4["anteriores"].get("primeiro_nome"), "Maria")
        self.assertNotIn("ssn", w4["anteriores"])
        sens = onboarding.sensiveis(self.conn, self.conn.execute("SELECT * FROM onboardings WHERE id=?", (ob["id"],)).fetchone())
        self.assertEqual(sens["ssn"], "212-55-1234")
        if FORMULARIOS_REAIS:
            texto = texto_pdf(onboarding.ler_arquivo(self.conn, doc["arquivo"]))
            self.assertTrue(texto)

    def test_conclusao_avisa_gestores_nos_idiomas(self):
        cand = self.candidato()
        ob = self.oferta(cand)
        st, r = self.portal(ob, "concluir", "POST", {})
        self.assertEqual(st, 400)
        d = self.completar(ob)
        self.assertEqual(d["pendentes"], [])
        self.enviados.clear()
        st, d = self.portal(ob, "concluir", "POST", {})
        self.assertEqual(st, 200, d)
        self.assertEqual(d["status"], "concluido")
        assuntos = {e["para"]: e["assunto"] for e in self.enviados}
        self.assertTrue(assuntos["tony@example.com"].startswith("Onboarding concluído"))
        self.assertTrue(assuntos["carine@example.com"].startswith("Onboarding complete"))
        self.assertTrue(assuntos["ana@example.com"].startswith("Incorporación completa"))
        self.assertNotIn("intruso@example.com", assuntos)
        self.assertIn("/gestor#candidato=%d" % cand["id"], [e for e in self.enviados if e["para"] == "tony@example.com"][0]["corpo"])
        self.assertIn("I-9", [e for e in self.enviados if e["para"] == "carine@example.com"][0]["corpo"])
        self.assertIn("maria@example.com", assuntos)
        for e in self.enviados:   # nenhum dado sensível nos e-mails
            for segredo in ("212-55-1234", "123456789", "011000015", "1990-04-12"):
                self.assertNotIn(segredo, e["corpo"] + e["html"])
        st, r = self.dados_pessoais(ob)
        self.assertEqual(st, 400)   # concluído fica só leitura


class TestGestor(Base):
    def test_painel_mascara_revelar_admin_auditado(self):
        cand = self.candidato()
        ob = self.oferta(cand)
        self.completar(ob)
        st, r = self.req("GET", "/api/gestor/onboarding/candidato/%d" % cand["id"], gestor="joao")
        self.assertEqual(st, 200)
        info = r["onboardings"][0]
        self.assertEqual(info["mascaras"]["conta"], "•••6789")
        self.assertEqual(info["mascaras"]["routing"], "•••0015")
        self.assertNotIn("123456789", json.dumps(r))
        self.assertNotIn("1990-04-12", json.dumps(r))
        st, r = self.req("POST", "/api/gestor/onboarding/%d/revelar" % ob["id"], {"campo": "conta"}, gestor="joao")
        self.assertEqual(st, 403)
        st, r = self.req("POST", "/api/gestor/onboarding/%d/revelar" % ob["id"], {"campo": "conta"}, gestor="tony")
        self.assertEqual(st, 200)
        self.assertEqual(r["valor"], "123456789")
        linhas = self.conn.execute("SELECT * FROM auditoria WHERE acao='revelar_dado_sensivel'").fetchall()
        self.assertEqual(len(linhas), 1)
        self.assertIn("campo:conta", linhas[0]["alvo"])
        tudo = json.dumps([dict(x) for x in self.conn.execute("SELECT * FROM auditoria").fetchall()])
        tudo += json.dumps([dict(x) for x in self.conn.execute("SELECT * FROM eventos").fetchall()])
        for segredo in ("123456789", "011000015", "212-55-1234", "1990-04-12"):
            self.assertNotIn(segredo, tudo)

    def test_acesso_aos_arquivos(self):
        cand = self.candidato()
        ob = self.oferta(cand)
        self.consentir(ob)
        st, d = self.portal(ob, "arquivo?categoria=id_frente&nome=id.jpg", "POST", bruto=JPEG)
        doc_id = d["arquivos"][0]["id"]
        url = "/api/gestor/onboarding/%d/arquivo/%d" % (ob["id"], doc_id)
        st, corpo = self.req("GET", url, gestor="tony")
        self.assertEqual(st, 200)
        self.assertEqual(corpo, JPEG)
        self.assertTrue(self.conn.execute("SELECT 1 FROM auditoria WHERE acao='baixar_documento_onboarding'").fetchone())
        st, _ = self.req("GET", url)                       # anônimo
        self.assertEqual(st, 401)
        st, _ = self.req("GET", url, gestor="intruso")     # outra empresa
        self.assertEqual(st, 404)
        # outro novo contratado (outro token) não baixa o arquivo
        ob2 = self.oferta(self.candidato(email="outro@example.com", nome="Outro Nome"))
        st, _ = self.portal(ob2, "arquivo/%d" % doc_id)
        self.assertEqual(st, 404)
        st, corpo = self.portal(ob, "arquivo/%d" % doc_id)
        self.assertEqual(st, 200)
        # nada do onboarding é servido como arquivo estático
        st, _ = self.req("GET", "/uploads/onboarding/%d/x.bin" % ob["id"])
        self.assertEqual(st, 404)

    def test_isolamento_entre_empresas(self):
        cand = self.candidato()
        ob = self.oferta(cand)
        st, _ = self.req("GET", "/api/gestor/onboarding/candidato/%d" % cand["id"], gestor="intruso")
        self.assertEqual(st, 404)
        st, r = self.req("GET", "/api/gestor/onboarding/lista", gestor="intruso")
        self.assertEqual(r["onboardings"], [])
        st, r = self.req("GET", "/api/gestor/onboarding/lista", gestor="tony")
        self.assertEqual(len(r["onboardings"]), 1)
        for acao in ("reenviar", "cancelar", "revelar", "contratado"):
            st, _ = self.req("POST", "/api/gestor/onboarding/%d/%s" % (ob["id"], acao), {"campo": "conta"}, gestor="intruso")
            self.assertEqual(st, 404, acao)
        st, _ = self.req("POST", "/api/gestor/onboarding/oferta", {"candidato_id": cand["id"], "tipo": "w2"}, gestor="intruso")
        self.assertEqual(st, 404)
        # modelos são por empresa
        mb = onboarding.modelos(self.conn, self.eb)
        st, _ = self.req("DELETE", "/api/gestor/onboarding/modelo/%d" % mb[0]["id"], gestor="tony")
        self.assertEqual(st, 404)

    def test_cancelar_e_reenviar(self):
        ob = self.oferta(self.candidato())
        self.enviados.clear()
        st, _ = self.req("POST", "/api/gestor/onboarding/%d/reenviar" % ob["id"], {}, gestor="joao")
        self.assertEqual(st, 200)
        self.assertEqual(len(self.enviados), 1)
        st, _ = self.req("POST", "/api/gestor/onboarding/%d/cancelar" % ob["id"], {}, gestor="joao")
        self.assertEqual(st, 403)
        st, _ = self.req("POST", "/api/gestor/onboarding/%d/cancelar" % ob["id"], {}, gestor="tony")
        self.assertEqual(st, 200)
        st, r = self.portal(ob)
        self.assertEqual(st, 410)

    def test_i9_secao2_e_prazo(self):
        cand = self.candidato()
        ob = self.oferta(cand)
        self.completar(ob)
        st, r = self.req("GET", "/api/gestor/onboarding/candidato/%d" % cand["id"], gestor="tony")
        info = r["onboardings"][0]
        self.assertEqual(info["i9"]["prazo"], "2026-11-12")    # segunda 9/11 + 3 dias úteis
        self.assertTrue(info["i9"]["secao1"])
        self.assertTrue(r["campos_i9_secao2"])
        padroes = r["padroes_i9"][str(ob["id"])]
        self.assertEqual(padroes["primeiro_dia"], "2026-11-09")
        st, e = self.req("POST", "/api/gestor/onboarding/%d/i9-secao2" % ob["id"], {"dados": {"lista": "A"}}, gestor="tony")
        self.assertEqual(st, 400)
        dados = dict(padroes, lista="A", doc_a_titulo="U.S. Passport", doc_a_autoridade="U.S. Department of State",
                     doc_a_numero="123456789", doc_a_validade="2030-01-01", representante_nome="Belleza, Carine, Owner",
                     data=date.today().isoformat())
        st, r = self.req("POST", "/api/gestor/onboarding/%d/i9-secao2" % ob["id"], {"dados": dados, "assinatura": ASSINATURA},
                         gestor="tony")
        self.assertEqual(st, 200, r)
        self.assertTrue(r["onboarding"]["i9"]["feito"])
        doc = self.conn.execute("SELECT * FROM onboarding_docs WHERE onboarding_id=? AND tipo='i9_secao2'", (ob["id"],)).fetchone()
        self.assertTrue(onboarding.ler_arquivo(self.conn, doc["arquivo"]).startswith(b"%PDF"))

    def test_config_e_modelos(self):
        st, r = self.req("GET", "/api/gestor/onboarding/config", gestor="joao")
        self.assertEqual(st, 403)
        st, r = self.req("GET", "/api/gestor/onboarding/config", gestor="tony")
        self.assertEqual(st, 200)
        self.assertEqual(r["config"]["estaduais"], ["ctw4"])                 # empresa de CT
        self.assertEqual(onboarding.config(self.conn, self.eb)["estaduais"], [])
        self.assertEqual(len(r["modelos"]), 7)
        st, r = self.req("POST", "/api/gestor/onboarding/config", {"empregador_ein": "12"}, gestor="tony")
        self.assertEqual(st, 400)
        st, r = self.req("POST", "/api/gestor/onboarding/config", {"lembrete_dias": 3, "metodos": ["cheque", "zelle"],
                                                                   "retencao_dias": 30}, gestor="tony")
        self.assertEqual(st, 200, r)
        self.assertEqual(r["config"]["metodos"], ["zelle", "cheque"])
        st, r = self.req("POST", "/api/gestor/onboarding/modelo", {"titulos": {"en": "Uniform Policy"}, "textos": {"en": "# Uniform\n\nHello {{nome}}"},
                                                                   "aplica": "w2", "ordem": 5}, gestor="tony")
        self.assertEqual(st, 200, r)
        st, _ = self.req("DELETE", "/api/gestor/onboarding/modelo/%d" % r["modelo"]["id"], gestor="tony")
        self.assertEqual(st, 200)

    def test_purga_depois_da_retencao(self):
        cand = self.candidato()
        ob = self.oferta(cand)
        self.completar(ob)
        self.portal(ob, "concluir", "POST", {})
        onboarding.salvar_config(self.conn, self.ea, dict(onboarding.config(self.conn, self.ea), retencao_dias=30))
        st, r = self.req("POST", "/api/gestor/onboarding/%d/purgar" % ob["id"], {}, gestor="tony")
        self.assertEqual(st, 400)
        self.conn.execute("UPDATE onboardings SET concluido_em=datetime('now','-40 days') WHERE id=?", (ob["id"],))
        self.conn.commit()
        st, r = self.req("POST", "/api/gestor/onboarding/%d/purgar" % ob["id"], {}, gestor="tony")
        self.assertEqual(st, 200, r)
        linha = self.conn.execute("SELECT sensiveis, purgado_em FROM onboardings WHERE id=?", (ob["id"],)).fetchone()
        self.assertEqual(linha["sensiveis"], "")
        self.assertTrue(linha["purgado_em"])


class TestLembretes(Base):
    def test_um_por_dia_a_cada_n_dias(self):
        ob = self.oferta(self.candidato("es"))
        self.conn.execute("UPDATE onboardings SET criado_em=datetime('now','-3 days') WHERE id=?", (ob["id"],))
        self.conn.commit()
        self.enviados.clear()
        agora = datetime.now(timezone.utc)
        self.assertEqual(onboarding.enviar_lembretes(self.conn, agora), 1)
        self.assertEqual(onboarding.enviar_lembretes(self.conn, agora), 0)            # mesmo dia
        self.assertEqual(onboarding.enviar_lembretes(self.conn, agora + timedelta(days=1)), 0)   # cadência de 2 dias
        self.assertEqual(onboarding.enviar_lembretes(self.conn, agora + timedelta(days=2)), 1)
        self.assertIn("Recordatorio", self.enviados[0]["assunto"])
        self.assertIn("Carta de oferta", self.enviados[0]["corpo"])
        # depois do prazo, sem lembretes
        self.assertEqual(onboarding.enviar_lembretes(self.conn, agora + timedelta(days=30)), 0)

    def test_sem_lembrete_quando_cancelado_ou_desligado(self):
        ob = self.oferta(self.candidato())
        self.conn.execute("UPDATE onboardings SET criado_em=datetime('now','-3 days') WHERE id=?", (ob["id"],))
        self.conn.commit()
        onboarding.salvar_config(self.conn, self.ea, dict(onboarding.config(self.conn, self.ea), lembrete_dias=0))
        self.assertEqual(onboarding.enviar_lembretes(self.conn), 0)


class TestChave(Base):
    def test_ida_e_volta_e_permissao(self):
        texto = onboarding.cifrar_dict(self.conn, {"ssn": "212-55-1234"})
        self.assertNotIn("212", texto)
        self.assertEqual(onboarding.decifrar_dict(self.conn, texto), {"ssn": "212-55-1234"})
        caminho = os.path.join(server.BASE_DIR, "chave_dados.key")
        self.assertTrue(os.path.isfile(caminho))
        self.assertEqual(os.stat(caminho).st_mode & 0o777, 0o600)
        self.assertFalse(caminho.startswith(server.PUBLIC_DIR))

    def test_nao_cria_chave_nova_com_dados_cifrados(self):
        ob = self.oferta(self.candidato())
        self.consentir(ob)
        self.dados_pessoais(ob)
        os.remove(os.path.join(server.BASE_DIR, "chave_dados.key"))
        onboarding.esquecer_chave()
        with self.assertRaises(onboarding.ErroChave):
            onboarding.fernet(self.conn)
        self.assertFalse(os.path.exists(os.path.join(server.BASE_DIR, "chave_dados.key")))
        st, r = self.req("GET", "/api/gestor/onboarding/candidato/%d" % ob["candidato_id"], gestor="tony")
        self.assertEqual(st, 200)
        self.assertTrue(r["onboardings"][0]["erro_chave"])

    def test_chave_trocada_e_detectada(self):
        ob = self.oferta(self.candidato())
        self.consentir(ob)
        self.dados_pessoais(ob)
        onboarding.esquecer_chave()
        from cryptography.fernet import Fernet
        os.environ["BUSSOLA_CHAVE_DADOS"] = Fernet.generate_key().decode()
        try:
            with self.assertRaises(onboarding.ErroChave):
                onboarding.fernet(self.conn)
        finally:
            os.environ.pop("BUSSOLA_CHAVE_DADOS", None)
            onboarding.esquecer_chave()
        self.assertTrue(onboarding.fernet(self.conn))


class TestTextos(unittest.TestCase):
    def test_chaves_nos_3_idiomas(self):
        for lang in ("en", "es"):
            self.assertEqual(set(onboarding.T["pt"]), set(onboarding.T[lang]), lang)
            self.assertEqual(set(onboarding.T["pt"]["etapas"]), set(onboarding.T[lang]["etapas"]))
        self.assertEqual(set(onboarding.CONSENTIMENTO), {"pt", "en", "es"})

    def test_sem_travessoes(self):
        for arq in ("onboarding.py", "teste_onboarding.py", "public/onboarding.html", "public/js/onboarding.js",
                    "public/js/gestor-onboarding.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)

    def test_erros_traduzidos(self):
        import erros_i18n
        with open(os.path.join(AQUI, "onboarding.py"), encoding="utf-8") as f:
            fonte = f.read()
        msgs = set(re.findall(r'"erro": "([^"]+)"', fonte)) | set(re.findall(r'ErroOnboarding\(\d+, "([^"]+)"', fonte))
        msgs |= set(re.findall(r'return None, "([^"]+)"', fonte))
        for m in msgs:
            if m.endswith(": "):
                continue
            self.assertIn(m, erros_i18n.ERROS, m)
            self.assertNotEqual(erros_i18n.traduzir(m, "en"), m, m)

    def test_modelos_marcados_como_rascunho(self):
        for m in onboarding.MODELOS_PADRAO:
            for lang, txt in m["textos"].items():
                self.assertTrue(txt.lstrip().startswith("> "), (m["chave"], lang))
                self.assertNotIn("non-compete", txt.lower().replace("does not contain a non-compete", ""))

    def test_chave_no_gitignore(self):
        with open(os.path.join(AQUI, ".gitignore"), encoding="utf-8") as f:
            self.assertIn("chave_dados.key", f.read())
        with open(os.path.join(AQUI, "DEPLOY.md"), encoding="utf-8") as f:
            self.assertIn("--exclude chave_dados.key", f.read())


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
