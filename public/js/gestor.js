/* =====================================================================
   Painel do Gestor: visão geral, candidatos, cargos/funções,
   matriz de gaps consolidada e configurações.
   Textos da interface: tg(chave) de i18n-gestor.js (pt, en, es).
   ===================================================================== */

const app = document.getElementById("app");
let cargos = [];
let candidatos = [];
let abaAtiva = "visao";
let painelAtivo = false;     // true depois do login (abas visíveis)
let telaAtual = null;        // função que redesenha a tela de login/setup atual
let pipelineAberto = null;   // { vagaId, modo } quando o pipeline de uma vaga está aberto
let idiomaEscolhidoSemLogin = false;

// ------------------------------------------------ API
async function api(caminho, opcoes = {}) {
  const headers = { "Content-Type": "application/json", "X-Idioma": idiomaGestor };
  const token = localStorage.getItem("gestor_token");
  if (token) headers["X-Gestor-Token"] = token;
  const resp = await fetch(caminho, {
    method: opcoes.method || "GET",
    headers,
    body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
  });
  const dados = await resp.json().catch(() => ({}));
  if (resp.status === 401 && caminho !== "/api/gestor/login") {
    localStorage.removeItem("gestor_token");
    telaLogin();
    throw new Error(dados.erro || tg("erro_sessao"));
  }
  if (!resp.ok) throw new Error(dados.erro || tg("erro_comunicacao"));
  return dados;
}

// cabeçalhos dos downloads feitos com fetch direto (currículo, PDF)
function headersDownload() {
  return { "X-Gestor-Token": localStorage.getItem("gestor_token") || "", "X-Idioma": idiomaGestor };
}

async function carregarDados() {
  const [rc, rl] = await Promise.all([api("/api/gestor/cargos"), api("/api/gestor/candidatos")]);
  cargos = rc.cargos;
  candidatos = rl.candidatos;
}

// ------------------------------------------------ idioma do painel
// Uma única configuração: localStorage "idioma" (a mesma da aba de voz)
// e, com sessão aberta, o idioma salvo no servidor (e-mails do gestor).
function trocarIdiomaPainel(lang) {
  const cod = normalizarIdiomaGestor(lang);
  if (!cod) return;
  definirIdiomaGestor(cod);
  if (localStorage.getItem("gestor_token")) {
    const info = infoGestor();
    if (info.nome) {
      info.idioma = cod;
      localStorage.setItem("gestor_info", JSON.stringify(info));
    }
    api("/api/gestor/idioma", { method: "POST", body: { idioma: cod } }).catch(() => {});
  } else {
    idiomaEscolhidoSemLogin = true;
  }
  redesenharTelaAtual();
}

function redesenharTelaAtual() {
  atualizarTopo();
  if (!painelAtivo) {
    if (telaAtual) telaAtual();
    return;
  }
  // formulário do diagnóstico aberto: redesenha mantendo o que já foi digitado
  if (abaAtiva === "diagnostico" && typeof diagRedesenharFormulario === "function" && diagRedesenharFormulario()) {
    desenharAbas();
    return;
  }
  desenharPainel();
}

// os botões PT/EN/ES da aba de voz também trocam o idioma do painel
document.addEventListener("click", (ev) => {
  const b = ev.target.closest && ev.target.closest("[data-voz-idioma]");
  if (!b) return;
  const cod = normalizarIdiomaGestor(b.dataset.vozIdioma);
  if (!cod || cod === idiomaGestor) return;
  setTimeout(() => trocarIdiomaPainel(cod), 0);
});

function atualizarTopo() {
  const sub = document.querySelector(".topbar .sub");
  if (!sub) return;
  const info = infoGestor();
  if (painelAtivo && info.nome) {
    const partes = [info.nome];
    if (info.empresa && info.empresa.nome) partes.push(info.empresa.nome);
    if (info.local) partes.push(info.local);
    if (info.admin && info.nome !== "Administrador") partes.push(tg("administrador"));
    sub.textContent = partes.join(" · ");
  } else {
    sub.textContent = tg("topo_sub");
  }
}

function salvarSessao(r) {
  localStorage.setItem("gestor_token", r.token);
  localStorage.setItem("gestor_info", JSON.stringify({
    nome: r.nome, login: r.login, local: r.local, admin: r.admin,
    modulos: r.modulos || [], empresa: r.empresa || null, idioma: r.idioma || "",
  }));
  const servidor = normalizarIdiomaGestor(r.idioma);
  if (idiomaEscolhidoSemLogin) {
    // escolheu o idioma na tela de login: vale também para os e-mails
    if (servidor !== idiomaGestor) {
      api("/api/gestor/idioma", { method: "POST", body: { idioma: idiomaGestor } }).catch(() => {});
    }
  } else if (!idiomaGestorSalvo() && servidor) {
    definirIdiomaGestor(servidor);
  }
  idiomaEscolhidoSemLogin = false;
}

// ------------------------------------------------ login
function telaLogin() {
  painelAtivo = false;
  telaAtual = telaLogin;
  atualizarTopo();
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:440px;margin:48px auto">
      <h2 class="icone-titulo">${icone("cadeado")}<span>${tg("login_titulo")}</span></h2>
      <p class="desc">${tg("login_desc")}</p>
      <label class="field">${tg("login")}
        <input type="text" id="login-usuario" placeholder="${tg("login_ph")}" autocomplete="username">
      </label>
      <label class="field">${tg("senha")}
        <input type="password" id="login-senha" placeholder="••••••••" autocomplete="current-password">
      </label>
      <div class="form-erro" id="login-erro"></div>
      <button class="btn block" id="login-entrar">${tg("entrar")}</button>
      <p class="texto-centro" style="margin:14px 0 6px">
        <a href="#" id="link-esqueci" style="color:var(--text-2);font-size:.85rem">${tg("esqueci_senha")}</a>
      </p>
      <p class="texto-centro" style="margin:0;border-top:1px solid var(--line-soft);padding-top:12px">
        <span style="color:var(--muted);font-size:.85rem">${tg("sem_conta")} </span>
        <a href="#" id="link-solicitar" style="color:var(--accent);font-size:.85rem;font-weight:500">${tg("solicitar_acesso")}</a>
      </p>
    </div>`;
  document.getElementById("link-esqueci").addEventListener("click", (ev) => {
    ev.preventDefault();
    telaEsqueciSenha();
  });
  document.getElementById("link-solicitar").addEventListener("click", (ev) => {
    ev.preventDefault();
    telaSolicitarAcesso();
  });
  const entrar = async () => {
    const erro = document.getElementById("login-erro");
    erro.textContent = "";
    try {
      const r = await api("/api/gestor/login", {
        method: "POST",
        body: {
          login: document.getElementById("login-usuario").value.trim(),
          senha: document.getElementById("login-senha").value,
        },
      });
      salvarSessao(r);
      iniciarPainel();
    } catch (e) {
      erro.textContent = e.message;
    }
  };
  document.getElementById("login-entrar").addEventListener("click", entrar);
  ["login-usuario", "login-senha"].forEach((id) =>
    document.getElementById(id).addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") entrar();
    })
  );
}

function telaEsqueciSenha() {
  painelAtivo = false;
  telaAtual = telaEsqueciSenha;
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:440px;margin:48px auto">
      <h2 class="icone-titulo">${icone("chave")}<span>${tg("esq_titulo")}</span></h2>
      <p class="desc">${tg("esq_desc")}</p>
      <label class="field">${tg("esq_ident")}
        <input type="text" id="esq-ident" placeholder="${tg("esq_ident_ph")}">
      </label>
      <div class="form-erro" id="esq-msg"></div>
      <button class="btn block" id="esq-enviar">${tg("esq_enviar")}</button>
      <p class="texto-centro" style="margin:14px 0 0">
        <a href="#" id="esq-voltar" style="color:var(--text-2);font-size:.85rem">${tg("voltar_login")}</a>
      </p>
    </div>`;
  document.getElementById("esq-voltar").addEventListener("click", (ev) => {
    ev.preventDefault();
    telaLogin();
  });
  document.getElementById("esq-enviar").addEventListener("click", async () => {
    const msg = document.getElementById("esq-msg");
    msg.style.color = "var(--err)";
    msg.textContent = "";
    try {
      await api("/api/gestor/esqueci-senha", {
        method: "POST",
        body: { login: document.getElementById("esq-ident").value.trim() },
      });
      msg.style.color = "var(--ok)";
      msg.textContent = tg("esq_ok");
    } catch (e) {
      msg.textContent = e.message;
    }
  });
}

function telaSolicitarAcesso() {
  painelAtivo = false;
  telaAtual = telaSolicitarAcesso;
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:460px;margin:48px auto">
      <h2 class="icone-titulo">${icone("usuario")}<span>${tg("solicitar_acesso")}</span></h2>
      <p class="desc">${tg("sol_desc")}</p>
      <label class="field">${tg("nome_completo")}
        <input type="text" id="sol-nome" placeholder="${tg("seu_nome_ph")}">
      </label>
      <label class="field">${tg("sol_login")}
        <input type="text" id="sol-login" placeholder="${tg("login_ph")}" autocomplete="username">
      </label>
      <label class="field">${tg("email")}
        <input type="email" id="sol-email" placeholder="${tg("email_ph")}" autocomplete="email">
      </label>
      <label class="field">${tg("sol_local")} <span class="hint">${tg("opcional")}</span>
        <input type="text" id="sol-local" placeholder="${tg("local_ph")}">
      </label>
      <label class="field">${tg("senha_min")}
        <input type="password" id="sol-senha" autocomplete="new-password">
      </label>
      <div class="form-erro" id="sol-msg"></div>
      <button class="btn block" id="sol-enviar">${tg("sol_enviar")}</button>
      <p class="texto-centro" style="margin:14px 0 0">
        <a href="#" id="sol-voltar" style="color:var(--text-2);font-size:.85rem">${tg("voltar_login")}</a>
      </p>
    </div>`;
  document.getElementById("sol-voltar").addEventListener("click", (ev) => {
    ev.preventDefault();
    telaLogin();
  });
  document.getElementById("sol-enviar").addEventListener("click", async () => {
    const msg = document.getElementById("sol-msg");
    msg.style.color = "var(--err)";
    msg.textContent = "";
    try {
      await api("/api/gestor/solicitar-acesso", {
        method: "POST",
        body: {
          nome: document.getElementById("sol-nome").value.trim(),
          login: document.getElementById("sol-login").value.trim(),
          email: document.getElementById("sol-email").value.trim(),
          local: document.getElementById("sol-local").value.trim(),
          senha: document.getElementById("sol-senha").value,
          // a solicitação vale para a empresa do link recebido (?e=empresa)
          empresa: new URLSearchParams(location.search).get("e") || "",
        },
      });
      const telaEnviada = () => {
        app.innerHTML = `
          <div class="card texto-centro" style="max-width:460px;margin:48px auto">
            <div class="selo-final">${icone("check")}</div>
            <h2>${tg("sol_enviada")}</h2>
            <p class="desc">${tg("sol_enviada_desc")}</p>
            <button class="btn" id="sol-ok">${tg("voltar_login")}</button>
          </div>`;
        document.getElementById("sol-ok").addEventListener("click", telaLogin);
      };
      telaAtual = telaEnviada;
      telaEnviada();
    } catch (e) {
      msg.textContent = e.message;
    }
  });
}

function telaRedefinirSenha(token) {
  painelAtivo = false;
  telaAtual = () => telaRedefinirSenha(token);
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:440px;margin:48px auto">
      <h2 class="icone-titulo">${icone("cadeado")}<span>${tg("red_titulo")}</span></h2>
      <p class="desc">${tg("red_desc")}</p>
      <label class="field">${tg("nova_senha_min")}
        <input type="password" id="red-senha" autocomplete="new-password">
      </label>
      <label class="field">${tg("red_confirmar")}
        <input type="password" id="red-senha2" autocomplete="new-password">
      </label>
      <div class="form-erro" id="red-msg"></div>
      <button class="btn block" id="red-salvar">${tg("red_salvar")}</button>
    </div>`;
  document.getElementById("red-salvar").addEventListener("click", async () => {
    const msg = document.getElementById("red-msg");
    msg.style.color = "var(--err)";
    msg.textContent = "";
    const senha = document.getElementById("red-senha").value;
    if (senha !== document.getElementById("red-senha2").value) {
      msg.textContent = tg("senhas_diferentes");
      return;
    }
    try {
      await api("/api/gestor/redefinir-senha", {
        method: "POST",
        body: { token, nova: senha },
      });
      history.replaceState({}, "", "/gestor");
      msg.style.color = "var(--ok)";
      msg.textContent = tg("red_ok");
      setTimeout(telaLogin, 1500);
    } catch (e) {
      msg.textContent = e.message;
    }
  });
}

