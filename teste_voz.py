#!/usr/bin/env python3
"""
Testes do módulo Triagem por Voz (voz.py).

Uso:  python3 teste_voz.py

Roda com banco isolado numa pasta temporária e um ElevenLabs falso: nenhuma
ligação real é feita e nada sai da máquina.
"""
import hashlib
import hmac
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="voz-teste-")
for arquivo in ("server.py", "voz.py"):
    shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)

import server  # noqa: E402  (importa a cópia, com banco isolado em PASTA)
import voz  # noqa: E402

CT = ZoneInfo("America/New_York")


def ct(texto):
    """Data e hora de Connecticut ('2026-10-27 10:00') em UTC."""
    return datetime.strptime(texto, "%Y-%m-%d %H:%M").replace(tzinfo=CT).astimezone(timezone.utc)


def local_ct(dt):
    return dt.astimezone(CT).strftime("%a %Y-%m-%d %H:%M")


FATOS_FORTES = {
    "candidate_name": "Maria", "preferred_language": "es", "outcome": "QUALIFIED",
    "recording_consent": True, "license": "yes", "own_car": "yes", "city": "West Hartford",
    "distance_band": "25mi", "weekdays_available": 5, "days_available": "L a V",
    "saturdays_ok": True, "experience_level": "two_plus_years", "experience": "5 años",
    "works_alone": "yes", "has_smartphone": True, "start_timeframe": "within_1_week",
    "start_date": "lunes", "pets": "comfortable", "standards": "accepted",
    "text_phone": "8605550101", "ok_to_text": True, "interview_windows": "martes mañana",
    "candidate_questions": None, "notes": None,
}


def conversa(fatos, falou=True, status="done"):
    return {
        "status": status,
        "transcript": (
            [{"role": "agent", "message": "[calm] Hola", "time_in_call_secs": 0},
             {"role": "user", "message": "Hola", "time_in_call_secs": 2.4}]
            if falou else [{"role": "agent", "message": "Hola", "time_in_call_secs": 0}]
        ),
        "metadata": {"call_duration_secs": 300},
        "analysis": {
            "transcript_summary": "Resumo",
            "data_collection_results": {k: {"value": v} for k, v in (fatos or {}).items()},
        },
        "has_audio": True,
    }


class FalsoElevenLabs:
    def __init__(self):
        self.ligacoes = []
        self.conversas = {}
        self.falhar = False

    def iniciar(self, telefone, nome, idioma, candidato_id):
        if self.falhar:
            self.falhar = False
            raise RuntimeError("twilio fora do ar")
        cid = "conv_%d" % (len(self.ligacoes) + 1)
        self.ligacoes.append((telefone, nome, idioma))
        self.conversas[cid] = {"status": "in-progress", "transcript": []}
        return cid, "CA" + cid

    def conversa(self, cid):
        return self.conversas[cid]

    def audio(self, cid):
        return b"ID3audio"


# ================================================================ regras puras

