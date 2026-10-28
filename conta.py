"""Conta da empresa: consentimento para ligações e mensagens automáticas (TCPA),
acesso de suporte do dono, exportação de todos os dados e encerramento da conta.

1. Consentimento (TCPA)
   O cadastro público tem uma caixa separada, desmarcada por padrão. Guardamos no
   candidato a data, o texto exato mostrado (no idioma dele), o IP e a origem
   ("formulario" ou "importado"). Candidatos importados (CSV ou e-mail do Indeed)
   ficam com origem "importado" e sem data de consentimento.
   Cada empresa escolhe se a fila automática de ligações liga só para quem
   consentiu (padrão: desligado, que mantém o comportamento de antes). A regra
   fica em pode_ligar_automatico(conn, linha), chamada pela fila do voz.py.
   O candidato pode pedir "Parar ligações e mensagens" no portal: registramos a
   revogação, marcamos as candidaturas como nao_ligar e gravamos um evento.

2. Suporte do dono ("Entrar no painel como administrador")
   O dono gera um código de uso único (2 minutos). A aba nova do /gestor troca o
   código por uma sessão de 2 horas (POST /api/gestor/suporte/entrar) de um gestor
   oculto da empresa (suporte=1, is_admin=1, aprovado=1), que nunca entra com senha,
   não aparece nas listas da empresa e não conta no limite do plano. Tudo fica na
   trilha de auditoria com quem = "Suporte (dono)".

3. Dados e conta
   Exportação em ZIP (em segundo plano), com JSON e CSV de candidatos, candidaturas,
   eventos, testes, entrevistas, ligações (metadados e transcrições), onboarding e
   os arquivos (currículos e PDFs de modelos). Dados sensíveis só mascarados e só
   com a senha do administrador. O link vale 24 horas e só para quem pediu.
   Encerrar a conta: status cancelada com exclusão em 30 dias; o dono recebe um
   e-mail e pode cancelar a exclusão no painel. A rotina diária apaga de vez as
   empresas cuja data passou (linhas por empresa_id, arquivos e pastas).
"""
import csv
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import sqlite3
import sys
import threading
import time
import zipfile
from datetime import datetime, timedelta

srv = None  # módulo server, injetado por ligar()

QUEM_SUPORTE = "Suporte (dono)"
QUEM_DONO = "Dono da plataforma"
HORAS_SUPORTE = 2
MINUTOS_CODIGO = 2
HORAS_EXPORTACAO = 24
DIAS_EXCLUSAO = 30
PADRAO = {"so_com_consentimento": False}

# texto exato da caixa de consentimento (o mesmo de i18n-candidato.js, cad_contato)
TEXTO_CONSENTIMENTO = {
    "en": ("I agree that {empresa} may call and text me about my application, including with automated "
           "technology and an AI assistant, at the number I provided. Calls may be recorded. Consent is not a "
           "condition of employment. Reply STOP to opt out of texts."),
    "pt": ("Concordo que {empresa} pode me ligar e enviar mensagens de texto sobre a minha candidatura, inclusive "
           "com tecnologia automatizada e uma assistente de IA, no número que informei. As ligações podem ser "
           "gravadas. O consentimento não é condição para a contratação. Responda STOP para deixar de receber "
           "mensagens."),
    "es": ("Acepto que {empresa} me llame y me envíe mensajes de texto sobre mi postulación, incluso con tecnología "
           "automatizada y una asistente de IA, al número que proporcioné. Las llamadas pueden ser grabadas. El "
           "consentimiento no es una condición para el empleo. Responde STOP para dejar de recibir mensajes."),
}

# frase sugerida para o anúncio da vaga no Indeed (bloco de copiar em Configurações)
TEXTO_ANUNCIO = {
    "en": ("By applying, you agree that {empresa} may call and text you about your application, including with "
           "automated technology and an AI assistant, at the number you provide. Calls may be recorded. Consent is "
           "not a condition of employment. Message and data rates may apply. Reply STOP to opt out of texts."),
    "pt": ("Ao se candidatar, você concorda que {empresa} pode ligar e enviar mensagens de texto sobre a sua "
           "candidatura, inclusive com tecnologia automatizada e uma assistente de IA, no número informado. As "
           "ligações podem ser gravadas. O consentimento não é condição para a contratação. Podem ser cobradas "
           "tarifas de mensagens e dados. Responda STOP para deixar de receber mensagens."),
    "es": ("Al postularte, aceptas que {empresa} te llame y te envíe mensajes de texto sobre tu postulación, incluso "
           "con tecnología automatizada y una asistente de IA, al número que proporciones. Las llamadas pueden ser "
           "grabadas. El consentimiento no es una condición para el empleo. Pueden aplicarse tarifas de mensajes y "
           "datos. Responde STOP para dejar de recibir mensajes."),
}

# colunas que nunca saem na exportação (acesso e segredos)
COLUNAS_SECRETAS = {"token", "agenda_token", "senha", "reset_token", "reset_expira", "codigo_hash",
                    "sensiveis", "dados_cifrados"}

_trava_export = threading.Lock()


def ligar(modulo_server):
    global srv
    srv = modulo_server


# ------------------------------------------------------------------ banco

def _colunas(c, tabela):
    return {r[1] for r in c.execute("PRAGMA table_info(%s)" % tabela).fetchall()}


