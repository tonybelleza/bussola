/* =====================================================================
   Painel do Dono do software: contas, troubleshooting e billing.
   Acesso exclusivo do proprietário (Tony), acima dos gestores.
   ===================================================================== */

const app = document.getElementById("app");
let abaAtiva = "visao";

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

// ------------------------------------------------ painel
async function desenhar() {
  document.getElementById("btn-sair").classList.remove("oculto");
  app.innerHTML = `
    <div class="tabs">
      ${[["visao", "Visão geral e saúde"], ["contas", "Contas"],
         ["billing", "Clientes e cobrança"], ["config", "Configurações"]]
        .map(([id, rot]) => `<button class="tab ${abaAtiva === id ? "ativa" : ""}" data-aba="${id}">${rot}</button>`).join("")}
    </div>
    <div id="conteudo"><p class="desc">Carregando…</p></div>`;
  app.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => { abaAtiva = t.dataset.aba; desenhar(); })
  );
  const el = document.getElementById("conteudo");
  if (abaAtiva === "visao") await abaVisao(el);
  if (abaAtiva === "contas") await abaContas(el);
  if (abaAtiva === "billing") await abaBilling(el);
  if (abaAtiva === "config") abaConfig(el);
}

async function abaVisao(el) {
  const r = await api("/api/dono/visao");
  el.innerHTML = `
    <div class="metricas">
      <div class="metrica"><div class="num">${r.totais.gestores}</div><div class="rot">Contas de gestor</div></div>
      <div class="metrica"><div class="num">${r.totais.candidatos}</div><div class="rot">Pessoas avaliadas</div></div>
      <div class="metrica"><div class="num">${r.totais.internos}</div><div class="rot">Colaboradores internos</div></div>
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
          <tr><td>Backups recentes</td><td class="num">${r.sistema.backups.length ? r.sistema.backups.map(esc).join("<br>") : "—"}</td></tr>
        </tbody></table></div>
      </div>
      <div class="card">
        <h2 class="icone-titulo">${icone("documento")}<span>Uso por cliente (local)</span></h2>
        <div class="tabela-wrap"><table class="tabela">
          <thead><tr><th>Local</th><th class="num">Pessoas</th><th class="num">Internos</th></tr></thead>
          <tbody>${r.locais.map((l) => `
            <tr><td><strong>${esc(l.local)}</strong></td>
            <td class="num">${l.candidatos}</td><td class="num">${l.internos}</td></tr>`).join("")
            || '<tr><td colspan="3" style="color:var(--muted)">Nenhum uso ainda.</td></tr>'}</tbody>
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
      <p class="desc">Entre em qualquer conta para dar suporte (troubleshooting) ou redefina a senha de quem perdeu o acesso. Cada acesso seu abre o painel exatamente como o gestor o vê.</p>
      <div class="tabela-wrap"><table class="tabela">
        <thead><tr><th>Nome</th><th>Login</th><th>Local</th><th class="num">Perfil</th>
          <th class="num">Candidatos visíveis</th><th></th></tr></thead>
        <tbody>${r.gestores.map((g) => `
          <tr>
            <td><strong>${esc(g.nome)}</strong><br><span style="color:var(--muted);font-size:.78rem">${esc(g.email || "sem e-mail")}</span></td>
            <td>${esc(g.login)}</td>
            <td>${g.local ? esc(g.local) : '<span style="color:var(--muted)">todos</span>'}</td>
            <td class="num">${g.admin ? '<span class="badge neutral">Admin</span>' : '<span class="badge tipo">Gestor</span>'}</td>
            <td class="num">${g.candidatos_visiveis}</td>
            <td class="num">
              <button class="btn secondary small" data-entrar="${g.id}">Entrar na conta</button>
              <button class="btn ghost small" data-senha="${g.id}">Redefinir senha</button>
            </td>
          </tr>`).join("") || '<tr><td colspan="6" style="color:var(--muted)">Nenhuma conta criada ainda.</td></tr>'}</tbody>
      </table></div>
    </div>`;
  el.querySelectorAll("[data-entrar]").forEach((b) =>
    b.addEventListener("click", async () => {
      const r2 = await api("/api/dono/entrar-como", {
        method: "POST", body: { gestor_id: Number(b.dataset.entrar) },
      });
      localStorage.setItem("gestor_token", r2.token);
      localStorage.setItem("gestor_info", JSON.stringify({
        nome: r2.nome, login: r2.login, local: r2.local, admin: r2.admin,
      }));
      window.open("gestor.html", "_blank");
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
      } catch (e) {
        alert(e.message);
      }
    })
  );
}

async function abaBilling(el) {
  const r = await api("/api/dono/billing");
  const cores = { ativo: "ok", teste: "neutral", inadimplente: "err", cancelado: "tipo" };
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("relatorio")}<span>Clientes e cobrança</span></h2>
      <p class="desc">Cada local/instituição que usa o sistema aparece aqui. Registre plano, valor e situação de cada cliente. (A cobrança automática pode ser plugada depois; por enquanto este é o seu controle central.)</p>
      ${r.clientes.map((c, i) => `
        <div class="comp-item">
          <div class="nome">${esc(c.local)}
            <span class="badge ${cores[c.status] || "tipo"}">${esc(c.status)}</span></div>
          <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px">
            <input type="text" id="bl-plano-${i}" value="${esc(c.plano)}" placeholder="Plano (ex.: mensal)" style="margin:0">
            <input type="text" id="bl-valor-${i}" value="${esc(c.valor)}" placeholder="Valor (ex.: R$ 490/mês)" style="margin:0">
            <select id="bl-status-${i}" style="margin:0">
              ${["ativo", "teste", "inadimplente", "cancelado"].map((s) =>
                `<option value="${s}" ${c.status === s ? "selected" : ""}>${s}</option>`).join("")}
            </select>
            <input type="text" id="bl-notas-${i}" value="${esc(c.notas)}" placeholder="Notas" style="margin:0">
            <button class="btn secondary small" data-salvar-billing="${i}" data-local="${esc(c.local)}">Salvar</button>
          </div>
        </div>`).join("") || '<p class="desc">Nenhum cliente ainda. Os locais aparecem aqui conforme gestores e candidatos são criados.</p>'}
    </div>`;
  el.querySelectorAll("[data-salvar-billing]").forEach((b) =>
    b.addEventListener("click", async () => {
      const i = b.dataset.salvarBilling;
      await api("/api/dono/billing", {
        method: "POST",
        body: {
          local: b.dataset.local,
          plano: document.getElementById("bl-plano-" + i).value,
          valor: document.getElementById("bl-valor-" + i).value,
          status: document.getElementById("bl-status-" + i).value,
          notas: document.getElementById("bl-notas-" + i).value,
        },
      });
      b.textContent = "Salvo ✓";
      setTimeout(() => { b.textContent = "Salvar"; }, 1500);
    })
  );
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
