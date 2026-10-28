"""Entrada automática de candidatos: leitura dos e-mails de candidatura do Indeed
(IMAP, configurada por cada empresa) e importação de planilha CSV.

A caixa é aberta só para leitura (nenhum e-mail é marcado como lido, movido ou
apagado) e só as mensagens do Indeed são consideradas. Cada mensagem é lida uma
vez: guardamos o último UID processado por caixa. Quem já existe na empresa
(mesmo e-mail ou telefone) não é duplicado.
"""
import base64
import csv
import email
import email.policy
import html as _html
import imaplib
import io
import json
import os
import re
import secrets
import socket
import sys
import threading
import time
from email.utils import getaddresses, parseaddr

srv = None  # módulo server, injetado por ligar()
voz = None

INTERVALO_SEGUNDOS = 300
MAX_POR_RODADA = 50
_trava = threading.Lock()

PADRAO = {
    "ativo": False, "imap_host": "imap.gmail.com", "imap_porta": 993, "usuario": "", "senha": "",
    "pasta": "INBOX", "remetentes": "indeed.com, indeedemail.com", "vaga_id": None, "auto_fila": False,
    "ultimo_uid": 0, "uidvalidity": "", "ultima_execucao": "", "ultimo_erro": "", "importados": 0,
}


def ligar(modulo_server):
    global srv, voz
    srv = modulo_server
    voz = modulo_server.voz


def _chave(empresa_id):
    return "entrada:%d" % int(empresa_id)


def config(conn, empresa_id):
    cfg = dict(PADRAO)
    try:
        cfg.update(json.loads(srv.config_get(conn, _chave(empresa_id)) or "{}"))
    except ValueError:
        pass
    return cfg


def salvar(conn, empresa_id, cfg):
    srv.config_set(conn, _chave(empresa_id), json.dumps(cfg, ensure_ascii=False))
    conn.commit()


def config_publica(cfg):
    """Configuração sem a senha (para o painel)."""
    saida = {k: v for k, v in cfg.items() if k != "senha"}
    saida["senha_configurada"] = bool(cfg.get("senha"))
    return saida


# ------------------------------------------------------------- criação do candidato

def _digitos(t):
    d = re.sub(r"\D", "", t or "")
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return d


def _telefone(t):
    d = _digitos(t)
    return "+1" + d if len(d) == 10 else (t or "").strip()


def ja_existe(conn, empresa_id, email_, telefone):
    email_ = (email_ or "").strip().lower()
    fone = _digitos(telefone)
    for r in conn.execute("SELECT id, email, telefone FROM candidatos WHERE empresa_id=? AND anonimizado=0",
                          (empresa_id,)).fetchall():
        if email_ and (r["email"] or "").strip().lower() == email_:
            return r["id"]
        if len(fone) >= 10 and _digitos(r["telefone"]) == fone:
            return r["id"]
    return None


