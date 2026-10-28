/* =====================================================================
   Páginas legais (termos.html, privacidade.html e dpa.html): troca de idioma.
   O texto de cada idioma fica no próprio HTML, em <article data-doc-lang>.
   Este script mostra o artigo certo, traduz o cabeçalho e o rodapé e
   desenha o seletor de idioma. Escolha: localStorage "idioma", depois o
   idioma do navegador; padrão inglês.
   ===================================================================== */

(function () {
  "use strict";

  const IDIOMAS = ["en", "pt", "es"];
  const LANG_HTML = { pt: "pt-BR", en: "en", es: "es" };
  const NOMES = { pt: "Português", en: "English", es: "Español" };

  const TXT = {
    en: {
      pular: "Skip to content", entrar: "Sign in", idioma_rot: "Language", tema: "Toggle light and dark theme",
      rod_sub: "AI phone screening and onboarding for companies that hire hourly workers.",
      rod_produto: "Product", rod_acesso: "Access", rod_legal: "Legal",
      rod_inicio: "Home", rod_precos: "Pricing", rod_teste: "Free trial",
      rod_vagas: "Jobs page", rod_candidato: "Candidate area", rod_gestor: "Manager login",
      rod_termos: "Terms of use", rod_privacidade: "Privacy", rod_dpa: "Data Processing Addendum",
      rod_copy: "© {ano} Tony Belleza. Bússola, B.A.S.E. methodology curated by Tony Belleza.",
    },
    pt: {
      pular: "Pular para o conteúdo", entrar: "Entrar", idioma_rot: "Idioma", tema: "Alternar tema claro e escuro",
      rod_sub: "Triagem por telefone com IA e onboarding para empresas que contratam por hora.",
      rod_produto: "Produto", rod_acesso: "Acesso", rod_legal: "Legal",
      rod_inicio: "Início", rod_precos: "Preços", rod_teste: "Teste grátis",
      rod_vagas: "Página de vagas", rod_candidato: "Área do candidato", rod_gestor: "Login do gestor",
      rod_termos: "Termos de uso", rod_privacidade: "Privacidade", rod_dpa: "Aditivo de Tratamento de Dados",
      rod_copy: "© {ano} Tony Belleza. Bússola, metodologia B.A.S.E. e curadoria Tony Belleza.",
    },
    es: {
      pular: "Saltar al contenido", entrar: "Entrar", idioma_rot: "Idioma", tema: "Cambiar tema claro y oscuro",
      rod_sub: "Entrevistas telefónicas con IA y onboarding para empresas que contratan personal por hora.",
      rod_produto: "Producto", rod_acesso: "Acceso", rod_legal: "Legal",
      rod_inicio: "Inicio", rod_precos: "Precios", rod_teste: "Prueba gratis",
      rod_vagas: "Página de vacantes", rod_candidato: "Área del candidato", rod_gestor: "Acceso del gestor",
      rod_termos: "Términos de uso", rod_privacidade: "Privacidad", rod_dpa: "Anexo de Tratamiento de Datos",
      rod_copy: "© {ano} Tony Belleza. Bússola, metodología B.A.S.E. y curaduría de Tony Belleza.",
    },
  };

  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const normalizar = (v) => {
    const cod = String(v || "").trim().toLowerCase().slice(0, 2);
    return IDIOMAS.includes(cod) ? cod : "";
  };

  function idiomaInicial() {
    let salvo = "";
    try { salvo = normalizar(localStorage.getItem("idioma")); } catch (e) { /* armazenamento bloqueado */ }
    if (salvo) return salvo;
    const n = String(navigator.language || "").toLowerCase();
    if (n.startsWith("pt")) return "pt";
    if (n.startsWith("es")) return "es";
    return "en";
  }

  let idioma = idiomaInicial();

  function desenhar() {
    const t = TXT[idioma];
    document.documentElement.lang = LANG_HTML[idioma];

    let artigo = null;
    $$("[data-doc-lang]").forEach((a) => {
      const ativo = a.dataset.docLang === idioma;
      a.hidden = !ativo;
      if (ativo) artigo = a;
    });
    if (artigo) {
      if (artigo.dataset.title) document.title = artigo.dataset.title;
      const md = document.querySelector('meta[name="description"]');
      if (md && artigo.dataset.desc) md.setAttribute("content", artigo.dataset.desc);
    }

    $$("[data-t]").forEach((el) => {
      const v = t[el.dataset.t];
      if (v) el.textContent = v.replace("{ano}", String(new Date().getFullYear()));
    });

    $$(".lp-lang").forEach((g) => {
      g.setAttribute("aria-label", t.idioma_rot);
      g.innerHTML = IDIOMAS.map((c) =>
        '<button type="button" data-lang="' + c + '" lang="' + LANG_HTML[c] + '" aria-pressed="' + (c === idioma) +
        '" title="' + NOMES[c] + '">' + c.toUpperCase() + "</button>").join("");
    });

    const bt = document.querySelector(".btn-tema");
    if (bt) bt.setAttribute("aria-label", t.tema);
  }

  function trocar(cod) {
    if (!IDIOMAS.includes(cod) || cod === idioma) return;
    idioma = cod;
    try { localStorage.setItem("idioma", cod); } catch (e) { /* armazenamento bloqueado */ }
    desenhar();
    // as âncoras do sumário mudam com o idioma: limpa o hash antigo
    if (location.hash && history.replaceState) history.replaceState(null, "", location.pathname + location.search);
    const botao = document.querySelector('.lp-lang button[data-lang="' + cod + '"]');
    if (botao) botao.focus();
  }

  document.addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-lang]");
    if (b) trocar(b.dataset.lang);
  });

  // o botão de tema (tema.js) nasce no DOMContentLoaded: traduz o rótulo dele também
  document.addEventListener("DOMContentLoaded", () => {
    const bt = document.querySelector(".btn-tema");
    if (bt) bt.setAttribute("aria-label", TXT[idioma].tema);
  });

  desenhar();

  // link direto para uma seção (#en-billing, #pt-cobranca...) abre no idioma dela
  const alvo = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  const artigoAlvo = alvo && alvo.closest("[data-doc-lang]");
  if (artigoAlvo && artigoAlvo.dataset.docLang !== idioma) {
    idioma = artigoAlvo.dataset.docLang;
    desenhar();
    alvo.scrollIntoView();
  }
})();
