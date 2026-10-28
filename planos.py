"""
Planos, medição de uso e cobrança da Bússola (SaaS).

- Catálogo de planos editável pelo dono (config "planos_catalogo", JSON), com
  complementos (minuto extra, número extra, SMS extra) e teste grátis.
- Premissas de custo (config "planos_premissas") e a calculadora custos():
  custo variável no uso total, rateio do custo fixo, margem, ponto de
  equilíbrio e preço sugerido para a margem alvo.
- Medição por empresa e mês civil (America/New_York): minutos de voz =
  soma de ceil(duracao/60) das ligações dos candidatos da empresa.
- Limite do plano: voz.iniciar_ligacao consulta voz_bloqueada() e recusa com
  o código "plan_limit" quando a empresa passou do limite sem excedente.
- Gestores e vagas ativas: limite_gestores() e limite_vagas() devolvem
  (permitido, usado, maximo); o server.py e o empresas.py consultam antes de
  criar ou aprovar um gestor e antes de abrir uma vaga, e respondem 403 com
  erro_limite_gestores() ou erro_limite_vagas(). O dono libera mais com
  gestores_extra e vagas_extra (ou trocando o plano da empresa).
- Assinatura pelo site (POST /api/assinar), catálogo público (GET /api/planos),
  Stripe (Checkout, webhook assinado e portal de cobrança) via urllib.
- Rotina diária: avisa o fim do teste (3 dias e 1 dia antes) e suspende o
  teste vencido sem pagamento depois de 3 dias de tolerância.

Empresas sem plano do catálogo (contratos antigos, cobrança manual) não têm
limite de minutos, de gestores nem de vagas ativas.
"""
import copy
import hashlib
import hmac
import json
import math
import re
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

srv = None  # módulo do servidor, injetado por ligar()

FUSO = ZoneInfo("America/New_York")
IDIOMAS = ("pt", "en", "es")
CICLOS = ("mensal", "anual")
TOLERANCIA_TESTE_DIAS = 3       # dias depois do fim do teste até suspender
TOLERANCIA_CANCELAMENTO_DIAS = 3
STRIPE_TOLERANCIA = 300         # segundos (5 minutos) para o carimbo do webhook
ENVIO_EM_SEGUNDO_PLANO = True   # os testes desligam para conferir os e-mails na hora
STRIPE_TESTE = None             # função falsa (metodo, caminho, params) -> dict, nos testes
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
CODIGO_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,29}$")
MODULO_RE = re.compile(r"^[a-z_]{2,30}$")


def ligar(modulo_servidor):
    global srv
    srv = modulo_servidor


# ------------------------------------------------------------ catálogo padrão

def _txt(pt, en, es):
    return {"pt": pt, "en": en, "es": es}


_BASE_RECURSOS = {
    "pt": ["Recrutamento com página de vagas", "Testes DISC e B.A.S.E.", "Pipeline de candidatos",
           "Matriz de gaps de competências", "Agenda de entrevistas", "Onboarding de contratados",
           "Entrada de candidatos do Indeed"],
    "en": ["Recruiting with a careers page", "DISC and B.A.S.E. assessments", "Candidate pipeline",
           "Skills gap matrix", "Interview scheduling", "New hire onboarding", "Indeed applicant intake"],
    "es": ["Reclutamiento con página de vacantes", "Pruebas DISC y B.A.S.E.", "Pipeline de candidatos",
           "Matriz de brechas de competencias", "Agenda de entrevistas", "Onboarding de contratados",
           "Ingreso de candidatos desde Indeed"],
}
_MODULOS_BASE = ["diagnostico", "onboarding", "agenda", "entrada"]


def _recursos(extra):
    return {lang: list(extra[lang]) + _BASE_RECURSOS[lang] for lang in IDIOMAS}


CATALOGO_PADRAO = {
    "planos": [
        {
            "codigo": "essencial",
            "nome": _txt("Essencial", "Essential", "Esencial"),
            "descricao": _txt("Recrutamento completo, sem triagem por voz.",
                              "Full recruiting toolkit, without voice screening.",
                              "Reclutamiento completo, sin entrevista por voz."),
            "preco_mensal": 39, "preco_anual": 390, "minutos_voz": 0, "numero_exclusivo": False,
            "sms_mes": 0, "gestores_max": 3, "vagas_ativas_max": None, "modulos": list(_MODULOS_BASE),
            "destaque": False, "ordem": 1, "ativo": True,
            "recursos": _recursos({"pt": ["Até 3 gestores"], "en": ["Up to 3 managers"],
                                   "es": ["Hasta 3 gerentes"]}),
        },
        {
            "codigo": "voz100",
            "nome": _txt("Voz 100", "Voice 100", "Voz 100"),
            "descricao": _txt("Tudo do Essencial e 100 minutos de triagem por voz com IA.",
                              "Everything in Essential plus 100 minutes of AI voice screening.",
                              "Todo lo de Esencial y 100 minutos de entrevista por voz con IA."),
            "preco_mensal": 99, "preco_anual": 990, "minutos_voz": 100, "numero_exclusivo": False,
            "sms_mes": 0, "gestores_max": 5, "vagas_ativas_max": None, "modulos": _MODULOS_BASE + ["voz"],
            "destaque": False, "ordem": 2, "ativo": True,
            "recursos": _recursos({
                "pt": ["100 minutos de triagem por voz por mês", "Número de chamada compartilhado", "Até 5 gestores"],
                "en": ["100 voice screening minutes per month", "Shared caller ID number", "Up to 5 managers"],
                "es": ["100 minutos de entrevista por voz al mes", "Número de llamada compartido", "Hasta 5 gerentes"],
            }),
        },
        {
            "codigo": "voz300",
            "nome": _txt("Voz 300", "Voice 300", "Voz 300"),
            "descricao": _txt("Para quem contrata todo mês: 300 minutos, número local exclusivo e SMS.",
                              "For teams hiring every month: 300 minutes, a dedicated local number and SMS.",
                              "Para quien contrata cada mes: 300 minutos, número local exclusivo y SMS."),
            "preco_mensal": 199, "preco_anual": 1990, "minutos_voz": 300, "numero_exclusivo": True,
            "sms_mes": 300, "gestores_max": 10, "vagas_ativas_max": None, "modulos": _MODULOS_BASE + ["voz"],
            "destaque": True, "ordem": 3, "ativo": True,
            "recursos": _recursos({
                "pt": ["300 minutos de triagem por voz por mês", "Número local exclusivo", "300 SMS por mês",
                       "Até 10 gestores"],
                "en": ["300 voice screening minutes per month", "Dedicated local number", "300 SMS per month",
                       "Up to 10 managers"],
                "es": ["300 minutos de entrevista por voz al mes", "Número local exclusivo", "300 SMS al mes",
                       "Hasta 10 gerentes"],
            }),
        },
        {
            "codigo": "voz1000",
            "nome": _txt("Voz 1000", "Voice 1000", "Voz 1000"),
            "descricao": _txt("Alto volume: 1000 minutos, número exclusivo, 1000 SMS e suporte prioritário.",
                              "High volume: 1000 minutes, a dedicated number, 1000 SMS and priority support.",
                              "Alto volumen: 1000 minutos, número exclusivo, 1000 SMS y soporte prioritario."),
            "preco_mensal": 449, "preco_anual": 4490, "minutos_voz": 1000, "numero_exclusivo": True,
            "sms_mes": 1000, "gestores_max": None, "vagas_ativas_max": None, "modulos": _MODULOS_BASE + ["voz"],
            "destaque": False, "ordem": 4, "ativo": True,
            "recursos": _recursos({
                "pt": ["1000 minutos de triagem por voz por mês", "Número local exclusivo", "1000 SMS por mês",
                       "Gestores ilimitados", "Suporte prioritário"],
                "en": ["1000 voice screening minutes per month", "Dedicated local number", "1000 SMS per month",
                       "Unlimited managers", "Priority support"],
                "es": ["1000 minutos de entrevista por voz al mes", "Número local exclusivo", "1000 SMS al mes",
                       "Gerentes ilimitados", "Soporte prioritario"],
            }),
        },
    ],
    "addons": {"minuto_extra": 0.30, "numero_extra": 10, "sms_extra": 0.03},
    "trial": {"dias": 14, "minutos": 20},
}

