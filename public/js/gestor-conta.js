/* =====================================================================
   Conta da empresa no painel do gestor (conta.py):
   - Configurações: consentimento para ligações e mensagens automáticas
     (fila só para quem consentiu) e frase sugerida para o anúncio no Indeed;
   - Configurações > Dados e conta: exportar todos os dados (ZIP) e encerrar a conta;
   - selo de consentimento na ficha do candidato;
   - modo suporte do dono: troca do código (#suporte=...) por uma sessão de 2 horas
     e faixa vermelha fixa com o botão para encerrar.
   Textos em pt, en e es (tg de i18n-gestor.js).
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  cs_banner: "Modo suporte: você está vendo {empresa} como dono da plataforma.",
  cs_banner_expira: "A sessão termina às {hora}.",
  cs_encerrar: "Encerrar sessão de suporte",
  cs_encerrada: "Sessão de suporte encerrada. Você já pode fechar esta aba.",
  cs_codigo_invalido: "O link de suporte expirou ou já foi usado. Gere outro no painel do dono.",
  cs_indisponivel: "Indisponível no modo suporte.",
  ct_cfg_titulo: "Ligações e mensagens automáticas",
  ct_cfg_desc: "Lei dos EUA (TCPA): ligações e mensagens com tecnologia automatizada ou IA pedem consentimento por escrito. O cadastro tem uma caixa separada para isso; candidatos importados (CSV ou Indeed) chegam sem consentimento escrito.",
  ct_cfg_fila: "Fila automática de ligações só para candidatos que consentiram",
  ct_cfg_fila_desc: "Desligado: a fila liga como antes. Ligado: quem não marcou a caixa (ou foi importado) fica fora da fila automática; você ainda pode ligar manualmente. Quem pediu para parar nunca recebe ligações automáticas.",
  ct_cfg_salvo: "Configuração salva.",
  ct_cfg_so_admin: "Só o administrador da empresa altera esta configuração.",
  ct_anuncio_titulo: "Frase sugerida para o anúncio da vaga no Indeed",
  ct_anuncio_desc: "Cole no fim da descrição da vaga. Ajuda a registrar o aviso de contato para quem se candidata pelo Indeed (não substitui a caixa de consentimento do cadastro).",
  ct_lang_en: "Inglês", ct_lang_pt: "Português", ct_lang_es: "Espanhol",
  ct_copiar: "Copiar",
  ct_badge_consentiu: "Consentiu ligações e mensagens em {data}",
  ct_badge_importado: "Importado, sem consentimento escrito",
  ct_badge_sem: "Sem consentimento para ligações automáticas",
  ct_badge_revogado: "Pediu para parar ligações e mensagens em {data}",
  dc_titulo: "Dados e conta",
  dc_exportar_titulo: "Exportar todos os dados",
  dc_exportar_desc: "Gera um arquivo ZIP com JSON e CSV de candidatos, candidaturas, linha do tempo, testes, entrevistas, ligações (dados e transcrições), onboarding, além dos currículos e PDFs dos modelos. Fica pronto em alguns minutos; o link vale 24 horas e só para você.",
  dc_sensivel: "Incluir dados sensíveis (só mascarados, como ••••1234)",
  dc_senha: "Sua senha (obrigatória para dados sensíveis)",
  dc_exportar: "Exportar dados",
  dc_preparando: "Preparando…",
  dc_pronto: "Pronto",
  dc_erro: "Falhou",
  dc_expirado: "Expirado",
  dc_baixar: "Baixar ZIP",
  dc_vale_ate: "vale até {data}",
  dc_com_sensivel: "com dados sensíveis mascarados",
  dc_atualizar: "Atualizar",
  dc_nenhuma: "Nenhuma exportação ainda.",
  dc_encerrar_titulo: "Encerrar a conta",
  dc_encerrar_desc: "A conta fica cancelada na hora e todos os dados da empresa (candidatos, arquivos, onboarding, ligações) são apagados em definitivo em 30 dias. Até lá, fale com o suporte para desfazer. Exporte os dados antes.",
  dc_encerrar_digite: "Digite o nome da empresa para confirmar: {empresa}",
  dc_encerrar: "Encerrar a conta",
  dc_encerrar_confirmar: "Encerrar a conta de {empresa}? Todos os dados serão apagados em definitivo em 30 dias.",
  dc_encerrada: "Conta encerrada. Os dados serão apagados em {data}.",
  au_suporte_iniciado: "Dono da plataforma gerou acesso de suporte",
  au_suporte_entrou: "Acesso de suporte iniciado (dono da plataforma)",
  au_suporte_encerrado: "Acesso de suporte encerrado",
  au_exportacao_pedida: "Pediu a exportação de todos os dados",
  au_exportacao_baixada: "Baixou a exportação de dados #{a}",
  au_conta_encerrada: "Encerrou a conta (exclusão em {a})",
  au_exclusao_cancelada: "Dono da plataforma cancelou a exclusão da conta",
  au_contato_revogado: "Candidato pediu para parar ligações e mensagens ({a})",
});
Object.assign(I18N_GESTOR.en, {
  cs_banner: "Support mode: you are viewing {empresa} as the platform owner.",
  cs_banner_expira: "The session ends at {hora}.",
  cs_encerrar: "End support session",
  cs_encerrada: "Support session ended. You can close this tab.",
  cs_codigo_invalido: "The support link expired or was already used. Create a new one in the owner panel.",
  cs_indisponivel: "Not available in support mode.",
  ct_cfg_titulo: "Automated calls and texts",
  ct_cfg_desc: "US law (TCPA): calls and texts that use automated technology or AI require written consent. The sign-up form has a separate checkbox for it; imported candidates (CSV or Indeed) arrive without written consent.",
  ct_cfg_fila: "Automatic call queue only for candidates who consented",
  ct_cfg_fila_desc: "Off: the queue calls as before. On: anyone who did not check the box (or was imported) stays out of the automatic queue; you can still call manually. Anyone who asked to stop never gets automated calls.",
  ct_cfg_salvo: "Setting saved.",
  ct_cfg_so_admin: "Only the company admin can change this setting.",
  ct_anuncio_titulo: "Suggested sentence for your Indeed job posting",
  ct_anuncio_desc: "Paste it at the end of the job description. It helps document the contact notice for people who apply through Indeed (it does not replace the consent checkbox on the sign-up form).",
  ct_lang_en: "English", ct_lang_pt: "Portuguese", ct_lang_es: "Spanish",
  ct_copiar: "Copy",
  ct_badge_consentiu: "Agreed to calls and texts on {data}",
  ct_badge_importado: "Imported, no written consent",
  ct_badge_sem: "No consent for automated calls",
  ct_badge_revogado: "Asked to stop calls and texts on {data}",
  dc_titulo: "Data and account",
  dc_exportar_titulo: "Export all data",
  dc_exportar_desc: "Creates a ZIP file with JSON and CSV for candidates, applications, timeline, tests, interviews, calls (metadata and transcripts) and onboarding, plus resumes and template PDFs. It is ready in a few minutes; the link is valid for 24 hours and only for you.",
  dc_sensivel: "Include sensitive data (masked only, like ••••1234)",
  dc_senha: "Your password (required for sensitive data)",
  dc_exportar: "Export data",
  dc_preparando: "Preparing…",
  dc_pronto: "Ready",
  dc_erro: "Failed",
  dc_expirado: "Expired",
  dc_baixar: "Download ZIP",
  dc_vale_ate: "valid until {data}",
  dc_com_sensivel: "with masked sensitive data",
  dc_atualizar: "Refresh",
  dc_nenhuma: "No exports yet.",
  dc_encerrar_titulo: "Close account",
  dc_encerrar_desc: "The account is canceled right away and all company data (candidates, files, onboarding, calls) is permanently deleted in 30 days. Until then, contact support to undo it. Export your data first.",
  dc_encerrar_digite: "Type the company name to confirm: {empresa}",
  dc_encerrar: "Close account",
  dc_encerrar_confirmar: "Close the {empresa} account? All data will be permanently deleted in 30 days.",
  dc_encerrada: "Account closed. Data will be deleted on {data}.",
  au_suporte_iniciado: "Platform owner created support access",
  au_suporte_entrou: "Support access started (platform owner)",
  au_suporte_encerrado: "Support access ended",
  au_exportacao_pedida: "Requested an export of all data",
  au_exportacao_baixada: "Downloaded data export #{a}",
  au_conta_encerrada: "Closed the account (deletion on {a})",
  au_exclusao_cancelada: "Platform owner canceled the account deletion",
  au_contato_revogado: "Candidate asked to stop calls and texts ({a})",
});
Object.assign(I18N_GESTOR.es, {
  cs_banner: "Modo soporte: estás viendo {empresa} como dueño de la plataforma.",
  cs_banner_expira: "La sesión termina a las {hora}.",
  cs_encerrar: "Terminar sesión de soporte",
  cs_encerrada: "Sesión de soporte terminada. Ya puedes cerrar esta pestaña.",
  cs_codigo_invalido: "El enlace de soporte venció o ya se usó. Genera otro en el panel del dueño.",
  cs_indisponivel: "No disponible en modo soporte.",
  ct_cfg_titulo: "Llamadas y mensajes automáticos",
  ct_cfg_desc: "Ley de EE. UU. (TCPA): las llamadas y los mensajes con tecnología automatizada o IA requieren consentimiento por escrito. El registro tiene una casilla aparte para eso; los candidatos importados (CSV o Indeed) llegan sin consentimiento por escrito.",
  ct_cfg_fila: "Cola automática de llamadas solo para candidatos que dieron su consentimiento",
  ct_cfg_fila_desc: "Apagado: la cola llama como antes. Encendido: quien no marcó la casilla (o fue importado) queda fuera de la cola automática; igual puedes llamar manualmente. Quien pidió que dejaran de llamar nunca recibe llamadas automáticas.",
  ct_cfg_salvo: "Configuración guardada.",
  ct_cfg_so_admin: "Solo el administrador de la empresa cambia esta configuración.",
  ct_anuncio_titulo: "Frase sugerida para el anuncio de la vacante en Indeed",
  ct_anuncio_desc: "Pégala al final de la descripción de la vacante. Ayuda a dejar constancia del aviso de contacto para quienes se postulan por Indeed (no reemplaza la casilla de consentimiento del registro).",
  ct_lang_en: "Inglés", ct_lang_pt: "Portugués", ct_lang_es: "Español",
  ct_copiar: "Copiar",
  ct_badge_consentiu: "Autorizó llamadas y mensajes el {data}",
  ct_badge_importado: "Importado, sin consentimiento por escrito",
  ct_badge_sem: "Sin consentimiento para llamadas automáticas",
  ct_badge_revogado: "Pidió dejar de recibir llamadas y mensajes el {data}",
  dc_titulo: "Datos y cuenta",
  dc_exportar_titulo: "Exportar todos los datos",
  dc_exportar_desc: "Genera un archivo ZIP con JSON y CSV de candidatos, postulaciones, historial, pruebas, entrevistas, llamadas (datos y transcripciones) y onboarding, además de los currículums y los PDF de las plantillas. Queda listo en unos minutos; el enlace vale 24 horas y solo para ti.",
  dc_sensivel: "Incluir datos sensibles (solo enmascarados, como ••••1234)",
  dc_senha: "Tu contraseña (obligatoria para datos sensibles)",
  dc_exportar: "Exportar datos",
  dc_preparando: "Preparando…",
  dc_pronto: "Listo",
  dc_erro: "Falló",
  dc_expirado: "Vencido",
  dc_baixar: "Descargar ZIP",
  dc_vale_ate: "vale hasta {data}",
  dc_com_sensivel: "con datos sensibles enmascarados",
  dc_atualizar: "Actualizar",
  dc_nenhuma: "Aún no hay exportaciones.",
  dc_encerrar_titulo: "Cerrar la cuenta",
  dc_encerrar_desc: "La cuenta queda cancelada de inmediato y todos los datos de la empresa (candidatos, archivos, onboarding, llamadas) se eliminan de forma definitiva en 30 días. Hasta entonces, contacta a soporte para deshacerlo. Exporta tus datos antes.",
  dc_encerrar_digite: "Escribe el nombre de la empresa para confirmar: {empresa}",
  dc_encerrar: "Cerrar la cuenta",
  dc_encerrar_confirmar: "¿Cerrar la cuenta de {empresa}? Todos los datos se eliminarán de forma definitiva en 30 días.",
  dc_encerrada: "Cuenta cerrada. Los datos se eliminarán el {data}.",
  au_suporte_iniciado: "El dueño de la plataforma generó un acceso de soporte",
  au_suporte_entrou: "Acceso de soporte iniciado (dueño de la plataforma)",
  au_suporte_encerrado: "Acceso de soporte terminado",
  au_exportacao_pedida: "Pidió exportar todos los datos",
  au_exportacao_baixada: "Descargó la exportación de datos #{a}",
  au_conta_encerrada: "Cerró la cuenta (eliminación el {a})",
  au_exclusao_cancelada: "El dueño de la plataforma canceló la eliminación de la cuenta",
  au_contato_revogado: "El candidato pidió dejar de recibir llamadas y mensajes ({a})",
});

// ------------------------------------------------ utilidades
function contaData(s, comHora) {
  const d = new Date(String(s || "").replace(" ", "T") + (String(s || "").endsWith("Z") ? "" : "Z"));
  if (isNaN(d)) return "";
  const loc = { pt: "pt-BR", en: "en-US", es: "es-US" }[idiomaGestor] || "en-US";
  return comHora ? d.toLocaleString(loc, { dateStyle: "short", timeStyle: "short" }) : d.toLocaleDateString(loc);
}

// ------------------------------------------------ selo na ficha do candidato
function contaBadgeConsentimento(cc) {
  if (!cc) return "";
  if (cc.estado === "consentiu") return `<span class="badge ok" title="${esc(cc.texto || "")}">${esc(tg("ct_badge_consentiu", { data: contaData(cc.em) }))}</span>`;
  if (cc.estado === "revogado") return `<span class="badge err">${esc(tg("ct_badge_revogado", { data: contaData(cc.revogado_em) }))}</span>`;
  if (cc.estado === "importado") return `<span class="badge warn">${esc(tg("ct_badge_importado"))}</span>`;
  return `<span class="badge tipo">${esc(tg("ct_badge_sem"))}</span>`;
}

// ------------------------------------------------ modo suporte do dono
// A aba aberta pelo dono chega com /gestor#suporte=CODIGO (o código não vai ao servidor
// na URL, vale 2 minutos e uma única vez). Trocamos por uma sessão de 2 horas.
async function contaBootSuporte() {
  const m = location.hash.match(/^#suporte=([A-Za-z0-9_-]{20,200})$/);
  if (!m) return false;
  history.replaceState(null, "", location.pathname);
  try {
    const r = await api("/api/gestor/suporte/entrar", { method: "POST", body: { codigo: m[1] } });
    salvarSessao(r);
    const info = infoGestor();
    info.suporte = r.suporte || { ativo: true };
    localStorage.setItem("gestor_info", JSON.stringify(info));
    return true;
  } catch (e) {
    localStorage.removeItem("gestor_token");
    localStorage.removeItem("gestor_info");
    alert(tg("cs_codigo_invalido"));
    return false;
  }
}

let contaSessaoConferida = false;

function contaBannerSuporte(ativo) {
  let faixa = document.getElementById("faixa-suporte");
  const info = infoGestor();
  if (!ativo || !info.suporte) {
    if (faixa) faixa.remove();
    document.body.style.paddingTop = "";
    if (ativo && !contaSessaoConferida && localStorage.getItem("gestor_token")) contaConferirSessao();
    return;
  }
  if (!contaSessaoConferida) contaConferirSessao();
  if (!faixa) {
    faixa = document.createElement("div");
    faixa.id = "faixa-suporte";
    faixa.setAttribute("role", "alert");
    faixa.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:9999;background:#B42318;color:#fff;" +
      "padding:8px 16px;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;justify-content:center;" +
      "font-size:.86rem;font-weight:600;box-shadow:0 2px 8px rgba(0,0,0,.25)";
    document.body.appendChild(faixa);
  }
  const s = info.suporte || {};
  const hora = s.expira_em ? contaData(s.expira_em, true) : "";
  faixa.innerHTML = `<span>${esc(tg("cs_banner", { empresa: s.empresa || (info.empresa && info.empresa.nome) || "" }))}
    ${hora ? `<span style="font-weight:400;opacity:.9">${esc(tg("cs_banner_expira", { hora }))}</span>` : ""}</span>
    <button type="button" id="faixa-suporte-encerrar" style="background:#fff;color:#B42318;border:0;border-radius:999px;padding:5px 12px;font:inherit;font-size:.8rem;cursor:pointer">${esc(tg("cs_encerrar"))}</button>`;
  document.body.style.paddingTop = faixa.offsetHeight + "px";
  faixa.querySelector("#faixa-suporte-encerrar").addEventListener("click", async () => {
    try { await api("/api/gestor/suporte/encerrar", { method: "POST" }); } catch (e) { /* sessão já encerrada */ }
    localStorage.removeItem("gestor_token");
    localStorage.removeItem("gestor_info");
    faixa.remove();
    document.body.style.paddingTop = "";
    painelAtivo = false;
    document.getElementById("btn-sair").classList.add("oculto");
    app.innerHTML = `<div class="card texto-centro" style="max-width:520px;margin:48px auto"><p>${esc(tg("cs_encerrada"))}</p></div>`;
  });
}

