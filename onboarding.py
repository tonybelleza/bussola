"""Onboarding de novos contratados (estilo Gusto), com portal próprio por link.

Fluxo
- Na ficha do candidato o administrador envia a proposta e o onboarding: tipo de
  vínculo (W-2 empregado ou 1099 prestador), cargo, data de início, pagamento,
  horário, documentos, formas de pagamento aceitas e prazo. Isso cria um registro
  em onboardings, manda o link /onboarding?t=TOKEN por e-mail (idioma da pessoa,
  logo da empresa) e move a candidatura para "proposta". Quando a pessoa assina a
  carta de proposta, a candidatura vai para "contratado".
- O portal (público, por token) tem consentimento ESIGN/UETA no início e as
  etapas: carta de proposta, dados pessoais, documentos para assinar (modelos da
  empresa), formulários fiscais oficiais (formularios.py: W-4, CT-W4, I-9 e W-9),
  envio de documentos (foto do documento, I-9...), forma de pagamento e revisão.
- Cada assinatura gera um PDF (fpdf2) com o documento e uma página de certificado
  (nome, e-mail, IP, navegador, data e hora UTC, SHA-256 do texto, consentimento).

Segurança
- SSN, ITIN/EIN, routing e conta bancária, número da carteira de motorista e data
  de nascimento ficam cifrados (Fernet). Os arquivos do onboarding (PDFs e
  uploads) também ficam cifrados em UPLOAD_DIR/onboarding/<id>/ e só saem por
  rotas autenticadas (o dono do token, para os próprios arquivos, e os gestores da
  empresa).
- Chave: variável de ambiente BUSSOLA_CHAVE_DADOS ou o arquivo BASE_DIR/chave_dados.key
  (criado no primeiro uso, permissão 0600, fora de public/). Se já houver dados
  cifrados e a chave sumir, o servidor NÃO cria outra: devolve um erro claro.
  Um verificador cifrado na tabela config detecta chave trocada.
- Valores sensíveis nunca vão para logs, eventos ou e-mails. O painel mostra só a
  máscara (•••1234); "revelar" é só do administrador e entra na trilha de auditoria.

Os textos dos modelos padrão (no fim do arquivo) são RASCUNHOS para revisão de um
advogado. Tudo isolado por empresa.
"""
import base64
import hashlib
import io
import json
import os
import re
import secrets
import sys
import threading
import time
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

srv = None  # módulo server, injetado por ligar()

try:  # formularios.py (W-9, W-4, I-9, CT-W4) é de outro módulo: pode não existir ainda
    import formularios
except Exception:  # noqa: BLE001
    formularios = None

ENVIO_EM_SEGUNDO_PLANO = True
INTERVALO_ROTINA = 3600  # segundos entre verificações de lembrete

TIPOS = ("w2", "1099")
STATUS = ("enviado", "em_andamento", "concluido", "cancelado")
ATIVOS = ("enviado", "em_andamento")
ETAPAS = ("oferta", "dados", "documentos", "formularios", "arquivos", "pagamento", "revisao")
METODOS = ("deposito", "zelle", "cheque", "provedor")
UNIDADES = ("hora", "dia", "servico", "salario")
FORMULARIOS_FEDERAIS = {"w2": ["w4", "i9"], "1099": ["w9"]}
FORMULARIOS_ESTADUAIS = ("ctw4",)
TAMANHOS = ("XS", "S", "M", "L", "XL", "2XL", "3XL")
MAX_ARQUIVO = 10 * 1024 * 1024
MAX_POR_CATEGORIA = 4
CHAVE_ENV = "BUSSOLA_CHAVE_DADOS"
NOME_ARQUIVO_CHAVE = "chave_dados.key"

# categorias de envio de documentos: (chave, quando é pedida)
CATEGORIAS = ("id_frente", "id_verso", "cnh_frente", "cnh_verso", "i9_lista_a", "i9_lista_b", "i9_lista_c",
              "comprovante_endereco", "cheque_anulado")

# campos sensíveis dos dados pessoais e do pagamento (sempre cifrados)
SENSIVEIS_DADOS = ("nascimento", "cnh_numero")
SENSIVEIS_PAGAMENTO = ("routing", "conta")
# campos dos formulários oficiais que contam como sensíveis (nome da chave)
RE_SENSIVEL = re.compile(r"(ssn|social|itin|\bein\b|_ein|ein_|tin\b|_tin|tin_|nascimento|birth|dob|passport|passaporte|"
                         r"uscis|alien|a_number|anumber|i94|i_94|documento_numero|numero_documento|doc_numero|"
                         r"routing|account|conta)", re.I)

PADRAO_CFG = {
    "ordem": ["oferta", "dados", "documentos", "formularios", "arquivos", "pagamento"],
    "metodos": ["deposito", "zelle", "cheque"],
    "estaduais": None,          # None = automático (CT-W4 quando a empresa é de Connecticut)
    "prazo_dias": 7,
    "lembrete_dias": 2,
    "retencao_dias": 0,         # 0 = guardar; N = oferecer a limpeza N dias depois de concluído
    "provedor_nome": "Gusto",
    "periodo_experiencia": 90,
    # dados do empregador para os formulários oficiais (W-4, CT-W4, W-9, I-9 Seção 2)
    "empregador_nome": "",
    "empregador_endereco": "",
    "empregador_cidade_estado_cep": "",
    "empregador_ein": "",
    "empregador_contato": "",
    "empregador_telefone": "",
}
CAMPOS_EMPREGADOR_CFG = ("empregador_nome", "empregador_endereco", "empregador_cidade_estado_cep", "empregador_ein",
                         "empregador_contato", "empregador_telefone")

# limite leve das rotas públicas (por IP)
_JANELA = 600
_LIMITE_PEDIDOS = 300
_LIMITE_INVALIDOS = 20
_pedidos = {}
_invalidos = {}
_trava_limite = threading.Lock()

_fernet = None
_trava_chave = threading.Lock()


class ErroOnboarding(Exception):
    def __init__(self, status, mensagem, extra=None):
        Exception.__init__(self, mensagem)
        self.status = status
        self.mensagem = mensagem
        self.extra = extra or {}


class ErroChave(Exception):
    pass


def ligar(modulo_server):
    global srv
    srv = modulo_server


def _formularios():
    """O módulo formularios (importado de novo se apareceu depois do arranque)."""
    global formularios
    if formularios is None:
        try:
            import formularios as _f
            formularios = _f
        except Exception:  # noqa: BLE001
            return None
    return formularios


# ------------------------------------------------------------- banco

def init_onboarding(c):
    c.execute(
        "CREATE TABLE IF NOT EXISTS onboardings ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " candidato_id INTEGER NOT NULL REFERENCES candidatos(id) ON DELETE CASCADE,"
        " candidatura_id INTEGER,"
        " token TEXT UNIQUE NOT NULL,"
        " tipo TEXT NOT NULL DEFAULT 'w2',"
        " oferta TEXT NOT NULL DEFAULT '{}',"
        " status TEXT NOT NULL DEFAULT 'enviado',"
        " prazo TEXT DEFAULT '',"
        " idioma TEXT DEFAULT '',"
        " dados TEXT DEFAULT '{}',"
        " pagamento TEXT DEFAULT '{}',"
        " sensiveis TEXT DEFAULT '',"
        " consentimento TEXT DEFAULT '',"
        " criado_por TEXT DEFAULT '',"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " atualizado_em TEXT DEFAULT (datetime('now')),"
        " concluido_em TEXT DEFAULT '',"
        " cancelado_em TEXT DEFAULT '',"
        " lembrete_em TEXT DEFAULT '',"
        " lembretes INTEGER DEFAULT 0,"
        " purgado_em TEXT DEFAULT '')"
    )
    c.execute("CREATE INDEX IF NOT EXISTS ix_onboardings_empresa ON onboardings(empresa_id, status)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_onboardings_candidato ON onboardings(candidato_id)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_onboardings_ativo ON onboardings(candidato_id)"
              " WHERE status IN ('enviado','em_andamento')")
    c.execute(
        "CREATE TABLE IF NOT EXISTS onboarding_docs ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " onboarding_id INTEGER NOT NULL REFERENCES onboardings(id) ON DELETE CASCADE,"
        " empresa_id INTEGER NOT NULL,"
        " tipo TEXT NOT NULL,"                 # assinatura | formulario | arquivo | i9_secao2
        " chave TEXT NOT NULL,"                # tpl:<id> | w4 | i9 | id_frente ...
        " titulo TEXT DEFAULT '',"
        " arquivo TEXT DEFAULT '',"            # relativo a UPLOAD_DIR, sempre cifrado
        " mime TEXT DEFAULT '',"
        " tamanho INTEGER DEFAULT 0,"
        " sha256 TEXT DEFAULT '',"             # do arquivo final (antes de cifrar)
        " sha256_texto TEXT DEFAULT '',"       # do texto ou PDF original apresentado
        " nome_original TEXT DEFAULT '',"
        " idioma TEXT DEFAULT '',"
        " assinante TEXT DEFAULT '',"
        " ip TEXT DEFAULT '',"
        " ua TEXT DEFAULT '',"
        " declaracao TEXT DEFAULT '',"
        " dados_cifrados TEXT DEFAULT '',"
        " ativo INTEGER NOT NULL DEFAULT 1,"
        " criado_em TEXT DEFAULT (datetime('now')))"
    )
    c.execute("CREATE INDEX IF NOT EXISTS ix_onboarding_docs ON onboarding_docs(onboarding_id, tipo, ativo)")
    c.execute(
        "CREATE TABLE IF NOT EXISTS onboarding_templates ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " empresa_id INTEGER NOT NULL,"
        " chave TEXT DEFAULT '',"
        " categoria TEXT NOT NULL DEFAULT 'documento',"   # oferta | documento
        " titulos TEXT NOT NULL DEFAULT '{}',"            # {en, pt, es}
        " tipo TEXT NOT NULL DEFAULT 'texto',"            # texto | pdf
        " textos TEXT NOT NULL DEFAULT '{}',"             # {en, pt, es}
        " arquivo TEXT DEFAULT '',"
        " aplica TEXT NOT NULL DEFAULT 'ambos',"          # w2 | 1099 | ambos
        " ordem INTEGER NOT NULL DEFAULT 0,"
        " requer_declaracao INTEGER NOT NULL DEFAULT 0,"
        " ativo INTEGER NOT NULL DEFAULT 1,"
        " criado_em TEXT DEFAULT (datetime('now')),"
        " atualizado_em TEXT DEFAULT (datetime('now')))"
    )
    c.execute("CREATE INDEX IF NOT EXISTS ix_onboarding_templates ON onboarding_templates(empresa_id, ordem)")


# ------------------------------------------------------------- utilidades

def idioma(valor):
    return srv.mensagens.idioma(valor)


def _agora():
    return datetime.now(timezone.utc)


def _hoje():
    """Data de hoje no fuso da plataforma (Connecticut), para {{data}} e prazos."""
    try:
        from zoneinfo import ZoneInfo
        return _agora().astimezone(ZoneInfo("America/New_York")).date()
    except Exception:  # noqa: BLE001
        return _agora().date()


def apagar_arquivos_candidato(conn, candidato_id):
    """Remove do disco os PDFs e documentos cifrados dos onboardings do candidato
    (chamado ao excluir ou anonimizar o candidato)."""
    import shutil
    for r in conn.execute("SELECT id FROM onboardings WHERE candidato_id=?", (candidato_id,)).fetchall():
        shutil.rmtree(os.path.join(srv.UPLOAD_DIR, "onboarding", str(int(r["id"]))), ignore_errors=True)
    conn.execute("UPDATE onboardings SET sensiveis='' WHERE candidato_id=?", (candidato_id,))


def _iso_utc(dt=None):
    return (dt or _agora()).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json(texto, padrao=None):
    try:
        v = json.loads(texto) if texto else None
    except ValueError:
        v = None
    return padrao if v is None else v


def _data(texto):
    try:
        return date.fromisoformat(str(texto or "")[:10])
    except ValueError:
        return None


def _limpo(v, n=200):
    return re.sub(r"\s+", " ", str(v or "")).strip()[:n]


def _digitos(v):
    return re.sub(r"\D", "", str(v or ""))


MESES = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"],
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
           "novembro", "dezembro"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
           "noviembre", "diciembre"],
}


def data_extenso(d, lang):
    if isinstance(d, str):
        d = _data(d)
    if not d:
        return ""
    lang = idioma(lang)
    if lang == "en":
        return "%s %d, %d" % (MESES["en"][d.month - 1], d.day, d.year)
    return "%d de %s de %d" % (d.day, MESES[lang][d.month - 1], d.year)


UNIDADE_TXT = {
    "en": {"hora": "per hour", "dia": "per day", "servico": "per service", "salario": "per year (salary)"},
    "pt": {"hora": "por hora", "dia": "por dia", "servico": "por serviço", "salario": "por ano (salário)"},
    "es": {"hora": "por hora", "dia": "por día", "servico": "por servicio", "salario": "por año (salario)"},
}


def texto_pagamento(oferta, lang):
    try:
        valor = float(oferta.get("valor") or 0)
    except (TypeError, ValueError):
        valor = 0
    lang = idioma(lang)
    return "$%s %s" % ("{:,.2f}".format(valor), UNIDADE_TXT[lang].get(oferta.get("unidade"), ""))


def dias_uteis_depois(d, n):
    """Data n dias úteis depois de d (sábado e domingo não contam)."""
    atual = d
    while n > 0:
        atual += timedelta(days=1)
        if atual.isoweekday() <= 5:
            n -= 1
    return atual


def aba_valido(numero):
    """Routing number ABA: 9 dígitos com dígito verificador (pesos 3, 7, 1)."""
    d = _digitos(numero)
    if len(d) != 9 or d == "000000000" or d != str(numero or "").strip().replace(" ", "").replace("-", ""):
        return False
    n = [int(x) for x in d]
    soma = 3 * (n[0] + n[3] + n[6]) + 7 * (n[1] + n[4] + n[7]) + (n[2] + n[5] + n[8])
    return soma % 10 == 0


def mascarar(valor, campo=""):
    v = str(valor or "")
    if not v:
        return ""
    if campo == "nascimento":
        return "••/••/••••"
    f = _formularios()
    if campo == "ssn" and f is not None and hasattr(f, "mascarar_ssn"):
        try:
            return f.mascarar_ssn(v)
        except Exception:  # noqa: BLE001
            pass
    alnum = re.sub(r"[^0-9A-Za-z]", "", v)
    return "•••" + alnum[-4:] if len(alnum) > 4 else "•••"


# ------------------------------------------------------------- criptografia

def caminho_chave():
    return os.path.join(srv.BASE_DIR, NOME_ARQUIVO_CHAVE)


def _cripto():
    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError:
        raise ErroChave("Biblioteca de criptografia não instalada no servidor (python3-cryptography)")
    return Fernet, InvalidToken


def existem_dados_cifrados(conn):
    return bool(
        conn.execute("SELECT 1 FROM onboardings WHERE sensiveis!='' LIMIT 1").fetchone()
        or conn.execute("SELECT 1 FROM onboarding_docs WHERE arquivo!='' OR dados_cifrados!='' LIMIT 1").fetchone()
        or srv.config_get(conn, "onboarding_chave_verificador"))


def esquecer_chave():
    """Limpa a chave em memória (testes ou troca do arquivo)."""
    global _fernet
    with _trava_chave:
        _fernet = None