PREMISSAS_PADRAO = {
    "custo_min_voz": 0.09,     # ElevenLabs, US$ por minuto de ligação
    "custo_min_tel": 0.014,    # Twilio, US$ por minuto iniciado
    "custo_numero": 1.15,      # número local, US$ por mês
    "custo_sms": 0.0083,       # US$ por segmento
    "custo_a2p": 15,           # campanha A2P, US$ por mês por empresa com SMS
    "horas_manutencao": 10,    # horas por mês
    "valor_hora": 60,          # US$ por hora (a confirmar)
    "empresas_pagantes": 10,
    "margem_alvo": 70,         # %
}


# ------------------------------------------------------------ banco

COLUNAS_EMPRESA = (
    ("ciclo", "TEXT DEFAULT 'mensal'"),
    ("trial_fim", "TEXT DEFAULT ''"),
    ("trial_avisos", "TEXT DEFAULT ''"),
    ("minutos_extra", "INTEGER DEFAULT 0"),
    ("numeros_extra", "INTEGER DEFAULT 0"),
    ("excedente_permitido", "INTEGER DEFAULT 0"),
    ("contato_telefone", "TEXT DEFAULT ''"),
    ("stripe_customer", "TEXT DEFAULT ''"),
    ("stripe_subscription", "TEXT DEFAULT ''"),
    ("pagamento_status", "TEXT DEFAULT ''"),
    ("pago_ate", "TEXT DEFAULT ''"),
    ("suspender_em", "TEXT DEFAULT ''"),
    ("gestores_extra", "INTEGER DEFAULT 0"),   # gestores além do plano, liberados pelo dono
    ("vagas_extra", "INTEGER DEFAULT 0"),      # vagas ativas além do plano, liberadas pelo dono
)


def init_planos(c):
    """Colunas de cobrança na tabela empresas, eventos do Stripe e catálogo inicial."""
    colunas = {r[1] for r in c.execute("PRAGMA table_info(empresas)").fetchall()}
    for nome, ddl in COLUNAS_EMPRESA:
        if nome not in colunas:
            c.execute("ALTER TABLE empresas ADD COLUMN %s %s" % (nome, ddl))
    c.execute(
        "CREATE TABLE IF NOT EXISTS stripe_eventos ("
        " id TEXT PRIMARY KEY,"
        " tipo TEXT DEFAULT '',"
        " empresa_id INTEGER,"
        " recebido_em TEXT DEFAULT (datetime('now')))"
    )
    for chave, valor in (("planos_catalogo", CATALOGO_PADRAO), ("planos_premissas", PREMISSAS_PADRAO)):
        if not c.execute("SELECT 1 FROM config WHERE chave=?", (chave,)).fetchone():
            c.execute("INSERT INTO config (chave, valor) VALUES (?,?)", (chave, json.dumps(valor, ensure_ascii=False)))


# ------------------------------------------------------------ utilidades

def _num(v, padrao=None, minimo=0.0):
    try:
        if isinstance(v, bool):
            raise ValueError
        f = float(v)
    except (TypeError, ValueError):
        return padrao
    if math.isnan(f) or math.isinf(f) or f < minimo:
        return padrao
    return f


def _int_ou_nulo(v):
    if v is None or v == "":
        return None, True
    f = _num(v)
    if f is None:
        return None, False
    return int(f), True


def _lang(v):
    s = str(v or "").lower()[:2]
    return s if s in IDIOMAS else "pt"


def _texto(d, lang):
    if isinstance(d, dict):
        return d.get(lang) or d.get("pt") or d.get("en") or ""
    return str(d or "")


def _r2(v):
    return round(float(v) + 0.0, 2)


def hoje_ny(agora=None):
    agora = agora or datetime.now(timezone.utc)
    return agora.astimezone(FUSO).date()


def _data(texto):
    try:
        return date.fromisoformat(str(texto or "")[:10])
    except ValueError:
        return None


def _row_get(row, chave, padrao=None):
    try:
        if chave in row.keys():
            v = row[chave]
            return padrao if v is None else v
    except AttributeError:
        return row.get(chave, padrao)
    return padrao


# ------------------------------------------------------------ catálogo

def catalogo(conn):
    try:
        cat = json.loads(srv.config_get(conn, "planos_catalogo") or "")
        if not isinstance(cat, dict) or not isinstance(cat.get("planos"), list):
            raise ValueError
    except (ValueError, TypeError):
        cat = copy.deepcopy(CATALOGO_PADRAO)
    cat.setdefault("addons", dict(CATALOGO_PADRAO["addons"]))
    cat.setdefault("trial", dict(CATALOGO_PADRAO["trial"]))
    for k, v in CATALOGO_PADRAO["addons"].items():
        cat["addons"].setdefault(k, v)
    for k, v in CATALOGO_PADRAO["trial"].items():
        cat["trial"].setdefault(k, v)
    cat["planos"] = sorted(cat["planos"], key=lambda p: (p.get("ordem") or 0, p.get("codigo") or ""))
    return cat


def plano(conn_ou_cat, codigo):
    cat = conn_ou_cat if isinstance(conn_ou_cat, dict) else catalogo(conn_ou_cat)
    for p in cat["planos"]:
        if p.get("codigo") == (codigo or "").strip():
            return p
    return None


def _textos_validos(v, obrigatorio=False):
    if isinstance(v, str):
        v = {"pt": v}
    if not isinstance(v, dict):
        return None
    pt = str(v.get("pt") or "").strip()[:200]
    if obrigatorio and not pt:
        return None
    return {lang: (str(v.get(lang) or "").strip()[:400] or pt) for lang in IDIOMAS}


def _lista_recursos(v):
    if isinstance(v, str):
        v = {"pt": v}
    if not isinstance(v, dict):
        v = {}
    saida = {}
    for lang in IDIOMAS:
        itens = v.get(lang) if v.get(lang) else v.get("pt") or []
        if isinstance(itens, str):
            itens = itens.split("\n")
        saida[lang] = [str(x).strip()[:160] for x in itens if str(x).strip()][:20]
    return saida


def validar_catalogo(d):
    """Devolve (catalogo_limpo, erro)."""
    if not isinstance(d, dict) or not isinstance(d.get("planos"), list) or not d["planos"]:
        return None, "Catálogo inválido"
    planos, codigos = [], set()
    for i, p in enumerate(d["planos"]):
        if not isinstance(p, dict):
            return None, "Catálogo inválido"
        codigo = str(p.get("codigo") or "").strip().lower()
        if not CODIGO_RE.match(codigo):
            return None, "Código de plano inválido"
        if codigo in codigos:
            return None, "Códigos de plano repetidos"
        codigos.add(codigo)
        nome = _textos_validos(p.get("nome"), obrigatorio=True)
        if not nome:
            return None, "Informe o nome do plano"
        mensal = _num(p.get("preco_mensal"))
        anual = _num(p.get("preco_anual")) if p.get("preco_anual") not in (None, "") else (
            mensal * 10 if mensal is not None else None)
        minutos = _num(p.get("minutos_voz"), 0 if p.get("minutos_voz") in (None, "") else None)
        sms = _num(p.get("sms_mes"), 0 if p.get("sms_mes") in (None, "") else None)
        gmax, ok1 = _int_ou_nulo(p.get("gestores_max"))
        vmax, ok2 = _int_ou_nulo(p.get("vagas_ativas_max"))
        if None in (mensal, anual, minutos, sms) or not (ok1 and ok2):
            return None, "Valor inválido no catálogo"
        modulos = sorted({str(m).strip() for m in (p.get("modulos") or []) if MODULO_RE.match(str(m).strip())})
        planos.append({
            "codigo": codigo, "nome": nome,
            "descricao": _textos_validos(p.get("descricao")) or {lang: "" for lang in IDIOMAS},
            "preco_mensal": _r2(mensal), "preco_anual": _r2(anual), "minutos_voz": int(minutos),
            "numero_exclusivo": bool(p.get("numero_exclusivo")), "sms_mes": int(sms),
            "gestores_max": gmax, "vagas_ativas_max": vmax, "modulos": modulos,
            "destaque": bool(p.get("destaque")), "ordem": int(_num(p.get("ordem"), i + 1)),
            "ativo": p.get("ativo") is not False and p.get("ativo") not in (0, "0", "false"),
            "recursos": _lista_recursos(p.get("recursos")),
        })
    addons_in = d.get("addons") if isinstance(d.get("addons"), dict) else {}
    addons = {}
    for k, padrao in CATALOGO_PADRAO["addons"].items():
        v = _num(addons_in.get(k, padrao))
        if v is None:
            return None, "Valor inválido no catálogo"
        addons[k] = _r2(v)
    trial_in = d.get("trial") if isinstance(d.get("trial"), dict) else {}
    dias = _num(trial_in.get("dias", CATALOGO_PADRAO["trial"]["dias"]))
    mins = _num(trial_in.get("minutos", CATALOGO_PADRAO["trial"]["minutos"]))
    if dias is None or mins is None or dias > 90:
        return None, "Valor inválido no catálogo"
    planos.sort(key=lambda p: (p["ordem"], p["codigo"]))
    return {"planos": planos, "addons": addons, "trial": {"dias": int(dias), "minutos": int(mins)}}, None


