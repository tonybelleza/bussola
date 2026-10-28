"""
Testes dos números por empresa e dos alertas de uso (telefonia.py).

Nenhuma chamada real: urllib.request.urlopen é trocado por um falso que imita a
Twilio e a ElevenLabs (o servidor local de teste continua com o urlopen real).

Uso:  python3 teste_telefonia.py
"""
import base64
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
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="tel-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import planos  # noqa: E402
import server  # noqa: E402
import telefonia  # noqa: E402
import voz  # noqa: E402

SID = "AC" + "1" * 32
TOKEN = "f" * 32
EL_KEY = "sk_el_secreta"
TRACOS = re.compile("[%s%s]" % (chr(0x2013), chr(0x2014)))
URLOPEN_REAL = urllib.request.urlopen


class Resposta:
    def __init__(self, status, corpo):
        self.status = status
        self._corpo = corpo

    def read(self):
        return self._corpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FalsoExterno:
    """Imita os endpoints da Twilio e da ElevenLabs usados pela telefonia e pela voz."""

    def __init__(self):
        self.pedidos = []
        self.twilio_numeros = {}   # numero -> sid
        self.disponiveis = ["+18605550111", "+18605550122"]
        self.el_numeros = {}       # phone_number_id -> dados
        self.falhar_el = False
        self.contador = 0

    def __call__(self, req, timeout=None, **kw):
        url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
        if url.startswith("http://127.0.0.1"):
            return URLOPEN_REAL(req, timeout=timeout or 30, **kw)
        assert timeout, "chamada externa sem timeout"
        metodo = req.get_method()
        corpo = req.data.decode("utf-8") if req.data else ""
        cab = {k.lower(): v for k, v in req.header_items()}
        self.pedidos.append({"metodo": metodo, "url": url, "corpo": corpo, "cab": cab})
        status, dados = self.responder(metodo, url, corpo, cab)
        bruto = json.dumps(dados).encode("utf-8") if dados is not None else b""
        if status >= 400:
            raise urllib.error.HTTPError(url, status, "erro", {}, io.BytesIO(bruto))
        return Resposta(status, bruto)

    def responder(self, metodo, url, corpo, cab):
        u = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(u.query)
        if u.netloc == "api.twilio.com":
            esperado = "Basic " + base64.b64encode(("%s:%s" % (SID, TOKEN)).encode()).decode()
            if cab.get("authorization") != esperado:
                return 401, {"message": "Authenticate", "code": 20003}
            base = "/2010-04-01/Accounts/%s/" % SID
            caminho = u.path[len(base):]
            if metodo == "GET" and caminho == "AvailablePhoneNumbers/US/Local.json":
                return 200, {"available_phone_numbers": [
                    {"phone_number": n, "friendly_name": "(860) 555-0" + n[-3:], "locality": "Hartford", "region": "CT"}
                    for n in self.disponiveis]}
            if metodo == "POST" and caminho == "IncomingPhoneNumbers.json":
                numero = urllib.parse.parse_qs(corpo)["PhoneNumber"][0]
                if numero not in self.disponiveis:
                    return 400, {"message": "Phone number %s is not available" % numero, "code": 21422}
                self.contador += 1
                sid = "PN%032d" % self.contador
                self.twilio_numeros[numero] = sid
                self.disponiveis.remove(numero)
                return 201, {"sid": sid, "phone_number": numero}
            if metodo == "GET" and caminho == "IncomingPhoneNumbers.json":
                numero = qs.get("PhoneNumber", [""])[0]
                achados = [{"sid": s, "phone_number": n} for n, s in self.twilio_numeros.items() if n == numero]
                return 200, {"incoming_phone_numbers": achados}
            m = re.match(r"^IncomingPhoneNumbers/(PN\w+)\.json$", caminho)
            if metodo == "DELETE" and m:
                for n, s in list(self.twilio_numeros.items()):
                    if s == m.group(1):
                        del self.twilio_numeros[n]
                        return 204, None
                return 404, {"message": "not found"}
        if u.netloc == "api.elevenlabs.io":
            if cab.get("xi-api-key") != EL_KEY:
                return 401, {"detail": "invalid key"}
            if self.falhar_el:
                return 500, {"detail": {"message": "temporary failure"}}
            if metodo == "POST" and u.path == "/v1/convai/phone-numbers":
                d = json.loads(corpo)
                self.contador += 1
                pid = "phnum_%d" % self.contador
                self.el_numeros[pid] = d
                return 200, {"phone_number_id": pid}
            m = re.match(r"^/v1/convai/phone-numbers/(\w+)$", u.path)
            if m and metodo == "PATCH":
                self.el_numeros[m.group(1)]["agent_id"] = json.loads(corpo)["agent_id"]
                return 200, {"phone_number_id": m.group(1)}
            if m and metodo == "DELETE":
                if self.el_numeros.pop(m.group(1), None) is None:
                    return 404, {"detail": "not found"}
                return 200, {}
            if metodo == "POST" and u.path == "/v1/convai/twilio/outbound-call":
                return 200, {"success": True, "conversation_id": "conv_%d" % len(self.pedidos), "callSid": "CA1"}
        return 404, {"message": "rota falsa desconhecida: %s %s" % (metodo, url)}

    def externos(self, trecho=""):
        return [p for p in self.pedidos if trecho in p["url"]]


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
        self.ea, self.slug_a = empresas.criar_empresa(c, "Empresa A")
        self.eb, self.slug_b = empresas.criar_empresa(c, "Empresa B")
        c.execute("INSERT INTO sessoes_dono (token) VALUES ('dono-tok')")
        for chave, valor in (("twilio_account_sid", SID), ("twilio_auth_token", TOKEN),
                             ("elevenlabs_api_key", EL_KEY), ("elevenlabs_agent_id", "agent_plat"),
                             ("elevenlabs_phone_number_id", "phnum_plataforma"),
                             ("url_publica", "https://rh.exemplo.com"), ("dono_email", "tony@exemplo.com")):
            server.config_set(c, chave, valor)
        c.commit()
        self.falso = FalsoExterno()
        urllib.request.urlopen = self.falso
        voz.GATEWAY_TESTE = None
        telefonia.ENVIO_EM_SEGUNDO_PLANO = False
        self.enviados = []
        self._email = server.enviar_email

        def gravar(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt"):
            self.enviados.append({"para": para, "assunto": assunto, "corpo": corpo, "idioma": idioma, "marca": marca})
            return True, "enviado"

        server.enviar_email = gravar

    def tearDown(self):
        urllib.request.urlopen = URLOPEN_REAL
        server.enviar_email = self._email
        telefonia.ENVIO_EM_SEGUNDO_PLANO = True
        self.conn.close()

    def req(self, metodo, caminho, dados=None, idioma=None, dono=True):
        h = {"Content-Type": "application/json"}
        if dono:
            h["X-Dono-Token"] = "dono-tok"
        if idioma:
            h["X-Idioma"] = idioma
        corpo = json.dumps(dados).encode() if dados is not None else None
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=h)
        try:
            with URLOPEN_REAL(r, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def numero_row(self, numero):
        return self.conn.execute("SELECT * FROM numeros_empresa WHERE numero=? ORDER BY id DESC", (numero,)).fetchone()


# ================================================================ credenciais e números

class TestNumeros(Base):
    def test_credenciais_twilio_mascaradas(self):
        self.assertEqual(self.req("GET", "/api/dono/telefonia/twilio", dono=False)[0], 401)
        s, d = self.req("POST", "/api/dono/telefonia/twilio", {"account_sid": "XX123"}, idioma="en")
        self.assertEqual((s, d["erro"]), (400, "Invalid Account SID (starts with AC and has 34 characters)"))
        novo_sid, novo_token = "AC" + "2" * 32, "a" * 32
        s, d = self.req("POST", "/api/dono/telefonia/twilio", {"account_sid": novo_sid, "auth_token": novo_token})
        self.assertEqual(s, 200, d)
        s, d = self.req("GET", "/api/dono/telefonia/twilio")
        self.assertTrue(d["configurado"])
        self.assertEqual(d["token_final"], "aaaa")
        self.assertNotIn(novo_token, json.dumps(d))
        self.assertNotIn(novo_sid, json.dumps(d))
        self.assertEqual(server.config_get(self.conn, "twilio_auth_token"), novo_token)
        s, d = self.req("POST", "/api/dono/telefonia/twilio", {"remover": True})
        self.assertFalse(d["configurado"])
        s, d = self.req("GET", "/api/dono/telefonia/disponiveis?ddd=860", idioma="es")
        self.assertEqual((s, d["erro"]), (400, "Configura primero Twilio en Integraciones"))

    def test_buscar_por_codigo_de_area(self):
        s, d = self.req("GET", "/api/dono/telefonia/disponiveis?ddd=860")
        self.assertEqual(s, 200, d)
        self.assertEqual([n["numero"] for n in d["numeros"]], ["+18605550111", "+18605550122"])
        self.assertEqual(d["custo_mensal"], 1.15)
        p = self.falso.externos("AvailablePhoneNumbers")[0]
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(p["url"]).query)
        self.assertEqual((qs["AreaCode"], qs["VoiceEnabled"], qs["SmsEnabled"]), (["860"], ["true"], ["true"]))
        self.assertIn("/2010-04-01/Accounts/%s/AvailablePhoneNumbers/US/Local.json" % SID, p["url"])
        s, d = self.req("GET", "/api/dono/telefonia/disponiveis?ddd=86a", idioma="en")
        self.assertEqual((s, d["erro"]), (400, "Invalid area code: use 3 digits, for example 860"))

    def test_compra_exige_confirmacao(self):
        caminho = "/api/dono/telefonia/empresa/%d/comprar" % self.ea
        for corpo in ({"numero": "+18605550111"}, {"numero": "+18605550111", "confirmar": "true"},
                      {"numero": "+18605550111", "confirmar": 1}):
            s, d = self.req("POST", caminho, corpo, idioma="en")
            self.assertEqual(s, 400, d)
            self.assertTrue(d["confirmacao_necessaria"])
            self.assertEqual(d["custo_mensal"], 1.15)
            self.assertEqual(d["erro"], "Confirm the purchase and the monthly cost of the number")
        self.assertEqual(self.falso.externos("IncomingPhoneNumbers"), [])
        self.assertIsNone(self.numero_row("+18605550111"))

    def test_compra_importa_na_elevenlabs(self):
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/comprar" % self.ea,
                        {"numero": "+18605550111", "confirmar": True})
        self.assertEqual(s, 200, d)
        n = d["numero"]
        self.assertEqual((n["status"], n["origem"], n["numero"]), ("ativo", "comprado", "+18605550111"))
        compra = self.falso.externos("IncomingPhoneNumbers.json")[0]
        self.assertEqual(compra["metodo"], "POST")
        self.assertEqual(urllib.parse.parse_qs(compra["corpo"])["PhoneNumber"], ["+18605550111"])
        el = self.falso.el_numeros[n["elevenlabs_phone_id"]]
        self.assertEqual((el["phone_number"], el["provider"], el["sid"], el["token"], el["agent_id"]),
                         ("+18605550111", "twilio", SID, TOKEN, "agent_plat"))
        self.assertTrue(el["label"])
        metodos = [(p["metodo"], urllib.parse.urlparse(p["url"]).path.split("/")[-1]) for p in self.falso.pedidos]
        self.assertEqual(metodos, [("POST", "IncomingPhoneNumbers.json"), ("POST", "phone-numbers"),
                                   ("PATCH", n["elevenlabs_phone_id"])])
        row = self.numero_row("+18605550111")
        self.assertEqual((row["empresa_id"], row["twilio_sid"]), (self.ea, self.falso.twilio_numeros["+18605550111"]))
        self.assertTrue(row["comprado_em"])
        # aparece na lista da empresa e não na da outra
        self.assertEqual(len(self.req("GET", "/api/dono/telefonia/empresa/%d" % self.ea)[1]["numeros"]), 1)
        self.assertEqual(self.req("GET", "/api/dono/telefonia/empresa/%d" % self.eb)[1]["numeros"], [])
        # auditoria sem segredos
        aud = self.conn.execute("SELECT acao, alvo, quem, empresa_id FROM auditoria WHERE acao LIKE 'telefonia%'").fetchall()
        self.assertIn(("telefonia comprar", self.ea), [(a["acao"], a["empresa_id"]) for a in aud])
        self.assertTrue(all(TOKEN not in (a["alvo"] or "") and EL_KEY not in (a["alvo"] or "") for a in aud))
        # o mesmo número não entra duas vezes
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/anexar" % self.eb, {"numero": "+18605550111"}, idioma="en")
        self.assertEqual((s, d["erro"]), (409, "This number is already in use on the platform"))

    def test_erro_da_twilio_traduzido(self):
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/comprar" % self.ea,
                        {"numero": "+18605559999", "confirmar": True}, idioma="es")
        self.assertEqual(s, 502)
        self.assertEqual(d["erro"], "Error de Twilio: Phone number +18605559999 is not available")
        self.assertIsNone(self.numero_row("+18605559999"))
        server.config_set(self.conn, "twilio_auth_token", "b" * 32)
        self.conn.commit()
        s, d = self.req("GET", "/api/dono/telefonia/disponiveis?ddd=860", idioma="en")
        self.assertEqual((s, d["erro"]), (502, "Twilio rejected the credentials. Check the Account SID and Auth Token."))
        self.assertNotIn("b" * 32, json.dumps(d))

    def test_falha_na_elevenlabs_fica_pendente_e_reimporta(self):
        self.falso.falhar_el = True
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/comprar" % self.ea,
                        {"numero": "+18605550111", "confirmar": True}, idioma="en")
        self.assertEqual(s, 502)
        self.assertEqual(d["erro"], "The number is in Twilio, but importing it into ElevenLabs failed. "
                                    "ElevenLabs error: temporary failure")
        row = self.numero_row("+18605550111")
        self.assertEqual(row["status"], "pendente")
        self.assertIsNone(telefonia.phone_id_da_empresa(self.conn, self.ea))
        self.falso.falhar_el = False
        s, d = self.req("POST", "/api/dono/telefonia/numero/%d/importar" % row["id"])
        self.assertEqual((s, d["numero"]["status"]), (200, "ativo"))
        self.assertEqual(telefonia.phone_id_da_empresa(self.conn, self.ea), d["numero"]["elevenlabs_phone_id"])

    def test_anexar_numero_existente(self):
        self.falso.twilio_numeros["+12035550199"] = "PN" + "9" * 32
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/anexar" % self.eb, {"numero": "(203) 555-0199"})
        self.assertEqual(s, 200, d)
        self.assertEqual((d["numero"]["numero"], d["numero"]["origem"], d["numero"]["status"]),
                         ("+12035550199", "anexado", "ativo"))
        self.assertEqual(d["numero"]["twilio_sid"], "PN" + "9" * 32)
        self.assertEqual(self.falso.externos("IncomingPhoneNumbers.json")[0]["metodo"], "GET")
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/anexar" % self.eb, {"numero": "+12035550100"}, idioma="es")
        self.assertEqual((s, d["erro"]), (404, "Este número no está en tu cuenta de Twilio"))
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/anexar" % self.eb, {"numero": "123"}, idioma="en")
        self.assertEqual((s, d["erro"]), (400, "Invalid number: use the format +1XXXXXXXXXX"))
        s, d = self.req("POST", "/api/dono/telefonia/empresa/999/anexar", {"numero": "+12035550199"}, idioma="en")
        self.assertEqual((s, d["erro"]), (404, "Company not found"))

    def test_liberar_exige_confirmacao_e_segue_a_ordem(self):
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/comprar" % self.ea, {"numero": "+18605550111", "confirmar": True})
        nid, pid = d["numero"]["id"], d["numero"]["elevenlabs_phone_id"]
        s, d = self.req("POST", "/api/dono/telefonia/numero/%d/liberar" % nid, {}, idioma="en")
        self.assertEqual((s, d["erro"]), (400, "Confirm releasing the number"))
        self.assertIn("+18605550111", self.falso.twilio_numeros)
        self.falso.pedidos.clear()
        s, d = self.req("POST", "/api/dono/telefonia/numero/%d/liberar" % nid, {"confirmar": True})
        self.assertEqual((s, d["numero"]["status"]), (200, "liberado"))
        self.assertEqual([(p["metodo"], urllib.parse.urlparse(p["url"]).netloc) for p in self.falso.pedidos],
                         [("DELETE", "api.elevenlabs.io"), ("DELETE", "api.twilio.com")])
        self.assertNotIn(pid, self.falso.el_numeros)
        self.assertNotIn("+18605550111", self.falso.twilio_numeros)
        self.assertIsNone(telefonia.phone_id_da_empresa(self.conn, self.ea))
        s, d = self.req("POST", "/api/dono/telefonia/numero/%d/liberar" % nid, {"confirmar": True}, idioma="en")
        self.assertEqual((s, d["erro"]), (409, "This number was already released"))
        self.assertEqual(self.req("GET", "/api/dono/telefonia/empresa/%d" % self.ea)[1]["numeros"], [])
        self.assertTrue(self.conn.execute("SELECT 1 FROM auditoria WHERE acao='telefonia liberar'").fetchone())

    def test_desanexar_mantem_na_twilio(self):
        self.falso.twilio_numeros["+12035550199"] = "PN" + "9" * 32
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/anexar" % self.ea, {"numero": "+12035550199"})
        self.falso.pedidos.clear()
        s, d = self.req("POST", "/api/dono/telefonia/numero/%d/liberar" % d["numero"]["id"],
                        {"confirmar": True, "manter_twilio": True})
        self.assertEqual((s, d["numero"]["status"]), (200, "liberado"))
        self.assertEqual([p["metodo"] for p in self.falso.pedidos], ["DELETE"])
        self.assertIn("+12035550199", self.falso.twilio_numeros)


