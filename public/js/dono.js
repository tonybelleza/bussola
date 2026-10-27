/* =====================================================================
   Painel do Dono do software: contas, troubleshooting e billing.
   Acesso exclusivo do proprietário (Tony), acima dos gestores.
   ===================================================================== */

const app = document.getElementById("app");
let abaAtiva = "empresas";
let telaAtual = "";  // "setup", "login" ou "painel": redesenhada ao trocar o idioma

async function api(caminho, opcoes = {}) {
  const headers = { "Content-Type": "application/json", "X-Idioma": idiomaDono };
  const token = localStorage.getItem("dono_token");
  if (token) headers["X-Dono-Token"] = token;
  const resp = await fetch(caminho, {
    method: opcoes.method || "GET",
    headers,
    body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
  });
  const dados = await resp.json().catch(() => ({}));
  if (resp.status === 401 && !caminho.endsWith("/login") && !caminho.endsWith("/setup")) {
    localStorage.removeItem("dono_token");
    telaLogin();
    throw new Error(dados.erro || td("sessao_expirada"));
  }
  if (!resp.ok) throw new Error(dados.erro || td("erro_comunicacao"));
  return dados;
}

document.getElementById("btn-sair").addEventListener("click", () => {
  localStorage.removeItem("dono_token");
  telaLogin();
});

// seletor de idioma: salva e redesenha a tela atual
montarSeletorIdiomaDono(() => {
  if (telaAtual === "setup") telaSetup();
  else if (telaAtual === "login") telaLogin();
  else if (telaAtual === "painel") desenhar().catch(() => {});
});

// ------------------------------------------------ acesso
function telaSetup() {
  telaAtual = "setup";
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:460px;margin:48px auto">
      <h2 class="icone-titulo">${icone("chave")}<span>${td("setup_titulo")}</span></h2>
      <p class="desc">${td("setup_desc")}</p>
      <label class="field">${td("setup_senha")} <input type="password" id="dn-senha" autocomplete="new-password"></label>
      <label class="field">${td("setup_confirmar")} <input type="password" id="dn-senha2" autocomplete="new-password"></label>
      <div class="form-erro" id="dn-erro"></div>
      <button class="btn block" id="dn-criar">${td("setup_criar")}</button>
    </div>`;
  document.getElementById("dn-criar").addEventListener("click", async () => {
    const erro = document.getElementById("dn-erro");
    const senha = document.getElementById("dn-senha").value;
    if (senha !== document.getElementById("dn-senha2").value) {
      erro.textContent = td("senhas_nao_conferem");
      return;
    }
    try {
      const r = await api("/api/dono/setup", { method: "POST", body: { senha } });
      localStorage.setItem("dono_token", r.token);
      iniciar();
    } catch (e) {
      erro.textContent = e.message;
    }
  });
}

function telaLogin() {
  telaAtual = "login";
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:420px;margin:48px auto">
      <h2 class="icone-titulo">${icone("cadeado")}<span>${td("login_titulo")}</span></h2>
      <p class="desc">${td("login_desc")}</p>
      <label class="field">${td("login_senha")}
        <input type="password" id="lg-senha" autocomplete="current-password">
      </label>
      <div class="form-erro" id="lg-erro"></div>
      <button class="btn block" id="lg-entrar">${td("login_entrar")}</button>
    </div>`;
  const entrar = async () => {
    const erro = document.getElementById("lg-erro");
    erro.textContent = "";
    try {
      const r = await api("/api/dono/login", {
        method: "POST",
        body: { senha: document.getElementById("lg-senha").value },
      });
      localStorage.setItem("dono_token", r.token);
      iniciar();
    } catch (e) {
      erro.textContent = e.message;
    }
  };
  document.getElementById("lg-entrar").addEventListener("click", entrar);
  document.getElementById("lg-senha").addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") entrar();
  });
}

