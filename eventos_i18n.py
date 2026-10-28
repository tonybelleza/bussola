"""Traduções (EN e ES) dos textos da linha do tempo (tabela eventos).

Os eventos continuam gravados em português; a tradução acontece só na hora de
mostrar ao gestor (ficha do candidato e feed de atividades).

Uso:
    from eventos_i18n import traduzir_evento
    traduzir_evento("Currículo enviado", "en")  # "Resume uploaded"

EVENTOS: texto exato em português -> {"en": ..., "es": ...}
PADROES: textos montados com % (regex com grupos nomeados). O modelo pode ser
uma string com {grupo} ou uma função (grupos, idioma) -> texto.
VALORES: traduz o valor capturado de alguns grupos (etapa, data, motivo...).
Nomes, cargos, títulos de vaga e textos digitados pela empresa ficam como estão.
traduzir_evento(texto, idioma): nunca lança exceção; devolve o original quando
o idioma é "pt", desconhecido, ou quando não há tradução.
"""

import re

try:
    import erros_i18n  # detalhes de falhas de e-mail podem ser mensagens de erro conhecidas
except Exception:  # noqa: BLE001
    erros_i18n = None

_IDIOMAS = ("en", "es")

EVENTOS = {
    # candidato e avaliações (server.py)
    "Avaliação completa": {"en": "Assessment complete", "es": "Evaluación completa"},
    "Dados pessoais anonimizados (LGPD)": {
        "en": "Personal data anonymized (LGPD)", "es": "Datos personales anonimizados (LGPD)"},
    "Lembrete de avaliação incompleta enviado": {
        "en": "Incomplete assessment reminder sent", "es": "Recordatorio de evaluación incompleta enviado"},
    "Link de acesso reenviado (cadastro duplicado)": {
        "en": "Access link resent (duplicate sign-up)", "es": "Enlace de acceso reenviado (registro duplicado)"},
    "E-mail de confirmação enviado ao candidato": {
        "en": "Confirmation email sent to the candidate", "es": "Correo de confirmación enviado al candidato"},
    "Link de acesso reenviado a pedido": {
        "en": "Access link resent on request", "es": "Enlace de acceso reenviado a pedido"},
    "Autoavaliação de competências respondida": {
        "en": "Skills self-assessment completed", "es": "Autoevaluación de competencias respondida"},
    "Currículo enviado": {"en": "Resume uploaded", "es": "Currículum enviado"},
    "E-mail de atualização enviado": {"en": "Update email sent", "es": "Correo de actualización enviado"},

    # agenda de entrevistas (agenda.py)
    "Lembrete de entrevista enviado": {"en": "Interview reminder sent", "es": "Recordatorio de entrevista enviado"},
    "Entrevista realizada": {"en": "Interview held", "es": "Entrevista realizada"},
    "Entrevista marcada como falta (não compareceu)": {
        "en": "Interview marked as a no-show", "es": "Entrevista marcada como inasistencia (no se presentó)"},
    # Google Agenda e Google Meet (agenda.py + google_cal.py)
    "Google Agenda: evento criado": {"en": "Google Calendar: event created", "es": "Google Calendar: evento creado"},
    "Google Agenda: evento criado com link do Google Meet": {
        "en": "Google Calendar: event created with a Google Meet link",
        "es": "Google Calendar: evento creado con enlace de Google Meet"},
    "Google Agenda: evento atualizado": {"en": "Google Calendar: event updated", "es": "Google Calendar: evento actualizado"},
    "Google Agenda: evento removido": {"en": "Google Calendar: event removed", "es": "Google Calendar: evento eliminado"},
    "Google Agenda: não foi possível sincronizar o evento": {
        "en": "Google Calendar: could not sync the event", "es": "Google Calendar: no se pudo sincronizar el evento"},

    # banco de talentos (talentos.py)
    "Lembrete removido": {"en": "Reminder removed", "es": "Recordatorio eliminado"},

    # aviso ao banco de talentos (campanhas.py)
    "Cancelou os e-mails de vagas da empresa": {
        "en": "Unsubscribed from the company's job emails", "es": "Canceló los correos de vacantes de la empresa"},

    # triagem por voz (voz.py)
    "Entrou na fila da triagem por voz": {
        "en": "Added to the voice screening queue", "es": "Entró en la cola de evaluación por voz"},
    "Falha ao iniciar a ligação": {"en": "Failed to start the call", "es": "No se pudo iniciar la llamada"},
    "Voltou para a fila da triagem por voz": {
        "en": "Back in the voice screening queue", "es": "Volvió a la cola de evaluación por voz"},
    "Marcado como Não ligar": {"en": "Marked as Do not call", "es": "Marcado como No llamar"},
    "Tentativas da triagem por voz zeradas": {
        "en": "Voice screening attempts reset", "es": "Intentos de evaluación por voz reiniciados"},
    "Ligação recebida: o candidato ligou para a Francisca": {
        "en": "Inbound call: the candidate called Francisca", "es": "Llamada recibida: el candidato llamó a Francisca"},
    "Cadastro criado pela Francisca (ligação recebida)": {
        "en": "Profile created by Francisca (inbound call)", "es": "Registro creado por Francisca (llamada recibida)"},

    # onboarding (onboarding.py)
    "Onboarding cancelado": {"en": "Onboarding canceled", "es": "Incorporación cancelada"},
    "Consentimento para documentos eletrônicos aceito": {
        "en": "Electronic records consent accepted", "es": "Consentimiento para documentos electrónicos aceptado"},
    "Onboarding concluído pelo novo contratado": {
        "en": "Onboarding completed by the new hire", "es": "Incorporación completada por el nuevo empleado"},
    "Lembrete de onboarding enviado": {"en": "Onboarding reminder sent", "es": "Recordatorio de incorporación enviado"},
    "I-9 Seção 2 preenchida pelo empregador": {
        "en": "I-9 Section 2 completed by the employer", "es": "Sección 2 del I-9 completada por el empleador"},
    "Dados sensíveis do onboarding apagados (retenção)": {
        "en": "Sensitive onboarding data deleted (retention)",
        "es": "Datos sensibles de la incorporación borrados (retención)"},
}

