/* =====================================================================
   Área do Candidato: cadastro → testes → autoavaliação → resultados
   O candidato acessa apenas os próprios dados (token individual).
   Textos em pt, en e es: t() e o seletor de idioma vêm de i18n-candidato.js.
   ===================================================================== */

const app = document.getElementById("app");

// códigos de país para o telefone (mesmos países das vagas), ordem alfabética
const CODIGOS_PAIS = [
  { pais: "Angola", ddi: "+244", bandeira: "🇦🇴" },
  { pais: "Brasil", ddi: "+55", bandeira: "🇧🇷" },
  { pais: "Espanha", ddi: "+34", bandeira: "🇪🇸" },
  { pais: "Estados Unidos", ddi: "+1", bandeira: "🇺🇸" },
  { pais: "França", ddi: "+33", bandeira: "🇫🇷" },
  { pais: "Portugal", ddi: "+351", bandeira: "🇵🇹" },
];
// código de telefone sugerido por idioma (o candidato pode trocar)
const DDI_PADRAO = { pt: "+244", en: "+1", es: "+1" };

let cargos = [];
let me = null; // resumo do candidato (dados + testes + gaps)
let quizQuestoes = null; // questões do teste de conhecimento do cargo de interesse
let vagaEscolhida = Number(new URLSearchParams(location.search).get("vaga")) || null;
// empresa do link (?e=empresa) ou da vaga escolhida: define quem recebe o cadastro
let empresaSlug = new URLSearchParams(location.search).get("e") || "";
try {
  if (empresaSlug) localStorage.setItem("cand_empresa", empresaSlug);
  else empresaSlug = localStorage.getItem("cand_empresa") || "";
} catch (e) { /* armazenamento bloqueado */ }
// link de indicação (?ref=codigo): guardado até o cadastro
let indicacaoRef = new URLSearchParams(location.search).get("ref") || "";
try {
  if (indicacaoRef) localStorage.setItem("cand_ref", indicacaoRef);
  else indicacaoRef = localStorage.getItem("cand_ref") || "";
} catch (e) { /* armazenamento bloqueado */ }
let vagaInfo = null;
// função que redesenha a tela atual (usada na troca de idioma)
let redesenhar = null;

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
  if (typeof idiomaCand !== "undefined") headers["X-Idioma"] = idiomaCand;
  const resp = await fetch(caminho, {
    method: opcoes.method || "GET",
    headers,
    body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
  });
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const erro = new Error(dados.erro || t("erro_comunicacao"));
    erro.status = resp.status;
    erro.dados = dados;
    throw erro;
  }
  return dados;
}

// mensagens conhecidas do servidor (em português) no idioma do candidato
const ERROS_SERVIDOR = {
  "Nome e e-mail são obrigatórios": "val_nome_email",
  "Informe onde você está fazendo a avaliação": "val_local",
  "Informe um telefone válido com o código do país": "val_telefone",
  "É necessário autorizar o uso dos seus dados para o processo seletivo": "val_consentimento",
  "Esta vaga não está mais aberta": "erro_vaga_fechada",
  "Use o link de inscrição enviado pela empresa.": "erro_link_empresa",
  "Erro de comunicação com o servidor": "erro_comunicacao",
};

function mensagemErro(e) {
  if (e && e.dados && e.dados.ja_cadastrado) {
    return t(/Enviamos/.test(e.message) ? "erro_email_enviado" : "erro_email_existente");
  }
  const chave = ERROS_SERVIDOR[(e && e.message) || ""];
  return chave ? t(chave) : (e && e.message) || t("erro_comunicacao");
}

// ------------------------------------------------ idioma
function idiomaSalvoNoCadastro() {
  if (!me) return "";
  return normalizarIdioma(me.idioma || (me.candidato && me.candidato.idioma));
}

