"""Formulários oficiais de admissão: preenchimento dos PDFs preenchíveis originais.

Formulários suportados (arquivos em docs/forms/):
  w9    IRS Form W-9 (Rev. March 2024)            fw9.pdf
  w4    IRS Form W-4 (2026)                        fw4.pdf
  i9    USCIS Form I-9 (Seção 1 e Seção 2)         i-9.pdf
  ctw4  Connecticut Form CT-W4 (Effective 1/1/2026) ct-w4.pdf

API pública:
  CAMPOS                   dados que o portal de admissão precisa coletar, por formulário
  CAMPOS_EMPREGADOR        dados opcionais preenchidos pela empresa (não pelo candidato)
  CAMPOS_I9_SECAO2         dados da Seção 2 do I-9 (empregador)
  MENSAGENS_ERRO           texto trilíngue de cada motivo de erro devolvido por validar()
  validar(tipo, dados)     lista de códigos de erro "chave:motivo" (lista vazia = ok)
  preencher(tipo, dados, assinatura_png=None, data_assinatura=None, nome_assinatura=None) -> bytes
  preencher_i9_secao2(pdf_bytes, dados_empregador, assinatura_png=None) -> bytes
  mascarar_ssn("123456789") -> "•••-••-6789"

Como funciona:
  * Os valores vão para os campos AcroForm reais (nomes conferidos com pypdf).
  * Cada campo recebe /V e uma aparência (/AP) gerada aqui, e o formulário fica
    com NeedAppearances = true, então o valor aparece em qualquer leitor.
  * W-9 e W-4 da Receita trazem XFA: o XFA é removido para que os leitores usem
    o AcroForm preenchido.
  * O CT-W4 vem criptografado (AES-256, sem senha de abertura). O pypdf usa a
    biblioteca cryptography quando existe; sem ela, este módulo usa um AES em
    Python puro (mais lento só na primeira vez, o modelo aberto fica em memória).
  * A assinatura (PNG) é desenhada com fpdf2 numa página transparente do mesmo
    tamanho e mesclada (merge_page) sobre a linha de assinatura do formulário.

Privacidade: este módulo nunca registra nem imprime SSN ou dados pessoais. As
mensagens de erro trazem só a chave do campo e o motivo.
"""
import datetime
import io
import os
import re
import secrets
import threading
import unicodedata
from decimal import Decimal, InvalidOperation

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    DecodedStreamObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    TextStringObject,
)

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA_FORMS = os.path.join(AQUI, "docs", "forms")
ARQUIVOS = {"w9": "fw9.pdf", "w4": "fw4.pdf", "i9": "i-9.pdf", "ctw4": "ct-w4.pdf"}
TIPOS = tuple(ARQUIVOS)


class ErroFormulario(ValueError):
    """Erro de validação. .erros traz a lista de códigos (sem dados pessoais)."""

    def __init__(self, erros):
        self.erros = list(erros)
        super().__init__("dados_invalidos: " + ", ".join(self.erros))


# ---------------------------------------------------------------------------
# Textos trilíngues
# ---------------------------------------------------------------------------

def _t(pt, en, es):
    return {"pt": pt, "en": en, "es": es}


def _opc(valor, pt, en=None, es=None):
    return {"valor": valor, "rotulo": _t(pt, en if en is not None else pt, es if es is not None else pt)}


ESTADOS_EUA = (
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
    "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM",
    "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA",
    "WV", "WI", "WY", "AS", "GU", "MP", "PR", "VI", "FM", "MH", "PW", "AA", "AE", "AP",
)
_OPC_ESTADOS = [_opc(uf, uf) for uf in ESTADOS_EUA]
# A lista do I-9 é fixa no PDF: sem os códigos militares/ilhas livres, com CAN e MEX.
ESTADOS_I9 = tuple(uf for uf in ESTADOS_EUA if uf not in ("AA", "AE", "AP", "FM", "MH", "PW")) + ("CAN", "MEX")
_OPC_ESTADOS_I9 = [_opc(uf, uf) for uf in ESTADOS_I9]
_OPC_0_10 = [_opc(str(n), str(n)) for n in range(11)]


def _campo(chave, tipo, obrigatorio, rotulo, ajuda, opcoes=None, condicao=None, formato=None):
    c = {"chave": chave, "tipo": tipo, "obrigatorio": bool(obrigatorio), "rotulo": rotulo, "ajuda": ajuda}
    if opcoes is not None:
        c["opcoes"] = opcoes
    if condicao is not None:
        # condicao: {"campo": chave, "valores": [...]} -> mostrar e validar só quando
        # dados[campo] for um dos valores (para checkbox use [True]).
        c["condicao"] = condicao
    if formato is not None:
        c["formato"] = formato  # dica extra para a interface: "email", "telefone", "cep"
    return c


# Campos pessoais repetidos em vários formulários.
def _c_primeiro_nome():
    return _campo("primeiro_nome", "text", True,
                  _t("Primeiro nome", "First name", "Primer nombre"),
                  _t("Escreva igual ao seu cartão do Social Security.",
                     "Write it exactly as on your Social Security card.",
                     "Escríbalo igual que en su tarjeta del Seguro Social."))


def _c_inicial():
    return _campo("inicial_meio", "text", False,
                  _t("Inicial do nome do meio (se tiver)", "Middle initial (if any)",
                     "Inicial del segundo nombre (si tiene)"),
                  _t("Só a primeira letra. Deixe em branco se não tiver.",
                     "Just the first letter. Leave blank if you do not have one.",
                     "Solo la primera letra. Déjelo en blanco si no tiene."))


def _c_sobrenome():
    return _campo("sobrenome", "text", True,
                  _t("Sobrenome", "Last name", "Apellido"),
                  _t("Seu sobrenome de família, igual ao cartão do Social Security.",
                     "Your family name, as on your Social Security card.",
                     "Su apellido, igual que en su tarjeta del Seguro Social."))


def _c_endereco():
    return _campo("endereco", "text", True,
                  _t("Endereço (número e rua)", "Address (number and street)", "Dirección (número y calle)"),
                  _t("Onde você mora hoje. Exemplo: 123 Main St.",
                     "Where you live now. Example: 123 Main St.",
                     "Donde vive ahora. Ejemplo: 123 Main St."))


def _c_apto():
    return _campo("apto", "text", False,
                  _t("Apartamento (se tiver)", "Apartment (if any)", "Apartamento (si tiene)"),
                  _t("Número do apartamento ou unidade.", "Apartment or unit number.",
                     "Número de apartamento o unidad."))


def _c_cidade():
    return _campo("cidade", "text", True, _t("Cidade", "City", "Ciudad"),
                  _t("Cidade onde você mora.", "City where you live.", "Ciudad donde vive."))


def _c_estado(opcoes=None):
    return _campo("estado", "select", True, _t("Estado", "State", "Estado"),
                  _t("Sigla do estado. Exemplo: CT.", "State abbreviation. Example: CT.",
                     "Abreviatura del estado. Ejemplo: CT."), opcoes=opcoes or _OPC_ESTADOS)


def _c_cep():
    return _campo("cep", "text", True, _t("ZIP code (CEP)", "ZIP code", "Código postal (ZIP)"),
                  _t("5 números. Exemplo: 06902.", "5 digits. Example: 06902.", "5 números. Ejemplo: 06902."),
                  formato="cep")


def _c_ssn(obrigatorio=True, ajuda=None):
    return _campo("ssn", "ssn", obrigatorio,
                  _t("Número do Social Security (SSN)", "Social Security number (SSN)",
                     "Número de Seguro Social (SSN)"),
                  ajuda or _t("9 números, está no seu cartão do Social Security. Fica protegido no sistema.",
                              "9 digits, on your Social Security card. It is kept protected.",
                              "9 números, está en su tarjeta del Seguro Social. Se guarda protegido."))


_AJUDA_DINHEIRO = _t("Valor em dólares, por ano. Deixe em branco se não se aplica.",
                     "Amount in dollars, per year. Leave blank if it does not apply.",
                     "Cantidad en dólares, por año. Déjelo en blanco si no aplica.")

