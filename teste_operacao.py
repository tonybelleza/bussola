"""
Testes da operação (operacao.py): backup externo cifrado, saúde e alertas.

Uso:  python3 teste_operacao.py

Roda numa pasta temporária (cópia dos .py e de public/). Nenhum serviço real é
chamado: a rede do S3 é trocada por um bucket falso em memória que confere os
cabeçalhos AWS Signature V4 (recalcula a assinatura de forma independente).
"""
import datetime
import hashlib
import hmac
import io
import json
import os
import re
import shutil
import sqlite3
import stat
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="op-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)
os.environ["OPERACAO_MONITOR_DESLIGADO"] = "1"

import operacao  # noqa: E402
import server  # noqa: E402

ACESSO = "AKIDTESTE0000EXEMPLO"
SEGREDO = "segredoDeTeste/abc123XYZ+987"
FRASE = "frase de backup bem longa 42"
BUCKET = "meu-bucket"
ENDPOINT = "https://ns.compat.objectstorage.us-ashburn-1.oraclecloud.com"
REGIAO = "us-ashburn-1"


# ---------------------------------------------------------------- bucket falso

def _q(s, seguro="-_.~"):
    return urllib.parse.quote(s, safe=seguro)


def assinatura_independente(metodo, url, cab, segredo, regiao):
    """Recalcula a SigV4 a partir do pedido (implementação separada da do módulo)."""
    auth = cab["authorization"]
    m = re.match(r"^AWS4-HMAC-SHA256 Credential=([^/]+)/(\d{8})/([^/]+)/s3/aws4_request, "
                 r"SignedHeaders=([a-z0-9;-]+), Signature=([0-9a-f]{64})$", auth)
    assert m, "Authorization mal formado: %s" % auth
    _, dia, reg, assinados, assinatura = m.groups()
    assert reg == regiao
    p = urllib.parse.urlsplit(url)
    valores = dict(cab)
    valores["host"] = p.netloc
    nomes = assinados.split(";")
    assert nomes == sorted(nomes) and "host" in nomes and "x-amz-date" in nomes and "x-amz-content-sha256" in nomes
    pares = sorted(urllib.parse.parse_qsl(p.query, keep_blank_values=True))
    consulta = "&".join("%s=%s" % (_q(k), _q(v)) for k, v in pares)
    canon = "".join("%s:%s\n" % (n, valores[n].strip()) for n in nomes)
    pedido = "\n".join([metodo, p.path, consulta, canon, assinados, valores["x-amz-content-sha256"]])
    escopo = "%s/%s/s3/aws4_request" % (dia, regiao)
    texto = "AWS4-HMAC-SHA256\n%s\n%s\n%s" % (valores["x-amz-date"], escopo, hashlib.sha256(pedido.encode()).hexdigest())
    k = ("AWS4" + segredo).encode()
    for parte in (dia, regiao, "s3", "aws4_request"):
        k = hmac.new(k, parte.encode(), hashlib.sha256).digest()
    return hmac.compare_digest(hmac.new(k, texto.encode(), hashlib.sha256).hexdigest(), assinatura)


class Resp:
    def __init__(self, corpo, status=200):
        self._b = io.BytesIO(corpo)
        self.status = status

    def read(self, n=-1):
        return self._b.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def erro_xml(url, status, codigo):
    corpo = ("<?xml version=\"1.0\"?><Error><Code>%s</Code><Message>falha simulada</Message></Error>" % codigo).encode()
    return urllib.error.HTTPError(url, status, codigo, {}, io.BytesIO(corpo))


