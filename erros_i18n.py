"""Traduções (EN e ES) das mensagens de erro que o servidor devolve aos clientes.

Uso:
    from erros_i18n import traduzir
    traduzir("Cargo não encontrado", "en")  # "Role not found"

ERROS: texto exato em português -> {"en": ..., "es": ...}
PADROES: mensagens montadas com % ou format (regex com grupos nomeados).
CODIGOS: códigos curtos do módulo de voz (voz.py), que também chegam em "erro".
traduzir(texto, idioma): nunca lança exceção; devolve o original quando o idioma
é "pt", desconhecido, ou quando não há tradução.
"""

import re

ERROS = {
    # ------------------------------------------------------------ genéricos
    "Não encontrado": {"en": "Not found", "es": "No encontrado"},
    "Rota não encontrada": {"en": "Route not found", "es": "Ruta no encontrada"},
    "Erro interno": {"en": "Internal error", "es": "Error interno"},
    "Envio grande demais": {"en": "Upload is too large", "es": "El envío es demasiado grande"},
    "Idioma inválido": {"en": "Invalid language", "es": "Idioma inválido"},
    "Arquivo inválido": {"en": "Invalid file", "es": "Archivo inválido"},
    "Arquivo maior que 8 MB": {"en": "File is larger than 8 MB", "es": "El archivo supera los 8 MB"},
    "Arquivo não encontrado": {"en": "File not found", "es": "Archivo no encontrado"},
    "Arquivo não disponível no servidor": {
        "en": "File is not available on the server",
        "es": "El archivo no está disponible en el servidor"},

    # ------------------------------------------------- acesso, login, senha
    "Muitas tentativas. Aguarde alguns minutos e tente de novo.": {
        "en": "Too many attempts. Wait a few minutes and try again.",
        "es": "Demasiados intentos. Espera unos minutos e inténtalo de nuevo."},
    "Muitas tentativas. Aguarde alguns minutos.": {
        "en": "Too many attempts. Wait a few minutes.",
        "es": "Demasiados intentos. Espera unos minutos."},
    "Senha incorreta": {"en": "Incorrect password", "es": "Contraseña incorrecta"},
    "Senha atual incorreta": {"en": "Current password is incorrect", "es": "La contraseña actual es incorrecta"},
    "Login ou senha incorretos": {"en": "Incorrect username or password", "es": "Usuario o contraseña incorrectos"},
    "A senha deve ter ao menos 6 caracteres": {
        "en": "Password must be at least 6 characters",
        "es": "La contraseña debe tener al menos 6 caracteres"},
    "A nova senha deve ter ao menos 6 caracteres": {
        "en": "New password must be at least 6 characters",
        "es": "La nueva contraseña debe tener al menos 6 caracteres"},
    "A nova senha deve ter ao menos 8 caracteres": {
        "en": "New password must be at least 8 characters",
        "es": "La nueva contraseña debe tener al menos 8 caracteres"},
    "A senha do dono deve ter ao menos 8 caracteres": {
        "en": "Owner password must be at least 8 characters",
        "es": "La contraseña del propietario debe tener al menos 8 caracteres"},
    "A senha do gestor deve ter ao menos 8 caracteres": {
        "en": "Manager password must be at least 8 characters",
        "es": "La contraseña del gestor debe tener al menos 8 caracteres"},
    "Acesso restrito ao dono do software": {
        "en": "Access restricted to the software owner",
        "es": "Acceso restringido al propietario del software"},
    "Acesso restrito ao gestor": {"en": "Access restricted to managers", "es": "Acceso restringido a gestores"},
    "O dono já foi cadastrado": {"en": "The owner is already registered", "es": "El propietario ya está registrado"},
    "O administrador já foi cadastrado": {
        "en": "The administrator is already registered",
        "es": "El administrador ya está registrado"},
    "Sua conta ainda está aguardando aprovação do administrador. Você receberá um aviso quando for liberada.": {
        "en": "Your account is still awaiting administrator approval. You will be notified once it is approved.",
        "es": "Tu cuenta aún está esperando la aprobación del administrador. Recibirás un aviso cuando sea habilitada."},
    "O acesso desta empresa está suspenso. Fale com o suporte.": {
        "en": "This company's access is suspended. Please contact support.",
        "es": "El acceso de esta empresa está suspendido. Comunícate con soporte."},
    "Link de redefinição inválido ou expirado. Peça um novo.": {
        "en": "Reset link is invalid or expired. Request a new one.",
        "es": "El enlace de restablecimiento es inválido o expiró. Solicita uno nuevo."},
    "Use o link de cadastro enviado pela sua empresa para solicitar acesso.": {
        "en": "Use the sign-up link sent by your company to request access.",
        "es": "Usa el enlace de registro que te envió tu empresa para solicitar acceso."},
    "Preencha nome, login e e-mail": {
        "en": "Fill in name, username and email",
        "es": "Completa nombre, usuario y correo electrónico"},
    "Este login já está em uso. Escolha outro.": {
        "en": "This username is already taken. Choose another one.",
        "es": "Este usuario ya está en uso. Elige otro."},
    "Este login já existe": {"en": "This username already exists", "es": "Este usuario ya existe"},
    "Já existe um gestor com este login": {
        "en": "A manager with this username already exists",
        "es": "Ya existe un gestor con este usuario"},
    "Nome e login são obrigatórios": {
        "en": "Name and username are required",
        "es": "El nombre y el usuario son obligatorios"},
    "Nome e login do gestor são obrigatórios": {
        "en": "Manager name and username are required",
        "es": "El nombre y el usuario del gestor son obligatorios"},
    "Sessão inválida. Faça o cadastro novamente.": {
        "en": "Invalid session. Please sign up again.",
        "es": "Sesión inválida. Vuelve a registrarte."},

    # ----------------------------------------------- permissões e módulos
    "Apenas o administrador altera cargos e avaliações": {
        "en": "Only the administrator can change roles and assessments",
        "es": "Solo el administrador puede modificar cargos y evaluaciones"},
    "Apenas o administrador altera cargos.": {
        "en": "Only the administrator can change roles.",
        "es": "Solo el administrador puede modificar cargos."},
    "Apenas o administrador da empresa edita o roteiro.": {
        "en": "Only the company administrator can edit the script.",
        "es": "Solo el administrador de la empresa puede editar el guion."},
    "Apenas o administrador da empresa pode trocar a logo": {
        "en": "Only the company administrator can change the logo",
        "es": "Solo el administrador de la empresa puede cambiar el logo"},
    "Apenas o administrador edita os modelos": {
        "en": "Only the administrator can edit the templates",
        "es": "Solo el administrador puede editar las plantillas"},
    "Apenas o administrador gerencia contas de gestor": {
        "en": "Only the administrator can manage manager accounts",
        "es": "Solo el administrador puede gestionar las cuentas de gestor"},
    "Só o administrador da empresa altera as regras.": {
        "en": "Only the company administrator can change the rules.",
        "es": "Solo el administrador de la empresa puede cambiar las reglas."},
    "Você não pode excluir a sua própria conta": {
        "en": "You cannot delete your own account",
        "es": "No puedes eliminar tu propia cuenta"},
    "Módulo desconhecido": {"en": "Unknown module", "es": "Módulo desconocido"},
    "Módulo não liberado para esta conta. Fale com o administrador do sistema.": {
        "en": "Module not enabled for this account. Contact the system administrator.",
        "es": "Módulo no habilitado para esta cuenta. Comunícate con el administrador del sistema."},
    "Módulo não liberado para esta empresa.": {
        "en": "Module not enabled for this company.",
        "es": "Módulo no habilitado para esta empresa."},
    "As integrações agora são configuradas pelo administrador do sistema (painel do dono).": {
        "en": "Integrations are now configured by the system administrator (owner panel).",
        "es": "Las integraciones ahora las configura el administrador del sistema (panel del propietario)."},
    "A integração com o ElevenLabs é configurada no painel do administrador do sistema.": {
        "en": "The ElevenLabs integration is configured in the system administrator panel.",
        "es": "La integración con ElevenLabs se configura en el panel del administrador del sistema."},

    # ------------------------------------------------------ empresas e contas
    "Empresa não encontrada": {"en": "Company not found", "es": "Empresa no encontrada"},
    "Informe o nome da empresa": {"en": "Enter the company name", "es": "Ingresa el nombre de la empresa"},
    "Este link já é usado por outra empresa": {
        "en": "This link is already used by another company",
        "es": "Este enlace ya lo usa otra empresa"},
    "Gestor não encontrado": {"en": "Manager not found", "es": "Gestor no encontrado"},
    "Conta não encontrada": {"en": "Account not found", "es": "Cuenta no encontrada"},
    "Envie a logo em PNG ou JPG": {"en": "Upload the logo as PNG or JPG", "es": "Sube el logo en PNG o JPG"},
    "A logo deve ter até 1 MB": {"en": "The logo must be 1 MB or smaller", "es": "El logo debe pesar como máximo 1 MB"},
    "Arquivo de imagem inválido": {"en": "Invalid image file", "es": "Archivo de imagen inválido"},
    "Logo não encontrada": {"en": "Logo not found", "es": "Logo no encontrado"},

    # ------------------------------------------- candidatura (área pública)
    "Nome e e-mail são obrigatórios": {
        "en": "Name and email are required",
        "es": "El nombre y el correo electrónico son obligatorios"},
    "Informe onde você está fazendo a avaliação": {
        "en": "Tell us where you are taking the assessment",
        "es": "Indica desde dónde estás haciendo la evaluación"},
    "Informe um telefone válido com o código do país": {
        "en": "Enter a valid phone number with the country code",
        "es": "Ingresa un teléfono válido con el código de país"},
    "É necessário autorizar o uso dos seus dados para o processo seletivo": {
        "en": "You must authorize the use of your data for the selection process",
        "es": "Debes autorizar el uso de tus datos para el proceso de selección"},
    "Esta vaga não está mais aberta": {
        "en": "This job opening is no longer open",
        "es": "Esta vacante ya no está abierta"},
    "Use o link de inscrição enviado pela empresa.": {
        "en": "Use the application link sent by the company.",
        "es": "Usa el enlace de inscripción que te envió la empresa."},
    "Este e-mail já possui cadastro. Enviamos o seu link de acesso para o e-mail informado.": {
        "en": "This email is already registered. We sent your access link to the email you entered.",
        "es": "Este correo ya está registrado. Enviamos tu enlace de acceso al correo que ingresaste."},
    "Este e-mail já possui cadastro. Use o seu link pessoal de acesso para continuar.": {
        "en": "This email is already registered. Use your personal access link to continue.",
        "es": "Este correo ya está registrado. Usa tu enlace personal de acceso para continuar."},
    "Página de vagas não encontrada": {"en": "Jobs page not found", "es": "Página de vacantes no encontrada"},
    "Informe o e-mail cadastrado": {"en": "Enter your registered email", "es": "Ingresa el correo con el que te registraste"},
    "O reenvio por e-mail ainda não está ativo. Fale com o gestor do processo para recuperar seu link.": {
        "en": "Email resend is not active yet. Contact the hiring manager to recover your link.",
        "es": "El reenvío por correo aún no está activo. Comunícate con el gestor del proceso para recuperar tu enlace."},
    "Tipo de teste inválido": {"en": "Invalid test type", "es": "Tipo de prueba inválido"},
    "Respostas do teste inválidas ou incompletas": {
        "en": "Test answers are invalid or incomplete",
        "es": "Las respuestas de la prueba son inválidas o están incompletas"},
    "Nenhum cargo de interesse selecionado": {
        "en": "No role of interest selected",
        "es": "No seleccionaste ningún cargo de interés"},
    "Este cargo não possui teste de conhecimento": {
        "en": "This role has no knowledge test",
        "es": "Este cargo no tiene prueba de conocimientos"},

    # ------------------------------------------------- painel do gestor
    "Sessão não encontrada": {"en": "Session not found", "es": "Sesión no encontrada"},
    "Informe o nome do colaborador": {"en": "Enter the employee name", "es": "Ingresa el nombre del colaborador"},
    "Título e cargo são obrigatórios": {"en": "Title and role are required", "es": "El título y el cargo son obligatorios"},
    "Cargo não encontrado": {"en": "Role not found", "es": "Cargo no encontrado"},
    "Vaga não encontrada": {"en": "Job opening not found", "es": "Vacante no encontrada"},
    "Candidatura não encontrada": {"en": "Application not found", "es": "Postulación no encontrada"},
    "Etapa inválida": {"en": "Invalid stage", "es": "Etapa inválida"},
    "Candidato não encontrado": {"en": "Candidate not found", "es": "Candidato no encontrado"},
    "Candidato ou vaga não encontrados": {
        "en": "Candidate or job opening not found",
        "es": "Candidato o vacante no encontrados"},
    "O candidato já está nesta vaga": {
        "en": "The candidate is already in this job opening",
        "es": "El candidato ya está en esta vacante"},
    "Cargo e texto da pergunta são obrigatórios": {
        "en": "Role and question text are required",
        "es": "El cargo y el texto de la pregunta son obligatorios"},
    "Pergunta não encontrada": {"en": "Question not found", "es": "Pregunta no encontrada"},
    "Informe a pergunta e ao menos 2 opções": {
        "en": "Enter the question and at least 2 options",
        "es": "Ingresa la pregunta y al menos 2 opciones"},
    "Opção correta inválida": {"en": "Invalid correct option", "es": "Opción correcta inválida"},
    "Questão não encontrada": {"en": "Question not found", "es": "Pregunta no encontrada"},
    "Informe ao menos uma nota de 1 a 5": {
        "en": "Enter at least one rating from 1 to 5",
        "es": "Ingresa al menos una calificación del 1 al 5"},
    "Candidato e texto são obrigatórios": {
        "en": "Candidate and text are required",
        "es": "El candidato y el texto son obligatorios"},
    "Assunto e mensagem são obrigatórios": {
        "en": "Subject and message are required",
        "es": "El asunto y el mensaje son obligatorios"},
    "Currículo não encontrado": {"en": "Resume not found", "es": "Currículum no encontrado"},
    "Nome do cargo é obrigatório": {"en": "Role name is required", "es": "El nombre del cargo es obligatorio"},
    "Cargo e nome da competência são obrigatórios": {
        "en": "Role and competency name are required",
        "es": "El cargo y el nombre de la competencia son obligatorios"},
    "Competência não encontrada": {"en": "Competency not found", "es": "Competencia no encontrada"},
    "Informe o cargo": {"en": "Enter the role", "es": "Indica el cargo"},

    # ---------------------------------------------------------- e-mail/SMTP
    "SMTP não configurado": {"en": "SMTP is not configured", "es": "SMTP no está configurado"},
    "Preencha e salve os dados de SMTP antes de testar.": {
        "en": "Fill in and save the SMTP settings before testing.",
        "es": "Completa y guarda los datos de SMTP antes de probar."},
    "Informe um e-mail de destino para o teste.": {
        "en": "Enter a recipient email for the test.",
        "es": "Ingresa un correo de destino para la prueba."},

    # -------------------------------------------------------- PDF (relatório)
    "Biblioteca de PDF não instalada no servidor (pip3 install fpdf2)": {
        "en": "PDF library is not installed on the server (pip3 install fpdf2)",
        "es": "La biblioteca de PDF no está instalada en el servidor (pip3 install fpdf2)"},
    "Fontes do PDF não encontradas no servidor": {
        "en": "PDF fonts not found on the server",
        "es": "No se encontraron las fuentes del PDF en el servidor"},
    "O candidato ainda não tem resultados para gerar o relatório": {
        "en": "The candidate has no results yet to generate the report",
        "es": "El candidato aún no tiene resultados para generar el informe"},

    # ------------------------------------------------ análise de currículo IA
    "Configure a chave da API da Anthropic na aba Configurações": {
        "en": "Set up the Anthropic API key in the Settings tab",
        "es": "Configura la clave de la API de Anthropic en la pestaña Configuración"},
    "Este candidato não enviou currículo": {
        "en": "This candidate has not submitted a resume",
        "es": "Este candidato no envió currículum"},
    "A análise por IA exige currículo em PDF": {
        "en": "AI analysis requires a PDF resume",
        "es": "El análisis con IA requiere un currículum en PDF"},
    "Arquivo do currículo não encontrado": {"en": "Resume file not found", "es": "No se encontró el archivo del currículum"},
    "Biblioteca da Anthropic não instalada no servidor. Rode: pip3 install anthropic": {
        "en": "Anthropic library is not installed on the server. Run: pip3 install anthropic",
        "es": "La biblioteca de Anthropic no está instalada en el servidor. Ejecuta: pip3 install anthropic"},
    "A análise foi recusada pelos filtros de segurança do modelo": {
        "en": "The analysis was declined by the model's safety filters",
        "es": "El análisis fue rechazado por los filtros de seguridad del modelo"},
}

