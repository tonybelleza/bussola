/* =====================================================================
   Link de indicação (painel do gestor): link pessoal por pessoa da equipe,
   quem indicou quem e o bônus. Backend: indicacoes.py.
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  ind_titulo: "Indicações", ind_gerar: "Gerar link de indicação", ind_copiar: "Copiar link", ind_copiado: "Copiado ✓",
  ind_link_desc: "Envie este link para {nome}. Quem se candidatar por ele fica marcado como indicado por {nome}.",
  ind_por: "Indicado por {nome}", ind_feitas: "Pessoas que {nome} indicou", ind_nenhuma: "Ninguém indicado ainda.",
  ind_sit_inscrito: "inscrito", ind_sit_contratado: "contratado, bônus vence em {d}", ind_sit_devido: "bônus devido desde {d}", ind_sit_pago: "bônus pago em {d}",
  ind_cfg_titulo: "Programa de indicação", ind_cfg_desc: "Cada pessoa da equipe pode ter um link pessoal (gere na ficha dela). O bônus vence alguns dias depois que o indicado é contratado.",
  ind_ativo: "Programa ativo", ind_valor: "Valor do bônus (ex.: US$ 100)", ind_dias: "Dias depois da contratação para o bônus vencer",
  ind_texto: "Regra do bônus (texto interno)", ind_salvar: "Salvar", ind_salvo: "Salvo.",
  ind_lista: "Indicações", ind_col_indicou: "Indicou", ind_col_indicado: "Indicado", ind_col_situacao: "Situação",
  ind_marcar_pago: "Marcar bônus pago", ind_desmarcar: "Desfazer",
});
Object.assign(I18N_GESTOR.en, {
  ind_titulo: "Referrals", ind_gerar: "Create referral link", ind_copiar: "Copy link", ind_copiado: "Copied ✓",
  ind_link_desc: "Send this link to {nome}. Anyone who applies through it is marked as referred by {nome}.",
  ind_por: "Referred by {nome}", ind_feitas: "People {nome} referred", ind_nenhuma: "No referrals yet.",
  ind_sit_inscrito: "applied", ind_sit_contratado: "hired, bonus due on {d}", ind_sit_devido: "bonus due since {d}", ind_sit_pago: "bonus paid on {d}",
  ind_cfg_titulo: "Referral program", ind_cfg_desc: "Each team member can have a personal link (create it on their profile). The bonus is due some days after the referred person is hired.",
  ind_ativo: "Program on", ind_valor: "Bonus amount (e.g. $100)", ind_dias: "Days after hire until the bonus is due",
  ind_texto: "Bonus rule (internal note)", ind_salvar: "Save", ind_salvo: "Saved.",
  ind_lista: "Referrals", ind_col_indicou: "Referred by", ind_col_indicado: "Referred person", ind_col_situacao: "Status",
  ind_marcar_pago: "Mark bonus paid", ind_desmarcar: "Undo",
});
Object.assign(I18N_GESTOR.es, {
  ind_titulo: "Recomendaciones", ind_gerar: "Crear enlace de recomendación", ind_copiar: "Copiar enlace", ind_copiado: "Copiado ✓",
  ind_link_desc: "Envía este enlace a {nome}. Quien se postule con él queda marcado como recomendado por {nome}.",
  ind_por: "Recomendado por {nome}", ind_feitas: "Personas que {nome} recomendó", ind_nenhuma: "Aún no hay recomendaciones.",
  ind_sit_inscrito: "postulado", ind_sit_contratado: "contratado, el bono vence el {d}", ind_sit_devido: "bono pendiente desde {d}", ind_sit_pago: "bono pagado el {d}",
  ind_cfg_titulo: "Programa de recomendación", ind_cfg_desc: "Cada persona del equipo puede tener un enlace personal (créalo en su ficha). El bono vence algunos días después de que contraten a la persona recomendada.",
  ind_ativo: "Programa activo", ind_valor: "Monto del bono (ej.: US$ 100)", ind_dias: "Días después de la contratación para que venza el bono",
  ind_texto: "Regla del bono (nota interna)", ind_salvar: "Guardar", ind_salvo: "Guardado.",
  ind_lista: "Recomendaciones", ind_col_indicou: "Recomendó", ind_col_indicado: "Recomendado", ind_col_situacao: "Estado",
  ind_marcar_pago: "Marcar bono pagado", ind_desmarcar: "Deshacer",
});

function indicacaoSituacao(i) {
  const d = { contratado: i.bonus_vence_em, devido: i.bonus_vence_em, pago: i.bonus_pago_em, inscrito: "" }[i.situacao];
  return tg("ind_sit_" + i.situacao, { d: d ? fmtData(d) : "" });
}

// ------------------------------------------------------------ ficha do candidato
async function indicacoesPreencherFicha(candidatoId, nome, alvo) {
  if (!alvo) return;
  let r;
  try { r = await api("/api/gestor/indicacoes/candidato/" + candidatoId); } catch (e) { alvo.remove(); return; }
  if (!r.config.ativo && !r.codigo && !r.indicado_por && !r.indicacoes.length) { alvo.remove(); return; }
  const primeiro = (nome || "").split(" ")[0];
  alvo.innerHTML = `
    ${tituloIcone("usuarios", tg("ind_titulo"))}
    ${r.indicado_por ? `<p><span class="badge ok">${esc(tg("ind_por", { nome: r.indicado_por.indicador }))}</span></p>` : ""}
    ${r.codigo ? `<p class="desc">${esc(tg("ind_link_desc", { nome: primeiro }))}</p>
      <div class="linha-acoes"><input type="text" readonly value="${esc(r.link)}" id="ind-link" style="flex:1;margin:0">
      <button class="btn secondary small" id="ind-copiar">${tg("ind_copiar")}</button></div>`
      : (r.config.ativo ? `<button class="btn secondary small" id="ind-gerar">${tg("ind_gerar")}</button>` : "")}
    ${r.codigo ? `<h4 style="margin:14px 0 6px">${esc(tg("ind_feitas", { nome: primeiro }))}</h4>
      ${r.indicacoes.length ? r.indicacoes.map((i) => `<div><a href="#" data-ind-cand="${i.indicado_id}">${esc(i.indicado)}</a>
        <span class="hint"> · ${esc(indicacaoSituacao(i))}</span></div>`).join("") : `<p class="desc">${tg("ind_nenhuma")}</p>`}` : ""}`;
  const gerar = alvo.querySelector("#ind-gerar");
  if (gerar) gerar.addEventListener("click", async () => {
    await api("/api/gestor/indicacoes/candidato/" + candidatoId, { method: "POST" });
    indicacoesPreencherFicha(candidatoId, nome, alvo);
  });
  const copiar = alvo.querySelector("#ind-copiar");
  if (copiar) copiar.addEventListener("click", () => {
    navigator.clipboard.writeText(alvo.querySelector("#ind-link").value);
    copiar.textContent = tg("ind_copiado");
  });
  alvo.querySelectorAll("[data-ind-cand]").forEach((a) => a.addEventListener("click", (ev) => {
    ev.preventDefault();
    abrirDetalheCandidato(Number(a.dataset.indCand));
  }));
}

// ------------------------------------------------------------ configurações
async function secaoIndicacoes(el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/indicacoes"); } catch (e) { el.innerHTML = ""; return; }
  const c = r.config;
  const admin = !!infoGestor().admin;
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("usuarios")}<span>${tg("ind_cfg_titulo")}</span></h2>
      <p class="desc">${tg("ind_cfg_desc")}</p>
      ${admin ? `
      <label style="display:flex;gap:8px;align-items:center;margin:6px 0"><input type="checkbox" id="ind-ativo" ${c.ativo ? "checked" : ""}> ${tg("ind_ativo")}</label>
      <div class="grid cols-2">
        <label class="field">${tg("ind_valor")}<input type="text" id="ind-valor" value="${esc(c.valor_bonus || "")}"></label>
        <label class="field">${tg("ind_dias")}<input type="number" min="0" max="365" id="ind-dias" value="${esc(String(c.dias_bonus ?? 30))}"></label>
      </div>
      <label class="field">${tg("ind_texto")}<textarea id="ind-texto" rows="2">${esc(c.texto || "")}</textarea></label>
      <div class="form-erro" id="ind-msg"></div>
      <button class="btn" id="ind-salvar">${tg("ind_salvar")}</button>` : ""}
      <h3 style="margin-top:20px">${tg("ind_lista")} (${r.indicacoes.length})</h3>
      ${r.indicacoes.length ? `<div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>${tg("ind_col_indicado")}</th><th>${tg("ind_col_indicou")}</th><th>${tg("ind_col_situacao")}</th><th></th></tr></thead>
        <tbody>${r.indicacoes.map((i) => `<tr>
          <td><a href="#" data-ind-cand="${i.indicado_id}">${esc(i.indicado)}</a></td>
          <td><a href="#" data-ind-cand="${i.indicador_id}">${esc(i.indicador)}</a></td>
          <td>${esc(indicacaoSituacao(i))}</td>
          <td>${admin && (i.situacao === "devido" || i.situacao === "contratado") ? `<button class="btn secondary small" data-ind-pago="${i.id}">${tg("ind_marcar_pago")}</button>` : ""}
              ${admin && i.situacao === "pago" ? `<button class="btn ghost small" data-ind-desfazer="${i.id}">${tg("ind_desmarcar")}</button>` : ""}</td></tr>`).join("")}</tbody>
      </table></div>` : `<p class="desc">${tg("ind_nenhuma")}</p>`}
    </div>`;
  const salvar = el.querySelector("#ind-salvar");
  if (salvar) salvar.addEventListener("click", async () => {
    const msg = el.querySelector("#ind-msg");
    try {
      await api("/api/gestor/indicacoes/config", { method: "POST", body: {
        ativo: el.querySelector("#ind-ativo").checked, valor_bonus: el.querySelector("#ind-valor").value.trim(),
        dias_bonus: Number(el.querySelector("#ind-dias").value) || 0, texto: el.querySelector("#ind-texto").value.trim(),
      } });
      msg.style.color = "var(--ok)";
      msg.textContent = tg("ind_salvo");
    } catch (e) { msg.style.color = "var(--err)"; msg.textContent = e.message; }
  });
  el.querySelectorAll("[data-ind-pago],[data-ind-desfazer]").forEach((b) => b.addEventListener("click", async () => {
    const id = b.dataset.indPago || b.dataset.indDesfazer;
    await api("/api/gestor/indicacoes/" + id + "/pago", { method: "POST", body: { pago: !!b.dataset.indPago } });
    secaoIndicacoes(el);
  }));
  el.querySelectorAll("[data-ind-cand]").forEach((a) => a.addEventListener("click", (ev) => {
    ev.preventDefault();
    abrirDetalheCandidato(Number(a.dataset.indCand));
  }));
}
