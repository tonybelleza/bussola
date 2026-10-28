"""Relatório de contratação para gestores (painel do gestor, aba Relatórios).

GET /api/gestor/relatorios/contratacao?de=AAAA-MM-DD&ate=AAAA-MM-DD&vaga_id=&cargo_id=

- Coorte: candidaturas criadas no período (data da inscrição, UTC), da empresa do
  gestor e de candidatos que ele enxerga (server.gestor_ve_candidato).
- Funil por etapa alcançada: inscritos, triados por voz (atendeu), qualificados
  (STRONG ou GOOD), testes concluídos, entrevista marcada, entrevista realizada,
  proposta, contratados; reprovados à parte. Conversão entre etapas vizinhas.
- Origem (tags: indeed, facebook, notion, csv; indicação pelo indicacoes.py; site
  quando nenhuma), tempos (inscrição até contratação, até a primeira ligação e da
  ligação até a entrevista), custo da voz (minutos x premissas do planos.py),
  tabelas por vaga e por cargo, tendência semanal e motivos de encerramento.

O servidor devolve só números e códigos; o painel traduz (pt, en, es).
Sem dependências externas.
"""
import json
import math
import re
from datetime import datetime, timedelta

srv = None  # módulo server, injetado por ligar()

CUSTO_MIN_VOZ_PADRAO = 0.09
CUSTO_MIN_TEL_PADRAO = 0.014
MAX_DIAS = 731
RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")

ORDEM_ETAPAS = {"inscrito": 0, "avaliacoes": 1, "entrevista": 2, "proposta": 3, "contratado": 4}
ETAPAS_FUNIL = ("inscritos", "triados", "qualificados", "testes", "entrevista_marcada",
                "entrevista_realizada", "proposta", "contratados")
FLAG_ETAPA = {"inscritos": None, "triados": "triado", "qualificados": "qualificado", "testes": "testes",
              "entrevista_marcada": "marcada", "entrevista_realizada": "realizada", "proposta": "proposta",
              "contratados": "contratado"}
FONTES = ("indeed", "facebook", "notion", "csv", "indicacao", "site")
TAGS_INDICACAO = ("indicacao", "indicação", "referral", "indicado")
TIERS_QUALIFICADOS = ("STRONG", "GOOD")
ENCERRAMENTOS = ("numero_errado", "sem_interesse", "nao_ligar", "nao_qualificado",
                 "sem_resposta", "reprovacao_manual")
OUTCOME_ENCERRAMENTO = {"WRONG_NUMBER": "numero_errado", "NOT_INTERESTED": "sem_interesse",
                        "DO_NOT_CALL": "nao_ligar"}


def ligar(modulo_server):
    global srv
    srv = modulo_server


# ------------------------------------------------------------- utilidades

def ler_data(texto):
    """datetime (UTC, sem fuso) a partir de 'AAAA-MM-DD HH:MM:SS', ISO com T/Z ou só data."""
    s = str(texto or "").strip()
    if not s:
        return None
    s = s.replace("T", " ").rstrip("Zz")
    s = re.sub(r"[+-]\d{2}:?\d{2}$", "", s)[:19]
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, formato)
        except ValueError:
            continue
    return None


def data_valida(texto):
    if not RE_DATA.match(texto or ""):
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def mediana(valores):
    v = sorted(valores)
    if not v:
        return None
    meio = len(v) // 2
    return float(v[meio]) if len(v) % 2 else (v[meio - 1] + v[meio]) / 2.0


def media(valores):
    return sum(valores) / float(len(valores)) if valores else None


def pct(parte, todo):
    return round(100.0 * parte / todo, 1) if todo else None


def r1(v):
    return round(v, 1) if v is not None else None


def dinheiro(v):
    return round(v, 2) if v is not None else None


def resumo_tempos(valores):
    return {"n": len(valores), "mediana": r1(mediana(valores)), "media": r1(media(valores))}


def _tags(texto):
    try:
        t = json.loads(texto or "[]")
    except (TypeError, ValueError):
        return []
    return [str(x).strip().lower() for x in t] if isinstance(t, list) else []


def fonte_de(tags, indicado=False):
    """Origem do candidato: indicação primeiro, depois a primeira tag conhecida, senão site."""
    if indicado or any(t in TAGS_INDICACAO for t in tags):
        return "indicacao"
    for t in tags:
        if t in ("indeed", "facebook", "notion", "csv"):
            return t
    return "site"