def criar_candidato(conn, empresa_id, dados, vaga_id, origem, auto_fila=False, autor="sistema"):
    """Cria candidato + candidatura. dados: nome, email, telefone, local, experiencia,
    escolaridade, observacoes, data, curriculo (nome, bytes), etiquetas.
    Devolve ("criado", id) ou ("duplicado", id) ou ("invalido", motivo)."""
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return "invalido", "sem_nome"
    if not (dados.get("email") or "").strip() and len(_digitos(dados.get("telefone"))) < 10:
        return "invalido", "sem_contato"
    existente = ja_existe(conn, empresa_id, dados.get("email"), dados.get("telefone"))
    if existente:
        return "duplicado", existente
    vaga = conn.execute("SELECT id, cargo_id, titulo FROM vagas WHERE id=? AND empresa_id=?",
                        (vaga_id, empresa_id)).fetchone() if vaga_id else None
    etiquetas = [origem] + [e for e in (dados.get("etiquetas") or []) if e and e != origem]
    criado_em = (dados.get("data") or "").strip()
    criado_em = criado_em[:10] + " 12:00:00" if re.match(r"^\d{4}-\d{2}-\d{2}", criado_em) else None
    cur = conn.execute(
        "INSERT INTO candidatos (token, nome, email, local, telefone, cargo_atual, cargo_desejado_id,"
        " empresa_id, tags, tipo, idioma, criado_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,COALESCE(?, datetime('now')))",
        (secrets.token_urlsafe(24), nome[:120], (dados.get("email") or "").strip().lower()[:200],
         (dados.get("local") or "").strip()[:200], _telefone(dados.get("telefone")),
         (dados.get("experiencia") or "").strip()[:120], vaga["cargo_id"] if vaga else None,
         empresa_id, json.dumps(etiquetas, ensure_ascii=False), "externo", "", criado_em),
    )
    cid = cur.lastrowid
    if dados.get("curriculo"):
        nome_arq, conteudo = dados["curriculo"]
        nome_arq = re.sub(r"[^A-Za-z0-9._-]", "_", nome_arq or "curriculo.pdf")[-80:]
        destino = "cand%d_%s" % (cid, nome_arq)
        with open(os.path.join(srv.UPLOAD_DIR, destino), "wb") as f:
            f.write(conteudo)
        conn.execute("UPDATE candidatos SET curriculo_arquivo=? WHERE id=?", (destino, cid))
    if vaga:
        conn.execute(
            "INSERT INTO candidaturas (candidato_id, vaga_id, etapa, criado_em, atualizado_em, voz_status)"
            " VALUES (?,?,'inscrito',COALESCE(?, datetime('now')),datetime('now'),'')",
            (cid, vaga["id"], criado_em),
        )
        srv.registrar_evento(conn, cid, "candidatura", "Inscrição na vaga: %s" % vaga["titulo"])
        if auto_fila:
            voz.nova_candidatura(conn, cid, vaga["id"])
    partes = [dados.get(k, "").strip() for k in ("observacoes",) if (dados.get(k) or "").strip()]
    if (dados.get("experiencia") or "").strip():
        partes.append("Experience: " + dados["experiencia"].strip())
    if (dados.get("escolaridade") or "").strip():
        partes.append("Education: " + dados["escolaridade"].strip())
    if partes:
        srv.registrar_evento(conn, cid, "anotacao", "\n".join(partes), autor)
    srv.registrar_evento(conn, cid, "sistema", "Importado (%s)" % origem)
    return "criado", cid


# ------------------------------------------------------------- e-mails do Indeed

RE_TELEFONE = re.compile(r"(?:\+?1[\s.-]?)?\(?\b(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b")
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RE_LOCAL = re.compile(r"\b([A-Z][a-zA-Z .'-]{2,30}),\s*(CT|MA|NY|RI|NJ|Connecticut|Massachusetts)\b(?:\s*\d{5})?")
ASSUNTOS = [
    # "Maria Lopez applied to House Cleaning Technician"
    re.compile(r"^(?:new application:\s*)?(?P<nome>.+?)\s+(?:has\s+)?applied (?:to|for)\s+(?P<vaga>.+)$", re.I),
    # "New application: House Cleaning Technician from Maria Lopez"
    re.compile(r"^new (?:application|applicant|candidate)[^:]*:\s*(?P<vaga>.+?)\s+(?:from|-)\s+(?P<nome>.+)$", re.I),
    # "Maria Lopez is interested in House Cleaning Technician"
    re.compile(r"^(?P<nome>.+?)\s+is interested in\s+(?P<vaga>.+)$", re.I),
    # "Indeed Application: House Cleaning Technician"
    re.compile(r"^indeed application:\s*(?P<vaga>.+)$", re.I),
]
RESUMOS = re.compile(r"\b(\d+\s+new candidates?|candidate update|daily digest|jobs? for you|new jobs)\b", re.I)


def _texto_da_mensagem(msg):
    partes = []
    for parte in msg.walk():
        if parte.get_content_maintype() == "multipart" or parte.get_filename():
            continue
        tipo = parte.get_content_type()
        if tipo not in ("text/plain", "text/html"):
            continue
        try:
            conteudo = parte.get_content()
        except Exception:  # noqa: BLE001
            continue
        if tipo == "text/html":
            conteudo = re.sub(r"(?is)<(script|style).*?</\1>", " ", conteudo)
            conteudo = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", conteudo)
            conteudo = _html.unescape(re.sub(r"<[^>]+>", " ", conteudo))
        partes.append(conteudo)
    return "\n".join(partes)


def _curriculo(msg):
    for parte in msg.walk():
        nome = parte.get_filename() or ""
        if nome.lower().endswith((".pdf", ".doc", ".docx")):
            dados = parte.get_payload(decode=True)
            if dados and len(dados) <= 8 * 1024 * 1024:
                return nome, dados
    return None


