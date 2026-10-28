"""Domínios próprios por empresa para as páginas de vagas (ex.: jobs.cliente.com).

Fluxo:
1. O administrador da empresa cadastra o domínio no painel (Configurações).
2. O painel mostra os registros DNS: CNAME para o endereço da plataforma (ou registro A
   para o IP do servidor) e um TXT em _bussola.<domínio> com o código de posse.
3. "Verificar": o domínio precisa resolver (socket.getaddrinfo) para o mesmo IP da
   plataforma e o TXT precisa conter o código (consulta DNS over HTTPS em
   https://dns.google/resolve, pois a stdlib não lê TXT).
4. Só domínios verificados de empresas ativas (ou em teste) entram no mapeamento de Host
   e na resposta de GET /api/dominios/permitido, usada pelo Caddy (on_demand_tls "ask")
   para decidir se emite certificado.

Rotas:
- GET  /api/dominio                       público: {slug, nome, dominio} da empresa do Host
                                          (ou {slug: null}); usado por vagas.html e candidato.js.
- GET  /api/dominios/permitido?domain=X   público (Caddy): 200 só para domínio verificado.
- GET  /api/gestor/dominios               lista, instruções DNS e limite do plano (admin).
- POST /api/gestor/dominios               {dominio} cadastra (admin).
- POST /api/gestor/dominios/<id>/verificar verifica DNS e TXT (admin).
- DELETE /api/gestor/dominios/<id>        remove (admin).

Mapeamento de Host (rotear_host, chamado no início do do_GET):
- "/"               página de vagas da empresa (vagas.html, que lê a empresa em /api/dominio);
- "/gestor", "/dono" redirecionam (302) para o endereço principal da plataforma;
- o resto (/vaga?id=, /candidato, estáticos, /api/...) segue o fluxo normal.

Limite: campo "dominios_max" do plano no catálogo (planos.py); sem o campo, 1 por empresa.
"""
import ipaddress
import json
import re
import secrets
import socket
import sys
import threading
import time
import urllib.parse
import urllib.request
from urllib.parse import urlparse, parse_qs

srv = None  # módulo server, injetado por ligar()

PLATAFORMA_PADRAO = "rh.tonybelleza.com"
PREFIXO_TXT = "_bussola"
PREFIXO_TOKEN = "bussola-verificacao="
DOH_URL = "https://dns.google/resolve"
DOH_TIMEOUT = 6
SUFIXOS_RESERVADOS = ("localhost", "local", "test", "example", "invalid", "internal", "lan", "home", "arpa")
REDIRECIONAR = ("/gestor", "/dono", "/gestor.html", "/dono.html")

# fotografia dos domínios verificados (Host -> empresa), relida a cada 30 s ou após mudanças
_CACHE_TTL = 30.0
_cache = {"expira": 0.0, "mapa": {}}
_cache_trava = threading.Lock()

# limite do "ask": domínios desconhecidos (que vão ao banco), janela de 60 s
_ASK_LIMITE = 300
_ask_hits = []
_ask_trava = threading.Lock()

# limite de verificações por empresa (cada uma faz consultas DNS externas)
_VERIF_LIMITE = 10
_VERIF_JANELA = 600
_verif_hits = {}
_verif_trava = threading.Lock()

_RE_ROTULO = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


def ligar(modulo_server):
    global srv
    srv = modulo_server


def init_dominios(c):
    c.execute(
        "CREATE TABLE IF NOT EXISTS dominios_empresa ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " dominio TEXT NOT NULL,"
        " token TEXT NOT NULL,"
        " verificado INTEGER DEFAULT 0,"
        " verificado_em TEXT DEFAULT '',"
        " ultima_verificacao TEXT DEFAULT '',"
        " ultimo_erro TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " UNIQUE (empresa_id, dominio))"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_dominios_dominio ON dominios_empresa (dominio, verificado)")
    limpar_cache()


def limpar_cache():
    with _cache_trava:
        _cache["expira"] = 0.0


# ------------------------------------------------------------ DNS (substituíveis nos testes)

