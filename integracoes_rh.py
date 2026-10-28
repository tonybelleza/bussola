"""Integrações de RH: exportação para a folha de pagamento e verificação de
antecedentes pela Checkr.

A. Exportação para a folha (Gusto, QuickBooks Payroll ou CSV genérico)
- Usa os onboardings em andamento ou concluídos (onboarding.py): dados pessoais,
  proposta (cargo, início, pagamento), formulários W-4/W-9 e forma de pagamento.
- Dois arquivos: empregados (W-2) e prestadores (1099, com os dados do W-9 para
  o 1099-NEC: nome, empresa, classificação fiscal, tipo de TIN, TIN e endereço).
- Os nomes das colunas seguem o modelo de importação de cada sistema e podem ser
  trocados por empresa (mapa de colunas; coluna em branco = não exportar).
- SSN, data de nascimento, TIN, routing e conta só entram depois que o
  administrador digita a própria senha de novo. O arquivo é montado na memória,
  enviado uma única vez e nunca gravado. A trilha de auditoria registra quem
  exportou, quantos registros e se havia dados sensíveis (nunca os valores).

B. Checkr (verificação de antecedentes)
- Configuração por empresa (administrador): chave da API (cifrada com a mesma
  chave Fernet do onboarding, mostrada só mascarada), pacote padrão, local de
  trabalho (estado/cidade), ambiente (produção ou staging) e "exigir verificação
  antes de contratar".
- Na ficha do candidato (depois da proposta): cria o candidato na Checkr
  (POST /v1/candidates) e o convite (POST /v1/invitations com package e
  work_locations). A Checkr manda o e-mail ao candidato, cuida da autorização e
  da divulgação da FCRA no fluxo hospedado dela.
- Webhook público POST /api/integracoes/checkr/webhook: confere o
  X-Checkr-Signature (HMAC SHA-256 do corpo com a chave da API), atualiza o
  status, grava na linha do tempo e avisa os administradores (no idioma de cada
  um) quando o relatório fica pronto.
- E-Verify não é integrado (exige cadastro do empregador): o painel só mostra um
  aviso com o link para e-verify.gov.

Tudo isolado por empresa. Nenhuma chamada real nos testes (urllib é simulado).
"""
import base64
import csv
import hashlib
import hmac
import io
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from urllib.parse import parse_qs, urlparse

import onboarding

srv = None  # módulo server, injetado por ligar()

ENVIO_EM_SEGUNDO_PLANO = True
TIMEOUT = 20

CHECKR_API = {"producao": "https://api.checkr.com/v1", "staging": "https://api.checkr-staging.com/v1"}
CHECKR_PAINEL = {"producao": "https://dashboard.checkr.com", "staging": "https://dashboard.checkr-staging.com"}
FCRA_URL = "https://www.ftc.gov/business-guidance/resources/using-consumer-reports-what-employers-need-know"
EVERIFY_URL = "https://www.e-verify.gov/"

STATUS_CHECKR = ("convite_enviado", "pendente", "clear", "consider", "suspenso", "cancelado", "expirado")
STATUS_ABERTOS = ("convite_enviado", "pendente", "suspenso")
ROTULO_EVENTO = {
    "convite_enviado": "convite enviado",
    "pendente": "em andamento",
    "clear": "clear (sem apontamentos)",
    "consider": "consider (revisar)",
    "suspenso": "suspensa",
    "cancelado": "cancelada",
    "expirado": "convite expirado",
}

PROVEDORES = ("gusto", "quickbooks", "generico")
STATUS_EXPORTAVEIS = ("em_andamento", "concluido")

# (chave interna, sensível, vale para: w2 | 1099 | ambos)
CAMPOS = (
    ("tipo_membro", False, "ambos"),
    ("primeiro_nome", False, "ambos"),
    ("inicial", False, "ambos"),
    ("sobrenome", False, "ambos"),
    ("nome_preferido", False, "w2"),
    ("nome_w9", False, "1099"),
    ("nome_empresa", False, "1099"),
    ("classificacao", False, "1099"),
    ("email", False, "ambos"),
    ("telefone", False, "ambos"),
    ("data_inicio", False, "ambos"),
    ("estado_trabalho", False, "ambos"),
    ("cargo", False, "ambos"),
    ("tipo_emprego", False, "w2"),
    ("valor", False, "ambos"),
    ("unidade", False, "ambos"),
    ("ssn", True, "w2"),
    ("nascimento", True, "w2"),
    ("tipo_tin", False, "1099"),
    ("tin", True, "1099"),
    ("endereco", False, "ambos"),
    ("apto", False, "ambos"),
    ("cidade", False, "ambos"),
    ("estado", False, "ambos"),
    ("cep", False, "ambos"),
    ("metodo", False, "ambos"),
    ("banco", False, "ambos"),
    ("tipo_conta", False, "ambos"),
    ("routing", True, "ambos"),
    ("conta", True, "ambos"),
)
SENSIVEIS = tuple(k for k, s, _ in CAMPOS if s)

# nomes das colunas no modelo de importação de cada sistema (podem ser trocados por empresa)
COLUNAS_PADRAO = {
    "gusto": {
        "tipo_membro": "Member type", "primeiro_nome": "Legal first name", "inicial": "Middle initial",
        "sobrenome": "Last name", "nome_preferido": "Preferred first name", "nome_w9": "Legal name (W-9)",
        "nome_empresa": "Business name", "classificacao": "Federal tax classification", "email": "Personal email",
        "telefone": "Phone number", "data_inicio": "Start date", "estado_trabalho": "Work state",
        "cargo": "Job title", "tipo_emprego": "Employee type", "valor": "Compensation amount",
        "unidade": "Compensation unit", "ssn": "SSN", "nascimento": "Date of birth", "tipo_tin": "TIN type",
        "tin": "TIN", "endereco": "Home address street 1", "apto": "Home address street 2",
        "cidade": "Home address city", "estado": "Home address state", "cep": "Home address ZIP",
        "metodo": "Payment method", "banco": "Bank name", "tipo_conta": "Bank account type",
        "routing": "Routing number", "conta": "Account number",
    },
    "quickbooks": {
        "tipo_membro": "Worker type", "primeiro_nome": "First name", "inicial": "Middle initial",
        "sobrenome": "Last name", "nome_preferido": "Display name", "nome_w9": "Legal name (W-9)",
        "nome_empresa": "Company name", "classificacao": "Tax classification", "email": "Email",
        "telefone": "Phone", "data_inicio": "Hire date", "estado_trabalho": "Work location state",
        "cargo": "Job title", "tipo_emprego": "Pay type", "valor": "Pay rate", "unidade": "Pay rate unit",
        "ssn": "SSN", "nascimento": "Birth date", "tipo_tin": "Tax ID type", "tin": "Tax ID",
        "endereco": "Address line 1", "apto": "Address line 2", "cidade": "City", "estado": "State",
        "cep": "ZIP code", "metodo": "Pay method", "banco": "Bank name", "tipo_conta": "Account type",
        "routing": "Routing number", "conta": "Account number",
    },
    "generico": {
        "tipo_membro": "worker_type", "primeiro_nome": "first_name", "inicial": "middle_initial",
        "sobrenome": "last_name", "nome_preferido": "preferred_name", "nome_w9": "w9_legal_name",
        "nome_empresa": "business_name", "classificacao": "tax_classification", "email": "email",
        "telefone": "phone", "data_inicio": "start_date", "estado_trabalho": "work_state", "cargo": "job_title",
        "tipo_emprego": "pay_type", "valor": "pay_rate", "unidade": "pay_unit", "ssn": "ssn",
        "nascimento": "date_of_birth", "tipo_tin": "tin_type", "tin": "tin", "endereco": "address_line1",
        "apto": "address_line2", "cidade": "city", "estado": "state", "cep": "zip", "metodo": "payment_method",
        "banco": "bank_name", "tipo_conta": "account_type", "routing": "routing_number",
        "conta": "account_number",
    },
}

