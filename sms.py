"""
Mensagens de texto (SMS) para candidatos, pela Twilio. DESLIGADO por padrão.

O módulo está completo, mas só envia quando o dono liga a chave global
"SMS ligado" (config sms_habilitado), o que exige marcar a campanha A2P 10DLC
como aprovada (config sms_a2p: brand id, campaign id, status e notas).

Regras de envio (verificar()):
  1. SMS ligado na plataforma e na empresa (config "sms:<empresa_id>", ativo);
  2. credenciais da Twilio (telefonia.py guarda twilio_account_sid e
     twilio_auth_token) e um número de envio: o número próprio ativo da empresa
     (numeros_empresa) ou o número da plataforma (config sms_numero_plataforma);
  3. celular dos EUA válido (+1, sem 800/8xx/900) e não marcado como fixo;
  4. sem descadastro (STOP) para o par número de envio + celular, e sem
     revogação do contato registrada pelo conta.py (contato_revogado_em);
  5. consentimento: exigido quando a empresa exige no conta.py
     (so_com_consentimento) ou na configuração de SMS (exigir_consentimento,
     padrão ligado). Vale candidatos.consentimento_contato_em (conta.py), se a
     coluna existir. Na resposta manual do gestor, uma mensagem recebida do
     candidato também conta como consentimento (foi ele quem escreveu);
  6. limite do plano: sms_mes do plano (planos.py, só leitura). Passou do
     limite, bloqueia, a não ser que a empresa tenha excedente liberado.
Horário de silêncio: só entre 8h e 21h no fuso da empresa (agenda ou voz,
senão America/New_York). Fora disso a mensagem fica agendada para as 8h e a
rotina_sms() envia (conferindo as regras de novo).
Toda mensagem termina com "Reply STOP to opt out" no idioma do candidato.

Entrada (POST /api/sms/entrada, assinatura X-Twilio-Signature conferida):
STOP, STOPALL, UNSUBSCRIBE, CANCEL, END, QUIT, PARAR, ALTO, REVOKE e OPTOUT
descadastram (com uma única confirmação); START e UNSTOP voltam; HELP, INFO,
AJUDA e AYUDA devolvem a ajuda. O resto vira conversa na ficha do candidato e
os administradores da empresa recebem um e-mail no idioma de cada um.
Status (POST /api/sms/status) atualiza a entrega.

Uso por empresa e mês (segmentos): uso_mes(). Outros módulos chamam
enviar_modelo(conn, candidato_id, chave, variaveis), que devolve um código e
nunca lança; com o SMS desligado não faz nada e devolve "desligado".

Sem dependências externas: urllib com timeout. Segredos nunca vão para log.
"""
import base64
import hashlib
import hmac
import json
import math
import re
import socket
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape as _xml

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

srv = None  # módulo do servidor, injetado por ligar()

TWILIO_API = "https://api.twilio.com/2010-04-01"
TIMEOUT = 15
ENVIO_EM_SEGUNDO_PLANO = True   # e-mails aos administradores (os testes desligam)
AGORA = None                    # nos testes: função sem argumentos que devolve um datetime UTC
FUSO_PADRAO = "America/New_York"
HORA_INICIO, HORA_FIM = 8, 21   # 8h às 21h no fuso do candidato (o da empresa)
MAX_TEXTO = 640                 # envio manual do gestor
MAX_MODELO = 480                # modelo editável
IDIOMAS = ("en", "pt", "es")
A2P_STATUS = ("nao_iniciado", "em_analise", "aprovado", "rejeitado")
E164_RE = re.compile(r"^\+1[2-9]\d{2}[2-9]\d{6}$")
SEM_SMS = {"800", "811", "833", "844", "855", "866", "877", "888", "900", "911"}
CODIGOS_OK = ("enviado", "agendado")

# palavra -> (tipo, idioma da palavra)
PALAVRAS = {
    "STOP": ("stop", None), "STOPALL": ("stop", None), "UNSUBSCRIBE": ("stop", "en"), "CANCEL": ("stop", "en"),
    "END": ("stop", "en"), "QUIT": ("stop", "en"), "REVOKE": ("stop", "en"), "OPTOUT": ("stop", "en"),
    "PARAR": ("stop", "es"), "ALTO": ("stop", "es"),
    "START": ("start", None), "UNSTOP": ("start", None),
    "HELP": ("help", "en"), "INFO": ("help", None), "AJUDA": ("help", "pt"), "AYUDA": ("help", "es"),
}

RODAPE = {"en": "Reply STOP to opt out.", "pt": "Responda STOP para sair.", "es": "Responde STOP para darte de baja."}

# modelos padrão (editáveis por empresa). Variáveis: {empresa} {nome} {vaga} {link} {data} {hora} {telefone}
MODELOS = {
    "convite_teste": {
        "en": "{empresa}: Hi {nome}, thanks for talking with us about the {vaga} job! Next step: complete two short "
              "assessments here: {link}",
        "pt": "{empresa}: Olá, {nome}! Obrigado pela conversa sobre a vaga de {vaga}. Próximo passo: faça duas "
              "avaliações rápidas aqui: {link}",
        "es": "{empresa}: Hola, {nome}. Gracias por hablar con nosotros sobre la vacante de {vaga}. Siguiente paso: "
              "completa dos evaluaciones cortas aquí: {link}",
    },
    "lembrete_entrevista": {
        "en": "{empresa}: Hi {nome}, reminder: your interview for {vaga} is on {data} at {hora}. Details: {link}",
        "pt": "{empresa}: Olá, {nome}! Lembrete: sua entrevista para {vaga} é em {data}, às {hora}. Detalhes: {link}",
        "es": "{empresa}: Hola, {nome}. Recordatorio: tu entrevista para {vaga} es el {data} a las {hora}. "
              "Detalles: {link}",
    },
    "onboarding_pendente": {
        "en": "{empresa}: Hi {nome}, you still have onboarding items to finish before your first day. "
              "Continue here: {link}",
        "pt": "{empresa}: Olá, {nome}! Ainda faltam itens do seu onboarding antes do primeiro dia. "
              "Continue aqui: {link}",
        "es": "{empresa}: Hola, {nome}. Todavía tienes pasos pendientes de tu incorporación antes de tu primer día. "
              "Continúa aquí: {link}",
    },
    "tentamos_ligar": {
        "en": "{empresa}: Hi {nome}, we tried to call you about your application for {vaga}. You can call us back "
              "at {telefone} or reply here.",
        "pt": "{empresa}: Olá, {nome}! Tentamos ligar para você sobre a sua candidatura para {vaga}. Você pode "
              "retornar para {telefone} ou responder aqui.",
        "es": "{empresa}: Hola, {nome}. Intentamos llamarte sobre tu postulación para {vaga}. Puedes devolvernos "
              "la llamada al {telefone} o responder aquí.",
    },
    "candidatura_recebida": {
        "en": "{empresa}: Hi {nome}, we received your application for {vaga}. Track your status here: {link}",
        "pt": "{empresa}: Olá, {nome}! Recebemos a sua candidatura para {vaga}. Acompanhe por aqui: {link}",
        "es": "{empresa}: Hola, {nome}. Recibimos tu postulación para {vaga}. Sigue el estado aquí: {link}",
    },
}

