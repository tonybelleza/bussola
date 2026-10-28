"""Vagas públicas: página de cada vaga pronta para o Google for Jobs, sitemap,
robots.txt e a marca (nome e logo) da empresa nas páginas públicas.

- GET /vaga?id=<id>[&lang=pt|en|es]  página da vaga renderizada no servidor, com
  JSON-LD JobPosting (o Google lê sem JavaScript) e botão de candidatura.
- GET /sitemap.xml                    início, /vagas?e=<slug> de cada empresa com
  vagas abertas e cada vaga aberta, com lastmod.
- GET /robots.txt                     regras para robôs e endereço do sitemap.
- GET /api/empresa/<slug>/marca       {nome, slug, logo_url} da empresa ativa.

Campos extras da vaga (migração em init_vagas_publicas): tipo_emprego, salario_min,
salario_max, salario_unidade, moeda, endereco_cidade, endereco_estado, endereco_cep,
remoto, data_validade, descricao_rica e atualizado_em.

Só são públicas as vagas com status "aberta" de empresas com status ativa ou teste.
O texto livre do roteiro de voz (voz.py) não é lido aqui: o salário vem só dos
campos explícitos da vaga.
"""
import html
import json
import re
import sys
from datetime import date, datetime, timezone
from urllib.parse import urlparse, parse_qs, quote

srv = None  # módulo server, injetado por ligar()

TIPOS_EMPREGO = ("FULL_TIME", "PART_TIME", "CONTRACTOR", "TEMPORARY", "PER_DIEM")
UNIDADES_SALARIO = ("HOUR", "DAY", "WEEK", "MONTH", "YEAR")
IDIOMAS = ("pt", "en", "es")

COLUNAS = (
    ("tipo_emprego", "TEXT DEFAULT ''"),
    ("salario_min", "REAL"),
    ("salario_max", "REAL"),
    ("salario_unidade", "TEXT DEFAULT ''"),
    ("moeda", "TEXT DEFAULT 'USD'"),
    ("endereco_cidade", "TEXT DEFAULT ''"),
    ("endereco_estado", "TEXT DEFAULT ''"),
    ("endereco_cep", "TEXT DEFAULT ''"),
    ("remoto", "INTEGER DEFAULT 0"),
    ("data_validade", "TEXT DEFAULT ''"),
    ("descricao_rica", "TEXT DEFAULT ''"),
    ("atualizado_em", "TEXT DEFAULT ''"),
)

# país da vaga (nomes usados no painel) -> código ISO 3166-1
PAISES_ISO = {
    "Angola": "AO", "Brasil": "BR", "Espanha": "ES",
    "Estados Unidos": "US", "França": "FR", "Portugal": "PT",
}
PAISES_NOMES = {
    "en": {"Angola": "Angola", "Brasil": "Brazil", "Espanha": "Spain",
           "Estados Unidos": "United States", "França": "France", "Portugal": "Portugal"},
    "es": {"Angola": "Angola", "Brasil": "Brasil", "Espanha": "España",
           "Estados Unidos": "Estados Unidos", "França": "Francia", "Portugal": "Portugal"},
}
SIMBOLOS_MOEDA = {"USD": "$", "BRL": "R$", "EUR": "€", "GBP": "£", "CAD": "CA$", "MXN": "MX$"}

