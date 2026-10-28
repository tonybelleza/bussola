"""Assistente de configuração (primeiro acesso) e página "Meu plano" do administrador.

Assistente: GET /api/gestor/assistente devolve os passos com "feito" calculado a partir dos
dados reais da empresa (logo, equipe, cargos com competências, voz com roteiro revisado,
agenda, entrada do Indeed ou CSV, primeira vaga, dados do empregador no onboarding e,
opcional, programa de indicação). O administrador pode dispensar o cartão (guardado por
empresa em config "assistente:<id>") e reabrir em Configurações.

Meu plano: GET /api/gestor/assistente/plano junta o plano atual (planos.info_gestor), o
catálogo para comparar e o uso de minutos de voz dos últimos 6 meses. Sem Stripe, a troca
de plano e o cancelamento viram um pedido (POST /api/gestor/assistente/pedido) que vai por
e-mail ao dono (config dono_email) e fica na tabela pedidos_plano.

Tudo aqui é só para o administrador da empresa e sempre filtrado pela empresa do gestor.
"""
import json
import sys
import threading
from datetime import datetime, timezone

srv = None  # módulo server, injetado por ligar()

ENVIO_EM_SEGUNDO_PLANO = True  # os testes desligam para conferir o e-mail na hora
PEDIDOS_POR_DIA = 5
MESES_HISTORICO = 6
TIPOS_PEDIDO = ("trocar_plano", "cancelar")
MOTIVOS_CANCELAMENTO = ("caro", "pouco_uso", "faltou_recurso", "outro_sistema", "temporario", "outro")
MOTIVOS_PT = {
    "caro": "Preço alto", "pouco_uso": "Pouco uso", "faltou_recurso": "Faltou um recurso",
    "outro_sistema": "Mudou para outro sistema", "temporario": "Pausa temporária", "outro": "Outro motivo",
}

# id do passo -> (aba do painel, âncora dentro da aba, opcional)
PASSOS = (
    ("logo", "config", "cfg-marca", False),
    ("equipe", "config", "cfg-gestores", False),
    ("cargos", "cargos", "", False),
    ("voz", "voz", "", False),
    ("agenda", "config", "cfg-agenda", False),
    ("entrada", "config", "cfg-entrada", False),
    ("vaga", "vagas", "", False),
    ("onboarding", "config", "cfg-onboarding", False),
    ("indicacoes", "config", "cfg-indicacoes", True),
)


def ligar(modulo_server):
    global srv
    srv = modulo_server