class BucketFalso:
    PAGINA = 25  # pequena para exercitar a paginação do ListObjectsV2

    def __init__(self):
        self.objetos = {}
        self.pedidos = []

    def __call__(self, req, timeout):
        url = req.full_url
        metodo = req.get_method()
        cab = {k.lower(): v for k, v in req.header_items()}
        corpo = req.data
        if corpo is not None and not isinstance(corpo, bytes):
            corpo = corpo.read()
        corpo = corpo or b""
        self.pedidos.append((metodo, url))
        # SigV4: cabeçalhos presentes e bem formados, hash do corpo confere, assinatura confere
        assert re.match(r"^\d{8}T\d{6}Z$", cab.get("x-amz-date", "")), cab
        assert cab.get("x-amz-content-sha256") == hashlib.sha256(corpo).hexdigest()
        assert "authorization" in cab and SEGREDO not in cab["authorization"]
        if not assinatura_independente(metodo, url, cab, SEGREDO, REGIAO):
            raise erro_xml(url, 403, "SignatureDoesNotMatch")
        p = urllib.parse.urlsplit(url)
        assert url.startswith(ENDPOINT + "/" + BUCKET)
        chave = urllib.parse.unquote(p.path[len("/" + BUCKET):].lstrip("/"))
        q = dict(urllib.parse.parse_qsl(p.query))
        if metodo == "PUT":
            assert int(cab["content-length"]) == len(corpo)
            self.objetos[chave] = corpo
            return Resp(b"")
        if metodo == "GET" and not chave and q.get("list-type") == "2":
            nomes = sorted(k for k in self.objetos if k.startswith(q.get("prefix", "")))
            inicio = int(q.get("continuation-token") or 0)
            pagina = nomes[inicio:inicio + self.PAGINA]
            mais = inicio + self.PAGINA < len(nomes)
            xml = ['<?xml version="1.0" encoding="UTF-8"?><ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">']
            for k in pagina:
                xml.append("<Contents><Key>%s</Key><LastModified>2026-10-27T00:00:00.000Z</LastModified><Size>%d</Size></Contents>"
                           % (k, len(self.objetos[k])))
            xml.append("<IsTruncated>%s</IsTruncated>" % ("true" if mais else "false"))
            if mais:
                xml.append("<NextContinuationToken>%d</NextContinuationToken>" % (inicio + self.PAGINA))
            xml.append("</ListBucketResult>")
            return Resp("".join(xml).encode())
        if metodo == "GET":
            if chave not in self.objetos:
                raise erro_xml(url, 404, "NoSuchKey")
            return Resp(self.objetos[chave])
        if metodo == "DELETE":
            self.objetos.pop(chave, None)
            return Resp(b"", 204)
        raise AssertionError("pedido inesperado %s %s" % (metodo, url))


# ---------------------------------------------------------------- testes

