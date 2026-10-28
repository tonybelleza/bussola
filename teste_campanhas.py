"""
Testes do aviso ao banco de talentos (campanhas.py).

Uso:  python3 teste_campanhas.py
"""
import html as _html
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="camp-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
if os.path.isdir(os.path.join(AQUI, "docs")):
    shutil.copytree(os.path.join(AQUI, "docs"), os.path.join(PASTA, "docs"))
sys.path.insert(0, PASTA)

import campanhas  # noqa: E402
import empresas  # noqa: E402
import eventos_i18n  # noqa: E402
import server  # noqa: E402

TRACOS = re.compile("[\u2013\u2014]")
ENVIADOS = []  # (para, assunto, texto, html, idioma)


ENVIAR_ORIGINAL = server.enviar_email


def falso_enviar(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt", cabecalhos=None):
    ENVIADOS.append({"para": para, "assunto": assunto, "texto": corpo, "html": html or "", "idioma": idioma,
                     "cabecalhos": cabecalhos})
    return True, "enviado"


class FalsoSMTP:
    """Substitui smtplib.SMTP e guarda a mensagem montada por server.enviar_email."""
    mensagens = []

    def __init__(self, host, porta, timeout=None):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def ehlo(self):
        pass

    def starttls(self):
        pass

    def login(self, usuario, senha):
        pass

    def sendmail(self, de, para, texto):
        FalsoSMTP.mensagens.append(texto)


class TestCampanhas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        server.enviar_email = falso_enviar
        campanhas.SINCRONO = True
        campanhas.PAUSA = 0
        conn = server.db()
        server.config_set(conn, "smtp_host", "smtp.teste.local")
        server.config_set(conn, "url_publica", "https://rh.exemplo.com")
        conn.commit()
        conn.close()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls._tokens = {}

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    # ------------------------------------------------------------ ajudantes
    def req(self, metodo, caminho, dados=None, cab=None, bruto=False):
        if isinstance(dados, bytes):
            corpo = dados
        else:
            corpo = json.dumps(dados).encode() if dados is not None else None
        h = {"Content-Type": "application/json"}
        h.update(cab or {})
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                conteudo = resp.read()
                return resp.status, (_html.unescape(conteudo.decode()) if bruto else json.loads(conteudo or b"{}"))
        except urllib.error.HTTPError as e:
            conteudo = e.read()
            return e.code, (_html.unescape(conteudo.decode()) if bruto else json.loads(conteudo or b"{}"))

    def token(self, login):
        if login not in self._tokens:
            s, d = self.req("POST", "/api/gestor/login", {"login": login, "senha": "senha-123"})
            self.assertEqual(s, 200, d)
            self._tokens[login] = {"X-Gestor-Token": d["token"]}
        return self._tokens[login]

    def empresa(self, nome):
        """Empresa com admin, cargos Tech e Driver, vaga aberta, vaga antiga e vaga de outro cargo."""
        conn = server.db()
        eid, slug = empresas.criar_empresa(conn, nome)
        login = "admin." + slug
        conn.execute("INSERT INTO gestores (login, senha, nome, is_admin, aprovado, empresa_id) VALUES (?,?,?,1,1,?)",
                     (login, server.hash_senha("senha-123"), "Admin " + nome, eid))
        tech = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Cleaning Tech', ?)", (eid,)).lastrowid
        driver = conn.execute("INSERT INTO cargos (nome, empresa_id) VALUES ('Driver', ?)", (eid,)).lastrowid
        vaga = conn.execute(
            "INSERT INTO vagas (cargo_id, titulo, local, descricao, status, empresa_id) VALUES (?,?,?,?, 'aberta', ?)",
            (tech, "Cleaning Technician", "Hartford, CT", "Residential cleaning team. Weekdays only.", eid)).lastrowid
        antiga = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Tech 2025', 'encerrada', ?)",
                              (tech, eid)).lastrowid
        outra = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Driver', 'encerrada', ?)",
                             (driver, eid)).lastrowid
        conn.commit()
        conn.close()
        return {"id": eid, "slug": slug, "login": login, "tech": tech, "vaga": vaga, "antiga": antiga, "outra": outra}

    def cand(self, emp, nome, email=None, idioma="en", local="Hartford", vaga=None, etapa="inscrito",
             quando=None, tier="", voz_status="", tags=None, tipo="externo", anonimizado=0, cargo_desejado=None):
        conn = server.db()
        cid = conn.execute(
            "INSERT INTO candidatos (token, nome, email, empresa_id, local, idioma, tipo, tags, anonimizado, cargo_desejado_id)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (secrets.token_hex(8), nome, nome.split()[0].lower() + "@x.com" if email is None else email, emp["id"], local,
             idioma, tipo, json.dumps(tags or [], ensure_ascii=False), anonimizado, cargo_desejado)).lastrowid
        if vaga:
            conn.execute("INSERT INTO candidaturas (candidato_id, vaga_id, etapa, voz_tier, voz_status, criado_em)"
                         " VALUES (?,?,?,?,?, COALESCE(?, datetime('now')))", (cid, vaga, etapa, tier, voz_status, quando))
        conn.commit()
        conn.close()
        return cid

    def previa(self, emp, filtros=None, vaga=None):
        s, d = self.req("POST", "/api/gestor/campanhas/vaga/%d/previa" % (vaga or emp["vaga"]),
                        {"filtros": filtros or {}}, self.token(emp["login"]))
        self.assertEqual(s, 200, d)
        return d

    def nomes(self, d):
        return sorted(c["nome"] for c in d["amostra"])

    # ------------------------------------------------------------ testes
    def test_filtros_e_exclusoes(self):
        e = self.empresa("Filtros Co")
        self.cand(e, "Ana Antiga", vaga=e["antiga"], tier="GOOD")
        self.cand(e, "Bia Outra", idioma="es", local="New Britain", vaga=e["outra"])
        self.cand(e, "Kim Velha", local="Waterbury", vaga=e["antiga"], quando="2023-01-10 10:00:00", tags=["forklift"])
        self.cand(e, "Rui Review", local="Hartford", vaga=e["antiga"], tier="REVIEW")
        # exclusões
        self.cand(e, "Caio Contratado", vaga=e["antiga"], etapa="contratado")
        self.cand(e, "Duda NaVaga", vaga=e["vaga"])
        self.cand(e, "Eva Anonima", vaga=e["antiga"], anonimizado=1)
        self.cand(e, "Fabio SemEmail", email="", vaga=e["antiga"])
        self.cand(e, "Hugo NaoLigar", vaga=e["antiga"], voz_status="nao_ligar")
        self.cand(e, "Iris Errado", vaga=e["antiga"], voz_status="numero_errado")
        self.cand(e, "Ivo Tag", vaga=e["antiga"], tags=["não contatar"])
        self.cand(e, "Jose Interno", tipo="interno")
        outra = self.empresa("Outra Co")
        self.cand(outra, "Lia OutraEmpresa", vaga=outra["antiga"])

        d = self.previa(e)
        self.assertEqual(self.nomes(d), ["Ana Antiga", "Bia Outra", "Kim Velha", "Rui Review"])
        self.assertEqual(d["total"], 4)
        self.assertEqual(d["por_idioma"], {"pt": 0, "en": 3, "es": 1})
        self.assertEqual(self.nomes(self.previa(e, {"cargo": "mesmo"})), ["Ana Antiga", "Kim Velha", "Rui Review"])
        self.assertEqual(self.nomes(self.previa(e, {"cidade": "hartford"})), ["Ana Antiga", "Rui Review"])
        self.assertEqual(self.nomes(self.previa(e, {"meses": 12})), ["Ana Antiga", "Bia Outra", "Rui Review"])
        self.assertEqual(self.nomes(self.previa(e, {"tier": "GOOD"})), ["Ana Antiga"])
        self.assertEqual(self.nomes(self.previa(e, {"tier": "REVIEW"})), ["Ana Antiga", "Rui Review"])
        self.assertEqual(self.nomes(self.previa(e, {"tags": ["forklift"]})), ["Kim Velha"])
        # cargo de interesse também conta como "mesmo cargo"
        self.cand(e, "Nina Interesse", cargo_desejado=e["tech"])
        self.assertIn("Nina Interesse", self.nomes(self.previa(e, {"cargo": "mesmo"})))
        # a outra empresa não vê a vaga nem os candidatos daqui
        s, _ = self.req("POST", "/api/gestor/campanhas/vaga/%d/previa" % e["vaga"], {"filtros": {}}, self.token(outra["login"]))
        self.assertEqual(s, 404)
        self.assertEqual(self.req("GET", "/api/gestor/campanhas/vaga/%d" % e["vaga"], cab=self.token(outra["login"]))[0], 404)
        self.assertEqual(self.nomes(self.previa(outra)), ["Lia OutraEmpresa"])
        # etiquetas oferecidas no filtro (sem as de bloqueio)
        s, info = self.req("GET", "/api/gestor/campanhas/vaga/%d" % e["vaga"], cab=self.token(e["login"]))
        self.assertEqual((s, info["tags"], info["limite"], info["smtp"]), (200, ["forklift"], 200, True))

    def test_envio_por_idioma_e_descadastro(self):
        e = self.empresa("Idiomas Co")
        conn = server.db()
        # campos de pagamento podem vir de outro módulo: cria se ainda não existirem
        cols = {r[1] for r in conn.execute("PRAGMA table_info(vagas)")}
        for coluna, tipo in (("salario_min", "REAL"), ("salario_max", "REAL"), ("salario_unidade", "TEXT DEFAULT ''")):
            if coluna not in cols:
                conn.execute("ALTER TABLE vagas ADD COLUMN %s %s" % (coluna, tipo))
        conn.execute("UPDATE vagas SET salario_min=18, salario_max=22, salario_unidade='hora' WHERE id=?", (e["vaga"],))
        conn.commit()
        conn.close()
        ids = {
            "en": self.cand(e, "Amy English", idioma="en", vaga=e["antiga"]),
            "es": self.cand(e, "Beto Espanol", idioma="es", vaga=e["antiga"]),
            "pt": self.cand(e, "Caca Portugues", idioma="pt", vaga=e["antiga"]),
            "sem": self.cand(e, "Dani SemIdioma", idioma="", vaga=e["antiga"]),
        }
        # prévia nos três idiomas
        d = self.previa(e)
        self.assertIn("New opening at Idiomas Co: Cleaning Technician", d["emails"]["en"]["assunto"])
        self.assertIn("Nueva vacante en Idiomas Co", d["emails"]["es"]["assunto"])
        self.assertIn("Nova vaga na Idiomas Co", d["emails"]["pt"]["assunto"])
        self.assertIn("$18 - $22 per hour", d["emails"]["en"]["html"])
        self.assertIn("$18 - $22 por hora", d["emails"]["es"]["html"])
        for lang in ("en", "es", "pt"):
            self.assertIsNone(TRACOS.search(d["emails"][lang]["html"]), lang)

        del ENVIADOS[:]
        s, r = self.req("POST", "/api/gestor/campanhas/vaga/%d/enviar" % e["vaga"], {"filtros": {}}, self.token(e["login"]))
        self.assertEqual((s, r["total"]), (200, 4), r)
        por_email = {m["para"]: m for m in ENVIADOS}
        self.assertEqual(len(por_email), 4)
        en = por_email["amy@x.com"]
        self.assertEqual(en["idioma"], "en")
        # cabeçalhos List-Unsubscribe (RFC 2369) e one-click (RFC 8058)
        token_en = re.search(r"/descadastrar\?t=([A-Za-z0-9_-]+)", en["texto"]).group(1)
        self.assertEqual(en["cabecalhos"], {
            "List-Unsubscribe": "<https://rh.exemplo.com/api/descadastrar?t=%s>, "
                                "<mailto:privacy@tonybelleza.com?subject=unsubscribe>" % token_en,
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"})
        for m in ENVIADOS:
            self.assertIn("List-Unsubscribe", m["cabecalhos"])
        self.assertIn("You applied to Idiomas Co before", en["texto"])
        self.assertIn("Hi Amy,", en["texto"])
        self.assertIn("Location: Hartford, CT", en["texto"])
        self.assertIn("Pay: $18 - $22 per hour", en["texto"])
        self.assertIn("https://rh.exemplo.com/candidato?vaga=%d&amp;e=%s&amp;lang=en" % (e["vaga"], e["slug"]), en["html"])
        self.assertIn("Unsubscribe", en["html"])
        es = por_email["beto@x.com"]
        self.assertEqual(es["idioma"], "es")
        self.assertIn("Te postulaste en Idiomas Co antes", es["texto"])
        self.assertIn("lang=es", es["texto"])
        pt = por_email["caca@x.com"]
        self.assertIn("Você se candidatou na Idiomas Co antes", pt["texto"])
        self.assertEqual(por_email["dani@x.com"]["idioma"], "pt")  # sem idioma: português
        for m in ENVIADOS:
            self.assertIsNone(TRACOS.search(m["texto"] + m["html"] + m["assunto"]))

        # registro do envio e evento na linha do tempo
        conn = server.db()
        envios = conn.execute("SELECT * FROM campanha_envios WHERE candidato_id=?", (ids["en"],)).fetchall()
        self.assertEqual([x["status"] for x in envios], ["enviado"])
        self.assertTrue(envios[0]["enviado_em"])
        ev = conn.execute("SELECT texto FROM eventos WHERE candidato_id=? ORDER BY id DESC", (ids["en"],)).fetchone()["texto"]
        conn.close()
        self.assertEqual(ev, "Avisado por e-mail sobre a vaga: Cleaning Technician (banco de talentos)")
        self.assertEqual(eventos_i18n.traduzir_evento(ev, "en"), "Notified about job Cleaning Technician (talent pool email)")
        self.assertIn("vacante Cleaning Technician", eventos_i18n.traduzir_evento(ev, "es"))
        s, ficha = self.req("GET", "/api/gestor/candidato/%d" % ids["en"], cab=dict(self.token(e["login"]), **{"X-Idioma": "en"}))
        self.assertEqual(s, 200)

        # não avisa de novo sobre a mesma vaga
        self.assertEqual(self.previa(e)["total"], 0)
        s, r = self.req("POST", "/api/gestor/campanhas/vaga/%d/enviar" % e["vaga"], {"filtros": {}}, self.token(e["login"]))
        self.assertEqual(s, 400)

        # histórico da vaga
        s, info = self.req("GET", "/api/gestor/campanhas/vaga/%d" % e["vaga"], cab=self.token(e["login"]))
        self.assertEqual(len(info["campanhas"]), 1)
        c = info["campanhas"][0]
        self.assertEqual((c["total"], c["enviados"], c["falhas"], c["pendentes"], c["candidaturas"]), (4, 4, 0, 0, 0))

        # abrir o link NÃO descadastra (leitores de links abrem sozinhos): só mostra o botão
        token = token_en
        s, pagina = self.req("GET", "/descadastrar?t=" + token, bruto=True)
        self.assertEqual(s, 200)
        self.assertIn("Stop job emails?", pagina)
        self.assertIn("Confirm unsubscribe", pagina)
        self.assertIn("Idiomas Co", pagina)
        self.assertIn('lang="en"', pagina)
        self.assertIn("/api/descadastrar", pagina)
        self.assertIsNone(TRACOS.search(pagina))
        s, pagina_es = self.req("GET", "/descadastrar?t=%s&lang=es" % token, bruto=True)
        self.assertIn("Confirmar cancelación", pagina_es)
        s, pagina_pt = self.req("GET", "/descadastrar?t=%s&lang=pt" % token, bruto=True)
        self.assertIn("Confirmar cancelamento", pagina_pt)
        self.assertIn("Idiomas Co", pagina_pt)
        conn = server.db()
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM campanhas_descadastros WHERE candidato_id=?",
                                      (ids["en"],)).fetchone()[0], 0)
        self.assertNotIn("não contatar", conn.execute("SELECT tags FROM candidatos WHERE id=?", (ids["en"],)).fetchone()["tags"])
        conn.close()
        s, invalida = self.req("GET", "/descadastrar?t=naoexiste", bruto=True)
        self.assertEqual(s, 404)
        self.assertIn("Invalid link", invalida)
        self.assertNotIn("Confirm unsubscribe", invalida)
        # o botão faz POST na API pública
        self.assertEqual(self.req("POST", "/api/descadastrar", {"t": "naoexiste"})[0], 404)
        self.assertEqual(self.req("POST", "/api/descadastrar", {})[0], 404)
        s, r = self.req("POST", "/api/descadastrar", {"t": token})
        self.assertEqual((s, r), (200, {"ok": True, "empresa": "Idiomas Co"}))
        s, r = self.req("POST", "/api/descadastrar", {"t": token})  # repetir não duplica
        self.assertEqual(s, 200)
        s, pagina = self.req("GET", "/descadastrar?t=" + token, bruto=True)
        self.assertEqual(s, 200)
        self.assertIn("You're unsubscribed", pagina)
        self.assertNotIn("Confirm unsubscribe", pagina)
        s, pagina_es = self.req("GET", "/descadastrar?t=%s&lang=es" % token, bruto=True)
        self.assertIn("Suscripción cancelada", pagina_es)
        conn = server.db()
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM campanhas_descadastros WHERE candidato_id=?",
                                      (ids["en"],)).fetchone()[0], 1)  # repetir o clique não duplica
        tags = json.loads(conn.execute("SELECT tags FROM candidatos WHERE id=?", (ids["en"],)).fetchone()["tags"])
        self.assertIn("não contatar", tags)
        ev = conn.execute("SELECT texto FROM eventos WHERE candidato_id=? ORDER BY id DESC", (ids["en"],)).fetchone()["texto"]
        self.assertEqual(eventos_i18n.traduzir_evento(ev, "en"), "Unsubscribed from the company's job emails")
        # nova vaga da mesma empresa: quem saiu não aparece mais
        nova = conn.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Supervisor', 'aberta', ?)",
                            (e["tech"], e["id"])).lastrowid
        conn.commit()
        conn.close()
        nomes = self.nomes(self.previa(e, vaga=nova))
        self.assertNotIn("Amy English", nomes)
        self.assertIn("Beto Espanol", nomes)
        # a ficha mostra o descadastro
        s, st = self.req("GET", "/api/gestor/campanhas/candidato/%d" % ids["en"], cab=self.token(e["login"]))
        self.assertEqual((s, st["descadastrado"], len(st["envios"])), (200, True, 1))
        s, st = self.req("GET", "/api/gestor/campanhas/candidato/%d" % ids["es"], cab=self.token(e["login"]))
        self.assertFalse(st["descadastrado"])
        outra = self.empresa("Curiosa Co")
        self.assertEqual(self.req("GET", "/api/gestor/campanhas/candidato/%d" % ids["en"], cab=self.token(outra["login"]))[0], 404)
        # one-click da RFC 8058: POST ?t=TOKEN com corpo form-encoded
        tok_es = re.search(r"/descadastrar\?t=([A-Za-z0-9_-]+)", por_email["beto@x.com"]["texto"]).group(1)
        form = {"Content-Type": "application/x-www-form-urlencoded"}
        s, r = self.req("POST", "/api/descadastrar?t=naoexiste", b"List-Unsubscribe=One-Click", form)
        self.assertEqual(s, 404)
        s, r = self.req("POST", "/api/descadastrar?t=" + tok_es, b"List-Unsubscribe=One-Click", form)
        self.assertEqual((s, r["ok"]), (200, True))
        s, st = self.req("GET", "/api/gestor/campanhas/candidato/%d" % ids["es"], cab=self.token(e["login"]))
        self.assertTrue(st["descadastrado"])
        # formulário da página sem JavaScript: devolve a página de confirmação
        tok_pt = re.search(r"/descadastrar\?t=([A-Za-z0-9_-]+)", por_email["caca@x.com"]["texto"]).group(1)
        s, pag = self.req("POST", "/api/descadastrar?t=%s&lang=pt" % tok_pt, b"List-Unsubscribe=One-Click",
                          dict(form, Accept="text/html"), bruto=True)
        self.assertEqual(s, 200)
        self.assertIn("Inscrição cancelada", pag)
        s, st = self.req("GET", "/api/gestor/campanhas/candidato/%d" % ids["pt"], cab=self.token(e["login"]))
        self.assertTrue(st["descadastrado"])
        # e-mails transacionais continuam: o descadastro não bloqueia o envio direto
        del ENVIADOS[:]
        conn = server.db()
        ok, _ = server.enviar_email(conn, "amy@x.com", "Interview confirmed", "See you Monday.")
        conn.close()
        self.assertTrue(ok)
        self.assertEqual(len(ENVIADOS), 1)

    def test_enviar_email_aplica_cabecalhos(self):
        import smtplib
        original = smtplib.SMTP
        smtplib.SMTP = FalsoSMTP
        del FalsoSMTP.mensagens[:]
        conn = server.db()
        try:
            cab = {"List-Unsubscribe": "<https://rh.exemplo.com/api/descadastrar?t=abc>, "
                                       "<mailto:privacy@tonybelleza.com?subject=unsubscribe>",
                   "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}
            ok, msg = ENVIAR_ORIGINAL(conn, "amy@x.com", "Nova vaga", "Corpo", cabecalhos=cab)
            self.assertEqual((ok, msg), (True, "enviado"))
            ok, _ = ENVIAR_ORIGINAL(conn, "amy@x.com", "Sem extras", "Corpo",
                                    anexos=[("a.txt", b"oi", "text/plain")])
            self.assertTrue(ok)
        finally:
            smtplib.SMTP = original
            conn.close()
        import email
        com, sem = [email.message_from_string(m) for m in FalsoSMTP.mensagens]
        self.assertEqual(com["List-Unsubscribe"], cab["List-Unsubscribe"])
        self.assertEqual(com["List-Unsubscribe-Post"], "List-Unsubscribe=One-Click")
        self.assertEqual((com["Subject"], com["To"]), ("Nova vaga", "amy@x.com"))
        self.assertTrue(com.is_multipart())
        self.assertIsNone(sem["List-Unsubscribe"])  # chamadas antigas não mudam
        self.assertEqual(sem.get_content_subtype(), "mixed")

    def test_limite_de_200(self):
        e = self.empresa("Grande Co")
        conn = server.db()
        for i in range(230):
            cid = conn.execute("INSERT INTO candidatos (token, nome, email, empresa_id, idioma) VALUES (?,?,?,?, 'en')",
                               (secrets.token_hex(8), "Pessoa %03d" % i, "p%03d@grande.com" % i, e["id"])).lastrowid
            conn.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cid, e["antiga"]))
        conn.commit()
        conn.close()
        d = self.previa(e)
        self.assertEqual((d["total"], d["enviar"], d["limite"]), (230, 200, 200))
        del ENVIADOS[:]
        s, r = self.req("POST", "/api/gestor/campanhas/vaga/%d/enviar" % e["vaga"], {"filtros": {}}, self.token(e["login"]))
        self.assertEqual((s, r["total"]), (200, 200))
        self.assertEqual(len(ENVIADOS), 200)
        # os 30 restantes ficam para um próximo aviso
        self.assertEqual(self.previa(e)["total"], 30)

    def test_atribuicao_de_candidaturas(self):
        e = self.empresa("Atribui Co")
        a = self.cand(e, "Olga Volta", vaga=e["antiga"])
        self.cand(e, "Paulo Fica", vaga=e["antiga"])
        s, r = self.req("POST", "/api/gestor/campanhas/vaga/%d/enviar" % e["vaga"], {"filtros": {}}, self.token(e["login"]))
        self.assertEqual(s, 200)
        conn = server.db()
        conn.execute("UPDATE campanha_envios SET enviado_em=datetime('now','-1 minute') WHERE campanha_id=?", (r["campanha_id"],))
        conn.commit()
        conn.close()
        # Olga clica em "Apply" e se inscreve de novo com o mesmo e-mail
        s, d = self.req("POST", "/api/candidato/cadastro", {
            "nome": "Olga Volta", "email": "olga@x.com", "telefone": "+1 860 555 0199", "local": "Hartford",
            "vaga_id": e["vaga"], "empresa": e["slug"], "consentimento": True})
        self.assertIn(s, (200, 409), d)
        conn = server.db()
        self.assertTrue(conn.execute("SELECT 1 FROM candidaturas WHERE candidato_id=? AND vaga_id=?", (a, e["vaga"])).fetchone())
        conn.close()
        s, info = self.req("GET", "/api/gestor/campanhas/vaga/%d" % e["vaga"], cab=self.token(e["login"]))
        self.assertEqual(info["campanhas"][0]["candidaturas"], 1)
        self.assertEqual(info["campanhas"][0]["enviados"], 2)

    def test_regras_de_envio(self):
        e = self.empresa("Regras Co")
        self.cand(e, "Quim Pool", vaga=e["antiga"])
        cab = self.token(e["login"])
        # vaga fechada não envia
        self.assertEqual(self.req("POST", "/api/gestor/campanhas/vaga/%d/enviar" % e["antiga"], {"filtros": {}}, cab)[0], 400)
        # sem SMTP não envia (mensagem traduzida)
        conn = server.db()
        server.config_set(conn, "smtp_host", "")
        conn.commit()
        s, d = self.req("POST", "/api/gestor/campanhas/vaga/%d/enviar" % e["vaga"], {"filtros": {}}, dict(cab, **{"X-Idioma": "en"}))
        server.config_set(conn, "smtp_host", "smtp.teste.local")
        conn.commit()
        conn.close()
        self.assertEqual((s, d["erro"]), (400, "Set up email sending (SMTP) before notifying the talent pool"))
        # filtros inválidos viram padrão
        f = campanhas.normalizar_filtros({"cargo": "x", "meses": "abc", "tier": "LOW", "tags": "nao-lista"})
        self.assertEqual(f, {"cargo": "qualquer", "cidade": "", "meses": 0, "tier": "", "tags": []})
        # falha de envio fica registrada
        def falha(*a, **k):
            return False, "SMTP fora do ar"
        server.enviar_email = falha
        try:
            s, r = self.req("POST", "/api/gestor/campanhas/vaga/%d/enviar" % e["vaga"], {"filtros": {}}, cab)
        finally:
            server.enviar_email = falso_enviar
        self.assertEqual(s, 200)
        s, info = self.req("GET", "/api/gestor/campanhas/vaga/%d" % e["vaga"], cab=cab)
        self.assertEqual((info["campanhas"][0]["falhas"], info["campanhas"][0]["enviados"]), (1, 0))

    def test_arquivos(self):
        for arq in ("campanhas.py", "teste_campanhas.py", "public/js/gestor-campanhas.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)
        with open(os.path.join(AQUI, "public", "gestor.html"), encoding="utf-8") as f:
            self.assertIn("js/gestor-campanhas.js", f.read())
        with open(os.path.join(AQUI, "public", "js", "gestor-campanhas.js"), encoding="utf-8") as f:
            js = f.read()
        for chave in ("camp_botao", "camp_titulo", "camp_enviar", "camp_descadastrado"):
            self.assertEqual(js.count(chave + ":"), 3, chave)  # pt, en e es
        with open(os.path.join(AQUI, "public", "js", "gestor.js"), encoding="utf-8") as f:
            g = f.read()
        self.assertIn("campanhasBotaoVaga", g)
        self.assertIn("campanhasPreencherFicha", g)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
