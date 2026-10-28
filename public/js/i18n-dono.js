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

// ================================================================
// Planos e preços (planos.py): textos da aba "Planos e preços" e da
// seção do Stripe em Integrações.
// ================================================================
Object.assign(I18N_DONO.pt, {
  aba_planos: "Planos e preços",
  pl_assin_titulo: "Cadastro público e teste grátis", pl_assin_desc: "Quando aberto, qualquer pessoa cria uma empresa pela página de assinatura e ganha o teste grátis (com minutos de ligação). Deixe fechado até revisar preços, termos e privacidade.", pl_assin_rotulo: "Abrir o cadastro público", pl_assin_previa: "Ver a prévia da nova página inicial", pl_assin_confirma: "Abrir o cadastro público? Novas empresas poderão se cadastrar e usar os minutos de teste.",
  pl_resumo: "Resumo do mês", pl_mes: "Mês", pl_mrr: "Receita recorrente (MRR)", pl_custo_var_mes: "Custo variável real",
  pl_custo_fixo_mes: "Custo fixo (manutenção)", pl_resultado: "Resultado", pl_pagantes: "Empresas pagantes",
  pl_uso_titulo: "Uso por empresa", pl_uso_desc: "Minutos de voz do mês (horário de Nova York), custo real estimado, receita e margem de cada empresa.",
  pl_empresa: "Empresa", pl_plano: "Plano", pl_minutos: "Minutos (uso / limite)", pl_custo_real: "Custo real", pl_receita: "Receita",
  pl_margem: "Margem", pl_ajustar: "Ajustar", pl_sem_plano: "Sem plano (sem limite)", pl_mensal: "Mensal", pl_anual: "Anual",
  pl_ciclo: "Ciclo", pl_min_extra: "Minutos extras comprados", pl_num_extra: "Números extras", pl_fim_teste: "Fim do teste",
  pl_excedente: "Permitir excedente (cobrar minuto extra)", pl_aplicar_modulos: "Aplicar os módulos do plano",
  pl_teste_ate: "teste até {data}", pl_pag_falhou: "Pagamento recusado",
  pl_st_ok: "OK", pl_st_near: "Perto do limite", pl_st_over: "Acima do limite",
  pl_rodar_rotina: "Verificar testes vencidos agora", pl_rotina_ok: "{avisos} aviso(s) e {suspensas} suspensão(ões).",
  pl_calc_titulo: "Calculadora de preços", pl_calc_desc: "Premissas de custo e o resultado por plano no uso total dos minutos e SMS. A tabela recalcula enquanto você digita; salve para guardar.",
  pr_custo_min_voz: "Voz IA (US$ por minuto)", pr_custo_min_tel: "Telefonia (US$ por minuto)", pr_custo_numero: "Número local (US$ por mês)",
  pr_custo_sms: "SMS (US$ por segmento)", pr_custo_a2p: "Campanha A2P (US$ por mês)", pr_horas_manutencao: "Manutenção (horas por mês)",
  pr_valor_hora: "Valor da hora (US$)", pr_empresas_pagantes: "Empresas pagantes (rateio)", pr_margem_alvo: "Margem alvo (%)",
  pl_salvar_premissas: "Salvar premissas", pl_salvo: "Salvo.",
  pl_preco: "Preço mensal", pl_custo_var: "Custo variável", pl_custo_fixo: "Custo fixo (rateio)", pl_custo_total: "Custo total",
  pl_margem_pct: "Margem %", pl_equilibrio: "Empresas para empatar", pl_sugerido: "Preço sugerido",
  pl_addons_margem: "Complementos: minuto extra {minuto} (custo {mcusto}, margem {mpct}); número extra {numero} (margem {npct}); SMS extra {sms} (margem {spct}).",
  pl_calc_nota: "Empresas para empatar: quantas empresas neste plano cobrem sozinhas o custo fixo de {fixo} por mês. Preço sugerido: custo total dividido por (1 menos a margem alvo); abaixo, arredondado para cima.",
  pl_cat_titulo: "Catálogo de planos", pl_cat_desc: "Planos mostrados na página de assinatura. Textos nos três idiomas; recursos com um item por linha.",
  pl_codigo: "Código", pl_nome: "Nome", pl_descricao: "Descrição", pl_recursos: "Recursos", pl_preco_mensal: "Preço mensal (US$)",
  pl_preco_anual: "Preço anual (US$)", pl_anual_padrao: "10 x mensal", pl_minutos_voz: "Minutos de voz por mês", pl_sms: "SMS por mês",
  pl_gestores_max: "Máximo de gestores", pl_vagas_max: "Máximo de vagas ativas", pl_ilimitado: "Ilimitado", pl_ordem: "Ordem",
  pl_modulos: "Módulos (separados por vírgula)", pl_numero_exclusivo: "Número exclusivo", pl_destaque: "Destaque", pl_ativo: "Ativo",
  pl_novo_plano: "Novo plano", pl_remover_plano: "Remover plano", pl_add_plano: "Adicionar plano",
  pl_addons: "Complementos e teste grátis", pl_minuto_extra: "Minuto extra (US$)", pl_numero_extra: "Número extra (US$ por mês)",
  pl_sms_extra: "SMS extra (US$)", pl_trial_dias: "Dias de teste", pl_trial_minutos: "Minutos no teste",
  pl_excedente_dica: "O excedente é liberado por empresa (botão Ajustar no uso por empresa). Sem excedente, as ligações param no limite.",
  pl_salvar_catalogo: "Salvar catálogo", pl_restaurar: "Restaurar padrão",
  pl_confirmar_remover: "Remover este plano do catálogo?", pl_confirmar_restaurar: "Restaurar o catálogo padrão? As edições serão perdidas.",
  st_titulo: "Cobrança (Stripe)", st_desc: "Chaves do Stripe para assinatura com cartão. Sem chave, a assinatura pelo site cria só o teste grátis.",
  st_modo_teste: "Modo de teste (final {final})", st_modo_real: "Modo real (final {final})",
  st_chave: "Chave secreta (sk_...)", st_segredo: "Segredo do webhook (whsec_...)", st_dono_email: "Seu e-mail para avisos",
  st_dono_email_dica: "recebe novas assinaturas e pagamentos recusados",
  st_webhook: "Endereço do webhook para cadastrar no Stripe:",
  st_eventos: "Eventos: checkout.session.completed, invoice.paid, invoice.payment_failed e customer.subscription.deleted.",
  st_precos: "Preços do Stripe por plano", st_precos_dica: "Opcional. Em branco, o preço é criado na hora com o valor do catálogo.",
  st_salvar: "Salvar Stripe", st_salvo: "Stripe salvo.",
});

