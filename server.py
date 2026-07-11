#!/usr/bin/env python3
"""
Sistema de RH — DISC + B.A.S.E. + Mapeamento de Cargos e Matriz de Gaps
Servidor sem dependências externas (Python 3 stdlib + SQLite).

Uso:  python3 server.py [porta]   (padrão: 8080)
"""
import base64
import hashlib
import html as _html
import json
import os
import re
import secrets
import sqlite3
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
DB_PATH = os.path.join(BASE_DIR, "rh.db")

SENHA_GESTOR_PADRAO = "gestor123"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------- banco

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


MODULOS_DISPONIVEIS = {"diagnostico": "Diagnóstico de Competências"}

# arquivos de referência do módulo Diagnóstico (servidos só a gestores com o módulo)
ARQUIVOS_DIAGNOSTICO = {
    "cronograma-p2.pptx": "Cronograma do projecto (P2, v2)",
    "instrumento-levantamento-funcional.docx": "Instrumento de Levantamento Funcional (A, B e C)",
    "estatuto-organico-inss.pdf": "Estatuto Orgânico do INSS (DP-232-21)",
    "regulamento-inss-gti.pdf": "Regulamento dos Serviços Centrais e Locais do INSS (Deliberação 5/2022)",
}


def modulos_do_gestor(gestor):
    try:
        m = json.loads(gestor["modulos"] or "[]")
        return m if isinstance(m, list) else []
    except Exception:  # noqa: BLE001
        return []


def _sha256_hex(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def hash_senha(senha):
    """Gera hash PBKDF2-HMAC-SHA256 com sal aleatório: pbkdf2$iteracoes$sal$hash."""
    iteracoes = 200000
    sal = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(sal), iteracoes)
    return "pbkdf2$%d$%s$%s" % (iteracoes, sal, dk.hex())


def senha_confere(senha, armazenado):
    """Confere a senha, aceitando o hash antigo (SHA-256 puro) e o novo (PBKDF2)."""
    if not armazenado:
        return False
    if armazenado.startswith("pbkdf2$"):
        try:
            _, it, sal, esperado = armazenado.split("$", 3)
            dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"),
                                     bytes.fromhex(sal), int(it))
            return secrets.compare_digest(dk.hex(), esperado)
        except (ValueError, TypeError):
            return False
    return secrets.compare_digest(_sha256_hex(senha), armazenado)


def migrar_hash_se_preciso(senha, armazenado):
    """Devolve um hash PBKDF2 novo se o guardado ainda for o formato antigo."""
    if armazenado and not armazenado.startswith("pbkdf2$"):
        return hash_senha(senha)
    return None


def init_db():
    conn = db()
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS gestores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome TEXT NOT NULL,
            email TEXT DEFAULT '',
            local TEXT DEFAULT '',
            is_admin INTEGER NOT NULL DEFAULT 0,
            criado_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sessoes_gestor (
            token TEXT PRIMARY KEY,
            gestor_id INTEGER REFERENCES gestores(id) ON DELETE CASCADE,
            criado_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS cargos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            area TEXT DEFAULT '',
            nivel TEXT DEFAULT '',
            descricao TEXT DEFAULT '',
            disc_alvo TEXT DEFAULT '',
            base_alvo TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS competencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cargo_id INTEGER NOT NULL REFERENCES cargos(id) ON DELETE CASCADE,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'tecnica',
            nivel_requerido INTEGER NOT NULL DEFAULT 3,
            obrigatoria INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS candidatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            local TEXT DEFAULT '',
            linkedin TEXT DEFAULT '',
            instagram TEXT DEFAULT '',
            cargo_atual TEXT DEFAULT '',
            cargo_desejado_id INTEGER REFERENCES cargos(id) ON DELETE SET NULL,
            curriculo_arquivo TEXT DEFAULT '',
            criado_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS resultados_teste (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,
            tipo TEXT NOT NULL,
            payload TEXT NOT NULL,
            criado_em TEXT DEFAULT (datetime('now')),
            UNIQUE(candidato_id, tipo)
        );
        CREATE TABLE IF NOT EXISTS autoavaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,
            competencia_id INTEGER NOT NULL REFERENCES competencias(id) ON DELETE CASCADE,
            nivel_atual INTEGER NOT NULL DEFAULT 0,
            UNIQUE(candidato_id, competencia_id)
        );
        CREATE TABLE IF NOT EXISTS vagas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cargo_id INTEGER NOT NULL REFERENCES cargos(id) ON DELETE CASCADE,
            titulo TEXT NOT NULL,
            local TEXT DEFAULT '',
            pais TEXT DEFAULT '',
            descricao TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'aberta',
            criado_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS candidaturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,
            vaga_id INTEGER NOT NULL REFERENCES vagas(id) ON DELETE CASCADE,
            etapa TEXT NOT NULL DEFAULT 'inscrito',
            motivo_reprovacao TEXT DEFAULT '',
            criado_em TEXT DEFAULT (datetime('now')),
            atualizado_em TEXT DEFAULT (datetime('now')),
            UNIQUE(candidato_id, vaga_id)
        );
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,
            tipo TEXT NOT NULL,
            texto TEXT NOT NULL,
            autor TEXT DEFAULT 'sistema',
            criado_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS perguntas_entrevista (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cargo_id INTEGER NOT NULL REFERENCES cargos(id) ON DELETE CASCADE,
            texto TEXT NOT NULL,
            ordem INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS entrevistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,
            cargo_id INTEGER NOT NULL REFERENCES cargos(id) ON DELETE CASCADE,
            gestor_nome TEXT DEFAULT '',
            payload TEXT NOT NULL,
            media REAL NOT NULL DEFAULT 0,
            criado_em TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cargo_id INTEGER NOT NULL REFERENCES cargos(id) ON DELETE CASCADE,
            pergunta TEXT NOT NULL,
            opcoes TEXT NOT NULL,
            correta INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS resultados_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,
            cargo_id INTEGER NOT NULL REFERENCES cargos(id) ON DELETE CASCADE,
            acertos INTEGER NOT NULL DEFAULT 0,
            total INTEGER NOT NULL DEFAULT 0,
            payload TEXT DEFAULT '{}',
            criado_em TEXT DEFAULT (datetime('now')),
            UNIQUE(candidato_id, cargo_id)
        );
        """
    )
    # migrações para bancos criados em versões anteriores
    colunas_cand = {r[1] for r in c.execute("PRAGMA table_info(candidatos)").fetchall()}
    if "local" not in colunas_cand:
        c.execute("ALTER TABLE candidatos ADD COLUMN local TEXT DEFAULT ''")
    if "linkedin" not in colunas_cand:
        c.execute("ALTER TABLE candidatos ADD COLUMN linkedin TEXT DEFAULT ''")
        c.execute("ALTER TABLE candidatos ADD COLUMN instagram TEXT DEFAULT ''")
    if "analise_ia" not in colunas_cand:
        c.execute("ALTER TABLE candidatos ADD COLUMN analise_ia TEXT DEFAULT ''")
    if "notificado_completo" not in colunas_cand:
        c.execute("ALTER TABLE candidatos ADD COLUMN notificado_completo INTEGER DEFAULT 0")
    if "tags" not in colunas_cand:
        c.execute("ALTER TABLE candidatos ADD COLUMN tags TEXT DEFAULT '[]'")
        c.execute("ALTER TABLE candidatos ADD COLUMN lembrete_enviado INTEGER DEFAULT 0")
        c.execute("ALTER TABLE candidatos ADD COLUMN consentimento_em TEXT DEFAULT ''")
        c.execute("ALTER TABLE candidatos ADD COLUMN anonimizado INTEGER DEFAULT 0")
    if "tipo" not in colunas_cand:
        c.execute("ALTER TABLE candidatos ADD COLUMN tipo TEXT DEFAULT 'externo'")
    if "telefone" not in colunas_cand:
        c.execute("ALTER TABLE candidatos ADD COLUMN telefone TEXT DEFAULT ''")
    if "funcao" not in colunas_cand:
        c.execute("ALTER TABLE candidatos ADD COLUMN funcao TEXT DEFAULT ''")
    colunas_vagas = {r[1] for r in c.execute("PRAGMA table_info(vagas)").fetchall()}
    if "pais" not in colunas_vagas:
        c.execute("ALTER TABLE vagas ADD COLUMN pais TEXT DEFAULT ''")
    colunas_gest = {r[1] for r in c.execute("PRAGMA table_info(gestores)").fetchall()}
    if "modulos" not in colunas_gest:
        c.execute("ALTER TABLE gestores ADD COLUMN modulos TEXT DEFAULT '[]'")
    if "reset_token" not in colunas_gest:
        c.execute("ALTER TABLE gestores ADD COLUMN reset_token TEXT DEFAULT ''")
        c.execute("ALTER TABLE gestores ADD COLUMN reset_expira TEXT DEFAULT ''")
    c.execute(
        "CREATE TABLE IF NOT EXISTS sessoes_diagnostico ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " gestor_id INTEGER NOT NULL REFERENCES gestores(id) ON DELETE CASCADE,"
        " colaborador TEXT NOT NULL,"
        " cargo TEXT DEFAULT '',"
        " unidade TEXT DEFAULT '',"
        " status TEXT NOT NULL DEFAULT 'rascunho',"
        " dados TEXT DEFAULT '{}',"
        " local TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " atualizado_em TEXT DEFAULT (datetime('now')))"
    )
    colunas_diag = {r[1] for r in c.execute("PRAGMA table_info(sessoes_diagnostico)").fetchall()}
    if "local" not in colunas_diag:
        c.execute("ALTER TABLE sessoes_diagnostico ADD COLUMN local TEXT DEFAULT ''")
        # herda o local do gestor que criou cada sessão existente
        c.execute(
            "UPDATE sessoes_diagnostico SET local = COALESCE("
            "(SELECT local FROM gestores WHERE gestores.id = sessoes_diagnostico.gestor_id), '')"
        )
    c.execute(
        "CREATE TABLE IF NOT EXISTS sessoes_dono ("
        " token TEXT PRIMARY KEY, criado_em TEXT DEFAULT (datetime('now')))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS billing ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " local TEXT UNIQUE NOT NULL,"
        " plano TEXT DEFAULT '',"
        " valor TEXT DEFAULT '',"
        " status TEXT DEFAULT 'ativo',"
        " notas TEXT DEFAULT '',"
        " atualizado_em TEXT DEFAULT (datetime('now')))"
    )
    colunas_gest = {r[1] for r in c.execute("PRAGMA table_info(gestores)").fetchall()}
    if "email" not in colunas_gest:
        c.execute("ALTER TABLE gestores ADD COLUMN email TEXT DEFAULT ''")
    colunas_cargo = {r[1] for r in c.execute("PRAGMA table_info(cargos)").fetchall()}
    if "disc_alvo" not in colunas_cargo:
        c.execute("ALTER TABLE cargos ADD COLUMN disc_alvo TEXT DEFAULT ''")
        c.execute("ALTER TABLE cargos ADD COLUMN base_alvo TEXT DEFAULT ''")
        # aplica perfis desejados aos cargos de exemplo já existentes
        for nome, disc, base in [
            ("Analista de Sistemas Júnior", "C", "E"),
            ("Analista de Sistemas Pleno", "C", "E"),
            ("Analista de Sistemas Sênior", "C", "E"),
            ("Gestor de TI", "D", "B"),
        ]:
            c.execute(
                "UPDATE cargos SET disc_alvo=?, base_alvo=? WHERE nome=?",
                (disc, base, nome),
            )
    colunas_sessao = {r[1] for r in c.execute("PRAGMA table_info(sessoes_gestor)").fetchall()}
    if "gestor_id" not in colunas_sessao:
        c.execute("DROP TABLE sessoes_gestor")
        c.execute(
            "CREATE TABLE sessoes_gestor ("
            " token TEXT PRIMARY KEY,"
            " gestor_id INTEGER REFERENCES gestores(id) ON DELETE CASCADE,"
            " criado_em TEXT DEFAULT (datetime('now')))"
        )
    # remove a conta padrão de versões anteriores — o primeiro acesso agora
    # exige o cadastro real do administrador (tela de configuração inicial)
    c.execute(
        "DELETE FROM gestores WHERE login='admin' AND nome='Administrador' AND senha=?",
        (_sha256_hex(SENHA_GESTOR_PADRAO),),
    )
    if not c.execute("SELECT 1 FROM cargos LIMIT 1").fetchone():
        seed_cargos(c)
    conn.commit()
    conn.close()


def seed_cargos(c):
    """Cargos de exemplo da área de GTI (baseados na descrição do projeto)."""
    cargos = [
        {
            "nome": "Analista de Sistemas Júnior",
            "area": "GTI",
            "nivel": "Júnior",
            "disc_alvo": "C",
            "base_alvo": "E",
            "descricao": "Apoio no desenvolvimento e manutenção de sistemas, sob supervisão.",
            "competencias": [
                ("Lógica de programação", "tecnica", 3, 1),
                ("Banco de dados SQL", "tecnica", 2, 1),
                ("Formação em TI (graduação ou técnico)", "formacao", 3, 1),
                ("Comunicação com a equipe", "relacional", 3, 0),
                ("Experiência em desenvolvimento (1+ ano)", "experiencia", 2, 0),
            ],
        },
        {
            "nome": "Analista de Sistemas Pleno",
            "area": "GTI",
            "nivel": "Pleno",
            "disc_alvo": "C",
            "base_alvo": "E",
            "descricao": "Desenvolvimento e análise de sistemas com autonomia em demandas de média complexidade.",
            "competencias": [
                ("Desenvolvimento Java", "tecnica", 4, 1),
                ("Banco de dados SQL", "tecnica", 4, 1),
                ("Análise de requisitos", "tecnica", 3, 1),
                ("Formação em TI (graduação)", "formacao", 4, 1),
                ("Comunicação com usuários e stakeholders", "relacional", 3, 0),
                ("Trabalho em equipe", "relacional", 4, 0),
                ("Experiência em desenvolvimento (3+ anos)", "experiencia", 3, 1),
            ],
        },
        {
            "nome": "Analista de Sistemas Sênior",
            "area": "GTI",
            "nivel": "Sênior",
            "disc_alvo": "C",
            "base_alvo": "E",
            "descricao": "Responsável por demandas de alta complexidade, arquitetura de soluções e apoio técnico à equipe.",
            "competencias": [
                ("Certificação Java", "formacao", 4, 1),
                ("Desenvolvimento Java avançado", "tecnica", 5, 1),
                ("Arquitetura de software", "tecnica", 4, 1),
                ("Banco de dados SQL avançado", "tecnica", 4, 1),
                ("Análise de sistemas complexos", "tecnica", 5, 1),
                ("Comunicação com stakeholders", "relacional", 4, 1),
                ("Mentoria de equipe", "relacional", 4, 0),
                ("Gestão de demandas de alta complexidade", "tecnica", 4, 1),
                ("Experiência em desenvolvimento (5+ anos)", "experiencia", 5, 1),
            ],
        },
        {
            "nome": "Gestor de TI",
            "area": "GTI",
            "nivel": "Gestão",
            "disc_alvo": "D",
            "base_alvo": "B",
            "descricao": "Gestão da equipe e das entregas da área de tecnologia da informação.",
            "competencias": [
                ("Gestão de pessoas", "relacional", 5, 1),
                ("Gestão de projetos", "tecnica", 4, 1),
                ("Planejamento estratégico de TI", "tecnica", 4, 1),
                ("Formação em gestão (pós/MBA)", "formacao", 3, 0),
                ("Comunicação executiva", "relacional", 4, 1),
                ("Negociação e resolução de conflitos", "relacional", 4, 1),
                ("Experiência em liderança (3+ anos)", "experiencia", 4, 1),
            ],
        },
    ]
    for cargo in cargos:
        c.execute(
            "INSERT INTO cargos (nome, area, nivel, descricao, disc_alvo, base_alvo)"
            " VALUES (?,?,?,?,?,?)",
            (cargo["nome"], cargo["area"], cargo["nivel"], cargo["descricao"],
             cargo.get("disc_alvo", ""), cargo.get("base_alvo", "")),
        )
        cid = c.lastrowid
        for nome, tipo, req, obrig in cargo["competencias"]:
            c.execute(
                "INSERT INTO competencias (cargo_id, nome, tipo, nivel_requerido, obrigatoria)"
                " VALUES (?,?,?,?,?)",
                (cid, nome, tipo, req, obrig),
            )


# ------------------------------------------------------------ regras

def cargo_com_competencias(conn, cargo_id):
    cargo = conn.execute("SELECT * FROM cargos WHERE id=?", (cargo_id,)).fetchone()
    if not cargo:
        return None
    comps = conn.execute(
        "SELECT * FROM competencias WHERE cargo_id=? ORDER BY obrigatoria DESC, tipo, nome",
        (cargo_id,),
    ).fetchall()
    return {**dict(cargo), "competencias": [dict(x) for x in comps]}


RECOMENDACAO_POR_TIPO = {
    "formacao": "Buscar a formação/certificação: {nome}",
    "tecnica": "Realizar capacitação técnica em: {nome}",
    "relacional": "Desenvolvimento comportamental em: {nome} (mentoria, feedback, treinamento)",
    "experiencia": "Adquirir experiência prática em: {nome} (projetos, job rotation, sombra)",
}


def matriz_gaps(conn, candidato_id, cargo_id):
    """Cruza a autoavaliação do candidato com as competências exigidas pelo cargo."""
    cargo = cargo_com_competencias(conn, cargo_id)
    if not cargo:
        return None
    respostas = {
        r["competencia_id"]: r["nivel_atual"]
        for r in conn.execute(
            "SELECT competencia_id, nivel_atual FROM autoavaliacoes WHERE candidato_id=?",
            (candidato_id,),
        ).fetchall()
    }
    itens, total_req, total_atendido = [], 0, 0
    obrigatorias_pendentes = 0
    for comp in cargo["competencias"]:
        atual = respostas.get(comp["id"])
        respondida = atual is not None
        atual = atual or 0
        gap = max(0, comp["nivel_requerido"] - atual)
        total_req += comp["nivel_requerido"]
        total_atendido += min(atual, comp["nivel_requerido"])
        if comp["obrigatoria"] and gap > 0:
            obrigatorias_pendentes += 1
        item = {
            "competencia_id": comp["id"],
            "nome": comp["nome"],
            "tipo": comp["tipo"],
            "obrigatoria": bool(comp["obrigatoria"]),
            "nivel_requerido": comp["nivel_requerido"],
            "nivel_atual": atual,
            "respondida": respondida,
            "gap": gap,
        }
        if gap > 0:
            item["recomendacao"] = RECOMENDACAO_POR_TIPO.get(
                comp["tipo"], "Desenvolver: {nome}"
            ).format(nome=comp["nome"])
        itens.append(item)
    aderencia = round(100 * total_atendido / total_req) if total_req else 0
    plano = sorted(
        [i for i in itens if i["gap"] > 0],
        key=lambda i: (not i["obrigatoria"], -i["gap"]),
    )
    if aderencia >= 90 and obrigatorias_pendentes == 0:
        status = "apto"
    elif aderencia >= 60:
        status = "desenvolvimento"
    else:
        status = "gap_alto"
    return {
        "cargo": {k: cargo[k] for k in ("id", "nome", "area", "nivel", "descricao")},
        "itens": itens,
        "aderencia": aderencia,
        "obrigatorias_pendentes": obrigatorias_pendentes,
        "status": status,
        "plano_desenvolvimento": plano,
        "respondeu_autoavaliacao": len(respostas) > 0,
    }


# pesos do match geral candidato × cargo (renormalizados sobre o que existir).
# Com apenas os três primeiros disponíveis, equivale a 50/25/25.
PESOS_MATCH = {
    "competencias": 0.30,
    "disc": 0.15,
    "base": 0.15,
    "conhecimento": 0.20,
    "entrevista": 0.20,
}

def _num_valido(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _para_int(v, padrao=None):
    """Converte para int sem estourar (entradas do usuário chegam como texto)."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return padrao