VALORES = {
    "gusto": {
        "membro": {"w2": "Employee", "1099_individual": "Contractor (individual)",
                   "1099_empresa": "Contractor (business)"},
        "unidade": {"hora": "Hour", "dia": "Day", "servico": "Job", "salario": "Year"},
        "emprego": {"hora": "Hourly", "dia": "Hourly", "servico": "Hourly", "salario": "Salary"},
        "conta": {"corrente": "Checking", "poupanca": "Savings"},
        "metodo": {"deposito": "Direct deposit", "zelle": "Zelle", "cheque": "Check", "provedor": "Direct deposit"},
    },
    "quickbooks": {
        "membro": {"w2": "Employee", "1099_individual": "Contractor", "1099_empresa": "Contractor"},
        "unidade": {"hora": "Per hour", "dia": "Per day", "servico": "Per job", "salario": "Per year"},
        "emprego": {"hora": "Hourly", "dia": "Hourly", "servico": "Hourly", "salario": "Salary"},
        "conta": {"corrente": "Checking", "poupanca": "Savings"},
        "metodo": {"deposito": "Direct deposit", "zelle": "Zelle", "cheque": "Paper check", "provedor": "Direct deposit"},
    },
    "generico": {
        "membro": {"w2": "employee", "1099_individual": "contractor_individual",
                   "1099_empresa": "contractor_business"},
        "unidade": {"hora": "hour", "dia": "day", "servico": "job", "salario": "year"},
        "emprego": {"hora": "hourly", "dia": "hourly", "servico": "hourly", "salario": "salary"},
        "conta": {"corrente": "checking", "poupanca": "savings"},
        "metodo": {"deposito": "direct_deposit", "zelle": "zelle", "cheque": "check", "provedor": "payroll_provider"},
    },
}

CLASSIFICACAO_W9 = {"individual": "Individual/sole proprietor", "c_corp": "C corporation", "s_corp": "S corporation",
                    "partnership": "Partnership", "trust": "Trust/estate", "llc": "LLC", "outro": "Other"}

# tentativas de senha erradas na exportação: no máximo 5 em 10 minutos por gestor
_JANELA_SENHA = 600
_LIMITE_SENHA = 5
_falhas_senha = {}
_trava = threading.Lock()


class ErroIntegracao(Exception):
    def __init__(self, status, mensagem):
        Exception.__init__(self, mensagem)
        self.status = status
        self.mensagem = mensagem


def ligar(modulo_server):
    global srv
    srv = modulo_server


# ------------------------------------------------------------- banco

def init_integracoes_rh(c):
    c.execute(
        "CREATE TABLE IF NOT EXISTS checkr_verificacoes ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,"
        " checkr_candidato_id TEXT DEFAULT '',"
        " convite_id TEXT DEFAULT '',"
        " convite_url TEXT DEFAULT '',"
        " relatorio_id TEXT DEFAULT '',"
        " pacote TEXT DEFAULT '',"
        " ambiente TEXT DEFAULT 'producao',"
        " status TEXT NOT NULL DEFAULT 'convite_enviado',"
        " resultado TEXT DEFAULT '',"
        " criado_por TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " atualizado_em TEXT DEFAULT (datetime('now')),"
        " concluido_em TEXT DEFAULT '')"
    )
    c.execute("CREATE INDEX IF NOT EXISTS ix_checkr_candidato ON checkr_verificacoes(empresa_id, candidato_id)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_checkr_ids ON checkr_verificacoes(checkr_candidato_id)")
    c.execute("CREATE TABLE IF NOT EXISTS checkr_eventos (evento_id TEXT PRIMARY KEY,"
              " criado_em TEXT DEFAULT (datetime('now')))")


# ------------------------------------------------------------- utilidades

def _json(texto, padrao=None):
    try:
        v = json.loads(texto) if texto else None
    except ValueError:
        v = None
    return padrao if v is None else v


def _digitos(v):
    return re.sub(r"\D", "", str(v or ""))


def _limpo(v, n=200):
    return re.sub(r"[\r\n\t]+", " ", str(v or "")).strip()[:n]


def _data(texto):
    try:
        return date.fromisoformat(str(texto or "")[:10])
    except ValueError:
        return None


def _idioma(v):
    v = str(v or "").strip().lower()[:2]
    return v if v in ("pt", "en", "es") else "pt"


def _resp(h, status, dados):
    h._json(status, dados)
    return True


# ------------------------------------------------------------- configuração

def _chave_cfg(empresa_id):
    return "integracoes_rh:%d" % int(empresa_id)


def config(conn, empresa_id):
    salvo = _json(srv.config_get(conn, _chave_cfg(empresa_id)), {})
    if not isinstance(salvo, dict):
        salvo = {}
    ck = salvo.get("checkr") if isinstance(salvo.get("checkr"), dict) else {}
    fo = salvo.get("folha") if isinstance(salvo.get("folha"), dict) else {}
    return {
        "checkr": {
            "chave_cifrada": ck.get("chave_cifrada") or "",
            "chave_final": ck.get("chave_final") or "",
            "pacote": ck.get("pacote") or "",
            "estado": ck.get("estado") or "",
            "cidade": ck.get("cidade") or "",
            "exigir": bool(ck.get("exigir")),
            "ambiente": ck.get("ambiente") if ck.get("ambiente") in CHECKR_API else "producao",
        },
        "folha": {
            "provedor": fo.get("provedor") if fo.get("provedor") in PROVEDORES else "gusto",
            "estado_trabalho": fo.get("estado_trabalho") or "",
            "mapas": fo.get("mapas") if isinstance(fo.get("mapas"), dict) else {},
        },
    }


