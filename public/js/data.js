/* =====================================================================
   Dados dos testes: DISC (24 blocos) e B.A.S.E. (6 rodadas de cartas)
   ===================================================================== */

// ---------------------------------------------------------- DISC
// Em cada bloco o candidato escolhe a palavra que MAIS se parece com ele
// e a que MENOS se parece. Cada palavra pontua em uma dimensão D, I, S ou C.
const DISC_BLOCOS = [
  [{ t: "Decidido", d: "D" }, { t: "Comunicativo", d: "I" }, { t: "Paciente", d: "S" }, { t: "Detalhista", d: "C" }],
  [{ t: "Competitivo", d: "D" }, { t: "Entusiasmado", d: "I" }, { t: "Leal", d: "S" }, { t: "Analítico", d: "C" }],
  [{ t: "Direto", d: "D" }, { t: "Sociável", d: "I" }, { t: "Calmo", d: "S" }, { t: "Preciso", d: "C" }],
  [{ t: "Ousado", d: "D" }, { t: "Otimista", d: "I" }, { t: "Constante", d: "S" }, { t: "Cauteloso", d: "C" }],
  [{ t: "Determinado", d: "D" }, { t: "Persuasivo", d: "I" }, { t: "Bom ouvinte", d: "S" }, { t: "Organizado", d: "C" }],
  [{ t: "Enérgico", d: "D" }, { t: "Inspirador", d: "I" }, { t: "Conciliador", d: "S" }, { t: "Metódico", d: "C" }],
  [{ t: "Focado em resultados", d: "D" }, { t: "Expressivo", d: "I" }, { t: "Cooperativo", d: "S" }, { t: "Perfeccionista", d: "C" }],
  [{ t: "Assume riscos", d: "D" }, { t: "Espontâneo", d: "I" }, { t: "Previsível", d: "S" }, { t: "Sistemático", d: "C" }],
  [{ t: "Autoconfiante", d: "D" }, { t: "Carismático", d: "I" }, { t: "Acolhedor", d: "S" }, { t: "Criterioso", d: "C" }],
  [{ t: "Firme", d: "D" }, { t: "Divertido", d: "I" }, { t: "Tolerante", d: "S" }, { t: "Disciplinado", d: "C" }],
  [{ t: "Independente", d: "D" }, { t: "Popular", d: "I" }, { t: "Prestativo", d: "S" }, { t: "Lógico", d: "C" }],
  [{ t: "Ambicioso", d: "D" }, { t: "Convincente", d: "I" }, { t: "Estável", d: "S" }, { t: "Rigoroso", d: "C" }],
  [{ t: "Objetivo", d: "D" }, { t: "Animado", d: "I" }, { t: "Harmonioso", d: "S" }, { t: "Exato", d: "C" }],
  [{ t: "Corajoso", d: "D" }, { t: "Extrovertido", d: "I" }, { t: "Sereno", d: "S" }, { t: "Reservado", d: "C" }],
  [{ t: "Exigente", d: "D" }, { t: "Encantador", d: "I" }, { t: "Gentil", d: "S" }, { t: "Racional", d: "C" }],
  [{ t: "Rápido nas decisões", d: "D" }, { t: "Falante", d: "I" }, { t: "Ponderado", d: "S" }, { t: "Cuidadoso", d: "C" }],
  [{ t: "Assertivo", d: "D" }, { t: "Envolvente", d: "I" }, { t: "Discreto", d: "S" }, { t: "Formal", d: "C" }],
  [{ t: "Pioneiro", d: "D" }, { t: "Contagiante", d: "I" }, { t: "Fiel", d: "S" }, { t: "Meticuloso", d: "C" }],
  [{ t: "Vigoroso", d: "D" }, { t: "Descontraído", d: "I" }, { t: "Amável", d: "S" }, { t: "Prudente", d: "C" }],
  [{ t: "Dominante", d: "D" }, { t: "Influente", d: "I" }, { t: "Solidário", d: "S" }, { t: "Estruturado", d: "C" }],
  [{ t: "Prático", d: "D" }, { t: "Criativo ao se expressar", d: "I" }, { t: "Pacificador", d: "S" }, { t: "Investigativo", d: "C" }],
  [{ t: "Impaciente por resultados", d: "D" }, { t: "Busca reconhecimento", d: "I" }, { t: "Evita conflitos", d: "S" }, { t: "Teme cometer erros", d: "C" }],
  [{ t: "Gosta de desafios", d: "D" }, { t: "Gosta de pessoas", d: "I" }, { t: "Gosta de rotina estável", d: "S" }, { t: "Gosta de regras claras", d: "C" }],
  [{ t: "Toma a frente", d: "D" }, { t: "Motiva o grupo", d: "I" }, { t: "Apoia o grupo", d: "S" }, { t: "Garante a qualidade", d: "C" }],
];

