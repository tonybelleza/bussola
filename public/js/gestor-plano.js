/* =====================================================================
   Plano e uso (planos.py): cartão em Configurações e aviso no topo do
   painel quando a empresa está perto ou acima do limite de minutos de
   voz, ou quando o teste grátis está terminando. O cartão também mostra
   gestores ativos e vagas ativas contra o limite do plano.
   Ganchos no gestor.js: secaoPlano(el) e planoBanner(app).
   Textos: tp(chave) em pt, en e es, no idioma do painel (idiomaGestor).
   ===================================================================== */

const I18N_PLANO = {
  pt: {
    titulo: "Plano e uso",
    plano: "Plano",
    sem_plano: "Plano personalizado",
    status_teste: "Teste grátis",
    status_ativa: "Ativa",
    teste_ate: "Teste grátis até {data} ({n} dia(s) restante(s))",
    teste_terminou: "O teste grátis terminou em {data}",
    renova_em: "Próxima renovação: {data}",
    ciclo_mensal: "Cobrança mensal",
    ciclo_anual: "Cobrança anual",
    minutos_mes: "Minutos de voz neste mês",
    de_limite: "{usados} de {limite} min",
    ilimitado: "{usados} min (sem limite)",
    extras: "Inclui {n} minutos extras",
    st_ok: "Dentro do limite",
    st_near: "Perto do limite",
    st_over: "Limite atingido",
    excedente_on: "Minutos além do limite são cobrados como extra.",
    excedente_off: "Ao atingir o limite, as ligações automáticas param até o próximo mês.",
    pagamento_falhou: "O último pagamento foi recusado. Atualize a forma de pagamento.",
    mudar_plano: "Mudar para {plano}",
    escolher_plano: "Escolher plano",
    gerenciar: "Gerenciar cobrança",
    so_admin: "Só o administrador da empresa altera o plano.",
    banner_near: "Sua empresa já usou {pct}% dos minutos de voz deste mês ({usados} de {limite}).",
    banner_over: "Os minutos de voz deste mês acabaram ({usados} de {limite}). As ligações estão pausadas até o próximo mês.",
    banner_teste: "Seu teste grátis termina em {n} dia(s).",
    banner_ok: "Assinatura confirmada. Obrigado!",
    ver_planos: "Ver planos",
    fechar: "Fechar",
    plan_limit: "Os minutos de voz do plano acabaram neste mês.",
    gestores_titulo: "Gestores ativos",
    gestores_uso: "{usados} de {maximo} gestores",
    gestores_ilimitado: "{usados} gestores (sem limite)",
    vagas_titulo: "Vagas ativas",
    vagas_uso: "{usados} de {maximo} vagas ativas",
    vagas_ilimitado: "{usados} vagas ativas (sem limite)",
    limite_atingido: "Limite do plano atingido",
  },
  en: {
    titulo: "Plan and usage",
    plano: "Plan",
    sem_plano: "Custom plan",
    status_teste: "Free trial",
    status_ativa: "Active",
    teste_ate: "Free trial until {data} ({n} day(s) left)",
    teste_terminou: "The free trial ended on {data}",
    renova_em: "Next renewal: {data}",
    ciclo_mensal: "Billed monthly",
    ciclo_anual: "Billed yearly",
    minutos_mes: "Voice minutes this month",
    de_limite: "{usados} of {limite} min",
    ilimitado: "{usados} min (no limit)",
    extras: "Includes {n} extra minutes",
    st_ok: "Within the limit",
    st_near: "Close to the limit",
    st_over: "Limit reached",
    excedente_on: "Minutes over the limit are billed as extra minutes.",
    excedente_off: "Once the limit is reached, automatic calls stop until next month.",
    pagamento_falhou: "The last payment was declined. Please update your payment method.",
    mudar_plano: "Switch to {plano}",
    escolher_plano: "Choose a plan",
    gerenciar: "Manage billing",
    so_admin: "Only the company admin can change the plan.",
    banner_near: "Your company has used {pct}% of this month's voice minutes ({usados} of {limite}).",
    banner_over: "This month's voice minutes are used up ({usados} of {limite}). Calls are paused until next month.",
    banner_teste: "Your free trial ends in {n} day(s).",
    banner_ok: "Subscription confirmed. Thank you!",
    ver_planos: "See plans",
    fechar: "Close",
    plan_limit: "Your plan's voice minutes for this month are used up.",
    gestores_titulo: "Active managers",
    gestores_uso: "{usados} of {maximo} managers",
    gestores_ilimitado: "{usados} managers (no limit)",
    vagas_titulo: "Active jobs",
    vagas_uso: "{usados} of {maximo} active jobs",
    vagas_ilimitado: "{usados} active jobs (no limit)",
    limite_atingido: "Plan limit reached",
  },
  es: {
    titulo: "Plan y uso",
    plano: "Plan",
    sem_plano: "Plan personalizado",
    status_teste: "Prueba gratis",
    status_ativa: "Activa",
    teste_ate: "Prueba gratis hasta el {data} ({n} día(s) restante(s))",
    teste_terminou: "La prueba gratis terminó el {data}",
    renova_em: "Próxima renovación: {data}",
    ciclo_mensal: "Facturación mensual",
    ciclo_anual: "Facturación anual",
    minutos_mes: "Minutos de voz este mes",
    de_limite: "{usados} de {limite} min",
    ilimitado: "{usados} min (sin límite)",
    extras: "Incluye {n} minutos extra",
    st_ok: "Dentro del límite",
    st_near: "Cerca del límite",
    st_over: "Límite alcanzado",
    excedente_on: "Los minutos por encima del límite se cobran como extra.",
    excedente_off: "Al alcanzar el límite, las llamadas automáticas se detienen hasta el próximo mes.",
    pagamento_falhou: "El último pago fue rechazado. Actualiza tu forma de pago.",
    mudar_plano: "Cambiar a {plano}",
    escolher_plano: "Elegir plan",
    gerenciar: "Administrar facturación",
    so_admin: "Solo el administrador de la empresa cambia el plan.",
    banner_near: "Tu empresa ya usó el {pct}% de los minutos de voz de este mes ({usados} de {limite}).",
    banner_over: "Se agotaron los minutos de voz de este mes ({usados} de {limite}). Las llamadas están en pausa hasta el próximo mes.",
    banner_teste: "Tu prueba gratis termina en {n} día(s).",
    banner_ok: "Suscripción confirmada. ¡Gracias!",
    ver_planos: "Ver planes",
    fechar: "Cerrar",
    plan_limit: "Se agotaron los minutos de voz de tu plan este mes.",
    gestores_titulo: "Gerentes activos",
    gestores_uso: "{usados} de {maximo} gerentes",
    gestores_ilimitado: "{usados} gerentes (sin límite)",
    vagas_titulo: "Vacantes activas",
    vagas_uso: "{usados} de {maximo} vacantes activas",
    vagas_ilimitado: "{usados} vacantes activas (sin límite)",
    limite_atingido: "Límite del plan alcanzado",
  },
};

