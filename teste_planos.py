"""
Testes de planos, medição de uso e cobrança (planos.py): catálogo padrão e
edição pelo dono, calculadora de custos, minutos por mês e por empresa
(America/New_York), status de limite, voz bloqueada no limite (fila e ligação
manual) e liberada com excedente, assinatura pelo site (empresa em teste,
administrador e sessão, limite por IP), webhook do Stripe (assinatura válida,
inválida e antiga, ativação), rotina de fim do teste e isolamento.

Uso:  python3 teste_planos.py

Banco isolado numa pasta temporária. Nenhum e-mail sai da máquina e nenhuma
chamada vai ao Stripe ou ao ElevenLabs (falsos nos testes).
"""
import hashlib
import hmac
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = tempfile.mkdtemp(prefix="planos-teste-")
for arquivo in os.listdir(AQUI):
    if arquivo.endswith(".py") and not arquivo.startswith("teste_"):
        shutil.copy(os.path.join(AQUI, arquivo), PASTA)
shutil.copytree(os.path.join(AQUI, "public"), os.path.join(PASTA, "public"))
sys.path.insert(0, PASTA)

import empresas  # noqa: E402
import planos  # noqa: E402
import server  # noqa: E402
import voz  # noqa: E402

planos.ENVIO_EM_SEGUNDO_PLANO = False
server.Handler.log_message = lambda *a: None
CT = ZoneInfo("America/New_York")
TRACOS = re.compile("[\u2013\u2014]")


def ct(texto):
    return datetime.strptime(texto, "%Y-%m-%d %H:%M").replace(tzinfo=CT).astimezone(timezone.utc)


class FalsoElevenLabs:
    def __init__(self):
        self.ligacoes = []

    def iniciar(self, telefone, variaveis, idioma, candidato_id, abertura):
        cid = "conv_%d_%d" % (len(self.ligacoes) + 1, int(time.time() * 1000))
        self.ligacoes.append(telefone)
        return cid, "CA" + cid

    def conversa(self, cid):
        return {"status": "in-progress", "transcript": []}


class FalsoStripe:
    def __init__(self):
        self.chamadas = []

    def __call__(self, metodo, caminho, params):
        self.chamadas.append((metodo, caminho, params))
        if caminho == "/v1/checkout/sessions":
            return {"id": "cs_test_1", "url": "https://checkout.stripe.com/c/pay/cs_test_1"}
        if caminho == "/v1/billing_portal/sessions":
            return {"url": "https://billing.stripe.com/p/session/abc"}
        return {}


def assinar_stripe(corpo, segredo, t=None):
    t = int(time.time()) if t is None else t
    sig = hmac.new(segredo.encode(), ("%d." % t).encode() + corpo, hashlib.sha256).hexdigest()
    return "t=%d,v1=%s" % (t, sig)


# ================================================================ unidades

class TestCalculadora(unittest.TestCase):
    def test_custos_padrao(self):
        r = planos.custos(planos.CATALOGO_PADRAO, dict(planos.PREMISSAS_PADRAO))
        por = {x["codigo"]: x for x in r["planos"]}
        v300 = por["voz300"]
        # 300 x (0.09 + 0.014) + número 1.15 + 300 x 0.0083 + A2P 15
        self.assertAlmostEqual(v300["custo_variavel"], 49.84, places=2)
        self.assertAlmostEqual(v300["custo_fixo"], 60.0)          # 10 h x 60 / 10 empresas
        self.assertAlmostEqual(v300["custo_total"], 109.84, places=2)
        self.assertAlmostEqual(v300["margem"], 89.16, places=2)
        self.assertAlmostEqual(v300["margem_pct"], 44.8, places=1)
        self.assertEqual(v300["empresas_equilibrio"], 5)           # ceil(600 / (199 - 49.84))
        self.assertAlmostEqual(v300["preco_sugerido"], 366.13, places=2)
        self.assertEqual(v300["preco_sugerido_redondo"], 367)
        ess = por["essencial"]
        self.assertEqual(ess["custo_variavel"], 0)
        self.assertEqual(ess["empresas_equilibrio"], 16)            # ceil(600 / 39)
        self.assertAlmostEqual(ess["preco_sugerido"], 200.0)
        v100 = por["voz100"]
        self.assertAlmostEqual(v100["custo_variavel"], 10.4, places=2)  # número compartilhado, sem SMS
        self.assertEqual(r["custo_fixo_total"], 600)
        self.assertAlmostEqual(r["addons"]["minuto_extra"]["margem_pct"], 65.33, places=2)

    def test_premissas_mudam_o_resultado(self):
        pr = dict(planos.PREMISSAS_PADRAO, empresas_pagantes=20, margem_alvo=50, valor_hora=100)
        r = {x["codigo"]: x for x in planos.custos(planos.CATALOGO_PADRAO, pr)["planos"]}
        self.assertAlmostEqual(r["voz100"]["custo_fixo"], 50.0)
        self.assertAlmostEqual(r["voz100"]["preco_sugerido"], (10.4 + 50) * 2, places=2)
        p, erro = planos.validar_premissas({"empresas_pagantes": 0})
        self.assertEqual(erro, "Premissas inválidas")
        p, erro = planos.validar_premissas({"custo_min_voz": "abc"})
        self.assertEqual(erro, "Premissas inválidas")

    def test_status_de_uso(self):
        self.assertEqual(planos.status_uso(10, None), ("ok", None))
        self.assertEqual(planos.status_uso(79, 100)[0], "ok")
        self.assertEqual(planos.status_uso(80, 100)[0], "near")
        self.assertEqual(planos.status_uso(100, 100)[0], "over")
        self.assertEqual(planos.status_uso(130, 100), ("over", 130.0))
        self.assertEqual(planos.status_uso(0, 0)[0], "ok")
        self.assertEqual(planos.status_uso(1, 0)[0], "over")

    def test_assinatura_stripe(self):
        corpo = b'{"id":"evt_1"}'
        agora = 1_800_000_000
        cab = assinar_stripe(corpo, "whsec_x", agora)
        self.assertTrue(planos.assinatura_stripe_valida(corpo, cab, "whsec_x", agora=agora + 10))
        self.assertFalse(planos.assinatura_stripe_valida(corpo, cab, "whsec_outro", agora=agora))
        self.assertFalse(planos.assinatura_stripe_valida(b'{"id":"evt_2"}', cab, "whsec_x", agora=agora))
        self.assertFalse(planos.assinatura_stripe_valida(corpo, cab, "whsec_x", agora=agora + 301))
        self.assertFalse(planos.assinatura_stripe_valida(corpo, "", "whsec_x", agora=agora))
        self.assertFalse(planos.assinatura_stripe_valida(corpo, "t=abc,v1=00", "whsec_x", agora=agora))
        # várias assinaturas v1 (rotação de segredo): basta uma conferir
        dupla = cab.replace("v1=", "v1=deadbeef,v1=")
        self.assertTrue(planos.assinatura_stripe_valida(corpo, dupla, "whsec_x", agora=agora))

    def test_limites_do_mes_em_nova_york(self):
        self.assertEqual(planos.limites_do_mes("2026-10"), ("2026-10-01 04:00:00", "2026-11-01 04:00:00"))
        self.assertEqual(planos.limites_do_mes("2026-12"), ("2026-12-01 05:00:00", "2027-01-01 05:00:00"))
        self.assertEqual(planos.mes_de(ct("2026-10-31 23:30")), "2026-10")

    def test_formulario_do_stripe(self):
        pares = planos._achatar({"line_items": [{"price_data": {"unit_amount": 9900}, "quantity": 1}],
                                 "metadata": {"empresa_id": "3"}, "x": True})
        self.assertIn(("line_items[0][price_data][unit_amount]", "9900"), pares)
        self.assertIn(("metadata[empresa_id]", "3"), pares)
        self.assertIn(("x", "true"), pares)


