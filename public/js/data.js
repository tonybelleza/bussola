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
// Formato do teste B.A.S.E. de Tony Belleza: em cada rodada o candidato
// ordena 4 cartas da que MAIS combina com ele para a que MENOS combina.
const BASE_RODADAS = [
  {
    pergunta: "O que mais pesa quando você toma uma decisão importante?",
    cartas: [
      { p: "B", ic: "bussola", t: "Planejamento e segurança", sub: "Analiso o plano, os riscos e as responsabilidades" },
      { p: "A", ic: "raio", t: "Oportunidade e velocidade", sub: "Se a chance é boa, eu ajo antes que ela passe" },
      { p: "S", ic: "coracao", t: "Impacto nas pessoas", sub: "Penso em como a decisão afeta quem está envolvido" },
      { p: "E", ic: "grafico", t: "Dados e lógica", sub: "Busco informações e analiso racionalmente" },
    ],
  },
  {
    pergunta: "No trabalho, você se destaca principalmente por...",
    cartas: [
      { p: "B", ic: "bussola", t: "Organização e responsabilidade", sub: "Cumpro prazos e mantenho tudo sob controle" },
      { p: "A", ic: "raio", t: "Iniciativa e energia", sub: "Faço acontecer e gosto de competir" },
      { p: "S", ic: "coracao", t: "Empatia e colaboração", sub: "Cuido das pessoas e do clima do time" },
      { p: "E", ic: "grafico", t: "Análise e inovação", sub: "Resolvo problemas com lógica e ideias novas" },
    ],
  },
  {
    pergunta: "Um projeto ideal para você tem...",
    cartas: [
      { p: "B", ic: "bussola", t: "Etapas claras e prazos definidos", sub: "Estrutura e previsibilidade" },
      { p: "A", ic: "raio", t: "Metas desafiadoras", sub: "Competição e conquista" },
      { p: "S", ic: "coracao", t: "Propósito humano", sub: "Conexão e impacto na vida das pessoas" },
      { p: "E", ic: "grafico", t: "Problemas complexos", sub: "Espaço para investigar e inovar" },
    ],
  },
  {
    pergunta: "Diante de um imprevisto, sua primeira reação é...",
    cartas: [
      { p: "B", ic: "bussola", t: "Reorganizar o plano", sub: "Ajusto o cronograma e retomo o controle" },
      { p: "A", ic: "raio", t: "Agir imediatamente", sub: "Resolvo primeiro, ajusto depois" },
      { p: "S", ic: "coracao", t: "Acalmar as pessoas", sub: "Alinho o time e cuido de quem foi afetado" },
      { p: "E", ic: "grafico", t: "Investigar a causa", sub: "Entendo o que aconteceu antes de agir" },
    ],
  },
  {
    pergunta: "Você se sente realizado quando...",
    cartas: [
      { p: "B", ic: "bussola", t: "Tudo sai conforme o planejado", sub: "Entrega feita com responsabilidade" },
      { p: "A", ic: "raio", t: "Vence um grande desafio", sub: "Supera a meta ou a concorrência" },
      { p: "S", ic: "coracao", t: "Ajuda alguém a crescer", sub: "Vê o impacto positivo nas pessoas" },
      { p: "E", ic: "grafico", t: "Descobre algo novo", sub: "Aprende, entende ou cria uma solução" },
    ],
  },
  {
    pergunta: "Seu maior receio no trabalho é...",
    cartas: [
      { p: "B", ic: "bussola", t: "Perder o controle da situação", sub: "Desorganização e improviso constante" },
      { p: "A", ic: "raio", t: "Ficar parado", sub: "Perder oportunidades e ritmo" },
      { p: "S", ic: "coracao", t: "Magoar ou decepcionar pessoas", sub: "Conflitos e ambientes hostis" },
      { p: "E", ic: "grafico", t: "Decidir sem informação", sub: "Agir no achismo, sem dados" },
    ],
  },
];

const BASE_PERFIS = {
  B: {
    nome: "Bússola",
    ic: "bussola",
    cor: "#3B67CA",
    resumo: "Movido por estrutura, planejamento e responsabilidade. A Bússola dá direção: organiza, prevê riscos e garante que o combinado seja cumprido.",
    fortes: ["Planejamento e organização", "Senso de responsabilidade e compromisso", "Gestão de riscos e prazos", "Constância e disciplina"],
    desenvolvimento: ["Flexibilizar quando o plano precisa mudar", "Tolerar improvisos pontuais", "Delegar sem perder a tranquilidade"],
  },
  A: {
    nome: "Atuante",
    ic: "raio",
    cor: "#9BB9DD",
    resumo: "Movido por ação, competição e oportunidade. O Atuante faz acontecer: age rápido, assume riscos e transforma ideias em resultado.",
    fortes: ["Velocidade de execução", "Espírito competitivo e ambição", "Coragem para decidir e arriscar", "Energia que mobiliza o time"],
    desenvolvimento: ["Planejar antes de agir em temas críticos", "Ouvir opiniões divergentes", "Cuidar dos detalhes e da consistência"],
  },
  S: {
    nome: "Sensível",
    ic: "coracao",
    cor: "#7695B4",
    resumo: "Movido por empatia, conexão e propósito humano. O Sensível cuida das pessoas: cria confiança, harmoniza o time e dá sentido ao trabalho.",
    fortes: ["Empatia e escuta ativa", "Construção de relacionamentos de confiança", "Mediação de conflitos", "Trabalho orientado a propósito"],
    desenvolvimento: ["Tomar decisões difíceis mesmo quando desagradam", "Estabelecer limites claros", "Não absorver os problemas de todos"],
  },
  E: {
    nome: "Estudioso",
    ic: "grafico",
    cor: "#85A0BF",
    resumo: "Movido por lógica, dados e inovação. O Estudioso entende o problema a fundo: analisa, questiona e encontra soluções que ninguém viu.",
    fortes: ["Pensamento analítico e crítico", "Decisões baseadas em dados", "Curiosidade e aprendizado contínuo", "Capacidade de inovar"],
    desenvolvimento: ["Decidir mesmo com informação incompleta", "Comunicar ideias de forma simples", "Equilibrar análise com ação"],
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
