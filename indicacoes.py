"""Link de indicação: cada pessoa da equipe (normalmente quem já foi contratado)
ganha um link pessoal. Quem se candidata por ele fica marcado como "indicado por",
e o painel mostra as indicações, quem foi contratado e quando vence o bônus.

O bônus é configurável por empresa (valor e dias depois da contratação). A data de
contratação é a da candidatura que chegou à etapa "contratado".
"""
import json
import re
import secrets
from datetime import datetime, timedelta

srv = None  # módulo server, injetado por ligar()

PADRAO = {"ativo": False, "valor_bonus": "", "dias_bonus": 30, "texto": ""}


def ligar(modulo_server):
    global srv
    srv = modulo_server


def init_indicacoes(c):
    c.execute(
        "CREATE TABLE IF NOT EXISTS indicadores ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " candidato_id INTEGER NOT NULL,"
        " codigo TEXT UNIQUE NOT NULL,"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " UNIQUE(empresa_id, candidato_id))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS indicacoes ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " indicador_id INTEGER NOT NULL,"
        " indicado_id INTEGER NOT NULL UNIQUE,"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " bonus_pago_em TEXT DEFAULT '',"
        " bonus_pago_por TEXT DEFAULT '')"
    )


def _chave(empresa_id):
    return "indicacoes:%d" % int(empresa_id)


def config(conn, empresa_id):
    cfg = dict(PADRAO)
    try:
        cfg.update(json.loads(srv.config_get(conn, _chave(empresa_id)) or "{}"))
    except ValueError:
        pass
    return cfg


def codigo_de(conn, empresa_id, candidato_id, criar=True):
    r = conn.execute("SELECT codigo FROM indicadores WHERE empresa_id=? AND candidato_id=?",
                     (empresa_id, candidato_id)).fetchone()
    if r or not criar:
        return r["codigo"] if r else ""
    for _ in range(5):
        codigo = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8].lower()
        try:
            conn.execute("INSERT INTO indicadores (empresa_id, candidato_id, codigo) VALUES (?,?,?)",
                         (empresa_id, candidato_id, codigo))
            conn.commit()
            return codigo
        except Exception:  # noqa: BLE001  (código repetido: tenta outro)
            continue
    return ""


