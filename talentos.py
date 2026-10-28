"""Decidir mais rápido no banco de talentos (painel do gestor).

- Resumo da ligação na ficha do candidato: tier, pontos, resultado e três linhas
  montadas só a partir dos fatos da triagem por voz (sem IA): pontos fortes,
  alertas e próximo passo. O servidor devolve códigos; o painel traduz (pt, en, es).
- Dados de voz por candidato para os filtros e a comparação lado a lado.
- "Lembrar em": data de retorno com nota, por candidato e por empresa. No dia
  (ou depois) o candidato aparece em "Ligar hoje" no quadro do dia (entrada.py).

Tudo isolado por empresa com server.gestor_ve_candidato.
"""
import json
import re
from datetime import date

srv = None  # módulo server, injetado por ligar()

TIERS = ("STRONG", "GOOD", "REVIEW", "LOW")
STATUS_ENCERRADOS = ("numero_errado", "nao_interessado", "nao_ligar", "nao_qualificado")
CAMPOS_LISTA = ("city", "own_car", "license", "weekdays_available", "experience_level")
RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def ligar(modulo_server):
    global srv
    srv = modulo_server


def init_talentos(c):
    """Tabela dos lembretes (migração no arranque). Um lembrete por candidato na empresa."""
    c.execute(
        "CREATE TABLE IF NOT EXISTS lembretes_talentos ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,"
        " data TEXT NOT NULL,"
        " nota TEXT DEFAULT '',"
        " autor TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " UNIQUE (empresa_id, candidato_id))"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_lembretes_talentos_data ON lembretes_talentos(empresa_id, data)")


# ------------------------------------------------------------- dados da voz

def _json(texto):
    try:
        return json.loads(texto) if texto else None
    except ValueError:
        return None


def _candidatura_principal(linhas):
    """A candidatura que melhor representa a triagem: a mais recente com tier;
    sem tier, a mais recente com algum status de voz."""
    com_tier = [r for r in linhas if (r["voz_tier"] or "") in TIERS]
    if com_tier:
        return com_tier[0]
    com_status = [r for r in linhas if r["voz_status"] or r["voz_outcome"]]
    return com_status[0] if com_status else None


def _info(ca, fatos_chamada):
    """Pacote de voz de uma candidatura. fatos_chamada: fatos da ligação mais recente
    (vale mais que os do último resultado pontuado, que pode ser antigo)."""
    resultado = _json(ca["voz_resultado"]) or {}
    fatos = fatos_chamada or resultado.get("fatos") or {}
    status = ca["voz_status"] or ""
    tier = ca["voz_tier"] if (ca["voz_tier"] or "") in TIERS else ""
    return {
        "candidatura_id": ca["id"],
        "vaga": ca["vaga_titulo"] if "vaga_titulo" in ca.keys() else "",
        "etapa": ca["etapa"],
        "tier": tier,
        "score": ca["voz_score"] if tier else None,
        "outcome": ca["voz_outcome"] or "",
        "status": status,
        "encerrado": status in STATUS_ENCERRADOS,
        "faixa": resultado.get("faixa") or "",
        "motivos": resultado.get("motivos") or [],
        "fatos": fatos,
    }


def _fatos_recentes(conn, candidato_ids):
    """{candidato_id: fatos da ligação atendida mais recente}."""
    saida = {}
    if not candidato_ids:
        return saida
    marcas = ",".join("?" * len(candidato_ids))
    for r in conn.execute(
        "SELECT candidato_id, fatos FROM voz_chamadas WHERE fatos<>'' AND candidato_id IN (%s)"
        " ORDER BY id DESC" % marcas, list(candidato_ids)).fetchall():
        if r["candidato_id"] not in saida:
            f = _json(r["fatos"])
            if f:
                saida[r["candidato_id"]] = f
    return saida


