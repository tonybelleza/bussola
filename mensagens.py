"""Mensagens do Bússola em português, inglês e espanhol: e-mails com a marca de
cada empresa (logo e nome), o e-mail único de resultados do candidato (DISC e
B.A.S.E.), o aviso único aos gestores e os textos do relatório em PDF.

O idioma do candidato vem de candidatos.idioma (escolhido no portal ou na
ligação da Francisca); o do gestor, de gestores.idioma. Português é o padrão.
"""
import html as _html
import json
import os

srv = None  # módulo server, injetado por ligar()

IDIOMAS = ("pt", "en", "es")

T = {
    "pt": {
        "acessar": "Acessar",
        "botao_falhou": "Se o botão não funcionar, copie e cole no navegador:",
        "rodape_empresa": "{empresa} · seleção com a plataforma Bússola",
        "rodape": "Bússola · metodologia B.A.S.E. e curadoria Tony Belleza",
        "subtitulo": "Recrutamento e Seleção",
        "equipe": "Equipe de Seleção",
        "assinatura": "Atenciosamente,\nEquipe {empresa}",
        # resultado do candidato
        "res_assunto": "Seus resultados: perfil DISC e B.A.S.E.",
        "res_titulo": "Avaliação concluída",
        "res_ola": "Olá, {nome}!",
        "res_intro": "Obrigado por concluir a sua avaliação para {vaga}. Aqui está um resumo do seu perfil. O relatório completo segue em anexo, em PDF.",
        "res_proximos": "E agora? A equipe da {empresa} vai analisar a sua candidatura e falar com você sobre os próximos passos.",
        "res_link": "Você pode rever os seus resultados quando quiser pelo seu link pessoal:",
        "res_pdf": "resultados.pdf",
        "disc_titulo": "Seu perfil comportamental DISC",
        "disc_dominante": "Estilo principal: {nome}",
        "base_titulo": "Seu código de personalidade B.A.S.E.",
        "base_codigo": "Código {codigo}",
        "base_principal": "Arquétipo principal: {nome}",
        "base_complemento": "Complementado por {nome}.",
        # aviso aos gestores
        "g_assunto": "Candidato pronto: {nome} ({vaga})",
        "g_assunto_pendente": "Triagem aprovada, testes pendentes: {nome} ({vaga})",
        "g_titulo": "Candidato pronto para análise",
        "g_titulo_pendente": "Testes ainda não concluídos",
        "g_intro": "{nome} concluiu toda a avaliação para {vaga}.",
        "g_intro_pendente": "{nome} passou na triagem por voz para {vaga}, mas ainda não concluiu os testes. O convite foi enviado há mais de 48 horas.",
        "g_contato": "Contato",
        "g_cidade": "Cidade",
        "g_telefone": "Telefone",
        "g_email": "E-mail",
        "g_idioma": "Idioma",
        "g_voz": "Triagem por voz (Francisca)",
        "g_voz_pontos": "{tier} · {score} de 100 pontos",
        "g_voz_janelas": "Disponibilidade para entrevista",
        "g_voz_resumo": "Resumo da ligação",
        "g_match": "Match com o cargo {cargo}",
        "g_testes_pendentes": "DISC e B.A.S.E. ainda não respondidos.",
        "g_disc_titulo": "Perfil DISC",
        "g_base_titulo": "Código B.A.S.E.",
        "g_botao": "Abrir a ficha no painel",
        "idiomas": {"pt": "Português", "en": "Inglês", "es": "Espanhol"},
        "componentes": {"competencias": "Competências", "disc": "DISC", "base": "B.A.S.E.",
                        "conhecimento": "Conhecimento", "entrevista": "Entrevista", "voz": "Triagem por voz"},
        # PDF
        "pdf_relatorio": "RELATÓRIO DE AVALIAÇÃO",
        "pdf_sem_cargo": "Sem cargo de interesse",
        "pdf_match": "MATCH GERAL",
        "pdf_disc": "Perfil comportamental DISC",
        "pdf_disc_dom": "Perfil dominante: {nome}",
        "pdf_base": "Código de personalidade B.A.S.E.",
        "pdf_codigo": "Código: {codigo}",
        "pdf_arquetipo": "Arquétipo dominante: {a}. Complementado por {b}.",
        "pdf_gaps": "Matriz de gaps: aderência ao cargo",
        "pdf_aderencia": "{pct}% de aderência",
        "pdf_competencia": "COMPETÊNCIA",
        "pdf_exigido": "EXIGIDO",
        "pdf_atual": "ATUAL",
        "pdf_gap": "GAP",
        "data": "{dia} de {mes} de {ano}",
        "meses": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                  "agosto", "setembro", "outubro", "novembro", "dezembro"],
    },
    "en": {
        "acessar": "Open",
        "botao_falhou": "If the button doesn't work, copy and paste this link into your browser:",
        "rodape_empresa": "{empresa} · hiring powered by Bússola",
        "rodape": "Bússola · B.A.S.E. methodology by Tony Belleza",
        "subtitulo": "Recruiting and Hiring",
        "equipe": "Hiring Team",
        "assinatura": "Best regards,\nThe {empresa} team",
        "res_assunto": "Your results: DISC and B.A.S.E. profile",
        "res_titulo": "Assessment complete",
        "res_ola": "Hi {nome}!",
        "res_intro": "Thank you for completing your assessment for {vaga}. Here is a summary of your profile. Your full report is attached as a PDF.",
        "res_proximos": "What's next? The {empresa} team will review your application and reach out about the next steps.",
        "res_link": "You can review your results anytime with your personal link:",
        "res_pdf": "results.pdf",
        "disc_titulo": "Your DISC behavioral profile",
        "disc_dominante": "Main style: {nome}",
        "base_titulo": "Your B.A.S.E. personality code",
        "base_codigo": "Code {codigo}",
        "base_principal": "Main archetype: {nome}",
        "base_complemento": "Complemented by {nome}.",
        "g_assunto": "Candidate ready: {nome} ({vaga})",
        "g_assunto_pendente": "Passed screening, tests pending: {nome} ({vaga})",
        "g_titulo": "Candidate ready for review",
        "g_titulo_pendente": "Tests not completed yet",
        "g_intro": "{nome} completed the full assessment for {vaga}.",
        "g_intro_pendente": "{nome} passed the phone screening for {vaga} but has not completed the tests yet. The invitation was sent more than 48 hours ago.",
        "g_contato": "Contact",
        "g_cidade": "Town",
        "g_telefone": "Phone",
        "g_email": "Email",
        "g_idioma": "Language",
        "g_voz": "Phone screening (Francisca)",
        "g_voz_pontos": "{tier} · {score} out of 100 points",
        "g_voz_janelas": "Interview availability",
        "g_voz_resumo": "Call summary",
        "g_match": "Match with {cargo}",
        "g_testes_pendentes": "DISC and B.A.S.E. not answered yet.",
        "g_disc_titulo": "DISC profile",
        "g_base_titulo": "B.A.S.E. code",
        "g_botao": "Open the candidate in the panel",
        "idiomas": {"pt": "Portuguese", "en": "English", "es": "Spanish"},
        "componentes": {"competencias": "Skills", "disc": "DISC", "base": "B.A.S.E.",
                        "conhecimento": "Knowledge", "entrevista": "Interview", "voz": "Phone screening"},
        "pdf_relatorio": "ASSESSMENT REPORT",
        "pdf_sem_cargo": "No position selected",
        "pdf_match": "OVERALL MATCH",
        "pdf_disc": "DISC behavioral profile",
        "pdf_disc_dom": "Main style: {nome}",
        "pdf_base": "B.A.S.E. personality code",
        "pdf_codigo": "Code: {codigo}",
        "pdf_arquetipo": "Main archetype: {a}. Complemented by {b}.",
        "pdf_gaps": "Skills gap matrix: fit for the role",
        "pdf_aderencia": "{pct}% fit",
        "pdf_competencia": "SKILL",
        "pdf_exigido": "REQUIRED",
        "pdf_atual": "CURRENT",
        "pdf_gap": "GAP",
        "data": "{mes} {dia}, {ano}",
        "meses": ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December"],
    },
    "es": {
        "acessar": "Abrir",
        "botao_falhou": "Si el botón no funciona, copia y pega este enlace en tu navegador:",
        "rodape_empresa": "{empresa} · selección con la plataforma Bússola",
        "rodape": "Bússola · metodología B.A.S.E. de Tony Belleza",
        "subtitulo": "Reclutamiento y Selección",
        "equipe": "Equipo de Selección",
        "assinatura": "Saludos,\nEquipo de {empresa}",
        "res_assunto": "Tus resultados: perfil DISC y B.A.S.E.",
        "res_titulo": "Evaluación completada",
        "res_ola": "¡Hola, {nome}!",
        "res_intro": "Gracias por completar tu evaluación para {vaga}. Aquí tienes un resumen de tu perfil. El informe completo va adjunto en PDF.",
        "res_proximos": "¿Y ahora? El equipo de {empresa} revisará tu solicitud y se comunicará contigo sobre los próximos pasos.",
        "res_link": "Puedes ver tus resultados cuando quieras con tu enlace personal:",
        "res_pdf": "resultados.pdf",
        "disc_titulo": "Tu perfil de comportamiento DISC",
        "disc_dominante": "Estilo principal: {nome}",
        "base_titulo": "Tu código de personalidad B.A.S.E.",
        "base_codigo": "Código {codigo}",
        "base_principal": "Arquetipo principal: {nome}",
        "base_complemento": "Complementado por {nome}.",
        "g_assunto": "Candidato listo: {nome} ({vaga})",
        "g_assunto_pendente": "Aprobó la llamada, pruebas pendientes: {nome} ({vaga})",
        "g_titulo": "Candidato listo para revisión",
        "g_titulo_pendente": "Pruebas aún no completadas",
        "g_intro": "{nome} completó toda la evaluación para {vaga}.",
        "g_intro_pendente": "{nome} aprobó la entrevista telefónica para {vaga}, pero aún no completó las pruebas. La invitación se envió hace más de 48 horas.",
        "g_contato": "Contacto",
        "g_cidade": "Ciudad",
        "g_telefone": "Teléfono",
        "g_email": "Correo",
        "g_idioma": "Idioma",
        "g_voz": "Entrevista telefónica (Francisca)",
        "g_voz_pontos": "{tier} · {score} de 100 puntos",
        "g_voz_janelas": "Disponibilidad para entrevista",
        "g_voz_resumo": "Resumen de la llamada",
        "g_match": "Compatibilidad con {cargo}",
        "g_testes_pendentes": "DISC y B.A.S.E. aún sin responder.",
        "g_disc_titulo": "Perfil DISC",
        "g_base_titulo": "Código B.A.S.E.",
        "g_botao": "Abrir la ficha en el panel",
        "idiomas": {"pt": "Portugués", "en": "Inglés", "es": "Español"},
        "componentes": {"competencias": "Competencias", "disc": "DISC", "base": "B.A.S.E.",
                        "conhecimento": "Conocimiento", "entrevista": "Entrevista", "voz": "Entrevista telefónica"},
        "pdf_relatorio": "INFORME DE EVALUACIÓN",
        "pdf_sem_cargo": "Sin puesto de interés",
        "pdf_match": "COMPATIBILIDAD",
        "pdf_disc": "Perfil de comportamiento DISC",
        "pdf_disc_dom": "Estilo principal: {nome}",
        "pdf_base": "Código de personalidad B.A.S.E.",
        "pdf_codigo": "Código: {codigo}",
        "pdf_arquetipo": "Arquetipo principal: {a}. Complementado por {b}.",
        "pdf_gaps": "Matriz de brechas: adecuación al puesto",
        "pdf_aderencia": "{pct}% de adecuación",
        "pdf_competencia": "COMPETENCIA",
        "pdf_exigido": "REQUERIDO",
        "pdf_atual": "ACTUAL",
        "pdf_gap": "BRECHA",
        "data": "{dia} de {mes} de {ano}",
        "meses": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                  "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    },
}

