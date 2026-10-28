/* =====================================================================
   Página de assinatura (assinar.html): resumo do plano escolhido
   (GET /api/planos) e criação da conta (POST /api/assinar).
   Idiomas: pt, en, es. Escolha: ?lang=, localStorage "idioma",
   depois o idioma do navegador.
   Depois do cadastro grava a sessão como o login do gestor (gestor.js)
   e segue para o checkout_url, se houver, ou para /gestor.
   ===================================================================== */

(function () {
  "use strict";

  const IDIOMAS = ["pt", "en", "es"];
  const LOCALES = { pt: "pt-BR", en: "en-US", es: "es-US" };
  const LANG_HTML = { pt: "pt-BR", en: "en", es: "es" };

  const TXT = {
    pt: {
      titulo_pagina: "Comece seu teste grátis · Bússola",
      pular: "Pular para o formulário", entrar: "Entrar", idioma_rot: "Idioma", tema: "Alternar tema",
      eyebrow: "Teste grátis", titulo: "Crie sua conta na Bússola",
      sub: "Cadastre a sua empresa. Logo depois você configura a Francisca e a sua primeira vaga.",
      empresa: "Nome da empresa", nome: "Seu nome", telefone: "Telefone", email: "E-mail de trabalho",
      senha: "Senha", senha_dica: "Pelo menos 8 caracteres.", mostrar: "Mostrar", ocultar: "Ocultar",
      mostrar_rot: "Mostrar a senha", ocultar_rot: "Ocultar a senha",
      aceite: 'Li e aceito os <a href="/termos.html" target="_blank" rel="noopener">Termos de uso</a> e a <a href="/privacidade.html" target="_blank" rel="noopener">Política de privacidade</a>.',
      enviar: "Começar teste grátis", enviando: "Criando a sua conta...",
      ja_tem: "Já tem conta?",
      erro_empresa: "Informe o nome da empresa.", erro_nome: "Informe o seu nome.",
      erro_email: "Informe um e-mail válido.", erro_telefone: "Informe um telefone válido, com DDD.",
      erro_senha: "A senha precisa ter pelo menos 8 caracteres.", erro_aceite: "Aceite os termos para continuar.",
      erro_generico: "Não foi possível criar a sua conta. Tente de novo.",
      erro_rede: "Problema de conexão. Verifique a internet e tente de novo.",
      erro_indisponivel: "O cadastro não está disponível agora. Tente de novo mais tarde.",
      resumo: "Seu plano", plano_rot: "Plano", mensal: "Mensal", anual: "Anual",
      mes: "/mês", cobrado_anual: "Cobrado {v} por ano", economia: "Você economiza {v} por ano",
      minutos: "{n} minutos de voz por mês", numero_sim: "Número de telefone exclusivo", numero_nao: "Número de ligação compartilhado",
      sms: "{n} SMS por mês", gestores: "Até {n} gestores", gestores_ilim: "Gestores ilimitados",
      carregando: "Carregando planos...",
      plano_indisponivel: "Não foi possível carregar os planos agora. Você ainda pode criar a conta e escolher o plano lá dentro.",
      trial_sem_cartao: "{dias} dias grátis, sem cartão de crédito.",
      trial_com_cartao: "{dias} dias grátis. No próximo passo você informa a forma de pagamento num checkout seguro.",
      trial_min: " Inclui {min} minutos de voz para testar a Francisca.",
      seguro: "Seus dados trafegam criptografados.",
      up_eyebrow: "Mudar de plano", up_titulo: "Confirme o seu plano", up_sub: "Você está conectado como {quem}. Escolha o plano ao lado e siga para o checkout seguro.", up_btn: "Continuar para o pagamento", up_enviando: "Abrindo o checkout...", up_voltar: "Voltar ao painel", up_erro: "Não foi possível abrir o checkout agora.",
    },
    en: {
      titulo_pagina: "Start your free trial · Bússola",
      pular: "Skip to form", entrar: "Sign in", idioma_rot: "Language", tema: "Toggle theme",
      eyebrow: "Free trial", titulo: "Create your Bússola account",
      sub: "Set up your company. Right after, you can configure Francisca and your first job.",
      empresa: "Company name", nome: "Your name", telefone: "Phone", email: "Work email",
      senha: "Password", senha_dica: "At least 8 characters.", mostrar: "Show", ocultar: "Hide",
      mostrar_rot: "Show password", ocultar_rot: "Hide password",
      aceite: 'I have read and agree to the <a href="/termos.html" target="_blank" rel="noopener">Terms of use</a> and the <a href="/privacidade.html" target="_blank" rel="noopener">Privacy policy</a>.',
      enviar: "Start free trial", enviando: "Creating your account...",
      ja_tem: "Already have an account?",
      erro_empresa: "Enter your company name.", erro_nome: "Enter your name.",
      erro_email: "Enter a valid email address.", erro_telefone: "Enter a valid phone number, including area code.",
      erro_senha: "Your password needs at least 8 characters.", erro_aceite: "Please accept the terms to continue.",
      erro_generico: "We couldn't create your account. Please try again.",
      erro_rede: "Connection problem. Check your internet and try again.",
      erro_indisponivel: "Sign up isn't available right now. Please try again later.",
      resumo: "Your plan", plano_rot: "Plan", mensal: "Monthly", anual: "Annual",
      mes: "/mo", cobrado_anual: "Billed {v} per year", economia: "You save {v} per year",
      minutos: "{n} voice minutes per month", numero_sim: "Dedicated phone number", numero_nao: "Shared calling number",
      sms: "{n} SMS per month", gestores: "Up to {n} managers", gestores_ilim: "Unlimited managers",
      carregando: "Loading plans...",
      plano_indisponivel: "We couldn't load the plans right now. You can still create your account and choose a plan inside.",
      trial_sem_cartao: "{dias} days free, no credit card required.",
      trial_com_cartao: "{dias} days free. Next, you'll add a payment method in a secure checkout.",
      trial_min: " Includes {min} voice minutes to try Francisca.",
      seguro: "Your data is encrypted in transit.",
      up_eyebrow: "Change plan", up_titulo: "Confirm your plan", up_sub: "You are signed in as {quem}. Pick the plan on this page and continue to secure checkout.", up_btn: "Continue to payment", up_enviando: "Opening checkout...", up_voltar: "Back to the panel", up_erro: "We couldn't open checkout right now.",
    },
    es: {
      titulo_pagina: "Empieza tu prueba gratis · Bússola",
      pular: "Saltar al formulario", entrar: "Entrar", idioma_rot: "Idioma", tema: "Cambiar tema",
      eyebrow: "Prueba gratis", titulo: "Crea tu cuenta en Bússola",
      sub: "Registra tu empresa. Justo después puedes configurar a Francisca y tu primera vacante.",
      empresa: "Nombre de la empresa", nome: "Tu nombre", telefone: "Teléfono", email: "Correo de trabajo",
      senha: "Contraseña", senha_dica: "Al menos 8 caracteres.", mostrar: "Mostrar", ocultar: "Ocultar",
      mostrar_rot: "Mostrar la contraseña", ocultar_rot: "Ocultar la contraseña",
      aceite: 'Leí y acepto los <a href="/termos.html" target="_blank" rel="noopener">Términos de uso</a> y la <a href="/privacidade.html" target="_blank" rel="noopener">Política de privacidad</a>.',
      enviar: "Empezar prueba gratis", enviando: "Creando tu cuenta...",
      ja_tem: "¿Ya tienes cuenta?",
      erro_empresa: "Escribe el nombre de la empresa.", erro_nome: "Escribe tu nombre.",
      erro_email: "Escribe un correo válido.", erro_telefone: "Escribe un teléfono válido, con código de área.",
      erro_senha: "La contraseña necesita al menos 8 caracteres.", erro_aceite: "Acepta los términos para continuar.",
      erro_generico: "No pudimos crear tu cuenta. Inténtalo de nuevo.",
      erro_rede: "Problema de conexión. Revisa tu internet e inténtalo de nuevo.",
      erro_indisponivel: "El registro no está disponible ahora. Inténtalo más tarde.",
      resumo: "Tu plan", plano_rot: "Plan", mensal: "Mensual", anual: "Anual",
      mes: "/mes", cobrado_anual: "Facturado {v} al año", economia: "Ahorras {v} al año",
      minutos: "{n} minutos de voz al mes", numero_sim: "Número de teléfono exclusivo", numero_nao: "Número de llamada compartido",
      sms: "{n} SMS al mes", gestores: "Hasta {n} gestores", gestores_ilim: "Gestores ilimitados",
      carregando: "Cargando planes...",
      plano_indisponivel: "No pudimos cargar los planes ahora. Igual puedes crear tu cuenta y elegir el plan adentro.",
      trial_sem_cartao: "{dias} días gratis, sin tarjeta de crédito.",
      trial_com_cartao: "{dias} días gratis. En el siguiente paso agregas un medio de pago en un checkout seguro.",
      trial_min: " Incluye {min} minutos de voz para probar a Francisca.",
      seguro: "Tus datos viajan cifrados.",
      up_eyebrow: "Cambiar de plan", up_titulo: "Confirma tu plan", up_sub: "Iniciaste sesión como {quem}. Elige el plan en esta página y sigue al checkout seguro.", up_btn: "Continuar al pago", up_enviando: "Abriendo el checkout...", up_voltar: "Volver al panel", up_erro: "No pudimos abrir el checkout ahora.",
    },
  };

  const ICONES = {
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    presente: '<rect x="3.5" y="8" width="17" height="4" rx="1"/><path d="M5 12v8h14v-8M12 8v12"/><path d="M12 8c-1.5-3-5-3.5-5-1.5S10 8 12 8zM12 8c1.5-3 5-3.5 5-1.5S14 8 12 8z"/>',
    cadeado: '<rect x="4.5" y="10.5" width="15" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
  };
  const ic = (n) => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + ICONES[n] + "</svg>";

  // ------------------------------------------------ utilidades
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = (txt, vars) => String(txt || "").replace(/\{(\w+)\}/g, (m, k) => (vars && vars[k] != null ? vars[k] : m));
  function num(v) { const n = Number(v); return v !== null && v !== undefined && v !== "" && isFinite(n) ? n : null; }
  function normalizar(v) { const c = String(v || "").trim().toLowerCase().slice(0, 2); return IDIOMAS.includes(c) ? c : ""; }

  const params = new URLSearchParams(location.search);
  let idioma = normalizar(params.get("lang"));
  if (!idioma) { try { idioma = normalizar(localStorage.getItem("idioma")); } catch (e) { /* armazenamento bloqueado */ } }
  if (!idioma) {
    const n = String(navigator.language || "").toLowerCase();
    idioma = n.startsWith("pt") ? "pt" : n.startsWith("es") ? "es" : "en";
  }
  const t = (k) => TXT[idioma][k] || TXT.en[k] || "";

  function inteiro(n) { return new Intl.NumberFormat(LOCALES[idioma]).format(Math.round(n)); }
  function dinheiro(v, moeda) {
    const n = num(v); if (n === null) return "";
    const frac = Math.abs(n - Math.round(n)) > 1e-9;
    try {
      return new Intl.NumberFormat(LOCALES[idioma], {
        style: "currency", currency: moeda || "USD",
        minimumFractionDigits: frac ? 2 : 0, maximumFractionDigits: frac ? 2 : 0,
      }).format(n);
    } catch (e) { return "$" + n; }
  }

  // ------------------------------------------------ estado
  let PLANOS = null;
  let estado = "carregando";
  let plano = String(params.get("plano") || "").trim().slice(0, 60);
  let ciclo = params.get("ciclo") === "anual" ? "anual" : "mensal";
  let senhaVisivel = false;
  let pedido = 0;
  let enviando = false;
  // com sessão de gestor aberta (link "mudar de plano" do painel) não mostramos o cadastro
  let tokenGestor = "";
  try { tokenGestor = localStorage.getItem("gestor_token") || ""; } catch (e) { /* armazenamento bloqueado */ }
  function infoGestor() {
    try { return JSON.parse(localStorage.getItem("gestor_info")) || {}; } catch (e) { return {}; }
  }

  function anualTotal(p) {
    const a = num(p.preco_anual), m = num(p.preco_mensal);
    if (a === null || a <= 0) return null;
    return m && a < m * 2 ? a * 12 : a;
  }
  function planoAtual() {
    if (!PLANOS) return null;
    return PLANOS.planos.find((p) => String(p.codigo) === plano) || null;
  }
  function stripeAtivo() { return !!(PLANOS && PLANOS.stripe_ativo); }

  function atualizarUrl() {
    const u = new URL(location.href);
    if (plano) u.searchParams.set("plano", plano); else u.searchParams.delete("plano");
    u.searchParams.set("ciclo", ciclo);
    try { history.replaceState(null, "", u.pathname + u.search); } catch (e) { /* sem history */ }
  }

  async function carregarPlanos() {
    const meu = ++pedido;
    let d = null;
    try {
      const r = await fetch("/api/planos?idioma=" + idioma, { headers: { Accept: "application/json", "X-Idioma": idioma } });
      if (!r.ok) throw new Error("http");
      d = await r.json();
      if (!d || !Array.isArray(d.planos)) throw new Error("formato");
      d.planos = d.planos.filter((p) => p && p.codigo && p.nome);
      if (!d.planos.length) throw new Error("vazio");
    } catch (e) { d = null; }
    if (meu !== pedido) return;
    if (d) {
      PLANOS = d; estado = "ok";
      if (!planoAtual()) {
        const dest = d.planos.find((p) => p.destaque) || d.planos[0];
        plano = String(dest.codigo);
      }
      if (ciclo === "anual" && !d.planos.some((p) => anualTotal(p) !== null)) ciclo = "mensal";
      atualizarUrl();
    } else if (!PLANOS) {
      estado = "erro";
    }
    desenharResumo();
    aplicarCadastroFechado();
  }

  // cadastro público fechado pelo dono: mostra um aviso no lugar do formulário
  const AVISO_FECHADO = {
    pt: "As assinaturas abrem em breve. Para conhecer o Bússola agora, fale com a gente: rh.tonybelleza.com",
    en: "Signups open soon. To see Bússola now, get in touch: rh.tonybelleza.com",
    es: "Las suscripciones abren pronto. Para conocer Bússola ahora, contáctanos: rh.tonybelleza.com",
  };
  function aplicarCadastroFechado() {
    const form = document.getElementById("form-assinar");
    if (!form || tokenGestor || !PLANOS || PLANOS.assinatura_aberta !== false) return;
    form.style.display = "none";
    let aviso = document.getElementById("aviso-fechado");
    if (!aviso) {
      aviso = document.createElement("p");
      aviso.id = "aviso-fechado";
      aviso.className = "as-plano-desc";
      form.parentNode.insertBefore(aviso, form);
    }
    aviso.textContent = AVISO_FECHADO[idioma] || AVISO_FECHADO.en;
  }

  // ------------------------------------------------ desenho
  function desenharTextos() {
    document.documentElement.lang = LANG_HTML[idioma];
    document.title = t("titulo_pagina");
    $$("[data-t]").forEach((el) => { el.textContent = t(el.dataset.t); });
    $$("[data-t-html]").forEach((el) => { el.innerHTML = t(el.dataset.tHtml); });
    const g = $("#idiomas");
    g.setAttribute("aria-label", t("idioma_rot"));
    g.innerHTML = IDIOMAS.map((c) =>
      '<button type="button" data-lang="' + c + '" lang="' + LANG_HTML[c] + '" aria-pressed="' + (c === idioma) + '" title="' +
      { pt: "Português", en: "English", es: "Español" }[c] + '">' + c.toUpperCase() + "</button>").join("");
    desenharBotaoSenha();
    if (enviando) $("#btn-enviar").textContent = t("enviando");
    if (tokenGestor) {
      const info = infoGestor();
      const quem = [info.nome, info.empresa && info.empresa.nome].filter(Boolean).join(", ") || "";
      $("#form-assinar").hidden = true;
      $("#upgrade").hidden = false;
      $(".as-form .lp-eyebrow").textContent = t("up_eyebrow");
      $("#as-titulo").textContent = t("up_titulo");
      $(".as-form > p.sub").textContent = quem ? fmt(t("up_sub"), { quem: quem }) : t("up_sub").replace(/ \{quem\}[^.]*\./, "").trim();
      $(".lp-skip").setAttribute("href", "#btn-checkout");
      document.title = t("up_titulo") + " · Bússola";
      $("#trial").hidden = true;
      if (enviando) $("#btn-checkout").textContent = t("up_enviando");
    }
    $("#seguro").innerHTML = ic("cadeado") + "<span>" + esc(t("seguro")) + "</span>";
    const bt = document.querySelector(".btn-tema"); if (bt) bt.setAttribute("aria-label", t("tema"));
  }

  function desenharBotaoSenha() {
    const b = $("#ver-senha");
    b.textContent = senhaVisivel ? t("ocultar") : t("mostrar");
    b.setAttribute("aria-label", senhaVisivel ? t("ocultar_rot") : t("mostrar_rot"));
    b.setAttribute("aria-pressed", String(senhaVisivel));
  }

  function desenharResumo() {
    const caixa = $("#resumo-corpo");
    if (estado === "carregando") {
      caixa.innerHTML = '<p class="as-plano-desc">' + esc(t("carregando")) + "</p>";
    } else if (estado === "erro") {
      caixa.innerHTML = '<p class="as-plano-desc">' + esc(t("plano_indisponivel")) + "</p>";
    } else {
      const p = planoAtual();
      const moeda = PLANOS.moeda || "USD";
      const temAnual = PLANOS.planos.some((x) => anualTotal(x) !== null);
      const m = num(p.preco_mensal), tot = anualTotal(p);
      const anual = ciclo === "anual" && tot !== null;
      const preco = anual ? tot / 12 : m;
      let nota = "";
      if (anual) {
        nota = esc(fmt(t("cobrado_anual"), { v: dinheiro(tot, moeda) }));
        const eco = m ? m * 12 - tot : 0;
        if (eco > 0) nota += '<span class="eco">' + esc(fmt(t("economia"), { v: dinheiro(eco, moeda) })) + "</span>";
      }
      // o servidor já manda a lista de recursos traduzida; sem ela, montamos pelos campos
      const recursos = (Array.isArray(p.recursos) ? p.recursos : []).filter(Boolean).map(String);
      const itens = recursos.slice(0, 6);
      if (!recursos.length) {
        if (num(p.minutos_voz) > 0) itens.push(fmt(t("minutos"), { n: inteiro(p.minutos_voz) }));
        if ("numero_exclusivo" in p && num(p.minutos_voz) > 0) itens.push(p.numero_exclusivo ? t("numero_sim") : t("numero_nao"));
        if (num(p.sms_mes)) itens.push(fmt(t("sms"), { n: inteiro(p.sms_mes) }));
        if ("gestores_max" in p) itens.push(num(p.gestores_max) > 0 ? fmt(t("gestores"), { n: inteiro(p.gestores_max) }) : t("gestores_ilim"));
      }

      caixa.innerHTML =
        '<label class="field" style="margin-bottom:6px"><span>' + esc(t("plano_rot")) + '</span><select id="sel-plano">' +
        PLANOS.planos.map((x) => '<option value="' + esc(x.codigo) + '"' + (String(x.codigo) === plano ? " selected" : "") + ">" + esc(x.nome) + "</option>").join("") +
        "</select></label>" +
        (temAnual
          ? '<div class="lp-toggle" role="group" aria-label="' + esc(t("mensal") + " / " + t("anual")) + '">' +
            '<button type="button" data-ciclo="mensal" aria-pressed="' + (ciclo === "mensal") + '">' + esc(t("mensal")) + "</button>" +
            '<button type="button" data-ciclo="anual" aria-pressed="' + (ciclo === "anual") + '">' + esc(t("anual")) + "</button></div>"
          : "") +
        '<div class="as-plano-nome">' + esc(p.nome) + "</div>" +
        '<p class="as-plano-desc">' + esc(p.descricao || "") + "</p>" +
        '<div class="lp-preco"><b>' + esc(dinheiro(preco, moeda)) + "</b><span>" + esc(t("mes")) + "</span></div>" +
        '<p class="lp-preco-nota">' + nota + "</p>" +
        "<ul>" + itens.map((x) => "<li>" + ic("check") + "<span>" + esc(x) + "</span></li>").join("") + "</ul>";
    }
    const dias = PLANOS && num(PLANOS.trial_dias) ? num(PLANOS.trial_dias) : 14;
    const min = PLANOS && num(PLANOS.trial_minutos) ? num(PLANOS.trial_minutos) : null;
    let txt = fmt(stripeAtivo() ? t("trial_com_cartao") : t("trial_sem_cartao"), { dias: dias });
    if (min) txt += fmt(t("trial_min"), { min: inteiro(min) });
    $("#trial").innerHTML = ic("presente") + "<span>" + esc(txt) + "</span>";
  }

  // ------------------------------------------------ formulário
  function mostrarErro(msg, campo) {
    const caixa = $("#erro");
    caixa.textContent = msg;
    caixa.hidden = !msg;
    $$("#form-assinar input").forEach((i) => i.removeAttribute("aria-invalid"));
    if (campo) { campo.setAttribute("aria-invalid", "true"); campo.focus(); }
    else if (msg) caixa.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  function validar() {
    const empresa = $("#f-empresa"), nome = $("#f-nome"), email = $("#f-email"),
      tel = $("#f-telefone"), senha = $("#f-senha"), aceite = $("#f-aceite");
    if (empresa.value.trim().length < 2) return [t("erro_empresa"), empresa];
    if (nome.value.trim().length < 2) return [t("erro_nome"), nome];
    const digitos = tel.value.replace(/\D/g, "");
    if (digitos.length < 10 || digitos.length > 15) return [t("erro_telefone"), tel];
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim())) return [t("erro_email"), email];
    if (senha.value.length < 8) return [t("erro_senha"), senha];
    if (!aceite.checked) return [t("erro_aceite"), aceite];
    return null;
  }

  // só segue para endereços https ou caminhos do próprio site
  function urlSegura(u) {
    if (typeof u !== "string" || !u) return "";
    if (u.startsWith("/") && !u.startsWith("//")) return u;
    try { const x = new URL(u); return x.protocol === "https:" ? x.href : ""; } catch (e) { return ""; }
  }

  // mesma sessão que salvarSessao() em gestor.js grava depois do login
  function salvarSessao(r) {
    try {
      localStorage.setItem("gestor_token", r.token);
      localStorage.setItem("gestor_info", JSON.stringify({
        nome: r.nome, login: r.login, local: r.local, admin: r.admin,
        modulos: r.modulos || [], empresa: r.empresa || null, idioma: r.idioma || "",
      }));
      localStorage.setItem("idioma", idioma);
    } catch (e) { /* armazenamento bloqueado: o gestor faz login de novo */ }
  }

  async function enviar(ev) {
    ev.preventDefault();
    if (enviando) return;
    const problema = validar();
    if (problema) { mostrarErro(problema[0], problema[1]); return; }
    mostrarErro("");
    const btn = $("#btn-enviar");
    enviando = true;
    btn.setAttribute("aria-busy", "true");
    btn.textContent = t("enviando");

    const corpo = {
      empresa: $("#f-empresa").value.trim(),
      nome: $("#f-nome").value.trim(),
      email: $("#f-email").value.trim(),
      senha: $("#f-senha").value,
      telefone: $("#f-telefone").value.trim(),
      plano: plano,
      ciclo: ciclo,
      idioma: idioma,
      aceite_termos: true,
    };

    let resp = null, dados = {};
    try {
      resp = await fetch("/api/assinar", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json", "X-Idioma": idioma },
        body: JSON.stringify(corpo),
      });
      dados = await resp.json().catch(() => ({}));
    } catch (e) {
      resp = null;
    }

    const terminar = (msg) => {
      enviando = false;
      btn.removeAttribute("aria-busy");
      btn.textContent = t("enviar");
      mostrarErro(msg);
    };
    if (!resp) { terminar(t("erro_rede")); return; }
    if (!resp.ok) {
      const msg = dados && typeof dados.erro === "string" && dados.erro
        ? dados.erro
        : (resp.status === 404 || resp.status === 405 || resp.status === 501 ? t("erro_indisponivel") : t("erro_generico"));
      terminar(msg);
      return;
    }

    const checkout = urlSegura(dados && dados.checkout_url);
    if (dados && dados.token) salvarSessao(dados);
    if (checkout) { location.href = checkout; return; }
    if (!dados || !dados.token) { terminar(t("erro_generico")); return; }
    location.href = "/gestor";
  }

  // ------------------------------------------------ mudar de plano (gestor logado)
  async function irParaCheckout() {
    if (enviando) return;
    mostrarErro("");
    const btn = $("#btn-checkout");
    enviando = true;
    btn.setAttribute("aria-busy", "true");
    btn.textContent = t("up_enviando");
    let resp = null, dados = {};
    try {
      resp = await fetch("/api/gestor/plano/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json", "X-Idioma": idioma, "X-Gestor-Token": tokenGestor },
        body: JSON.stringify({ plano: plano, ciclo: ciclo }),
      });
      dados = await resp.json().catch(() => ({}));
    } catch (e) { resp = null; }
    const checkout = resp && resp.ok && dados && !dados.erro ? urlSegura(dados.checkout_url) : "";
    if (checkout) { location.href = checkout; return; }
    enviando = false;
    btn.removeAttribute("aria-busy");
    btn.textContent = t("up_btn");
    let msg = !resp ? t("erro_rede") : (dados && typeof dados.erro === "string" && dados.erro) ? dados.erro : t("up_erro");
    mostrarErro(msg);
  }

  // ------------------------------------------------ eventos
  document.addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-lang]");
    if (b) {
      const c = normalizar(b.dataset.lang);
      if (!c || c === idioma) return;
      idioma = c;
      try { localStorage.setItem("idioma", c); } catch (e) { /* armazenamento bloqueado */ }
      desenharTextos();
      desenharResumo();
      carregarPlanos();
      return;
    }
    const cb = ev.target.closest("[data-ciclo]");
    if (cb) { ciclo = cb.dataset.ciclo === "anual" ? "anual" : "mensal"; atualizarUrl(); desenharResumo(); }
  });
  document.addEventListener("change", (ev) => {
    if (ev.target && ev.target.id === "sel-plano") {
      plano = ev.target.value;
      atualizarUrl();
      desenharResumo();
      const s = $("#sel-plano"); if (s) s.focus();
    }
  });
  $("#ver-senha").addEventListener("click", () => {
    senhaVisivel = !senhaVisivel;
    $("#f-senha").type = senhaVisivel ? "text" : "password";
    desenharBotaoSenha();
  });
  $("#form-assinar").addEventListener("submit", enviar);
  $("#btn-checkout").addEventListener("click", irParaCheckout);
  document.addEventListener("DOMContentLoaded", () => {
    const bt = document.querySelector(".btn-tema"); if (bt) bt.setAttribute("aria-label", t("tema"));
  });

  desenharTextos();
  desenharResumo();
  carregarPlanos();
})();