Object.assign(I18N_DONO.en, {
  aba_planos: "Plans and pricing",
  pl_assin_titulo: "Public signup and free trial", pl_assin_desc: "When open, anyone can create a company from the signup page and get the free trial (with call minutes). Keep it closed until prices, terms and privacy are reviewed.", pl_assin_rotulo: "Open public signup", pl_assin_previa: "See the preview of the new home page", pl_assin_confirma: "Open public signup? New companies will be able to sign up and use the trial minutes.",
  pl_resumo: "Monthly summary", pl_mes: "Month", pl_mrr: "Monthly recurring revenue (MRR)", pl_custo_var_mes: "Actual variable cost",
  pl_custo_fixo_mes: "Fixed cost (maintenance)", pl_resultado: "Net result", pl_pagantes: "Paying companies",
  pl_uso_titulo: "Usage by company", pl_uso_desc: "Voice minutes this month (New York time), estimated actual cost, revenue and margin for each company.",
  pl_empresa: "Company", pl_plano: "Plan", pl_minutos: "Minutes (used / limit)", pl_custo_real: "Actual cost", pl_receita: "Revenue",
  pl_margem: "Margin", pl_ajustar: "Adjust", pl_sem_plano: "No plan (no limit)", pl_mensal: "Monthly", pl_anual: "Yearly",
  pl_ciclo: "Billing cycle", pl_min_extra: "Extra minutes purchased", pl_num_extra: "Extra numbers", pl_fim_teste: "Trial end",
  pl_excedente: "Allow overage (bill extra minutes)", pl_aplicar_modulos: "Apply the plan's modules",
  pl_teste_ate: "trial until {data}", pl_pag_falhou: "Payment declined",
  pl_st_ok: "OK", pl_st_near: "Near the limit", pl_st_over: "Over the limit",
  pl_rodar_rotina: "Check expired trials now", pl_rotina_ok: "{avisos} reminder(s) and {suspensas} suspension(s).",
  pl_calc_titulo: "Pricing calculator", pl_calc_desc: "Cost assumptions and the result per plan at full use of minutes and SMS. The table updates as you type; save to keep it.",
  pr_custo_min_voz: "Voice AI (US$ per minute)", pr_custo_min_tel: "Telephony (US$ per minute)", pr_custo_numero: "Local number (US$ per month)",
  pr_custo_sms: "SMS (US$ per segment)", pr_custo_a2p: "A2P campaign (US$ per month)", pr_horas_manutencao: "Maintenance (hours per month)",
  pr_valor_hora: "Hourly rate (US$)", pr_empresas_pagantes: "Paying companies (cost split)", pr_margem_alvo: "Target margin (%)",
  pl_salvar_premissas: "Save assumptions", pl_salvo: "Saved.",
  pl_preco: "Monthly price", pl_custo_var: "Variable cost", pl_custo_fixo: "Fixed cost (share)", pl_custo_total: "Total cost",
  pl_margem_pct: "Margin %", pl_equilibrio: "Companies to break even", pl_sugerido: "Suggested price",
  pl_addons_margem: "Add-ons: extra minute {minuto} (cost {mcusto}, margin {mpct}); extra number {numero} (margin {npct}); extra SMS {sms} (margin {spct}).",
  pl_calc_nota: "Companies to break even: how many companies on this plan cover the {fixo} monthly fixed cost on their own. Suggested price: total cost divided by (1 minus the target margin); below it, rounded up.",
  pl_cat_titulo: "Plan catalog", pl_cat_desc: "Plans shown on the signup page. Texts in all three languages; features with one item per line.",
  pl_codigo: "Code", pl_nome: "Name", pl_descricao: "Description", pl_recursos: "Features", pl_preco_mensal: "Monthly price (US$)",
  pl_preco_anual: "Yearly price (US$)", pl_anual_padrao: "10 x monthly", pl_minutos_voz: "Voice minutes per month", pl_sms: "SMS per month",
  pl_gestores_max: "Max managers", pl_vagas_max: "Max active jobs", pl_ilimitado: "Unlimited", pl_ordem: "Order",
  pl_modulos: "Modules (comma separated)", pl_numero_exclusivo: "Dedicated number", pl_destaque: "Highlight", pl_ativo: "Active",
  pl_novo_plano: "New plan", pl_remover_plano: "Remove plan", pl_add_plano: "Add plan",
  pl_addons: "Add-ons and free trial", pl_minuto_extra: "Extra minute (US$)", pl_numero_extra: "Extra number (US$ per month)",
  pl_sms_extra: "Extra SMS (US$)", pl_trial_dias: "Trial days", pl_trial_minutos: "Trial minutes",
  pl_excedente_dica: "Overage is turned on per company (Adjust button under usage by company). Without overage, calls stop at the limit.",
  pl_salvar_catalogo: "Save catalog", pl_restaurar: "Restore defaults",
  pl_confirmar_remover: "Remove this plan from the catalog?", pl_confirmar_restaurar: "Restore the default catalog? Your edits will be lost.",
  st_titulo: "Billing (Stripe)", st_desc: "Stripe keys for card subscriptions. Without a key, signing up on the site only creates the free trial.",
  st_modo_teste: "Test mode (ending {final})", st_modo_real: "Live mode (ending {final})",
  st_chave: "Secret key (sk_...)", st_segredo: "Webhook signing secret (whsec_...)", st_dono_email: "Your email for alerts",
  st_dono_email_dica: "gets new signups and declined payments",
  st_webhook: "Webhook URL to add in Stripe:",
  st_eventos: "Events: checkout.session.completed, invoice.paid, invoice.payment_failed and customer.subscription.deleted.",
  st_precos: "Stripe prices per plan", st_precos_dica: "Optional. If blank, the price is created on the fly from the catalog amount.",
  st_salvar: "Save Stripe", st_salvo: "Stripe saved.",
});