def salvar_catalogo(conn, d):
    cat, erro = validar_catalogo(d)
    if erro:
        return None, erro
    srv.config_set(conn, "planos_catalogo", json.dumps(cat, ensure_ascii=False))
    conn.commit()
    return cat, None


def premissas(conn):
    p = dict(PREMISSAS_PADRAO)
    try:
        salvo = json.loads(srv.config_get(conn, "planos_premissas") or "{}")
        if isinstance(salvo, dict):
            for k in PREMISSAS_PADRAO:
                v = _num(salvo.get(k))
                if v is not None:
                    p[k] = v
    except (ValueError, TypeError):
        pass
    return p


def validar_premissas(d, base=None):
    if not isinstance(d, dict):
        return None, "Premissas inválidas"
    p = dict(base or PREMISSAS_PADRAO)
    for k in PREMISSAS_PADRAO:
        if k in d:
            v = _num(d.get(k))
            if v is None:
                return None, "Premissas inválidas"
            p[k] = v
    if p["empresas_pagantes"] < 1 or p["margem_alvo"] >= 100:
        return None, "Premissas inválidas"
    return p, None


def salvar_premissas(conn, d):
    p, erro = validar_premissas(d, premissas(conn))
    if erro:
        return None, erro
    srv.config_set(conn, "planos_premissas", json.dumps(p))
    conn.commit()
    return p, None


# ------------------------------------------------------------ calculadora

def custo_variavel(p, pr, minutos=None, sms=None, numeros_extra=0):
    """Custo real de um mês. Sem minutos/sms informados, considera o uso total do plano."""
    minutos = p.get("minutos_voz", 0) if minutos is None else minutos
    sms = p.get("sms_mes", 0) if sms is None else sms
    numeros = (1 if p.get("numero_exclusivo") else 0) + (numeros_extra or 0)
    total = (minutos * (pr["custo_min_voz"] + pr["custo_min_tel"]) + numeros * pr["custo_numero"]
             + sms * pr["custo_sms"] + (pr["custo_a2p"] if (p.get("sms_mes") or 0) > 0 or sms > 0 else 0))
    return total


def custos(cat, pr):
    """Por plano: custo variável no uso total, rateio do custo fixo, margem em US$ e %,
    empresas para empatar (cobrir todo o custo fixo só com este plano) e preço
    sugerido para a margem alvo."""
    fixo_total = pr["horas_manutencao"] * pr["valor_hora"]
    pagantes = max(pr["empresas_pagantes"], 1)
    fixo = fixo_total / pagantes
    alvo = min(max(pr["margem_alvo"], 0), 99) / 100.0
    linhas = []
    for p in cat["planos"]:
        var = custo_variavel(p, pr)
        total = var + fixo
        preco = float(p.get("preco_mensal") or 0)
        margem = preco - total
        contribuicao = preco - var
        linhas.append({
            "codigo": p["codigo"], "nome": p["nome"], "preco_mensal": _r2(preco),
            "preco_anual_mes": _r2((p.get("preco_anual") or 0) / 12.0),
            "custo_variavel": _r2(var), "custo_fixo": _r2(fixo), "custo_total": _r2(total),
            "margem": _r2(margem), "margem_pct": _r2(100.0 * margem / preco) if preco > 0 else None,
            "empresas_equilibrio": int(math.ceil(fixo_total / contribuicao - 1e-9)) if contribuicao > 0 else None,
            "preco_sugerido": _r2(total / (1 - alvo)),
            "preco_sugerido_redondo": int(math.ceil(total / (1 - alvo) - 1e-9)),
        })
    custo_minuto = pr["custo_min_voz"] + pr["custo_min_tel"]
    addons = cat.get("addons") or {}
    return {
        "planos": linhas,
        "custo_fixo_total": _r2(fixo_total),
        "custo_minuto": round(custo_minuto, 4),
        "addons": {
            "minuto_extra": {"preco": addons.get("minuto_extra", 0), "custo": round(custo_minuto, 4),
                             "margem_pct": _r2(100.0 * (addons.get("minuto_extra", 0) - custo_minuto)
                                               / addons["minuto_extra"]) if addons.get("minuto_extra") else None},
            "numero_extra": {"preco": addons.get("numero_extra", 0), "custo": pr["custo_numero"],
                             "margem_pct": _r2(100.0 * (addons.get("numero_extra", 0) - pr["custo_numero"])
                                               / addons["numero_extra"]) if addons.get("numero_extra") else None},
            "sms_extra": {"preco": addons.get("sms_extra", 0), "custo": pr["custo_sms"],
                          "margem_pct": _r2(100.0 * (addons.get("sms_extra", 0) - pr["custo_sms"])
                                            / addons["sms_extra"]) if addons.get("sms_extra") else None},
        },
    }


# ------------------------------------------------------------ medição de uso

def mes_de(agora=None):
    d = hoje_ny(agora)
    return "%04d-%02d" % (d.year, d.month)


def limites_do_mes(mes):
    """Início e fim (exclusivo) do mês civil de Nova York, em UTC no formato do SQLite."""
    ano, m = int(mes[:4]), int(mes[5:7])
    inicio = datetime(ano, m, 1, tzinfo=FUSO)
    fim = datetime(ano + (m == 12), 1 if m == 12 else m + 1, 1, tzinfo=FUSO)
    fmt = "%Y-%m-%d %H:%M:%S"
    return inicio.astimezone(timezone.utc).strftime(fmt), fim.astimezone(timezone.utc).strftime(fmt)


def minutos_usados(conn, empresa_id, mes):
    ini, fim = limites_do_mes(mes)
    r = conn.execute(
        "SELECT COALESCE(SUM((vc.duracao + 59) / 60), 0) FROM voz_chamadas vc"
        " JOIN candidatos c ON c.id=vc.candidato_id"
        " WHERE c.empresa_id=? AND vc.duracao > 0 AND vc.iniciada_em >= ? AND vc.iniciada_em < ?",
        (empresa_id, ini, fim),
    ).fetchone()
    return int(r[0] or 0)


def _empresa(conn, empresa):
    if isinstance(empresa, int):
        return conn.execute("SELECT * FROM empresas WHERE id=?", (empresa,)).fetchone()
    return empresa


def em_teste(e):
    return _row_get(e, "status") == "teste" and bool(_row_get(e, "trial_fim", ""))


def limite_minutos(cat, e):
    """Minutos do mês: os do teste (empresa em teste pelo site) ou do plano, mais os extras
    comprados. None = sem limite (empresa sem plano do catálogo)."""
    extra = int(_row_get(e, "minutos_extra", 0) or 0)
    if em_teste(e):
        return int(cat["trial"]["minutos"]) + extra
    p = plano(cat, _row_get(e, "plano", ""))
    if not p:
        return None
    return int(p.get("minutos_voz") or 0) + extra


def status_uso(minutos, limite):
    if limite is None:
        return "ok", None
    if limite <= 0:
        return ("over" if minutos > 0 else "ok"), (100.0 if minutos > 0 else 0.0)
    pct = 100.0 * minutos / limite
    if minutos >= limite:
        return "over", round(pct, 1)
    if pct >= 80:
        return "near", round(pct, 1)
    return "ok", round(pct, 1)


def uso(conn, empresa, mes=None, cat=None, agora=None):
    e = _empresa(conn, empresa)
    if not e:
        return None
    cat = cat or catalogo(conn)
    mes = mes or mes_de(agora)
    minutos = minutos_usados(conn, e["id"], mes)
    limite = limite_minutos(cat, e)
    st, pct = status_uso(minutos, limite)
    return {
        "mes": mes, "minutos": minutos, "limite": limite, "ilimitado": limite is None,
        "minutos_extra": int(_row_get(e, "minutos_extra", 0) or 0),
        "restantes": None if limite is None else max(limite - minutos, 0),
        "excedente": 0 if limite is None else max(minutos - limite, 0),
        "pct": pct, "status": st, "sms": 0,
        "sms_limite": (plano(cat, _row_get(e, "plano", "")) or {}).get("sms_mes", 0),
        "excedente_permitido": bool(_row_get(e, "excedente_permitido", 0)) and _row_get(e, "status") == "ativa",
    }