def init_assistente(c):
    c.execute(
        "CREATE TABLE IF NOT EXISTS pedidos_plano ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " gestor_id INTEGER,"
        " gestor_nome TEXT DEFAULT '',"
        " gestor_email TEXT DEFAULT '',"
        " tipo TEXT NOT NULL,"
        " plano_atual TEXT DEFAULT '',"
        " plano TEXT DEFAULT '',"
        " ciclo TEXT DEFAULT '',"
        " motivo TEXT DEFAULT '',"
        " mensagem TEXT DEFAULT '',"
        " email_enviado INTEGER DEFAULT 0,"
        " criado_em TEXT DEFAULT (datetime('now')))"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_plano_empresa ON pedidos_plano (empresa_id, criado_em)")


# ------------------------------------------------------------ utilidades

def _json_cfg(conn, chave):
    try:
        v = json.loads(srv.config_get(conn, chave) or "{}")
        return v if isinstance(v, dict) else {}
    except (ValueError, TypeError):
        return {}


def _chave(empresa_id):
    return "assistente:%d" % int(empresa_id)


def _lang(h, gestor):
    v = (h.headers.get("X-Idioma") if h is not None and getattr(h, "headers", None) else "") or ""
    if not v:
        try:
            v = gestor["idioma"] or ""
        except (IndexError, KeyError):
            v = ""
    v = str(v).lower()[:2]
    return v if v in ("pt", "en", "es") else "pt"


def _existe(conn, sql, params):
    return conn.execute(sql, params).fetchone() is not None


def _colunas(conn, tabela):
    return {r[1] for r in conn.execute("PRAGMA table_info(%s)" % tabela).fetchall()}


def _revisado(roteiro_json):
    try:
        return bool((json.loads(roteiro_json or "{}") or {}).get("revisado_em"))
    except (ValueError, TypeError, AttributeError):
        return False


def _cfg_modulo(conn, nome_modulo, empresa_id):
    """config(conn, empresa_id) de agenda, entrada, onboarding ou indicacoes, sem quebrar
    se o módulo não estiver carregado."""
    mod = getattr(srv, nome_modulo, None)
    if mod is None or not hasattr(mod, "config"):
        return _json_cfg(conn, "%s:%d" % (nome_modulo, int(empresa_id)))
    try:
        return mod.config(conn, empresa_id) or {}
    except Exception:  # noqa: BLE001
        return {}


# ------------------------------------------------------------ assistente

def voz_disponivel(conn, empresa_row):
    """O passo de voz só aparece quando o plano da empresa tem minutos de voz (ou o módulo
    de voz foi liberado pelo dono, ou a empresa não tem plano do catálogo)."""
    try:
        mods = json.loads(empresa_row["modulos"] or "[]")
    except (ValueError, TypeError, IndexError, KeyError):
        mods = []
    if isinstance(mods, list) and "voz" in mods:
        return True
    planos = getattr(srv, "planos", None)
    if planos is None:
        return True
    try:
        limite = planos.limite_minutos(planos.catalogo(conn), empresa_row)
    except Exception:  # noqa: BLE001
        return True
    return limite is None or limite > 0


def feitos(conn, empresa_id):
    """{id_do_passo: bool} calculado a partir dos dados da empresa."""
    eid = int(empresa_id)
    r = {}
    # logo da empresa (mensagens.marca confere se o arquivo existe)
    try:
        r["logo"] = bool(srv.mensagens.marca(conn, eid).get("logo_url"))
    except Exception:  # noqa: BLE001
        e = conn.execute("SELECT logo FROM empresas WHERE id=?", (eid,)).fetchone()
        r["logo"] = bool(e and e["logo"])
    # equipe: mais de um gestor aprovado
    n = conn.execute("SELECT COUNT(*) FROM gestores WHERE empresa_id=? AND aprovado=1 AND COALESCE(suporte,0)=0",
                     (eid,)).fetchone()[0]
    r["equipe"] = int(n or 0) > 1
    # pelo menos um cargo com competências
    r["cargos"] = _existe(conn, "SELECT 1 FROM cargos g JOIN competencias c ON c.cargo_id=g.id"
                                " WHERE g.empresa_id=? LIMIT 1", (eid,))
    # voz: cargo com voz ligada e roteiro revisado
    r["voz"] = False
    if {"voz_ativa", "roteiro_voz"} <= _colunas(conn, "cargos"):
        for g in conn.execute("SELECT roteiro_voz FROM cargos WHERE empresa_id=? AND voz_ativa=1", (eid,)).fetchall():
            if _revisado(g["roteiro_voz"]):
                r["voz"] = True
                break
    # agenda de entrevistas ligada
    r["agenda"] = bool(_cfg_modulo(conn, "agenda", eid).get("ativo"))
    # entrada do Indeed ligada ou candidatos já importados por CSV ou pelo Indeed
    r["entrada"] = bool(_cfg_modulo(conn, "entrada", eid).get("ativo"))
    if not r["entrada"] and "tags" in _colunas(conn, "candidatos"):
        r["entrada"] = _existe(conn, "SELECT 1 FROM candidatos WHERE empresa_id=? AND"
                                     " (tags LIKE '%\"csv\"%' OR tags LIKE '%\"indeed\"%') LIMIT 1", (eid,))
    # primeira vaga
    r["vaga"] = _existe(conn, "SELECT 1 FROM vagas WHERE empresa_id=? LIMIT 1", (eid,))
    # dados do empregador no onboarding (razão social e EIN)
    cfg_onb = _cfg_modulo(conn, "onboarding", eid)
    r["onboarding"] = bool(str(cfg_onb.get("empregador_nome") or "").strip()
                           and str(cfg_onb.get("empregador_ein") or "").strip())
    # programa de indicação (opcional)
    r["indicacoes"] = bool(_cfg_modulo(conn, "indicacoes", eid).get("ativo"))
    return r


def estado(conn, empresa_id):
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (int(empresa_id),)).fetchone()
    if not e:
        return None
    feito = feitos(conn, empresa_id)
    com_voz = voz_disponivel(conn, e)
    passos = []
    for pid, aba, ancora, opcional in PASSOS:
        if pid == "voz" and not com_voz:
            continue
        passos.append({"id": pid, "feito": bool(feito.get(pid)), "opcional": opcional, "aba": aba, "ancora": ancora})
    obrigatorios = [p for p in passos if not p["opcional"]]
    feitos_n = sum(1 for p in obrigatorios if p["feito"])
    total = len(obrigatorios)
    cfg = _json_cfg(conn, _chave(empresa_id))
    dispensado = bool(cfg.get("dispensado"))
    completo = feitos_n >= total
    return {
        "passos": passos, "feitos": feitos_n, "total": total,
        "pct": int(round(100.0 * feitos_n / total)) if total else 100,
        "completo": completo, "dispensado": dispensado,
        "dispensado_em": cfg.get("dispensado_em", "") if dispensado else "",
        "mostrar": not dispensado and not completo,
    }