# Nomes de reserva, caso o arquivo de perfis do portal não esteja disponível.
PERFIS_RESERVA = {
    "pt": {"DISC": {"D": "Dominância", "I": "Influência", "S": "Estabilidade", "C": "Conformidade"},
           "BASE": {"B": "Bússola", "A": "Atuante", "S": "Sensível", "E": "Estudioso"}},
    "en": {"DISC": {"D": "Dominance", "I": "Influence", "S": "Steadiness", "C": "Conscientiousness"},
           "BASE": {"B": "B", "A": "A", "S": "S", "E": "E"}},
    "es": {"DISC": {"D": "Dominancia", "I": "Influencia", "S": "Estabilidad", "C": "Cumplimiento"},
           "BASE": {"B": "B", "A": "A", "S": "S", "E": "E"}},
}

CORES_DISC = {"D": "#3B67CA", "I": "#9BB9DD", "S": "#7695B4", "C": "#5E7086"}
CORES_BASE = {"B": "#3B67CA", "A": "#E05C2E", "S": "#2EA87B", "E": "#8B5CF6"}

# Modelos padrão dos e-mails ao candidato em inglês e espanhol (o português
# fica em server.TEMPLATES_PADRAO). Cada empresa pode personalizar todos.
TEMPLATES_I18N = {
    "confirmacao_en": {
        "assunto": "Application received: {vaga}",
        "corpo": ("Hi {nome}!\n\nYour application for \"{vaga}\" was received.\n\n"
                  "This is your personal access link. Keep it: you can use it on any device to "
                  "continue your assessment and see your results:\n\n{link}\n\n"
                  "Best regards,\nHiring Team"),
    },
    "confirmacao_es": {
        "assunto": "Solicitud recibida: {vaga}",
        "corpo": ("¡Hola, {nome}!\n\nRecibimos tu solicitud para \"{vaga}\".\n\n"
                  "Este es tu enlace personal de acceso. Guárdalo: con él puedes continuar tu "
                  "evaluación y ver tus resultados desde cualquier dispositivo:\n\n{link}\n\n"
                  "Saludos,\nEquipo de Selección"),
    },
    "lembrete_en": {
        "assunto": "Almost done: finish your assessment",
        "corpo": ("Hi {nome}!\n\nYou started your assessment for \"{vaga}\" but some steps are "
                  "still missing. They only take a few minutes and are an important part of "
                  "your application.\n\nPick up where you left off with your personal link:\n\n"
                  "{link}\n\nBest regards,\nHiring Team"),
    },
    "lembrete_es": {
        "assunto": "Falta poco: termina tu evaluación",
        "corpo": ("¡Hola, {nome}!\n\nComenzaste tu evaluación para \"{vaga}\" y todavía faltan "
                  "algunos pasos. Toman pocos minutos y son importantes para tu solicitud.\n\n"
                  "Continúa donde lo dejaste con tu enlace personal:\n\n{link}\n\n"
                  "Saludos,\nEquipo de Selección"),
    },
    "etapa_inscrito_en": {
        "assunto": "Update on your application: {vaga}",
        "corpo": "Hi {nome}!\n\nYour application for \"{vaga}\" has been registered.\n\nBest regards,\nHiring Team",
    },
    "etapa_inscrito_es": {
        "assunto": "Novedades de tu solicitud: {vaga}",
        "corpo": "¡Hola, {nome}!\n\nTu solicitud para \"{vaga}\" quedó registrada.\n\nSaludos,\nEquipo de Selección",
    },
    "etapa_avaliacoes_en": {
        "assunto": "Update on your application: {vaga}",
        "corpo": "Hi {nome}!\n\nYour application for \"{vaga}\" moved to the assessment stage.\n\nBest regards,\nHiring Team",
    },
    "etapa_avaliacoes_es": {
        "assunto": "Novedades de tu solicitud: {vaga}",
        "corpo": "¡Hola, {nome}!\n\nTu solicitud para \"{vaga}\" pasó a la etapa de evaluaciones.\n\nSaludos,\nEquipo de Selección",
    },
    "etapa_entrevista_en": {
        "assunto": "You've been selected for an interview: {vaga}",
        "corpo": ("Hi {nome}!\n\nGood news: you've been selected for the interview stage for "
                  "\"{vaga}\". We'll contact you soon to schedule it.\n\nBest regards,\nHiring Team"),
    },
    "etapa_entrevista_es": {
        "assunto": "Fuiste seleccionado(a) para una entrevista: {vaga}",
        "corpo": ("¡Hola, {nome}!\n\nBuenas noticias: fuiste seleccionado(a) para la etapa de "
                  "entrevista de \"{vaga}\". Pronto te contactaremos para agendarla.\n\n"
                  "Saludos,\nEquipo de Selección"),
    },
    "etapa_proposta_en": {
        "assunto": "You've moved to the offer stage: {vaga}",
        "corpo": "Hi {nome}!\n\nCongratulations! You've moved to the offer stage for \"{vaga}\".\n\nBest regards,\nHiring Team",
    },
    "etapa_proposta_es": {
        "assunto": "Avanzaste a la etapa de oferta: {vaga}",
        "corpo": "¡Hola, {nome}!\n\n¡Felicidades! Avanzaste a la etapa de oferta de \"{vaga}\".\n\nSaludos,\nEquipo de Selección",
    },
    "etapa_contratado_en": {
        "assunto": "Congratulations, you're hired: {vaga}",
        "corpo": "Hi {nome}!\n\nCongratulations! You were selected for \"{vaga}\". Welcome to the team!\n\nBest regards,\nHiring Team",
    },
    "etapa_contratado_es": {
        "assunto": "¡Felicidades, fuiste contratado(a)!: {vaga}",
        "corpo": "¡Hola, {nome}!\n\n¡Felicidades! Fuiste seleccionado(a) para \"{vaga}\". ¡Bienvenido(a) al equipo!\n\nSaludos,\nEquipo de Selección",
    },
    "etapa_reprovado_en": {
        "assunto": "Update on your application: {vaga}",
        "corpo": ("Hi {nome},\n\nThank you for taking part in the hiring process for \"{vaga}\". "
                  "We won't be moving forward with your application at this time, but your "
                  "profile stays in our talent pool for future openings.\n\nBest regards,\nHiring Team"),
    },
    "etapa_reprovado_es": {
        "assunto": "Novedades de tu solicitud: {vaga}",
        "corpo": ("Hola, {nome}:\n\nGracias por participar en el proceso de \"{vaga}\". Por ahora "
                  "no seguirás en el proceso, pero tu perfil queda en nuestro banco de talentos "
                  "para futuras oportunidades.\n\nSaludos,\nEquipo de Selección"),
    },
}