def init_conta(c):
    """Colunas e tabelas do módulo (roda depois de empresas.init_empresas)."""
    for tabela, coluna, ddl in (
        ("candidatos", "consentimento_contato_em", "TEXT DEFAULT ''"),
        ("candidatos", "consentimento_contato_texto", "TEXT DEFAULT ''"),
        ("candidatos", "consentimento_contato_ip", "TEXT DEFAULT ''"),
        ("candidatos", "origem_consentimento", "TEXT DEFAULT ''"),
        ("candidatos", "contato_revogado_em", "TEXT DEFAULT ''"),
        ("gestores", "suporte", "INTEGER DEFAULT 0"),
        ("sessoes_gestor", "expira_em", "TEXT DEFAULT ''"),
        ("sessoes_gestor", "suporte", "INTEGER DEFAULT 0"),
        ("empresas", "exclusao_em", "TEXT DEFAULT ''"),
        ("empresas", "encerrada_em", "TEXT DEFAULT ''"),
        ("empresas", "encerrada_por", "TEXT DEFAULT ''"),
        ("empresas", "status_anterior", "TEXT DEFAULT ''"),
    ):
        if coluna not in _colunas(c, tabela):
            c.execute("ALTER TABLE %s ADD COLUMN %s %s" % (tabela, coluna, ddl))
    c.execute(
        "CREATE TABLE IF NOT EXISTS suporte_codigos ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " codigo_hash TEXT UNIQUE NOT NULL,"
        " expira_em TEXT NOT NULL,"
        " usado_em TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS exportacoes ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " gestor_id INTEGER NOT NULL,"
        " status TEXT NOT NULL DEFAULT 'preparando',"  # preparando | pronto | erro | expirado
        " sensivel INTEGER NOT NULL DEFAULT 0,"
        " arquivo TEXT DEFAULT '',"
        " tamanho INTEGER DEFAULT 0,"
        " erro TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " pronto_em TEXT DEFAULT '',"
        " expira_em TEXT DEFAULT '')"
    )
    c.execute("CREATE INDEX IF NOT EXISTS ix_exportacoes_empresa ON exportacoes(empresa_id, id)")
    # registro das exclusões definitivas (fica depois que a empresa some)
    c.execute(
        "CREATE TABLE IF NOT EXISTS exclusoes_empresa ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " nome TEXT DEFAULT '',"
        " resumo TEXT DEFAULT '{}',"
        " excluida_em TEXT DEFAULT (datetime('now')))"
    )


def _agora_sql(delta=None):
    t = datetime.utcnow() + (delta or timedelta(0))
    return t.strftime("%Y-%m-%d %H:%M:%S")


def _get(row, chave, padrao=None):
    try:
        if isinstance(row, dict):
            return row.get(chave, padrao)
        return row[chave] if chave in row.keys() else padrao
    except (KeyError, IndexError, TypeError):
        return padrao


def _idioma(valor):
    v = str(valor or "").strip().lower()[:2]
    return v if v in ("pt", "en", "es") else "en"


def _resp(h, status, dados):
    h._json(status, dados)
    return True


def _chave(empresa_id):
    return "conta:%d" % int(empresa_id)


def config(conn, empresa_id):
    cfg = dict(PADRAO)
    try:
        cfg.update(json.loads(srv.config_get(conn, _chave(empresa_id)) or "{}"))
    except ValueError:
        pass
    cfg["so_com_consentimento"] = bool(cfg.get("so_com_consentimento"))
    return cfg


