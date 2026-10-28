/* =====================================================================
   Idiomas da área do candidato e da página de vagas: português (pt),
   inglês (en) e espanhol (es).

   Ordem de escolha do idioma:
     1. parâmetro da URL ?lang=pt|en|es
     2. idioma salvo no cadastro do candidato (GET /api/candidato/me)
     3. localStorage "cand_idioma"
     4. idioma do navegador (pt*, es*, senão en)

   Uso: t(chave, { variavel: valor }) devolve o texto no idioma atual.
   Os textos dos testes (data.js) são trocados por aplicarIdiomaDados().
   Conteúdo escrito pela empresa (vagas, cargos, competências, questões)
   vem da API e não é traduzido.
   ===================================================================== */

const IDIOMAS_CAND = ["pt", "en", "es"];
const LANG_HTML = { pt: "pt-BR", en: "en", es: "es" };

const I18N_CAND = {
  // ================================================================ PT
  pt: {
    // topo e geral
    titulo_pagina: "Bússola · Área do Candidato",
    topo_sub: "Área do candidato",
    inicio: "Início",
    sair: "Sair",
    carregando: "Carregando…",
    idioma: "Idioma",
    ola: "Olá, {nome}",
    confirmar_sair: "Sair da sua sessão? Você poderá voltar fazendo um novo cadastro.",
    opcional: "(opcional)",
    voltar: "← Voltar",
    continuar: "Continuar",
    concluido: "Concluído",
    iniciar: "Iniciar",
    refazer: "Refazer",
    revisar: "Revisar",
    enviar: "Enviar",
    substituir: "Substituir",
    finalizar_teste: "Finalizar teste",
    obrigatoria: "obrigatória",
    erro_comunicacao: "Erro de comunicação com o servidor",
    erro_carregar: "Erro ao carregar: {msg}. Verifique sua conexão e tente novamente.",

    // cadastro
    aviso_carregando_vaga: "Carregando dados da vaga…",
    cad_titulo: "Cadastro",
    cad_desc: "Preencha seus dados para iniciar a avaliação. Você terá acesso apenas aos seus próprios resultados.",
    cad_tipo_rotulo: "Você está...",
    cad_tipo_externo: "Me candidatando a uma oportunidade",
    cad_tipo_interno: "Já trabalho na instituição (desenvolvimento e upgrade de cargo)",
    cad_nome: "Nome completo",
    cad_nome_ph: "Seu nome",
    cad_email: "E-mail",
    cad_email_ph: "voce@email.com",
    cad_telefone: "Telefone (com código do país)",
    cad_telefone_ph: "923 000 000",
    cad_local: "Onde você está fazendo a avaliação?",
    cad_local_ph: "Instituição, unidade ou setor (ex.: Secretaria de GTI)",
    cad_atual: "Cargo atual",
    cad_atual_ph: "Ex.: Analista de Sistemas Júnior",
    cad_funcao: "Função que exerce",
    cad_funcao_ph: "Ex.: Suporte de rede do 2.º nível",
    cad_linkedin_ph: "linkedin.com/in/seu-perfil",
    cad_instagram_ph: "@seu.usuario",
    cad_cargo_interesse: "Cargo de interesse",
    cad_cargo_interno: "Seu cargo (base da matriz de gaps e do plano de desenvolvimento)",
    cad_selecione_cargo: "Selecione o cargo",
    cad_cargo_novo_opcao: "+ Adicionar um cargo que não está na lista",
    cad_novo_cargo: "Nome do novo cargo",
    cad_novo_cargo_ph: "Ex.: Especialista em Cibersegurança",
    cad_area: "Área",
    cad_area_ph: "Ex.: Infraestrutura",
    cad_novo_cargo_desc: "O cargo adicionado passa a fazer parte do sistema e fica disponível para o gestor.",
    cad_consentimento: "Autorizo o uso dos meus dados pessoais e respostas para este processo seletivo e para o banco de talentos, conforme a LGPD. Posso solicitar a exclusão dos meus dados a qualquer momento.",
    cad_enviar: "Iniciar avaliação",
    rec_titulo: "Já tem cadastro?",
    rec_desc: "Seu acesso é pelo link pessoal enviado ao seu e-mail. Se o perdeu, receba de novo:",
    rec_email_ph: "seu e-mail cadastrado",
    rec_enviar: "Reenviar meu link",
    rec_ok: "Se este e-mail estiver cadastrado, o link de acesso chegará em instantes.",
    vaga_fechada_cadastro: "Esta vaga não está mais aberta. Você pode se cadastrar escolhendo um cargo de interesse.",
    vaga_aviso: "Você está se candidatando à vaga:",

    // validação e erros do cadastro
    val_nome_email: "Nome e e-mail são obrigatórios.",
    val_local: "Informe onde você está fazendo a avaliação.",
    val_telefone: "Informe um telefone válido com o código do país.",
    val_consentimento: "É necessário autorizar o uso dos seus dados para o processo seletivo.",
    erro_vaga_fechada: "Esta vaga não está mais aberta.",
    erro_link_empresa: "Use o link de inscrição enviado pela empresa.",
    erro_email_enviado: "Este e-mail já possui cadastro. Enviamos o seu link de acesso para o e-mail informado.",
    erro_email_existente: "Este e-mail já possui cadastro. Use o seu link pessoal de acesso para continuar.",

    // painel
    painel_titulo: "Sua jornada de avaliação",
    painel_cargo: "Cargo de interesse: <strong>{cargo}</strong>",
    painel_sem_cargo: "Você ainda não selecionou um cargo de interesse, por isso a matriz de gaps ficará indisponível.",
    painel_vaga: "Vaga",
    painel_status: "Status da candidatura",
    passo_disc_t: "Teste DISC",
    passo_disc_sub: "24 blocos · escolha a palavra que MAIS e a que MENOS se parece com você",
    passo_base_t: "Teste B.A.S.E.",
    passo_base_sub: "8 rodadas · ordene as cartas da que mais combina com você para a que menos combina",
    passo_auto_t: "Autoavaliação de competências",
    passo_auto_sub: "Avalie seu nível em cada competência exigida por: {cargo}",
    passo_quiz_t: "Teste de conhecimento",
    passo_quiz_sub: "{n} questões de múltipla escolha sobre o cargo",
    passo_cv_t: "Currículo (opcional)",
    passo_cv_enviado: "Currículo enviado",
    passo_cv_sub: "Envie seu currículo em PDF para enriquecer a análise",
    res_titulo: "Resultados",
    res_pronto: "Tudo pronto! Veja seu relatório completo.",
    res_pendente: "Conclua os testes acima para liberar seu relatório completo.",
    res_ver: "Ver meus resultados",
    link_pessoal: "Seu link pessoal de acesso (para continuar de outro aparelho):",
    copiar_link: "Copiar link",
    copiado: "Copiado",
    etapa_inscrito: "Inscrito",
    etapa_avaliacoes: "Avaliações",
    etapa_entrevista: "Entrevista",
    etapa_proposta: "Proposta",
    etapa_contratado: "Contratado",
    etapa_reprovado: "Reprovado",

    // DISC
    disc_titulo: "Teste DISC · bloco {n} de {total}",
    disc_instrucao: 'Marque a palavra que <strong style="color:var(--success)">MAIS</strong> se parece com você e a que <strong style="color:var(--danger)">MENOS</strong> se parece.',
    mais: "MAIS",
    menos: "MENOS",
    anterior: "← Anterior",
    proximo: "Próximo →",
    disc_concluido: "Teste DISC concluído",

    // B.A.S.E.
    base_titulo: "Teste B.A.S.E. · rodada {n} de {total}",
    base_instrucao: "Clique nas 4 cartas em ordem: da que <strong>MAIS</strong> combina com você (1º) até a que <strong>MENOS</strong> combina (4º).",
    ord_1: "1º", ord_2: "2º", ord_3: "3º", ord_4: "4º",
    limpar: "Limpar escolhas",
    proxima_rodada: "Próxima rodada →",
    base_concluido: "Teste B.A.S.E. concluído",

    // autoavaliação
    auto_titulo: "Autoavaliação de competências",
    auto_desc: "Cargo: <strong>{cargo}</strong>. Para cada competência, indique com sinceridade o seu nível atual.",
    nivel_exigido: "nível exigido: {n}",
    auto_salvar: "Salvar autoavaliação",
    auto_faltam: "Responda todas as competências (faltam {n}).",

    // teste de conhecimento
    quiz_titulo: "Teste de conhecimento",
    quiz_desc: "Responda as {n} questões. Cada questão tem apenas uma alternativa correta.",
    quiz_enviar: "Enviar respostas",
    quiz_faltam: "Responda todas as questões (faltam {n}).",
    quiz_concluido: "Teste de conhecimento concluído",
    quiz_acertos: "Você acertou {a} de {total} questões.",
    quiz_pct: "{pct}% de acerto",
    quiz_corretas: "{a} de {total} questões corretas",

    // currículo
    cv_titulo: "Enviar currículo",
    cv_desc: "Envie seu currículo em PDF (até 8 MB). O gestor poderá cruzar as informações do currículo com as suas respostas.",
    cv_selecione: "Selecione um arquivo.",
    cv_grande: "Arquivo maior que 8 MB.",

    // resultados
    res_seus: "Seus resultados",
    res_pdf: "Baixar relatório em PDF",
    res_nenhum: "Nenhum teste concluído ainda.",
    gerando: "Gerando…",
    erro_pdf: "Não foi possível gerar o relatório",

    // render.js (blocos de resultado)
    r_pontos_fortes: "Pontos fortes",
    r_pontos_desenv: "Pontos de desenvolvimento",
    r_disc_titulo: "Perfil Comportamental DISC",
    r_perfil_dominante: "Perfil dominante: {nome} ({letra})",
    r_perfil_secundario: "Perfil secundário: {nome} ({letra})",
    r_estilo_trabalho: "Estilo de trabalho",
    r_base_titulo: "Código de Personalidade B.A.S.E.",
    r_seu_codigo: "Seu código: {codigo}",
    r_arquetipo: "Arquétipo dominante: <strong>{nome}</strong>, {titulo}",
    r_com_perfil: "Com o perfil {nome}",
    r_interpretar: "Como interpretar o código completo",
    r_interpretar_desc: "Cada posição do código revela algo diferente sobre como a pessoa funciona.",
    r_gatilhos: "Gatilhos e pontos de atenção",
    r_impulsiona: "O que impulsiona",
    r_incomoda: "O que incomoda",
    r_comunicar: "Como se comunicar com os outros perfis",
    r_m_competencias: "Competências",
    r_m_disc: "Perfil DISC",
    r_m_base: "Código B.A.S.E.",
    r_m_conhecimento: "Conhecimento",
    r_m_entrevista: "Entrevista",
    r_m_voz: "Triagem por voz",
    r_md_competencias: "aderência às competências exigidas",
    r_md_disc: "alinhamento com o perfil desejado: {nome}",
    r_md_base: "alinhamento com o arquétipo desejado: {nome}",
    r_md_conhecimento: "acertos no teste de conhecimento do cargo",
    r_md_entrevista: "média do scorecard da entrevista estruturada",
    r_md_voz: "pontuação da ligação de triagem com a Francisca",
    r_mf_competencias: "autoavaliação de competências",
    r_mf_disc: "teste DISC",
    r_mf_base: "teste B.A.S.E.",
    r_mf_conhecimento: "teste de conhecimento",
    r_mf_entrevista: "entrevista",
    r_match_titulo: "Match com o cargo",
    r_match_desc: "Índice único que cruza todas as dimensões da avaliação: competências (peso 30%), perfil DISC (15%), código B.A.S.E. (15%), teste de conhecimento (20%) e entrevista (20%). Os pesos se redistribuem sobre o que já foi respondido.",
    r_match_desc_voz: " A triagem por voz entra com o peso definido no cargo e os demais componentes dividem o restante.",
    r_match_geral: "match geral",
    r_pendente: "Ainda não considerado (pendente): {lista}.",
    r_apto: "Apto para a função",
    r_desenv: "Em desenvolvimento",
    r_gap_alto: "Gap alto",
    r_obrig_title: "Competência obrigatória",
    r_sem_resposta: "sem resposta",
    r_plano: "Plano de desenvolvimento sugerido",
    r_gap: "gap {n}",
    r_nenhum_gap: "Nenhum gap identificado: todas as competências exigidas foram atendidas.",
    r_aviso_sem_auto: "A autoavaliação de competências ainda não foi respondida, por isso os níveis atuais aparecem zerados.",
    r_matriz_titulo: "Matriz de Gaps: {cargo}",
    r_aderencia: "Aderência ao cargo: {pct}%",
    r_obrig_pend: "{n} competência(s) obrigatória(s) com gap",
    r_th_comp: "Competência",
    r_th_tipo: "Tipo",
    r_th_exigido: "Exigido",
    r_th_atual: "Atual",
    r_th_gap: "Gap",

    // página de vagas
    v_titulo_pagina: "Bússola · Vagas Abertas",
    v_sub: "Vagas abertas",
    v_hero_h: "Vagas abertas",
    v_hero_h_local: "Vagas abertas · {local}",
    v_hero_p: "Candidate-se a uma vaga e faça a avaliação completa: testes comportamentais, competências e teste de conhecimento.",
    v_pais: "País:",
    v_todos_paises: "Todos os países",
    v_carregando: "Carregando vagas…",
    v_nenhuma_pais: "Nenhuma vaga aberta neste país no momento.",
    v_nenhuma: "Nenhuma vaga aberta no momento. Volte em breve.",
    v_candidatar: "Candidatar-se",
    v_use_link: "Use o link de vagas enviado pela empresa.",
    v_de: "Vagas de {nome}",
    v_erro: "Erro ao carregar as vagas.",
  },

  // ================================================================ EN
  en: {
    titulo_pagina: "Bússola · Candidate Area",
    topo_sub: "Candidate area",
    inicio: "Home",
    sair: "Sign out",
    carregando: "Loading…",
    idioma: "Language",
    ola: "Hi, {nome}",
    confirmar_sair: "Sign out of your session? You can come back later using your personal link.",
    opcional: "(optional)",
    voltar: "← Back",
    continuar: "Continue",
    concluido: "Completed",
    iniciar: "Start",
    refazer: "Retake",
    revisar: "Review",
    enviar: "Upload",
    substituir: "Replace",
    finalizar_teste: "Finish test",
    obrigatoria: "required",
    erro_comunicacao: "Could not connect to the server",
    erro_carregar: "Error while loading: {msg}. Please check your connection and try again.",

    aviso_carregando_vaga: "Loading job details…",
    cad_titulo: "Sign up",
    cad_desc: "Fill in your details to start the assessment. You will only have access to your own results.",
    cad_tipo_rotulo: "You are...",
    cad_tipo_externo: "Applying for an opportunity",
    cad_tipo_interno: "Already working at the organization (growth and promotion)",
    cad_nome: "Full name",
    cad_nome_ph: "Your name",
    cad_email: "Email",
    cad_email_ph: "you@email.com",
    cad_telefone: "Phone (with country code)",
    cad_telefone_ph: "555 123 4567",
    cad_local: "Where are you taking the assessment?",
    cad_local_ph: "Organization, branch or department (e.g. Downtown office)",
    cad_atual: "Current job title",
    cad_atual_ph: "e.g. Junior Systems Analyst",
    cad_funcao: "What you do",
    cad_funcao_ph: "e.g. Residential cleaning",
    cad_linkedin_ph: "linkedin.com/in/your-profile",
    cad_instagram_ph: "@your.username",
    cad_cargo_interesse: "Position you are interested in",
    cad_cargo_interno: "Your position (used for the gap matrix and development plan)",
    cad_selecione_cargo: "Select a position",
    cad_cargo_novo_opcao: "+ Add a position that is not on the list",
    cad_novo_cargo: "New position name",
    cad_novo_cargo_ph: "e.g. Cybersecurity Specialist",
    cad_area: "Area",
    cad_area_ph: "e.g. Operations",
    cad_novo_cargo_desc: "The position you add becomes part of the system and is available to the hiring manager.",
    cad_consentimento: "I authorize the use of my personal data and answers for this hiring process and for the talent pool, in accordance with data protection laws (LGPD). I can ask for my data to be deleted at any time.",
    cad_enviar: "Start assessment",
    rec_titulo: "Already signed up?",
    rec_desc: "You access your assessment through the personal link sent to your email. If you lost it, get it again:",
    rec_email_ph: "the email you signed up with",
    rec_enviar: "Resend my link",
    rec_ok: "If this email is registered, your access link will arrive shortly.",
    vaga_fechada_cadastro: "This job is no longer open. You can still sign up by choosing a position you are interested in.",
    vaga_aviso: "You are applying for:",

    val_nome_email: "Name and email are required.",
    val_local: "Please tell us where you are taking the assessment.",
    val_telefone: "Please enter a valid phone number with the country code.",
    val_consentimento: "You need to authorize the use of your data for the hiring process.",
    erro_vaga_fechada: "This job is no longer open.",
    erro_link_empresa: "Please use the application link sent by the company.",
    erro_email_enviado: "This email is already registered. We sent your access link to that email address.",
    erro_email_existente: "This email is already registered. Please use your personal access link to continue.",

    painel_titulo: "Your assessment journey",
    painel_cargo: "Position: <strong>{cargo}</strong>",
    painel_sem_cargo: "You have not selected a position yet, so the gap matrix will not be available.",
    painel_vaga: "Job",
    painel_status: "Application status",
    passo_disc_t: "DISC test",
    passo_disc_sub: "24 sets · choose the word that is MOST like you and the one that is LEAST like you",
    passo_base_t: "B.A.S.E. test",
    passo_base_sub: "8 rounds · put the cards in order, from the one most like you to the one least like you",
    passo_auto_t: "Skills self-assessment",
    passo_auto_sub: "Rate your level in each skill required for: {cargo}",
    passo_quiz_t: "Knowledge test",
    passo_quiz_sub: "{n} multiple choice questions about the position",
    passo_cv_t: "Resume (optional)",
    passo_cv_enviado: "Resume uploaded",
    passo_cv_sub: "Upload your resume as a PDF to enrich the analysis",
    res_titulo: "Results",
    res_pronto: "All set! See your full report.",
    res_pendente: "Complete the tests above to unlock your full report.",
    res_ver: "See my results",
    link_pessoal: "Your personal access link (to continue on another device):",
    copiar_link: "Copy link",
    copiado: "Copied",
    etapa_inscrito: "Applied",
    etapa_avaliacoes: "Assessments",
    etapa_entrevista: "Interview",
    etapa_proposta: "Offer",
    etapa_contratado: "Hired",
    etapa_reprovado: "Not selected",

    disc_titulo: "DISC test · set {n} of {total}",
    disc_instrucao: 'Mark the word that is <strong style="color:var(--success)">MOST</strong> like you and the one that is <strong style="color:var(--danger)">LEAST</strong> like you.',
    mais: "MOST",
    menos: "LEAST",
    anterior: "← Previous",
    proximo: "Next →",
    disc_concluido: "DISC test completed",

    base_titulo: "B.A.S.E. test · round {n} of {total}",
    base_instrucao: "Click the 4 cards in order: from the one <strong>MOST</strong> like you (1st) to the one <strong>LEAST</strong> like you (4th).",
    ord_1: "1st", ord_2: "2nd", ord_3: "3rd", ord_4: "4th",
    limpar: "Clear choices",
    proxima_rodada: "Next round →",
    base_concluido: "B.A.S.E. test completed",

    auto_titulo: "Skills self-assessment",
    auto_desc: "Position: <strong>{cargo}</strong>. For each skill, honestly choose your current level.",
    nivel_exigido: "required level: {n}",
    auto_salvar: "Save self-assessment",
    auto_faltam: "Please answer every skill ({n} left).",

    quiz_titulo: "Knowledge test",
    quiz_desc: "Answer the {n} questions. Each question has only one correct answer.",
    quiz_enviar: "Submit answers",
    quiz_faltam: "Please answer every question ({n} left).",
    quiz_concluido: "Knowledge test completed",
    quiz_acertos: "You got {a} out of {total} questions right.",
    quiz_pct: "{pct}% correct",
    quiz_corretas: "{a} out of {total} questions correct",

    cv_titulo: "Upload resume",
    cv_desc: "Upload your resume as a PDF (up to 8 MB). The hiring manager can compare your resume with your answers.",
    cv_selecione: "Please select a file.",
    cv_grande: "The file is larger than 8 MB.",

    res_seus: "Your results",
    res_pdf: "Download PDF report",
    res_nenhum: "No tests completed yet.",
    gerando: "Generating…",
    erro_pdf: "We could not generate the report",

    r_pontos_fortes: "Strengths",
    r_pontos_desenv: "Areas for growth",
    r_disc_titulo: "DISC Behavioral Profile",
    r_perfil_dominante: "Main profile: {nome} ({letra})",
    r_perfil_secundario: "Secondary profile: {nome} ({letra})",
    r_estilo_trabalho: "Work style",
    r_base_titulo: "B.A.S.E. Personality Code",
    r_seu_codigo: "Your code: {codigo}",
    r_arquetipo: "Main archetype: <strong>{nome}</strong>, {titulo}",
    r_com_perfil: "With the {nome} profile",
    r_interpretar: "How to read the full code",
    r_interpretar_desc: "Each position in the code reveals something different about how a person works.",
    r_gatilhos: "Triggers and points of attention",
    r_impulsiona: "What drives you",
    r_incomoda: "What bothers you",
    r_comunicar: "How to communicate with the other profiles",
    r_m_competencias: "Skills",
    r_m_disc: "DISC profile",
    r_m_base: "B.A.S.E. code",
    r_m_conhecimento: "Knowledge",
    r_m_entrevista: "Interview",
    r_m_voz: "Voice screening",
    r_md_competencias: "fit with the required skills",
    r_md_disc: "alignment with the desired profile: {nome}",
    r_md_base: "alignment with the desired archetype: {nome}",
    r_md_conhecimento: "correct answers on the knowledge test for the position",
    r_md_entrevista: "average score of the structured interview",
    r_md_voz: "score from the screening call with Francisca",
    r_mf_competencias: "skills self-assessment",
    r_mf_disc: "DISC test",
    r_mf_base: "B.A.S.E. test",
    r_mf_conhecimento: "knowledge test",
    r_mf_entrevista: "interview",
    r_match_titulo: "Match with the position",
    r_match_desc: "A single score that combines every part of the assessment: skills (30% weight), DISC profile (15%), B.A.S.E. code (15%), knowledge test (20%) and interview (20%). The weights are spread over what has already been answered.",
    r_match_desc_voz: " Voice screening counts with the weight set for the position, and the other parts share the rest.",
    r_match_geral: "overall match",
    r_pendente: "Not counted yet (pending): {lista}.",
    r_apto: "Ready for the role",
    r_desenv: "Developing",
    r_gap_alto: "Large gap",
    r_obrig_title: "Required skill",
    r_sem_resposta: "no answer",
    r_plano: "Suggested development plan",
    r_gap: "gap {n}",
    r_nenhum_gap: "No gaps found: every required skill is covered.",
    r_aviso_sem_auto: "The skills self-assessment has not been answered yet, so current levels show as zero.",
    r_matriz_titulo: "Gap Matrix: {cargo}",
    r_aderencia: "Fit with the position: {pct}%",
    r_obrig_pend: "{n} required skill(s) with a gap",
    r_th_comp: "Skill",
    r_th_tipo: "Type",
    r_th_exigido: "Required",
    r_th_atual: "Current",
    r_th_gap: "Gap",

    v_titulo_pagina: "Bússola · Open Positions",
    v_sub: "Open positions",
    v_hero_h: "Open positions",
    v_hero_h_local: "Open positions · {local}",
    v_hero_p: "Apply for a job and complete the full assessment: behavioral tests, skills and a knowledge test.",
    v_pais: "Country:",
    v_todos_paises: "All countries",
    v_carregando: "Loading jobs…",
    v_nenhuma_pais: "There are no open jobs in this country right now.",
    v_nenhuma: "There are no open jobs right now. Please check back soon.",
    v_candidatar: "Apply",
    v_use_link: "Please use the jobs link sent by the company.",
    v_de: "Jobs with {nome}",
    v_erro: "Error while loading the jobs.",
  },

  // ================================================================ ES
  es: {
    titulo_pagina: "Bússola · Área del Candidato",
    topo_sub: "Área del candidato",
    inicio: "Inicio",
    sair: "Salir",
    carregando: "Cargando…",
    idioma: "Idioma",
    ola: "Hola, {nome}",
    confirmar_sair: "¿Quieres salir de tu sesión? Puedes volver después con tu enlace personal.",
    opcional: "(opcional)",
    voltar: "← Volver",
    continuar: "Continuar",
    concluido: "Completado",
    iniciar: "Empezar",
    refazer: "Repetir",
    revisar: "Revisar",
    enviar: "Enviar",
    substituir: "Reemplazar",
    finalizar_teste: "Terminar prueba",
    obrigatoria: "obligatoria",
    erro_comunicacao: "Error de comunicación con el servidor",
    erro_carregar: "Error al cargar: {msg}. Revisa tu conexión e inténtalo de nuevo.",

    aviso_carregando_vaga: "Cargando datos de la vacante…",
    cad_titulo: "Registro",
    cad_desc: "Completa tus datos para empezar la evaluación. Solo tendrás acceso a tus propios resultados.",
    cad_tipo_rotulo: "Tú estás...",
    cad_tipo_externo: "Postulándome a una oportunidad",
    cad_tipo_interno: "Ya trabajo en la empresa (desarrollo y ascenso de puesto)",
    cad_nome: "Nombre completo",
    cad_nome_ph: "Tu nombre",
    cad_email: "Correo electrónico",
    cad_email_ph: "tu@correo.com",
    cad_telefone: "Teléfono (con código de país)",
    cad_telefone_ph: "555 123 4567",
    cad_local: "¿Dónde estás haciendo la evaluación?",
    cad_local_ph: "Empresa, sucursal o área (ej.: Oficina central)",
    cad_atual: "Puesto actual",
    cad_atual_ph: "Ej.: Auxiliar de limpieza",
    cad_funcao: "Lo que haces",
    cad_funcao_ph: "Ej.: Limpieza de casas",
    cad_linkedin_ph: "linkedin.com/in/tu-perfil",
    cad_instagram_ph: "@tu.usuario",
    cad_cargo_interesse: "Puesto que te interesa",
    cad_cargo_interno: "Tu puesto (base de la matriz de brechas y del plan de desarrollo)",
    cad_selecione_cargo: "Elige el puesto",
    cad_cargo_novo_opcao: "+ Agregar un puesto que no está en la lista",
    cad_novo_cargo: "Nombre del nuevo puesto",
    cad_novo_cargo_ph: "Ej.: Supervisora de limpieza",
    cad_area: "Área",
    cad_area_ph: "Ej.: Operaciones",
    cad_novo_cargo_desc: "El puesto que agregues pasa a formar parte del sistema y queda disponible para el gerente.",
    cad_consentimento: "Autorizo el uso de mis datos personales y respuestas para este proceso de selección y para la bolsa de talento, de acuerdo con las leyes de protección de datos (LGPD). Puedo pedir que borren mis datos en cualquier momento.",
    cad_enviar: "Empezar evaluación",
    rec_titulo: "¿Ya te registraste?",
    rec_desc: "Entras con el enlace personal que enviamos a tu correo. Si lo perdiste, pídelo de nuevo:",
    rec_email_ph: "tu correo registrado",
    rec_enviar: "Reenviar mi enlace",
    rec_ok: "Si este correo está registrado, el enlace de acceso llegará en unos momentos.",
    vaga_fechada_cadastro: "Esta vacante ya no está abierta. Puedes registrarte eligiendo un puesto que te interese.",
    vaga_aviso: "Te estás postulando a la vacante:",

    val_nome_email: "El nombre y el correo son obligatorios.",
    val_local: "Indica dónde estás haciendo la evaluación.",
    val_telefone: "Escribe un teléfono válido con el código de país.",
    val_consentimento: "Debes autorizar el uso de tus datos para el proceso de selección.",
    erro_vaga_fechada: "Esta vacante ya no está abierta.",
    erro_link_empresa: "Usa el enlace de registro que envió la empresa.",
    erro_email_enviado: "Este correo ya está registrado. Enviamos tu enlace de acceso a ese correo.",
    erro_email_existente: "Este correo ya está registrado. Usa tu enlace personal de acceso para continuar.",

    painel_titulo: "Tu camino de evaluación",
    painel_cargo: "Puesto de interés: <strong>{cargo}</strong>",
    painel_sem_cargo: "Todavía no elegiste un puesto de interés, por eso la matriz de brechas no estará disponible.",
    painel_vaga: "Vacante",
    painel_status: "Estado de la postulación",
    passo_disc_t: "Prueba DISC",
    passo_disc_sub: "24 grupos · elige la palabra que MÁS se parece a ti y la que MENOS se parece",
    passo_base_t: "Prueba B.A.S.E.",
    passo_base_sub: "8 rondas · ordena las tarjetas, de la que más va contigo a la que menos va contigo",
    passo_auto_t: "Autoevaluación de competencias",
    passo_auto_sub: "Evalúa tu nivel en cada competencia que pide el puesto: {cargo}",
    passo_quiz_t: "Prueba de conocimientos",
    passo_quiz_sub: "{n} preguntas de opción múltiple sobre el puesto",
    passo_cv_t: "Currículum (opcional)",
    passo_cv_enviado: "Currículum enviado",
    passo_cv_sub: "Envía tu currículum en PDF para enriquecer el análisis",
    res_titulo: "Resultados",
    res_pronto: "¡Todo listo! Mira tu informe completo.",
    res_pendente: "Termina las pruebas de arriba para ver tu informe completo.",
    res_ver: "Ver mis resultados",
    link_pessoal: "Tu enlace personal de acceso (para seguir desde otro dispositivo):",
    copiar_link: "Copiar enlace",
    copiado: "Copiado",
    etapa_inscrito: "Postulado",
    etapa_avaliacoes: "Evaluaciones",
    etapa_entrevista: "Entrevista",
    etapa_proposta: "Oferta",
    etapa_contratado: "Contratado",
    etapa_reprovado: "No seleccionado",

    disc_titulo: "Prueba DISC · grupo {n} de {total}",
    disc_instrucao: 'Marca la palabra que <strong style="color:var(--success)">MÁS</strong> se parece a ti y la que <strong style="color:var(--danger)">MENOS</strong> se parece.',
    mais: "MÁS",
    menos: "MENOS",
    anterior: "← Anterior",
    proximo: "Siguiente →",
    disc_concluido: "Prueba DISC completada",

    base_titulo: "Prueba B.A.S.E. · ronda {n} de {total}",
    base_instrucao: "Toca las 4 tarjetas en orden: desde la que <strong>MÁS</strong> va contigo (1.º) hasta la que <strong>MENOS</strong> va contigo (4.º).",
    ord_1: "1.º", ord_2: "2.º", ord_3: "3.º", ord_4: "4.º",
    limpar: "Borrar selección",
    proxima_rodada: "Siguiente ronda →",
    base_concluido: "Prueba B.A.S.E. completada",

    auto_titulo: "Autoevaluación de competencias",
    auto_desc: "Puesto: <strong>{cargo}</strong>. En cada competencia, indica con sinceridad tu nivel actual.",
    nivel_exigido: "nivel requerido: {n}",
    auto_salvar: "Guardar autoevaluación",
    auto_faltam: "Responde todas las competencias (faltan {n}).",

    quiz_titulo: "Prueba de conocimientos",
    quiz_desc: "Responde las {n} preguntas. Cada pregunta tiene una sola respuesta correcta.",
    quiz_enviar: "Enviar respuestas",
    quiz_faltam: "Responde todas las preguntas (faltan {n}).",
    quiz_concluido: "Prueba de conocimientos completada",
    quiz_acertos: "Acertaste {a} de {total} preguntas.",
    quiz_pct: "{pct}% de aciertos",
    quiz_corretas: "{a} de {total} preguntas correctas",

    cv_titulo: "Enviar currículum",
    cv_desc: "Envía tu currículum en PDF (hasta 8 MB). El gerente podrá comparar tu currículum con tus respuestas.",
    cv_selecione: "Elige un archivo.",
    cv_grande: "El archivo pesa más de 8 MB.",

    res_seus: "Tus resultados",
    res_pdf: "Descargar informe en PDF",
    res_nenhum: "Todavía no completaste ninguna prueba.",
    gerando: "Generando…",
    erro_pdf: "No fue posible generar el informe",

    r_pontos_fortes: "Puntos fuertes",
    r_pontos_desenv: "Puntos a desarrollar",
    r_disc_titulo: "Perfil de Comportamiento DISC",
    r_perfil_dominante: "Perfil principal: {nome} ({letra})",
    r_perfil_secundario: "Perfil secundario: {nome} ({letra})",
    r_estilo_trabalho: "Estilo de trabajo",
    r_base_titulo: "Código de Personalidad B.A.S.E.",
    r_seu_codigo: "Tu código: {codigo}",
    r_arquetipo: "Arquetipo principal: <strong>{nome}</strong>, {titulo}",
    r_com_perfil: "Con el perfil {nome}",
    r_interpretar: "Cómo leer el código completo",
    r_interpretar_desc: "Cada posición del código muestra algo diferente sobre cómo funciona la persona.",
    r_gatilhos: "Lo que te motiva y lo que te molesta",
    r_impulsiona: "Lo que te impulsa",
    r_incomoda: "Lo que te molesta",
    r_comunicar: "Cómo comunicarte con los otros perfiles",
    r_m_competencias: "Competencias",
    r_m_disc: "Perfil DISC",
    r_m_base: "Código B.A.S.E.",
    r_m_conhecimento: "Conocimientos",
    r_m_entrevista: "Entrevista",
    r_m_voz: "Entrevista por voz",
    r_md_competencias: "ajuste a las competencias requeridas",
    r_md_disc: "alineación con el perfil buscado: {nome}",
    r_md_base: "alineación con el arquetipo buscado: {nome}",
    r_md_conhecimento: "aciertos en la prueba de conocimientos del puesto",
    r_md_entrevista: "promedio de la entrevista estructurada",
    r_md_voz: "puntaje de la llamada de preselección con Francisca",
    r_mf_competencias: "autoevaluación de competencias",
    r_mf_disc: "prueba DISC",
    r_mf_base: "prueba B.A.S.E.",
    r_mf_conhecimento: "prueba de conocimientos",
    r_mf_entrevista: "entrevista",
    r_match_titulo: "Compatibilidad con el puesto",
    r_match_desc: "Un solo puntaje que combina todas las partes de la evaluación: competencias (peso 30%), perfil DISC (15%), código B.A.S.E. (15%), prueba de conocimientos (20%) y entrevista (20%). Los pesos se reparten entre lo que ya fue respondido.",
    r_match_desc_voz: " La entrevista por voz cuenta con el peso definido para el puesto y las demás partes se reparten el resto.",
    r_match_geral: "compatibilidad general",
    r_pendente: "Todavía no se cuenta (pendiente): {lista}.",
    r_apto: "Apto para el puesto",
    r_desenv: "En desarrollo",
    r_gap_alto: "Brecha alta",
    r_obrig_title: "Competencia obligatoria",
    r_sem_resposta: "sin respuesta",
    r_plano: "Plan de desarrollo sugerido",
    r_gap: "brecha {n}",
    r_nenhum_gap: "No se encontraron brechas: cumples todas las competencias requeridas.",
    r_aviso_sem_auto: "Todavía no respondiste la autoevaluación de competencias, por eso los niveles actuales aparecen en cero.",
    r_matriz_titulo: "Matriz de Brechas: {cargo}",
    r_aderencia: "Ajuste al puesto: {pct}%",
    r_obrig_pend: "{n} competencia(s) obligatoria(s) con brecha",
    r_th_comp: "Competencia",
    r_th_tipo: "Tipo",
    r_th_exigido: "Requerido",
    r_th_atual: "Actual",
    r_th_gap: "Brecha",

    v_titulo_pagina: "Bússola · Vacantes Abiertas",
    v_sub: "Vacantes abiertas",
    v_hero_h: "Vacantes abiertas",
    v_hero_h_local: "Vacantes abiertas · {local}",
    v_hero_p: "Postúlate a una vacante y haz la evaluación completa: pruebas de comportamiento, competencias y prueba de conocimientos.",
    v_pais: "País:",
    v_todos_paises: "Todos los países",
    v_carregando: "Cargando vacantes…",
    v_nenhuma_pais: "No hay vacantes abiertas en este país por ahora.",
    v_nenhuma: "No hay vacantes abiertas por ahora. Vuelve pronto.",
    v_candidatar: "Postularme",
    v_use_link: "Usa el enlace de vacantes que envió la empresa.",
    v_de: "Vacantes de {nome}",
    v_erro: "Error al cargar las vacantes.",
  },
};

