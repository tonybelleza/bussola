/* =====================================================================
   Portal de onboarding do novo contratado (/onboarding?t=TOKEN).
   Idioma: ?lang, depois o idioma salvo do onboarding, depois o navegador.
   Etapas: carta de proposta, dados pessoais, documentos para assinar,
   formulários fiscais (montados a partir de formularios.CAMPOS), envio de
   documentos, forma de pagamento e revisão. Consentimento ESIGN/UETA no início.
   API: /api/onboarding/<token>[/consentimento|assinar|dados|formulario/<tipo>|
   arquivo|pagamento|concluir|idioma].
   ===================================================================== */

const OB_IDIOMAS = ["pt", "en", "es"];
const OB_LOCALE = { pt: "pt-BR", en: "en-US", es: "es" };

const OB_TXT = {
  pt: {
    carregando: "Carregando…", ola: "Olá, {nome}!", intro: "Bem-vindo(a) à {empresa}. Complete as etapas abaixo para concluir a sua contratação.",
    progresso: "{pct}% concluído", prazo: "Prazo: {data}", voltar: "Voltar", continuar: "Continuar", salvar: "Salvar",
    salvando: "Salvando…", feito: "Concluído", pendente: "Pendente", abrir: "Abrir",
    etapas: { oferta: "Carta de proposta", dados: "Dados pessoais", documentos: "Documentos para assinar",
      formularios: "Formulários fiscais", arquivos: "Envio de documentos", pagamento: "Forma de pagamento", revisao: "Revisão e envio" },
    porque: {
      oferta: "Revise a proposta e assine para aceitar.",
      dados: "Usados na folha de pagamento, em emergências e na sua ficha de colaborador.",
      documentos: "Documentos da empresa que precisam da sua assinatura.",
      formularios: "Exigidos pelo IRS e pelo estado para calcular a retenção de impostos e confirmar a autorização de trabalho.",
      arquivos: "A lei federal exige confirmar a identidade e a autorização de trabalho (Formulário I-9).",
      pagamento: "Para a empresa saber como pagar você.",
      revisao: "Confira tudo e envie.",
    },
    cons_titulo: "Antes de começar", cons_aceito: "Concordo em usar documentos e assinaturas eletrônicas.", cons_botao: "Concordar e começar",
    oferta_cargo: "Cargo", oferta_inicio: "Início", oferta_pagamento: "Pagamento", oferta_horario: "Horário", oferta_notas: "Observações",
    oferta_tipo: "Vínculo", tipo_w2: "Empregado (W-2)", tipo_1099: "Prestador independente (1099)",
    unidades: { hora: "por hora", dia: "por dia", servico: "por serviço", salario: "por ano (salário)" },
    so_ingles: "Este documento está em inglês. A versão em inglês é a oficial. Se tiver dúvidas, fale com a empresa antes de assinar.",
    rolar: "Role o documento até o fim para poder assinar.", declaracao: "Sua declaração pessoal", declaracao_ph: "Escreva algumas frases…",
    nome_completo: "Digite o seu nome completo (assinatura digitada)", desenhe: "Desenhe a sua assinatura no quadro", limpar: "Limpar",
    dica_assin: "Assine aqui com o dedo ou o mouse", assinar: "Assinar", assinando: "Assinando…", assinado_em: "Assinado em {data}",
    baixar: "Baixar PDF", abrir_pdf: "Abrir o documento (PDF)", abrir_pdf_antes: "Abra o documento antes de assinar.",
    falta_assin: "Desenhe a sua assinatura.", falta_aceite: "Marque a caixa de concordância.", falta_nome: "Digite o seu nome completo.",
    falta_decl: "Escreva a sua declaração pessoal.",
    d_nome_legal: "Nome legal completo", d_nome_preferido: "Como prefere ser chamado(a) (opcional)", d_endereco: "Endereço (rua e número)",
    d_apto: "Apto / unidade (opcional)", d_cidade: "Cidade", d_estado: "Estado (sigla, ex.: CT)", d_cep: "ZIP code", d_telefone: "Telefone",
    d_email: "E-mail", d_nascimento: "Data de nascimento", d_contato: "Contato de emergência", d_contato_nome: "Nome",
    d_contato_relacao: "Parentesco ou relação", d_contato_telefone: "Telefone", d_tamanho: "Tamanho do uniforme / camiseta",
    d_cnh: "Carteira de motorista (o cargo dirige entre as casas)", d_cnh_numero: "Número da carteira", d_cnh_estado: "Estado emissor",
    d_ja_salvo: "Já informado ({m}). Deixe em branco para manter.", d_escolha: "Escolha…",
    erro_campo: "Confira este campo", f_indisponivel: "Os formulários fiscais ainda não estão disponíveis. Tente mais tarde ou fale com a empresa.",
    f_assinar_titulo: "Assinatura do formulário", f_aceite: "Declaro, sob as penas da lei, que as informações acima são verdadeiras e corretas, e assino eletronicamente.",
    f_titulos: { w4: "Formulário W-4 (retenção federal)", w9: "Formulário W-9 (prestador)", i9: "Formulário I-9, Seção 1", ctw4: "Formulário CT-W4 (retenção de Connecticut)" },
    f_refazer: "Preencher de novo", f_feito: "Preenchido e assinado",
    up_titulo: { id_frente: "Documento com foto (frente)", id_verso: "Documento com foto (verso)", cnh_frente: "Carteira de motorista (frente)",
      cnh_verso: "Carteira de motorista (verso)", i9_lista_a: "I-9 Lista A (um documento)", i9_lista_b: "I-9 Lista B (identidade)",
      i9_lista_c: "I-9 Lista C (autorização de trabalho)", comprovante_endereco: "Comprovante de endereço", cheque_anulado: "Cheque anulado (voided check)" },
    up_obrigatorio: "Obrigatório", up_opcional: "Opcional", up_enviar: "Enviar foto ou PDF", up_enviando: "Enviando…", up_remover: "Remover",
    up_grande: "O arquivo passa de 10 MB.", up_i9: "Para o I-9, envie UM documento da Lista A (ex.: passaporte dos EUA, green card) OU um da Lista B (ex.: carteira de motorista) MAIS um da Lista C (ex.: cartão do Seguro Social, certidão de nascimento). Leve os originais no primeiro dia.",
    up_i9_falta: "Falta o I-9: Lista A, ou Lista B mais Lista C.", up_ver: "Ver",
    p_metodos: { deposito: "Depósito direto", zelle: "Zelle", cheque: "Cheque em papel", provedor: "Pelo sistema de folha ({p})" },
    p_porque: { deposito: "O pagamento cai direto na sua conta no dia do pagamento. Precisamos do routing e do número da conta para enviar.",
      zelle: "Enviamos o pagamento para o e-mail ou telefone ligado ao seu Zelle.",
      cheque: "Você recebe um cheque em papel. Precisamos de um endereço correto para correspondência.",
      provedor: "Você vai receber um convite do {p} para cadastrar os dados de pagamento diretamente com eles." },
    p_banco: "Nome do banco", p_tipo: "Tipo de conta", p_corrente: "Corrente (checking)", p_poupanca: "Poupança (savings)",
    p_routing: "Routing number (9 dígitos)", p_conta: "Número da conta", p_conta2: "Confirme o número da conta",
    p_ja_salvo: "Já informado: routing {r}, conta {c}. Deixe em branco para manter.", p_cheque_anulado: "Cheque anulado (opcional)",
    p_zelle: "E-mail ou telefone do Zelle", p_endereco_ok: "Confirmo que o meu endereço nos dados pessoais está correto para receber o cheque.",
    p_endereco_outro: "Outro endereço para o cheque (opcional)", p_provedor_ok: "Entendi que vou cadastrar os dados de pagamento pelo convite do {p}.",
    p_routing_invalido: "Routing number inválido. Confira os 9 dígitos.",
    r_titulo: "Revisão", r_tudo: "Tudo pronto! Envie para a empresa.", r_faltam: "Ainda faltam etapas:", r_enviar: "Enviar onboarding",
    r_enviando: "Enviando…", fim_titulo: "Onboarding concluído", fim_desc: "Obrigado! A empresa recebeu tudo e vai entrar em contato com os próximos passos.",
    fim_docs: "Seus documentos", cancelado: "Este onboarding foi cancelado. Fale com a empresa se tiver dúvidas.",
    link_invalido: "Este link de onboarding não é válido. Confira o e-mail que você recebeu.",
    erro: "Não foi possível concluir. Tente de novo.", sim: "Sim", nao: "Não", proximo: "Próxima etapa",
  },
  en: {
    carregando: "Loading…", ola: "Hi {nome}!", intro: "Welcome to {empresa}. Complete the steps below to finish your hiring.",
    progresso: "{pct}% complete", prazo: "Deadline: {data}", voltar: "Back", continuar: "Continue", salvar: "Save",
    salvando: "Saving…", feito: "Done", pendente: "To do", abrir: "Open",
    etapas: { oferta: "Offer letter", dados: "Personal info", documentos: "Documents to sign",
      formularios: "Tax forms", arquivos: "Document uploads", pagamento: "Payment setup", revisao: "Review and submit" },
    porque: {
      oferta: "Review your offer and sign to accept it.",
      dados: "Used for payroll, emergencies, and your employee file.",
      documentos: "Company documents that need your signature.",
      formularios: "Required by the IRS and the state to calculate tax withholding and confirm work authorization.",
      arquivos: "Federal law requires verifying identity and work authorization (Form I-9).",
      pagamento: "So the company knows how to pay you.",
      revisao: "Check everything and submit.",
    },
    cons_titulo: "Before you start", cons_aceito: "I agree to use electronic records and signatures.", cons_botao: "Agree and start",
    oferta_cargo: "Position", oferta_inicio: "Start date", oferta_pagamento: "Pay", oferta_horario: "Schedule", oferta_notas: "Notes",
    oferta_tipo: "Type", tipo_w2: "Employee (W-2)", tipo_1099: "Independent contractor (1099)",
    unidades: { hora: "per hour", dia: "per day", servico: "per service", salario: "per year (salary)" },
    so_ingles: "This document is in English. The English version is the official one. If you have questions, ask the company before signing.",
    rolar: "Scroll to the end of the document to sign.", declaracao: "Your personal statement", declaracao_ph: "Write a few sentences…",
    nome_completo: "Type your full legal name (typed signature)", desenhe: "Draw your signature in the box", limpar: "Clear",
    dica_assin: "Sign here with your finger or mouse", assinar: "Sign", assinando: "Signing…", assinado_em: "Signed on {data}",
    baixar: "Download PDF", abrir_pdf: "Open the document (PDF)", abrir_pdf_antes: "Open the document before signing.",
    falta_assin: "Please draw your signature.", falta_aceite: "Please check the agreement box.", falta_nome: "Please type your full name.",
    falta_decl: "Please write your personal statement.",
    d_nome_legal: "Full legal name", d_nome_preferido: "Preferred name (optional)", d_endereco: "Street address",
    d_apto: "Apt / unit (optional)", d_cidade: "City", d_estado: "State (e.g., CT)", d_cep: "ZIP code", d_telefone: "Phone",
    d_email: "Email", d_nascimento: "Date of birth", d_contato: "Emergency contact", d_contato_nome: "Name",
    d_contato_relacao: "Relationship", d_contato_telefone: "Phone", d_tamanho: "T-shirt / uniform size",
    d_cnh: "Driver's license (this position drives between homes)", d_cnh_numero: "License number", d_cnh_estado: "Issuing state",
    d_ja_salvo: "Already provided ({m}). Leave blank to keep it.", d_escolha: "Choose…",
    erro_campo: "Please check this field", f_indisponivel: "Tax forms are not available yet. Please try again later or contact the company.",
    f_assinar_titulo: "Sign the form", f_aceite: "Under penalties of perjury, I declare that the information above is true and correct, and I sign electronically.",
    f_titulos: { w4: "Form W-4 (federal withholding)", w9: "Form W-9 (contractor)", i9: "Form I-9, Section 1", ctw4: "Form CT-W4 (Connecticut withholding)" },
    f_refazer: "Fill out again", f_feito: "Completed and signed",
    up_titulo: { id_frente: "Photo ID (front)", id_verso: "Photo ID (back)", cnh_frente: "Driver's license (front)",
      cnh_verso: "Driver's license (back)", i9_lista_a: "I-9 List A (one document)", i9_lista_b: "I-9 List B (identity)",
      i9_lista_c: "I-9 List C (work authorization)", comprovante_endereco: "Proof of address", cheque_anulado: "Voided check" },
    up_obrigatorio: "Required", up_opcional: "Optional", up_enviar: "Upload photo or PDF", up_enviando: "Uploading…", up_remover: "Remove",
    up_grande: "The file is larger than 10 MB.", up_i9: "For Form I-9, upload ONE List A document (for example, a U.S. passport or a green card) OR one List B document (for example, a driver's license) PLUS one List C document (for example, a Social Security card or a birth certificate). Bring the originals on your first day.",
    up_i9_falta: "I-9 still missing: List A, or List B plus List C.", up_ver: "View",
    p_metodos: { deposito: "Direct deposit", zelle: "Zelle", cheque: "Paper check", provedor: "Through the payroll provider ({p})" },
    p_porque: { deposito: "Your pay goes straight to your bank account on payday. We need the routing and account numbers to send it.",
      zelle: "We send your pay to the email or phone number linked to your Zelle.",
      cheque: "You receive a paper check. We need a correct mailing address.",
      provedor: "You will get an invitation from {p} to enter your payment details directly with them." },
    p_banco: "Bank name", p_tipo: "Account type", p_corrente: "Checking", p_poupanca: "Savings",
    p_routing: "Routing number (9 digits)", p_conta: "Account number", p_conta2: "Confirm account number",
    p_ja_salvo: "Already provided: routing {r}, account {c}. Leave blank to keep them.", p_cheque_anulado: "Voided check (optional)",
    p_zelle: "Zelle email or phone", p_endereco_ok: "I confirm that the address in my personal info is correct for mailing my check.",
    p_endereco_outro: "Different mailing address for the check (optional)", p_provedor_ok: "I understand I will enter my payment details through the {p} invitation.",
    p_routing_invalido: "Invalid routing number. Please check the 9 digits.",
    r_titulo: "Review", r_tudo: "All set! Submit it to the company.", r_faltam: "Steps still open:", r_enviar: "Submit onboarding",
    r_enviando: "Submitting…", fim_titulo: "Onboarding complete", fim_desc: "Thank you! The company received everything and will reach out with next steps.",
    fim_docs: "Your documents", cancelado: "This onboarding was canceled. Please contact the company if you have questions.",
    link_invalido: "This onboarding link isn't valid. Please check the email you received.",
    erro: "Something went wrong. Please try again.", sim: "Yes", nao: "No", proximo: "Next step",
  },
  es: {
    carregando: "Cargando…", ola: "¡Hola, {nome}!", intro: "Bienvenido(a) a {empresa}. Completa los pasos de abajo para terminar tu contratación.",
    progresso: "{pct}% completado", prazo: "Fecha límite: {data}", voltar: "Volver", continuar: "Continuar", salvar: "Guardar",
    salvando: "Guardando…", feito: "Listo", pendente: "Pendiente", abrir: "Abrir",
    etapas: { oferta: "Carta de oferta", dados: "Datos personales", documentos: "Documentos para firmar",
      formularios: "Formularios de impuestos", arquivos: "Envío de documentos", pagamento: "Forma de pago", revisao: "Revisión y envío" },
    porque: {
      oferta: "Revisa tu oferta y fírmala para aceptarla.",
      dados: "Se usan para la nómina, emergencias y tu expediente de empleado.",
      documentos: "Documentos de la empresa que necesitan tu firma.",
      formularios: "Los exigen el IRS y el estado para calcular la retención de impuestos y confirmar la autorización de trabajo.",
      arquivos: "La ley federal exige verificar la identidad y la autorización de trabajo (Formulario I-9).",
      pagamento: "Para que la empresa sepa cómo pagarte.",
      revisao: "Revisa todo y envíalo.",
    },
    cons_titulo: "Antes de empezar", cons_aceito: "Acepto usar documentos y firmas electrónicas.", cons_botao: "Aceptar y empezar",
    oferta_cargo: "Puesto", oferta_inicio: "Inicio", oferta_pagamento: "Pago", oferta_horario: "Horario", oferta_notas: "Notas",
    oferta_tipo: "Tipo", tipo_w2: "Empleado (W-2)", tipo_1099: "Contratista independiente (1099)",
    unidades: { hora: "por hora", dia: "por día", servico: "por servicio", salario: "por año (salario)" },
    so_ingles: "Este documento está en inglés. La versión en inglés es la oficial. Si tienes dudas, consulta con la empresa antes de firmar.",
    rolar: "Desplázate hasta el final del documento para poder firmar.", declaracao: "Tu declaración personal", declaracao_ph: "Escribe algunas frases…",
    nome_completo: "Escribe tu nombre legal completo (firma escrita)", desenhe: "Dibuja tu firma en el recuadro", limpar: "Borrar",
    dica_assin: "Firma aquí con el dedo o el mouse", assinar: "Firmar", assinando: "Firmando…", assinado_em: "Firmado el {data}",
    baixar: "Descargar PDF", abrir_pdf: "Abrir el documento (PDF)", abrir_pdf_antes: "Abre el documento antes de firmar.",
    falta_assin: "Dibuja tu firma.", falta_aceite: "Marca la casilla de aceptación.", falta_nome: "Escribe tu nombre completo.",
    falta_decl: "Escribe tu declaración personal.",
    d_nome_legal: "Nombre legal completo", d_nome_preferido: "Cómo prefieres que te llamen (opcional)", d_endereco: "Dirección (calle y número)",
    d_apto: "Apto / unidad (opcional)", d_cidade: "Ciudad", d_estado: "Estado (ej.: CT)", d_cep: "Código postal (ZIP)", d_telefone: "Teléfono",
    d_email: "Correo electrónico", d_nascimento: "Fecha de nacimiento", d_contato: "Contacto de emergencia", d_contato_nome: "Nombre",
    d_contato_relacao: "Parentesco o relación", d_contato_telefone: "Teléfono", d_tamanho: "Talla de camiseta / uniforme",
    d_cnh: "Licencia de conducir (este puesto maneja entre casas)", d_cnh_numero: "Número de licencia", d_cnh_estado: "Estado emisor",
    d_ja_salvo: "Ya informado ({m}). Déjalo en blanco para mantenerlo.", d_escolha: "Elige…",
    erro_campo: "Revisa este campo", f_indisponivel: "Los formularios de impuestos aún no están disponibles. Intenta más tarde o comunícate con la empresa.",
    f_assinar_titulo: "Firma del formulario", f_aceite: "Declaro, bajo pena de perjurio, que la información anterior es verdadera y correcta, y firmo electrónicamente.",
    f_titulos: { w4: "Formulario W-4 (retención federal)", w9: "Formulario W-9 (contratista)", i9: "Formulario I-9, Sección 1", ctw4: "Formulario CT-W4 (retención de Connecticut)" },
    f_refazer: "Llenar de nuevo", f_feito: "Completado y firmado",
    up_titulo: { id_frente: "Identificación con foto (frente)", id_verso: "Identificación con foto (reverso)", cnh_frente: "Licencia de conducir (frente)",
      cnh_verso: "Licencia de conducir (reverso)", i9_lista_a: "I-9 Lista A (un documento)", i9_lista_b: "I-9 Lista B (identidad)",
      i9_lista_c: "I-9 Lista C (autorización de trabajo)", comprovante_endereco: "Comprobante de domicilio", cheque_anulado: "Cheque anulado (voided check)" },
    up_obrigatorio: "Obligatorio", up_opcional: "Opcional", up_enviar: "Subir foto o PDF", up_enviando: "Subiendo…", up_remover: "Quitar",
    up_grande: "El archivo supera los 10 MB.", up_i9: "Para el I-9, sube UN documento de la Lista A (por ejemplo, pasaporte de EE. UU. o green card) O uno de la Lista B (por ejemplo, licencia de conducir) MÁS uno de la Lista C (por ejemplo, tarjeta del Seguro Social o acta de nacimiento). Lleva los originales el primer día.",
    up_i9_falta: "Falta el I-9: Lista A, o Lista B más Lista C.", up_ver: "Ver",
    p_metodos: { deposito: "Depósito directo", zelle: "Zelle", cheque: "Cheque en papel", provedor: "Por el sistema de nómina ({p})" },
    p_porque: { deposito: "Tu pago llega directo a tu cuenta el día de pago. Necesitamos el routing y el número de cuenta para enviarlo.",
      zelle: "Enviamos tu pago al correo o teléfono vinculado a tu Zelle.",
      cheque: "Recibes un cheque en papel. Necesitamos una dirección postal correcta.",
      provedor: "Recibirás una invitación de {p} para registrar tus datos de pago directamente con ellos." },
    p_banco: "Nombre del banco", p_tipo: "Tipo de cuenta", p_corrente: "Corriente (checking)", p_poupanca: "Ahorros (savings)",
    p_routing: "Routing number (9 dígitos)", p_conta: "Número de cuenta", p_conta2: "Confirma el número de cuenta",
    p_ja_salvo: "Ya informado: routing {r}, cuenta {c}. Déjalo en blanco para mantenerlos.", p_cheque_anulado: "Cheque anulado (opcional)",
    p_zelle: "Correo o teléfono de Zelle", p_endereco_ok: "Confirmo que la dirección de mis datos personales es correcta para enviar el cheque.",
    p_endereco_outro: "Otra dirección para el cheque (opcional)", p_provedor_ok: "Entiendo que registraré mis datos de pago con la invitación de {p}.",
    p_routing_invalido: "Routing number inválido. Revisa los 9 dígitos.",
    r_titulo: "Revisión", r_tudo: "¡Todo listo! Envíalo a la empresa.", r_faltam: "Todavía faltan pasos:", r_enviar: "Enviar incorporación",
    r_enviando: "Enviando…", fim_titulo: "Incorporación completa", fim_desc: "¡Gracias! La empresa recibió todo y se comunicará contigo con los próximos pasos.",
    fim_docs: "Tus documentos", cancelado: "Esta incorporación fue cancelada. Comunícate con la empresa si tienes dudas.",
    link_invalido: "Este enlace de incorporación no es válido. Revisa el correo que recibiste.",
    erro: "No se pudo completar. Inténtalo de nuevo.", sim: "Sí", nao: "No", proximo: "Siguiente paso",
  },
};

