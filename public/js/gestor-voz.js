/* =====================================================================
   Módulo Triagem por Voz (aba do painel do gestor e bloco na ficha do
   candidato). A Francisca liga para o candidato, o servidor calcula o
   score e convida STRONG e GOOD para os testes.
   Textos em português, inglês e espanhol (seletor próprio na aba).
   ===================================================================== */

const VOZ_TEXTOS = {
  pt: {
    identidade: "Identidade na ligação", nomeLigacao: "Nome da empresa falado na ligação", cidadeLigacao: "Cidade",
    telefoneRetorno: "Telefone de retorno (recado de correio de voz)", gerente: "Nome de quem contrata (ex.: Carine)",
    roteiro: "Roteiro", roteiroTitulo: "Roteiro da Francisca: {cargo}",
    roteiroDesc: "A Francisca só responde com o que estiver aqui. Pagamento, vínculo, horário, benefícios e regras.",
    fatosVaga: "Fatos da vaga", faqs: "Perguntas frequentes", faqPergunta: "Pergunta", faqResposta: "Resposta",
    addFaq: "Adicionar FAQ", perguntasExtras: "Perguntas extras de triagem (até 10)", addPergunta: "Adicionar pergunta",
    requisitos: "Requisitos que reprovam", exigeCarro: "Exige carro próprio", exigeCarteira: "Exige carteira de motorista",
    exigeSmartphone: "Exige smartphone", area25: "Cidades até ~25 milhas (uma por linha)", area40: "Cidades até ~40 milhas (uma por linha)",
    areaDica: "Deixe vazio para usar a área padrão de Hartford.", remover: "Remover", fechar: "Fechar",
    aba: "Triagem por voz",
    titulo: "Triagem por voz",
    sub: "A Francisca liga para cada candidato inscrito nas vagas com triagem por voz.",
    naoConfigurado: "ElevenLabs ainda não configurado. Preencha a integração abaixo.",
    semWebhook: "Webhook sem segredo: o resultado chega pela verificação automática (1 a 3 minutos).",
    rodar: "Rodar fila agora", pausar: "Pausar ligações", retomar: "Retomar ligações",
    pausado: "Ligações pausadas", ativo: "Fila ativa", desligado: "Triagem desligada",
    hoje: "Ligações hoje", atendidas: "Atendidas", strong: "STRONG hoje", good: "GOOD hoje", andamento: "Em andamento",
    fila: "Candidatos na triagem", todos: "Todos os status", vazio: "Nenhum candidato na triagem por voz.",
    col: { nome: "Candidato", vaga: "Vaga", status: "Status", tier: "Resultado", tentativas: "Tentativas", proxima: "Próxima" },
    ligar: "Ligar agora", naoLigar: "Não ligar", voltarFila: "Voltar à fila", zerar: "Zerar tentativas",
    entrarFila: "Colocar na fila",     revisadoHa: "fatos revisados há {n} dia(s)", revisarFatos: "revise os fatos (mais de 60 dias)", nuncaRevisado: "fatos ainda não revisados", ultimaRevisao: "Última revisão dos fatos: {d} por {p}.", avisoRevisao: "Salário, horário e regras mudam: revise os fatos da vaga pelo menos a cada 60 dias.", simular: "Simular ligação", simTitulo: "Simular ligação: {cargo}", simDesc: "Converse com a Francisca pelo microfone do computador, como se fosse um candidato. Usa o roteiro salvo (salve antes de simular) e não liga para ninguém. Conta como poucos minutos na ElevenLabs.", simIniciar: "Começar conversa", simEncerrar: "Encerrar", simConectando: "Conectando...", simFalando: "Francisca falando", simOuvindo: "Ouvindo você", simEncerrada: "Conversa encerrada.", simMic: "Permita o uso do microfone no navegador.", simVoce: "Você", simIdioma: "Idioma da simulação",     encerrados: "Encerrados", encerradosDesc: "Número errado, sem interesse, pediram para não ligar ou não qualificados. Saem da lista principal e do pipeline ativo da vaga.", semEncerrados: "Nenhum candidato encerrado.", fora: "Fora da triagem", foraDesc: "Candidatos de vagas com triagem por voz que ainda não entraram na fila (por exemplo, importados). Ligue agora para um ou coloque vários na fila: a fila só liga dentro da janela de horário.", foraVazio: "Todos os candidatos já estão na triagem.", selecionarTodos: "Selecionar todos", filaSelecionados: "Colocar selecionados na fila", colocados: "{n} candidato(s) na fila.", nenhumSelecionado: "Selecione ao menos um candidato.", semTelefone: "Sem telefone válido dos EUA",
    confirmaLigar: "Ligar agora para {nome}? A ligação sai na hora, mesmo fora da janela.",
    ligacaoIniciada: "Ligação iniciada. O resultado aparece em alguns minutos.",
    recentes: "Últimas ligações", semLigacoes: "Nenhuma ligação ainda.", entrada: "Recebida", atendidaEntrada: "Atendida", desconhecido: "Número desconhecido", vozTitulo: "Voz da Francisca", vozDesc: "Escolha a voz usada em cada idioma, nas ligações feitas e recebidas.", vozPadrao: "padrão", ouvir: "Ouvir amostra", parar: "Parar",
    config: "Regras de ligação", local: "Local", padrao: "Padrão (todos os locais)",
    cAtivo: "Triagem por voz ligada", cPausado: "Pausar todas as ligações deste local",
    fuso: "Fuso horário", inicio: "Início", fim: "Fim", dias: "Dias permitidos",
    diasSemana: ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
    maxTentativas: "Máximo de tentativas", simultaneas: "Ligações ao mesmo tempo",
    intervalo: "Horas entre tentativas", idiomaPadrao: "Idioma da abertura (quando desconhecido)",
    salvar: "Salvar", salvo: "Salvo",
    cargos: "Cargos com triagem por voz", cargosDesc: "Candidatos que se inscrevem em vagas destes cargos entram na fila. O peso define quanto a ligação vale no match geral.",
    peso: "Peso no match",
    integracao: "Integração ElevenLabs", apiKey: "Chave da API", apiKeyAtual: "Chave salva terminando em {f}. Deixe vazio para manter.",
    agentId: "ID da agente", phoneId: "ID do número de telefone", webhookSecret: "Segredo do webhook",
    webhookUrl: "Endereço do webhook para colar no ElevenLabs",
    ficha: "Triagem por voz", fichaVazia: "Sem triagem por voz.", pontos: "Pontos", motivos: "Motivos para revisar",
    respostas: "Respostas na ligação", transcricao: "Transcrição", esconder: "Esconder transcrição",
    resumo: "Resumo", gravacao: "Ouvir gravação", carregando: "Carregando...", convite: "Convite para os testes enviado",
    francisca: "Francisca", candidato: "Candidato", por: "por {q}", fila_auto: "fila automática",
    idiomaLigacao: { es: "espanhol", en: "inglês", pt: "português" },
    placar: "Placar da Francisca", placarSub: "Números por semana, no fuso da empresa ({fuso}).",
    periodos: { sem0: "Esta semana", sem1: "Semana passada", sem4: "Últimas 4 semanas", sem8: "Últimas 8 semanas" },
    pLigacoes: "Ligações", pTaxa: "Taxa de atendimento", pDuracao: "Duração média", pMediana: "mediana {d}",
    pQualificados: "Qualificados", pStrongGood: "STRONG + GOOD", pDetalhe: "{a} atendidas, {c} correio de voz, {s} sem resposta",
    pDeAtendidas: "das atendidas", pResultados: "Resultados", pTiers: "Tiers", pIdiomas: "Idioma (atendidas)",
    pHoras: "Melhores horários", pHorasDica: "Taxa de atendimento por hora local (top 5).", pLigs: "{n} lig.",
    pAbandono: "Onde desligaram", pAbandonoDica: "Última etapa alcançada nas ligações que terminaram sem resultado.",
    pFaltando: "Respostas que faltaram", pFaltandoDica: "Perguntas sem resposta nas ligações pontuadas.",
    pVazio: "Nenhuma ligação neste período.", pSemDados: "Sem dados no período.",
    etapas: { start: "Antes do consentimento", consent: "Consentimento", language: "Idioma", still_looking: "Ainda procura trabalho", requirements: "Requisitos (carteira e carro)", town: "Cidade", availability: "Disponibilidade", experience: "Experiência", previous_work: "Trabalhos anteriores", works_alone: "Trabalha sozinho", smartphone: "Smartphone", pets: "Pets", standards: "Padrões", start_date: "Data de início", text_phone: "Telefone para SMS", questions: "Perguntas do candidato" },
  },
  en: {
    identidade: "Call identity", nomeLigacao: "Company name spoken on the call", cidadeLigacao: "City",
    telefoneRetorno: "Callback phone (voicemail message)", gerente: "Hiring manager name (e.g. Carine)",
    roteiro: "Script", roteiroTitulo: "Francisca's script: {cargo}",
    roteiroDesc: "Francisca only answers with what is written here. Pay, employment type, hours, benefits and rules.",
    fatosVaga: "Job facts", faqs: "FAQs", faqPergunta: "Question", faqResposta: "Answer",
    addFaq: "Add FAQ", perguntasExtras: "Extra screening questions (up to 10)", addPergunta: "Add question",
    requisitos: "Requirements that disqualify", exigeCarro: "Own car required", exigeCarteira: "Driver's license required",
    exigeSmartphone: "Smartphone required", area25: "Towns within ~25 miles (one per line)", area40: "Towns within ~40 miles (one per line)",
    areaDica: "Leave empty to use the default Hartford area.", remover: "Remove", fechar: "Close",
    aba: "Voice screening",
    titulo: "Voice screening",
    sub: "Francisca calls every candidate who applies to a job with voice screening.",
    naoConfigurado: "ElevenLabs is not configured yet. Fill in the integration below.",
    semWebhook: "No webhook secret: results arrive through the automatic check (1 to 3 minutes).",
    rodar: "Run queue now", pausar: "Pause calls", retomar: "Resume calls",
    pausado: "Calls paused", ativo: "Queue active", desligado: "Screening off",
    hoje: "Calls today", atendidas: "Answered", strong: "STRONG today", good: "GOOD today", andamento: "In progress",
    fila: "Candidates in screening", todos: "All statuses", vazio: "No candidates in voice screening.",
    col: { nome: "Candidate", vaga: "Job", status: "Status", tier: "Result", tentativas: "Attempts", proxima: "Next" },
    ligar: "Call now", naoLigar: "Do not call", voltarFila: "Back to queue", zerar: "Reset attempts",
    entrarFila: "Add to queue",     revisadoHa: "facts reviewed {n} day(s) ago", revisarFatos: "review the facts (over 60 days)", nuncaRevisado: "facts not reviewed yet", ultimaRevisao: "Facts last reviewed: {d} by {p}.", avisoRevisao: "Pay, schedule and rules change: review the job facts at least every 60 days.", simular: "Simulate call", simTitulo: "Simulate call: {cargo}", simDesc: "Talk to Francisca with your computer microphone, as if you were a candidate. It uses the saved script (save before simulating) and calls nobody. It uses a few ElevenLabs minutes.", simIniciar: "Start conversation", simEncerrar: "End", simConectando: "Connecting...", simFalando: "Francisca speaking", simOuvindo: "Listening to you", simEncerrada: "Conversation ended.", simMic: "Allow microphone access in the browser.", simVoce: "You", simIdioma: "Simulation language",     encerrados: "Closed", encerradosDesc: "Wrong number, not interested, asked not to be called or not qualified. They leave the main list and the active job pipeline.", semEncerrados: "No closed candidates.", fora: "Not in screening", foraDesc: "Candidates for positions with phone screening who are not in the queue yet (for example, imported ones). Call one now or add several to the queue: the queue only calls within the calling window.", foraVazio: "All candidates are already in screening.", selecionarTodos: "Select all", filaSelecionados: "Add selected to queue", colocados: "{n} candidate(s) added to the queue.", nenhumSelecionado: "Select at least one candidate.", semTelefone: "No valid US phone number",
    confirmaLigar: "Call {nome} now? The call goes out right away, even outside the window.",
    ligacaoIniciada: "Call started. The result shows up in a few minutes.",
    recentes: "Latest calls", semLigacoes: "No calls yet.", entrada: "Inbound", atendidaEntrada: "Answered", desconhecido: "Unknown number", vozTitulo: "Francisca's voice", vozDesc: "Pick the voice used in each language, on outbound and inbound calls.", vozPadrao: "default", ouvir: "Play sample", parar: "Stop",
    config: "Calling rules", local: "Location", padrao: "Default (all locations)",
    cAtivo: "Voice screening on", cPausado: "Pause all calls for this location",
    fuso: "Time zone", inicio: "Start", fim: "End", dias: "Allowed days",
    diasSemana: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    maxTentativas: "Max attempts", simultaneas: "Calls at the same time",
    intervalo: "Hours between attempts", idiomaPadrao: "Opening language (when unknown)",
    salvar: "Save", salvo: "Saved",
    cargos: "Roles with voice screening", cargosDesc: "Candidates who apply to jobs for these roles enter the queue. The weight sets how much the call counts in the overall match.",
    peso: "Match weight",
    integracao: "ElevenLabs integration", apiKey: "API key", apiKeyAtual: "Saved key ending in {f}. Leave empty to keep it.",
    agentId: "Agent ID", phoneId: "Phone number ID", webhookSecret: "Webhook secret",
    webhookUrl: "Webhook address to paste in ElevenLabs",
    ficha: "Voice screening", fichaVazia: "No voice screening.", pontos: "Points", motivos: "Reasons to review",
    respostas: "Answers on the call", transcricao: "Transcript", esconder: "Hide transcript",
    resumo: "Summary", gravacao: "Play recording", carregando: "Loading...", convite: "Assessment invite sent",
    francisca: "Francisca", candidato: "Candidate", por: "by {q}", fila_auto: "automatic queue",
    idiomaLigacao: { es: "Spanish", en: "English", pt: "Portuguese" },
    placar: "Francisca's scoreboard", placarSub: "Weekly numbers in the company time zone ({fuso}).",
    periodos: { sem0: "This week", sem1: "Last week", sem4: "Last 4 weeks", sem8: "Last 8 weeks" },
    pLigacoes: "Calls", pTaxa: "Answer rate", pDuracao: "Avg. duration", pMediana: "median {d}",
    pQualificados: "Qualified", pStrongGood: "STRONG + GOOD", pDetalhe: "{a} answered, {c} voicemail, {s} no answer",
    pDeAtendidas: "of answered calls", pResultados: "Outcomes", pTiers: "Tiers", pIdiomas: "Language (answered)",
    pHoras: "Best hours", pHorasDica: "Answer rate by local hour (top 5).", pLigs: "{n} calls",
    pAbandono: "Where they hung up", pAbandonoDica: "Last step reached on calls that ended without a result.",
    pFaltando: "Missing answers", pFaltandoDica: "Questions left unanswered on scored calls.",
    pVazio: "No calls in this period.", pSemDados: "No data for this period.",
    etapas: { start: "Before consent", consent: "Consent", language: "Language", still_looking: "Still looking for work", requirements: "Requirements (license and car)", town: "Town", availability: "Availability", experience: "Experience", previous_work: "Previous work", works_alone: "Works alone", smartphone: "Smartphone", pets: "Pets", standards: "Standards", start_date: "Start date", text_phone: "Phone for texts", questions: "Candidate questions" },
  },
  es: {
    identidade: "Identidad en la llamada", nomeLigacao: "Nombre de la empresa dicho en la llamada", cidadeLigacao: "Ciudad",
    telefoneRetorno: "Teléfono de retorno (mensaje de buzón de voz)", gerente: "Nombre de quien contrata (ej.: Carine)",
    roteiro: "Guion", roteiroTitulo: "Guion de Francisca: {cargo}",
    roteiroDesc: "Francisca solo responde con lo que esté aquí. Pago, tipo de contrato, horario, beneficios y reglas.",
    fatosVaga: "Datos de la vacante", faqs: "Preguntas frecuentes", faqPergunta: "Pregunta", faqResposta: "Respuesta",
    addFaq: "Agregar pregunta frecuente", perguntasExtras: "Preguntas extra de evaluación (hasta 10)", addPergunta: "Agregar pregunta",
    requisitos: "Requisitos eliminatorios", exigeCarro: "Exige carro propio", exigeCarteira: "Exige licencia de conducir",
    exigeSmartphone: "Exige smartphone", area25: "Ciudades hasta ~25 millas (una por línea)", area40: "Ciudades hasta ~40 millas (una por línea)",
    areaDica: "Deje vacío para usar el área predeterminada de Hartford.", remover: "Quitar", fechar: "Cerrar",
    aba: "Evaluación por voz",
    titulo: "Evaluación por voz",
    sub: "Francisca llama a cada candidato que se postula a una vacante con evaluación por voz.",
    naoConfigurado: "ElevenLabs todavía no está configurado. Complete la integración abajo.",
    semWebhook: "Webhook sin secreto: el resultado llega por la verificación automática (1 a 3 minutos).",
    rodar: "Ejecutar cola ahora", pausar: "Pausar llamadas", retomar: "Reanudar llamadas",
    pausado: "Llamadas en pausa", ativo: "Cola activa", desligado: "Evaluación apagada",
    hoje: "Llamadas hoy", atendidas: "Contestadas", strong: "STRONG hoy", good: "GOOD hoy", andamento: "En curso",
    fila: "Candidatos en evaluación", todos: "Todos los estados", vazio: "Ningún candidato en evaluación por voz.",
    col: { nome: "Candidato", vaga: "Vacante", status: "Estado", tier: "Resultado", tentativas: "Intentos", proxima: "Próximo" },
    ligar: "Llamar ahora", naoLigar: "No llamar", voltarFila: "Volver a la cola", zerar: "Reiniciar intentos",
    entrarFila: "Agregar a la cola",     revisadoHa: "datos revisados hace {n} día(s)", revisarFatos: "revisa los datos (más de 60 días)", nuncaRevisado: "datos aún no revisados", ultimaRevisao: "Última revisión de los datos: {d} por {p}.", avisoRevisao: "El pago, el horario y las reglas cambian: revisa los datos de la vacante al menos cada 60 días.", simular: "Simular llamada", simTitulo: "Simular llamada: {cargo}", simDesc: "Habla con Francisca con el micrófono de la computadora, como si fueras un candidato. Usa el guion guardado (guarda antes de simular) y no llama a nadie. Usa pocos minutos de ElevenLabs.", simIniciar: "Empezar conversación", simEncerrar: "Terminar", simConectando: "Conectando...", simFalando: "Francisca hablando", simOuvindo: "Escuchándote", simEncerrada: "Conversación terminada.", simMic: "Permite el uso del micrófono en el navegador.", simVoce: "Tú", simIdioma: "Idioma de la simulación",     encerrados: "Cerrados", encerradosDesc: "Número equivocado, sin interés, pidieron no ser llamados o no calificados. Salen de la lista principal y del pipeline activo de la vacante.", semEncerrados: "Ningún candidato cerrado.", fora: "Fuera de la evaluación", foraDesc: "Candidatos de vacantes con evaluación por voz que aún no están en la cola (por ejemplo, importados). Llama a uno ahora o agrega varios a la cola: la cola solo llama dentro del horario permitido.", foraVazio: "Todos los candidatos ya están en la evaluación.", selecionarTodos: "Seleccionar todos", filaSelecionados: "Agregar seleccionados a la cola", colocados: "{n} candidato(s) agregados a la cola.", nenhumSelecionado: "Selecciona al menos un candidato.", semTelefone: "Sin teléfono válido de EE. UU.",
    confirmaLigar: "¿Llamar ahora a {nome}? La llamada sale de inmediato, incluso fuera del horario.",
    ligacaoIniciada: "Llamada iniciada. El resultado aparece en unos minutos.",
    recentes: "Últimas llamadas", semLigacoes: "Ninguna llamada todavía.", entrada: "Entrante", atendidaEntrada: "Atendida", desconhecido: "Número desconocido", vozTitulo: "Voz de Francisca", vozDesc: "Elija la voz usada en cada idioma, en las llamadas hechas y recibidas.", vozPadrao: "predeterminada", ouvir: "Escuchar muestra", parar: "Detener",
    config: "Reglas de llamada", local: "Local", padrao: "Predeterminado (todos los locales)",
    cAtivo: "Evaluación por voz encendida", cPausado: "Pausar todas las llamadas de este local",
    fuso: "Zona horaria", inicio: "Inicio", fim: "Fin", dias: "Días permitidos",
    diasSemana: ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
    maxTentativas: "Máximo de intentos", simultaneas: "Llamadas al mismo tiempo",
    intervalo: "Horas entre intentos", idiomaPadrao: "Idioma del saludo (si se desconoce)",
    salvar: "Guardar", salvo: "Guardado",
    cargos: "Cargos con evaluación por voz", cargosDesc: "Los candidatos que se postulan a vacantes de estos cargos entran en la cola. El peso define cuánto cuenta la llamada en el match general.",
    peso: "Peso en el match",
    integracao: "Integración ElevenLabs", apiKey: "Clave de la API", apiKeyAtual: "Clave guardada que termina en {f}. Deje vacío para mantenerla.",
    agentId: "ID de la agente", phoneId: "ID del número de teléfono", webhookSecret: "Secreto del webhook",
    webhookUrl: "Dirección del webhook para pegar en ElevenLabs",
    ficha: "Evaluación por voz", fichaVazia: "Sin evaluación por voz.", pontos: "Puntos", motivos: "Motivos para revisar",
    respostas: "Respuestas en la llamada", transcricao: "Transcripción", esconder: "Ocultar transcripción",
    resumo: "Resumen", gravacao: "Escuchar grabación", carregando: "Cargando...", convite: "Invitación a las pruebas enviada",
    francisca: "Francisca", candidato: "Candidato", por: "por {q}", fila_auto: "cola automática",
    idiomaLigacao: { es: "español", en: "inglés", pt: "portugués" },
    placar: "Marcador de Francisca", placarSub: "Números por semana, en la zona horaria de la empresa ({fuso}).",
    periodos: { sem0: "Esta semana", sem1: "Semana pasada", sem4: "Últimas 4 semanas", sem8: "Últimas 8 semanas" },
    pLigacoes: "Llamadas", pTaxa: "Tasa de respuesta", pDuracao: "Duración promedio", pMediana: "mediana {d}",
    pQualificados: "Calificados", pStrongGood: "STRONG + GOOD", pDetalhe: "{a} contestadas, {c} buzón de voz, {s} sin respuesta",
    pDeAtendidas: "de las contestadas", pResultados: "Resultados", pTiers: "Tiers", pIdiomas: "Idioma (contestadas)",
    pHoras: "Mejores horarios", pHorasDica: "Tasa de respuesta por hora local (top 5).", pLigs: "{n} llam.",
    pAbandono: "Dónde colgaron", pAbandonoDica: "Último paso alcanzado en las llamadas que terminaron sin resultado.",
    pFaltando: "Respuestas que faltaron", pFaltandoDica: "Preguntas sin respuesta en las llamadas con puntaje.",
    pVazio: "Ninguna llamada en este período.", pSemDados: "Sin datos en este período.",
    etapas: { start: "Antes del consentimiento", consent: "Consentimiento", language: "Idioma", still_looking: "Todavía busca trabajo", requirements: "Requisitos (licencia y carro)", town: "Ciudad", availability: "Disponibilidad", experience: "Experiencia", previous_work: "Trabajos anteriores", works_alone: "Trabaja solo", smartphone: "Smartphone", pets: "Mascotas", standards: "Normas", start_date: "Fecha de inicio", text_phone: "Teléfono para mensajes", questions: "Preguntas del candidato" },
  },
};