// ------------------------------------------------ detecção do idioma
function normalizarIdioma(v) {
  const cod = String(v || "").trim().toLowerCase().slice(0, 2);
  return IDIOMAS_CAND.includes(cod) ? cod : "";
}

function idiomaNavegador() {
  const n = String(navigator.language || "").toLowerCase();
  if (n.startsWith("pt")) return "pt";
  if (n.startsWith("es")) return "es";
  return "en";
}

function lerIdiomaLocal() {
  try { return normalizarIdioma(localStorage.getItem("cand_idioma")); } catch (e) { return ""; }
}

// idioma pedido na URL (?lang=): tem prioridade sobre tudo
const idiomaDaUrl = normalizarIdioma(new URLSearchParams(location.search).get("lang"));
let idiomaCand = idiomaDaUrl || lerIdiomaLocal() || idiomaNavegador();

// ------------------------------------------------ tradução
function t(chave, vars) {
  const dic = I18N_CAND[idiomaCand] || I18N_CAND.pt;
  let s = dic[chave];
  if (s === undefined) s = I18N_CAND.pt[chave];
  if (s === undefined) return chave;
  if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
  return s;
}

// nome do país no idioma atual (o valor gravado nas vagas continua em português)
function nomePais(p) {
  return (typeof PAISES_NOMES !== "undefined" && PAISES_NOMES[p]) || p;
}