def resolver_ips(host):
    """Conjunto de IPs (v4 e v6) para o host; vazio se não resolve."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError, OSError):
        return set()
    return {i[4][0] for i in infos if i and i[4]}


def consultar_txt(nome):
    """Lista de valores TXT de nome, via DNS over HTTPS (dns.google). Levanta OSError em falha de rede."""
    url = DOH_URL + "?" + urllib.parse.urlencode({"name": nome, "type": "TXT"})
    req = urllib.request.Request(url, headers={"Accept": "application/dns-json", "User-Agent": "Bussola/1.0"})
    with urllib.request.urlopen(req, timeout=DOH_TIMEOUT) as resp:
        dados = json.loads(resp.read().decode("utf-8") or "{}")
    valores = []
    for ans in dados.get("Answer") or []:
        if ans.get("type") != 16:
            continue
        bruto = str(ans.get("data") or "")
        partes = re.findall(r'"((?:[^"\\]|\\.)*)"', bruto)
        valores.append("".join(partes) if partes else bruto)
    return valores


# ------------------------------------------------------------ plataforma

def host_principal(conn):
    """Host do endereço público da plataforma (config url_publica) ou o padrão."""
    url = ""
    try:
        url = (srv.config_get(conn, "url_publica") or "").strip()
    except Exception:  # noqa: BLE001
        url = ""
    host = (urlparse(url).hostname or "") if url else ""
    return (host or PLATAFORMA_PADRAO).lower().rstrip(".")


def url_principal(conn):
    try:
        url = (srv.config_get(conn, "url_publica") or "").strip().rstrip("/")
    except Exception:  # noqa: BLE001
        url = ""
    return url or ("https://" + PLATAFORMA_PADRAO)


def ips_plataforma(conn):
    """IPs aceitos: config dominios_ip (lista separada por vírgula) mais os do host principal."""
    ips = set()
    try:
        extra = srv.config_get(conn, "dominios_ip") or ""
    except Exception:  # noqa: BLE001
        extra = ""
    for parte in extra.replace(";", ",").split(","):
        parte = parte.strip()
        if parte:
            ips.add(parte)
    ips |= resolver_ips(host_principal(conn))
    return ips


def ip_exibido(conn):
    """IP mostrado nas instruções do registro A (prefere IPv4)."""
    ips = sorted(ips_plataforma(conn), key=lambda i: (":" in i, i))
    return ips[0] if ips else ""


# ------------------------------------------------------------ validação

def normalizar(texto):
    """Domínio em minúsculas, sem esquema, caminho, porta ou ponto final; IDN em punycode."""
    t = (texto or "").strip().lower()
    if "://" in t:
        t = t.split("://", 1)[1]
    t = t.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if "@" in t:
        return ""
    if t.startswith("[") or t.count(":") > 1:
        return t  # IPv6: validar() recusa
    t = t.split(":", 1)[0].rstrip(".")
    try:
        t = t.encode("idna").decode("ascii") if t and not t.isascii() else t
    except UnicodeError:
        return ""
    return t


def _eh_ip(t):
    try:
        ipaddress.ip_address(t.strip("[]"))
        return True
    except ValueError:
        return False


def validar(conn, dominio):
    """Mensagem de erro (português) ou None. dominio já normalizado."""
    if not dominio or len(dominio) > 253 or _eh_ip(dominio):
        return "Domínio inválido"
    rotulos = dominio.split(".")
    if len(rotulos) < 2 or not all(_RE_ROTULO.match(r) for r in rotulos):
        return "Domínio inválido"
    if not re.match(r"^(xn--[a-z0-9-]+|[a-z]{2,63})$", rotulos[-1]):
        return "Domínio inválido"
    if rotulos[-1] in SUFIXOS_RESERVADOS:
        return "Domínio inválido"
    principal = host_principal(conn)
    pai = ".".join(principal.split(".")[-2:]) if principal.count(".") >= 1 else principal
    for reservado in {principal, pai, PLATAFORMA_PADRAO, "tonybelleza.com"}:
        if dominio == reservado or dominio.endswith("." + reservado):
            return "Este domínio pertence à plataforma"
    return None


def token_novo():
    return PREFIXO_TOKEN + secrets.token_hex(16)


def limite_da_empresa(conn, empresa_id):
    """Máximo de domínios: dominios_max do plano no catálogo; None = sem limite; padrão 1."""
    try:
        e = conn.execute("SELECT plano FROM empresas WHERE id=?", (empresa_id,)).fetchone()
        codigo = (e["plano"] if e else "") or ""
        p = srv.planos.plano(conn, codigo) if codigo else None
    except Exception:  # noqa: BLE001
        p = None
    if isinstance(p, dict) and "dominios_max" in p:
        v = p.get("dominios_max")
        if v is None:
            return None
        try:
            return max(0, int(v))
        except (TypeError, ValueError):
            return 1
    return 1


# ------------------------------------------------------------ consultas

def _linha(r):
    return {"id": r["id"], "dominio": r["dominio"], "token": r["token"],
            "verificado": bool(r["verificado"]), "verificado_em": r["verificado_em"] or "",
            "ultima_verificacao": r["ultima_verificacao"] or "", "ultimo_erro": r["ultimo_erro"] or ""}


def listar(conn, empresa_id):
    return [_linha(r) for r in conn.execute(
        "SELECT * FROM dominios_empresa WHERE empresa_id=? ORDER BY id", (empresa_id,)).fetchall()]


def _mapa_verificados(conn):
    """{dominio: {dominio, empresa_id, slug, nome}} dos domínios verificados de empresas
    ativas ou em teste. Uma consulta a cada 30 s (ou após mudanças), nunca por pedido."""
    agora = time.time()
    with _cache_trava:
        if _cache["expira"] > agora:
            return _cache["mapa"]
    fechar = conn is None
    if fechar:
        conn = srv.db()
    try:
        linhas = conn.execute(
            "SELECT d.dominio, e.id AS empresa_id, e.slug, e.nome FROM dominios_empresa d"
            " JOIN empresas e ON e.id=d.empresa_id"
            " WHERE d.verificado=1 AND e.status IN ('ativa','teste') ORDER BY d.id").fetchall()
    finally:
        if fechar:
            conn.close()
    mapa = {}
    for r in linhas:
        mapa.setdefault(r["dominio"], {"dominio": r["dominio"], "empresa_id": r["empresa_id"],
                                       "slug": r["slug"], "nome": r["nome"]})
    with _cache_trava:
        _cache["mapa"] = mapa
        _cache["expira"] = agora + _CACHE_TTL
    return mapa


def empresa_do_dominio(conn, dominio):
    """Empresa dona do domínio verificado (dict) ou None."""
    dominio = normalizar(dominio)
    if not dominio:
        return None
    return _mapa_verificados(conn).get(dominio)


def _host_do_pedido(handler):
    host = (handler.headers.get("Host") or "").strip().lower() if getattr(handler, "headers", None) else ""
    if host.startswith("["):
        return ""
    return host.split(":", 1)[0].rstrip(".")


def _host_ignorado(host):
    return (not host or host in ("localhost", PLATAFORMA_PADRAO) or _eh_ip(host)
            or host.endswith(".localhost") or "." not in host)


def empresa_do_pedido(handler, conn=None):
    """Empresa do Host do pedido quando é um domínio próprio verificado; senão None."""
    host = _host_do_pedido(handler)
    if _host_ignorado(host):
        return None
    if conn is not None and host == host_principal(conn):
        return None
    return empresa_do_dominio(conn, host)


def dominio_da_empresa(conn, empresa_id):
    """Primeiro domínio verificado da empresa (ou None)."""
    r = conn.execute("SELECT dominio FROM dominios_empresa WHERE empresa_id=? AND verificado=1 ORDER BY id LIMIT 1",
                     (empresa_id,)).fetchone()
    return r["dominio"] if r else None


def base_da_empresa(conn, empresa_id):
    """https://<domínio próprio> da empresa, ou None quando não há domínio verificado."""
    d = dominio_da_empresa(conn, empresa_id)
    return ("https://" + d) if d else None