CAMPOS = {
    # ------------------------------------------------------------------ W-9
    "w9": [
        _campo("nome", "text", True,
               _t("Nome (linha 1)", "Name (line 1)", "Nombre (línea 1)"),
               _t("Seu nome completo, igual à sua declaração de imposto. Se você trabalha por conta "
                  "própria, coloque o seu nome aqui e o nome da empresa na linha 2.",
                  "Your full name as shown on your tax return. If you work for yourself, put your "
                  "name here and your business name on line 2.",
                  "Su nombre completo, igual que en su declaración de impuestos. Si trabaja por su "
                  "cuenta, ponga su nombre aquí y el nombre de su negocio en la línea 2.")),
        _campo("nome_empresa", "text", False,
               _t("Nome da empresa (linha 2, se tiver)", "Business name (line 2, if any)",
                  "Nombre del negocio (línea 2, si tiene)"),
               _t("Só se você tem um nome de negócio diferente do seu nome.",
                  "Only if you have a business name different from your own name.",
                  "Solo si tiene un nombre de negocio distinto de su nombre.")),
        _campo("classificacao", "select", True,
               _t("Tipo de contribuinte (linha 3a)", "Federal tax classification (line 3a)",
                  "Clasificación tributaria federal (línea 3a)"),
               _t("A maioria das pessoas escolhe \"Pessoa física / autônomo\".",
                  "Most people choose \"Individual / sole proprietor\".",
                  "La mayoría de las personas elige \"Persona individual / trabajador por cuenta propia\"."),
               opcoes=[
                   _opc("individual", "Pessoa física / autônomo (ou LLC de um dono só)",
                        "Individual / sole proprietor (or single-member LLC)",
                        "Persona individual / por cuenta propia (o LLC de un solo dueño)"),
                   _opc("c_corp", "Corporação C", "C corporation", "Corporación C"),
                   _opc("s_corp", "Corporação S", "S corporation", "Corporación S"),
                   _opc("partnership", "Sociedade (partnership)", "Partnership", "Sociedad (partnership)"),
                   _opc("trust", "Trust / espólio", "Trust/estate", "Fideicomiso / patrimonio"),
                   _opc("llc", "LLC (empresa de responsabilidade limitada)", "Limited liability company (LLC)",
                        "LLC (compañía de responsabilidad limitada)"),
                   _opc("outro", "Outro", "Other", "Otro"),
               ]),
        _campo("llc_classificacao", "select", True,
               _t("Como a LLC é tributada", "LLC tax classification", "Cómo tributa la LLC"),
               _t("C = corporação C, S = corporação S, P = sociedade. LLC de um dono só deve escolher "
                  "\"Pessoa física\" acima.",
                  "C = C corporation, S = S corporation, P = partnership. A single-member LLC should "
                  "choose \"Individual\" above.",
                  "C = corporación C, S = corporación S, P = sociedad. Una LLC de un solo dueño debe "
                  "elegir \"Persona individual\" arriba."),
               opcoes=[_opc("C", "C"), _opc("S", "S"), _opc("P", "P")],
               condicao={"campo": "classificacao", "valores": ["llc"]}),
        _campo("outro_descricao", "text", True,
               _t("Descreva o tipo", "Describe the type", "Describa el tipo"),
               _t("Escreva o tipo de entidade.", "Write the type of entity.", "Escriba el tipo de entidad."),
               condicao={"campo": "classificacao", "valores": ["outro"]}),
        _campo("socios_estrangeiros", "checkbox", False,
               _t("Tem sócios, donos ou beneficiários estrangeiros (linha 3b)",
                  "Has foreign partners, owners, or beneficiaries (line 3b)",
                  "Tiene socios, dueños o beneficiarios extranjeros (línea 3b)"),
               _t("Só para sociedade, trust ou LLC tributada como sociedade.",
                  "Only for a partnership, trust, or LLC taxed as a partnership.",
                  "Solo para sociedad, fideicomiso o LLC que tributa como sociedad."),
               condicao={"campo": "classificacao", "valores": ["partnership", "trust", "llc"]}),
        _campo("codigo_isencao", "text", False,
               _t("Código de isenção (se tiver)", "Exempt payee code (if any)", "Código de beneficiario exento (si tiene)"),
               _t("Pessoas físicas quase nunca têm. Deixe em branco.",
                  "Individuals almost never have one. Leave blank.",
                  "Las personas individuales casi nunca tienen. Déjelo en blanco.")),
        _campo("codigo_fatca", "text", False,
               _t("Código FATCA (se tiver)", "FATCA exemption code (if any)", "Código de exención FATCA (si tiene)"),
               _t("Só para contas fora dos EUA. Deixe em branco.",
                  "Only for accounts outside the U.S. Leave blank.",
                  "Solo para cuentas fuera de EE. UU. Déjelo en blanco.")),
        _c_endereco(), _c_apto(), _c_cidade(), _c_estado(), _c_cep(),
        _campo("numeros_conta", "text", False,
               _t("Números de conta (opcional)", "Account numbers (optional)", "Números de cuenta (opcional)"),
               _t("Normalmente fica em branco.", "Usually left blank.", "Normalmente se deja en blanco.")),
        _campo("tipo_tin", "select", True,
               _t("Qual número você vai usar", "Which number will you use", "Qué número va a usar"),
               _t("Pessoa física usa o SSN (ou ITIN). Empresa usa o EIN.",
                  "Individuals use their SSN (or ITIN). Businesses use their EIN.",
                  "Las personas usan su SSN (o ITIN). Los negocios usan su EIN."),
               opcoes=[_opc("ssn", "SSN ou ITIN", "SSN or ITIN", "SSN o ITIN"),
                       _opc("ein", "EIN (número da empresa)", "EIN (business number)", "EIN (número del negocio)")]),
        _campo("ssn", "ssn", True,
               _t("SSN ou ITIN", "SSN or ITIN", "SSN o ITIN"),
               _t("9 números. Fica protegido no sistema.", "9 digits. It is kept protected.",
                  "9 números. Se guarda protegido."),
               condicao={"campo": "tipo_tin", "valores": ["ssn"]}),
        _campo("ein", "ein", True,
               _t("EIN (número da empresa)", "Employer identification number (EIN)",
                  "Número de identificación del empleador (EIN)"),
               _t("9 números, dado pelo IRS para a empresa.", "9 digits, issued by the IRS to the business.",
                  "9 números, dado por el IRS al negocio."),
               condicao={"campo": "tipo_tin", "valores": ["ein"]}),
    ],
    # ------------------------------------------------------------------ W-4 (2026)
    "w4": [
        _c_primeiro_nome(), _c_inicial(), _c_sobrenome(),
        _c_endereco(), _c_apto(), _c_cidade(), _c_estado(), _c_cep(),
        _c_ssn(True, _t("9 números. O nome acima precisa ser igual ao do seu cartão do Social Security.",
                        "9 digits. Your name above must match your Social Security card.",
                        "9 números. Su nombre arriba debe ser igual al de su tarjeta del Seguro Social.")),
        _campo("estado_civil", "select", True,
               _t("Situação para o imposto (Passo 1c)", "Filing status (Step 1c)", "Estado civil para impuestos (Paso 1c)"),
               _t("Escolha como você vai declarar o imposto deste ano.",
                  "Choose how you will file your tax return this year.",
                  "Elija cómo va a presentar su declaración de impuestos este año."),
               opcoes=[
                   _opc("solteiro", "Solteiro(a) ou casado(a) declarando separado",
                        "Single or Married filing separately", "Soltero(a) o casado(a) declarando por separado"),
                   _opc("casado_conjunto", "Casado(a) declarando junto, ou viúvo(a) com dependente",
                        "Married filing jointly or Qualifying surviving spouse",
                        "Casado(a) declarando en conjunto, o cónyuge sobreviviente calificado"),
                   _opc("chefe_familia", "Chefe de família (solteiro que paga mais da metade da casa para alguém dependente)",
                        "Head of household (unmarried and pay more than half the costs of keeping up a home for a qualifying person)",
                        "Cabeza de familia (soltero que paga más de la mitad de los gastos del hogar para una persona dependiente)"),
               ]),
        _campo("multiplos_empregos", "checkbox", False,
               _t("Tenho só 2 empregos no total (eu e cônjuge somados) (Passo 2c)",
                  "There are only two jobs total (Step 2c)",
                  "Hay solo dos trabajos en total (Paso 2c)"),
               _t("Marque se você tem dois empregos ao mesmo tempo, ou se é casado(a) declarando junto e os "
                  "dois trabalham, e são só 2 empregos no total. Marque também no W-4 do outro emprego.",
                  "Check if you hold two jobs at a time, or are married filing jointly and both of you work, "
                  "and there are only two jobs total. Check it on the W-4 for the other job too.",
                  "Marque si tiene dos trabajos a la vez, o si está casado(a) declarando en conjunto y los dos "
                  "trabajan, y son solo 2 trabajos en total. Márquelo también en el W-4 del otro trabajo.")),
        _campo("filhos_menores_17", "select", False,
               _t("Filhos com menos de 17 anos (Passo 3a)", "Qualifying children under age 17 (Step 3a)",
                  "Hijos menores de 17 años (Paso 3a)"),
               _t("Quantos filhos menores de 17 anos você vai declarar. Cada um vale $2,200. Só se a sua "
                  "renda total for até $200,000 ($400,000 casados declarando junto).",
                  "How many children under 17 you will claim. Each one is $2,200. Only if your total income "
                  "is $200,000 or less ($400,000 or less if married filing jointly).",
                  "Cuántos hijos menores de 17 años va a declarar. Cada uno vale $2,200. Solo si su ingreso "
                  "total es de $200,000 o menos ($400,000 casados declarando en conjunto)."),
               opcoes=_OPC_0_10),
        _campo("outros_dependentes", "select", False,
               _t("Outros dependentes (Passo 3b)", "Other dependents (Step 3b)", "Otros dependientes (Paso 3b)"),
               _t("Outras pessoas que dependem de você (por exemplo, pais ou filhos com 17 anos ou mais). "
                  "Cada uma vale $500.",
                  "Other people who depend on you (for example, parents or children 17 or older). Each one is $500.",
                  "Otras personas que dependen de usted (por ejemplo, padres o hijos de 17 años o más). "
                  "Cada una vale $500."),
               opcoes=_OPC_0_10),
        _campo("outros_creditos", "money", False,
               _t("Outros créditos de imposto (Passo 3)", "Other credits (Step 3)", "Otros créditos (Paso 3)"),
               _t("Valor de outros créditos, como crédito de educação. Quase sempre fica em branco.",
                  "Amount of other credits, such as education credits. Almost always left blank.",
                  "Cantidad de otros créditos, como créditos de educación. Casi siempre se deja en blanco.")),
        _campo("outra_renda", "money", False,
               _t("Outra renda sem desconto de imposto (Passo 4a)", "Other income, not from jobs (Step 4a)",
                  "Otros ingresos que no son de trabajo (Paso 4a)"),
               _t("Juros, dividendos, aposentadoria. Valor por ano. Deixe em branco se não tem.",
                  "Interest, dividends, retirement income. Yearly amount. Leave blank if none.",
                  "Intereses, dividendos, jubilación. Cantidad por año. Déjelo en blanco si no tiene.")),
        _campo("deducoes", "money", False,
               _t("Deduções (Passo 4b)", "Deductions (Step 4b)", "Deducciones (Paso 4b)"),
               _t("Só se você vai usar deduções acima da dedução padrão (planilha da página 4). "
                  "Quase sempre fica em branco.",
                  "Only if you expect deductions beyond the standard deduction (worksheet on page 4). "
                  "Almost always left blank.",
                  "Solo si espera deducciones mayores que la deducción estándar (hoja de la página 4). "
                  "Casi siempre se deja en blanco.")),
        _campo("retencao_extra", "money", False,
               _t("Desconto extra por pagamento (Passo 4c)", "Extra withholding per pay period (Step 4c)",
                  "Retención adicional por pago (Paso 4c)"),
               _t("Valor a mais que você quer descontar em CADA pagamento. Deixe em branco se não quer.",
                  "Extra amount you want withheld from EACH paycheck. Leave blank if none.",
                  "Cantidad extra que quiere que se retenga de CADA pago. Déjelo en blanco si no quiere.")),
        _campo("isento", "checkbox", False,
               _t("Peço isenção de desconto em 2026", "I claim exemption from withholding for 2026",
                  "Solicito exención de retención para 2026"),
               _t("Só se você não pagou imposto federal em 2025 e espera não pagar em 2026. Se marcar, "
                  "os passos 2 a 4 ficam em branco.",
                  "Only if you had no federal tax liability in 2025 and expect none in 2026. If checked, "
                  "Steps 2 to 4 are left blank.",
                  "Solo si no tuvo obligación de impuesto federal en 2025 y espera no tenerla en 2026. Si lo "
                  "marca, los pasos 2 a 4 quedan en blanco.")),
    ],
    # ------------------------------------------------------------------ CT-W4 (2026)
    "ctw4": [
        _campo("codigo_retencao", "select", True,
               _t("Código de desconto de Connecticut (linha 1)", "Connecticut withholding code (line 1)",
                  "Código de retención de Connecticut (línea 1)"),
               _t("Use a tabela do formulário. Exemplo: solteiro com renda acima de $15,000 por ano = F; "
                  "solteiro até $15,000 = E; chefe de família acima de $19,000 = B. Se não escolher, o "
                  "empregador desconta como D (o maior desconto).",
                  "Use the table on the form. Example: single earning more than $15,000 a year = F; single "
                  "earning $15,000 or less = E; head of household over $19,000 = B. If you do not choose, "
                  "your employer withholds at code D (the highest).",
                  "Use la tabla del formulario. Ejemplo: soltero con ingresos de más de $15,000 al año = F; "
                  "soltero hasta $15,000 = E; cabeza de familia de más de $19,000 = B. Si no elige, el "
                  "empleador retiene con el código D (la mayor retención)."),
               opcoes=[
                   _opc("A", "A: casado(a) junto, cônjuge trabalha, renda do casal entre $24,000 e $100,500",
                        "A: married filing jointly, spouse employed, combined income over $24,000 and under $100,500",
                        "A: casados en conjunto, cónyuge trabaja, ingreso combinado entre $24,000 y $100,500"),
                   _opc("B", "B: chefe de família, renda acima de $19,000",
                        "B: head of household, income over $19,000", "B: cabeza de familia, ingreso de más de $19,000"),
                   _opc("C", "C: casado(a) junto com cônjuge sem emprego e renda acima de $24,000, ou viúvo(a) qualificado com renda acima de $24,000",
                        "C: married filing jointly with spouse not employed and income over $24,000, or qualifying surviving spouse over $24,000",
                        "C: casados en conjunto con cónyuge sin empleo e ingreso de más de $24,000, o cónyuge sobreviviente calificado con más de $24,000"),
                   _opc("D", "D: maior desconto (renda alta do casal, muita renda sem desconto, ou não residente de CT)",
                        "D: highest withholding (high combined income, a lot of nonwage income, or nonresident of CT)",
                        "D: mayor retención (ingreso alto de la pareja, muchos ingresos sin retención, o no residente de CT)"),
                   _opc("E", "E: sem desconto (renda baixa pela tabela, ou isenção MSRRA)",
                        "E: no withholding (low income per the table, or MSRRA exemption)",
                        "E: sin retención (ingreso bajo según la tabla, o exención MSRRA)"),
                   _opc("F", "F: solteiro(a), renda acima de $15,000", "F: single, income over $15,000",
                        "F: soltero(a), ingreso de más de $15,000"),
               ]),
        _campo("retencao_adicional", "money", False,
               _t("Desconto adicional por pagamento (linha 2)", "Additional withholding per pay period (line 2)",
                  "Retención adicional por pago (línea 2)"),
               _t("Valor a mais em CADA pagamento. Deixe em branco se não quer.",
                  "Extra amount from EACH paycheck. Leave blank if none.",
                  "Cantidad extra de CADA pago. Déjelo en blanco si no quiere.")),
        _campo("retencao_reduzida", "money", False,
               _t("Desconto reduzido por pagamento (linha 3)", "Reduced withholding per pay period (line 3)",
                  "Retención reducida por pago (línea 3)"),
               _t("Só se você calculou pelas instruções da página 2. Quase sempre fica em branco.",
                  "Only if you figured it with the page 2 instructions. Almost always left blank.",
                  "Solo si lo calculó con las instrucciones de la página 2. Casi siempre se deja en blanco.")),
        _campo("msrra", "checkbox", False,
               _t("Peço a isenção MSRRA (cônjuge de militar)", "I claim the MSRRA exemption (military spouse)",
                  "Solicito la exención MSRRA (cónyuge de militar)"),
               _t("Só para cônjuge de militar que mora em CT por causa do serviço militar. Use o código E.",
                  "Only for a military spouse living in CT because of military orders. Use code E.",
                  "Solo para cónyuge de militar que vive en CT por órdenes militares. Use el código E.")),
        _campo("estado_residencia", "select", True,
               _t("Estado de residência legal", "State of legal residence/domicile", "Estado de residencia legal"),
               _t("O estado onde você tem domicílio legal.", "The state of your legal residence (domicile).",
                  "El estado de su residencia legal (domicilio)."),
               opcoes=_OPC_ESTADOS, condicao={"campo": "msrra", "valores": [True]}),
        _c_primeiro_nome(), _c_inicial(), _c_sobrenome(),
        _c_ssn(True),
        _c_endereco(), _c_apto(), _c_cidade(), _c_estado(), _c_cep(),
    ],
    # ------------------------------------------------------------------ I-9 Seção 1
    "i9": [
        _c_sobrenome(), _c_primeiro_nome(), _c_inicial(),
        _campo("outros_sobrenomes", "text", False,
               _t("Outros sobrenomes que já usou (se tiver)", "Other last names used (if any)",
                  "Otros apellidos que ha usado (si tiene)"),
               _t("Por exemplo, sobrenome de solteira. Se não tiver, deixe em branco (vamos escrever N/A).",
                  "For example, a maiden name. If none, leave blank (we will write N/A).",
                  "Por ejemplo, apellido de soltera. Si no tiene, déjelo en blanco (escribiremos N/A).")),
        _c_endereco(), _c_apto(), _c_cidade(), _c_estado(_OPC_ESTADOS_I9), _c_cep(),
        _campo("data_nascimento", "date", True,
               _t("Data de nascimento", "Date of birth", "Fecha de nacimiento"),
               _t("Mês, dia e ano.", "Month, day and year.", "Mes, día y año.")),
        _c_ssn(False, _t("Opcional, a não ser que a empresa use E-Verify. 9 números.",
                         "Optional unless the employer uses E-Verify. 9 digits.",
                         "Opcional, a menos que el empleador use E-Verify. 9 números.")),
        _campo("email", "text", False, _t("E-mail (opcional)", "Email (optional)", "Correo electrónico (opcional)"),
               _t("Pode deixar em branco.", "You may leave it blank.", "Puede dejarlo en blanco."), formato="email"),
        _campo("telefone", "text", False, _t("Telefone (opcional)", "Phone number (optional)", "Teléfono (opcional)"),
               _t("Pode deixar em branco.", "You may leave it blank.", "Puede dejarlo en blanco."), formato="telefone"),
        _campo("status_cidadania", "select", True,
               _t("Sua situação nos EUA", "Your citizenship or immigration status", "Su situación en EE. UU."),
               _t("Marque só uma opção. Escolha a que é verdade para você hoje.",
                  "Check only one. Choose the one that is true for you today.",
                  "Marque solo una. Elija la que es verdad para usted hoy."),
               opcoes=[
                   _opc("cidadao", "1. Cidadão dos Estados Unidos", "1. A citizen of the United States",
                        "1. Ciudadano de los Estados Unidos"),
                   _opc("nacional", "2. Nacional dos EUA que não é cidadão (por exemplo, Samoa Americana)",
                        "2. A noncitizen national of the United States", "2. Nacional no ciudadano de los Estados Unidos"),
                   _opc("residente_permanente", "3. Residente permanente (green card)",
                        "3. A lawful permanent resident", "3. Residente permanente legal (green card)"),
                   _opc("autorizado", "4. Estrangeiro com autorização de trabalho (não é residente permanente)",
                        "4. A noncitizen (other than item 3) authorized to work",
                        "4. Extranjero (distinto del punto 3) autorizado para trabajar"),
               ]),
        _campo("residente_numero", "text", True,
               _t("Número USCIS ou A-Number", "USCIS number or A-Number", "Número USCIS o A-Number"),
               _t("Está no seu green card. O A-Number começa com A e tem 7 a 9 números.",
                  "It is on your green card. The A-Number starts with A and has 7 to 9 digits.",
                  "Está en su green card. El A-Number empieza con A y tiene de 7 a 9 números."),
               condicao={"campo": "status_cidadania", "valores": ["residente_permanente"]}),
        _campo("autorizado_ate", "date", False,
               _t("Autorização de trabalho válida até", "Work authorization expiration date",
                  "Autorización de trabajo válida hasta"),
               _t("Data de vencimento da sua autorização. Deixe em branco se não vence (vamos escrever N/A).",
                  "When your authorization ends. Leave blank if it does not expire (we will write N/A).",
                  "Cuándo vence su autorización. Déjelo en blanco si no vence (escribiremos N/A)."),
               condicao={"campo": "status_cidadania", "valores": ["autorizado"]}),
        _campo("autorizado_documento", "select", True,
               _t("Qual número você vai informar", "Which number will you give", "Qué número va a dar"),
               _t("Escolha só um: A-Number/USCIS, número do I-94, ou passaporte estrangeiro.",
                  "Choose only one: A-Number/USCIS number, Form I-94 number, or foreign passport.",
                  "Elija solo uno: A-Number/USCIS, número del I-94, o pasaporte extranjero."),
               opcoes=[_opc("uscis", "A-Number ou número USCIS", "A-Number or USCIS number", "A-Number o número USCIS"),
                       _opc("i94", "Número de admissão do I-94", "Form I-94 admission number", "Número de admisión del I-94"),
                       _opc("passaporte", "Passaporte estrangeiro", "Foreign passport", "Pasaporte extranjero")],
               condicao={"campo": "status_cidadania", "valores": ["autorizado"]}),
        _campo("autorizado_uscis", "text", True,
               _t("A-Number ou número USCIS", "A-Number or USCIS number", "A-Number o número USCIS"),
               _t("Está no seu cartão de autorização de trabalho (EAD).",
                  "It is on your work permit card (EAD).",
                  "Está en su tarjeta de permiso de trabajo (EAD)."),
               condicao={"campo": "autorizado_documento", "valores": ["uscis"]}),
        _campo("i94_numero", "text", True,
               _t("Número do I-94", "Form I-94 admission number", "Número del I-94"),
               _t("11 caracteres, está no seu registro I-94.", "11 characters, on your I-94 record.",
                  "11 caracteres, está en su registro I-94."),
               condicao={"campo": "autorizado_documento", "valores": ["i94"]}),
        _campo("passaporte_numero", "text", True,
               _t("Número do passaporte", "Passport number", "Número de pasaporte"),
               _t("Como está no passaporte.", "As shown on the passport.", "Como aparece en el pasaporte."),
               condicao={"campo": "autorizado_documento", "valores": ["passaporte"]}),
        _campo("passaporte_pais", "text", True,
               _t("País que emitiu o passaporte", "Country of issuance", "País que emitió el pasaporte"),
               _t("Exemplo: Brasil, México.", "Example: Brazil, Mexico.", "Ejemplo: Brasil, México."),
               condicao={"campo": "autorizado_documento", "valores": ["passaporte"]}),
    ],
}

