/* =====================================================================
   Área do Candidato: cadastro → testes → autoavaliação → resultados
   O candidato acessa apenas os próprios dados (token individual).
   ===================================================================== */

const app = document.getElementById("app");
let cargos = [];
let me = null; // resumo do candidato (dados + testes + gaps)
let quizQuestoes = null; // questões do teste de conhecimento do cargo de interesse
let vagaEscolhida = Number(new URLSearchParams(location.search).get("vaga")) || null;

// link de acesso vindo do e-mail de confirmação (?token=...)
const tokenDaUrl = new URLSearchParams(location.search).get("token");
if (tokenDaUrl) {
  localStorage.setItem("cand_token", tokenDaUrl);
  history.replaceState(null, "", location.pathname);
}

// ------------------------------------------------ API
async function api(caminho, opcoes = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = localStorage.getItem("cand_token");
  if (token) headers["X-Token"] = token;
  const resp = await fetch(caminho, {
    method: opcoes.method || "GET",
    headers,
    body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
  });
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dados.erro || "Erro de comunicação com o servidor");
  return dados;
}

// ------------------------------------------------ inicialização
async function iniciar() {
  cargos = (await api("/api/cargos")).cargos;
  const token = localStorage.getItem("cand_token");
  if (!token) return telaCadastro();
  try {
    me = await api("/api/candidato/me");
    document.getElementById("btn-sair").classList.remove("oculto");
    document.getElementById("topo-sub").textContent = "Olá, " + me.candidato.nome;
    await carregarQuiz();
    telaPainel();
  } catch (e) {
    localStorage.removeItem("cand_token");
    telaCadastro();
  }
}

async function carregarQuiz() {
  quizQuestoes = null;
  if (!me.candidato.cargo_desejado_id) return;
  try {
    const r = await api("/api/candidato/quiz");
    if (r.questoes && r.questoes.length) quizQuestoes = r.questoes;
  } catch (e) { /* cargo sem teste de conhecimento */ }
}

document.getElementById("btn-sair").addEventListener("click", () => {
  if (confirm("Sair da sua sessão? Você poderá voltar fazendo um novo cadastro.")) {
    localStorage.removeItem("cand_token");
    location.reload();
  }
});