# ================================================================ com banco e HTTP

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
        server._login_falhas.clear()
        self.conn = c = server.db()
        self.ea, self.slug_a = empresas.criar_empresa(c, "Belleza Home Services")
        self.eb, self.slug_b = empresas.criar_empresa(c, "Outra Empresa")
        c.execute("UPDATE empresas SET modulos='[\"voz\"]', plano='voz100' WHERE id IN (?,?)", (self.ea, self.eb))
        self.cargo = c.execute("INSERT INTO cargos (nome, empresa_id, voz_ativa) VALUES ('Tech', ?, 1)",
                               (self.ea,)).lastrowid
        self.vaga = c.execute("INSERT INTO vagas (cargo_id, titulo, local, status, empresa_id)"
                              " VALUES (?, 'Tech', '', 'aberta', ?)", (self.cargo, self.ea)).lastrowid
        for login, empresa, admin in (("tony", self.ea, 1), ("carine", self.ea, 0), ("intruso", self.eb, 1)):
            gid = c.execute("INSERT INTO gestores (nome, login, senha, email, is_admin, aprovado, empresa_id, idioma)"
                            " VALUES (?,?,?,?,?,1,?,'pt')", (login.title(), login, "x", login + "@example.com",
                                                             admin, empresa)).lastrowid
            c.execute("INSERT INTO sessoes_gestor (token, gestor_id) VALUES (?,?)", ("sess-" + login, gid))
        c.execute("INSERT INTO sessoes_dono (token) VALUES ('dono-tok')")
        server.config_set(c, "smtp_host", "smtp.teste")
        server.config_set(c, "url_publica", "https://rh.exemplo.com")
        c.commit()
        self.enviados = []
        self._original = server.enviar_email

        def gravar(conn, para, assunto, corpo, anexos=None, html=None, marca=None, idioma="pt"):
            self.enviados.append({"para": para, "assunto": assunto, "corpo": corpo, "idioma": idioma})
            return True, "enviado"

        server.enviar_email = gravar
        self.falso = FalsoElevenLabs()
        voz.GATEWAY_TESTE = self.falso
        planos.STRIPE_TESTE = None

    def tearDown(self):
        server.enviar_email = self._original
        voz.GATEWAY_TESTE = None
        planos.STRIPE_TESTE = None
        self.conn.close()

    def req(self, metodo, caminho, dados=None, gestor=None, dono=False, idioma=None, cab=None, bruto=None):
        h = {"Content-Type": "application/json"}
        if gestor:
            h["X-Gestor-Token"] = gestor if gestor.startswith("sess-") or len(gestor) > 20 else "sess-" + gestor
        if dono:
            h["X-Dono-Token"] = "dono-tok"
        if idioma:
            h["X-Idioma"] = idioma
        h.update(cab or {})
        corpo = bruto if bruto is not None else (json.dumps(dados).encode() if dados is not None else None)
        r = urllib.request.Request(self.base + caminho, data=corpo, method=metodo, headers=h)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def candidato(self, empresa=None, nome="Maria", telefone="+1 8605550101"):
        c = self.conn
        empresa = empresa or self.ea
        cid = c.execute("INSERT INTO candidatos (token, nome, email, local, telefone, idioma, empresa_id)"
                        " VALUES (?,?,?,?,?,?,?)", ("tk-%s-%f" % (nome, time.time()), nome, nome + "@x.com", "",
                                                    telefone, "es", empresa)).lastrowid
        ca = c.execute("INSERT INTO candidaturas (candidato_id, vaga_id) VALUES (?,?)", (cid, self.vaga)).lastrowid
        c.commit()
        return cid, ca

    def chamada(self, empresa, segundos, quando="2026-10-15 15:00:00", status="concluida"):
        cid, ca = self.candidato(empresa)
        self.conn.execute(
            "INSERT INTO voz_chamadas (candidatura_id, candidato_id, status, iniciada_em, duracao) VALUES (?,?,?,?,?)",
            (ca, cid, status, quando, segundos))
        self.conn.commit()

    def empresa(self, eid):
        return self.conn.execute("SELECT * FROM empresas WHERE id=?", (eid,)).fetchone()