def link(conn, empresa_id, codigo):
    emp = conn.execute("SELECT slug FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    return "%s/vagas?e=%s&ref=%s" % (srv.url_publica(conn), emp["slug"] if emp else "", codigo)


def registrar_cadastro(conn, candidato_id, empresa_id, codigo):
    """Chamado no cadastro público: liga o novo candidato a quem indicou (mesma empresa)."""
    codigo = re.sub(r"[^a-z0-9]", "", (codigo or "").lower())[:16]
    if not codigo:
        return
    ind = conn.execute("SELECT id, candidato_id FROM indicadores WHERE codigo=? AND empresa_id=?",
                       (codigo, empresa_id)).fetchone()
    if not ind or ind["candidato_id"] == candidato_id:
        return
    try:
        conn.execute("INSERT INTO indicacoes (empresa_id, indicador_id, indicado_id) VALUES (?,?,?)",
                     (empresa_id, ind["id"], candidato_id))
    except Exception:  # noqa: BLE001  (já registrado)
        return
    quem = conn.execute("SELECT nome FROM candidatos WHERE id=?", (ind["candidato_id"],)).fetchone()
    srv.registrar_evento(conn, candidato_id, "candidatura", "Indicado por %s" % (quem["nome"] if quem else "?"))
    srv.registrar_evento(conn, ind["candidato_id"], "sistema", "Indicou um candidato (#%d)" % candidato_id)


def _contratado_em(conn, candidato_id):
    r = conn.execute("SELECT MIN(atualizado_em) AS d FROM candidaturas WHERE candidato_id=? AND etapa='contratado'",
                     (candidato_id,)).fetchone()
    return (r["d"] or "")[:10] if r else ""


def _linha(conn, r, cfg):
    contratado = _contratado_em(conn, r["indicado_id"])
    vence = ""
    if contratado:
        vence = (datetime.strptime(contratado, "%Y-%m-%d") + timedelta(days=int(cfg.get("dias_bonus") or 0))).strftime("%Y-%m-%d")
    hoje = datetime.utcnow().strftime("%Y-%m-%d")
    if r["bonus_pago_em"]:
        situacao = "pago"
    elif contratado and vence <= hoje:
        situacao = "devido"
    elif contratado:
        situacao = "contratado"
    else:
        situacao = "inscrito"
    return {"id": r["id"], "indicador_id": r["indicador_candidato_id"], "indicador": r["indicador_nome"],
            "indicado_id": r["indicado_id"], "indicado": r["indicado_nome"], "criado_em": r["criado_em"],
            "contratado_em": contratado, "bonus_vence_em": vence, "bonus_pago_em": r["bonus_pago_em"],
            "situacao": situacao}


_SQL = (
    "SELECT i.*, d.candidato_id AS indicador_candidato_id, ci.nome AS indicador_nome, cd.nome AS indicado_nome,"
    " cd.local AS indicado_local, cd.empresa_id AS indicado_empresa"
    " FROM indicacoes i JOIN indicadores d ON d.id=i.indicador_id"
    " JOIN candidatos ci ON ci.id=d.candidato_id JOIN candidatos cd ON cd.id=i.indicado_id"
)


def listar(conn, gestor):
    cfg = config(conn, gestor["empresa_id"])
    linhas = conn.execute(_SQL + " WHERE i.empresa_id=? ORDER BY i.id DESC LIMIT 500", (gestor["empresa_id"],)).fetchall()
    return [_linha(conn, r, cfg) for r in linhas
            if srv.gestor_ve_candidato(gestor, {"local": r["indicado_local"], "empresa_id": r["indicado_empresa"]})]


def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/indicacoes"):
        return None
    empresa_id = gestor["empresa_id"]

    if method == "GET" and path == "/api/gestor/indicacoes":
        return _resp(h, 200, {"config": config(conn, empresa_id), "indicacoes": listar(conn, gestor)})

    if method == "POST" and path == "/api/gestor/indicacoes/config":
        if not gestor["is_admin"]:
            return _resp(h, 403, {"erro": "Apenas o administrador da empresa configura as indicações"})
        d = h._body()
        cfg = config(conn, empresa_id)
        cfg["ativo"] = bool(d.get("ativo"))
        cfg["valor_bonus"] = str(d.get("valor_bonus") or "").strip()[:40]
        try:
            cfg["dias_bonus"] = max(0, min(365, int(d.get("dias_bonus") or 0)))
        except (TypeError, ValueError):
            return _resp(h, 400, {"erro": "Número de dias inválido"})
        cfg["texto"] = str(d.get("texto") or "").strip()[:500]
        srv.config_set(conn, _chave(empresa_id), json.dumps(cfg, ensure_ascii=False))
        conn.commit()
        return _resp(h, 200, {"ok": True, "config": cfg})

    m = re.match(r"^/api/gestor/indicacoes/candidato/(\d+)$", path)
    if m and method in ("GET", "POST"):
        cid = int(m.group(1))
        cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (cid,)).fetchone()
        if not cand or not srv.gestor_ve_candidato(gestor, cand):
            return _resp(h, 404, {"erro": "Candidato não encontrado"})
        codigo = codigo_de(conn, empresa_id, cid, criar=(method == "POST"))
        cfg = config(conn, empresa_id)
        feitas = [x for x in listar(conn, gestor) if x["indicador_id"] == cid]
        por = conn.execute(_SQL + " WHERE i.indicado_id=? AND i.empresa_id=?", (cid, empresa_id)).fetchone()
        return _resp(h, 200, {
            "codigo": codigo, "link": link(conn, empresa_id, codigo) if codigo else "",
            "indicacoes": feitas, "indicado_por": _linha(conn, por, cfg) if por else None, "config": cfg,
        })

    m = re.match(r"^/api/gestor/indicacoes/(\d+)/pago$", path)
    if m and method == "POST":
        if not gestor["is_admin"]:
            return _resp(h, 403, {"erro": "Apenas o administrador da empresa registra o pagamento do bônus"})
        r = conn.execute("SELECT * FROM indicacoes WHERE id=? AND empresa_id=?", (int(m.group(1)), empresa_id)).fetchone()
        if not r:
            return _resp(h, 404, {"erro": "Indicação não encontrada"})
        pago = bool(h._body().get("pago", True))
        conn.execute("UPDATE indicacoes SET bonus_pago_em=?, bonus_pago_por=? WHERE id=?",
                     (datetime.utcnow().strftime("%Y-%m-%d") if pago else "", gestor["nome"] if pago else "", r["id"]))
        conn.commit()
        return _resp(h, 200, {"ok": True})

    return _resp(h, 404, {"erro": "Rota não encontrada"})


def info_publica(conn, empresa_slug, codigo):
    """Para a página de vagas: nome de quem indicou (só o primeiro nome) e o texto da empresa."""
    emp = srv.empresas.por_slug(conn, empresa_slug)
    if not emp:
        return None
    codigo = re.sub(r"[^a-z0-9]", "", (codigo or "").lower())[:16]
    r = conn.execute("SELECT c.nome FROM indicadores d JOIN candidatos c ON c.id=d.candidato_id"
                     " WHERE d.codigo=? AND d.empresa_id=?", (codigo, emp["id"])).fetchone()
    if not r:
        return None
    return {"primeiro_nome": (r["nome"] or "").split(" ")[0]}


def rotear_publico(h, method, path, conn):
    if not (method == "GET" and path == "/api/indicacao"):
        return None
    from urllib.parse import parse_qs, urlparse
    qs = parse_qs(urlparse(h.path).query)
    info = info_publica(conn, qs.get("e", [""])[0], qs.get("ref", [""])[0])
    return _resp(h, 200 if info else 404, info or {"erro": "Indicação não encontrada"})


def _resp(h, status, dados):
    h._json(status, dados)
    return True