function telaSetup() {
  painelAtivo = false;
  telaAtual = telaSetup;
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:480px;margin:48px auto">
      <h2 class="icone-titulo">${icone("usuario")}<span>${tg("st_titulo")}</span></h2>
      <p class="desc">${tg("st_desc")}</p>
      <label class="field">${tg("st_nome")}
        <input type="text" id="st-nome" placeholder="${tg("nome_completo")}">
      </label>
      <label class="field">${tg("login")}
        <input type="text" id="st-login" placeholder="${tg("st_login_ph")}" autocomplete="username">
      </label>
      <label class="field">${tg("st_email")} <span class="hint">${tg("st_email_hint")}</span>
        <input type="email" id="st-email" placeholder="${tg("email_ph")}" autocomplete="email">
      </label>
      <label class="field">${tg("senha_min")}
        <input type="password" id="st-senha" autocomplete="new-password">
      </label>
      <label class="field">${tg("st_confirmar")}
        <input type="password" id="st-senha2" autocomplete="new-password">
      </label>
      <div class="form-erro" id="st-erro"></div>
      <button class="btn block" id="st-criar">${tg("st_criar")}</button>
    </div>`;
  document.getElementById("st-criar").addEventListener("click", async () => {
    const erro = document.getElementById("st-erro");
    erro.textContent = "";
    const senha = document.getElementById("st-senha").value;
    if (senha !== document.getElementById("st-senha2").value) {
      erro.textContent = tg("senhas_diferentes");
      return;
    }
    try {
      const r = await api("/api/gestor/setup", {
        method: "POST",
        body: {
          nome: document.getElementById("st-nome").value.trim(),
          login: document.getElementById("st-login").value.trim(),
          email: document.getElementById("st-email").value.trim(),
          senha,
        },
      });
      salvarSessao(r);
      iniciarPainel();
    } catch (e) {
      erro.textContent = e.message;
    }
  });
}

function infoGestor() {
  try {
    return JSON.parse(localStorage.getItem("gestor_info")) || {};
  } catch (e) {
    return {};
  }
}

document.getElementById("btn-sair").addEventListener("click", () => {
  localStorage.removeItem("gestor_token");
  localStorage.removeItem("gestor_info");
  telaLogin();
});

// ------------------------------------------------ estrutura do painel
async function iniciarPainel() {
  document.getElementById("btn-sair").classList.remove("oculto");
  painelAtivo = true;
  telaAtual = null;
  atualizarTopo();
  await carregarDados();
  desenharPainel();
  // link direto vindo dos e-mails: /gestor#candidato=ID
  const direto = location.hash.match(/^#candidato=(\d+)$/);
  if (direto) {
    history.replaceState(null, "", location.pathname);
    abrirDetalheCandidato(Number(direto[1]));
  }
}

async function secaoMarca(el) {
  const r = await api("/api/gestor/empresa/marca");
  const admin = !!infoGestor().admin;
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("engrenagem")}<span>${tg("marca_titulo")}</span></h2>
      <div class="grid cols-2">
        <div>
          <h3>${tg("marca_logo")}</h3>
          <p class="desc" style="font-size:.82rem">${tg("marca_logo_desc")}</p>
          <div id="marca-preview" style="background:#fff;border:1px solid var(--line, #e4e9f0);border-radius:12px;padding:14px;min-height:60px;display:flex;align-items:center">
            ${r.logo_url ? `<img src="${esc(r.logo_url)}" alt="" style="max-height:56px;max-width:240px">` : `<span class="desc">${tg("marca_sem_logo")}</span>`}
          </div>
          ${admin ? `<div class="linha-acoes mt">
            <label class="btn secondary small" style="cursor:pointer">${tg("marca_enviar")}<input type="file" id="marca-arquivo" accept="image/png,image/jpeg" style="display:none"></label>
            ${r.logo_url ? `<button class="btn secondary small" id="marca-remover">${tg("remover")}</button>` : ""}
          </div>` : `<p class="desc" style="font-size:.8rem">${tg("marca_so_admin")}</p>`}
        </div>
        <div>
          <label class="field">${tg("marca_idioma")}
            <select id="marca-idioma">
              ${IDIOMAS_GESTOR.map((v) => `<option value="${v}" ${idiomaGestor === v ? "selected" : ""}>${NOMES_IDIOMAS_GESTOR[v]}</option>`).join("")}
            </select>
          </label>
          <p class="desc" style="font-size:.8rem">${tg("marca_idioma_desc")}</p>
        </div>
      </div>
      <div class="form-erro" id="marca-erro"></div>
    </div>`;
  const erro = document.getElementById("marca-erro");
  const mostrar = (msg, ok) => { erro.style.color = ok ? "var(--ok)" : "var(--err)"; erro.textContent = msg; };
  document.getElementById("marca-idioma").addEventListener("change", (ev) => {
    trocarIdiomaPainel(ev.target.value);
  });
  const arquivo = document.getElementById("marca-arquivo");
  if (arquivo) arquivo.addEventListener("change", () => {
    const f = arquivo.files[0];
    if (!f) return;
    const leitor = new FileReader();
    leitor.onload = async () => {
      try {
        await api("/api/gestor/empresa/logo", { method: "POST", body: { filename: f.name, data: String(leitor.result).split(",")[1] } });
        secaoMarca(el);
      } catch (e) { mostrar(e.message); }
    };
    leitor.readAsDataURL(f);
  });
  const remover = document.getElementById("marca-remover");
  if (remover) remover.addEventListener("click", async () => {
    try {
      await api("/api/gestor/empresa/logo", { method: "POST", body: { remover: true } });
      secaoMarca(el);
    } catch (e) { mostrar(e.message); }
  });
}

function listaAbas() {
  const abas = [
    ["visao", tg("aba_visao")],
    ["vagas", tg("aba_vagas")],
    ["candidatos", tg("aba_candidatos")],
    ["cargos", tg("aba_cargos")],
    ["matriz", tg("aba_matriz")],
    ["relatorios", tg("aba_relatorios")],
    ["guia", tg("aba_guia")],
    ["config", tg("aba_config")],
  ];
  if ((infoGestor().modulos || []).includes("diagnostico")) {
    abas.splice(6, 0, ["diagnostico", tg("aba_diagnostico")]);
  }
  if (typeof vozModuloAtivo === "function" && vozModuloAtivo()) {
    abas.splice(3, 0, ["voz", vt("aba")]);
  }
  return abas;
}

function htmlAbas() {
  return listaAbas().map(([id, rot]) =>
    `<button class="tab ${abaAtiva === id ? "ativa" : ""}" data-aba="${id}">${rot}</button>`).join("");
}

function ligarAbas() {
  app.querySelectorAll(".tabs-painel .tab").forEach((t) =>
    t.addEventListener("click", () => {
      abaAtiva = t.dataset.aba;
      pipelineAberto = null;
      desenharPainel();
    })
  );
}

// redesenha só a barra de abas (o conteúdo da aba fica como está)
function desenharAbas() {
  const barra = app.querySelector(".tabs-painel");
  if (!barra) return;
  barra.innerHTML = htmlAbas();
  ligarAbas();
}

function desenharPainel() {
  app.innerHTML = `
    <div class="tabs tabs-painel">${htmlAbas()}</div>
    <div id="conteudo"></div>`;
  ligarAbas();
  const conteudo = document.getElementById("conteudo");
  if (abaAtiva === "visao") abaVisao(conteudo);
  if (abaAtiva === "vagas") {
    if (pipelineAberto) telaPipeline(conteudo, pipelineAberto.vagaId, pipelineAberto.modo);
    else abaVagas(conteudo);
  }
  if (abaAtiva === "candidatos") abaCandidatos(conteudo);
  if (abaAtiva === "cargos") abaCargos(conteudo);
  if (abaAtiva === "matriz") abaMatriz(conteudo);
  if (abaAtiva === "relatorios") abaRelatorios(conteudo);
  if (abaAtiva === "guia") abaGuia(conteudo);
  if (abaAtiva === "diagnostico") abaDiagnostico(conteudo);
  if (abaAtiva === "voz") abaVoz(conteudo);
  if (abaAtiva === "config") abaConfig(conteudo);
}

// ------------------------------------------------ relatórios
async function abaRelatorios(el) {
  const r = await api("/api/gestor/relatorios");
  const barra = (rotulo, valor, maximo, cor) => `
    <div class="perfil-barra">
      <div class="rotulo">${esc(rotulo)}</div>
      <div class="trilha"><div class="valor" style="width:${maximo ? Math.round(100 * valor / maximo) : 0}%;background:${cor || "var(--accent-grad)"}"></div></div>
      <div class="num">${fmtNum(valor)}</div>
    </div>`;

  const funilHtml = r.funil.map((f) => {
    const ativos = f.total - f.etapas.reprovado;
    return `
      <div class="card">
        <h2 style="font-size:1.05rem">${esc(f.vaga)}
          ${f.status === "aberta" ? '<span class="badge ok">' + tg("status_aberta") + "</span>" : '<span class="badge tipo">' + esc(nomeStatusVaga(f.status)) + "</span>"}</h2>
        <p class="desc">${tg("rel_funil_resumo", { total: fmtNum(f.total), ativos: fmtNum(ativos), reprovados: fmtNum(f.etapas.reprovado) })}</p>
        <div class="perfil-barras">
          ${barra(tg("rel_inscritos"), f.total, Math.max(f.total, 1))}
          ${barra(tg("rel_avaliacoes_mais"), f.etapas.avaliacoes + f.etapas.entrevista + f.etapas.proposta + f.etapas.contratado, Math.max(f.total, 1))}
          ${barra(tg("rel_entrevista_mais"), f.etapas.entrevista + f.etapas.proposta + f.etapas.contratado, Math.max(f.total, 1))}
          ${barra(tg("rel_proposta_mais"), f.etapas.proposta + f.etapas.contratado, Math.max(f.total, 1))}
          ${barra(tg("rel_contratados"), f.etapas.contratado, Math.max(f.total, 1), "var(--ok)")}
        </div>
      </div>`;
  }).join("");

  const distHtml = (titulo, dist, perfis) => {
    const chaves = Object.keys(dist);
    if (!chaves.length) return "";
    const maximo = Math.max(...chaves.map((k) => dist[k]));
    return `<div class="card"><h2 style="font-size:1.05rem">${titulo}</h2>
      <div class="perfil-barras">
        ${chaves.sort((a, b) => dist[b] - dist[a]).map((k) =>
          barra(perfis[k] ? perfis[k].nome : k, dist[k], maximo,
                perfis[k] ? perfis[k].cor : null)).join("")}
      </div></div>`;
  };

  const maxMes = Math.max(...r.por_mes.map((m2) => m2.total), 1);

  el.innerHTML = `
    <div class="metricas">
      <div class="metrica"><div class="num">${fmtNum(r.total_candidatos)}</div><div class="rot">${tg("rel_m_banco")}</div></div>
      <div class="metrica"><div class="num">${fmtNum(r.avaliacoes_completas)}</div><div class="rot">${tg("m_avaliacoes_completas")}</div></div>
      <div class="metrica"><div class="num">${r.total_candidatos ? Math.round(100 * r.avaliacoes_completas / r.total_candidatos) + "%" : "0%"}</div><div class="rot">${tg("rel_m_conclusao")}</div></div>
      <div class="metrica"><div class="num">${fmtNum(r.contratados)}</div><div class="rot">${tg("rel_contratados")}</div></div>
      <div class="metrica"><div class="num">${r.tempo_medio_contratacao != null ? tg("rel_dias", { n: fmtNum(r.tempo_medio_contratacao) }) : "…"}</div><div class="rot">${tg("rel_m_tempo")}</div></div>
    </div>
    ${r.por_mes.length ? `<div class="card"><h2 style="font-size:1.05rem">${tg("rel_por_mes")}</h2>
      <div class="perfil-barras">${r.por_mes.map((m2) => barra(fmtMes(m2.mes), m2.total, maxMes)).join("")}</div></div>` : ""}
    ${funilHtml || '<div class="card"><p class="desc">' + tg("rel_sem_vagas") + "</p></div>"}
    <div class="grid cols-2">
      ${distHtml(tg("rel_disc_banco"), r.disc, DISC_PERFIS)}
      ${distHtml(tg("rel_base_banco"), r.base, BASE_PERFIS)}
    </div>`;
}