def ligar(modulo_server):
    global srv
    srv = modulo_server
    srv.TEMPLATES_PADRAO.update(TEMPLATES_I18N)
    for chave in TEMPLATES_I18N:
        base, sufixo = chave.rsplit("_", 1)
        nome = srv.NOMES_TEMPLATES.get(base, base)
        srv.NOMES_TEMPLATES[chave] = "%s (%s)" % (nome, sufixo.upper())


def idioma(valor, padrao="pt"):
    v = (valor or "").strip().lower()[:2]
    return v if v in IDIOMAS else padrao


def t(lang, chave, **kw):
    texto = T[idioma(lang)].get(chave) or T["pt"][chave]
    return texto.format(**kw) if kw and isinstance(texto, str) else texto


def data_extenso(lang, iso):
    ano, mes, dia = iso[:10].split("-")
    return t(lang, "data", dia=int(dia), mes=T[idioma(lang)]["meses"][int(mes) - 1], ano=ano)


_cache_perfis = {}


def perfis(lang):
    """Nomes e resumos dos perfis DISC e B.A.S.E. no idioma pedido, lidos do
    mesmo arquivo de traduções que o portal do candidato usa."""
    lang = idioma(lang)
    caminho = os.path.join(srv.PUBLIC_DIR, "js", "resumo-perfis.json")
    try:
        mtime = os.path.getmtime(caminho)
        if _cache_perfis.get("mtime") != mtime:
            with open(caminho, encoding="utf-8") as f:
                _cache_perfis.update(mtime=mtime, dados=json.load(f))
        dados = _cache_perfis["dados"].get(lang) or {}
    except (OSError, ValueError):
        dados = {}
    reserva = PERFIS_RESERVA[lang]
    saida = {"DISC": {}, "BASE": {}}
    for grupo in ("DISC", "BASE"):
        for letra, nome in reserva[grupo].items():
            item = dict((dados.get(grupo) or {}).get(letra) or {})
            item.setdefault("nome", nome if nome != letra else PERFIS_RESERVA["pt"][grupo][letra])
            saida[grupo][letra] = item
    return saida