def premissas_custo(conn):
    """Custo por minuto (voz + telefonia) das premissas do planos.py, com padrões."""
    voz, tel = CUSTO_MIN_VOZ_PADRAO, CUSTO_MIN_TEL_PADRAO
    planos = getattr(srv, "planos", None) if srv else None
    try:
        if planos is not None and hasattr(planos, "premissas"):
            p = planos.premissas(conn)
            voz = float(p.get("custo_min_voz", voz))
            tel = float(p.get("custo_min_tel", tel))
    except Exception:  # noqa: BLE001  (premissas ilegíveis: usa os padrões)
        voz, tel = CUSTO_MIN_VOZ_PADRAO, CUSTO_MIN_TEL_PADRAO
    return voz, tel


def minutos_cobrados(duracao):
    """Minutos iniciados (como no planos.py: ceil(duracao/60))."""
    d = _segundos(duracao)
    return int(math.ceil(d / 60.0)) if d > 0 else 0


def _segundos(duracao):
    try:
        return max(int(duracao or 0), 0)
    except (TypeError, ValueError):
        return 0


def _atendeu(chamada):
    """A pessoa falou na ligação (mesma regra do placar do voz.py)."""
    try:
        transcricao = json.loads(chamada["transcricao"] or "[]")
    except (TypeError, ValueError):
        transcricao = []
    return isinstance(transcricao, list) and any(
        isinstance(t, dict) and t.get("papel") == "user" for t in transcricao)


def segunda_de(d):
    return d - timedelta(days=d.weekday())


# ------------------------------------------------------------- etapas pelos eventos

def _nomes_etapas():
    nomes = getattr(srv, "NOMES_ETAPAS", None) or {
        "inscrito": "Inscrito", "avaliacoes": "Avaliações", "entrevista": "Entrevista",
        "proposta": "Proposta", "contratado": "Contratado", "reprovado": "Reprovado"}
    return sorted(nomes.items(), key=lambda kv: -len(kv[1]))


def etapas_dos_eventos(eventos, titulo_vaga):
    """{etapa: primeira data} a partir dos eventos 'etapa' ('Vaga X: movido para Y')."""
    prefixo = "Vaga %s: movido para " % (titulo_vaga or "")
    achadas = {}
    nomes = _nomes_etapas()
    for texto, quando in eventos:
        if not texto.startswith(prefixo):
            continue
        resto = texto[len(prefixo):]
        for etapa, nome in nomes:
            if resto.startswith(nome):
                dt = ler_data(quando)
                if etapa not in achadas or (dt and achadas[etapa] and dt < achadas[etapa]):
                    achadas[etapa] = dt
                break
    return achadas


# ------------------------------------------------------------- cálculo

def _validar_filtros(conn, gestor, consulta):
    """(de, ate, vaga_id, cargo_id, erro, status)."""
    hoje = datetime.utcnow().date()
    de_txt = (consulta.get("de") or [""])[0].strip()
    ate_txt = (consulta.get("ate") or [""])[0].strip()
    ate = data_valida(ate_txt) if ate_txt else hoje
    de = data_valida(de_txt) if de_txt else (ate - timedelta(days=29) if ate else None)
    if not de or not ate or de > ate or (ate - de).days > MAX_DIAS:
        return None, None, None, None, "Período inválido", 400
    ids = {}
    for chave in ("vaga_id", "cargo_id"):
        bruto = (consulta.get(chave) or [""])[0].strip()
        if not bruto:
            ids[chave] = None
            continue
        if not bruto.isdigit():
            return None, None, None, None, "Filtro inválido", 400
        ids[chave] = int(bruto)
    if ids["vaga_id"] and not conn.execute(
            "SELECT 1 FROM vagas WHERE id=? AND empresa_id=?", (ids["vaga_id"], gestor["empresa_id"])).fetchone():
        return None, None, None, None, "Vaga não encontrada", 404
    if ids["cargo_id"] and not conn.execute(
            "SELECT 1 FROM cargos WHERE id=? AND empresa_id=?", (ids["cargo_id"], gestor["empresa_id"])).fetchone():
        return None, None, None, None, "Cargo não encontrado", 404
    return de, ate, ids["vaga_id"], ids["cargo_id"], "", 200