# Mensagens montadas com % ou format. Os grupos nomeados viram {nome} no modelo.
# Grupos chamados "detalhe" são traduzidos de novo (ex.: "Falha ao enviar: SMTP não configurado").
PADROES = [
    (r"^A senha deve ter ao menos (?P<n>\d+) caracteres$",
     {"en": "Password must be at least {n} characters",
      "es": "La contraseña debe tener al menos {n} caracteres"}),
    (r"^A nova senha deve ter ao menos (?P<n>\d+) caracteres$",
     {"en": "New password must be at least {n} characters",
      "es": "La nueva contraseña debe tener al menos {n} caracteres"}),
    (r"^A senha do dono deve ter ao menos (?P<n>\d+) caracteres$",
     {"en": "Owner password must be at least {n} characters",
      "es": "La contraseña del propietario debe tener al menos {n} caracteres"}),
    (r"^A senha do gestor deve ter ao menos (?P<n>\d+) caracteres$",
     {"en": "Manager password must be at least {n} characters",
      "es": "La contraseña del gestor debe tener al menos {n} caracteres"}),
    (r"^Arquivo maior que (?P<n>\d+) MB$",
     {"en": "File is larger than {n} MB", "es": "El archivo supera los {n} MB"}),
    (r"^A logo deve ter até (?P<n>\d+) MB$",
     {"en": "The logo must be {n} MB or smaller", "es": "El logo debe pesar como máximo {n} MB"}),
    # server.py: "Falha ao enviar: %s" % msg (teste de SMTP)
    (r"^Falha ao enviar: (?P<detalhe>.*)$",
     {"en": "Failed to send: {detalhe}", "es": "Error al enviar: {detalhe}"}),
    # server.py: "Não foi possível enviar: " + msg (e-mail ao candidato)
    (r"^Não foi possível enviar: (?P<detalhe>.*)$",
     {"en": "Could not send: {detalhe}", "es": "No se pudo enviar: {detalhe}"}),
    # server.py: "Falha na análise: %s" % exc (análise de currículo por IA)
    (r"^Falha na análise: (?P<detalhe>.*)$",
     {"en": "Analysis failed: {detalhe}", "es": "Error en el análisis: {detalhe}"}),
    # voz.py: RuntimeError("Ligação não iniciada: %s"), chega ao cliente dentro de start_failed
    (r"^Ligação não iniciada: (?P<detalhe>.*)$",
     {"en": "Call not started: {detalhe}", "es": "Llamada no iniciada: {detalhe}"}),
    # voz.py: str(ErroVoz("start_failed", detalhe)) == "start_failed: <detalhe>"
    (r"^start_failed: (?P<detalhe>.*)$",
     {"en": "Could not start the call: {detalhe}", "es": "No se pudo iniciar la llamada: {detalhe}"}),
]