// ------------------------------------------------ guia do gestor
function abaGuia(el) {
  const cartaoPerfil = (p, letra) => `
    <div class="card" style="margin-bottom:0">
      <h2 class="icone-titulo" style="font-size:1.05rem">${p.ic ? icone(p.ic) : ""}<span>${esc(p.nome)}${letra ? " (" + letra + ")" : ""}</span></h2>
      <p style="font-size:.9rem;color:var(--text-2)">${esc(p.resumo)}</p>
    </div>`;
  const nomesDisc = ["D", "I", "S", "C"].map((k) => DISC_PERFIS[k].nome);
  const nomesBase = ["B", "A", "S", "E"].map((k) => BASE_PERFIS[k].nome);
  const listaNomes = (nomes) => tg("lista_e", { inicio: nomes.slice(0, -1).join(", "), fim: nomes[nomes.length - 1] });

  el.innerHTML = `
    <div class="card">
      <h2>${tg("g_titulo")}</h2>
      <p class="desc">${tg("g_desc")}</p>
    </div>

    <div class="card">
      ${tituloIcone("camadas", tg("g_disc_titulo"))}
      <p class="desc">${tg("g_disc_desc", { nomes: listaNomes(nomesDisc) })}</p>
      <h3>${tg("g_como_responde")}</h3>
      <p>${tg("g_disc_responde")}</p>
      <h3>${tg("g_como_interpretar")}</h3>
      <p>${tg("g_disc_interpretar")}</p>
      <div class="grid cols-2 mt">
        ${["D", "I", "S", "C"].map((k) => cartaoPerfil(DISC_PERFIS[k], k)).join("")}
      </div>
    </div>

    <div class="card">
      ${tituloIcone("bussola", tg("g_base_titulo"))}
      <p class="desc">${tg("g_base_desc", { nomes: listaNomes(nomesBase) })}</p>
      <h3>${tg("g_como_responde")}</h3>
      <p>${tg("g_base_responde")}</p>
      <h3>${tg("g_como_interpretar")}</h3>
      <p>${tg("g_base_interpretar")}</p>
      <div class="grid cols-2 mt">
        ${["B", "A", "S", "E"].map((k) => cartaoPerfil(BASE_PERFIS[k])).join("")}
      </div>
    </div>

    <div class="card">
      ${tituloIcone("barras", tg("g_auto_titulo"))}
      <p class="desc">${tg("g_auto_desc")}</p>
      <h3>${tg("g_como_responde")}</h3>
      <p>${tg("g_auto_responde", { escala: ESCALA_NIVEIS.map((n) => n.rot.replace(" · ", " ")).join(", ") })}</p>
      <h3>${tg("g_tipos_titulo")}</h3>
      <p>${tg("g_tipos_texto")}</p>
    </div>

    <div class="card">
      ${tituloIcone("matriz", tg("aba_matriz"))}
      <p class="desc">${tg("g_matriz_desc")}</p>
      <h3>${tg("g_como_calculada")}</h3>
      <p>${tg("g_matriz_calculo", {
        apto: '<span class="badge ok">' + tg("r_apto") + "</span>",
        desenv: '<span class="badge warn">' + tg("r_desenv") + "</span>",
        alto: '<span class="badge err">' + tg("r_gap_alto") + "</span>",
      })}</p>
      <h3>${tg("r_plano_titulo_guia")}</h3>
      <p>${tg("g_plano_texto")}</p>
    </div>

    <div class="card">
      ${tituloIcone("usuarios", tg("g_entrevista_titulo"))}
      <h3>${tg("g_roteiro_titulo")}</h3>
      <p>${tg("g_roteiro_texto")}</p>
      <h3>${tg("g_quiz_titulo")}</h3>
      <p>${tg("g_quiz_texto")}</p>
      <h3>${tg("g_pipeline_titulo")}</h3>
      <p>${tg("g_pipeline_texto", { etapas: listaNomes(ETAPAS_GESTOR.map(nomeEtapa)) })}</p>
    </div>

    <div class="card">
      ${tituloIcone("alvo", tg("g_match_titulo"))}
      <p class="desc">${tg("g_match_desc")}</p>
      <h3>${tg("g_como_calculado")}</h3>
      <p>${tg("g_match_calculo")}</p>
      <h3>${tg("g_como_usar")}</h3>
      <p>${tg("g_match_usar")}</p>
    </div>`;
}

// ------------------------------------------------ visão geral
function abaVisao(el) {
  const comDisc = candidatos.filter((c) => c.testes.disc).length;
  const comBase = candidatos.filter((c) => c.testes.base).length;
  const comAuto = candidatos.filter((c) => c.gaps && c.gaps.respondeu_autoavaliacao).length;
  const completos = candidatos.filter(
    (c) => c.testes.disc && c.testes.base && c.gaps && c.gaps.respondeu_autoavaliacao
  ).length;

  el.innerHTML = `
    <div class="card" id="quadro-dia"></div>
    <div class="card" id="agenda-hoje"></div>
    <div class="metricas">
      <div class="metrica"><div class="num">${fmtNum(candidatos.length)}</div><div class="rot">${tg("v_m_cadastrados")}</div></div>
      <div class="metrica"><div class="num">${fmtNum(comDisc)}</div><div class="rot">${tg("v_m_disc")}</div></div>
      <div class="metrica"><div class="num">${fmtNum(comBase)}</div><div class="rot">${tg("v_m_base")}</div></div>
      <div class="metrica"><div class="num">${fmtNum(comAuto)}</div><div class="rot">${tg("v_m_auto")}</div></div>
      <div class="metrica"><div class="num">${fmtNum(completos)}</div><div class="rot">${tg("m_avaliacoes_completas")}</div></div>
      <div class="metrica"><div class="num">${fmtNum(cargos.length)}</div><div class="rot">${tg("v_m_cargos")}</div></div>
    </div>
    <div class="card">
      <h2>${tg("v_ultimos")}</h2>
      ${tabelaCandidatos(candidatos.slice(0, 8))}
    </div>
    <div class="card">
      <h2 class="icone-titulo">${icone("documento")}<span>${tg("v_atividades")}</span></h2>
      <p class="desc">${tg("v_atividades_desc")}</p>
      <div id="feed-atividades"><p class="desc">${tg("carregando")}</p></div>
    </div>`;
  ligarLinhasCandidato(el);
  quadroDoDia(document.getElementById("quadro-dia"));
  if (typeof agendaHoje === "function") agendaHoje(document.getElementById("agenda-hoje")); // agenda de entrevistas (gestor-agenda.js)
  api("/api/gestor/atividades").then((r) => {
    const alvo = document.getElementById("feed-atividades");
    if (!alvo) return;
    if (!r.atividades.length) {
      alvo.innerHTML = '<p class="desc">' + tg("v_sem_atividades") + "</p>";
      return;
    }
    alvo.innerHTML = `<div class="timeline">${r.atividades.map((a) => `
      <div class="timeline-item ${["cadastro", "sistema", "etapa"].includes(a.tipo) ? "destaque" : ""}">
        <div class="quando">${esc(fmtDataHora(a.criado_em))}</div>
        <div class="texto-evento"><strong><a href="#" data-detalhe="${a.candidato_id}" style="color:inherit">${esc(a.candidato_nome)}</a></strong>: ${esc(a.texto)}</div>
      </div>`).join("")}</div>`;
    ligarDetalhes(alvo);
  }).catch(() => {});
}

// ------------------------------------------------ vagas e pipeline
function badgeStatusVaga(status) {
  if (status === "aberta") return '<span class="badge ok">' + tg("status_aberta") + "</span>";
  if (status === "pausada") return '<span class="badge warn">' + tg("status_pausada") + "</span>";
  return '<span class="badge tipo">' + tg("status_encerrada") + "</span>";
}

