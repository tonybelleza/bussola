"""Agenda de entrevistas: o candidato escolhe o próprio horário.

Cada empresa define (Configurações, só o administrador) os dias da semana, a
janela do dia, a duração, o intervalo entre entrevistas, a antecedência mínima,
o horizonte, o limite por dia, o formato, o local ou as instruções, o nome de
quem entrevista, o fuso horário e as datas bloqueadas. Tudo fica em JSON na
chave de config "agenda:<empresa_id>".

Os horários são calculados no fuso da empresa e gravados em UTC
("AAAA-MM-DDTHH:MM:SSZ"). Cada candidato tem um link próprio
(/agendar?t=<candidatos.agenda_token>, criado quando é preciso) para marcar,
remarcar ou cancelar. Só uma entrevista ativa por candidato e um candidato por
horário na empresa: a marcação revalida o horário dentro de uma transação
(BEGIN IMMEDIATE) e o banco tem índices únicos parciais como segunda trava.

E-mails (candidato no idioma dele, gestores no idioma de cada um) levam um
convite .ics (METHOD:REQUEST ao marcar ou remarcar, METHOD:CANCEL ao cancelar).
Um lembrete único sai cerca de 24 horas antes.

Google Agenda (google_cal.py, opcional): os períodos ocupados das agendas
Google escolhidas pela empresa saem dos horários livres; marcar cria o evento
na agenda do entrevistador (com link do Google Meet na videochamada), remarcar
atualiza e cancelar apaga. Qualquer falha do Google volta aos horários normais.
"""
import json
import re
import secrets
import sys
import threading
import time
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

try:  # Google Agenda nos dois sentidos, com Google Meet (google_cal.py)
    import google_cal
except ImportError:  # pragma: no cover
    google_cal = None

srv = None  # módulo server, injetado por ligar()

# Envio dos e-mails em segundo plano (as rotas respondem na hora). Os testes desligam.
ENVIO_EM_SEGUNDO_PLANO = True
INTERVALO_LEMBRETES = 600  # segundos entre verificações de lembrete

FORMATOS = ("presencial", "telefone", "video")
STATUS = ("marcada", "cancelada", "realizada", "faltou")
FUSO_PADRAO = "America/New_York"

PADRAO = {
    "ativo": False,
    "dias": [1, 2, 3, 4, 5],          # isoweekday: 1 = segunda ... 7 = domingo
    "inicio": "09:00",
    "fim": "17:00",
    "duracao": 30,                     # minutos
    "intervalo": 0,                    # minutos entre entrevistas
    "antecedencia_horas": 12,
    "horizonte_dias": 14,
    "max_por_dia": 0,                  # 0 = sem limite
    "formato": "presencial",
    "local": "",
    "entrevistador": "",
    "fuso": "",                        # vazio = fuso da triagem por voz ou America/New_York
    "bloqueios": [],                   # ["AAAA-MM-DD", ...]
    "google_entrevistadores": [],      # ids dos gestores com Google Agenda conectado que valem para a agenda
    "google_organizador": 0,           # gestor em cuja agenda Google o evento é criado (0 = o primeiro)
}

# ------------------------------------------------------------- textos (pt, en, es)

T = {
    "pt": {
        "formatos": {"presencial": "Presencial", "telefone": "Ligação telefônica", "video": "Videochamada"},
        "dias_semana": ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"],
        "data_hora": "{semana}, {dia} de {mes} de {ano}, às {hora}",
        "rot_quando": "Quando", "rot_formato": "Formato", "rot_local": "Local / instruções",
        "rot_entrevistador": "Entrevistador(a)", "rot_duracao": "Duração", "duracao_min": "{n} minutos",
        "rot_candidato": "Candidato(a)",
        "botao_escolher": "Escolher horário da entrevista",
        "botao_gerenciar": "Remarcar ou cancelar",
        "botao_ficha": "Abrir ficha do candidato",
        "res_agenda": "Próximo passo: escolha o melhor horário para a sua entrevista. É rápido e você pode remarcar depois, se precisar.",
        "link_assunto": "Escolha o horário da sua entrevista",
        "link_titulo": "Vamos marcar a sua entrevista",
        "link_corpo": "Olá, {nome}! A equipe da {empresa} quer conversar com você. Escolha o dia e o horário que forem melhores para você:",
        "c_marcada_assunto": "Entrevista confirmada: {quando}",
        "c_marcada_titulo": "Entrevista confirmada",
        "c_marcada_corpo": "Olá, {nome}! A sua entrevista com a {empresa} está confirmada. O convite segue em anexo para você salvar na sua agenda.",
        "c_remarcada_assunto": "Entrevista remarcada: {quando}",
        "c_remarcada_titulo": "Entrevista remarcada",
        "c_remarcada_corpo": "Olá, {nome}! A sua entrevista com a {empresa} foi remarcada para o novo horário abaixo. O convite atualizado segue em anexo.",
        "c_cancelada_assunto": "Entrevista cancelada",
        "c_cancelada_titulo": "Entrevista cancelada",
        "c_cancelada_corpo": "Olá, {nome}. A sua entrevista com a {empresa} marcada para {quando} foi cancelada.",
        "c_cancelada_novo": "Se quiser, você pode escolher um novo horário pelo mesmo link:",
        "c_lembrete_assunto": "Lembrete: sua entrevista é amanhã",
        "c_lembrete_titulo": "Sua entrevista está chegando",
        "c_lembrete_corpo": "Olá, {nome}! Este é um lembrete da sua entrevista com a {empresa}.",
        "g_marcada_assunto": "Entrevista marcada: {nome}, {quando}",
        "g_remarcada_assunto": "Entrevista remarcada: {nome}, {quando}",
        "g_cancelada_assunto": "Entrevista cancelada: {nome}",
        "g_marcada_corpo": "{nome} escolheu um horário para a entrevista.",
        "g_remarcada_corpo": "{nome} remarcou a entrevista.",
        "g_cancelada_corpo": "A entrevista de {nome} marcada para {quando} foi cancelada.",
        "assinatura": "Até breve,\nEquipe {empresa}",
        "ics_resumo": "Entrevista: {empresa}",
        "ics_resumo_gestor": "Entrevista: {nome}",
        "ics_arquivo": "entrevista.ics",
        "rot_meet": "Link da videochamada (Google Meet)",
        "botao_meet": "Entrar na videochamada",
    },
    "en": {
        "formatos": {"presencial": "In person", "telefone": "Phone call", "video": "Video call"},
        "dias_semana": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "data_hora": "{semana}, {mes} {dia}, {ano} at {hora}",
        "rot_quando": "When", "rot_formato": "Format", "rot_local": "Location / instructions",
        "rot_entrevistador": "Interviewer", "rot_duracao": "Length", "duracao_min": "{n} minutes",
        "rot_candidato": "Candidate",
        "botao_escolher": "Choose your interview time",
        "botao_gerenciar": "Reschedule or cancel",
        "botao_ficha": "Open candidate profile",
        "res_agenda": "Next step: choose the best time for your interview. It only takes a minute, and you can reschedule later if you need to.",
        "link_assunto": "Choose your interview time",
        "link_titulo": "Let's schedule your interview",
        "link_corpo": "Hi {nome}! The {empresa} team would like to talk with you. Pick the day and time that work best for you:",
        "c_marcada_assunto": "Interview confirmed: {quando}",
        "c_marcada_titulo": "Interview confirmed",
        "c_marcada_corpo": "Hi {nome}! Your interview with {empresa} is confirmed. The calendar invite is attached so you can save it.",
        "c_remarcada_assunto": "Interview rescheduled: {quando}",
        "c_remarcada_titulo": "Interview rescheduled",
        "c_remarcada_corpo": "Hi {nome}! Your interview with {empresa} has been moved to the new time below. The updated calendar invite is attached.",
        "c_cancelada_assunto": "Interview canceled",
        "c_cancelada_titulo": "Interview canceled",
        "c_cancelada_corpo": "Hi {nome}. Your interview with {empresa} scheduled for {quando} has been canceled.",
        "c_cancelada_novo": "If you'd like, you can pick a new time with the same link:",
        "c_lembrete_assunto": "Reminder: your interview is tomorrow",
        "c_lembrete_titulo": "Your interview is coming up",
        "c_lembrete_corpo": "Hi {nome}! This is a reminder about your interview with {empresa}.",
        "g_marcada_assunto": "Interview scheduled: {nome}, {quando}",
        "g_remarcada_assunto": "Interview rescheduled: {nome}, {quando}",
        "g_cancelada_assunto": "Interview canceled: {nome}",
        "g_marcada_corpo": "{nome} picked a time for the interview.",
        "g_remarcada_corpo": "{nome} rescheduled the interview.",
        "g_cancelada_corpo": "The interview with {nome} scheduled for {quando} has been canceled.",
        "assinatura": "See you soon,\nThe {empresa} team",
        "ics_resumo": "Interview: {empresa}",
        "ics_resumo_gestor": "Interview: {nome}",
        "ics_arquivo": "interview.ics",
        "rot_meet": "Video call link (Google Meet)",
        "botao_meet": "Join the video call",
    },
    "es": {
        "formatos": {"presencial": "Presencial", "telefone": "Llamada telefónica", "video": "Videollamada"},
        "dias_semana": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
        "data_hora": "{semana} {dia} de {mes} de {ano}, a las {hora}",
        "rot_quando": "Cuándo", "rot_formato": "Formato", "rot_local": "Lugar / instrucciones",
        "rot_entrevistador": "Entrevistador(a)", "rot_duracao": "Duración", "duracao_min": "{n} minutos",
        "rot_candidato": "Candidato(a)",
        "botao_escolher": "Elige el horario de tu entrevista",
        "botao_gerenciar": "Cambiar o cancelar",
        "botao_ficha": "Abrir ficha del candidato",
        "res_agenda": "Siguiente paso: elige el mejor horario para tu entrevista. Es rápido y puedes cambiarlo después si lo necesitas.",
        "link_assunto": "Elige el horario de tu entrevista",
        "link_titulo": "Agendemos tu entrevista",
        "link_corpo": "¡Hola, {nome}! El equipo de {empresa} quiere conversar contigo. Elige el día y la hora que mejor te queden:",
        "c_marcada_assunto": "Entrevista confirmada: {quando}",
        "c_marcada_titulo": "Entrevista confirmada",
        "c_marcada_corpo": "¡Hola, {nome}! Tu entrevista con {empresa} está confirmada. Adjuntamos la invitación para que la guardes en tu calendario.",
        "c_remarcada_assunto": "Entrevista reprogramada: {quando}",
        "c_remarcada_titulo": "Entrevista reprogramada",
        "c_remarcada_corpo": "¡Hola, {nome}! Tu entrevista con {empresa} cambió al nuevo horario de abajo. Adjuntamos la invitación actualizada.",
        "c_cancelada_assunto": "Entrevista cancelada",
        "c_cancelada_titulo": "Entrevista cancelada",
        "c_cancelada_corpo": "Hola, {nome}. Tu entrevista con {empresa} del {quando} fue cancelada.",
        "c_cancelada_novo": "Si quieres, puedes elegir un nuevo horario con el mismo enlace:",
        "c_lembrete_assunto": "Recordatorio: tu entrevista es mañana",
        "c_lembrete_titulo": "Tu entrevista se acerca",
        "c_lembrete_corpo": "¡Hola, {nome}! Te recordamos tu entrevista con {empresa}.",
        "g_marcada_assunto": "Entrevista agendada: {nome}, {quando}",
        "g_remarcada_assunto": "Entrevista reprogramada: {nome}, {quando}",
        "g_cancelada_assunto": "Entrevista cancelada: {nome}",
        "g_marcada_corpo": "{nome} eligió un horario para la entrevista.",
        "g_remarcada_corpo": "{nome} reprogramó la entrevista.",
        "g_cancelada_corpo": "La entrevista de {nome} del {quando} fue cancelada.",
        "assinatura": "Hasta pronto,\nEquipo {empresa}",
        "ics_resumo": "Entrevista: {empresa}",
        "ics_resumo_gestor": "Entrevista: {nome}",
        "ics_arquivo": "entrevista.ics",
        "rot_meet": "Enlace de la videollamada (Google Meet)",
        "botao_meet": "Unirse a la videollamada",
    },
}

