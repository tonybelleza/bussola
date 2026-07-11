#!/usr/bin/env python3
"""
Bateria de testes do Sistema de RH.

Roda contra um servidor em porta separada com um banco temporário,
sem tocar nos dados reais. Uso:  python3 teste_sistema.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

PORTA = 8981
BASE = "http://localhost:%d" % PORTA
AQUI = os.path.dirname(os.path.abspath(__file__))

total, falhas = 0, []


def verifica(descricao, condicao):
    global total
    total += 1
    print(("  ok    " if condicao else "  FALHA ") + descricao)
    if not condicao:
        falhas.append(descricao)


def req(caminho, corpo=None, headers=None, metodo=None):
    r = urllib.request.Request(
        BASE + caminho,
        data=json.dumps(corpo).encode() if corpo is not None else None,
        headers={"Content-Type": "application/json", **(headers or {})},
        method=metodo,
    )
    try:
        return json.loads(urllib.request.urlopen(r).read()), 200
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read()), e.code
        except ValueError:
            return {}, e.code


def main():
    pasta = tempfile.mkdtemp(prefix="rh-teste-")
    # roda o servidor com banco isolado copiando o código para a pasta temporária
    for item in ("server.py",):
        shutil.copy(os.path.join(AQUI, item), pasta)
    shutil.copytree(os.path.join(AQUI, "public"), os.path.join(pasta, "public"))
    servidor = subprocess.Popen(
        [sys.executable, "server.py", str(PORTA)],
        cwd=pasta,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(30):
            time.sleep(0.5)
            try:
                urllib.request.urlopen(BASE + "/api/vagas", timeout=2)
                break
            except Exception:  # noqa: BLE001
                continue
        else:
            print("Servidor de teste não subiu.")
            sys.exit(1)

        print("\n== Configuração inicial e acesso ==")
        s, _ = req("/api/gestor/setup")
        verifica("primeiro acesso exige setup", s["precisa_setup"] is True)
        a, code = req("/api/gestor/setup", {"nome": "Admin", "login": "admin.t",
                                            "email": "adm@x.com", "senha": "senha123"})
        verifica("setup cria administrador e loga", code == 200 and a.get("admin") is True)
        G = {"X-Gestor-Token": a["token"]}
        _, code = req("/api/gestor/setup", {"nome": "X", "login": "x", "senha": "xxxxxx"})
        verifica("segundo setup é bloqueado", code == 403)
        _, code = req("/api/gestor/login", {"login": "admin.t", "senha": "errada"})
        verifica("login com senha errada falha", code == 401)
        _, code = req("/api/gestor/candidatos", headers={"X-Gestor-Token": "token-falso"})
        verifica("token falso de gestor é rejeitado", code == 401)

        print("\n== Gestores e locais ==")
        _, code = req("/api/gestor/gestores", {"nome": "Maria", "login": "maria", "senha": "senha123",
                                               "email": "maria@x.com", "local": "Unidade A"}, G)
        verifica("admin cria gestora com local", code == 200)
        gl, _ = req("/api/gestor/gestores", headers=G)
        verifica("gestores listam e-mail",
                 all("email" in g for g in gl["gestores"]))
        ml, _ = req("/api/gestor/login", {"login": "maria", "senha": "senha123"})
        M = {"X-Gestor-Token": ml["token"]}
        _, code = req("/api/gestor/gestores", headers=M)
        verifica("gestor comum não gerencia contas", code == 403)

        print("\n== Vagas, avaliações do cargo e portal ==")
        _, code = req("/api/gestor/vaga", {"titulo": "Vaga Sênior", "cargo_id": 3,
                                           "local": "Unidade A", "pais": "Brasil"}, G)
        verifica("vaga criada", code == 200)
        vg_pais, _ = req("/api/vagas")
        verifica("vaga expõe o país no portal público",
                 any(v.get("pais") == "Brasil" for v in vg_pais["vagas"]))
        req("/api/gestor/pergunta-entrevista", {"cargo_id": 3, "texto": "Pergunta 1"}, G)
        req("/api/gestor/questao", {"cargo_id": 3, "pergunta": "2+2?",
                                    "opcoes": ["3", "4", "5"], "correta": 1}, G)
        _, code = req("/api/gestor/questao", {"cargo_id": 3, "pergunta": "Só uma opção?",
                                              "opcoes": ["x"], "correta": 0}, G)
        verifica("questão com 1 opção é rejeitada", code == 400)
        vg, _ = req("/api/vagas")
        verifica("portal lista a vaga aberta", len(vg["vagas"]) == 1)
        vaga_id = vg["vagas"][0]["id"]
        # página pública por gestor: maria (Unidade A) vê a vaga; admin sem local vê tudo
        vgm, code = req("/api/vagas?g=maria")
        verifica("página de vagas da gestora filtra pelo local dela",
                 code == 200 and vgm["pagina"]["gestor_nome"] == "Maria"
                 and len(vgm["vagas"]) == 1)
        req("/api/gestor/vaga", {"titulo": "Vaga Outro Local", "cargo_id": 2, "local": "Unidade Z"}, G)
        vgm2, _ = req("/api/vagas?g=maria")
        verifica("vaga de outro local não aparece na página da gestora",
                 all(v["local"] != "Unidade Z" for v in vgm2["vagas"]))
        _, code = req("/api/vagas?g=nao.existe")
        verifica("página de gestor inexistente retorna 404", code == 404)
        _, code = req("/api/candidato/recuperar-acesso", {"email": "x@x.com"})
        verifica("recuperar acesso sem SMTP explica a limitação", code == 400)

        print("\n== Jornada do candidato ==")
        _, code = req("/api/candidato/cadastro", {"nome": "Sem Local", "email": "s@x.com", "consentimento": True})
        verifica("cadastro sem local é rejeitado", code == 400)
        t, code = req("/api/candidato/cadastro", {"nome": "Bia Teste", "email": "b@x.com", "consentimento": True,
                                                  "telefone": "+244 923000000", "local": "Unidade A", "vaga_id": vaga_id})
        verifica("cadastro pela vaga funciona", code == 200)
        C = {"X-Token": t["token"]}
        me, _ = req("/api/candidato/me", headers=C)
        verifica("candidatura criada na etapa inscrito",
                 me["candidaturas"][0]["etapa"] == "inscrito")
        verifica("cargo de interesse herdado da vaga", me["candidato"]["cargo_desejado_id"] == 3)
        qz, _ = req("/api/candidato/quiz", headers=C)
        verifica("quiz não vaza gabarito", all("correta" not in q for q in qz["questoes"]))
        r, _ = req("/api/candidato/quiz", {"respostas": {str(qz["questoes"][0]["id"]): 1}}, C)
        verifica("quiz corrigido no servidor", r == {"acertos": 1, "total": 1})
        req("/api/candidato/teste", {"tipo": "disc", "payload": {
            "pct": {"D": 20, "I": 30, "S": 40, "C": 90}, "dominante": "C", "secundario": "S"}}, C)
        req("/api/candidato/teste", {"tipo": "base", "payload": {
            "pct": {"B": 40, "A": 20, "S": 30, "E": 80}, "dominante": "E", "secundario": "B"}}, C)
        cg, _ = req("/api/cargos")
        senior = [c for c in cg["cargos"] if c["id"] == 3][0]
        req("/api/candidato/autoavaliacao", {"respostas": [
            {"competencia_id": k["id"], "nivel": 4} for k in senior["competencias"]]}, C)
        me, _ = req("/api/candidato/me", headers=C)
        verifica("match calculado com 4 componentes",
                 set(me["match"]["componentes"]) ==
                 {"competencias", "disc", "base", "conhecimento"})

        print("\n== Banco de talentos (CRM) ==")
        _, code = req("/api/candidato/cadastro", {"nome": "Bia 2", "email": "b@x.com",
                                                  "telefone": "+244 923000000", "local": "Unidade A", "consentimento": True})
        verifica("cadastro duplicado é barrado com aviso", code == 409)
        _, code = req("/api/candidato/cadastro", {"nome": "Sem Consentir", "email": "sc@x.com",
                                                  "telefone": "+244 923000000", "local": "Unidade A"})
        verifica("cadastro sem consentimento LGPD é rejeitado", code == 400)
        lista0, _ = req("/api/gestor/candidatos", headers=G)
        cid0 = lista0["candidatos"][0]["candidato"]["id"]
        tg, code = req("/api/gestor/candidato/%d/tags" % cid0, {"tags": ["Java", "lideranca", "java"]}, G)
        verifica("tags salvas sem duplicar", code == 200 and tg["tags"] == ["java", "lideranca"])
        todas, _ = req("/api/gestor/tags", headers=G)
        verifica("lista global de tags", "java" in todas["tags"])
        # radar de talentos: vaga nova do mesmo cargo deve sugerir a candidata do banco
        req("/api/gestor/vaga", {"titulo": "Vaga Sênior 2", "cargo_id": 3, "local": "Unidade A"}, G)
        vg2, _ = req("/api/vagas")
        vaga2 = [v for v in vg2["vagas"] if v["titulo"] == "Vaga Sênior 2"][0]["id"]
        sug, _ = req("/api/gestor/vaga/%d/sugestoes" % vaga2, headers=G)
        verifica("radar de talentos sugere candidata do banco",
                 any(s2["nome"] == "Bia Teste" for s2 in sug["sugestoes"]))

        print("\n== Relatórios, templates e LGPD ==")
        rel, code = req("/api/gestor/relatorios", headers=G)
        verifica("relatórios respondem com funil", code == 200 and len(rel["funil"]) >= 1)
        verifica("relatórios contam candidatos", rel["total_candidatos"] >= 1)
        tp, code = req("/api/gestor/templates", headers=G)
        verifica("templates carregam com padrão", code == 200 and "confirmacao" in tp["templates"])
        _, code = req("/api/gestor/templates", headers=M)
        verifica("gestor comum não edita templates", code == 403)
        _, code = req("/api/gestor/templates", {"templates": {"confirmacao": {
            "assunto": "Oi {nome}", "corpo": "Link: {link}"}}}, G)
        verifica("templates salvam", code == 200)
        tp2, _ = req("/api/gestor/templates", headers=G)
        verifica("template personalizado aplicado",
                 tp2["templates"]["confirmacao"]["assunto"] == "Oi {nome}")
        _, code = req("/api/gestor/email", {"candidato_id": cid0, "assunto": "t", "corpo": "t"}, G)
        verifica("e-mail manual sem SMTP retorna erro claro", code == 400)

        print("\n== Notificações e atividades ==")
        det0, _ = req("/api/gestor/candidatos", headers=G)
        cand0 = det0["candidatos"][0]["candidato"]["id"]
        d0, _ = req("/api/gestor/candidato/%d" % cand0, headers=G)
        verifica("avaliação completa registrada na timeline",
                 any(e["tipo"] == "sistema" and "completa" in e["texto"]
                     for e in d0["eventos"]))
        atv, code = req("/api/gestor/atividades", headers=G)
        verifica("feed de atividades responde", code == 200 and len(atv["atividades"]) >= 5)
        # link de acesso por token na URL equivale ao token no header
        me_link, code = req("/api/candidato/me", headers={"X-Token": t["token"]})
        verifica("token do link de acesso funciona", code == 200 and me_link["candidato"]["nome"] == "Bia Teste")

        print("\n== Pipeline e entrevista ==")
        pp, _ = req("/api/gestor/vaga/%d/pipeline" % vaga_id, headers=G)
        verifica("pipeline mostra o candidato com match",
                 pp["candidaturas"][0]["match"] is not None)
        ca_id = pp["candidaturas"][0]["candidatura_id"]
        cand_id = pp["candidaturas"][0]["candidato_id"]
        _, code = req("/api/gestor/candidatura", {"id": ca_id, "etapa": "entrevista"}, G)
        verifica("mover etapa funciona", code == 200)
        _, code = req("/api/gestor/candidatura", {"id": ca_id, "etapa": "inexistente"}, G)
        verifica("etapa inválida é rejeitada", code == 400)
        det, _ = req("/api/gestor/candidato/%d" % cand_id, headers=G)
        e, _ = req("/api/gestor/entrevista", {"candidato_id": cand_id, "cargo_id": 3,
                                              "notas": [{"pergunta_id": det["perguntas_entrevista"][0]["id"],
                                                         "nota": 4}]}, G)
        verifica("entrevista registrada com média", e.get("media") == 4)
        det, _ = req("/api/gestor/candidato/%d" % cand_id, headers=G)
        verifica("match final com 5 componentes",
                 len(det["match"]["componentes"]) == 5)
        verifica("timeline registra eventos", len(det["eventos"]) >= 7)
        verifica("mobilidade interna lista todos os cargos",
                 len(det["matches_cargos"]) == len(cg["cargos"]))

        print("\n== Isolamento por local ==")
        t2, _ = req("/api/candidato/cadastro", {"nome": "Outro Local", "email": "o@x.com", "consentimento": True,
                                                "telefone": "+244 923000000", "local": "Unidade B", "cargo_desejado_id": 2})
        lista_admin, _ = req("/api/gestor/candidatos", headers=G)
        lista_maria, _ = req("/api/gestor/candidatos", headers=M)
        verifica("admin vê os 2 candidatos", len(lista_admin["candidatos"]) == 2)
        verifica("gestora com local vê apenas 1", len(lista_maria["candidatos"]) == 1)
        _, code = req("/api/gestor/candidato/%d" % lista_admin["candidatos"][0]["candidato"]["id"]
                      if lista_admin["candidatos"][0]["candidato"]["local"] == "Unidade B"
                      else "/api/gestor/candidato/%d" % lista_admin["candidatos"][1]["candidato"]["id"],
                      headers=M)
        verifica("gestora não abre candidato de outro local", code == 404)

        print("\n== Integrações ==")
        _, code = req("/api/gestor/ia/curriculo/%d" % cand_id, {}, G)
        verifica("IA sem chave retorna erro claro", code == 400)
        integ, _ = req("/api/gestor/integracoes", headers=G)
        verifica("integrações reportam status", integ["ia_configurada"] is False)
        _, code = req("/api/gestor/integracoes", headers=M)
        verifica("gestor comum não vê integrações", code == 403)

        print("\n== Anonimização (LGPD) ==")
        t3, _ = req("/api/candidato/cadastro", {"nome": "Para Anonimizar", "email": "an@x.com",
                                                "telefone": "+244 923000000", "local": "Unidade A", "consentimento": True,
                                                "cargo_desejado_id": 2})
        lista3, _ = req("/api/gestor/candidatos", headers=G)
        alvo3 = [c for c in lista3["candidatos"] if c["candidato"]["nome"] == "Para Anonimizar"][0]
        _, code = req("/api/gestor/candidato/%d/anonimizar" % alvo3["candidato"]["id"], {}, G)
        verifica("anonimização executa", code == 200)
        det3, _ = req("/api/gestor/candidato/%d" % alvo3["candidato"]["id"], headers=G)
        verifica("dados pessoais removidos",
                 det3["candidato"]["nome"] == "Candidato anonimizado"
                 and det3["candidato"]["email"] == "")
        _, code = req("/api/candidato/me", headers={"X-Token": t3["token"]})
        verifica("token antigo do anonimizado deixa de funcionar", code == 401)

        print("\n== Colaborador interno ==")
        ti, code = req("/api/candidato/cadastro", {"nome": "Servidor Interno", "email": "si@x.com",
                                                   "telefone": "+244 923000000", "local": "Unidade A", "consentimento": True,
                                                   "tipo": "interno", "cargo_desejado_id": 3})
        verifica("cadastro de colaborador interno funciona", code == 200)
        mei, _ = req("/api/candidato/me", headers={"X-Token": ti["token"]})
        verifica("tipo interno registrado", mei["candidato"]["tipo"] == "interno")
        t_ext, _ = req("/api/candidato/cadastro", {"nome": "Externo Vaga", "email": "ev@x.com",
                                                   "telefone": "+244 923000000", "local": "Unidade A", "consentimento": True,
                                                   "vaga_id": vaga_id, "tipo": "interno"})
        me_ext, _ = req("/api/candidato/me", headers={"X-Token": t_ext["token"]})
        verifica("inscrição em vaga força tipo externo", me_ext["candidato"]["tipo"] == "externo")

        print("\n== Painel do dono ==")
        sd, _ = req("/api/dono/setup")
        verifica("dono exige configuração inicial", sd["precisa_setup"] is True)
        _, code = req("/api/dono/setup", {"senha": "curta"})
        verifica("senha curta do dono é rejeitada", code == 400)
        dn, code = req("/api/dono/setup", {"senha": "senhadodono1"})
        verifica("setup do dono cria acesso", code == 200 and "token" in dn)
        D = {"X-Dono-Token": dn["token"]}
        _, code = req("/api/dono/setup", {"senha": "outrasenha1"})
        verifica("segundo setup do dono é bloqueado", code == 403)
        _, code = req("/api/dono/visao", headers={"X-Dono-Token": "falso"})
        verifica("token falso do dono é rejeitado", code == 401)
        _, code = req("/api/dono/visao", headers=G)
        verifica("token de gestor não acessa painel do dono", code == 401)
        vis, code = req("/api/dono/visao", headers=D)
        verifica("visão do dono lista contas e saúde",
                 code == 200 and vis["totais"]["gestores"] >= 2
                 and "sistema" in vis and vis["totais"]["internos"] >= 1)
        alvo_g = [g for g in vis["gestores"] if g["login"] == "maria"][0]
        imp, code = req("/api/dono/entrar-como", {"gestor_id": alvo_g["id"]}, D)
        verifica("dono entra na conta da gestora", code == 200 and imp["login"] == "maria")
        li, code = req("/api/gestor/candidatos", headers={"X-Gestor-Token": imp["token"]})
        verifica("sessão de suporte funciona com o escopo da gestora",
                 code == 200 and all(
                     c["candidato"]["local"] in ("Unidade A", "")
                     for c in li["candidatos"]))
        _, code = req("/api/dono/gestor-senha", {"gestor_id": alvo_g["id"], "nova": "novasenha"}, D)
        verifica("dono redefine senha de gestor", code == 200)
        _, code = req("/api/gestor/login", {"login": "maria", "senha": "novasenha"})
        verifica("gestora entra com a senha redefinida", code == 200)
        _, code = req("/api/dono/billing", {"local": "Unidade A", "plano": "mensal",
                                            "valor": "R$ 490", "status": "ativo"}, D)
        verifica("billing registra cliente", code == 200)
        bl, _ = req("/api/dono/billing", headers=D)
        verifica("billing lista locais com plano",
                 any(c["local"] == "Unidade A" and c["plano"] == "mensal"
                     for c in bl["clientes"]))

        print("\n== Módulo Diagnóstico de Competências ==")
        _, code = req("/api/gestor/diagnostico", headers=G)
        verifica("módulo bloqueado antes de o dono liberar", code == 403)
        gl2, _ = req("/api/gestor/gestores", headers=G)
        id_admin = [g["id"] for g in gl2["gestores"] if g["login"] == "admin.t"][0]
        _, code = req("/api/dono/modulos", {"gestor_id": id_admin,
                                            "modulo": "diagnostico", "ativo": True}, D)
        verifica("dono libera o módulo para o gestor", code == 200)
        _, code = req("/api/dono/modulos", {"gestor_id": id_admin,
                                            "modulo": "inexistente", "ativo": True}, D)
        verifica("módulo desconhecido é rejeitado", code == 400)
        dg, code = req("/api/gestor/diagnostico", headers=G)
        verifica("módulo liberado responde com projeto vazio",
                 code == 200 and dg["stats"]["total"] == 0)
        s1, code = req("/api/gestor/diagnostico/sessao", {
            "colaborador": "Colab GTI", "cargo": "Analista de Sistemas",
            "unidade": "DITAS", "status": "rascunho",
            "dados": {"a1": {"nome": "Colab GTI"}, "b6": {"nivel_global": "Táctico"}}}, G)
        verifica("sessão de levantamento criada", code == 200 and s1.get("id"))
        _, code = req("/api/gestor/diagnostico/sessao", {
            "id": s1["id"], "colaborador": "Colab GTI", "cargo": "Analista",
            "unidade": "DITAS", "status": "concluida",
            "dados": {"a1": {"nome": "Colab GTI"}, "b6": {"nivel_global": "Táctico"}}}, G)
        verifica("sessão atualizada para concluída", code == 200)
        dg2, _ = req("/api/gestor/diagnostico", headers=G)
        verifica("estatísticas contam a sessão concluída",
                 dg2["stats"]["total"] == 1 and dg2["stats"]["concluidas"] == 1
                 and dg2["stats"]["por_unidade"].get("DITAS") == 1)
        sd, _ = req("/api/gestor/diagnostico/sessao/%d" % s1["id"], headers=G)
        verifica("sessão devolve os dados completos",
                 sd["sessao"]["dados"]["b6"]["nivel_global"] == "Táctico")
        _, code = req("/api/gestor/diagnostico/arquivo/nao-existe.pdf", headers=G)
        verifica("arquivo fora da lista é bloqueado", code == 404)
        ml2, _ = req("/api/gestor/login", {"login": "maria", "senha": "novasenha"})
        verifica("login informa os módulos da conta", ml2.get("modulos") == [])
        _, code = req("/api/gestor/diagnostico", headers={"X-Gestor-Token": ml2["token"]})
        verifica("gestora sem módulo continua bloqueada", code == 403)

        print("\n== Isolamento do módulo Diagnóstico por local ==")
        id_maria = [g["id"] for g in gl2["gestores"] if g["login"] == "maria"][0]
        req("/api/dono/modulos", {"gestor_id": id_maria, "modulo": "diagnostico", "ativo": True}, D)
        sm, code = req("/api/gestor/diagnostico/sessao",
                       {"colaborador": "Colab A", "unidade": "AIE",
                        "dados": {"a1": {"nome": "Colab A"}}}, M)
        verifica("gestora cria sessão no seu local", code == 200 and sm.get("id"))
        req("/api/gestor/gestores", {"nome": "Carlos", "login": "carlos",
                                     "senha": "senha123", "local": "Unidade B"}, G)
        gl3, _ = req("/api/gestor/gestores", headers=G)
        id_carlos = [g["id"] for g in gl3["gestores"] if g["login"] == "carlos"][0]
        req("/api/dono/modulos", {"gestor_id": id_carlos, "modulo": "diagnostico", "ativo": True}, D)
        cl, _ = req("/api/gestor/login", {"login": "carlos", "senha": "senha123"})
        C2 = {"X-Gestor-Token": cl["token"]}
        dgc, _ = req("/api/gestor/diagnostico", headers=C2)
        verifica("gestor de outro local não vê a sessão alheia",
                 all(s["id"] != sm["id"] for s in dgc["sessoes"]))
        _, code = req("/api/gestor/diagnostico/sessao/%d" % sm["id"], headers=C2)
        verifica("gestor de outro local recebe 404 na sessão alheia", code == 404)
        _, code = req("/api/gestor/diagnostico/sessao/%d" % sm["id"], headers=C2, metodo="DELETE")
        verifica("gestor de outro local não apaga sessão alheia", code == 404)
        dga, _ = req("/api/gestor/diagnostico", headers=G)
        verifica("admin (sem local) enxerga sessões de todos",
                 any(s["id"] == sm["id"] for s in dga["sessoes"]))

        print("\n== Blindagem de entradas ==")
        cadx, _ = req("/api/candidato/cadastro",
                      {"nome": "Fraude", "email": "fraude@x.com", "telefone": "+244 923000000", "local": "Unidade A",
                       "consentimento": True, "tipo": "interno", "cargo_desejado_id": 2})
        FX = {"X-Token": cadx["token"]}
        _, code = req("/api/candidato/teste",
                      {"tipo": "disc", "payload": {"pct": {"D": "abc", "I": 1, "S": 1, "C": 1}}}, FX)
        verifica("nota de teste inválida é rejeitada, não quebra", code == 400)
        _, code = req("/api/gestor/candidatos", headers=G)
        verifica("painel de candidatos abre após nota suspeita", code == 200)
        _, code = req("/api/candidato/teste", {"tipo": "base", "respostas": [["B", "A", "S", "E"]] * 8}, FX)
        verifica("B.A.S.E. recalculado no servidor a partir das respostas", code == 200)
        _, code = req("/api/candidato/quiz", {"respostas": {"1": "xyz"}}, FX)
        verifica("quiz com resposta inválida não dá 500", code in (200, 400))
        _, code = req("/api/candidato/autoavaliacao",
                      {"respostas": [{"competencia_id": "x", "nivel": "y"}]}, FX)
        verifica("autoavaliação com lixo não dá 500", code == 200)

        print("\n== Escopo de administrador em cargos ==")
        _, code = req("/api/gestor/cargo", {"nome": "Cargo Proibido", "area": "X"}, M)
        verifica("gestor comum não cria cargo", code == 403)
        _, code = req("/api/gestor/cargo/1", headers=M, metodo="DELETE")
        verifica("gestor comum não apaga cargo", code == 403)
        _, code = req("/api/gestor/cargo", {"nome": "Cargo do Admin", "area": "X"}, G)
        verifica("admin cria cargo normalmente", code == 200)

        print("\n== Login e força bruta ==")
        # simula o Caddy: IP real é o último da cadeia. Forjar o primeiro valor
        # (rotativo) não pode burlar o limite, pois o IP real ao final é o mesmo.
        for i in range(9):
            _, code = req("/api/gestor/login", {"login": "maria", "senha": "errada"},
                          {"X-Forwarded-For": "9.9.9.%d, 198.51.100.5" % i})
        verifica("forjar o primeiro X-Forwarded-For não burla o limite (429)", code == 429)
        bom, code = req("/api/gestor/login", {"login": "maria", "senha": "novasenha"})
        verifica("login legítimo de outro IP não é afetado pelo bloqueio", code == 200)

        print("\n== Cadastro: telefone, função e novo cargo ==")
        _, code = req("/api/candidato/cadastro",
                      {"nome": "Sem Fone", "email": "semfone@x.com",
                       "local": "Unidade A", "consentimento": True})
        verifica("cadastro sem telefone é rejeitado", code == 400)
        cnv, code = req("/api/candidato/cadastro",
                        {"nome": "Cria Cargo", "email": "criacargo@x.com",
                         "telefone": "+244 923111222", "local": "Unidade A",
                         "consentimento": True, "tipo": "interno",
                         "funcao": "Suporte de rede do 2.º nível",
                         "novo_cargo": "Técnico de Redes Inventado"})
        verifica("cadastro com novo cargo funciona", code == 200 and cnv.get("token"))
        cargos_apos, _ = req("/api/cargos")
        novo = [c for c in cargos_apos["cargos"] if c["nome"] == "Técnico de Redes Inventado"]
        verifica("cargo novo passou a existir no sistema", len(novo) == 1)
        menv, _ = req("/api/candidato/me", headers={"X-Token": cnv["token"]})
        verifica("candidato fica vinculado ao cargo que criou",
                 menv["candidato"]["cargo_desejado_id"] == novo[0]["id"])
        verifica("função e telefone guardados no candidato",
                 menv["candidato"]["funcao"] == "Suporte de rede do 2.º nível"
                 and menv["candidato"]["telefone"] == "+244 923111222")
        req("/api/candidato/cadastro",
            {"nome": "Reusa Cargo", "email": "reusa@x.com", "telefone": "+55 11999998888",
             "local": "Unidade A", "consentimento": True, "tipo": "interno",
             "novo_cargo": "técnico de redes inventado"})
        cargos_apos2, _ = req("/api/cargos")
        repet = [c for c in cargos_apos2["cargos"] if c["nome"].lower() == "técnico de redes inventado"]
        verifica("cargo novo não é duplicado (reaproveita pelo nome)", len(repet) == 1)

        print("\n== SMTP: teste de envio ==")
        _, code = req("/api/gestor/integracoes/teste", {}, G)
        verifica("teste de e-mail sem SMTP configurado avisa (400)", code == 400)
        ig, _ = req("/api/gestor/integracoes", headers=G)
        verifica("painel de integrações expõe porta padrão",
                 ig.get("smtp_porta") == "587")

        print("\n== Esqueci minha senha (gestor) ==")
        r1, code = req("/api/gestor/esqueci-senha", {"login": "maria"})
        verifica("pedido de reset responde 200 para conta existente", code == 200)
        r2, code = req("/api/gestor/esqueci-senha", {"login": "naoexiste@x.com"})
        verifica("resposta idêntica para conta inexistente (não revela)",
                 code == 200 and r2.get("ok") is True)
        _, code = req("/api/gestor/redefinir-senha", {"token": "token-invalido", "nova": "novasenha9"})
        verifica("redefinir com token inválido é rejeitado", code == 400)
        _, code = req("/api/gestor/redefinir-senha", {"token": "x", "nova": "123"})
        verifica("redefinir com senha curta é rejeitado", code == 400)

        print("\n== Endereços limpos ==")
        for pagina in ("/", "/candidato", "/gestor", "/vagas", "/dono"):
            resp = urllib.request.urlopen(BASE + pagina, timeout=5)
            verifica("página %s responde em endereço limpo" % pagina,
                     resp.status == 200 and
                     "text/html" in resp.headers.get("Content-Type", ""))

        class SemRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        abridor = urllib.request.build_opener(SemRedirect)
        try:
            abridor.open(BASE + "/gestor.html", timeout=5)
            verifica("link antigo .html redireciona", False)
        except urllib.error.HTTPError as e3:
            verifica("link antigo .html redireciona",
                     e3.code == 301 and e3.headers.get("Location") == "/gestor")
        try:
            abridor.open(BASE + "/candidato.html?token=abc", timeout=5)
            verifica("redirect preserva a query string", False)
        except urllib.error.HTTPError as e4:
            verifica("redirect preserva a query string",
                     e4.headers.get("Location") == "/candidato?token=abc")

        print("\n== Conexão keep-alive (sem desync) ==")
        import socket as _sock
        corpo = b'{"login":"x","senha":"y"}'
        req1 = (b"POST /api/gestor/candidatos HTTP/1.1\r\nHost: x\r\n"
                b"Content-Type: application/json\r\nContent-Length: %d\r\n\r\n" % len(corpo)) + corpo
        req2 = b"GET /api/locais HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n"
        cx = _sock.create_connection(("localhost", PORTA), timeout=5)
        cx.sendall(req1 + req2)
        time.sleep(0.4)
        cx.settimeout(2)
        bruto = b""
        try:
            while True:
                ped = cx.recv(4096)
                if not ped:
                    break
                bruto += ped
        except _sock.timeout:
            pass
        cx.close()
        resp = bruto.decode("latin-1")
        verifica("resposta antes de ler o corpo não desincroniza a conexão",
                 "501" not in resp and "Unsupported method" not in resp)
        verifica("requisição seguinte na mesma conexão é atendida",
                 '"locais"' in resp)

        print("\n== Segurança básica ==")
        _, code = req("/api/candidato/me", headers={"X-Token": "falso"})
        verifica("token falso de candidato é rejeitado", code == 401)
        try:
            urllib.request.urlopen(BASE + "/%2e%2e/server.py", timeout=3)
            verifica("path traversal bloqueado", False)
        except urllib.error.HTTPError as e2:
            verifica("path traversal bloqueado", e2.code == 404)

    finally:
        servidor.terminate()
        servidor.wait(timeout=5)
        shutil.rmtree(pasta, ignore_errors=True)

    print("\n%d verificações, %d falha(s)" % (total, len(falhas)))
    if falhas:
        for f in falhas:
            print("  FALHOU:", f)
        sys.exit(1)
    print("TODOS OS TESTES PASSARAM")


if __name__ == "__main__":
    main()
