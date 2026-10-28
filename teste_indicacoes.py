"""
Testes do link de indicação (indicacoes.py).

Uso:  python3 teste_indicacoes.py
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
PASTA = tempfile.mkdtemp(prefix="ind-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import server  # noqa: E402


class TestIndicacoes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        conn = server.db()
        cls.ea, cls.slug_a = empresas.criar_empresa(conn, "Empresa A")
        cls.eb, cls.slug_b = empresas.criar_empresa(conn, "Empresa B")
        for login, admin, eid in (("admin.a", 1, cls.ea), ("gestor.a", 0, cls.ea), ("admin.b", 1, cls.eb)):
            conn.execute("INSERT INTO gestores (login, senha, nome, is_admin, aprovado, empresa_id) VALUES (?,?,?,?,1,?)",
                         (login, server.hash_senha("senha-123"), login.title(), admin, eid))
        cls.tecnica = conn.execute("INSERT INTO candidatos (token, nome, email, empresa_id) VALUES ('tk','Rosa Lima','rosa@x.com',?)",
                                   (cls.ea,)).lastrowid
        cargo = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Tech', ?)", (cls.ea,)).lastrowid
        cls.vaga = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Tech', 'aberta', ?)",
                                (cargo, cls.ea)).lastrowid
        conn.commit()
        conn.close()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def req(self, metodo, caminho, dados=None, cab=None):
        corpo = json.dumps(dados).encode() if dados is not None else None
        h = {"Content-Type": "application/json"}
        h.update(cab or {})
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def token(self, login):
        s, d = self.req("POST", "/api/gestor/login", {"login": login, "senha": "senha-123"})
        self.assertEqual(s, 200, d)
        return {"X-Gestor-Token": d["token"]}

    def test_fluxo_completo(self):
        admin = self.token("admin.a")
        self.assertEqual(self.req("POST", "/api/gestor/indicacoes/config", {"ativo": True}, self.token("gestor.a"))[0], 403)
        s, d = self.req("POST", "/api/gestor/indicacoes/config", {"ativo": True, "valor_bonus": "$100", "dias_bonus": 0}, admin)
        self.assertEqual(s, 200, d)
        s, d = self.req("POST", "/api/gestor/indicacoes/candidato/%d" % self.tecnica, cab=admin)
        codigo = d["codigo"]
        self.assertTrue(codigo and ("ref=" + codigo) in d["link"])
        # página pública mostra só o primeiro nome
        s, d = self.req("GET", "/api/indicacao?e=%s&ref=%s" % (self.slug_a, codigo))
        self.assertEqual((s, d["primeiro_nome"]), (200, "Rosa"))
        self.assertEqual(self.req("GET", "/api/indicacao?e=%s&ref=%s" % (self.slug_b, codigo))[0], 404)
        # cadastro com o código
        s, d = self.req("POST", "/api/candidato/cadastro", {
            "nome": "Ana Indicada", "email": "ana.ind@x.com", "telefone": "+1 860 555 0100", "local": "Hartford",
            "vaga_id": self.vaga, "empresa": self.slug_a, "indicacao": codigo, "consentimento": True})
        self.assertEqual(s, 200, d)
        s, d = self.req("GET", "/api/gestor/indicacoes", cab=admin)
        self.assertEqual(len(d["indicacoes"]), 1)
        ind = d["indicacoes"][0]
        self.assertEqual((ind["indicador"], ind["indicado"], ind["situacao"]), ("Rosa Lima", "Ana Indicada", "inscrito"))
        # contratado: com 0 dias o bônus já vence
        conn = server.db()
        conn.execute("UPDATE candidaturas SET etapa='contratado' WHERE candidato_id=?", (ind["indicado_id"],))
        conn.commit()
        conn.close()
        s, d = self.req("GET", "/api/gestor/indicacoes", cab=admin)
        self.assertEqual(d["indicacoes"][0]["situacao"], "devido")
        self.assertEqual(self.req("POST", "/api/gestor/indicacoes/%d/pago" % ind["id"], {"pago": True}, admin)[0], 200)
        s, d = self.req("GET", "/api/gestor/indicacoes", cab=admin)
        self.assertEqual(d["indicacoes"][0]["situacao"], "pago")
        # a outra empresa não vê nada
        s, d = self.req("GET", "/api/gestor/indicacoes", cab=self.token("admin.b"))
        self.assertEqual(d["indicacoes"], [])
        self.assertEqual(self.req("GET", "/api/gestor/indicacoes/candidato/%d" % self.tecnica, cab=self.token("admin.b"))[0], 404)

    def test_codigo_de_outra_empresa_e_ignorado(self):
        admin = self.token("admin.a")
        _, d = self.req("POST", "/api/gestor/indicacoes/candidato/%d" % self.tecnica, cab=admin)
        s, _ = self.req("POST", "/api/candidato/cadastro", {
            "nome": "Beto B", "email": "beto@x.com", "telefone": "+1 860 555 0101", "local": "X",
            "empresa": self.slug_b, "indicacao": d["codigo"], "consentimento": True})
        self.assertEqual(s, 200)
        conn = server.db()
        n = conn.execute("SELECT COUNT(*) FROM indicacoes WHERE empresa_id=?", (self.eb,)).fetchone()[0]
        conn.close()
        self.assertEqual(n, 0)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
