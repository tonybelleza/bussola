/* =====================================================================
   Painel do Gestor: visão geral, candidatos, cargos/funções,
   matriz de gaps consolidada e configurações.
   ===================================================================== */

const app = document.getElementById("app");
let cargos = [];
let candidatos = [];
let abaAtiva = "visao";

// ------------------------------------------------ API
async function api(caminho, opcoes = {}) {
  const headers = { "Content-Type": "application/json" };
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
    throw new Error(dados.erro || "Sessão expirada");
  }
  if (!resp.ok) throw new Error(dados.erro || "Erro de comunicação com o servidor");
  return dados;
}

async function carregarDados() {
  const [rc, rl] = await Promise.all([api("/api/cargos"), api("/api/gestor/candidatos")]);
  cargos = rc.cargos;
  candidatos = rl.candidatos;
}

// ------------------------------------------------ login
function telaLogin() {
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:440px;margin:48px auto">
      <h2 class="icone-titulo">${icone("cadeado")}<span>Acesso do gestor</span></h2>
      <p class="desc">Área restrita. Entre com o seu login e senha de gestor.</p>
      <label class="field">Login
        <input type="text" id="login-usuario" placeholder="seu.login" autocomplete="username">
      </label>
      <label class="field">Senha
        <input type="password" id="login-senha" placeholder="••••••••" autocomplete="current-password">
      </label>
      <div class="form-erro" id="login-erro"></div>
      <button class="btn block" id="login-entrar">Entrar</button>
      <p class="texto-centro" style="margin:14px 0 0">
        <a href="#" id="link-esqueci" style="color:var(--text-2);font-size:.85rem">Esqueci minha senha</a>
      </p>
    </div>`;
  document.getElementById("link-esqueci").addEventListener("click", (ev) => {
    ev.preventDefault();
    telaEsqueciSenha();
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
      localStorage.setItem("gestor_token", r.token);
      localStorage.setItem("gestor_info", JSON.stringify({
        nome: r.nome, login: r.login, local: r.local, admin: r.admin,
        modulos: r.modulos || [],
      }));
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
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:440px;margin:48px auto">
      <h2 class="icone-titulo">${icone("chave")}<span>Recuperar acesso</span></h2>
      <p class="desc">Informe o seu login ou e-mail. Se houver uma conta, enviaremos um
        link para redefinir a senha (válido por 2 horas).</p>
      <label class="field">Login ou e-mail
        <input type="text" id="esq-ident" placeholder="seu.login ou voce@email.com">
      </label>
      <div class="form-erro" id="esq-msg"></div>
      <button class="btn block" id="esq-enviar">Enviar link de redefinição</button>
      <p class="texto-centro" style="margin:14px 0 0">
        <a href="#" id="esq-voltar" style="color:var(--text-2);font-size:.85rem">Voltar ao login</a>
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
      msg.textContent = "Se houver uma conta com esse login ou e-mail, o link de redefinição chegará em instantes. Verifique também o spam.";
    } catch (e) {
      msg.textContent = e.message;
    }
  });
}

function telaRedefinirSenha(token) {
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:440px;margin:48px auto">
      <h2 class="icone-titulo">${icone("cadeado")}<span>Criar nova senha</span></h2>
      <p class="desc">Defina a sua nova senha de acesso.</p>
      <label class="field">Nova senha (mín. 6 caracteres)
        <input type="password" id="red-senha" autocomplete="new-password">
      </label>
      <label class="field">Confirmar nova senha
        <input type="password" id="red-senha2" autocomplete="new-password">
      </label>
      <div class="form-erro" id="red-msg"></div>
      <button class="btn block" id="red-salvar">Salvar nova senha</button>
    </div>`;
  document.getElementById("red-salvar").addEventListener("click", async () => {
    const msg = document.getElementById("red-msg");
    msg.style.color = "var(--err)";
    msg.textContent = "";
    const senha = document.getElementById("red-senha").value;
    if (senha !== document.getElementById("red-senha2").value) {
      msg.textContent = "As senhas não conferem.";
      return;
    }
    try {
      await api("/api/gestor/redefinir-senha", {
        method: "POST",
        body: { token, nova: senha },
      });
      history.replaceState({}, "", "/gestor");
      msg.style.color = "var(--ok)";
      msg.textContent = "Senha redefinida! Redirecionando para o login…";
      setTimeout(telaLogin, 1500);
    } catch (e) {
      msg.textContent = e.message;
    }
  });
}

