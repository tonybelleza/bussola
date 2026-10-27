/* =====================================================================
   Funções compartilhadas de renderização de resultados
   (usadas pela área do candidato e pelo painel do gestor)
   ===================================================================== */

function esc(txt) {
  return String(txt == null ? "" : txt)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Texto dos blocos de resultado. Na área do candidato (que carrega
// i18n-candidato.js) usa t() no idioma escolhido; no painel do gestor,
// que não carrega o dicionário, fica o português passado em "pt".
function txr(chave, pt, vars) {
  if (typeof I18N_CAND !== "undefined" && typeof t === "function") return t(chave, vars);
  return vars ? pt.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : pt;
}

function tituloIcone(ic, texto) {
  return `<h2 class="icone-titulo">${icone(ic)}<span>${texto}</span></h2>`;
}

// ------------------------------------------------ pontuação DISC
function calcularDisc(respostas) {
  // respostas: [{mais: 'D', menos: 'C'}, ...]
  const mais = { D: 0, I: 0, S: 0, C: 0 };
  const menos = { D: 0, I: 0, S: 0, C: 0 };
  respostas.forEach((r) => { mais[r.mais]++; menos[r.menos]++; });
  const total = respostas.length;
  const scores = {}, pct = {};
  ["D", "I", "S", "C"].forEach((k) => {
    scores[k] = mais[k] - menos[k];
    pct[k] = Math.round(((scores[k] + total) / (2 * total)) * 100);
  });
  const ordem = ["D", "I", "S", "C"].sort((a, b) => scores[b] - scores[a]);
  return { mais, menos, scores, pct, dominante: ordem[0], secundario: ordem[1] };
}

// ------------------------------------------------ pontuação BASE
function calcularBase(rodadas) {
  // rodadas: [['B','A','S','E'], ...] com a ordem escolhida (1º ao 4º).
  // Pontuação do teste original: 1º = 4, 2º = 3, 3º = 2, 4º = 1.
  const pontos = { B: 0, A: 0, S: 0, E: 0 };
  const primeiros = { B: 0, A: 0, S: 0, E: 0 };
  rodadas.forEach((ordem) => {
    ordem.forEach((p, i) => { pontos[p] += 4 - i; });
    primeiros[ordem[0]]++;
  });
  const n = rodadas.length;
  const pct = {};
  ["B", "A", "S", "E"].forEach((k) => {
    // normaliza a faixa possível (n a 4n pontos) para 0 a 100
    pct[k] = Math.round(((pontos[k] - n) / (3 * n)) * 100);
  });
  // desempate: quem teve mais primeiros lugares vem antes
  const ordem = ["B", "A", "S", "E"].sort((a, b) =>
    (pontos[b] - pontos[a]) || (primeiros[b] - primeiros[a]));
  return { pontos, pct, ordem, codigo: ordem.join(""), dominante: ordem[0], secundario: ordem[1] };
}

// ------------------------------------------------ blocos de resultado
function htmlBarras(pct, perfis, chaves) {
  return `<div class="perfil-barras">${chaves.map((k) => `
    <div class="perfil-barra">
      <div class="rotulo">${esc(perfis[k].nome)}</div>
      <div class="trilha"><div class="valor" style="width:${pct[k]}%;background:${perfis[k].cor}"></div></div>
      <div class="num">${pct[k]}%</div>
    </div>`).join("")}</div>`;
}

function htmlFortesDesenvolvimento(p) {
  return `
    <div class="grid cols-2 mt">
      <div>
        <h3>${txr("r_pontos_fortes", "Pontos fortes")}</h3>
        <ul class="lista-simples">${p.fortes.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      </div>
      <div>
        <h3>${txr("r_pontos_desenv", "Pontos de desenvolvimento")}</h3>
        <ul class="lista-simples">${p.desenvolvimento.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      </div>
    </div>`;
}

function htmlResultadoDisc(payload) {
  const p = DISC_PERFIS[payload.dominante];
  const sec = DISC_PERFIS[payload.secundario];
  return `
    ${tituloIcone("camadas", txr("r_disc_titulo", "Perfil Comportamental DISC"))}
    ${htmlBarras(payload.pct, DISC_PERFIS, ["D", "I", "S", "C"])}
    <div class="perfil-destaque">
      <div class="titulo">${txr("r_perfil_dominante", "Perfil dominante: {nome} ({letra})", { nome: esc(p.nome), letra: payload.dominante })}</div>
      <div>${txr("r_perfil_secundario", "Perfil secundário: {nome} ({letra})", { nome: esc(sec.nome), letra: payload.secundario })}</div>
    </div>
    <p>${esc(p.resumo)}</p>
    ${htmlFortesDesenvolvimento(p)}
    <h3>${txr("r_estilo_trabalho", "Estilo de trabalho")}</h3>
    <p>${esc(p.trabalho)}</p>`;
}

function htmlResultadoBase(payload) {
  // resultados antigos (antes do formato original) não têm "ordem"
  const ordem = payload.ordem ||
    ["B", "A", "S", "E"].sort((a, b) => payload.pct[b] - payload.pct[a]);
  const p = BASE_PERFIS[ordem[0]];
  const outros = ordem.slice(1);
  const posicoes = ordem.map((letra, i) => `
    <div class="passo">
      <div class="icone">${icone(BASE_PERFIS[letra].ic)}</div>
      <div class="info">
        <div class="titulo">${esc(BASE_POSICOES[i])}: ${esc(BASE_PERFIS[letra].nome)}</div>
        <p class="desc" style="margin:4px 0 0">${esc(BASE_PERFIS[letra].posicoes[i])}</p>
      </div>
    </div>`).join("");
  const comunicacao = outros.map((letra) => `
    <div>
      <h3 class="icone-titulo" style="font-size:.95rem">${icone(BASE_PERFIS[letra].ic)}<span>${txr("r_com_perfil", "Com o perfil {nome}", { nome: esc(BASE_PERFIS[letra].nome) })}</span></h3>
      <ul class="lista-simples">${(p.comunicacao[letra] || []).map((t) => `<li>${esc(t)}</li>`).join("")}</ul>
    </div>`).join("");
  return `
    ${tituloIcone("bussola", txr("r_base_titulo", "Código de Personalidade B.A.S.E."))}
    <div class="perfil-destaque">
      <div class="titulo icone-titulo">${icone(p.ic)}<span>${txr("r_seu_codigo", "Seu código: {codigo}", { codigo: esc(ordem.join(" · ")) })}</span></div>
      <div>${txr("r_arquetipo", "Arquétipo dominante: <strong>{nome}</strong>, {titulo}", { nome: esc(p.nome), titulo: esc(p.titulo || "") })}</div>
    </div>
    ${htmlBarras(payload.pct, BASE_PERFIS, ["B", "A", "S", "E"])}
    ${p.tagline ? `<p><em>${esc(p.tagline)}</em></p>` : ""}
    <p>${esc(p.resumo)}</p>
    <h3>${txr("r_pontos_fortes", "Pontos fortes")}</h3>
    <ul class="lista-simples grid cols-2" style="gap:4px 22px">${p.fortes.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
    ${p.posicoes ? `<h3>${txr("r_interpretar", "Como interpretar o código completo")}</h3>
    <p class="desc">${txr("r_interpretar_desc", "Cada posição do código revela algo diferente sobre como a pessoa funciona.")}</p>
    ${posicoes}` : ""}
    ${p.gatilhos ? `<h3>${txr("r_gatilhos", "Gatilhos e pontos de atenção")}</h3>
    <div class="grid cols-2 mt">
      <div>
        <h3 style="font-size:.95rem">${txr("r_impulsiona", "O que impulsiona")}</h3>
        <ul class="lista-simples">${p.gatilhos.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>
      </div>
      <div>
        <h3 style="font-size:.95rem">${txr("r_incomoda", "O que incomoda")}</h3>
        <ul class="lista-simples">${p.repulsores.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>
      </div>
    </div>` : ""}
    ${p.comunicacao ? `<h3>${txr("r_comunicar", "Como se comunicar com os outros perfis")}</h3>
    <div class="grid cols-3 mt">${comunicacao}</div>` : ""}`;
}

function htmlMatch(match, nomeCargo) {
  if (!match) return "";
  const rotulos = {
    competencias: txr("r_m_competencias", "Competências"),
    disc: txr("r_m_disc", "Perfil DISC"),
    base: txr("r_m_base", "Código B.A.S.E."),
    conhecimento: txr("r_m_conhecimento", "Conhecimento"),
    entrevista: txr("r_m_entrevista", "Entrevista"),
    voz: txr("r_m_voz", "Triagem por voz"),
  };
  const detalhes = {
    competencias: txr("r_md_competencias", "aderência às competências exigidas"),
    disc: match.disc_alvo ? txr("r_md_disc", "alinhamento com o perfil desejado: {nome}", { nome: DISC_PERFIS[match.disc_alvo].nome }) : "",
    base: match.base_alvo ? txr("r_md_base", "alinhamento com o arquétipo desejado: {nome}", { nome: BASE_PERFIS[match.base_alvo].nome }) : "",
    conhecimento: txr("r_md_conhecimento", "acertos no teste de conhecimento do cargo"),
    entrevista: txr("r_md_entrevista", "média do scorecard da entrevista estruturada"),
    voz: txr("r_md_voz", "pontuação da ligação de triagem com a Francisca"),
  };
  const CHAVES = ["voz", "competencias", "disc", "base", "conhecimento", "entrevista"];
  const ordem = CHAVES.filter((k) => k in match.componentes);
  // a triagem por voz só existe em cargos que a usam: não aparece como pendente
  const faltando = CHAVES.filter((k) => k !== "voz" && !(k in match.componentes));
  const nomesFaltando = {
    competencias: txr("r_mf_competencias", "autoavaliação de competências"),
    disc: txr("r_mf_disc", "teste DISC"),
    base: txr("r_mf_base", "teste B.A.S.E."),
    conhecimento: txr("r_mf_conhecimento", "teste de conhecimento"),
    entrevista: txr("r_mf_entrevista", "entrevista"),
  };
  return `
    ${tituloIcone("alvo", txr("r_match_titulo", "Match com o cargo") + (nomeCargo ? ": " + esc(nomeCargo) : ""))}
    <p class="desc">${txr("r_match_desc", "Índice único que cruza todas as dimensões da avaliação: competências (peso 30%), perfil DISC (15%), código B.A.S.E. (15%), teste de conhecimento (20%) e entrevista (20%). Os pesos se redistribuem sobre o que já foi respondido.")}${"voz" in match.componentes ? txr("r_match_desc_voz", " A triagem por voz entra com o peso definido no cargo e os demais componentes dividem o restante.") : ""}</p>
    <div class="match-geral">
      <div class="match-num">${match.geral}%</div>
      <div class="match-rotulo">${txr("r_match_geral", "match geral")}</div>
    </div>
    <div class="perfil-barras">
      ${ordem.map((k) => `
        <div class="perfil-barra">
          <div class="rotulo" title="${esc(detalhes[k])}">${rotulos[k]}</div>
          <div class="trilha"><div class="valor" style="width:${match.componentes[k]}%;background:var(--accent-grad)"></div></div>
          <div class="num">${match.componentes[k]}%</div>
        </div>`).join("")}
    </div>
    ${faltando.length ? `<p class="desc" style="margin-top:10px">${txr("r_pendente", "Ainda não considerado (pendente): {lista}.", { lista: faltando.map((k) => nomesFaltando[k]).join(", ") })}</p>` : ""}`;
}

function classeGap(item) {
  if (!item.respondida) return "vazio";
  if (item.gap === 0) return "ok";
  if (item.gap <= 2) return "medio";
  return "alto";
}

function badgeStatus(status) {
  if (status === "apto") return '<span class="badge ok">' + txr("r_apto", "Apto para a função") + "</span>";
  if (status === "desenvolvimento") return '<span class="badge warn">' + txr("r_desenv", "Em desenvolvimento") + "</span>";
  return '<span class="badge err">' + txr("r_gap_alto", "Gap alto") + "</span>";
}

function htmlMatrizGaps(gaps) {
  if (!gaps) return "";
  const cargo = gaps.cargo;
  const linhas = gaps.itens.map((i) => `
    <tr>
      <td><strong>${esc(i.nome)}</strong> ${i.obrigatoria ? `<span class="badge err" title="${txr("r_obrig_title", "Competência obrigatória")}">${txr("obrigatoria", "obrigatória")}</span>` : ""}</td>
      <td><span class="badge tipo">${esc(TIPOS_COMPETENCIA[i.tipo] || i.tipo)}</span></td>
      <td class="num">${i.nivel_requerido}</td>
      <td class="num">${i.respondida ? i.nivel_atual : "·"}</td>
      <td class="num"><span class="celula-gap ${classeGap(i)}">${i.respondida ? (i.gap === 0 ? "OK" : "-" + i.gap) : txr("r_sem_resposta", "sem resposta")}</span></td>
    </tr>`).join("");
  const plano = gaps.plano_desenvolvimento.length
    ? `<h3>${txr("r_plano", "Plano de desenvolvimento sugerido")}</h3>
       <ol class="lista-simples">${gaps.plano_desenvolvimento.map((i) =>
        `<li><strong>${esc(i.nome)}</strong> (${txr("r_gap", "gap {n}", { n: i.gap })})${i.obrigatoria ? " · <em>" + txr("obrigatoria", "obrigatória") + "</em>" : ""}<br>${esc(i.recomendacao || "")}</li>`).join("")}</ol>`
    : (gaps.respondeu_autoavaliacao ? '<p class="mt">' + txr("r_nenhum_gap", "Nenhum gap identificado: todas as competências exigidas foram atendidas.") + "</p>" : "");
  const avisoSemResposta = gaps.respondeu_autoavaliacao ? "" :
    '<div class="aviso mb">' + txr("r_aviso_sem_auto", "A autoavaliação de competências ainda não foi respondida, por isso os níveis atuais aparecem zerados.") + "</div>";
  return `
    ${tituloIcone("matriz", txr("r_matriz_titulo", "Matriz de Gaps: {cargo}", { cargo: esc(cargo.nome) }))}
    <p class="desc">${esc(cargo.area)}${cargo.nivel ? " · " + esc(cargo.nivel) : ""}</p>
    ${avisoSemResposta}
    <div class="perfil-destaque">
      <div class="titulo">${txr("r_aderencia", "Aderência ao cargo: {pct}%", { pct: gaps.aderencia })}</div>
      <div>${badgeStatus(gaps.status)}${gaps.obrigatorias_pendentes ? " · " + txr("r_obrig_pend", "{n} competência(s) obrigatória(s) com gap", { n: gaps.obrigatorias_pendentes }) : ""}</div>
    </div>
    <div class="tabela-wrap">
      <table class="tabela">
        <thead><tr><th>${txr("r_th_comp", "Competência")}</th><th>${txr("r_th_tipo", "Tipo")}</th><th class="num">${txr("r_th_exigido", "Exigido")}</th><th class="num">${txr("r_th_atual", "Atual")}</th><th class="num">${txr("r_th_gap", "Gap")}</th></tr></thead>
        <tbody>${linhas}</tbody>
      </table>
    </div>
    ${plano}`;
}