def voz_bloqueada(conn, empresa_id, agora=None):
    """True quando a empresa gastou os minutos do mês e não tem excedente liberado
    (empresa em teste nunca tem excedente). Usado por voz.iniciar_ligacao."""
    e = _empresa(conn, empresa_id)
    if not e:
        return False
    u = uso(conn, e, agora=agora)
    if u["ilimitado"] or u["minutos"] < u["limite"]:
        return False
    return not u["excedente_permitido"]


def _limite_recurso(conn, empresa_id, campo_max, campo_extra, sql_uso):
    """(permitido, usado, maximo) para um recurso contado do plano. maximo None =
    sem limite (empresa sem plano do catálogo, ou plano com o campo vazio)."""
    e = _empresa(conn, empresa_id)
    if not e:
        return True, 0, None
    usado = int(conn.execute(sql_uso, (e["id"],)).fetchone()[0] or 0)
    p = plano(conn, _row_get(e, "plano", ""))
    if not p or p.get(campo_max) is None:
        return True, usado, None
    maximo = max(int(p.get(campo_max) or 0) + int(_row_get(e, campo_extra, 0) or 0), 0)
    return usado < maximo, usado, maximo


def limite_gestores(conn, empresa_id):
    """Gestores aprovados da empresa contra gestores_max do plano (mais gestores_extra).
    Contas pendentes de aprovação não contam."""
    return _limite_recurso(conn, empresa_id, "gestores_max", "gestores_extra",
                           "SELECT COUNT(*) FROM gestores WHERE empresa_id=? AND aprovado=1")


def limite_vagas(conn, empresa_id):
    """Vagas com status 'aberta' contra vagas_ativas_max do plano (mais vagas_extra)."""
    return _limite_recurso(conn, empresa_id, "vagas_ativas_max", "vagas_extra",
                           "SELECT COUNT(*) FROM vagas WHERE empresa_id=? AND status='aberta'")


def _erro_limite(conn, empresa_id, modelo, maximo, lang=None):
    """Monta a mensagem em português com o nome do plano; com lang en ou es, traduz pelo
    erros_i18n e troca o nome do plano pelo nome naquele idioma."""
    e = _empresa(conn, empresa_id)
    p = plano(conn, _row_get(e, "plano", "")) if e else None
    nome_pt = _texto(p["nome"], "pt") if p else ""
    texto = modelo % (nome_pt, maximo)
    idioma = str(lang or "").strip().lower()[:2]
    if p and idioma in ("en", "es"):
        texto = srv.erros_i18n.traduzir(texto, idioma)
        if nome_pt:
            texto = texto.replace(nome_pt, _texto(p["nome"], idioma), 1)
    return texto


def erro_limite_gestores(conn, empresa_id, maximo, lang=None):
    """Mensagem do 403 de limite de gestores (em pt; en e es vêm do erros_i18n)."""
    return _erro_limite(conn, empresa_id, "O plano %s permite até %d gestores ativos. "
                        "Faça upgrade do plano para adicionar mais gestores.", maximo, lang)


def erro_limite_vagas(conn, empresa_id, maximo, lang=None):
    """Mensagem do 403 de limite de vagas ativas (em pt; en e es vêm do erros_i18n)."""
    return _erro_limite(conn, empresa_id, "O plano %s permite até %d vagas ativas. "
                        "Faça upgrade do plano ou encerre uma vaga para abrir outra.", maximo, lang)


def receita_mensal(cat, e, u=None):
    """MRR da empresa: plano (anual / 12) mais excedente cobrado. Só empresas ativas."""
    if _row_get(e, "status") != "ativa":
        return 0.0
    p = plano(cat, _row_get(e, "plano", ""))
    if not p:
        try:
            return float(str(_row_get(e, "valor", "") or "0").replace("$", "").replace(",", ".").strip() or 0)
        except ValueError:
            return 0.0
    base = (p.get("preco_anual") or 0) / 12.0 if _row_get(e, "ciclo", "mensal") == "anual" else p.get("preco_mensal") or 0
    extra = (int(_row_get(e, "numeros_extra", 0) or 0)) * cat["addons"].get("numero_extra", 0)
    if u and u.get("excedente") and u.get("excedente_permitido"):
        extra += u["excedente"] * cat["addons"].get("minuto_extra", 0)
    return float(base) + extra


def painel_uso(conn, mes=None, agora=None):
    cat = catalogo(conn)
    pr = premissas(conn)
    mes = mes or mes_de(agora)
    linhas, mrr, custo_total = [], 0.0, 0.0
    for e in conn.execute("SELECT * FROM empresas ORDER BY nome").fetchall():
        u = uso(conn, e, mes, cat)
        p = plano(cat, e["plano"]) or {}
        # em teste a empresa usa o número compartilhado, sem SMS: só os minutos custam
        custo = custo_variavel({} if em_teste(e) else p, pr, minutos=u["minutos"], sms=u["sms"],
                               numeros_extra=int(_row_get(e, "numeros_extra", 0) or 0))
        receita = receita_mensal(cat, e, u)
        mrr += receita
        custo_total += custo
        linhas.append({
            "id": e["id"], "nome": e["nome"], "slug": e["slug"], "status": e["status"],
            "plano": e["plano"] or "", "plano_nome": p.get("nome") or None, "ciclo": _row_get(e, "ciclo", "mensal"),
            "trial_fim": _row_get(e, "trial_fim", ""), "pago_ate": _row_get(e, "pago_ate", ""),
            "pagamento_status": _row_get(e, "pagamento_status", ""),
            "stripe": bool(_row_get(e, "stripe_subscription", "")),
            "minutos_extra": int(_row_get(e, "minutos_extra", 0) or 0),
            "numeros_extra": int(_row_get(e, "numeros_extra", 0) or 0),
            "gestores_extra": int(_row_get(e, "gestores_extra", 0) or 0),
            "vagas_extra": int(_row_get(e, "vagas_extra", 0) or 0),
            "excedente_permitido": bool(_row_get(e, "excedente_permitido", 0)),
            "uso": u, "custo_real": _r2(custo), "receita": _r2(receita), "margem": _r2(receita - custo),
            "margem_pct": _r2(100.0 * (receita - custo) / receita) if receita > 0 else None,
        })
    fixo = pr["horas_manutencao"] * pr["valor_hora"]
    return {
        "mes": mes, "empresas": linhas,
        "totais": {"mrr": _r2(mrr), "custo_variavel": _r2(custo_total), "custo_fixo": _r2(fixo),
                   "resultado": _r2(mrr - custo_total - fixo),
                   "pagantes": sum(1 for x in linhas if x["receita"] > 0)},
    }


# ------------------------------------------------------------ e-mails

TEXTOS = {
    "pt": {
        "boas_vindas_assunto": "Bem-vindo à Bússola",
        "boas_vindas": ("Olá, {nome}!\n\nA conta da {empresa} na Bússola está pronta. Seu teste grátis vai até "
                        "{fim} e inclui {minutos} minutos de triagem por voz.\n\nSeu login: {login}\n\n"
                        "Acesse o painel:\n{url}\n\nQualquer dúvida, é só responder este e-mail.\n\nEquipe Bússola"),
        "aviso_assunto": "Seu teste da Bússola termina em {n} dia(s)",
        "aviso": ("Olá, {nome}!\n\nO teste grátis da {empresa} termina em {fim}. Para continuar usando a Bússola "
                  "sem interrupção, escolha seu plano:\n{url}\n\nEquipe Bússola"),
        "suspensa_assunto": "Seu teste da Bússola terminou",
        "suspensa": ("Olá, {nome}!\n\nO teste grátis da {empresa} terminou e o acesso foi pausado. Seus dados "
                     "continuam guardados. Para reativar, escolha seu plano:\n{url}\n\nEquipe Bússola"),
    },
    "en": {
        "boas_vindas_assunto": "Welcome to Bússola",
        "boas_vindas": ("Hi {nome},\n\nThe {empresa} account on Bússola is ready. Your free trial runs until {fim} "
                        "and includes {minutos} minutes of voice screening.\n\nYour username: {login}\n\n"
                        "Open your dashboard:\n{url}\n\nQuestions? Just reply to this email.\n\nThe Bússola team"),
        "aviso_assunto": "Your Bússola trial ends in {n} day(s)",
        "aviso": ("Hi {nome},\n\nThe free trial for {empresa} ends on {fim}. To keep using Bússola without "
                  "interruption, pick your plan:\n{url}\n\nThe Bússola team"),
        "suspensa_assunto": "Your Bússola trial has ended",
        "suspensa": ("Hi {nome},\n\nThe free trial for {empresa} has ended and access is paused. Your data is "
                     "still saved. To reactivate, pick your plan:\n{url}\n\nThe Bússola team"),
    },
    "es": {
        "boas_vindas_assunto": "Bienvenido a Bússola",
        "boas_vindas": ("Hola, {nome}:\n\nLa cuenta de {empresa} en Bússola está lista. Tu prueba gratis dura "
                        "hasta el {fim} e incluye {minutos} minutos de entrevista por voz.\n\nTu usuario: {login}\n\n"
                        "Entra a tu panel:\n{url}\n\n¿Dudas? Solo responde este correo.\n\nEl equipo de Bússola"),
        "aviso_assunto": "Tu prueba de Bússola termina en {n} día(s)",
        "aviso": ("Hola, {nome}:\n\nLa prueba gratis de {empresa} termina el {fim}. Para seguir usando Bússola "
                  "sin interrupciones, elige tu plan:\n{url}\n\nEl equipo de Bússola"),
        "suspensa_assunto": "Tu prueba de Bússola terminó",
        "suspensa": ("Hola, {nome}:\n\nLa prueba gratis de {empresa} terminó y el acceso está en pausa. Tus datos "
                     "siguen guardados. Para reactivarla, elige tu plan:\n{url}\n\nEl equipo de Bússola"),
    },
}


