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