MESES_EN = ["January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"]


def ligar(modulo_server):
    global srv
    srv = modulo_server


def init_agenda(c):
    """Tabela entrevistas_agenda (o nome entrevistas já é das notas da entrevista estruturada), coluna candidatos.agenda_token e índices (migração no arranque)."""
    c.execute(
        "CREATE TABLE IF NOT EXISTS entrevistas_agenda ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,"
        " candidatura_id INTEGER REFERENCES candidaturas(id) ON DELETE SET NULL,"
        " inicio_utc TEXT NOT NULL,"
        " fim_utc TEXT NOT NULL,"
        " status TEXT NOT NULL DEFAULT 'marcada',"
        " token TEXT UNIQUE NOT NULL,"
        " sequencia INTEGER NOT NULL DEFAULT 0,"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " atualizado_em TEXT DEFAULT (datetime('now')),"
        " cancelada_em TEXT DEFAULT '',"
        " lembrete_enviado INTEGER NOT NULL DEFAULT 0)"
    )
    # segunda trava contra corrida: um candidato por horário na empresa e uma entrevista ativa por candidato
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_entrevistas_agenda_horario ON entrevistas_agenda(empresa_id, inicio_utc)"
              " WHERE status='marcada'")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_entrevistas_agenda_ativa ON entrevistas_agenda(candidato_id)"
              " WHERE status='marcada'")
    c.execute("CREATE INDEX IF NOT EXISTS ix_entrevistas_agenda_empresa ON entrevistas_agenda(empresa_id, status, inicio_utc)")
    if "agenda_token" not in {r[1] for r in c.execute("PRAGMA table_info(candidatos)").fetchall()}:
        c.execute("ALTER TABLE candidatos ADD COLUMN agenda_token TEXT DEFAULT ''")
    c.execute("CREATE INDEX IF NOT EXISTS ix_candidatos_agenda_token ON candidatos(agenda_token)")
    # Google Agenda: evento criado, gestor dono da agenda e link do Google Meet
    colunas = {r[1] for r in c.execute("PRAGMA table_info(entrevistas_agenda)").fetchall()}
    for coluna, tipo in (("google_evento_id", "TEXT DEFAULT ''"), ("google_gestor_id", "INTEGER DEFAULT 0"),
                         ("meet_link", "TEXT DEFAULT ''")):
        if coluna not in colunas:
            c.execute("ALTER TABLE entrevistas_agenda ADD COLUMN %s %s" % (coluna, tipo))
    if google_cal:
        google_cal.init_google(c)


# ------------------------------------------------------------- utilidades

def idioma(valor):
    return srv.mensagens.idioma(valor)


def t(lang, chave, **kw):
    texto = T[idioma(lang)].get(chave)
    if texto is None:
        texto = T["pt"][chave]
    return texto.format(**kw) if kw and isinstance(texto, str) else texto


def _agora():
    return datetime.now(timezone.utc)