def _t(lang, chave, **kw):
    return TEXTOS[_lang(lang)][chave].format(**kw)


def _enviar(lista):
    """lista de (para, assunto, corpo, idioma). Em segundo plano, com conexão própria."""
    lista = [x for x in lista if x[0]]
    if not lista:
        return

    def trabalho(conn):
        for para, assunto, corpo, lang in lista:
            try:
                srv.enviar_email(conn, para, assunto, corpo, idioma=_lang(lang))
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write("Planos: e-mail falhou: %r\n" % exc)

    if not ENVIO_EM_SEGUNDO_PLANO:
        conn = srv.db()
        try:
            trabalho(conn)
        finally:
            conn.close()
        return

    def rodar():
        conn = srv.db()
        try:
            trabalho(conn)
        finally:
            conn.close()

    threading.Thread(target=rodar, daemon=True).start()


def _admins(conn, empresa_id):
    return conn.execute(
        "SELECT * FROM gestores WHERE empresa_id=? AND is_admin=1 AND aprovado=1 AND email != ''", (empresa_id,)
    ).fetchall()


def _idioma_gestor(g):
    return _lang(_row_get(g, "idioma", "pt"))


def _base_url(conn, h=None):
    host = h.headers.get("Host") if h is not None and getattr(h, "headers", None) else None
    return srv.url_publica(conn, host).rstrip("/")


def _link_assinar(conn, e, codigo=None, h=None):
    return "%s/assinar?plano=%s&e=%s" % (_base_url(conn, h), urllib.parse.quote(codigo or e["plano"] or ""),
                                         urllib.parse.quote(e["slug"]))


# ------------------------------------------------------------ Stripe

class ErroStripe(Exception):
    pass


def stripe_ativo(conn):
    return STRIPE_TESTE is not None or bool(srv.config_get(conn, "stripe_secret_key"))


def _achatar(valor, prefixo=""):
    pares = []
    if isinstance(valor, dict):
        for k, v in valor.items():
            pares += _achatar(v, "%s[%s]" % (prefixo, k) if prefixo else str(k))
    elif isinstance(valor, (list, tuple)):
        for i, v in enumerate(valor):
            pares += _achatar(v, "%s[%d]" % (prefixo, i))
    elif isinstance(valor, bool):
        pares.append((prefixo, "true" if valor else "false"))
    elif valor is not None:
        pares.append((prefixo, str(valor)))
    return pares