const DISC_PERFIS = {
  D: {
    nome: "Dominância",
    cor: "var(--d-color)",
    resumo: "Perfil orientado a resultados, desafios e decisões rápidas. Pessoas com alta Dominância são diretas, competitivas e assumem o controle das situações.",
    fortes: ["Foco em resultados e metas", "Rapidez na tomada de decisão", "Iniciativa e coragem para assumir riscos", "Capacidade de liderar sob pressão"],
    desenvolvimento: ["Ouvir mais antes de decidir", "Ter paciência com ritmos diferentes do seu", "Suavizar a comunicação em temas sensíveis", "Delegar sem microgerenciar o resultado"],
    trabalho: "Prefere autonomia, metas claras e ambientes desafiadores. Comunica-se de forma direta e objetiva; espera o mesmo dos outros.",
  },
  I: {
    nome: "Influência",
    cor: "var(--i-color)",
    resumo: "Perfil comunicativo, entusiasmado e persuasivo. Pessoas com alta Influência motivam equipes, criam conexões e vendem ideias com facilidade.",
    fortes: ["Comunicação e persuasão", "Otimismo e energia contagiante", "Facilidade para criar relacionamentos", "Criatividade para engajar pessoas"],
    desenvolvimento: ["Atenção a prazos e detalhes", "Concluir o que começa antes de iniciar algo novo", "Ouvir com a mesma intensidade com que fala", "Basear decisões também em dados"],
    trabalho: "Prefere ambientes colaborativos, com espaço para interação e reconhecimento. Comunica-se de forma expressiva e envolvente.",
  },
  S: {
    nome: "Estabilidade",
    cor: "var(--s-color)",
    resumo: "Perfil paciente, leal e colaborativo. Pessoas com alta Estabilidade sustentam o time, mantêm a harmonia e entregam com consistência.",
    fortes: ["Consistência e confiabilidade", "Escuta ativa e empatia", "Trabalho em equipe e cooperação", "Calma em momentos de tensão"],
    desenvolvimento: ["Adaptar-se mais rápido a mudanças", "Expressar discordâncias com mais frequência", "Dizer não quando necessário", "Sair da zona de conforto em novos desafios"],
    trabalho: "Prefere ambientes previsíveis, com relações de confiança e mudanças bem comunicadas. Comunica-se de forma calma e atenciosa.",
  },
  C: {
    nome: "Conformidade",
    cor: "var(--c-color)",
    resumo: "Perfil analítico, preciso e orientado à qualidade. Pessoas com alta Conformidade seguem padrões, analisam dados e garantem excelência técnica.",
    fortes: ["Análise criteriosa e atenção a detalhes", "Qualidade e precisão nas entregas", "Planejamento e organização", "Decisões baseadas em dados e fatos"],
    desenvolvimento: ["Aceitar que 'bom' às vezes basta (perfeccionismo)", "Decidir mesmo sem 100% das informações", "Flexibilizar regras quando o contexto pede", "Comunicar-se de forma mais calorosa"],
    trabalho: "Prefere ambientes estruturados, com processos claros e tempo para análise. Comunica-se de forma precisa e formal.",
  },
};