# Códigos curtos do módulo de voz (validar_config, validar_roteiro, ErroVoz,
# motivo_bloqueio, webhook). Chegam no campo "erro" (e em "codigo").
CODIGOS = {
    "not_found": {"en": "Not found", "es": "No encontrado"},
    "forbidden": {"en": "Not allowed", "es": "Sin permiso"},
    "module_disabled": {"en": "Module not enabled for this company", "es": "Módulo no habilitado para esta empresa"},
    "invalid_data": {"en": "Invalid data", "es": "Datos inválidos"},
    "text_too_long": {"en": "Text is too long", "es": "El texto es demasiado largo"},
    "invalid_timezone": {"en": "Invalid time zone", "es": "Zona horaria inválida"},
    "invalid_time": {"en": "Invalid time (use HH:MM)", "es": "Hora inválida (usa HH:MM)"},
    "invalid_days": {"en": "Pick at least one day", "es": "Elige al menos un día"},
    "invalid_number": {"en": "Number out of range", "es": "Número fuera del rango permitido"},
    "invalid_language": {"en": "Invalid language", "es": "Idioma inválido"},
    "invalid_action": {"en": "Invalid action", "es": "Acción inválida"},
    "invalid_payload": {"en": "Invalid payload", "es": "Contenido inválido"},
    "invalid_signature": {"en": "Invalid signature", "es": "Firma inválida"},
    "webhook_not_configured": {"en": "Webhook is not configured", "es": "El webhook no está configurado"},
    "not_configured": {"en": "Set up the ElevenLabs integration first", "es": "Configura primero la integración con ElevenLabs"},
    "plan_limit": {"en": "Your plan's voice minutes for this month are used up", "es": "Se agotaron los minutos de voz de tu plan este mes"},  # planos.py
    "no_recording": {"en": "No recording available", "es": "No hay grabación disponible"},
    "in_call": {"en": "The candidate is on a call right now", "es": "El candidato está en una llamada ahora"},
    "status_changed": {"en": "The status changed. Reload the page.", "es": "El estado cambió. Recarga la página."},
    "start_failed": {"en": "Could not start the call", "es": "No se pudo iniciar la llamada"},
    "anonymized": {"en": "Candidate has been anonymized", "es": "El candidato fue anonimizado"},
    "do_not_call": {"en": "Candidate is marked Do not call", "es": "El candidato está marcado como No llamar"},
    "blocked_outcome": {
        "en": "The candidate asked not to be called or is not interested",
        "es": "El candidato pidió no ser llamado o no tiene interés"},
    "invalid_phone": {"en": "Invalid phone: calls only go to US numbers", "es": "Teléfono inválido: las llamadas solo salen a números de EE. UU."},
    "attempts_exhausted": {"en": "No attempts left. Reset attempts first.", "es": "Intentos agotados. Reinicia los intentos primero."},
    "disabled": {"en": "Voice screening is turned off", "es": "La evaluación por voz está desactivada"},
    "paused": {"en": "Voice screening is paused", "es": "La evaluación por voz está en pausa"},
    "wrong_status": {"en": "The application is not in the call queue", "es": "La postulación no está en la cola de llamadas"},
    "waiting_retry": {"en": "Waiting for the next retry", "es": "Esperando el próximo reintento"},
    "outside_window": {"en": "Outside the calling hours", "es": "Fuera del horario de llamadas"},
}