// ------------------------------------------------ painel do administrador do sistema
async function desenhar() {
  telaAtual = "painel";
  document.getElementById("btn-sair").classList.remove("oculto");
  app.innerHTML = `
    <div class="tabs">
      ${[["empresas", td("aba_empresas")], ["visao", td("aba_visao")], ["contas", td("aba_contas")],
         ["integracoes", td("aba_integracoes")], ["config", td("aba_config")]]
        .map(([id, rot]) => `<button class="tab ${abaAtiva === id ? "ativa" : ""}" data-aba="${id}">${rot}</button>`).join("")}
    </div>
    <div id="conteudo"><p class="desc">${td("carregando")}</p></div>`;
  app.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => { abaAtiva = t.dataset.aba; desenhar(); })
  );
  const el = document.getElementById("conteudo");
  if (abaAtiva === "empresas") await abaEmpresas(el);
  if (abaAtiva === "visao") await abaVisao(el);
  if (abaAtiva === "contas") await abaContas(el);
  if (abaAtiva === "integracoes") await abaIntegracoes(el);
  if (abaAtiva === "config") abaConfig(el);
}

async function abaVisao(el) {
  const [r, emp] = await Promise.all([api("/api/dono/visao"), api("/api/dono/empresas")]);
  el.innerHTML = `
    <div class="metricas">
      <div class="metrica"><div class="num">${fmtNumDono(emp.empresas.length)}</div><div class="rot">${td("m_empresas")}</div></div>
      <div class="metrica"><div class="num">${fmtNumDono(r.totais.gestores)}</div><div class="rot">${td("m_contas_gestor")}</div></div>
      <div class="metrica"><div class="num">${fmtNumDono(r.totais.candidatos)}</div><div class="rot">${td("m_pessoas_avaliadas")}</div></div>
      <div class="metrica"><div class="num">${fmtNumDono(r.totais.vagas)}</div><div class="rot">${td("m_vagas_criadas")}</div></div>
      <div class="metrica"><div class="num">${fmtNumDono(r.totais.avaliacoes_completas)}</div><div class="rot">${td("m_avaliacoes_completas")}</div></div>
    </div>
    <div class="grid cols-2">
      <div class="card">
        <h2 class="icone-titulo">${icone("engrenagem")}<span>${td("saude_titulo")}</span></h2>
        <div class="tabela-wrap"><table class="tabela"><tbody>
          <tr><td>${td("saude_versao")}</td><td class="num"><strong>${esc(r.sistema.versao)}</strong></td></tr>
          <tr><td>Python</td><td class="num">${esc(r.sistema.python)}</td></tr>
          <tr><td>${td("saude_banco")}</td><td class="num">${td("mb", { n: fmtNumDono(r.sistema.banco_mb) })}</td></tr>
          <tr><td>${td("saude_ia")}</td><td class="num">${r.sistema.ia_configurada ? `<span class="badge ok">${td("configurada")}</span>` : `<span class="badge warn">${td("nao_configurada")}</span>`}</td></tr>
          <tr><td>${td("saude_email")}</td><td class="num">${r.sistema.smtp_configurado ? `<span class="badge ok">${td("configurado")}</span>` : `<span class="badge warn">${td("nao_configurado")}</span>`}</td></tr>
          <tr><td>${td("saude_backups")}</td><td class="num">${r.sistema.backups.length ? r.sistema.backups.map(esc).join("<br>") : td("nenhum")}</td></tr>
        </tbody></table></div>
      </div>
      <div class="card">
        <h2 class="icone-titulo">${icone("documento")}<span>${td("uso_titulo")}</span></h2>
        <div class="tabela-wrap"><table class="tabela">
          <thead><tr><th>${td("col_empresa")}</th><th class="num">${td("col_candidatos")}</th><th class="num">${td("col_vagas_abertas")}</th><th class="num">${td("col_ligacoes")}</th></tr></thead>
          <tbody>${emp.empresas.map((e) => `
            <tr><td><strong>${esc(e.nome)}</strong></td><td class="num">${fmtNumDono(e.candidatos)}</td>
            <td class="num">${fmtNumDono(e.vagas_abertas)}</td><td class="num">${fmtNumDono(e.ligacoes_voz)}</td></tr>`).join("")
            || `<tr><td colspan="4" style="color:var(--muted)">${td("nenhuma_empresa")}</td></tr>`}</tbody>
        </table></div>
      </div>
    </div>
    <div class="card">
      <h2 class="icone-titulo">${icone("bloco")}<span>${td("log_titulo")}</span></h2>
      <pre style="font-size:.72rem;color:var(--text-2);white-space:pre-wrap;max-height:260px;overflow-y:auto;background:rgba(7,11,20,.5);padding:14px;border-radius:12px">${esc(r.sistema.log || td("sem_registros"))}</pre>
    </div>`;
}

