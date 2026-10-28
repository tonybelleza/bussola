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
for arquivo in ("server.py", "voz.py", "empresas.py", "mensagens.py", "erros_i18n.py", "entrada.py", "agenda.py", "talentos.py", "seguranca.py"):
    shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
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

    def link_assinado(self):
        return "wss://exemplo/assinado"

    def iniciar(self, telefone, variaveis, idioma, candidato_id, abertura):
        nome = variaveis["candidate_name"]
        self.ultimas_variaveis = variaveis
        self.ultima_abertura = abertura
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

class TestRoteiro(unittest.TestCase):
    def test_validacao_e_limites(self):
        r, erro = voz.validar_roteiro({
            "fatos": "Pay $18/h", "faqs": [{"pergunta": "Uniform?", "resposta": "Yes"}, {"pergunta": "", "resposta": "x"}],
            "perguntas": ["Do you speak English?", "  "], "exige_carro": False, "cidades_25": ["Hartford", ""],
        })
        self.assertIsNone(erro)
        self.assertEqual(r["faqs"], [{"pergunta": "Uniform?", "resposta": "Yes"}])
        self.assertEqual(r["perguntas"], ["Do you speak English?"])
        self.assertEqual((r["exige_carro"], r["exige_carteira"]), (False, True))
        self.assertEqual(r["cidades_25"], ["Hartford"])
        self.assertEqual(voz.validar_roteiro({"fatos": "x" * 7000})[1], "text_too_long")

    def test_cargo_sem_exigencia_de_carro_nao_reprova(self):
        sem_carro = dict(FATOS_FORTES, own_car="no")
        self.assertEqual(voz.pontuar(sem_carro)["outcome"], "NOT_QUALIFIED")
        r = voz.pontuar(sem_carro, dict(voz.ROTEIRO_PADRAO, exige_carro=False))
        self.assertEqual((r["outcome"], r["score"]), ("QUALIFIED", 100))

    def test_area_propria_do_cargo(self):
        roteiro = dict(voz.ROTEIRO_PADRAO, cidades_25=["Sacramento"], cidades_40=["Davis"])
        self.assertEqual(voz.faixa_da_cidade("sacramento, CA", roteiro), "25mi")
        self.assertEqual(voz.faixa_da_cidade("Davis", roteiro), "40mi")
        self.assertIsNone(voz.faixa_da_cidade("Hartford", roteiro))
        r = voz.pontuar(dict(FATOS_FORTES, city="Davis", distance_band="unknown"), roteiro)
        self.assertEqual(r["pontos"]["location"], 10)


