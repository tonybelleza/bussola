"""
Testes da agenda de entrevistas (agenda.py): horários livres (dias, janela,
duração, intervalo, antecedência, horizonte, datas bloqueadas, fuso e horário de
verão), marcação sem conflito, remarcação, cancelamento, convite .ics, idiomas
dos e-mails, link no e-mail de resultados, isolamento entre empresas e lembrete.

Uso:  python3 teste_agenda.py

Banco isolado numa pasta temporária. Nenhum e-mail sai da máquina: o envio SMTP
é substituído por um gravador.
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
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="agenda-teste-")
for arquivo in ("server.py", "voz.py", "empresas.py", "mensagens.py", "erros_i18n.py", "eventos_i18n.py", "entrada.py", "agenda.py", "talentos.py", "seguranca.py", "planos.py", "indicacoes.py") + tuple(
        f for f in ("onboarding.py", "formularios.py", "vagas_publicas.py", "relatorios.py", "campanhas.py", "assistente.py", "telefonia.py") if os.path.exists(os.path.join(AQUI, f))):
    shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)

import agenda  # noqa: E402
import empresas  # noqa: E402
import mensagens  # noqa: E402
import server  # noqa: E402

agenda.ENVIO_EM_SEGUNDO_PLANO = False
server.Handler.log_message = lambda *a: None  # sem log de cada requisição na saída dos testes
NY = ZoneInfo("America/New_York")
TRACOS = re.compile("[\u2013\u2014]")
DISC = {"pct": {"D": 20, "I": 25, "S": 40, "C": 15}, "dominante": "S"}
BASE = {"pct": {"B": 35, "A": 15, "S": 30, "E": 20}, "ordem": ["B", "S", "E", "A"], "codigo": "BSEA"}


def cfg(**extra):
    c = dict(agenda.PADRAO, ativo=True, dias=[1, 2, 3, 4, 5], inicio="09:00", fim="11:00", duracao=30,
             intervalo=0, antecedencia_horas=0, horizonte_dias=7, fuso="America/New_York", bloqueios=[])
    c.update(extra)
    return c


def utc(ano, mes, dia, h, m=0):
    return datetime(ano, mes, dia, h, m, tzinfo=timezone.utc)


def local_ny(ano, mes, dia, h, m=0):
    return datetime(ano, mes, dia, h, m, tzinfo=NY)


class TestHorarios(unittest.TestCase):
    # segunda-feira, 2 de novembro de 2026, 06:00 em Nova York (já no horário padrão, EST)
    AGORA = local_ny(2026, 11, 2, 6)

    def test_dias_janela_e_duracao(self):
        h = agenda.gerar_horarios(cfg(), agora=self.AGORA)
        # seg a seg seguinte (8 dias, 6 dias úteis) x 4 horários (09:00, 09:30, 10:00, 10:30)
        self.assertEqual(len(h), 24)
        self.assertEqual(h[0][0], utc(2026, 11, 2, 14))           # 09:00 EST = 14:00Z
        self.assertEqual([x[3] for x in h[:4]], ["09:00", "09:30", "10:00", "10:30"])
        self.assertEqual(h[0][1] - h[0][0], timedelta(minutes=30))
        self.assertTrue(all(datetime.fromisoformat(x[2]).isoweekday() <= 5 for x in h))

    def test_intervalo_entre_entrevistas(self):
        h = agenda.gerar_horarios(cfg(intervalo=15, horizonte_dias=0), agora=self.AGORA)
        self.assertEqual([x[3] for x in h], ["09:00", "09:45", "10:30"])

    def test_antecedencia_minima(self):
        agora = local_ny(2026, 11, 2, 8)
        h = agenda.gerar_horarios(cfg(antecedencia_horas=2, horizonte_dias=0), agora=agora)
        self.assertEqual([x[3] for x in h], ["10:00", "10:30"])

    def test_horizonte(self):
        h = agenda.gerar_horarios(cfg(horizonte_dias=1), agora=self.AGORA)
        self.assertEqual(sorted({x[2] for x in h}), ["2026-11-02", "2026-11-03"])

    def test_datas_bloqueadas_e_dias_da_semana(self):
        h = agenda.gerar_horarios(cfg(bloqueios=["2026-11-03"], horizonte_dias=2), agora=self.AGORA)
        self.assertEqual(sorted({x[2] for x in h}), ["2026-11-02", "2026-11-04"])
        h = agenda.gerar_horarios(cfg(dias=[6], horizonte_dias=7), agora=self.AGORA)
        self.assertEqual(sorted({x[2] for x in h}), ["2026-11-07"])

    def test_fuso_da_empresa(self):
        h = agenda.gerar_horarios(cfg(fuso="America/Sao_Paulo", horizonte_dias=0), agora=utc(2026, 11, 2, 10))
        self.assertEqual(h[0][0], utc(2026, 11, 2, 12))           # 09:00 em São Paulo = 12:00Z
        self.assertEqual(h[0][3], "09:00")

    def test_horario_de_verao_fim(self):
        # o horário de verão dos EUA termina no domingo, 1 de novembro de 2026
        h = agenda.gerar_horarios(cfg(dias=[1, 2, 3, 4, 5, 6, 7], horizonte_dias=4, fim="09:30"),
                                  agora=utc(2026, 10, 30, 12))
        por_dia = {x[2]: x for x in h}
        self.assertEqual(por_dia["2026-10-31"][0], utc(2026, 10, 31, 13))   # 09:00 EDT
        self.assertEqual(por_dia["2026-11-02"][0], utc(2026, 11, 2, 14))    # 09:00 EST
        self.assertTrue(all(x[3] == "09:00" for x in h))

    def test_horario_de_verao_inicio_pula_hora_inexistente(self):
        # 8 de março de 2026: 02:00 a 03:00 não existe em Nova York
        h = agenda.gerar_horarios(cfg(dias=[7, 1], inicio="02:00", fim="03:00", horizonte_dias=1),
                                  agora=utc(2026, 3, 8, 5))
        dias = [x[2] for x in h]
        self.assertNotIn("2026-03-08", dias)
        self.assertEqual(dias.count("2026-03-09"), 2)

    def test_ocupados_e_limite_por_dia(self):
        ocupado = (utc(2026, 11, 2, 14, 30), utc(2026, 11, 2, 15))   # 09:30 local
        h = agenda.gerar_horarios(cfg(horizonte_dias=0), [ocupado], agora=self.AGORA)
        self.assertEqual([x[3] for x in h], ["09:00", "10:00", "10:30"])
        h = agenda.gerar_horarios(cfg(horizonte_dias=0, intervalo=30, fim="12:00"), [ocupado], agora=self.AGORA)
        self.assertNotIn("09:00", [x[3] for x in h])   # 09:00 a 09:30 não deixa 30 min antes das 09:30
        h = agenda.gerar_horarios(cfg(horizonte_dias=1, max_por_dia=1), [ocupado], agora=self.AGORA)
        self.assertEqual({x[2] for x in h}, {"2026-11-03"})

    def test_validacao_da_config(self):
        base = agenda.PADRAO
        self.assertEqual(agenda.validar({"inicio": "18:00", "fim": "09:00"}, base)[1], "O fim da janela deve ser depois do início")
        self.assertEqual(agenda.validar({"fuso": "Lua/Base"}, base)[1], "Fuso horário inválido")
        self.assertEqual(agenda.validar({"formato": "carta"}, base)[1], "Formato de entrevista inválido")
        self.assertEqual(agenda.validar({"bloqueios": "2026-13-40"}, base)[1], "Data bloqueada inválida (use AAAA-MM-DD)")
        c, erro = agenda.validar({"bloqueios": "2026-12-25, 2026-12-24\n2026-12-25", "max_por_dia": "", "duracao": "45"}, base)
        self.assertIsNone(erro)
        self.assertEqual((c["bloqueios"], c["max_por_dia"], c["duracao"]), (["2026-12-24", "2026-12-25"], 0, 45))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def setUp(self):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        self.conn = c = server.db()
        self.ea, _ = empresas.criar_empresa(c, "Belleza's Home Services CT")
        self.eb, _ = empresas.criar_empresa(c, "Outra Empresa")
        c.execute("UPDATE empresas SET modulos='[\"voz\"]' WHERE id IN (?,?)", (self.ea, self.eb))
        self.cargo = c.execute("INSERT INTO cargos (nome, empresa_id, voz_ativa) VALUES ('Cleaning Tech', ?, 0)",
                               (self.ea,)).lastrowid
        self.cargo_voz = c.execute("INSERT INTO cargos (nome, empresa_id, voz_ativa) VALUES ('Tech Voz', ?, 1)",
                                   (self.ea,)).lastrowid
        self.vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'House Cleaning Technician', 'aberta', ?)",
                              (self.cargo, self.ea)).lastrowid
        self.vaga_voz = c.execute("INSERT INTO vagas (cargo_id, titulo, status, empresa_id) VALUES (?, 'Tech Voz', 'aberta', ?)",
                                  (self.cargo_voz, self.ea)).lastrowid
        self.gestores = {}
        for login, idioma, empresa in (("tony", "pt", self.ea), ("carine", "en", self.ea), ("ana", "es", self.ea),
                                       ("intruso", "pt", self.eb)):
            gid = c.execute("INSERT INTO gestores (nome, login, senha, email, is_admin, aprovado, empresa_id, idioma)"
                            " VALUES (?,?,?,?,1,1,?,?)", (login, login, "x", login + "@example.com", empresa, idioma)).lastrowid
            c.execute("INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)", ("sess-" + login, gid))
            self.gestores[login] = gid
        server.config_set(c, "smtp_host", "smtp.teste")
        server.config_set(c, "smtp_remetente", "Equipe <rh@example.com>")
        server.config_set(c, "url_publica", "https://rh.exemplo.com")
        c.commit()
        self.enviados = []
        self._original = server.enviar_email

        def gravar(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt"):
            self.enviados.append({"para": para, "assunto": assunto, "corpo": corpo, "html": html or "",
                                  "anexos": anexos or []})
            return True, "enviado"

        server.enviar_email = gravar

    def tearDown(self):
        server.enviar_email = self._original
        self.conn.close()

    def ligar_agenda(self, empresa=None, **extra):
        c = cfg(dias=[1, 2, 3, 4, 5, 6, 7], inicio="09:00", fim="17:00", horizonte_dias=14, antecedencia_horas=0,
                local="100 Main St, New Britain, CT", entrevistador="Carine", formato="presencial")
        c.update(extra)
        agenda.salvar(self.conn, empresa or self.ea, c)

    def candidato(self, idioma="es", empresa=None, vaga=None, email="maria@example.com", nome="Maria Lopez", testes=True):
        c = self.conn
        empresa = empresa or self.ea
        cid = c.execute("INSERT INTO candidatos (token, nome, email, local, telefone, cargo_desejado_id, idioma, empresa_id)"
                        " VALUES (?,?,?,?,?,?,?,?)",
                        ("tok-" + email, nome, email, "", "+18605550101", None, idioma, empresa)).lastrowid
        if vaga is not False:
            c.execute("INSERT INTO candidaturas (candidato_id, vaga_id, etapa) VALUES (?,?,'avaliacoes')",
                      (cid, vaga or self.vaga))
        if testes:
            c.execute("INSERT INTO resultados_teste (candidato_id, tipo, payload) VALUES (?,?,?)", (cid, "disc", json.dumps(DISC)))
            c.execute("INSERT INTO resultados_teste (candidato_id, tipo, payload) VALUES (?,?,?)", (cid, "base", json.dumps(BASE)))
        c.commit()
        return c.execute("SELECT * FROM candidatos WHERE id=?", (cid,)).fetchone()

    def req(self, metodo, caminho, dados=None, gestor=None, idioma=None):
        cab = {"Content-Type": "application/json"}
        if gestor:
            cab["X-Gestor-Token"] = "sess-" + gestor
        if idioma:
            cab["X-Idioma"] = idioma
        corpo = json.dumps(dados).encode() if dados is not None else None
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=cab)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def token(self, cand):
        return agenda.token_do_candidato(self.conn, cand["id"])

    def primeiro_livre(self, token, pular=0):
        st, d = self.req("GET", "/api/agenda/" + token)
        self.assertEqual(st, 200, d)
        return [h for dia in d["dias"] for h in dia["horarios"]][pular]["inicio_utc"]

    def para(self, email):
        return [e for e in self.enviados if e["para"] == email]


class TestMarcacao(Base):
    def test_pagina_publica_e_dados(self):
        self.ligar_agenda()
        cand = self.candidato()
        st, d = self.req("GET", "/api/agenda/" + self.token(cand))
        self.assertEqual(st, 200)
        self.assertEqual((d["empresa"]["nome"], d["nome"], d["idioma"], d["formato"], d["duracao"]),
                         ("Belleza's Home Services CT", "Maria", "es", "presencial", 30))
        self.assertEqual(d["fuso"], "America/New_York")
        self.assertIn("New York", d["rotulo_fuso"])
        self.assertTrue(d["dias"] and d["dias"][0]["horarios"])
        self.assertIsNone(d["entrevista"])
        self.assertNotIn("email", d)
        # token inválido, curto ou de candidato anonimizado
        self.assertEqual(self.req("GET", "/api/agenda/" + "x" * 30)[0], 404)
        st, d = self.req("GET", "/api/agenda/abc", idioma="en")
        self.assertEqual((st, d["erro"]), (404, "Invalid scheduling link"))

    def test_pagina_html_servida(self):
        with urllib.request.urlopen(self.base + "/agendar?t=qualquer") as resp:
            html = resp.read().decode()
        self.assertIn("js/agendar.js", html)

    def test_marcar_move_etapa_registra_evento_e_avisa(self):
        self.ligar_agenda()
        cand = self.candidato(idioma="es")
        tok = self.token(cand)
        inicio = self.primeiro_livre(tok, 5)
        st, d = self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": inicio})
        self.assertEqual(st, 200, d)
        self.assertEqual(d["entrevista"]["inicio_utc"], inicio)
        ent = self.conn.execute("SELECT * FROM entrevistas_agenda WHERE candidato_id=?", (cand["id"],)).fetchone()
        self.assertEqual((ent["status"], ent["empresa_id"]), ("marcada", self.ea))
        self.assertTrue(ent["candidatura_id"])
        etapa = self.conn.execute("SELECT etapa FROM candidaturas WHERE candidato_id=?", (cand["id"],)).fetchone()[0]
        self.assertEqual(etapa, "entrevista")
        eventos = [r[0] for r in self.conn.execute("SELECT texto FROM eventos WHERE candidato_id=?", (cand["id"],))]
        self.assertTrue(any(e.startswith("Entrevista marcada pelo candidato") for e in eventos))
        # e-mails: candidata em espanhol, cada gestor no seu idioma, intruso de outra empresa nada
        self.assertEqual(len(self.para("maria@example.com")), 1)
        self.assertTrue(self.para("maria@example.com")[0]["assunto"].startswith("Entrevista confirmada"))
        self.assertIn("Presencial", self.para("maria@example.com")[0]["corpo"])
        self.assertTrue(self.para("tony@example.com")[0]["assunto"].startswith("Entrevista marcada: Maria Lopez"))
        self.assertTrue(self.para("carine@example.com")[0]["assunto"].startswith("Interview scheduled: Maria Lopez"))
        self.assertTrue(self.para("ana@example.com")[0]["assunto"].startswith("Entrevista agendada: Maria Lopez"))
        self.assertEqual(self.para("intruso@example.com"), [])
        nome, ics, mime = self.para("carine@example.com")[0]["anexos"][0]
        self.assertEqual((nome, mime), ("interview.ics", "text/calendar"))
        # o horário marcado sai da lista dos outros
        outro = self.candidato(idioma="en", email="joe@example.com", nome="Joe Smith")
        st, d = self.req("GET", "/api/agenda/" + self.token(outro))
        self.assertNotIn(inicio, [h["inicio_utc"] for dia in d["dias"] for h in dia["horarios"]])

    def test_nao_marca_o_mesmo_horario_duas_vezes(self):
        self.ligar_agenda()
        a = self.candidato(email="a@example.com")
        b = self.candidato(email="b@example.com", idioma="en")
        inicio = self.primeiro_livre(self.token(a), 3)
        self.assertEqual(self.req("POST", "/api/agenda/%s/marcar" % self.token(a), {"inicio_utc": inicio})[0], 200)
        st, d = self.req("POST", "/api/agenda/%s/marcar" % self.token(b), {"inicio_utc": inicio}, idioma="en")
        self.assertEqual((st, d["erro"]), (409, "This time is no longer available"))
        # horário fora das regras também é recusado
        st, _ = self.req("POST", "/api/agenda/%s/marcar" % self.token(b), {"inicio_utc": "2026-01-01T03:17:00Z"})
        self.assertEqual(st, 409)
        st, _ = self.req("POST", "/api/agenda/%s/marcar" % self.token(b), {"inicio_utc": "ontem"})
        self.assertEqual(st, 400)

    def test_corrida_simultanea_so_um_ganha(self):
        self.ligar_agenda()
        cands = [self.candidato(email="c%d@example.com" % i) for i in range(6)]
        tokens = [self.token(c) for c in cands]
        inicio = self.primeiro_livre(tokens[0], 2)
        resultados = []

        def tentar(tok):
            resultados.append(self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": inicio})[0])

        fios = [threading.Thread(target=tentar, args=(tok,)) for tok in tokens]
        for f in fios:
            f.start()
        for f in fios:
            f.join()
        self.assertEqual(sorted(resultados), [200, 409, 409, 409, 409, 409])
        n = self.conn.execute("SELECT COUNT(*) FROM entrevistas_agenda WHERE inicio_utc=? AND status='marcada'",
                              (inicio,)).fetchone()[0]
        self.assertEqual(n, 1)

    def test_remarcar_mantem_a_mesma_entrevista(self):
        self.ligar_agenda()
        cand = self.candidato(idioma="pt")
        tok = self.token(cand)
        primeiro = self.primeiro_livre(tok, 4)
        self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": primeiro})
        segundo = self.primeiro_livre(tok, 10)
        st, d = self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": segundo})
        self.assertEqual(st, 200, d)
        linhas = self.conn.execute("SELECT * FROM entrevistas_agenda WHERE candidato_id=?", (cand["id"],)).fetchall()
        self.assertEqual(len(linhas), 1)
        self.assertEqual((linhas[0]["inicio_utc"], linhas[0]["sequencia"], linhas[0]["status"]), (segundo, 1, "marcada"))
        self.assertTrue(self.para("maria@example.com")[-1]["assunto"].startswith("Entrevista remarcada"))
        ics = self.para("maria@example.com")[-1]["anexos"][0][1].decode()
        self.assertIn("SEQUENCE:1", ics)
        # o horário antigo volta a ficar livre
        outro = self.candidato(email="z@example.com")
        st, d = self.req("GET", "/api/agenda/" + self.token(outro))
        self.assertIn(primeiro, [h["inicio_utc"] for dia in d["dias"] for h in dia["horarios"]])

    def test_cancelar_pelo_candidato_e_marcar_de_novo(self):
        self.ligar_agenda()
        cand = self.candidato(idioma="en")
        tok = self.token(cand)
        inicio = self.primeiro_livre(tok, 4)
        self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": inicio})
        self.enviados.clear()
        st, d = self.req("POST", "/api/agenda/%s/cancelar" % tok)
        self.assertEqual(st, 200, d)
        self.assertIsNone(d["entrevista"])
        ent = self.conn.execute("SELECT * FROM entrevistas_agenda WHERE candidato_id=?", (cand["id"],)).fetchone()
        self.assertEqual(ent["status"], "cancelada")
        self.assertTrue(ent["cancelada_em"])
        email = self.para("maria@example.com")[0]
        self.assertEqual(email["assunto"], "Interview canceled")
        ics = email["anexos"][0][1].decode()
        self.assertIn("METHOD:CANCEL", ics)
        self.assertIn("STATUS:CANCELLED", ics)
        self.assertTrue(self.para("tony@example.com")[0]["assunto"].startswith("Entrevista cancelada: Maria Lopez"))
        self.assertEqual(self.req("POST", "/api/agenda/%s/cancelar" % tok)[0], 400)
        # pode marcar de novo, inclusive o mesmo horário
        self.assertEqual(self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": inicio})[0], 200)

    def test_agenda_desligada(self):
        cand = self.candidato()
        st, d = self.req("GET", "/api/agenda/" + self.token(cand))
        self.assertEqual((st, d["ativo"], d["dias"]), (200, False, []))
        st, d = self.req("POST", "/api/agenda/%s/marcar" % self.token(cand), {"inicio_utc": "2030-01-01T14:00:00Z"})
        self.assertEqual((st, d["erro"]), (400, "A agenda de entrevistas está desativada"))


class TestIcs(Base):
    def test_conteudo_do_convite(self):
        self.ligar_agenda(local="100 Main St, New Britain; CT")
        cand = self.candidato(idioma="en")
        inicio = self.primeiro_livre(self.token(cand), 1)
        ent, acao = agenda.marcar(self.conn, cand, inicio)
        self.assertEqual(acao, "marcada")
        ics = agenda.gerar_ics(self.conn, ent, "en").decode()
        self.assertTrue(ics.startswith("BEGIN:VCALENDAR\r\n"))
        self.assertTrue(ics.endswith("END:VCALENDAR\r\n"))
        self.assertIn("METHOD:REQUEST", ics)
        self.assertIn("UID:entrevista-%d@rh.exemplo.com" % ent["id"], ics)
        dt = datetime.strptime(inicio, "%Y-%m-%dT%H:%M:%SZ")
        self.assertIn("DTSTART:" + dt.strftime("%Y%m%dT%H%M%SZ"), ics)
        self.assertIn("DTEND:" + (dt + timedelta(minutes=30)).strftime("%Y%m%dT%H%M%SZ"), ics)
        self.assertIn("SUMMARY:Interview: Belleza's Home Services CT", ics)
        self.assertIn("LOCATION:100 Main St\\, New Britain\\; CT", ics)
        self.assertIn("ORGANIZER;CN=Belleza's Home Services CT:mailto:rh@example.com", ics)
        self.assertTrue(all(len(l.encode()) <= 75 for l in ics.split("\r\n")))
        self.assertIn("mailto:maria@example.com", ics.replace("\r\n ", ""))
        # UID estável: o cancelamento usa o mesmo
        ent = self.conn.execute("SELECT * FROM entrevistas_agenda WHERE id=?", (ent["id"],)).fetchone()
        agenda.cancelar(self.conn, ent)
        ent = self.conn.execute("SELECT * FROM entrevistas_agenda WHERE id=?", (ent["id"],)).fetchone()
        cancel = agenda.gerar_ics(self.conn, ent, "pt", cancelar_evento=True).decode()
        self.assertIn("UID:entrevista-%d@rh.exemplo.com" % ent["id"], cancel)
        self.assertIn("SEQUENCE:1", cancel)

    def test_linha_longa_e_dobrada(self):
        linha = "DESCRIPTION:" + "á" * 100
        dobrada = agenda._ics_dobrar(linha)
        self.assertTrue(all(len(p.encode()) <= 75 for p in dobrada.split("\r\n")))
        self.assertEqual(dobrada.replace("\r\n ", ""), linha)


class TestEmailResultados(Base):
    def resultados(self, cand):
        return mensagens.email_resultado_candidato(self.conn, cand)

    def test_link_so_quando_qualifica_e_agenda_ligada(self):
        cand = self.candidato(idioma="en")
        _, texto, html, _ = self.resultados(cand)
        self.assertNotIn("/agendar?t=", texto + html)               # agenda desligada
        self.ligar_agenda()
        _, texto, html, _ = self.resultados(cand)                    # cargo sem triagem por voz
        self.assertIn("/agendar?t=", texto)
        self.assertIn("Choose your interview time", html)
        self.assertIn("lang=en", texto)

    def test_cargo_com_voz_exige_strong_ou_good(self):
        self.ligar_agenda()
        cand = self.candidato(idioma="es", vaga=self.vaga_voz)
        self.assertFalse(agenda.qualifica(self.conn, cand))
        _, texto, html, _ = self.resultados(cand)
        self.assertNotIn("/agendar?t=", texto + html)
        self.conn.execute("UPDATE candidaturas SET voz_tier='WEAK' WHERE candidato_id=?", (cand["id"],))
        self.assertFalse(agenda.qualifica(self.conn, cand))
        self.conn.execute("UPDATE candidaturas SET voz_tier='GOOD' WHERE candidato_id=?", (cand["id"],))
        self.assertTrue(agenda.qualifica(self.conn, cand))
        _, texto, html, _ = self.resultados(cand)
        self.assertIn("Elige el horario de tu entrevista", html)

    def test_empresa_sem_modulo_de_voz_qualifica(self):
        self.ligar_agenda()
        self.conn.execute("UPDATE empresas SET modulos='[]' WHERE id=?", (self.ea,))
        cand = self.candidato(vaga=self.vaga_voz)
        self.assertTrue(agenda.qualifica(self.conn, cand))

    def test_fluxo_completo_de_notificacao(self):
        self.ligar_agenda()
        cand = self.candidato(idioma="pt")
        server.notificar_avaliacao_completa(self.conn, cand)
        email = self.para("maria@example.com")[0]
        self.assertIn("/agendar?t=", email["corpo"])
        self.assertIn("Escolher horário da entrevista", email["html"])


class TestGestor(Base):
    def test_config_somente_admin_e_validada(self):
        self.conn.execute("UPDATE gestores SET is_admin=0 WHERE login='carine'")
        self.conn.commit()
        self.assertEqual(self.req("GET", "/api/gestor/agenda/config", gestor="carine")[0], 403)
        st, d = self.req("GET", "/api/gestor/agenda/config", gestor="tony")
        self.assertEqual((st, d["config"]["fuso"], d["config"]["duracao"], d["config"]["antecedencia_horas"],
                          d["config"]["horizonte_dias"], d["config"]["ativo"]), (200, "America/New_York", 30, 12, 14, False))
        st, d = self.req("POST", "/api/gestor/agenda/config", {"ativo": True, "dias": [1, 3], "inicio": "10:00",
                                                                "fim": "12:00", "formato": "video", "bloqueios": "2026-12-25"},
                         gestor="tony")
        self.assertEqual(st, 200, d)
        salvo = agenda.config(self.conn, self.ea)
        self.assertEqual((salvo["dias"], salvo["formato"], salvo["bloqueios"]), ([1, 3], "video", ["2026-12-25"]))
        st, d = self.req("POST", "/api/gestor/agenda/config", {"inicio": "25:00"}, gestor="tony", idioma="es")
        self.assertEqual((st, d["erro"]), (400, "Horario inválido"))
        # outra empresa continua com a própria configuração
        self.assertFalse(agenda.config(self.conn, self.eb)["ativo"])

    def test_ficha_enviar_link_e_status(self):
        self.ligar_agenda()
        cand = self.candidato(idioma="en", vaga=self.vaga_voz)   # não se qualifica, mas o gestor pode enviar
        st, d = self.req("GET", "/api/gestor/agenda/candidato/%d" % cand["id"], gestor="tony")
        self.assertEqual((st, d["ativo"], d["entrevista"], d["qualifica"]), (200, True, None, False))
        self.assertIn("/agendar?t=", d["link"])
        st, d = self.req("POST", "/api/gestor/agenda/enviar-link", {"candidato_id": cand["id"]}, gestor="tony")
        self.assertEqual(st, 200, d)
        email = self.para("maria@example.com")[0]
        self.assertEqual(email["assunto"], "Choose your interview time")
        self.assertIn("/agendar?t=", email["corpo"])
        tok = self.token(cand)
        self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": self.primeiro_livre(tok, 2)})
        st, d = self.req("GET", "/api/gestor/agenda/candidato/%d" % cand["id"], gestor="carine")
        ent_id = d["entrevista"]["id"]
        self.assertEqual(self.req("POST", "/api/gestor/agenda/entrevista/%d/status" % ent_id, {"status": "xyz"},
                                  gestor="tony")[0], 400)
        self.assertEqual(self.req("POST", "/api/gestor/agenda/entrevista/%d/status" % ent_id, {"status": "realizada"},
                                  gestor="tony")[0], 200)
        self.assertEqual(self.conn.execute("SELECT status FROM entrevistas_agenda WHERE id=?", (ent_id,)).fetchone()[0],
                         "realizada")
        self.assertEqual(self.req("POST", "/api/gestor/agenda/entrevista/%d/status" % ent_id, {"status": "faltou"},
                                  gestor="tony")[0], 200)

    def test_cancelar_pelo_gestor_avisa(self):
        self.ligar_agenda()
        cand = self.candidato(idioma="es")
        tok = self.token(cand)
        self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": self.primeiro_livre(tok, 2)})
        ent_id = self.conn.execute("SELECT id FROM entrevistas_agenda").fetchone()[0]
        self.enviados.clear()
        st, d = self.req("POST", "/api/gestor/agenda/entrevista/%d/status" % ent_id, {"status": "cancelada"}, gestor="tony")
        self.assertEqual(st, 200, d)
        self.assertEqual(self.para("maria@example.com")[0]["assunto"], "Entrevista cancelada")
        self.assertIn("METHOD:CANCEL", self.para("ana@example.com")[0]["anexos"][0][1].decode())

    def test_isolamento_entre_empresas(self):
        self.ligar_agenda()
        self.ligar_agenda(self.eb)
        cand = self.candidato()
        tok = self.token(cand)
        inicio = self.primeiro_livre(tok, 0)
        self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": inicio})
        ent_id = self.conn.execute("SELECT id FROM entrevistas_agenda").fetchone()[0]
        self.assertEqual(self.req("GET", "/api/gestor/agenda/candidato/%d" % cand["id"], gestor="intruso")[0], 404)
        self.assertEqual(self.req("POST", "/api/gestor/agenda/enviar-link", {"candidato_id": cand["id"]},
                                  gestor="intruso")[0], 404)
        self.assertEqual(self.req("POST", "/api/gestor/agenda/entrevista/%d/status" % ent_id, {"status": "cancelada"},
                                  gestor="intruso")[0], 404)
        self.assertEqual(self.conn.execute("SELECT status FROM entrevistas_agenda").fetchone()[0], "marcada")
        # o mesmo horário continua livre na outra empresa
        outro = self.candidato(empresa=self.eb, vaga=False, email="b@example.com")
        st, d = self.req("GET", "/api/agenda/" + self.token(outro))
        self.assertEqual(d["empresa"]["nome"], "Outra Empresa")
        self.assertIn(inicio, [h["inicio_utc"] for dia in d["dias"] for h in dia["horarios"]])
        self.assertEqual(self.req("POST", "/api/agenda/%s/marcar" % self.token(outro), {"inicio_utc": inicio})[0], 200)
        # proximas: cada gestor só vê a própria empresa
        hoje_a = agenda.proximas(self.conn, self.conn.execute("SELECT * FROM gestores WHERE login='tony'").fetchone(),
                                 agora=datetime.strptime(inicio, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) - timedelta(minutes=1))
        nomes = [i["candidato_id"] for i in hoje_a["hoje"] + hoje_a["amanha"]]
        self.assertEqual(nomes, [cand["id"]])
        st, d = self.req("GET", "/api/gestor/agenda/proximas", gestor="intruso")
        self.assertEqual(st, 200)
        self.assertNotIn(cand["id"], [i["candidato_id"] for i in d["hoje"] + d["amanha"]])

    def test_gestor_com_unidade_nao_ve_outra_unidade(self):
        self.ligar_agenda()
        self.conn.execute("UPDATE gestores SET is_admin=0, local='Hartford' WHERE login='carine'")
        self.conn.commit()
        cand = self.candidato()
        self.conn.execute("UPDATE candidatos SET local='New Britain' WHERE id=?", (cand["id"],))
        self.conn.commit()
        self.assertEqual(self.req("GET", "/api/gestor/agenda/candidato/%d" % cand["id"], gestor="carine")[0], 404)
        tok = self.token(cand)
        self.req("POST", "/api/agenda/%s/marcar" % tok, {"inicio_utc": self.primeiro_livre(tok, 0)})
        self.assertEqual(self.para("carine@example.com"), [])


class TestLembrete(Base):
    def test_lembrete_uma_vez_cerca_de_24h_antes(self):
        self.ligar_agenda(antecedencia_horas=48)
        cand = self.candidato(idioma="en")
        inicio = self.primeiro_livre(self.token(cand), 0)
        agenda.marcar(self.conn, cand, inicio)
        quando = datetime.strptime(inicio, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        self.enviados.clear()
        self.assertEqual(agenda.enviar_lembretes(self.conn, agora=quando - timedelta(hours=30)), 0)
        self.assertEqual(agenda.enviar_lembretes(self.conn, agora=quando - timedelta(hours=23)), 1)
        self.assertEqual(agenda.enviar_lembretes(self.conn, agora=quando - timedelta(hours=22)), 0)
        self.assertEqual(len(self.enviados), 1)
        self.assertEqual(self.enviados[0]["assunto"], "Reminder: your interview is tomorrow")
        self.assertEqual(self.enviados[0]["para"], "maria@example.com")

    def test_marcacao_em_cima_da_hora_nao_gera_lembrete_extra(self):
        self.ligar_agenda()
        cand = self.candidato()
        inicio = self.primeiro_livre(self.token(cand), 0)   # menos de 24 horas à frente (antecedência 0)
        quando = datetime.strptime(inicio, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if quando - datetime.now(timezone.utc) > timedelta(hours=24):
            self.skipTest("sem horário nas próximas 24 horas")
        agenda.marcar(self.conn, cand, inicio)
        self.enviados.clear()
        self.assertEqual(agenda.enviar_lembretes(self.conn), 0)


class TestTextos(unittest.TestCase):
    def test_chaves_nos_3_idiomas(self):
        for lang in ("en", "es"):
            self.assertEqual(set(agenda.T["pt"]), set(agenda.T[lang]), lang)
            self.assertEqual(set(agenda.T["pt"]["formatos"]), set(agenda.T[lang]["formatos"]))

    def test_sem_travessoes_nos_arquivos_da_agenda(self):
        for arq in ("agenda.py", "teste_agenda.py", "public/agendar.html", "public/js/agendar.js",
                    "public/js/gestor-agenda.js"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)

    def test_erros_traduzidos(self):
        import erros_i18n
        with open(os.path.join(AQUI, "agenda.py"), encoding="utf-8") as f:
            fonte = f.read()
        msgs = set(re.findall(r'"erro": "([^"]+)"', fonte)) | set(re.findall(r'ErroAgenda\(\d+, "([^"]+)"\)', fonte))
        msgs |= set(re.findall(r'return None, "([^"]+)"', fonte))
        for m in msgs:
            if m.endswith(": "):
                continue
            self.assertIn(m, erros_i18n.ERROS, m)
            self.assertNotEqual(erros_i18n.traduzir(m, "en"), m, m)


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