const VOZ_STATUS = {
  pt: { para_ligar: "Para ligar", ligando: "Ligando", concluida: "Concluída", callback: "Callback", nao_qualificado: "Não qualificado", nao_interessado: "Não interessado", correio_voz: "Correio de voz", numero_errado: "Número errado", nao_ligar: "Não ligar", revisar: "Revisar" },
  en: { para_ligar: "To call", ligando: "Calling", concluida: "Completed", callback: "Callback", nao_qualificado: "Not qualified", nao_interessado: "Not interested", correio_voz: "Voicemail", numero_errado: "Wrong number", nao_ligar: "Do not call", revisar: "Review" },
  es: { para_ligar: "Por llamar", ligando: "Llamando", concluida: "Completada", callback: "Devolver llamada", nao_qualificado: "No calificado", nao_interessado: "No interesado", correio_voz: "Buzón de voz", numero_errado: "Número equivocado", nao_ligar: "No llamar", revisar: "Revisar" },
};

const VOZ_OUTCOME = {
  pt: { QUALIFIED: "Qualificado", NOT_QUALIFIED: "Não qualificado", NEEDS_REVIEW: "Revisar", CALLBACK: "Callback", NOT_INTERESTED: "Não interessado", VOICEMAIL: "Correio de voz", WRONG_NUMBER: "Número errado", NOT_AVAILABLE: "Não disponível", DO_NOT_CALL: "Não ligar", NO_ANSWER: "Sem resposta" },
  en: { QUALIFIED: "Qualified", NOT_QUALIFIED: "Not qualified", NEEDS_REVIEW: "Needs review", CALLBACK: "Callback", NOT_INTERESTED: "Not interested", VOICEMAIL: "Voicemail", WRONG_NUMBER: "Wrong number", NOT_AVAILABLE: "Not available", DO_NOT_CALL: "Do not call", NO_ANSWER: "No answer" },
  es: { QUALIFIED: "Calificado", NOT_QUALIFIED: "No calificado", NEEDS_REVIEW: "Revisar", CALLBACK: "Devolver llamada", NOT_INTERESTED: "No interesado", VOICEMAIL: "Buzón de voz", WRONG_NUMBER: "Número equivocado", NOT_AVAILABLE: "No disponible", DO_NOT_CALL: "No llamar", NO_ANSWER: "Sin respuesta" },
};