async function abaContas(el) {
  const r = await api("/api/dono/visao");
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("usuarios")}<span>${td("contas_titulo")}</span></h2>
      <p class="desc">${td("contas_desc")}</p>
      <div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>${td("col_nome")}</th><th>${td("col_empresa")}</th><th>${td("col_login")}</th><th>${td("col_local")}</th><th class="num">${td("col_perfil")}</th>
          <th class="num">${td("col_candidatos_visiveis")}</th><th></th></tr></thead>
        <tbody>${r.gestores.map((g) => `
          <tr>
            <td><strong>${esc(g.nome)}</strong><br><span style="color:var(--muted);font-size:.78rem">${g.email ? esc(g.email) : td("sem_email")}</span></td>
            <td>${esc(g.empresa || "")}</td>
            <td>${esc(g.login)}${g.aprovado ? "" : ` <span class="badge warn">${td("inativo")}</span>`}</td>
            <td>${g.local ? esc(g.local) : `<span style="color:var(--muted)">${td("empresa_toda")}</span>`}</td>
            <td class="num">${g.admin ? `<span class="badge neutral">${td("perfil_admin")}</span>` : `<span class="badge tipo">${td("perfil_gestor")}</span>`}</td>
            <td class="num">${fmtNumDono(g.candidatos_visiveis)}</td>
            <td class="num">
              <button class="btn secondary small" data-entrar="${g.id}">${td("entrar_conta")}</button>
              <button class="btn ghost small" data-senha="${g.id}">${td("redefinir_senha")}</button>
            </td>
          </tr>`).join("") || `<tr><td colspan="7" style="color:var(--muted)">${td("nenhuma_conta")}</td></tr>`}</tbody>
      </table></div>
    </div>`;
  ligarAcoesGestor(el, () => abaContas(el));
}

// ------------------------------------------------ empresas (subcontas)
const STATUS_EMPRESA = { ativa: "ok", teste: "neutral", suspensa: "err", cancelada: "tipo" };

async function abaEmpresas(el) {
  const r = await api("/api/dono/empresas");
  const mods = Object.entries(r.modulos_disponiveis || {});
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("camadas")}<span>${td("empresas_titulo")}</span></h2>
      <p class="desc">${td("empresas_desc")}</p>
      ${r.empresas.map((e) => `
        <div class="comp-item" style="margin-top:14px">
          <div class="nome" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px">
            <span><strong>${esc(e.nome)}</strong> <span class="badge ${STATUS_EMPRESA[e.status] || "tipo"}">${esc(rotuloStatusDono(e.status))}</span></span>
            <span style="color:var(--muted);font-size:.8rem">${esc(location.origin)}/vagas?e=${esc(e.slug)}</span>
          </div>
          <div class="metricas" style="margin:10px 0">
            <div class="metrica"><div class="num">${fmtNumDono(e.gestores)}</div><div class="rot">${td("m_gestores")}</div></div>
            <div class="metrica"><div class="num">${fmtNumDono(e.cargos)}</div><div class="rot">${td("m_cargos")}</div></div>
            <div class="metrica"><div class="num">${fmtNumDono(e.vagas_abertas)}</div><div class="rot">${td("m_vagas_abertas")}</div></div>
            <div class="metrica"><div class="num">${fmtNumDono(e.candidatos)}</div><div class="rot">${td("m_candidatos")}</div></div>
            <div class="metrica"><div class="num">${fmtNumDono(e.ligacoes_voz)}</div><div class="rot">${td("m_ligacoes_voz")}</div></div>
          </div>
          <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px">
            <select data-campo="status" data-id="${e.id}" style="margin:0">
              ${["ativa", "teste", "suspensa", "cancelada"].map((s) => `<option value="${s}" ${e.status === s ? "selected" : ""}>${esc(rotuloStatusDono(s))}</option>`).join("")}
            </select>
            <input type="text" data-campo="plano" data-id="${e.id}" value="${esc(e.plano)}" placeholder="${td("ph_plano")}" style="margin:0">
            <input type="text" data-campo="valor" data-id="${e.id}" value="${esc(e.valor)}" placeholder="${td("ph_valor")}" style="margin:0">
            <input type="text" data-campo="notas" data-id="${e.id}" value="${esc(e.notas)}" placeholder="${td("ph_notas")}" style="margin:0">
            <input type="text" data-campo="slug" data-id="${e.id}" value="${esc(e.slug)}" placeholder="${td("ph_slug")}" title="${td("title_slug")}" style="margin:0">
          </div>
          <div class="linha-acoes" style="margin-top:10px">
            ${mods.map(([m, rot]) => `<label class="badge ${e.modulos.includes(m) ? "ok" : ""}" style="cursor:pointer">
              <input type="checkbox" data-modulo="${m}" data-id="${e.id}" ${e.modulos.includes(m) ? "checked" : ""}> ${esc(rotuloModuloDono(m, rot))}</label>`).join("")}
            <button class="btn small" data-salvar-empresa="${e.id}">${td("salvar")}</button>
            <button class="btn secondary small" data-ver-gestores="${e.id}">${td("gestores_acesso")}</button>
            <label class="btn secondary small" style="cursor:pointer">${e.logo_url ? td("trocar_logo") : td("enviar_logo")}<input type="file" data-logo-empresa="${e.id}" accept="image/png,image/jpeg" style="display:none"></label>
            ${e.logo_url ? `<img src="${esc(e.logo_url)}" alt="" style="height:30px;max-width:120px;background:#fff;border-radius:6px;padding:2px 6px">` : ""}
          </div>
          <div id="gestores-empresa-${e.id}"></div>
        </div>`).join("") || `<p class="desc">${td("nenhuma_empresa")}</p>`}
    </div>
    <div class="card">
      <h2 class="icone-titulo">${icone("chave")}<span>${td("nova_empresa")}</span></h2>
      <div class="grid cols-2">
        <label class="field">${td("ne_nome")} <input type="text" id="ne-nome" placeholder="Belleza's Home Services CT"></label>
        <label class="field">${td("ne_situacao")} <select id="ne-status"><option value="ativa">${td("status_ativa")}</option><option value="teste">${td("status_teste")}</option></select></label>
      </div>
      <p class="desc">${td("ne_admin_desc")}</p>
      <div class="grid cols-2">
        <label class="field">${td("campo_nome")} <input type="text" id="ne-a-nome"></label>
        <label class="field">${td("campo_email")} <input type="email" id="ne-a-email"></label>
        <label class="field">${td("campo_login")} <input type="text" id="ne-a-login" autocomplete="off"></label>
        <label class="field">${td("campo_senha_min8")} <input type="password" id="ne-a-senha" autocomplete="new-password"></label>
      </div>
      <div class="form-erro" id="ne-erro"></div>
      <button class="btn" id="ne-criar">${td("criar_empresa")}</button>
    </div>`;

  const valor = (id, campo) => el.querySelector(`[data-campo="${campo}"][data-id="${id}"]`).value;
  el.querySelectorAll("[data-salvar-empresa]").forEach((b) => b.addEventListener("click", async () => {
    const id = b.dataset.salvarEmpresa;
    const modulos = [...el.querySelectorAll(`[data-modulo][data-id="${id}"]:checked`)].map((c) => c.dataset.modulo);
    try {
      await api("/api/dono/empresa/" + id, { method: "POST", body: {
        status: valor(id, "status"), plano: valor(id, "plano"), valor: valor(id, "valor"),
        notas: valor(id, "notas"), slug: valor(id, "slug"), modulos,
      } });
      b.textContent = td("salvo");
      setTimeout(() => abaEmpresas(el), 800);
    } catch (e) { alert(e.message); }
  }));
  el.querySelectorAll("[data-logo-empresa]").forEach((inp) => inp.addEventListener("change", () => {
    const f = inp.files[0];
    if (!f) return;
    const leitor = new FileReader();
    leitor.onload = async () => {
      try {
        await api("/api/dono/empresa/" + inp.dataset.logoEmpresa + "/logo", { method: "POST", body: { filename: f.name, data: String(leitor.result).split(",")[1] } });
        abaEmpresas(el);
      } catch (e) { alert(e.message); }
    };
    leitor.readAsDataURL(f);
  }));
  el.querySelectorAll("[data-ver-gestores]").forEach((b) => b.addEventListener("click", () =>
    gestoresDaEmpresa(Number(b.dataset.verGestores), el.querySelector("#gestores-empresa-" + b.dataset.verGestores))));
  el.querySelector("#ne-criar").addEventListener("click", async () => {
    const erro = el.querySelector("#ne-erro");
    erro.textContent = "";
    const corpo = { nome: el.querySelector("#ne-nome").value.trim(), status: el.querySelector("#ne-status").value };
    const login = el.querySelector("#ne-a-login").value.trim();
    if (login) corpo.admin = { nome: el.querySelector("#ne-a-nome").value.trim(), email: el.querySelector("#ne-a-email").value.trim(),
                               login, senha: el.querySelector("#ne-a-senha").value };
    try {
      await api("/api/dono/empresas", { method: "POST", body: corpo });
      abaEmpresas(el);
    } catch (e) { erro.textContent = e.message; }
  });
}