// ------------------------------------------------ cadastro
function telaCadastro() {
  app.innerHTML = `
    ${vagaEscolhida ? '<div class="card" id="aviso-vaga" style="padding:18px 24px"><p class="desc" style="margin:0">Carregando dados da vaga…</p></div>' : ""}
    <div class="card">
      <h2 class="icone-titulo">${icone("usuario")}<span>Cadastro</span></h2>
      <p class="desc">Preencha seus dados para iniciar a avaliação. Você terá acesso apenas aos seus próprios resultados.</p>
      <label class="field" id="campo-tipo" ${vagaEscolhida ? 'style="display:none"' : ""}>Você está...
        <select id="cad-tipo">
          <option value="externo">Me candidatando a uma oportunidade</option>
          <option value="interno">Já trabalho na instituição (desenvolvimento e upgrade de cargo)</option>
        </select>
      </label>
      <label class="field">Nome completo
        <input type="text" id="cad-nome" placeholder="Seu nome">
      </label>
      <label class="field">E-mail
        <input type="email" id="cad-email" placeholder="voce@email.com">
      </label>
      <label class="field">Onde você está fazendo a avaliação?
        <input type="text" id="cad-local" list="lista-locais"
          placeholder="Instituição, unidade ou setor (ex.: Secretaria de GTI)">
        <datalist id="lista-locais"></datalist>
      </label>
      <label class="field">Cargo/função atual <span class="hint">(opcional)</span>
        <input type="text" id="cad-atual" placeholder="Ex.: Analista de Sistemas Júnior">
      </label>
      <div class="grid cols-2">
        <label class="field">LinkedIn <span class="hint">(opcional)</span>
          <input type="text" id="cad-linkedin" placeholder="linkedin.com/in/seu-perfil">
        </label>
        <label class="field">Instagram <span class="hint">(opcional)</span>
          <input type="text" id="cad-instagram" placeholder="@seu.usuario">
        </label>
      </div>
      <label class="field" id="campo-cargo" ${vagaEscolhida ? 'style="display:none"' : ""}><span id="rotulo-cargo">Cargo/função de interesse</span>
        <select id="cad-desejado">
          <option value="">Selecione o cargo</option>
          ${cargos.map((c) => `<option value="${c.id}">${esc(c.nome)}${c.nivel ? " · " + esc(c.nivel) : ""}</option>`).join("")}
        </select>
      </label>
      <label class="field" style="display:flex;align-items:flex-start;gap:10px;font-weight:340">
        <input type="checkbox" id="cad-consentimento" style="width:auto;margin-top:4px">
        <span>Autorizo o uso dos meus dados pessoais e respostas para este processo
        seletivo e para o banco de talentos, conforme a LGPD. Posso solicitar a
        exclusão dos meus dados a qualquer momento.</span>
      </label>
      <div class="form-erro" id="cad-erro"></div>
      <button class="btn block" id="cad-enviar">Iniciar avaliação</button>
    </div>
    <div class="card" style="padding:20px 24px">
      <p class="desc" style="margin:0 0 10px"><strong style="color:var(--text)">Já tem cadastro?</strong>
        Seu acesso é pelo link pessoal enviado ao seu e-mail. Se o perdeu, receba de novo:</p>
      <div class="linha-acoes" style="margin:0">
        <input type="email" id="rec-email" placeholder="seu e-mail cadastrado" style="flex:1;min-width:200px;margin:0">
        <button class="btn secondary small" id="rec-enviar">Reenviar meu link</button>
      </div>
      <div class="form-erro" id="rec-msg" style="margin-bottom:0"></div>
    </div>`;
  document.getElementById("cad-tipo").addEventListener("change", (ev) => {
    const interno = ev.target.value === "interno";
    document.getElementById("rotulo-cargo").textContent = interno
      ? "Sua função (base da matriz de gaps e do plano de desenvolvimento)"
      : "Cargo/função de interesse";
  });
  document.getElementById("rec-enviar").addEventListener("click", async () => {
    const msg = document.getElementById("rec-msg");
    msg.style.color = "var(--err)";
    msg.textContent = "";
    try {
      await api("/api/candidato/recuperar-acesso", {
        method: "POST",
        body: { email: document.getElementById("rec-email").value.trim() },
      });
      msg.style.color = "var(--ok)";
      msg.textContent = "Se este e-mail estiver cadastrado, o link de acesso chegará em instantes.";
    } catch (e) {
      msg.textContent = e.message;
    }
  });
  api("/api/locais").then((r) => {
    document.getElementById("lista-locais").innerHTML =
      r.locais.map((l) => `<option value="${esc(l)}"></option>`).join("");
  }).catch(() => {});
  if (vagaEscolhida) {
    api("/api/vagas").then((r) => {
      const v = r.vagas.find((x) => x.id === vagaEscolhida);
      const aviso = document.getElementById("aviso-vaga");
      if (!v) {
        vagaEscolhida = null;
        aviso.innerHTML = '<p class="form-erro" style="margin:0">Esta vaga não está mais aberta. Você pode se cadastrar escolhendo um cargo de interesse.</p>';
        document.getElementById("campo-cargo").style.display = "";
        return;
      }
      aviso.innerHTML = `<p class="desc" style="margin:0">Você está se candidatando à vaga:
        <strong style="color:var(--text)">${esc(v.titulo)}</strong> (${esc(v.cargo_nome)}${v.local ? " · " + esc(v.local) : ""})</p>`;
      const campoLocal = document.getElementById("cad-local");
      if (v.local && !campoLocal.value) campoLocal.value = v.local;
    }).catch(() => {});
  }
  document.getElementById("cad-enviar").addEventListener("click", async () => {
    const erro = document.getElementById("cad-erro");
    erro.textContent = "";
    try {
      const r = await api("/api/candidato/cadastro", {
        method: "POST",
        body: {
          nome: document.getElementById("cad-nome").value.trim(),
          email: document.getElementById("cad-email").value.trim(),
          local: document.getElementById("cad-local").value.trim(),
          linkedin: document.getElementById("cad-linkedin").value.trim(),
          instagram: document.getElementById("cad-instagram").value.trim(),
          cargo_atual: document.getElementById("cad-atual").value.trim(),
          cargo_desejado_id: Number(document.getElementById("cad-desejado").value) || null,
          vaga_id: vagaEscolhida,
          tipo: vagaEscolhida ? "externo" : document.getElementById("cad-tipo").value,
          consentimento: document.getElementById("cad-consentimento").checked,
        },
      });
      localStorage.setItem("cand_token", r.token);
      location.reload();
    } catch (e) {
      erro.textContent = e.message;
    }
  });
}

