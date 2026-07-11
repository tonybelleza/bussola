/* =====================================================================
   Módulo Diagnóstico de Competências (aba do painel do gestor)
   Liberado pelo dono do sistema conta a conta. Contém o perfil do
   projeto (cronograma, entregáveis, governança e documentos) e as
   sessões de levantamento funcional (instrumentos A, B e C).
   ===================================================================== */

let diagVisao = "projeto"; // projeto | sessoes
let DIAG = null; // conteúdo do projeto, entregue pela API só a contas com o módulo

async function abaDiagnostico(el) {
  let r;
  try {
    r = await api("/api/gestor/diagnostico");
  } catch (e) {
    el.innerHTML = `<div class="card"><p class="form-erro">${esc(e.message)}</p></div>`;
    return;
  }
  DIAG = r.conteudo;
  if (!DIAG) {
    el.innerHTML = '<div class="card"><p class="form-erro">O conteúdo do projeto não está instalado neste servidor (docs/diagnostico-conteudo.json). Fale com o administrador.</p></div>';
    return;
  }
  el.innerHTML = `
    <div class="card" style="padding:22px 28px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
        <div>
          <h2 class="icone-titulo" style="margin-bottom:2px">${icone("bussola")}<span>${esc(DIAG.projeto.codigo)} · ${esc(DIAG.projeto.nome)}</span></h2>
          <p class="desc" style="margin:0">${esc(DIAG.projeto.cliente)} · ${esc(DIAG.projeto.area)} · ${esc(DIAG.projeto.periodo)}</p>
        </div>
        <div class="tabs" style="margin:0">
          <button class="tab ${diagVisao === "projeto" ? "ativa" : ""}" data-dv="projeto">Projeto</button>
          <button class="tab ${diagVisao === "sessoes" ? "ativa" : ""}" data-dv="sessoes">Sessões (${r.stats.total})</button>
        </div>
      </div>
    </div>
    <div id="diag-conteudo"></div>`;
  el.querySelectorAll("[data-dv]").forEach((b) =>
    b.addEventListener("click", () => {
      diagVisao = b.dataset.dv;
      abaDiagnostico(el);
    })
  );
  const alvo = document.getElementById("diag-conteudo");
  if (diagVisao === "projeto") diagTelaProjeto(alvo, r);
  else diagTelaSessoes(alvo, r);
}

