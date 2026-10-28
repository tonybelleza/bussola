"""Segurança do Bússola: robôs que vasculham o servidor, cabeçalhos de segurança
e trilha de auditoria (quem viu ou alterou o quê, por empresa).

Os robôs procuram arquivos de outros sistemas (.env, phpinfo, wp-admin, cgi-bin).
Esses pedidos recebem 404 na hora, sem tocar no disco nem no banco; quem insiste
(muitos pedidos suspeitos em pouco tempo) fica bloqueado por uma hora.
"""
import re
import threading
import time

srv = None  # módulo server, injetado por ligar()

PADRAO_ROBO = re.compile(
    r"(\.php\b|\.asp|\.env\b|\.git/|\.svn|\.aws|\.ds_store|/wp-|wordpress|phpmyadmin|/cgi-bin|"
    r"/shell\b|gponform|/sdk/|/actuator|/vendor/|/boaform|/hnap1|/\.well-known/(?!acme)|"
    r"/config\.json|/server-status|/owa/|/autodiscover|/solr/|/druid/|\$\{|%24%7b|/etc/passwd)",
    re.I,
)
JANELA_ROBO = 600        # 10 minutos
LIMITE_ROBO = 6          # pedidos suspeitos na janela até bloquear
BLOQUEIO_SEGUNDOS = 3600

_suspeitos = {}   # ip -> [instantes]
_bloqueados = {}  # ip -> até quando
_trava = threading.Lock()

CABECALHOS = (
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    # o microfone fica liberado só para o próprio site (simulação da Francisca)
    ("Permissions-Policy", "microphone=(self), camera=(), geolocation=(), payment=()"),
    ("Strict-Transport-Security", "max-age=31536000"),
    ("Cross-Origin-Opener-Policy", "same-origin"),
)


def ligar(modulo_server):
    global srv
    srv = modulo_server


def init_seguranca(c):
    c.execute(
        "CREATE TABLE IF NOT EXISTS auditoria ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER,"
        " gestor_id INTEGER,"
        " quem TEXT DEFAULT '',"
        " acao TEXT NOT NULL,"
        " alvo TEXT DEFAULT '',"
        " ip TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')))"
    )
    c.execute("CREATE INDEX IF NOT EXISTS ix_auditoria_empresa ON auditoria(empresa_id, id)")


# ------------------------------------------------------------- robôs

def bloqueado(ip):
    with _trava:
        ate = _bloqueados.get(ip)
        if ate and ate > time.time():
            return True
        if ate:
            _bloqueados.pop(ip, None)
        return False


def pedido_suspeito(ip, caminho):
    """True se o caminho é de varredura; conta para o bloqueio do IP."""
    if not PADRAO_ROBO.search(caminho or ""):
        return False
    agora = time.time()
    with _trava:
        recentes = [t for t in _suspeitos.get(ip, []) if agora - t < JANELA_ROBO] + [agora]
        _suspeitos[ip] = recentes
        if len(recentes) >= LIMITE_ROBO:
            _bloqueados[ip] = agora + BLOQUEIO_SEGUNDOS
            _suspeitos.pop(ip, None)
        # limpeza ocasional para a memória não crescer
        if len(_suspeitos) > 5000:
            for k in [k for k, v in _suspeitos.items() if agora - v[-1] > JANELA_ROBO]:
                _suspeitos.pop(k, None)
    return True


def filtrar(handler, caminho):
    """Chamado no início de cada pedido. Responde e devolve True quando o pedido
    não deve seguir (IP bloqueado ou varredura)."""
    ip = handler._ip_cliente()
    if bloqueado(ip):
        _responder(handler, 403)
        return True
    if pedido_suspeito(ip, caminho):
        _responder(handler, 404)
        return True
    return False


def _responder(handler, status):
    corpo = b"{}"
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(corpo)))
    handler.send_header("Connection", "close")
    handler.end_headers()
    handler.wfile.write(corpo)
    handler.close_connection = True


def cabecalhos(handler):
    for nome, valor in CABECALHOS:
        handler.send_header(nome, valor)


# ------------------------------------------------------------- auditoria

ACOES_LEITURA = (
    (re.compile(r"^/api/gestor/candidato/(\d+)$"), "ver_candidato"),
    (re.compile(r"^/api/gestor/candidato/(\d+)/curriculo$"), "baixar_curriculo"),
    (re.compile(r"^/api/gestor/candidato/(\d+)/relatorio\.pdf$"), "baixar_relatorio"),
    (re.compile(r"^/api/gestor/voz/chamada/(\d+)/audio$"), "ouvir_ligacao"),
)


def registrar(conn, acao, gestor=None, alvo="", ip="", empresa_id=None, quem=""):
    try:
        conn.execute(
            "INSERT INTO auditoria (empresa_id, gestor_id, quem, acao, alvo, ip) VALUES (?,?,?,?,?,?)",
            (empresa_id if empresa_id is not None else (gestor["empresa_id"] if gestor else None),
             gestor["id"] if gestor else None, quem or (gestor["nome"] if gestor else ""),
             acao[:80], str(alvo)[:200], ip[:60]),
        )
        conn.commit()
    except Exception:  # noqa: BLE001
        pass


def auditar_pedido(handler, conn, gestor, method, caminho):
    """Registra alterações (POST/DELETE) e leituras sensíveis feitas por um gestor."""
    if not gestor:
        return
    ip = handler._ip_cliente()
    if method in ("POST", "DELETE"):
        if caminho in ("/api/gestor/idioma",):
            return
        registrar(conn, method.lower() + " " + caminho.replace("/api/gestor/", ""), gestor, "", ip)
        return
    for padrao, acao in ACOES_LEITURA:
        m = padrao.match(caminho)
        if m:
            registrar(conn, acao, gestor, m.group(1), ip)
            return


def listar(conn, empresa_id, limite=200, antes_de=None):
    sql = "SELECT id, quem, acao, alvo, ip, criado_em FROM auditoria WHERE empresa_id=?"
    params = [empresa_id]
    if antes_de:
        sql += " AND id < ?"
        params.append(int(antes_de))
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(max(1, min(500, int(limite))))
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def rotear_dono(h, method, path, conn):
    """Histórico de acessos de qualquer empresa (painel do dono)."""
    if not (method == "GET" and path == "/api/dono/auditoria"):
        return None
    from urllib.parse import parse_qs, urlparse
    qs = parse_qs(urlparse(h.path).query)
    try:
        empresa_id = int(qs.get("empresa_id", ["0"])[0])
    except ValueError:
        empresa_id = 0
    h._json(200, {"registros": listar(conn, empresa_id, qs.get("limite", ["200"])[0], qs.get("antes", [None])[0])})
    return True


def rotear_gestor(h, method, path, conn, gestor):
    if path != "/api/gestor/auditoria":
        return None
    if not gestor["is_admin"]:
        h._json(403, {"erro": "Apenas o administrador da empresa vê o histórico de acessos"})
        return True
    from urllib.parse import parse_qs, urlparse
    qs = parse_qs(urlparse(h.path).query)
    h._json(200, {"registros": listar(conn, gestor["empresa_id"], qs.get("limite", ["200"])[0],
                                      qs.get("antes", [None])[0])})
    return True