async function gestoresDaEmpresa(id, box) {
  const r = await api("/api/dono/empresa/" + id);
  box.innerHTML = `
    <div class="tabela-wrap" style="margin-top:10px"><table class="tabela">
      <thead><tr><th>${td("col_nome")}</th><th>${td("col_login")}</th><th>${td("col_local")}</th><th class="num">${td("col_perfil")}</th><th></th></tr></thead>
      <tbody>${r.gestores_lista.map((g) => `
        <tr><td><strong>${esc(g.nome)}</strong><br><span style="color:var(--muted);font-size:.78rem">${g.email ? esc(g.email) : td("sem_email")}</span></td>
          <td>${esc(g.login)}${g.aprovado ? "" : ` <span class="badge warn">${td("pendente")}</span>`}</td>
          <td>${g.local ? esc(g.local) : `<span style="color:var(--muted)">${td("empresa_toda")}</span>`}</td>
          <td class="num">${g.admin ? `<span class="badge neutral">${td("perfil_admin")}</span>` : `<span class="badge tipo">${td("perfil_gestor")}</span>`}</td>
          <td class="num"><button class="btn secondary small" data-entrar="${g.id}">${td("entrar_conta")}</button>
            <button class="btn ghost small" data-senha="${g.id}">${td("redefinir_senha")}</button></td></tr>`).join("")
        || `<tr><td colspan="5" style="color:var(--muted)">${td("nenhum_gestor")}</td></tr>`}</tbody>
    </table></div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-top:10px">
      <input type="text" id="ng-nome-${id}" placeholder="${td("campo_nome")}" style="margin:0">
      <input type="email" id="ng-email-${id}" placeholder="${td("campo_email")}" style="margin:0">
      <input type="text" id="ng-login-${id}" placeholder="${td("campo_login")}" style="margin:0" autocomplete="off">
      <input type="password" id="ng-senha-${id}" placeholder="${td("campo_senha_min8")}" style="margin:0" autocomplete="new-password">
      <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" id="ng-admin-${id}"> ${td("perfil_admin")}</label>
      <button class="btn small" id="ng-criar-${id}">${td("adicionar_gestor")}</button>
    </div>
    <p class="form-erro" id="ng-erro-${id}"></p>`;
  ligarAcoesGestor(box, () => gestoresDaEmpresa(id, box));
  box.querySelector("#ng-criar-" + id).addEventListener("click", async () => {
    try {
      await api("/api/dono/empresa/" + id + "/gestor", { method: "POST", body: {
        nome: box.querySelector("#ng-nome-" + id).value.trim(), email: box.querySelector("#ng-email-" + id).value.trim(),
        login: box.querySelector("#ng-login-" + id).value.trim(), senha: box.querySelector("#ng-senha-" + id).value,
        admin: box.querySelector("#ng-admin-" + id).checked,
      } });
      gestoresDaEmpresa(id, box);
    } catch (e) { box.querySelector("#ng-erro-" + id).textContent = e.message; }
  });
}