class TestCatalogo(Base):
    def test_padrao_semeado(self):
        cat = planos.catalogo(self.conn)
        self.assertEqual([p["codigo"] for p in cat["planos"]], ["essencial", "voz100", "voz300", "voz1000"])
        ess, v100, v300, v1000 = cat["planos"]
        self.assertEqual((ess["preco_mensal"], ess["minutos_voz"], ess["gestores_max"]), (39, 0, 3))
        self.assertNotIn("voz", ess["modulos"])
        self.assertEqual((v100["preco_mensal"], v100["minutos_voz"], v100["numero_exclusivo"], v100["gestores_max"]),
                         (99, 100, False, 5))
        self.assertEqual((v300["preco_mensal"], v300["minutos_voz"], v300["sms_mes"], v300["destaque"]),
                         (199, 300, 300, True))
        self.assertEqual((v1000["preco_mensal"], v1000["sms_mes"], v1000["gestores_max"]), (449, 1000, None))
        self.assertTrue(all(p["preco_anual"] == p["preco_mensal"] * 10 for p in cat["planos"]))
        self.assertEqual(cat["addons"], {"minuto_extra": 0.30, "numero_extra": 10, "sms_extra": 0.03})
        self.assertEqual(cat["trial"], {"dias": 14, "minutos": 20})
        self.assertEqual(planos.premissas(self.conn)["custo_min_voz"], 0.09)

    def test_api_publica_nos_tres_idiomas(self):
        st, d = self.req("GET", "/api/planos?idioma=en")
        self.assertEqual(st, 200)
        self.assertEqual((d["moeda"], d["trial_dias"], d["trial_minutos"], d["stripe_ativo"]), ("USD", 14, 20, False))
        self.assertEqual(set(d["planos"][0]), {"codigo", "nome", "descricao", "preco_mensal", "preco_anual",
                                               "minutos_voz", "numero_exclusivo", "sms_mes", "gestores_max",
                                               "recursos", "destaque"})
        self.assertEqual(d["planos"][1]["nome"], "Voice 100")
        self.assertIn("Shared caller ID number", d["planos"][1]["recursos"])
        self.assertEqual(d["addons"], {"minuto_extra": 0.30, "numero_extra": 10, "sms_extra": 0.03})
        self.assertEqual(self.req("GET", "/api/planos?idioma=es")[1]["planos"][0]["nome"], "Esencial")
        self.assertEqual(self.req("GET", "/api/planos")[1]["planos"][0]["nome"], "Essencial")
        for lang in ("pt", "en", "es"):
            self.assertFalse(TRACOS.search(json.dumps(self.req("GET", "/api/planos?idioma=" + lang)[1],
                                                      ensure_ascii=False)))

    def test_dono_edita_catalogo(self):
        self.assertEqual(self.req("GET", "/api/dono/planos")[0], 401)
        st, d = self.req("GET", "/api/dono/planos", dono=True)
        self.assertEqual(st, 200)
        cat = d["catalogo"]
        cat["planos"][1]["preco_mensal"] = 109
        cat["planos"][1]["preco_anual"] = ""
        cat["planos"][3]["ativo"] = False
        cat["addons"]["minuto_extra"] = 0.25
        st, d = self.req("POST", "/api/dono/planos/catalogo", {"catalogo": cat}, dono=True)
        self.assertEqual(st, 200, d)
        pub = self.req("GET", "/api/planos?idioma=pt")[1]
        self.assertEqual([p["codigo"] for p in pub["planos"]], ["essencial", "voz100", "voz300"])
        self.assertEqual((pub["planos"][1]["preco_mensal"], pub["planos"][1]["preco_anual"]), (109, 1090))
        self.assertEqual(pub["addons"]["minuto_extra"], 0.25)
        # erros de validação
        ruim = json.loads(json.dumps(cat))
        ruim["planos"][0]["codigo"] = "Com Espaço"
        st, d = self.req("POST", "/api/dono/planos/catalogo", {"catalogo": ruim}, dono=True, idioma="en")
        self.assertEqual((st, d["erro"]), (400, "Invalid plan code"))
        ruim = json.loads(json.dumps(cat))
        ruim["planos"][1]["codigo"] = "essencial"
        self.assertEqual(self.req("POST", "/api/dono/planos/catalogo", {"catalogo": ruim}, dono=True)[1]["erro"],
                         "Códigos de plano repetidos")
        ruim = json.loads(json.dumps(cat))
        ruim["planos"][0]["preco_mensal"] = -5
        self.assertEqual(self.req("POST", "/api/dono/planos/catalogo", {"catalogo": ruim}, dono=True)[0], 400)
        # restaurar o padrão
        self.req("POST", "/api/dono/planos/restaurar", {}, dono=True)
        self.assertEqual(planos.plano(self.conn, "voz100")["preco_mensal"], 99)

    def test_dono_premissas_e_calculo(self):
        st, d = self.req("POST", "/api/dono/planos/premissas", {"premissas": {"valor_hora": 80, "empresas_pagantes": 20}},
                         dono=True)
        self.assertEqual(st, 200, d)
        self.assertEqual(planos.premissas(self.conn)["valor_hora"], 80)
        v100 = [x for x in d["custos"]["planos"] if x["codigo"] == "voz100"][0]
        self.assertAlmostEqual(v100["custo_fixo"], 40.0)
        st, d = self.req("POST", "/api/dono/planos/calcular", {"premissas": {"margem_alvo": 50}}, dono=True)
        self.assertEqual(st, 200)
        self.assertEqual(self.req("POST", "/api/dono/planos/premissas", {"premissas": {"margem_alvo": 100}},
                                  dono=True)[0], 400)


class TestUso(Base):
    def test_minutos_por_mes_e_empresa(self):
        self.chamada(self.ea, 61)                                   # 2 min
        self.chamada(self.ea, 300)                                  # 5 min
        self.chamada(self.ea, 45, status="falhou")                  # falhou mas teve duração: 1 min
        self.chamada(self.ea, 0)                                    # sem duração: não conta
        self.chamada(self.ea, None)
        self.chamada(self.ea, 600, quando="2026-11-01 03:30:00")    # 31/10 23:30 em Nova York: outubro
        self.chamada(self.ea, 600, quando="2026-11-01 04:30:00")    # 01/11 00:30 em Nova York: novembro
        self.chamada(self.ea, 120, quando="2026-09-30 12:00:00")    # setembro
        self.chamada(self.eb, 900)                                  # outra empresa
        self.assertEqual(planos.minutos_usados(self.conn, self.ea, "2026-10"), 18)
        self.assertEqual(planos.minutos_usados(self.conn, self.ea, "2026-11"), 10)
        self.assertEqual(planos.minutos_usados(self.conn, self.ea, "2026-09"), 2)
        self.assertEqual(planos.minutos_usados(self.conn, self.eb, "2026-10"), 15)

    def test_limite_e_status(self):
        self.chamada(self.ea, 79 * 60)
        u = planos.uso(self.conn, self.ea, "2026-10")
        self.assertEqual((u["minutos"], u["limite"], u["status"], u["restantes"]), (79, 100, "ok", 21))
        self.chamada(self.ea, 60)
        self.assertEqual(planos.uso(self.conn, self.ea, "2026-10")["status"], "near")
        self.chamada(self.ea, 20 * 60)
        u = planos.uso(self.conn, self.ea, "2026-10")
        self.assertEqual((u["status"], u["excedente"]), ("over", 0))
        # minutos extras comprados aumentam o limite
        self.conn.execute("UPDATE empresas SET minutos_extra=50 WHERE id=?", (self.ea,))
        u = planos.uso(self.conn, self.ea, "2026-10")
        self.assertEqual((u["limite"], u["status"]), (150, "ok"))
        # teste grátis pelo site: 20 minutos (mais os extras)
        self.conn.execute("UPDATE empresas SET status='teste', trial_fim='2026-11-10', minutos_extra=0 WHERE id=?",
                          (self.ea,))
        self.assertEqual(planos.uso(self.conn, self.ea, "2026-10")["limite"], 20)
        # empresa sem plano do catálogo (contrato antigo): sem limite
        self.conn.execute("UPDATE empresas SET plano='', status='ativa', trial_fim='' WHERE id=?", (self.ea,))
        u = planos.uso(self.conn, self.ea, "2026-10")
        self.assertTrue(u["ilimitado"])
        self.assertEqual(u["status"], "ok")

    def test_painel_do_dono(self):
        self.chamada(self.ea, 50 * 60, quando=planos.limites_do_mes(planos.mes_de())[0])
        self.conn.execute("UPDATE empresas SET plano='voz300', ciclo='anual' WHERE id=?", (self.eb,))
        self.conn.commit()
        st, d = self.req("GET", "/api/dono/planos", dono=True)
        self.assertEqual(st, 200)
        por = {x["id"]: x for x in d["uso"]["empresas"]}
        a, b = por[self.ea], por[self.eb]
        self.assertEqual((a["uso"]["minutos"], a["uso"]["limite"], a["receita"]), (50, 100, 99))
        self.assertAlmostEqual(a["custo_real"], 50 * 0.104, places=2)
        self.assertAlmostEqual(a["margem"], 99 - 5.2, places=2)
        self.assertAlmostEqual(b["receita"], 1990 / 12.0, places=2)
        self.assertAlmostEqual(b["custo_real"], 1.15 + 15, places=2)   # número exclusivo e A2P mesmo sem uso
        self.assertAlmostEqual(d["uso"]["totais"]["mrr"], 99 + 1990 / 12.0, places=1)
        self.assertEqual(d["uso"]["totais"]["custo_fixo"], 600)
        self.assertIn("planos", d["custos"])

    def test_dono_ajusta_empresa(self):
        st, d = self.req("POST", "/api/dono/planos/empresa/%d" % self.ea,
                         {"plano": "voz300", "minutos_extra": 25, "excedente_permitido": True, "aplicar_modulos": True},
                         dono=True)
        self.assertEqual(st, 200, d)
        e = self.empresa(self.ea)
        self.assertEqual((e["plano"], e["minutos_extra"], e["excedente_permitido"]), ("voz300", 25, 1))
        self.assertIn("voz", json.loads(e["modulos"]))
        self.assertEqual(d["uso"]["limite"], 325)
        self.assertEqual(self.req("POST", "/api/dono/planos/empresa/%d" % self.ea, {"plano": "nada"}, dono=True)[0], 400)
        self.assertEqual(self.req("POST", "/api/dono/planos/empresa/9999", {}, dono=True)[0], 404)


