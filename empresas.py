"""
Empresas (subcontas) da Bússola.

Cada empresa é um cliente isolado: gestores, candidatos, vagas, cargos (com
competências, roteiro de entrevista e teste), sessões de diagnóstico e regras da
triagem por voz pertencem a uma empresa. Só o dono do software (painel /dono)
enxerga e administra todas.

Dentro de uma empresa, o "local" continua existindo como unidade: um gestor com
local definido vê só os candidatos daquela unidade; o administrador da empresa e
gestores sem local veem a empresa inteira. Nada atravessa de uma empresa para
outra.
"""
import json
import re
import secrets
import unicodedata

srv = None  # módulo do servidor, injetado por ligar()

STATUS_EMPRESA = ("ativa", "teste", "suspensa", "cancelada")

# módulos agora são liberados por empresa (antes eram por gestor)
TABELAS_COM_EMPRESA = ("gestores", "candidatos", "vagas", "cargos", "sessoes_diagnostico")


def ligar(modulo_servidor):
    global srv
    srv = modulo_servidor


def gerar_slug(texto, existentes=()):
    t = unicodedata.normalize("NFD", texto or "")
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn").lower()
    t = re.sub(r"['’`]", "", t)  # Belleza's vira bellezas
    base = re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40] or "empresa"
    slug, n = base, 2
    while slug in existentes:
        slug = "%s-%d" % (base, n)
        n += 1
    return slug


# ------------------------------------------------------------ banco

def init_empresas(c):
    """Cria a tabela, as colunas empresa_id e migra os dados de antes das
    empresas: cada "local" usado vira uma empresa, e o que não tinha local vai
    para a empresa "Principal". Roda uma vez (só quando ainda não há empresas)."""
    c.execute(
        "CREATE TABLE IF NOT EXISTS empresas ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " nome TEXT NOT NULL,"
        " slug TEXT UNIQUE NOT NULL,"
        " status TEXT NOT NULL DEFAULT 'ativa',"
        " modulos TEXT NOT NULL DEFAULT '[]',"
        " plano TEXT DEFAULT '',"
        " valor TEXT DEFAULT '',"
        " notas TEXT DEFAULT '',"
        " criada_em TEXT DEFAULT (datetime('now')))"
    )
    for tabela in TABELAS_COM_EMPRESA:
        colunas = {r[1] for r in c.execute("PRAGMA table_info(%s)" % tabela).fetchall()}
        if "empresa_id" not in colunas:
            c.execute("ALTER TABLE %s ADD COLUMN empresa_id INTEGER REFERENCES empresas(id)" % tabela)
    if c.execute("SELECT 1 FROM empresas LIMIT 1").fetchone():
        return
    tem_dados = any(
        c.execute("SELECT 1 FROM %s LIMIT 1" % t).fetchone()
        for t in ("gestores", "candidatos", "vagas", "sessoes_diagnostico")
    )
    if not tem_dados:
        return  # banco novo: a primeira empresa nasce na configuração inicial

    locais = {}
    for tabela in ("gestores", "candidatos", "vagas", "sessoes_diagnostico"):
        for r in c.execute("SELECT DISTINCT local FROM %s" % tabela).fetchall():
            nome = (r[0] or "").strip()
            if nome:
                locais.setdefault(nome.lower(), nome)
    slugs = set()
    ids = {}
    for chave, nome in sorted(locais.items()):
        slug = gerar_slug(nome, slugs)
        slugs.add(slug)
        ids[chave] = c.execute("INSERT INTO empresas (nome, slug) VALUES (?,?)", (nome, slug)).lastrowid
    principal = c.execute(
        "INSERT INTO empresas (nome, slug) VALUES (?,?)", ("Principal", gerar_slug("principal", slugs))
    ).lastrowid

    def empresa_de(local):
        return ids.get((local or "").strip().lower(), principal)

    # módulos que estavam ligados por gestor passam para a empresa dele
    modulos = {}
    for tabela in ("gestores", "candidatos", "vagas", "sessoes_diagnostico"):
        colunas = {r[1] for r in c.execute("PRAGMA table_info(%s)" % tabela).fetchall()}
        extra = ", modulos" if (tabela == "gestores" and "modulos" in colunas) else ""
        for r in c.execute("SELECT id, local%s FROM %s" % (extra, tabela)).fetchall():
            eid = empresa_de(r[1])
            c.execute("UPDATE %s SET empresa_id=? WHERE id=?" % tabela, (eid, r[0]))
            if extra:
                try:
                    modulos.setdefault(eid, set()).update(json.loads(r[2] or "[]"))
                except ValueError:
                    pass
    for eid, mods in modulos.items():
        c.execute("UPDATE empresas SET modulos=? WHERE id=?", (json.dumps(sorted(mods)), eid))

    # cargo pertence à empresa das vagas que o usam; os demais vão para a Principal
    for r in c.execute("SELECT id FROM cargos").fetchall():
        dono = c.execute(
            "SELECT empresa_id FROM vagas WHERE cargo_id=? AND empresa_id IS NOT NULL"
            " UNION SELECT empresa_id FROM candidatos WHERE cargo_desejado_id=? AND empresa_id IS NOT NULL"
            " LIMIT 1", (r[0], r[0]),
        ).fetchone()
        c.execute("UPDATE cargos SET empresa_id=? WHERE id=?", (dono[0] if dono else principal, r[0]))

    # cobrança que era por local passa para a empresa
    colunas = {r[1] for r in c.execute("PRAGMA table_info(billing)").fetchall()}
    if "local" in colunas:
        for r in c.execute("SELECT local, plano, valor, status, notas FROM billing").fetchall():
            status = {"ativo": "ativa", "teste": "teste", "inadimplente": "suspensa",
                      "cancelado": "cancelada"}.get(r[3] or "", "ativa")
            c.execute(
                "UPDATE empresas SET plano=?, valor=?, notas=?, status=? WHERE id=?",
                (r[1] or "", r[2] or "", r[4] or "", status, empresa_de(r[0])),
            )

    # regras da triagem por voz que eram por local passam para a empresa
    for r in c.execute("SELECT local, dados FROM voz_config").fetchall():
        if (r[0] or "").strip():
            c.execute(
                "INSERT OR REPLACE INTO voz_config (local, dados) VALUES (?,?)",
                ("empresa:%d" % empresa_de(r[0]), r[1]),
            )