class TestRetorno(unittest.TestCase):
    CFG = {"fuso": "America/New_York", "inicio": "09:00", "fim": "19:30", "dias": [1, 2, 3, 4, 5, 6], "intervalo_horas": 4}

    def quando(self, texto, agora="2026-10-27 14:00"):
        r = voz.horario_de_retorno(texto, ct(agora), self.CFG)
        return r.astimezone(CT).strftime("%a %H:%M") if r else None

    def test_frases_comuns(self):
        self.assertEqual(self.quando("tomorrow 3 pm"), "Wed 15:00")
        self.assertEqual(self.quando("Thursday morning"), "Thu 10:00")
        self.assertEqual(self.quando("today 5 pm"), "Tue 17:00")
        self.assertEqual(self.quando("mañana en la mañana"), "Wed 10:00")
        self.assertEqual(self.quando("viernes por la tarde"), "Fri 14:00")
        self.assertEqual(self.quando("amanhã às 10h"), "Wed 10:00")

    def test_fora_da_janela_vai_para_a_proxima_abertura(self):
        self.assertEqual(self.quando("Sunday 10 am"), "Mon 09:00")
        self.assertEqual(self.quando("today 9 pm"), "Wed 09:00")

    def test_sem_horario_reconhecivel(self):
        self.assertIsNone(self.quando("later"))
        self.assertIsNone(self.quando(""))


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

    def test_nao_disponivel_com_triagem_completa_e_pontuado(self):
        r = voz.pontuar(dict(FATOS_FORTES, outcome="NOT_AVAILABLE"))
        self.assertEqual((r["outcome"], r["motivos"][0]), ("NEEDS_REVIEW", "outcome_corrected"))
        self.assertIsNotNone(r["score"])
        self.assertIsNone(voz.pontuar({"outcome": "NOT_AVAILABLE"})["score"])

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

    def test_etapa_alcancada_no_placar(self):
        self.assertEqual(voz.etapa_alcancada({}), "start")
        self.assertEqual(voz.etapa_alcancada({"recording_consent": True}), "consent")
        self.assertEqual(voz.etapa_alcancada({"recording_consent": True, "preferred_language": "es",
                                              "license": "yes", "city": "Hartford"}), "town")
        self.assertEqual(voz.etapa_alcancada(FATOS_FORTES), "text_phone")
        self.assertEqual(voz.etapa_alcancada({"recording_consent": False, "has_smartphone": False}), "smartphone")


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
        self.empresa, _ = empresas.criar_empresa(c, "BHS CT")
        c.execute("UPDATE empresas SET modulos='[\"voz\"]' WHERE id=?", (self.empresa,))
        self.cargo = c.execute(
            "INSERT INTO cargos (nome, area, nivel, voz_ativa, peso_voz, empresa_id)"
            " VALUES ('Cleaning Tech','Ops','',1,0.30,?)", (self.empresa,),
        ).lastrowid
        self.vaga = c.execute(
            "INSERT INTO vagas (cargo_id, titulo, local, status, empresa_id)"
            " VALUES (?, 'Cleaning Technician', 'BHS CT', 'aberta', ?)",
            (self.cargo, self.empresa),
        ).lastrowid
        c.commit()

    def tearDown(self):
        voz.GATEWAY_TESTE = None
        self.conn.close()

    def candidato(self, nome="Maria", telefone="+1 8605550101", email="maria@example.com", idioma=""):
        c = self.conn
        cid = c.execute(
            "INSERT INTO candidatos (token, nome, email, local, telefone, cargo_desejado_id, idioma, empresa_id)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (nome + str(time.time()), nome, email, "BHS CT", telefone, self.cargo, idioma, self.empresa),
        ).lastrowid
        c.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cid, self.vaga))
        voz.nova_candidatura(c, cid, self.vaga)
        c.commit()
        return cid

    def candidatura(self, cid):
        return self.conn.execute("SELECT * FROM candidaturas WHERE candidato_id=?", (cid,)).fetchone()

    def test_variaveis_levam_identidade_roteiro_e_curriculo(self):
        a = self.candidato()
        voz.salvar_config(self.conn, self.empresa, {"nome_ligacao": "Belleza's Home Services", "cidade": "Hartford",
                                                    "telefone_retorno": "860-790-9545", "gerente": "Carine"})
        self.conn.execute("UPDATE cargos SET roteiro_voz=? WHERE id=?", (json.dumps({
            "fatos": "Pay starts at $18 per hour.", "faqs": [{"pergunta": "Uniform?", "resposta": "Provided."}],
            "perguntas": ["Can you start at 7:30 am?"], "exige_carro": False}), self.cargo))
        self.conn.execute("UPDATE candidatos SET analise_ia=? WHERE id=?",
                          (json.dumps({"resumo": "5 years cleaning homes.", "experiencias": ["Maid Pro 2019-2024"]}), a))
        self.conn.execute("UPDATE candidatos SET cargo_atual='Cleaner at Maid Pro' WHERE id=?", (a,))
        server.registrar_evento(self.conn, a, "anotacao", "Ask why she left the last job after 2 months", "Carine")
        self.conn.commit()
        voz.tick(self.conn, self.TERCA_10H)
        v = self.falso.ultimas_variaveis
        self.assertIn("Current job (from the application): Cleaner at Maid Pro", v["resume_summary"])
        self.assertIn("Ask why she left", v["team_notes"])
        self.assertEqual((v["company_name"], v["company_city"], v["hiring_manager"]), ("Belleza's Home Services", "Hartford", "Carine"))
        self.assertIn("$18", v["job_facts"])
        self.assertIn("Q: Uniform?", v["faq"])
        self.assertIn("7:30", v["extra_questions"])
        self.assertIn("NOT required", v["requirements"])
        self.assertIn("Maid Pro", v["resume_summary"])
        self.assertIn("Belleza's Home Services en Hartford", self.falso.ultima_abertura)
        self.assertTrue(all(isinstance(x, str) for x in v.values()))
        self.assertEqual(v["voicemail_message"], "Hola Maria, le habla Francisca de Belleza's Home Services, sobre su "
                         "solicitud para el puesto de Cleaning Tech. Por favor llámenos al 860-790-9545. Gracias.")

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
        voz.salvar_config(self.conn, self.empresa, {"pausado": 1})
        voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(self.falso.ligacoes, [])
        voz.salvar_config(self.conn, self.empresa, {"pausado": 0})
        self.conn.execute("UPDATE candidaturas SET voz_status='nao_ligar' WHERE candidato_id=?", (a,))
        self.conn.execute("UPDATE candidatos SET telefone='+55 11999998888'")
        self.candidato(nome="Ana", telefone="+55 11988887777", email="ana@example.com")
        voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(self.falso.ligacoes, [])

    def test_config_da_empresa_sobrepoe_o_padrao(self):
        self.candidato()
        voz.salvar_config(self.conn, self.empresa, {"pausado": 1})
        voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(self.falso.ligacoes, [])
        self.assertEqual(voz.config_empresa(self.conn, self.empresa)["pausado"], 1)
        self.assertEqual(voz.config_empresa(self.conn, None)["pausado"], 0)

    def test_empresa_sem_modulo_ou_suspensa_nao_liga(self):
        self.candidato()
        self.conn.execute("UPDATE empresas SET modulos='[]' WHERE id=?", (self.empresa,))
        voz.tick(self.conn, self.TERCA_10H)
        self.conn.execute("UPDATE empresas SET modulos='[\"voz\"]', status='suspensa' WHERE id=?", (self.empresa,))
        voz.tick(self.conn, self.TERCA_10H)
        self.assertEqual(self.falso.ligacoes, [])

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

    def test_numero_errado_e_sem_interesse_saem_do_pipeline(self):
        for outcome, etiqueta in (("WRONG_NUMBER", "número errado"), ("NOT_INTERESTED", "sem interesse")):
            a = self.candidato(nome="Pessoa " + outcome, telefone="+1 86055501%02d" % len(outcome))
            voz.tick(self.conn, self.TERCA_10H)
            self.conn.execute("UPDATE voz_chamadas SET iniciada_em=datetime('now','-10 minutes')")
            self.conn.commit()
            conv = [c for c in self.conn.execute("SELECT conversation_id FROM voz_chamadas WHERE candidato_id=?", (a,))][-1][0]
            self.falso.conversas[conv] = conversa(dict(FATOS_FORTES, outcome=outcome))
            voz.reconciliar(self.conn)
            ca = self.candidatura(a)
            self.assertEqual(ca["etapa"], "reprovado")
            self.assertIn("triagem por voz", ca["motivo_reprovacao"])
            tags = json.loads(self.conn.execute("SELECT tags FROM candidatos WHERE id=?", (a,)).fetchone()[0])
            self.assertIn(etiqueta, tags)

    def test_ligacao_presa_em_initiated_libera_a_fila(self):
        a = self.candidato()
        voz.tick(self.conn, self.TERCA_10H)
        self.conn.execute("UPDATE voz_chamadas SET iniciada_em=datetime('now','-20 minutes')")
        self.conn.commit()
        self.falso.conversas["conv_1"] = {"status": "initiated", "transcript": []}
        self.assertEqual(voz.reconciliar(self.conn), 1)
        ca = self.candidatura(a)
        self.assertEqual(ca["voz_status"], "para_ligar")
        ch = self.conn.execute("SELECT status, erro FROM voz_chamadas").fetchone()
        self.assertEqual((ch["status"], ch["erro"]), ("falhou", "stuck_initiated"))

    def test_ligacao_recente_em_initiated_espera(self):
        self.candidato()
        voz.tick(self.conn, self.TERCA_10H)
        self.conn.execute("UPDATE voz_chamadas SET iniciada_em=datetime('now','-5 minutes')")
        self.conn.commit()
        self.falso.conversas["conv_1"] = {"status": "initiated", "transcript": []}
        self.assertEqual(voz.reconciliar(self.conn), 0)

    def test_callback_com_horario_volta_para_a_fila_no_horario(self):
        a = self.candidato()
        voz.tick(self.conn, self.TERCA_10H)
        self.conn.execute("UPDATE voz_chamadas SET iniciada_em=datetime('now','-10 minutes')")
        self.conn.commit()
        self.falso.conversas["conv_1"] = conversa(dict(FATOS_FORTES, outcome="CALLBACK", callback_time="Friday 10 am"))
        voz.reconciliar(self.conn)
        ca = self.candidatura(a)
        self.assertEqual((ca["voz_status"], ca["voz_tentativas"]), ("para_ligar", 0))
        proxima = voz._de_sql(ca["voz_proxima"]).astimezone(CT)
        self.assertEqual((proxima.isoweekday(), proxima.hour), (5, 10))

    def test_callback_sem_horario_fica_para_o_gestor(self):
        a = self.candidato()
        voz.tick(self.conn, self.TERCA_10H)
        self.conn.execute("UPDATE voz_chamadas SET iniciada_em=datetime('now','-10 minutes')")
        self.conn.commit()
        self.falso.conversas["conv_1"] = conversa(dict(FATOS_FORTES, outcome="CALLBACK", callback_time=None))
        voz.reconciliar(self.conn)
        self.assertEqual(self.candidatura(a)["voz_status"], "callback")

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