# Dados opcionais que a empresa preenche (não aparecem para o candidato).
CAMPOS_EMPREGADOR = {
    "w9": [
        _campo("solicitante_nome_endereco", "text", False,
               _t("Nome e endereço de quem pede o W-9", "Requester's name and address", "Nombre y dirección del solicitante"),
               _t("Opcional.", "Optional.", "Opcional.")),
    ],
    "w4": [
        _campo("empregador_nome_endereco", "text", False,
               _t("Nome e endereço do empregador", "Employer's name and address", "Nombre y dirección del empleador"),
               _t("Preenchido pela empresa.", "Filled in by the employer.", "Lo llena el empleador.")),
        _campo("primeiro_dia", "date", False,
               _t("Primeiro dia de trabalho", "First date of employment", "Primer día de empleo"),
               _t("Preenchido pela empresa.", "Filled in by the employer.", "Lo llena el empleador.")),
        _campo("ein_empregador", "ein", False,
               _t("EIN do empregador", "Employer identification number (EIN)", "EIN del empleador"),
               _t("9 números.", "9 digits.", "9 números.")),
    ],
    "ctw4": [
        _campo("novo_ou_recontratado", "select", False,
               _t("Funcionário novo ou recontratado?", "New or rehired employee?", "¿Empleado nuevo o recontratado?"),
               _t("Preenchido pela empresa.", "Filled in by the employer.", "Lo llena el empleador."),
               opcoes=[_opc("sim", "Sim", "Yes", "Sí"), _opc("nao", "Não", "No", "No")]),
        _campo("data_contratacao", "date", False, _t("Data de contratação", "Date hired", "Fecha de contratación"),
               _t("Preenchido pela empresa.", "Filled in by the employer.", "Lo llena el empleador."),
               condicao={"campo": "novo_ou_recontratado", "valores": ["sim"]}),
        _campo("empregador_nome", "text", False, _t("Nome da empresa", "Employer's business name", "Nombre del negocio"),
               _t("Preenchido pela empresa.", "Filled in by the employer.", "Lo llena el empleador.")),
        _campo("ein_empregador", "ein", False, _t("EIN da empresa", "Federal Employer Identification Number", "EIN del negocio"),
               _t("9 números.", "9 digits.", "9 números.")),
        _campo("empregador_endereco", "text", False, _t("Endereço da empresa", "Employer's business address", "Dirección del negocio"),
               _t("Preenchido pela empresa.", "Filled in by the employer.", "Lo llena el empleador.")),
        _campo("empregador_cidade_estado_cep", "text", False,
               _t("Cidade, estado e ZIP da empresa", "City/town, State, ZIP code", "Ciudad, estado y ZIP del negocio"),
               _t("Exemplo: Stamford, CT 06902.", "Example: Stamford, CT 06902.", "Ejemplo: Stamford, CT 06902.")),
        _campo("empregador_contato", "text", False, _t("Pessoa de contato", "Contact person", "Persona de contacto"),
               _t("Preenchido pela empresa.", "Filled in by the employer.", "Lo llena el empleador.")),
        _campo("empregador_telefone", "text", False, _t("Telefone da empresa", "Telephone number", "Teléfono del negocio"),
               _t("Preenchido pela empresa.", "Filled in by the employer.", "Lo llena el empleador."), formato="telefone"),
    ],
}