// confere no servidor se a sessão atual é de suporte (a faixa não depende só do navegador)
async function contaConferirSessao() {
  contaSessaoConferida = true;
  try {
    const r = await api("/api/gestor/conta/sessao");
    const info = infoGestor();
    if (!info.nome) return;
    const antes = !!info.suporte;
    if (r.suporte) info.suporte = { ativo: true, empresa: r.empresa, expira_em: r.expira_em };
    else delete info.suporte;
    localStorage.setItem("gestor_info", JSON.stringify(info));
    if (antes !== !!r.suporte || r.suporte) contaBannerSuporte(painelAtivo);
  } catch (e) { /* sem sessão: a tela de login cuida */ }
}

// ------------------------------------------------ Configurações
async function secaoConta(el) {
  if (!el) return;
  const info = infoGestor();
  const admin = !!info.admin;
  let r;
  try { r = await api("/api/gestor/conta"); } catch (e) { el.innerHTML = ""; return; }
  const linhasAnuncio = ["en", "pt", "es"].map((lang) => `
    <div style="margin-top:10px">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
        <strong style="font-size:.82rem">${tg("ct_lang_" + lang)}</strong>
        <button class="btn ghost small" data-copiar-anuncio="${lang}">${tg("ct_copiar")}</button>
      </div>
      <textarea readonly rows="3" id="ct-anuncio-${lang}" style="margin:4px 0 0;font-size:.82rem">${esc(r.anuncio[lang] || "")}</textarea>
    </div>`).join("");
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("chave")}<span>${tg("ct_cfg_titulo")}</span></h2>
      <p class="desc">${tg("ct_cfg_desc")}</p>
      <label style="display:flex;gap:10px;align-items:flex-start;font-weight:500">
        <input type="checkbox" id="ct-fila" style="width:auto;margin-top:4px" ${r.config.so_com_consentimento ? "checked" : ""} ${admin ? "" : "disabled"}>
        <span>${tg("ct_cfg_fila")}<br><span class="desc" style="font-size:.8rem;font-weight:400">${tg("ct_cfg_fila_desc")}</span></span>
      </label>
      ${admin ? "" : `<p class="desc" style="font-size:.8rem">${tg("ct_cfg_so_admin")}</p>`}
      <div class="form-erro" id="ct-msg"></div>
      <h3 style="margin-top:18px">${tg("ct_anuncio_titulo")}</h3>
      <p class="desc" style="font-size:.82rem">${tg("ct_anuncio_desc")}</p>
      ${linhasAnuncio}
    </div>
    ${admin ? `<div class="card" id="dc-card">
      <h2 class="icone-titulo">${icone("documento")}<span>${tg("dc_titulo")}</span></h2>
      <h3>${tg("dc_exportar_titulo")}</h3>
      <p class="desc">${tg("dc_exportar_desc")}</p>
      <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="dc-sensivel" style="width:auto"> ${tg("dc_sensivel")}</label>
      <label class="field" id="dc-senha-campo" style="display:none">${tg("dc_senha")}
        <input type="password" id="dc-senha" autocomplete="current-password"></label>
      <div class="linha-acoes">
        <button class="btn" id="dc-exportar" ${r.suporte ? "disabled" : ""}>${tg("dc_exportar")}</button>
        <button class="btn ghost small" id="dc-atualizar">${tg("dc_atualizar")}</button>
      </div>
      <div class="form-erro" id="dc-msg">${r.suporte ? esc(tg("cs_indisponivel")) : ""}</div>
      <div id="dc-lista"></div>
      <h3 style="margin-top:22px;color:var(--err)">${tg("dc_encerrar_titulo")}</h3>
      <p class="desc">${tg("dc_encerrar_desc")}</p>
      <label class="field">${esc(tg("dc_encerrar_digite", { empresa: r.empresa }))}
        <input type="text" id="dc-confirmacao" autocomplete="off" ${r.suporte ? "disabled" : ""}></label>
      <button class="btn danger" id="dc-encerrar" ${r.suporte ? "disabled" : ""}>${tg("dc_encerrar")}</button>
      <div class="form-erro" id="dc-encerrar-msg"></div>
    </div>` : ""}`;

  el.querySelectorAll("[data-copiar-anuncio]").forEach((b) => b.addEventListener("click", () => {
    navigator.clipboard.writeText(el.querySelector("#ct-anuncio-" + b.dataset.copiarAnuncio).value);
    b.textContent = tg("copiado");
  }));
  const fila = el.querySelector("#ct-fila");
  if (admin) fila.addEventListener("change", async () => {
    const msg = el.querySelector("#ct-msg");
    try {
      await api("/api/gestor/conta/config", { method: "POST", body: { so_com_consentimento: fila.checked } });
      msg.style.color = "var(--ok)";
      msg.textContent = tg("ct_cfg_salvo");
    } catch (e) {
      msg.style.color = "var(--err)";
      msg.textContent = e.message;
      fila.checked = !fila.checked;
    }
  });
  if (!admin) return;

  const lista = el.querySelector("#dc-lista");
  const desenharLista = (exps) => {
    if (!exps.length) { lista.innerHTML = `<p class="desc" style="font-size:.82rem">${tg("dc_nenhuma")}</p>`; return; }
    const rot = { preparando: ["warn", "dc_preparando"], pronto: ["ok", "dc_pronto"], erro: ["err", "dc_erro"], expirado: ["tipo", "dc_expirado"] };
    lista.innerHTML = `<div class="tabela-wrap mt"><table class="tabela"><tbody>${exps.map((x) => `
      <tr><td style="white-space:nowrap">${esc(contaData(x.criado_em, true))}</td>
        <td><span class="badge ${(rot[x.status] || ["tipo"])[0]}">${esc(tg((rot[x.status] || [0, "dc_erro"])[1]))}</span>
          ${x.sensivel ? `<span class="hint">${esc(tg("dc_com_sensivel"))}</span>` : ""}</td>
        <td class="hint">${x.status === "pronto" ? esc(tg("dc_vale_ate", { data: contaData(x.expira_em, true) })) : ""}</td>
        <td class="num">${x.status === "pronto" ? `<button class="btn secondary small" data-baixar-exp="${x.id}">${icone("anexo")} ${tg("dc_baixar")}</button>` : ""}</td></tr>`).join("")}
      </tbody></table></div>`;
    lista.querySelectorAll("[data-baixar-exp]").forEach((b) => b.addEventListener("click", () => contaBaixar(b.dataset.baixarExp, el)));
  };
  let tentativas = 0;
  const recarregar = async () => {
    try {
      const atual = await api("/api/gestor/conta");
      desenharLista(atual.exportacoes || []);
      if ((atual.exportacoes || []).some((x) => x.status === "preparando") && tentativas++ < 40 && document.body.contains(lista)) {
        setTimeout(recarregar, 3000);
      }
    } catch (e) { /* tenta de novo no botão Atualizar */ }
  };
  desenharLista(r.exportacoes || []);
  if ((r.exportacoes || []).some((x) => x.status === "preparando")) setTimeout(recarregar, 3000);
  el.querySelector("#dc-atualizar").addEventListener("click", () => { tentativas = 0; recarregar(); });
  const sensivel = el.querySelector("#dc-sensivel");
  sensivel.addEventListener("change", () => {
    el.querySelector("#dc-senha-campo").style.display = sensivel.checked ? "" : "none";
  });
  el.querySelector("#dc-exportar").addEventListener("click", async () => {
    const msg = el.querySelector("#dc-msg");
    msg.style.color = "var(--err)";
    msg.textContent = "";
    try {
      await api("/api/gestor/conta/exportar", { method: "POST", body: {
        sensivel: sensivel.checked, senha: sensivel.checked ? el.querySelector("#dc-senha").value : "" } });
      el.querySelector("#dc-senha").value = "";
      tentativas = 0;
      recarregar();
    } catch (e) { msg.textContent = e.message; }
  });
  el.querySelector("#dc-encerrar").addEventListener("click", async () => {
    const msg = el.querySelector("#dc-encerrar-msg");
    msg.style.color = "var(--err)";
    msg.textContent = "";
    const confirmacao = el.querySelector("#dc-confirmacao").value.trim();
    if (confirmacao.toLowerCase() !== String(r.empresa || "").trim().toLowerCase()) {
      msg.textContent = tg("dc_encerrar_digite", { empresa: r.empresa });
      return;
    }
    if (!confirm(tg("dc_encerrar_confirmar", { empresa: r.empresa }))) return;
    try {
      const res = await api("/api/gestor/conta/encerrar", { method: "POST", body: { confirmacao } });
      alert(tg("dc_encerrada", { data: contaData(res.exclusao_em) }));
      localStorage.removeItem("gestor_token");
      localStorage.removeItem("gestor_info");
      telaLogin();
    } catch (e) { msg.textContent = e.message; }
  });
}

// download com o cabeçalho da sessão (o link não funciona fora do painel nem para outra pessoa)
async function contaBaixar(id, el) {
  const msg = el.querySelector("#dc-msg");
  try {
    const resp = await fetch("/api/gestor/conta/exportacao/" + encodeURIComponent(id) + "/baixar", { headers: headersDownload() });
    if (!resp.ok) {
      const d = await resp.json().catch(() => ({}));
      throw new Error(d.erro || tg("erro_comunicacao"));
    }
    const blob = await resp.blob();
    const nome = ((resp.headers.get("Content-Disposition") || "").match(/filename="([^"]+)"/) || [])[1] || "bussola-dados.zip";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = nome;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  } catch (e) {
    if (msg) { msg.style.color = "var(--err)"; msg.textContent = e.message; }
  }
}