def stripe(conn, metodo, caminho, params=None):
    """Chamada à API do Stripe (form-encoded). Nunca registra dados de cartão (não os recebemos)."""
    if STRIPE_TESTE is not None:
        return STRIPE_TESTE(metodo, caminho, params or {})
    chave = srv.config_get(conn, "stripe_secret_key")
    if not chave:
        raise ErroStripe("Stripe não configurado")
    corpo = urllib.parse.urlencode(_achatar(params or {})).encode("utf-8")
    url = "https://api.stripe.com" + caminho
    if metodo == "GET" and corpo:
        url += "?" + corpo.decode("ascii")
        corpo = None
    req = urllib.request.Request(url, data=corpo if metodo != "GET" else None, method=metodo, headers={
        "Authorization": "Bearer " + chave, "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            msg = json.loads(exc.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:  # noqa: BLE001
            msg = ""
        raise ErroStripe(msg or "HTTP %d" % exc.code)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise ErroStripe(str(exc))


def precos_stripe(conn):
    try:
        d = json.loads(srv.config_get(conn, "stripe_precos") or "{}")
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


def criar_checkout(conn, e, p, ciclo, email, h=None, dias_teste=0):
    """Checkout Session (mode=subscription). Preço do Stripe salvo pelo dono
    (stripe_precos["<codigo>_<ciclo>"]) ou criado na hora com price_data."""
    base = _base_url(conn, h)
    preco_id = precos_stripe(conn).get("%s_%s" % (p["codigo"], ciclo), "")
    if preco_id:
        item = {"price": preco_id, "quantity": 1}
    else:
        valor = p["preco_anual"] if ciclo == "anual" else p["preco_mensal"]
        item = {"quantity": 1, "price_data": {
            "currency": "usd", "unit_amount": int(round(float(valor) * 100)),
            "recurring": {"interval": "year" if ciclo == "anual" else "month"},
            "product_data": {"name": "Bússola %s" % _texto(p["nome"], "en")},
        }}
    meta = {"empresa_id": str(e["id"]), "plano": p["codigo"], "ciclo": ciclo}
    params = {
        "mode": "subscription",
        "client_reference_id": str(e["id"]),
        "line_items": [item],
        "metadata": meta,
        "subscription_data": {"metadata": meta},
        "success_url": base + "/gestor?assinatura=ok",
        "cancel_url": "%s/assinar?plano=%s&e=%s&cancelado=1" % (base, p["codigo"], e["slug"]),
    }
    if dias_teste > 0:
        params["subscription_data"]["trial_period_days"] = int(dias_teste)
    if _row_get(e, "stripe_customer", ""):
        params["customer"] = e["stripe_customer"]
    elif email:
        params["customer_email"] = email
    sessao = stripe(conn, "POST", "/v1/checkout/sessions", params)
    url = sessao.get("url") or ""
    if not url:
        raise ErroStripe("Checkout sem URL")
    return url


def assinatura_stripe_valida(corpo, cabecalho, segredo, agora=None, tolerancia=STRIPE_TOLERANCIA):
    """Stripe-Signature: 't=<unix>,v1=<hex>[,v1=...]', HMAC-SHA256 de '<t>.<corpo>'."""
    if not cabecalho or not segredo:
        return False
    t, assinaturas = None, []
    for parte in cabecalho.split(","):
        if "=" not in parte:
            continue
        k, v = parte.strip().split("=", 1)
        if k == "t":
            t = v
        elif k == "v1":
            assinaturas.append(v)
    try:
        t = int(t)
    except (TypeError, ValueError):
        return False
    agora = int(time.time()) if agora is None else int(agora)
    if abs(agora - t) > tolerancia or not assinaturas:
        return False
    if isinstance(corpo, str):
        corpo = corpo.encode("utf-8")
    esperado = hmac.new(segredo.encode("utf-8"), ("%d." % t).encode("utf-8") + corpo, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(esperado, a) for a in assinaturas)


def _empresa_do_evento(conn, obj):
    meta = obj.get("metadata") or {}
    for chave in (meta.get("empresa_id"), obj.get("client_reference_id")):
        try:
            e = conn.execute("SELECT * FROM empresas WHERE id=?", (int(chave),)).fetchone()
            if e:
                return e
        except (TypeError, ValueError):
            pass
    sub = obj.get("subscription") if isinstance(obj.get("subscription"), str) else ""
    if obj.get("object") == "subscription":
        sub = obj.get("id") or ""
    for coluna, valor in (("stripe_subscription", sub), ("stripe_customer", obj.get("customer"))):
        if valor and isinstance(valor, str):
            e = conn.execute("SELECT * FROM empresas WHERE %s=?" % coluna, (valor,)).fetchone()
            if e:
                return e
    return None


def _data_unix(v):
    try:
        return datetime.fromtimestamp(int(v), timezone.utc).astimezone(FUSO).date().isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return ""


def processar_evento(conn, evento, hoje=None):
    """Aplica um evento do Stripe. Idempotente pelo id do evento. Devolve o que fez."""
    hoje = hoje or hoje_ny()
    eid_evento = str(evento.get("id") or "")
    tipo = str(evento.get("type") or "")
    obj = ((evento.get("data") or {}).get("object")) or {}
    if eid_evento and conn.execute("SELECT 1 FROM stripe_eventos WHERE id=?", (eid_evento,)).fetchone():
        return "repetido"
    e = _empresa_do_evento(conn, obj) if isinstance(obj, dict) else None
    acao = "ignorado"
    if e is not None:
        if tipo == "checkout.session.completed":
            meta = obj.get("metadata") or {}
            campos = {"status": "ativa", "pagamento_status": "ok", "suspender_em": "",
                      "stripe_customer": obj.get("customer") or _row_get(e, "stripe_customer", ""),
                      "stripe_subscription": obj.get("subscription") or _row_get(e, "stripe_subscription", "")}
            if meta.get("plano") and plano(conn, meta["plano"]):
                campos["plano"] = meta["plano"]
            if meta.get("ciclo") in CICLOS:
                campos["ciclo"] = meta["ciclo"]
            _atualizar(conn, e["id"], campos)
            acao = "ativada"
        elif tipo == "invoice.paid":
            linhas = ((obj.get("lines") or {}).get("data")) or []
            fim = (linhas[0].get("period") or {}).get("end") if linhas else None
            campos = {"pagamento_status": "ok", "suspender_em": "", "pago_ate": _data_unix(fim or obj.get("period_end"))}
            if e["status"] in ("teste", "suspensa"):
                campos["status"] = "ativa"
            _atualizar(conn, e["id"], campos)
            acao = "estendida"
        elif tipo == "invoice.payment_failed":
            _atualizar(conn, e["id"], {"pagamento_status": "falhou"})
            acao = "sinalizada"
            email = srv.config_get(conn, "dono_email")
            if email:
                _enviar([(email, "Pagamento recusado: %s" % e["nome"],
                          "O Stripe recusou o pagamento da empresa %s (%s). O Stripe vai tentar de novo; "
                          "se a assinatura for cancelada, o acesso é suspenso." % (e["nome"], e["slug"]), "pt")])
        elif tipo == "customer.subscription.deleted":
            _atualizar(conn, e["id"], {
                "pagamento_status": "cancelada",
                "suspender_em": (hoje + timedelta(days=TOLERANCIA_CANCELAMENTO_DIAS)).isoformat()})
            acao = "cancelamento"
    conn.execute("INSERT OR IGNORE INTO stripe_eventos (id, tipo, empresa_id) VALUES (?,?,?)",
                 (eid_evento or secrets.token_hex(8), tipo[:80], e["id"] if e is not None else None))
    conn.commit()
    return acao


def _atualizar(conn, empresa_id, campos):
    if not campos:
        return
    conn.execute("UPDATE empresas SET %s WHERE id=?" % ", ".join("%s=?" % k for k in campos),
                 list(campos.values()) + [empresa_id])


# ------------------------------------------------------------ rotina diária

def _suspender(conn, e):
    conn.execute("UPDATE empresas SET status='suspensa', suspender_em='' WHERE id=?", (e["id"],))
    conn.execute("DELETE FROM sessoes_gestor WHERE gestor_id IN (SELECT id FROM gestores WHERE empresa_id=?)",
                 (e["id"],))


def verificar_trials(conn, hoje=None):
    """Avisos de fim de teste (3 dias e 1 dia antes) e suspensão do teste vencido
    (fim + 3 dias, sem pagamento); suspende também cancelamentos depois da tolerância."""
    hoje = hoje or hoje_ny()
    rel = {"avisos": 0, "suspensas": 0}
    emails = []
    for e in conn.execute(
        "SELECT * FROM empresas WHERE status='teste' AND trial_fim != '' AND COALESCE(stripe_subscription,'')=''"
    ).fetchall():
        fim = _data(e["trial_fim"])
        if not fim:
            continue
        restantes = (fim - hoje).days
        avisos = set(filter(None, (e["trial_avisos"] or "").split(",")))
        chave = None
        if 0 <= restantes <= 1 and "1" not in avisos:
            chave = "1"
        elif 1 < restantes <= 3 and "3" not in avisos:
            chave = "3"
        if chave:
            avisos.update({chave} if chave == "3" else {"1", "3"})
            conn.execute("UPDATE empresas SET trial_avisos=? WHERE id=?", (",".join(sorted(avisos)), e["id"]))
            for g in _admins(conn, e["id"]):
                lang = _idioma_gestor(g)
                emails.append((g["email"], _t(lang, "aviso_assunto", n=max(restantes, 0)),
                               _t(lang, "aviso", nome=g["nome"], empresa=e["nome"], fim=fim.isoformat(),
                                  url=_link_assinar(conn, e)), lang))
            rel["avisos"] += 1
        if (hoje - fim).days > TOLERANCIA_TESTE_DIAS:
            admins = _admins(conn, e["id"])
            _suspender(conn, e)
            for g in admins:
                lang = _idioma_gestor(g)
                emails.append((g["email"], _t(lang, "suspensa_assunto"),
                               _t(lang, "suspensa", nome=g["nome"], empresa=e["nome"], url=_link_assinar(conn, e)),
                               lang))
            rel["suspensas"] += 1
    for e in conn.execute(
        "SELECT * FROM empresas WHERE status IN ('ativa','teste') AND COALESCE(suspender_em,'') != ''"
    ).fetchall():
        quando = _data(e["suspender_em"])
        if quando and hoje >= quando:
            _suspender(conn, e)
            rel["suspensas"] += 1
    conn.commit()
    _enviar(emails)
    return rel


def rotina_planos(intervalo=3600):
    """Thread: uma verificação por dia (confere a cada hora se o dia mudou)."""
    while True:
        try:
            conn = srv.db()
            try:
                dia = hoje_ny().isoformat()
                if srv.config_get(conn, "planos_rotina_dia") != dia:
                    verificar_trials(conn)
                    srv.config_set(conn, "planos_rotina_dia", dia)
                    conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Planos: rotina falhou: %r\n" % exc)
        time.sleep(intervalo)


# ------------------------------------------------------------ visão pública

def plano_publico(p, lang):
    return {
        "codigo": p["codigo"], "nome": _texto(p.get("nome"), lang), "descricao": _texto(p.get("descricao"), lang),
        "preco_mensal": p.get("preco_mensal", 0), "preco_anual": p.get("preco_anual", 0),
        "minutos_voz": p.get("minutos_voz", 0), "numero_exclusivo": bool(p.get("numero_exclusivo")),
        "sms_mes": p.get("sms_mes", 0), "gestores_max": p.get("gestores_max"),
        "recursos": list((p.get("recursos") or {}).get(lang) or (p.get("recursos") or {}).get("pt") or []),
        "destaque": bool(p.get("destaque")),
    }


def catalogo_publico(conn, lang):
    cat = catalogo(conn)
    return {
        "moeda": "USD",
        "trial_dias": cat["trial"]["dias"],
        "trial_minutos": cat["trial"]["minutos"],
        "planos": [plano_publico(p, lang) for p in cat["planos"] if p.get("ativo", True)],
        "addons": {k: cat["addons"].get(k, 0) for k in ("minuto_extra", "numero_extra", "sms_extra")},
        "stripe_ativo": stripe_ativo(conn),
        "assinatura_aberta": assinatura_aberta(conn),
    }


# ------------------------------------------------------------ assinatura pelo site

def _resp(h, status, dados):
    h._json(status, dados)
    return True


def _erro(h, status, msg, lang):
    """Erro já traduzido pelo idioma do formulário (o cabeçalho X-Idioma também vale)."""
    if not h.headers.get("X-Idioma"):
        msg = srv.erros_i18n.traduzir(msg, lang)
    return _resp(h, status, {"erro": msg})


def validar_assinatura(conn, d):
    empresa = (d.get("empresa") or "").strip()
    nome = (d.get("nome") or "").strip()
    email = (d.get("email") or "").strip().lower()
    if not empresa or len(empresa) > 120:
        return "Informe o nome da empresa"
    if not nome or len(nome) > 120:
        return "Informe seu nome"
    if not EMAIL_RE.match(email) or len(email) > 160:
        return "E-mail inválido"
    if len(d.get("senha") or "") < 8:
        return "A senha deve ter ao menos 8 caracteres"
    p = plano(conn, d.get("plano"))
    if not p or not p.get("ativo", True):
        return "Plano inválido"
    if (d.get("ciclo") or "mensal") not in CICLOS:
        return "Ciclo de cobrança inválido"
    if d.get("aceite_termos") is not True:
        return "Aceite os termos de uso para continuar"
    if conn.execute("SELECT 1 FROM gestores WHERE lower(login)=? OR lower(email)=?", (email, email)).fetchone():
        return "Este e-mail já tem uma conta. Entre pelo painel do gestor."
    return None


def assinar(h, conn):
    d = h._body()
    lang = _lang(d.get("idioma") or h.headers.get("X-Idioma"))
    if h._login_bloqueado("assinar"):
        return _erro(h, 429, "Muitas tentativas. Aguarde alguns minutos e tente de novo.", lang)
    h._registrar_falha_login("assinar")  # toda tentativa conta (freia cadastros em massa)
    erro = validar_assinatura(conn, d)
    if erro:
        return _erro(h, 400, erro, lang)
    cat = catalogo(conn)
    p = plano(cat, d["plano"])
    ciclo = d.get("ciclo") or "mensal"
    email = d["email"].strip().lower()
    nome = d["nome"].strip()
    fim = hoje_ny() + timedelta(days=int(cat["trial"]["dias"]))
    eid, slug = srv.empresas.criar_empresa(conn, d["empresa"].strip(), "teste")
    modulos = sorted(m for m in p.get("modulos") or [] if m in srv.MODULOS_DISPONIVEIS)
    valor = p["preco_anual"] if ciclo == "anual" else p["preco_mensal"]
    conn.execute(
        "UPDATE empresas SET plano=?, valor=?, modulos=?, ciclo=?, trial_fim=?, contato_telefone=?, notas=? WHERE id=?",
        (p["codigo"], "%g" % valor, json.dumps(modulos), ciclo, fim.isoformat(),
         (d.get("telefone") or "").strip()[:40], "Assinatura pelo site (%s)" % hoje_ny().isoformat(), eid),
    )
    erro = srv.empresas._criar_gestor(conn, eid, {"nome": nome, "login": email, "senha": d["senha"], "email": email},
                                      is_admin=1)
    if erro:
        conn.rollback()
        return _erro(h, 400, erro, lang)
    g = conn.execute("SELECT * FROM gestores WHERE login=?", (email,)).fetchone()
    if "idioma" in g.keys():
        conn.execute("UPDATE gestores SET idioma=? WHERE id=?", (lang, g["id"]))
    token = secrets.token_urlsafe(24)
    conn.execute("INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)", (token, g["id"]))
    conn.commit()
    try:
        srv.seguranca.registrar(conn, "login", g, "assinatura", h._ip_cliente())
    except Exception:  # noqa: BLE001
        pass
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (eid,)).fetchone()
    resposta = {
        "token": token, "nome": g["nome"], "login": g["login"], "local": g["local"] or "",
        "modulos": srv.empresas.modulos(e), "admin": True, "idioma": lang,
        "empresa": {"nome": e["nome"], "slug": e["slug"]},
        "plano": p["codigo"], "ciclo": ciclo, "trial_fim": fim.isoformat(), "trial_minutos": cat["trial"]["minutos"],
    }
    if stripe_ativo(conn) and float(valor) > 0:
        try:
            resposta["checkout_url"] = criar_checkout(conn, e, p, ciclo, email, h, dias_teste=int(cat["trial"]["dias"]))
        except ErroStripe as exc:
            sys.stderr.write("Planos: checkout falhou para a empresa %s: %s\n" % (eid, exc))
    url = _base_url(conn, h)
    emails = [(email, _t(lang, "boas_vindas_assunto"),
               _t(lang, "boas_vindas", nome=nome, empresa=e["nome"], fim=fim.isoformat(),
                  minutos=cat["trial"]["minutos"], login=email, url=url + "/gestor"), lang)]
    dono = srv.config_get(conn, "dono_email")
    if dono:
        emails.append((dono, "Nova assinatura: %s (%s)" % (e["nome"], p["codigo"]),
                       "Empresa: %s\nLink: %s\nPlano: %s (%s)\nAdministrador: %s <%s>\nTelefone: %s\n"
                       "Teste até: %s\nIdioma: %s\n\n%s/dono"
                       % (e["nome"], e["slug"], p["codigo"], ciclo, nome, email, (d.get("telefone") or "").strip(),
                          fim.isoformat(), lang, url), "pt"))
    _enviar(emails)
    return _resp(h, 200, resposta)


def webhook(h, conn):
    segredo = srv.config_get(conn, "stripe_webhook_secret")
    corpo = getattr(h, "_raw", b"") or b""
    if not assinatura_stripe_valida(corpo, h.headers.get("Stripe-Signature", ""), segredo):
        return _resp(h, 400, {"erro": "Assinatura inválida"})
    try:
        evento = json.loads(corpo.decode("utf-8"))
        if not isinstance(evento, dict):
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        return _resp(h, 400, {"erro": "Assinatura inválida"})
    acao = processar_evento(conn, evento)
    return _resp(h, 200, {"ok": True, "acao": acao})


def rotear_publico(h, method, path, conn):
    if method == "GET" and path == "/api/planos":
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(h.path).query)
        return _resp(h, 200, catalogo_publico(conn, _lang(qs.get("idioma", [""])[0] or h.headers.get("X-Idioma"))))
    if method == "POST" and path == "/api/assinar":
        if not assinatura_aberta(conn):
            return _resp(h, 403, {"erro": "As assinaturas ainda não estão abertas. Fale com a gente."})
        return assinar(h, conn)
    if method == "POST" and path == "/api/stripe/webhook":
        return webhook(h, conn)
    return None