# ------------------------------------------------------------- marca da empresa

def marca(conn, empresa_id):
    """Nome e logo da empresa para os e-mails (logo por URL pública)."""
    if not empresa_id:
        return None
    e = conn.execute("SELECT id, nome, slug, logo FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    if not e:
        return None
    logo_url = ""
    if e["logo"] and os.path.isfile(caminho_logo(e["logo"])):
        versao = int(os.path.getmtime(caminho_logo(e["logo"])))
        logo_url = "%s/api/empresa/%s/logo?v=%d" % (srv.url_publica(conn), e["slug"], versao)
    return {"nome": e["nome"], "slug": e["slug"], "logo_url": logo_url, "logo": e["logo"]}


def pasta_logos():
    pasta = os.path.join(srv.UPLOAD_DIR, "logos")
    os.makedirs(pasta, exist_ok=True)
    return pasta


def caminho_logo(arquivo):
    return os.path.join(pasta_logos(), os.path.basename(arquivo or ""))


TIPOS_LOGO = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}


def salvar_logo(conn, empresa_id, nome_arquivo, dados):
    """Grava a logo (PNG ou JPG, até 1 MB). Retorna mensagem de erro ou None.
    SVG não é aceito: a maioria dos leitores de e-mail não mostra SVG."""
    ext = (nome_arquivo or "").rsplit(".", 1)[-1].lower()
    if ext not in TIPOS_LOGO:
        return "Envie a logo em PNG ou JPG"
    if not dados or len(dados) > 1024 * 1024:
        return "A logo deve ter até 1 MB"
    assinatura_ok = dados.startswith(b"\x89PNG") if ext == "png" else dados.startswith(b"\xff\xd8")
    if not assinatura_ok:
        return "Arquivo de imagem inválido"
    antigo = conn.execute("SELECT logo FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    destino = "empresa%d.%s" % (empresa_id, "jpg" if ext == "jpeg" else ext)
    if antigo and antigo["logo"] and antigo["logo"] != destino:
        try:
            os.remove(caminho_logo(antigo["logo"]))
        except OSError:
            pass
    with open(caminho_logo(destino), "wb") as f:
        f.write(dados)
    conn.execute("UPDATE empresas SET logo=? WHERE id=?", (destino, empresa_id))
    conn.commit()
    return None


def remover_logo(conn, empresa_id):
    antigo = conn.execute("SELECT logo FROM empresas WHERE id=?", (empresa_id,)).fetchone()
    if antigo and antigo["logo"]:
        try:
            os.remove(caminho_logo(antigo["logo"]))
        except OSError:
            pass
    conn.execute("UPDATE empresas SET logo='' WHERE id=?", (empresa_id,))
    conn.commit()


# ------------------------------------------------------------- layout do e-mail

HEROIS = [
    # (palavras do assunto, ícone, chave do título, cor)
    (("bem-vind", "welcome", "bienvenid"), "🧭", None, "#3B67CA"),
    (("inscri", "confirmad", "application received", "solicitud recibida"), "🧭", None, "#3B67CA"),
    (("falta pouco", "lembr", "almost done", "falta poco"), "⏳", None, "#C79A3E"),
    (("senha", "password", "contraseña"), "🔒", None, "#5E7086"),
    (("entrevista", "interview"), "📌", None, "#3B67CA"),
]


def _e(texto):
    return _html.escape(texto or "", quote=True)


def _botao(url, rotulo, cor="#3B67CA"):
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:10px 0 18px">'
        '<tr><td style="border-radius:12px;background:%s">'
        '<a href="%s" style="display:inline-block;padding:14px 30px;font-size:15px;'
        'font-weight:700;color:#ffffff;text-decoration:none;border-radius:12px">%s &#8594;</a>'
        '</td></tr></table>' % (cor, _e(url), _e(rotulo))
    )