# ================================================================ voz usa o número da empresa

class TestVozUsaNumero(Base):
    def candidatura(self, empresa_id, telefone):
        c = self.conn
        cargo = c.execute("INSERT INTO cargos (nome, voz_ativa, empresa_id) VALUES ('Tech', 1, ?)", (empresa_id,)).lastrowid
        vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Tech', 'aberta', ?)",
                         (cargo, empresa_id)).lastrowid
        cid = c.execute("INSERT INTO candidatos (token, nome, email, telefone, empresa_id) VALUES (?,?,?,?,?)",
                        ("tk%s" % time.time(), "Maria", "m@x.com", telefone, empresa_id)).lastrowid
        caid = c.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cid, vaga)).lastrowid
        voz.nova_candidatura(c, cid, vaga)
        c.commit()
        return caid

    def ultima_ligacao(self):
        return json.loads(self.falso.externos("outbound-call")[-1]["corpo"])

    def test_ligacao_usa_numero_proprio_e_cai_no_padrao(self):
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/comprar" % self.ea, {"numero": "+18605550111", "confirmar": True})
        pid = d["numero"]["elevenlabs_phone_id"]
        self.assertEqual(voz.gateway(self.conn, self.ea).phone_number_id, pid)
        self.assertEqual(voz.gateway(self.conn, self.eb).phone_number_id, "phnum_plataforma")
        self.assertEqual(voz.gateway(self.conn).phone_number_id, "phnum_plataforma")

        voz.iniciar_ligacao(self.conn, self.candidatura(self.ea, "+1 860 555 0101"), "teste", manual=True)
        self.assertEqual(self.ultima_ligacao()["agent_phone_number_id"], pid)
        voz.iniciar_ligacao(self.conn, self.candidatura(self.eb, "+1 860 555 0102"), "teste", manual=True)
        self.assertEqual(self.ultima_ligacao()["agent_phone_number_id"], "phnum_plataforma")

        # depois de liberar, a empresa A volta para o número da plataforma
        self.req("POST", "/api/dono/telefonia/numero/%d/liberar" % d["numero"]["id"], {"confirmar": True})
        voz.iniciar_ligacao(self.conn, self.candidatura(self.ea, "+1 860 555 0103"), "teste", manual=True)
        self.assertEqual(self.ultima_ligacao()["agent_phone_number_id"], "phnum_plataforma")

    def test_empresa_com_numero_liga_mesmo_sem_numero_da_plataforma(self):
        s, d = self.req("POST", "/api/dono/telefonia/empresa/%d/comprar" % self.ea, {"numero": "+18605550122", "confirmar": True})
        server.config_set(self.conn, "elevenlabs_phone_number_id", "")
        self.conn.commit()
        self.assertIsNone(voz.gateway(self.conn, self.eb))
        self.assertEqual(voz.gateway(self.conn, self.ea).phone_number_id, d["numero"]["elevenlabs_phone_id"])

    def test_gateway_falso_dos_testes_continua_valendo(self):
        falso = object()
        voz.GATEWAY_TESTE = falso
        try:
            self.assertIs(voz.gateway(self.conn, self.ea), falso)
        finally:
            voz.GATEWAY_TESTE = None


