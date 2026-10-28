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
         ["planos", td("aba_planos")], ["integracoes", td("aba_integracoes")], ["config", td("aba_config")]]
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
  if (abaAtiva === "planos") await abaPlanos(el); // planos e preços (planos.py)
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
    <div class="card" id="int-voz"><p class="desc">${td("carregando_voz")}</p></div>
    <div class="card" id="int-stripe"></div>`;
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
  await secaoStripe(document.getElementById("int-stripe")); // Stripe (planos.py)
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

// ================================================================
// Planos e preços (planos.py): catálogo, premissas, calculadora,
// uso por empresa e chaves do Stripe (seção em Integrações).
// ================================================================
let planosDados = null;
let planosMes = "";

function fmtUSD(n, casas) {
  const v = Number(n);
  if (n === null || n === undefined || n === "" || Number.isNaN(v)) return "";
  const c = casas === undefined ? 2 : casas;
  return v.toLocaleString(localeDono(), { style: "currency", currency: "USD", minimumFractionDigits: c, maximumFractionDigits: c });
}

function fmtPct(n) {
  if (n === null || n === undefined) return "";
  return Number(n).toLocaleString(localeDono(), { maximumFractionDigits: 1 }) + "%";
}

function textoPlanoDono(obj) {
  if (!obj || typeof obj !== "object") return String(obj || "");
  return obj[idiomaDono] || obj.pt || obj.en || "";
}

async function abaPlanos(el) {
  planosDados = await api("/api/dono/planos" + (planosMes ? "?mes=" + encodeURIComponent(planosMes) : ""));
  const d = planosDados;
  const t = d.uso.totais;
  el.innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
        <h2 class="icone-titulo" style="margin:0">${icone("grafico")}<span>${td("pl_resumo")}</span></h2>
        <label class="field" style="margin:0">${td("pl_mes")} <input type="month" id="pl-mes" value="${esc(d.uso.mes)}" style="margin:0"></label>
      </div>
      <div class="metricas" style="margin-top:14px">
        <div class="metrica"><div class="num">${fmtUSD(t.mrr, 0)}</div><div class="rot">${td("pl_mrr")}</div></div>
        <div class="metrica"><div class="num">${fmtUSD(t.custo_variavel, 0)}</div><div class="rot">${td("pl_custo_var_mes")}</div></div>
        <div class="metrica"><div class="num">${fmtUSD(t.custo_fixo, 0)}</div><div class="rot">${td("pl_custo_fixo_mes")}</div></div>
        <div class="metrica"><div class="num">${fmtUSD(t.resultado, 0)}</div><div class="rot">${td("pl_resultado")}</div></div>
        <div class="metrica"><div class="num">${fmtNumDono(t.pagantes)}</div><div class="rot">${td("pl_pagantes")}</div></div>
      </div>
    </div>
    <div class="card">
      <h3 style="margin-top:0">${td("pl_assin_titulo")}</h3>
      <p class="desc">${td("pl_assin_desc")}</p>
      <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="pl-assin" ${d.assinatura_aberta ? "checked" : ""}> ${td("pl_assin_rotulo")}</label>
      <p class="desc"><a href="/site-novo.html" target="_blank" rel="noopener">${td("pl_assin_previa")}</a></p>
    </div>
    <div class="card" id="pl-uso"></div>
    <div class="card" id="pl-calc"></div>
    <div class="card" id="pl-catalogo"></div>`;
  el.querySelector("#pl-mes").addEventListener("change", (ev) => { planosMes = ev.target.value; abaPlanos(el); });
  el.querySelector("#pl-assin").addEventListener("change", async (ev) => {
    if (ev.target.checked && !confirm(td("pl_assin_confirma"))) { ev.target.checked = false; return; }
    try { await api("/api/dono/planos/assinatura", { method: "POST", body: { aberta: ev.target.checked } }); }
    catch (e) { alert(e.message); ev.target.checked = !ev.target.checked; }
  });
  desenharUsoPlanos(el.querySelector("#pl-uso"), el);
  desenharCalculadora(el.querySelector("#pl-calc"), el);
  desenharCatalogo(el.querySelector("#pl-catalogo"), el);
}

