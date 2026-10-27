/* =====================================================================
   Idiomas do Painel do Dono: português (pt), inglês (en) e espanhol (es).

   Ordem de escolha do idioma:
     1. localStorage "idioma" (compartilhado com o resto do produto)
     2. idioma do navegador (pt*, es*, senão en)

   Uso: td(chave, { variavel: valor }) devolve o texto no idioma atual.
   Dados digitados pelos usuários (nomes de empresas, notas, planos)
   vêm da API e não são traduzidos.
   ===================================================================== */

const IDIOMAS_DONO = ["pt", "en", "es"];
const LANG_HTML_DONO = { pt: "pt-BR", en: "en-US", es: "es-US" };
const NOMES_IDIOMA_DONO = { pt: "Português", en: "English", es: "Español" };

const I18N_DONO = {
  // ================================================================ PT
  pt: {
    titulo_pagina: "Bússola · Painel do Dono",
    topo_sub: "Painel do dono do software",
    inicio: "Início",
    sair: "Sair",
    idioma: "Idioma",
    carregando: "Carregando…",
    erro_comunicacao: "Erro de comunicação",
    sessao_expirada: "Sessão expirada",

    // configuração inicial
    setup_titulo: "Configuração do dono",
    setup_desc: "Primeiro acesso ao painel do proprietário do software. Defina a senha mestra (mínimo 8 caracteres). Ela é independente das contas de gestor.",
    setup_senha: "Senha do dono",
    setup_confirmar: "Confirmar senha",
    setup_criar: "Criar acesso do dono",
    senhas_nao_conferem: "As senhas não conferem.",

    // login
    login_titulo: "Acesso do dono",
    login_desc: "Área exclusiva do proprietário do software.",
    login_senha: "Senha mestra",
    login_entrar: "Entrar",

    // abas
    aba_empresas: "Empresas",
    aba_visao: "Visão geral e saúde",
    aba_contas: "Todas as contas",
    aba_integracoes: "Integrações",
    aba_config: "Configurações",

    // visão geral
    m_empresas: "Empresas",
    m_contas_gestor: "Contas de gestor",
    m_pessoas_avaliadas: "Pessoas avaliadas",
    m_vagas_criadas: "Vagas criadas",
    m_avaliacoes_completas: "Avaliações completas",
    saude_titulo: "Saúde do sistema",
    saude_versao: "Versão",
    saude_banco: "Tamanho do banco",
    saude_ia: "IA (Anthropic)",
    saude_email: "E-mail (SMTP)",
    saude_backups: "Backups recentes",
    configurada: "Configurada",
    nao_configurada: "Não configurada",
    configurado: "Configurado",
    nao_configurado: "Não configurado",
    nenhum: "nenhum",
    mb: "{n} MB",
    uso_titulo: "Uso por empresa",
    col_empresa: "Empresa",
    col_candidatos: "Candidatos",
    col_vagas_abertas: "Vagas abertas",
    col_ligacoes: "Ligações",
    nenhuma_empresa: "Nenhuma empresa ainda.",
    log_titulo: "Log do servidor (últimas linhas)",
    sem_registros: "Sem registros.",

    // todas as contas
    contas_titulo: "Todas as contas de gestor",
    contas_desc: "Entre em qualquer conta para dar suporte ou redefina a senha de quem perdeu o acesso. Cada acesso seu abre o painel exatamente como o gestor o vê, só com os dados da empresa dele.",
    col_nome: "Nome",
    col_login: "Login",
    col_local: "Local",
    col_perfil: "Perfil",
    col_candidatos_visiveis: "Candidatos visíveis",
    sem_email: "sem e-mail",
    inativo: "inativo",
    pendente: "pendente",
    empresa_toda: "empresa toda",
    perfil_admin: "Admin",
    perfil_gestor: "Gestor",
    entrar_conta: "Entrar na conta",
    redefinir_senha: "Redefinir senha",
    nenhuma_conta: "Nenhuma conta criada ainda.",
    nenhum_gestor: "Nenhum gestor ainda.",
    prompt_nova_senha: "Nova senha para esta conta (mínimo 6 caracteres):",
    senha_redefinida: "Senha redefinida.",

    // empresas
    empresas_titulo: "Empresas",
    empresas_desc: "Cada empresa é uma subconta isolada: só enxerga os próprios gestores, cargos, vagas, candidatos e ligações. Só você vê todas.",
    m_gestores: "Gestores",
    m_cargos: "Cargos",
    m_vagas_abertas: "Vagas abertas",
    m_candidatos: "Candidatos",
    m_ligacoes_voz: "Ligações de voz",
    status_ativa: "ativa",
    status_teste: "teste",
    status_suspensa: "suspensa",
    status_cancelada: "cancelada",
    ph_plano: "Plano (ex.: mensal)",
    ph_valor: "Valor",
    ph_notas: "Notas",
    ph_slug: "link (ex.: bhs-ct)",
    title_slug: "Link público da empresa",
    mod_diagnostico: "Diagnóstico de Competências",
    mod_voz: "Triagem por Voz",
    salvar: "Salvar",
    salvo: "Salvo ✓",
    gestores_acesso: "Gestores e acesso",
    trocar_logo: "Trocar logo",
    enviar_logo: "Enviar logo",
    nova_empresa: "Nova empresa",
    ne_nome: "Nome da empresa",
    ne_situacao: "Situação",
    ne_admin_desc: "Primeiro administrador da empresa (opcional agora, dá para criar depois):",
    campo_nome: "Nome",
    campo_email: "E-mail",
    campo_login: "Login",
    campo_senha_min8: "Senha (mín. 8)",
    criar_empresa: "Criar empresa",
    adicionar_gestor: "Adicionar gestor",

    // integrações
    int_titulo: "Integrações da plataforma (valem para todas as empresas)",
    int_desc: "Estes são os únicos recursos do sistema que dependem de serviços externos. Tudo o mais funciona sem custo. Sem estas credenciais, os botões de IA e as notificações por e-mail apenas ficam indisponíveis.",
    ia_titulo: "Análise de currículo por IA",
    ia_desc: "Usa a API da Anthropic (Claude Haiku 4.5, rápido e econômico). Crie uma chave em console.anthropic.com. Custo aproximado: US$ 25 a cada mil currículos analisados. Status:",
    ia_configurada_final: "Configurada (...{final})",
    ia_chave: "Chave da API Anthropic",
    ph_trocar: "Preencher apenas para trocar",
    smtp_titulo: "E-mail para candidatos (SMTP)",
    smtp_desc: "Com o SMTP configurado, o sistema envia automaticamente: confirmação de inscrição com link de acesso ao candidato, avisos de mudança de etapa, e alertas aos gestores (novo candidato e avaliação completa com o match). Funciona com qualquer SMTP; no Gmail use uma senha de app. Status:",
    smtp_servidor: "Servidor SMTP",
    smtp_porta: "Porta",
    smtp_porta_dica: "(587 STARTTLS ou 465 SSL)",
    smtp_usuario: "Usuário",
    ph_usuario: "voce@gmail.com",
    smtp_senha: "Senha",
    dica_trocar: "(preencher apenas para trocar)",
    smtp_remetente: "Remetente",
    opcional: "(opcional)",
    ph_remetente: "selecao@suaempresa.com",
    url_publica: "Endereço público do sistema",
    url_publica_dica: "(usado nos links dos e-mails)",
    ph_url: "http://localhost:8080 ou https://rh.seudominio.com",
    retencao: "Retenção de dados (LGPD)",
    retencao_dica: "(anonimizar candidatos automaticamente após)",
    retencao_nunca: "Nunca (manter tudo)",
    meses: "{n} meses",
    salvar_integracoes: "Salvar integrações",
    salvar_testar: "Salvar e enviar e-mail de teste",
    email_teste: "E-mail para o teste",
    ph_email_teste: "voce@seudominio.com",
    carregando_voz: "Carregando integração de voz…",
    integracoes_salvas: "Integrações salvas.",
    enviando_teste: "Salvando e enviando e-mail de teste…",
    teste_enviado: "E-mail de teste enviado para {destino}. Verifique a caixa de entrada (e o spam).",

    // voz (ElevenLabs)
    voz_titulo: "Triagem por voz (ElevenLabs)",
    voz_desc: "Conta da plataforma usada pela Francisca em todas as empresas que tiverem o módulo Triagem por Voz.",
    voz_chave: "Chave da API",
    voz_chave_salva: "Chave salva terminando em {final}. Deixe vazio para manter.",
    voz_segredo: "Segredo do webhook",
    voz_agente: "ID da agente",
    voz_telefone: "ID do número de telefone",
    voz_webhook: "Endereço do webhook para colar no ElevenLabs:",
    voz_salvar: "Salvar integração de voz",
    voz_salva: "Integração de voz salva.",

    // configurações
    cf_titulo: "Alterar senha do dono",
    cf_atual: "Senha atual",
    cf_nova: "Nova senha (mín. 8 caracteres)",
    cf_salvar: "Alterar senha",
    cf_alterada: "Senha alterada.",
  },

  // ================================================================ EN
  en: {
    titulo_pagina: "Bússola · Owner Panel",
    topo_sub: "Software owner panel",
    inicio: "Home",
    sair: "Sign out",
    idioma: "Language",
    carregando: "Loading…",
    erro_comunicacao: "Connection error",
    sessao_expirada: "Session expired",

    setup_titulo: "Owner setup",
    setup_desc: "First access to the software owner panel. Set the master password (at least 8 characters). It is separate from the manager accounts.",
    setup_senha: "Owner password",
    setup_confirmar: "Confirm password",
    setup_criar: "Create owner access",
    senhas_nao_conferem: "The passwords do not match.",

    login_titulo: "Owner access",
    login_desc: "Restricted to the software owner.",
    login_senha: "Master password",
    login_entrar: "Sign in",

    aba_empresas: "Companies",
    aba_visao: "Overview and health",
    aba_contas: "All accounts",
    aba_integracoes: "Integrations",
    aba_config: "Settings",

    m_empresas: "Companies",
    m_contas_gestor: "Manager accounts",
    m_pessoas_avaliadas: "People assessed",
    m_vagas_criadas: "Jobs created",
    m_avaliacoes_completas: "Completed assessments",
    saude_titulo: "System health",
    saude_versao: "Version",
    saude_banco: "Database size",
    saude_ia: "AI (Anthropic)",
    saude_email: "Email (SMTP)",
    saude_backups: "Recent backups",
    configurada: "Configured",
    nao_configurada: "Not configured",
    configurado: "Configured",
    nao_configurado: "Not configured",
    nenhum: "none",
    mb: "{n} MB",
    uso_titulo: "Usage by company",
    col_empresa: "Company",
    col_candidatos: "Candidates",
    col_vagas_abertas: "Open jobs",
    col_ligacoes: "Calls",
    nenhuma_empresa: "No companies yet.",
    log_titulo: "Server log (latest lines)",
    sem_registros: "No entries.",

    contas_titulo: "All manager accounts",
    contas_desc: "Sign in to any account to provide support, or reset the password for someone who lost access. Each time you sign in, the panel opens exactly as the manager sees it, with only their company's data.",
    col_nome: "Name",
    col_login: "Username",
    col_local: "Location",
    col_perfil: "Role",
    col_candidatos_visiveis: "Visible candidates",
    sem_email: "no email",
    inativo: "inactive",
    pendente: "pending",
    empresa_toda: "entire company",
    perfil_admin: "Admin",
    perfil_gestor: "Manager",
    entrar_conta: "Sign in to account",
    redefinir_senha: "Reset password",
    nenhuma_conta: "No accounts created yet.",
    nenhum_gestor: "No managers yet.",
    prompt_nova_senha: "New password for this account (at least 6 characters):",
    senha_redefinida: "Password reset.",

    empresas_titulo: "Companies",
    empresas_desc: "Each company is an isolated sub-account: it only sees its own managers, positions, jobs, candidates and calls. Only you can see all of them.",
    m_gestores: "Managers",
    m_cargos: "Positions",
    m_vagas_abertas: "Open jobs",
    m_candidatos: "Candidates",
    m_ligacoes_voz: "Voice calls",
    status_ativa: "active",
    status_teste: "trial",
    status_suspensa: "suspended",
    status_cancelada: "canceled",
    ph_plano: "Plan (e.g., monthly)",
    ph_valor: "Amount",
    ph_notas: "Notes",
    ph_slug: "link (e.g., bhs-ct)",
    title_slug: "Company public link",
    mod_diagnostico: "Competency Assessment",
    mod_voz: "Voice Screening",
    salvar: "Save",
    salvo: "Saved ✓",
    gestores_acesso: "Managers and access",
    trocar_logo: "Change logo",
    enviar_logo: "Upload logo",
    nova_empresa: "New company",
    ne_nome: "Company name",
    ne_situacao: "Status",
    ne_admin_desc: "The company's first administrator (optional now, you can create one later):",
    campo_nome: "Name",
    campo_email: "Email",
    campo_login: "Username",
    campo_senha_min8: "Password (min. 8)",
    criar_empresa: "Create company",
    adicionar_gestor: "Add manager",

    int_titulo: "Platform integrations (apply to all companies)",
    int_desc: "These are the only system features that rely on external services. Everything else works at no cost. Without these credentials, the AI buttons and email notifications are simply unavailable.",
    ia_titulo: "AI resume analysis",
    ia_desc: "Uses the Anthropic API (Claude Haiku 4.5, fast and cost effective). Create a key at console.anthropic.com. Approximate cost: US$25 per 1,000 resumes analyzed. Status:",
    ia_configurada_final: "Configured (...{final})",
    ia_chave: "Anthropic API key",
    ph_trocar: "Fill in only to replace",
    smtp_titulo: "Candidate email (SMTP)",
    smtp_desc: "With SMTP configured, the system automatically sends: application confirmation with the candidate's access link, stage change notices, and alerts to managers (new candidate and completed assessment with the match). Works with any SMTP server; for Gmail, use an app password. Status:",
    smtp_servidor: "SMTP server",
    smtp_porta: "Port",
    smtp_porta_dica: "(587 STARTTLS or 465 SSL)",
    smtp_usuario: "Username",
    ph_usuario: "you@gmail.com",
    smtp_senha: "Password",
    dica_trocar: "(fill in only to replace)",
    smtp_remetente: "Sender",
    opcional: "(optional)",
    ph_remetente: "hiring@yourcompany.com",
    url_publica: "System public address",
    url_publica_dica: "(used in email links)",
    ph_url: "http://localhost:8080 or https://hr.yourdomain.com",
    retencao: "Data retention (privacy)",
    retencao_dica: "(automatically anonymize candidates after)",
    retencao_nunca: "Never (keep everything)",
    meses: "{n} months",
    salvar_integracoes: "Save integrations",
    salvar_testar: "Save and send test email",
    email_teste: "Test email recipient",
    ph_email_teste: "you@yourdomain.com",
    carregando_voz: "Loading voice integration…",
    integracoes_salvas: "Integrations saved.",
    enviando_teste: "Saving and sending test email…",
    teste_enviado: "Test email sent to {destino}. Check your inbox (and spam folder).",

    voz_titulo: "Voice screening (ElevenLabs)",
    voz_desc: "Platform account used by Francisca across all companies that have the Voice Screening module.",
    voz_chave: "API key",
    voz_chave_salva: "Saved key ending in {final}. Leave blank to keep it.",
    voz_segredo: "Webhook secret",
    voz_agente: "Agent ID",
    voz_telefone: "Phone number ID",
    voz_webhook: "Webhook URL to paste into ElevenLabs:",
    voz_salvar: "Save voice integration",
    voz_salva: "Voice integration saved.",

    cf_titulo: "Change owner password",
    cf_atual: "Current password",
    cf_nova: "New password (min. 8 characters)",
    cf_salvar: "Change password",
    cf_alterada: "Password changed.",
  },

  // ================================================================ ES
  es: {
    titulo_pagina: "Bússola · Panel del Propietario",
    topo_sub: "Panel del propietario del software",
    inicio: "Inicio",
    sair: "Cerrar sesión",
    idioma: "Idioma",
    carregando: "Cargando…",
    erro_comunicacao: "Error de comunicación",
    sessao_expirada: "Sesión expirada",

    setup_titulo: "Configuración del propietario",
    setup_desc: "Primer acceso al panel del propietario del software. Define la contraseña maestra (mínimo 8 caracteres). Es independiente de las cuentas de gerente.",
    setup_senha: "Contraseña del propietario",
    setup_confirmar: "Confirmar contraseña",
    setup_criar: "Crear acceso del propietario",
    senhas_nao_conferem: "Las contraseñas no coinciden.",

    login_titulo: "Acceso del propietario",
    login_desc: "Área exclusiva del propietario del software.",
    login_senha: "Contraseña maestra",
    login_entrar: "Ingresar",

    aba_empresas: "Empresas",
    aba_visao: "Resumen y estado",
    aba_contas: "Todas las cuentas",
    aba_integracoes: "Integraciones",
    aba_config: "Configuración",

    m_empresas: "Empresas",
    m_contas_gestor: "Cuentas de gerente",
    m_pessoas_avaliadas: "Personas evaluadas",
    m_vagas_criadas: "Vacantes creadas",
    m_avaliacoes_completas: "Evaluaciones completas",
    saude_titulo: "Estado del sistema",
    saude_versao: "Versión",
    saude_banco: "Tamaño de la base de datos",
    saude_ia: "IA (Anthropic)",
    saude_email: "Correo (SMTP)",
    saude_backups: "Copias de seguridad recientes",
    configurada: "Configurada",
    nao_configurada: "No configurada",
    configurado: "Configurado",
    nao_configurado: "No configurado",
    nenhum: "ninguna",
    mb: "{n} MB",
    uso_titulo: "Uso por empresa",
    col_empresa: "Empresa",
    col_candidatos: "Candidatos",
    col_vagas_abertas: "Vacantes abiertas",
    col_ligacoes: "Llamadas",
    nenhuma_empresa: "Todavía no hay empresas.",
    log_titulo: "Registro del servidor (últimas líneas)",
    sem_registros: "Sin registros.",

    contas_titulo: "Todas las cuentas de gerente",
    contas_desc: "Ingresa a cualquier cuenta para dar soporte o restablece la contraseña de quien perdió el acceso. Cada vez que ingresas, el panel se abre exactamente como lo ve el gerente, solo con los datos de su empresa.",
    col_nome: "Nombre",
    col_login: "Usuario",
    col_local: "Ubicación",
    col_perfil: "Perfil",
    col_candidatos_visiveis: "Candidatos visibles",
    sem_email: "sin correo",
    inativo: "inactivo",
    pendente: "pendiente",
    empresa_toda: "toda la empresa",
    perfil_admin: "Admin",
    perfil_gestor: "Gerente",
    entrar_conta: "Ingresar a la cuenta",
    redefinir_senha: "Restablecer contraseña",
    nenhuma_conta: "Todavía no se ha creado ninguna cuenta.",
    nenhum_gestor: "Todavía no hay gerentes.",
    prompt_nova_senha: "Nueva contraseña para esta cuenta (mínimo 6 caracteres):",
    senha_redefinida: "Contraseña restablecida.",

    empresas_titulo: "Empresas",
    empresas_desc: "Cada empresa es una subcuenta aislada: solo ve sus propios gerentes, puestos, vacantes, candidatos y llamadas. Solo tú ves todas.",
    m_gestores: "Gerentes",
    m_cargos: "Puestos",
    m_vagas_abertas: "Vacantes abiertas",
    m_candidatos: "Candidatos",
    m_ligacoes_voz: "Llamadas de voz",
    status_ativa: "activa",
    status_teste: "prueba",
    status_suspensa: "suspendida",
    status_cancelada: "cancelada",
    ph_plano: "Plan (ej.: mensual)",
    ph_valor: "Monto",
    ph_notas: "Notas",
    ph_slug: "enlace (ej.: bhs-ct)",
    title_slug: "Enlace público de la empresa",
    mod_diagnostico: "Diagnóstico de Competencias",
    mod_voz: "Evaluación por Voz",
    salvar: "Guardar",
    salvo: "Guardado ✓",
    gestores_acesso: "Gerentes y acceso",
    trocar_logo: "Cambiar logo",
    enviar_logo: "Subir logo",
    nova_empresa: "Nueva empresa",
    ne_nome: "Nombre de la empresa",
    ne_situacao: "Estado",
    ne_admin_desc: "Primer administrador de la empresa (opcional ahora, se puede crear después):",
    campo_nome: "Nombre",
    campo_email: "Correo electrónico",
    campo_login: "Usuario",
    campo_senha_min8: "Contraseña (mín. 8)",
    criar_empresa: "Crear empresa",
    adicionar_gestor: "Agregar gerente",

    int_titulo: "Integraciones de la plataforma (aplican a todas las empresas)",
    int_desc: "Estos son los únicos recursos del sistema que dependen de servicios externos. Todo lo demás funciona sin costo. Sin estas credenciales, los botones de IA y las notificaciones por correo simplemente no están disponibles.",
    ia_titulo: "Análisis de currículum con IA",
    ia_desc: "Usa la API de Anthropic (Claude Haiku 4.5, rápido y económico). Crea una clave en console.anthropic.com. Costo aproximado: US$ 25 por cada mil currículums analizados. Estado:",
    ia_configurada_final: "Configurada (...{final})",
    ia_chave: "Clave de la API de Anthropic",
    ph_trocar: "Completar solo para cambiarla",
    smtp_titulo: "Correo para candidatos (SMTP)",
    smtp_desc: "Con el SMTP configurado, el sistema envía automáticamente: confirmación de postulación con el enlace de acceso del candidato, avisos de cambio de etapa y alertas a los gerentes (nuevo candidato y evaluación completa con el match). Funciona con cualquier SMTP; en Gmail usa una contraseña de aplicación. Estado:",
    smtp_servidor: "Servidor SMTP",
    smtp_porta: "Puerto",
    smtp_porta_dica: "(587 STARTTLS o 465 SSL)",
    smtp_usuario: "Usuario",
    ph_usuario: "tu@gmail.com",
    smtp_senha: "Contraseña",
    dica_trocar: "(completar solo para cambiarla)",
    smtp_remetente: "Remitente",
    opcional: "(opcional)",
    ph_remetente: "seleccion@tuempresa.com",
    url_publica: "Dirección pública del sistema",
    url_publica_dica: "(se usa en los enlaces de los correos)",
    ph_url: "http://localhost:8080 o https://rh.tudominio.com",
    retencao: "Retención de datos (privacidad)",
    retencao_dica: "(anonimizar candidatos automáticamente después de)",
    retencao_nunca: "Nunca (conservar todo)",
    meses: "{n} meses",
    salvar_integracoes: "Guardar integraciones",
    salvar_testar: "Guardar y enviar correo de prueba",
    email_teste: "Correo para la prueba",
    ph_email_teste: "tu@tudominio.com",
    carregando_voz: "Cargando integración de voz…",
    integracoes_salvas: "Integraciones guardadas.",
    enviando_teste: "Guardando y enviando correo de prueba…",
    teste_enviado: "Correo de prueba enviado a {destino}. Revisa la bandeja de entrada (y el spam).",

    voz_titulo: "Evaluación por voz (ElevenLabs)",
    voz_desc: "Cuenta de la plataforma que usa Francisca en todas las empresas que tengan el módulo Evaluación por Voz.",
    voz_chave: "Clave de la API",
    voz_chave_salva: "Clave guardada que termina en {final}. Déjalo vacío para conservarla.",
    voz_segredo: "Secreto del webhook",
    voz_agente: "ID de la agente",
    voz_telefone: "ID del número de teléfono",
    voz_webhook: "Dirección del webhook para pegar en ElevenLabs:",
    voz_salvar: "Guardar integración de voz",
    voz_salva: "Integración de voz guardada.",

    cf_titulo: "Cambiar contraseña del propietario",
    cf_atual: "Contraseña actual",
    cf_nova: "Nueva contraseña (mín. 8 caracteres)",
    cf_salvar: "Cambiar contraseña",
    cf_alterada: "Contraseña cambiada.",
  },
};