class TestScorecard(unittest.TestCase):
    def test_candidato_ideal(self):
        r = voz.pontuar(FATOS_FORTES)
        self.assertEqual((r["score"], r["tier"], r["outcome"], r["motivos"]), (100, "STRONG", "QUALIFIED", []))

    def test_faixas_menores(self):
        r = voz.pontuar(dict(FATOS_FORTES, weekdays_available=4, experience_level="under_two_or_informal",
                             city="Springfield, MA", works_alone="hesitant",
                             start_timeframe="within_2_weeks", pets="some_or_no"))
        self.assertEqual(r["pontos"], {"availability": 15, "experience": 10, "location": 10, "works_alone": 3,
                                       "smartphone": 10, "start_date": 7, "pets": 0, "standards": 5})
        self.assertEqual((r["score"], r["tier"]), (60, "GOOD"))

    def test_gate_reprova_sem_score(self):
        r = voz.pontuar(dict(FATOS_FORTES, own_car="no", outcome="NOT_QUALIFIED"))
        self.assertEqual((r["outcome"], r["score"]), ("NOT_QUALIFIED", None))

    def test_gate_incerto_vai_para_revisao(self):
        r = voz.pontuar(dict(FATOS_FORTES, license="unclear"))
        self.assertEqual(r["outcome"], "NEEDS_REVIEW")
        self.assertIn("license_unclear", r["motivos"])

    def test_resposta_faltando_nao_e_inventada(self):
        r = voz.pontuar(dict(FATOS_FORTES, weekdays_available=None, pets=None))
        self.assertEqual(r["pontos"]["availability"], 0)
        self.assertEqual(r["motivos"], ["missing:availability", "missing:pets"])

    def test_ligacoes_sem_triagem_nao_pontuam(self):
        for outcome in ("VOICEMAIL", "CALLBACK", "WRONG_NUMBER", "DO_NOT_CALL"):
            self.assertIsNone(voz.pontuar(dict(FATOS_FORTES, outcome=outcome))["score"])

    def test_sem_outcome(self):
        self.assertEqual(voz.pontuar(dict(FATOS_FORTES, outcome=None))["outcome"], "NEEDS_REVIEW")

    def test_tiers(self):
        for score, tier in ((75, "STRONG"), (74, "GOOD"), (55, "GOOD"), (54, "REVIEW"), (40, "REVIEW"), (39, "LOW")):
            self.assertEqual(voz.tier_do_score(score), tier)


class TestFatos(unittest.TestCase):
    def test_extrai_valida_e_normaliza(self):
        fatos, invalidos = voz.extrair_fatos(conversa(dict(FATOS_FORTES, weekdays_available="4", outcome="MAYBE")))
        self.assertEqual(fatos["weekdays_available"], 4)
        self.assertIsNone(fatos["outcome"])
        self.assertEqual(fatos["text_phone"], "+18605550101")
        self.assertEqual(invalidos, ['outcome="MAYBE"'])

    def test_telefones(self):
        self.assertEqual(voz.para_e164("+1 8605550101"), "+18605550101")
        self.assertEqual(voz.para_e164("(860) 555-0101"), "+18605550101")
        self.assertIsNone(voz.para_e164("+55 11999998888"))

    def test_marcas_de_voz(self):
        self.assertEqual(voz.limpar_marcas_de_voz("[neutral] Perfecto. [calm] ¿Qué días?"), "Perfecto. ¿Qué días?")

    def test_cidades(self):
        self.assertEqual(voz.faixa_da_cidade("west hartford, CT"), "25mi")
        self.assertEqual(voz.faixa_da_cidade("Chicopee MA"), "40mi")
        self.assertIsNone(voz.faixa_da_cidade("Boston"))