_IDIOMAS = ("en", "es")
_COMPILADOS = []
for _regex, _modelos in PADROES:
    try:
        _COMPILADOS.append((re.compile(_regex, re.S), _modelos))
    except re.error:
        pass


def traduzir(texto, idioma, _profundidade=0):
    """Traduz uma mensagem de erro para "en" ou "es". Devolve o texto original
    quando o idioma é "pt", desconhecido, ou não há tradução. Nunca lança."""
    try:
        if not isinstance(texto, str) or not texto:
            return texto
        lang = (idioma or "").strip().lower()[:2] if isinstance(idioma, str) else ""
        if lang not in _IDIOMAS:
            return texto
        chave = texto.strip()
        item = ERROS.get(chave) or CODIGOS.get(chave)
        if item and item.get(lang):
            return item[lang]
        if _profundidade > 3:
            return texto
        for regex, modelos in _COMPILADOS:
            m = regex.match(chave)
            if not m or not modelos.get(lang):
                continue
            grupos = {}
            for nome, valor in m.groupdict().items():
                valor = valor or ""
                if nome.startswith("detalhe"):
                    valor = traduzir(valor, lang, _profundidade + 1)
                grupos[nome] = valor
            return modelos[lang].format(**grupos)
        return texto
    except Exception:  # noqa: BLE001
        return texto