const VOZ_PONTOS = {
  pt: { availability: ["Disponibilidade", 25], experience: ["Experiência", 20], location: ["Localização", 15], works_alone: ["Trabalha sozinho", 10], smartphone: ["Smartphone", 10], start_date: ["Início", 10], pets: ["Pets", 5], standards: ["Padrões", 5] },
  en: { availability: ["Availability", 25], experience: ["Experience", 20], location: ["Location", 15], works_alone: ["Works alone", 10], smartphone: ["Smartphone", 10], start_date: ["Start date", 10], pets: ["Pets", 5], standards: ["Standards", 5] },
  es: { availability: ["Disponibilidad", 25], experience: ["Experiencia", 20], location: ["Ubicación", 15], works_alone: ["Trabaja solo", 10], smartphone: ["Smartphone", 10], start_date: ["Inicio", 10], pets: ["Mascotas", 5], standards: ["Normas", 5] },
};

const VOZ_FATOS = {
  pt: { license: "Carteira de motorista", own_car: "Carro próprio", city: "Cidade", weekdays_available: "Dias úteis disponíveis", days_available: "Dias (palavras do candidato)", saturdays_ok: "Aceita sábado", experience: "Experiência", works_alone: "Trabalha sozinho", has_smartphone: "Tem smartphone", start_date: "Início", pets: "Pets", standards: "Padrões", interview_windows: "Janelas para entrevista", text_phone: "Telefone para SMS", ok_to_text: "Aceita SMS", candidate_questions: "Perguntas do candidato", callback_time: "Pediu retorno em", notes: "Notas da agente", extra_answers: "Respostas às perguntas extras", previous_work: "Trabalhos anteriores e currículo" },
  en: { license: "Driver's license", own_car: "Own car", city: "Town", weekdays_available: "Weekdays available", days_available: "Days (candidate's words)", saturdays_ok: "Open to Saturdays", experience: "Experience", works_alone: "Works alone", has_smartphone: "Has a smartphone", start_date: "Start", pets: "Pets", standards: "Standards", interview_windows: "Interview windows", text_phone: "Phone for texts", ok_to_text: "OK to text", candidate_questions: "Candidate questions", callback_time: "Callback requested for", notes: "Agent notes", extra_answers: "Answers to extra questions", previous_work: "Previous work and resume" },
  es: { license: "Licencia de conducir", own_car: "Carro propio", city: "Ciudad", weekdays_available: "Días entre semana", days_available: "Días (palabras del candidato)", saturdays_ok: "Acepta sábados", experience: "Experiencia", works_alone: "Trabaja solo", has_smartphone: "Tiene smartphone", start_date: "Inicio", pets: "Mascotas", standards: "Normas", interview_windows: "Horarios para entrevista", text_phone: "Teléfono para mensajes", ok_to_text: "Acepta mensajes", candidate_questions: "Preguntas del candidato", callback_time: "Pidió que le llamen", notes: "Notas de la agente", extra_answers: "Respuestas a preguntas extra", previous_work: "Trabajos anteriores y currículum" },
};

const VOZ_VALORES = {
  pt: { yes: "sim", no: "não", unclear: "não ficou claro", hesitant: "hesitante", comfortable: "à vontade", some_or_no: "só alguns ou não", accepted: "aceitou", hesitant_or_objects: "hesitou ou discordou", true: "sim", false: "não" },
  en: { yes: "yes", no: "no", unclear: "unclear", hesitant: "hesitant", comfortable: "comfortable", some_or_no: "only some or no", accepted: "accepted", hesitant_or_objects: "hesitant or objects", true: "yes", false: "no" },
  es: { yes: "sí", no: "no", unclear: "no quedó claro", hesitant: "dudoso", comfortable: "cómodo", some_or_no: "solo algunas o no", accepted: "aceptó", hesitant_or_objects: "dudó o se opuso", true: "sí", false: "no" },
};

const VOZ_MOTIVOS = {
  pt: { no_outcome: "A ligação não trouxe um resultado", outcome_corrected: "Desligou antes do fim, mas respondeu a triagem", license_unclear: "Resposta sobre carteira não ficou clara", car_unclear: "Resposta sobre carro não ficou clara", not_qualified_without_gate: "A agente reprovou sem falha nos requisitos", outside_area: "Mora fora da área atendida", location_unknown: "Cidade desconhecida ou fora da lista", no_smartphone: "Não tem smartphone", standards_objection: "Hesitou ou discordou dos padrões", missing: "Sem resposta: {i}" },
  en: { no_outcome: "The call returned no outcome", outcome_corrected: "Hung up before the end but answered the screening", license_unclear: "License answer was unclear", car_unclear: "Own car answer was unclear", not_qualified_without_gate: "Agent rejected without a failed requirement", outside_area: "Lives outside the service area", location_unknown: "Town unknown or not on the list", no_smartphone: "No smartphone", standards_objection: "Hesitant or objects to the standards", missing: "No answer: {i}" },
  es: { no_outcome: "La llamada no trajo un resultado", outcome_corrected: "Colgó antes del final, pero respondió la evaluación", license_unclear: "La respuesta sobre la licencia no quedó clara", car_unclear: "La respuesta sobre el carro no quedó clara", not_qualified_without_gate: "La agente rechazó sin fallar un requisito", outside_area: "Vive fuera del área de servicio", location_unknown: "Ciudad desconocida o fuera de la lista", no_smartphone: "No tiene smartphone", standards_objection: "Dudó o se opuso a las normas", missing: "Sin respuesta: {i}" },
};

