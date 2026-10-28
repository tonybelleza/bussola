"""Google Agenda (Google Calendar) nos dois sentidos, com links do Google Meet.

O dono da plataforma cria UM cliente OAuth no Google Cloud (ID e segredo do
cliente, salvos no Painel do Dono > Integrações). Cada gestor (entrevistador)
conecta a própria conta Google pela agenda de entrevistas: fluxo OAuth 2.0 web
(código de autorização, acesso offline), com o parâmetro state assinado por
HMAC e amarrado ao gestor e à empresa, válido por 10 minutos e de uso único.

O refresh token fica cifrado em repouso (Fernet do onboarding:
onboarding.cifrar_dict / decifrar_dict, só leitura) na tabela google_contas.
O access token vive só em memória. Tokens nunca vão para logs nem respostas.

A empresa escolhe, na configuração da agenda, quais contas conectadas valem
para as entrevistas ("google_entrevistadores") e em qual delas o evento é
criado ("google_organizador"). Então:
  1. Disponibilidade: os períodos ocupados (freeBusy) das agendas escolhidas
     saem dos horários livres; a consulta fica em cache por 5 minutos.
  2. Marcação: evento na agenda do entrevistador com o candidato como
     convidado (sendUpdates=none: os e-mails são os nossos) e, no formato
     videochamada, um link do Google Meet (conferenceDataVersion=1).
     Remarcar atualiza o evento; cancelar apaga.
  3. Token revogado ou expirado: a conta fica "reconectar", a agenda volta aos
     horários normais e o gestor vê o botão "Reconectar".

Só biblioteca padrão (urllib). Os testes trocam urllib.request.urlopen por um
simulador: nada sai para a internet.
"""
import base64
import hashlib
import hmac
import json
import re
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

srv = None  # módulo server, injetado por ligar()

URL_AUTORIZAR = "https://accounts.google.com/o/oauth2/v2/auth"
URL_TOKEN = "https://oauth2.googleapis.com/token"
URL_REVOGAR = "https://oauth2.googleapis.com/revoke"
URL_API = "https://www.googleapis.com/calendar/v3"
ESCOPOS = (
    "openid",
    "email",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
)
CAMINHO_CALLBACK = "/api/google/callback"
VALIDADE_STATE = 600      # segundos
CACHE_OCUPADO = 300       # segundos (5 minutos)
TIMEOUT = 10              # segundos por chamada ao Google

_trava = threading.Lock()
_tokens = {}       # gestor_id -> (access_token, expira_em_epoch)  (só memória)
_cache = {}        # gestor_id -> (criado_epoch, ini, fim, [(ini, fim), ...])
_states_usados = {}  # nonce -> expira_em_epoch (uso único do state)

# títulos e descrição do evento no idioma do gestor dono da agenda
T = {
    "pt": {"titulo": "Entrevista: {nome} ({vaga})", "titulo_sem_vaga": "Entrevista: {nome}",
           "ficha": "Ficha do candidato", "formato": "Formato", "local": "Local / instruções",
           "rodape": "Marcada pelo candidato na Bússola."},
    "en": {"titulo": "Interview: {nome} ({vaga})", "titulo_sem_vaga": "Interview: {nome}",
           "ficha": "Candidate profile", "formato": "Format", "local": "Location / instructions",
           "rodape": "Booked by the candidate in Bússola."},
    "es": {"titulo": "Entrevista: {nome} ({vaga})", "titulo_sem_vaga": "Entrevista: {nome}",
           "ficha": "Ficha del candidato", "formato": "Formato", "local": "Lugar / instrucciones",
           "rodape": "Agendada por el candidato en Bússola."},
}


class ErroGoogle(Exception):
    def __init__(self, status, mensagem):
        Exception.__init__(self, mensagem)
        self.status = status
        self.mensagem = mensagem


def ligar(modulo_server):
    global srv
    srv = modulo_server