# --------------------------------------------------- valores dentro dos textos

ETAPAS = {  # server.NOMES_ETAPAS (mesmos rótulos do painel, i18n-gestor.js)
    "Inscrito": {"en": "Applied", "es": "Inscrito"},
    "Avaliações": {"en": "Assessments", "es": "Evaluaciones"},
    "Entrevista": {"en": "Interview", "es": "Entrevista"},
    "Proposta": {"en": "Offer", "es": "Oferta"},
    "Contratado": {"en": "Hired", "es": "Contratado"},
    "Reprovado": {"en": "Rejected", "es": "Descartado"},
}

MOTIVOS = {  # motivos gravados pelo sistema (voz.ENCERRAMENTOS); motivos digitados ficam como estão
    "triagem por voz": {"en": "voice screening", "es": "evaluación por voz"},
    "Número errado (triagem por voz)": {"en": "Wrong number (voice screening)", "es": "Número equivocado (evaluación por voz)"},
    "Sem interesse na vaga (triagem por voz)": {
        "en": "Not interested in the job (voice screening)", "es": "Sin interés en la vacante (evaluación por voz)"},
    "Pediu para não ser chamado (triagem por voz)": {
        "en": "Asked not to be called (voice screening)", "es": "Pidió no ser llamado (evaluación por voz)"},
}