// ---------------------------------------------------------- B.A.S.E.
// Teste B.A.S.E. original de tonybelleza.com/base: 8 rodadas em que o
// candidato ordena 4 cartas da que MAIS combina com ele para a que MENOS
// combina. Pontuação por posição: 1º = 4, 2º = 3, 3º = 2, 4º = 1.
const BASE_INSTRUCAO = "Clique nas 4 cartas em ordem, da que mais combina com você até a que menos combina";
const BASE_RODADAS = [
  {
    pergunta: "O que mais te impulsiona no trabalho e na vida?",
    cartas: [
      { p: "B", ic: "bussola", t: "Estabilidade", sub: "Segurança e previsibilidade" },
      { p: "A", ic: "raio", t: "Resultado", sub: "Vencer e alcançar metas" },
      { p: "S", ic: "coracao", t: "Conexão", sub: "Relacionamentos verdadeiros" },
      { p: "E", ic: "grafico", t: "Conhecimento", sub: "Aprender e evoluir sempre" },
    ],
  },
  {
    pergunta: "Qual valor você mais preza em um ambiente?",
    cartas: [
      { p: "B", ic: "bussola", t: "Organização", sub: "Tudo no lugar certo" },
      { p: "A", ic: "raio", t: "Liberdade", sub: "Fazer do seu jeito" },
      { p: "S", ic: "coracao", t: "Harmonia", sub: "Paz e colaboração" },
      { p: "E", ic: "grafico", t: "Inovação", sub: "Novas ideias e soluções" },
    ],
  },
  {
    pergunta: "Como você prefere tomar decisões importantes?",
    cartas: [
      { p: "B", ic: "bussola", t: "Planejamento", sub: "Com análise detalhada" },
      { p: "A", ic: "raio", t: "Intuição", sub: "Rápido, baseado em oportunidade" },
      { p: "S", ic: "coracao", t: "Consenso", sub: "Ouvindo todos os envolvidos" },
      { p: "E", ic: "grafico", t: "Dados", sub: "Com evidências e lógica" },
    ],
  },
  {
    pergunta: "O que mais te motiva a agir?",
    cartas: [
      { p: "B", ic: "bussola", t: "Responsabilidade", sub: "Cumprir o que foi prometido" },
      { p: "A", ic: "raio", t: "Competição", sub: "Ser o melhor e superar limites" },
      { p: "S", ic: "coracao", t: "Propósito", sub: "Fazer diferença nas pessoas" },
      { p: "E", ic: "grafico", t: "Estratégia", sub: "Resolver problemas complexos" },
    ],
  },
  {
    pergunta: "Como você prefere se comunicar?",
    cartas: [
      { p: "B", ic: "bussola", t: "Clareza", sub: "Direto ao ponto" },
      { p: "A", ic: "raio", t: "Impacto", sub: "Energético, com entusiasmo" },
      { p: "S", ic: "coracao", t: "Empatia", sub: "Com cuidado e escuta ativa" },
      { p: "E", ic: "grafico", t: "Precisão", sub: "Com informação e detalhes" },
    ],
  },
  {
    pergunta: "O que mais te incomoda em um projeto?",
    cartas: [
      { p: "B", ic: "bussola", t: "Imprevistos", sub: "Falta de planejamento" },
      { p: "A", ic: "raio", t: "Lentidão", sub: "Processos lentos e burocracia" },
      { p: "S", ic: "coracao", t: "Conflito", sub: "Disputas e ambiente hostil" },
      { p: "E", ic: "grafico", t: "Superficialidade", sub: "Falta de profundidade" },
    ],
  },
  {
    pergunta: "Qual é sua maior força pessoal?",
    cartas: [
      { p: "B", ic: "bussola", t: "Disciplina", sub: "Consistência e comprometimento" },
      { p: "A", ic: "raio", t: "Liderança", sub: "Influenciar e mobilizar" },
      { p: "S", ic: "coracao", t: "Cuidado", sub: "Apoiar e desenvolver os outros" },
      { p: "E", ic: "grafico", t: "Visão", sub: "Enxergar além do óbvio" },
    ],
  },
  {
    pergunta: "O que mais te dá satisfação ao final do dia?",
    cartas: [
      { p: "B", ic: "bussola", t: "Cumprimento", sub: "Entregar tudo que planejei" },
      { p: "A", ic: "raio", t: "Conquista", sub: "Ter vencido um desafio" },
      { p: "S", ic: "coracao", t: "Impacto", sub: "Ter ajudado alguém de verdade" },
      { p: "E", ic: "grafico", t: "Aprendizado", sub: "Ter descoberto algo novo" },
    ],
  },
];

