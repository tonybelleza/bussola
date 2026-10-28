/* =====================================================================
   Domínio próprio das páginas de vagas (painel do gestor, Configurações).
   - secaoDominio(el): cartão para o administrador cadastrar um domínio
     (ex.: jobs.empresa.com), ver os registros DNS (CNAME ou A e o TXT
     de posse em _bussola.<domínio>), verificar e remover.
   Dados: /api/gestor/dominios (dominios.py). Carregado sob demanda pelo
   gestor.js. Textos em pt, en e es (tg do i18n-gestor.js, chaves "dm_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  dm_titulo: "Domínio próprio das vagas",
  dm_desc: "Mostre a página de vagas no endereço da sua empresa, por exemplo jobs.suaempresa.com. Depois de verificado, o endereço abre a lista de vagas, as páginas de cada vaga e o cadastro, com HTTPS automático.",
  dm_campo: "Domínio", dm_placeholder: "jobs.suaempresa.com", dm_adicionar: "Adicionar domínio",
  dm_limite: "Seu plano permite {n} domínio(s) próprio(s).", dm_limite_atingido: "Limite do plano atingido. Remova um domínio para cadastrar outro.",
  dm_nenhum: "Nenhum domínio cadastrado.",
  dm_verificado: "Verificado", dm_pendente: "Aguardando DNS",
  dm_verificar: "Verificar", dm_verificando: "Verificando...", dm_remover: "Remover",
  dm_remover_conf: "Remover o domínio {d}? A página de vagas deixa de abrir nesse endereço.",
  dm_passos: "No painel do seu provedor de DNS (GoDaddy, Cloudflare, Registro.br etc.), crie os registros abaixo. A propagação pode levar de alguns minutos a algumas horas.",
  dm_passo1: "1. Aponte o domínio para a Bússola (use uma das opções):",
  dm_passo1_cname: "Opção A, para subdomínios como jobs.suaempresa.com: registro CNAME",
  dm_passo1_a: "Opção B, para o domínio raiz (suaempresa.com) ou se o provedor não aceita CNAME: registro A",
  dm_passo2: "2. Comprove que o domínio é seu: registro TXT",
  dm_apex: "Domínio raiz não aceita CNAME na maioria dos provedores: use o registro A.",
  dm_tipo: "Tipo", dm_nome: "Nome", dm_valor: "Valor", dm_copiar: "Copiar", dm_copiado: "Copiado",
  dm_ok: "Domínio verificado. A página de vagas já responde em https://{d} (o certificado é emitido no primeiro acesso).",
  dm_e_dns: "O domínio ainda não aponta para a Bússola. Encontrado: {ips}. Esperado: {esp}.",
  dm_e_txt: "O registro TXT em {nome} não foi encontrado ou está com outro valor.",
  dm_e_txt_rede: "Não foi possível consultar o registro TXT agora. Tente de novo em alguns minutos.",
  dm_e_em_uso: "Este domínio já está verificado por outra empresa.",
  dm_nada: "nada",
  dm_abrir: "Abrir página", dm_ultima: "Última verificação: {d}",
});
Object.assign(I18N_GESTOR.en, {
  dm_titulo: "Custom domain for jobs",
  dm_desc: "Show your jobs page on your company's address, for example jobs.yourcompany.com. Once verified, the address opens the job list, each job page and the signup, with automatic HTTPS.",
  dm_campo: "Domain", dm_placeholder: "jobs.yourcompany.com", dm_adicionar: "Add domain",
  dm_limite: "Your plan allows {n} custom domain(s).", dm_limite_atingido: "Plan limit reached. Remove a domain to add another.",
  dm_nenhum: "No domain added yet.",
  dm_verificado: "Verified", dm_pendente: "Waiting for DNS",
  dm_verificar: "Verify", dm_verificando: "Verifying...", dm_remover: "Remove",
  dm_remover_conf: "Remove the domain {d}? The jobs page will stop opening at this address.",
  dm_passos: "In your DNS provider's dashboard (GoDaddy, Cloudflare, Namecheap etc.), create the records below. Propagation can take from a few minutes to a few hours.",
  dm_passo1: "1. Point the domain to Bússola (use one of the options):",
  dm_passo1_cname: "Option A, for subdomains like jobs.yourcompany.com: CNAME record",
  dm_passo1_a: "Option B, for the root domain (yourcompany.com) or if your provider does not accept CNAME: A record",
  dm_passo2: "2. Prove the domain is yours: TXT record",
  dm_apex: "Most providers do not accept CNAME on a root domain: use the A record.",
  dm_tipo: "Type", dm_nome: "Name", dm_valor: "Value", dm_copiar: "Copy", dm_copiado: "Copied",
  dm_ok: "Domain verified. The jobs page now answers at https://{d} (the certificate is issued on the first visit).",
  dm_e_dns: "The domain does not point to Bússola yet. Found: {ips}. Expected: {esp}.",
  dm_e_txt: "The TXT record at {nome} was not found or has a different value.",
  dm_e_txt_rede: "Could not check the TXT record right now. Try again in a few minutes.",
  dm_e_em_uso: "This domain is already verified by another company.",
  dm_nada: "nothing",
  dm_abrir: "Open page", dm_ultima: "Last check: {d}",
});
Object.assign(I18N_GESTOR.es, {
  dm_titulo: "Dominio propio de las vacantes",
  dm_desc: "Muestra la página de vacantes en la dirección de tu empresa, por ejemplo jobs.tuempresa.com. Una vez verificada, la dirección abre la lista de vacantes, la página de cada vacante y el registro, con HTTPS automático.",
  dm_campo: "Dominio", dm_placeholder: "jobs.tuempresa.com", dm_adicionar: "Agregar dominio",
  dm_limite: "Tu plan permite {n} dominio(s) propio(s).", dm_limite_atingido: "Límite del plan alcanzado. Elimina un dominio para agregar otro.",
  dm_nenhum: "Ningún dominio registrado.",
  dm_verificado: "Verificado", dm_pendente: "Esperando DNS",
  dm_verificar: "Verificar", dm_verificando: "Verificando...", dm_remover: "Eliminar",
  dm_remover_conf: "¿Eliminar el dominio {d}? La página de vacantes dejará de abrir en esta dirección.",
  dm_passos: "En el panel de tu proveedor de DNS (GoDaddy, Cloudflare, Namecheap etc.), crea los registros de abajo. La propagación puede tardar de unos minutos a algunas horas.",
  dm_passo1: "1. Apunta el dominio a Bússola (usa una de las opciones):",
  dm_passo1_cname: "Opción A, para subdominios como jobs.tuempresa.com: registro CNAME",
  dm_passo1_a: "Opción B, para el dominio raíz (tuempresa.com) o si tu proveedor no acepta CNAME: registro A",
  dm_passo2: "2. Demuestra que el dominio es tuyo: registro TXT",
  dm_apex: "La mayoría de los proveedores no acepta CNAME en un dominio raíz: usa el registro A.",
  dm_tipo: "Tipo", dm_nome: "Nombre", dm_valor: "Valor", dm_copiar: "Copiar", dm_copiado: "Copiado",
  dm_ok: "Dominio verificado. La página de vacantes ya responde en https://{d} (el certificado se emite en la primera visita).",
  dm_e_dns: "El dominio todavía no apunta a Bússola. Encontrado: {ips}. Esperado: {esp}.",
  dm_e_txt: "El registro TXT en {nome} no se encontró o tiene otro valor.",
  dm_e_txt_rede: "No se pudo consultar el registro TXT ahora. Inténtalo de nuevo en unos minutos.",
  dm_e_em_uso: "Este dominio ya está verificado por otra empresa.",
  dm_nada: "nada",
  dm_abrir: "Abrir página", dm_ultima: "Última verificación: {d}",
});

function dmMensagemResultado(res) {
  if (!res) return "";
  if (res.ok) return tg("dm_ok", { d: res.dominio });
  if (res.erro === "dns") {
    return tg("dm_e_dns", {
      ips: (res.dns.ips || []).join(", ") || tg("dm_nada"),
      esp: (res.dns.esperado || []).join(", ") || "?",
    });
  }
  if (res.erro === "txt") return tg("dm_e_txt", { nome: res.txt.nome });
  if (res.erro === "txt_rede") return tg("dm_e_txt_rede");
  if (res.erro === "em_uso") return tg("dm_e_em_uso");
  return "";
}

function dmLinhaRegistro(reg) {
  return `<tr>
    <td><strong>${esc(reg.tipo)}</strong></td>
    <td style="word-break:break-all">${esc(reg.nome)}</td>
    <td style="word-break:break-all"><code>${esc(reg.valor || "?")}</code></td>
    <td class="num"><button class="btn secondary small" data-dm-copiar="${esc(reg.valor || "")}">${tg("dm_copiar")}</button></td>
  </tr>`;
}

function dmTabela(regs) {
  return `<div class="tabela-wrap mt"><table class="tabela">
    <thead><tr><th>${tg("dm_tipo")}</th><th>${tg("dm_nome")}</th><th>${tg("dm_valor")}</th><th></th></tr></thead>
    <tbody>${regs.map(dmLinhaRegistro).join("")}</tbody></table></div>`;
}

function dmItem(it, resultado) {
  const ins = it.instrucoes || {};
  const badge = it.verificado
    ? `<span class="badge ok">${tg("dm_verificado")}</span>`
    : `<span class="badge warn">${tg("dm_pendente")}</span>`;
  const msg = resultado && resultado.item && resultado.item.id === it.id ? dmMensagemResultado(resultado) : "";
  const cor = resultado && resultado.ok ? "var(--ok)" : "var(--err)";
  return `<div class="comp-item" data-dm-item="${it.id}">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
      <div class="nome">${esc(it.dominio)} ${badge}</div>
      <div>
        ${it.verificado ? `<a class="btn secondary small" href="https://${esc(it.dominio)}/" target="_blank" rel="noopener">${tg("dm_abrir")}</a>` : ""}
        <button class="btn small" data-dm-verificar="${it.id}">${tg("dm_verificar")}</button>
        <button class="btn danger small" data-dm-remover="${it.id}" data-dm-nome="${esc(it.dominio)}">${tg("dm_remover")}</button>
      </div>
    </div>
    ${it.ultima_verificacao ? `<p class="desc" style="margin:6px 0 0">${tg("dm_ultima", { d: esc(it.ultima_verificacao) })}</p>` : ""}
    ${msg ? `<p class="form-erro" style="color:${cor}">${esc(msg)}</p>` : ""}
    ${it.verificado ? "" : `
      <p class="desc mt">${tg("dm_passos")}</p>
      <p class="desc" style="margin-bottom:0"><strong>${tg("dm_passo1")}</strong></p>
      ${ins.apex ? `<p class="desc" style="color:var(--warn)">${tg("dm_apex")}</p>` : ""}
      <p class="desc" style="margin:8px 0 0">${tg("dm_passo1_cname")}</p>
      ${dmTabela([ins.cname])}
      <p class="desc" style="margin:8px 0 0">${tg("dm_passo1_a")}</p>
      ${dmTabela([ins.a])}
      <p class="desc mt" style="margin-bottom:0"><strong>${tg("dm_passo2")}</strong></p>
      ${dmTabela([ins.txt])}`}
  </div>`;
}

async function secaoDominio(el, resultado) {
  if (!el) return;
  let r;
  try {
    r = resultado && resultado.dominios ? resultado : await api("/api/gestor/dominios");
  } catch (e) {
    el.innerHTML = "";
    return;
  }
  const limiteTxt = r.limite == null ? "" : tg("dm_limite", { n: fmtNumDm(r.limite) });
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("link")}<span>${tg("dm_titulo")}</span></h2>
      <p class="desc">${tg("dm_desc")}</p>
      ${r.dominios.length ? r.dominios.map((it) => dmItem(it, r.resultado)).join("") : `<p class="desc">${tg("dm_nenhum")}</p>`}
      ${r.pode_adicionar ? `
        <label class="field mt">${tg("dm_campo")}
          <input type="text" id="dm-dominio" placeholder="${esc(tg("dm_placeholder"))}" autocomplete="off" spellcheck="false">
        </label>
        <button class="btn" id="dm-adicionar">${tg("dm_adicionar")}</button>`
        : `<p class="desc mt">${tg("dm_limite_atingido")}</p>`}
      ${limiteTxt ? `<p class="desc" style="margin-top:10px">${limiteTxt}</p>` : ""}
      <div class="form-erro" id="dm-erro"></div>
    </div>`;
  const erro = el.querySelector("#dm-erro");
  const falhar = (e) => { erro.style.color = "var(--err)"; erro.textContent = e.message; };
  const add = el.querySelector("#dm-adicionar");
  if (add) {
    add.addEventListener("click", async () => {
      erro.textContent = "";
      try {
        const novo = await api("/api/gestor/dominios", { method: "POST", body: { dominio: el.querySelector("#dm-dominio").value } });
        secaoDominio(el, novo);
      } catch (e) { falhar(e); }
    });
  }
  el.querySelectorAll("[data-dm-verificar]").forEach((b) => b.addEventListener("click", async () => {
    erro.textContent = "";
    b.disabled = true;
    b.textContent = tg("dm_verificando");
    try {
      const res = await api("/api/gestor/dominios/" + b.dataset.dmVerificar + "/verificar", { method: "POST" });
      secaoDominio(el, res);
    } catch (e) {
      b.disabled = false;
      b.textContent = tg("dm_verificar");
      falhar(e);
    }
  }));
  el.querySelectorAll("[data-dm-remover]").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm(tg("dm_remover_conf", { d: b.dataset.dmNome }))) return;
    try {
      const res = await api("/api/gestor/dominios/" + b.dataset.dmRemover, { method: "DELETE" });
      secaoDominio(el, res);
    } catch (e) { falhar(e); }
  }));
  el.querySelectorAll("[data-dm-copiar]").forEach((b) => b.addEventListener("click", () => {
    try { navigator.clipboard.writeText(b.dataset.dmCopiar); } catch (e) { /* sem área de transferência */ }
    b.textContent = tg("dm_copiado");
  }));
}

function fmtNumDm(n) {
  return typeof fmtNum === "function" ? fmtNum(n) : String(n);
}