function desenharUsoPlanos(box, el) {
  const d = planosDados;
  const corUso = { ok: "ok", near: "warn", over: "err" };
  const opcoesPlano = (atual) => `<option value="">${td("pl_sem_plano")}</option>` +
    d.catalogo.planos.map((p) => `<option value="${esc(p.codigo)}" ${p.codigo === atual ? "selected" : ""}>${esc(textoPlanoDono(p.nome))}</option>`).join("");
  box.innerHTML = `
    <h2 class="icone-titulo">${icone("barras")}<span>${td("pl_uso_titulo")}</span></h2>
    <p class="desc">${td("pl_uso_desc")}</p>
    <div class="tabela-wrap"><table class="tabela">
      <thead><tr><th>${td("pl_empresa")}</th><th>${td("pl_plano")}</th><th class="num">${td("pl_minutos")}</th>
        <th class="num">${td("pl_custo_real")}</th><th class="num">${td("pl_receita")}</th><th class="num">${td("pl_margem")}</th><th></th></tr></thead>
      <tbody>${d.uso.empresas.map((e) => `
        <tr>
          <td><strong>${esc(e.nome)}</strong><br><span class="badge ${STATUS_EMPRESA[e.status] || "tipo"}">${esc(rotuloStatusDono(e.status))}</span>
            ${e.trial_fim && e.status === "teste" ? `<span style="font-size:.78rem;color:var(--muted)"> ${td("pl_teste_ate", { data: fmtDataDono(e.trial_fim + "T12:00:00") })}</span>` : ""}
            ${e.pagamento_status === "falhou" ? `<span class="badge err">${td("pl_pag_falhou")}</span>` : ""}
            ${e.stripe ? `<span class="badge neutral">Stripe</span>` : ""}</td>
          <td>${esc(e.plano_nome ? textoPlanoDono(e.plano_nome) : (e.plano || td("pl_sem_plano")))}${e.plano ? `<br><span style="font-size:.78rem;color:var(--muted)">${td(e.ciclo === "anual" ? "pl_anual" : "pl_mensal")}</span>` : ""}</td>
          <td class="num">${e.uso.ilimitado ? `${fmtNumDono(e.uso.minutos)} / ∞` : `${fmtNumDono(e.uso.minutos)} / ${fmtNumDono(e.uso.limite)}`}
            <br><span class="badge ${corUso[e.uso.status] || "ok"}">${td("pl_st_" + e.uso.status)}</span></td>
          <td class="num">${fmtUSD(e.custo_real)}</td>
          <td class="num">${fmtUSD(e.receita)}</td>
          <td class="num">${fmtUSD(e.margem)}${e.margem_pct !== null ? `<br><span style="font-size:.78rem">${fmtPct(e.margem_pct)}</span>` : ""}</td>
          <td><button class="btn secondary small" data-pl-editar="${e.id}">${td("pl_ajustar")}</button></td>
        </tr>
        <tr class="oculto" id="pl-editar-${e.id}"><td colspan="7">
          <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;align-items:end">
            <label class="field" style="margin:0">${td("pl_plano")} <select data-pl-campo="plano">${opcoesPlano(e.plano)}</select></label>
            <label class="field" style="margin:0">${td("pl_ciclo")} <select data-pl-campo="ciclo">
              <option value="mensal" ${e.ciclo !== "anual" ? "selected" : ""}>${td("pl_mensal")}</option>
              <option value="anual" ${e.ciclo === "anual" ? "selected" : ""}>${td("pl_anual")}</option></select></label>
            <label class="field" style="margin:0">${td("pl_min_extra")} <input type="number" min="0" data-pl-campo="minutos_extra" value="${e.minutos_extra}"></label>
            <label class="field" style="margin:0">${td("pl_num_extra")} <input type="number" min="0" data-pl-campo="numeros_extra" value="${e.numeros_extra}"></label>
            <label class="field" style="margin:0">${td("pl_fim_teste")} <input type="date" data-pl-campo="trial_fim" value="${esc(e.trial_fim)}"></label>
            <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-pl-campo="excedente_permitido" ${e.excedente_permitido ? "checked" : ""}> ${td("pl_excedente")}</label>
            <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-pl-campo="aplicar_modulos"> ${td("pl_aplicar_modulos")}</label>
            <button class="btn small" data-pl-salvar-empresa="${e.id}">${td("salvar")}</button>
          </div>
          <div class="form-erro" id="pl-erro-${e.id}"></div>
        </td></tr>`).join("") || `<tr><td colspan="7">${td("nenhuma_empresa")}</td></tr>`}</tbody>
    </table></div>
    <div class="linha-acoes"><button class="btn secondary small" id="pl-rotina">${td("pl_rodar_rotina")}</button><span class="form-erro" id="pl-rotina-msg"></span></div>`;
  box.querySelectorAll("[data-pl-editar]").forEach((b) => b.addEventListener("click", () => {
    box.querySelector("#pl-editar-" + b.dataset.plEditar).classList.toggle("oculto");
  }));
  box.querySelectorAll("[data-pl-salvar-empresa]").forEach((b) => b.addEventListener("click", async () => {
    const id = b.dataset.plSalvarEmpresa;
    const linha = box.querySelector("#pl-editar-" + id);
    const corpo = {};
    linha.querySelectorAll("[data-pl-campo]").forEach((c) => {
      corpo[c.dataset.plCampo] = c.type === "checkbox" ? c.checked : c.value;
    });
    const erro = box.querySelector("#pl-erro-" + id);
    try {
      await api("/api/dono/planos/empresa/" + id, { method: "POST", body: corpo });
      await abaPlanos(el);
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  }));
  box.querySelector("#pl-rotina").addEventListener("click", async () => {
    const msg = box.querySelector("#pl-rotina-msg");
    try {
      const r = await api("/api/dono/planos/rotina", { method: "POST", body: {} });
      msg.style.color = "var(--ok)";
      msg.textContent = td("pl_rotina_ok", { avisos: fmtNumDono(r.resultado.avisos), suspensas: fmtNumDono(r.resultado.suspensas) });
    } catch (e) {
      msg.style.color = "var(--err)";
      msg.textContent = e.message;
    }
  });
}

const CAMPOS_PREMISSAS = [
  ["custo_min_voz", "0.001"], ["custo_min_tel", "0.001"], ["custo_numero", "0.01"], ["custo_sms", "0.0001"],
  ["custo_a2p", "0.01"], ["horas_manutencao", "0.5"], ["valor_hora", "1"], ["empresas_pagantes", "1"], ["margem_alvo", "1"],
];

function tabelaCustos(c) {
  return `
    <div class="tabela-wrap"><table class="tabela">
      <thead><tr><th>${td("pl_plano")}</th><th class="num">${td("pl_preco")}</th><th class="num">${td("pl_custo_var")}</th>
        <th class="num">${td("pl_custo_fixo")}</th><th class="num">${td("pl_custo_total")}</th><th class="num">${td("pl_margem")}</th>
        <th class="num">${td("pl_margem_pct")}</th><th class="num">${td("pl_equilibrio")}</th><th class="num">${td("pl_sugerido")}</th></tr></thead>
      <tbody>${c.planos.map((p) => `
        <tr><td><strong>${esc(textoPlanoDono(p.nome))}</strong></td>
          <td class="num">${fmtUSD(p.preco_mensal)}</td><td class="num">${fmtUSD(p.custo_variavel)}</td>
          <td class="num">${fmtUSD(p.custo_fixo)}</td><td class="num">${fmtUSD(p.custo_total)}</td>
          <td class="num" style="color:${p.margem < 0 ? "var(--err)" : "inherit"}">${fmtUSD(p.margem)}</td>
          <td class="num">${p.margem_pct === null ? "" : fmtPct(p.margem_pct)}</td>
          <td class="num">${p.empresas_equilibrio === null ? "" : fmtNumDono(p.empresas_equilibrio)}</td>
          <td class="num">${fmtUSD(p.preco_sugerido)}<br><span style="font-size:.78rem;color:var(--muted)">${fmtUSD(p.preco_sugerido_redondo, 0)}</span></td></tr>`).join("")}
      </tbody></table></div>
    <p class="desc" style="font-size:.82rem;margin-top:10px">${td("pl_addons_margem", {
      minuto: fmtUSD(c.addons.minuto_extra.preco), mcusto: fmtUSD(c.addons.minuto_extra.custo, 3), mpct: fmtPct(c.addons.minuto_extra.margem_pct),
      numero: fmtUSD(c.addons.numero_extra.preco), npct: fmtPct(c.addons.numero_extra.margem_pct),
      sms: fmtUSD(c.addons.sms_extra.preco), spct: fmtPct(c.addons.sms_extra.margem_pct) })}</p>
    <p class="desc" style="font-size:.78rem">${td("pl_calc_nota", { fixo: fmtUSD(c.custo_fixo_total, 0) })}</p>`;
}

function desenharCalculadora(box) {
  const d = planosDados;
  box.innerHTML = `
    <h2 class="icone-titulo">${icone("alvo")}<span>${td("pl_calc_titulo")}</span></h2>
    <p class="desc">${td("pl_calc_desc")}</p>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px">
      ${CAMPOS_PREMISSAS.map(([k, passo]) => `<label class="field" style="margin:0">${td("pr_" + k)}
        <input type="number" min="0" step="${passo}" data-premissa="${k}" value="${esc(d.premissas[k])}"></label>`).join("")}
    </div>
    <div class="linha-acoes"><button class="btn" id="pl-salvar-premissas">${td("pl_salvar_premissas")}</button><span class="form-erro" id="pl-premissas-erro"></span></div>
    <div id="pl-tabela-custos" class="mt">${tabelaCustos(d.custos)}</div>`;
  const ler = () => {
    const pr = {};
    box.querySelectorAll("[data-premissa]").forEach((i) => { pr[i.dataset.premissa] = i.value; });
    return pr;
  };
  let espera = null;
  box.querySelectorAll("[data-premissa]").forEach((i) => i.addEventListener("input", () => {
    clearTimeout(espera);
    espera = setTimeout(async () => {
      try {
        const r = await api("/api/dono/planos/calcular", { method: "POST", body: { premissas: ler() } });
        box.querySelector("#pl-tabela-custos").innerHTML = tabelaCustos(r.custos);
      } catch (e) { /* valor incompleto enquanto digita */ }
    }, 350);
  }));
  box.querySelector("#pl-salvar-premissas").addEventListener("click", async () => {
    const erro = box.querySelector("#pl-premissas-erro");
    try {
      const r = await api("/api/dono/planos/premissas", { method: "POST", body: { premissas: ler() } });
      planosDados.premissas = r.premissas;
      planosDados.custos = r.custos;
      box.querySelector("#pl-tabela-custos").innerHTML = tabelaCustos(r.custos);
      erro.style.color = "var(--ok)";
      erro.textContent = td("pl_salvo");
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
}

function htmlPlanoCatalogo(p, i) {
  const idiomas = ["pt", "en", "es"];
  const val = (v) => (v === null || v === undefined ? "" : esc(v));
  return `
    <div class="comp-item" style="margin-top:14px" data-plano-idx="${i}">
      <div class="nome" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px">
        <strong>${esc(textoPlanoDono(p.nome) || p.codigo || td("pl_novo_plano"))}</strong>
        <button class="btn secondary small" data-remover-plano="${i}">${td("pl_remover_plano")}</button>
      </div>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:10px">
        <label class="field" style="margin:0">${td("pl_codigo")} <input type="text" data-c="codigo" value="${val(p.codigo)}"></label>
        ${idiomas.map((l) => `<label class="field" style="margin:0">${td("pl_nome")} (${l.toUpperCase()}) <input type="text" data-c="nome.${l}" value="${val((p.nome || {})[l])}"></label>`).join("")}
        <label class="field" style="margin:0">${td("pl_preco_mensal")} <input type="number" min="0" step="1" data-c="preco_mensal" value="${val(p.preco_mensal)}"></label>
        <label class="field" style="margin:0">${td("pl_preco_anual")} <input type="number" min="0" step="1" data-c="preco_anual" value="${val(p.preco_anual)}" placeholder="${td("pl_anual_padrao")}"></label>
        <label class="field" style="margin:0">${td("pl_minutos_voz")} <input type="number" min="0" data-c="minutos_voz" value="${val(p.minutos_voz)}"></label>
        <label class="field" style="margin:0">${td("pl_sms")} <input type="number" min="0" data-c="sms_mes" value="${val(p.sms_mes)}"></label>
        <label class="field" style="margin:0">${td("pl_gestores_max")} <input type="number" min="0" data-c="gestores_max" value="${val(p.gestores_max)}" placeholder="${td("pl_ilimitado")}"></label>
        <label class="field" style="margin:0">${td("pl_vagas_max")} <input type="number" min="0" data-c="vagas_ativas_max" value="${val(p.vagas_ativas_max)}" placeholder="${td("pl_ilimitado")}"></label>
        <label class="field" style="margin:0">${td("pl_ordem")} <input type="number" data-c="ordem" value="${val(p.ordem)}"></label>
        <label class="field" style="margin:0">${td("pl_modulos")} <input type="text" data-c="modulos" value="${esc((p.modulos || []).join(", "))}"></label>
      </div>
      <div class="linha-acoes" style="margin-top:10px">
        <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-c="numero_exclusivo" ${p.numero_exclusivo ? "checked" : ""}> ${td("pl_numero_exclusivo")}</label>
        <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-c="destaque" ${p.destaque ? "checked" : ""}> ${td("pl_destaque")}</label>
        <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-c="ativo" ${p.ativo !== false ? "checked" : ""}> ${td("pl_ativo")}</label>
      </div>
      <div class="grid cols-2" style="gap:10px;margin-top:10px">
        ${idiomas.map((l) => `<label class="field" style="margin:0">${td("pl_descricao")} (${l.toUpperCase()}) <input type="text" data-c="descricao.${l}" value="${val((p.descricao || {})[l])}"></label>`).join("")}
      </div>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin-top:10px">
        ${idiomas.map((l) => `<label class="field" style="margin:0">${td("pl_recursos")} (${l.toUpperCase()}) <textarea rows="5" data-c="recursos.${l}">${esc(((p.recursos || {})[l] || []).join("\n"))}</textarea></label>`).join("")}
      </div>
    </div>`;
}

function lerCatalogo(box) {
  const planosLidos = [...box.querySelectorAll("[data-plano-idx]")].map((bloco) => {
    const p = { nome: {}, descricao: {}, recursos: {} };
    bloco.querySelectorAll("[data-c]").forEach((c) => {
      const [k, sub] = c.dataset.c.split(".");
      let v = c.type === "checkbox" ? c.checked : c.value;
      if (k === "modulos") v = String(v).split(",").map((x) => x.trim()).filter(Boolean);
      if (k === "recursos") v = String(v).split("\n").map((x) => x.trim()).filter(Boolean);
      if (sub) p[k][sub] = v; else p[k] = v;
    });
    return p;
  });
  return {
    planos: planosLidos,
    addons: {
      minuto_extra: box.querySelector("#pl-ad-minuto").value,
      numero_extra: box.querySelector("#pl-ad-numero").value,
      sms_extra: box.querySelector("#pl-ad-sms").value,
    },
    trial: { dias: box.querySelector("#pl-tr-dias").value, minutos: box.querySelector("#pl-tr-minutos").value },
  };
}

function desenharCatalogo(box, el, catalogo) {
  const cat = catalogo || planosDados.catalogo;
  box.innerHTML = `
    <h2 class="icone-titulo">${icone("camadas")}<span>${td("pl_cat_titulo")}</span></h2>
    <p class="desc">${td("pl_cat_desc")}</p>
    <div id="pl-lista">${cat.planos.map(htmlPlanoCatalogo).join("")}</div>
    <div class="linha-acoes"><button class="btn secondary small" id="pl-add-plano">${td("pl_add_plano")}</button></div>
    <h3 class="mt">${td("pl_addons")}</h3>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px">
      <label class="field" style="margin:0">${td("pl_minuto_extra")} <input type="number" min="0" step="0.01" id="pl-ad-minuto" value="${esc(cat.addons.minuto_extra)}"></label>
      <label class="field" style="margin:0">${td("pl_numero_extra")} <input type="number" min="0" step="0.5" id="pl-ad-numero" value="${esc(cat.addons.numero_extra)}"></label>
      <label class="field" style="margin:0">${td("pl_sms_extra")} <input type="number" min="0" step="0.01" id="pl-ad-sms" value="${esc(cat.addons.sms_extra)}"></label>
      <label class="field" style="margin:0">${td("pl_trial_dias")} <input type="number" min="0" id="pl-tr-dias" value="${esc(cat.trial.dias)}"></label>
      <label class="field" style="margin:0">${td("pl_trial_minutos")} <input type="number" min="0" id="pl-tr-minutos" value="${esc(cat.trial.minutos)}"></label>
    </div>
    <p class="desc" style="font-size:.78rem">${td("pl_excedente_dica")}</p>
    <div class="form-erro" id="pl-cat-erro"></div>
    <div class="linha-acoes">
      <button class="btn" id="pl-salvar-cat">${td("pl_salvar_catalogo")}</button>
      <button class="btn secondary" id="pl-restaurar">${td("pl_restaurar")}</button>
    </div>`;
  box.querySelector("#pl-add-plano").addEventListener("click", () => {
    const atual = lerCatalogo(box);
    atual.planos.push({ codigo: "", nome: {}, descricao: {}, recursos: {}, preco_mensal: "", minutos_voz: 0, sms_mes: 0,
      modulos: ["diagnostico", "onboarding", "agenda", "entrada"], ativo: true, ordem: atual.planos.length + 1 });
    desenharCatalogo(box, el, atual);
  });
  box.querySelectorAll("[data-remover-plano]").forEach((b) => b.addEventListener("click", () => {
    if (!confirm(td("pl_confirmar_remover"))) return;
    const atual = lerCatalogo(box);
    atual.planos.splice(Number(b.dataset.removerPlano), 1);
    desenharCatalogo(box, el, atual);
  }));
  box.querySelector("#pl-salvar-cat").addEventListener("click", async () => {
    const erro = box.querySelector("#pl-cat-erro");
    try {
      await api("/api/dono/planos/catalogo", { method: "POST", body: { catalogo: lerCatalogo(box) } });
      await abaPlanos(el);
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
  box.querySelector("#pl-restaurar").addEventListener("click", async () => {
    if (!confirm(td("pl_confirmar_restaurar"))) return;
    await api("/api/dono/planos/restaurar", { method: "POST", body: {} });
    await abaPlanos(el);
  });
}

async function secaoStripe(box) {
  if (!box) return;
  const [s, d] = await Promise.all([api("/api/dono/planos/stripe"), api("/api/dono/planos")]);
  const chaves = [];
  d.catalogo.planos.filter((p) => Number(p.preco_mensal) > 0).forEach((p) => {
    chaves.push([p.codigo + "_mensal", textoPlanoDono(p.nome) + " · " + td("pl_mensal")]);
    chaves.push([p.codigo + "_anual", textoPlanoDono(p.nome) + " · " + td("pl_anual")]);
  });
  box.innerHTML = `
    <h2 class="icone-titulo">${icone("cadeado")}<span>${td("st_titulo")}</span></h2>
    <p class="desc">${td("st_desc")}
      ${s.configurado ? `<span class="badge ok">${td(s.modo_teste ? "st_modo_teste" : "st_modo_real", { final: esc(s.chave_final) })}</span>` : `<span class="badge warn">${td("nao_configurado")}</span>`}</p>
    <div class="grid cols-2">
      <label class="field">${td("st_chave")} <input type="password" id="st-chave" autocomplete="off" placeholder="${s.configurado ? td("ph_trocar") : "sk_live_..."}"></label>
      <label class="field">${td("st_segredo")} <input type="password" id="st-segredo" autocomplete="off" placeholder="${s.webhook_configurado ? "••••••" : "whsec_..."}"></label>
      <label class="field">${td("st_dono_email")} <span class="hint">${td("st_dono_email_dica")}</span><input type="email" id="st-email" value="${esc(s.dono_email)}"></label>
    </div>
    <p class="desc">${td("st_webhook")} <code>${esc(s.webhook_url)}</code></p>
    <p class="desc" style="font-size:.82rem">${td("st_eventos")}</p>
    <h3>${td("st_precos")}</h3>
    <p class="desc" style="font-size:.82rem">${td("st_precos_dica")}</p>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px">
      ${chaves.map(([k, rot]) => `<label class="field" style="margin:0">${esc(rot)} <input type="text" data-preco="${esc(k)}" value="${esc(s.precos[k] || "")}" placeholder="price_..."></label>`).join("")}
    </div>
    <div class="form-erro" id="st-erro"></div>
    <button class="btn mt" id="st-salvar">${td("st_salvar")}</button>`;
  box.querySelector("#st-salvar").addEventListener("click", async () => {
    const corpo = { dono_email: box.querySelector("#st-email").value.trim(), precos: {} };
    box.querySelectorAll("[data-preco]").forEach((i) => { corpo.precos[i.dataset.preco] = i.value.trim(); });
    const k = box.querySelector("#st-chave").value.trim();
    const sg = box.querySelector("#st-segredo").value.trim();
    if (k) corpo.stripe_secret_key = k;
    if (sg) corpo.stripe_webhook_secret = sg;
    const erro = box.querySelector("#st-erro");
    try {
      await api("/api/dono/planos/stripe", { method: "POST", body: corpo });
      erro.style.color = "var(--ok)";
      erro.textContent = td("st_salvo");
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
}
// ================================================================ fim planos e preços

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