async function abaVagas(el, vagaAberta) {
  const r = await api("/api/gestor/vagas");
  if (vagaAberta) return telaPipeline(el, vagaAberta);
  pipelineAberto = null;
  el.innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2 class="icone-titulo">${icone("pasta")}<span>${tg("aba_vagas")}</span></h2>
          <p class="desc" style="margin:0">${tg("vg_desc")}</p>
        </div>
        <button class="btn" id="nova-vaga">${tg("vg_nova")}</button>
      </div>
    </div>
    ${r.vagas.map((v) => `
      <div class="card" style="padding:22px 28px">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
          <div>
            <h2 style="font-size:1.1rem;margin-bottom:2px">${esc(v.titulo)}
              ${badgeStatusVaga(v.status)}
            </h2>
            <p class="desc" style="margin:0">${esc(v.cargo_nome)}${v.local ? " · " + esc(v.local) : ""}${v.pais ? " · " + esc(nomePaisGestor(v.pais)) : ""}
              · ${tgn("n_candidatos", v.total)} · ${tg("vg_resumo_etapas", { entrevista: fmtNum(v.etapas.entrevista), contratados: fmtNum(v.etapas.contratado) })}</p>
          </div>
          <div class="linha-acoes" style="margin:0">
            <button class="btn small" data-pipeline="${v.id}">${tg("vg_ver_pipeline")}</button>
            <button class="btn secondary small" data-editar-vaga="${v.id}">${tg("editar")}</button>
            <button class="btn danger small" data-excluir-vaga="${v.id}">${tg("excluir")}</button>
          </div>
        </div>
      </div>`).join("") || '<div class="card"><p class="desc">' + tg("vg_nenhuma") + "</p></div>"}`;

  document.getElementById("nova-vaga").addEventListener("click", () => formVaga(null));
  el.querySelectorAll("[data-editar-vaga]").forEach((b) =>
    b.addEventListener("click", () =>
      formVaga(r.vagas.find((v) => v.id === Number(b.dataset.editarVaga))))
  );
  el.querySelectorAll("[data-excluir-vaga]").forEach((b) =>
    b.addEventListener("click", async () => {
      const v = r.vagas.find((x) => x.id === Number(b.dataset.excluirVaga));
      if (!confirm(tg("vg_confirmar_excluir", { titulo: v.titulo }))) return;
      await api("/api/gestor/vaga/" + v.id, { method: "DELETE" });
      desenharPainel();
    })
  );
  el.querySelectorAll("[data-pipeline]").forEach((b) =>
    b.addEventListener("click", () => telaPipeline(el, Number(b.dataset.pipeline)))
  );
}

function formVaga(v) {
  modalForm(v ? tg("vg_editar") : tg("vg_nova_titulo"), `
    <label class="field">${tg("vg_titulo")}
      <input type="text" id="fv-titulo" value="${v ? esc(v.titulo) : ""}" placeholder="${tg("vg_titulo_ph")}">
    </label>
    <label class="field">${tg("cargo")}
      <select id="fv-cargo">
        ${cargos.map((c) => `<option value="${c.id}" ${v && v.cargo_id === c.id ? "selected" : ""}>${esc(c.nome)}</option>`).join("")}
      </select>
    </label>
    <label class="field">${tg("local")} <span class="hint">${tg("vg_local_hint")}</span>
      <input type="text" id="fv-local" value="${v ? esc(v.local) : ""}" placeholder="${tg("local_ph")}">
    </label>
    <label class="field">${tg("vg_pais")}
      <select id="fv-pais">
        <option value="">${tg("vg_selecione_pais")}</option>
        ${PAISES.map((pa) => `<option value="${pa}" ${v && v.pais === pa ? "selected" : ""}>${esc(nomePaisGestor(pa))}</option>`).join("")}
      </select>
    </label>
    <label class="field">${tg("descricao")}
      <textarea id="fv-desc" rows="3">${v ? esc(v.descricao) : ""}</textarea>
    </label>
    <label class="field">${tg("status")}
      <select id="fv-status">
        ${["aberta", "pausada", "encerrada"].map((s) =>
          `<option value="${s}" ${v && v.status === s ? "selected" : ""}>${nomeStatusVaga(s)}</option>`).join("")}
      </select>
    </label>`,
    async (f) => {
      await api("/api/gestor/vaga", {
        method: "POST",
        body: {
          id: v ? v.id : undefined,
          titulo: f.querySelector("#fv-titulo").value.trim(),
          cargo_id: Number(f.querySelector("#fv-cargo").value),
          local: f.querySelector("#fv-local").value.trim(),
          pais: f.querySelector("#fv-pais").value,
          descricao: f.querySelector("#fv-desc").value.trim(),
          status: f.querySelector("#fv-status").value,
        },
      });
    });
}

async function telaPipeline(el, vagaId, modo) {
  const r = await api("/api/gestor/vaga/" + vagaId + "/pipeline");
  modo = modo || "kanban";
  pipelineAberto = { vagaId, modo };
  const porEtapa = {};
  r.etapas.forEach((e) => { porEtapa[e] = []; });
  r.candidaturas.forEach((c) => porEtapa[c.etapa].push(c));
  const etapaNome = (e) => esc(nomeEtapa(e, r.nomes_etapas && r.nomes_etapas[e]));

  const cartao = (c) => `
    <div class="kanban-card" draggable="true" data-candidatura="${c.candidatura_id}">
      <div class="nome-card">${linkCandidato(c.candidato_id, c.nome)}</div>
      <div class="sub-card">${c.local ? esc(c.local) : esc(c.email)}</div>
      ${c.match != null ? `<div class="match-card">${tg("pp_match_card", { n: c.match })}</div>` : ""}
      ${c.etapa === "reprovado" && c.motivo_reprovacao ? `<div class="sub-card">${esc(c.motivo_reprovacao)}</div>` : ""}
      <div class="linha-acoes" style="margin-top:8px;gap:6px">
        <button class="btn ghost small" data-detalhe="${c.candidato_id}" style="padding:4px 10px">${tg("relatorio")}</button>
      </div>
      <select data-mover="${c.candidatura_id}" title="${tg("pp_mover_title")}">
        ${r.etapas.map((e) => `<option value="${e}" ${c.etapa === e ? "selected" : ""}>${etapaNome(e)}</option>`).join("")}
      </select>
    </div>`;

  el.innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
        <div>
          <h2>${esc(r.vaga.titulo)}</h2>
          <p class="desc" style="margin:0">${esc(r.vaga.cargo_nome)}${r.vaga.local ? " · " + esc(r.vaga.local) : ""} · ${tgn("n_candidatos", r.candidaturas.length)}</p>
        </div>
        <div class="linha-acoes" style="margin:0">
          <button class="btn ghost small" id="pp-voltar">${tg("pp_voltar")}</button>
          <button class="btn ${modo === "kanban" ? "" : "secondary"} small" id="pp-kanban">${tg("pp_pipeline")}</button>
          <button class="btn ${modo === "ranking" ? "" : "secondary"} small" id="pp-ranking">${tg("pp_ranking")}</button>
          <button class="btn secondary small" id="pp-adicionar">${tg("pp_adicionar")}</button>
        </div>
      </div>
    </div>
    ${modo === "kanban" ? `
      <div class="kanban">
        ${r.etapas.map((e) => `
          <div class="kanban-col" data-etapa="${e}">
            <div class="titulo-col"><span>${etapaNome(e)}</span><span>${porEtapa[e].length}</span></div>
            ${porEtapa[e].map(cartao).join("")}
          </div>`).join("")}
      </div>
      <p class="desc mt">${tg("pp_dica")}</p>
      <div id="radar-talentos"></div>`
    : `
      <div class="card">
        <div class="tabela-wrap">
          <table class="tabela">
            <thead><tr><th>#</th><th>${tg("candidato")}</th><th>${tg("local")}</th><th class="num">${tg("match")}</th><th class="num">${tg("pp_etapa")}</th><th></th></tr></thead>
            <tbody>
              ${r.candidaturas.map((c, i) => `
                <tr data-linha-cand="${c.candidato_id}">
                  <td>${tg("ordinal", { n: i + 1 })}</td>
                  <td><strong>${linkCandidato(c.candidato_id, c.nome)}</strong><br><span style="color:var(--muted);font-size:.78rem">${esc(c.email)}</span></td>
                  <td>${c.local ? esc(c.local) : "·"}</td>
                  <td class="num">${c.match != null ? `<strong>${c.match}%</strong>` : "·"}</td>
                  <td class="num"><span class="badge ${c.etapa === "reprovado" ? "err" : c.etapa === "contratado" ? "ok" : "neutral"}">${etapaNome(c.etapa)}</span></td>
                  <td class="num"><button class="btn secondary small" data-detalhe="${c.candidato_id}">${tg("relatorio")}</button></td>
                </tr>`).join("")}
            </tbody>
          </table>
        </div>
      </div>`}`;

  // radar de talentos: quem já está no banco e tem match alto com esta vaga
  if (modo === "kanban") {
    api("/api/gestor/vaga/" + vagaId + "/sugestoes").then((s) => {
      const alvo = document.getElementById("radar-talentos");
      if (!alvo || !s.sugestoes.length) return;
      alvo.innerHTML = `
        <div class="card" style="margin-top:18px">
          <h2 class="icone-titulo">${icone("alvo")}<span>${tg("radar_titulo")}</span></h2>
          <p class="desc">${tgn("radar_desc", s.sugestoes.length)}</p>
          <div class="tabela-wrap"><table class="tabela">
            <tbody>
              ${s.sugestoes.map((g) => `
                <tr data-linha-cand="${g.candidato_id}">
                  <td><strong>${linkCandidato(g.candidato_id, g.nome)}</strong>${g.local ? ` <span style="color:var(--muted);font-size:.8rem">· ${esc(g.local)}</span>` : ""}</td>
                  <td class="num"><strong>${g.match}%</strong></td>
                  <td class="num">
                    <button class="btn ghost small" data-detalhe="${g.candidato_id}">${tg("relatorio")}</button>
                    <button class="btn secondary small" data-radar-add="${g.candidato_id}">${tg("radar_adicionar")}</button>
                  </td>
                </tr>`).join("")}
            </tbody>
          </table></div>
        </div>`;
      ligarDetalhes(alvo);
      alvo.querySelectorAll("[data-radar-add]").forEach((b) =>
        b.addEventListener("click", async () => {
          await api("/api/gestor/candidatura/adicionar", {
            method: "POST",
            body: { candidato_id: Number(b.dataset.radarAdd), vaga_id: vagaId },
          });
          telaPipeline(el, vagaId, modo);
        })
      );
    }).catch(() => {});
  }

  document.getElementById("pp-voltar").addEventListener("click", () => abaVagas(el));
  document.getElementById("pp-kanban").addEventListener("click", () => telaPipeline(el, vagaId, "kanban"));
  document.getElementById("pp-ranking").addEventListener("click", () => telaPipeline(el, vagaId, "ranking"));
  document.getElementById("pp-adicionar").addEventListener("click", () => {
    const disponiveis = candidatos.filter(
      (c) => !r.candidaturas.some((x) => x.candidato_id === c.candidato.id)
    );
    if (!disponiveis.length) return alert(tg("pp_todos_na_vaga"));
    modalForm(tg("pp_adicionar_titulo"), `
      <label class="field">${tg("candidato")}
        <select id="ac-cand">
          ${disponiveis.map((c) => `<option value="${c.candidato.id}">${esc(c.candidato.nome)}${c.candidato.local ? " (" + esc(c.candidato.local) + ")" : ""}</option>`).join("")}
        </select>
      </label>`,
      async (f) => {
        await api("/api/gestor/candidatura/adicionar", {
          method: "POST",
          body: { candidato_id: Number(f.querySelector("#ac-cand").value), vaga_id: vagaId },
        });
      });
  });
  ligarDetalhes(el);

  async function mover(candidaturaId, etapa) {
    let motivo = "";
    if (etapa === "reprovado") {
      motivo = prompt(tg("pp_motivo")) || "";
    }
    const notificar = confirm(tg("pp_notificar"));
    const resp = await api("/api/gestor/candidatura", {
      method: "POST",
      body: { id: candidaturaId, etapa, motivo, notificar },
    });
    if (resp.aviso_email) alert(tg("pp_aviso_email", { msg: resp.aviso_email }));
    await carregarDados();
    telaPipeline(el, vagaId, modo);
  }

  el.querySelectorAll("[data-mover]").forEach((sel) =>
    sel.addEventListener("change", () => mover(Number(sel.dataset.mover), sel.value))
  );
  // arrastar e soltar
  el.querySelectorAll(".kanban-card").forEach((card) =>
    card.addEventListener("dragstart", (ev) => {
      ev.dataTransfer.setData("text/plain", card.dataset.candidatura);
    })
  );
  el.querySelectorAll(".kanban-col").forEach((col) => {
    col.addEventListener("dragover", (ev) => { ev.preventDefault(); col.classList.add("arrastando"); });
    col.addEventListener("dragleave", () => col.classList.remove("arrastando"));
    col.addEventListener("drop", (ev) => {
      ev.preventDefault();
      col.classList.remove("arrastando");
      const id = Number(ev.dataTransfer.getData("text/plain"));
      if (!id) return;
      // ignora quando o cartão é solto na mesma coluna de origem
      const cartao = el.querySelector(`.kanban-card[data-candidatura="${id}"]`);
      const etapaOrigem = cartao && cartao.closest(".kanban-col") &&
        cartao.closest(".kanban-col").dataset.etapa;
      if (etapaOrigem === col.dataset.etapa) return;
      mover(id, col.dataset.etapa);
    });
  });
}

// ------------------------------------------------ candidatos
function urlPerfil(valor, rede) {
  const v = valor.trim().replace(/^@/, "");
  if (/^https?:\/\//i.test(v)) return v;
  if (rede === "instagram") return "https://instagram.com/" + v;
  if (v.includes("linkedin.com")) return "https://" + v;
  return "https://linkedin.com/in/" + v;
}

function nomeCargo(id) {
  const c = cargos.find((x) => x.id === id);
  return c ? c.nome : "·";
}

function tabelaCandidatos(lista) {
  if (!lista.length) return "<p class='desc'>" + tg("c_nenhum") + "</p>";
  return `
    <div class="tabela-wrap">
      <table class="tabela">
        <thead><tr>
          <th>${tg("nome")}</th><th>${tg("local")}</th><th>${tg("cargo_interesse")}</th><th class="num">DISC</th>
          <th class="num">B.A.S.E.</th><th class="num">${tg("match")}</th><th class="num">${tg("status")}</th><th></th>
        </tr></thead>
        <tbody>
          ${lista.map((c) => {
            const disc = c.testes.disc ? c.testes.disc.payload.dominante : null;
            const base = c.testes.base ? c.testes.base.payload.dominante : null;
            return `<tr data-linha-cand="${c.candidato.id}">
              <td><strong>${linkCandidato(c.candidato.id, c.candidato.nome)}</strong>
                ${c.candidato.tipo === "interno" ? ' <span class="badge neutral">' + tg("colaborador") + "</span>" : ""}
                <br><span style="color:var(--muted);font-size:.8rem">${esc(c.candidato.email)}</span>
                ${c.candidato.telefone ? `<br><span style="color:var(--muted);font-size:.8rem">${linkTelefone(c.candidato.telefone)}</span>` : ""}
                ${(c.candidato.tags || []).length ? "<br>" + c.candidato.tags.map((t) => `<span class="badge tipo">${esc(t)}</span>`).join(" ") : ""}</td>
              <td>${c.candidato.local ? esc(c.candidato.local) : "·"}</td>
              <td>${esc(nomeCargo(c.candidato.cargo_desejado_id))}</td>
              <td class="num">${disc ? `<span class="badge neutral">${disc} · ${esc(DISC_PERFIS[disc].nome)}</span>` : '<span class="badge tipo">' + tg("pendente") + "</span>"}</td>
              <td class="num">${base ? `<span class="badge neutral">${esc(BASE_PERFIS[base].nome)}</span>` : '<span class="badge tipo">' + tg("pendente") + "</span>"}</td>
              <td class="num">${c.match ? `<strong>${c.match.geral}%</strong>` : "·"}</td>
              <td class="num">${c.gaps && c.gaps.respondeu_autoavaliacao ? badgeStatus(c.gaps.status) : '<span class="badge tipo">·</span>'}</td>
              <td class="num"><button class="btn secondary small" data-detalhe="${c.candidato.id}">${tg("ver_relatorio")}</button></td>
            </tr>`;
          }).join("")}
        </tbody>
      </table>
    </div>`;
}

// nome do candidato como link que abre o relatório
function linkCandidato(id, nome) {
  return `<a href="#" data-detalhe="${id}" style="color:inherit">${esc(nome)}</a>`;
}

// telefone como link tel: (vazio se não houver)
function linkTelefone(tel) {
  if (!tel) return "";
  const numero = String(tel).replace(/[^\d+]/g, "");
  return `<a href="tel:${esc(numero)}" style="color:inherit">${esc(tel)}</a>`;
}

// liga os links/botões [data-detalhe] e as linhas [data-linha-cand] ao relatório do candidato.
// Cada elemento é ligado uma vez só; cliques em botões, links e campos dentro da linha
// não disparam a linha de novo.
function ligarDetalhes(raiz) {
  raiz.querySelectorAll("[data-detalhe]").forEach((b) => {
    if (b.dataset.ligado) return;
    b.dataset.ligado = "1";
    b.addEventListener("click", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      abrirDetalheCandidato(Number(b.dataset.detalhe));
    });
  });
  raiz.querySelectorAll("[data-linha-cand]").forEach((linha) => {
    if (linha.dataset.ligado) return;
    linha.dataset.ligado = "1";
    linha.style.cursor = "pointer";
    linha.addEventListener("click", (ev) => {
      if (ev.target.closest("a, button, select, input, textarea, label")) return;
      if (window.getSelection && String(window.getSelection()).trim()) return; // selecionando texto
      abrirDetalheCandidato(Number(linha.dataset.linhaCand));
    });
  });
}

function ligarLinhasCandidato(el) {
  ligarDetalhes(el);
}

