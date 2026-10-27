/* =====================================================================
   Contenido de las pruebas en español (neutro de Latinoamérica, lenguaje
   sencillo y trato de "tú"). Solo lo cargan el área del candidato y la
   página de vacantes, después de data.js. aplicarIdiomaDados("es") mezcla
   estos textos sobre los originales en portugués y mantiene colores,
   íconos, letras de perfil (p) y dimensiones DISC (d) de data.js.

   Nombres de perfil elegidos para español (las letras no cambian):
     DISC:     D Dominancia, I Influencia, S Estabilidad, C Cumplimiento
     B.A.S.E.: B Brújula   (dirección, estructura, confiabilidad)
               A Activo    (acción, competencia, resultados)
               S Sensible  (empatía, personas, propósito)
               E Estudioso (ideas, lógica, aprendizaje constante)
   ===================================================================== */

DADOS_I18N.es = {
  DISC_BLOCOS: [
    [{ t: "Decidido", d: "D" }, { t: "Comunicativo", d: "I" }, { t: "Paciente", d: "S" }, { t: "Detallista", d: "C" }],
    [{ t: "Competitivo", d: "D" }, { t: "Entusiasta", d: "I" }, { t: "Leal", d: "S" }, { t: "Analítico", d: "C" }],
    [{ t: "Directo", d: "D" }, { t: "Sociable", d: "I" }, { t: "Tranquilo", d: "S" }, { t: "Preciso", d: "C" }],
    [{ t: "Atrevido", d: "D" }, { t: "Optimista", d: "I" }, { t: "Constante", d: "S" }, { t: "Cauteloso", d: "C" }],
    [{ t: "Determinado", d: "D" }, { t: "Persuasivo", d: "I" }, { t: "Sabe escuchar", d: "S" }, { t: "Organizado", d: "C" }],
    [{ t: "Enérgico", d: "D" }, { t: "Inspirador", d: "I" }, { t: "Conciliador", d: "S" }, { t: "Metódico", d: "C" }],
    [{ t: "Enfocado en resultados", d: "D" }, { t: "Expresivo", d: "I" }, { t: "Cooperativo", d: "S" }, { t: "Perfeccionista", d: "C" }],
    [{ t: "Toma riesgos", d: "D" }, { t: "Espontáneo", d: "I" }, { t: "Predecible", d: "S" }, { t: "Sistemático", d: "C" }],
    [{ t: "Seguro de sí mismo", d: "D" }, { t: "Carismático", d: "I" }, { t: "Acogedor", d: "S" }, { t: "Juicioso", d: "C" }],
    [{ t: "Firme", d: "D" }, { t: "Divertido", d: "I" }, { t: "Tolerante", d: "S" }, { t: "Disciplinado", d: "C" }],
    [{ t: "Independiente", d: "D" }, { t: "Popular", d: "I" }, { t: "Servicial", d: "S" }, { t: "Lógico", d: "C" }],
    [{ t: "Ambicioso", d: "D" }, { t: "Convincente", d: "I" }, { t: "Estable", d: "S" }, { t: "Riguroso", d: "C" }],
    [{ t: "Objetivo", d: "D" }, { t: "Animado", d: "I" }, { t: "Armonioso", d: "S" }, { t: "Exacto", d: "C" }],
    [{ t: "Valiente", d: "D" }, { t: "Extrovertido", d: "I" }, { t: "Sereno", d: "S" }, { t: "Reservado", d: "C" }],
    [{ t: "Exigente", d: "D" }, { t: "Encantador", d: "I" }, { t: "Amable", d: "S" }, { t: "Racional", d: "C" }],
    [{ t: "Decide rápido", d: "D" }, { t: "Conversador", d: "I" }, { t: "Reflexivo", d: "S" }, { t: "Cuidadoso", d: "C" }],
    [{ t: "Asertivo", d: "D" }, { t: "Cautivador", d: "I" }, { t: "Discreto", d: "S" }, { t: "Formal", d: "C" }],
    [{ t: "Pionero", d: "D" }, { t: "Contagia alegría", d: "I" }, { t: "Fiel", d: "S" }, { t: "Minucioso", d: "C" }],
    [{ t: "Vigoroso", d: "D" }, { t: "Relajado", d: "I" }, { t: "Cariñoso", d: "S" }, { t: "Prudente", d: "C" }],
    [{ t: "Dominante", d: "D" }, { t: "Influyente", d: "I" }, { t: "Solidario", d: "S" }, { t: "Estructurado", d: "C" }],
    [{ t: "Práctico", d: "D" }, { t: "Creativo al expresarse", d: "I" }, { t: "Pacificador", d: "S" }, { t: "Investigador", d: "C" }],
    [{ t: "Impaciente por resultados", d: "D" }, { t: "Busca reconocimiento", d: "I" }, { t: "Evita conflictos", d: "S" }, { t: "Teme cometer errores", d: "C" }],
    [{ t: "Le gustan los retos", d: "D" }, { t: "Le gusta la gente", d: "I" }, { t: "Le gusta una rutina estable", d: "S" }, { t: "Le gustan las reglas claras", d: "C" }],
    [{ t: "Toma la iniciativa", d: "D" }, { t: "Motiva al grupo", d: "I" }, { t: "Apoya al grupo", d: "S" }, { t: "Cuida la calidad", d: "C" }],
  ],

  DISC_PERFIS: {
    D: {
      nome: "Dominancia",
      resumo: "Un perfil enfocado en resultados, retos y decisiones rápidas. Las personas con alta Dominancia son directas, competitivas y toman el control de las situaciones.",
      fortes: ["Enfoque en resultados y metas", "Rapidez para tomar decisiones", "Iniciativa y valor para tomar riesgos", "Capacidad de liderar bajo presión"],
      desenvolvimento: ["Escuchar más antes de decidir", "Tener paciencia con quienes trabajan a otro ritmo", "Suavizar la forma de hablar en temas delicados", "Delegar sin controlar cada detalle"],
      trabalho: "Prefiere la autonomía, las metas claras y los ambientes con retos. Se comunica de forma directa y concreta, y espera lo mismo de los demás.",
    },
    I: {
      nome: "Influencia",
      resumo: "Un perfil comunicativo, entusiasta y persuasivo. Las personas con alta Influencia motivan a los equipos, crean conexiones y venden ideas con facilidad.",
      fortes: ["Comunicación y persuasión", "Optimismo y energía contagiosa", "Facilidad para crear relaciones", "Creatividad para involucrar a las personas"],
      desenvolvimento: ["Prestar atención a plazos y detalles", "Terminar lo que empieza antes de comenzar algo nuevo", "Escuchar tanto como habla", "Tomar decisiones también con base en datos"],
      trabalho: "Prefiere ambientes de colaboración, con espacio para convivir y recibir reconocimiento. Se comunica de forma expresiva y cercana.",
    },
    S: {
      nome: "Estabilidad",
      resumo: "Un perfil paciente, leal y colaborador. Las personas con alta Estabilidad sostienen al equipo, mantienen la armonía y cumplen con constancia.",
      fortes: ["Constancia y confiabilidad", "Escucha atenta y empatía", "Trabajo en equipo y cooperación", "Calma en momentos de tensión"],
      desenvolvimento: ["Adaptarse más rápido a los cambios", "Decir con más frecuencia cuando no está de acuerdo", "Decir que no cuando hace falta", "Salir de la zona de confort ante nuevos retos"],
      trabalho: "Prefiere ambientes predecibles, relaciones de confianza y cambios bien explicados. Se comunica de forma tranquila y atenta.",
    },
    C: {
      nome: "Cumplimiento",
      resumo: "Un perfil analítico, preciso y enfocado en la calidad. Las personas con alto Cumplimiento siguen normas, analizan datos y aseguran un trabajo excelente.",
      fortes: ["Análisis cuidadoso y atención a los detalles", "Calidad y precisión en el trabajo", "Planificación y organización", "Decisiones basadas en datos y hechos"],
      desenvolvimento: ["Aceptar que a veces 'bueno' es suficiente (perfeccionismo)", "Decidir aunque no tenga el 100% de la información", "Ser flexible con las reglas cuando la situación lo pide", "Comunicarse de forma más cálida"],
      trabalho: "Prefiere ambientes ordenados, con procesos claros y tiempo para analizar. Se comunica de forma precisa y formal.",
    },
  },

  BASE_INSTRUCAO: "Toca las 4 tarjetas en orden, desde la que más va contigo hasta la que menos va contigo",

  BASE_RODADAS: [
    {
      pergunta: "¿Qué es lo que más te impulsa en el trabajo y en la vida?",
      cartas: [
        { p: "B", t: "Estabilidad", sub: "Seguridad y saber qué esperar" },
        { p: "A", t: "Resultados", sub: "Ganar y lograr metas" },
        { p: "S", t: "Conexión", sub: "Relaciones sinceras" },
        { p: "E", t: "Conocimiento", sub: "Aprender y crecer siempre" },
      ],
    },
    {
      pergunta: "¿Qué valor aprecias más en un lugar de trabajo?",
      cartas: [
        { p: "B", t: "Orden", sub: "Cada cosa en su lugar" },
        { p: "A", t: "Libertad", sub: "Hacerlo a tu manera" },
        { p: "S", t: "Armonía", sub: "Paz y colaboración" },
        { p: "E", t: "Innovación", sub: "Nuevas ideas y soluciones" },
      ],
    },
    {
      pergunta: "¿Cómo prefieres tomar las decisiones importantes?",
      cartas: [
        { p: "B", t: "Planificación", sub: "Analizando con cuidado" },
        { p: "A", t: "Intuición", sub: "Rápido, aprovechando la oportunidad" },
        { p: "S", t: "Acuerdo", sub: "Escuchando a todos los involucrados" },
        { p: "E", t: "Datos", sub: "Con pruebas y lógica" },
      ],
    },
    {
      pergunta: "¿Qué es lo que más te motiva a actuar?",
      cartas: [
        { p: "B", t: "Responsabilidad", sub: "Cumplir lo que prometí" },
        { p: "A", t: "Competencia", sub: "Ser el mejor y superar límites" },
        { p: "S", t: "Propósito", sub: "Hacer la diferencia en las personas" },
        { p: "E", t: "Estrategia", sub: "Resolver problemas difíciles" },
      ],
    },
    {
      pergunta: "¿Cómo prefieres comunicarte?",
      cartas: [
        { p: "B", t: "Claridad", sub: "Directo al punto" },
        { p: "A", t: "Impacto", sub: "Con energía y entusiasmo" },
        { p: "S", t: "Empatía", sub: "Con cuidado y escuchando" },
        { p: "E", t: "Precisión", sub: "Con información y detalles" },
      ],
    },
    {
      pergunta: "¿Qué es lo que más te molesta en un proyecto?",
      cartas: [
        { p: "B", t: "Imprevistos", sub: "Falta de planificación" },
        { p: "A", t: "Lentitud", sub: "Procesos lentos y mucho papeleo" },
        { p: "S", t: "Conflicto", sub: "Peleas y un ambiente hostil" },
        { p: "E", t: "Superficialidad", sub: "Falta de profundidad" },
      ],
    },
    {
      pergunta: "¿Cuál es tu mayor fortaleza personal?",
      cartas: [
        { p: "B", t: "Disciplina", sub: "Constancia y compromiso" },
        { p: "A", t: "Liderazgo", sub: "Influir y mover a las personas" },
        { p: "S", t: "Cuidado", sub: "Apoyar y ayudar a crecer a otros" },
        { p: "E", t: "Visión", sub: "Ver más allá de lo obvio" },
      ],
    },
    {
      pergunta: "¿Qué te da más satisfacción al final del día?",
      cartas: [
        { p: "B", t: "Cumplimiento", sub: "Terminar todo lo que planeé" },
        { p: "A", t: "Logro", sub: "Haber superado un reto" },
        { p: "S", t: "Impacto", sub: "Haber ayudado de verdad a alguien" },
        { p: "E", t: "Aprendizaje", sub: "Haber descubierto algo nuevo" },
      ],
    },
  ],

  BASE_POSICOES: [
    "1.ª posición · Tu motor principal",
    "2.ª posición · Tu influencia secundaria",
    "3.ª posición · Cómo actúas bajo estrés",
    "4.ª posición · Tus valores menos prioritarios",
  ],

  BASE_PERFIS: {
    B: {
      nome: "Brújula",
      titulo: "El Guardián de los Sistemas",
      tagline: "Eres el ancla que mantiene todo en su lugar. Responsable, detallista y ordenado, tu fuerza está en crear sistemas confiables, cumplir tus compromisos y asegurar que cada pieza funcione con precisión. Cuando das tu palabra, la cumples.",
      resumo: "Las personas con perfil Brújula ponen la responsabilidad en primer lugar. Vives con un código moral interno fuerte, respetas las reglas, las tradiciones y la autoridad, y esperas lo mismo de los demás. Detallista y ordenado, conviertes el caos en orden con mucha habilidad. Tu capacidad de planificar, organizar y cumplir con disciplina te hace una de las personas más confiables de cualquier equipo. Prefieres analizar con cuidado antes de actuar, trabajas mejor con plazos definidos y sistemas claros, y te destacas en logística, gestión y puesta en marcha. Para ti, la constancia no es una limitación, es excelencia.",
      fortes: ["Organizado y detallista", "Disciplinado y constante", "Experto en planificar", "Comprometido con cumplir", "Eficiente para poner en marcha", "Piensa paso a paso", "Confiable y responsable", "Gestión y logística"],
      gatilhos: ["Personas profesionales que llegan preparadas y puntuales.", "Ambientes con reglas claras y expectativas bien definidas.", "Quien cumple lo que promete, sin excepciones ni excusas.", "Sistemas ordenados, documentación y procesos bien armados.", "Quien muestra credenciales, referencias y experiencia comprobada.", "Planes con pasos claros, plazos realistas y presupuesto definido.", "Quien presenta un plan paso a paso para lograr el éxito.", "Tradiciones, métodos probados y respeto a la jerarquía.", "Reuniones eficientes con agenda clara y resultados concretos.", "Quien reduce los riesgos con hechos y pruebas que se pueden verificar."],
      repulsores: ["Imprevistos y cambios de último momento sin una buena razón.", "Personas desordenadas que improvisan y no siguen los procesos.", "Quien promete y no cumple, o cambia los planes sin avisar.", "Ambientes caóticos sin estructura, sistemas ni responsabilidades claras.", "Quien no respeta la jerarquía, las reglas ni la autoridad establecida.", "Decisiones impulsivas tomadas sin suficiente análisis o datos.", "Personas que no respetan plazos, compromisos ni presupuestos.", "Desperdicio de recursos o falta de planificación financiera.", "Quien es demasiado emocional o sensible al decidir.", "Falta de profesionalismo y de atención a los detalles."],
      posicoes: [
        "Con Brújula en la primera posición, la estructura, la responsabilidad y la planificación son lo que más impulsa tus decisiones. Lideras con orden y confiabilidad.",
        "Brújula en la segunda posición significa que eres muy capaz en organización y procesos, y usas esas habilidades para apoyar tu perfil principal en el día a día.",
        "Bajo estrés, tiendes a pasar al modo Brújula, buscando control, sistemas y planificación para volver a sentirte seguro.",
        "Los valores de Brújula como la tradición, la jerarquía y los sistemas rígidos son los menos prioritarios para ti. Prefieres la flexibilidad a las reglas fijas.",
      ],
      comunicacao: {
        A: ["Muestra entusiasmo y energía, y presenta la oportunidad con confianza.", "Ve directo al punto, muestra el resultado y el impacto inmediato.", "Evita los detalles de más, enfócate en el estilo de vida y el sueño.", "Preséntale personas influyentes y exitosas de tus contactos.", "Transmite sentido de urgencia: recuerda que el tiempo es dinero.", "Muestra seguridad y buena autoestima al presentar."],
        S: ["Muestra que de verdad te importan las personas, más allá del negocio.", "Comparte historias reales de cambio e impacto humano.", "Construye la relación personal antes de hablar de negocios o números.", "Muestra cómo tu propuesta se conecta con valores, propósito y misión.", "Sé auténtico, habla de tu historia personal y de lo que te motiva.", "Pregúntale por su vida personal (familia, pasatiempos, pasiones)."],
        E: ["Presenta datos, estudios y pruebas concretas, sé inteligente.", "Dale tiempo para analizar y procesar la información antes de decidir.", "Prepárate para debatir y defender tu postura con lógica.", "Mantente racional, evita exagerar con emociones o demasiado entusiasmo.", "Entrega documentación, recursos y datos para estudiar a fondo.", "Mantente abierto a escuchar su punto de vista y ver el panorama completo."],
      },
    },
    A: {
      nome: "Activo",
      titulo: "El Realizador Imparable",
      tagline: "No te da miedo arriesgarte y siempre estás buscando la próxima gran oportunidad. Tu energía, tu confianza y tus ganas de actuar te hacen un líder natural que pone todo en movimiento a donde vayas.",
      resumo: "Las personas con perfil Activo se mueven por la acción, la competencia y las ganas constantes de ganar. Eres el primero en levantarse cuando aparece una oportunidad y el último en rendirse ante un reto. No te da miedo tomar riesgos y siempre buscas maneras de cambiar y mejorar las cosas. Tu flexibilidad, tu capacidad de improvisar y tu talento para poner todo en movimiento te hacen una fuerza de la naturaleza en negociaciones, ventas y liderazgo. Piensas rápido, actúas todavía más rápido e inspiras a quienes te rodean con tu seguridad y tu visión de futuro. Si algo grande va a pasar, tú quieres ser el protagonista.",
      fortes: ["Enfocado en resultados y en ganar", "Decidido y rápido para actuar", "Competitivo y ambicioso", "Líder natural y carismático", "Pone todo en movimiento", "Resiliente en las crisis", "Persuasivo y con presencia", "Flexible y buen improvisador"],
      gatilhos: ["Oportunidades de ser el primero, el mejor o el más grande.", "Ambientes dinámicos que valoran la rapidez, la acción y los resultados.", "Reconocimiento público por logros y desempeño.", "Quien presenta ideas con energía, entusiasmo y visión de impacto.", "Hacer contactos con personas influyentes, poderosas y exitosas.", "Retos que a otros les parecen imposibles: cuanto más grandes, mejor.", "Imagen, estilo y presencia que transmitan éxito y confianza.", "Total libertad para actuar sin papeleo ni control excesivo.", "Diversión, estilo de vida y experiencias que alimenten el sueño.", "Sentido de urgencia y oportunidades exclusivas."],
      repulsores: ["Procesos lentos, papeleo y demasiada planificación sin acción.", "Reuniones largas sin decisión, sin resultado claro ni objetivo definido.", "Personas que cuestionan demasiado, analizan demasiado y nunca actúan.", "Ambientes que limitan la creatividad, la iniciativa y la autonomía.", "Falta de reconocimiento por el esfuerzo, los logros y el desempeño.", "Presentaciones aburridas, sin energía y sin visión.", "Control excesivo que te ahoga y te quita libertad para actuar.", "Demasiados detalles, datos e historias cuando quieres la conclusión.", "Personas miedosas que no se atreven a arriesgar ni a decidir.", "Quien no tiene autoestima ni confianza en lo que presenta."],
      posicoes: [
        "Con Activo en la primera posición, la acción, la competencia y los resultados son el combustible de tus decisiones. Lideras con energía y ganas de ganar.",
        "Activo en la segunda posición le suma dinamismo y rapidez a tu perfil principal. Sabes cuándo es momento de actuar y poner todo en movimiento.",
        "Bajo estrés, pasas al modo Activo: buscas actuar de inmediato, tomas decisiones rápidas y te haces cargo de la situación.",
        "Los valores de Activo como la competencia, el riesgo y las decisiones impulsivas son los menos importantes para ti. Prefieres pensarlo antes de actuar.",
      ],
      comunicacao: {
        B: ["Sé ordenado y profesional, y presenta un plan claro paso a paso.", "Llega de 15 a 30 minutos antes: la puntualidad es respeto.", "Entrega hechos, pruebas, referencias y credenciales que se puedan verificar.", "Reduce los riesgos con datos y sistemas comprobados.", "No seas demasiado emocional o sensible, muestra el sistema.", "Respeta el presupuesto y mantente dentro de los límites acordados."],
        S: ["Construye de verdad la relación humana antes de cualquier oferta.", "Muestra empatía e interés real por su historia personal.", "Conecta tu propuesta con un impacto social y un propósito mayor.", "Sé auténtico y transparente, evita sonar como vendedor o falso.", "Comparte historias reales de vidas transformadas y de impacto.", "Preséntale a miembros de tu equipo y crea sentido de comunidad."],
        E: ["Presenta una lógica sólida, datos concretos y razones bien fundadas.", "Dale espacio y tiempo para analizar, nunca lo presiones a decidir rápido.", "Prepárate para conversaciones técnicas y debates a fondo.", "Entrega pruebas y deja que haga todas las preguntas que quiera.", "Mantente racional y abierto a ver el panorama completo.", "Vístete bien y muestra nivel intelectual."],
      },
    },
    S: {
      nome: "Sensible",
      titulo: "El Constructor de Puentes",
      tagline: "Pones a las personas en primer lugar. Tu presencia ilumina cualquier lugar, crea comunidad donde no la había y despierta en los demás un potencial que ni sabían que tenían. Las conexiones sinceras son tu superpoder.",
      resumo: "Las personas con perfil Sensible se guían por la empatía, la autenticidad y un deseo profundo de hacer el bien a quienes las rodean. Eres amigable, acogedor y abierto, y haces que todos se sientan parte de la comunidad. Las relaciones son tu prioridad y siempre buscas una conexión sincera y profunda. Ayudar a las personas a ser su mejor versión es lo que te mueve. Aunque el trabajo y el dinero importan, sabes que en la vida hay mucho más y siempre buscas un sentido más profundo. Evitas la competencia excesiva y los conflictos, y prefieres animar a los equipos a apoyarse entre sí. Nadie es tan hábil como tú para resolver problemas con diplomacia y despertar el potencial escondido de las personas.",
      fortes: ["Empático y acogedor", "Se mueve por propósito y sentido", "Despierta el potencial de otros", "Diplomático y crea armonía", "Siempre auténtico y sincero", "Guía y mentor natural", "Intuye lo que otros necesitan", "Enfocado en el impacto humano"],
      gatilhos: ["Quien participa en causas sociales y de la comunidad, más allá de su trabajo.", "Personas apasionadas por lo que hacen, con un propósito claro y verdadero.", "Quien crea un sentido real de comunidad y pertenencia.", "Energía cálida, amigable y de verdad humana.", "Quien hace un esfuerzo extra para mostrar cuidado, gratitud y reconocimiento.", "Conectar por historias, intereses y experiencias en común.", "Quien busca entender a cada persona como alguien único.", "Quien te presenta a su equipo y te incluye en la comunidad.", "Preguntas sobre tu historia personal, tu familia, tus pasatiempos y pasiones.", "Personas accesibles, simpáticas y que tratan a todos por igual."],
      repulsores: ["Personas a las que parece importarles más el dinero que la gente.", "Ambientes de competencia excesiva, agresividad y frialdad.", "Quien se muestra falso o poco auténtico.", "Personas groseras, maleducadas o sin amabilidad básica.", "Quien no intenta entender a los demás como personas únicas.", "Quien no comparte historias y experiencias de clientes y personas.", "Personas que olvidan detalles personales importantes (cumpleaños, familia).", "Falta de integridad moral y de valores éticos altos.", "Quien no comparte lo que siente, su propósito o su razón de ser.", "Personas egocéntricas, sin humildad ni empatía."],
      posicoes: [
        "Con Sensible en la primera posición, las personas, la conexión y el propósito humano guían todas tus decisiones. Lideras con empatía y autenticidad.",
        "Sensible en la segunda posición enriquece tu perfil con inteligencia emocional y la capacidad de crear conexiones sinceras en cualquier situación.",
        "Bajo estrés, pasas al modo Sensible: buscas apoyo emocional, armonía y volver a conectar con las personas que te rodean.",
        "Los valores de Sensible como la armonía a toda costa y evitar los conflictos no son tu prioridad. Puedes ser más directo cuando hace falta.",
      ],
      comunicacao: {
        B: ["Sé ordenado, profesional y puntual, y llega preparado.", "Presenta un plan claro con etapas definidas, paso a paso.", "Entrega hechos, pruebas y referencias, y reduce los riesgos.", "No seas demasiado emocional o sensible al presentar.", "Muestra el sistema para el éxito con datos y credenciales.", "Respeta el presupuesto y muestra responsabilidad con el dinero."],
        A: ["Muestra entusiasmo, energía y confianza, y ve directo al punto.", "Presenta la oportunidad de ganar y una ventaja clara frente a otros.", "Conéctalo con personas influyentes y poderosas de tus contactos.", "Enfócate en el impacto, el resultado y el estilo de vida, no en el proceso.", "Transmite una urgencia real: para esta persona el tiempo es dinero.", "Muestra seguridad, buena autoestima y diviértete."],
        E: ["Presenta datos concretos, razonamiento lógico y pruebas sólidas.", "Mantente objetivo, evita exagerar con emociones o dramas.", "Dale espacio y tiempo para analizar antes de pedir cualquier decisión.", "Usa palabras precisas y entrega documentación para estudiar.", "Mantente abierto al debate y dispuesto a ver el panorama completo.", "Muestra profundidad intelectual y dominio del tema."],
      },
    },
    E: {
      nome: "Estudioso",
      titulo: "El Arquitecto de Ideas",
      tagline: "Tu mente es tu mejor herramienta. Valoras la razón por encima de todo y tomas decisiones con base en hechos y ciencia, nunca en emociones. Ves patrones donde otros solo ven información y conviertes lo complicado en estrategia.",
      resumo: "Las personas con perfil Estudioso se mueven por la lógica, el aprendizaje constante y la búsqueda de soluciones nuevas. No te conformas con respuestas superficiales: quieres entender el porqué profundo de cada cosa. Tomas decisiones con base en hechos y ciencia, nunca en emociones, y te destacas al analizar datos, planear a largo plazo y encontrar errores que otros no ven. Tu capacidad de pensar en ideas abstractas, de ver el sistema completo y de hablar con precisión te hace una fuente inagotable de conocimiento. Muchas veces disfrutas más el proceso de aprender que actuar con la información. Creativo y visionario, siempre buscas una mejor forma de hacer las cosas y, cuando la encuentras, creas modelos, diagramas y teorías que cambian la manera de pensar.",
      fortes: ["Analítico y lógico", "Innovador y visionario", "Piensa en sistemas e ideas abstractas", "Aprende toda la vida", "Estratega a largo plazo", "Preciso al hablar y al pensar", "Resuelve problemas difíciles", "Crea modelos y teorías"],
      gatilhos: ["Conversaciones que hacen pensar y debates a fondo.", "Quien presenta datos sólidos, estudios y razonamiento lógico.", "Tecnología de punta, innovación y soluciones que desafían lo de siempre.", "Espacio y tiempo para analizar antes de tomar cualquier decisión.", "Quien domina a fondo el tema que presenta, con experiencia real.", "Proyectos con complejidad y un verdadero reto intelectual.", "Precisión al hablar, información coherente y atención a los detalles.", "Quien respeta que necesitas tiempo para pensar y procesar.", "Recursos, documentación y datos para estudiar a fondo.", "Personas refinadas, inteligentes y con una presencia elegante."],
      repulsores: ["Información superficial o argumentos sin fundamento.", "Quien pide una decisión rápida sin datos, sin análisis o sin tiempo suficiente.", "Exageraciones emocionales, entusiasmo vacío y dramas innecesarios.", "Ambientes que no valoran la experiencia, el conocimiento ni la profundidad.", "Quien no está abierto al debate, a las preguntas ni a otros puntos de vista.", "Promesas exageradas sin pruebas concretas ni casos verificables.", "Reuniones improductivas sin agenda, sin objetivo claro ni resultado concreto.", "Demasiados detalles personales, historias y dramas cuando quieres lógica.", "Personas que no admiten cuando no saben algo, falta de humildad intelectual.", "Quien intenta manipular con emociones en lugar de convencer con razones."],
      posicoes: [
        "Con Estudioso en la primera posición, la lógica, los datos y el aprendizaje constante dominan tu forma de decidir. Lideras con razón y visión estratégica.",
        "Estudioso en la segunda posición le da a tu perfil principal profundidad para analizar y visión del sistema completo, y enriquece tus decisiones.",
        "Bajo estrés, pasas al modo Estudioso: te sumerges en el análisis, buscas datos e intentas entender la situación con la razón antes de reaccionar.",
        "Los valores de Estudioso como el análisis excesivo y la búsqueda de la perfección intelectual son los menos prioritarios. Prefieres actuar a analizar sin fin.",
      ],
      comunicacao: {
        B: ["Sé ordenado y puntual, y presenta documentación completa.", "Muestra el sistema, el proceso y el paso a paso detrás de la propuesta.", "Entrega hechos y pruebas, y reduce los riesgos con evidencias concretas.", "Respeta la necesidad de procesos, jerarquía y tradición.", "Presenta referencias, credenciales y casos comprobados.", "Mantente dentro del presupuesto y muestra responsabilidad."],
        A: ["Muestra entusiasmo y energía, y presenta la oportunidad con confianza.", "Enfócate en ganar, en el resultado y en el estilo de vida, no en los detalles.", "Ve directo a la conclusión, evita la charla de más y el exceso de datos.", "Conéctalo con personas influyentes y exitosas de tus contactos.", "Crea urgencia: presenta la oportunidad como algo exclusivo y por tiempo limitado.", "Muestra seguridad, sé divertido y ten una autoestima sana."],
        S: ["Construye la relación humana con autenticidad e interés sincero.", "Comparte el propósito, la misión y el impacto humano detrás del negocio.", "Muestra cómo tu propuesta mejora la vida de las personas.", "Demuestra que te importa como ser humano, no como cliente.", "Usa historias reales de cambio, impacto y vidas transformadas como prueba.", "Pregúntale por su familia, sus pasiones y su historia personal."],
      },
    },
  },

  PAISES_NOMES: {
    "Angola": "Angola",
    "Brasil": "Brasil",
    "Espanha": "España",
    "Estados Unidos": "Estados Unidos",
    "França": "Francia",
    "Portugal": "Portugal",
  },

  ESCALA_NIVEIS: [
    { v: 0, rot: "0 · No lo tengo" },
    { v: 1, rot: "1 · Básico" },
    { v: 2, rot: "2 · En desarrollo" },
    { v: 3, rot: "3 · Intermedio" },
    { v: 4, rot: "4 · Avanzado" },
    { v: 5, rot: "5 · Experto" },
  ],

  TIPOS_COMPETENCIA: {
    tecnica: "Técnica",
    relacional: "Trato con personas",
    formacao: "Estudios / Certificación",
    experiencia: "Experiencia",
  },
};