def html_de_texto(corpo_texto, lang="pt"):
    """Converte o texto simples do modelo em HTML: parágrafos e botões para links."""
    blocos, paragrafo = [], []

    def fecha():
        if paragrafo:
            blocos.append('<p style="margin:0 0 16px;font-size:15px;line-height:1.65;color:#2b3648">'
                          + "<br>".join(_e(x) for x in paragrafo) + "</p>")
            paragrafo.clear()

    for linha in (corpo_texto or "").split("\n"):
        s = linha.strip()
        if s.startswith("http://") or s.startswith("https://"):
            fecha()
            blocos.append(_botao(s, t(lang, "acessar")))
            blocos.append('<p style="margin:0 0 16px;font-size:12px;color:#8a97a8">%s<br>'
                          '<a href="%s" style="color:#3258AB;word-break:break-all">%s</a></p>'
                          % (_e(t(lang, "botao_falhou")), _e(s), _e(s)))
        elif not s:
            fecha()
        else:
            paragrafo.append(linha)
    fecha()
    return "\n".join(blocos)


def layout(conteudo_html, lang="pt", marca_empresa=None, hero=None):
    """Moldura do e-mail. Com marca: cabeçalho branco com a logo da empresa.
    Sem marca: cabeçalho navy da Bússola. hero = (ícone, título, cor) opcional."""
    lang = idioma(lang)
    m = marca_empresa or {}
    if m.get("nome"):
        if m.get("logo_url"):
            identidade = ('<img src="%s" alt="%s" height="56" style="display:block;height:56px;'
                          'max-width:240px;border:0;outline:none">' % (_e(m["logo_url"]), _e(m["nome"])))
        else:
            identidade = ('<div style="font-size:21px;font-weight:700;color:#101B37">%s</div>' % _e(m["nome"]))
        cabecalho = (
            '<tr><td style="background:#ffffff;padding:24px 34px 18px">' + identidade
            + '<div style="font-size:11px;color:#8a97a8;letter-spacing:2px;text-transform:uppercase;'
            'margin-top:8px">' + _e(t(lang, "subtitulo")) + '</div></td></tr>'
        )
        rodape = _e(t(lang, "rodape_empresa", empresa=m["nome"]))
    else:
        cabecalho = (
            '<tr><td style="background:#101B37;padding:26px 34px">'
            '<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
            '<td style="width:40px;height:40px;background:#3B67CA;border-radius:10px;'
            'text-align:center;font-size:22px;line-height:40px">🧭</td>'
            '<td style="padding-left:14px"><div style="font-size:21px;font-weight:700;color:#ffffff">Bússola</div>'
            '<div style="font-size:11px;color:#9BB9DD;letter-spacing:2px;text-transform:uppercase">'
            + _e(t(lang, "subtitulo")) + '</div></td></tr></table></td></tr>'
        )
        rodape = _e(t(lang, "rodape"))
    hero_html = ""
    if hero and hero[1]:
        icone_h, titulo_h, cor_h = hero
        hero_html = (
            '<tr><td style="padding:26px 34px 0;text-align:center">'
            '<div style="display:inline-block;width:64px;height:64px;line-height:64px;border-radius:50%;'
            'font-size:30px;background:' + cor_h + '1f;border:1px solid ' + cor_h + '33">' + icone_h + '</div>'
            '<div style="font-size:20px;font-weight:700;color:#101B37;margin-top:14px">'
            + _e(titulo_h) + '</div></td></tr>'
        )
    return (
        '<!DOCTYPE html><html lang="' + {"pt": "pt-BR", "en": "en", "es": "es"}[lang] + '"><head>'
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
        '<body style="margin:0;padding:0;background:#eef1f6;font-family:Arial,Helvetica,sans-serif">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f6">'
        '<tr><td align="center" style="padding:28px 12px">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="max-width:580px;background:#ffffff;border-radius:18px;overflow:hidden;'
        'box-shadow:0 10px 34px rgba(16,27,55,.10)">'
        + cabecalho +
        '<tr><td style="height:4px;font-size:0;line-height:0;'
        'background:linear-gradient(90deg,#3258AB,#5B84DB,#9BB9DD)">&nbsp;</td></tr>'
        + hero_html +
        '<tr><td style="padding:26px 34px 12px">' + conteudo_html + '</td></tr>'
        '<tr><td style="padding:18px 34px 30px;border-top:1px solid #eef1f6">'
        '<div style="font-size:12px;color:#8a97a8;line-height:1.5">' + rodape + '<br>'
        '<a href="https://rh.tonybelleza.com" style="color:#5E7086;text-decoration:none">rh.tonybelleza.com</a>'
        '</div></td></tr></table></td></tr></table></body></html>'
    )