def iso_utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ler_utc(texto):
    return datetime.strptime(texto, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _minutos(hhmm):
    h, m = str(hhmm).split(":")
    return int(h) * 60 + int(m)


def _hhmm_valido(v):
    return bool(re.match(r"^([01]\d|2[0-3]):[0-5]\d$", str(v or "")))


def zona(cfg):
    try:
        return ZoneInfo(cfg.get("fuso") or FUSO_PADRAO)
    except Exception:  # noqa: BLE001
        return ZoneInfo(FUSO_PADRAO)


def rotulo_fuso(cfg, quando=None):
    """Ex.: "New York (EDT)". A sigla muda com o horário de verão."""
    z = zona(cfg)
    quando = (quando or _agora()).astimezone(z)
    sigla = quando.strftime("%Z")
    if not re.match(r"^[A-Za-z]{2,5}$", sigla or ""):
        off = quando.strftime("%z")
        sigla = "UTC%s:%s" % (off[:3], off[3:])
    cidade = str(z.key).split("/")[-1].replace("_", " ")
    return "%s (%s)" % (cidade, sigla)


# ------------------------------------------------------------- configuração

def _chave(empresa_id):
    return "agenda:%d" % int(empresa_id)


def config(conn, empresa_id):
    cfg = dict(PADRAO)
    try:
        cfg.update(json.loads(srv.config_get(conn, _chave(empresa_id)) or "{}"))
    except ValueError:
        pass
    if not cfg.get("fuso"):
        try:
            cfg["fuso"] = srv.voz.config_empresa(conn, empresa_id).get("fuso") or FUSO_PADRAO
        except Exception:  # noqa: BLE001
            cfg["fuso"] = FUSO_PADRAO
    return cfg


def validar(d, atual):
    """Aplica os campos conhecidos de d sobre a configuração atual. Devolve (cfg, erro)."""
    cfg = dict(atual)
    if "ativo" in d:
        cfg["ativo"] = bool(d["ativo"])
    if "dias" in d:
        try:
            dias = sorted({int(x) for x in (d["dias"] or [])})
        except (TypeError, ValueError):
            return None, "Dias da semana inválidos"
        if any(x < 1 or x > 7 for x in dias):
            return None, "Dias da semana inválidos"
        cfg["dias"] = dias
    for campo in ("inicio", "fim"):
        if campo in d:
            if not _hhmm_valido(d[campo]):
                return None, "Horário inválido"
            cfg[campo] = str(d[campo])
    if _minutos(cfg["fim"]) <= _minutos(cfg["inicio"]):
        return None, "O fim da janela deve ser depois do início"
    limites = {"duracao": (5, 480), "intervalo": (0, 240), "antecedencia_horas": (0, 720),
               "horizonte_dias": (1, 180), "max_por_dia": (0, 200)}
    for campo, (minimo, maximo) in limites.items():
        if campo in d:
            valor = d[campo]
            if valor in (None, "") and campo == "max_por_dia":
                valor = 0
            try:
                valor = int(valor)
            except (TypeError, ValueError):
                return None, "Valor inválido na agenda"
            if valor < minimo or valor > maximo:
                return None, "Valor inválido na agenda"
            cfg[campo] = valor
    if "formato" in d:
        if d["formato"] not in FORMATOS:
            return None, "Formato de entrevista inválido"
        cfg["formato"] = d["formato"]
    for campo, tamanho in (("local", 500), ("entrevistador", 120)):
        if campo in d:
            cfg[campo] = str(d[campo] or "").strip()[:tamanho]
    if "fuso" in d:
        fuso = str(d["fuso"] or "").strip()
        if fuso:
            try:
                ZoneInfo(fuso)
            except Exception:  # noqa: BLE001
                return None, "Fuso horário inválido"
        cfg["fuso"] = fuso
    if "bloqueios" in d:
        itens = d["bloqueios"]
        if isinstance(itens, str):
            itens = re.split(r"[\s,;]+", itens)
        saida = []
        for item in itens or []:
            item = str(item or "").strip()
            if not item:
                continue
            try:
                date.fromisoformat(item)
            except ValueError:
                return None, "Data bloqueada inválida (use AAAA-MM-DD)"
            saida.append(item)
        cfg["bloqueios"] = sorted(set(saida))
    if "google_entrevistadores" in d:
        try:
            ids = [int(x) for x in (d["google_entrevistadores"] or [])]
        except (TypeError, ValueError):
            return None, "Entrevistador inválido"
        cfg["google_entrevistadores"] = list(dict.fromkeys(ids))[:20]
    if "google_organizador" in d:
        try:
            cfg["google_organizador"] = int(d["google_organizador"] or 0)
        except (TypeError, ValueError):
            return None, "Entrevistador inválido"
    if cfg.get("google_organizador") and cfg["google_organizador"] not in (cfg.get("google_entrevistadores") or []):
        cfg["google_organizador"] = 0
    if cfg["ativo"] and not cfg["dias"]:
        return None, "Escolha ao menos um dia da semana"
    return cfg, None


def salvar(conn, empresa_id, cfg):
    srv.config_set(conn, _chave(empresa_id), json.dumps(cfg, ensure_ascii=False))
    conn.commit()


# ------------------------------------------------------------- horários livres

def _ocupadas(conn, empresa_id, ignorar_id=None):
    return [(ler_utc(r["inicio_utc"]), ler_utc(r["fim_utc"])) for r in conn.execute(
        "SELECT inicio_utc, fim_utc FROM entrevistas_agenda WHERE empresa_id=? AND status='marcada' AND id!=?",
        (empresa_id, ignorar_id or 0)).fetchall()]


def gerar_horarios(cfg, ocupadas=(), agora=None, externos=()):
    """Horários livres [(inicio_utc, fim_utc, data_local, hora_local)] pelas regras da empresa.
    Os horários de parede (09:00, 09:30...) são montados no fuso da empresa, então
    continuam iguais na troca do horário de verão; horários que não existem no
    relógio local (pulo da primavera) são descartados.
    externos: períodos ocupados fora da Bússola (Google Agenda). Bloqueiam o
    horário (com o intervalo), mas não contam no limite de entrevistas por dia."""
    agora = agora or _agora()
    z = zona(cfg)
    duracao = timedelta(minutes=int(cfg["duracao"]))
    passo = int(cfg["duracao"]) + int(cfg.get("intervalo") or 0)
    gap = timedelta(minutes=int(cfg.get("intervalo") or 0))
    minimo = agora + timedelta(hours=int(cfg.get("antecedencia_horas") or 0))
    ini_min, fim_min = _minutos(cfg["inicio"]), _minutos(cfg["fim"])
    bloqueios = set(cfg.get("bloqueios") or [])
    dias = set(int(x) for x in (cfg.get("dias") or []))
    limite_dia = int(cfg.get("max_por_dia") or 0)
    hoje = agora.astimezone(z).date()
    ocupadas = list(ocupadas)
    externos = list(externos)
    por_dia = {}
    for ini, _fim in ocupadas:
        d = ini.astimezone(z).date()
        por_dia[d] = por_dia.get(d, 0) + 1
    saida = []
    for n in range(int(cfg.get("horizonte_dias") or 0) + 1):
        dia = hoje + timedelta(days=n)
        if dia.isoweekday() not in dias or dia.isoformat() in bloqueios:
            continue
        if limite_dia and por_dia.get(dia, 0) >= limite_dia:
            continue
        m = ini_min
        while m + int(cfg["duracao"]) <= fim_min:
            local = datetime(dia.year, dia.month, dia.day, m // 60, m % 60, tzinfo=z)
            inicio = local.astimezone(timezone.utc)
            m += passo
            # hora inexistente no relógio local (troca de horário): ida e volta não confere
            if inicio.astimezone(z).replace(tzinfo=None) != local.replace(tzinfo=None):
                continue
            fim = inicio + duracao
            if inicio < minimo:
                continue
            if any(inicio < o_fim + gap and o_ini < fim + gap for o_ini, o_fim in ocupadas):
                continue
            if any(inicio < o_fim + gap and o_ini < fim + gap for o_ini, o_fim in externos):
                continue
            saida.append((inicio, fim, dia.isoformat(), local.strftime("%H:%M")))
    return saida


def _subtrair(blocos, ini, fim):
    """Tira [ini, fim) de cada bloco (o próprio evento de quem está remarcando)."""
    saida = []
    for b_ini, b_fim in blocos:
        if b_fim <= ini or b_ini >= fim:
            saida.append((b_ini, b_fim))
            continue
        if b_ini < ini:
            saida.append((b_ini, ini))
        if b_fim > fim:
            saida.append((fim, b_fim))
    return saida


def google_ocupados(conn, empresa_id, cfg, ignorar_id=None, agora=None):
    """Períodos ocupados nas agendas Google escolhidas pela empresa (cache de 5 min
    no google_cal). Sem Google, sem contas ou com falha: lista vazia (horários normais)."""
    if not google_cal or not cfg.get("google_entrevistadores"):
        return []
    try:
        if not google_cal.configurado(conn):
            return []
        agora = agora or _agora()
        # janela arredondada (hora cheia até o fim do dia) para o cache servir às próximas consultas
        ini = agora.replace(minute=0, second=0, microsecond=0)
        fim_dia = (agora + timedelta(days=int(cfg.get("horizonte_dias") or 0) + 2)).astimezone(timezone.utc)
        fim = fim_dia.replace(hour=0, minute=0, second=0, microsecond=0)
        blocos = google_cal.ocupados(conn, empresa_id, cfg["google_entrevistadores"], ini, fim)
        if ignorar_id:
            atual = conn.execute("SELECT inicio_utc, fim_utc FROM entrevistas_agenda WHERE id=?", (ignorar_id,)).fetchone()
            if atual:
                blocos = _subtrair(blocos, ler_utc(atual["inicio_utc"]), ler_utc(atual["fim_utc"]))
        return blocos
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("Agenda: Google Agenda indisponível: %s\n" % type(exc).__name__)
        return []


def horarios_livres(conn, empresa_id, cfg=None, ignorar_id=None, agora=None):
    cfg = cfg or config(conn, empresa_id)
    return gerar_horarios(cfg, _ocupadas(conn, empresa_id, ignorar_id), agora,
                          google_ocupados(conn, empresa_id, cfg, ignorar_id, agora))


def agrupar_por_dia(horarios):
    dias = []
    for inicio, fim, data_local, hora in horarios:
        if not dias or dias[-1]["data"] != data_local:
            dias.append({"data": data_local, "horarios": []})
        dias[-1]["horarios"].append({"inicio_utc": iso_utc(inicio), "fim_utc": iso_utc(fim), "hora": hora})
    return dias


# ------------------------------------------------------------- candidato, token e qualificação

def token_do_candidato(conn, cand_id):
    """Token de agendamento do candidato (separado do token do portal), criado na primeira vez."""
    r = conn.execute("SELECT agenda_token FROM candidatos WHERE id=?", (cand_id,)).fetchone()
    if r and r["agenda_token"]:
        return r["agenda_token"]
    token = secrets.token_urlsafe(24)
    conn.execute("UPDATE candidatos SET agenda_token=? WHERE id=? AND (agenda_token IS NULL OR agenda_token='')",
                 (token, cand_id))
    conn.commit()
    return conn.execute("SELECT agenda_token FROM candidatos WHERE id=?", (cand_id,)).fetchone()["agenda_token"]


def link(conn, cand):
    lang = idioma(cand["idioma"] if "idioma" in cand.keys() else "")
    return "%s/agendar?t=%s&lang=%s" % (srv.url_publica(conn), token_do_candidato(conn, cand["id"]), lang)


def candidato_do_token(conn, token):
    """Candidato (com empresa ativa) dono do token de agendamento, ou do token de uma entrevista."""
    token = (token or "").strip()
    if len(token) < 16:
        return None
    sql = ("SELECT c.* FROM candidatos c JOIN empresas e ON e.id=c.empresa_id"
           " WHERE %s AND c.anonimizado=0 AND e.status IN ('ativa','teste')")
    cand = conn.execute(sql % "c.agenda_token=?", (token,)).fetchone()
    if not cand:
        cand = conn.execute(sql % "c.id=(SELECT candidato_id FROM entrevistas_agenda WHERE token=?)", (token,)).fetchone()
    return cand


def qualifica(conn, cand):
    """Recebe o link automático no e-mail de resultados quando a agenda da empresa
    está ligada e: tem triagem por voz STRONG ou GOOD em alguma candidatura, ou o
    cargo dele não usa triagem por voz (cargos.voz_ativa 0 ou vazio, ou a empresa
    sem o módulo de voz)."""
    if not cand["empresa_id"] or not config(conn, cand["empresa_id"]).get("ativo"):
        return False
    if "anonimizado" in cand.keys() and cand["anonimizado"]:
        return False
    if conn.execute("SELECT 1 FROM candidaturas WHERE candidato_id=? AND voz_tier IN ('STRONG','GOOD') LIMIT 1",
                    (cand["id"],)).fetchone():
        return True
    emp = conn.execute("SELECT modulos FROM empresas WHERE id=?", (cand["empresa_id"],)).fetchone()
    if "voz" not in srv.empresas.modulos(emp):
        return True
    cargos = {cand["cargo_desejado_id"]} if cand["cargo_desejado_id"] else set()
    cargos |= {r["cargo_id"] for r in conn.execute(
        "SELECT v.cargo_id FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id WHERE ca.candidato_id=?",
        (cand["id"],)).fetchall() if r["cargo_id"]}
    if not cargos:
        return True
    marcas = ",".join("?" * len(cargos))
    com_voz = conn.execute("SELECT 1 FROM cargos WHERE id IN (%s) AND voz_ativa=1 LIMIT 1" % marcas,
                           list(cargos)).fetchone()
    return not com_voz


def bloco_resultado(conn, cand, lang):
    """(linhas de texto, html) com o botão "Escolher horário" para o e-mail de
    resultados, ou ([], "") quando o candidato não se qualifica."""
    try:
        if not qualifica(conn, cand):
            return [], ""
        url = link(conn, cand)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("Agenda: link no e-mail de resultados falhou: %r\n" % exc)
        return [], ""
    m = srv.mensagens
    html = ('<div style="background:#eef4ff;border:1px solid #cddcf7;border-radius:14px;padding:16px 18px;margin:18px 0">'
            + m._paragrafo(t(lang, "res_agenda"), "#101B37", 15)
            + m._botao(url, t(lang, "botao_escolher"), "#2E9E6A") + '</div>')
    return [t(lang, "res_agenda"), "", url, ""], html


def entrevista_ativa(conn, cand_id):
    return conn.execute("SELECT * FROM entrevistas_agenda WHERE candidato_id=? AND status='marcada'"
                        " ORDER BY inicio_utc DESC LIMIT 1", (cand_id,)).fetchone()


def _candidatura_recente(conn, cand):
    r = conn.execute(
        "SELECT ca.id FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
        " WHERE ca.candidato_id=? AND v.empresa_id=? AND ca.etapa!='reprovado'"
        " ORDER BY ca.criado_em DESC, ca.id DESC LIMIT 1", (cand["id"], cand["empresa_id"])).fetchone()
    return r["id"] if r else None


# ------------------------------------------------------------- marcar, remarcar, cancelar

class ErroAgenda(Exception):
    def __init__(self, status, mensagem):
        Exception.__init__(self, mensagem)
        self.status = status
        self.mensagem = mensagem


def marcar(conn, cand, inicio_texto, agora=None):
    """Marca (ou remarca, se já houver uma ativa) no horário pedido. Revalida o
    horário dentro de BEGIN IMMEDIATE: dois pedidos ao mesmo tempo não pegam o
    mesmo horário. Devolve (entrevista, "marcada" | "remarcada")."""
    try:
        inicio = ler_utc(str(inicio_texto or ""))
    except ValueError:
        raise ErroAgenda(400, "Horário inválido")
    empresa_id = cand["empresa_id"]
    cfg = config(conn, empresa_id)
    if not cfg.get("ativo"):
        raise ErroAgenda(400, "A agenda de entrevistas está desativada")
    # Google Agenda antes da transação (chamada de rede nunca segura a trava do banco)
    antes = entrevista_ativa(conn, cand["id"])
    externos = google_ocupados(conn, empresa_id, cfg, antes["id"] if antes else None, agora)
    conn.commit()
    conn.execute("BEGIN IMMEDIATE")
    try:
        atual = entrevista_ativa(conn, cand["id"])
        if atual and ler_utc(atual["inicio_utc"]) == inicio:
            conn.rollback()
            return atual, "sem_mudanca"
        livres = gerar_horarios(cfg, _ocupadas(conn, empresa_id, atual["id"] if atual else None), agora, externos)
        escolhido = next((h for h in livres if h[0] == inicio), None)
        if not escolhido:
            raise ErroAgenda(409, "Este horário não está mais disponível")
        fim = escolhido[1]
        # lembrete: se faltar menos de 24 horas, a própria confirmação já serve de lembrete
        perto = (inicio - (agora or _agora())) <= timedelta(hours=24)
        if atual:
            conn.execute(
                "UPDATE entrevistas_agenda SET inicio_utc=?, fim_utc=?, sequencia=sequencia+1,"
                " atualizado_em=datetime('now'), lembrete_enviado=? WHERE id=?",
                (iso_utc(inicio), iso_utc(fim), 1 if perto else 0, atual["id"]))
            eid, acao = atual["id"], "remarcada"
        else:
            eid = conn.execute(
                "INSERT INTO entrevistas_agenda (empresa_id, candidato_id, candidatura_id, inicio_utc, fim_utc,"
                " status, token, lembrete_enviado) VALUES (?,?,?,?,?,'marcada',?,?)",
                (empresa_id, cand["id"], _candidatura_recente(conn, cand), iso_utc(inicio), iso_utc(fim),
                 secrets.token_urlsafe(24), 1 if perto else 0)).lastrowid
            acao = "marcada"
        ent = conn.execute("SELECT * FROM entrevistas_agenda WHERE id=?", (eid,)).fetchone()
        quando = formatar(cfg, inicio, "pt")
        srv.registrar_evento(conn, cand["id"], "entrevista",
                             ("Entrevista marcada pelo candidato: %s" if acao == "marcada"
                              else "Entrevista remarcada pelo candidato: %s") % quando)
        _mover_para_entrevista(conn, cand, ent)
        conn.commit()
    except ErroAgenda:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        if "UNIQUE" in str(exc):
            raise ErroAgenda(409, "Este horário não está mais disponível")
        raise
    sincronizar_google(conn, ent["id"], acao)
    ent = conn.execute("SELECT * FROM entrevistas_agenda WHERE id=?", (ent["id"],)).fetchone()
    avisar(conn, ent["id"], acao)
    return ent, acao


def _mover_para_entrevista(conn, cand, ent):
    """A candidatura da entrevista (ou, sem ela, as do candidato nesta empresa) vai
    para a etapa Entrevista se ainda estava em Inscrito ou Avaliações."""
    if ent["candidatura_id"]:
        alvo = conn.execute("SELECT ca.id, ca.etapa, v.titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                            " WHERE ca.id=?", (ent["candidatura_id"],)).fetchall()
    else:
        alvo = conn.execute("SELECT ca.id, ca.etapa, v.titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                            " WHERE ca.candidato_id=? AND v.empresa_id=?", (cand["id"], cand["empresa_id"])).fetchall()
    for ca in alvo:
        if ca["etapa"] in ("inscrito", "avaliacoes"):
            conn.execute("UPDATE candidaturas SET etapa='entrevista', atualizado_em=datetime('now') WHERE id=?",
                         (ca["id"],))
            srv.registrar_evento(conn, cand["id"], "etapa", "Vaga %s: movido para %s" % (
                ca["titulo"], srv.NOMES_ETAPAS.get("entrevista", "Entrevista")))


def cancelar(conn, ent, autor="candidato"):
    """Cancela uma entrevista marcada e avisa todos. Devolve True se cancelou."""
    feito = conn.execute(
        "UPDATE entrevistas_agenda SET status='cancelada', cancelada_em=datetime('now'), atualizado_em=datetime('now'),"
        " sequencia=sequencia+1 WHERE id=? AND status='marcada'", (ent["id"],)).rowcount
    if not feito:
        return False
    cfg = config(conn, ent["empresa_id"])
    srv.registrar_evento(conn, ent["candidato_id"], "entrevista",
                         "Entrevista cancelada (%s): %s" % (
                             "pelo candidato" if autor == "candidato" else autor,
                             formatar(cfg, ler_utc(ent["inicio_utc"]), "pt")),
                         "sistema" if autor == "candidato" else autor)
    conn.commit()
    sincronizar_google(conn, ent["id"], "cancelada")
    avisar(conn, ent["id"], "cancelada")
    return True


def mudar_status(conn, ent, status, gestor):
    if status not in STATUS or status == "marcada":
        raise ErroAgenda(400, "Status inválido")
    if status == "cancelada":
        if not cancelar(conn, ent, gestor["nome"]):
            raise ErroAgenda(400, "Esta entrevista não está mais marcada")
        return
    if ent["status"] not in ("marcada", "realizada", "faltou"):
        raise ErroAgenda(400, "Esta entrevista não está mais marcada")
    conn.execute("UPDATE entrevistas_agenda SET status=?, atualizado_em=datetime('now') WHERE id=?", (status, ent["id"]))
    srv.registrar_evento(conn, ent["candidato_id"], "entrevista",
                         "Entrevista %s" % ("realizada" if status == "realizada" else "marcada como falta (não compareceu)"),
                         gestor["nome"])
    conn.commit()


# ------------------------------------------------------------- Google Agenda (google_cal.py)

def _meet(ent):
    return (ent["meet_link"] or "") if ent is not None and "meet_link" in ent.keys() else ""


def _vaga_da_entrevista(conn, ent, cand):
    if ent["candidatura_id"]:
        r = conn.execute("SELECT v.titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id WHERE ca.id=?",
                         (ent["candidatura_id"],)).fetchone()
        if r and r["titulo"]:
            return r["titulo"]
    if cand["cargo_desejado_id"]:
        r = conn.execute("SELECT nome FROM cargos WHERE id=?", (cand["cargo_desejado_id"],)).fetchone()
        if r:
            return r["nome"]
    return ""


def organizador_google(conn, empresa_id, cfg):
    """Conta Google ativa onde o evento é criado: a escolhida, senão a primeira ativa da lista."""
    ids = list(cfg.get("google_entrevistadores") or [])
    if not ids:
        return None
    ordem = ([cfg["google_organizador"]] if cfg.get("google_organizador") in ids else []) + ids
    for row in google_cal.contas_validas(conn, empresa_id, ordem):
        if row["status"] == "ativa":
            return row
    return None


def corpo_evento_google(conn, ent, cfg, gestor_id, meet):
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ent["candidato_id"],)).fetchone()
    g = conn.execute("SELECT idioma FROM gestores WHERE id=?", (gestor_id,)).fetchone()
    lang = idioma(g["idioma"] if g else "pt")
    tt = google_cal.T.get(lang) or google_cal.T["pt"]
    ficha = "%s/gestor#candidato=%d" % (srv.url_publica(conn), cand["id"])
    linhas = ["%s: %s" % (tt["ficha"], ficha),
              "%s: %s" % (tt["formato"], t(lang, "formatos").get(cfg["formato"], cfg["formato"]))]
    if cfg.get("local"):
        linhas.append("%s: %s" % (tt["local"], cfg["local"]))
    linhas += ["", tt["rodape"]]
    return google_cal.corpo_evento(
        google_cal.titulo_evento(lang, cand["nome"] or "", _vaga_da_entrevista(conn, ent, cand)),
        "\n".join(linhas), ler_utc(ent["inicio_utc"]), ler_utc(ent["fim_utc"]), zona(cfg).key,
        (cand["email"] or "").strip(), cand["nome"] or "",
        cfg.get("local") if cfg["formato"] == "presencial" else "",
        meet, "bussola-%d-%d" % (ent["id"], int(ent["sequencia"] or 0)))


def sincronizar_google(conn, entrevista_id, acao):
    """Cria (marcada), atualiza (remarcada) ou apaga (cancelada) o evento no Google
    Agenda. Nunca lança exceção: sem Google, a agenda segue com os próprios e-mails."""
    if not google_cal:
        return
    try:
        _sincronizar_google(conn, entrevista_id, acao)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("Agenda: sincronização com o Google Agenda falhou: %s\n" % type(exc).__name__)


def _sincronizar_google(conn, entrevista_id, acao):
    ent = conn.execute("SELECT * FROM entrevistas_agenda WHERE id=?", (entrevista_id,)).fetchone()
    if not ent:
        return
    evento_id, dono = ent["google_evento_id"] or "", int(ent["google_gestor_id"] or 0)
    falha = "Google Agenda: não foi possível sincronizar o evento"
    if acao == "cancelada":
        if not (evento_id and dono):
            return
        if google_cal.apagar_evento(conn, dono, evento_id):
            conn.execute("UPDATE entrevistas_agenda SET google_evento_id='' WHERE id=?", (ent["id"],))
            srv.registrar_evento(conn, ent["candidato_id"], "entrevista", "Google Agenda: evento removido")
        else:
            srv.registrar_evento(conn, ent["candidato_id"], "entrevista", falha)
        conn.commit()
        return
    if not google_cal.configurado(conn):
        return
    cfg = config(conn, ent["empresa_id"])
    video = cfg["formato"] == "video"
    if evento_id and dono:
        corpo = corpo_evento_google(conn, ent, cfg, dono, video and not _meet(ent))
        ok, meet = google_cal.atualizar_evento(conn, dono, evento_id, corpo)
        if ok:
            conn.execute("UPDATE entrevistas_agenda SET meet_link=? WHERE id=?", (meet or _meet(ent), ent["id"]))
            srv.registrar_evento(conn, ent["candidato_id"], "entrevista", "Google Agenda: evento atualizado")
        else:
            srv.registrar_evento(conn, ent["candidato_id"], "entrevista", falha)
        conn.commit()
        return
    org = organizador_google(conn, ent["empresa_id"], cfg)
    if not org:
        return
    novo_id, meet = google_cal.criar_evento(conn, org["gestor_id"], corpo_evento_google(conn, ent, cfg, org["gestor_id"], video))
    if novo_id:
        conn.execute("UPDATE entrevistas_agenda SET google_evento_id=?, google_gestor_id=?, meet_link=? WHERE id=?",
                     (novo_id, org["gestor_id"], meet or "", ent["id"]))
        srv.registrar_evento(conn, ent["candidato_id"], "entrevista",
                             "Google Agenda: evento criado com link do Google Meet" if meet else "Google Agenda: evento criado")
    else:
        srv.registrar_evento(conn, ent["candidato_id"], "entrevista", falha)
    conn.commit()


# ------------------------------------------------------------- textos de data

def formatar(cfg, quando_utc, lang):
    """Data e hora por extenso no fuso da empresa, com a sigla do fuso."""
    lang = idioma(lang)
    local = quando_utc.astimezone(zona(cfg))
    semana = T[lang]["dias_semana"][local.isoweekday() - 1]
    if lang == "en":
        mes = MESES_EN[local.month - 1]
        hora = local.strftime("%I:%M %p").lstrip("0")
    else:
        mes = srv.mensagens.T[lang]["meses"][local.month - 1]
        hora = local.strftime("%H:%M")
    texto = T[lang]["data_hora"].format(semana=semana, dia=local.day, mes=mes, ano=local.year, hora=hora)
    return "%s · %s" % (texto, rotulo_fuso(cfg, quando_utc))


# ------------------------------------------------------------- convite .ics

def _ics_texto(v):
    return (str(v or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\\n").replace("\n", "\\n"))


def _ics_dobrar(linha):
    """Linhas de no máximo 75 octetos (RFC 5545), continuação com espaço."""
    dados = linha.encode("utf-8")
    if len(dados) <= 75:
        return linha
    partes, atual = [], b""
    for ch in linha:
        b = ch.encode("utf-8")
        if len(atual) + len(b) > (75 if not partes else 74):
            partes.append(atual.decode("utf-8"))
            atual = b""
        atual += b
    partes.append(atual.decode("utf-8"))
    return "\r\n ".join(partes)


def gerar_ics(conn, ent, lang, para_gestor=False, cancelar_evento=False):
    """Convite de calendário (bytes). UID estável por entrevista; SEQUENCE sobe a
    cada remarcação ou cancelamento para o calendário atualizar o mesmo evento."""
    cfg = config(conn, ent["empresa_id"])
    cand = conn.execute("SELECT nome, email FROM candidatos WHERE id=?", (ent["candidato_id"],)).fetchone()
    m = srv.mensagens.marca(conn, ent["empresa_id"]) or {}
    empresa = m.get("nome") or ""
    host = re.sub(r"^https?://", "", srv.url_publica(conn)).split("/")[0] or "bussola"
    remetente = (srv.config_get(conn, "smtp_remetente") or srv.config_get(conn, "smtp_usuario") or "").strip()
    if "<" in remetente:
        remetente = remetente.split("<", 1)[1].rstrip(">").strip()
    resumo = (t(lang, "ics_resumo_gestor", nome=cand["nome"]) if para_gestor
              else t(lang, "ics_resumo", empresa=empresa))
    descricao = [t(lang, "rot_formato") + ": " + t(lang, "formatos").get(cfg["formato"], cfg["formato"])]
    if cfg.get("entrevistador"):
        descricao.append(t(lang, "rot_entrevistador") + ": " + cfg["entrevistador"])
    if cfg.get("local"):
        descricao.append(t(lang, "rot_local") + ": " + cfg["local"])
    meet = _meet(ent) if not cancelar_evento else ""
    if meet:
        descricao.append(t(lang, "rot_meet") + ": " + meet)
    if para_gestor:
        descricao.append(t(lang, "rot_candidato") + ": " + cand["nome"] + (" <%s>" % cand["email"] if cand["email"] else ""))
    linhas = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Bussola//Agenda de entrevistas//PT", "CALSCALE:GREGORIAN",
        "METHOD:" + ("CANCEL" if cancelar_evento else "REQUEST"),
        "BEGIN:VEVENT",
        "UID:entrevista-%d@%s" % (ent["id"], host),
        "SEQUENCE:%d" % int(ent["sequencia"] or 0),
        "DTSTAMP:" + _agora().strftime("%Y%m%dT%H%M%SZ"),
        "DTSTART:" + ler_utc(ent["inicio_utc"]).strftime("%Y%m%dT%H%M%SZ"),
        "DTEND:" + ler_utc(ent["fim_utc"]).strftime("%Y%m%dT%H%M%SZ"),
        "SUMMARY:" + _ics_texto(resumo),
        "DESCRIPTION:" + _ics_texto("\n".join(descricao)),
    ]
    if meet and cfg["formato"] == "video":
        linhas.append("LOCATION:" + _ics_texto(meet))
    elif cfg.get("local"):
        linhas.append("LOCATION:" + _ics_texto(cfg["local"]))
    if meet:
        linhas.append("URL:" + meet)
    if remetente:
        linhas.append("ORGANIZER;CN=%s:mailto:%s" % (_ics_texto(empresa or "Bussola"), remetente))
    if cand["email"]:
        linhas.append("ATTENDEE;CN=%s;ROLE=REQ-PARTICIPANT;RSVP=FALSE:mailto:%s" % (_ics_texto(cand["nome"]), cand["email"]))
    linhas += ["STATUS:" + ("CANCELLED" if cancelar_evento else "CONFIRMED"), "TRANSP:OPAQUE",
               "END:VEVENT", "END:VCALENDAR"]
    return ("\r\n".join(_ics_dobrar(l) for l in linhas) + "\r\n").encode("utf-8")


# ------------------------------------------------------------- e-mails

def _detalhes_html(cfg, ent, lang, com_candidato=None):
    m = srv.mensagens
    linhas = m._linha(t(lang, "rot_quando"), formatar(cfg, ler_utc(ent["inicio_utc"]), lang))
    linhas += m._linha(t(lang, "rot_duracao"), t(lang, "duracao_min", n=cfg["duracao"]))
    linhas += m._linha(t(lang, "rot_formato"), t(lang, "formatos").get(cfg["formato"], cfg["formato"]))
    linhas += m._linha(t(lang, "rot_local"), cfg.get("local"))
    linhas += m._linha(t(lang, "rot_entrevistador"), cfg.get("entrevistador"))
    linhas += m._linha(t(lang, "rot_meet"), _meet(ent))
    if com_candidato:
        linhas += m._linha(t(lang, "rot_candidato"), com_candidato)
    return ('<div style="background:#f5f7fb;border-radius:12px;padding:12px 16px;margin:6px 0 16px">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">' + linhas + '</table></div>')


def _detalhes_texto(cfg, ent, lang):
    saida = ["%s: %s" % (t(lang, "rot_quando"), formatar(cfg, ler_utc(ent["inicio_utc"]), lang)),
             "%s: %s" % (t(lang, "rot_formato"), t(lang, "formatos").get(cfg["formato"], cfg["formato"]))]
    if cfg.get("local"):
        saida.append("%s: %s" % (t(lang, "rot_local"), cfg["local"]))
    if cfg.get("entrevistador"):
        saida.append("%s: %s" % (t(lang, "rot_entrevistador"), cfg["entrevistador"]))
    if _meet(ent):
        saida.append("%s: %s" % (t(lang, "rot_meet"), _meet(ent)))
    return saida


def email_candidato(conn, ent, acao):
    """(assunto, texto, html, anexos) ao candidato no idioma dele.
    acao: marcada, remarcada, cancelada ou lembrete."""
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ent["candidato_id"],)).fetchone()
    lang = idioma(cand["idioma"])
    cfg = config(conn, ent["empresa_id"])
    m = srv.mensagens
    marca = m.marca(conn, ent["empresa_id"])
    empresa = (marca or {}).get("nome") or m.t(lang, "equipe")
    primeiro = (cand["nome"] or "").split(" ")[0]
    quando = formatar(cfg, ler_utc(ent["inicio_utc"]), lang)
    url = link(conn, cand)
    pre = {"marcada": "c_marcada", "remarcada": "c_remarcada", "cancelada": "c_cancelada", "lembrete": "c_lembrete"}[acao]
    assunto = t(lang, pre + "_assunto", quando=quando)
    intro = t(lang, pre + "_corpo", nome=primeiro, empresa=empresa, quando=quando)
    texto = [intro, ""]
    corpo = [m._paragrafo(intro)]
    if acao == "cancelada":
        if config(conn, ent["empresa_id"]).get("ativo"):
            texto += [t(lang, "c_cancelada_novo"), "", url, ""]
            corpo.append(m._paragrafo(t(lang, "c_cancelada_novo"), "#4a5568", 14))
            corpo.append(m._botao(url, t(lang, "botao_escolher")))
    else:
        texto += _detalhes_texto(cfg, ent, lang) + ["", t(lang, "botao_gerenciar") + ":", url, ""]
        corpo.append(_detalhes_html(cfg, ent, lang))
        if _meet(ent):
            corpo.append(m._botao(_meet(ent), t(lang, "botao_meet"), "#2E9E6A"))
        corpo.append(m._botao(url, t(lang, "botao_gerenciar"), "#5E7086"))
    texto.append(t(lang, "assinatura", empresa=empresa))
    corpo.append(m._paragrafo(t(lang, "assinatura", empresa=empresa), "#4a5568", 14))
    cor = {"cancelada": "#C0392B", "lembrete": "#C79A3E"}.get(acao, "#2E9E6A")
    icone = {"cancelada": "✖", "lembrete": "⏰"}.get(acao, "📅")
    html = m.layout("".join(corpo), lang, marca, (icone, t(lang, pre + "_titulo"), cor))
    anexos = [(t(lang, "ics_arquivo"), gerar_ics(conn, ent, lang, cancelar_evento=(acao == "cancelada")), "text/calendar")]
    return assunto, "\n".join(texto), html, anexos


def email_gestor(conn, ent, acao, lang):
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ent["candidato_id"],)).fetchone()
    lang = idioma(lang)
    cfg = config(conn, ent["empresa_id"])
    m = srv.mensagens
    marca = m.marca(conn, ent["empresa_id"])
    quando = formatar(cfg, ler_utc(ent["inicio_utc"]), lang)
    nome = cand["nome"] or ""
    assunto = t(lang, "g_%s_assunto" % acao, nome=nome, quando=quando)
    intro = t(lang, "g_%s_corpo" % acao, nome=nome, quando=quando)
    ficha = "%s/gestor#candidato=%d" % (srv.url_publica(conn), cand["id"])
    contato = " · ".join(x for x in (cand["email"], cand["telefone"]) if x)
    texto = [intro, ""] + _detalhes_texto(cfg, ent, lang) + ["%s: %s" % (t(lang, "rot_candidato"), nome + (" (%s)" % contato if contato else "")), "", ficha]
    corpo = (m._paragrafo(intro) + _detalhes_html(cfg, ent, lang, nome + (" (%s)" % contato if contato else ""))
             + m._botao(ficha, t(lang, "botao_ficha")))
    cor = "#C0392B" if acao == "cancelada" else "#3B67CA"
    html = m.layout(corpo, lang, marca, ("✖" if acao == "cancelada" else "📅", assunto, cor))
    anexos = [(t(lang, "ics_arquivo"), gerar_ics(conn, ent, lang, para_gestor=True,
                                                 cancelar_evento=(acao == "cancelada")), "text/calendar")]
    return assunto, "\n".join(texto), html, anexos