def _gravar_config(conn, empresa_id, cfg):
    srv.config_set(conn, _chave_cfg(empresa_id), json.dumps(cfg, ensure_ascii=False))
    conn.commit()


def chave_checkr(conn, empresa_id, cfg=None):
    cfg = cfg or config(conn, empresa_id)
    cifrada = cfg["checkr"]["chave_cifrada"]
    if not cifrada:
        return ""
    return str(onboarding.decifrar_dict(conn, cifrada).get("k") or "")


def config_publica(conn, empresa_id):
    cfg = config(conn, empresa_id)
    ck = cfg["checkr"]
    return {
        "checkr": {
            "configurado": bool(ck["chave_cifrada"]),
            "chave_mascara": ("•••" + ck["chave_final"]) if ck["chave_cifrada"] else "",
            "pacote": ck["pacote"], "estado": ck["estado"], "cidade": ck["cidade"], "exigir": ck["exigir"],
            "ambiente": ck["ambiente"],
            "webhook_url": srv.url_publica(conn) + "/api/integracoes/checkr/webhook",
        },
        "folha": {
            "provedor": cfg["folha"]["provedor"],
            "estado_trabalho": cfg["folha"]["estado_trabalho"],
            "estado_sugerido": estado_trabalho(conn, empresa_id, cfg),
            "mapas": {p: colunas(cfg, p) for p in PROVEDORES},
            "padroes": COLUNAS_PADRAO,
            "campos": [{"chave": k, "sensivel": s, "aplica": a} for k, s, a in CAMPOS],
        },
    }


def salvar_config(conn, empresa_id, d):
    cfg = config(conn, empresa_id)
    ck = cfg["checkr"]
    if isinstance(d.get("checkr"), dict):
        n = d["checkr"]
        if n.get("remover_chave"):
            ck["chave_cifrada"], ck["chave_final"] = "", ""
        chave = str(n.get("chave") or "").strip()
        if chave and "•" not in chave:
            if not re.match(r"^[A-Za-z0-9_\-]{16,128}$", chave):
                raise ErroIntegracao(400, "Chave da API da Checkr inválida")
            ck["chave_cifrada"] = onboarding.cifrar_dict(conn, {"k": chave})
            ck["chave_final"] = chave[-4:]
        if "pacote" in n:
            pacote = str(n.get("pacote") or "").strip()
            if pacote and not re.match(r"^[A-Za-z0-9_\-]{1,80}$", pacote):
                raise ErroIntegracao(400, "Pacote da Checkr inválido")
            ck["pacote"] = pacote
        if "estado" in n:
            uf = str(n.get("estado") or "").strip().upper()
            if uf and not re.match(r"^[A-Z]{2}$", uf):
                raise ErroIntegracao(400, "Estado inválido: use a sigla de 2 letras")
            ck["estado"] = uf
        if "cidade" in n:
            ck["cidade"] = _limpo(n.get("cidade"), 80)
        if "exigir" in n:
            ck["exigir"] = bool(n.get("exigir"))
        if n.get("ambiente") in CHECKR_API:
            ck["ambiente"] = n["ambiente"]
    fo = cfg["folha"]
    if isinstance(d.get("folha"), dict):
        n = d["folha"]
        if n.get("provedor") in PROVEDORES:
            fo["provedor"] = n["provedor"]
        if "estado_trabalho" in n:
            uf = str(n.get("estado_trabalho") or "").strip().upper()
            if uf and not re.match(r"^[A-Z]{2}$", uf):
                raise ErroIntegracao(400, "Estado inválido: use a sigla de 2 letras")
            fo["estado_trabalho"] = uf
        if isinstance(n.get("mapas"), dict):
            chaves = {k for k, _, _ in CAMPOS}
            mapas = {}
            for prov, mapa in n["mapas"].items():
                if prov not in PROVEDORES or not isinstance(mapa, dict):
                    continue
                limpo = {}
                for k, v in mapa.items():
                    if k in chaves:
                        limpo[k] = _limpo(v, 60).replace('"', "")
                mapas[prov] = {k: v for k, v in limpo.items() if v != COLUNAS_PADRAO[prov][k]}
            fo["mapas"] = mapas
    _gravar_config(conn, empresa_id, cfg)
    return cfg


def colunas(cfg, provedor):
    """{chave: nome da coluna} do provedor, com as trocas da empresa ("" = não exportar)."""
    base = dict(COLUNAS_PADRAO[provedor])
    troca = (cfg["folha"]["mapas"] or {}).get(provedor) or {}
    for k, v in troca.items():
        if k in base:
            base[k] = v
    return base


def estado_trabalho(conn, empresa_id, cfg=None):
    cfg = cfg or config(conn, empresa_id)
    if cfg["folha"]["estado_trabalho"]:
        return cfg["folha"]["estado_trabalho"]
    try:
        ocfg = onboarding.config(conn, empresa_id)
        m = re.search(r"\b([A-Z]{2})\s+\d{5}", ocfg.get("empregador_cidade_estado_cep") or "")
        if m:
            return m.group(1)
    except Exception:  # noqa: BLE001
        pass
    return cfg["checkr"]["estado"] or ""


# ------------------------------------------------------------- A. exportação para a folha

def _hires(conn, gestor, ids=None, de=None, ate=None, tipo=None):
    """Onboardings exportáveis da empresa do gestor (com filtros), mais o candidato."""
    sql = ("SELECT o.*, c.nome AS cand_nome, c.email AS cand_email, c.telefone AS cand_telefone"
           " FROM onboardings o JOIN candidatos c ON c.id=o.candidato_id"
           " WHERE o.empresa_id=? AND c.empresa_id=o.empresa_id AND o.status IN ('em_andamento','concluido')")
    p = [gestor["empresa_id"]]
    if tipo:
        sql += " AND o.tipo=?"
        p.append(tipo)
    linhas = conn.execute(sql + " ORDER BY o.id", p).fetchall()
    ids = {int(x) for x in ids} if ids else None
    d_de, d_ate = _data(de), _data(ate)
    saida = []
    for ob in linhas:
        if ids is not None and ob["id"] not in ids:
            continue
        cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
        if not cand or not srv.gestor_ve_candidato(gestor, cand):
            continue
        inicio = _data(_json(ob["oferta"], {}).get("data_inicio"))
        if d_de and (not inicio or inicio < d_de):
            continue
        if d_ate and (not inicio or inicio > d_ate):
            continue
        saida.append(ob)
    return saida