function salvarIdiomaNoServidor(lang) {
  if (!localStorage.getItem("cand_token")) return;
  api("/api/candidato/idioma", { method: "POST", body: { idioma: lang } }).catch(() => {});
}

// guarda e devolve o que estava digitado, para não perder nada ao redesenhar
function capturarFormulario() {
  const valores = {};
  app.querySelectorAll("input[id], select[id], textarea[id]").forEach((el) => {
    if (el.type === "file") return;
    valores[el.id] = el.type === "checkbox" ? el.checked : el.value;
  });
  return valores;
}

function restaurarFormulario(valores) {
  Object.entries(valores).forEach(([id, v]) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.type === "checkbox") el.checked = v;
    else el.value = v;
    if (el.tagName === "SELECT") el.dispatchEvent(new Event("change"));
  });
}

function atualizarSaudacao() {
  if (me) document.getElementById("topo-sub").textContent = t("ola", { nome: me.candidato.nome });
}

function aoTrocarIdioma(lang) {
  salvarIdiomaNoServidor(lang);
  atualizarSaudacao();
  if (!redesenhar) return;
  const valores = capturarFormulario();
  redesenhar();
  restaurarFormulario(valores);
}

montarSeletorIdioma(aoTrocarIdioma);

// ------------------------------------------------ inicialização
async function iniciar() {
  if (vagaEscolhida) {
    try {
      vagaInfo = await api("/api/vaga/" + vagaEscolhida);
      empresaSlug = vagaInfo.empresa.slug;
    } catch (e) {
      vagaInfo = null;
    }
  }
  cargos = (await api("/api/cargos?e=" + encodeURIComponent(empresaSlug))).cargos;
  const token = localStorage.getItem("cand_token");
  if (!token) return telaCadastro();
  try {
    me = await api("/api/candidato/me");
  } catch (e) {
    localStorage.removeItem("cand_token");
    return telaCadastro();
  }
  // a URL manda; sem ela, vale o idioma salvo no cadastro do candidato
  const salvo = idiomaSalvoNoCadastro();
  if (idiomaDaUrl) {
    if (idiomaDaUrl !== salvo) salvarIdiomaNoServidor(idiomaDaUrl);
  } else if (salvo && salvo !== idiomaCand) {
    definirIdioma(salvo);
  }
  document.getElementById("btn-sair").classList.remove("oculto");
  atualizarSaudacao();
  await carregarQuiz();
  telaPainel();
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
  if (confirm(t("confirmar_sair"))) {
    localStorage.removeItem("cand_token");
    location.reload();
  }
});