class TestVozNoLimite(Base):
    TERCA_10H = ct("2026-10-27 10:00")

    def preparar(self, usados):
        # chamadas antigas do mês corrente (Nova York) somando `usados` minutos
        inicio = planos.limites_do_mes(planos.mes_de())[0]
        if usados:
            self.chamada(self.ea, usados * 60, quando=inicio)
        cid, ca = self.candidato(nome="Novo")
        self.conn.execute("UPDATE candidaturas SET voz_status='para_ligar' WHERE id=?", (ca,))
        self.conn.commit()
        return ca

    def test_fila_bloqueada_no_limite(self):
        self.preparar(100)
        self.assertTrue(planos.voz_bloqueada(self.conn, self.ea))
        r = voz.tick(self.conn, self.TERCA_10H, empresa_id=self.ea)
        self.assertEqual((r["iniciadas"], self.falso.ligacoes), (0, []))

    def test_fila_liga_abaixo_do_limite(self):
        self.preparar(99)
        self.assertFalse(planos.voz_bloqueada(self.conn, self.ea))
        r = voz.tick(self.conn, self.TERCA_10H, empresa_id=self.ea)
        self.assertEqual(r["iniciadas"], 1)

    def test_ligacao_manual_bloqueada_com_codigo(self):
        ca = self.preparar(120)
        st, d = self.req("POST", "/api/gestor/voz/candidatura/%d/ligar" % ca, {}, gestor="tony")
        self.assertEqual((st, d["codigo"]), (409, "plan_limit"))
        st, d = self.req("POST", "/api/gestor/voz/candidatura/%d/ligar" % ca, {}, gestor="tony", idioma="en")
        self.assertEqual(d["erro"], "Your plan's voice minutes for this month are used up")
        self.assertEqual(self.falso.ligacoes, [])

    def test_excedente_liberado(self):
        ca = self.preparar(150)
        self.conn.execute("UPDATE empresas SET excedente_permitido=1 WHERE id=?", (self.ea,))
        self.conn.commit()
        self.assertFalse(planos.voz_bloqueada(self.conn, self.ea))
        st, d = self.req("POST", "/api/gestor/voz/candidatura/%d/ligar" % ca, {}, gestor="tony")
        self.assertEqual(st, 200, d)
        u = planos.uso(self.conn, self.ea)
        self.assertEqual((u["status"], u["excedente"]), ("over", 50))
        receita = planos.receita_mensal(planos.catalogo(self.conn), self.empresa(self.ea), u)
        self.assertAlmostEqual(receita, 99 + 50 * 0.30, places=2)

    def test_teste_gratis_nunca_tem_excedente(self):
        self.preparar(20)
        self.conn.execute("UPDATE empresas SET status='teste', trial_fim='2026-12-31', excedente_permitido=1"
                          " WHERE id=?", (self.ea,))
        self.conn.commit()
        self.assertTrue(planos.voz_bloqueada(self.conn, self.ea))

    def test_sem_plano_nao_bloqueia(self):
        self.preparar(5000)
        self.conn.execute("UPDATE empresas SET plano='' WHERE id=?", (self.ea,))
        self.conn.commit()
        self.assertFalse(planos.voz_bloqueada(self.conn, self.ea))

    def test_limite_de_uma_empresa_nao_afeta_outra(self):
        self.preparar(100)
        self.assertTrue(planos.voz_bloqueada(self.conn, self.ea))
        self.assertFalse(planos.voz_bloqueada(self.conn, self.eb))


