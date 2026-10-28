/* =====================================================================
   Banco de talentos: avisar candidatos antigos sobre uma vaga aberta.
   Botão no pipeline da vaga, filtros, contagem, prévia do e-mail em cada
   idioma, envio e histórico. Na ficha do candidato: descadastro e avisos.
   Backend: campanhas.py.
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  camp_botao: "Avisar banco de talentos", camp_titulo: "Avisar o banco de talentos: {vaga}",
  camp_desc: "Envie esta vaga por e-mail para quem já se candidatou na empresa. Ficam de fora: quem já está nesta vaga, contratados, anonimizados, quem cancelou os e-mails, quem já foi avisado desta vaga e quem pediu para não ligar ou tem número errado.",
  camp_historico: "Avisos anteriores desta vaga", camp_sem_historico: "Nenhum aviso enviado para esta vaga ainda.",
  camp_col_data: "Data", camp_col_por: "Enviado por", camp_col_enviados: "Enviados", camp_col_falhas: "Falhas", camp_col_candidaturas: "Candidaturas depois do aviso",
  camp_enviando: "enviando ({n} na fila)",
  camp_filtros: "Filtros", camp_cargo: "Cargo", camp_cargo_mesmo: "Mesmo cargo desta vaga ({cargo})", camp_cargo_qualquer: "Qualquer cargo",
  camp_cidade: "Cidade (contém)", camp_cidade_ph: "ex.: Hartford", camp_meses: "Candidatou-se nos últimos",
  camp_meses_todos: "Qualquer data", camp_meses_n: "{n} meses", camp_tier: "Triagem por voz", camp_tier_todos: "Qualquer resultado",
  camp_tier_min: "{tier} ou melhor", camp_tags: "Etiquetas (qualquer uma)", camp_sem_tags: "Nenhuma etiqueta no banco.",
  camp_total: "{n} candidato(s) encontrados", camp_total_1: "1 candidato encontrado",
  camp_limite: "Cada aviso vai para no máximo {limite} pessoas: serão enviados {n} agora.",
  camp_por_idioma: "Por idioma: português {pt}, inglês {en}, espanhol {es}.",
  camp_amostra: "Quem vai receber (primeiros {n})", camp_ultima: "última candidatura {d}",
  camp_previa: "Prévia do e-mail", camp_assunto: "Assunto:",
  camp_enviar: "Enviar para {n} candidato(s)", camp_confirmar: "Enviar o aviso desta vaga para {n} candidato(s)? Cada um recebe no próprio idioma.",
  camp_enviado: "Envio iniciado para {n} candidato(s). Os e-mails saem aos poucos nos próximos minutos.",
  camp_sem_smtp: "Configure o envio de e-mails (SMTP) para poder enviar.", camp_nenhum: "Ninguém para avisar com esses filtros.",
  camp_ficha_titulo: "E-mails de vagas", camp_descadastrado: "Cancelou os e-mails de vagas em {d}",
  camp_descadastrado_desc: "Não recebe mais avisos de vagas da empresa. E-mails do processo (entrevista, onboarding) continuam.",
  camp_avisos: "Avisos de vagas recebidos", camp_st_enviado: "enviado", camp_st_falhou: "falhou", camp_st_pendente: "na fila", camp_st_ignorado: "não enviado",
  camp_carregando: "Calculando...",
});
Object.assign(I18N_GESTOR.en, {
  camp_botao: "Notify talent pool", camp_titulo: "Notify the talent pool: {vaga}",
  camp_desc: "Email this job to people who applied to your company before. Left out: people already in this job, hires, anonymized records, anyone who unsubscribed, anyone already notified about this job, and anyone who asked not to be called or has a wrong number.",
  camp_historico: "Past notices for this job", camp_sem_historico: "No notices sent for this job yet.",
  camp_col_data: "Date", camp_col_por: "Sent by", camp_col_enviados: "Sent", camp_col_falhas: "Failed", camp_col_candidaturas: "Applications after the notice",
  camp_enviando: "sending ({n} in queue)",
  camp_filtros: "Filters", camp_cargo: "Role", camp_cargo_mesmo: "Same role as this job ({cargo})", camp_cargo_qualquer: "Any role",
  camp_cidade: "Town (contains)", camp_cidade_ph: "e.g. Hartford", camp_meses: "Applied in the last",
  camp_meses_todos: "Any time", camp_meses_n: "{n} months", camp_tier: "Voice screening", camp_tier_todos: "Any result",
  camp_tier_min: "{tier} or better", camp_tags: "Tags (any of them)", camp_sem_tags: "No tags in the pool.",
  camp_total: "{n} candidates found", camp_total_1: "1 candidate found",
  camp_limite: "Each notice goes to at most {limite} people: {n} will be sent now.",
  camp_por_idioma: "By language: Portuguese {pt}, English {en}, Spanish {es}.",
  camp_amostra: "Who will get it (first {n})", camp_ultima: "last applied {d}",
  camp_previa: "Email preview", camp_assunto: "Subject:",
  camp_enviar: "Send to {n} candidates", camp_confirmar: "Send this job notice to {n} candidates? Each one gets it in their own language.",
  camp_enviado: "Sending started for {n} candidates. The emails go out gradually over the next few minutes.",
  camp_sem_smtp: "Set up email sending (SMTP) to be able to send.", camp_nenhum: "Nobody to notify with these filters.",
  camp_ficha_titulo: "Job emails", camp_descadastrado: "Unsubscribed from job emails on {d}",
  camp_descadastrado_desc: "No longer gets job notices from the company. Hiring process emails (interviews, onboarding) still go out.",
  camp_avisos: "Job notices received", camp_st_enviado: "sent", camp_st_falhou: "failed", camp_st_pendente: "queued", camp_st_ignorado: "not sent",
  camp_carregando: "Calculating...",
});
Object.assign(I18N_GESTOR.es, {
  camp_botao: "Avisar al banco de talentos", camp_titulo: "Avisar al banco de talentos: {vaga}",
  camp_desc: "Envía esta vacante por correo a quienes ya se postularon en la empresa. Quedan fuera: quienes ya están en esta vacante, contratados, registros anonimizados, quienes cancelaron los correos, quienes ya recibieron el aviso de esta vacante y quienes pidieron no recibir llamadas o tienen un número equivocado.",
  camp_historico: "Avisos anteriores de esta vacante", camp_sem_historico: "Aún no se enviaron avisos para esta vacante.",
  camp_col_data: "Fecha", camp_col_por: "Enviado por", camp_col_enviados: "Enviados", camp_col_falhas: "Fallidos", camp_col_candidaturas: "Postulaciones después del aviso",
  camp_enviando: "enviando ({n} en cola)",
  camp_filtros: "Filtros", camp_cargo: "Cargo", camp_cargo_mesmo: "Mismo cargo de esta vacante ({cargo})", camp_cargo_qualquer: "Cualquier cargo",
  camp_cidade: "Ciudad (contiene)", camp_cidade_ph: "ej.: Hartford", camp_meses: "Se postuló en los últimos",
  camp_meses_todos: "Cualquier fecha", camp_meses_n: "{n} meses", camp_tier: "Evaluación por voz", camp_tier_todos: "Cualquier resultado",
  camp_tier_min: "{tier} o mejor", camp_tags: "Etiquetas (cualquiera)", camp_sem_tags: "No hay etiquetas en el banco.",
  camp_total: "{n} candidatos encontrados", camp_total_1: "1 candidato encontrado",
  camp_limite: "Cada aviso llega a un máximo de {limite} personas: se enviarán {n} ahora.",
  camp_por_idioma: "Por idioma: portugués {pt}, inglés {en}, español {es}.",
  camp_amostra: "Quiénes lo recibirán (primeros {n})", camp_ultima: "última postulación {d}",
  camp_previa: "Vista previa del correo", camp_assunto: "Asunto:",
  camp_enviar: "Enviar a {n} candidatos", camp_confirmar: "¿Enviar el aviso de esta vacante a {n} candidatos? Cada uno lo recibe en su propio idioma.",
  camp_enviado: "Envío iniciado para {n} candidatos. Los correos salen poco a poco en los próximos minutos.",
  camp_sem_smtp: "Configura el envío de correos (SMTP) para poder enviar.", camp_nenhum: "No hay a quién avisar con estos filtros.",
  camp_ficha_titulo: "Correos de vacantes", camp_descadastrado: "Canceló los correos de vacantes el {d}",
  camp_descadastrado_desc: "Ya no recibe avisos de vacantes de la empresa. Los correos del proceso (entrevistas, incorporación) siguen saliendo.",
  camp_avisos: "Avisos de vacantes recibidos", camp_st_enviado: "enviado", camp_st_falhou: "falló", camp_st_pendente: "en cola", camp_st_ignorado: "no enviado",
  camp_carregando: "Calculando...",
});

// ------------------------------------------------------------ botão no pipeline da vaga
function campanhasBotaoVaga(vaga, ancora) {
  if (!vaga || vaga.status !== "aberta" || !ancora || !ancora.parentNode) return;
  const b = document.createElement("button");
  b.className = "btn secondary small";
  b.id = "pp-campanha";
  b.textContent = tg("camp_botao");
  b.addEventListener("click", () => campanhasAbrir(vaga.id));
  ancora.parentNode.insertBefore(b, ancora.nextSibling);
}

function campanhasHistorico(lista) {
  if (!lista.length) return `<p class="desc">${tg("camp_sem_historico")}</p>`;
  return `<div class="tabela-wrap"><table class="tabela">
    <thead><tr><th>${tg("camp_col_data")}</th><th>${tg("camp_col_por")}</th><th class="num">${tg("camp_col_enviados")}</th>
      <th class="num">${tg("camp_col_falhas")}</th><th class="num">${tg("camp_col_candidaturas")}</th></tr></thead>
    <tbody>${lista.map((c) => `<tr>
      <td>${esc(fmtDataHora(c.criado_em))}${c.pendentes ? `<div class="hint">${esc(tg("camp_enviando", { n: fmtNum(c.pendentes) }))}</div>` : ""}</td>
      <td>${esc(c.gestor || "")}</td>
      <td class="num">${fmtNum(c.enviados)} / ${fmtNum(c.total)}</td>
      <td class="num">${fmtNum(c.falhas)}</td>
      <td class="num"><strong>${fmtNum(c.candidaturas)}</strong></td></tr>`).join("")}</tbody></table></div>`;
}

async function campanhasAbrir(vagaId) {
  let info;
  try { info = await api("/api/gestor/campanhas/vaga/" + vagaId); } catch (e) { return alert(e.message); }
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  const linguas = ["en", "pt", "es"];
  const nomesLingua = { en: "English", pt: "Português", es: "Español" };
  let linguaPrevia = linguas.includes(idiomaGestor) ? idiomaGestor : "en";
  fundo.innerHTML = `
    <div class="modal" style="max-width:860px">
      <button class="btn ghost small fechar" id="camp-fechar">${icone("fechar")} ${tg("fechar")}</button>
      <h2>${esc(tg("camp_titulo", { vaga: info.vaga.titulo }))}</h2>
      <p class="desc">${tg("camp_desc")}</p>
      <h3 style="margin:18px 0 8px">${tg("camp_historico")}</h3>
      <div id="camp-historico">${campanhasHistorico(info.campanhas)}</div>
      <h3 style="margin:22px 0 8px">${tg("camp_filtros")}</h3>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0 16px">
        <label class="field">${tg("camp_cargo")}
          <select id="camp-cargo">
            <option value="qualquer">${tg("camp_cargo_qualquer")}</option>
            <option value="mesmo">${esc(tg("camp_cargo_mesmo", { cargo: info.vaga.cargo_nome }))}</option>
          </select></label>
        <label class="field">${tg("camp_cidade")}<input type="text" id="camp-cidade" placeholder="${esc(tg("camp_cidade_ph"))}"></label>
        <label class="field">${tg("camp_meses")}
          <select id="camp-meses"><option value="0">${tg("camp_meses_todos")}</option>
            ${[3, 6, 12, 24].map((n) => `<option value="${n}">${tg("camp_meses_n", { n })}</option>`).join("")}</select></label>
        <label class="field">${tg("camp_tier")}
          <select id="camp-tier"><option value="">${tg("camp_tier_todos")}</option>
            ${["STRONG", "GOOD", "REVIEW"].map((t) => `<option value="${t}">${tg("camp_tier_min", { tier: t })}</option>`).join("")}</select></label>
      </div>
      <div class="field" style="margin-bottom:14px"><div style="font-size:.86rem;color:var(--text-2)">${tg("camp_tags")}</div>
        ${info.tags.length ? info.tags.map((t) => `<label style="display:inline-flex;gap:6px;align-items:center;margin:6px 14px 0 0;font-size:.85rem">
          <input type="checkbox" data-camp-tag="${esc(t)}"> ${esc(t)}</label>`).join("") : `<p class="desc" style="margin:4px 0 0">${tg("camp_sem_tags")}</p>`}
      </div>
      <div id="camp-resultado" class="card" style="margin:0 0 16px;padding:16px 20px"><p class="desc">${tg("camp_carregando")}</p></div>
      <h3 style="margin:18px 0 8px">${tg("camp_previa")}</h3>
      <div class="linha-acoes" style="margin:0 0 8px" id="camp-linguas">
        ${linguas.map((l) => `<button class="btn ${l === linguaPrevia ? "" : "secondary"} small" data-camp-lingua="${l}">${nomesLingua[l]}</button>`).join("")}
      </div>
      <div class="hint" id="camp-assunto" style="margin-bottom:6px"></div>
      <iframe id="camp-iframe" sandbox="" title="${esc(tg("camp_previa"))}" style="width:100%;height:520px;border:1px solid var(--line);border-radius:12px;background:#eef1f6"></iframe>
      <div class="linha-acoes" style="margin-top:16px">
        <button class="btn" id="camp-enviar" disabled>${tg("camp_enviar", { n: 0 })}</button>
        <span class="hint" id="camp-aviso"></span>
      </div>
    </div>`;
  document.body.appendChild(fundo);
  const fechar = () => fundo.remove();
  fundo.querySelector("#camp-fechar").addEventListener("click", fechar);
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fechar(); });

  let previa = null;
  let seq = 0;
  const filtros = () => ({
    cargo: fundo.querySelector("#camp-cargo").value,
    cidade: fundo.querySelector("#camp-cidade").value.trim(),
    meses: Number(fundo.querySelector("#camp-meses").value) || 0,
    tier: fundo.querySelector("#camp-tier").value,
    tags: [...fundo.querySelectorAll("[data-camp-tag]:checked")].map((c) => c.dataset.campTag),
  });
  const mostrarPrevia = () => {
    if (!previa) return;
    const em = previa.emails[linguaPrevia];
    fundo.querySelector("#camp-assunto").innerHTML = `<strong>${tg("camp_assunto")}</strong> ${esc(em.assunto)}`;
    fundo.querySelector("#camp-iframe").srcdoc = em.html;
    fundo.querySelectorAll("[data-camp-lingua]").forEach((b) => {
      b.className = "btn " + (b.dataset.campLingua === linguaPrevia ? "" : "secondary") + " small";
    });
  };
  const atualizar = async () => {
    const meu = ++seq;
    let r;
    try {
      r = await api("/api/gestor/campanhas/vaga/" + vagaId + "/previa", { method: "POST", body: { filtros: filtros() } });
    } catch (e) {
      fundo.querySelector("#camp-resultado").innerHTML = `<p class="desc">${esc(e.message)}</p>`;
      return;
    }
    if (meu !== seq) return;
    previa = r;
    const pi = r.por_idioma || {};
    fundo.querySelector("#camp-resultado").innerHTML = `
      <div style="font-size:1.05rem"><strong>${esc(tgn("camp_total", r.total))}</strong></div>
      ${r.total ? `<p class="desc" style="margin:4px 0 0">${esc(tg("camp_limite", { limite: fmtNum(r.limite), n: fmtNum(r.enviar) }))}
        ${esc(tg("camp_por_idioma", { pt: fmtNum(pi.pt || 0), en: fmtNum(pi.en || 0), es: fmtNum(pi.es || 0) }))}</p>
        <details style="margin-top:8px"><summary class="hint">${esc(tg("camp_amostra", { n: fmtNum(r.amostra.length) }))}</summary>
          <ul style="margin:8px 0 0;padding-left:18px">${r.amostra.map((c) => `<li>${linkCandidato(c.id, c.nome)}
            <span class="hint">${c.local ? esc(c.local) + " · " : ""}${esc(c.idioma.toUpperCase())}${c.tier ? " · " + esc(c.tier) : ""}${c.ultima ? " · " + esc(tg("camp_ultima", { d: fmtData(c.ultima) })) : ""}</span></li>`).join("")}</ul>
        </details>` : `<p class="desc" style="margin:4px 0 0">${tg("camp_nenhum")}</p>`}`;
    const botao = fundo.querySelector("#camp-enviar");
    botao.textContent = tg("camp_enviar", { n: fmtNum(r.enviar) });
    botao.disabled = !r.enviar || !info.smtp;
    fundo.querySelector("#camp-aviso").textContent = info.smtp ? "" : tg("camp_sem_smtp");
    mostrarPrevia();
  };
  let espera = null;
  const agendar = () => { clearTimeout(espera); espera = setTimeout(atualizar, 300); };
  fundo.querySelectorAll("#camp-cargo, #camp-meses, #camp-tier, [data-camp-tag]").forEach((el) => el.addEventListener("change", agendar));
  fundo.querySelector("#camp-cidade").addEventListener("input", agendar);
  fundo.querySelectorAll("[data-camp-lingua]").forEach((b) => b.addEventListener("click", () => {
    linguaPrevia = b.dataset.campLingua;
    mostrarPrevia();
  }));
  fundo.querySelector("#camp-enviar").addEventListener("click", async () => {
    if (!previa || !previa.enviar) return;
    if (!confirm(tg("camp_confirmar", { n: fmtNum(previa.enviar) }))) return;
    const botao = fundo.querySelector("#camp-enviar");
    botao.disabled = true;
    try {
      const r = await api("/api/gestor/campanhas/vaga/" + vagaId + "/enviar", { method: "POST", body: { filtros: filtros() } });
      fundo.querySelector("#camp-aviso").textContent = tg("camp_enviado", { n: fmtNum(r.total) });
      const novo = await api("/api/gestor/campanhas/vaga/" + vagaId);
      fundo.querySelector("#camp-historico").innerHTML = campanhasHistorico(novo.campanhas);
      atualizar();
    } catch (e) {
      fundo.querySelector("#camp-aviso").textContent = e.message;
      botao.disabled = false;
    }
  });
  atualizar();
}

// ------------------------------------------------------------ ficha do candidato
async function campanhasPreencherFicha(candidatoId, fundo) {
  if (!fundo) return;
  let r;
  try { r = await api("/api/gestor/campanhas/candidato/" + candidatoId); } catch (e) { return; }
  if (!r.descadastrado && !r.envios.length) return;
  const modal = fundo.querySelector(".modal");
  if (!modal) return;
  const card = document.createElement("div");
  card.className = "card";
  card.id = "bloco-campanhas";
  card.innerHTML = `
    ${tituloIcone("documento", tg("camp_ficha_titulo"))}
    ${r.descadastrado ? `<p><span class="badge err">${esc(tg("camp_descadastrado", { d: fmtData(r.descadastrado_em) }))}</span></p>
      <p class="desc">${tg("camp_descadastrado_desc")}</p>` : ""}
    ${r.envios.length ? `<h4 style="margin:12px 0 6px">${tg("camp_avisos")}</h4>
      ${r.envios.map((e) => `<div>${esc(e.vaga)} <span class="hint">· ${esc(fmtData(e.enviado_em))} · ${esc(tg("camp_st_" + e.status))}</span></div>`).join("")}` : ""}`;
  const tags = modal.querySelector("#tags-lista");
  const depois = tags && tags.parentNode && tags.parentNode.parentNode === modal ? tags.parentNode : null;
  if (depois) modal.insertBefore(card, depois.nextSibling);
  else modal.appendChild(card);
}