# ------------------------------------------------------------ gestor

def proximo_plano(cat, atual):
    ativos = [p for p in cat["planos"] if p.get("ativo", True)]
    if not ativos:
        return None
    p = plano(cat, atual)
    if not p:
        return next((x for x in ativos if x.get("destaque")), ativos[0])
    maiores = [x for x in ativos if (x.get("minutos_voz") or 0) > (p.get("minutos_voz") or 0)]
    return maiores[0] if maiores else p


def info_gestor(conn, gestor, lang, h=None):
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (gestor["empresa_id"],)).fetchone()
    cat = catalogo(conn)
    p = plano(cat, e["plano"])
    u = uso(conn, e, cat=cat)
    prox = proximo_plano(cat, e["plano"])
    fim = _data(_row_get(e, "trial_fim", ""))
    admin = bool(gestor["is_admin"])
    return {
        "plano": {"codigo": p["codigo"], "nome": _texto(p["nome"], lang), "minutos_voz": p.get("minutos_voz", 0),
                  "preco_mensal": p.get("preco_mensal"), "preco_anual": p.get("preco_anual")} if p else None,
        "status": e["status"], "ciclo": _row_get(e, "ciclo", "mensal"),
        "em_teste": em_teste(e), "trial_fim": fim.isoformat() if fim else "",
        "dias_teste": (fim - hoje_ny()).days if fim and em_teste(e) else None,
        "renovacao": _row_get(e, "pago_ate", ""), "pagamento_status": _row_get(e, "pagamento_status", ""),
        "uso": u, "admin": admin,
        "gestores": dict(zip(("permitido", "usados", "maximo"), limite_gestores(conn, e))),
        "vagas": dict(zip(("permitido", "usados", "maximo"), limite_vagas(conn, e))),
        "upgrade_url": ("/assinar?plano=%s&e=%s" % (urllib.parse.quote(prox["codigo"]), urllib.parse.quote(e["slug"])))
        if (admin and prox) else "",
        "upgrade_plano": _texto(prox["nome"], lang) if prox else "",
        "portal_disponivel": admin and stripe_ativo(conn) and bool(_row_get(e, "stripe_customer", "")),
        "stripe_ativo": stripe_ativo(conn),
    }