// ------------------------------------------------ painel de passos
function telaPainel() {
  const feitoDisc = !!me.testes.disc;
  const feitoBase = !!me.testes.base;
  const cargoSel = cargos.find((c) => c.id === me.candidato.cargo_desejado_id);
  const feitoAuto = !!(me.gaps && me.gaps.respondeu_autoavaliacao);
  const feitoQuiz = !!me.quiz;
  const tudoPronto = feitoDisc && feitoBase && (!cargoSel || feitoAuto);
  const candidatura = (me.candidaturas || [])[0];
  const badgeEtapa = candidatura
    ? (candidatura.etapa === "reprovado"
        ? '<span class="badge err">' + esc(candidatura.etapa_nome) + "</span>"
        : candidatura.etapa === "contratado"
          ? '<span class="badge ok">' + esc(candidatura.etapa_nome) + "</span>"
          : '<span class="badge neutral">' + esc(candidatura.etapa_nome) + "</span>")
    : "";

  const passo = (ic, titulo, sub, feito, botao, acao, desabilitado) => `
    <div class="passo">
      <div class="icone">${icone(ic)}</div>
      <div class="info">
        <div class="titulo">${titulo}</div>
        <div class="sub">${sub}</div>
      </div>
      ${feito ? '<span class="badge ok">Concluído</span>' : ""}
      <button class="btn ${feito ? "secondary" : ""} small" data-acao="${acao}" ${desabilitado ? "disabled" : ""}>${botao}</button>
    </div>`;

  app.innerHTML = `
    <div class="card">
      <h2>Sua jornada de avaliação</h2>
      <p class="desc">${cargoSel
        ? `Cargo de interesse: <strong>${esc(cargoSel.nome)}</strong>`
        : "Você ainda não selecionou um cargo de interesse, por isso a matriz de gaps ficará indisponível."}</p>
      ${candidatura ? `<p class="desc" style="margin-bottom:0">Vaga: <strong style="color:var(--text)">${esc(candidatura.vaga_titulo)}</strong> · Status da candidatura: ${badgeEtapa}</p>` : ""}
    </div>
    ${passo("camadas", "Teste DISC", "24 blocos · escolha a palavra que MAIS e a que MENOS se parece com você", feitoDisc, feitoDisc ? "Refazer" : "Iniciar", "disc")}
    ${passo("bussola", "Teste B.A.S.E.", "6 rodadas · ordene as cartas da que mais combina com você para a que menos combina", feitoBase, feitoBase ? "Refazer" : "Iniciar", "base")}
    ${cargoSel ? passo("barras", "Autoavaliação de competências", `Avalie seu nível em cada competência exigida por: ${esc(cargoSel.nome)}`, feitoAuto, feitoAuto ? "Revisar" : "Iniciar", "auto") : ""}
    ${quizQuestoes ? passo("bloco", "Teste de conhecimento", `${quizQuestoes.length} questões de múltipla escolha sobre o cargo`, feitoQuiz, feitoQuiz ? "Refazer" : "Iniciar", "quiz") : ""}
    ${passo("anexo", "Currículo (opcional)", me.candidato.curriculo ? "Currículo enviado" : "Envie seu currículo em PDF para enriquecer a análise", me.candidato.curriculo, me.candidato.curriculo ? "Substituir" : "Enviar", "cv")}
    <div class="card texto-centro">
      <h2>Resultados</h2>
      <p class="desc">${tudoPronto ? "Tudo pronto! Veja seu relatório completo." : "Conclua os testes acima para liberar seu relatório completo."}</p>
      <button class="btn block" data-acao="resultados" ${feitoDisc || feitoBase ? "" : "disabled"}>Ver meus resultados</button>
    </div>
    <div class="card" style="padding:18px 24px">
      <p class="desc" style="margin:0">Seu link pessoal de acesso (para continuar de outro aparelho):
        <button class="btn ghost small" id="copiar-link" style="margin-left:6px">Copiar link</button>
        <span id="link-copiado" class="badge ok oculto">Copiado</span>
      </p>
    </div>`;
  document.getElementById("copiar-link").addEventListener("click", () => {
    navigator.clipboard.writeText(
      location.origin + "/candidato.html?token=" + localStorage.getItem("cand_token")
    );
    document.getElementById("link-copiado").classList.remove("oculto");
  });

  app.querySelectorAll("[data-acao]").forEach((b) =>
    b.addEventListener("click", () => {
      const acao = b.dataset.acao;
      if (acao === "disc") telaDisc();
      if (acao === "base") telaBase();
      if (acao === "auto") telaAutoavaliacao();
      if (acao === "quiz") telaQuiz();
      if (acao === "cv") telaCurriculo();
      if (acao === "resultados") telaResultados();
    })
  );
}

