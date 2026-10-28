"""
Testes das mensagens de texto (sms.py).

Nenhum SMS real: urllib.request.urlopen é trocado por um falso que imita a API
de mensagens da Twilio (o servidor local de teste continua com o urlopen real).
O relógio do módulo (sms.AGORA) é fixo para testar o horário de silêncio.

Uso:  python3 teste_sms.py
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
import unittest
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="sms-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import server  # noqa: E402
import sms  # noqa: E402

SID = "AC" + "1" * 32
TOKEN = "f" * 32
URL = "https://rh.exemplo.com"
NUM_PLAT = "+18605550100"
NUM_B = "+12035550199"           # número próprio da empresa B
TRACOS = re.compile("[%s%s]" % (chr(0x2013), chr(0x2014)))
URLOPEN_REAL = urllib.request.urlopen
MEIO_DIA = datetime(2026, 10, 27, 16, 0, tzinfo=timezone.utc)      # 12:00 em Nova York (EDT)
NOITE = datetime(2026, 10, 28, 2, 30, tzinfo=timezone.utc)         # 22:30 em Nova York
MANHA = datetime(2026, 10, 28, 12, 5, tzinfo=timezone.utc)         # 08:05 em Nova York


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


class FalsoTwilio:
    def __init__(self):
        self.pedidos = []
        self.erro = None      # (status, code, message) para a próxima mensagem
        self.n = 0

    def __call__(self, req, timeout=None, **kw):
        url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
        if url.startswith("http://127.0.0.1"):
            return URLOPEN_REAL(req, timeout=timeout or 30, **kw)
        assert timeout, "chamada externa sem timeout"
        corpo = req.data.decode("utf-8") if req.data else ""
        cab = {k.lower(): v for k, v in req.header_items()}
        self.pedidos.append({"metodo": req.get_method(), "url": url, "corpo": urllib.parse.parse_qs(corpo), "cab": cab})
        esperado = "Basic " + base64.b64encode(("%s:%s" % (SID, TOKEN)).encode()).decode()
        if cab.get("authorization") != esperado:
            return self._erro(url, 401, 20003, "Authenticate")
        if url.endswith("/Accounts/%s/Messages.json" % SID) and req.get_method() == "POST":
            if self.erro:
                st, code, msg = self.erro
                self.erro = None
                return self._erro(url, st, code, msg)
            self.n += 1
            corpo_sms = urllib.parse.parse_qs(corpo)["Body"][0]
            seg = sms.segmentos(corpo_sms)[0]
            dados = {"sid": "SM%032d" % self.n, "status": "queued", "num_segments": str(seg)}
            return Resposta(201, json.dumps(dados).encode())
        return self._erro(url, 404, 20404, "not found")

    def _erro(self, url, status, code, msg):
        raise urllib.error.HTTPError(url, status, "erro", {}, io.BytesIO(json.dumps({"code": code, "message": msg}).encode()))

    def mensagens(self):
        return [p for p in self.pedidos if p["url"].endswith("Messages.json")]


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
        self.ea, _ = empresas.criar_empresa(c, "Clean Co")
        self.eb, _ = empresas.criar_empresa(c, "Bright Homes")
        c.execute("INSERT INTO sessoes_dono (token) VALUES ('dono-tok')")
        for chave, valor in (("twilio_account_sid", SID), ("twilio_auth_token", TOKEN), ("url_publica", URL),
                             ("sms_numero_plataforma", NUM_PLAT)):
            server.config_set(c, chave, valor)
        c.execute("INSERT INTO numeros_empresa (empresa_id, numero, twilio_sid, status) VALUES (?,?,?, 'ativo')",
                  (self.eb, NUM_B, "PN" + "2" * 32))
        self.gestores = {}
        for login, eid, idioma in (("ana", self.ea, "en"), ("rui", self.ea, "pt"), ("bia", self.eb, "es")):
            gid = c.execute("INSERT INTO gestores (nome, login, senha, email, is_admin, aprovado, empresa_id, idioma)"
                            " VALUES (?,?, 'x', ?, 1, 1, ?, ?)",
                            (login.title(), login, login + "@exemplo.com", eid, idioma)).lastrowid
            c.execute("INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)", ("sess-" + login, gid))
            self.gestores[login] = gid
        self.maria = self.candidato("Maria Lopez", "(860) 555-0123", self.ea, "es")
        self.john = self.candidato("John Smith", "8605550124", self.ea, "en")
        self.lucas = self.candidato("Lucas Lima", "+1 203 555 0125", self.eb, "pt")
        c.commit()
        self.falso = FalsoTwilio()
        urllib.request.urlopen = self.falso
        sms.AGORA = lambda: MEIO_DIA
        sms.ENVIO_EM_SEGUNDO_PLANO = False
        self.enviados = []
        self._email = server.enviar_email

        def gravar(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt", cabecalhos=None):
            self.enviados.append({"para": para, "assunto": assunto, "corpo": corpo, "idioma": idioma})
            return True, "enviado"

        server.enviar_email = gravar

    def tearDown(self):
        urllib.request.urlopen = URLOPEN_REAL
        server.enviar_email = self._email
        sms.AGORA = None
        sms.ENVIO_EM_SEGUNDO_PLANO = True
        self.conn.close()

    # ---------------------------------------------------------------- ajudantes
    def candidato(self, nome, telefone, eid, idioma, consentiu=True):
        cid = self.conn.execute(
            "INSERT INTO candidatos (token, nome, email, local, telefone, idioma, empresa_id) VALUES (?,?,?,?,?,?,?)",
            ("tok-" + nome.replace(" ", "-").lower(), nome, nome.split()[0].lower() + "@mail.com", "", telefone, idioma, eid)
        ).lastrowid
        if consentiu:
            self.conn.execute("UPDATE candidatos SET consentimento_contato_em=datetime('now') WHERE id=?", (cid,))
        return cid

    def ligar(self, empresas_ids=None):
        server.config_set(self.conn, "sms_a2p", json.dumps({"status": "aprovado"}))
        server.config_set(self.conn, "sms_habilitado", "1")
        for eid in (empresas_ids if empresas_ids is not None else (self.ea, self.eb)):
            server.config_set(self.conn, "sms:%d" % eid, json.dumps({"ativo": True}))
        self.conn.commit()

    def req(self, metodo, caminho, dados=None, gestor=None, dono=False, idioma=None):
        h = {"Content-Type": "application/json"}
        if gestor:
            h["X-Gestor-Token"] = "sess-" + gestor
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

    def webhook(self, caminho, params, assinatura=None):
        corpo = urllib.parse.urlencode(params).encode()
        if assinatura is None:
            assinatura = sms.assinatura(URL + caminho, list(params.items()), TOKEN)
        r = urllib.request.Request(self.base + caminho, data=corpo, method="POST", headers={
            "Content-Type": "application/x-www-form-urlencoded", "X-Twilio-Signature": assinatura})
        try:
            with URLOPEN_REAL(r, timeout=30) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    def entrada(self, de, corpo, para=NUM_PLAT, sid=None):
        self._n = getattr(self, "_n", 0) + 1
        return self.webhook("/api/sms/entrada", {"From": de, "To": para, "Body": corpo, "AccountSid": SID,
                                                 "MessageSid": sid or "SMin%d" % self._n})

    def linhas(self, candidato_id):
        return self.conn.execute("SELECT * FROM sms_mensagens WHERE candidato_id=? ORDER BY id", (candidato_id,)).fetchall()


# ================================================================ desligado

class TestDesligado(Base):
    def test_desligado_por_padrao_nao_faz_nada(self):
        self.assertFalse(sms.config_global(self.conn)["habilitado"])
        for chave in sms.MODELOS:
            self.assertEqual(sms.enviar_modelo(self.conn, self.maria, chave, {"vaga": "Cleaner"}), "desligado")
        self.assertEqual(self.falso.pedidos, [])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM sms_mensagens").fetchone()[0], 0)
        s, d = self.req("GET", "/api/gestor/sms/candidato/%d" % self.maria, gestor="ana")
        self.assertEqual(s, 200)
        self.assertEqual((d["global"], d["motivo"]), (False, "desligado"))
        s, d = self.req("POST", "/api/gestor/sms/candidato/%d/responder" % self.maria, {"texto": "Hi"}, gestor="ana")
        self.assertEqual((d["ok"], d["status"]), (False, "desligado"))
        self.assertEqual(self.falso.pedidos, [])

    def test_ligar_exige_campanha_aprovada(self):
        s, d = self.req("POST", "/api/dono/sms", {"habilitado": True}, dono=True, idioma="en")
        self.assertEqual((s, d["erro"]), (400, "Mark the A2P campaign as approved before turning on text messages"))
        self.assertEqual(self.req("GET", "/api/dono/sms")[0], 401)
        s, d = self.req("POST", "/api/dono/sms", {"a2p": {"status": "aprovado", "brand_id": "BN123",
                                                          "campaign_id": "CM456"}, "habilitado": True}, dono=True)
        self.assertEqual(s, 200, d)
        self.assertTrue(d["habilitado"])
        self.assertEqual((d["a2p"]["brand_id"], d["a2p"]["campaign_id"]), ("BN123", "CM456"))
        self.assertEqual(d["webhook_entrada"], URL + "/api/sms/entrada")
        # campanha volta a "em análise": o envio desliga sozinho
        s, d = self.req("POST", "/api/dono/sms", {"a2p": {"status": "em_analise"}}, dono=True)
        self.assertFalse(d["habilitado"])
        s, d = self.req("POST", "/api/dono/sms", {"a2p": {"status": "xyz"}}, dono=True, idioma="es")
        self.assertEqual((s, d["erro"]), (400, "Estado A2P no válido"))
        s, d = self.req("POST", "/api/dono/sms", {"numero_plataforma": "123"}, dono=True, idioma="en")
        self.assertEqual(s, 400)

    def test_empresa_desligada(self):
        self.ligar(empresas_ids=[self.eb])
        self.assertEqual(sms.enviar_modelo(self.conn, self.maria, "convite_teste"), "empresa_desligada")
        s, d = self.req("POST", "/api/dono/sms/empresa/%d" % self.ea, {"ativo": True}, dono=True)
        self.assertEqual(s, 200, d)
        self.assertEqual(sms.enviar_modelo(self.conn, self.maria, "convite_teste"), "enviado")


# ================================================================ regras de envio

class TestRegras(Base):
    def test_envio_monta_pedido_da_twilio(self):
        self.ligar()
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "convite_teste", {"vaga": "House Cleaner"}), "enviado")
        p = self.falso.mensagens()[0]
        self.assertIn("/2010-04-01/Accounts/%s/Messages.json" % SID, p["url"])
        self.assertEqual(p["corpo"]["To"], ["+18605550124"])
        self.assertEqual(p["corpo"]["From"], [NUM_PLAT])
        self.assertEqual(p["corpo"]["StatusCallback"], [URL + "/api/sms/status"])
        corpo = p["corpo"]["Body"][0]
        self.assertTrue(corpo.startswith("Clean Co: Hi John, thanks for talking with us about the House Cleaner job!"))
        self.assertTrue(corpo.endswith("\nReply STOP to opt out."))
        self.assertIn("/candidato?token=tok-john-smith", corpo)
        # número próprio da empresa B e idioma do candidato
        self.assertEqual(sms.enviar_modelo(self.conn, self.lucas, "tentamos_ligar", {"vaga": "Faxina"}), "enviado")
        p = self.falso.mensagens()[1]
        self.assertEqual(p["corpo"]["From"], [NUM_B])
        self.assertIn("(203) 555-0199", p["corpo"]["Body"][0])
        self.assertTrue(p["corpo"]["Body"][0].endswith("\nResponda STOP para sair."))
        evs = [r["texto"] for r in self.conn.execute("SELECT texto FROM eventos WHERE candidato_id=?", (self.john,))]
        self.assertIn("SMS enviado: convite para os testes", evs)
        row = self.linhas(self.john)[0]
        self.assertEqual((row["status"], row["twilio_sid"][:2], row["direcao"]), ("queued", "SM", "saida"))

    def test_rodape_espanhol(self):
        self.ligar()
        self.assertEqual(sms.enviar_modelo(self.conn, self.maria, "candidatura_recebida", {"vaga": "Limpieza"}),
                         "enviado")
        corpo = self.falso.mensagens()[0]["corpo"]["Body"][0]
        self.assertTrue(corpo.startswith("Clean Co: Hola, Maria. Recibimos tu postulación para Limpieza."))
        self.assertTrue(corpo.endswith("\nResponde STOP para darte de baja."))

    def test_bloqueios(self):
        self.ligar()
        c = self.conn
        sem = self.candidato("Ana Fixo", "800-555-0100", self.ea, "en")
        self.assertEqual(sms.enviar_modelo(c, sem, "convite_teste"), "telefone_invalido")
        curto = self.candidato("Bob Curto", "5550100", self.ea, "en")
        self.assertEqual(sms.enviar_modelo(c, curto, "convite_teste"), "telefone_invalido")
        sem_consent = self.candidato("Carl Sem", "8605550177", self.ea, "en", consentiu=False)
        self.assertEqual(sms.enviar_modelo(c, sem_consent, "convite_teste"), "sem_consentimento")
        # a empresa pode desligar a exigência na configuração de SMS
        server.config_set(c, "sms:%d" % self.ea, json.dumps({"ativo": True, "exigir_consentimento": False}))
        c.commit()
        self.assertEqual(sms.enviar_modelo(c, sem_consent, "convite_teste"), "enviado")
        # ... mas se a empresa exige consentimento no conta.py, vale também para o SMS
        if getattr(server, "conta", None) is not None:
            server.config_set(c, "conta:%d" % self.ea, json.dumps({"so_com_consentimento": True}))
            c.commit()
            self.assertEqual(sms.enviar_modelo(c, sem_consent, "convite_teste"), "sem_consentimento")
        # revogação do contato (portal do candidato, conta.py)
        c.execute("UPDATE candidatos SET contato_revogado_em=datetime('now') WHERE id=?", (self.john,))
        c.commit()
        self.assertEqual(sms.enviar_modelo(c, self.john, "convite_teste"), "optout")
        self.assertEqual(sms.enviar_modelo(c, self.maria, "nao_existe"), "modelo_invalido")
        self.assertEqual(sms.enviar_modelo(c, 99999, "convite_teste"), "candidato_nao_encontrado")
        # sem número de envio (empresa A usa o da plataforma)
        server.config_set(c, "sms_numero_plataforma", "")
        c.commit()
        self.assertEqual(sms.enviar_modelo(c, self.maria, "convite_teste"), "sem_remetente")
        server.config_set(c, "twilio_auth_token", "")
        c.commit()
        self.assertEqual(sms.enviar_modelo(c, self.maria, "convite_teste"), "sem_twilio")

    def test_erros_da_twilio(self):
        self.ligar()
        self.falso.erro = (400, 21614, "To number is not a valid mobile number")
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "convite_teste"), "telefone_invalido")
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "convite_teste"), "telefone_invalido")
        self.assertEqual(len(self.falso.mensagens()), 1)  # o fixo fica marcado
        self.falso.erro = (400, 21610, "Attempt to send to unsubscribed recipient")
        self.assertEqual(sms.enviar_modelo(self.conn, self.maria, "convite_teste"), "optout")
        self.assertEqual(sms.enviar_modelo(self.conn, self.maria, "convite_teste"), "optout")
        self.falso.erro = (500, 20500, "Internal error " + TOKEN)
        self.assertEqual(sms.enviar_modelo(self.conn, self.lucas, "convite_teste"), "erro_envio")
        row = self.linhas(self.lucas)[-1]
        self.assertEqual(row["status"], "failed")
        self.assertNotIn(TOKEN, row["erro"])

    def test_nunca_lanca(self):
        self.ligar()
        self.conn.execute("DROP TABLE sms_optout")
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "convite_teste"), "erro_envio")


# ================================================================ horário de silêncio

class TestHorario(Base):
    def test_fora_do_horario_agenda_e_rotina_envia(self):
        self.ligar()
        sms.AGORA = lambda: NOITE
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "lembrete_entrevista",
                                           {"vaga": "Cleaner", "data": "Oct 29", "hora": "10:00 AM"}), "agendado")
        self.assertEqual(self.falso.mensagens(), [])
        row = self.linhas(self.john)[0]
        self.assertEqual((row["status"], row["agendado_para"]), ("agendado", "2026-10-28 12:00:00"))
        self.assertEqual(sms.processar_agendados(self.conn), 0)  # ainda é noite
        sms.AGORA = lambda: MANHA
        self.assertEqual(sms.processar_agendados(self.conn), 1)
        self.assertEqual(len(self.falso.mensagens()), 1)
        self.assertEqual(self.linhas(self.john)[0]["status"], "queued")
        self.assertEqual(sms.processar_agendados(self.conn), 0)

    def test_agendado_reconfere_regras(self):
        self.ligar()
        sms.AGORA = lambda: NOITE
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "convite_teste"), "agendado")
        sms._registrar_optout(self.conn, NUM_PLAT, "+18605550124", self.ea, "STOP")
        self.conn.commit()
        sms.AGORA = lambda: MANHA
        self.assertEqual(sms.processar_agendados(self.conn), 0)
        self.assertEqual(self.linhas(self.john)[0]["status"], "cancelado")
        self.assertEqual(self.falso.mensagens(), [])

    def test_fuso_da_empresa(self):
        self.ligar()
        # 16:00 UTC = 9:00 em Los Angeles: pode; 15:30 UTC = 8:30 em Los Angeles
        server.config_set(self.conn, "agenda:%d" % self.ea, json.dumps({"fuso": "America/Los_Angeles"}))
        self.conn.commit()
        self.assertIsNone(sms.proximo_horario(self.conn, self.ea, MEIO_DIA))
        cedo = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)  # 7:00 em LA, 10:00 em NY
        self.assertEqual(sms.proximo_horario(self.conn, self.ea, cedo), datetime(2026, 10, 27, 15, 0, tzinfo=timezone.utc))
        self.assertIsNone(sms.proximo_horario(self.conn, self.eb, cedo))


# ================================================================ STOP, START e HELP

class TestPalavras(Base):
    def test_stop_start_help_em_ingles(self):
        self.ligar()
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "convite_teste"), "enviado")
        s, xml = self.entrada("+18605550124", "STOP")
        self.assertEqual(s, 200)
        self.assertIn("<Message>Clean Co: You are unsubscribed and will not receive more text messages from us.", xml)
        s, xml = self.entrada("+18605550124", "stop")
        self.assertEqual(xml, '<?xml version="1.0" encoding="UTF-8"?><Response></Response>')  # confirma uma vez
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "convite_teste"), "optout")
        s, d = self.req("GET", "/api/gestor/sms/candidato/%d" % self.john, gestor="ana")
        self.assertTrue(d["optout"])
        self.assertEqual(d["motivo"], "optout")
        s, xml = self.entrada("+18605550124", "Help")
        self.assertIn("Clean Co: Text messages about your job application. Help: ana@exemplo.com.", xml)
        self.assertIn("Reply STOP to opt out.", xml)
        s, xml = self.entrada("+18605550124", "START")
        self.assertIn("You are resubscribed", xml)
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "convite_teste"), "enviado")
        evs = [r["texto"] for r in self.conn.execute("SELECT texto FROM eventos WHERE candidato_id=?", (self.john,))]
        self.assertIn("Pediu para não receber SMS (STOP)", evs)
        self.assertIn("Voltou a receber SMS (START)", evs)

    def test_palavras_em_espanhol(self):
        self.ligar()
        self.assertEqual(sms.enviar_modelo(self.conn, self.maria, "convite_teste"), "enviado")
        s, xml = self.entrada("+18605550123", "Parar")
        self.assertIn("Clean Co: Te diste de baja y no recibirás más mensajes de texto nuestros.", xml)
        self.assertEqual(sms.enviar_modelo(self.conn, self.maria, "convite_teste"), "optout")
        s, xml = self.entrada("+18605550123", "AYUDA")
        self.assertIn("Mensajes de texto sobre tu postulación", xml)
        s, xml = self.entrada("+18605550123", "start")
        self.assertIn("Volviste a recibir mensajes de texto", xml)
        # ALTO de um número desconhecido: descadastra e responde em espanhol
        s, xml = self.entrada("+13055550100", "ALTO")
        self.assertIn("Te diste de baja", xml)
        self.assertTrue(sms._optout(self.conn, NUM_PLAT, "+13055550100"))

    def test_outras_palavras_de_stop(self):
        self.ligar()
        for i, palavra in enumerate(("UNSUBSCRIBE", "cancel", "End", "QUIT", "stop.", "Opt out")):
            numero = "+1860555020%d" % i
            self.entrada(numero, palavra)
            self.assertTrue(sms._optout(self.conn, NUM_PLAT, numero), palavra)
        self.entrada("+18605550299", "Cancel my interview please")
        self.assertFalse(sms._optout(self.conn, NUM_PLAT, "+18605550299"))

    def test_stop_vale_por_numero_de_envio(self):
        self.ligar()
        # Lucas (empresa B, número próprio) manda STOP para o número da plataforma: B continua podendo enviar
        self.entrada("+12035550125", "STOP", para=NUM_PLAT)
        self.assertEqual(sms.enviar_modelo(self.conn, self.lucas, "convite_teste"), "enviado")
        self.entrada("+12035550125", "STOP", para=NUM_B)
        self.assertEqual(sms.enviar_modelo(self.conn, self.lucas, "convite_teste"), "optout")

    def test_sem_resposta_quando_desligado_mas_grava_stop(self):
        s, xml = self.entrada("+18605550124", "STOP")
        self.assertEqual(xml, '<?xml version="1.0" encoding="UTF-8"?><Response></Response>')
        self.assertTrue(sms._optout(self.conn, NUM_PLAT, "+18605550124"))

    def test_resposta_desligada_pelo_dono(self):
        self.ligar()
        server.config_set(self.conn, "sms_responder_palavras", "0")
        self.conn.commit()
        s, xml = self.entrada("+18605550124", "HELP")
        self.assertNotIn("<Message>", xml)


# ================================================================ assinatura

class TestAssinatura(Base):
    def test_exemplo_da_documentacao_da_twilio(self):
        # exemplo público da Twilio (token 12345, URL e parâmetros da documentação de segurança)
        pares = [("CallSid", "CA1234567890ABCDE"), ("Caller", "+14158675309"), ("Digits", "1234"),
                 ("From", "+14158675309"), ("To", "+18005551212")]
        self.assertEqual(sms.assinatura("https://mycompany.com/myapp.php?foo=1&bar=2", pares, "12345"),
                         "RSOYDt4T1cUTdK1PDd93/VVr8B8=")

    def test_assinatura_invalida_e_recusada(self):
        self.ligar()
        s, _ = self.webhook("/api/sms/entrada", {"From": "+18605550124", "To": NUM_PLAT, "Body": "STOP",
                                                 "AccountSid": SID}, assinatura="errada")
        self.assertEqual(s, 403)
        s, _ = self.webhook("/api/sms/entrada", {"From": "+18605550124", "To": NUM_PLAT, "Body": "STOP",
                                                 "AccountSid": SID}, assinatura="")
        self.assertEqual(s, 403)
        self.assertFalse(sms._optout(self.conn, NUM_PLAT, "+18605550124"))
        # assinatura certa, mas de outra conta
        params = {"From": "+18605550124", "To": NUM_PLAT, "Body": "STOP", "AccountSid": "AC" + "9" * 32}
        s, _ = self.webhook("/api/sms/entrada", params)
        self.assertEqual(s, 403)
        # sem credenciais da Twilio, nada passa
        server.config_set(self.conn, "twilio_auth_token", "")
        self.conn.commit()
        s, _ = self.webhook("/api/sms/status", {"MessageSid": "SM1", "MessageStatus": "delivered"}, assinatura="x")
        self.assertEqual(s, 403)

    def test_status_exige_assinatura(self):
        s, _ = self.webhook("/api/sms/status", {"MessageSid": "SM1", "MessageStatus": "delivered"}, assinatura="x")
        self.assertEqual(s, 403)


# ================================================================ conversa e resposta

class TestConversa(Base):
    def test_resposta_vira_conversa_e_avisa_admins(self):
        self.ligar()
        self.assertEqual(sms.enviar_modelo(self.conn, self.maria, "tentamos_ligar"), "enviado")
        s, xml = self.entrada("+18605550123", "Hola, puedo mañana a las 10?")
        self.assertNotIn("<Message>", xml)
        # e-mail para os dois administradores da empresa A, cada um no seu idioma
        por = {e["para"]: e for e in self.enviados}
        self.assertEqual(set(por), {"ana@exemplo.com", "rui@exemplo.com"})
        self.assertEqual(por["ana@exemplo.com"]["assunto"], "New text message from Maria Lopez")
        self.assertEqual(por["rui@exemplo.com"]["assunto"], "Nova mensagem de texto de Maria Lopez")
        self.assertIn("Hola, puedo mañana a las 10?", por["ana@exemplo.com"]["corpo"])
        s, d = self.req("GET", "/api/gestor/sms/candidato/%d" % self.maria, gestor="ana")
        self.assertEqual([m["direcao"] for m in d["mensagens"]], ["saida", "entrada"])
        self.assertEqual(self.conn.execute("SELECT lido FROM sms_mensagens WHERE direcao='entrada'").fetchone()[0], 1)
        s, d = self.req("POST", "/api/gestor/sms/candidato/%d/responder" % self.maria,
                        {"texto": "Sí, te esperamos a las 10."}, gestor="ana")
        self.assertEqual((s, d["ok"], d["status"]), (200, True, "enviado"))
        self.assertEqual(d["mensagens"][-1]["autor"], "Ana")
        self.assertTrue(self.falso.mensagens()[-1]["corpo"]["Body"][0].endswith("Responde STOP para darte de baja."))
        evs = [r["texto"] for r in self.conn.execute("SELECT texto FROM eventos WHERE candidato_id=?", (self.maria,))]
        self.assertIn("SMS recebido", evs)
        self.assertIn("SMS enviado: mensagem do gestor", evs)
        # repetição do webhook não duplica
        n = self.conn.execute("SELECT COUNT(*) FROM sms_mensagens").fetchone()[0]
        self.entrada("+18605550123", "Hola", sid="SMrepetido")
        self.entrada("+18605550123", "Hola", sid="SMrepetido")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM sms_mensagens").fetchone()[0], n + 1)

    def test_resposta_manual_valida_texto_e_modelo(self):
        self.ligar()
        s, d = self.req("POST", "/api/gestor/sms/candidato/%d/responder" % self.john, {"texto": "  "}, gestor="ana",
                        idioma="en")
        self.assertEqual((s, d["erro"]), (400, "Type the message"))
        s, d = self.req("POST", "/api/gestor/sms/candidato/%d/responder" % self.john, {"texto": "x" * 641},
                        gestor="ana", idioma="es")
        self.assertEqual(s, 400)
        s, d = self.req("POST", "/api/gestor/sms/candidato/%d/modelo" % self.john, {"chave": "xyz"}, gestor="ana")
        self.assertEqual(s, 400)
        s, d = self.req("POST", "/api/gestor/sms/candidato/%d/modelo" % self.john, {"chave": "tentamos_ligar"},
                        gestor="ana")
        self.assertEqual((d["status"], d["mensagens"][-1]["autor"]), ("enviado", "Ana"))

    def test_quem_escreveu_pode_receber_resposta_manual_sem_consentimento(self):
        self.ligar()
        sem = self.candidato("Pedro Novo", "8605550188", self.ea, "pt", consentiu=False)
        server.config_set(self.conn, "sms:%d" % self.ea, json.dumps({"ativo": True}))
        self.conn.commit()
        self.assertEqual(sms.enviar_modelo(self.conn, sem, "convite_teste"), "sem_consentimento")
        # número próprio de A para a mensagem chegar na empresa certa
        self.conn.execute("INSERT INTO numeros_empresa (empresa_id, numero, status) VALUES (?, '+18605550111', 'ativo')",
                          (self.ea,))
        self.conn.commit()
        self.entrada("+18605550188", "Oi, vi a vaga", para="+18605550111")
        s, d = self.req("POST", "/api/gestor/sms/candidato/%d/responder" % sem, {"texto": "Olá!"}, gestor="rui")
        self.assertEqual(d["status"], "enviado")
        self.assertEqual(sms.enviar_modelo(self.conn, sem, "convite_teste"), "sem_consentimento")

    def test_status_de_entrega(self):
        self.ligar()
        sms.enviar_modelo(self.conn, self.john, "convite_teste")
        msid = self.linhas(self.john)[0]["twilio_sid"]
        s, _ = self.webhook("/api/sms/status", {"MessageSid": msid, "MessageStatus": "sent", "AccountSid": SID})
        self.assertEqual(s, 200)
        self.webhook("/api/sms/status", {"MessageSid": msid, "MessageStatus": "delivered", "AccountSid": SID})
        self.webhook("/api/sms/status", {"MessageSid": msid, "MessageStatus": "sent", "AccountSid": SID})  # atrasado
        self.assertEqual(self.linhas(self.john)[0]["status"], "delivered")
        sms.enviar_modelo(self.conn, self.maria, "convite_teste")
        msid = self.linhas(self.maria)[0]["twilio_sid"]
        self.webhook("/api/sms/status", {"MessageSid": msid, "MessageStatus": "undelivered", "ErrorCode": "30006",
                                         "AccountSid": SID})
        row = self.linhas(self.maria)[0]
        self.assertEqual((row["status"], row["erro_codigo"]), ("undelivered", "30006"))
        self.assertEqual(sms.enviar_modelo(self.conn, self.maria, "convite_teste"), "telefone_invalido")


# ================================================================ uso e plano

class TestUso(Base):
    def test_segmentos(self):
        self.assertEqual(sms.segmentos("a" * 160), (1, "GSM-7"))
        self.assertEqual(sms.segmentos("a" * 161), (2, "GSM-7"))
        self.assertEqual(sms.segmentos("a" * 306), (2, "GSM-7"))
        self.assertEqual(sms.segmentos("a" * 307), (3, "GSM-7"))
        self.assertEqual(sms.segmentos("€" * 80), (1, "GSM-7"))       # extensão ocupa 2
        self.assertEqual(sms.segmentos("€" * 81), (2, "GSM-7"))
        self.assertEqual(sms.segmentos("ç" * 70), (1, "UCS-2"))
        self.assertEqual(sms.segmentos("Olá " * 18), (2, "UCS-2"))
        self.assertEqual(sms.segmentos("ñé" * 80), (1, "GSM-7"))

    def test_uso_por_empresa_e_limite_do_plano(self):
        self.ligar()
        c = self.conn
        c.execute("UPDATE empresas SET plano='voz300', status='ativa' WHERE id=?", (self.ea,))
        c.commit()
        self.assertEqual(sms.enviar_modelo(c, self.john, "convite_teste", {"vaga": "Cleaner"}), "enviado")
        u = sms.uso_mes(c, self.ea)
        self.assertEqual((u["mensagens"], u["limite"], u["ilimitado"]), (1, 300, False))
        self.assertEqual(u["segmentos"], self.linhas(self.john)[0]["segmentos"])
        self.assertEqual(sms.uso_mes(c, self.eb)["segmentos"], 0)  # isolamento
        # quase no limite: uma mensagem de 2 segmentos não cabe
        c.execute("INSERT INTO sms_mensagens (empresa_id, direcao, segmentos, twilio_sid, status, criado_em)"
                  " VALUES (?, 'saida', ?, 'SMvelho', 'delivered', ?)", (self.ea, 299 - u["segmentos"],
                                                                         sms._sql(MEIO_DIA)))
        c.commit()
        self.assertEqual(sms.uso_mes(c, self.ea)["segmentos"], 299)
        s, d = self.req("POST", "/api/gestor/sms/candidato/%d/responder" % self.john,
                        {"texto": "Hi John, " + "we look forward to meeting you. " * 6}, gestor="ana")
        self.assertEqual(d["status"], "limite_plano")
        self.assertEqual(sms.enviar_modelo(c, self.john, "candidatura_recebida", {"vaga": "Cleaner"}), "limite_plano")
        # excedente liberado (planos.py, só leitura) deixa passar
        c.execute("UPDATE empresas SET excedente_permitido=1 WHERE id=?", (self.ea,))
        c.commit()
        self.assertEqual(sms.enviar_modelo(c, self.john, "candidatura_recebida", {"vaga": "Cleaner"}), "enviado")
        u = sms.uso_mes(c, self.ea)
        self.assertGreater(u["excedente"], 0)
        # plano sem SMS (sms_mes 0) bloqueia
        c.execute("UPDATE empresas SET plano='essencial', excedente_permitido=0 WHERE id=?", (self.eb,))
        c.commit()
        self.assertEqual(sms.enviar_modelo(c, self.lucas, "convite_teste"), "limite_plano")
        # mês seguinte zera
        self.assertEqual(sms.uso_mes(c, self.ea, "2026-11")["segmentos"], 0)

    def test_uso_nas_rotas_do_gestor_e_do_dono(self):
        self.ligar()
        sms.enviar_modelo(self.conn, self.john, "convite_teste")
        sms.enviar_modelo(self.conn, self.lucas, "convite_teste")
        s, d = self.req("GET", "/api/gestor/sms/uso", gestor="ana")
        self.assertEqual((s, d["uso"]["mensagens"], d["global"], d["ativo"]), (200, 1, True, True))
        s, d = self.req("GET", "/api/dono/sms", dono=True)
        por = {e["id"]: e for e in d["empresas"]}
        self.assertEqual((por[self.ea]["uso"]["mensagens"], por[self.eb]["uso"]["mensagens"]), (1, 1))
        self.assertEqual(por[self.eb]["numero"], "(203) 555-0199")
        self.assertTrue(por[self.eb]["numero_proprio"])


# ================================================================ isolamento e configuração

class TestIsolamento(Base):
    def test_gestor_nao_ve_conversa_de_outra_empresa(self):
        self.ligar()
        sms.enviar_modelo(self.conn, self.lucas, "convite_teste")
        s, d = self.req("GET", "/api/gestor/sms/candidato/%d" % self.lucas, gestor="ana", idioma="en")
        self.assertEqual((s, d["erro"]), (404, "Candidate not found"))
        s, d = self.req("POST", "/api/gestor/sms/candidato/%d/responder" % self.lucas, {"texto": "oi"}, gestor="ana")
        self.assertEqual(s, 404)
        s, d = self.req("GET", "/api/gestor/sms/candidato/%d" % self.lucas, gestor="bia")
        self.assertEqual(len(d["mensagens"]), 1)

    def test_entrada_no_numero_proprio_fica_na_empresa_dona(self):
        self.ligar()
        # o mesmo celular é candidato nas duas empresas
        dupla = self.candidato("Lucas Dois", "+1 203 555 0125", self.ea, "pt")
        self.conn.commit()
        self.entrada("+12035550125", "Oi, ainda tem vaga?", para=NUM_B)
        row = self.conn.execute("SELECT * FROM sms_mensagens WHERE direcao='entrada'").fetchone()
        self.assertEqual((row["empresa_id"], row["candidato_id"]), (self.eb, self.lucas))
        self.assertEqual([e["para"] for e in self.enviados], ["bia@exemplo.com"])
        self.assertEqual(self.enviados[0]["assunto"], "Nuevo mensaje de texto de Lucas Lima")
        self.assertEqual(self.linhas(dupla), [])

    def test_entrada_no_numero_da_plataforma_segue_a_ultima_conversa(self):
        self.ligar()
        sms.enviar_modelo(self.conn, self.john, "convite_teste")
        self.entrada("+18605550124", "Sounds good")
        row = self.conn.execute("SELECT * FROM sms_mensagens WHERE direcao='entrada'").fetchone()
        self.assertEqual((row["empresa_id"], row["candidato_id"]), (self.ea, self.john))
        # desconhecido no número da plataforma: guarda sem empresa e sem aviso
        self.enviados.clear()
        self.entrada("+17185550100", "Who is this?")
        row = self.conn.execute("SELECT * FROM sms_mensagens WHERE direcao='entrada' ORDER BY id DESC").fetchone()
        self.assertEqual((row["empresa_id"], row["candidato_id"]), (None, None))
        self.assertEqual(self.enviados, [])

    def test_configuracao_da_empresa(self):
        s, d = self.req("GET", "/api/gestor/sms/config", gestor="ana")
        self.assertEqual((s, d["ativo"], d["exigir_consentimento"], d["global"]), (200, False, True, False))
        self.assertIn("convite_teste", d["padroes"])
        s, d = self.req("POST", "/api/gestor/sms/config", {"ativo": True, "contato_ajuda": "(860) 555-0000",
                                                          "modelos": {"convite_teste": {"en": "{empresa}: Hey {nome}! {link}"}}},
                        gestor="ana")
        self.assertEqual(s, 200, d)
        self.assertTrue(d["ativo"])
        self.assertEqual(d["modelos"]["convite_teste"]["en"], "{empresa}: Hey {nome}! {link}")
        s, d = self.req("POST", "/api/gestor/sms/config", {"modelos": {"xyz": {"en": "x"}}}, gestor="ana", idioma="en")
        self.assertEqual((s, d["erro"]), (400, "Invalid text message template"))
        s, d = self.req("POST", "/api/gestor/sms/config", {"modelos": {"convite_teste": {"en": "x" * 481}}},
                        gestor="ana")
        self.assertEqual(s, 400)
        # empresa B não é afetada
        self.assertFalse(sms.config_empresa(self.conn, self.eb)["ativo"])
        # gestor não administrador não altera
        gid = self.conn.execute("INSERT INTO gestores (nome, login, senha, email, is_admin, aprovado, empresa_id)"
                                " VALUES ('Leo', 'leo', 'x', '', 0, 1, ?)", (self.ea,)).lastrowid
        self.conn.execute("INSERT INTO sessoes_gestor (token, gestor_id) VALUES ('sess-leo', ?)", (gid,))
        self.conn.commit()
        s, d = self.req("POST", "/api/gestor/sms/config", {"ativo": False}, gestor="leo", idioma="es")
        self.assertEqual((s, d["erro"]), (403, "Solo el administrador de la empresa configura los SMS"))
        # o modelo personalizado e o contato da ajuda valem no envio
        self.ligar(empresas_ids=[])
        self.assertEqual(sms.enviar_modelo(self.conn, self.john, "convite_teste"), "enviado")
        self.assertTrue(self.falso.mensagens()[0]["corpo"]["Body"][0].startswith("Clean Co: Hey John! "))
        s, xml = self.entrada("+18605550124", "HELP")
        self.assertIn("Help: (860) 555-0000.", xml)


# ================================================================ textos

class TestTextos(unittest.TestCase):
    def test_sem_travessoes(self):
        for arq in ("sms.py", "teste_sms.py", "public/js/gestor-sms.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)

    def test_modelos_trilingues_com_rodape(self):
        for chave, textos in sms.MODELOS.items():
            self.assertEqual(set(textos), {"en", "pt", "es"}, chave)
            for lang, texto in textos.items():
                self.assertTrue(texto.startswith("{empresa}: "), (chave, lang))
                self.assertLessEqual(len(texto), sms.MAX_MODELO)
        for lang in ("en", "pt", "es"):
            self.assertTrue(sms.compor("Oi", lang).endswith(sms.RODAPE[lang]))
            self.assertEqual(sms.compor(sms.compor("Oi", lang), lang).count("STOP"), 1)

    def test_erros_e_eventos_traduzidos(self):
        import erros_i18n
        import eventos_i18n
        for erro in ("Escreva a mensagem", "Modelo de SMS inválido", "Status A2P inválido",
                     "Apenas o administrador da empresa configura o SMS",
                     "Marque a campanha A2P como aprovada antes de ligar o SMS"):
            for lang in ("en", "es"):
                self.assertNotEqual(erros_i18n.traduzir(erro, lang), erro)
        for rotulo in sms.ROTULO_EVENTO.values():
            self.assertTrue(eventos_i18n.cobre("SMS enviado: " + rotulo, "en"), rotulo)


if __name__ == "__main__":
    unittest.main(verbosity=1)
