"""
Testes do Google Agenda com Google Meet (google_cal.py + agenda.py): state
assinado (HMAC), troca do código e refresh token cifrado em repouso, freeBusy
tirando horários (com cache de 5 minutos), evento com pedido de Google Meet,
atualização na remarcação e exclusão no cancelamento, token revogado voltando
aos horários normais, rotas do dono e isolamento entre empresas.

Uso:  python3 teste_google_cal.py

Banco isolado numa pasta temporária (cópia de todos os .py que não são testes e
de public/). Nenhuma chamada real ao Google: urllib.request.urlopen é trocado
por um simulador, e qualquer endereço fora do simulador e do servidor local de
teste faz o teste falhar. Nenhum e-mail sai: o envio SMTP vira um gravador.
"""
import base64
import contextlib
import http.client
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
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from unittest import mock

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="google-cal-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)

import agenda  # noqa: E402
import empresas  # noqa: E402
import google_cal  # noqa: E402
import onboarding  # noqa: E402
import server  # noqa: E402

agenda.ENVIO_EM_SEGUNDO_PLANO = False
server.Handler.log_message = lambda *a: None
TRACOS = re.compile("[\u2013\u2014]")
URLOPEN_REAL = urllib.request.urlopen
REFRESH = "1//RT-segredo-do-teste"
MEET = "https://meet.google.com/abc-defg-hij"
CLIENT_ID = "123-abc.apps.googleusercontent.com"


def _jwt(email):
    corpo = base64.urlsafe_b64encode(json.dumps({"email": email}).encode()).decode().rstrip("=")
    return "e30." + corpo + ".assinatura"


