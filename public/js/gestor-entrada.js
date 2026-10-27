/* =====================================================================
   Entrada de candidatos e quadro do dia (painel do gestor).
   - quadroDoDia: Ligar hoje, Aguardando testes, Prontos para entrevista,
     Sem resposta (GET /api/gestor/prioridades).
   - secaoEntrada: caixa de e-mail que recebe as candidaturas do Indeed
     (só o administrador da empresa; a senha nunca volta do servidor).
   - modalImportarCsv: planilha exportada do Indeed, com prévia.
   Textos em pt, en e es (tg do i18n-gestor.js, chaves "en_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  en_quadro: "Quadro do dia", en_quadro_desc: "O que precisa de atenção hoje. Clique no nome para abrir a ficha.",
  en_ligar_hoje: "Ligar hoje", en_aguardando: "Aguardando testes", en_prontos: "Prontos para entrevista", en_sem_resposta: "Sem resposta",
  en_vazio: "Ninguém por aqui.", en_mais: "e mais {n}", en_callback: "pediu retorno", en_tentativas: "{n} tentativa(s)",
  en_titulo: "Entrada automática de candidatos (Indeed)",
  en_desc: "O sistema lê a cada 5 minutos a caixa de e-mail que recebe as candidaturas do Indeed e cria o candidato com o currículo anexo. A caixa é aberta só para leitura: nada é marcado como lido, movido ou apagado. No Indeed, ative o envio de um e-mail por candidatura (com currículo) para esta caixa.",
  en_host: "Servidor IMAP", en_porta: "Porta", en_usuario: "E-mail da caixa", en_senha: "Senha de app",
  en_senha_hint: "No Gmail ou Google Workspace, crie uma senha de app (Conta Google, Segurança, Senhas de app). Preencha só para trocar.",
  en_pasta: "Pasta", en_remetentes: "Remetentes aceitos", en_vaga: "Vaga para os novos candidatos", en_sem_vaga: "Usar a vaga do assunto do e-mail",
  en_auto_fila: "Novos candidatos importados (e-mail e planilha) entram na fila da Francisca automaticamente",
  en_ativo: "Ler a caixa automaticamente a cada 5 minutos",
  en_salvar: "Salvar", en_testar: "Testar conexão", en_ler: "Ler agora",
  en_salvo: "Configuração salva.", en_teste_ok: "Conexão OK. {n} e-mail(s) do Indeed encontrados na pasta.",
  en_lido: "Leitura concluída: {c} novo(s), {d} já existiam, {i} ignorado(s).",
  en_ultima: "Última leitura: {d}", en_nunca: "Ainda não leu a caixa.", en_erro_ultima: "Último erro: {e}", en_total: "Importados até agora: {n}",
  en_importar: "Importar planilha (CSV)", en_csv_titulo: "Importar candidatos de uma planilha",
  en_csv_desc: "Use o CSV exportado do Indeed (Candidatos, selecionar, Exportar) ou qualquer planilha com nome, e-mail e telefone. Ninguém é duplicado.",
  en_csv_arquivo: "Arquivo CSV", en_csv_previa: "Ver prévia", en_csv_confirmar: "Importar {n} candidato(s)",
  en_csv_resumo: "{c} novo(s), {d} já cadastrado(s), {i} sem nome ou contato",
  en_csv_feito: "{n} candidato(s) importado(s).",
  en_st_novo: "novo", en_st_criado: "importado", en_st_duplicado: "já existe", en_st_invalido: "sem dados",
  en_col_nome: "Nome", en_col_contato: "Contato", en_col_status: "Situação",
  en_e_not_configured: "Preencha servidor, e-mail e senha.", en_e_login_failed: "Não foi possível entrar na caixa: confira o e-mail e a senha de app.",
  en_e_connection_failed: "Não foi possível conectar ao servidor de e-mail.", en_e_folder_not_found: "Pasta não encontrada.",
});
Object.assign(I18N_GESTOR.en, {
  en_quadro: "Today's board", en_quadro_desc: "What needs attention today. Click a name to open the profile.",
  en_ligar_hoje: "Call today", en_aguardando: "Waiting for tests", en_prontos: "Ready for interview", en_sem_resposta: "No answer",
  en_vazio: "Nobody here.", en_mais: "and {n} more", en_callback: "asked for a callback", en_tentativas: "{n} attempt(s)",
  en_titulo: "Automatic candidate intake (Indeed)",
  en_desc: "Every 5 minutes the system reads the mailbox that receives Indeed applications and creates the candidate with the attached resume. The mailbox is opened read-only: nothing is marked as read, moved or deleted. In Indeed, turn on one email per application (with resume) to this mailbox.",
  en_host: "IMAP server", en_porta: "Port", en_usuario: "Mailbox email", en_senha: "App password",
  en_senha_hint: "In Gmail or Google Workspace, create an app password (Google Account, Security, App passwords). Fill in only to change it.",
  en_pasta: "Folder", en_remetentes: "Accepted senders", en_vaga: "Job for new candidates", en_sem_vaga: "Use the job from the email subject",
  en_auto_fila: "Imported candidates (email and spreadsheet) go to Francisca's call queue automatically",
  en_ativo: "Read the mailbox automatically every 5 minutes",
  en_salvar: "Save", en_testar: "Test connection", en_ler: "Read now",
  en_salvo: "Settings saved.", en_teste_ok: "Connection OK. {n} Indeed email(s) found in the folder.",
  en_lido: "Done: {c} new, {d} already existed, {i} ignored.",
  en_ultima: "Last read: {d}", en_nunca: "The mailbox has not been read yet.", en_erro_ultima: "Last error: {e}", en_total: "Imported so far: {n}",
  en_importar: "Import spreadsheet (CSV)", en_csv_titulo: "Import candidates from a spreadsheet",
  en_csv_desc: "Use the CSV exported from Indeed (Candidates, select, Export) or any spreadsheet with name, email and phone. Nobody is duplicated.",
  en_csv_arquivo: "CSV file", en_csv_previa: "Preview", en_csv_confirmar: "Import {n} candidate(s)",
  en_csv_resumo: "{c} new, {d} already registered, {i} without name or contact",
  en_csv_feito: "{n} candidate(s) imported.",
  en_st_novo: "new", en_st_criado: "imported", en_st_duplicado: "already exists", en_st_invalido: "missing data",
  en_col_nome: "Name", en_col_contato: "Contact", en_col_status: "Status",
  en_e_not_configured: "Fill in server, email and password.", en_e_login_failed: "Could not sign in to the mailbox: check the email and app password.",
  en_e_connection_failed: "Could not connect to the email server.", en_e_folder_not_found: "Folder not found.",
});
Object.assign(I18N_GESTOR.es, {
  en_quadro: "Tablero del día", en_quadro_desc: "Lo que necesita atención hoy. Haz clic en el nombre para abrir la ficha.",
  en_ligar_hoje: "Llamar hoy", en_aguardando: "Esperando pruebas", en_prontos: "Listos para entrevista", en_sem_resposta: "Sin respuesta",
  en_vazio: "Nadie por aquí.", en_mais: "y {n} más", en_callback: "pidió que le llamen", en_tentativas: "{n} intento(s)",
  en_titulo: "Entrada automática de candidatos (Indeed)",
  en_desc: "Cada 5 minutos el sistema lee el buzón que recibe las solicitudes de Indeed y crea el candidato con el currículum adjunto. El buzón se abre solo para lectura: nada se marca como leído, se mueve ni se borra. En Indeed, activa el envío de un correo por solicitud (con currículum) a este buzón.",
  en_host: "Servidor IMAP", en_porta: "Puerto", en_usuario: "Correo del buzón", en_senha: "Contraseña de aplicación",
  en_senha_hint: "En Gmail o Google Workspace, crea una contraseña de aplicación (Cuenta de Google, Seguridad, Contraseñas de aplicaciones). Llénala solo para cambiarla.",
  en_pasta: "Carpeta", en_remetentes: "Remitentes aceptados", en_vaga: "Vacante para los nuevos candidatos", en_sem_vaga: "Usar la vacante del asunto del correo",
  en_auto_fila: "Los candidatos importados (correo y planilla) entran en la cola de Francisca automáticamente",
  en_ativo: "Leer el buzón automáticamente cada 5 minutos",
  en_salvar: "Guardar", en_testar: "Probar conexión", en_ler: "Leer ahora",
  en_salvo: "Configuración guardada.", en_teste_ok: "Conexión OK. {n} correo(s) de Indeed en la carpeta.",
  en_lido: "Listo: {c} nuevo(s), {d} ya existían, {i} ignorado(s).",
  en_ultima: "Última lectura: {d}", en_nunca: "Todavía no se leyó el buzón.", en_erro_ultima: "Último error: {e}", en_total: "Importados hasta ahora: {n}",
  en_importar: "Importar planilla (CSV)", en_csv_titulo: "Importar candidatos desde una planilla",
  en_csv_desc: "Usa el CSV exportado de Indeed (Candidatos, seleccionar, Exportar) o cualquier planilla con nombre, correo y teléfono. Nadie se duplica.",
  en_csv_arquivo: "Archivo CSV", en_csv_previa: "Ver vista previa", en_csv_confirmar: "Importar {n} candidato(s)",
  en_csv_resumo: "{c} nuevo(s), {d} ya registrado(s), {i} sin nombre o contacto",
  en_csv_feito: "{n} candidato(s) importado(s).",
  en_st_novo: "nuevo", en_st_criado: "importado", en_st_duplicado: "ya existe", en_st_invalido: "sin datos",
  en_col_nome: "Nombre", en_col_contato: "Contacto", en_col_status: "Estado",
  en_e_not_configured: "Completa servidor, correo y contraseña.", en_e_login_failed: "No se pudo entrar al buzón: revisa el correo y la contraseña de aplicación.",
  en_e_connection_failed: "No se pudo conectar al servidor de correo.", en_e_folder_not_found: "Carpeta no encontrada.",
});

function entradaErro(msg) {
  const codigo = String(msg || "").split(":")[0];
  const chave = "en_e_" + codigo;
  return I18N_GESTOR.pt[chave] ? tg(chave) : msg;
}

// ------------------------------------------------------------ quadro do dia
async function quadroDoDia(el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/prioridades"); } catch (e) { el.remove(); return; }
  const grupos = [
    ["ligar_hoje", tg("en_ligar_hoje"), "info"],
    ["aguardando_testes", tg("en_aguardando"), "warn"],
    ["prontos", tg("en_prontos"), "ok"],
    ["sem_resposta", tg("en_sem_resposta"), "err"],
  ];
  const detalhe = (k, i) => {
    if (k === "ligar_hoje") return i.status === "callback" ? tg("en_callback") : (i.tentativas ? tg("en_tentativas", { n: i.tentativas }) : "");
    if (k === "sem_resposta") return tg("en_tentativas", { n: i.tentativas || 0 });
    return i.tier ? i.tier + (i.score != null ? " · " + i.score : "") : "";
  };
  el.innerHTML = `
    <h2 style="margin-top:0">${tg("en_quadro")}</h2>
    <p class="desc">${tg("en_quadro_desc")}</p>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px">
      ${grupos.map(([k, rot, cor]) => `
        <div class="sub-card" style="margin:0">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <strong>${rot}</strong><span class="badge ${cor}">${fmtNum(r[k].total)}</span>
          </div>
          ${r[k].itens.length ? r[k].itens.map((i) => `
            <div style="padding:5px 0;border-top:1px solid var(--line, rgba(127,127,127,.15))">
              <a href="#" data-quadro-cand="${i.candidato_id}"><strong>${esc(i.nome)}</strong></a>
              <div class="hint">${esc(i.vaga || "")}${detalhe(k, i) ? " · " + esc(detalhe(k, i)) : ""}</div>
            </div>`).join("") : `<p class="desc" style="margin:0">${tg("en_vazio")}</p>`}
          ${r[k].total > r[k].itens.length ? `<p class="hint" style="margin:6px 0 0">${tg("en_mais", { n: r[k].total - r[k].itens.length })}</p>` : ""}
        </div>`).join("")}
    </div>`;
  el.querySelectorAll("[data-quadro-cand]").forEach((a) => a.addEventListener("click", (ev) => {
    ev.preventDefault();
    abrirDetalheCandidato(Number(a.dataset.quadroCand));
  }));
}

// ------------------------------------------------------------ configuração da caixa
async function secaoEntrada(el) {
  if (!el || !infoGestor().admin) return;
  let r;
  try { r = await api("/api/gestor/entrada"); } catch (e) { el.innerHTML = ""; return; }
  const c = r.config;
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("documento")}<span>${tg("en_titulo")}</span></h2>
      <p class="desc">${tg("en_desc")}</p>
      <div class="grid cols-2">
        <label class="field">${tg("en_usuario")}<input type="email" id="en-usuario" value="${esc(c.usuario || "")}" autocomplete="off"></label>
        <label class="field">${tg("en_senha")} <span class="hint">${c.senha_configurada ? "✓" : ""}</span>
          <input type="password" id="en-senha" autocomplete="new-password" placeholder="${c.senha_configurada ? "••••••••" : ""}">
          <span class="hint">${tg("en_senha_hint")}</span></label>
        <label class="field">${tg("en_host")}<input type="text" id="en-host" value="${esc(c.imap_host || "")}"></label>
        <div class="grid cols-2">
          <label class="field">${tg("en_porta")}<input type="text" id="en-porta" value="${esc(String(c.imap_porta || 993))}"></label>
          <label class="field">${tg("en_pasta")}<input type="text" id="en-pasta" value="${esc(c.pasta || "INBOX")}"></label>
        </div>
        <label class="field">${tg("en_vaga")}
          <select id="en-vaga"><option value="">${tg("en_sem_vaga")}</option>
            ${r.vagas.map((v) => `<option value="${v.id}" ${c.vaga_id === v.id ? "selected" : ""}>${esc(v.titulo)}</option>`).join("")}
          </select></label>
        <label class="field">${tg("en_remetentes")}<input type="text" id="en-remetentes" value="${esc(c.remetentes || "")}"></label>
      </div>
      <label style="display:flex;gap:8px;align-items:center;margin:6px 0"><input type="checkbox" id="en-auto" ${c.auto_fila ? "checked" : ""}> ${tg("en_auto_fila")}</label>
      <label style="display:flex;gap:8px;align-items:center;margin:6px 0 12px"><input type="checkbox" id="en-ativo" ${c.ativo ? "checked" : ""}> ${tg("en_ativo")}</label>
      <p class="hint">${c.ultima_execucao ? tg("en_ultima", { d: fmtDataHora(c.ultima_execucao) }) : tg("en_nunca")}
        · ${tg("en_total", { n: fmtNum(c.importados || 0) })}
        ${c.ultimo_erro ? `<br><span style="color:var(--err)">${esc(tg("en_erro_ultima", { e: entradaErro(c.ultimo_erro) }))}</span>` : ""}</p>
      <div class="form-erro" id="en-msg"></div>
      <div class="linha-acoes">
        <button class="btn" id="en-salvar">${tg("en_salvar")}</button>
        <button class="btn secondary" id="en-testar">${tg("en_testar")}</button>
        <button class="btn secondary" id="en-ler">${tg("en_ler")}</button>
      </div>
    </div>`;
  const msg = (texto, ok) => {
    const m = el.querySelector("#en-msg");
    m.style.color = ok ? "var(--ok)" : "var(--err)";
    m.textContent = texto;
  };
  const salvar = async () => {
    const corpo = {
      usuario: el.querySelector("#en-usuario").value.trim(), imap_host: el.querySelector("#en-host").value.trim(),
      imap_porta: el.querySelector("#en-porta").value.trim(), pasta: el.querySelector("#en-pasta").value.trim(),
      remetentes: el.querySelector("#en-remetentes").value.trim(), vaga_id: Number(el.querySelector("#en-vaga").value) || null,
      auto_fila: el.querySelector("#en-auto").checked, ativo: el.querySelector("#en-ativo").checked,
    };
    const senha = el.querySelector("#en-senha").value;
    if (senha) corpo.senha = senha;
    await api("/api/gestor/entrada", { method: "POST", body: corpo });
  };
  el.querySelector("#en-salvar").addEventListener("click", async () => {
    try { await salvar(); msg(tg("en_salvo"), true); setTimeout(() => secaoEntrada(el), 900); } catch (e) { msg(entradaErro(e.message)); }
  });
  el.querySelector("#en-testar").addEventListener("click", async () => {
    msg(tg("carregando"), true);
    try {
      await salvar();
      const t = await api("/api/gestor/entrada/testar", { method: "POST" });
      msg(tg("en_teste_ok", { n: t.mensagens_indeed }), true);
    } catch (e) { msg(entradaErro(e.message)); }
  });
  el.querySelector("#en-ler").addEventListener("click", async () => {
    msg(tg("carregando"), true);
    try {
      await salvar();
      const t = await api("/api/gestor/entrada/ler", { method: "POST" });
      msg(tg("en_lido", { c: t.criados, d: t.duplicados, i: t.ignoradas }), true);
      if (t.criados && typeof carregarDados === "function") carregarDados();
    } catch (e) { msg(entradaErro(e.message)); }
  });
}

// ------------------------------------------------------------ importação de CSV
async function modalImportarCsv(aoTerminar) {
  let vagas = [];
  try { vagas = (await api("/api/gestor/entrada")).vagas; } catch (e) { /* sem vagas */ }
  let base64 = "";
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal" style="max-width:760px">
      <button class="btn ghost small fechar" id="csv-fechar">${icone("fechar")}</button>
      <h2>${tg("en_csv_titulo")}</h2>
      <p class="desc">${tg("en_csv_desc")}</p>
      <div class="grid cols-2">
        <label class="field">${tg("en_csv_arquivo")}<input type="file" id="csv-arquivo" accept=".csv,text/csv"></label>
        <label class="field">${tg("en_vaga")}
          <select id="csv-vaga"><option value="">·</option>
            ${vagas.map((v, i) => `<option value="${v.id}" ${i === 0 ? "selected" : ""}>${esc(v.titulo)}</option>`).join("")}</select></label>
      </div>
      <label style="display:flex;gap:8px;align-items:center;margin:4px 0 12px"><input type="checkbox" id="csv-auto"> ${tg("en_auto_fila")}</label>
      <div class="form-erro" id="csv-msg"></div>
      <div id="csv-previa"></div>
      <div class="linha-acoes">
        <button class="btn secondary" id="csv-ver" disabled>${tg("en_csv_previa")}</button>
        <button class="btn" id="csv-importar" disabled>${tg("en_csv_confirmar", { n: 0 })}</button>
      </div>
    </div>`;
  document.body.appendChild(fundo);
  const $ = (s) => fundo.querySelector(s);
  const fechar = () => fundo.remove();
  $("#csv-fechar").addEventListener("click", fechar);
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fechar(); });
  const corpo = (aplicar) => ({ base64, vaga_id: Number($("#csv-vaga").value) || null, auto_fila: $("#csv-auto").checked, aplicar });
  const mostrar = (r) => {
    $("#csv-previa").innerHTML = `
      <p><strong>${tg("en_csv_resumo", { c: r.criados, d: r.duplicados, i: r.invalidos })}</strong></p>
      <div class="tabela-wrap" style="max-height:300px;overflow:auto"><table class="tabela">
        <thead><tr><th>${tg("en_col_nome")}</th><th>${tg("en_col_contato")}</th><th>${tg("en_col_status")}</th></tr></thead>
        <tbody>${r.linhas.slice(0, 300).map((l) => `<tr><td>${esc(l.nome || "·")}<div class="hint">${esc(l.local || "")}</div></td>
          <td>${esc(l.email || "")}<div class="hint">${esc(l.telefone || "")}</div></td>
          <td><span class="badge ${{ novo: "info", criado: "ok", duplicado: "", invalido: "err" }[l.status] || ""}">${tg("en_st_" + l.status)}</span></td></tr>`).join("")}</tbody>
      </table></div>`;
  };
  $("#csv-arquivo").addEventListener("change", () => {
    const f = $("#csv-arquivo").files[0];
    if (!f) return;
    const leitor = new FileReader();
    leitor.onload = () => { base64 = String(leitor.result).split(",")[1] || ""; $("#csv-ver").disabled = !base64; };
    leitor.readAsDataURL(f);
  });
  $("#csv-ver").addEventListener("click", async () => {
    try {
      const r = await api("/api/gestor/importar-csv", { method: "POST", body: corpo(false) });
      mostrar(r);
      $("#csv-importar").disabled = !r.criados;
      $("#csv-importar").textContent = tg("en_csv_confirmar", { n: r.criados });
    } catch (e) { $("#csv-msg").textContent = e.message; }
  });
  $("#csv-importar").addEventListener("click", async () => {
    $("#csv-importar").disabled = true;
    try {
      const r = await api("/api/gestor/importar-csv", { method: "POST", body: corpo(true) });
      mostrar(r);
      const m = $("#csv-msg");
      m.style.color = "var(--ok)";
      m.textContent = tg("en_csv_feito", { n: r.criados });
      if (aoTerminar) aoTerminar();
    } catch (e) { $("#csv-msg").textContent = e.message; $("#csv-importar").disabled = false; }
  });
}