function ligarAcoesGestor(el, recarregar) {
  el.querySelectorAll("[data-entrar]").forEach((b) =>
    b.addEventListener("click", async () => {
      const r2 = await api("/api/dono/entrar-como", {
        method: "POST", body: { gestor_id: Number(b.dataset.entrar) },
      });
      localStorage.setItem("gestor_token", r2.token);
      localStorage.setItem("gestor_info", JSON.stringify({
        nome: r2.nome, login: r2.login, local: r2.local, admin: r2.admin,
        modulos: r2.modulos || [], empresa: r2.empresa || null,
      }));
      window.open("/gestor", "_blank");
    })
  );
  el.querySelectorAll("[data-senha]").forEach((b) =>
    b.addEventListener("click", async () => {
      const nova = prompt(td("prompt_nova_senha"));
      if (!nova) return;
      try {
        await api("/api/dono/gestor-senha", {
          method: "POST", body: { gestor_id: Number(b.dataset.senha), nova },
        });
        alert(td("senha_redefinida"));
        if (recarregar) recarregar();
      } catch (e) {
        alert(e.message);
      }
    })
  );
}

async function abaIntegracoes(el) {
  const r = await api("/api/dono/integracoes");
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("engrenagem")}<span>${td("int_titulo")}</span></h2>
      <p class="desc">${td("int_desc")}</p>
      <div class="grid cols-2">
        <div>
          <h3>${td("ia_titulo")}</h3>
          <p class="desc" style="font-size:.82rem">${td("ia_desc")}
            ${r.ia_configurada ? `<span class="badge ok">${td("ia_configurada_final", { final: esc(r.ia_final) })}</span>` : `<span class="badge warn">${td("nao_configurada")}</span>`}</p>
          <label class="field">${td("ia_chave")}
            <input type="password" id="int-chave" placeholder="${r.ia_configurada ? td("ph_trocar") : "sk-ant-..."}" autocomplete="off">
          </label>
        </div>
        <div>
          <h3>${td("smtp_titulo")}</h3>
          <p class="desc" style="font-size:.82rem">${td("smtp_desc")}
            ${r.smtp_host ? `<span class="badge ok">${td("configurado")}</span>` : `<span class="badge warn">${td("nao_configurado")}</span>`}</p>
          <label class="field">${td("smtp_servidor")} <input type="text" id="int-host" value="${esc(r.smtp_host)}" placeholder="smtp.gmail.com"></label>
          <div class="grid cols-2">
            <label class="field">${td("smtp_porta")} <span class="hint">${td("smtp_porta_dica")}</span><input type="text" id="int-porta" value="${esc(r.smtp_porta)}" placeholder="587"></label>
            <label class="field">${td("smtp_usuario")} <input type="text" id="int-usuario" value="${esc(r.smtp_usuario)}" placeholder="${td("ph_usuario")}"></label>
          </div>
          <label class="field">${td("smtp_senha")} ${r.smtp_senha_configurada ? `<span class="hint">${td("dica_trocar")}</span>` : ""}
            <input type="password" id="int-senha" autocomplete="off">
          </label>
          <label class="field">${td("smtp_remetente")} <span class="hint">${td("opcional")}</span>
            <input type="text" id="int-remetente" value="${esc(r.smtp_remetente)}" placeholder="${td("ph_remetente")}">
          </label>
        </div>
      </div>
      <div class="grid cols-2 mt">
        <label class="field">${td("url_publica")} <span class="hint">${td("url_publica_dica")}</span>
          <input type="text" id="int-url" value="${esc(r.url_publica)}" placeholder="${td("ph_url")}">
        </label>
        <label class="field">${td("retencao")} <span class="hint">${td("retencao_dica")}</span>
          <select id="int-retencao">
            <option value="0" ${r.retencao_meses === "0" ? "selected" : ""}>${td("retencao_nunca")}</option>
            ${[6, 12, 24, 36].map((m) => `<option value="${m}" ${r.retencao_meses === String(m) ? "selected" : ""}>${td("meses", { n: fmtNumDono(m) })}</option>`).join("")}
          </select>
        </label>
      </div>
      <div class="form-erro" id="int-erro"></div>
      <div class="linha-acoes">
        <button class="btn" id="int-salvar">${td("salvar_integracoes")}</button>
        <button class="btn secondary" id="int-testar">${td("salvar_testar")}</button>
      </div>
      <label class="field" style="max-width:360px">${td("email_teste")} <input type="email" id="int-destino" placeholder="${td("ph_email_teste")}"></label>
    </div>
    <div class="card" id="int-voz"><p class="desc">${td("carregando_voz")}</p></div>`;
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
      await api("/api/dono/integracoes", { method: "POST", body: corpo });
      erro.style.color = "var(--ok)";
      erro.textContent = td("integracoes_salvas");
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
  document.getElementById("int-testar").addEventListener("click", async () => {
    const erro = document.getElementById("int-erro");
    erro.style.color = "var(--text-2)";
    erro.textContent = td("enviando_teste");
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
      await api("/api/dono/integracoes", { method: "POST", body: corpo });
      const r = await api("/api/dono/integracoes/teste", { method: "POST", body: { destino: document.getElementById("int-destino").value.trim() } });
      erro.style.color = "var(--ok)";
      erro.textContent = td("teste_enviado", { destino: r.destino });
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
  await secaoVozPlataforma(document.getElementById("int-voz"));
}



async function secaoVozPlataforma(box) {
  const r = await api("/api/dono/voz/integracao");
  box.innerHTML = `
    <h2 class="icone-titulo">${icone("usuarios")}<span>${td("voz_titulo")}</span></h2>
    <p class="desc">${td("voz_desc")}</p>
    <div class="grid cols-2">
      <label class="field">${td("voz_chave")} <input type="password" id="vi-key" autocomplete="off" placeholder="sk_...">
        ${r.api_key_final ? `<span class="hint">${td("voz_chave_salva", { final: esc(r.api_key_final) })}</span>` : ""}</label>
      <label class="field">${td("voz_segredo")} <input type="password" id="vi-secret" autocomplete="off" placeholder="${r.webhook_configurado ? "••••••" : "wsec_..."}"></label>
      <label class="field">${td("voz_agente")} <input type="text" id="vi-agent" value="${esc(r.agent_id)}"></label>
      <label class="field">${td("voz_telefone")} <input type="text" id="vi-phone" value="${esc(r.phone_number_id)}"></label>
    </div>
    <p class="desc">${td("voz_webhook")} <code>${esc(r.webhook_url)}</code></p>
    <div class="form-erro" id="vi-erro"></div>
    <button class="btn" id="vi-salvar">${td("voz_salvar")}</button>`;
  box.querySelector("#vi-salvar").addEventListener("click", async () => {
    const corpo = { agent_id: box.querySelector("#vi-agent").value, phone_number_id: box.querySelector("#vi-phone").value };
    const k = box.querySelector("#vi-key").value.trim();
    const sgr = box.querySelector("#vi-secret").value.trim();
    if (k) corpo.api_key = k;
    if (sgr) corpo.webhook_secret = sgr;
    const erro = box.querySelector("#vi-erro");
    try {
      await api("/api/dono/voz/integracao", { method: "POST", body: corpo });
      erro.style.color = "var(--ok)";
      erro.textContent = td("voz_salva");
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
}

function abaConfig(el) {
  el.innerHTML = `
    <div class="card" style="max-width:480px">
      <h2 class="icone-titulo">${icone("chave")}<span>${td("cf_titulo")}</span></h2>
      <label class="field">${td("cf_atual")} <input type="password" id="cf-atual"></label>
      <label class="field">${td("cf_nova")} <input type="password" id="cf-nova"></label>
      <div class="form-erro" id="cf-erro"></div>
      <button class="btn" id="cf-salvar">${td("cf_salvar")}</button>
    </div>`;
  document.getElementById("cf-salvar").addEventListener("click", async () => {
    const erro = document.getElementById("cf-erro");
    try {
      await api("/api/dono/senha", {
        method: "POST",
        body: {
          atual: document.getElementById("cf-atual").value,
          nova: document.getElementById("cf-nova").value,
        },
      });
      erro.style.color = "var(--ok)";
      erro.textContent = td("cf_alterada");
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
}

// ------------------------------------------------ boot
async function iniciar() {
  try {
    const s = await api("/api/dono/setup");
    if (s.precisa_setup) return telaSetup();
  } catch (e) { /* segue */ }
  if (!localStorage.getItem("dono_token")) return telaLogin();
  try {
    await desenhar();
  } catch (e) {
    telaLogin();
  }
}
iniciar();
