/* =====================================================================
   Módulo Diagnóstico de Competências (aba do painel do gestor)
   Liberado pelo dono do sistema conta a conta. Contém o perfil do
   projeto (cronograma, entregáveis, governança e documentos) e as
   sessões de levantamento funcional (instrumentos A, B e C).
   O conteúdo do projeto (JSON do servidor) não é traduzido; os
   textos da interface vêm de tg() (i18n-gestor.js).
   ===================================================================== */

let diagVisao = "projeto"; // projeto | sessoes
let DIAG = null; // conteúdo do projeto, entregue pela API só a contas com o módulo
let diagSessaoAberta = null; // sessão em edição (para redesenhar ao trocar o idioma)

async function abaDiagnostico(el) {
  diagSessaoAberta = null;
  let r;
  try {
    r = await api("/api/gestor/diagnostico");
  } catch (e) {
    el.innerHTML = `<div class="card"><p class="form-erro">${esc(e.message)}</p></div>`;
    return;
  }
  DIAG = r.conteudo;
  if (!DIAG) {
    el.innerHTML = '<div class="card"><p class="form-erro">' + tg("dg_sem_conteudo") + "</p></div>";
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
          <button class="tab ${diagVisao === "projeto" ? "ativa" : ""}" data-dv="projeto">${tg("dg_projeto")}</button>
          <button class="tab ${diagVisao === "sessoes" ? "ativa" : ""}" data-dv="sessoes">${tg("dg_sessoes_n", { n: fmtNum(r.stats.total) })}</button>
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
        <h2 class="icone-titulo">${icone("alvo")}<span>${tg("dg_o_projeto")}</span></h2>
        <p>${esc(DIAG.projeto.objetivo)}</p>
        <div class="tabela-wrap"><table class="tabela"><tbody>
          <tr><td>${tg("dg_consultora")}</td><td class="num"><strong>${esc(DIAG.projeto.consultora)}</strong></td></tr>
          <tr><td>${tg("dg_contratacao")}</td><td class="num">${esc(DIAG.projeto.contratante)}</td></tr>
          <tr><td>${tg("dg_publico")}</td><td class="num">${tg("dg_publico_valor", { n: fmtNum(DIAG.projeto.meta_colaboradores) })}</td></tr>
          <tr><td>${tg("dg_recolha")}</td><td class="num">${esc(DIAG.projeto.instrumentos_recolha)}</td></tr>
        </tbody></table></div>
        <div class="aviso" style="margin-top:14px">${tg("dg_fora_escopo")} ${esc(DIAG.projeto.fora_escopo)}</div>
        <div class="linha-acoes">
          <a class="btn" href="${DIAG.projeto.link_questionario}" target="_blank" rel="noopener">${tg("dg_abrir_questionario")}</a>
        </div>
      </div>
      <div class="card">
        <h2 class="icone-titulo">${icone("camadas")}<span>${tg("dg_abordagem")}</span></h2>
        <p class="desc">${tg("dg_triade")}</p>
        ${DIAG.projeto.metodologia.map(([t, d], i) => `
          <div class="passo" style="margin-bottom:10px">
            <div class="icone" style="font-family:var(--font-display);font-weight:650">${i + 1}</div>
            <div class="info"><div class="titulo">${esc(t)}</div>
              <p class="desc" style="margin:2px 0 0">${esc(d)}</p></div>
          </div>`).join("")}
      </div>
    </div>

    <div class="card">
      <h2 class="icone-titulo">${icone("relatorio")}<span>${tg("dg_cronograma")}</span></h2>
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
      <h3 style="margin-top:22px">${tg("dg_marcos")}</h3>
      <div class="linha-acoes" style="margin-top:8px">
        ${DIAG.marcos.map(([g, t, d]) => `
          <span class="badge neutral" title="${esc(t)}" style="padding:9px 16px">
            <strong>${g}</strong> · ${esc(t)} · ${esc(d)}</span>`).join("")}
      </div>
    </div>

    <div class="grid cols-2">
      <div class="card">
        <h2 class="icone-titulo">${icone("documento")}<span>${tg("dg_entregaveis")}</span></h2>
        ${DIAG.entregaveis.map(([n, t, d]) => `
          <div class="passo" style="margin-bottom:10px">
            <div class="icone" style="font-family:var(--font-display);font-weight:650;font-size:.85rem">${n}</div>
            <div class="info"><div class="titulo">${esc(t)}</div>
              <p class="desc" style="margin:2px 0 0">${esc(d)}</p></div>
          </div>`).join("")}
      </div>
      <div>
        <div class="card">
          <h2 class="icone-titulo">${icone("anexo")}<span>${tg("dg_documentos")}</span></h2>
          <p class="desc">${tg("dg_documentos_desc")}</p>
          ${r.arquivos.map((a) => `
            <div class="comp-item" style="display:flex;justify-content:space-between;align-items:center;gap:12px">
              <div class="nome" style="font-size:.9rem">${esc(a.titulo)}</div>
              <button class="btn secondary small" data-arquivo="${esc(a.nome)}">${tg("dg_baixar")}</button>
            </div>`).join("") || '<p class="desc">' + tg("dg_sem_documentos") + "</p>"}
        </div>
        <div class="card">
          <h2 class="icone-titulo">${icone("cadeado")}<span>${tg("dg_riscos")}</span></h2>
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
          headers: { "X-Gestor-Token": localStorage.getItem("gestor_token"), "X-Idioma": idiomaGestor },
        });
        if (!resp.ok) throw new Error(tg("dg_erro_baixar"));
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
      <div class="metrica"><div class="num">${fmtNum(r.stats.total)}</div><div class="rot">${tg("dg_m_registradas")}</div></div>
      <div class="metrica"><div class="num">${fmtNum(r.stats.concluidas)}</div><div class="rot">${tg("dg_m_concluidas")}</div></div>
      <div class="metrica"><div class="num">${Math.round((r.stats.total / meta) * 100)}%</div><div class="rot">${tg("dg_m_cobertura", { n: fmtNum(meta) })}</div></div>
    </div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2 class="icone-titulo">${icone("usuarios")}<span>${tg("dg_sessoes_titulo")}</span></h2>
          <p class="desc" style="margin:0">${tg("dg_sessoes_desc")}</p>
        </div>
        <button class="btn" id="diag-nova">${tg("dg_nova")}</button>
      </div>
      <div class="tabela-wrap" style="margin-top:16px"><table class="tabela">
        <thead><tr><th>${tg("dg_colaborador")}</th><th>${tg("cargo")}</th><th>${tg("dg_unidade")}</th>
          <th class="num">${tg("status")}</th><th class="num">${tg("dg_atualizada")}</th><th></th></tr></thead>
        <tbody>
          ${r.sessoes.map((s) => `
            <tr>
              <td><strong>${esc(s.colaborador)}</strong></td>
              <td>${esc(s.cargo || "")}</td>
              <td>${esc(s.unidade || "")}</td>
              <td class="num">${s.status === "concluida"
                ? '<span class="badge ok">' + tg("dg_concluida") + "</span>"
                : '<span class="badge warn">' + tg("dg_rascunho") + "</span>"}</td>
              <td class="num" style="font-size:.8rem;color:var(--muted)">${esc(fmtDataHora(s.atualizado_em))}</td>
              <td class="num">
                <button class="btn secondary small" data-abrir="${s.id}">${tg("dg_abrir")}</button>
                <button class="btn danger small" data-excluir="${s.id}">${tg("excluir")}</button>
              </td>
            </tr>`).join("") || '<tr><td colspan="6" style="color:var(--muted)">' + tg("dg_nenhuma_sessao") + "</td></tr>"}
        </tbody>
      </table></div>
      ${Object.keys(r.stats.por_unidade).length ? `
        <h3 style="margin-top:18px">${tg("dg_cobertura_unidade")}</h3>
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
      if (!confirm(tg("dg_confirmar_excluir"))) return;
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
    <option value="">${esc(vazio || tg("dg_selecione"))}</option>
    ${opcoes.map((o) => `<option value="${esc(o)}" ${atual === o ? "selected" : ""}>${esc(o)}</option>`).join("")}
  </select>`;
}