def voz_do_candidato(conn, candidato_id):
    linhas = conn.execute(
        "SELECT ca.*, v.titulo AS vaga_titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
        " WHERE ca.candidato_id=? ORDER BY ca.atualizado_em DESC, ca.id DESC", (candidato_id,)).fetchall()
    ca = _candidatura_principal(linhas)
    if not ca:
        return None
    return _info(ca, _fatos_recentes(conn, [candidato_id]).get(candidato_id))


def testes_feitos(conn, cand):
    if "notificado_completo" in cand.keys() and cand["notificado_completo"]:
        return True
    tipos = {r["tipo"] for r in conn.execute(
        "SELECT tipo FROM resultados_teste WHERE candidato_id=?", (cand["id"],)).fetchall()}
    return {"disc", "base"} <= tipos


# ------------------------------------------------------------- resumo da ligação

def linhas_resumo(info, testes_ok=False, etapa_avancada=False, entrevista_marcada=False):
    """Três linhas determinísticas a partir dos fatos. Cada item é {"c": código, ...parâmetros}.
    Devolve {"fortes": [...], "alertas": [...], "proximo": {"c": ...}}."""
    fortes, alertas = [], []
    info = info or {}
    f = info.get("fatos") or {}
    motivos = info.get("motivos") or []
    tier = info.get("tier") or ""
    outcome = info.get("outcome") or ""
    falou = bool(f) and any(v is not None for k, v in f.items() if k not in ("outcome", "preferred_language"))

    dias = f.get("weekdays_available")
    if isinstance(dias, int):
        if dias >= 4:
            fortes.append({"c": "dias", "n": dias})
        else:
            alertas.append({"c": "poucos_dias", "n": dias})
    exp = f.get("experience_level")
    if exp == "two_plus_years":
        fortes.append({"c": "experiencia"})
    elif exp == "none":
        alertas.append({"c": "sem_experiencia"})
    faixa = info.get("faixa") or ""
    cidade = (f.get("city") or "").strip()
    if faixa in ("25mi", "40mi"):
        fortes.append({"c": "perto", "raio": 25 if faixa == "25mi" else 40, "cidade": cidade})
    elif faixa == "outside" or "outside_area" in motivos:
        alertas.append({"c": "fora_area", "cidade": cidade})
    if f.get("license") == "yes" and f.get("own_car") == "yes":
        fortes.append({"c": "carro_carteira"})
    if f.get("works_alone") == "yes":
        fortes.append({"c": "sozinho"})
    elif f.get("works_alone") in ("hesitant", "no"):
        alertas.append({"c": "sozinho_hesita"})
    prazo = f.get("start_timeframe")
    if prazo in ("within_1_week", "within_2_weeks"):
        fortes.append({"c": "inicio", "semanas": 1 if prazo == "within_1_week" else 2})

    if falou:
        for campo, codigo in (("license", "carteira"), ("own_car", "carro")):
            valor = f.get(campo)
            if valor == "no":
                alertas.append({"c": codigo + "_nao"})
            elif valor != "yes":
                alertas.append({"c": codigo + "_incerto"})
    if f.get("standards") == "hesitant_or_objects" or "standards_objection" in motivos:
        alertas.append({"c": "padroes"})
    if f.get("has_smartphone") is False or "no_smartphone" in motivos:
        alertas.append({"c": "sem_smartphone"})
    if "outcome_corrected" in motivos or outcome == "NOT_AVAILABLE":
        alertas.append({"c": "desligou"})
    faltando = [m.split(":", 1)[1] for m in motivos if m.startswith("missing:")]
    if faltando:
        alertas.append({"c": "faltam", "n": len(faltando), "itens": faltando})

    # próximo passo
    if entrevista_marcada:
        proximo = "entrevista_marcada"
    elif etapa_avancada:
        proximo = "acompanhar"
    elif info.get("encerrado"):
        proximo = "encerrado"
    elif tier in ("STRONG", "GOOD"):
        proximo = "agendar_entrevista" if testes_ok else "aguardar_testes"
    elif tier == "REVIEW":
        proximo = "ouvir_ligacao"
    elif tier == "LOW" or outcome == "NOT_QUALIFIED":
        proximo = "considerar_reprovar"
    elif info.get("status") in ("para_ligar", "ligando", "callback", ""):
        proximo = "aguardar_ligacao"
    else:
        proximo = "ouvir_ligacao"
    return {"fortes": fortes, "alertas": alertas, "proximo": {"c": proximo}}