def criar_empresa(conn, nome, status="ativa"):
    slugs = {r[0] for r in conn.execute("SELECT slug FROM empresas").fetchall()}
    slug = gerar_slug(nome, slugs)
    eid = conn.execute(
        "INSERT INTO empresas (nome, slug, status) VALUES (?,?,?)",
        (nome.strip(), slug, status if status in STATUS_EMPRESA else "ativa"),
    ).lastrowid
    return eid, slug


def por_slug(conn, slug):
    if not slug:
        return None
    return conn.execute(
        "SELECT * FROM empresas WHERE slug=? AND status IN ('ativa','teste')", (slug.strip().lower(),)
    ).fetchone()


def modulos(empresa_row):
    try:
        m = json.loads((empresa_row["modulos"] if empresa_row else "[]") or "[]")
        return m if isinstance(m, list) else []
    except (ValueError, TypeError):
        return []


# ------------------------------------------------------------ regras de acesso

def mesma_empresa(gestor, registro):
    """True quando o registro (candidato, vaga, cargo, sessão...) é da empresa do gestor."""
    eid = gestor["empresa_id"]
    return eid is not None and registro is not None and registro["empresa_id"] == eid


def ve_local(gestor, local):
    """Dentro da empresa: admin e gestor sem local veem todas as unidades; gestor
    com local vê só a própria unidade."""
    if gestor["is_admin"]:
        return True
    proprio = (gestor["local"] or "").strip().lower()
    return not proprio or (local or "").strip().lower() == proprio


def ve_candidato(gestor, cand):
    return mesma_empresa(gestor, cand) and ve_local(gestor, cand["local"])


# ------------------------------------------------------------ painel do dono

def _resp(h, status, dados):
    h._json(status, dados)
    return True


def resumo_empresa(conn, e):
    def n(sql):
        return conn.execute(sql, (e["id"],)).fetchone()[0]

    return {
        "id": e["id"], "nome": e["nome"], "slug": e["slug"], "status": e["status"],
        "modulos": modulos(e), "plano": e["plano"], "valor": e["valor"], "notas": e["notas"],
        "criada_em": e["criada_em"],
        "gestores": n("SELECT COUNT(*) FROM gestores WHERE empresa_id=?"),
        "candidatos": n("SELECT COUNT(*) FROM candidatos WHERE empresa_id=?"),
        "vagas_abertas": n("SELECT COUNT(*) FROM vagas WHERE empresa_id=? AND status='aberta'"),
        "cargos": n("SELECT COUNT(*) FROM cargos WHERE empresa_id=?"),
        "avaliacoes_completas": n("SELECT COUNT(*) FROM candidatos WHERE empresa_id=? AND notificado_completo=1"),
        "ligacoes_voz": n(
            "SELECT COUNT(*) FROM voz_chamadas vc JOIN candidatos c ON c.id=vc.candidato_id WHERE c.empresa_id=?"
        ),
    }


