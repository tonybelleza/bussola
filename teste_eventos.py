"""Testes da tradução da linha do tempo (eventos_i18n.py).

A varredura lê o código (ast) e acha todo texto literal passado a
registrar_evento, inclusive em chamadas de várias linhas, expressões
condicionais, % e f-strings, e textos montados numa variável antes da chamada.
Cada literal precisa aparecer em algum EXEMPLO traduzido para en e es: um
evento novo sem tradução faz este teste falhar.
"""

import ast
import os
import re
import sqlite3
import sys
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import eventos_i18n  # noqa: E402
from eventos_i18n import traduzir_evento, traduzir_lista  # noqa: E402

TRACOS = re.compile("[\u2013\u2014]")

# um exemplo real (valores preenchidos) de cada evento gravado pelo sistema
EXEMPLOS = [
    # server.py
    "Avaliação completa",
    "Resultados enviados ao candidato (en)",
    "Dados pessoais anonimizados (LGPD)",
    "Currículo analisado automaticamente por IA (aderência 82%)",
    "Lembrete de avaliação incompleta enviado",
    "Nova inscrição na vaga: Operador de Empilhadeira",
    "Link de acesso reenviado (cadastro duplicado)",
    "Cadastro de colaborador interno (Hartford)",
    "Cadastro realizado (Hartford)",
    "Inscrição na vaga: Operador de Empilhadeira",
    "E-mail de confirmação enviado ao candidato",
    "Link de acesso reenviado a pedido",
    "Teste DISC concluído",
    "Teste B.A.S.E. concluído",
    "Teste de conhecimento concluído: 7 de 10 acertos",
    "Autoavaliação de competências respondida",
    "Currículo enviado",
    "Vaga Operador de Empilhadeira: movido para Entrevista",
    "Vaga Operador de Empilhadeira: movido para Reprovado (Sem experiência com CNC)",
    "E-mail de atualização enviado",
    "Falha ao enviar e-mail: SMTP não configurado",
    "Adicionado à vaga: Operador de Empilhadeira",
    "Entrevista registrada: média 4.2 de 5",
    "Currículo analisado por IA (aderência 75%)",
    "E-mail enviado pelo gestor: Próximos passos",
    # agenda.py
    "Entrevista marcada pelo candidato: terça-feira, 5 de março de 2026, às 14:00 · EST",
    "Entrevista remarcada pelo candidato: sexta-feira, 6 de março de 2026, às 09:30 · EST",
    "Entrevista cancelada (pelo candidato): terça-feira, 5 de março de 2026, às 14:00 · EST",
    "Entrevista cancelada (Carine Souza): terça-feira, 5 de março de 2026, às 14:00 · EST",
    "Entrevista realizada",
    "Entrevista marcada como falta (não compareceu)",
    "Entrevista marcada: e-mail ao candidato e a 2 gestor(es)",
    "Entrevista remarcada: e-mail ao candidato não enviado e a 1 gestor(es)",
    "Entrevista cancelada: e-mail ao candidato e a 0 gestor(es)",
    "Link de agendamento de entrevista enviado (es)",
    "Lembrete de entrevista enviado",
    "Google Agenda: evento criado",
    "Google Agenda: evento criado com link do Google Meet",
    "Google Agenda: evento atualizado",
    "Google Agenda: evento removido",
    "Google Agenda: não foi possível sincronizar o evento",
    # campanhas.py
    "Avisado por e-mail sobre a vaga: Cleaning Technician (banco de talentos)",
    "Falha ao avisar sobre a vaga: Cleaning Technician (banco de talentos)",
    "Cancelou os e-mails de vagas da empresa",
    # entrada.py
    "Importado (csv)",
    # indicacoes.py
    "Indicado por Ana Lima",
    "Indicado por ?",
    "Indicou um candidato (#42)",
    # mensagens.py
    "Gestores notificados por e-mail (3): testes pendentes",
    "Gestores notificados por e-mail (3): avaliação completa",
    "Gestores notificados por e-mail (2): novo candidato",
    # onboarding.py
    "Proposta e onboarding enviados (W-2, Machine Operator, início 2026-11-03)",
    "Proposta e onboarding enviados (1099, Consultor, Senior, início 2026-11-03)",
    "Vaga Machine Operator: movido para Contratado",
    "E-mail da proposta e do onboarding enviado (en)",
    "E-mail da proposta e do onboarding não enviado (pt)",
    "Onboarding cancelado",
    "Consentimento para documentos eletrônicos aceito",
    "Documento assinado: Employee Handbook",
    "Formulário preenchido e assinado: W-4",
    "Onboarding concluído pelo novo contratado",
    "Onboarding concluído: aviso a 2 gestor(es)",
    "Lembrete de onboarding enviado",
    "I-9 Seção 2 preenchida pelo empregador",
    "Dados sensíveis do onboarding apagados (retenção)",
    # integracoes_rh.py
    "Verificação de antecedentes solicitada (Checkr, pacote tasker_standard)",
    "Verificação de antecedentes (Checkr): convite enviado",
    "Verificação de antecedentes (Checkr): em andamento",
    "Verificação de antecedentes (Checkr): clear (sem apontamentos)",
    "Verificação de antecedentes (Checkr): consider (revisar)",
    "Verificação de antecedentes (Checkr): suspensa",
    "Verificação de antecedentes (Checkr): cancelada",
    "Verificação de antecedentes (Checkr): convite expirado",
    "Verificação de antecedentes concluída: aviso a 2 administrador(es)",
    # talentos.py
    "Lembrete para 2026-12-01: ligar de novo",
    "Lembrete para 2026-12-01",
    "Lembrete removido",
    # conta.py (consentimento para ligações e mensagens automáticas)
    "Autorizou ligações e mensagens automáticas",
    "Pediu para não receber ligações nem mensagens automáticas",
    # voz.py
    "Entrou na fila da triagem por voz",
    "Falha ao iniciar a ligação",
    "Ligação da triagem por voz iniciada (es, tentativa 2)",
    "Triagem por voz: QUALIFIED (STRONG, 87 pontos)",
    "Triagem por voz: sem resposta [no_answer_exhausted]",
    "Triagem por voz: VOICEMAIL",
    "Vaga Warehouse Associate: movido para Avaliações (triagem por voz)",
    "Vaga Warehouse Associate: movido para Reprovado (Número errado (triagem por voz))",
    "Convite para os testes enviado (en)",
    "Falha ao enviar convite: SMTP não configurado",
    "Ligação recebida: o candidato ligou para a Francisca",
    "Cadastro criado pela Francisca (ligação recebida)",
    "Ligou para a empresa (interesse: Cleaning Technician)",
    "Link de inscrição enviado a quem ligou (es)",
    "Falha ao enviar o link de inscrição: SMTP não configurado",
    "Voltou para a fila da triagem por voz",
    "Marcado como Não ligar",
    "Tentativas da triagem por voz zeradas",
    # sms.py
    "SMS enviado: convite para os testes",
    "SMS enviado: lembrete de entrevista",
    "SMS enviado: lembrete do onboarding",
    "SMS enviado: tentamos ligar",
    "SMS enviado: candidatura recebida",
    "SMS enviado: mensagem do gestor",
    "SMS agendado para o horário permitido (8h às 21h)",
    "SMS recebido",
    "Pediu para não receber SMS (STOP)",
    "Voltou a receber SMS (START)",
    "Falha ao enviar SMS: HTTP 500",
]