def _texto_pdf(dados):
    """Texto simples de um PDF (melhor esforço, sem bibliotecas externas)."""
    try:
        import logging
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        from pypdf import PdfReader  # opcional
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(dados)).pages[:3])
    except Exception:  # noqa: BLE001
        return ""


def ler_mensagem(bruto, remetentes):
    """Extrai os dados de um e-mail de candidatura. Devolve dict ou None quando
    não é uma candidatura individual (resumos diários, alertas de vagas etc.)."""
    msg = email.message_from_bytes(bruto, policy=email.policy.default)
    de = parseaddr(str(msg.get("From") or ""))[1].lower()
    if not any(r and de.endswith(r) for r in remetentes):
        return None
    assunto = re.sub(r"\s+", " ", str(msg.get("Subject") or "")).strip()
    if RESUMOS.search(assunto):
        return None
    nome = vaga = ""
    for padrao in ASSUNTOS:
        m = padrao.match(assunto)
        if m:
            nome = (m.groupdict().get("nome") or "").strip(" -:")
            vaga = (m.groupdict().get("vaga") or "").strip(" -:")
            break
    texto = _texto_da_mensagem(msg)
    # o e-mail de contato do candidato vem no Reply-To (endereço intermediário do Indeed)
    contato = ""
    for _, endereco in getaddresses([str(msg.get("Reply-To") or "")]):
        if endereco and "noreply" not in endereco.lower() and "no-reply" not in endereco.lower():
            contato = endereco.lower()
            break
    if not nome:
        nome_reply = parseaddr(str(msg.get("Reply-To") or ""))[0]
        m = re.search(r"(?im)^\s*(?:name|nombre|nome)\s*[:\n]\s*(.+)$", texto)
        nome = (m.group(1) if m else nome_reply or "").strip()
    curriculo = _curriculo(msg)
    texto_busca = texto + "\n" + (_texto_pdf(curriculo[1]) if curriculo and curriculo[0].lower().endswith(".pdf") else "")
    if not contato:
        for e in RE_EMAIL.findall(texto_busca):
            if not any(x in e.lower() for x in ("indeed.com", "noreply", "no-reply")):
                contato = e.lower()
                break
    m = RE_TELEFONE.search(texto_busca)
    telefone = "".join(m.groups()) if m else ""
    m = RE_LOCAL.search(texto_busca)
    local = m.group(0).strip() if m else ""
    if not nome or not (contato or telefone):
        return None
    return {"nome": nome[:120], "email": contato, "telefone": telefone, "local": local, "vaga_titulo": vaga,
            "curriculo": curriculo, "message_id": str(msg.get("Message-ID") or "")}


def _vaga_para(conn, empresa_id, titulo, padrao):
    if titulo:
        v = conn.execute("SELECT id FROM vagas WHERE empresa_id=? AND lower(titulo)=lower(?) ORDER BY status='aberta' DESC",
                         (empresa_id, titulo.strip())).fetchone()
        if v:
            return v["id"]
    return padrao


def conectar(cfg):
    socket.setdefaulttimeout(30)
    imap = imaplib.IMAP4_SSL(cfg["imap_host"], int(cfg.get("imap_porta") or 993))
    imap.login(cfg["usuario"], cfg["senha"])
    return imap


def testar(cfg):
    """Testa a conexão. Devolve (ok, mensagem, total_de_mensagens_do_indeed)."""
    try:
        imap = conectar(cfg)
        try:
            tipo, _ = imap.select('"%s"' % (cfg.get("pasta") or "INBOX"), readonly=True)
            if tipo != "OK":
                return False, "folder_not_found", 0
            total = 0
            for r in _remetentes(cfg):
                tipo, dados = imap.uid("search", None, "FROM", '"%s"' % r)
                if tipo == "OK" and dados and dados[0]:
                    total += len(dados[0].split())
            return True, "ok", total
        finally:
            try:
                imap.logout()
            except Exception:  # noqa: BLE001
                pass
    except imaplib.IMAP4.error as exc:
        return False, "login_failed: %s" % str(exc)[:120], 0
    except Exception as exc:  # noqa: BLE001
        return False, "connection_failed: %s" % str(exc)[:120], 0


