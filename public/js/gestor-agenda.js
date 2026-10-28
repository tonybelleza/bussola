/* =====================================================================
   Agenda de entrevistas no painel do gestor (agenda.py).
   - secaoAgenda: configuração da agenda (só o administrador da empresa).
   - agendaPreencherFicha: entrevista marcada na ficha do candidato, com
     realizada, faltou, cancelar e "Enviar link de agendamento".
   - agendaHoje: entrevistas de hoje e de amanhã na visão geral.
   - Google Agenda (google_cal.py): cada gestor conecta a própria conta;
     o administrador escolhe quais agendas valem para as entrevistas e em
     qual o evento é criado (com link do Google Meet na videochamada).
   Textos em pt, en e es (tg do i18n-gestor.js, chaves "ag_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  ag_titulo: "Agenda de entrevistas",
  ag_desc: "O candidato escolhe o horário da entrevista por um link próprio. O link vai no e-mail de resultados de quem passou na triagem por voz (STRONG ou GOOD) ou concorre a um cargo sem triagem por voz. Você também pode enviar o link pela ficha do candidato.",
  ag_ativo: "Agenda ativa (candidatos podem marcar entrevista)",
  ag_dias: "Dias da semana", ag_inicio: "Início (HH:MM)", ag_fim: "Fim (HH:MM)", ag_duracao: "Duração (minutos)",
  ag_intervalo: "Intervalo entre entrevistas (minutos)", ag_antecedencia: "Antecedência mínima (horas)",
  ag_horizonte: "Mostrar horários dos próximos (dias)", ag_max_dia: "Máximo de entrevistas por dia (vazio = sem limite)",
  ag_formato: "Formato", ag_local: "Local ou instruções", ag_local_ph: "Ex.: 100 Main St, New Britain, CT ou \"Vamos ligar para você\"",
  ag_entrevistador: "Nome de quem entrevista (aparece para o candidato)", ag_fuso: "Fuso horário",
  ag_bloqueios: "Datas bloqueadas (uma por linha, AAAA-MM-DD)", ag_salvar: "Salvar agenda", ag_salvo: "Agenda salva.",
  ag_formatos: { presencial: "Presencial", telefone: "Ligação telefônica", video: "Videochamada" },
  ag_semana: ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
  ag_ficha_titulo: "Agenda da entrevista", ag_nenhuma: "Nenhuma entrevista marcada.", ag_desligada: "A agenda de entrevistas está desativada (Configurações).",
  ag_enviar_link: "Enviar link de agendamento", ag_link_enviado: "Link enviado por e-mail ao candidato.", ag_copiar: "Copiar link", ag_copiado: "Copiado!",
  ag_sem_email: "O candidato não tem e-mail.", ag_qualifica: "Recebe o link automaticamente no e-mail de resultados.",
  ag_realizada: "Realizada", ag_faltou: "Não compareceu", ag_cancelar: "Cancelar", ag_confirmar_cancelar: "Cancelar esta entrevista? O candidato e os gestores serão avisados por e-mail.",
  ag_status: { marcada: "Marcada", cancelada: "Cancelada", realizada: "Realizada", faltou: "Não compareceu" },
  ag_historico: "Histórico",
  ag_hoje_titulo: "Entrevistas de hoje e amanhã", ag_hoje: "Hoje", ag_amanha: "Amanhã", ag_vazio: "Nenhuma entrevista.",
  ag_horarios_em: "Horários em {fuso}",
  ag_g_titulo: "Google Agenda",
  ag_g_desc: "Conecte a sua conta Google: os horários ocupados na sua agenda somem da lista do candidato e cada entrevista marcada vira um evento na sua agenda, com link do Google Meet nas videochamadas.",
  ag_g_indisponivel: "O Google Agenda ainda não foi configurado na plataforma.",
  ag_g_conectar: "Conectar Google Agenda", ag_g_reconectar: "Reconectar", ag_g_desconectar: "Desconectar",
  ag_g_conectado: "Conectado: {email}", ag_g_precisa: "Precisa reconectar",
  ag_g_precisa_desc: "O Google recusou o acesso (senha trocada ou acesso removido). Enquanto isso, a agenda usa só os horários normais.",
  ag_g_confirmar_desconectar: "Desconectar o Google Agenda? Os eventos já criados continuam na sua agenda.",
  ag_g_desconectado: "Google Agenda desconectado.", ag_g_abrindo: "Abrindo o Google…",
  ag_g_entrevistadores: "Agendas Google usadas nas entrevistas",
  ag_g_entrevistadores_desc: "Os horários ocupados das agendas marcadas saem da lista do candidato.",
  ag_g_sem_contas: "Nenhum gestor desta empresa conectou o Google Agenda ainda.",
  ag_g_organizador: "Criar os eventos na agenda de", ag_g_primeira: "Primeira agenda marcada",
  ag_g_ret_ok: "Google Agenda conectado.", ag_g_ret_negado: "A conexão com o Google Agenda foi cancelada.",
  ag_g_ret_invalido: "O link de conexão expirou. Tente conectar de novo.", ag_g_ret_erro: "Não foi possível conectar ao Google Agenda. Tente de novo.",
  ag_meet: "Entrar no Google Meet",
});
Object.assign(I18N_GESTOR.en, {
  ag_titulo: "Interview scheduling",
  ag_desc: "Candidates pick their interview time with a personal link. The link goes in the results email for candidates who passed the voice screening (STRONG or GOOD) or applied to a role without voice screening. You can also send the link from the candidate profile.",
  ag_ativo: "Scheduling on (candidates can book interviews)",
  ag_dias: "Weekdays", ag_inicio: "Start (HH:MM, 24h)", ag_fim: "End (HH:MM, 24h)", ag_duracao: "Length (minutes)",
  ag_intervalo: "Break between interviews (minutes)", ag_antecedencia: "Minimum notice (hours)",
  ag_horizonte: "Show times for the next (days)", ag_max_dia: "Max interviews per day (blank = no limit)",
  ag_formato: "Format", ag_local: "Location or instructions", ag_local_ph: "E.g. 100 Main St, New Britain, CT or \"We'll call you\"",
  ag_entrevistador: "Interviewer name (shown to candidates)", ag_fuso: "Time zone",
  ag_bloqueios: "Blocked dates (one per line, YYYY-MM-DD)", ag_salvar: "Save scheduling", ag_salvo: "Scheduling saved.",
  ag_formatos: { presencial: "In person", telefone: "Phone call", video: "Video call" },
  ag_semana: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  ag_ficha_titulo: "Interview schedule", ag_nenhuma: "No interview scheduled.", ag_desligada: "Interview scheduling is off (Settings).",
  ag_enviar_link: "Send scheduling link", ag_link_enviado: "Link emailed to the candidate.", ag_copiar: "Copy link", ag_copiado: "Copied!",
  ag_sem_email: "This candidate has no email.", ag_qualifica: "Gets the link automatically in the results email.",
  ag_realizada: "Done", ag_faltou: "No-show", ag_cancelar: "Cancel", ag_confirmar_cancelar: "Cancel this interview? The candidate and managers will be notified by email.",
  ag_status: { marcada: "Scheduled", cancelada: "Canceled", realizada: "Done", faltou: "No-show" },
  ag_historico: "History",
  ag_hoje_titulo: "Interviews today and tomorrow", ag_hoje: "Today", ag_amanha: "Tomorrow", ag_vazio: "No interviews.",
  ag_horarios_em: "Times in {fuso}",
  ag_g_titulo: "Google Calendar",
  ag_g_desc: "Connect your Google account: busy times on your calendar disappear from the candidate's list, and each booked interview becomes an event on your calendar, with a Google Meet link for video calls.",
  ag_g_indisponivel: "Google Calendar has not been set up on the platform yet.",
  ag_g_conectar: "Connect Google Calendar", ag_g_reconectar: "Reconnect", ag_g_desconectar: "Disconnect",
  ag_g_conectado: "Connected: {email}", ag_g_precisa: "Needs reconnecting",
  ag_g_precisa_desc: "Google refused access (password changed or access removed). Meanwhile, scheduling uses the regular times only.",
  ag_g_confirmar_desconectar: "Disconnect Google Calendar? Events already created stay on your calendar.",
  ag_g_desconectado: "Google Calendar disconnected.", ag_g_abrindo: "Opening Google…",
  ag_g_entrevistadores: "Google calendars used for interviews",
  ag_g_entrevistadores_desc: "Busy times on the checked calendars are removed from the candidate's list.",
  ag_g_sem_contas: "No manager at this company has connected Google Calendar yet.",
  ag_g_organizador: "Create events on the calendar of", ag_g_primeira: "First checked calendar",
  ag_g_ret_ok: "Google Calendar connected.", ag_g_ret_negado: "The Google Calendar connection was canceled.",
  ag_g_ret_invalido: "The connection link expired. Try connecting again.", ag_g_ret_erro: "Could not connect to Google Calendar. Try again.",
  ag_meet: "Join Google Meet",
});
Object.assign(I18N_GESTOR.es, {
  ag_titulo: "Agenda de entrevistas",
  ag_desc: "El candidato elige el horario de la entrevista con un enlace propio. El enlace va en el correo de resultados de quien pasó la evaluación por voz (STRONG o GOOD) o postuló a un puesto sin evaluación por voz. También puedes enviar el enlace desde la ficha del candidato.",
  ag_ativo: "Agenda activa (los candidatos pueden agendar entrevistas)",
  ag_dias: "Días de la semana", ag_inicio: "Inicio (HH:MM)", ag_fim: "Fin (HH:MM)", ag_duracao: "Duración (minutos)",
  ag_intervalo: "Pausa entre entrevistas (minutos)", ag_antecedencia: "Anticipación mínima (horas)",
  ag_horizonte: "Mostrar horarios de los próximos (días)", ag_max_dia: "Máximo de entrevistas por día (vacío = sin límite)",
  ag_formato: "Formato", ag_local: "Lugar o instrucciones", ag_local_ph: "Ej.: 100 Main St, New Britain, CT o \"Te llamaremos\"",
  ag_entrevistador: "Nombre de quien entrevista (lo ve el candidato)", ag_fuso: "Zona horaria",
  ag_bloqueios: "Fechas bloqueadas (una por línea, AAAA-MM-DD)", ag_salvar: "Guardar agenda", ag_salvo: "Agenda guardada.",
  ag_formatos: { presencial: "Presencial", telefone: "Llamada telefónica", video: "Videollamada" },
  ag_semana: ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
  ag_ficha_titulo: "Agenda de la entrevista", ag_nenhuma: "No hay entrevista agendada.", ag_desligada: "La agenda de entrevistas está desactivada (Configuración).",
  ag_enviar_link: "Enviar enlace para agendar", ag_link_enviado: "Enlace enviado por correo al candidato.", ag_copiar: "Copiar enlace", ag_copiado: "¡Copiado!",
  ag_sem_email: "El candidato no tiene correo.", ag_qualifica: "Recibe el enlace automáticamente en el correo de resultados.",
  ag_realizada: "Realizada", ag_faltou: "No se presentó", ag_cancelar: "Cancelar", ag_confirmar_cancelar: "¿Cancelar esta entrevista? El candidato y los gestores recibirán un aviso por correo.",
  ag_status: { marcada: "Agendada", cancelada: "Cancelada", realizada: "Realizada", faltou: "No se presentó" },
  ag_historico: "Historial",
  ag_hoje_titulo: "Entrevistas de hoy y mañana", ag_hoje: "Hoy", ag_amanha: "Mañana", ag_vazio: "Ninguna entrevista.",
  ag_horarios_em: "Horarios en {fuso}",
  ag_g_titulo: "Google Calendar",
  ag_g_desc: "Conecta tu cuenta de Google: los horarios ocupados en tu calendario desaparecen de la lista del candidato y cada entrevista agendada se vuelve un evento en tu calendario, con enlace de Google Meet en las videollamadas.",
  ag_g_indisponivel: "Google Calendar todavía no está configurado en la plataforma.",
  ag_g_conectar: "Conectar Google Calendar", ag_g_reconectar: "Reconectar", ag_g_desconectar: "Desconectar",
  ag_g_conectado: "Conectado: {email}", ag_g_precisa: "Hay que reconectar",
  ag_g_precisa_desc: "Google rechazó el acceso (contraseña cambiada o acceso eliminado). Mientras tanto, la agenda usa solo los horarios normales.",
  ag_g_confirmar_desconectar: "¿Desconectar Google Calendar? Los eventos ya creados siguen en tu calendario.",
  ag_g_desconectado: "Google Calendar desconectado.", ag_g_abrindo: "Abriendo Google…",
  ag_g_entrevistadores: "Calendarios de Google usados en las entrevistas",
  ag_g_entrevistadores_desc: "Los horarios ocupados de los calendarios marcados salen de la lista del candidato.",
  ag_g_sem_contas: "Ningún gestor de esta empresa conectó Google Calendar todavía.",
  ag_g_organizador: "Crear los eventos en el calendario de", ag_g_primeira: "Primer calendario marcado",
  ag_g_ret_ok: "Google Calendar conectado.", ag_g_ret_negado: "Se canceló la conexión con Google Calendar.",
  ag_g_ret_invalido: "El enlace de conexión venció. Intenta conectar de nuevo.", ag_g_ret_erro: "No se pudo conectar con Google Calendar. Inténtalo de nuevo.",
  ag_meet: "Unirse a Google Meet",
});

// objetos e listas do dicionário (tg devolve só texto)
function agTabela(chave) {
  return (I18N_GESTOR[idiomaGestor] || I18N_GESTOR.pt)[chave] || I18N_GESTOR.pt[chave];
}

function agQuando(inicioUtc, fuso) {
  try {
    return new Intl.DateTimeFormat(localeGestor(), {
      timeZone: fuso || "America/New_York", weekday: "short", day: "numeric", month: "short", hour: "numeric", minute: "2-digit",
    }).format(new Date(inicioUtc));
  } catch (e) { return inicioUtc; }
}

const AG_COR_STATUS = { marcada: "info", cancelada: "err", realizada: "ok", faltou: "warn" };

// ------------------------------------------------------------ configuração (admin)
// ------------------------------------------------------------ Google Agenda
function agLinkSeguro(url) {
  return /^https:\/\//i.test(String(url || "")) ? url : "";
}

// conexão do próprio gestor (todos os gestores)
function agGoogleMinha(g) {
  let corpo;
  if (!g.disponivel && !g.minha) corpo = `<p class="hint">${tg("ag_g_indisponivel")}</p>`;
  else if (!g.minha) corpo = `<button class="btn secondary small" data-ag-g="conectar">${tg("ag_g_conectar")}</button>`;
  else if (g.minha.status !== "ativa") corpo = `
      <p class="desc"><span class="badge warn">${tg("ag_g_precisa")}</span> ${esc(g.minha.email || "")}</p>
      <p class="hint">${tg("ag_g_precisa_desc")}</p>
      <div class="linha-acoes">${g.disponivel ? `<button class="btn small" data-ag-g="conectar">${tg("ag_g_reconectar")}</button>` : ""}
        <button class="btn ghost small" data-ag-g="desconectar">${tg("ag_g_desconectar")}</button></div>`;
  else corpo = `
      <p class="desc"><span class="badge ok">${esc(tg("ag_g_conectado", { email: g.minha.email || "Google" }))}</span></p>
      <div class="linha-acoes"><button class="btn ghost small" data-ag-g="desconectar">${tg("ag_g_desconectar")}</button></div>`;
  return `
    <div class="sub-card" style="margin:12px 0">
      <h3 style="margin-top:0">${tg("ag_g_titulo")}</h3>
      <p class="desc">${tg("ag_g_desc")}</p>
      ${corpo}
      <span class="hint" id="ag-g-msg"></span>
    </div>`;
}

// escolha das agendas da empresa (administrador)
function agGoogleEscolha(g, c) {
  const contas = g.contas || [];
  if (!g.disponivel && !contas.length) return "";
  const marcados = (c.google_entrevistadores || []).map(Number);
  return `
    <div class="field" style="margin:6px 0 14px">${tg("ag_g_entrevistadores")}
      <span class="hint">${tg("ag_g_entrevistadores_desc")}</span>
      ${contas.length ? `
        <div style="display:flex;flex-direction:column;gap:6px;margin-top:6px">
          ${contas.map((x) => `<label style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-ag-google="${x.gestor_id}" ${marcados.includes(x.gestor_id) ? "checked" : ""}>
            <strong>${esc(x.nome)}</strong> <span class="hint">${esc(x.email || "")}</span>
            ${x.status !== "ativa" ? `<span class="badge warn">${tg("ag_g_precisa")}</span>` : ""}</label>`).join("")}
        </div>
        <label class="field" style="margin-top:8px">${tg("ag_g_organizador")}
          <select id="ag-g-org"><option value="0">${tg("ag_g_primeira")}</option>
            ${contas.map((x) => `<option value="${x.gestor_id}" ${Number(c.google_organizador) === x.gestor_id ? "selected" : ""}>${esc(x.nome)}</option>`).join("")}
          </select></label>` : `<p class="hint">${tg("ag_g_sem_contas")}</p>`}
    </div>`;
}

function agLigarGoogle(el, recarregar) {
  const msg = (texto, ok) => {
    const m = el.querySelector("#ag-g-msg");
    if (m) { m.style.color = ok ? "var(--ok)" : "var(--err)"; m.textContent = texto; } else alert(texto);
  };
  el.querySelectorAll("[data-ag-g]").forEach((b) => b.addEventListener("click", async () => {
    if (b.dataset.agG === "conectar") {
      b.disabled = true;
      try {
        const r = await api("/api/gestor/agenda/google/conectar", { method: "POST", body: {} });
        msg(tg("ag_g_abrindo"), true);
        location.href = r.url;
      } catch (e) { msg(e.message); b.disabled = false; }
      return;
    }
    if (!confirm(tg("ag_g_confirmar_desconectar"))) return;
    try {
      await api("/api/gestor/agenda/google/desconectar", { method: "POST", body: {} });
      recarregar();
    } catch (e) { msg(e.message); }
  }));
}

async function secaoAgenda(el) {
  if (!el) return;
  let g = null;
  try { g = await api("/api/gestor/agenda/google"); } catch (e) { g = null; }
  if (!infoGestor().admin) {
    // gestor sem administração: só a própria conexão com o Google Agenda
    el.innerHTML = g && (g.disponivel || g.minha) ? `<div class="card">${agGoogleMinha(g)}</div>` : "";
    agLigarGoogle(el, () => secaoAgenda(el));
    return;
  }
  let r;
  try { r = await api("/api/gestor/agenda/config"); } catch (e) { el.innerHTML = ""; return; }
  const c = r.config;
  const semana = agTabela("ag_semana");
  const formatos = agTabela("ag_formatos");
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("bloco")}<span>${tg("ag_titulo")}</span></h2>
      <p class="desc">${tg("ag_desc")}</p>
      <label style="display:flex;gap:8px;align-items:center;margin:6px 0 12px"><input type="checkbox" id="ag-ativo" ${c.ativo ? "checked" : ""}> <strong>${tg("ag_ativo")}</strong></label>
      <div class="field" style="margin-bottom:14px">${tg("ag_dias")}
        <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:6px">
          ${semana.map((nome, i) => `<label style="display:flex;gap:4px;align-items:center"><input type="checkbox" data-ag-dia="${i + 1}" ${(c.dias || []).includes(i + 1) ? "checked" : ""}> ${esc(nome)}</label>`).join("")}
        </div>
      </div>
      <div class="grid cols-2">
        <div class="grid cols-2">
          <label class="field">${tg("ag_inicio")}<input type="text" id="ag-inicio" inputmode="numeric" maxlength="5" placeholder="09:00" value="${esc(c.inicio)}"></label>
          <label class="field">${tg("ag_fim")}<input type="text" id="ag-fim" inputmode="numeric" maxlength="5" placeholder="17:00" value="${esc(c.fim)}"></label>
        </div>
        <div class="grid cols-2">
          <label class="field">${tg("ag_duracao")}<input type="number" min="5" max="480" id="ag-duracao" value="${esc(String(c.duracao))}"></label>
          <label class="field">${tg("ag_intervalo")}<input type="number" min="0" max="240" id="ag-intervalo" value="${esc(String(c.intervalo || 0))}"></label>
        </div>
        <div class="grid cols-2">
          <label class="field">${tg("ag_antecedencia")}<input type="number" min="0" max="720" id="ag-antecedencia" value="${esc(String(c.antecedencia_horas))}"></label>
          <label class="field">${tg("ag_horizonte")}<input type="number" min="1" max="180" id="ag-horizonte" value="${esc(String(c.horizonte_dias))}"></label>
        </div>
        <label class="field">${tg("ag_max_dia")}<input type="number" min="0" max="200" id="ag-max" value="${c.max_por_dia ? esc(String(c.max_por_dia)) : ""}"></label>
        <label class="field">${tg("ag_formato")}
          <select id="ag-formato">${r.formatos.map((f) => `<option value="${f}" ${c.formato === f ? "selected" : ""}>${esc(formatos[f] || f)}</option>`).join("")}</select></label>
        <label class="field">${tg("ag_fuso")}<input type="text" id="ag-fuso" value="${esc(c.fuso || "")}" placeholder="America/New_York" list="ag-fusos">
          <datalist id="ag-fusos">${["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Sao_Paulo", "America/Mexico_City", "America/Bogota", "Europe/Lisbon", "Africa/Luanda"].map((z) => `<option value="${z}"></option>`).join("")}</datalist></label>
        <label class="field">${tg("ag_entrevistador")}<input type="text" id="ag-entrevistador" maxlength="120" value="${esc(c.entrevistador || "")}"></label>
        <label class="field">${tg("ag_local")}<input type="text" id="ag-local" maxlength="500" value="${esc(c.local || "")}" placeholder="${esc(tg("ag_local_ph"))}"></label>
      </div>
      <label class="field">${tg("ag_bloqueios")}<textarea id="ag-bloqueios" rows="3" placeholder="2026-12-25">${esc((c.bloqueios || []).join("\n"))}</textarea></label>
      ${g ? agGoogleMinha(g) + agGoogleEscolha(g, c) : ""}
      <div class="form-erro" id="ag-msg"></div>
      <div class="linha-acoes"><button class="btn" id="ag-salvar">${tg("ag_salvar")}</button></div>
    </div>`;
  const msg = (texto, ok) => {
    const m = el.querySelector("#ag-msg");
    m.style.color = ok ? "var(--ok)" : "var(--err)";
    m.textContent = texto;
  };
  el.querySelector("#ag-salvar").addEventListener("click", async () => {
    const v = (id) => el.querySelector(id).value.trim();
    const corpo = {
      ativo: el.querySelector("#ag-ativo").checked,
      dias: [...el.querySelectorAll("[data-ag-dia]")].filter((x) => x.checked).map((x) => Number(x.dataset.agDia)),
      inicio: v("#ag-inicio"), fim: v("#ag-fim"), duracao: v("#ag-duracao"), intervalo: v("#ag-intervalo") || 0,
      antecedencia_horas: v("#ag-antecedencia") || 0, horizonte_dias: v("#ag-horizonte"), max_por_dia: v("#ag-max") || 0,
      formato: v("#ag-formato"), fuso: v("#ag-fuso"), entrevistador: v("#ag-entrevistador"), local: v("#ag-local"),
      bloqueios: v("#ag-bloqueios"),
    };
    if (g && (g.contas || []).length) {
      corpo.google_entrevistadores = [...el.querySelectorAll("[data-ag-google]")].filter((x) => x.checked).map((x) => Number(x.dataset.agGoogle));
      corpo.google_organizador = Number((el.querySelector("#ag-g-org") || {}).value || 0);
    }
    try {
      await api("/api/gestor/agenda/config", { method: "POST", body: corpo });
      msg(tg("ag_salvo"), true);
    } catch (e) { msg(e.message); }
  });
  agLigarGoogle(el, () => secaoAgenda(el));
}

// ------------------------------------------------------------ ficha do candidato
async function agendaPreencherFicha(candidatoId, el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/agenda/candidato/" + candidatoId); } catch (e) { el.remove(); return; }
  const status = agTabela("ag_status");
  const ent = r.entrevista;
  const antigas = (r.historico || []).filter((h) => h.status !== "marcada");
  el.innerHTML = `
    ${tituloIcone("bloco", tg("ag_ficha_titulo"))}
    ${ent ? `
      <div class="perfil-destaque">
        <div class="titulo">${esc(agQuando(ent.inicio_utc, r.fuso))}</div>
        <div><span class="badge ${AG_COR_STATUS[ent.status] || "tipo"}">${esc(status[ent.status] || ent.status)}</span>
          <span class="hint">${esc(tg("ag_horarios_em", { fuso: r.rotulo_fuso }))}</span></div>
        ${agLinkSeguro(ent.meet_link) ? `<div style="margin-top:6px"><a href="${esc(ent.meet_link)}" target="_blank" rel="noopener">${icone("link")} ${tg("ag_meet")}</a></div>` : ""}
      </div>
      <div class="linha-acoes no-print">
        <button class="btn secondary small" data-ag-status="realizada">${tg("ag_realizada")}</button>
        <button class="btn secondary small" data-ag-status="faltou">${tg("ag_faltou")}</button>
        <button class="btn danger small" data-ag-status="cancelada">${tg("ag_cancelar")}</button>
      </div>` : `<p class="desc">${r.ativo ? tg("ag_nenhuma") : tg("ag_desligada")}</p>`}
    ${r.ativo ? `
      <div class="linha-acoes no-print" style="margin-top:8px">
        <button class="btn secondary small" id="ag-enviar-link" ${r.tem_email ? "" : `disabled title="${esc(tg("ag_sem_email"))}"`}>${icone("link")} ${tg("ag_enviar_link")}</button>
        ${r.link ? `<button class="btn ghost small" id="ag-copiar-link">${tg("ag_copiar")}</button>` : ""}
        <span class="hint" id="ag-ficha-msg">${r.qualifica ? esc(tg("ag_qualifica")) : ""}</span>
      </div>` : ""}
    ${antigas.length ? `
      <h3 style="margin-top:14px">${tg("ag_historico")}</h3>
      <ul class="lista-simples">${antigas.map((h) => `<li>${esc(agQuando(h.inicio_utc, r.fuso))} <span class="badge ${AG_COR_STATUS[h.status] || "tipo"}">${esc(status[h.status] || h.status)}</span>
        ${h.status !== "cancelada" ? `<a href="#" class="no-print" data-ag-hist="${h.id}" data-ag-novo="${h.status === "realizada" ? "faltou" : "realizada"}" style="font-size:.78rem;margin-left:6px">${esc(h.status === "realizada" ? tg("ag_faltou") : tg("ag_realizada"))}</a>` : ""}</li>`).join("")}</ul>` : ""}`;
  const aviso = (texto, ok) => {
    const m = el.querySelector("#ag-ficha-msg");
    if (m) { m.style.color = ok ? "var(--ok)" : "var(--err)"; m.textContent = texto; } else if (!ok) alert(texto);
  };
  const mudar = async (id, novo) => {
    if (novo === "cancelada" && !confirm(tg("ag_confirmar_cancelar"))) return;
    try {
      await api("/api/gestor/agenda/entrevista/" + id + "/status", { method: "POST", body: { status: novo } });
      agendaPreencherFicha(candidatoId, el);
    } catch (e) { aviso(e.message); }
  };
  el.querySelectorAll("[data-ag-status]").forEach((b) => b.addEventListener("click", () => mudar(ent.id, b.dataset.agStatus)));
  el.querySelectorAll("[data-ag-hist]").forEach((a) => a.addEventListener("click", (ev) => {
    ev.preventDefault();
    mudar(Number(a.dataset.agHist), a.dataset.agNovo);
  }));
  const enviar = el.querySelector("#ag-enviar-link");
  if (enviar) enviar.addEventListener("click", async () => {
    enviar.disabled = true;
    try {
      await api("/api/gestor/agenda/enviar-link", { method: "POST", body: { candidato_id: candidatoId } });
      aviso(tg("ag_link_enviado"), true);
    } catch (e) { aviso(e.message); }
    enviar.disabled = false;
  });
  const copiar = el.querySelector("#ag-copiar-link");
  if (copiar) copiar.addEventListener("click", () => {
    navigator.clipboard.writeText(r.link).then(() => { copiar.textContent = tg("ag_copiado"); }).catch(() => {});
  });
}

// ------------------------------------------------------------ visão geral: hoje e amanhã
async function agendaHoje(el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/agenda/proximas"); } catch (e) { el.remove(); return; }
  if (!r.ativo && !r.hoje.length && !r.amanha.length) { el.remove(); return; }
  const status = agTabela("ag_status");
  const lista = (itens) => itens.length ? itens.map((i) => `
    <div style="padding:6px 0;border-top:1px solid var(--line, rgba(127,127,127,.15));display:flex;gap:10px;align-items:baseline">
      <strong style="min-width:52px">${esc(i.hora)}</strong>
      <div style="flex:1"><a href="#" data-agenda-cand="${i.candidato_id}"><strong>${esc(i.nome)}</strong></a>
        ${i.telefone ? `<div class="hint">${esc(i.telefone)}</div>` : ""}</div>
      ${i.status !== "marcada" ? `<span class="badge ${AG_COR_STATUS[i.status] || "tipo"}">${esc(status[i.status] || i.status)}</span>` : ""}
    </div>`).join("") : `<p class="desc" style="margin:0">${tg("ag_vazio")}</p>`;
  el.innerHTML = `
    <h2 style="margin-top:0">${tg("ag_hoje_titulo")}</h2>
    <p class="desc">${esc(tg("ag_horarios_em", { fuso: r.rotulo_fuso }))}</p>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px">
      <div class="sub-card" style="margin:0">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <strong>${tg("ag_hoje")}</strong><span class="badge info">${fmtNum(r.hoje.length)}</span></div>
        ${lista(r.hoje)}
      </div>
      <div class="sub-card" style="margin:0">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <strong>${tg("ag_amanha")}</strong><span class="badge neutral">${fmtNum(r.amanha.length)}</span></div>
        ${lista(r.amanha)}
      </div>
    </div>`;
  el.querySelectorAll("[data-agenda-cand]").forEach((a) => a.addEventListener("click", (ev) => {
    ev.preventDefault();
    abrirDetalheCandidato(Number(a.dataset.agendaCand));
  }));
}

// ------------------------------------------------------------ volta do Google (/gestor#google=ok|negado|invalido|erro)
(function agRetornoGoogle() {
  const m = location.hash.match(/^#google=(\w+)$/);
  if (!m) return;
  try { history.replaceState(null, "", location.pathname + location.search); } catch (e) { /* sem history */ }
  const chave = { ok: "ag_g_ret_ok", negado: "ag_g_ret_negado", invalido: "ag_g_ret_invalido" }[m[1]] || "ag_g_ret_erro";
  window.addEventListener("load", () => setTimeout(() => alert(tg(chave)), 400));
})();