def lembrete_do_candidato(conn, empresa_id, candidato_id):
    r = conn.execute("SELECT data, nota, autor, criado_em FROM lembretes_talentos WHERE empresa_id=? AND candidato_id=?",
                     (empresa_id, candidato_id)).fetchone()
    return dict(r) if r else None


def resumo(conn, gestor, cand):
    """Pacote do cartão "Resumo da ligação" (e o lembrete) para a ficha."""
    info = voz_do_candidato(conn, cand["id"])
    etapas = {r["etapa"] for r in conn.execute("SELECT etapa FROM candidaturas WHERE candidato_id=?", (cand["id"],))}
    marcada = False
    try:
        marcada = conn.execute("SELECT 1 FROM entrevistas_agenda WHERE candidato_id=? AND empresa_id=? AND status='marcada'",
                               (cand["id"], gestor["empresa_id"])).fetchone() is not None
    except Exception:  # noqa: BLE001  (agenda ausente)
        marcada = False
    tem_voz = bool(info and (info["tier"] or info["fatos"] or info["outcome"]))
    saida = {"candidato_id": cand["id"], "tem_voz": tem_voz,
             "lembrete": lembrete_do_candidato(conn, gestor["empresa_id"], cand["id"])}
    if tem_voz:
        testes_ok = testes_feitos(conn, cand)
        saida.update({
            "tier": info["tier"], "score": info["score"], "outcome": info["outcome"], "status": info["status"],
            "vaga": info["vaga"], "testes_ok": testes_ok,
            "linhas": linhas_resumo(info, testes_ok,
                                    bool(etapas & {"entrevista", "proposta", "contratado"}), marcada),
        })
    return saida


# ------------------------------------------------------------- lista (filtros e comparação)

def voz_da_lista(conn, gestor):
    """{candidato_id: campos mínimos de voz} dos candidatos visíveis ao gestor."""
    visiveis = {}
    for c in conn.execute("SELECT id, local, empresa_id FROM candidatos WHERE empresa_id=? AND anonimizado=0",
                          (gestor["empresa_id"],)).fetchall():
        if srv.gestor_ve_candidato(gestor, c):
            visiveis[c["id"]] = c
    por_cand = {}
    for r in conn.execute(
        "SELECT ca.*, v.titulo AS vaga_titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
        " JOIN candidatos c ON c.id=ca.candidato_id WHERE c.empresa_id=?"
        " ORDER BY ca.atualizado_em DESC, ca.id DESC", (gestor["empresa_id"],)).fetchall():
        if r["candidato_id"] in visiveis:
            por_cand.setdefault(r["candidato_id"], []).append(r)
    fatos = _fatos_recentes(conn, list(por_cand))
    lembretes = {r["candidato_id"]: {"data": r["data"], "nota": r["nota"]} for r in conn.execute(
        "SELECT candidato_id, data, nota FROM lembretes_talentos WHERE empresa_id=?", (gestor["empresa_id"],))}
    saida = {}
    for cid in visiveis:
        ca = _candidatura_principal(por_cand.get(cid, []))
        item = {"tier": "", "score": None, "outcome": "", "status": "", "encerrado": False}
        item.update({k: None for k in CAMPOS_LISTA})
        if ca:
            info = _info(ca, fatos.get(cid))
            item.update({k: info[k] for k in ("tier", "score", "outcome", "status", "encerrado")})
            item.update({k: info["fatos"].get(k) for k in CAMPOS_LISTA})
        if cid in lembretes:
            item["lembrete"] = lembretes[cid]
        saida[str(cid)] = item
    return saida


# ------------------------------------------------------------- lembretes