def _remetentes(cfg):
    return [r.strip().lower() for r in (cfg.get("remetentes") or "").split(",") if r.strip()]


def ler_caixa(conn, empresa_id):
    """Lê as mensagens novas do Indeed e cria os candidatos. Devolve um resumo."""
    cfg = config(conn, empresa_id)
    resumo = {"lidas": 0, "criados": 0, "duplicados": 0, "ignoradas": 0, "erro": ""}
    if not (cfg.get("usuario") and cfg.get("senha") and cfg.get("imap_host")):
        resumo["erro"] = "not_configured"
        return resumo
    remetentes = _remetentes(cfg)
    try:
        imap = conectar(cfg)
    except Exception as exc:  # noqa: BLE001
        resumo["erro"] = "login_failed: %s" % str(exc)[:120]
        cfg.update(ultima_execucao=_agora(), ultimo_erro=resumo["erro"])
        salvar(conn, empresa_id, cfg)
        return resumo
    try:
        tipo, _ = imap.select('"%s"' % (cfg.get("pasta") or "INBOX"), readonly=True)
        if tipo != "OK":
            raise RuntimeError("folder_not_found")
        validade = (imap.response("UIDVALIDITY")[1] or [b""])[0]
        validade = validade.decode() if isinstance(validade, bytes) else str(validade or "")
        if validade != cfg.get("uidvalidity"):
            # caixa nova (ou recriada): começa pelas mensagens dos últimos 14 dias
            cfg["ultimo_uid"] = 0
            cfg["uidvalidity"] = validade
            desde = time.strftime("%d-%b-%Y", time.gmtime(time.time() - 14 * 86400))
            criterio = ["SINCE", desde]
        else:
            criterio = ["UID", "%d:*" % (int(cfg.get("ultimo_uid") or 0) + 1)]
        uids = set()
        for r in remetentes:
            tipo, dados = imap.uid("search", None, *criterio, "FROM", '"%s"' % r)
            if tipo == "OK" and dados and dados[0]:
                uids.update(int(u) for u in dados[0].split())
        uids = sorted(u for u in uids if u > int(cfg.get("ultimo_uid") or 0))[:MAX_POR_RODADA]
        for uid in uids:
            tipo, dados = imap.uid("fetch", str(uid), "(BODY.PEEK[])")
            bruto = next((d[1] for d in (dados or []) if isinstance(d, tuple)), None)
            cfg["ultimo_uid"] = max(int(cfg.get("ultimo_uid") or 0), uid)
            if not bruto:
                continue
            resumo["lidas"] += 1
            info = ler_mensagem(bruto, remetentes)
            if not info:
                resumo["ignoradas"] += 1
                continue
            vaga_id = _vaga_para(conn, empresa_id, info.get("vaga_titulo"), cfg.get("vaga_id"))
            status, valor = criar_candidato(conn, empresa_id, info, vaga_id, "indeed", bool(cfg.get("auto_fila")))
            if status == "criado":
                resumo["criados"] += 1
                conn.commit()
                cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (valor,)).fetchone()
                vt = conn.execute("SELECT titulo FROM vagas WHERE id=?", (vaga_id,)).fetchone() if vaga_id else None
                try:
                    srv.mensagens.avisar_novo_candidato(conn, cand, vt["titulo"] if vt else "")
                except Exception:  # noqa: BLE001
                    pass
            elif status == "duplicado":
                resumo["duplicados"] += 1
            else:
                resumo["ignoradas"] += 1
        cfg["ultimo_erro"] = ""
    except Exception as exc:  # noqa: BLE001
        resumo["erro"] = str(exc)[:160]
        cfg["ultimo_erro"] = resumo["erro"]
    finally:
        try:
            imap.logout()
        except Exception:  # noqa: BLE001
            pass
    cfg["ultima_execucao"] = _agora()
    cfg["importados"] = int(cfg.get("importados") or 0) + resumo["criados"]
    salvar(conn, empresa_id, cfg)
    conn.commit()
    return resumo