// ------------------------------------------------ cadastro
function telaCadastro() {
  redesenhar = telaCadastro;
  const ddiPadrao = DDI_PADRAO[idiomaCand] || CODIGOS_PAIS[0].ddi;
  app.innerHTML = `
    ${vagaEscolhida ? `<div class="card" id="aviso-vaga" style="padding:18px 24px"><p class="desc" style="margin:0">${t("aviso_carregando_vaga")}</p></div>` : ""}
    <div class="card">
      <h2 class="icone-titulo">${icone("usuario")}<span>${t("cad_titulo")}</span></h2>
      <p class="desc">${t("cad_desc")}</p>
      <label class="field" id="campo-tipo" ${vagaEscolhida ? 'style="display:none"' : ""}>${t("cad_tipo_rotulo")}
        <select id="cad-tipo">
          <option value="externo">${t("cad_tipo_externo")}</option>
          <option value="interno">${t("cad_tipo_interno")}</option>
        </select>
      </label>
      <label class="field">${t("cad_nome")}
        <input type="text" id="cad-nome" placeholder="${esc(t("cad_nome_ph"))}">
      </label>
      <label class="field">${t("cad_email")}
        <input type="email" id="cad-email" placeholder="${esc(t("cad_email_ph"))}">
      </label>
      <label class="field">${t("cad_telefone")}
        <div class="linha-acoes" style="margin:0;gap:8px">
          <select id="cad-ddi" style="max-width:130px">
            ${CODIGOS_PAIS.map((p) => `<option value="${p.ddi}" title="${esc(nomePais(p.pais))}" ${p.ddi === ddiPadrao ? "selected" : ""}>${p.bandeira} ${p.ddi}</option>`).join("")}
          </select>
          <input type="tel" id="cad-telefone" placeholder="${esc(t("cad_telefone_ph"))}" style="flex:1;margin:0">
        </div>
      </label>
      <label class="field">${t("cad_local")}
        <input type="text" id="cad-local" list="lista-locais"
          placeholder="${esc(t("cad_local_ph"))}">
        <datalist id="lista-locais"></datalist>
      </label>
      <div class="grid cols-2">
        <label class="field">${t("cad_atual")} <span class="hint">${t("opcional")}</span>
          <input type="text" id="cad-atual" placeholder="${esc(t("cad_atual_ph"))}">
        </label>
        <label class="field">${t("cad_funcao")} <span class="hint">${t("opcional")}</span>
          <input type="text" id="cad-funcao" placeholder="${esc(t("cad_funcao_ph"))}">
        </label>
      </div>
      <div class="grid cols-2">
        <label class="field">LinkedIn <span class="hint">${t("opcional")}</span>
          <input type="text" id="cad-linkedin" placeholder="${esc(t("cad_linkedin_ph"))}">
        </label>
        <label class="field">Instagram <span class="hint">${t("opcional")}</span>
          <input type="text" id="cad-instagram" placeholder="${esc(t("cad_instagram_ph"))}">
        </label>
      </div>
      <label class="field" id="campo-cargo" ${vagaEscolhida ? 'style="display:none"' : ""}><span id="rotulo-cargo">${t("cad_cargo_interesse")}</span>
        <select id="cad-desejado">
          <option value="">${t("cad_selecione_cargo")}</option>
          ${cargos.map((c) => `<option value="${c.id}">${esc(c.nome)}${c.nivel ? " · " + esc(c.nivel) : ""}</option>`).join("")}
          <option value="__novo__">${t("cad_cargo_novo_opcao")}</option>
        </select>
      </label>
      <div id="campo-novo-cargo" style="display:none">
        <div class="grid cols-2">
          <label class="field">${t("cad_novo_cargo")}
            <input type="text" id="cad-novo-cargo" placeholder="${esc(t("cad_novo_cargo_ph"))}">
          </label>
          <label class="field">${t("cad_area")} <span class="hint">${t("opcional")}</span>
            <input type="text" id="cad-novo-cargo-area" placeholder="${esc(t("cad_area_ph"))}">
          </label>
        </div>
        <p class="desc" style="margin:-4px 0 4px">${t("cad_novo_cargo_desc")}</p>
      </div>
      <label class="field" style="display:flex;align-items:flex-start;gap:10px;font-weight:340">
        <input type="checkbox" id="cad-consentimento" style="width:auto;margin-top:4px">
        <span>${t("cad_consentimento")}</span>
      </label>
      <div class="form-erro" id="cad-erro"></div>
      <button class="btn block" id="cad-enviar">${t("cad_enviar")}</button>
    </div>
    <div class="card" style="padding:20px 24px">
      <p class="desc" style="margin:0 0 10px"><strong style="color:var(--text)">${t("rec_titulo")}</strong>
        ${t("rec_desc")}</p>
      <div class="linha-acoes" style="margin:0">
        <input type="email" id="rec-email" placeholder="${esc(t("rec_email_ph"))}" style="flex:1;min-width:200px;margin:0">
        <button class="btn secondary small" id="rec-enviar">${t("rec_enviar")}</button>
      </div>
      <div class="form-erro" id="rec-msg" style="margin-bottom:0"></div>
    </div>`;
  document.getElementById("cad-tipo").addEventListener("change", (ev) => {
    const interno = ev.target.value === "interno";
    document.getElementById("rotulo-cargo").textContent = interno
      ? t("cad_cargo_interno")
      : t("cad_cargo_interesse");
  });
  document.getElementById("cad-desejado").addEventListener("change", (ev) => {
    document.getElementById("campo-novo-cargo").style.display =
      ev.target.value === "__novo__" ? "" : "none";
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
      msg.textContent = t("rec_ok");
    } catch (e) {
      msg.textContent = mensagemErro(e);
    }
  });
  api("/api/locais?e=" + encodeURIComponent(empresaSlug)).then((r) => {
    document.getElementById("lista-locais").innerHTML =
      r.locais.map((l) => `<option value="${esc(l)}"></option>`).join("");
  }).catch(() => {});
  if (vagaEscolhida) {
    Promise.resolve(vagaInfo).then((info) => {
      const v = info ? info.vaga : null;
      const aviso = document.getElementById("aviso-vaga");
      if (!v) {
        vagaEscolhida = null;
        aviso.innerHTML = `<p class="form-erro" style="margin:0">${t("vaga_fechada_cadastro")}</p>`;
        document.getElementById("campo-cargo").style.display = "";
        return;
      }
      aviso.innerHTML = `<p class="desc" style="margin:0">${t("vaga_aviso")}
        <strong style="color:var(--text)">${esc(v.titulo)}</strong> (${esc(v.cargo_nome)}${v.local ? " · " + esc(v.local) : ""})</p>`;
      const campoLocal = document.getElementById("cad-local");
      if (v.local && !campoLocal.value) campoLocal.value = v.local;
    }).catch(() => {});
  }
  document.getElementById("cad-enviar").addEventListener("click", async () => {
    const erro = document.getElementById("cad-erro");
    erro.textContent = "";
    const valor = (id) => document.getElementById(id).value.trim();
    const cargoSel = document.getElementById("cad-desejado").value;
    const telefone = valor("cad-telefone");
    // validação no navegador, com a mesma regra do servidor
    if (!valor("cad-nome") || !valor("cad-email")) { erro.textContent = t("val_nome_email"); return; }
    if (!valor("cad-local")) { erro.textContent = t("val_local"); return; }
    if (telefone.replace(/\D/g, "").length + document.getElementById("cad-ddi").value.replace(/\D/g, "").length < 8) {
      erro.textContent = t("val_telefone");
      return;
    }
    if (!document.getElementById("cad-consentimento").checked) { erro.textContent = t("val_consentimento"); return; }
    try {
      const r = await api("/api/candidato/cadastro", {
        method: "POST",
        body: {
          nome: valor("cad-nome"),
          email: valor("cad-email"),
          telefone: telefone ? document.getElementById("cad-ddi").value + " " + telefone : "",
          local: valor("cad-local"),
          linkedin: valor("cad-linkedin"),
          instagram: valor("cad-instagram"),
          cargo_atual: valor("cad-atual"),
          funcao: valor("cad-funcao"),
          cargo_desejado_id: cargoSel === "__novo__" ? null : (Number(cargoSel) || null),
          novo_cargo: cargoSel === "__novo__" ? valor("cad-novo-cargo") : "",
          novo_cargo_area: cargoSel === "__novo__" ? valor("cad-novo-cargo-area") : "",
          vaga_id: vagaEscolhida,
          empresa: empresaSlug,
          indicacao: indicacaoRef,
          tipo: vagaEscolhida ? "externo" : document.getElementById("cad-tipo").value,
          consentimento: document.getElementById("cad-consentimento").checked,
          idioma: idiomaCand,
        },
      });
      localStorage.setItem("cand_token", r.token);
      location.reload();
    } catch (e) {
      erro.textContent = mensagemErro(e);
    }
  });
}