TEXTOS = {
    "pt": {
        "html_lang": "pt-BR", "vagas_abertas": "Vagas abertas", "inicio": "Início",
        "candidatar": "Candidatar-se", "ver_todas": "Ver todas as vagas",
        "tipo": "Tipo", "salario": "Salário", "local": "Local", "remoto": "Remoto",
        "valida_ate": "Inscrições até", "publicada": "Publicada em",
        "sobre": "Sobre a vaga", "nao_encontrada": "Vaga não encontrada",
        "nao_encontrada_p": "Esta vaga não está mais aberta ou o link está incorreto.",
        "encerrada": "As inscrições desta vaga já terminaram.",
        "idioma": "Idioma", "a": "a",
        "tipos": {"FULL_TIME": "Tempo integral", "PART_TIME": "Meio período",
                  "CONTRACTOR": "Prestador de serviço", "TEMPORARY": "Temporário",
                  "PER_DIEM": "Por diária"},
        "unidades": {"HOUR": "por hora", "DAY": "por dia", "WEEK": "por semana",
                     "MONTH": "por mês", "YEAR": "por ano"},
    },
    "en": {
        "html_lang": "en", "vagas_abertas": "Open jobs", "inicio": "Home",
        "candidatar": "Apply now", "ver_todas": "See all jobs",
        "tipo": "Job type", "salario": "Pay", "local": "Location", "remoto": "Remote",
        "valida_ate": "Apply by", "publicada": "Posted on",
        "sobre": "About the job", "nao_encontrada": "Job not found",
        "nao_encontrada_p": "This job is no longer open or the link is incorrect.",
        "encerrada": "Applications for this job have closed.",
        "idioma": "Language", "a": "to",
        "tipos": {"FULL_TIME": "Full-time", "PART_TIME": "Part-time",
                  "CONTRACTOR": "Contractor", "TEMPORARY": "Temporary",
                  "PER_DIEM": "Per diem"},
        "unidades": {"HOUR": "per hour", "DAY": "per day", "WEEK": "per week",
                     "MONTH": "per month", "YEAR": "per year"},
    },
    "es": {
        "html_lang": "es", "vagas_abertas": "Vacantes abiertas", "inicio": "Inicio",
        "candidatar": "Postularme", "ver_todas": "Ver todas las vacantes",
        "tipo": "Tipo de empleo", "salario": "Salario", "local": "Ubicación", "remoto": "Remoto",
        "valida_ate": "Postúlate hasta el", "publicada": "Publicada el",
        "sobre": "Sobre la vacante", "nao_encontrada": "Vacante no encontrada",
        "nao_encontrada_p": "Esta vacante ya no está abierta o el enlace es incorrecto.",
        "encerrada": "Las postulaciones para esta vacante ya cerraron.",
        "idioma": "Idioma", "a": "a",
        "tipos": {"FULL_TIME": "Tiempo completo", "PART_TIME": "Medio tiempo",
                  "CONTRACTOR": "Contratista", "TEMPORARY": "Temporal",
                  "PER_DIEM": "Por día"},
        "unidades": {"HOUR": "por hora", "DAY": "por día", "WEEK": "por semana",
                     "MONTH": "por mes", "YEAR": "por año"},
    },
}


def ligar(modulo_server):
    global srv
    srv = modulo_server


def init_vagas_publicas(c):
    existentes = {r[1] for r in c.execute("PRAGMA table_info(vagas)").fetchall()}
    for coluna, ddl in COLUNAS:
        if coluna not in existentes:
            c.execute("ALTER TABLE vagas ADD COLUMN %s %s" % (coluna, ddl))


# ------------------------------------------------------------ campos da vaga