function tp(chave, vars) {
  const lang = (typeof idiomaGestor !== "undefined" && I18N_PLANO[idiomaGestor]) ? idiomaGestor : "pt";
  let s = I18N_PLANO[lang][chave];
  if (s === undefined) s = I18N_PLANO.pt[chave];
  if (s === undefined) return chave;
  if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
  return s;
}

// a ligação manual recusada pelo limite do plano mostra uma mensagem clara (gestor-voz.js)
if (typeof VOZ_ERROS !== "undefined") {
  ["pt", "en", "es"].forEach((l) => { if (VOZ_ERROS[l]) VOZ_ERROS[l].plan_limit = I18N_PLANO[l].plan_limit; });
}

let planoCache = null;
let planoCacheEm = 0;
let planoBannerFechado = false;

async function planoCarregar(forcar) {
  if (!forcar && planoCache && Date.now() - planoCacheEm < 60000) return planoCache;
  planoCache = await api("/api/gestor/plano");
  planoCacheEm = Date.now();
  return planoCache;
}

function planoNum(n) {
  return typeof fmtNum === "function" ? fmtNum(n) : String(n);
}

function planoData(d) {
  return typeof fmtData === "function" ? fmtData(d) : String(d || "");
}

function planoBarra(u) {
  if (u.ilimitado) return "";
  const pct = Math.min(100, Math.round(u.pct || 0));
  const cor = u.status === "over" ? "var(--err)" : u.status === "near" ? "var(--warn)" : "var(--accent-grad)";
  return `<div style="height:10px;border-radius:999px;background:var(--surface-2);overflow:hidden;margin:8px 0 6px">
      <div style="height:100%;width:${pct}%;background:${cor};border-radius:999px"></div></div>`;
}

// linha "x de y gestores" / "x de y vagas ativas" no cartão do plano
function planoLinhaLimite(lim, prefixo) {
  if (!lim) return "";
  const texto = lim.maximo === null || lim.maximo === undefined
    ? tp(prefixo + "_ilimitado", { usados: planoNum(lim.usados) })
    : tp(prefixo + "_uso", { usados: planoNum(lim.usados), maximo: planoNum(lim.maximo) });
  const cheio = lim.maximo !== null && lim.maximo !== undefined && lim.usados >= lim.maximo;
  return `<div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;margin-top:8px">
      <strong>${tp(prefixo + "_titulo")}</strong>
      <span>${esc(texto)}${cheio ? ` <span class="badge warn">${tp("limite_atingido")}</span>` : ""}</span>
    </div>`;
}

async function planoAbrirPortal(botao) {
  botao.disabled = true;
  try {
    const r = await api("/api/gestor/plano/portal");
    if (r.url) location.href = r.url;
  } catch (e) {
    alert(e.message);
  } finally {
    botao.disabled = false;
  }
}