const VOZ_ERROS = {
  pt: { do_not_call: "Candidato marcado como Não ligar.", blocked_outcome: "O candidato pediu para não ligar ou não tem interesse.", invalid_phone: "Telefone inválido: a ligação só sai para números dos EUA.", in_call: "O candidato está em ligação agora.", attempts_exhausted: "Tentativas esgotadas. Zere as tentativas primeiro.", not_configured: "Configure a integração ElevenLabs primeiro.", start_failed: "Não foi possível iniciar a ligação.", status_changed: "O status mudou. Recarregue.", anonymized: "Candidato anonimizado.", forbidden: "Sem permissão.", invalid_time: "Horário inválido (use HH:MM).", invalid_number: "Número fora do permitido.", invalid_days: "Escolha ao menos um dia.", text_too_long: "Texto longo demais.", module_disabled: "Módulo não liberado para esta conta.", invalid_voice: "Voz inválida." },
  en: { do_not_call: "Candidate is marked Do not call.", blocked_outcome: "The candidate asked not to be called or is not interested.", invalid_phone: "Invalid phone: calls only go to US numbers.", in_call: "The candidate is on a call right now.", attempts_exhausted: "No attempts left. Reset attempts first.", not_configured: "Set up the ElevenLabs integration first.", start_failed: "Could not start the call.", status_changed: "The status changed. Reload.", anonymized: "Candidate anonymized.", forbidden: "Not allowed.", invalid_time: "Invalid time (use HH:MM).", invalid_number: "Number out of range.", invalid_days: "Pick at least one day.", text_too_long: "Text is too long.", module_disabled: "Module not enabled for this account.", invalid_voice: "Invalid voice." },
  es: { do_not_call: "Candidato marcado como No llamar.", blocked_outcome: "El candidato pidió no ser llamado o no tiene interés.", invalid_phone: "Teléfono inválido: las llamadas solo salen a números de EE. UU.", in_call: "El candidato está en una llamada ahora.", attempts_exhausted: "Intentos agotados. Reinicie los intentos primero.", not_configured: "Configure primero la integración ElevenLabs.", start_failed: "No se pudo iniciar la llamada.", status_changed: "El estado cambió. Recargue.", anonymized: "Candidato anonimizado.", forbidden: "Sin permiso.", invalid_time: "Hora inválida (use HH:MM).", invalid_number: "Número fuera del rango.", invalid_days: "Elija al menos un día.", text_too_long: "Texto demasiado largo.", module_disabled: "Módulo no habilitado para esta cuenta.", invalid_voice: "Voz inválida." },
};

const VOZ_CORES_TIER = { STRONG: "ok", GOOD: "info", REVIEW: "warn", LOW: "err" };

let vozIdioma = (() => {
  try {
    const salvo = localStorage.getItem("idioma");
    if (salvo === "pt" || salvo === "en" || salvo === "es") return salvo;
  } catch (e) { /* armazenamento bloqueado */ }
  return "pt";
})();
let vozFiltro = "";

function vt(chave, vars) {
  let txt = VOZ_TEXTOS[vozIdioma][chave];
  if (vars) Object.keys(vars).forEach((k) => { txt = txt.replace("{" + k + "}", vars[k]); });
  return txt;
}

function vozModuloAtivo() {
  const info = infoGestor();
  return !!info.admin || (info.modulos || []).includes("voz");
}

/** Mensagem traduzida de um erro de API (a mensagem do servidor traz o código antes de ':'). */
function vozErro(e) {
  const codigo = String((e && e.message) || "").split(":")[0].trim();
  return VOZ_ERROS[vozIdioma][codigo] || (e && e.message) || "Erro";
}

async function vozApi(caminho, opcoes) {
  try {
    return await api(caminho, opcoes);
  } catch (e) {
    throw new Error(vozErro(e));
  }
}