def fernet(conn):
    """Fernet com a chave do ambiente ou do arquivo. Nunca cria uma chave nova
    quando já existem dados cifrados (eles ficariam ilegíveis)."""
    global _fernet
    with _trava_chave:
        if _fernet is not None:
            return _fernet
        Fernet, InvalidToken = _cripto()
        chave = (os.environ.get(CHAVE_ENV) or "").strip().encode()
        if not chave:
            caminho = caminho_chave()
            if os.path.isfile(caminho):
                with open(caminho, "rb") as f:
                    chave = f.read().strip()
            else:
                if existem_dados_cifrados(conn):
                    raise ErroChave("A chave de criptografia dos dados não foi encontrada. Restaure o arquivo "
                                    "chave_dados.key (ou a variável BUSSOLA_CHAVE_DADOS); uma chave nova deixaria "
                                    "os dados já cifrados ilegíveis.")
                chave = Fernet.generate_key()
                fd = os.open(caminho, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as f:
                    f.write(chave + b"\n")
        try:
            f = Fernet(chave)
        except (ValueError, TypeError):
            raise ErroChave("A chave de criptografia dos dados é inválida")
        verificador = srv.config_get(conn, "onboarding_chave_verificador")
        if verificador:
            try:
                f.decrypt(verificador.encode())
            except InvalidToken:
                raise ErroChave("A chave de criptografia dos dados não confere com a usada antes. Restaure o "
                                "arquivo chave_dados.key original.")
        else:
            srv.config_set(conn, "onboarding_chave_verificador", f.encrypt(b"bussola").decode())
            conn.commit()
        _fernet = f
        return f


def cifrar_dict(conn, dados):
    if not dados:
        return ""
    return fernet(conn).encrypt(json.dumps(dados, ensure_ascii=False).encode("utf-8")).decode()


def decifrar_dict(conn, texto):
    if not texto:
        return {}
    _, InvalidToken = _cripto()
    try:
        return json.loads(fernet(conn).decrypt(texto.encode()).decode("utf-8"))
    except InvalidToken:
        raise ErroChave("A chave de criptografia dos dados não confere com a usada antes. Restaure o "
                        "arquivo chave_dados.key original.")


def sensiveis(conn, ob):
    return decifrar_dict(conn, ob["sensiveis"])


def salvar_sensiveis(conn, ob_id, novos):
    """Mescla novos valores sensíveis (vazio apaga o campo)."""
    atual = sensiveis(conn, conn.execute("SELECT sensiveis FROM onboardings WHERE id=?", (ob_id,)).fetchone())
    for k, v in novos.items():
        if v:
            atual[k] = v
        else:
            atual.pop(k, None)
    conn.execute("UPDATE onboardings SET sensiveis=?, atualizado_em=datetime('now') WHERE id=?",
                 (cifrar_dict(conn, atual), ob_id))


# ------------------------------------------------------------- arquivos (sempre cifrados)

def pasta(ob_id):
    p = os.path.join(srv.UPLOAD_DIR, "onboarding", str(int(ob_id)))
    os.makedirs(p, exist_ok=True)
    return p


def gravar_arquivo(conn, ob_id, dados):
    nome = "%s.bin" % secrets.token_hex(16)
    with open(os.path.join(pasta(ob_id), nome), "wb") as f:
        f.write(fernet(conn).encrypt(dados))
    return "onboarding/%d/%s" % (int(ob_id), nome)


def ler_arquivo(conn, rel):
    caminho = os.path.normpath(os.path.join(srv.UPLOAD_DIR, rel or ""))
    base = os.path.normpath(os.path.join(srv.UPLOAD_DIR, "onboarding"))
    if not rel or not caminho.startswith(base + os.sep) or not os.path.isfile(caminho):
        return None
    with open(caminho, "rb") as f:
        bruto = f.read()
    _, InvalidToken = _cripto()
    try:
        return fernet(conn).decrypt(bruto)
    except InvalidToken:
        raise ErroChave("A chave de criptografia dos dados não confere com a usada antes. Restaure o "
                        "arquivo chave_dados.key original.")


def apagar_arquivo(rel):
    caminho = os.path.normpath(os.path.join(srv.UPLOAD_DIR, rel or ""))
    base = os.path.normpath(os.path.join(srv.UPLOAD_DIR, "onboarding"))
    if rel and caminho.startswith(base + os.sep):
        try:
            os.remove(caminho)
        except OSError:
            pass


def tipo_do_arquivo(dados):
    """MIME pelo conteúdo (não pelo nome): JPEG, PNG, PDF ou HEIC/HEIF."""
    if dados.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpg"
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if dados.startswith(b"%PDF-"):
        return "application/pdf", "pdf"
    if len(dados) > 12 and dados[4:8] == b"ftyp" and dados[8:12] in (
            b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1", b"heim", b"heis"):
        return "image/heic", "heic"
    return None, None


# ------------------------------------------------------------- configuração

def _chave_cfg(empresa_id):
    return "onboarding:%d" % int(empresa_id)


def _empresa_de_ct(conn, empresa_id):
    e = conn.execute("SELECT nome FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    return bool(e and re.search(r"\bCT\b|Connecticut", e["nome"] or ""))


def config(conn, empresa_id):
    cfg = json.loads(json.dumps(PADRAO_CFG))
    salvo = _json(srv.config_get(conn, _chave_cfg(empresa_id)), {})
    if isinstance(salvo, dict):
        cfg.update({k: v for k, v in salvo.items() if k in PADRAO_CFG})
    if cfg.get("estaduais") is None:
        cfg["estaduais"] = ["ctw4"] if _empresa_de_ct(conn, empresa_id) else []
    ordem = [e for e in cfg["ordem"] if e in ETAPAS and e != "revisao"]
    for e in PADRAO_CFG["ordem"]:
        if e not in ordem:
            ordem.append(e)
    cfg["ordem"] = ordem
    return cfg


def validar_config(d, atual):
    cfg = dict(atual)
    if "ordem" in d:
        ordem = [str(x) for x in (d.get("ordem") or [])]
        if sorted(ordem) != sorted(PADRAO_CFG["ordem"]):
            return None, "Ordem das etapas inválida"
        cfg["ordem"] = ordem
    if "metodos" in d:
        metodos = [m for m in (d.get("metodos") or []) if m in METODOS]
        if not metodos:
            return None, "Escolha ao menos uma forma de pagamento"
        cfg["metodos"] = [m for m in METODOS if m in metodos]
    if "estaduais" in d:
        cfg["estaduais"] = [f for f in FORMULARIOS_ESTADUAIS if f in (d.get("estaduais") or [])]
    for campo, minimo, maximo in (("prazo_dias", 1, 90), ("lembrete_dias", 0, 30), ("retencao_dias", 0, 3650),
                                  ("periodo_experiencia", 0, 365)):
        if campo in d:
            try:
                v = int(d.get(campo) or 0)
            except (TypeError, ValueError):
                return None, "Valor inválido nas configurações do onboarding"
            if v < minimo or v > maximo:
                return None, "Valor inválido nas configurações do onboarding"
            cfg[campo] = v
    if "provedor_nome" in d:
        cfg["provedor_nome"] = _limpo(d.get("provedor_nome"), 60) or "Gusto"
    for campo in CAMPOS_EMPREGADOR_CFG:
        if campo in d:
            cfg[campo] = _limpo(d.get(campo), 160)
    if cfg.get("empregador_ein"):
        ein = _digitos(cfg["empregador_ein"])
        if len(ein) != 9:
            return None, "EIN inválido (9 dígitos)"
        cfg["empregador_ein"] = ein[:2] + "-" + ein[2:]
    return cfg, None


def salvar_config(conn, empresa_id, cfg):
    srv.config_set(conn, _chave_cfg(empresa_id), json.dumps(cfg, ensure_ascii=False))
    conn.commit()


# ------------------------------------------------------------- modelos (templates)

def _semear(conn, empresa_id):
    """Modelos padrão da empresa, uma única vez (apagar um modelo não o recria)."""
    marca = "onboarding_semeado:%d" % int(empresa_id)
    if srv.config_get(conn, marca):
        return
    for ordem, m in enumerate(MODELOS_PADRAO):
        conn.execute(
            "INSERT INTO onboarding_templates (empresa_id, chave, categoria, titulos, tipo, textos, aplica, ordem,"
            " requer_declaracao, ativo) VALUES (?,?,?,?,?,?,?,?,?,1)",
            (empresa_id, m["chave"], m["categoria"], json.dumps(m["titulos"], ensure_ascii=False), "texto",
             json.dumps(m["textos"], ensure_ascii=False), m["aplica"], (ordem + 1) * 10, 1 if m.get("declaracao") else 0))
    srv.config_set(conn, marca, "1")
    conn.commit()


def modelos(conn, empresa_id, so_ativos=False):
    _semear(conn, empresa_id)
    sql = "SELECT * FROM onboarding_templates WHERE empresa_id=?" + (" AND ativo=1" if so_ativos else "")
    return conn.execute(sql + " ORDER BY ordem, id", (empresa_id,)).fetchall()


def modelo(conn, empresa_id, tid):
    return conn.execute("SELECT * FROM onboarding_templates WHERE id=? AND empresa_id=?",
                        (tid, empresa_id)).fetchone()


def aplica(m, tipo):
    return m["aplica"] in ("ambos", tipo)


def modelo_publico(m):
    return {"id": m["id"], "chave": m["chave"], "categoria": m["categoria"], "titulos": _json(m["titulos"], {}),
            "tipo": m["tipo"], "textos": _json(m["textos"], {}), "aplica": m["aplica"], "ordem": m["ordem"],
            "requer_declaracao": bool(m["requer_declaracao"]), "ativo": bool(m["ativo"]),
            "tem_pdf": bool(m["arquivo"])}


def titulo_modelo(m, lang):
    t = _json(m["titulos"], {})
    return t.get(idioma(lang)) or t.get("en") or t.get("pt") or ""


def salvar_modelo(conn, empresa_id, d, atual=None):
    titulos = d.get("titulos") if isinstance(d.get("titulos"), dict) else {}
    titulos = {k: _limpo(titulos.get(k), 150) for k in ("en", "pt", "es") if _limpo(titulos.get(k), 150)}
    if not titulos:
        raise ErroOnboarding(400, "Informe o título do documento")
    textos = d.get("textos") if isinstance(d.get("textos"), dict) else {}
    textos = {k: str(textos.get(k) or "").replace("\r\n", "\n")[:60000] for k in ("en", "pt", "es")
              if str(textos.get(k) or "").strip()}
    tipo = d.get("tipo") if d.get("tipo") in ("texto", "pdf") else "texto"
    categoria = d.get("categoria") if d.get("categoria") in ("oferta", "documento") else "documento"
    aplica_v = d.get("aplica") if d.get("aplica") in ("w2", "1099", "ambos") else "ambos"
    try:
        ordem = int(d.get("ordem") or 0)
    except (TypeError, ValueError):
        ordem = 0
    arquivo = atual["arquivo"] if atual else ""
    if d.get("pdf"):
        try:
            bruto = base64.b64decode(str(d["pdf"]).split(",")[-1])
        except ValueError:
            raise ErroOnboarding(400, "Arquivo inválido")
        if not bruto.startswith(b"%PDF-") or len(bruto) > 8 * 1024 * 1024:
            raise ErroOnboarding(400, "Envie um PDF de até 8 MB")
        p = os.path.join(srv.UPLOAD_DIR, "onboarding", "modelos")
        os.makedirs(p, exist_ok=True)
        nome = "empresa%d-%s.pdf" % (int(empresa_id), secrets.token_hex(8))
        with open(os.path.join(p, nome), "wb") as f:
            f.write(bruto)
        if arquivo:
            apagar_modelo_pdf(arquivo)
        arquivo = "onboarding/modelos/" + nome
    if tipo == "texto" and not textos.get("en") and not textos:
        raise ErroOnboarding(400, "Escreva o texto do documento")
    if tipo == "pdf" and not arquivo:
        raise ErroOnboarding(400, "Envie um PDF de até 8 MB")
    valores = (categoria, json.dumps(titulos, ensure_ascii=False), tipo, json.dumps(textos, ensure_ascii=False),
               arquivo, aplica_v, ordem, 1 if d.get("requer_declaracao") else 0, 0 if d.get("ativo") is False else 1)
    if atual:
        conn.execute("UPDATE onboarding_templates SET categoria=?, titulos=?, tipo=?, textos=?, arquivo=?, aplica=?,"
                     " ordem=?, requer_declaracao=?, ativo=?, atualizado_em=datetime('now') WHERE id=? AND empresa_id=?",
                     valores + (atual["id"], empresa_id))
        tid = atual["id"]
    else:
        tid = conn.execute("INSERT INTO onboarding_templates (categoria, titulos, tipo, textos, arquivo, aplica, ordem,"
                           " requer_declaracao, ativo, empresa_id, chave) VALUES (?,?,?,?,?,?,?,?,?,?,'')",
                           valores + (empresa_id,)).lastrowid
    conn.commit()
    return tid


def apagar_modelo_pdf(rel):
    caminho = os.path.normpath(os.path.join(srv.UPLOAD_DIR, rel or ""))
    base = os.path.normpath(os.path.join(srv.UPLOAD_DIR, "onboarding", "modelos"))
    if rel and caminho.startswith(base + os.sep):
        try:
            os.remove(caminho)
        except OSError:
            pass


def ler_modelo_pdf(rel):
    caminho = os.path.normpath(os.path.join(srv.UPLOAD_DIR, rel or ""))
    base = os.path.normpath(os.path.join(srv.UPLOAD_DIR, "onboarding", "modelos"))
    if not rel or not caminho.startswith(base + os.sep) or not os.path.isfile(caminho):
        return None
    with open(caminho, "rb") as f:
        return f.read()


# ------------------------------------------------------------- variáveis dos documentos

def variaveis(conn, ob, lang):
    oferta = _json(ob["oferta"], {})
    dados = _json(ob["dados"], {})
    cand = conn.execute("SELECT nome FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    m = srv.mensagens.marca(conn, ob["empresa_id"]) or {}
    return {
        "nome": dados.get("nome_legal") or (cand["nome"] if cand else ""),
        "empresa": m.get("nome") or "",
        "cargo": oferta.get("cargo") or "",
        "data_inicio": data_extenso(oferta.get("data_inicio"), lang),
        "pagamento": texto_pagamento(oferta, lang),
        "horario": oferta.get("horario") or "",
        "periodo_experiencia": str(oferta.get("periodo_experiencia") or 90),
        "prazo": data_extenso(ob["prazo"], lang),
        "representante": oferta.get("representante") or "",
        "data": data_extenso(_hoje(), lang),
    }


def preencher(texto, vars_):
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: str(vars_.get(m.group(1), "")), texto or "")


def textos_preenchidos(conn, ob, m):
    """{lang: texto} das versões que o modelo tem, com as variáveis."""
    textos = _json(m["textos"], {})
    return {lang: preencher(txt, variaveis(conn, ob, lang)) for lang, txt in textos.items() if lang in ("en", "pt", "es")}


# ------------------------------------------------------------- consultas

def onboarding_do_token(conn, token):
    token = (token or "").strip()
    if len(token) < 24 or not re.match(r"^[A-Za-z0-9_-]+$", token):
        return None
    return conn.execute(
        "SELECT o.* FROM onboardings o JOIN empresas e ON e.id=o.empresa_id JOIN candidatos c ON c.id=o.candidato_id"
        " WHERE o.token=? AND e.status IN ('ativa','teste') AND c.empresa_id=o.empresa_id", (token,)).fetchone()


def recarregar(conn, ob_id):
    return conn.execute("SELECT * FROM onboardings WHERE id=?", (ob_id,)).fetchone()


def docs(conn, ob_id, tipo=None, chave=None, ativos=True):
    sql = "SELECT * FROM onboarding_docs WHERE onboarding_id=?"
    p = [ob_id]
    if ativos:
        sql += " AND ativo=1"
    if tipo:
        sql += " AND tipo=?"
        p.append(tipo)
    if chave:
        sql += " AND chave=?"
        p.append(chave)
    return conn.execute(sql + " ORDER BY id", p).fetchall()


def ativo_do_candidato(conn, cand_id):
    return conn.execute("SELECT * FROM onboardings WHERE candidato_id=? AND status IN ('enviado','em_andamento')",
                        (cand_id,)).fetchone()


# ------------------------------------------------------------- plano e progresso

def plano(conn, ob):
    """O que este onboarding pede: modelo da proposta, documentos, formulários,
    categorias de envio e formas de pagamento."""
    oferta = _json(ob["oferta"], {})
    cfg = config(conn, ob["empresa_id"])
    tipo = ob["tipo"]
    oferta_tpl = modelo(conn, ob["empresa_id"], oferta.get("modelo_oferta")) if oferta.get("modelo_oferta") else None
    docs_ids = [int(x) for x in (oferta.get("documentos") or []) if str(x).isdigit()]
    documentos = []
    for tid in docs_ids:
        m = modelo(conn, ob["empresa_id"], tid)
        if m and m["categoria"] == "documento":
            documentos.append(m)
    formularios_ = [f for f in (oferta.get("formularios") or []) if f in ("w4", "i9", "w9") + FORMULARIOS_ESTADUAIS]
    dirige = bool(oferta.get("dirige"))
    categorias = [{"chave": "id_frente", "obrigatorio": True}, {"chave": "id_verso", "obrigatorio": False}]
    if dirige:
        categorias += [{"chave": "cnh_frente", "obrigatorio": True}, {"chave": "cnh_verso", "obrigatorio": False}]
    if "i9" in formularios_:
        categorias += [{"chave": "i9_lista_a", "obrigatorio": False, "grupo": "i9"},
                       {"chave": "i9_lista_b", "obrigatorio": False, "grupo": "i9"},
                       {"chave": "i9_lista_c", "obrigatorio": False, "grupo": "i9"}]
    categorias.append({"chave": "comprovante_endereco", "obrigatorio": False})
    metodos = [m for m in (oferta.get("metodos") or cfg["metodos"]) if m in METODOS] or ["cheque"]
    etapas = []
    for e in cfg["ordem"]:
        if e == "oferta" and not oferta_tpl:
            continue
        if e == "documentos" and not documentos:
            continue
        if e == "formularios" and not formularios_:
            continue
        etapas.append(e)
    etapas.append("revisao")
    return {"tipo": tipo, "oferta": oferta, "cfg": cfg, "modelo_oferta": oferta_tpl, "documentos": documentos,
            "formularios": formularios_, "categorias": categorias, "metodos": metodos, "dirige": dirige,
            "etapas": etapas}


CAMPOS_DADOS_OBRIGATORIOS = ("nome_legal", "endereco", "cidade", "estado", "cep", "telefone", "email",
                             "contato_nome", "contato_relacao", "contato_telefone")


def dados_completos(ob, sens, dirige):
    d = _json(ob["dados"], {})
    if any(not str(d.get(k) or "").strip() for k in CAMPOS_DADOS_OBRIGATORIOS):
        return False
    if not sens.get("nascimento"):
        return False
    if dirige and (not sens.get("cnh_numero") or not d.get("cnh_estado")):
        return False
    return True


def pagamento_completo(ob, sens, metodos):
    p = _json(ob["pagamento"], {})
    metodo = p.get("metodo")
    if metodo not in metodos:
        return False
    if metodo == "deposito":
        return bool(sens.get("routing") and sens.get("conta") and p.get("banco") and p.get("tipo_conta"))
    if metodo == "zelle":
        return bool(p.get("zelle"))
    if metodo == "cheque":
        return bool(p.get("endereco_confirmado"))
    return bool(p.get("provedor_ciente"))


def arquivos_completos(lista_docs, pl):
    tem = {d["chave"] for d in lista_docs}
    for c in pl["categorias"]:
        if c["obrigatorio"] and c["chave"] not in tem:
            return False
    if "i9" in pl["formularios"]:
        if not ("i9_lista_a" in tem or ("i9_lista_b" in tem and "i9_lista_c" in tem)):
            return False
    return True


def progresso(conn, ob, pl=None, sens=None):
    pl = pl or plano(conn, ob)
    if sens is None:
        sens = sensiveis(conn, ob) if ob["sensiveis"] else {}
    todos = docs(conn, ob["id"])
    assinados = {d["chave"] for d in todos if d["tipo"] == "assinatura"}
    forms = {d["chave"] for d in todos if d["tipo"] == "formulario"}
    feito = {}
    for e in pl["etapas"]:
        if e == "oferta":
            feito[e] = "tpl:%d" % pl["modelo_oferta"]["id"] in assinados
        elif e == "dados":
            feito[e] = dados_completos(ob, sens, pl["dirige"])
        elif e == "documentos":
            feito[e] = all("tpl:%d" % m["id"] in assinados for m in pl["documentos"])
        elif e == "formularios":
            feito[e] = all(f in forms for f in pl["formularios"])
        elif e == "arquivos":
            feito[e] = arquivos_completos([d for d in todos if d["tipo"] == "arquivo"], pl)
        elif e == "pagamento":
            feito[e] = pagamento_completo(ob, sens, pl["metodos"])
        elif e == "revisao":
            feito[e] = ob["status"] == "concluido"
    n = len(pl["etapas"])
    pct = int(round(100.0 * sum(1 for v in feito.values() if v) / n)) if n else 0
    return {"etapas": [{"chave": e, "feito": bool(feito.get(e))} for e in pl["etapas"]], "pct": pct,
            "pendentes": [e for e in pl["etapas"] if not feito.get(e) and e != "revisao"]}


def i9_prazo(ob):
    """Seção 2 do I-9: até 3 dias úteis depois do primeiro dia de trabalho."""
    oferta = _json(ob["oferta"], {})
    inicio = _data(oferta.get("data_inicio"))
    if ob["tipo"] != "w2" or "i9" not in (oferta.get("formularios") or []) or not inicio:
        return None
    return dias_uteis_depois(inicio, 3)


# ------------------------------------------------------------- textos (e-mails)

T = {
    "pt": {
        "etapas": {"oferta": "Carta de proposta", "dados": "Dados pessoais", "documentos": "Documentos para assinar",
                   "formularios": "Formulários fiscais", "arquivos": "Envio de documentos",
                   "pagamento": "Forma de pagamento", "revisao": "Revisão e envio"},
        "of_assunto": "{empresa}: sua proposta de trabalho e o onboarding",
        "of_titulo": "Bem-vindo(a) à equipe!",
        "of_corpo": "Olá, {nome}! A {empresa} tem o prazer de oferecer a você a vaga de {cargo}. Para aceitar e concluir o seu onboarding, use o botão abaixo.",
        "of_detalhes": "Início: {inicio} · Pagamento: {pagamento}",
        "of_prazo": "Conclua tudo até {prazo}. Pelo celular leva cerca de 20 minutos. Tenha à mão um documento com foto, o seu número de Seguro Social (SSN) e os dados bancários, se escolher depósito.",
        "of_botao": "Começar o onboarding",
        "lem_assunto": "Lembrete: falta pouco para concluir o seu onboarding",
        "lem_titulo": "Falta pouco",
        "lem_corpo": "Olá, {nome}! Ainda faltam algumas etapas do seu onboarding na {empresa}:",
        "lem_prazo": "Prazo: {prazo}.",
        "lem_botao": "Continuar o onboarding",
        "fim_assunto": "Onboarding concluído: {nome}",
        "fim_corpo": "{nome} concluiu o onboarding ({cargo}, início em {inicio}). Os documentos assinados e os formulários estão na ficha.",
        "fim_i9": "Lembrete: a Seção 2 do Formulário I-9 deve ser preenchida até {prazo}, com a conferência dos documentos originais.",
        "fim_botao": "Abrir a ficha",
        "fim_cand_assunto": "Onboarding concluído. Obrigado!",
        "fim_cand_corpo": "Olá, {nome}! Recebemos tudo. A equipe da {empresa} vai entrar em contato com os próximos passos. Você pode baixar cópias dos documentos assinados pelo mesmo link.",
        "assinatura": "Até breve,\nEquipe {empresa}",
    },
    "en": {
        "etapas": {"oferta": "Offer letter", "dados": "Personal info", "documentos": "Documents to sign",
                   "formularios": "Tax forms", "arquivos": "Document uploads", "pagamento": "Payment setup",
                   "revisao": "Review and submit"},
        "of_assunto": "{empresa}: your job offer and onboarding",
        "of_titulo": "Welcome to the team!",
        "of_corpo": "Hi {nome}! {empresa} is happy to offer you the {cargo} position. To accept and complete your onboarding, use the button below.",
        "of_detalhes": "Start date: {inicio} · Pay: {pagamento}",
        "of_prazo": "Please finish by {prazo}. It takes about 20 minutes on your phone. Have a photo ID, your Social Security number, and your bank details (if you choose direct deposit) ready.",
        "of_botao": "Start onboarding",
        "lem_assunto": "Reminder: you're almost done with your onboarding",
        "lem_titulo": "Almost there",
        "lem_corpo": "Hi {nome}! A few onboarding steps with {empresa} are still open:",
        "lem_prazo": "Deadline: {prazo}.",
        "lem_botao": "Continue onboarding",
        "fim_assunto": "Onboarding complete: {nome}",
        "fim_corpo": "{nome} finished onboarding ({cargo}, starting {inicio}). The signed documents and forms are in the profile.",
        "fim_i9": "Reminder: Form I-9 Section 2 is due by {prazo}, after you examine the original documents.",
        "fim_botao": "Open profile",
        "fim_cand_assunto": "Onboarding complete. Thank you!",
        "fim_cand_corpo": "Hi {nome}! We received everything. The {empresa} team will reach out with next steps. You can download copies of your signed documents with the same link.",
        "assinatura": "See you soon,\nThe {empresa} team",
    },
    "es": {
        "etapas": {"oferta": "Carta de oferta", "dados": "Datos personales", "documentos": "Documentos para firmar",
                   "formularios": "Formularios de impuestos", "arquivos": "Envío de documentos",
                   "pagamento": "Forma de pago", "revisao": "Revisión y envío"},
        "of_assunto": "{empresa}: tu oferta de trabajo y la incorporación",
        "of_titulo": "¡Bienvenido(a) al equipo!",
        "of_corpo": "¡Hola, {nome}! {empresa} tiene el gusto de ofrecerte el puesto de {cargo}. Para aceptar y completar tu incorporación, usa el botón de abajo.",
        "of_detalhes": "Inicio: {inicio} · Pago: {pagamento}",
        "of_prazo": "Termina todo antes del {prazo}. Desde el celular toma unos 20 minutos. Ten a mano una identificación con foto, tu número de Seguro Social (SSN) y tus datos bancarios si eliges depósito directo.",
        "of_botao": "Comenzar la incorporación",
        "lem_assunto": "Recordatorio: te falta poco para terminar tu incorporación",
        "lem_titulo": "Te falta poco",
        "lem_corpo": "¡Hola, {nome}! Todavía tienes pasos pendientes de tu incorporación en {empresa}:",
        "lem_prazo": "Fecha límite: {prazo}.",
        "lem_botao": "Continuar la incorporación",
        "fim_assunto": "Incorporación completa: {nome}",
        "fim_corpo": "{nome} completó la incorporación ({cargo}, inicio el {inicio}). Los documentos firmados y los formularios están en la ficha.",
        "fim_i9": "Recordatorio: la Sección 2 del Formulario I-9 vence el {prazo}, después de revisar los documentos originales.",
        "fim_botao": "Abrir la ficha",
        "fim_cand_assunto": "Incorporación completa. ¡Gracias!",
        "fim_cand_corpo": "¡Hola, {nome}! Recibimos todo. El equipo de {empresa} se comunicará contigo con los próximos pasos. Puedes descargar copias de tus documentos firmados con el mismo enlace.",
        "assinatura": "Hasta pronto,\nEquipo {empresa}",
    },
}

CONSENTIMENTO = {
    "en": ("Consent to electronic records and signatures. By checking the box below, you agree that {empresa} may "
           "provide documents, notices, and disclosures to you electronically, and that you will sign documents "
           "electronically in this portal. Your electronic signature has the same legal effect as a handwritten "
           "signature under the federal ESIGN Act and the Uniform Electronic Transactions Act (UETA). You may ask "
           "{empresa} for a paper copy of any document at no cost, and you may withdraw this consent before signing "
           "by contacting {empresa}; withdrawing does not affect documents you already signed. To use this portal "
           "you need a device with an up-to-date web browser that can open PDF files. You can download a copy of "
           "every document you sign."),
    "pt": ("Consentimento para documentos e assinaturas eletrônicas. Ao marcar a caixa abaixo, você concorda que a "
           "{empresa} entregue documentos, avisos e comunicados a você por meio eletrônico e que você assine "
           "documentos eletronicamente neste portal. A sua assinatura eletrônica tem o mesmo efeito legal de uma "
           "assinatura à mão, nos termos da lei federal ESIGN e da Uniform Electronic Transactions Act (UETA). Você "
           "pode pedir à {empresa} uma cópia em papel de qualquer documento sem custo e pode retirar este "
           "consentimento antes de assinar, falando com a {empresa}; a retirada não afeta documentos já assinados. "
           "Para usar este portal você precisa de um aparelho com navegador atualizado que abra arquivos PDF. Você "
           "pode baixar uma cópia de cada documento que assinar."),
    "es": ("Consentimiento para documentos y firmas electrónicas. Al marcar la casilla de abajo, aceptas que "
           "{empresa} te entregue documentos, avisos y comunicaciones por medios electrónicos y que firmes "
           "documentos electrónicamente en este portal. Tu firma electrónica tiene el mismo efecto legal que una "
           "firma a mano, según la ley federal ESIGN y la Uniform Electronic Transactions Act (UETA). Puedes pedir a "
           "{empresa} una copia en papel de cualquier documento sin costo y puedes retirar este consentimiento antes "
           "de firmar, comunicándote con {empresa}; retirarlo no afecta los documentos ya firmados. Para usar este "
           "portal necesitas un dispositivo con un navegador actualizado que abra archivos PDF. Puedes descargar una "
           "copia de cada documento que firmes."),
}

ACEITE_ASSINATURA = {
    "en": "I have read this document and I agree to sign it electronically.",
    "pt": "Li este documento e concordo em assiná-lo eletronicamente.",
    "es": "Leí este documento y acepto firmarlo electrónicamente.",
}


def t(lang, chave, **kw):
    texto = T[idioma(lang)].get(chave)
    if texto is None:
        texto = T["pt"][chave]
    return texto.format(**kw) if kw and isinstance(texto, str) else texto


def texto_consentimento(empresa, lang):
    return CONSENTIMENTO[idioma(lang)].format(empresa=empresa or "the company")


# ------------------------------------------------------------- PDF de assinatura

def _pdf():
    try:
        from fpdf import FPDF
    except ImportError:
        raise ErroOnboarding(500, "Biblioteca de PDF não instalada no servidor (pip3 install fpdf2)")
    fontes = srv.FONTS_PDF_DIR
    if not os.path.isfile(os.path.join(fontes, "JustSans-Regular.ttf")):
        raise ErroOnboarding(500, "Fontes do PDF não encontradas no servidor")
    pdf = FPDF(format="Letter")
    pdf.set_margins(20, 18, 20)
    pdf.set_auto_page_break(True, margin=18)
    pdf.add_font("Just", "", os.path.join(fontes, "JustSans-Regular.ttf"))
    pdf.add_font("Just", "B", os.path.join(fontes, "JustSans-Bold.ttf"))
    pdf.add_font("Gab", "B", os.path.join(fontes, "Gabarito-Bold.ttf"))
    return pdf


def _texto_pdf(v):
    """Só caracteres que as fontes do PDF desenham (troca o que não for Latin-1)."""
    s = str(v or "").replace("•", "-").replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"').replace(" ", " ")
    return "".join(ch if ord(ch) < 256 else "?" for ch in s)


def _linha_pdf(pdf, texto, tam=10.5, negrito=False, cor=(30, 38, 52), altura=5.2, recuo=0):
    pdf.set_font("Just", "B" if negrito else "", tam)
    pdf.set_text_color(*cor)
    pdf.set_x(pdf.l_margin + recuo)
    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - recuo, altura, _texto_pdf(texto))
    pdf.set_x(pdf.l_margin)


def _cabecalho_pdf(pdf, conn, empresa_id):
    m = srv.mensagens.marca(conn, empresa_id) or {}
    y = pdf.get_y()
    logo_ok = False
    if m.get("logo"):
        caminho = srv.mensagens.caminho_logo(m["logo"])
        if os.path.isfile(caminho):
            try:
                pdf.image(caminho, x=pdf.l_margin, y=y, h=14, keep_aspect_ratio=True, w=50)
                logo_ok = True
            except Exception:  # noqa: BLE001
                logo_ok = False
    if logo_ok:
        pdf.set_y(y + 17)
    else:
        pdf.set_font("Gab", "B", 15)
        pdf.set_text_color(16, 27, 55)
        pdf.cell(0, 8, _texto_pdf(m.get("nome") or ""))
        pdf.ln(10)
    pdf.set_draw_color(155, 185, 221)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(5)


def _corpo_pdf(pdf, texto):
    for linha in (texto or "").split("\n"):
        s = linha.rstrip()
        if not s.strip():
            pdf.ln(2.4)
        elif s.startswith("# "):
            pdf.ln(1)
            pdf.set_font("Gab", "B", 15)
            pdf.set_text_color(16, 27, 55)
            pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin, 7.5, _texto_pdf(s[2:]))
            pdf.set_x(pdf.l_margin)
            pdf.ln(1)
        elif s.startswith("## "):
            pdf.ln(1.5)
            _linha_pdf(pdf, s[3:], 11.5, True, (16, 27, 55), 6)
        elif s.startswith("- "):
            _linha_pdf(pdf, "-  " + s[2:], 10.3, False, (30, 38, 52), 5.1, 4)
        elif s.startswith("> "):
            _linha_pdf(pdf, s[2:], 9, True, (138, 106, 43), 4.6)
        else:
            _linha_pdf(pdf, s)


def _bloco_assinatura(pdf, assinatura_png, nome, quando_utc, declaracao, lang_rotulos="en"):
    if pdf.get_y() > pdf.h - 80:
        pdf.add_page()
    pdf.ln(6)
    if declaracao:
        _linha_pdf(pdf, "Personal statement", 11, True, (16, 27, 55), 6)
        _linha_pdf(pdf, declaracao, 10.3)
        pdf.ln(4)
    _linha_pdf(pdf, "Signed electronically by", 9, False, (110, 120, 135), 4.6)
    y = pdf.get_y() + 1
    if assinatura_png:
        try:
            pdf.image(io.BytesIO(assinatura_png), x=pdf.l_margin, y=y, h=20, keep_aspect_ratio=True, w=70)
        except Exception:  # noqa: BLE001
            pass
    pdf.set_y(y + 22)
    pdf.set_draw_color(120, 130, 150)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 80, pdf.get_y())
    pdf.ln(1.5)
    _linha_pdf(pdf, nome, 10.5, True)
    _linha_pdf(pdf, "Date (UTC): " + quando_utc.replace("T", " ").replace("Z", ""), 9.5, False, (90, 100, 115))


