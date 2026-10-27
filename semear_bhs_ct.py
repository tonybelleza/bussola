#!/usr/bin/env python3
"""
Cria (ou completa) a empresa Belleza's Home Services CT com os cargos de limpeza
e escritório: competências, perfil DISC e B.A.S.E. desejado, roteiro de entrevista
e teste de conhecimento. Rascunho para o Tony revisar no próprio painel.

Uso:  python3 semear_bhs_ct.py
Pode rodar mais de uma vez: só cria o que falta e nunca apaga ou sobrescreve
competências, perguntas ou questões que já existam num cargo.
"""
import json
import sys

import empresas
import server

NOME_EMPRESA = "Belleza's Home Services CT"

# (nome, área, nível, descrição, DISC alvo, B.A.S.E. alvo, triagem por voz,
#  competências [(nome, tipo, nível 1-5, obrigatória)], perguntas de entrevista,
#  questões [(pergunta, [opções], índice da correta)])
CARGOS = [
    (
        "Cleaning Technician", "Field operations", "Entry",
        "Cleans homes solo on a planned route (2 to 3 houses a day), following each home's checklist in Jobber.",
        "S", "B", True,
        [
            ("Residential cleaning techniques (kitchens, bathrooms, dusting, floors)", "tecnica", 3, 1),
            ("Following a checklist in the Jobber app", "tecnica", 3, 1),
            ("Time management on a route (2 to 2.5 h per house)", "tecnica", 3, 1),
            ("Attention to detail and putting everything back in place", "relacional", 4, 1),
            ("Professional conduct in clients' homes (no perfume, minimal phone use)", "relacional", 4, 1),
            ("Comfort with pets", "relacional", 3, 0),
            ("House cleaning experience", "experiencia", 2, 0),
        ],
        [
            "Walk me through how you clean a bathroom from start to finish.",
            "A client's home is not finished and you are running late for the next house. What do you do?",
            "Tell me about a time a client was unhappy with your work. How did you handle it?",
            "How do you make sure nothing is damaged or out of place when you leave a home?",
            "How do you stay organized when you work alone all day?",
        ],
        [
            ("Which order is correct when cleaning a room?", ["Floors first, then dust", "Top to bottom: dust high surfaces, then floors", "It does not matter"], 1),
            ("You find a scratch on a client's furniture before you start. What do you do?", ["Ignore it", "Take a photo and report it to the office before cleaning", "Try to fix it"], 1),
            ("Which product should never be mixed with bleach?", ["Water", "Ammonia", "Dish soap diluted in a bucket"], 1),
            ("A client asks for your personal phone number. What is the right answer?", ["Give it to them", "Politely refer them to the office", "Ignore the request"], 1),
            ("Before leaving a house you should:", ["Leave quietly", "Do a final walkthrough, turn off lights you turned on, and put everything back", "Only check the kitchen"], 1),
        ],
    ),
    (
        "Cleaning Technician Driver", "Field operations", "Entry",
        "Cleaning Technician who uses their own car to drive the route between clients' homes.",
        "S", "B", True,
        [
            ("Valid driver's license and own reliable car", "formacao", 3, 1),
            ("Safe driving and route planning between homes", "tecnica", 3, 1),
            ("Residential cleaning techniques", "tecnica", 3, 1),
            ("Following a checklist in the Jobber app", "tecnica", 3, 1),
            ("Punctuality and reliability", "relacional", 4, 1),
            ("Professional conduct in clients' homes", "relacional", 4, 1),
            ("House cleaning experience", "experiencia", 2, 0),
        ],
        [
            "How do you plan your day when you have three homes in different towns?",
            "Your car breaks down on the way to a client. What do you do first?",
            "Walk me through how you clean a kitchen from start to finish.",
            "How do you handle parking at clients' homes in busy neighborhoods?",
            "Tell me about a time you had to be on time no matter what.",
        ],
        [
            ("You will be 20 minutes late to the next client. What do you do?", ["Nothing, just arrive", "Tell the office right away so the client is informed", "Skip the client"], 1),
            ("Where should you park at a client's home?", ["Anywhere close", "Where approved by the client or office, never blocking driveways", "On the lawn"], 1),
            ("Which order is correct when cleaning a room?", ["Floors first, then dust", "Top to bottom: dust high surfaces, then floors", "It does not matter"], 1),
            ("Which product should never be mixed with bleach?", ["Water", "Ammonia", "Dish soap diluted in a bucket"], 1),
            ("Parking costs at a client's home are:", ["Always paid by you", "Reimbursed when approved by the office", "Charged to the client directly by you"], 1),
        ],
    ),
    (
        "Trainer", "Field operations", "Senior",
        "Trains new Cleaning Technicians in the field: standards, checklists, Jobber and client etiquette.",
        "I", "S", False,
        [
            ("Mastery of the BHS cleaning standards and checklists", "tecnica", 5, 1),
            ("Teaching and demonstrating hands-on", "relacional", 4, 1),
            ("Giving clear, respectful feedback", "relacional", 4, 1),
            ("Patience and encouragement with new hires", "relacional", 4, 1),
            ("Jobber app (checklists, schedule, photos)", "tecnica", 4, 1),
            ("Professional house cleaning experience (2+ years)", "experiencia", 4, 1),
        ],
        [
            "How would you train someone on their first day in a client's home?",
            "A new tech keeps missing the same step on the checklist. What do you do?",
            "How do you give feedback that corrects without discouraging?",
            "How do you know a trainee is ready to work solo?",
            "Tell me about someone you helped grow at work.",
        ],
        [
            ("A trainee skipped the final walkthrough. The best response is:", ["Report them without talking to them", "Explain why it matters, show how to do it, and check the next house", "Do it for them every time"], 1),
            ("When is a trainee ready to work solo?", ["After one day", "When they complete the checklist to standard on their own in several homes", "When they ask to"], 1),
            ("Good feedback is:", ["General and delayed", "Specific, timely and focused on the task", "Only positive"], 1),
            ("Which order is correct when cleaning a room?", ["Floors first, then dust", "Top to bottom: dust high surfaces, then floors", "It does not matter"], 1),
            ("A client complains about a trainee's work. You should:", ["Ignore it", "Thank the client, inform the office, and retrain on that point", "Argue with the client"], 1),
        ],
    ),
    (
        "Office Coordinator", "Office", "Mid",
        "Manages schedules, client communication and support to the field team from the office.",
        "C", "B", False,
        [
            ("Scheduling and route coordination in Jobber", "tecnica", 4, 1),
            ("Customer service by phone, text and email", "relacional", 4, 1),
            ("Written and spoken English; Spanish or Portuguese is a plus", "formacao", 3, 1),
            ("Organization and follow-through on details", "relacional", 4, 1),
            ("Problem solving with clients and techs", "relacional", 3, 1),
            ("Office or customer service experience", "experiencia", 3, 0),
        ],
        [
            "A tech calls in sick at 7 am with three homes on the schedule. What do you do?",
            "How do you handle an upset client on the phone?",
            "How do you organize your day when everything feels urgent?",
            "Tell me about a process you improved in a previous job.",
            "How do you make sure nothing falls through the cracks between the office and the field?",
        ],
        [
            ("A tech calls in sick in the morning. The first step is:", ["Cancel all their clients", "Check who can cover and inform affected clients quickly", "Wait to see if they feel better"], 1),
            ("An upset client calls. The best first response is:", ["Defend the tech", "Listen, acknowledge, and promise a concrete next step", "Transfer the call"], 1),
            ("How much notice does a tech need to give to drop a route?", ["None", "24 hours", "One week"], 1),
            ("Client information like door codes should be:", ["Shared in group chats", "Kept in Jobber and shared only with the assigned tech", "Written on paper in the car"], 1),
            ("Best way to confirm tomorrow's schedule with techs:", ["Assume they know", "Confirm in Jobber and send a clear reminder", "Call only if there is a problem"], 1),
        ],
    ),
    (
        "Operations Manager", "Office", "Senior",
        "Leads the field team: staffing, routes, quality, supplies and client retention.",
        "D", "B", False,
        [
            ("Team leadership and hiring", "relacional", 5, 1),
            ("Route planning and capacity management", "tecnica", 4, 1),
            ("Quality control and client retention", "tecnica", 4, 1),
            ("Supplies and inventory management", "tecnica", 3, 1),
            ("Using data (Jobber reports, complaints, hours) to decide", "tecnica", 3, 0),
            ("Management experience in cleaning or field services", "experiencia", 4, 1),
        ],
        [
            "How would you reduce turnover among cleaning techs?",
            "Two clients complain about the same tech in one week. What do you do?",
            "How do you balance routes so techs are not overloaded?",
            "Tell me about a time you turned around an underperforming team.",
            "Which numbers would you look at every week to know the operation is healthy?",
        ],
        [
            ("A tech gets repeated complaints. The best approach is:", ["Fire them right away", "Review the facts, retrain, set clear expectations and follow up", "Ignore it if they are fast"], 1),
            ("A healthy route for one tech is usually:", ["5 or more houses a day", "2 to 3 houses a day of about 2 to 2.5 hours each", "1 house a day"], 1),
            ("Which metric best signals client retention risk?", ["Number of supplies used", "Complaints and skipped or cancelled visits", "Miles driven"], 1),
            ("When hiring, the first filter for a field tech is:", ["Years in the US", "Valid license and own car when the role requires driving", "Age"], 1),
            ("Supplies run low in a tech's kit. The right process is:", ["Tech buys and keeps receipts", "Restock from inventory on a schedule and track usage", "Ask the client for supplies"], 1),
        ],
    ),
    (
        "Quality Supervisor", "Field operations", "Mid",
        "Inspects homes after cleaning, gives feedback to techs and closes the loop on client complaints.",
        "C", "E", False,
        [
            ("Inspection against the home checklist", "tecnica", 5, 1),
            ("Spotting details others miss", "relacional", 5, 1),
            ("Clear written reports with photos", "tecnica", 4, 1),
            ("Constructive feedback to techs", "relacional", 4, 1),
            ("Professional house cleaning experience (2+ years)", "experiencia", 3, 1),
        ],
        [
            "Walk me through how you inspect a home after it was cleaned.",
            "What are the three things most often missed in a cleaning, in your experience?",
            "How do you report a problem so it gets fixed and does not happen again?",
            "A tech disagrees with your inspection. How do you handle it?",
            "How do you balance being strict with keeping the team motivated?",
        ],
        [
            ("During an inspection you find dust on top of door frames. You should:", ["Ignore small things", "Record it with a photo and give the tech specific feedback", "Clean it and say nothing"], 1),
            ("A good inspection report includes:", ["Only a score", "What was checked, what failed, photos and the corrective action", "The client's opinion only"], 1),
            ("A client complaint is closed when:", ["The client stops calling", "The issue is fixed, the client confirms, and the cause is addressed with the tech", "The tech says it is done"], 1),
            ("Which order is correct when cleaning a room?", ["Floors first, then dust", "Top to bottom: dust high surfaces, then floors", "It does not matter"], 1),
            ("Feedback to a tech should be:", ["Public in the group chat", "Private, specific and with the standard shown", "Only when there is a complaint"], 1),
        ],
    ),
]