def lista_contratacoes(conn, gestor, de=None, ate=None):
    out = []
    for ob in _hires(conn, gestor, de=de, ate=ate):
        oferta = _json(ob["oferta"], {})
        out.append({"id": ob["id"], "candidato_id": ob["candidato_id"], "nome": ob["cand_nome"] or "",
                    "tipo": ob["tipo"], "status": ob["status"], "cargo": oferta.get("cargo") or "",
                    "data_inicio": oferta.get("data_inicio") or ""})
    return out


def _form(conn, ob_id, chave):
    lista = onboarding.docs(conn, ob_id, "formulario", chave)
    if not lista or not lista[-1]["dados_cifrados"]:
        return {}
    return onboarding.decifrar_dict(conn, lista[-1]["dados_cifrados"])


def _separar_nome(nome):
    partes = [p for p in str(nome or "").split() if p]
    if not partes:
        return "", "", ""
    if len(partes) == 1:
        return partes[0], "", ""
    inicial = partes[1][0].upper() if len(partes) > 2 else ""
    return partes[0], inicial, partes[-1]


def dados_brutos(conn, ob, uf_trabalho=""):
    """Todos os campos (inclusive os sensíveis) de um onboarding, sem formatação de provedor."""
    oferta = _json(ob["oferta"], {})
    dados = _json(ob["dados"], {})
    pag = _json(ob["pagamento"], {})
    sens = onboarding.sensiveis(conn, ob) if ob["sensiveis"] else {}
    tipo = ob["tipo"]
    if tipo == "w2":
        f = _form(conn, ob["id"], "w4") or _form(conn, ob["id"], "i9")
    else:
        f = _form(conn, ob["id"], "w9")
    nome_legal = dados.get("nome_legal") or (ob["cand_nome"] if "cand_nome" in ob.keys() else "")
    p, i, s = _separar_nome(nome_legal or (f.get("nome") if tipo == "1099" else ""))
    r = {
        "primeiro_nome": f.get("primeiro_nome") or p,
        "inicial": (f.get("inicial_meio") or i or "")[:1].upper(),
        "sobrenome": f.get("sobrenome") or s,
        "nome_preferido": dados.get("nome_preferido") or "",
        "email": dados.get("email") or (ob["cand_email"] if "cand_email" in ob.keys() else "") or "",
        "telefone": dados.get("telefone") or (ob["cand_telefone"] if "cand_telefone" in ob.keys() else "") or "",
        "data_inicio": oferta.get("data_inicio") or "",
        "estado_trabalho": uf_trabalho or dados.get("estado") or "",
        "cargo": oferta.get("cargo") or "",
        "valor": oferta.get("valor"),
        "unidade_cod": oferta.get("unidade") or "",
        "nascimento": sens.get("nascimento") or "",
        "ssn": sens.get("ssn") or f.get("ssn") or "",
        "endereco": dados.get("endereco") or f.get("endereco") or "",
        "apto": dados.get("apto") or f.get("apto") or "",
        "cidade": dados.get("cidade") or f.get("cidade") or "",
        "estado": dados.get("estado") or f.get("estado") or "",
        "cep": dados.get("cep") or f.get("cep") or "",
        "metodo_cod": pag.get("metodo") or "",
        "banco": pag.get("banco") or "" if pag.get("metodo") == "deposito" else "",
        "tipo_conta_cod": pag.get("tipo_conta") or "" if pag.get("metodo") == "deposito" else "",
        "routing": sens.get("routing") or "" if pag.get("metodo") == "deposito" else "",
        "conta": sens.get("conta") or "" if pag.get("metodo") == "deposito" else "",
        "tipo": tipo,
    }
    if tipo == "1099":
        tipo_tin = f.get("tipo_tin") or ("ein" if f.get("ein") or sens.get("ein") else "ssn")
        r["tipo_tin_cod"] = tipo_tin
        r["tin"] = (f.get("ein") or sens.get("ein")) if tipo_tin == "ein" else (f.get("ssn") or sens.get("ssn") or "")
        r["nome_w9"] = f.get("nome") or nome_legal or ""
        r["nome_empresa"] = f.get("nome_empresa") or ""
        cls = f.get("classificacao") or ""
        txt = CLASSIFICACAO_W9.get(cls, cls)
        if cls == "llc" and f.get("llc_classificacao"):
            txt = "LLC (%s)" % f["llc_classificacao"]
        elif cls == "outro" and f.get("outro_descricao"):
            txt = "Other: %s" % f["outro_descricao"]
        r["classificacao"] = txt
        r["membro_cod"] = "1099_empresa" if (r["nome_empresa"] or (cls and cls != "individual")) else "1099_individual"
        r["tem_w9"] = bool(f)
    else:
        r["membro_cod"] = "w2"
    return r


def _fmt_data(iso, provedor):
    d = _data(iso)
    if not d:
        return ""
    return d.isoformat() if provedor == "generico" else d.strftime("%m/%d/%Y")


def _fmt_ssn(v):
    d = _digitos(v)
    return "%s-%s-%s" % (d[:3], d[3:5], d[5:]) if len(d) == 9 else str(v or "")


def _fmt_ein(v):
    d = _digitos(v)
    return "%s-%s" % (d[:2], d[2:]) if len(d) == 9 else str(v or "")


def _fmt_tel(v):
    d = _digitos(v)
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return "(%s) %s-%s" % (d[:3], d[3:6], d[6:]) if len(d) == 10 else d


def formatar(r, provedor):
    """{chave: texto} já no formato do provedor."""
    V = VALORES[provedor]
    try:
        valor = "%.2f" % float(r.get("valor"))
    except (TypeError, ValueError):
        valor = ""
    out = {
        "tipo_membro": V["membro"].get(r["membro_cod"], ""),
        "primeiro_nome": r["primeiro_nome"], "inicial": r["inicial"], "sobrenome": r["sobrenome"],
        "nome_preferido": r.get("nome_preferido", ""), "nome_w9": r.get("nome_w9", ""),
        "nome_empresa": r.get("nome_empresa", ""), "classificacao": r.get("classificacao", ""),
        "email": r["email"], "telefone": _fmt_tel(r["telefone"]),
        "data_inicio": _fmt_data(r["data_inicio"], provedor), "estado_trabalho": r["estado_trabalho"],
        "cargo": r["cargo"], "tipo_emprego": V["emprego"].get(r["unidade_cod"], ""), "valor": valor,
        "unidade": V["unidade"].get(r["unidade_cod"], r["unidade_cod"]),
        "ssn": _fmt_ssn(r["ssn"]), "nascimento": _fmt_data(r["nascimento"], provedor),
        "tipo_tin": {"ssn": "SSN", "ein": "EIN"}.get(r.get("tipo_tin_cod", ""), ""),
        "tin": (_fmt_ein(r.get("tin")) if r.get("tipo_tin_cod") == "ein" else _fmt_ssn(r.get("tin"))) if r.get("tin") else "",
        "endereco": r["endereco"], "apto": r["apto"], "cidade": r["cidade"], "estado": r["estado"], "cep": r["cep"],
        "metodo": V["metodo"].get(r["metodo_cod"], ""), "banco": r["banco"],
        "tipo_conta": V["conta"].get(r["tipo_conta_cod"], ""), "routing": _digitos(r["routing"]),
        "conta": _digitos(r["conta"]),
    }
    if provedor == "generico" and out["tipo_tin"]:
        out["tipo_tin"] = out["tipo_tin"].lower()
    return out