// ------------------------------------------------ escolha do idioma
function normalizarIdiomaDono(v) {
  const s = String(v || "").toLowerCase().slice(0, 2);
  return IDIOMAS_DONO.includes(s) ? s : "";
}

function idiomaNavegadorDono() {
  const n = String(navigator.language || "").toLowerCase();
  if (n.startsWith("pt")) return "pt";
  if (n.startsWith("es")) return "es";
  return "en";
}

function lerIdiomaDono() {
  try { return normalizarIdiomaDono(localStorage.getItem("idioma")); } catch (e) { return ""; }
}

let idiomaDono = lerIdiomaDono() || idiomaNavegadorDono();

// ------------------------------------------------ tradução e formatação
function td(chave, vars) {
  const dic = I18N_DONO[idiomaDono] || I18N_DONO.pt;
  let s = dic[chave];
  if (s === undefined) s = I18N_DONO.pt[chave];
  if (s === undefined) return chave;
  if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
  return s;
}

function localeDono() {
  return LANG_HTML_DONO[idiomaDono] || "pt-BR";
}

// números no formato do idioma (1.234 em pt, 1,234 em en/es-US)
function fmtNumDono(n) {
  const v = Number(n);
  if (n === null || n === undefined || n === "" || Number.isNaN(v)) return esc(n ?? "");
  return v.toLocaleString(localeDono());
}