_AJ_EMP = _t("Preenchido pela empresa, olhando o documento original.",
             "Filled in by the employer after looking at the original document.",
             "Lo llena el empleador al ver el documento original.")


def _campos_doc(prefixo, nome_pt, nome_en, nome_es, condicao):
    return [
        _campo(prefixo + "_titulo", "text", True, _t("Documento " + nome_pt + ": título", "Document " + nome_en + ": title",
                                                      "Documento " + nome_es + ": título"), _AJ_EMP, condicao=condicao),
        _campo(prefixo + "_autoridade", "text", True, _t("Documento " + nome_pt + ": órgão emissor",
                                                          "Document " + nome_en + ": issuing authority",
                                                          "Documento " + nome_es + ": autoridad emisora"), _AJ_EMP, condicao=condicao),
        _campo(prefixo + "_numero", "text", True, _t("Documento " + nome_pt + ": número", "Document " + nome_en + ": number",
                                                      "Documento " + nome_es + ": número"), _AJ_EMP, condicao=condicao),
        _campo(prefixo + "_validade", "date", False, _t("Documento " + nome_pt + ": validade (se tiver)",
                                                         "Document " + nome_en + ": expiration date (if any)",
                                                         "Documento " + nome_es + ": vencimiento (si tiene)"), _AJ_EMP, condicao=condicao),
    ]


CAMPOS_I9_SECAO2 = (
    [_campo("lista", "select", True, _t("Documentos apresentados", "Documents presented", "Documentos presentados"),
            _t("Um documento da Lista A, ou um da Lista B mais um da Lista C.",
               "One document from List A, or one from List B plus one from List C.",
               "Un documento de la Lista A, o uno de la Lista B más uno de la Lista C."),
            opcoes=[_opc("A", "Lista A", "List A", "Lista A"),
                    _opc("BC", "Listas B e C", "Lists B and C", "Listas B y C")])]
    + _campos_doc("doc_a", "Lista A", "List A", "Lista A", {"campo": "lista", "valores": ["A"]})
    + [dict(c, obrigatorio=False) for c in _campos_doc("doc_a2", "Lista A (2)", "List A (2)", "Lista A (2)",
                                                       {"campo": "lista", "valores": ["A"]})]
    + [dict(c, obrigatorio=False) for c in _campos_doc("doc_a3", "Lista A (3)", "List A (3)", "Lista A (3)",
                                                       {"campo": "lista", "valores": ["A"]})]
    + _campos_doc("doc_b", "Lista B", "List B", "Lista B", {"campo": "lista", "valores": ["BC"]})
    + _campos_doc("doc_c", "Lista C", "List C", "Lista C", {"campo": "lista", "valores": ["BC"]})
    + [
        _campo("info_adicional", "text", False, _t("Informação adicional", "Additional information", "Información adicional"), _AJ_EMP),
        _campo("procedimento_alternativo", "checkbox", False,
               _t("Usei o procedimento alternativo do DHS (exame remoto)",
                  "I used an alternative procedure authorized by DHS",
                  "Usé un procedimiento alternativo autorizado por DHS"), _AJ_EMP),
        _campo("primeiro_dia", "date", True, _t("Primeiro dia de trabalho", "First day of employment", "Primer día de empleo"), _AJ_EMP),
        _campo("representante_nome", "text", True,
               _t("Sobrenome, nome e cargo de quem conferiu", "Last name, first name and title of employer or authorized representative",
                  "Apellido, nombre y cargo de quien revisó"), _AJ_EMP),
        _campo("empresa_nome", "text", True, _t("Nome da empresa", "Employer's business or organization name",
                                                "Nombre de la empresa"), _AJ_EMP),
        _campo("empresa_endereco", "text", True, _t("Endereço da empresa (rua, cidade, estado, ZIP)",
                                                    "Employer's business or organization address (street, city, state, ZIP)",
                                                    "Dirección de la empresa (calle, ciudad, estado, ZIP)"), _AJ_EMP),
        _campo("data", "date", False, _t("Data de hoje", "Today's date", "Fecha de hoy"),
               _t("Se vazio, usamos a data de hoje.", "If empty, today's date is used.", "Si está vacío, usamos la fecha de hoy.")),
    ]
)

MENSAGENS_ERRO = {
    "obrigatorio": _t("Campo obrigatório.", "This field is required.", "Este campo es obligatorio."),
    "formato": _t("Formato inválido.", "Invalid format.", "Formato no válido."),
    "opcao_invalida": _t("Escolha uma das opções.", "Choose one of the options.", "Elija una de las opciones."),
    "data_invalida": _t("Data inválida. Use mês/dia/ano.", "Invalid date. Use month/day/year.",
                        "Fecha no válida. Use mes/día/año."),
    "data_futura": _t("A data não pode ser no futuro.", "The date cannot be in the future.",
                      "La fecha no puede ser en el futuro."),
    "expirada": _t("Esta data já passou.", "This date has already passed.", "Esta fecha ya pasó."),
    "valor_invalido": _t("Valor inválido. Use só números.", "Invalid amount. Use numbers only.",
                         "Cantidad no válida. Use solo números."),
    "exige_codigo_e": _t("Com a isenção MSRRA o código precisa ser E.", "With the MSRRA exemption the code must be E.",
                         "Con la exención MSRRA el código debe ser E."),
    "tipo_invalido": _t("Formulário desconhecido.", "Unknown form.", "Formulario desconocido."),
}


# ---------------------------------------------------------------------------
# Normalização e validação
# ---------------------------------------------------------------------------

def _digitos(v):
    return re.sub(r"\D", "", str(v or ""))


def _vazio(v):
    return v is None or (isinstance(v, str) and not v.strip()) or v == []


def _bool(v):
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "sim", "yes", "si", "sí", "on", "x")
    return bool(v)


def _ssn_valido(v, aceitar_itin=False):
    d = _digitos(v)
    if len(d) != 9 or (isinstance(v, str) and re.search(r"[^\d\s-]", v)):
        return False
    area, grupo, serie = d[:3], d[3:5], d[5:]
    if area in ("000", "666") or grupo == "00" or serie == "0000":
        return False
    if area[0] == "9" and not aceitar_itin:
        return False
    return True


def _ein_valido(v):
    d = _digitos(v)
    if len(d) != 9 or (isinstance(v, str) and re.search(r"[^\d\s-]", v)):
        return False
    return d[:2] != "00"