function abaCandidatos(el) {
  const locais = [...new Set(candidatos.map((c) => c.candidato.local).filter(Boolean))].sort();
  const tags = [...new Set(candidatos.flatMap((c) => c.candidato.tags || []))].sort();

  el.innerHTML = `<div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:6px">
      <h2 style="margin:0">${tg("c_banco", { n: fmtNum(candidatos.length) })}</h2>
      <div class="linha-acoes" style="margin:0">
        ${infoGestor().admin ? `<button class="btn small" id="importar-csv">${tg("en_importar")}</button>` : ""}
        ${candidatos.length ? `<button class="btn secondary small" id="exportar-csv">${tg("c_exportar")}</button>` : ""}
      </div>
    </div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0 4px">
      <input type="text" id="ft-busca" placeholder="${tg("c_buscar_ph")}" style="margin:0">
      <select id="ft-local" style="margin:0"><option value="">${tg("c_todos_locais")}</option>
        ${locais.map((l) => `<option value="${esc(l)}">${esc(l)}</option>`).join("")}</select>
      <select id="ft-cargo" style="margin:0"><option value="">${tg("c_todos_cargos")}</option>
        ${cargos.map((c) => `<option value="${c.id}">${esc(c.nome)}</option>`).join("")}</select>
      <select id="ft-tag" style="margin:0"><option value="">${tg("c_todas_tags")}</option>
        ${tags.map((t) => `<option value="${esc(t)}">${esc(t)}</option>`).join("")}</select>
      <select id="ft-match" style="margin:0">
        <option value="">${tg("c_qualquer_match")}</option>
        <option value="80">${tg("c_match_min", { n: 80 })}</option>
        <option value="60">${tg("c_match_min", { n: 60 })}</option>
        <option value="40">${tg("c_match_min", { n: 40 })}</option>
      </select>
      <select id="ft-tipo" style="margin:0">
        <option value="">${tg("c_todos_perfis")}</option>
        <option value="externo">${tg("aba_candidatos")}</option>
        <option value="interno">${tg("c_internos")}</option>
      </select>
      ${typeof talentosFiltrosHtml === "function" ? talentosFiltrosHtml() : ""}
    </div>
    <div id="ft-resultado">${tabelaCandidatos(candidatos)}</div></div>`;

  const aplicar = () => {
    const busca = document.getElementById("ft-busca").value.trim().toLowerCase();
    const local = document.getElementById("ft-local").value;
    const cargo = Number(document.getElementById("ft-cargo").value) || null;
    const tag = document.getElementById("ft-tag").value;
    const matchMin = Number(document.getElementById("ft-match").value) || 0;
    const tipoSel = document.getElementById("ft-tipo").value;
    const filtrados = candidatos.filter((c) => {
      if (busca) {
        const tel = c.candidato.telefone || "";
        const texto = (c.candidato.nome + " " + c.candidato.email + " " + tel).toLowerCase();
        const digitosBusca = busca.replace(/\D/g, "");
        const casaTel = digitosBusca.length >= 3 && tel.replace(/\D/g, "").includes(digitosBusca);
        if (!texto.includes(busca) && !casaTel) return false;
      }
      if (local && c.candidato.local !== local) return false;
      if (cargo && c.candidato.cargo_desejado_id !== cargo) return false;
      if (tag && !(c.candidato.tags || []).includes(tag)) return false;
      if (matchMin && !(c.match && c.match.geral >= matchMin)) return false;
      if (tipoSel && (c.candidato.tipo || "externo") !== tipoSel) return false;
      if (typeof talentosFiltra === "function" && !talentosFiltra(c)) return false; // banco de talentos (gestor-talentos.js)
      return true;
    });
    document.getElementById("ft-resultado").innerHTML = tabelaCandidatos(filtrados);
    ligarLinhasCandidato(el);
    if (typeof talentosDecorarTabela === "function") talentosDecorarTabela(el); // seleção para comparar (gestor-talentos.js)
  };
  ["ft-busca", "ft-local", "ft-cargo", "ft-tag", "ft-match", "ft-tipo"].forEach((id) =>
    document.getElementById(id).addEventListener(id === "ft-busca" ? "input" : "change", aplicar)
  );
  ligarLinhasCandidato(el);
  const btn = document.getElementById("exportar-csv");
  if (btn) btn.addEventListener("click", exportarCandidatosCsv);
  const imp = document.getElementById("importar-csv");
  if (imp) imp.addEventListener("click", () => modalImportarCsv(async () => { await carregarDados(); abaCandidatos(el); }));
  if (typeof talentosLigarAba === "function") talentosLigarAba(el, aplicar); // filtros de voz e comparação (gestor-talentos.js)
}

function exportarCandidatosCsv() {
  const celula = (v) => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
  const linhas = [[
    tg("nome"), tg("email"), tg("telefone"), tg("local"), tg("cargo_interesse"), tg("csv_disc"),
    tg("csv_base"), tg("csv_aderencia"), tg("csv_match"),
    tg("status"), "LinkedIn", "Instagram", tg("csv_cadastro"),
  ]];
  candidatos.forEach((c) => {
    const disc = c.testes.disc ? c.testes.disc.payload.dominante + " " + DISC_PERFIS[c.testes.disc.payload.dominante].nome : "";
    const base = c.testes.base ? BASE_PERFIS[c.testes.base.payload.dominante].nome : "";
    linhas.push([
      c.candidato.nome, c.candidato.email, c.candidato.telefone || "", c.candidato.local,
      nomeCargo(c.candidato.cargo_desejado_id), disc, base,
      c.gaps && c.gaps.respondeu_autoavaliacao ? c.gaps.aderencia : "",
      c.match ? c.match.geral : "",
      c.gaps && c.gaps.respondeu_autoavaliacao
        ? { apto: tg("csv_apto"), desenvolvimento: tg("r_desenv"), gap_alto: tg("r_gap_alto") }[c.gaps.status]
        : "",
      c.candidato.linkedin, c.candidato.instagram,
      (c.candidato.criado_em || "").slice(0, 10),
    ]);
  });
  const csv = "﻿" + linhas.map((l) => l.map(celula).join(";")).join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  a.download = tg("csv_arquivo") + ".csv";
  a.click();
  URL.revokeObjectURL(a.href);
}