def dispensar(conn, empresa_id, gestor, dispensado=True):
    cfg = _json_cfg(conn, _chave(empresa_id))
    cfg["dispensado"] = bool(dispensado)
    cfg["dispensado_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if dispensado else ""
    cfg["dispensado_por"] = (gestor["nome"] if dispensado else "") or ""
    srv.config_set(conn, _chave(empresa_id), json.dumps(cfg, ensure_ascii=False))
    conn.commit()


# ------------------------------------------------------------ meu plano

def _mes_anterior(mes):
    ano, m = int(mes[:4]), int(mes[5:7])
    if m == 1:
        return "%04d-12" % (ano - 1)
    return "%04d-%02d" % (ano, m - 1)


def historico_uso(conn, empresa_id, meses=MESES_HISTORICO, agora=None):
    """Minutos de voz por mês (mais antigo primeiro), pelo mesmo medidor do planos.py."""
    planos = srv.planos
    mes = planos.mes_de(agora)
    lista = []
    for _ in range(meses):
        lista.append({"mes": mes, "minutos": planos.minutos_usados(conn, int(empresa_id), mes)})
        mes = _mes_anterior(mes)
    return list(reversed(lista))


def status_conta(e, em_teste):
    st = e["status"] or ""
    pag = ""
    try:
        pag = e["pagamento_status"] or ""
    except (IndexError, KeyError):
        pass
    if st == "suspensa":
        return "suspensa"
    if pag == "falhou":
        return "pagamento_falhou"
    if pag == "cancelada":
        return "cancelada"
    if em_teste or st == "teste":
        return "teste"
    return "ativa"


def _plano_lista(p, lang, atual):
    planos = srv.planos
    return {
        "codigo": p.get("codigo"), "nome": planos._texto(p.get("nome"), lang),
        "descricao": planos._texto(p.get("descricao"), lang),
        "preco_mensal": p.get("preco_mensal"), "preco_anual": p.get("preco_anual"),
        "minutos_voz": p.get("minutos_voz") or 0, "gestores_max": p.get("gestores_max"),
        "vagas_ativas_max": p.get("vagas_ativas_max"), "sms_mes": p.get("sms_mes") or 0,
        "numero_exclusivo": bool(p.get("numero_exclusivo")), "destaque": bool(p.get("destaque")),
        "recursos": (p.get("recursos") or {}).get(lang) or (p.get("recursos") or {}).get("pt") or [],
        "atual": p.get("codigo") == atual,
    }


def pedidos_recentes(conn, empresa_id, limite=5):
    linhas = conn.execute(
        "SELECT id, tipo, plano, ciclo, motivo, gestor_nome, criado_em FROM pedidos_plano"
        " WHERE empresa_id=? ORDER BY id DESC LIMIT ?", (int(empresa_id), int(limite))).fetchall()
    return [dict(r) for r in linhas]


def meu_plano(conn, gestor, lang, h=None):
    planos = srv.planos
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (gestor["empresa_id"],)).fetchone()
    info = planos.info_gestor(conn, gestor, lang, h)
    cat = planos.catalogo(conn)
    atual = e["plano"] or ""
    lista = [_plano_lista(p, lang, atual) for p in cat["planos"] if p.get("ativo", True) or p.get("codigo") == atual]
    return {
        "info": info,
        "status_conta": status_conta(e, info.get("em_teste")),
        "plano_codigo": atual,
        "planos": lista,
        "historico": historico_uso(conn, e["id"]),
        "limite_minutos": (info.get("uso") or {}).get("limite"),
        "stripe_ativo": bool(info.get("stripe_ativo")),
        "portal_disponivel": bool(info.get("portal_disponivel")),
        "pedidos": pedidos_recentes(conn, e["id"]),
        "motivos": list(MOTIVOS_CANCELAMENTO),
        "addons": cat.get("addons", {}),
    }


