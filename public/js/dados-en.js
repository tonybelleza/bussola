/* =====================================================================
   Test content in English (US). Loaded only by the candidate area and
   the jobs page, after data.js. aplicarIdiomaDados("en") merges these
   texts over the Portuguese originals, keeping colors, icons, profile
   letters (p) and DISC dimensions (d) from data.js.

   Profile names chosen for English (letters never change):
     DISC:     D Dominance, I Influence, S Steadiness, C Conscientiousness
     B.A.S.E.: B Bearing   (a compass bearing: direction, structure, reliability)
               A Achiever  (action, competition, results)
               S Sensitive (empathy, people, purpose)
               E Explorer  (ideas, logic, endless learning)
   ===================================================================== */

DADOS_I18N.en = {
  DISC_BLOCOS: [
    [{ t: "Decisive", d: "D" }, { t: "Talkative", d: "I" }, { t: "Patient", d: "S" }, { t: "Detail-oriented", d: "C" }],
    [{ t: "Competitive", d: "D" }, { t: "Enthusiastic", d: "I" }, { t: "Loyal", d: "S" }, { t: "Analytical", d: "C" }],
    [{ t: "Direct", d: "D" }, { t: "Sociable", d: "I" }, { t: "Calm", d: "S" }, { t: "Precise", d: "C" }],
    [{ t: "Bold", d: "D" }, { t: "Optimistic", d: "I" }, { t: "Steady", d: "S" }, { t: "Cautious", d: "C" }],
    [{ t: "Determined", d: "D" }, { t: "Persuasive", d: "I" }, { t: "Good listener", d: "S" }, { t: "Organized", d: "C" }],
    [{ t: "Energetic", d: "D" }, { t: "Inspiring", d: "I" }, { t: "Accommodating", d: "S" }, { t: "Methodical", d: "C" }],
    [{ t: "Results-focused", d: "D" }, { t: "Expressive", d: "I" }, { t: "Cooperative", d: "S" }, { t: "Perfectionist", d: "C" }],
    [{ t: "Takes risks", d: "D" }, { t: "Spontaneous", d: "I" }, { t: "Predictable", d: "S" }, { t: "Systematic", d: "C" }],
    [{ t: "Self-confident", d: "D" }, { t: "Charismatic", d: "I" }, { t: "Welcoming", d: "S" }, { t: "Discerning", d: "C" }],
    [{ t: "Firm", d: "D" }, { t: "Fun", d: "I" }, { t: "Tolerant", d: "S" }, { t: "Disciplined", d: "C" }],
    [{ t: "Independent", d: "D" }, { t: "Popular", d: "I" }, { t: "Helpful", d: "S" }, { t: "Logical", d: "C" }],
    [{ t: "Ambitious", d: "D" }, { t: "Convincing", d: "I" }, { t: "Stable", d: "S" }, { t: "Rigorous", d: "C" }],
    [{ t: "Straightforward", d: "D" }, { t: "Lively", d: "I" }, { t: "Harmonious", d: "S" }, { t: "Exact", d: "C" }],
    [{ t: "Brave", d: "D" }, { t: "Outgoing", d: "I" }, { t: "Serene", d: "S" }, { t: "Reserved", d: "C" }],
    [{ t: "Demanding", d: "D" }, { t: "Charming", d: "I" }, { t: "Kind", d: "S" }, { t: "Rational", d: "C" }],
    [{ t: "Quick to decide", d: "D" }, { t: "Chatty", d: "I" }, { t: "Thoughtful", d: "S" }, { t: "Careful", d: "C" }],
    [{ t: "Assertive", d: "D" }, { t: "Engaging", d: "I" }, { t: "Discreet", d: "S" }, { t: "Formal", d: "C" }],
    [{ t: "Pioneering", d: "D" }, { t: "Uplifting", d: "I" }, { t: "Faithful", d: "S" }, { t: "Meticulous", d: "C" }],
    [{ t: "Vigorous", d: "D" }, { t: "Easygoing", d: "I" }, { t: "Gentle", d: "S" }, { t: "Prudent", d: "C" }],
    [{ t: "Dominant", d: "D" }, { t: "Influential", d: "I" }, { t: "Supportive", d: "S" }, { t: "Structured", d: "C" }],
    [{ t: "Practical", d: "D" }, { t: "Creative communicator", d: "I" }, { t: "Peacemaker", d: "S" }, { t: "Inquisitive", d: "C" }],
    [{ t: "Impatient for results", d: "D" }, { t: "Seeks recognition", d: "I" }, { t: "Avoids conflict", d: "S" }, { t: "Afraid of making mistakes", d: "C" }],
    [{ t: "Likes challenges", d: "D" }, { t: "Likes people", d: "I" }, { t: "Likes a steady routine", d: "S" }, { t: "Likes clear rules", d: "C" }],
    [{ t: "Takes the lead", d: "D" }, { t: "Motivates the group", d: "I" }, { t: "Supports the group", d: "S" }, { t: "Ensures quality", d: "C" }],
  ],

  DISC_PERFIS: {
    D: {
      nome: "Dominance",
      resumo: "A profile driven by results, challenges and quick decisions. People high in Dominance are direct, competitive and take charge of situations.",
      fortes: ["Focus on results and goals", "Quick decision making", "Initiative and courage to take risks", "Ability to lead under pressure"],
      desenvolvimento: ["Listen more before deciding", "Be patient with people who work at a different pace", "Soften communication on sensitive topics", "Delegate without micromanaging the outcome"],
      trabalho: "Prefers autonomy, clear goals and challenging environments. Communicates in a direct, to-the-point way and expects the same from others.",
    },
    I: {
      nome: "Influence",
      resumo: "A communicative, enthusiastic and persuasive profile. People high in Influence motivate teams, build connections and sell ideas with ease.",
      fortes: ["Communication and persuasion", "Optimism and contagious energy", "Ease in building relationships", "Creativity to engage people"],
      desenvolvimento: ["Pay attention to deadlines and details", "Finish what you start before beginning something new", "Listen as much as you talk", "Base decisions on data as well"],
      trabalho: "Prefers collaborative environments with room for interaction and recognition. Communicates in an expressive, engaging way.",
    },
    S: {
      nome: "Steadiness",
      resumo: "A patient, loyal and collaborative profile. People high in Steadiness hold the team together, keep the peace and deliver consistently.",
      fortes: ["Consistency and reliability", "Active listening and empathy", "Teamwork and cooperation", "Calm in tense moments"],
      desenvolvimento: ["Adapt more quickly to change", "Speak up about disagreements more often", "Say no when needed", "Step out of your comfort zone for new challenges"],
      trabalho: "Prefers predictable environments, trusting relationships and well-communicated changes. Communicates in a calm, attentive way.",
    },
    C: {
      nome: "Conscientiousness",
      resumo: "An analytical, precise and quality-focused profile. People high in Conscientiousness follow standards, analyze data and ensure technical excellence.",
      fortes: ["Careful analysis and attention to detail", "Quality and accuracy in their work", "Planning and organization", "Decisions based on data and facts"],
      desenvolvimento: ["Accept that 'good' is sometimes enough (perfectionism)", "Decide even without 100% of the information", "Be flexible with rules when the situation calls for it", "Communicate in a warmer way"],
      trabalho: "Prefers structured environments with clear processes and time for analysis. Communicates in a precise, formal way.",
    },
  },

  BASE_INSTRUCAO: "Click the 4 cards in order, from the one most like you to the one least like you",

  BASE_RODADAS: [
    {
      pergunta: "What drives you most at work and in life?",
      cartas: [
        { p: "B", t: "Stability", sub: "Security and predictability" },
        { p: "A", t: "Results", sub: "Winning and reaching goals" },
        { p: "S", t: "Connection", sub: "Genuine relationships" },
        { p: "E", t: "Knowledge", sub: "Always learning and growing" },
      ],
    },
    {
      pergunta: "Which value matters most to you in a workplace?",
      cartas: [
        { p: "B", t: "Organization", sub: "Everything in its place" },
        { p: "A", t: "Freedom", sub: "Doing it your own way" },
        { p: "S", t: "Harmony", sub: "Peace and teamwork" },
        { p: "E", t: "Innovation", sub: "New ideas and solutions" },
      ],
    },
    {
      pergunta: "How do you prefer to make important decisions?",
      cartas: [
        { p: "B", t: "Planning", sub: "With careful analysis" },
        { p: "A", t: "Intuition", sub: "Fast, seizing the opportunity" },
        { p: "S", t: "Agreement", sub: "Listening to everyone involved" },
        { p: "E", t: "Data", sub: "With evidence and logic" },
      ],
    },
    {
      pergunta: "What motivates you most to take action?",
      cartas: [
        { p: "B", t: "Responsibility", sub: "Keeping my promises" },
        { p: "A", t: "Competition", sub: "Being the best and pushing limits" },
        { p: "S", t: "Purpose", sub: "Making a difference for people" },
        { p: "E", t: "Strategy", sub: "Solving complex problems" },
      ],
    },
    {
      pergunta: "How do you prefer to communicate?",
      cartas: [
        { p: "B", t: "Clarity", sub: "Straight to the point" },
        { p: "A", t: "Impact", sub: "Energetic and enthusiastic" },
        { p: "S", t: "Empathy", sub: "With care and active listening" },
        { p: "E", t: "Precision", sub: "With information and details" },
      ],
    },
    {
      pergunta: "What bothers you most in a project?",
      cartas: [
        { p: "B", t: "Surprises", sub: "Lack of planning" },
        { p: "A", t: "Slowness", sub: "Slow processes and red tape" },
        { p: "S", t: "Conflict", sub: "Arguments and a hostile environment" },
        { p: "E", t: "Shallowness", sub: "Lack of depth" },
      ],
    },
    {
      pergunta: "What is your greatest personal strength?",
      cartas: [
        { p: "B", t: "Discipline", sub: "Consistency and commitment" },
        { p: "A", t: "Leadership", sub: "Influencing and rallying people" },
        { p: "S", t: "Care", sub: "Supporting and developing others" },
        { p: "E", t: "Vision", sub: "Seeing beyond the obvious" },
      ],
    },
    {
      pergunta: "What gives you the most satisfaction at the end of the day?",
      cartas: [
        { p: "B", t: "Completion", sub: "Finishing everything I planned" },
        { p: "A", t: "Achievement", sub: "Having overcome a challenge" },
        { p: "S", t: "Impact", sub: "Having truly helped someone" },
        { p: "E", t: "Learning", sub: "Having discovered something new" },
      ],
    },
  ],

  BASE_POSICOES: [
    "1st position · Your main engine",
    "2nd position · Your secondary influence",
    "3rd position · How you act under stress",
    "4th position · Your lowest priority values",
  ],

  BASE_PERFIS: {
    B: {
      nome: "Bearing",
      titulo: "The Guardian of Systems",
      tagline: "You are the anchor that keeps everything in place. Responsible, detail-oriented and process-driven, your strength lies in building reliable systems, keeping commitments and making sure every gear runs with precision. When you give your word, it is law.",
      resumo: "People with the Bearing profile put responsibility first. You live by a strong inner moral code, respect rules, traditions and authority, and expect the same from others. Detail-oriented and process-driven, you masterfully turn chaos into order. Your ability to plan, organize and execute with discipline makes you one of the most reliable people on any team. You prefer to analyze carefully before acting, work best with set deadlines and clear systems, and stand out in logistics, management and implementation. For you, consistency is not a limitation, it is excellence.",
      fortes: ["Organized and detail-oriented", "Disciplined and consistent", "Expert planner", "Committed to delivering", "Efficient implementer", "Step-by-step thinker", "Reliable and responsible", "Management and logistics"],
      gatilhos: ["Professional people who show up prepared and on time.", "Environments with clear rules and well-defined expectations.", "People who keep their promises, no exceptions and no excuses.", "Organized systems, documentation and well-structured processes.", "People who show credentials, references and a proven track record.", "Plans with clear steps, realistic deadlines and a set budget.", "People who present a step-by-step plan for success.", "Traditions, tested methods and respect for hierarchy.", "Efficient meetings with a clear agenda and concrete results.", "People who reduce risk with verifiable facts and proof."],
      repulsores: ["Surprises and last-minute changes without a solid reason.", "Disorganized people who improvise and do not follow processes.", "People who promise and do not deliver, or change plans without notice.", "Chaotic environments with no structure, systems or clear responsibilities.", "People who disrespect hierarchy, rules and established authority.", "Impulsive decisions made without enough analysis or data.", "People who do not respect deadlines, commitments and budgets.", "Wasted resources or lack of financial planning.", "People who are overly emotional or sensitive when making decisions.", "Lack of professionalism and attention to detail."],
      posicoes: [
        "With Bearing in the first position, structure, responsibility and planning are what drive your decisions most. You lead with organization and reliability.",
        "Bearing in the second position means you are very skilled at organization and processes, and you use these skills to support your main profile day to day.",
        "Under stress, you tend to switch to Bearing mode, looking for control, systems and planning to feel safe again.",
        "Bearing values such as tradition, hierarchy and rigid systems are your lowest priority. You prefer flexibility over fixed rules.",
      ],
      comunicacao: {
        A: ["Show enthusiasm and energy, and present the opportunity with confidence.", "Get straight to the point, show the result and the immediate impact.", "Skip excessive details, focus on the lifestyle and the dream.", "Introduce influencers and successful people from your network.", "Convey a sense of urgency: remember that time is money.", "Be confident and show strong self-esteem when presenting."],
        S: ["Show that you genuinely care about people beyond business.", "Share real stories of transformation and human impact.", "Build the personal relationship before talking business or numbers.", "Show how your proposal connects to values, purpose and mission.", "Be authentic, open up about your personal story and motivations.", "Ask about their personal life (family, hobbies, passions)."],
        E: ["Present data, research and concrete evidence, be smart.", "Give them time to analyze and process the information before deciding.", "Be ready to debate and defend your position with logic.", "Stay rational, avoid emotional exaggeration or too much excitement.", "Provide documentation, resources and data for in-depth study.", "Be open to hearing their point of view and seeing the big picture."],
      },
    },
    A: {
      nome: "Achiever",
      titulo: "The Relentless Doer",
      tagline: "You are not afraid to take risks and you are always looking for the next big opportunity. Your energy, confidence and drive to act make you a natural leader who creates momentum wherever you go.",
      resumo: "People with the Achiever profile are driven by action, competition and the constant pursuit of winning. You are the first to stand up when an opportunity appears and the last to give up when a challenge shows up. You are not afraid to take risks and you are always looking for ways to shake up and improve the status quo. Your flexibility, ability to improvise and talent for creating momentum make you a force of nature in negotiation, sales and leadership. You think fast, act even faster, and inspire the people around you with your self-confidence and vision of the future. If something big is going to happen, you want to be the one leading it.",
      fortes: ["Focused on results and winning", "Decisive and quick to act", "Competitive and ambitious", "Natural, charismatic leadership", "Creates momentum", "Resilient in a crisis", "Persuasive performer", "Flexible improviser"],
      gatilhos: ["Chances to be the first, the best or the biggest.", "Dynamic environments that value speed, action and results.", "Public recognition for achievements and performance.", "People who present ideas with energy, enthusiasm and a vision of impact.", "Networking with influential, powerful and successful people.", "Challenges that seem impossible to others, the bigger the better.", "Image, style and presence that convey success and confidence.", "Total freedom to act without red tape or micromanagement.", "Fun, lifestyle and experiences that feed the dream.", "A sense of urgency and exclusive windows of opportunity."],
      repulsores: ["Slow processes, red tape and too much planning without action.", "Long meetings with no decision, clear result or defined goal.", "People who question too much, analyze too much and never act.", "Environments that limit creativity, initiative and autonomy.", "Lack of recognition for effort, achievement and performance.", "Dull presentations with no energy and no vision.", "Micromanagement that smothers you and takes away your freedom to act.", "Too many details, data and stories when you want the conclusion.", "Fearful people who refuse to take risks or make decisions.", "People who lack self-esteem or confidence in what they present."],
      posicoes: [
        "With Achiever in the first position, action, competition and results fuel your decisions. You lead with energy and a vision of winning.",
        "Achiever in the second position adds drive and speed to your main profile. You know when it is time to act and create momentum.",
        "Under stress, you switch to Achiever mode, looking for immediate action, making quick decisions and taking control of the situation.",
        "Achiever values such as competition, risk and impulsive decisions matter least to you. You prefer to think things through before acting.",
      ],
      comunicacao: {
        B: ["Be organized and professional, and present a clear step-by-step plan.", "Arrive 15 to 30 minutes early, being on time is a sign of respect.", "Provide facts, proof, references and verifiable credentials.", "Reduce the risks involved with data and proven systems.", "Do not be overly emotional or sensitive, show the system.", "Respect the budget and stay within the agreed limits."],
        S: ["Genuinely build the human relationship before making any offer.", "Show empathy and real interest in their personal story.", "Connect your proposal to a greater social impact and purpose.", "Be authentic and transparent, avoid sounding pushy or fake.", "Share real stories of lives transformed and impact made.", "Introduce them to members of your team and create a sense of community."],
        E: ["Present solid logic, concrete data and well-grounded reasoning.", "Give them space and time to analyze, never force quick decisions.", "Be ready for technical discussions and in-depth debates.", "Provide evidence and let them question freely.", "Stay rational and open to seeing the big picture.", "Dress well and show intellectual sophistication."],
      },
    },
    S: {
      nome: "Sensitive",
      titulo: "The Bridge Builder",
      tagline: "You put people first. Your presence lights up any room, builds community where there was none and awakens potential others did not know they had. Genuine connection is your superpower.",
      resumo: "People with the Sensitive profile are guided by empathy, authenticity and a deep desire to make a positive difference in the lives of those around them. You are friendly, welcoming and open, and you make everyone feel part of the community. Relationships are your priority, and you always look for real, deep connection. Helping people become the best version of themselves is what moves you. While business matters, you know there is more to life than money, and you are always looking for deeper meaning. You avoid too much competition and conflict, and prefer to encourage teams to lift each other up. No one is as skilled as you at solving problems diplomatically and awakening hidden potential in people.",
      fortes: ["Empathetic and welcoming", "Driven by purpose and meaning", "Brings out potential in others", "Diplomat who creates harmony", "Always authentic and genuine", "Natural coach and mentor", "Intuitive about others' needs", "Focused on human impact"],
      gatilhos: ["People who take part in social and community causes beyond their job.", "People who are passionate about what they do, with a clear and true purpose.", "People who create a genuine sense of community and belonging.", "Warm, friendly and truly human energy.", "People who go the extra mile to show care, gratitude and appreciation.", "Connecting through shared stories, interests and experiences.", "People who try to understand each person as a unique individual.", "People who introduce their team and include you in the community.", "Questions about your personal story, family, hobbies and passions.", "Approachable, friendly people who treat everyone as equals."],
      repulsores: ["People who seem to care more about money than about people.", "Environments with too much competition, aggressiveness and emotional coldness.", "People who come across as fake or artificial.", "Rude people who lack basic kindness and manners.", "People who do not try to understand others as unique individuals.", "People who do not share stories and experiences of clients and others.", "People who forget important personal details (birthdays, family).", "Lack of moral integrity and high ethical standards.", "People who do not share their heart, purpose or reason for being.", "Self-centered people who lack humility and empathy."],
      posicoes: [
        "With Sensitive in the first position, people, connection and human purpose guide all your choices. You lead with empathy and authenticity.",
        "Sensitive in the second position enriches your profile with emotional intelligence and the ability to build genuine connections in any setting.",
        "Under stress, you switch to Sensitive mode, looking for emotional support, harmony and reconnection with the people around you.",
        "Sensitive values such as harmony at any cost and avoiding conflict are not your priority. You can be more direct when needed.",
      ],
      comunicacao: {
        B: ["Be organized, professional and on time, and come prepared.", "Present a clear plan with defined, step-by-step stages.", "Provide facts, proof and references, and reduce the risks.", "Do not be overly emotional or sensitive in presentations.", "Show the system for success with data and credentials.", "Respect the budget and show financial responsibility."],
        A: ["Show enthusiasm, energy and confidence, and get straight to the point.", "Present the chance to win and a clear competitive advantage.", "Connect them with influential and powerful people from your network.", "Focus on impact, results and lifestyle, not on the process.", "Convey genuine urgency: time is money to them.", "Be confident, show strong self-esteem and have fun."],
        E: ["Present concrete data, logical reasoning and solid evidence.", "Stay objective, avoid emotional exaggeration or drama.", "Give them space and time to analyze before asking for any decision.", "Use precise language and provide documentation for study.", "Be open to debate and willing to see the big picture.", "Show intellectual depth and command of the subject."],
      },
    },
    E: {
      nome: "Explorer",
      titulo: "The Architect of Ideas",
      tagline: "Your mind is your greatest tool. You value reason above all, and make decisions based on facts and science, never on emotion. You see patterns where others see only information, and you turn complexity into strategy.",
      resumo: "People with the Explorer profile are driven by logic, continuous learning and the constant search for innovative solutions. You are not satisfied with shallow answers, you want to understand the deep why of everything. You make decisions based on facts and science, never on emotion, and you excel at analyzing data, planning for the long term and finding errors others miss. Your capacity for abstract thinking, big-picture vision and precise language make you an endless source of knowledge. You often enjoy the process of learning more than acting on the information. Creative and visionary, you are always looking for a better way to do things, and when you find it, you build models, diagrams and theories that change paradigms.",
      fortes: ["Analytical and logical", "Innovative and visionary", "Systemic and abstract thinker", "Lifelong learner", "Long-term strategist", "Precise in language and thought", "Solves complex problems", "Creates models and theories"],
      gatilhos: ["Intellectually stimulating discussions and in-depth debates.", "People who present solid data, research and logical reasoning.", "Cutting-edge technology, innovation and solutions that challenge the status quo.", "Space and time to analyze before making any decision.", "People who truly master the subject they present, real expertise.", "Projects with genuine complexity and intellectual challenge.", "Precise language, consistent information and attention to detail.", "People who respect the need for time to think and process.", "Resources, documentation and data for in-depth study.", "Refined, intelligent people with a sophisticated presence."],
      repulsores: ["Shallow information or arguments with no basis.", "People who ask for a quick decision without data, analysis or enough time.", "Emotional exaggeration, enthusiasm without substance and needless drama.", "Environments that undervalue expertise, knowledge and depth.", "People who are not open to debate, questions and different perspectives.", "Exaggerated promises without concrete evidence or verifiable cases.", "Unproductive meetings with no agenda, clear goal or tangible result.", "Too many personal details, stories and drama when you want logic.", "People who will not admit when they do not know something, lack of intellectual humility.", "People who try to manipulate with emotion instead of convincing with reason."],
      posicoes: [
        "With Explorer in the first position, logic, data and continuous learning lead your decision process. You lead with reason and strategic vision.",
        "Explorer in the second position brings analytical depth and big-picture vision to your main profile, enriching your decisions.",
        "Under stress, you switch to Explorer mode, diving into analysis, looking for data and trying to make sense of the situation before reacting.",
        "Explorer values such as overanalysis and the pursuit of intellectual perfection are your lowest priority. You prefer acting to analyzing endlessly.",
      ],
      comunicacao: {
        B: ["Be organized and on time, and present complete documentation.", "Show the system, the process and the step by step behind the proposal.", "Provide facts and proof, and reduce the risks with concrete evidence.", "Respect the need for process, hierarchy and tradition.", "Present references, credentials and proven cases.", "Stay within budget and show responsibility."],
        A: ["Show enthusiasm and energy, and present the opportunity with confidence.", "Focus on winning, results and lifestyle, not on details.", "Go straight to the conclusion, skip small talk and excess data.", "Connect them with influencers and successful people from your network.", "Create urgency: present the window of opportunity as something exclusive.", "Be confident, fun and have healthy self-esteem."],
        S: ["Build the human relationship with authenticity and genuine interest.", "Share the purpose, mission and human impact behind the business.", "Show how your proposal changes people's lives for the better.", "Show that you care about them as human beings, not as clients.", "Use real stories of transformation, impact and life change as proof.", "Ask about their family, passions and personal story."],
      },
    },
  },

  PAISES_NOMES: {
    "Angola": "Angola",
    "Brasil": "Brazil",
    "Espanha": "Spain",
    "Estados Unidos": "United States",
    "França": "France",
    "Portugal": "Portugal",
  },

  ESCALA_NIVEIS: [
    { v: 0, rot: "0 · None" },
    { v: 1, rot: "1 · Basic" },
    { v: 2, rot: "2 · Developing" },
    { v: 3, rot: "3 · Intermediate" },
    { v: 4, rot: "4 · Advanced" },
    { v: 5, rot: "5 · Expert" },
  ],

  TIPOS_COMPETENCIA: {
    tecnica: "Technical",
    relacional: "Interpersonal",
    formacao: "Education / Certification",
    experiencia: "Experience",
  },
};