class _Resposta:
    def __init__(self, status, dados):
        self.status = status
        self._bruto = json.dumps(dados).encode() if dados is not None else b""

    def read(self):
        return self._bruto

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class GoogleFalso:
    """Simula OAuth (accounts/oauth2) e a Calendar API v3."""

    def __init__(self):
        self.chamadas = []
        self.busy = []
        self.revogado = False
        self.expirar_uma_vez = False
        self.eventos = {}
        self.n_access = 0
        self.n_eventos = 0

    def __call__(self, req, *args, **kwargs):
        url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
        p = urllib.parse.urlparse(url)
        if p.hostname in ("127.0.0.1", "localhost"):
            return URLOPEN_REAL(req, *args, **kwargs)
        if p.hostname not in ("oauth2.googleapis.com", "www.googleapis.com", "accounts.google.com"):
            raise AssertionError("chamada real para fora do teste: %s" % url)
        metodo = req.get_method()
        bruto = req.data or b""
        cab = {k.lower(): v for k, v in req.header_items()}
        if cab.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            corpo = dict(urllib.parse.parse_qsl(bruto.decode()))
        else:
            corpo = json.loads(bruto or b"null")
        q = dict(urllib.parse.parse_qsl(p.query))
        self.chamadas.append({"metodo": metodo, "host": p.hostname, "path": p.path, "query": q, "corpo": corpo,
                              "auth": cab.get("authorization", "")})
        status, dados = self.rotear(metodo, p.hostname, p.path, q, corpo, cab.get("authorization", ""))
        if status >= 400:
            raise urllib.error.HTTPError(url, status, "erro", {}, io.BytesIO(json.dumps(dados).encode()))
        return _Resposta(status, dados)

    def _novo_access(self):
        self.n_access += 1
        return "ya29.access-%d" % self.n_access

    def rotear(self, metodo, host, path, q, corpo, auth):
        if host == "oauth2.googleapis.com" and path == "/token":
            if corpo.get("client_id") != CLIENT_ID or corpo.get("client_secret") != "GOCSPX-segredo":
                return 401, {"error": "invalid_client"}
            if corpo.get("grant_type") == "authorization_code":
                if corpo.get("code") == "bom":
                    return 200, {"access_token": self._novo_access(), "expires_in": 3599, "refresh_token": REFRESH,
                                 "id_token": _jwt("tony.google@example.com"), "token_type": "Bearer"}
                if corpo.get("code") == "sem-refresh":
                    return 200, {"access_token": self._novo_access(), "expires_in": 3599}
                return 400, {"error": "invalid_grant"}
            if corpo.get("grant_type") == "refresh_token":
                if self.revogado or corpo.get("refresh_token") != REFRESH:
                    return 400, {"error": "invalid_grant", "error_description": "Token has been expired or revoked."}
                return 200, {"access_token": self._novo_access(), "expires_in": 3599}
            return 400, {"error": "unsupported_grant_type"}
        if host == "oauth2.googleapis.com" and path == "/revoke":
            return 200, {}
        if host == "www.googleapis.com":
            if not auth.startswith("Bearer ya29."):
                return 401, {"error": {"code": 401, "status": "UNAUTHENTICATED"}}
            if self.expirar_uma_vez:
                self.expirar_uma_vez = False
                return 401, {"error": {"code": 401, "status": "UNAUTHENTICATED"}}
            if path == "/calendar/v3/freeBusy" and metodo == "POST":
                return 200, {"kind": "calendar#freeBusy", "timeMin": corpo["timeMin"], "timeMax": corpo["timeMax"],
                             "calendars": {"primary": {"busy": list(self.busy)}}}
            m = re.match(r"^/calendar/v3/calendars/([^/]+)/events(?:/([^/]+))?$", path)
            if m and metodo == "POST" and not m.group(2):
                self.n_eventos += 1
                ev = dict(corpo, id="evt%d" % self.n_eventos, status="confirmed")
                if corpo.get("conferenceData", {}).get("createRequest"):
                    ev["hangoutLink"] = MEET
                    ev["conferenceData"] = {"entryPoints": [{"entryPointType": "video", "uri": MEET}]}
                self.eventos[ev["id"]] = ev
                return 200, ev
            if m and m.group(2):
                ev = self.eventos.get(m.group(2))
                if not ev or ev.get("status") == "cancelled":
                    return 404, {"error": {"code": 404, "status": "NOT_FOUND"}}
                if metodo == "PATCH":
                    ev.update(corpo)
                    return 200, ev
                if metodo == "DELETE":
                    ev["status"] = "cancelled"
                    return 204, None
                if metodo == "GET":
                    return 200, ev
        return 404, {"error": {"code": 404}}

    def de(self, path_inicio, metodo=None):
        return [c for c in self.chamadas if c["path"].startswith(path_inicio) and (not metodo or c["metodo"] == metodo)]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.porta = cls.httpd.server_address[1]
        cls.base = "http://127.0.0.1:%d" % cls.porta
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        chave = os.path.join(server.BASE_DIR, onboarding.NOME_ARQUIVO_CHAVE)
        if os.path.exists(chave):
            os.remove(chave)
        onboarding.esquecer_chave()
        google_cal.esquecer_caches()
        google_cal.CACHE_OCUPADO = 300
        server.init_db()
        self.conn = c = server.db()
        self.ea, _ = empresas.criar_empresa(c, "Belleza's Home Services CT")
        self.eb, _ = empresas.criar_empresa(c, "Outra Empresa")
        self.cargo = c.execute("INSERT INTO cargos (nome, empresa_id, voz_ativa) VALUES ('Cleaning Tech', ?, 0)",
                               (self.ea,)).lastrowid
        self.vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id)"
                              " VALUES (?, 'House Cleaning Technician', 'aberta', ?)", (self.cargo, self.ea)).lastrowid
        self.g = {}
        for login, idioma, empresa, admin in (("tony", "pt", self.ea, 1), ("carine", "en", self.ea, 0),
                                              ("intruso", "pt", self.eb, 1)):
            gid = c.execute("INSERT INTO gestores (nome, login, senha, email, is_admin, aprovado, empresa_id, idioma)"
                            " VALUES (?,?,?,?,?,1,?,?)", (login.title(), login, "x", login + "@example.com", admin,
                                                         empresa, idioma)).lastrowid
            c.execute("INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)", ("sess-" + login, gid))
            self.g[login] = gid
        c.execute("INSERT INTO sessoes_dono (token) VALUES ('dono-tok')")
        server.config_set(c, "smtp_host", "smtp.teste")
        server.config_set(c, "smtp_remetente", "Equipe <rh@example.com>")
        server.config_set(c, "url_publica", "https://rh.tonybelleza.com")
        server.config_set(c, "google_client_id", CLIENT_ID)
        server.config_set(c, "google_client_secret", "GOCSPX-segredo")
        c.commit()
        self.enviados = []
        self._original = server.enviar_email

        def gravar(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt"):
            self.enviados.append({"para": para, "assunto": assunto, "corpo": corpo, "html": html or "",
                                  "anexos": anexos or []})
            return True, "enviado"

        server.enviar_email = gravar
        self.google = GoogleFalso()
        self._patch = mock.patch("urllib.request.urlopen", self.google)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        server.enviar_email = self._original
        self.conn.close()

    # ---------------------------------------------------------------- ajudas
    def req(self, metodo, caminho, dados=None, gestor=None, idioma=None, dono=False):
        cab = {"Content-Type": "application/json"}
        if gestor:
            cab["X-Gestor-Token"] = "sess-" + gestor
        if dono:
            cab["X-Dono-Token"] = "dono-tok"
        if idioma:
            cab["X-Idioma"] = idioma
        corpo = json.dumps(dados).encode() if dados is not None else None
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=cab)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def callback(self, query):
        """GET /api/google/callback sem seguir o redirecionamento: (status, Location)."""
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        c.request("GET", "/api/google/callback?" + urllib.parse.urlencode(query))
        r = c.getresponse()
        r.read()
        c.close()
        return r.status, r.getheader("Location")

    def conectar(self, login="tony"):
        st, d = self.req("POST", "/api/gestor/agenda/google/conectar", {}, gestor=login)
        self.assertEqual(st, 200, d)
        state = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(d["url"]).query))["state"]
        self.assertEqual(self.callback({"code": "bom", "state": state}), (302, "/gestor#google=ok"))

    def ligar_agenda(self, empresa=None, **extra):
        c = dict(agenda.PADRAO, ativo=True, dias=[1, 2, 3, 4, 5, 6, 7], inicio="09:00", fim="17:00", duracao=30,
                 intervalo=0, antecedencia_horas=0, horizonte_dias=7, fuso="America/New_York", bloqueios=[],
                 formato="video", local="", entrevistador="Carine")
        c.update(extra)
        agenda.salvar(self.conn, empresa or self.ea, c)

    def candidato(self, email="maria@example.com", nome="Maria Lopez", idioma="es", empresa=None):
        c = self.conn
        cid = c.execute("INSERT INTO candidatos (token, nome, email, local, telefone, idioma, empresa_id)"
                        " VALUES (?,?,?,?,?,?,?)", ("tok-" + email, nome, email, "", "+18605550101", idioma,
                                                    empresa or self.ea)).lastrowid
        if (empresa or self.ea) == self.ea:
            c.execute("INSERT INTO candidaturas (candidato_id, vaga_id, etapa) VALUES (?,?,'avaliacoes')", (cid, self.vaga))
        c.commit()
        return c.execute("SELECT * FROM candidatos WHERE id=?", (cid,)).fetchone()

    def horarios(self, cand):
        st, d = self.req("GET", "/api/agenda/" + agenda.token_do_candidato(self.conn, cand["id"]))
        self.assertEqual(st, 200, d)
        return [h["inicio_utc"] for dia in d["dias"] for h in dia["horarios"]]

    def marcar(self, cand, inicio):
        return self.req("POST", "/api/agenda/%s/marcar" % agenda.token_do_candidato(self.conn, cand["id"]),
                        {"inicio_utc": inicio})

    def ent(self, cand):
        return self.conn.execute("SELECT * FROM entrevistas_agenda WHERE candidato_id=? ORDER BY id DESC",
                                 (cand["id"],)).fetchone()