def _agora():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def rotina_entrada():
    """A cada 5 minutos, lê a caixa de cada empresa com a entrada ativa."""
    while True:
        time.sleep(INTERVALO_SEGUNDOS)
        if not _trava.acquire(blocking=False):
            continue
        try:
            conn = srv.db()
            try:
                for r in conn.execute("SELECT chave FROM config WHERE chave LIKE 'entrada:%'").fetchall():
                    empresa_id = int(r["chave"].split(":")[1])
                    emp = conn.execute("SELECT status FROM empresas WHERE id=?", (empresa_id,)).fetchone()
                    if emp and emp["status"] in ("ativa", "teste") and config(conn, empresa_id).get("ativo"):
                        ler_caixa(conn, empresa_id)
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Entrada de candidatos falhou: %r\n" % exc)
        finally:
            _trava.release()


# ------------------------------------------------------------- planilha CSV

COLUNAS = {
    "nome": ("name", "nome", "nombre", "candidate", "candidate name", "candidato", "full name"),
    "email": ("email", "e-mail", "email address", "correo"),
    "telefone": ("phone", "phone number", "telefone", "teléfono", "telefono", "mobile"),
    "local": ("candidate location", "location", "local", "cidade", "city", "ubicación"),
    "experiencia": ("relevant experience", "relvant experiencie", "experience", "experiência", "experiencia"),
    "escolaridade": ("education", "escolaridade", "educación"),
    "data": ("date", "date applied", "applied", "data", "fecha"),
    "status": ("status", "estado"),
    "fonte": ("source", "fonte", "origen"),
    "vaga": ("job title", "job", "vaga", "position", "puesto"),
    "observacoes": ("interest level", "notes", "observações", "observacoes", "notas"),
}


def _data_iso(texto):
    texto = (texto or "").strip()
    for padrao, ordem in ((r"^(\d{4})-(\d{1,2})-(\d{1,2})", "ymd"), (r"^(\d{1,2})/(\d{1,2})/(\d{4})", "mdy")):
        m = re.match(padrao, texto)
        if m:
            a, b, c = m.groups()
            y, mo, d = (a, b, c) if ordem == "ymd" else (c, a, b)
            return "%04d-%02d-%02d" % (int(y), int(mo), int(d))
    return ""


def ler_csv(texto):
    """Linhas da planilha como dicts padronizados."""
    texto = texto.lstrip("﻿")
    amostra = texto[:4096]
    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=",;\t")
    except csv.Error:
        dialeto = csv.excel
    leitor = csv.reader(io.StringIO(texto), dialeto)
    linhas = list(leitor)
    if not linhas:
        return []
    cab = [c.strip().lower() for c in linhas[0]]
    indice = {}
    for campo, nomes in COLUNAS.items():
        for i, c in enumerate(cab):
            if c in nomes:
                indice[campo] = i
                break
    saida = []
    for linha in linhas[1:]:
        if not any(x.strip() for x in linha):
            continue
        d = {campo: (linha[i].strip() if i < len(linha) else "") for campo, i in indice.items()}
        d["data"] = _data_iso(d.get("data"))
        d["etiquetas"] = [x for x in ((d.get("fonte") or "").strip().lower(),) if x]
        saida.append(d)
    return saida


def importar_csv(conn, empresa_id, texto, vaga_id, auto_fila=False, aplicar=False, autor="sistema"):
    """Prévia (aplicar=False) ou importação. Devolve contagens e as linhas com status."""
    linhas = ler_csv(texto)
    resultado = {"total": len(linhas), "criados": 0, "duplicados": 0, "invalidos": 0, "linhas": []}
    vistos = set()
    for d in linhas[:2000]:
        chave = ((d.get("email") or "").lower(), _digitos(d.get("telefone")))
        if not (d.get("nome") or "").strip():
            status, valor = "invalido", "sem_nome"
        elif not chave[0] and len(chave[1]) < 10:
            status, valor = "invalido", "sem_contato"
        elif (chave[0] and chave[0] in vistos) or (len(chave[1]) >= 10 and chave[1] in vistos):
            status, valor = "duplicado", None
        elif aplicar:
            status, valor = criar_candidato(conn, empresa_id, d, vaga_id, "csv", auto_fila, autor)
        else:
            existente = ja_existe(conn, empresa_id, d.get("email"), d.get("telefone"))
            status, valor = ("duplicado", existente) if existente else ("novo", None)
        vistos.update(x for x in chave if x)
        chave_cont = {"criado": "criados", "novo": "criados", "duplicado": "duplicados"}.get(status, "invalidos")
        resultado[chave_cont] += 1
        resultado["linhas"].append({"nome": d.get("nome", ""), "email": d.get("email", ""), "telefone": d.get("telefone", ""),
                                    "local": d.get("local", ""), "status": status,
                                    "motivo": valor if status == "invalido" else ""})
    if aplicar:
        conn.commit()
    return resultado


