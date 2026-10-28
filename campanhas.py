"""Reengajamento do banco de talentos: avisar candidatos antigos sobre uma vaga aberta.

O gestor abre uma vaga com status "aberta" e clica em "Avisar banco de talentos".
O painel mostra quem pode receber o aviso (mesma empresa, fora desta vaga, não
contratado, não anonimizado, com e-mail, sem descadastro, ainda não avisado sobre
esta vaga e sem encerramento de "não ligar" ou "número errado"), com filtros, a
contagem e a prévia do e-mail em cada idioma. O envio vai em segundo plano, com
pausas curtas, no idioma de cada candidato, até LIMITE e-mails por campanha.

Cada e-mail tem o link de candidatura e um link de descadastro
(/descadastrar?t=TOKEN). Abrir o link NÃO descadastra (leitores de links dos
provedores de e-mail abrem os links sozinhos): a página mostra o nome da
empresa e um botão "Confirmar" que faz POST em /api/descadastrar {t}. O
cabeçalho List-Unsubscribe aponta para /api/descadastrar?t=TOKEN, que também
aceita o descadastro de um clique da RFC 8058 (corpo
"List-Unsubscribe=One-Click"). O descadastro vale só para os e-mails de vagas
(marketing) daquela empresa: e-mails transacionais (entrevista, onboarding,
resultados) continuam. Ele também coloca a etiqueta "não contatar".

Tabelas: campanhas, campanha_envios, campanhas_tokens, campanhas_descadastros.
"""
import html as _html
import json
import re
import secrets
import threading
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

srv = None  # módulo server, injetado por ligar()

LIMITE = 200        # e-mails por campanha
PAUSA = 1.5         # segundos entre um e-mail e outro
SINCRONO = False    # testes: envia na mesma thread da requisição
TIERS = ("STRONG", "GOOD", "REVIEW", "LOW")  # do melhor para o pior (voz.py)
TAG_DESCADASTRO = "não contatar"
TAGS_BLOQUEIO = ("não contatar", "não ligar", "número errado")
VOZ_STATUS_BLOQUEIO = ("nao_ligar", "numero_errado")
VOZ_OUTCOME_BLOQUEIO = ("DO_NOT_CALL", "WRONG_NUMBER")
IDIOMAS = ("pt", "en", "es")

# textos da linha do tempo: gravados em português com server.registrar_evento e
# traduzidos na hora de mostrar (eventos_i18n.py, exemplos em teste_eventos.py)


def ligar(modulo_server):
    global srv
    srv = modulo_server


# ------------------------------------------------------------ banco

