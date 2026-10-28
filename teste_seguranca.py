"""
Testes de segurança (seguranca.py): robôs de varredura, bloqueio por IP,
cabeçalhos de segurança, limite na recuperação de acesso e trilha de auditoria.

Uso:  python3 teste_seguranca.py
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="seg-teste-")
for arquivo in ("server.py", "voz.py", "empresas.py", "mensagens.py", "erros_i18n.py", "eventos_i18n.py", "entrada.py",
                "agenda.py", "talentos.py", "seguranca.py", "planos.py", "indicacoes.py",
                "onboarding.py", "formularios.py", "vagas_publicas.py", "relatorios.py", "campanhas.py", "assistente.py", "telefonia.py"):
    if os.path.exists(os.path.join(AQUI, arquivo)):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import seguranca  # noqa: E402
import server  # noqa: E402


class TestSeguranca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        conn = server.db()
        cls.ea, _ = empresas.criar_empresa(conn, "Empresa A")
        cls.eb, _ = empresas.criar_empresa(conn, "Empresa B")
        for login, admin, eid in (("admin.a", 1, cls.ea), ("gestor.a", 0, cls.ea), ("admin.b", 1, cls.eb)):
            conn.execute("INSERT INTO gestores (login, senha, nome, is_admin, aprovado, empresa_id) VALUES (?,?,?,?,1,?)",
                         (login, server.hash_senha("senha-123"), login.title(), admin, eid))
        cls.cand = conn.execute("INSERT INTO candidatos (token, nome, email, empresa_id) VALUES ('t1','Maria','m@x.com',?)",
                                (cls.ea,)).lastrowid
        conn.commit()
        conn.close()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        seguranca._suspeitos.clear()
        seguranca._bloqueados.clear()
        server._login_falhas.clear()

    @staticmethod
    def _json(bruto):
        try:
            return json.loads(bruto or b"{}")
        except ValueError:
            return {}

    def req(self, metodo, caminho, dados=None, cab=None, ip="10.0.0.1"):
        corpo = json.dumps(dados).encode() if dados is not None else None
        h = {"Content-Type": "application/json", "X-Forwarded-For": ip}
        h.update(cab or {})
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, resp.headers, self._json(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, e.headers, self._json(e.read())

    def token(self, login, ip="10.0.0.1"):
        s, _, d = self.req("POST", "/api/gestor/login", {"login": login, "senha": "senha-123"}, ip=ip)
        self.assertEqual(s, 200, d)
        return {"X-Gestor-Token": d["token"]}

    def test_robos_recebem_404_e_sao_bloqueados(self):
        for caminho in ("/.env", "/wp-admin/setup.php", "/cgi-bin/x", "/phpmyadmin/", "/.git/config", "/admin/info.php"):
            self.assertEqual(self.req("GET", caminho, ip="6.6.6.6")[0], 404)
        self.assertEqual(self.req("GET", "/", ip="6.6.6.6")[0], 403)
        self.assertEqual(self.req("GET", "/", ip="7.7.7.7")[0], 200)

    def test_paginas_e_api_normais_nao_sao_afetadas(self):
        for caminho in ("/", "/gestor", "/candidato", "/vagas", "/js/gestor.js", "/api/gestor/setup"):
            self.assertEqual(self.req("GET", caminho)[0], 200, caminho)

    def test_cabecalhos_de_seguranca(self):
        _, h, _ = self.req("GET", "/gestor")
        self.assertEqual(h["X-Content-Type-Options"], "nosniff")
        self.assertEqual(h["X-Frame-Options"], "DENY")
        self.assertIn("microphone=(self)", h["Permissions-Policy"])
        _, h, _ = self.req("GET", "/api/gestor/setup")
        self.assertEqual(h["X-Frame-Options"], "DENY")

    def test_limite_na_recuperacao_de_acesso(self):
        codigos = [self.req("POST", "/api/candidato/recuperar-acesso", {"email": "x%d@x.com" % i}, ip="8.8.8.8")[0]
                   for i in range(10)]
        self.assertIn(429, codigos)

    def test_auditoria_de_login_leitura_e_alteracao(self):
        self.req("POST", "/api/gestor/login", {"login": "gestor.a", "senha": "errada"}, ip="9.9.9.9")
        g = self.token("gestor.a")
        self.assertEqual(self.req("GET", "/api/gestor/candidato/%d" % self.cand, cab=g)[0], 200)
        self.req("POST", "/api/gestor/candidato/%d/tags" % self.cand, {"tags": ["vip"]}, cab=g)
        self.assertEqual(self.req("GET", "/api/gestor/auditoria", cab=g)[0], 403)
        s, _, d = self.req("GET", "/api/gestor/auditoria", cab=self.token("admin.a"))
        self.assertEqual(s, 200)
        acoes = [(r["acao"], r["alvo"]) for r in d["registros"]]
        self.assertIn(("login_falhou", "gestor.a"), acoes)
        self.assertIn(("ver_candidato", str(self.cand)), acoes)
        self.assertTrue(any(a.startswith("post candidato/") for a, _ in acoes))
        self.assertTrue(any(a == "login" for a, _ in acoes))
        # a outra empresa não vê nada disso
        s, _, d = self.req("GET", "/api/gestor/auditoria", cab=self.token("admin.b"))
        self.assertFalse([r for r in d["registros"] if r["acao"] == "ver_candidato"])


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