def empresas_com_dominio(conn):
    """{empresa_id: dominio} de todas as empresas com domínio verificado."""
    saida = {}
    for r in conn.execute("SELECT empresa_id, dominio FROM dominios_empresa WHERE verificado=1 ORDER BY id").fetchall():
        saida.setdefault(r["empresa_id"], r["dominio"])
    return saida


# ------------------------------------------------------------ ações

def adicionar(conn, empresa_id, texto):
    """(linha, None) ou (None, erro)."""
    dominio = normalizar(texto)
    erro = validar(conn, dominio)
    if erro:
        return None, erro
    if conn.execute("SELECT 1 FROM dominios_empresa WHERE empresa_id=? AND dominio=?",
                    (empresa_id, dominio)).fetchone():
        return None, "Este domínio já foi cadastrado"
    if conn.execute("SELECT 1 FROM dominios_empresa WHERE dominio=? AND verificado=1 AND empresa_id!=?",
                    (dominio, empresa_id)).fetchone():
        return None, "Este domínio já está em uso por outra empresa"
    limite = limite_da_empresa(conn, empresa_id)
    total = conn.execute("SELECT COUNT(*) FROM dominios_empresa WHERE empresa_id=?", (empresa_id,)).fetchone()[0]
    if limite is not None and total >= limite:
        return None, "Seu plano permite até %d domínio(s) próprio(s)" % limite
    cur = conn.execute("INSERT INTO dominios_empresa (empresa_id, dominio, token) VALUES (?,?,?)",
                       (empresa_id, dominio, token_novo()))
    conn.commit()
    return _linha(conn.execute("SELECT * FROM dominios_empresa WHERE id=?", (cur.lastrowid,)).fetchone()), None