# entrada de candidatos (entrada.py)
ERROS['Apenas o administrador da empresa configura a entrada de candidatos'] = {"en": 'Only the company admin can set up candidate intake', "es": 'Solo el administrador de la empresa configura la entrada de candidatos'}
ERROS['Porta inválida'] = {"en": 'Invalid port', "es": 'Puerto inválido'}
ERROS['Preencha servidor, usuário e senha antes de ativar'] = {"en": 'Fill in server, username and password before turning it on', "es": 'Completa servidor, usuario y contraseña antes de activar'}
ERROS['A leitura já está em andamento'] = {"en": 'Reading is already in progress', "es": 'La lectura ya está en curso'}
ERROS['Envie a planilha CSV'] = {"en": 'Upload the CSV spreadsheet', "es": 'Sube la planilla CSV'}

# agenda de entrevistas (agenda.py)
ERROS['A agenda de entrevistas está desativada'] = {"en": 'Interview scheduling is turned off', "es": 'La agenda de entrevistas está desactivada'}
ERROS['Apenas o administrador da empresa configura a agenda'] = {"en": 'Only the company admin can set up interview scheduling', "es": 'Solo el administrador de la empresa configura la agenda'}
ERROS['Candidato sem e-mail'] = {"en": 'This candidate has no email', "es": 'El candidato no tiene correo electrónico'}
ERROS['Data bloqueada inválida (use AAAA-MM-DD)'] = {"en": 'Invalid blocked date (use YYYY-MM-DD)', "es": 'Fecha bloqueada inválida (usa AAAA-MM-DD)'}
ERROS['Dias da semana inválidos'] = {"en": 'Invalid weekdays', "es": 'Días de la semana inválidos'}
ERROS['Entrevista não encontrada'] = {"en": 'Interview not found', "es": 'Entrevista no encontrada'}
ERROS['Escolha ao menos um dia da semana'] = {"en": 'Pick at least one weekday', "es": 'Elige al menos un día de la semana'}
ERROS['Esta entrevista não está mais marcada'] = {"en": 'This interview is no longer scheduled', "es": 'Esta entrevista ya no está agendada'}
ERROS['Este horário não está mais disponível'] = {"en": 'This time is no longer available', "es": 'Este horario ya no está disponible'}
ERROS['Formato de entrevista inválido'] = {"en": 'Invalid interview format', "es": 'Formato de entrevista inválido'}
ERROS['Fuso horário inválido'] = {"en": 'Invalid time zone', "es": 'Zona horaria inválida'}
ERROS['Horário inválido'] = {"en": 'Invalid time', "es": 'Horario inválido'}
ERROS['Link de agendamento inválido'] = {"en": 'Invalid scheduling link', "es": 'Enlace de agenda inválido'}
ERROS['Nenhuma entrevista marcada'] = {"en": 'No interview scheduled', "es": 'No hay ninguna entrevista agendada'}
ERROS['O fim da janela deve ser depois do início'] = {"en": 'The window end must be after the start', "es": 'El fin del horario debe ser después del inicio'}
ERROS['Status inválido'] = {"en": 'Invalid status', "es": 'Estado inválido'}
ERROS['Valor inválido na agenda'] = {"en": 'Invalid value in the scheduling settings', "es": 'Valor inválido en la agenda'}

# segurança (seguranca.py)
ERROS["Apenas o administrador da empresa vê o histórico de acessos"] = {"en": "Only the company admin can see the access history", "es": "Solo el administrador de la empresa ve el historial de accesos"}

# banco de talentos (talentos.py)
ERROS['Data do lembrete inválida (use AAAA-MM-DD)'] = {"en": 'Invalid reminder date (use YYYY-MM-DD)', "es": 'Fecha del recordatorio inválida (usa AAAA-MM-DD)'}

# indicações (indicacoes.py)
ERROS["Apenas o administrador da empresa configura as indicações"] = {"en": "Only the company admin can set up referrals", "es": "Solo el administrador de la empresa configura las recomendaciones"}
ERROS["Número de dias inválido"] = {"en": "Invalid number of days", "es": "Número de días inválido"}
ERROS["Apenas o administrador da empresa registra o pagamento do bônus"] = {"en": "Only the company admin can record the bonus payment", "es": "Solo el administrador de la empresa registra el pago del bono"}
ERROS["Indicação não encontrada"] = {"en": "Referral not found", "es": "Recomendación no encontrada"}
ERROS["Candidato não encontrado"] = {"en": "Candidate not found", "es": "Candidato no encontrado"}

