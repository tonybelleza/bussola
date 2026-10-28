/* =====================================================================
   Integrações de RH no painel do gestor (integracoes_rh.py).
   - integracoesRhPreencherFicha: bloco "Verificação de antecedentes" na ficha
     do candidato (Checkr: pedir, status, link do relatório, aviso de ação
     adversa da FCRA) e o aviso informativo do E-Verify na área do I-9.
   - integracoesRhAvisoContratar: aviso ao mover para Contratado sem relatório
     clear quando a empresa exige a verificação.
   - secaoIntegracoesRh: cartões em Configurações (só o administrador):
     "Exportar para a folha" e "Verificação de antecedentes (Checkr)".
   Textos em pt, en e es (tg do i18n-gestor.js, chaves "irh_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  irh_titulo: "Verificação de antecedentes",
  irh_status: { convite_enviado: "Convite enviado", pendente: "Em andamento", clear: "Clear", consider: "Consider (revisar)",
    suspenso: "Suspensa", cancelado: "Cancelada", expirado: "Convite expirado" },
  irh_nenhuma: "Nenhuma verificação pedida para este candidato.",
  irh_pedir: "Pedir verificação de antecedentes", irh_confirmar_pedir: "Pedir a verificação de antecedentes pela Checkr (pacote {pacote})? O candidato recebe o e-mail da Checkr para autorizar e informar os dados.",
  irh_pedido_ok: "Pedido enviado. A Checkr mandou o convite ao candidato.",
  irh_motivo: { sem_config: "Configure a Checkr em Configurações (chave, pacote e estado de trabalho).", sem_email: "Candidato sem e-mail.",
    sem_proposta: "Envie a proposta antes de pedir a verificação.", em_andamento: "Já há uma verificação em andamento." },
  irh_so_admin: "Só o administrador da empresa pede a verificação.",
  irh_pacote: "Pacote: {pacote}", irh_pedido_em: "Pedido em {data} por {quem}", irh_atualizado: "Atualizado em {data}",
  irh_abrir: "Abrir na Checkr", irh_convite: "Link do convite do candidato", irh_staging: "teste (staging)",
  irh_checklist: "Checklist do onboarding: verificação de antecedentes", irh_check_ok: "concluída (clear)", irh_check_pend: "pendente",
  irh_exige: "A empresa exige uma verificação clear antes de contratar.",
  irh_fcra: "Se pensar em não contratar por causa do relatório, a lei FCRA exige o processo de ação adversa (aviso prévio, prazo e aviso final). Isso é responsabilidade do empregador.",
  irh_fcra_link: "Orientação da FTC sobre ação adversa",
  irh_everify_titulo: "Formulário I-9 e E-Verify",
  irh_everify: "O Bússola não faz a consulta ao E-Verify: ela exige o cadastro da empresa no programa. Se a sua empresa participa, faça a consulta em e-verify.gov depois de concluir o I-9.",
  irh_everify_link: "Abrir e-verify.gov",
  irh_aviso_contratar: "A empresa exige uma verificação de antecedentes clear antes de contratar, e este candidato ainda não tem (status: {status}). Mover para Contratado mesmo assim?",
  irh_sem_status: "nenhuma",
  // configurações: folha
  irh_f_titulo: "Exportar para a folha", irh_f_desc: "Gere o arquivo de importação de novos contratados (onboarding em andamento ou concluído) para o Gusto, o QuickBooks Payroll ou um CSV genérico. Prestadores 1099 saem num arquivo separado com os dados do W-9 para o 1099-NEC.",
  irh_f_provedor: "Sistema de folha", irh_f_prov: { gusto: "Gusto", quickbooks: "QuickBooks Payroll", generico: "CSV genérico" },
  irh_f_de: "Início a partir de", irh_f_ate: "Início até", irh_f_carregar: "Listar contratações", irh_f_vazio: "Nenhuma contratação com onboarding em andamento ou concluído nesse período.",
  irh_f_todos: "Selecionar todos", irh_f_tipo: { w2: "W-2", 1099: "1099" }, irh_f_onb: { em_andamento: "em andamento", concluido: "concluído" },
  irh_f_previa: "Prévia", irh_f_previa_w2: "Empregados (W-2): {n}", irh_f_previa_1099: "Prestadores (1099): {n}",
  irh_f_previa_obs: "A prévia mostra só as colunas não sensíveis. Colunas sensíveis no arquivo (com senha): {cols}.",
  irh_f_faltando: "{nome}: falta {itens}", irh_f_falta: { w9: "W-9", ssn: "SSN", endereco: "endereço" },
  irh_f_exportar: "Exportar…", irh_f_estado: "Estado de trabalho (sigla)", irh_f_estado_dica: "Em branco usa o estado do empregador: {uf}",
  irh_f_mapa: "Nomes das colunas ({prov})", irh_f_mapa_dica: "Ajuste se o modelo de importação do seu sistema usar outro nome. Deixe em branco para não exportar a coluna.",
  irh_f_salvar: "Salvar exportação", irh_f_salvo: "Configuração da exportação salva.", irh_f_restaurar: "Restaurar nomes padrão",
  irh_d_titulo: "Exportar arquivo", irh_d_sens: "Incluir dados sensíveis (SSN, data de nascimento, TIN, routing e conta)",
  irh_d_senha: "Digite a sua senha para confirmar", irh_d_aviso: "O arquivo é gerado agora e baixado uma única vez; o Bússola não guarda cópia. A exportação fica registrada no histórico de acessos (sem os valores). Guarde o arquivo com cuidado e apague depois de importar.",
  irh_d_w2: "Baixar empregados (W-2)", irh_d_1099: "Baixar prestadores (1099 / W-9)", irh_d_fechar: "Fechar", irh_d_baixado: "Arquivo baixado.",
  irh_d_sem_senha: "Digite a sua senha para incluir os dados sensíveis.",
  // configurações: Checkr
  irh_c_titulo: "Verificação de antecedentes (Checkr)", irh_c_desc: "Peça a verificação na ficha do candidato depois da proposta. A Checkr manda o e-mail ao candidato e cuida da autorização e da divulgação exigidas pela FCRA. Você precisa de uma conta na Checkr.",
  irh_c_chave: "Chave da API (secreta)", irh_c_chave_salva: "Chave salva: {mask}. Digite uma nova para trocar.", irh_c_remover: "Remover chave",
  irh_c_ambiente: "Ambiente", irh_c_amb: { producao: "Produção", staging: "Teste (staging)" },
  irh_c_pacote: "Pacote padrão (slug)", irh_c_estado: "Estado de trabalho (sigla)", irh_c_cidade: "Cidade de trabalho (opcional)",
  irh_c_exigir: "Exigir verificação clear antes de contratar (mostra um aviso ao mover para Contratado)",
  irh_c_webhook: "URL do webhook (cole no painel da Checkr, em Account Settings > Developer Settings)",
  irh_c_salvar: "Salvar Checkr", irh_c_salvo: "Configuração da Checkr salva.", irh_c_testar: "Testar conexão",
  irh_c_teste_ok: "Conexão OK. Pacotes da conta: {pacotes}", irh_c_copiar: "Copiar", irh_c_copiado: "Copiado!",
});
Object.assign(I18N_GESTOR.en, {
  irh_titulo: "Background check",
  irh_status: { convite_enviado: "Invitation sent", pendente: "In progress", clear: "Clear", consider: "Consider (review)",
    suspenso: "Suspended", cancelado: "Canceled", expirado: "Invitation expired" },
  irh_nenhuma: "No background check ordered for this candidate yet.",
  irh_pedir: "Order background check", irh_confirmar_pedir: "Order a Checkr background check (package {pacote})? The candidate will get an email from Checkr to authorize it and enter their information.",
  irh_pedido_ok: "Order placed. Checkr sent the invitation to the candidate.",
  irh_motivo: { sem_config: "Set up Checkr in Settings (API key, package, and work state).", sem_email: "This candidate has no email.",
    sem_proposta: "Send the offer before ordering a background check.", em_andamento: "A background check is already in progress." },
  irh_so_admin: "Only the company admin can order a background check.",
  irh_pacote: "Package: {pacote}", irh_pedido_em: "Ordered on {data} by {quem}", irh_atualizado: "Updated on {data}",
  irh_abrir: "Open in Checkr", irh_convite: "Candidate invitation link", irh_staging: "test (staging)",
  irh_checklist: "Onboarding checklist: background check", irh_check_ok: "complete (clear)", irh_check_pend: "pending",
  irh_exige: "Your company requires a clear background check before hiring.",
  irh_fcra: "If you are considering not hiring because of the report, the FCRA requires the adverse action process (a pre-adverse action notice, a waiting period, and a final notice). This is the employer's responsibility.",
  irh_fcra_link: "FTC guidance on adverse action",
  irh_everify_titulo: "Form I-9 and E-Verify",
  irh_everify: "Bússola does not run E-Verify cases: E-Verify requires your company to enroll in the program. If your company participates, create the case at e-verify.gov after Form I-9 is complete.",
  irh_everify_link: "Open e-verify.gov",
  irh_aviso_contratar: "Your company requires a clear background check before hiring, and this candidate does not have one yet (status: {status}). Move to Hired anyway?",
  irh_sem_status: "none",
  irh_f_titulo: "Payroll export", irh_f_desc: "Create the import file for new hires (onboarding in progress or complete) for Gusto, QuickBooks Payroll, or a generic CSV. 1099 contractors go in a separate file with their W-9 data for 1099-NEC filing.",
  irh_f_provedor: "Payroll provider", irh_f_prov: { gusto: "Gusto", quickbooks: "QuickBooks Payroll", generico: "Generic CSV" },
  irh_f_de: "Start date from", irh_f_ate: "Start date to", irh_f_carregar: "List hires", irh_f_vazio: "No hires with onboarding in progress or complete in this period.",
  irh_f_todos: "Select all", irh_f_tipo: { w2: "W-2", 1099: "1099" }, irh_f_onb: { em_andamento: "in progress", concluido: "complete" },
  irh_f_previa: "Preview", irh_f_previa_w2: "Employees (W-2): {n}", irh_f_previa_1099: "Contractors (1099): {n}",
  irh_f_previa_obs: "The preview shows only non-sensitive columns. Sensitive columns in the file (password required): {cols}.",
  irh_f_faltando: "{nome}: missing {itens}", irh_f_falta: { w9: "W-9", ssn: "SSN", endereco: "address" },
  irh_f_exportar: "Export…", irh_f_estado: "Work state (2-letter code)", irh_f_estado_dica: "Leave blank to use the employer's state: {uf}",
  irh_f_mapa: "Column names ({prov})", irh_f_mapa_dica: "Change a name if your provider's import template uses a different one. Leave it blank to skip the column.",
  irh_f_salvar: "Save export settings", irh_f_salvo: "Export settings saved.", irh_f_restaurar: "Restore default names",
  irh_d_titulo: "Export file", irh_d_sens: "Include sensitive data (SSN, date of birth, TIN, routing and account numbers)",
  irh_d_senha: "Enter your password to confirm", irh_d_aviso: "The file is created now and downloaded once; Bússola does not keep a copy. The export is recorded in the access log (without the values). Store the file carefully and delete it after the import.",
  irh_d_w2: "Download employees (W-2)", irh_d_1099: "Download contractors (1099 / W-9)", irh_d_fechar: "Close", irh_d_baixado: "File downloaded.",
  irh_d_sem_senha: "Enter your password to include sensitive data.",
  irh_c_titulo: "Background checks (Checkr)", irh_c_desc: "Order a check from the candidate profile after the offer. Checkr emails the candidate and handles the authorization and disclosure the FCRA requires. You need a Checkr account.",
  irh_c_chave: "API key (secret)", irh_c_chave_salva: "Saved key: {mask}. Enter a new one to replace it.", irh_c_remover: "Remove key",
  irh_c_ambiente: "Environment", irh_c_amb: { producao: "Production", staging: "Test (staging)" },
  irh_c_pacote: "Default package (slug)", irh_c_estado: "Work state (2-letter code)", irh_c_cidade: "Work city (optional)",
  irh_c_exigir: "Require a clear background check before hiring (shows a warning when moving to Hired)",
  irh_c_webhook: "Webhook URL (paste it in the Checkr dashboard under Account Settings > Developer Settings)",
  irh_c_salvar: "Save Checkr", irh_c_salvo: "Checkr settings saved.", irh_c_testar: "Test connection",
  irh_c_teste_ok: "Connection OK. Account packages: {pacotes}", irh_c_copiar: "Copy", irh_c_copiado: "Copied!",
});
Object.assign(I18N_GESTOR.es, {
  irh_titulo: "Verificación de antecedentes",
  irh_status: { convite_enviado: "Invitación enviada", pendente: "En curso", clear: "Clear", consider: "Consider (revisar)",
    suspenso: "Suspendida", cancelado: "Cancelada", expirado: "Invitación vencida" },
  irh_nenhuma: "Todavía no se solicitó ninguna verificación para este candidato.",
  irh_pedir: "Solicitar verificación de antecedentes", irh_confirmar_pedir: "¿Solicitar la verificación de antecedentes con Checkr (paquete {pacote})? El candidato recibirá el correo de Checkr para autorizarla e ingresar sus datos.",
  irh_pedido_ok: "Solicitud enviada. Checkr mandó la invitación al candidato.",
  irh_motivo: { sem_config: "Configura Checkr en Configuración (clave, paquete y estado de trabajo).", sem_email: "Este candidato no tiene correo.",
    sem_proposta: "Envía la oferta antes de solicitar la verificación.", em_andamento: "Ya hay una verificación en curso." },
  irh_so_admin: "Solo el administrador de la empresa solicita la verificación.",
  irh_pacote: "Paquete: {pacote}", irh_pedido_em: "Solicitada el {data} por {quem}", irh_atualizado: "Actualizada el {data}",
  irh_abrir: "Abrir en Checkr", irh_convite: "Enlace de invitación del candidato", irh_staging: "prueba (staging)",
  irh_checklist: "Lista de incorporación: verificación de antecedentes", irh_check_ok: "completada (clear)", irh_check_pend: "pendiente",
  irh_exige: "Tu empresa exige una verificación clear antes de contratar.",
  irh_fcra: "Si consideras no contratar por el informe, la ley FCRA exige el proceso de acción adversa (aviso previo, un plazo de espera y un aviso final). Esto es responsabilidad del empleador.",
  irh_fcra_link: "Guía de la FTC sobre acción adversa",
  irh_everify_titulo: "Formulario I-9 y E-Verify",
  irh_everify: "Bússola no hace la consulta en E-Verify: E-Verify exige que la empresa se inscriba en el programa. Si tu empresa participa, crea el caso en e-verify.gov después de completar el I-9.",
  irh_everify_link: "Abrir e-verify.gov",
  irh_aviso_contratar: "Tu empresa exige una verificación de antecedentes clear antes de contratar, y este candidato todavía no la tiene (estado: {status}). ¿Mover a Contratado de todos modos?",
  irh_sem_status: "ninguna",
  irh_f_titulo: "Exportar a la nómina", irh_f_desc: "Genera el archivo de importación de las nuevas contrataciones (incorporación en curso o completada) para Gusto, QuickBooks Payroll o un CSV genérico. Los contratistas 1099 salen en un archivo aparte con los datos del W-9 para el 1099-NEC.",
  irh_f_provedor: "Sistema de nómina", irh_f_prov: { gusto: "Gusto", quickbooks: "QuickBooks Payroll", generico: "CSV genérico" },
  irh_f_de: "Inicio desde", irh_f_ate: "Inicio hasta", irh_f_carregar: "Listar contrataciones", irh_f_vazio: "No hay contrataciones con incorporación en curso o completada en este período.",
  irh_f_todos: "Seleccionar todos", irh_f_tipo: { w2: "W-2", 1099: "1099" }, irh_f_onb: { em_andamento: "en curso", concluido: "completada" },
  irh_f_previa: "Vista previa", irh_f_previa_w2: "Empleados (W-2): {n}", irh_f_previa_1099: "Contratistas (1099): {n}",
  irh_f_previa_obs: "La vista previa muestra solo las columnas no sensibles. Columnas sensibles en el archivo (con contraseña): {cols}.",
  irh_f_faltando: "{nome}: falta {itens}", irh_f_falta: { w9: "W-9", ssn: "SSN", endereco: "dirección" },
  irh_f_exportar: "Exportar…", irh_f_estado: "Estado de trabajo (código de 2 letras)", irh_f_estado_dica: "En blanco usa el estado del empleador: {uf}",
  irh_f_mapa: "Nombres de las columnas ({prov})", irh_f_mapa_dica: "Cámbialo si la plantilla de importación de tu sistema usa otro nombre. Déjalo en blanco para no exportar la columna.",
  irh_f_salvar: "Guardar exportación", irh_f_salvo: "Configuración de la exportación guardada.", irh_f_restaurar: "Restaurar nombres predeterminados",
  irh_d_titulo: "Exportar archivo", irh_d_sens: "Incluir datos sensibles (SSN, fecha de nacimiento, TIN, routing y cuenta)",
  irh_d_senha: "Escribe tu contraseña para confirmar", irh_d_aviso: "El archivo se genera ahora y se descarga una sola vez; Bússola no guarda una copia. La exportación queda en el historial de accesos (sin los valores). Guarda el archivo con cuidado y bórralo después de importarlo.",
  irh_d_w2: "Descargar empleados (W-2)", irh_d_1099: "Descargar contratistas (1099 / W-9)", irh_d_fechar: "Cerrar", irh_d_baixado: "Archivo descargado.",
  irh_d_sem_senha: "Escribe tu contraseña para incluir los datos sensibles.",
  irh_c_titulo: "Verificación de antecedentes (Checkr)", irh_c_desc: "Solicita la verificación desde la ficha del candidato después de la oferta. Checkr le escribe al candidato y se encarga de la autorización y la divulgación que exige la FCRA. Necesitas una cuenta de Checkr.",
  irh_c_chave: "Clave de API (secreta)", irh_c_chave_salva: "Clave guardada: {mask}. Escribe una nueva para cambiarla.", irh_c_remover: "Eliminar clave",
  irh_c_ambiente: "Entorno", irh_c_amb: { producao: "Producción", staging: "Prueba (staging)" },
  irh_c_pacote: "Paquete predeterminado (slug)", irh_c_estado: "Estado de trabajo (código de 2 letras)", irh_c_cidade: "Ciudad de trabajo (opcional)",
  irh_c_exigir: "Exigir verificación clear antes de contratar (muestra un aviso al mover a Contratado)",
  irh_c_webhook: "URL del webhook (pégala en el panel de Checkr, en Account Settings > Developer Settings)",
  irh_c_salvar: "Guardar Checkr", irh_c_salvo: "Configuración de Checkr guardada.", irh_c_testar: "Probar conexión",
  irh_c_teste_ok: "Conexión correcta. Paquetes de la cuenta: {pacotes}", irh_c_copiar: "Copiar", irh_c_copiado: "¡Copiado!",
});

function irhTab(chave) {
  return (I18N_GESTOR[idiomaGestor] || I18N_GESTOR.pt)[chave] || I18N_GESTOR.pt[chave] || {};
}
const IRH_COR = { convite_enviado: "neutral", pendente: "warn", clear: "ok", consider: "err", suspenso: "warn", cancelado: "neutral", expirado: "neutral" };

// ------------------------------------------------------------ ficha do candidato
async function integracoesRhPreencherFicha(candidatoId, el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/integracoes-rh/checkr/candidato/" + candidatoId); } catch (e) { el.remove(); return; }
  const st = irhTab("irh_status");
  const atual = r.verificacoes[0];
  const lista = r.verificacoes.map((v) => `
    <div class="perfil-destaque" style="margin-top:8px">
      <div class="titulo"><span class="badge ${IRH_COR[v.status] || "neutral"}">${esc(st[v.status] || v.status)}</span>
        ${v.staging ? `<span class="hint"> · ${tg("irh_staging")}</span>` : ""}</div>
      <div class="desc">${tg("irh_pacote", { pacote: esc(v.pacote) })} · ${tg("irh_pedido_em", { data: esc(fmtData(v.criado_em)), quem: esc(v.criado_por || "") })}
        · ${tg("irh_atualizado", { data: esc(fmtData(v.atualizado_em)) })}</div>
      <div class="linha-acoes no-print">
        ${v.link ? `<a class="btn secondary small" href="${esc(v.link)}" target="_blank" rel="noopener noreferrer">${icone("link")} ${tg("irh_abrir")}</a>` : ""}
        ${v.convite_url && (v.status === "convite_enviado") ? `<button class="btn secondary small" data-irh-copiar="${esc(v.convite_url)}">${tg("irh_convite")}</button>` : ""}
      </div>
    </div>`).join("");
  const ok = atual && atual.status === "clear";
  el.innerHTML = `
    ${tituloIcone("cadeado", tg("irh_titulo"))}
    <p class="desc">${tg("irh_checklist")}: <span class="badge ${ok ? "ok" : "warn"}">${ok ? tg("irh_check_ok") : tg("irh_check_pend")}</span></p>
    ${r.exigir ? `<p class="hint">${tg("irh_exige")}</p>` : ""}
    ${!r.verificacoes.length ? `<p class="desc">${tg("irh_nenhuma")}</p>` : lista}
    ${r.admin ? (r.pode_pedir
      ? `<div class="linha-acoes no-print"><button class="btn small" id="irh-pedir">${icone("mais")} ${tg("irh_pedir")}</button></div>`
      : (r.motivo && r.motivo !== "em_andamento" ? `<p class="hint">${esc(irhTab("irh_motivo")[r.motivo] || "")}</p>` : ""))
      : (!r.verificacoes.length ? `<p class="hint">${tg("irh_so_admin")}</p>` : "")}
    ${atual && atual.status === "consider" ? `<p class="hint" style="color:var(--warn)">${tg("irh_fcra")}
      <a href="${esc(r.fcra_url)}" target="_blank" rel="noopener noreferrer">${tg("irh_fcra_link")}</a></p>` : ""}
    ${r.tem_w2 ? `<div class="perfil-destaque" style="margin-top:12px">
      <div class="titulo">${tg("irh_everify_titulo")}</div>
      <div class="desc">${tg("irh_everify")}</div>
      <a href="${esc(r.everify_url)}" target="_blank" rel="noopener noreferrer">${tg("irh_everify_link")}</a></div>` : ""}
    <div class="form-erro" id="irh-msg"></div>`;
  const msg = (t, bom) => { const m = el.querySelector("#irh-msg"); m.style.color = bom ? "var(--ok)" : "var(--err)"; m.textContent = t; };
  const pedir = el.querySelector("#irh-pedir");
  if (pedir) pedir.addEventListener("click", async () => {
    if (!confirm(tg("irh_confirmar_pedir", { pacote: r.pacote }))) return;
    pedir.disabled = true;
    try {
      await api("/api/gestor/integracoes-rh/checkr/candidato/" + candidatoId + "/pedir", { method: "POST", body: {} });
      await integracoesRhPreencherFicha(candidatoId, el);
      const m = el.querySelector("#irh-msg");
      if (m) { m.style.color = "var(--ok)"; m.textContent = tg("irh_pedido_ok"); }
    } catch (e) { msg(e.message); pedir.disabled = false; }
  });
  el.querySelectorAll("[data-irh-copiar]").forEach((b) => b.addEventListener("click", () => {
    navigator.clipboard.writeText(b.dataset.irhCopiar).then(() => { b.textContent = tg("irh_c_copiado"); }).catch(() => {});
  }));
}

// aviso ao mover para Contratado: devolve true para seguir
async function integracoesRhAvisoContratar(candidaturaId) {
  try {
    const r = await api("/api/gestor/integracoes-rh/checkr/aviso?candidatura=" + encodeURIComponent(candidaturaId));
    if (!r.avisar) return true;
    const st = irhTab("irh_status");
    return confirm(tg("irh_aviso_contratar", { status: r.status ? (st[r.status] || r.status) : tg("irh_sem_status") }) + "\n\n" + tg("irh_fcra") + "\n" + r.fcra_url);
  } catch (e) {
    return true;
  }
}

// ------------------------------------------------------------ Configurações
async function secaoIntegracoesRh(el) {
  if (!el || !infoGestor().admin) return;
  let cfg;
  try { cfg = await api("/api/gestor/integracoes-rh/config"); } catch (e) { el.innerHTML = ""; return; }
  el.innerHTML = '<div id="irh-folha"></div><div id="irh-checkr"></div>';
  irhCartaoFolha(el.querySelector("#irh-folha"), cfg);
  irhCartaoCheckr(el.querySelector("#irh-checkr"), cfg);
}

function irhCartaoFolha(el, cfg) {
  const f = cfg.folha;
  const prov = irhTab("irh_f_prov");
  let provedor = f.provedor;
  let mapas = JSON.parse(JSON.stringify(f.mapas));
  let contratacoes = [];
  const hoje = new Date();
  const iso = (d) => d.toISOString().slice(0, 10);
  const de0 = iso(new Date(hoje.getFullYear(), hoje.getMonth() - 1, 1));
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("relatorio")}<span>${tg("irh_f_titulo")}</span></h2>
      <p class="desc">${tg("irh_f_desc")}</p>
      <div class="grid cols-2">
        <label class="field">${tg("irh_f_provedor")}
          <select id="irhf-prov">${Object.keys(prov).map((p) => `<option value="${p}" ${p === provedor ? "selected" : ""}>${esc(prov[p])}</option>`).join("")}</select></label>
        <label class="field">${tg("irh_f_estado")}
          <input type="text" id="irhf-uf" maxlength="2" value="${esc(f.estado_trabalho || "")}" placeholder="${esc(f.estado_sugerido || "")}">
          <span class="hint">${tg("irh_f_estado_dica", { uf: esc(f.estado_sugerido || "-") })}</span></label>
        <label class="field">${tg("irh_f_de")} <input type="date" id="irhf-de" value="${de0}"></label>
        <label class="field">${tg("irh_f_ate")} <input type="date" id="irhf-ate" value=""></label>
      </div>
      <div class="linha-acoes"><button class="btn secondary small" id="irhf-carregar">${tg("irh_f_carregar")}</button></div>
      <div id="irhf-lista"></div>
      <div id="irhf-previa"></div>
      <details style="margin-top:12px"><summary id="irhf-mapa-tit"></summary>
        <p class="hint">${tg("irh_f_mapa_dica")}</p>
        <div class="grid cols-2" id="irhf-mapa"></div>
        <button class="btn secondary small" id="irhf-restaurar">${tg("irh_f_restaurar")}</button>
      </details>
      <div class="form-erro" id="irhf-msg"></div>
      <button class="btn mt" id="irhf-salvar">${tg("irh_f_salvar")}</button>
    </div>`;
  const $ = (s) => el.querySelector(s);
  const msg = (t, bom) => { const m = $("#irhf-msg"); m.style.color = bom ? "var(--ok)" : "var(--err)"; m.textContent = t; };
  const campos = f.campos;
  function desenharMapa() {
    $("#irhf-mapa-tit").textContent = tg("irh_f_mapa", { prov: prov[provedor] });
    const m = mapas[provedor];
    $("#irhf-mapa").innerHTML = campos.map((c) => `<label class="field">${esc(f.padroes[provedor][c.chave])}${c.sensivel ? " " + icone("cadeado", 12) : ""}
      <input type="text" maxlength="60" data-irh-col="${c.chave}" value="${esc(m[c.chave] || "")}"></label>`).join("");
    $("#irhf-mapa").querySelectorAll("[data-irh-col]").forEach((i) => i.addEventListener("input", () => { mapas[provedor][i.dataset.irhCol] = i.value; }));
  }
  desenharMapa();
  $("#irhf-prov").addEventListener("change", () => { provedor = $("#irhf-prov").value; desenharMapa(); $("#irhf-previa").innerHTML = ""; });
  $("#irhf-restaurar").addEventListener("click", () => { mapas[provedor] = Object.assign({}, f.padroes[provedor]); desenharMapa(); });
  $("#irhf-salvar").addEventListener("click", async () => {
    try {
      const r = await api("/api/gestor/integracoes-rh/config", { method: "POST", body: { folha: { provedor, estado_trabalho: $("#irhf-uf").value.trim(), mapas } } });
      mapas = JSON.parse(JSON.stringify(r.folha.mapas));
      msg(tg("irh_f_salvo"), true);
    } catch (e) { msg(e.message); }
  });
  const selecionados = () => [...el.querySelectorAll("[data-irh-ob]:checked")].map((c) => Number(c.dataset.irhOb));
  const filtro = () => ({ provedor, ids: selecionados(), de: $("#irhf-de").value, ate: $("#irhf-ate").value });
  $("#irhf-carregar").addEventListener("click", async () => {
    try {
      const q = "?de=" + encodeURIComponent($("#irhf-de").value) + "&ate=" + encodeURIComponent($("#irhf-ate").value);
      const r = await api("/api/gestor/integracoes-rh/folha/contratacoes" + q);
      contratacoes = r.contratacoes;
      const tipos = irhTab("irh_f_tipo"), onb = irhTab("irh_f_onb");
      $("#irhf-previa").innerHTML = "";
      $("#irhf-lista").innerHTML = !contratacoes.length ? `<p class="desc">${tg("irh_f_vazio")}</p>` : `
        <label style="display:block;margin:8px 0"><input type="checkbox" id="irhf-todos" checked> ${tg("irh_f_todos")}</label>
        <div style="display:grid;gap:4px">${contratacoes.map((c) => `<label><input type="checkbox" data-irh-ob="${c.id}" checked>
          ${esc(c.nome)} · ${esc(tipos[c.tipo] || c.tipo)} · ${esc(c.cargo)} · ${esc(fmtData(c.data_inicio))} · ${esc(onb[c.status] || c.status)}</label>`).join("")}</div>
        <div class="linha-acoes"><button class="btn secondary small" id="irhf-ver">${tg("irh_f_previa")}</button>
          <button class="btn small" id="irhf-exportar">${icone("cadeado")} ${tg("irh_f_exportar")}</button></div>`;
      if (!contratacoes.length) return;
      $("#irhf-todos").addEventListener("change", () => el.querySelectorAll("[data-irh-ob]").forEach((c) => { c.checked = $("#irhf-todos").checked; }));
      $("#irhf-ver").addEventListener("click", previa);
      $("#irhf-exportar").addEventListener("click", () => irhDialogoExportar(filtro()));
    } catch (e) { msg(e.message); }
  });
  async function previa() {
    try {
      const r = await api("/api/gestor/integracoes-rh/folha/previa", { method: "POST", body: filtro() });
      const falta = irhTab("irh_f_falta");
      const tabela = (t, rot) => !t.total ? "" : `
        <h3 style="margin-top:14px">${rot}</h3>
        <div style="overflow-x:auto"><table class="tabela"><thead><tr>${t.colunas.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead>
        <tbody>${t.linhas.map((l) => `<tr>${l.map((v) => `<td>${esc(v)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
        ${t.sensiveis.length ? `<p class="hint">${tg("irh_f_previa_obs", { cols: esc(t.sensiveis.join(", ")) })}</p>` : ""}
        ${t.avisos.map((a) => `<p class="hint" style="color:var(--warn)">${tg("irh_f_faltando", { nome: esc(a.nome), itens: esc(a.faltando.map((x) => falta[x] || x).join(", ")) })}</p>`).join("")}`;
      $("#irhf-previa").innerHTML = tabela(r.w2, tg("irh_f_previa_w2", { n: r.w2.total })) + tabela(r["1099"], tg("irh_f_previa_1099", { n: r["1099"].total }))
        || `<p class="desc">${tg("irh_f_vazio")}</p>`;
    } catch (e) { msg(e.message); }
  }
}

function irhDialogoExportar(filtro) {
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal" style="max-width:560px">
      <button class="btn ghost small fechar" id="irhd-x" aria-label="${esc(tg("irh_d_fechar"))}">${icone("fechar")}</button>
      <h2 class="icone-titulo">${icone("cadeado")}<span>${tg("irh_d_titulo")}</span></h2>
      <label style="display:block;margin:10px 0"><input type="checkbox" id="irhd-sens"> ${tg("irh_d_sens")}</label>
      <label class="field" id="irhd-senha-campo" style="display:none">${tg("irh_d_senha")}
        <input type="password" id="irhd-senha" autocomplete="current-password"></label>
      <p class="hint">${tg("irh_d_aviso")}</p>
      <div class="form-erro" id="irhd-msg"></div>
      <div class="linha-acoes">
        <button class="btn small" data-irhd-tipo="w2">${tg("irh_d_w2")}</button>
        <button class="btn small" data-irhd-tipo="1099">${tg("irh_d_1099")}</button>
        <button class="btn secondary small" id="irhd-fechar">${tg("irh_d_fechar")}</button>
      </div>
    </div>`;
  document.body.appendChild(fundo);
  const $ = (s) => fundo.querySelector(s);
  const fechar = () => { $("#irhd-senha").value = ""; fundo.remove(); };
  $("#irhd-x").addEventListener("click", fechar);
  $("#irhd-fechar").addEventListener("click", fechar);
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fechar(); });
  $("#irhd-sens").addEventListener("change", () => { $("#irhd-senha-campo").style.display = $("#irhd-sens").checked ? "" : "none"; });
  const msg = (t, bom) => { const m = $("#irhd-msg"); m.style.color = bom ? "var(--ok)" : "var(--err)"; m.textContent = t; };
  fundo.querySelectorAll("[data-irhd-tipo]").forEach((b) => b.addEventListener("click", async () => {
    const sens = $("#irhd-sens").checked;
    const senha = $("#irhd-senha").value;
    if (sens && !senha) return msg(tg("irh_d_sem_senha"));
    b.disabled = true;
    try {
      const resp = await fetch("/api/gestor/integracoes-rh/folha/exportar", {
        method: "POST",
        headers: Object.assign({ "Content-Type": "application/json" }, headersDownload()),
        body: JSON.stringify(Object.assign({}, filtro, { tipo: b.dataset.irhdTipo, incluir_sensiveis: sens, senha: sens ? senha : "" })),
      });
      if (!resp.ok) { const d = await resp.json().catch(() => ({})); throw new Error(d.erro || tg("erro_comunicacao")); }
      const disp = resp.headers.get("Content-Disposition") || "";
      const m = disp.match(/filename="([^"]+)"/);
      const blob = await resp.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = m ? m[1] : "payroll.csv";
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
      msg(tg("irh_d_baixado"), true);
    } catch (e) { msg(e.message); }
    b.disabled = false;
  }));
}

function irhCartaoCheckr(el, cfg) {
  const c = cfg.checkr;
  const amb = irhTab("irh_c_amb");
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("cadeado")}<span>${tg("irh_c_titulo")}</span></h2>
      <p class="desc">${tg("irh_c_desc")}</p>
      <div class="grid cols-2">
        <label class="field">${tg("irh_c_chave")}
          <input type="password" id="irhc-chave" autocomplete="off" placeholder="${esc(c.chave_mascara || "")}">
          ${c.configurado ? `<span class="hint">${tg("irh_c_chave_salva", { mask: esc(c.chave_mascara) })}</span>` : ""}</label>
        <label class="field">${tg("irh_c_ambiente")}
          <select id="irhc-amb">${Object.keys(amb).map((a) => `<option value="${a}" ${a === c.ambiente ? "selected" : ""}>${esc(amb[a])}</option>`).join("")}</select></label>
        <label class="field">${tg("irh_c_pacote")} <input type="text" id="irhc-pacote" maxlength="80" value="${esc(c.pacote)}" placeholder="tasker_standard"></label>
        <label class="field">${tg("irh_c_estado")} <input type="text" id="irhc-uf" maxlength="2" value="${esc(c.estado)}" placeholder="CT"></label>
        <label class="field">${tg("irh_c_cidade")} <input type="text" id="irhc-cidade" maxlength="80" value="${esc(c.cidade)}"></label>
      </div>
      <label style="display:block;margin:8px 0"><input type="checkbox" id="irhc-exigir" ${c.exigir ? "checked" : ""}> ${tg("irh_c_exigir")}</label>
      <label class="field">${tg("irh_c_webhook")}
        <input type="text" readonly id="irhc-webhook" value="${esc(c.webhook_url)}"></label>
      <button class="btn secondary small" id="irhc-copiar">${tg("irh_c_copiar")}</button>
      <div class="form-erro" id="irhc-msg"></div>
      <div class="linha-acoes">
        <button class="btn" id="irhc-salvar">${tg("irh_c_salvar")}</button>
        <button class="btn secondary" id="irhc-testar" ${c.configurado ? "" : "disabled"}>${tg("irh_c_testar")}</button>
        ${c.configurado ? `<button class="btn secondary" id="irhc-remover">${tg("irh_c_remover")}</button>` : ""}
      </div>
    </div>`;
  const $ = (s) => el.querySelector(s);
  const msg = (t, bom) => { const m = $("#irhc-msg"); m.style.color = bom ? "var(--ok)" : "var(--err)"; m.textContent = t; };
  const salvar = async (extra) => {
    const r = await api("/api/gestor/integracoes-rh/config", { method: "POST", body: { checkr: Object.assign({
      chave: $("#irhc-chave").value.trim(), ambiente: $("#irhc-amb").value, pacote: $("#irhc-pacote").value.trim(),
      estado: $("#irhc-uf").value.trim(), cidade: $("#irhc-cidade").value.trim(), exigir: $("#irhc-exigir").checked }, extra || {}) } });
    irhCartaoCheckr(el, r);
    const m = el.querySelector("#irhc-msg");
    if (m) { m.style.color = "var(--ok)"; m.textContent = tg("irh_c_salvo"); }
  };
  $("#irhc-salvar").addEventListener("click", () => salvar().catch((e) => msg(e.message)));
  const rem = $("#irhc-remover");
  if (rem) rem.addEventListener("click", () => salvar({ chave: "", remover_chave: true }).catch((e) => msg(e.message)));
  $("#irhc-copiar").addEventListener("click", () => {
    navigator.clipboard.writeText($("#irhc-webhook").value).then(() => { $("#irhc-copiar").textContent = tg("irh_c_copiado"); }).catch(() => {});
  });
  $("#irhc-testar").addEventListener("click", async () => {
    try {
      const r = await api("/api/gestor/integracoes-rh/checkr/testar", { method: "POST", body: {} });
      msg(tg("irh_c_teste_ok", { pacotes: r.pacotes.map((p) => p.slug).join(", ") || "-" }), true);
    } catch (e) { msg(e.message); }
  });
}