Object.assign(I18N_DONO.es, {
  aba_planos: "Planes y precios",
  pl_assin_titulo: "Registro público y prueba gratis", pl_assin_desc: "Cuando está abierto, cualquier persona crea una empresa desde la página de suscripción y recibe la prueba gratis (con minutos de llamada). Déjalo cerrado hasta revisar precios, términos y privacidad.", pl_assin_rotulo: "Abrir el registro público", pl_assin_previa: "Ver la vista previa de la nueva página de inicio", pl_assin_confirma: "¿Abrir el registro público? Nuevas empresas podrán registrarse y usar los minutos de prueba.",
  pl_resumo: "Resumen del mes", pl_mes: "Mes", pl_mrr: "Ingreso recurrente (MRR)", pl_custo_var_mes: "Costo variable real",
  pl_custo_fixo_mes: "Costo fijo (mantenimiento)", pl_resultado: "Resultado", pl_pagantes: "Empresas que pagan",
  pl_uso_titulo: "Uso por empresa", pl_uso_desc: "Minutos de voz del mes (hora de Nueva York), costo real estimado, ingreso y margen de cada empresa.",
  pl_empresa: "Empresa", pl_plano: "Plan", pl_minutos: "Minutos (uso / límite)", pl_custo_real: "Costo real", pl_receita: "Ingreso",
  pl_margem: "Margen", pl_ajustar: "Ajustar", pl_sem_plano: "Sin plan (sin límite)", pl_mensal: "Mensual", pl_anual: "Anual",
  pl_ciclo: "Ciclo", pl_min_extra: "Minutos extra comprados", pl_num_extra: "Números extra", pl_fim_teste: "Fin de la prueba",
  pl_excedente: "Permitir excedente (cobrar minuto extra)", pl_aplicar_modulos: "Aplicar los módulos del plan",
  pl_teste_ate: "prueba hasta el {data}", pl_pag_falhou: "Pago rechazado",
  pl_st_ok: "OK", pl_st_near: "Cerca del límite", pl_st_over: "Por encima del límite",
  pl_rodar_rotina: "Revisar pruebas vencidas ahora", pl_rotina_ok: "{avisos} aviso(s) y {suspensas} suspensión(es).",
  pl_calc_titulo: "Calculadora de precios", pl_calc_desc: "Supuestos de costo y el resultado por plan con el uso total de minutos y SMS. La tabla se recalcula mientras escribes; guarda para conservarla.",
  pr_custo_min_voz: "Voz IA (US$ por minuto)", pr_custo_min_tel: "Telefonía (US$ por minuto)", pr_custo_numero: "Número local (US$ al mes)",
  pr_custo_sms: "SMS (US$ por segmento)", pr_custo_a2p: "Campaña A2P (US$ al mes)", pr_horas_manutencao: "Mantenimiento (horas al mes)",
  pr_valor_hora: "Valor de la hora (US$)", pr_empresas_pagantes: "Empresas que pagan (prorrateo)", pr_margem_alvo: "Margen objetivo (%)",
  pl_salvar_premissas: "Guardar supuestos", pl_salvo: "Guardado.",
  pl_preco: "Precio mensual", pl_custo_var: "Costo variable", pl_custo_fixo: "Costo fijo (prorrateo)", pl_custo_total: "Costo total",
  pl_margem_pct: "Margen %", pl_equilibrio: "Empresas para el punto de equilibrio", pl_sugerido: "Precio sugerido",
  pl_addons_margem: "Complementos: minuto extra {minuto} (costo {mcusto}, margen {mpct}); número extra {numero} (margen {npct}); SMS extra {sms} (margen {spct}).",
  pl_calc_nota: "Punto de equilibrio: cuántas empresas en este plan cubren por sí solas el costo fijo de {fixo} al mes. Precio sugerido: costo total dividido entre (1 menos el margen objetivo); abajo, redondeado hacia arriba.",
  pl_cat_titulo: "Catálogo de planes", pl_cat_desc: "Planes que aparecen en la página de suscripción. Textos en los tres idiomas; recursos con un elemento por línea.",
  pl_codigo: "Código", pl_nome: "Nombre", pl_descricao: "Descripción", pl_recursos: "Recursos", pl_preco_mensal: "Precio mensual (US$)",
  pl_preco_anual: "Precio anual (US$)", pl_anual_padrao: "10 x mensual", pl_minutos_voz: "Minutos de voz al mes", pl_sms: "SMS al mes",
  pl_gestores_max: "Máximo de gerentes", pl_vagas_max: "Máximo de vacantes activas", pl_ilimitado: "Ilimitado", pl_ordem: "Orden",
  pl_modulos: "Módulos (separados por coma)", pl_numero_exclusivo: "Número exclusivo", pl_destaque: "Destacado", pl_ativo: "Activo",
  pl_novo_plano: "Nuevo plan", pl_remover_plano: "Quitar plan", pl_add_plano: "Agregar plan",
  pl_addons: "Complementos y prueba gratis", pl_minuto_extra: "Minuto extra (US$)", pl_numero_extra: "Número extra (US$ al mes)",
  pl_sms_extra: "SMS extra (US$)", pl_trial_dias: "Días de prueba", pl_trial_minutos: "Minutos en la prueba",
  pl_excedente_dica: "El excedente se habilita por empresa (botón Ajustar en el uso por empresa). Sin excedente, las llamadas se detienen en el límite.",
  pl_salvar_catalogo: "Guardar catálogo", pl_restaurar: "Restaurar valores predeterminados",
  pl_confirmar_remover: "¿Quitar este plan del catálogo?", pl_confirmar_restaurar: "¿Restaurar el catálogo predeterminado? Se perderán tus cambios.",
  st_titulo: "Cobro (Stripe)", st_desc: "Claves de Stripe para suscripciones con tarjeta. Sin clave, la suscripción en el sitio solo crea la prueba gratis.",
  st_modo_teste: "Modo de prueba (termina en {final})", st_modo_real: "Modo real (termina en {final})",
  st_chave: "Clave secreta (sk_...)", st_segredo: "Secreto del webhook (whsec_...)", st_dono_email: "Tu correo para avisos",
  st_dono_email_dica: "recibe nuevas suscripciones y pagos rechazados",
  st_webhook: "URL del webhook para registrar en Stripe:",
  st_eventos: "Eventos: checkout.session.completed, invoice.paid, invoice.payment_failed y customer.subscription.deleted.",
  st_precos: "Precios de Stripe por plan", st_precos_dica: "Opcional. Si está vacío, el precio se crea en el momento con el valor del catálogo.",
  st_salvar: "Guardar Stripe", st_salvo: "Stripe guardado.",
});
// ================================================================ fim planos e preços
