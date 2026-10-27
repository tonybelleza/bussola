/* =====================================================================
   Painel do Dono do software: contas, troubleshooting e billing.
   Acesso exclusivo do proprietário (Tony), acima dos gestores.
   ===================================================================== */

const app = document.getElementById("app");
let abaAtiva = "empresas";

async function api(caminho, opcoes = {}) {
  const headers = { "Content-Type": "application/json" };
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
    throw new Error(dados.erro || "Sessão expirada");
  }
  if (!resp.ok) throw new Error(dados.erro || "Erro de comunicação");
  return dados;
}

document.getElementById("btn-sair").addEventListener("click", () => {
  localStorage.removeItem("dono_token");
  telaLogin();
});

// ------------------------------------------------ acesso
function telaSetup() {
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:460px;margin:48px auto">
      <h2 class="icone-titulo">${icone("chave")}<span>Configuração do dono</span></h2>
      <p class="desc">Primeiro acesso ao painel do proprietário do software. Defina a senha mestra (mínimo 8 caracteres). Ela é independente das contas de gestor.</p>
      <label class="field">Senha do dono <input type="password" id="dn-senha" autocomplete="new-password"></label>
      <label class="field">Confirmar senha <input type="password" id="dn-senha2" autocomplete="new-password"></label>
      <div class="form-erro" id="dn-erro"></div>
      <button class="btn block" id="dn-criar">Criar acesso do dono</button>
    </div>`;
  document.getElementById("dn-criar").addEventListener("click", async () => {
    const erro = document.getElementById("dn-erro");
    const senha = document.getElementById("dn-senha").value;
    if (senha !== document.getElementById("dn-senha2").value) {
      erro.textContent = "As senhas não conferem.";
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
  document.getElementById("btn-sair").classList.add("oculto");
  app.innerHTML = `
    <div class="card" style="max-width:420px;margin:48px auto">
      <h2 class="icone-titulo">${icone("cadeado")}<span>Acesso do dono</span></h2>
      <p class="desc">Área exclusiva do proprietário do software.</p>
      <label class="field">Senha mestra
        <input type="password" id="lg-senha" autocomplete="current-password">
      </label>
      <div class="form-erro" id="lg-erro"></div>
      <button class="btn block" id="lg-entrar">Entrar</button>
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
  document.getElementById("btn-sair").classList.remove("oculto");
  app.innerHTML = `
    <div class="tabs">
      ${[["empresas", "Empresas"], ["visao", "Visão geral e saúde"], ["contas", "Todas as contas"],
         ["integracoes", "Integrações"], ["config", "Configurações"]]
        .map(([id, rot]) => `<button class="tab ${abaAtiva === id ? "ativa" : ""}" data-aba="${id}">${rot}</button>`).join("")}
    </div>
    <div id="conteudo"><p class="desc">Carregando…</p></div>`;
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
      <div class="metrica"><div class="num">${emp.empresas.length}</div><div class="rot">Empresas</div></div>
      <div class="metrica"><div class="num">${r.totais.gestores}</div><div class="rot">Contas de gestor</div></div>
      <div class="metrica"><div class="num">${r.totais.candidatos}</div><div class="rot">Pessoas avaliadas</div></div>
      <div class="metrica"><div class="num">${r.totais.vagas}</div><div class="rot">Vagas criadas</div></div>
      <div class="metrica"><div class="num">${r.totais.avaliacoes_completas}</div><div class="rot">Avaliações completas</div></div>
    </div>
    <div class="grid cols-2">
      <div class="card">
        <h2 class="icone-titulo">${icone("engrenagem")}<span>Saúde do sistema</span></h2>
        <div class="tabela-wrap"><table class="tabela"><tbody>
          <tr><td>Versão</td><td class="num"><strong>${esc(r.sistema.versao)}</strong></td></tr>
          <tr><td>Python</td><td class="num">${esc(r.sistema.python)}</td></tr>
          <tr><td>Tamanho do banco</td><td class="num">${r.sistema.banco_mb} MB</td></tr>
          <tr><td>IA (Anthropic)</td><td class="num">${r.sistema.ia_configurada ? '<span class="badge ok">Configurada</span>' : '<span class="badge warn">Não configurada</span>'}</td></tr>
          <tr><td>E-mail (SMTP)</td><td class="num">${r.sistema.smtp_configurado ? '<span class="badge ok">Configurado</span>' : '<span class="badge warn">Não configurado</span>'}</td></tr>
          <tr><td>Backups recentes</td><td class="num">${r.sistema.backups.length ? r.sistema.backups.map(esc).join("<br>") : "nenhum"}</td></tr>
        </tbody></table></div>
      </div>
      <div class="card">
        <h2 class="icone-titulo">${icone("documento")}<span>Uso por empresa</span></h2>
        <div class="tabela-wrap"><table class="tabela">
          <thead><tr><th>Empresa</th><th class="num">Candidatos</th><th class="num">Vagas abertas</th><th class="num">Ligações</th></tr></thead>
          <tbody>${emp.empresas.map((e) => `
            <tr><td><strong>${esc(e.nome)}</strong></td><td class="num">${e.candidatos}</td>
            <td class="num">${e.vagas_abertas}</td><td class="num">${e.ligacoes_voz}</td></tr>`).join("")
            || '<tr><td colspan="4" style="color:var(--muted)">Nenhuma empresa ainda.</td></tr>'}</tbody>
        </table></div>
      </div>
    </div>
    <div class="card">
      <h2 class="icone-titulo">${icone("bloco")}<span>Log do servidor (últimas linhas)</span></h2>
      <pre style="font-size:.72rem;color:var(--text-2);white-space:pre-wrap;max-height:260px;overflow-y:auto;background:rgba(7,11,20,.5);padding:14px;border-radius:12px">${esc(r.sistema.log || "Sem registros.")}</pre>
    </div>`;
}

async function abaContas(el) {
  const r = await api("/api/dono/visao");
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("usuarios")}<span>Todas as contas de gestor</span></h2>
      <p class="desc">Entre em qualquer conta para dar suporte ou redefina a senha de quem perdeu o acesso. Cada acesso seu abre o painel exatamente como o gestor o vê, só com os dados da empresa dele.</p>
      <div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>Nome</th><th>Empresa</th><th>Login</th><th>Local</th><th class="num">Perfil</th>
          <th class="num">Candidatos visíveis</th><th></th></tr></thead>
        <tbody>${r.gestores.map((g) => `
          <tr>
            <td><strong>${esc(g.nome)}</strong><br><span style="color:var(--muted);font-size:.78rem">${esc(g.email || "sem e-mail")}</span></td>
            <td>${esc(g.empresa || "")}</td>
            <td>${esc(g.login)}${g.aprovado ? "" : ' <span class="badge warn">inativo</span>'}</td>
            <td>${g.local ? esc(g.local) : '<span style="color:var(--muted)">empresa toda</span>'}</td>
            <td class="num">${g.admin ? '<span class="badge neutral">Admin</span>' : '<span class="badge tipo">Gestor</span>'}</td>
            <td class="num">${g.candidatos_visiveis}</td>
            <td class="num">
              <button class="btn secondary small" data-entrar="${g.id}">Entrar na conta</button>
              <button class="btn ghost small" data-senha="${g.id}">Redefinir senha</button>
            </td>
          </tr>`).join("") || '<tr><td colspan="7" style="color:var(--muted)">Nenhuma conta criada ainda.</td></tr>'}</tbody>
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
      <h2 class="icone-titulo">${icone("camadas")}<span>Empresas</span></h2>
      <p class="desc">Cada empresa é uma subconta isolada: só enxerga os próprios gestores, cargos, vagas, candidatos e ligações. Só você vê todas.</p>
      ${r.empresas.map((e) => `
        <div class="comp-item" style="margin-top:14px">
          <div class="nome" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px">
            <span><strong>${esc(e.nome)}</strong> <span class="badge ${STATUS_EMPRESA[e.status] || "tipo"}">${esc(e.status)}</span></span>
            <span style="color:var(--muted);font-size:.8rem">${esc(location.origin)}/vagas?e=${esc(e.slug)}</span>
          </div>
          <div class="metricas" style="margin:10px 0">
            <div class="metrica"><div class="num">${e.gestores}</div><div class="rot">Gestores</div></div>
            <div class="metrica"><div class="num">${e.cargos}</div><div class="rot">Cargos</div></div>
            <div class="metrica"><div class="num">${e.vagas_abertas}</div><div class="rot">Vagas abertas</div></div>
            <div class="metrica"><div class="num">${e.candidatos}</div><div class="rot">Candidatos</div></div>
            <div class="metrica"><div class="num">${e.ligacoes_voz}</div><div class="rot">Ligações de voz</div></div>
          </div>
          <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px">
            <select data-campo="status" data-id="${e.id}" style="margin:0">
              ${["ativa", "teste", "suspensa", "cancelada"].map((s) => `<option value="${s}" ${e.status === s ? "selected" : ""}>${s}</option>`).join("")}
            </select>
            <input type="text" data-campo="plano" data-id="${e.id}" value="${esc(e.plano)}" placeholder="Plano (ex.: mensal)" style="margin:0">
            <input type="text" data-campo="valor" data-id="${e.id}" value="${esc(e.valor)}" placeholder="Valor" style="margin:0">
            <input type="text" data-campo="notas" data-id="${e.id}" value="${esc(e.notas)}" placeholder="Notas" style="margin:0">
            <input type="text" data-campo="slug" data-id="${e.id}" value="${esc(e.slug)}" placeholder="link (ex.: bhs-ct)" title="Link público da empresa" style="margin:0">
          </div>
          <div class="linha-acoes" style="margin-top:10px">
            ${mods.map(([m, rot]) => `<label class="badge ${e.modulos.includes(m) ? "ok" : ""}" style="cursor:pointer">
              <input type="checkbox" data-modulo="${m}" data-id="${e.id}" ${e.modulos.includes(m) ? "checked" : ""}> ${esc(rot)}</label>`).join("")}
            <button class="btn small" data-salvar-empresa="${e.id}">Salvar</button>
            <button class="btn secondary small" data-ver-gestores="${e.id}">Gestores e acesso</button>
          </div>
          <div id="gestores-empresa-${e.id}"></div>
        </div>`).join("") || '<p class="desc">Nenhuma empresa ainda.</p>'}
    </div>
    <div class="card">
      <h2 class="icone-titulo">${icone("chave")}<span>Nova empresa</span></h2>
      <div class="grid cols-2">
        <label class="field">Nome da empresa <input type="text" id="ne-nome" placeholder="Belleza's Home Services CT"></label>
        <label class="field">Situação <select id="ne-status"><option value="ativa">ativa</option><option value="teste">teste</option></select></label>
      </div>
      <p class="desc">Primeiro administrador da empresa (opcional agora, dá para criar depois):</p>
      <div class="grid cols-2">
        <label class="field">Nome <input type="text" id="ne-a-nome"></label>
        <label class="field">E-mail <input type="email" id="ne-a-email"></label>
        <label class="field">Login <input type="text" id="ne-a-login" autocomplete="off"></label>
        <label class="field">Senha (mín. 8) <input type="password" id="ne-a-senha" autocomplete="new-password"></label>
      </div>
      <div class="form-erro" id="ne-erro"></div>
      <button class="btn" id="ne-criar">Criar empresa</button>
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
      b.textContent = "Salvo ✓";
      setTimeout(() => abaEmpresas(el), 800);
    } catch (e) { alert(e.message); }
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
      <thead><tr><th>Nome</th><th>Login</th><th>Local</th><th class="num">Perfil</th><th></th></tr></thead>
      <tbody>${r.gestores_lista.map((g) => `
        <tr><td><strong>${esc(g.nome)}</strong><br><span style="color:var(--muted);font-size:.78rem">${esc(g.email || "sem e-mail")}</span></td>
          <td>${esc(g.login)}${g.aprovado ? "" : ' <span class="badge warn">pendente</span>'}</td>
          <td>${g.local ? esc(g.local) : '<span style="color:var(--muted)">empresa toda</span>'}</td>
          <td class="num">${g.admin ? '<span class="badge neutral">Admin</span>' : '<span class="badge tipo">Gestor</span>'}</td>
          <td class="num"><button class="btn secondary small" data-entrar="${g.id}">Entrar na conta</button>
            <button class="btn ghost small" data-senha="${g.id}">Redefinir senha</button></td></tr>`).join("")
        || '<tr><td colspan="5" style="color:var(--muted)">Nenhum gestor ainda.</td></tr>'}</tbody>
    </table></div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-top:10px">
      <input type="text" id="ng-nome-${id}" placeholder="Nome" style="margin:0">
      <input type="email" id="ng-email-${id}" placeholder="E-mail" style="margin:0">
      <input type="text" id="ng-login-${id}" placeholder="Login" style="margin:0" autocomplete="off">
      <input type="password" id="ng-senha-${id}" placeholder="Senha (mín. 8)" style="margin:0" autocomplete="new-password">
      <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" id="ng-admin-${id}"> Admin</label>
      <button class="btn small" id="ng-criar-${id}">Adicionar gestor</button>
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
      const nova = prompt("Nova senha para esta conta (mínimo 6 caracteres):");
      if (!nova) return;
      try {
        await api("/api/dono/gestor-senha", {
          method: "POST", body: { gestor_id: Number(b.dataset.senha), nova },
        });
        alert("Senha redefinida.");
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
      <h2 class="icone-titulo">${icone("engrenagem")}<span>Integrações da plataforma (valem para todas as empresas)</span></h2>
      <p class="desc">Estes são os únicos recursos do sistema que dependem de serviços externos. Tudo o mais funciona sem custo. Sem estas credenciais, os botões de IA e as notificações por e-mail apenas ficam indisponíveis.</p>
      <div class="grid cols-2">
        <div>
          <h3>Análise de currículo por IA</h3>
          <p class="desc" style="font-size:.82rem">Usa a API da Anthropic (Claude Haiku 4.5, rápido e econômico). Crie uma chave em console.anthropic.com. Custo aproximado: US$ 25 a cada mil currículos analisados. Status:
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
      <label class="field" style="max-width:360px">E-mail para o teste <input type="email" id="int-destino" placeholder="voce@seudominio.com"></label>
    </div>
    <div class="card" id="int-voz"><p class="desc">Carregando integração de voz…</p></div>`;
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
      await api("/api/dono/integracoes", { method: "POST", body: corpo });
      const r = await api("/api/dono/integracoes/teste", { method: "POST", body: { destino: document.getElementById("int-destino").value.trim() } });
      erro.style.color = "var(--ok)";
      erro.textContent = "E-mail de teste enviado para " + r.destino + ". Verifique a caixa de entrada (e o spam).";
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
    <h2 class="icone-titulo">${icone("usuarios")}<span>Triagem por voz (ElevenLabs)</span></h2>
    <p class="desc">Conta da plataforma usada pela Francisca em todas as empresas que tiverem o módulo Triagem por Voz.</p>
    <div class="grid cols-2">
      <label class="field">Chave da API <input type="password" id="vi-key" autocomplete="off" placeholder="sk_...">
        ${r.api_key_final ? `<span class="hint">Chave salva terminando em ${esc(r.api_key_final)}. Deixe vazio para manter.</span>` : ""}</label>
      <label class="field">Segredo do webhook <input type="password" id="vi-secret" autocomplete="off" placeholder="${r.webhook_configurado ? "••••••" : "wsec_..."}"></label>
      <label class="field">ID da agente <input type="text" id="vi-agent" value="${esc(r.agent_id)}"></label>
      <label class="field">ID do número de telefone <input type="text" id="vi-phone" value="${esc(r.phone_number_id)}"></label>
    </div>
    <p class="desc">Endereço do webhook para colar no ElevenLabs: <code>${esc(r.webhook_url)}</code></p>
    <div class="form-erro" id="vi-erro"></div>
    <button class="btn" id="vi-salvar">Salvar integração de voz</button>`;
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
      erro.textContent = "Integração de voz salva.";
    } catch (e) {
      erro.style.color = "var(--err)";
      erro.textContent = e.message;
    }
  });
}

function abaConfig(el) {
  el.innerHTML = `
    <div class="card" style="max-width:480px">
      <h2 class="icone-titulo">${icone("chave")}<span>Alterar senha do dono</span></h2>
      <label class="field">Senha atual <input type="password" id="cf-atual"></label>
      <label class="field">Nova senha (mín. 8 caracteres) <input type="password" id="cf-nova"></label>
      <div class="form-erro" id="cf-erro"></div>
      <button class="btn" id="cf-salvar">Alterar senha</button>
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
      erro.textContent = "Senha alterada.";
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