def colunas_do_arquivo(cfg, provedor, tipo, incluir_sensiveis):
    nomes = colunas(cfg, provedor)
    saida = []
    for k, sensivel, aplica in CAMPOS:
        if aplica not in ("ambos", tipo):
            continue
        if sensivel and not incluir_sensiveis:
            continue
        if not nomes.get(k):
            continue
        saida.append((k, nomes[k]))
    return saida


def _celula(v):
    """Evita fórmulas no Excel/Sheets (injeção de CSV)."""
    s = "" if v is None else str(v)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    return s


def montar(conn, gestor, provedor, tipo, ids=None, de=None, ate=None, incluir_sensiveis=False):
    """(colunas [(chave, nome)], linhas [[...]], avisos) do arquivo."""
    if provedor not in PROVEDORES:
        raise ErroIntegracao(400, "Sistema de folha inválido")
    if tipo not in ("w2", "1099"):
        raise ErroIntegracao(400, "Tipo de vínculo inválido")
    cfg = config(conn, gestor["empresa_id"])
    uf = estado_trabalho(conn, gestor["empresa_id"], cfg)
    cols = colunas_do_arquivo(cfg, provedor, tipo, incluir_sensiveis)
    linhas, avisos = [], []
    for ob in _hires(conn, gestor, ids=ids, de=de, ate=ate, tipo=tipo):
        r = dados_brutos(conn, ob, uf)
        f = formatar(r, provedor)
        linhas.append([_celula(f.get(k, "")) for k, _ in cols])
        faltas = []
        if tipo == "1099" and not r.get("tem_w9"):
            faltas.append("w9")
        if tipo == "w2" and not r["ssn"]:
            faltas.append("ssn")
        if not r["endereco"]:
            faltas.append("endereco")
        if faltas:
            avisos.append({"onboarding_id": ob["id"], "nome": ob["cand_nome"] or "", "faltando": faltas})
    return cols, linhas, avisos


def csv_bytes(cols, linhas):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow([n for _, n in cols])
    for l in linhas:
        w.writerow(l)
    return buf.getvalue().encode("utf-8")


def _senha_bloqueada(gestor_id):
    agora = time.time()
    with _trava:
        recentes = [t for t in _falhas_senha.get(gestor_id, []) if agora - t < _JANELA_SENHA]
        _falhas_senha[gestor_id] = recentes
        return len(recentes) >= _LIMITE_SENHA


def _marcar_falha_senha(gestor_id):
    with _trava:
        _falhas_senha.setdefault(gestor_id, []).append(time.time())


def zerar_limites():
    with _trava:
        _falhas_senha.clear()


def exportar(h, conn, gestor, d, ip):
    provedor = d.get("provedor")
    tipo = d.get("tipo") or "w2"
    incluir = bool(d.get("incluir_sensiveis"))
    if incluir:
        if _senha_bloqueada(gestor["id"]):
            return _resp(h, 429, {"erro": "Muitas tentativas. Aguarde alguns minutos."})
        if not srv.senha_confere(str(d.get("senha") or ""), gestor["senha"]):
            _marcar_falha_senha(gestor["id"])
            srv.seguranca.registrar(conn, "exportar_folha_senha_incorreta", gestor, "provedor:%s" % provedor, ip)
            return _resp(h, 403, {"erro": "Senha incorreta"})
    cols, linhas, _ = montar(conn, gestor, provedor, tipo, ids=d.get("ids") or None, de=d.get("de"),
                             ate=d.get("ate"), incluir_sensiveis=incluir)
    if not linhas:
        return _resp(h, 400, {"erro": "Nenhuma contratação para exportar com esses filtros"})
    corpo = csv_bytes(cols, linhas)
    srv.seguranca.registrar(conn, "exportar_folha", gestor, "provedor:%s tipo:%s registros:%d sensiveis:%s" % (
        provedor, tipo, len(linhas), "sim" if incluir else "nao"), ip)
    nome = "%s-%s-%s.csv" % (provedor, "employees" if tipo == "w2" else "contractors-1099", date.today().isoformat())
    h.send_response(200)
    h.send_header("Content-Type", "text/csv; charset=utf-8")
    h.send_header("Content-Disposition", 'attachment; filename="%s"' % nome)
    h.send_header("Content-Length", str(len(corpo)))
    h.send_header("Cache-Control", "no-store, max-age=0")
    h.send_header("Pragma", "no-cache")
    h.end_headers()
    h.wfile.write(corpo)
    return True


# ------------------------------------------------------------- B. Checkr

def _checkr(conn, empresa_id, metodo, caminho, corpo=None, cfg=None):
    """Chamada à API da Checkr (Basic auth com a chave como usuário). Devolve o JSON."""
    cfg = cfg or config(conn, empresa_id)
    chave = chave_checkr(conn, empresa_id, cfg)
    if not chave:
        raise ErroIntegracao(400, "Configure a Checkr em Configurações antes de pedir a verificação")
    url = CHECKR_API[cfg["checkr"]["ambiente"]] + caminho
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo)
    req.add_header("Authorization", "Basic " + base64.b64encode((chave + ":").encode()).decode())
    req.add_header("Accept", "application/json")
    if dados is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return _json(r.read().decode("utf-8", "replace"), {})
    except urllib.error.HTTPError as e:
        try:
            det = _json(e.read().decode("utf-8", "replace"), {})
        except Exception:  # noqa: BLE001
            det = {}
        if e.code in (401, 403):
            raise ErroIntegracao(400, "A Checkr recusou a chave da API. Confira em Configurações.")
        msg = det.get("error") if isinstance(det, dict) else ""
        if isinstance(msg, list):
            msg = "; ".join(str(x) for x in msg)
        raise ErroIntegracao(502, "Erro na Checkr: %s" % (_limpo(msg, 200) or ("HTTP %d" % e.code)))
    except (urllib.error.URLError, OSError, ValueError):
        raise ErroIntegracao(502, "Sem conexão com a Checkr. Tente de novo.")


def testar_checkr(conn, empresa_id):
    r = _checkr(conn, empresa_id, "GET", "/packages")
    pacotes = r.get("data") if isinstance(r, dict) else None
    return [{"slug": p.get("slug"), "nome": p.get("name")} for p in (pacotes or []) if isinstance(p, dict)]


