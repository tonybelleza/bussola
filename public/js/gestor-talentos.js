/* =====================================================================
   Banco de talentos: decidir mais rápido (talentos.py).
   - talentosPreencherFicha: cartão "Resumo da ligação" no topo da ficha
     (tier, pontos, resultado, pontos fortes, alertas, próximo passo) e o
     controle "Lembrar em" (data e nota).
   - talentosFiltrosHtml / talentosFiltra / talentosLigarAba: filtros por
     triagem por voz, carro, carteira, cidade e etapa no banco de talentos.
   - talentosDecorarTabela / talentosComparar: seleção (até 3) e comparação
     lado a lado.
   Textos em pt, en e es (tg do i18n-gestor.js, chaves "tal_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  tal_resumo_titulo: "Resumo da ligação", tal_pontos: "{n} pontos", tal_vaga: "Vaga: {v}",
  tal_fortes: "Pontos fortes", tal_alertas: "Alertas", tal_proximo: "Próximo passo", tal_nada: "nenhum",
  tal_out_QUALIFIED: "Qualificado", tal_out_NOT_QUALIFIED: "Não qualificado", tal_out_NEEDS_REVIEW: "Precisa de revisão",
  tal_out_CALLBACK: "Pediu retorno", tal_out_NOT_INTERESTED: "Sem interesse", tal_out_VOICEMAIL: "Caixa postal",
  tal_out_WRONG_NUMBER: "Número errado", tal_out_NOT_AVAILABLE: "Não pôde falar", tal_out_DO_NOT_CALL: "Pediu para não ligar",
  tal_f_dias: "{n} dias úteis", tal_f_experiencia: "2+ anos de experiência",
  tal_f_perto: "mora em {cidade} (até {raio} milhas)", tal_f_perto_sem: "mora a até {raio} milhas",
  tal_f_carro_carteira: "tem carro e carteira", tal_f_sozinho: "à vontade trabalhando sem companhia",
  tal_f_inicio_1: "começa em até 1 semana", tal_f_inicio_2: "começa em até 2 semanas",
  tal_a_poucos_dias: "só {n} dia(s) úteis", tal_a_sem_experiencia: "sem experiência",
  tal_a_fora_area: "fora da área ({cidade})", tal_a_fora_area_sem: "fora da área",
  tal_a_sozinho_hesita: "hesita em trabalhar sem companhia",
  tal_a_carteira_nao: "sem carteira de motorista", tal_a_carteira_incerto: "carteira não confirmada",
  tal_a_carro_nao: "sem carro próprio", tal_a_carro_incerto: "carro não confirmado",
  tal_a_padroes: "objeções aos padrões de trabalho", tal_a_sem_smartphone: "sem smartphone",
  tal_a_desligou: "desligou antes do fim", tal_a_faltam: "{n} resposta(s) faltando",
  tal_p_agendar_entrevista: "Marcar a entrevista.", tal_p_aguardar_testes: "Aguardar os testes ou ligar para lembrar.",
  tal_p_ouvir_ligacao: "Ouvir a ligação antes de decidir.", tal_p_considerar_reprovar: "Considerar reprovar.",
  tal_p_aguardar_ligacao: "Aguardar a ligação da Francisca.", tal_p_encerrado: "Triagem encerrada: nada a fazer.",
  tal_p_entrevista_marcada: "Entrevista já marcada.", tal_p_acompanhar: "Já avançou no pipeline: acompanhar a etapa.",
  tal_lembrar: "Lembrar em", tal_nota_ph: "Nota (opcional)", tal_salvar: "Salvar", tal_limpar: "Limpar",
  tal_lembrete_ativo: "Lembrete em {data}", tal_lembrete_quadro: "Lembrete", tal_lembrete_salvo: "Lembrete salvo.",
  tal_lembrete_removido: "Lembrete removido.", tal_lembrete_desc: "No dia escolhido o candidato aparece em \"Ligar hoje\" no quadro do dia.",
  tal_ft_voz: "Triagem por voz: todas", tal_ft_sem: "Sem triagem", tal_ft_encerrada: "Encerrada",
  tal_ft_carro: "Carro: todos", tal_ft_carteira: "Carteira: todas", tal_ft_etapa: "Etapa: todas",
  tal_carro_sim: "Com carro", tal_carro_nao: "Sem carro", tal_carro_desc: "Carro não informado",
  tal_cart_sim: "Com carteira", tal_cart_nao: "Sem carteira", tal_cart_desc: "Carteira não informada",
  tal_ft_cidade: "Cidade",
  tal_comparar: "Comparar ({n})", tal_limpar_sel: "Limpar seleção", tal_max3: "Escolha no máximo 3 candidatos para comparar.",
  tal_min2: "Selecione 2 ou 3 candidatos para comparar.", tal_selecionar: "Selecionar para comparar",
  tal_comparar_titulo: "Comparar candidatos", tal_abrir: "Abrir ficha",
  tal_r_voz: "Triagem por voz", tal_r_cidade: "Cidade", tal_r_dias: "Dias úteis", tal_r_exp: "Experiência",
  tal_r_carro: "Carro próprio", tal_r_carteira: "Carteira", tal_r_disc: "DISC dominante", tal_r_base: "B.A.S.E.",
  tal_r_match: "Match com o cargo", tal_r_etapa: "Etapa", tal_r_tags: "Etiquetas",
  tal_sim: "Sim", tal_nao: "Não", tal_incerto: "Incerto",
  tal_exp_two_plus_years: "2+ anos", tal_exp_under_two_or_informal: "Menos de 2 anos ou informal", tal_exp_none: "Nenhuma",
});
Object.assign(I18N_GESTOR.en, {
  tal_resumo_titulo: "Call summary", tal_pontos: "{n} points", tal_vaga: "Job: {v}",
  tal_fortes: "Strengths", tal_alertas: "Alerts", tal_proximo: "Next step", tal_nada: "none",
  tal_out_QUALIFIED: "Qualified", tal_out_NOT_QUALIFIED: "Not qualified", tal_out_NEEDS_REVIEW: "Needs review",
  tal_out_CALLBACK: "Asked for a callback", tal_out_NOT_INTERESTED: "Not interested", tal_out_VOICEMAIL: "Voicemail",
  tal_out_WRONG_NUMBER: "Wrong number", tal_out_NOT_AVAILABLE: "Couldn't talk", tal_out_DO_NOT_CALL: "Asked not to be called",
  tal_f_dias: "{n} weekdays", tal_f_experiencia: "2+ years of experience",
  tal_f_perto: "lives in {cidade} (within {raio} miles)", tal_f_perto_sem: "lives within {raio} miles",
  tal_f_carro_carteira: "has a car and a license", tal_f_sozinho: "comfortable working alone",
  tal_f_inicio_1: "can start within a week", tal_f_inicio_2: "can start within 2 weeks",
  tal_a_poucos_dias: "only {n} weekday(s)", tal_a_sem_experiencia: "no experience",
  tal_a_fora_area: "outside the area ({cidade})", tal_a_fora_area_sem: "outside the area",
  tal_a_sozinho_hesita: "hesitant to work alone",
  tal_a_carteira_nao: "no driver's license", tal_a_carteira_incerto: "license not confirmed",
  tal_a_carro_nao: "no car", tal_a_carro_incerto: "car not confirmed",
  tal_a_padroes: "objects to the work standards", tal_a_sem_smartphone: "no smartphone",
  tal_a_desligou: "hung up early", tal_a_faltam: "{n} missing answer(s)",
  tal_p_agendar_entrevista: "Schedule the interview.", tal_p_aguardar_testes: "Wait for the tests or call to remind them.",
  tal_p_ouvir_ligacao: "Listen to the call before deciding.", tal_p_considerar_reprovar: "Consider rejecting.",
  tal_p_aguardar_ligacao: "Wait for Francisca's call.", tal_p_encerrado: "Screening closed: nothing to do.",
  tal_p_entrevista_marcada: "Interview already scheduled.", tal_p_acompanhar: "Already moving in the pipeline: follow up on the stage.",
  tal_lembrar: "Remind me on", tal_nota_ph: "Note (optional)", tal_salvar: "Save", tal_limpar: "Clear",
  tal_lembrete_ativo: "Reminder on {data}", tal_lembrete_quadro: "Reminder", tal_lembrete_salvo: "Reminder saved.",
  tal_lembrete_removido: "Reminder cleared.", tal_lembrete_desc: "On that day the candidate shows up in \"Call today\" on today's board.",
  tal_ft_voz: "Voice screening: all", tal_ft_sem: "Not screened", tal_ft_encerrada: "Closed",
  tal_ft_carro: "Car: all", tal_ft_carteira: "License: all", tal_ft_etapa: "Stage: all",
  tal_carro_sim: "Has a car", tal_carro_nao: "No car", tal_carro_desc: "Car unknown",
  tal_cart_sim: "Has a license", tal_cart_nao: "No license", tal_cart_desc: "License unknown",
  tal_ft_cidade: "Town",
  tal_comparar: "Compare ({n})", tal_limpar_sel: "Clear selection", tal_max3: "Pick up to 3 candidates to compare.",
  tal_min2: "Select 2 or 3 candidates to compare.", tal_selecionar: "Select to compare",
  tal_comparar_titulo: "Compare candidates", tal_abrir: "Open profile",
  tal_r_voz: "Voice screening", tal_r_cidade: "Town", tal_r_dias: "Weekdays", tal_r_exp: "Experience",
  tal_r_carro: "Own car", tal_r_carteira: "License", tal_r_disc: "DISC dominant", tal_r_base: "B.A.S.E.",
  tal_r_match: "Match with the role", tal_r_etapa: "Stage", tal_r_tags: "Tags",
  tal_sim: "Yes", tal_nao: "No", tal_incerto: "Unclear",
  tal_exp_two_plus_years: "2+ years", tal_exp_under_two_or_informal: "Under 2 years or informal", tal_exp_none: "None",
});
Object.assign(I18N_GESTOR.es, {
  tal_resumo_titulo: "Resumen de la llamada", tal_pontos: "{n} puntos", tal_vaga: "Vacante: {v}",
  tal_fortes: "Fortalezas", tal_alertas: "Alertas", tal_proximo: "Siguiente paso", tal_nada: "ninguno",
  tal_out_QUALIFIED: "Calificado", tal_out_NOT_QUALIFIED: "No calificado", tal_out_NEEDS_REVIEW: "Necesita revisión",
  tal_out_CALLBACK: "Pidió que le llamen", tal_out_NOT_INTERESTED: "Sin interés", tal_out_VOICEMAIL: "Buzón de voz",
  tal_out_WRONG_NUMBER: "Número equivocado", tal_out_NOT_AVAILABLE: "No pudo hablar", tal_out_DO_NOT_CALL: "Pidió que no le llamen",
  tal_f_dias: "{n} días entre semana", tal_f_experiencia: "más de 2 años de experiencia",
  tal_f_perto: "vive en {cidade} (hasta {raio} millas)", tal_f_perto_sem: "vive a menos de {raio} millas",
  tal_f_carro_carteira: "tiene auto y licencia", tal_f_sozinho: "trabaja bien sin compañía",
  tal_f_inicio_1: "puede empezar en una semana", tal_f_inicio_2: "puede empezar en 2 semanas",
  tal_a_poucos_dias: "solo {n} día(s) entre semana", tal_a_sem_experiencia: "sin experiencia",
  tal_a_fora_area: "fuera del área ({cidade})", tal_a_fora_area_sem: "fuera del área",
  tal_a_sozinho_hesita: "duda en trabajar sin compañía",
  tal_a_carteira_nao: "sin licencia de conducir", tal_a_carteira_incerto: "licencia sin confirmar",
  tal_a_carro_nao: "sin auto propio", tal_a_carro_incerto: "auto sin confirmar",
  tal_a_padroes: "objeta los estándares de trabajo", tal_a_sem_smartphone: "sin smartphone",
  tal_a_desligou: "colgó antes de terminar", tal_a_faltam: "{n} respuesta(s) pendiente(s)",
  tal_p_agendar_entrevista: "Agendar la entrevista.", tal_p_aguardar_testes: "Esperar las pruebas o llamar para recordarle.",
  tal_p_ouvir_ligacao: "Escuchar la llamada antes de decidir.", tal_p_considerar_reprovar: "Considerar descartarlo.",
  tal_p_aguardar_ligacao: "Esperar la llamada de Francisca.", tal_p_encerrado: "Evaluación cerrada: nada que hacer.",
  tal_p_entrevista_marcada: "Entrevista ya agendada.", tal_p_acompanhar: "Ya avanzó en el proceso: dar seguimiento a la etapa.",
  tal_lembrar: "Recordarme el", tal_nota_ph: "Nota (opcional)", tal_salvar: "Guardar", tal_limpar: "Quitar",
  tal_lembrete_ativo: "Recordatorio el {data}", tal_lembrete_quadro: "Recordatorio", tal_lembrete_salvo: "Recordatorio guardado.",
  tal_lembrete_removido: "Recordatorio quitado.", tal_lembrete_desc: "Ese día el candidato aparece en \"Llamar hoy\" en el tablero del día.",
  tal_ft_voz: "Evaluación por voz: todas", tal_ft_sem: "Sin evaluar", tal_ft_encerrada: "Cerrada",
  tal_ft_carro: "Auto: todos", tal_ft_carteira: "Licencia: todas", tal_ft_etapa: "Etapa: todas",
  tal_carro_sim: "Con auto", tal_carro_nao: "Sin auto", tal_carro_desc: "Auto sin dato",
  tal_cart_sim: "Con licencia", tal_cart_nao: "Sin licencia", tal_cart_desc: "Licencia sin dato",
  tal_ft_cidade: "Ciudad",
  tal_comparar: "Comparar ({n})", tal_limpar_sel: "Quitar selección", tal_max3: "Elige hasta 3 candidatos para comparar.",
  tal_min2: "Selecciona 2 o 3 candidatos para comparar.", tal_selecionar: "Seleccionar para comparar",
  tal_comparar_titulo: "Comparar candidatos", tal_abrir: "Abrir ficha",
  tal_r_voz: "Evaluación por voz", tal_r_cidade: "Ciudad", tal_r_dias: "Días entre semana", tal_r_exp: "Experiencia",
  tal_r_carro: "Auto propio", tal_r_carteira: "Licencia", tal_r_disc: "DISC dominante", tal_r_base: "B.A.S.E.",
  tal_r_match: "Match con el puesto", tal_r_etapa: "Etapa", tal_r_tags: "Etiquetas",
  tal_sim: "Sí", tal_nao: "No", tal_incerto: "Incierto",
  tal_exp_two_plus_years: "Más de 2 años", tal_exp_under_two_or_informal: "Menos de 2 años o informal", tal_exp_none: "Ninguna",
});

let talVoz = {};                 // {candidato_id: {tier, score, outcome, encerrado, city, own_car, license, ...}}
const talSelecionados = new Set(); // candidatos marcados para comparar (até 3)
const TAL_MAX = 3;
const TAL_COR_TIER = { STRONG: "ok", GOOD: "neutral", REVIEW: "warn", LOW: "err" };

function talBadgeTier(tier, score) {
  if (!tier) return "";
  return `<span class="badge ${TAL_COR_TIER[tier] || "tipo"}">${esc(tier)}${score != null ? " · " + esc(String(score)) : ""}</span>`;
}

function talOutcome(o) {
  return o ? tg("tal_out_" + o) : "";
}

function talSimNao(v) {
  if (v === "yes") return tg("tal_sim");
  if (v === "no") return tg("tal_nao");
  if (v === "unclear") return tg("tal_incerto");
  return "·";
}

// texto de um item das linhas do resumo ({c: código, ...parâmetros})
function talItem(tipo, i) {
  const k = "tal_" + tipo + "_" + i.c;
  if (i.c === "perto") return tg(i.cidade ? k : k + "_sem", { cidade: i.cidade, raio: i.raio });
  if (i.c === "fora_area") return tg(i.cidade ? k : k + "_sem", { cidade: i.cidade });
  if (i.c === "inicio") return tg(k + "_" + i.semanas);
  return tg(k, { n: i.n });
}

// ------------------------------------------------------------ ficha: resumo e lembrete
async function talentosPreencherFicha(candidatoId, el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/talentos/resumo/" + candidatoId); } catch (e) { el.remove(); return; }
  const l = r.linhas;
  const lista = (itens, tipo) => (itens.length ? itens.map((i) => esc(talItem(tipo, i))).join(" · ") : tg("tal_nada"));
  const lem = r.lembrete;
  el.innerHTML = `
    ${r.tem_voz ? `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <h2 style="margin:0">${tg("tal_resumo_titulo")}</h2>
        <div>${talBadgeTier(r.tier, r.score)} ${r.outcome ? `<span class="badge tipo">${esc(talOutcome(r.outcome))}</span>` : ""}</div>
      </div>
      ${r.vaga ? `<p class="hint" style="margin:4px 0 8px">${esc(tg("tal_vaga", { v: r.vaga }))}</p>` : ""}
      <div style="display:grid;gap:6px;margin:8px 0 12px">
        <div><strong style="color:var(--ok)">${tg("tal_fortes")}:</strong> ${lista(l.fortes, "f")}</div>
        <div><strong style="color:var(--warn)">${tg("tal_alertas")}:</strong> ${lista(l.alertas, "a")}</div>
        <div><strong>${tg("tal_proximo")}:</strong> ${esc(tg("tal_p_" + l.proximo.c))}</div>
      </div>` : ""}
    <div class="no-print" style="${r.tem_voz ? "border-top:1px solid var(--line, rgba(127,127,127,.15));padding-top:10px" : ""}">
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <strong>${tg("tal_lembrar")}</strong>
        <input type="date" id="tal-data" value="${esc(lem ? lem.data : "")}" style="margin:0;width:auto">
        <input type="text" id="tal-nota" maxlength="300" placeholder="${tg("tal_nota_ph")}" value="${esc(lem ? lem.nota || "" : "")}" style="margin:0;flex:1;min-width:160px">
        <button class="btn secondary small" id="tal-salvar">${tg("tal_salvar")}</button>
        ${lem ? `<button class="btn ghost small" id="tal-limpar">${tg("tal_limpar")}</button>` : ""}
      </div>
      <p class="hint" style="margin:6px 0 0" id="tal-msg">${lem ? esc(tg("tal_lembrete_ativo", { data: fmtData(lem.data) })) + (lem.nota ? ": " + esc(lem.nota) : "") : tg("tal_lembrete_desc")}</p>
    </div>`;
  const msg = (t, erro) => {
    const m = el.querySelector("#tal-msg");
    if (!m) return;
    m.style.color = erro ? "var(--err)" : "var(--ok)";
    m.textContent = t;
  };
  el.querySelector("#tal-salvar").addEventListener("click", async () => {
    try {
      await api("/api/gestor/talentos/lembrete/" + candidatoId, {
        method: "POST", body: { data: el.querySelector("#tal-data").value, nota: el.querySelector("#tal-nota").value },
      });
      msg(tg("tal_lembrete_salvo"));
      setTimeout(() => talentosPreencherFicha(candidatoId, el), 700);
    } catch (e) { msg(e.message, true); }
  });
  const limpar = el.querySelector("#tal-limpar");
  if (limpar) limpar.addEventListener("click", async () => {
    try {
      await api("/api/gestor/talentos/lembrete/" + candidatoId, { method: "DELETE" });
      msg(tg("tal_lembrete_removido"));
      setTimeout(() => talentosPreencherFicha(candidatoId, el), 700);
    } catch (e) { msg(e.message, true); }
  });
}

// ------------------------------------------------------------ filtros do banco de talentos
function talentosFiltrosHtml() {
  const etapas = ["inscrito", "avaliacoes", "entrevista", "proposta", "contratado", "reprovado"];
  return `
    <select id="ft-voz" style="margin:0">
      <option value="">${tg("tal_ft_voz")}</option>
      ${["STRONG", "GOOD", "REVIEW", "LOW"].map((t) => `<option value="${t}">${t}</option>`).join("")}
      <option value="sem">${tg("tal_ft_sem")}</option>
      <option value="encerrada">${tg("tal_ft_encerrada")}</option>
    </select>
    <select id="ft-carro" style="margin:0">
      <option value="">${tg("tal_ft_carro")}</option>
      <option value="yes">${tg("tal_carro_sim")}</option><option value="no">${tg("tal_carro_nao")}</option>
      <option value="unknown">${tg("tal_carro_desc")}</option>
    </select>
    <select id="ft-carteira" style="margin:0">
      <option value="">${tg("tal_ft_carteira")}</option>
      <option value="yes">${tg("tal_cart_sim")}</option><option value="no">${tg("tal_cart_nao")}</option>
      <option value="unknown">${tg("tal_cart_desc")}</option>
    </select>
    <input type="text" id="ft-cidade" placeholder="${tg("tal_ft_cidade")}" style="margin:0">
    <select id="ft-etapa" style="margin:0">
      <option value="">${tg("tal_ft_etapa")}</option>
      ${etapas.map((e) => `<option value="${e}">${esc(tg("et_" + e))}</option>`).join("")}
    </select>`;
}

function talValor(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : "";
}

function talCasaSimNao(valor, filtro) {
  if (!filtro) return true;
  if (filtro === "unknown") return valor !== "yes" && valor !== "no";
  return valor === filtro;
}

// true quando o candidato (item da lista /api/gestor/candidatos) passa nos filtros novos
function talentosFiltra(c) {
  const v = talVoz[c.candidato.id] || {};
  const voz = talValor("ft-voz");
  if (voz === "sem" && (v.tier || v.encerrado)) return false;
  if (voz === "encerrada" && !v.encerrado) return false;
  if (voz && voz !== "sem" && voz !== "encerrada" && v.tier !== voz) return false;
  if (!talCasaSimNao(v.own_car, talValor("ft-carro"))) return false;
  if (!talCasaSimNao(v.license, talValor("ft-carteira"))) return false;
  const cidade = talValor("ft-cidade").toLowerCase();
  if (cidade && !((v.city || "") + " " + (c.candidato.local || "")).toLowerCase().includes(cidade)) return false;
  const etapa = talValor("ft-etapa");
  if (etapa && !(c.candidaturas || []).some((ca) => ca.etapa === etapa)) return false;
  return true;
}

// liga os filtros novos, o botão Comparar e carrega os dados de voz da lista
function talentosLigarAba(el, aplicar) {
  ["ft-voz", "ft-carro", "ft-carteira", "ft-etapa"].forEach((id) => {
    const s = document.getElementById(id);
    if (s) s.addEventListener("change", aplicar);
  });
  const cidade = document.getElementById("ft-cidade");
  if (cidade) cidade.addEventListener("input", aplicar);
  const acoes = el.querySelector(".linha-acoes");
  if (acoes && !el.querySelector("#tal-comparar")) {
    acoes.insertAdjacentHTML("afterbegin", `
      <button class="btn ghost small oculto" id="tal-limpar-sel">${tg("tal_limpar_sel")}</button>
      <button class="btn secondary small" id="tal-comparar">${tg("tal_comparar", { n: talSelecionados.size })}</button>`);
    el.querySelector("#tal-comparar").addEventListener("click", talentosComparar);
    el.querySelector("#tal-limpar-sel").addEventListener("click", () => { talSelecionados.clear(); talentosDecorarTabela(el); });
  }
  talentosDecorarTabela(el);
  api("/api/gestor/talentos/voz").then((r) => {
    talVoz = r.candidatos || {};
    if (document.body.contains(el)) aplicar();
  }).catch(() => {});
}

function talAtualizarBotao(el) {
  const b = el.querySelector("#tal-comparar");
  if (b) b.textContent = tg("tal_comparar", { n: talSelecionados.size });
  const l = el.querySelector("#tal-limpar-sel");
  if (l) l.classList.toggle("oculto", !talSelecionados.size);
  el.querySelectorAll("[data-tal-sel]").forEach((cx) => {
    cx.disabled = !cx.checked && talSelecionados.size >= TAL_MAX;
  });
}

// caixa de seleção por linha da tabela do banco de talentos
function talentosDecorarTabela(el) {
  const alvo = el.querySelector("#ft-resultado") || el;
  const cab = alvo.querySelector("thead tr");
  if (cab && !cab.querySelector(".tal-th")) cab.insertAdjacentHTML("afterbegin", '<th class="tal-th"></th>');
  alvo.querySelectorAll("tr[data-linha-cand]").forEach((tr) => {
    if (tr.querySelector("[data-tal-sel]")) return;
    const id = Number(tr.dataset.linhaCand);
    tr.insertAdjacentHTML("afterbegin", `<td style="width:28px"><input type="checkbox" data-tal-sel="${id}"
      title="${tg("tal_selecionar")}" aria-label="${tg("tal_selecionar")}" ${talSelecionados.has(id) ? "checked" : ""} style="margin:0;width:auto"></td>`);
  });
  alvo.querySelectorAll("[data-tal-sel]").forEach((cx) => {
    if (cx.dataset.ligado) return;
    cx.dataset.ligado = "1";
    cx.addEventListener("click", (ev) => ev.stopPropagation());
    cx.addEventListener("change", () => {
      const id = Number(cx.dataset.talSel);
      if (cx.checked) {
        if (talSelecionados.size >= TAL_MAX) { cx.checked = false; alert(tg("tal_max3")); return; }
        talSelecionados.add(id);
      } else talSelecionados.delete(id);
      talAtualizarBotao(el);
    });
  });
  talAtualizarBotao(el);
}

// ------------------------------------------------------------ comparação lado a lado
function talentosComparar() {
  const lista = [...talSelecionados].map((id) => candidatos.find((c) => c.candidato.id === id)).filter(Boolean);
  if (lista.length < 2) return alert(tg("tal_min2"));
  const v = (c) => talVoz[c.candidato.id] || {};
  const linhas = [
    [tg("tal_r_voz"), (c) => (v(c).tier ? talBadgeTier(v(c).tier, v(c).score) : (v(c).encerrado ? esc(tg("tal_ft_encerrada")) : esc(tg("tal_ft_sem"))))
      + (v(c).outcome ? `<div class="hint">${esc(talOutcome(v(c).outcome))}</div>` : "")],
    [tg("tal_r_cidade"), (c) => esc(v(c).city || c.candidato.local || "·")],
    [tg("tal_r_dias"), (c) => (v(c).weekdays_available != null ? esc(String(v(c).weekdays_available)) : "·")],
    [tg("tal_r_exp"), (c) => (v(c).experience_level ? esc(tg("tal_exp_" + v(c).experience_level)) : "·")],
    [tg("tal_r_carro"), (c) => esc(talSimNao(v(c).own_car))],
    [tg("tal_r_carteira"), (c) => esc(talSimNao(v(c).license))],
    [tg("tal_r_disc"), (c) => {
      const d = c.testes.disc ? c.testes.disc.payload.dominante : null;
      return d ? `<span class="badge neutral">${esc(d)} · ${esc(DISC_PERFIS[d].nome)}</span>` : `<span class="badge tipo">${tg("pendente")}</span>`;
    }],
    [tg("tal_r_base"), (c) => {
      const b = c.testes.base ? c.testes.base.payload.dominante : null;
      return b ? `<span class="badge neutral">${esc(BASE_PERFIS[b].nome)}</span>` : `<span class="badge tipo">${tg("pendente")}</span>`;
    }],
    [tg("tal_r_match"), (c) => {
      if (!c.match) return "·";
      const comp = Object.entries(c.match.componentes || {})
        .map(([k, val]) => `<div class="hint">${esc(tg("r_m_" + k))}: ${esc(String(val))}%</div>`).join("");
      return `<strong>${c.match.geral}%</strong><div class="hint">${esc(nomeCargo(c.candidato.cargo_desejado_id))}</div>${comp}`;
    }],
    [tg("tal_r_etapa"), (c) => (c.candidaturas || []).map((ca) =>
      `<div>${esc(tg("et_" + ca.etapa))}<span class="hint"> · ${esc(ca.vaga_titulo || "")}</span></div>`).join("") || "·"],
    [tg("tal_r_tags"), (c) => (c.candidato.tags || []).map((t) => `<span class="badge tipo">${esc(t)}</span>`).join(" ") || "·"],
  ];
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal" style="max-width:${lista.length * 260 + 180}px">
      <button class="btn ghost small fechar" id="tal-cmp-fechar">${icone("fechar")} ${tg("fechar")}</button>
      <h2>${tg("tal_comparar_titulo")}</h2>
      <div style="overflow-x:auto;-webkit-overflow-scrolling:touch">
        <table class="tabela" style="min-width:${lista.length * 190 + 130}px">
          <thead><tr><th style="width:130px"></th>${lista.map((c) => `<th style="min-width:190px">${esc(c.candidato.nome)}</th>`).join("")}</tr></thead>
          <tbody>
            ${linhas.map(([rot, f]) => `<tr><td><strong>${rot}</strong></td>${lista.map((c) => `<td>${f(c)}</td>`).join("")}</tr>`).join("")}
            <tr><td></td>${lista.map((c) => `<td><button class="btn secondary small" data-tal-abrir="${c.candidato.id}">${tg("tal_abrir")}</button></td>`).join("")}</tr>
          </tbody>
        </table>
      </div>
    </div>`;
  document.body.appendChild(fundo);
  const fechar = () => fundo.remove();
  fundo.querySelector("#tal-cmp-fechar").addEventListener("click", fechar);
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fechar(); });
  fundo.querySelectorAll("[data-tal-abrir]").forEach((b) => b.addEventListener("click", () => {
    abrirDetalheCandidato(Number(b.dataset.talAbrir));
  }));
}