# ================================================================ alertas de uso

class TestAlertas(Base):
    def setUp(self):
        Base.setUp(self)
        c = self.conn
        c.execute("UPDATE empresas SET plano='voz100', status='ativa' WHERE id IN (?,?)", (self.ea, self.eb))
        for nome, email, idioma, admin, eid in (("Ana", "ana@a.com", "en", 1, self.ea), ("Beto", "beto@a.com", "es", 1, self.ea),
                                                ("Caio", "caio@a.com", "pt", 0, self.ea), ("Duda", "duda@b.com", "pt", 1, self.eb)):
            c.execute("INSERT INTO gestores (nome, login, senha, email, is_admin, aprovado, empresa_id, idioma)"
                      " VALUES (?,?,?,?,?,1,?,?)", (nome, nome.lower(), "x", email, admin, eid, idioma))
        self.cand = c.execute("INSERT INTO candidatos (token, nome, email, empresa_id) VALUES ('tka','X','x@x.com',?)", (self.ea,)).lastrowid
        cargo = c.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('T', ?)", (self.ea,)).lastrowid
        vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'T', 'aberta', ?)",
                         (cargo, self.ea)).lastrowid
        self.cdt = c.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (self.cand, vaga)).lastrowid
        c.commit()

    def minutos(self, n, quando=None):
        self.conn.execute("INSERT INTO voz_chamadas (candidatura_id, candidato_id, duracao, iniciada_em, status)"
                          " VALUES (?,?,?,COALESCE(?, datetime('now')),'concluida')",
                          (self.cdt, self.cand, n * 60, quando))
        self.conn.commit()

    def test_80_e_100_uma_vez_por_limiar(self):
        self.minutos(79)
        self.assertFalse(planos.voz_bloqueada(self.conn, self.ea))
        self.assertEqual(self.enviados, [])
        self.minutos(2)  # 81%
        self.assertFalse(planos.voz_bloqueada(self.conn, self.ea))  # o gancho roda antes de cada ligação
        self.assertEqual(sorted(e["para"] for e in self.enviados), ["ana@a.com", "beto@a.com"])
        en = next(e for e in self.enviados if e["para"] == "ana@a.com")
        es = next(e for e in self.enviados if e["para"] == "beto@a.com")
        self.assertEqual((en["idioma"], es["idioma"]), ("en", "es"))
        self.assertIn("80%", en["assunto"])
        self.assertIn("Hi Ana", en["corpo"])
        self.assertIn("81 of the 100 voice screening minutes", en["corpo"])
        self.assertIn("Hola, Beto", es["corpo"])
        self.assertIn("https://rh.exemplo.com/assinar?plano=voz300&e=%s" % self.slug_a, en["corpo"])
        self.assertIn("upgrade to the", en["corpo"])
        self.assertEqual(en["marca"]["slug"], self.slug_a)  # logo e nome da empresa no e-mail
        # repetir não manda de novo
        planos.voz_bloqueada(self.conn, self.ea)
        telefonia.verificar_alertas(self.conn)
        self.assertEqual(len(self.enviados), 2)
        # 100%: admins e dono
        self.minutos(19)
        self.assertTrue(planos.voz_bloqueada(self.conn, self.ea))
        novos = self.enviados[2:]
        self.assertEqual(sorted(e["para"] for e in novos), ["ana@a.com", "beto@a.com", "tony@exemplo.com"])
        dono = next(e for e in novos if e["para"] == "tony@exemplo.com")
        self.assertIsNone(dono["marca"])
        self.assertIn("100", next(e for e in novos if e["para"] == "ana@a.com")["corpo"])
        self.assertIn("paused", next(e for e in novos if e["para"] == "ana@a.com")["corpo"])
        planos.voz_bloqueada(self.conn, self.ea)
        telefonia.verificar_alertas(self.conn)
        self.assertEqual(len(self.enviados), 5)
        for e in self.enviados:
            self.assertIsNone(TRACOS.search(e["assunto"] + e["corpo"]))
        linhas = self.conn.execute("SELECT limiar, enviados FROM alertas_uso WHERE empresa_id=? ORDER BY limiar",
                                   (self.ea,)).fetchall()
        self.assertEqual([tuple(r) for r in linhas], [(80, 2), (100, 3)])
        # a empresa B não recebeu nada
        self.assertFalse(any(e["para"] == "duda@b.com" for e in self.enviados))

    def test_salto_direto_para_100_manda_so_o_de_100(self):
        self.minutos(120)
        telefonia.verificar_alertas(self.conn)  # rotina diária
        self.assertEqual(len(self.enviados), 3)
        self.assertTrue(all("80%" not in e["assunto"] for e in self.enviados))
        telefonia.verificar_alertas(self.conn)
        self.assertEqual(len(self.enviados), 3)

    def test_excedente_e_mes_novo(self):
        self.conn.execute("UPDATE empresas SET excedente_permitido=1 WHERE id=?", (self.ea,))
        self.conn.commit()
        mes_atual = planos.mes_de()
        ano, m = int(mes_atual[:4]), int(mes_atual[5:7])
        anterior = "%04d-%02d" % (ano - (m == 1), 12 if m == 1 else m - 1)
        self.minutos(100, anterior + "-15 15:00:00")
        e = self.conn.execute("SELECT * FROM empresas WHERE id=?", (self.ea,)).fetchone()
        telefonia.verificar_alerta(self.conn, e, planos.uso(self.conn, e, mes=anterior))
        self.assertEqual(len(self.enviados), 3)
        self.assertIn("billed as overage", next(x for x in self.enviados if x["para"] == "ana@a.com")["corpo"])
        # o mês atual ainda não passou do limite; quando passar, sai um alerta novo
        self.assertEqual(telefonia.verificar_alerta(self.conn, e), [])
        self.minutos(100)
        self.assertEqual(len(telefonia.verificar_alerta(self.conn, e)), 3)
        meses = {r[0] for r in self.conn.execute("SELECT DISTINCT mes FROM alertas_uso").fetchall()}
        self.assertEqual(meses, {anterior, mes_atual})

    def test_sem_limite_ou_sem_admin_nao_quebra(self):
        self.conn.execute("UPDATE empresas SET plano='' WHERE id=?", (self.ea,))
        self.conn.commit()
        self.minutos(500)
        self.assertEqual(telefonia.verificar_alertas(self.conn), 0)
        self.assertEqual(self.enviados, [])
        self.assertEqual(telefonia.verificar_alerta(self.conn, 999), [])

    def test_rota_do_dono_roda_os_alertas(self):
        self.minutos(85)
        s, d = self.req("POST", "/api/dono/telefonia/alertas", {})
        self.assertEqual((s, d["emails"]), (200, 2))


class TestArquivos(unittest.TestCase):
    def test_sem_travessoes(self):
        for arq in ("telefonia.py", "teste_telefonia.py", "public/js/dono.js", "public/js/i18n-dono.js", "erros_i18n.py"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)

    def test_textos_nos_tres_idiomas(self):
        with open(os.path.join(AQUI, "public", "js", "i18n-dono.js"), encoding="utf-8") as f:
            js = f.read()
        with open(os.path.join(AQUI, "public", "js", "dono.js"), encoding="utf-8") as f:
            usadas = set(re.findall(r'td\("(tel_[a-z_]*[a-z])"[,)]', f.read()))
        usadas |= {"tel_st_ativo", "tel_st_pendente", "tel_st_liberado", "tel_or_comprado", "tel_or_anexado"}
        for chave in usadas:
            self.assertEqual(js.count(chave + ":"), 3, chave)
        for lang in ("pt", "en", "es"):
            self.assertEqual(set(telefonia.TEXTOS[lang]), set(telefonia.TEXTOS["pt"]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
