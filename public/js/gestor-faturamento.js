/* =====================================================================
   Meu plano (aba "Plano", só para o administrador da empresa).
   - Plano atual, preço, situação (teste com dias restantes, ativa,
     pagamento recusado, suspensa), uso de minutos de voz do mês,
     histórico dos últimos 6 meses, gestores e vagas ativas.
   - Comparar planos: com Stripe ativo, vai para o checkout
     (POST /api/gestor/plano/checkout); sem Stripe, envia um pedido ao
     dono (POST /api/gestor/assistente/pedido).
   - Pedido de cancelamento com motivo e "Gerenciar cobrança e faturas"
     (GET /api/gestor/plano/portal) quando houver cliente no Stripe.
   Ganchos no gestor.js: fatAbaVisivel(), fatRotuloAba(), abaFaturamento(el).
   Textos em pt, en e es (tg do i18n-gestor.js, chaves "fa_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  fa_aba: "Plano",
  fa_titulo: "Meu plano",
  fa_sem_plano: "Plano personalizado",
  fa_por_mes: "{v}/mês",
  fa_por_ano: "{v}/ano",
  fa_ciclo_mensal: "Cobrança mensal",
  fa_ciclo_anual: "Cobrança anual",
  fa_st_teste: "Teste grátis",
  fa_st_ativa: "Ativa",
  fa_st_pagamento_falhou: "Pagamento recusado",
  fa_st_suspensa: "Suspensa",
  fa_st_cancelada: "Cancelada",
  fa_teste_dias: "Teste grátis até {data}: {n} dia(s) restante(s).",
  fa_teste_fim: "O teste grátis terminou em {data}.",
  fa_renova: "Próxima renovação: {data}.",
  fa_falhou_aviso: "O último pagamento foi recusado. Atualize a forma de pagamento para não perder o acesso.",
  fa_suspensa_aviso: "A conta está suspensa. Escolha um plano para reativar.",
  fa_cancelada_aviso: "A assinatura foi cancelada.",
  fa_portal: "Gerenciar cobrança e faturas",
  fa_uso_titulo: "Uso neste mês",
  fa_minutos: "Minutos de voz",
  fa_de: "{u} de {l}",
  fa_sem_limite: "{u} (sem limite)",
  fa_gestores: "Gestores",
  fa_vagas: "Vagas ativas",
  fa_limite_atingido: "Limite atingido",
  fa_hist_titulo: "Minutos de voz nos últimos 6 meses",
  fa_hist_limite: "Limite atual do plano: {l} min por mês",
  fa_min: "{n} min",
  fa_comparar: "Comparar planos",
  fa_mensal: "Mensal",
  fa_anual: "Anual",
  fa_min_voz: "{n} minutos de voz por mês",
  fa_sem_voz: "Sem triagem por voz",
  fa_ate_gestores: "Até {n} gestores",
  fa_gestores_ilimitados: "Gestores ilimitados",
  fa_atual: "Plano atual",
  fa_upgrade: "Fazer upgrade",
  fa_trocar: "Trocar de plano",
  fa_escolher: "Escolher este plano",
  fa_pedido_titulo: "Pedir troca para {plano}",
  fa_pedido_desc: "Vamos falar com você por e-mail para confirmar a troca e o valor.",
  fa_mensagem: "Mensagem (opcional)",
  fa_enviar: "Enviar pedido",
  fa_cancelar_titulo: "Cancelar assinatura",
  fa_cancelar_desc: "Sentiremos sua falta. Conte o motivo para a gente melhorar.",
  fa_cancelar_btn: "Pedir cancelamento",
  fa_motivo: "Motivo",
  fa_m_caro: "O preço está alto",
  fa_m_pouco_uso: "Usamos pouco",
  fa_m_faltou_recurso: "Faltou um recurso",
  fa_m_outro_sistema: "Vamos usar outro sistema",
  fa_m_temporario: "É uma pausa temporária",
  fa_m_outro: "Outro motivo",
  fa_enviado: "Pedido enviado. Vamos responder por e-mail em breve.",
  fa_pedidos: "Pedidos recentes",
  fa_ped_trocar_plano: "Troca para {plano}",
  fa_ped_cancelar: "Cancelamento",
  fa_fechar: "Fechar",
  fa_so_admin: "Só o administrador da empresa vê o plano e a cobrança.",
});
Object.assign(I18N_GESTOR.en, {
  fa_aba: "Plan",
  fa_titulo: "My plan",
  fa_sem_plano: "Custom plan",
  fa_por_mes: "{v}/month",
  fa_por_ano: "{v}/year",
  fa_ciclo_mensal: "Billed monthly",
  fa_ciclo_anual: "Billed yearly",
  fa_st_teste: "Free trial",
  fa_st_ativa: "Active",
  fa_st_pagamento_falhou: "Payment failed",
  fa_st_suspensa: "Suspended",
  fa_st_cancelada: "Canceled",
  fa_teste_dias: "Free trial until {data}: {n} day(s) left.",
  fa_teste_fim: "The free trial ended on {data}.",
  fa_renova: "Next renewal: {data}.",
  fa_falhou_aviso: "Your last payment was declined. Update your payment method to keep your access.",
  fa_suspensa_aviso: "Your account is suspended. Choose a plan to reactivate it.",
  fa_cancelada_aviso: "Your subscription was canceled.",
  fa_portal: "Manage billing and invoices",
  fa_uso_titulo: "Usage this month",
  fa_minutos: "Voice minutes",
  fa_de: "{u} of {l}",
  fa_sem_limite: "{u} (no limit)",
  fa_gestores: "Managers",
  fa_vagas: "Active jobs",
  fa_limite_atingido: "Limit reached",
  fa_hist_titulo: "Voice minutes over the last 6 months",
  fa_hist_limite: "Current plan limit: {l} min per month",
  fa_min: "{n} min",
  fa_comparar: "Compare plans",
  fa_mensal: "Monthly",
  fa_anual: "Yearly",
  fa_min_voz: "{n} voice minutes per month",
  fa_sem_voz: "No voice screening",
  fa_ate_gestores: "Up to {n} managers",
  fa_gestores_ilimitados: "Unlimited managers",
  fa_atual: "Current plan",
  fa_upgrade: "Upgrade",
  fa_trocar: "Change plan",
  fa_escolher: "Choose this plan",
  fa_pedido_titulo: "Request a switch to {plano}",
  fa_pedido_desc: "We'll reach out by email to confirm the change and the price.",
  fa_mensagem: "Message (optional)",
  fa_enviar: "Send request",
  fa_cancelar_titulo: "Cancel subscription",
  fa_cancelar_desc: "We'd hate to see you go. Tell us why so we can do better.",
  fa_cancelar_btn: "Request cancellation",
  fa_motivo: "Reason",
  fa_m_caro: "It's too expensive",
  fa_m_pouco_uso: "We don't use it enough",
  fa_m_faltou_recurso: "A feature we need is missing",
  fa_m_outro_sistema: "We're switching to another tool",
  fa_m_temporario: "It's a temporary pause",
  fa_m_outro: "Something else",
  fa_enviado: "Request sent. We'll get back to you by email soon.",
  fa_pedidos: "Recent requests",
  fa_ped_trocar_plano: "Switch to {plano}",
  fa_ped_cancelar: "Cancellation",
  fa_fechar: "Close",
  fa_so_admin: "Only the company admin can see the plan and billing.",
});
Object.assign(I18N_GESTOR.es, {
  fa_aba: "Plan",
  fa_titulo: "Mi plan",
  fa_sem_plano: "Plan personalizado",
  fa_por_mes: "{v}/mes",
  fa_por_ano: "{v}/año",
  fa_ciclo_mensal: "Facturación mensual",
  fa_ciclo_anual: "Facturación anual",
  fa_st_teste: "Prueba gratis",
  fa_st_ativa: "Activa",
  fa_st_pagamento_falhou: "Pago rechazado",
  fa_st_suspensa: "Suspendida",
  fa_st_cancelada: "Cancelada",
  fa_teste_dias: "Prueba gratis hasta el {data}: {n} día(s) restante(s).",
  fa_teste_fim: "La prueba gratis terminó el {data}.",
  fa_renova: "Próxima renovación: {data}.",
  fa_falhou_aviso: "Tu último pago fue rechazado. Actualiza tu método de pago para no perder el acceso.",
  fa_suspensa_aviso: "Tu cuenta está suspendida. Elige un plan para reactivarla.",
  fa_cancelada_aviso: "Tu suscripción fue cancelada.",
  fa_portal: "Administrar facturación y facturas",
  fa_uso_titulo: "Uso este mes",
  fa_minutos: "Minutos de voz",
  fa_de: "{u} de {l}",
  fa_sem_limite: "{u} (sin límite)",
  fa_gestores: "Gerentes",
  fa_vagas: "Vacantes activas",
  fa_limite_atingido: "Límite alcanzado",
  fa_hist_titulo: "Minutos de voz en los últimos 6 meses",
  fa_hist_limite: "Límite actual del plan: {l} min por mes",
  fa_min: "{n} min",
  fa_comparar: "Comparar planes",
  fa_mensal: "Mensual",
  fa_anual: "Anual",
  fa_min_voz: "{n} minutos de voz al mes",
  fa_sem_voz: "Sin entrevista por voz",
  fa_ate_gestores: "Hasta {n} gerentes",
  fa_gestores_ilimitados: "Gerentes ilimitados",
  fa_atual: "Plan actual",
  fa_upgrade: "Mejorar plan",
  fa_trocar: "Cambiar de plan",
  fa_escolher: "Elegir este plan",
  fa_pedido_titulo: "Solicitar el cambio a {plano}",
  fa_pedido_desc: "Te contactaremos por correo para confirmar el cambio y el precio.",
  fa_mensagem: "Mensaje (opcional)",
  fa_enviar: "Enviar solicitud",
  fa_cancelar_titulo: "Cancelar suscripción",
  fa_cancelar_desc: "Nos dará pena verte partir. Cuéntanos el motivo para mejorar.",
  fa_cancelar_btn: "Solicitar cancelación",
  fa_motivo: "Motivo",
  fa_m_caro: "El precio es alto",
  fa_m_pouco_uso: "Lo usamos poco",
  fa_m_faltou_recurso: "Falta una función que necesitamos",
  fa_m_outro_sistema: "Vamos a usar otra herramienta",
  fa_m_temporario: "Es una pausa temporal",
  fa_m_outro: "Otro motivo",
  fa_enviado: "Solicitud enviada. Te responderemos por correo pronto.",
  fa_pedidos: "Solicitudes recientes",
  fa_ped_trocar_plano: "Cambio a {plano}",
  fa_ped_cancelar: "Cancelación",
  fa_fechar: "Cerrar",
  fa_so_admin: "Solo el administrador de la empresa ve el plan y la facturación.",
});

let fatCiclo = null;   // ciclo escolhido na comparação (mensal ou anual)
let fatAviso = "";     // mensagem depois de enviar um pedido

function fatAbaVisivel() {
  return typeof infoGestor === "function" && !!infoGestor().admin;
}

function fatRotuloAba() {
  return tg("fa_aba");
}

function fatEsc(v) {
  return typeof esc === "function" ? esc(v) : String(v == null ? "" : v);
}

function fatNum(n) {
  return typeof fmtNum === "function" ? fmtNum(n) : String(n);
}

function fatData(d) {
  return typeof fmtData === "function" ? fmtData(d) : String(d || "");
}

function fatLocale() {
  return typeof localeGestor === "function" ? localeGestor() : "en-US";
}

function fatDinheiro(v) {
  const n = Number(v);
  if (v === null || v === undefined || v === "" || isNaN(n)) return "";
  return n.toLocaleString(fatLocale(), {
    style: "currency", currency: "USD",
    minimumFractionDigits: Number.isInteger(n) ? 0 : 2, maximumFractionDigits: 2,
  });
}

function fatPreco(p, ciclo) {
  if (!p) return "";
  return ciclo === "anual" ? tg("fa_por_ano", { v: fatDinheiro(p.preco_anual) })
    : tg("fa_por_mes", { v: fatDinheiro(p.preco_mensal) });
}

function fatMes(mes) {
  const [a, m] = String(mes || "").split("-").map(Number);
  if (!a || !m) return String(mes || "");
  return new Date(a, m - 1, 15).toLocaleDateString(fatLocale(), { month: "short" });
}

function fatBarra(pct, status) {
  const p = Math.max(0, Math.min(100, Math.round(Number(pct) || 0)));
  const cor = status === "over" ? "var(--err)" : status === "near" ? "var(--warn)" : "var(--accent-grad, var(--ok))";
  return `<div style="height:10px;border-radius:999px;background:var(--surface-2);overflow:hidden;margin:8px 0 6px">
      <div style="height:100%;width:${p}%;background:${cor};border-radius:999px"></div></div>`;
}

function fatLinhaLimite(rotulo, lim) {
  if (!lim) return "";
  const temMax = lim.maximo !== null && lim.maximo !== undefined;
  const texto = temMax ? tg("fa_de", { u: fatNum(lim.usados), l: fatNum(lim.maximo) })
    : tg("fa_sem_limite", { u: fatNum(lim.usados) });
  const cheio = temMax && lim.usados >= lim.maximo;
  const pct = temMax && lim.maximo > 0 ? (100 * lim.usados) / lim.maximo : 0;
  return `<div style="margin-top:14px">
      <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap">
        <strong>${rotulo}</strong>
        <span>${fatEsc(texto)}${cheio ? ` <span class="badge warn">${tg("fa_limite_atingido")}</span>` : ""}</span>
      </div>
      ${temMax ? fatBarra(pct, cheio ? "over" : pct >= 80 ? "near" : "ok") : ""}
    </div>`;
}

function fatHistorico(hist, limite) {
  const lista = hist || [];
  const maior = Math.max(1, limite || 0, ...lista.map((h) => h.minutos || 0));
  const barras = lista.map((h) => {
    const alt = Math.round((100 * (h.minutos || 0)) / maior);
    const acima = limite && h.minutos > limite;
    return `<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;min-width:0">
        <span style="font-size:.78rem" class="desc">${fatNum(h.minutos || 0)}</span>
        <div style="width:100%;max-width:46px;height:120px;display:flex;align-items:flex-end;background:var(--surface-2);border-radius:8px;overflow:hidden">
          <div title="${fatEsc(tg("fa_min", { n: fatNum(h.minutos || 0) }))}" style="width:100%;height:${alt}%;background:${acima ? "var(--err)" : "var(--accent-grad, var(--ok))"}"></div>
        </div>
        <span style="font-size:.78rem;text-transform:capitalize">${fatEsc(fatMes(h.mes))}</span>
      </div>`;
  }).join("");
  return `<div style="display:flex;gap:10px;align-items:flex-end;margin-top:12px">${barras}</div>
    ${limite ? `<p class="desc" style="font-size:.8rem;margin-top:8px">${tg("fa_hist_limite", { l: fatNum(limite) })}</p>` : ""}`;
}

function fatBotaoPlano(p, atual) {
  if (p.atual) return `<button class="btn ghost small block" disabled>${tg("fa_atual")}</button>`;
  let rot = "fa_escolher";
  if (atual) rot = Number(p.preco_mensal || 0) > Number(atual.preco_mensal || 0) ? "fa_upgrade" : "fa_trocar";
  return `<button class="btn ${rot === "fa_upgrade" ? "" : "secondary"} small block" data-fa-plano="${fatEsc(p.codigo)}">${tg(rot)}</button>`;
}

function fatCartaoPlano(p, ciclo, atual) {
  const linhas = [
    p.minutos_voz ? tg("fa_min_voz", { n: fatNum(p.minutos_voz) }) : tg("fa_sem_voz"),
    p.gestores_max === null || p.gestores_max === undefined ? tg("fa_gestores_ilimitados")
      : tg("fa_ate_gestores", { n: fatNum(p.gestores_max) }),
  ];
  const extras = (p.recursos || []).filter((x) => !/\d/.test(x)).slice(0, 4);
  return `<div style="border:1px solid ${p.atual ? "var(--accent, #3B67CA)" : "var(--line, #e4e9f0)"};border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:8px">
      <div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline;flex-wrap:wrap">
        <h3 style="margin:0">${fatEsc(p.nome)}</h3>
        ${p.atual ? `<span class="badge ok">${tg("fa_atual")}</span>` : ""}
      </div>
      <div style="font-size:1.25rem;font-weight:600">${fatEsc(fatPreco(p, ciclo))}</div>
      <p class="desc" style="font-size:.85rem;margin:0">${fatEsc(p.descricao || "")}</p>
      <ul style="margin:4px 0 8px 18px;padding:0;font-size:.85rem">
        ${linhas.concat(extras).map((x) => `<li>${fatEsc(x)}</li>`).join("")}
      </ul>
      <div style="margin-top:auto">${fatBotaoPlano(p, atual)}</div>
    </div>`;
}

function fatModal(titulo, corpo, rotuloBotao, aoEnviar) {
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal" style="max-width:520px">
      <button class="btn ghost small fechar" data-fa-fechar aria-label="${fatEsc(tg("fa_fechar"))}">${typeof icone === "function" ? icone("fechar") : "x"}</button>
      <h2>${fatEsc(titulo)}</h2>
      <div class="mt">${corpo}</div>
      <div class="form-erro" data-fa-erro></div>
      <button class="btn block" data-fa-enviar>${fatEsc(rotuloBotao)}</button>
    </div>`;
  document.body.appendChild(fundo);
  const fechar = () => fundo.remove();
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fechar(); });
  fundo.querySelector("[data-fa-fechar]").addEventListener("click", fechar);
  const botao = fundo.querySelector("[data-fa-enviar]");
  botao.addEventListener("click", async () => {
    botao.disabled = true;
    try {
      await aoEnviar(fundo);
      fechar();
    } catch (e) {
      fundo.querySelector("[data-fa-erro]").textContent = e.message;
      botao.disabled = false;
    }
  });
  return fundo;
}

function fatPedirTroca(el, p, ciclo) {
  fatModal(tg("fa_pedido_titulo", { plano: p.nome }), `
      <p class="desc">${fatEsc(fatPreco(p, ciclo))}. ${tg("fa_pedido_desc")}</p>
      <label class="field">${tg("fa_mensagem")}<textarea data-fa-msg rows="3" maxlength="1000"></textarea></label>`,
  tg("fa_enviar"), async (m) => {
    await api("/api/gestor/assistente/pedido", {
      method: "POST",
      body: { tipo: "trocar_plano", plano: p.codigo, ciclo, mensagem: m.querySelector("[data-fa-msg]").value },
    });
    fatAviso = tg("fa_enviado");
    abaFaturamento(el);
  });
}

function fatPedirCancelamento(el, motivos) {
  fatModal(tg("fa_cancelar_titulo"), `
      <p class="desc">${tg("fa_cancelar_desc")}</p>
      <label class="field">${tg("fa_motivo")}
        <select data-fa-motivo>${(motivos || []).map((m) => `<option value="${fatEsc(m)}">${tg("fa_m_" + m)}</option>`).join("")}</select>
      </label>
      <label class="field">${tg("fa_mensagem")}<textarea data-fa-msg rows="3" maxlength="1000"></textarea></label>`,
  tg("fa_cancelar_btn"), async (m) => {
    await api("/api/gestor/assistente/pedido", {
      method: "POST",
      body: { tipo: "cancelar", motivo: m.querySelector("[data-fa-motivo]").value, mensagem: m.querySelector("[data-fa-msg]").value },
    });
    fatAviso = tg("fa_enviado");
    abaFaturamento(el);
  });
}

async function fatEscolherPlano(el, r, codigo, botao) {
  const p = (r.planos || []).find((x) => x.codigo === codigo);
  if (!p) return;
  const ciclo = fatCiclo || "mensal";
  if (!r.stripe_ativo) {
    fatPedirTroca(el, p, ciclo);
    return;
  }
  botao.disabled = true;
  try {
    const res = await api("/api/gestor/plano/checkout", { method: "POST", body: { plano: codigo, ciclo } });
    if (res.checkout_url) location.href = res.checkout_url;
  } catch (e) {
    alert(e.message);
  } finally {
    botao.disabled = false;
  }
}

async function abaFaturamento(el) {
  if (!el) return;
  if (!fatAbaVisivel()) {
    el.innerHTML = `<div class="card"><p class="desc">${tg("fa_so_admin")}</p></div>`;
    return;
  }
  el.innerHTML = `<div class="card texto-centro"><p>${tg("carregando")}</p></div>`;
  let r;
  try {
    r = await api("/api/gestor/assistente/plano");
  } catch (e) {
    el.innerHTML = `<div class="card"><p class="form-erro">${fatEsc(e.message)}</p></div>`;
    return;
  }
  const info = r.info || {};
  const u = info.uso || {};
  const atual = (r.planos || []).find((p) => p.atual) || null;
  const cicloAtual = info.ciclo === "anual" ? "anual" : "mensal";
  if (!fatCiclo) fatCiclo = cicloAtual;
  const st = r.status_conta || "ativa";
  const corSt = { ativa: "ok", teste: "warn", pagamento_falhou: "err", suspensa: "err", cancelada: "err" }[st] || "neutral";
  let datas = "";
  if (st === "teste" && info.trial_fim) {
    datas = info.dias_teste !== null && info.dias_teste >= 0
      ? tg("fa_teste_dias", { data: fatData(info.trial_fim), n: fatNum(info.dias_teste) })
      : tg("fa_teste_fim", { data: fatData(info.trial_fim) });
  } else if (info.renovacao) {
    datas = tg("fa_renova", { data: fatData(info.renovacao) });
  }
  const aviso = { pagamento_falhou: "fa_falhou_aviso", suspensa: "fa_suspensa_aviso", cancelada: "fa_cancelada_aviso" }[st];
  const usoTxt = u.ilimitado ? tg("fa_sem_limite", { u: tg("fa_min", { n: fatNum(u.minutos || 0) }) })
    : tg("fa_de", { u: fatNum(u.minutos || 0), l: tg("fa_min", { n: fatNum(u.limite || 0) }) });
  const nomeTipo = (p) => (p.tipo === "cancelar" ? tg("fa_ped_cancelar")
    : tg("fa_ped_trocar_plano", { plano: ((r.planos || []).find((x) => x.codigo === p.plano) || {}).nome || p.plano }));

  el.innerHTML = `
    ${fatAviso ? `<div class="aviso mb" style="border-color:var(--ok);color:var(--ok)">${fatEsc(fatAviso)}</div>` : ""}
    <div class="card">
      <h2 class="icone-titulo">${typeof icone === "function" ? icone("grafico") : ""}<span>${tg("fa_titulo")}</span></h2>
      <div style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;align-items:flex-start">
        <div>
          <div style="font-size:1.4rem;font-weight:600">${fatEsc(info.plano ? info.plano.nome : tg("fa_sem_plano"))}
            <span class="badge ${corSt}" style="vertical-align:middle">${tg("fa_st_" + st)}</span></div>
          ${atual ? `<p class="desc" style="margin:4px 0 0">${fatEsc(fatPreco(atual, cicloAtual))} · ${tg(cicloAtual === "anual" ? "fa_ciclo_anual" : "fa_ciclo_mensal")}</p>` : ""}
          ${datas ? `<p class="desc" style="margin:4px 0 0">${fatEsc(datas)}</p>` : ""}
        </div>
        ${r.portal_disponivel ? `<button class="btn secondary small" id="fa-portal">${tg("fa_portal")}</button>` : ""}
      </div>
      ${aviso ? `<div class="aviso mt">${tg(aviso)}</div>` : ""}
    </div>
    <div class="grid cols-2">
      <div class="card">
        <h2>${tg("fa_uso_titulo")}</h2>
        <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap">
          <strong>${tg("fa_minutos")}</strong><span>${fatEsc(usoTxt)}</span>
        </div>
        ${u.ilimitado ? "" : fatBarra(u.pct, u.status)}
        ${fatLinhaLimite(tg("fa_gestores"), info.gestores)}
        ${fatLinhaLimite(tg("fa_vagas"), info.vagas)}
      </div>
      <div class="card">
        <h2>${tg("fa_hist_titulo")}</h2>
        ${fatHistorico(r.historico, r.limite_minutos)}
      </div>
    </div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center">
        <h2 style="margin:0">${tg("fa_comparar")}</h2>
        <div class="tabs" style="margin:0">
          <button class="tab ${fatCiclo === "mensal" ? "ativa" : ""}" data-fa-ciclo="mensal">${tg("fa_mensal")}</button>
          <button class="tab ${fatCiclo === "anual" ? "ativa" : ""}" data-fa-ciclo="anual">${tg("fa_anual")}</button>
        </div>
      </div>
      <div class="grid cols-3 mt">${(r.planos || []).map((p) => fatCartaoPlano(p, fatCiclo, atual)).join("")}</div>
    </div>
    <div class="card">
      <h2>${tg("fa_cancelar_titulo")}</h2>
      <p class="desc">${tg("fa_cancelar_desc")}</p>
      <button class="btn ghost small" id="fa-cancelar">${tg("fa_cancelar_btn")}</button>
      ${(r.pedidos || []).length ? `<h3 class="mt">${tg("fa_pedidos")}</h3>
        <ul style="margin:6px 0 0 18px;padding:0;font-size:.88rem">${r.pedidos.map((p) =>
          `<li>${fatEsc(nomeTipo(p))} · ${fatEsc(typeof fmtDataHora === "function" ? fmtDataHora(p.criado_em) : p.criado_em)} · ${fatEsc(p.gestor_nome || "")}</li>`).join("")}</ul>` : ""}
    </div>`;
  fatAviso = "";

  const portal = el.querySelector("#fa-portal");
  if (portal) portal.addEventListener("click", async () => {
    portal.disabled = true;
    try {
      const res = await api("/api/gestor/plano/portal");
      if (res.url) location.href = res.url;
    } catch (e) {
      alert(e.message);
    } finally {
      portal.disabled = false;
    }
  });
  el.querySelectorAll("[data-fa-ciclo]").forEach((b) => b.addEventListener("click", () => {
    fatCiclo = b.dataset.faCiclo;
    abaFaturamento(el);
  }));
  el.querySelectorAll("[data-fa-plano]").forEach((b) =>
    b.addEventListener("click", () => fatEscolherPlano(el, r, b.dataset.faPlano, b)));
  el.querySelector("#fa-cancelar").addEventListener("click", () => fatPedirCancelamento(el, r.motivos));
}