def hero_do_assunto(assunto):
    alvo = (assunto or "").lower()
    for chaves, icone, _, cor in HEROIS:
        if any(c in alvo for c in chaves):
            return (icone, assunto, cor)
    return None


def html_email(assunto, corpo_texto, lang="pt", marca_empresa=None):
    """E-mail a partir de texto simples (modelos editáveis), com a marca."""
    return layout(html_de_texto(corpo_texto, lang), lang, marca_empresa, hero_do_assunto(assunto))


# ------------------------------------------------------------- blocos de resultado

def _titulo_secao(texto, direita=""):
    return ('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:22px 0 10px">'
            '<tr><td style="font-size:16px;font-weight:700;color:#101B37">' + _e(texto) + '</td>'
            '<td align="right" style="font-size:14px;font-weight:700;color:#3B67CA">' + _e(direita)
            + '</td></tr></table>')


def _barra(rotulo, pct, cor):
    pct = max(0, min(100, int(round(pct or 0))))
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 9px">'
        '<tr><td style="font-size:13px;color:#2b3648;padding-bottom:4px">{rotulo}</td>'
        '<td align="right" style="font-size:13px;font-weight:700;color:{cor};padding-bottom:4px">{pct}%</td></tr>'
        '<tr><td colspan="2"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="background:#eef1f6;border-radius:6px"><tr>'
        '<td width="{largura}%" style="background:{cor};height:9px;border-radius:6px;font-size:0;line-height:0">&nbsp;</td>'
        '<td style="font-size:0;line-height:0">&nbsp;</td></tr></table></td></tr></table>'
    ).format(rotulo=_e(rotulo), cor=cor, pct=pct, largura=max(pct, 2))


def _paragrafo(texto, cor="#2b3648", tamanho=15):
    return ('<p style="margin:0 0 14px;font-size:%dpx;line-height:1.6;color:%s">%s</p>'
            % (tamanho, cor, _e(texto).replace("\n", "<br>")))


def bloco_disc(disc, lang, titulo=None):
    if not disc or not disc.get("pct"):
        return ""
    p = perfis(lang)["DISC"]
    dom = disc.get("dominante") or max(disc["pct"], key=disc["pct"].get)
    partes = [_titulo_secao(titulo or t(lang, "disc_titulo"), "")]
    for k in ("D", "I", "S", "C"):
        partes.append(_barra("%s (%s)" % (p[k]["nome"], k), disc["pct"].get(k, 0), CORES_DISC[k]))
    caixa = ('<div style="background:#f5f7fb;border-radius:12px;padding:14px 16px;margin-top:8px">'
             '<div style="font-size:14px;font-weight:700;color:#101B37;margin-bottom:4px">'
             + _e(t(lang, "disc_dominante", nome=p[dom]["nome"])) + '</div>')
    if p[dom].get("resumo"):
        caixa += '<div style="font-size:13px;line-height:1.55;color:#4a5568">' + _e(p[dom]["resumo"]) + '</div>'
    partes.append(caixa + '</div>')
    return "".join(partes)


def bloco_base(base, lang, titulo=None):
    if not base or not base.get("pct"):
        return ""
    p = perfis(lang)["BASE"]
    pct = base["pct"]
    ordem = base.get("ordem") or sorted(pct, key=lambda k: -pct[k])
    codigo = base.get("codigo") or "".join(ordem)
    celulas = []
    for k in ordem:
        celulas.append(
            '<td width="25%" align="center" style="padding:4px">'
            '<div style="border:1px solid ' + CORES_BASE[k] + '55;border-top:4px solid ' + CORES_BASE[k]
            + ';border-radius:10px;padding:10px 4px;background:' + CORES_BASE[k] + '0f">'
            '<div style="font-size:22px;font-weight:800;color:' + CORES_BASE[k] + '">' + k + '</div>'
            '<div style="font-size:11px;color:#4a5568;margin-top:2px">' + _e(p[k]["nome"]) + '</div>'
            '<div style="font-size:14px;font-weight:700;color:#101B37;margin-top:4px">%d%%</div>'
            '</div></td>' % pct.get(k, 0)
        )
    principal = p[ordem[0]]
    caixa = ('<div style="background:#f5f7fb;border-radius:12px;padding:14px 16px;margin-top:10px">'
             '<div style="font-size:14px;font-weight:700;color:#101B37;margin-bottom:4px">'
             + _e(t(lang, "base_principal", nome=principal["nome"]))
             + (_e(" · " + principal["titulo"]) if principal.get("titulo") else "") + '</div>')
    if principal.get("tagline"):
        caixa += '<div style="font-size:13px;line-height:1.55;color:#4a5568">' + _e(principal["tagline"]) + '</div>'
    if len(ordem) > 1:
        caixa += ('<div style="font-size:13px;color:#4a5568;margin-top:6px">'
                  + _e(t(lang, "base_complemento", nome=p[ordem[1]]["nome"])) + '</div>')
    return (_titulo_secao(titulo or t(lang, "base_titulo"), t(lang, "base_codigo", codigo=codigo))
            + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            + "".join(celulas) + '</tr></table>' + caixa + '</div>')