def relatorio(conn, gestor, de, ate, vaga_id=None, cargo_id=None):
    """Monta o relatório de contratação. de/ate: date (inclusivos, UTC)."""
    empresa_id = gestor["empresa_id"]
    inicio = datetime(de.year, de.month, de.day)
    fim = datetime(ate.year, ate.month, ate.day) + timedelta(days=1)  # exclusivo

    filtro_sql, args = "", [empresa_id]
    if vaga_id:
        filtro_sql += " AND v.id=?"
        args.append(vaga_id)
    if cargo_id:
        filtro_sql += " AND v.cargo_id=?"
        args.append(cargo_id)
    linhas = conn.execute(
        "SELECT ca.*, v.titulo AS vaga_titulo, v.cargo_id AS vaga_cargo_id, v.status AS vaga_status,"
        " cg.nome AS cargo_nome, c.local AS cand_local, c.empresa_id AS cand_empresa,"
        " c.tags AS cand_tags, c.notificado_completo AS cand_completo"
        " FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
        " JOIN candidatos c ON c.id=ca.candidato_id"
        " LEFT JOIN cargos cg ON cg.id=v.cargo_id"
        " WHERE v.empresa_id=? AND c.empresa_id=v.empresa_id" + filtro_sql,
        args,
    ).fetchall()
    # isolamento: só candidatos visíveis para o gestor
    linhas = [r for r in linhas if srv.gestor_ve_candidato(
        gestor, {"empresa_id": r["cand_empresa"], "local": r["cand_local"]})]
    cand_ids = sorted({r["candidato_id"] for r in linhas})
    cands_ok = set(cand_ids)
    cand_ids_por_ca = {r["id"]: r["candidato_id"] for r in linhas}

    # dados auxiliares em lote (por empresa) e filtrados em memória
    eventos = {}
    for e in conn.execute(
            "SELECT e.candidato_id, e.texto, e.criado_em FROM eventos e JOIN candidatos c ON c.id=e.candidato_id"
            " WHERE c.empresa_id=? AND e.tipo='etapa' ORDER BY e.criado_em, e.id", (empresa_id,)):
        if e["candidato_id"] in cands_ok:
            eventos.setdefault(e["candidato_id"], []).append((e["texto"] or "", e["criado_em"]))

    chamadas = {}
    for ch in conn.execute(
            "SELECT vc.id, vc.candidatura_id, vc.candidato_id, vc.status, vc.iniciada_em, vc.duracao, vc.transcricao"
            " FROM voz_chamadas vc JOIN candidatos c ON c.id=vc.candidato_id WHERE c.empresa_id=?"
            " ORDER BY vc.iniciada_em, vc.id", (empresa_id,)):
        if ch["candidatura_id"] in cand_ids_por_ca:
            chamadas.setdefault(ch["candidatura_id"], []).append(ch)

    testes = {}
    for t in conn.execute(
            "SELECT rt.candidato_id, rt.tipo FROM resultados_teste rt JOIN candidatos c ON c.id=rt.candidato_id"
            " WHERE c.empresa_id=?", (empresa_id,)):
        testes.setdefault(t["candidato_id"], set()).add(t["tipo"])

    agenda_por_ca, agenda_por_cand = {}, {}
    try:
        for a in conn.execute(
                "SELECT candidato_id, candidatura_id, inicio_utc, status FROM entrevistas_agenda"
                " WHERE empresa_id=? AND status IN ('marcada','realizada','faltou') ORDER BY inicio_utc",
                (empresa_id,)):
            if a["candidato_id"] not in cands_ok:
                continue
            if a["candidatura_id"]:
                agenda_por_ca.setdefault(a["candidatura_id"], []).append(a)
            else:
                agenda_por_cand.setdefault(a["candidato_id"], []).append(a)
    except Exception:  # noqa: BLE001  (sem agenda.py: segue sem a agenda)
        pass

    notas_entrevista = set()
    for n in conn.execute(
            "SELECT en.candidato_id, en.cargo_id FROM entrevistas en JOIN candidatos c ON c.id=en.candidato_id"
            " WHERE c.empresa_id=?", (empresa_id,)):
        notas_entrevista.add((n["candidato_id"], n["cargo_id"]))

    indicados = set()
    try:
        for i in conn.execute("SELECT indicado_id FROM indicacoes WHERE empresa_id=?", (empresa_id,)):
            indicados.add(i["indicado_id"])
    except Exception:  # noqa: BLE001  (sem indicacoes.py)
        pass

    # ---------------------------------------------- uma linha por candidatura
    itens = []
    for r in linhas:
        criado = ler_data(r["criado_em"])
        ev = etapas_dos_eventos(eventos.get(r["candidato_id"], []), r["vaga_titulo"])
        etapa = r["etapa"]
        alcance = ORDEM_ETAPAS.get(etapa, 0) if etapa != "reprovado" else 0
        for e in ev:
            if e in ORDEM_ETAPAS:
                alcance = max(alcance, ORDEM_ETAPAS[e])
        chs = chamadas.get(r["id"], [])
        primeira_ligacao = ler_data(chs[0]["iniciada_em"]) if chs else None
        triado = any(_atendeu(c) for c in chs)
        qualificado = (r["voz_tier"] or "") in TIERS_QUALIFICADOS
        tipos = testes.get(r["candidato_id"], set())
        testes_ok = bool(r["cand_completo"]) or ("disc" in tipos and "base" in tipos)
        ents = agenda_por_ca.get(r["id"]) or agenda_por_cand.get(r["candidato_id"]) or []
        entrevista_data = ler_data(ents[0]["inicio_utc"]) if ents else None
        if not entrevista_data and "entrevista" in ev:
            entrevista_data = ev["entrevista"]
        realizada = (any(a["status"] == "realizada" for a in ents)
                     or (r["candidato_id"], r["vaga_cargo_id"]) in notas_entrevista
                     or alcance >= ORDEM_ETAPAS["proposta"])
        marcada = realizada or bool(ents) or alcance >= ORDEM_ETAPAS["entrevista"]
        contratado = etapa == "contratado"
        contratado_em = None
        if contratado:
            contratado_em = ev.get("contratado") or ler_data(r["atualizado_em"])
        itens.append({
            "r": r, "criado": criado, "coorte": bool(criado and inicio <= criado < fim),
            "fonte": fonte_de(_tags(r["cand_tags"]), r["candidato_id"] in indicados),
            "triado": triado, "qualificado": qualificado, "testes": testes_ok,
            "marcada": marcada, "realizada": realizada,
            "proposta": alcance >= ORDEM_ETAPAS["proposta"], "contratado": contratado,
            "contratado_em": contratado_em, "reprovado": etapa == "reprovado",
            "primeira_ligacao": primeira_ligacao, "entrevista_data": entrevista_data,
            "chamadas": chs,
        })

    coorte = [i for i in itens if i["coorte"]]

    def contar(grupo):
        return {
            "inscritos": len(grupo),
            "triados": sum(1 for i in grupo if i["triado"]),
            "qualificados": sum(1 for i in grupo if i["qualificado"]),
            "testes": sum(1 for i in grupo if i["testes"]),
            "entrevista_marcada": sum(1 for i in grupo if i["marcada"]),
            "entrevista_realizada": sum(1 for i in grupo if i["realizada"]),
            "proposta": sum(1 for i in grupo if i["proposta"]),
            "contratados": sum(1 for i in grupo if i["contratado"]),
            "reprovados": sum(1 for i in grupo if i["reprovado"]),
        }

    def dias_contratacao(grupo):
        dias = []
        for i in grupo:
            if i["contratado"] and i["criado"] and i["contratado_em"] and i["contratado_em"] >= i["criado"]:
                dias.append((i["contratado_em"] - i["criado"]).total_seconds() / 86400.0)
        return dias

    total = contar(coorte)
    # conversão: dos que chegaram à etapa anterior, quantos chegaram a esta (nunca passa de 100%)
    funil, anterior = [], None
    for etapa in ETAPAS_FUNIL:
        flag = FLAG_ETAPA[etapa]
        atual = [i for i in coorte if flag is None or i[flag]]
        conversao = None
        if anterior is not None:
            seguiram = sum(1 for i in anterior if flag is None or i[flag])
            conversao = pct(seguiram, len(anterior))
        funil.append({"etapa": etapa, "n": len(atual), "conversao_pct": conversao,
                      "do_total_pct": pct(len(atual), total["inscritos"])})
        anterior = atual

    # ---------------------------------------------- tempos
    dias_hire = dias_contratacao(coorte)
    horas_ligacao, dias_lig_entrevista = [], []
    for i in coorte:
        if i["criado"] and i["primeira_ligacao"] and i["primeira_ligacao"] >= i["criado"]:
            horas_ligacao.append((i["primeira_ligacao"] - i["criado"]).total_seconds() / 3600.0)
        if i["primeira_ligacao"] and i["entrevista_data"] and i["entrevista_data"] >= i["primeira_ligacao"]:
            dias_lig_entrevista.append((i["entrevista_data"] - i["primeira_ligacao"]).total_seconds() / 86400.0)
    tempos = {
        "contratacao_dias": resumo_tempos(dias_hire),
        "primeira_ligacao_horas": resumo_tempos(horas_ligacao),
        "ligacao_entrevista_dias": resumo_tempos(dias_lig_entrevista),
    }

    # ---------------------------------------------- custo da voz (ligações do período)
    custo_voz_min, custo_tel_min = premissas_custo(conn)
    custo_minuto = custo_voz_min + custo_tel_min
    n_ligacoes, minutos, segundos = 0, 0, 0
    minutos_por_ca = {}
    for i in itens:
        for ch in i["chamadas"]:
            quando = ler_data(ch["iniciada_em"])
            if not quando or not (inicio <= quando < fim):
                continue
            n_ligacoes += 1
            m = minutos_cobrados(ch["duracao"])
            minutos += m
            segundos += _segundos(ch["duracao"])
            minutos_por_ca[i["r"]["id"]] = minutos_por_ca.get(i["r"]["id"], 0) + m
    custo_total = minutos * custo_minuto
    custo = {
        "ligacoes": n_ligacoes, "minutos": minutos, "minutos_reais": r1(segundos / 60.0),
        "custo_min_voz": custo_voz_min, "custo_min_tel": custo_tel_min,
        "custo_minuto": round(custo_minuto, 4), "moeda": "USD",
        "custo_total": dinheiro(custo_total),
        "por_qualificado": dinheiro(custo_total / total["qualificados"]) if total["qualificados"] else None,
        "por_contratacao": dinheiro(custo_total / total["contratados"]) if total["contratados"] else None,
    }

    # ---------------------------------------------- origem
    fontes = []
    for f in FONTES:
        grupo = [i for i in coorte if i["fonte"] == f]
        if not grupo:
            continue
        c = contar(grupo)
        fontes.append({"fonte": f, "inscritos": c["inscritos"], "qualificados": c["qualificados"],
                       "contratados": c["contratados"],
                       "qualificacao_pct": pct(c["qualificados"], c["inscritos"]),
                       "conversao_pct": pct(c["contratados"], c["inscritos"])})

    # ---------------------------------------------- por vaga e por cargo
    def tabela(chave, rotulo):
        grupos = {}
        for i in coorte:
            grupos.setdefault(i["r"][chave], []).append(i)
        saida = []
        for k, grupo in grupos.items():
            c = contar(grupo)
            dias = dias_contratacao(grupo)
            minutos_g = sum(minutos_por_ca.get(i["r"]["id"], 0) for i in grupo)
            linha = rotulo(grupo[0]["r"])
            linha.update({
                "inscritos": c["inscritos"], "triados": c["triados"], "qualificados": c["qualificados"],
                "entrevistas": c["entrevista_marcada"], "propostas": c["proposta"],
                "contratados": c["contratados"], "reprovados": c["reprovados"],
                "conversao_pct": pct(c["contratados"], c["inscritos"]),
                "mediana_dias_contratacao": r1(mediana(dias)),
                "custo_voz": dinheiro(minutos_g * custo_minuto),
            })
            saida.append(linha)
        saida.sort(key=lambda x: (-x["inscritos"], str(x.get("titulo") or x.get("nome") or "")))
        return saida

    por_vaga = tabela("vaga_id", lambda r: {"vaga_id": r["vaga_id"], "titulo": r["vaga_titulo"],
                                            "cargo_id": r["vaga_cargo_id"], "cargo": r["cargo_nome"] or "",
                                            "status": r["vaga_status"]})
    por_cargo = tabela("vaga_cargo_id", lambda r: {"cargo_id": r["vaga_cargo_id"], "nome": r["cargo_nome"] or ""})

    # ---------------------------------------------- tendência semanal
    semanas, s = [], segunda_de(de)
    while s <= ate:
        ano, num, _ = s.isocalendar()
        semanas.append({"semana": "%d-W%02d" % (ano, num), "inicio": s.isoformat(),
                        "inscritos": 0, "contratados": 0})
        s += timedelta(days=7)
    indice = {w["inicio"]: w for w in semanas}
    for i in coorte:
        w = indice.get(segunda_de(i["criado"].date()).isoformat())
        if w:
            w["inscritos"] += 1
    for i in itens:  # contratações pela data da contratação, dentro do período
        ce = i["contratado_em"]
        if ce and inicio <= ce < fim:
            w = indice.get(segunda_de(ce.date()).isoformat())
            if w:
                w["contratados"] += 1

    # ---------------------------------------------- motivos de encerramento
    enc = dict.fromkeys(ENCERRAMENTOS, 0)
    manuais = {}
    for i in coorte:
        r = i["r"]
        outcome = r["voz_outcome"] or ""
        status_voz = r["voz_status"] or ""
        if outcome in OUTCOME_ENCERRAMENTO:
            enc[OUTCOME_ENCERRAMENTO[outcome]] += 1
        elif outcome == "NOT_QUALIFIED" or status_voz == "nao_qualificado":
            enc["nao_qualificado"] += 1
        elif r["etapa"] == "reprovado":
            enc["reprovacao_manual"] += 1
            motivo = (r["motivo_reprovacao"] or "").strip()
            manuais[motivo] = manuais.get(motivo, 0) + 1
        elif status_voz == "correio_voz":
            enc["sem_resposta"] += 1
    motivos_manuais = [{"motivo": k, "n": n} for k, n in
                       sorted(manuais.items(), key=lambda kv: (-kv[1], kv[0]))][:15]

    # ---------------------------------------------- opções dos filtros
    opcoes = {
        "vagas": [{"id": v["id"], "titulo": v["titulo"], "cargo_id": v["cargo_id"], "status": v["status"]}
                  for v in conn.execute("SELECT id, titulo, cargo_id, status FROM vagas WHERE empresa_id=?"
                                        " ORDER BY titulo COLLATE NOCASE", (empresa_id,))],
        "cargos": [{"id": c["id"], "nome": c["nome"]}
                   for c in conn.execute("SELECT id, nome FROM cargos WHERE empresa_id=?"
                                         " ORDER BY nome COLLATE NOCASE", (empresa_id,))],
    }

    return {
        "periodo": {"de": de.isoformat(), "ate": ate.isoformat()},
        "filtros": {"vaga_id": vaga_id, "cargo_id": cargo_id},
        "opcoes": opcoes,
        "kpis": {
            "inscritos": total["inscritos"], "qualificados": total["qualificados"],
            "entrevistas": total["entrevista_marcada"], "contratados": total["contratados"],
            "reprovados": total["reprovados"],
            "taxa_qualificacao_pct": pct(total["qualificados"], total["inscritos"]),
            "taxa_contratacao_pct": pct(total["contratados"], total["inscritos"]),
            "mediana_dias_contratacao": tempos["contratacao_dias"]["mediana"],
            "custo_total": custo["custo_total"], "custo_por_contratacao": custo["por_contratacao"],
        },
        "funil": funil,
        "reprovados": total["reprovados"],
        "fontes": fontes,
        "tempos": tempos,
        "custo_voz": custo,
        "por_vaga": por_vaga,
        "por_cargo": por_cargo,
        "tendencia": semanas,
        "encerramentos": enc,
        "motivos_manuais": motivos_manuais,
    }


# ------------------------------------------------------------- rota

def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/relatorios/"):
        return None
    if method == "GET" and path == "/api/gestor/relatorios/contratacao":
        from urllib.parse import parse_qs, urlparse
        consulta = parse_qs(urlparse(h.path).query)
        de, ate, vaga_id, cargo_id, erro, status = _validar_filtros(conn, gestor, consulta)
        if erro:
            return _resp(h, status, {"erro": erro})
        return _resp(h, 200, relatorio(conn, gestor, de, ate, vaga_id, cargo_id))
    return _resp(h, 404, {"erro": "Rota não encontrada"})


def _resp(h, status, dados):
    h._json(status, dados)
    return True