def _data(v):
    """Aceita date, datetime, 'AAAA-MM-DD', 'MM/DD/AAAA' ou 'MM-DD-AAAA'. Devolve date ou None."""
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    s = str(v or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _fmt_data(v):
    d = _data(v)
    return d.strftime("%m/%d/%Y") if d else ""


def _dinheiro(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, bool):
        raise InvalidOperation
    s = str(v).strip().replace("$", "").replace(",", "").replace(" ", "")
    d = Decimal(s)
    if not d.is_finite() or d < 0:
        raise InvalidOperation
    return d


def _fmt_dinheiro(d):
    if d is None:
        return ""
    if d == d.to_integral_value():
        return "{:,}".format(int(d))
    return "{:,.2f}".format(d)


def _visivel(campo, dados):
    cond = campo.get("condicao")
    if not cond:
        return True
    atual = dados.get(cond["campo"])
    valores = cond["valores"]
    if True in valores:
        return _bool(atual)
    return atual in valores


def _lista_campos(tipo):
    if tipo == "i9_secao2":
        return CAMPOS_I9_SECAO2
    return CAMPOS[tipo] + CAMPOS_EMPREGADOR.get(tipo, [])


def validar(tipo, dados):
    """Valida os dados de um formulário. Devolve lista de códigos "chave:motivo".

    tipo: "w9", "w4", "i9", "ctw4" ou "i9_secao2". Campos condicionais só são
    validados quando a condição vale. Nenhum valor pessoal entra nos códigos.
    """
    if tipo not in CAMPOS and tipo != "i9_secao2":
        return ["tipo:tipo_invalido"]
    dados = dados or {}
    erros = []
    hoje = datetime.date.today()
    for c in _lista_campos(tipo):
        if not _visivel(c, dados):
            continue
        k, v = c["chave"], dados.get(c["chave"])
        if c["tipo"] == "checkbox":
            continue
        if _vazio(v):
            if c["obrigatorio"]:
                erros.append(k + ":obrigatorio")
            continue
        t = c["tipo"]
        if t == "ssn":
            if not _ssn_valido(v, aceitar_itin=(tipo == "w9")):
                erros.append(k + ":formato")
        elif t == "ein":
            if not _ein_valido(v):
                erros.append(k + ":formato")
        elif t == "date":
            d = _data(v)
            if d is None:
                erros.append(k + ":data_invalida")
            elif k == "data_nascimento" and d >= hoje:
                erros.append(k + ":data_futura")
            elif k == "autorizado_ate" and d < hoje:
                erros.append(k + ":expirada")
        elif t == "money":
            try:
                _dinheiro(v)
            except (InvalidOperation, ValueError):
                erros.append(k + ":valor_invalido")
        elif t == "select":
            vals = [o["valor"] for o in c.get("opcoes", [])]
            if str(v).strip() not in vals and str(v).strip().upper() not in vals:
                erros.append(k + ":opcao_invalida")
        elif t == "text":
            fmt = c.get("formato")
            s = str(v).strip()
            if fmt == "email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s):
                erros.append(k + ":formato")
            elif fmt == "cep" and not re.fullmatch(r"\d{5}(-?\d{4})?", s):
                erros.append(k + ":formato")
            elif fmt == "telefone" and not 10 <= len(_digitos(s)) <= 15:
                erros.append(k + ":formato")
    # Regras próprias de cada formulário.
    if tipo == "ctw4" and _bool(dados.get("msrra")) and str(dados.get("codigo_retencao") or "E").strip().upper() != "E":
        erros.append("codigo_retencao:exige_codigo_e")
    if tipo == "i9":
        st = dados.get("status_cidadania")
        if st == "residente_permanente" and not _vazio(dados.get("residente_numero")):
            if not re.fullmatch(r"A?\d{7,9}", re.sub(r"[\s-]", "", str(dados["residente_numero"]).upper())):
                erros.append("residente_numero:formato")
        if st == "autorizado" and dados.get("autorizado_documento") == "uscis" and not _vazio(dados.get("autorizado_uscis")):
            if not re.fullmatch(r"A?\d{7,9}", re.sub(r"[\s-]", "", str(dados["autorizado_uscis"]).upper())):
                erros.append("autorizado_uscis:formato")
        if st == "autorizado" and dados.get("autorizado_documento") == "i94" and not _vazio(dados.get("i94_numero")):
            if not re.fullmatch(r"[A-Za-z0-9]{11}", re.sub(r"[\s-]", "", str(dados["i94_numero"]))):
                erros.append("i94_numero:formato")
        if not _vazio(dados.get("inicial_meio")) and len(str(dados["inicial_meio"]).strip().rstrip(".")) != 1:
            erros.append("inicial_meio:formato")
    return erros


def mascarar_ssn(ssn):
    """Mostra só os 4 últimos números: "123456789" -> "•••-••-6789"."""
    d = _digitos(ssn)
    fim = d[-4:] if len(d) >= 4 else "••••"
    return "•••-••-" + fim


# ---------------------------------------------------------------------------
# AES em Python puro (só usado se o pypdf não tiver cryptography/pycryptodome)
# ---------------------------------------------------------------------------

def _xtime(a):
    a <<= 1
    return (a ^ 0x11B) if a & 0x100 else a


def _gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = _xtime(a)
        b >>= 1
    return r


def _montar_tabelas_aes():
    sbox = [0] * 256
    for x in range(256):
        inv = 0
        if x:
            inv = 1
            for _ in range(254):  # x^254 = inverso multiplicativo em GF(2^8)
                inv = _gmul(inv, x)
        s = inv
        for i in range(1, 5):
            s ^= ((inv << i) | (inv >> (8 - i))) & 0xFF
        sbox[x] = s ^ 0x63
    inv_sbox = [0] * 256
    for i, s in enumerate(sbox):
        inv_sbox[s] = i
    te = [[0] * 256 for _ in range(4)]
    td = [[0] * 256 for _ in range(4)]
    for x in range(256):
        s = sbox[x]
        w = (_gmul(s, 2) << 24) | (s << 16) | (s << 8) | _gmul(s, 3)
        si = inv_sbox[x]
        wd = (_gmul(si, 14) << 24) | (_gmul(si, 9) << 16) | (_gmul(si, 13) << 8) | _gmul(si, 11)
        for k in range(4):
            te[k][x] = ((w >> (8 * k)) | (w << (32 - 8 * k))) & 0xFFFFFFFF
            td[k][x] = ((wd >> (8 * k)) | (wd << (32 - 8 * k))) & 0xFFFFFFFF
    return sbox, inv_sbox, te, td


_AES_TAB = None
_AES_TRAVA = threading.Lock()


def _aes_tab():
    global _AES_TAB
    with _AES_TRAVA:
        if _AES_TAB is None:
            _AES_TAB = _montar_tabelas_aes()
    return _AES_TAB


class _AESBloco:
    def __init__(self, chave):
        sbox, _inv, _te, td = _aes_tab()
        nk = len(chave) // 4
        if len(chave) not in (16, 24, 32):
            raise ValueError("chave_aes_invalida")
        self.nr = nk + 6
        w = [int.from_bytes(chave[4 * i:4 * i + 4], "big") for i in range(nk)]
        rcon = 1
        for i in range(nk, 4 * (self.nr + 1)):
            t = w[i - 1]
            if i % nk == 0:
                t = ((t << 8) | (t >> 24)) & 0xFFFFFFFF
                t = (sbox[t >> 24] << 24) | (sbox[(t >> 16) & 255] << 16) | (sbox[(t >> 8) & 255] << 8) | sbox[t & 255]
                t ^= rcon << 24
                rcon = _xtime(rcon)
            elif nk > 6 and i % nk == 4:
                t = (sbox[t >> 24] << 24) | (sbox[(t >> 16) & 255] << 16) | (sbox[(t >> 8) & 255] << 8) | sbox[t & 255]
            w.append(w[i - nk] ^ t)
        self.ek = w
        dk = []
        for r in range(self.nr, -1, -1):
            bloco = w[4 * r:4 * r + 4]
            if 0 < r < self.nr:
                bloco = [td[0][sbox[x >> 24]] ^ td[1][sbox[(x >> 16) & 255]] ^ td[2][sbox[(x >> 8) & 255]]
                         ^ td[3][sbox[x & 255]] for x in bloco]
            dk.extend(bloco)
        self.dk = dk

    def cifrar(self, b):
        sbox, _inv, te, _td = _aes_tab()
        te0, te1, te2, te3 = te
        k = self.ek
        s0 = int.from_bytes(b[0:4], "big") ^ k[0]
        s1 = int.from_bytes(b[4:8], "big") ^ k[1]
        s2 = int.from_bytes(b[8:12], "big") ^ k[2]
        s3 = int.from_bytes(b[12:16], "big") ^ k[3]
        i = 4
        for _ in range(self.nr - 1):
            t0 = te0[s0 >> 24] ^ te1[(s1 >> 16) & 255] ^ te2[(s2 >> 8) & 255] ^ te3[s3 & 255] ^ k[i]
            t1 = te0[s1 >> 24] ^ te1[(s2 >> 16) & 255] ^ te2[(s3 >> 8) & 255] ^ te3[s0 & 255] ^ k[i + 1]
            t2 = te0[s2 >> 24] ^ te1[(s3 >> 16) & 255] ^ te2[(s0 >> 8) & 255] ^ te3[s1 & 255] ^ k[i + 2]
            t3 = te0[s3 >> 24] ^ te1[(s0 >> 16) & 255] ^ te2[(s1 >> 8) & 255] ^ te3[s2 & 255] ^ k[i + 3]
            s0, s1, s2, s3 = t0, t1, t2, t3
            i += 4
        o = []
        for a, b2, c, d, kk in ((s0, s1, s2, s3, k[i]), (s1, s2, s3, s0, k[i + 1]),
                                (s2, s3, s0, s1, k[i + 2]), (s3, s0, s1, s2, k[i + 3])):
            v = (sbox[a >> 24] << 24) | (sbox[(b2 >> 16) & 255] << 16) | (sbox[(c >> 8) & 255] << 8) | sbox[d & 255]
            o.append((v ^ kk).to_bytes(4, "big"))
        return b"".join(o)

    def decifrar(self, b):
        _s, inv, _te, td = _aes_tab()
        td0, td1, td2, td3 = td
        k = self.dk
        s0 = int.from_bytes(b[0:4], "big") ^ k[0]
        s1 = int.from_bytes(b[4:8], "big") ^ k[1]
        s2 = int.from_bytes(b[8:12], "big") ^ k[2]
        s3 = int.from_bytes(b[12:16], "big") ^ k[3]
        i = 4
        for _ in range(self.nr - 1):
            t0 = td0[s0 >> 24] ^ td1[(s3 >> 16) & 255] ^ td2[(s2 >> 8) & 255] ^ td3[s1 & 255] ^ k[i]
            t1 = td0[s1 >> 24] ^ td1[(s0 >> 16) & 255] ^ td2[(s3 >> 8) & 255] ^ td3[s2 & 255] ^ k[i + 1]
            t2 = td0[s2 >> 24] ^ td1[(s1 >> 16) & 255] ^ td2[(s0 >> 8) & 255] ^ td3[s3 & 255] ^ k[i + 2]
            t3 = td0[s3 >> 24] ^ td1[(s2 >> 16) & 255] ^ td2[(s1 >> 8) & 255] ^ td3[s0 & 255] ^ k[i + 3]
            s0, s1, s2, s3 = t0, t1, t2, t3
            i += 4
        o = []
        for a, b2, c, d, kk in ((s0, s3, s2, s1, k[i]), (s1, s0, s3, s2, k[i + 1]),
                                (s2, s1, s0, s3, k[i + 2]), (s3, s2, s1, s0, k[i + 3])):
            v = (inv[a >> 24] << 24) | (inv[(b2 >> 16) & 255] << 16) | (inv[(c >> 8) & 255] << 8) | inv[d & 255]
            o.append((v ^ kk).to_bytes(4, "big"))
        return b"".join(o)


def _aes_ecb_encrypt(key, data):
    a = _AESBloco(key)
    return b"".join(a.cifrar(data[i:i + 16]) for i in range(0, len(data), 16))


def _aes_ecb_decrypt(key, data):
    a = _AESBloco(key)
    return b"".join(a.decifrar(data[i:i + 16]) for i in range(0, len(data), 16))


def _aes_cbc_encrypt(key, iv, data):
    a = _AESBloco(key)
    out, ant = [], iv
    for i in range(0, len(data), 16):
        x = bytes(p ^ q for p, q in zip(data[i:i + 16], ant))
        ant = a.cifrar(x)
        out.append(ant)
    return b"".join(out)


def _aes_cbc_decrypt(key, iv, data):
    a = _AESBloco(key)
    out, ant = [], iv
    for i in range(0, len(data) - len(data) % 16, 16):
        bloco = data[i:i + 16]
        out.append(bytes(p ^ q for p, q in zip(a.decifrar(bloco), ant)))
        ant = bloco
    return b"".join(out)


class _CryptAESPuro:
    """Mesma interface do CryptAES do pypdf (IV de 16 bytes + PKCS7)."""

    def __init__(self, key):
        self.key = key

    def encrypt(self, data):
        iv = secrets.token_bytes(16)
        n = 16 - len(data) % 16
        return iv + _aes_cbc_encrypt(self.key, iv, data + bytes([n]) * n)

    def decrypt(self, data, *, strict=True):
        iv, corpo = data[:16], data[16:]
        if not corpo:
            return corpo
        if len(corpo) % 16:
            n = 16 - len(corpo) % 16
            corpo += bytes([n]) * n
        claro = _aes_cbc_decrypt(self.key, iv, corpo)
        n = claro[-1] if claro else 0
        if 1 <= n <= 16 and claro.endswith(bytes([n]) * n):
            return claro[:-n]
        return claro


def _instalar_aes_puro(forcar=False):
    """Liga o AES em Python puro dentro do pypdf quando ele não tem biblioteca de AES."""
    try:
        import pypdf._encryption as enc
    except ImportError:
        return False
    try:
        from pypdf._crypt_providers import crypt_provider  # pypdf 3.17 ou mais novo
        sem_aes = crypt_provider[0] == "local_crypt_fallback"
    except ImportError:  # pypdf 3.0 a 3.16: AES vinha do pycryptodome
        sem_aes = False
        teste = getattr(enc, "AES_ECB_encrypt", None)
        if teste is not None:
            try:
                teste(bytes(16), bytes(16))
            except Exception:
                sem_aes = True
    if not (forcar or sem_aes):
        return False
    for nome, func in (("aes_cbc_decrypt", _aes_cbc_decrypt), ("aes_cbc_encrypt", _aes_cbc_encrypt),
                       ("aes_ecb_decrypt", _aes_ecb_decrypt), ("aes_ecb_encrypt", _aes_ecb_encrypt),
                       ("AES_CBC_decrypt", _aes_cbc_decrypt), ("AES_CBC_encrypt", _aes_cbc_encrypt),
                       ("AES_ECB_decrypt", _aes_ecb_decrypt), ("AES_ECB_encrypt", _aes_ecb_encrypt),
                       ("CryptAES", _CryptAESPuro)):
        if hasattr(enc, nome):
            setattr(enc, nome, func)
    return True


# ---------------------------------------------------------------------------
# Leitura dos modelos e escrita de campos
# ---------------------------------------------------------------------------

_CACHE_MODELOS = {}
_TRAVA_MODELOS = threading.Lock()


def _bytes_modelo(tipo):
    """Bytes do PDF modelo (o CT-W4 já sai sem criptografia). Fica em memória."""
    with _TRAVA_MODELOS:
        if tipo in _CACHE_MODELOS:
            return _CACHE_MODELOS[tipo]
        caminho = os.path.join(PASTA_FORMS, ARQUIVOS[tipo])
        with open(caminho, "rb") as f:
            dados = f.read()
        if b"/Encrypt" in dados:  # antes do PdfReader: o pypdf 3.x já tenta abrir no construtor
            _instalar_aes_puro()
        r = PdfReader(io.BytesIO(dados))
        if r.is_encrypted:
            r.decrypt("")
            w = _novo_writer(r)
            buf = io.BytesIO()
            w.write(buf)
            dados = buf.getvalue()
        _CACHE_MODELOS[tipo] = dados
        return dados


def _novo_writer(reader):
    try:
        return PdfWriter(clone_from=reader)
    except TypeError:  # pypdf 3.0 a 3.1 não tem clone_from
        w = PdfWriter()
        w.clone_reader_document_root(reader)
        return w


def _add_obj(writer, obj):
    f = getattr(writer, "_add_object", None) or getattr(writer, "add_object")
    return f(obj)


def _r(obj):
    """Resolve referência indireta (pypdf 3.x nem sempre resolve sozinho)."""
    return obj.get_object() if hasattr(obj, "get_object") else obj


def _nome_completo(anot):
    partes, o, n = [], anot, 0
    while o is not None and n < 20:
        if "/T" in o:
            partes.append(str(o["/T"]))
        p = o.get("/Parent")
        o = _r(p) if p is not None else None
        n += 1
    return ".".join(reversed(partes))


def _herdado(anot, chave):
    o, n = anot, 0
    while o is not None and n < 20:
        if chave in o:
            return o[chave]
        p = o.get("/Parent")
        o = _r(p) if p is not None else None
        n += 1
    return None


def _indice_widgets(writer):
    """{nome completo: [(indice_pagina, widget)]} de todos os widgets."""
    idx = {}
    for i, pag in enumerate(writer.pages):
        for ref in _r(pag.get("/Annots")) or []:
            a = _r(ref)
            if a.get("/Subtype") != "/Widget":
                continue
            idx.setdefault(_nome_completo(a), []).append((i, a))
    return idx


def _campo_terminal(widget):
    if "/T" in widget:
        return widget
    p = widget.get("/Parent")
    return p.get_object() if p is not None else widget


_LARGURAS = None


def _larguras(negrito):
    global _LARGURAS
    if _LARGURAS is None:
        try:
            from fpdf.fonts import CORE_FONTS_CHARWIDTHS
            _LARGURAS = CORE_FONTS_CHARWIDTHS
        except ImportError:
            _LARGURAS = {}
    return _LARGURAS.get("helveticaB" if negrito else "helvetica") or {}


def _largura_texto(texto, tamanho, negrito):
    tab = _larguras(negrito)
    return sum(tab.get(ch, 556) for ch in texto) * tamanho / 1000.0


def _latin(texto):
    """Texto que cabe em WinAnsi (fontes padrão do PDF). Tira acentos que não cabem."""
    out = []
    for ch in str(texto):
        try:
            ch.encode("cp1252")
            out.append(ch)
        except UnicodeEncodeError:
            base = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode("ascii")
            out.append(base or "?")
    return "".join(out).replace("\r", " ").replace("\t", " ")


def _str_pdf(texto):
    b = _latin(texto).encode("cp1252", "replace")
    out = []
    for c in b:
        if c in (0x28, 0x29, 0x5C):
            out.append("\\" + chr(c))
        elif 32 <= c < 127:
            out.append(chr(c))
        else:
            out.append("\\%03o" % c)
    return "(" + "".join(out) + ")"


def _fonte_do_campo(widget, acroform):
    """(nome do recurso, referência da fonte, negrito, tamanho do DA)."""
    da = str(_herdado(widget, "/DA") or acroform.get("/DA") or "/Helv 0 Tf 0 g")
    m = re.search(r"/([^\s/]+)\s+([\d.]+)\s+Tf", da)
    nome, tam = (m.group(1), float(m.group(2))) if m else ("Helv", 0.0)
    dr = _r(acroform.get("/DR"))
    fontes = _r(dr.get("/Font")) if dr else None
    fontes = fontes if fontes is not None else {}
    padrao = ("Helvetica", "Helvetica-Bold", "Courier", "Times-Roman")
    alvo = "/" + nome
    if alvo in fontes and str(fontes[alvo].get_object().get("/BaseFont", "")).lstrip("/") in padrao:
        base = str(fontes[alvo].get_object().get("/BaseFont")).lstrip("/")
        return alvo, fontes.raw_get(alvo) if hasattr(fontes, "raw_get") else fontes[alvo], base.endswith("Bold"), tam
    for cand in ("/Helv", "/HeBo"):
        if cand in fontes:
            return cand, fontes.raw_get(cand) if hasattr(fontes, "raw_get") else fontes[cand], cand == "/HeBo", tam
    return "/Helv", None, False, tam


def _cor_fundo(widget):
    mk = _r(widget.get("/MK")) or {}
    bg = _r(mk.get("/BG"))
    if not bg:
        return ""
    vals = [float(x) for x in bg]
    if len(vals) == 1:
        return "%.3f g " % vals[0]
    if len(vals) == 3:
        return "%.3f %.3f %.3f rg " % tuple(vals)
    return ""


def _aparencia_texto(writer, widget, valor):
    acro = writer._root_object["/AcroForm"]
    r = [float(_r(x)) for x in _r(widget["/Rect"])]
    w, h = abs(r[2] - r[0]), abs(r[3] - r[1])
    fnome, fref, negrito, tam_da = _fonte_do_campo(widget, acro)
    ff = int(_herdado(widget, "/Ff") or 0)
    maxlen = int(_herdado(widget, "/MaxLen") or 0)
    q = int(_herdado(widget, "/Q") or 0)
    texto = _latin(valor)
    pente = bool(ff & (1 << 24)) and maxlen > 0
    multilinha = bool(ff & (1 << 12))
    tam = tam_da if tam_da > 0 else min(10.0, max(6.0, h * 0.62))
    if multilinha:
        tam = min(tam, 9.0)
    elif not pente:
        tam = min(tam, max(4.0, h - 2.0))
        while tam > 5.0 and _largura_texto(texto, tam, negrito) > w - 4:
            tam -= 0.5
    partes = []
    fundo = _cor_fundo(widget)
    if fundo:
        partes.append("q %s0 0 %.2f %.2f re f Q" % (fundo, w, h))
    partes.append("/Tx BMC q BT %s %.2f Tf 0 g" % (fnome, tam))
    base_y = (h - tam * 0.72) / 2.0
    if pente:
        cel = w / maxlen
        for n, ch in enumerate(texto[:maxlen]):
            x = n * cel + (cel - _largura_texto(ch, tam, negrito)) / 2.0
            partes.append("1 0 0 1 %.2f %.2f Tm %s Tj" % (x, base_y, _str_pdf(ch)))
    elif multilinha:
        linhas, atual = [], ""
        for palavra in texto.split():
            teste = (atual + " " + palavra).strip()
            if _largura_texto(teste, tam, negrito) <= w - 4 or not atual:
                atual = teste
            else:
                linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
        y = h - 2 - tam
        for ln in linhas:
            if y < 0:
                break
            partes.append("1 0 0 1 2 %.2f Tm %s Tj" % (y, _str_pdf(ln)))
            y -= tam * 1.15
    else:
        lt = _largura_texto(texto, tam, negrito)
        x = 2.0 if q == 0 else ((w - lt) / 2.0 if q == 1 else w - 2.0 - lt)
        partes.append("1 0 0 1 %.2f %.2f Tm %s Tj" % (max(1.0, x), base_y, _str_pdf(texto)))
    partes.append("ET Q EMC")
    stream = DecodedStreamObject()
    conteudo = "\n".join(partes).encode("latin-1")
    if hasattr(stream, "set_data"):
        try:
            stream.set_data(conteudo)
        except Exception:
            stream._data = conteudo
    else:
        stream._data = conteudo
    stream.update({
        NameObject("/Type"): NameObject("/XObject"),
        NameObject("/Subtype"): NameObject("/Form"),
        NameObject("/BBox"): ArrayObject([FloatObject(0), FloatObject(0), FloatObject(w), FloatObject(h)]),
    })
    if fref is not None:
        stream[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject(fnome): fref})})
    widget[NameObject("/AP")] = DictionaryObject({NameObject("/N"): _add_obj(writer, stream)})