def _testes(conn, candidato_id):
    return {r["tipo"]: json.loads(r["payload"]) for r in conn.execute(
        "SELECT tipo, payload FROM resultados_teste WHERE candidato_id=?", (candidato_id,)).fetchall()}


def _vaga_do_candidato(conn, cand):
    v = conn.execute(
        "SELECT v.titulo FROM candidaturas ca JOIN vagas v ON v.id=ca.vaga_id"
        " WHERE ca.candidato_id=? ORDER BY ca.criado_em DESC LIMIT 1", (cand["id"],)).fetchone()
    if v:
        return v["titulo"]
    c = conn.execute("SELECT nome FROM cargos WHERE id=?", (cand["cargo_desejado_id"],)).fetchone() \
        if cand["cargo_desejado_id"] else None
    return c["nome"] if c else ""


# ------------------------------------------------------------- e-mail ao candidato

def email_resultado_candidato(conn, cand):
    """(assunto, texto, html, anexos) do e-mail único de resultados, no idioma do candidato."""
    lang = idioma(cand["idioma"] if "idioma" in cand.keys() else "")
    m = marca(conn, cand["empresa_id"])
    empresa = (m or {}).get("nome") or t(lang, "equipe")
    testes = _testes(conn, cand["id"])
    vaga = _vaga_do_candidato(conn, cand) or empresa
    primeiro = (cand["nome"] or "").split(" ")[0]
    link = "%s/candidato?token=%s&lang=%s" % (srv.url_publica(conn), cand["token"], lang)

    texto = [t(lang, "res_ola", nome=primeiro), "", t(lang, "res_intro", vaga=vaga), ""]
    p = perfis(lang)
    if testes.get("disc", {}).get("pct"):
        d = testes["disc"]
        dom = d.get("dominante") or max(d["pct"], key=d["pct"].get)
        texto.append(t(lang, "disc_titulo") + ": " + " · ".join(
            "%s %d%%" % (p["DISC"][k]["nome"], d["pct"].get(k, 0)) for k in "DISC"))
        texto.append(t(lang, "disc_dominante", nome=p["DISC"][dom]["nome"]))
        texto.append("")
    if testes.get("base", {}).get("pct"):
        b = testes["base"]
        ordem = b.get("ordem") or sorted(b["pct"], key=lambda k: -b["pct"][k])
        texto.append(t(lang, "base_titulo") + ": " + (b.get("codigo") or "".join(ordem)))
        texto.append(t(lang, "base_principal", nome=p["BASE"][ordem[0]]["nome"]))
        texto.append("")
    texto += [t(lang, "res_proximos", empresa=empresa), "", t(lang, "res_link"), "", link, "",
              t(lang, "assinatura", empresa=empresa)]
    texto = "\n".join(texto)

    corpo = (_paragrafo(t(lang, "res_ola", nome=primeiro), "#101B37", 17)
             + _paragrafo(t(lang, "res_intro", vaga=vaga))
             + bloco_disc(testes.get("disc"), lang)
             + bloco_base(testes.get("base"), lang)
             + '<div style="height:18px"></div>'
             + _paragrafo(t(lang, "res_proximos", empresa=empresa))
             + _paragrafo(t(lang, "res_link"), "#4a5568", 14)
             + _botao(link, t(lang, "acessar"))
             + _paragrafo(t(lang, "assinatura", empresa=empresa), "#4a5568", 14))
    html = layout(corpo, lang, m, ("✅", t(lang, "res_titulo"), "#2E9E6A"))

    anexos = []
    pdf, erro = srv.gerar_pdf_resultado(conn, cand, idioma_pdf=lang, para_candidato=True)
    if pdf and not erro:
        anexos.append((t(lang, "res_pdf"), pdf, "application/pdf"))
    return t(lang, "res_assunto"), texto, html, anexos


# ------------------------------------------------------------- aviso aos gestores

def _voz_da_candidatura(conn, cand):
    r = conn.execute(
        "SELECT ca.voz_tier, ca.voz_score, ca.voz_outcome, ch.fatos, ch.resumo"
        " FROM candidaturas ca LEFT JOIN voz_chamadas ch ON ch.candidatura_id=ca.id AND ch.status='concluida'"
        " WHERE ca.candidato_id=? AND ca.voz_tier IS NOT NULL AND ca.voz_tier!=''"
        " ORDER BY ch.id DESC LIMIT 1", (cand["id"],)).fetchone()
    if not r:
        return None
    try:
        fatos = json.loads(r["fatos"] or "{}")
    except ValueError:
        fatos = {}
    return {"tier": r["voz_tier"], "score": r["voz_score"], "outcome": r["voz_outcome"],
            "fatos": fatos, "resumo": r["resumo"] or ""}


