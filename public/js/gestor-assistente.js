/* =====================================================================
   Assistente de configuração (primeiro acesso), só para o administrador.
   - assistenteVisao(el): cartão no topo da visão geral até a empresa
     concluir os passos obrigatórios ou o administrador dispensar.
   - assistenteConfig(el): resumo em Configurações, com "Mostrar na visão
     geral" para reabrir o cartão dispensado.
   - assistenteIr(aba, ancora): leva ao lugar certo do painel.
   API: GET /api/gestor/assistente, POST /api/gestor/assistente/dispensar.
   Textos em pt, en e es (tg do i18n-gestor.js, chaves "as_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  as_titulo: "Deixe a Bússola pronta para contratar",
  as_desc: "Alguns passos rápidos para a sua empresa aproveitar tudo o que o sistema faz.",
  as_progresso: "{n} de {t} passos concluídos",
  as_dispensar: "Dispensar",
  as_dispensar_dica: "Você pode reabrir este guia em Configurações.",
  as_fazer: "Fazer agora",
  as_rever: "Ver",
  as_feito: "Concluído",
  as_opcional: "Opcional",
  as_cfg_titulo: "Guia de configuração",
  as_cfg_desc: "Os passos para deixar a sua empresa pronta. {n} de {t} concluídos.",
  as_cfg_completo: "Tudo pronto! Todos os passos obrigatórios foram concluídos.",
  as_cfg_mostrar: "Mostrar na visão geral",
  as_cfg_ocultar: "Ocultar da visão geral",
  as_cfg_visivel: "O guia aparece no topo da visão geral.",
  as_cfg_oculto: "O guia está oculto da visão geral.",
  as_p_logo: "Envie a logo da empresa",
  as_w_logo: "Ela aparece na página de vagas, nos e-mails e nos documentos que os candidatos recebem.",
  as_p_equipe: "Convide a sua equipe",
  as_w_equipe: "Adicione os gestores que vão avaliar candidatos e fazer entrevistas.",
  as_p_cargos: "Crie um cargo com competências",
  as_w_cargos: "As competências alimentam a matriz de gaps e a avaliação dos candidatos.",
  as_p_voz: "Ligue a triagem por voz e revise o roteiro",
  as_w_voz: "Revisar o roteiro garante que a ligação pergunte exatamente o que importa para o cargo.",
  as_p_agenda: "Ative a agenda de entrevistas",
  as_w_agenda: "Os candidatos marcam a entrevista sozinhos nos horários que você liberar.",
  as_p_entrada: "Conecte o Indeed ou importe uma planilha",
  as_w_entrada: "Traga os candidatos que você já tem sem digitar nada de novo.",
  as_p_vaga: "Abra a sua primeira vaga",
  as_w_vaga: "A vaga entra na sua página de vagas e começa a receber candidatos.",
  as_p_onboarding: "Preencha os dados do empregador no onboarding",
  as_w_onboarding: "A razão social e o EIN são usados no W-4, no I-9 e nos outros formulários do novo contratado.",
  as_p_indicacoes: "Configure o programa de indicação",
  as_w_indicacoes: "A equipe compartilha um link pessoal e você acompanha os bônus de indicação.",
});
Object.assign(I18N_GESTOR.en, {
  as_titulo: "Get Bússola ready to hire",
  as_desc: "A few quick steps so your company gets the most out of the system.",
  as_progresso: "{n} of {t} steps done",
  as_dispensar: "Dismiss",
  as_dispensar_dica: "You can reopen this guide in Settings.",
  as_fazer: "Do it now",
  as_rever: "View",
  as_feito: "Done",
  as_opcional: "Optional",
  as_cfg_titulo: "Setup guide",
  as_cfg_desc: "The steps to get your company ready. {n} of {t} done.",
  as_cfg_completo: "You're all set! Every required step is done.",
  as_cfg_mostrar: "Show on overview",
  as_cfg_ocultar: "Hide from overview",
  as_cfg_visivel: "The guide shows at the top of the overview.",
  as_cfg_oculto: "The guide is hidden from the overview.",
  as_p_logo: "Upload your company logo",
  as_w_logo: "It shows on your careers page and on the emails and documents candidates receive.",
  as_p_equipe: "Invite your team",
  as_w_equipe: "Add the managers who will review candidates and run interviews.",
  as_p_cargos: "Create a position with competencies",
  as_w_cargos: "Competencies power the skills gap matrix and how candidates are scored.",
  as_p_voz: "Turn on voice screening and review the script",
  as_w_voz: "Reviewing the script makes sure the call asks exactly what matters for the role.",
  as_p_agenda: "Turn on interview scheduling",
  as_w_agenda: "Candidates book their own interviews in the time slots you open.",
  as_p_entrada: "Connect Indeed or import a spreadsheet",
  as_w_entrada: "Bring in the candidates you already have without retyping anything.",
  as_p_vaga: "Open your first job",
  as_w_vaga: "The job goes live on your careers page and starts receiving candidates.",
  as_p_onboarding: "Add your employer details for onboarding",
  as_w_onboarding: "Your legal business name and EIN are used on the W-4, I-9 and other new hire forms.",
  as_p_indicacoes: "Set up the referral program",
  as_w_indicacoes: "Your team shares a personal link and you keep track of referral bonuses.",
});
Object.assign(I18N_GESTOR.es, {
  as_titulo: "Deja Bússola lista para contratar",
  as_desc: "Unos pasos rápidos para que tu empresa aproveche todo lo que hace el sistema.",
  as_progresso: "{n} de {t} pasos completados",
  as_dispensar: "Ocultar",
  as_dispensar_dica: "Puedes volver a abrir esta guía en Configuración.",
  as_fazer: "Hacerlo ahora",
  as_rever: "Ver",
  as_feito: "Completado",
  as_opcional: "Opcional",
  as_cfg_titulo: "Guía de configuración",
  as_cfg_desc: "Los pasos para dejar lista tu empresa. {n} de {t} completados.",
  as_cfg_completo: "¡Todo listo! Completaste todos los pasos obligatorios.",
  as_cfg_mostrar: "Mostrar en la vista general",
  as_cfg_ocultar: "Ocultar de la vista general",
  as_cfg_visivel: "La guía aparece arriba en la vista general.",
  as_cfg_oculto: "La guía está oculta de la vista general.",
  as_p_logo: "Sube el logo de la empresa",
  as_w_logo: "Aparece en tu página de vacantes y en los correos y documentos que reciben los candidatos.",
  as_p_equipe: "Invita a tu equipo",
  as_w_equipe: "Agrega a los gerentes que van a evaluar candidatos y hacer entrevistas.",
  as_p_cargos: "Crea un puesto con competencias",
  as_w_cargos: "Las competencias alimentan la matriz de brechas y la evaluación de los candidatos.",
  as_p_voz: "Activa la entrevista por voz y revisa el guion",
  as_w_voz: "Revisar el guion asegura que la llamada pregunte justo lo que importa para el puesto.",
  as_p_agenda: "Activa la agenda de entrevistas",
  as_w_agenda: "Los candidatos agendan su entrevista solos en los horarios que tú habilites.",
  as_p_entrada: "Conecta Indeed o importa una hoja de cálculo",
  as_w_entrada: "Trae a los candidatos que ya tienes sin volver a escribir nada.",
  as_p_vaga: "Abre tu primera vacante",
  as_w_vaga: "La vacante se publica en tu página de vacantes y empieza a recibir candidatos.",
  as_p_onboarding: "Completa los datos del empleador para la incorporación",
  as_w_onboarding: "La razón social y el EIN se usan en el W-4, el I-9 y los demás formularios del nuevo empleado.",
  as_p_indicacoes: "Configura el programa de recomendados",
  as_w_indicacoes: "Tu equipo comparte un enlace personal y tú das seguimiento a los bonos por recomendación.",
});

function assistenteEsc(v) {
  return typeof esc === "function" ? esc(v) : String(v == null ? "" : v);
}

function assistenteBarra(pct) {
  const p = Math.max(0, Math.min(100, Number(pct) || 0));
  return `<div style="height:10px;border-radius:999px;background:var(--surface-2);overflow:hidden;margin:10px 0 6px">
      <div style="height:100%;width:${p}%;background:var(--accent-grad, var(--ok));border-radius:999px"></div></div>`;
}

function assistenteListaPassos(passos) {
  return `<div class="assistente-passos" style="display:flex;flex-direction:column;gap:10px;margin-top:12px">
    ${passos.map((p) => `
      <div style="display:flex;gap:12px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;padding:10px 12px;border:1px solid var(--line, #e4e9f0);border-radius:12px;${p.feito ? "opacity:.75" : ""}">
        <div style="display:flex;gap:10px;align-items:flex-start;flex:1;min-width:220px">
          <span aria-hidden="true" style="flex:none;width:22px;height:22px;border-radius:999px;display:inline-flex;align-items:center;justify-content:center;${p.feito ? "background:var(--ok-bg);color:var(--ok)" : "border:2px solid var(--line, #c9d3e0)"}">${p.feito && typeof icone === "function" ? icone("check") : ""}</span>
          <div>
            <strong>${tg("as_p_" + p.id)}</strong>
            ${p.opcional ? ` <span class="badge tipo">${tg("as_opcional")}</span>` : ""}
            ${p.feito ? ` <span class="badge ok">${tg("as_feito")}</span>` : ""}
            <div class="desc" style="font-size:.85rem;margin-top:2px">${tg("as_w_" + p.id)}</div>
          </div>
        </div>
        <button class="btn ${p.feito ? "ghost" : "secondary"} small" data-as-aba="${assistenteEsc(p.aba)}" data-as-ancora="${assistenteEsc(p.ancora || "")}">${tg(p.feito ? "as_rever" : "as_fazer")}</button>
      </div>`).join("")}
  </div>`;
}

function assistenteLigarBotoes(raiz) {
  raiz.querySelectorAll("[data-as-aba]").forEach((b) =>
    b.addEventListener("click", () => assistenteIr(b.dataset.asAba, b.dataset.asAncora)));
}

// troca de aba e rola até a seção (as seções de Configurações carregam depois)
function assistenteIr(aba, ancora) {
  if (typeof abaAtiva === "undefined" || typeof desenharPainel !== "function") return;
  abaAtiva = aba;
  if (typeof pipelineAberto !== "undefined") pipelineAberto = null;
  desenharPainel();
  window.scrollTo(0, 0);
  if (!ancora) return;
  let tentativas = 0;
  const procurar = () => {
    const alvo = document.getElementById(ancora);
    if (alvo && alvo.innerHTML.trim()) {
      alvo.scrollIntoView({ behavior: "smooth", block: "start" });
      const card = alvo.querySelector(".card") || alvo;
      card.style.transition = "box-shadow .3s";
      card.style.boxShadow = "0 0 0 3px var(--accent, #3B67CA)";
      setTimeout(() => { card.style.boxShadow = ""; }, 2200);
      return;
    }
    if (++tentativas < 30) setTimeout(procurar, 150);
  };
  setTimeout(procurar, 100);
}

async function assistenteVisao(el) {
  if (!el) return;
  if (!(typeof infoGestor === "function" && infoGestor().admin)) { el.remove(); return; }
  let r;
  try {
    r = await api("/api/gestor/assistente");
  } catch (e) {
    el.remove();
    return;
  }
  if (!r || !r.mostrar) { el.remove(); return; }
  el.classList.add("card");
  el.innerHTML = `
    <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap">
      <div>
        <h2 class="icone-titulo">${typeof icone === "function" ? icone("bussola") : ""}<span>${tg("as_titulo")}</span></h2>
        <p class="desc">${tg("as_desc")}</p>
      </div>
      <button class="btn ghost small" id="as-dispensar" title="${assistenteEsc(tg("as_dispensar_dica"))}">${tg("as_dispensar")}</button>
    </div>
    ${assistenteBarra(r.pct)}
    <p class="desc" style="font-size:.85rem">${tg("as_progresso", { n: r.feitos, t: r.total })}</p>
    ${assistenteListaPassos(r.passos || [])}
    <p class="desc" style="font-size:.8rem;margin-top:10px">${tg("as_dispensar_dica")}</p>`;
  assistenteLigarBotoes(el);
  el.querySelector("#as-dispensar").addEventListener("click", async () => {
    try {
      await api("/api/gestor/assistente/dispensar", { method: "POST", body: { dispensado: true } });
      el.remove();
    } catch (e) {
      alert(e.message);
    }
  });
}

async function assistenteConfig(el) {
  if (!el) return;
  if (!(typeof infoGestor === "function" && infoGestor().admin)) { el.innerHTML = ""; return; }
  let r;
  try {
    r = await api("/api/gestor/assistente");
  } catch (e) {
    el.innerHTML = "";
    return;
  }
  const situacao = r.completo ? tg("as_cfg_completo")
    : tg(r.dispensado ? "as_cfg_oculto" : "as_cfg_visivel");
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${typeof icone === "function" ? icone("bussola") : ""}<span>${tg("as_cfg_titulo")}</span></h2>
      <p class="desc">${tg("as_cfg_desc", { n: r.feitos, t: r.total })}</p>
      ${assistenteBarra(r.pct)}
      <p class="desc" style="font-size:.85rem">${assistenteEsc(situacao)}</p>
      <details class="mt"><summary style="cursor:pointer">${tg("as_progresso", { n: r.feitos, t: r.total })}</summary>
        ${assistenteListaPassos(r.passos || [])}
      </details>
      ${r.completo ? "" : `<div class="linha-acoes" style="margin-top:12px">
        <button class="btn secondary small" id="as-cfg-alternar">${tg(r.dispensado ? "as_cfg_mostrar" : "as_cfg_ocultar")}</button>
      </div>`}
    </div>`;
  assistenteLigarBotoes(el);
  const b = el.querySelector("#as-cfg-alternar");
  if (b) b.addEventListener("click", async () => {
    b.disabled = true;
    try {
      await api("/api/gestor/assistente/dispensar", { method: "POST", body: { dispensado: !r.dispensado } });
      if (r.dispensado) {
        abaAtiva = "visao";
        desenharPainel();
        window.scrollTo(0, 0);
      } else {
        assistenteConfig(el);
      }
    } catch (e) {
      b.disabled = false;
      alert(e.message);
    }
  });
}