# ================================================================ isolamento entre empresas

class TestIsolamento(unittest.TestCase):
    def test_regras_de_visibilidade(self):
        admin_a = {"is_admin": 1, "local": "", "empresa_id": 1}
        unidade_a = {"is_admin": 0, "local": "Hartford", "empresa_id": 1}
        geral_a = {"is_admin": 0, "local": "", "empresa_id": 1}
        admin_b = {"is_admin": 1, "local": "", "empresa_id": 2}
        cand_a = {"local": "hartford ", "empresa_id": 1}
        cand_a2 = {"local": "Springfield", "empresa_id": 1}
        cand_b = {"local": "Hartford", "empresa_id": 2}
        self.assertTrue(server.gestor_ve_candidato(admin_a, cand_a2))
        self.assertTrue(server.gestor_ve_candidato(unidade_a, cand_a))
        self.assertFalse(server.gestor_ve_candidato(unidade_a, cand_a2))
        self.assertTrue(server.gestor_ve_candidato(geral_a, cand_a2))
        # nada atravessa de uma empresa para outra, nem para o admin
        self.assertFalse(server.gestor_ve_candidato(admin_b, cand_a))
        self.assertFalse(server.gestor_ve_candidato(admin_a, cand_b))
        self.assertFalse(server.gestor_ve_candidato({"is_admin": 1, "local": "", "empresa_id": None}, cand_a))

    def test_avisos_so_para_a_empresa_do_candidato(self):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        conn = server.db()
        ea, _ = empresas.criar_empresa(conn, "Empresa A")
        eb, _ = empresas.criar_empresa(conn, "Empresa B")
        for login, local, admin, eid in (("dono.a", "", 1, ea), ("unidade.a", "Hartford", 0, ea),
                                         ("outra.unidade.a", "Boston", 0, ea), ("admin.b", "", 1, eb)):
            conn.execute(
                "INSERT INTO gestores (login, senha, nome, email, local, is_admin, empresa_id) VALUES (?,?,?,?,?,?,?)",
                (login, "x", login, login + "@example.com", local, admin, eid),
            )
        conn.commit()
        self.assertEqual(server.emails_gestores_do_local(conn, {"empresa_id": ea, "local": "Hartford"}),
                         ["dono.a@example.com", "unidade.a@example.com"])
        self.assertEqual(server.emails_gestores_do_local(conn, {"empresa_id": eb, "local": ""}),
                         ["admin.b@example.com"])
        conn.close()