def _nome_empresa(conn, empresa_id):
    r = conn.execute("SELECT nome FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    return r["nome"] if r else ""


# ------------------------------------------------------- 1. consentimento

def texto_consentimento(nome_empresa, idioma):
    return TEXTO_CONSENTIMENTO[_idioma(idioma)].format(empresa=nome_empresa or "")


def registrar_consentimento_cadastro(conn, candidato_id, dados, ip, empresa_id):
    """Cadastro público: guarda a origem "formulario" e, se a caixa veio marcada
    (consentimento_contato: true), a data, o texto exato e o IP."""
    conn.execute("UPDATE candidatos SET origem_consentimento='formulario' WHERE id=?", (candidato_id,))
    if dados.get("consentimento_contato") is not True:
        return False
    texto = texto_consentimento(_nome_empresa(conn, empresa_id), dados.get("idioma"))
    conn.execute(
        "UPDATE candidatos SET consentimento_contato_em=datetime('now'), consentimento_contato_texto=?,"
        " consentimento_contato_ip=?, contato_revogado_em='' WHERE id=?",
        (texto, (ip or "")[:60], candidato_id),
    )
    srv.registrar_evento(conn, candidato_id, "cadastro", "Autorizou ligações e mensagens automáticas")
    return True


def marcar_importado(conn, candidato_id):
    """entrada.py (CSV ou e-mail): importado, sem consentimento escrito."""
    conn.execute("UPDATE candidatos SET origem_consentimento='importado' WHERE id=?", (candidato_id,))


def resumo_consentimento(cand):
    """Selo da ficha do candidato."""
    revogado = _get(cand, "contato_revogado_em", "") or ""
    em = _get(cand, "consentimento_contato_em", "") or ""
    origem = _get(cand, "origem_consentimento", "") or ""
    if revogado:
        estado = "revogado"
    elif em:
        estado = "consentiu"
    elif origem == "importado":
        estado = "importado"
    else:
        estado = "sem_consentimento"
    return {"estado": estado, "em": em, "origem": origem, "revogado_em": revogado,
            "texto": _get(cand, "consentimento_contato_texto", "") or ""}


def estado_candidato(cand):
    """Para o portal do candidato (sem IP)."""
    r = resumo_consentimento(cand)
    return {"estado": r["estado"], "em": r["em"], "revogado_em": r["revogado_em"]}


def pode_ligar_automatico(conn, candidato_row):
    """Fila automática de ligações: False quando o candidato revogou o contato, ou
    quando a empresa só liga para quem consentiu e ele não consentiu.
    Aceita uma linha de candidatos (id, empresa_id) ou de candidaturas/fila
    (candidato_id). Ligações manuais do gestor não passam por aqui."""
    cid = _get(candidato_row, "candidato_id") or _get(candidato_row, "id")
    if not cid:
        return False
    c = conn.execute(
        "SELECT empresa_id, consentimento_contato_em, contato_revogado_em FROM candidatos WHERE id=?", (cid,)
    ).fetchone()
    if not c:
        return False
    if c["contato_revogado_em"]:
        return False
    if not c["empresa_id"] or not config(conn, c["empresa_id"])["so_com_consentimento"]:
        return True
    return bool(c["consentimento_contato_em"])


def revogar_contato(conn, cand, ip=""):
    if cand["contato_revogado_em"] if "contato_revogado_em" in cand.keys() else False:
        return False
    conn.execute("UPDATE candidatos SET contato_revogado_em=datetime('now') WHERE id=?", (cand["id"],))
    conn.execute("UPDATE candidaturas SET voz_status='nao_ligar', voz_proxima='' WHERE candidato_id=?",
                 (cand["id"],))
    srv.registrar_evento(conn, cand["id"], "sistema", "Pediu para não receber ligações nem mensagens automáticas",
                         autor="candidato")
    srv.seguranca.registrar(conn, "contato_revogado", None, "candidato:%d" % cand["id"], ip,
                            empresa_id=cand["empresa_id"], quem=(cand["nome"] or "")[:80])
    conn.commit()
    return True


# ---------------------------------------------------------- 2. suporte do dono

def _hash(codigo):
    return hashlib.sha256((codigo or "").encode("utf-8")).hexdigest()


def gestor_suporte(conn, empresa_id):
    """Gestor oculto de suporte da empresa (cria na primeira vez). Senha inutilizável."""
    r = conn.execute("SELECT * FROM gestores WHERE empresa_id=? AND suporte=1", (empresa_id,)).fetchone()
    if r:
        if not (r["is_admin"] and r["aprovado"]):
            conn.execute("UPDATE gestores SET is_admin=1, aprovado=1 WHERE id=?", (r["id"],))
        return conn.execute("SELECT * FROM gestores WHERE id=?", (r["id"],)).fetchone()
    login = "suporte.%d.%s" % (int(empresa_id), secrets.token_hex(6))
    gid = conn.execute(
        "INSERT INTO gestores (login, senha, nome, email, local, is_admin, aprovado, empresa_id, suporte)"
        " VALUES (?,?,?,'','',1,1,?,1)",
        (login, "!suporte-sem-senha", QUEM_SUPORTE, empresa_id),
    ).lastrowid
    return conn.execute("SELECT * FROM gestores WHERE id=?", (gid,)).fetchone()


def criar_codigo_suporte(conn, empresa_id, ip=""):
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    if not e:
        return None, "Empresa não encontrada"
    if e["status"] not in ("ativa", "teste"):
        return None, "O acesso desta empresa está suspenso. Fale com o suporte."
    g = gestor_suporte(conn, empresa_id)
    codigo = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO suporte_codigos (empresa_id, codigo_hash, expira_em) VALUES (?,?,?)",
                 (empresa_id, _hash(codigo), _agora_sql(timedelta(minutes=MINUTOS_CODIGO))))
    conn.commit()
    srv.seguranca.registrar(conn, "suporte_iniciado", g, e["nome"], ip, empresa_id=empresa_id, quem=QUEM_SUPORTE)
    return codigo, None


def trocar_codigo(conn, codigo, ip=""):
    """Código de uso único -> sessão de suporte de 2 horas. Devolve (payload, erro)."""
    if not codigo or len(codigo) > 200:
        return None, "Código de suporte inválido ou expirado"
    r = conn.execute(
        "SELECT * FROM suporte_codigos WHERE codigo_hash=? AND usado_em='' AND expira_em > ?",
        (_hash(codigo), _agora_sql()),
    ).fetchone()
    if not r:
        return None, "Código de suporte inválido ou expirado"
    cur = conn.execute("UPDATE suporte_codigos SET usado_em=datetime('now') WHERE id=? AND usado_em=''", (r["id"],))
    if cur.rowcount == 0:
        return None, "Código de suporte inválido ou expirado"
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (r["empresa_id"],)).fetchone()
    if not e or e["status"] not in ("ativa", "teste"):
        conn.commit()
        return None, "O acesso desta empresa está suspenso. Fale com o suporte."
    g = gestor_suporte(conn, e["id"])
    token = secrets.token_urlsafe(24)
    expira = _agora_sql(timedelta(hours=HORAS_SUPORTE))
    conn.execute("INSERT INTO sessoes_gestor (token, gestor_id, expira_em, suporte) VALUES (?,?,?,1)",
                 (token, g["id"], expira))
    conn.commit()
    srv.seguranca.registrar(conn, "suporte_entrou", g, e["nome"], ip, empresa_id=e["id"], quem=QUEM_SUPORTE)
    return {
        "token": token, "nome": g["nome"], "login": g["login"], "local": "", "admin": True,
        "modulos": srv.empresas.modulos(e), "idioma": "",
        "empresa": {"nome": e["nome"], "slug": e["slug"]},
        "suporte": {"ativo": True, "empresa": e["nome"], "expira_em": expira},
    }, None


def sessao_de_suporte(gestor):
    return bool(_get(gestor, "sessao_suporte", 0)) or bool(_get(gestor, "suporte", 0))


def estado_sessao(conn, h, gestor):
    token = h.headers.get("X-Gestor-Token", "")
    s = conn.execute("SELECT expira_em, suporte FROM sessoes_gestor WHERE token=?", (token,)).fetchone()
    suporte = bool(s and s["suporte"]) or bool(_get(gestor, "suporte", 0))
    return {"suporte": suporte, "empresa": _get(gestor, "empresa_nome", "") or "",
            "expira_em": (s["expira_em"] if s else "") or ""}


# --------------------------------------------------------- 3. exportação