def _enviar_avisos(conn, entrevista_id, acao):
    ent = conn.execute("SELECT * FROM entrevistas_agenda WHERE id=?", (entrevista_id,)).fetchone()
    if not ent or not srv.config_get(conn, "smtp_host"):
        return 0
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ent["candidato_id"],)).fetchone()
    enviados = 0
    if (cand["email"] or "").strip():
        assunto, texto, html, anexos = email_candidato(conn, ent, acao)
        ok, _ = srv.enviar_email(conn, cand["email"].strip(), assunto, texto, anexos=anexos, html=html)
        enviados += 1 if ok else 0
    gestores = 0
    for g in conn.execute("SELECT email, local, is_admin, empresa_id, idioma FROM gestores"
                          " WHERE empresa_id=? AND aprovado=1", (ent["empresa_id"],)).fetchall():
        if not (g["email"] or "").strip() or not srv.empresas.ve_local(g, cand["local"]):
            continue
        assunto, texto, html, anexos = email_gestor(conn, ent, acao, g["idioma"])
        ok, _ = srv.enviar_email(conn, g["email"].strip(), assunto, texto, anexos=anexos, html=html)
        gestores += 1 if ok else 0
    srv.registrar_evento(conn, cand["id"], "email", "Entrevista %s: e-mail ao candidato%s e a %d gestor(es)" % (
        acao, "" if enviados else " não enviado", gestores))
    conn.commit()
    return enviados + gestores