# ------------------------------------------------------------- rotas do gestor

def prioridades(conn, gestor):
    """Quadro do dia: quem ligar hoje, quem está devendo os testes, quem está
    pronto para entrevista e quem não atende. Só candidatos visíveis ao gestor."""
    empresa_id = gestor["empresa_id"]
    linhas = conn.execute(
        "SELECT ca.id AS candidatura_id, ca.candidato_id, ca.etapa, ca.voz_status, ca.voz_tier, ca.voz_score,"
        " ca.voz_tentativas, ca.voz_proxima, ca.voz_ultima, ca.voz_convite_enviado, ca.atualizado_em,"
        " c.nome, c.telefone, c.local, c.notificado_completo, c.anonimizado, v.titulo AS vaga, v.local AS vaga_local"
        " FROM candidaturas ca JOIN candidatos c ON c.id=ca.candidato_id JOIN vagas v ON v.id=ca.vaga_id"
        " WHERE c.empresa_id=? AND c.anonimizado=0 AND ca.etapa NOT IN ('contratado','reprovado')"
        " ORDER BY ca.atualizado_em DESC LIMIT 1500", (empresa_id,)).fetchall()
    cfg = voz.config_empresa(conn, empresa_id)
    from datetime import datetime, timezone
    zona = voz._zona(cfg)
    agora_local = datetime.now(zona)
    fim_local = agora_local.replace(hour=23, minute=59, second=59, microsecond=0)
    fim_do_dia = fim_local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    grupos = {"ligar_hoje": [], "aguardando_testes": [], "prontos": [], "sem_resposta": []}
    vistos = {k: set() for k in grupos}
    for r in linhas:
        cand = {"local": r["local"], "empresa_id": empresa_id}
        if not srv.gestor_ve_candidato(gestor, cand):
            continue
        item = {"candidato_id": r["candidato_id"], "candidatura_id": r["candidatura_id"], "nome": r["nome"],
                "vaga": r["vaga"], "tier": r["voz_tier"], "score": r["voz_score"], "status": r["voz_status"],
                "proxima": r["voz_proxima"], "tentativas": r["voz_tentativas"]}
        if r["voz_status"] == "callback" or (r["voz_status"] == "para_ligar" and (r["voz_tentativas"] or 0) < cfg["max_tentativas"]
                                             and (not r["voz_proxima"] or r["voz_proxima"] <= fim_do_dia)):
            grupo = "ligar_hoje"
        elif r["voz_status"] in ("para_ligar", "correio_voz") and (r["voz_tentativas"] or 0) >= cfg["max_tentativas"]:
            grupo = "sem_resposta"
        elif r["notificado_completo"] and r["etapa"] in ("inscrito", "avaliacoes"):
            grupo = "prontos"
        elif r["voz_convite_enviado"] and not r["notificado_completo"]:
            grupo = "aguardando_testes"
        else:
            continue
        if r["candidato_id"] in vistos[grupo]:
            continue
        vistos[grupo].add(r["candidato_id"])
        grupos[grupo].append(item)
    # lembretes vencidos ("Lembrar em", talentos.py) entram primeiro em "Ligar hoje"
    talentos = getattr(srv, "talentos", None)
    if talentos is not None:
        lembretes = []
        for r in talentos.lembretes_vencidos(conn, empresa_id, agora_local.strftime("%Y-%m-%d")):
            if not srv.gestor_ve_candidato(gestor, {"local": r["local"], "empresa_id": r["empresa_id"]}):
                continue
            extra = {"lembrete": True, "lembrete_data": r["data"], "lembrete_nota": r["nota"] or ""}
            existente = next((i for i in grupos["ligar_hoje"] if i["candidato_id"] == r["candidato_id"]), None)
            if existente:
                grupos["ligar_hoje"].remove(existente)
                existente.update(extra)
                lembretes.append(existente)
                continue
            lembretes.append(dict({"candidato_id": r["candidato_id"], "candidatura_id": r["candidatura_id"], "nome": r["nome"],
                                   "vaga": r["vaga"] or "", "tier": "", "score": None, "status": "", "proxima": "",
                                   "tentativas": 0}, **extra))
        grupos["ligar_hoje"] = lembretes + grupos["ligar_hoje"]
    return {k: {"total": len(v), "itens": v[:12]} for k, v in grupos.items()}