def calcular_disc_payload(respostas):
    """Recalcula o DISC no servidor a partir das respostas cruas [{mais, menos}].
    Não confia em nota vinda do cliente: garante que o match nunca quebre nem
    seja fraudado. Retorna None se não houver respostas válidas."""
    letras = ["D", "I", "S", "C"]
    mais = {k: 0 for k in letras}
    menos = {k: 0 for k in letras}
    n = 0
    for r in (respostas or []):
        if not isinstance(r, dict):
            continue
        m, mn = r.get("mais"), r.get("menos")
        if m in mais and mn in menos:
            mais[m] += 1
            menos[mn] += 1
            n += 1
    if n == 0:
        return None
    scores, pct = {}, {}
    for k in letras:
        scores[k] = mais[k] - menos[k]
        pct[k] = int(((scores[k] + n) / (2 * n)) * 100 + 0.5)
    ordem = sorted(letras, key=lambda k: -scores[k])
    return {"mais": mais, "menos": menos, "scores": scores, "pct": pct,
            "dominante": ordem[0], "secundario": ordem[1]}


def calcular_base_payload(rodadas):
    """Recalcula o B.A.S.E. no servidor a partir das ordens cruas
    [['B','A','S','E'], ...]. Cada rodada precisa conter exatamente as 4 letras."""
    letras = ["B", "A", "S", "E"]
    pontos = {k: 0 for k in letras}
    primeiros = {k: 0 for k in letras}
    n = 0
    for ordem in (rodadas or []):
        if not isinstance(ordem, list) or sorted(ordem) != sorted(letras):
            continue
        for i, p in enumerate(ordem):
            pontos[p] += 4 - i
        primeiros[ordem[0]] += 1
        n += 1
    if n == 0:
        return None
    pct = {}
    for k in letras:
        pct[k] = int(((pontos[k] - n) / (3 * n)) * 100 + 0.5)
    ordem = sorted(letras, key=lambda k: (-pontos[k], -primeiros[k]))
    return {"pontos": pontos, "primeiros": primeiros, "pct": pct, "ordem": ordem,
            "codigo": "".join(ordem), "dominante": ordem[0], "secundario": ordem[1]}


def sanitizar_payload_teste(tipo, payload):
    """Defesa para chamadas diretas à API que mandam a nota pronta: aceita só
    números de 0 a 100 nas chaves conhecidas, para o match jamais quebrar."""
    if not isinstance(payload, dict):
        return None
    letras = ["D", "I", "S", "C"] if tipo == "disc" else ["B", "A", "S", "E"]
    pct_in = payload.get("pct")
    if not isinstance(pct_in, dict):
        return None
    pct = {}
    for k in letras:
        v = pct_in.get(k)
        if not _num_valido(v):
            return None
        pct[k] = max(0, min(100, int(v)))
    ordem = sorted(letras, key=lambda k: -pct[k])
    saida = {"pct": pct, "dominante": ordem[0], "secundario": ordem[1]}
    if tipo == "base":
        saida["ordem"] = ordem
        saida["codigo"] = "".join(ordem)
    return saida


ETAPAS_PIPELINE = ["inscrito", "avaliacoes", "entrevista", "proposta", "contratado", "reprovado"]

NOMES_ETAPAS = {
    "inscrito": "Inscrito",
    "avaliacoes": "Avaliações",
    "entrevista": "Entrevista",
    "proposta": "Proposta",
    "contratado": "Contratado",
    "reprovado": "Reprovado",
}


def registrar_evento(conn, candidato_id, tipo, texto, autor="sistema"):
    conn.execute(
        "INSERT INTO eventos (candidato_id, tipo, texto, autor) VALUES (?,?,?,?)",
        (candidato_id, tipo, texto, autor),
    )


def config_get(conn, chave):
    r = conn.execute("SELECT valor FROM config WHERE chave=?", (chave,)).fetchone()
    return r["valor"] if r else ""


def config_set(conn, chave, valor):
    conn.execute(
        "INSERT INTO config (chave, valor) VALUES (?,?)"
        " ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
        (chave, valor),
    )


def montar_email_html(assunto, corpo_texto):
    """Envolve o texto do e-mail num layout moderno com a marca Bússola.
    Linhas que são só um link viram botão; parágrafos separados por linha em
    branco. O 'herói' do topo (ícone + título + cor) muda conforme o tipo de
    e-mail, inferido pelo assunto. Animações são progressivas: onde o cliente
    não suporta (Gmail, Outlook), o e-mail continua bonito e estático."""
    HEROIS = [
        ("bem-vind", "🧭", "Bem-vindo(a) à sua avaliação", "#3B67CA"),
        ("confirmad", "🧭", "Inscrição confirmada", "#3B67CA"),
        ("inscri", "🧭", "Inscrição confirmada", "#3B67CA"),
        ("falta pouco", "⏳", "Falta pouco para concluir", "#C79A3E"),
        ("lembr", "⏳", "Um lembrete rápido", "#C79A3E"),
        ("completa", "✅", "Avaliação concluída", "#2E9E6A"),
        ("novo candidato", "👤", "Novo candidato", "#3B67CA"),
        ("senha", "🔒", "Redefinição de senha", "#5E7086"),
        ("teste", "✉️", "E-mail de teste", "#3B67CA"),
        ("etapa", "📌", "Atualização do processo", "#3B67CA"),
    ]
    alvo = (assunto or "").lower()
    icone_h, titulo_h, cor_h = "🧭", "", "#3B67CA"
    for chave, ic, tit, cor in HEROIS:
        if chave in alvo:
            icone_h, titulo_h, cor_h = ic, tit, cor
            break

    blocos = []
    paragrafo = []

    def fecha():
        if paragrafo:
            blocos.append(
                '<p style="margin:0 0 16px;font-size:15px;line-height:1.65;color:#2b3648">'
                + "<br>".join(_html.escape(x) for x in paragrafo) + "</p>"
            )
            paragrafo.clear()

    for linha in corpo_texto.split("\n"):
        s = linha.strip()
        if s.startswith("http://") or s.startswith("https://"):
            fecha()
            blocos.append(
                '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 18px">'
                '<tr><td class="cta" style="border-radius:12px;'
                'background:linear-gradient(135deg,#3258AB,#3B67CA 60%%,#5B84DB);'
                'box-shadow:0 6px 18px rgba(50,88,171,.35)">'
                '<a href="%s" style="display:inline-block;padding:14px 34px;font-size:15px;'
                'font-weight:700;color:#ffffff;text-decoration:none;border-radius:12px">Acessar &#8594;</a>'
                '</td></tr></table>'
                '<p style="margin:0 0 16px;font-size:12px;color:#8a97a8">'
                'Se o botão não funcionar, copie e cole no navegador:<br>'
                '<a href="%s" style="color:#3258AB;word-break:break-all">%s</a></p>'
                % (_html.escape(s, quote=True), _html.escape(s, quote=True), _html.escape(s))
            )
        elif s == "":
            fecha()
        else:
            paragrafo.append(linha)
    fecha()
    corpo_html = "\n".join(blocos)

    hero_html = ""
    if titulo_h:
        hero_html = (
            '<tr><td style="padding:26px 34px 0;text-align:center">'
            '<div class="hero-icone" style="display:inline-block;width:64px;height:64px;'
            'line-height:64px;border-radius:50%;font-size:30px;'
            'background:' + cor_h + '1f;border:1px solid ' + cor_h + '33">' + icone_h + '</div>'
            '<div style="font-size:19px;font-weight:700;color:#101B37;margin-top:14px">'
            + _html.escape(titulo_h) + '</div></td></tr>'
        )

    estilo = (
        '<style>'
        '@keyframes brilho{0%{background-position:-260px 0}100%{background-position:260px 0}}'
        '@keyframes pulso{0%,100%{box-shadow:0 6px 18px rgba(50,88,171,.35)}'
        '50%{box-shadow:0 8px 26px rgba(91,132,219,.6)}}'
        '@keyframes flutua{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}'
        '.faixa{background:linear-gradient(90deg,#3258AB,#5B84DB,#9BB9DD,#5B84DB,#3258AB);'
        'background-size:260px 100%;animation:brilho 2.6s linear infinite}'
        '.cta{animation:pulso 2.6s ease-in-out infinite}'
        '.hero-icone{animation:flutua 3s ease-in-out infinite}'
        '</style>'
    )
    modelo = (
        '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        + estilo +
        '</head>'
        '<body style="margin:0;padding:0;background:#eef1f6;'
        '-webkit-font-smoothing:antialiased;font-family:Arial,Helvetica,sans-serif">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f6">'
        '<tr><td align="center" style="padding:28px 12px">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="max-width:560px;background:#ffffff;border-radius:18px;overflow:hidden;'
        'box-shadow:0 10px 34px rgba(16,27,55,.10)">'
        # cabeçalho navy com selo da bússola
        '<tr><td style="background:linear-gradient(135deg,#101B37,#182B54);padding:26px 34px">'
        '<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
        '<td style="width:40px;height:40px;background:#3B67CA;border-radius:10px;'
        'text-align:center;font-size:22px;line-height:40px">🧭</td>'
        '<td style="padding-left:14px">'
        '<div style="font-size:21px;font-weight:700;color:#ffffff;letter-spacing:.3px">Bússola</div>'
        '<div style="font-size:11px;color:#9BB9DD;letter-spacing:2px;text-transform:uppercase">'
        'Recrutamento e Seleção</div></td></tr></table></td></tr>'
        # faixa animada
        '<tr><td class="faixa" style="height:4px;font-size:0;line-height:0;'
        'background:linear-gradient(90deg,#3258AB,#5B84DB,#9BB9DD)">&nbsp;</td></tr>'
        # herói opcional
        '__HERO__'
        # corpo
        '<tr><td style="padding:26px 34px 12px">__CORPO__</td></tr>'
        # rodapé
        '<tr><td style="padding:18px 34px 30px;border-top:1px solid #eef1f6">'
        '<div style="font-size:12px;color:#8a97a8;line-height:1.5">'
        'Bússola · metodologia B.A.S.E. e curadoria Tony Belleza<br>'
        '<a href="https://rh.tonybelleza.com" style="color:#5E7086;text-decoration:none">rh.tonybelleza.com</a>'
        '</div></td></tr>'
        '</table></td></tr></table></body></html>'
    )
    return modelo.replace("__HERO__", hero_html).replace("__CORPO__", corpo_html)


def enviar_email(conn, para, assunto, corpo):
    """Envia e-mail via SMTP configurado (HTML com a marca + texto). Retorna (ok, mensagem)."""
    host = config_get(conn, "smtp_host")
    if not host:
        return False, "SMTP não configurado"
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    try:
        porta = int(config_get(conn, "smtp_porta") or 587)
        usuario = config_get(conn, "smtp_usuario")
        senha = config_get(conn, "smtp_senha")
        remetente = config_get(conn, "smtp_remetente") or usuario
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = remetente
        msg["To"] = para
        # texto puro primeiro (fallback), depois o HTML da marca
        msg.attach(MIMEText(corpo, "plain", "utf-8"))
        msg.attach(MIMEText(montar_email_html(assunto, corpo), "html", "utf-8"))
        # porta 465 usa SSL direto; 587 (e demais) usam STARTTLS
        if porta == 465:
            with smtplib.SMTP_SSL(host, porta, timeout=20) as servidor:
                if usuario:
                    servidor.login(usuario, senha)
                servidor.sendmail(remetente, [para], msg.as_string())
        else:
            with smtplib.SMTP(host, porta, timeout=20) as servidor:
                servidor.ehlo()
                servidor.starttls()
                servidor.ehlo()
                if usuario:
                    servidor.login(usuario, senha)
                servidor.sendmail(remetente, [para], msg.as_string())
        return True, "enviado"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