def _estado_ligado(widget):
    ap = _r(widget.get("/AP"))
    n = _r(ap.get("/N")) if ap is not None else None
    if n is not None and hasattr(n, "keys"):
        for k in n.keys():
            if k != "/Off":
                return k
    return "/Yes"


def _escrever(writer, valores, marcas):
    """valores: {nome completo: texto}; marcas: {nome completo: bool}."""
    idx = _indice_widgets(writer)
    faltando = [n for n in list(valores) + list(marcas) if n not in idx]
    if faltando:
        raise KeyError("campo_pdf_inexistente: " + ", ".join(faltando))
    for nome, valor in valores.items():
        if valor is None:
            continue
        valor = str(valor)
        for _pag, w in idx[nome]:
            _campo_terminal(w)[NameObject("/V")] = TextStringObject(valor)
            if valor:
                _aparencia_texto(writer, w, valor)
    for nome, ligado in marcas.items():
        for _pag, w in idx[nome]:
            estado = _estado_ligado(w) if ligado else "/Off"
            w[NameObject("/AS")] = NameObject(estado)
            _campo_terminal(w)[NameObject("/V")] = NameObject(estado)


def _preparar(writer):
    root = writer._root_object
    acro = root["/AcroForm"]
    if "/XFA" in acro:
        del acro["/XFA"]
    for k in ("/NeedsRendering", "/Perms"):
        if k in root:
            del root[k]
    acro[NameObject("/NeedAppearances")] = BooleanObject(True)