def _limpar_linha(d, extra=()):
    return {k: v for k, v in d.items() if k not in COLUNAS_SECRETAS and k not in extra}


def _mascarar(v):
    s = str(v if v is not None else "")
    if not s:
        return ""
    if len(s) <= 4:
        return "•" * len(s)
    return "•" * (len(s) - 4) + s[-4:]


def _mascarar_dict(d):
    if isinstance(d, dict):
        return {k: (_mascarar_dict(v) if isinstance(v, (dict, list)) else
                    (v if isinstance(v, bool) or k in ("metodo", "tipo_conta") else _mascarar(v)))
                for k, v in d.items()}
    if isinstance(d, list):
        return [_mascarar_dict(x) for x in d]
    return _mascarar(d)


def _csv(linhas):
    buf = io.StringIO()
    chaves = []
    for linha in linhas:
        for k in linha:
            if k not in chaves:
                chaves.append(k)
    w = csv.writer(buf)
    w.writerow(chaves)
    for linha in linhas:
        w.writerow([json.dumps(linha.get(k), ensure_ascii=False) if isinstance(linha.get(k), (dict, list))
                    else ("" if linha.get(k) is None else linha.get(k)) for k in chaves])
    return buf.getvalue()


def _tabela_existe(conn, nome):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nome,)).fetchone() is not None


def _linhas(conn, sql, params):
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except sqlite3.OperationalError:
        return []


def montar_dados(conn, empresa_id, sensivel=False):
    """{nome_do_arquivo: [linhas]} só da empresa. Segredos e campos sensíveis
    nunca saem em claro: com sensivel=True, saem mascarados."""
    eid = int(empresa_id)
    cands = "SELECT id FROM candidatos WHERE empresa_id=%d" % eid
    dados = {}

    def por_candidato(tabela):
        if not _tabela_existe(conn, tabela):
            return []
        return [_limpar_linha(x) for x in _linhas(conn, "SELECT * FROM %s WHERE candidato_id IN (%s) ORDER BY id"
                                                  % (tabela, cands), ())]

    def por_empresa(tabela):
        if not _tabela_existe(conn, tabela):
            return []
        return [_limpar_linha(x) for x in _linhas(conn, "SELECT * FROM %s WHERE empresa_id=? ORDER BY id" % tabela,
                                                  (eid,))]

    dados["candidatos"] = []
    for c in _linhas(conn, "SELECT * FROM candidatos WHERE empresa_id=? ORDER BY id", (eid,)):
        linha = _limpar_linha(c)
        if not sensivel:
            linha.pop("consentimento_contato_ip", None)
        else:
            linha["consentimento_contato_ip"] = _mascarar(c.get("consentimento_contato_ip"))
        dados["candidatos"].append(linha)
    dados["candidaturas"] = por_candidato("candidaturas")
    dados["eventos"] = por_candidato("eventos")
    dados["resultados_testes"] = por_candidato("resultados_teste")
    dados["autoavaliacoes"] = por_candidato("autoavaliacoes")
    dados["resultados_quiz"] = por_candidato("resultados_quiz")
    dados["entrevistas_notas"] = por_candidato("entrevistas")
    dados["entrevistas_agenda"] = por_empresa("entrevistas_agenda")
    dados["ligacoes_voz"] = por_candidato("voz_chamadas")
    # onboarding: sem os dados cifrados; forma de pagamento só mascarada e só com a senha
    obs = []
    for o in _linhas(conn, "SELECT * FROM onboardings WHERE empresa_id=? ORDER BY id", (eid,)) \
            if _tabela_existe(conn, "onboardings") else []:
        linha = _limpar_linha(o, ("pagamento",))
        if sensivel:
            try:
                linha["pagamento_mascarado"] = _mascarar_dict(json.loads(o.get("pagamento") or "{}"))
            except ValueError:
                linha["pagamento_mascarado"] = {}
            linha["dados_sensiveis"] = "•••• (cifrados, não exportados)" if o.get("sensiveis") else ""
        obs.append(linha)
    dados["onboardings"] = obs
    dados["onboarding_documentos"] = [_limpar_linha(x, ("arquivo",)) for x in por_empresa("onboarding_docs")]
    dados["onboarding_modelos"] = por_empresa("onboarding_templates")
    dados["vagas"] = por_empresa("vagas")
    dados["cargos"] = por_empresa("cargos")
    cargos = "SELECT id FROM cargos WHERE empresa_id=%d" % eid
    for tabela, nome in (("competencias", "competencias"), ("perguntas_entrevista", "perguntas_entrevista"),
                         ("questoes", "questoes_quiz")):
        dados[nome] = [_limpar_linha(x) for x in _linhas(
            conn, "SELECT * FROM %s WHERE cargo_id IN (%s) ORDER BY id" % (tabela, cargos), ())]
    dados["gestores"] = [_limpar_linha(x) for x in _linhas(
        conn, "SELECT * FROM gestores WHERE empresa_id=? AND COALESCE(suporte,0)=0 ORDER BY id", (eid,))]
    dados["indicacoes"] = por_empresa("indicacoes")
    dados["historico_acessos"] = por_empresa("auditoria")
    return dados