async function abrirDetalheCandidato(id) {
  const c = await api("/api/gestor/candidato/" + id);
  const blocos = [];
  if (typeof talentosPreencherFicha === "function") blocos.push('<div class="card" id="bloco-talentos"></div>'); // resumo da ligação e lembrete (gestor-talentos.js)
  if (c.match) blocos.push(`<div class="card">${htmlMatch(c.match, c.gaps ? c.gaps.cargo.nome : "")}</div>`);
  const comVoz = typeof vozModuloAtivo === "function" && vozModuloAtivo();
  if (comVoz) blocos.push('<div class="card" id="bloco-voz"></div>');
  blocos.push('<div class="card" id="bloco-agenda"></div>'); // agenda de entrevistas (gestor-agenda.js)
  if (c.testes.disc) blocos.push(`<div class="card">${htmlResultadoDisc(c.testes.disc.payload)}</div>`);
  if (c.testes.base) blocos.push(`<div class="card">${htmlResultadoBase(c.testes.base.payload)}</div>`);
  if (c.quiz) blocos.push(`<div class="card">${tituloIcone("bloco", tg("quiz_titulo"))}
    <div class="perfil-destaque"><div class="titulo">${tg("quiz_pct", { pct: c.quiz.pct })}</div>
    <div>${tg("quiz_acertos", { acertos: fmtNum(c.quiz.acertos), total: fmtNum(c.quiz.total) })}</div></div></div>`);

  // entrevista estruturada
  const nomeCargoInteresse = nomeCargo(c.candidato.cargo_desejado_id);
  blocos.push(`<div class="card">
    ${tituloIcone("usuarios", tg("ent_titulo"))}
    ${c.entrevista ? `
      <div class="perfil-destaque">
        <div class="titulo">${tg("ent_media", { media: fmtNum(c.entrevista.media, 1), pct: c.entrevista.pct })}</div>
        <div>${tg("ent_avaliada_por", { gestor: esc(c.entrevista.gestor), data: esc(fmtData(c.entrevista.criado_em)) })}</div>
      </div>
      ${c.entrevista.payload.observacao ? `<p>${esc(c.entrevista.payload.observacao)}</p>` : ""}`
      : '<p class="desc">' + tg("ent_nenhuma") + "</p>"}
    <button class="btn secondary small no-print" id="btn-entrevista">${c.entrevista ? tg("ent_registrar_nova") : tg("ent_registrar")}</button>
  </div>`);

  // análise de currículo por IA
  const ia = c.analise_ia;
  blocos.push(`<div class="card">
    ${tituloIcone("relatorio", tg("ia_titulo"))}
    ${ia ? `
      <div class="perfil-destaque">
        <div class="titulo">${tg("ia_aderencia", { pct: ia.aderencia_curriculo })}</div>
        <div>${esc(ia.recomendacao)}</div>
      </div>
      <p>${esc(ia.resumo)}</p>
      <div class="grid cols-2 mt">
        <div><h3>${tg("ia_formacoes")}</h3>
          <ul class="lista-simples">${(ia.formacoes || []).map((f) => `<li>${esc(f)}</li>`).join("") || "<li>" + tg("ia_nenhuma_identificada") + "</li>"}</ul></div>
        <div><h3>${tg("ia_experiencias")}</h3>
          <ul class="lista-simples">${(ia.experiencias || []).map((f) => `<li>${esc(f)}</li>`).join("") || "<li>" + tg("ia_nenhuma_identificada") + "</li>"}</ul></div>
      </div>
      <h3>${tg("r_pontos_fortes")}</h3>
      <ul class="lista-simples">${(ia.pontos_fortes || []).map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      ${(ia.divergencias || []).length ? `
        <h3>${tg("ia_divergencias")}</h3>
        <div class="tabela-wrap"><table class="tabela">
          <thead><tr><th>${tg("r_th_comp")}</th><th>${tg("ia_declarado")}</th><th>${tg("ia_no_curriculo")}</th><th>${tg("ia_comentario")}</th></tr></thead>
          <tbody>${ia.divergencias.map((d) => `
            <tr><td><strong>${esc(d.competencia)}</strong></td><td>${esc(d.nivel_declarado)}</td>
            <td>${esc(d.evidencia_no_curriculo)}</td><td>${esc(d.comentario)}</td></tr>`).join("")}</tbody>
        </table></div>` : "<p>" + tg("ia_sem_divergencias") + "</p>"}`
      : '<p class="desc">' + tg("ia_desc") + "</p>"}
    <div class="linha-acoes no-print">
      <button class="btn secondary small" id="btn-ia" ${c.candidato.curriculo ? "" : `disabled title="${tg("ia_sem_cv")}"`}>${ia ? tg("ia_analisar_novamente") : tg("ia_analisar")}</button>
      <span id="ia-status" class="desc" style="margin:0"></span>
    </div>
  </div>`);

  // recrutamento interno: match com todos os cargos
  if ((c.matches_cargos || []).some((mc) => mc.match != null)) {
    blocos.push(`<div class="card">
      ${tituloIcone("camadas", tg("mob_titulo"))}
      <p class="desc">${tg("mob_desc")}</p>
      <div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>${tg("cargo")}</th><th class="num">${tg("match")}</th></tr></thead>
        <tbody>${c.matches_cargos.map((mc) => `
          <tr><td><strong>${esc(mc.cargo_nome)}</strong>${mc.nivel ? ' <span class="badge tipo">' + esc(nomeNivelCargo(mc.nivel)) + "</span>" : ""}</td>
          <td class="num">${mc.match != null ? `<strong>${mc.match}%</strong>` : "·"}</td></tr>`).join("")}</tbody>
      </table></div>
    </div>`);
  }

  if (c.gaps) blocos.push(`<div class="card">${htmlMatrizGaps(c.gaps)}</div>`);

  // linha do tempo e anotações
  blocos.push(`<div class="card">
    ${tituloIcone("documento", tg("tl_titulo"))}
    <div class="linha-acoes no-print" style="margin-top:4px">
      <input type="text" id="nova-anotacao" placeholder="${tg("tl_ph")}" style="flex:1;min-width:220px;margin:0">
      <button class="btn secondary small" id="btn-anotar">${tg("tl_anotar")}</button>
    </div>
    <div class="timeline">
      ${(c.eventos || []).map((ev) => `
        <div class="timeline-item ${ev.tipo === "anotacao" || ev.tipo === "etapa" ? "destaque" : ""}">
          <div class="quando">${esc(fmtDataHora(ev.criado_em))} · ${esc(ev.autor)}</div>
          <div class="texto-evento">${ev.tipo === "anotacao" ? "<strong>" + tg("tl_anotacao") + "</strong> " : ""}${esc(ev.texto)}</div>
        </div>`).join("") || '<p class="desc">' + tg("tl_nenhum") + "</p>"}
    </div>
  </div>`);
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal">
      <button class="btn ghost small fechar" id="modal-fechar">${icone("fechar")} ${tg("fechar")}</button>
      <h2>${esc(c.candidato.nome)} ${c.candidato.tipo === "interno" ? '<span class="badge neutral">' + tg("colaborador_interno") + "</span>" : ""}</h2>
      <p class="desc">${esc(c.candidato.email)}
        ${c.candidato.telefone ? ` · <strong>${tg("d_tel")}</strong> ${linkTelefone(c.candidato.telefone)}` : ""}
        ${c.candidato.local ? " · " + tg("d_local") + " " + esc(c.candidato.local) : ""}
        ${c.candidato.cargo_atual ? " · " + tg("d_cargo_atual") + " " + esc(c.candidato.cargo_atual) : ""}
        ${c.candidato.funcao ? " · " + tg("d_funcao") + " " + esc(c.candidato.funcao) : ""}
        · ${tg("d_interesse")} ${esc(nomeCargo(c.candidato.cargo_desejado_id))}
        · ${tg("d_cadastro")} ${esc(fmtData(c.candidato.criado_em))}</p>
      <div class="linha-acoes no-print">
        ${c.candidato.linkedin ? `<a class="btn secondary small" target="_blank" rel="noopener" href="${esc(urlPerfil(c.candidato.linkedin, "linkedin"))}">${icone("link")} LinkedIn</a>` : ""}
        ${c.candidato.instagram ? `<a class="btn secondary small" target="_blank" rel="noopener" href="${esc(urlPerfil(c.candidato.instagram, "instagram"))}">${icone("link")} Instagram</a>` : ""}
        ${c.candidato.curriculo ? `<a class="btn secondary small" href="/api/gestor/curriculo/${c.candidato.id}?t=${Date.now()}" id="baixar-cv">${icone("anexo")} ${tg("d_baixar_cv")}</a>` : '<span class="badge tipo">' + tg("d_sem_cv") + "</span>"}
        <button class="btn secondary small" id="btn-email-manual">${tg("d_enviar_email")}</button>
        <button class="btn secondary small" id="btn-relatorio-pdf" data-cand="${c.candidato.id}">${icone("documento")} ${tg("d_relatorio_pdf")}</button>
        <button class="btn danger small" id="btn-anonimizar" title="${tg("d_anonimizar_title")}">${tg("d_anonimizar")}</button>
        <button class="btn danger small" id="excluir-cand">${icone("lixeira")} ${tg("d_excluir")}</button>
      </div>
      <div class="no-print" style="margin:14px 0 4px">
        <span style="font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em">${tg("d_tags")}</span>
        <span id="tags-lista">${(c.candidato.tags || []).map((t) =>
          `<span class="badge tipo" style="margin:0 3px">${esc(t)} <a href="#" data-remover-tag="${esc(t)}" style="color:inherit;text-decoration:none">×</a></span>`).join("")}</span>
        <input type="text" id="nova-tag" list="tags-existentes" placeholder="${tg("d_tag_ph")}"
          style="width:130px;display:inline-block;margin:0 0 0 6px;padding:5px 10px;font-size:.78rem">
        <datalist id="tags-existentes"></datalist>
      </div>
      ${blocos.join("") || "<p class='mt'>" + tg("d_nenhum_teste") + "</p>"}
    </div>`;
  document.body.appendChild(fundo);
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fundo.remove(); });
  fundo.querySelector("#modal-fechar").addEventListener("click", () => fundo.remove());
  if (comVoz) vozPreencherFicha(c.candidato.id, fundo.querySelector("#bloco-voz"));
  if (typeof agendaPreencherFicha === "function") agendaPreencherFicha(c.candidato.id, fundo.querySelector("#bloco-agenda"));
  if (typeof talentosPreencherFicha === "function") talentosPreencherFicha(c.candidato.id, fundo.querySelector("#bloco-talentos")); // gestor-talentos.js
  const baixar = fundo.querySelector("#baixar-cv");
  if (baixar) {
    baixar.addEventListener("click", async (ev) => {
      ev.preventDefault();
      const resp = await fetch("/api/gestor/curriculo/" + c.candidato.id, { headers: headersDownload() });
      if (!resp.ok) return alert(tg("d_erro_cv"));
      const blob = await resp.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = tg("d_arquivo_cv") + "_" + c.candidato.nome.replace(/\s+/g, "_") + ".pdf";
      a.click();
      URL.revokeObjectURL(a.href);
    });
  }
  fundo.querySelector("#excluir-cand").addEventListener("click", async () => {
    if (!confirm(tg("d_confirmar_excluir", { nome: c.candidato.nome }))) return;
    await api("/api/gestor/candidato/" + id, { method: "DELETE" });
    fundo.remove();
    await carregarDados();
    desenharPainel();
  });

  // tags
  api("/api/gestor/tags").then((r) => {
    const dl = fundo.querySelector("#tags-existentes");
    if (dl) dl.innerHTML = r.tags.map((t) => `<option value="${esc(t)}"></option>`).join("");
  }).catch(() => {});
  const salvarTags = async (tags) => {
    await api("/api/gestor/candidato/" + id + "/tags", { method: "POST", body: { tags } });
    await carregarDados();
    fundo.remove();
    abrirDetalheCandidato(id);
  };
  fundo.querySelector("#nova-tag").addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && ev.target.value.trim()) {
      salvarTags([...(c.candidato.tags || []), ev.target.value.trim()]);
    }
  });
  fundo.querySelectorAll("[data-remover-tag]").forEach((lnk) =>
    lnk.addEventListener("click", (ev) => {
      ev.preventDefault();
      salvarTags((c.candidato.tags || []).filter((t) => t !== lnk.dataset.removerTag));
    })
  );

  // e-mail manual
  fundo.querySelector("#btn-email-manual").addEventListener("click", () => {
    modalForm(tg("em_titulo", { nome: c.candidato.nome }), `
      <p class="desc">${tg("em_desc")}</p>
      <label class="field">${tg("assunto")} <input type="text" id="em-assunto"></label>
      <label class="field">${tg("mensagem")} <textarea id="em-corpo" rows="7" placeholder="${tg("em_ph")}"></textarea></label>`,
      async (f) => {
        await api("/api/gestor/email", {
          method: "POST",
          body: {
            candidato_id: id,
            assunto: f.querySelector("#em-assunto").value,
            corpo: f.querySelector("#em-corpo").value,
          },
        });
        fundo.remove();
        abrirDetalheCandidato(id);
      });
  });

  fundo.querySelector("#btn-relatorio-pdf").addEventListener("click", async (ev) => {
    const btn = ev.currentTarget;
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.textContent = tg("gerando");
    try {
      const resp = await fetch("/api/gestor/candidato/" + id + "/relatorio.pdf", { headers: headersDownload() });
      if (!resp.ok) {
        const d = await resp.json().catch(() => ({}));
        throw new Error(d.erro || tg("d_erro_pdf"));
      }
      const blob = await resp.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = tg("d_arquivo_pdf") + "-" + (c.candidato.nome || tg("candidato")).replace(/[^a-z0-9]+/gi, "-").toLowerCase() + ".pdf";
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      alert(e.message);
    }
    btn.disabled = false;
    btn.innerHTML = original;
  });

  // anonimização LGPD
  fundo.querySelector("#btn-anonimizar").addEventListener("click", async () => {
    if (!confirm(tg("d_confirmar_anonimizar", { nome: c.candidato.nome }))) return;
    await api("/api/gestor/candidato/" + id + "/anonimizar", { method: "POST" });
    fundo.remove();
    await carregarDados();
    desenharPainel();
  });

  // anotação
  fundo.querySelector("#btn-anotar").addEventListener("click", async () => {
    const campo = fundo.querySelector("#nova-anotacao");
    if (!campo.value.trim()) return;
    await api("/api/gestor/anotacao", {
      method: "POST",
      body: { candidato_id: id, texto: campo.value.trim() },
    });
    fundo.remove();
    abrirDetalheCandidato(id);
  });

  // scorecard de entrevista
  fundo.querySelector("#btn-entrevista").addEventListener("click", () => {
    const perguntas = (c.perguntas_entrevista || []).length
      ? c.perguntas_entrevista
      : [{ id: 0, texto: tg("sc_geral") }];
    modalForm(tg("sc_titulo", { nome: c.candidato.nome }), `
      <p class="desc">${tg("sc_desc")}${nomeCargoInteresse !== "·" ? " " + tg("sc_roteiro_cargo", { cargo: esc(nomeCargoInteresse) }) : ""}. ${tg("sc_desc2")}</p>
      ${perguntas.map((p) => `
        <div class="comp-item">
          <div class="nome">${esc(p.texto)}</div>
          <div class="escala" data-perg="${p.id}">
            ${[1, 2, 3, 4, 5].map((n) => `<button data-v="${n}">${n}</button>`).join("")}
          </div>
        </div>`).join("")}
      <label class="field mt">${tg("sc_obs")}
        <textarea id="ent-obs" rows="3" placeholder="${tg("sc_obs_ph")}"></textarea>
      </label>`,
      async (f) => {
        const notas = [];
        f.querySelectorAll(".escala[data-perg]").forEach((g) => {
          const ativo = g.querySelector("button.ativo");
          if (ativo) {
            notas.push({
              pergunta_id: Number(g.dataset.perg),
              pergunta: perguntas.find((p) => p.id === Number(g.dataset.perg)).texto,
              nota: Number(ativo.dataset.v),
            });
          }
        });
        await api("/api/gestor/entrevista", {
          method: "POST",
          body: {
            candidato_id: id,
            cargo_id: c.candidato.cargo_desejado_id,
            notas,
            observacao: f.querySelector("#ent-obs").value,
          },
        });
        fundo.remove();
        abrirDetalheCandidato(id);
      });
    document.querySelectorAll(".modal-fundo:last-child .escala[data-perg]").forEach((g) =>
      g.querySelectorAll("button").forEach((b) =>
        b.addEventListener("click", () => {
          g.querySelectorAll("button").forEach((x) => x.classList.remove("ativo"));
          b.classList.add("ativo");
        })
      )
    );
  });

  // análise de currículo por IA
  const btnIa = fundo.querySelector("#btn-ia");
  btnIa.addEventListener("click", async () => {
    const status = fundo.querySelector("#ia-status");
    btnIa.disabled = true;
    status.textContent = tg("ia_analisando");
    try {
      await api("/api/gestor/ia/curriculo/" + id, { method: "POST" });
      fundo.remove();
      abrirDetalheCandidato(id);
    } catch (e) {
      btnIa.disabled = false;
      status.textContent = e.message;
    }
  });
}

// ------------------------------------------------ cargos e funções
function abaCargos(el) {
  el.innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2>${tg("cg_titulo")}</h2>
          <p class="desc" style="margin:0">${tg("cg_desc")}</p>
        </div>
        <button class="btn" id="novo-cargo">${tg("cg_novo")}</button>
      </div>
    </div>
    <div id="lista-cargos">
      ${cargos.map((c) => cartaoCargo(c)).join("") || "<div class='card'><p class='desc'>" + tg("cg_nenhum") + "</p></div>"}
    </div>`;

  document.getElementById("novo-cargo").addEventListener("click", () => formCargo(null));
  el.querySelectorAll("[data-editar-cargo]").forEach((b) =>
    b.addEventListener("click", () => formCargo(cargos.find((c) => c.id === Number(b.dataset.editarCargo))))
  );
  el.querySelectorAll("[data-excluir-cargo]").forEach((b) =>
    b.addEventListener("click", async () => {
      const c = cargos.find((x) => x.id === Number(b.dataset.excluirCargo));
      if (!confirm(tg("cg_confirmar_excluir", { nome: c.nome }))) return;
      await api("/api/gestor/cargo/" + c.id, { method: "DELETE" });
      await carregarDados();
      desenharPainel();
    })
  );
  el.querySelectorAll("[data-nova-comp]").forEach((b) =>
    b.addEventListener("click", () => formCompetencia(Number(b.dataset.novaComp), null))
  );
  el.querySelectorAll("[data-avaliacoes]").forEach((b) =>
    b.addEventListener("click", () =>
      modalAvaliacoesCargo(cargos.find((c) => c.id === Number(b.dataset.avaliacoes))))
  );
  el.querySelectorAll("[data-editar-comp]").forEach((b) =>
    b.addEventListener("click", () => {
      const [cargoId, compId] = b.dataset.editarComp.split(":").map(Number);
      const cargo = cargos.find((c) => c.id === cargoId);
      formCompetencia(cargoId, cargo.competencias.find((x) => x.id === compId));
    })
  );
  el.querySelectorAll("[data-excluir-comp]").forEach((b) =>
    b.addEventListener("click", async () => {
      if (!confirm(tg("cg_confirmar_excluir_comp"))) return;
      await api("/api/gestor/competencia/" + b.dataset.excluirComp, { method: "DELETE" });
      await carregarDados();
      desenharPainel();
    })
  );
}

function cartaoCargo(c) {
  return `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px">
        <div>
          <h2>${esc(c.nome)} ${c.nivel ? `<span class="badge neutral">${esc(nomeNivelCargo(c.nivel))}</span>` : ""}</h2>
          <p class="desc" style="margin:0">${esc(c.area)}${c.descricao ? ". " + esc(c.descricao) : ""}</p>
          <p style="margin-top:8px">
            ${c.disc_alvo ? `<span class="badge tipo">${tg("cg_disc_desejado", { nome: esc(DISC_PERFIS[c.disc_alvo].nome) })}</span> ` : ""}
            ${c.base_alvo ? `<span class="badge tipo">${tg("cg_base_desejado", { nome: esc(BASE_PERFIS[c.base_alvo].nome) })}</span>` : ""}
          </p>
        </div>
        <div class="linha-acoes" style="margin:0">
          <button class="btn secondary small" data-editar-cargo="${c.id}">${tg("editar")}</button>
          <button class="btn danger small" data-excluir-cargo="${c.id}">${tg("excluir")}</button>
        </div>
      </div>
      <div class="tabela-wrap mt">
        <table class="tabela">
          <thead><tr><th>${tg("r_th_comp")}</th><th>${tg("r_th_tipo")}</th><th class="num">${tg("cg_nivel_exigido")}</th><th class="num">${tg("cg_obrigatoria")}</th></tr></thead>
          <tbody>
            ${c.competencias.map((k) => `
              <tr>
                <td>${esc(k.nome)}
                  <div style="margin-top:4px;white-space:nowrap">
                    <button class="btn ghost small" data-editar-comp="${c.id}:${k.id}" title="${tg("editar")}">${icone("lapis")} ${tg("editar")}</button>
                    <button class="btn ghost small" data-excluir-comp="${k.id}" title="${tg("excluir")}">${icone("lixeira")}</button>
                  </div></td>
                <td><span class="badge tipo">${esc(TIPOS_COMPETENCIA[k.tipo] || k.tipo)}</span></td>
                <td class="num">${k.nivel_requerido}</td>
                <td class="num">${k.obrigatoria ? '<span class="badge neutral">' + tg("sim") + "</span>" : "·"}</td>
              </tr>`).join("") || '<tr><td colspan="4" style="color:var(--muted)">' + tg("cg_nenhuma_comp") + "</td></tr>"}
          </tbody>
        </table>
      </div>
      <div class="linha-acoes" style="margin-top:14px">
        <button class="btn secondary small" data-nova-comp="${c.id}">${tg("cg_adicionar_comp")}</button>
        <button class="btn ghost small" data-avaliacoes="${c.id}">${tg("cg_avaliacoes")}</button>
      </div>
    </div>`;
}

async function modalAvaliacoesCargo(cargo) {
  const r = await api("/api/gestor/cargo/" + cargo.id + "/avaliacoes");
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal" style="max-width:720px">
      <button class="btn ghost small fechar" id="av-fechar">${icone("fechar")}</button>
      <h2>${esc(cargo.nome)}</h2>
      <p class="desc">${tg("av_desc")}</p>

      <h3>${tg("g_roteiro_titulo")}</h3>
      ${r.perguntas.map((p) => `
        <div class="comp-item" style="display:flex;justify-content:space-between;align-items:center;gap:10px">
          <div>${esc(p.texto)}</div>
          <button class="btn ghost small" data-del-perg="${p.id}" title="${tg("excluir")}">${icone("lixeira")}</button>
        </div>`).join("") || '<p class="desc">' + tg("av_sem_perguntas") + "</p>"}
      <div class="linha-acoes" style="margin-top:10px">
        <input type="text" id="nova-perg" placeholder="${tg("av_pergunta_ph")}" style="flex:1;min-width:220px;margin:0">
        <button class="btn secondary small" id="add-perg">${tg("av_add_pergunta")}</button>
      </div>

      <h3 style="margin-top:28px">${tg("av_quiz_titulo")}</h3>
      ${r.questoes.map((q) => `
        <div class="comp-item">
          <div style="display:flex;justify-content:space-between;gap:10px">
            <div class="nome" style="margin-bottom:6px">${esc(q.pergunta)}</div>
            <button class="btn ghost small" data-del-quest="${q.id}" title="${tg("excluir")}">${icone("lixeira")}</button>
          </div>
          <div style="font-size:.82rem;color:var(--muted)">
            ${q.opcoes.map((op, j) => `${String.fromCharCode(65 + j)}) ${esc(op)}${j === q.correta ? " ✓" : ""}`).join(" &nbsp;·&nbsp; ")}
          </div>
        </div>`).join("") || '<p class="desc">' + tg("av_sem_questoes") + "</p>"}
      <button class="btn secondary small mt" id="add-quest">${tg("av_nova_questao")}</button>
    </div>`;
  document.body.appendChild(fundo);
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fundo.remove(); });
  fundo.querySelector("#av-fechar").addEventListener("click", () => fundo.remove());
  const reabrir = () => { fundo.remove(); modalAvaliacoesCargo(cargo); };

  fundo.querySelector("#add-perg").addEventListener("click", async () => {
    const texto = fundo.querySelector("#nova-perg").value.trim();
    if (!texto) return;
    await api("/api/gestor/pergunta-entrevista", {
      method: "POST", body: { cargo_id: cargo.id, texto },
    });
    reabrir();
  });
  fundo.querySelectorAll("[data-del-perg]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api("/api/gestor/pergunta-entrevista/" + b.dataset.delPerg, { method: "DELETE" });
      reabrir();
    })
  );
  fundo.querySelectorAll("[data-del-quest]").forEach((b) =>
    b.addEventListener("click", async () => {
      await api("/api/gestor/questao/" + b.dataset.delQuest, { method: "DELETE" });
      reabrir();
    })
  );
  fundo.querySelector("#add-quest").addEventListener("click", () => {
    modalForm(tg("qz_titulo", { cargo: cargo.nome }), `
      <label class="field">${tg("qz_pergunta")}
        <textarea id="qz-perg" rows="2" placeholder="${tg("qz_pergunta_ph")}"></textarea>
      </label>
      ${[0, 1, 2, 3].map((j) => `
        <label class="field">${tg("qz_opcao", { letra: String.fromCharCode(65 + j) })} ${j > 1 ? '<span class="hint">' + tg("opcional") + "</span>" : ""}
          <input type="text" id="qz-op${j}">
        </label>`).join("")}
      <label class="field">${tg("qz_correta")}
        <select id="qz-correta">
          ${[0, 1, 2, 3].map((j) => `<option value="${j}">${String.fromCharCode(65 + j)}</option>`).join("")}
        </select>
      </label>`,
      async (f) => {
        await api("/api/gestor/questao", {
          method: "POST",
          body: {
            cargo_id: cargo.id,
            pergunta: f.querySelector("#qz-perg").value.trim(),
            opcoes: [0, 1, 2, 3].map((j) => f.querySelector("#qz-op" + j).value),
            correta: Number(f.querySelector("#qz-correta").value),
          },
        });
        reabrir();
      });
  });
}

function modalForm(titulo, corpo, aoSalvar) {
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal" style="max-width:560px">
      <button class="btn ghost small fechar" id="mf-fechar">${icone("fechar")}</button>
      <h2>${esc(titulo)}</h2>
      <div class="mt">${corpo}</div>
      <div class="form-erro" id="mf-erro"></div>
      <button class="btn block" id="mf-salvar">${tg("salvar")}</button>
    </div>`;
  document.body.appendChild(fundo);
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fundo.remove(); });
  fundo.querySelector("#mf-fechar").addEventListener("click", () => fundo.remove());
  fundo.querySelector("#mf-salvar").addEventListener("click", async () => {
    try {
      await aoSalvar(fundo);
      fundo.remove();
      await carregarDados();
      desenharPainel();
    } catch (e) {
      fundo.querySelector("#mf-erro").textContent = e.message;
    }
  });
  return fundo;
}