def rotear_gestor(h, method, path, conn, gestor):
    if method == "GET" and path == "/api/gestor/prioridades":
        return _resp(h, 200, prioridades(conn, gestor))
    if not (path.startswith("/api/gestor/entrada") or path == "/api/gestor/importar-csv"):
        return None
    if not gestor["is_admin"]:
        return _resp(h, 403, {"erro": "Apenas o administrador da empresa configura a entrada de candidatos"})
    empresa_id = gestor["empresa_id"]

    if method == "GET" and path == "/api/gestor/entrada":
        cfg = config(conn, empresa_id)
        vagas = [{"id": v["id"], "titulo": v["titulo"], "status": v["status"]} for v in conn.execute(
            "SELECT id, titulo, status FROM vagas WHERE empresa_id=? ORDER BY status='aberta' DESC, titulo",
            (empresa_id,)).fetchall()]
        return _resp(h, 200, {"config": config_publica(cfg), "vagas": vagas})

    if method == "POST" and path == "/api/gestor/entrada":
        d = h._body()
        cfg = config(conn, empresa_id)
        for campo in ("imap_host", "usuario", "pasta", "remetentes"):
            if campo in d:
                cfg[campo] = str(d[campo] or "").strip()[:200]
        if "imap_porta" in d:
            try:
                cfg["imap_porta"] = max(1, min(65535, int(d["imap_porta"])))
            except (TypeError, ValueError):
                return _resp(h, 400, {"erro": "Porta inválida"})
        if d.get("senha"):
            cfg["senha"] = str(d["senha"])[:200]
        if "vaga_id" in d:
            vid = d.get("vaga_id")
            if vid and not conn.execute("SELECT 1 FROM vagas WHERE id=? AND empresa_id=?", (vid, empresa_id)).fetchone():
                return _resp(h, 400, {"erro": "Vaga não encontrada"})
            cfg["vaga_id"] = int(vid) if vid else None
        for campo in ("ativo", "auto_fila"):
            if campo in d:
                cfg[campo] = bool(d[campo])
        if cfg["ativo"] and not (cfg["usuario"] and cfg["senha"] and cfg["imap_host"]):
            return _resp(h, 400, {"erro": "Preencha servidor, usuário e senha antes de ativar"})
        salvar(conn, empresa_id, cfg)
        return _resp(h, 200, {"ok": True, "config": config_publica(cfg)})

    if method == "POST" and path == "/api/gestor/entrada/testar":
        ok, msg, total = testar(config(conn, empresa_id))
        return _resp(h, 200 if ok else 400, {"ok": ok, "erro": "" if ok else msg, "mensagens_indeed": total})

    if method == "POST" and path == "/api/gestor/entrada/ler":
        if not _trava.acquire(blocking=False):
            return _resp(h, 409, {"erro": "A leitura já está em andamento"})
        try:
            resumo = ler_caixa(conn, empresa_id)
        finally:
            _trava.release()
        return _resp(h, 200 if not resumo["erro"] else 400, dict(resumo, ok=not resumo["erro"]))

    if method == "POST" and path == "/api/gestor/importar-csv":
        d = h._body()
        texto = d.get("csv") or ""
        if d.get("base64"):
            try:
                texto = base64.b64decode(d["base64"]).decode("utf-8-sig", errors="replace")
            except ValueError:
                return _resp(h, 400, {"erro": "Arquivo inválido"})
        if not texto.strip():
            return _resp(h, 400, {"erro": "Envie a planilha CSV"})
        vid = d.get("vaga_id")
        if vid and not conn.execute("SELECT 1 FROM vagas WHERE id=? AND empresa_id=?", (vid, empresa_id)).fetchone():
            return _resp(h, 400, {"erro": "Vaga não encontrada"})
        r = importar_csv(conn, empresa_id, texto, int(vid) if vid else None, bool(d.get("auto_fila")),
                         bool(d.get("aplicar")), gestor["nome"])
        return _resp(h, 200, r)

    return _resp(h, 404, {"erro": "Rota não encontrada"})


def _resp(h, status, dados):
    h._json(status, dados)
    return True