def verificacoes(conn, empresa_id, cand_id):
    return conn.execute("SELECT * FROM checkr_verificacoes WHERE empresa_id=? AND candidato_id=? ORDER BY id DESC",
                        (empresa_id, cand_id)).fetchall()


def link_painel(v):
    if not v["checkr_candidato_id"]:
        return ""
    base = CHECKR_PAINEL.get(v["ambiente"] or "producao", CHECKR_PAINEL["producao"])
    return "%s/candidates/%s" % (base, re.sub(r"[^A-Za-z0-9_\-]", "", v["checkr_candidato_id"]))


def _v_publica(v):
    return {"id": v["id"], "status": v["status"], "resultado": v["resultado"], "pacote": v["pacote"],
            "criado_em": v["criado_em"], "atualizado_em": v["atualizado_em"], "concluido_em": v["concluido_em"],
            "criado_por": v["criado_por"], "link": link_painel(v), "convite_url": v["convite_url"],
            "staging": v["ambiente"] == "staging"}


def _tem_proposta(conn, empresa_id, cand_id):
    if conn.execute("SELECT 1 FROM onboardings WHERE candidato_id=? AND empresa_id=? AND status!='cancelado' LIMIT 1",
                    (cand_id, empresa_id)).fetchone():
        return True
    return bool(conn.execute(
        "SELECT 1 FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id WHERE ca.candidato_id=? AND v.empresa_id=?"
        " AND ca.etapa IN ('proposta','contratado') LIMIT 1", (cand_id, empresa_id)).fetchone())


def estado_candidato(conn, gestor, cand):
    cfg = config(conn, gestor["empresa_id"])
    ck = cfg["checkr"]
    lista = verificacoes(conn, gestor["empresa_id"], cand["id"])
    configurado = bool(ck["chave_cifrada"] and ck["pacote"] and ck["estado"])
    motivo = ""
    if not configurado:
        motivo = "sem_config"
    elif not (cand["email"] or "").strip():
        motivo = "sem_email"
    elif not _tem_proposta(conn, gestor["empresa_id"], cand["id"]):
        motivo = "sem_proposta"
    elif lista and lista[0]["status"] in STATUS_ABERTOS:
        motivo = "em_andamento"
    tem_w2 = bool(conn.execute("SELECT 1 FROM onboardings WHERE candidato_id=? AND empresa_id=? AND tipo='w2'"
                               " AND status!='cancelado' LIMIT 1", (cand["id"], gestor["empresa_id"])).fetchone())
    atual = lista[0]["status"] if lista else ""
    return {"configurado": configurado, "exigir": ck["exigir"], "admin": bool(gestor["is_admin"]),
            "pode_pedir": bool(gestor["is_admin"]) and not motivo, "motivo": motivo, "pacote": ck["pacote"],
            "verificacoes": [_v_publica(v) for v in lista[:5]], "status_atual": atual,
            "aviso_contratar": bool(ck["exigir"] and atual != "clear"), "tem_w2": tem_w2,
            "fcra_url": FCRA_URL, "everify_url": EVERIFY_URL}


def pedir_verificacao(conn, gestor, cand, ip=""):
    est = estado_candidato(conn, gestor, cand)
    if est["motivo"] == "sem_config":
        raise ErroIntegracao(400, "Configure a Checkr em Configurações antes de pedir a verificação")
    if est["motivo"] == "sem_email":
        raise ErroIntegracao(400, "Candidato sem e-mail")
    if est["motivo"] == "sem_proposta":
        raise ErroIntegracao(400, "Envie a proposta antes de pedir a verificação de antecedentes")
    if est["motivo"] == "em_andamento":
        raise ErroIntegracao(409, "Já existe uma verificação de antecedentes em andamento para este candidato")
    cfg = config(conn, gestor["empresa_id"])
    ck = cfg["checkr"]
    primeiro, _, ultimo = _separar_nome(cand["nome"])
    corpo_cand = {"email": cand["email"].strip(), "first_name": primeiro or None, "last_name": ultimo or None,
                  "custom_id": "bussola-%d-%d" % (gestor["empresa_id"], cand["id"])}
    tel = _digitos(cand["telefone"] if "telefone" in cand.keys() else "")
    if len(tel) >= 10:
        corpo_cand["phone"] = tel[-10:]
    corpo_cand = {k: v for k, v in corpo_cand.items() if v}
    rc = _checkr(conn, gestor["empresa_id"], "POST", "/candidates", corpo_cand, cfg)
    checkr_cand = str(rc.get("id") or "")
    if not checkr_cand:
        raise ErroIntegracao(502, "Erro na Checkr: resposta sem o id do candidato")
    local = {"country": "US", "state": ck["estado"]}
    if ck["cidade"]:
        local["city"] = ck["cidade"]
    ri = _checkr(conn, gestor["empresa_id"], "POST", "/invitations",
                 {"candidate_id": checkr_cand, "package": ck["pacote"], "work_locations": [local]}, cfg)
    vid = conn.execute(
        "INSERT INTO checkr_verificacoes (empresa_id, candidato_id, checkr_candidato_id, convite_id, convite_url, pacote,"
        " ambiente, status, criado_por) VALUES (?,?,?,?,?,?,?,'convite_enviado',?)",
        (gestor["empresa_id"], cand["id"], checkr_cand, str(ri.get("id") or ""),
         str(ri.get("invitation_url") or "")[:500], ck["pacote"], ck["ambiente"], gestor["nome"])).lastrowid
    srv.registrar_evento(conn, cand["id"], "onboarding",
                         "Verificação de antecedentes solicitada (Checkr, pacote %s)" % ck["pacote"], gestor["nome"])
    conn.commit()
    srv.seguranca.registrar(conn, "checkr_pedido", gestor, "candidato:%d verificacao:%d" % (cand["id"], vid), ip)
    return vid


def aviso_contratar(conn, gestor, candidatura_id=None, candidato_id=None):
    cand_id = None
    if candidatura_id:
        r = conn.execute("SELECT ca.candidato_id FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                         " WHERE ca.id=? AND v.empresa_id=?", (candidatura_id, gestor["empresa_id"])).fetchone()
        cand_id = r["candidato_id"] if r else None
    elif candidato_id:
        cand_id = candidato_id
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (cand_id,)).fetchone() if cand_id else None
    if not cand or not srv.gestor_ve_candidato(gestor, cand):
        return None
    ck = config(conn, gestor["empresa_id"])["checkr"]
    lista = verificacoes(conn, gestor["empresa_id"], cand["id"])
    atual = lista[0]["status"] if lista else ""
    return {"avisar": bool(ck["exigir"] and atual != "clear"), "status": atual, "fcra_url": FCRA_URL}


