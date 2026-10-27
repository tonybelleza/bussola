/* =====================================================================
   Agendamento da entrevista pelo candidato (/agendar?t=TOKEN).
   Idioma: ?lang, depois o idioma salvo do candidato, depois o navegador.
   Mostra dias e horários livres no fuso da empresa, confirma, remarca e
   cancela (uma entrevista ativa por candidato).
   API: GET /api/agenda/<token>, POST /api/agenda/<token>/marcar e /cancelar.
   ===================================================================== */

const AG_IDIOMAS = ["pt", "en", "es"];
const AG_LOCALE = { pt: "pt-BR", en: "en-US", es: "es" };

const AG_TXT = {
  pt: {
    titulo: "Entrevista", carregando: "Carregando…", idioma: "Idioma",
    ola: "Olá, {nome}!", escolha: "Escolha o dia e o horário da sua entrevista.",
    formato: "Formato", local: "Local / instruções", entrevistador: "Entrevistador(a)", duracao: "Duração",
    minutos: "{n} minutos", fuso: "Horários em {fuso}",
    formatos: { presencial: "Presencial", telefone: "Ligação telefônica", video: "Videochamada" },
    dia: "Dia", horario: "Horário", sem_horarios: "No momento não há horários livres. Tente de novo mais tarde ou fale com a empresa.",
    confirmar: "Confirmar {quando}", confirmando: "Confirmando…",
    marcada: "Entrevista confirmada", marcada_desc: "Enviamos a confirmação por e-mail, com o convite para a sua agenda.",
    remarcar: "Remarcar", cancelar: "Cancelar entrevista", voltar: "Voltar",
    confirmar_cancelar: "Cancelar a entrevista? Você poderá escolher outro horário depois.",
    cancelada: "Entrevista cancelada. Se quiser, escolha um novo horário abaixo.",
    escolher_novo: "Escolha o novo horário", desativada: "A agenda de entrevistas não está disponível no momento.",
    link_invalido: "Este link de agendamento não é válido. Confira o e-mail que você recebeu.",
    erro: "Não foi possível concluir. Tente de novo.", ocupado: "Esse horário acabou de ser escolhido por outra pessoa. Escolha outro.",
    atual: "Sua entrevista atual",
  },
  en: {
    titulo: "Interview", carregando: "Loading…", idioma: "Language",
    ola: "Hi {nome}!", escolha: "Pick the day and time for your interview.",
    formato: "Format", local: "Location / instructions", entrevistador: "Interviewer", duracao: "Length",
    minutos: "{n} minutes", fuso: "Times shown in {fuso}",
    formatos: { presencial: "In person", telefone: "Phone call", video: "Video call" },
    dia: "Day", horario: "Time", sem_horarios: "There are no open times right now. Please try again later or contact the company.",
    confirmar: "Confirm {quando}", confirmando: "Confirming…",
    marcada: "Interview confirmed", marcada_desc: "We emailed you a confirmation with a calendar invite.",
    remarcar: "Reschedule", cancelar: "Cancel interview", voltar: "Back",
    confirmar_cancelar: "Cancel your interview? You can pick another time later.",
    cancelada: "Your interview was canceled. If you'd like, pick a new time below.",
    escolher_novo: "Pick a new time", desativada: "Interview scheduling isn't available right now.",
    link_invalido: "This scheduling link isn't valid. Please check the email you received.",
    erro: "Something went wrong. Please try again.", ocupado: "Someone just took that time. Please pick another one.",
    atual: "Your current interview",
  },
  es: {
    titulo: "Entrevista", carregando: "Cargando…", idioma: "Idioma",
    ola: "¡Hola, {nome}!", escolha: "Elige el día y la hora de tu entrevista.",
    formato: "Formato", local: "Lugar / instrucciones", entrevistador: "Entrevistador(a)", duracao: "Duración",
    minutos: "{n} minutos", fuso: "Horarios en {fuso}",
    formatos: { presencial: "Presencial", telefone: "Llamada telefónica", video: "Videollamada" },
    dia: "Día", horario: "Hora", sem_horarios: "Por ahora no hay horarios libres. Intenta más tarde o comunícate con la empresa.",
    confirmar: "Confirmar {quando}", confirmando: "Confirmando…",
    marcada: "Entrevista confirmada", marcada_desc: "Te enviamos la confirmación por correo, con la invitación para tu calendario.",
    remarcar: "Cambiar horario", cancelar: "Cancelar entrevista", voltar: "Volver",
    confirmar_cancelar: "¿Cancelar la entrevista? Podrás elegir otro horario después.",
    cancelada: "Tu entrevista fue cancelada. Si quieres, elige un nuevo horario abajo.",
    escolher_novo: "Elige el nuevo horario", desativada: "La agenda de entrevistas no está disponible en este momento.",
    link_invalido: "Este enlace de agenda no es válido. Revisa el correo que recibiste.",
    erro: "No se pudo completar. Inténtalo de nuevo.", ocupado: "Alguien acaba de elegir ese horario. Elige otro.",
    atual: "Tu entrevista actual",
  },
};