async function recarregarMe() {
  me = await api("/api/candidato/me");
}

// ------------------------------------------------ teste DISC
function telaDisc() {
  let indice = 0;
  const respostas = []; // {mais, menos}
  let selMais = null, selMenos = null;

  function desenhar() {
    const bloco = DISC_BLOCOS[indice];
    app.innerHTML = `
      <div class="card">
        <h2 class="icone-titulo">${icone("camadas")}<span>Teste DISC · bloco ${indice + 1} de ${DISC_BLOCOS.length}</span></h2>
        <div class="progress-wrap"><div class="progress-bar" style="width:${(indice / DISC_BLOCOS.length) * 100}%"></div></div>
        <p class="desc">Marque a palavra que <strong style="color:var(--success)">MAIS</strong> se parece com você e a que <strong style="color:var(--danger)">MENOS</strong> se parece.</p>
        <div class="disc-opcoes">
          ${bloco.map((op, i) => `
            <div class="disc-opcao">
              <div class="palavra">${esc(op.t)}</div>
              <button class="disc-pick mais ${selMais === i ? "ativo" : ""}" data-i="${i}" data-tipo="mais">MAIS</button>
              <button class="disc-pick menos ${selMenos === i ? "ativo" : ""}" data-i="${i}" data-tipo="menos">MENOS</button>
            </div>`).join("")}
        </div>
        <div class="linha-acoes">
          <button class="btn ghost" id="disc-voltar" ${indice === 0 ? "disabled" : ""}>← Anterior</button>
          <button class="btn" id="disc-avancar" ${selMais === null || selMenos === null ? "disabled" : ""}>
            ${indice === DISC_BLOCOS.length - 1 ? "Finalizar teste" : "Próximo →"}
          </button>
        </div>
      </div>`;

    app.querySelectorAll(".disc-pick").forEach((b) =>
      b.addEventListener("click", () => {
        const i = Number(b.dataset.i);
        if (b.dataset.tipo === "mais") {
          selMais = i;
          if (selMenos === i) selMenos = null;
        } else {
          selMenos = i;
          if (selMais === i) selMais = null;
        }
        desenhar();
      })
    );
    document.getElementById("disc-voltar").addEventListener("click", () => {
      indice--;
      const ant = respostas[indice];
      const bloco2 = DISC_BLOCOS[indice];
      selMais = bloco2.findIndex((o) => o.d === ant.mais);
      selMenos = bloco2.findIndex((o) => o.d === ant.menos);
      respostas.length = indice;
      desenhar();
    });
    document.getElementById("disc-avancar").addEventListener("click", async () => {
      const bloco2 = DISC_BLOCOS[indice];
      respostas[indice] = { mais: bloco2[selMais].d, menos: bloco2[selMenos].d };
      selMais = null;
      selMenos = null;
      if (indice < DISC_BLOCOS.length - 1) {
        indice++;
        desenhar();
      } else {
        const payload = calcularDisc(respostas);
        await api("/api/candidato/teste", { method: "POST", body: { tipo: "disc", payload } });
        await recarregarMe();
        app.innerHTML = `<div class="card texto-centro">
          <div class="selo-final">${icone("check")}</div>
          <h2>Teste DISC concluído</h2>
          <div class="linha-acoes" style="justify-content:center">
            <button class="btn" id="ir-painel">Continuar</button>
          </div></div>`;
        document.getElementById("ir-painel").addEventListener("click", telaPainel);
      }
    });
  }
  desenhar();
}