# --------------------------------------------------- webhook

def assinatura_valida(chave, corpo, assinatura):
    if not chave or not assinatura:
        return False
    esperado = hmac.new(chave.encode("utf-8"), corpo or b"", hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, str(assinatura).strip().lower())


def novo_status(tipo, obj, atual=""):
    """Status interno a partir do evento da Checkr (None = não muda)."""
    obj = obj if isinstance(obj, dict) else {}
    if tipo == "invitation.created":
        return "convite_enviado"
    if tipo == "invitation.completed":
        return "pendente"
    if tipo == "invitation.expired":
        return "expirado"
    if tipo == "invitation.deleted":
        return "cancelado"
    if not tipo.startswith("report."):
        return None
    if tipo == "report.suspended" or obj.get("status") == "suspended":
        return "suspenso"
    if tipo == "report.canceled" or obj.get("status") == "canceled":
        return "cancelado"
    if tipo in ("report.pre_adverse_action", "report.post_adverse_action", "report.disputed",
                "report.dispute_completed"):
        return None
    if tipo == "report.completed" or obj.get("status") == "complete":
        resultado = obj.get("result")
        if resultado == "clear" or (resultado is None and obj.get("assessment") == "eligible"):
            return "clear"
        if resultado == "consider" or obj.get("assessment") in ("review", "escalated"):
            return "consider"
        return "pendente"
    return "pendente"


def _localizar(conn, obj):
    if not isinstance(obj, dict):
        return None
    cid = str(obj.get("candidate_id") or "")
    if not cid and str(obj.get("object") or "") == "candidate":
        cid = str(obj.get("id") or "")
    if cid:
        v = conn.execute("SELECT * FROM checkr_verificacoes WHERE checkr_candidato_id=? ORDER BY id DESC LIMIT 1",
                         (cid,)).fetchone()
        if v:
            return v
    oid = str(obj.get("id") or "")
    if oid:
        return conn.execute("SELECT * FROM checkr_verificacoes WHERE convite_id=? OR relatorio_id=?"
                            " ORDER BY id DESC LIMIT 1", (oid, oid)).fetchone()
    return None


def processar_webhook(conn, corpo, assinatura):
    """(status http, resposta). Só confia no conteúdo depois de conferir a assinatura."""
    evento = _json(corpo.decode("utf-8", "replace") if corpo else "", None)
    if not isinstance(evento, dict):
        return 400, {"erro": "Evento inválido"}
    data = evento.get("data") if isinstance(evento.get("data"), dict) else {}
    obj = data.get("object") if isinstance(data.get("object"), dict) else {}
    v = _localizar(conn, obj)
    if not v:
        return 404, {"erro": "Verificação não encontrada"}
    try:
        chave = chave_checkr(conn, v["empresa_id"])
    except onboarding.ErroChave:
        return 500, {"erro": "Erro interno"}
    if not assinatura_valida(chave, corpo, assinatura):
        return 401, {"erro": "Assinatura inválida"}
    eid = str(evento.get("id") or "")
    if eid:
        if not conn.execute("INSERT OR IGNORE INTO checkr_eventos (evento_id) VALUES (?)", (eid[:80],)).rowcount:
            return 200, {"ok": True, "repetido": True}
    tipo = str(evento.get("type") or "")
    status = novo_status(tipo, obj, v["status"])
    if tipo.startswith("report.") and obj.get("id"):
        conn.execute("UPDATE checkr_verificacoes SET relatorio_id=? WHERE id=?", (str(obj["id"])[:80], v["id"]))
    if not status or status == v["status"]:
        conn.execute("UPDATE checkr_verificacoes SET atualizado_em=datetime('now') WHERE id=?", (v["id"],))
        conn.commit()
        return 200, {"ok": True}
    concluido = status in ("clear", "consider")
    conn.execute("UPDATE checkr_verificacoes SET status=?, resultado=?, atualizado_em=datetime('now'),"
                 " concluido_em=CASE WHEN ? THEN datetime('now') ELSE concluido_em END WHERE id=?",
                 (status, status if concluido else (v["resultado"] or ""), 1 if concluido else 0, v["id"]))
    srv.registrar_evento(conn, v["candidato_id"], "onboarding",
                         "Verificação de antecedentes (Checkr): %s" % ROTULO_EVENTO[status], "sistema")
    conn.commit()
    srv.seguranca.registrar(conn, "checkr_status", None, "candidato:%d status:%s" % (v["candidato_id"], status), "",
                            empresa_id=v["empresa_id"], quem="Checkr")
    if concluido:
        avisar_admins(conn, v["id"])
    return 200, {"ok": True}


# --------------------------------------------------- e-mail aos administradores

T = {
    "pt": {"assunto": "Verificação de antecedentes concluída: {nome}",
           "corpo": "A verificação de antecedentes de {nome} pela Checkr foi concluída. Resultado: {resultado}.",
           "clear": "clear (sem apontamentos)", "consider": "consider (revisar o relatório)",
           "consider_nota": ("Se a empresa pensar em não contratar por causa do relatório, a FCRA exige o processo de "
                             "ação adversa (aviso prévio com cópia do relatório e resumo de direitos, prazo e aviso "
                             "final). Isso é responsabilidade do empregador. Orientação da FTC: {url}"),
           "botao_checkr": "Abrir o relatório na Checkr", "botao_ficha": "Abrir a ficha do candidato"},
    "en": {"assunto": "Background check complete: {nome}",
           "corpo": "The Checkr background check for {nome} is complete. Result: {resultado}.",
           "clear": "clear", "consider": "consider (review the report)",
           "consider_nota": ("If the company is considering not hiring because of the report, the FCRA requires the "
                             "adverse action process (a pre-adverse action notice with a copy of the report and the "
                             "summary of rights, a waiting period, and a final notice). This is the employer's "
                             "responsibility. FTC guidance: {url}"),
           "botao_checkr": "Open the report in Checkr", "botao_ficha": "Open the candidate profile"},
    "es": {"assunto": "Verificación de antecedentes completada: {nome}",
           "corpo": "La verificación de antecedentes de {nome} con Checkr se completó. Resultado: {resultado}.",
           "clear": "clear (sin observaciones)", "consider": "consider (revisar el informe)",
           "consider_nota": ("Si la empresa considera no contratar por el informe, la FCRA exige el proceso de acción "
                             "adversa (aviso previo con copia del informe y resumen de derechos, un plazo de espera y "
                             "un aviso final). Esto es responsabilidad del empleador. Guía de la FTC: {url}"),
           "botao_checkr": "Abrir el informe en Checkr", "botao_ficha": "Abrir la ficha del candidato"},
}


