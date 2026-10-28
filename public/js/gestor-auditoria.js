/* =====================================================================
   Histórico de acessos (trilha de auditoria) no painel do gestor.
   Só o administrador da empresa vê. Dados de GET /api/gestor/auditoria.
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  au_titulo: "Histórico de acessos", au_desc: "Quem entrou no painel, abriu fichas, baixou currículos, ouviu ligações ou alterou dados nesta empresa. Fica guardado para consulta.",
  au_ver: "Ver histórico", au_mais: "Carregar mais", au_vazio: "Nenhum registro ainda.",
  au_quando: "Quando", au_quem: "Quem", au_acao: "Ação", au_ip: "IP",
  au_login: "Entrou no painel", au_login_falhou: "Tentativa de login com senha errada ({a})", au_ver_candidato: "Abriu a ficha do candidato #{a}",
  au_baixar_curriculo: "Baixou o currículo do candidato #{a}", au_baixar_relatorio: "Baixou o relatório do candidato #{a}",
  au_ouvir_ligacao: "Ouviu a ligação #{a}", au_post: "Alterou: {a}", au_delete: "Excluiu: {a}",
});
Object.assign(I18N_GESTOR.en, {
  au_titulo: "Access history", au_desc: "Who signed in, opened profiles, downloaded resumes, listened to calls or changed data in this company. Kept for reference.",
  au_ver: "View history", au_mais: "Load more", au_vazio: "No records yet.",
  au_quando: "When", au_quem: "Who", au_acao: "Action", au_ip: "IP",
  au_login: "Signed in", au_login_falhou: "Sign in attempt with wrong password ({a})", au_ver_candidato: "Opened candidate #{a}",
  au_baixar_curriculo: "Downloaded the resume of candidate #{a}", au_baixar_relatorio: "Downloaded the report of candidate #{a}",
  au_ouvir_ligacao: "Listened to call #{a}", au_post: "Changed: {a}", au_delete: "Deleted: {a}",
});
Object.assign(I18N_GESTOR.es, {
  au_titulo: "Historial de accesos", au_desc: "Quién entró al panel, abrió fichas, descargó currículums, escuchó llamadas o cambió datos en esta empresa. Queda guardado para consulta.",
  au_ver: "Ver historial", au_mais: "Cargar más", au_vazio: "Aún no hay registros.",
  au_quando: "Cuándo", au_quem: "Quién", au_acao: "Acción", au_ip: "IP",
  au_login: "Entró al panel", au_login_falhou: "Intento de inicio de sesión con contraseña incorrecta ({a})", au_ver_candidato: "Abrió la ficha del candidato #{a}",
  au_baixar_curriculo: "Descargó el currículum del candidato #{a}", au_baixar_relatorio: "Descargó el informe del candidato #{a}",
  au_ouvir_ligacao: "Escuchó la llamada #{a}", au_post: "Cambió: {a}", au_delete: "Eliminó: {a}",
});

function auditoriaTexto(r) {
  const [verbo, ...resto] = String(r.acao || "").split(" ");
  if (verbo === "post" || verbo === "delete") return tg("au_" + verbo, { a: resto.join(" ") });
  const chave = "au_" + r.acao;
  return I18N_GESTOR.pt[chave] ? tg(chave, { a: r.alvo || "" }) : r.acao;
}

async function secaoAuditoria(el) {
  if (!el || !infoGestor().admin) return;
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("chave")}<span>${tg("au_titulo")}</span></h2>
      <p class="desc">${tg("au_desc")}</p>
      <button class="btn secondary small" id="au-ver">${tg("au_ver")}</button>
      <div id="au-lista"></div>
    </div>`;
  let ultimo = null;
  const lista = el.querySelector("#au-lista");
  const carregar = async () => {
    const r = await api("/api/gestor/auditoria?limite=100" + (ultimo ? "&antes=" + ultimo : ""));
    if (!r.registros.length && !ultimo) {
      lista.innerHTML = `<p class="desc">${tg("au_vazio")}</p>`;
      return;
    }
    if (!ultimo) {
      lista.innerHTML = `<div class="tabela-wrap mt" style="max-height:420px;overflow:auto"><table class="tabela">
        <thead><tr><th>${tg("au_quando")}</th><th>${tg("au_quem")}</th><th>${tg("au_acao")}</th><th>${tg("au_ip")}</th></tr></thead>
        <tbody id="au-corpo"></tbody></table></div><button class="btn ghost small mt" id="au-mais">${tg("au_mais")}</button>`;
      lista.querySelector("#au-mais").addEventListener("click", carregar);
    }
    lista.querySelector("#au-corpo").insertAdjacentHTML("beforeend", r.registros.map((x) => `
      <tr><td style="white-space:nowrap">${esc(fmtDataHora(x.criado_em))}</td><td>${esc(x.quem || "·")}</td>
        <td>${esc(auditoriaTexto(x))}</td><td class="hint">${esc(x.ip || "")}</td></tr>`).join(""));
    if (r.registros.length) ultimo = r.registros[r.registros.length - 1].id;
    const mais = lista.querySelector("#au-mais");
    if (mais && r.registros.length < 100) mais.remove();
  };
  el.querySelector("#au-ver").addEventListener("click", async (ev) => {
    ev.target.remove();
    try { await carregar(); } catch (e) { lista.innerHTML = `<p class="form-erro">${esc(e.message)}</p>`; }
  });
}