// ------------------------------------------------ teste BASE
function telaBase() {
  let rodada = 0;
  const escolhas = []; // por rodada: ['B','A',...]
  let ordemAtual = [];

  function desenhar() {
    const r = BASE_RODADAS[rodada];
    app.innerHTML = `
      <div class="card">
        <h2 class="icone-titulo">${icone("bussola")}<span>Teste B.A.S.E. · rodada ${rodada + 1} de ${BASE_RODADAS.length}</span></h2>
        <div class="progress-wrap"><div class="progress-bar" style="width:${(rodada / BASE_RODADAS.length) * 100}%"></div></div>
        <h3 style="margin-top:0">${esc(r.pergunta)}</h3>
        <p class="desc">Clique nas 4 cartas em ordem: da que <strong>MAIS</strong> combina com você (1º) até a que <strong>MENOS</strong> combina (4º).</p>
        <div class="base-cartas">
          ${r.cartas.map((c) => {
            const pos = ordemAtual.indexOf(c.p);
            return `
              <div class="base-carta ${pos >= 0 ? "escolhida" : ""}" data-p="${c.p}">
                ${pos >= 0 ? `<div class="ordem">${pos + 1}º</div>` : ""}
                <div class="icone-carta">${icone(c.ic)}</div>
                <strong>${esc(c.t)}</strong>
                <div class="sub-carta">${esc(c.sub)}</div>
              </div>`;
          }).join("")}
        </div>
        <div class="linha-acoes">
          <button class="btn ghost" id="base-limpar">Limpar escolhas</button>
          <button class="btn" id="base-avancar" ${ordemAtual.length < 4 ? "disabled" : ""}>
            ${rodada === BASE_RODADAS.length - 1 ? "Finalizar teste" : "Próxima rodada →"}
          </button>
        </div>
      </div>`;

    app.querySelectorAll(".base-carta").forEach((el) =>
      el.addEventListener("click", () => {
        const p = el.dataset.p;
        if (ordemAtual.includes(p)) return;
        ordemAtual.push(p);
        desenhar();
      })
    );
    document.getElementById("base-limpar").addEventListener("click", () => {
      ordemAtual = [];
      desenhar();
    });
    document.getElementById("base-avancar").addEventListener("click", async () => {
      escolhas[rodada] = ordemAtual.slice();
      ordemAtual = [];
      if (rodada < BASE_RODADAS.length - 1) {
        rodada++;
        desenhar();
      } else {
        const payload = calcularBase(escolhas);
        await api("/api/candidato/teste", { method: "POST", body: { tipo: "base", payload } });
        await recarregarMe();
        app.innerHTML = `<div class="card texto-centro">
          <div class="selo-final">${icone("check")}</div>
          <h2>Teste B.A.S.E. concluído</h2>
          <div class="linha-acoes" style="justify-content:center">
            <button class="btn" id="ir-painel">Continuar</button>
          </div></div>`;
        document.getElementById("ir-painel").addEventListener("click", telaPainel);
      }
    });
  }
  desenhar();
}