def remover(conn, empresa_id, dominio_id):
    cur = conn.execute("DELETE FROM dominios_empresa WHERE id=? AND empresa_id=?", (dominio_id, empresa_id))
    conn.commit()
    limpar_cache()
    return cur.rowcount > 0


def checar_dns(conn, dominio):
    """(ok, ips_do_dominio, ips_da_plataforma)."""
    ips_dom = resolver_ips(dominio)
    ips_plat = ips_plataforma(conn)
    return bool(ips_dom and ips_plat and (ips_dom & ips_plat)), sorted(ips_dom), sorted(ips_plat)


def checar_txt(dominio, token):
    """(ok, valores_encontrados, erro_de_rede)."""
    try:
        valores = consultar_txt("%s.%s" % (PREFIXO_TXT, dominio))
    except Exception as exc:  # noqa: BLE001
        return False, [], str(exc)[:200] or "falha"
    return any(v.strip() == token for v in valores), valores[:10], ""


def verificar(conn, empresa_id, dominio_id):
    """Confere DNS e TXT. Devolve (resultado, None) ou (None, erro)."""
    r = conn.execute("SELECT * FROM dominios_empresa WHERE id=? AND empresa_id=?",
                     (dominio_id, empresa_id)).fetchone()
    if not r:
        return None, "Domínio não encontrado"
    dominio = r["dominio"]
    dns_ok, ips_dom, ips_plat = checar_dns(conn, dominio)
    txt_ok, txt_vals, txt_erro = checar_txt(dominio, r["token"])
    conflito = conn.execute("SELECT 1 FROM dominios_empresa WHERE dominio=? AND verificado=1 AND empresa_id!=?",
                            (dominio, empresa_id)).fetchone()
    ok = dns_ok and txt_ok and not conflito
    if conflito:
        erro = "em_uso"
    elif not dns_ok:
        erro = "dns"
    elif not txt_ok:
        erro = "txt_rede" if txt_erro else "txt"
    else:
        erro = ""
    if ok:
        conn.execute("UPDATE dominios_empresa SET verificado=1, verificado_em=CASE WHEN verificado=1"
                     " AND verificado_em!='' THEN verificado_em ELSE datetime('now') END,"
                     " ultima_verificacao=datetime('now'), ultimo_erro='' WHERE id=?", (dominio_id,))
        # pedidos pendentes do mesmo domínio em outras empresas deixam de valer
        conn.execute("DELETE FROM dominios_empresa WHERE dominio=? AND empresa_id!=? AND verificado=0",
                     (dominio, empresa_id))
    else:
        conn.execute("UPDATE dominios_empresa SET verificado=0, ultima_verificacao=datetime('now'),"
                     " ultimo_erro=? WHERE id=?", (erro, dominio_id))
    conn.commit()
    limpar_cache()
    return {"ok": ok, "dominio": dominio, "erro": erro,
            "dns": {"ok": dns_ok, "ips": ips_dom, "esperado": ips_plat},
            "txt": {"ok": txt_ok, "nome": "%s.%s" % (PREFIXO_TXT, dominio), "encontrados": txt_vals,
                    "erro_rede": bool(txt_erro)},
            "item": _linha(conn.execute("SELECT * FROM dominios_empresa WHERE id=?", (dominio_id,)).fetchone())}, None


def instrucoes(conn, item):
    """Registros DNS que o cliente precisa criar."""
    d = item["dominio"]
    return {
        "cname": {"tipo": "CNAME", "nome": d, "valor": host_principal(conn)},
        "a": {"tipo": "A", "nome": d, "valor": ip_exibido(conn)},
        "txt": {"tipo": "TXT", "nome": "%s.%s" % (PREFIXO_TXT, d), "valor": item["token"]},
        "apex": d.count(".") == 1,
    }


# ------------------------------------------------------------ respostas e rotas

def _responder_texto(handler, status, texto, extra=None):
    corpo = texto.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Content-Length", str(len(corpo)))
    handler.send_header("Cache-Control", "no-store")
    for k, v in (extra or {}).items():
        handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(corpo)


def _ask_permitido_agora():
    agora = time.time()
    with _ask_trava:
        while _ask_hits and agora - _ask_hits[0] > 60:
            _ask_hits.pop(0)
        if len(_ask_hits) >= _ASK_LIMITE:
            return False
        _ask_hits.append(agora)
        return True


def permitido(conn, dominio):
    """True se o Caddy pode emitir certificado para o domínio. Domínios verificados são
    sempre aceitos; os demais contam para o limite por minuto (OverflowError quando passa)."""
    if empresa_do_dominio(conn, dominio):
        return True
    if not _ask_permitido_agora():
        raise OverflowError("limite")
    return False