LEIA_ME = """Bússola: exportação de dados / data export / exportación de datos

EN: One JSON and one CSV file per dataset (candidates, applications, timeline events, test results,
interviews, voice call metadata and transcripts, onboarding records, jobs, roles). Resumes are in
"curriculos/" and onboarding template PDFs in "onboarding_modelos/". Access tokens and passwords are
never exported. Sensitive onboarding data (bank details, date of birth, license numbers, tax form data)
is encrypted at rest and is not exported; when requested with the admin password, payment details are
included only as masked values. Signed onboarding documents stay encrypted: download them one by one
from the panel.

PT: Um arquivo JSON e um CSV por conjunto de dados. Currículos em "curriculos/" e PDFs de modelos do
onboarding em "onboarding_modelos/". Tokens de acesso e senhas nunca saem. Dados sensíveis do onboarding
ficam cifrados e não são exportados; com a senha do administrador, a forma de pagamento sai só mascarada.
Documentos assinados continuam cifrados: baixe um a um pelo painel.

ES: Un archivo JSON y un CSV por conjunto de datos. Currículums en "curriculos/" y PDF de plantillas de
onboarding en "onboarding_modelos/". Los tokens de acceso y las contraseñas nunca se exportan. Los datos
sensibles del onboarding están cifrados y no se exportan; con la contraseña del administrador, la forma de
pago sale solo enmascarada. Los documentos firmados siguen cifrados: descárgalos uno por uno desde el panel.
"""


def _pasta_exportacoes(empresa_id):
    p = os.path.join(srv.BASE_DIR, "exportacoes", str(int(empresa_id)))
    os.makedirs(p, exist_ok=True)
    return p


def _arquivo_no_upload(rel):
    if not rel:
        return None
    caminho = os.path.normpath(os.path.join(srv.UPLOAD_DIR, rel))
    base = os.path.normpath(srv.UPLOAD_DIR)
    if not caminho.startswith(base + os.sep) or not os.path.isfile(caminho):
        return None
    return caminho


def gerar_exportacao(exp_id):
    """Monta o ZIP (roda numa thread). Usa uma conexão própria."""
    conn = srv.db()
    try:
        exp = conn.execute("SELECT * FROM exportacoes WHERE id=?", (exp_id,)).fetchone()
        if not exp or exp["status"] != "preparando":
            return
        eid = exp["empresa_id"]
        dados = montar_dados(conn, eid, bool(exp["sensivel"]))
        nome = "%s.zip" % secrets.token_hex(16)
        destino = os.path.join(_pasta_exportacoes(eid), nome)
        temp = destino + ".parcial"
        with _trava_export, zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("LEIA-ME_README.txt", LEIA_ME)
            for chave, linhas in dados.items():
                z.writestr("%s.json" % chave, json.dumps(linhas, ensure_ascii=False, indent=1, default=str))
                z.writestr("%s.csv" % chave, _csv(linhas))
            for c in conn.execute("SELECT id, nome, curriculo_arquivo FROM candidatos WHERE empresa_id=?"
                                  " AND curriculo_arquivo != ''", (eid,)).fetchall():
                caminho = _arquivo_no_upload(c["curriculo_arquivo"])
                if caminho:
                    z.write(caminho, "curriculos/%d_%s" % (c["id"], os.path.basename(caminho)))
            if _tabela_existe(conn, "onboarding_templates"):
                for m in conn.execute("SELECT id, arquivo FROM onboarding_templates WHERE empresa_id=?"
                                      " AND arquivo != ''", (eid,)).fetchall():
                    caminho = _arquivo_no_upload(m["arquivo"])
                    if caminho and caminho.lower().endswith(".pdf"):
                        z.write(caminho, "onboarding_modelos/%d_%s" % (m["id"], os.path.basename(caminho)))
        os.replace(temp, destino)
        conn.execute(
            "UPDATE exportacoes SET status='pronto', arquivo=?, tamanho=?, pronto_em=datetime('now'), expira_em=?"
            " WHERE id=?",
            (os.path.relpath(destino, srv.BASE_DIR), os.path.getsize(destino),
             _agora_sql(timedelta(hours=HORAS_EXPORTACAO)), exp_id),
        )
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("Exportação %s falhou: %r\n" % (exp_id, exc))
        try:
            conn.execute("UPDATE exportacoes SET status='erro', erro=? WHERE id=?", (repr(exc)[:300], exp_id))
            conn.commit()
        except Exception:  # noqa: BLE001
            pass
    finally:
        conn.close()


def _exportacao_publica(r):
    return {"id": r["id"], "status": r["status"], "sensivel": bool(r["sensivel"]), "tamanho": r["tamanho"] or 0,
            "criado_em": r["criado_em"], "pronto_em": r["pronto_em"], "expira_em": r["expira_em"]}


def listar_exportacoes(conn, gestor):
    expirar_exportacoes(conn)
    return [_exportacao_publica(r) for r in conn.execute(
        "SELECT * FROM exportacoes WHERE empresa_id=? AND gestor_id=? ORDER BY id DESC LIMIT 10",
        (gestor["empresa_id"], gestor["id"])).fetchall()]


def expirar_exportacoes(conn):
    for r in conn.execute("SELECT * FROM exportacoes WHERE status='pronto' AND expira_em != '' AND expira_em <= ?",
                          (_agora_sql(),)).fetchall():
        _apagar_zip(r["arquivo"])
        conn.execute("UPDATE exportacoes SET status='expirado', arquivo='' WHERE id=?", (r["id"],))
    conn.commit()


def _apagar_zip(rel):
    if not rel:
        return
    caminho = os.path.normpath(os.path.join(srv.BASE_DIR, rel))
    base = os.path.normpath(os.path.join(srv.BASE_DIR, "exportacoes"))
    if caminho.startswith(base + os.sep):
        try:
            os.remove(caminho)
        except OSError:
            pass


def _enviar_zip(h, caminho, nome):
    tamanho = os.path.getsize(caminho)
    h.send_response(200)
    h.send_header("Content-Type", "application/zip")
    h.send_header("Content-Disposition", 'attachment; filename="%s"' % nome)
    h.send_header("Content-Length", str(tamanho))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    with open(caminho, "rb") as f:
        shutil.copyfileobj(f, h.wfile)
    return True


# ------------------------------------------------------- encerramento e exclusão