function vozData(texto) {
  if (!texto) return "";
  const d = new Date(texto.replace(" ", "T") + "Z");
  const locale = { pt: "pt-BR", en: "en-US", es: "es-US" }[vozIdioma];
  return d.toLocaleString(locale, { timeZone: "America/New_York", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function vozBadgeStatus(s) {
  const cor = { concluida: "ok", ligando: "info", para_ligar: "info", revisar: "warn", callback: "warn", nao_ligar: "err", nao_qualificado: "err" }[s] || "";
  return `<span class="badge ${cor}">${esc(VOZ_STATUS[vozIdioma][s] || (s ? s : vt("fora")))}</span>`;
}

function vozBadgeTier(tier, score) {
  if (!tier) return "";
  return `<span class="badge ${VOZ_CORES_TIER[tier] || ""}">${esc(tier)}${score != null ? " " + score : ""}</span>`;
}

function vozSeletorIdioma() {
  return `<div class="tabs" style="margin:0">${["pt", "en", "es"].map((l) =>
    `<button class="tab ${vozIdioma === l ? "ativa" : ""}" data-voz-idioma="${l}">${l.toUpperCase()}</button>`).join("")}</div>`;
}

function vozLigarSeletor(el, redesenhar) {
  el.querySelectorAll("[data-voz-idioma]").forEach((b) => b.addEventListener("click", () => {
    vozIdioma = b.dataset.vozIdioma;
    try { localStorage.setItem("idioma", vozIdioma); } catch (e) { /* ok */ }
    redesenhar();
  }));
}

// ------------------------------------------------ aba
async function abaVoz(el) {
  el.innerHTML = `<div class="card"><p class="desc">${vt("carregando")}</p></div>`;
  let r;
  try {
    r = await vozApi("/api/gestor/voz");
  } catch (e) {
    el.innerHTML = `<div class="card"><p class="form-erro">${esc(e.message)}</p></div>`;
    return;
  }
  const cfg = r.config;
  const ENCERRADOS = ["numero_errado", "nao_interessado", "nao_ligar", "nao_qualificado"];
  const encerrados = r.fila.filter((f) => ENCERRADOS.includes(f.voz_status));
  const fila = r.fila.filter((f) => !ENCERRADOS.includes(f.voz_status) && (!vozFiltro || f.voz_status === vozFiltro));
  const estado = !cfg.ativo ? vt("desligado") : cfg.pausado ? vt("pausado") : vt("ativo");

  el.innerHTML = `
    <div class="card" style="padding:22px 28px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
        <div>
          <h2 class="icone-titulo" style="margin-bottom:2px">${icone("usuarios")}<span>${vt("titulo")}</span></h2>
          <p class="desc" style="margin:0">${vt("sub")}</p>
        </div>
        ${vozSeletorIdioma()}
      </div>
      ${!r.configurado ? `<p class="form-erro" style="margin-top:12px">${vt("naoConfigurado")}</p>` : ""}
      ${r.configurado && !r.webhook_configurado ? `<p class="hint" style="margin-top:12px">${vt("semWebhook")}</p>` : ""}
      <div class="linha-acoes" style="margin-top:14px">
        <span class="badge ${cfg.pausado || !cfg.ativo ? "err" : "ok"}">${estado}${r.empresa ? " · " + esc(r.empresa) : ""}</span>
        <button class="btn secondary small" id="voz-rodar" ${cfg.pausado || !r.configurado ? "disabled" : ""}>${vt("rodar")}</button>
        <button class="btn ${cfg.pausado ? "" : "secondary"} small" id="voz-pausa">${cfg.pausado ? vt("retomar") : vt("pausar")}</button>
        <span class="desc" id="voz-aviso" style="margin:0"></span>
      </div>
    </div>
    <div class="metricas">
      <div class="metrica"><div class="num">${r.hoje.ligacoes}</div><div class="rot">${vt("hoje")}</div></div>
      <div class="metrica"><div class="num">${r.hoje.atendidas}</div><div class="rot">${vt("atendidas")}</div></div>
      <div class="metrica"><div class="num">${r.hoje.strong}</div><div class="rot">${vt("strong")}</div></div>
      <div class="metrica"><div class="num">${r.hoje.good}</div><div class="rot">${vt("good")}</div></div>
      <div class="metrica"><div class="num">${r.ativas}</div><div class="rot">${vt("andamento")}</div></div>
    </div>
    <div class="card" id="voz-placar"></div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <h3 style="margin:0">${vt("fila")} (${fila.length})</h3>
        <select id="voz-filtro" style="max-width:220px">
          <option value="">${vt("todos")}</option>
          ${Object.entries(VOZ_STATUS[vozIdioma]).filter(([k]) => !ENCERRADOS.includes(k)).map(([k, v]) => `<option value="${k}" ${vozFiltro === k ? "selected" : ""}>${esc(v)}</option>`).join("")}
        </select>
      </div>
      ${fila.length ? `<div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>${vt("col").nome}</th><th>${vt("col").vaga}</th><th>${vt("col").status}</th><th>${vt("col").tier}</th>
          <th class="num">${vt("col").tentativas}</th><th>${vt("col").proxima}</th><th></th></tr></thead>
        <tbody>${fila.map((f) => `
          <tr>
            <td><a href="#" data-voz-cand="${f.candidato_id}"><strong>${esc(f.nome)}</strong></a>
              ${f.telefone_valido ? "" : ` <span class="badge err" title="${esc(VOZ_ERROS[vozIdioma].invalid_phone)}">!</span>`}</td>
            <td>${esc(f.vaga)}<div class="hint">${esc(f.local || "")}</div></td>
            <td>${vozBadgeStatus(f.voz_status)}</td>
            <td>${vozBadgeTier(f.voz_tier, f.voz_score)} ${f.voz_outcome && !f.voz_tier ? esc(VOZ_OUTCOME[vozIdioma][f.voz_outcome] || f.voz_outcome) : ""}</td>
            <td class="num">${f.voz_tentativas || 0}</td>
            <td>${f.voz_status === "para_ligar" ? esc(vozData(f.voz_proxima)) : ""}</td>
            <td style="white-space:nowrap">${vozBotoesCandidatura(f)}</td>
          </tr>`).join("")}</tbody></table></div>` : `<p class="desc">${vt("vazio")}</p>`}
    </div>
    ${vozHtmlFora(r.fora || [])}
    <details class="card" id="voz-encerrados">
      <summary style="cursor:pointer"><h3 style="display:inline;margin:0">${vt("encerrados")} (${encerrados.length})</h3></summary>
      <p class="desc">${vt("encerradosDesc")}</p>
      ${encerrados.length ? `<div class="tabela-wrap"><table class="tabela"><tbody>${encerrados.map((f) => `
        <tr>
          <td><a href="#" data-voz-cand="${f.candidato_id}"><strong>${esc(f.nome)}</strong></a><div class="hint">${esc(f.vaga)}</div></td>
          <td>${vozBadgeStatus(f.voz_status)}</td>
          <td style="white-space:nowrap">${f.voz_status !== "ligando" ? `<button class="btn secondary small" data-voz-acao="fila" data-id="${f.id}">${vt("voltarFila")}</button>` : ""}</td>
        </tr>`).join("")}</tbody></table></div>` : `<p class="desc">${vt("semEncerrados")}</p>`}
    </details>
    <div class="card">
      <h3 style="margin-top:0">${vt("recentes")}</h3>
      ${r.recentes.length ? `<div class="tabela-wrap"><table class="tabela"><tbody>${r.recentes.map((c) => `
        <tr><td>${esc(vozData(c.iniciada_em))}${c.direcao === "entrada" ? ` <span class="badge info">${vt("entrada")}</span>` : ""}</td>
          <td>${c.candidato_id ? `<a href="#" data-voz-cand="${c.candidato_id}">${esc(c.nome)}</a>`
            : `${esc(c.telefone || vt("desconhecido"))}${c.resumo ? `<div class="hint">${esc(c.resumo.slice(0, 200))}</div>` : ""}`}</td>
          <td>${esc((VOZ_TEXTOS[vozIdioma].idiomaLigacao)[c.idioma] || c.idioma)}</td>
          <td>${c.resultado ? esc(VOZ_OUTCOME[vozIdioma][c.resultado.outcome] || c.resultado.outcome) + " " + vozBadgeTier(c.resultado.tier, c.resultado.score)
            : c.direcao === "entrada" && c.status === "concluida" && !c.erro ? esc(vt("atendidaEntrada"))
            : (c.status === "concluida" || c.status === "falhou" ? esc(VOZ_OUTCOME[vozIdioma].NO_ANSWER) : esc(VOZ_STATUS[vozIdioma].ligando))}</td>
          <td class="num">${c.duracao != null ? Math.floor(c.duracao / 60) + ":" + String(c.duracao % 60).padStart(2, "0") : ""}</td></tr>`).join("")}
      </tbody></table></div>` : `<p class="desc">${vt("semLigacoes")}</p>`}
    </div>
    ${r.admin ? vozHtmlConfig(r, cfg) : ""}
    ${r.admin ? vozHtmlCargos(r) : ""}`;

  const redesenhar = () => abaVoz(el);
  vozLigarSeletor(el, redesenhar);
  const aviso = (msg, erro) => {
    const a = el.querySelector("#voz-aviso");
    a.textContent = msg;
    a.style.color = erro ? "var(--err, #c0392b)" : "";
  };
  el.querySelector("#voz-filtro").addEventListener("change", (ev) => { vozFiltro = ev.target.value; redesenhar(); });
  el.querySelector("#voz-rodar").addEventListener("click", async () => {
    try { await vozApi("/api/gestor/voz/rodar", { method: "POST" }); redesenhar(); } catch (e) { aviso(e.message, true); }
  });
  el.querySelector("#voz-pausa").addEventListener("click", async () => {
    try {
      await vozApi("/api/gestor/voz/config", { method: "POST", body: { config: { pausado: !cfg.pausado } } });
      redesenhar();
    } catch (e) { aviso(e.message, true); }
  });
  el.querySelectorAll("[data-voz-cand]").forEach((a) => a.addEventListener("click", (ev) => {
    ev.preventDefault();
    abrirDetalheCandidato(Number(a.dataset.vozCand));
  }));
  vozCarregarPlacar(el.querySelector("#voz-placar"));
  vozLigarBotoesCandidatura(el, redesenhar, aviso);
  vozLigarFora(el, redesenhar, aviso);
  if (r.admin) {
    vozLigarConfig(el, r, redesenhar);
    vozLigarCargos(el, redesenhar);
  }
}

// ------------------------------------------------ placar semanal
let vozPlacarPeriodo = "sem0";
const VOZ_PLACAR_SEMANAS = { sem0: 1, sem1: 2, sem4: 4, sem8: 8 };

function vozDuracao(seg) {
  if (seg == null) return "";
  const s = Math.round(seg);
  return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
}

function vozPct(v) {
  return v == null ? "" : String(v).replace(/\.0$/, "") + "%";
}

/** Lista de barras horizontais em HTML e CSS puro: itens = [{rot, n, valor?, dica?}]. */
function vozBarras(itens, maximo) {
  const lista = itens.filter((i) => i.n > 0);
  if (!lista.length) return `<p class="hint" style="margin:6px 0 0">${vt("pSemDados")}</p>`;
  const max = maximo || Math.max(...lista.map((i) => i.n)) || 1;
  return `<div style="display:flex;flex-direction:column;gap:7px;margin-top:8px">${lista.map((i) => `
    <div title="${esc(i.dica || "")}">
      <div style="display:flex;justify-content:space-between;gap:8px;font-size:.85rem">
        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(i.rot)}</span>
        <strong style="white-space:nowrap">${esc(i.valor != null ? i.valor : String(i.n))}</strong>
      </div>
      <div style="height:6px;border-radius:3px;background:var(--line-soft, rgba(127,127,127,.18));overflow:hidden;margin-top:3px">
        <div style="height:100%;width:${Math.max(2, Math.round((100 * i.n) / max))}%;background:var(--accent, #4a7bd0);border-radius:3px"></div>
      </div>
    </div>`).join("")}</div>`;
}

function vozBlocoPlacar(titulo, dica, corpo) {
  return `<div style="min-width:0">
    <h4 style="margin:0">${titulo}</h4>
    ${dica ? `<p class="hint" style="margin:2px 0 0">${dica}</p>` : ""}
    ${corpo}
  </div>`;
}

function vozHtmlPlacar(d) {
  const p = vozPlacarPeriodo === "sem1" ? d.semanas[1] : d.total;
  const T = VOZ_TEXTOS[vozIdioma];
  const seletor = `<div class="tabs" style="margin:0;flex-wrap:wrap">${Object.keys(VOZ_PLACAR_SEMANAS).map((k) =>
    `<button class="tab ${vozPlacarPeriodo === k ? "ativa" : ""}" data-voz-periodo="${k}">${esc(T.periodos[k])}</button>`).join("")}</div>`;
  const topo = `<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
      <div><h3 style="margin:0">${vt("placar")}</h3>
        <p class="hint" style="margin:2px 0 0">${esc(vt("placarSub", { fuso: d.fuso }))}${p ? " " + esc(p.inicio) + " / " + esc(p.fim) : ""}</p></div>
      ${seletor}
    </div>`;
  if (!p || !p.ligacoes) return topo + `<p class="desc" style="margin-top:14px">${vt("pVazio")}</p>`;
  const outcomes = Object.entries(p.outcomes).map(([k, n]) => ({ rot: VOZ_OUTCOME[vozIdioma][k] || k, n }));
  const tiers = Object.entries(p.tiers).map(([k, n]) => ({ rot: k, n }));
  const idiomas = Object.entries(p.idiomas).map(([k, n]) => ({ rot: T.idiomaLigacao[k] || k, n }));
  const horas = [...p.horas].sort((a, b) => (b.taxa - a.taxa) || (b.ligacoes - a.ligacoes) || (a.hora - b.hora)).slice(0, 5)
    .map((h) => ({ rot: String(h.hora).padStart(2, "0") + ":00", n: h.taxa || 0.0001, valor: vozPct(h.taxa) + " (" + vt("pLigs", { n: h.ligacoes }) + ")" }));
  const abandono = p.abandono.map((a) => ({ rot: T.etapas[a.etapa] || a.etapa, n: a.n }));
  const faltando = p.faltando.map((f) => ({ rot: (VOZ_PONTOS[vozIdioma][f.item] || [f.item])[0], n: f.n }));
  const tile = (num, rot, sub) => `<div class="metrica"><div class="num">${esc(String(num))}</div><div class="rot">${esc(rot)}</div>${sub ? `<div class="hint" style="margin-top:4px">${esc(sub)}</div>` : ""}</div>`;
  return topo + `
    <div class="metricas" style="margin:16px 0">
      ${tile(p.ligacoes, vt("pLigacoes"), vt("pDetalhe", { a: p.atendidas, c: p.correio_voz, s: p.sem_resposta }))}
      ${tile(p.taxa_atendimento == null ? "0%" : vozPct(p.taxa_atendimento), vt("pTaxa"), "")}
      ${tile(p.duracao_media == null ? "0:00" : vozDuracao(p.duracao_media), vt("pDuracao"), p.duracao_mediana == null ? "" : vt("pMediana", { d: vozDuracao(p.duracao_mediana) }))}
      ${tile(p.qualificados_pct == null ? "0%" : vozPct(p.qualificados_pct), vt("pQualificados"), vt("pDeAtendidas"))}
      ${tile(p.strong_good, vt("pStrongGood"), "")}
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:22px">
      ${vozBlocoPlacar(vt("pResultados"), "", vozBarras(outcomes))}
      ${vozBlocoPlacar(vt("pTiers"), "", vozBarras(tiers))}
      ${vozBlocoPlacar(vt("pIdiomas"), "", vozBarras(idiomas))}
      ${vozBlocoPlacar(vt("pHoras"), vt("pHorasDica"), vozBarras(horas, 100))}
      ${vozBlocoPlacar(vt("pAbandono"), vt("pAbandonoDica"), vozBarras(abandono))}
      ${vozBlocoPlacar(vt("pFaltando"), vt("pFaltandoDica"), vozBarras(faltando))}
    </div>`;
}

async function vozCarregarPlacar(caixa) {
  if (!caixa) return;
  caixa.innerHTML = `<h3 style="margin:0">${vt("placar")}</h3><p class="desc">${vt("carregando")}</p>`;
  let d;
  try {
    d = await vozApi("/api/gestor/voz/placar?semanas=" + VOZ_PLACAR_SEMANAS[vozPlacarPeriodo]);
  } catch (e) {
    caixa.innerHTML = `<h3 style="margin:0">${vt("placar")}</h3><p class="form-erro">${esc(e.message)}</p>`;
    return;
  }
  caixa.innerHTML = vozHtmlPlacar(d);
  caixa.querySelectorAll("[data-voz-periodo]").forEach((b) => b.addEventListener("click", () => {
    vozPlacarPeriodo = b.dataset.vozPeriodo;
    vozCarregarPlacar(caixa);
  }));
}

function vozHtmlFora(fora) {
  return `<div class="card" id="voz-fora">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
      <h3 style="margin:0">${vt("fora")} (${fora.length})</h3>
      ${fora.length ? `<button class="btn small" id="voz-fora-fila">${vt("filaSelecionados")}</button>` : ""}
    </div>
    <p class="desc">${vt("foraDesc")}</p>
    ${fora.length ? `<div class="tabela-wrap"><table class="tabela">
      <thead><tr><th><input type="checkbox" id="voz-fora-todos" title="${esc(vt("selecionarTodos"))}"></th>
        <th>${vt("col").nome}</th><th>${vt("col").vaga}</th><th></th></tr></thead>
      <tbody>${fora.map((f) => `
        <tr>
          <td><input type="checkbox" data-voz-fora="${f.id}" ${f.telefone_valido ? "" : "disabled"}></td>
          <td><a href="#" data-voz-cand="${f.candidato_id}"><strong>${esc(f.nome)}</strong></a>
            ${f.telefone_valido ? "" : ` <span class="badge err">${esc(vt("semTelefone"))}</span>`}</td>
          <td>${esc(f.vaga)}<div class="hint">${esc(f.local || "")}</div></td>
          <td style="white-space:nowrap">${f.telefone_valido ? `<button class="btn small" data-voz-ligar="${f.id}" data-nome="${esc(f.nome)}">${vt("ligar")}</button>
            <button class="btn secondary small" data-voz-acao="fila" data-id="${f.id}">${vt("entrarFila")}</button>` : ""}</td>
        </tr>`).join("")}</tbody></table></div>` : `<p class="desc">${vt("foraVazio")}</p>`}
  </div>`;
}

function vozLigarFora(el, redesenhar, aviso) {
  const todos = el.querySelector("#voz-fora-todos");
  if (todos) todos.addEventListener("change", () => {
    el.querySelectorAll("[data-voz-fora]:not([disabled])").forEach((c) => { c.checked = todos.checked; });
  });
  const botao = el.querySelector("#voz-fora-fila");
  if (botao) botao.addEventListener("click", async () => {
    const ids = [...el.querySelectorAll("[data-voz-fora]:checked")].map((c) => Number(c.dataset.vozFora));
    if (!ids.length) return aviso(vt("nenhumSelecionado"), true);
    botao.disabled = true;
    try {
      const r = await vozApi("/api/gestor/voz/fila", { method: "POST", body: { ids } });
      aviso(vt("colocados", { n: r.colocados }));
      setTimeout(redesenhar, 900);
    } catch (e) { aviso(e.message, true); botao.disabled = false; }
  });
}

function vozBotoesCandidatura(f) {
  const b = [];
  if (f.voz_status !== "ligando") {
    b.push(`<button class="btn small" data-voz-ligar="${f.id}" data-nome="${esc(f.nome)}">${vt("ligar")}</button>`);
    if (f.voz_status !== "para_ligar") b.push(`<button class="btn secondary small" data-voz-acao="fila" data-id="${f.id}">${f.voz_status === "" ? vt("entrarFila") : vt("voltarFila")}</button>`);
    if (f.voz_status !== "nao_ligar") b.push(`<button class="btn ghost small" data-voz-acao="nao_ligar" data-id="${f.id}">${vt("naoLigar")}</button>`);
    if (f.voz_tentativas) b.push(`<button class="btn ghost small" data-voz-acao="zerar" data-id="${f.id}">${vt("zerar")}</button>`);
  }
  return b.join(" ");
}

function vozLigarBotoesCandidatura(el, redesenhar, aviso) {
  el.querySelectorAll("[data-voz-ligar]").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm(vt("confirmaLigar", { nome: b.dataset.nome }))) return;
    b.disabled = true;
    try {
      await vozApi("/api/gestor/voz/candidatura/" + b.dataset.vozLigar + "/ligar", { method: "POST" });
      aviso(vt("ligacaoIniciada"));
      setTimeout(redesenhar, 1200);
    } catch (e) { aviso(e.message, true); b.disabled = false; }
  }));
  el.querySelectorAll("[data-voz-acao]").forEach((b) => b.addEventListener("click", async () => {
    try {
      await vozApi("/api/gestor/voz/candidatura/" + b.dataset.id, { method: "POST", body: { acao: b.dataset.vozAcao } });
      redesenhar();
    } catch (e) { aviso(e.message, true); }
  }));
}