# ------------------------------------------------------------ varredura (ast)

def _eh_registrar(no):
    f = no.func
    return (isinstance(f, ast.Name) and f.id == "registrar_evento") or (
        isinstance(f, ast.Attribute) and f.attr == "registrar_evento")


def _texto_arg(no):
    if len(no.args) >= 4:
        return no.args[3]
    for kw in no.keywords:
        if kw.arg == "texto":
            return kw.value
    return None


def _literais(expr):
    """Strings literais que formam o texto: segue %, +, condicionais e tuplas;
    ignora chaves de dicionário, comparações e argumentos de chamadas.
    f-strings viram modelo com %s."""
    if isinstance(expr, ast.Constant):
        return [expr.value] if isinstance(expr.value, str) else []
    if isinstance(expr, ast.JoinedStr):
        return ["".join(v.value if isinstance(v, ast.Constant) else "%s" for v in expr.values)]
    if isinstance(expr, ast.BinOp):
        return _literais(expr.left) + _literais(expr.right)
    if isinstance(expr, ast.IfExp):
        return _literais(expr.body) + _literais(expr.orelse)
    if isinstance(expr, (ast.Tuple, ast.List)):
        return [s for e in expr.elts for s in _literais(e)]
    if isinstance(expr, ast.BoolOp):
        return [s for e in expr.values for s in _literais(e)]
    return []