def rotear_host(handler, path):
    """Chamado no início do do_GET. Responde e devolve True quando o Host é um domínio
    próprio e o caminho é "/" (página de vagas) ou do painel (redireciona)."""
    if path != "/" and path not in REDIRECIONAR:
        return False
    host = _host_do_pedido(handler)
    if _host_ignorado(host):
        return False
    conn = srv.db()
    try:
        if host == host_principal(conn):
            return False
        emp = empresa_do_dominio(conn, host)
        if not emp:
            return False
        if path in REDIRECIONAR:
            query = urlparse(handler.path).query
            destino = url_principal(conn) + path.replace(".html", "") + ("?" + query if query else "")
            handler.send_response(302)
            handler.send_header("Location", destino)
            handler.send_header("Content-Length", "0")
            handler.send_header("Cache-Control", "no-store")
            handler.end_headers()
            return True
    finally:
        conn.close()
    handler.static("/vagas")  # "/" do domínio próprio = página de vagas da empresa
    return True


def rotear_publico(h, method, path, conn):
    if method == "GET" and path == "/api/dominio":
        emp = empresa_do_pedido(h, conn)
        h._json(200, {"slug": emp["slug"], "nome": emp["nome"], "dominio": emp["dominio"]} if emp
                else {"slug": None})
        return True
    if method == "GET" and path == "/api/dominios/permitido":
        qs = parse_qs(urlparse(h.path).query)
        dominio = (qs.get("domain") or qs.get("dominio") or [""])[0]
        try:
            ok = permitido(conn, dominio)
        except OverflowError:
            _responder_texto(h, 429, "too many requests", {"Retry-After": "60"})
            return True
        _responder_texto(h, 200 if ok else 404, "ok" if ok else "not allowed")
        return True
    return False


def _pode_verificar(empresa_id):
    agora = time.time()
    with _verif_trava:
        recentes = [t for t in _verif_hits.get(empresa_id, []) if agora - t < _VERIF_JANELA]
        if len(recentes) >= _VERIF_LIMITE:
            _verif_hits[empresa_id] = recentes
            return False
        recentes.append(agora)
        _verif_hits[empresa_id] = recentes
        return True


def _estado(conn, empresa_id):
    itens = listar(conn, empresa_id)
    for it in itens:
        it["instrucoes"] = instrucoes(conn, it)
    limite = limite_da_empresa(conn, empresa_id)
    return {"dominios": itens, "limite": limite,
            "pode_adicionar": limite is None or len(itens) < limite,
            "plataforma": host_principal(conn), "ip": ip_exibido(conn)}


def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/dominios"):
        return False
    if not gestor["is_admin"]:
        h._json(403, {"erro": "Apenas o administrador da empresa gerencia o domínio próprio"})
        return True
    eid = gestor["empresa_id"]
    if path == "/api/gestor/dominios" and method == "GET":
        h._json(200, _estado(conn, eid))
        return True
    if path == "/api/gestor/dominios" and method == "POST":
        item, erro = adicionar(conn, eid, (h._body() or {}).get("dominio"))
        if erro:
            h._json(400, {"erro": erro})
        else:
            _auditar(h, conn, gestor, "dominio_adicionado", item["dominio"])
            h._json(200, dict(_estado(conn, eid), item=item))
        return True
    m = re.match(r"^/api/gestor/dominios/(\d+)/verificar$", path)
    if m and method == "POST":
        if not _pode_verificar(eid):
            h._json(429, {"erro": "Muitas verificações. Aguarde alguns minutos."})
            return True
        res, erro = verificar(conn, eid, int(m.group(1)))
        if erro:
            h._json(404, {"erro": erro})
        else:
            if res["ok"]:
                _auditar(h, conn, gestor, "dominio_verificado", res["dominio"])
            h._json(200, dict(_estado(conn, eid), resultado=res))
        return True
    m = re.match(r"^/api/gestor/dominios/(\d+)$", path)
    if m and method == "DELETE":
        if not remover(conn, eid, int(m.group(1))):
            h._json(404, {"erro": "Domínio não encontrado"})
        else:
            _auditar(h, conn, gestor, "dominio_removido", m.group(1))
            h._json(200, _estado(conn, eid))
        return True
    h._json(404, {"erro": "Rota não encontrada"})
    return True


def _auditar(h, conn, gestor, acao, alvo):
    try:
        srv.seguranca.registrar(conn, acao, gestor=gestor, alvo=alvo, ip=h._ip_cliente())
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("dominios: auditoria falhou %r\n" % exc)