_SIMPLES = {
    "acao_entrevista": {
        "marcada": {"en": "booked", "es": "agendada"},
        "remarcada": {"en": "rescheduled", "es": "reprogramada"},
        "cancelada": {"en": "canceled", "es": "cancelada"},
    },
    "quem": {"pelo candidato": {"en": "by the candidate", "es": "por el candidato"}},
    "aviso": {
        "testes pendentes": {"en": "tests pending", "es": "pruebas pendientes"},
        "avaliação completa": {"en": "assessment complete", "es": "evaluación completa"},
        "novo candidato": {"en": "new candidate", "es": "nuevo candidato"},
    },
    "envio": {
        "enviado": {"en": "sent", "es": "enviado"},
        "não enviado": {"en": "not sent", "es": "no enviado"},
    },
    "outcome": {"sem resposta": {"en": "no answer", "es": "sin respuesta"}},
    "etapa": ETAPAS,
    "motivo": MOTIVOS,
}

_DIAS_PT = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
_DIAS = {"en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
         "es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]}
_MESES_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]
_MESES = {"en": ["January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"],
          "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]}
# agenda.formatar(cfg, quando, "pt"): "{semana}, {dia} de {mes} de {ano}, às {hora} · {fuso}"
_DATA_PT = re.compile(
    r"^(?P<sem>[^,]+), (?P<dia>\d{1,2}) de (?P<mes>[^ ]+) de (?P<ano>\d{4}), às (?P<h>\d{1,2}):(?P<m>\d{2})(?P<fuso> · .*)?$")


def _data(valor, lang):
    """Data por extenso da agenda (em português) no formato do idioma pedido."""
    m = _DATA_PT.match(valor)
    if not m or m.group("sem") not in _DIAS_PT or m.group("mes") not in _MESES_PT:
        return valor
    sem = _DIAS[lang][_DIAS_PT.index(m.group("sem"))]
    mes = _MESES[lang][_MESES_PT.index(m.group("mes"))]
    h, mi, fuso = int(m.group("h")), m.group("m"), m.group("fuso") or ""
    if lang == "en":
        hora = "%d:%s %s" % (h % 12 or 12, mi, "AM" if h < 12 else "PM")
        return "%s, %s %s, %s at %s%s" % (sem, mes, m.group("dia"), m.group("ano"), hora, fuso)
    return "%s %s de %s de %s, a las %02d:%s%s" % (sem, m.group("dia"), mes, m.group("ano"), h, mi, fuso)


def _detalhe(valor, lang):
    if erros_i18n is None:
        return valor
    return erros_i18n.traduzir(valor, lang)


VALORES = {nome: (lambda tabela: lambda v, lang: (tabela.get(v) or {}).get(lang, v))(tabela)
           for nome, tabela in _SIMPLES.items()}
VALORES["quando"] = _data
VALORES["detalhe"] = _detalhe


# ------------------------------------------------------------ textos com %s

def _mover(g, lang):
    motivo = g.get("motivo")
    extra = " (%s)" % motivo if motivo else ""
    if lang == "en":
        return "Job %s: moved to %s%s" % (g["vaga"], g["etapa"], extra)
    return "Vacante %s: movido a %s%s" % (g["vaga"], g["etapa"], extra)


def _triagem(g, lang):
    texto = ("Voice screening: %s" if lang == "en" else "Evaluación por voz: %s") % g["outcome"]
    if g.get("tier"):
        texto += " (%s, %s %s)" % (g["tier"], g["pontos"], "points" if lang == "en" else "puntos")
    if g.get("nota"):
        texto += " [%s]" % g["nota"]
    return texto


def _lembrete(g, lang):
    nota = g.get("nota")
    base = ("Reminder for %s" if lang == "en" else "Recordatorio para %s") % g["data"]
    return base + (": " + nota if nota else "")


_ETAPAS_RE = "|".join(re.escape(e) for e in ETAPAS)

PADROES = [
    # server.py
    (r"^Resultados enviados ao candidato \((?P<lang>[^()]*)\)$",
     {"en": "Results sent to the candidate ({lang})", "es": "Resultados enviados al candidato ({lang})"}),
    (r"^Currículo analisado automaticamente por IA \(aderência (?P<n>[^()%]*)%\)$",
     {"en": "Resume automatically analyzed by AI ({n}% match)",
      "es": "Currículum analizado automáticamente por IA (afinidad {n}%)"}),
    (r"^Currículo analisado por IA \(aderência (?P<n>[^()%]*)%\)$",
     {"en": "Resume analyzed by AI ({n}% match)", "es": "Currículum analizado por IA (afinidad {n}%)"}),
    (r"^Nova inscrição na vaga: (?P<vaga>.*)$",
     {"en": "New application to job: {vaga}", "es": "Nueva postulación a la vacante: {vaga}"}),
    (r"^Inscrição na vaga: (?P<vaga>.*)$",
     {"en": "Applied to job: {vaga}", "es": "Postulación a la vacante: {vaga}"}),
    (r"^Cadastro de colaborador interno \((?P<local>.*)\)$",
     {"en": "Internal employee sign-up ({local})", "es": "Registro de colaborador interno ({local})"}),
    (r"^Cadastro realizado \((?P<local>.*)\)$",
     {"en": "Signed up ({local})", "es": "Registro realizado ({local})"}),
    (r"^Teste (?P<teste>DISC|B\.A\.S\.E\.) concluído$",
     {"en": "{teste} test completed", "es": "Prueba {teste} completada"}),
    (r"^Teste de conhecimento concluído: (?P<a>\d+) de (?P<b>\d+) acertos$",
     {"en": "Knowledge test completed: {a} of {b} correct",
      "es": "Prueba de conocimientos completada: {a} de {b} aciertos"}),
    (r"^Vaga (?P<vaga>.+): movido para (?P<etapa>%s)(?: \((?P<motivo>.*)\))?$" % _ETAPAS_RE,
     {"en": _mover, "es": _mover}),
    (r"^Falha ao enviar e-mail: (?P<detalhe>.*)$",
     {"en": "Failed to send email: {detalhe}", "es": "Error al enviar el correo: {detalhe}"}),
    (r"^Adicionado à vaga: (?P<vaga>.*)$",
     {"en": "Added to job: {vaga}", "es": "Agregado a la vacante: {vaga}"}),
    (r"^Entrevista registrada: média (?P<m>[\d.,]+) de 5$",
     {"en": "Interview recorded: average {m} out of 5", "es": "Entrevista registrada: promedio {m} de 5"}),
    (r"^E-mail enviado pelo gestor: (?P<assunto>.*)$",
     {"en": "Email sent by manager: {assunto}", "es": "Correo enviado por el gerente: {assunto}"}),

    # agenda.py
    (r"^Entrevista marcada pelo candidato: (?P<quando>.*)$",
     {"en": "Interview booked by the candidate: {quando}", "es": "Entrevista agendada por el candidato: {quando}"}),
    (r"^Entrevista remarcada pelo candidato: (?P<quando>.*)$",
     {"en": "Interview rescheduled by the candidate: {quando}",
      "es": "Entrevista reprogramada por el candidato: {quando}"}),
    (r"^Entrevista cancelada \((?P<quem>[^()]*)\): (?P<quando>.*)$",
     {"en": "Interview canceled ({quem}): {quando}", "es": "Entrevista cancelada ({quem}): {quando}"}),
    (r"^Entrevista (?P<acao_entrevista>marcada|remarcada|cancelada): e-mail ao candidato e a (?P<n>\d+) gestor\(es\)$",
     {"en": "Interview {acao_entrevista}: email sent to the candidate and {n} manager(s)",
      "es": "Entrevista {acao_entrevista}: correo enviado al candidato y a {n} gerente(s)"}),
    (r"^Entrevista (?P<acao_entrevista>marcada|remarcada|cancelada): e-mail ao candidato não enviado e a (?P<n>\d+) gestor\(es\)$",
     {"en": "Interview {acao_entrevista}: candidate email not sent, {n} manager(s) emailed",
      "es": "Entrevista {acao_entrevista}: correo al candidato no enviado, {n} gerente(s) avisado(s)"}),
    (r"^Link de agendamento de entrevista enviado \((?P<lang>[^()]*)\)$",
     {"en": "Interview scheduling link sent ({lang})", "es": "Enlace para agendar la entrevista enviado ({lang})"}),

    # campanhas.py
    (r"^Avisado por e-mail sobre a vaga: (?P<vaga>.*) \(banco de talentos\)$",
     {"en": "Notified about job {vaga} (talent pool email)",
      "es": "Avisado por correo sobre la vacante {vaga} (banco de talentos)"}),
    (r"^Falha ao avisar sobre a vaga: (?P<vaga>.*) \(banco de talentos\)$",
     {"en": "Could not notify about job {vaga} (talent pool email)",
      "es": "No se pudo avisar sobre la vacante {vaga} (banco de talentos)"}),

    # entrada.py
    (r"^Importado \((?P<origem>[^()]*)\)$", {"en": "Imported ({origem})", "es": "Importado ({origem})"}),

    # indicacoes.py
    (r"^Indicado por (?P<nome>.*)$", {"en": "Referred by {nome}", "es": "Recomendado por {nome}"}),
    (r"^Indicou um candidato \(#(?P<n>\d+)\)$",
     {"en": "Referred a candidate (#{n})", "es": "Recomendó a un candidato (#{n})"}),

    # mensagens.py
    (r"^Gestores notificados por e-mail \((?P<n>\d+)\): (?P<aviso>testes pendentes|avaliação completa|novo candidato)$",
     {"en": "Managers notified by email ({n}): {aviso}", "es": "Gerentes notificados por correo ({n}): {aviso}"}),

    # onboarding.py
    (r"^Proposta e onboarding enviados \((?P<tipo>W-2|1099), (?P<cargo>.*), início (?P<data>[^,()]*)\)$",
     {"en": "Offer and onboarding sent ({tipo}, {cargo}, start {data})",
      "es": "Oferta e incorporación enviadas ({tipo}, {cargo}, inicio {data})"}),
    (r"^E-mail da proposta e do onboarding (?P<envio>enviado|não enviado) \((?P<lang>[^()]*)\)$",
     {"en": "Offer and onboarding email {envio} ({lang})",
      "es": "Correo de la oferta y la incorporación {envio} ({lang})"}),
    (r"^Documento assinado: (?P<titulo>.*)$", {"en": "Document signed: {titulo}", "es": "Documento firmado: {titulo}"}),
    (r"^Formulário preenchido e assinado: (?P<titulo>.*)$",
     {"en": "Form completed and signed: {titulo}", "es": "Formulario completado y firmado: {titulo}"}),
    (r"^Onboarding concluído: aviso a (?P<n>\d+) gestor\(es\)$",
     {"en": "Onboarding complete: {n} manager(s) notified", "es": "Incorporación completada: aviso a {n} gerente(s)"}),

    # talentos.py
    (r"^Lembrete para (?P<data>\d{4}-\d{2}-\d{2})(?:: (?P<nota>.*))?$", {"en": _lembrete, "es": _lembrete}),

    # voz.py
    (r"^Ligação da triagem por voz iniciada \((?P<lang>[^(),]*), tentativa (?P<n>\d+)\)$",
     {"en": "Voice screening call started ({lang}, attempt {n})",
      "es": "Llamada de evaluación por voz iniciada ({lang}, intento {n})"}),
    (r"^Triagem por voz: (?P<outcome>.+?)(?: \((?P<tier>[^,()]*), (?P<pontos>-?\d+) pontos\))?(?: \[(?P<nota>[^\]]*)\])?$",
     {"en": _triagem, "es": _triagem}),
    (r"^Convite para os testes enviado \((?P<lang>[^()]*)\)$",
     {"en": "Test invitation sent ({lang})", "es": "Invitación a las pruebas enviada ({lang})"}),
    (r"^Falha ao enviar convite: (?P<detalhe>.*)$",
     {"en": "Failed to send invitation: {detalhe}", "es": "Error al enviar la invitación: {detalhe}"}),
    (r"^Ligou para a empresa \(interesse: (?P<interesse>.*)\)$",
     {"en": "Called the company (interest: {interesse})", "es": "Llamó a la empresa (interés: {interesse})"}),
    (r"^Link de inscrição enviado a quem ligou \((?P<lang>[^()]*)\)$",
     {"en": "Application link sent to the caller ({lang})", "es": "Enlace de solicitud enviado a quien llamó ({lang})"}),
    (r"^Falha ao enviar o link de inscrição: (?P<detalhe>.*)$",
     {"en": "Failed to send the application link: {detalhe}",
      "es": "Error al enviar el enlace de solicitud: {detalhe}"}),
]

_COMPILADOS = [(re.compile(regex, re.S), modelos) for regex, modelos in PADROES]

AUTORES = {"sistema": {"en": "system", "es": "sistema"}}


def _lang(idioma):
    lang = idioma.strip().lower()[:2] if isinstance(idioma, str) else ""
    return lang if lang in _IDIOMAS else ""


def _traduzir(texto, lang):
    """Tradução ou None quando nenhum texto/padrão conhecido casa."""
    item = EVENTOS.get(texto)
    if item and item.get(lang):
        return item[lang]
    for regex, modelos in _COMPILADOS:
        m = regex.match(texto)
        if not m or not modelos.get(lang):
            continue
        grupos = {}
        for nome, valor in m.groupdict().items():
            valor = valor or ""
            if valor and nome in VALORES:
                valor = VALORES[nome](valor, lang)
            grupos[nome] = valor
        modelo = modelos[lang]
        return modelo(grupos, lang) if callable(modelo) else modelo.format(**grupos)
    return None


def cobre(texto, idioma):
    """True quando há tradução explícita deste texto para o idioma (usado nos testes)."""
    lang = _lang(idioma)
    try:
        return bool(lang) and isinstance(texto, str) and _traduzir(texto, lang) is not None
    except Exception:  # noqa: BLE001
        return False


def traduzir_evento(texto, idioma):
    """Texto do evento em "en" ou "es". Devolve o original quando o idioma é "pt",
    desconhecido, ou não há tradução. Nunca lança."""
    try:
        lang = _lang(idioma)
        if not lang or not isinstance(texto, str) or not texto:
            return texto
        traduzido = _traduzir(texto, lang)
        return texto if traduzido is None else traduzido
    except Exception:  # noqa: BLE001
        return texto


def traduzir_autor(autor, idioma):
    """Só o autor automático ("sistema") é traduzido; nomes de pessoas ficam iguais."""
    lang = _lang(idioma)
    item = AUTORES.get(autor) if isinstance(autor, str) else None
    return item[lang] if lang and item else autor


def traduzir_lista(eventos, idioma):
    """Aplica a tradução de texto e autor a uma lista de dicts de evento (in place) e a devolve."""
    if not _lang(idioma):
        return eventos
    for ev in eventos:
        if "texto" in ev:
            ev["texto"] = traduzir_evento(ev["texto"], idioma)
        if "autor" in ev:
            ev["autor"] = traduzir_autor(ev["autor"], idioma)
    return eventos


# verificação de antecedentes pela Checkr (integracoes_rh.py)
_CHECKR_STATUS = {
    "convite enviado": {"en": "invitation sent", "es": "invitación enviada"},
    "em andamento": {"en": "in progress", "es": "en curso"},
    "clear (sem apontamentos)": {"en": "clear", "es": "clear (sin observaciones)"},
    "consider (revisar)": {"en": "consider (review)", "es": "consider (revisar)"},
    "suspensa": {"en": "suspended", "es": "suspendida"},
    "cancelada": {"en": "canceled", "es": "cancelada"},
    "convite expirado": {"en": "invitation expired", "es": "invitación vencida"},
}


def _checkr_status(g, lang):
    st = _CHECKR_STATUS.get(g["status"], {}).get(lang, g["status"])
    return ("Background check (Checkr): %s" if lang == "en" else "Verificación de antecedentes (Checkr): %s") % st


_NOVOS_PADROES = [
    (r"^Verificação de antecedentes solicitada \(Checkr, pacote (?P<pacote>[^()]*)\)$",
     {"en": "Background check ordered (Checkr, package {pacote})",
      "es": "Verificación de antecedentes solicitada (Checkr, paquete {pacote})"}),
    (r"^Verificação de antecedentes \(Checkr\): (?P<status>%s)$" % "|".join(re.escape(k) for k in _CHECKR_STATUS),
     {"en": _checkr_status, "es": _checkr_status}),
    (r"^Verificação de antecedentes concluída: aviso a (?P<n>\d+) administrador\(es\)$",
     {"en": "Background check complete: {n} admin(s) notified",
      "es": "Verificación de antecedentes completada: aviso a {n} administrador(es)"}),
]
PADROES.extend(_NOVOS_PADROES)
_COMPILADOS.extend((re.compile(regex, re.S), modelos) for regex, modelos in _NOVOS_PADROES)

# consentimento para ligações e mensagens automáticas (conta.py)
EVENTOS.update({
    "Autorizou ligações e mensagens automáticas": {
        "en": "Agreed to automated calls and texts", "es": "Autorizó llamadas y mensajes automáticos"},
    "Pediu para não receber ligações nem mensagens automáticas": {
        "en": "Asked to stop automated calls and texts", "es": "Pidió no recibir llamadas ni mensajes automáticos"},
})

# mensagens de texto (sms.py)
EVENTOS.update({
    "SMS enviado: convite para os testes": {
        "en": "Text sent: assessment invitation", "es": "SMS enviado: invitación a las evaluaciones"},
    "SMS enviado: lembrete de entrevista": {
        "en": "Text sent: interview reminder", "es": "SMS enviado: recordatorio de entrevista"},
    "SMS enviado: lembrete do onboarding": {
        "en": "Text sent: onboarding reminder", "es": "SMS enviado: recordatorio de incorporación"},
    "SMS enviado: tentamos ligar": {
        "en": "Text sent: we tried to call you", "es": "SMS enviado: intentamos llamarte"},
    "SMS enviado: candidatura recebida": {
        "en": "Text sent: application received", "es": "SMS enviado: postulación recibida"},
    "SMS enviado: mensagem do gestor": {
        "en": "Text sent: message from the hiring team", "es": "SMS enviado: mensaje del equipo de selección"},
    "SMS agendado para o horário permitido (8h às 21h)": {
        "en": "Text scheduled for allowed hours (8 AM to 9 PM)",
        "es": "SMS programado para el horario permitido (8 a. m. a 9 p. m.)"},
    "SMS recebido": {"en": "Text received", "es": "SMS recibido"},
    "Pediu para não receber SMS (STOP)": {
        "en": "Opted out of texts (STOP)", "es": "Pidió no recibir SMS (STOP)"},
    "Voltou a receber SMS (START)": {
        "en": "Opted back in to texts (START)", "es": "Volvió a recibir SMS (START)"},
})
_SMS_PADROES = [
    (r"^Falha ao enviar SMS: (?P<detalhe>.*)$",
     {"en": "Failed to send text: {detalhe}", "es": "No se pudo enviar el SMS: {detalhe}"}),
]
PADROES.extend(_SMS_PADROES)
_COMPILADOS.extend((re.compile(regex, re.S), modelos) for regex, modelos in _SMS_PADROES)