def init_google(c):
    """Tabela das contas Google conectadas (uma por gestor). Chamada por agenda.init_agenda."""
    c.execute(
        "CREATE TABLE IF NOT EXISTS google_contas ("
        " gestor_id INTEGER PRIMARY KEY REFERENCES gestores(id) ON DELETE CASCADE,"
        " empresa_id INTEGER NOT NULL,"
        " email TEXT DEFAULT '',"
        " calendario TEXT NOT NULL DEFAULT 'primary',"
        " token_cifrado TEXT NOT NULL DEFAULT '',"
        " status TEXT NOT NULL DEFAULT 'ativa',"      # ativa | reconectar
        " erro TEXT DEFAULT '',"
        " conectado_em TEXT DEFAULT (datetime('now')),"
        " atualizado_em TEXT DEFAULT (datetime('now')))"
    )
    c.execute("CREATE INDEX IF NOT EXISTS ix_google_contas_empresa ON google_contas(empresa_id)")


def esquecer_caches():
    """Limpa tokens e cache em memória (testes)."""
    with _trava:
        _tokens.clear()
        _cache.clear()
        _states_usados.clear()


# ------------------------------------------------------------- configuração da plataforma

def credenciais(conn):
    return ((srv.config_get(conn, "google_client_id") or "").strip(),
            (srv.config_get(conn, "google_client_secret") or "").strip())


def configurado(conn):
    cid, seg = credenciais(conn)
    return bool(cid and seg)


def redirect_uri(conn):
    return srv.url_publica(conn) + CAMINHO_CALLBACK


# ------------------------------------------------------------- HTTP (nunca registra tokens)