// datas no formato do idioma (aceita ISO ou timestamp)
function fmtDataDono(d, comHora) {
  const dt = d instanceof Date ? d : new Date(d);
  if (Number.isNaN(dt.getTime())) return esc(d ?? "");
  const op = { dateStyle: "short" };
  if (comHora) op.timeStyle = "short";
  return dt.toLocaleString(localeDono(), op);
}

// rótulo traduzido da situação da empresa (o valor enviado ao servidor continua em português)
function rotuloStatusDono(s) {
  const k = "status_" + s;
  return k in I18N_DONO.pt ? td(k) : s;
}

// nome traduzido do módulo pela chave; senão usa o rótulo vindo do servidor
function rotuloModuloDono(chave, rotuloServidor) {
  const k = "mod_" + chave;
  return k in I18N_DONO.pt ? td(k) : rotuloServidor;
}

// ------------------------------------------------ aplicação na página
function aplicarTextosDono() {
  document.documentElement.lang = localeDono();
  document.title = td("titulo_pagina");
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = td(el.dataset.i18n);
  });
  document.querySelectorAll(".seletor-idioma button").forEach((b) => {
    b.classList.toggle("ativo", b.dataset.lang === idiomaDono);
    b.setAttribute("aria-pressed", b.dataset.lang === idiomaDono ? "true" : "false");
  });
  document.querySelectorAll(".seletor-idioma").forEach((c) => c.setAttribute("aria-label", td("idioma")));
}