# planos, uso e cobrança (planos.py)
ERROS["Informe seu nome"] = {"en": "Enter your name", "es": "Ingresa tu nombre"}
ERROS["E-mail inválido"] = {"en": "Invalid email", "es": "Correo electrónico inválido"}
ERROS["Plano inválido"] = {"en": "Invalid plan", "es": "Plan inválido"}
ERROS["Ciclo de cobrança inválido"] = {"en": "Invalid billing cycle", "es": "Ciclo de facturación inválido"}
ERROS["Aceite os termos de uso para continuar"] = {"en": "Accept the terms of use to continue", "es": "Acepta los términos de uso para continuar"}
ERROS["Este e-mail já tem uma conta. Entre pelo painel do gestor."] = {"en": "This email already has an account. Sign in from the manager dashboard.", "es": "Este correo ya tiene una cuenta. Inicia sesión desde el panel del gerente."}
ERROS["Assinatura inválida"] = {"en": "Invalid signature", "es": "Firma inválida"}
ERROS["Stripe não configurado"] = {"en": "Stripe is not set up", "es": "Stripe no está configurado"}
ERROS["Esta empresa ainda não tem assinatura no Stripe"] = {"en": "This company does not have a Stripe subscription yet", "es": "Esta empresa todavía no tiene una suscripción en Stripe"}
ERROS["Apenas o administrador da empresa gerencia a assinatura"] = {"en": "Only the company admin can manage the subscription", "es": "Solo el administrador de la empresa gestiona la suscripción"}
ERROS["Não foi possível falar com o Stripe"] = {"en": "Could not reach Stripe", "es": "No fue posible comunicarse con Stripe"}
ERROS["Catálogo inválido"] = {"en": "Invalid plan catalog", "es": "Catálogo de planes inválido"}
ERROS["Código de plano inválido"] = {"en": "Invalid plan code", "es": "Código de plan inválido"}
ERROS["Códigos de plano repetidos"] = {"en": "Duplicate plan codes", "es": "Códigos de plan repetidos"}
ERROS["Informe o nome do plano"] = {"en": "Enter the plan name", "es": "Ingresa el nombre del plan"}
ERROS["Valor inválido no catálogo"] = {"en": "Invalid value in the plan catalog", "es": "Valor inválido en el catálogo de planes"}
ERROS["Premissas inválidas"] = {"en": "Invalid cost assumptions", "es": "Supuestos de costo inválidos"}
ERROS["Data inválida (use AAAA-MM-DD)"] = {"en": "Invalid date (use YYYY-MM-DD)", "es": "Fecha inválida (usa AAAA-MM-DD)"}

