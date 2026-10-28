"""
Testes das vagas públicas (vagas_publicas.py): página da vaga com JSON-LD para o
Google for Jobs, sitemap.xml, robots.txt, marca da empresa e campos novos da vaga.

Uso:  python3 teste_vagas_publicas.py
"""
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="vagas-pub-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import mensagens  # noqa: E402
import server  # noqa: E402

BASE_PUBLICA = "https://rh.exemplo.com"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


class TestVagasPublicas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        conn = server.db()
        server.config_set(conn, "url_publica", BASE_PUBLICA)
        cls.ea, cls.slug_a = empresas.criar_empresa(conn, "Empresa Alfa")
        cls.eb, cls.slug_b = empresas.criar_empresa(conn, "Empresa Beta")
        cls.ec, cls.slug_c = empresas.criar_empresa(conn, "Empresa Suspensa")
        conn.execute("UPDATE empresas SET status='suspensa' WHERE id=?", (cls.ec,))
        for login, eid in (("admin.a", cls.ea), ("admin.b", cls.eb)):
            conn.execute("INSERT INTO gestores (login, senha, nome, is_admin, aprovado, empresa_id) VALUES (?,?,?,1,1,?)",
                         (login, server.hash_senha("senha-123"), login.title(), eid))
        cls.cargo_a = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Técnico', ?)", (cls.ea,)).lastrowid
        cls.cargo_b = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Vendas', ?)", (cls.eb,)).lastrowid
        cargo_c = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('X', ?)", (cls.ec,)).lastrowid
        cls.pausada_b = conn.execute(
            "INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Vendedor pausado', 'pausada', ?)",
            (cls.cargo_b, cls.eb)).lastrowid
        cls.aberta_b = conn.execute(
            "INSERT INTO vagas (cargo_id, titulo, status, empresa_id, descricao) VALUES (?, 'Vendedor', 'aberta', ?, 'Vender')",
            (cls.cargo_b, cls.eb)).lastrowid
        cls.vaga_c = conn.execute(
            "INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Oculta', 'aberta', ?)",
            (cargo_c, cls.ec)).lastrowid
        cls.expirada_b = conn.execute(
            "INSERT INTO vagas (cargo_id, titulo, status, empresa_id, data_validade) VALUES (?, 'Antiga', 'aberta', ?, '2000-01-01')",
            (cls.cargo_b, cls.eb)).lastrowid
        conn.commit()
        assert mensagens.salvar_logo(conn, cls.ea, "logo.png", PNG) is None
        conn.close()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

        # vaga da empresa A criada pelo painel do gestor, com os campos novos
        cab = cls.token("admin.a")
        s, d = cls.req("POST", "/api/gestor/vaga", {
            "titulo": "Técnico de HVAC", "cargo_id": cls.cargo_a, "local": "Danbury", "pais": "Estados Unidos",
            "descricao": "Resumo curto", "status": "aberta",
            "descricao_rica": "Primeiro parágrafo <b>com tag</b>.\n\n- Item um\n- Item dois",
            "tipo_emprego": "full_time", "salario_min": "25", "salario_max": 32.5, "salario_unidade": "HOUR",
            "moeda": "USD", "endereco_cidade": "Danbury", "endereco_estado": "CT", "endereco_cep": "06810",
            "remoto": False, "data_validade": "2099-12-31",
        }, cab)
        assert s == 200, d
        s, d = cls.req("GET", "/api/gestor/vagas", cab=cab)
        cls.vaga_a = [v for v in d["vagas"] if v["titulo"] == "Técnico de HVAC"][0]

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        shutil.rmtree(PASTA, ignore_errors=True)

    @classmethod
    def req(cls, metodo, caminho, dados=None, cab=None):
        corpo = json.dumps(dados).encode() if dados is not None else None
        h = {"Content-Type": "application/json"}
        h.update(cab or {})
        r = urllib.request.Request(cls.base + caminho, data=corpo, method=metodo, headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    @classmethod
    def token(cls, login):
        s, d = cls.req("POST", "/api/gestor/login", {"login": login, "senha": "senha-123"})
        assert s == 200, d
        return {"X-Gestor-Token": d["token"]}

    def bruto(self, caminho, cab=None):
        r = urllib.request.Request(self.base + caminho, headers=cab or {})
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, resp.headers, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read().decode("utf-8")

    def json_ld(self, html):
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(m, "JSON-LD ausente")
        return json.loads(m.group(1))

    # ------------------------------------------------------------ campos
    def test_campos_salvos_e_devolvidos(self):
        v = self.vaga_a
        self.assertEqual(v["tipo_emprego"], "FULL_TIME")
        self.assertEqual(v["salario_min"], 25.0)
        self.assertEqual(v["salario_max"], 32.5)
        self.assertEqual(v["endereco_cep"], "06810")
        self.assertFalse(v["remoto"])
        self.assertEqual(v["data_validade"], "2099-12-31")

    def test_validacao_dos_campos(self):
        cab = self.token("admin.a")
        base = {"titulo": "X", "cargo_id": self.cargo_a, "status": "pausada"}
        for extra, erro in (({"tipo_emprego": "SOMETIMES"}, "Invalid employment type"),
                            ({"salario_min": "abc"}, "Invalid pay amount"),
                            ({"salario_min": 30, "salario_max": 20}, "The minimum pay cannot be higher than the maximum"),
                            ({"salario_unidade": "DECADE"}, "Invalid pay period"),
                            ({"data_validade": "31/12/2099"}, "Invalid expiration date")):
            s, d = self.req("POST", "/api/gestor/vaga", dict(base, **extra), dict(cab, **{"X-Idioma": "en"}))
            self.assertEqual(s, 400, extra)
            self.assertEqual(d["erro"], erro)

    def test_edicao_parcial_preserva_campos(self):
        cab = self.token("admin.a")
        v = self.vaga_a
        # cliente antigo, sem os campos novos: nada se perde
        s, _ = self.req("POST", "/api/gestor/vaga", {"id": v["id"], "titulo": v["titulo"], "cargo_id": self.cargo_a,
                                                    "local": "Danbury", "pais": "Estados Unidos",
                                                    "descricao": "Resumo curto", "status": "aberta"}, cab)
        self.assertEqual(s, 200)
        s, d = self.req("GET", "/api/gestor/vagas", cab=cab)
        nova = [x for x in d["vagas"] if x["id"] == v["id"]][0]
        self.assertEqual(nova["salario_max"], 32.5)
        self.assertEqual(nova["endereco_estado"], "CT")
        # outra empresa não edita a vaga
        s, _ = self.req("POST", "/api/gestor/vaga", {"id": v["id"], "titulo": "Invadido", "cargo_id": self.cargo_b,
                                                    "salario_min": 1}, self.token("admin.b"))
        self.assertNotEqual(s, 200)

    # ------------------------------------------------------------ página da vaga
    def test_pagina_com_json_ld(self):
        s, h, html = self.bruto("/vaga?id=%d&lang=en" % self.vaga_a["id"])
        self.assertEqual(s, 200)
        self.assertIn("text/html", h["Content-Type"])
        self.assertIn("Técnico de HVAC", html)  # texto principal sem JavaScript
        self.assertIn("Apply now", html)
        self.assertIn("/candidato?vaga=%d&amp;e=%s" % (self.vaga_a["id"], self.slug_a), html)
        self.assertIn("/api/empresa/%s/logo" % self.slug_a, html)
        self.assertIn("$25 to $32.50 per hour", html)
        self.assertNotIn("<b>com tag</b>", html)  # texto do gestor sempre escapado
        ld = self.json_ld(html)
        self.assertEqual(ld["@context"], "https://schema.org/")
        self.assertEqual(ld["@type"], "JobPosting")
        self.assertEqual(ld["title"], "Técnico de HVAC")
        self.assertIn("<ul><li>Item um</li><li>Item dois</li></ul>", ld["description"])
        self.assertIn("&lt;b&gt;", ld["description"])
        self.assertTrue(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$", ld["datePosted"]))
        self.assertEqual(ld["validThrough"], "2099-12-31T23:59:59")
        self.assertEqual(ld["employmentType"], "FULL_TIME")
        self.assertTrue(ld["directApply"])
        org = ld["hiringOrganization"]
        self.assertEqual(org["name"], "Empresa Alfa")
        self.assertTrue(org["logo"].startswith(BASE_PUBLICA + "/api/empresa/%s/logo" % self.slug_a))
        self.assertEqual(ld["identifier"]["value"], str(self.vaga_a["id"]))
        end = ld["jobLocation"]["address"]
        self.assertEqual(end, {"@type": "PostalAddress", "addressCountry": "US", "addressLocality": "Danbury",
                               "addressRegion": "CT", "postalCode": "06810"})
        sal = ld["baseSalary"]
        self.assertEqual(sal["@type"], "MonetaryAmount")
        self.assertEqual(sal["currency"], "USD")
        self.assertEqual(sal["value"], {"@type": "QuantitativeValue", "minValue": 25.0, "maxValue": 32.5,
                                        "unitText": "HOUR"})
        self.assertEqual(ld["url"], BASE_PUBLICA + "/vaga?id=%d" % self.vaga_a["id"])

    def test_idiomas_e_sem_travessoes(self):
        for lang, texto in (("pt", "Candidatar-se"), ("es", "Postularme"), ("en", "Apply now")):
            s, _, html = self.bruto("/vaga?id=%d&lang=%s" % (self.vaga_a["id"], lang))
            self.assertEqual(s, 200)
            self.assertIn(texto, html)
            self.assertNotIn("\u2014", html)
            self.assertNotIn("\u2013", html)
        s, _, html = self.bruto("/vaga?id=%d" % self.vaga_a["id"], {"Accept-Language": "es-MX,es;q=0.9"})
        self.assertIn("Postularme", html)

    def test_vaga_remota_e_minima(self):
        # vaga sem campos extras: JSON-LD válido, sem salário e com país padrão
        s, _, html = self.bruto("/vaga?id=%d" % self.aberta_b)
        self.assertEqual(s, 200)
        ld = self.json_ld(html)
        self.assertNotIn("baseSalary", ld)
        self.assertNotIn("validThrough", ld)
        self.assertEqual(ld["description"], "<p>Vender</p>")
        self.assertNotIn("logo", ld["hiringOrganization"])
        cab = self.token("admin.b")
        s, _ = self.req("POST", "/api/gestor/vaga", {"id": self.aberta_b, "titulo": "Vendedor", "cargo_id": self.cargo_b,
                                                    "descricao": "Vender", "status": "aberta", "remoto": True,
                                                    "salario_min": 50000, "salario_unidade": "YEAR", "moeda": "brl"}, cab)
        self.assertEqual(s, 200)
        ld = self.json_ld(self.bruto("/vaga?id=%d" % self.aberta_b)[2])
        self.assertEqual(ld["jobLocationType"], "TELECOMMUTE")
        self.assertEqual(ld["applicantLocationRequirements"]["name"], "US")
        self.assertEqual(ld["baseSalary"]["currency"], "BRL")
        self.assertEqual(ld["baseSalary"]["value"]["value"], 50000.0)

    def test_vagas_nao_publicas_404(self):
        cab = self.token("admin.a")
        conn = server.db()
        fechada = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Fechada', 'encerrada', ?)",
                               (self.cargo_a, self.ea)).lastrowid
        conn.commit()
        conn.close()
        for vid in (fechada, self.pausada_b, self.vaga_c, 999999):
            s, _, html = self.bruto("/vaga?id=%d" % vid)
            self.assertEqual(s, 404, vid)
            self.assertNotIn("application/ld+json", html)
            self.assertIn("noindex", html)
        self.assertEqual(self.bruto("/vaga?id=abc")[0], 404)
        self.assertEqual(self.bruto("/vaga")[0], 404)
        self.assertIsNotNone(cab)

    def test_vaga_expirada_sem_json_ld(self):
        s, _, html = self.bruto("/vaga?id=%d&lang=en" % self.expirada_b)
        self.assertEqual(s, 200)
        self.assertNotIn("application/ld+json", html)
        self.assertIn("Applications for this job have closed.", html)

    def test_endereco_alternativo_redireciona(self):
        r = urllib.request.Request(self.base + "/vagas/%d" % self.vaga_a["id"], method="GET")

        class SemSeguir(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        try:
            urllib.request.build_opener(SemSeguir).open(r)
            self.fail("esperava 301")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 301)
            self.assertEqual(e.headers["Location"], "/vaga?id=%d" % self.vaga_a["id"])

    # ------------------------------------------------------------ sitemap e robots
    def test_sitemap(self):
        s, h, xml = self.bruto("/sitemap.xml")
        self.assertEqual(s, 200)
        self.assertIn("application/xml", h["Content-Type"])
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        self.assertIn("<loc>%s/</loc>" % BASE_PUBLICA, xml)
        self.assertIn("<loc>%s/vagas?e=%s</loc>" % (BASE_PUBLICA, self.slug_a), xml)
        self.assertIn("<loc>%s/vagas?e=%s</loc>" % (BASE_PUBLICA, self.slug_b), xml)
        self.assertIn("<loc>%s/vaga?id=%d</loc>" % (BASE_PUBLICA, self.vaga_a["id"]), xml)
        self.assertIn("<loc>%s/vaga?id=%d</loc>" % (BASE_PUBLICA, self.aberta_b), xml)
        for oculta in (self.pausada_b, self.vaga_c, self.expirada_b):
            self.assertNotIn("/vaga?id=%d<" % oculta, xml)
        self.assertNotIn(self.slug_c, xml)
        self.assertEqual(xml.count("<url>"), xml.count("<lastmod>"))
        self.assertTrue(re.search(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", xml))

    def test_robots(self):
        s, h, txt = self.bruto("/robots.txt")
        self.assertEqual(s, 200)
        self.assertTrue(h["Content-Type"].startswith("text/plain"))
        for linha in ("Allow: /vagas", "Allow: /vaga", "Disallow: /api/", "Disallow: /gestor", "Disallow: /dono",
                      "Disallow: /onboarding", "Disallow: /agendar", "Disallow: /assinar", "Disallow: /candidato",
                      "Sitemap: %s/sitemap.xml" % BASE_PUBLICA):
            self.assertIn(linha, txt.splitlines())
        with open(os.path.join(AQUI, "public", "robots.txt"), encoding="utf-8") as f:
            self.assertIn("Sitemap: https://rh.tonybelleza.com/sitemap.xml", f.read())

    # ------------------------------------------------------------ marca
    def test_marca_publica(self):
        s, d = self.req("GET", "/api/empresa/%s/marca" % self.slug_a)
        self.assertEqual(s, 200)
        self.assertEqual(d["nome"], "Empresa Alfa")
        self.assertTrue(d["logo_url"].startswith("/api/empresa/%s/logo" % self.slug_a))
        s, d = self.req("GET", "/api/empresa/%s/marca" % self.slug_b)
        self.assertEqual((s, d["logo_url"]), (200, ""))
        self.assertEqual(self.req("GET", "/api/empresa/%s/marca" % self.slug_c)[0], 404)
        s, d = self.req("GET", "/api/vagas?e=%s" % self.slug_a)
        self.assertEqual(d["empresa"]["nome"], "Empresa Alfa")
        self.assertTrue(d["empresa"]["logo_url"].startswith("/api/empresa/"))
        # a lista pública de B não mostra a vaga pausada nem vagas de A
        s, d = self.req("GET", "/api/vagas?e=%s" % self.slug_b)
        ids = {v["id"] for v in d["vagas"]}
        self.assertNotIn(self.pausada_b, ids)
        self.assertNotIn(self.vaga_a["id"], ids)

    def test_sem_travessoes_nos_arquivos(self):
        for arq in ("vagas_publicas.py", "teste_vagas_publicas.py", "public/js/gestor-vaga-campos.js",
                    "public/robots.txt", "public/vagas.html"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                texto = f.read()
            self.assertNotIn("\u2014", texto, arq)
            self.assertNotIn("\u2013", texto, arq)


if __name__ == "__main__":
    unittest.main(verbosity=2)