// textos fixos do HTML: elementos com o atributo data-i18n (nome da chave)
function aplicarTextosEstaticos() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPh);
  });
}

// troca o idioma da página inteira (sem redesenhar a tela atual)
function definirIdioma(lang) {
  const cod = normalizarIdioma(lang) || "pt";
  idiomaCand = cod;
  try { localStorage.setItem("cand_idioma", cod); } catch (e) { /* armazenamento bloqueado */ }
  document.documentElement.lang = LANG_HTML[cod];
  if (typeof aplicarIdiomaDados === "function") aplicarIdiomaDados(cod);
  aplicarTextosEstaticos();
  document.querySelectorAll(".seletor-idioma button").forEach((b) => {
    b.classList.toggle("ativo", b.dataset.lang === cod);
    b.setAttribute("aria-pressed", b.dataset.lang === cod ? "true" : "false");
  });
}

// seletor PT / EN / ES na barra superior; aoTrocar(lang) redesenha a tela
function montarSeletorIdioma(aoTrocar) {
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
  if (!acoes) return;
  const caixa = document.createElement("div");
  caixa.className = "seletor-idioma";
  caixa.setAttribute("role", "group");
  caixa.setAttribute("aria-label", t("idioma"));
  caixa.innerHTML = IDIOMAS_CAND.map((cod) =>
    `<button type="button" data-lang="${cod}" title="${{ pt: "Português", en: "English", es: "Español" }[cod]}">${cod.toUpperCase()}</button>`
  ).join("");
  acoes.insertBefore(caixa, acoes.firstChild);
  caixa.querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => {
      if (b.dataset.lang === idiomaCand) return;
      definirIdioma(b.dataset.lang);
      caixa.setAttribute("aria-label", t("idioma"));
      if (aoTrocar) aoTrocar(b.dataset.lang);
    })
  );
  definirIdioma(idiomaCand);
}