class TestAssinatura(Base):
    DADOS = {"empresa": "Clean Pros LLC", "nome": "Ana Smith", "email": "Ana@CleanPros.com", "senha": "senha-forte-1",
             "telefone": "+1 860 555 0199", "plano": "voz300", "ciclo": "mensal", "idioma": "en",
             "aceite_termos": True}

    def setUp(self):
        super().setUp()
        server.config_set(self.conn, "assinatura_publica", "1")  # o dono abriu o cadastro
        self.conn.commit()

    def test_cadastro_fechado_por_padrao(self):
        server.config_set(self.conn, "assinatura_publica", "")
        self.conn.commit()
        st, d = self.req("POST", "/api/assinar", self.DADOS)
        self.assertEqual(st, 403)
        st, d = self.req("GET", "/api/planos?idioma=en")
        self.assertIs(d["assinatura_aberta"], False)

    def test_cria_empresa_admin_e_sessao(self):
        server.config_set(self.conn, "dono_email", "dono@example.com")
        self.conn.commit()
        st, d = self.req("POST", "/api/assinar", self.DADOS)
        self.assertEqual(st, 200, d)
        for chave in ("token", "nome", "login", "local", "modulos", "admin", "idioma", "empresa"):
            self.assertIn(chave, d)
        self.assertEqual((d["login"], d["admin"], d["idioma"], d["empresa"]["nome"]),
                         ("ana@cleanpros.com", True, "en", "Clean Pros LLC"))
        self.assertNotIn("checkout_url", d)
        e = self.conn.execute("SELECT * FROM empresas WHERE slug=?", (d["empresa"]["slug"],)).fetchone()
        self.assertEqual((e["status"], e["plano"], e["ciclo"]), ("teste", "voz300", "mensal"))
        self.assertEqual(e["trial_fim"], (planos.hoje_ny() + timedelta(days=14)).isoformat())
        self.assertIn("voz", json.loads(e["modulos"]))
        self.assertEqual(e["contato_telefone"], "+1 860 555 0199")
        g = self.conn.execute("SELECT * FROM gestores WHERE login='ana@cleanpros.com'").fetchone()
        self.assertEqual((g["is_admin"], g["aprovado"], g["empresa_id"], g["idioma"]), (1, 1, e["id"], "en"))
        self.assertTrue(server.senha_confere("senha-forte-1", g["senha"]))
        # a sessão devolvida já funciona no painel do gestor
        st, info = self.req("GET", "/api/gestor/plano", gestor=d["token"], idioma="en")
        self.assertEqual(st, 200, info)
        self.assertEqual((info["plano"]["nome"], info["em_teste"], info["dias_teste"], info["uso"]["limite"]),
                         ("Voice 300", True, 14, 20))
        self.assertEqual(info["upgrade_url"], "/assinar?plano=voz1000&e=" + e["slug"])
        # e-mails: boas-vindas em inglês ao admin e aviso ao dono
        boas = [m for m in self.enviados if m["para"] == "ana@cleanpros.com"]
        self.assertEqual(len(boas), 1)
        self.assertEqual((boas[0]["assunto"], boas[0]["idioma"]), ("Welcome to Bússola", "en"))
        self.assertIn("https://rh.exemplo.com/gestor", boas[0]["corpo"])
        dono = [m for m in self.enviados if m["para"] == "dono@example.com"]
        self.assertEqual((dono[0]["assunto"], dono[0]["idioma"]), ("Nova assinatura: Clean Pros LLC (voz300)", "pt"))
        self.assertFalse(any(TRACOS.search(m["corpo"] + m["assunto"]) for m in self.enviados))

    def test_aviso_ao_dono_no_idioma_escolhido(self):
        server.config_set(self.conn, "dono_email", "dono@example.com")
        server.config_set(self.conn, "dono_idioma", "es")
        self.conn.commit()
        st, d = self.req("POST", "/api/assinar", self.DADOS)
        self.assertEqual(st, 200, d)
        dono = [m for m in self.enviados if m["para"] == "dono@example.com"]
        self.assertEqual(len(dono), 1)
        self.assertEqual((dono[0]["assunto"], dono[0]["idioma"]), ("Nueva suscripción: Clean Pros LLC (voz300)", "es"))
        self.assertIn("Prueba hasta:", dono[0]["corpo"])
        self.assertIn("https://rh.exemplo.com/dono", dono[0]["corpo"])
        self.assertIsNone(TRACOS.search(dono[0]["corpo"] + dono[0]["assunto"]))

    def test_validacoes(self):
        casos = (
            ({"empresa": ""}, "Enter the company name"),
            ({"nome": " "}, "Enter your name"),
            ({"email": "sem-arroba"}, "Invalid email"),
            ({"senha": "curta"}, "Password must be at least 8 characters"),
            ({"plano": "ouro"}, "Invalid plan"),
            ({"ciclo": "semanal"}, "Invalid billing cycle"),
            ({"aceite_termos": False}, "Accept the terms of use to continue"),
        )
        for extra, msg in casos:
            st, d = self.req("POST", "/api/assinar", dict(self.DADOS, **extra))
            self.assertEqual((st, d["erro"]), (400, msg))
        st, d = self.req("POST", "/api/assinar", dict(self.DADOS, aceite_termos=False, idioma="es"))
        self.assertEqual(d["erro"], "Acepta los términos de uso para continuar")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0], 2)

    def test_email_repetido(self):
        server._login_falhas.clear()
        self.assertEqual(self.req("POST", "/api/assinar", self.DADOS)[0], 200)
        st, d = self.req("POST", "/api/assinar", dict(self.DADOS, empresa="Outra"), idioma="pt")
        self.assertEqual((st, d["erro"]), (400, "Este e-mail já tem uma conta. Entre pelo painel do gestor."))

    def test_limite_por_ip(self):
        for i in range(8):
            st, _ = self.req("POST", "/api/assinar", dict(self.DADOS, email="x%d@example.com" % i, senha="1"))
            self.assertEqual(st, 400)
        st, d = self.req("POST", "/api/assinar", dict(self.DADOS, email="ok@example.com"))
        self.assertEqual((st, d["erro"]), (429, "Too many attempts. Wait a few minutes and try again."))
        self.assertIsNone(self.conn.execute("SELECT 1 FROM gestores WHERE login='ok@example.com'").fetchone())

    def test_checkout_do_stripe(self):
        falso = FalsoStripe()
        planos.STRIPE_TESTE = falso
        st, d = self.req("POST", "/api/assinar", dict(self.DADOS, ciclo="anual"))
        self.assertEqual(st, 200, d)
        self.assertEqual(d["checkout_url"], "https://checkout.stripe.com/c/pay/cs_test_1")
        metodo, caminho, p = falso.chamadas[0]
        self.assertEqual((metodo, caminho, p["mode"]), ("POST", "/v1/checkout/sessions", "subscription"))
        item = p["line_items"][0]
        self.assertEqual(item["price_data"]["unit_amount"], 199000)
        self.assertEqual(item["price_data"]["recurring"]["interval"], "year")
        self.assertEqual(p["subscription_data"]["trial_period_days"], 14)
        self.assertEqual(p["customer_email"], "ana@cleanpros.com")
        self.assertEqual(self.req("GET", "/api/planos")[1]["stripe_ativo"], True)
        # preço salvo pelo dono tem prioridade
        server.config_set(self.conn, "stripe_precos", json.dumps({"voz100_mensal": "price_123"}))
        self.conn.commit()
        self.req("POST", "/api/assinar", dict(self.DADOS, email="b@example.com", plano="voz100"))
        self.assertEqual(falso.chamadas[-1][2]["line_items"][0], {"price": "price_123", "quantity": 1})


