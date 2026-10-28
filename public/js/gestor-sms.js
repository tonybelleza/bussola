/* =====================================================================
   Mensagens de texto (SMS) no painel do gestor (sms.py).
   - smsPreencherFicha: bloco na ficha do candidato com a conversa, o
     motivo quando não dá para enviar, a resposta do gestor e o envio de
     um modelo.
   - secaoSms: cartão em Configurações (ligar, consentimento, contato da
     resposta HELP e modelos em en, pt e es). Só o administrador altera.
   - smsUsoPlano: uso do mês (segmentos) na área do plano.
   O envio fica desligado até o dono ligar o SMS (campanha A2P aprovada).
   Textos em pt, en e es (tg do i18n-gestor.js, chaves "sms_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  sms_titulo: "Mensagens de texto (SMS)",
  sms_off_global: "O envio de SMS ainda não está disponível: aguardando a aprovação da campanha pelas operadoras dos EUA.",
  sms_off_empresa: "O SMS está desligado para a sua empresa. O administrador liga em Configurações.",
  sms_motivo: {
    desligado: "O envio de SMS ainda não está disponível.", empresa_desligada: "O SMS está desligado para a sua empresa.",
    sem_twilio: "A plataforma ainda não configurou o serviço de SMS.", sem_remetente: "Nenhum número de envio configurado.",
    telefone_invalido: "O candidato não tem um celular válido dos EUA.", optout: "O candidato pediu para não receber SMS (STOP).",
    sem_consentimento: "O candidato não deu consentimento para receber mensagens de texto.",
    limite_plano: "O limite de SMS do plano neste mês acabou.", candidato_nao_encontrado: "Candidato não encontrado.",
    modelo_invalido: "Modelo inválido.", erro_envio: "A mensagem não foi enviada. Tente de novo.",
  },
  sms_enviado: "Mensagem enviada.", sms_agendado: "Fora do horário permitido (8h às 21h no fuso da empresa). A mensagem sai às 8h.",
  sms_fora_horario: "Agora é horário de silêncio (antes das 8h ou depois das 21h): o envio fica agendado para as 8h.",
  sms_vazio: "Nenhuma mensagem com este candidato.",
  sms_ph: "Escreva a mensagem…", sms_enviar: "Enviar",
  sms_rodape: "O aviso \"{rodape}\" entra no fim de cada mensagem.",
  sms_modelo_enviar: "Enviar modelo", sms_modelo_escolher: "Escolha um modelo…",
  sms_modelos: { convite_teste: "Convite para os testes", lembrete_entrevista: "Lembrete de entrevista",
    onboarding_pendente: "Onboarding pendente", tentamos_ligar: "Tentamos ligar", candidatura_recebida: "Candidatura recebida" },
  sms_st: { agendado: "Agendada", enviando: "Enviando", accepted: "Na fila", queued: "Na fila", sending: "Enviando",
    sent: "Enviada", delivered: "Entregue", undelivered: "Não entregue", failed: "Falhou", recebido: "Recebida",
    resposta: "Resposta automática", cancelado: "Cancelada", read: "Lida" },
  sms_optout: "Descadastrado (STOP)", sms_consent_ok: "Consentimento registrado", sms_consent_falta: "Sem consentimento",
  sms_tel: "Celular: {tel}", sms_sem_tel: "Sem celular válido dos EUA", sms_agendada_para: "sai em {data}",
  sms_candidato: "Candidato", sms_sistema: "Sistema",
  // configurações
  sms_c_titulo: "Mensagens de texto (SMS)",
  sms_c_desc: "Mensagens de texto aos candidatos pelo número da empresa: convite para os testes, lembretes e respostas. Toda mensagem termina com o aviso de STOP no idioma do candidato e só sai entre 8h e 21h (fuso da empresa).",
  sms_c_ativo: "Enviar mensagens de texto aos candidatos",
  sms_c_consent: "Enviar só para quem marcou a caixa de consentimento no cadastro (recomendado pela lei TCPA)",
  sms_c_consent_conta: "A sua empresa exige consentimento em Dados e conta, e essa regra vale também para o SMS.",
  sms_c_contato: "Contato na resposta HELP (e-mail ou telefone)", sms_c_contato_ph: "Padrão: {contato}",
  sms_c_numero: "Número de envio: {numero}", sms_c_numero_proprio: "número próprio da empresa", sms_c_numero_plat: "número da plataforma",
  sms_c_sem_numero: "Ainda não há número de envio.",
  sms_c_modelos: "Modelos", sms_c_modelos_dica: "Variáveis: {empresa} {nome} {vaga} {link} {data} {hora} {telefone}. Em branco volta ao padrão. O aviso de STOP entra sozinho no fim.",
  sms_c_idioma: { en: "Inglês", pt: "Português", es: "Espanhol" },
  sms_c_salvar: "Salvar SMS", sms_c_salvo: "Configuração de SMS salva.", sms_c_restaurar: "Restaurar padrão",
  sms_c_so_admin: "Só o administrador da empresa altera estas configurações.", sms_c_segmentos: "{n} segmento(s)",
  // uso
  sms_u_titulo: "SMS no mês", sms_u_linha: "{usados} de {limite} segmentos", sms_u_ilimitado: "{usados} segmentos (sem limite no plano)",
  sms_u_msgs: "{n} mensagens enviadas, {r} recebidas", sms_u_excedente: "Excedente liberado: os segmentos extras são cobrados à parte.",
  sms_u_bloqueio: "Ao chegar ao limite, novos SMS ficam bloqueados até o mês que vem.",
});
Object.assign(I18N_GESTOR.en, {
  sms_titulo: "Text messages (SMS)",
  sms_off_global: "Text messaging isn't available yet: we're waiting for US carriers to approve the campaign.",
  sms_off_empresa: "Text messages are turned off for your company. An admin can turn them on in Settings.",
  sms_motivo: {
    desligado: "Text messaging isn't available yet.", empresa_desligada: "Text messages are turned off for your company.",
    sem_twilio: "The platform hasn't set up the text messaging service yet.", sem_remetente: "No sending number is set up.",
    telefone_invalido: "This candidate doesn't have a valid US mobile number.", optout: "This candidate opted out of texts (STOP).",
    sem_consentimento: "This candidate hasn't agreed to receive text messages.",
    limite_plano: "Your plan's text message limit for this month has been reached.", candidato_nao_encontrado: "Candidate not found.",
    modelo_invalido: "Invalid template.", erro_envio: "The message wasn't sent. Try again.",
  },
  sms_enviado: "Message sent.", sms_agendado: "Outside allowed hours (8 AM to 9 PM company time). The message will go out at 8 AM.",
  sms_fora_horario: "It's quiet hours right now (before 8 AM or after 9 PM): messages are scheduled for 8 AM.",
  sms_vazio: "No messages with this candidate yet.",
  sms_ph: "Type a message…", sms_enviar: "Send",
  sms_rodape: "\"{rodape}\" is added to the end of every message.",
  sms_modelo_enviar: "Send template", sms_modelo_escolher: "Choose a template…",
  sms_modelos: { convite_teste: "Assessment invitation", lembrete_entrevista: "Interview reminder",
    onboarding_pendente: "Onboarding pending", tentamos_ligar: "We tried to call you", candidatura_recebida: "Application received" },
  sms_st: { agendado: "Scheduled", enviando: "Sending", accepted: "Queued", queued: "Queued", sending: "Sending",
    sent: "Sent", delivered: "Delivered", undelivered: "Undelivered", failed: "Failed", recebido: "Received",
    resposta: "Auto reply", cancelado: "Canceled", read: "Read" },
  sms_optout: "Opted out (STOP)", sms_consent_ok: "Consent on file", sms_consent_falta: "No consent",
  sms_tel: "Mobile: {tel}", sms_sem_tel: "No valid US mobile number", sms_agendada_para: "goes out {data}",
  sms_candidato: "Candidate", sms_sistema: "System",
  sms_c_titulo: "Text messages (SMS)",
  sms_c_desc: "Text candidates from your company number: assessment invitations, reminders, and replies. Every message ends with the STOP notice in the candidate's language and only goes out between 8 AM and 9 PM (company time zone).",
  sms_c_ativo: "Send text messages to candidates",
  sms_c_consent: "Only text candidates who checked the consent box when they applied (recommended under the TCPA)",
  sms_c_consent_conta: "Your company requires consent in Data and account, and that rule also applies to texts.",
  sms_c_contato: "Contact in the HELP reply (email or phone)", sms_c_contato_ph: "Default: {contato}",
  sms_c_numero: "Sending number: {numero}", sms_c_numero_proprio: "company's own number", sms_c_numero_plat: "platform number",
  sms_c_sem_numero: "No sending number yet.",
  sms_c_modelos: "Templates", sms_c_modelos_dica: "Variables: {empresa} {nome} {vaga} {link} {data} {hora} {telefone}. Leave blank to use the default. The STOP notice is added automatically.",
  sms_c_idioma: { en: "English", pt: "Portuguese", es: "Spanish" },
  sms_c_salvar: "Save text settings", sms_c_salvo: "Text message settings saved.", sms_c_restaurar: "Restore default",
  sms_c_so_admin: "Only the company admin can change these settings.", sms_c_segmentos: "{n} segment(s)",
  sms_u_titulo: "Texts this month", sms_u_linha: "{usados} of {limite} segments", sms_u_ilimitado: "{usados} segments (no plan limit)",
  sms_u_msgs: "{n} messages sent, {r} received", sms_u_excedente: "Overage allowed: extra segments are billed separately.",
  sms_u_bloqueio: "Once you reach the limit, new texts are blocked until next month.",
});
Object.assign(I18N_GESTOR.es, {
  sms_titulo: "Mensajes de texto (SMS)",
  sms_off_global: "El envío de SMS todavía no está disponible: estamos esperando la aprobación de la campaña por parte de los operadores de EE. UU.",
  sms_off_empresa: "Los SMS están desactivados para tu empresa. Un administrador los activa en Configuración.",
  sms_motivo: {
    desligado: "El envío de SMS todavía no está disponible.", empresa_desligada: "Los SMS están desactivados para tu empresa.",
    sem_twilio: "La plataforma todavía no configuró el servicio de SMS.", sem_remetente: "No hay un número de envío configurado.",
    telefone_invalido: "El candidato no tiene un celular válido de EE. UU.", optout: "El candidato pidió no recibir SMS (STOP).",
    sem_consentimento: "El candidato no dio su consentimiento para recibir mensajes de texto.",
    limite_plano: "Se alcanzó el límite de SMS del plan este mes.", candidato_nao_encontrado: "Candidato no encontrado.",
    modelo_invalido: "Plantilla no válida.", erro_envio: "El mensaje no se envió. Inténtalo de nuevo.",
  },
  sms_enviado: "Mensaje enviado.", sms_agendado: "Fuera del horario permitido (8 a. m. a 9 p. m., hora de la empresa). El mensaje sale a las 8 a. m.",
  sms_fora_horario: "Ahora es horario de silencio (antes de las 8 a. m. o después de las 9 p. m.): el envío queda programado para las 8 a. m.",
  sms_vazio: "Todavía no hay mensajes con este candidato.",
  sms_ph: "Escribe un mensaje…", sms_enviar: "Enviar",
  sms_rodape: "El aviso \"{rodape}\" se agrega al final de cada mensaje.",
  sms_modelo_enviar: "Enviar plantilla", sms_modelo_escolher: "Elige una plantilla…",
  sms_modelos: { convite_teste: "Invitación a las evaluaciones", lembrete_entrevista: "Recordatorio de entrevista",
    onboarding_pendente: "Incorporación pendiente", tentamos_ligar: "Intentamos llamarte", candidatura_recebida: "Postulación recibida" },
  sms_st: { agendado: "Programado", enviando: "Enviando", accepted: "En cola", queued: "En cola", sending: "Enviando",
    sent: "Enviado", delivered: "Entregado", undelivered: "No entregado", failed: "Falló", recebido: "Recibido",
    resposta: "Respuesta automática", cancelado: "Cancelado", read: "Leído" },
  sms_optout: "Dado de baja (STOP)", sms_consent_ok: "Consentimiento registrado", sms_consent_falta: "Sin consentimiento",
  sms_tel: "Celular: {tel}", sms_sem_tel: "Sin celular válido de EE. UU.", sms_agendada_para: "sale el {data}",
  sms_candidato: "Candidato", sms_sistema: "Sistema",
  sms_c_titulo: "Mensajes de texto (SMS)",
  sms_c_desc: "Mensajes de texto a los candidatos desde el número de la empresa: invitación a las evaluaciones, recordatorios y respuestas. Cada mensaje termina con el aviso de STOP en el idioma del candidato y solo sale entre las 8 a. m. y las 9 p. m. (zona horaria de la empresa).",
  sms_c_ativo: "Enviar mensajes de texto a los candidatos",
  sms_c_consent: "Enviar solo a quienes marcaron la casilla de consentimiento al postularse (recomendado por la ley TCPA)",
  sms_c_consent_conta: "Tu empresa exige consentimiento en Datos y cuenta, y esa regla también vale para los SMS.",
  sms_c_contato: "Contacto en la respuesta HELP (correo o teléfono)", sms_c_contato_ph: "Predeterminado: {contato}",
  sms_c_numero: "Número de envío: {numero}", sms_c_numero_proprio: "número propio de la empresa", sms_c_numero_plat: "número de la plataforma",
  sms_c_sem_numero: "Todavía no hay número de envío.",
  sms_c_modelos: "Plantillas", sms_c_modelos_dica: "Variables: {empresa} {nome} {vaga} {link} {data} {hora} {telefone}. En blanco vuelve a la predeterminada. El aviso de STOP se agrega solo al final.",
  sms_c_idioma: { en: "Inglés", pt: "Portugués", es: "Español" },
  sms_c_salvar: "Guardar SMS", sms_c_salvo: "Configuración de SMS guardada.", sms_c_restaurar: "Restaurar predeterminada",
  sms_c_so_admin: "Solo el administrador de la empresa cambia esta configuración.", sms_c_segmentos: "{n} segmento(s)",
  sms_u_titulo: "SMS del mes", sms_u_linha: "{usados} de {limite} segmentos", sms_u_ilimitado: "{usados} segmentos (sin límite en el plan)",
  sms_u_msgs: "{n} mensajes enviados, {r} recibidos", sms_u_excedente: "Excedente permitido: los segmentos extra se cobran aparte.",
  sms_u_bloqueio: "Al llegar al límite, los nuevos SMS quedan bloqueados hasta el próximo mes.",
});

function smsTab(chave) {
  return (I18N_GESTOR[idiomaGestor] || I18N_GESTOR.pt)[chave] || I18N_GESTOR.pt[chave] || {};
}
const SMS_COR = { delivered: "ok", sent: "ok", read: "ok", failed: "err", undelivered: "err", cancelado: "neutral",
  agendado: "warn", recebido: "neutral", resposta: "neutral" };

// segmentos como a operadora conta (GSM-7: 160 ou 153 por parte; com acento fora do GSM: 70 ou 67)
function smsSegmentos(texto) {
  const basico = "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà";
  const ext = "^{}\\[~]|€\f";
  const s = String(texto || "");
  if ([...s].every((c) => basico.includes(c) || ext.includes(c))) {
    const n = s.length + [...s].filter((c) => ext.includes(c)).length;
    return n <= 160 ? 1 : Math.ceil(n / 153);
  }
  return s.length <= 70 ? 1 : Math.ceil(s.length / 67);
}

// ------------------------------------------------------------ ficha do candidato
async function smsPreencherFicha(candidatoId, el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/sms/candidato/" + candidatoId); } catch (e) { el.remove(); return; }
  smsDesenharFicha(candidatoId, el, r);
}

function smsDesenharFicha(candidatoId, el, r, aviso) {
  const st = smsTab("sms_st");
  const modelos = smsTab("sms_modelos");
  const rodape = { pt: "Responda STOP para sair.", en: "Reply STOP to opt out.", es: "Responde STOP para darte de baja." };
  const conversa = r.mensagens.map((m) => {
    const minha = m.direcao === "saida";
    const autor = minha ? (m.autor === "sistema" ? tg("sms_sistema") : esc(m.autor || "")) : tg("sms_candidato");
    const status = st[m.status] || m.status;
    return `<div style="display:flex;justify-content:${minha ? "flex-end" : "flex-start"};margin:6px 0">
      <div style="max-width:80%;padding:8px 12px;border-radius:12px;border:1px solid var(--line);${minha ? "background:var(--ok-bg)" : ""}">
        <div style="white-space:pre-wrap;word-break:break-word">${esc(m.corpo)}</div>
        <div class="hint" style="margin-top:4px">${autor} · ${esc(fmtDataHora(m.criado_em))}
          ${minha ? ` · <span class="badge ${SMS_COR[m.status] || "neutral"}">${esc(status)}</span>` : ""}
          ${m.status === "agendado" && m.agendado_para ? ` · ${tg("sms_agendada_para", { data: esc(fmtDataHora(m.agendado_para)) })}` : ""}</div>
      </div></div>`;
  }).join("");
  const pode = r.global && r.empresa && !r.motivo;
  const motivo = r.motivo ? (smsTab("sms_motivo")[r.motivo] || r.motivo) : "";
  el.innerHTML = `
    ${tituloIcone("aspas", tg("sms_titulo"))}
    <p class="desc">${r.telefone ? tg("sms_tel", { tel: esc(r.telefone) }) : tg("sms_sem_tel")}
      ${r.optout ? ` · <span class="badge err">${tg("sms_optout")}</span>` : ""}
      ${r.exige_consentimento ? ` · <span class="badge ${r.consentimento ? "ok" : "warn"}">${r.consentimento ? tg("sms_consent_ok") : tg("sms_consent_falta")}</span>` : ""}</p>
    ${!r.global ? `<p class="hint">${tg("sms_off_global")}</p>` : (!r.empresa ? `<p class="hint">${tg("sms_off_empresa")}</p>` : "")}
    <div style="max-height:320px;overflow-y:auto" id="sms-conversa">${conversa || `<p class="desc">${tg("sms_vazio")}</p>`}</div>
    ${r.global && r.empresa && motivo ? `<p class="hint" style="color:var(--warn)">${esc(motivo)}</p>` : ""}
    ${pode ? `
      <div class="no-print" style="margin-top:10px">
        ${r.fora_do_horario ? `<p class="hint">${tg("sms_fora_horario")}</p>` : ""}
        <label class="field"><textarea id="sms-texto" rows="3" maxlength="640" placeholder="${esc(tg("sms_ph"))}"></textarea></label>
        <p class="hint" id="sms-contagem">${tg("sms_rodape", { rodape: esc(rodape[idiomaGestor] || rodape.en) })}</p>
        <div class="linha-acoes">
          <button class="btn small" id="sms-enviar">${tg("sms_enviar")}</button>
          <select id="sms-modelo" style="margin:0;max-width:260px"><option value="">${esc(tg("sms_modelo_escolher"))}</option>
            ${r.modelos.map((k) => `<option value="${esc(k)}">${esc(modelos[k] || k)}</option>`).join("")}</select>
          <button class="btn secondary small" id="sms-enviar-modelo">${tg("sms_modelo_enviar")}</button>
        </div>
      </div>` : ""}
    <div class="form-erro" id="sms-msg"></div>`;
  const box = el.querySelector("#sms-conversa");
  if (box) box.scrollTop = box.scrollHeight;
  const msg = (t, bom) => { const m = el.querySelector("#sms-msg"); if (!m) return; m.style.color = bom ? "var(--ok)" : "var(--err)"; m.textContent = t; };
  if (aviso) msg(aviso.texto, aviso.bom);
  const resultado = (res) => {
    const texto = res.status === "enviado" ? tg("sms_enviado") : res.status === "agendado" ? tg("sms_agendado")
      : (smsTab("sms_motivo")[res.status] || res.status);
    smsDesenharFicha(candidatoId, el, res, { texto, bom: !!res.ok });
  };
  const txt = el.querySelector("#sms-texto");
  if (txt) txt.addEventListener("input", () => {
    const n = smsSegmentos(txt.value + "\n" + (rodape[idiomaGestor] || rodape.en));
    el.querySelector("#sms-contagem").textContent = tg("sms_rodape", { rodape: rodape[idiomaGestor] || rodape.en }) + " " + tg("sms_c_segmentos", { n: fmtNum(n) });
  });
  const enviar = el.querySelector("#sms-enviar");
  if (enviar) enviar.addEventListener("click", async () => {
    enviar.disabled = true;
    try {
      resultado(await api("/api/gestor/sms/candidato/" + candidatoId + "/responder", { method: "POST", body: { texto: txt.value } }));
    } catch (e) { msg(e.message); enviar.disabled = false; }
  });
  const btModelo = el.querySelector("#sms-enviar-modelo");
  if (btModelo) btModelo.addEventListener("click", async () => {
    const chave = el.querySelector("#sms-modelo").value;
    if (!chave) return;
    btModelo.disabled = true;
    try {
      resultado(await api("/api/gestor/sms/candidato/" + candidatoId + "/modelo", { method: "POST", body: { chave } }));
    } catch (e) { msg(e.message); btModelo.disabled = false; }
  });
}

// ------------------------------------------------------------ Configurações
async function secaoSms(el) {
  if (!el) return;
  let c;
  try { c = await api("/api/gestor/sms/config"); } catch (e) { el.innerHTML = ""; return; }
  smsCartaoConfig(el, c);
}

function smsCartaoConfig(el, c, aviso) {
  const nomesIdioma = smsTab("sms_c_idioma");
  const modelos = smsTab("sms_modelos");
  const dis = c.admin ? "" : "disabled";
  const blocos = Object.keys(c.padroes).map((k) => `
    <details style="margin:8px 0"><summary><strong>${esc(modelos[k] || k)}</strong></summary>
      ${["en", "pt", "es"].map((lang) => `
        <label class="field">${esc(nomesIdioma[lang] || lang)}
          <textarea rows="3" maxlength="${c.max_modelo}" data-sms-modelo="${k}" data-lang="${lang}" placeholder="${esc(c.padroes[k][lang])}" ${dis}>${esc(((c.modelos[k] || {})[lang]) || "")}</textarea></label>`).join("")}
      ${c.admin ? `<button class="btn ghost small" data-sms-restaurar="${k}">${tg("sms_c_restaurar")}</button>` : ""}
    </details>`).join("");
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("aspas")}<span>${tg("sms_c_titulo")}</span></h2>
      <p class="desc">${tg("sms_c_desc")}</p>
      ${!c.global ? `<p class="hint" style="color:var(--warn)">${tg("sms_off_global")}</p>` : ""}
      <p class="desc">${c.numero ? tg("sms_c_numero", { numero: esc(c.numero) }) + " (" + (c.numero_proprio ? tg("sms_c_numero_proprio") : tg("sms_c_numero_plat")) + ")" : tg("sms_c_sem_numero")}</p>
      <label style="display:block;margin:8px 0"><input type="checkbox" id="smsc-ativo" ${c.ativo ? "checked" : ""} ${dis}> ${tg("sms_c_ativo")}</label>
      <label style="display:block;margin:8px 0"><input type="checkbox" id="smsc-consent" ${c.exigir_consentimento ? "checked" : ""} ${dis}> ${tg("sms_c_consent")}</label>
      ${c.consentimento_conta ? `<p class="hint">${tg("sms_c_consent_conta")}</p>` : ""}
      <label class="field">${tg("sms_c_contato")}
        <input type="text" id="smsc-contato" maxlength="80" value="${esc(c.contato_ajuda)}" placeholder="${esc(c.contato_padrao ? tg("sms_c_contato_ph", { contato: c.contato_padrao }) : "")}" ${dis}></label>
      <h3>${tg("sms_c_modelos")}</h3>
      <p class="hint">${esc(tg("sms_c_modelos_dica"))}</p>
      ${blocos}
      ${c.admin ? "" : `<p class="hint">${tg("sms_c_so_admin")}</p>`}
      <div class="form-erro" id="smsc-msg"></div>
      ${c.admin ? `<div class="linha-acoes"><button class="btn" id="smsc-salvar">${tg("sms_c_salvar")}</button></div>` : ""}
    </div>`;
  const msg = (t, bom) => { const m = el.querySelector("#smsc-msg"); m.style.color = bom ? "var(--ok)" : "var(--err)"; m.textContent = t; };
  if (aviso) msg(aviso, true);
  el.querySelectorAll("[data-sms-restaurar]").forEach((b) => b.addEventListener("click", () => {
    el.querySelectorAll(`[data-sms-modelo="${b.dataset.smsRestaurar}"]`).forEach((t) => { t.value = ""; });
  }));
  const salvar = el.querySelector("#smsc-salvar");
  if (salvar) salvar.addEventListener("click", async () => {
    const modelosNovos = {};
    el.querySelectorAll("[data-sms-modelo]").forEach((t) => {
      modelosNovos[t.dataset.smsModelo] = modelosNovos[t.dataset.smsModelo] || {};
      modelosNovos[t.dataset.smsModelo][t.dataset.lang] = t.value.trim();
    });
    try {
      const r = await api("/api/gestor/sms/config", { method: "POST", body: {
        ativo: el.querySelector("#smsc-ativo").checked, exigir_consentimento: el.querySelector("#smsc-consent").checked,
        contato_ajuda: el.querySelector("#smsc-contato").value.trim(), modelos: modelosNovos } });
      smsCartaoConfig(el, r, tg("sms_c_salvo"));
    } catch (e) { msg(e.message); }
  });
}

// ------------------------------------------------------------ uso na área do plano
async function smsUsoPlano(el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/sms/uso"); } catch (e) { el.innerHTML = ""; return; }
  const u = r.uso;
  if (!r.global && !u.mensagens) { el.innerHTML = ""; return; }
  const pct = u.limite ? Math.min(100, Math.round(100 * u.segmentos / u.limite)) : 0;
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("aspas")}<span>${tg("sms_u_titulo")}</span></h2>
      <p class="desc"><strong>${u.ilimitado ? tg("sms_u_ilimitado", { usados: fmtNum(u.segmentos) })
        : tg("sms_u_linha", { usados: fmtNum(u.segmentos), limite: fmtNum(u.limite) })}</strong></p>
      ${u.ilimitado ? "" : `<div style="height:8px;border-radius:6px;background:var(--line);overflow:hidden">
        <div style="height:100%;width:${pct}%;background:${pct >= 100 ? "var(--err)" : pct >= 80 ? "var(--warn)" : "var(--ok)"}"></div></div>`}
      <p class="hint">${tg("sms_u_msgs", { n: fmtNum(u.mensagens), r: fmtNum(u.recebidas) })}</p>
      ${u.ilimitado ? "" : `<p class="hint">${u.excedente_permitido ? tg("sms_u_excedente") : tg("sms_u_bloqueio")}</p>`}
      ${!r.global ? `<p class="hint">${tg("sms_off_global")}</p>` : ""}
    </div>`;
}