def _linha(rotulo, valor):
    if not valor:
        return ""
    return ('<tr><td style="padding:5px 0;font-size:13px;color:#8a97a8;width:40%%">%s</td>'
            '<td style="padding:5px 0;font-size:14px;color:#101B37;font-weight:600">%s</td></tr>'
            % (_e(rotulo), _e(str(valor))))


def email_gestor(conn, cand, lang, pendente=False):
    """(assunto, texto, html) do aviso único ao gestor, no idioma dele."""
    lang = idioma(lang)
    m = marca(conn, cand["empresa_id"])
    vaga = _vaga_do_candidato(conn, cand)
    testes = _testes(conn, cand["id"])
    voz = _voz_da_candidatura(conn, cand)
    match, cargo = None, ""
    if cand["cargo_desejado_id"]:
        cargo_row = conn.execute("SELECT nome FROM cargos WHERE id=?", (cand["cargo_desejado_id"],)).fetchone()
        cargo = cargo_row["nome"] if cargo_row else ""
        try:
            match = srv.match_completo(conn, cand, cand["cargo_desejado_id"])
        except Exception:  # noqa: BLE001
            match = None
    link = "%s/gestor#candidato=%d" % (srv.url_publica(conn), cand["id"])
    nome = cand["nome"] or ""
    cidade = (voz or {}).get("fatos", {}).get("city") or cand["local"] or ""
    idioma_cand = t(lang, "idiomas").get(idioma(cand["idioma"] if "idioma" in cand.keys() else "", ""), "")

    assunto = t(lang, "g_assunto_pendente" if pendente else "g_assunto", nome=nome, vaga=vaga or cargo)
    intro = t(lang, "g_intro_pendente" if pendente else "g_intro", nome=nome, vaga=vaga or cargo)
    texto = [intro, ""]
    corpo = [_paragrafo(intro)]

    contato = (_linha(t(lang, "g_cidade"), cidade) + _linha(t(lang, "g_telefone"), cand["telefone"])
               + _linha(t(lang, "g_email"), cand["email"]) + _linha(t(lang, "g_idioma"), idioma_cand))
    corpo.append(_titulo_secao(t(lang, "g_contato")))
    corpo.append('<table role="presentation" width="100%" cellpadding="0" cellspacing="0">' + contato + '</table>')
    texto += ["%s: %s" % (t(lang, "g_cidade"), cidade or "-"), "%s: %s" % (t(lang, "g_telefone"), cand["telefone"] or "-"), ""]

    if match:
        corpo.append(_titulo_secao(t(lang, "g_match", cargo=cargo), "%d%%" % match["geral"]))
        nomes = t(lang, "componentes")
        for k, v in match.get("componentes", {}).items():
            corpo.append(_barra(nomes.get(k, k), v, "#3B67CA"))
        texto.append("%s: %d%%" % (t(lang, "g_match", cargo=cargo), match["geral"]))

    if voz:
        corpo.append(_titulo_secao(t(lang, "g_voz"), voz["tier"] or ""))
        f = voz["fatos"]
        linhas = _linha(t(lang, "g_voz"), t(lang, "g_voz_pontos", tier=voz["tier"], score=voz["score"])
                        if voz["score"] is not None else voz["outcome"])
        linhas += _linha(t(lang, "g_voz_janelas"), f.get("interview_windows"))
        corpo.append('<table role="presentation" width="100%" cellpadding="0" cellspacing="0">' + linhas + '</table>')
        if voz["resumo"]:
            corpo.append('<div style="background:#f5f7fb;border-radius:12px;padding:12px 14px;margin-top:8px;'
                         'font-size:13px;line-height:1.55;color:#4a5568"><strong>' + _e(t(lang, "g_voz_resumo"))
                         + ':</strong> ' + _e(voz["resumo"]) + '</div>')
        texto.append("%s: %s (%s)" % (t(lang, "g_voz"), voz["tier"], voz["score"]))

    if testes.get("disc") or testes.get("base"):
        corpo.append(bloco_disc(testes.get("disc"), lang, t(lang, "g_disc_titulo")))
        corpo.append(bloco_base(testes.get("base"), lang, t(lang, "g_base_titulo")))
    else:
        corpo.append(_paragrafo(t(lang, "g_testes_pendentes"), "#C0392B", 14))
        texto.append(t(lang, "g_testes_pendentes"))

    corpo.append('<div style="height:14px"></div>' + _botao(link, t(lang, "g_botao")))
    texto += ["", link]
    titulo = t(lang, "g_titulo_pendente" if pendente else "g_titulo")
    html = layout("".join(corpo), lang, m, ("⏳" if pendente else "👤", titulo, "#C79A3E" if pendente else "#3B67CA"))
    return assunto, "\n".join(texto), html


def avisar_gestores(conn, cand, pendente=False):
    """Um e-mail por gestor da empresa (que enxerga o candidato), no idioma de cada um."""
    if not srv.config_get(conn, "smtp_host"):
        return 0
    enviados = 0
    for g in conn.execute(
        "SELECT email, local, is_admin, empresa_id, idioma FROM gestores WHERE empresa_id=? AND aprovado=1",
        (cand["empresa_id"],),
    ).fetchall():
        if not (g["email"] or "").strip() or not srv.empresas.ve_local(g, cand["local"]):
            continue
        assunto, texto, html = email_gestor(conn, cand, g["idioma"], pendente)
        ok, _ = srv.enviar_email(conn, g["email"].strip(), assunto, texto, html=html)
        enviados += 1 if ok else 0
    if enviados:
        srv.registrar_evento(conn, cand["id"], "email",
                             "Gestores notificados por e-mail (%d): %s" % (enviados, "testes pendentes" if pendente else "avaliação completa"))
    return enviados