function formCargo(cargo) {
  modalForm(cargo ? tg("cg_editar") : tg("cg_novo_titulo"), `
    <label class="field">${tg("cg_nome")}
      <input type="text" id="fc-nome" value="${cargo ? esc(cargo.nome) : ""}" placeholder="${tg("cg_nome_ph")}">
    </label>
    <label class="field">${tg("area")} <input type="text" id="fc-area" value="${cargo ? esc(cargo.area) : ""}" placeholder="${tg("cg_area_ph")}"></label>
    <label class="field">${tg("cg_nivel")}
      <select id="fc-nivel">
        ${NIVEIS_CARGO.map((n) =>
          `<option value="${n}" ${cargo && cargo.nivel === n ? "selected" : ""}>${n ? esc(nomeNivelCargo(n)) : "·"}</option>`).join("")}
      </select>
    </label>
    <label class="field">${tg("descricao")}
      <textarea id="fc-desc" rows="3" placeholder="${tg("cg_desc_ph")}">${cargo ? esc(cargo.descricao) : ""}</textarea>
    </label>
    <label class="field">${tg("cg_disc_alvo")} <span class="hint">${tg("cg_usado_match")}</span>
      <select id="fc-disc">
        <option value="">${tg("cg_nao_considerar")}</option>
        ${["D", "I", "S", "C"].map((k) =>
          `<option value="${k}" ${cargo && cargo.disc_alvo === k ? "selected" : ""}>${DISC_PERFIS[k].nome} (${k})</option>`).join("")}
      </select>
    </label>
    <label class="field">${tg("cg_base_alvo")} <span class="hint">${tg("cg_usado_match")}</span>
      <select id="fc-base">
        <option value="">${tg("cg_nao_considerar")}</option>
        ${["B", "A", "S", "E"].map((k) =>
          `<option value="${k}" ${cargo && cargo.base_alvo === k ? "selected" : ""}>${BASE_PERFIS[k].nome}</option>`).join("")}
      </select>
    </label>`,
    async (f) => {
      await api("/api/gestor/cargo", {
        method: "POST",
        body: {
          id: cargo ? cargo.id : undefined,
          nome: f.querySelector("#fc-nome").value.trim(),
          area: f.querySelector("#fc-area").value.trim(),
          nivel: f.querySelector("#fc-nivel").value,
          descricao: f.querySelector("#fc-desc").value.trim(),
          disc_alvo: f.querySelector("#fc-disc").value,
          base_alvo: f.querySelector("#fc-base").value,
        },
      });
    });
}

function formCompetencia(cargoId, comp) {
  modalForm(comp ? tg("ck_editar") : tg("ck_nova"), `
    <label class="field">${tg("ck_nome")}
      <input type="text" id="fk-nome" value="${comp ? esc(comp.nome) : ""}" placeholder="${tg("ck_nome_ph")}">
    </label>
    <label class="field">${tg("r_th_tipo")}
      <select id="fk-tipo">
        ${Object.entries(TIPOS_COMPETENCIA).map(([v, r]) =>
          `<option value="${v}" ${comp && comp.tipo === v ? "selected" : ""}>${r}</option>`).join("")}
      </select>
    </label>
    <label class="field">${tg("ck_nivel")}
      <select id="fk-nivel">
        ${[1, 2, 3, 4, 5].map((n) =>
          `<option value="${n}" ${(comp ? comp.nivel_requerido : 3) === n ? "selected" : ""}>${n}</option>`).join("")}
      </select>
    </label>
    <label class="field" style="display:flex;align-items:center;gap:8px;font-weight:600">
      <input type="checkbox" id="fk-obrig" style="width:auto" ${comp && comp.obrigatoria ? "checked" : ""}>
      ${tg("ck_obrigatoria")}
    </label>`,
    async (f) => {
      await api("/api/gestor/competencia", {
        method: "POST",
        body: {
          id: comp ? comp.id : undefined,
          cargo_id: cargoId,
          nome: f.querySelector("#fk-nome").value.trim(),
          tipo: f.querySelector("#fk-tipo").value,
          nivel_requerido: Number(f.querySelector("#fk-nivel").value),
          obrigatoria: f.querySelector("#fk-obrig").checked,
        },
      });
    });
}