// aplica o idioma inicial assim que o arquivo carrega
definirIdioma(idiomaCand);

// consentimento para ligações e mensagens automáticas (TCPA) e "Parar ligações e mensagens".
// O texto de cad_contato é o mesmo guardado pelo servidor (conta.py, TEXTO_CONSENTIMENTO).
Object.assign(I18N_CAND.pt, {
  cad_contato: "Concordo que {empresa} pode me ligar e enviar mensagens de texto sobre a minha candidatura, inclusive com tecnologia automatizada e uma assistente de IA, no número que informei. As ligações podem ser gravadas. O consentimento não é condição para a contratação. Responda STOP para deixar de receber mensagens.",
  cad_contato_empresa: "a empresa",
  ct_titulo: "Ligações e mensagens",
  ct_desc: "Você pode pedir a qualquer momento que a empresa pare de ligar e de enviar mensagens automáticas sobre a sua candidatura.",
  ct_consentiu: "Você autorizou ligações e mensagens em {data}.",
  ct_parar: "Parar ligações e mensagens",
  ct_confirmar: "Parar as ligações e mensagens automáticas sobre a sua candidatura? A empresa ainda pode falar com você por e-mail.",
  ct_revogado: "Pronto. Você pediu para não receber ligações nem mensagens automáticas sobre a sua candidatura.",
});
Object.assign(I18N_CAND.en, {
  cad_contato: "I agree that {empresa} may call and text me about my application, including with automated technology and an AI assistant, at the number I provided. Calls may be recorded. Consent is not a condition of employment. Reply STOP to opt out of texts.",
  cad_contato_empresa: "the company",
  ct_titulo: "Calls and texts",
  ct_desc: "You can ask the company at any time to stop calling and sending automated texts about your application.",
  ct_consentiu: "You agreed to calls and texts on {data}.",
  ct_parar: "Stop calls and texts",
  ct_confirmar: "Stop automated calls and texts about your application? The company can still reach you by email.",
  ct_revogado: "Done. You asked not to receive automated calls or texts about your application.",
});
Object.assign(I18N_CAND.es, {
  cad_contato: "Acepto que {empresa} me llame y me envíe mensajes de texto sobre mi postulación, incluso con tecnología automatizada y una asistente de IA, al número que proporcioné. Las llamadas pueden ser grabadas. El consentimiento no es una condición para el empleo. Responde STOP para dejar de recibir mensajes.",
  cad_contato_empresa: "la empresa",
  ct_titulo: "Llamadas y mensajes",
  ct_desc: "Puedes pedirle a la empresa en cualquier momento que deje de llamarte y de enviarte mensajes automáticos sobre tu postulación.",
  ct_consentiu: "Autorizaste llamadas y mensajes el {data}.",
  ct_parar: "Dejar de recibir llamadas y mensajes",
  ct_confirmar: "¿Quieres dejar de recibir llamadas y mensajes automáticos sobre tu postulación? La empresa aún puede escribirte por correo.",
  ct_revogado: "Listo. Pediste no recibir llamadas ni mensajes automáticos sobre tu postulación.",
});