// junta os campos preenchidos do formulário num objeto (mesma estrutura salva no servidor)
function diagColetarDados() {
  const dados = {};
  document.querySelectorAll("#diag-form [data-campo]").forEach((campo) => {
    const valor = campo.type === "checkbox" ? campo.checked : campo.value.trim();
    if (valor === "" || valor === false) return;
    const partes = campo.dataset.campo.split(".");
    let alvo = dados;
    partes.slice(0, -1).forEach((p) => { alvo = alvo[p] = alvo[p] || {}; });
    alvo[partes[partes.length - 1]] = valor;
  });
  return dados;
}

// chamada ao trocar o idioma: redesenha o formulário aberto sem perder o que foi digitado
function diagRedesenharFormulario() {
  if (!diagSessaoAberta || !document.getElementById("diag-form")) return false;
  const sessao = diagSessaoAberta.sessao;
  const dados = diagColetarDados();
  diagFormSessao(sessao ? Object.assign({}, sessao, { dados }) : { dados, novo: true });
  return true;
}

function diagFormSessao(sessaoEntrada) {
  // { dados, novo: true } = sessão nova redesenhada ao trocar o idioma
  const sessao = sessaoEntrada && !sessaoEntrada.novo ? sessaoEntrada : null;
  diagSessaoAberta = { sessao };
  const d = (sessaoEntrada && sessaoEntrada.dados) || {};
  const el = document.getElementById("conteudo");
  el.innerHTML = `
    <div class="card" style="padding:22px 28px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <div>
          <h2 class="icone-titulo" style="margin-bottom:2px">${icone("lapis")}<span>${sessao ? tg("dg_sessao_de", { nome: esc(sessao.colaborador) }) : tg("dg_nova_titulo")}</span></h2>
          <p class="desc" style="margin:0">${tg("dg_instrumento")} · ${esc(DIAG.projeto.codigo)} · v1.0</p>
        </div>
        <button class="btn ghost small" id="diag-voltar">${tg("dg_voltar")}</button>
      </div>
    </div>
    <div id="diag-form">

    <div class="card">
      <h2>${tg("dg_a_titulo")}</h2>
      <h3>${tg("dg_a1")}</h3>
      <div class="grid cols-2">
        <label class="field">${tg("nome_completo")} ${diagInput("a1.nome", d)}</label>
        <label class="field">${tg("dg_a1_cargo")} ${diagInput("a1.cargo", d)}</label>
        <label class="field">${tg("dg_a1_area")} ${diagInput("a1.area", d)}</label>
        <label class="field">${tg("dg_a1_nivel")} ${diagSelect("a1.nivel", d, DIAG.opcoes.nivel_hierarquico)}</label>
        <label class="field">${tg("dg_a1_tempo")} ${diagInput("a1.tempo", d, tg("dg_a1_tempo_ph"))}</label>
        <label class="field">${tg("dg_a1_anterior")} ${diagInput("a1.cargo_anterior", d)}</label>
        <label class="field">${tg("dg_a1_data")} ${diagInput("a1.data", d, tg("dg_a1_data_ph"))}</label>
        <label class="field">${tg("dg_a1_observador")} ${diagInput("a1.observador", d)}</label>
      </div>
      <h3>${tg("dg_a2")}</h3>
      <div class="grid cols-2">
        <label class="field">${tg("dg_a2_formal")} ${diagSelect("a2.unidade", d, DIAG.unidades)}</label>
        <label class="field">${tg("dg_a2_real")} ${diagInput("a2.unidade_real", d)}</label>
      </div>
      <h3>${tg("dg_a3")}</h3>
      <div class="grid cols-2">
        <label class="field">${tg("dg_a3_superior")} ${diagInput("a3.superior", d, tg("dg_a3_superior_ph"))}</label>
        <label class="field">${tg("dg_a3_pares")} ${diagInput("a3.pares", d)}</label>
        <label class="field">${tg("dg_a3_subordinados")} ${diagInput("a3.subordinados", d)}</label>
        <label class="field">${tg("dg_a3_interlocutores")} ${diagInput("a3.interlocutores", d)}</label>
        <label class="field">${tg("dg_a3_externas")} ${diagInput("a3.externas", d)}</label>
      </div>
      <label class="field">${tg("dg_a3_funcoes_fora")} ${diagArea("a3.funcoes_fora", d)}</label>
    </div>

    <div class="card">
      <h2>${tg("dg_b_titulo")}</h2>
      <h3>${tg("dg_b1")}</h3>
      <p class="desc">${tg("dg_b1_desc")}</p>
      ${[0, 1, 2, 3, 4, 5, 6, 7].map((i) => `
        <div class="grid" style="grid-template-columns:2fr 1fr 1fr;gap:10px;margin-bottom:8px">
          <label class="field" style="margin:0">${i === 0 ? tg("dg_b1_atividade") : ""} ${diagInput("b1.atividades.a" + i + ".texto", d, tg("dg_b1_atividade_ph", { n: i + 1 }))}</label>
          <label class="field" style="margin:0">${i === 0 ? tg("dg_b1_frequencia") : ""} ${diagSelect("b1.atividades.a" + i + ".freq", d, DIAG.opcoes.frequencia)}</label>
          <label class="field" style="margin:0">${i === 0 ? tg("dg_b1_autonomia") : ""} ${diagSelect("b1.atividades.a" + i + ".aut", d, DIAG.opcoes.autonomia)}</label>
        </div>`).join("")}
      <div class="grid cols-2">
        <label class="field">${tg("dg_b1_nao_rotineiras")} ${diagArea("b1.nao_rotineiras", d)}</label>
        <label class="field">${tg("dg_b1_incidentes")} ${diagArea("b1.incidentes", d)}</label>
      </div>
      <h3>${tg("dg_b2")}</h3>
      <div class="grid cols-2">
        <label class="field">${tg("dg_b2_missao")} ${diagArea("b2.missao", d, 3)}</label>
        <label class="field">${tg("dg_b2_reformulacao")} ${diagArea("b2.reformulacao", d, 3)}</label>
      </div>
      <h3>${tg("dg_b3")}</h3>
      ${DIAG.familias_tic.map((f, i) => `
        <div class="grid" style="grid-template-columns:auto 2fr 1fr;gap:12px;align-items:center;margin-bottom:6px">
          <input type="checkbox" data-campo="b3.familias.f${i}.aplica" ${diagCampo("b3.familias.f" + i + ".aplica", d) ? "checked" : ""} style="width:auto">
          <span style="font-size:.9rem">${esc(f)}</span>
          ${diagSelect("b3.familias.f" + i + ".envolv", d, DIAG.opcoes.envolvimento, tg("dg_b3_grau"))}
        </div>`).join("")}
      <label class="field" style="margin-top:10px">${tg("dg_b3_dominios")} ${diagArea("b3.dominios", d)}</label>
      <h3>${tg("dg_b4")}</h3>
      ${[0, 1, 2].map((i) => `
        <div class="comp-item" style="display:block">
          <div class="nome" style="margin-bottom:8px">${tg("dg_b4_funcao", { n: i + 1 })}</div>
          <div class="grid cols-2">
            <label class="field">${tg("dg_b4_designacao")} ${diagInput("b4.funcoes.f" + i + ".designacao", d)}</label>
            <label class="field">${tg("dg_b4_criterio")} ${diagInput("b4.funcoes.f" + i + ".criterio", d)}</label>
            <label class="field">${tg("dg_b4_sub", { n: 1 })} ${diagInput("b4.funcoes.f" + i + ".sub1", d)}</label>
            <label class="field">${tg("dg_b4_sub", { n: 2 })} ${diagInput("b4.funcoes.f" + i + ".sub2", d)}</label>
            <label class="field">${tg("dg_b4_sub", { n: 3 })} ${diagInput("b4.funcoes.f" + i + ".sub3", d)}</label>
            <label class="field">${tg("dg_b4_condicoes")} ${diagInput("b4.funcoes.f" + i + ".condicoes", d)}</label>
          </div>
        </div>`).join("")}
      <h3>${tg("dg_b5")}</h3>
      ${DIAG.b5_dimensoes.map((dim, i) => `
        <div class="grid" style="grid-template-columns:1fr 1fr 1fr auto;gap:10px;align-items:end;margin-bottom:8px">
          <label class="field" style="margin:0">${i === 0 ? tg("dg_b5_dimensao") : ""}<input type="text" value="${esc(dim)}" disabled></label>
          <label class="field" style="margin:0">${i === 0 ? tg("dg_b5_prescrito") : ""} ${diagInput("b5.dim.d" + i + ".prescrito", d)}</label>
          <label class="field" style="margin:0">${i === 0 ? tg("dg_b5_real") : ""} ${diagInput("b5.dim.d" + i + ".real", d)}</label>
          <label class="field" style="margin:0">${i === 0 ? tg("dg_b5_discrepancia") : ""} ${diagSelect("b5.dim.d" + i + ".disc", d, ["Sim", "Não"], "?")}</label>
        </div>`).join("")}
      <label class="field" style="margin-top:8px">${tg("dg_b5_notas")} ${diagArea("b5.notas", d)}</label>
      <h3>${tg("dg_b6")}</h3>
      <div class="grid cols-2">
        ${DIAG.b6_indicadores.map(([chave, rotulo, op]) => `
          <label class="field">${esc(rotulo)} ${diagSelect("b6." + chave, d, DIAG.opcoes[op])}</label>`).join("")}
        <label class="field">${tg("dg_b6_global")} ${diagSelect("b6.nivel_global", d, DIAG.opcoes.nivel_global)}</label>
      </div>
      <label class="field">${tg("dg_b6_justificacao")} ${diagArea("b6.justificacao", d)}</label>
    </div>

    <div class="card">
      <h2>${tg("dg_c_titulo")}</h2>
      <h3>${tg("dg_c1")}</h3>
      <p class="desc">${tg("dg_c1_desc", { escala: DIAG.niveis.join(" · ") })}</p>
      ${Object.entries(DIAG.competencias_tecnicas).map(([grupo, lista]) => `
        <h3 style="font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;color:var(--blue-200)">${esc(grupo)}</h3>
        ${lista.map((c, i) => {
          const base = "c1." + grupo.replace(/[^A-Za-z]/g, "").toLowerCase() + ".c" + i;
          return `
          <div class="grid" style="grid-template-columns:auto 2fr 1fr 1fr;gap:10px;align-items:center;margin-bottom:6px">
            <input type="checkbox" data-campo="${base}.aplica" ${diagCampo(base + ".aplica", d) ? "checked" : ""} style="width:auto">
            <span style="font-size:.88rem">${esc(c)}</span>
            ${diagSelect(base + ".auto", d, DIAG.niveis, tg("dg_autopercebido"))}
            ${diagSelect(base + ".desejado", d, DIAG.niveis, tg("dg_desejado"))}
          </div>`;
        }).join("")}`).join("")}
      <h3>${tg("dg_c2")}</h3>
      ${DIAG.competencias_comportamentais.map((c, i) => `
        <div class="grid" style="grid-template-columns:2fr 1fr 1fr;gap:10px;align-items:center;margin-bottom:6px">
          <span style="font-size:.88rem">${esc(c)}</span>
          ${diagSelect("c2.c" + i + ".auto", d, DIAG.niveis, tg("dg_autopercebido"))}
          ${diagSelect("c2.c" + i + ".desejado", d, DIAG.niveis, tg("dg_desejado"))}
        </div>`).join("")}
      <h3>${tg("dg_c3")}</h3>
      <div class="grid cols-2">
        <label class="field">${tg("dg_c3_habilitacoes")} ${diagInput("c3.habilitacoes", d)}</label>
        <label class="field">${tg("dg_c3_area")} ${diagInput("c3.area_formacao", d)}</label>
        <label class="field">${tg("dg_c3_certificacoes")} ${diagInput("c3.certificacoes", d)}</label>
        <label class="field">${tg("dg_c3_recentes")} ${diagInput("c3.formacoes_recentes", d)}</label>
      </div>
      <label class="field">${tg("dg_c3_desejadas")} ${diagArea("c3.formacoes_desejadas", d)}</label>
      <h3>${tg("dg_c4")}</h3>
      <label class="field">${tg("dg_c4_falta")} ${diagArea("c4.falta", d)}</label>
      <label class="field">${tg("dg_c4_insuficiente")} ${diagArea("c4.insuficiente", d)}</label>
      <label class="field">${tg("dg_c4_formacao")} ${diagArea("c4.formacao_escolhida", d)}</label>
    </div>

    <div class="card">
      <div class="form-erro" id="diag-erro"></div>
      <div class="linha-acoes">
        <button class="btn secondary" id="diag-salvar">${tg("dg_salvar_rascunho")}</button>
        <button class="btn" id="diag-concluir">${tg("dg_salvar_concluir")}</button>
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
    const dados = diagColetarDados();
    const colaborador = (dados.a1 && dados.a1.nome) || "";
    if (!colaborador) {
      erro.textContent = tg("dg_erro_nome");
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