class TestRegras(unittest.TestCase):
    cfg = dict(voz.CONFIG_PADRAO)

    def linha(self, **extra):
        base = {"anonimizado": 0, "voz_status": "para_ligar", "voz_outcome": "", "telefone": "+1 8605550101",
                "voz_tentativas": 0, "voz_proxima": ""}
        base.update(extra)
        return base

    def test_janela(self):
        for texto, esperado in (("2026-10-26 09:00", True), ("2026-10-26 08:59", False),
                                ("2026-10-26 19:30", False), ("2026-10-31 12:00", True),
                                ("2026-11-01 12:00", False)):
            self.assertEqual(voz.dentro_da_janela(ct(texto), self.cfg), esperado, texto)

    def test_horario_de_verao(self):
        # 2026-11-02 é a segunda depois do fim do horário de verão: 14:00 UTC = 09:00 EST
        self.assertTrue(voz.dentro_da_janela(datetime(2026, 11, 2, 14, 0, tzinfo=timezone.utc), self.cfg))
        self.assertFalse(voz.dentro_da_janela(datetime(2026, 11, 2, 13, 59, tzinfo=timezone.utc), self.cfg))

    def test_bloqueios(self):
        agora = ct("2026-10-27 10:00")
        self.assertIsNone(voz.motivo_bloqueio(self.linha(), self.cfg, agora))
        casos = [
            ({"voz_status": "nao_ligar"}, "do_not_call"),
            ({"voz_outcome": "NOT_INTERESTED"}, "blocked_outcome"),
            ({"telefone": "+55 11999998888"}, "invalid_phone"),
            ({"voz_status": "ligando"}, "in_call"),
            ({"voz_tentativas": 3}, "attempts_exhausted"),
            ({"voz_status": "callback"}, "wrong_status"),
            ({"voz_proxima": "2026-10-27 18:00:00"}, "waiting_retry"),
            ({"anonimizado": 1}, "anonymized"),
        ]
        for extra, motivo in casos:
            self.assertEqual(voz.motivo_bloqueio(self.linha(**extra), self.cfg, agora), motivo, extra)
        self.assertEqual(voz.motivo_bloqueio(self.linha(), self.cfg, ct("2026-10-27 20:00")), "outside_window")
        self.assertEqual(voz.motivo_bloqueio(self.linha(), dict(self.cfg, pausado=1), agora), "paused")

    def test_manual_ignora_janela_mas_nao_bloqueios(self):
        noite = ct("2026-10-27 21:00")
        self.assertIsNone(voz.motivo_bloqueio(self.linha(voz_status="callback"), self.cfg, noite, manual=True))
        self.assertEqual(voz.motivo_bloqueio(self.linha(voz_status="nao_ligar"), self.cfg, noite, manual=True), "do_not_call")

    def test_proxima_tentativa(self):
        self.assertEqual(local_ct(voz.proxima_tentativa(ct("2026-10-27 10:00"), self.cfg)), "Tue 2026-10-27 14:00")
        self.assertEqual(local_ct(voz.proxima_tentativa(ct("2026-10-27 17:00"), self.cfg)), "Wed 2026-10-28 09:00")
        self.assertEqual(local_ct(voz.proxima_tentativa(ct("2026-10-31 17:00"), self.cfg)), "Mon 2026-11-02 09:00")

    def test_transicoes(self):
        self.assertEqual(voz.transicao("QUALIFIED", 1, 3), ("concluida", False, None))
        self.assertEqual(voz.transicao("DO_NOT_CALL", 1, 3), ("nao_ligar", False, None))
        self.assertEqual(voz.transicao("VOICEMAIL", 1, 3), ("para_ligar", True, None))
        self.assertEqual(voz.transicao(None, 3, 3), ("correio_voz", False, "no_answer_exhausted"))

    def test_assinatura(self):
        corpo = b'{"type":"post_call_transcription"}'
        t = int(time.time())
        bom = "t=%d,v0=%s" % (t, hmac.new(b"seg", b"%d." % t + corpo, hashlib.sha256).hexdigest())
        self.assertTrue(voz.assinatura_valida(corpo, bom, "seg"))
        self.assertFalse(voz.assinatura_valida(corpo, bom, "outro"))
        self.assertFalse(voz.assinatura_valida(corpo + b"x", bom, "seg"))
        velho = "t=%d,v0=%s" % (t - 7200, hmac.new(b"seg", b"%d." % (t - 7200) + corpo, hashlib.sha256).hexdigest())
        self.assertFalse(voz.assinatura_valida(corpo, velho, "seg"))


# ================================================================ fluxo com banco

