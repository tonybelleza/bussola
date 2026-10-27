"""
Testes da entrada de candidatos (entrada.py): leitura dos e-mails do Indeed,
importação de CSV, duplicados, fila automática e o quadro "Ligar hoje".

Uso:  python3 teste_entrada.py

Banco isolado numa pasta temporária. A caixa de e-mail é falsa: nada sai da máquina.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from email.message import EmailMessage

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="entrada-teste-")
for arquivo in ("server.py", "voz.py", "empresas.py", "mensagens.py", "erros_i18n.py", "entrada.py"):
    shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import entrada  # noqa: E402
import server  # noqa: E402


def email_indeed(assunto, corpo="", reply_to="", remetente="indeedapply@indeed.com", curriculo=None):
    m = EmailMessage()
    m["From"] = "Indeed <%s>" % remetente
    m["To"] = "ct@example.com"
    m["Subject"] = assunto
    if reply_to:
        m["Reply-To"] = reply_to
    m.set_content(corpo or "Hello")
    if curriculo:
        m.add_attachment(curriculo, maintype="application", subtype="pdf", filename="Resume.pdf")
    return m.as_bytes()


class ImapFalso:
    def __init__(self, mensagens):
        self.mensagens = mensagens  # {uid: bytes}
        self.lidas = []

    def select(self, pasta, readonly=False):
        assert readonly, "a caixa deve ser aberta só para leitura"
        return "OK", [b"1"]

    def response(self, nome):
        return nome, [b"777"]

    def uid(self, comando, *args):
        if comando == "search":
            return "OK", [" ".join(str(u) for u in self.mensagens).encode()]
        if comando == "fetch":
            uid = int(args[0])
            assert "PEEK" in args[1], "não pode marcar como lido"
            self.lidas.append(uid)
            return "OK", [(b"%d (BODY[] {1}" % uid, self.mensagens[uid]), b")"]
        raise AssertionError(comando)

    def logout(self):
        pass


class Base(unittest.TestCase):
    def setUp(self):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        self.conn = server.db()
        c = self.conn
        self.empresa, _ = empresas.criar_empresa(c, "BHS CT")
        c.execute("UPDATE empresas SET modulos='[\"voz\"]' WHERE id=?", (self.empresa,))
        self.cargo = c.execute("INSERT INTO cargos (nome, voz_ativa, empresa_id) VALUES ('Cleaning Tech', 1, ?)",
                               (self.empresa,)).lastrowid
        self.vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'House Cleaning Technician', 'pausada', ?)",
                              (self.cargo, self.empresa)).lastrowid
        self.gestor = c.execute("INSERT INTO gestores (nome, login, senha, is_admin, aprovado, empresa_id) VALUES ('Admin','adm','x',1,1,?)",
                                (self.empresa,)).lastrowid
        c.commit()

    def tearDown(self):
        self.conn.close()

    def g(self):
        return self.conn.execute("SELECT g.*, e.modulos AS empresa_modulos FROM gestores g JOIN empresas e ON e.id=g.empresa_id WHERE g.id=?",
                                 (self.gestor,)).fetchone()


class TestLeituraDoEmail(Base):
    REM = ["indeed.com", "indeedemail.com"]

    def test_candidatura_individual(self):
        bruto = email_indeed("Maria Lopez applied to House Cleaning Technician",
                             "Maria Lopez\nNew Britain, CT 06051\nPhone: (860) 555-0101",
                             reply_to="Maria Lopez <marialopez7abc_q1@indeedemail.com>", curriculo=b"%PDF-1.4 teste")
        d = entrada.ler_mensagem(bruto, self.REM)
        self.assertEqual(d["nome"], "Maria Lopez")
        self.assertEqual(d["email"], "marialopez7abc_q1@indeedemail.com")
        self.assertEqual(d["telefone"], "8605550101")
        self.assertEqual(d["local"], "New Britain, CT 06051")
        self.assertEqual(d["vaga_titulo"], "House Cleaning Technician")
        self.assertEqual(d["curriculo"][0], "Resume.pdf")

    def test_outro_formato_de_assunto(self):
        d = entrada.ler_mensagem(email_indeed("New application: House Cleaning Technician from Jose Perez",
                                              reply_to="jose_x@indeedemail.com"), self.REM)
        self.assertEqual((d["nome"], d["vaga_titulo"]), ("Jose Perez", "House Cleaning Technician"))

    def test_ignora_resumo_diario_alertas_e_outros_remetentes(self):
        self.assertIsNone(entrada.ler_mensagem(email_indeed("Candidate update: House Cleaning Technician",
                                                            "1 new candidate applied today", remetente="employers-noreply@indeed.com"), self.REM))
        self.assertIsNone(entrada.ler_mensagem(email_indeed("Flooring Sales Associate and 19 more new jobs",
                                                            remetente="alert@indeed.com"), self.REM))
        self.assertIsNone(entrada.ler_mensagem(email_indeed("Maria applied to X", reply_to="m@x.com",
                                                            remetente="spam@outro.com"), self.REM))

    def test_sem_contato_e_ignorado(self):
        self.assertIsNone(entrada.ler_mensagem(email_indeed("Ana applied to House Cleaning Technician"), self.REM))


class TestLerCaixa(Base):
    def configurar(self, **extra):
        cfg = entrada.config(self.conn, self.empresa)
        cfg.update(usuario="ct@example.com", senha="app-pass", vaga_id=self.vaga, ativo=True, **extra)
        entrada.salvar(self.conn, self.empresa, cfg)

    def test_cria_candidatos_sem_duplicar_e_sem_reler(self):
        self.configurar()
        caixa = ImapFalso({
            10: email_indeed("Maria Lopez applied to House Cleaning Technician", reply_to="maria_q@indeedemail.com"),
            11: email_indeed("Candidate update: House Cleaning Technician", "1 new candidate", remetente="employers-noreply@indeed.com"),
            12: email_indeed("Maria Lopez applied to House Cleaning Technician", reply_to="maria_q@indeedemail.com"),
        })
        entrada.conectar = lambda cfg: caixa
        r = entrada.ler_caixa(self.conn, self.empresa)
        self.assertEqual((r["criados"], r["duplicados"], r["ignoradas"], r["erro"]), (1, 1, 1, ""))
        cand = self.conn.execute("SELECT * FROM candidatos WHERE empresa_id=?", (self.empresa,)).fetchall()
        self.assertEqual(len(cand), 1)
        self.assertIn("indeed", json.loads(cand[0]["tags"]))
        ca = self.conn.execute("SELECT * FROM candidaturas WHERE candidato_id=?", (cand[0]["id"],)).fetchone()
        self.assertEqual((ca["vaga_id"], ca["voz_status"]), (self.vaga, ""))
        self.assertEqual(entrada.config(self.conn, self.empresa)["ultimo_uid"], 12)
        # segunda rodada: nada novo
        caixa.lidas.clear()
        r = entrada.ler_caixa(self.conn, self.empresa)
        self.assertEqual(caixa.lidas, [])

    def test_fila_automatica_quando_ligada(self):
        self.configurar(auto_fila=True)
        entrada.conectar = lambda cfg: ImapFalso({5: email_indeed("Ana Silva applied to House Cleaning Technician",
                                                                   "Phone 860-555-0177", reply_to="ana_q@indeedemail.com")})
        entrada.ler_caixa(self.conn, self.empresa)
        st = self.conn.execute("SELECT voz_status FROM candidaturas").fetchone()[0]
        self.assertEqual(st, "para_ligar")

    def test_senha_nunca_vai_para_o_painel(self):
        self.configurar()
        publica = entrada.config_publica(entrada.config(self.conn, self.empresa))
        self.assertNotIn("senha", publica)
        self.assertTrue(publica["senha_configurada"])


class TestCSV(Base):
    CSV = ("name,email,phone,status,candidate location,relevant experience,education,date,source,job title\n"
           "Erika Valentin,erika@example.com,9192161797,In progress,\"New Britain, CT\",2 years,GED,2026-09-13,Facebook,House Cleaning Technician\n"
           "Sem Contato,,,,,,,,,\n"
           ",x@example.com,,,,,,,,\n"
           "Erika V,ERIKA@example.com,,,,,,,,\n"
           "Jorge Perez,,860-201-7898,,Hartford CT,,,08/07/2025,Indeed,\n")

    def test_previa_nao_grava(self):
        r = entrada.importar_csv(self.conn, self.empresa, self.CSV, self.vaga)
        self.assertEqual((r["criados"], r["duplicados"], r["invalidos"]), (2, 1, 2))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM candidatos").fetchone()[0], 0)

    def test_importa_e_nao_duplica(self):
        r = entrada.importar_csv(self.conn, self.empresa, self.CSV, self.vaga, aplicar=True)
        self.assertEqual(r["criados"], 2)
        jorge = self.conn.execute("SELECT * FROM candidatos WHERE nome='Jorge Perez'").fetchone()
        self.assertEqual(jorge["telefone"], "+18602017898")
        self.assertTrue(jorge["criado_em"].startswith("2025-08-07"))
        self.assertIn("indeed", json.loads(jorge["tags"]))
        r = entrada.importar_csv(self.conn, self.empresa, self.CSV, self.vaga, aplicar=True)
        self.assertEqual(r["criados"], 0)

    def test_ponto_e_virgula_e_cabecalho_em_portugues(self):
        texto = "﻿Nome;E-mail;Telefone\nAna;ana@example.com;8605550000\n"
        r = entrada.importar_csv(self.conn, self.empresa, texto, None, aplicar=True)
        self.assertEqual(r["criados"], 1)


class TestPrioridades(Base):
    def test_grupos_do_dia(self):
        c = self.conn

        def novo(nome, **campos):
            cid = c.execute("INSERT INTO candidatos (token, nome, email, telefone, empresa_id, notificado_completo) VALUES (?,?,?,?,?,?)",
                            (nome, nome, nome + "@x.com", "+18605550100", self.empresa, campos.pop("completo", 0))).lastrowid
            sets = ", ".join("%s=?" % k for k in campos)
            caid = c.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cid, self.vaga)).lastrowid
            if campos:
                c.execute("UPDATE candidaturas SET %s WHERE id=?" % sets, list(campos.values()) + [caid])
            return cid
        novo("Ligar", voz_status="para_ligar", voz_tentativas=0)
        novo("Callback", voz_status="callback")
        novo("Esgotado", voz_status="para_ligar", voz_tentativas=3)
        novo("Testes", voz_status="concluida", voz_tier="STRONG", voz_convite_enviado=1)
        novo("Pronto", voz_status="concluida", completo=1, etapa="avaliacoes")
        novo("Reprovado", voz_status="para_ligar", etapa="reprovado")
        c.commit()
        p = entrada.prioridades(c, self.g())
        nomes = {k: [i["nome"] for i in v["itens"]] for k, v in p.items()}
        self.assertEqual(sorted(nomes["ligar_hoje"]), ["Callback", "Ligar"])
        self.assertEqual(nomes["sem_resposta"], ["Esgotado"])
        self.assertEqual(nomes["aguardando_testes"], ["Testes"])
        self.assertEqual(nomes["prontos"], ["Pronto"])


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