async function secaoPlano(el) {
  if (!el) return;
  let r;
  try {
    r = await planoCarregar(true);
  } catch (e) {
    el.innerHTML = "";
    return;
  }
  const u = r.uso || {};
  const badge = r.status === "teste"
    ? `<span class="badge warn">${tp("status_teste")}</span>`
    : `<span class="badge ok">${tp("status_ativa")}</span>`;
  const stBadge = { ok: "ok", near: "warn", over: "err" }[u.status] || "ok";
  let datas = "";
  if (r.em_teste && r.trial_fim) {
    datas = r.dias_teste >= 0 ? tp("teste_ate", { data: planoData(r.trial_fim), n: planoNum(r.dias_teste) })
      : tp("teste_terminou", { data: planoData(r.trial_fim) });
  } else if (r.renovacao) {
    datas = tp("renova_em", { data: planoData(r.renovacao) });
  }
  const uso = u.ilimitado ? tp("ilimitado", { usados: planoNum(u.minutos) })
    : tp("de_limite", { usados: planoNum(u.minutos), limite: planoNum(u.limite) });
  const acoes = [];
  if (r.admin && r.upgrade_url) {
    const rot = r.plano && r.upgrade_plano && r.upgrade_plano !== r.plano.nome
      ? tp("mudar_plano", { plano: esc(r.upgrade_plano) }) : tp("escolher_plano");
    acoes.push(`<a class="btn small" href="${esc(r.upgrade_url)}">${rot}</a>`);
  }
  if (r.portal_disponivel) acoes.push(`<button class="btn secondary small" id="plano-portal">${tp("gerenciar")}</button>`);
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${typeof icone === "function" ? icone("grafico") : ""}<span>${tp("titulo")}</span></h2>
      <p class="desc">${tp("plano")}: <strong>${esc(r.plano ? r.plano.nome : tp("sem_plano"))}</strong> ${badge}
        ${r.status === "ativa" && r.plano ? " · " + tp(r.ciclo === "anual" ? "ciclo_anual" : "ciclo_mensal") : ""}</p>
      ${datas ? `<p class="desc">${esc(datas)}</p>` : ""}
      ${r.pagamento_status === "falhou" ? `<div class="aviso mb">${tp("pagamento_falhou")}</div>` : ""}
      <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;margin-top:10px">
        <strong>${tp("minutos_mes")}</strong>
        <span>${esc(uso)} <span class="badge ${stBadge}">${tp("st_" + (u.status || "ok"))}</span></span>
      </div>
      ${planoBarra(u)}
      ${u.minutos_extra ? `<p class="desc" style="font-size:.82rem">${tp("extras", { n: planoNum(u.minutos_extra) })}</p>` : ""}
      ${u.ilimitado ? "" : `<p class="desc" style="font-size:.82rem">${tp(u.excedente_permitido ? "excedente_on" : "excedente_off")}</p>`}
      ${planoLinhaLimite(r.gestores, "gestores")}
      ${planoLinhaLimite(r.vagas, "vagas")}
      ${acoes.length ? `<div class="linha-acoes" style="margin-top:12px">${acoes.join("")}</div>`
        : (r.admin ? "" : `<p class="desc" style="font-size:.82rem">${tp("so_admin")}</p>`)}
    </div>`;
  const b = el.querySelector("#plano-portal");
  if (b) b.addEventListener("click", () => planoAbrirPortal(b));
}

async function planoBanner(raiz) {
  if (!raiz || planoBannerFechado) return;
  let r;
  try {
    r = await planoCarregar(false);
  } catch (e) {
    return;
  }
  const antigo = document.getElementById("plano-banner");
  if (antigo) antigo.remove();
  const u = r.uso || {};
  let texto = "";
  let cor = "aviso";
  const params = new URLSearchParams(location.search);
  if (params.get("assinatura") === "ok") {
    texto = tp("banner_ok");
    cor = "ok";
    history.replaceState(null, "", location.pathname);
  } else if (!u.ilimitado && u.status === "over") {
    texto = tp("banner_over", { usados: planoNum(u.minutos), limite: planoNum(u.limite) });
  } else if (!u.ilimitado && u.status === "near") {
    texto = tp("banner_near", { pct: planoNum(Math.round(u.pct)), usados: planoNum(u.minutos), limite: planoNum(u.limite) });
  } else if (r.em_teste && r.dias_teste !== null && r.dias_teste <= 3) {
    texto = tp("banner_teste", { n: planoNum(Math.max(r.dias_teste, 0)) });
  }
  if (!texto) return;
  const div = document.createElement("div");
  div.id = "plano-banner";
  div.className = "aviso mb";
  if (cor === "ok") div.style.cssText = "background:var(--ok-bg);color:var(--ok);border-color:transparent";
  div.style.display = "flex";
  div.style.gap = "12px";
  div.style.alignItems = "center";
  div.style.flexWrap = "wrap";
  div.innerHTML = `<span style="flex:1;min-width:200px">${esc(texto)}</span>
    ${cor !== "ok" && r.admin && r.upgrade_url ? `<a class="btn small" href="${esc(r.upgrade_url)}">${tp("ver_planos")}</a>` : ""}
    <button class="btn secondary small" type="button">${tp("fechar")}</button>`;
  div.querySelector("button").addEventListener("click", () => { planoBannerFechado = true; div.remove(); });
  raiz.insertBefore(div, raiz.firstChild);
}