class TestFluxo(unittest.TestCase):
    TERCA_10H = ct("2026-10-27 10:00")

    def setUp(self):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        self.falso = FalsoElevenLabs()
        voz.GATEWAY_TESTE = self.falso
        self.conn = server.db()
        c = self.conn
        self.cargo = c.execute(
            "INSERT INTO cargos (nome, area, nivel, voz_ativa, peso_voz) VALUES ('Cleaning Tech','Ops','',1,0.30)"
        ).lastrowid
        self.vaga = c.execute(
            "INSERT INTO vagas (cargo_id, titulo, local, status) VALUES (?, 'Cleaning Technician', 'BHS CT', 'aberta')",
            (self.cargo,),
        ).lastrowid
        c.commit()

    def tearDown(self):
        voz.GATEWAY_TESTE = None
        self.conn.close()

    def candidato(self, nome="Maria", telefone="+1 8605550101", email="maria@example.com", idioma=""):
        c = self.conn
        cid = c.execute(
            "INSERT INTO candidatos (token, nome, email, local, telefone, cargo_desejado_id, idioma)"
            " VALUES (?,?,?,?,?,?,?)",
            (nome + str(time.time()), nome, email, "BHS CT", telefone, self.cargo, idioma),
        ).lastrowid
        c.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cid, self.vaga))
        voz.nova_candidatura(c, cid, self.vaga)
        c.commit()
        return cid

    def candidatura(self, cid):
        return self.conn.execute("SELECT * FROM candidaturas WHERE candidato_id=?", (cid,)).fetchone()

    def test_entra_na_fila_so_com_voz_ativa(self):
        cid = self.candidato()
        self.assertEqual(self.candidatura(cid)["voz_status"], "para_ligar")
        self.conn.execute("UPDATE cargos SET voz_ativa=0")
        outro = self.candidato(nome="Ana", email="ana@example.com")
        self.assertEqual(self.candidatura(outro)["voz_status"], "")

    def test_liga_um_por_vez_e_pontua(self):
        a = self.candidato()
        b = self.candidato(nome="Ana", telefone="(860) 555-0102", email="ana@example.com", idioma="pt")
        r = voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(r["iniciadas"], 1)
        self.assertEqual(self.falso.ligacoes, [("+18605550101", "Maria", "es")])
        self.assertEqual(self.candidatura(a)["voz_status"], "ligando")

        self.assertEqual(voz.tick(self.conn, self.TERCA_10H)["iniciadas"], 0)  # linha ocupada

        self.falso.conversas["conv_1"] = conversa(FATOS_FORTES)
        self.assertTrue(voz.processar_conversa(self.conn, "conv_1"))
        ca = self.candidatura(a)
        self.assertEqual((ca["voz_status"], ca["voz_score"], ca["voz_tier"], ca["etapa"]),
                         ("concluida", 100, "STRONG", "avaliacoes"))
        chamada = self.conn.execute("SELECT * FROM voz_chamadas WHERE conversation_id='conv_1'").fetchone()
        self.assertEqual(json.loads(chamada["transcricao"]),
                         [{"papel": "agent", "texto": "Hola", "t": 0}, {"papel": "user", "texto": "Hola", "t": 2}])
        # idempotente
        voz.processar_conversa(self.conn, "conv_1")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM eventos WHERE texto LIKE 'Triagem por voz: QUALIFIED%'").fetchone()[0], 1)

        voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(self.falso.ligacoes[1], ("+18605550102", "Ana", "pt"))
        self.assertEqual(self.candidatura(b)["voz_status"], "ligando")

    def test_match_inclui_a_voz_com_peso_do_cargo(self):
        a = self.candidato()
        voz.tick(self.conn, self.TERCA_10H)
        self.falso.conversas["conv_1"] = conversa(dict(FATOS_FORTES, weekdays_available=4,
                                                       pets="some_or_no"))  # 85 pontos
        voz.processar_conversa(self.conn, "conv_1")
        cand = self.conn.execute("SELECT * FROM candidatos WHERE id=?", (a,)).fetchone()
        m = server.match_completo(self.conn, cand, self.cargo)
        self.assertEqual((m["geral"], m["componentes"]["voz"]), (85, 85))
        # com DISC alvo: 70% para os demais componentes e 30% para a voz
        self.conn.execute("UPDATE cargos SET disc_alvo='S' WHERE id=?", (self.cargo,))
        self.conn.execute(
            "INSERT INTO resultados_teste (candidato_id, tipo, payload) VALUES (?, 'disc', ?)",
            (a, json.dumps({"pct": {"D": 10, "I": 20, "S": 50, "C": 30}})),
        )
        m = server.match_completo(self.conn, cand, self.cargo)
        self.assertEqual(m["geral"], round(0.7 * 50 + 0.3 * 85))

    def test_sem_resposta_tenta_de_novo_e_para_no_limite(self):
        a = self.candidato()
        for tentativa in (1, 2, 3):
            self.conn.execute("UPDATE candidaturas SET voz_proxima=''")
            self.conn.commit()
            voz.tick(self.conn, self.TERCA_10H)
            cid = "conv_%d" % tentativa
            self.falso.conversas[cid] = conversa(None, falou=False)
            voz.processar_conversa(self.conn, cid)
            ca = self.candidatura(a)
            self.assertEqual(ca["voz_tentativas"], tentativa)
            self.assertEqual(ca["voz_status"], "para_ligar" if tentativa < 3 else "correio_voz")
        voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(len(self.falso.ligacoes), 3)

    def test_nao_liga_fora_da_janela_pausado_ou_bloqueado(self):
        a = self.candidato()
        voz.tick(self.conn, ct("2026-11-01 12:00"))  # domingo
        voz.salvar_config(self.conn, "", {"pausado": 1})
        voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(self.falso.ligacoes, [])
        voz.salvar_config(self.conn, "", {"pausado": 0})
        self.conn.execute("UPDATE candidaturas SET voz_status='nao_ligar' WHERE candidato_id=?", (a,))
        self.conn.execute("UPDATE candidatos SET telefone='+55 11999998888'")
        self.candidato(nome="Ana", telefone="+55 11988887777", email="ana@example.com")
        voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(self.falso.ligacoes, [])

    def test_config_do_local_sobrepoe_o_padrao(self):
        self.candidato()
        voz.salvar_config(self.conn, "BHS CT", {"pausado": 1})
        voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(self.falso.ligacoes, [])
        self.assertEqual(voz.config_local(self.conn, "bhs ct")["pausado"], 1)
        self.assertEqual(voz.config_local(self.conn, "")["pausado"], 0)

    def test_falha_ao_iniciar_nao_gasta_tentativa(self):
        a = self.candidato()
        self.falso.falhar = True
        voz.tick(self.conn, self.TERCA_10H)
        ca = self.candidatura(a)
        self.assertEqual((ca["voz_status"], ca["voz_tentativas"]), ("para_ligar", 0))

    def test_falha_de_inicio_pelo_webhook_conta_como_sem_resposta(self):
        a = self.candidato()
        voz.tick(self.conn, self.TERCA_10H)
        voz.falha_de_inicio(self.conn, "conv_1", "busy")
        ca = self.candidatura(a)
        self.assertEqual((ca["voz_status"], ca["voz_tentativas"]), ("para_ligar", 1))

    def test_reconcilia_webhook_perdido(self):
        a = self.candidato()
        voz.tick(self.conn, self.TERCA_10H)
        self.conn.execute("UPDATE voz_chamadas SET iniciada_em=datetime('now','-10 minutes')")
        self.conn.commit()
        self.falso.conversas["conv_1"] = conversa(dict(FATOS_FORTES, outcome="CALLBACK"))
        self.assertEqual(voz.reconciliar(self.conn), 1)
        ca = self.candidatura(a)
        self.assertEqual((ca["voz_status"], ca["voz_score"]), ("callback", None))

    def test_anonimizar_apaga_dados_da_voz(self):
        a = self.candidato()
        voz.tick(self.conn, self.TERCA_10H)
        self.falso.conversas["conv_1"] = conversa(FATOS_FORTES)
        voz.processar_conversa(self.conn, "conv_1")
        cand = self.conn.execute("SELECT * FROM candidatos WHERE id=?", (a,)).fetchone()
        server.anonimizar_candidato(self.conn, cand)
        self.conn.commit()
        self.assertEqual(self.conn.execute("SELECT telefone FROM candidatos WHERE id=?", (a,)).fetchone()[0], "")
        ch = self.conn.execute("SELECT transcricao, fatos FROM voz_chamadas").fetchone()
        self.assertEqual((ch["transcricao"], ch["fatos"]), ("[]", ""))