def rotear_dono(h, method, path, conn):
    """Rotas /api/dono/empresas* (o guarda do dono já rodou no server.py)."""
    if not path.startswith("/api/dono/empresa"):
        return None

    if method == "GET" and path == "/api/dono/empresas":
        empresas = [resumo_empresa(conn, e) for e in conn.execute("SELECT * FROM empresas ORDER BY nome").fetchall()]
        return _resp(h, 200, {"empresas": empresas, "modulos_disponiveis": srv.MODULOS_DISPONIVEIS})

    if method == "POST" and path == "/api/dono/empresas":
        d = h._body()
        nome = (d.get("nome") or "").strip()
        if not nome:
            return _resp(h, 400, {"erro": "Informe o nome da empresa"})
        eid, slug = criar_empresa(conn, nome, d.get("status") or "ativa")
        admin = d.get("admin") or {}
        if admin.get("login"):
            erro = _criar_gestor(conn, eid, admin, is_admin=1)
            if erro:
                conn.rollback()
                return _resp(h, 400, {"erro": erro})
        conn.commit()
        return _resp(h, 200, {"ok": True, "id": eid, "slug": slug})

    m = re.match(r"^/api/dono/empresa/(\d+)$", path)
    if m:
        e = conn.execute("SELECT * FROM empresas WHERE id=?", (int(m.group(1)),)).fetchone()
        if not e:
            return _resp(h, 404, {"erro": "Empresa não encontrada"})
        if method == "GET":
            gestores = [
                {"id": g["id"], "nome": g["nome"], "login": g["login"], "email": g["email"],
                 "local": g["local"], "admin": bool(g["is_admin"]), "aprovado": bool(g["aprovado"]),
                 "criado_em": g["criado_em"]}
                for g in conn.execute("SELECT * FROM gestores WHERE empresa_id=? ORDER BY nome", (e["id"],)).fetchall()
            ]
            return _resp(h, 200, {"empresa": resumo_empresa(conn, e), "gestores_lista": gestores})
        if method == "POST":
            d = h._body()
            campos, valores = [], []
            if "nome" in d and (d.get("nome") or "").strip():
                campos.append("nome=?")
                valores.append(d["nome"].strip())
            if d.get("status") in STATUS_EMPRESA:
                campos.append("status=?")
                valores.append(d["status"])
            for chave in ("plano", "valor", "notas"):
                if chave in d:
                    campos.append("%s=?" % chave)
                    valores.append((d.get(chave) or "").strip())
            if "slug" in d and (d.get("slug") or "").strip():
                novo = gerar_slug(d["slug"])
                if novo != e["slug"]:
                    if conn.execute("SELECT 1 FROM empresas WHERE slug=? AND id!=?", (novo, e["id"])).fetchone():
                        return _resp(h, 400, {"erro": "Este link já é usado por outra empresa"})
                    campos.append("slug=?")
                    valores.append(novo)
            if "modulos" in d:
                mods = sorted({x for x in (d.get("modulos") or []) if x in srv.MODULOS_DISPONIVEIS})
                campos.append("modulos=?")
                valores.append(json.dumps(mods))
            if campos:
                conn.execute("UPDATE empresas SET %s WHERE id=?" % ", ".join(campos), valores + [e["id"]])
                if d.get("status") in ("suspensa", "cancelada"):
                    # derruba as sessões dos gestores da empresa suspensa
                    conn.execute(
                        "DELETE FROM sessoes_gestor WHERE gestor_id IN (SELECT id FROM gestores WHERE empresa_id=?)",
                        (e["id"],),
                    )
                conn.commit()
            return _resp(h, 200, {"ok": True})

    m = re.match(r"^/api/dono/empresa/(\d+)/gestor$", path)
    if m and method == "POST":
        e = conn.execute("SELECT * FROM empresas WHERE id=?", (int(m.group(1)),)).fetchone()
        if not e:
            return _resp(h, 404, {"erro": "Empresa não encontrada"})
        d = h._body()
        erro = _criar_gestor(conn, e["id"], d, is_admin=1 if d.get("admin") else 0)
        if erro:
            return _resp(h, 400, {"erro": erro})
        conn.commit()
        return _resp(h, 200, {"ok": True})

    return _resp(h, 404, {"erro": "Rota não encontrada"})


def _criar_gestor(conn, empresa_id, d, is_admin):
    nome = (d.get("nome") or "").strip()
    login = (d.get("login") or "").strip().lower()
    senha = d.get("senha") or ""
    if not nome or not login:
        return "Nome e login do gestor são obrigatórios"
    if len(senha) < 8:
        return "A senha do gestor deve ter ao menos 8 caracteres"
    if conn.execute("SELECT 1 FROM gestores WHERE login=?", (login,)).fetchone():
        return "Este login já existe"
    conn.execute(
        "INSERT INTO gestores (login, senha, nome, email, local, is_admin, aprovado, empresa_id)"
        " VALUES (?,?,?,?,?,?,1,?)",
        (login, srv.hash_senha(senha), nome, (d.get("email") or "").strip(),
         (d.get("local") or "").strip(), is_admin, empresa_id),
    )
    return None


def token_temporario():
    return secrets.token_urlsafe(24)