function telaSetup() {
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:480px;margin:48px auto">
      <h2 class="icone-titulo">${icone("usuario")}<span>Configuração inicial</span></h2>
      <p class="desc">Bem-vindo! Este é o primeiro acesso ao sistema. Cadastre a conta do administrador, que gerencia cargos, gestores e candidatos.</p>
      <label class="field">Seu nome
        <input type="text" id="st-nome" placeholder="Nome completo">
      </label>
      <label class="field">Login
        <input type="text" id="st-login" placeholder="ex.: tony" autocomplete="username">
      </label>
      <label class="field">Seu e-mail <span class="hint">(para receber avisos de novos candidatos e avaliações)</span>
        <input type="email" id="st-email" placeholder="voce@email.com" autocomplete="email">
      </label>
      <label class="field">Senha (mín. 6 caracteres)
        <input type="password" id="st-senha" autocomplete="new-password">
      </label>
      <label class="field">Confirmar senha
        <input type="password" id="st-senha2" autocomplete="new-password">
      </label>
      <div class="form-erro" id="st-erro"></div>
      <button class="btn block" id="st-criar">Criar conta e entrar</button>
    </div>`;
  document.getElementById("st-criar").addEventListener("click", async () => {
    const erro = document.getElementById("st-erro");
    erro.textContent = "";
    const senha = document.getElementById("st-senha").value;
    if (senha !== document.getElementById("st-senha2").value) {
      erro.textContent = "As senhas não conferem.";
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
      localStorage.setItem("gestor_token", r.token);
      localStorage.setItem("gestor_info", JSON.stringify({
        nome: r.nome, login: r.login, local: r.local, admin: r.admin,
      }));
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
  const info = infoGestor();
  const sub = document.querySelector(".topbar .sub");
  if (sub && info.nome) {
    const partes = [info.nome];
    if (info.local) partes.push(info.local);
    if (info.admin && info.nome !== "Administrador") partes.push("Administrador");
    sub.textContent = partes.join(" · ");
  }
  await carregarDados();
  desenharPainel();
}

function desenharPainel() {
  const abas = [
    ["visao", "Visão geral"],
    ["vagas", "Vagas"],
    ["candidatos", "Candidatos"],
    ["cargos", "Cargos e funções"],
    ["matriz", "Matriz de gaps"],
    ["relatorios", "Relatórios"],
    ["guia", "Guia"],
    ["config", "Configurações"],
  ];
  if ((infoGestor().modulos || []).includes("diagnostico")) {
    abas.splice(6, 0, ["diagnostico", "Diagnóstico"]);
  }
  app.innerHTML = `
    <div class="tabs">
      ${abas.map(([id, rot]) => `<button class="tab ${abaAtiva === id ? "ativa" : ""}" data-aba="${id}">${rot}</button>`).join("")}
    </div>
    <div id="conteudo"></div>`;
  app.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => {
      abaAtiva = t.dataset.aba;
      desenharPainel();
    })
  );
  const conteudo = document.getElementById("conteudo");
  if (abaAtiva === "visao") abaVisao(conteudo);
  if (abaAtiva === "vagas") abaVagas(conteudo);
  if (abaAtiva === "candidatos") abaCandidatos(conteudo);
  if (abaAtiva === "cargos") abaCargos(conteudo);
  if (abaAtiva === "matriz") abaMatriz(conteudo);
  if (abaAtiva === "relatorios") abaRelatorios(conteudo);
  if (abaAtiva === "guia") abaGuia(conteudo);
  if (abaAtiva === "diagnostico") abaDiagnostico(conteudo);
  if (abaAtiva === "config") abaConfig(conteudo);
}

// ------------------------------------------------ relatórios
async function abaRelatorios(el) {
  const r = await api("/api/gestor/relatorios");
  const barra = (rotulo, valor, maximo, cor) => `
    <div class="perfil-barra">
      <div class="rotulo">${esc(rotulo)}</div>
      <div class="trilha"><div class="valor" style="width:${maximo ? Math.round(100 * valor / maximo) : 0}%;background:${cor || "var(--accent-grad)"}"></div></div>
      <div class="num">${valor}</div>
    </div>`;

  const funilHtml = r.funil.map((f) => {
    const maximo = Math.max(f.etapas.inscrito + f.etapas.avaliacoes + f.etapas.entrevista
      + f.etapas.proposta + f.etapas.contratado, 1);
    const ativos = f.total - f.etapas.reprovado;
    return `
      <div class="card">
        <h2 style="font-size:1.05rem">${esc(f.vaga)}
          ${f.status === "aberta" ? '<span class="badge ok">Aberta</span>' : '<span class="badge tipo">' + esc(f.status) + "</span>"}</h2>
        <p class="desc">${f.total} candidato(s) no total · ${ativos} ativo(s) · ${f.etapas.reprovado} reprovado(s)</p>
        <div class="perfil-barras">
          ${barra("Inscritos", f.total, Math.max(f.total, 1))}
          ${barra("Avaliações+", f.etapas.avaliacoes + f.etapas.entrevista + f.etapas.proposta + f.etapas.contratado, Math.max(f.total, 1))}
          ${barra("Entrevista+", f.etapas.entrevista + f.etapas.proposta + f.etapas.contratado, Math.max(f.total, 1))}
          ${barra("Proposta+", f.etapas.proposta + f.etapas.contratado, Math.max(f.total, 1))}
          ${barra("Contratados", f.etapas.contratado, Math.max(f.total, 1), "var(--ok)")}
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
      <div class="metrica"><div class="num">${r.total_candidatos}</div><div class="rot">Candidatos no banco</div></div>
      <div class="metrica"><div class="num">${r.avaliacoes_completas}</div><div class="rot">Avaliações completas</div></div>
      <div class="metrica"><div class="num">${r.total_candidatos ? Math.round(100 * r.avaliacoes_completas / r.total_candidatos) + "%" : "0%"}</div><div class="rot">Taxa de conclusão</div></div>
      <div class="metrica"><div class="num">${r.contratados}</div><div class="rot">Contratados</div></div>
      <div class="metrica"><div class="num">${r.tempo_medio_contratacao != null ? r.tempo_medio_contratacao + "d" : "…"}</div><div class="rot">Tempo médio até contratar</div></div>
    </div>
    ${r.por_mes.length ? `<div class="card"><h2 style="font-size:1.05rem">Candidatos por mês</h2>
      <div class="perfil-barras">${r.por_mes.map((m2) => barra(m2.mes, m2.total, maxMes)).join("")}</div></div>` : ""}
    ${funilHtml || '<div class="card"><p class="desc">Crie vagas para ver o funil de conversão.</p></div>'}
    <div class="grid cols-2">
      ${distHtml("Perfis DISC do banco", r.disc, DISC_PERFIS)}
      ${distHtml("Arquétipos B.A.S.E. do banco", r.base, BASE_PERFIS)}
    </div>`;
}

// ------------------------------------------------ guia do gestor
function abaGuia(el) {
  const cartaoPerfil = (p, letra) => `
    <div class="card" style="margin-bottom:0">
      <h2 class="icone-titulo" style="font-size:1.05rem">${p.ic ? icone(p.ic) : ""}<span>${esc(p.nome)}${letra ? " (" + letra + ")" : ""}</span></h2>
      <p style="font-size:.9rem;color:var(--text-2)">${esc(p.resumo)}</p>
    </div>`;

  el.innerHTML = `
    <div class="card">
      <h2>Como funciona cada avaliação</h2>
      <p class="desc">Este guia explica o que cada instrumento mede, como o candidato responde e como interpretar os resultados no painel.</p>
    </div>

    <div class="card">
      ${tituloIcone("camadas", "Teste DISC")}
      <p class="desc">Perfil comportamental em 4 dimensões: Dominância, Influência, Estabilidade e Conformidade.</p>
      <h3>Como o candidato responde</h3>
      <p>São 24 blocos com 4 palavras cada. Em cada bloco, a pessoa marca a palavra que MAIS se parece com ela e a que MENOS se parece. Leva cerca de 8 minutos.</p>
      <h3>Como interpretar</h3>
      <p>Cada dimensão recebe um percentual de 0 a 100. O perfil dominante é a dimensão mais alta e o secundário é a segunda mais alta. A combinação das duas descreve o estilo de trabalho: como a pessoa decide, se comunica e reage à pressão. Não existe perfil bom ou ruim, existe perfil mais ou menos ajustado ao tipo de função.</p>
      <div class="grid cols-2 mt">
        ${["D", "I", "S", "C"].map((k) => cartaoPerfil(DISC_PERFIS[k], k)).join("")}
      </div>
    </div>

    <div class="card">
      ${tituloIcone("bussola", "Teste B.A.S.E.")}
      <p class="desc">Código de personalidade em 4 arquétipos: Bússola, Atuante, Sensível e Estudioso. Metodologia de Tony Belleza que revela o que realmente impulsiona as decisões da pessoa.</p>
      <h3>Como o candidato responde</h3>
      <p>São 8 rodadas com 4 cartas cada, no formato do teste original de tonybelleza.com/base. Em cada rodada, a pessoa clica nas cartas em ordem, da que mais combina com ela (1º) até a que menos combina (4º). Cada posição vale pontos (1º vale 4, 2º vale 3, 3º vale 2 e 4º vale 1) e o resultado é o código completo: a ordem das 4 letras por pontuação. Leva menos de 3 minutos.</p>
      <h3>Como interpretar</h3>
      <p>O código se lê por posição: a 1ª letra é o motor principal da pessoa, a 2ª é a influência secundária, a 3ª é o modo ativado sob estresse e a 4ª mostra os valores menos prioritários. O relatório traz ainda os gatilhos (o que impulsiona e o que incomoda) e dicas de comunicação com os outros perfis, úteis para conduzir a entrevista. Enquanto o DISC descreve o comportamento observável, o B.A.S.E. revela o motor interno das decisões. Os dois juntos dão uma visão completa.</p>
      <div class="grid cols-2 mt">
        ${["B", "A", "S", "E"].map((k) => cartaoPerfil(BASE_PERFIS[k])).join("")}
      </div>
    </div>

    <div class="card">
      ${tituloIcone("barras", "Autoavaliação de competências")}
      <p class="desc">Nível atual do candidato em cada competência exigida pelo cargo de interesse.</p>
      <h3>Como o candidato responde</h3>
      <p>Para cada competência mapeada no cargo (na aba Cargos e funções), a pessoa indica seu nível atual numa escala de 0 a 5: 0 Não possuo, 1 Básico, 2 Em desenvolvimento, 3 Intermediário, 4 Avançado e 5 Especialista.</p>
      <h3>Tipos de competência</h3>
      <p>Técnica (o que precisa saber fazer), Relacional (como se relaciona e se comunica), Formação/Certificação (diplomas e certificados exigidos) e Experiência (tempo e vivência prática). Competências marcadas como obrigatórias são requisitos para exercer a função.</p>
    </div>

    <div class="card">
      ${tituloIcone("matriz", "Matriz de gaps")}
      <p class="desc">Cruzamento da autoavaliação com o mapeamento do cargo, gerando o plano de desenvolvimento priorizado.</p>
      <h3>Como é calculada</h3>
      <p>Para cada competência: gap = nível exigido menos nível atual. A aderência é o percentual do total exigido que a pessoa já atende. O status resume a leitura: <span class="badge ok">Apto para a função</span> quando a aderência é 90% ou mais sem nenhuma obrigatória pendente, <span class="badge warn">Em desenvolvimento</span> a partir de 60%, e <span class="badge err">Gap alto</span> abaixo disso.</p>
      <h3>Plano de desenvolvimento</h3>
      <p>O sistema lista as competências com gap em ordem de prioridade (obrigatórias primeiro, depois os maiores gaps) e sugere a ação conforme o tipo: buscar formação, capacitação técnica, desenvolvimento comportamental ou experiência prática. É a base para decidir treinamento, mentoria ou upgrade de cargo.</p>
    </div>

    <div class="card">
      ${tituloIcone("usuarios", "Entrevista estruturada e teste de conhecimento")}
      <h3>Roteiro de entrevista (scorecard)</h3>
      <p>Em Cargos e funções, cada cargo pode ter um roteiro de perguntas. Ao registrar a entrevista no relatório do candidato, o gestor dá nota de 1 a 5 por pergunta. A média padroniza a avaliação entre entrevistadores diferentes e elimina o julgamento por impressão geral.</p>
      <h3>Teste de conhecimento</h3>
      <p>Também por cargo, o gestor monta questões de múltipla escolha. O candidato responde na jornada de avaliação e o sistema corrige automaticamente.</p>
      <h3>Pipeline de vagas</h3>
      <p>Na aba Vagas, cada vaga tem um quadro com as etapas Inscrito, Avaliações, Entrevista, Proposta, Contratado e Reprovado. Arraste os cartões para mover candidatos; cada mudança fica registrada na linha do tempo e pode notificar o candidato por e-mail.</p>
    </div>

    <div class="card">
      ${tituloIcone("alvo", "Match geral")}
      <p class="desc">Índice único que cruza tudo: competências, DISC, B.A.S.E., teste de conhecimento e entrevista.</p>
      <h3>Como é calculado</h3>
      <p>Competências valem 30%, perfil DISC 15%, B.A.S.E. 15%, teste de conhecimento 20% e entrevista 20%. Os componentes comportamentais usam o perfil desejado definido em cada cargo (aba Cargos e funções). Se algo ainda não foi respondido, os pesos se redistribuem sobre o que existe: com apenas os três primeiros, a proporção equivale aos antigos 50/25/25.</p>
      <h3>Como usar</h3>
      <p>O match ordena os candidatos na matriz de gaps e aparece na lista e nos relatórios. Use como referência para priorizar conversas e decisões de desenvolvimento. Importante: os perfis comportamentais indicam estilo, não capacidade. Ninguém deve ser aprovado ou eliminado apenas pelo DISC ou pelo B.A.S.E.</p>
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
    <div class="metricas">
      <div class="metrica"><div class="num">${candidatos.length}</div><div class="rot">Candidatos cadastrados</div></div>
      <div class="metrica"><div class="num">${comDisc}</div><div class="rot">Testes DISC concluídos</div></div>
      <div class="metrica"><div class="num">${comBase}</div><div class="rot">Testes B.A.S.E. concluídos</div></div>
      <div class="metrica"><div class="num">${comAuto}</div><div class="rot">Autoavaliações respondidas</div></div>
      <div class="metrica"><div class="num">${completos}</div><div class="rot">Avaliações completas</div></div>
      <div class="metrica"><div class="num">${cargos.length}</div><div class="rot">Cargos mapeados</div></div>
    </div>
    <div class="card">
      <h2>Últimos candidatos</h2>
      ${tabelaCandidatos(candidatos.slice(0, 8))}
    </div>
    <div class="card">
      <h2 class="icone-titulo">${icone("documento")}<span>Últimas atividades</span></h2>
      <p class="desc">Tudo o que aconteceu recentemente: novos candidatos, testes concluídos, mudanças de etapa e anotações.</p>
      <div id="feed-atividades"><p class="desc">Carregando…</p></div>
    </div>`;
  ligarLinhasCandidato(el);
  api("/api/gestor/atividades").then((r) => {
    const alvo = document.getElementById("feed-atividades");
    if (!alvo) return;
    if (!r.atividades.length) {
      alvo.innerHTML = '<p class="desc">Nenhuma atividade registrada ainda.</p>';
      return;
    }
    alvo.innerHTML = `<div class="timeline">${r.atividades.map((a) => `
      <div class="timeline-item ${["cadastro", "sistema", "etapa"].includes(a.tipo) ? "destaque" : ""}">
        <div class="quando">${esc((a.criado_em || "").slice(0, 16).replace("T", " "))}</div>
        <div class="texto-evento"><strong><a href="#" data-detalhe="${a.candidato_id}" style="color:inherit">${esc(a.candidato_nome)}</a></strong>: ${esc(a.texto)}</div>
      </div>`).join("")}</div>`;
    alvo.querySelectorAll("[data-detalhe]").forEach((lnk) =>
      lnk.addEventListener("click", (ev) => {
        ev.preventDefault();
        abrirDetalheCandidato(Number(lnk.dataset.detalhe));
      })
    );
  }).catch(() => {});
}

// ------------------------------------------------ vagas e pipeline
async function abaVagas(el, vagaAberta) {
  const r = await api("/api/gestor/vagas");
  if (vagaAberta) return telaPipeline(el, vagaAberta);
  el.innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2 class="icone-titulo">${icone("pasta")}<span>Vagas</span></h2>
          <p class="desc" style="margin:0">Abra vagas vinculadas aos cargos mapeados e acompanhe o processo seletivo no pipeline. O link público para candidatos é <strong>/vagas</strong>.</p>
        </div>
        <button class="btn" id="nova-vaga">+ Nova vaga</button>
      </div>
    </div>
    ${r.vagas.map((v) => `
      <div class="card" style="padding:22px 28px">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
          <div>
            <h2 style="font-size:1.1rem;margin-bottom:2px">${esc(v.titulo)}
              ${v.status === "aberta" ? '<span class="badge ok">Aberta</span>'
                : v.status === "pausada" ? '<span class="badge warn">Pausada</span>'
                : '<span class="badge tipo">Encerrada</span>'}
            </h2>
            <p class="desc" style="margin:0">${esc(v.cargo_nome)}${v.local ? " · " + esc(v.local) : ""}${v.pais ? " · " + esc(v.pais) : ""}
              · ${v.total} candidato(s) · Entrevista: ${v.etapas.entrevista} · Contratados: ${v.etapas.contratado}</p>
          </div>
          <div class="linha-acoes" style="margin:0">
            <button class="btn small" data-pipeline="${v.id}">Ver pipeline</button>
            <button class="btn secondary small" data-editar-vaga="${v.id}">Editar</button>
            <button class="btn danger small" data-excluir-vaga="${v.id}">Excluir</button>
          </div>
        </div>
      </div>`).join("") || '<div class="card"><p class="desc">Nenhuma vaga criada ainda.</p></div>'}`;

  document.getElementById("nova-vaga").addEventListener("click", () => formVaga(null));
  el.querySelectorAll("[data-editar-vaga]").forEach((b) =>
    b.addEventListener("click", () =>
      formVaga(r.vagas.find((v) => v.id === Number(b.dataset.editarVaga))))
  );
  el.querySelectorAll("[data-excluir-vaga]").forEach((b) =>
    b.addEventListener("click", async () => {
      const v = r.vagas.find((x) => x.id === Number(b.dataset.excluirVaga));
      if (!confirm(`Excluir a vaga "${v.titulo}" e todas as candidaturas dela?`)) return;
      await api("/api/gestor/vaga/" + v.id, { method: "DELETE" });
      desenharPainel();
    })
  );
  el.querySelectorAll("[data-pipeline]").forEach((b) =>
    b.addEventListener("click", () => telaPipeline(el, Number(b.dataset.pipeline)))
  );
}