def encerrar_conta(conn, gestor, confirmacao, ip=""):
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (gestor["empresa_id"],)).fetchone()
    if not e:
        return None, "Empresa não encontrada"
    if (confirmacao or "").strip().lower() != (e["nome"] or "").strip().lower():
        return None, "Digite o nome da empresa exatamente como aparece para confirmar"
    exclusao = _agora_sql(timedelta(days=DIAS_EXCLUSAO))
    conn.execute(
        "UPDATE empresas SET status_anterior=?, status='cancelada', exclusao_em=?, encerrada_em=datetime('now'),"
        " encerrada_por=? WHERE id=?",
        (e["status"], exclusao, (gestor["nome"] or "")[:120], e["id"]),
    )
    conn.execute("DELETE FROM sessoes_gestor WHERE gestor_id IN (SELECT id FROM gestores WHERE empresa_id=?)",
                 (e["id"],))
    conn.commit()
    srv.seguranca.registrar(conn, "conta_encerrada", gestor, exclusao[:10], ip)
    _avisar_dono(conn, e, gestor, exclusao)
    return {"ok": True, "exclusao_em": exclusao}, None


def _avisar_dono(conn, e, gestor, exclusao):
    dono = (srv.config_get(conn, "dono_email") or "").strip()
    if not dono:
        return False
    planos = getattr(srv, "planos", None)
    lang = "pt"
    try:
        lang = _idioma(planos.idioma_dono(conn)) if planos else "pt"
    except Exception:  # noqa: BLE001
        lang = "pt"
    textos = {
        "pt": ("Conta encerrada: %s", "A empresa %s encerrou a conta na Bússola (pedido de %s).\n\n"
               "Todos os dados serão apagados em definitivo em %s.\n"
               "Para cancelar a exclusão, abra o Painel do Dono, aba Empresas, Exclusões pendentes."),
        "en": ("Account closed: %s", "The company %s closed its Bússola account (requested by %s).\n\n"
               "All data will be permanently deleted on %s.\n"
               "To cancel the deletion, open the Owner Panel, Companies tab, Pending deletions."),
        "es": ("Cuenta cerrada: %s", "La empresa %s cerró su cuenta en Bússola (pedido de %s).\n\n"
               "Todos los datos se eliminarán de forma definitiva el %s.\n"
               "Para cancelar la eliminación, abre el Panel del Dueño, pestaña Empresas, Eliminaciones pendientes."),
    }[lang]
    try:
        ok, _ = srv.enviar_email(conn, dono, textos[0] % e["nome"], textos[1] % (e["nome"], gestor["nome"],
                                                                                  exclusao[:10]), idioma=lang)
        return ok
    except Exception:  # noqa: BLE001
        return False


def exclusoes_pendentes(conn):
    return [{"id": r["id"], "nome": r["nome"], "slug": r["slug"], "exclusao_em": r["exclusao_em"],
             "encerrada_em": r["encerrada_em"], "encerrada_por": r["encerrada_por"]}
            for r in conn.execute("SELECT * FROM empresas WHERE status='cancelada' AND exclusao_em != ''"
                                  " ORDER BY exclusao_em").fetchall()]


def cancelar_exclusao(conn, empresa_id, ip=""):
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    if not e or not e["exclusao_em"]:
        return False
    volta = e["status_anterior"] if e["status_anterior"] in ("ativa", "teste") else "ativa"
    conn.execute("UPDATE empresas SET status=?, exclusao_em='', status_anterior='' WHERE id=?", (volta, e["id"]))
    conn.commit()
    srv.seguranca.registrar(conn, "exclusao_cancelada", None, e["nome"], ip, empresa_id=e["id"], quem=QUEM_DONO)
    return True


