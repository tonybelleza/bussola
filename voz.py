"""
Módulo Triagem por Voz da Bússola.

A Francisca (agente de voz no ElevenLabs) liga para o candidato logo depois da
inscrição numa vaga cujo cargo tem a triagem por voz ativa. O ElevenLabs extrai
os fatos da conversa (data collection) e este módulo calcula pontos, tier e
resultado, atualiza a candidatura e convida STRONG e GOOD para os testes.

Sem dependências externas: stdlib (urllib, threading, zoneinfo) e SQLite.
O server.py chama ligar(modulo) na inicialização para emprestar as funções de
banco, eventos, e-mail e templates.
"""
import hashlib
import hmac
import json
import re
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover (Python < 3.9)
    ZoneInfo = None

srv = None  # módulo do servidor, injetado por ligar()

# Em testes, um objeto com iniciar/conversa/audio substitui o ElevenLabs real.
GATEWAY_TESTE = None


def ligar(modulo_servidor):
    """Recebe o módulo do servidor e registra os modelos de e-mail do convite."""
    global srv
    srv = modulo_servidor
    srv.TEMPLATES_PADRAO.update(TEMPLATES_VOZ)
    srv.NOMES_TEMPLATES.update(NOMES_TEMPLATES_VOZ)


# ------------------------------------------------------------ vocabulário

OUTCOMES = (
    "QUALIFIED", "NOT_QUALIFIED", "NEEDS_REVIEW", "CALLBACK", "NOT_INTERESTED",
    "VOICEMAIL", "WRONG_NUMBER", "NOT_AVAILABLE", "DO_NOT_CALL",
)
SCORED_OUTCOMES = ("QUALIFIED", "NOT_QUALIFIED", "NEEDS_REVIEW")

# status da triagem por voz em cada candidatura ('' = cargo sem triagem por voz)
STATUS_VOZ = (
    "para_ligar", "ligando", "concluida", "callback", "nao_qualificado",
    "nao_interessado", "correio_voz", "numero_errado", "nao_ligar", "revisar",
)

OUTCOME_STATUS = {
    "QUALIFIED": "concluida",
    "NOT_QUALIFIED": "nao_qualificado",
    "NEEDS_REVIEW": "revisar",
    "CALLBACK": "callback",
    "NOT_INTERESTED": "nao_interessado",
    "WRONG_NUMBER": "numero_errado",
    "DO_NOT_CALL": "nao_ligar",
}

IDIOMAS_LIGACAO = ("es", "en", "pt")
CODIGO_ELEVENLABS = {"es": "es", "en": "en", "pt": "pt-br"}

PRIMEIRAS_FRASES = {
    "es": ("Hola, soy Francisca, la asistente virtual de reclutamiento de Belleza's Home "
           "Services en Hartford. Soy una asistente automatizada, no una persona. "
           "¿Hablo con {{candidate_name}}?"),
    "en": ("Hi, this is Francisca, the AI recruiting assistant for Belleza's Home Services "
           "in Hartford. I'm an automated assistant, not a person. Am I speaking with "
           "{{candidate_name}}?"),
    "pt": ("Oi, aqui é a Francisca, a assistente virtual de recrutamento da Belleza's Home "
           "Services, em Hartford. Sou uma assistente automatizada, não uma pessoa. "
           "Estou falando com {{candidate_name}}?"),
}

CONFIG_PADRAO = {
    "ativo": 1,
    "pausado": 0,
    "fuso": "America/New_York",
    "inicio": "09:00",
    "fim": "19:30",
    "dias": [1, 2, 3, 4, 5, 6],
    "max_tentativas": 3,
    "simultaneas": 1,
    "intervalo_horas": 4,
    "idioma_padrao": "es",
}

# ------------------------------------------------------------ distância

DENTRO_25 = [
    "Hartford", "East Hartford", "West Hartford", "Wethersfield", "Newington", "Rocky Hill",
    "Cromwell", "Glastonbury", "Manchester", "South Windsor", "Windsor", "Windsor Locks",
    "Bloomfield", "Simsbury", "Avon", "Farmington", "Unionville", "Canton", "Granby",
    "East Granby", "Suffield", "Enfield", "East Windsor", "Ellington", "Vernon", "Rockville",
    "Tolland", "Bolton", "Coventry", "Andover", "Hebron", "Marlborough", "Portland",
    "Middletown", "Berlin", "Kensington", "New Britain", "Plainville", "Southington",
    "Bristol", "Burlington", "Meriden", "Colchester", "East Hampton", "Durham", "Middlefield",
    "Columbia", "Somers",
]
DENTRO_40 = [
    "East Haddam", "Haddam", "Hamden", "Niantic", "East Lyme", "Wallingford", "Cheshire",
    "North Haven", "New Haven", "Waterbury", "Wolcott", "Stafford", "Stafford Springs",
    "Willington", "Mansfield", "Storrs", "Lebanon", "Springfield", "West Springfield",
    "Chicopee", "Agawam", "Westfield", "Northampton", "Holyoke", "Longmeadow",
    "East Longmeadow", "Ludlow",
]