def init_campanhas(c):
    c.execute(
        "CREATE TABLE IF NOT EXISTS campanhas ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " vaga_id INTEGER NOT NULL,"
        " gestor TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " filtros TEXT DEFAULT '{}',"
        " total INTEGER DEFAULT 0,"
        " status TEXT DEFAULT 'enviando')"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS campanha_envios ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " campanha_id INTEGER NOT NULL REFERENCES campanhas(id) ON DELETE CASCADE,"
        " candidato_id INTEGER NOT NULL,"
        " idioma TEXT DEFAULT '',"
        " enviado_em TEXT DEFAULT '',"
        " status TEXT DEFAULT 'pendente',"
        " erro TEXT DEFAULT '',"
        " aberto_em TEXT DEFAULT '',"
        " UNIQUE(campanha_id, candidato_id))"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_campanha_envios_cand ON campanha_envios(candidato_id)")
    c.execute(
        "CREATE TABLE IF NOT EXISTS campanhas_tokens ("
        " token TEXT PRIMARY KEY,"
        " empresa_id INTEGER NOT NULL,"
        " candidato_id INTEGER NOT NULL,"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " UNIQUE(empresa_id, candidato_id))"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS campanhas_descadastros ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " candidato_id INTEGER,"
        " email TEXT NOT NULL,"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " UNIQUE(empresa_id, email))"
    )


def _agora():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _tags(cand):
    try:
        v = json.loads(cand["tags"] or "[]") if "tags" in cand.keys() else []
        return [str(x) for x in v] if isinstance(v, list) else []
    except (TypeError, ValueError):
        return []


def token_de(conn, empresa_id, candidato_id):
    r = conn.execute("SELECT token FROM campanhas_tokens WHERE empresa_id=? AND candidato_id=?",
                     (empresa_id, candidato_id)).fetchone()
    if r:
        return r["token"]
    token = secrets.token_urlsafe(24)
    conn.execute("INSERT INTO campanhas_tokens (token, empresa_id, candidato_id) VALUES (?,?,?)",
                 (token, empresa_id, candidato_id))
    return token


def descadastrado(conn, empresa_id, cand):
    email = (cand["email"] or "").strip().lower()
    return conn.execute(
        "SELECT criado_em FROM campanhas_descadastros WHERE empresa_id=? AND (candidato_id=? OR email=?)"
        " ORDER BY id LIMIT 1", (empresa_id, cand["id"], email)).fetchone()


# ------------------------------------------------------------ quem recebe

def normalizar_filtros(d):
    d = d if isinstance(d, dict) else {}
    cargo = "mesmo" if d.get("cargo") == "mesmo" else "qualquer"
    try:
        meses = max(0, min(120, int(d.get("meses") or 0)))
    except (TypeError, ValueError):
        meses = 0
    tier = str(d.get("tier") or "").upper()
    if tier not in TIERS[:3]:
        tier = ""
    tags = d.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    tags = [str(t).strip()[:60] for t in tags if str(t).strip()][:20]
    cidade = str(d.get("cidade") or "").strip()[:80]
    return {"cargo": cargo, "cidade": cidade, "meses": meses, "tier": tier, "tags": tags}


def _ids(conn, sql, params):
    return {r[0] for r in conn.execute(sql, params).fetchall()}


def elegiveis(conn, gestor, vaga, filtros):
    """Candidatos que podem receber o aviso desta vaga, do mais recente para o mais antigo."""
    eid = vaga["empresa_id"]
    f = normalizar_filtros(filtros)
    na_vaga = _ids(conn, "SELECT candidato_id FROM candidaturas WHERE vaga_id=?", (vaga["id"],))
    contratados = _ids(conn, "SELECT ca.candidato_id FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                             " WHERE v.empresa_id=? AND ca.etapa='contratado'", (eid,))
    bloq_voz = set()
    colunas = {r[1] for r in conn.execute("PRAGMA table_info(candidaturas)").fetchall()}
    if "voz_status" in colunas:
        bloq_voz = _ids(
            conn, "SELECT ca.candidato_id FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                  " WHERE v.empresa_id=? AND (ca.voz_status IN (%s) OR ca.voz_outcome IN (%s))"
                  % (",".join("?" * len(VOZ_STATUS_BLOQUEIO)), ",".join("?" * len(VOZ_OUTCOME_BLOQUEIO))),
            (eid,) + VOZ_STATUS_BLOQUEIO + VOZ_OUTCOME_BLOQUEIO)
    ja_avisados = _ids(conn, "SELECT e.candidato_id FROM campanha_envios e JOIN campanhas c ON c.id=e.campanha_id"
                             " WHERE c.vaga_id=? AND c.empresa_id=?", (vaga["id"], eid))
    sairam_ids = _ids(conn, "SELECT candidato_id FROM campanhas_descadastros WHERE empresa_id=?"
                            " AND candidato_id IS NOT NULL", (eid,))
    sairam_emails = _ids(conn, "SELECT email FROM campanhas_descadastros WHERE empresa_id=?", (eid,))

    historico = {}  # candidato_id -> {"cargos": set, "ultima": str, "tier": int}
    sel_tier = ", ca.voz_tier" if "voz_tier" in colunas else ", '' AS voz_tier"
    for r in conn.execute("SELECT ca.candidato_id, ca.criado_em, v.cargo_id" + sel_tier +
                          " FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id WHERE v.empresa_id=?", (eid,)):
        h = historico.setdefault(r["candidato_id"], {"cargos": set(), "ultima": "", "tier": 99})
        h["cargos"].add(r["cargo_id"])
        h["ultima"] = max(h["ultima"], r["criado_em"] or "")
        if r["voz_tier"] in TIERS:
            h["tier"] = min(h["tier"], TIERS.index(r["voz_tier"]))

    corte = ""
    if f["meses"]:
        corte = (datetime.utcnow() - timedelta(days=30 * f["meses"])).strftime("%Y-%m-%d %H:%M:%S")
    cidade = f["cidade"].lower()
    tags_filtro = {t.lower() for t in f["tags"]}
    vistos = set()
    saida = []
    for c in conn.execute("SELECT * FROM candidatos WHERE empresa_id=? AND COALESCE(anonimizado,0)=0"
                          " AND trim(COALESCE(email,''))<>''", (eid,)).fetchall():
        cid = c["id"]
        email = c["email"].strip().lower()
        if "@" not in email or email in vistos:
            continue
        if cid in na_vaga or cid in contratados or cid in bloq_voz or cid in ja_avisados:
            continue
        if cid in sairam_ids or email in sairam_emails:
            continue
        if ("tipo" in c.keys() and c["tipo"] == "interno") or not srv.gestor_ve_candidato(gestor, c):
            continue
        tags = _tags(c)
        tags_min = {t.lower() for t in tags}
        if tags_min & set(TAGS_BLOQUEIO):
            continue
        h = historico.get(cid) or {"cargos": set(), "ultima": "", "tier": 99}
        if f["cargo"] == "mesmo" and vaga["cargo_id"] not in h["cargos"] and c["cargo_desejado_id"] != vaga["cargo_id"]:
            continue
        if cidade and cidade not in (c["local"] or "").lower():
            continue
        ultima = h["ultima"] or (c["criado_em"] or "")
        if corte and ultima < corte:
            continue
        if f["tier"] and h["tier"] > TIERS.index(f["tier"]):
            continue
        if tags_filtro and not (tags_min & tags_filtro):
            continue
        vistos.add(email)
        saida.append({
            "id": cid, "nome": c["nome"], "email": c["email"].strip(), "local": c["local"] or "",
            "idioma": idioma_de(c), "ultima": ultima,
            "tier": TIERS[h["tier"]] if h["tier"] < len(TIERS) else "",
        })
    saida.sort(key=lambda x: (x["ultima"], x["id"]), reverse=True)
    return saida


def idioma_de(cand):
    return srv.mensagens.idioma(cand["idioma"] if "idioma" in cand.keys() else "", "pt")


# ------------------------------------------------------------ e-mail

T = {
    "pt": {
        "assunto": "Nova vaga na {empresa}: {vaga}",
        "ola": "Olá, {nome}!",
        "motivo": "Você se candidatou na {empresa} antes, por isso queremos contar que abrimos uma vaga que pode combinar com você.",
        "local": "Local", "pagamento": "Remuneração",
        "botao": "Quero me candidatar",
        "botao_falhou": "Se o botão não funcionar, copie este link no navegador:",
        "porque": "Você recebeu este e-mail porque se candidatou na {empresa} antes.",
        "sair": "Não quer mais receber vagas da {empresa}?", "sair_link": "Cancelar inscrição",
        "exemplo": "Maria",
        "unidades": {"hora": "por hora", "dia": "por dia", "semana": "por semana", "mes": "por mês", "ano": "por ano"},
        "pagina_conf_titulo": "Cancelar e-mails de vagas?",
        "pagina_conf": "Confirme para deixar de receber e-mails de vagas da {empresa}. Avisos sobre processos em andamento, como entrevistas, continuam chegando normalmente.",
        "pagina_botao": "Confirmar cancelamento",
        "pagina_falhou": "Não foi possível cancelar agora. Tente de novo em instantes.",
        "pagina_ok_titulo": "Inscrição cancelada",
        "pagina_ok": "Você não vai mais receber e-mails de vagas da {empresa}. Avisos sobre processos em andamento, como entrevistas, continuam chegando normalmente.",
        "pagina_erro_titulo": "Link inválido",
        "pagina_erro": "Este link de cancelamento não é válido ou expirou.",
    },
    "en": {
        "assunto": "New opening at {empresa}: {vaga}",
        "ola": "Hi {nome},",
        "motivo": "You applied to {empresa} before, so we wanted to let you know about a new opening that might be a good fit for you.",
        "local": "Location", "pagamento": "Pay",
        "botao": "Apply now",
        "botao_falhou": "If the button doesn't work, copy this link into your browser:",
        "porque": "You're getting this email because you applied to {empresa} before.",
        "sair": "Don't want job emails from {empresa}?", "sair_link": "Unsubscribe",
        "exemplo": "Mary",
        "unidades": {"hora": "per hour", "dia": "per day", "semana": "per week", "mes": "per month", "ano": "per year"},
        "pagina_conf_titulo": "Stop job emails?",
        "pagina_conf": "Confirm to stop getting job emails from {empresa}. Messages about an application in progress, like interviews, will still reach you.",
        "pagina_botao": "Confirm unsubscribe",
        "pagina_falhou": "We couldn't unsubscribe you right now. Please try again in a moment.",
        "pagina_ok_titulo": "You're unsubscribed",
        "pagina_ok": "You won't get job emails from {empresa} anymore. Messages about an application in progress, like interviews, will still reach you.",
        "pagina_erro_titulo": "Invalid link",
        "pagina_erro": "This unsubscribe link is not valid or has expired.",
    },
    "es": {
        "assunto": "Nueva vacante en {empresa}: {vaga}",
        "ola": "Hola, {nome}:",
        "motivo": "Te postulaste en {empresa} antes, así que queremos avisarte de una vacante nueva que podría interesarte.",
        "local": "Ubicación", "pagamento": "Pago",
        "botao": "Postularme",
        "botao_falhou": "Si el botón no funciona, copia este enlace en tu navegador:",
        "porque": "Recibes este correo porque te postulaste en {empresa} antes.",
        "sair": "¿No quieres recibir más vacantes de {empresa}?", "sair_link": "Cancelar suscripción",
        "exemplo": "María",
        "unidades": {"hora": "por hora", "dia": "por día", "semana": "por semana", "mes": "por mes", "ano": "por año"},
        "pagina_conf_titulo": "¿Dejar de recibir correos de vacantes?",
        "pagina_conf": "Confirma para dejar de recibir correos de vacantes de {empresa}. Los avisos sobre un proceso en curso, como entrevistas, te seguirán llegando.",
        "pagina_botao": "Confirmar cancelación",
        "pagina_falhou": "No pudimos cancelar la suscripción ahora. Inténtalo de nuevo en un momento.",
        "pagina_ok_titulo": "Suscripción cancelada",
        "pagina_ok": "Ya no recibirás correos de vacantes de {empresa}. Los avisos sobre un proceso en curso, como entrevistas, te seguirán llegando.",
        "pagina_erro_titulo": "Enlace inválido",
        "pagina_erro": "Este enlace para cancelar la suscripción no es válido o venció.",
    },
}

_UNIDADES = {
    "hora": "hora", "hour": "hora", "hr": "hora", "h": "hora", "hourly": "hora",
    "dia": "dia", "day": "dia", "daily": "dia",
    "semana": "semana", "week": "semana", "weekly": "semana",
    "mes": "mes", "mês": "mes", "month": "mes", "monthly": "mes",
    "ano": "ano", "year": "ano", "yearly": "ano", "annual": "ano",
}
_MOEDAS = {"USD": "$", "US$": "$", "$": "$", "BRL": "R$", "R$": "R$", "EUR": "€", "€": "€"}


def _e(s):
    return _html.escape(str(s or ""), quote=True)


def _campo(vaga, *nomes):
    chaves = vaga.keys()
    for n in nomes:
        if n in chaves and vaga[n] not in (None, ""):
            return vaga[n]
    return None


def _num(v):
    try:
        x = float(str(v).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None
    return x if x > 0 else None


def pagamento(vaga, lang):
    """Faixa de pagamento da vaga, se os campos existirem (lidos com cuidado)."""
    texto = _campo(vaga, "salario_texto", "salario", "pagamento")
    if isinstance(texto, str) and texto.strip() and _num(texto) is None:
        return texto.strip()[:80]
    minimo = _num(_campo(vaga, "salario_min", "salario_minimo", "pagamento_min"))
    maximo = _num(_campo(vaga, "salario_max", "salario_maximo", "pagamento_max"))
    if minimo is None and texto is not None:
        minimo = _num(texto)
    if minimo is None and maximo is None:
        return ""
    moeda = str(_campo(vaga, "salario_moeda", "moeda") or "").strip()
    simbolo = _MOEDAS.get(moeda.upper(), moeda + " " if moeda else "$")

    def fmt(x):
        return simbolo + ("{:,.0f}".format(x) if x >= 1000 or x == int(x) else "{:,.2f}".format(x))

    if minimo is not None and maximo is not None and maximo > minimo:
        faixa = "%s - %s" % (fmt(minimo), fmt(maximo))
    else:
        faixa = fmt(minimo if minimo is not None else maximo)
    unidade = _UNIDADES.get(str(_campo(vaga, "salario_unidade", "salario_periodo", "salario_tipo") or "").strip().lower())
    if unidade:
        faixa += " " + T[lang]["unidades"][unidade]
    return faixa


def _resumo(texto, limite=420):
    texto = re.sub(r"\s+", " ", texto or "").strip()
    if len(texto) <= limite:
        return texto
    corte = texto[:limite].rsplit(" ", 1)[0]
    return corte.rstrip(".,;:") + "..."


def montar_email(conn, vaga, empresa, cand_nome, lang, token):
    """(assunto, texto, html) do aviso no idioma pedido."""
    lang = lang if lang in IDIOMAS else "pt"
    t = T[lang]
    base = srv.url_publica(conn)
    marca = srv.mensagens.marca(conn, empresa["id"]) or {"nome": empresa["nome"], "logo_url": ""}
    nome_emp = empresa["nome"]
    primeiro = (cand_nome or "").strip().split(" ")[0] or t["exemplo"]
    link = "%s/candidato?vaga=%d&e=%s&lang=%s" % (base, vaga["id"], empresa["slug"], lang)
    sair = "%s/descadastrar?t=%s" % (base, token)
    assunto = t["assunto"].format(empresa=nome_emp, vaga=vaga["titulo"])
    local = (vaga["local"] or "").strip() if "local" in vaga.keys() else ""
    pago = pagamento(vaga, lang)
    resumo = _resumo(vaga["descricao"] if "descricao" in vaga.keys() else "")

    linhas = [t["ola"].format(nome=primeiro), "", t["motivo"].format(empresa=nome_emp), "", vaga["titulo"]]
    if local:
        linhas.append("%s: %s" % (t["local"], local))
    if pago:
        linhas.append("%s: %s" % (t["pagamento"], pago))
    if resumo:
        linhas += ["", resumo]
    linhas += ["", "%s: %s" % (t["botao"], link), "", t["porque"].format(empresa=nome_emp),
               "%s %s: %s" % (t["sair"].format(empresa=nome_emp), t["sair_link"], sair)]
    texto = "\n".join(linhas)

    detalhes = ""
    for rotulo, valor in ((t["local"], local), (t["pagamento"], pago)):
        if valor:
            detalhes += ('<div style="font-size:14px;color:#2b3648;margin:4px 0"><strong>%s:</strong> %s</div>'
                         % (_e(rotulo), _e(valor)))
    conteudo = (
        '<p style="margin:0 0 14px;font-size:15px;line-height:1.65;color:#2b3648">%s</p>' % _e(t["ola"].format(nome=primeiro))
        + '<p style="margin:0 0 18px;font-size:15px;line-height:1.65;color:#2b3648">%s</p>' % _e(t["motivo"].format(empresa=nome_emp))
        + '<div style="border:1px solid #e3e8f0;border-radius:14px;padding:18px 20px;margin:0 0 18px">'
        + '<div style="font-size:18px;font-weight:700;color:#101B37;margin-bottom:6px">%s</div>' % _e(vaga["titulo"])
        + detalhes
        + ('<p style="margin:10px 0 0;font-size:14px;line-height:1.6;color:#5E7086">%s</p>' % _e(resumo) if resumo else "")
        + '</div>'
        + srv.mensagens._botao(link, t["botao"])
        + '<p style="margin:0 0 16px;font-size:12px;color:#8a97a8">%s<br><a href="%s" style="color:#3258AB;word-break:break-all">%s</a></p>'
        % (_e(t["botao_falhou"]), _e(link), _e(link))
        + '<p style="margin:18px 0 0;font-size:12px;line-height:1.6;color:#8a97a8">%s<br>%s '
          '<a href="%s" style="color:#5E7086">%s</a></p>'
        % (_e(t["porque"].format(empresa=nome_emp)), _e(t["sair"].format(empresa=nome_emp)), _e(sair), _e(t["sair_link"]))
    )
    html = srv.mensagens.layout(conteudo, lang, marca)
    return assunto, texto, html


# ------------------------------------------------------------ envio

def criar_campanha(conn, gestor, vaga, filtros):
    lista = elegiveis(conn, gestor, vaga, filtros)[:LIMITE]
    if not lista:
        return None, 0
    cur = conn.execute(
        "INSERT INTO campanhas (empresa_id, vaga_id, gestor, filtros, total) VALUES (?,?,?,?,?)",
        (vaga["empresa_id"], vaga["id"], gestor["nome"], json.dumps(normalizar_filtros(filtros), ensure_ascii=False),
         len(lista)))
    campanha_id = cur.lastrowid
    for c in lista:
        conn.execute("INSERT INTO campanha_envios (campanha_id, candidato_id, idioma) VALUES (?,?,?)",
                     (campanha_id, c["id"], c["idioma"]))
    conn.commit()
    return campanha_id, len(lista)


def enviar_campanha(campanha_id):
    """Envia os e-mails pendentes da campanha (thread própria, conexão própria)."""
    conn = srv.db()
    try:
        camp = conn.execute("SELECT * FROM campanhas WHERE id=?", (campanha_id,)).fetchone()
        if not camp:
            return
        vaga = conn.execute("SELECT * FROM vagas WHERE id=?", (camp["vaga_id"],)).fetchone()
        empresa = conn.execute("SELECT * FROM empresas WHERE id=?", (camp["empresa_id"],)).fetchone()
        pendentes = conn.execute("SELECT * FROM campanha_envios WHERE campanha_id=? AND status='pendente' ORDER BY id",
                                 (campanha_id,)).fetchall()
        marca = srv.mensagens.marca(conn, camp["empresa_id"])
        for i, env in enumerate(pendentes):
            cand = conn.execute("SELECT * FROM candidatos WHERE id=? AND empresa_id=?",
                                (env["candidato_id"], camp["empresa_id"])).fetchone()
            if not vaga or not empresa or not cand or cand["anonimizado"] or descadastrado(conn, camp["empresa_id"], cand):
                conn.execute("UPDATE campanha_envios SET status='ignorado' WHERE id=?", (env["id"],))
                conn.commit()
                continue
            lang = env["idioma"] if env["idioma"] in IDIOMAS else idioma_de(cand)
            token = token_de(conn, camp["empresa_id"], cand["id"])
            assunto, texto, html = montar_email(conn, vaga, empresa, cand["nome"], lang, token)
            try:
                ok, msg = srv.enviar_email(conn, cand["email"].strip(), assunto, texto, html=html, marca=marca,
                                           idioma=lang, cabecalhos=cabecalhos_email(conn, token))
            except Exception as exc:  # noqa: BLE001
                ok, msg = False, str(exc)
            conn.execute("UPDATE campanha_envios SET status=?, erro=?, enviado_em=? WHERE id=?",
                         ("enviado" if ok else "falhou", "" if ok else str(msg)[:300], _agora(), env["id"]))
            srv.registrar_evento(conn, cand["id"], "email",
                                 ("Avisado por e-mail sobre a vaga: %s (banco de talentos)" if ok
                                  else "Falha ao avisar sobre a vaga: %s (banco de talentos)") % vaga["titulo"])
            conn.commit()
            if PAUSA and not SINCRONO and i < len(pendentes) - 1:
                time.sleep(PAUSA)
        conn.execute("UPDATE campanhas SET status='concluida' WHERE id=?", (campanha_id,))
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        import sys
        sys.stderr.write("campanhas: erro no envio %s: %r\n" % (campanha_id, exc))
    finally:
        conn.close()


def disparar(campanha_id):
    if SINCRONO:
        enviar_campanha(campanha_id)
    else:
        threading.Thread(target=enviar_campanha, args=(campanha_id,), daemon=True).start()


# ------------------------------------------------------------ painel

def historico(conn, vaga):
    saida = []
    for c in conn.execute("SELECT * FROM campanhas WHERE vaga_id=? AND empresa_id=? ORDER BY id DESC",
                          (vaga["id"], vaga["empresa_id"])).fetchall():
        cont = {r["status"]: r["n"] for r in conn.execute(
            "SELECT status, COUNT(*) AS n FROM campanha_envios WHERE campanha_id=? GROUP BY status", (c["id"],))}
        candidaturas = conn.execute(
            "SELECT COUNT(DISTINCT e.candidato_id) FROM campanha_envios e JOIN candidaturas ca"
            " ON ca.candidato_id=e.candidato_id AND ca.vaga_id=?"
            " WHERE e.campanha_id=? AND e.status='enviado' AND ca.criado_em >= e.enviado_em",
            (c["vaga_id"], c["id"])).fetchone()[0]
        try:
            filtros = json.loads(c["filtros"] or "{}")
        except ValueError:
            filtros = {}
        saida.append({
            "id": c["id"], "criado_em": c["criado_em"], "gestor": c["gestor"], "total": c["total"],
            "status": c["status"], "enviados": cont.get("enviado", 0), "falhas": cont.get("falhou", 0),
            "pendentes": cont.get("pendente", 0), "candidaturas": candidaturas, "filtros": filtros,
        })
    return saida


def _tags_da_empresa(conn, gestor):
    todas = set()
    for c in conn.execute("SELECT tags, local, empresa_id FROM candidatos WHERE empresa_id=? AND COALESCE(anonimizado,0)=0",
                          (gestor["empresa_id"],)).fetchall():
        for t in _tags(c):
            if t.lower() not in TAGS_BLOQUEIO:
                todas.add(t)
    return sorted(todas, key=str.lower)[:200]


def _vaga_do_gestor(conn, gestor, vaga_id):
    return conn.execute("SELECT v.*, c.nome AS cargo_nome FROM vagas v LEFT JOIN cargos c ON c.id=v.cargo_id"
                        " WHERE v.id=? AND v.empresa_id=?", (vaga_id, gestor["empresa_id"])).fetchone()


def _resp(h, status, dados):
    h._json(status, dados)
    return True


def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/campanhas/"):
        return None

    m = re.match(r"^/api/gestor/campanhas/candidato/(\d+)$", path)
    if m and method == "GET":
        cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)).fetchone()
        if not cand or not srv.gestor_ve_candidato(gestor, cand):
            return _resp(h, 404, {"erro": "Candidato não encontrado"})
        saiu = descadastrado(conn, gestor["empresa_id"], cand)
        envios = [{"vaga_id": r["vaga_id"], "vaga": r["titulo"], "status": r["status"],
                   "enviado_em": r["enviado_em"] or r["criado_em"]}
                  for r in conn.execute(
                      "SELECT e.status, e.enviado_em, c.criado_em, c.vaga_id, v.titulo FROM campanha_envios e"
                      " JOIN campanhas c ON c.id=e.campanha_id JOIN vagas v ON v.id=c.vaga_id"
                      " WHERE e.candidato_id=? AND c.empresa_id=? ORDER BY e.id DESC LIMIT 20",
                      (cand["id"], gestor["empresa_id"])).fetchall()]
        return _resp(h, 200, {"descadastrado": bool(saiu), "descadastrado_em": saiu["criado_em"] if saiu else "",
                              "envios": envios})

    m = re.match(r"^/api/gestor/campanhas/vaga/(\d+)(/previa|/enviar)?$", path)
    if not m:
        return _resp(h, 404, {"erro": "Rota não encontrada"})
    vaga = _vaga_do_gestor(conn, gestor, int(m.group(1)))
    if not vaga:
        return _resp(h, 404, {"erro": "Vaga não encontrada"})
    acao = m.group(2) or ""

    if method == "GET" and not acao:
        return _resp(h, 200, {
            "vaga": {"id": vaga["id"], "titulo": vaga["titulo"], "status": vaga["status"],
                     "cargo_nome": vaga["cargo_nome"] or ""},
            "campanhas": historico(conn, vaga), "tags": _tags_da_empresa(conn, gestor),
            "limite": LIMITE, "smtp": bool(srv.config_get(conn, "smtp_host")),
        })

    if method != "POST" or not acao:
        return _resp(h, 404, {"erro": "Rota não encontrada"})
    d = h._body()
    filtros = normalizar_filtros(d.get("filtros") if isinstance(d, dict) else {})

    if acao == "/previa":
        lista = elegiveis(conn, gestor, vaga, filtros)
        empresa = conn.execute("SELECT * FROM empresas WHERE id=?", (vaga["empresa_id"],)).fetchone()
        por_idioma = {k: 0 for k in IDIOMAS}
        for c in lista[:LIMITE]:
            por_idioma[c["idioma"]] = por_idioma.get(c["idioma"], 0) + 1
        emails = {}
        for lang in IDIOMAS:
            assunto, _, html = montar_email(conn, vaga, empresa, "", lang, "exemplo")
            emails[lang] = {"assunto": assunto, "html": html}
        return _resp(h, 200, {
            "total": len(lista), "enviar": min(len(lista), LIMITE), "limite": LIMITE, "por_idioma": por_idioma,
            "amostra": [{k: c[k] for k in ("id", "nome", "local", "idioma", "ultima", "tier")} for c in lista[:50]],
            "emails": emails, "filtros": filtros,
        })

    # acao == "/enviar"
    if vaga["status"] != "aberta":
        return _resp(h, 400, {"erro": "A vaga precisa estar aberta para avisar o banco de talentos"})
    if not srv.config_get(conn, "smtp_host"):
        return _resp(h, 400, {"erro": "Configure o envio de e-mails (SMTP) antes de avisar o banco de talentos"})
    campanha_id, total = criar_campanha(conn, gestor, vaga, filtros)
    if not campanha_id:
        return _resp(h, 400, {"erro": "Nenhum candidato para avisar com esses filtros"})
    disparar(campanha_id)
    return _resp(h, 200, {"ok": True, "campanha_id": campanha_id, "total": total})


# ------------------------------------------------------------ descadastro (página pública)

def _limpar_token(token):
    return re.sub(r"[^A-Za-z0-9_-]", "", token or "")[:64]


def buscar_token(conn, token):
    """(candidato, empresa) do token, sem alterar nada; (None, None) se inválido."""
    token = _limpar_token(token)
    if not token:
        return None, None
    r = conn.execute("SELECT * FROM campanhas_tokens WHERE token=?", (token,)).fetchone()
    if not r:
        return None, None
    cand = conn.execute("SELECT * FROM candidatos WHERE id=? AND empresa_id=?", (r["candidato_id"], r["empresa_id"])).fetchone()
    empresa = conn.execute("SELECT * FROM empresas WHERE id=?", (r["empresa_id"],)).fetchone()
    if not cand or not empresa:
        return None, None
    return cand, empresa


def descadastrar(conn, token):
    """Aplica o descadastro. Devolve (candidato, empresa) ou (None, None)."""
    cand, empresa = buscar_token(conn, token)
    if cand is None:
        return None, None
    if not descadastrado(conn, empresa["id"], cand):
        conn.execute("INSERT OR IGNORE INTO campanhas_descadastros (empresa_id, candidato_id, email) VALUES (?,?,?)",
                     (empresa["id"], cand["id"], (cand["email"] or "").strip().lower()))
        tags = _tags(cand)
        if TAG_DESCADASTRO not in tags:
            tags.append(TAG_DESCADASTRO)
            conn.execute("UPDATE candidatos SET tags=? WHERE id=?", (json.dumps(tags, ensure_ascii=False), cand["id"]))
        srv.registrar_evento(conn, cand["id"], "sistema", "Cancelou os e-mails de vagas da empresa")
        conn.commit()
    return cand, empresa


def cabecalhos_email(conn, token):
    """Cabeçalhos List-Unsubscribe (RFC 2369) e List-Unsubscribe-Post (RFC 8058)."""
    return {
        "List-Unsubscribe": "<%s/api/descadastrar?t=%s>, <mailto:privacy@tonybelleza.com?subject=unsubscribe>"
                            % (srv.url_publica(conn), token),
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


_HTML_LANG = {"pt": "pt-BR", "en": "en", "es": "es"}


def pagina(lang, estado, empresa_nome, token):
    """estado: "confirmar" (botão), "ok" (já cancelado) ou "erro" (link inválido)."""
    t = T[lang]
    token = _limpar_token(token)
    titulo_ok = t["pagina_ok_titulo"]
    texto_ok = t["pagina_ok"].format(empresa=empresa_nome)
    if estado == "confirmar":
        titulo, texto = t["pagina_conf_titulo"], t["pagina_conf"].format(empresa=empresa_nome)
    elif estado == "ok":
        titulo, texto = titulo_ok, texto_ok
    else:
        titulo, texto = t["pagina_erro_titulo"], t["pagina_erro"]
    trocas = " · ".join(
        ('<strong>%s</strong>' % rot) if cod == lang else
        '<a href="/descadastrar?t=%s&amp;lang=%s">%s</a>' % (_e(token), cod, rot)
        for cod, rot in (("en", "English"), ("pt", "Português"), ("es", "Español")))
    acao = ""
    if estado == "confirmar":
        # sem JavaScript o formulário também funciona (o servidor devolve esta página)
        acao = (
            '<form id="f" method="post" action="/api/descadastrar?t=%s&amp;lang=%s">'
            '<input type="hidden" name="List-Unsubscribe" value="One-Click">'
            '<button type="submit" id="b">%s</button></form><p id="falhou" class="falhou" hidden>%s</p>'
            '<script>(function(){var f=document.getElementById("f"),b=document.getElementById("b");'
            'f.addEventListener("submit",function(ev){ev.preventDefault();b.disabled=true;'
            'fetch("/api/descadastrar",{method:"POST",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify({t:%s})}).then(function(r){if(!r.ok)throw r;return r.json();})'
            '.then(function(){document.getElementById("t").textContent=%s;'
            'document.getElementById("x").textContent=%s;document.title=%s;f.remove();'
            'document.getElementById("falhou").hidden=true;})'
            '.catch(function(){b.disabled=false;document.getElementById("falhou").hidden=false;});});})();</script>'
            % (_e(token), lang, _e(t["pagina_botao"]), _e(t["pagina_falhou"]),
               _js(token), _js(titulo_ok), _js(texto_ok), _js(titulo_ok)))
    return (
        '<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex"><title>%s</title>'
        '<style>body{margin:0;background:#eef1f6;font-family:Arial,Helvetica,sans-serif;color:#2b3648}'
        '.caixa{max-width:520px;margin:48px auto;background:#fff;border-radius:18px;padding:32px 28px;'
        'box-shadow:0 10px 34px rgba(16,27,55,.10)}h1{font-size:22px;color:#101B37;margin:0 0 12px}'
        'p{font-size:15px;line-height:1.65;margin:0 0 16px}.idiomas{font-size:13px;color:#8a97a8;margin-top:22px}'
        'a{color:#3258AB}.empresa{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#8a97a8;margin-bottom:14px}'
        'button{background:#3258AB;color:#fff;border:0;border-radius:12px;padding:12px 22px;font-size:15px;'
        'font-weight:700;cursor:pointer}button:disabled{opacity:.6;cursor:default}.falhou{color:#b42318;font-size:14px;margin-top:12px}'
        '@media (max-width:560px){.caixa{margin:16px;padding:24px 18px}}</style></head><body>'
        '<div class="caixa">%s<h1 id="t">%s</h1><p id="x">%s</p>%s<div class="idiomas">%s</div></div></body></html>'
        % (_HTML_LANG[lang], _e(titulo), ('<div class="empresa">%s</div>' % _e(empresa_nome)) if empresa_nome else "",
           _e(titulo), _e(texto), acao, trocas)
    )


def _js(valor):
    """String JSON segura dentro de <script>."""
    return json.dumps(str(valor)).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _idioma_pagina(lang_url, cand):
    if lang_url in IDIOMAS:
        return lang_url
    return idioma_de(cand) if cand is not None else "en"


def _html_resp(h, status, corpo):
    corpo = corpo.encode("utf-8")
    h.send_response(status)
    h.send_header("Content-Type", "text/html; charset=utf-8")
    h.send_header("Content-Length", str(len(corpo)))
    h.send_header("Cache-Control", "no-store")
    h.send_header("X-Robots-Tag", "noindex")
    h.send_header("Referrer-Policy", "no-referrer")
    h.end_headers()
    h.wfile.write(corpo)
    return True


def servir_descadastro(h):
    """GET /descadastrar?t=TOKEN: só mostra a página com o botão de confirmar (não descadastra)."""
    qs = parse_qs(urlparse(h.path).query)
    token = qs.get("t", [""])[0]
    lang_url = (qs.get("lang", [""])[0] or "").strip().lower()[:2]
    conn = srv.db()
    try:
        cand, empresa = buscar_token(conn, token)
        ja_saiu = bool(cand is not None and descadastrado(conn, empresa["id"], cand))
    except Exception as exc:  # noqa: BLE001
        import sys
        sys.stderr.write("campanhas: erro na página de descadastro: %r\n" % exc)
        cand, empresa, ja_saiu = None, None, False
    finally:
        conn.close()
    lang = _idioma_pagina(lang_url, cand)
    if cand is None:
        return _html_resp(h, 404, pagina(lang, "erro", "", token))
    return _html_resp(h, 200, pagina(lang, "ok" if ja_saiu else "confirmar", empresa["nome"], token))


def rotear_publico(h, method, path, conn):
    """POST /api/descadastrar: {t} em JSON (botão da página) ou ?t=TOKEN com o corpo
    "List-Unsubscribe=One-Click" (RFC 8058, enviado pelo provedor de e-mail)."""
    if path != "/api/descadastrar":
        return None
    if method != "POST":
        return _resp(h, 404, {"erro": "Rota não encontrada"})
    qs = parse_qs(urlparse(h.path).query)
    d = h._body()
    token = (d.get("t") if isinstance(d, dict) else "") or qs.get("t", [""])[0]
    if not isinstance(token, str):
        token = ""
    tipo = (h.headers.get("Content-Type") or "").lower()
    formulario = tipo.startswith("application/x-www-form-urlencoded")
    navegador = formulario and "text/html" in (h.headers.get("Accept") or "")
    cand, empresa = descadastrar(conn, token)
    if navegador:  # formulário da página sem JavaScript
        lang = _idioma_pagina((qs.get("lang", [""])[0] or "").strip().lower()[:2], cand)
        if cand is None:
            return _html_resp(h, 404, pagina(lang, "erro", "", token))
        return _html_resp(h, 200, pagina(lang, "ok", empresa["nome"], token))
    if cand is None:
        return _resp(h, 404, {"erro": "Não encontrado"})
    return _resp(h, 200, {"ok": True, "empresa": empresa["nome"]})