const agParams = new URLSearchParams(location.search);
const agToken = agParams.get("t") || "";
const agLangUrl = norm(agParams.get("lang"));
let agLang = agLangUrl || lerLocal() || navegador();
let agDados = null;
let agDiaSel = null;
let agHoraSel = null;
let agModo = "auto"; // auto | escolher
let agAviso = "";

function norm(v) {
  const c = String(v || "").toLowerCase().slice(0, 2);
  return AG_IDIOMAS.includes(c) ? c : "";
}
function lerLocal() {
  try { return norm(localStorage.getItem("cand_idioma")); } catch (e) { return ""; }
}
function navegador() {
  const n = (navigator.language || "").toLowerCase();
  return n.startsWith("pt") ? "pt" : n.startsWith("es") ? "es" : "en";
}
function tx(chave, vars) {
  let s = (AG_TXT[agLang] || AG_TXT.pt)[chave];
  if (s === undefined) s = AG_TXT.pt[chave];
  if (typeof s === "string" && vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
  return s;
}
function escHtml(v) {
  return String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// datas: "AAAA-MM-DD" do dia local da empresa (meio-dia UTC evita virar o dia)
function dataDoDia(iso) { return new Date(iso + "T12:00:00Z"); }
function fmt(dt, opcoes, fuso) {
  return new Intl.DateTimeFormat(AG_LOCALE[agLang], Object.assign({ timeZone: fuso || "UTC" }, opcoes)).format(dt);
}
function quandoTexto(inicioUtc) {
  const d = new Date(inicioUtc);
  const fuso = agDados.fuso;
  const dia = fmt(d, { weekday: "long", day: "numeric", month: "long" }, fuso);
  const hora = fmt(d, { hour: "numeric", minute: "2-digit" }, fuso);
  return dia + ", " + hora;
}
function horaTexto(inicioUtc) {
  return fmt(new Date(inicioUtc), { hour: "numeric", minute: "2-digit" }, agDados.fuso);
}

async function chamar(caminho, metodo, corpo) {
  const r = await fetch(caminho, {
    method: metodo || "GET",
    headers: { "Content-Type": "application/json", "X-Idioma": agLang },
    body: metodo === "POST" ? JSON.stringify(corpo || {}) : undefined,
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) { const e = new Error(d.erro || tx("erro")); e.status = r.status; throw e; }
  return d;
}

function definirIdioma(lang) {
  agLang = norm(lang) || "pt";
  try { localStorage.setItem("cand_idioma", agLang); } catch (e) { /* armazenamento bloqueado */ }
  document.documentElement.lang = { pt: "pt-BR", en: "en", es: "es" }[agLang];
  document.title = (agDados && agDados.empresa.nome ? agDados.empresa.nome + " · " : "Bússola · ") + tx("titulo");
  document.getElementById("topo-sub").textContent = tx("titulo");
  document.querySelectorAll(".seletor-idioma button").forEach((b) => {
    b.classList.toggle("ativo", b.dataset.lang === agLang);
    b.setAttribute("aria-pressed", b.dataset.lang === agLang ? "true" : "false");
  });
}

function montarSeletor() {
  const estilo = document.createElement("style");
  estilo.textContent =
    ".seletor-idioma{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden}" +
    ".seletor-idioma button{background:none;border:0;color:var(--text-2);font:inherit;font-size:.72rem;font-weight:600;letter-spacing:.05em;padding:6px 9px;cursor:pointer;line-height:1}" +
    ".seletor-idioma button.ativo{background:var(--surface-2);color:var(--text)}";
  document.head.appendChild(estilo);
  const caixa = document.createElement("div");
  caixa.className = "seletor-idioma";
  caixa.setAttribute("role", "group");
  caixa.innerHTML = AG_IDIOMAS.map((c) =>
    `<button type="button" data-lang="${c}" title="${{ pt: "Português", en: "English", es: "Español" }[c]}">${c.toUpperCase()}</button>`).join("");
  document.querySelector(".topbar .actions").appendChild(caixa);
  caixa.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    definirIdioma(b.dataset.lang);
    desenhar();
  }));
}