function vozHtmlConfig(r, cfg) {
  return `<div class="card" id="voz-config">
    <h3 style="margin-top:0">${vt("config")}</h3>
    <div class="grid cols-2">
      <label class="field">${vt("idiomaPadrao")}
        <select id="vc-idioma">${["es", "en", "pt"].map((l) => `<option value="${l}" ${cfg.idioma_padrao === l ? "selected" : ""}>${esc(VOZ_TEXTOS[vozIdioma].idiomaLigacao[l])}</option>`).join("")}</select>
      </label>
    </div>
    <p class="hint" style="margin-top:4px">${vt("identidade")}</p>
    <div class="grid cols-2">
      <label class="field">${vt("nomeLigacao")}<input type="text" id="vc-nome" maxlength="120" value="${esc(cfg.nome_ligacao || "")}" placeholder="${esc(r.empresa || "")}"></label>
      <label class="field">${vt("cidadeLigacao")}<input type="text" id="vc-cidade" maxlength="120" value="${esc(cfg.cidade || "")}" placeholder="Hartford"></label>
      <label class="field">${vt("telefoneRetorno")}<input type="text" id="vc-telefone" maxlength="40" value="${esc(cfg.telefone_retorno || "")}" placeholder="860-790-9545"></label>
      <label class="field">${vt("gerente")}<input type="text" id="vc-gerente" maxlength="80" value="${esc(cfg.gerente || "")}" placeholder="Carine"></label>
    </div>
    <label class="field" style="flex-direction:row;align-items:center;gap:8px"><input type="checkbox" id="vc-ativo" ${cfg.ativo ? "checked" : ""}> ${vt("cAtivo")}</label>
    <label class="field" style="flex-direction:row;align-items:center;gap:8px"><input type="checkbox" id="vc-pausado" ${cfg.pausado ? "checked" : ""}> ${vt("cPausado")}</label>
    <div class="grid cols-3">
      <label class="field">${vt("fuso")}
        <select id="vc-fuso">${["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Sao_Paulo"].map((z) => `<option ${cfg.fuso === z ? "selected" : ""}>${z}</option>`).join("")}</select>
      </label>
      <label class="field">${vt("inicio")}<input type="time" id="vc-inicio" value="${esc(cfg.inicio)}" style="display:block;width:100%"></label>
      <label class="field">${vt("fim")}<input type="time" id="vc-fim" value="${esc(cfg.fim)}" style="display:block;width:100%"></label>
    </div>
    <p class="hint">${vt("dias")}</p>
    <div class="linha-acoes" id="vc-dias">${VOZ_TEXTOS[vozIdioma].diasSemana.map((d, i) => `
      <label class="badge ${cfg.dias.includes(i + 1) ? "ok" : ""}" style="cursor:pointer"><input type="checkbox" value="${i + 1}" ${cfg.dias.includes(i + 1) ? "checked" : ""} style="display:none">${d}</label>`).join("")}</div>
    <div class="grid cols-3">
      <label class="field">${vt("maxTentativas")}<input type="number" id="vc-max" min="1" max="10" value="${cfg.max_tentativas}"></label>
      <label class="field">${vt("simultaneas")}<input type="number" id="vc-sim" min="1" max="5" value="${cfg.simultaneas}"></label>
      <label class="field">${vt("intervalo")}<input type="number" id="vc-int" min="1" max="72" value="${cfg.intervalo_horas}"></label>
    </div>
    ${vozHtmlVozes(r, cfg)}
    <div class="form-erro" id="vc-erro"></div>
    <button class="btn" id="vc-salvar">${vt("salvar")}</button> <span class="desc" id="vc-ok" style="margin:0"></span>
  </div>`;
}

/** Voz da Francisca por idioma (lista curada no servidor, voz.VOZES) com amostra. */
function vozHtmlVozes(r, cfg) {
  const vozes = r.vozes || {};
  return `<h4 style="margin:16px 0 2px">${vt("vozTitulo")}</h4>
    <p class="hint" style="margin-top:0">${vt("vozDesc")}</p>
    <div class="grid cols-3">${["es", "en", "pt"].map((l) => {
      const lista = vozes[l] || [];
      const atual = cfg["voz_" + l] || (lista.find((v) => v.padrao) || {}).id || "";
      return `<label class="field">${esc(VOZ_TEXTOS[vozIdioma].idiomaLigacao[l])}
        <select id="vc-voz-${l}">${lista.map((v) => `<option value="${esc(v.id)}" ${v.id === atual ? "selected" : ""}>${esc(v.nome)}${v.padrao ? " (" + vt("vozPadrao") + ")" : ""} · ${esc((v.descricao || {})[vozIdioma] || "")}</option>`).join("")}</select>
        <button type="button" class="btn ghost small" data-voz-amostra="${l}" style="margin-top:6px;align-self:flex-start">${vt("ouvir")}</button>
      </label>`;
    }).join("")}</div>`;
}

let vozAudioAmostra = null;

function vozLigarVozes(el, r) {
  el.querySelectorAll("[data-voz-amostra]").forEach((b) => b.addEventListener("click", () => {
    const l = b.dataset.vozAmostra;
    const id = el.querySelector("#vc-voz-" + l).value;
    const voz = ((r.vozes || {})[l] || []).find((v) => v.id === id);
    const tocando = vozAudioAmostra && !vozAudioAmostra.paused && vozAudioAmostra.dataset.botao === l;
    if (vozAudioAmostra) vozAudioAmostra.pause();
    el.querySelectorAll("[data-voz-amostra]").forEach((x) => { x.textContent = vt("ouvir"); });
    if (tocando || !voz || !voz.preview_url) return;
    vozAudioAmostra = new Audio(voz.preview_url);
    vozAudioAmostra.dataset.botao = l;
    vozAudioAmostra.addEventListener("ended", () => { b.textContent = vt("ouvir"); });
    vozAudioAmostra.play().then(() => { b.textContent = vt("parar"); }).catch(() => { b.textContent = vt("ouvir"); });
  }));
}