def email_admin(conn, v, cand, lang):
    lang = _idioma(lang)
    tx = T[lang]
    m = srv.mensagens
    marca = m.marca(conn, v["empresa_id"])
    nome = cand["nome"] or ""
    corpo = tx["corpo"].format(nome=nome, resultado=tx.get(v["status"], v["status"]))
    partes, texto = [m._paragrafo(corpo)], [corpo, ""]
    if v["status"] == "consider":
        nota = tx["consider_nota"].format(url=FCRA_URL)
        partes.append(m._paragrafo(nota, "#8A6A2B", 14))
        texto += [nota, ""]
    link = link_painel(v)
    if link:
        partes.append(m._botao(link, tx["botao_checkr"]))
        texto.append(link)
    ficha = "%s/gestor#candidato=%d" % (srv.url_publica(conn), cand["id"])
    partes.append(m._botao(ficha, tx["botao_ficha"], "#5E7086"))
    texto.append(ficha)
    assunto = tx["assunto"].format(nome=nome)
    cor = "#2E9E6A" if v["status"] == "clear" else "#C2872B"
    return assunto, "\n".join(texto), m.layout("".join(partes), lang, marca, ("🔎", assunto, cor))


def _enviar_admins(conn, vid):
    v = conn.execute("SELECT * FROM checkr_verificacoes WHERE id=?", (vid,)).fetchone()
    if not v or not srv.config_get(conn, "smtp_host"):
        return 0
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (v["candidato_id"],)).fetchone()
    if not cand:
        return 0
    n = 0
    for g in conn.execute("SELECT email, idioma FROM gestores WHERE empresa_id=? AND aprovado=1 AND is_admin=1",
                          (v["empresa_id"],)).fetchall():
        if not (g["email"] or "").strip():
            continue
        assunto, texto, html = email_admin(conn, v, cand, g["idioma"])
        ok, _ = srv.enviar_email(conn, g["email"].strip(), assunto, texto, html=html)
        n += 1 if ok else 0
    srv.registrar_evento(conn, cand["id"], "email",
                         "Verificação de antecedentes concluída: aviso a %d administrador(es)" % n)
    conn.commit()
    return n


def avisar_admins(conn, vid):
    if not ENVIO_EM_SEGUNDO_PLANO:
        return _enviar_admins(conn, vid)

    def rodar():
        c = srv.db()
        try:
            _enviar_admins(c, vid)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Checkr: aviso aos administradores falhou: %s\n" % type(exc).__name__)
        finally:
            c.close()
    threading.Thread(target=rodar, daemon=True).start()
    return None


# ------------------------------------------------------------- rotas

def rotear_publico(h, method, path, conn):
    if path != "/api/integracoes/checkr/webhook":
        return None
    if method != "POST":
        return _resp(h, 405, {"erro": "Método não permitido"})
    corpo = getattr(h, "_raw", None) or b""
    status, dados = processar_webhook(conn, corpo, h.headers.get("X-Checkr-Signature") or "")
    return _resp(h, status, dados)


def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/integracoes-rh/"):
        return None
    empresa_id = gestor["empresa_id"]
    ip = h._ip_cliente()
    sub = path[len("/api/gestor/integracoes-rh/"):]
    q = parse_qs(urlparse(h.path).query)
    admin = bool(gestor["is_admin"])
    try:
        # ---- configuração (administrador)
        if sub == "config":
            if not admin:
                return _resp(h, 403, {"erro": "Apenas o administrador da empresa configura as integrações"})
            if method == "GET":
                return _resp(h, 200, config_publica(conn, empresa_id))
            if method == "POST":
                salvar_config(conn, empresa_id, h._body() or {})
                srv.seguranca.registrar(conn, "integracoes_rh_config", gestor, "", ip)
                return _resp(h, 200, dict(config_publica(conn, empresa_id), ok=True))
        if sub == "checkr/testar" and method == "POST":
            if not admin:
                return _resp(h, 403, {"erro": "Apenas o administrador da empresa configura as integrações"})
            return _resp(h, 200, {"ok": True, "pacotes": testar_checkr(conn, empresa_id)})

        # ---- Checkr na ficha do candidato
        m = re.match(r"^checkr/candidato/(\d+)(/pedir)?$", sub)
        if m:
            cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)).fetchone()
            if not cand or cand["empresa_id"] != empresa_id or not srv.gestor_ve_candidato(gestor, cand):
                return _resp(h, 404, {"erro": "Candidato não encontrado"})
            if not m.group(2) and method == "GET":
                return _resp(h, 200, estado_candidato(conn, gestor, cand))
            if m.group(2) and method == "POST":
                if not admin:
                    return _resp(h, 403, {"erro": "Apenas o administrador da empresa pede a verificação de antecedentes"})
                pedir_verificacao(conn, gestor, cand, ip)
                return _resp(h, 200, dict(estado_candidato(conn, gestor, cand), ok=True))
        if sub == "checkr/aviso" and method == "GET":
            r = aviso_contratar(conn, gestor, (q.get("candidatura") or [None])[0], (q.get("candidato") or [None])[0])
            if r is None:
                return _resp(h, 404, {"erro": "Candidato não encontrado"})
            return _resp(h, 200, r)

        # ---- exportação para a folha (administrador)
        if sub.startswith("folha/"):
            if not admin:
                return _resp(h, 403, {"erro": "Apenas o administrador da empresa exporta para a folha"})
            if sub == "folha/contratacoes" and method == "GET":
                return _resp(h, 200, {"contratacoes": lista_contratacoes(
                    conn, gestor, (q.get("de") or [None])[0], (q.get("ate") or [None])[0])})
            if sub == "folha/previa" and method == "POST":
                d = h._body() or {}
                saida = {}
                for tipo in ("w2", "1099"):
                    cols, linhas, avisos = montar(conn, gestor, d.get("provedor"), tipo, ids=d.get("ids") or None,
                                                  de=d.get("de"), ate=d.get("ate"), incluir_sensiveis=False)
                    cfg = config(conn, empresa_id)
                    sens = [n for k, n in colunas_do_arquivo(cfg, d.get("provedor"), tipo, True) if k in SENSIVEIS]
                    saida[tipo] = {"colunas": [n for _, n in cols], "linhas": linhas[:50], "total": len(linhas),
                                   "sensiveis": sens, "avisos": avisos}
                return _resp(h, 200, saida)
            if sub == "folha/exportar" and method == "POST":
                return exportar(h, conn, gestor, h._body() or {}, ip)
    except ErroIntegracao as e:
        return _resp(h, e.status, {"erro": e.mensagem})
    except onboarding.ErroChave as e:
        sys.stderr.write("Integrações RH: %s\n" % e)
        return _resp(h, 500, {"erro": "A chave de criptografia dos dados não foi encontrada ou não confere. Fale com o administrador do sistema."})
    return _resp(h, 404, {"erro": "Rota não encontrada"})