def _certificado(pdf, linhas, consentimento_txt):
    pdf.add_page()
    pdf.set_font("Gab", "B", 15)
    pdf.set_text_color(16, 27, 55)
    pdf.cell(0, 8, "Electronic Signature Certificate")
    pdf.ln(11)
    largura = pdf.w - pdf.l_margin - pdf.r_margin
    for rotulo, valor in linhas:
        pdf.set_font("Just", "B", 9)
        pdf.set_text_color(110, 120, 135)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(largura, 4.6, _texto_pdf(rotulo))
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Just", "", 10)
        pdf.set_text_color(30, 38, 52)
        pdf.multi_cell(largura, 5, _texto_pdf(valor or "-"))
        pdf.set_x(pdf.l_margin)
        pdf.ln(1.6)
    pdf.ln(2)
    _linha_pdf(pdf, "Electronic records consent shown to the signer", 9, True, (110, 120, 135), 4.6)
    _linha_pdf(pdf, consentimento_txt, 9, False, (60, 70, 85), 4.6)
    pdf.ln(3)
    _linha_pdf(pdf, "The SHA-256 hash identifies the exact document content that was presented and signed. "
                    "This certificate is part of the signed record.", 8.5, False, (110, 120, 135), 4.4)


def gerar_pdf_assinado(conn, ob, cand, titulo, texto, assinatura_png, nome, declaracao, meta, pdf_original=None):
    """(bytes do PDF, sha256 do conteúdo apresentado). meta: email, ip, ua, quando, consentimento, ref."""
    if pdf_original is not None:
        sha_conteudo = hashlib.sha256(pdf_original).hexdigest()
    else:
        sha_conteudo = hashlib.sha256(("%s\n\n%s" % (titulo, texto)).encode("utf-8")).hexdigest()
    pdf = _pdf()
    pdf.add_page()
    _cabecalho_pdf(pdf, conn, ob["empresa_id"])
    if pdf_original is None:
        if not (texto or "").lstrip().startswith("# "):
            _corpo_pdf(pdf, "# " + titulo)
        _corpo_pdf(pdf, texto)
    else:
        _corpo_pdf(pdf, "# " + titulo)
        _linha_pdf(pdf, "Signature page for the attached PDF document. Original document SHA-256: " + sha_conteudo, 9.5)
    _bloco_assinatura(pdf, assinatura_png, nome, meta["quando"], declaracao)
    cons = meta.get("consentimento") or {}
    m = srv.mensagens.marca(conn, ob["empresa_id"]) or {}
    linhas = [
        ("Document", titulo),
        ("Company", m.get("nome") or ""),
        ("Record reference", meta.get("ref") or ""),
        ("Signer (typed name)", nome),
        ("Signer email", meta.get("email") or (cand["email"] if cand else "")),
        ("Signed at (UTC)", meta["quando"]),
        ("IP address", meta.get("ip") or ""),
        ("Device / browser (user agent)", meta.get("ua") or ""),
        ("Document SHA-256", sha_conteudo),
        ("Signature image SHA-256", hashlib.sha256(assinatura_png or b"").hexdigest()),
        ("Signer agreement", meta.get("aceite") or ACEITE_ASSINATURA["en"]),
        ("Electronic records consent given at (UTC)", "%s from IP %s" % (cons.get("em", ""), cons.get("ip", ""))),
        ("Offer issued by", meta.get("emissor") or ""),
    ]
    if declaracao:
        linhas.insert(9, ("Personal statement SHA-256", hashlib.sha256(declaracao.encode("utf-8")).hexdigest()))
    _certificado(pdf, linhas, cons.get("texto") or "")
    saida = bytes(pdf.output())
    if pdf_original is not None:
        try:  # junta o PDF original na frente, quando o pypdf existe
            from pypdf import PdfReader, PdfWriter
            w = PdfWriter()
            for fonte in (pdf_original, saida):
                for pg in PdfReader(io.BytesIO(fonte)).pages:
                    w.add_page(pg)
            buf = io.BytesIO()
            w.write(buf)
            saida = buf.getvalue()
        except Exception:  # noqa: BLE001
            pass
    return saida, sha_conteudo


# ------------------------------------------------------------- criar, enviar, cancelar

def padroes_oferta(conn, gestor, cand):
    cfg = config(conn, gestor["empresa_id"])
    ms = modelos(conn, gestor["empresa_id"], so_ativos=True)
    ca = conn.execute(
        "SELECT ca.id, v.titulo, v.cargo_id FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
        " WHERE ca.candidato_id=? AND v.empresa_id=? AND ca.etapa!='reprovado'"
        " ORDER BY ca.atualizado_em DESC, ca.id DESC LIMIT 1", (cand["id"], gestor["empresa_id"])).fetchone()
    cargo_id = (ca["cargo_id"] if ca else None) or cand["cargo_desejado_id"]
    cargo_nome = ""
    if cargo_id:
        r = conn.execute("SELECT nome FROM cargos WHERE id=? AND empresa_id=?", (cargo_id, gestor["empresa_id"])).fetchone()
        cargo_nome = r["nome"] if r else ""
    return {
        "cargo": (ca["titulo"] if ca else "") or cargo_nome, "cargo_id": cargo_id,
        "candidatura_id": ca["id"] if ca else None,
        "prazo": (_hoje() + timedelta(days=cfg["prazo_dias"])).isoformat(),
        "metodos": cfg["metodos"], "estaduais": cfg["estaduais"], "periodo_experiencia": cfg["periodo_experiencia"],
        "modelos": [dict(modelo_publico(m), textos=None) for m in ms],
        "formularios": {tipo: FORMULARIOS_FEDERAIS[tipo] + (cfg["estaduais"] if tipo == "w2" else []) for tipo in TIPOS},
        "formularios_disponivel": _formularios() is not None,
    }