def _numero(valor):
    """None para vazio; float para número; levanta ValueError para texto inválido."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    if isinstance(valor, bool):
        raise ValueError
    n = float(str(valor).replace(",", ".").strip()) if isinstance(valor, str) else float(valor)
    if n < 0 or n != n or n > 1e9:
        raise ValueError
    return n


def _data_valida(texto):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", texto or ""):
        return False
    try:
        date.fromisoformat(texto)
        return True
    except ValueError:
        return False


def validar(d):
    """Mensagem de erro (português, traduzida por erros_i18n) ou None."""
    tipo = (d.get("tipo_emprego") or "").strip().upper()
    if tipo and tipo not in TIPOS_EMPREGO:
        return "Tipo de emprego inválido"
    try:
        smin = _numero(d.get("salario_min"))
        smax = _numero(d.get("salario_max"))
    except (TypeError, ValueError):
        return "Salário inválido"
    if smin is not None and smax is not None and smin > smax:
        return "O salário mínimo não pode ser maior que o máximo"
    unidade = (d.get("salario_unidade") or "").strip().upper()
    if unidade and unidade not in UNIDADES_SALARIO:
        return "Unidade do salário inválida"
    moeda = (d.get("moeda") or "").strip().upper()
    if moeda and not re.match(r"^[A-Z]{3}$", moeda):
        return "Moeda inválida"
    validade = (d.get("data_validade") or "").strip()
    if validade and not _data_valida(validade):
        return "Data de validade inválida"
    return None


def salvar(conn, vaga_id, empresa_id, d):
    """Grava os campos extras presentes em d (campos ausentes ficam como estão).
    Chame depois de validar(d). Sempre marca atualizado_em."""
    sets, valores = [], []

    def por(coluna, valor):
        sets.append("%s=?" % coluna)
        valores.append(valor)

    if "tipo_emprego" in d:
        por("tipo_emprego", (d.get("tipo_emprego") or "").strip().upper())
    for chave in ("salario_min", "salario_max"):
        if chave in d:
            por(chave, _numero(d.get(chave)))
    if "salario_unidade" in d:
        por("salario_unidade", (d.get("salario_unidade") or "").strip().upper())
    if "moeda" in d:
        por("moeda", (d.get("moeda") or "").strip().upper() or "USD")
    for chave, limite in (("endereco_cidade", 100), ("endereco_estado", 60), ("endereco_cep", 20)):
        if chave in d:
            por(chave, (d.get(chave) or "").strip()[:limite])
    if "remoto" in d:
        por("remoto", 1 if d.get("remoto") in (True, 1, "1", "true", "on") else 0)
    if "data_validade" in d:
        por("data_validade", (d.get("data_validade") or "").strip())
    if "descricao_rica" in d:
        por("descricao_rica", (d.get("descricao_rica") or "").strip()[:20000])
    sets.append("atualizado_em=datetime('now')")
    conn.execute("UPDATE vagas SET %s WHERE id=? AND empresa_id=?" % ", ".join(sets),
                 valores + [vaga_id, empresa_id])


def campos(row):
    """Campos extras de uma linha de vagas, para as respostas da API."""
    chaves = row.keys()

    def v(k, padrao=""):
        return row[k] if k in chaves and row[k] is not None else padrao

    return {
        "tipo_emprego": v("tipo_emprego"),
        "salario_min": v("salario_min", None),
        "salario_max": v("salario_max", None),
        "salario_unidade": v("salario_unidade"),
        "moeda": v("moeda") or "USD",
        "endereco_cidade": v("endereco_cidade"),
        "endereco_estado": v("endereco_estado"),
        "endereco_cep": v("endereco_cep"),
        "remoto": bool(v("remoto", 0)),
        "data_validade": v("data_validade"),
        "descricao_rica": v("descricao_rica"),
    }


# ------------------------------------------------------------ marca da empresa

def logo_relativa(conn, empresa_id):
    """Caminho /api/empresa/<slug>/logo?v=... (sem domínio) ou ''."""
    m = srv.mensagens.marca(conn, empresa_id) or {}
    url = m.get("logo_url") or ""
    i = url.find("/api/empresa/")
    return url[i:] if i >= 0 else ""


def marca_publica(conn, empresa_row):
    return {"nome": empresa_row["nome"], "slug": empresa_row["slug"],
            "logo_url": logo_relativa(conn, empresa_row["id"])}


# ------------------------------------------------------------ utilidades

def _esc(texto):
    return html.escape(str(texto or ""), quote=True)


def _base(conn, handler):
    return srv.url_publica(conn, handler.headers.get("Host") if handler else None).rstrip("/")


def _idioma(handler, qs):
    lang = (qs.get("lang", [""])[0] or "").strip().lower()[:2]
    if lang in IDIOMAS:
        return lang, True
    aceito = (handler.headers.get("Accept-Language") or "").lower()
    for parte in aceito.split(","):
        cod = parte.strip()[:2]
        if cod in IDIOMAS:
            return cod, False
    return "en", False


def texto_para_html(texto):
    """Texto simples do gestor -> HTML seguro: parágrafos, quebras e listas com - ou *."""
    blocos = re.split(r"\n\s*\n", (texto or "").replace("\r\n", "\n").strip())
    saida = []
    for bloco in blocos:
        linhas = [l.rstrip() for l in bloco.split("\n") if l.strip()]
        if not linhas:
            continue
        if all(re.match(r"^\s*[-*•]\s+", l) for l in linhas):
            itens = "".join("<li>%s</li>" % _esc(re.sub(r"^\s*[-*•]\s+", "", l)) for l in linhas)
            saida.append("<ul>%s</ul>" % itens)
        else:
            saida.append("<p>%s</p>" % "<br>".join(_esc(l) for l in linhas))
    return "".join(saida)


def _fmt_numero(n, lang):
    inteiro = float(n).is_integer()
    s = "{:,.0f}".format(n) if inteiro else "{:,.2f}".format(n)
    if lang in ("pt", "es"):
        s = s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return s


def texto_salario(v, lang):
    smin, smax = v["salario_min"], v["salario_max"]
    if smin is None and smax is None:
        return ""
    moeda = (v["moeda"] or "USD").upper()
    simbolo = SIMBOLOS_MOEDA.get(moeda, moeda + " ")
    t = TEXTOS[lang]
    if smin is not None and smax is not None and smin != smax:
        valor = "%s%s %s %s%s" % (simbolo, _fmt_numero(smin, lang), t["a"], simbolo, _fmt_numero(smax, lang))
    else:
        valor = "%s%s" % (simbolo, _fmt_numero(smin if smin is not None else smax, lang))
    unidade = t["unidades"].get((v["salario_unidade"] or "").upper(), "")
    return (valor + " " + unidade).strip()


def _data_iso(texto):
    """'YYYY-MM-DD HH:MM:SS' (UTC do SQLite) -> ISO 8601 com fuso."""
    texto = (texto or "").strip()
    if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", texto):
        return texto.replace(" ", "T") + "+00:00"
    return texto[:10]


def _expirada(v):
    validade = v["data_validade"] or ""
    return bool(validade) and _data_valida(validade) and validade < date.today().isoformat()


# ------------------------------------------------------------ consultas

SQL_VAGA = (
    "SELECT v.*, c.nome AS cargo_nome, e.id AS emp_id, e.nome AS empresa_nome,"
    " e.slug AS empresa_slug FROM vagas v JOIN cargos c ON c.id=v.cargo_id"
    " JOIN empresas e ON e.id=v.empresa_id"
    " WHERE v.status='aberta' AND e.status IN ('ativa','teste')"
)


def vaga_publica(conn, vaga_id):
    return conn.execute(SQL_VAGA + " AND v.id=?", (vaga_id,)).fetchone()


def json_ld(conn, r, base):
    """Dicionário JobPosting (schema.org) da vaga."""
    v = campos(r)
    descricao = texto_para_html(v["descricao_rica"] or r["descricao"] or "") or \
        "<p>%s</p>" % _esc("%s, %s" % (r["titulo"], r["empresa_nome"]))
    org = {"@type": "Organization", "name": r["empresa_nome"],
           "sameAs": "%s/vagas?e=%s" % (base, quote(r["empresa_slug"]))}
    logo = logo_relativa(conn, r["emp_id"])
    if logo:
        org["logo"] = base + logo
    pais = PAISES_ISO.get((r["pais"] or "").strip(), "US")
    dados = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": r["titulo"],
        "description": descricao,
        "datePosted": _data_iso(r["criado_em"]),
        "hiringOrganization": org,
        "directApply": True,
        "identifier": {"@type": "PropertyValue", "name": r["empresa_nome"], "value": str(r["id"])},
        "url": "%s/vaga?id=%d" % (base, r["id"]),
    }
    if v["data_validade"] and _data_valida(v["data_validade"]):
        dados["validThrough"] = v["data_validade"] + "T23:59:59"
    if v["tipo_emprego"] in TIPOS_EMPREGO:
        dados["employmentType"] = v["tipo_emprego"]
    endereco = {"@type": "PostalAddress", "addressCountry": pais}
    cidade = v["endereco_cidade"] or (r["local"] or "").strip()
    if cidade:
        endereco["addressLocality"] = cidade
    if v["endereco_estado"]:
        endereco["addressRegion"] = v["endereco_estado"]
    if v["endereco_cep"]:
        endereco["postalCode"] = v["endereco_cep"]
    if v["remoto"]:
        dados["jobLocationType"] = "TELECOMMUTE"
        dados["applicantLocationRequirements"] = {"@type": "Country", "name": pais}
    if not v["remoto"] or cidade:
        dados["jobLocation"] = {"@type": "Place", "address": endereco}
    smin, smax = v["salario_min"], v["salario_max"]
    if smin is not None or smax is not None:
        valor = {"@type": "QuantitativeValue"}
        if smin is not None and smax is not None and smin != smax:
            valor["minValue"] = smin
            valor["maxValue"] = smax
        else:
            valor["value"] = smin if smin is not None else smax
        if v["salario_unidade"] in UNIDADES_SALARIO:
            valor["unitText"] = v["salario_unidade"]
        dados["baseSalary"] = {"@type": "MonetaryAmount", "currency": v["moeda"] or "USD", "value": valor}
    return dados


# ------------------------------------------------------------ respostas

def _responder(handler, status, corpo, tipo, cache="public, max-age=300"):
    dados = corpo.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", tipo)
    handler.send_header("Content-Length", str(len(dados)))
    handler.send_header("Cache-Control", cache)
    handler.end_headers()
    handler.wfile.write(dados)


ESTILO = (
    ".seletor-idioma{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;margin-right:6px}"
    ".seletor-idioma a{color:var(--text-2);font-size:.72rem;font-weight:600;letter-spacing:.05em;padding:6px 9px;line-height:1;text-decoration:none}"
    ".seletor-idioma a:hover{color:var(--text)}"
    ".seletor-idioma a.ativo{background:var(--surface-2);color:var(--text)}"
    ".marca-empresa{display:flex;align-items:center;gap:14px;margin-bottom:18px}"
    ".marca-empresa img{max-height:56px;max-width:160px;border-radius:8px;background:#fff;padding:6px}"
    ".marca-empresa .nome{font-size:1rem;color:var(--text-2)}"
    ".fatos-vaga{display:flex;flex-wrap:wrap;gap:8px 22px;margin:14px 0 4px;font-size:.88rem;color:var(--text-2)}"
    ".fatos-vaga strong{color:var(--text);font-weight:500}"
    ".texto-vaga{color:var(--text-2);line-height:1.6}.texto-vaga p{margin:0 0 12px}.texto-vaga ul{margin:0 0 12px 20px}"
)


def _pagina(lang, titulo, corpo, cabeca="", caminho_lang=None, robots=""):
    t = TEXTOS[lang]
    seletor = ""
    if caminho_lang:
        seletor = '<div class="seletor-idioma" role="group" aria-label="%s">%s</div>' % (
            _esc(t["idioma"]),
            "".join('<a href="%s" hreflang="%s"%s>%s</a>' % (
                _esc(caminho_lang(cod)), cod, ' class="ativo"' if cod == lang else "", cod.upper())
                for cod in IDIOMAS))
    return (
        '<!DOCTYPE html>\n<html lang="%(hl)s">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>%(titulo)s</title>\n%(robots)s'
        '<link rel="stylesheet" href="/css/style.css">\n<script src="/js/tema.js"></script>\n'
        '<style>%(estilo)s</style>\n%(cabeca)s</head>\n<body>\n'
        '<div class="topbar"><div class="inner"><div class="brand">'
        '<img src="/img/logo-white.svg" alt="Tony Belleza"><div class="sep"></div>'
        '<div><h1>Bússola</h1><div class="sub">%(sub)s</div></div></div>'
        '<div class="actions">%(seletor)s<a class="btn on-dark small" href="/">%(inicio)s</a></div>'
        '</div></div>\n<div class="container narrow">%(corpo)s</div>\n</body>\n</html>\n'
    ) % {"hl": t["html_lang"], "titulo": _esc(titulo), "estilo": ESTILO, "cabeca": cabeca,
         "sub": _esc(t["vagas_abertas"]), "seletor": seletor, "inicio": _esc(t["inicio"]),
         "corpo": corpo, "robots": robots}


def _pagina_404(handler, lang):
    t = TEXTOS[lang]
    corpo = ('<div class="card texto-centro" style="margin-top:40px"><h2>%s</h2>'
             '<p class="desc">%s</p></div>') % (_esc(t["nao_encontrada"]), _esc(t["nao_encontrada_p"]))
    _responder(handler, 404, _pagina(lang, t["nao_encontrada"], corpo,
                                     robots='<meta name="robots" content="noindex">\n'),
               "text/html; charset=utf-8", cache="no-store")


def pagina_vaga(handler, conn, qs):
    lang, lang_na_url = _idioma(handler, qs)
    t = TEXTOS[lang]
    try:
        vaga_id = int((qs.get("id", [""])[0] or "").strip())
    except ValueError:
        return _pagina_404(handler, lang)
    r = vaga_publica(conn, vaga_id)
    if not r:
        return _pagina_404(handler, lang)
    v = campos(r)
    base = _base(conn, handler)
    ref = re.sub(r"[^a-zA-Z0-9]", "", qs.get("ref", [""])[0] or "")
    slug_q = quote(r["empresa_slug"])

    def url_lang(cod):
        return "/vaga?id=%d&lang=%s" % (r["id"], cod)

    candidatar = "/candidato?vaga=%d&e=%s&lang=%s%s" % (r["id"], slug_q, lang, "&ref=" + ref if ref else "")
    todas = "/vagas?e=%s&lang=%s%s" % (slug_q, lang, "&ref=" + ref if ref else "")
    logo = logo_relativa(conn, r["emp_id"])
    expirada = _expirada(v)

    # fatos da vaga
    fatos = []
    tipo = t["tipos"].get(v["tipo_emprego"], "")
    if tipo:
        fatos.append((t["tipo"], tipo))
    partes_local = [p for p in (v["endereco_cidade"] or (r["local"] or "").strip(), v["endereco_estado"]) if p]
    pais_nome = (r["pais"] or "").strip()
    if pais_nome:
        partes_local.append(PAISES_NOMES.get(lang, {}).get(pais_nome, pais_nome))
    local = ", ".join(partes_local)
    if v["remoto"]:
        local = (local + " (" + t["remoto"] + ")") if local else t["remoto"]
    if local:
        fatos.append((t["local"], local))
    salario = texto_salario(v, lang)
    if salario:
        fatos.append((t["salario"], salario))
    if v["data_validade"] and _data_valida(v["data_validade"]):
        fatos.append((t["valida_ate"], v["data_validade"]))
    fatos.append((t["publicada"], (r["criado_em"] or "")[:10]))

    descricao = texto_para_html(v["descricao_rica"] or r["descricao"] or "")
    marca = ('<div class="marca-empresa">%s<span class="nome">%s</span></div>' % (
        '<img src="%s" alt="%s">' % (_esc(logo), _esc(r["empresa_nome"])) if logo else "",
        _esc(r["empresa_nome"])))
    botao = ('<p class="form-erro">%s</p>' % _esc(t["encerrada"]) if expirada else
             '<a class="btn" href="%s">%s</a>' % (_esc(candidatar), _esc(t["candidatar"])))
    corpo = (
        '<div style="padding-top:28px">%(marca)s</div>'
        '<div class="card"><h2 style="font-size:1.5rem;margin-bottom:4px">%(titulo)s</h2>'
        '<div class="desc" style="margin:0">%(cargo)s</div>'
        '<div class="fatos-vaga">%(fatos)s</div>'
        '<div class="linha-acoes" style="margin-top:18px">%(botao)s'
        '<a class="btn secondary" href="%(todas)s">%(ver_todas)s</a></div></div>'
        '%(sobre)s'
    ) % {
        "marca": marca, "titulo": _esc(r["titulo"]), "cargo": _esc(r["cargo_nome"]),
        "fatos": "".join("<span>%s: <strong>%s</strong></span>" % (_esc(a), _esc(b)) for a, b in fatos),
        "botao": botao, "todas": _esc(todas), "ver_todas": _esc(t["ver_todas"]),
        "sobre": ('<div class="card" style="margin-top:16px"><h3 style="margin-bottom:10px">%s</h3>'
                  '<div class="texto-vaga">%s</div></div>' % (_esc(t["sobre"]), descricao)) if descricao else "",
    }
    canonica = base + (url_lang(lang) if lang_na_url else "/vaga?id=%d" % r["id"])
    cabeca = '<link rel="canonical" href="%s">\n' % _esc(canonica)
    cabeca += "".join('<link rel="alternate" hreflang="%s" href="%s">\n' % (cod, _esc(base + url_lang(cod)))
                      for cod in IDIOMAS)
    cabeca += '<link rel="alternate" hreflang="x-default" href="%s">\n' % _esc(base + "/vaga?id=%d" % r["id"])
    resumo = re.sub(r"\s+", " ", v["descricao_rica"] or r["descricao"] or "").strip()[:160]
    if resumo:
        cabeca += '<meta name="description" content="%s">\n' % _esc(resumo)
    cabeca += '<meta property="og:title" content="%s">\n' % _esc("%s | %s" % (r["titulo"], r["empresa_nome"]))
    if logo:
        cabeca += '<meta property="og:image" content="%s">\n' % _esc(base + logo)
    if not expirada:
        # "</" escapado para o JSON não fechar a tag <script>
        ld = json.dumps(json_ld(conn, r, base), ensure_ascii=False).replace("</", "<\\/")
        cabeca += '<script type="application/ld+json">%s</script>\n' % ld
    _responder(handler, 200, _pagina(lang, "%s | %s" % (r["titulo"], r["empresa_nome"]), corpo, cabeca,
                                     caminho_lang=url_lang),
               "text/html; charset=utf-8")


def sitemap(conn, base):
    """XML do sitemap: início, página de vagas de cada empresa e cada vaga aberta."""
    hoje = datetime.now(timezone.utc).date().isoformat()  # mesmo fuso das datas do SQLite
    urls = [(base + "/", hoje)]
    por_empresa = {}
    vagas = []
    for r in conn.execute(SQL_VAGA + " ORDER BY e.slug, v.id").fetchall():
        if _expirada(campos(r)):
            continue
        mod = ((r["atualizado_em"] or "") or (r["criado_em"] or ""))[:10] or hoje
        por_empresa[r["empresa_slug"]] = max(por_empresa.get(r["empresa_slug"], ""), mod)
        vagas.append(("%s/vaga?id=%d" % (base, r["id"]), mod))
    for slug, mod in por_empresa.items():
        urls.append(("%s/vagas?e=%s" % (base, quote(slug)), mod))
    urls.extend(vagas)
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in urls:
        linhas.append("  <url><loc>%s</loc><lastmod>%s</lastmod></url>" % (html.escape(loc, quote=False), mod))
    linhas.append("</urlset>")
    return "\n".join(linhas) + "\n"


def robots(base):
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Allow: /vagas\n"
        "Allow: /vaga\n"
        "Disallow: /api/\n"
        "Disallow: /gestor\n"
        "Disallow: /dono\n"
        "Disallow: /onboarding\n"
        "Disallow: /agendar\n"
        "Disallow: /assinar\n"
        "Disallow: /candidato\n"
        "\n"
        "Sitemap: %s/sitemap.xml\n" % base
    )


# ------------------------------------------------------------ rotas

def rotear_pagina(handler, path):
    """Páginas fora de /api/ (chamado no do_GET antes dos estáticos). True se respondeu."""
    if path not in ("/vaga", "/sitemap.xml", "/robots.txt") and not re.match(r"^/vagas/\d+$", path):
        return False
    conn = srv.db()
    try:
        qs = parse_qs(urlparse(handler.path).query)
        if path == "/robots.txt":
            _responder(handler, 200, robots(_base(conn, handler)), "text/plain; charset=utf-8")
        elif path == "/sitemap.xml":
            _responder(handler, 200, sitemap(conn, _base(conn, handler)), "application/xml; charset=utf-8")
        else:
            m = re.match(r"^/vagas/(\d+)$", path)
            if m:  # endereço alternativo /vagas/<id> redireciona para o canônico
                handler.send_response(301)
                handler.send_header("Location", "/vaga?id=%s" % m.group(1))
                handler.send_header("Content-Length", "0")
                handler.end_headers()
            else:
                pagina_vaga(handler, conn, qs)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("ERRO vagas_publicas: %r\n" % exc)
        _responder(handler, 500, "Erro interno", "text/plain; charset=utf-8", cache="no-store")
    finally:
        conn.close()
    return True


def rotear_publico(h, method, path, conn):
    """API pública: marca da empresa (nome e logo) pelo slug."""
    m = re.match(r"^/api/empresa/([a-z0-9-]+)/marca$", path)
    if method == "GET" and m:
        emp = srv.empresas.por_slug(conn, m.group(1))
        if not emp:
            h._json(404, {"erro": "Empresa não encontrada"})
        else:
            h._json(200, marca_publica(conn, emp))
        return True
    return False