// ------------------------------------------------ painel de passos
function nomeEtapa(candidatura) {
  const chave = "etapa_" + candidatura.etapa;
  const traduzido = t(chave);
  return traduzido === chave ? candidatura.etapa_nome : traduzido;
}

function telaPainel() {
  redesenhar = telaPainel;
  const feitoDisc = !!me.testes.disc;
  const feitoBase = !!me.testes.base;
  const cargoSel = cargos.find((c) => c.id === me.candidato.cargo_desejado_id);
  const feitoAuto = !!(me.gaps && me.gaps.respondeu_autoavaliacao);
  const feitoQuiz = !!me.quiz;
  const tudoPronto = feitoDisc && feitoBase && (!cargoSel || feitoAuto);
  const candidatura = (me.candidaturas || [])[0];
  const badgeEtapa = candidatura
    ? (candidatura.etapa === "reprovado"
        ? '<span class="badge err">' + esc(nomeEtapa(candidatura)) + "</span>"
        : candidatura.etapa === "contratado"
          ? '<span class="badge ok">' + esc(nomeEtapa(candidatura)) + "</span>"
          : '<span class="badge neutral">' + esc(nomeEtapa(candidatura)) + "</span>")
    : "";

  const passo = (ic, titulo, sub, feito, botao, acao, desabilitado) => `
    <div class="passo">
      <div class="icone">${icone(ic)}</div>
      <div class="info">
        <div class="titulo">${titulo}</div>
        <div class="sub">${sub}</div>
      </div>
      ${feito ? `<span class="badge ok">${t("concluido")}</span>` : ""}
      <button class="btn ${feito ? "secondary" : ""} small" data-acao="${acao}" ${desabilitado ? "disabled" : ""}>${botao}</button>
    </div>`;

  app.innerHTML = `
    <div class="card">
      <h2>${t("painel_titulo")}</h2>
      <p class="desc">${cargoSel
        ? t("painel_cargo", { cargo: esc(cargoSel.nome) })
        : t("painel_sem_cargo")}</p>
      ${candidatura ? `<p class="desc" style="margin-bottom:0">${t("painel_vaga")}: <strong style="color:var(--text)">${esc(candidatura.vaga_titulo)}</strong> · ${t("painel_status")}: ${badgeEtapa}</p>` : ""}
    </div>
    ${passo("camadas", t("passo_disc_t"), t("passo_disc_sub"), feitoDisc, feitoDisc ? t("refazer") : t("iniciar"), "disc")}
    ${passo("bussola", t("passo_base_t"), t("passo_base_sub"), feitoBase, feitoBase ? t("refazer") : t("iniciar"), "base")}
    ${cargoSel ? passo("barras", t("passo_auto_t"), t("passo_auto_sub", { cargo: esc(cargoSel.nome) }), feitoAuto, feitoAuto ? t("revisar") : t("iniciar"), "auto") : ""}
    ${quizQuestoes ? passo("bloco", t("passo_quiz_t"), t("passo_quiz_sub", { n: quizQuestoes.length }), feitoQuiz, feitoQuiz ? t("refazer") : t("iniciar"), "quiz") : ""}
    ${passo("anexo", t("passo_cv_t"), me.candidato.curriculo ? t("passo_cv_enviado") : t("passo_cv_sub"), me.candidato.curriculo, me.candidato.curriculo ? t("substituir") : t("enviar"), "cv")}
    <div class="card texto-centro">
      <h2>${t("res_titulo")}</h2>
      <p class="desc">${tudoPronto ? t("res_pronto") : t("res_pendente")}</p>
      <button class="btn block" data-acao="resultados" ${feitoDisc || feitoBase ? "" : "disabled"}>${t("res_ver")}</button>
    </div>
    <div class="card" style="padding:18px 24px">
      <p class="desc" style="margin:0">${t("link_pessoal")}
        <button class="btn ghost small" id="copiar-link" style="margin-left:6px">${t("copiar_link")}</button>
        <span id="link-copiado" class="badge ok oculto">${t("copiado")}</span>
      </p>
    </div>`;
  document.getElementById("copiar-link").addEventListener("click", () => {
    navigator.clipboard.writeText(
      location.origin + "/candidato?token=" + localStorage.getItem("cand_token")
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

// tela de "teste concluído" com o botão para voltar ao painel
function telaConcluido(chaveTitulo, textoExtra) {
  function desenhar() {
    app.innerHTML = `<div class="card texto-centro">
      <div class="selo-final">${icone("check")}</div>
      <h2>${t(chaveTitulo)}</h2>
      ${textoExtra ? `<p class="desc">${textoExtra()}</p>` : ""}
      <div class="linha-acoes" style="justify-content:center">
        <button class="btn" id="ir-painel">${t("continuar")}</button>
      </div></div>`;
    document.getElementById("ir-painel").addEventListener("click", telaPainel);
  }
  redesenhar = desenhar;
  desenhar();
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
        <h2 class="icone-titulo">${icone("camadas")}<span>${t("disc_titulo", { n: indice + 1, total: DISC_BLOCOS.length })}</span></h2>
        <div class="progress-wrap"><div class="progress-bar" style="width:${(indice / DISC_BLOCOS.length) * 100}%"></div></div>
        <p class="desc">${t("disc_instrucao")}</p>
        <div class="disc-opcoes">
          ${bloco.map((op, i) => `
            <div class="disc-opcao">
              <div class="palavra">${esc(op.t)}</div>
              <button class="disc-pick mais ${selMais === i ? "ativo" : ""}" data-i="${i}" data-tipo="mais">${t("mais")}</button>
              <button class="disc-pick menos ${selMenos === i ? "ativo" : ""}" data-i="${i}" data-tipo="menos">${t("menos")}</button>
            </div>`).join("")}
        </div>
        <div class="linha-acoes">
          <button class="btn ghost" id="disc-voltar" ${indice === 0 ? "disabled" : ""}>${t("anterior")}</button>
          <button class="btn" id="disc-avancar" ${selMais === null || selMenos === null ? "disabled" : ""}>
            ${indice === DISC_BLOCOS.length - 1 ? t("finalizar_teste") : t("proximo")}
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
        await api("/api/candidato/teste", { method: "POST", body: { tipo: "disc", respostas } });
        await recarregarMe();
        telaConcluido("disc_concluido");
      }
    });
  }
  redesenhar = desenhar;
  desenhar();
}