// ------------------------------------------------ perfil do projeto
function diagTelaProjeto(el, r) {
  el.innerHTML = `
    <div class="grid cols-2">
      <div class="card">
        <h2 class="icone-titulo">${icone("alvo")}<span>O projecto</span></h2>
        <p>${esc(DIAG.projeto.objetivo)}</p>
        <div class="tabela-wrap"><table class="tabela"><tbody>
          <tr><td>Consultora técnica</td><td class="num"><strong>${esc(DIAG.projeto.consultora)}</strong></td></tr>
          <tr><td>Contratação</td><td class="num">${esc(DIAG.projeto.contratante)}</td></tr>
          <tr><td>Público-alvo</td><td class="num">${DIAG.projeto.meta_colaboradores} colaboradores do GTI</td></tr>
          <tr><td>Recolha de dados</td><td class="num">${esc(DIAG.projeto.instrumentos_recolha)}</td></tr>
        </tbody></table></div>
        <div class="aviso" style="margin-top:14px">Fora do escopo desta etapa: ${esc(DIAG.projeto.fora_escopo)}</div>
        <div class="linha-acoes">
          <a class="btn" href="${DIAG.projeto.link_questionario}" target="_blank" rel="noopener">Abrir questionário online</a>
        </div>
      </div>
      <div class="card">
        <h2 class="icone-titulo">${icone("camadas")}<span>Abordagem metodológica</span></h2>
        <p class="desc">Tríade multimétodo com triangulação de dados.</p>
        ${DIAG.projeto.metodologia.map(([t, d], i) => `
          <div class="passo" style="margin-bottom:10px">
            <div class="icone" style="font-family:var(--font-display);font-weight:650">${i + 1}</div>
            <div class="info"><div class="titulo">${esc(t)}</div>
              <p class="desc" style="margin:2px 0 0">${esc(d)}</p></div>
          </div>`).join("")}
      </div>
    </div>

    <div class="card">
      <h2 class="icone-titulo">${icone("relatorio")}<span>Cronograma</span></h2>
      <p class="desc">${esc(DIAG.validacoes)}</p>
      <div class="grid cols-3">
        ${DIAG.cronograma.map((s) => `
          <div class="card" style="margin:0;padding:20px 22px">
            <div style="display:flex;justify-content:space-between;align-items:baseline">
              <strong style="font-family:var(--font-display);font-size:1.15rem">${s.sem}</strong>
              <span class="badge tipo">${esc(s.datas)}</span>
            </div>
            <div style="font-weight:480;margin:6px 0 2px">${esc(s.titulo)}</div>
            <div class="desc" style="font-size:.78rem;margin-bottom:8px">${esc(s.modo)}</div>
            <ul class="lista-simples" style="font-size:.84rem">${s.itens.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>
          </div>`).join("")}
      </div>
      <h3 style="margin-top:22px">Marcos de aprovação</h3>
      <div class="linha-acoes" style="margin-top:8px">
        ${DIAG.marcos.map(([g, t, d]) => `
          <span class="badge neutral" title="${esc(t)}" style="padding:9px 16px">
            <strong>${g}</strong> · ${esc(t)} · ${esc(d)}</span>`).join("")}
      </div>
    </div>

    <div class="grid cols-2">
      <div class="card">
        <h2 class="icone-titulo">${icone("documento")}<span>Entregáveis da fase</span></h2>
        ${DIAG.entregaveis.map(([n, t, d]) => `
          <div class="passo" style="margin-bottom:10px">
            <div class="icone" style="font-family:var(--font-display);font-weight:650;font-size:.85rem">${n}</div>
            <div class="info"><div class="titulo">${esc(t)}</div>
              <p class="desc" style="margin:2px 0 0">${esc(d)}</p></div>
          </div>`).join("")}
      </div>
      <div>
        <div class="card">
          <h2 class="icone-titulo">${icone("anexo")}<span>Documentos do projecto</span></h2>
          <p class="desc">Disponíveis apenas para contas com o módulo liberado.</p>
          ${r.arquivos.map((a) => `
            <div class="comp-item" style="display:flex;justify-content:space-between;align-items:center;gap:12px">
              <div class="nome" style="font-size:.9rem">${esc(a.titulo)}</div>
              <button class="btn secondary small" data-arquivo="${esc(a.nome)}">Baixar</button>
            </div>`).join("") || '<p class="desc">Nenhum documento no servidor.</p>'}
        </div>
        <div class="card">
          <h2 class="icone-titulo">${icone("cadeado")}<span>Riscos e medidas</span></h2>
          ${DIAG.riscos.map(([risco, medida]) => `
            <p style="font-size:.9rem;margin-bottom:10px"><strong>${esc(risco)}.</strong>
              <span style="color:var(--text-2)">${esc(medida)}</span></p>`).join("")}
        </div>
      </div>
    </div>`;

  el.querySelectorAll("[data-arquivo]").forEach((b) =>
    b.addEventListener("click", async () => {
      b.disabled = true;
      try {
        const resp = await fetch("/api/gestor/diagnostico/arquivo/" + b.dataset.arquivo, {
          headers: { "X-Gestor-Token": localStorage.getItem("gestor_token") },
        });
        if (!resp.ok) throw new Error("Falha ao baixar o arquivo");
        const blob = await resp.blob();
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = b.dataset.arquivo;
        a.click();
        URL.revokeObjectURL(a.href);
      } catch (e) {
        alert(e.message);
      }
      b.disabled = false;
    })
  );
}

// ------------------------------------------------ sessões
function diagTelaSessoes(el, r) {
  const meta = DIAG.projeto.meta_colaboradores;
  el.innerHTML = `
    <div class="metricas">
      <div class="metrica"><div class="num">${r.stats.total}</div><div class="rot">Sessões registradas</div></div>
      <div class="metrica"><div class="num">${r.stats.concluidas}</div><div class="rot">Concluídas</div></div>
      <div class="metrica"><div class="num">${Math.round((r.stats.total / meta) * 100)}%</div><div class="rot">Cobertura da meta (${meta})</div></div>
    </div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2 class="icone-titulo">${icone("usuarios")}<span>Sessões de levantamento funcional</span></h2>
          <p class="desc" style="margin:0">Uma sessão por colaborador, com os instrumentos A (identificação), B (levantamento funcional) e C (competências autopercebidas). Salve como rascunho e continue depois.</p>
        </div>
        <button class="btn" id="diag-nova">+ Nova sessão</button>
      </div>
      <div class="tabela-wrap" style="margin-top:16px"><table class="tabela">
        <thead><tr><th>Colaborador</th><th>Cargo</th><th>Unidade</th>
          <th class="num">Status</th><th class="num">Atualizada</th><th></th></tr></thead>
        <tbody>
          ${r.sessoes.map((s) => `
            <tr>
              <td><strong>${esc(s.colaborador)}</strong></td>
              <td>${esc(s.cargo || "")}</td>
              <td>${esc(s.unidade || "")}</td>
              <td class="num">${s.status === "concluida"
                ? '<span class="badge ok">Concluída</span>'
                : '<span class="badge warn">Rascunho</span>'}</td>
              <td class="num" style="font-size:.8rem;color:var(--muted)">${esc((s.atualizado_em || "").slice(0, 16))}</td>
              <td class="num">
                <button class="btn secondary small" data-abrir="${s.id}">Abrir</button>
                <button class="btn danger small" data-excluir="${s.id}">Excluir</button>
              </td>
            </tr>`).join("") || '<tr><td colspan="6" style="color:var(--muted)">Nenhuma sessão ainda. Clique em "+ Nova sessão" para aplicar o instrumento.</td></tr>'}
        </tbody>
      </table></div>
      ${Object.keys(r.stats.por_unidade).length ? `
        <h3 style="margin-top:18px">Cobertura por unidade</h3>
        <div class="linha-acoes" style="margin-top:6px">
          ${Object.entries(r.stats.por_unidade).map(([u, n]) =>
            `<span class="badge tipo">${esc(u)}: ${n}</span>`).join("")}
        </div>` : ""}
    </div>`;
  document.getElementById("diag-nova").addEventListener("click", () => diagFormSessao(null));
  el.querySelectorAll("[data-abrir]").forEach((b) =>
    b.addEventListener("click", async () => {
      const resp = await api("/api/gestor/diagnostico/sessao/" + b.dataset.abrir);
      diagFormSessao(resp.sessao);
    })
  );
  el.querySelectorAll("[data-excluir]").forEach((b) =>
    b.addEventListener("click", async () => {
      if (!confirm("Excluir esta sessão? Os dados registrados serão perdidos.")) return;
      await api("/api/gestor/diagnostico/sessao/" + b.dataset.excluir, { method: "DELETE" });
      abaDiagnostico(document.getElementById("conteudo"));
    })
  );
}

// ------------------------------------------------ formulário da sessão
function diagCampo(caminho, dados) {
  return caminho.split(".").reduce((o, k) => (o && o[k] !== undefined ? o[k] : ""), dados);
}

function diagInput(caminho, dados, ph) {
  return `<input type="text" data-campo="${caminho}" value="${esc(diagCampo(caminho, dados))}" placeholder="${esc(ph || "")}">`;
}

function diagArea(caminho, dados, linhas) {
  return `<textarea data-campo="${caminho}" rows="${linhas || 2}">${esc(diagCampo(caminho, dados))}</textarea>`;
}

function diagSelect(caminho, dados, opcoes, vazio) {
  const atual = diagCampo(caminho, dados);
  return `<select data-campo="${caminho}">
    <option value="">${esc(vazio || "Selecione")}</option>
    ${opcoes.map((o) => `<option value="${esc(o)}" ${atual === o ? "selected" : ""}>${esc(o)}</option>`).join("")}
  </select>`;
}

function diagFormSessao(sessao) {
  const d = (sessao && sessao.dados) || {};
  const el = document.getElementById("conteudo");
  el.innerHTML = `
    <div class="card" style="padding:22px 28px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2 class="icone-titulo" style="margin-bottom:2px">${icone("lapis")}<span>${sessao ? "Sessão: " + esc(sessao.colaborador) : "Nova sessão de levantamento"}</span></h2>
          <p class="desc" style="margin:0">Instrumento de Levantamento Funcional · ${esc(DIAG.projeto.codigo)} · v1.0</p>
        </div>
        <button class="btn ghost small" id="diag-voltar">← Voltar às sessões</button>
      </div>
    </div>
    <div id="diag-form">

    <div class="card">
      <h2>Instrumento A · Identificação e posicionamento hierárquico</h2>
      <h3>A.1 · Dados de identificação</h3>
      <div class="grid cols-2">
        <label class="field">Nome completo ${diagInput("a1.nome", d)}</label>
        <label class="field">Designação do cargo actual ${diagInput("a1.cargo", d)}</label>
        <label class="field">Área / Departamento / Equipa ${diagInput("a1.area", d)}</label>
        <label class="field">Nível hierárquico percebido ${diagSelect("a1.nivel", d, DIAG.opcoes.nivel_hierarquico)}</label>
        <label class="field">Tempo no cargo actual ${diagInput("a1.tempo", d, "ex.: 3 anos")}</label>
        <label class="field">Cargo anterior (se aplicável) ${diagInput("a1.cargo_anterior", d)}</label>
        <label class="field">Data da sessão ${diagInput("a1.data", d, "aaaa-mm-dd")}</label>
        <label class="field">Observador / Aplicador ${diagInput("a1.observador", d)}</label>
      </div>
      <h3>A.2 · Posicionamento na estrutura do GTI</h3>
      <div class="grid cols-2">
        <label class="field">Unidade orgânica formal ${diagSelect("a2.unidade", d, DIAG.unidades)}</label>
        <label class="field">Unidade orgânica real (se diferente) ${diagInput("a2.unidade_real", d)}</label>
      </div>
      <h3>A.3 · Relacionamentos funcionais</h3>
      <div class="grid cols-2">
        <label class="field">Superior hierárquico directo ${diagInput("a3.superior", d, "nome / cargo / área")}</label>
        <label class="field">Pares (mesmo nível) ${diagInput("a3.pares", d)}</label>
        <label class="field">Subordinados directos ${diagInput("a3.subordinados", d)}</label>
        <label class="field">Interlocutores externos ao GTI ${diagInput("a3.interlocutores", d)}</label>
        <label class="field">Entidades externas ao INSS ${diagInput("a3.externas", d)}</label>
      </div>
      <label class="field">Funções que exerce mas que não estão no cargo formal ${diagArea("a3.funcoes_fora", d)}</label>
    </div>

    <div class="card">
      <h2>Instrumento B · Levantamento funcional</h2>
      <h3>B.1 · Rotina e ciclo de trabalho</h3>
      <p class="desc">Liste as 5 a 8 actividades mais frequentes num dia típico.</p>
      ${[0, 1, 2, 3, 4, 5, 6, 7].map((i) => `
        <div class="grid" style="grid-template-columns:2fr 1fr 1fr;gap:10px;margin-bottom:8px">
          <label class="field" style="margin:0">${i === 0 ? "Actividade" : ""} ${diagInput("b1.atividades.a" + i + ".texto", d, (i + 1) + "ª actividade")}</label>
          <label class="field" style="margin:0">${i === 0 ? "Frequência" : ""} ${diagSelect("b1.atividades.a" + i + ".freq", d, DIAG.opcoes.frequencia)}</label>
          <label class="field" style="margin:0">${i === 0 ? "Autonomia" : ""} ${diagSelect("b1.atividades.a" + i + ".aut", d, DIAG.opcoes.autonomia)}</label>
        </div>`).join("")}
      <div class="grid cols-2">
        <label class="field">Actividades não rotineiras mas relevantes ${diagArea("b1.nao_rotineiras", d)}</label>
        <label class="field">O que acontece num incidente ou problema urgente? ${diagArea("b1.incidentes", d)}</label>
      </div>
      <h3>B.2 · Missão e propósito da função</h3>
      <div class="grid cols-2">
        <label class="field">Resposta do colaborador (na íntegra) ${diagArea("b2.missao", d, 3)}</label>
        <label class="field">Reformulação analítica (observador) ${diagArea("b2.reformulacao", d, 3)}</label>
      </div>
      <h3>B.3 · Família funcional TIC e domínio técnico</h3>
      ${DIAG.familias_tic.map((f, i) => `
        <div class="grid" style="grid-template-columns:auto 2fr 1fr;gap:12px;align-items:center;margin-bottom:6px">
          <input type="checkbox" data-campo="b3.familias.f${i}.aplica" ${diagCampo("b3.familias.f" + i + ".aplica", d) ? "checked" : ""} style="width:auto">
          <span style="font-size:.9rem">${esc(f)}</span>
          ${diagSelect("b3.familias.f" + i + ".envolv", d, DIAG.opcoes.envolvimento, "Grau")}
        </div>`).join("")}
      <label class="field" style="margin-top:10px">Domínios técnicos específicos (ferramentas, tecnologias, sistemas) ${diagArea("b3.dominios", d)}</label>
      <h3>B.4 · Funções, subfunções e critérios de desempenho</h3>
      ${[0, 1, 2].map((i) => `
        <div class="comp-item" style="display:block">
          <div class="nome" style="margin-bottom:8px">Função principal ${i + 1}</div>
          <div class="grid cols-2">
            <label class="field">Designação da função ${diagInput("b4.funcoes.f" + i + ".designacao", d)}</label>
            <label class="field">Critério de desempenho observável ${diagInput("b4.funcoes.f" + i + ".criterio", d)}</label>
            <label class="field">Subfunção 1 ${diagInput("b4.funcoes.f" + i + ".sub1", d)}</label>
            <label class="field">Subfunção 2 ${diagInput("b4.funcoes.f" + i + ".sub2", d)}</label>
            <label class="field">Subfunção 3 ${diagInput("b4.funcoes.f" + i + ".sub3", d)}</label>
            <label class="field">Condições de exercício ${diagInput("b4.funcoes.f" + i + ".condicoes", d)}</label>
          </div>
        </div>`).join("")}
      <h3>B.5 · Trabalho prescrito vs. trabalho real</h3>
      ${DIAG.b5_dimensoes.map((dim, i) => `
        <div class="grid" style="grid-template-columns:1fr 1fr 1fr auto;gap:10px;align-items:end;margin-bottom:8px">
          <label class="field" style="margin:0">${i === 0 ? "Dimensão" : ""}<input type="text" value="${esc(dim)}" disabled></label>
          <label class="field" style="margin:0">${i === 0 ? "Trabalho prescrito" : ""} ${diagInput("b5.dim.d" + i + ".prescrito", d)}</label>
          <label class="field" style="margin:0">${i === 0 ? "Trabalho real" : ""} ${diagInput("b5.dim.d" + i + ".real", d)}</label>
          <label class="field" style="margin:0">${i === 0 ? "Discrepância" : ""} ${diagSelect("b5.dim.d" + i + ".disc", d, ["Sim", "Não"], "?")}</label>
        </div>`).join("")}
      <label class="field" style="margin-top:8px">Notas sobre discrepâncias (exemplos concretos) ${diagArea("b5.notas", d)}</label>
      <h3>B.6 · Nível de complexidade e autonomia (Dutra, Hipólito & Silva, 2004)</h3>
      <div class="grid cols-2">
        ${DIAG.b6_indicadores.map(([chave, rotulo, op]) => `
          <label class="field">${esc(rotulo)} ${diagSelect("b6." + chave, d, DIAG.opcoes[op])}</label>`).join("")}
        <label class="field">Nível de complexidade global (síntese) ${diagSelect("b6.nivel_global", d, DIAG.opcoes.nivel_global)}</label>
      </div>
      <label class="field">Justificação da classificação (exemplos que sustentam a escolha) ${diagArea("b6.justificacao", d)}</label>
    </div>

    <div class="card">
      <h2>Instrumento C · Mapa de competências autopercebidas</h2>
      <h3>C.1 · Competências técnicas TIC</h3>
      <p class="desc">Escala: ${DIAG.niveis.join(" · ")}. Marque as que aplica na função, com nível autopercebido e nível desejado para o cargo.</p>
      ${Object.entries(DIAG.competencias_tecnicas).map(([grupo, lista]) => `
        <h3 style="font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;color:var(--blue-200)">${esc(grupo)}</h3>
        ${lista.map((c, i) => {
          const base = "c1." + grupo.replace(/[^A-Za-z]/g, "").toLowerCase() + ".c" + i;
          return `
          <div class="grid" style="grid-template-columns:auto 2fr 1fr 1fr;gap:10px;align-items:center;margin-bottom:6px">
            <input type="checkbox" data-campo="${base}.aplica" ${diagCampo(base + ".aplica", d) ? "checked" : ""} style="width:auto">
            <span style="font-size:.88rem">${esc(c)}</span>
            ${diagSelect(base + ".auto", d, DIAG.niveis, "Autopercebido")}
            ${diagSelect(base + ".desejado", d, DIAG.niveis, "Desejado")}
          </div>`;
        }).join("")}`).join("")}
      <h3>C.2 · Competências comportamentais e transversais</h3>
      ${DIAG.competencias_comportamentais.map((c, i) => `
        <div class="grid" style="grid-template-columns:2fr 1fr 1fr;gap:10px;align-items:center;margin-bottom:6px">
          <span style="font-size:.88rem">${esc(c)}</span>
          ${diagSelect("c2.c" + i + ".auto", d, DIAG.niveis, "Autopercebido")}
          ${diagSelect("c2.c" + i + ".desejado", d, DIAG.niveis, "Desejado")}
        </div>`).join("")}
      <h3>C.3 · Formação e certificações</h3>
      <div class="grid cols-2">
        <label class="field">Habilitações académicas ${diagInput("c3.habilitacoes", d)}</label>
        <label class="field">Área de formação base ${diagInput("c3.area_formacao", d)}</label>
        <label class="field">Certificações TIC activas ${diagInput("c3.certificacoes", d)}</label>
        <label class="field">Formações relevantes (últimos 3 anos) ${diagInput("c3.formacoes_recentes", d)}</label>
      </div>
      <label class="field">Formações desejadas / identificadas pelo colaborador ${diagArea("c3.formacoes_desejadas", d)}</label>
      <h3>C.4 · Percepção de lacunas e necessidades de desenvolvimento</h3>
      <label class="field">O que lhe falta para desempenhar o cargo com maior eficácia? ${diagArea("c4.falta", d)}</label>
      <label class="field">Competência usada todos os dias mas dominada de forma insuficiente ${diagArea("c4.insuficiente", d)}</label>
      <label class="field">Se pudesse fazer uma formação agora, qual escolheria? Porquê? ${diagArea("c4.formacao_escolhida", d)}</label>
    </div>

    <div class="card">
      <div class="form-erro" id="diag-erro"></div>
      <div class="linha-acoes">
        <button class="btn secondary" id="diag-salvar">Salvar rascunho</button>
        <button class="btn" id="diag-concluir">Salvar e marcar como concluída</button>
      </div>
    </div>
    </div>`;

  document.getElementById("diag-voltar").addEventListener("click", () => {
    diagVisao = "sessoes";
    abaDiagnostico(el);
  });

  async function salvar(status) {
    const erro = document.getElementById("diag-erro");
    erro.textContent = "";
    const dados = {};
    document.querySelectorAll("#diag-form [data-campo]").forEach((campo) => {
      const valor = campo.type === "checkbox" ? campo.checked : campo.value.trim();
      if (valor === "" || valor === false) return;
      const partes = campo.dataset.campo.split(".");
      let alvo = dados;
      partes.slice(0, -1).forEach((p) => { alvo = alvo[p] = alvo[p] || {}; });
      alvo[partes[partes.length - 1]] = valor;
    });
    const colaborador = (dados.a1 && dados.a1.nome) || "";
    if (!colaborador) {
      erro.textContent = "Informe ao menos o nome completo do colaborador (A.1).";
      window.scrollTo(0, 0);
      return;
    }
    const unidade = ((dados.a2 && dados.a2.unidade) || "").split("·")[0].trim();
    try {
      await api("/api/gestor/diagnostico/sessao", {
        method: "POST",
        body: {
          id: sessao ? sessao.id : undefined,
          colaborador,
          cargo: (dados.a1 && dados.a1.cargo) || "",
          unidade,
          status,
          dados,
        },
      });
      diagVisao = "sessoes";
      abaDiagnostico(el);
    } catch (e) {
      erro.textContent = e.message;
    }
  }
  document.getElementById("diag-salvar").addEventListener("click", () => salvar("rascunho"));
  document.getElementById("diag-concluir").addEventListener("click", () => salvar("concluida"));
}
