"""
Números de telefone por empresa e alertas de uso da Bússola.

1. Números próprios: o dono configura a Twilio (Account SID e Auth Token) em
   Integrações e, no cartão de cada empresa, busca números locais dos EUA por
   código de área, compra um (só com confirmação explícita do custo mensal),
   importa na ElevenLabs como número Twilio do agente da plataforma e guarda
   em numeros_empresa. Também anexa um número que já está na conta Twilio e
   libera um número (sai da ElevenLabs e depois é devolvido à Twilio).
   voz.gateway() usa o phone_number_id da empresa quando ela tem número ativo;
   senão, o número padrão da plataforma.
2. Alertas de uso: quando o uso de minutos de voz do mês passa de 80% e de 100%
   do limite, os administradores da empresa recebem um e-mail (no idioma de
   cada um, com a logo da empresa) uma única vez por mês e por limiar; o dono
   (config dono_email) também recebe o aviso de 100%. A tabela alertas_uso
   impede repetição. planos.voz_bloqueada() (antes de cada ligação) e a rotina
   diária chamam verificar_alerta().

Sem dependências externas: urllib com timeout. Segredos nunca vão para log,
erro ou auditoria.
"""
import json
import re
import socket
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

srv = None  # módulo do servidor, injetado por ligar()

TWILIO_API = "https://api.twilio.com/2010-04-01"
ELEVENLABS_API = "https://api.elevenlabs.io/v1/convai"
TIMEOUT = 20
ENVIO_EM_SEGUNDO_PLANO = True  # os testes desligam para conferir os e-mails na hora
LIMIARES = (80, 100)
E164_RE = re.compile(r"^\+1[2-9]\d{2}[2-9]\d{6}$")
DDD_RE = re.compile(r"^[2-9]\d{2}$")
SID_RE = re.compile(r"^AC[0-9a-fA-F]{32}$")
IDIOMAS = ("pt", "en", "es")


def ligar(modulo_servidor):
    global srv
    srv = modulo_servidor