# --------------------------------------------------- modelos de e-mail
# Placeholders disponíveis: {nome}, {vaga}, {link}, {local}, {etapa}
TEMPLATES_PADRAO = {
    "confirmacao": {
        "assunto": "Inscrição confirmada: {vaga}",
        "corpo": ("Olá, {nome}!\n\nSeu cadastro em \"{vaga}\" foi realizado com sucesso.\n\n"
                  "Este é o seu link pessoal de acesso. Guarde-o: por ele você continua a "
                  "avaliação e acompanha seus resultados de qualquer aparelho:\n\n{link}\n\n"
                  "Atenciosamente,\nEquipe de Seleção"),
    },
    "lembrete": {
        "assunto": "Falta pouco para concluir sua avaliação",
        "corpo": ("Olá, {nome}!\n\nNotamos que você começou a avaliação em \"{vaga}\" e "
                  "ainda não concluiu todas as etapas. Elas levam poucos minutos e são "
                  "essenciais para a sua candidatura.\n\nContinue de onde parou pelo seu "
                  "link pessoal:\n\n{link}\n\nAtenciosamente,\nEquipe de Seleção"),
    },
    "etapa_inscrito": {
        "assunto": "Atualização da sua candidatura: {vaga}",
        "corpo": "Olá, {nome}!\n\nSua inscrição na vaga \"{vaga}\" foi registrada.\n\nAtenciosamente,\nEquipe de Seleção",
    },
    "etapa_avaliacoes": {
        "assunto": "Atualização da sua candidatura: {vaga}",
        "corpo": "Olá, {nome}!\n\nSua candidatura na vaga \"{vaga}\" avançou para a etapa de avaliações.\n\nAtenciosamente,\nEquipe de Seleção",
    },
    "etapa_entrevista": {
        "assunto": "Você foi selecionado(a) para entrevista: {vaga}",
        "corpo": ("Olá, {nome}!\n\nBoa notícia: você foi selecionado(a) para a etapa de "
                  "entrevista da vaga \"{vaga}\". Em breve entraremos em contato para "
                  "agendar.\n\nAtenciosamente,\nEquipe de Seleção"),
    },
    "etapa_proposta": {
        "assunto": "Você avançou para a proposta: {vaga}",
        "corpo": "Olá, {nome}!\n\nParabéns! Você avançou para a etapa de proposta da vaga \"{vaga}\".\n\nAtenciosamente,\nEquipe de Seleção",
    },
    "etapa_contratado": {
        "assunto": "Parabéns! Você foi aprovado(a): {vaga}",
        "corpo": "Olá, {nome}!\n\nParabéns! Você foi aprovado(a) no processo seletivo da vaga \"{vaga}\". Bem-vindo(a) ao time!\n\nAtenciosamente,\nEquipe de Seleção",
    },
    "etapa_reprovado": {
        "assunto": "Atualização da sua candidatura: {vaga}",
        "corpo": ("Olá, {nome}.\n\nAgradecemos a sua participação no processo da vaga "
                  "\"{vaga}\". Neste momento você não seguirá no processo, mas seu perfil "
                  "fica em nosso banco de talentos para futuras oportunidades.\n\n"
                  "Atenciosamente,\nEquipe de Seleção"),
    },
}

NOMES_TEMPLATES = {
    "confirmacao": "Confirmação de inscrição",
    "lembrete": "Lembrete de avaliação incompleta",
    "etapa_inscrito": "Etapa: Inscrito",
    "etapa_avaliacoes": "Etapa: Avaliações",
    "etapa_entrevista": "Etapa: Entrevista",
    "etapa_proposta": "Etapa: Proposta",
    "etapa_contratado": "Etapa: Contratado",
    "etapa_reprovado": "Etapa: Reprovado",
}


def templates_email(conn):
    salvos = config_get(conn, "templates_email")
    try:
        salvos = json.loads(salvos) if salvos else {}
    except ValueError:
        salvos = {}
    resultado = {}
    for chave, padrao in TEMPLATES_PADRAO.items():
        atual = salvos.get(chave) or {}
        resultado[chave] = {
            "assunto": atual.get("assunto") or padrao["assunto"],
            "corpo": atual.get("corpo") or padrao["corpo"],
        }
    return resultado


class _DicionarioSeguro(dict):
    def __missing__(self, chave):
        return "{" + chave + "}"


def renderizar(texto, variaveis):
    return texto.format_map(_DicionarioSeguro(variaveis))


def url_publica(conn, host_header=None):
    configurada = (config_get(conn, "url_publica") or "").strip().rstrip("/")
    if configurada:
        return configurada
    return "http://" + (host_header or "localhost:8080")


def variaveis_candidato(conn, cand, host_header=None):
    vaga = conn.execute(
        "SELECT v.titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
        " WHERE ca.candidato_id=? ORDER BY ca.criado_em DESC LIMIT 1",
        (cand["id"],),
    ).fetchone()
    nome_vaga = vaga["titulo"] if vaga else "processo seletivo"
    return {
        "nome": cand["nome"],
        "local": cand["local"] or "",
        "vaga": nome_vaga,
        "link": "%s/candidato?token=%s" % (url_publica(conn, host_header), cand["token"]),
    }


def emails_gestores_do_local(conn, local_candidato):
    """Gestores que devem ser avisados sobre um candidato: administradores,
    gestores sem local definido e gestores do mesmo local."""
    alvo = (local_candidato or "").strip().lower()
    emails = []
    for g in conn.execute("SELECT email, local, is_admin FROM gestores").fetchall():
        if not (g["email"] or "").strip():
            continue
        if g["is_admin"] or not (g["local"] or "").strip() \
                or (g["local"] or "").strip().lower() == alvo:
            emails.append(g["email"].strip())
    return sorted(set(emails))


def notificar_gestores(conn, cand, assunto, corpo):
    """Envia e-mail aos gestores responsáveis pelo local do candidato (best-effort)."""
    if not config_get(conn, "smtp_host"):
        return
    enviados = 0
    for email in emails_gestores_do_local(conn, cand["local"]):
        ok, _ = enviar_email(conn, email, assunto, corpo)
        if ok:
            enviados += 1
    if enviados:
        registrar_evento(
            conn, cand["id"], "email",
            "Gestores notificados por e-mail (%d): %s" % (enviados, assunto),
        )


def avaliacao_ficou_completa(conn, cand):
    """True na primeira vez em que o candidato conclui DISC + B.A.S.E. +
    autoavaliação (e o quiz, quando o cargo tiver questões)."""
    if cand["notificado_completo"]:
        return False
    tipos = {
        r["tipo"] for r in conn.execute(
            "SELECT tipo FROM resultados_teste WHERE candidato_id=?", (cand["id"],)
        ).fetchall()
    }
    if "disc" not in tipos or "base" not in tipos:
        return False
    if cand["cargo_desejado_id"]:
        tem_comp = conn.execute(
            "SELECT 1 FROM competencias WHERE cargo_id=? LIMIT 1",
            (cand["cargo_desejado_id"],),
        ).fetchone()
        respondeu = conn.execute(
            "SELECT 1 FROM autoavaliacoes WHERE candidato_id=? LIMIT 1", (cand["id"],)
        ).fetchone()
        if tem_comp and not respondeu:
            return False
        tem_quiz = conn.execute(
            "SELECT 1 FROM questoes WHERE cargo_id=? LIMIT 1",
            (cand["cargo_desejado_id"],),
        ).fetchone()
        fez_quiz = conn.execute(
            "SELECT 1 FROM resultados_quiz WHERE candidato_id=? AND cargo_id=?",
            (cand["id"], cand["cargo_desejado_id"]),
        ).fetchone()
        if tem_quiz and not fez_quiz:
            return False
    return True


def notificar_avaliacao_completa(conn, cand):
    """Ao completar a avaliação, marca o candidato e avisa os gestores com o match."""
    if not avaliacao_ficou_completa(conn, cand):
        return
    conn.execute(
        "UPDATE candidatos SET notificado_completo=1 WHERE id=?", (cand["id"],)
    )
    registrar_evento(conn, cand["id"], "sistema", "Avaliação completa")
    match = None
    nome_cargo = ""
    if cand["cargo_desejado_id"]:
        match = match_completo(conn, cand, cand["cargo_desejado_id"])
        cargo = conn.execute(
            "SELECT nome FROM cargos WHERE id=?", (cand["cargo_desejado_id"],)
        ).fetchone()
        nome_cargo = cargo["nome"] if cargo else ""
    linha_match = (
        "Match geral com o cargo %s: %d%%\n" % (nome_cargo, match["geral"])
        if match else ""
    )
    notificar_gestores(
        conn, cand,
        "Avaliação completa: %s" % cand["nome"],
        ("O candidato %s (%s) concluiu toda a avaliação.\n%s\n"
         "Acesse o painel do gestor para ver o relatório completo.")
        % (cand["nome"], cand["local"] or "local não informado", linha_match),
    )


def quiz_do_candidato(conn, candidato_id, cargo_id):
    r = conn.execute(
        "SELECT acertos, total, criado_em FROM resultados_quiz"
        " WHERE candidato_id=? AND cargo_id=?",
        (candidato_id, cargo_id),
    ).fetchone()
    if not r or not r["total"]:
        return None
    return {
        "acertos": r["acertos"],
        "total": r["total"],
        "pct": round(100 * r["acertos"] / r["total"]),
        "criado_em": r["criado_em"],
    }


def entrevista_do_candidato(conn, candidato_id, cargo_id):
    r = conn.execute(
        "SELECT media, gestor_nome, payload, criado_em FROM entrevistas"
        " WHERE candidato_id=? AND cargo_id=? ORDER BY criado_em DESC LIMIT 1",
        (candidato_id, cargo_id),
    ).fetchone()
    if not r:
        return None
    return {
        "media": r["media"],
        "pct": round(r["media"] / 5 * 100),
        "gestor": r["gestor_nome"],
        "payload": json.loads(r["payload"]),
        "criado_em": r["criado_em"],
    }


def calcular_match(cargo_row, testes, gaps, quiz=None, entrevista=None):
    """Cruza TUDO num índice único: competências, DISC, B.A.S.E.,
    teste de conhecimento e entrevista estruturada."""
    if not cargo_row:
        return None
    componentes = {}
    if gaps and gaps["respondeu_autoavaliacao"]:
        componentes["competencias"] = gaps["aderencia"]
    if (cargo_row["disc_alvo"] or "") and "disc" in testes:
        pct = testes["disc"]["payload"].get("pct") or {}
        if cargo_row["disc_alvo"] in pct:
            componentes["disc"] = pct[cargo_row["disc_alvo"]]
    if (cargo_row["base_alvo"] or "") and "base" in testes:
        pct = testes["base"]["payload"].get("pct") or {}
        if cargo_row["base_alvo"] in pct:
            componentes["base"] = pct[cargo_row["base_alvo"]]
    if quiz:
        componentes["conhecimento"] = quiz["pct"]
    if entrevista:
        componentes["entrevista"] = entrevista["pct"]
    if not componentes:
        return None
    peso_total = sum(PESOS_MATCH[k] for k in componentes)
    geral = round(sum(v * PESOS_MATCH[k] for k, v in componentes.items()) / peso_total)
    return {
        "geral": geral,
        "componentes": componentes,
        "disc_alvo": cargo_row["disc_alvo"] or "",
        "base_alvo": cargo_row["base_alvo"] or "",
    }


def match_completo(conn, cand, cargo_id, testes=None, gaps=None):
    """Calcula o match do candidato contra um cargo, juntando todas as fontes."""
    cargo_row = conn.execute("SELECT * FROM cargos WHERE id=?", (cargo_id,)).fetchone()
    if not cargo_row:
        return None
    if testes is None:
        testes = {
            r["tipo"]: {"payload": json.loads(r["payload"])}
            for r in conn.execute(
                "SELECT tipo, payload FROM resultados_teste WHERE candidato_id=?",
                (cand["id"],),
            ).fetchall()
        }
    if gaps is None:
        gaps = matriz_gaps(conn, cand["id"], cargo_id)
    quiz = quiz_do_candidato(conn, cand["id"], cargo_id)
    entrevista = entrevista_do_candidato(conn, cand["id"], cargo_id)
    return calcular_match(cargo_row, testes, gaps, quiz, entrevista)


def resumo_candidato(conn, cand):
    """Monta o pacote completo de resultados de um candidato."""
    testes = {
        r["tipo"]: {"payload": json.loads(r["payload"]), "criado_em": r["criado_em"]}
        for r in conn.execute(
            "SELECT tipo, payload, criado_em FROM resultados_teste WHERE candidato_id=?",
            (cand["id"],),
        ).fetchall()
    }
    gaps = None
    match = None
    quiz = None
    entrevista = None
    if cand["cargo_desejado_id"]:
        gaps = matriz_gaps(conn, cand["id"], cand["cargo_desejado_id"])
        quiz = quiz_do_candidato(conn, cand["id"], cand["cargo_desejado_id"])
        entrevista = entrevista_do_candidato(conn, cand["id"], cand["cargo_desejado_id"])
        match = match_completo(conn, cand, cand["cargo_desejado_id"], testes, gaps)
    candidaturas = [
        {
            "id": r["id"],
            "vaga_id": r["vaga_id"],
            "vaga_titulo": r["titulo"],
            "vaga_status": r["status"],
            "etapa": r["etapa"],
            "etapa_nome": NOMES_ETAPAS.get(r["etapa"], r["etapa"]),
            "motivo_reprovacao": r["motivo_reprovacao"],
        }
        for r in conn.execute(
            "SELECT ca.*, v.titulo, v.status FROM candidaturas ca"
            " JOIN vagas v ON v.id = ca.vaga_id WHERE ca.candidato_id=?"
            " ORDER BY ca.criado_em DESC",
            (cand["id"],),
        ).fetchall()
    ]
    return {
        "candidato": {
            "id": cand["id"],
            "nome": cand["nome"],
            "email": cand["email"],
            "local": cand["local"],
            "telefone": cand["telefone"] if "telefone" in cand.keys() else "",
            "funcao": cand["funcao"] if "funcao" in cand.keys() else "",
            "linkedin": cand["linkedin"],
            "instagram": cand["instagram"],
            "cargo_atual": cand["cargo_atual"],
            "tags": json.loads(cand["tags"] or "[]"),
            "anonimizado": bool(cand["anonimizado"]),
            "tipo": cand["tipo"] or "externo",
            "cargo_desejado_id": cand["cargo_desejado_id"],
            "curriculo": bool(cand["curriculo_arquivo"]),
            "criado_em": cand["criado_em"],
        },
        "testes": testes,
        "gaps": gaps,
        "match": match,
        "quiz": quiz,
        "entrevista": entrevista,
        "candidaturas": candidaturas,
    }


ESQUEMA_ANALISE_IA = {
    "type": "object",
    "properties": {
        "resumo": {"type": "string"},
        "formacoes": {"type": "array", "items": {"type": "string"}},
        "experiencias": {"type": "array", "items": {"type": "string"}},
        "pontos_fortes": {"type": "array", "items": {"type": "string"}},
        "divergencias": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "competencia": {"type": "string"},
                    "nivel_declarado": {"type": "string"},
                    "evidencia_no_curriculo": {"type": "string"},
                    "comentario": {"type": "string"},
                },
                "required": ["competencia", "nivel_declarado",
                             "evidencia_no_curriculo", "comentario"],
                "additionalProperties": False,
            },
        },
        "aderencia_curriculo": {"type": "integer"},
        "recomendacao": {"type": "string"},
    },
    "required": ["resumo", "formacoes", "experiencias", "pontos_fortes",
                 "divergencias", "aderencia_curriculo", "recomendacao"],
    "additionalProperties": False,
}


def analisar_curriculo_ia(conn, cand):
    """Lê o currículo (PDF) com a API da Anthropic e cruza com a autoavaliação."""
    api_key = config_get(conn, "anthropic_api_key")
    if not api_key:
        return None, "Configure a chave da API da Anthropic na aba Configurações"
    if not cand["curriculo_arquivo"]:
        return None, "Este candidato não enviou currículo"
    if not cand["curriculo_arquivo"].lower().endswith(".pdf"):
        return None, "A análise por IA exige currículo em PDF"
    caminho = os.path.join(UPLOAD_DIR, cand["curriculo_arquivo"])
    if not os.path.isfile(caminho):
        return None, "Arquivo do currículo não encontrado"
    try:
        import anthropic
    except ImportError:
        return None, ("Biblioteca da Anthropic não instalada no servidor."
                      " Rode: pip3 install anthropic")

    with open(caminho, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode("ascii")

    contexto = {"cargo": None, "competencias": []}
    if cand["cargo_desejado_id"]:
        cargo = cargo_com_competencias(conn, cand["cargo_desejado_id"])
        if cargo:
            respostas = {
                r["competencia_id"]: r["nivel_atual"]
                for r in conn.execute(
                    "SELECT competencia_id, nivel_atual FROM autoavaliacoes"
                    " WHERE candidato_id=?",
                    (cand["id"],),
                ).fetchall()
            }
            contexto["cargo"] = "%s (%s)" % (cargo["nome"], cargo["nivel"])
            contexto["competencias"] = [
                {
                    "competencia": k["nome"],
                    "tipo": k["tipo"],
                    "nivel_exigido": k["nivel_requerido"],
                    "nivel_autodeclarado": respostas.get(k["id"], "não respondeu"),
                }
                for k in cargo["competencias"]
            ]

    prompt = (
        "Você é um analista de RH. Analise o currículo em PDF anexo do candidato %s.\n"
        "Cargo de interesse: %s.\n"
        "Autoavaliação de competências do candidato (escala 0 a 5):\n%s\n\n"
        "Tarefas:\n"
        "1. Resuma o perfil profissional em um parágrafo.\n"
        "2. Liste as formações/certificações e as experiências principais do currículo.\n"
        "3. Compare a autoavaliação com o currículo e aponte divergências: competências"
        " com nível declarado alto sem evidência no currículo, ou o contrário.\n"
        "4. Estime a aderência do CURRÍCULO ao cargo (0 a 100), independente da autoavaliação.\n"
        "5. Dê uma recomendação objetiva para o gestor (2 a 3 frases).\n"
        "Responda em português."
    ) % (
        cand["nome"],
        contexto["cargo"] or "não informado",
        json.dumps(contexto["competencias"], ensure_ascii=False, indent=1),
    )

    client = anthropic.Anthropic(api_key=api_key)
    resposta = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
        output_config={"format": {"type": "json_schema", "schema": ESQUEMA_ANALISE_IA}},
    )
    if resposta.stop_reason == "refusal":
        return None, "A análise foi recusada pelos filtros de segurança do modelo"
    texto = next((b.text for b in resposta.content if b.type == "text"), "")
    return json.loads(texto), None


