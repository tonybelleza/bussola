/* =====================================================================
   Relatório de contratação (painel do gestor, aba Relatórios).
   - relatoriosContratacao(el): cartão com período (30 ou 90 dias, este
     ano, personalizado), filtros de vaga e cargo, indicadores, funil,
     origem dos candidatos, tempos, custo da voz, tendência semanal,
     tabelas por vaga e por cargo e motivos de encerramento.
   - Exporta CSV das tabelas de origem e de vagas.
   Dados: GET /api/gestor/relatorios/contratacao (relatorios.py).
   Textos em pt, en e es (tg do i18n-gestor.js, chaves "hr_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  hr_titulo: "Relatório de contratação",
  hr_desc: "Candidaturas recebidas no período escolhido e até onde cada uma chegou. Só entram candidatos que você pode ver.",
  hr_periodo: "Período", hr_p30: "Últimos 30 dias", hr_p90: "Últimos 90 dias", hr_pano: "Este ano", hr_pcustom: "Personalizado",
  hr_de: "De", hr_ate: "Até", hr_aplicar: "Aplicar", hr_vaga: "Vaga", hr_cargo: "Cargo", hr_todas: "Todas", hr_todos: "Todos",
  hr_carregando: "Carregando relatório...", hr_erro: "Não foi possível carregar o relatório: {e}",
  hr_k_inscritos: "Candidaturas", hr_k_qualificados: "Qualificados", hr_k_entrevistas: "Entrevistas", hr_k_contratados: "Contratados",
  hr_k_tempo: "Mediana até contratar", hr_k_custo: "Custo da voz", hr_k_de: "{p} do total",
  hr_funil: "Funil de contratação", hr_funil_desc: "Cada barra mostra quantos chegaram à etapa. A porcentagem compara com quem chegou à etapa anterior.",
  hr_f_inscritos: "Inscritos", hr_f_triados: "Atenderam a ligação", hr_f_qualificados: "Qualificados (STRONG ou GOOD)",
  hr_f_testes: "Testes concluídos", hr_f_entrevista_marcada: "Entrevista marcada", hr_f_entrevista_realizada: "Entrevista realizada",
  hr_f_proposta: "Proposta", hr_f_contratados: "Contratados",
  hr_conv: "{p} da etapa anterior", hr_reprovados: "Reprovados no período: {n}",
  hr_fontes: "Origem dos candidatos", hr_fontes_desc: "De onde vieram as candidaturas e quantas viraram contratação.",
  hr_src_indeed: "Indeed", hr_src_facebook: "Facebook", hr_src_notion: "Notion", hr_src_csv: "Planilha (CSV)",
  hr_src_indicacao: "Indicação", hr_src_site: "Site",
  hr_c_fonte: "Origem", hr_c_inscritos: "Inscritos", hr_c_qualificados: "Qualificados", hr_c_contratados: "Contratados",
  hr_c_qualif_pct: "% qualificados", hr_c_conv: "Conversão", hr_c_vaga: "Vaga", hr_c_cargo: "Cargo",
  hr_c_triados: "Atenderam", hr_c_entrevistas: "Entrevistas", hr_c_reprovados: "Reprovados",
  hr_c_tempo: "Mediana (dias)", hr_c_custo: "Custo da voz", hr_c_status: "Status",
  hr_csv: "Exportar CSV", hr_csv_fontes: "origem-candidatos", hr_csv_vagas: "contratacao-por-vaga",
  hr_tempos: "Tempos", hr_t_contratar: "Da inscrição à contratação", hr_t_ligacao: "Da inscrição à primeira ligação",
  hr_t_entrevista: "Da ligação à entrevista", hr_t_mediana: "mediana", hr_t_media: "média {v}",
  hr_t_base: "base: {n}", hr_dias: "{n} dias", hr_dia: "{n} dia", hr_horas: "{n} h",
  hr_custo: "Custo da triagem por voz", hr_custo_desc: "Ligações feitas no período. Estimativa: minutos x {c} por minuto (voz + telefonia).",
  hr_c_ligacoes: "Ligações", hr_c_minutos: "Minutos", hr_c_total: "Custo estimado", hr_c_por_qualif: "Por qualificado", hr_c_por_contr: "Por contratação",
  hr_tendencia: "Tendência semanal", hr_tend_inscritos: "Candidaturas", hr_tend_contratados: "Contratações",
  hr_tend_semana: "Semana de {d}",
  hr_vagas: "Por vaga", hr_cargos: "Por cargo",
  hr_encerramentos: "Motivos de encerramento", hr_enc_desc: "Por que as candidaturas do período saíram do processo.",
  hr_e_numero_errado: "Número errado", hr_e_sem_interesse: "Sem interesse", hr_e_nao_ligar: "Pediu para não ligar",
  hr_e_nao_qualificado: "Não qualificado na ligação", hr_e_sem_resposta: "Sem resposta (tentativas esgotadas)",
  hr_e_reprovacao_manual: "Reprovado pelo gestor", hr_motivos: "Motivos informados pelo gestor", hr_sem_motivo: "(sem motivo)",
  hr_vazio: "Nenhuma candidatura neste período.", hr_nada: "Nada a mostrar.",
});
Object.assign(I18N_GESTOR.en, {
  hr_titulo: "Hiring report",
  hr_desc: "Applications received in the selected period and how far each one got. Only candidates you can see are included.",
  hr_periodo: "Period", hr_p30: "Last 30 days", hr_p90: "Last 90 days", hr_pano: "This year", hr_pcustom: "Custom",
  hr_de: "From", hr_ate: "To", hr_aplicar: "Apply", hr_vaga: "Job", hr_cargo: "Position", hr_todas: "All", hr_todos: "All",
  hr_carregando: "Loading report...", hr_erro: "Could not load the report: {e}",
  hr_k_inscritos: "Applications", hr_k_qualificados: "Qualified", hr_k_entrevistas: "Interviews", hr_k_contratados: "Hires",
  hr_k_tempo: "Median time to hire", hr_k_custo: "Voice cost", hr_k_de: "{p} of total",
  hr_funil: "Hiring funnel", hr_funil_desc: "Each bar shows how many reached the stage. The percentage compares with those who reached the previous stage.",
  hr_f_inscritos: "Applied", hr_f_triados: "Answered the call", hr_f_qualificados: "Qualified (STRONG or GOOD)",
  hr_f_testes: "Tests completed", hr_f_entrevista_marcada: "Interview scheduled", hr_f_entrevista_realizada: "Interview done",
  hr_f_proposta: "Offer", hr_f_contratados: "Hired",
  hr_conv: "{p} of previous stage", hr_reprovados: "Rejected in the period: {n}",
  hr_fontes: "Candidate sources", hr_fontes_desc: "Where applications came from and how many turned into hires.",
  hr_src_indeed: "Indeed", hr_src_facebook: "Facebook", hr_src_notion: "Notion", hr_src_csv: "Spreadsheet (CSV)",
  hr_src_indicacao: "Referral", hr_src_site: "Website",
  hr_c_fonte: "Source", hr_c_inscritos: "Applied", hr_c_qualificados: "Qualified", hr_c_contratados: "Hired",
  hr_c_qualif_pct: "% qualified", hr_c_conv: "Conversion", hr_c_vaga: "Job", hr_c_cargo: "Position",
  hr_c_triados: "Answered", hr_c_entrevistas: "Interviews", hr_c_reprovados: "Rejected",
  hr_c_tempo: "Median (days)", hr_c_custo: "Voice cost", hr_c_status: "Status",
  hr_csv: "Export CSV", hr_csv_fontes: "candidate-sources", hr_csv_vagas: "hiring-by-job",
  hr_tempos: "Timing", hr_t_contratar: "Application to hire", hr_t_ligacao: "Application to first call",
  hr_t_entrevista: "Call to interview", hr_t_mediana: "median", hr_t_media: "average {v}",
  hr_t_base: "based on {n}", hr_dias: "{n} days", hr_dia: "{n} day", hr_horas: "{n} h",
  hr_custo: "Voice screening cost", hr_custo_desc: "Calls made in the period. Estimate: minutes x {c} per minute (voice + telephony).",
  hr_c_ligacoes: "Calls", hr_c_minutos: "Minutes", hr_c_total: "Estimated cost", hr_c_por_qualif: "Per qualified", hr_c_por_contr: "Per hire",
  hr_tendencia: "Weekly trend", hr_tend_inscritos: "Applications", hr_tend_contratados: "Hires",
  hr_tend_semana: "Week of {d}",
  hr_vagas: "By job", hr_cargos: "By position",
  hr_encerramentos: "Closure reasons", hr_enc_desc: "Why applications from the period left the process.",
  hr_e_numero_errado: "Wrong number", hr_e_sem_interesse: "Not interested", hr_e_nao_ligar: "Asked not to be called",
  hr_e_nao_qualificado: "Not qualified on the call", hr_e_sem_resposta: "No answer (attempts used up)",
  hr_e_reprovacao_manual: "Rejected by a manager", hr_motivos: "Reasons given by managers", hr_sem_motivo: "(no reason)",
  hr_vazio: "No applications in this period.", hr_nada: "Nothing to show.",
});
Object.assign(I18N_GESTOR.es, {
  hr_titulo: "Informe de contratación",
  hr_desc: "Solicitudes recibidas en el período elegido y hasta dónde llegó cada una. Solo se incluyen candidatos que puedes ver.",
  hr_periodo: "Período", hr_p30: "Últimos 30 días", hr_p90: "Últimos 90 días", hr_pano: "Este año", hr_pcustom: "Personalizado",
  hr_de: "Desde", hr_ate: "Hasta", hr_aplicar: "Aplicar", hr_vaga: "Vacante", hr_cargo: "Cargo", hr_todas: "Todas", hr_todos: "Todos",
  hr_carregando: "Cargando informe...", hr_erro: "No se pudo cargar el informe: {e}",
  hr_k_inscritos: "Solicitudes", hr_k_qualificados: "Calificados", hr_k_entrevistas: "Entrevistas", hr_k_contratados: "Contratados",
  hr_k_tempo: "Mediana hasta contratar", hr_k_custo: "Costo de voz", hr_k_de: "{p} del total",
  hr_funil: "Embudo de contratación", hr_funil_desc: "Cada barra muestra cuántos llegaron a la etapa. El porcentaje compara con quienes llegaron a la etapa anterior.",
  hr_f_inscritos: "Inscritos", hr_f_triados: "Contestaron la llamada", hr_f_qualificados: "Calificados (STRONG o GOOD)",
  hr_f_testes: "Pruebas completadas", hr_f_entrevista_marcada: "Entrevista agendada", hr_f_entrevista_realizada: "Entrevista realizada",
  hr_f_proposta: "Oferta", hr_f_contratados: "Contratados",
  hr_conv: "{p} de la etapa anterior", hr_reprovados: "Rechazados en el período: {n}",
  hr_fontes: "Origen de los candidatos", hr_fontes_desc: "De dónde vinieron las solicitudes y cuántas terminaron en contratación.",
  hr_src_indeed: "Indeed", hr_src_facebook: "Facebook", hr_src_notion: "Notion", hr_src_csv: "Planilla (CSV)",
  hr_src_indicacao: "Referido", hr_src_site: "Sitio web",
  hr_c_fonte: "Origen", hr_c_inscritos: "Inscritos", hr_c_qualificados: "Calificados", hr_c_contratados: "Contratados",
  hr_c_qualif_pct: "% calificados", hr_c_conv: "Conversión", hr_c_vaga: "Vacante", hr_c_cargo: "Cargo",
  hr_c_triados: "Contestaron", hr_c_entrevistas: "Entrevistas", hr_c_reprovados: "Rechazados",
  hr_c_tempo: "Mediana (días)", hr_c_custo: "Costo de voz", hr_c_status: "Estado",
  hr_csv: "Exportar CSV", hr_csv_fontes: "origen-candidatos", hr_csv_vagas: "contratacion-por-vacante",
  hr_tempos: "Tiempos", hr_t_contratar: "De la solicitud a la contratación", hr_t_ligacao: "De la solicitud a la primera llamada",
  hr_t_entrevista: "De la llamada a la entrevista", hr_t_mediana: "mediana", hr_t_media: "promedio {v}",
  hr_t_base: "base: {n}", hr_dias: "{n} días", hr_dia: "{n} día", hr_horas: "{n} h",
  hr_custo: "Costo de la evaluación por voz", hr_custo_desc: "Llamadas hechas en el período. Estimación: minutos x {c} por minuto (voz + telefonía).",
  hr_c_ligacoes: "Llamadas", hr_c_minutos: "Minutos", hr_c_total: "Costo estimado", hr_c_por_qualif: "Por calificado", hr_c_por_contr: "Por contratación",
  hr_tendencia: "Tendencia semanal", hr_tend_inscritos: "Solicitudes", hr_tend_contratados: "Contrataciones",
  hr_tend_semana: "Semana del {d}",
  hr_vagas: "Por vacante", hr_cargos: "Por cargo",
  hr_encerramentos: "Motivos de cierre", hr_enc_desc: "Por qué las solicitudes del período salieron del proceso.",
  hr_e_numero_errado: "Número equivocado", hr_e_sem_interesse: "Sin interés", hr_e_nao_ligar: "Pidió que no lo llamen",
  hr_e_nao_qualificado: "No calificado en la llamada", hr_e_sem_resposta: "Sin respuesta (intentos agotados)",
  hr_e_reprovacao_manual: "Rechazado por un gerente", hr_motivos: "Motivos indicados por los gerentes", hr_sem_motivo: "(sin motivo)",
  hr_vazio: "No hay solicitudes en este período.", hr_nada: "Nada que mostrar.",
});

const HR_ESTADO = { periodo: "30", de: "", ate: "", vaga_id: "", cargo_id: "" };

function hrIsoLocal(d) {
  const p = (n) => String(n).padStart(2, "0");
  return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
}

function hrIntervalo() {
  const hoje = new Date();
  if (HR_ESTADO.periodo === "custom" && HR_ESTADO.de && HR_ESTADO.ate) return { de: HR_ESTADO.de, ate: HR_ESTADO.ate };
  if (HR_ESTADO.periodo === "ano") return { de: hoje.getFullYear() + "-01-01", ate: hrIsoLocal(hoje) };
  const dias = HR_ESTADO.periodo === "90" ? 89 : 29;
  const de = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() - dias);
  return { de: hrIsoLocal(de), ate: hrIsoLocal(hoje) };
}

function hrPct(v) {
  return v == null ? "…" : fmtNum(v, 1) + "%";
}

function hrDinheiro(v) {
  if (v == null) return "…";
  const loc = typeof localeGestor === "function" ? localeGestor() : "pt-BR";
  try {
    return Number(v).toLocaleString(loc, { style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 2 });
  } catch (e) {
    return "US$ " + fmtNum(v, 2);
  }
}

function hrDias(v) {
  if (v == null) return "…";
  return tg(Number(v) === 1 ? "hr_dia" : "hr_dias", { n: fmtNum(v, 1) });
}

function hrHoras(v) {
  return v == null ? "…" : tg("hr_horas", { n: fmtNum(v, 1) });
}

function hrDataCurta(iso) {
  const d = typeof lerDataServidor === "function" ? lerDataServidor(iso) : null;
  if (!d) return fmtData(iso);
  const loc = typeof localeGestor === "function" ? localeGestor() : "pt-BR";
  return d.toLocaleDateString(loc, { day: "2-digit", month: "2-digit" });
}

function hrEstilo() {
  if (document.getElementById("hr-estilo")) return;
  const s = document.createElement("style");
  s.id = "hr-estilo";
  s.textContent = `
    .hr-filtros { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; margin-top: 12px; }
    .hr-filtros label { display: flex; flex-direction: column; gap: 4px; font-size: .78rem; color: var(--text-2); min-width: 150px; flex: 1 1 150px; }
    .hr-filtros select, .hr-filtros input { margin: 0; }
    .hr-funil { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
    .hr-etapa { display: grid; grid-template-columns: minmax(120px, 220px) 1fr 64px; gap: 12px; align-items: center; }
    .hr-etapa .rot { font-size: .85rem; color: var(--text-2); }
    .hr-etapa .rot small { display: block; font-size: .72rem; color: var(--muted); }
    .hr-trilha { background: var(--surface-2); height: 22px; border-radius: 6px; overflow: hidden; }
    .hr-trilha div { height: 100%; background: var(--accent-grad); border-radius: 6px; min-width: 2px; transition: width .4s ease; }
    .hr-trilha div.ok { background: var(--ok); }
    .hr-etapa .n { text-align: right; font-weight: 520; font-family: var(--font-display); }
    .hr-tend { display: flex; align-items: flex-end; gap: 6px; height: 160px; overflow-x: auto; padding-top: 8px; }
    .hr-sem { flex: 1 0 28px; display: flex; flex-direction: column; align-items: center; gap: 4px; height: 100%; justify-content: flex-end; }
    .hr-sem .cols { display: flex; align-items: flex-end; gap: 2px; height: 120px; width: 100%; justify-content: center; }
    .hr-sem .cols div { width: 45%; max-width: 14px; border-radius: 3px 3px 0 0; background: var(--accent-grad); min-height: 1px; }
    .hr-sem .cols div.ok { background: var(--ok); }
    .hr-sem span { font-size: .66rem; color: var(--muted); white-space: nowrap; }
    .hr-legenda { display: flex; gap: 16px; font-size: .78rem; color: var(--text-2); margin-top: 8px; }
    .hr-legenda i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; background: var(--accent-grad); vertical-align: middle; }
    .hr-legenda i.ok { background: var(--ok); }
    .hr-sub { font-size: .78rem; color: var(--muted); margin-top: 4px; }
    .hr-cab { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
    @media (max-width: 600px) { .hr-etapa { grid-template-columns: 1fr 48px; } .hr-etapa .hr-trilha { grid-column: 1 / -1; grid-row: 2; } }
  `;
  document.head.appendChild(s);
}

function hrCsv(nome, cabecalho, linhas) {
  const celula = (v) => {
    const s = v == null ? "" : String(v);
    return /[";\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const csv = "\uFEFF" + [cabecalho].concat(linhas).map((l) => l.map(celula).join(";")).join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  a.download = nome + ".csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function hrNumCsv(v, casas) {
  return v == null ? "" : fmtNum(v, casas);
}

async function relatoriosContratacao(el) {
  if (!el) return;
  hrEstilo();
  const intervalo = hrIntervalo();
  const qs = new URLSearchParams({ de: intervalo.de, ate: intervalo.ate });
  if (HR_ESTADO.vaga_id) qs.set("vaga_id", HR_ESTADO.vaga_id);
  if (HR_ESTADO.cargo_id) qs.set("cargo_id", HR_ESTADO.cargo_id);
  if (!el.innerHTML) el.innerHTML = `<div class="card"><p class="desc">${tg("hr_carregando")}</p></div>`;
  let r;
  try {
    r = await api("/api/gestor/relatorios/contratacao?" + qs.toString());
  } catch (e) {
    el.innerHTML = `<div class="card"><h2 style="font-size:1.05rem">${tg("hr_titulo")}</h2>
      <p class="desc">${esc(tg("hr_erro", { e: e.message }))}</p></div>`;
    return;
  }
  hrDesenhar(el, r, intervalo);
}

function hrDesenhar(el, r, intervalo) {
  const k = r.kpis;
  const opVaga = (v) => `<option value="${v.id}" ${String(v.id) === String(HR_ESTADO.vaga_id) ? "selected" : ""}>${esc(v.titulo)}</option>`;
  const opCargo = (c) => `<option value="${c.id}" ${String(c.id) === String(HR_ESTADO.cargo_id) ? "selected" : ""}>${esc(c.nome)}</option>`;
  const vagas = r.opcoes.vagas.filter((v) => !HR_ESTADO.cargo_id || String(v.cargo_id) === String(HR_ESTADO.cargo_id));
  const custom = HR_ESTADO.periodo === "custom";

  const filtros = `
    <div class="hr-filtros">
      <label>${tg("hr_periodo")}
        <select id="hr-periodo">
          ${[["30", "hr_p30"], ["90", "hr_p90"], ["ano", "hr_pano"], ["custom", "hr_pcustom"]].map(([v, c]) =>
            `<option value="${v}" ${HR_ESTADO.periodo === v ? "selected" : ""}>${tg(c)}</option>`).join("")}
        </select></label>
      ${custom ? `
      <label>${tg("hr_de")}<input type="date" id="hr-de" value="${esc(intervalo.de)}" max="${esc(intervalo.ate)}"></label>
      <label>${tg("hr_ate")}<input type="date" id="hr-ate" value="${esc(intervalo.ate)}"></label>
      <button class="btn secondary small" id="hr-aplicar" type="button">${tg("hr_aplicar")}</button>` : ""}
      <label>${tg("hr_cargo")}
        <select id="hr-cargo"><option value="">${tg("hr_todos")}</option>${r.opcoes.cargos.map(opCargo).join("")}</select></label>
      <label>${tg("hr_vaga")}
        <select id="hr-vaga"><option value="">${tg("hr_todas")}</option>${vagas.map(opVaga).join("")}</select></label>
    </div>
    <p class="hr-sub">${esc(fmtData(r.periodo.de))} - ${esc(fmtData(r.periodo.ate))}</p>`;

  const tile = (num, rot, sub) => `<div class="metrica"><div class="num">${num}</div><div class="rot">${rot}</div>${sub ? `<div class="hr-sub">${sub}</div>` : ""}</div>`;
  const kpis = `
    <div class="metricas">
      ${tile(fmtNum(k.inscritos), tg("hr_k_inscritos"))}
      ${tile(fmtNum(k.qualificados), tg("hr_k_qualificados"), k.taxa_qualificacao_pct != null ? tg("hr_k_de", { p: hrPct(k.taxa_qualificacao_pct) }) : "")}
      ${tile(fmtNum(k.entrevistas), tg("hr_k_entrevistas"))}
      ${tile(fmtNum(k.contratados), tg("hr_k_contratados"), k.taxa_contratacao_pct != null ? tg("hr_k_de", { p: hrPct(k.taxa_contratacao_pct) }) : "")}
      ${tile(hrDias(k.mediana_dias_contratacao), tg("hr_k_tempo"))}
      ${tile(hrDinheiro(k.custo_total), tg("hr_k_custo"))}
    </div>`;

  if (!k.inscritos) {
    el.innerHTML = `<div class="card"><h2 style="font-size:1.05rem">${tg("hr_titulo")}</h2>
      <p class="desc">${tg("hr_desc")}</p>${filtros}</div>
      ${kpis}<div class="card"><p class="desc">${tg("hr_vazio")}</p></div>`;
    hrLigar(el);
    return;
  }

  const topo = Math.max(r.funil[0] ? r.funil[0].n : 0, 1);
  const funil = `
    <div class="card">
      <h2 style="font-size:1.05rem">${tg("hr_funil")}</h2>
      <p class="desc">${tg("hr_funil_desc")}</p>
      <div class="hr-funil">
        ${r.funil.map((f) => `
          <div class="hr-etapa">
            <div class="rot">${tg("hr_f_" + f.etapa)}${f.conversao_pct != null ? `<small>${tg("hr_conv", { p: hrPct(f.conversao_pct) })}</small>` : ""}</div>
            <div class="hr-trilha" title="${esc(hrPct(f.do_total_pct))}"><div class="${f.etapa === "contratados" ? "ok" : ""}" style="width:${Math.round(100 * f.n / topo)}%"></div></div>
            <div class="n">${fmtNum(f.n)}</div>
          </div>`).join("")}
      </div>
      <p class="hr-sub" style="margin-top:12px">${tg("hr_reprovados", { n: fmtNum(r.reprovados) })}</p>
    </div>`;

  const fontes = `
    <div class="card">
      <div class="hr-cab"><h2 style="font-size:1.05rem;margin:0">${tg("hr_fontes")}</h2>
        <button class="btn secondary small" id="hr-csv-fontes" type="button">${tg("hr_csv")}</button></div>
      <p class="desc">${tg("hr_fontes_desc")}</p>
      <div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>${tg("hr_c_fonte")}</th><th>${tg("hr_c_inscritos")}</th><th>${tg("hr_c_qualificados")}</th>
          <th>${tg("hr_c_qualif_pct")}</th><th>${tg("hr_c_contratados")}</th><th>${tg("hr_c_conv")}</th></tr></thead>
        <tbody>${r.fontes.map((f) => `<tr><td><strong>${tg("hr_src_" + f.fonte)}</strong></td><td>${fmtNum(f.inscritos)}</td>
          <td>${fmtNum(f.qualificados)}</td><td>${hrPct(f.qualificacao_pct)}</td><td>${fmtNum(f.contratados)}</td>
          <td>${hrPct(f.conversao_pct)}</td></tr>`).join("")}</tbody>
      </table></div>
    </div>`;

  const t = r.tempos;
  const tempoTile = (rot, bloco, fmt) => tile(fmt(bloco.mediana), rot,
    bloco.n ? tg("hr_t_mediana") + ", " + tg("hr_t_media", { v: fmt(bloco.media) }) + ", " + tg("hr_t_base", { n: fmtNum(bloco.n) }) : "");
  const tempos = `
    <div class="card"><h2 style="font-size:1.05rem">${tg("hr_tempos")}</h2>
      <div class="metricas" style="margin-bottom:0">
        ${tempoTile(tg("hr_t_contratar"), t.contratacao_dias, hrDias)}
        ${tempoTile(tg("hr_t_ligacao"), t.primeira_ligacao_horas, hrHoras)}
        ${tempoTile(tg("hr_t_entrevista"), t.ligacao_entrevista_dias, hrDias)}
      </div></div>`;

  const c = r.custo_voz;
  const custo = `
    <div class="card"><h2 style="font-size:1.05rem">${tg("hr_custo")}</h2>
      <p class="desc">${tg("hr_custo_desc", { c: esc(hrDinheiroMinuto(c.custo_minuto)) })}</p>
      <div class="metricas" style="margin-bottom:0">
        ${tile(fmtNum(c.ligacoes), tg("hr_c_ligacoes"))}
        ${tile(fmtNum(c.minutos), tg("hr_c_minutos"))}
        ${tile(hrDinheiro(c.custo_total), tg("hr_c_total"))}
        ${tile(hrDinheiro(c.por_qualificado), tg("hr_c_por_qualif"))}
        ${tile(hrDinheiro(c.por_contratacao), tg("hr_c_por_contr"))}
      </div></div>`;

  const maxTend = Math.max(1, ...r.tendencia.map((w) => Math.max(w.inscritos, w.contratados)));
  const tendencia = `
    <div class="card"><h2 style="font-size:1.05rem">${tg("hr_tendencia")}</h2>
      <div class="hr-tend">
        ${r.tendencia.map((w) => {
          const dica = tg("hr_tend_semana", { d: fmtData(w.inicio) }) + ": " + tg("hr_tend_inscritos") + " " + fmtNum(w.inscritos)
            + ", " + tg("hr_tend_contratados") + " " + fmtNum(w.contratados);
          return `<div class="hr-sem" title="${esc(dica)}">
            <div class="cols"><div style="height:${Math.round(100 * w.inscritos / maxTend)}%"></div>
              <div class="ok" style="height:${Math.round(100 * w.contratados / maxTend)}%"></div></div>
            <span>${esc(hrDataCurta(w.inicio))}</span></div>`;
        }).join("")}
      </div>
      <div class="hr-legenda"><span><i></i>${tg("hr_tend_inscritos")}</span><span><i class="ok"></i>${tg("hr_tend_contratados")}</span></div>
    </div>`;

  const linhaTabela = (l, primeiro) => `<tr>${primeiro}<td>${fmtNum(l.inscritos)}</td><td>${fmtNum(l.triados)}</td>
    <td>${fmtNum(l.qualificados)}</td><td>${fmtNum(l.entrevistas)}</td><td>${fmtNum(l.contratados)}</td>
    <td>${fmtNum(l.reprovados)}</td><td>${hrPct(l.conversao_pct)}</td><td>${l.mediana_dias_contratacao != null ? fmtNum(l.mediana_dias_contratacao, 1) : "…"}</td>
    <td>${hrDinheiro(l.custo_voz)}</td></tr>`;
  const colunas = `<th>${tg("hr_c_inscritos")}</th><th>${tg("hr_c_triados")}</th><th>${tg("hr_c_qualificados")}</th>
    <th>${tg("hr_c_entrevistas")}</th><th>${tg("hr_c_contratados")}</th><th>${tg("hr_c_reprovados")}</th>
    <th>${tg("hr_c_conv")}</th><th>${tg("hr_c_tempo")}</th><th>${tg("hr_c_custo")}</th>`;
  const tabelas = `
    <div class="card">
      <div class="hr-cab"><h2 style="font-size:1.05rem;margin:0">${tg("hr_vagas")}</h2>
        <button class="btn secondary small" id="hr-csv-vagas" type="button">${tg("hr_csv")}</button></div>
      <div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>${tg("hr_c_vaga")}</th><th>${tg("hr_c_cargo")}</th>${colunas}</tr></thead>
        <tbody>${r.por_vaga.map((v) => linhaTabela(v, `<td><strong>${esc(v.titulo)}</strong></td><td>${esc(v.cargo)}</td>`)).join("")}</tbody>
      </table></div>
    </div>
    <div class="card">
      <h2 style="font-size:1.05rem">${tg("hr_cargos")}</h2>
      <div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>${tg("hr_c_cargo")}</th>${colunas}</tr></thead>
        <tbody>${r.por_cargo.map((c2) => linhaTabela(c2, `<td><strong>${esc(c2.nome)}</strong></td>`)).join("")}</tbody>
      </table></div>
    </div>`;

  const enc = r.encerramentos;
  const chavesEnc = Object.keys(enc).filter((x) => enc[x] > 0);
  const maxEnc = Math.max(1, ...chavesEnc.map((x) => enc[x]));
  const encerramentos = `
    <div class="card"><h2 style="font-size:1.05rem">${tg("hr_encerramentos")}</h2>
      <p class="desc">${tg("hr_enc_desc")}</p>
      ${chavesEnc.length ? `<div class="hr-funil">${chavesEnc.sort((a, b) => enc[b] - enc[a]).map((x) => `
        <div class="hr-etapa"><div class="rot">${tg("hr_e_" + x)}</div>
          <div class="hr-trilha"><div style="width:${Math.round(100 * enc[x] / maxEnc)}%"></div></div>
          <div class="n">${fmtNum(enc[x])}</div></div>`).join("")}</div>` : `<p class="desc">${tg("hr_nada")}</p>`}
      ${r.motivos_manuais.length ? `<h3 style="margin-top:16px">${tg("hr_motivos")}</h3>
        <ul class="lista-simples">${r.motivos_manuais.map((m) => `<li>${esc(m.motivo || tg("hr_sem_motivo"))}: <strong>${fmtNum(m.n)}</strong></li>`).join("")}</ul>` : ""}
    </div>`;

  el.innerHTML = `
    <div class="card"><h2 style="font-size:1.05rem">${tg("hr_titulo")}</h2>
      <p class="desc">${tg("hr_desc")}</p>${filtros}</div>
    ${kpis}${funil}${fontes}${tempos}${custo}${tendencia}${tabelas}${encerramentos}`;
  hrLigar(el, r);
}

function hrDinheiroMinuto(v) {
  if (v == null) return "…";
  const loc = typeof localeGestor === "function" ? localeGestor() : "pt-BR";
  try {
    return Number(v).toLocaleString(loc, { style: "currency", currency: "USD", minimumFractionDigits: 3, maximumFractionDigits: 4 });
  } catch (e) {
    return "US$ " + fmtNum(v, 3);
  }
}

function hrLigar(el, r) {
  const q = (id) => el.querySelector("#" + id);
  const recarregar = () => relatoriosContratacao(el);
  if (q("hr-periodo")) q("hr-periodo").onchange = (ev) => {
    HR_ESTADO.periodo = ev.target.value;
    if (HR_ESTADO.periodo === "custom") {
      const atual = hrIntervalo();
      if (!HR_ESTADO.de) HR_ESTADO.de = r ? r.periodo.de : atual.de;
      if (!HR_ESTADO.ate) HR_ESTADO.ate = r ? r.periodo.ate : atual.ate;
    }
    recarregar();
  };
  if (q("hr-aplicar")) q("hr-aplicar").onclick = () => {
    const de = q("hr-de").value, ate = q("hr-ate").value;
    if (!de || !ate) return;
    HR_ESTADO.de = de <= ate ? de : ate;
    HR_ESTADO.ate = de <= ate ? ate : de;
    recarregar();
  };
  if (q("hr-cargo")) q("hr-cargo").onchange = (ev) => {
    HR_ESTADO.cargo_id = ev.target.value;
    HR_ESTADO.vaga_id = "";
    recarregar();
  };
  if (q("hr-vaga")) q("hr-vaga").onchange = (ev) => {
    HR_ESTADO.vaga_id = ev.target.value;
    recarregar();
  };
  if (!r) return;
  const sufixo = "_" + r.periodo.de + "_" + r.periodo.ate;
  if (q("hr-csv-fontes")) q("hr-csv-fontes").onclick = () => hrCsv(tg("hr_csv_fontes") + sufixo,
    [tg("hr_c_fonte"), tg("hr_c_inscritos"), tg("hr_c_qualificados"), tg("hr_c_qualif_pct"), tg("hr_c_contratados"), tg("hr_c_conv")],
    r.fontes.map((f) => [tg("hr_src_" + f.fonte), f.inscritos, f.qualificados, hrNumCsv(f.qualificacao_pct, 1),
      f.contratados, hrNumCsv(f.conversao_pct, 1)]));
  if (q("hr-csv-vagas")) q("hr-csv-vagas").onclick = () => hrCsv(tg("hr_csv_vagas") + sufixo,
    [tg("hr_c_vaga"), tg("hr_c_cargo"), tg("hr_c_inscritos"), tg("hr_c_triados"), tg("hr_c_qualificados"),
      tg("hr_c_entrevistas"), tg("hr_c_contratados"), tg("hr_c_reprovados"), tg("hr_c_conv"), tg("hr_c_tempo"), tg("hr_c_custo")],
    r.por_vaga.map((v) => [v.titulo, v.cargo, v.inscritos, v.triados, v.qualificados, v.entrevistas, v.contratados,
      v.reprovados, hrNumCsv(v.conversao_pct, 1), hrNumCsv(v.mediana_dias_contratacao, 1), hrNumCsv(v.custo_voz, 2)]));
}