MOTIVOS_DONO = {
    "pt": MOTIVOS_PT,
    "en": {"caro": "Price too high", "pouco_uso": "Low usage", "faltou_recurso": "Missing a feature",
           "outro_sistema": "Switched to another system", "temporario": "Temporary pause", "outro": "Other reason"},
    "es": {"caro": "Precio alto", "pouco_uso": "Poco uso", "faltou_recurso": "Faltó una función",
           "outro_sistema": "Se cambió a otro sistema", "temporario": "Pausa temporal", "outro": "Otro motivo"},
}

TEXTOS_DONO = {
    "pt": {"troca": "troca de plano", "cancelamento": "cancelamento", "novo": "Novo pedido de %s.",
           "empresa": "Empresa: %s (%s, id %d)", "atual": "Plano atual: %s", "sem_plano": "sem plano do catálogo",
           "pedido": "Plano pedido: %s (%s)", "anual": "anual", "mensal": "mensal",
           "motivo": "Motivo: %s", "nao_informado": "não informado", "por": "Pedido por: %s <%s>",
           "sem_email": "sem e-mail", "mensagem": "Mensagem:", "sem_mensagem": "(sem mensagem)",
           "fim": "Responda ao administrador e ajuste o plano no painel do dono.",
           "assunto": "Bússola: pedido de %s (%s)"},
    "en": {"troca": "plan change", "cancelamento": "cancellation", "novo": "New %s request.",
           "empresa": "Company: %s (%s, id %d)", "atual": "Current plan: %s", "sem_plano": "no catalog plan",
           "pedido": "Requested plan: %s (%s)", "anual": "yearly", "mensal": "monthly",
           "motivo": "Reason: %s", "nao_informado": "not given", "por": "Requested by: %s <%s>",
           "sem_email": "no email", "mensagem": "Message:", "sem_mensagem": "(no message)",
           "fim": "Reply to the admin and adjust the plan in the owner panel.",
           "assunto": "Bússola: %s request (%s)"},
    "es": {"troca": "cambio de plan", "cancelamento": "cancelación", "novo": "Nueva solicitud de %s.",
           "empresa": "Empresa: %s (%s, id %d)", "atual": "Plan actual: %s", "sem_plano": "sin plan del catálogo",
           "pedido": "Plan solicitado: %s (%s)", "anual": "anual", "mensal": "mensual",
           "motivo": "Motivo: %s", "nao_informado": "no indicado", "por": "Solicitado por: %s <%s>",
           "sem_email": "sin correo", "mensagem": "Mensaje:", "sem_mensagem": "(sin mensaje)",
           "fim": "Responde al administrador y ajusta el plan en el panel del dueño.",
           "assunto": "Bússola: solicitud de %s (%s)"},
}


def _email_dono(conn, pedido, empresa, plano_atual_nome, plano_nome, lang="pt"):
    """E-mail ao dono no idioma escolhido no painel do dono (config dono_idioma; padrão pt)."""
    lang = lang if lang in TEXTOS_DONO else "pt"
    t = TEXTOS_DONO[lang]
    tipo_txt = t["troca"] if pedido["tipo"] == "trocar_plano" else t["cancelamento"]
    linhas = [
        t["novo"] % tipo_txt,
        "",
        t["empresa"] % (empresa["nome"], empresa["slug"], empresa["id"]),
        t["atual"] % (plano_atual_nome or t["sem_plano"]),
    ]
    if pedido["tipo"] == "trocar_plano":
        linhas.append(t["pedido"] % (plano_nome or pedido["plano"],
                                     t["anual"] if pedido["ciclo"] == "anual" else t["mensal"]))
    else:
        linhas.append(t["motivo"] % MOTIVOS_DONO[lang].get(pedido["motivo"], pedido["motivo"] or t["nao_informado"]))
    linhas += [
        t["por"] % (pedido["gestor_nome"], pedido["gestor_email"] or t["sem_email"]),
        "",
        t["mensagem"],
        pedido["mensagem"] or t["sem_mensagem"],
        "",
        t["fim"],
    ]
    assunto = t["assunto"] % (tipo_txt, empresa["nome"])
    return assunto, "\n".join(linhas)


def _enviar(pedido_id, para, assunto, corpo, idioma="pt"):
    def trabalho(conn):
        try:
            res = srv.enviar_email(conn, para, assunto, corpo, idioma=idioma)
            ok = bool(res[0]) if isinstance(res, (tuple, list)) and res else bool(res)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Assistente: e-mail ao dono falhou: %r\n" % exc)
            ok = False
        if ok:
            conn.execute("UPDATE pedidos_plano SET email_enviado=1 WHERE id=?", (pedido_id,))
            conn.commit()

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