def anonimizar_candidato(conn, cand, autor="sistema"):
    """Remove os dados pessoais mantendo as estatísticas (LGPD)."""
    if cand["curriculo_arquivo"]:
        arquivo = os.path.join(UPLOAD_DIR, cand["curriculo_arquivo"])
        if os.path.isfile(arquivo):
            os.remove(arquivo)
    conn.execute(
        "UPDATE candidatos SET nome='Candidato anonimizado', email='',"
        " linkedin='', instagram='', curriculo_arquivo='', analise_ia='',"
        " cargo_atual='', anonimizado=1, token=? WHERE id=?",
        (secrets.token_urlsafe(24), cand["id"]),
    )
    conn.execute("DELETE FROM eventos WHERE candidato_id=?", (cand["id"],))
    registrar_evento(conn, cand["id"], "sistema",
                     "Dados pessoais anonimizados (LGPD)", autor)


def analisar_curriculo_em_segundo_plano(candidato_id):
    """Roda a análise de IA do currículo sem travar o upload do candidato."""
    try:
        conn = db()
        cand = conn.execute(
            "SELECT * FROM candidatos WHERE id=?", (candidato_id,)
        ).fetchone()
        if not cand or cand["analise_ia"]:
            conn.close()
            return
        analise, erro = analisar_curriculo_ia(conn, cand)
        if analise:
            conn.execute(
                "UPDATE candidatos SET analise_ia=? WHERE id=?",
                (json.dumps(analise, ensure_ascii=False), cand["id"]),
            )
            registrar_evento(
                conn, cand["id"], "ia",
                "Currículo analisado automaticamente por IA (aderência %s%%)"
                % analise.get("aderencia_curriculo"),
            )
            conn.commit()
        conn.close()
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("Análise automática de currículo falhou: %r\n" % exc)


def rotina_automatica():
    """Roda a cada hora: lembrete de avaliação incompleta (48h) e retenção LGPD."""
    import time

    while True:
        try:
            conn = db()
            # lembrete para quem começou e não terminou em 2 dias
            if config_get(conn, "smtp_host"):
                pendentes = conn.execute(
                    "SELECT * FROM candidatos WHERE notificado_completo=0"
                    " AND lembrete_enviado=0 AND anonimizado=0 AND email != ''"
                    " AND criado_em <= datetime('now', '-2 days')"
                ).fetchall()
                for cand in pendentes:
                    variaveis = variaveis_candidato(conn, cand)
                    modelo = templates_email(conn)["lembrete"]
                    # envia o e-mail (I/O de rede) ANTES de qualquer escrita, para
                    # não segurar o lock do SQLite durante o SMTP.
                    ok, _ = enviar_email(
                        conn, cand["email"],
                        renderizar(modelo["assunto"], variaveis),
                        renderizar(modelo["corpo"], variaveis),
                    )
                    if ok:
                        conn.execute(
                            "UPDATE candidatos SET lembrete_enviado=1 WHERE id=?",
                            (cand["id"],),
                        )
                        registrar_evento(
                            conn, cand["id"], "email",
                            "Lembrete de avaliação incompleta enviado",
                        )
                        conn.commit()  # libera o lock antes do próximo e-mail
            # retenção de dados (LGPD)
            meses = int(config_get(conn, "retencao_meses") or 0)
            if meses > 0:
                antigos = conn.execute(
                    "SELECT * FROM candidatos WHERE anonimizado=0"
                    " AND criado_em <= datetime('now', ?)",
                    ("-%d months" % meses,),
                ).fetchall()
                for cand in antigos:
                    anonimizar_candidato(conn, cand)
                    conn.commit()
            conn.close()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Rotina automática falhou: %r\n" % exc)
        time.sleep(3600)


def gestor_ve_candidato(gestor, cand):
    """Gestor vinculado a um local enxerga apenas candidatos daquele local."""
    if gestor["is_admin"] or not (gestor["local"] or "").strip():
        return True
    return (cand["local"] or "").strip().lower() == gestor["local"].strip().lower()


def gestor_ve_local(gestor, local):
    """Mesma regra de escopo por local, aplicada a um valor de local avulso
    (usada nas sessões do módulo Diagnóstico)."""
    if gestor["is_admin"] or not (gestor["local"] or "").strip():
        return True
    return (local or "").strip().lower() == gestor["local"].strip().lower()


# ------------------------------------------------------------ servidor

MAX_BODY = 12 * 1024 * 1024  # 12 MB: cobre currículo de 8 MB em base64 com folga