function cabecalho() {
  const e = agDados.empresa;
  const info = [
    [tx("formato"), (tx("formatos")[agDados.formato] || agDados.formato)],
    [tx("duracao"), tx("minutos", { n: agDados.duracao })],
  ];
  if (agDados.entrevistador) info.push([tx("entrevistador"), agDados.entrevistador]);
  if (agDados.local) info.push([tx("local"), agDados.local]);
  return `
    <div class="ag-marca">
      ${e.logo_url ? `<img src="${escHtml(e.logo_url)}" alt="${escHtml(e.nome)}">` : ""}
      <div class="nome">${escHtml(e.nome)}</div>
    </div>
    <div class="ag-info">${info.map(([r, v]) => `<div><span class="rot">${escHtml(r)}</span><strong>${escHtml(v)}</strong></div>`).join("")}</div>`;
}

function telaConfirmada() {
  const ent = agDados.entrevista;
  return `
    <div class="card">${cabecalho()}</div>
    <div class="card ag-ok">
      <div class="icone-ok">✅</div>
      <h2 style="margin:6px 0">${tx("marcada")}</h2>
      <div class="ag-quando">${escHtml(quandoTexto(ent.inicio_utc))}</div>
      <p class="ag-fuso">${escHtml(tx("fuso", { fuso: agDados.rotulo_fuso }))}</p>
      <p class="desc">${tx("marcada_desc")}</p>
      <div class="ag-msg" id="ag-msg"></div>
      <div class="linha-acoes" style="justify-content:center">
        ${agDados.ativo ? `<button class="btn" id="ag-remarcar">${tx("remarcar")}</button>` : ""}
        <button class="btn danger" id="ag-cancelar">${tx("cancelar")}</button>
      </div>
    </div>`;
}

function telaEscolha() {
  const dias = agDados.dias || [];
  if (!agDiaSel || !dias.some((d) => d.data === agDiaSel)) agDiaSel = dias.length ? dias[0].data : null;
  const dia = dias.find((d) => d.data === agDiaSel);
  const atual = agDados.entrevista;
  let corpo;
  if (!agDados.ativo) corpo = `<p class="desc">${tx("desativada")}</p>`;
  else if (!dias.length) corpo = `<p class="desc">${tx("sem_horarios")}</p>`;
  else {
    corpo = `
      <h3 style="margin:8px 0 6px">${tx("dia")}</h3>
      <div class="ag-dias" role="listbox">
        ${dias.map((d) => {
          const dt = dataDoDia(d.data);
          return `<button type="button" class="ag-dia ${d.data === agDiaSel ? "ativo" : ""}" data-dia="${d.data}">
            <div class="sem">${escHtml(fmt(dt, { weekday: "short" }))}</div>
            <div class="num">${escHtml(fmt(dt, { day: "numeric" }))}</div>
            <div class="mes">${escHtml(fmt(dt, { month: "short" }))}</div></button>`;
        }).join("")}
      </div>
      <h3 style="margin:10px 0 6px">${tx("horario")}</h3>
      <div class="ag-horas">
        ${dia.horarios.map((h) => `<button type="button" class="ag-hora ${h.inicio_utc === agHoraSel ? "ativo" : ""}" data-hora="${h.inicio_utc}">${escHtml(horaTexto(h.inicio_utc))}</button>`).join("")}
      </div>
      <p class="ag-fuso">${escHtml(tx("fuso", { fuso: agDados.rotulo_fuso }))}</p>
      <div class="ag-confirmar">
        <div class="ag-msg" id="ag-msg"></div>
        <button class="btn block" id="ag-confirmar" ${agHoraSel ? "" : "disabled"}>${agHoraSel ? escHtml(tx("confirmar", { quando: quandoTexto(agHoraSel) })) : escHtml(tx("confirmar", { quando: "" }).trim())}</button>
      </div>`;
  }
  return `
    <div class="card">
      ${cabecalho()}
      <p style="margin:14px 0 0">${escHtml(tx("ola", { nome: agDados.nome }))} ${escHtml(atual ? tx("escolher_novo") + "." : tx("escolha"))}</p>
      ${agAviso ? `<p class="desc" style="color:var(--ok)">${escHtml(agAviso)}</p>` : ""}
    </div>
    <div class="card">
      ${atual ? `<p class="hint" style="margin-top:0">${tx("atual")}: <strong>${escHtml(quandoTexto(atual.inicio_utc))}</strong></p>` : ""}
      ${corpo}
      ${atual ? `<button class="btn ghost small mt" id="ag-voltar">${tx("voltar")}</button>` : ""}
    </div>`;
}