def validar_oferta(conn, gestor, d):
    tipo = d.get("tipo")
    if tipo not in TIPOS:
        raise ErroOnboarding(400, "Tipo de vínculo inválido")
    cargo = _limpo(d.get("cargo"), 120)
    if not cargo:
        raise ErroOnboarding(400, "Informe o cargo")
    inicio = _data(d.get("data_inicio"))
    if not inicio:
        raise ErroOnboarding(400, "Data de início inválida")
    try:
        valor = round(float(str(d.get("valor") or "").replace("$", "").replace(",", "")), 2)
    except ValueError:
        valor = -1
    if valor <= 0 or valor > 10000000:
        raise ErroOnboarding(400, "Valor do pagamento inválido")
    unidade = d.get("unidade")
    if unidade not in UNIDADES:
        raise ErroOnboarding(400, "Unidade do pagamento inválida")
    prazo = _data(d.get("prazo"))
    if not prazo or prazo < _hoje():
        raise ErroOnboarding(400, "Prazo inválido")
    cfg = config(conn, gestor["empresa_id"])
    metodos = [m for m in (d.get("metodos") or cfg["metodos"]) if m in METODOS]
    if not metodos:
        raise ErroOnboarding(400, "Escolha ao menos uma forma de pagamento")
    ms = {m["id"]: m for m in modelos(conn, gestor["empresa_id"], so_ativos=True)}
    if "documentos" in d:
        docs_ids = []
        for x in d.get("documentos") or []:
            try:
                x = int(x)
            except (TypeError, ValueError):
                continue
            if x in ms and ms[x]["categoria"] == "documento" and aplica(ms[x], tipo):
                docs_ids.append(x)
    else:
        docs_ids = [m["id"] for m in ms.values() if m["categoria"] == "documento" and aplica(m, tipo)]
    oferta_tpl = next((m for m in ms.values() if m["categoria"] == "oferta" and aplica(m, tipo)), None)
    permitidos = FORMULARIOS_FEDERAIS[tipo] + (list(FORMULARIOS_ESTADUAIS) if tipo == "w2" else [])
    if "formularios" in d:
        forms = [f for f in (d.get("formularios") or []) if f in permitidos]
    else:
        forms = FORMULARIOS_FEDERAIS[tipo] + (cfg["estaduais"] if tipo == "w2" else [])
    try:
        experiencia = int(d.get("periodo_experiencia") if d.get("periodo_experiencia") not in (None, "") else cfg["periodo_experiencia"])
    except (TypeError, ValueError):
        experiencia = cfg["periodo_experiencia"]
    cargo_id = d.get("cargo_id")
    if cargo_id and not srv.cargo_do_gestor(conn, gestor, cargo_id):
        cargo_id = None
    return {
        "tipo": tipo, "cargo": cargo, "cargo_id": cargo_id, "data_inicio": inicio.isoformat(), "valor": valor,
        "unidade": unidade, "horario": _limpo(d.get("horario"), 300), "notas": str(d.get("notas") or "").strip()[:2000],
        "documentos": docs_ids, "formularios": forms, "metodos": [m for m in METODOS if m in metodos],
        "dirige": bool(d.get("dirige")), "modelo_oferta": oferta_tpl["id"] if oferta_tpl else None,
        "periodo_experiencia": max(0, min(365, experiencia)), "representante": gestor["nome"],
    }, prazo.isoformat()


def criar(conn, gestor, cand, d, ip=""):
    if ativo_do_candidato(conn, cand["id"]):
        raise ErroOnboarding(409, "Já existe um onboarding em andamento para este candidato")
    if not (cand["email"] or "").strip():
        raise ErroOnboarding(400, "Candidato sem e-mail")
    oferta, prazo = validar_oferta(conn, gestor, d)
    ca_id = d.get("candidatura_id")
    ca = None
    if ca_id:
        ca = conn.execute("SELECT ca.id FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                          " WHERE ca.id=? AND ca.candidato_id=? AND v.empresa_id=?",
                          (ca_id, cand["id"], gestor["empresa_id"])).fetchone()
    if not ca:
        ca = conn.execute("SELECT ca.id FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                          " WHERE ca.candidato_id=? AND v.empresa_id=? AND ca.etapa!='reprovado'"
                          " ORDER BY ca.atualizado_em DESC, ca.id DESC LIMIT 1",
                          (cand["id"], gestor["empresa_id"])).fetchone()
    token = secrets.token_urlsafe(32)
    try:
        ob_id = conn.execute(
            "INSERT INTO onboardings (empresa_id, candidato_id, candidatura_id, token, tipo, oferta, status, prazo,"
            " idioma, criado_por) VALUES (?,?,?,?,?,?,'enviado',?,?,?)",
            (gestor["empresa_id"], cand["id"], ca["id"] if ca else None, token, oferta["tipo"],
             json.dumps(oferta, ensure_ascii=False), prazo, idioma(cand["idioma"] or "en") if cand["idioma"] else "",
             gestor["nome"])).lastrowid
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise ErroOnboarding(409, "Já existe um onboarding em andamento para este candidato")
        raise
    mover_etapa(conn, cand, ca["id"] if ca else None, ("inscrito", "avaliacoes", "entrevista"), "proposta", gestor["nome"])
    srv.registrar_evento(conn, cand["id"], "onboarding", "Proposta e onboarding enviados (%s, %s, início %s)" % (
        "W-2" if oferta["tipo"] == "w2" else "1099", oferta["cargo"], oferta["data_inicio"]), gestor["nome"])
    conn.commit()
    srv.seguranca.registrar(conn, "onboarding_enviado", gestor, "candidato:%d onboarding:%d" % (cand["id"], ob_id), ip)
    ob = recarregar(conn, ob_id)
    ok, msg = enviar_convite(conn, ob)
    return ob, ok, msg