RESPOSTAS = {
    "stop": {
        "en": "{empresa}: You are unsubscribed and will not receive more text messages from us. Reply START to "
              "resubscribe.",
        "pt": "{empresa}: Você não vai mais receber mensagens de texto nossas. Responda START para voltar a receber.",
        "es": "{empresa}: Te diste de baja y no recibirás más mensajes de texto nuestros. Responde START para "
              "volver a recibirlos.",
    },
    "start": {
        "en": "{empresa}: You are resubscribed to text messages about your application. Msg & data rates may "
              "apply. Reply HELP for help, STOP to opt out.",
        "pt": "{empresa}: Você voltou a receber mensagens de texto sobre a sua candidatura. Podem ser cobradas "
              "tarifas de mensagens e dados. Responda HELP para ajuda ou STOP para sair.",
        "es": "{empresa}: Volviste a recibir mensajes de texto sobre tu postulación. Pueden aplicarse tarifas de "
              "mensajes y datos. Responde HELP para ayuda o STOP para darte de baja.",
    },
    "help": {
        "en": "{empresa}: Text messages about your job application. Help: {contato}. Msg frequency varies. "
              "Msg & data rates may apply. Reply STOP to opt out.",
        "pt": "{empresa}: Mensagens de texto sobre a sua candidatura. Ajuda: {contato}. A frequência varia. "
              "Podem ser cobradas tarifas de mensagens e dados. Responda STOP para sair.",
        "es": "{empresa}: Mensajes de texto sobre tu postulación. Ayuda: {contato}. La frecuencia varía. "
              "Pueden aplicarse tarifas de mensajes y datos. Responde STOP para darte de baja.",
    },
}

# texto da linha do tempo (em português; eventos_i18n.py traduz)
ROTULO_EVENTO = {
    "convite_teste": "convite para os testes", "lembrete_entrevista": "lembrete de entrevista",
    "onboarding_pendente": "lembrete do onboarding", "tentamos_ligar": "tentamos ligar",
    "candidatura_recebida": "candidatura recebida", "manual": "mensagem do gestor",
}

EMAIL_ADMIN = {
    "pt": {"assunto": "Nova mensagem de texto de {nome}",
           "corpo": "Olá, {gestor}!\n\n{nome} respondeu por mensagem de texto:\n\n\"{texto}\"\n\n"
                    "Abra a ficha do candidato para responder:\n{url}\n\nEquipe Bússola"},
    "en": {"assunto": "New text message from {nome}",
           "corpo": "Hi {gestor},\n\n{nome} replied by text message:\n\n\"{texto}\"\n\n"
                    "Open the candidate profile to reply:\n{url}\n\nThe Bússola team"},
    "es": {"assunto": "Nuevo mensaje de texto de {nome}",
           "corpo": "Hola, {gestor}:\n\n{nome} respondió por mensaje de texto:\n\n\"{texto}\"\n\n"
                    "Abre el perfil del candidato para responder:\n{url}\n\nEl equipo de Bússola"},
}

PADRAO_EMPRESA = {"ativo": False, "exigir_consentimento": True, "contato_ajuda": "", "modelos": {}}

# GSM-7 (3GPP 23.038): básico e extensão (a extensão ocupa 2 posições)
GSM_BASICO = set("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                 "ÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà")
GSM_EXTENSAO = set("^{}\\[~]|€\f")

ORDEM_STATUS = {"accepted": 0, "scheduled": 0, "queued": 1, "sending": 2, "sent": 3, "delivered": 4,
                "undelivered": 4, "failed": 4, "read": 5}


def ligar(modulo_servidor):
    global srv
    srv = modulo_servidor


def init_sms(c):
    """Tabelas do módulo. Chamado dentro de init_db() com o cursor aberto."""
    c.execute(
        "CREATE TABLE IF NOT EXISTS sms_mensagens ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER REFERENCES empresas(id) ON DELETE CASCADE,"
        " candidato_id INTEGER REFERENCES candidatos(id) ON DELETE CASCADE,"
        " direcao TEXT NOT NULL,"             # saida ou entrada
        " chave TEXT DEFAULT '',"             # modelo, manual, stop, start, help
        " de TEXT DEFAULT '',"
        " para TEXT DEFAULT '',"
        " corpo TEXT DEFAULT '',"
        " idioma TEXT DEFAULT '',"
        " segmentos INTEGER DEFAULT 0,"
        " twilio_sid TEXT DEFAULT '',"
        " status TEXT DEFAULT '',"            # agendado, enviando, queued, sent, delivered, failed, recebido...
        " erro_codigo TEXT DEFAULT '',"
        " erro TEXT DEFAULT '',"
        " autor TEXT DEFAULT '',"
        " lido INTEGER DEFAULT 1,"
        " agendado_para TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " atualizado_em TEXT DEFAULT (datetime('now')))"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_sms_cand ON sms_mensagens(empresa_id, candidato_id, id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sms_sid ON sms_mensagens(twilio_sid)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sms_fila ON sms_mensagens(status, agendado_para)")
    # descadastro por par (número de envio, celular), como as operadoras e a Twilio.
    # Sem a coluna empresa_id de propósito: o registro de STOP fica mesmo se a empresa for excluída.
    c.execute(
        "CREATE TABLE IF NOT EXISTS sms_optout ("
        " numero_de TEXT NOT NULL,"
        " telefone TEXT NOT NULL,"
        " empresa_origem INTEGER,"
        " palavra TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " PRIMARY KEY (numero_de, telefone))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS sms_bloqueios ("
        " telefone TEXT PRIMARY KEY,"
        " motivo TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')))"
    )


class ErroSms(Exception):
    """Erro com mensagem em português (traduzida por erros_i18n) e status HTTP."""

    def __init__(self, mensagem, status=400):
        Exception.__init__(self, mensagem)
        self.mensagem = mensagem
        self.status = status


# ------------------------------------------------------------ utilidades

def _agora():
    return AGORA() if AGORA else datetime.now(timezone.utc)