// Rótulos das 4 posições do código completo (relatório original)
const BASE_POSICOES = [
  "1ª posição · Seu motor principal",
  "2ª posição · Sua influência secundária",
  "3ª posição · Seu modo sob estresse",
  "4ª posição · Seus valores menos prioritários",
];

const BASE_PERFIS = {
  B: {
    nome: "Bússola",
    titulo: "O Guardião dos Sistemas",
    ic: "bussola",
    cor: "#3B67CA",
    tagline: "Você é a âncora que mantém tudo no lugar. Responsável, detalhista e orientado a processos, sua força está em criar sistemas confiáveis, cumprir compromissos e garantir que cada engrenagem funcione com precisão. Quando você dá sua palavra, ela é lei.",
    resumo: "Pessoas com perfil Bússola colocam a responsabilidade em primeiro lugar. Você vive por um código moral interno forte, respeita regras, tradições e autoridade e espera o mesmo dos outros. Detalhista e orientado a processos, você transforma o caos em ordem com maestria. Sua capacidade de planejar, organizar e executar com disciplina faz de você uma das pessoas mais confiáveis de qualquer equipe. Você prefere analisar cuidadosamente antes de agir, trabalha melhor com prazos definidos e sistemas claros, e se destaca em logística, gestão e implementação. Para você, a consistência não é limitação, é excelência.",
    fortes: ["Organizado e detalhista", "Disciplinado e consistente", "Especialista em planejamento", "Comprometido com entregas", "Implementador eficiente", "Pensamento sequencial", "Confiável e responsável", "Gestão e logística"],
    gatilhos: ["Pessoas profissionais que chegam preparadas e pontuais.", "Ambientes com regras claras e expectativas bem definidas.", "Quem cumpre o que promete, sem exceções e sem desculpas.", "Sistemas organizados, documentação e processos bem estruturados.", "Quem demonstra credenciais, referências e histórico comprovado.", "Planejamentos com etapas claras, prazos realistas e orçamento definido.", "Quem apresenta um plano passo a passo para o sucesso.", "Tradições, métodos testados e respeito à hierarquia.", "Reuniões eficientes com pauta clara e resultados concretos.", "Quem minimiza riscos com fatos e provas verificáveis."],
    repulsores: ["Imprevistos e mudanças de última hora sem justificativa sólida.", "Pessoas desorganizadas que improvisam e não seguem processos.", "Quem promete e não entrega, ou muda os planos sem aviso.", "Ambientes caóticos sem estrutura, sistemas ou responsabilidades definidas.", "Quem desrespeita hierarquias, regras e autoridade estabelecida.", "Decisões impulsivas tomadas sem análise ou dados suficientes.", "Pessoas que não respeitam prazos, compromissos e orçamentos.", "Desperdício de recursos ou falta de planejamento financeiro.", "Quem é excessivamente emocional ou sensível nas decisões.", "Falta de profissionalismo e de atenção aos detalhes."],
    posicoes: [
      "Como Bússola na posição primária, estrutura, responsabilidade e planejamento são o que mais impulsionam suas decisões. Você lidera com organização e confiabilidade.",
      "O Bússola na segunda posição significa que você é muito competente em organização e processos, e usa essas habilidades para apoiar seu perfil primário no dia a dia.",
      "Sob estresse, você tende a recorrer ao modo Bússola, buscando controle, sistemas e planejamento para recuperar a sensação de segurança.",
      "Valores de Bússola como tradição, hierarquia e sistemas rígidos são os menos prioritários para você. Você prefere flexibilidade a regras fixas.",
    ],
    comunicacao: {
      A: ["Demonstre entusiasmo e energia, transmita a oportunidade com confiança.", "Vá direto ao ponto, mostre o resultado e o impacto imediato.", "Pule os detalhes excessivos, foque no estilo de vida e no sonho.", "Apresente influenciadores e pessoas de sucesso do seu networking.", "Transmita senso de urgência: lembre que tempo é dinheiro.", "Seja confiante e tenha autoestima elevada ao apresentar."],
      S: ["Demonstre que você genuinamente se importa com as pessoas além do negócio.", "Compartilhe histórias reais de transformação e impacto humano.", "Construa a relação pessoal antes de falar de negócios ou números.", "Mostre como sua proposta se conecta a valores, propósito e missão.", "Seja autêntico, abra-se sobre sua história pessoal e motivações.", "Pergunte sobre a vida pessoal deles (família, hobbies, paixões)."],
      E: ["Apresente dados, pesquisas e evidências concretas, seja inteligente.", "Dê-lhes tempo para analisar e processar as informações antes de decidir.", "Esteja preparado para debater e defender sua posição com lógica.", "Mantenha-se racional, evite exageros emocionais ou excitação excessiva.", "Forneça documentação, recursos e dados para estudo aprofundado.", "Seja aberto para ouvir o ponto de vista deles e ver o panorama completo."],
    },
  },
  A: {
    nome: "Atuante",
    titulo: "O Realizador Implacável",
    ic: "raio",
    cor: "#E05C2E",
    tagline: "Você não tem medo de arriscar e está sempre em busca da próxima grande oportunidade. Sua energia, confiança e capacidade de ação fazem de você um líder natural que cria momentum onde quer que vá.",
    resumo: "Pessoas com perfil Atuante são movidas por ação, competição e a busca constante por vitórias. Você é o primeiro a se levantar quando surge uma oportunidade e o último a desistir quando o desafio aparece. Não tem medo de assumir riscos e sempre está de olho em maneiras de disruptar e melhorar o status quo. Sua flexibilidade, capacidade de improvisação e habilidade de criar momentum fazem de você uma força da natureza em negociações, vendas e liderança. Você pensa rápido, age mais rápido ainda, e inspira as pessoas ao seu redor com sua autoconfiança e visão de futuro. Se algo grande vai acontecer, você quer ser o protagonista.",
    fortes: ["Orientado a resultados e vitórias", "Decisivo e rápido na ação", "Competitivo e ambicioso", "Liderança natural e carismática", "Criador de momentum", "Resiliente e gestor de crises", "Performático e persuasivo", "Flexível e improvisador"],
    gatilhos: ["Oportunidades de ser o primeiro, o melhor ou o maior.", "Ambientes dinâmicos que valorizam velocidade, ação e resultados.", "Reconhecimento público por conquistas e performance.", "Quem apresenta ideias com energia, entusiasmo e visão de impacto.", "Networking com pessoas influentes, poderosas e bem-sucedidas.", "Desafios que parecem impossíveis para os outros, quanto maior, melhor.", "Imagem, estilo e presença que transmitam sucesso e confiança.", "Liberdade total para agir sem burocracia ou microgerenciamento.", "Diversão, estilo de vida e experiências que alimentem o sonho.", "Senso de urgência e janelas de oportunidade exclusivas."],
    repulsores: ["Processos lentos, burocracia e excesso de planejamento sem ação.", "Reuniões longas sem decisão, resultado claro ou objetivo definido.", "Pessoas que questionam demais, analisam demais e nunca agem.", "Ambientes que limitam a criatividade, iniciativa e autonomia.", "Falta de reconhecimento pelo esforço, conquista e performance.", "Apresentações monótonas, sem energia e sem visão.", "Microgerenciamento que sufoca e tira sua liberdade de ação.", "Excesso de detalhes, dados e histórias quando você quer a conclusão.", "Pessoas medrosas que recusam arriscar ou tomar decisões.", "Quem não tem autoestima ou confiança no que apresenta."],
    posicoes: [
      "Como Atuante na posição primária, ação, competição e resultados são o combustível das suas decisões. Você lidera com energia e visão de conquista.",
      "O Atuante na segunda posição adiciona dinamismo e velocidade ao seu perfil principal. Você sabe quando é hora de agir e criar momentum.",
      "Sob estresse, você ativa o modo Atuante, buscando ação imediata, tomando decisões rápidas e assumindo o controle da situação.",
      "Valores de Atuante como competição, risco e decisões impulsivas são os menos importantes para você. Você prefere considerar antes de agir.",
    ],
    comunicacao: {
      B: ["Seja organizado, profissional e apresente um plano passo a passo claro.", "Chegue 15 a 30 minutos adiantado, pontualidade é respeito.", "Forneça fatos, provas, referências e credenciais verificáveis.", "Minimize os riscos envolvidos com dados e sistemas comprovados.", "Não seja excessivamente emocional ou sensível, mostre o sistema.", "Respeite o orçamento e mantenha-se dentro dos limites acordados."],
      S: ["Construa genuinamente a relação humana antes de qualquer oferta.", "Mostre empatia e interesse real pela história pessoal deles.", "Conecte sua proposta a um impacto social maior e propósito.", "Seja autêntico e transparente, evite parecer vendedor ou artificial.", "Compartilhe histórias reais de transformação de vidas e impacto.", "Apresente-os a membros da sua equipe e crie senso de comunidade."],
      E: ["Apresente lógica sólida, dados concretos e raciocínio fundamentado.", "Dê espaço e tempo para análise, nunca force decisões rápidas.", "Esteja preparado para discussões técnicas e debates aprofundados.", "Forneça evidências e permita que eles questionem livremente.", "Mantenha-se racional e aberto para ver o panorama completo.", "Vista-se bem e demonstre sofisticação intelectual."],
    },
  },
  S: {
    nome: "Sensível",
    titulo: "O Construtor de Pontes",
    ic: "coracao",
    cor: "#2EA87B",
    tagline: "Você coloca as pessoas em primeiro lugar. Sua presença ilumina qualquer ambiente, cria comunidade onde não existia e desperta o potencial que os outros nem sabiam que tinham. Conexões genuínas são sua superpotência.",
    resumo: "Pessoas com perfil Sensível são guiadas por empatia, autenticidade e o desejo profundo de impactar positivamente os seres humanos ao seu redor. Você é amigável, acolhedor e tem uma disposição aberta que faz todos se sentirem parte da comunidade. Relacionamentos são a sua prioridade, você sempre busca conexão genuína e profunda. Empoderar pessoas a serem o melhor de si mesmas é o que te move. Enquanto negócios são importantes, você sabe que há mais na vida do que dinheiro, e busca constantemente um significado mais profundo. Você evita competição excessiva e conflito, preferindo encorajar equipes a se fortalecerem mutuamente. Ninguém é tão habilidoso quanto você em resolver problemas diplomaticamente e em despertar potencial adormecido nas pessoas.",
    fortes: ["Empático e acolhedor", "Movido por propósito e significado", "Despertar de potencial nos outros", "Diplomata e criador de harmonia", "Autêntico e genuíno sempre", "Coaching e mentoria natural", "Intuitivo com necessidades alheias", "Orientado a impacto humano"],
    gatilhos: ["Quem participa de causas sociais e comunitárias além da profissão.", "Pessoas apaixonadas pelo que fazem com propósito claro e verdadeiro.", "Quem cria senso de comunidade e pertencimento genuíno.", "Energia calorosa, amigável e genuinamente humana.", "Quem vai além para demonstrar cuidado, gratidão e reconhecimento.", "Conexão por histórias em comum, interesses compartilhados e experiências.", "Quem busca entender cada pessoa como indivíduo único.", "Quem apresenta sua equipe e inclui você na comunidade.", "Perguntas sobre sua história pessoal, família, hobbies e paixões.", "Pessoas acessíveis, simpáticas e que tratam todos com igualdade."],
    repulsores: ["Pessoas que parecem se importar mais com dinheiro do que com gente.", "Ambientes de competição excessiva, agressividade e frieza emocional.", "Quem se apresenta de forma inautêntica ou artificial.", "Pessoas rudes, mal-educadas ou que faltam com gentileza básica.", "Quem não tenta entender os outros como indivíduos únicos.", "Quem não compartilha histórias e experiências de clientes e pessoas.", "Pessoas que esquecem detalhes pessoais importantes (aniversário, família).", "Falta de integridade moral e padrões éticos elevados.", "Quem não compartilha seu coração, propósito ou razão de existir.", "Pessoas egocêntricas que faltam com humildade e empatia."],
    posicoes: [
      "Como Sensível na posição primária, pessoas, conexão e propósito humano guiam todas as suas escolhas. Você lidera com empatia e autenticidade.",
      "O Sensível na segunda posição enriquece seu perfil com inteligência emocional e capacidade de criar conexões genuínas em qualquer contexto.",
      "Sob estresse, você recorre ao modo Sensível, buscando apoio emocional, harmonia e reconexão com as pessoas ao seu redor.",
      "Valores de Sensível como harmonia a todo custo e evitar conflito não são sua prioridade. Você consegue ser mais direto quando necessário.",
    ],
    comunicacao: {
      B: ["Seja organizado, profissional e pontual, chegue preparado.", "Apresente um plano claro com etapas definidas e passo a passo.", "Forneça fatos, provas e referências, minimize os riscos.", "Não seja excessivamente emocional ou sensível nas apresentações.", "Mostre o sistema para o sucesso com dados e credenciais.", "Respeite o orçamento e demonstre responsabilidade financeira."],
      A: ["Demonstre entusiasmo, energia e confiança, vá direto ao ponto.", "Apresente a oportunidade de vitória e vantagem competitiva clara.", "Conecte-os com pessoas influentes e poderosas do seu networking.", "Foque no impacto, no resultado e no estilo de vida, não no processo.", "Transmita urgência genuína: tempo é dinheiro para eles.", "Seja confiante, tenha autoestima elevada e divirta-se."],
      E: ["Apresente dados concretos, raciocínio lógico e evidências sólidas.", "Mantenha a objetividade, evite exageros emocionais ou drama.", "Dê espaço e tempo para análise antes de pedir qualquer decisão.", "Seja preciso na linguagem e forneça documentação para estudo.", "Esteja aberto a debates e disposto a ver o panorama completo.", "Demonstre profundidade intelectual e domínio do assunto."],
    },
  },
  E: {
    nome: "Estudioso",
    titulo: "O Arquiteto de Ideias",
    ic: "grafico",
    cor: "#8B5CF6",
    tagline: "Sua mente é sua maior ferramenta. Você valoriza a razão acima de tudo, toma decisões baseadas em fatos e ciência, nunca em emoção. Enxerga padrões onde os outros veem apenas informação e transforma complexidade em estratégia.",
    resumo: "Pessoas com perfil Estudioso são movidas por lógica, aprendizado contínuo e a busca incessante por soluções inovadoras. Você não se satisfaz com respostas superficiais, quer entender o porquê profundo de cada coisa. Toma decisões com base em fatos e ciência, nunca em emoção, e se destaca em analisar dados, estrategizar para o longo prazo e encontrar erros que os outros perdem. Sua capacidade de pensamento abstrato, visão sistêmica e precisão na linguagem fazem de você uma fonte inesgotável de conhecimento. Você frequentemente aprecia mais o processo de aprender do que agir sobre a informação. Criativo e visionário, você está sempre buscando uma maneira melhor de fazer as coisas e quando encontra, constrói modelos, diagramas e teorias que mudam paradigmas.",
    fortes: ["Analítico e lógico", "Inovador e visionário", "Pensamento sistêmico e abstrato", "Aprendizado perpétuo", "Estrategista de longo prazo", "Precisão na linguagem e pensamento", "Solucionador de problemas complexos", "Criador de modelos e teorias"],
    gatilhos: ["Discussões intelectualmente estimulantes e debates aprofundados.", "Quem apresenta dados sólidos, pesquisas e raciocínio lógico.", "Tecnologia de ponta, inovação e soluções que desafiam o status quo.", "Espaço e tempo para analisar antes de tomar qualquer decisão.", "Quem domina profundamente o assunto que apresenta, expertise real.", "Projetos com complexidade e desafio intelectual genuíno.", "Precisão na linguagem, coerência nas informações e atenção aos detalhes.", "Quem respeita a necessidade de tempo para pensar e processar.", "Recursos, documentação e dados para estudo aprofundado.", "Pessoas refinadas, inteligentes e com postura sofisticada."],
    repulsores: ["Informações superficiais, rasas ou argumentos sem embasamento.", "Quem pede decisão rápida sem dados, análise ou tempo suficiente.", "Exageros emocionais, entusiasmo sem substância e drama desnecessário.", "Ambientes que desvalorizam expertise, conhecimento e profundidade.", "Quem não está aberto a debates, questionamentos e diferentes perspectivas.", "Promessas exageradas sem evidências concretas ou casos verificáveis.", "Reuniões improdutivas sem pauta, objetivo claro ou resultado tangível.", "Excesso de detalhes pessoais, histórias e drama quando você quer lógica.", "Pessoas que não admitem quando não sabem algo, falta de humildade intelectual.", "Quem tenta manipular com emoção em vez de convencer com razão."],
    posicoes: [
      "Como Estudioso na posição primária, lógica, dados e aprendizado contínuo dominam seu processo de decisão. Você lidera com razão e visão estratégica.",
      "O Estudioso na segunda posição traz profundidade analítica e capacidade de visão sistêmica ao seu perfil principal, enriquecendo suas decisões.",
      "Sob estresse, você ativa o modo Estudioso, mergulhando em análise, buscando dados e tentando racionalizar a situação antes de reagir.",
      "Valores de Estudioso como análise excessiva e busca por perfeição intelectual são os menos prioritários. Você prefere agir a analisar indefinidamente.",
    ],
    comunicacao: {
      B: ["Seja organizado, pontual e apresente documentação completa.", "Mostre o sistema, o processo e o passo a passo por trás da proposta.", "Forneça fatos, provas e minimize os riscos com evidências concretas.", "Respeite a necessidade de processo, hierarquia e tradição.", "Apresente referências, credenciais e casos comprovados.", "Mantenha-se dentro do orçamento e demonstre responsabilidade."],
      A: ["Demonstre entusiasmo e energia, transmita a oportunidade com confiança.", "Foque na vitória, no resultado e no estilo de vida, não nos detalhes.", "Vá direto à conclusão, pule conversa fiada e dados excessivos.", "Conecte-os com influenciadores e pessoas de sucesso do networking.", "Crie urgência: apresente a janela de oportunidade com senso de exclusividade.", "Seja confiante, divertido e tenha uma autoestima saudável."],
      S: ["Construa a relação humana com autenticidade e interesse genuíno.", "Compartilhe o propósito, a missão e o impacto humano por trás do negócio.", "Mostre como sua proposta transforma positivamente a vida das pessoas.", "Demonstre que você se importa com eles como seres humanos, não como clientes.", "Use histórias reais de transformação, impacto e mudança de vida como prova.", "Pergunte sobre a família, paixões e história pessoal deles."],
    },
  },
};

// ---------------------------------------------------------- escala da autoavaliação
const ESCALA_NIVEIS = [
  { v: 0, rot: "0 · Não possuo" },
  { v: 1, rot: "1 · Básico" },
  { v: 2, rot: "2 · Em desenvolvimento" },
  { v: 3, rot: "3 · Intermediário" },
  { v: 4, rot: "4 · Avançado" },
  { v: 5, rot: "5 · Especialista" },
];

const TIPOS_COMPETENCIA = {
  tecnica: "Técnica",
  relacional: "Relacional",
  formacao: "Formação / Certificação",
  experiencia: "Experiência",
};