def mover_etapa(conn, cand, candidatura_id, de, para, autor):
    if candidatura_id:
        alvo = conn.execute("SELECT ca.id, ca.etapa, v.titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                            " WHERE ca.id=?", (candidatura_id,)).fetchall()
    else:
        alvo = conn.execute("SELECT ca.id, ca.etapa, v.titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
                            " WHERE ca.candidato_id=? AND v.empresa_id=?", (cand["id"], cand["empresa_id"])).fetchall()
    for ca in alvo:
        if ca["etapa"] in de:
            conn.execute("UPDATE candidaturas SET etapa=?, atualizado_em=datetime('now') WHERE id=?", (para, ca["id"]))
            srv.registrar_evento(conn, cand["id"], "etapa", "Vaga %s: movido para %s" % (
                ca["titulo"], srv.NOMES_ETAPAS.get(para, para)), autor)


def link(conn, ob):
    lang = idioma(ob["idioma"]) if ob["idioma"] else ""
    return "%s/onboarding?t=%s%s" % (srv.url_publica(conn), ob["token"], ("&lang=" + lang) if lang else "")


def _lang_ob(conn, ob):
    if ob["idioma"]:
        return idioma(ob["idioma"])
    cand = conn.execute("SELECT idioma FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    return idioma(cand["idioma"] if cand and cand["idioma"] else "en")


def email_convite(conn, ob):
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    lang = _lang_ob(conn, ob)
    m = srv.mensagens
    marca = m.marca(conn, ob["empresa_id"])
    empresa = (marca or {}).get("nome") or ""
    oferta = _json(ob["oferta"], {})
    primeiro = (cand["nome"] or "").split(" ")[0]
    url = link(conn, ob)
    corpo_txt = t(lang, "of_corpo", nome=primeiro, empresa=empresa, cargo=oferta.get("cargo", ""))
    detalhes = t(lang, "of_detalhes", inicio=data_extenso(oferta.get("data_inicio"), lang),
                 pagamento=texto_pagamento(oferta, lang))
    prazo = t(lang, "of_prazo", prazo=data_extenso(ob["prazo"], lang))
    assinatura = t(lang, "assinatura", empresa=empresa)
    html = m.layout(
        m._paragrafo(corpo_txt) + m._paragrafo(detalhes, "#101B37", 14) + m._botao(url, t(lang, "of_botao"), "#2E9E6A")
        + m._paragrafo(prazo, "#4a5568", 14) + m._paragrafo(assinatura, "#4a5568", 14),
        lang, marca, ("🎉", t(lang, "of_titulo"), "#2E9E6A"))
    texto = "\n".join([corpo_txt, "", detalhes, "", url, "", prazo, "", assinatura])
    return t(lang, "of_assunto", empresa=empresa), texto, html


def enviar_convite(conn, ob, autor="sistema"):
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    if not cand or not (cand["email"] or "").strip():
        return False, "Candidato sem e-mail"
    assunto, texto, html = email_convite(conn, ob)
    ok, msg = srv.enviar_email(conn, cand["email"].strip(), assunto, texto, html=html)
    srv.registrar_evento(conn, cand["id"], "email", "E-mail da proposta e do onboarding %s (%s)" % (
        "enviado" if ok else "não enviado", _lang_ob(conn, ob)), autor)
    conn.commit()
    return ok, msg


def cancelar(conn, ob, gestor, ip=""):
    if ob["status"] not in ATIVOS:
        raise ErroOnboarding(400, "Este onboarding não está mais em andamento")
    conn.execute("UPDATE onboardings SET status='cancelado', cancelado_em=datetime('now'), atualizado_em=datetime('now')"
                 " WHERE id=?", (ob["id"],))
    srv.registrar_evento(conn, ob["candidato_id"], "onboarding", "Onboarding cancelado", gestor["nome"])
    conn.commit()
    srv.seguranca.registrar(conn, "onboarding_cancelado", gestor, "onboarding:%d" % ob["id"], ip)


# ------------------------------------------------------------- ações do portal

def _exigir_ativo(ob):
    if ob["status"] == "cancelado":
        raise ErroOnboarding(410, "Este onboarding foi cancelado")
    if ob["status"] == "concluido":
        raise ErroOnboarding(400, "Este onboarding já foi concluído")


def _exigir_consentimento(ob):
    _exigir_ativo(ob)
    if not ob["consentimento"]:
        raise ErroOnboarding(400, "Aceite o consentimento para documentos eletrônicos antes de continuar")


def _meta(h):
    return {"ip": h._ip_cliente()[:60], "ua": (h.headers.get("User-Agent") or "")[:400], "quando": _iso_utc()}


def registrar_consentimento(conn, ob, lang, meta):
    _exigir_ativo(ob)
    if ob["consentimento"]:
        return
    m = srv.mensagens.marca(conn, ob["empresa_id"]) or {}
    lang = idioma(lang)
    dados = {"em": meta["quando"], "ip": meta["ip"], "ua": meta["ua"], "idioma": lang,
             "texto": texto_consentimento(m.get("nome"), lang)}
    if lang != "en":
        dados["texto_en"] = texto_consentimento(m.get("nome"), "en")
    conn.execute("UPDATE onboardings SET consentimento=?, idioma=?, status='em_andamento', atualizado_em=datetime('now')"
                 " WHERE id=?", (json.dumps(dados, ensure_ascii=False), lang, ob["id"]))
    srv.registrar_evento(conn, ob["candidato_id"], "onboarding", "Consentimento para documentos eletrônicos aceito")
    conn.commit()


def _png_da_assinatura(valor):
    s = str(valor or "")
    if s.startswith("data:"):
        s = s.split(",", 1)[-1]
    try:
        png = base64.b64decode(s, validate=False)
    except ValueError:
        png = b""
    if not png.startswith(b"\x89PNG\r\n\x1a\n") or len(png) < 200 or len(png) > 600 * 1024:
        raise ErroOnboarding(400, "Desenhe a sua assinatura")
    return png


def assinar(conn, ob, cand, d, meta):
    """Assina a carta de proposta ou um documento. d: modelo_id, nome, assinatura, aceite, leu_tudo, declaracao, idioma."""
    _exigir_consentimento(ob)
    pl = plano(conn, ob)
    try:
        tid = int(d.get("modelo_id") or 0)
    except (TypeError, ValueError):
        tid = 0
    alvos = ([pl["modelo_oferta"]] if pl["modelo_oferta"] else []) + pl["documentos"]
    m = next((x for x in alvos if x["id"] == tid), None)
    if not m:
        raise ErroOnboarding(404, "Documento não encontrado")
    if not d.get("aceite"):
        raise ErroOnboarding(400, "Marque a caixa de concordância para assinar")
    if not d.get("leu_tudo"):
        raise ErroOnboarding(400, "Role o documento até o fim antes de assinar")
    nome = _limpo(d.get("nome"), 120)
    if len(nome) < 3 or " " not in nome:
        raise ErroOnboarding(400, "Digite o seu nome completo")
    png = _png_da_assinatura(d.get("assinatura"))
    declaracao = str(d.get("declaracao") or "").strip()[:2000]
    if m["requer_declaracao"] and len(declaracao) < 10:
        raise ErroOnboarding(400, "Escreva a sua declaração pessoal")
    lang = idioma(d.get("idioma") or ob["idioma"] or "en")
    textos = textos_preenchidos(conn, ob, m)
    versao = lang if lang in textos else ("en" if "en" in textos else (next(iter(textos)) if textos else "en"))
    titulos = _json(m["titulos"], {})
    titulo = titulos.get(versao) or titulos.get("en") or next(iter(titulos.values()), "")
    original = None
    texto = textos.get(versao, "")
    if m["tipo"] == "pdf":
        original = ler_modelo_pdf(m["arquivo"])
        if original is None:
            raise ErroOnboarding(404, "Documento não encontrado")
    if versao != "en" and "en" in textos and m["tipo"] != "pdf":
        texto += "\n\n> The English version of this document controls if there is any difference between translations."
    meta = dict(meta, email=cand["email"], consentimento=_json(ob["consentimento"], {}),
                ref="Onboarding %d / %s" % (ob["id"], m["chave"] or "doc-%d" % m["id"]),
                aceite=ACEITE_ASSINATURA.get(lang, ACEITE_ASSINATURA["en"]),
                emissor="%s, %s" % (_json(ob["oferta"], {}).get("representante") or "", ob["criado_em"]))
    pdf, sha_conteudo = gerar_pdf_assinado(conn, ob, cand, titulo, texto, png, nome, declaracao, meta, original)
    rel = gravar_arquivo(conn, ob["id"], pdf)
    chave = "tpl:%d" % m["id"]
    for antigo in docs(conn, ob["id"], "assinatura", chave):
        conn.execute("UPDATE onboarding_docs SET ativo=0 WHERE id=?", (antigo["id"],))
    conn.execute(
        "INSERT INTO onboarding_docs (onboarding_id, empresa_id, tipo, chave, titulo, arquivo, mime, tamanho, sha256,"
        " sha256_texto, idioma, assinante, ip, ua, declaracao) VALUES (?,?,'assinatura',?,?,?,'application/pdf',?,?,?,?,?,?,?,?)",
        (ob["id"], ob["empresa_id"], chave, titulo, rel, len(pdf), hashlib.sha256(pdf).hexdigest(), sha_conteudo,
         versao, nome, meta["ip"], meta["ua"], declaracao))
    srv.registrar_evento(conn, cand["id"], "onboarding", "Documento assinado: %s" % titulo)
    if m["categoria"] == "oferta":
        mover_etapa(conn, cand, ob["candidatura_id"], ("inscrito", "avaliacoes", "entrevista", "proposta"),
                    "contratado", "sistema")
    conn.execute("UPDATE onboardings SET atualizado_em=datetime('now') WHERE id=?", (ob["id"],))
    conn.commit()
    srv.seguranca.registrar(conn, "onboarding_assinado", None, "onboarding:%d %s" % (ob["id"], chave), meta["ip"],
                            empresa_id=ob["empresa_id"], quem="novo contratado: %s" % (cand["nome"] or ""))


def salvar_dados(conn, ob, d, pl):
    _exigir_consentimento(ob)
    atual = _json(ob["dados"], {})
    novos = {}
    erros = []
    for campo, n in (("nome_legal", 120), ("nome_preferido", 80), ("endereco", 200), ("apto", 40), ("cidade", 80),
                     ("estado", 2), ("cep", 10), ("telefone", 30), ("email", 160), ("contato_nome", 120),
                     ("contato_relacao", 60), ("contato_telefone", 30), ("tamanho", 4), ("cnh_estado", 2)):
        if campo in d:
            novos[campo] = _limpo(d.get(campo), n)
    for k in ("estado", "cnh_estado"):
        if k in novos:
            novos[k] = novos[k].upper()
    dados = dict(atual, **novos)
    for k in CAMPOS_DADOS_OBRIGATORIOS:
        if not dados.get(k):
            erros.append(k)
    if dados.get("estado") and not re.match(r"^[A-Z]{2}$", dados["estado"]):
        erros.append("estado")
    if dados.get("cep") and not re.match(r"^\d{5}(-\d{4})?$", dados["cep"]):
        erros.append("cep")
    for k in ("telefone", "contato_telefone"):
        if dados.get(k) and len(_digitos(dados[k])) < 10:
            erros.append(k)
    if dados.get("email") and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", dados["email"]):
        erros.append("email")
    if dados.get("tamanho") and dados["tamanho"] not in TAMANHOS:
        erros.append("tamanho")
    sens_atual = sensiveis(conn, ob) if ob["sensiveis"] else {}
    sens_novos = {}
    nasc = str(d.get("nascimento") or "").strip()
    if nasc:
        dn = _data(nasc)
        hoje = _hoje()
        if not dn or dn > hoje - timedelta(days=14 * 365) or dn < hoje - timedelta(days=100 * 365):
            erros.append("nascimento")
        else:
            sens_novos["nascimento"] = dn.isoformat()
    elif not sens_atual.get("nascimento"):
        erros.append("nascimento")
    cnh = re.sub(r"[^0-9A-Za-z]", "", str(d.get("cnh_numero") or "")).upper()[:25]
    if cnh:
        if len(cnh) < 4:
            erros.append("cnh_numero")
        else:
            sens_novos["cnh_numero"] = cnh
    if pl["dirige"]:
        if not cnh and not sens_atual.get("cnh_numero"):
            erros.append("cnh_numero")
        if not dados.get("cnh_estado"):
            erros.append("cnh_estado")
    if dados.get("cnh_estado") and not re.match(r"^[A-Z]{2}$", dados["cnh_estado"]):
        erros.append("cnh_estado")
    if erros:
        raise ErroOnboarding(400, "Confira os campos destacados", {"campos": sorted(set(erros))})
    conn.execute("UPDATE onboardings SET dados=?, atualizado_em=datetime('now') WHERE id=?",
                 (json.dumps(dados, ensure_ascii=False), ob["id"]))
    if sens_novos:
        salvar_sensiveis(conn, ob["id"], sens_novos)
    conn.commit()


def campos_formulario(tipo):
    f = _formularios()
    if f is None:
        return None
    try:
        return list(f.CAMPOS[tipo])
    except Exception:  # noqa: BLE001
        return None


def _codigos(erros):
    """Códigos "chave:motivo" de formularios.validar -> (campos, mensagens trilíngues por campo)."""
    f = _formularios()
    textos = getattr(f, "MENSAGENS_ERRO", {}) if f is not None else {}
    campos, mensagens = [], {}
    for e in erros or []:
        chave, _, motivo = str(e).partition(":")
        campos.append(chave)
        if chave not in mensagens and motivo in textos:
            mensagens[chave] = textos[motivo]
    return sorted(set(campos)), mensagens


def dados_empregador(cfg, tipo, oferta):
    """Campos de CAMPOS_EMPREGADOR[tipo] preenchidos com as configurações da empresa."""
    nome = cfg.get("empregador_nome") or ""
    linha_end = ", ".join(x for x in (cfg.get("empregador_endereco"), cfg.get("empregador_cidade_estado_cep")) if x)
    inicio = oferta.get("data_inicio") or ""
    valores = {}
    if tipo == "w4":
        valores = {"empregador_nome_endereco": ", ".join(x for x in (nome, linha_end) if x),
                   "primeiro_dia": inicio, "ein_empregador": cfg.get("empregador_ein")}
    elif tipo == "ctw4":
        valores = {"novo_ou_recontratado": "sim" if inicio else "", "data_contratacao": inicio,
                   "empregador_nome": nome, "ein_empregador": cfg.get("empregador_ein"),
                   "empregador_endereco": cfg.get("empregador_endereco"),
                   "empregador_cidade_estado_cep": cfg.get("empregador_cidade_estado_cep"),
                   "empregador_contato": cfg.get("empregador_contato"),
                   "empregador_telefone": cfg.get("empregador_telefone")}
    elif tipo == "w9":
        valores = {"solicitante_nome_endereco": ", ".join(x for x in (nome, linha_end) if x)}
    f = _formularios()
    permitidos = {c.get("chave") for c in (getattr(f, "CAMPOS_EMPREGADOR", {}) or {}).get(tipo, [])} if f else set()
    return {k: v for k, v in valores.items() if v and k in permitidos}


def _sensivel(campo):
    return bool(RE_SENSIVEL.search(str(campo.get("chave") or ""))) or str(campo.get("tipo") or "").lower() in (
        "ssn", "ein", "itin", "tin", "cpf")


def salvar_formulario(conn, ob, cand, tipo, d, meta):
    _exigir_consentimento(ob)
    pl = plano(conn, ob)
    if tipo not in pl["formularios"]:
        raise ErroOnboarding(404, "Formulário não encontrado")
    f = _formularios()
    campos = campos_formulario(tipo)
    if f is None or campos is None:
        raise ErroOnboarding(503, "Os formulários fiscais ainda não estão disponíveis. Tente mais tarde.")
    bruto = d.get("dados") if isinstance(d.get("dados"), dict) else {}
    chaves = {c.get("chave") for c in campos}
    dados = {k: v for k, v in bruto.items() if k in chaves}
    erros = list(f.validar(tipo, dados) or [])
    if erros:
        campos_err, mensagens = _codigos(erros)
        raise ErroOnboarding(400, "Confira os campos destacados", {"campos": campos_err, "mensagens": mensagens})
    nome = _limpo(d.get("nome"), 120)
    if len(nome) < 3:
        raise ErroOnboarding(400, "Digite o seu nome completo")
    if not d.get("aceite"):
        raise ErroOnboarding(400, "Marque a caixa de concordância para assinar")
    png = _png_da_assinatura(d.get("assinatura"))
    completos = dict(dados, **dados_empregador(pl["cfg"], tipo, pl["oferta"]))
    try:
        pdf = f.preencher(tipo, completos, assinatura_png=png, data_assinatura=_hoje().strftime("%m/%d/%Y"),
                          nome_assinatura=nome)
    except Exception as exc:  # noqa: BLE001
        if getattr(exc, "erros", None) is not None:
            campos_err, mensagens = _codigos(exc.erros)
            if set(campos_err) - chaves:
                sys.stderr.write("Onboarding: dados do empregador inválidos no formulário %s: %s\n"
                                 % (tipo, ",".join(sorted(set(campos_err) - chaves))))
                raise ErroOnboarding(400, "Os dados do empregador nas configurações do onboarding estão incompletos ou inválidos")
            raise ErroOnboarding(400, "Confira os campos destacados", {"campos": campos_err, "mensagens": mensagens})
        sys.stderr.write("Onboarding: preenchimento do formulário %s falhou (%s)\n" % (tipo, type(exc).__name__))
        raise ErroOnboarding(500, "Não foi possível gerar o formulário. Tente de novo.")
    if not isinstance(pdf, (bytes, bytearray)) or not bytes(pdf).startswith(b"%PDF"):
        raise ErroOnboarding(500, "Não foi possível gerar o formulário. Tente de novo.")
    pdf = bytes(pdf)
    rel = gravar_arquivo(conn, ob["id"], pdf)
    for antigo in docs(conn, ob["id"], "formulario", tipo):
        conn.execute("UPDATE onboarding_docs SET ativo=0 WHERE id=?", (antigo["id"],))
        apagar_arquivo(antigo["arquivo"])
    titulo = {"w4": "Form W-4", "w9": "Form W-9", "i9": "Form I-9 (Section 1)", "ctw4": "Form CT-W4"}.get(tipo, tipo)
    conn.execute(
        "INSERT INTO onboarding_docs (onboarding_id, empresa_id, tipo, chave, titulo, arquivo, mime, tamanho, sha256,"
        " idioma, assinante, ip, ua, dados_cifrados) VALUES (?,?,'formulario',?,?,?,'application/pdf',?,?,?,?,?,?,?)",
        (ob["id"], ob["empresa_id"], tipo, titulo, rel, len(pdf), hashlib.sha256(pdf).hexdigest(),
         idioma(ob["idioma"] or "en"), nome, meta["ip"], meta["ua"], cifrar_dict(conn, dados)))
    # identificadores fiscais para a máscara do painel
    novos = {}
    for c in campos:
        k = str(c.get("chave") or "")
        v = str(dados.get(k) or "").strip()
        if not v:
            continue
        kl = k.lower()
        if "ssn" in kl or "social" in kl or str(c.get("tipo") or "").lower() == "ssn":
            novos["ssn"] = v
        elif "itin" in kl:
            novos["itin"] = v
        elif re.search(r"(^|_)ein($|_)", kl) or str(c.get("tipo") or "").lower() == "ein":
            novos["ein"] = v
    if novos:
        salvar_sensiveis(conn, ob["id"], novos)
    srv.registrar_evento(conn, cand["id"], "onboarding", "Formulário preenchido e assinado: %s" % titulo)
    conn.commit()
    srv.seguranca.registrar(conn, "onboarding_formulario", None, "onboarding:%d %s" % (ob["id"], tipo), meta["ip"],
                            empresa_id=ob["empresa_id"], quem="novo contratado: %s" % (cand["nome"] or ""))


def salvar_upload(conn, ob, categoria, nome_original, dados, pl):
    _exigir_consentimento(ob)
    validas = {c["chave"] for c in pl["categorias"]} | {"cheque_anulado"}
    if categoria not in validas:
        raise ErroOnboarding(400, "Tipo de documento inválido")
    if not dados:
        raise ErroOnboarding(400, "Arquivo inválido")
    if len(dados) > MAX_ARQUIVO:
        raise ErroOnboarding(400, "Arquivo maior que 10 MB")
    mime, ext = tipo_do_arquivo(dados)
    if not mime:
        raise ErroOnboarding(400, "Envie uma foto (JPG, PNG ou HEIC) ou um PDF")
    if len(docs(conn, ob["id"], "arquivo", categoria)) >= MAX_POR_CATEGORIA:
        raise ErroOnboarding(400, "Limite de arquivos para este documento atingido")
    rel = gravar_arquivo(conn, ob["id"], dados)
    nome = re.sub(r"[^\w.\- ]", "_", os.path.basename(str(nome_original or "")))[:80] or ("arquivo." + ext)
    did = conn.execute(
        "INSERT INTO onboarding_docs (onboarding_id, empresa_id, tipo, chave, titulo, arquivo, mime, tamanho, sha256,"
        " nome_original) VALUES (?,?,'arquivo',?,?,?,?,?,?,?)",
        (ob["id"], ob["empresa_id"], categoria, categoria, rel, mime, len(dados), hashlib.sha256(dados).hexdigest(),
         nome)).lastrowid
    conn.execute("UPDATE onboardings SET atualizado_em=datetime('now') WHERE id=?", (ob["id"],))
    conn.commit()
    return did


def apagar_upload(conn, ob, doc_id):
    _exigir_consentimento(ob)
    d = conn.execute("SELECT * FROM onboarding_docs WHERE id=? AND onboarding_id=? AND tipo='arquivo' AND ativo=1",
                     (doc_id, ob["id"])).fetchone()
    if not d:
        raise ErroOnboarding(404, "Arquivo não encontrado")
    conn.execute("UPDATE onboarding_docs SET ativo=0, arquivo='' WHERE id=?", (d["id"],))
    apagar_arquivo(d["arquivo"])
    conn.commit()


def salvar_pagamento(conn, ob, d, pl):
    _exigir_consentimento(ob)
    metodo = d.get("metodo")
    if metodo not in pl["metodos"]:
        raise ErroOnboarding(400, "Forma de pagamento inválida")
    pag = {"metodo": metodo}
    sens_novos = {"routing": "", "conta": ""}
    erros = []
    atual_sens = sensiveis(conn, ob) if ob["sensiveis"] else {}
    if metodo == "deposito":
        pag["banco"] = _limpo(d.get("banco"), 80)
        pag["tipo_conta"] = d.get("tipo_conta") if d.get("tipo_conta") in ("corrente", "poupanca") else ""
        routing = str(d.get("routing") or "").strip().replace(" ", "")
        conta = str(d.get("conta") or "").strip().replace(" ", "")
        confirma = str(d.get("conta_confirmacao") or "").strip().replace(" ", "")
        if not pag["banco"]:
            erros.append("banco")
        if not pag["tipo_conta"]:
            erros.append("tipo_conta")
        manter = not routing and not conta and atual_sens.get("routing") and atual_sens.get("conta")
        if manter:
            sens_novos = {}
        else:
            if not aba_valido(routing):
                erros.append("routing")
            if not re.match(r"^\d{4,17}$", conta):
                erros.append("conta")
            elif conta != confirma:
                erros.append("conta_confirmacao")
            sens_novos = {"routing": routing, "conta": conta}
        if "routing" in erros and len(erros) == 1:
            raise ErroOnboarding(400, "Routing number inválido. Confira os 9 dígitos no seu cheque ou no app do banco.",
                                 {"campos": ["routing"]})
    elif metodo == "zelle":
        z = _limpo(d.get("zelle"), 120)
        if not (re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", z) or len(_digitos(z)) >= 10):
            erros.append("zelle")
        pag["zelle"] = z
    elif metodo == "cheque":
        if not d.get("endereco_confirmado"):
            erros.append("endereco_confirmado")
        pag["endereco_confirmado"] = bool(d.get("endereco_confirmado"))
        pag["endereco_cheque"] = _limpo(d.get("endereco_cheque"), 250)
    else:
        if not d.get("provedor_ciente"):
            erros.append("provedor_ciente")
        pag["provedor_ciente"] = bool(d.get("provedor_ciente"))
    if erros:
        raise ErroOnboarding(400, "Confira os campos destacados", {"campos": erros})
    conn.execute("UPDATE onboardings SET pagamento=?, atualizado_em=datetime('now') WHERE id=?",
                 (json.dumps(pag, ensure_ascii=False), ob["id"]))
    if sens_novos:
        salvar_sensiveis(conn, ob["id"], sens_novos)
    conn.commit()


def concluir(conn, ob, cand, meta):
    _exigir_consentimento(ob)
    pl = plano(conn, ob)
    prog = progresso(conn, ob, pl)
    if prog["pendentes"]:
        raise ErroOnboarding(400, "Ainda há etapas pendentes", {"pendentes": prog["pendentes"]})
    feito = conn.execute("UPDATE onboardings SET status='concluido', concluido_em=datetime('now'),"
                         " atualizado_em=datetime('now') WHERE id=? AND status IN ('enviado','em_andamento')",
                         (ob["id"],)).rowcount
    if not feito:
        raise ErroOnboarding(400, "Este onboarding já foi concluído")
    srv.registrar_evento(conn, cand["id"], "onboarding", "Onboarding concluído pelo novo contratado")
    conn.commit()
    srv.seguranca.registrar(conn, "onboarding_concluido", None, "onboarding:%d" % ob["id"], meta["ip"],
                            empresa_id=ob["empresa_id"], quem="novo contratado: %s" % (cand["nome"] or ""))
    avisar_conclusao(conn, ob["id"])


# ------------------------------------------------------------- avisos

def _em_segundo_plano(funcao, *args):
    def rodar():
        conn = srv.db()
        try:
            funcao(conn, *args)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Onboarding: envio falhou: %s\n" % type(exc).__name__)
        finally:
            conn.close()
    threading.Thread(target=rodar, daemon=True).start()


def avisar_conclusao(conn, ob_id):
    if ENVIO_EM_SEGUNDO_PLANO:
        _em_segundo_plano(_enviar_conclusao, ob_id)
    else:
        _enviar_conclusao(conn, ob_id)


def email_conclusao_gestor(conn, ob, lang):
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    lang = idioma(lang)
    m = srv.mensagens
    marca = m.marca(conn, ob["empresa_id"])
    oferta = _json(ob["oferta"], {})
    nome = cand["nome"] or ""
    ficha = "%s/gestor#candidato=%d" % (srv.url_publica(conn), cand["id"])
    corpo = t(lang, "fim_corpo", nome=nome, cargo=oferta.get("cargo", ""), inicio=data_extenso(oferta.get("data_inicio"), lang))
    partes = [m._paragrafo(corpo)]
    texto = [corpo, ""]
    prazo_i9 = i9_prazo(ob)
    if prazo_i9:
        aviso = t(lang, "fim_i9", prazo=data_extenso(prazo_i9, lang))
        partes.append(m._paragrafo(aviso, "#8A6A2B", 14))
        texto += [aviso, ""]
    partes.append(m._botao(ficha, t(lang, "fim_botao")))
    texto.append(ficha)
    assunto = t(lang, "fim_assunto", nome=nome)
    return assunto, "\n".join(texto), m.layout("".join(partes), lang, marca, ("✅", assunto, "#2E9E6A"))


def _enviar_conclusao(conn, ob_id):
    ob = recarregar(conn, ob_id)
    if not ob or not srv.config_get(conn, "smtp_host"):
        return 0
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    n = 0
    for g in conn.execute("SELECT email, local, is_admin, empresa_id, idioma FROM gestores WHERE empresa_id=? AND aprovado=1",
                          (ob["empresa_id"],)).fetchall():
        if not (g["email"] or "").strip() or not srv.empresas.ve_local(g, cand["local"]):
            continue
        assunto, texto, html = email_conclusao_gestor(conn, ob, g["idioma"])
        ok, _ = srv.enviar_email(conn, g["email"].strip(), assunto, texto, html=html)
        n += 1 if ok else 0
    if (cand["email"] or "").strip():
        lang = _lang_ob(conn, ob)
        m = srv.mensagens
        marca = m.marca(conn, ob["empresa_id"])
        empresa = (marca or {}).get("nome") or ""
        corpo = t(lang, "fim_cand_corpo", nome=(cand["nome"] or "").split(" ")[0], empresa=empresa)
        url = link(conn, ob)
        html = m.layout(m._paragrafo(corpo) + m._botao(url, t(lang, "lem_botao"), "#5E7086")
                        + m._paragrafo(t(lang, "assinatura", empresa=empresa), "#4a5568", 14),
                        lang, marca, ("✅", t(lang, "fim_cand_assunto"), "#2E9E6A"))
        srv.enviar_email(conn, cand["email"].strip(), t(lang, "fim_cand_assunto"),
                         "\n".join([corpo, "", url, "", t(lang, "assinatura", empresa=empresa)]), html=html)
    srv.registrar_evento(conn, cand["id"], "email", "Onboarding concluído: aviso a %d gestor(es)" % n)
    conn.commit()
    return n


def email_lembrete(conn, ob, pendentes):
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    lang = _lang_ob(conn, ob)
    m = srv.mensagens
    marca = m.marca(conn, ob["empresa_id"])
    empresa = (marca or {}).get("nome") or ""
    nomes = t(lang, "etapas")
    intro = t(lang, "lem_corpo", nome=(cand["nome"] or "").split(" ")[0], empresa=empresa)
    itens = [nomes.get(e, e) for e in pendentes]
    prazo = t(lang, "lem_prazo", prazo=data_extenso(ob["prazo"], lang))
    url = link(conn, ob)
    lista = "".join('<li style="margin:4px 0">%s</li>' % m._e(i) for i in itens)
    html = m.layout(m._paragrafo(intro) + '<ul style="color:#101B37;font-size:15px;margin:0 0 12px">' + lista + "</ul>"
                    + m._paragrafo(prazo, "#4a5568", 14) + m._botao(url, t(lang, "lem_botao"), "#2E9E6A")
                    + m._paragrafo(t(lang, "assinatura", empresa=empresa), "#4a5568", 14),
                    lang, marca, ("⏳", t(lang, "lem_titulo"), "#C79A3E"))
    texto = "\n".join([intro] + ["- " + i for i in itens] + ["", prazo, "", url, "", t(lang, "assinatura", empresa=empresa)])
    return t(lang, "lem_assunto"), texto, html


def enviar_lembretes(conn, agora=None):
    """Lembrete ao novo contratado a cada N dias (configuração da empresa), no
    máximo um por dia, até concluir ou passar o prazo."""
    if not srv.config_get(conn, "smtp_host"):
        return 0
    hoje = (agora or _agora()).date()
    hoje_iso = hoje.isoformat()
    enviados = 0
    for ob in conn.execute("SELECT * FROM onboardings WHERE status IN ('enviado','em_andamento')").fetchall():
        cfg = config(conn, ob["empresa_id"])
        n = int(cfg.get("lembrete_dias") or 0)
        if n <= 0:
            continue
        prazo = _data(ob["prazo"])
        if prazo and hoje > prazo:
            continue
        base = _data(ob["lembrete_em"]) or _data(ob["criado_em"]) or hoje
        if (hoje - base).days < n or ob["lembrete_em"] == hoje_iso:
            continue
        pendentes = progresso(conn, ob)["pendentes"]
        if not pendentes:
            continue
        # marca antes de enviar (atômico): nunca dois lembretes no mesmo dia
        if not conn.execute("UPDATE onboardings SET lembrete_em=?, lembretes=lembretes+1 WHERE id=? AND lembrete_em!=?",
                            (hoje_iso, ob["id"], hoje_iso)).rowcount:
            continue
        conn.commit()
        cand = conn.execute("SELECT email FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
        if not cand or not (cand["email"] or "").strip():
            continue
        assunto, texto, html = email_lembrete(conn, ob, pendentes)
        ok, _ = srv.enviar_email(conn, cand["email"].strip(), assunto, texto, html=html)
        if ok:
            enviados += 1
            srv.registrar_evento(conn, ob["candidato_id"], "email", "Lembrete de onboarding enviado")
            conn.commit()
    return enviados


def rotina_onboarding():
    while True:
        try:
            conn = srv.db()
            try:
                enviar_lembretes(conn)
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Rotina do onboarding falhou: %s\n" % type(exc).__name__)
        time.sleep(INTERVALO_ROTINA)


# ------------------------------------------------------------- dados para o portal

def _doc_publico(d):
    return {"id": d["id"], "tipo": d["tipo"], "chave": d["chave"], "titulo": d["titulo"], "criado_em": d["criado_em"],
            "nome": d["nome_original"], "tamanho": d["tamanho"], "mime": d["mime"]}


def _sem_sensiveis(campos, dados):
    sens = {c.get("chave") for c in campos if _sensivel(c)}
    return {k: v for k, v in (dados or {}).items() if k not in sens}


def dados_publicos(conn, ob):
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    m = srv.mensagens.marca(conn, ob["empresa_id"]) or {}
    pl = plano(conn, ob)
    sens = sensiveis(conn, ob) if ob["sensiveis"] else {}
    prog = progresso(conn, ob, pl, sens)
    todos = docs(conn, ob["id"])
    assinados = {d["chave"]: d for d in todos if d["tipo"] == "assinatura"}
    forms_feitos = {d["chave"]: d for d in todos if d["tipo"] == "formulario"}

    def doc_modelo(mo):
        ass = assinados.get("tpl:%d" % mo["id"])
        return {"id": mo["id"], "categoria": mo["categoria"], "tipo": mo["tipo"], "titulos": _json(mo["titulos"], {}),
                "textos": textos_preenchidos(conn, ob, mo) if mo["tipo"] == "texto" else {},
                "requer_declaracao": bool(mo["requer_declaracao"]),
                "assinado": bool(ass), "doc_id": ass["id"] if ass else None,
                "assinado_em": ass["criado_em"] if ass else ""}

    formularios_ = []
    for tipo in pl["formularios"]:
        campos = campos_formulario(tipo)
        feito = forms_feitos.get(tipo)
        anteriores = {}
        if feito and feito["dados_cifrados"] and campos:
            anteriores = _sem_sensiveis(campos, decifrar_dict(conn, feito["dados_cifrados"]))
        formularios_.append({"tipo": tipo, "campos": campos, "feito": bool(feito), "doc_id": feito["id"] if feito else None,
                             "anteriores": anteriores})
    dados = _json(ob["dados"], {})
    pag = _json(ob["pagamento"], {})
    oferta = pl["oferta"]
    return {
        "empresa": {"nome": m.get("nome") or "", "logo_url": m.get("logo_url") or ""},
        "nome": (cand["nome"] or "").split(" ")[0],
        "nome_completo": cand["nome"] or "",
        "email": cand["email"] or "",
        "idioma": idioma(ob["idioma"]) if ob["idioma"] else (idioma(cand["idioma"]) if cand["idioma"] else ""),
        "status": ob["status"], "tipo": ob["tipo"], "prazo": ob["prazo"],
        "consentimento": bool(ob["consentimento"]),
        "textos_consentimento": {lang: texto_consentimento(m.get("nome"), lang) for lang in ("pt", "en", "es")},
        "aceite_assinatura": ACEITE_ASSINATURA,
        "oferta": {"cargo": oferta.get("cargo"), "data_inicio": oferta.get("data_inicio"), "valor": oferta.get("valor"),
                   "unidade": oferta.get("unidade"), "horario": oferta.get("horario"), "notas": oferta.get("notas"),
                   "dirige": pl["dirige"]},
        "etapas": prog["etapas"], "pct": prog["pct"], "pendentes": prog["pendentes"],
        "modelo_oferta": doc_modelo(pl["modelo_oferta"]) if pl["modelo_oferta"] else None,
        "documentos": [doc_modelo(mo) for mo in pl["documentos"]],
        "formularios": formularios_, "formularios_disponivel": _formularios() is not None,
        "categorias": pl["categorias"],
        "arquivos": [_doc_publico(d) for d in todos if d["tipo"] == "arquivo"],
        "metodos": pl["metodos"], "provedor_nome": pl["cfg"]["provedor_nome"],
        "pagamento": dict(pag, routing_mascara=mascarar(sens.get("routing")), conta_mascara=mascarar(sens.get("conta"))),
        "dados": dict(dados, nascimento_mascara=mascarar(sens.get("nascimento"), "nascimento"),
                      cnh_numero_mascara=mascarar(sens.get("cnh_numero"))),
        "baixaveis": [_doc_publico(d) for d in todos if d["tipo"] in ("assinatura", "formulario")],
    }


# ------------------------------------------------------------- dados para o gestor

def resumo_gestor(conn, ob, gestor):
    pl = plano(conn, ob)
    sens = {}
    erro_chave = ""
    if ob["sensiveis"]:
        try:
            sens = sensiveis(conn, ob)
        except ErroChave as e:
            erro_chave = str(e)
    prog = progresso(conn, ob, pl, sens)
    todos = docs(conn, ob["id"])
    prazo = _data(ob["prazo"])
    prazo_i9 = i9_prazo(ob)
    i9_feito = any(d["tipo"] == "i9_secao2" for d in todos)
    cfg = pl["cfg"]
    concl = _data(ob["concluido_em"])
    pode_purgar = bool(ob["status"] == "concluido" and cfg["retencao_dias"] and concl and not ob["purgado_em"]
                       and (_hoje() - concl).days >= cfg["retencao_dias"] and ob["sensiveis"])
    cons = _json(ob["consentimento"], {})
    return {
        "id": ob["id"], "status": ob["status"], "tipo": ob["tipo"], "oferta": pl["oferta"], "prazo": ob["prazo"],
        "criado_em": ob["criado_em"], "criado_por": ob["criado_por"], "concluido_em": ob["concluido_em"],
        "cancelado_em": ob["cancelado_em"], "idioma": ob["idioma"],
        "link": link(conn, ob) if ob["status"] in ATIVOS else "",
        "etapas": prog["etapas"], "pct": prog["pct"], "pendentes": prog["pendentes"],
        "atrasado": bool(ob["status"] in ATIVOS and prazo and prazo < _hoje()),
        "consentimento_em": cons.get("em", ""),
        "documentos": [_doc_publico(d) for d in todos],
        "esperados": {"documentos": [{"id": mo["id"], "titulo": titulo_modelo(mo, "en")} for mo in pl["documentos"]],
                      "modelo_oferta": ({"id": pl["modelo_oferta"]["id"], "titulo": titulo_modelo(pl["modelo_oferta"], "en")}
                                        if pl["modelo_oferta"] else None),
                      "formularios": pl["formularios"], "categorias": pl["categorias"]},
        "dados": _json(ob["dados"], {}),
        "pagamento": _json(ob["pagamento"], {}),
        "mascaras": {k: mascarar(v, k) for k, v in sens.items()},
        "erro_chave": erro_chave,
        "i9": {"necessario": bool(prazo_i9), "prazo": prazo_i9.isoformat() if prazo_i9 else "",
               "feito": i9_feito, "secao1": any(d["tipo"] == "formulario" and d["chave"] == "i9" for d in todos),
               "atrasado": bool(prazo_i9 and not i9_feito and prazo_i9 < _hoje())},
        "pode_purgar": pode_purgar, "purgado_em": ob["purgado_em"], "retencao_dias": cfg["retencao_dias"],
    }


def lista_gestor(conn, gestor):
    saida = []
    for r in conn.execute(
            "SELECT o.*, c.nome, c.local, c.empresa_id AS c_empresa FROM onboardings o JOIN candidatos c ON c.id=o.candidato_id"
            " WHERE o.empresa_id=? AND (o.status IN ('enviado','em_andamento')"
            " OR (o.status='concluido' AND o.concluido_em>=datetime('now','-21 days'))) ORDER BY o.criado_em DESC",
            (gestor["empresa_id"],)).fetchall():
        if not srv.gestor_ve_candidato(gestor, {"empresa_id": r["c_empresa"], "local": r["local"]}):
            continue
        try:
            prog = progresso(conn, r)
        except ErroChave:
            prog = {"pct": 0, "pendentes": []}
        oferta = _json(r["oferta"], {})
        prazo = _data(r["prazo"])
        prazo_i9 = i9_prazo(r)
        i9_feito = bool(conn.execute("SELECT 1 FROM onboarding_docs WHERE onboarding_id=? AND tipo='i9_secao2' AND ativo=1",
                                     (r["id"],)).fetchone())
        saida.append({
            "id": r["id"], "candidato_id": r["candidato_id"], "nome": r["nome"], "cargo": oferta.get("cargo") or "",
            "tipo": r["tipo"], "status": r["status"], "pct": prog["pct"], "pendentes": prog["pendentes"],
            "prazo": r["prazo"], "data_inicio": oferta.get("data_inicio") or "",
            "atrasado": bool(r["status"] in ATIVOS and prazo and prazo < _hoje()),
            "i9_prazo": prazo_i9.isoformat() if prazo_i9 else "", "i9_feito": i9_feito,
            "i9_atrasado": bool(prazo_i9 and not i9_feito and prazo_i9 < _hoje()),
        })
    return saida


# ------------------------------------------------------------- I-9 Seção 2

def campos_i9_secao2():
    f = _formularios()
    if f is not None and getattr(f, "CAMPOS_I9_SECAO2", None):
        return list(f.CAMPOS_I9_SECAO2)
    return []


def padroes_i9_secao2(conn, ob, gestor):
    cfg = config(conn, ob["empresa_id"])
    oferta = _json(ob["oferta"], {})
    m = srv.mensagens.marca(conn, ob["empresa_id"]) or {}
    return {"lista": "", "primeiro_dia": oferta.get("data_inicio") or "", "representante_nome": gestor["nome"],
            "empresa_nome": cfg.get("empregador_nome") or m.get("nome") or "",
            "empresa_endereco": ", ".join(x for x in (cfg.get("empregador_endereco"), cfg.get("empregador_cidade_estado_cep")) if x),
            "data": _hoje().isoformat()}


def i9_secao2(conn, ob, gestor, d, ip=""):
    f = _formularios()
    campos = campos_i9_secao2()
    if f is None or not hasattr(f, "preencher_i9_secao2") or not campos:
        raise ErroOnboarding(503, "Os formulários fiscais ainda não estão disponíveis. Tente mais tarde.")
    secao1 = docs(conn, ob["id"], "formulario", "i9")
    if not secao1:
        raise ErroOnboarding(400, "A Seção 1 do I-9 ainda não foi preenchida")
    bruto = d.get("dados") if isinstance(d.get("dados"), dict) else {}
    chaves = {c.get("chave") for c in campos}
    dados = {k: (v if isinstance(v, bool) else _limpo(v, 200)) for k, v in bruto.items() if k in chaves}
    erros = list(f.validar("i9_secao2", dados) or [])
    if erros:
        campos_err, mensagens = _codigos(erros)
        raise ErroOnboarding(400, "Confira os campos destacados", {"campos": campos_err, "mensagens": mensagens})
    png = _png_da_assinatura(d.get("assinatura")) if d.get("assinatura") else None
    original = ler_arquivo(conn, secao1[0]["arquivo"])
    if original is None:
        raise ErroOnboarding(404, "Arquivo não encontrado")
    try:
        pdf = bytes(f.preencher_i9_secao2(original, dados, assinatura_png=png))
    except Exception as exc:  # noqa: BLE001
        if getattr(exc, "erros", None) is not None:
            campos_err, mensagens = _codigos(exc.erros)
            raise ErroOnboarding(400, "Confira os campos destacados", {"campos": campos_err, "mensagens": mensagens})
        sys.stderr.write("Onboarding: I-9 seção 2 falhou (%s)\n" % type(exc).__name__)
        raise ErroOnboarding(500, "Não foi possível gerar o formulário. Tente de novo.")
    rel = gravar_arquivo(conn, ob["id"], pdf)
    for antigo in docs(conn, ob["id"], "i9_secao2"):
        conn.execute("UPDATE onboarding_docs SET ativo=0 WHERE id=?", (antigo["id"],))
        apagar_arquivo(antigo["arquivo"])
    conn.execute(
        "INSERT INTO onboarding_docs (onboarding_id, empresa_id, tipo, chave, titulo, arquivo, mime, tamanho, sha256,"
        " assinante, ip) VALUES (?,?,'i9_secao2','i9','Form I-9 (Sections 1 and 2)',?,'application/pdf',?,?,?,?)",
        (ob["id"], ob["empresa_id"], rel, len(pdf), hashlib.sha256(pdf).hexdigest(), gestor["nome"], ip))
    srv.registrar_evento(conn, ob["candidato_id"], "onboarding", "I-9 Seção 2 preenchida pelo empregador", gestor["nome"])
    conn.commit()
    srv.seguranca.registrar(conn, "onboarding_i9_secao2", gestor, "onboarding:%d" % ob["id"], ip)


def purgar(conn, ob, gestor, ip=""):
    """Apaga os campos sensíveis (cifrados) e os dados dos formulários. Os PDFs
    oficiais ficam: há prazos legais de guarda (I-9, W-4)."""
    conn.execute("UPDATE onboardings SET sensiveis='', purgado_em=datetime('now') WHERE id=?", (ob["id"],))
    conn.execute("UPDATE onboarding_docs SET dados_cifrados='' WHERE onboarding_id=?", (ob["id"],))
    srv.registrar_evento(conn, ob["candidato_id"], "onboarding", "Dados sensíveis do onboarding apagados (retenção)",
                         gestor["nome"])
    conn.commit()
    srv.seguranca.registrar(conn, "onboarding_purga_sensiveis", gestor, "onboarding:%d" % ob["id"], ip)


# ------------------------------------------------------------- limite de pedidos públicos

def _limite_excedido(ip):
    agora = time.time()
    with _trava_limite:
        recentes = [x for x in _pedidos.get(ip, []) if agora - x < _JANELA] + [agora]
        _pedidos[ip] = recentes
        invalidos = [x for x in _invalidos.get(ip, []) if agora - x < _JANELA]
        _invalidos[ip] = invalidos
        if len(_pedidos) > 5000:
            for k in [k for k, v in _pedidos.items() if agora - v[-1] > _JANELA]:
                _pedidos.pop(k, None)
                _invalidos.pop(k, None)
        return len(recentes) > _LIMITE_PEDIDOS or len(invalidos) >= _LIMITE_INVALIDOS


def _marcar_invalido(ip):
    with _trava_limite:
        _invalidos.setdefault(ip, []).append(time.time())


def zerar_limites():
    with _trava_limite:
        _pedidos.clear()
        _invalidos.clear()


# ------------------------------------------------------------- respostas HTTP

def _resp(h, status, dados):
    h._json(status, dados)
    return True


def _erro(h, e):
    return _resp(h, e.status, dict({"erro": e.mensagem}, **e.extra))


def _enviar_arquivo(h, dados, mime, nome):
    nome = re.sub(r'[^\w.\- ]', "_", nome or "arquivo")[:100]
    h.send_response(200)
    h.send_header("Content-Type", mime or "application/octet-stream")
    h.send_header("Content-Disposition", 'attachment; filename="%s"' % nome)
    h.send_header("Content-Length", str(len(dados)))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    h.wfile.write(dados)
    return True


def _nome_download(d, cand_nome=""):
    base = re.sub(r"\s+", "_", (cand_nome or "").strip())[:40]
    if d["tipo"] == "arquivo":
        return "%s_%s" % (d["chave"], d["nome_original"] or "arquivo")
    return "%s%s.pdf" % (re.sub(r"[^\w]+", "_", d["titulo"] or d["chave"]).strip("_"), ("_" + base) if base else "")


def rotear_publico(h, method, path, conn):
    """/api/onboarding/<token>[/acao] sem login: o token é a credencial."""
    if not path.startswith("/api/onboarding/"):
        return None
    ip = h._ip_cliente()
    if _limite_excedido(ip):
        return _resp(h, 429, {"erro": "Muitas tentativas. Aguarde alguns minutos e tente de novo."})
    partes = path[len("/api/onboarding/"):].split("/")
    ob = onboarding_do_token(conn, partes[0])
    if not ob:
        _marcar_invalido(ip)
        return _resp(h, 404, {"erro": "Link de onboarding inválido"})
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    acao = partes[1] if len(partes) > 1 else ""
    try:
        if method == "GET" and not acao:
            if ob["status"] == "cancelado":
                return _resp(h, 410, {"erro": "Este onboarding foi cancelado"})
            return _resp(h, 200, dados_publicos(conn, ob))
        if method == "GET" and acao == "modelo" and len(partes) == 3 and partes[2].isdigit():
            pl = plano(conn, ob)
            alvos = ([pl["modelo_oferta"]] if pl["modelo_oferta"] else []) + pl["documentos"]
            mo = next((x for x in alvos if x["id"] == int(partes[2]) and x["tipo"] == "pdf"), None)
            dados = ler_modelo_pdf(mo["arquivo"]) if mo else None
            if dados is None:
                return _resp(h, 404, {"erro": "Documento não encontrado"})
            return _enviar_arquivo(h, dados, "application/pdf", "documento.pdf")
        if method == "GET" and acao == "arquivo" and len(partes) == 3 and partes[2].isdigit():
            d = conn.execute("SELECT * FROM onboarding_docs WHERE id=? AND onboarding_id=? AND ativo=1"
                             " AND tipo IN ('assinatura','formulario','arquivo')", (int(partes[2]), ob["id"])).fetchone()
            dados = ler_arquivo(conn, d["arquivo"]) if d else None
            if dados is None:
                return _resp(h, 404, {"erro": "Arquivo não encontrado"})
            return _enviar_arquivo(h, dados, d["mime"], _nome_download(d))
        meta = _meta(h)
        if method == "POST" and acao == "idioma":
            lang = (h._body() or {}).get("idioma")
            if lang in ("pt", "en", "es") and ob["status"] in ATIVOS:
                conn.execute("UPDATE onboardings SET idioma=? WHERE id=?", (lang, ob["id"]))
                conn.commit()
            return _resp(h, 200, {"ok": True})
        if method == "POST" and acao == "consentimento":
            d = h._body() or {}
            if not d.get("aceito"):
                return _resp(h, 400, {"erro": "Aceite o consentimento para documentos eletrônicos antes de continuar"})
            registrar_consentimento(conn, ob, d.get("idioma") or ob["idioma"] or "en", meta)
            return _resp(h, 200, dados_publicos(conn, recarregar(conn, ob["id"])))
        if method == "POST" and acao == "assinar":
            assinar(conn, ob, cand, h._body() or {}, meta)
            return _resp(h, 200, dados_publicos(conn, recarregar(conn, ob["id"])))
        if method == "POST" and acao == "dados":
            salvar_dados(conn, ob, h._body() or {}, plano(conn, ob))
            return _resp(h, 200, dados_publicos(conn, recarregar(conn, ob["id"])))
        if method == "POST" and acao == "formulario" and len(partes) == 3:
            salvar_formulario(conn, ob, cand, partes[2], h._body() or {}, meta)
            return _resp(h, 200, dados_publicos(conn, recarregar(conn, ob["id"])))
        if method == "POST" and acao == "arquivo":
            qs = parse_qs(urlparse(h.path).query)
            salvar_upload(conn, ob, qs.get("categoria", [""])[0], qs.get("nome", [""])[0],
                          getattr(h, "_raw", b"") or b"", plano(conn, ob))
            return _resp(h, 200, dados_publicos(conn, recarregar(conn, ob["id"])))
        if method == "DELETE" and acao == "arquivo" and len(partes) == 3 and partes[2].isdigit():
            apagar_upload(conn, ob, int(partes[2]))
            return _resp(h, 200, dados_publicos(conn, recarregar(conn, ob["id"])))
        if method == "POST" and acao == "pagamento":
            salvar_pagamento(conn, ob, h._body() or {}, plano(conn, ob))
            return _resp(h, 200, dados_publicos(conn, recarregar(conn, ob["id"])))
        if method == "POST" and acao == "concluir":
            concluir(conn, ob, cand, meta)
            return _resp(h, 200, dados_publicos(conn, recarregar(conn, ob["id"])))
    except ErroOnboarding as e:
        return _erro(h, e)
    except ErroChave as e:
        sys.stderr.write("Onboarding: %s\n" % e)
        return _resp(h, 500, {"erro": "Erro interno"})
    return _resp(h, 404, {"erro": "Rota não encontrada"})


def _ob_do_gestor(conn, gestor, ob_id):
    ob = conn.execute("SELECT * FROM onboardings WHERE id=? AND empresa_id=?", (ob_id, gestor["empresa_id"])).fetchone()
    if not ob:
        return None
    cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
    if not cand or not srv.gestor_ve_candidato(gestor, cand):
        return None
    return ob


def rotear_gestor(h, method, path, conn, gestor):
    if not path.startswith("/api/gestor/onboarding"):
        return None
    empresa_id = gestor["empresa_id"]
    ip = h._ip_cliente()
    try:
        if path == "/api/gestor/onboarding/config":
            if not gestor["is_admin"]:
                return _resp(h, 403, {"erro": "Apenas o administrador da empresa configura o onboarding"})
            if method == "GET":
                return _resp(h, 200, {"config": config(conn, empresa_id), "etapas": list(PADRAO_CFG["ordem"]),
                                      "metodos": list(METODOS), "estaduais": list(FORMULARIOS_ESTADUAIS),
                                      "modelos": [modelo_publico(m) for m in modelos(conn, empresa_id)]})
            if method == "POST":
                cfg, erro = validar_config(h._body() or {}, config(conn, empresa_id))
                if erro:
                    return _resp(h, 400, {"erro": erro})
                salvar_config(conn, empresa_id, cfg)
                return _resp(h, 200, {"ok": True, "config": config(conn, empresa_id)})

        if path == "/api/gestor/onboarding/modelo" and method == "POST":
            if not gestor["is_admin"]:
                return _resp(h, 403, {"erro": "Apenas o administrador da empresa configura o onboarding"})
            d = h._body() or {}
            atual = modelo(conn, empresa_id, d.get("id")) if d.get("id") else None
            if d.get("id") and not atual:
                return _resp(h, 404, {"erro": "Documento não encontrado"})
            tid = salvar_modelo(conn, empresa_id, d, atual)
            return _resp(h, 200, {"ok": True, "modelo": modelo_publico(modelo(conn, empresa_id, tid))})

        m = re.match(r"^/api/gestor/onboarding/modelo/(\d+)$", path)
        if m and method == "DELETE":
            if not gestor["is_admin"]:
                return _resp(h, 403, {"erro": "Apenas o administrador da empresa configura o onboarding"})
            mo = modelo(conn, empresa_id, int(m.group(1)))
            if not mo:
                return _resp(h, 404, {"erro": "Documento não encontrado"})
            conn.execute("DELETE FROM onboarding_templates WHERE id=? AND empresa_id=?", (mo["id"], empresa_id))
            conn.commit()
            apagar_modelo_pdf(mo["arquivo"])
            return _resp(h, 200, {"ok": True})

        if method == "GET" and path == "/api/gestor/onboarding/lista":
            return _resp(h, 200, {"onboardings": lista_gestor(conn, gestor)})

        m = re.match(r"^/api/gestor/onboarding/candidato/(\d+)$", path)
        if m and method == "GET":
            cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (int(m.group(1)),)).fetchone()
            if not cand or not srv.gestor_ve_candidato(gestor, cand):
                return _resp(h, 404, {"erro": "Candidato não encontrado"})
            lista = [resumo_gestor(conn, ob, gestor) for ob in conn.execute(
                "SELECT * FROM onboardings WHERE candidato_id=? AND empresa_id=? ORDER BY id DESC LIMIT 5",
                (cand["id"], empresa_id)).fetchall()]
            return _resp(h, 200, {"onboardings": lista, "tem_email": bool((cand["email"] or "").strip()),
                                  "pode_enviar": bool(gestor["is_admin"]), "admin": bool(gestor["is_admin"]),
                                  "padroes": padroes_oferta(conn, gestor, cand) if gestor["is_admin"] else None,
                                  "campos_i9_secao2": campos_i9_secao2(),
                                  "padroes_i9": {str(ob["id"]): padroes_i9_secao2(conn, ob, gestor) for ob in conn.execute(
                                      "SELECT * FROM onboardings WHERE candidato_id=? AND empresa_id=? ORDER BY id DESC LIMIT 5",
                                      (cand["id"], empresa_id)).fetchall()}})

        if method == "POST" and path == "/api/gestor/onboarding/oferta":
            if not gestor["is_admin"]:
                return _resp(h, 403, {"erro": "Apenas o administrador da empresa envia a proposta"})
            d = h._body() or {}
            cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (d.get("candidato_id"),)).fetchone()
            if not cand or not srv.gestor_ve_candidato(gestor, cand):
                return _resp(h, 404, {"erro": "Candidato não encontrado"})
            ob, ok, msg = criar(conn, gestor, cand, d, ip)
            return _resp(h, 200, {"ok": True, "id": ob["id"], "link": link(conn, ob), "email_enviado": ok,
                                  "aviso_email": "" if ok else msg})

        m = re.match(r"^/api/gestor/onboarding/(\d+)/(reenviar|cancelar|contratado|revelar|i9-secao2|purgar)$", path)
        if m and method == "POST":
            ob = _ob_do_gestor(conn, gestor, int(m.group(1)))
            if not ob:
                return _resp(h, 404, {"erro": "Onboarding não encontrado"})
            acao = m.group(2)
            if acao == "reenviar":
                if ob["status"] not in ATIVOS:
                    return _resp(h, 400, {"erro": "Este onboarding não está mais em andamento"})
                ok, msg = enviar_convite(conn, ob, gestor["nome"])
                if not ok:
                    return _resp(h, 400, {"erro": "Não foi possível enviar: " + msg})
                return _resp(h, 200, {"ok": True})
            if acao == "cancelar":
                if not gestor["is_admin"]:
                    return _resp(h, 403, {"erro": "Apenas o administrador da empresa cancela o onboarding"})
                cancelar(conn, ob, gestor, ip)
                return _resp(h, 200, {"ok": True})
            if acao == "contratado":
                cand = conn.execute("SELECT * FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
                mover_etapa(conn, cand, ob["candidatura_id"], ("inscrito", "avaliacoes", "entrevista", "proposta"),
                            "contratado", gestor["nome"])
                conn.commit()
                return _resp(h, 200, {"ok": True})
            if acao == "revelar":
                if not gestor["is_admin"]:
                    return _resp(h, 403, {"erro": "Apenas o administrador da empresa pode revelar dados sensíveis"})
                campo = str((h._body() or {}).get("campo") or "")
                valor = sensiveis(conn, ob).get(campo) if ob["sensiveis"] else None
                if not valor:
                    return _resp(h, 404, {"erro": "Dado não encontrado"})
                srv.seguranca.registrar(conn, "revelar_dado_sensivel", gestor, "onboarding:%d campo:%s" % (ob["id"], campo), ip)
                return _resp(h, 200, {"campo": campo, "valor": valor})
            if acao == "i9-secao2":
                i9_secao2(conn, ob, gestor, h._body() or {}, ip)
                return _resp(h, 200, {"ok": True, "onboarding": resumo_gestor(conn, recarregar(conn, ob["id"]), gestor)})
            if acao == "purgar":
                if not gestor["is_admin"]:
                    return _resp(h, 403, {"erro": "Apenas o administrador da empresa pode apagar dados sensíveis"})
                if not resumo_gestor(conn, ob, gestor)["pode_purgar"]:
                    return _resp(h, 400, {"erro": "Os dados ainda estão no prazo de retenção"})
                purgar(conn, ob, gestor, ip)
                return _resp(h, 200, {"ok": True})

        m = re.match(r"^/api/gestor/onboarding/(\d+)/arquivo/(\d+)$", path)
        if m and method == "GET":
            ob = _ob_do_gestor(conn, gestor, int(m.group(1)))
            d = conn.execute("SELECT * FROM onboarding_docs WHERE id=? AND onboarding_id=? AND empresa_id=? AND ativo=1",
                             (int(m.group(2)), ob["id"], empresa_id)).fetchone() if ob else None
            dados = ler_arquivo(conn, d["arquivo"]) if d else None
            if dados is None:
                return _resp(h, 404, {"erro": "Arquivo não encontrado"})
            srv.seguranca.registrar(conn, "baixar_documento_onboarding", gestor,
                                    "onboarding:%d doc:%d" % (ob["id"], d["id"]), ip)
            cand = conn.execute("SELECT nome FROM candidatos WHERE id=?", (ob["candidato_id"],)).fetchone()
            return _enviar_arquivo(h, dados, d["mime"], _nome_download(d, cand["nome"] if cand else ""))
    except ErroOnboarding as e:
        return _erro(h, e)
    except ErroChave as e:
        sys.stderr.write("Onboarding: %s\n" % e)
        return _resp(h, 500, {"erro": "A chave de criptografia dos dados não foi encontrada ou não confere. Fale com o administrador do sistema."})
    return _resp(h, 404, {"erro": "Rota não encontrada"})


# ------------------------------------------------------------- modelos padrão (RASCUNHOS)
# Formato do texto: "# " título, "## " seção, "- " item, "> " aviso; linha em branco
# separa parágrafos. Variáveis: {{nome}}, {{empresa}}, {{cargo}}, {{data_inicio}},
# {{pagamento}}, {{horario}}, {{periodo_experiencia}}, {{prazo}}, {{representante}}, {{data}}.

_AVISO_EN = ("> DRAFT TEMPLATE FOR LEGAL REVIEW. This text is a starting point, not legal advice. Have it reviewed by a "
             "licensed Connecticut employment attorney, adjust it to your company, and remove this note before use.")
_AVISO_PT = ("> RASCUNHO PARA REVISÃO JURÍDICA. Este texto é um ponto de partida, não é aconselhamento jurídico. Peça a "
             "revisão de um advogado trabalhista licenciado em Connecticut, ajuste à sua empresa e remova este aviso antes de usar.")
_AVISO_ES = ("> BORRADOR PARA REVISIÓN LEGAL. Este texto es un punto de partida, no es asesoría legal. Pide la revisión "
             "de un abogado laboral con licencia en Connecticut, ajústalo a tu empresa y elimina esta nota antes de usarlo.")

_OFERTA_W2 = _AVISO_EN + """

# Offer of Employment

{{data}}

Dear {{nome}},

We are happy to offer you the position of {{cargo}} at {{empresa}}. We enjoyed getting to know you and we believe you will be a great addition to our team.

## Position details
- Position: {{cargo}}
- Employment type: W-2 employee
- Start date: {{data_inicio}}
- Pay: {{pagamento}}
- Schedule: {{horario}}
- Introductory period: the first {{periodo_experiencia}} days

Pay is subject to the tax withholdings required by law. You will be paid on the company's regular payday, as required by Connecticut law. If your position is non-exempt, hours worked over 40 in a workweek are paid at one and a half times your regular rate. Travel time between client homes during the workday is paid working time.

## At-will employment
Your employment with {{empresa}} is at will. Either you or the company may end the employment relationship at any time, with or without cause or advance notice. Nothing in this letter, the introductory period, or any other company document creates a promise of employment for a specific length of time.

## Conditions of this offer
This offer depends on:
- Completing your onboarding, including your tax forms and Form I-9 (proof of identity and authorization to work in the United States) within the time required by federal law.
- Reviewing and acknowledging the Employee Handbook.
- For positions that drive between client homes: a valid driver's license and proof of auto insurance.

## Accepting this offer
To accept, please sign this letter electronically by {{prazo}}. If you have any questions, reply to the email that brought you here.

We look forward to working with you.

Sincerely,

{{representante}}
{{empresa}}
"""

_OFERTA_1099 = _AVISO_EN + """

# Independent Contractor Engagement Offer

{{data}}

Dear {{nome}},

{{empresa}} would like to engage you as an independent contractor to provide {{cargo}} services.

## Engagement details
- Services: {{cargo}}
- Expected start date: {{data_inicio}}
- Rate: {{pagamento}}
- Availability notes: {{horario}}

As an independent contractor you are not an employee of {{empresa}}. The company will not withhold income tax, Social Security, or Medicare from your payments, and you are not eligible for employee benefits. You are responsible for your own taxes. The company will send you a Form 1099-NEC when required by law.

You decide how to perform the services, you may accept or decline individual jobs, and you may offer your services to others. The full terms are in the Independent Contractor Agreement included in this onboarding.

## Next steps
To accept, please sign this letter electronically by {{prazo}} and complete the remaining steps, including Form W-9.

Sincerely,

{{representante}}
{{empresa}}
"""

_INTERESSE_EN = _AVISO_EN + """

# Interest Agreement (Preliminary Agreement)

This Interest Agreement records the mutual interest of {{empresa}} ("the Company") and {{nome}} ("the Team Member") in starting a working relationship.

## 1. Purpose
Both parties confirm their interest in working together in the position of {{cargo}}. This agreement formalizes that commitment before the final Employment Contract, which is signed after onboarding is complete and the Team Member's personal documents have been submitted.

## 2. Expected start date
The expected start date is {{data_inicio}}. The date may change by mutual agreement, for example to complete training or required paperwork.

## 3. Introductory period
The first {{periodo_experiencia}} days are an introductory period for training, feedback, and for both sides to confirm the fit. All work during the introductory period is paid, including training time. Completing the introductory period does not change the at-will nature of employment and does not guarantee employment for any length of time.

## 4. Pay
Work will be paid at {{pagamento}}, under the terms of the offer letter.

## 5. Not a fixed-term contract
This agreement is not a contract for a fixed term. Employment remains at will: either party may end it at any time, with or without cause or notice.

## 6. Signatures
By signing electronically, the Team Member confirms the information above. The Company's acceptance was recorded by {{representante}} on behalf of {{empresa}} when this onboarding was sent.
"""

_INTERESSE_PT = _AVISO_PT + """

# Acordo de Interesse (Acordo Preliminar)

Este Acordo de Interesse registra o interesse mútuo da {{empresa}} ("a Empresa") e de {{nome}} ("o Colaborador") em iniciar uma relação de trabalho.

## 1. Finalidade
As partes confirmam o interesse em trabalhar juntas no cargo de {{cargo}}. Este acordo formaliza o compromisso antes do Contrato de Trabalho final, que é assinado depois de concluído o onboarding e entregues os documentos pessoais do Colaborador.

## 2. Data prevista de início
A data prevista de início é {{data_inicio}}. A data pode mudar de comum acordo, por exemplo para concluir o treinamento ou a documentação necessária.

## 3. Período de experiência
Os primeiros {{periodo_experiencia}} dias são um período de experiência para treinamento, retorno e para que as duas partes confirmem a adequação. Todo o trabalho nesse período é pago, inclusive o tempo de treinamento. Concluir o período de experiência não muda a natureza "at will" do vínculo e não garante emprego por nenhum prazo.

## 4. Pagamento
O trabalho será pago a {{pagamento}}, nos termos da carta de proposta.

## 5. Não é contrato por prazo determinado
Este acordo não é um contrato por prazo determinado. O vínculo continua "at will": qualquer das partes pode encerrá-lo a qualquer momento, com ou sem motivo ou aviso.

## 6. Assinaturas
Ao assinar eletronicamente, o Colaborador confirma as informações acima. O aceite da Empresa foi registrado por {{representante}}, em nome da {{empresa}}, quando este onboarding foi enviado.
"""

_INTERESSE_ES = _AVISO_ES + """

# Acuerdo de Interés (Acuerdo Preliminar)

Este Acuerdo de Interés registra el interés mutuo de {{empresa}} ("la Empresa") y de {{nome}} ("el Colaborador") en iniciar una relación de trabajo.

## 1. Propósito
Ambas partes confirman su interés en trabajar juntas en el puesto de {{cargo}}. Este acuerdo formaliza ese compromiso antes del Contrato de Trabajo final, que se firma después de completar la incorporación y de entregar los documentos personales del Colaborador.

## 2. Fecha prevista de inicio
La fecha prevista de inicio es {{data_inicio}}. La fecha puede cambiar de común acuerdo, por ejemplo para completar la capacitación o los trámites necesarios.

## 3. Período de prueba
Los primeros {{periodo_experiencia}} días son un período de prueba para capacitación, comentarios y para que ambas partes confirmen que la relación funciona. Todo el trabajo durante este período se paga, incluido el tiempo de capacitación. Completar el período de prueba no cambia la naturaleza "at will" del empleo y no garantiza empleo por ningún plazo.

## 4. Pago
El trabajo se pagará a {{pagamento}}, según la carta de oferta.

## 5. No es un contrato a plazo fijo
Este acuerdo no es un contrato a plazo fijo. El empleo sigue siendo "at will": cualquiera de las partes puede terminarlo en cualquier momento, con o sin causa o aviso.

## 6. Firmas
Al firmar electrónicamente, el Colaborador confirma la información anterior. La aceptación de la Empresa fue registrada por {{representante}}, en nombre de {{empresa}}, cuando se envió esta incorporación.
"""

_MANUAL_EN = _AVISO_EN + """

# Employee Handbook

## 1. Welcome
Welcome to {{empresa}}. Our clients trust us with their homes, their keys, and their families' privacy. This handbook explains how we work together to earn that trust every day. Please read it carefully and ask your manager about anything that is not clear.

## 2. About this handbook
This handbook describes our main policies and expectations. It is not a contract of employment and it does not promise employment for any length of time. The company may update these policies; when it does, we will tell you. Where Connecticut or federal law gives you greater rights than this handbook, the law applies.

## 3. At-will employment
Employment with {{empresa}} is at will. You or the company may end the employment relationship at any time, with or without cause or advance notice. Only the owner of the company, in a signed writing, can change this.

## 4. Equal employment opportunity
We make employment decisions based on ability and performance. We do not discriminate on the basis of race, color, religious creed, age, sex (including pregnancy), gender identity or expression, sexual orientation, marital status, national origin, ancestry, present or past history of mental disability, intellectual disability, learning disability, physical disability, veteran status, genetic information, status as a victim of domestic violence, or any other characteristic protected by law. We provide reasonable accommodations for disabilities, pregnancy, and sincerely held religious beliefs. Ask your manager or the owner if you need one.

## 5. Anti-harassment and no retaliation
Harassment of any kind, including sexual harassment, is not allowed, whether it comes from a coworker, a manager, a client, or anyone else connected to our work. Sexual harassment is illegal under Connecticut and federal law. Examples include unwelcome sexual advances, requests for sexual favors, sexual jokes or comments, and touching. If you experience or see harassment, including by a client in a client's home, leave the situation if you feel unsafe and report it to your manager or the owner right away. We will investigate promptly and take appropriate action. No one will be punished for making a report in good faith or for taking part in an investigation. You may also contact the Connecticut Commission on Human Rights and Opportunities (CHRO) or the U.S. Equal Employment Opportunity Commission (EEOC). The company provides sexual harassment prevention training as required by Connecticut law.

## 6. Attendance and call-out policy
Clients plan their day around our visits, so reliability matters.
- If you cannot work a scheduled shift, call or text your manager at least 2 hours before your first job, or as soon as possible in an emergency. Telling a coworker is not enough.
- If you will be late, let your manager know as soon as you know.
- Not showing up without notice (no call, no show) is a serious problem. Repeated no call, no show absences may lead to discipline, up to termination.
- Request time off in advance through your manager so we can adjust the routes.

## 7. Scheduling and routes
- Your schedule and route (usually 2 to 3 homes a day) are shared in advance through the company scheduling app.
- Check the app before leaving home each day; routes can change when clients reschedule.
- Follow the order of the route unless your manager approves a change, and tell your manager right away if you are running behind.
- Do not change dates or times directly with clients. Send client requests to the office.

## 8. Timekeeping and breaks
- Record all time worked accurately in the company app: clock in at the start of your workday and clock out at the end. Never work off the clock and never record time for someone else.
- Travel time between client homes during the workday is paid working time.
- Meal break: if you work 7 and a half or more consecutive hours, you will have a 30-minute unpaid meal break, taken after the first 2 hours and before the last 2 hours of your shift, as required by Connecticut law. During the meal break you are completely relieved of duty.
- Short rest breaks are paid.
- Overtime must be approved in advance by your manager, but all overtime worked is always paid.

## 9. Pay and pay days
- Pay days are weekly, as required by Connecticut law, on the day the company announces in writing. You will receive a pay statement showing your hours, pay, and deductions.
- If you believe your pay is wrong, tell your manager or the office right away. We will review it and correct any error promptly.
- The company makes only the deductions required by law or the ones you authorize in writing for your own benefit. The company never deducts money from your pay for damage, breakage, lost items, uniforms, or client complaints.
- Direct deposit is optional. You may choose to be paid by paper check.
- Paid sick leave is provided as required by the Connecticut Paid Sick Leave law (accrual of 1 hour for every 30 hours worked, up to 40 hours per year, once the law applies to the company).

## 10. Dress code and uniform
- The company provides uniform shirts at no cost to you. Wear a clean uniform every workday.
- Wear clean, closed-toe, non-slip shoes. Keep hair tied back and jewelry to a minimum.
- Do not wear perfume, cologne, or scented lotions (see section 11).
- Return company uniforms and equipment when your employment ends. No money will be deducted from your pay for unreturned items.

## 11. Conduct in client homes
- Privacy: do not open drawers, closets, cabinets, mail, documents, or screens unless it is part of the cleaning task. Do not take photos in client homes except the before and after photos the company asks for, and never include people, documents, or personal items in them.
- Keys and alarm codes: keep keys and codes secure at all times. Never label a key with a client's address or name, never share codes, and report a lost key or a code problem to your manager immediately.
- No perfume or scented products: many clients and pets are sensitive to fragrances.
- Phone use: use your phone only for the company app, navigation, and work communication or emergencies. No personal calls, videos, or social media while working in a home.
- Leave everything in place: put items back exactly where you found them.
- Do not bring anyone with you (friends, family, children, or pets) to a client home.
- Do not eat, smoke, or vape in client homes or on their property, and do not use client belongings such as the TV or the kitchen for personal use. You may use the restroom respectfully.
- Pets: follow the client's instructions, keep doors closed so pets do not get out, and never discipline a pet. If an animal seems aggressive, do not enter; step away and call your manager.
- If a client offers you a tip, you may accept it. Tips belong to you.
- While you work for {{empresa}}, do not offer private cleaning services to company clients.

## 12. Safety and chemicals
- Use only company-approved cleaning products and follow the label directions. Safety Data Sheets (SDS) for every product are available from your manager and in the company app; ask if you have questions.
- Never mix chemicals. Mixing bleach with ammonia or acids creates toxic gases.
- Use the gloves and other protective equipment the company provides at no cost to you, and keep rooms ventilated.
- Use a step stool only as instructed. Do not stand on furniture, counters, or tubs, and do not lift anything that is too heavy; ask for help.
- Report any injury to your manager immediately, even a small one. Work injuries are covered by workers' compensation.
- You may refuse a task you believe is unsafe and report safety concerns without retaliation.

## 13. Driving and mileage (for positions that drive)
- Keep a valid driver's license and auto insurance that meets Connecticut requirements, and tell your manager right away about any suspension, accident, or change in your insurance.
- Obey all traffic laws. Connecticut law prohibits using a handheld phone while driving; set your navigation before you start.
- Driving between client homes during the workday is paid working time. The company reimburses mileage between client homes at the rate it announces in writing. Your normal commute from home to the first job and from the last job back home is not reimbursed.
- Follow parking rules at client homes. If there is no legal parking, call your manager.

## 14. Quality checklist and re-cleans
- Follow the cleaning checklist for each home in the company app and take the before and after photos it asks for.
- If a client reports a problem, usually within 24 hours, the company may schedule a re-clean. Time spent on a re-clean is paid.
- Quality feedback is used for coaching and training. It never results in deductions from your pay.

## 15. Damage and breakage reporting
Accidents happen. If something breaks or is damaged, stop, take a photo, and report it to your manager before you leave the home. Never hide damage or try to repair it yourself. The company handles the conversation with the client. The company will not deduct damage from your pay; repeated carelessness may lead to coaching or discipline.

## 16. Confidentiality
Client information is confidential: names, addresses, keys, alarm codes, schedules, and anything you see or hear in a client home. Keep it private during and after your employment. Nothing in this handbook prevents you from discussing your wages, hours, or working conditions with coworkers or others, or from reporting concerns to a government agency.

## 17. Social media
Do not post photos, videos, names, addresses, or details about clients or their homes. Do not speak on behalf of {{empresa}} online without permission. This policy does not limit your right to discuss your wages, hours, or working conditions.

## 18. Drugs and alcohol
Do not work under the influence of alcohol, cannabis, illegal drugs, or misused prescription medication, and do not bring them into client homes or company vehicles. Lawful off-duty cannabis use is handled as provided by Connecticut law, but you must never be impaired at work. If a medication may affect your ability to work safely, tell your manager that you need an accommodation; you do not need to name the medication.

## 19. Complaints and open door
We want to hear from you. Bring questions, concerns, or complaints to your manager or directly to the owner, in person or in writing. No one will be retaliated against for raising a concern in good faith. You also have the right to contact government agencies such as the Connecticut Department of Labor, CHRO, the EEOC, or OSHA.

## 20. Acknowledgment
By signing below, I confirm that I received and read the {{empresa}} Employee Handbook, that I had the chance to ask questions, and that I agree to follow its policies. I understand that the handbook is not a contract, that the company may update it, and that my employment is at will.
"""

_VALORES = {
    "en": _AVISO_EN + """

# Our Core Values

These values describe how we work at {{empresa}}, in every home and with every teammate.

## 1. Respect for every home
We treat each home as if it were our own: with care, privacy, and discretion. We leave everything in its place and protect what our clients trust us with.

## 2. Reliability
We show up on time, follow the route, and do what we promised. When something gets in the way, we communicate early.

## 3. Attention to detail
We follow the checklist, notice the small things, and check our work before we leave. Quality is what clients remember.

## 4. Honesty and integrity
We tell the truth, report problems and accidents right away, and do the right thing even when no one is watching.

## 5. Teamwork and growth
We help each other, share what we learn, welcome feedback, and keep improving together.

## Your statement
In the box below, write a short statement about how you plan to live these values in your work.
""",
    "pt": _AVISO_PT + """

# Nossos Valores

Estes valores descrevem como trabalhamos na {{empresa}}, em cada casa e com cada colega.

## 1. Respeito por cada casa
Tratamos cada casa como se fosse a nossa: com cuidado, privacidade e discrição. Deixamos tudo no lugar e protegemos o que os clientes nos confiam.

## 2. Confiabilidade
Chegamos no horário, seguimos a rota e cumprimos o combinado. Quando algo atrapalha, avisamos cedo.

## 3. Atenção aos detalhes
Seguimos o checklist, reparamos nos pequenos detalhes e conferimos o trabalho antes de sair. Qualidade é o que o cliente lembra.

## 4. Honestidade e integridade
Falamos a verdade, avisamos na hora sobre problemas e acidentes e fazemos o certo mesmo quando ninguém está olhando.

## 5. Trabalho em equipe e crescimento
Ajudamos uns aos outros, compartilhamos o que aprendemos, recebemos bem o retorno e melhoramos juntos.

## Sua declaração
No campo abaixo, escreva uma declaração curta sobre como você pretende viver esses valores no seu trabalho.
""",
    "es": _AVISO_ES + """

# Nuestros Valores

Estos valores describen cómo trabajamos en {{empresa}}, en cada casa y con cada compañero.

## 1. Respeto por cada hogar
Tratamos cada casa como si fuera la nuestra: con cuidado, privacidad y discreción. Dejamos todo en su lugar y protegemos lo que los clientes nos confían.

## 2. Confiabilidad
Llegamos a tiempo, seguimos la ruta y cumplimos lo prometido. Cuando algo se interpone, avisamos con anticipación.

## 3. Atención al detalle
Seguimos la lista de verificación, notamos los pequeños detalles y revisamos el trabajo antes de salir. La calidad es lo que el cliente recuerda.

## 4. Honestidad e integridad
Decimos la verdad, reportamos de inmediato los problemas y accidentes y hacemos lo correcto aunque nadie nos vea.

## 5. Trabajo en equipo y crecimiento
Nos ayudamos, compartimos lo que aprendemos, recibimos bien los comentarios y mejoramos juntos.

## Tu declaración
En el espacio de abajo, escribe una declaración breve sobre cómo piensas vivir estos valores en tu trabajo.
""",
}

_CONTRATO_W2 = _AVISO_EN + """

# Employment Contract

This Employment Contract is made on {{data}} between {{empresa}} ("the Company") and {{nome}} ("the Employee").

## 1. Position and duties
The Employee is hired as {{cargo}}. The Employee will perform residential cleaning services at client homes assigned by the Company, following the Company's checklists, safety rules, and the Employee Handbook, and other reasonable duties related to the position.

## 2. Start date
Employment begins on {{data_inicio}}.

## 3. At-will employment
Employment is at will. Either party may end it at any time, with or without cause or advance notice. Nothing in this contract promises employment for a specific length of time.

## 4. Pay
- The Employee will be paid {{pagamento}}, less the withholdings required by law.
- Pay is issued weekly on the Company's regular payday, as required by Connecticut law.
- If the position is non-exempt, hours worked over 40 in a workweek are paid at one and a half times the regular rate.
- Travel time between client homes during the workday is paid working time. Approved mileage between client homes is reimbursed at the Company's announced rate.
- The Company makes only deductions required by law or authorized by the Employee in writing for the Employee's benefit. The Company does not deduct for damage, breakage, lost items, or uniforms.

## 5. Schedule
{{horario}}

Schedules and routes are shared in advance through the Company's scheduling app and may change based on client needs.

## 6. Introductory period
The first {{periodo_experiencia}} days are an introductory period for training and feedback. Completing it does not change the at-will nature of employment.

## 7. Company policies
The Employee agrees to follow the Employee Handbook and the Company's written policies, as updated from time to time.

## 8. Confidentiality
The Employee will keep confidential all client information (names, addresses, keys, alarm codes, schedules, and anything seen or heard in client homes) and the Company's non-public business information, during and after employment. Nothing in this contract prevents the Employee from discussing wages, hours, or working conditions, or from reporting concerns to a government agency.

## 9. Company property
When employment ends, or whenever the Company asks, the Employee will promptly return all Company and client property, including keys, access cards, uniforms, equipment, and any client information. No amount will be deducted from wages for unreturned items.

## 10. Employee information
The Employee confirms that the personal information provided during onboarding is true and agrees to keep it up to date.

## 11. Governing law
This contract is governed by the laws of the State of Connecticut.

## 12. Entire agreement
This contract, the offer letter, and the Employee Handbook acknowledgment are the full understanding between the parties about the terms of employment. Changes must be in writing and signed by the Employee and the owner of the Company.

## Signatures
The Company's signature was recorded by {{representante}} on behalf of {{empresa}} when this onboarding was sent. The Employee signs electronically below.
"""

_CONTRATO_1099 = _AVISO_EN + """

> Legal note for the company: Connecticut uses the "ABC test" for unemployment insurance. A worker is an independent contractor only if (A) they are free from the company's control and direction, (B) the work is outside the usual course of the company's business or performed outside all of its places of business, and (C) they are customarily engaged in an independently established trade or business. Residential cleaners who clean homes for a cleaning company often fail part B. Confirm the classification with an attorney before using this agreement.

# Independent Contractor Agreement

This Independent Contractor Agreement is made on {{data}} between {{empresa}} ("the Company") and {{nome}} ("the Contractor").

## 1. Services
The Contractor will provide {{cargo}} services for jobs the Contractor chooses to accept. The Contractor decides how, when, and by what methods the services are performed, consistent with the results agreed for each job and with client access and safety requirements.

## 2. Term
This agreement starts on {{data_inicio}} and continues until either party ends it under section 9.

## 3. Independent contractor status
The Contractor is an independent contractor, not an employee, partner, or agent of the Company. The Contractor:
- may accept or decline any job;
- may offer services to other businesses and clients, including competitors;
- controls the manner and means of the work and sets their own hours for accepted jobs;
- is not eligible for employee benefits, unemployment insurance, or workers' compensation through the Company.

## 4. Payment and invoicing
- The Company will pay the Contractor {{pagamento}} for completed services.
- The Contractor will send invoices listing the jobs completed. The Company will pay correct invoices within 15 days of receiving them.
- Any reimbursement of expenses must be agreed in writing in advance.

## 5. Taxes
The Company will not withhold income tax, Social Security, Medicare, or any other taxes. The Contractor is responsible for all taxes on payments received. The Contractor will provide a completed Form W-9, and the Company will issue Form 1099-NEC when required.

## 6. Tools and supplies
The Contractor provides their own tools, equipment, supplies, and transportation, unless the parties agree otherwise in writing for a specific client.

## 7. Insurance
The Contractor will maintain general liability insurance appropriate for residential cleaning work and, if the Contractor uses a vehicle, auto insurance that meets Connecticut requirements, and will provide proof of insurance when asked.

## 8. Client homes and confidentiality
The Contractor will respect client privacy and property, keep keys and alarm codes secure, and report any damage right away. The Contractor will keep confidential all client information and the Company's non-public business information, during and after this agreement. Nothing in this agreement prevents the Contractor from reporting concerns to a government agency.

## 9. Termination
Either party may end this agreement at any time with 7 days' written notice, or immediately if the other party materially breaches it. The Company will pay for services completed before the end date. The Contractor will promptly return any client keys or property.

## 10. No restrictions after the agreement
This agreement does not contain a non-compete. Nothing in it prevents the Contractor from working in the cleaning industry after the agreement ends.

## 11. Governing law
This agreement is governed by the laws of the State of Connecticut.

## 12. Entire agreement
This agreement and the engagement offer are the full understanding between the parties. Changes must be in writing and signed by both parties.

## Signatures
The Company's signature was recorded by {{representante}} on behalf of {{empresa}} when this onboarding was sent. The Contractor signs electronically below.
"""

MODELOS_PADRAO = [
    {"chave": "offer_letter", "categoria": "oferta", "aplica": "w2",
     "titulos": {"en": "Offer Letter", "pt": "Carta de proposta", "es": "Carta de oferta"},
     "textos": {"en": _OFERTA_W2}},
    {"chave": "engagement_offer", "categoria": "oferta", "aplica": "1099",
     "titulos": {"en": "Contractor Engagement Offer", "pt": "Proposta de prestação de serviços",
                 "es": "Oferta de contratación independiente"},
     "textos": {"en": _OFERTA_1099}},
    {"chave": "interest_agreement", "categoria": "documento", "aplica": "w2",
     "titulos": {"en": "Interest Agreement", "pt": "Acordo de Interesse", "es": "Acuerdo de Interés"},
     "textos": {"en": _INTERESSE_EN, "pt": _INTERESSE_PT, "es": _INTERESSE_ES}},
    {"chave": "employee_handbook", "categoria": "documento", "aplica": "w2",
     "titulos": {"en": "Employee Handbook (acknowledgment)", "pt": "Manual do Colaborador (ciência)",
                 "es": "Manual del Empleado (acuse de recibo)"},
     "textos": {"en": _MANUAL_EN}},
    {"chave": "core_values", "categoria": "documento", "aplica": "ambos", "declaracao": True,
     "titulos": {"en": "Core Values", "pt": "Nossos Valores", "es": "Nuestros Valores"},
     "textos": _VALORES},
    {"chave": "employment_contract", "categoria": "documento", "aplica": "w2",
     "titulos": {"en": "Employment Contract", "pt": "Contrato de Trabalho", "es": "Contrato de Trabajo"},
     "textos": {"en": _CONTRATO_W2}},
    {"chave": "contractor_agreement", "categoria": "documento", "aplica": "1099",
     "titulos": {"en": "Independent Contractor Agreement", "pt": "Contrato de Prestador Independente",
                 "es": "Contrato de Contratista Independiente"},
     "textos": {"en": _CONTRATO_1099}},
]