class TestState(Base):
    def test_assinatura_validade_e_uso_unico(self):
        s = google_cal.assinar_state(self.conn, self.g["tony"], self.ea)
        self.assertEqual(google_cal.verificar_state(self.conn, s, consumir=False)["g"], self.g["tony"])
        carga = google_cal.verificar_state(self.conn, s)
        self.assertEqual((carga["g"], carga["e"]), (self.g["tony"], self.ea))
        self.assertIsNone(google_cal.verificar_state(self.conn, s))          # uso único
        # carga trocada (outro gestor) com a assinatura antiga
        s2 = google_cal.assinar_state(self.conn, self.g["tony"], self.ea)
        corpo, sig = s2.split(".")
        falso = base64.urlsafe_b64encode(json.dumps(
            {"g": self.g["intruso"], "e": self.eb, "n": "x", "x": 9999999999}).encode()).decode().rstrip("=")
        self.assertIsNone(google_cal.verificar_state(self.conn, falso + "." + sig))
        self.assertIsNone(google_cal.verificar_state(self.conn, corpo + "." + sig[:-2] + "AA"))
        self.assertIsNone(google_cal.verificar_state(self.conn, "lixo"))
        self.assertIsNone(google_cal.verificar_state(self.conn, ""))
        # vencido
        velho = google_cal.assinar_state(self.conn, self.g["tony"], self.ea, agora=1000)
        self.assertIsNone(google_cal.verificar_state(self.conn, velho))

    def test_url_de_autorizacao(self):
        st, d = self.req("POST", "/api/gestor/agenda/google/conectar", {}, gestor="carine")
        self.assertEqual(st, 200, d)
        u = urllib.parse.urlparse(d["url"])
        q = dict(urllib.parse.parse_qsl(u.query))
        self.assertEqual(u.netloc + u.path, "accounts.google.com/o/oauth2/v2/auth")
        self.assertEqual((q["client_id"], q["redirect_uri"], q["response_type"], q["access_type"], q["prompt"]),
                         (CLIENT_ID, "https://rh.tonybelleza.com/api/google/callback", "code", "offline", "consent"))
        self.assertIn("https://www.googleapis.com/auth/calendar.events", q["scope"].split())
        self.assertIn("https://www.googleapis.com/auth/calendar.freebusy", q["scope"].split())
        self.assertEqual(google_cal.verificar_state(self.conn, q["state"], consumir=False)["g"], self.g["carine"])
        self.assertEqual(self.google.chamadas, [])                           # nada foi chamado ainda

    def test_sem_cliente_oauth(self):
        server.config_set(self.conn, "google_client_secret", "")
        self.conn.commit()
        st, d = self.req("POST", "/api/gestor/agenda/google/conectar", {}, gestor="tony", idioma="en")
        self.assertEqual((st, d["erro"]), (400, "Google Calendar is not set up on the platform"))
        self.assertFalse(self.req("GET", "/api/gestor/agenda/google", gestor="tony")[1]["disponivel"])


