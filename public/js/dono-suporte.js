/* =====================================================================
   Painel do Dono: "Entrar no painel como administrador" (suporte) e
   exclusões de contas pendentes (conta.py). Textos em pt, en e es.
   O dono recebe um código de uso único (2 minutos) e abre /gestor#suporte=código
   numa aba nova; o token da sessão nunca passa pela URL.
   ===================================================================== */

Object.assign(I18N_DONO.pt, {
  sup_botao: "Entrar no painel como admin",
  sup_confirmar: "Entrar no painel de {empresa} como administrador (modo suporte, 2 horas)? Tudo o que você fizer fica no histórico de acessos da empresa.",
  sup_bloqueado: "O navegador bloqueou a aba nova. Permita pop-ups para este site e tente de novo.",
  exc_titulo: "Exclusões pendentes",
  exc_desc: "Contas encerradas pelas empresas. Os dados são apagados em definitivo na data indicada.",
  exc_data: "Exclusão em {data}",
  exc_por: "encerrada por {nome} em {data}",
  exc_cancelar: "Cancelar exclusão",
  exc_cancelar_confirmar: "Cancelar a exclusão de {empresa} e reativar a conta?",
  exc_cancelada: "Exclusão cancelada. A conta voltou a ficar ativa.",
});
Object.assign(I18N_DONO.en, {
  sup_botao: "Enter panel as admin",
  sup_confirmar: "Enter the {empresa} panel as admin (support mode, 2 hours)? Everything you do is recorded in the company's access history.",
  sup_bloqueado: "The browser blocked the new tab. Allow pop-ups for this site and try again.",
  exc_titulo: "Pending deletions",
  exc_desc: "Accounts closed by the companies. Data is permanently deleted on the date shown.",
  exc_data: "Deletion on {data}",
  exc_por: "closed by {nome} on {data}",
  exc_cancelar: "Cancel deletion",
  exc_cancelar_confirmar: "Cancel the deletion of {empresa} and reactivate the account?",
  exc_cancelada: "Deletion canceled. The account is active again.",
});
Object.assign(I18N_DONO.es, {
  sup_botao: "Entrar al panel como admin",
  sup_confirmar: "¿Entrar al panel de {empresa} como administrador (modo soporte, 2 horas)? Todo lo que hagas queda en el historial de accesos de la empresa.",
  sup_bloqueado: "El navegador bloqueó la pestaña nueva. Permite ventanas emergentes para este sitio e inténtalo de nuevo.",
  exc_titulo: "Eliminaciones pendientes",
  exc_desc: "Cuentas cerradas por las empresas. Los datos se eliminan de forma definitiva en la fecha indicada.",
  exc_data: "Eliminación el {data}",
  exc_por: "cerrada por {nome} el {data}",
  exc_cancelar: "Cancelar eliminación",
  exc_cancelar_confirmar: "¿Cancelar la eliminación de {empresa} y reactivar la cuenta?",
  exc_cancelada: "Eliminación cancelada. La cuenta volvió a estar activa.",
});

function donoData(s) {
  const d = new Date(String(s || "").replace(" ", "T") + "Z");
  return isNaN(d) ? "" : d.toLocaleDateString(LANG_HTML_DONO[idiomaDono] || "en-US");
}

// botão no cartão da empresa (só para empresas ativas ou em teste)
function donoSuporteBotao(e) {
  if (!e || !["ativa", "teste"].includes(e.status)) return "";
  return `<button class="btn secondary small" data-suporte-empresa="${e.id}" data-suporte-nome="${esc(e.nome)}">${td("sup_botao")}</button>`;
}

function donoSuporteLigar(el) {
  el.querySelectorAll("[data-suporte-empresa]").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm(td("sup_confirmar", { empresa: b.dataset.suporteNome }))) return;
    // abre a aba já no clique (evita o bloqueio de pop-up) e só depois põe o endereço
    const aba = window.open("about:blank", "_blank");
    try {
      const r = await api("/api/dono/conta/suporte/" + b.dataset.suporteEmpresa, { method: "POST" });
      if (!aba) { alert(td("sup_bloqueado")); return; }
      aba.opener = null;
      aba.location.href = "/gestor#suporte=" + encodeURIComponent(r.codigo);
    } catch (e) {
      if (aba) aba.close();
      alert(e.message);
    }
  }));
}

// lista de exclusões pendentes, no topo da aba Empresas
async function donoExclusoesPendentes(box) {
  if (!box) return;
  let r;
  try { r = await api("/api/dono/conta/exclusoes"); } catch (e) { box.innerHTML = ""; return; }
  if (!r.exclusoes.length) { box.innerHTML = ""; return; }
  box.innerHTML = `
    <div class="card" style="border-color:var(--err)">
      <h2 class="icone-titulo">${icone("lixeira")}<span>${td("exc_titulo")}</span></h2>
      <p class="desc">${td("exc_desc")}</p>
      ${r.exclusoes.map((x) => `
        <div class="comp-item" style="margin-top:10px;display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
          <span><strong>${esc(x.nome)}</strong> <span class="badge err">${esc(td("exc_data", { data: donoData(x.exclusao_em) }))}</span>
            <br><span style="color:var(--muted);font-size:.8rem">${esc(td("exc_por", { nome: x.encerrada_por || "?", data: donoData(x.encerrada_em) }))}</span></span>
          <button class="btn small" data-cancelar-exclusao="${x.id}" data-nome="${esc(x.nome)}">${td("exc_cancelar")}</button>
        </div>`).join("")}
    </div>`;
  box.querySelectorAll("[data-cancelar-exclusao]").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm(td("exc_cancelar_confirmar", { empresa: b.dataset.nome }))) return;
    try {
      await api("/api/dono/conta/exclusao/" + b.dataset.cancelarExclusao + "/cancelar", { method: "POST" });
      alert(td("exc_cancelada"));
      desenhar();
    } catch (e) { alert(e.message); }
  }));
}