function formVaga(v) {
  modalForm(v ? "Editar vaga" : "Nova vaga", `
    <label class="field">Título da vaga
      <input type="text" id="fv-titulo" value="${v ? esc(v.titulo) : ""}" placeholder="Ex.: Analista de Sistemas Sênior (GTI)">
    </label>
    <label class="field">Cargo
      <select id="fv-cargo">
        ${cargos.map((c) => `<option value="${c.id}" ${v && v.cargo_id === c.id ? "selected" : ""}>${esc(c.nome)}</option>`).join("")}
      </select>
    </label>
    <label class="field">Local <span class="hint">(sugerido no cadastro do candidato)</span>
      <input type="text" id="fv-local" value="${v ? esc(v.local) : ""}" placeholder="Ex.: Secretaria de GTI">
    </label>
    <label class="field">País
      <select id="fv-pais">
        <option value="">Selecione o país</option>
        ${PAISES.map((pa) => `<option value="${pa}" ${v && v.pais === pa ? "selected" : ""}>${pa}</option>`).join("")}
      </select>
    </label>
    <label class="field">Descrição
      <textarea id="fv-desc" rows="3">${v ? esc(v.descricao) : ""}</textarea>
    </label>
    <label class="field">Status
      <select id="fv-status">
        ${["aberta", "pausada", "encerrada"].map((s) =>
          `<option value="${s}" ${v && v.status === s ? "selected" : ""}>${s.charAt(0).toUpperCase() + s.slice(1)}</option>`).join("")}
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
  const porEtapa = {};
  r.etapas.forEach((e) => { porEtapa[e] = []; });
  r.candidaturas.forEach((c) => porEtapa[c.etapa].push(c));

  const cartao = (c) => `
    <div class="kanban-card" draggable="true" data-candidatura="${c.candidatura_id}">
      <div class="nome-card">${esc(c.nome)}</div>
      <div class="sub-card">${c.local ? esc(c.local) : esc(c.email)}</div>
      ${c.match != null ? `<div class="match-card">${c.match}% match</div>` : ""}
      ${c.etapa === "reprovado" && c.motivo_reprovacao ? `<div class="sub-card">${esc(c.motivo_reprovacao)}</div>` : ""}
      <div class="linha-acoes" style="margin-top:8px;gap:6px">
        <button class="btn ghost small" data-detalhe="${c.candidato_id}" style="padding:4px 10px">Relatório</button>
      </div>
      <select data-mover="${c.candidatura_id}" title="Mover para etapa">
        ${r.etapas.map((e) => `<option value="${e}" ${c.etapa === e ? "selected" : ""}>${r.nomes_etapas[e]}</option>`).join("")}
      </select>
    </div>`;

  el.innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
        <div>
          <h2>${esc(r.vaga.titulo)}</h2>
          <p class="desc" style="margin:0">${esc(r.vaga.cargo_nome)}${r.vaga.local ? " · " + esc(r.vaga.local) : ""} · ${r.candidaturas.length} candidato(s)</p>
        </div>
        <div class="linha-acoes" style="margin:0">
          <button class="btn ghost small" id="pp-voltar">← Vagas</button>
          <button class="btn ${modo === "kanban" ? "" : "secondary"} small" id="pp-kanban">Pipeline</button>
          <button class="btn ${modo === "ranking" ? "" : "secondary"} small" id="pp-ranking">Ranking</button>
          <button class="btn secondary small" id="pp-adicionar">+ Adicionar candidato</button>
        </div>
      </div>
    </div>
    ${modo === "kanban" ? `
      <div class="kanban">
        ${r.etapas.map((e) => `
          <div class="kanban-col" data-etapa="${e}">
            <div class="titulo-col"><span>${r.nomes_etapas[e]}</span><span>${porEtapa[e].length}</span></div>
            ${porEtapa[e].map(cartao).join("")}
          </div>`).join("")}
      </div>
      <p class="desc mt">Arraste os cartões entre as colunas ou use o seletor no cartão. Ao mover, você pode notificar o candidato por e-mail (se o SMTP estiver configurado).</p>
      <div id="radar-talentos"></div>`
    : `
      <div class="card">
        <div class="tabela-wrap">
          <table class="tabela">
            <thead><tr><th>#</th><th>Candidato</th><th>Local</th><th class="num">Match</th><th class="num">Etapa</th><th></th></tr></thead>
            <tbody>
              ${r.candidaturas.map((c, i) => `
                <tr>
                  <td>${i + 1}º</td>
                  <td><strong>${esc(c.nome)}</strong><br><span style="color:var(--muted);font-size:.78rem">${esc(c.email)}</span></td>
                  <td>${c.local ? esc(c.local) : "—"}</td>
                  <td class="num">${c.match != null ? `<strong>${c.match}%</strong>` : "—"}</td>
                  <td class="num"><span class="badge ${c.etapa === "reprovado" ? "err" : c.etapa === "contratado" ? "ok" : "neutral"}">${r.nomes_etapas[c.etapa]}</span></td>
                  <td class="num"><button class="btn secondary small" data-detalhe="${c.candidato_id}">Relatório</button></td>
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
          <h2 class="icone-titulo">${icone("alvo")}<span>Radar de talentos</span></h2>
          <p class="desc">${s.sugestoes.length} candidato(s) do seu banco têm 60% ou mais de match com esta vaga e ainda não estão nela:</p>
          <div class="tabela-wrap"><table class="tabela">
            <tbody>
              ${s.sugestoes.map((g) => `
                <tr>
                  <td><strong>${esc(g.nome)}</strong>${g.local ? ` <span style="color:var(--muted);font-size:.8rem">· ${esc(g.local)}</span>` : ""}</td>
                  <td class="num"><strong>${g.match}%</strong></td>
                  <td class="num">
                    <button class="btn ghost small" data-detalhe="${g.candidato_id}">Relatório</button>
                    <button class="btn secondary small" data-radar-add="${g.candidato_id}">Adicionar à vaga</button>
                  </td>
                </tr>`).join("")}
            </tbody>
          </table></div>
        </div>`;
      alvo.querySelectorAll("[data-detalhe]").forEach((b) =>
        b.addEventListener("click", () => abrirDetalheCandidato(Number(b.dataset.detalhe)))
      );
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
    if (!disponiveis.length) return alert("Todos os candidatos cadastrados já estão nesta vaga.");
    modalForm("Adicionar candidato à vaga", `
      <label class="field">Candidato
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
  el.querySelectorAll("[data-detalhe]").forEach((b) =>
    b.addEventListener("click", () => abrirDetalheCandidato(Number(b.dataset.detalhe)))
  );

  async function mover(candidaturaId, etapa) {
    let motivo = "";
    if (etapa === "reprovado") {
      motivo = prompt("Motivo da reprovação (opcional):") || "";
    }
    const notificar = confirm("Notificar o candidato por e-mail sobre esta mudança?\n(OK = sim, Cancelar = não)");
    const resp = await api("/api/gestor/candidatura", {
      method: "POST",
      body: { id: candidaturaId, etapa, motivo, notificar },
    });
    if (resp.aviso_email) alert("Etapa alterada, mas o e-mail não foi enviado: " + resp.aviso_email);
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
  return c ? c.nome : "—";
}

function tabelaCandidatos(lista) {
  if (!lista.length) return "<p class='desc'>Nenhum candidato cadastrado ainda. Compartilhe o link da área do candidato para iniciar as avaliações.</p>";
  return `
    <div class="tabela-wrap">
      <table class="tabela">
        <thead><tr>
          <th>Nome</th><th>Local</th><th>Cargo de interesse</th><th class="num">DISC</th>
          <th class="num">B.A.S.E.</th><th class="num">Match</th><th class="num">Status</th><th></th>
        </tr></thead>
        <tbody>
          ${lista.map((c) => {
            const disc = c.testes.disc ? c.testes.disc.payload.dominante : null;
            const base = c.testes.base ? c.testes.base.payload.dominante : null;
            return `<tr>
              <td><strong>${esc(c.candidato.nome)}</strong>
                ${c.candidato.tipo === "interno" ? ' <span class="badge neutral">Colaborador</span>' : ""}
                <br><span style="color:var(--muted);font-size:.8rem">${esc(c.candidato.email)}</span>
                ${(c.candidato.tags || []).length ? "<br>" + c.candidato.tags.map((t) => `<span class="badge tipo">${esc(t)}</span>`).join(" ") : ""}</td>
              <td>${c.candidato.local ? esc(c.candidato.local) : "—"}</td>
              <td>${esc(nomeCargo(c.candidato.cargo_desejado_id))}</td>
              <td class="num">${disc ? `<span class="badge neutral">${disc} · ${esc(DISC_PERFIS[disc].nome)}</span>` : '<span class="badge tipo">pendente</span>'}</td>
              <td class="num">${base ? `<span class="badge neutral">${esc(BASE_PERFIS[base].nome)}</span>` : '<span class="badge tipo">pendente</span>'}</td>
              <td class="num">${c.match ? `<strong>${c.match.geral}%</strong>` : "—"}</td>
              <td class="num">${c.gaps && c.gaps.respondeu_autoavaliacao ? badgeStatus(c.gaps.status) : '<span class="badge tipo">—</span>'}</td>
              <td class="num"><button class="btn secondary small" data-detalhe="${c.candidato.id}">Ver relatório</button></td>
            </tr>`;
          }).join("")}
        </tbody>
      </table>
    </div>`;
}

function ligarLinhasCandidato(el) {
  el.querySelectorAll("[data-detalhe]").forEach((b) =>
    b.addEventListener("click", () => abrirDetalheCandidato(Number(b.dataset.detalhe)))
  );
}

function abaCandidatos(el) {
  const locais = [...new Set(candidatos.map((c) => c.candidato.local).filter(Boolean))].sort();
  const tags = [...new Set(candidatos.flatMap((c) => c.candidato.tags || []))].sort();

  el.innerHTML = `<div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:6px">
      <h2 style="margin:0">Banco de talentos (${candidatos.length})</h2>
      ${candidatos.length ? `<button class="btn secondary small" id="exportar-csv">Exportar planilha (CSV)</button>` : ""}
    </div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0 4px">
      <input type="text" id="ft-busca" placeholder="Buscar nome ou e-mail..." style="margin:0">
      <select id="ft-local" style="margin:0"><option value="">Todos os locais</option>
        ${locais.map((l) => `<option value="${esc(l)}">${esc(l)}</option>`).join("")}</select>
      <select id="ft-cargo" style="margin:0"><option value="">Todos os cargos</option>
        ${cargos.map((c) => `<option value="${c.id}">${esc(c.nome)}</option>`).join("")}</select>
      <select id="ft-tag" style="margin:0"><option value="">Todas as tags</option>
        ${tags.map((t) => `<option value="${esc(t)}">${esc(t)}</option>`).join("")}</select>
      <select id="ft-match" style="margin:0">
        <option value="">Qualquer match</option>
        <option value="80">Match 80%+</option>
        <option value="60">Match 60%+</option>
        <option value="40">Match 40%+</option>
      </select>
      <select id="ft-tipo" style="margin:0">
        <option value="">Todos os perfis</option>
        <option value="externo">Candidatos</option>
        <option value="interno">Colaboradores internos</option>
      </select>
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
      if (busca && !(c.candidato.nome + " " + c.candidato.email).toLowerCase().includes(busca)) return false;
      if (local && c.candidato.local !== local) return false;
      if (cargo && c.candidato.cargo_desejado_id !== cargo) return false;
      if (tag && !(c.candidato.tags || []).includes(tag)) return false;
      if (matchMin && !(c.match && c.match.geral >= matchMin)) return false;
      if (tipoSel && (c.candidato.tipo || "externo") !== tipoSel) return false;
      return true;
    });
    document.getElementById("ft-resultado").innerHTML = tabelaCandidatos(filtrados);
    ligarLinhasCandidato(el);
  };
  ["ft-busca", "ft-local", "ft-cargo", "ft-tag", "ft-match", "ft-tipo"].forEach((id) =>
    document.getElementById(id).addEventListener(id === "ft-busca" ? "input" : "change", aplicar)
  );
  ligarLinhasCandidato(el);
  const btn = document.getElementById("exportar-csv");
  if (btn) btn.addEventListener("click", exportarCandidatosCsv);
}

function exportarCandidatosCsv() {
  const celula = (v) => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
  const linhas = [[
    "Nome", "E-mail", "Local", "Cargo de interesse", "DISC dominante",
    "BASE dominante", "Aderência competências (%)", "Match geral (%)",
    "Status", "LinkedIn", "Instagram", "Cadastro",
  ]];
  candidatos.forEach((c) => {
    const disc = c.testes.disc ? c.testes.disc.payload.dominante + " " + DISC_PERFIS[c.testes.disc.payload.dominante].nome : "";
    const base = c.testes.base ? BASE_PERFIS[c.testes.base.payload.dominante].nome : "";
    linhas.push([
      c.candidato.nome, c.candidato.email, c.candidato.local,
      nomeCargo(c.candidato.cargo_desejado_id), disc, base,
      c.gaps && c.gaps.respondeu_autoavaliacao ? c.gaps.aderencia : "",
      c.match ? c.match.geral : "",
      c.gaps && c.gaps.respondeu_autoavaliacao
        ? { apto: "Apto", desenvolvimento: "Em desenvolvimento", gap_alto: "Gap alto" }[c.gaps.status]
        : "",
      c.candidato.linkedin, c.candidato.instagram,
      (c.candidato.criado_em || "").slice(0, 10),
    ]);
  });
  const csv = "﻿" + linhas.map((l) => l.map(celula).join(";")).join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  a.download = "candidatos.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}

async function abrirDetalheCandidato(id) {
  const c = await api("/api/gestor/candidato/" + id);
  const blocos = [];
  if (c.match) blocos.push(`<div class="card">${htmlMatch(c.match, c.gaps ? c.gaps.cargo.nome : "")}</div>`);
  if (c.testes.disc) blocos.push(`<div class="card">${htmlResultadoDisc(c.testes.disc.payload)}</div>`);
  if (c.testes.base) blocos.push(`<div class="card">${htmlResultadoBase(c.testes.base.payload)}</div>`);
  if (c.quiz) blocos.push(`<div class="card">${tituloIcone("bloco", "Teste de conhecimento")}
    <div class="perfil-destaque"><div class="titulo">${c.quiz.pct}% de acerto</div>
    <div>${c.quiz.acertos} de ${c.quiz.total} questões corretas</div></div></div>`);

  // entrevista estruturada
  const nomeCargoInteresse = nomeCargo(c.candidato.cargo_desejado_id);
  blocos.push(`<div class="card">
    ${tituloIcone("usuarios", "Entrevista estruturada")}
    ${c.entrevista ? `
      <div class="perfil-destaque">
        <div class="titulo">Média ${c.entrevista.media.toFixed(1)} de 5 (${c.entrevista.pct}%)</div>
        <div>Avaliada por ${esc(c.entrevista.gestor)} em ${esc((c.entrevista.criado_em || "").slice(0, 10))}</div>
      </div>
      ${c.entrevista.payload.observacao ? `<p>${esc(c.entrevista.payload.observacao)}</p>` : ""}`
      : '<p class="desc">Nenhuma entrevista registrada ainda. O resultado entra no match com peso de 20%.</p>'}
    <button class="btn secondary small no-print" id="btn-entrevista">${c.entrevista ? "Registrar nova entrevista" : "Registrar entrevista"}</button>
  </div>`);

  // análise de currículo por IA
  const ia = c.analise_ia;
  blocos.push(`<div class="card">
    ${tituloIcone("relatorio", "Análise do currículo por IA")}
    ${ia ? `
      <div class="perfil-destaque">
        <div class="titulo">Aderência do currículo ao cargo: ${ia.aderencia_curriculo}%</div>
        <div>${esc(ia.recomendacao)}</div>
      </div>
      <p>${esc(ia.resumo)}</p>
      <div class="grid cols-2 mt">
        <div><h3>Formações e certificações</h3>
          <ul class="lista-simples">${(ia.formacoes || []).map((f) => `<li>${esc(f)}</li>`).join("") || "<li>Nenhuma identificada</li>"}</ul></div>
        <div><h3>Experiências</h3>
          <ul class="lista-simples">${(ia.experiencias || []).map((f) => `<li>${esc(f)}</li>`).join("") || "<li>Nenhuma identificada</li>"}</ul></div>
      </div>
      <h3>Pontos fortes</h3>
      <ul class="lista-simples">${(ia.pontos_fortes || []).map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      ${(ia.divergencias || []).length ? `
        <h3>Divergências entre autoavaliação e currículo</h3>
        <div class="tabela-wrap"><table class="tabela">
          <thead><tr><th>Competência</th><th>Declarado</th><th>No currículo</th><th>Comentário</th></tr></thead>
          <tbody>${ia.divergencias.map((d) => `
            <tr><td><strong>${esc(d.competencia)}</strong></td><td>${esc(d.nivel_declarado)}</td>
            <td>${esc(d.evidencia_no_curriculo)}</td><td>${esc(d.comentario)}</td></tr>`).join("")}</tbody>
        </table></div>` : "<p>Nenhuma divergência relevante entre a autoavaliação e o currículo.</p>"}`
      : '<p class="desc">A IA lê o currículo em PDF, cruza com a autoavaliação de competências e aponta divergências. Requer a chave da API configurada em Configurações.</p>'}
    <div class="linha-acoes no-print">
      <button class="btn secondary small" id="btn-ia" ${c.candidato.curriculo ? "" : "disabled title='Sem currículo enviado'"}>${ia ? "Analisar novamente" : "Analisar currículo com IA"}</button>
      <span id="ia-status" class="desc" style="margin:0"></span>
    </div>
  </div>`);

  // recrutamento interno: match com todos os cargos
  if ((c.matches_cargos || []).some((mc) => mc.match != null)) {
    blocos.push(`<div class="card">
      ${tituloIcone("camadas", "Match com todos os cargos (mobilidade interna)")}
      <p class="desc">Compara este candidato com todos os cargos mapeados. Útil para realocação e upgrade de cargo.</p>
      <div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>Cargo</th><th class="num">Match</th></tr></thead>
        <tbody>${c.matches_cargos.map((mc) => `
          <tr><td><strong>${esc(mc.cargo_nome)}</strong>${mc.nivel ? ' <span class="badge tipo">' + esc(mc.nivel) + "</span>" : ""}</td>
          <td class="num">${mc.match != null ? `<strong>${mc.match}%</strong>` : "—"}</td></tr>`).join("")}</tbody>
      </table></div>
    </div>`);
  }

  if (c.gaps) blocos.push(`<div class="card">${htmlMatrizGaps(c.gaps)}</div>`);

  // linha do tempo e anotações
  blocos.push(`<div class="card">
    ${tituloIcone("documento", "Linha do tempo e anotações")}
    <div class="linha-acoes no-print" style="margin-top:4px">
      <input type="text" id="nova-anotacao" placeholder="Escreva uma anotação sobre o candidato..." style="flex:1;min-width:220px;margin:0">
      <button class="btn secondary small" id="btn-anotar">Anotar</button>
    </div>
    <div class="timeline">
      ${(c.eventos || []).map((ev) => `
        <div class="timeline-item ${ev.tipo === "anotacao" || ev.tipo === "etapa" ? "destaque" : ""}">
          <div class="quando">${esc((ev.criado_em || "").slice(0, 16).replace("T", " "))} · ${esc(ev.autor)}</div>
          <div class="texto-evento">${ev.tipo === "anotacao" ? "<strong>Anotação:</strong> " : ""}${esc(ev.texto)}</div>
        </div>`).join("") || '<p class="desc">Nenhum evento registrado.</p>'}
    </div>
  </div>`);
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal">
      <button class="btn ghost small fechar" id="modal-fechar">${icone("fechar")} Fechar</button>
      <h2>${esc(c.candidato.nome)} ${c.candidato.tipo === "interno" ? '<span class="badge neutral">Colaborador interno</span>' : ""}</h2>
      <p class="desc">${esc(c.candidato.email)}
        ${c.candidato.telefone ? " · Tel: " + esc(c.candidato.telefone) : ""}
        ${c.candidato.local ? " · Local: " + esc(c.candidato.local) : ""}
        ${c.candidato.cargo_atual ? " · Cargo atual: " + esc(c.candidato.cargo_atual) : ""}
        ${c.candidato.funcao ? " · Função: " + esc(c.candidato.funcao) : ""}
        · Interesse: ${esc(nomeCargo(c.candidato.cargo_desejado_id))}
        · Cadastro: ${esc((c.candidato.criado_em || "").slice(0, 10))}</p>
      <div class="linha-acoes no-print">
        ${c.candidato.linkedin ? `<a class="btn secondary small" target="_blank" rel="noopener" href="${esc(urlPerfil(c.candidato.linkedin, "linkedin"))}">${icone("link")} LinkedIn</a>` : ""}
        ${c.candidato.instagram ? `<a class="btn secondary small" target="_blank" rel="noopener" href="${esc(urlPerfil(c.candidato.instagram, "instagram"))}">${icone("link")} Instagram</a>` : ""}
        ${c.candidato.curriculo ? `<a class="btn secondary small" href="/api/gestor/curriculo/${c.candidato.id}?t=${Date.now()}" id="baixar-cv">${icone("anexo")} Baixar currículo</a>` : '<span class="badge tipo">sem currículo</span>'}
        <button class="btn secondary small" id="btn-email-manual">Enviar e-mail</button>
        <button class="btn secondary small" id="btn-relatorio-pdf" data-cand="${c.candidato.id}">${icone("documento")} Relatório em PDF</button>
        <button class="btn danger small" id="btn-anonimizar" title="Remove os dados pessoais e mantém as estatísticas">Anonimizar (LGPD)</button>
        <button class="btn danger small" id="excluir-cand">${icone("lixeira")} Excluir candidato</button>
      </div>
      <div class="no-print" style="margin:14px 0 4px">
        <span style="font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em">Tags:</span>
        <span id="tags-lista">${(c.candidato.tags || []).map((t) =>
          `<span class="badge tipo" style="margin:0 3px">${esc(t)} <a href="#" data-remover-tag="${esc(t)}" style="color:inherit;text-decoration:none">×</a></span>`).join("")}</span>
        <input type="text" id="nova-tag" list="tags-existentes" placeholder="+ tag"
          style="width:130px;display:inline-block;margin:0 0 0 6px;padding:5px 10px;font-size:.78rem">
        <datalist id="tags-existentes"></datalist>
      </div>
      ${blocos.join("") || "<p class='mt'>Este candidato ainda não concluiu nenhum teste.</p>"}
    </div>`;
  document.body.appendChild(fundo);
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fundo.remove(); });
  fundo.querySelector("#modal-fechar").addEventListener("click", () => fundo.remove());
  const baixar = fundo.querySelector("#baixar-cv");
  if (baixar) {
    baixar.addEventListener("click", async (ev) => {
      ev.preventDefault();
      const resp = await fetch("/api/gestor/curriculo/" + c.candidato.id, {
        headers: { "X-Gestor-Token": localStorage.getItem("gestor_token") },
      });
      if (!resp.ok) return alert("Não foi possível baixar o currículo.");
      const blob = await resp.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "curriculo_" + c.candidato.nome.replace(/\s+/g, "_") + ".pdf";
      a.click();
      URL.revokeObjectURL(a.href);
    });
  }
  fundo.querySelector("#excluir-cand").addEventListener("click", async () => {
    if (!confirm(`Excluir ${c.candidato.nome} e todos os seus resultados? Esta ação não pode ser desfeita.`)) return;
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
    modalForm("Enviar e-mail para " + c.candidato.nome, `
      <p class="desc">Você pode usar os campos {nome}, {vaga} e {link} no texto: eles são preenchidos automaticamente.</p>
      <label class="field">Assunto <input type="text" id="em-assunto"></label>
      <label class="field">Mensagem <textarea id="em-corpo" rows="7" placeholder="Olá, {nome}!"></textarea></label>`,
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
    btn.textContent = "Gerando…";
    try {
      const resp = await fetch("/api/gestor/candidato/" + id + "/relatorio.pdf", {
        headers: { "X-Gestor-Token": localStorage.getItem("gestor_token") },
      });
      if (!resp.ok) {
        const d = await resp.json().catch(() => ({}));
        throw new Error(d.erro || "Não foi possível gerar o relatório");
      }
      const blob = await resp.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "relatorio-" + (c.candidato.nome || "candidato").replace(/[^a-z0-9]+/gi, "-").toLowerCase() + ".pdf";
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
    if (!confirm("Anonimizar " + c.candidato.nome + "?\n\nNome, contato, redes, currículo e histórico serão removidos em definitivo. As estatísticas (testes e match) são mantidas de forma anônima. Esta ação não pode ser desfeita.")) return;
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
      : [{ id: 0, texto: "Avaliação geral da entrevista" }];
    modalForm("Scorecard de entrevista: " + c.candidato.nome, `
      <p class="desc">Dê uma nota de 1 a 5 para cada critério${nomeCargoInteresse !== "—" ? " (roteiro do cargo " + esc(nomeCargoInteresse) + ")" : ""}. As perguntas do roteiro são definidas em Cargos e funções.</p>
      ${perguntas.map((p) => `
        <div class="comp-item">
          <div class="nome">${esc(p.texto)}</div>
          <div class="escala" data-perg="${p.id}">
            ${[1, 2, 3, 4, 5].map((n) => `<button data-v="${n}">${n}</button>`).join("")}
          </div>
        </div>`).join("")}
      <label class="field mt">Observações gerais
        <textarea id="ent-obs" rows="3" placeholder="Impressões, próximos passos..."></textarea>
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
    status.textContent = "Analisando o currículo... isso pode levar até um minuto.";
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
          <h2>Mapeamento de cargos e funções</h2>
          <p class="desc" style="margin:0">Defina as competências, formações, experiências e o nível exigido por cada cargo. É este mapeamento que alimenta a matriz de gaps.</p>
        </div>
        <button class="btn" id="novo-cargo">+ Novo cargo</button>
      </div>
    </div>
    <div id="lista-cargos">
      ${cargos.map((c) => cartaoCargo(c)).join("") || "<div class='card'><p class='desc'>Nenhum cargo cadastrado.</p></div>"}
    </div>`;

  document.getElementById("novo-cargo").addEventListener("click", () => formCargo(null));
  el.querySelectorAll("[data-editar-cargo]").forEach((b) =>
    b.addEventListener("click", () => formCargo(cargos.find((c) => c.id === Number(b.dataset.editarCargo))))
  );
  el.querySelectorAll("[data-excluir-cargo]").forEach((b) =>
    b.addEventListener("click", async () => {
      const c = cargos.find((x) => x.id === Number(b.dataset.excluirCargo));
      if (!confirm(`Excluir o cargo "${c.nome}" e todas as suas competências?`)) return;
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
      if (!confirm("Excluir esta competência?")) return;
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
          <h2>${esc(c.nome)} ${c.nivel ? `<span class="badge neutral">${esc(c.nivel)}</span>` : ""}</h2>
          <p class="desc" style="margin:0">${esc(c.area)}${c.descricao ? ". " + esc(c.descricao) : ""}</p>
          <p style="margin-top:8px">
            ${c.disc_alvo ? `<span class="badge tipo">DISC desejado: ${esc(DISC_PERFIS[c.disc_alvo].nome)}</span> ` : ""}
            ${c.base_alvo ? `<span class="badge tipo">B.A.S.E. desejado: ${esc(BASE_PERFIS[c.base_alvo].nome)}</span>` : ""}
          </p>
        </div>
        <div class="linha-acoes" style="margin:0">
          <button class="btn secondary small" data-editar-cargo="${c.id}">Editar</button>
          <button class="btn danger small" data-excluir-cargo="${c.id}">Excluir</button>
        </div>
      </div>
      <div class="tabela-wrap mt">
        <table class="tabela">
          <thead><tr><th>Competência</th><th>Tipo</th><th class="num">Nível exigido</th><th class="num">Obrigatória</th><th></th></tr></thead>
          <tbody>
            ${c.competencias.map((k) => `
              <tr>
                <td>${esc(k.nome)}</td>
                <td><span class="badge tipo">${esc(TIPOS_COMPETENCIA[k.tipo] || k.tipo)}</span></td>
                <td class="num">${k.nivel_requerido}</td>
                <td class="num">${k.obrigatoria ? '<span class="badge neutral">Sim</span>' : "—"}</td>
                <td class="num">
                  <button class="btn ghost small" data-editar-comp="${c.id}:${k.id}" title="Editar">${icone("lapis")}</button>
                  <button class="btn ghost small" data-excluir-comp="${k.id}" title="Excluir">${icone("lixeira")}</button>
                </td>
              </tr>`).join("") || '<tr><td colspan="5" style="color:var(--muted)">Nenhuma competência cadastrada.</td></tr>'}
          </tbody>
        </table>
      </div>
      <div class="linha-acoes" style="margin-top:14px">
        <button class="btn secondary small" data-nova-comp="${c.id}">+ Adicionar competência</button>
        <button class="btn ghost small" data-avaliacoes="${c.id}">Entrevista e teste de conhecimento</button>
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
      <p class="desc">Roteiro de entrevista e teste de conhecimento usados nas avaliações deste cargo.</p>

      <h3>Roteiro de entrevista (scorecard)</h3>
      ${r.perguntas.map((p) => `
        <div class="comp-item" style="display:flex;justify-content:space-between;align-items:center;gap:10px">
          <div>${esc(p.texto)}</div>
          <button class="btn ghost small" data-del-perg="${p.id}" title="Excluir">${icone("lixeira")}</button>
        </div>`).join("") || '<p class="desc">Nenhuma pergunta ainda. Sem roteiro, o scorecard usa uma avaliação geral única.</p>'}
      <div class="linha-acoes" style="margin-top:10px">
        <input type="text" id="nova-perg" placeholder="Ex.: Como você lida com prazos apertados?" style="flex:1;min-width:220px;margin:0">
        <button class="btn secondary small" id="add-perg">Adicionar pergunta</button>
      </div>

      <h3 style="margin-top:28px">Teste de conhecimento (múltipla escolha)</h3>
      ${r.questoes.map((q) => `
        <div class="comp-item">
          <div style="display:flex;justify-content:space-between;gap:10px">
            <div class="nome" style="margin-bottom:6px">${esc(q.pergunta)}</div>
            <button class="btn ghost small" data-del-quest="${q.id}" title="Excluir">${icone("lixeira")}</button>
          </div>
          <div style="font-size:.82rem;color:var(--muted)">
            ${q.opcoes.map((op, j) => `${String.fromCharCode(65 + j)}) ${esc(op)}${j === q.correta ? " ✓" : ""}`).join(" &nbsp;·&nbsp; ")}
          </div>
        </div>`).join("") || '<p class="desc">Nenhuma questão ainda. O teste aparece para o candidato quando houver questões, e o resultado entra no match com peso de 20%.</p>'}
      <button class="btn secondary small mt" id="add-quest">+ Nova questão</button>
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
    modalForm("Nova questão: " + cargo.nome, `
      <label class="field">Pergunta
        <textarea id="qz-perg" rows="2" placeholder="Ex.: Qual comando SQL retorna registros únicos?"></textarea>
      </label>
      ${[0, 1, 2, 3].map((j) => `
        <label class="field">Opção ${String.fromCharCode(65 + j)} ${j > 1 ? '<span class="hint">(opcional)</span>' : ""}
          <input type="text" id="qz-op${j}">
        </label>`).join("")}
      <label class="field">Alternativa correta
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
      <button class="btn block" id="mf-salvar">Salvar</button>
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
  modalForm(cargo ? "Editar cargo" : "Novo cargo", `
    <label class="field">Nome do cargo
      <input type="text" id="fc-nome" value="${cargo ? esc(cargo.nome) : ""}" placeholder="Ex.: Analista de Sistemas Sênior">
    </label>
    <label class="field">Área <input type="text" id="fc-area" value="${cargo ? esc(cargo.area) : ""}" placeholder="Ex.: GTI"></label>
    <label class="field">Nível
      <select id="fc-nivel">
        ${["", "Júnior", "Pleno", "Sênior", "Especialista", "Gestão"].map((n) =>
          `<option value="${n}" ${cargo && cargo.nivel === n ? "selected" : ""}>${n || "—"}</option>`).join("")}
      </select>
    </label>
    <label class="field">Descrição
      <textarea id="fc-desc" rows="3" placeholder="Responsabilidades principais">${cargo ? esc(cargo.descricao) : ""}</textarea>
    </label>
    <label class="field">Perfil DISC desejado <span class="hint">(usado no cálculo do match)</span>
      <select id="fc-disc">
        <option value="">Não considerar</option>
        ${["D", "I", "S", "C"].map((k) =>
          `<option value="${k}" ${cargo && cargo.disc_alvo === k ? "selected" : ""}>${DISC_PERFIS[k].nome} (${k})</option>`).join("")}
      </select>
    </label>
    <label class="field">Arquétipo B.A.S.E. desejado <span class="hint">(usado no cálculo do match)</span>
      <select id="fc-base">
        <option value="">Não considerar</option>
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
  modalForm(comp ? "Editar competência" : "Nova competência", `
    <label class="field">Nome da competência
      <input type="text" id="fk-nome" value="${comp ? esc(comp.nome) : ""}" placeholder="Ex.: Certificação Java">
    </label>
    <label class="field">Tipo
      <select id="fk-tipo">
        ${Object.entries(TIPOS_COMPETENCIA).map(([v, r]) =>
          `<option value="${v}" ${comp && comp.tipo === v ? "selected" : ""}>${r}</option>`).join("")}
      </select>
    </label>
    <label class="field">Nível exigido (1 a 5)
      <select id="fk-nivel">
        ${[1, 2, 3, 4, 5].map((n) =>
          `<option value="${n}" ${(comp ? comp.nivel_requerido : 3) === n ? "selected" : ""}>${n}</option>`).join("")}
      </select>
    </label>
    <label class="field" style="display:flex;align-items:center;gap:8px;font-weight:600">
      <input type="checkbox" id="fk-obrig" style="width:auto" ${comp && comp.obrigatoria ? "checked" : ""}>
      Competência obrigatória para exercer a função
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
      <h2>Matriz de gaps consolidada</h2>
      <p class="desc">Selecione um cargo para comparar todos os candidatos com as competências exigidas. Serve também para avaliar upgrade de cargo de quem já está na instituição.</p>
      <label class="field" style="max-width:420px">Cargo
        <select id="mx-cargo">
          <option value="">Selecione um cargo</option>
          ${cargos.map((c) => `<option value="${c.id}">${esc(c.nome)}</option>`).join("")}
        </select>
      </label>
      <div id="mx-resultado"></div>
    </div>`;
  document.getElementById("mx-cargo").addEventListener("change", async (ev) => {
    const cargoId = Number(ev.target.value);
    const alvo = document.getElementById("mx-resultado");
    if (!cargoId) { alvo.innerHTML = ""; return; }
    alvo.innerHTML = "<p class='desc'>Carregando…</p>";
    const r = await api("/api/gestor/matriz?cargo_id=" + cargoId);
    if (!r.linhas.length) {
      alvo.innerHTML = "<p class='desc'>Nenhum candidato cadastrado.</p>";
      return;
    }
    const comps = r.cargo.competencias;
    alvo.innerHTML = `
      <div class="tabela-wrap">
        <table class="tabela">
          <thead>
            <tr>
              <th>Candidato</th><th class="num">Match</th><th class="num">Aderência</th><th class="num">Status</th>
              ${comps.map((k) => `<th class="num" title="${esc(k.nome)} (exigido: ${k.nivel_requerido})">${esc(k.nome.length > 18 ? k.nome.slice(0, 17) + "…" : k.nome)}<br><span style="font-weight:400">exig. ${k.nivel_requerido}</span></th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${r.linhas.map((l) => `
              <tr>
                <td><strong>${esc(l.nome)}</strong>${l.local ? `<br><span style="color:var(--muted);font-size:.76rem">${esc(l.local)}</span>` : ""}</td>
                <td class="num">${l.match != null ? `<strong>${l.match}%</strong>` : "—"}</td>
                <td class="num">${l.respondeu ? l.aderencia + "%" : "—"}</td>
                <td class="num">${l.respondeu ? badgeStatus(l.status) : '<span class="badge tipo">sem autoavaliação</span>'}</td>
                ${l.itens.map((i) => `
                  <td class="num"><span class="celula-gap ${classeGap(i)}">${i.respondida ? i.nivel_atual + "/" + i.nivel_requerido : "—"}</span></td>`).join("")}
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
      <p class="desc mt">Legenda: <span class="celula-gap ok">OK</span> atende ·
        <span class="celula-gap medio">gap 1–2</span> desenvolvimento ·
        <span class="celula-gap alto">gap 3+</span> gap alto ·
        <span class="celula-gap vazio">—</span> sem resposta</p>`;
  });
}

// ------------------------------------------------ configurações
async function abaConfig(el) {
  const linkCandidato = location.origin + "/candidato";
  const info = infoGestor();
  el.innerHTML = `
    <div class="grid cols-2">
      <div class="card">
        <h2 class="icone-titulo">${icone("link")}<span>Seus links públicos</span></h2>
        <p class="desc"><strong style="color:var(--text)">Sua página de vagas</strong>: mostra apenas as vagas do seu local${info.local ? " (" + esc(info.local) + ")" : " (sem local definido: mostra todas)"}. Quem se candidatar por ela entra direto no seu processo:</p>
        <input type="text" readonly value="${esc(location.origin + "/vagas?g=" + (info.login || ""))}" id="cfg-link-vagas">
        <button class="btn secondary small mt" id="cfg-copiar-vagas">Copiar página de vagas</button>
        <p class="desc" style="margin-top:16px"><strong style="color:var(--text)">Cadastro direto</strong> (sem vaga específica):</p>
        <input type="text" readonly value="${esc(linkCandidato)}" id="cfg-link">
        <button class="btn secondary small mt" id="cfg-copiar">Copiar link</button>
      </div>
      <div class="card">
        <h2 class="icone-titulo">${icone("chave")}<span>Alterar minha senha</span></h2>
        <p class="desc">Conta: <strong>${esc(info.nome || "")}</strong> (${esc(info.login || "")})</p>
        <label class="field">Senha atual <input type="password" id="cfg-atual" autocomplete="current-password"></label>
        <label class="field">Nova senha (mín. 6 caracteres) <input type="password" id="cfg-nova" autocomplete="new-password"></label>
        <div class="form-erro" id="cfg-erro"></div>
        <button class="btn" id="cfg-salvar">Alterar senha</button>
      </div>
    </div>
    <div id="cfg-gestores"></div>
    <div id="cfg-integracoes"></div>`;
  document.getElementById("cfg-copiar").addEventListener("click", () => {
    navigator.clipboard.writeText(linkCandidato);
    document.getElementById("cfg-copiar").textContent = "Copiado ✓";
  });
  document.getElementById("cfg-copiar-vagas").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("cfg-link-vagas").value);
    document.getElementById("cfg-copiar-vagas").textContent = "Copiado ✓";
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
      erro.textContent = "Senha alterada com sucesso.";
      document.getElementById("cfg-atual").value = "";
      document.getElementById("cfg-nova").value = "";
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
  if (info.admin) {
    await secaoGestores(document.getElementById("cfg-gestores"));
    await secaoIntegracoes(document.getElementById("cfg-integracoes"));
  }
}

async function secaoIntegracoes(el) {
  const r = await api("/api/gestor/integracoes");
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("engrenagem")}<span>Integrações (serviços pagos)</span></h2>
      <p class="desc">Estes são os únicos recursos do sistema que dependem de serviços externos. Tudo o mais funciona sem custo. Sem estas credenciais, os botões de IA e as notificações por e-mail apenas ficam indisponíveis.</p>
      <div class="grid cols-2">
        <div>
          <h3>Análise de currículo por IA</h3>
          <p class="desc" style="font-size:.82rem">Usa a API da Anthropic (Claude). Crie uma chave em console.anthropic.com. Custo por análise: centavos de dólar. Status:
            ${r.ia_configurada ? '<span class="badge ok">Configurada (...' + esc(r.ia_final) + ")</span>" : '<span class="badge warn">Não configurada</span>'}</p>
          <label class="field">Chave da API Anthropic
            <input type="password" id="int-chave" placeholder="${r.ia_configurada ? "Preencher apenas para trocar" : "sk-ant-..."}" autocomplete="off">
          </label>
        </div>
        <div>
          <h3>E-mail para candidatos (SMTP)</h3>
          <p class="desc" style="font-size:.82rem">Com o SMTP configurado, o sistema envia automaticamente: confirmação de inscrição com link de acesso ao candidato, avisos de mudança de etapa, e alertas aos gestores (novo candidato e avaliação completa com o match). Funciona com qualquer SMTP; no Gmail use uma senha de app. Status:
            ${r.smtp_host ? '<span class="badge ok">Configurado</span>' : '<span class="badge warn">Não configurado</span>'}</p>
          <label class="field">Servidor SMTP <input type="text" id="int-host" value="${esc(r.smtp_host)}" placeholder="smtp.gmail.com"></label>
          <div class="grid cols-2">
            <label class="field">Porta <span class="hint">(587 STARTTLS ou 465 SSL)</span><input type="text" id="int-porta" value="${esc(r.smtp_porta)}" placeholder="587"></label>
            <label class="field">Usuário <input type="text" id="int-usuario" value="${esc(r.smtp_usuario)}" placeholder="voce@gmail.com"></label>
          </div>
          <label class="field">Senha ${r.smtp_senha_configurada ? '<span class="hint">(preencher apenas para trocar)</span>' : ""}
            <input type="password" id="int-senha" autocomplete="off">
          </label>
          <label class="field">Remetente <span class="hint">(opcional)</span>
            <input type="text" id="int-remetente" value="${esc(r.smtp_remetente)}" placeholder="selecao@suaempresa.com">
          </label>
        </div>
      </div>
      <div class="grid cols-2 mt">
        <label class="field">Endereço público do sistema <span class="hint">(usado nos links dos e-mails)</span>
          <input type="text" id="int-url" value="${esc(r.url_publica)}" placeholder="http://localhost:8080 ou https://rh.seudominio.com">
        </label>
        <label class="field">Retenção de dados (LGPD) <span class="hint">(anonimizar candidatos automaticamente após)</span>
          <select id="int-retencao">
            <option value="0" ${r.retencao_meses === "0" ? "selected" : ""}>Nunca (manter tudo)</option>
            ${[6, 12, 24, 36].map((m) => `<option value="${m}" ${r.retencao_meses === String(m) ? "selected" : ""}>${m} meses</option>`).join("")}
          </select>
        </label>
      </div>
      <div class="form-erro" id="int-erro"></div>
      <div class="linha-acoes">
        <button class="btn" id="int-salvar">Salvar integrações</button>
        <button class="btn secondary" id="int-testar">Salvar e enviar e-mail de teste</button>
      </div>
      <p class="desc" style="font-size:.8rem;margin-top:6px">O e-mail de teste vai para o endereço cadastrado na sua conta de gestor.</p>
    </div>
    <div id="cfg-templates"></div>`;
  document.getElementById("int-salvar").addEventListener("click", async () => {
    const erro = document.getElementById("int-erro");
    erro.textContent = "";
    const corpo = {
      smtp_host: document.getElementById("int-host").value.trim(),
      smtp_porta: document.getElementById("int-porta").value.trim(),
      smtp_usuario: document.getElementById("int-usuario").value.trim(),
      smtp_remetente: document.getElementById("int-remetente").value.trim(),
      url_publica: document.getElementById("int-url").value.trim(),
      retencao_meses: document.getElementById("int-retencao").value,
    };
    const chave = document.getElementById("int-chave").value.trim();
    if (chave) corpo.anthropic_api_key = chave;
    const senha = document.getElementById("int-senha").value;
    if (senha) corpo.smtp_senha = senha;
    try {
      await api("/api/gestor/integracoes", { method: "POST", body: corpo });
      erro.style.color = "var(--ok)";
      erro.textContent = "Integrações salvas.";
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
  document.getElementById("int-testar").addEventListener("click", async () => {
    const erro = document.getElementById("int-erro");
    erro.style.color = "var(--text-2)";
    erro.textContent = "Salvando e enviando e-mail de teste…";
    const corpo = {
      smtp_host: document.getElementById("int-host").value.trim(),
      smtp_porta: document.getElementById("int-porta").value.trim(),
      smtp_usuario: document.getElementById("int-usuario").value.trim(),
      smtp_remetente: document.getElementById("int-remetente").value.trim(),
      url_publica: document.getElementById("int-url").value.trim(),
      retencao_meses: document.getElementById("int-retencao").value,
    };
    const senha = document.getElementById("int-senha").value;
    if (senha) corpo.smtp_senha = senha;
    try {
      await api("/api/gestor/integracoes", { method: "POST", body: corpo });
      const r = await api("/api/gestor/integracoes/teste", { method: "POST", body: {} });
      erro.style.color = "var(--ok)";
      erro.textContent = "E-mail de teste enviado para " + r.destino + ". Verifique a caixa de entrada (e o spam).";
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
  await secaoTemplates(document.getElementById("cfg-templates"));
}

async function secaoTemplates(el) {
  const r = await api("/api/gestor/templates");
  const chaves = Object.keys(r.nomes);
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("bloco")}<span>Modelos de e-mail</span></h2>
      <p class="desc">Personalize os textos enviados aos candidatos. Campos disponíveis:
        <code>{nome}</code>, <code>{vaga}</code>, <code>{link}</code> (link pessoal de acesso), <code>{local}</code> e <code>{etapa}</code>.
        Deixe em branco para voltar ao texto padrão.</p>
      ${chaves.map((k) => `
        <div class="comp-item">
          <div class="nome">${esc(r.nomes[k])}</div>
          <label class="field" style="margin-bottom:8px">Assunto
            <input type="text" id="tp-assunto-${k}" value="${esc(r.templates[k].assunto)}">
          </label>
          <label class="field" style="margin-bottom:0">Mensagem
            <textarea id="tp-corpo-${k}" rows="4">${esc(r.templates[k].corpo)}</textarea>
          </label>
        </div>`).join("")}
      <div class="form-erro" id="tp-erro"></div>
      <button class="btn mt" id="tp-salvar">Salvar modelos</button>
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
      erro.textContent = "Modelos salvos.";
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
}

async function secaoGestores(el) {
  const r = await api("/api/gestor/gestores");
  el.innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2 class="icone-titulo">${icone("usuarios")}<span>Contas de gestor</span></h2>
          <p class="desc" style="margin:0">Cada gestor entra com o próprio login e senha. Gestores vinculados a um local veem apenas os candidatos que fizeram a avaliação naquele local; contas sem local (ou administradoras) veem todos.</p>
        </div>
        <button class="btn" id="novo-gestor">+ Novo gestor</button>
      </div>
      <div class="tabela-wrap mt">
        <table class="tabela">
          <thead><tr><th>Nome</th><th>Login</th><th>E-mail</th><th>Local</th><th class="num">Perfil</th><th></th></tr></thead>
          <tbody>
            ${r.gestores.map((g) => `
              <tr>
                <td><strong>${esc(g.nome)}</strong></td>
                <td>${esc(g.login)}</td>
                <td>${g.email ? esc(g.email) : '<span class="badge warn">sem e-mail</span>'}</td>
                <td>${g.local ? esc(g.local) : '<span style="color:var(--muted)">todos os locais</span>'}</td>
                <td class="num">${g.admin ? '<span class="badge neutral">Administrador</span>' : '<span class="badge tipo">Gestor</span>'}</td>
                <td class="num">
                  <button class="btn ghost small" data-editar-gestor="${g.id}" title="Editar">${icone("lapis")}</button>
                  <button class="btn ghost small" data-excluir-gestor="${g.id}" title="Excluir">${icone("lixeira")}</button>
                </td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
    </div>`;
  document.getElementById("novo-gestor").addEventListener("click", () => formGestor(null));
  el.querySelectorAll("[data-editar-gestor]").forEach((b) =>
    b.addEventListener("click", () =>
      formGestor(r.gestores.find((g) => g.id === Number(b.dataset.editarGestor)))
    )
  );
  el.querySelectorAll("[data-excluir-gestor]").forEach((b) =>
    b.addEventListener("click", async () => {
      const g = r.gestores.find((x) => x.id === Number(b.dataset.excluirGestor));
      if (!confirm(`Excluir a conta de ${g.nome} (${g.login})?`)) return;
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
  modalForm(g ? "Editar gestor" : "Novo gestor", `
    <label class="field">Nome
      <input type="text" id="fg-nome" value="${g ? esc(g.nome) : ""}" placeholder="Ex.: Maria Andrade">
    </label>
    <label class="field">Login ${g ? '<span class="hint">(não pode ser alterado)</span>' : ""}
      <input type="text" id="fg-login" value="${g ? esc(g.login) : ""}" placeholder="ex.: maria.andrade" ${g ? "disabled" : ""}>
    </label>
    <label class="field">E-mail <span class="hint">(recebe avisos de novos candidatos e avaliações do seu local)</span>
      <input type="email" id="fg-email" value="${g ? esc(g.email || "") : ""}" placeholder="gestor@email.com">
    </label>
    <label class="field">Local / instituição <span class="hint">(deixe vazio para ver todos os candidatos)</span>
      <input type="text" id="fg-local" value="${g ? esc(g.local) : ""}" placeholder="Ex.: Secretaria de GTI">
    </label>
    <label class="field">${g ? "Nova senha <span class='hint'>(deixe vazio para manter a atual)</span>" : "Senha (mín. 6 caracteres)"}
      <input type="password" id="fg-senha" autocomplete="new-password">
    </label>
    <label class="field" style="display:flex;align-items:center;gap:8px">
      <input type="checkbox" id="fg-admin" style="width:auto" ${g && g.admin ? "checked" : ""}>
      Administrador (gerencia contas e vê todos os locais)
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
