"""
Operação da Bússola: backups externos cifrados, saúde do servidor e alertas ao dono.

1. Backup externo (S3 compatível: Oracle Object Storage, Backblaze B2, AWS S3,
   Cloudflare R2). O dono informa endpoint, região, bucket, chave de acesso e
   segredo no painel do dono (aba Sistema) e define UMA frase de backup.
   Todo dia, depois do backup_diario() local, a rotina deste módulo cifra e
   envia: a cópia do banco (rh.db), um tar da pasta uploads/ e, se existir, a
   chave_dados.key. A cifra usa Fernet (cryptography) com chave derivada da
   frase por PBKDF2-HMAC-SHA256 (sal aleatório por arquivo, gravado no
   cabeçalho). Assim, para restaurar, basta a frase: nada de segredo do
   servidor é necessário.
   A frase precisa estar disponível para a rotina diária, então fica guardada
   cifrada com a chave da máquina backups.key (0600, na pasta do app, fora de
   public/). O segredo do bucket também. A config guarda ainda um verificador
   com sal da frase (nunca a frase em claro). O dono deve guardar uma cópia
   da backups.key junto com a chave_dados.key (ver DEPLOY.md).
   Retenção remota: 30 dias diários + 12 mensais (o último dia de cada mês).
   Assinatura AWS Signature V4 feita só com a biblioteca padrão.
2. Saúde e alertas: GET /api/saude (público, sem dados sensíveis); erros não
   tratados em api() vão para erros_servidor e geram e-mail ao dono (no
   máximo um a cada 30 minutos por assinatura de erro) e um resumo diário.
   Uma thread verifica a cada 15 minutos: disco acima de 85%, backup local
   com mais de 26 horas, ligação de voz presa há mais de 60 minutos, falhas
   repetidas da ElevenLabs/Twilio (5 ou mais erros em voz_chamadas na última
   hora) e backup externo atrasado. Um e-mail por condição a cada 6 horas.

Segredos nunca vão para log, erro, resposta ou auditoria.

Restaurar fora do servidor (pede a frase sem eco):
    python3 operacao.py decifrar rh.db.enc rh.db
"""
import base64
import datetime
import getpass
import hashlib
import hmac
import io
import json
import os
import re
import shutil
import struct
import sys
import tarfile
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover - servidor sem python3-cryptography
    Fernet = None

    class InvalidToken(Exception):
        pass

srv = None  # módulo do servidor, injetado por ligar()

INICIO = time.time()
TIMEOUT = 60
ITERACOES = 200000
MAGICO = b"BSLBKP1\n"
BLOCO = 1024 * 1024
DIAS_DIARIOS = 30
MESES_MENSAIS = 12
ENVIO_EM_SEGUNDO_PLANO = True    # os testes desligam para conferir os e-mails na hora
BACKUP_EM_SEGUNDO_PLANO = True   # idem para "Fazer backup agora"
INTERVALO_MONITOR = 15 * 60
PRIMEIRA_ESPERA = 60
JANELA_ERRO = 30 * 60
JANELA_CONDICAO = 6 * 3600
LIMITE_DISCO = 0.85
HORAS_BACKUP_LOCAL = 26
HORAS_BACKUP_REMOTO = 50
MINUTOS_VOZ_PRESA = 60
FALHAS_VOZ_HORA = 5
IDIOMAS = ("pt", "en", "es")
ARQUIVO_CHAVE_MAQUINA = "backups.key"

_lock_backup = threading.Lock()
_lock_alerta = threading.Lock()
_versao_cache = None

RE_ENDPOINT = re.compile(r"^https://[A-Za-z0-9.-]+(:\d{1,5})?$|^http://(localhost|127\.0\.0\.1)(:\d{1,5})?$")
RE_REGIAO = re.compile(r"^[a-z0-9-]{1,40}$")
RE_BUCKET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
RE_PREFIXO = re.compile(r"^[A-Za-z0-9._/-]{0,100}$")
RE_DIA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ErroOperacao(Exception):
    """Mensagem em português (traduzida por erros_i18n) e status HTTP."""

    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def ligar(modulo_servidor):
    global srv
    srv = modulo_servidor