class TestOperacao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        operacao.ENVIO_EM_SEGUNDO_PLANO = False
        operacao.BACKUP_EM_SEGUNDO_PLANO = False
        operacao.ITERACOES = 2000  # rápido nos testes (o cabeçalho guarda as iterações)
        cls.emails = []
        server.enviar_email = lambda conn, para, assunto, corpo, **kw: (cls.emails.append((para, assunto, corpo, kw.get("idioma"))) or (True, "ok"))
        cls.bucket = BucketFalso()
        operacao._urlopen = cls.bucket
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        s, d = cls.req_cls("POST", "/api/dono/setup", {"senha": "senha-do-dono-1"})
        assert s == 200, d
        cls.dono = {"X-Dono-Token": d["token"]}

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        shutil.rmtree(PASTA, ignore_errors=True)

    @classmethod
    def req_cls(cls, metodo, caminho, dados=None, cab=None, cru=False):
        corpo = json.dumps(dados).encode() if dados is not None else None
        h = {"Content-Type": "application/json"}
        h.update(cab or {})
        r = urllib.request.Request(cls.base + caminho, data=corpo, method=metodo, headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                b = resp.read()
                return resp.status, (b if cru else json.loads(b or b"{}"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def req(self, *a, **k):
        return self.req_cls(*a, **k)

    def setUp(self):
        self.emails.clear()

    def configurar(self, segredo=SEGREDO):
        s, d = self.req("POST", "/api/dono/operacao/backup/config", {
            "endpoint": ENDPOINT, "regiao": REGIAO, "bucket": BUCKET, "prefixo": "bussola/",
            "chave_acesso": ACESSO, "segredo": segredo}, self.dono)
        self.assertEqual(s, 200, d)
        conn = server.db()
        if not server.config_get(conn, "op_backup_verificador"):
            operacao.definir_frase(conn, FRASE)
        conn.close()

    # ------------------------------------------------ SigV4
    def test_sigv4_vetores_aws(self):
        """Exemplos oficiais da documentação da AWS (S3, Signature V4)."""
        ak, sk, quando = "AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", datetime.datetime(2013, 5, 24)
        h = operacao.assinar_v4("GET", "https://examplebucket.s3.amazonaws.com/test.txt", {"Range": "bytes=0-9"},
                                operacao.VAZIO, ak, sk, "us-east-1", quando)
        self.assertTrue(h["authorization"].endswith("Signature=f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41"))
        self.assertIn("SignedHeaders=host;range;x-amz-content-sha256;x-amz-date", h["authorization"])
        self.assertEqual(h["x-amz-date"], "20130524T000000Z")
        corpo = b"Welcome to Amazon S3."
        h = operacao.assinar_v4("PUT", "https://examplebucket.s3.amazonaws.com/test%24file.text",
                                {"Date": "Fri, 24 May 2013 00:00:00 GMT", "x-amz-storage-class": "REDUCED_REDUNDANCY"},
                                hashlib.sha256(corpo).hexdigest(), ak, sk, "us-east-1", quando)
        self.assertTrue(h["authorization"].endswith("Signature=98ad721746da40c64f1a55b78f14c238d841ea1380cd77a1b5971af0ece108bd"))
        h = operacao.assinar_v4("GET", "https://examplebucket.s3.amazonaws.com/?max-keys=2&prefix=J", {},
                                operacao.VAZIO, ak, sk, "us-east-1", quando)
        self.assertTrue(h["authorization"].endswith("Signature=34b48302e7b5fa45bde8084f4b7868a86f0a534bc59db6670ed5711ef69dc6f7"))

    # ------------------------------------------------ cifra
    def test_cifra_ida_e_volta(self):
        bloco = operacao.BLOCO
        operacao.BLOCO = 1000
        try:
            dados = os.urandom(5500)
            c = operacao.cifrar_bytes(dados, FRASE)
            self.assertTrue(c.startswith(operacao.MAGICO))
            self.assertNotIn(dados[:64], c)
            self.assertEqual(operacao.decifrar_bytes(c, FRASE), dados)
            self.assertNotEqual(operacao.cifrar_bytes(dados, FRASE), c)  # sal novo a cada arquivo
            with self.assertRaises(operacao.ErroOperacao) as e:
                operacao.decifrar_bytes(c, "outra frase qualquer")
            self.assertIn("Frase de backup incorreta", e.exception.mensagem)
            with self.assertRaises(operacao.ErroOperacao):
                operacao.decifrar_bytes(c[:-10], FRASE)  # truncado
            with self.assertRaises(operacao.ErroOperacao):
                operacao.decifrar_bytes(b"lixo", FRASE)
            self.assertEqual(operacao.decifrar_bytes(operacao.cifrar_bytes(b"", FRASE), FRASE), b"")
        finally:
            operacao.BLOCO = bloco

    def test_dias_a_manter(self):
        inicio = datetime.date(2025, 1, 1)
        dias = [(inicio + datetime.timedelta(days=i)).isoformat() for i in range(700)]
        manter = operacao.dias_a_manter(dias)
        recentes = sorted(dias)[-30:]
        self.assertTrue(set(recentes) <= manter)
        mensais = manter - set(recentes)
        self.assertEqual(len({d[:7] for d in manter}), 12)
        for d in mensais:  # último dia de cada mês
            proximo = (datetime.date.fromisoformat(d) + datetime.timedelta(days=1))
            self.assertEqual(proximo.day, 1)
        ultimo_do_mes = {}
        for d in sorted(dias):
            ultimo_do_mes[d[:7]] = d
        doze = {ultimo_do_mes[m] for m in sorted(ultimo_do_mes)[-12:]}
        self.assertEqual(manter, set(recentes) | doze)

    # ------------------------------------------------ configuração e segredos
    def test_config_segredos_e_frase(self):
        self.assertEqual(self.req("GET", "/api/dono/operacao")[0], 401)
        s, d = self.req("POST", "/api/dono/operacao/backup/config", {
            "endpoint": "ftp://x", "regiao": REGIAO, "bucket": BUCKET, "chave_acesso": ACESSO, "segredo": SEGREDO}, self.dono)
        self.assertEqual(s, 400)
        s, d = self.req("POST", "/api/dono/operacao/backup/config", {
            "endpoint": "ftp://x", "regiao": REGIAO, "bucket": BUCKET, "chave_acesso": ACESSO, "segredo": SEGREDO},
            dict(self.dono, **{"X-Idioma": "en"}))
        self.assertEqual(d["erro"], "Invalid endpoint (use https://...)")
        self.configurar()
        s, d = self.req("GET", "/api/dono/operacao", cab=self.dono)
        self.assertEqual(s, 200)
        texto = json.dumps(d)
        self.assertNotIn(SEGREDO, texto)
        self.assertNotIn(ACESSO, texto)
        self.assertNotIn(FRASE, texto)
        self.assertTrue(d["backup"]["tem_segredo"] and d["backup"]["tem_frase"])
        self.assertEqual(d["backup"]["chave_acesso_final"], ACESSO[-4:])
        conn = server.db()
        tudo = " ".join(r[0] or "" for r in conn.execute("SELECT valor FROM config").fetchall())
        conn.close()
        self.assertNotIn(SEGREDO, tudo)
        self.assertNotIn(FRASE, tudo)
        chave = operacao.caminho_chave_maquina()
        self.assertTrue(os.path.isfile(chave))
        self.assertEqual(stat.S_IMODE(os.stat(chave).st_mode), 0o600)
        self.assertFalse(chave.startswith(server.PUBLIC_DIR))
        # salvar sem segredo mantém o guardado
        s, _ = self.req("POST", "/api/dono/operacao/backup/config", {
            "endpoint": ENDPOINT, "regiao": REGIAO, "bucket": BUCKET, "prefixo": "bussola/", "chave_acesso": ""}, self.dono)
        self.assertEqual(s, 200)
        # trocar a frase exige a atual
        s, d = self.req("POST", "/api/dono/operacao/backup/frase", {"frase": "outra frase comprida 1"}, self.dono)
        self.assertEqual((s, d["erro"]), (400, "Frase de backup atual incorreta"))
        s, d = self.req("POST", "/api/dono/operacao/backup/frase", {"frase": "curta", "atual": FRASE}, self.dono)
        self.assertEqual(s, 400)
        s, d = self.req("POST", "/api/dono/operacao/backup/frase", {"frase": FRASE, "atual": FRASE}, self.dono)
        self.assertEqual(s, 200, d)

    def test_testar_conexao(self):
        self.configurar()
        s, d = self.req("POST", "/api/dono/operacao/backup/testar", cab=self.dono)
        self.assertEqual((s, d), (200, {"ok": True}))
        self.assertNotIn("bussola/teste-conexao.txt", self.bucket.objetos)
        # segredo errado: o bucket recusa a assinatura e a mensagem não vaza segredos
        self.configurar(segredo="segredoErrado999")
        s, d = self.req("POST", "/api/dono/operacao/backup/testar", cab=self.dono)
        self.assertEqual(s, 400)
        self.assertIn("SignatureDoesNotMatch", d["erro"])
        self.assertNotIn("segredoErrado999", d["erro"])
        self.configurar()

    # ------------------------------------------------ backup, lista, poda e download
    def test_backup_lista_poda_e_download(self):
        self.configurar()
        os.makedirs(server.UPLOAD_DIR, exist_ok=True)
        with open(os.path.join(server.UPLOAD_DIR, "curriculo.txt"), "wb") as fh:
            fh.write(b"conteudo do upload")
        chave_dados = os.path.join(server.BASE_DIR, "chave_dados.key")
        with open(chave_dados, "wb") as fh:
            fh.write(b"chave-de-dados-falsa")
        # 400 dias antigos no bucket (para a poda)
        hoje = datetime.date.today()
        antigos = [(hoje - datetime.timedelta(days=i)).isoformat() for i in range(1, 401)]
        for dia in antigos:
            self.bucket.objetos["bussola/diario/%s/rh.db.enc" % dia] = b"x"
        self.bucket.objetos["outra-pasta/nao-mexer.txt"] = b"y"
        s, d = self.req("POST", "/api/dono/operacao/backup/agora", cab=self.dono)
        self.assertEqual(s, 200, d)
        r = d["resultado"]
        self.assertEqual(r["dia"], hoje.isoformat())
        self.assertEqual(sorted(r["arquivos"]), ["chave_dados.key.enc", "rh.db.enc", "uploads.tar.enc"])
        dias_restantes = {k.split("/")[2] for k in self.bucket.objetos if k.startswith("bussola/diario/")}
        esperado = operacao.dias_a_manter(antigos + [hoje.isoformat()])
        self.assertEqual(dias_restantes, esperado)
        self.assertTrue(40 <= len(esperado) <= 42, len(esperado))
        self.assertIn("outra-pasta/nao-mexer.txt", self.bucket.objetos)
        # o que subiu está cifrado e volta íntegro
        enviado = self.bucket.objetos["bussola/diario/%s/rh.db.enc" % hoje.isoformat()]
        self.assertTrue(enviado.startswith(operacao.MAGICO))
        self.assertNotIn(b"SQLite format 3", enviado)
        claro = operacao.decifrar_bytes(enviado, FRASE)
        self.assertTrue(claro.startswith(b"SQLite format 3"))
        tmp = os.path.join(PASTA, "restaurado.db")
        with open(tmp, "wb") as fh:
            fh.write(claro)
        c = sqlite3.connect(tmp)
        self.assertTrue(c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='config'").fetchone()[0])
        c.close()
        chave_env = self.bucket.objetos["bussola/diario/%s/chave_dados.key.enc" % hoje.isoformat()]
        self.assertNotIn(b"chave-de-dados-falsa", chave_env)
        self.assertEqual(operacao.decifrar_bytes(chave_env, FRASE), b"chave-de-dados-falsa")
        # status
        _, est = self.req("GET", "/api/dono/operacao", cab=self.dono)
        self.assertTrue(est["backup"]["ultimo_ok"])
        self.assertEqual(est["backup"]["ultimo_erro"], "")
        self.assertGreater(est["backup"]["tamanho"], 0)
        self.assertEqual(est["saude"]["ultimo_backup_remoto"], est["backup"]["ultimo_ok"])
        # lista (paginada no bucket falso)
        s, lista = self.req("GET", "/api/dono/operacao/backup/lista", cab=self.dono)
        self.assertEqual(s, 200)
        self.assertEqual(lista["dias"][0]["dia"], hoje.isoformat())
        self.assertEqual(len(lista["dias"]), len(esperado))
        # download decifrado
        chave_up = "bussola/diario/%s/uploads.tar.enc" % hoje.isoformat()
        s, corpo = self.req("GET", "/api/dono/operacao/backup/baixar?chave=" + urllib.parse.quote(chave_up), cab=self.dono, cru=True)
        self.assertEqual(s, 200)
        import tarfile
        with tarfile.open(fileobj=io.BytesIO(corpo)) as tar:
            self.assertIn("uploads/curriculo.txt", tar.getnames())
        # chaves fora do prefixo ou estranhas são recusadas
        for ruim in ("outra-pasta/nao-mexer.txt", "bussola/diario/../x.enc", "bussola/diario/2026-01-01/a/b.enc"):
            s, _ = self.req("GET", "/api/dono/operacao/backup/baixar?chave=" + urllib.parse.quote(ruim), cab=self.dono)
            self.assertEqual(s, 404)
        # a rotina diária não repete no mesmo dia
        self.assertIsNone(operacao.tarefa_backup_diario())
        os.remove(chave_dados)

    def test_falha_no_backup_fica_registrada(self):
        self.configurar(segredo="segredoErrado999")
        s, d = self.req("POST", "/api/dono/operacao/backup/agora", cab=self.dono)
        self.assertEqual(s, 400)
        _, est = self.req("GET", "/api/dono/operacao", cab=self.dono)
        self.assertIn("SignatureDoesNotMatch", est["backup"]["ultimo_erro"])
        self.assertNotIn("segredoErrado999", json.dumps(est))
        self.configurar()

    # ------------------------------------------------ saúde
    def test_saude(self):
        s, d = self.req("GET", "/api/saude")
        self.assertEqual(s, 200)
        self.assertEqual(set(d), {"ok", "versao", "uptime_s", "db_ok", "fila_voz", "ultimo_backup", "ultimo_backup_remoto"})
        self.assertTrue(d["ok"] and d["db_ok"])
        self.assertIsInstance(d["uptime_s"], int)
        self.assertTrue(d["versao"])
        conn = server.db()
        eid = conn.execute("INSERT INTO empresas (nome, slug) VALUES ('Saude', 'saude-x')").lastrowid
        cand = conn.execute("INSERT INTO candidatos (token, nome, email, empresa_id) VALUES ('tk-s','A','a@x.com',?)", (eid,)).lastrowid
        cargo = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('C', ?)", (eid,)).lastrowid
        vaga = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'V', 'aberta', ?)", (cargo, eid)).lastrowid
        conn.execute("INSERT INTO candidaturas (candidato_id, vaga_id, voz_status) VALUES (?,?, 'para_ligar')", (cand, vaga))
        conn.commit()
        conn.close()
        _, d = self.req("GET", "/api/saude")
        self.assertEqual(d["fila_voz"], 1)

    # ------------------------------------------------ erros e e-mails
    def test_erro_capturado_e_limite_de_email(self):
        conn = server.db()
        server.config_set(conn, "dono_email", "dono@bussola.test")
        server.config_set(conn, "dono_idioma", "en")
        conn.commit()
        conn.close()
        original = server.Handler.route

        def route(h, method, path, conn):
            if path.startswith("/api/teste-erro/"):
                raise ValueError("falhou para ana@exemplo.com com tok3nSuperSecretoABCDEFGH123456")
            return original(h, method, path, conn)

        server.Handler.route = route
        try:
            caminho = "/api/teste-erro/42/AbCdEfGhIjKlMnOpQr12"
            for _ in range(2):
                s, d = self.req("GET", caminho)
                self.assertEqual((s, d), (500, {"erro": "Erro interno"}))
            self.assertEqual(len(self.emails), 1)
            para, assunto, corpo, idioma = self.emails[0]
            self.assertEqual((para, idioma), ("dono@bussola.test", "en"))
            self.assertIn("Server error: ValueError", assunto)
            self.assertNotIn("ana@exemplo.com", corpo)
            self.assertNotIn("tok3nSuperSecreto", corpo)
            conn = server.db()
            linhas = conn.execute("SELECT * FROM erros_servidor WHERE tipo='ValueError' ORDER BY id").fetchall()
            self.assertEqual(len(linhas), 2)
            self.assertEqual(linhas[0]["rota"], "/api/teste-erro/:id/:token")
            self.assertEqual(linhas[0]["assinatura"], linhas[1]["assinatura"])
            self.assertIn("Traceback", linhas[0]["traceback"])
            self.assertNotIn("ana@exemplo.com", linhas[0]["traceback"] + linhas[0]["mensagem"])
            # passados 30 minutos, o mesmo erro avisa de novo
            conn.execute("UPDATE alertas_operacao SET ultimo=ultimo-1801 WHERE chave=?", ("erro:" + linhas[0]["assinatura"],))
            conn.commit()
            conn.close()
            self.req("GET", caminho)
            self.assertEqual(len(self.emails), 2)
        finally:
            server.Handler.route = original
        # painel: lista, resolve e reabre
        s, d = self.req("GET", "/api/dono/operacao/erros", cab=self.dono)
        abertos = [e for e in d["erros"] if e["tipo"] == "ValueError"]
        self.assertEqual(len(abertos), 3)
        eid = abertos[0]["id"]
        self.assertEqual(self.req("POST", "/api/dono/operacao/erros/%d/resolver" % eid, {"resolvido": True}, self.dono)[0], 200)
        _, d = self.req("GET", "/api/dono/operacao/erros", cab=self.dono)
        self.assertNotIn(eid, [e["id"] for e in d["erros"]])
        _, d = self.req("GET", "/api/dono/operacao/erros?todos=1", cab=self.dono)
        self.assertIn(eid, [e["id"] for e in d["erros"]])
        self.assertEqual(self.req("POST", "/api/dono/operacao/erros/999999/resolver", {}, self.dono)[0], 404)
        # resumo diário: uma vez por dia, só com erros
        conn = server.db()
        conn.execute("UPDATE erros_servidor SET quando=datetime('now','-1 day') WHERE tipo='ValueError'")
        conn.commit()
        self.emails.clear()
        hoje = datetime.datetime.utcnow().date()
        self.assertEqual(operacao.enviar_resumo_diario(conn, hoje), 3)
        self.assertEqual(len(self.emails), 1)
        self.assertIn("Error digest", self.emails[0][1])
        self.assertEqual(operacao.enviar_resumo_diario(conn, hoje), 0)
        self.assertEqual(len(self.emails), 1)
        conn.close()

    def test_alertas_de_condicao(self):
        conn = server.db()
        server.config_set(conn, "dono_email", "dono@bussola.test")
        server.config_set(conn, "dono_idioma", "es")
        conn.commit()
        conn.execute("DELETE FROM alertas_operacao WHERE chave LIKE 'cond:%'")
        conn.commit()
        uso = operacao._uso_disco
        operacao._uso_disco = lambda: (0.91, 5e9)
        try:
            server.backup_diario()
            u = operacao.ultimo_backup_local()
            velho = time.time() - 30 * 3600
            os.utime(u[0], (velho, velho))
            eid = conn.execute("INSERT INTO empresas (nome, slug) VALUES ('Voz', 'voz-x')").lastrowid
            cand = conn.execute("INSERT INTO candidatos (token, nome, email, empresa_id) VALUES ('tk-v','B','b@x.com',?)", (eid,)).lastrowid
            cargo = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('C', ?)", (eid,)).lastrowid
            vaga = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'V', 'aberta', ?)", (cargo, eid)).lastrowid
            ca = conn.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cand, vaga)).lastrowid
            conn.execute("INSERT INTO voz_chamadas (candidatura_id, candidato_id, status, iniciada_em)"
                         " VALUES (?,?,'em_andamento', datetime('now','-2 hours'))", (ca, cand))
            for i in range(5):
                conn.execute("INSERT INTO voz_chamadas (candidatura_id, candidato_id, status, erro, terminada_em)"
                             " VALUES (?,?,'falhou','twilio_error', datetime('now','-10 minutes'))", (ca, cand))
            conn.commit()
            agora = time.time()
            avisados = operacao.verificar_condicoes(conn, agora)
            self.assertEqual(sorted(avisados), ["backup_local", "disco", "voz_falhas", "voz_presa"])
            self.assertEqual(len(self.emails), 4)
            self.assertTrue(all(e[3] == "es" and e[0] == "dono@bussola.test" for e in self.emails))
            self.assertTrue(any("Disco casi lleno" in e[1] for e in self.emails))
            # dentro de 6 horas: nada; depois: avisa de novo
            self.assertEqual(operacao.verificar_condicoes(conn, agora + 60), [])
            self.assertEqual(operacao.verificar_condicoes(conn, agora + 5 * 3600), [])
            # (as falhas de voz já saíram da janela de 1 hora)
            self.assertEqual(sorted(operacao.verificar_condicoes(conn, agora + 6 * 3600 + 5)),
                             ["backup_local", "disco", "voz_presa"])
            # condição resolvida: some da lista
            operacao._uso_disco = lambda: (0.5, 5e10)
            self.assertNotIn("disco", [c for c, _ in operacao.condicoes_ativas(conn)])
            s, d = self.req("GET", "/api/dono/operacao", cab=self.dono)
            self.assertIn("voz_presa", d["condicoes"])
        finally:
            operacao._uso_disco = uso
            conn.execute("DELETE FROM voz_chamadas")
            conn.commit()
            conn.close()

    def test_sem_travessoes(self):
        for arq in ("operacao.py", "teste_operacao.py", "public/js/dono-operacao.js", ".github/workflows/saude.yml"):
            caminho = os.path.join(AQUI, arq)
            if not os.path.exists(caminho):
                continue
            with open(caminho, encoding="utf-8") as fh:
                texto = fh.read()
            for proibido in (chr(0x2014), chr(0x2013)):
                self.assertFalse(proibido in texto, "travessão em " + arq)


if __name__ == "__main__":
    unittest.main(verbosity=2)