class TestStripeWebhook(Base):
    SEGREDO = "whsec_teste"

    def setUp(self):
        super().setUp()
        server.config_set(self.conn, "stripe_webhook_secret", self.SEGREDO)
        self.conn.execute("UPDATE empresas SET status='teste', trial_fim='2026-11-01' WHERE id=?", (self.ea,))
        self.conn.commit()

    def enviar(self, evento, segredo=None, t=None):
        corpo = json.dumps(evento).encode()
        return self.req("POST", "/api/stripe/webhook", bruto=corpo,
                        cab={"Stripe-Signature": assinar_stripe(corpo, segredo or self.SEGREDO, t)})

    def test_assinatura_invalida_ou_antiga(self):
        ev = {"id": "evt_1", "type": "checkout.session.completed",
              "data": {"object": {"client_reference_id": str(self.ea), "customer": "cus_1", "subscription": "sub_1"}}}
        self.assertEqual(self.enviar(ev, segredo="whsec_errado")[0], 400)
        self.assertEqual(self.enviar(ev, t=int(time.time()) - 400)[0], 400)
        st, _ = self.req("POST", "/api/stripe/webhook", bruto=json.dumps(ev).encode())
        self.assertEqual(st, 400)
        self.assertEqual(self.empresa(self.ea)["status"], "teste")

    def test_ativacao_pagamento_falha_e_cancelamento(self):
        ev = {"id": "evt_1", "type": "checkout.session.completed",
              "data": {"object": {"object": "checkout.session", "client_reference_id": str(self.ea),
                                  "customer": "cus_1", "subscription": "sub_1",
                                  "metadata": {"empresa_id": str(self.ea), "plano": "voz300", "ciclo": "anual"}}}}
        st, d = self.enviar(ev)
        self.assertEqual((st, d["acao"]), (200, "ativada"))
        e = self.empresa(self.ea)
        self.assertEqual((e["status"], e["stripe_customer"], e["stripe_subscription"], e["plano"], e["ciclo"]),
                         ("ativa", "cus_1", "sub_1", "voz300", "anual"))
        self.assertEqual(self.enviar(ev)[1]["acao"], "repetido")
        fim = int(datetime(2027, 10, 27, 16, tzinfo=timezone.utc).timestamp())
        st, d = self.enviar({"id": "evt_2", "type": "invoice.paid", "data": {"object": {
            "object": "invoice", "customer": "cus_1", "subscription": "sub_1",
            "lines": {"data": [{"period": {"end": fim}}]}}}})
        self.assertEqual(d["acao"], "estendida")
        self.assertEqual(self.empresa(self.ea)["pago_ate"], "2027-10-27")
        server.config_set(self.conn, "dono_email", "dono@example.com")
        server.config_set(self.conn, "dono_idioma", "en")
        self.conn.commit()
        self.enviar({"id": "evt_3", "type": "invoice.payment_failed",
                     "data": {"object": {"object": "invoice", "customer": "cus_1", "subscription": "sub_1"}}})
        self.assertEqual(self.empresa(self.ea)["pagamento_status"], "falhou")
        recusado = [m for m in self.enviados if m["para"] == "dono@example.com"]
        self.assertEqual((recusado[-1]["assunto"], recusado[-1]["idioma"]),
                         ("Payment declined: Belleza Home Services", "en"))
        self.assertIn("Stripe declined the payment", recusado[-1]["corpo"])
        self.enviar({"id": "evt_4", "type": "customer.subscription.deleted",
                     "data": {"object": {"object": "subscription", "id": "sub_1", "customer": "cus_1"}}})
        e = self.empresa(self.ea)
        self.assertEqual(e["status"], "ativa")                       # ainda na tolerância
        self.assertTrue(e["suspender_em"])
        planos.verificar_trials(self.conn, hoje=date.fromisoformat(e["suspender_em"]))
        self.assertEqual(self.empresa(self.ea)["status"], "suspensa")
        # evento de empresa desconhecida é aceito e ignorado
        st, d = self.enviar({"id": "evt_5", "type": "invoice.paid", "data": {"object": {"customer": "cus_x"}}})
        self.assertEqual((st, d["acao"]), (200, "ignorado"))

    def test_portal_de_cobranca(self):
        planos.STRIPE_TESTE = FalsoStripe()
        st, d = self.req("GET", "/api/gestor/plano/portal", gestor="tony")
        self.assertEqual((st, d["erro"]), (400, "Esta empresa ainda não tem assinatura no Stripe"))
        self.conn.execute("UPDATE empresas SET stripe_customer='cus_1' WHERE id=?", (self.ea,))
        self.conn.commit()
        st, d = self.req("GET", "/api/gestor/plano/portal", gestor="tony")
        self.assertEqual((st, d["url"]), (200, "https://billing.stripe.com/p/session/abc"))
        self.assertEqual(self.req("GET", "/api/gestor/plano/portal", gestor="carine")[0], 403)
        planos.STRIPE_TESTE = None
        self.assertEqual(self.req("GET", "/api/gestor/plano/portal", gestor="tony")[1]["erro"], "Stripe não configurado")

    def test_dono_salva_chaves_sem_expor(self):
        st, d = self.req("POST", "/api/dono/planos/stripe", {"stripe_secret_key": "sk_test_abcd1234",
                                                             "precos": {"voz100_mensal": "price_1"},
                                                             "dono_email": "tony@example.com"}, dono=True)
        self.assertEqual(st, 200, d)
        st, d = self.req("GET", "/api/dono/planos/stripe", dono=True)
        self.assertEqual((d["configurado"], d["chave_final"], d["modo_teste"]), (True, "1234", True))
        self.assertNotIn("sk_test_abcd1234", json.dumps(d))
        self.assertTrue(d["webhook_url"].endswith("/api/stripe/webhook"))
        self.assertEqual(self.req("POST", "/api/dono/planos/stripe", {"dono_email": "ruim"}, dono=True)[0], 400)
        # idioma dos e-mails ao dono (padrão pt)
        self.assertEqual(d["dono_idioma"], "pt")
        st, d = self.req("POST", "/api/dono/planos/stripe", {"dono_idioma": "en"}, dono=True)
        self.assertEqual((st, d["stripe"]["dono_idioma"]), (200, "en"))
        self.assertEqual(self.req("GET", "/api/dono/planos/stripe", dono=True)[1]["dono_idioma"], "en")
        self.assertEqual(server.config_get(self.conn, "dono_idioma"), "en")
        self.assertEqual(self.req("POST", "/api/dono/planos/stripe", {"dono_idioma": "fr"}, dono=True)[0], 400)
        self.assertEqual(self.req("GET", "/api/dono/planos/stripe", dono=True)[1]["dono_idioma"], "en")