def lembretes_vencidos(conn, empresa_id, hoje_iso):
    """Lembretes com data até hoje (inclusive), com o nome e a vaga mais recente."""
    return conn.execute(
        "SELECT l.candidato_id, l.data, l.nota, c.nome, c.local, c.empresa_id,"
        " (SELECT v.titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id WHERE ca.candidato_id=c.id"
        "  ORDER BY ca.atualizado_em DESC LIMIT 1) AS vaga,"
        " (SELECT ca.id FROM candidaturas ca WHERE ca.candidato_id=c.id ORDER BY ca.atualizado_em DESC LIMIT 1) AS candidatura_id"
        " FROM lembretes_talentos l JOIN candidatos c ON c.id=l.candidato_id"
        " WHERE l.empresa_id=? AND c.empresa_id=? AND c.anonimizado=0 AND l.data<=? ORDER BY l.data, l.id",
        (empresa_id, empresa_id, hoje_iso)).fetchall()


def data_valida(texto):
    texto = (texto or "").strip()
    if not RE_DATA.match(texto):
        return None
    try:
        return date.fromisoformat(texto).isoformat()
    except ValueError:
        return None


def salvar_lembrete(conn, gestor, candidato_id, data_iso, nota):
    nota = (nota or "").strip()[:300]
    conn.execute(
        "INSERT INTO lembretes_talentos (empresa_id, candidato_id, data, nota, autor) VALUES (?,?,?,?,?)"
        " ON CONFLICT(empresa_id, candidato_id) DO UPDATE SET data=excluded.data, nota=excluded.nota,"
        " autor=excluded.autor, criado_em=datetime('now')",
        (gestor["empresa_id"], candidato_id, data_iso, nota, gestor["nome"]))
    srv.registrar_evento(conn, candidato_id, "lembrete",
                         "Lembrete para %s%s" % (data_iso, (": " + nota) if nota else ""), gestor["nome"])
    conn.commit()


def apagar_lembrete(conn, gestor, candidato_id):
    cur = conn.execute("DELETE FROM lembretes_talentos WHERE empresa_id=? AND candidato_id=?",
                       (gestor["empresa_id"], candidato_id))
    if cur.rowcount:
        srv.registrar_evento(conn, candidato_id, "lembrete", "Lembrete removido", gestor["nome"])
    conn.commit()


# ------------------------------------------------------------- rotas do gestor

def _candidato(conn, gestor, cid):
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (cid,)).fetchone()
    if not cand or not srv.gestor_ve_candidato(gestor, cand):
        return None
    return cand


def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/talentos/"):
        return None

    if method == "GET" and path == "/api/gestor/talentos/voz":
        return _resp(h, 200, {"candidatos": voz_da_lista(conn, gestor)})

    m = re.match(r"^/api/gestor/talentos/resumo/(\d+)$", path)
    if m and method == "GET":
        cand = _candidato(conn, gestor, int(m.group(1)))
        if not cand:
            return _resp(h, 404, {"erro": "Candidato não encontrado"})
        return _resp(h, 200, resumo(conn, gestor, cand))

    m = re.match(r"^/api/gestor/talentos/lembrete/(\d+)$", path)
    if m and method in ("POST", "DELETE"):
        cand = _candidato(conn, gestor, int(m.group(1)))
        if not cand:
            return _resp(h, 404, {"erro": "Candidato não encontrado"})
        if method == "DELETE":
            apagar_lembrete(conn, gestor, cand["id"])
            return _resp(h, 200, {"ok": True, "lembrete": None})
        d = h._body() or {}
        data_iso = data_valida(str(d.get("data") or ""))
        if not data_iso:
            return _resp(h, 400, {"erro": "Data do lembrete inválida (use AAAA-MM-DD)"})
        salvar_lembrete(conn, gestor, cand["id"], data_iso, str(d.get("nota") or ""))
        return _resp(h, 200, {"ok": True, "lembrete": lembrete_do_candidato(conn, gestor["empresa_id"], cand["id"])})

    return _resp(h, 404, {"erro": "Rota não encontrada"})


def _resp(h, status, dados):
    h._json(status, dados)
    return True