function mensagem(texto, ok) {
  const m = document.getElementById("ag-msg");
  if (!m) return;
  m.style.color = ok ? "var(--ok)" : "var(--err)";
  m.textContent = texto;
}

function desenhar() {
  const app = document.getElementById("app");
  if (!agDados) return;
  definirIdioma(agLang);
  const confirmada = agDados.entrevista && agModo !== "escolher";
  app.innerHTML = confirmada ? telaConfirmada() : telaEscolha();
  app.querySelectorAll("[data-dia]").forEach((b) => b.addEventListener("click", () => {
    agDiaSel = b.dataset.dia; agHoraSel = null; desenhar();
  }));
  app.querySelectorAll("[data-hora]").forEach((b) => b.addEventListener("click", () => {
    agHoraSel = b.dataset.hora; desenhar();
    const btn = document.getElementById("ag-confirmar");
    if (btn) btn.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }));
  const conf = document.getElementById("ag-confirmar");
  if (conf) conf.addEventListener("click", async () => {
    conf.disabled = true;
    conf.textContent = tx("confirmando");
    try {
      agDados = await chamar("/api/agenda/" + encodeURIComponent(agToken) + "/marcar", "POST", { inicio_utc: agHoraSel });
      agModo = "auto"; agHoraSel = null; agAviso = "";
      desenhar();
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      if (e.status === 409) {
        try { agDados = await chamar("/api/agenda/" + encodeURIComponent(agToken)); } catch (e2) { /* mantém */ }
        agHoraSel = null; desenhar(); mensagem(tx("ocupado"));
      } else { conf.disabled = false; conf.textContent = tx("confirmar", { quando: quandoTexto(agHoraSel) }); mensagem(e.message); }
    }
  });
  const rem = document.getElementById("ag-remarcar");
  if (rem) rem.addEventListener("click", () => { agModo = "escolher"; agAviso = ""; desenhar(); });
  const volta = document.getElementById("ag-voltar");
  if (volta) volta.addEventListener("click", () => { agModo = "auto"; agHoraSel = null; desenhar(); });
  const canc = document.getElementById("ag-cancelar");
  if (canc) canc.addEventListener("click", async () => {
    if (!confirm(tx("confirmar_cancelar"))) return;
    canc.disabled = true;
    try {
      agDados = await chamar("/api/agenda/" + encodeURIComponent(agToken) + "/cancelar", "POST", {});
      agModo = "auto"; agAviso = tx("cancelada");
      desenhar();
    } catch (e) { canc.disabled = false; mensagem(e.message); }
  });
}

async function iniciar() {
  montarSeletor();
  definirIdioma(agLang);
  const app = document.getElementById("app");
  app.innerHTML = `<div class="card texto-centro"><p>${tx("carregando")}</p></div>`;
  try {
    if (!agToken) throw Object.assign(new Error(""), { status: 404 });
    agDados = await chamar("/api/agenda/" + encodeURIComponent(agToken));
    if (!agLangUrl && agDados.idioma) agLang = norm(agDados.idioma) || agLang;
    desenhar();
  } catch (e) {
    app.innerHTML = `<div class="card texto-centro"><p>${escHtml(e.status === 404 ? tx("link_invalido") : tx("erro"))}</p></div>`;
  }
}

iniciar();