// ------------------------------------------------ teste BASE
function telaBase() {
  let rodada = 0;
  const escolhas = []; // por rodada: ['B','A',...]
  let ordemAtual = [];
  let ordemCartas = null; // letras das cartas da rodada, embaralhadas uma vez

  function embaralhar(lista) {
    // Fisher-Yates, evita viés de posição das cartas
    const a = lista.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function desenhar() {
    const r = BASE_RODADAS[rodada];
    // guarda só a ordem das letras: os textos vêm sempre do idioma atual
    if (!ordemCartas) ordemCartas = embaralhar(r.cartas.map((c) => c.p));
    const cartasRodada = ordemCartas.map((p) => r.cartas.find((c) => c.p === p));
    app.innerHTML = `
      <div class="card">
        <h2 class="icone-titulo">${icone("bussola")}<span>${t("base_titulo", { n: rodada + 1, total: BASE_RODADAS.length })}</span></h2>
        <div class="progress-wrap"><div class="progress-bar" style="width:${(rodada / BASE_RODADAS.length) * 100}%"></div></div>
        <h3 style="margin-top:0">${esc(r.pergunta)}</h3>
        <p class="desc">${t("base_instrucao")}</p>
        <div class="base-cartas">
          ${cartasRodada.map((c) => {
            const pos = ordemAtual.indexOf(c.p);
            return `
              <div class="base-carta ${pos >= 0 ? "escolhida" : ""}" data-p="${c.p}">
                ${pos >= 0 ? `<div class="ordem">${t("ord_" + (pos + 1))}</div>` : ""}
                <div class="icone-carta">${icone(c.ic)}</div>
                <strong>${esc(c.t)}</strong>
                <div class="sub-carta">${esc(c.sub)}</div>
              </div>`;
          }).join("")}
        </div>
        <div class="linha-acoes">
          <button class="btn ghost" id="base-limpar">${t("limpar")}</button>
          <button class="btn" id="base-avancar" ${ordemAtual.length < 4 ? "disabled" : ""}>
            ${rodada === BASE_RODADAS.length - 1 ? t("finalizar_teste") : t("proxima_rodada")}
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
      ordemCartas = null;
      if (rodada < BASE_RODADAS.length - 1) {
        rodada++;
        desenhar();
      } else {
        await api("/api/candidato/teste", { method: "POST", body: { tipo: "base", respostas: escolhas } });
        await recarregarMe();
        telaConcluido("base_concluido");
      }
    });
  }
  redesenhar = desenhar;
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

  function desenhar() {
    app.innerHTML = `
      <div class="card">
        <h2 class="icone-titulo">${icone("barras")}<span>${t("auto_titulo")}</span></h2>
        <p class="desc">${t("auto_desc", { cargo: esc(cargo.nome) })}</p>
        ${Object.keys(grupos).map((tipo) => `
          <h3>${esc(TIPOS_COMPETENCIA[tipo] || tipo)}</h3>
          ${grupos[tipo].map((c) => `
            <div class="comp-item">
              <div class="nome">${esc(c.nome)}
                ${c.obrigatoria ? `<span class="badge err">${t("obrigatoria")}</span>` : ""}
                <span class="badge neutral">${t("nivel_exigido", { n: c.nivel_requerido })}</span>
              </div>
              <div class="escala" data-comp="${c.id}">
                ${ESCALA_NIVEIS.map((n) => `
                  <button data-v="${n.v}" class="${respostas[c.id] === n.v ? "ativo" : ""}">${esc(n.rot)}</button>`).join("")}
              </div>
            </div>`).join("")}
        `).join("")}
        <div class="form-erro" id="auto-erro"></div>
        <div class="linha-acoes">
          <button class="btn ghost" id="auto-voltar">${t("voltar")}</button>
          <button class="btn" id="auto-salvar">${t("auto_salvar")}</button>
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
        erro.textContent = t("auto_faltam", { n: pendentes.length });
        return;
      }
      try {
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
      } catch (e) {
        erro.textContent = mensagemErro(e);
      }
    });
  }
  redesenhar = desenhar;
  desenhar();
}