def _em_segundo_plano(funcao, *args):
    def rodar():
        conn = srv.db()
        try:
            funcao(conn, *args)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Agenda: envio falhou: %r\n" % exc)
        finally:
            conn.close()
    threading.Thread(target=rodar, daemon=True).start()


def avisar(conn, entrevista_id, acao):
    """E-mails da marcação, remarcação ou cancelamento (candidato e gestores)."""
    if acao not in ("marcada", "remarcada", "cancelada"):
        return
    if ENVIO_EM_SEGUNDO_PLANO:
        _em_segundo_plano(_enviar_avisos, entrevista_id, acao)
    else:
        _enviar_avisos(conn, entrevista_id, acao)


def enviar_link(conn, cand, autor="sistema"):
    """E-mail curto com o link de agendamento, no idioma do candidato. Devolve (ok, msg)."""
    lang = idioma(cand["idioma"])
    m = srv.mensagens
    marca = m.marca(conn, cand["empresa_id"])
    empresa = (marca or {}).get("nome") or m.t(lang, "equipe")
    url = link(conn, cand)
    primeiro = (cand["nome"] or "").split(" ")[0]
    intro = t(lang, "link_corpo", nome=primeiro, empresa=empresa)
    cfg = config(conn, cand["empresa_id"])
    detalhes = [m._linha(t(lang, "rot_formato"), t(lang, "formatos").get(cfg["formato"], cfg["formato"])),
                m._linha(t(lang, "rot_duracao"), t(lang, "duracao_min", n=cfg["duracao"]))]
    corpo = (m._paragrafo(intro) + m._botao(url, t(lang, "botao_escolher"), "#2E9E6A")
             + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">' + "".join(detalhes) + '</table>'
             + '<div style="height:12px"></div>'
             + m._paragrafo(t(lang, "assinatura", empresa=empresa), "#4a5568", 14))
    texto = "\n".join([intro, "", url, "", t(lang, "assinatura", empresa=empresa)])
    html = m.layout(corpo, lang, marca, ("📅", t(lang, "link_titulo"), "#3B67CA"))
    ok, msg = srv.enviar_email(conn, cand["email"].strip(), t(lang, "link_assunto"), texto, html=html)
    if ok:
        srv.registrar_evento(conn, cand["id"], "email", "Link de agendamento de entrevista enviado (%s)" % lang, autor)
        conn.commit()
    return ok, msg