def _http(metodo, url, dados=None, token=None, form=False):
    """(status, json). Falha de rede devolve (0, {})."""
    cab = {"Accept": "application/json"}
    corpo = None
    if dados is not None:
        if form:
            corpo = urllib.parse.urlencode(dados).encode("utf-8")
            cab["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            corpo = json.dumps(dados).encode("utf-8")
            cab["Content-Type"] = "application/json"
    if token:
        cab["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=corpo, method=metodo, headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            status, bruto = r.status, r.read()
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            bruto = e.read()
        except Exception:  # noqa: BLE001
            bruto = b""
    except (urllib.error.URLError, OSError, ValueError) as exc:
        sys.stderr.write("Google Agenda: sem conexão (%s %s): %s\n" % (
            metodo, url.split("?")[0], type(exc).__name__))
        return 0, {}
    try:
        d = json.loads(bruto or b"{}")
    except ValueError:
        d = {}
    return status, d if isinstance(d, dict) else {}


def _log_falha(onde, status, d):
    """Só o código de erro do Google, nunca tokens nem corpo inteiro."""
    erro = d.get("error")
    if isinstance(erro, dict):
        erro = erro.get("status") or erro.get("code")
    sys.stderr.write("Google Agenda: %s falhou (HTTP %s, %s)\n" % (onde, status, str(erro or "")[:60]))


# ------------------------------------------------------------- state assinado (HMAC)

def _b64(dados):
    return base64.urlsafe_b64encode(dados).decode("ascii").rstrip("=")


def _de_b64(texto):
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def _segredo_state(conn):
    s = srv.config_get(conn, "google_state_segredo")
    if not s:
        s = secrets.token_hex(32)
        srv.config_set(conn, "google_state_segredo", s)
        conn.commit()
    return s.encode("utf-8")


def assinar_state(conn, gestor_id, empresa_id, agora=None):
    carga = {"g": int(gestor_id), "e": int(empresa_id), "n": secrets.token_urlsafe(12),
             "x": int(agora if agora is not None else time.time()) + VALIDADE_STATE}
    corpo = _b64(json.dumps(carga, separators=(",", ":")).encode("utf-8"))
    assinatura = _b64(hmac.new(_segredo_state(conn), corpo.encode("ascii"), hashlib.sha256).digest())
    return corpo + "." + assinatura


def verificar_state(conn, state, agora=None, consumir=True):
    """Carga {"g", "e", "n", "x"} do state válido, ou None (assinatura, validade, uso único)."""
    try:
        corpo, assinatura = str(state or "").split(".", 1)
        esperado = _b64(hmac.new(_segredo_state(conn), corpo.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(esperado, assinatura):
            return None
        carga = json.loads(_de_b64(corpo).decode("utf-8"))
    except (ValueError, UnicodeError, TypeError):
        return None
    agora = int(agora if agora is not None else time.time())
    if not isinstance(carga, dict) or int(carga.get("x") or 0) < agora:
        return None
    with _trava:
        for n, exp in list(_states_usados.items()):
            if exp < agora:
                del _states_usados[n]
        if carga.get("n") in _states_usados:
            return None
        if consumir:
            _states_usados[carga.get("n")] = int(carga["x"])
    return carga


def url_autorizacao(conn, gestor):
    if not configurado(conn):
        raise ErroGoogle(400, "O Google Agenda não está configurado na plataforma")
    cid, _ = credenciais(conn)
    params = {
        "client_id": cid,
        "redirect_uri": redirect_uri(conn),
        "response_type": "code",
        "scope": " ".join(ESCOPOS),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": assinar_state(conn, gestor["id"], gestor["empresa_id"]),
    }
    email = (gestor["email"] if "email" in gestor.keys() else "") or ""
    if email.strip():
        params["login_hint"] = email.strip()
    return URL_AUTORIZAR + "?" + urllib.parse.urlencode(params)


# ------------------------------------------------------------- tokens cifrados

def _cifrar(conn, dados):
    return srv.onboarding.cifrar_dict(conn, dados)


def _decifrar(conn, texto):
    return srv.onboarding.decifrar_dict(conn, texto)


def conta(conn, gestor_id):
    return conn.execute("SELECT * FROM google_contas WHERE gestor_id=?", (int(gestor_id or 0),)).fetchone()


def _email_do_id_token(id_token):
    """E-mail da conta conectada (o id_token vem direto do Google por TLS)."""
    try:
        return str(json.loads(_de_b64(str(id_token).split(".")[1]).decode("utf-8")).get("email") or "")[:200]
    except (ValueError, IndexError, UnicodeError, AttributeError):
        return ""


def trocar_codigo(conn, codigo):
    cid, seg = credenciais(conn)
    st, d = _http("POST", URL_TOKEN, {
        "code": codigo, "client_id": cid, "client_secret": seg,
        "redirect_uri": redirect_uri(conn), "grant_type": "authorization_code"}, form=True)
    if st != 200 or not d.get("access_token"):
        _log_falha("troca do código", st, d)
        raise ErroGoogle(400, "Não foi possível conectar ao Google Agenda. Tente de novo.")
    return d


def salvar_conexao(conn, gestor, d):
    """Grava a conexão do gestor (refresh token cifrado) a partir da resposta do token."""
    gid = int(gestor["id"])
    refresh = d.get("refresh_token") or ""
    atual = conta(conn, gid)
    if not refresh and atual and atual["token_cifrado"]:
        try:
            refresh = _decifrar(conn, atual["token_cifrado"]).get("refresh_token") or ""
        except Exception:  # noqa: BLE001
            refresh = ""
    if not refresh:
        raise ErroGoogle(400, "O Google não liberou o acesso contínuo. Remova o acesso da Bússola na sua Conta Google e conecte de novo.")
    email = _email_do_id_token(d.get("id_token")) or (atual["email"] if atual else "")
    cifrado = _cifrar(conn, {"refresh_token": refresh})
    conn.execute(
        "INSERT INTO google_contas (gestor_id, empresa_id, email, token_cifrado, status, erro)"
        " VALUES (?,?,?,?,'ativa','')"
        " ON CONFLICT(gestor_id) DO UPDATE SET empresa_id=excluded.empresa_id, email=excluded.email,"
        " token_cifrado=excluded.token_cifrado, status='ativa', erro='', atualizado_em=datetime('now')",
        (gid, int(gestor["empresa_id"]), email, cifrado))
    conn.commit()
    with _trava:
        _tokens[gid] = (d["access_token"], time.time() + int(d.get("expires_in") or 3600))
        _cache.pop(gid, None)


def _marcar_reconectar(conn, gestor_id, motivo):
    with _trava:
        _tokens.pop(gestor_id, None)
        _cache.pop(gestor_id, None)
    conn.execute("UPDATE google_contas SET status='reconectar', erro=?, atualizado_em=datetime('now')"
                 " WHERE gestor_id=?", (motivo[:120], gestor_id))
    conn.commit()
    sys.stderr.write("Google Agenda: conta do gestor %d precisa reconectar (%s)\n" % (gestor_id, motivo[:60]))


def _access_token(conn, gestor_id, renovar=False):
    """Access token válido (renova com o refresh token). None se a conta não está ativa."""
    gestor_id = int(gestor_id)
    with _trava:
        atual = _tokens.get(gestor_id)
        if atual and not renovar and atual[1] > time.time() + 60:
            return atual[0]
    row = conta(conn, gestor_id)
    if not row or row["status"] != "ativa" or not row["token_cifrado"]:
        return None
    try:
        refresh = _decifrar(conn, row["token_cifrado"]).get("refresh_token") or ""
    except Exception:  # noqa: BLE001  (chave trocada: o token antigo não abre mais)
        _marcar_reconectar(conn, gestor_id, "token ilegivel")
        return None
    cid, seg = credenciais(conn)
    if not (cid and seg):
        return None
    st, d = _http("POST", URL_TOKEN, {"client_id": cid, "client_secret": seg, "refresh_token": refresh,
                                      "grant_type": "refresh_token"}, form=True)
    if st == 200 and d.get("access_token"):
        with _trava:
            _tokens[gestor_id] = (d["access_token"], time.time() + int(d.get("expires_in") or 3600))
        return d["access_token"]
    if st in (400, 401) and d.get("error") == "invalid_grant":
        _marcar_reconectar(conn, gestor_id, "invalid_grant")
    else:
        _log_falha("renovação do token", st, d)
    return None


def _api(conn, gestor_id, metodo, caminho, dados=None):
    """Chamada à Calendar API em nome do gestor. (status, json); (None, {}) sem conta ativa."""
    for tentativa in (0, 1):
        token = _access_token(conn, gestor_id, renovar=bool(tentativa))
        if not token:
            return None, {}
        st, d = _http(metodo, URL_API + caminho, dados, token=token)
        if st == 401 and tentativa == 0:
            with _trava:
                _tokens.pop(int(gestor_id), None)
            continue
        return st, d
    return None, {}


def desconectar(conn, gestor_id):
    row = conta(conn, gestor_id)
    if not row:
        return False
    try:
        refresh = _decifrar(conn, row["token_cifrado"]).get("refresh_token") if row["token_cifrado"] else ""
    except Exception:  # noqa: BLE001
        refresh = ""
    if refresh:  # melhor esforço: revoga no Google
        st, d = _http("POST", URL_REVOGAR, {"token": refresh}, form=True)
        if st not in (200, 400):
            _log_falha("revogação", st, d)
    conn.execute("DELETE FROM google_contas WHERE gestor_id=?", (int(gestor_id),))
    conn.commit()
    with _trava:
        _tokens.pop(int(gestor_id), None)
        _cache.pop(int(gestor_id), None)
    return True


# ------------------------------------------------------------- disponibilidade (freeBusy)

def _iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ler_rfc3339(texto):
    texto = str(texto or "").strip()
    if texto.endswith("Z") or texto.endswith("z"):
        texto = texto[:-1] + "+00:00"
    texto = re.sub(r"\.\d+(?=[+-]\d\d:\d\d$)", "", texto)  # frações de segundo
    dt = datetime.fromisoformat(texto)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def contas_validas(conn, empresa_id, ids):
    """Só contas da própria empresa (isolamento), na ordem pedida."""
    saida = []
    for gid in ids or []:
        try:
            gid = int(gid)
        except (TypeError, ValueError):
            continue
        row = conn.execute("SELECT gc.* FROM google_contas gc JOIN gestores g ON g.id=gc.gestor_id"
                           " WHERE gc.gestor_id=? AND gc.empresa_id=? AND g.empresa_id=? AND g.aprovado=1",
                           (gid, empresa_id, empresa_id)).fetchone()
        if row and gid not in [r["gestor_id"] for r in saida]:
            saida.append(row)
    return saida


def _ocupado_gestor(conn, row, ini, fim):
    gid = row["gestor_id"]
    agora = time.time()
    with _trava:
        c = _cache.get(gid)
        if c and agora - c[0] < CACHE_OCUPADO and c[1] <= ini and c[2] >= fim:
            return list(c[3])
    if row["status"] != "ativa":
        return []
    cal = row["calendario"] or "primary"
    st, d = _api(conn, gid, "POST", "/freeBusy", {"timeMin": _iso(ini), "timeMax": _iso(fim), "items": [{"id": cal}]})
    if st is None:
        return []
    if st != 200:
        _log_falha("freeBusy", st, d)
        return []
    calendarios = d.get("calendars") or {}
    info = calendarios.get(cal)
    if info is None and len(calendarios) == 1:
        info = list(calendarios.values())[0]
    info = info or {}
    if info.get("errors"):
        _log_falha("freeBusy (agenda)", st, {"error": (info["errors"][0] or {}).get("reason")})
        return []
    blocos = []
    for b in info.get("busy") or []:
        try:
            blocos.append((_ler_rfc3339(b["start"]), _ler_rfc3339(b["end"])))
        except (KeyError, ValueError, TypeError):
            continue
    with _trava:
        _cache[gid] = (agora, ini, fim, list(blocos))
    return blocos


def ocupados(conn, empresa_id, ids, ini, fim):
    """Períodos ocupados [(ini, fim)] em UTC nas agendas escolhidas pela empresa.
    Qualquer falha devolve o que deu para ler (no pior caso, lista vazia)."""
    blocos = []
    for row in contas_validas(conn, empresa_id, ids):
        try:
            blocos += _ocupado_gestor(conn, row, ini, fim)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Google Agenda: freeBusy falhou: %s\n" % type(exc).__name__)
    return blocos


def limpar_cache(gestor_id=None):
    with _trava:
        if gestor_id is None:
            _cache.clear()
        else:
            _cache.pop(int(gestor_id), None)


# ------------------------------------------------------------- eventos

def titulo_evento(lang, nome, vaga):
    lang = lang if lang in T else "pt"
    if vaga:
        return T[lang]["titulo"].format(nome=nome, vaga=vaga)
    return T[lang]["titulo_sem_vaga"].format(nome=nome)


def corpo_evento(titulo, descricao, inicio, fim, fuso, convidado_email="", convidado_nome="", local="",
                 meet=False, request_id=""):
    """Corpo do evento (Calendar API v3). meet=True pede um link do Google Meet."""
    corpo = {
        "summary": titulo,
        "description": descricao,
        "start": {"dateTime": _iso(inicio), "timeZone": fuso},
        "end": {"dateTime": _iso(fim), "timeZone": fuso},
        "reminders": {"useDefault": True},
        "guestsCanModify": False,
        "guestsCanInviteOthers": False,
    }
    if convidado_email:
        corpo["attendees"] = [{"email": convidado_email, "displayName": convidado_nome or convidado_email}]
    if local:
        corpo["location"] = local
    if meet:
        corpo["conferenceData"] = {"createRequest": {
            "requestId": request_id or secrets.token_hex(12),
            "conferenceSolutionKey": {"type": "hangoutsMeet"}}}
    return corpo


def link_meet(evento):
    if not isinstance(evento, dict):
        return ""
    if evento.get("hangoutLink"):
        return str(evento["hangoutLink"])
    for p in ((evento.get("conferenceData") or {}).get("entryPoints") or []):
        if p.get("entryPointType") == "video" and p.get("uri"):
            return str(p["uri"])
    return ""


def _cal(calendario):
    return urllib.parse.quote(calendario or "primary", safe="")


def criar_evento(conn, gestor_id, corpo):
    """(evento_id, link_meet) ou (None, '') se falhar."""
    row = conta(conn, gestor_id)
    if not row:
        return None, ""
    cal = row["calendario"] or "primary"
    st, d = _api(conn, gestor_id, "POST", "/calendars/%s/events?sendUpdates=none&conferenceDataVersion=1" % _cal(cal), corpo)
    if st not in (200, 201) or not d.get("id"):
        if st is not None:
            _log_falha("criar evento", st, d)
        return None, ""
    meet = link_meet(d)
    if not meet and corpo.get("conferenceData"):
        # a sala do Meet pode ficar "pending" por um instante: uma releitura basta
        st2, d2 = _api(conn, gestor_id, "GET", "/calendars/%s/events/%s" % (_cal(cal), urllib.parse.quote(d["id"], safe="")))
        if st2 == 200:
            meet = link_meet(d2)
    limpar_cache(gestor_id)
    return d["id"], meet


def atualizar_evento(conn, gestor_id, evento_id, corpo):
    """PATCH do evento. (ok, link_meet)."""
    row = conta(conn, gestor_id)
    if not row or not evento_id:
        return False, ""
    cal = row["calendario"] or "primary"
    st, d = _api(conn, gestor_id, "PATCH", "/calendars/%s/events/%s?sendUpdates=none&conferenceDataVersion=1" % (
        _cal(cal), urllib.parse.quote(evento_id, safe="")), corpo)
    if st != 200:
        if st is not None:
            _log_falha("atualizar evento", st, d)
        return False, ""
    limpar_cache(gestor_id)
    return True, link_meet(d)


def apagar_evento(conn, gestor_id, evento_id):
    """DELETE do evento. Evento que já não existe (404, 410) conta como apagado."""
    row = conta(conn, gestor_id)
    if not row or not evento_id:
        return False
    cal = row["calendario"] or "primary"
    st, d = _api(conn, gestor_id, "DELETE", "/calendars/%s/events/%s?sendUpdates=none" % (
        _cal(cal), urllib.parse.quote(evento_id, safe="")))
    limpar_cache(gestor_id)
    if st in (200, 204, 404, 410):
        return True
    if st is not None:
        _log_falha("apagar evento", st, d)
    return False


# ------------------------------------------------------------- respostas da API

def _conta_publica(row, nome=""):
    if not row:
        return None
    return {"gestor_id": row["gestor_id"], "nome": nome, "email": row["email"] or "", "status": row["status"],
            "conectado_em": row["conectado_em"] or "", "atualizado_em": row["atualizado_em"] or ""}


def estado_gestor(conn, gestor):
    """Situação do Google Agenda para o painel do gestor."""
    saida = {"disponivel": configurado(conn), "minha": _conta_publica(conta(conn, gestor["id"]), gestor["nome"])}
    if gestor["is_admin"]:
        saida["contas"] = [_conta_publica(r, r["nome"]) for r in conn.execute(
            "SELECT gc.*, g.nome FROM google_contas gc JOIN gestores g ON g.id=gc.gestor_id"
            " WHERE gc.empresa_id=? AND g.empresa_id=? AND g.aprovado=1 ORDER BY g.nome",
            (gestor["empresa_id"], gestor["empresa_id"])).fetchall()]
    return saida


def _resp(h, status, dados):
    h._json(status, dados)
    return True


def _redirecionar(h, destino):
    h.send_response(302)
    h.send_header("Location", destino)
    h.send_header("Content-Length", "0")
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    return True


def rotear_publico(h, method, path, conn):
    """GET /api/google/callback?code=...&state=... (volta do consentimento do Google)."""
    if path != CAMINHO_CALLBACK:
        return None
    if method != "GET":
        return _resp(h, 405, {"erro": "Método não permitido"})
    q = urllib.parse.parse_qs(urllib.parse.urlparse(h.path).query)
    pegar = lambda k: (q.get(k) or [""])[0]  # noqa: E731
    carga = verificar_state(conn, pegar("state"))
    if not carga:
        return _redirecionar(h, "/gestor#google=invalido")
    if pegar("error") or not pegar("code"):
        return _redirecionar(h, "/gestor#google=negado")
    gestor = conn.execute("SELECT * FROM gestores WHERE id=? AND empresa_id=? AND aprovado=1",
                          (carga["g"], carga["e"])).fetchone()
    if not gestor or not configurado(conn):
        return _redirecionar(h, "/gestor#google=invalido")
    try:
        salvar_conexao(conn, gestor, trocar_codigo(conn, pegar("code")))
    except ErroGoogle:
        return _redirecionar(h, "/gestor#google=erro")
    except Exception as exc:  # noqa: BLE001  (ex.: chave de criptografia indisponível)
        sys.stderr.write("Google Agenda: falha ao salvar a conexão: %s\n" % type(exc).__name__)
        return _redirecionar(h, "/gestor#google=erro")
    return _redirecionar(h, "/gestor#google=ok")


def rotear_gestor(h, method, path, conn, gestor):
    """/api/gestor/agenda/google (estado), /conectar e /desconectar. Chamado por agenda.rotear_gestor."""
    if not path.startswith("/api/gestor/agenda/google"):
        return None
    if method == "GET" and path == "/api/gestor/agenda/google":
        return _resp(h, 200, estado_gestor(conn, gestor))
    if method == "POST" and path == "/api/gestor/agenda/google/conectar":
        if "sessao_suporte" in gestor.keys() and gestor["sessao_suporte"]:
            return _resp(h, 403, {"erro": "Indisponível no modo suporte"})
        try:
            return _resp(h, 200, {"url": url_autorizacao(conn, gestor)})
        except ErroGoogle as e:
            return _resp(h, e.status, {"erro": e.mensagem})
    if method == "POST" and path == "/api/gestor/agenda/google/desconectar":
        desconectar(conn, gestor["id"])
        return _resp(h, 200, {"ok": True})
    return _resp(h, 404, {"erro": "Rota não encontrada"})


def rotear_dono(h, method, path, conn):
    """GET/POST /api/dono/google: cliente OAuth da plataforma (ID e segredo)."""
    if path != "/api/dono/google":
        return None
    if method == "GET":
        cid, seg = credenciais(conn)
        n = conn.execute("SELECT COUNT(*) FROM google_contas WHERE status='ativa'").fetchone()[0]
        return _resp(h, 200, {"client_id": cid, "segredo_configurado": bool(seg),
                              "segredo_final": seg[-4:] if len(seg) >= 8 else "",
                              "redirect_uri": redirect_uri(conn), "configurado": bool(cid and seg),
                              "contas_conectadas": n, "escopos": list(ESCOPOS)})
    if method == "POST":
        d = h._body() or {}
        if d.get("remover"):
            for chave in ("google_client_id", "google_client_secret"):
                srv.config_set(conn, chave, "")
            conn.commit()
            return _resp(h, 200, {"ok": True})
        if "client_id" in d:
            cid = str(d.get("client_id") or "").strip()
            if cid and not re.match(r"^[A-Za-z0-9._-]+\.apps\.googleusercontent\.com$", cid):
                return _resp(h, 400, {"erro": "ID do cliente OAuth inválido (termina em .apps.googleusercontent.com)"})
            srv.config_set(conn, "google_client_id", cid)
        if d.get("client_secret"):
            srv.config_set(conn, "google_client_secret", str(d["client_secret"]).strip()[:200])
        conn.commit()
        with _trava:
            _tokens.clear()
        return _resp(h, 200, {"ok": True})
    return _resp(h, 405, {"erro": "Método não permitido"})
