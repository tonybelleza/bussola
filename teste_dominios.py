"""
Testes dos domínios próprios por empresa (dominios.py): validação do hostname,
verificação por DNS (A/CNAME) e TXT, "ask" do Caddy, mapeamento do Host, redirecionamento
de /gestor e /dono, URLs canônicas (página da vaga, JSON-LD e sitemap) e isolamento.

As consultas DNS são simuladas (dominios.resolver_ips e dominios.consultar_txt).

Uso:  python3 teste_dominios.py
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
PASTA = tempfile.mkdtemp(prefix="dominios-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)

import dominios  # noqa: E402
import empresas  # noqa: E402
import erros_i18n  # noqa: E402
import server  # noqa: E402

BASE_PUBLICA = "https://rh.exemplo.com"
IP_PLATAFORMA = "203.0.113.10"

# DNS simulado
DNS = {"rh.exemplo.com": {IP_PLATAFORMA}}
TXT = {}
TXT_FALHA = set()


def resolver_falso(host):
    return set(DNS.get(host, set()))


def txt_falso(nome):
    if nome in TXT_FALHA:
        raise OSError("timeout")
    return list(TXT.get(nome, []))


CONSULTAR_TXT_REAL = dominios.consultar_txt
dominios.resolver_ips = resolver_falso
dominios.consultar_txt = txt_falso


class SemSeguir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


class TestDominios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        conn = server.db()
        server.config_set(conn, "url_publica", BASE_PUBLICA)
        cls.ea, cls.slug_a = empresas.criar_empresa(conn, "Empresa Alfa")
        cls.eb, cls.slug_b = empresas.criar_empresa(conn, "Empresa Beta")
        cls.ec, cls.slug_c = empresas.criar_empresa(conn, "Empresa Gama")
        for login, eid, admin in (("admin.a", cls.ea, 1), ("comum.a", cls.ea, 0), ("admin.b", cls.eb, 1),
                                  ("admin.c", cls.ec, 1)):
            conn.execute("INSERT INTO gestores (login, senha, nome, is_admin, aprovado, empresa_id) VALUES (?,?,?,?,1,?)",
                         (login, server.hash_senha("senha-123"), login.title(), admin, eid))
        cargo_a = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Técnico', ?)", (cls.ea,)).lastrowid
        cargo_b = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Vendas', ?)", (cls.eb,)).lastrowid
        cls.vaga_a = conn.execute(
            "INSERT INTO vagas (cargo_id, titulo, status, empresa_id, descricao) VALUES (?, 'Técnico HVAC', 'aberta', ?, 'Consertar')",
            (cargo_a, cls.ea)).lastrowid
        cls.vaga_b = conn.execute(
            "INSERT INTO vagas (cargo_id, titulo, status, empresa_id, descricao) VALUES (?, 'Vendedor', 'aberta', ?, 'Vender')",
            (cargo_b, cls.eb)).lastrowid
        conn.commit()
        conn.close()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.porta = cls.httpd.server_address[1]
        cls.base = "http://127.0.0.1:%d" % cls.porta
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.cab_a = cls.token("admin.a")
        cls.cab_b = cls.token("admin.b")
        cls.cab_c = cls.token("admin.c")
        # domínio da empresa A, verificado
        s, d = cls.req("POST", "/api/gestor/dominios", {"dominio": "https://Jobs.Alfa.com/vagas"}, cls.cab_a)
        assert s == 200, d
        cls.item_a = d["item"]
        DNS["jobs.alfa.com"] = {IP_PLATAFORMA}
        TXT["_bussola.jobs.alfa.com"] = [cls.item_a["token"]]
        s, d = cls.req("POST", "/api/gestor/dominios/%d/verificar" % cls.item_a["id"], None, cls.cab_a)
        assert s == 200 and d["resultado"]["ok"], d

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

    def bruto(self, caminho, host=None, seguir=True):
        cab = {"Host": host} if host else {}
        r = urllib.request.Request(self.base + caminho, headers=cab)
        abrir = urllib.request.urlopen if seguir else urllib.request.build_opener(SemSeguir).open
        try:
            with abrir(r) as resp:
                return resp.status, resp.headers, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read().decode("utf-8", "replace")

    def novo_dominio(self, cab, dominio):
        return self.req("POST", "/api/gestor/dominios", {"dominio": dominio}, cab)

    def conn(self):
        return server.db()

    # ------------------------------------------------------------ validação
    def test_normalizar(self):
        self.assertEqual(dominios.normalizar(" HTTPS://Jobs.Cliente.com:443/x?y "), "jobs.cliente.com")
        self.assertEqual(dominios.normalizar("vagas.empresa.com."), "vagas.empresa.com")
        self.assertEqual(dominios.normalizar("vagas.açaí.com.br"), "vagas.xn--aa-4iaz.com.br")
        self.assertEqual(dominios.normalizar("user@evil.com"), "")

    def test_validar_hostname(self):
        conn = self.conn()
        try:
            for ok in ("jobs.cliente.com", "cliente.com", "carreiras.cliente.com.br", "a-b.c-d.io",
                       "vagas.xn--aa-4iaz.com.br"):
                self.assertIsNone(dominios.validar(conn, ok), ok)
            for ruim in ("", "localhost", "cliente", "-a.com", "a-.com", "a..com", "1.2.3.4", "[::1]",
                         "jobs.cliente.c0m", "x" * 64 + ".com", "intranet.local", "site.test",
                         "a_b.com", "jobs.cliente.com/x"):
                self.assertEqual(dominios.validar(conn, ruim), "Domínio inválido", ruim)
            for plataforma in ("rh.exemplo.com", "x.rh.exemplo.com", "exemplo.com", "rh.tonybelleza.com",
                               "tonybelleza.com", "jobs.tonybelleza.com"):
                self.assertEqual(dominios.validar(conn, plataforma), "Este domínio pertence à plataforma", plataforma)
        finally:
            conn.close()

    def test_api_recusa_invalido_e_traduz(self):
        s, d = self.req("POST", "/api/gestor/dominios", {"dominio": "não é domínio"},
                        dict(self.cab_c, **{"X-Idioma": "en"}))
        self.assertEqual((s, d["erro"]), (400, "Invalid domain"))
        s, d = self.req("POST", "/api/gestor/dominios", {"dominio": "rh.exemplo.com"},
                        dict(self.cab_c, **{"X-Idioma": "es"}))
        self.assertEqual((s, d["erro"]), (400, "Este dominio pertenece a la plataforma"))
        self.assertEqual(erros_i18n.traduzir("Seu plano permite até 1 domínio(s) próprio(s)", "en"),
                         "Your plan allows up to 1 custom domain(s)")

    def test_somente_admin(self):
        cab = self.token("comum.a")
        self.assertEqual(self.req("GET", "/api/gestor/dominios", cab=cab)[0], 403)
        self.assertEqual(self.novo_dominio(cab, "outro.alfa.com")[0], 403)
        self.assertEqual(self.req("GET", "/api/gestor/dominios")[0], 401)

    def test_limite_do_plano(self):
        # A já tem 1 (limite padrão)
        s, d = self.req("GET", "/api/gestor/dominios", cab=self.cab_a)
        self.assertEqual((s, d["limite"], d["pode_adicionar"]), (200, 1, False))
        s, d = self.novo_dominio(self.cab_a, "carreiras.alfa.com")
        self.assertEqual((s, d["erro"]), (400, "Seu plano permite até 1 domínio(s) próprio(s)"))
        # plano com dominios_max = 2 no catálogo
        conn = self.conn()
        try:
            cat = server.planos.catalogo(conn)
            cat["planos"][0]["dominios_max"] = 2
            server.config_set(conn, "planos_catalogo", json.dumps(cat))
            conn.execute("UPDATE empresas SET plano=? WHERE id=?", (cat["planos"][0]["codigo"], self.ea))
            conn.commit()
            self.assertEqual(dominios.limite_da_empresa(conn, self.ea), 2)
            self.assertEqual(dominios.limite_da_empresa(conn, self.eb), 1)
        finally:
            conn.close()
        s, d = self.novo_dominio(self.cab_a, "carreiras.alfa.com")
        self.assertEqual(s, 200, d)
        self.assertFalse(d["pode_adicionar"])
        self.assertEqual(self.novo_dominio(self.cab_a, "mais.alfa.com")[0], 400)
        # repetido na mesma empresa
        conn = self.conn()
        try:
            conn.execute("UPDATE empresas SET plano='' WHERE id=?", (self.ea,))
            conn.commit()
        finally:
            conn.close()
        self.req("DELETE", "/api/gestor/dominios/%d" % d["item"]["id"], cab=self.cab_a)

    # ------------------------------------------------------------ verificação
    def test_verificacao_dns_e_txt(self):
        s, d = self.novo_dominio(self.cab_b, "vagas.beta.com")
        self.assertEqual(s, 200, d)
        item = d["item"]
        self.assertTrue(item["token"].startswith("bussola-verificacao="))
        ins = [i for i in d["dominios"] if i["id"] == item["id"]][0]["instrucoes"]
        self.assertEqual(ins["cname"], {"tipo": "CNAME", "nome": "vagas.beta.com", "valor": "rh.exemplo.com"})
        self.assertEqual(ins["a"]["valor"], IP_PLATAFORMA)
        self.assertEqual(ins["txt"], {"tipo": "TXT", "nome": "_bussola.vagas.beta.com", "valor": item["token"]})
        caminho = "/api/gestor/dominios/%d/verificar" % item["id"]
        try:
            # 1) sem DNS
            s, d = self.req("POST", caminho, None, self.cab_b)
            self.assertEqual((s, d["resultado"]["ok"], d["resultado"]["erro"]), (200, False, "dns"))
            # 2) DNS para outro IP
            DNS["vagas.beta.com"] = {"198.51.100.7"}
            self.assertEqual(self.req("POST", caminho, None, self.cab_b)[1]["resultado"]["erro"], "dns")
            # 3) CNAME resolvido para o IP da plataforma, sem TXT
            DNS["vagas.beta.com"] = {IP_PLATAFORMA, "2001:db8::1"}
            r = self.req("POST", caminho, None, self.cab_b)[1]["resultado"]
            self.assertEqual((r["dns"]["ok"], r["erro"]), (True, "txt"))
            # 4) TXT com outro valor e falha de rede do DoH
            TXT["_bussola.vagas.beta.com"] = ["bussola-verificacao=errado"]
            self.assertEqual(self.req("POST", caminho, None, self.cab_b)[1]["resultado"]["erro"], "txt")
            TXT_FALHA.add("_bussola.vagas.beta.com")
            self.assertEqual(self.req("POST", caminho, None, self.cab_b)[1]["resultado"]["erro"], "txt_rede")
            TXT_FALHA.discard("_bussola.vagas.beta.com")
            # ainda não verificado: o ask nega
            self.assertEqual(self.bruto("/api/dominios/permitido?domain=vagas.beta.com")[0], 404)
            # 5) tudo certo
            TXT["_bussola.vagas.beta.com"] = ["outro=1", item["token"]]
            s, d = self.req("POST", caminho, None, self.cab_b)
            self.assertTrue(d["resultado"]["ok"], d)
            self.assertTrue([i for i in d["dominios"] if i["id"] == item["id"]][0]["verificado"])
            self.assertEqual(self.bruto("/api/dominios/permitido?domain=vagas.beta.com")[0], 200)
            # registro A direto (sem CNAME) também vale
            DNS["vagas.beta.com"] = {IP_PLATAFORMA}
            self.assertTrue(self.req("POST", caminho, None, self.cab_b)[1]["resultado"]["ok"])
            # DNS removido: nova verificação falha e o domínio sai do ask
            DNS.pop("vagas.beta.com")
            self.assertFalse(self.req("POST", caminho, None, self.cab_b)[1]["resultado"]["ok"])
            self.assertEqual(self.bruto("/api/dominios/permitido?domain=vagas.beta.com")[0], 404)
        finally:
            self.req("DELETE", "/api/gestor/dominios/%d" % item["id"], cab=self.cab_b)
            TXT.pop("_bussola.vagas.beta.com", None)

    def test_ip_da_config(self):
        conn = self.conn()
        try:
            server.config_set(conn, "dominios_ip", "192.0.2.55")
            self.assertIn("192.0.2.55", dominios.ips_plataforma(conn))
            self.assertIn(IP_PLATAFORMA, dominios.ips_plataforma(conn))
            DNS["teste-ip.cliente.com"] = {"192.0.2.55"}
            self.assertTrue(dominios.checar_dns(conn, "teste-ip.cliente.com")[0])
            server.config_set(conn, "dominios_ip", "")
            self.assertFalse(dominios.checar_dns(conn, "teste-ip.cliente.com")[0])
        finally:
            conn.close()

    # ------------------------------------------------------------ ask do Caddy
    def test_ask_so_verificados(self):
        self.assertEqual(self.bruto("/api/dominios/permitido?domain=jobs.alfa.com")[0], 200)
        self.assertEqual(self.bruto("/api/dominios/permitido?domain=JOBS.ALFA.COM")[0], 200)
        for nao in ("", "desconhecido.com", "rh.exemplo.com", "carreiras.alfa.com", "jobs.alfa.com.evil.com"):
            self.assertEqual(self.bruto("/api/dominios/permitido?domain=" + nao)[0], 404, nao)
        # empresa suspensa perde o certificado
        conn = self.conn()
        try:
            conn.execute("UPDATE empresas SET status='suspensa' WHERE id=?", (self.ea,))
            conn.commit()
            dominios.limpar_cache()
            self.assertEqual(self.bruto("/api/dominios/permitido?domain=jobs.alfa.com")[0], 404)
            self.assertEqual(self.bruto("/", host="jobs.alfa.com")[2].count("lista-vagas"), 0)
        finally:
            conn.execute("UPDATE empresas SET status='ativa' WHERE id=?", (self.ea,))
            conn.commit()
            conn.close()
            dominios.limpar_cache()

    def test_ask_limite(self):
        antigo = dominios._ASK_LIMITE
        dominios._ASK_LIMITE = 3
        with dominios._ask_trava:
            del dominios._ask_hits[:]
        try:
            codigos = [self.bruto("/api/dominios/permitido?domain=x%d.cliente.com" % i)[0] for i in range(5)]
            self.assertEqual(codigos, [404, 404, 404, 429, 429])
            # verificado continua liberado mesmo com o limite estourado
            self.assertEqual(self.bruto("/api/dominios/permitido?domain=jobs.alfa.com")[0], 200)
        finally:
            dominios._ASK_LIMITE = antigo
            with dominios._ask_trava:
                del dominios._ask_hits[:]

    # ------------------------------------------------------------ mapeamento do Host
    def test_raiz_do_dominio_proprio_e_pagina_de_vagas(self):
        s, h, html = self.bruto("/", host="jobs.alfa.com")
        self.assertEqual(s, 200)
        self.assertIn('id="lista-vagas"', html)
        self.assertIn("/api/dominio", html)
        # com porta e no endereço principal: página inicial normal
        self.assertIn('id="lista-vagas"', self.bruto("/", host="jobs.alfa.com:443")[2])
        self.assertNotIn('id="lista-vagas"', self.bruto("/", host="rh.exemplo.com")[2])
        self.assertNotIn('id="lista-vagas"', self.bruto("/")[2])
        # domínio não verificado não é mapeado
        self.assertNotIn('id="lista-vagas"', self.bruto("/", host="desconhecido.com")[2])

    def test_api_dominio(self):
        s, h, corpo = self.bruto("/api/dominio", host="jobs.alfa.com")
        self.assertEqual(json.loads(corpo), {"slug": self.slug_a, "nome": "Empresa Alfa", "dominio": "jobs.alfa.com"})
        self.assertEqual(json.loads(self.bruto("/api/dominio", host="rh.exemplo.com")[2]), {"slug": None})
        self.assertEqual(json.loads(self.bruto("/api/dominio")[2]), {"slug": None})
        self.assertEqual(json.loads(self.bruto("/api/dominio", host="outra.com")[2]), {"slug": None})

    def test_paginas_publicas_no_dominio_proprio(self):
        for caminho in ("/candidato", "/vagas", "/css/style.css", "/js/candidato.js", "/js/tema.js"):
            self.assertEqual(self.bruto(caminho, host="jobs.alfa.com")[0], 200, caminho)
        # a API pública continua funcionando
        s, h, corpo = self.bruto("/api/vagas?e=" + self.slug_a, host="jobs.alfa.com")
        self.assertEqual(s, 200)
        self.assertEqual({v["id"] for v in json.loads(corpo)["vagas"]}, {self.vaga_a})

    def test_redireciona_gestor_e_dono(self):
        for caminho, destino in (("/gestor", BASE_PUBLICA + "/gestor"), ("/dono", BASE_PUBLICA + "/dono"),
                                 ("/gestor?reset=abc", BASE_PUBLICA + "/gestor?reset=abc"),
                                 ("/gestor.html", BASE_PUBLICA + "/gestor")):
            s, h, _ = self.bruto(caminho, host="jobs.alfa.com", seguir=False)
            self.assertEqual((s, h["Location"]), (302, destino), caminho)
        # no endereço principal o painel abre normalmente
        s, h, html = self.bruto("/gestor", host="rh.exemplo.com", seguir=False)
        self.assertEqual(s, 200)
        # a API do gestor segue funcionando pelo domínio próprio
        r = urllib.request.Request(self.base + "/api/gestor/dominios", headers=dict(self.cab_a, Host="jobs.alfa.com"))
        with urllib.request.urlopen(r) as resp:
            self.assertEqual(resp.status, 200)

    # ------------------------------------------------------------ URLs canônicas
    def test_pagina_da_vaga_canonica(self):
        s, h, html = self.bruto("/vaga?id=%d" % self.vaga_a, host="jobs.alfa.com")
        self.assertEqual(s, 200)
        self.assertIn('<link rel="canonical" href="https://jobs.alfa.com/vaga?id=%d">' % self.vaga_a, html)
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(ld["url"], "https://jobs.alfa.com/vaga?id=%d" % self.vaga_a)
        self.assertEqual(ld["hiringOrganization"]["sameAs"], "https://jobs.alfa.com/")
        # pelo endereço principal a canônica também aponta para o domínio próprio
        s, h, html = self.bruto("/vaga?id=%d" % self.vaga_a, host="rh.exemplo.com")
        self.assertIn('<link rel="canonical" href="https://jobs.alfa.com/vaga?id=%d">' % self.vaga_a, html)
        self.assertIn('hreflang="en" href="https://jobs.alfa.com/vaga?id=%d&amp;lang=en"' % self.vaga_a, html)
        # empresa sem domínio: canônica no endereço principal
        s, h, html = self.bruto("/vaga?id=%d" % self.vaga_b, host="rh.exemplo.com")
        self.assertIn('<link rel="canonical" href="%s/vaga?id=%d">' % (BASE_PUBLICA, self.vaga_b), html)
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(ld["hiringOrganization"]["sameAs"], "%s/vagas?e=%s" % (BASE_PUBLICA, self.slug_b))

    def test_isolamento_da_pagina_da_vaga(self):
        # vaga de B não abre no domínio de A
        self.assertEqual(self.bruto("/vaga?id=%d" % self.vaga_b, host="jobs.alfa.com")[0], 404)

    def test_sitemap_e_robots(self):
        s, h, xml = self.bruto("/sitemap.xml", host="jobs.alfa.com")
        self.assertEqual(s, 200)
        self.assertIn("<loc>https://jobs.alfa.com/</loc>", xml)
        self.assertIn("<loc>https://jobs.alfa.com/vaga?id=%d</loc>" % self.vaga_a, xml)
        self.assertNotIn("vaga?id=%d<" % self.vaga_b, xml)
        self.assertNotIn("rh.exemplo.com", xml)
        self.assertNotIn("/vagas?e=", xml)
        # sitemap principal: sem a empresa com domínio próprio
        s, h, xml = self.bruto("/sitemap.xml", host="rh.exemplo.com")
        self.assertIn("<loc>%s/vaga?id=%d</loc>" % (BASE_PUBLICA, self.vaga_b), xml)
        self.assertIn("<loc>%s/vagas?e=%s</loc>" % (BASE_PUBLICA, self.slug_b), xml)
        self.assertNotIn("vaga?id=%d<" % self.vaga_a, xml)
        self.assertNotIn("e=%s<" % self.slug_a, xml)
        txt = self.bruto("/robots.txt", host="jobs.alfa.com")[2]
        self.assertIn("Sitemap: https://jobs.alfa.com/sitemap.xml", txt.splitlines())
        self.assertIn("Sitemap: %s/sitemap.xml" % BASE_PUBLICA, self.bruto("/robots.txt")[2].splitlines())

    # ------------------------------------------------------------ isolamento
    def test_isolamento_entre_empresas(self):
        # B não vê, não verifica e não remove o domínio de A
        s, d = self.req("GET", "/api/gestor/dominios", cab=self.cab_b)
        self.assertNotIn("jobs.alfa.com", [i["dominio"] for i in d["dominios"]])
        self.assertEqual(self.req("POST", "/api/gestor/dominios/%d/verificar" % self.item_a["id"], None, self.cab_b)[0], 404)
        self.assertEqual(self.req("DELETE", "/api/gestor/dominios/%d" % self.item_a["id"], cab=self.cab_b)[0], 404)
        # B não cadastra domínio já verificado por A
        s, d = self.novo_dominio(self.cab_b, "jobs.alfa.com")
        self.assertEqual((s, d["erro"]), (400, "Este domínio já está em uso por outra empresa"))
        self.assertEqual(self.bruto("/api/dominios/permitido?domain=jobs.alfa.com")[0], 200)

    def test_pedido_pendente_nao_bloqueia_o_dono_real(self):
        # C reivindica primeiro sem provar posse; B verifica e o pedido de C some
        s, d = self.novo_dominio(self.cab_c, "talentos.beta.com")
        self.assertEqual(s, 200, d)
        s, d = self.novo_dominio(self.cab_b, "talentos.beta.com")
        self.assertEqual(s, 200, d)
        item_b = d["item"]
        self.assertNotEqual(item_b["token"], self.req("GET", "/api/gestor/dominios", cab=self.cab_c)[1]["dominios"][0]["token"])
        DNS["talentos.beta.com"] = {IP_PLATAFORMA}
        TXT["_bussola.talentos.beta.com"] = [item_b["token"]]
        try:
            self.assertTrue(self.req("POST", "/api/gestor/dominios/%d/verificar" % item_b["id"], None,
                                     self.cab_b)[1]["resultado"]["ok"])
            self.assertEqual(self.req("GET", "/api/gestor/dominios", cab=self.cab_c)[1]["dominios"], [])
            self.assertEqual(json.loads(self.bruto("/api/dominio", host="talentos.beta.com")[2])["slug"], self.slug_b)
        finally:
            self.req("DELETE", "/api/gestor/dominios/%d" % item_b["id"], cab=self.cab_b)
            DNS.pop("talentos.beta.com", None)
        # removido: deixa de ser mapeado
        self.assertEqual(json.loads(self.bruto("/api/dominio", host="talentos.beta.com")[2]), {"slug": None})

    # ------------------------------------------------------------ arquivos
    def test_doh_parse(self):
        # consultar_txt real com urlopen simulado (sem rede)
        resposta = json.dumps({"Status": 0, "Answer": [
            {"name": "_bussola.x.com.", "type": 16, "data": "\"bussola-verificacao=\" \"abc\""},
            {"name": "_bussola.x.com.", "type": 5, "data": "y.com."},
            {"name": "_bussola.x.com.", "type": 16, "data": "semaspas"}]}).encode()

        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return resposta

        visto = {}

        def abrir(req, timeout=None):
            visto["url"] = req.full_url
            visto["timeout"] = timeout
            return Resp()

        original = dominios.urllib.request.urlopen
        dominios.urllib.request.urlopen = abrir
        try:
            self.assertEqual(CONSULTAR_TXT_REAL("_bussola.x.com"), ["bussola-verificacao=abc", "semaspas"])
        finally:
            dominios.urllib.request.urlopen = original
        self.assertTrue(visto["url"].startswith("https://dns.google/resolve?"))
        self.assertIn("name=_bussola.x.com", visto["url"])
        self.assertIn("type=TXT", visto["url"])
        self.assertTrue(visto["timeout"])

    def test_sem_travessoes_nos_arquivos(self):
        for arq in ("dominios.py", "teste_dominios.py", "public/js/gestor-dominio.js", "vagas_publicas.py",
                    "public/vagas.html", "public/js/candidato.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                texto = f.read()
            self.assertNotIn(chr(0x2014), texto, arq)
            self.assertNotIn(chr(0x2013), texto, arq)

    def test_trilingue(self):
        with open(os.path.join(AQUI, "public", "js", "gestor-dominio.js"), encoding="utf-8") as f:
            js = f.read()
        blocos = re.findall(r"Object\.assign\(I18N_GESTOR\.(pt|en|es), \{(.*?)\n\}\);", js, re.S)
        self.assertEqual([b[0] for b in blocos], ["pt", "en", "es"])
        chaves = [set(re.findall(r"\b(dm_\w+):", b[1])) for b in blocos]
        self.assertTrue(chaves[0])
        self.assertEqual(chaves[0], chaves[1])
        self.assertEqual(chaves[0], chaves[2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