# ================================================================ HTTP

class TestHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        conn = server.db()
        server.config_set(conn, "elevenlabs_webhook_secret", "segredo")
        for login, admin, modulos in (("admin", 1, "[]"), ("carine", 0, '["voz"]'), ("outro", 0, "[]")):
            conn.execute(
                "INSERT INTO gestores (login, senha, nome, local, is_admin, modulos) VALUES (?,?,?,?,?,?)",
                (login, server.hash_senha("senha-123"), login.title(), "" if admin else "BHS CT", admin, modulos),
            )
        conn.commit()
        conn.close()
        voz.GATEWAY_TESTE = FalsoElevenLabs()
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        voz.GATEWAY_TESTE = None

    def req(self, metodo, caminho, dados=None, cabecalhos=None, bruto=None):
        corpo = bruto if bruto is not None else (json.dumps(dados).encode() if dados is not None else None)
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo,
                                   headers=dict({"Content-Type": "application/json"}, **(cabecalhos or {})))
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def token(self, login):
        status, d = self.req("POST", "/api/gestor/login", {"login": login, "senha": "senha-123"})
        self.assertEqual(status, 200, d)
        return {"X-Gestor-Token": d["token"]}

    def test_webhook_exige_assinatura(self):
        corpo = json.dumps({"type": "post_call_transcription", "data": {"conversation_id": "x"}}).encode()
        status, _ = self.req("POST", "/api/voz/webhook", bruto=corpo, cabecalhos={"ElevenLabs-Signature": "t=1,v0=abc"})
        self.assertEqual(status, 401)
        t = int(time.time())
        assinatura = "t=%d,v0=%s" % (t, hmac.new(b"segredo", b"%d." % t + corpo, hashlib.sha256).hexdigest())
        status, _ = self.req("POST", "/api/voz/webhook", bruto=corpo, cabecalhos={"ElevenLabs-Signature": assinatura})
        self.assertEqual(status, 200)

    def test_modulo_liberado_por_gestor(self):
        self.assertEqual(self.req("GET", "/api/gestor/voz", cabecalhos=self.token("outro"))[0], 403)
        status, d = self.req("GET", "/api/gestor/voz", cabecalhos=self.token("carine"))
        self.assertEqual(status, 200)
        self.assertIn("fila", d)
        self.assertEqual(self.req("GET", "/api/gestor/voz", cabecalhos=self.token("admin"))[0], 200)
        self.assertEqual(self.req("GET", "/api/gestor/voz")[0], 401)

    def test_integracao_e_cargo_so_admin(self):
        carine = self.token("carine")
        self.assertEqual(self.req("POST", "/api/gestor/voz/integracao", {"api_key": "x"}, carine)[0], 403)
        self.assertEqual(self.req("POST", "/api/gestor/voz/cargo/1", {"voz_ativa": True}, carine)[0], 403)
        admin = self.token("admin")
        self.assertEqual(self.req("POST", "/api/gestor/voz/integracao", {"api_key": "sk_123456", "agent_id": "a"}, admin)[0], 200)
        status, d = self.req("GET", "/api/gestor/voz/integracao", cabecalhos=admin)
        self.assertEqual((d["api_key_final"], d["agent_id"]), ("3456", "a"))
        self.assertNotIn("api_key", d)

    def test_config_respeita_o_local(self):
        carine = self.token("carine")
        self.assertEqual(self.req("POST", "/api/gestor/voz/config", {"local": "", "config": {"pausado": 1}}, carine)[0], 403)
        self.assertEqual(self.req("POST", "/api/gestor/voz/config", {"local": "Outro Local", "config": {"pausado": 1}}, carine)[0], 403)
        status, d = self.req("POST", "/api/gestor/voz/config", {"local": "BHS CT", "config": {"inicio": "08:30", "max_tentativas": 2}}, carine)
        self.assertEqual((status, d["config"]["inicio"], d["config"]["max_tentativas"]), (200, "08:30", 2))
        status, d = self.req("POST", "/api/gestor/voz/config", {"local": "BHS CT", "config": {"inicio": "25:00"}}, carine)
        self.assertEqual((status, d.get("codigo")), (400, "invalid_time"))


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