def semear(conn):
    e = conn.execute("SELECT * FROM empresas WHERE lower(nome)=lower(?)", (NOME_EMPRESA,)).fetchone()
    if e:
        empresa_id = e["id"]
    else:
        empresa_id, _ = empresas.criar_empresa(conn, NOME_EMPRESA)
        print("Empresa criada:", NOME_EMPRESA)
    mods = set(empresas.modulos(conn.execute("SELECT modulos FROM empresas WHERE id=?", (empresa_id,)).fetchone()))
    mods.add("voz")
    conn.execute("UPDATE empresas SET modulos=? WHERE id=?", (json.dumps(sorted(mods)), empresa_id))

    for (nome, area, nivel, descricao, disc, base, voz_ativa, comps, perguntas, questoes) in CARGOS:
        r = conn.execute(
            "SELECT id FROM cargos WHERE lower(nome)=lower(?) AND empresa_id=?", (nome, empresa_id)
        ).fetchone()
        if r:
            cargo_id = r["id"]
            conn.execute(
                "UPDATE cargos SET area=COALESCE(NULLIF(area,''),?), nivel=COALESCE(NULLIF(nivel,''),?),"
                " descricao=COALESCE(NULLIF(descricao,''),?), disc_alvo=COALESCE(NULLIF(disc_alvo,''),?),"
                " base_alvo=COALESCE(NULLIF(base_alvo,''),?) WHERE id=?",
                (area, nivel, descricao, disc, base, cargo_id),
            )
        else:
            cargo_id = conn.execute(
                "INSERT INTO cargos (nome, area, nivel, descricao, disc_alvo, base_alvo, empresa_id, voz_ativa, peso_voz)"
                " VALUES (?,?,?,?,?,?,?,?,0.30)",
                (nome, area, nivel, descricao, disc, base, empresa_id, 1 if voz_ativa else 0),
            ).lastrowid
            print("Cargo criado:", nome)
        if not conn.execute("SELECT 1 FROM competencias WHERE cargo_id=? LIMIT 1", (cargo_id,)).fetchone():
            for c_nome, tipo, nivel_req, obrig in comps:
                conn.execute(
                    "INSERT INTO competencias (cargo_id, nome, tipo, nivel_requerido, obrigatoria) VALUES (?,?,?,?,?)",
                    (cargo_id, c_nome, tipo, nivel_req, obrig),
                )
        if not conn.execute("SELECT 1 FROM perguntas_entrevista WHERE cargo_id=? LIMIT 1", (cargo_id,)).fetchone():
            for ordem, texto in enumerate(perguntas):
                conn.execute(
                    "INSERT INTO perguntas_entrevista (cargo_id, texto, ordem) VALUES (?,?,?)", (cargo_id, texto, ordem)
                )
        if not conn.execute("SELECT 1 FROM questoes WHERE cargo_id=? LIMIT 1", (cargo_id,)).fetchone():
            for pergunta, opcoes, correta in questoes:
                conn.execute(
                    "INSERT INTO questoes (cargo_id, pergunta, opcoes, correta) VALUES (?,?,?,?)",
                    (cargo_id, pergunta, json.dumps(opcoes, ensure_ascii=False), correta),
                )
    conn.commit()
    return empresa_id


if __name__ == "__main__":
    server.init_db()
    c = server.db()
    eid = semear(c)
    for r in c.execute(
        "SELECT g.nome, g.disc_alvo, g.base_alvo, g.voz_ativa,"
        " (SELECT COUNT(*) FROM competencias WHERE cargo_id=g.id) AS comp,"
        " (SELECT COUNT(*) FROM perguntas_entrevista WHERE cargo_id=g.id) AS perg,"
        " (SELECT COUNT(*) FROM questoes WHERE cargo_id=g.id) AS quest"
        " FROM cargos g WHERE empresa_id=? ORDER BY g.nome", (eid,),
    ):
        print("%-28s DISC %s  BASE %s  voz %s  competências %d  entrevista %d  teste %d" % tuple(r))
    c.close()
    sys.exit(0)