def init_operacao(c):
    """Tabelas do módulo. Chamado dentro de init_db() com o cursor aberto."""
    c.execute(
        "CREATE TABLE IF NOT EXISTS erros_servidor ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " quando TEXT DEFAULT (datetime('now')),"
        " rota TEXT DEFAULT '',"
        " metodo TEXT DEFAULT '',"
        " tipo TEXT DEFAULT '',"
        " mensagem TEXT DEFAULT '',"
        " traceback TEXT DEFAULT '',"
        " assinatura TEXT DEFAULT '',"
        " resolvido INTEGER DEFAULT 0,"
        " resolvido_em TEXT DEFAULT '')"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_erros_servidor_res ON erros_servidor(resolvido, id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_erros_servidor_assin ON erros_servidor(assinatura)")
    c.execute(
        "CREATE TABLE IF NOT EXISTS alertas_operacao ("
        " chave TEXT PRIMARY KEY,"
        " ultimo REAL DEFAULT 0,"
        " contagem INTEGER DEFAULT 0)"
    )


def iniciar():
    """Sobe a thread de monitoramento (chamado em main())."""
    if os.environ.get("OPERACAO_MONITOR_DESLIGADO") == "1":
        return
    threading.Thread(target=rotina_operacao, daemon=True).start()


# ================================================================ utilidades

def _lang(v):
    v = (v or "").strip().lower()[:2]
    return v if v in IDIOMAS else "pt"


def _cfg(conn, chave):
    return srv.config_get(conn, chave) or ""


def _agora_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_RE_TOKEN = re.compile(r"\b(?=[A-Za-z0-9_\-+/=]*\d)(?=[A-Za-z0-9_\-+/=]*[A-Za-z])[A-Za-z0-9_\-+/=]{24,}\b")


def redigir(texto):
    """Mascara e-mails e sequências com cara de token/segredo."""
    texto = _RE_EMAIL.sub("[email]", texto or "")
    return _RE_TOKEN.sub("[redigido]", texto)


def _normalizar_rota(rota):
    rota = re.sub(r"/[A-Za-z0-9_-]{16,}", "/:token", rota or "")
    return re.sub(r"/\d+", "/:id", rota)[:200]


# ================================================================ cifra

def cripto_disponivel():
    return Fernet is not None


def _exigir_cripto():
    if Fernet is None:
        raise ErroOperacao("Instale python3-cryptography no servidor para usar o backup externo")


def derivar_chave(frase, sal, iteracoes=None):
    dk = hashlib.pbkdf2_hmac("sha256", frase.encode("utf-8"), sal, iteracoes or ITERACOES, dklen=32)
    return base64.urlsafe_b64encode(dk)


def cifrar_fluxo(entrada, saida, frase):
    """Formato: MAGICO + sal(16) + iterações(4) + blocos [tamanho(4) + token Fernet] + 0000."""
    _exigir_cripto()
    sal = os.urandom(16)
    f = Fernet(derivar_chave(frase, sal, ITERACOES))
    saida.write(MAGICO + sal + struct.pack(">I", ITERACOES))
    while True:
        pedaco = entrada.read(BLOCO)
        if not pedaco:
            break
        token = f.encrypt(pedaco)
        saida.write(struct.pack(">I", len(token)) + token)
    saida.write(struct.pack(">I", 0))


def decifrar_fluxo(entrada, saida, frase):
    _exigir_cripto()
    cab = entrada.read(len(MAGICO) + 20)
    if len(cab) != len(MAGICO) + 20 or not cab.startswith(MAGICO):
        raise ErroOperacao("Arquivo de backup inválido")
    sal = cab[len(MAGICO):len(MAGICO) + 16]
    (iteracoes,) = struct.unpack(">I", cab[-4:])
    if not 1000 <= iteracoes <= 10000000:
        raise ErroOperacao("Arquivo de backup inválido")
    f = Fernet(derivar_chave(frase, sal, iteracoes))
    while True:
        t = entrada.read(4)
        if len(t) != 4:
            raise ErroOperacao("Arquivo de backup incompleto")
        (n,) = struct.unpack(">I", t)
        if n == 0:
            return
        if n > BLOCO * 2 + 4096:
            raise ErroOperacao("Arquivo de backup inválido")
        token = entrada.read(n)
        if len(token) != n:
            raise ErroOperacao("Arquivo de backup incompleto")
        try:
            saida.write(f.decrypt(token))
        except InvalidToken:
            raise ErroOperacao("Frase de backup incorreta ou arquivo corrompido")


def cifrar_bytes(dados, frase):
    out = io.BytesIO()
    cifrar_fluxo(io.BytesIO(dados), out, frase)
    return out.getvalue()


def decifrar_bytes(dados, frase):
    out = io.BytesIO()
    decifrar_fluxo(io.BytesIO(dados), out, frase)
    return out.getvalue()


def cifrar_arquivo(origem, destino, frase):
    with open(origem, "rb") as e, open(destino, "wb") as s:
        cifrar_fluxo(e, s, frase)


def decifrar_arquivo(origem, destino, frase):
    with open(origem, "rb") as e, open(destino, "wb") as s:
        decifrar_fluxo(e, s, frase)


# ---------------------------------------------------- chave da máquina (backups.key)

def caminho_chave_maquina():
    return os.path.join(srv.BASE_DIR, ARQUIVO_CHAVE_MAQUINA)


def _fernet_maquina(criar=False):
    _exigir_cripto()
    caminho = caminho_chave_maquina()
    if not os.path.isfile(caminho):
        if not criar:
            return None
        try:
            fd = os.open(caminho, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as fh:
                fh.write(Fernet.generate_key())
        except FileExistsError:
            pass
    with open(caminho, "rb") as fh:
        return Fernet(fh.read().strip())


def _guardar_segredo(conn, chave, valor):
    f = _fernet_maquina(criar=True)
    srv.config_set(conn, chave, "f1:" + f.encrypt(valor.encode("utf-8")).decode("ascii"))


def _ler_segredo(conn, chave):
    v = _cfg(conn, chave)
    if not v.startswith("f1:"):
        return ""
    f = _fernet_maquina(criar=False)
    if f is None:
        raise ErroOperacao("A chave da máquina (backups.key) não foi encontrada. Informe de novo o segredo e a frase de backup.")
    try:
        return f.decrypt(v[3:].encode("ascii")).decode("utf-8")
    except InvalidToken:
        raise ErroOperacao("A chave da máquina (backups.key) não confere. Informe de novo o segredo e a frase de backup.")


# ================================================================ S3 (Signature V4)

def _enc(s, seguro="-_.~"):
    return urllib.parse.quote(s, safe=seguro)


def assinar_v4(metodo, url, cabecalhos, hash_corpo, chave_acesso, segredo, regiao, agora=None, servico="s3"):
    """Devolve os cabeçalhos (com Authorization) para a requisição. url já codificada."""
    agora = agora or datetime.datetime.utcnow()
    amz_data = agora.strftime("%Y%m%dT%H%M%SZ")
    dia = amz_data[:8]
    p = urllib.parse.urlsplit(url)
    cab = {k.lower(): str(v) for k, v in (cabecalhos or {}).items()}
    cab["host"] = p.netloc
    cab["x-amz-date"] = amz_data
    cab["x-amz-content-sha256"] = hash_corpo
    pares = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    consulta = "&".join("%s=%s" % (_enc(k), _enc(v)) for k, v in sorted(pares))
    nomes = sorted(cab)
    canon_cab = "".join("%s:%s\n" % (n, " ".join(cab[n].strip().split())) for n in nomes)
    assinados = ";".join(nomes)
    pedido = "\n".join([metodo, p.path or "/", consulta, canon_cab, assinados, hash_corpo])
    escopo = "%s/%s/%s/aws4_request" % (dia, regiao, servico)
    texto = "\n".join(["AWS4-HMAC-SHA256", amz_data, escopo,
                       hashlib.sha256(pedido.encode("utf-8")).hexdigest()])

    def _h(chave, msg):
        return hmac.new(chave, msg.encode("utf-8"), hashlib.sha256).digest()

    k = _h(_h(_h(_h(("AWS4" + segredo).encode("utf-8"), dia), regiao), servico), "aws4_request")
    assinatura = hmac.new(k, texto.encode("utf-8"), hashlib.sha256).hexdigest()
    cab["authorization"] = "AWS4-HMAC-SHA256 Credential=%s/%s, SignedHeaders=%s, Signature=%s" % (
        chave_acesso, escopo, assinados, assinatura)
    return cab


def _urlopen(req, timeout):
    """Ponto único de rede (os testes trocam por um bucket falso)."""
    return urllib.request.urlopen(req, timeout=timeout)


VAZIO = hashlib.sha256(b"").hexdigest()


class S3:
    def __init__(self, endpoint, regiao, bucket, chave_acesso, segredo):
        self.endpoint = endpoint.rstrip("/")
        self.regiao = regiao
        self.bucket = bucket
        self.chave_acesso = chave_acesso
        self.segredo = segredo

    def _url(self, chave="", consulta=None):
        u = self.endpoint + "/" + _enc(self.bucket)
        if chave:
            u += "/" + _enc(chave, "-_.~/")
        if consulta:
            u += "?" + "&".join("%s=%s" % (_enc(k), _enc(v)) for k, v in sorted(consulta.items()))
        return u

    def _pedir(self, metodo, url, corpo=None, hash_corpo=VAZIO, cabecalhos=None):
        cab = assinar_v4(metodo, url, cabecalhos or {}, hash_corpo, self.chave_acesso, self.segredo, self.regiao)
        cab.pop("host", None)
        req = urllib.request.Request(url, data=corpo, method=metodo, headers=cab)
        try:
            return _urlopen(req, TIMEOUT)
        except urllib.error.HTTPError as e:
            try:
                corpo_erro = e.read(4096)
            except Exception:  # noqa: BLE001
                corpo_erro = b""
            raise ErroOperacao("Erro no armazenamento: " + _descrever_erro_s3(e.code, corpo_erro))
        except (urllib.error.URLError, OSError, ValueError):
            raise ErroOperacao("Sem conexão com o armazenamento. Confira o endpoint.")

    def put_bytes(self, chave, dados):
        h = hashlib.sha256(dados).hexdigest()
        with self._pedir("PUT", self._url(chave), dados, h,
                         {"Content-Length": str(len(dados)), "Content-Type": "application/octet-stream"}) as r:
            r.read()

    def put_arquivo(self, chave, caminho):
        h = hashlib.sha256()
        with open(caminho, "rb") as fh:
            for pedaco in iter(lambda: fh.read(BLOCO), b""):
                h.update(pedaco)
        tamanho = os.path.getsize(caminho)
        with open(caminho, "rb") as fh:
            with self._pedir("PUT", self._url(chave), fh, h.hexdigest(),
                             {"Content-Length": str(tamanho), "Content-Type": "application/octet-stream"}) as r:
                r.read()
        return tamanho

    def get_bytes(self, chave):
        with self._pedir("GET", self._url(chave)) as r:
            return r.read()

    def get_para_arquivo(self, chave, caminho):
        with self._pedir("GET", self._url(chave)) as r, open(caminho, "wb") as fh:
            for pedaco in iter(lambda: r.read(BLOCO), b""):
                fh.write(pedaco)

    def apagar(self, chave):
        with self._pedir("DELETE", self._url(chave)) as r:
            r.read()

    def listar(self, prefixo):
        objetos, token = [], None
        for _ in range(200):
            q = {"list-type": "2", "prefix": prefixo, "max-keys": "1000"}
            if token:
                q["continuation-token"] = token
            with self._pedir("GET", self._url("", q)) as r:
                raiz = ET.fromstring(r.read())
            ns = ""
            m = re.match(r"\{.*\}", raiz.tag)
            if m:
                ns = m.group(0)
            for c in raiz.findall(ns + "Contents"):
                objetos.append({
                    "chave": c.findtext(ns + "Key") or "",
                    "tamanho": int(c.findtext(ns + "Size") or 0),
                    "modificado": c.findtext(ns + "LastModified") or "",
                })
            if (raiz.findtext(ns + "IsTruncated") or "").lower() != "true":
                break
            token = raiz.findtext(ns + "NextContinuationToken")
            if not token:
                break
        return objetos


def _descrever_erro_s3(status, corpo):
    codigo = mensagem = ""
    try:
        raiz = ET.fromstring(corpo)
        codigo = raiz.findtext("Code") or ""
        mensagem = raiz.findtext("Message") or ""
    except ET.ParseError:
        pass
    partes = ["HTTP %s" % status]
    if codigo:
        partes.append(codigo)
    if mensagem:
        partes.append(mensagem[:200])
    return redigir(" ".join(partes))


# ================================================================ configuração do backup

CHAVES_CFG = ("op_s3_endpoint", "op_s3_regiao", "op_s3_bucket", "op_s3_prefixo", "op_s3_chave_acesso")


def _prefixo(conn):
    p = _cfg(conn, "op_s3_prefixo")
    return p if p else "bussola/"


def config_backup(conn):
    acesso = _cfg(conn, "op_s3_chave_acesso")
    return {
        "endpoint": _cfg(conn, "op_s3_endpoint"),
        "regiao": _cfg(conn, "op_s3_regiao"),
        "bucket": _cfg(conn, "op_s3_bucket"),
        "prefixo": _prefixo(conn),
        "chave_acesso_final": acesso[-4:] if acesso else "",
        "tem_segredo": _cfg(conn, "op_s3_segredo").startswith("f1:"),
        "tem_frase": bool(_cfg(conn, "op_backup_verificador")),
        "chave_maquina_existe": os.path.isfile(caminho_chave_maquina()),
        "cripto_disponivel": cripto_disponivel(),
        "ultimo_ok": _cfg(conn, "op_backup_ultimo_ok"),
        "ultimo_dia": _cfg(conn, "op_backup_ultimo_dia"),
        "tamanho": int(_cfg(conn, "op_backup_tamanho") or 0),
        "ultimo_erro": _cfg(conn, "op_backup_ultimo_erro"),
        "ultima_tentativa": _cfg(conn, "op_backup_ultima_tentativa"),
        "rodando": _lock_backup.locked(),
    }


def configurado(conn):
    return all(_cfg(conn, k) for k in ("op_s3_endpoint", "op_s3_regiao", "op_s3_bucket", "op_s3_chave_acesso")) \
        and _cfg(conn, "op_s3_segredo").startswith("f1:") and bool(_cfg(conn, "op_backup_verificador"))


def salvar_config(conn, d):
    _exigir_cripto()
    endpoint = str(d.get("endpoint") or "").strip().rstrip("/")
    regiao = str(d.get("regiao") or "").strip()
    bucket = str(d.get("bucket") or "").strip()
    prefixo = str(d.get("prefixo") if d.get("prefixo") is not None else "bussola/").strip().lstrip("/")
    acesso = str(d.get("chave_acesso") or "").strip()
    segredo = str(d.get("segredo") or "").strip()
    if not RE_ENDPOINT.match(endpoint):
        raise ErroOperacao("Endpoint inválido (use https://...)")
    if not RE_REGIAO.match(regiao):
        raise ErroOperacao("Região inválida")
    if not RE_BUCKET.match(bucket):
        raise ErroOperacao("Nome do bucket inválido")
    if prefixo and not prefixo.endswith("/"):
        prefixo += "/"
    if not RE_PREFIXO.match(prefixo) or ".." in prefixo:
        raise ErroOperacao("Prefixo inválido")
    if not acesso:
        acesso = _cfg(conn, "op_s3_chave_acesso")
    if not acesso or len(acesso) > 128 or any(ch.isspace() for ch in acesso):
        raise ErroOperacao("Chave de acesso inválida")
    if segredo:
        if len(segredo) > 256 or any(ch.isspace() for ch in segredo):
            raise ErroOperacao("Segredo inválido")
        _guardar_segredo(conn, "op_s3_segredo", segredo)
    elif not _cfg(conn, "op_s3_segredo").startswith("f1:"):
        raise ErroOperacao("Informe o segredo da chave de acesso")
    srv.config_set(conn, "op_s3_endpoint", endpoint)
    srv.config_set(conn, "op_s3_regiao", regiao)
    srv.config_set(conn, "op_s3_bucket", bucket)
    srv.config_set(conn, "op_s3_prefixo", prefixo or "bussola/")
    srv.config_set(conn, "op_s3_chave_acesso", acesso)
    conn.commit()


def definir_frase(conn, frase, atual=""):
    """Define a frase de backup. Se já existe, exige a atual (também serve para
    regravar a frase depois de trocar a backups.key)."""
    _exigir_cripto()
    frase = str(frase or "")
    if len(frase) < 12:
        raise ErroOperacao("A frase de backup deve ter ao menos 12 caracteres")
    verificador = _cfg(conn, "op_backup_verificador")
    if verificador and not srv.senha_confere(str(atual or ""), verificador):
        raise ErroOperacao("Frase de backup atual incorreta")
    _guardar_segredo(conn, "op_backup_frase", frase)
    srv.config_set(conn, "op_backup_verificador", srv.hash_senha(frase))
    conn.commit()


def _cliente(conn):
    _exigir_cripto()
    if not all(_cfg(conn, k) for k in ("op_s3_endpoint", "op_s3_regiao", "op_s3_bucket", "op_s3_chave_acesso")):
        raise ErroOperacao("Configure o armazenamento externo primeiro")
    segredo = _ler_segredo(conn, "op_s3_segredo")
    if not segredo:
        raise ErroOperacao("Configure o armazenamento externo primeiro")
    return S3(_cfg(conn, "op_s3_endpoint"), _cfg(conn, "op_s3_regiao"), _cfg(conn, "op_s3_bucket"),
              _cfg(conn, "op_s3_chave_acesso"), segredo)


def _frase(conn):
    frase = _ler_segredo(conn, "op_backup_frase")
    if not frase:
        raise ErroOperacao("Defina a frase de backup primeiro")
    return frase


def testar_conexao(conn):
    s3 = _cliente(conn)
    chave = _prefixo(conn) + "teste-conexao.txt"
    conteudo = ("bussola " + _agora_iso()).encode("utf-8")
    s3.put_bytes(chave, conteudo)
    nomes = [o["chave"] for o in s3.listar(_prefixo(conn))]
    lido = s3.get_bytes(chave)
    s3.apagar(chave)
    if chave not in nomes or lido != conteudo:
        raise ErroOperacao("O teste de conexão falhou: o arquivo de teste não voltou igual")
    return {"ok": True}


# ================================================================ backup diário

def _backups_locais():
    pasta = srv.BACKUP_DIR
    if not os.path.isdir(pasta):
        return []
    return sorted(f for f in os.listdir(pasta) if f.startswith("rh-") and f.endswith(".db")
                  and RE_DIA.match(f[3:-3]))


def ultimo_backup_local():
    """(caminho, dia, mtime) do backup local mais recente, ou None."""
    lista = _backups_locais()
    if not lista:
        return None
    nome = lista[-1]
    caminho = os.path.join(srv.BACKUP_DIR, nome)
    return caminho, nome[3:-3], os.path.getmtime(caminho)


def _tar_uploads(destino):
    with tarfile.open(destino, "w") as tar:
        if os.path.isdir(srv.UPLOAD_DIR):
            tar.add(srv.UPLOAD_DIR, arcname="uploads")


def _mensagem_segura(exc):
    if isinstance(exc, ErroOperacao):
        return exc.mensagem[:300]
    return redigir("%s: %s" % (type(exc).__name__, exc))[:300]


def _registrar_status(campos):
    conn = srv.db()
    try:
        for k, v in campos.items():
            srv.config_set(conn, k, v)
        conn.commit()
    finally:
        conn.close()


def executar_backup():
    """Cifra e envia o backup do dia. Devolve um resumo; levanta ErroOperacao."""
    if not _lock_backup.acquire(blocking=False):
        raise ErroOperacao("Já existe um backup em andamento", 409)
    pasta_tmp = None
    try:
        conn = srv.db()
        try:
            s3 = _cliente(conn)
            frase = _frase(conn)
            prefixo = _prefixo(conn)
        finally:
            conn.close()
        hoje = datetime.date.today().isoformat()
        local = ultimo_backup_local()
        if not local or local[1] != hoje:
            srv.backup_diario()
            local = ultimo_backup_local()
        if not local:
            raise ErroOperacao("Nenhum backup local encontrado")
        caminho_db, dia, _ = local
        os.makedirs(srv.BACKUP_DIR, exist_ok=True)
        pasta_tmp = tempfile.mkdtemp(prefix=".remoto-", dir=srv.BACKUP_DIR)
        arquivos = [("rh.db.enc", caminho_db)]
        tar = os.path.join(pasta_tmp, "uploads.tar")
        _tar_uploads(tar)
        arquivos.append(("uploads.tar.enc", tar))
        chave_dados = os.path.join(srv.BASE_DIR, "chave_dados.key")
        if os.path.isfile(chave_dados):
            arquivos.append(("chave_dados.key.enc", chave_dados))
        total = 0
        enviados = []
        for nome, origem in arquivos:
            cifrado = os.path.join(pasta_tmp, nome)
            cifrar_arquivo(origem, cifrado, frase)
            total += s3.put_arquivo(prefixo + "diario/" + dia + "/" + nome, cifrado)
            enviados.append(nome)
        apagados = podar(s3, prefixo)
        _registrar_status({
            "op_backup_ultimo_ok": _agora_iso(), "op_backup_ultimo_dia": dia,
            "op_backup_tamanho": str(total), "op_backup_ultimo_erro": "",
            "op_backup_ultima_tentativa": _agora_iso(),
        })
        return {"dia": dia, "tamanho": total, "arquivos": enviados, "apagados": apagados}
    except Exception as exc:  # noqa: BLE001
        try:
            _registrar_status({"op_backup_ultimo_erro": _mensagem_segura(exc),
                               "op_backup_ultima_tentativa": _agora_iso()})
        except Exception:  # noqa: BLE001
            pass
        if isinstance(exc, ErroOperacao):
            raise
        raise ErroOperacao("O backup externo falhou: " + _mensagem_segura(exc), 500)
    finally:
        if pasta_tmp:
            shutil.rmtree(pasta_tmp, ignore_errors=True)
        _lock_backup.release()


def dias_a_manter(dias):
    """30 dias mais recentes + o último dia de cada um dos 12 meses mais recentes."""
    dias = sorted(set(dias), reverse=True)
    manter = set(dias[:DIAS_DIARIOS])
    por_mes = {}
    for d in dias:  # decrescente: o primeiro visto de cada mês é o último dia dele
        por_mes.setdefault(d[:7], d)
    for mes in sorted(por_mes, reverse=True)[:MESES_MENSAIS]:
        manter.add(por_mes[mes])
    return manter


def _agrupar_por_dia(objetos, prefixo):
    base = prefixo + "diario/"
    grupos = {}
    for o in objetos:
        resto = o["chave"][len(base):] if o["chave"].startswith(base) else ""
        dia = resto.split("/", 1)[0]
        if RE_DIA.match(dia) and "/" in resto:
            grupos.setdefault(dia, []).append(o)
    return grupos


def podar(s3, prefixo):
    grupos = _agrupar_por_dia(s3.listar(prefixo + "diario/"), prefixo)
    manter = dias_a_manter(grupos)
    apagados = 0
    for dia, objs in grupos.items():
        if dia in manter:
            continue
        for o in objs:
            s3.apagar(o["chave"])
            apagados += 1
    return apagados


def listar_remotos(conn):
    s3 = _cliente(conn)
    prefixo = _prefixo(conn)
    grupos = _agrupar_por_dia(s3.listar(prefixo + "diario/"), prefixo)
    saida = []
    for dia in sorted(grupos, reverse=True):
        saida.append({"dia": dia, "arquivos": [
            {"nome": o["chave"].rsplit("/", 1)[-1], "chave": o["chave"], "tamanho": o["tamanho"],
             "modificado": o["modificado"]} for o in sorted(grupos[dia], key=lambda x: x["chave"])]})
    return saida


def baixar_decifrado(conn, chave):
    """Baixa e decifra para um arquivo temporário. Devolve (caminho, nome)."""
    prefixo = _prefixo(conn)
    base = prefixo + "diario/"
    resto = chave[len(base):] if chave.startswith(base) else ""
    partes = resto.split("/")
    if len(partes) != 2 or not RE_DIA.match(partes[0]) or not partes[1].endswith(".enc") \
            or not re.match(r"^[A-Za-z0-9._-]+$", partes[1]):
        raise ErroOperacao("Arquivo não encontrado", 404)
    s3 = _cliente(conn)
    frase = _frase(conn)
    pasta = tempfile.mkdtemp(prefix=".baixar-")
    cifrado = os.path.join(pasta, "c")
    claro = os.path.join(pasta, "d")
    try:
        s3.get_para_arquivo(chave, cifrado)
        decifrar_arquivo(cifrado, claro, frase)
        os.remove(cifrado)
    except Exception:
        shutil.rmtree(pasta, ignore_errors=True)
        raise
    return claro, partes[0] + "-" + partes[1][:-4]


def tarefa_backup_diario(agora=None):
    """Chamado pela rotina a cada 15 minutos: envia o backup do dia uma vez."""
    conn = srv.db()
    try:
        if not cripto_disponivel() or not configurado(conn):
            return None
        hoje = datetime.date.today().isoformat()
        if _cfg(conn, "op_backup_ultimo_dia") == hoje:
            return None
        tentativa = _cfg(conn, "op_backup_ultima_tentativa")
    finally:
        conn.close()
    agora = agora or time.time()
    if tentativa:
        try:
            t = datetime.datetime.strptime(tentativa, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
            if agora - t.timestamp() < 3600:
                return None
        except ValueError:
            pass
    srv.backup_diario()
    return executar_backup()


# ================================================================ saúde

def versao():
    global _versao_cache
    if _versao_cache:
        return _versao_cache
    v = ""
    try:
        git = os.path.join(srv.BASE_DIR, ".git")
        with open(os.path.join(git, "HEAD"), encoding="utf-8") as fh:
            head = fh.read().strip()
        if head.startswith("ref:"):
            ref = head[4:].strip()
            caminho = os.path.join(git, ref)
            if os.path.isfile(caminho):
                with open(caminho, encoding="utf-8") as fh:
                    v = fh.read().strip()[:7]
            else:
                with open(os.path.join(git, "packed-refs"), encoding="utf-8") as fh:
                    for linha in fh:
                        if linha.strip().endswith(" " + ref):
                            v = linha.split()[0][:7]
        else:
            v = head[:7]
    except (OSError, IndexError):
        v = ""
    if not re.match(r"^[0-9a-f]{7}$", v or ""):
        try:
            mt = os.path.getmtime(os.path.join(srv.BASE_DIR, "server.py"))
            v = "m" + datetime.datetime.utcfromtimestamp(mt).strftime("%Y%m%d%H%M")
        except OSError:
            v = "desconhecida"
    _versao_cache = v
    return v


def _iso_de_epoch(t):
    return datetime.datetime.utcfromtimestamp(t).replace(microsecond=0).isoformat() + "Z"


def saude(conn=None):
    proprio = conn is None
    db_ok = False
    fila = None
    remoto = None
    try:
        if proprio:
            conn = srv.db()
        conn.execute("SELECT 1 FROM config LIMIT 1").fetchall()
        db_ok = True
        try:
            fila = conn.execute("SELECT COUNT(*) FROM candidaturas WHERE voz_status='para_ligar'").fetchone()[0]
        except Exception:  # noqa: BLE001
            fila = None
        remoto = _cfg(conn, "op_backup_ultimo_ok") or None
    except Exception:  # noqa: BLE001
        db_ok = False
    finally:
        if proprio and conn is not None:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
    local = None
    try:
        u = ultimo_backup_local()
        local = _iso_de_epoch(u[2]) if u else None
    except OSError:
        local = None
    return {
        "ok": db_ok,
        "versao": versao(),
        "uptime_s": int(time.time() - INICIO),
        "db_ok": db_ok,
        "fila_voz": fila,
        "ultimo_backup": local,
        "ultimo_backup_remoto": remoto,
    }


def _uso_disco():
    """Fração usada do disco da pasta do app (os testes trocam esta função)."""
    u = shutil.disk_usage(srv.BASE_DIR)
    return (u.used / u.total if u.total else 0.0), u.free


# ================================================================ alertas

def _reservar_alerta(conn, chave, janela, agora=None):
    """True quando pode enviar (e já marca o envio); False se ainda está na janela."""
    agora = agora if agora is not None else time.time()
    with _lock_alerta:
        r = conn.execute("SELECT ultimo FROM alertas_operacao WHERE chave=?", (chave,)).fetchone()
        if r and agora - (r[0] or 0) < janela:
            conn.execute("UPDATE alertas_operacao SET contagem=contagem+1 WHERE chave=?", (chave,))
            conn.commit()
            return False
        conn.execute(
            "INSERT INTO alertas_operacao (chave, ultimo, contagem) VALUES (?,?,1)"
            " ON CONFLICT(chave) DO UPDATE SET ultimo=excluded.ultimo, contagem=1",
            (chave, agora))
        conn.commit()
        return True


def _enviar_dono(para, assunto, corpo, lang):
    def tarefa():
        c = srv.db()
        try:
            srv.enviar_email(c, para, assunto, corpo, idioma=lang)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Operação: e-mail ao dono falhou: %s\n" % type(exc).__name__)
        finally:
            c.close()
    if ENVIO_EM_SEGUNDO_PLANO:
        threading.Thread(target=tarefa, daemon=True).start()
    else:
        tarefa()


TEXTOS = {
    "pt": {
        "erro_assunto": "[Bússola] Erro no servidor: {tipo} em {rota}",
        "erro_corpo": "Ocorreu um erro não tratado no servidor.\n\nQuando: {quando} (UTC)\nRota: {metodo} {rota}\nTipo: {tipo}\nMensagem: {mensagem}\n\nO detalhe completo está no painel do dono, aba Sistema. Novos e-mails deste mesmo erro só depois de 30 minutos.",
        "resumo_assunto": "[Bússola] Resumo de erros de {dia}: {total}",
        "resumo_corpo": "Erros do servidor em {dia} (UTC):\n\n{linhas}\n\nVeja e marque como resolvidos no painel do dono, aba Sistema.",
        "cond_assunto": "[Bússola] Alerta: {titulo}",
        "cond_corpo": "{titulo}\n\n{detalhe}\n\nEste aviso se repete no máximo a cada 6 horas enquanto a condição continuar.",
        "disco": "Disco quase cheio",
        "disco_d": "O disco do servidor está com {pct}% de uso (limite 85%).",
        "backup_local": "Backup local atrasado",
        "backup_local_d": "O último backup local tem mais de 26 horas ({quando}).",
        "backup_local_nenhum": "Não há nenhum backup local na pasta backups/.",
        "voz_presa": "Fila de voz travada",
        "voz_presa_d": "{n} ligação(ões) em andamento há mais de 60 minutos.",
        "voz_falhas": "Falhas repetidas na ElevenLabs/Twilio",
        "voz_falhas_d": "{n} ligações com erro na última hora.",
        "backup_remoto": "Backup externo atrasado",
        "backup_remoto_d": "O último backup externo com sucesso foi em {quando}. Último erro: {erro}",
        "nunca": "nunca",
    },
    "en": {
        "erro_assunto": "[Bússola] Server error: {tipo} at {rota}",
        "erro_corpo": "An unhandled error happened on the server.\n\nWhen: {quando} (UTC)\nRoute: {metodo} {rota}\nType: {tipo}\nMessage: {mensagem}\n\nFull details are in the owner panel, System tab. New emails for this same error only after 30 minutes.",
        "resumo_assunto": "[Bússola] Error digest for {dia}: {total}",
        "resumo_corpo": "Server errors on {dia} (UTC):\n\n{linhas}\n\nReview them and mark them resolved in the owner panel, System tab.",
        "cond_assunto": "[Bússola] Alert: {titulo}",
        "cond_corpo": "{titulo}\n\n{detalhe}\n\nThis alert repeats at most every 6 hours while the condition lasts.",
        "disco": "Disk almost full",
        "disco_d": "The server disk is {pct}% used (limit 85%).",
        "backup_local": "Local backup is late",
        "backup_local_d": "The latest local backup is older than 26 hours ({quando}).",
        "backup_local_nenhum": "There is no local backup in the backups/ folder.",
        "voz_presa": "Voice queue stuck",
        "voz_presa_d": "{n} call(s) in progress for more than 60 minutes.",
        "voz_falhas": "Repeated ElevenLabs/Twilio failures",
        "voz_falhas_d": "{n} calls with errors in the last hour.",
        "backup_remoto": "Offsite backup is late",
        "backup_remoto_d": "The last successful offsite backup was at {quando}. Last error: {erro}",
        "nunca": "never",
    },
    "es": {
        "erro_assunto": "[Bússola] Error en el servidor: {tipo} en {rota}",
        "erro_corpo": "Ocurrió un error no controlado en el servidor.\n\nCuándo: {quando} (UTC)\nRuta: {metodo} {rota}\nTipo: {tipo}\nMensaje: {mensagem}\n\nEl detalle completo está en el panel del dueño, pestaña Sistema. Nuevos correos de este mismo error solo después de 30 minutos.",
        "resumo_assunto": "[Bússola] Resumen de errores del {dia}: {total}",
        "resumo_corpo": "Errores del servidor el {dia} (UTC):\n\n{linhas}\n\nRevísalos y márcalos como resueltos en el panel del dueño, pestaña Sistema.",
        "cond_assunto": "[Bússola] Alerta: {titulo}",
        "cond_corpo": "{titulo}\n\n{detalhe}\n\nEste aviso se repite como máximo cada 6 horas mientras la condición continúe.",
        "disco": "Disco casi lleno",
        "disco_d": "El disco del servidor tiene {pct}% de uso (límite 85%).",
        "backup_local": "Respaldo local atrasado",
        "backup_local_d": "El último respaldo local tiene más de 26 horas ({quando}).",
        "backup_local_nenhum": "No hay ningún respaldo local en la carpeta backups/.",
        "voz_presa": "Cola de voz trabada",
        "voz_presa_d": "{n} llamada(s) en curso desde hace más de 60 minutos.",
        "voz_falhas": "Fallas repetidas en ElevenLabs/Twilio",
        "voz_falhas_d": "{n} llamadas con error en la última hora.",
        "backup_remoto": "Respaldo externo atrasado",
        "backup_remoto_d": "El último respaldo externo exitoso fue el {quando}. Último error: {erro}",
        "nunca": "nunca",
    },
}


def _t(lang, chave, **v):
    return TEXTOS[_lang(lang)][chave].format(**v)


def _dono(conn):
    return (_cfg(conn, "dono_email") or "").strip(), _lang(_cfg(conn, "dono_idioma"))


def erro(handler, metodo, rota, exc):
    """Chamado no except de api(): registra e avisa o dono. Nunca levanta exceção."""
    try:
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_txt = redigir("".join(tb))
        if len(tb_txt) > 4000:
            tb_txt = "...\n" + tb_txt[-4000:]
        tipo = type(exc).__name__[:80]
        mensagem = redigir(str(exc))[:500]
        rota_n = _normalizar_rota(rota)
        metodo = (metodo or "")[:10]
        frames = traceback.extract_tb(exc.__traceback__)
        ultimo = frames[-1] if frames else None
        local = "%s:%s:%s" % (os.path.basename(ultimo.filename), ultimo.lineno, ultimo.name) if ultimo else ""
        assinatura = hashlib.sha1(("%s|%s|%s|%s" % (tipo, metodo, rota_n, local)).encode("utf-8")).hexdigest()[:16]
        conn = srv.db()
        try:
            cur = conn.execute(
                "INSERT INTO erros_servidor (rota, metodo, tipo, mensagem, traceback, assinatura) VALUES (?,?,?,?,?,?)",
                (rota_n, metodo, tipo, mensagem, tb_txt, assinatura))
            conn.commit()
            novo_id = cur.lastrowid
            para, lang = _dono(conn)
            if para and _reservar_alerta(conn, "erro:" + assinatura, JANELA_ERRO):
                quando = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                _enviar_dono(para, _t(lang, "erro_assunto", tipo=tipo, rota=rota_n),
                             _t(lang, "erro_corpo", quando=quando, metodo=metodo, rota=rota_n,
                                tipo=tipo, mensagem=mensagem), lang)
            return novo_id
        finally:
            conn.close()
    except Exception as e2:  # noqa: BLE001
        sys.stderr.write("Operação: falha ao registrar erro: %s\n" % type(e2).__name__)
        return None


def enviar_resumo_diario(conn, hoje=None):
    """Resumo dos erros do dia anterior (UTC), uma vez por dia. Devolve o total."""
    hoje = hoje or datetime.datetime.utcnow().date()
    ontem = (hoje - datetime.timedelta(days=1)).isoformat()
    chave = "resumo:" + ontem
    if conn.execute("SELECT 1 FROM alertas_operacao WHERE chave=?", (chave,)).fetchone():
        return 0
    linhas = conn.execute(
        "SELECT tipo, metodo, rota, COUNT(*) AS n FROM erros_servidor WHERE date(quando)=?"
        " GROUP BY tipo, metodo, rota ORDER BY n DESC LIMIT 30", (ontem,)).fetchall()
    total = sum(r["n"] for r in linhas)
    para, lang = _dono(conn)
    if not _reservar_alerta(conn, chave, 10 ** 9):
        return 0
    if total and para:
        texto = "\n".join("%5d  %s  %s %s" % (r["n"], r["tipo"], r["metodo"], r["rota"]) for r in linhas)
        _enviar_dono(para, _t(lang, "resumo_assunto", dia=ontem, total=total),
                     _t(lang, "resumo_corpo", dia=ontem, linhas=texto), lang)
    return total


def condicoes_ativas(conn, agora=None):
    """Lista de (codigo, detalhe_vars) das condições de alerta ativas agora."""
    agora = agora if agora is not None else time.time()
    ativas = []
    try:
        uso, _ = _uso_disco()
        if uso > LIMITE_DISCO:
            ativas.append(("disco", {"pct": int(round(uso * 100))}))
    except OSError:
        pass
    if os.path.isfile(srv.DB_PATH):
        u = ultimo_backup_local()
        if not u:
            ativas.append(("backup_local", {"nenhum": True}))
        elif agora - u[2] > HORAS_BACKUP_LOCAL * 3600:
            ativas.append(("backup_local", {"quando": _iso_de_epoch(u[2])}))
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM voz_chamadas WHERE status='em_andamento'"
            " AND iniciada_em <= datetime(?, 'unixepoch', ?)",
            (int(agora), "-%d minutes" % MINUTOS_VOZ_PRESA)).fetchone()[0]
        if n:
            ativas.append(("voz_presa", {"n": n}))
        n = conn.execute(
            "SELECT COUNT(*) FROM voz_chamadas WHERE COALESCE(erro,'') != ''"
            " AND COALESCE(NULLIF(terminada_em,''), iniciada_em) >= datetime(?, 'unixepoch', '-1 hours')",
            (int(agora),)).fetchone()[0]
        if n >= FALHAS_VOZ_HORA:
            ativas.append(("voz_falhas", {"n": n}))
    except Exception:  # noqa: BLE001  (sem módulo de voz)
        pass
    if configurado(conn):
        ok = _cfg(conn, "op_backup_ultimo_ok")
        atrasado = True
        if ok:
            try:
                t = datetime.datetime.strptime(ok, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
                atrasado = agora - t.timestamp() > HORAS_BACKUP_REMOTO * 3600
            except ValueError:
                pass
        # só avisa depois da primeira tentativa (evita alarme logo após configurar)
        if atrasado and _cfg(conn, "op_backup_ultima_tentativa"):
            ativas.append(("backup_remoto", {"quando": ok, "erro": _cfg(conn, "op_backup_ultimo_erro")}))
    return ativas


def _detalhe(lang, codigo, v):
    if codigo == "backup_local" and v.get("nenhum"):
        return _t(lang, "backup_local_nenhum")
    if codigo == "backup_remoto":
        return _t(lang, "backup_remoto_d", quando=v.get("quando") or _t(lang, "nunca"), erro=v.get("erro") or "-")
    return _t(lang, codigo + "_d", **v)


def verificar_condicoes(conn, agora=None):
    """Envia um e-mail por condição ativa, no máximo a cada 6 horas. Devolve os códigos avisados."""
    ativas = condicoes_ativas(conn, agora)
    para, lang = _dono(conn)
    avisados = []
    if not para:
        return avisados
    for codigo, v in ativas:
        if _reservar_alerta(conn, "cond:" + codigo, JANELA_CONDICAO, agora):
            titulo = _t(lang, codigo)
            _enviar_dono(para, _t(lang, "cond_assunto", titulo=titulo),
                         _t(lang, "cond_corpo", titulo=titulo, detalhe=_detalhe(lang, codigo, v)), lang)
            avisados.append(codigo)
    return avisados


def rotina_operacao():
    time.sleep(PRIMEIRA_ESPERA)
    while True:
        conn = None
        try:
            conn = srv.db()
            verificar_condicoes(conn)
            enviar_resumo_diario(conn)
            conn.execute("DELETE FROM erros_servidor WHERE quando < datetime('now', '-90 days')")
            conn.commit()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Operação: verificação falhou: %s\n" % type(exc).__name__)
        finally:
            if conn is not None:
                conn.close()
        try:
            tarefa_backup_diario()
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("Operação: backup externo falhou: %s\n" % _mensagem_segura(exc))
        time.sleep(INTERVALO_MONITOR)


# ================================================================ rotas

def rotear_publico(h, method, path, conn):
    if method == "GET" and path == "/api/saude":
        dados = saude(conn)
        h._json(200 if dados["ok"] else 503, dados)
        return True
    return False


def _estado(conn, idioma=""):
    backup = config_backup(conn)
    if backup["ultimo_erro"] and idioma:
        try:
            import erros_i18n
            backup["ultimo_erro"] = erros_i18n.traduzir(backup["ultimo_erro"], idioma)
        except ImportError:  # pragma: no cover
            pass
    try:
        uso, livre = _uso_disco()
        disco = {"usado_pct": round(uso * 100, 1), "livre_gb": round(livre / 1e9, 1)}
    except OSError:
        disco = None
    return {
        "saude": saude(conn),
        "disco": disco,
        "condicoes": [c for c, _ in condicoes_ativas(conn)],
        "backup": backup,
        "erros_abertos": conn.execute("SELECT COUNT(*) FROM erros_servidor WHERE resolvido=0").fetchone()[0],
    }


def _enviar_arquivo(h, caminho, nome):
    try:
        tamanho = os.path.getsize(caminho)
        h.send_response(200)
        h.send_header("Content-Type", "application/octet-stream")
        h.send_header("Content-Disposition", 'attachment; filename="%s"' % nome)
        h.send_header("Content-Length", str(tamanho))
        h.send_header("Cache-Control", "no-store")
        h.end_headers()
        with open(caminho, "rb") as fh:
            for pedaco in iter(lambda: fh.read(BLOCO), b""):
                h.wfile.write(pedaco)
    finally:
        shutil.rmtree(os.path.dirname(caminho), ignore_errors=True)


def rotear_dono(h, method, path, conn):
    """Rotas /api/dono/operacao* (a autenticação do dono já foi feita no servidor)."""
    if not path.startswith("/api/dono/operacao"):
        return False
    try:
        if method == "GET" and path == "/api/dono/operacao":
            h._json(200, _estado(conn, h.headers.get("X-Idioma") or ""))
        elif method == "POST" and path == "/api/dono/operacao/backup/config":
            salvar_config(conn, h._body())
            h._json(200, {"ok": True, "backup": config_backup(conn)})
        elif method == "POST" and path == "/api/dono/operacao/backup/frase":
            d = h._body()
            definir_frase(conn, d.get("frase"), d.get("atual"))
            h._json(200, {"ok": True})
        elif method == "POST" and path == "/api/dono/operacao/backup/testar":
            h._json(200, testar_conexao(conn))
        elif method == "POST" and path == "/api/dono/operacao/backup/agora":
            _cliente(conn)
            _frase(conn)
            if _lock_backup.locked():
                raise ErroOperacao("Já existe um backup em andamento", 409)
            if BACKUP_EM_SEGUNDO_PLANO:
                def tarefa():
                    try:
                        executar_backup()
                    except Exception as exc:  # noqa: BLE001
                        sys.stderr.write("Operação: backup manual falhou: %s\n" % _mensagem_segura(exc))
                threading.Thread(target=tarefa, daemon=True).start()
                h._json(200, {"iniciado": True})
            else:
                h._json(200, {"iniciado": True, "resultado": executar_backup()})
        elif method == "GET" and path == "/api/dono/operacao/backup/lista":
            h._json(200, {"dias": listar_remotos(conn)})
        elif method == "GET" and path == "/api/dono/operacao/backup/baixar":
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(h.path).query)
            caminho, nome = baixar_decifrado(conn, (q.get("chave") or [""])[0])
            _enviar_arquivo(h, caminho, nome)
        elif method == "GET" and path == "/api/dono/operacao/erros":
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(h.path).query)
            onde = "" if (q.get("todos") or [""])[0] == "1" else " WHERE resolvido=0"
            linhas = conn.execute(
                "SELECT id, quando, rota, metodo, tipo, mensagem, traceback, assinatura, resolvido, resolvido_em"
                " FROM erros_servidor" + onde + " ORDER BY id DESC LIMIT 100").fetchall()
            h._json(200, {"erros": [dict(r) for r in linhas]})
        elif method == "POST" and re.match(r"^/api/dono/operacao/erros/\d+/resolver$", path):
            eid = int(path.split("/")[-2])
            resolvido = 1 if h._body().get("resolvido", True) else 0
            cur = conn.execute(
                "UPDATE erros_servidor SET resolvido=?, resolvido_em=CASE WHEN ?=1 THEN datetime('now') ELSE '' END"
                " WHERE id=?", (resolvido, resolvido, eid))
            conn.commit()
            if not cur.rowcount:
                raise ErroOperacao("Não encontrado", 404)
            h._json(200, {"ok": True})
        else:
            h._json(404, {"erro": "Rota não encontrada"})
    except ErroOperacao as e:
        h._json(e.status, {"erro": e.mensagem})
    return True


# ================================================================ linha de comando

def _main(argv):
    if len(argv) == 4 and argv[1] == "decifrar":
        frase = getpass.getpass("Frase de backup / Backup passphrase / Frase de respaldo: ")
        try:
            decifrar_arquivo(argv[2], argv[3], frase)
        except ErroOperacao as e:
            sys.stderr.write(e.mensagem + "\n")
            return 1
        print("OK: %s" % argv[3])
        return 0
    sys.stderr.write("Uso: python3 operacao.py decifrar ARQUIVO.enc SAIDA\n")
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