# ------------------------------------------------------------- lembrete

def enviar_lembretes(conn, agora=None):
    """Lembrete único ao candidato cerca de 24 horas antes da entrevista (e-mail e SMS)."""
    tem_smtp = bool(srv.config_get(conn, "smtp_host"))
    tem_sms = getattr(srv, "sms", None) is not None
    if not tem_smtp and not tem_sms:
        return 0
    agora = agora or _agora()
    enviados = 0
    for ent in conn.execute(
            "SELECT * FROM entrevistas_agenda WHERE status='marcada' AND lembrete_enviado=0 AND inicio_utc>? AND inicio_utc<=?",
            (iso_utc(agora), iso_utc(agora + timedelta(hours=24)))).fetchall():
        # marca antes de enviar (atômico): duas rotinas nunca mandam o mesmo lembrete
        if not conn.execute("UPDATE entrevistas_agenda SET lembrete_enviado=1 WHERE id=? AND lembrete_enviado=0",
                            (ent["id"],)).rowcount:
            continue
        conn.commit()
        if tem_sms:
            try:
                local = ler_utc(ent["inicio_utc"]).astimezone(zona(config(conn, ent["empresa_id"])))
                srv.sms.enviar_modelo(conn, ent["candidato_id"], "lembrete_entrevista",
                                      {"data": local.strftime("%m/%d"), "hora": local.strftime("%I:%M %p").lstrip("0")})
            except Exception:  # noqa: BLE001  (o SMS nunca impede o e-mail)
                pass
        if not tem_smtp:
            continue
        cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ent["candidato_id"],)).fetchone()
        if not cand or not (cand["email"] or "").strip():
            continue
        assunto, texto, html, anexos = email_candidato(conn, ent, "lembrete")
        ok, _ = srv.enviar_email(conn, cand["email"].strip(), assunto, texto, anexos=anexos, html=html)
        if ok:
            enviados += 1
            srv.registrar_evento(conn, cand["id"], "email", "Lembrete de entrevista enviado")
            conn.commit()
    return enviados