// ------------------------------------------------ autoavaliação de competências
function telaAutoavaliacao() {
  const cargo = cargos.find((c) => c.id === me.candidato.cargo_desejado_id);
  if (!cargo) return telaPainel();
  const respostas = {};
  if (me.gaps) {
    me.gaps.itens.forEach((i) => {
      if (i.respondida) respostas[i.competencia_id] = i.nivel_atual;
    });
  }

  const grupos = {};
  cargo.competencias.forEach((c) => {
    (grupos[c.tipo] = grupos[c.tipo] || []).push(c);
  });

  app.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("barras")}<span>Autoavaliação de competências</span></h2>
      <p class="desc">Cargo: <strong>${esc(cargo.nome)}</strong>. Para cada competência, indique com sinceridade o seu nível atual.</p>
      ${Object.keys(grupos).map((tipo) => `
        <h3>${esc(TIPOS_COMPETENCIA[tipo] || tipo)}</h3>
        ${grupos[tipo].map((c) => `
          <div class="comp-item">
            <div class="nome">${esc(c.nome)}
              ${c.obrigatoria ? '<span class="badge err">obrigatória</span>' : ""}
              <span class="badge neutral">nível exigido: ${c.nivel_requerido}</span>
            </div>
            <div class="escala" data-comp="${c.id}">
              ${ESCALA_NIVEIS.map((n) => `
                <button data-v="${n.v}" class="${respostas[c.id] === n.v ? "ativo" : ""}">${n.rot}</button>`).join("")}
            </div>
          </div>`).join("")}
      `).join("")}
      <div class="form-erro" id="auto-erro"></div>
      <div class="linha-acoes">
        <button class="btn ghost" id="auto-voltar">← Voltar</button>
        <button class="btn" id="auto-salvar">Salvar autoavaliação</button>
      </div>
    </div>`;

  app.querySelectorAll(".escala").forEach((esc2) =>
    esc2.querySelectorAll("button").forEach((b) =>
      b.addEventListener("click", () => {
        respostas[Number(esc2.dataset.comp)] = Number(b.dataset.v);
        esc2.querySelectorAll("button").forEach((x) => x.classList.remove("ativo"));
        b.classList.add("ativo");
      })
    )
  );
  document.getElementById("auto-voltar").addEventListener("click", telaPainel);
  document.getElementById("auto-salvar").addEventListener("click", async () => {
    const erro = document.getElementById("auto-erro");
    const pendentes = cargo.competencias.filter((c) => respostas[c.id] === undefined);
    if (pendentes.length) {
      erro.textContent = `Responda todas as competências (faltam ${pendentes.length}).`;
      return;
    }
    await api("/api/candidato/autoavaliacao", {
      method: "POST",
      body: {
        respostas: Object.entries(respostas).map(([competencia_id, nivel]) => ({
          competencia_id: Number(competencia_id),
          nivel,
        })),
      },
    });
    await recarregarMe();
    telaPainel();
  });
}

// ------------------------------------------------ teste de conhecimento
function telaQuiz() {
  const respostas = {};
  function desenhar() {
    app.innerHTML = `
      <div class="card">
        <h2 class="icone-titulo">${icone("bloco")}<span>Teste de conhecimento</span></h2>
        <p class="desc">Responda as ${quizQuestoes.length} questões. Cada questão tem apenas uma alternativa correta.</p>
        ${quizQuestoes.map((q, i) => `
          <div class="comp-item">
            <div class="nome">${i + 1}. ${esc(q.pergunta)}</div>
            <div class="escala" style="flex-direction:column;align-items:flex-start" data-q="${q.id}">
              ${q.opcoes.map((op, j) => `
                <button data-v="${j}" class="${respostas[q.id] === j ? "ativo" : ""}"
                  style="text-align:left">${String.fromCharCode(65 + j)}) ${esc(op)}</button>`).join("")}
            </div>
          </div>`).join("")}
        <div class="form-erro" id="quiz-erro"></div>
        <div class="linha-acoes">
          <button class="btn ghost" id="quiz-voltar">← Voltar</button>
          <button class="btn" id="quiz-enviar">Enviar respostas</button>
        </div>
      </div>`;
    app.querySelectorAll(".escala[data-q]").forEach((grupo) =>
      grupo.querySelectorAll("button").forEach((b) =>
        b.addEventListener("click", () => {
          respostas[Number(grupo.dataset.q)] = Number(b.dataset.v);
          grupo.querySelectorAll("button").forEach((x) => x.classList.remove("ativo"));
          b.classList.add("ativo");
        })
      )
    );
    document.getElementById("quiz-voltar").addEventListener("click", telaPainel);
    document.getElementById("quiz-enviar").addEventListener("click", async () => {
      const erro = document.getElementById("quiz-erro");
      const faltam = quizQuestoes.filter((q) => respostas[q.id] === undefined);
      if (faltam.length) {
        erro.textContent = `Responda todas as questões (faltam ${faltam.length}).`;
        return;
      }
      const corpo = {};
      Object.entries(respostas).forEach(([k, v]) => { corpo[k] = v; });
      const r = await api("/api/candidato/quiz", { method: "POST", body: { respostas: corpo } });
      await recarregarMe();
      app.innerHTML = `<div class="card texto-centro">
        <div class="selo-final">${icone("check")}</div>
        <h2>Teste de conhecimento concluído</h2>
        <p class="desc">Você acertou ${r.acertos} de ${r.total} questões.</p>
        <div class="linha-acoes" style="justify-content:center">
          <button class="btn" id="ir-painel">Continuar</button>
        </div></div>`;
      document.getElementById("ir-painel").addEventListener("click", telaPainel);
    });
  }
  desenhar();
}

// ------------------------------------------------ currículo
function telaCurriculo() {
  app.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("anexo")}<span>Enviar currículo</span></h2>
      <p class="desc">Envie seu currículo em PDF (até 8 MB). O gestor poderá cruzar as informações do currículo com as suas respostas.</p>
      <input type="file" id="cv-arquivo" accept=".pdf,.doc,.docx">
      <div class="form-erro" id="cv-erro"></div>
      <div class="linha-acoes">
        <button class="btn ghost" id="cv-voltar">← Voltar</button>
        <button class="btn" id="cv-enviar">Enviar</button>
      </div>
    </div>`;
  document.getElementById("cv-voltar").addEventListener("click", telaPainel);
  document.getElementById("cv-enviar").addEventListener("click", () => {
    const arquivo = document.getElementById("cv-arquivo").files[0];
    const erro = document.getElementById("cv-erro");
    if (!arquivo) { erro.textContent = "Selecione um arquivo."; return; }
    if (arquivo.size > 8 * 1024 * 1024) { erro.textContent = "Arquivo maior que 8 MB."; return; }
    const leitor = new FileReader();
    leitor.onload = async () => {
      try {
        await api("/api/candidato/curriculo", {
          method: "POST",
          body: { filename: arquivo.name, data: leitor.result.split(",")[1] },
        });
        await recarregarMe();
        telaPainel();
      } catch (e) {
        erro.textContent = e.message;
      }
    };
    leitor.readAsDataURL(arquivo);
  });
}