# onboarding de novos contratados (onboarding.py)
ERROS['A Seção 1 do I-9 ainda não foi preenchida'] = {"en": 'Form I-9 Section 1 has not been completed yet', "es": 'La Sección 1 del I-9 aún no se ha llenado'}
ERROS['A chave de criptografia dos dados não foi encontrada ou não confere. Fale com o administrador do sistema.'] = {"en": 'The data encryption key is missing or does not match. Contact the system administrator.', "es": 'La clave de cifrado de los datos no se encontró o no coincide. Comunícate con el administrador del sistema.'}
ERROS['Aceite o consentimento para documentos eletrônicos antes de continuar'] = {"en": 'Please accept the electronic records consent before continuing', "es": 'Acepta el consentimiento para documentos electrónicos antes de continuar'}
ERROS['Ainda há etapas pendentes'] = {"en": 'There are still steps to complete', "es": 'Todavía hay pasos pendientes'}
ERROS['Apenas o administrador da empresa cancela o onboarding'] = {"en": 'Only the company admin can cancel onboarding', "es": 'Solo el administrador de la empresa cancela la incorporación'}
ERROS['Apenas o administrador da empresa configura o onboarding'] = {"en": 'Only the company admin can set up onboarding', "es": 'Solo el administrador de la empresa configura la incorporación'}
ERROS['Apenas o administrador da empresa envia a proposta'] = {"en": 'Only the company admin can send the offer', "es": 'Solo el administrador de la empresa envía la oferta'}
ERROS['Apenas o administrador da empresa pode apagar dados sensíveis'] = {"en": 'Only the company admin can delete sensitive data', "es": 'Solo el administrador de la empresa puede borrar datos sensibles'}
ERROS['Apenas o administrador da empresa pode revelar dados sensíveis'] = {"en": 'Only the company admin can reveal sensitive data', "es": 'Solo el administrador de la empresa puede mostrar datos sensibles'}
ERROS['Arquivo maior que 10 MB'] = {"en": 'File is larger than 10 MB', "es": 'El archivo supera los 10 MB'}
ERROS['Confira os campos destacados'] = {"en": 'Please check the highlighted fields', "es": 'Revisa los campos marcados'}
ERROS['Dado não encontrado'] = {"en": 'Data not found', "es": 'Dato no encontrado'}
ERROS['Data de início inválida'] = {"en": 'Invalid start date', "es": 'Fecha de inicio inválida'}
ERROS['Desenhe a sua assinatura'] = {"en": 'Please draw your signature', "es": 'Dibuja tu firma'}
ERROS['Digite o seu nome completo'] = {"en": 'Please type your full name', "es": 'Escribe tu nombre completo'}
ERROS['Documento não encontrado'] = {"en": 'Document not found', "es": 'Documento no encontrado'}
ERROS['EIN inválido (9 dígitos)'] = {"en": 'Invalid EIN (9 digits)', "es": 'EIN inválido (9 dígitos)'}
ERROS['Envie um PDF de até 8 MB'] = {"en": 'Upload a PDF up to 8 MB', "es": 'Sube un PDF de hasta 8 MB'}
ERROS['Envie uma foto (JPG, PNG ou HEIC) ou um PDF'] = {"en": 'Upload a photo (JPG, PNG or HEIC) or a PDF', "es": 'Sube una foto (JPG, PNG o HEIC) o un PDF'}
ERROS['Escolha ao menos uma forma de pagamento'] = {"en": 'Choose at least one payment method', "es": 'Elige al menos una forma de pago'}
ERROS['Escreva a sua declaração pessoal'] = {"en": 'Please write your personal statement', "es": 'Escribe tu declaración personal'}
ERROS['Escreva o texto do documento'] = {"en": 'Write the document text', "es": 'Escribe el texto del documento'}
ERROS['Este onboarding foi cancelado'] = {"en": 'This onboarding was canceled', "es": 'Esta incorporación fue cancelada'}
ERROS['Este onboarding já foi concluído'] = {"en": 'This onboarding is already complete', "es": 'Esta incorporación ya fue completada'}
ERROS['Este onboarding não está mais em andamento'] = {"en": 'This onboarding is no longer in progress', "es": 'Esta incorporación ya no está en curso'}
ERROS['Forma de pagamento inválida'] = {"en": 'Invalid payment method', "es": 'Forma de pago inválida'}
ERROS['Formulário não encontrado'] = {"en": 'Form not found', "es": 'Formulario no encontrado'}
ERROS['Informe o título do documento'] = {"en": 'Enter the document title', "es": 'Escribe el título del documento'}
ERROS['Já existe um onboarding em andamento para este candidato'] = {"en": 'This candidate already has an onboarding in progress', "es": 'Este candidato ya tiene una incorporación en curso'}
ERROS['Limite de arquivos para este documento atingido'] = {"en": 'File limit reached for this document', "es": 'Se alcanzó el límite de archivos para este documento'}
ERROS['Link de onboarding inválido'] = {"en": 'Invalid onboarding link', "es": 'Enlace de incorporación inválido'}
ERROS['Marque a caixa de concordância para assinar'] = {"en": 'Check the agreement box to sign', "es": 'Marca la casilla de aceptación para firmar'}
ERROS['Não foi possível gerar o formulário. Tente de novo.'] = {"en": 'The form could not be generated. Please try again.', "es": 'No se pudo generar el formulario. Inténtalo de nuevo.'}
ERROS['Onboarding não encontrado'] = {"en": 'Onboarding not found', "es": 'Incorporación no encontrada'}
ERROS['Ordem das etapas inválida'] = {"en": 'Invalid step order', "es": 'Orden de pasos inválido'}
ERROS['Os dados ainda estão no prazo de retenção'] = {"en": 'The data is still within the retention period', "es": 'Los datos aún están dentro del plazo de retención'}
ERROS['Os dados do empregador nas configurações do onboarding estão incompletos ou inválidos'] = {"en": 'The employer details in the onboarding settings are incomplete or invalid', "es": 'Los datos del empleador en la configuración de la incorporación están incompletos o son inválidos'}
ERROS['Os formulários fiscais ainda não estão disponíveis. Tente mais tarde.'] = {"en": 'Tax forms are not available yet. Please try again later.', "es": 'Los formularios de impuestos aún no están disponibles. Intenta más tarde.'}
ERROS['Prazo inválido'] = {"en": 'Invalid deadline', "es": 'Fecha límite inválida'}
ERROS['Role o documento até o fim antes de assinar'] = {"en": 'Scroll to the end of the document before signing', "es": 'Desplázate hasta el final del documento antes de firmar'}
ERROS['Routing number inválido. Confira os 9 dígitos no seu cheque ou no app do banco.'] = {"en": 'Invalid routing number. Check the 9 digits on your check or in your bank app.', "es": 'Routing number inválido. Revisa los 9 dígitos en tu cheque o en la app del banco.'}
ERROS['Tipo de documento inválido'] = {"en": 'Invalid document type', "es": 'Tipo de documento inválido'}
ERROS['Tipo de vínculo inválido'] = {"en": 'Invalid employment type', "es": 'Tipo de vínculo inválido'}
ERROS['Unidade do pagamento inválida'] = {"en": 'Invalid pay unit', "es": 'Unidad de pago inválida'}
ERROS['Valor do pagamento inválido'] = {"en": 'Invalid pay amount', "es": 'Monto de pago inválido'}
ERROS['Valor inválido nas configurações do onboarding'] = {"en": 'Invalid value in the onboarding settings', "es": 'Valor inválido en la configuración de la incorporación'}

# cadastro público fechado (planos.py)
ERROS["As assinaturas ainda não estão abertas. Fale com a gente."] = {"en": "Signups are not open yet. Please get in touch.", "es": "Las suscripciones aún no están abiertas. Contáctanos."}

# limites de gestores e vagas ativas do plano (planos.py: erro_limite_gestores, erro_limite_vagas)
PADROES.append((
    r"^O plano (?P<plano>.+) permite até (?P<n>\d+) gestores ativos\. Faça upgrade do plano para adicionar mais gestores\.$",
    {"en": "The {plano} plan allows up to {n} active managers. Upgrade your plan to add more managers.",
     "es": "El plan {plano} permite hasta {n} gerentes activos. Mejora tu plan para agregar más gerentes."}))
PADROES.append((
    r"^O plano (?P<plano>.+) permite até (?P<n>\d+) vagas ativas\. Faça upgrade do plano ou encerre uma vaga para abrir outra\.$",
    {"en": "The {plano} plan allows up to {n} active jobs. Upgrade your plan or close a job to open another one.",
     "es": "El plan {plano} permite hasta {n} vacantes activas. Mejora tu plan o cierra una vacante para abrir otra."}))
for _regex, _modelos in PADROES[-2:]:
    _COMPILADOS.append((re.compile(_regex, re.S), _modelos))

# relatório de contratação (relatorios.py)
ERROS["Período inválido"] = {"en": "Invalid period", "es": "Período inválido"}
ERROS["Filtro inválido"] = {"en": "Invalid filter", "es": "Filtro inválido"}