class TestFimDoTeste(Base):
    def setUp(self):
        super().setUp()
        self.conn.execute("UPDATE empresas SET status='teste', trial_fim='2026-11-10', plano='voz300' WHERE id=?",
                          (self.ea,))
        self.conn.commit()

    def test_avisos_e_suspensao(self):
        r = planos.verificar_trials(self.conn, hoje=date(2026, 11, 5))
        self.assertEqual(r, {"avisos": 0, "suspensas": 0})
        planos.verificar_trials(self.conn, hoje=date(2026, 11, 7))          # 3 dias antes
        avisos = [m for m in self.enviados if m["para"] == "tony@example.com"]
        self.assertEqual(len(avisos), 1)
        self.assertIn("3", avisos[0]["assunto"])
        self.assertIn("/assinar?plano=voz300&e=" + self.slug_a, avisos[0]["corpo"])
        self.assertFalse([m for m in self.enviados if m["para"] == "carine@example.com"])  # só administradores
        planos.verificar_trials(self.conn, hoje=date(2026, 11, 8))          # não repete
        self.assertEqual(len([m for m in self.enviados if m["para"] == "tony@example.com"]), 1)
        planos.verificar_trials(self.conn, hoje=date(2026, 11, 9))          # 1 dia antes
        self.assertEqual(len([m for m in self.enviados if m["para"] == "tony@example.com"]), 2)
        planos.verificar_trials(self.conn, hoje=date(2026, 11, 13))         # fim + 3: ainda na tolerância
        self.assertEqual(self.empresa(self.ea)["status"], "teste")
        self.assertEqual(self.req("GET", "/api/gestor/plano", gestor="tony")[0], 200)
        r = planos.verificar_trials(self.conn, hoje=date(2026, 11, 14))
        self.assertEqual(r["suspensas"], 1)
        self.assertEqual(self.empresa(self.ea)["status"], "suspensa")
        self.assertEqual(self.req("GET", "/api/gestor/plano", gestor="tony")[0], 401)   # sessões derrubadas
        self.assertEqual(self.empresa(self.eb)["status"], "ativa")
        self.assertTrue([m for m in self.enviados if "terminou" in m["assunto"]])

    def test_teste_pago_nao_suspende(self):
        self.conn.execute("UPDATE empresas SET stripe_subscription='sub_1' WHERE id=?", (self.ea,))
        self.conn.commit()
        planos.verificar_trials(self.conn, hoje=date(2026, 12, 31))
        self.assertEqual(self.empresa(self.ea)["status"], "teste")

    def test_rota_do_dono(self):
        st, d = self.req("POST", "/api/dono/planos/rotina", {}, dono=True)
        self.assertEqual(st, 200)
        self.assertIn("suspensas", d["resultado"])


class TestIsolamento(Base):
    def test_gestor_ve_so_a_propria_empresa(self):
        inicio = planos.limites_do_mes(planos.mes_de())[0]
        self.chamada(self.ea, 30 * 60, quando=inicio)
        self.chamada(self.eb, 90 * 60, quando=inicio)
        a = self.req("GET", "/api/gestor/plano", gestor="tony")[1]
        b = self.req("GET", "/api/gestor/plano", gestor="intruso")[1]
        self.assertEqual((a["uso"]["minutos"], b["uso"]["minutos"]), (30, 90))
        self.assertEqual(b["uso"]["status"], "near")
        # gestor comum vê o uso, mas não o link de upgrade nem o portal
        c = self.req("GET", "/api/gestor/plano", gestor="carine")[1]
        self.assertEqual((c["admin"], c["upgrade_url"], c["portal_disponivel"]), (False, "", False))
        self.assertEqual(self.req("POST", "/api/gestor/plano/checkout", {"plano": "voz300"}, gestor="carine")[0], 403)
        self.assertEqual(self.req("GET", "/api/gestor/plano")[0], 401)
        self.assertEqual(self.req("GET", "/api/dono/planos", gestor="tony")[0], 401)
        self.assertEqual(self.req("POST", "/api/dono/planos/empresa/%d" % self.eb, {"plano": ""}, gestor="intruso")[0],
                         401)

    def test_checkout_de_upgrade_e_da_propria_empresa(self):
        falso = FalsoStripe()
        planos.STRIPE_TESTE = falso
        st, d = self.req("POST", "/api/gestor/plano/checkout", {"plano": "voz1000", "ciclo": "mensal"}, gestor="intruso")
        self.assertEqual(st, 200, d)
        p = falso.chamadas[-1][2]
        self.assertEqual((p["client_reference_id"], p["metadata"]["plano"]), (str(self.eb), "voz1000"))