def excluir_empresa(empresa_id):
    """Apaga de vez a empresa: todas as linhas com empresa_id, as ligadas aos seus
    candidatos, cargos e gestores, as configurações da empresa e os arquivos."""
    eid = int(empresa_id)
    conn = srv.db()
    try:
        e = conn.execute("SELECT * FROM empresas WHERE id=?", (eid,)).fetchone()
        if not e:
            return None
        arquivos = []
        for r in conn.execute("SELECT curriculo_arquivo FROM candidatos WHERE empresa_id=? AND curriculo_arquivo!=''",
                              (eid,)).fetchall():
            arquivos.append(_arquivo_no_upload(r["curriculo_arquivo"]))
        pastas = [os.path.join(srv.UPLOAD_DIR, "onboarding", str(int(r["id"])))
                  for r in _linhas(conn, "SELECT id FROM onboardings WHERE empresa_id=?", (eid,))]
        for r in _linhas(conn, "SELECT arquivo FROM onboarding_templates WHERE empresa_id=? AND arquivo!=''", (eid,)):
            arquivos.append(_arquivo_no_upload(r["arquivo"]))
        try:
            srv.mensagens.remover_logo(conn, eid)
        except Exception:  # noqa: BLE001
            pass
        # devolve os números exclusivos à Twilio e tira da ElevenLabs (telefonia.py)
        tel = getattr(srv, "telefonia", None)
        if tel is not None:
            for r in _linhas(conn, "SELECT id FROM numeros_empresa WHERE empresa_id=? AND status IN ('ativo','pendente')", (eid,)):
                try:
                    tel.liberar(conn, r["id"], True, manter_twilio=False, ip="exclusao")
                except Exception as exc:  # noqa: BLE001
                    sys.stderr.write("conta: não liberou o número %s: %r\n" % (r["id"], exc))
        tabelas = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            " AND name NOT IN ('empresas', 'exclusoes_empresa')").fetchall()]
        cols = {t: _colunas(conn, t) for t in tabelas}
        ids = {
            "candidato_id": [r[0] for r in conn.execute("SELECT id FROM candidatos WHERE empresa_id=?", (eid,))],
            "cargo_id": [r[0] for r in conn.execute("SELECT id FROM cargos WHERE empresa_id=?", (eid,))],
            "gestor_id": [r[0] for r in conn.execute("SELECT id FROM gestores WHERE empresa_id=?", (eid,))],
            "vaga_id": [r[0] for r in conn.execute("SELECT id FROM vagas WHERE empresa_id=?", (eid,))],
        }
        conn.commit()
        conn.execute("PRAGMA foreign_keys = OFF")
        resumo = {}
        conn.execute("BEGIN")
        for t in tabelas:
            n = 0
            for coluna, lista in ids.items():
                if coluna in cols[t] and "empresa_id" not in cols[t] and lista:
                    for i in range(0, len(lista), 500):
                        parte = lista[i:i + 500]
                        n += conn.execute("DELETE FROM %s WHERE %s IN (%s)" % (t, coluna, ",".join("?" * len(parte))),
                                          parte).rowcount
            if "empresa_id" in cols[t]:
                n += conn.execute("DELETE FROM %s WHERE empresa_id=?" % t, (eid,)).rowcount
            if n:
                resumo[t] = n
        n = conn.execute("DELETE FROM config WHERE chave LIKE ? ESCAPE '\\'", ("%:" + str(eid),)).rowcount
        if n:
            resumo["config"] = resumo.get("config", 0) + n
        if "voz_config" in tabelas:
            conn.execute("DELETE FROM voz_config WHERE local=?", ("empresa:%d" % eid,))
        conn.execute("DELETE FROM empresas WHERE id=?", (eid,))
        conn.execute("INSERT INTO exclusoes_empresa (empresa_id, nome, resumo) VALUES (?,?,?)",
                     (eid, e["nome"], json.dumps(resumo, ensure_ascii=False)))
        conn.commit()
        conn.execute("PRAGMA foreign_keys = ON")
        for caminho in arquivos:
            if caminho:
                try:
                    os.remove(caminho)
                except OSError:
                    pass
        for p in pastas:
            shutil.rmtree(p, ignore_errors=True)
        shutil.rmtree(os.path.join(srv.BASE_DIR, "exportacoes", str(eid)), ignore_errors=True)
        srv.seguranca.registrar(conn, "empresa_excluida", None, "%s (#%d)" % (e["nome"], eid), "",
                                empresa_id=None, quem="sistema")
        sys.stderr.write("Conta: empresa #%d (%s) excluída em definitivo: %s\n" % (eid, e["nome"], resumo))
        return resumo
    except Exception:
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        raise
    finally:
        conn.close()


def rodar_rotina(conn=None):
    """Uma rodada: exportações vencidas, códigos e sessões de suporte vencidos e
    empresas com a data de exclusão vencida. Devolve os ids excluídos."""
    proprio = conn is None
    conn = conn or srv.db()
    excluidas = []
    try:
        expirar_exportacoes(conn)
        agora = _agora_sql()
        conn.execute("DELETE FROM suporte_codigos WHERE expira_em <= ?", (_agora_sql(timedelta(days=-1)),))
        conn.execute("DELETE FROM sessoes_gestor WHERE expira_em != '' AND expira_em IS NOT NULL AND expira_em <= ?",
                     (agora,))
        conn.commit()
        vencidas = [r["id"] for r in conn.execute(
            "SELECT id FROM empresas WHERE status='cancelada' AND exclusao_em != '' AND exclusao_em <= ?",
            (agora,)).fetchall()]
    finally:
        if proprio:
            conn.close()
    for eid in vencidas:
        try:
            excluir_empresa(eid)
            excluidas.append(eid)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Conta: exclusão da empresa #%s falhou: %r\n" % (eid, exc))
    return excluidas


def rotina_conta(intervalo=3600):
    """Thread do servidor: confere uma vez por hora (a exclusão vale pela data)."""
    while True:
        try:
            rodar_rotina()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Rotina da conta falhou: %r\n" % exc)
        time.sleep(intervalo)


# ------------------------------------------------------------------ rotas

def rotear_publico(h, method, path, conn):
    """Rotas sem sessão de gestor: troca do código de suporte e revogação pelo candidato."""
    if method == "POST" and path == "/api/gestor/suporte/entrar":
        if h._login_bloqueado("suporte"):
            return _resp(h, 429, {"erro": "Muitas tentativas. Aguarde alguns minutos e tente de novo."})
        payload, erro = trocar_codigo(conn, str(h._body().get("codigo") or ""), h._ip_cliente())
        if erro:
            h._registrar_falha_login("suporte")
            return _resp(h, 401, {"erro": erro})
        return _resp(h, 200, payload)

    if (method == "GET" and path == "/api/candidato/contato") or (
            method == "POST" and path == "/api/candidato/contato/revogar"):
        cand = h._candidato(conn)
        if not cand:
            return _resp(h, 401, {"erro": "Sessão inválida. Faça o cadastro novamente."})
        if method == "POST":
            revogar_contato(conn, cand, h._ip_cliente())
            cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (cand["id"],)).fetchone()
        return _resp(h, 200, {"ok": True, "contato": estado_candidato(cand)})
    return None


def rotear_dono(h, method, path, conn):
    """Rotas /api/dono/conta/* (o guarda do dono já rodou no server.py)."""
    if not path.startswith("/api/dono/conta/"):
        return None
    ip = h._ip_cliente()
    m = re.match(r"^/api/dono/conta/suporte/(\d+)$", path)
    if m and method == "POST":
        codigo, erro = criar_codigo_suporte(conn, int(m.group(1)), ip)
        if erro:
            return _resp(h, 404 if erro == "Empresa não encontrada" else 403, {"erro": erro})
        return _resp(h, 200, {"codigo": codigo, "expira_em_min": MINUTOS_CODIGO})
    if method == "GET" and path == "/api/dono/conta/exclusoes":
        return _resp(h, 200, {"exclusoes": exclusoes_pendentes(conn)})
    m = re.match(r"^/api/dono/conta/exclusao/(\d+)/cancelar$", path)
    if m and method == "POST":
        if not cancelar_exclusao(conn, int(m.group(1)), ip):
            return _resp(h, 404, {"erro": "Empresa não encontrada"})
        return _resp(h, 200, {"ok": True})
    return _resp(h, 404, {"erro": "Rota não encontrada"})