def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/plano"):
        return None
    lang = _lang(h.headers.get("X-Idioma") or _row_get(gestor, "idioma", "pt"))
    if method == "GET" and path == "/api/gestor/plano":
        return _resp(h, 200, info_gestor(conn, gestor, lang, h))
    if not gestor["is_admin"]:
        return _resp(h, 403, {"erro": "Apenas o administrador da empresa gerencia a assinatura"})
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (gestor["empresa_id"],)).fetchone()
    if method == "GET" and path == "/api/gestor/plano/portal":
        if not stripe_ativo(conn):
            return _resp(h, 400, {"erro": "Stripe não configurado"})
        if not _row_get(e, "stripe_customer", ""):
            return _resp(h, 400, {"erro": "Esta empresa ainda não tem assinatura no Stripe"})
        try:
            s = stripe(conn, "POST", "/v1/billing_portal/sessions",
                       {"customer": e["stripe_customer"], "return_url": _base_url(conn, h) + "/gestor"})
        except ErroStripe as exc:
            sys.stderr.write("Planos: portal falhou: %s\n" % exc)
            return _resp(h, 502, {"erro": "Não foi possível falar com o Stripe"})
        return _resp(h, 200, {"url": s.get("url", "")})
    if method == "POST" and path == "/api/gestor/plano/checkout":
        d = h._body()
        p = plano(conn, d.get("plano") or e["plano"])
        ciclo = d.get("ciclo") or _row_get(e, "ciclo", "mensal")
        if not p or not p.get("ativo", True):
            return _resp(h, 400, {"erro": "Plano inválido"})
        if ciclo not in CICLOS:
            return _resp(h, 400, {"erro": "Ciclo de cobrança inválido"})
        if not stripe_ativo(conn):
            return _resp(h, 400, {"erro": "Stripe não configurado"})
        try:
            url = criar_checkout(conn, e, p, ciclo, gestor["email"], h)
        except ErroStripe as exc:
            sys.stderr.write("Planos: checkout falhou: %s\n" % exc)
            return _resp(h, 502, {"erro": "Não foi possível falar com o Stripe"})
        return _resp(h, 200, {"checkout_url": url})
    return _resp(h, 404, {"erro": "Rota não encontrada"})


# ------------------------------------------------------------ dono

def _stripe_dono(conn, h):
    chave = srv.config_get(conn, "stripe_secret_key")
    return {
        "configurado": bool(chave), "chave_final": chave[-4:] if chave else "",
        "modo_teste": chave.startswith("sk_test_") if chave else False,
        "webhook_configurado": bool(srv.config_get(conn, "stripe_webhook_secret")),
        "webhook_url": _base_url(conn, h) + "/api/stripe/webhook",
        "precos": precos_stripe(conn),
        "dono_email": srv.config_get(conn, "dono_email"),
    }


def assinatura_aberta(conn):
    """O cadastro público (teste grátis) fica fechado até o dono abrir no painel."""
    return srv.config_get(conn, "assinatura_publica") == "1"


def rotear_dono(h, method, path, conn):
    """Rotas /api/dono/planos* (o guarda do dono já rodou no server.py)."""
    if not path.startswith("/api/dono/planos"):
        return None
    if method == "GET" and path == "/api/dono/planos":
        cat = catalogo(conn)
        pr = premissas(conn)
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(h.path).query)
        mes = qs.get("mes", [""])[0]
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", mes or ""):
            mes = None
        return _resp(h, 200, {
            "catalogo": cat, "premissas": pr, "custos": custos(cat, pr), "uso": painel_uso(conn, mes),
            "stripe": _stripe_dono(conn, h), "modulos_disponiveis": sorted(srv.MODULOS_DISPONIVEIS),
            "assinatura_aberta": assinatura_aberta(conn),
        })
    if method == "POST" and path == "/api/dono/planos/catalogo":
        cat, erro = salvar_catalogo(conn, h._body().get("catalogo"))
        if erro:
            return _resp(h, 400, {"erro": erro})
        return _resp(h, 200, {"ok": True, "catalogo": cat, "custos": custos(cat, premissas(conn))})
    if method == "POST" and path == "/api/dono/planos/restaurar":
        srv.config_set(conn, "planos_catalogo", json.dumps(CATALOGO_PADRAO, ensure_ascii=False))
        conn.commit()
        return _resp(h, 200, {"ok": True, "catalogo": catalogo(conn)})
    if method == "POST" and path == "/api/dono/planos/premissas":
        pr, erro = salvar_premissas(conn, h._body().get("premissas"))
        if erro:
            return _resp(h, 400, {"erro": erro})
        return _resp(h, 200, {"ok": True, "premissas": pr, "custos": custos(catalogo(conn), pr)})
    if method == "POST" and path == "/api/dono/planos/calcular":
        # simulação sem salvar (a tela recalcula enquanto o dono digita)
        d = h._body()
        cat, erro = validar_catalogo(d.get("catalogo")) if d.get("catalogo") else (catalogo(conn), None)
        pr, erro2 = validar_premissas(d.get("premissas") or {}, premissas(conn))
        if erro or erro2:
            return _resp(h, 400, {"erro": erro or erro2})
        return _resp(h, 200, {"custos": custos(cat, pr)})
    if path == "/api/dono/planos/stripe":
        if method == "GET":
            return _resp(h, 200, _stripe_dono(conn, h))
        if method == "POST":
            d = h._body()
            for chave in ("stripe_secret_key", "stripe_webhook_secret"):
                if d.get(chave):
                    srv.config_set(conn, chave, str(d[chave]).strip())
                elif d.get("remover_" + chave):
                    srv.config_set(conn, chave, "")
            if "precos" in d and isinstance(d.get("precos"), dict):
                limpos = {str(k)[:60]: str(v).strip()[:120] for k, v in d["precos"].items() if str(v or "").strip()}
                srv.config_set(conn, "stripe_precos", json.dumps(limpos))
            if "dono_email" in d:
                email = (d.get("dono_email") or "").strip()
                if email and not EMAIL_RE.match(email):
                    return _resp(h, 400, {"erro": "E-mail inválido"})
                srv.config_set(conn, "dono_email", email)
            conn.commit()
            return _resp(h, 200, {"ok": True, "stripe": _stripe_dono(conn, h)})
    if method == "POST" and path == "/api/dono/planos/assinatura":
        aberta = bool(h._body().get("aberta"))
        srv.config_set(conn, "assinatura_publica", "1" if aberta else "")
        conn.commit()
        return _resp(h, 200, {"ok": True, "assinatura_aberta": aberta})
    if method == "POST" and path == "/api/dono/planos/rotina":
        return _resp(h, 200, {"ok": True, "resultado": verificar_trials(conn)})
    m = re.match(r"^/api/dono/planos/empresa/(\d+)$", path)
    if m and method == "POST":
        e = conn.execute("SELECT * FROM empresas WHERE id=?", (int(m.group(1)),)).fetchone()
        if not e:
            return _resp(h, 404, {"erro": "Empresa não encontrada"})
        d = h._body()
        campos = {}
        if "plano" in d:
            codigo = (d.get("plano") or "").strip()
            p = plano(conn, codigo)
            if codigo and not p:
                return _resp(h, 400, {"erro": "Plano inválido"})
            campos["plano"] = codigo
            if p and d.get("aplicar_modulos"):
                campos["modulos"] = json.dumps(sorted(x for x in p.get("modulos") or [] if x in srv.MODULOS_DISPONIVEIS))
        if "ciclo" in d:
            if d.get("ciclo") not in CICLOS:
                return _resp(h, 400, {"erro": "Ciclo de cobrança inválido"})
            campos["ciclo"] = d["ciclo"]
        for chave in ("minutos_extra", "numeros_extra", "gestores_extra", "vagas_extra"):
            if chave in d:
                v = _num(d.get(chave))
                if v is None:
                    return _resp(h, 400, {"erro": "Valor inválido no catálogo"})
                campos[chave] = int(v)
        if "excedente_permitido" in d:
            campos["excedente_permitido"] = 1 if d.get("excedente_permitido") else 0
        if "trial_fim" in d:
            fim = (d.get("trial_fim") or "").strip()
            if fim and not _data(fim):
                return _resp(h, 400, {"erro": "Data inválida (use AAAA-MM-DD)"})
            campos["trial_fim"] = fim
            campos["trial_avisos"] = ""
        _atualizar(conn, e["id"], campos)
        conn.commit()
        return _resp(h, 200, {
            "ok": True, "uso": uso(conn, e["id"]),
            "gestores": dict(zip(("permitido", "usados", "maximo"), limite_gestores(conn, e["id"]))),
            "vagas": dict(zip(("permitido", "usados", "maximo"), limite_vagas(conn, e["id"]))),
        })
    return _resp(h, 404, {"erro": "Rota não encontrada"})