def _saida(writer):
    for pag in writer.pages:
        try:
            pag.compress_content_streams()
        except Exception:  # compressão é só para reduzir o tamanho
            pass
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Assinatura: imagem desenhada com fpdf2 e mesclada na página
# ---------------------------------------------------------------------------

# Caixa da assinatura (x0, y0, x1, y1 em pontos, origem embaixo à esquerda) e
# posição da data quando o formulário não tem campo de data (x, y da linha de base).
LOCAL_ASSINATURA = {
    "w9": {"pagina": 0, "caixa": (142, 195, 395, 214), "data_xy": (428, 199)},
    "w4": {"pagina": 0, "caixa": (106, 90, 430, 109), "data_xy": (478, 92)},
    "i9": {"pagina": 0, "caixa": (45, 420, 362, 433), "data_campo": "Today's Date mmddyyy"},
    "ctw4": {"pagina": 0, "caixa": (40, 175, 410, 189), "data_campo": "Date"},
    "i9_secao2": {"pagina": 0, "caixa": (296, 81, 484, 99), "data_campo": "S2 Todays Date mmddyyyy"},
}


def _preparar_imagem(png):
    """Recorta as margens vazias e deixa o fundo branco transparente (usa Pillow, que vem com fpdf2)."""
    if not isinstance(png, (bytes, bytearray)) or not (png[:8] == b"\x89PNG\r\n\x1a\n" or png[:3] == b"\xff\xd8\xff"):
        raise ValueError("assinatura_png_invalida")
    try:
        from PIL import Image
    except ImportError:
        return bytes(png), None
    try:
        img = Image.open(io.BytesIO(png))
        img.load()
    except Exception:
        raise ValueError("assinatura_png_invalida")
    rgba = img.convert("RGBA")
    alfa = rgba.getchannel("A")
    if alfa.getextrema()[0] == 255:  # sem transparência: branco vira transparente
        cinza = rgba.convert("L")
        alfa = cinza.point(lambda v: 0 if v > 225 else min(255, (255 - v) * 2))
        rgba.putalpha(alfa)
    caixa = alfa.point(lambda v: 255 if v > 20 else 0).getbbox()
    if not caixa:
        raise ValueError("assinatura_vazia")
    rgba = rgba.crop(caixa)
    out = io.BytesIO()
    rgba.save(out, format="PNG")
    return out.getvalue(), rgba.size


def _carimbar(writer, pagina, imagens=(), textos=()):
    """imagens: [(png_bytes, (x0,y0,x1,y1))]; textos: [(texto, x, y_base, tamanho, estilo, cinza)]."""
    from fpdf import FPDF
    pag = writer.pages[pagina]
    mb = pag.mediabox
    largura, altura = float(mb.width), float(mb.height)
    pdf = FPDF(unit="pt", format=(largura, altura))
    pdf.set_auto_page_break(False)
    pdf.set_margins(0, 0, 0)
    pdf.add_page()
    for png, (x0, y0, x1, y1) in imagens:
        dados, tam = _preparar_imagem(png)
        bw, bh = x1 - x0, y1 - y0
        if tam:
            iw, ih = tam
            esc = min(bw / iw, bh / ih)
            w, h = iw * esc, ih * esc
        else:
            w, h = bw, bh
        pdf.image(io.BytesIO(dados), x=x0, y=altura - y0 - h, w=w, h=h)
    for texto, x, y, tam, estilo, cinza in textos:
        pdf.set_font("helvetica", estilo, tam)
        pdf.set_text_color(cinza)
        pdf.text(x, altura - y, _latin(texto))
    sobre = PdfReader(io.BytesIO(bytes(pdf.output()))).pages[0]
    pag.merge_page(sobre)


def _assinar(writer, chave_local, assinatura_png, data_txt, nome_assinatura, valores):
    loc = LOCAL_ASSINATURA[chave_local]
    x0, y0, x1, y1 = loc["caixa"]
    imagens, textos = [], []
    if assinatura_png:
        imagens.append((assinatura_png, loc["caixa"]))
    elif nome_assinatura:
        nome = _latin(nome_assinatura)[:80]
        tam = min(14.0, (y1 - y0) - 2)
        while tam > 6 and _largura_texto(nome, tam, False) > (x1 - x0) - 4:
            tam -= 0.5
        textos.append((nome, x0 + 2, y0 + 3, tam, "I", 0))
    if data_txt:
        if "data_campo" in loc:
            valores[loc["data_campo"]] = data_txt
        else:
            dx, dy = loc["data_xy"]
            textos.append((data_txt, dx, dy, 9, "", 0))
    if imagens or textos:
        _carimbar(writer, loc["pagina"], imagens, textos)


# ---------------------------------------------------------------------------
# Mapeamento dos campos de cada formulário
# ---------------------------------------------------------------------------

_W9 = "topmostSubform[0].Page1[0]."
_W9B = _W9 + "Boxes3a-b_ReadOrder[0]."
_W4 = "topmostSubform[0].Page1[0]."

_W9_CLASSE = {"individual": 0, "c_corp": 1, "s_corp": 2, "partnership": 3, "trust": 4, "llc": 5, "outro": 6}
_W4_ESTADO = {"solteiro": 0, "casado_conjunto": 1, "chefe_familia": 2}
_I9_STATUS = {"cidadao": "CB_1", "nacional": "CB_2", "residente_permanente": "CB_3", "autorizado": "CB_4"}


def _s(dados, k):
    v = dados.get(k)
    return "" if v is None else str(v).strip()


def _rua(dados):
    rua, apto = _s(dados, "endereco"), _s(dados, "apto")
    if apto:
        return rua + (", Apt " + apto if not apto.lower().startswith(("apt", "unit", "#", "ste", "suite")) else ", " + apto)
    return rua


def _cidade_uf_cep(dados, pc="cidade", pe="estado", pz="cep"):
    cidade, uf, cep = _s(dados, pc), _s(dados, pe).upper(), _s(dados, pz)
    return ", ".join(p for p in (cidade, (uf + " " + cep).strip()) if p)


def _ssn_tracos(v):
    d = _digitos(v)
    return "%s-%s-%s" % (d[:3], d[3:5], d[5:]) if len(d) == 9 else ""


def _ein_traco(v):
    d = _digitos(v)
    return "%s-%s" % (d[:2], d[2:]) if len(d) == 9 else ""


def _mapa_w9(d):
    v, m = {}, {}
    v[_W9 + "f1_01[0]"] = _s(d, "nome")
    v[_W9 + "f1_02[0]"] = _s(d, "nome_empresa")
    cls = d.get("classificacao")
    for nome, i in _W9_CLASSE.items():
        m[_W9B + "c1_1[%d]" % i] = (cls == nome)
    v[_W9B + "f1_03[0]"] = _s(d, "llc_classificacao").upper() if cls == "llc" else ""
    v[_W9B + "f1_04[0]"] = _s(d, "outro_descricao") if cls == "outro" else ""
    m[_W9B + "c1_2[0]"] = cls in ("partnership", "trust", "llc") and _bool(d.get("socios_estrangeiros"))
    v[_W9 + "f1_05[0]"] = _s(d, "codigo_isencao")
    v[_W9 + "f1_06[0]"] = _s(d, "codigo_fatca")
    v[_W9 + "Address_ReadOrder[0].f1_07[0]"] = _rua(d)
    v[_W9 + "Address_ReadOrder[0].f1_08[0]"] = _cidade_uf_cep(d)
    v[_W9 + "f1_09[0]"] = _s(d, "solicitante_nome_endereco")
    v[_W9 + "f1_10[0]"] = _s(d, "numeros_conta")
    ssn = _digitos(d.get("ssn")) if d.get("tipo_tin", "ssn") == "ssn" else ""
    ein = _digitos(d.get("ein")) if d.get("tipo_tin") == "ein" else ""
    v[_W9 + "f1_11[0]"], v[_W9 + "f1_12[0]"], v[_W9 + "f1_13[0]"] = ssn[:3], ssn[3:5], ssn[5:9]
    v[_W9 + "f1_14[0]"], v[_W9 + "f1_15[0]"] = ein[:2], ein[2:9]
    return v, m