function vozLigarConfig(el, r, redesenhar) {
  const q = (s) => el.querySelector(s);
  vozLigarVozes(el, r);
  q("#vc-dias").querySelectorAll("label").forEach((lab) => lab.addEventListener("click", (ev) => {
    ev.preventDefault();
    const cb = lab.querySelector("input");
    cb.checked = !cb.checked;
    lab.classList.toggle("ok", cb.checked);
  }));
  q("#vc-salvar").addEventListener("click", async () => {
    q("#vc-erro").textContent = "";
    const dias = [...q("#vc-dias").querySelectorAll("input:checked")].map((i) => Number(i.value));
    try {
      await vozApi("/api/gestor/voz/config", { method: "POST", body: { config: {
        ativo: q("#vc-ativo").checked, pausado: q("#vc-pausado").checked, fuso: q("#vc-fuso").value,
        inicio: q("#vc-inicio").value, fim: q("#vc-fim").value, dias,
        max_tentativas: Number(q("#vc-max").value), simultaneas: Number(q("#vc-sim").value),
        intervalo_horas: Number(q("#vc-int").value), idioma_padrao: q("#vc-idioma").value,
        nome_ligacao: q("#vc-nome").value, cidade: q("#vc-cidade").value,
        telefone_retorno: q("#vc-telefone").value, gerente: q("#vc-gerente").value,
        voz_es: q("#vc-voz-es").value, voz_en: q("#vc-voz-en").value, voz_pt: q("#vc-voz-pt").value,
      } } });
      q("#vc-ok").textContent = vt("salvo");
      setTimeout(redesenhar, 700);
    } catch (e) { q("#vc-erro").textContent = e.message; }
  });
}

function vozHtmlCargos(r) {
  return `<div class="card">
    <h3 style="margin-top:0">${vt("cargos")}</h3>
    <p class="desc">${vt("cargosDesc")}</p>
    <div class="tabela-wrap"><table class="tabela"><tbody>${r.cargos.map((c) => `
      <tr><td><label style="display:flex;gap:8px;align-items:center"><input type="checkbox" data-voz-cargo="${c.id}" ${c.voz_ativa ? "checked" : ""}> ${esc(c.nome)}</label>
        ${c.voz_ativa ? vozSeloRevisao(c.revisado_em) : ""}</td>
        <td class="num">${vt("peso")} <input type="number" min="0" max="80" step="5" style="width:70px" data-voz-peso="${c.id}" value="${Math.round((c.peso_voz || 0) * 100)}">%</td>
        <td class="num"><button class="btn secondary small" data-voz-roteiro="${c.id}" data-nome="${esc(c.nome)}">${vt("roteiro")}</button></td></tr>`).join("")}
    </tbody></table></div></div>`;
}

function vozDiasDesde(data) {
  if (!data) return null;
  return Math.floor((Date.now() - new Date(data + "T12:00:00Z").getTime()) / 86400000);
}

function vozSeloRevisao(data) {
  const dias = vozDiasDesde(data);
  if (dias === null) return `<div><span class="badge warn">${vt("nuncaRevisado")}</span></div>`;
  if (dias > 60) return `<div><span class="badge warn">${vt("revisarFatos")}</span></div>`;
  return `<div class="hint">${vt("revisadoHa", { n: Math.max(0, dias) })}</div>`;
}

function vozLigarCargos(el, redesenhar) {
  const salvar = async (id) => {
    const ativa = el.querySelector(`[data-voz-cargo="${id}"]`).checked;
    const peso = Number(el.querySelector(`[data-voz-peso="${id}"]`).value) / 100;
    try { await vozApi("/api/gestor/voz/cargo/" + id, { method: "POST", body: { voz_ativa: ativa, peso_voz: peso } }); }
    catch (e) { alert(e.message); redesenhar(); }
  };
  el.querySelectorAll("[data-voz-cargo]").forEach((cb) => cb.addEventListener("change", () => salvar(cb.dataset.vozCargo)));
  el.querySelectorAll("[data-voz-peso]").forEach((inp) => inp.addEventListener("change", () => salvar(inp.dataset.vozPeso)));
  el.querySelectorAll("[data-voz-roteiro]").forEach((b) => b.addEventListener("click", () =>
    vozEditarRoteiro(Number(b.dataset.vozRoteiro), b.dataset.nome)));
}


// ------------------------------------------------ editor do roteiro (por cargo)
async function vozEditarRoteiro(cargoId, nomeCargo) {
  let r;
  try { r = await vozApi("/api/gestor/voz/cargo/" + cargoId + "/roteiro"); } catch (e) { alert(e.message); return; }
  const rot = r.roteiro;
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  const linhaFaq = (f) => `<div class="sub-card voz-faq" style="margin-top:8px">
      <label class="field">${vt("faqPergunta")}<input type="text" class="vf-p" maxlength="600" value="${esc(f.pergunta || "")}"></label>
      <label class="field">${vt("faqResposta")}<textarea class="vf-r" rows="2" maxlength="1200">${esc(f.resposta || "")}</textarea></label>
      <button class="btn ghost small vf-rem">${vt("remover")}</button></div>`;
  const linhaPergunta = (p) => `<div class="linha-acoes voz-perg" style="margin-top:6px">
      <input type="text" class="vp-t" maxlength="600" value="${esc(p || "")}" style="flex:1;margin:0">
      <button class="btn ghost small vp-rem">${vt("remover")}</button></div>`;
  fundo.innerHTML = `<div class="modal">
    <button class="btn ghost small fechar" id="vr-fechar">${vt("fechar")}</button>
    <h2 style="margin-top:0">${esc(vt("roteiroTitulo", { cargo: nomeCargo }))}</h2>
    <p class="desc">${vt("roteiroDesc")}</p>
    ${rot.revisado_em ? `<p class="hint">${esc(vt("ultimaRevisao", { d: rot.revisado_em, p: rot.revisado_por || "" }))}</p>` : ""}
    ${vozDiasDesde(rot.revisado_em) === null || vozDiasDesde(rot.revisado_em) > 60 ? `<p class="form-erro" style="color:var(--warn, #b7791f)">${vt("avisoRevisao")}</p>` : ""}
    <label class="field">${vt("fatosVaga")}<textarea id="vr-fatos" rows="7" maxlength="${r.limites.fatos}">${esc(rot.fatos || "")}</textarea></label>
    <h3>${vt("requisitos")}</h3>
    <div class="linha-acoes">
      <label><input type="checkbox" id="vr-carteira" ${rot.exige_carteira ? "checked" : ""}> ${vt("exigeCarteira")}</label>
      <label><input type="checkbox" id="vr-carro" ${rot.exige_carro ? "checked" : ""}> ${vt("exigeCarro")}</label>
      <label><input type="checkbox" id="vr-smart" ${rot.exige_smartphone ? "checked" : ""}> ${vt("exigeSmartphone")}</label>
    </div>
    <h3>${vt("perguntasExtras")}</h3>
    <div id="vr-perguntas">${(rot.perguntas || []).map(linhaPergunta).join("")}</div>
    <button class="btn secondary small" id="vr-add-perg" style="margin-top:6px">${vt("addPergunta")}</button>
    <h3>${vt("faqs")}</h3>
    <div id="vr-faqs">${(rot.faqs || []).map(linhaFaq).join("")}</div>
    <button class="btn secondary small" id="vr-add-faq" style="margin-top:6px">${vt("addFaq")}</button>
    <div class="grid cols-2" style="margin-top:12px">
      <label class="field">${vt("area25")}<textarea id="vr-a25" rows="5">${esc((rot.cidades_25 || []).join("\n"))}</textarea></label>
      <label class="field">${vt("area40")}<textarea id="vr-a40" rows="5">${esc((rot.cidades_40 || []).join("\n"))}</textarea></label>
    </div>
    <p class="hint">${vt("areaDica")}</p>
    <p class="form-erro" id="vr-erro"></p>
    <button class="btn" id="vr-salvar">${vt("salvar")}</button>
    <button class="btn secondary" id="vr-simular">${vt("simular")}</button>
    <span class="desc" id="vr-ok" style="margin:0"></span>
  </div>`;
  document.body.appendChild(fundo);
  const q = (sel) => fundo.querySelector(sel);
  const ligarRemover = () => {
    fundo.querySelectorAll(".vf-rem").forEach((b) => { b.onclick = () => b.closest(".voz-faq").remove(); });
    fundo.querySelectorAll(".vp-rem").forEach((b) => { b.onclick = () => b.closest(".voz-perg").remove(); });
  };
  ligarRemover();
  q("#vr-fechar").addEventListener("click", () => fundo.remove());
  q("#vr-simular").addEventListener("click", () => vozSimular(cargoId, nomeCargo));
  q("#vr-add-faq").addEventListener("click", () => {
    q("#vr-faqs").insertAdjacentHTML("beforeend", linhaFaq({}));
    ligarRemover();
  });
  q("#vr-add-perg").addEventListener("click", () => {
    if (fundo.querySelectorAll(".voz-perg").length >= r.limites.perguntas) return;
    q("#vr-perguntas").insertAdjacentHTML("beforeend", linhaPergunta(""));
    ligarRemover();
  });
  q("#vr-salvar").addEventListener("click", async () => {
    q("#vr-erro").textContent = "";
    const linhas = (id) => q(id).value.split("\n").map((x) => x.trim()).filter(Boolean);
    const corpo = {
      fatos: q("#vr-fatos").value,
      exige_carteira: q("#vr-carteira").checked, exige_carro: q("#vr-carro").checked, exige_smartphone: q("#vr-smart").checked,
      perguntas: [...fundo.querySelectorAll(".vp-t")].map((i) => i.value.trim()).filter(Boolean),
      faqs: [...fundo.querySelectorAll(".voz-faq")].map((d) => ({
        pergunta: d.querySelector(".vf-p").value.trim(), resposta: d.querySelector(".vf-r").value.trim(),
      })).filter((f) => f.pergunta && f.resposta),
      cidades_25: linhas("#vr-a25"), cidades_40: linhas("#vr-a40"),
    };
    try {
      await vozApi("/api/gestor/voz/cargo/" + cargoId + "/roteiro", { method: "POST", body: corpo });
      q("#vr-ok").textContent = vt("salvo");
    } catch (e) { q("#vr-erro").textContent = e.message; }
  });
}

