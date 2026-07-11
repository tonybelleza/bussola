/* =====================================================================
   Funções compartilhadas de renderização de resultados
   (usadas pela área do candidato e pelo painel do gestor)
   ===================================================================== */

function esc(txt) {
  return String(txt == null ? "" : txt)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
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
  // rodadas: [['B','A','S','E'], ...] — ordem escolhida (1º ao 4º)
  const pontos = { B: 0, A: 0, S: 0, E: 0 };
  rodadas.forEach((ordem) => {
    ordem.forEach((p, i) => { pontos[p] += 4 - i; });
  });
  const n = rodadas.length;
  const pct = {};
  ["B", "A", "S", "E"].forEach((k) => {
    pct[k] = Math.round(((pontos[k] - n) / (3 * n)) * 100);
  });
  const ordem = ["B", "A", "S", "E"].sort((a, b) => pontos[b] - pontos[a]);
  return { pontos, pct, dominante: ordem[0], secundario: ordem[1] };
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
        <h3>Pontos fortes</h3>
        <ul class="lista-simples">${p.fortes.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      </div>
      <div>
        <h3>Pontos de desenvolvimento</h3>
        <ul class="lista-simples">${p.desenvolvimento.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      </div>
    </div>`;
}

function htmlResultadoDisc(payload) {
  const p = DISC_PERFIS[payload.dominante];
  const sec = DISC_PERFIS[payload.secundario];
  return `
    ${tituloIcone("camadas", "Perfil Comportamental DISC")}
    ${htmlBarras(payload.pct, DISC_PERFIS, ["D", "I", "S", "C"])}
    <div class="perfil-destaque">
      <div class="titulo">Perfil dominante: ${esc(p.nome)} (${payload.dominante})</div>
      <div>Perfil secundário: ${esc(sec.nome)} (${payload.secundario})</div>
    </div>
    <p>${esc(p.resumo)}</p>
    ${htmlFortesDesenvolvimento(p)}
    <h3>Estilo de trabalho</h3>
    <p>${esc(p.trabalho)}</p>`;
}

function htmlResultadoBase(payload) {
  const p = BASE_PERFIS[payload.dominante];
  const sec = BASE_PERFIS[payload.secundario];
  return `
    ${tituloIcone("bussola", "Código de Personalidade B.A.S.E.")}
    ${htmlBarras(payload.pct, BASE_PERFIS, ["B", "A", "S", "E"])}
    <div class="perfil-destaque">
      <div class="titulo icone-titulo">${icone(p.ic)}<span>Arquétipo dominante: ${esc(p.nome)}</span></div>
      <div>Arquétipo secundário: ${esc(sec.nome)}</div>
    </div>
    <p>${esc(p.resumo)}</p>
    ${htmlFortesDesenvolvimento(p)}`;
}

function htmlMatch(match, nomeCargo) {
  if (!match) return "";
  const rotulos = {
    competencias: "Competências",
    disc: "Perfil DISC",
    base: "Código B.A.S.E.",
    conhecimento: "Conhecimento",
    entrevista: "Entrevista",
  };
  const detalhes = {
    competencias: "aderência às competências exigidas",
    disc: match.disc_alvo ? "alinhamento com o perfil desejado: " + DISC_PERFIS[match.disc_alvo].nome : "",
    base: match.base_alvo ? "alinhamento com o arquétipo desejado: " + BASE_PERFIS[match.base_alvo].nome : "",
    conhecimento: "acertos no teste de conhecimento do cargo",
    entrevista: "média do scorecard da entrevista estruturada",
  };
  const CHAVES = ["competencias", "disc", "base", "conhecimento", "entrevista"];
  const ordem = CHAVES.filter((k) => k in match.componentes);
  const faltando = CHAVES.filter((k) => !(k in match.componentes));
  const nomesFaltando = {
    competencias: "autoavaliação de competências", disc: "teste DISC",
    base: "teste B.A.S.E.", conhecimento: "teste de conhecimento", entrevista: "entrevista",
  };
  return `
    ${tituloIcone("alvo", "Match com o cargo" + (nomeCargo ? ": " + esc(nomeCargo) : ""))}
    <p class="desc">Índice único que cruza todas as dimensões da avaliação: competências (peso 30%), perfil DISC (15%), código B.A.S.E. (15%), teste de conhecimento (20%) e entrevista (20%). Os pesos se redistribuem sobre o que já foi respondido.</p>
    <div class="match-geral">
      <div class="match-num">${match.geral}%</div>
      <div class="match-rotulo">match geral</div>
    </div>
    <div class="perfil-barras">
      ${ordem.map((k) => `
        <div class="perfil-barra">
          <div class="rotulo" title="${esc(detalhes[k])}">${rotulos[k]}</div>
          <div class="trilha"><div class="valor" style="width:${match.componentes[k]}%;background:var(--accent-grad)"></div></div>
          <div class="num">${match.componentes[k]}%</div>
        </div>`).join("")}
    </div>
    ${faltando.length ? `<p class="desc" style="margin-top:10px">Ainda não considerado (pendente): ${faltando.map((k) => nomesFaltando[k]).join(", ")}.</p>` : ""}`;
}

function classeGap(item) {
  if (!item.respondida) return "vazio";
  if (item.gap === 0) return "ok";
  if (item.gap <= 2) return "medio";
  return "alto";
}

function badgeStatus(status) {
  if (status === "apto") return '<span class="badge ok">Apto para a função</span>';
  if (status === "desenvolvimento") return '<span class="badge warn">Em desenvolvimento</span>';
  return '<span class="badge err">Gap alto</span>';
}

function htmlMatrizGaps(gaps) {
  if (!gaps) return "";
  const cargo = gaps.cargo;
  const linhas = gaps.itens.map((i) => `
    <tr>
      <td><strong>${esc(i.nome)}</strong> ${i.obrigatoria ? '<span class="badge err" title="Competência obrigatória">obrigatória</span>' : ""}</td>
      <td><span class="badge tipo">${esc(TIPOS_COMPETENCIA[i.tipo] || i.tipo)}</span></td>
      <td class="num">${i.nivel_requerido}</td>
      <td class="num">${i.respondida ? i.nivel_atual : "—"}</td>
      <td class="num"><span class="celula-gap ${classeGap(i)}">${i.respondida ? (i.gap === 0 ? "OK" : "-" + i.gap) : "sem resposta"}</span></td>
    </tr>`).join("");
  const plano = gaps.plano_desenvolvimento.length
    ? `<h3>Plano de desenvolvimento sugerido</h3>
       <ol class="lista-simples">${gaps.plano_desenvolvimento.map((i) =>
        `<li><strong>${esc(i.nome)}</strong> (gap ${i.gap})${i.obrigatoria ? " · <em>obrigatória</em>" : ""}<br>${esc(i.recomendacao || "")}</li>`).join("")}</ol>`
    : (gaps.respondeu_autoavaliacao ? '<p class="mt">Nenhum gap identificado: todas as competências exigidas foram atendidas.</p>' : "");
  const avisoSemResposta = gaps.respondeu_autoavaliacao ? "" :
    '<div class="aviso mb">A autoavaliação de competências ainda não foi respondida, por isso os níveis atuais aparecem zerados.</div>';
  return `
    ${tituloIcone("matriz", "Matriz de Gaps: " + esc(cargo.nome))}
    <p class="desc">${esc(cargo.area)}${cargo.nivel ? " · " + esc(cargo.nivel) : ""}</p>
    ${avisoSemResposta}
    <div class="perfil-destaque">
      <div class="titulo">Aderência ao cargo: ${gaps.aderencia}%</div>
      <div>${badgeStatus(gaps.status)}${gaps.obrigatorias_pendentes ? ` · ${gaps.obrigatorias_pendentes} competência(s) obrigatória(s) com gap` : ""}</div>
    </div>
    <div class="tabela-wrap">
      <table class="tabela">
        <thead><tr><th>Competência</th><th>Tipo</th><th class="num">Exigido</th><th class="num">Atual</th><th class="num">Gap</th></tr></thead>
        <tbody>${linhas}</tbody>
      </table>
    </div>
    ${plano}`;
}