def varrer():
    """{(arquivo, linha): [literais]} de todos os registrar_evento do código."""
    resultado = {}
    for arq in sorted(os.listdir(AQUI)):
        if not arq.endswith(".py") or arq.startswith("teste"):
            continue
        with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
            arvore = ast.parse(f.read(), arq)
        funcoes = [n for n in ast.walk(arvore) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for func in funcoes + [arvore]:
            for no in ast.walk(func):
                if not isinstance(no, ast.Call) or not _eh_registrar(no):
                    continue
                expr = _texto_arg(no)
                if expr is None:
                    continue
                lits = _literais(expr)
                if isinstance(expr, ast.Name) and func is not arvore:
                    # texto montado numa variável antes da chamada (voz.py)
                    for a in ast.walk(func):
                        alvos = a.targets if isinstance(a, ast.Assign) else (
                            [a.target] if isinstance(a, ast.AugAssign) else [])
                        if any(isinstance(t, ast.Name) and t.id == expr.id for t in alvos):
                            lits += _literais(a.value)
                chave = (arq, no.lineno)
                resultado.setdefault(chave, [])
                for s in lits:
                    if s not in resultado[chave]:
                        resultado[chave].append(s)
    return resultado


def _relevante(literal):
    return bool(re.search(r"[A-Za-zÀ-ÿ]{2}", literal))


def _regex_do_literal(literal):
    pedacos = re.split(r"%(?:\.\d+)?[sdif]|%%", literal)
    return re.compile(".*".join(re.escape(p) for p in pedacos), re.S)


class TestVarredura(unittest.TestCase):
    def test_varredura_acha_chamadas(self):
        achados = varrer()
        self.assertGreaterEqual(len(achados), 50)
        arquivos = {a for a, _ in achados}
        for arq in ("server.py", "voz.py", "entrada.py", "agenda.py", "talentos.py", "onboarding.py",
                    "indicacoes.py", "mensagens.py", "campanhas.py"):
            self.assertIn(arq, arquivos)
        todos = [s for lits in achados.values() for s in lits]
        self.assertIn("Triagem por voz: %s", todos)  # variável montada antes da chamada
        self.assertIn("marcada como falta (não compareceu)", todos)  # expressão condicional

    def test_todo_literal_tem_en_e_es(self):
        exemplos_ok = []
        for ex in EXEMPLOS:
            for lang in ("en", "es"):
                self.assertTrue(eventos_i18n.cobre(ex, lang), "%s sem tradução %s" % (ex, lang))
            exemplos_ok.append(ex)
        faltando = []
        for (arq, linha), lits in sorted(varrer().items()):
            for lit in lits:
                if not _relevante(lit):
                    continue
                rx = _regex_do_literal(lit)
                if not any(rx.search(ex) for ex in exemplos_ok):
                    faltando.append("%s:%d %r" % (arq, linha, lit))
        self.assertEqual(faltando, [], "eventos sem tradução (adicione em eventos_i18n.py e um exemplo aqui)")

    def test_exemplos_mudam_em_en(self):
        for ex in EXEMPLOS:
            self.assertNotEqual(traduzir_evento(ex, "en"), ex, ex)


class TestTraducao(unittest.TestCase):
    def test_pt_devolve_original(self):
        for ex in EXEMPLOS:
            self.assertEqual(traduzir_evento(ex, "pt"), ex)
            self.assertEqual(traduzir_evento(ex, ""), ex)
            self.assertEqual(traduzir_evento(ex, None), ex)
            self.assertEqual(traduzir_evento(ex, "fr"), ex)

    def test_desconhecido_passa_igual(self):
        for texto in ("Ask why she left the last job after 2 months", "Ligou de volta às 15h", "", None, 7):
            self.assertEqual(traduzir_evento(texto, "en"), texto)
            self.assertEqual(traduzir_evento(texto, "es"), texto)

    def test_nomes_e_valores_ficam(self):
        casos = [
            ("Inscrição na vaga: Operador de Empilhadeira", "Operador de Empilhadeira"),
            ("Indicado por Ana Lima", "Ana Lima"),
            ("Documento assinado: Employee Handbook", "Employee Handbook"),
            ("E-mail enviado pelo gestor: Próximos passos", "Próximos passos"),
            ("Lembrete para 2026-12-01: ligar de novo", "ligar de novo"),
            ("Proposta e onboarding enviados (1099, Consultor, Senior, início 2026-11-03)", "Consultor, Senior"),
            ("Entrevista cancelada (Carine Souza): terça-feira, 5 de março de 2026, às 14:00 · EST", "Carine Souza"),
            ("Vaga Dev: Backend: movido para Reprovado (Sem experiência com CNC)", "Sem experiência com CNC"),
        ]
        for texto, valor in casos:
            for lang in ("en", "es"):
                self.assertIn(valor, traduzir_evento(texto, lang), (texto, lang))

    def test_exemplos_concretos(self):
        self.assertEqual(traduzir_evento("Currículo enviado", "en"), "Resume uploaded")
        self.assertEqual(traduzir_evento("Vaga Dev: Backend: movido para Reprovado (Sem experiência)", "en"),
                         "Job Dev: Backend: moved to Rejected (Sem experiência)")
        self.assertEqual(traduzir_evento("Vaga X: movido para Avaliações (triagem por voz)", "es"),
                         "Vacante X: movido a Evaluaciones (evaluación por voz)")
        self.assertEqual(traduzir_evento("Triagem por voz: QUALIFIED (STRONG, 87 pontos)", "en"),
                         "Voice screening: QUALIFIED (STRONG, 87 points)")
        self.assertEqual(traduzir_evento("Triagem por voz: sem resposta [no_answer_exhausted]", "es"),
                         "Evaluación por voz: sin respuesta [no_answer_exhausted]")
        self.assertEqual(
            traduzir_evento("Entrevista marcada pelo candidato: terça-feira, 5 de março de 2026, às 14:00 · EST", "en"),
            "Interview booked by the candidate: Tuesday, March 5, 2026 at 2:00 PM · EST")
        self.assertEqual(
            traduzir_evento("Entrevista cancelada (pelo candidato): terça-feira, 5 de março de 2026, às 09:05 · EST", "es"),
            "Entrevista cancelada (por el candidato): martes 5 de marzo de 2026, a las 09:05 · EST")
        self.assertEqual(traduzir_evento("Teste de conhecimento concluído: 7 de 10 acertos", "en"),
                         "Knowledge test completed: 7 of 10 correct")

    def test_lista_traduz_texto_e_autor_sistema(self):
        evs = [{"tipo": "email", "texto": "Currículo enviado", "autor": "sistema"},
               {"tipo": "anotacao", "texto": "Boa candidata", "autor": "Carine"}]
        traduzir_lista(evs, "en")
        self.assertEqual(evs[0], {"tipo": "email", "texto": "Resume uploaded", "autor": "system"})
        self.assertEqual(evs[1]["texto"], "Boa candidata")
        self.assertEqual(evs[1]["autor"], "Carine")
        evs2 = [{"texto": "Currículo enviado", "autor": "sistema"}]
        self.assertEqual(traduzir_lista(evs2, "pt"), [{"texto": "Currículo enviado", "autor": "sistema"}])

    def test_sem_travessoes(self):
        for arq in ("eventos_i18n.py", "teste_eventos.py"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                self.assertIsNone(TRACOS.search(f.read()), arq)
        for ex in EXEMPLOS:
            for lang in ("en", "es"):
                self.assertIsNone(TRACOS.search(traduzir_evento(ex, lang)), ex)


class TestServidor(unittest.TestCase):
    """O banco continua em português; a resposta ao gestor sai traduzida."""

    def test_banco_guarda_portugues(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE eventos (candidato_id INTEGER, tipo TEXT, texto TEXT, autor TEXT)")
        conn.execute("INSERT INTO eventos VALUES (1, 'curriculo', 'Currículo enviado', 'sistema')")
        evs = [dict(r) for r in conn.execute("SELECT tipo, texto, autor FROM eventos")]
        traduzir_lista(evs, "es")
        self.assertEqual(evs[0]["texto"], "Currículum enviado")
        self.assertEqual(conn.execute("SELECT texto FROM eventos").fetchone()[0], "Currículo enviado")

    def test_server_usa_traducao_nas_respostas(self):
        with open(os.path.join(AQUI, "server.py"), encoding="utf-8") as f:
            codigo = f.read()
        self.assertIn("import eventos_i18n", codigo)
        self.assertEqual(codigo.count("eventos_i18n.traduzir_lista("), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