# limite de tentativas de login por IP (freia força bruta)
_LOGIN_JANELA = 900      # 15 minutos
_LOGIN_LIMITE = 8        # tentativas falhas na janela
_login_falhas = {}
_login_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _ip_cliente(self):
        # atrás do Caddy o IP real é o ÚLTIMO da cadeia X-Forwarded-For (o proxy
        # acrescenta quem conectou); o primeiro valor é enviado pelo cliente e
        # seria forjável para burlar o limite de tentativas.
        encaminhado = self.headers.get("X-Forwarded-For", "")
        if encaminhado:
            return encaminhado.split(",")[-1].strip()
        return self.client_address[0] if self.client_address else "?"

    def _login_bloqueado(self, escopo):
        chave = escopo + ":" + self._ip_cliente()
        agora = time.time()
        with _login_lock:
            recentes = [t for t in _login_falhas.get(chave, []) if agora - t < _LOGIN_JANELA]
            _login_falhas[chave] = recentes
            return len(recentes) >= _LOGIN_LIMITE

    def _registrar_falha_login(self, escopo):
        chave = escopo + ":" + self._ip_cliente()
        with _login_lock:
            _login_falhas.setdefault(chave, []).append(time.time())

    def _limpar_falhas_login(self, escopo):
        chave = escopo + ":" + self._ip_cliente()
        with _login_lock:
            _login_falhas.pop(chave, None)

    def _corpo_grande_demais(self):
        """Rejeita corpos acima do limite antes de ler tudo na memória (DoS)."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length > MAX_BODY:
            body = json.dumps({"erro": "Envio grande demais"}).encode("utf-8")
            self.send_response(413)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            return True
        return False

    # ---------- utilitários ----------
    def _json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _ler_corpo(self):
        """Lê o corpo inteiro uma única vez, logo no início da requisição.
        Essencial com keep-alive (HTTP/1.1): se uma rota responde antes de ler o
        corpo, os bytes sobram na conexão e a requisição seguinte é lida
        embaralhada (erro 501 'Unsupported method'). Drenar aqui evita isso."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        self._raw = self.rfile.read(length) if length > 0 else b""

    def _body(self):
        raw = getattr(self, "_raw", None)
        if raw is None:  # fallback defensivo, caso _ler_corpo não tenha rodado
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if length > 0 else b""
            self._raw = raw
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def _candidato(self, conn):
        token = self.headers.get("X-Token", "")
        if not token:
            return None
        return conn.execute(
            "SELECT * FROM candidatos WHERE token=?", (token,)
        ).fetchone()

    def _gestor(self, conn):
        token = self.headers.get("X-Gestor-Token", "")
        if not token:
            return None
        return conn.execute(
            "SELECT g.* FROM sessoes_gestor s JOIN gestores g ON g.id = s.gestor_id"
            " WHERE s.token=?",
            (token,),
        ).fetchone()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # ---------- roteamento ----------
    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            return self.api("GET", path)
        return self.static(path)

    def do_POST(self):
        if self._corpo_grande_demais():
            return None
        self._ler_corpo()  # drena o corpo sempre (mantém a conexão em sincronia)
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            return self.api("POST", path)
        return self._json(404, {"erro": "Não encontrado"})

    def do_DELETE(self):
        if self._corpo_grande_demais():
            return None
        self._ler_corpo()
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            return self.api("DELETE", path)
        return self._json(404, {"erro": "Não encontrado"})

    # ---------- estáticos ----------
    PAGINAS = {
        "/": "index.html",
        "/candidato": "candidato.html",
        "/gestor": "gestor.html",
        "/vagas": "vagas.html",
        "/dono": "dono.html",
    }

    def static(self, path):
        # endereços limpos: /gestor serve gestor.html etc.
        if path in self.PAGINAS:
            path = "/" + self.PAGINAS[path]
        elif path.endswith(".html") and path.lstrip("/") in self.PAGINAS.values():
            # links antigos com .html redirecionam para o endereço limpo
            limpo = path[:-len(".html")]
            if limpo == "/index":
                limpo = "/"
            query = urlparse(self.path).query
            self.send_response(301)
            self.send_header("Location", limpo + ("?" + query if query else ""))
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        # normaliza e impede path traversal
        safe = os.path.normpath(path).lstrip("/").replace("..", "")
        full = os.path.join(PUBLIC_DIR, safe)
        if not full.startswith(PUBLIC_DIR) or not os.path.isfile(full):
            return self._json(404, {"erro": "Não encontrado"})
        ctypes = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".png": "image/png",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".ttf": "font/ttf",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
        }
        ext = os.path.splitext(full)[1]
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctypes.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        if ext in (".css", ".js", ".html"):
            self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    # ---------- API ----------
    def api(self, method, path):
        conn = db()
        try:
            return self.route(method, path, conn)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("ERRO: %r\n" % exc)
            return self._json(500, {"erro": "Erro interno"})
        finally:
            conn.close()

    def route(self, method, path, conn):
        # ---- público ----
        if method == "GET" and path == "/api/cargos":
            cargos = [
                cargo_com_competencias(conn, r["id"])
                for r in conn.execute("SELECT id FROM cargos ORDER BY nome").fetchall()
            ]
            return self._json(200, {"cargos": cargos})

        # ---- candidato ----
        if method == "POST" and path == "/api/candidato/cadastro":
            d = self._body()
            nome = (d.get("nome") or "").strip()
            email = (d.get("email") or "").strip()
            if not nome or not email:
                return self._json(400, {"erro": "Nome e e-mail são obrigatórios"})
            local = (d.get("local") or "").strip()
            if not local:
                return self._json(400, {"erro": "Informe onde você está fazendo a avaliação"})
            telefone = (d.get("telefone") or "").strip()
            if len(re.sub(r"\D", "", telefone)) < 8:
                return self._json(400, {"erro": "Informe um telefone válido com o código do país"})
            if not d.get("consentimento"):
                return self._json(400, {"erro": "É necessário autorizar o uso dos seus dados para o processo seletivo"})
            # candidato duplicado: reaproveita a ficha existente com segurança
            existente = conn.execute(
                "SELECT * FROM candidatos WHERE lower(email)=lower(?) AND anonimizado=0",
                (email,),
            ).fetchone()
            vaga = None
            if d.get("vaga_id"):
                vaga = conn.execute(
                    "SELECT * FROM vagas WHERE id=? AND status='aberta'",
                    (d["vaga_id"],),
                ).fetchone()
                if not vaga:
                    return self._json(400, {"erro": "Esta vaga não está mais aberta"})
            if existente:
                # não devolve o token de outra pessoa: envia o link por e-mail
                if vaga and not conn.execute(
                    "SELECT 1 FROM candidaturas WHERE candidato_id=? AND vaga_id=?",
                    (existente["id"], vaga["id"]),
                ).fetchone():
                    conn.execute(
                        "INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)",
                        (existente["id"], vaga["id"]),
                    )
                    registrar_evento(
                        conn, existente["id"], "candidatura",
                        "Nova inscrição na vaga: %s" % vaga["titulo"],
                    )
                enviou = False
                if config_get(conn, "smtp_host"):
                    variaveis = variaveis_candidato(conn, existente, self.headers.get("Host"))
                    ok, _ = enviar_email(
                        conn, existente["email"], "Seu link de acesso à avaliação",
                        renderizar(
                            "Olá, {nome}!\n\nVocê já possui cadastro no nosso sistema de "
                            "seleção. Use o seu link pessoal para continuar:\n\n{link}\n\n"
                            "Atenciosamente,\nEquipe de Seleção", variaveis),
                    )
                    enviou = ok
                    if ok:
                        registrar_evento(conn, existente["id"], "email",
                                         "Link de acesso reenviado (cadastro duplicado)")
                conn.commit()
                return self._json(409, {
                    "erro": ("Este e-mail já possui cadastro. "
                             + ("Enviamos o seu link de acesso para o e-mail informado."
                                if enviou else
                                "Use o seu link pessoal de acesso para continuar.")),
                    "ja_cadastrado": True,
                })
            # resolve o cargo de interesse: da vaga, do id escolhido, ou de um
            # cargo novo digitado pelo candidato (passa a existir no sistema).
            if vaga:
                cargo_desejado = vaga["cargo_id"]
            else:
                cargo_desejado = d.get("cargo_desejado_id") or None
                novo_cargo = (d.get("novo_cargo") or "").strip()
                if novo_cargo:
                    ja = conn.execute(
                        "SELECT id FROM cargos WHERE lower(nome)=lower(?)", (novo_cargo,)
                    ).fetchone()
                    if ja:
                        cargo_desejado = ja["id"]
                    else:
                        cur = conn.execute(
                            "INSERT INTO cargos (nome, area, nivel) VALUES (?,?,?)",
                            (novo_cargo, (d.get("novo_cargo_area") or "").strip(), ""),
                        )
                        cargo_desejado = cur.lastrowid
            token = secrets.token_urlsafe(24)
            conn.execute(
                "INSERT INTO candidatos (token, nome, email, local, telefone, funcao,"
                " linkedin, instagram, cargo_atual, cargo_desejado_id)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    token,
                    nome,
                    email,
                    local,
                    telefone,
                    (d.get("funcao") or "").strip(),
                    (d.get("linkedin") or "").strip(),
                    (d.get("instagram") or "").strip().lstrip("@"),
                    (d.get("cargo_atual") or "").strip(),
                    cargo_desejado or None,
                ),
            )
            conn.execute(
                "UPDATE candidatos SET consentimento_em=datetime('now') WHERE token=?",
                (token,),
            )
            tipo = "interno" if d.get("tipo") == "interno" and not vaga else "externo"
            conn.execute(
                "UPDATE candidatos SET tipo=? WHERE token=?", (tipo, token)
            )
            novo = conn.execute(
                "SELECT * FROM candidatos WHERE token=?", (token,)
            ).fetchone()
            novo_id = novo["id"]
            registrar_evento(
                conn, novo_id, "cadastro",
                ("Cadastro de colaborador interno (%s)" if tipo == "interno"
                 else "Cadastro realizado (%s)") % local,
            )
            if vaga:
                conn.execute(
                    "INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)",
                    (novo_id, vaga["id"]),
                )
                registrar_evento(
                    conn, novo_id, "candidatura",
                    "Inscrição na vaga: %s" % vaga["titulo"],
                )
            # e-mails automáticos (só quando o SMTP estiver configurado)
            if config_get(conn, "smtp_host"):
                variaveis = variaveis_candidato(conn, novo, self.headers.get("Host"))
                modelo = templates_email(conn)["confirmacao"]
                ok, _ = enviar_email(
                    conn, email,
                    renderizar(modelo["assunto"], variaveis),
                    renderizar(modelo["corpo"], variaveis),
                )
                if ok:
                    registrar_evento(conn, novo_id, "email",
                                     "E-mail de confirmação enviado ao candidato")
                notificar_gestores(
                    conn, novo,
                    "Novo candidato: %s" % nome,
                    ("Novo cadastro no sistema de RH.\n\nNome: %s\nE-mail: %s\n"
                     "Local: %s\n%s\nAcesse o painel do gestor para acompanhar.")
                    % (nome, email, local,
                       ("Vaga: %s\n" % vaga["titulo"]) if vaga else ""),
                )
            conn.commit()
            return self._json(200, {"token": token})

        if method == "GET" and path == "/api/vagas":
            qs = parse_qs(urlparse(self.path).query)
            pagina = None
            filtro_local = None
            login_gestor = (qs.get("g", [""])[0] or "").strip().lower()
            if login_gestor:
                dono = conn.execute(
                    "SELECT nome, local FROM gestores WHERE lower(login)=?",
                    (login_gestor,),
                ).fetchone()
                if not dono:
                    return self._json(404, {"erro": "Página de vagas não encontrada"})
                pagina = {"gestor_nome": dono["nome"], "local": dono["local"] or ""}
                if (dono["local"] or "").strip():
                    filtro_local = dono["local"].strip().lower()
            vagas = []
            for r in conn.execute(
                "SELECT v.*, c.nome, c.nivel, c.area FROM vagas v"
                " JOIN cargos c ON c.id = v.cargo_id"
                " WHERE v.status='aberta' ORDER BY v.criado_em DESC"
            ).fetchall():
                if filtro_local and (r["local"] or "").strip().lower() != filtro_local:
                    continue
                vagas.append({
                    "id": r["id"], "titulo": r["titulo"], "local": r["local"],
                    "pais": r["pais"] or "",
                    "descricao": r["descricao"], "cargo_id": r["cargo_id"],
                    "cargo_nome": r["nome"], "nivel": r["nivel"], "area": r["area"],
                })
            return self._json(200, {"vagas": vagas, "pagina": pagina})

        if method == "POST" and path == "/api/candidato/recuperar-acesso":
            d = self._body()
            email = (d.get("email") or "").strip()
            if not email:
                return self._json(400, {"erro": "Informe o e-mail cadastrado"})
            if not config_get(conn, "smtp_host"):
                return self._json(400, {"erro": "O reenvio por e-mail ainda não está ativo. Fale com o gestor do processo para recuperar seu link."})
            cand = conn.execute(
                "SELECT * FROM candidatos WHERE lower(email)=lower(?) AND anonimizado=0",
                (email,),
            ).fetchone()
            if cand:
                variaveis = variaveis_candidato(conn, cand, self.headers.get("Host"))
                ok, _ = enviar_email(
                    conn, cand["email"], "Seu link de acesso à avaliação",
                    renderizar(
                        "Olá, {nome}!\n\nAqui está o seu link pessoal de acesso:\n\n{link}\n\n"
                        "Atenciosamente,\nEquipe de Seleção", variaveis),
                )
                if ok:
                    registrar_evento(conn, cand["id"], "email", "Link de acesso reenviado a pedido")
                    conn.commit()
            # resposta idêntica com ou sem cadastro (não revela quem está na base)
            return self._json(200, {"ok": True})

        if method == "GET" and path == "/api/locais":
            locais = sorted({
                (r["local"] or "").strip()
                for r in conn.execute(
                    "SELECT local FROM gestores UNION SELECT local FROM candidatos"
                ).fetchall()
                if (r["local"] or "").strip()
            })
            return self._json(200, {"locais": locais})

        cand = self._candidato(conn)
        if path.startswith("/api/candidato/") and path != "/api/candidato/cadastro":
            if not cand:
                return self._json(401, {"erro": "Sessão inválida. Faça o cadastro novamente."})

        if method == "GET" and path == "/api/candidato/me":
            return self._json(200, resumo_candidato(conn, cand))

        if method == "POST" and path == "/api/candidato/teste":
            d = self._body()
            tipo = d.get("tipo")
            if tipo not in ("disc", "base"):
                return self._json(400, {"erro": "Tipo de teste inválido"})
            # o servidor recalcula a nota a partir das respostas cruas (não confia
            # no que o cliente mandou pronto); se vierem só a nota, sanitiza.
            respostas = d.get("respostas")
            if isinstance(respostas, list):
                payload = (calcular_disc_payload(respostas) if tipo == "disc"
                           else calcular_base_payload(respostas))
            else:
                payload = None
            if not payload:
                payload = sanitizar_payload_teste(tipo, d.get("payload"))
            if not payload:
                return self._json(400, {"erro": "Respostas do teste inválidas ou incompletas"})
            conn.execute(
                "INSERT INTO resultados_teste (candidato_id, tipo, payload) VALUES (?,?,?)"
                " ON CONFLICT(candidato_id, tipo) DO UPDATE SET"
                " payload=excluded.payload, criado_em=datetime('now')",
                (cand["id"], tipo, json.dumps(payload, ensure_ascii=False)),
            )
            registrar_evento(
                conn, cand["id"], "teste",
                "Teste %s concluído" % ("DISC" if tipo == "disc" else "B.A.S.E."),
                cand["nome"],
            )
            notificar_avaliacao_completa(conn, cand)
            conn.commit()
            return self._json(200, {"ok": True})

        if method == "GET" and path == "/api/candidato/quiz":
            if not cand["cargo_desejado_id"]:
                return self._json(400, {"erro": "Nenhum cargo de interesse selecionado"})
            questoes = [
                {"id": q["id"], "pergunta": q["pergunta"], "opcoes": json.loads(q["opcoes"])}
                for q in conn.execute(
                    "SELECT * FROM questoes WHERE cargo_id=? ORDER BY id",
                    (cand["cargo_desejado_id"],),
                ).fetchall()
            ]
            return self._json(200, {"questoes": questoes})

        if method == "POST" and path == "/api/candidato/quiz":
            if not cand["cargo_desejado_id"]:
                return self._json(400, {"erro": "Nenhum cargo de interesse selecionado"})
            d = self._body()
            respostas = d.get("respostas") or {}
            questoes = conn.execute(
                "SELECT * FROM questoes WHERE cargo_id=?", (cand["cargo_desejado_id"],)
            ).fetchall()
            if not questoes:
                return self._json(400, {"erro": "Este cargo não possui teste de conhecimento"})
            acertos = 0
            detalhe = {}
            if not isinstance(respostas, dict):
                respostas = {}
            for q in questoes:
                marcada = _para_int(respostas.get(str(q["id"])))
                if marcada is not None and marcada == q["correta"]:
                    acertos += 1
                detalhe[str(q["id"])] = {"marcada": marcada, "correta": q["correta"]}
            conn.execute(
                "INSERT INTO resultados_quiz (candidato_id, cargo_id, acertos, total, payload)"
                " VALUES (?,?,?,?,?)"
                " ON CONFLICT(candidato_id, cargo_id) DO UPDATE SET"
                " acertos=excluded.acertos, total=excluded.total,"
                " payload=excluded.payload, criado_em=datetime('now')",
                (cand["id"], cand["cargo_desejado_id"], acertos, len(questoes),
                 json.dumps(detalhe)),
            )
            registrar_evento(
                conn, cand["id"], "quiz",
                "Teste de conhecimento concluído: %d de %d acertos" % (acertos, len(questoes)),
                cand["nome"],
            )
            notificar_avaliacao_completa(conn, cand)
            conn.commit()
            return self._json(200, {"acertos": acertos, "total": len(questoes)})

        if method == "POST" and path == "/api/candidato/autoavaliacao":
            d = self._body()
            respostas = d.get("respostas") or []
            if not isinstance(respostas, list):
                respostas = []
            # só aceita competências do cargo de interesse do candidato
            validas = {
                row["id"] for row in conn.execute(
                    "SELECT id FROM competencias WHERE cargo_id=?",
                    (cand["cargo_desejado_id"],),
                ).fetchall()
            }
            for r in respostas:
                if not isinstance(r, dict):
                    continue
                comp_id = _para_int(r.get("competencia_id"))
                if comp_id not in validas:
                    continue
                nivel = max(0, min(5, _para_int(r.get("nivel"), 0)))
                conn.execute(
                    "INSERT INTO autoavaliacoes (candidato_id, competencia_id, nivel_atual)"
                    " VALUES (?,?,?)"
                    " ON CONFLICT(candidato_id, competencia_id) DO UPDATE SET"
                    " nivel_atual=excluded.nivel_atual",
                    (cand["id"], comp_id, nivel),
                )
            registrar_evento(
                conn, cand["id"], "autoavaliacao",
                "Autoavaliação de competências respondida", cand["nome"],
            )
            notificar_avaliacao_completa(conn, cand)
            conn.commit()
            return self._json(200, {"ok": True})

        if method == "POST" and path == "/api/candidato/curriculo":
            d = self._body()
            nome_arq = re.sub(r"[^A-Za-z0-9._-]", "_", d.get("filename") or "curriculo.pdf")
            try:
                dados = base64.b64decode(d.get("data") or "")
            except ValueError:
                return self._json(400, {"erro": "Arquivo inválido"})
            if len(dados) > 8 * 1024 * 1024:
                return self._json(400, {"erro": "Arquivo maior que 8 MB"})
            destino = "cand%d_%s" % (cand["id"], nome_arq)
            with open(os.path.join(UPLOAD_DIR, destino), "wb") as f:
                f.write(dados)
            conn.execute(
                "UPDATE candidatos SET curriculo_arquivo=? WHERE id=?",
                (destino, cand["id"]),
            )
            registrar_evento(conn, cand["id"], "curriculo", "Currículo enviado", cand["nome"])
            conn.commit()
            # análise automática por IA em segundo plano (quando configurada)
            if config_get(conn, "anthropic_api_key") and destino.lower().endswith(".pdf"):
                import threading
                threading.Thread(
                    target=analisar_curriculo_em_segundo_plano,
                    args=(cand["id"],), daemon=True,
                ).start()
            return self._json(200, {"ok": True})

        # ---- painel do dono do software ----
        if method == "GET" and path == "/api/dono/setup":
            return self._json(200, {"precisa_setup": not config_get(conn, "senha_dono")})

        if method == "POST" and path == "/api/dono/setup":
            if config_get(conn, "senha_dono"):
                return self._json(403, {"erro": "O dono já foi cadastrado"})
            d = self._body()
            senha = d.get("senha") or ""
            if len(senha) < 8:
                return self._json(400, {"erro": "A senha do dono deve ter ao menos 8 caracteres"})
            config_set(conn, "senha_dono", hash_senha(senha))
            token = secrets.token_urlsafe(24)
            conn.execute("INSERT INTO sessoes_dono (token) VALUES (?)", (token,))
            conn.commit()
            return self._json(200, {"token": token})

        if method == "POST" and path == "/api/dono/login":
            if self._login_bloqueado("dono"):
                return self._json(429, {"erro": "Muitas tentativas. Aguarde alguns minutos e tente de novo."})
            d = self._body()
            salva = config_get(conn, "senha_dono")
            if not senha_confere(d.get("senha") or "", salva):
                self._registrar_falha_login("dono")
                return self._json(401, {"erro": "Senha incorreta"})
            self._limpar_falhas_login("dono")
            novo_hash = migrar_hash_se_preciso(d.get("senha") or "", salva)
            if novo_hash:
                config_set(conn, "senha_dono", novo_hash)
            token = secrets.token_urlsafe(24)
            conn.execute("INSERT INTO sessoes_dono (token) VALUES (?)", (token,))
            conn.commit()
            return self._json(200, {"token": token})

        if path.startswith("/api/dono/") and path not in (
            "/api/dono/setup", "/api/dono/login"
        ):
            token_dono = self.headers.get("X-Dono-Token", "")
            if not token_dono or not conn.execute(
                "SELECT 1 FROM sessoes_dono WHERE token=?", (token_dono,)
            ).fetchone():
                return self._json(401, {"erro": "Acesso restrito ao dono do software"})

        if method == "GET" and path == "/api/dono/visao":
            gestores_lista = []
            for g in conn.execute("SELECT * FROM gestores ORDER BY nome").fetchall():
                alvo = (g["local"] or "").strip().lower()
                cand_count = 0
                for r in conn.execute("SELECT local FROM candidatos").fetchall():
                    if g["is_admin"] or not alvo \
                            or (r["local"] or "").strip().lower() == alvo:
                        cand_count += 1
                gestores_lista.append({
                    "id": g["id"], "nome": g["nome"], "login": g["login"],
                    "email": g["email"], "local": g["local"],
                    "admin": bool(g["is_admin"]), "criado_em": g["criado_em"],
                    "candidatos_visiveis": cand_count,
                    "modulos": modulos_do_gestor(g),
                })
            locais = {}
            for r in conn.execute("SELECT local, tipo FROM candidatos").fetchall():
                chave = (r["local"] or "(sem local)").strip()
                locais.setdefault(chave, {"candidatos": 0, "internos": 0})
                locais[chave]["candidatos"] += 1
                if r["tipo"] == "interno":
                    locais[chave]["internos"] += 1
            backups = sorted(
                f for f in (os.listdir(BACKUP_DIR) if os.path.isdir(BACKUP_DIR) else [])
                if f.endswith(".db")
            )
            log_final = ""
            try:
                with open("/tmp/rh-server.log", encoding="utf-8", errors="replace") as f:
                    log_final = "".join(f.readlines()[-25:])
            except OSError:
                pass
            return self._json(200, {
                "totais": {
                    "gestores": conn.execute("SELECT COUNT(*) c FROM gestores").fetchone()["c"],
                    "candidatos": conn.execute("SELECT COUNT(*) c FROM candidatos").fetchone()["c"],
                    "internos": conn.execute(
                        "SELECT COUNT(*) c FROM candidatos WHERE tipo='interno'"
                    ).fetchone()["c"],
                    "vagas": conn.execute("SELECT COUNT(*) c FROM vagas").fetchone()["c"],
                    "avaliacoes_completas": conn.execute(
                        "SELECT COUNT(*) c FROM candidatos WHERE notificado_completo=1"
                    ).fetchone()["c"],
                },
                "gestores": gestores_lista,
                "locais": [
                    {"local": k, **v} for k, v in sorted(locais.items())
                ],
                "sistema": {
                    "versao": "1.0",
                    "python": sys.version.split()[0],
                    "banco_mb": round(os.path.getsize(DB_PATH) / 1048576, 2)
                    if os.path.isfile(DB_PATH) else 0,
                    "backups": backups[-5:],
                    "ia_configurada": bool(config_get(conn, "anthropic_api_key")),
                    "smtp_configurado": bool(config_get(conn, "smtp_host")),
                    "log": log_final,
                },
            })

        if method == "POST" and path == "/api/dono/entrar-como":
            d = self._body()
            g = conn.execute(
                "SELECT * FROM gestores WHERE id=?", (d.get("gestor_id"),)
            ).fetchone()
            if not g:
                return self._json(404, {"erro": "Gestor não encontrado"})
            token = secrets.token_urlsafe(24)
            conn.execute(
                "INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)",
                (token, g["id"]),
            )
            conn.commit()
            return self._json(200, {
                "token": token, "nome": g["nome"], "login": g["login"],
                "local": g["local"], "admin": bool(g["is_admin"]),
                "modulos": modulos_do_gestor(g),
            })

        if method == "POST" and path == "/api/dono/modulos":
            d = self._body()
            modulo = d.get("modulo")
            if modulo not in MODULOS_DISPONIVEIS:
                return self._json(400, {"erro": "Módulo desconhecido"})
            g = conn.execute(
                "SELECT * FROM gestores WHERE id=?", (d.get("gestor_id"),)
            ).fetchone()
            if not g:
                return self._json(404, {"erro": "Gestor não encontrado"})
            mods = set(modulos_do_gestor(g))
            if d.get("ativo"):
                mods.add(modulo)
            else:
                mods.discard(modulo)
            conn.execute(
                "UPDATE gestores SET modulos=? WHERE id=?",
                (json.dumps(sorted(mods)), g["id"]),
            )
            conn.commit()
            return self._json(200, {"ok": True, "modulos": sorted(mods)})

        if method == "POST" and path == "/api/dono/gestor-senha":
            d = self._body()
            nova = d.get("nova") or ""
            if len(nova) < 6:
                return self._json(400, {"erro": "A nova senha deve ter ao menos 6 caracteres"})
            g = conn.execute(
                "SELECT * FROM gestores WHERE id=?", (d.get("gestor_id"),)
            ).fetchone()
            if not g:
                return self._json(404, {"erro": "Gestor não encontrado"})
            conn.execute(
                "UPDATE gestores SET senha=? WHERE id=?", (hash_senha(nova), g["id"])
            )
            conn.commit()
            return self._json(200, {"ok": True})

        if method == "POST" and path == "/api/dono/senha":
            d = self._body()
            if not senha_confere(d.get("atual") or "", config_get(conn, "senha_dono")):
                return self._json(400, {"erro": "Senha atual incorreta"})
            nova = d.get("nova") or ""
            if len(nova) < 8:
                return self._json(400, {"erro": "A nova senha deve ter ao menos 8 caracteres"})
            config_set(conn, "senha_dono", hash_senha(nova))
            conn.commit()
            return self._json(200, {"ok": True})

        if path == "/api/dono/billing":
            if method == "GET":
                registros = {
                    r["local"]: dict(r)
                    for r in conn.execute("SELECT * FROM billing").fetchall()
                }
                locais = sorted({
                    (r["local"] or "").strip()
                    for r in conn.execute(
                        "SELECT local FROM gestores UNION SELECT local FROM candidatos"
                    ).fetchall()
                    if (r["local"] or "").strip()
                })
                linhas = []
                for local in locais:
                    reg = registros.get(local, {})
                    linhas.append({
                        "local": local,
                        "plano": reg.get("plano", ""),
                        "valor": reg.get("valor", ""),
                        "status": reg.get("status", "ativo"),
                        "notas": reg.get("notas", ""),
                    })
                return self._json(200, {"clientes": linhas})
            if method == "POST":
                d = self._body()
                local = (d.get("local") or "").strip()
                if not local:
                    return self._json(400, {"erro": "Informe o local/cliente"})
                conn.execute(
                    "INSERT INTO billing (local, plano, valor, status, notas)"
                    " VALUES (?,?,?,?,?)"
                    " ON CONFLICT(local) DO UPDATE SET plano=excluded.plano,"
                    " valor=excluded.valor, status=excluded.status,"
                    " notas=excluded.notas, atualizado_em=datetime('now')",
                    (local, (d.get("plano") or "").strip(),
                     (d.get("valor") or "").strip(),
                     d.get("status") if d.get("status") in ("ativo", "teste", "inadimplente", "cancelado") else "ativo",
                     (d.get("notas") or "").strip()),
                )
                conn.commit()
                return self._json(200, {"ok": True})

        # ---- gestor: configuração inicial (cria o primeiro administrador) ----
        if method == "GET" and path == "/api/gestor/setup":
            existe = bool(conn.execute("SELECT 1 FROM gestores LIMIT 1").fetchone())
            return self._json(200, {"precisa_setup": not existe})

        if method == "POST" and path == "/api/gestor/setup":
            if conn.execute("SELECT 1 FROM gestores LIMIT 1").fetchone():
                return self._json(403, {"erro": "O administrador já foi cadastrado"})
            d = self._body()
            nome = (d.get("nome") or "").strip()
            login = (d.get("login") or "").strip().lower()
            senha = d.get("senha") or ""
            if not nome or not login:
                return self._json(400, {"erro": "Nome e login são obrigatórios"})
            if len(senha) < 6:
                return self._json(400, {"erro": "A senha deve ter ao menos 6 caracteres"})
            conn.execute(
                "INSERT INTO gestores (login, senha, nome, email, local, is_admin)"
                " VALUES (?,?,?,?,?,1)",
                (login, hash_senha(senha), nome, (d.get("email") or "").strip(),
                 (d.get("local") or "").strip()),
            )
            gestor_id = conn.execute(
                "SELECT id FROM gestores WHERE login=?", (login,)
            ).fetchone()["id"]
            token = secrets.token_urlsafe(24)
            conn.execute(
                "INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)",
                (token, gestor_id),
            )
            conn.commit()
            return self._json(200, {
                "token": token, "nome": nome, "login": login,
                "local": (d.get("local") or "").strip(), "admin": True,
            })

        # ---- gestor ----
        if method == "POST" and path == "/api/gestor/login":
            if self._login_bloqueado("gestor"):
                return self._json(429, {"erro": "Muitas tentativas. Aguarde alguns minutos e tente de novo."})
            d = self._body()
            gestor_row = conn.execute(
                "SELECT * FROM gestores WHERE lower(login)=lower(?)",
                ((d.get("login") or "").strip(),),
            ).fetchone()
            senha_ok = gestor_row and senha_confere(d.get("senha") or "", gestor_row["senha"])
            if not senha_ok:
                self._registrar_falha_login("gestor")
                return self._json(401, {"erro": "Login ou senha incorretos"})
            self._limpar_falhas_login("gestor")
            # atualiza o hash para o formato novo (PBKDF2), se ainda for o antigo
            novo_hash = migrar_hash_se_preciso(d.get("senha") or "", gestor_row["senha"])
            if novo_hash:
                conn.execute("UPDATE gestores SET senha=? WHERE id=?", (novo_hash, gestor_row["id"]))
            token = secrets.token_urlsafe(24)
            conn.execute(
                "INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)",
                (token, gestor_row["id"]),
            )
            conn.commit()
            return self._json(200, {
                "token": token,
                "nome": gestor_row["nome"],
                "login": gestor_row["login"],
                "local": gestor_row["local"],
                "modulos": modulos_do_gestor(gestor_row),
                "admin": bool(gestor_row["is_admin"]),
            })

        # ---- esqueci minha senha (gestor) ----
        if method == "POST" and path == "/api/gestor/esqueci-senha":
            if self._login_bloqueado("reset"):
                return self._json(429, {"erro": "Muitas tentativas. Aguarde alguns minutos."})
            self._registrar_falha_login("reset")
            d = self._body()
            ident = (d.get("login") or "").strip()
            alvo = conn.execute(
                "SELECT * FROM gestores WHERE lower(login)=lower(?) OR lower(email)=lower(?)",
                (ident, ident),
            ).fetchone()
            enviou = False
            if alvo and (alvo["email"] or "").strip() and config_get(conn, "smtp_host"):
                token_reset = secrets.token_urlsafe(24)
                conn.execute(
                    "UPDATE gestores SET reset_token=?, reset_expira=datetime('now','+2 hours')"
                    " WHERE id=?",
                    (token_reset, alvo["id"]),
                )
                link = "%s/gestor?reset=%s" % (url_publica(conn, self.headers.get("Host")), token_reset)
                ok, _ = enviar_email(
                    conn, alvo["email"], "Redefinição de senha - Bússola",
                    "Olá, %s!\n\nRecebemos um pedido para redefinir a sua senha de gestor.\n"
                    "Abra o link abaixo (válido por 2 horas) para criar uma nova senha:\n\n%s\n\n"
                    "Se você não pediu isso, ignore este e-mail.\n\nEquipe Bússola"
                    % (alvo["nome"], link),
                )
                enviou = ok
                conn.commit()
            # resposta idêntica com ou sem conta (não revela quem tem cadastro)
            return self._json(200, {"ok": True, "enviou": enviou})

        if method == "POST" and path == "/api/gestor/redefinir-senha":
            d = self._body()
            token_reset = (d.get("token") or "").strip()
            nova = d.get("nova") or ""
            if len(nova) < 6:
                return self._json(400, {"erro": "A nova senha deve ter ao menos 6 caracteres"})
            alvo = conn.execute(
                "SELECT * FROM gestores WHERE reset_token=? AND reset_token != ''"
                " AND reset_expira >= datetime('now')",
                (token_reset,),
            ).fetchone()
            if not alvo:
                return self._json(400, {"erro": "Link de redefinição inválido ou expirado. Peça um novo."})
            conn.execute(
                "UPDATE gestores SET senha=?, reset_token='', reset_expira='' WHERE id=?",
                (hash_senha(nova), alvo["id"]),
            )
            conn.commit()
            return self._json(200, {"ok": True})

        gestor = None
        if path.startswith("/api/gestor/") and path not in (
            "/api/gestor/login", "/api/gestor/esqueci-senha", "/api/gestor/redefinir-senha"
        ):
            gestor = self._gestor(conn)
            if not gestor:
                return self._json(401, {"erro": "Acesso restrito ao gestor"})

        # objetos globais de configuração: só o administrador cria, edita ou
        # remove cargos, competências e avaliações (evita dano em cascata).
        CONFIG_GLOBAL = ("/api/gestor/cargo", "/api/gestor/competencia",
                         "/api/gestor/questao", "/api/gestor/pergunta-entrevista")
        if gestor and method in ("POST", "DELETE") and any(
            path == p or path.startswith(p + "/") for p in CONFIG_GLOBAL
        ):
            if not gestor["is_admin"]:
                return self._json(403, {"erro": "Apenas o administrador altera cargos e avaliações"})

        if method == "POST" and path == "/api/gestor/senha":
            d = self._body()
            if not senha_confere(d.get("atual") or "", gestor["senha"]):
                return self._json(400, {"erro": "Senha atual incorreta"})
            nova = d.get("nova") or ""
            if len(nova) < 6:
                return self._json(400, {"erro": "A nova senha deve ter ao menos 6 caracteres"})
            conn.execute(
                "UPDATE gestores SET senha=? WHERE id=?",
                (hash_senha(nova), gestor["id"]),
            )
            conn.commit()
            return self._json(200, {"ok": True})

        # -- módulo Diagnóstico de Competências (liberado pelo dono) --
        if path.startswith("/api/gestor/diagnostico"):
            if "diagnostico" not in modulos_do_gestor(gestor):
                return self._json(403, {"erro": "Módulo não liberado para esta conta. Fale com o administrador do sistema."})

            if method == "GET" and path == "/api/gestor/diagnostico":
                conteudo = None
                caminho_conteudo = os.path.join(DOCS_DIR, "diagnostico-conteudo.json")
                if os.path.isfile(caminho_conteudo):
                    with open(caminho_conteudo, encoding="utf-8") as f:
                        conteudo = json.load(f)
                sessoes = []
                for s in conn.execute(
                    "SELECT id, colaborador, cargo, unidade, status, local,"
                    " criado_em, atualizado_em FROM sessoes_diagnostico"
                    " ORDER BY atualizado_em DESC"
                ).fetchall():
                    if gestor_ve_local(gestor, s["local"]):
                        sessoes.append(dict(s))
                por_unidade = {}
                concluidas = 0
                for s in sessoes:
                    chave = s["unidade"] or "(sem unidade)"
                    por_unidade[chave] = por_unidade.get(chave, 0) + 1
                    if s["status"] == "concluida":
                        concluidas += 1
                return self._json(200, {
                    "sessoes": sessoes,
                    "conteudo": conteudo,
                    "stats": {"total": len(sessoes), "concluidas": concluidas,
                              "por_unidade": por_unidade},
                    "arquivos": [
                        {"nome": n, "titulo": t} for n, t in ARQUIVOS_DIAGNOSTICO.items()
                        if os.path.isfile(os.path.join(DOCS_DIR, n))
                    ],
                })

            m = re.match(r"^/api/gestor/diagnostico/sessao/(\d+)$", path)
            if m and method == "GET":
                s = conn.execute(
                    "SELECT * FROM sessoes_diagnostico WHERE id=?", (int(m.group(1)),)
                ).fetchone()
                if not s or not gestor_ve_local(gestor, s["local"]):
                    return self._json(404, {"erro": "Sessão não encontrada"})
                d = dict(s)
                d["dados"] = json.loads(d["dados"] or "{}")
                return self._json(200, {"sessao": d})

            if m and method == "DELETE":
                s = conn.execute(
                    "SELECT local FROM sessoes_diagnostico WHERE id=?", (int(m.group(1)),)
                ).fetchone()
                if not s or not gestor_ve_local(gestor, s["local"]):
                    return self._json(404, {"erro": "Sessão não encontrada"})
                conn.execute("DELETE FROM sessoes_diagnostico WHERE id=?", (int(m.group(1)),))
                conn.commit()
                return self._json(200, {"ok": True})

            if method == "POST" and path == "/api/gestor/diagnostico/sessao":
                d = self._body()
                colaborador = (d.get("colaborador") or "").strip()
                if not colaborador:
                    return self._json(400, {"erro": "Informe o nome do colaborador"})
                status = d.get("status") if d.get("status") in ("rascunho", "concluida") else "rascunho"
                dados = json.dumps(d.get("dados") or {})
                if d.get("id"):
                    atual = conn.execute(
                        "SELECT local FROM sessoes_diagnostico WHERE id=?", (d["id"],)
                    ).fetchone()
                    if not atual or not gestor_ve_local(gestor, atual["local"]):
                        return self._json(404, {"erro": "Sessão não encontrada"})
                    conn.execute(
                        "UPDATE sessoes_diagnostico SET colaborador=?, cargo=?,"
                        " unidade=?, status=?, dados=?, atualizado_em=datetime('now')"
                        " WHERE id=?",
                        (colaborador, (d.get("cargo") or "").strip(),
                         (d.get("unidade") or "").strip(), status, dados, d["id"]),
                    )
                    sessao_id = d["id"]
                else:
                    cur = conn.execute(
                        "INSERT INTO sessoes_diagnostico"
                        " (gestor_id, colaborador, cargo, unidade, status, dados, local)"
                        " VALUES (?,?,?,?,?,?,?)",
                        (gestor["id"], colaborador, (d.get("cargo") or "").strip(),
                         (d.get("unidade") or "").strip(), status, dados,
                         (gestor["local"] or "").strip()),
                    )
                    sessao_id = cur.lastrowid
                conn.commit()
                return self._json(200, {"ok": True, "id": sessao_id})

            m = re.match(r"^/api/gestor/diagnostico/arquivo/([\w.\-]+)$", path)
            if m and method == "GET":
                nome = m.group(1)
                if nome not in ARQUIVOS_DIAGNOSTICO:
                    return self._json(404, {"erro": "Arquivo não encontrado"})
                caminho = os.path.join(DOCS_DIR, nome)
                if not os.path.isfile(caminho):
                    return self._json(404, {"erro": "Arquivo não disponível no servidor"})
                with open(caminho, "rb") as f:
                    corpo = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition",
                                 'attachment; filename="%s"' % nome)
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)
                return None

            return self._json(404, {"erro": "Não encontrado"})

        # -- gestão de contas de gestor (somente administrador) --
        if path.startswith("/api/gestor/gestores"):
            if not gestor["is_admin"]:
                return self._json(403, {"erro": "Apenas o administrador gerencia contas de gestor"})
            if method == "GET" and path == "/api/gestor/gestores":
                lista = [
                    {"id": g["id"], "login": g["login"], "nome": g["nome"],
                     "email": g["email"], "local": g["local"],
                     "admin": bool(g["is_admin"]),
                     "modulos": modulos_do_gestor(g)}
                    for g in conn.execute("SELECT * FROM gestores ORDER BY nome").fetchall()
                ]
                return self._json(200, {"gestores": lista})
            if method == "POST" and path == "/api/gestor/gestores":
                d = self._body()
                login = (d.get("login") or "").strip().lower()
                nome = (d.get("nome") or "").strip()
                if not nome or (not d.get("id") and not login):
                    return self._json(400, {"erro": "Nome e login são obrigatórios"})
                senha = d.get("senha") or ""
                if d.get("id"):
                    conn.execute(
                        "UPDATE gestores SET nome=?, email=?, local=?, is_admin=? WHERE id=?",
                        (nome, (d.get("email") or "").strip(),
                         (d.get("local") or "").strip(),
                         1 if d.get("admin") else 0, d["id"]),
                    )
                    if senha:
                        if len(senha) < 6:
                            return self._json(400, {"erro": "A senha deve ter ao menos 6 caracteres"})
                        conn.execute(
                            "UPDATE gestores SET senha=? WHERE id=?",
                            (hash_senha(senha), d["id"]),
                        )
                else:
                    if len(senha) < 6:
                        return self._json(400, {"erro": "A senha deve ter ao menos 6 caracteres"})
                    if conn.execute(
                        "SELECT 1 FROM gestores WHERE lower(login)=?", (login,)
                    ).fetchone():
                        return self._json(400, {"erro": "Já existe um gestor com este login"})
                    conn.execute(
                        "INSERT INTO gestores (login, senha, nome, email, local, is_admin)"
                        " VALUES (?,?,?,?,?,?)",
                        (login, hash_senha(senha), nome,
                         (d.get("email") or "").strip(),
                         (d.get("local") or "").strip(), 1 if d.get("admin") else 0),
                    )
                conn.commit()
                return self._json(200, {"ok": True})
            m = re.match(r"^/api/gestor/gestores/(\d+)$", path)
            if m and method == "DELETE":
                alvo = int(m.group(1))
                if alvo == gestor["id"]:
                    return self._json(400, {"erro": "Você não pode excluir a sua própria conta"})
                conn.execute("DELETE FROM gestores WHERE id=?", (alvo,))
                conn.commit()
                return self._json(200, {"ok": True})

        # -- vagas e pipeline de seleção --
        if method == "GET" and path == "/api/gestor/vagas":
            vagas = []
            for v in conn.execute(
                "SELECT v.*, c.nome AS cargo_nome FROM vagas v"
                " JOIN cargos c ON c.id = v.cargo_id ORDER BY v.criado_em DESC"
            ).fetchall():
                contagem = {e: 0 for e in ETAPAS_PIPELINE}
                for r in conn.execute(
                    "SELECT ca.etapa, ca.candidato_id FROM candidaturas ca WHERE ca.vaga_id=?",
                    (v["id"],),
                ).fetchall():
                    cand_row = conn.execute(
                        "SELECT * FROM candidatos WHERE id=?", (r["candidato_id"],)
                    ).fetchone()
                    if cand_row and gestor_ve_candidato(gestor, cand_row):
                        contagem[r["etapa"]] = contagem.get(r["etapa"], 0) + 1
                vagas.append({
                    "id": v["id"], "titulo": v["titulo"], "local": v["local"],
                    "pais": v["pais"] or "",
                    "descricao": v["descricao"], "status": v["status"],
                    "cargo_id": v["cargo_id"], "cargo_nome": v["cargo_nome"],
                    "criado_em": v["criado_em"], "etapas": contagem,
                    "total": sum(contagem.values()),
                })
            return self._json(200, {"vagas": vagas})

        if method == "POST" and path == "/api/gestor/vaga":
            d = self._body()
            titulo = (d.get("titulo") or "").strip()
            if not titulo or not d.get("cargo_id"):
                return self._json(400, {"erro": "Título e cargo são obrigatórios"})
            status = d.get("status") if d.get("status") in ("aberta", "pausada", "encerrada") else "aberta"
            if d.get("id"):
                conn.execute(
                    "UPDATE vagas SET titulo=?, cargo_id=?, local=?, pais=?, descricao=?,"
                    " status=? WHERE id=?",
                    (titulo, d["cargo_id"], (d.get("local") or "").strip(),
                     (d.get("pais") or "").strip(),
                     (d.get("descricao") or "").strip(), status, d["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO vagas (titulo, cargo_id, local, pais, descricao, status)"
                    " VALUES (?,?,?,?,?,?)",
                    (titulo, d["cargo_id"], (d.get("local") or "").strip(),
                     (d.get("pais") or "").strip(),
                     (d.get("descricao") or "").strip(), status),
                )
            conn.commit()
            return self._json(200, {"ok": True})

        m = re.match(r"^/api/gestor/vaga/(\d+)$", path)
        if m and method == "DELETE":
            conn.execute("DELETE FROM vagas WHERE id=?", (int(m.group(1)),))
            conn.commit()
            return self._json(200, {"ok": True})

        m = re.match(r"^/api/gestor/vaga/(\d+)/pipeline$", path)
        if m and method == "GET":
            vaga = conn.execute(
                "SELECT v.*, c.nome AS cargo_nome FROM vagas v"
                " JOIN cargos c ON c.id = v.cargo_id WHERE v.id=?",
                (int(m.group(1)),),
            ).fetchone()
            if not vaga:
                return self._json(404, {"erro": "Vaga não encontrada"})
            linhas = []
            for ca in conn.execute(
                "SELECT * FROM candidaturas WHERE vaga_id=?", (vaga["id"],)
            ).fetchall():
                cand_row = conn.execute(
                    "SELECT * FROM candidatos WHERE id=?", (ca["candidato_id"],)
                ).fetchone()
                if not cand_row or not gestor_ve_candidato(gestor, cand_row):
                    continue
                match = match_completo(conn, cand_row, vaga["cargo_id"])
                linhas.append({
                    "candidatura_id": ca["id"],
                    "candidato_id": cand_row["id"],
                    "nome": cand_row["nome"],
                    "email": cand_row["email"],
                    "local": cand_row["local"],
                    "etapa": ca["etapa"],
                    "motivo_reprovacao": ca["motivo_reprovacao"],
                    "match": match["geral"] if match else None,
                    "atualizado_em": ca["atualizado_em"],
                })
            linhas.sort(key=lambda l: -(l["match"] if l["match"] is not None else -1))
            return self._json(200, {
                "vaga": {k: vaga[k] for k in
                         ("id", "titulo", "local", "descricao", "status",
                          "cargo_id", "cargo_nome")},
                "etapas": ETAPAS_PIPELINE,
                "nomes_etapas": NOMES_ETAPAS,
                "candidaturas": linhas,
            })

        if method == "POST" and path == "/api/gestor/candidatura":
            d = self._body()
            ca = conn.execute(
                "SELECT ca.*, v.titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                " WHERE ca.id=?", (d.get("id"),),
            ).fetchone()
            if not ca:
                return self._json(404, {"erro": "Candidatura não encontrada"})
            etapa = d.get("etapa")
            if etapa not in ETAPAS_PIPELINE:
                return self._json(400, {"erro": "Etapa inválida"})
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (ca["candidato_id"],)
            ).fetchone()
            if not cand_row or not gestor_ve_candidato(gestor, cand_row):
                return self._json(404, {"erro": "Candidato não encontrado"})
            motivo = (d.get("motivo") or "").strip()
            conn.execute(
                "UPDATE candidaturas SET etapa=?, motivo_reprovacao=?,"
                " atualizado_em=datetime('now') WHERE id=?",
                (etapa, motivo if etapa == "reprovado" else "", ca["id"]),
            )
            registrar_evento(
                conn, cand_row["id"], "etapa",
                "Vaga %s: movido para %s%s" % (
                    ca["titulo"], NOMES_ETAPAS[etapa],
                    (" (" + motivo + ")") if etapa == "reprovado" and motivo else "",
                ),
                gestor["nome"],
            )
            aviso_email = ""
            if d.get("notificar"):
                variaveis = variaveis_candidato(conn, cand_row, self.headers.get("Host"))
                variaveis["vaga"] = ca["titulo"]
                variaveis["etapa"] = NOMES_ETAPAS[etapa]
                modelo = templates_email(conn).get(
                    "etapa_" + etapa, TEMPLATES_PADRAO["etapa_inscrito"]
                )
                ok, msg = enviar_email(
                    conn, cand_row["email"],
                    renderizar(modelo["assunto"], variaveis),
                    renderizar(modelo["corpo"], variaveis),
                )
                registrar_evento(
                    conn, cand_row["id"], "email",
                    ("E-mail de atualização enviado" if ok
                     else "Falha ao enviar e-mail: %s" % msg),
                )
                if not ok:
                    aviso_email = msg
            conn.commit()
            return self._json(200, {"ok": True, "aviso_email": aviso_email})

        if method == "POST" and path == "/api/gestor/candidatura/adicionar":
            d = self._body()
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (d.get("candidato_id"),)
            ).fetchone()
            vaga = conn.execute(
                "SELECT * FROM vagas WHERE id=?", (d.get("vaga_id"),)
            ).fetchone()
            if not cand_row or not vaga or not gestor_ve_candidato(gestor, cand_row):
                return self._json(404, {"erro": "Candidato ou vaga não encontrados"})
            if conn.execute(
                "SELECT 1 FROM candidaturas WHERE candidato_id=? AND vaga_id=?",
                (cand_row["id"], vaga["id"]),
            ).fetchone():
                return self._json(400, {"erro": "O candidato já está nesta vaga"})
            conn.execute(
                "INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)",
                (cand_row["id"], vaga["id"]),
            )
            registrar_evento(
                conn, cand_row["id"], "candidatura",
                "Adicionado à vaga: %s" % vaga["titulo"], gestor["nome"],
            )
            conn.commit()
            return self._json(200, {"ok": True})

        # -- roteiro de entrevista e teste de conhecimento por cargo --
        m = re.match(r"^/api/gestor/cargo/(\d+)/avaliacoes$", path)
        if m and method == "GET":
            cargo_id = int(m.group(1))
            perguntas = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM perguntas_entrevista WHERE cargo_id=? ORDER BY ordem, id",
                    (cargo_id,),
                ).fetchall()
            ]
            questoes = [
                {"id": q["id"], "pergunta": q["pergunta"],
                 "opcoes": json.loads(q["opcoes"]), "correta": q["correta"]}
                for q in conn.execute(
                    "SELECT * FROM questoes WHERE cargo_id=? ORDER BY id", (cargo_id,)
                ).fetchall()
            ]
            return self._json(200, {"perguntas": perguntas, "questoes": questoes})

        if method == "POST" and path == "/api/gestor/pergunta-entrevista":
            d = self._body()
            texto = (d.get("texto") or "").strip()
            if not texto or not d.get("cargo_id"):
                return self._json(400, {"erro": "Cargo e texto da pergunta são obrigatórios"})
            if d.get("id"):
                conn.execute(
                    "UPDATE perguntas_entrevista SET texto=? WHERE id=?", (texto, d["id"])
                )
            else:
                conn.execute(
                    "INSERT INTO perguntas_entrevista (cargo_id, texto) VALUES (?,?)",
                    (d["cargo_id"], texto),
                )
            conn.commit()
            return self._json(200, {"ok": True})

        m = re.match(r"^/api/gestor/pergunta-entrevista/(\d+)$", path)
        if m and method == "DELETE":
            conn.execute("DELETE FROM perguntas_entrevista WHERE id=?", (int(m.group(1)),))
            conn.commit()
            return self._json(200, {"ok": True})

        if method == "POST" and path == "/api/gestor/questao":
            d = self._body()
            pergunta = (d.get("pergunta") or "").strip()
            opcoes = [o.strip() for o in (d.get("opcoes") or []) if o.strip()]
            correta = int(d.get("correta", 0))
            if not pergunta or not d.get("cargo_id") or len(opcoes) < 2:
                return self._json(400, {"erro": "Informe a pergunta e ao menos 2 opções"})
            if correta < 0 or correta >= len(opcoes):
                return self._json(400, {"erro": "Opção correta inválida"})
            if d.get("id"):
                conn.execute(
                    "UPDATE questoes SET pergunta=?, opcoes=?, correta=? WHERE id=?",
                    (pergunta, json.dumps(opcoes, ensure_ascii=False), correta, d["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO questoes (cargo_id, pergunta, opcoes, correta)"
                    " VALUES (?,?,?,?)",
                    (d["cargo_id"], pergunta, json.dumps(opcoes, ensure_ascii=False), correta),
                )
            conn.commit()
            return self._json(200, {"ok": True})

        m = re.match(r"^/api/gestor/questao/(\d+)$", path)
        if m and method == "DELETE":
            conn.execute("DELETE FROM questoes WHERE id=?", (int(m.group(1)),))
            conn.commit()
            return self._json(200, {"ok": True})

        # -- entrevista estruturada (scorecard) --
        if method == "POST" and path == "/api/gestor/entrevista":
            d = self._body()
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (d.get("candidato_id"),)
            ).fetchone()
            if not cand_row or not gestor_ve_candidato(gestor, cand_row):
                return self._json(404, {"erro": "Candidato não encontrado"})
            notas = d.get("notas") or []
            validas = [n for n in notas if 1 <= int(n.get("nota", 0)) <= 5]
            if not validas:
                return self._json(400, {"erro": "Informe ao menos uma nota de 1 a 5"})
            media = sum(int(n["nota"]) for n in validas) / len(validas)
            conn.execute(
                "INSERT INTO entrevistas (candidato_id, cargo_id, gestor_nome, payload, media)"
                " VALUES (?,?,?,?,?)",
                (cand_row["id"], d.get("cargo_id"), gestor["nome"],
                 json.dumps({"notas": validas, "observacao": (d.get("observacao") or "").strip()},
                            ensure_ascii=False),
                 round(media, 2)),
            )
            registrar_evento(
                conn, cand_row["id"], "entrevista",
                "Entrevista registrada: média %.1f de 5" % media, gestor["nome"],
            )
            conn.commit()
            return self._json(200, {"ok": True, "media": round(media, 2)})

        # -- anotações --
        if method == "POST" and path == "/api/gestor/anotacao":
            d = self._body()
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (d.get("candidato_id"),)
            ).fetchone()
            texto = (d.get("texto") or "").strip()
            if not cand_row or not gestor_ve_candidato(gestor, cand_row) or not texto:
                return self._json(400, {"erro": "Candidato e texto são obrigatórios"})
            registrar_evento(conn, cand_row["id"], "anotacao", texto, gestor["nome"])
            conn.commit()
            return self._json(200, {"ok": True})

        # -- integrações (IA e e-mail) --
        if method == "POST" and path == "/api/gestor/integracoes/teste":
            if not gestor["is_admin"]:
                return self._json(403, {"erro": "Apenas o administrador configura integrações"})
            if not config_get(conn, "smtp_host"):
                return self._json(400, {"erro": "Preencha e salve os dados de SMTP antes de testar."})
            destino = ((gestor["email"] or "").strip()
                       or config_get(conn, "smtp_remetente")
                       or config_get(conn, "smtp_usuario"))
            if not destino:
                return self._json(400, {"erro": "Cadastre um e-mail na sua conta de gestor para receber o teste."})
            ok, msg = enviar_email(
                conn, destino, "Teste de e-mail - Bússola",
                "Este é um e-mail de teste da Bússola.\n\nSe você recebeu esta mensagem, "
                "o envio automático está funcionando: confirmações de inscrição, avisos de "
                "etapa e de novos candidatos, lembretes e redefinição de senha já operam.\n\n"
                "Equipe Bússola",
            )
            if ok:
                return self._json(200, {"ok": True, "destino": destino})
            return self._json(400, {"erro": "Falha ao enviar: %s" % msg})

        if path == "/api/gestor/integracoes":
            if not gestor["is_admin"]:
                return self._json(403, {"erro": "Apenas o administrador configura integrações"})
            if method == "GET":
                chave = config_get(conn, "anthropic_api_key")
                return self._json(200, {
                    "ia_configurada": bool(chave),
                    "ia_final": chave[-6:] if chave else "",
                    "smtp_host": config_get(conn, "smtp_host"),
                    "smtp_porta": config_get(conn, "smtp_porta") or "587",
                    "smtp_usuario": config_get(conn, "smtp_usuario"),
                    "smtp_remetente": config_get(conn, "smtp_remetente"),
                    "smtp_senha_configurada": bool(config_get(conn, "smtp_senha")),
                    "url_publica": config_get(conn, "url_publica"),
                    "retencao_meses": config_get(conn, "retencao_meses") or "0",
                })
            if method == "POST":
                d = self._body()
                if "anthropic_api_key" in d:
                    config_set(conn, "anthropic_api_key", (d.get("anthropic_api_key") or "").strip())
                for chave in ("smtp_host", "smtp_porta", "smtp_usuario",
                              "smtp_remetente", "url_publica", "retencao_meses"):
                    if chave in d:
                        config_set(conn, chave, (d.get(chave) or "").strip())
                if d.get("smtp_senha"):
                    config_set(conn, "smtp_senha", d["smtp_senha"])
                conn.commit()
                return self._json(200, {"ok": True})

        # -- análise de currículo por IA --
        m = re.match(r"^/api/gestor/ia/curriculo/(\d+)$", path)
        if m and method == "POST":
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)
            ).fetchone()
            if not cand_row or not gestor_ve_candidato(gestor, cand_row):
                return self._json(404, {"erro": "Candidato não encontrado"})
            try:
                analise, erro = analisar_curriculo_ia(conn, cand_row)
            except Exception as exc:  # noqa: BLE001
                return self._json(500, {"erro": "Falha na análise: %s" % exc})
            if erro:
                return self._json(400, {"erro": erro})
            conn.execute(
                "UPDATE candidatos SET analise_ia=? WHERE id=?",
                (json.dumps(analise, ensure_ascii=False), cand_row["id"]),
            )
            registrar_evento(
                conn, cand_row["id"], "ia",
                "Currículo analisado por IA (aderência %s%%)" % analise.get("aderencia_curriculo"),
                gestor["nome"],
            )
            conn.commit()
            return self._json(200, {"analise": analise})

        # -- tags do banco de talentos --
        m = re.match(r"^/api/gestor/candidato/(\d+)/tags$", path)
        if m and method == "POST":
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)
            ).fetchone()
            if not cand_row or not gestor_ve_candidato(gestor, cand_row):
                return self._json(404, {"erro": "Candidato não encontrado"})
            d = self._body()
            tags = sorted({
                t.strip().lower() for t in (d.get("tags") or []) if t.strip()
            })[:20]
            conn.execute(
                "UPDATE candidatos SET tags=? WHERE id=?",
                (json.dumps(tags, ensure_ascii=False), cand_row["id"]),
            )
            conn.commit()
            return self._json(200, {"ok": True, "tags": tags})

        if method == "GET" and path == "/api/gestor/tags":
            todas = set()
            for r in conn.execute("SELECT tags FROM candidatos").fetchall():
                try:
                    todas.update(json.loads(r["tags"] or "[]"))
                except ValueError:
                    pass
            return self._json(200, {"tags": sorted(todas)})

        # -- radar de talentos: candidatos do banco com match alto para a vaga --
        m = re.match(r"^/api/gestor/vaga/(\d+)/sugestoes$", path)
        if m and method == "GET":
            vaga = conn.execute(
                "SELECT * FROM vagas WHERE id=?", (int(m.group(1)),)
            ).fetchone()
            if not vaga:
                return self._json(404, {"erro": "Vaga não encontrada"})
            ja_na_vaga = {
                r["candidato_id"] for r in conn.execute(
                    "SELECT candidato_id FROM candidaturas WHERE vaga_id=?",
                    (vaga["id"],),
                ).fetchall()
            }
            sugestoes = []
            for cand_row in conn.execute(
                "SELECT * FROM candidatos WHERE anonimizado=0"
            ).fetchall():
                if cand_row["id"] in ja_na_vaga:
                    continue
                if not gestor_ve_candidato(gestor, cand_row):
                    continue
                match = match_completo(conn, cand_row, vaga["cargo_id"])
                if match and match["geral"] >= 60:
                    sugestoes.append({
                        "candidato_id": cand_row["id"],
                        "nome": cand_row["nome"],
                        "local": cand_row["local"],
                        "match": match["geral"],
                    })
            sugestoes.sort(key=lambda s: -s["match"])
            return self._json(200, {"sugestoes": sugestoes[:10]})

        # -- e-mail manual para o candidato --
        if method == "POST" and path == "/api/gestor/email":
            d = self._body()
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (d.get("candidato_id"),)
            ).fetchone()
            assunto = (d.get("assunto") or "").strip()
            corpo = (d.get("corpo") or "").strip()
            if not cand_row or not gestor_ve_candidato(gestor, cand_row):
                return self._json(404, {"erro": "Candidato não encontrado"})
            if not assunto or not corpo:
                return self._json(400, {"erro": "Assunto e mensagem são obrigatórios"})
            variaveis = variaveis_candidato(conn, cand_row, self.headers.get("Host"))
            ok, msg = enviar_email(
                conn, cand_row["email"],
                renderizar(assunto, variaveis), renderizar(corpo, variaveis),
            )
            if not ok:
                return self._json(400, {"erro": "Não foi possível enviar: " + msg})
            registrar_evento(
                conn, cand_row["id"], "email",
                "E-mail enviado pelo gestor: %s" % assunto, gestor["nome"],
            )
            conn.commit()
            return self._json(200, {"ok": True})

        # -- anonimização (LGPD) --
        m = re.match(r"^/api/gestor/candidato/(\d+)/anonimizar$", path)
        if m and method == "POST":
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)
            ).fetchone()
            if not cand_row or not gestor_ve_candidato(gestor, cand_row):
                return self._json(404, {"erro": "Candidato não encontrado"})
            anonimizar_candidato(conn, cand_row, gestor["nome"])
            conn.commit()
            return self._json(200, {"ok": True})

        # -- modelos de e-mail (administrador) --
        if path == "/api/gestor/templates":
            if not gestor["is_admin"]:
                return self._json(403, {"erro": "Apenas o administrador edita os modelos"})
            if method == "GET":
                return self._json(200, {
                    "templates": templates_email(conn),
                    "nomes": NOMES_TEMPLATES,
                    "padrao": TEMPLATES_PADRAO,
                })
            if method == "POST":
                d = self._body()
                novos = {}
                for chave in TEMPLATES_PADRAO:
                    item = (d.get("templates") or {}).get(chave) or {}
                    novos[chave] = {
                        "assunto": (item.get("assunto") or "").strip(),
                        "corpo": (item.get("corpo") or "").strip(),
                    }
                config_set(conn, "templates_email", json.dumps(novos, ensure_ascii=False))
                conn.commit()
                return self._json(200, {"ok": True})

        # -- relatórios --
        if method == "GET" and path == "/api/gestor/relatorios":
            visiveis = [
                r for r in conn.execute("SELECT * FROM candidatos").fetchall()
                if gestor_ve_candidato(gestor, r)
            ]
            ids_visiveis = {r["id"] for r in visiveis}
            # funil por vaga
            funil = []
            for v in conn.execute(
                "SELECT v.*, c.nome AS cargo_nome FROM vagas v"
                " JOIN cargos c ON c.id=v.cargo_id ORDER BY v.criado_em DESC"
            ).fetchall():
                etapas = {e: 0 for e in ETAPAS_PIPELINE}
                for ca in conn.execute(
                    "SELECT * FROM candidaturas WHERE vaga_id=?", (v["id"],)
                ).fetchall():
                    if ca["candidato_id"] in ids_visiveis:
                        etapas[ca["etapa"]] += 1
                total = sum(etapas.values())
                funil.append({
                    "vaga": v["titulo"], "status": v["status"],
                    "total": total, "etapas": etapas,
                })
            # candidatos por mês (últimos 6 meses)
            por_mes = {}
            for r in visiveis:
                mes = (r["criado_em"] or "")[:7]
                if mes:
                    por_mes[mes] = por_mes.get(mes, 0) + 1
            meses = sorted(por_mes)[-6:]
            # distribuição de perfis e conclusão
            disc_dist, base_dist = {}, {}
            completos = 0
            for r in visiveis:
                if r["notificado_completo"]:
                    completos += 1
                for t in conn.execute(
                    "SELECT tipo, payload FROM resultados_teste WHERE candidato_id=?",
                    (r["id"],),
                ).fetchall():
                    dom = (json.loads(t["payload"]) or {}).get("dominante")
                    if not dom:
                        continue
                    if t["tipo"] == "disc":
                        disc_dist[dom] = disc_dist.get(dom, 0) + 1
                    else:
                        base_dist[dom] = base_dist.get(dom, 0) + 1
            # tempo médio até contratação
            dias = []
            for ca in conn.execute(
                "SELECT * FROM candidaturas WHERE etapa='contratado'"
            ).fetchall():
                if ca["candidato_id"] in ids_visiveis:
                    try:
                        import datetime as dt
                        inicio = dt.datetime.fromisoformat(ca["criado_em"])
                        fim = dt.datetime.fromisoformat(ca["atualizado_em"])
                        dias.append((fim - inicio).days)
                    except ValueError:
                        pass
            return self._json(200, {
                "total_candidatos": len(visiveis),
                "avaliacoes_completas": completos,
                "funil": funil,
                "por_mes": [{"mes": m2, "total": por_mes[m2]} for m2 in meses],
                "disc": disc_dist,
                "base": base_dist,
                "tempo_medio_contratacao": round(sum(dias) / len(dias)) if dias else None,
                "contratados": len(dias),
            })

        # -- feed de atividades (visão geral) --
        if method == "GET" and path == "/api/gestor/atividades":
            atividades = []
            for ev in conn.execute(
                "SELECT e.*, c.nome AS candidato_nome, c.local AS candidato_local"
                " FROM eventos e JOIN candidatos c ON c.id = e.candidato_id"
                " ORDER BY e.criado_em DESC, e.id DESC LIMIT 120"
            ).fetchall():
                cand_row = conn.execute(
                    "SELECT * FROM candidatos WHERE id=?", (ev["candidato_id"],)
                ).fetchone()
                if not cand_row or not gestor_ve_candidato(gestor, cand_row):
                    continue
                atividades.append({
                    "candidato_id": ev["candidato_id"],
                    "candidato_nome": ev["candidato_nome"],
                    "tipo": ev["tipo"],
                    "texto": ev["texto"],
                    "autor": ev["autor"],
                    "criado_em": ev["criado_em"],
                })
                if len(atividades) >= 30:
                    break
            return self._json(200, {"atividades": atividades})

        if method == "GET" and path == "/api/gestor/candidatos":
            lista = []
            for cand_row in conn.execute(
                "SELECT * FROM candidatos ORDER BY criado_em DESC"
            ).fetchall():
                if gestor_ve_candidato(gestor, cand_row):
                    lista.append(resumo_candidato(conn, cand_row))
            return self._json(200, {"candidatos": lista})

        m = re.match(r"^/api/gestor/candidato/(\d+)$", path)
        if m:
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)
            ).fetchone()
            if not cand_row or not gestor_ve_candidato(gestor, cand_row):
                return self._json(404, {"erro": "Candidato não encontrado"})
            if method == "GET":
                resumo = resumo_candidato(conn, cand_row)
                resumo["eventos"] = [
                    dict(r) for r in conn.execute(
                        "SELECT tipo, texto, autor, criado_em FROM eventos"
                        " WHERE candidato_id=? ORDER BY criado_em DESC, id DESC",
                        (cand_row["id"],),
                    ).fetchall()
                ]
                resumo["analise_ia"] = (
                    json.loads(cand_row["analise_ia"]) if cand_row["analise_ia"] else None
                )
                # recrutamento interno: match contra todos os cargos
                resumo["matches_cargos"] = sorted(
                    [
                        {
                            "cargo_id": c["id"], "cargo_nome": c["nome"],
                            "nivel": c["nivel"],
                            "match": (match_completo(conn, cand_row, c["id"]) or {}).get("geral"),
                        }
                        for c in conn.execute("SELECT * FROM cargos").fetchall()
                    ],
                    key=lambda x: -(x["match"] if x["match"] is not None else -1),
                )
                # roteiro de entrevista do cargo de interesse (para o scorecard)
                if cand_row["cargo_desejado_id"]:
                    resumo["perguntas_entrevista"] = [
                        dict(r) for r in conn.execute(
                            "SELECT id, texto FROM perguntas_entrevista"
                            " WHERE cargo_id=? ORDER BY ordem, id",
                            (cand_row["cargo_desejado_id"],),
                        ).fetchall()
                    ]
                else:
                    resumo["perguntas_entrevista"] = []
                return self._json(200, resumo)
            if method == "DELETE":
                conn.execute("DELETE FROM candidatos WHERE id=?", (cand_row["id"],))
                conn.commit()
                return self._json(200, {"ok": True})

        m = re.match(r"^/api/gestor/curriculo/(\d+)$", path)
        if m and method == "GET":
            cand_row = conn.execute(
                "SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)
            ).fetchone()
            if (not cand_row or not cand_row["curriculo_arquivo"]
                    or not gestor_ve_candidato(gestor, cand_row)):
                return self._json(404, {"erro": "Currículo não encontrado"})
            full = os.path.join(UPLOAD_DIR, cand_row["curriculo_arquivo"])
            if not os.path.isfile(full):
                return self._json(404, {"erro": "Arquivo não encontrado"})
            with open(full, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header(
                "Content-Disposition",
                'attachment; filename="%s"' % cand_row["curriculo_arquivo"],
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return None

        if method == "POST" and path == "/api/gestor/cargo":
            d = self._body()
            nome = (d.get("nome") or "").strip()
            if not nome:
                return self._json(400, {"erro": "Nome do cargo é obrigatório"})
            disc_alvo = d.get("disc_alvo") if d.get("disc_alvo") in ("D", "I", "S", "C") else ""
            base_alvo = d.get("base_alvo") if d.get("base_alvo") in ("B", "A", "S", "E") else ""
            if d.get("id"):
                conn.execute(
                    "UPDATE cargos SET nome=?, area=?, nivel=?, descricao=?,"
                    " disc_alvo=?, base_alvo=? WHERE id=?",
                    (nome, d.get("area") or "", d.get("nivel") or "",
                     d.get("descricao") or "", disc_alvo, base_alvo, d["id"]),
                )
                cargo_id = d["id"]
            else:
                cur = conn.execute(
                    "INSERT INTO cargos (nome, area, nivel, descricao, disc_alvo, base_alvo)"
                    " VALUES (?,?,?,?,?,?)",
                    (nome, d.get("area") or "", d.get("nivel") or "",
                     d.get("descricao") or "", disc_alvo, base_alvo),
                )
                cargo_id = cur.lastrowid
            conn.commit()
            return self._json(200, {"ok": True, "id": cargo_id})

        m = re.match(r"^/api/gestor/cargo/(\d+)$", path)
        if m and method == "DELETE":
            conn.execute("DELETE FROM cargos WHERE id=?", (int(m.group(1)),))
            conn.commit()
            return self._json(200, {"ok": True})

        if method == "POST" and path == "/api/gestor/competencia":
            d = self._body()
            nome = (d.get("nome") or "").strip()
            if not nome or not d.get("cargo_id"):
                return self._json(400, {"erro": "Cargo e nome da competência são obrigatórios"})
            tipo = d.get("tipo") if d.get("tipo") in RECOMENDACAO_POR_TIPO else "tecnica"
            req = max(1, min(5, int(d.get("nivel_requerido", 3))))
            obrig = 1 if d.get("obrigatoria") else 0
            if d.get("id"):
                conn.execute(
                    "UPDATE competencias SET nome=?, tipo=?, nivel_requerido=?, obrigatoria=?"
                    " WHERE id=?",
                    (nome, tipo, req, obrig, d["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO competencias (cargo_id, nome, tipo, nivel_requerido, obrigatoria)"
                    " VALUES (?,?,?,?,?)",
                    (d["cargo_id"], nome, tipo, req, obrig),
                )
            conn.commit()
            return self._json(200, {"ok": True})

        m = re.match(r"^/api/gestor/competencia/(\d+)$", path)
        if m and method == "DELETE":
            conn.execute("DELETE FROM competencias WHERE id=?", (int(m.group(1)),))
            conn.commit()
            return self._json(200, {"ok": True})

        if method == "GET" and path == "/api/gestor/matriz":
            qs = parse_qs(urlparse(self.path).query)
            cargo_id = int(qs.get("cargo_id", ["0"])[0] or 0)
            if not cargo_id:
                return self._json(400, {"erro": "Informe o cargo"})
            cargo_row = conn.execute(
                "SELECT * FROM cargos WHERE id=?", (cargo_id,)
            ).fetchone()
            linhas = []
            for cand_row in conn.execute(
                "SELECT * FROM candidatos ORDER BY nome"
            ).fetchall():
                if not gestor_ve_candidato(gestor, cand_row):
                    continue
                mg = matriz_gaps(conn, cand_row["id"], cargo_id)
                if mg:
                    match = match_completo(conn, cand_row, cargo_id, gaps=mg)
                    linhas.append(
                        {
                            "candidato_id": cand_row["id"],
                            "nome": cand_row["nome"],
                            "local": cand_row["local"],
                            "aderencia": mg["aderencia"],
                            "match": match["geral"] if match else None,
                            "status": mg["status"],
                            "respondeu": mg["respondeu_autoavaliacao"],
                            "itens": mg["itens"],
                        }
                    )
            linhas.sort(key=lambda l: -(l["match"] if l["match"] is not None else -1))
            cargo = cargo_com_competencias(conn, cargo_id)
            return self._json(200, {"cargo": cargo, "linhas": linhas})

        return self._json(404, {"erro": "Rota não encontrada"})


def backup_diario():
    """Guarda uma cópia diária do banco em backups/ e mantém as 14 mais recentes."""
    if not os.path.isfile(DB_PATH):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    import datetime
    import shutil

    destino = os.path.join(
        BACKUP_DIR, "rh-%s.db" % datetime.date.today().isoformat()
    )
    if not os.path.isfile(destino):
        origem = sqlite3.connect(DB_PATH)
        copia = sqlite3.connect(destino)
        with copia:
            origem.backup(copia)
        copia.close()
        origem.close()
        print("Backup diário criado: %s" % destino)
    antigos = sorted(
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith("rh-") and f.endswith(".db")
    )
    for velho in antigos[:-14]:
        os.remove(os.path.join(BACKUP_DIR, velho))


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    backup_diario()
    init_db()
    import threading
    threading.Thread(target=rotina_automatica, daemon=True).start()
    servidor = ThreadingHTTPServer(("0.0.0.0", porta), Handler)
    print("Sistema de RH rodando em http://localhost:%d" % porta)
    servidor.serve_forever()


if __name__ == "__main__":
    main()