def rotina_agenda():
    while True:
        try:
            conn = srv.db()
            try:
                enviar_lembretes(conn)
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Rotina da agenda falhou: %r\n" % exc)
        time.sleep(INTERVALO_LEMBRETES)


# ------------------------------------------------------------- respostas da API

def _ent_publica(cfg, ent):
    if not ent:
        return None
    inicio = ler_utc(ent["inicio_utc"])
    local = inicio.astimezone(zona(cfg))
    return {"id": ent["id"], "inicio_utc": ent["inicio_utc"], "fim_utc": ent["fim_utc"], "status": ent["status"],
            "data": local.date().isoformat(), "hora": local.strftime("%H:%M"),
            "meet_link": _meet(ent) if ent["status"] == "marcada" else ""}


def dados_publicos(conn, cand):
    cfg = config(conn, cand["empresa_id"])
    m = srv.mensagens.marca(conn, cand["empresa_id"]) or {}
    ent = entrevista_ativa(conn, cand["id"])
    dias = agrupar_por_dia(horarios_livres(conn, cand["empresa_id"], cfg, ent["id"] if ent else None)) if cfg.get("ativo") else []
    return {
        "empresa": {"nome": m.get("nome") or "", "logo_url": m.get("logo_url") or ""},
        "nome": (cand["nome"] or "").split(" ")[0],
        "idioma": idioma(cand["idioma"]) if cand["idioma"] else "",
        "ativo": bool(cfg.get("ativo")),
        "formato": cfg["formato"], "local": cfg.get("local") or "", "entrevistador": cfg.get("entrevistador") or "",
        "duracao": cfg["duracao"], "fuso": zona(cfg).key, "rotulo_fuso": rotulo_fuso(cfg),
        "dias": dias, "entrevista": _ent_publica(cfg, ent),
    }