def init_telefonia(c):
    """Tabelas do módulo. Chamado dentro de init_db() com o cursor aberto."""
    c.execute(
        "CREATE TABLE IF NOT EXISTS numeros_empresa ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,"
        " numero TEXT NOT NULL,"
        " twilio_sid TEXT DEFAULT '',"
        " elevenlabs_phone_id TEXT DEFAULT '',"
        " origem TEXT DEFAULT 'comprado',"      # comprado ou anexado
        " status TEXT DEFAULT 'pendente',"      # pendente, ativo ou liberado
        " comprado_em TEXT DEFAULT (datetime('now')),"
        " liberado_em TEXT DEFAULT '',"
        " erro TEXT DEFAULT '')"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_numeros_empresa ON numeros_empresa(empresa_id, status)")
    c.execute(
        "CREATE TABLE IF NOT EXISTS alertas_uso ("
        " empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,"
        " mes TEXT NOT NULL,"
        " limiar INTEGER NOT NULL,"
        " minutos INTEGER DEFAULT 0,"
        " limite INTEGER DEFAULT 0,"
        " enviados INTEGER DEFAULT 0,"
        " enviado_em TEXT DEFAULT (datetime('now')),"
        " PRIMARY KEY (empresa_id, mes, limiar))"
    )


class ErroTelefonia(Exception):
    """Erro com mensagem em português (traduzida por erros_i18n) e status HTTP."""

    def __init__(self, mensagem, status=400, extra=None):
        Exception.__init__(self, mensagem)
        self.mensagem = mensagem
        self.status = status
        self.extra = extra or {}


# ------------------------------------------------------------ HTTP externo

def _limpar(texto, segredos=()):
    """Detalhe de erro externo sem segredos e curto."""
    texto = str(texto or "")
    for s in segredos:
        if s:
            texto = texto.replace(s, "***")
    return re.sub(r"\s+", " ", texto).strip()[:200]


def _http(metodo, url, corpo=None, headers=None, form=False, servico="Twilio"):
    """(status, json) da chamada. Erro de rede vira ErroTelefonia (502)."""
    h = dict(headers or {})
    dados = None
    if corpo is not None:
        if form:
            dados = urllib.parse.urlencode(corpo).encode("utf-8")
            h["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            dados = json.dumps(corpo).encode("utf-8")
            h["Content-Type"] = "application/json"
    h.setdefault("Accept", "application/json")
    req = urllib.request.Request(url, data=dados, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status, bruto = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, bruto = exc.code, exc.read()
    except (urllib.error.URLError, socket.timeout, OSError):
        raise ErroTelefonia("Sem conexão com a %s. Tente de novo." % servico, 502)
    try:
        conteudo = json.loads(bruto.decode("utf-8")) if bruto else {}
    except (ValueError, UnicodeDecodeError):
        conteudo = {}
    return status, conteudo


def twilio_credenciais(conn):
    sid = (srv.config_get(conn, "twilio_account_sid") or "").strip()
    token = (srv.config_get(conn, "twilio_auth_token") or "").strip()
    if not (sid and token):
        raise ErroTelefonia("Configure a Twilio em Integrações primeiro", 400)
    return sid, token


def _twilio(conn, metodo, caminho, corpo=None, aceitar_404=False):
    sid, token = twilio_credenciais(conn)
    import base64
    auth = base64.b64encode(("%s:%s" % (sid, token)).encode("utf-8")).decode("ascii")
    url = "%s/Accounts/%s/%s" % (TWILIO_API, urllib.parse.quote(sid), caminho)
    status, r = _http(metodo, url, corpo, {"Authorization": "Basic " + auth}, form=True, servico="Twilio")
    if status == 404 and aceitar_404:
        return None
    if status >= 400:
        if status in (401, 403):
            raise ErroTelefonia("A Twilio recusou as credenciais. Confira o Account SID e o Auth Token.", 502)
        detalhe = _limpar(r.get("message") if isinstance(r, dict) else "", (sid, token)) or ("HTTP %d" % status)
        raise ErroTelefonia("Erro na Twilio: %s" % detalhe, 502)
    return r


def elevenlabs_credenciais(conn):
    chave = (srv.config_get(conn, "elevenlabs_api_key") or "").strip()
    agente = (srv.config_get(conn, "elevenlabs_agent_id") or "").strip()
    if not (chave and agente):
        raise ErroTelefonia("Configure a ElevenLabs (chave e agente) em Integrações primeiro", 400)
    return chave, agente


def _elevenlabs(conn, metodo, caminho, corpo=None, aceitar_404=False):
    chave, _ = elevenlabs_credenciais(conn)
    status, r = _http(metodo, ELEVENLABS_API + caminho, corpo, {"xi-api-key": chave}, servico="ElevenLabs")
    if status == 404 and aceitar_404:
        return None
    if status >= 400:
        if status in (401, 403):
            raise ErroTelefonia("A ElevenLabs recusou a chave da API. Confira em Integrações.", 502)
        detalhe = ""
        if isinstance(r, dict):
            d = r.get("detail")
            detalhe = d.get("message") if isinstance(d, dict) else (d if isinstance(d, str) else r.get("message"))
        segredos = (chave,) + twilio_segredos(conn)
        raise ErroTelefonia("Erro na ElevenLabs: %s" % (_limpar(detalhe, segredos) or ("HTTP %d" % status)), 502)
    return r


def twilio_segredos(conn):
    return tuple(x for x in (srv.config_get(conn, "twilio_account_sid"), srv.config_get(conn, "twilio_auth_token")) if x)


# ------------------------------------------------------------ números

def custo_mensal(conn):
    """Custo do número local (premissa do dono, US$ por mês) e preço do número extra no catálogo."""
    planos = getattr(srv, "planos", None)
    custo, preco = 1.15, 0
    if planos is not None:
        try:
            custo = float(planos.premissas(conn).get("custo_numero", custo))
            preco = float(planos.catalogo(conn)["addons"].get("numero_extra", 0))
        except Exception:  # noqa: BLE001
            pass
    return custo, preco


def _empresa(conn, empresa_id):
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    if not e:
        raise ErroTelefonia("Empresa não encontrada", 404)
    return e


def _numero_e164(numero):
    n = re.sub(r"[^\d+]", "", str(numero or ""))
    if re.match(r"^\d{10}$", n):
        n = "+1" + n
    elif re.match(r"^1\d{10}$", n):
        n = "+" + n
    if not E164_RE.match(n):
        raise ErroTelefonia("Número inválido: use o formato +1XXXXXXXXXX", 400)
    return n


def _publico(r):
    return {
        "id": r["id"], "empresa_id": r["empresa_id"], "numero": r["numero"], "twilio_sid": r["twilio_sid"],
        "elevenlabs_phone_id": r["elevenlabs_phone_id"], "origem": r["origem"], "status": r["status"],
        "comprado_em": r["comprado_em"], "liberado_em": r["liberado_em"], "erro": r["erro"],
    }


def numeros(conn, empresa_id=None, incluir_liberados=False):
    sql = "SELECT * FROM numeros_empresa WHERE 1=1"
    args = []
    if empresa_id is not None:
        sql += " AND empresa_id=?"
        args.append(empresa_id)
    if not incluir_liberados:
        sql += " AND status != 'liberado'"
    return [_publico(r) for r in conn.execute(sql + " ORDER BY id DESC", args).fetchall()]


def phone_id_da_empresa(conn, empresa_id):
    """phone_number_id da ElevenLabs do número ativo mais recente da empresa (ou None)."""
    try:
        r = conn.execute(
            "SELECT elevenlabs_phone_id FROM numeros_empresa WHERE empresa_id=? AND status='ativo'"
            " AND elevenlabs_phone_id != '' ORDER BY id DESC LIMIT 1", (empresa_id,)
        ).fetchone()
    except Exception:  # noqa: BLE001
        return None
    return r[0] if r else None


def buscar_disponiveis(conn, ddd, limite=20):
    ddd = str(ddd or "").strip()
    if not DDD_RE.match(ddd):
        raise ErroTelefonia("Código de área inválido: use 3 dígitos, ex.: 860", 400)
    qs = urllib.parse.urlencode({"AreaCode": ddd, "VoiceEnabled": "true", "SmsEnabled": "true",
                                 "PageSize": max(1, min(int(limite), 50))})
    r = _twilio(conn, "GET", "AvailablePhoneNumbers/US/Local.json?" + qs)
    return [{"numero": n.get("phone_number", ""), "formatado": n.get("friendly_name", ""),
             "cidade": n.get("locality") or "", "estado": n.get("region") or ""}
            for n in (r.get("available_phone_numbers") or []) if n.get("phone_number")]


def _ja_usado(conn, numero):
    return conn.execute("SELECT 1 FROM numeros_empresa WHERE numero=? AND status != 'liberado'", (numero,)).fetchone()


def _auditar(conn, acao, alvo, empresa_id, ip=""):
    seg = getattr(srv, "seguranca", None)
    if seg is not None:
        seg.registrar(conn, acao, None, alvo, ip or "", empresa_id=empresa_id, quem="dono")


def comprar(conn, empresa_id, numero, confirmar, ip=""):
    """Compra o número na Twilio (só com confirmar=True) e importa na ElevenLabs."""
    e = _empresa(conn, empresa_id)
    numero = _numero_e164(numero)
    custo, preco = custo_mensal(conn)
    if confirmar is not True:
        raise ErroTelefonia("Confirme a compra e o custo mensal do número", 400,
                            {"confirmacao_necessaria": True, "custo_mensal": custo, "preco_numero_extra": preco})
    if _ja_usado(conn, numero):
        raise ErroTelefonia("Este número já está em uso na plataforma", 409)
    twilio_credenciais(conn)
    elevenlabs_credenciais(conn)  # confere antes de gastar dinheiro
    r = _twilio(conn, "POST", "IncomingPhoneNumbers.json",
                {"PhoneNumber": numero, "FriendlyName": ("Bussola %s" % e["nome"])[:64]})
    nid = conn.execute(
        "INSERT INTO numeros_empresa (empresa_id, numero, twilio_sid, origem, status) VALUES (?,?,?,?, 'pendente')",
        (e["id"], r.get("phone_number") or numero, r.get("sid") or "", "comprado"),
    ).lastrowid
    conn.commit()
    _auditar(conn, "telefonia comprar", "%s (US$ %.2f/mes)" % (numero, custo), e["id"], ip)
    return importar(conn, nid, ip)


def anexar(conn, empresa_id, numero, ip=""):
    """Anexa um número que já está na conta Twilio e importa na ElevenLabs."""
    e = _empresa(conn, empresa_id)
    numero = _numero_e164(numero)
    if _ja_usado(conn, numero):
        raise ErroTelefonia("Este número já está em uso na plataforma", 409)
    elevenlabs_credenciais(conn)
    r = _twilio(conn, "GET", "IncomingPhoneNumbers.json?" + urllib.parse.urlencode({"PhoneNumber": numero}))
    achados = [x for x in (r.get("incoming_phone_numbers") or []) if x.get("phone_number") == numero]
    if not achados:
        raise ErroTelefonia("Este número não está na sua conta Twilio", 404)
    nid = conn.execute(
        "INSERT INTO numeros_empresa (empresa_id, numero, twilio_sid, origem, status) VALUES (?,?,?,?, 'pendente')",
        (e["id"], numero, achados[0].get("sid") or "", "anexado"),
    ).lastrowid
    conn.commit()
    _auditar(conn, "telefonia anexar", numero, e["id"], ip)
    return importar(conn, nid, ip)


def _registro(conn, nid):
    r = conn.execute("SELECT * FROM numeros_empresa WHERE id=?", (nid,)).fetchone()
    if not r:
        raise ErroTelefonia("Número não encontrado", 404)
    return r


def importar(conn, nid, ip=""):
    """Importa (ou termina de importar) o número na ElevenLabs e liga ao agente da plataforma."""
    r = _registro(conn, nid)
    if r["status"] == "liberado":
        raise ErroTelefonia("Este número já foi liberado", 409)
    _, agente = elevenlabs_credenciais(conn)
    sid, token = twilio_credenciais(conn)
    phone_id = r["elevenlabs_phone_id"]
    try:
        if not phone_id:
            e = _empresa(conn, r["empresa_id"])
            resp = _elevenlabs(conn, "POST", "/phone-numbers", {
                "phone_number": r["numero"], "label": ("Bussola %s" % e["nome"])[:60],
                "provider": "twilio", "sid": sid, "token": token,
            })
            phone_id = (resp or {}).get("phone_number_id") or ""
            if not phone_id:
                raise ErroTelefonia("Erro na ElevenLabs: resposta sem phone_number_id", 502)
            conn.execute("UPDATE numeros_empresa SET elevenlabs_phone_id=? WHERE id=?", (phone_id, nid))
            conn.commit()
        _elevenlabs(conn, "PATCH", "/phone-numbers/" + urllib.parse.quote(phone_id), {"agent_id": agente})
    except ErroTelefonia as exc:
        conn.execute("UPDATE numeros_empresa SET erro=? WHERE id=?", (exc.mensagem[:300], nid))
        conn.commit()
        raise ErroTelefonia("O número está na Twilio, mas a importação na ElevenLabs falhou. %s" % exc.mensagem,
                            exc.status, {"numero": _publico(_registro(conn, nid))})
    conn.execute("UPDATE numeros_empresa SET status='ativo', erro='' WHERE id=?", (nid,))
    conn.commit()
    _auditar(conn, "telefonia importar", r["numero"], r["empresa_id"], ip)
    return _publico(_registro(conn, nid))


def liberar(conn, nid, confirmar, manter_twilio=False, ip=""):
    """Remove da ElevenLabs e devolve à Twilio (ou só desanexa, com manter_twilio)."""
    r = _registro(conn, nid)
    if confirmar is not True:
        raise ErroTelefonia("Confirme a liberação do número", 400, {"confirmacao_necessaria": True})
    if r["status"] == "liberado":
        raise ErroTelefonia("Este número já foi liberado", 409)
    if r["elevenlabs_phone_id"]:
        _elevenlabs(conn, "DELETE", "/phone-numbers/" + urllib.parse.quote(r["elevenlabs_phone_id"]), aceitar_404=True)
        conn.execute("UPDATE numeros_empresa SET elevenlabs_phone_id='', status='pendente' WHERE id=?", (nid,))
        conn.commit()
    if not manter_twilio and r["twilio_sid"]:
        _twilio(conn, "DELETE", "IncomingPhoneNumbers/%s.json" % urllib.parse.quote(r["twilio_sid"]), aceitar_404=True)
    conn.execute("UPDATE numeros_empresa SET status='liberado', liberado_em=datetime('now'), erro='' WHERE id=?", (nid,))
    conn.commit()
    _auditar(conn, "telefonia desanexar" if manter_twilio else "telefonia liberar", r["numero"], r["empresa_id"], ip)
    return _publico(_registro(conn, nid))


# ------------------------------------------------------------ alertas de uso

MESES = {
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
           "outubro", "novembro", "dezembro"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
           "October", "November", "December"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
           "octubre", "noviembre", "diciembre"],
}

TEXTOS = {
    "pt": {
        "assunto_80": "{empresa}: 80% dos minutos de voz de {mes} já foram usados",
        "assunto_100": "{empresa}: os minutos de voz de {mes} acabaram",
        "corpo": ("Olá, {nome}!\n\nA {empresa} usou {minutos} dos {limite} minutos de triagem por voz do plano "
                  "{plano} em {mes} ({pct}%).\n\n{situacao}\n\n{acao}\n{url}\n\nEquipe Bússola"),
        "situacao_80": "Quando chegar a 100%, as novas ligações de triagem ficam pausadas até o mês que vem.",
        "situacao_100_pausa": "As novas ligações de triagem estão pausadas até o mês que vem ou até a troca de plano.",
        "situacao_100_excedente": "As ligações continuam, e os minutos extras são cobrados como excedente.",
        "acao_upgrade": "Para ter mais minutos, mude para o plano {proximo}:",
        "acao_mais": "Para ter mais minutos, veja as opções do seu plano:",
        "teste": "teste grátis",
    },
    "en": {
        "assunto_80": "{empresa}: 80% of the {mes} voice minutes are used",
        "assunto_100": "{empresa}: the {mes} voice minutes are used up",
        "corpo": ("Hi {nome},\n\n{empresa} has used {minutos} of the {limite} voice screening minutes in the "
                  "{plano} plan for {mes} ({pct}%).\n\n{situacao}\n\n{acao}\n{url}\n\nThe Bússola team"),
        "situacao_80": "Once usage reaches 100%, new screening calls are paused until next month.",
        "situacao_100_pausa": "New screening calls are paused until next month or until you change your plan.",
        "situacao_100_excedente": "Calls keep going, and the extra minutes are billed as overage.",
        "acao_upgrade": "To get more minutes, upgrade to the {proximo} plan:",
        "acao_mais": "To get more minutes, see the options for your plan:",
        "teste": "free trial",
    },
    "es": {
        "assunto_80": "{empresa}: ya se usó el 80% de los minutos de voz de {mes}",
        "assunto_100": "{empresa}: se acabaron los minutos de voz de {mes}",
        "corpo": ("Hola, {nome}:\n\n{empresa} usó {minutos} de los {limite} minutos de entrevista por voz del plan "
                  "{plano} en {mes} ({pct}%).\n\n{situacao}\n\n{acao}\n{url}\n\nEl equipo de Bússola"),
        "situacao_80": "Al llegar al 100%, las nuevas llamadas de entrevista se pausan hasta el próximo mes.",
        "situacao_100_pausa": "Las nuevas llamadas de entrevista están en pausa hasta el próximo mes o hasta que cambies de plan.",
        "situacao_100_excedente": "Las llamadas continúan y los minutos extra se cobran como excedente.",
        "acao_upgrade": "Para tener más minutos, cámbiate al plan {proximo}:",
        "acao_mais": "Para tener más minutos, revisa las opciones de tu plan:",
        "teste": "prueba gratis",
    },
}


def _lang(v):
    v = (v or "").strip().lower()[:2]
    return v if v in IDIOMAS else "pt"


def _nome_mes(mes, lang):
    try:
        return "%s %s" % (MESES[lang][int(mes[5:7]) - 1], mes[:4]) if lang == "en" else \
            "%s de %s" % (MESES[lang][int(mes[5:7]) - 1], mes[:4])
    except (ValueError, IndexError):
        return mes


def email_alerta(conn, e, u, limiar, lang, nome):
    """(assunto, corpo) do alerta no idioma pedido."""
    planos = srv.planos
    lang = _lang(lang)
    tx = TEXTOS[lang]
    cat = planos.catalogo(conn)
    p = planos.plano(cat, e["plano"] or "")
    if planos.em_teste(e) or not p:
        nome_plano = tx["teste"] if planos.em_teste(e) else (e["plano"] or "")
    else:
        nome_plano = planos._texto(p["nome"], lang)
    prox = planos.proximo_plano(cat, e["plano"] or "")
    maior = bool(prox and (not p or prox["codigo"] != p["codigo"] or planos.em_teste(e)))
    codigo = prox["codigo"] if prox else (e["plano"] or "")
    url = "%s/assinar?plano=%s&e=%s" % (srv.url_publica(conn).rstrip("/"), urllib.parse.quote(codigo),
                                        urllib.parse.quote(e["slug"]))
    if limiar >= 100:
        situacao = tx["situacao_100_excedente"] if u.get("excedente_permitido") else tx["situacao_100_pausa"]
    else:
        situacao = tx["situacao_80"]
    acao = tx["acao_upgrade"].format(proximo=planos._texto(prox["nome"], lang)) if maior else tx["acao_mais"]
    mes = _nome_mes(u["mes"], lang)
    pct = int(round(u["pct"] or 0))
    assunto = tx["assunto_100" if limiar >= 100 else "assunto_80"].format(empresa=e["nome"], mes=mes)
    corpo = tx["corpo"].format(nome=nome or "", empresa=e["nome"], minutos=u["minutos"], limite=u["limite"],
                               plano=nome_plano, mes=mes, pct=pct, situacao=situacao, acao=acao, url=url)
    return assunto, corpo


def _enviar(lista):
    """lista de (para, assunto, corpo, idioma, empresa_id ou None)."""
    lista = [x for x in lista if x[0]]
    if not lista:
        return

    def trabalho(conn):
        for para, assunto, corpo, lang, empresa_id in lista:
            try:
                marca = srv.mensagens.marca(conn, empresa_id) if empresa_id else None
                srv.enviar_email(conn, para, assunto, corpo, marca=marca, idioma=lang)
            except Exception as exc:  # noqa: BLE001
                sys.stderr.write("Telefonia: e-mail de alerta falhou: %r\n" % exc)

    def rodar():
        conn = srv.db()
        try:
            trabalho(conn)
        finally:
            conn.close()

    if ENVIO_EM_SEGUNDO_PLANO:
        threading.Thread(target=rodar, daemon=True).start()
    else:
        rodar()


def verificar_alerta(conn, empresa, u=None):
    """Confere o uso do mês e manda o alerta de 80% ou 100% se ainda não foi enviado.
    Barato: sem limiar novo, só uma consulta. Nunca lança. Devolve a lista de e-mails."""
    try:
        planos = srv.planos
        e = planos._empresa(conn, empresa)
        if not e:
            return []
        u = u or planos.uso(conn, e)
        if not u or u.get("ilimitado") or not u.get("limite") or u["limite"] <= 0:
            return []
        pct = 100.0 * u["minutos"] / u["limite"]
        atingidos = [lim for lim in LIMIARES if pct >= lim]
        if not atingidos:
            return []
        ja = {r[0] for r in conn.execute(
            "SELECT limiar FROM alertas_uso WHERE empresa_id=? AND mes=?", (e["id"], u["mes"])).fetchall()}
        if all(lim in ja for lim in atingidos):
            return []
        novos = []
        for lim in atingidos:
            cur = conn.execute(
                "INSERT OR IGNORE INTO alertas_uso (empresa_id, mes, limiar, minutos, limite) VALUES (?,?,?,?,?)",
                (e["id"], u["mes"], lim, u["minutos"], u["limite"]))
            if cur.rowcount:
                novos.append(lim)
        conn.commit()
        maior = max(atingidos)
        if maior not in novos:
            return []
        emails = []
        for g in planos._admins(conn, e["id"]):
            lang = _lang(g["idioma"] if "idioma" in g.keys() else "pt")
            assunto, corpo = email_alerta(conn, e, u, maior, lang, g["nome"])
            emails.append((g["email"], assunto, corpo, lang, e["id"]))
        dono = srv.config_get(conn, "dono_email")
        if maior >= 100 and dono:
            lang_dono = _lang(srv.config_get(conn, "dono_idioma") or "pt")
            assunto, corpo = email_alerta(conn, e, u, maior, lang_dono, "")
            assunto = {"pt": "[Dono] ", "en": "[Owner] ", "es": "[Dueño] "}[lang_dono] + assunto
            emails.append((dono, assunto, corpo, lang_dono, None))
        conn.execute("UPDATE alertas_uso SET enviados=? WHERE empresa_id=? AND mes=? AND limiar=?",
                     (len(emails), e["id"], u["mes"], maior))
        conn.commit()
        _enviar(emails)
        return [(x[0], x[1]) for x in emails]
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("Telefonia: verificação de alerta falhou: %r\n" % exc)
        return []


def verificar_alertas(conn):
    """Todas as empresas com plano (rotina diária). Devolve quantos e-mails saíram."""
    total = 0
    for e in conn.execute("SELECT * FROM empresas WHERE status IN ('ativa', 'teste')").fetchall():
        total += len(verificar_alerta(conn, e))
    return total


# ------------------------------------------------------------ rotas do dono

def _resp(h, status, dados):
    h._json(status, dados)
    return True


def _twilio_dono(conn):
    sid = srv.config_get(conn, "twilio_account_sid") or ""
    token = srv.config_get(conn, "twilio_auth_token") or ""
    return {"configurado": bool(sid and token),
            "sid_mascarado": (sid[:4] + "..." + sid[-4:]) if len(sid) > 8 else "",
            "token_final": token[-4:] if token else ""}


def rotear_dono(h, method, path, conn):
    """Rotas /api/dono/telefonia* (o guarda do dono já rodou no server.py)."""
    if not path.startswith("/api/dono/telefonia"):
        return None
    ip = h._ip_cliente() if hasattr(h, "_ip_cliente") else ""
    try:
        if path == "/api/dono/telefonia/twilio":
            if method == "GET":
                return _resp(h, 200, _twilio_dono(conn))
            if method == "POST":
                d = h._body()
                if d.get("remover"):
                    srv.config_set(conn, "twilio_account_sid", "")
                    srv.config_set(conn, "twilio_auth_token", "")
                else:
                    sid = str(d.get("account_sid") or "").strip()
                    token = str(d.get("auth_token") or "").strip()
                    if sid:
                        if not SID_RE.match(sid):
                            raise ErroTelefonia("Account SID inválido (começa com AC e tem 34 caracteres)")
                        srv.config_set(conn, "twilio_account_sid", sid)
                    if token:
                        if not re.match(r"^[0-9a-zA-Z]{16,64}$", token):
                            raise ErroTelefonia("Auth Token inválido")
                        srv.config_set(conn, "twilio_auth_token", token)
                conn.commit()
                _auditar(conn, "telefonia credenciais twilio", "", None, ip)
                return _resp(h, 200, dict(_twilio_dono(conn), ok=True))
        if method == "GET" and path == "/api/dono/telefonia":
            custo, preco = custo_mensal(conn)
            return _resp(h, 200, {
                "twilio": _twilio_dono(conn),
                "elevenlabs_configurado": bool(srv.config_get(conn, "elevenlabs_api_key")
                                               and srv.config_get(conn, "elevenlabs_agent_id")),
                "custo_mensal": custo, "preco_numero_extra": preco, "numeros": numeros(conn),
            })
        if method == "GET" and path == "/api/dono/telefonia/disponiveis":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(h.path).query)
            custo, preco = custo_mensal(conn)
            return _resp(h, 200, {"numeros": buscar_disponiveis(conn, qs.get("ddd", [""])[0]),
                                  "custo_mensal": custo, "preco_numero_extra": preco})
        m = re.match(r"^/api/dono/telefonia/empresa/(\d+)(?:/(comprar|anexar))?$", path)
        if m:
            eid = int(m.group(1))
            if method == "GET" and not m.group(2):
                _empresa(conn, eid)
                custo, preco = custo_mensal(conn)
                return _resp(h, 200, {"numeros": numeros(conn, eid), "custo_mensal": custo,
                                      "preco_numero_extra": preco, "twilio": _twilio_dono(conn)["configurado"]})
            if method == "POST" and m.group(2) == "comprar":
                d = h._body()
                return _resp(h, 200, {"ok": True, "numero": comprar(conn, eid, d.get("numero"), d.get("confirmar"), ip)})
            if method == "POST" and m.group(2) == "anexar":
                return _resp(h, 200, {"ok": True, "numero": anexar(conn, eid, h._body().get("numero"), ip)})
        m = re.match(r"^/api/dono/telefonia/numero/(\d+)/(importar|liberar)$", path)
        if m and method == "POST":
            nid = int(m.group(1))
            if m.group(2) == "importar":
                return _resp(h, 200, {"ok": True, "numero": importar(conn, nid, ip)})
            d = h._body()
            return _resp(h, 200, {"ok": True, "numero": liberar(conn, nid, d.get("confirmar"),
                                                                bool(d.get("manter_twilio")), ip)})
        if method == "POST" and path == "/api/dono/telefonia/alertas":
            return _resp(h, 200, {"ok": True, "emails": verificar_alertas(conn)})
    except ErroTelefonia as exc:
        return _resp(h, exc.status, dict(exc.extra, erro=exc.mensagem))
    return _resp(h, 404, {"erro": "Rota não encontrada"})