function definirIdiomaDono(lang) {
  idiomaDono = normalizarIdiomaDono(lang) || "pt";
  try { localStorage.setItem("idioma", idiomaDono); } catch (e) { /* armazenamento bloqueado */ }
  aplicarTextosDono();
}

// seletor PT / EN / ES na barra superior (aparece também no login e na configuração inicial)
function montarSeletorIdiomaDono(aoTrocar) {
  if (!document.getElementById("estilo-seletor-idioma")) {
    const estilo = document.createElement("style");
    estilo.id = "estilo-seletor-idioma";
    estilo.textContent =
      ".seletor-idioma{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;margin-right:6px;flex-shrink:0}" +
      ".seletor-idioma button{background:none;border:0;color:var(--text-2);font:inherit;font-size:.72rem;font-weight:600;letter-spacing:.05em;padding:6px 9px;cursor:pointer;line-height:1}" +
      ".seletor-idioma button:hover{color:var(--text)}" +
      ".seletor-idioma button.ativo{background:var(--surface-2);color:var(--text)}";
    document.head.appendChild(estilo);
  }
  const acoes = document.querySelector(".topbar .actions");
  if (!acoes || acoes.querySelector(".seletor-idioma")) return;
  const caixa = document.createElement("div");
  caixa.className = "seletor-idioma";
  caixa.setAttribute("role", "group");
  caixa.innerHTML = IDIOMAS_DONO.map((cod) =>
    `<button type="button" data-lang="${cod}" title="${NOMES_IDIOMA_DONO[cod]}">${cod.toUpperCase()}</button>`
  ).join("");
  acoes.insertBefore(caixa, acoes.firstChild);
  caixa.querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => {
      if (b.dataset.lang === idiomaDono) return;
      definirIdiomaDono(b.dataset.lang);
      if (aoTrocar) aoTrocar(idiomaDono);
    })
  );
  aplicarTextosDono();
}