const obParams = new URLSearchParams(location.search);
const obToken = obParams.get("t") || "";
const obApp = document.getElementById("app");
let obLang = obNorm(obParams.get("lang")) || obLerLocal() || obNavegador();
let obLangDaUrl = !!obNorm(obParams.get("lang"));
let obD = null;          // dados do servidor
let obVista = "lista";   // lista | etapa:<chave> | doc:<id> | form:<tipo>
let obPdfAberto = {};

function obNorm(v) {
  const c = String(v || "").toLowerCase().slice(0, 2);
  return OB_IDIOMAS.includes(c) ? c : "";
}
function obLerLocal() {
  try { return obNorm(localStorage.getItem("cand_idioma")); } catch (e) { return ""; }
}
function obNavegador() {
  const n = (navigator.language || "").toLowerCase();
  return n.startsWith("pt") ? "pt" : n.startsWith("es") ? "es" : "en";
}
function tx(chave, vars) {
  let s = (OB_TXT[obLang] || OB_TXT.en)[chave];
  if (s === undefined) s = OB_TXT.en[chave];
  if (typeof s === "string" && vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
  return s;
}
function esc(v) {
  return String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function fmtData(iso) {
  if (!iso) return "";
  const d = new Date(String(iso).slice(0, 10) + "T12:00:00Z");
  if (isNaN(d)) return iso;
  return new Intl.DateTimeFormat(OB_LOCALE[obLang], { timeZone: "UTC", day: "numeric", month: "long", year: "numeric" }).format(d);
}
function fmtDinheiro(v) {
  return "$" + Number(v || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function rotulo(obj) {
  if (!obj) return "";
  if (typeof obj === "string") return obj;
  return obj[obLang] || obj.en || obj.pt || obj.es || "";
}

async function obChamar(acao, metodo, corpo, bruto) {
  const headers = { "X-Idioma": obLang };
  let body;
  if (bruto) { headers["Content-Type"] = "application/octet-stream"; body = bruto; }
  else if (metodo && metodo !== "GET") { headers["Content-Type"] = "application/json"; body = JSON.stringify(corpo || {}); }
  const r = await fetch("/api/onboarding/" + encodeURIComponent(obToken) + (acao ? "/" + acao : ""), { method: metodo || "GET", headers, body });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) { const e = new Error(d.erro || tx("erro")); e.status = r.status; e.dados = d; throw e; }
  return d;
}

// ------------------------------------------------------------ idioma
function obDesenharIdiomas() {
  const el = document.getElementById("ob-idiomas");
  el.innerHTML = OB_IDIOMAS.map((l) => `<button class="btn on-dark small ${l === obLang ? "ativo" : ""}" data-lang="${l}">${l.toUpperCase()}</button>`).join("");
  el.querySelectorAll("[data-lang]").forEach((b) => b.addEventListener("click", () => obTrocarIdioma(b.dataset.lang)));
  document.documentElement.lang = { pt: "pt-BR", en: "en", es: "es" }[obLang];
}
function obTrocarIdioma(l) {
  obLang = l;
  try { localStorage.setItem("cand_idioma", l); } catch (e) { /* sem armazenamento */ }
  obDesenharIdiomas();
  if (obD && obD.status !== "cancelado") obChamar("idioma", "POST", { idioma: l }).catch(() => {});
  desenhar();
}

// ------------------------------------------------------------ início
async function iniciar() {
  obDesenharIdiomas();
  if (!obToken) { obMensagem(tx("link_invalido")); return; }
  obApp.innerHTML = `<div class="card texto-centro"><p>${esc(tx("carregando"))}</p></div>`;
  try {
    obD = await obChamar("", "GET");
  } catch (e) {
    obMensagem(e.status === 410 ? tx("cancelado") : e.status === 404 ? tx("link_invalido") : e.message);
    return;
  }
  if (!obLangDaUrl && !obLerLocal() && obD.idioma) { obLang = obD.idioma; obDesenharIdiomas(); }
  desenhar();
}

function obMensagem(texto) {
  obApp.innerHTML = `<div class="card texto-centro"><p>${esc(texto)}</p></div>`;
}

function cabecalho() {
  const e = obD.empresa || {};
  return `<div class="ob-marca">${e.logo_url ? `<img src="${esc(e.logo_url)}" alt="${esc(e.nome)}">` : ""}<div class="nome">${esc(e.nome)}</div></div>`;
}

function desenhar() {
  if (!obD) return;
  document.title = (obD.empresa && obD.empresa.nome ? obD.empresa.nome + " · " : "") + "Onboarding";
  if (!obD.consentimento && obD.status !== "concluido") return telaConsentimento();
  if (obD.status === "concluido") return telaFim();
  if (obVista === "lista") return telaLista();
  const [tipo, alvo] = obVista.split(":");
  if (tipo === "doc") return telaDocumento(Number(alvo));
  if (tipo === "form") return telaFormulario(alvo);
  if (tipo === "etapa") return telaEtapa(alvo);
  telaLista();
}

function ir(vista) {
  obVista = vista;
  desenhar();
  window.scrollTo(0, 0);
}

function botaoVoltar(destino) {
  return `<button class="btn ghost small ob-voltar" data-voltar="${esc(destino || "lista")}">&larr; ${esc(tx("voltar"))}</button>`;
}
function ligarVoltar() {
  obApp.querySelectorAll("[data-voltar]").forEach((b) => b.addEventListener("click", () => ir(b.dataset.voltar)));
}

function aplicarDados(d) {
  obD = d;
}

// ------------------------------------------------------------ consentimento
function telaConsentimento() {
  obApp.innerHTML = `
    <div class="card">
      ${cabecalho()}
      <h2>${esc(tx("ola", { nome: obD.nome }))}</h2>
      <p class="desc">${esc(tx("intro", { empresa: obD.empresa.nome }))}</p>
      <h3>${esc(tx("cons_titulo"))}</h3>
      <div class="ob-doc" style="max-height:none">${esc(obD.textos_consentimento[obLang] || obD.textos_consentimento.en)}</div>
      <label class="ob-check"><input type="checkbox" id="ob-cons"> <span>${esc(tx("cons_aceito"))}</span></label>
      <div class="ob-msg" id="ob-msg"></div>
      <button class="btn block" id="ob-cons-ok">${esc(tx("cons_botao"))}</button>
    </div>`;
  document.getElementById("ob-cons-ok").addEventListener("click", async () => {
    const msg = document.getElementById("ob-msg");
    if (!document.getElementById("ob-cons").checked) { msg.style.color = "var(--err)"; msg.textContent = tx("falta_aceite"); return; }
    try {
      aplicarDados(await obChamar("consentimento", "POST", { aceito: true, idioma: obLang }));
      ir("lista");
    } catch (e) { msg.style.color = "var(--err)"; msg.textContent = e.message; }
  });
}

// ------------------------------------------------------------ lista de etapas
function resumoOferta() {
  const o = obD.oferta || {};
  const linhas = [
    [tx("oferta_cargo"), o.cargo],
    [tx("oferta_tipo"), obD.tipo === "w2" ? tx("tipo_w2") : tx("tipo_1099")],
    [tx("oferta_inicio"), fmtData(o.data_inicio)],
    [tx("oferta_pagamento"), fmtDinheiro(o.valor) + " " + (tx("unidades")[o.unidade] || "")],
    [tx("oferta_horario"), o.horario],
    [tx("oferta_notas"), o.notas],
  ].filter((l) => l[1]);
  return `<div class="ob-resumo">${linhas.map((l) => `<div><span class="rot">${esc(l[0])}</span><span>${esc(l[1])}</span></div>`).join("")}</div>`;
}

function telaLista() {
  const etapas = obD.etapas || [];
  const proxima = etapas.find((e) => !e.feito);
  obApp.innerHTML = `
    <div class="card">
      ${cabecalho()}
      <h2 style="margin-bottom:4px">${esc(tx("ola", { nome: obD.nome }))}</h2>
      <p class="desc">${esc(tx("intro", { empresa: obD.empresa.nome }))}</p>
      ${resumoOferta()}
      <div class="ob-barra"><div style="width:${obD.pct}%"></div></div>
      <div class="ob-pct">${esc(tx("progresso", { pct: obD.pct }))}${obD.prazo ? " · " + esc(tx("prazo", { data: fmtData(obD.prazo) })) : ""}</div>
      <div class="ob-lista">
        ${etapas.map((e, i) => `
          <button class="ob-item ${e.feito ? "feito" : ""}" data-etapa="${e.chave}">
            <span class="marca-etapa">${e.feito ? "&#10003;" : i + 1}</span>
            <span class="txt"><strong>${esc(tx("etapas")[e.chave])}</strong><small>${esc(e.feito ? tx("feito") : tx("porque")[e.chave])}</small></span>
            <span class="seta-ob">&rsaquo;</span>
          </button>`).join("")}
      </div>
      ${proxima ? `<div class="ob-acoes"><button class="btn block" data-etapa="${proxima.chave}">${esc(tx("continuar"))}: ${esc(tx("etapas")[proxima.chave])}</button></div>` : ""}
    </div>`;
  obApp.querySelectorAll("[data-etapa]").forEach((b) => b.addEventListener("click", () => abrirEtapa(b.dataset.etapa)));
}

function abrirEtapa(chave) {
  if (chave === "oferta" && obD.modelo_oferta) return ir("doc:" + obD.modelo_oferta.id);
  ir("etapa:" + chave);
}

function proximaEtapa() {
  const p = (obD.etapas || []).find((e) => !e.feito);
  if (!p) return ir("etapa:revisao");
  abrirEtapa(p.chave);
}

function telaEtapa(chave) {
  if (chave === "dados") return telaDados();
  if (chave === "documentos") return telaDocumentos();
  if (chave === "formularios") return telaFormularios();
  if (chave === "arquivos") return telaArquivos();
  if (chave === "pagamento") return telaPagamento();
  if (chave === "revisao") return telaRevisao();
  ir("lista");
}

// ------------------------------------------------------------ texto do documento
function htmlDoc(texto) {
  const linhas = String(texto || "").split("\n");
  let html = "";
  let lista = false;
  const fechar = () => { if (lista) { html += "</ul>"; lista = false; } };
  linhas.forEach((l) => {
    if (l.startsWith("- ")) { if (!lista) { html += "<ul>"; lista = true; } html += `<li>${esc(l.slice(2))}</li>`; return; }
    fechar();
    if (!l.trim()) return;
    if (l.startsWith("# ")) html += `<h2>${esc(l.slice(2))}</h2>`;
    else if (l.startsWith("## ")) html += `<h3>${esc(l.slice(3))}</h3>`;
    else if (l.startsWith("> ")) html += `<div class="ob-aviso">${esc(l.slice(2))}</div>`;
    else html += `<p>${esc(l)}</p>`;
  });
  fechar();
  return html;
}

// ------------------------------------------------------------ assinatura (canvas)
function padAssinatura(raiz) {
  const canvas = raiz.querySelector("canvas");
  const ctx = canvas.getContext("2d");
  let tinta = false;
  let desenhando = false;
  let ultimo = null;
  function ajustar() {
    const r = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(r.width * dpr));
    canvas.height = Math.max(1, Math.round(r.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineWidth = 2.4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#101B37";
    tinta = false;
  }
  function ponto(ev) {
    const r = canvas.getBoundingClientRect();
    return { x: ev.clientX - r.left, y: ev.clientY - r.top };
  }
  canvas.addEventListener("pointerdown", (ev) => {
    ev.preventDefault();
    desenhando = true;
    ultimo = ponto(ev);
    try { canvas.setPointerCapture(ev.pointerId); } catch (e) { /* ok */ }
  });
  canvas.addEventListener("pointermove", (ev) => {
    if (!desenhando) return;
    ev.preventDefault();
    const p = ponto(ev);
    ctx.beginPath();
    ctx.moveTo(ultimo.x, ultimo.y);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    ultimo = p;
    tinta = true;
    const dica = raiz.querySelector(".dica");
    if (dica) dica.style.display = "none";
  });
  const parar = () => { desenhando = false; };
  canvas.addEventListener("pointerup", parar);
  canvas.addEventListener("pointercancel", parar);
  canvas.addEventListener("pointerleave", parar);
  setTimeout(ajustar, 0);
  return {
    limpar() { ctx.clearRect(0, 0, canvas.width, canvas.height); tinta = false; const d = raiz.querySelector(".dica"); if (d) d.style.display = ""; },
    temTinta() { return tinta; },
    png() { return canvas.toDataURL("image/png"); },
  };
}

function htmlAssinatura() {
  return `
    <label class="field">${esc(tx("nome_completo"))}<input type="text" id="ob-nome" autocomplete="name" maxlength="120" value="${esc((obD.dados && obD.dados.nome_legal) || obD.nome_completo || "")}"></label>
    <div style="font-size:.86rem;margin:10px 0 6px">${esc(tx("desenhe"))}</div>
    <div class="ob-assin" id="ob-assin"><canvas></canvas><span class="dica">${esc(tx("dica_assin"))}</span></div>
    <div style="text-align:right;margin-top:4px"><button class="btn ghost small" id="ob-limpar" type="button">${esc(tx("limpar"))}</button></div>`;
}

// ------------------------------------------------------------ assinar documento
function acharModelo(id) {
  if (obD.modelo_oferta && obD.modelo_oferta.id === id) return obD.modelo_oferta;
  return (obD.documentos || []).find((d) => d.id === id);
}

function telaDocumento(id) {
  const m = acharModelo(id);
  if (!m) return ir("lista");
  const ehOferta = obD.modelo_oferta && obD.modelo_oferta.id === id;
  const versao = m.textos[obLang] ? obLang : (m.textos.en ? "en" : Object.keys(m.textos)[0]);
  const titulo = rotulo(m.titulos);
  const voltar = ehOferta ? "lista" : "etapa:documentos";
  if (m.assinado) {
    obApp.innerHTML = `
      <div class="card">
        ${botaoVoltar(voltar)}
        <h2>${esc(titulo)}</h2>
        <p><span class="badge ok">${esc(tx("assinado_em", { data: fmtData(m.assinado_em) }))}</span></p>
        <a class="btn secondary" href="/api/onboarding/${encodeURIComponent(obToken)}/arquivo/${m.doc_id}">${esc(tx("baixar"))}</a>
        <div class="ob-acoes"><button class="btn block" id="ob-prox">${esc(tx("proximo"))}</button></div>
      </div>`;
    ligarVoltar();
    document.getElementById("ob-prox").addEventListener("click", proximaEtapa);
    return;
  }
  const ehPdf = m.tipo === "pdf";
  obApp.innerHTML = `
    <div class="card">
      ${botaoVoltar(voltar)}
      <h2>${esc(titulo)}</h2>
      ${ehOferta ? resumoOferta() : ""}
      ${!ehPdf && versao !== obLang ? `<div class="ob-aviso">${esc(tx("so_ingles"))}</div>` : ""}
      ${ehPdf ? `<p><a class="btn secondary" id="ob-abrir-pdf" target="_blank" rel="noopener" href="/api/onboarding/${encodeURIComponent(obToken)}/modelo/${m.id}">${esc(tx("abrir_pdf"))}</a></p>`
        : `<div class="ob-doc" id="ob-doc">${htmlDoc(m.textos[versao])}</div><p class="ob-rolar" id="ob-rolar">${esc(tx("rolar"))}</p>`}
      ${m.requer_declaracao ? `<label class="field" style="margin-top:12px">${esc(tx("declaracao"))}<textarea id="ob-decl" rows="4" maxlength="2000" placeholder="${esc(tx("declaracao_ph"))}"></textarea></label>` : ""}
      <label class="ob-check"><input type="checkbox" id="ob-aceite"> <span>${esc(obD.aceite_assinatura[obLang] || obD.aceite_assinatura.en)}</span></label>
      ${htmlAssinatura()}
      <div class="ob-msg" id="ob-msg"></div>
      <div class="ob-acoes"><button class="btn block" id="ob-assinar">${esc(tx("assinar"))}</button></div>
    </div>`;
  ligarVoltar();
  const pad = padAssinatura(document.getElementById("ob-assin"));
  document.getElementById("ob-limpar").addEventListener("click", () => pad.limpar());
  let leu = ehPdf ? !!obPdfAberto[id] : false;
  if (ehPdf) {
    document.getElementById("ob-abrir-pdf").addEventListener("click", () => { obPdfAberto[id] = true; leu = true; });
  } else {
    const caixa = document.getElementById("ob-doc");
    const conferir = () => {
      if (caixa.scrollTop + caixa.clientHeight >= caixa.scrollHeight - 12) {
        leu = true;
        const aviso = document.getElementById("ob-rolar");
        if (aviso) aviso.style.display = "none";
      }
    };
    caixa.addEventListener("scroll", conferir);
    setTimeout(conferir, 50);
  }
  document.getElementById("ob-assinar").addEventListener("click", async (ev) => {
    const msg = document.getElementById("ob-msg");
    const erro = (t) => { msg.style.color = "var(--err)"; msg.textContent = t; };
    if (!leu) return erro(ehPdf ? tx("abrir_pdf_antes") : tx("rolar"));
    const decl = document.getElementById("ob-decl");
    if (decl && decl.value.trim().length < 10) return erro(tx("falta_decl"));
    if (!document.getElementById("ob-aceite").checked) return erro(tx("falta_aceite"));
    const nome = document.getElementById("ob-nome").value.trim();
    if (nome.length < 3 || nome.indexOf(" ") < 0) return erro(tx("falta_nome"));
    if (!pad.temTinta()) return erro(tx("falta_assin"));
    ev.target.disabled = true;
    ev.target.textContent = tx("assinando");
    try {
      aplicarDados(await obChamar("assinar", "POST", {
        modelo_id: id, nome, assinatura: pad.png(), aceite: true, leu_tudo: true,
        declaracao: decl ? decl.value.trim() : "", idioma: obLang,
      }));
      if (ehOferta) proximaEtapa(); else ir("etapa:documentos");
    } catch (e) {
      erro(e.message);
      ev.target.disabled = false;
      ev.target.textContent = tx("assinar");
    }
  });
}

function telaDocumentos() {
  const lista = obD.documentos || [];
  obApp.innerHTML = `
    <div class="card">
      ${botaoVoltar("lista")}
      <h2>${esc(tx("etapas").documentos)}</h2>
      <p class="desc">${esc(tx("porque").documentos)}</p>
      <div class="ob-lista">
        ${lista.map((d) => `
          <button class="ob-item ${d.assinado ? "feito" : ""}" data-doc="${d.id}">
            <span class="marca-etapa">${d.assinado ? "&#10003;" : "&#9998;"}</span>
            <span class="txt"><strong>${esc(rotulo(d.titulos))}</strong><small>${esc(d.assinado ? tx("assinado_em", { data: fmtData(d.assinado_em) }) : tx("pendente"))}</small></span>
            <span class="seta-ob">&rsaquo;</span>
          </button>`).join("")}
      </div>
      ${lista.every((d) => d.assinado) ? `<div class="ob-acoes"><button class="btn block" id="ob-prox">${esc(tx("proximo"))}</button></div>` : ""}
    </div>`;
  ligarVoltar();
  obApp.querySelectorAll("[data-doc]").forEach((b) => b.addEventListener("click", () => ir("doc:" + b.dataset.doc)));
  const p = document.getElementById("ob-prox");
  if (p) p.addEventListener("click", proximaEtapa);
}

// ------------------------------------------------------------ campos com erro
function marcarErros(raiz, campos) {
  raiz.querySelectorAll(".ob-campo-erro").forEach((x) => x.classList.remove("ob-campo-erro"));
  (campos || []).forEach((c) => {
    const el = raiz.querySelector(`[data-campo="${CSS.escape(c)}"]`);
    if (el) el.classList.add("ob-campo-erro");
  });
  const primeiro = raiz.querySelector(".ob-campo-erro");
  if (primeiro) primeiro.scrollIntoView({ behavior: "smooth", block: "center" });
}

function campoTexto(chave, rot, valor, extra) {
  return `<label class="field" data-campo="${chave}">${esc(rot)}<input type="${(extra && extra.tipo) || "text"}" id="d-${chave}" value="${esc(valor || "")}" ${(extra && extra.attrs) || ""}>
    ${extra && extra.ajuda ? `<span class="ob-ajuda">${esc(extra.ajuda)}</span>` : ""}<span class="erro-campo">${esc(tx("erro_campo"))}</span></label>`;
}

// ------------------------------------------------------------ dados pessoais
function telaDados() {
  const d = obD.dados || {};
  const tamanhos = ["XS", "S", "M", "L", "XL", "2XL", "3XL"];
  obApp.innerHTML = `
    <div class="card">
      ${botaoVoltar("lista")}
      <h2>${esc(tx("etapas").dados)}</h2>
      <p class="desc">${esc(tx("porque").dados)}</p>
      <div id="ob-form">
        ${campoTexto("nome_legal", tx("d_nome_legal"), d.nome_legal || obD.nome_completo, { attrs: 'autocomplete="name" maxlength="120"' })}
        ${campoTexto("nome_preferido", tx("d_nome_preferido"), d.nome_preferido, { attrs: 'maxlength="80"' })}
        ${campoTexto("endereco", tx("d_endereco"), d.endereco, { attrs: 'autocomplete="address-line1" maxlength="200"' })}
        ${campoTexto("apto", tx("d_apto"), d.apto, { attrs: 'autocomplete="address-line2" maxlength="40"' })}
        <div class="ob-grid2">
          ${campoTexto("cidade", tx("d_cidade"), d.cidade, { attrs: 'autocomplete="address-level2" maxlength="80"' })}
          <div class="ob-grid2">
            ${campoTexto("estado", tx("d_estado"), d.estado, { attrs: 'autocomplete="address-level1" maxlength="2" style="text-transform:uppercase"' })}
            ${campoTexto("cep", tx("d_cep"), d.cep, { attrs: 'autocomplete="postal-code" inputmode="numeric" maxlength="10"' })}
          </div>
        </div>
        <div class="ob-grid2">
          ${campoTexto("telefone", tx("d_telefone"), d.telefone, { tipo: "tel", attrs: 'autocomplete="tel" maxlength="30"' })}
          ${campoTexto("email", tx("d_email"), d.email || obD.email, { tipo: "email", attrs: 'autocomplete="email" maxlength="160"' })}
        </div>
        ${campoTexto("nascimento", tx("d_nascimento"), "", { tipo: "date", attrs: 'autocomplete="bday"', ajuda: d.nascimento_mascara ? tx("d_ja_salvo", { m: d.nascimento_mascara }) : "" })}
        <label class="field" data-campo="tamanho">${esc(tx("d_tamanho"))}<select id="d-tamanho"><option value="">${esc(tx("d_escolha"))}</option>
          ${tamanhos.map((t) => `<option ${d.tamanho === t ? "selected" : ""}>${t}</option>`).join("")}</select><span class="erro-campo">${esc(tx("erro_campo"))}</span></label>
        <h3>${esc(tx("d_contato"))}</h3>
        ${campoTexto("contato_nome", tx("d_contato_nome"), d.contato_nome, { attrs: 'maxlength="120"' })}
        <div class="ob-grid2">
          ${campoTexto("contato_relacao", tx("d_contato_relacao"), d.contato_relacao, { attrs: 'maxlength="60"' })}
          ${campoTexto("contato_telefone", tx("d_contato_telefone"), d.contato_telefone, { tipo: "tel", attrs: 'maxlength="30"' })}
        </div>
        ${obD.oferta.dirige ? `
          <h3>${esc(tx("d_cnh"))}</h3>
          <div class="ob-grid2">
            ${campoTexto("cnh_numero", tx("d_cnh_numero"), "", { attrs: 'maxlength="25" autocomplete="off"', ajuda: d.cnh_numero_mascara ? tx("d_ja_salvo", { m: d.cnh_numero_mascara }) : "" })}
            ${campoTexto("cnh_estado", tx("d_cnh_estado"), d.cnh_estado, { attrs: 'maxlength="2" style="text-transform:uppercase"' })}
          </div>` : ""}
      </div>
      <div class="ob-msg" id="ob-msg"></div>
      <div class="ob-acoes"><button class="btn block" id="ob-salvar">${esc(tx("salvar"))}</button></div>
    </div>`;
  ligarVoltar();
  document.getElementById("ob-salvar").addEventListener("click", async (ev) => {
    const v = (k) => { const el = document.getElementById("d-" + k); return el ? el.value.trim() : undefined; };
    const corpo = {};
    ["nome_legal", "nome_preferido", "endereco", "apto", "cidade", "estado", "cep", "telefone", "email", "nascimento",
      "tamanho", "contato_nome", "contato_relacao", "contato_telefone", "cnh_numero", "cnh_estado"].forEach((k) => {
      const x = v(k);
      if (x !== undefined) corpo[k] = x;
    });
    const msg = document.getElementById("ob-msg");
    ev.target.disabled = true;
    try {
      aplicarDados(await obChamar("dados", "POST", corpo));
      proximaEtapa();
    } catch (e) {
      msg.style.color = "var(--err)";
      msg.textContent = e.message;
      marcarErros(document.getElementById("ob-form"), (e.dados || {}).campos);
      ev.target.disabled = false;
    }
  });
}

// ------------------------------------------------------------ formulários fiscais
function telaFormularios() {
  const lista = obD.formularios || [];
  obApp.innerHTML = `
    <div class="card">
      ${botaoVoltar("lista")}
      <h2>${esc(tx("etapas").formularios)}</h2>
      <p class="desc">${esc(tx("porque").formularios)}</p>
      ${!obD.formularios_disponivel ? `<div class="ob-aviso">${esc(tx("f_indisponivel"))}</div>` : ""}
      <div class="ob-lista">
        ${lista.map((f) => `
          <button class="ob-item ${f.feito ? "feito" : ""}" data-form="${f.tipo}" ${obD.formularios_disponivel ? "" : "disabled"}>
            <span class="marca-etapa">${f.feito ? "&#10003;" : "&#9998;"}</span>
            <span class="txt"><strong>${esc(tx("f_titulos")[f.tipo] || f.tipo)}</strong><small>${esc(f.feito ? tx("f_feito") : tx("pendente"))}</small></span>
            <span class="seta-ob">&rsaquo;</span>
          </button>`).join("")}
      </div>
      ${lista.every((f) => f.feito) ? `<div class="ob-acoes"><button class="btn block" id="ob-prox">${esc(tx("proximo"))}</button></div>` : ""}
    </div>`;
  ligarVoltar();
  obApp.querySelectorAll("[data-form]").forEach((b) => b.addEventListener("click", () => ir("form:" + b.dataset.form)));
  const p = document.getElementById("ob-prox");
  if (p) p.addEventListener("click", proximaEtapa);
}

// pré-preenche os formulários com os dados pessoais (nunca com dados sensíveis)
function obPartesNome(d) {
  const p = String(d.nome_legal || "").trim().split(/\s+/).filter(Boolean);
  return { primeiro: p[0] || "", ultimo: p.length > 1 ? p[p.length - 1] : "", meio: p.length > 2 ? p[1].charAt(0).toUpperCase() : "" };
}
const OB_PREENCHER = {
  nome: (d) => d.nome_legal, nome_completo: (d) => d.nome_legal,
  primeiro_nome: (d) => obPartesNome(d).primeiro, sobrenome: (d) => obPartesNome(d).ultimo, inicial_meio: (d) => obPartesNome(d).meio,
  endereco: (d) => d.endereco, apto: (d) => d.apto, cidade: (d) => d.cidade, estado: (d) => d.estado, cep: (d) => d.cep,
  email: (d) => d.email, telefone: (d) => d.telefone,
};

function opcoesDoCampo(c) {
  return (c.opcoes || []).map((o) => (typeof o === "object" && o !== null)
    ? { valor: o.valor != null ? o.valor : (o.chave != null ? o.chave : o.value), rotulo: rotulo(o.rotulo || o.label) || String(o.valor != null ? o.valor : o.chave) }
    : { valor: o, rotulo: String(o) });
}

// condicao: {campo, valores}: o campo só aparece (e só vai ao servidor) quando o outro tem um desses valores
function obValorCampo(chave) {
  const el = document.getElementById("f-" + chave);
  if (!el) return undefined;
  return el.type === "checkbox" ? el.checked : el.value.trim();
}
function obCampoVisivel(c) {
  if (!c.condicao) return true;
  const pai = (obCampos || []).find((x) => x.chave === c.condicao.campo);
  if (pai && !obCampoVisivel(pai)) return false;
  const atual = obValorCampo(c.condicao.campo);
  const valores = c.condicao.valores || [];
  if (valores.includes(true)) return atual === true;
  return valores.map(String).includes(String(atual));
}
let obCampos = [];
function obAtualizarCondicoes(raiz) {
  obCampos.forEach((c) => {
    const el = raiz.querySelector(`[data-campo="${CSS.escape(String(c.chave))}"]`);
    if (el) el.style.display = obCampoVisivel(c) ? "" : "none";
  });
}
function obMostrarMensagens(raiz, mensagens) {
  Object.keys(mensagens || {}).forEach((k) => {
    const el = raiz.querySelector(`[data-campo="${CSS.escape(k)}"] .erro-campo`);
    if (el) el.textContent = rotulo(mensagens[k]) || tx("erro_campo");
  });
}

function htmlCampoForm(c, valor) {
  const tipo = String(c.tipo || "texto").toLowerCase();
  const chave = String(c.chave);
  const rot = rotulo(c.rotulo) + (c.obrigatorio ? " *" : "");
  const ajuda = rotulo(c.ajuda);
  const id = "f-" + chave;
  const fim = `${ajuda ? `<span class="ob-ajuda">${esc(ajuda)}</span>` : ""}<span class="erro-campo">${esc(tx("erro_campo"))}</span>`;
  if (["checkbox", "bool", "booleano", "boolean"].includes(tipo)) {
    return `<label class="ob-check" data-campo="${esc(chave)}"><input type="checkbox" id="${esc(id)}" ${valor === true || valor === "true" || valor === "1" ? "checked" : ""}> <span>${esc(rot)}${fim}</span></label>`;
  }
  if ((c.opcoes && c.opcoes.length) || ["select", "escolha", "opcoes", "radio"].includes(tipo)) {
    const ops = opcoesDoCampo(c);
    return `<label class="field" data-campo="${esc(chave)}">${esc(rot)}<select id="${esc(id)}"><option value="">${esc(tx("d_escolha"))}</option>
      ${ops.map((o) => `<option value="${esc(o.valor)}" ${String(valor) === String(o.valor) ? "selected" : ""}>${esc(o.rotulo)}</option>`).join("")}</select>${fim}</label>`;
  }
  if (["textarea", "texto_longo", "longo"].includes(tipo)) {
    return `<label class="field" data-campo="${esc(chave)}">${esc(rot)}<textarea id="${esc(id)}" rows="3">${esc(valor || "")}</textarea>${fim}</label>`;
  }
  let inputType = "text";
  let attrs = 'autocomplete="off"';
  if (["data", "date"].includes(tipo)) inputType = "date";
  else if (tipo === "email" || c.formato === "email") inputType = "email";
  else if (["telefone", "tel", "phone"].includes(tipo) || c.formato === "telefone") inputType = "tel";
  else if (c.formato === "cep") attrs += ' inputmode="numeric" maxlength="10"';
  else if (["numero", "number", "inteiro", "moeda", "dinheiro", "valor", "currency", "money"].includes(tipo)) attrs += ' inputmode="decimal"';
  else if (["ssn", "ein", "itin", "tin"].includes(tipo)) attrs += ' inputmode="numeric" maxlength="11"';
  return `<label class="field" data-campo="${esc(chave)}">${esc(rot)}<input type="${inputType}" id="${esc(id)}" value="${esc(valor == null ? "" : valor)}" ${attrs}>${fim}</label>`;
}

function telaFormulario(tipo) {
  const f = (obD.formularios || []).find((x) => x.tipo === tipo);
  if (!f) return ir("etapa:formularios");
  if (!obD.formularios_disponivel || !f.campos) {
    obApp.innerHTML = `<div class="card">${botaoVoltar("etapa:formularios")}<div class="ob-aviso">${esc(tx("f_indisponivel"))}</div></div>`;
    ligarVoltar();
    return;
  }
  const anteriores = f.anteriores || {};
  const dados = obD.dados || {};
  const valorInicial = (c) => {
    if (c.chave in anteriores) return anteriores[c.chave];
    const fn = OB_PREENCHER[String(c.chave).toLowerCase()];
    return fn ? fn(dados) : "";
  };
  obApp.innerHTML = `
    <div class="card">
      ${botaoVoltar("etapa:formularios")}
      <h2>${esc(tx("f_titulos")[tipo] || tipo)}</h2>
      ${f.feito ? `<p><span class="badge ok">${esc(tx("f_feito"))}</span> <a class="btn ghost small" href="/api/onboarding/${encodeURIComponent(obToken)}/arquivo/${f.doc_id}">${esc(tx("baixar"))}</a></p>` : ""}
      <div id="ob-form">${f.campos.map((c) => htmlCampoForm(c, valorInicial(c))).join("")}</div>
      <h3>${esc(tx("f_assinar_titulo"))}</h3>
      <label class="ob-check"><input type="checkbox" id="ob-aceite"> <span>${esc(tx("f_aceite"))}</span></label>
      ${htmlAssinatura()}
      <div class="ob-msg" id="ob-msg"></div>
      <div class="ob-acoes"><button class="btn block" id="ob-assinar">${esc(f.feito ? tx("f_refazer") : tx("assinar"))}</button></div>
    </div>`;
  ligarVoltar();
  obCampos = f.campos;
  const formEl = document.getElementById("ob-form");
  obAtualizarCondicoes(formEl);
  formEl.addEventListener("change", () => obAtualizarCondicoes(formEl));
  const pad = padAssinatura(document.getElementById("ob-assin"));
  document.getElementById("ob-limpar").addEventListener("click", () => pad.limpar());
  document.getElementById("ob-assinar").addEventListener("click", async (ev) => {
    const msg = document.getElementById("ob-msg");
    const erro = (t) => { msg.style.color = "var(--err)"; msg.textContent = t; };
    const valores = {};
    f.campos.forEach((c) => {
      const el = document.getElementById("f-" + c.chave);
      if (!el || !obCampoVisivel(c)) return;
      if (el.type === "checkbox") valores[c.chave] = el.checked;
      else if (el.value.trim() !== "") valores[c.chave] = el.value.trim();
    });
    if (!document.getElementById("ob-aceite").checked) return erro(tx("falta_aceite"));
    const nome = document.getElementById("ob-nome").value.trim();
    if (nome.length < 3) return erro(tx("falta_nome"));
    if (!pad.temTinta()) return erro(tx("falta_assin"));
    ev.target.disabled = true;
    ev.target.textContent = tx("assinando");
    try {
      aplicarDados(await obChamar("formulario/" + tipo, "POST", { dados: valores, nome, assinatura: pad.png(), aceite: true }));
      ir("etapa:formularios");
    } catch (e) {
      erro(e.message);
      obMostrarMensagens(formEl, (e.dados || {}).mensagens);
      marcarErros(formEl, (e.dados || {}).campos);
      ev.target.disabled = false;
      ev.target.textContent = f.feito ? tx("f_refazer") : tx("assinar");
    }
  });
}

// ------------------------------------------------------------ envio de documentos
function htmlUpload(cat, obrigatorio) {
  const enviados = (obD.arquivos || []).filter((a) => a.chave === cat);
  return `
    <div class="ob-up">
      <div class="cab">
        <div><strong>${esc(tx("up_titulo")[cat] || cat)}</strong>
          <div class="hint">${esc(obrigatorio ? tx("up_obrigatorio") : tx("up_opcional"))}${enviados.length ? " · &#10003;" : ""}</div></div>
        <label class="btn secondary small">${esc(tx("up_enviar"))}<input type="file" accept="image/*,application/pdf,.heic,.heif" data-cat="${cat}"></label>
      </div>
      ${enviados.map((a) => `
        <div class="arq"><span>${esc(a.nome || cat)}</span>
          <span><a href="/api/onboarding/${encodeURIComponent(obToken)}/arquivo/${a.id}">${esc(tx("up_ver"))}</a> ·
          <a href="#" data-remover="${a.id}">${esc(tx("up_remover"))}</a></span></div>`).join("")}
    </div>`;
}

function ligarUploads(raiz, aoMudar) {
  const msg = raiz.querySelector("#ob-msg");
  raiz.querySelectorAll("input[type=file][data-cat]").forEach((inp) => inp.addEventListener("change", async () => {
    const arq = inp.files && inp.files[0];
    if (!arq) return;
    if (arq.size > 10 * 1024 * 1024) { msg.style.color = "var(--err)"; msg.textContent = tx("up_grande"); return; }
    msg.style.color = "var(--text-2)";
    msg.textContent = tx("up_enviando");
    try {
      aplicarDados(await obChamar("arquivo?categoria=" + encodeURIComponent(inp.dataset.cat) + "&nome=" + encodeURIComponent(arq.name), "POST", null, arq));
      aoMudar();
    } catch (e) { msg.style.color = "var(--err)"; msg.textContent = e.message; }
  }));
  raiz.querySelectorAll("[data-remover]").forEach((a) => a.addEventListener("click", async (ev) => {
    ev.preventDefault();
    try {
      aplicarDados(await obChamar("arquivo/" + a.dataset.remover, "DELETE"));
      aoMudar();
    } catch (e) { msg.style.color = "var(--err)"; msg.textContent = e.message; }
  }));
}

function telaArquivos() {
  const cats = obD.categorias || [];
  const temI9 = cats.some((c) => c.grupo === "i9");
  const feito = (obD.etapas || []).find((e) => e.chave === "arquivos");
  const enviados = new Set((obD.arquivos || []).map((a) => a.chave));
  const i9ok = enviados.has("i9_lista_a") || (enviados.has("i9_lista_b") && enviados.has("i9_lista_c"));
  obApp.innerHTML = `
    <div class="card">
      ${botaoVoltar("lista")}
      <h2>${esc(tx("etapas").arquivos)}</h2>
      <p class="desc">${esc(tx("porque").arquivos)}</p>
      ${cats.filter((c) => c.grupo !== "i9").map((c) => htmlUpload(c.chave, c.obrigatorio)).join("")}
      ${temI9 ? `<h3>Form I-9</h3><div class="ob-aviso">${esc(tx("up_i9"))}</div>
        ${cats.filter((c) => c.grupo === "i9").map((c) => htmlUpload(c.chave, false)).join("")}
        ${!i9ok ? `<p class="hint" style="color:var(--warn)">${esc(tx("up_i9_falta"))}</p>` : ""}` : ""}
      <div class="ob-msg" id="ob-msg"></div>
      ${feito && feito.feito ? `<div class="ob-acoes"><button class="btn block" id="ob-prox">${esc(tx("proximo"))}</button></div>` : ""}
    </div>`;
  ligarVoltar();
  ligarUploads(obApp, () => telaArquivos());
  const p = document.getElementById("ob-prox");
  if (p) p.addEventListener("click", proximaEtapa);
}

// ------------------------------------------------------------ pagamento
function telaPagamento(metodoSel) {
  const pag = obD.pagamento || {};
  const metodos = obD.metodos || [];
  const sel = metodoSel || (metodos.includes(pag.metodo) ? pag.metodo : metodos[0]);
  const prov = obD.provedor_nome || "Gusto";
  const temSalvo = pag.routing_mascara && pag.conta_mascara;
  let campos = "";
  if (sel === "deposito") {
    campos = `
      ${campoTexto("banco", tx("p_banco"), pag.banco, { attrs: 'maxlength="80"' })}
      <label class="field" data-campo="tipo_conta">${esc(tx("p_tipo"))}<select id="d-tipo_conta"><option value="">${esc(tx("d_escolha"))}</option>
        <option value="corrente" ${pag.tipo_conta === "corrente" ? "selected" : ""}>${esc(tx("p_corrente"))}</option>
        <option value="poupanca" ${pag.tipo_conta === "poupanca" ? "selected" : ""}>${esc(tx("p_poupanca"))}</option></select><span class="erro-campo">${esc(tx("erro_campo"))}</span></label>
      ${temSalvo ? `<p class="hint">${esc(tx("p_ja_salvo", { r: pag.routing_mascara, c: pag.conta_mascara }))}</p>` : ""}
      ${campoTexto("routing", tx("p_routing"), "", { attrs: 'inputmode="numeric" maxlength="9" autocomplete="off"' })}
      <div class="ob-grid2">
        ${campoTexto("conta", tx("p_conta"), "", { attrs: 'inputmode="numeric" maxlength="17" autocomplete="off"' })}
        ${campoTexto("conta_confirmacao", tx("p_conta2"), "", { attrs: 'inputmode="numeric" maxlength="17" autocomplete="off"' })}
      </div>
      ${htmlUpload("cheque_anulado", false)}`;
  } else if (sel === "zelle") {
    campos = campoTexto("zelle", tx("p_zelle"), pag.zelle, { attrs: 'maxlength="120" autocomplete="off"' });
  } else if (sel === "cheque") {
    const d = obD.dados || {};
    const end = [d.endereco, d.apto, d.cidade, d.estado, d.cep].filter(Boolean).join(", ");
    campos = `${end ? `<p class="hint">${esc(end)}</p>` : ""}
      <label class="ob-check" data-campo="endereco_confirmado"><input type="checkbox" id="d-endereco_confirmado" ${pag.endereco_confirmado ? "checked" : ""}> <span>${esc(tx("p_endereco_ok"))}<span class="erro-campo">${esc(tx("erro_campo"))}</span></span></label>
      ${campoTexto("endereco_cheque", tx("p_endereco_outro"), pag.endereco_cheque, { attrs: 'maxlength="250"' })}`;
  } else if (sel === "provedor") {
    campos = `<label class="ob-check" data-campo="provedor_ciente"><input type="checkbox" id="d-provedor_ciente" ${pag.provedor_ciente ? "checked" : ""}> <span>${esc(tx("p_provedor_ok", { p: prov }))}<span class="erro-campo">${esc(tx("erro_campo"))}</span></span></label>`;
  }
  obApp.innerHTML = `
    <div class="card">
      ${botaoVoltar("lista")}
      <h2>${esc(tx("etapas").pagamento)}</h2>
      <div class="ob-metodos">
        ${metodos.map((m) => `
          <label class="ob-metodo ${m === sel ? "ativo" : ""}"><input type="radio" name="ob-metodo" value="${m}" ${m === sel ? "checked" : ""}>
            <span><strong>${esc(tx("p_metodos")[m].replace("{p}", prov))}</strong><small>${esc(tx("p_porque")[m].replace("{p}", prov))}</small></span></label>`).join("")}
      </div>
      <div id="ob-form">${campos}</div>
      <div class="ob-msg" id="ob-msg"></div>
      <div class="ob-acoes"><button class="btn block" id="ob-salvar">${esc(tx("salvar"))}</button></div>
    </div>`;
  ligarVoltar();
  obApp.querySelectorAll("input[name=ob-metodo]").forEach((r) => r.addEventListener("change", () => telaPagamento(r.value)));
  ligarUploads(obApp, () => telaPagamento(sel));
  document.getElementById("ob-salvar").addEventListener("click", async (ev) => {
    const v = (k) => { const el = document.getElementById("d-" + k); return el ? (el.type === "checkbox" ? el.checked : el.value.trim()) : undefined; };
    const corpo = { metodo: sel };
    ["banco", "tipo_conta", "routing", "conta", "conta_confirmacao", "zelle", "endereco_confirmado", "endereco_cheque", "provedor_ciente"].forEach((k) => {
      const x = v(k);
      if (x !== undefined) corpo[k] = x;
    });
    const msg = document.getElementById("ob-msg");
    if (sel === "deposito" && corpo.routing && !abaValido(corpo.routing)) {
      msg.style.color = "var(--err)";
      msg.textContent = tx("p_routing_invalido");
      marcarErros(document.getElementById("ob-form"), ["routing"]);
      return;
    }
    ev.target.disabled = true;
    try {
      aplicarDados(await obChamar("pagamento", "POST", corpo));
      proximaEtapa();
    } catch (e) {
      msg.style.color = "var(--err)";
      msg.textContent = e.message;
      marcarErros(document.getElementById("ob-form"), (e.dados || {}).campos);
      ev.target.disabled = false;
    }
  });
}

// mesma regra do servidor: pesos 3, 7, 1
function abaValido(r) {
  if (!/^\d{9}$/.test(r) || r === "000000000") return false;
  const n = r.split("").map(Number);
  return (3 * (n[0] + n[3] + n[6]) + 7 * (n[1] + n[4] + n[7]) + (n[2] + n[5] + n[8])) % 10 === 0;
}

// ------------------------------------------------------------ revisão e fim
function telaRevisao() {
  const pend = obD.pendentes || [];
  obApp.innerHTML = `
    <div class="card">
      ${botaoVoltar("lista")}
      <h2>${esc(tx("r_titulo"))}</h2>
      ${resumoOferta()}
      <div class="ob-lista">
        ${(obD.etapas || []).filter((e) => e.chave !== "revisao").map((e) => `
          <button class="ob-item ${e.feito ? "feito" : ""}" data-etapa="${e.chave}">
            <span class="marca-etapa">${e.feito ? "&#10003;" : "!"}</span>
            <span class="txt"><strong>${esc(tx("etapas")[e.chave])}</strong><small>${esc(e.feito ? tx("feito") : tx("pendente"))}</small></span>
            <span class="seta-ob">&rsaquo;</span>
          </button>`).join("")}
      </div>
      <p style="margin-top:14px">${esc(pend.length ? tx("r_faltam") : tx("r_tudo"))}</p>
      <div class="ob-msg" id="ob-msg"></div>
      <div class="ob-acoes"><button class="btn block" id="ob-enviar" ${pend.length ? "disabled" : ""}>${esc(tx("r_enviar"))}</button></div>
    </div>`;
  ligarVoltar();
  obApp.querySelectorAll("[data-etapa]").forEach((b) => b.addEventListener("click", () => abrirEtapa(b.dataset.etapa)));
  document.getElementById("ob-enviar").addEventListener("click", async (ev) => {
    ev.target.disabled = true;
    ev.target.textContent = tx("r_enviando");
    try {
      aplicarDados(await obChamar("concluir", "POST", {}));
      ir("lista");
    } catch (e) {
      const msg = document.getElementById("ob-msg");
      msg.style.color = "var(--err)";
      msg.textContent = e.message;
      ev.target.disabled = false;
      ev.target.textContent = tx("r_enviar");
    }
  });
}

function telaFim() {
  const docs = obD.baixaveis || [];
  obApp.innerHTML = `
    <div class="card texto-centro">
      ${cabecalho()}
      <div style="font-size:2.4rem">&#10003;</div>
      <h2>${esc(tx("fim_titulo"))}</h2>
      <p class="desc">${esc(tx("fim_desc"))}</p>
    </div>
    ${docs.length ? `<div class="card"><h3 style="margin-top:0">${esc(tx("fim_docs"))}</h3>
      ${docs.map((d) => `<div class="ob-up"><div class="cab"><span>${esc(d.titulo)}</span>
        <a class="btn ghost small" href="/api/onboarding/${encodeURIComponent(obToken)}/arquivo/${d.id}">${esc(tx("baixar"))}</a></div></div>`).join("")}</div>` : ""}`;
}

iniciar();
