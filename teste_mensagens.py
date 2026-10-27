"""
Testes das mensagens em 3 idiomas (mensagens.py): e-mail único de resultados ao
candidato, aviso único aos gestores, modelos por idioma, logo da empresa e PDF.

Uso:  python3 teste_mensagens.py

Roda com banco isolado numa pasta temporária. Nenhum e-mail sai da máquina:
o envio SMTP é substituído por um gravador.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="msg-teste-")
for arquivo in ("server.py", "voz.py", "empresas.py", "mensagens.py"):
    shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import mensagens  # noqa: E402
import server  # noqa: E402

DISC = {"pct": {"D": 20, "I": 25, "S": 40, "C": 15}, "dominante": "S"}
BASE = {"pct": {"B": 35, "A": 15, "S": 30, "E": 20}, "ordem": ["B", "S", "E", "A"], "codigo": "BSEA"}
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)
TRACOS = re.compile("[–—]")


class Base(unittest.TestCase):
    def setUp(self):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        self.conn = server.db()
        c = self.conn
        self.empresa, _ = empresas.criar_empresa(c, "Belleza's Home Services CT")
        self.cargo = c.execute("INSERT INTO cargos (nome, area, nivel, disc_alvo, base_alvo, empresa_id) VALUES ('Cleaning Technician','Ops','','S','B',?)",
                               (self.empresa,)).lastrowid
        self.vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, local, status, empresa_id)"
                              " VALUES (?, 'House Cleaning Technician', '', 'aberta', ?)", (self.cargo, self.empresa)).lastrowid
        for login, idioma in (("tony", "pt"), ("carine", "en"), ("ana", "es")):
            c.execute("INSERT INTO gestores (nome, login, senha, email, is_admin, aprovado, empresa_id, idioma)"
                      " VALUES (?,?,?,?,1,1,?,?)", (login, login, "x", login + "@example.com", self.empresa, idioma))
        server.config_set(c, "smtp_host", "smtp.teste")
        server.config_set(c, "url_publica", "https://rh.exemplo.com")
        c.commit()
        self.enviados = []
        self._original = server.enviar_email

        def gravar(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt"):
            if html is None:
                html = mensagens.html_email(assunto, corpo, idioma, marca) if marca else server.montar_email_html(assunto, corpo)
            self.enviados.append({"para": para, "assunto": assunto, "corpo": corpo, "html": html,
                                  "anexos": anexos or [], "idioma": idioma})
            return True, "enviado"

        server.enviar_email = gravar

    def tearDown(self):
        server.enviar_email = self._original
        self.conn.close()

    def candidato(self, idioma="es", testes=True, email="maria@example.com"):
        c = self.conn
        cid = c.execute("INSERT INTO candidatos (token, nome, email, local, telefone, cargo_desejado_id, idioma, empresa_id)"
                        " VALUES (?,?,?,?,?,?,?,?)",
                        ("tok" + idioma + email, "Maria Lopez", email, "", "+18605550101", self.cargo, idioma, self.empresa)).lastrowid
        c.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cid, self.vaga))
        if testes:
            c.execute("INSERT INTO resultados_teste (candidato_id, tipo, payload) VALUES (?,?,?)", (cid, "disc", json.dumps(DISC)))
            c.execute("INSERT INTO resultados_teste (candidato_id, tipo, payload) VALUES (?,?,?)", (cid, "base", json.dumps(BASE)))
        c.commit()
        return c.execute("SELECT * FROM candidatos WHERE id=?", (cid,)).fetchone()

    def para(self, email):
        return [e for e in self.enviados if e["para"] == email]


class TestTextos(Base):
    def test_todas_as_chaves_existem_nos_3_idiomas(self):
        for lang in ("en", "es"):
            self.assertEqual(set(mensagens.T["pt"]), set(mensagens.T[lang]), lang)

    def test_sem_travessoes(self):
        textos = json.dumps([mensagens.T, mensagens.TEMPLATES_I18N], ensure_ascii=False)
        self.assertIsNone(TRACOS.search(textos))

    def test_modelos_de_e_mail_existem_em_en_e_es(self):
        modelos = server.templates_email(self.conn, self.empresa)
        for chave in ("confirmacao", "lembrete", "etapa_inscrito", "etapa_avaliacoes", "etapa_entrevista",
                      "etapa_proposta", "etapa_contratado", "etapa_reprovado"):
            for lang in ("en", "es"):
                self.assertIn(chave + "_" + lang, modelos)

    def test_perfis_traduzidos(self):
        self.assertEqual(mensagens.perfis("en")["DISC"]["D"]["nome"], "Dominance")
        self.assertEqual(mensagens.perfis("es")["DISC"]["S"]["nome"], "Estabilidad")
        self.assertEqual(mensagens.perfis("pt")["BASE"]["B"]["nome"], "Bússola")
        for lang in ("pt", "en", "es"):
            for letra in "BASE":
                self.assertTrue(mensagens.perfis(lang)["BASE"][letra]["nome"])

    def test_idioma_invalido_cai_no_portugues(self):
        self.assertEqual(mensagens.idioma("fr"), "pt")
        self.assertEqual(mensagens.idioma("ES"), "es")
        self.assertEqual(mensagens.idioma("en-US"), "en")


class TestResultadoCandidato(Base):
    def test_um_unico_e_mail_no_idioma_do_candidato(self):
        esperado = {"pt": "Seus resultados", "en": "Your results", "es": "Tus resultados"}
        for lang, inicio in esperado.items():
            self.enviados.clear()
            cand = self.candidato(lang, email=lang + "@example.com")
            server.notificar_avaliacao_completa(self.conn, cand)
            server.notificar_avaliacao_completa(self.conn, cand)  # segundo envio do último teste
            meus = self.para(lang + "@example.com")
            self.assertEqual(len(meus), 1, lang)
            self.assertTrue(meus[0]["assunto"].startswith(inicio), meus[0]["assunto"])
            self.assertEqual(len(meus[0]["anexos"]), 1)
            self.assertTrue(meus[0]["anexos"][0][1].startswith(b"%PDF"))

    def test_candidato_ve_disc_e_base_sem_match(self):
        cand = self.candidato("en")
        assunto, texto, html, _ = mensagens.email_resultado_candidato(self.conn, cand)
        self.assertIn("Steadiness", html)
        self.assertIn("BSEA", html)
        self.assertNotIn("Match", html)
        self.assertNotIn("Match", texto)
        self.assertIn("lang=en", html)

    def test_espanhol_completo(self):
        cand = self.candidato("es")
        assunto, texto, html, anexos = mensagens.email_resultado_candidato(self.conn, cand)
        for trecho in ("¡Hola, Maria!", "Estilo principal: Estabilidad", "Código BSEA", "lang=es"):
            self.assertIn(trecho, texto + html)
        self.assertEqual(anexos[0][0], "resultados.pdf")
        self.assertIn('lang="es"', html)

    def test_sem_logo_usa_o_nome_da_empresa(self):
        cand = self.candidato("pt")
        _, _, html, _ = mensagens.email_resultado_candidato(self.conn, cand)
        self.assertIn("Belleza&#x27;s Home Services CT", html)
        self.assertNotIn("/logo?v=", html)

    def test_com_logo(self):
        self.assertIsNone(mensagens.salvar_logo(self.conn, self.empresa, "logo.png", PNG_1PX))
        cand = self.candidato("pt")
        _, _, html, anexos = mensagens.email_resultado_candidato(self.conn, cand)
        self.assertRegex(html, r'https://rh\.exemplo\.com/api/empresa/[a-z0-9-]+/logo\?v=\d+')
        self.assertTrue(anexos[0][1].startswith(b"%PDF"))


class TestGestores(Base):
    def test_aviso_unico_no_idioma_de_cada_gestor(self):
        cand = self.candidato("es")
        server.notificar_avaliacao_completa(self.conn, cand)
        self.assertTrue(self.para("tony@example.com")[0]["assunto"].startswith("Candidato pronto"))
        self.assertTrue(self.para("carine@example.com")[0]["assunto"].startswith("Candidate ready"))
        self.assertTrue(self.para("ana@example.com")[0]["assunto"].startswith("Candidato listo"))
        for g in ("tony", "carine", "ana"):
            self.assertEqual(len(self.para(g + "@example.com")), 1)
        html = self.para("carine@example.com")[0]["html"]
        self.assertIn("Match with Cleaning Technician", html)
        self.assertIn("#candidato=%d" % cand["id"], html)
        self.assertIn("Spanish", html)
        self.assertIn("DISC profile", html)
        self.assertNotIn("Your DISC", html)

    def test_testes_pendentes_apos_48_horas(self):
        cand = self.candidato("es", testes=False)
        self.conn.execute("UPDATE candidaturas SET voz_convite_enviado=1, voz_tier='STRONG', voz_score=88,"
                          " voz_ultima=datetime('now','-50 hours') WHERE candidato_id=?", (cand["id"],))
        self.conn.commit()
        server.avisar_testes_pendentes(self.conn)
        server.avisar_testes_pendentes(self.conn)
        avisos = self.para("carine@example.com")
        self.assertEqual(len(avisos), 1)
        self.assertIn("tests pending", avisos[0]["assunto"])
        self.assertIn("DISC and B.A.S.E. not answered yet", avisos[0]["html"])

    def test_nao_avisa_antes_de_48_horas_nem_sem_data(self):
        cand = self.candidato("es", testes=False)
        self.conn.execute("UPDATE candidaturas SET voz_convite_enviado=1, voz_tier='GOOD', voz_ultima=''"
                          " WHERE candidato_id=?", (cand["id"],))
        self.conn.commit()
        server.avisar_testes_pendentes(self.conn)
        self.conn.execute("UPDATE candidaturas SET voz_ultima=datetime('now','-2 hours') WHERE candidato_id=?", (cand["id"],))
        self.conn.commit()
        server.avisar_testes_pendentes(self.conn)
        self.assertEqual(self.enviados, [])


class TestModelos(Base):
    def test_confirmacao_no_idioma_e_com_marca(self):
        for lang, inicio in (("pt", "Inscrição confirmada"), ("en", "Application received"), ("es", "Solicitud recibida")):
            self.enviados.clear()
            cand = self.candidato(lang, testes=False, email="c" + lang + "@example.com")
            server.enviar_ao_candidato(self.conn, cand, "confirmacao", server.variaveis_candidato(self.conn, cand))
            e = self.enviados[0]
            self.assertTrue(e["assunto"].startswith(inicio), e["assunto"])
            self.assertEqual(e["idioma"], lang)
            self.assertIn("Belleza", e["html"])
            if lang != "pt":
                self.assertIn("lang=" + lang, e["corpo"])

    def test_modelo_personalizado_pela_empresa_vale_no_idioma(self):
        server.config_set(self.conn, "templates_email:%d" % self.empresa,
                          json.dumps({"confirmacao_es": {"assunto": "Hola {nome}", "corpo": "Gracias"}}))
        self.conn.commit()
        cand = self.candidato("es", testes=False)
        server.enviar_ao_candidato(self.conn, cand, "confirmacao", server.variaveis_candidato(self.conn, cand))
        self.assertEqual(self.enviados[0]["assunto"], "Hola Maria Lopez")

    def test_etapa_desconhecida_usa_o_padrao(self):
        modelo = server.modelo_email(self.conn, self.empresa, "etapa_xyz", "en")
        self.assertIn("assunto", modelo)


class TestLogo(Base):
    def test_valida_tipo_tamanho_e_conteudo(self):
        self.assertIn("PNG ou JPG", mensagens.salvar_logo(self.conn, self.empresa, "logo.svg", b"<svg/>"))
        self.assertIn("inválido", mensagens.salvar_logo(self.conn, self.empresa, "logo.png", b"nao e png"))
        self.assertIn("1 MB", mensagens.salvar_logo(self.conn, self.empresa, "logo.png", b"\x89PNG" + b"0" * (1024 * 1024)))
        self.assertIsNone(mensagens.salvar_logo(self.conn, self.empresa, "logo.png", PNG_1PX))
        mensagens.remover_logo(self.conn, self.empresa)
        self.assertEqual(mensagens.marca(self.conn, self.empresa)["logo_url"], "")


class TestPDF(Base):
    def test_pdf_nos_3_idiomas(self):
        cand = self.candidato("pt")
        for lang in ("pt", "en", "es"):
            pdf, erro = server.gerar_pdf_resultado(self.conn, cand, lang, para_candidato=True)
            self.assertIsNone(erro, lang)
            self.assertTrue(pdf.startswith(b"%PDF"))
        pdf_gestor, erro = server.gerar_pdf_resultado(self.conn, cand, "en")
        self.assertIsNone(erro)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
