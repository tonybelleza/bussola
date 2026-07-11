/* =====================================================================
   Tema claro/escuro. Carregar no <head> de todas as páginas:
   aplica o tema salvo antes da pintura (sem piscar) e injeta o botão
   de alternância na barra superior.
   ===================================================================== */

(function () {
  const salvo = localStorage.getItem("tema");
  if (salvo === "claro") document.documentElement.dataset.tema = "claro";

  const SOL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 2.5v2.5"/><path d="M12 19v2.5"/><path d="M2.5 12H5"/><path d="M19 12h2.5"/><path d="M5.3 5.3l1.8 1.8"/><path d="M16.9 16.9l1.8 1.8"/><path d="M18.7 5.3l-1.8 1.8"/><path d="M7.1 16.9l-1.8 1.8"/></svg>';
  const LUA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>';

  function desenharIcone(btn) {
    btn.innerHTML = document.documentElement.dataset.tema === "claro" ? LUA : SOL;
    btn.title = document.documentElement.dataset.tema === "claro" ? "Tema escuro" : "Tema claro";
  }

  document.addEventListener("DOMContentLoaded", function () {
    const acoes = document.querySelector(".topbar .actions");
    if (!acoes) return;
    const btn = document.createElement("button");
    btn.className = "btn-tema";
    btn.setAttribute("aria-label", "Alternar tema claro e escuro");
    desenharIcone(btn);
    btn.addEventListener("click", function () {
      const claro = document.documentElement.dataset.tema === "claro";
      if (claro) {
        delete document.documentElement.dataset.tema;
        localStorage.setItem("tema", "escuro");
      } else {
        document.documentElement.dataset.tema = "claro";
        localStorage.setItem("tema", "claro");
      }
      desenharIcone(btn);
    });
    acoes.appendChild(btn);
  });
})();