def normalizar_cidade(texto):
    t = unicodedata.normalize("NFD", texto or "")
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn").lower()
    t = re.sub(r"[,.]", " ", t)
    t = re.sub(r"\b(ct|connecticut|ma|massachusetts|usa)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


FAIXAS = {}
for _c in DENTRO_40:
    FAIXAS[normalizar_cidade(_c)] = "40mi"
for _c in DENTRO_25:
    FAIXAS[normalizar_cidade(_c)] = "25mi"


def faixa_da_cidade(cidade):
    return FAIXAS.get(normalizar_cidade(cidade)) if cidade else None


# ------------------------------------------------------------ fatos da ligação

_SIM_NAO_INCERTO = ("yes", "no", "unclear")

# campo: (tipo, valores permitidos ou None, descrição para o ElevenLabs)
CAMPOS_FATOS = {
    "candidate_name": ("string", None, "Candidate's name as confirmed on the call."),
    "preferred_language": ("string", ("en", "es", "pt"), "Language the candidate chose or used for most of the call."),
    "outcome": ("string", OUTCOMES, "Final outcome per the agent's closing."),
    "recording_consent": ("boolean", None, "True only if the agent said the call is recorded and the candidate agreed to continue."),
    "license": ("string", _SIM_NAO_INCERTO, "Does the candidate have a valid driver's license?"),
    "own_car": ("string", _SIM_NAO_INCERTO, "Does the candidate have their own car?"),
    "city": ("string", None, "Town or city where the candidate lives."),
    "distance_band": ("string", ("25mi", "40mi", "outside", "unknown"), "Rough distance from Hartford, CT."),
    "weekdays_available": ("integer", None, "How many weekdays (0 to 5) the candidate can work."),
    "days_available": ("string", None, "Weekdays available, in the candidate's words."),
    "saturdays_ok": ("boolean", None, "Open to an occasional Saturday?"),
    "experience_level": ("string", ("two_plus_years", "under_two_or_informal", "none"), "House cleaning experience."),
    "experience": ("string", None, "Short factual summary of the experience."),
    "works_alone": ("string", ("yes", "hesitant", "no"), "Comfortable working solo?"),
    "has_smartphone": ("boolean", None, "Has a smartphone?"),
    "start_timeframe": ("string", ("within_1_week", "within_2_weeks", "later"), "How soon the candidate could start."),
    "start_date": ("string", None, "Start availability in the candidate's words."),
    "pets": ("string", ("comfortable", "some_or_no"), "Comfortable with pets?"),
    "standards": ("string", ("accepted", "hesitant_or_objects"), "Reaction to the standards."),
    "text_phone": ("string", None, "Phone confirmed for texts."),
    "ok_to_text": ("boolean", None, "Agreed to receive texts?"),
    "interview_windows": ("string", None, "Days and times offered for a talk with the hiring manager."),
    "candidate_questions": ("string", None, "Questions the candidate asked."),
    "notes": ("string", None, "Short factual notes."),
}


def _valor_valido(tipo, permitidos, valor):
    if valor is None:
        return True, None
    if tipo == "boolean":
        if isinstance(valor, bool):
            return True, valor
        if isinstance(valor, str) and valor.lower() in ("true", "false"):
            return True, valor.lower() == "true"
        return False, None
    if tipo == "integer":
        if isinstance(valor, bool):
            return False, None
        if isinstance(valor, (int, float)) and float(valor).is_integer():
            valor = int(valor)
        elif isinstance(valor, str) and re.fullmatch(r"\d+", valor.strip()):
            valor = int(valor.strip())
        else:
            return False, None
        return (0 <= valor <= 5), (valor if 0 <= valor <= 5 else None)
    if not isinstance(valor, str):
        return False, None
    if permitidos and valor not in permitidos:
        return False, None
    return True, valor


def para_e164(telefone):
    """Número dos EUA em E.164 (+1XXXXXXXXXX) ou None. Aceita '+1 8605550101',
    '(860) 555-0101' e '18605550101'."""
    if not telefone:
        return None
    digitos = re.sub(r"\D", "", telefone)
    if len(digitos) == 10:
        return "+1" + digitos
    if len(digitos) == 11 and digitos.startswith("1"):
        return "+" + digitos
    return None


def extrair_fatos(conversa):
    """Resultados do data collection para um dicionário de fatos. Valor ausente ou
    inválido vira None (nunca é adivinhado) e é listado em `invalidos`."""
    resultados = ((conversa.get("analysis") or {}).get("data_collection_results")) or {}
    fatos, invalidos = {}, []
    for campo, (tipo, permitidos, _desc) in CAMPOS_FATOS.items():
        bruto = (resultados.get(campo) or {}).get("value")
        if isinstance(bruto, str) and bruto.strip() in ("", "null", "None"):
            bruto = None
        ok, valor = _valor_valido(tipo, permitidos, bruto)
        fatos[campo] = valor if ok else None
        if not ok:
            invalidos.append("%s=%s" % (campo, json.dumps(bruto, ensure_ascii=False)))
    if fatos.get("text_phone"):
        e164 = para_e164(fatos["text_phone"])
        if not e164:
            invalidos.append("text_phone=%s" % json.dumps(fatos["text_phone"]))
        fatos["text_phone"] = e164
    return fatos, invalidos


def limpar_marcas_de_voz(texto):
    """Remove marcas expressivas como '[calm]' que o modelo de voz escreve na fala."""
    return re.sub(r"\[[a-zA-Z_ ]{2,20}\]\s*", "", texto or "").strip()


# ------------------------------------------------------------ scorecard

def tier_do_score(score):
    if score >= 75:
        return "STRONG"
    if score >= 55:
        return "GOOD"
    if score >= 40:
        return "REVIEW"
    return "LOW"


def pontuar(fatos):
    """Scorecard determinístico. Mesmas regras do prompt da Francisca:
    gates (carteira e carro), pontos (máximo 100), tier e resultado final."""
    faixa = faixa_da_cidade(fatos.get("city")) or fatos.get("distance_band") or "unknown"
    gates = {"license": fatos.get("license") == "yes", "vehicle": fatos.get("own_car") == "yes"}
    base = {"faixa": faixa, "gates": gates, "score": None, "tier": None, "pontos": None}
    outcome = fatos.get("outcome")

    if not outcome:
        return dict(base, outcome="NEEDS_REVIEW", motivos=["no_outcome"])
    if outcome not in SCORED_OUTCOMES:
        return dict(base, outcome=outcome, motivos=[])
    if fatos.get("license") == "no" or fatos.get("own_car") == "no":
        return dict(base, outcome="NOT_QUALIFIED", motivos=[])

    motivos = []
    if fatos.get("license") != "yes":
        motivos.append("license_unclear")
    if fatos.get("own_car") != "yes":
        motivos.append("car_unclear")
    if outcome == "NOT_QUALIFIED":
        motivos.append("not_qualified_without_gate")

    def faltou(item):
        motivos.append("missing:" + item)
        return 0

    dias = fatos.get("weekdays_available")
    disponibilidade = faltou("availability") if dias is None else (25 if dias >= 5 else 15 if dias == 4 else 5)

    exp = fatos.get("experience_level")
    experiencia = faltou("experience") if exp is None else {"two_plus_years": 20, "under_two_or_informal": 10, "none": 5}[exp]

    if faixa == "25mi":
        localizacao = 15
    elif faixa == "40mi":
        localizacao = 10
    else:
        localizacao = 0
        motivos.append("outside_area" if faixa == "outside" else "location_unknown")

    sozinho = fatos.get("works_alone")
    trabalha_sozinho = faltou("works_alone") if sozinho is None else {"yes": 10, "hesitant": 3, "no": 0}[sozinho]

    if fatos.get("has_smartphone") is None:
        smartphone = faltou("smartphone")
    elif fatos["has_smartphone"]:
        smartphone = 10
    else:
        smartphone = 0
        motivos.append("no_smartphone")

    prazo = fatos.get("start_timeframe")
    inicio = faltou("start_date") if prazo is None else {"within_1_week": 10, "within_2_weeks": 7, "later": 3}[prazo]

    pets = faltou("pets") if fatos.get("pets") is None else (5 if fatos["pets"] == "comfortable" else 0)

    if fatos.get("standards") is None:
        padroes = faltou("standards")
    elif fatos["standards"] == "accepted":
        padroes = 5
    else:
        padroes = 0
        motivos.append("standards_objection")

    pontos = {
        "availability": disponibilidade, "experience": experiencia, "location": localizacao,
        "works_alone": trabalha_sozinho, "smartphone": smartphone, "start_date": inicio,
        "pets": pets, "standards": padroes,
    }
    score = sum(pontos.values())
    return dict(
        base, outcome="NEEDS_REVIEW" if motivos else "QUALIFIED",
        score=score, tier=tier_do_score(score), pontos=pontos, motivos=motivos,
    )


# ------------------------------------------------------------ regras de ligação

def _agora_utc():
    return datetime.now(timezone.utc)


def _sql(dt):
    """Data em UTC no mesmo formato de datetime('now') do SQLite."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _de_sql(texto):
    if not texto:
        return None
    return datetime.strptime(texto[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _minutos(hhmm):
    h, m = (hhmm or "00:00").split(":")
    return int(h) * 60 + int(m)


def _zona(cfg):
    try:
        return ZoneInfo(cfg.get("fuso") or "America/New_York")
    except Exception:  # noqa: BLE001
        return ZoneInfo("America/New_York")


def dentro_da_janela(agora, cfg):
    local = agora.astimezone(_zona(cfg))
    if local.isoweekday() not in cfg["dias"]:
        return False
    m = local.hour * 60 + local.minute
    return _minutos(cfg["inicio"]) <= m < _minutos(cfg["fim"])


def proxima_tentativa(agora, cfg):
    """Pelo menos intervalo_horas depois, empurrada para a próxima abertura da
    janela quando cair fora dela (outro turno ou outro dia)."""
    zona = _zona(cfg)
    t = agora.astimezone(zona) + timedelta(hours=cfg["intervalo_horas"])
    ini = _minutos(cfg["inicio"])
    fim = _minutos(cfg["fim"])
    for _ in range(14):
        m = t.hour * 60 + t.minute
        if t.isoweekday() in cfg["dias"] and ini <= m < fim:
            return t.astimezone(timezone.utc)
        abertura = t.replace(hour=ini // 60, minute=ini % 60, second=0, microsecond=0)
        t = abertura if (m < ini and t.isoweekday() in cfg["dias"]) else abertura + timedelta(days=1)
        if t.isoweekday() in cfg["dias"]:
            return t.astimezone(timezone.utc)
    return t.astimezone(timezone.utc)


def motivo_bloqueio(c, cfg, agora, manual=False):
    """Código do motivo pelo qual não se pode ligar agora, ou None.
    `c` precisa de: voz_status, voz_outcome, telefone, voz_tentativas, voz_proxima, anonimizado."""
    if c["anonimizado"]:
        return "anonymized"
    if c["voz_status"] == "nao_ligar":
        return "do_not_call"
    if c["voz_outcome"] in ("DO_NOT_CALL", "NOT_INTERESTED"):
        return "blocked_outcome"
    if not para_e164(c["telefone"]):
        return "invalid_phone"
    if c["voz_status"] == "ligando":
        return "in_call"
    if (c["voz_tentativas"] or 0) >= cfg["max_tentativas"]:
        return "attempts_exhausted"
    if manual:
        return None
    if not cfg["ativo"]:
        return "disabled"
    if cfg["pausado"]:
        return "paused"
    if c["voz_status"] != "para_ligar":
        return "wrong_status"
    proxima = _de_sql(c["voz_proxima"])
    if proxima and proxima > agora:
        return "waiting_retry"
    if not dentro_da_janela(agora, cfg):
        return "outside_window"
    return None


def transicao(outcome, tentativas, max_tentativas):
    """(novo status, tentar de novo?, nota). Correio de voz, sem resposta e
    'não disponível' tentam de novo até acabarem as tentativas."""
    direto = OUTCOME_STATUS.get(outcome) if outcome else None
    if direto:
        return direto, False, None
    if tentativas >= max_tentativas:
        nota = "voicemail_exhausted" if outcome == "VOICEMAIL" else "no_answer_exhausted"
        return "correio_voz", False, nota
    return "para_ligar", True, None


# ------------------------------------------------------------ banco

def init_voz(c):
    """Tabelas e colunas do módulo. Chamado dentro de init_db() com o cursor aberto."""
    c.execute(
        "CREATE TABLE IF NOT EXISTS voz_config ("
        " local TEXT PRIMARY KEY,"  # '' = padrão para todos os locais
        " dados TEXT NOT NULL DEFAULT '{}',"
        " atualizado_em TEXT DEFAULT (datetime('now')))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS voz_chamadas ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " candidatura_id INTEGER NOT NULL REFERENCES candidaturas(id) ON DELETE CASCADE,"
        " candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,"
        " conversation_id TEXT UNIQUE,"
        " call_sid TEXT DEFAULT '',"
        " status TEXT NOT NULL DEFAULT 'iniciando',"
        " idioma TEXT DEFAULT 'es',"
        " disparada_por TEXT DEFAULT '',"
        " iniciada_em TEXT DEFAULT (datetime('now')),"
        " terminada_em TEXT DEFAULT '',"
        " duracao INTEGER,"
        " transcricao TEXT DEFAULT '[]',"
        " fatos TEXT DEFAULT '',"
        " resultado TEXT DEFAULT '',"
        " invalidos TEXT DEFAULT '[]',"
        " resumo TEXT DEFAULT '',"
        " tem_audio INTEGER DEFAULT 0,"
        " erro TEXT DEFAULT '')"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_voz_chamadas_status ON voz_chamadas(status)")
    colunas = {r[1] for r in c.execute("PRAGMA table_info(candidaturas)").fetchall()}
    for nome, tipo in (
        ("voz_status", "TEXT DEFAULT ''"),
        ("voz_tentativas", "INTEGER DEFAULT 0"),
        ("voz_ultima", "TEXT DEFAULT ''"),
        ("voz_proxima", "TEXT DEFAULT ''"),
        ("voz_outcome", "TEXT DEFAULT ''"),
        ("voz_score", "INTEGER"),
        ("voz_tier", "TEXT DEFAULT ''"),
        ("voz_resultado", "TEXT DEFAULT ''"),
        ("voz_convite_enviado", "INTEGER DEFAULT 0"),
    ):
        if nome not in colunas:
            c.execute("ALTER TABLE candidaturas ADD COLUMN %s %s" % (nome, tipo))
    colunas = {r[1] for r in c.execute("PRAGMA table_info(cargos)").fetchall()}
    if "voz_ativa" not in colunas:
        c.execute("ALTER TABLE cargos ADD COLUMN voz_ativa INTEGER DEFAULT 0")
        c.execute("ALTER TABLE cargos ADD COLUMN peso_voz REAL DEFAULT 0.30")
    colunas = {r[1] for r in c.execute("PRAGMA table_info(candidatos)").fetchall()}
    if "idioma" not in colunas:
        c.execute("ALTER TABLE candidatos ADD COLUMN idioma TEXT DEFAULT ''")


def chave_empresa(empresa_id):
    return "empresa:%d" % int(empresa_id) if empresa_id else ""


def config_empresa(conn, empresa_id):
    """Regras da empresa, herdando do padrão da plataforma ('') e dos valores de fábrica."""
    cfg = dict(CONFIG_PADRAO)
    padrao = conn.execute("SELECT dados FROM voz_config WHERE local=''").fetchone()
    if padrao:
        cfg.update(json.loads(padrao["dados"] or "{}"))
    if empresa_id:
        r = conn.execute("SELECT dados FROM voz_config WHERE local=?", (chave_empresa(empresa_id),)).fetchone()
        if r:
            cfg.update(json.loads(r["dados"] or "{}"))
    return cfg


def validar_config(d):
    """Aceita só campos conhecidos e valores sãos; devolve (dados, erro)."""
    saida = {}
    for chave in ("ativo", "pausado"):
        if chave in d:
            saida[chave] = 1 if d[chave] else 0
    if "fuso" in d:
        try:
            ZoneInfo(str(d["fuso"]))
        except Exception:  # noqa: BLE001
            return None, "invalid_timezone"
        saida["fuso"] = str(d["fuso"])
    for chave in ("inicio", "fim"):
        if chave in d:
            if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", str(d[chave])):
                return None, "invalid_time"
            saida[chave] = str(d[chave])
    if "dias" in d:
        dias = sorted({int(x) for x in (d["dias"] or []) if str(x).isdigit() and 1 <= int(x) <= 7})
        if not dias:
            return None, "invalid_days"
        saida["dias"] = dias
    for chave, minimo, maximo in (("max_tentativas", 1, 10), ("simultaneas", 1, 5), ("intervalo_horas", 1, 72)):
        if chave in d:
            try:
                v = int(d[chave])
            except (TypeError, ValueError):
                return None, "invalid_number"
            if not minimo <= v <= maximo:
                return None, "invalid_number"
            saida[chave] = v
    if "idioma_padrao" in d:
        if d["idioma_padrao"] not in IDIOMAS_LIGACAO:
            return None, "invalid_language"
        saida["idioma_padrao"] = d["idioma_padrao"]
    return saida, None


def salvar_config(conn, empresa_id, novos):
    local = chave_empresa(empresa_id)
    atual = conn.execute("SELECT dados FROM voz_config WHERE local=?", (local,)).fetchone()
    dados = json.loads(atual["dados"]) if atual else {}
    dados.update(novos)
    conn.execute(
        "INSERT INTO voz_config (local, dados, atualizado_em) VALUES (?,?,datetime('now'))"
        " ON CONFLICT(local) DO UPDATE SET dados=excluded.dados, atualizado_em=excluded.atualizado_em",
        (local, json.dumps(dados)),
    )


def nova_candidatura(conn, candidato_id, vaga_id):
    """Chamado logo depois de criar uma candidatura: entra na fila de ligação se o
    cargo da vaga tiver a triagem por voz ativa."""
    r = conn.execute(
        "SELECT ca.id, g.voz_ativa FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
        " JOIN cargos g ON g.id=v.cargo_id WHERE ca.candidato_id=? AND ca.vaga_id=?",
        (candidato_id, vaga_id),
    ).fetchone()
    if r and r["voz_ativa"]:
        conn.execute("UPDATE candidaturas SET voz_status='para_ligar' WHERE id=?", (r["id"],))
        srv.registrar_evento(conn, candidato_id, "voz", "Entrou na fila da triagem por voz")


def anonimizar(conn, candidato_id):
    """LGPD: apaga telefone, transcrições e fatos da triagem por voz."""
    conn.execute("UPDATE candidatos SET telefone='' WHERE id=?", (candidato_id,))
    conn.execute(
        "UPDATE voz_chamadas SET transcricao='[]', fatos='', resumo='', call_sid=''"
        " WHERE candidato_id=?", (candidato_id,),
    )
    conn.execute(
        "UPDATE candidaturas SET voz_status=CASE WHEN voz_status IN ('para_ligar','ligando')"
        " THEN 'nao_ligar' ELSE voz_status END WHERE candidato_id=?", (candidato_id,),
    )


def voz_para_match(conn, candidato_id, cargo_id):
    """Score da última triagem por voz do candidato numa vaga deste cargo, com o
    peso configurado no cargo. None quando não houver."""
    r = conn.execute(
        "SELECT ca.voz_score, g.peso_voz, g.voz_ativa FROM candidaturas ca"
        " JOIN vagas v ON v.id=ca.vaga_id JOIN cargos g ON g.id=v.cargo_id"
        " WHERE ca.candidato_id=? AND v.cargo_id=? AND ca.voz_score IS NOT NULL"
        " ORDER BY ca.atualizado_em DESC LIMIT 1",
        (candidato_id, cargo_id),
    ).fetchone()
    if not r or not r["voz_ativa"] or not r["peso_voz"]:
        return None
    return {"pct": int(r["voz_score"]), "peso": float(r["peso_voz"])}


# ------------------------------------------------------------ ElevenLabs

class ElevenLabs:
    API = "https://api.elevenlabs.io/v1/convai"

    def __init__(self, api_key, agent_id, phone_number_id):
        self.api_key = api_key
        self.agent_id = agent_id
        self.phone_number_id = phone_number_id

    def _req(self, metodo, caminho, corpo=None, binario=False):
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        req = urllib.request.Request(
            self.API + caminho, data=dados, method=metodo,
            headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                bruto = resp.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError("ElevenLabs %s %s: HTTP %s %s" % (
                metodo, caminho, exc.code, exc.read()[:300].decode("utf-8", "replace")))
        return bruto if binario else json.loads(bruto.decode("utf-8"))

    def iniciar(self, telefone, nome, idioma, candidato_id):
        r = self._req("POST", "/twilio/outbound-call", {
            "agent_id": self.agent_id,
            "agent_phone_number_id": self.phone_number_id,
            "to_number": telefone,
            "call_recording_enabled": True,
            "conversation_initiation_client_data": {
                "user_id": str(candidato_id),
                "dynamic_variables": {"candidate_name": nome},
                "conversation_config_override": {"agent": {
                    "language": CODIGO_ELEVENLABS[idioma],
                    "first_message": PRIMEIRAS_FRASES[idioma],
                }},
            },
        })
        if not r.get("success") or not r.get("conversation_id"):
            raise RuntimeError("Ligação não iniciada: %s" % r.get("message"))
        return r["conversation_id"], r.get("callSid") or ""

    def conversa(self, conversation_id):
        return self._req("GET", "/conversations/" + conversation_id)

    def audio(self, conversation_id):
        return self._req("GET", "/conversations/%s/audio" % conversation_id, binario=True)


def gateway(conn):
    """O ElevenLabs configurado em Integrações (ou o falso dos testes)."""
    if GATEWAY_TESTE is not None:
        return GATEWAY_TESTE
    chave = srv.config_get(conn, "elevenlabs_api_key")
    agente = srv.config_get(conn, "elevenlabs_agent_id")
    numero = srv.config_get(conn, "elevenlabs_phone_number_id")
    if not (chave and agente and numero):
        return None
    return ElevenLabs(chave, agente, numero)


def assinatura_valida(corpo_bruto, cabecalho, segredo, agora=None, tolerancia=1800):
    """Confere o cabeçalho ElevenLabs-Signature ('t=<unix>,v0=<hex>'), HMAC-SHA256
    de '<t>.<corpo>' com o segredo do webhook."""
    if not cabecalho or not segredo:
        return False
    partes = dict(p.strip().split("=", 1) for p in cabecalho.split(",") if "=" in p)
    try:
        t = int(partes.get("t", ""))
    except ValueError:
        return False
    agora = int(time.time()) if agora is None else agora
    if abs(agora - t) > tolerancia or not partes.get("v0"):
        return False
    esperado = hmac.new(segredo.encode("utf-8"), ("%d." % t).encode("utf-8") + corpo_bruto,
                        hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, partes["v0"])


# ------------------------------------------------------------ ciclo da ligação

_SQL_CANDIDATURA = (
    "SELECT ca.*, c.nome, c.email, c.telefone, c.idioma, c.anonimizado, c.local AS cand_local,"
    " c.token, c.empresa_id AS empresa_id, v.titulo AS vaga_titulo, v.local AS vaga_local, v.cargo_id,"
    " g.voz_ativa, g.nome AS cargo_nome"
    " FROM candidaturas ca JOIN candidatos c ON c.id=ca.candidato_id"
    " JOIN vagas v ON v.id=ca.vaga_id JOIN cargos g ON g.id=v.cargo_id"
)

_trava_tick = threading.Lock()


class ErroVoz(Exception):
    def __init__(self, codigo, detalhe=""):
        Exception.__init__(self, "%s: %s" % (codigo, detalhe) if detalhe else codigo)
        self.codigo = codigo


def local_da_candidatura(row):
    return (row["vaga_local"] or row["cand_local"] or "").strip()


def visivel_para(gestor, row):
    """A candidatura é da empresa do gestor e da unidade que ele enxerga."""
    return srv.gestor_ve_candidato(gestor, {"empresa_id": row["empresa_id"], "local": row["cand_local"]})


def iniciar_ligacao(conn, candidatura_id, disparada_por, manual=False):
    """Liga para o candidato desta candidatura. Lança ErroVoz com um código."""
    row = conn.execute(_SQL_CANDIDATURA + " WHERE ca.id=?", (candidatura_id,)).fetchone()
    if not row:
        raise ErroVoz("not_found")
    cfg = config_empresa(conn, row["empresa_id"])
    motivo = motivo_bloqueio(row, cfg, _agora_utc(), manual)
    if motivo:
        raise ErroVoz(motivo)
    gw = gateway(conn)
    if gw is None:
        raise ErroVoz("not_configured")

    # reserva a candidatura (nenhum outro tick disca para a mesma pessoa)
    cur = conn.execute(
        "UPDATE candidaturas SET voz_status='ligando', voz_tentativas=voz_tentativas+1,"
        " voz_ultima=datetime('now'), atualizado_em=datetime('now')"
        " WHERE id=? AND voz_status=?",
        (row["id"], row["voz_status"]),
    )
    if cur.rowcount == 0:
        raise ErroVoz("status_changed")
    idioma = row["idioma"] if row["idioma"] in IDIOMAS_LIGACAO else cfg["idioma_padrao"]
    chamada_id = conn.execute(
        "INSERT INTO voz_chamadas (candidatura_id, candidato_id, idioma, disparada_por)"
        " VALUES (?,?,?,?)",
        (row["id"], row["candidato_id"], idioma, disparada_por),
    ).lastrowid
    conn.commit()  # libera o SQLite antes da chamada de rede

    telefone = para_e164(row["telefone"])
    try:
        conversation_id, call_sid = gw.iniciar(telefone, row["nome"], idioma, row["candidato_id"])
    except Exception as exc:  # noqa: BLE001
        conn.execute(
            "UPDATE voz_chamadas SET status='falhou', erro=?, terminada_em=datetime('now') WHERE id=?",
            (str(exc)[:500], chamada_id),
        )
        # ligação que nem começou não conta como tentativa
        conn.execute(
            "UPDATE candidaturas SET voz_status=?, voz_tentativas=? WHERE id=?",
            (row["voz_status"], row["voz_tentativas"] or 0, row["id"]),
        )
        srv.registrar_evento(conn, row["candidato_id"], "voz", "Falha ao iniciar a ligação")
        conn.commit()
        raise ErroVoz("start_failed", str(exc))

    conn.execute(
        "UPDATE voz_chamadas SET conversation_id=?, call_sid=?, status='em_andamento' WHERE id=?",
        (conversation_id, call_sid, chamada_id),
    )
    srv.registrar_evento(
        conn, row["candidato_id"], "voz",
        "Ligação da triagem por voz iniciada (%s, tentativa %d)" % (idioma, (row["voz_tentativas"] or 0) + 1),
        disparada_por,
    )
    conn.commit()
    return chamada_id


def processar_conversa(conn, conversation_id):
    """Busca a conversa no ElevenLabs e aplica o resultado. Idempotente.
    Devolve False enquanto a conversa ainda não terminou."""
    chamada = conn.execute(
        "SELECT * FROM voz_chamadas WHERE conversation_id=?", (conversation_id,)
    ).fetchone()
    if not chamada or chamada["status"] in ("concluida", "falhou"):
        return True
    gw = gateway(conn)
    if gw is None:
        return False
    conversa = gw.conversa(conversation_id)
    status = conversa.get("status")
    if status not in ("done", "failed"):
        if status == "processing" and chamada["status"] != "processando":
            conn.execute("UPDATE voz_chamadas SET status='processando' WHERE id=?", (chamada["id"],))
            conn.commit()
        return False
    aplicar_resultado(conn, chamada, conversa)
    return True


def falha_de_inicio(conn, conversation_id, motivo):
    """Ocupado, não atendeu ou erro de conexão antes de alguém atender."""
    chamada = conn.execute(
        "SELECT * FROM voz_chamadas WHERE conversation_id=?", (conversation_id,)
    ).fetchone()
    if not chamada or chamada["status"] in ("concluida", "falhou"):
        return
    aplicar_resultado(conn, chamada, {"status": "failed", "transcript": []}, erro=motivo)


def aplicar_resultado(conn, chamada, conversa, erro=""):
    row = conn.execute(_SQL_CANDIDATURA + " WHERE ca.id=?", (chamada["candidatura_id"],)).fetchone()
    if not row:
        return
    cfg = config_empresa(conn, row["empresa_id"])
    falas = [t for t in (conversa.get("transcript") or []) if (t.get("message") or "").strip()]
    candidato_falou = any(t.get("role") == "user" for t in falas)
    fatos, invalidos = extrair_fatos(conversa)
    atendeu = conversa.get("status") == "done" and (candidato_falou or fatos.get("outcome") == "VOICEMAIL")
    resultado = pontuar(fatos) if atendeu else None
    novo_status, tentar_de_novo, nota = transicao(
        resultado["outcome"] if resultado else None, row["voz_tentativas"] or 0, cfg["max_tentativas"]
    )
    transcricao = [
        {"papel": t.get("role"), "texto": limpar_marcas_de_voz(t.get("message")),
         "t": int(round(t.get("time_in_call_secs") or 0))}
        for t in falas
    ]
    meta = conversa.get("metadata") or {}

    conn.execute(
        "UPDATE voz_chamadas SET status=?, terminada_em=datetime('now'), duracao=?, transcricao=?,"
        " fatos=?, resultado=?, invalidos=?, resumo=?, tem_audio=?, erro=? WHERE id=?",
        (
            "concluida" if conversa.get("status") == "done" else "falhou",
            meta.get("call_duration_secs"),
            json.dumps(transcricao, ensure_ascii=False),
            json.dumps(fatos, ensure_ascii=False) if atendeu else "",
            json.dumps(resultado, ensure_ascii=False) if resultado else "",
            json.dumps(invalidos, ensure_ascii=False),
            ((conversa.get("analysis") or {}).get("transcript_summary") or "")[:4000],
            1 if conversa.get("has_audio") else 0,
            erro or ("" if atendeu else "no_answer"),
            chamada["id"],
        ),
    )
    pontuou = resultado and resultado["score"] is not None
    conn.execute(
        "UPDATE candidaturas SET voz_status=?, voz_proxima=?, voz_outcome=?, voz_score=?,"
        " voz_tier=?, voz_resultado=?, atualizado_em=datetime('now') WHERE id=?",
        (
            novo_status,
            _sql(proxima_tentativa(_agora_utc(), cfg)) if tentar_de_novo else "",
            resultado["outcome"] if resultado else (row["voz_outcome"] or ""),
            resultado["score"] if pontuou else row["voz_score"],
            resultado["tier"] if pontuou else (row["voz_tier"] or ""),
            json.dumps(dict(resultado, fatos=fatos), ensure_ascii=False) if pontuou else (row["voz_resultado"] or ""),
            row["id"],
        ),
    )
    if atendeu and fatos.get("preferred_language") in IDIOMAS_LIGACAO:
        conn.execute("UPDATE candidatos SET idioma=? WHERE id=?", (fatos["preferred_language"], row["candidato_id"]))

    texto = "Triagem por voz: %s" % (resultado["outcome"] if resultado else "sem resposta")
    if pontuou:
        texto += " (%s, %d pontos)" % (resultado["tier"], resultado["score"])
    if nota:
        texto += " [%s]" % nota
    srv.registrar_evento(conn, row["candidato_id"], "voz", texto)

    destaque = pontuou and resultado["outcome"] == "QUALIFIED" and resultado["tier"] in ("STRONG", "GOOD")
    if destaque and row["etapa"] == "inscrito":
        conn.execute(
            "UPDATE candidaturas SET etapa='avaliacoes', atualizado_em=datetime('now') WHERE id=?",
            (row["id"],),
        )
        srv.registrar_evento(
            conn, row["candidato_id"], "etapa",
            "Vaga %s: movido para %s (triagem por voz)" % (row["vaga_titulo"], srv.NOMES_ETAPAS["avaliacoes"]),
        )
    conn.commit()  # grava tudo antes do e-mail (I/O de rede)

    if destaque and not row["voz_convite_enviado"]:
        enviar_convite(conn, row, fatos.get("preferred_language") or row["idioma"] or cfg["idioma_padrao"])
        avisar_gestores(conn, row, resultado, fatos)


def enviar_convite(conn, row, idioma):
    """Convida o candidato STRONG ou GOOD para os testes, no idioma da ligação."""
    if not (row["email"] or "").strip() or not srv.config_get(conn, "smtp_host"):
        return
    idioma = idioma if idioma in IDIOMAS_LIGACAO else "es"
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (row["candidato_id"],)).fetchone()
    variaveis = srv.variaveis_candidato(conn, cand)
    variaveis["vaga"] = row["vaga_titulo"]
    variaveis["nome"] = (row["nome"] or "").split(" ")[0] or row["nome"]
    modelo = srv.templates_email(conn, row["empresa_id"])["voz_convite_" + idioma]
    ok, msg = srv.enviar_email(
        conn, row["email"], srv.renderizar(modelo["assunto"], variaveis),
        srv.renderizar(modelo["corpo"], variaveis),
    )
    if ok:
        conn.execute("UPDATE candidaturas SET voz_convite_enviado=1 WHERE id=?", (row["id"],))
    srv.registrar_evento(
        conn, row["candidato_id"], "email",
        "Convite para os testes enviado (%s)" % idioma if ok else "Falha ao enviar convite: %s" % msg,
    )
    conn.commit()


def avisar_gestores(conn, row, resultado, fatos):
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (row["candidato_id"],)).fetchone()
    srv.notificar_gestores(
        conn, cand,
        "Triagem por voz %s: %s" % (resultado["tier"], row["nome"]),
        ("%s passou na triagem por voz da vaga %s.\n\nTier: %s (%d pontos)\nCidade: %s\n"
         "Janelas para entrevista: %s\n\nO convite para os testes já foi enviado. "
         "Veja a ligação completa no painel do gestor.")
        % (row["nome"], row["vaga_titulo"], resultado["tier"], resultado["score"],
           fatos.get("city") or "-", fatos.get("interview_windows") or "-"),
    )
    conn.commit()


def reconciliar(conn, minutos=3):
    """Confere com o ElevenLabs as ligações abertas há mais de `minutos`
    (cobre webhooks perdidos e servidores sem endereço público)."""
    abertas = conn.execute(
        "SELECT conversation_id FROM voz_chamadas WHERE status IN ('em_andamento','processando')"
        " AND conversation_id IS NOT NULL AND iniciada_em <= datetime('now', ?)",
        ("-%d minutes" % minutos,),
    ).fetchall()
    fechadas = 0
    for a in abertas:
        try:
            if processar_conversa(conn, a["conversation_id"]):
                fechadas += 1
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Voz: reconciliação falhou: %r\n" % exc)
    return fechadas


def tick(conn, agora=None, empresa_id=None):
    """Uma rodada da fila: reconcilia e liga para os próximos elegíveis, por empresa.
    Com empresa_id, só aquela empresa (botão "Rodar fila agora" do gestor)."""
    if not _trava_tick.acquire(blocking=False):
        return {"ocupado": True}
    try:
        agora = agora or _agora_utc()
        relatorio = {"reconciliadas": reconciliar(conn), "iniciadas": 0, "locais": {}}
        if gateway(conn) is None:
            relatorio["pulado"] = "not_configured"
            return relatorio
        filtro = " AND c.empresa_id=?" if empresa_id else ""
        candidatas = conn.execute(
            _SQL_CANDIDATURA + " JOIN empresas e ON e.id=c.empresa_id"
            " WHERE ca.voz_status='para_ligar' AND g.voz_ativa=1 AND e.status IN ('ativa','teste')"
            " AND e.modulos LIKE '%\"voz\"%'"
            " AND c.anonimizado=0 AND (ca.voz_proxima='' OR ca.voz_proxima IS NULL OR ca.voz_proxima<=?)"
            + filtro + " ORDER BY ca.voz_proxima, ca.criado_em",
            (_sql(agora),) + ((empresa_id,) if empresa_id else ()),
        ).fetchall()
        em_curso = {}
        for r in conn.execute(
            "SELECT c.empresa_id AS eid, COUNT(*) AS n FROM voz_chamadas vc"
            " JOIN candidatos c ON c.id=vc.candidato_id"
            " WHERE vc.status IN ('iniciando','em_andamento') GROUP BY c.empresa_id"
        ).fetchall():
            em_curso[r["eid"]] = r["n"]
        for row in candidatas:
            chave = row["empresa_id"]
            cfg = config_empresa(conn, chave)
            if em_curso.get(chave, 0) >= cfg["simultaneas"]:
                continue
            motivo = motivo_bloqueio(row, cfg, agora)
            if motivo:
                relatorio["locais"].setdefault(str(chave), motivo)
                continue
            try:
                iniciar_ligacao(conn, row["id"], "fila")
                em_curso[chave] = em_curso.get(chave, 0) + 1
                relatorio["iniciadas"] += 1
            except ErroVoz as exc:
                sys.stderr.write("Voz: candidatura %s pulada: %s\n" % (row["id"], exc))
        return relatorio
    finally:
        _trava_tick.release()


def rotina_voz(intervalo=60):
    """Thread da fila: uma rodada por minuto."""
    while True:
        try:
            conn = srv.db()
            try:
                tick(conn)
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Voz: rotina falhou: %r\n" % exc)
        time.sleep(intervalo)


# ------------------------------------------------------------ e-mail do convite

TEMPLATES_VOZ = {
    "voz_convite_es": {
        "assunto": "Siguiente paso: {vaga}",
        "corpo": ("¡Hola, {nome}!\n\nGracias por hablar con Francisca. Usted cumple los "
                  "requisitos básicos para la vacante \"{vaga}\".\n\nEl siguiente paso es una "
                  "evaluación corta de perfil que toma pocos minutos y se hace desde el celular:\n\n"
                  "{link}\n\nCuando termine, nuestra gerente de contratación le contactará.\n\n"
                  "Atentamente,\nEquipo de Selección"),
    },
    "voz_convite_en": {
        "assunto": "Next step: {vaga}",
        "corpo": ("Hi {nome},\n\nThanks for talking with Francisca. You meet the basic "
                  "requirements for the \"{vaga}\" position.\n\nThe next step is a short profile "
                  "assessment that takes a few minutes on your phone:\n\n{link}\n\n"
                  "Once you finish, our hiring manager will reach out.\n\n"
                  "Best regards,\nHiring Team"),
    },
    "voz_convite_pt": {
        "assunto": "Próximo passo: {vaga}",
        "corpo": ("Olá, {nome}!\n\nObrigado por conversar com a Francisca. Você atende aos "
                  "requisitos básicos da vaga \"{vaga}\".\n\nO próximo passo é uma avaliação "
                  "rápida de perfil, que leva poucos minutos e pode ser feita pelo celular:\n\n"
                  "{link}\n\nAo concluir, nossa gerente de contratação vai entrar em contato.\n\n"
                  "Atenciosamente,\nEquipe de Seleção"),
    },
}
NOMES_TEMPLATES_VOZ = {
    "voz_convite_es": "Triagem por voz: convite para os testes (espanhol)",
    "voz_convite_en": "Triagem por voz: convite para os testes (inglês)",
    "voz_convite_pt": "Triagem por voz: convite para os testes (português)",
}


# ------------------------------------------------------------ rotas HTTP

def _chamada_publica(r, completa=False):
    d = {
        "id": r["id"], "candidatura_id": r["candidatura_id"], "candidato_id": r["candidato_id"],
        "status": r["status"], "idioma": r["idioma"], "disparada_por": r["disparada_por"],
        "iniciada_em": r["iniciada_em"], "terminada_em": r["terminada_em"], "duracao": r["duracao"],
        "resultado": json.loads(r["resultado"]) if r["resultado"] else None,
        "tem_audio": bool(r["tem_audio"]), "erro": r["erro"],
    }
    if completa:
        d["transcricao"] = json.loads(r["transcricao"] or "[]")
        d["fatos"] = json.loads(r["fatos"]) if r["fatos"] else None
        d["invalidos"] = json.loads(r["invalidos"] or "[]")
        d["resumo"] = r["resumo"]
    return d


def _candidatura_publica(r):
    return {
        "id": r["id"], "candidato_id": r["candidato_id"], "nome": r["nome"],
        "vaga": r["vaga_titulo"], "cargo": r["cargo_nome"], "local": local_da_candidatura(r),
        "etapa": r["etapa"], "voz_status": r["voz_status"], "voz_tentativas": r["voz_tentativas"],
        "voz_ultima": r["voz_ultima"], "voz_proxima": r["voz_proxima"],
        "voz_outcome": r["voz_outcome"], "voz_score": r["voz_score"], "voz_tier": r["voz_tier"],
        "voz_resultado": json.loads(r["voz_resultado"]) if r["voz_resultado"] else None,
        "convite_enviado": bool(r["voz_convite_enviado"]), "telefone_valido": bool(para_e164(r["telefone"])),
        "idioma": r["idioma"],
    }


def rotear_publico(h, method, path, conn):
    """Rotas sem login (webhook do ElevenLabs). Devolve a resposta ou None."""
    if path != "/api/voz/webhook" or method != "POST":
        return None
    segredo = srv.config_get(conn, "elevenlabs_webhook_secret")
    if not segredo:
        return _resp(h, 503, {"erro": "webhook_not_configured"})
    bruto = getattr(h, "_raw", b"") or b""
    if not assinatura_valida(bruto, h.headers.get("ElevenLabs-Signature"), segredo):
        return _resp(h, 401, {"erro": "invalid_signature"})
    try:
        evento = json.loads(bruto.decode("utf-8"))
        dados = evento.get("data") or {}
        conversation_id = dados.get("conversation_id")
    except (ValueError, AttributeError):
        return _resp(h, 400, {"erro": "invalid_payload"})
    if conversation_id:
        # nunca confia no conteúdo do webhook: busca a conversa na API
        if evento.get("type") == "post_call_transcription":
            processar_conversa(conn, conversation_id)
        elif evento.get("type") == "call_initiation_failure":
            falha_de_inicio(conn, conversation_id, dados.get("failure_reason") or "unknown")
    return _resp(h, 200, {"ok": True})


def _resp(h, status, dados):
    """Responde e sinaliza ao server.py que a rota foi tratada."""
    h._json(status, dados)
    return True


def rotear_dono(h, method, path, conn):
    """Integração ElevenLabs da plataforma (só o dono do sistema)."""
    if path != "/api/dono/voz/integracao":
        return None
    if method == "GET":
        chave = srv.config_get(conn, "elevenlabs_api_key")
        return _resp(h, 200, {
            "api_key_final": chave[-4:] if chave else "",
            "agent_id": srv.config_get(conn, "elevenlabs_agent_id"),
            "phone_number_id": srv.config_get(conn, "elevenlabs_phone_number_id"),
            "webhook_configurado": bool(srv.config_get(conn, "elevenlabs_webhook_secret")),
            "webhook_url": srv.url_publica(conn, h.headers.get("Host")) + "/api/voz/webhook",
        })
    if method == "POST":
        d = h._body()
        for chave in ("agent_id", "phone_number_id"):
            if chave in d:
                srv.config_set(conn, "elevenlabs_" + chave, (d.get(chave) or "").strip())
        for chave in ("api_key", "webhook_secret"):
            if d.get(chave):
                srv.config_set(conn, "elevenlabs_" + chave, d[chave].strip())
        conn.commit()
        return _resp(h, 200, {"ok": True})
    return None


def _enviar_audio(h, dados):
    h.send_response(200)
    h.send_header("Content-Type", "audio/mpeg")
    h.send_header("Content-Length", str(len(dados)))
    h.send_header("Cache-Control", "private, max-age=3600")
    h.end_headers()
    h.wfile.write(dados)
    return True


def rotear_gestor(h, method, path, conn, gestor):
    """Rotas /api/gestor/voz* (gestor logado com o módulo 'voz')."""
    if not path.startswith("/api/gestor/voz"):
        return None
    if "voz" not in srv.modulos_do_gestor(gestor):
        return _resp(h, 403, {"erro": "Módulo não liberado para esta empresa.", "codigo": "module_disabled"})
    empresa_id = gestor["empresa_id"]

    def visivel(row):
        return visivel_para(gestor, row)

    # painel: fila, ligações recentes, números de hoje e regras da empresa
    if method == "GET" and path == "/api/gestor/voz":
        linhas = conn.execute(
            _SQL_CANDIDATURA + " WHERE ca.voz_status != '' AND c.empresa_id=?"
            " ORDER BY ca.atualizado_em DESC LIMIT 400",
            (empresa_id,),
        ).fetchall()
        linhas = [r for r in linhas if visivel(r)]
        ids = {r["id"] for r in linhas}
        chamadas = [
            c for c in conn.execute(
                "SELECT vc.*, c.nome FROM voz_chamadas vc JOIN candidatos c ON c.id=vc.candidato_id"
                " WHERE c.empresa_id=? ORDER BY vc.iniciada_em DESC LIMIT 200",
                (empresa_id,),
            ).fetchall() if c["candidatura_id"] in ids
        ]
        cfg = config_empresa(conn, empresa_id)
        zona = _zona(cfg)
        hoje = datetime.now(zona).strftime("%Y-%m-%d")
        stats = {"ligacoes": 0, "atendidas": 0, "strong": 0, "good": 0}
        for c in chamadas:
            inicio = _de_sql(c["iniciada_em"])
            if inicio and inicio.astimezone(zona).strftime("%Y-%m-%d") == hoje:
                stats["ligacoes"] += 1
                res = json.loads(c["resultado"]) if c["resultado"] else None
                if res:
                    stats["atendidas"] += 1
                    if res.get("tier") == "STRONG":
                        stats["strong"] += 1
                    if res.get("tier") == "GOOD":
                        stats["good"] += 1
        cargos = [
            {"id": g["id"], "nome": g["nome"], "voz_ativa": bool(g["voz_ativa"]), "peso_voz": g["peso_voz"]}
            for g in conn.execute(
                "SELECT id, nome, voz_ativa, peso_voz FROM cargos WHERE empresa_id=? ORDER BY nome", (empresa_id,)
            ).fetchall()
        ]
        recentes = []
        for c in chamadas[:40]:
            d = _chamada_publica(c)
            d["nome"] = c["nome"]
            recentes.append(d)
        return _resp(h, 200, {
            "configurado": gateway(conn) is not None,
            "webhook_configurado": bool(srv.config_get(conn, "elevenlabs_webhook_secret")),
            "config": cfg,
            "empresa": gestor["empresa_nome"] if "empresa_nome" in gestor.keys() else "",
            "fila": [_candidatura_publica(r) for r in linhas],
            "recentes": recentes,
            "hoje": stats,
            "ativas": sum(1 for c in chamadas if c["status"] in ("iniciando", "em_andamento", "processando")),
            "cargos": cargos,
            "admin": bool(gestor["is_admin"]),
        })

    if method == "POST" and path == "/api/gestor/voz/config":
        d = h._body()
        config = d.get("config") or {}
        # pausar e retomar: qualquer gestor da empresa com o módulo; o resto, só o admin
        if set(config) - {"pausado"} and not gestor["is_admin"]:
            return _resp(h, 403, {"erro": "Só o administrador da empresa altera as regras.", "codigo": "forbidden"})
        dados, erro = validar_config(config)
        if erro:
            return _resp(h, 400, {"erro": erro, "codigo": erro})
        salvar_config(conn, empresa_id, dados)
        conn.commit()
        return _resp(h, 200, {"ok": True, "config": config_empresa(conn, empresa_id)})

    if method == "POST" and path == "/api/gestor/voz/rodar":
        return _resp(h, 200, tick(conn, empresa_id=empresa_id))

    if path == "/api/gestor/voz/integracao":
        return _resp(h, 403, {"erro": "A integração com o ElevenLabs é configurada no painel do administrador do sistema.",
                              "codigo": "forbidden"})

    m = re.match(r"^/api/gestor/voz/cargo/(\d+)$", path)
    if m and method == "POST":
        if not gestor["is_admin"]:
            return _resp(h, 403, {"erro": "Apenas o administrador altera cargos.", "codigo": "forbidden"})
        if not srv.cargo_do_gestor(conn, gestor, int(m.group(1))):
            return _resp(h, 404, {"erro": "not_found", "codigo": "not_found"})
        d = h._body()
        try:
            peso = float(d.get("peso_voz", 0.30))
        except (TypeError, ValueError):
            return _resp(h, 400, {"erro": "invalid_number", "codigo": "invalid_number"})
        if not 0 <= peso <= 0.8:
            return _resp(h, 400, {"erro": "invalid_number", "codigo": "invalid_number"})
        conn.execute(
            "UPDATE cargos SET voz_ativa=?, peso_voz=? WHERE id=?",
            (1 if d.get("voz_ativa") else 0, peso, int(m.group(1))),
        )
        conn.commit()
        return _resp(h, 200, {"ok": True})

    m = re.match(r"^/api/gestor/voz/candidatura/(\d+)(/ligar)?$", path)
    if m and method == "POST":
        row = conn.execute(_SQL_CANDIDATURA + " WHERE ca.id=?", (int(m.group(1)),)).fetchone()
        if not row or not visivel(row):
            return _resp(h, 404, {"erro": "not_found", "codigo": "not_found"})
        if m.group(2):
            try:
                chamada_id = iniciar_ligacao(conn, row["id"], gestor["nome"], manual=True)
            except ErroVoz as exc:
                return _resp(h, 409, {"erro": str(exc), "codigo": exc.codigo})
            return _resp(h, 200, {"ok": True, "chamada_id": chamada_id})
        acao = (h._body().get("acao") or "")
        if row["voz_status"] == "ligando":
            return _resp(h, 409, {"erro": "in_call", "codigo": "in_call"})
        if acao == "fila":
            conn.execute("UPDATE candidaturas SET voz_status='para_ligar', voz_proxima='' WHERE id=?", (row["id"],))
            texto = "Voltou para a fila da triagem por voz"
        elif acao == "nao_ligar":
            conn.execute("UPDATE candidaturas SET voz_status='nao_ligar', voz_proxima='' WHERE id=?", (row["id"],))
            texto = "Marcado como Não ligar"
        elif acao == "zerar":
            conn.execute("UPDATE candidaturas SET voz_tentativas=0, voz_proxima='' WHERE id=?", (row["id"],))
            texto = "Tentativas da triagem por voz zeradas"
        else:
            return _resp(h, 400, {"erro": "invalid_action", "codigo": "invalid_action"})
        srv.registrar_evento(conn, row["candidato_id"], "voz", texto, gestor["nome"])
        conn.commit()
        return _resp(h, 200, {"ok": True})

    m = re.match(r"^/api/gestor/voz/candidato/(\d+)$", path)
    if m and method == "GET":
        cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)).fetchone()
        if not cand or not srv.gestor_ve_candidato(gestor, cand):
            return _resp(h, 404, {"erro": "not_found", "codigo": "not_found"})
        candidaturas = [
            _candidatura_publica(r) for r in conn.execute(
                _SQL_CANDIDATURA + " WHERE ca.candidato_id=? AND ca.voz_status != ''"
                " ORDER BY ca.criado_em DESC", (cand["id"],),
            ).fetchall()
        ]
        chamadas = [
            _chamada_publica(r, completa=True) for r in conn.execute(
                "SELECT * FROM voz_chamadas WHERE candidato_id=? ORDER BY iniciada_em DESC", (cand["id"],),
            ).fetchall()
        ]
        return _resp(h, 200, {"candidaturas": candidaturas, "chamadas": chamadas})

    m = re.match(r"^/api/gestor/voz/chamada/(\d+)/audio$", path)
    if m and method == "GET":
        r = conn.execute(
            "SELECT vc.*, c.local AS cand_local FROM voz_chamadas vc JOIN candidatos c ON c.id=vc.candidato_id"
            " WHERE vc.id=?", (int(m.group(1)),),
        ).fetchone()
        cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (r["candidato_id"],)).fetchone() if r else None
        if not r or not cand or not srv.gestor_ve_candidato(gestor, cand) or not r["tem_audio"]:
            return _resp(h, 404, {"erro": "no_recording", "codigo": "no_recording"})
        gw = gateway(conn)
        if gw is None:
            return _resp(h, 503, {"erro": "not_configured", "codigo": "not_configured"})
        return _enviar_audio(h, gw.audio(r["conversation_id"]))

    return _resp(h, 404, {"erro": "Rota não encontrada"})