// ------------------------------------------------ resultados (somente os próprios)
function telaResultados() {
  const blocos = [];
  if (me.match) blocos.push(`<div class="card">${htmlMatch(me.match, me.gaps ? me.gaps.cargo.nome : "")}</div>`);
  if (me.testes.disc) blocos.push(`<div class="card">${htmlResultadoDisc(me.testes.disc.payload)}</div>`);
  if (me.testes.base) blocos.push(`<div class="card">${htmlResultadoBase(me.testes.base.payload)}</div>`);
  if (me.quiz) blocos.push(`<div class="card">${tituloIcone("bloco", "Teste de conhecimento")}
    <div class="perfil-destaque"><div class="titulo">${me.quiz.pct}% de acerto</div>
    <div>${me.quiz.acertos} de ${me.quiz.total} questões corretas</div></div></div>`);
  if (me.gaps) blocos.push(`<div class="card">${htmlMatrizGaps(me.gaps)}</div>`);
  app.innerHTML = `
    <div class="card no-print">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2>Seus resultados</h2>
          <p class="desc" style="margin:0">${esc(me.candidato.nome)} · ${esc(me.candidato.email)}</p>
        </div>
        <div class="linha-acoes" style="margin:0">
          <button class="btn ghost" id="res-voltar">← Voltar</button>
          <button class="btn secondary" onclick="window.print()">${icone("impressora")} Imprimir / PDF</button>
        </div>
      </div>
    </div>
    ${blocos.join("") || '<div class="card"><p>Nenhum teste concluído ainda.</p></div>'}`;
  document.getElementById("res-voltar").addEventListener("click", telaPainel);
}

iniciar().catch((e) => {
  app.innerHTML = `<div class="card"><p class="form-erro">Erro ao carregar: ${esc(e.message)}. O servidor está rodando?</p></div>`;
});