class TestLimitesDoPlano(Base):
    """gestores_max e vagas_ativas_max do plano: contagem, 403 com mensagem, extras do dono."""

    def limitar_vagas(self, codigo, maximo):
        cat = planos.catalogo(self.conn)
        for p in cat["planos"]:
            if p["codigo"] == codigo:
                p["vagas_ativas_max"] = maximo
        server.config_set(self.conn, "planos_catalogo", json.dumps(cat))
        self.conn.commit()

    def novo_gestor(self, login, quem="tony", idioma=None):
        return self.req("POST", "/api/gestor/gestores", {"nome": login.title(), "login": login, "senha": "segredo123"},
                        gestor=quem, idioma=idioma)

    def salvar_vaga(self, status="aberta", vid=None, quem="tony", idioma=None):
        d = {"titulo": "Vaga", "cargo_id": self.cargo, "status": status}
        if vid:
            d["id"] = vid
        return self.req("POST", "/api/gestor/vaga", d, gestor=quem, idioma=idioma)

    def test_contagem_e_empresa_sem_plano(self):
        self.assertEqual(planos.limite_gestores(self.conn, self.ea), (True, 2, 5))   # voz100: até 5
        self.conn.execute("INSERT INTO gestores (nome, login, senha, aprovado, empresa_id) VALUES ('P','pend','x',0,?)",
                          (self.ea,))
        self.assertEqual(planos.limite_gestores(self.conn, self.ea), (True, 2, 5))   # pendente não conta
        self.assertEqual(planos.limite_vagas(self.conn, self.ea), (True, 1, None))  # catálogo padrão: sem limite
        for codigo in ("", "contrato_antigo"):
            self.conn.execute("UPDATE empresas SET plano=? WHERE id=?", (codigo, self.ea))
            self.assertEqual(planos.limite_gestores(self.conn, self.ea), (True, 2, None))
            self.assertEqual(planos.limite_vagas(self.conn, self.ea), (True, 1, None))
        self.conn.commit()
        for i in range(6):
            self.assertEqual(self.novo_gestor("livre%d" % i)[0], 200)
        self.limitar_vagas("voz100", 1)
        self.assertEqual(self.salvar_vaga()[0], 200)   # sem plano do catálogo: nada é limitado

    def test_admin_cria_gestor_ate_o_limite(self):
        for i in range(3):
            st, d = self.novo_gestor("g%d" % i)
            self.assertEqual(st, 200, d)
        st, d = self.novo_gestor("g3")
        self.assertEqual(st, 403)
        self.assertIn("Voz 100", d["erro"])
        self.assertIn("5 gestores", d["erro"])
        self.assertIn("upgrade", d["erro"])
        self.assertIsNone(self.conn.execute("SELECT 1 FROM gestores WHERE login='g3'").fetchone())
        st, d = self.novo_gestor("g3", idioma="en")
        self.assertEqual(st, 403)
        self.assertEqual(d["erro"], "The Voice 100 plan allows up to 5 active managers. Upgrade your plan to add more managers.")
        st, d = self.novo_gestor("g3", idioma="es")
        self.assertIn("plan Voz 100 permite hasta 5 gerentes activos", d["erro"])
        self.assertIsNone(TRACOS.search(d["erro"]))
        # editar um gestor existente continua liberado no limite
        gid = self.conn.execute("SELECT id FROM gestores WHERE login='g0'").fetchone()[0]
        st, d = self.req("POST", "/api/gestor/gestores", {"id": gid, "nome": "G Zero"}, gestor="tony")
        self.assertEqual(st, 200, d)
        # a outra empresa (mesmo plano, 1 gestor) não é afetada
        self.assertEqual(self.novo_gestor("outro", quem="intruso")[0], 200)

    def test_aprovacao_de_solicitacao_respeita_o_limite(self):
        for i in range(3):
            self.assertEqual(self.novo_gestor("g%d" % i)[0], 200)
        st, d = self.req("POST", "/api/gestor/solicitar-acesso",
                         {"empresa": self.slug_a, "nome": "Pedro", "login": "pedro", "email": "p@x.com", "senha": "segredo1"})
        self.assertEqual(st, 200, d)  # a solicitação fica pendente e não conta
        pid = self.conn.execute("SELECT id FROM gestores WHERE login='pedro'").fetchone()[0]
        st, d = self.req("POST", "/api/gestor/gestores/%d/aprovar" % pid, {}, gestor="tony")
        self.assertEqual(st, 403)
        self.assertIn("Voz 100", d["erro"])
        self.assertEqual(self.conn.execute("SELECT aprovado FROM gestores WHERE id=?", (pid,)).fetchone()[0], 0)
        # o dono libera um gestor extra
        st, d = self.req("POST", "/api/dono/planos/empresa/%d" % self.ea, {"gestores_extra": 1}, dono=True)
        self.assertEqual(st, 200, d)
        self.assertEqual(d["gestores"], {"permitido": True, "usados": 5, "maximo": 6})
        self.assertEqual(self.req("POST", "/api/gestor/gestores/%d/aprovar" % pid, {}, gestor="tony")[0], 200)
        # aprovar de novo quem já está aprovado não esbarra no limite
        self.assertEqual(self.req("POST", "/api/gestor/gestores/%d/aprovar" % pid, {}, gestor="tony")[0], 200)

    def test_dono_cria_gestor_e_troca_o_plano(self):
        for i in range(3):
            self.assertEqual(self.novo_gestor("g%d" % i)[0], 200)
        novo = {"nome": "Ana", "login": "ana", "senha": "segredo123"}
        st, d = self.req("POST", "/api/dono/empresa/%d/gestor" % self.ea, novo, dono=True)
        self.assertEqual(st, 403)
        self.assertIn("Voz 100", d["erro"])
        st, d = self.req("POST", "/api/dono/planos/empresa/%d" % self.ea, {"plano": "voz1000"}, dono=True)
        self.assertEqual(st, 200, d)
        self.assertEqual(d["gestores"]["maximo"], None)
        self.assertEqual(self.req("POST", "/api/dono/empresa/%d/gestor" % self.ea, novo, dono=True)[0], 200)
        # empresa nova criada pelo dono sempre recebe o primeiro administrador
        st, d = self.req("POST", "/api/dono/empresas",
                         {"nome": "Nova", "admin": {"nome": "Adm", "login": "adm", "senha": "segredo123"}}, dono=True)
        self.assertEqual(st, 200, d)

    def test_vagas_ativas(self):
        self.limitar_vagas("voz100", 2)
        self.assertEqual(planos.limite_vagas(self.conn, self.ea), (True, 1, 2))
        self.assertEqual(self.salvar_vaga()[0], 200)
        st, d = self.salvar_vaga()
        self.assertEqual(st, 403)
        self.assertIn("Voz 100", d["erro"])
        self.assertIn("2 vagas ativas", d["erro"])
        st, d = self.salvar_vaga(idioma="en")
        self.assertEqual(d["erro"], "The Voice 100 plan allows up to 2 active jobs. "
                                    "Upgrade your plan or close a job to open another one.")
        # pausada pode ser criada; reabrir no limite é recusado
        st, d = self.salvar_vaga("pausada")
        self.assertEqual(st, 200, d)
        pausada = self.conn.execute("SELECT id FROM vagas WHERE status='pausada'").fetchone()[0]
        self.assertEqual(self.salvar_vaga("aberta", pausada)[0], 403)
        self.assertEqual(self.conn.execute("SELECT status FROM vagas WHERE id=?", (pausada,)).fetchone()[0], "pausada")
        # editar uma vaga que já está aberta continua liberado
        self.assertEqual(self.salvar_vaga("aberta", self.vaga_id_aberta())[0], 200)
        # encerrar uma libera a vaga
        self.assertEqual(self.salvar_vaga("encerrada", self.vaga_id_aberta())[0], 200)
        self.assertEqual(self.salvar_vaga("aberta", pausada)[0], 200)
        self.assertEqual(self.salvar_vaga()[0], 403)
        # o dono libera vagas extras
        st, d = self.req("POST", "/api/dono/planos/empresa/%d" % self.ea, {"vagas_extra": 1}, dono=True)
        self.assertEqual(d["vagas"], {"permitido": True, "usados": 2, "maximo": 3})
        self.assertEqual(self.salvar_vaga()[0], 200)
        self.assertEqual(self.req("POST", "/api/dono/planos/empresa/%d" % self.ea, {"vagas_extra": "x"},
                                  dono=True)[0], 400)

    def vaga_id_aberta(self):
        return self.conn.execute("SELECT id FROM vagas WHERE empresa_id=? AND status='aberta' ORDER BY id LIMIT 1",
                                 (self.ea,)).fetchone()[0]

    def test_cartao_do_plano_mostra_os_limites(self):
        self.limitar_vagas("voz100", 4)
        d = self.req("GET", "/api/gestor/plano", gestor="carine")[1]
        self.assertEqual(d["gestores"], {"permitido": True, "usados": 2, "maximo": 5})
        self.assertEqual(d["vagas"], {"permitido": True, "usados": 1, "maximo": 4})
        self.conn.execute("UPDATE empresas SET plano='' WHERE id=?", (self.ea,))
        self.conn.commit()
        d = self.req("GET", "/api/gestor/plano", gestor="carine")[1]
        self.assertEqual((d["gestores"]["maximo"], d["vagas"]["maximo"]), (None, None))
        with open(os.path.join(AQUI, "public", "js", "gestor-plano.js"), encoding="utf-8") as f:
            js = f.read()
        for chave in ("gestores_uso", "vagas_uso"):
            self.assertEqual(js.count(chave + ":"), 3, chave)   # pt, en e es


class TestArquivos(unittest.TestCase):
    def test_sem_travessoes(self):
        for arq in ("planos.py", "indicacoes.py", "teste_planos.py", "public/js/gestor-plano.js", "public/js/dono.js",
                    "public/js/i18n-dono.js", "erros_i18n.py"):
            caminho = os.path.join(AQUI, arq)
            if os.path.exists(caminho):
                with open(caminho, encoding="utf-8") as f:
                    self.assertIsNone(TRACOS.search(f.read()), arq)

    def test_gestor_html_carrega_o_script(self):
        with open(os.path.join(AQUI, "public", "gestor.html"), encoding="utf-8") as f:
            self.assertIn("js/gestor-plano.js", f.read())


if __name__ == "__main__":
    unittest.main(verbosity=1)