// ------------------------------------------------ teste de conhecimento
function telaQuiz() {
  const respostas = {};
  function desenhar() {
    app.innerHTML = `
      <div class="card">
        <h2 class="icone-titulo">${icone("bloco")}<span>${t("quiz_titulo")}</span></h2>
        <p class="desc">${t("quiz_desc", { n: quizQuestoes.length })}</p>
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
          <button class="btn ghost" id="quiz-voltar">${t("voltar")}</button>
          <button class="btn" id="quiz-enviar">${t("quiz_enviar")}</button>
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
        erro.textContent = t("quiz_faltam", { n: faltam.length });
        return;
      }
      const corpo = {};
      Object.entries(respostas).forEach(([k, v]) => { corpo[k] = v; });
      try {
        const r = await api("/api/candidato/quiz", { method: "POST", body: { respostas: corpo } });
        await recarregarMe();
        telaConcluido("quiz_concluido", () => t("quiz_acertos", { a: r.acertos, total: r.total }));
      } catch (e) {
        erro.textContent = mensagemErro(e);
      }
    });
  }
  redesenhar = desenhar;
  desenhar();
}

// ------------------------------------------------ currículo
function telaCurriculo() {
  redesenhar = telaCurriculo;
  app.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("anexo")}<span>${t("cv_titulo")}</span></h2>
      <p class="desc">${t("cv_desc")}</p>
      <input type="file" id="cv-arquivo" accept=".pdf,.doc,.docx">
      <div class="form-erro" id="cv-erro"></div>
      <div class="linha-acoes">
        <button class="btn ghost" id="cv-voltar">${t("voltar")}</button>
        <button class="btn" id="cv-enviar">${t("enviar")}</button>
      </div>
    </div>`;
  document.getElementById("cv-voltar").addEventListener("click", telaPainel);
  document.getElementById("cv-enviar").addEventListener("click", () => {
    const arquivo = document.getElementById("cv-arquivo").files[0];
    const erro = document.getElementById("cv-erro");
    if (!arquivo) { erro.textContent = t("cv_selecione"); return; }
    if (arquivo.size > 8 * 1024 * 1024) { erro.textContent = t("cv_grande"); return; }
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
        erro.textContent = mensagemErro(e);
      }
    };
    leitor.readAsDataURL(arquivo);
  });
}