class TestConexao(Base):
    def test_troca_do_codigo_e_token_cifrado(self):
        erros = io.StringIO()
        with contextlib.redirect_stderr(erros):
            self.conectar("tony")
        troca = self.google.de("/token")[0]
        self.assertEqual((troca["corpo"]["grant_type"], troca["corpo"]["code"], troca["corpo"]["redirect_uri"]),
                         ("authorization_code", "bom", "https://rh.tonybelleza.com/api/google/callback"))
        row = google_cal.conta(self.conn, self.g["tony"])
        self.assertEqual((row["status"], row["email"], row["empresa_id"]), ("ativa", "tony.google@example.com", self.ea))
        self.assertNotIn(REFRESH, row["token_cifrado"])
        self.assertNotIn("RT-segredo", json.dumps([dict(r) for r in self.conn.execute("SELECT * FROM config")]))
        self.assertEqual(onboarding.decifrar_dict(self.conn, row["token_cifrado"])["refresh_token"], REFRESH)
        # o estado do gestor nunca devolve tokens
        st, d = self.req("GET", "/api/gestor/agenda/google", gestor="tony")
        self.assertEqual((st, d["minha"]["status"], d["minha"]["email"]), (200, "ativa", "tony.google@example.com"))
        self.assertNotIn("ya29", json.dumps(d))
        self.assertNotIn("RT-segredo", json.dumps(d))
        self.assertEqual([c["gestor_id"] for c in d["contas"]], [self.g["tony"]])
        self.assertNotIn("ya29", erros.getvalue())
        self.assertNotIn("RT-segredo", erros.getvalue())

    def test_callback_recusado_negado_ou_invalido(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self._callbacks_ruins()

    def _callbacks_ruins(self):
        self.assertEqual(self.callback({"code": "bom", "state": "falso.falso"}), (302, "/gestor#google=invalido"))
        s = google_cal.assinar_state(self.conn, self.g["tony"], self.ea)
        self.assertEqual(self.callback({"error": "access_denied", "state": s}), (302, "/gestor#google=negado"))
        s = google_cal.assinar_state(self.conn, self.g["tony"], self.ea)
        self.assertEqual(self.callback({"code": "ruim", "state": s}), (302, "/gestor#google=erro"))
        s = google_cal.assinar_state(self.conn, self.g["tony"], self.ea)
        self.assertEqual(self.callback({"code": "sem-refresh", "state": s}), (302, "/gestor#google=erro"))
        self.assertIsNone(google_cal.conta(self.conn, self.g["tony"]))
        # state de um gestor com a empresa trocada (gestor não pertence à empresa)
        s = google_cal.assinar_state(self.conn, self.g["tony"], self.eb)
        self.assertEqual(self.callback({"code": "bom", "state": s}), (302, "/gestor#google=invalido"))
        self.assertIsNone(google_cal.conta(self.conn, self.g["tony"]))

    def test_reconectar_sem_novo_refresh_mantem_o_antigo(self):
        self.conectar("tony")
        s = google_cal.assinar_state(self.conn, self.g["tony"], self.ea)
        self.assertEqual(self.callback({"code": "sem-refresh", "state": s}), (302, "/gestor#google=ok"))
        row = google_cal.conta(self.conn, self.g["tony"])
        self.assertEqual(onboarding.decifrar_dict(self.conn, row["token_cifrado"])["refresh_token"], REFRESH)

    def test_desconectar_revoga(self):
        self.conectar("tony")
        st, _ = self.req("POST", "/api/gestor/agenda/google/desconectar", {}, gestor="tony")
        self.assertEqual(st, 200)
        self.assertIsNone(google_cal.conta(self.conn, self.g["tony"]))
        rev = self.google.de("/revoke")
        self.assertEqual(len(rev), 1)
        self.assertEqual(rev[0]["corpo"]["token"], REFRESH)


class TestDisponibilidade(Base):
    def test_freebusy_tira_horarios_e_usa_cache(self):
        self.conectar("tony")
        self.ligar_agenda(google_entrevistadores=[self.g["tony"]])
        cand = self.candidato()
        sem_google = agenda.gerar_horarios(agenda.config(self.conn, self.ea))
        alvo = agenda.iso_utc(sem_google[3][0])
        self.google.busy = [{"start": alvo, "end": agenda.iso_utc(sem_google[3][0] + timedelta(minutes=30))}]
        livres = self.horarios(cand)
        self.assertNotIn(alvo, livres)
        self.assertIn(agenda.iso_utc(sem_google[2][0]), livres)
        fb = self.google.de("/calendar/v3/freeBusy")
        self.assertEqual(len(fb), 1)
        self.assertEqual(fb[0]["corpo"]["items"], [{"id": "primary"}])
        self.assertTrue(fb[0]["auth"].startswith("Bearer ya29."))
        # cache de 5 minutos: a segunda consulta não chama o Google
        self.horarios(cand)
        self.assertEqual(len(self.google.de("/calendar/v3/freeBusy")), 1)
        # com o cache vencido, consulta de novo
        google_cal.CACHE_OCUPADO = 0
        self.google.busy = []
        self.assertIn(alvo, self.horarios(cand))
        self.assertEqual(len(self.google.de("/calendar/v3/freeBusy")), 2)

    def test_horario_ocupado_no_google_nao_pode_ser_marcado(self):
        self.conectar("tony")
        self.ligar_agenda(google_entrevistadores=[self.g["tony"]], formato="presencial")
        cand = self.candidato()
        sem_google = agenda.gerar_horarios(agenda.config(self.conn, self.ea))
        ini = sem_google[1][0]
        # bloco com fuso e frações de segundo (formato RFC 3339 do Google)
        local = ini.astimezone(timezone(timedelta(hours=-5)))
        self.google.busy = [{"start": local.strftime("%Y-%m-%dT%H:%M:%S.000-05:00"),
                             "end": (local + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S-05:00")}]
        st, d = self.marcar(cand, agenda.iso_utc(ini))
        self.assertEqual(st, 409, d)

    def test_ocupado_no_google_nao_conta_no_limite_por_dia(self):
        cfg = dict(agenda.PADRAO, ativo=True, dias=[1, 2, 3, 4, 5, 6, 7], inicio="09:00", fim="11:00", duracao=30,
                   antecedencia_horas=0, horizonte_dias=0, max_por_dia=1, fuso="America/New_York")
        agora = datetime(2026, 11, 2, 11, 0, tzinfo=timezone.utc)   # 06:00 em Nova York
        externo = (datetime(2026, 11, 2, 14, 0, tzinfo=timezone.utc), datetime(2026, 11, 2, 14, 30, tzinfo=timezone.utc))
        h = agenda.gerar_horarios(cfg, (), agora, [externo])
        self.assertEqual([x[3] for x in h], ["09:30", "10:00", "10:30"])

    def test_remarcar_ignora_o_proprio_evento(self):
        blocos = [(datetime(2026, 11, 2, 14, 0, tzinfo=timezone.utc), datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc))]
        saida = agenda._subtrair(blocos, datetime(2026, 11, 2, 14, 30, tzinfo=timezone.utc),
                                 datetime(2026, 11, 2, 15, 0, tzinfo=timezone.utc))
        self.assertEqual(saida, [(blocos[0][0], datetime(2026, 11, 2, 14, 30, tzinfo=timezone.utc))])


class TestEventos(Base):
    def test_video_cria_evento_com_meet_atualiza_e_apaga(self):
        self.conectar("carine")
        self.conectar("tony")
        self.ligar_agenda(google_entrevistadores=[self.g["tony"], self.g["carine"]], google_organizador=self.g["carine"])
        cand = self.candidato(idioma="es")
        livres = self.horarios(cand)
        st, d = self.marcar(cand, livres[2])
        self.assertEqual(st, 200, d)
        criados = self.google.de("/calendar/v3/calendars/primary/events", "POST")
        self.assertEqual(len(criados), 1)
        ev = criados[0]
        self.assertEqual(ev["query"], {"sendUpdates": "none", "conferenceDataVersion": "1"})
        corpo = ev["corpo"]
        self.assertEqual(corpo["summary"], "Interview: Maria Lopez (House Cleaning Technician)")   # Carine usa inglês
        self.assertEqual(corpo["attendees"], [{"email": "maria@example.com", "displayName": "Maria Lopez"}])
        self.assertEqual(corpo["conferenceData"]["createRequest"]["conferenceSolutionKey"], {"type": "hangoutsMeet"})
        self.assertTrue(corpo["conferenceData"]["createRequest"]["requestId"])
        self.assertEqual(corpo["start"], {"dateTime": livres[2], "timeZone": "America/New_York"})
        self.assertIn("https://rh.tonybelleza.com/gestor#candidato=%d" % cand["id"], corpo["description"])
        self.assertNotIn("location", corpo)
        # o evento foi criado com o token da Carine (organizadora escolhida)
        carine_tokens = {c["auth"] for c in self.google.de("/calendar/v3/calendars")}
        self.assertEqual(len(carine_tokens), 1)
        ent = self.ent(cand)
        self.assertEqual((ent["google_evento_id"], ent["google_gestor_id"], ent["meet_link"]), ("evt1", self.g["carine"], MEET))
        # link do Meet nos e-mails, no .ics e na página do candidato
        email_c = [e for e in self.enviados if e["para"] == "maria@example.com"][0]
        self.assertIn(MEET, email_c["corpo"])
        self.assertIn(MEET, email_c["html"])
        self.assertIn("Unirse a la videollamada", email_c["html"])
        ics = email_c["anexos"][0][1].decode().replace("\r\n ", "")
        self.assertIn("LOCATION:" + MEET, ics)
        self.assertIn("URL:" + MEET, ics)
        email_g = [e for e in self.enviados if e["para"] == "carine@example.com"][0]
        self.assertIn(MEET, email_g["corpo"])
        st, d = self.req("GET", "/api/agenda/" + agenda.token_do_candidato(self.conn, cand["id"]))
        self.assertEqual(d["entrevista"]["meet_link"], MEET)
        st, d = self.req("GET", "/api/gestor/agenda/candidato/%d" % cand["id"], gestor="tony")
        self.assertEqual(d["entrevista"]["meet_link"], MEET)
        eventos = [r[0] for r in self.conn.execute("SELECT texto FROM eventos WHERE candidato_id=?", (cand["id"],))]
        self.assertIn("Google Agenda: evento criado com link do Google Meet", eventos)

        # remarcar: PATCH no mesmo evento, sem pedir outro Meet
        self.enviados.clear()
        novo = self.horarios(cand)[6]
        st, d = self.marcar(cand, novo)
        self.assertEqual(st, 200, d)
        patch = self.google.de("/calendar/v3/calendars/primary/events/evt1", "PATCH")
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0]["query"]["sendUpdates"], "none")
        self.assertEqual(patch[0]["corpo"]["start"]["dateTime"], novo)
        self.assertNotIn("conferenceData", patch[0]["corpo"])
        self.assertEqual(len(self.google.de("/calendar/v3/calendars/primary/events", "POST")), 1)
        self.assertEqual(self.ent(cand)["meet_link"], MEET)
        self.assertIn(MEET, [e for e in self.enviados if e["para"] == "maria@example.com"][0]["corpo"])

        # cancelar: DELETE do evento
        st, d = self.req("POST", "/api/agenda/%s/cancelar" % agenda.token_do_candidato(self.conn, cand["id"]))
        self.assertEqual(st, 200, d)
        apagados = self.google.de("/calendar/v3/calendars/primary/events/evt1", "DELETE")
        self.assertEqual(len(apagados), 1)
        self.assertEqual(apagados[0]["query"], {"sendUpdates": "none"})
        self.assertEqual(self.ent(cand)["google_evento_id"], "")
        self.assertEqual(self.google.eventos["evt1"]["status"], "cancelled")

    def test_presencial_sem_meet_e_com_local(self):
        self.conectar("tony")
        self.ligar_agenda(google_entrevistadores=[self.g["tony"]], formato="presencial", local="100 Main St")
        cand = self.candidato(idioma="en")
        st, d = self.marcar(cand, self.horarios(cand)[0])
        self.assertEqual(st, 200, d)
        corpo = self.google.de("/calendar/v3/calendars/primary/events", "POST")[0]["corpo"]
        self.assertNotIn("conferenceData", corpo)
        self.assertEqual(corpo["location"], "100 Main St")
        self.assertEqual(corpo["summary"], "Entrevista: Maria Lopez (House Cleaning Technician)")  # Tony usa português
        self.assertEqual(self.ent(cand)["meet_link"], "")

    def test_cancelado_pelo_gestor_apaga_evento(self):
        self.conectar("tony")
        self.ligar_agenda(google_entrevistadores=[self.g["tony"]])
        cand = self.candidato()
        self.marcar(cand, self.horarios(cand)[0])
        ent = self.ent(cand)
        st, d = self.req("POST", "/api/gestor/agenda/entrevista/%d/status" % ent["id"], {"status": "cancelada"}, gestor="tony")
        self.assertEqual(st, 200, d)
        self.assertEqual(len(self.google.de("/calendar/v3/calendars/primary/events/evt1", "DELETE")), 1)

    def test_access_token_vencido_renova_e_repete(self):
        self.conectar("tony")
        self.ligar_agenda(google_entrevistadores=[self.g["tony"]])
        cand = self.candidato()
        self.google.expirar_uma_vez = True
        self.horarios(cand)
        self.assertEqual(len(self.google.de("/calendar/v3/freeBusy")), 2)       # 401 e repetição
        self.assertEqual([c["corpo"]["grant_type"] for c in self.google.de("/token")],
                         ["authorization_code", "refresh_token"])
        self.assertEqual(google_cal.conta(self.conn, self.g["tony"])["status"], "ativa")


class TestRevogado(Base):
    def test_token_revogado_volta_aos_horarios_normais(self):
        self.conectar("tony")
        self.ligar_agenda(google_entrevistadores=[self.g["tony"]])
        cand = self.candidato()
        normais = [agenda.iso_utc(h[0]) for h in agenda.gerar_horarios(agenda.config(self.conn, self.ea))]
        self.google.busy = [{"start": normais[0], "end": normais[5]}]
        self.google.revogado = True
        google_cal.esquecer_caches()                     # o access token em memória "venceu"
        erros = io.StringIO()
        with contextlib.redirect_stderr(erros):
            livres = self.horarios(cand)
        self.assertEqual(livres[:5], normais[:5])         # o bloqueio do Google foi ignorado
        self.assertEqual(google_cal.conta(self.conn, self.g["tony"])["status"], "reconectar")
        self.assertNotIn(REFRESH, erros.getvalue())
        self.assertNotIn("ya29", erros.getvalue())
        st, d = self.req("GET", "/api/gestor/agenda/google", gestor="tony")
        self.assertEqual(d["minha"]["status"], "reconectar")
        # marcar continua funcionando, sem evento no Google
        st, d = self.marcar(cand, livres[0])
        self.assertEqual(st, 200, d)
        self.assertEqual(self.google.de("/calendar/v3/calendars"), [])
        self.assertEqual(self.ent(cand)["google_evento_id"], "")
        self.assertTrue([e for e in self.enviados if e["para"] == "maria@example.com"])
        # reconectar volta ao normal
        self.google.revogado = False
        self.conectar("tony")
        self.assertEqual(google_cal.conta(self.conn, self.g["tony"])["status"], "ativa")

    def test_google_fora_do_ar_nao_quebra_a_agenda(self):
        self.conectar("tony")
        self.ligar_agenda(google_entrevistadores=[self.g["tony"]])
        cand = self.candidato()

        def sem_rede(req, *a, **kw):
            url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
            if "127.0.0.1" in url:
                return URLOPEN_REAL(req, *a, **kw)
            raise urllib.error.URLError("sem rede")

        with mock.patch("urllib.request.urlopen", sem_rede), contextlib.redirect_stderr(io.StringIO()):
            google_cal.esquecer_caches()
            livres = self.horarios(cand)
            self.assertTrue(livres)
            st, d = self.marcar(cand, livres[0])
        self.assertEqual(st, 200, d)
        eventos = [r[0] for r in self.conn.execute("SELECT texto FROM eventos WHERE candidato_id=?", (cand["id"],))]
        self.assertIn("Google Agenda: não foi possível sincronizar o evento", eventos)


class TestIsolamento(Base):
    def test_outra_empresa_nao_usa_a_agenda_do_gestor(self):
        self.conectar("tony")
        self.ligar_agenda(self.eb)
        st, d = self.req("POST", "/api/gestor/agenda/config", {"google_entrevistadores": [self.g["tony"]]},
                         gestor="intruso", idioma="en")
        self.assertEqual((st, d["erro"]), (400, "Invalid interviewer"))
        # mesmo gravada à força, a agenda de outra empresa ignora a conta
        self.ligar_agenda(self.eb, google_entrevistadores=[self.g["tony"]])
        outro = self.candidato(email="b@example.com", empresa=self.eb)
        self.horarios(outro)
        self.assertEqual(self.google.de("/calendar/v3/freeBusy"), [])
        st, d = self.req("GET", "/api/gestor/agenda/google", gestor="intruso")
        self.assertEqual((d["minha"], d["contas"]), (None, []))
        # a própria empresa escolhe a conta normalmente; gestor sem administração não configura
        st, d = self.req("POST", "/api/gestor/agenda/config", {"google_entrevistadores": [self.g["tony"]],
                                                                "google_organizador": self.g["tony"]}, gestor="tony")
        self.assertEqual(st, 200, d)
        self.assertEqual(agenda.config(self.conn, self.ea)["google_entrevistadores"], [self.g["tony"]])
        self.assertEqual(self.req("POST", "/api/gestor/agenda/config", {"google_entrevistadores": []}, gestor="carine")[0], 403)
        # desconectada, a conta sai da lista na próxima gravação
        self.req("POST", "/api/gestor/agenda/google/desconectar", {}, gestor="tony")
        st, d = self.req("POST", "/api/gestor/agenda/config", {"duracao": 45}, gestor="tony")
        self.assertEqual((st, d["config"]["google_entrevistadores"], d["config"]["google_organizador"]), (200, [], 0))


class TestDono(Base):
    def test_cliente_oauth_no_painel_do_dono(self):
        self.assertEqual(self.req("GET", "/api/dono/google")[0], 401)
        st, d = self.req("GET", "/api/dono/google", dono=True)
        self.assertEqual(st, 200)
        self.assertEqual((d["client_id"], d["segredo_configurado"], d["redirect_uri"], d["configurado"]),
                         (CLIENT_ID, True, "https://rh.tonybelleza.com/api/google/callback", True))
        self.assertNotIn("GOCSPX-segredo", json.dumps(d))
        st, d = self.req("POST", "/api/dono/google", {"client_id": "qualquer"}, dono=True, idioma="es")
        self.assertEqual((st, d["erro"]), (400, "ID de cliente OAuth inválido (termina en .apps.googleusercontent.com)"))
        st, _ = self.req("POST", "/api/dono/google", {"client_id": "999-x.apps.googleusercontent.com",
                                                      "client_secret": "GOCSPX-novo"}, dono=True)
        self.assertEqual(st, 200)
        self.assertEqual(google_cal.credenciais(self.conn), ("999-x.apps.googleusercontent.com", "GOCSPX-novo"))
        self.assertEqual(self.req("POST", "/api/dono/google", {"remover": True}, dono=True)[0], 200)
        self.assertFalse(google_cal.configurado(self.conn))


class TestTextos(unittest.TestCase):
    def test_sem_travessoes(self):
        for arq in ("google_cal.py", "teste_google_cal.py", "agenda.py", "public/js/gestor-agenda.js",
                    "public/js/agendar.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)
        for arq, ini, fim in (("public/js/i18n-dono.js", "Google Agenda (google_cal.py)", "fim Google Agenda"),
                              ("public/js/dono.js", "async function secaoGoogleAgenda", "\n}\n")):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                texto = f.read()
            trecho = texto[texto.index(ini):]
            trecho = trecho[:trecho.index(fim) + len(fim)]
            self.assertIsNone(TRACOS.search(trecho), arq)

    def test_textos_nos_3_idiomas(self):
        self.assertEqual(set(google_cal.T["pt"]), set(google_cal.T["en"]))
        self.assertEqual(set(google_cal.T["pt"]), set(google_cal.T["es"]))
        with open(os.path.join(AQUI, "public/js/gestor-agenda.js"), encoding="utf-8") as f:
            js = f.read()
        blocos = re.split(r"Object\.assign\(I18N_GESTOR\.(?:pt|en|es), \{", js)[1:4]
        chaves = [set(re.findall(r"\b(ag_g_\w+|ag_meet):", b.split("\n});")[0])) for b in blocos]
        self.assertTrue(chaves[0])
        self.assertEqual(chaves[0], chaves[1])
        self.assertEqual(chaves[0], chaves[2])
        with open(os.path.join(AQUI, "public/js/i18n-dono.js"), encoding="utf-8") as f:
            dono = f.read()
        trecho = dono[dono.index("Google Agenda (google_cal.py)"):]
        blocos = re.split(r"Object\.assign\(I18N_DONO\.(?:pt|en|es), \{", trecho)[1:4]
        chaves = [set(re.findall(r"\b(g_\w+):", b.split("\n});")[0])) for b in blocos]
        self.assertTrue(chaves[0])
        self.assertEqual(chaves[0], chaves[1])
        self.assertEqual(chaves[0], chaves[2])

    def test_erros_traduzidos(self):
        import erros_i18n
        msgs = set()
        for arq in ("google_cal.py", "agenda.py"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                fonte = f.read()
            msgs |= set(re.findall(r'"erro": "([^"]+)"', fonte)) | set(re.findall(r'ErroGoogle\(\d+, "([^"]+)"\)', fonte))
            msgs |= set(re.findall(r'return None, "([^"]+)"', fonte))
        self.assertIn("Entrevistador inválido", msgs)
        for m in msgs:
            if m.endswith(": "):
                continue
            self.assertIn(m, erros_i18n.ERROS, m)
            self.assertNotEqual(erros_i18n.traduzir(m, "en"), m, m)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