// ------------------------------------------------ bloco na ficha do candidato
async function vozPreencherFicha(candidatoId, alvo) {
  if (!alvo) return;
  let r;
  try { r = await vozApi("/api/gestor/voz/candidato/" + candidatoId); } catch (e) { alvo.remove(); return; }
  if (!r.candidaturas.length && !r.chamadas.length) { alvo.remove(); return; }
  const desenhar = () => {
    alvo.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        ${tituloIcone("usuarios", vt("ficha"))}
        ${vozSeletorIdioma()}
      </div>
      ${r.candidaturas.map(vozHtmlCandidaturaFicha).join("")}
      ${r.chamadas.map(vozHtmlChamadaFicha).join("")}
      <p class="form-erro" id="vf-erro"></p>`;
    vozLigarSeletor(alvo, desenhar);
    vozLigarBotoesCandidatura(alvo, () => vozPreencherFicha(candidatoId, alvo), (msg, erro) => {
      alvo.querySelector("#vf-erro").textContent = msg;
      alvo.querySelector("#vf-erro").style.color = erro ? "" : "var(--text-2)";
    });
    alvo.querySelectorAll("[data-voz-transcricao]").forEach((b) => b.addEventListener("click", () => {
      const box = alvo.querySelector("#vt-" + b.dataset.vozTranscricao);
      box.hidden = !box.hidden;
      b.textContent = box.hidden ? vt("transcricao") : vt("esconder");
    }));
    alvo.querySelectorAll("[data-voz-audio]").forEach((b) => b.addEventListener("click", async () => {
      b.disabled = true;
      b.textContent = vt("carregando");
      try {
        const resp = await fetch("/api/gestor/voz/chamada/" + b.dataset.vozAudio + "/audio", {
          headers: { "X-Gestor-Token": localStorage.getItem("gestor_token") || "" },
        });
        if (!resp.ok) throw new Error(VOZ_ERROS[vozIdioma].start_failed);
        const url = URL.createObjectURL(await resp.blob());
        const player = document.createElement("audio");
        player.controls = true;
        player.src = url;
        player.style.width = "100%";
        b.replaceWith(player);
        player.play().catch(() => {});
      } catch (e) { b.textContent = e.message; }
    }));
  };
  desenhar();
}

function vozHtmlCandidaturaFicha(f) {
  const res = f.voz_resultado;
  const pontos = res && res.pontos ? Object.entries(VOZ_PONTOS[vozIdioma]).map(([k, [rot, max]]) => `
    <div class="perfil-barra">
      <div class="rotulo">${esc(rot)}</div>
      <div class="trilha"><div class="valor" style="width:${Math.round(100 * (res.pontos[k] || 0) / max)}%;background:var(--accent-grad)"></div></div>
      <div class="num">${res.pontos[k] || 0}/${max}</div>
    </div>`).join("") : "";
  const motivos = res && res.motivos && res.motivos.length ? `
    <div class="sub-card"><strong>${vt("motivos")}</strong><ul class="lista-simples">${res.motivos.map((m) => {
      const [cod, item] = m.split(":");
      const txt = item ? VOZ_MOTIVOS[vozIdioma].missing.replace("{i}", (VOZ_PONTOS[vozIdioma][item] || [item])[0]) : (VOZ_MOTIVOS[vozIdioma][cod] || m);
      return `<li>${esc(txt)}</li>`;
    }).join("")}</ul></div>` : "";
  const fatos = res && res.fatos ? `
    <h3>${vt("respostas")}</h3>
    <div class="grid cols-2">${Object.entries(VOZ_FATOS[vozIdioma]).filter(([k]) => res.fatos[k] != null && res.fatos[k] !== "").map(([k, rot]) => {
      const v = res.fatos[k];
      const txt = VOZ_VALORES[vozIdioma][String(v)] || String(v);
      return `<div><div class="hint">${esc(rot)}</div><div>${esc(txt)}</div></div>`;
    }).join("")}</div>` : "";
  return `<div class="sub-card" style="margin-top:12px">
    <div class="linha-acoes">
      <strong>${esc(f.vaga)}</strong> ${vozBadgeStatus(f.voz_status)} ${vozBadgeTier(f.voz_tier, f.voz_score)}
      ${f.convite_enviado ? `<span class="badge ok">${vt("convite")}</span>` : ""}
      <span class="hint">${vt("col").tentativas}: ${f.voz_tentativas || 0}</span>
    </div>
    <div class="linha-acoes no-print" style="margin-top:8px">${vozBotoesCandidatura(f)}</div>
    ${pontos ? `<div class="perfil-barras" style="margin-top:10px">${pontos}</div>` : ""}
    ${motivos}
    ${fatos}
  </div>`;
}

function vozHtmlChamadaFicha(c) {
  const res = c.resultado;
  const quem = c.disparada_por === "fila" ? vt("fila_auto") : c.disparada_por === "entrada" ? vt("candidato") : c.disparada_por;
  const desfecho = res ? (VOZ_OUTCOME[vozIdioma][res.outcome] || res.outcome)
    : c.direcao === "entrada" && c.status === "concluida" && !c.erro ? vt("atendidaEntrada")
    : (c.status === "concluida" || c.status === "falhou" ? VOZ_OUTCOME[vozIdioma].NO_ANSWER : VOZ_STATUS[vozIdioma].ligando);
  const t = (s) => String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
  return `<div class="timeline-item" style="margin-top:12px">
    <div class="linha-acoes">
      <strong>${esc(vozData(c.iniciada_em))}</strong>${c.direcao === "entrada" ? ` <span class="badge info">${vt("entrada")}</span>` : ""}
      <span>${esc(desfecho)}</span> ${res ? vozBadgeTier(res.tier, res.score) : ""}
      ${c.duracao != null ? `<span class="hint">${t(c.duracao)}</span>` : ""}
      <span class="hint">${esc(VOZ_TEXTOS[vozIdioma].idiomaLigacao[c.idioma] || c.idioma)} · ${esc(vt("por", { q: quem }))}</span>
    </div>
    ${c.resumo ? `<p class="desc"><strong>${vt("resumo")}:</strong> ${esc(c.resumo)}</p>` : ""}
    <div class="linha-acoes no-print">
      ${c.tem_audio ? `<button class="btn secondary small" data-voz-audio="${c.id}">${vt("gravacao")}</button>` : ""}
      ${(c.transcricao || []).length ? `<button class="btn ghost small" data-voz-transcricao="${c.id}">${vt("transcricao")}</button>` : ""}
    </div>
    <div id="vt-${c.id}" hidden class="sub-card" style="max-height:420px;overflow:auto">
      ${(c.transcricao || []).map((l) => `<p style="margin:4px 0"><span class="hint">${t(l.t)}</span>
        <strong>${l.papel === "agent" ? vt("francisca") : vt("candidato")}:</strong> ${esc(l.texto)}</p>`).join("")}
    </div>
  </div>`;
}


// ------------------------------------------------ simulação pelo navegador
let vozSessaoSimulacao = null;

async function vozSimular(cargoId, nomeCargo) {
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `<div class="modal" style="max-width:620px">
    <button class="btn ghost small fechar" id="vs-fechar">${vt("fechar")}</button>
    <h2 style="margin-top:0">${esc(vt("simTitulo", { cargo: nomeCargo }))}</h2>
    <p class="desc">${vt("simDesc")}</p>
    <label class="field" style="max-width:240px">${vt("simIdioma")}
      <select id="vs-idioma">${["es", "en", "pt"].map((l) => `<option value="${l}" ${l === "es" ? "selected" : ""}>${esc(VOZ_TEXTOS[vozIdioma].idiomaLigacao[l] || l)}</option>`).join("")}</select></label>
    <div class="linha-acoes">
      <button class="btn" id="vs-iniciar">${vt("simIniciar")}</button>
      <button class="btn secondary" id="vs-encerrar" disabled>${vt("simEncerrar")}</button>
      <span class="badge" id="vs-estado"></span>
    </div>
    <p class="form-erro" id="vs-erro"></p>
    <div id="vs-conversa" style="max-height:320px;overflow:auto;margin-top:10px"></div>
  </div>`;
  document.body.appendChild(fundo);
  const q = (s) => fundo.querySelector(s);
  const estado = (t) => { q("#vs-estado").textContent = t; };
  const fala = (quem, texto) => {
    const d = document.createElement("div");
    d.className = "sub-card";
    d.style.margin = "6px 0";
    d.innerHTML = `<strong>${esc(quem)}:</strong> ${esc(texto)}`;
    q("#vs-conversa").appendChild(d);
    q("#vs-conversa").scrollTop = 1e6;
  };
  const encerrar = async () => {
    if (vozSessaoSimulacao) { try { await vozSessaoSimulacao.endSession(); } catch (e) { /* já encerrada */ } }
    vozSessaoSimulacao = null;
  };
  q("#vs-fechar").addEventListener("click", async () => { await encerrar(); fundo.remove(); });
  q("#vs-encerrar").addEventListener("click", encerrar);
  q("#vs-iniciar").addEventListener("click", async () => {
    q("#vs-erro").textContent = "";
    q("#vs-iniciar").disabled = true;
    estado(vt("simConectando"));
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      q("#vs-erro").textContent = vt("simMic");
      q("#vs-iniciar").disabled = false;
      estado("");
      return;
    }
    try {
      const r = await vozApi("/api/gestor/voz/cargo/" + cargoId + "/simular", { method: "POST", body: { idioma: q("#vs-idioma").value } });
      const sdk = await import("https://cdn.jsdelivr.net/npm/@elevenlabs/client@1.26.0/+esm");
      vozSessaoSimulacao = await sdk.Conversation.startSession({
        signedUrl: r.signed_url,
        dynamicVariables: r.dynamic_variables,
        overrides: Object.assign({ agent: { language: r.language, firstMessage: r.first_message } },
          r.voice_id ? { tts: { voiceId: r.voice_id } } : {}),
        onConnect: () => { q("#vs-encerrar").disabled = false; estado(vt("simOuvindo")); },
        onDisconnect: () => { estado(vt("simEncerrada")); q("#vs-iniciar").disabled = false; q("#vs-encerrar").disabled = true; vozSessaoSimulacao = null; },
        onModeChange: (m) => estado(m && m.mode === "speaking" ? vt("simFalando") : vt("simOuvindo")),
        onMessage: (m) => { if (m && m.message) fala(m.source === "user" ? vt("simVoce") : "Francisca", m.message); },
        onError: (e) => { q("#vs-erro").textContent = String((e && e.message) || e); },
      });
    } catch (e) {
      q("#vs-erro").textContent = e.message || String(e);
      q("#vs-iniciar").disabled = false;
      estado("");
    }
  });
}