// ------------------------------------------------ resultados (somente os próprios)
function telaResultados() {
  redesenhar = telaResultados;
  const blocos = [];
  if (me.match) blocos.push(`<div class="card">${htmlMatch(me.match, me.gaps ? me.gaps.cargo.nome : "")}</div>`);
  if (me.testes.disc) blocos.push(`<div class="card">${htmlResultadoDisc(me.testes.disc.payload)}</div>`);
  if (me.testes.base) blocos.push(`<div class="card">${htmlResultadoBase(me.testes.base.payload)}</div>`);
  if (me.quiz) blocos.push(`<div class="card">${tituloIcone("bloco", t("quiz_titulo"))}
    <div class="perfil-destaque"><div class="titulo">${t("quiz_pct", { pct: me.quiz.pct })}</div>
    <div>${t("quiz_corretas", { a: me.quiz.acertos, total: me.quiz.total })}</div></div></div>`);
  if (me.gaps) blocos.push(`<div class="card">${htmlMatrizGaps(me.gaps)}</div>`);
  app.innerHTML = `
    <div class="card no-print">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2>${t("res_seus")}</h2>
          <p class="desc" style="margin:0">${esc(me.candidato.nome)} · ${esc(me.candidato.email)}</p>
        </div>
        <div class="linha-acoes" style="margin:0">
          <button class="btn ghost" id="res-voltar">${t("voltar")}</button>
          <button class="btn" id="res-pdf">${icone("documento")} ${t("res_pdf")}</button>
        </div>
      </div>
    </div>
    ${blocos.join("") || `<div class="card"><p>${t("res_nenhum")}</p></div>`}`;
  document.getElementById("res-voltar").addEventListener("click", telaPainel);
  document.getElementById("res-pdf").addEventListener("click", baixarRelatorioPdf);
}

async function baixarRelatorioPdf() {
  const btn = document.getElementById("res-pdf");
  const original = btn.innerHTML;
  btn.disabled = true;
  btn.textContent = t("gerando");
  try {
    const resp = await fetch("/api/candidato/relatorio.pdf?lang=" + idiomaCand, {
      headers: { "X-Token": localStorage.getItem("cand_token") },
    });
    if (!resp.ok) {
      const d = await resp.json().catch(() => ({}));
      throw new Error(d.erro || t("erro_pdf"));
    }
    const blob = await resp.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "relatorio-bussola.pdf";
    a.click();
    URL.revokeObjectURL(a.href);
  } catch (e) {
    alert(e.message);
  }
  btn.disabled = false;
  btn.innerHTML = original;
}

iniciar().catch((e) => {
  redesenhar = null;
  app.innerHTML = `<div class="card"><p class="form-erro">${t("erro_carregar", { msg: esc(mensagemErro(e)) })}</p></div>`;
});