// ------------------------------------------------ matriz de gaps consolidada
function abaMatriz(el) {
  el.innerHTML = `
    <div class="card">
      <h2>${tg("mx_titulo")}</h2>
      <p class="desc">${tg("mx_desc")}</p>
      <label class="field" style="max-width:420px">${tg("cargo")}
        <select id="mx-cargo">
          <option value="">${tg("mx_selecione")}</option>
          ${cargos.map((c) => `<option value="${c.id}">${esc(c.nome)}</option>`).join("")}
        </select>
      </label>
      <div id="mx-resultado"></div>
    </div>`;
  document.getElementById("mx-cargo").addEventListener("change", async (ev) => {
    const cargoId = Number(ev.target.value);
    const alvo = document.getElementById("mx-resultado");
    if (!cargoId) { alvo.innerHTML = ""; return; }
    alvo.innerHTML = "<p class='desc'>" + tg("carregando") + "</p>";
    const r = await api("/api/gestor/matriz?cargo_id=" + cargoId);
    if (!r.linhas.length) {
      alvo.innerHTML = "<p class='desc'>" + tg("mx_nenhum") + "</p>";
      return;
    }
    const comps = r.cargo.competencias;
    alvo.innerHTML = `
      <div class="tabela-wrap">
        <table class="tabela">
          <thead>
            <tr>
              <th>${tg("candidato")}</th><th class="num">${tg("match")}</th><th class="num">${tg("mx_aderencia")}</th><th class="num">${tg("status")}</th>
              ${comps.map((k) => `<th class="num" title="${esc(tg("mx_th_title", { nome: k.nome, n: k.nivel_requerido }))}">${esc(k.nome.length > 18 ? k.nome.slice(0, 17) + "…" : k.nome)}<br><span style="font-weight:400">${tg("mx_exig", { n: k.nivel_requerido })}</span></th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${r.linhas.map((l) => `
              <tr ${l.candidato_id || l.id ? `data-linha-cand="${l.candidato_id || l.id}"` : ""}>
                <td><strong>${l.candidato_id || l.id ? linkCandidato(l.candidato_id || l.id, l.nome) : esc(l.nome)}</strong>${l.local ? `<br><span style="color:var(--muted);font-size:.76rem">${esc(l.local)}</span>` : ""}</td>
                <td class="num">${l.match != null ? `<strong>${l.match}%</strong>` : "·"}</td>
                <td class="num">${l.respondeu ? l.aderencia + "%" : "·"}</td>
                <td class="num">${l.respondeu ? badgeStatus(l.status) : '<span class="badge tipo">' + tg("mx_sem_auto") + "</span>"}</td>
                ${l.itens.map((i) => `
                  <td class="num"><span class="celula-gap ${classeGap(i)}">${i.respondida ? i.nivel_atual + "/" + i.nivel_requerido : "·"}</span></td>`).join("")}
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
      <p class="desc mt">${tg("mx_legenda")} <span class="celula-gap ok">OK</span> ${tg("mx_leg_ok")} ·
        <span class="celula-gap medio">${tg("mx_leg_gap12")}</span> ${tg("mx_leg_desenv")} ·
        <span class="celula-gap alto">${tg("mx_leg_gap3")}</span> ${tg("mx_leg_alto")} ·
        <span class="celula-gap vazio">·</span> ${tg("r_sem_resposta")}</p>`;
    ligarDetalhes(alvo);
  });
}

// ------------------------------------------------ configurações
async function abaConfig(el) {
  const info = infoGestor();
  const slug = (info.empresa && info.empresa.slug) || "";
  const linkCandidato = location.origin + "/candidato?e=" + encodeURIComponent(slug);
  const linkEmpresa = location.origin + "/vagas?e=" + encodeURIComponent(slug);
  el.innerHTML = `
    <div class="grid cols-2">
      <div class="card">
        <h2 class="icone-titulo">${icone("link")}<span>${tg("cfg_links")}</span></h2>
        <p class="desc">${tg("cfg_pag_empresa", { empresa: esc((info.empresa && info.empresa.nome) || tg("cfg_sua_empresa")) })}</p>
        <input type="text" readonly value="${esc(linkEmpresa)}" id="cfg-link-empresa">
        <button class="btn secondary small mt" id="cfg-copiar-empresa">${tg("cfg_copiar_empresa")}</button>
        <p class="desc" style="margin-top:16px">${tg("cfg_pag_vagas")}${info.local ? " (" + esc(info.local) + ")" : " " + tg("cfg_sem_local")}:</p>
        <input type="text" readonly value="${esc(location.origin + "/vagas?g=" + (info.login || ""))}" id="cfg-link-vagas">
        <button class="btn secondary small mt" id="cfg-copiar-vagas">${tg("cfg_copiar_vagas")}</button>
        <p class="desc" style="margin-top:16px">${tg("cfg_cadastro_direto")}</p>
        <input type="text" readonly value="${esc(linkCandidato)}" id="cfg-link">
        <button class="btn secondary small mt" id="cfg-copiar">${tg("cfg_copiar_link")}</button>
      </div>
      <div class="card">
        <h2 class="icone-titulo">${icone("chave")}<span>${tg("cfg_senha_titulo")}</span></h2>
        <p class="desc">${tg("cfg_conta")} <strong>${esc(info.nome || "")}</strong> (${esc(info.login || "")})</p>
        <label class="field">${tg("cfg_senha_atual")} <input type="password" id="cfg-atual" autocomplete="current-password"></label>
        <label class="field">${tg("nova_senha_min")} <input type="password" id="cfg-nova" autocomplete="new-password"></label>
        <div class="form-erro" id="cfg-erro"></div>
        <button class="btn" id="cfg-salvar">${tg("cfg_alterar_senha")}</button>
      </div>
    </div>
    <div id="cfg-marca"></div>
    <div id="cfg-entrada"></div>
    <div id="cfg-auditoria"></div>
    <div id="cfg-agenda"></div>
    <div id="cfg-gestores"></div>
    <div id="cfg-templates"></div>`;
  secaoMarca(document.getElementById("cfg-marca"));
  secaoEntrada(document.getElementById("cfg-entrada"));
  if (typeof secaoAuditoria === "function") secaoAuditoria(document.getElementById("cfg-auditoria"));
  if (typeof secaoAgenda === "function") secaoAgenda(document.getElementById("cfg-agenda")); // agenda de entrevistas
  document.getElementById("cfg-copiar").addEventListener("click", () => {
    navigator.clipboard.writeText(linkCandidato);
    document.getElementById("cfg-copiar").textContent = tg("copiado");
  });
  document.getElementById("cfg-copiar-empresa").addEventListener("click", () => {
    navigator.clipboard.writeText(linkEmpresa);
    document.getElementById("cfg-copiar-empresa").textContent = tg("copiado");
  });
  document.getElementById("cfg-copiar-vagas").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("cfg-link-vagas").value);
    document.getElementById("cfg-copiar-vagas").textContent = tg("copiado");
  });
  document.getElementById("cfg-salvar").addEventListener("click", async () => {
    const erro = document.getElementById("cfg-erro");
    erro.textContent = "";
    try {
      await api("/api/gestor/senha", {
        method: "POST",
        body: {
          atual: document.getElementById("cfg-atual").value,
          nova: document.getElementById("cfg-nova").value,
        },
      });
      erro.style.color = "var(--ok)";
      erro.textContent = tg("cfg_senha_ok");
      document.getElementById("cfg-atual").value = "";
      document.getElementById("cfg-nova").value = "";
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
  if (info.admin) {
    await secaoGestores(document.getElementById("cfg-gestores"));
    // e-mail, IA e endereço público agora são da plataforma: ficam no painel do administrador do sistema
    await secaoTemplates(document.getElementById("cfg-templates"));
  }
}

async function secaoTemplates(el) {
  const r = await api("/api/gestor/templates");
  const chaves = Object.keys(r.nomes);
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("bloco")}<span>${tg("tp_titulo")}</span></h2>
      <p class="desc">${tg("tp_desc")}</p>
      ${chaves.map((k) => `
        <div class="comp-item">
          <div class="nome">${esc(nomeTemplate(k, r.nomes[k]))}</div>
          <label class="field" style="margin-bottom:8px">${tg("assunto")}
            <input type="text" id="tp-assunto-${k}" value="${esc(r.templates[k].assunto)}">
          </label>
          <label class="field" style="margin-bottom:0">${tg("mensagem")}
            <textarea id="tp-corpo-${k}" rows="4">${esc(r.templates[k].corpo)}</textarea>
          </label>
        </div>`).join("")}
      <div class="form-erro" id="tp-erro"></div>
      <button class="btn mt" id="tp-salvar">${tg("tp_salvar")}</button>
    </div>`;
  document.getElementById("tp-salvar").addEventListener("click", async () => {
    const erro = document.getElementById("tp-erro");
    const templates = {};
    chaves.forEach((k) => {
      templates[k] = {
        assunto: document.getElementById("tp-assunto-" + k).value,
        corpo: document.getElementById("tp-corpo-" + k).value,
      };
    });
    try {
      await api("/api/gestor/templates", { method: "POST", body: { templates } });
      erro.style.color = "var(--ok)";
      erro.textContent = tg("tp_ok");
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
}

async function secaoGestores(el) {
  const r = await api("/api/gestor/gestores");
  const pendentes = r.gestores.filter((g) => !g.aprovado);
  const aprovados = r.gestores.filter((g) => g.aprovado);
  const semEmail = '<span class="badge warn">' + tg("gs_sem_email") + "</span>";
  const todosLocais = '<span style="color:var(--muted)">' + tg("gs_todos_locais") + "</span>";
  const cardPendentes = pendentes.length ? `
    <div class="card" style="border-color:var(--warn);background:var(--warn-bg)">
      <h2 class="icone-titulo"><span>${tg("gs_pendentes", { n: fmtNum(pendentes.length) })}</span></h2>
      <p class="desc">${tg("gs_pendentes_desc")}</p>
      <div class="tabela-wrap mt">
        <table class="tabela">
          <thead><tr><th>${tg("nome")}</th><th>${tg("login")}</th><th>${tg("email")}</th><th>${tg("local")}</th><th></th></tr></thead>
          <tbody>
            ${pendentes.map((g) => `
              <tr>
                <td><strong>${esc(g.nome)}</strong></td>
                <td>${esc(g.login)}</td>
                <td>${g.email ? esc(g.email) : semEmail}</td>
                <td>${g.local ? esc(g.local) : todosLocais}</td>
                <td class="num">
                  <button class="btn small" data-aprovar="${g.id}">${tg("gs_aprovar")}</button>
                  <button class="btn danger small" data-recusar="${g.id}">${tg("gs_recusar")}</button>
                </td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
    </div>` : "";
  el.innerHTML = `
    ${cardPendentes}
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2 class="icone-titulo">${icone("usuarios")}<span>${tg("gs_titulo")}</span></h2>
          <p class="desc" style="margin:0">${tg("gs_desc")}</p>
        </div>
        <button class="btn" id="novo-gestor">${tg("gs_novo")}</button>
      </div>
      <div class="tabela-wrap mt">
        <table class="tabela">
          <thead><tr><th>${tg("nome")}</th><th>${tg("login")}</th><th>${tg("email")}</th><th>${tg("local")}</th><th class="num">${tg("gs_perfil")}</th><th></th></tr></thead>
          <tbody>
            ${aprovados.map((g) => `
              <tr>
                <td><strong>${esc(g.nome)}</strong></td>
                <td>${esc(g.login)}</td>
                <td>${g.email ? esc(g.email) : semEmail}</td>
                <td>${g.local ? esc(g.local) : todosLocais}</td>
                <td class="num">${g.admin ? '<span class="badge neutral">' + tg("administrador") + "</span>" : '<span class="badge tipo">' + tg("gestor") + "</span>"}</td>
                <td class="num">
                  <button class="btn ghost small" data-editar-gestor="${g.id}" title="${tg("editar")}">${icone("lapis")}</button>
                  <button class="btn ghost small" data-excluir-gestor="${g.id}" title="${tg("excluir")}">${icone("lixeira")}</button>
                </td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
    </div>`;
  el.querySelectorAll("[data-aprovar]").forEach((b) =>
    b.addEventListener("click", async () => {
      b.disabled = true;
      try {
        await api("/api/gestor/gestores/" + b.dataset.aprovar + "/aprovar", { method: "POST" });
        secaoGestores(el);
      } catch (e) {
        alert(e.message);
        b.disabled = false;
      }
    })
  );
  el.querySelectorAll("[data-recusar]").forEach((b) =>
    b.addEventListener("click", async () => {
      const g = pendentes.find((x) => x.id === Number(b.dataset.recusar));
      if (!confirm(tg("gs_confirmar_recusar", { nome: g.nome, login: g.login }))) return;
      try {
        await api("/api/gestor/gestores/" + g.id, { method: "DELETE" });
        secaoGestores(el);
      } catch (e) {
        alert(e.message);
      }
    })
  );
  document.getElementById("novo-gestor").addEventListener("click", () => formGestor(null));
  el.querySelectorAll("[data-editar-gestor]").forEach((b) =>
    b.addEventListener("click", () =>
      formGestor(r.gestores.find((g) => g.id === Number(b.dataset.editarGestor)))
    )
  );
  el.querySelectorAll("[data-excluir-gestor]").forEach((b) =>
    b.addEventListener("click", async () => {
      const g = r.gestores.find((x) => x.id === Number(b.dataset.excluirGestor));
      if (!confirm(tg("gs_confirmar_excluir", { nome: g.nome, login: g.login }))) return;
      try {
        await api("/api/gestor/gestores/" + g.id, { method: "DELETE" });
        desenharPainel();
      } catch (e) {
        alert(e.message);
      }
    })
  );
}

function formGestor(g) {
  modalForm(g ? tg("gs_editar") : tg("gs_novo_titulo"), `
    <label class="field">${tg("nome")}
      <input type="text" id="fg-nome" value="${g ? esc(g.nome) : ""}" placeholder="${tg("gs_nome_ph")}">
    </label>
    <label class="field">${tg("login")} ${g ? '<span class="hint">' + tg("gs_login_fixo") + "</span>" : ""}
      <input type="text" id="fg-login" value="${g ? esc(g.login) : ""}" placeholder="${tg("gs_login_ph")}" ${g ? "disabled" : ""}>
    </label>
    <label class="field">${tg("email")} <span class="hint">${tg("gs_email_hint")}</span>
      <input type="email" id="fg-email" value="${g ? esc(g.email || "") : ""}" placeholder="${tg("gs_email_ph")}">
    </label>
    <label class="field">${tg("gs_local")} <span class="hint">${tg("gs_local_hint")}</span>
      <input type="text" id="fg-local" value="${g ? esc(g.local) : ""}" placeholder="${tg("local_ph")}">
    </label>
    <label class="field">${g ? tg("gs_nova_senha") + " <span class='hint'>" + tg("gs_manter_senha") + "</span>" : tg("senha_min")}
      <input type="password" id="fg-senha" autocomplete="new-password">
    </label>
    <label class="field" style="display:flex;align-items:center;gap:8px">
      <input type="checkbox" id="fg-admin" style="width:auto" ${g && g.admin ? "checked" : ""}>
      ${tg("gs_admin_check")}
    </label>`,
    async (f) => {
      await api("/api/gestor/gestores", {
        method: "POST",
        body: {
          id: g ? g.id : undefined,
          nome: f.querySelector("#fg-nome").value.trim(),
          login: f.querySelector("#fg-login").value.trim(),
          email: f.querySelector("#fg-email").value.trim(),
          local: f.querySelector("#fg-local").value.trim(),
          senha: f.querySelector("#fg-senha").value,
          admin: f.querySelector("#fg-admin").checked,
        },
      });
    });
}

// ------------------------------------------------ boot
(async function () {
  montarSeletorIdiomaGestor(trocarIdiomaPainel);
  atualizarTopo();
  // link de redefinição de senha (?reset=token) tem prioridade
  const tokenReset = new URLSearchParams(location.search).get("reset");
  if (tokenReset) return telaRedefinirSenha(tokenReset);
  try {
    const setup = await api("/api/gestor/setup");
    if (setup.precisa_setup) return telaSetup();
  } catch (e) { /* segue para o login */ }
  const token = localStorage.getItem("gestor_token");
  if (!token) return telaLogin();
  try {
    await iniciarPainel();
  } catch (e) {
    telaLogin();
  }
})();