def _mapa_w4(d):
    v, m = {}, {}
    nome = _s(d, "primeiro_nome")
    if _s(d, "inicial_meio"):
        nome += " " + _s(d, "inicial_meio").rstrip(".")[:1].upper()
    v[_W4 + "Step1a[0].f1_01[0]"] = nome
    v[_W4 + "Step1a[0].f1_02[0]"] = _s(d, "sobrenome")
    v[_W4 + "Step1a[0].f1_03[0]"] = _rua(d)
    v[_W4 + "Step1a[0].f1_04[0]"] = _cidade_uf_cep(d)
    v[_W4 + "f1_05[0]"] = _ssn_tracos(d.get("ssn"))
    est = d.get("estado_civil")
    for nomeest, i in _W4_ESTADO.items():
        m[_W4 + "c1_1[%d]" % i] = (est == nomeest)
    isento = _bool(d.get("isento"))
    m[_W4 + "c1_3[0]"] = isento
    if isento:  # IRS: quem pede isenção preenche só os passos 1(a), 1(b) e 5
        m[_W4 + "c1_2[0]"] = False
        for k in ("Step3_ReadOrder[0].f1_06[0]", "Step3_ReadOrder[0].f1_07[0]", "f1_08[0]", "f1_09[0]",
                  "f1_10[0]", "f1_11[0]"):
            v[_W4 + k] = ""
    else:
        m[_W4 + "c1_2[0]"] = _bool(d.get("multiplos_empregos"))
        filhos = int(_digitos(d.get("filhos_menores_17")) or 0)
        outros = int(_digitos(d.get("outros_dependentes")) or 0)
        a3a, a3b = Decimal(filhos * 2200), Decimal(outros * 500)
        creditos = _dinheiro(d.get("outros_creditos")) or Decimal(0)
        total = a3a + a3b + creditos
        v[_W4 + "Step3_ReadOrder[0].f1_06[0]"] = _fmt_dinheiro(a3a) if a3a else ""
        v[_W4 + "Step3_ReadOrder[0].f1_07[0]"] = _fmt_dinheiro(a3b) if a3b else ""
        v[_W4 + "f1_08[0]"] = _fmt_dinheiro(total) if total else ""
        v[_W4 + "f1_09[0]"] = _fmt_dinheiro(_dinheiro(d.get("outra_renda")))
        v[_W4 + "f1_10[0]"] = _fmt_dinheiro(_dinheiro(d.get("deducoes")))
        v[_W4 + "f1_11[0]"] = _fmt_dinheiro(_dinheiro(d.get("retencao_extra")))
    v[_W4 + "f1_12[0]"] = _s(d, "empregador_nome_endereco")
    v[_W4 + "f1_13[0]"] = _fmt_data(d.get("primeiro_dia")) if d.get("primeiro_dia") else ""
    v[_W4 + "f1_14[0]"] = _ein_traco(d.get("ein_empregador"))
    return v, m


def _mapa_ctw4(d):
    v, m = {}, {}
    v["1"] = _s(d, "codigo_retencao").upper()
    v["2"] = _fmt_dinheiro(_dinheiro(d.get("retencao_adicional")))
    v["3"] = _fmt_dinheiro(_dinheiro(d.get("retencao_reduzida")))
    msrra = _bool(d.get("msrra"))
    m["Check Box1"] = msrra
    v["residencedomicile"] = _s(d, "estado_residencia").upper() if msrra else ""
    partes = [_s(d, "primeiro_nome"), _s(d, "inicial_meio").rstrip(".")[:1].upper(), _s(d, "sobrenome")]
    v["First name Ml Last name"] = " ".join(p for p in partes if p)
    v["SSN"] = _ssn_tracos(d.get("ssn"))
    v["Home address number and street apartment number suite number PO Box"] = _rua(d)
    v["Citytown State ZIP code"] = _cidade_uf_cep(d)
    novo = d.get("novo_ou_recontratado")
    m["Check Box2"] = novo == "nao"
    m["Check Box3"] = novo == "sim"
    v["Yes  Enter date hired"] = _fmt_data(d.get("data_contratacao")) if novo == "sim" and d.get("data_contratacao") else ""
    v["Text3"] = _s(d, "empregador_nome")
    v["Text4"] = _ein_traco(d.get("ein_empregador"))
    v["Employers business address"] = _s(d, "empregador_endereco")
    v["Citytown State ZIP code_2"] = _s(d, "empregador_cidade_estado_cep")
    v["Contact person"] = _s(d, "empregador_contato")
    v["Telephone number"] = _fmt_telefone(d.get("empregador_telefone"))
    return v, m


def _fmt_telefone(v):
    d = _digitos(v)
    if len(d) == 11 and d[0] == "1":
        d = d[1:]
    if len(d) == 10:
        return "%s-%s-%s" % (d[:3], d[3:6], d[6:])
    return str(v or "").strip()


def _mapa_i9(d):
    v, m = {}, {}
    v["Last Name (Family Name)"] = _s(d, "sobrenome")
    v["First Name Given Name"] = _s(d, "primeiro_nome")
    v["Employee Middle Initial (if any)"] = _s(d, "inicial_meio").rstrip(".")[:1].upper()
    v["Employee Other Last Names Used (if any)"] = _s(d, "outros_sobrenomes") or "N/A"
    v["Address Street Number and Name"] = _s(d, "endereco")
    v["Apt Number (if any)"] = _s(d, "apto")
    v["City or Town"] = _s(d, "cidade")
    v["State"] = _s(d, "estado").upper()
    v["ZIP Code"] = _s(d, "cep")
    v["Date of Birth mmddyyyy"] = _fmt_data(d.get("data_nascimento"))
    v["US Social Security Number"] = _digitos(d.get("ssn"))[:9]
    v["Employees E-mail Address"] = _s(d, "email")
    v["Telephone Number"] = _fmt_telefone(d.get("telefone")) if d.get("telefone") else ""
    st = d.get("status_cidadania")
    for nome, cb in _I9_STATUS.items():
        m[cb] = (st == nome)
    v["3 A lawful permanent resident Enter USCIS or ANumber"] = (
        re.sub(r"[\s-]", "", _s(d, "residente_numero")).upper() if st == "residente_permanente" else "")
    uscis = i94 = passaporte = exp = ""
    if st == "autorizado":
        exp = _fmt_data(d.get("autorizado_ate")) if d.get("autorizado_ate") else "N/A"
        doc = d.get("autorizado_documento")
        if doc == "uscis":
            uscis = re.sub(r"[\s-]", "", _s(d, "autorizado_uscis")).upper()
        elif doc == "i94":
            i94 = re.sub(r"[\s-]", "", _s(d, "i94_numero")).upper()
        elif doc == "passaporte":
            passaporte = ", ".join(p for p in (_s(d, "passaporte_numero").upper(), _s(d, "passaporte_pais")) if p)
    v["Exp Date mmddyyyy"] = exp
    v["USCIS ANumber"] = uscis
    v["Form I94 Admission Number"] = i94
    v["Foreign Passport Number and Country of IssuanceRow1"] = passaporte
    return v, m


_MAPAS = {"w9": _mapa_w9, "w4": _mapa_w4, "ctw4": _mapa_ctw4, "i9": _mapa_i9}

# Campos da Seção 2 do I-9 (Lista A tem até 3 documentos; B e C um cada).
_I9_S2_DOCS = {
    "doc_a": ("Document Title 1", "Issuing Authority 1", "Document Number 0 (if any)", "Expiration Date if any"),
    "doc_a2": ("Document Title 2 If any", "Issuing Authority_2", "Document Number If any_2",
               "List A.  Document 2. Expiration Date (if any)"),
    "doc_a3": ("List A.   Document Title 3.  If any", "List A. Document 3.  Enter Issuing Authority",
               "List A.  Document 3 Number.  If any", "Document Number if any_3"),
    "doc_b": ("List B Document 1 Title", "List B Issuing Authority 1", "List B Document Number 1",
              "List B Expiration Date 1"),
    "doc_c": ("List C Document Title 1", "List C Issuing Authority 1", "List C Document Number 1",
              "List C Expiration Date 1"),
}


# ---------------------------------------------------------------------------
# API pública de preenchimento
# ---------------------------------------------------------------------------

def preencher(tipo, dados, assinatura_png=None, data_assinatura=None, nome_assinatura=None):
    """Preenche o PDF oficial e devolve os bytes.

    tipo: "w9", "w4", "i9" ou "ctw4". dados: dict com as chaves de CAMPOS[tipo]
    (e, se quiser, as de CAMPOS_EMPREGADOR[tipo]). Os dados são validados antes:
    se houver erro, levanta ErroFormulario com .erros (lista de códigos).
    assinatura_png: bytes PNG (ou JPEG) desenhados sobre a linha de assinatura.
    data_assinatura: date ou texto; se vazio, usa a data de hoje.
    nome_assinatura: nome digitado. Só é usado quando não há imagem: o nome
    digitado vira a assinatura (letra itálica) na linha de assinatura.
    """
    if tipo not in _MAPAS:
        raise ErroFormulario(["tipo:tipo_invalido"])
    dados = dict(dados or {})
    erros = validar(tipo, dados)
    if erros:
        raise ErroFormulario(erros)
    writer = _novo_writer(PdfReader(io.BytesIO(_bytes_modelo(tipo))))
    _preparar(writer)
    valores, marcas = _MAPAS[tipo](dados)
    data_txt = _fmt_data(data_assinatura) if data_assinatura else datetime.date.today().strftime("%m/%d/%Y")
    _assinar(writer, tipo, assinatura_png, data_txt, nome_assinatura, valores)
    _escrever(writer, valores, marcas)
    return _saida(writer)


def preencher_i9_secao2(pdf_bytes, dados_empregador, assinatura_png=None):
    """Empregador completa a Seção 2 de um I-9 já preenchido (bytes de preencher("i9", ...)).

    dados_empregador: chaves de CAMPOS_I9_SECAO2. lista "A" usa doc_a (e doc_a2,
    doc_a3 se houver); lista "BC" usa doc_b e doc_c. Datas em AAAA-MM-DD ou MM/DD/AAAA.
    """
    d = dict(dados_empregador or {})
    erros = validar("i9_secao2", d)
    if erros:
        raise ErroFormulario(erros)
    writer = _novo_writer(PdfReader(io.BytesIO(pdf_bytes)))
    _preparar(writer)
    valores, marcas = {}, {}
    usados = ("doc_a", "doc_a2", "doc_a3") if d.get("lista") == "A" else ("doc_b", "doc_c")
    for prefixo, nomes in _I9_S2_DOCS.items():
        ativo = prefixo in usados
        for sufixo, nome_pdf in zip(("_titulo", "_autoridade", "_numero", "_validade"), nomes):
            val = _s(d, prefixo + sufixo) if ativo else ""
            if sufixo == "_validade" and val:
                val = _fmt_data(val) or val
            elif sufixo == "_validade" and ativo and _s(d, prefixo + "_titulo"):
                val = "N/A"
            valores[nome_pdf] = val
    valores["Additional Information"] = _s(d, "info_adicional")
    marcas["CB_Alt"] = _bool(d.get("procedimento_alternativo"))
    valores["FirstDayEmployed mmddyyyy"] = _fmt_data(d.get("primeiro_dia"))
    valores["Last Name First Name and Title of Employer or Authorized Representative"] = _s(d, "representante_nome")
    valores["Employers Business or Org Name"] = _s(d, "empresa_nome")
    valores["Employers Business or Org Address"] = _s(d, "empresa_endereco")
    data_txt = _fmt_data(d.get("data")) if d.get("data") else datetime.date.today().strftime("%m/%d/%Y")
    _assinar(writer, "i9_secao2", assinatura_png, data_txt, None, valores)
    _escrever(writer, valores, marcas)
    return _saida(writer)