def _ent_gestor(conn, cfg, ent):
    d = _ent_publica(cfg, ent)
    d.update(candidato_id=ent["candidato_id"], quando=formatar(cfg, ler_utc(ent["inicio_utc"]), "pt"),
             cancelada_em=ent["cancelada_em"] or "", criado_em=ent["criado_em"])
    return d


def _resp(h, status, dados):
    h._json(status, dados)
    return True


def rotear_publico(h, method, path, conn):
    """GET /api/agenda/<token>, POST /api/agenda/<token>/marcar e /cancelar (sem login)."""
    if not path.startswith("/api/agenda/"):
        return None
    partes = path[len("/api/agenda/"):].split("/")
    cand = candidato_do_token(conn, partes[0])
    if not cand:
        return _resp(h, 404, {"erro": "Link de agendamento inválido"})
    acao = partes[1] if len(partes) > 1 else ""
    if method == "GET" and not acao:
        return _resp(h, 200, dados_publicos(conn, cand))
    if method == "POST" and acao == "marcar":
        try:
            marcar(conn, cand, (h._body() or {}).get("inicio_utc"))
        except ErroAgenda as e:
            return _resp(h, e.status, {"erro": e.mensagem})
        return _resp(h, 200, dict(dados_publicos(conn, cand), ok=True))
    if method == "POST" and acao == "cancelar":
        ent = entrevista_ativa(conn, cand["id"])
        if not ent:
            return _resp(h, 400, {"erro": "Nenhuma entrevista marcada"})
        cancelar(conn, ent, "candidato")
        return _resp(h, 200, dict(dados_publicos(conn, cand), ok=True))
    return _resp(h, 404, {"erro": "Rota não encontrada"})


def proximas(conn, gestor, agora=None):
    """Entrevistas de hoje e de amanhã (no fuso da empresa) que o gestor enxerga."""
    cfg = config(conn, gestor["empresa_id"])
    z = zona(cfg)
    agora = agora or _agora()
    hoje = agora.astimezone(z).date()
    ini = datetime(hoje.year, hoje.month, hoje.day, tzinfo=z)
    fim = ini + timedelta(days=2)
    saida = {"hoje": [], "amanha": [], "fuso": z.key, "rotulo_fuso": rotulo_fuso(cfg), "ativo": bool(cfg.get("ativo"))}
    for r in conn.execute(
            "SELECT en.*, c.nome, c.local, c.empresa_id AS c_empresa, c.telefone FROM entrevistas_agenda en"
            " JOIN candidatos c ON c.id=en.candidato_id"
            " WHERE en.empresa_id=? AND en.status IN ('marcada','realizada','faltou')"
            " AND en.inicio_utc>=? AND en.inicio_utc<? ORDER BY en.inicio_utc",
            (gestor["empresa_id"], iso_utc(ini), iso_utc(fim))).fetchall():
        if not srv.gestor_ve_candidato(gestor, {"empresa_id": r["c_empresa"], "local": r["local"]}):
            continue
        local = ler_utc(r["inicio_utc"]).astimezone(z)
        item = {"id": r["id"], "candidato_id": r["candidato_id"], "nome": r["nome"], "telefone": r["telefone"] or "",
                "hora": local.strftime("%H:%M"), "status": r["status"], "inicio_utc": r["inicio_utc"]}
        saida["hoje" if local.date() == hoje else "amanha"].append(item)
    return saida


def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/agenda"):
        return None
    empresa_id = gestor["empresa_id"]

    # Google Agenda do gestor: estado, conectar e desconectar (google_cal.py)
    if google_cal and path.startswith("/api/gestor/agenda/google"):
        return google_cal.rotear_gestor(h, method, path, conn, gestor)

    if path == "/api/gestor/agenda/config":
        if not gestor["is_admin"]:
            return _resp(h, 403, {"erro": "Apenas o administrador da empresa configura a agenda"})
        if method == "GET":
            return _resp(h, 200, {"config": config(conn, empresa_id), "formatos": list(FORMATOS)})
        if method == "POST":
            corpo = h._body() or {}
            cfg, erro = validar(corpo, config(conn, empresa_id))
            if erro:
                return _resp(h, 400, {"erro": erro})
            if cfg.get("google_entrevistadores"):
                # só contas Google conectadas de gestores desta empresa
                validos = [r["gestor_id"] for r in google_cal.contas_validas(
                    conn, empresa_id, cfg["google_entrevistadores"])] if google_cal else []
                if "google_entrevistadores" in corpo and len(validos) != len(cfg["google_entrevistadores"]):
                    return _resp(h, 400, {"erro": "Entrevistador inválido"})
                cfg["google_entrevistadores"] = validos  # contas desconectadas saem da lista
                if cfg.get("google_organizador") not in validos:
                    cfg["google_organizador"] = 0
            salvar(conn, empresa_id, cfg)
            return _resp(h, 200, {"ok": True, "config": config(conn, empresa_id)})

    if method == "GET" and path == "/api/gestor/agenda/proximas":
        return _resp(h, 200, proximas(conn, gestor))

    m = re.match(r"^/api/gestor/agenda/candidato/(\d+)$", path)
    if method == "GET" and m:
        cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)).fetchone()
        if not cand or not srv.gestor_ve_candidato(gestor, cand):
            return _resp(h, 404, {"erro": "Candidato não encontrado"})
        cfg = config(conn, empresa_id)
        historico = [_ent_gestor(conn, cfg, e) for e in conn.execute(
            "SELECT * FROM entrevistas_agenda WHERE candidato_id=? AND empresa_id=? ORDER BY inicio_utc DESC LIMIT 10",
            (cand["id"], empresa_id)).fetchall()]
        ativa = next((e for e in historico if e["status"] == "marcada"), None)
        return _resp(h, 200, {"ativo": bool(cfg.get("ativo")), "entrevista": ativa, "historico": historico,
                              "link": link(conn, cand) if cfg.get("ativo") else "",
                              "qualifica": qualifica(conn, cand), "tem_email": bool((cand["email"] or "").strip()),
                              "rotulo_fuso": rotulo_fuso(cfg), "fuso": zona(cfg).key})

    if method == "POST" and path == "/api/gestor/agenda/enviar-link":
        d = h._body() or {}
        cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (d.get("candidato_id"),)).fetchone()
        if not cand or not srv.gestor_ve_candidato(gestor, cand):
            return _resp(h, 404, {"erro": "Candidato não encontrado"})
        if not config(conn, empresa_id).get("ativo"):
            return _resp(h, 400, {"erro": "A agenda de entrevistas está desativada"})
        if not (cand["email"] or "").strip():
            return _resp(h, 400, {"erro": "Candidato sem e-mail"})
        ok, msg = enviar_link(conn, cand, gestor["nome"])
        if not ok:
            return _resp(h, 400, {"erro": "Não foi possível enviar: " + msg})
        return _resp(h, 200, {"ok": True})

    m = re.match(r"^/api/gestor/agenda/entrevista/(\d+)/status$", path)
    if method == "POST" and m:
        ent = conn.execute("SELECT * FROM entrevistas_agenda WHERE id=? AND empresa_id=?",
                           (int(m.group(1)), empresa_id)).fetchone()
        cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ent["candidato_id"],)).fetchone() if ent else None
        if not ent or not cand or not srv.gestor_ve_candidato(gestor, cand):
            return _resp(h, 404, {"erro": "Entrevista não encontrada"})
        try:
            mudar_status(conn, ent, (h._body() or {}).get("status"), gestor)
        except ErroAgenda as e:
            return _resp(h, e.status, {"erro": e.mensagem})
        return _resp(h, 200, {"ok": True})

    return _resp(h, 404, {"erro": "Rota não encontrada"})