# assistente de configuração e página Meu plano (assistente.py)
ERROS["Apenas o administrador da empresa acessa esta área"] = {"en": "Only the company admin can access this area", "es": "Solo el administrador de la empresa puede acceder a esta área"}
ERROS["Tipo de pedido inválido"] = {"en": "Invalid request type", "es": "Tipo de solicitud inválido"}
ERROS["Muitos pedidos hoje. Tente de novo amanhã."] = {"en": "Too many requests today. Please try again tomorrow.", "es": "Demasiadas solicitudes hoy. Inténtalo de nuevo mañana."}

# campos da vaga para o Google for Jobs (vagas_publicas.py)
ERROS["Tipo de emprego inválido"] = {"en": "Invalid employment type", "es": "Tipo de empleo inválido"}
ERROS["Salário inválido"] = {"en": "Invalid pay amount", "es": "Salario inválido"}
ERROS["O salário mínimo não pode ser maior que o máximo"] = {"en": "The minimum pay cannot be higher than the maximum", "es": "El salario mínimo no puede ser mayor que el máximo"}
ERROS["Unidade do salário inválida"] = {"en": "Invalid pay period", "es": "Unidad de salario inválida"}
ERROS["Moeda inválida"] = {"en": "Invalid currency", "es": "Moneda inválida"}
ERROS["Data de validade inválida"] = {"en": "Invalid expiration date", "es": "Fecha de vencimiento inválida"}

# números por empresa e Twilio (telefonia.py)
ERROS.update({
    "Configure a Twilio em Integrações primeiro": {"en": "Set up Twilio in Integrations first", "es": "Configura primero Twilio en Integraciones"},
    "Configure a ElevenLabs (chave e agente) em Integrações primeiro": {
        "en": "Set up ElevenLabs (API key and agent) in Integrations first",
        "es": "Configura primero ElevenLabs (clave y agente) en Integraciones"},
    "A Twilio recusou as credenciais. Confira o Account SID e o Auth Token.": {
        "en": "Twilio rejected the credentials. Check the Account SID and Auth Token.",
        "es": "Twilio rechazó las credenciales. Revisa el Account SID y el Auth Token."},
    "A ElevenLabs recusou a chave da API. Confira em Integrações.": {
        "en": "ElevenLabs rejected the API key. Check it in Integrations.",
        "es": "ElevenLabs rechazó la clave de la API. Revísala en Integraciones."},
    "Código de área inválido: use 3 dígitos, ex.: 860": {
        "en": "Invalid area code: use 3 digits, for example 860",
        "es": "Código de área inválido: usa 3 dígitos, por ejemplo 860"},
    "Número inválido: use o formato +1XXXXXXXXXX": {
        "en": "Invalid number: use the format +1XXXXXXXXXX",
        "es": "Número inválido: usa el formato +1XXXXXXXXXX"},
    "Confirme a compra e o custo mensal do número": {
        "en": "Confirm the purchase and the monthly cost of the number",
        "es": "Confirma la compra y el costo mensual del número"},
    "Confirme a liberação do número": {"en": "Confirm releasing the number", "es": "Confirma la liberación del número"},
    "Este número já está em uso na plataforma": {
        "en": "This number is already in use on the platform", "es": "Este número ya está en uso en la plataforma"},
    "Este número não está na sua conta Twilio": {
        "en": "This number is not in your Twilio account", "es": "Este número no está en tu cuenta de Twilio"},
    "Este número já foi liberado": {"en": "This number was already released", "es": "Este número ya fue liberado"},
    "Número não encontrado": {"en": "Number not found", "es": "Número no encontrado"},
    "Account SID inválido (começa com AC e tem 34 caracteres)": {
        "en": "Invalid Account SID (starts with AC and has 34 characters)",
        "es": "Account SID inválido (empieza con AC y tiene 34 caracteres)"},
    "Auth Token inválido": {"en": "Invalid Auth Token", "es": "Auth Token inválido"},
    "Sem conexão com a Twilio. Tente de novo.": {
        "en": "Could not reach Twilio. Try again.", "es": "No se pudo conectar con Twilio. Inténtalo de nuevo."},
    "Sem conexão com a ElevenLabs. Tente de novo.": {
        "en": "Could not reach ElevenLabs. Try again.", "es": "No se pudo conectar con ElevenLabs. Inténtalo de nuevo."},
})
PADROES.append((r"^Erro na Twilio: (?P<detalhe>.*)$",
                {"en": "Twilio error: {detalhe}", "es": "Error de Twilio: {detalhe}"}))
PADROES.append((r"^Erro na ElevenLabs: (?P<detalhe>.*)$",
                {"en": "ElevenLabs error: {detalhe}", "es": "Error de ElevenLabs: {detalhe}"}))
PADROES.append((r"^O número está na Twilio, mas a importação na ElevenLabs falhou\. (?P<detalhe>.*)$",
                {"en": "The number is in Twilio, but importing it into ElevenLabs failed. {detalhe}",
                 "es": "El número está en Twilio, pero falló la importación en ElevenLabs. {detalhe}"}))
for _regex, _modelos in PADROES[-3:]:
    _COMPILADOS.append((re.compile(_regex, re.S), _modelos))

# banco de talentos: aviso de vaga aberta (campanhas.py)
ERROS["A vaga precisa estar aberta para avisar o banco de talentos"] = {"en": "The job must be open to notify the talent pool", "es": "La vacante debe estar abierta para avisar al banco de talentos"}
ERROS["Configure o envio de e-mails (SMTP) antes de avisar o banco de talentos"] = {"en": "Set up email sending (SMTP) before notifying the talent pool", "es": "Configura el envío de correos (SMTP) antes de avisar al banco de talentos"}
ERROS["Nenhum candidato para avisar com esses filtros"] = {"en": "No candidates to notify with these filters", "es": "No hay candidatos para avisar con estos filtros"}