# ================================================================ HTTP

class TestHTTP(unittest.TestCase):
    """Duas empresas pelo HTTP: A tem o módulo de voz, B não. Nada de A aparece para B."""

    @classmethod
    def setUpClass(cls):
        if os.path.exists(server.DB_PATH):
            os.remove(server.DB_PATH)
        server.init_db()
        conn = server.db()
        server.config_set(conn, "elevenlabs_webhook_secret", "segredo")
        cls.ea, _ = empresas.criar_empresa(conn, "BHS CT")
        cls.eb, _ = empresas.criar_empresa(conn, "Outra Empresa")
        conn.execute("UPDATE empresas SET modulos='[\"voz\"]' WHERE id=?", (cls.ea,))
        for login, admin, eid, local in (("admin", 1, cls.ea, ""), ("carine", 0, cls.ea, "BHS CT"),
                                         ("admin.b", 1, cls.eb, ""), ("outro", 0, cls.eb, "")):
            conn.execute(
                "INSERT INTO gestores (login, senha, nome, local, is_admin, empresa_id) VALUES (?,?,?,?,?,?)",
                (login, server.hash_senha("senha-123"), login.title(), local, admin, eid),
            )
        cls.cargo_a = conn.execute(
            "INSERT INTO cargos (nome, empresa_id, voz_ativa) VALUES ('Cleaning Tech', ?, 1)", (cls.ea,)
        ).lastrowid
        cls.vaga_a = conn.execute(
            "INSERT INTO vagas (cargo_id, titulo, local, status, empresa_id) VALUES (?, 'Tech A', 'BHS CT', 'aberta', ?)",
            (cls.cargo_a, cls.ea),
        ).lastrowid
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

    def test_importados_aparecem_fora_da_triagem_e_entram_na_fila(self):
        conn = server.db()
        ids = []
        for nome, tel in (("Importada Um", "+18605550111"), ("Importada Dois", "8605550112"), ("Sem Fone", "")):
            cid = conn.execute("INSERT INTO candidatos (token, nome, email, local, telefone, empresa_id) VALUES (?,?,?,?,?,?)",
                               ("imp" + nome, nome, "", "BHS CT", tel, self.ea)).lastrowid
            ids.append(conn.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)",
                                    (cid, self.vaga_a)).lastrowid)
        conn.commit()
        admin = self.token("admin")
        status, d = self.req("GET", "/api/gestor/voz", cabecalhos=admin)
        fora = {f["id"]: f for f in d["fora"]}
        self.assertTrue(set(ids) <= set(fora))
        self.assertFalse(fora[ids[2]]["telefone_valido"])
        self.assertEqual(self.req("GET", "/api/gestor/voz", cabecalhos=self.token("admin.b"))[0], 403)
        status, d = self.req("POST", "/api/gestor/voz/fila", {"ids": ids[:2]}, admin)
        self.assertEqual((status, d["colocados"]), (200, 2))
        status, d = self.req("POST", "/api/gestor/voz/fila", {"ids": ids[:2]}, admin)
        self.assertEqual(d["colocados"], 0)
        st = conn.execute("SELECT voz_status FROM candidaturas WHERE id=?", (ids[0],)).fetchone()[0]
        self.assertEqual(st, "para_ligar")
        cand = conn.execute("SELECT candidato_id FROM candidaturas WHERE id=?", (ids[2],)).fetchone()[0]
        status, d = self.req("GET", "/api/gestor/voz/candidato/%d" % cand, cabecalhos=admin)
        self.assertEqual([c["voz_status"] for c in d["candidaturas"]], [""])
        conn.close()

    def test_simulacao_e_revisao_do_roteiro(self):
        admin, carine = self.token("admin"), self.token("carine")
        self.assertEqual(self.req("POST", "/api/gestor/voz/cargo/%d/simular" % self.cargo_a, {"idioma": "en"}, carine)[0], 403)
        status, d = self.req("POST", "/api/gestor/voz/cargo/%d/simular" % self.cargo_a, {"idioma": "en"}, admin)
        self.assertEqual(status, 200, d)
        self.assertEqual(d["signed_url"], "wss://exemplo/assinado")
        self.assertEqual(d["dynamic_variables"]["candidate_name"], "Test Candidate")
        self.assertIn("{{candidate_name}}", d["first_message"])
        self.assertEqual(self.req("POST", "/api/gestor/voz/cargo/%d/simular" % self.cargo_a, {}, self.token("admin.b"))[0], 403)
        status, d = self.req("POST", "/api/gestor/voz/cargo/%d/roteiro" % self.cargo_a, {"fatos": "Pay $20/h"}, admin)
        self.assertEqual(status, 200, d)
        self.assertEqual(len(d["roteiro"]["revisado_em"]), 10)
        status, d = self.req("GET", "/api/gestor/voz", cabecalhos=admin)
        self.assertTrue([c for c in d["cargos"] if c["id"] == self.cargo_a][0]["revisado_em"])

    def test_modulo_liberado_por_empresa(self):
        self.assertEqual(self.req("GET", "/api/gestor/voz", cabecalhos=self.token("admin.b"))[0], 403)
        status, d = self.req("GET", "/api/gestor/voz", cabecalhos=self.token("carine"))
        self.assertEqual(status, 200)
        self.assertEqual([c["nome"] for c in d["cargos"]], ["Cleaning Tech"])
        self.assertEqual(self.req("GET", "/api/gestor/voz")[0], 401)

    def test_integracao_e_da_plataforma_e_cargo_so_do_admin_da_empresa(self):
        admin = self.token("admin")
        self.assertEqual(self.req("POST", "/api/gestor/voz/integracao", {"api_key": "x"}, admin)[0], 403)
        self.assertEqual(self.req("POST", "/api/gestor/voz/cargo/%d" % self.cargo_a, {"voz_ativa": True},
                                  self.token("carine"))[0], 403)
        self.assertEqual(self.req("POST", "/api/gestor/voz/cargo/%d" % self.cargo_a, {"voz_ativa": True}, admin)[0], 200)

    def test_config_e_pausa(self):
        carine = self.token("carine")
        self.assertEqual(self.req("POST", "/api/gestor/voz/config", {"config": {"inicio": "08:30"}}, carine)[0], 403)
        status, d = self.req("POST", "/api/gestor/voz/config", {"config": {"pausado": True}}, carine)
        self.assertEqual((status, d["config"]["pausado"]), (200, 1))
        admin = self.token("admin")
        status, d = self.req("POST", "/api/gestor/voz/config", {"config": {"inicio": "08:30", "max_tentativas": 2,
                                                                           "pausado": False}}, admin)
        self.assertEqual((status, d["config"]["inicio"], d["config"]["max_tentativas"]), (200, "08:30", 2))
        status, d = self.req("POST", "/api/gestor/voz/config", {"config": {"inicio": "25:00"}}, admin)
        self.assertEqual((status, d.get("codigo")), (400, "invalid_time"))

    def test_outra_empresa_nao_ve_nem_altera_nada(self):
        b = self.token("admin.b")
        _, vagas = self.req("GET", "/api/gestor/vagas", cabecalhos=b)
        self.assertEqual(vagas["vagas"], [])
        _, cargos = self.req("GET", "/api/gestor/cargos", cabecalhos=b)
        self.assertEqual(cargos["cargos"], [])
        self.assertEqual(self.req("GET", "/api/gestor/vaga/%d/pipeline" % self.vaga_a, cabecalhos=b)[0], 404)
        self.assertEqual(self.req("GET", "/api/gestor/cargo/%d/avaliacoes" % self.cargo_a, cabecalhos=b)[0], 404)
        self.assertEqual(self.req("POST", "/api/gestor/vaga", {"id": self.vaga_a, "titulo": "invadida",
                                                               "cargo_id": self.cargo_a}, b)[0], 400)
        self.assertEqual(self.req("DELETE", "/api/gestor/vaga/%d" % self.vaga_a, cabecalhos=b)[0], 200)
        _, vagas_a = self.req("GET", "/api/gestor/vagas", cabecalhos=self.token("admin"))
        self.assertEqual([v["titulo"] for v in vagas_a["vagas"]], ["Tech A"])  # continua lá
        self.assertEqual(self.req("POST", "/api/gestor/pergunta-entrevista",
                                  {"cargo_id": self.cargo_a, "texto": "x"}, b)[0], 404)
        self.assertEqual(self.req("POST", "/api/gestor/competencia",
                                  {"cargo_id": self.cargo_a, "nome": "x"}, b)[0], 404)
        _, g = self.req("GET", "/api/gestor/gestores", cabecalhos=b)
        self.assertEqual(sorted(x["login"] for x in g["gestores"]), ["admin.b", "outro"])

    def test_roteiro_so_admin_edita_e_outra_empresa_nao_ve(self):
        caminho = "/api/gestor/voz/cargo/%d/roteiro" % self.cargo_a
        self.assertEqual(self.req("GET", caminho, cabecalhos=self.token("carine"))[0], 200)
        self.assertEqual(self.req("POST", caminho, {"fatos": "x"}, self.token("carine"))[0], 403)
        status, d = self.req("POST", caminho, {"fatos": "Pay $18", "faqs": [{"pergunta": "A?", "resposta": "B"}]},
                             self.token("admin"))
        self.assertEqual((status, d["roteiro"]["fatos"]), (200, "Pay $18"))
        self.assertEqual(self.req("GET", caminho, cabecalhos=self.token("admin.b"))[0], 403)  # sem o módulo
        _, lido = self.req("GET", caminho, cabecalhos=self.token("admin"))
        self.assertEqual(lido["roteiro"]["faqs"], [{"pergunta": "A?", "resposta": "B"}])

    def test_portal_publico_exige_o_link_da_empresa(self):
        _, sem = self.req("GET", "/api/vagas")
        self.assertEqual(sem["vagas"], [])
        _, com = self.req("GET", "/api/vagas?e=bhs-ct")
        self.assertEqual([v["titulo"] for v in com["vagas"]], ["Tech A"])
        _, outra = self.req("GET", "/api/vagas?e=outra-empresa")
        self.assertEqual(outra["vagas"], [])
        _, cargos = self.req("GET", "/api/cargos")
        self.assertEqual(cargos["cargos"], [])
        status, _ = self.req("POST", "/api/candidato/cadastro", {
            "nome": "X", "email": "x@example.com", "local": "BHS CT", "telefone": "+1 8605550101",
            "consentimento": True})
        self.assertEqual(status, 400)  # sem vaga e sem link da empresa
        status, d = self.req("POST", "/api/candidato/cadastro", {
            "nome": "Y", "email": "y@example.com", "local": "qualquer coisa", "telefone": "+1 8605550101",
            "consentimento": True, "vaga_id": self.vaga_a})
        self.assertEqual(status, 200)
        _, lista_b = self.req("GET", "/api/gestor/candidatos", cabecalhos=self.token("admin.b"))
        self.assertEqual(lista_b["candidatos"], [])
        status, _ = self.req("POST", "/api/gestor/solicitar-acesso",
                             {"nome": "Z", "login": "z", "email": "z@x.com", "senha": "senha-123"})
        self.assertEqual(status, 400)

    def test_placar_semanal_numeros_e_isolamento(self):
        conn = server.db()
        conn.execute("DELETE FROM voz_chamadas")
        zona = voz._zona(voz.config_empresa(conn, self.ea))
        agora = datetime.now(zona)
        seg = agora.date().toordinal() - agora.weekday()

        def quando(semanas_atras, hora, minuto=0):
            d = datetime.fromordinal(seg - 7 * semanas_atras)
            return voz._sql(datetime(d.year, d.month, d.day, hora, minuto, tzinfo=zona))

        cargo_b = conn.execute("INSERT INTO cargos (nome, empresa_id, voz_ativa) VALUES ('Tech B', ?, 1)",
                               (self.eb,)).lastrowid
        vaga_b = conn.execute("INSERT INTO vagas (cargo_id, titulo, local, status, empresa_id)"
                              " VALUES (?, 'Vaga B', '', 'aberta', ?)", (cargo_b, self.eb)).lastrowid
        conn.commit()

        def limpar():
            # apaga os dados do placar para não afetar os outros testes da classe
            conn.execute("DELETE FROM voz_chamadas WHERE conversation_id LIKE 'placar_%'")
            conn.execute("DELETE FROM candidaturas WHERE candidato_id IN"
                         " (SELECT id FROM candidatos WHERE token LIKE 'placar%')")
            conn.execute("DELETE FROM candidatos WHERE token LIKE 'placar%'")
            conn.execute("DELETE FROM vagas WHERE id=?", (vaga_b,))
            conn.execute("DELETE FROM cargos WHERE id=?", (cargo_b,))
            conn.commit()
            conn.close()

        self.addCleanup(limpar)
        seq = [0]

        def ligacao(empresa, vaga, local, inicio, status="concluida", falou=True, fatos=None, resultado=None,
                    duracao=None, idioma="es"):
            seq[0] += 1
            cid = conn.execute("INSERT INTO candidatos (token, nome, email, local, telefone, empresa_id)"
                               " VALUES (?,?,?,?,?,?)", ("placar%d" % seq[0], "Placar %d" % seq[0], "", local,
                                                        "+18605550199", empresa)).lastrowid
            ca = conn.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cid, vaga)).lastrowid
            falas = [{"papel": "agent", "texto": "Hola", "t": 0}] + ([{"papel": "user", "texto": "Si", "t": 3}] if falou else [])
            conn.execute(
                "INSERT INTO voz_chamadas (candidatura_id, candidato_id, conversation_id, status, idioma, iniciada_em,"
                " duracao, transcricao, fatos, resultado) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (ca, cid, "placar_%d" % seq[0], status, idioma, inicio, duracao, json.dumps(falas),
                 json.dumps(fatos) if fatos is not None else "", json.dumps(resultado) if resultado else ""))

        a, ct_local = self.ea, "BHS CT"
        # semana atual da empresa A
        ligacao(a, self.vaga_a, ct_local, quando(0, 10), fatos=FATOS_FORTES, duracao=300,
                resultado={"outcome": "QUALIFIED", "tier": "STRONG", "score": 95, "motivos": []})
        ligacao(a, self.vaga_a, ct_local, quando(0, 10, 30), idioma="en", duracao=200,
                fatos=dict(FATOS_FORTES, preferred_language="en", outcome="NEEDS_REVIEW", pets=None, standards=None),
                resultado={"outcome": "NEEDS_REVIEW", "tier": "GOOD", "score": 60,
                           "motivos": ["missing:pets", "missing:standards"]})
        ligacao(a, self.vaga_a, ct_local, quando(0, 14), duracao=60,
                fatos={"recording_consent": True, "preferred_language": "es", "license": "yes",
                       "own_car": "yes", "city": "Hartford", "outcome": None},
                resultado={"outcome": "NEEDS_REVIEW", "score": None, "tier": None, "motivos": ["no_outcome"]})
        ligacao(a, self.vaga_a, ct_local, quando(0, 14, 10), falou=False, duracao=25,
                fatos={"outcome": "VOICEMAIL"}, resultado={"outcome": "VOICEMAIL", "score": None})
        ligacao(a, self.vaga_a, ct_local, quando(0, 14, 20), status="falhou", falou=False)
        ligacao(a, self.vaga_a, ct_local, quando(0, 15), status="iniciando", falou=False)
        # outra unidade da empresa A: o admin vê, a Carine (BHS CT) não
        ligacao(a, self.vaga_a, "NY Office", quando(0, 11), status="falhou", falou=False)
        # semana passada da empresa A
        ligacao(a, self.vaga_a, ct_local, quando(1, 9), idioma="pt", duracao=40,
                fatos={"recording_consent": True, "preferred_language": "pt", "outcome": "CALLBACK"},
                resultado={"outcome": "CALLBACK", "score": None})
        ligacao(a, self.vaga_a, ct_local, quando(1, 9, 30), status="falhou", falou=False)
        # fora do período (9 semanas atrás) e uma ligação da empresa B
        ligacao(a, self.vaga_a, ct_local, quando(9, 10), status="falhou", falou=False)
        ligacao(self.eb, vaga_b, "", quando(0, 10), fatos=FATOS_FORTES, duracao=500,
                resultado={"outcome": "QUALIFIED", "tier": "STRONG", "score": 95, "motivos": []})
        conn.commit()

        status, d = self.req("GET", "/api/gestor/voz/placar?semanas=8", cabecalhos=self.token("carine"))
        self.assertEqual(status, 200, d)
        self.assertEqual(len(d["semanas"]), 8)
        s0, s1 = d["semanas"][0], d["semanas"][1]
        self.assertTrue(s0["inicio"] > s1["inicio"])
        self.assertEqual((s0["ligacoes"], s0["atendidas"], s0["correio_voz"], s0["sem_resposta"], s0["em_andamento"]),
                         (6, 3, 1, 1, 1))
        self.assertEqual(s0["taxa_atendimento"], 60.0)
        self.assertEqual((s0["duracao_media"], s0["duracao_mediana"]), (186.7, 200.0))
        self.assertEqual((s0["outcomes"]["QUALIFIED"], s0["outcomes"]["NEEDS_REVIEW"], s0["outcomes"]["CALLBACK"]),
                         (1, 2, 0))
        self.assertEqual(s0["tiers"], {"STRONG": 1, "GOOD": 1, "REVIEW": 0, "LOW": 0})
        self.assertEqual(s0["idiomas"], {"es": 2, "en": 1, "pt": 0})
        self.assertEqual(s0["horas"], [{"hora": 10, "ligacoes": 2, "atendidas": 2, "taxa": 100.0},
                                       {"hora": 14, "ligacoes": 3, "atendidas": 1, "taxa": 33.3}])
        self.assertEqual(s0["abandono"], [{"etapa": "town", "n": 1}])
        self.assertEqual(s0["faltando"], [{"item": "pets", "n": 1}, {"item": "standards", "n": 1}])
        self.assertEqual((s0["qualificados_pct"], s0["strong_good"]), (33.3, 2))
        self.assertEqual((s1["ligacoes"], s1["atendidas"], s1["taxa_atendimento"], s1["duracao_mediana"]),
                         (2, 1, 50.0, 40.0))
        self.assertEqual(s1["abandono"], [{"etapa": "language", "n": 1}])
        self.assertEqual(s1["outcomes"]["CALLBACK"], 1)
        self.assertTrue(all(s["ligacoes"] == 0 for s in d["semanas"][2:]))
        t = d["total"]
        self.assertEqual((t["ligacoes"], t["atendidas"], t["taxa_atendimento"]), (8, 4, round(400 / 7, 1)))
        self.assertEqual(t["idiomas"], {"es": 2, "en": 1, "pt": 1})

        _, admin = self.req("GET", "/api/gestor/voz/placar?semanas=1", cabecalhos=self.token("admin"))
        self.assertEqual(len(admin["semanas"]), 1)
        self.assertEqual((admin["total"]["ligacoes"], admin["total"]["sem_resposta"]), (7, 2))

        # empresa B: sem o módulo, 403; com o módulo, só vê a própria ligação
        self.assertEqual(self.req("GET", "/api/gestor/voz/placar", cabecalhos=self.token("admin.b"))[0], 403)
        modulos_b = conn.execute("SELECT modulos FROM empresas WHERE id=?", (self.eb,)).fetchone()[0]
        conn.execute("UPDATE empresas SET modulos='[\"voz\"]' WHERE id=?", (self.eb,))
        conn.commit()
        try:
            status, b = self.req("GET", "/api/gestor/voz/placar", cabecalhos=self.token("admin.b"))
            self.assertEqual(status, 200)
            self.assertEqual((b["total"]["ligacoes"], b["total"]["duracao_media"]), (1, 500.0))
        finally:
            conn.execute("UPDATE empresas SET modulos=? WHERE id=?", (modulos_b, self.eb))
            conn.commit()


if __name__ == "__main__":
    try:
        unittest.main(verbosity=1)
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