def rotear_gestor(h, method, path, conn, gestor):
    if not (path.startswith("/api/gestor/conta") or path.startswith("/api/gestor/suporte/")):
        return None
    eid = gestor["empresa_id"]
    ip = h._ip_cliente()
    suporte = sessao_de_suporte(gestor)

    if method == "GET" and path == "/api/gestor/conta/sessao":
        return _resp(h, 200, estado_sessao(conn, h, gestor))

    if method == "POST" and path == "/api/gestor/suporte/encerrar":
        if not suporte:
            return _resp(h, 403, {"erro": "Esta sessão não é de suporte"})
        conn.execute("DELETE FROM sessoes_gestor WHERE token=?", (h.headers.get("X-Gestor-Token", ""),))
        conn.commit()
        srv.seguranca.registrar(conn, "suporte_encerrado", gestor, gestor["empresa_nome"] if "empresa_nome" in
                                gestor.keys() else "", ip, quem=QUEM_SUPORTE)
        return _resp(h, 200, {"ok": True})

    if method == "GET" and path == "/api/gestor/conta":
        e = conn.execute("SELECT * FROM empresas WHERE id=?", (eid,)).fetchone()
        nome = e["nome"] if e else ""
        return _resp(h, 200, {
            "config": config(conn, eid),
            "anuncio": {lang: TEXTO_ANUNCIO[lang].format(empresa=nome) for lang in ("en", "pt", "es")},
            "empresa": nome, "suporte": suporte,
            "exportacoes": listar_exportacoes(conn, gestor) if gestor["is_admin"] else [],
        })

    if not gestor["is_admin"]:
        return _resp(h, 403, {"erro": "Apenas o administrador da empresa acessa os dados e a conta"})

    if method == "POST" and path == "/api/gestor/conta/config":
        d = h._body()
        cfg = config(conn, eid)
        cfg["so_com_consentimento"] = bool(d.get("so_com_consentimento"))
        srv.config_set(conn, _chave(eid), json.dumps(cfg))
        conn.commit()
        return _resp(h, 200, {"ok": True, "config": cfg})

    if method == "POST" and path == "/api/gestor/conta/exportar":
        if suporte:
            return _resp(h, 403, {"erro": "Indisponível no modo suporte"})
        d = h._body()
        sensivel = bool(d.get("sensivel"))
        if sensivel:
            if h._login_bloqueado("senha_conta"):
                return _resp(h, 429, {"erro": "Muitas tentativas. Aguarde alguns minutos e tente de novo."})
            if not srv.senha_confere(d.get("senha") or "", gestor["senha"]):
                h._registrar_falha_login("senha_conta")
                return _resp(h, 400, {"erro": "Senha incorreta"})
            h._limpar_falhas_login("senha_conta")
        if conn.execute("SELECT 1 FROM exportacoes WHERE empresa_id=? AND status='preparando'"
                        " AND criado_em > datetime('now','-30 minutes')", (eid,)).fetchone():
            return _resp(h, 409, {"erro": "Já existe uma exportação sendo preparada. Aguarde alguns minutos."})
        exp_id = conn.execute("INSERT INTO exportacoes (empresa_id, gestor_id, sensivel) VALUES (?,?,?)",
                              (eid, gestor["id"], 1 if sensivel else 0)).lastrowid
        conn.commit()
        srv.seguranca.registrar(conn, "exportacao_pedida", gestor, "sensivel" if sensivel else "", ip)
        threading.Thread(target=gerar_exportacao, args=(exp_id,), daemon=True).start()
        return _resp(h, 200, {"ok": True, "id": exp_id})

    m = re.match(r"^/api/gestor/conta/exportacao/(\d+)/baixar$", path)
    if m and method == "GET":
        expirar_exportacoes(conn)
        r = conn.execute("SELECT * FROM exportacoes WHERE id=? AND empresa_id=? AND gestor_id=?",
                         (int(m.group(1)), eid, gestor["id"])).fetchone()
        if not r:
            return _resp(h, 404, {"erro": "Exportação não encontrada"})
        if r["status"] != "pronto":
            return _resp(h, 410 if r["status"] == "expirado" else 409,
                         {"erro": "O link expirou. Gere uma nova exportação." if r["status"] == "expirado"
                          else "A exportação ainda está sendo preparada"})
        caminho = os.path.normpath(os.path.join(srv.BASE_DIR, r["arquivo"]))
        if not caminho.startswith(os.path.normpath(os.path.join(srv.BASE_DIR, "exportacoes")) + os.sep) \
                or not os.path.isfile(caminho):
            return _resp(h, 404, {"erro": "Arquivo não encontrado"})
        srv.seguranca.registrar(conn, "exportacao_baixada", gestor, str(r["id"]), ip)
        return _enviar_zip(h, caminho, "bussola-dados-%s.zip" % datetime.utcnow().strftime("%Y-%m-%d"))

    if method == "POST" and path == "/api/gestor/conta/encerrar":
        if suporte:
            return _resp(h, 403, {"erro": "Indisponível no modo suporte"})
        dados, erro = encerrar_conta(conn, gestor, h._body().get("confirmacao"), ip)
        if erro:
            return _resp(h, 400, {"erro": erro})
        return _resp(h, 200, dados)

    return _resp(h, 404, {"erro": "Rota não encontrada"})