def criar_pedido(conn, gestor, d):
    """Valida e grava o pedido; avisa o dono por e-mail. Devolve (status, resposta)."""
    planos = srv.planos
    tipo = str(d.get("tipo") or "").strip()
    if tipo not in TIPOS_PEDIDO:
        return 400, {"erro": "Tipo de pedido inválido"}
    e = conn.execute("SELECT * FROM empresas WHERE id=?", (gestor["empresa_id"],)).fetchone()
    cat = planos.catalogo(conn)
    plano_cod, ciclo, motivo, plano_nome = "", "", "", ""
    if tipo == "trocar_plano":
        p = planos.plano(cat, str(d.get("plano") or ""))
        if not p or not p.get("ativo", True):
            return 400, {"erro": "Plano inválido"}
        try:
            ciclo_atual = e["ciclo"] or "mensal"
        except (IndexError, KeyError):
            ciclo_atual = "mensal"
        ciclo = str(d.get("ciclo") or ciclo_atual)
        if ciclo not in planos.CICLOS:
            return 400, {"erro": "Ciclo de cobrança inválido"}
        plano_cod = p["codigo"]
        plano_nome = planos._texto(p.get("nome"), "pt")
    else:
        motivo = str(d.get("motivo") or "").strip()
        if motivo not in MOTIVOS_CANCELAMENTO:
            motivo = "outro"
    hoje = conn.execute(
        "SELECT COUNT(*) FROM pedidos_plano WHERE empresa_id=? AND criado_em >= datetime('now', '-1 day')",
        (e["id"],)).fetchone()[0]
    if int(hoje or 0) >= PEDIDOS_POR_DIA:
        return 429, {"erro": "Muitos pedidos hoje. Tente de novo amanhã."}
    mensagem = str(d.get("mensagem") or "").strip()[:1000]
    atual = planos.plano(cat, e["plano"] or "")
    pedido = {
        "tipo": tipo, "plano": plano_cod, "ciclo": ciclo, "motivo": motivo, "mensagem": mensagem,
        "gestor_nome": gestor["nome"] or "", "gestor_email": (gestor["email"] or "") if "email" in gestor.keys() else "",
    }
    cur = conn.execute(
        "INSERT INTO pedidos_plano (empresa_id, gestor_id, gestor_nome, gestor_email, tipo, plano_atual, plano, ciclo,"
        " motivo, mensagem) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (e["id"], gestor["id"], pedido["gestor_nome"], pedido["gestor_email"], tipo, e["plano"] or "",
         plano_cod, ciclo, motivo, mensagem))
    conn.commit()
    pid = cur.lastrowid
    dono = (srv.config_get(conn, "dono_email") or "").strip()
    if dono:
        lang_dono = planos.idioma_dono(conn)
        p_novo = planos.plano(cat, plano_cod) if plano_cod else None
        assunto, corpo = _email_dono(conn, pedido, e, planos._texto(atual.get("nome"), lang_dono) if atual else "",
                                     planos._texto(p_novo.get("nome"), lang_dono) if p_novo else plano_nome,
                                     lang_dono)
        _enviar(pid, dono, assunto, corpo, lang_dono)
    return 200, {"ok": True, "id": pid, "dono_avisado": bool(dono)}


# ------------------------------------------------------------ rotas

def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/assistente"):
        return None
    if not gestor["is_admin"]:
        return _resp(h, 403, {"erro": "Apenas o administrador da empresa acessa esta área"})
    empresa_id = gestor["empresa_id"]

    if method == "GET" and path == "/api/gestor/assistente":
        return _resp(h, 200, estado(conn, empresa_id) or {})

    if method == "POST" and path == "/api/gestor/assistente/dispensar":
        d = h._body()
        dispensar(conn, empresa_id, gestor, bool(d.get("dispensado", True)))
        return _resp(h, 200, dict(estado(conn, empresa_id) or {}, ok=True))

    if method == "GET" and path == "/api/gestor/assistente/plano":
        return _resp(h, 200, meu_plano(conn, gestor, _lang(h, gestor), h))

    if method == "POST" and path == "/api/gestor/assistente/pedido":
        status, dados = criar_pedido(conn, gestor, h._body())
        return _resp(h, status, dados)

    return _resp(h, 404, {"erro": "Rota não encontrada"})


def _resp(h, status, dados):
    h._json(status, dados)
    return True