def _sql(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _get(row, chave, padrao=None):
    try:
        if isinstance(row, dict):
            return row.get(chave, padrao)
        return row[chave] if chave in row.keys() else padrao
    except (KeyError, IndexError, TypeError):
        return padrao


def _colunas(conn, tabela):
    try:
        return {r[1] for r in conn.execute("PRAGMA table_info(%s)" % tabela).fetchall()}
    except Exception:  # noqa: BLE001
        return set()


def _lang(v, padrao="en"):
    v = str(v or "").strip().lower()[:2]
    return v if v in IDIOMAS else padrao


def e164(numero):
    """Número dos EUA em E.164 ou None."""
    d = re.sub(r"\D", "", str(numero or ""))
    if len(d) == 10:
        d = "1" + d
    if len(d) != 11 or not d.startswith("1"):
        return None
    n = "+" + d
    return n if E164_RE.match(n) else None


def celular_valido(numero):
    n = e164(numero)
    if not n or n[2:5] in SEM_SMS:
        return None
    return n


def formatar(numero):
    n = e164(numero)
    return "(%s) %s-%s" % (n[2:5], n[5:8], n[8:]) if n else (numero or "")


def segmentos(texto):
    """(quantidade de segmentos, codificação) como a operadora conta."""
    texto = texto or ""
    if all(ch in GSM_BASICO or ch in GSM_EXTENSAO for ch in texto):
        unidades = len(texto) + sum(1 for ch in texto if ch in GSM_EXTENSAO)
        return (1 if unidades <= 160 else int(math.ceil(unidades / 153.0))), "GSM-7"
    unidades = len(texto.encode("utf-16-le")) // 2
    return (1 if unidades <= 70 else int(math.ceil(unidades / 67.0))), "UCS-2"


def renderizar(texto, variaveis):
    return re.sub(r"\{(\w+)\}", lambda m: str(variaveis.get(m.group(1), "") or ""), texto or "")


def compor(texto, lang):
    """Texto final: sempre termina com o aviso de STOP no idioma."""
    texto = (texto or "").strip()
    rodape = RODAPE[_lang(lang)]
    if texto.endswith(rodape):
        return texto
    return texto + "\n" + rodape


def _limpar(texto, segredos=()):
    texto = str(texto or "")
    for s in segredos:
        if s:
            texto = texto.replace(s, "***")
    return re.sub(r"\s+", " ", texto).strip()[:200]


# ------------------------------------------------------------ configuração

def config_global(conn):
    try:
        a2p = json.loads(srv.config_get(conn, "sms_a2p") or "{}")
    except ValueError:
        a2p = {}
    a2p = {
        "brand_id": str(a2p.get("brand_id") or ""), "campaign_id": str(a2p.get("campaign_id") or ""),
        "messaging_service_sid": str(a2p.get("messaging_service_sid") or ""),
        "status": a2p.get("status") if a2p.get("status") in A2P_STATUS else "nao_iniciado",
        "notas": str(a2p.get("notas") or ""), "atualizado_em": str(a2p.get("atualizado_em") or ""),
    }
    return {
        "habilitado": srv.config_get(conn, "sms_habilitado") == "1",
        "a2p": a2p,
        "numero_plataforma": srv.config_get(conn, "sms_numero_plataforma") or "",
        "responder_palavras_chave": srv.config_get(conn, "sms_responder_palavras") != "0",
    }


def habilitado(conn):
    try:
        return srv.config_get(conn, "sms_habilitado") == "1"
    except Exception:  # noqa: BLE001
        return False


def _chave_empresa(empresa_id):
    return "sms:%d" % int(empresa_id)


def config_empresa(conn, empresa_id):
    cfg = json.loads(json.dumps(PADRAO_EMPRESA))
    try:
        cfg.update(json.loads(srv.config_get(conn, _chave_empresa(empresa_id)) or "{}"))
    except ValueError:
        pass
    cfg["ativo"] = bool(cfg.get("ativo"))
    cfg["exigir_consentimento"] = bool(cfg.get("exigir_consentimento", True))
    if not isinstance(cfg.get("modelos"), dict):
        cfg["modelos"] = {}
    return cfg


def _salvar_empresa(conn, empresa_id, cfg):
    srv.config_set(conn, _chave_empresa(empresa_id), json.dumps(cfg, ensure_ascii=False))
    conn.commit()


def validar_config_empresa(d, atual):
    cfg = dict(atual)
    if "ativo" in d:
        cfg["ativo"] = bool(d["ativo"])
    if "exigir_consentimento" in d:
        cfg["exigir_consentimento"] = bool(d["exigir_consentimento"])
    if "contato_ajuda" in d:
        contato = str(d.get("contato_ajuda") or "").strip()
        if len(contato) > 80:
            raise ErroSms("Contato de ajuda longo demais (máximo de 80 caracteres)")
        cfg["contato_ajuda"] = contato
    if "modelos" in d:
        if not isinstance(d["modelos"], dict):
            raise ErroSms("Modelo de SMS inválido")
        modelos = dict(cfg.get("modelos") or {})
        for chave, textos in d["modelos"].items():
            if chave not in MODELOS or not isinstance(textos, dict):
                raise ErroSms("Modelo de SMS inválido")
            atual_m = dict(modelos.get(chave) or {})
            for lang, texto in textos.items():
                if lang not in IDIOMAS or not isinstance(texto, str):
                    raise ErroSms("Modelo de SMS inválido")
                texto = texto.strip()
                if len(texto) > MAX_MODELO:
                    raise ErroSms("Modelo de SMS longo demais (máximo de 480 caracteres)")
                if not texto or texto == MODELOS[chave][lang]:
                    atual_m.pop(lang, None)
                else:
                    atual_m[lang] = texto
            if atual_m:
                modelos[chave] = atual_m
            else:
                modelos.pop(chave, None)
        cfg["modelos"] = modelos
    return cfg


def modelo(conn, empresa_id, chave, lang):
    cfg = config_empresa(conn, empresa_id)
    return (cfg["modelos"].get(chave) or {}).get(lang) or MODELOS[chave][lang]


# ------------------------------------------------------------ dados auxiliares

def _empresa(conn, empresa_id):
    if not empresa_id:
        return None
    return conn.execute("SELECT * FROM empresas WHERE id=?", (empresa_id,)).fetchone()


def _candidato(conn, candidato_id):
    return conn.execute("SELECT * FROM candidatos WHERE id=?", (candidato_id,)).fetchone()


def twilio_credenciais(conn):
    sid = (srv.config_get(conn, "twilio_account_sid") or "").strip()
    token = (srv.config_get(conn, "twilio_auth_token") or "").strip()
    return (sid, token) if sid and token else (None, None)


def numero_da_empresa(conn, empresa_id):
    """Número próprio ativo da empresa (numeros_empresa, telefonia.py) ou None."""
    try:
        r = conn.execute("SELECT numero FROM numeros_empresa WHERE empresa_id=? AND status='ativo'"
                         " ORDER BY id DESC LIMIT 1", (empresa_id,)).fetchone()
    except Exception:  # noqa: BLE001
        return None
    return e164(r[0]) if r else None


def remetente(conn, empresa_id):
    return numero_da_empresa(conn, empresa_id) or e164(srv.config_get(conn, "sms_numero_plataforma"))


def _fuso(conn, empresa_id):
    nome = ""
    agenda = getattr(srv, "agenda", None)
    if agenda is not None and hasattr(agenda, "config"):
        try:
            nome = agenda.config(conn, empresa_id).get("fuso") or ""
        except Exception:  # noqa: BLE001
            nome = ""
    if not nome:
        voz = getattr(srv, "voz", None)
        if voz is not None and hasattr(voz, "config_empresa"):
            try:
                nome = voz.config_empresa(conn, empresa_id).get("fuso") or ""
            except Exception:  # noqa: BLE001
                nome = ""
    try:
        return ZoneInfo(nome or FUSO_PADRAO)
    except Exception:  # noqa: BLE001
        return ZoneInfo(FUSO_PADRAO)


def proximo_horario(conn, empresa_id, agora=None):
    """None quando agora está entre 8h e 21h no fuso da empresa; senão o próximo 8h (UTC)."""
    agora = agora or _agora()
    z = _fuso(conn, empresa_id)
    local = agora.astimezone(z)
    if HORA_INICIO <= local.hour < HORA_FIM:
        return None
    dia = local.date() if local.hour < HORA_INICIO else local.date() + timedelta(days=1)
    alvo = datetime(dia.year, dia.month, dia.day, HORA_INICIO, 0, tzinfo=z)
    return alvo.astimezone(timezone.utc)


def _optout(conn, de, para):
    return conn.execute("SELECT 1 FROM sms_optout WHERE numero_de=? AND telefone=?", (de, para)).fetchone() is not None


def _bloqueado(conn, telefone):
    return conn.execute("SELECT 1 FROM sms_bloqueios WHERE telefone=?", (telefone,)).fetchone() is not None


def _bloquear(conn, telefone, motivo):
    conn.execute("INSERT OR REPLACE INTO sms_bloqueios (telefone, motivo) VALUES (?,?)", (telefone, motivo))


def _registrar_optout(conn, de, para, empresa_id, palavra):
    return conn.execute(
        "INSERT OR IGNORE INTO sms_optout (numero_de, telefone, empresa_origem, palavra, criado_em)"
        " VALUES (?,?,?,?,?)", (de, para, empresa_id, palavra, _sql(_agora()))).rowcount


def _consentiu(conn, cand):
    return bool(_get(cand, "consentimento_contato_em", "") or "")


def exige_consentimento(conn, empresa_id):
    if config_empresa(conn, empresa_id)["exigir_consentimento"]:
        return True
    conta = getattr(srv, "conta", None)
    if conta is not None and hasattr(conta, "config"):
        try:
            return bool(conta.config(conn, empresa_id).get("so_com_consentimento"))
        except Exception:  # noqa: BLE001
            return False
    return False


def _escreveu(conn, cand):
    return conn.execute("SELECT 1 FROM sms_mensagens WHERE candidato_id=? AND empresa_id=? AND direcao='entrada'"
                        " AND chave='' LIMIT 1", (cand["id"], cand["empresa_id"])).fetchone() is not None


# ------------------------------------------------------------ uso e plano

def _mes(agora=None):
    planos = getattr(srv, "planos", None)
    if planos is not None and hasattr(planos, "mes_de"):
        try:
            return planos.mes_de(agora or _agora())
        except Exception:  # noqa: BLE001
            pass
    d = (agora or _agora()).astimezone(ZoneInfo(FUSO_PADRAO))
    return "%04d-%02d" % (d.year, d.month)


def _limites(mes):
    ano, m = int(mes[:4]), int(mes[5:7])
    z = ZoneInfo(FUSO_PADRAO)
    ini = datetime(ano, m, 1, tzinfo=z)
    fim = datetime(ano + (m == 12), 1 if m == 12 else m + 1, 1, tzinfo=z)
    return _sql(ini), _sql(fim)


def limite_plano(conn, e):
    """(limite de segmentos do mês ou None = sem limite, excedente liberado?). Só lê o planos.py."""
    planos = getattr(srv, "planos", None)
    if planos is None or not e:
        return None, False
    try:
        cat = planos.catalogo(conn)
        excedente = bool(_get(e, "excedente_permitido", 0)) and _get(e, "status") == "ativa"
        if planos.em_teste(e):
            return int((cat.get("trial") or {}).get("sms_mes") or 0), False
        p = planos.plano(cat, _get(e, "plano", "") or "")
        if not p:
            return None, excedente
        return int(p.get("sms_mes") or 0), excedente
    except Exception:  # noqa: BLE001
        return None, False


def uso_mes(conn, empresa_id, mes=None):
    """Uso de SMS da empresa no mês (segmentos enviados), com o limite do plano."""
    mes = mes or _mes()
    ini, fim = _limites(mes)
    r = conn.execute(
        "SELECT COALESCE(SUM(segmentos),0), COUNT(*) FROM sms_mensagens WHERE empresa_id=? AND direcao='saida'"
        " AND twilio_sid!='' AND status!='failed' AND criado_em>=? AND criado_em<?", (empresa_id, ini, fim)
    ).fetchone()
    recebidas = conn.execute(
        "SELECT COUNT(*) FROM sms_mensagens WHERE empresa_id=? AND direcao='entrada' AND criado_em>=? AND criado_em<?",
        (empresa_id, ini, fim)).fetchone()[0]
    limite, excedente = limite_plano(conn, _empresa(conn, empresa_id))
    seg = int(r[0] or 0)
    return {
        "mes": mes, "segmentos": seg, "mensagens": int(r[1] or 0), "recebidas": int(recebidas or 0),
        "limite": limite, "ilimitado": limite is None, "excedente_permitido": excedente,
        "restantes": None if limite is None else max(limite - seg, 0),
        "excedente": 0 if limite is None else max(seg - limite, 0),
        "pct": None if not limite else round(100.0 * seg / limite, 1),
    }


def _limite_ok(conn, empresa_id, novos):
    u = uso_mes(conn, empresa_id)
    if u["ilimitado"] or u["segmentos"] + novos <= u["limite"]:
        return True
    return u["excedente_permitido"]


# ------------------------------------------------------------ regras de envio

def verificar(conn, cand, manual=False):
    """(código de bloqueio ou None, contexto). Não confere horário nem limite."""
    if not habilitado(conn):
        return "desligado", {}
    if not cand:
        return "candidato_nao_encontrado", {}
    eid = cand["empresa_id"]
    if not eid or not config_empresa(conn, eid)["ativo"]:
        return "empresa_desligada", {}
    sid, _ = twilio_credenciais(conn)
    if not sid:
        return "sem_twilio", {}
    para = celular_valido(_get(cand, "telefone", ""))
    if not para or _bloqueado(conn, para):
        return "telefone_invalido", {}
    de = remetente(conn, eid)
    if not de:
        return "sem_remetente", {}
    if _optout(conn, de, para) or (_get(cand, "contato_revogado_em", "") or ""):
        return "optout", {}
    if exige_consentimento(conn, eid) and not _consentiu(conn, cand):
        if not (manual and _escreveu(conn, cand)):
            return "sem_consentimento", {}
    return None, {"de": de, "para": para, "empresa_id": eid, "lang": _lang(_get(cand, "idioma", ""))}


def _variaveis_padrao(conn, cand, de, lang):
    e = _empresa(conn, cand["empresa_id"])
    v = {"empresa": e["nome"] if e else "", "nome": (cand["nome"] or "").split(" ")[0] or cand["nome"] or "",
         "vaga": "", "link": "", "data": "", "hora": "", "telefone": formatar(de)}
    try:
        base = srv.variaveis_candidato(conn, cand)
        v["vaga"] = base.get("vaga") or ""
        v["link"] = (base.get("link") or "") + ("&lang=" + lang if base.get("link") and lang != "pt" else "")
    except Exception:  # noqa: BLE001
        pass
    return v


def _inserir_saida(conn, cand, ctx, texto, chave, autor, status, agendado_para=""):
    seg, _ = segmentos(texto)
    agora = _sql(_agora())
    return conn.execute(
        "INSERT INTO sms_mensagens (empresa_id, candidato_id, direcao, chave, de, para, corpo, idioma, segmentos,"
        " status, autor, agendado_para, criado_em, atualizado_em) VALUES (?,?, 'saida', ?,?,?,?,?,?,?,?,?,?,?)",
        (ctx["empresa_id"], cand["id"], chave, ctx["de"], ctx["para"], texto, ctx["lang"], seg, status,
         autor or "sistema", agendado_para, agora, agora)).lastrowid


def _evento(conn, candidato_id, texto, autor="sistema"):
    try:
        srv.registrar_evento(conn, candidato_id, "sms", texto, autor)
    except Exception:  # noqa: BLE001
        pass


def _enviar(conn, cand, texto_base, chave, autor="sistema", manual=False, lang=None):
    codigo, ctx = verificar(conn, cand, manual)
    if codigo:
        return codigo, None
    if lang:
        ctx["lang"] = _lang(lang)
    texto = compor(texto_base, ctx["lang"])
    if not _limite_ok(conn, ctx["empresa_id"], segmentos(texto)[0]):
        return "limite_plano", None
    quando = proximo_horario(conn, ctx["empresa_id"])
    if quando:
        mid = _inserir_saida(conn, cand, ctx, texto, chave, autor, "agendado", _sql(quando))
        _evento(conn, cand["id"], "SMS agendado para o horário permitido (8h às 21h)", autor or "sistema")
        conn.commit()
        return "agendado", mid
    mid = _inserir_saida(conn, cand, ctx, texto, chave, autor, "enviando")
    conn.commit()
    return _despachar(conn, mid), mid


def _twilio_post(sid, token, caminho, dados):
    auth = base64.b64encode(("%s:%s" % (sid, token)).encode("utf-8")).decode("ascii")
    url = "%s/Accounts/%s/%s" % (TWILIO_API, urllib.parse.quote(sid), caminho)
    req = urllib.request.Request(url, data=urllib.parse.urlencode(dados).encode("utf-8"), method="POST", headers={
        "Authorization": "Basic " + auth, "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status, bruto = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, bruto = exc.code, exc.read()
    except (urllib.error.URLError, socket.timeout, OSError):
        return 0, {"message": "Sem conexão com a Twilio"}
    try:
        return status, (json.loads(bruto.decode("utf-8")) if bruto else {})
    except (ValueError, UnicodeDecodeError):
        return status, {}


def _base_url(conn):
    return srv.url_publica(conn).rstrip("/")


def _despachar(conn, mid):
    """Manda à Twilio a mensagem já gravada. Devolve o código final."""
    m = conn.execute("SELECT * FROM sms_mensagens WHERE id=?", (mid,)).fetchone()
    sid, token = twilio_credenciais(conn)
    if not sid:
        conn.execute("UPDATE sms_mensagens SET status='cancelado', erro='sem_twilio' WHERE id=?", (mid,))
        conn.commit()
        return "sem_twilio"
    status, r = _twilio_post(sid, token, "Messages.json", {
        "To": m["para"], "From": m["de"], "Body": m["corpo"],
        "StatusCallback": _base_url(conn) + "/api/sms/status"})
    agora = _sql(_agora())
    if 200 <= status < 300 and isinstance(r, dict) and r.get("sid"):
        try:
            seg = int(r.get("num_segments") or m["segmentos"] or 1)
        except (TypeError, ValueError):
            seg = m["segmentos"] or 1
        conn.execute("UPDATE sms_mensagens SET twilio_sid=?, status=?, segmentos=?, atualizado_em=? WHERE id=?",
                     (r["sid"], r.get("status") or "queued", seg, agora, mid))
        if m["candidato_id"]:
            _evento(conn, m["candidato_id"], "SMS enviado: %s" % ROTULO_EVENTO.get(m["chave"], "mensagem do gestor"),
                    m["autor"] or "sistema")
        conn.commit()
        return "enviado"
    codigo = str((r or {}).get("code") or "") if isinstance(r, dict) else ""
    detalhe = _limpar((r or {}).get("message") if isinstance(r, dict) else "", (sid, token)) or ("HTTP %d" % status)
    resultado = "erro_envio"
    if codigo == "21610":    # o celular já mandou STOP para este número
        _registrar_optout(conn, m["de"], m["para"], m["empresa_id"], "twilio_21610")
        resultado = "optout"
    elif codigo in ("21614", "21211", "21612", "21408"):  # não é celular, inválido ou região não liberada
        _bloquear(conn, m["para"], "twilio_" + codigo)
        resultado = "telefone_invalido"
    conn.execute("UPDATE sms_mensagens SET status='failed', erro_codigo=?, erro=?, atualizado_em=? WHERE id=?",
                 (codigo, detalhe, agora, mid))
    if m["candidato_id"]:
        _evento(conn, m["candidato_id"], "Falha ao enviar SMS: %s" % detalhe)
    conn.commit()
    sys.stderr.write("SMS: envio #%d falhou (%s)\n" % (mid, codigo or status))
    return resultado


def enviar_modelo(conn, candidato_id, chave, variaveis=None, autor="sistema"):
    """Para outros módulos. Devolve um código: enviado, agendado, desligado, empresa_desligada,
    sem_twilio, sem_remetente, telefone_invalido, optout, sem_consentimento, limite_plano,
    modelo_invalido, candidato_nao_encontrado ou erro_envio. Nunca lança."""
    try:
        if not habilitado(conn):
            return "desligado"
        if chave not in MODELOS:
            return "modelo_invalido"
        cand = _candidato(conn, candidato_id)
        codigo, ctx = verificar(conn, cand)
        if codigo:
            return codigo
        v = _variaveis_padrao(conn, cand, ctx["de"], ctx["lang"])
        v.update({k: v2 for k, v2 in (variaveis or {}).items() if v2 is not None})
        texto = renderizar(modelo(conn, cand["empresa_id"], chave, ctx["lang"]), v)
        return _enviar(conn, cand, texto, chave, autor=autor or "sistema")[0]
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("SMS: enviar_modelo falhou: %r\n" % exc)
        return "erro_envio"


def enviar_manual(conn, gestor, cand, texto):
    """Resposta do gestor pela ficha do candidato."""
    texto = (texto or "").strip()
    if not texto:
        raise ErroSms("Escreva a mensagem")
    if len(texto) > MAX_TEXTO:
        raise ErroSms("Mensagem longa demais (máximo de 640 caracteres)")
    return _enviar(conn, cand, texto, "manual", autor=gestor["nome"], manual=True)[0]


def processar_agendados(conn):
    """Envia as mensagens agendadas que chegaram na hora (conferindo as regras de novo)."""
    enviados = 0
    agora = _agora()
    for m in conn.execute("SELECT * FROM sms_mensagens WHERE status='agendado' AND agendado_para<=?"
                          " ORDER BY id LIMIT 200", (_sql(agora),)).fetchall():
        cand = _candidato(conn, m["candidato_id"]) if m["candidato_id"] else None
        codigo, _ = verificar(conn, cand, m["chave"] == "manual")
        if not codigo and not _limite_ok(conn, m["empresa_id"], m["segmentos"]):
            codigo = "limite_plano"
        if codigo:
            conn.execute("UPDATE sms_mensagens SET status='cancelado', erro=?, atualizado_em=? WHERE id=?",
                         (codigo, _sql(agora), m["id"]))
            conn.commit()
            continue
        quando = proximo_horario(conn, m["empresa_id"], agora)
        if quando:
            conn.execute("UPDATE sms_mensagens SET agendado_para=? WHERE id=?", (_sql(quando), m["id"]))
            conn.commit()
            continue
        if not conn.execute("UPDATE sms_mensagens SET status='enviando' WHERE id=? AND status='agendado'",
                            (m["id"],)).rowcount:
            continue
        conn.commit()
        if _despachar(conn, m["id"]) == "enviado":
            enviados += 1
    return enviados


def rotina_sms(intervalo=300):
    while True:
        try:
            conn = srv.db()
            try:
                if habilitado(conn):
                    processar_agendados(conn)
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("SMS: rotina falhou: %r\n" % exc)
        time.sleep(intervalo)


# ------------------------------------------------------------ entrada, status e assinatura

def assinatura(url, pares, token):
    """X-Twilio-Signature: HMAC-SHA1 (base64) da URL completa seguida dos parâmetros
    do POST em ordem alfabética (nome e valor colados)."""
    dados = url + "".join(k + v for k, v in sorted(pares))
    return base64.b64encode(hmac.new(token.encode("utf-8"), dados.encode("utf-8"), hashlib.sha1).digest()).decode()


def assinatura_valida(url, pares, token, recebida):
    if not (token and recebida):
        return False
    return hmac.compare_digest(assinatura(url, pares, token), str(recebida).strip())


def _urls_possiveis(h, conn):
    host = h.headers.get("Host") or ""
    urls = [srv.url_publica(conn, host).rstrip("/") + h.path]
    if host:
        for esquema in ("https", "http"):
            u = "%s://%s%s" % (esquema, host, h.path)
            if u not in urls:
                urls.append(u)
    return urls


def palavra_chave(corpo):
    """(tipo, idioma) quando a mensagem inteira é uma palavra-chave, senão (None, None)."""
    t = unicodedata.normalize("NFKD", str(corpo or "")).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"[^A-Za-z]", "", t).upper()
    if not t or len(str(corpo or "").split()) > 2:
        return None, None
    return PALAVRAS.get(t, (None, None))


def _candidato_por_telefone(conn, empresa_id, telefone):
    for c in conn.execute("SELECT * FROM candidatos WHERE empresa_id=? AND telefone LIKE ? ORDER BY id DESC",
                          (empresa_id, "%" + telefone[-4:] + "%")).fetchall():
        if e164(c["telefone"]) == telefone:
            return c
    return None


def localizar(conn, numero_nosso, telefone):
    """(empresa_id, candidato) da mensagem recebida. Número próprio: só a empresa dona dele.
    Número da plataforma: a conversa da última mensagem enviada a este celular por ele."""
    eid = None
    try:
        r = conn.execute("SELECT empresa_id FROM numeros_empresa WHERE numero=? AND status='ativo'"
                         " ORDER BY id DESC LIMIT 1", (numero_nosso,)).fetchone()
        eid = r[0] if r else None
    except Exception:  # noqa: BLE001
        eid = None
    sql = ("SELECT empresa_id, candidato_id FROM sms_mensagens WHERE direcao='saida' AND de=? AND para=?"
           " AND candidato_id IS NOT NULL")
    args = [numero_nosso, telefone]
    if eid:
        sql += " AND empresa_id=?"
        args.append(eid)
    r = conn.execute(sql + " ORDER BY id DESC LIMIT 1", args).fetchone()
    if r:
        cand = _candidato(conn, r["candidato_id"])
        if cand and cand["empresa_id"] == r["empresa_id"]:
            return r["empresa_id"], cand
    if eid:
        return eid, _candidato_por_telefone(conn, eid, telefone)
    return None, None


def _contato_ajuda(conn, empresa_id):
    if empresa_id:
        c = config_empresa(conn, empresa_id).get("contato_ajuda")
        if c:
            return c
        for g in _admins(conn, empresa_id):
            return g["email"]
    return srv.config_get(conn, "dono_email") or _base_url(conn)


def _admins(conn, empresa_id):
    sql = "SELECT * FROM gestores WHERE empresa_id=? AND is_admin=1 AND aprovado=1 AND email!=''"
    if "suporte" in _colunas(conn, "gestores"):
        sql += " AND COALESCE(suporte,0)=0"
    return conn.execute(sql + " ORDER BY id", (empresa_id,)).fetchall()


def _avisar_admins(conn, empresa_id, cand, texto):
    lista = []
    url = _base_url(conn) + "/gestor"
    for g in _admins(conn, empresa_id):
        lang = _lang(_get(g, "idioma", "pt"), "pt")
        tx = EMAIL_ADMIN[lang]
        nome = cand["nome"] if cand else ""
        lista.append((g["email"], tx["assunto"].format(nome=nome),
                      tx["corpo"].format(gestor=g["nome"] or "", nome=nome, texto=texto[:500], url=url), lang))
    if not lista:
        return []

    def trabalho(c):
        for para, assunto, corpo, lang in lista:
            try:
                marca = srv.mensagens.marca(c, empresa_id) if getattr(srv, "mensagens", None) else None
                srv.enviar_email(c, para, assunto, corpo, marca=marca, idioma=lang)
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write("SMS: e-mail ao administrador falhou: %r\n" % exc)

    if ENVIO_EM_SEGUNDO_PLANO:
        def rodar():
            c = srv.db()
            try:
                trabalho(c)
            finally:
                c.close()
        threading.Thread(target=rodar, daemon=True).start()
    else:
        trabalho(conn)
    return [x[0] for x in lista]


def processar_entrada(conn, p):
    """Mensagem recebida (parâmetros da Twilio). Devolve o texto da resposta ou None."""
    telefone = e164(p.get("From"))
    nosso = e164(p.get("To"))
    corpo = str(p.get("Body") or "")[:1600]
    msid = str(p.get("MessageSid") or p.get("SmsSid") or "")[:64]
    if not telefone or not nosso:
        return None
    if msid and conn.execute("SELECT 1 FROM sms_mensagens WHERE twilio_sid=? AND direcao='entrada'",
                             (msid,)).fetchone():
        return None  # a Twilio repetiu o webhook
    eid, cand = localizar(conn, nosso, telefone)
    tipo, lang_palavra = palavra_chave(corpo)
    lang = _lang(_get(cand, "idioma", "") if cand else "", "") or lang_palavra or "en"
    agora = _sql(_agora())
    conn.execute(
        "INSERT INTO sms_mensagens (empresa_id, candidato_id, direcao, chave, de, para, corpo, idioma, segmentos,"
        " twilio_sid, status, autor, lido, criado_em, atualizado_em) VALUES (?,?, 'entrada', ?,?,?,?,?,?,?,"
        " 'recebido', 'candidato', ?,?,?)",
        (eid, cand["id"] if cand else None, tipo or "", telefone, nosso, corpo, lang, segmentos(corpo)[0], msid,
         0 if (not tipo and cand) else 1, agora, agora))
    e = _empresa(conn, eid)
    nome_empresa = e["nome"] if e else (srv.config_get(conn, "sms_nome_plataforma") or "Bússola")
    resposta = None
    if tipo == "stop":
        if _registrar_optout(conn, nosso, telefone, eid, re.sub(r"[^A-Za-z]", "", corpo).upper()[:20]):
            resposta = RESPOSTAS["stop"][lang].format(empresa=nome_empresa)
            if cand:
                _evento(conn, cand["id"], "Pediu para não receber SMS (STOP)", "candidato")
    elif tipo == "start":
        if conn.execute("DELETE FROM sms_optout WHERE numero_de=? AND telefone=?", (nosso, telefone)).rowcount:
            resposta = RESPOSTAS["start"][lang].format(empresa=nome_empresa)
            if cand:
                _evento(conn, cand["id"], "Voltou a receber SMS (START)", "candidato")
    elif tipo == "help":
        resposta = RESPOSTAS["help"][lang].format(empresa=nome_empresa, contato=_contato_ajuda(conn, eid))
    elif cand:
        _evento(conn, cand["id"], "SMS recebido", "candidato")
    conn.commit()
    if not tipo and cand and habilitado(conn) and config_empresa(conn, eid)["ativo"]:
        _avisar_admins(conn, eid, cand, corpo)
    if resposta and not (habilitado(conn) and config_global(conn)["responder_palavras_chave"]):
        resposta = None
    if resposta:
        conn.execute(
            "INSERT INTO sms_mensagens (empresa_id, candidato_id, direcao, chave, de, para, corpo, idioma, segmentos,"
            " status, autor, criado_em, atualizado_em) VALUES (?,?, 'saida', ?,?,?,?,?,?, 'resposta', 'sistema', ?,?)",
            (eid, cand["id"] if cand else None, tipo, nosso, telefone, resposta, lang, segmentos(resposta)[0],
             agora, agora))
        conn.commit()
    return resposta


def processar_status(conn, p):
    msid = str(p.get("MessageSid") or p.get("SmsSid") or "")
    novo = str(p.get("MessageStatus") or p.get("SmsStatus") or "").lower()
    if not msid or novo not in ORDEM_STATUS:
        return False
    m = conn.execute("SELECT * FROM sms_mensagens WHERE twilio_sid=? AND direcao='saida'", (msid,)).fetchone()
    if not m:
        return False
    if ORDEM_STATUS.get(novo, 0) < ORDEM_STATUS.get(m["status"], 0):
        return False  # chegou fora de ordem
    codigo = str(p.get("ErrorCode") or "")[:10]
    campos, args = ["status=?", "erro_codigo=?", "atualizado_em=?"], [novo, codigo, _sql(_agora())]
    try:
        seg = int(p.get("NumSegments") or 0)
    except (TypeError, ValueError):
        seg = 0
    if seg > 0:
        campos.append("segmentos=?")
        args.append(seg)
    conn.execute("UPDATE sms_mensagens SET %s WHERE id=?" % ", ".join(campos), args + [m["id"]])
    if codigo == "21610":
        _registrar_optout(conn, m["de"], m["para"], m["empresa_id"], "twilio_21610")
    elif codigo in ("30006",):  # fixo ou operadora que não recebe SMS
        _bloquear(conn, m["para"], "twilio_" + codigo)
    conn.commit()
    return True


def _twiml(h, texto=None):
    corpo = '<?xml version="1.0" encoding="UTF-8"?><Response>%s</Response>' % (
        "<Message>%s</Message>" % _xml(texto) if texto else "")
    dados = corpo.encode("utf-8")
    h.send_response(200)
    h.send_header("Content-Type", "text/xml; charset=utf-8")
    h.send_header("Content-Length", str(len(dados)))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    h.wfile.write(dados)
    return True


def _proibido(h):
    dados = b"Forbidden"
    h.send_response(403)
    h.send_header("Content-Type", "text/plain; charset=utf-8")
    h.send_header("Content-Length", str(len(dados)))
    h.end_headers()
    h.wfile.write(dados)
    return True


def rotear_publico(h, method, path, conn):
    """POST /api/sms/entrada e /api/sms/status (webhooks da Twilio, assinados)."""
    if path not in ("/api/sms/entrada", "/api/sms/status"):
        return None
    if method != "POST":
        h._json(405, {"erro": "Método não permitido"})
        return True
    raw = getattr(h, "_raw", b"") or b""
    pares = urllib.parse.parse_qsl(raw.decode("utf-8", "replace"), keep_blank_values=True)
    sid, token = twilio_credenciais(conn)
    recebida = h.headers.get("X-Twilio-Signature", "")
    if not token or not any(assinatura_valida(u, pares, token, recebida) for u in _urls_possiveis(h, conn)):
        return _proibido(h)
    p = dict(pares)
    if p.get("AccountSid") and p["AccountSid"] != sid:
        return _proibido(h)
    if path == "/api/sms/entrada":
        return _twiml(h, processar_entrada(conn, p))
    processar_status(conn, p)
    return _twiml(h, None)


# ------------------------------------------------------------ rotas do gestor

def _resp(h, status, dados):
    h._json(status, dados)
    return True


def _mensagem_publica(m):
    return {"id": m["id"], "direcao": m["direcao"], "chave": m["chave"], "corpo": m["corpo"], "status": m["status"],
            "erro_codigo": m["erro_codigo"], "autor": m["autor"], "segmentos": m["segmentos"],
            "agendado_para": m["agendado_para"], "criado_em": m["criado_em"]}


def estado_candidato(conn, gestor, cand):
    eid = gestor["empresa_id"]
    codigo, _ = verificar(conn, cand, manual=True)
    conn.execute("UPDATE sms_mensagens SET lido=1 WHERE empresa_id=? AND candidato_id=? AND direcao='entrada'"
                 " AND lido=0", (eid, cand["id"]))
    conn.commit()
    msgs = conn.execute("SELECT * FROM sms_mensagens WHERE empresa_id=? AND candidato_id=? ORDER BY id DESC LIMIT 200",
                        (eid, cand["id"])).fetchall()
    de = remetente(conn, eid)
    para = celular_valido(_get(cand, "telefone", ""))
    cfg = config_empresa(conn, eid)
    return {
        "global": habilitado(conn), "empresa": cfg["ativo"],
        "telefone": para or "", "optout": bool(de and para and _optout(conn, de, para)),
        "consentimento": _consentiu(conn, cand), "exige_consentimento": exige_consentimento(conn, eid),
        "motivo": codigo, "fora_do_horario": proximo_horario(conn, eid) is not None,
        "modelos": list(MODELOS.keys()), "mensagens": [_mensagem_publica(m) for m in reversed(msgs)],
    }


def _publico_empresa(conn, gestor):
    eid = gestor["empresa_id"]
    cfg = config_empresa(conn, eid)
    g = config_global(conn)
    return {
        "global": g["habilitado"], "ativo": cfg["ativo"], "exigir_consentimento": cfg["exigir_consentimento"],
        "consentimento_conta": bool(getattr(srv, "conta", None)) and exige_consentimento(conn, eid)
        and not cfg["exigir_consentimento"],
        "contato_ajuda": cfg["contato_ajuda"], "contato_padrao": _contato_ajuda(conn, eid) if not cfg["contato_ajuda"] else "",
        "modelos": cfg["modelos"], "padroes": MODELOS, "rodape": RODAPE, "max_modelo": MAX_MODELO,
        "numero": formatar(remetente(conn, eid)) if remetente(conn, eid) else "",
        "numero_proprio": bool(numero_da_empresa(conn, eid)),
        "uso": uso_mes(conn, eid), "admin": bool(gestor["is_admin"]),
    }


def _candidato_do_gestor(conn, gestor, cid):
    cand = _candidato(conn, cid)
    if not cand or not srv.gestor_ve_candidato(gestor, cand):
        return None
    return cand


def _auditar(conn, acao, alvo, gestor=None, empresa_id=None, ip="", quem=""):
    seg = getattr(srv, "seguranca", None)
    if seg is not None:
        try:
            seg.registrar(conn, acao, gestor, alvo, ip or "", empresa_id=empresa_id, quem=quem)
        except Exception:  # noqa: BLE001
            pass


def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/sms"):
        return None
    ip = h._ip_cliente() if hasattr(h, "_ip_cliente") else ""
    try:
        if path == "/api/gestor/sms/uso" and method == "GET":
            return _resp(h, 200, {"uso": uso_mes(conn, gestor["empresa_id"]), "global": habilitado(conn),
                                  "ativo": config_empresa(conn, gestor["empresa_id"])["ativo"]})
        if path == "/api/gestor/sms/config":
            if method == "GET":
                return _resp(h, 200, _publico_empresa(conn, gestor))
            if method == "POST":
                if not gestor["is_admin"]:
                    return _resp(h, 403, {"erro": "Apenas o administrador da empresa configura o SMS"})
                cfg = validar_config_empresa(h._body(), config_empresa(conn, gestor["empresa_id"]))
                _salvar_empresa(conn, gestor["empresa_id"], cfg)
                _auditar(conn, "sms_config", "ativo=%d" % cfg["ativo"], gestor, ip=ip)
                conn.commit()
                return _resp(h, 200, dict(_publico_empresa(conn, gestor), ok=True))
        m = re.match(r"^/api/gestor/sms/candidato/(\d+)(?:/(responder|modelo))?$", path)
        if m:
            cand = _candidato_do_gestor(conn, gestor, int(m.group(1)))
            if not cand:
                return _resp(h, 404, {"erro": "Candidato não encontrado"})
            if method == "GET" and not m.group(2):
                return _resp(h, 200, estado_candidato(conn, gestor, cand))
            if method == "POST" and m.group(2) == "responder":
                codigo = enviar_manual(conn, gestor, cand, h._body().get("texto"))
            elif method == "POST" and m.group(2) == "modelo":
                chave = str(h._body().get("chave") or "")
                if chave not in MODELOS:
                    raise ErroSms("Modelo de SMS inválido")
                codigo = enviar_modelo(conn, cand["id"], chave, autor=gestor["nome"])
            else:
                return _resp(h, 405, {"erro": "Método não permitido"})
            return _resp(h, 200, dict(estado_candidato(conn, gestor, cand), ok=codigo in CODIGOS_OK, status=codigo))
    except ErroSms as exc:
        return _resp(h, exc.status, {"erro": exc.mensagem})
    return _resp(h, 404, {"erro": "Rota não encontrada"})


# ------------------------------------------------------------ rotas do dono

def painel_dono(conn):
    g = config_global(conn)
    sid, token = twilio_credenciais(conn)
    base = _base_url(conn)
    empresas = []
    for e in conn.execute("SELECT * FROM empresas ORDER BY nome").fetchall():
        cfg = config_empresa(conn, e["id"])
        de = remetente(conn, e["id"])
        empresas.append({"id": e["id"], "nome": e["nome"], "status": e["status"], "ativo": cfg["ativo"],
                         "numero": formatar(de) if de else "", "numero_proprio": bool(numero_da_empresa(conn, e["id"])),
                         "uso": uso_mes(conn, e["id"])})
    return dict(g, twilio_configurado=bool(sid and token), webhook_entrada=base + "/api/sms/entrada",
                webhook_status=base + "/api/sms/status", a2p_status_opcoes=list(A2P_STATUS), empresas=empresas,
                mes=_mes(), exemplos={k: v["en"] for k, v in MODELOS.items()}, rodape=RODAPE)


def salvar_dono(conn, d):
    g = config_global(conn)
    if "a2p" in d:
        a = d.get("a2p") if isinstance(d.get("a2p"), dict) else {}
        novo = dict(g["a2p"])
        for campo, maximo in (("brand_id", 64), ("campaign_id", 64), ("messaging_service_sid", 64), ("notas", 2000)):
            if campo in a:
                valor = str(a.get(campo) or "").strip()
                if len(valor) > maximo:
                    raise ErroSms("Texto longo demais")
                novo[campo] = valor
        if "status" in a:
            if a["status"] not in A2P_STATUS:
                raise ErroSms("Status A2P inválido")
            novo["status"] = a["status"]
        novo["atualizado_em"] = _sql(_agora())
        srv.config_set(conn, "sms_a2p", json.dumps(novo, ensure_ascii=False))
        g["a2p"] = novo
        if novo["status"] != "aprovado" and g["habilitado"]:
            srv.config_set(conn, "sms_habilitado", "")  # campanha não aprovada desliga o envio
    if "numero_plataforma" in d:
        n = str(d.get("numero_plataforma") or "").strip()
        if n and not e164(n):
            raise ErroSms("Número de envio inválido: use o formato +1XXXXXXXXXX")
        srv.config_set(conn, "sms_numero_plataforma", e164(n) if n else "")
    if "responder_palavras_chave" in d:
        srv.config_set(conn, "sms_responder_palavras", "1" if d.get("responder_palavras_chave") else "0")
    if "habilitado" in d:
        if d.get("habilitado"):
            if g["a2p"]["status"] != "aprovado":
                raise ErroSms("Marque a campanha A2P como aprovada antes de ligar o SMS")
            srv.config_set(conn, "sms_habilitado", "1")
        else:
            srv.config_set(conn, "sms_habilitado", "")
    conn.commit()


def configurar_webhooks(conn):
    """Aponta o webhook de SMS dos números (próprios ativos e o da plataforma) para /api/sms/entrada."""
    sid, token = twilio_credenciais(conn)
    if not sid:
        raise ErroSms("Configure a Twilio em Integrações primeiro")
    base = _base_url(conn)
    alvos = []
    try:
        alvos = [(r["numero"], r["twilio_sid"]) for r in conn.execute(
            "SELECT numero, twilio_sid FROM numeros_empresa WHERE status='ativo'").fetchall()]
    except Exception:  # noqa: BLE001
        alvos = []
    plat = e164(srv.config_get(conn, "sms_numero_plataforma"))
    if plat and plat not in [a[0] for a in alvos]:
        alvos.append((plat, ""))
    feitos, falhas = 0, []
    auth = base64.b64encode(("%s:%s" % (sid, token)).encode("utf-8")).decode("ascii")
    for numero, psid in alvos:
        if not psid:
            url = "%s/Accounts/%s/IncomingPhoneNumbers.json?%s" % (
                TWILIO_API, urllib.parse.quote(sid), urllib.parse.urlencode({"PhoneNumber": numero}))
            req = urllib.request.Request(url, method="GET", headers={"Authorization": "Basic " + auth,
                                                                      "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    achados = json.loads(resp.read().decode("utf-8") or "{}").get("incoming_phone_numbers") or []
                psid = achados[0].get("sid") if achados else ""
            except Exception:  # noqa: BLE001
                psid = ""
        if not psid:
            falhas.append(numero)
            continue
        status, _ = _twilio_post(sid, token, "IncomingPhoneNumbers/%s.json" % urllib.parse.quote(psid),
                                 {"SmsUrl": base + "/api/sms/entrada", "SmsMethod": "POST"})
        if 200 <= status < 300:
            feitos += 1
        else:
            falhas.append(numero)
    return {"configurados": feitos, "falhas": falhas}


def rotear_dono(h, method, path, conn):
    """Rotas /api/dono/sms* (o guarda do dono já rodou no server.py)."""
    if not path.startswith("/api/dono/sms"):
        return None
    ip = h._ip_cliente() if hasattr(h, "_ip_cliente") else ""
    try:
        if path == "/api/dono/sms":
            if method == "GET":
                return _resp(h, 200, painel_dono(conn))
            if method == "POST":
                salvar_dono(conn, h._body())
                g = config_global(conn)
                _auditar(conn, "sms_dono", "habilitado=%d a2p=%s" % (g["habilitado"], g["a2p"]["status"]),
                         ip=ip, quem="dono")
                conn.commit()
                return _resp(h, 200, dict(painel_dono(conn), ok=True))
        m = re.match(r"^/api/dono/sms/empresa/(\d+)$", path)
        if m and method == "POST":
            eid = int(m.group(1))
            if not _empresa(conn, eid):
                return _resp(h, 404, {"erro": "Empresa não encontrada"})
            cfg = validar_config_empresa({"ativo": h._body().get("ativo")}, config_empresa(conn, eid))
            _salvar_empresa(conn, eid, cfg)
            _auditar(conn, "sms_empresa", "ativo=%d" % cfg["ativo"], empresa_id=eid, ip=ip, quem="dono")
            conn.commit()
            return _resp(h, 200, dict(painel_dono(conn), ok=True))
        if path == "/api/dono/sms/webhooks" and method == "POST":
            return _resp(h, 200, dict(configurar_webhooks(conn), ok=True))
    except ErroSms as exc:
        return _resp(h, exc.status, {"erro": exc.mensagem})
    return _resp(h, 404, {"erro": "Rota não encontrada"})
