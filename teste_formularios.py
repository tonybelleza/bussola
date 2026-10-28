"""
Testes dos formulários oficiais (formularios.py): W-9, W-4 2026, I-9 e CT-W4 2026.

Uso:  python3 teste_formularios.py

Só dados de teste, claramente falsos (SSN 123-45-6789, EIN 12-3456789). Nada é
impresso além do resultado dos testes. Se FORM_PNG=1 e o sistema tiver o
comando sips (macOS), a página 1 de cada PDF preenchido é salva em PNG numa
pasta temporária para conferência visual.
"""
import datetime
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from pypdf import PdfReader  # noqa: E402

import formularios as F  # noqa: E402


def assinatura_teste():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (600, 200), "white")
    d = ImageDraw.Draw(img)
    d.line([(40, 150), (120, 40), (170, 160), (260, 50), (330, 150), (420, 60), (560, 140)], fill=(10, 20, 120), width=8)
    b = io.BytesIO()
    img.save(b, "PNG")
    return b.getvalue()


SIG = assinatura_teste()
BASE = dict(primeiro_nome="Maria", inicial_meio="J", sobrenome="Testelopez", endereco="123 Main St", apto="2B",
            cidade="Stamford", estado="CT", cep="06902", ssn="123-45-6789")
FUTURO = (datetime.date.today() + datetime.timedelta(days=700)).isoformat()

W9 = dict(BASE, nome="Maria J Testelopez", classificacao="individual", tipo_tin="ssn")
W4 = dict(BASE, estado_civil="chefe_familia", multiplos_empregos=True, filhos_menores_17="2", outros_dependentes="1",
          outra_renda="1200", retencao_extra="25.50", empregador_nome_endereco="Test Cleaning Co, 1 Test Rd, Stamford CT",
          primeiro_dia="2026-11-02", ein_empregador="12-3456789")
CTW4 = dict(BASE, codigo_retencao="F", retencao_adicional="10", novo_ou_recontratado="sim", data_contratacao="2026-11-02",
            empregador_nome="Test Cleaning Co", ein_empregador="123456789", empregador_endereco="1 Test Rd",
            empregador_cidade_estado_cep="Stamford, CT 06902", empregador_contato="Test Person",
            empregador_telefone="2035550100")
I9 = dict(BASE, data_nascimento="1990-05-17", email="maria@example.com", telefone="2035550101",
          status_cidadania="autorizado", autorizado_ate=FUTURO, autorizado_documento="passaporte",
          passaporte_numero="X1234567", passaporte_pais="Mexico")

W9P = "topmostSubform[0].Page1[0]."
W9B = W9P + "Boxes3a-b_ReadOrder[0]."


def campos(pdf):
    r = PdfReader(io.BytesIO(pdf))
    out = {}
    for nome, f in (r.get_fields() or {}).items():
        v = f.get("/V")
        out[nome] = None if v is None else str(v)
    return out


def imagens_da_pagina(pagina):
    """Conta XObjects de imagem na página (inclusive dentro de Form XObjects)."""
    total = 0
    vistos = set()

    def visitar(recursos):
        nonlocal total
        if not recursos:
            return
        xo = recursos.get_object().get("/XObject")
        if not xo:
            return
        for _k, ref in xo.get_object().items():
            obj = ref.get_object()
            if id(obj) in vistos:
                continue
            vistos.add(id(obj))
            if obj.get("/Subtype") == "/Image":
                total += 1
            elif obj.get("/Subtype") == "/Form":
                visitar(obj.get("/Resources"))

    visitar(pagina.get("/Resources"))
    return total


def imagens_modelo(tipo):
    r = PdfReader(io.BytesIO(F._bytes_modelo(tipo)))
    return [imagens_da_pagina(p) for p in r.pages]


class Base(unittest.TestCase):
    def conferir_assinatura(self, pdf, tipo_modelo, pagina=0):
        r = PdfReader(io.BytesIO(pdf))
        antes = imagens_modelo(tipo_modelo)
        depois = [imagens_da_pagina(p) for p in r.pages]
        self.assertEqual(depois[pagina], antes[pagina] + 1, "a assinatura deve estar na página certa")
        for i, (a, b) in enumerate(zip(antes, depois)):
            if i != pagina:
                self.assertEqual(a, b, "nenhuma imagem nova nas outras páginas")

    def conferir_basico(self, pdf):
        r = PdfReader(io.BytesIO(pdf))
        self.assertFalse(r.is_encrypted)
        acro = r.trailer["/Root"]["/AcroForm"]
        self.assertTrue(bool(acro.get("/NeedAppearances")))
        self.assertNotIn("/XFA", acro)
        return r


class TesteW9(Base):
    def test_preenche_e_assina(self):
        pdf = F.preencher("w9", W9, assinatura_png=SIG, data_assinatura="2026-10-27")
        self.conferir_basico(pdf)
        c = campos(pdf)
        self.assertEqual(c[W9P + "f1_01[0]"], "Maria J Testelopez")
        self.assertEqual(c[W9P + "Address_ReadOrder[0].f1_07[0]"], "123 Main St, Apt 2B")
        self.assertEqual(c[W9P + "Address_ReadOrder[0].f1_08[0]"], "Stamford, CT 06902")
        self.assertEqual((c[W9P + "f1_11[0]"], c[W9P + "f1_12[0]"], c[W9P + "f1_13[0]"]), ("123", "45", "6789"))
        self.assertEqual(c[W9P + "f1_14[0]"], "")
        self.assertEqual(c[W9B + "c1_1[0]"], "/1")
        for i in range(1, 7):
            self.assertEqual(c[W9B + "c1_1[%d]" % i], "/Off")
        self.conferir_assinatura(pdf, "w9")
        texto = PdfReader(io.BytesIO(pdf)).pages[0].extract_text()
        self.assertIn("10/27/2026", texto)

    def test_llc_e_ein(self):
        d = dict(W9, classificacao="llc", llc_classificacao="s", tipo_tin="ein", ein="12-3456789",
                 nome_empresa="Test Cleaning LLC", socios_estrangeiros=True)
        d.pop("ssn")
        c = campos(F.preencher("w9", d))
        self.assertEqual(c[W9B + "c1_1[5]"], "/6")
        self.assertEqual(c[W9B + "c1_1[0]"], "/Off")
        self.assertEqual(c[W9B + "f1_03[0]"], "S")
        self.assertEqual(c[W9B + "c1_2[0]"], "/1")
        self.assertEqual((c[W9P + "f1_14[0]"], c[W9P + "f1_15[0]"]), ("12", "3456789"))
        self.assertEqual(c[W9P + "f1_11[0]"], "")
        self.assertEqual(c[W9P + "f1_02[0]"], "Test Cleaning LLC")

    def test_validar(self):
        self.assertEqual(F.validar("w9", W9), [])
        e = F.validar("w9", {})
        for k in ("nome:obrigatorio", "classificacao:obrigatorio", "endereco:obrigatorio", "tipo_tin:obrigatorio"):
            self.assertIn(k, e)
        self.assertIn("llc_classificacao:obrigatorio", F.validar("w9", dict(W9, classificacao="llc")))
        self.assertIn("outro_descricao:obrigatorio", F.validar("w9", dict(W9, classificacao="outro")))
        self.assertIn("ein:obrigatorio", F.validar("w9", dict(W9, tipo_tin="ein")))
        self.assertIn("ein:formato", F.validar("w9", dict(W9, tipo_tin="ein", ein="1234")))
        self.assertIn("ssn:formato", F.validar("w9", dict(W9, ssn="12345678")))
        self.assertEqual(F.validar("w9", dict(W9, ssn="912-70-1234")), [], "W-9 aceita ITIN")
        self.assertIn("classificacao:opcao_invalida", F.validar("w9", dict(W9, classificacao="xyz")))


class TesteW4(Base):
    P = "topmostSubform[0].Page1[0]."

    def test_preenche_e_assina(self):
        pdf = F.preencher("w4", W4, assinatura_png=SIG, data_assinatura="10/27/2026")
        self.conferir_basico(pdf)
        c = campos(pdf)
        P = self.P
        self.assertEqual(c[P + "Step1a[0].f1_01[0]"], "Maria J")
        self.assertEqual(c[P + "Step1a[0].f1_02[0]"], "Testelopez")
        self.assertEqual(c[P + "Step1a[0].f1_04[0]"], "Stamford, CT 06902")
        self.assertEqual(c[P + "f1_05[0]"], "123-45-6789")
        self.assertEqual([c[P + "c1_1[%d]" % i] for i in range(3)], ["/Off", "/Off", "/3"])
        self.assertEqual(c[P + "c1_2[0]"], "/1")
        self.assertEqual(c[P + "Step3_ReadOrder[0].f1_06[0]"], "4,400")
        self.assertEqual(c[P + "Step3_ReadOrder[0].f1_07[0]"], "500")
        self.assertEqual(c[P + "f1_08[0]"], "4,900")
        self.assertEqual(c[P + "f1_09[0]"], "1,200")
        self.assertEqual(c[P + "f1_10[0]"], "")
        self.assertEqual(c[P + "f1_11[0]"], "25.50")
        self.assertEqual(c[P + "c1_3[0]"], "/Off")
        self.assertEqual(c[P + "f1_13[0]"], "11/02/2026")
        self.assertEqual(c[P + "f1_14[0]"], "12-3456789")
        self.conferir_assinatura(pdf, "w4")
        self.assertIn("10/27/2026", PdfReader(io.BytesIO(pdf)).pages[0].extract_text())

    def test_isento_limpa_passos_2_a_4(self):
        c = campos(F.preencher("w4", dict(W4, isento=True)))
        P = self.P
        self.assertEqual(c[P + "c1_3[0]"], "/1")
        self.assertEqual(c[P + "c1_2[0]"], "/Off")
        self.assertEqual(c[P + "f1_08[0]"], "")
        self.assertEqual(c[P + "f1_11[0]"], "")

    def test_validar(self):
        self.assertEqual(F.validar("w4", W4), [])
        e = F.validar("w4", {})
        for k in ("primeiro_nome:obrigatorio", "sobrenome:obrigatorio", "ssn:obrigatorio", "estado_civil:obrigatorio"):
            self.assertIn(k, e)
        self.assertIn("ssn:formato", F.validar("w4", dict(W4, ssn="000-12-3456")))
        self.assertIn("ssn:formato", F.validar("w4", dict(W4, ssn="912-70-1234")), "W-4 exige SSN, não ITIN")
        self.assertIn("ssn:formato", F.validar("w4", dict(W4, ssn="12a456789")))
        self.assertIn("retencao_extra:valor_invalido", F.validar("w4", dict(W4, retencao_extra="dez")))
        self.assertIn("retencao_extra:valor_invalido", F.validar("w4", dict(W4, retencao_extra="-5")))
        self.assertIn("ein_empregador:formato", F.validar("w4", dict(W4, ein_empregador="12")))
        self.assertIn("primeiro_dia:data_invalida", F.validar("w4", dict(W4, primeiro_dia="31/31/2026")))
        self.assertIn("cep:formato", F.validar("w4", dict(W4, cep="69")))

    def test_preencher_recusa_dados_invalidos(self):
        with self.assertRaises(F.ErroFormulario) as ctx:
            F.preencher("w4", dict(W4, ssn="123"))
        self.assertIn("ssn:formato", ctx.exception.erros)
        self.assertNotIn("123", str(ctx.exception).replace("ssn:formato", ""))


class TesteCTW4(Base):
    def test_preenche_e_assina(self):
        pdf = F.preencher("ctw4", CTW4, assinatura_png=SIG, data_assinatura="2026-10-27")
        self.conferir_basico(pdf)
        c = campos(pdf)
        self.assertEqual(c["1"], "F")
        self.assertEqual(c["2"], "10")
        self.assertEqual(c["3"], "")
        self.assertEqual(c["Check Box1"], "/Off")
        self.assertEqual(c["First name Ml Last name"], "Maria J Testelopez")
        self.assertEqual(c["SSN"], "123-45-6789")
        self.assertEqual(c["Home address number and street apartment number suite number PO Box"], "123 Main St, Apt 2B")
        self.assertEqual(c["Citytown State ZIP code"], "Stamford, CT 06902")
        self.assertEqual(c["Date"], "10/27/2026")
        self.assertEqual((c["Check Box2"], c["Check Box3"]), ("/Off", "/Yes"))
        self.assertEqual(c["Yes  Enter date hired"], "11/02/2026")
        self.assertEqual(c["Text3"], "Test Cleaning Co")
        self.assertEqual(c["Text4"], "12-3456789")
        self.assertEqual(c["Telephone number"], "203-555-0100")
        self.conferir_assinatura(pdf, "ctw4")

    def test_msrra(self):
        c = campos(F.preencher("ctw4", dict(CTW4, codigo_retencao="E", msrra=True, estado_residencia="TX")))
        self.assertEqual((c["Check Box1"], c["residencedomicile"], c["1"]), ("/Yes", "TX", "E"))

    def test_validar(self):
        self.assertEqual(F.validar("ctw4", CTW4), [])
        self.assertIn("codigo_retencao:obrigatorio", F.validar("ctw4", dict(CTW4, codigo_retencao="")))
        self.assertIn("codigo_retencao:opcao_invalida", F.validar("ctw4", dict(CTW4, codigo_retencao="Z")))
        e = F.validar("ctw4", dict(CTW4, msrra=True))
        self.assertIn("estado_residencia:obrigatorio", e)
        self.assertIn("codigo_retencao:exige_codigo_e", e)


class TesteI9(Base):
    def test_secao1_autorizado_passaporte(self):
        pdf = F.preencher("i9", I9, assinatura_png=SIG, data_assinatura="2026-10-27")
        self.conferir_basico(pdf)
        c = campos(pdf)
        self.assertEqual(c["Last Name (Family Name)"], "Testelopez")
        self.assertEqual(c["First Name Given Name"], "Maria")
        self.assertEqual(c["Employee Middle Initial (if any)"], "J")
        self.assertEqual(c["Employee Other Last Names Used (if any)"], "N/A")
        self.assertEqual(c["Address Street Number and Name"], "123 Main St")
        self.assertEqual(c["Apt Number (if any)"], "2B")
        self.assertEqual(c["State"], "CT")
        self.assertEqual(c["Date of Birth mmddyyyy"], "05/17/1990")
        self.assertEqual(c["US Social Security Number"], "123456789")
        self.assertEqual(c["Telephone Number"], "203-555-0101")
        self.assertEqual([c["CB_%d" % i] for i in range(1, 5)], ["/Off", "/Off", "/Off", "/On"])
        self.assertEqual(c["Exp Date mmddyyyy"], F._fmt_data(FUTURO))
        self.assertEqual(c["Foreign Passport Number and Country of IssuanceRow1"], "X1234567, Mexico")
        self.assertEqual(c["USCIS ANumber"], "")
        self.assertEqual(c["Form I94 Admission Number"], "")
        self.assertEqual(c["3 A lawful permanent resident Enter USCIS or ANumber"], "")
        self.assertEqual(c["Today's Date mmddyyy"], "10/27/2026")
        self.assertIn(c.get("Signature of Employee"), (None, ""), "o campo de texto da assinatura fica vazio, a imagem vai por cima")
        self.conferir_assinatura(pdf, "i9")

    def test_residente_permanente(self):
        d = dict(BASE, data_nascimento="1985-01-02", status_cidadania="residente_permanente", residente_numero="A-123456789")
        c = campos(F.preencher("i9", d))
        self.assertEqual(c["CB_3"], "/On")
        self.assertEqual(c["3 A lawful permanent resident Enter USCIS or ANumber"], "A123456789")
        self.assertEqual(c["Exp Date mmddyyyy"], "")

    def test_cidadao_sem_ssn(self):
        d = dict(BASE, data_nascimento="1985-01-02", status_cidadania="cidadao")
        d.pop("ssn")
        self.assertEqual(F.validar("i9", d), [])
        c = campos(F.preencher("i9", d))
        self.assertEqual(c["CB_1"], "/On")
        self.assertEqual(c["US Social Security Number"], "")

    def test_autorizado_sem_vencimento_vira_na(self):
        d = dict(I9, autorizado_ate="", autorizado_documento="i94", i94_numero="12345678901")
        c = campos(F.preencher("i9", d))
        self.assertEqual(c["Exp Date mmddyyyy"], "N/A")
        self.assertEqual(c["Form I94 Admission Number"], "12345678901")
        self.assertEqual(c["Foreign Passport Number and Country of IssuanceRow1"], "")

    def test_validar_condicionais(self):
        self.assertEqual(F.validar("i9", I9), [])
        e = F.validar("i9", {})
        for k in ("sobrenome:obrigatorio", "primeiro_nome:obrigatorio", "data_nascimento:obrigatorio",
                  "status_cidadania:obrigatorio"):
            self.assertIn(k, e)
        self.assertNotIn("ssn:obrigatorio", e)
        rp = dict(I9, status_cidadania="residente_permanente")
        self.assertIn("residente_numero:obrigatorio", F.validar("i9", rp))
        self.assertIn("residente_numero:formato", F.validar("i9", dict(rp, residente_numero="12")))
        self.assertNotIn("autorizado_documento:obrigatorio", F.validar("i9", rp))
        au = dict(I9, autorizado_documento=None)
        self.assertIn("autorizado_documento:obrigatorio", F.validar("i9", au))
        self.assertIn("passaporte_pais:obrigatorio", F.validar("i9", dict(I9, passaporte_pais="")))
        self.assertIn("i94_numero:obrigatorio", F.validar("i9", dict(I9, autorizado_documento="i94")))
        self.assertIn("i94_numero:formato", F.validar("i9", dict(I9, autorizado_documento="i94", i94_numero="123")))
        self.assertIn("autorizado_uscis:obrigatorio", F.validar("i9", dict(I9, autorizado_documento="uscis")))
        self.assertIn("autorizado_ate:expirada", F.validar("i9", dict(I9, autorizado_ate="2020-01-01")))
        self.assertIn("data_nascimento:data_futura", F.validar("i9", dict(I9, data_nascimento=FUTURO)))
        self.assertIn("data_nascimento:data_invalida", F.validar("i9", dict(I9, data_nascimento="13/45/1990")))
        self.assertIn("email:formato", F.validar("i9", dict(I9, email="maria-arroba")))
        self.assertIn("ssn:formato", F.validar("i9", dict(I9, ssn="123-45-678")))
        self.assertIn("estado:opcao_invalida", F.validar("i9", dict(I9, estado="XX")))

    def test_secao2_listas_b_c(self):
        s1 = F.preencher("i9", I9, assinatura_png=SIG)
        pdf = F.preencher_i9_secao2(s1, dict(
            lista="BC", doc_b_titulo="Driver's license", doc_b_autoridade="CT DMV", doc_b_numero="TEST123",
            doc_b_validade="2030-01-01", doc_c_titulo="Social Security card", doc_c_autoridade="SSA",
            doc_c_numero="TESTCARD", primeiro_dia="2026-11-02", representante_nome="Tester, Ana, HR Manager",
            empresa_nome="Test Cleaning Co", empresa_endereco="1 Test Rd, Stamford, CT 06902", data="2026-11-02"),
            assinatura_png=SIG)
        self.conferir_basico(pdf)
        c = campos(pdf)
        self.assertEqual(c["List B Document 1 Title"], "Driver's license")
        self.assertEqual(c["List B Expiration Date 1"], "01/01/2030")
        self.assertEqual(c["List C Document Number 1"], "TESTCARD")
        self.assertEqual(c["List C Expiration Date 1"], "N/A")
        self.assertEqual(c["Document Title 1"], "")
        self.assertEqual(c["FirstDayEmployed mmddyyyy"], "11/02/2026")
        self.assertEqual(c["S2 Todays Date mmddyyyy"], "11/02/2026")
        self.assertEqual(c["Employers Business or Org Name"], "Test Cleaning Co")
        self.assertEqual(c["Last Name First Name and Title of Employer or Authorized Representative"],
                         "Tester, Ana, HR Manager")
        self.assertEqual(c["Last Name (Family Name)"], "Testelopez", "a Seção 1 continua preenchida")
        r = PdfReader(io.BytesIO(pdf))
        self.assertEqual(imagens_da_pagina(r.pages[0]), imagens_modelo("i9")[0] + 2, "assinatura da Seção 1 e da Seção 2")

    def test_secao2_lista_a(self):
        pdf = F.preencher_i9_secao2(F.preencher("i9", I9), dict(
            lista="A", doc_a_titulo="U.S. Passport", doc_a_autoridade="U.S. Dept of State", doc_a_numero="TEST000",
            doc_a_validade="2031-05-05", primeiro_dia="2026-11-02", representante_nome="Tester, Ana, HR",
            empresa_nome="Test Cleaning Co", empresa_endereco="1 Test Rd", procedimento_alternativo=True))
        c = campos(pdf)
        self.assertEqual(c["Document Title 1"], "U.S. Passport")
        self.assertEqual(c["Document Number 0 (if any)"], "TEST000")
        self.assertEqual(c["Expiration Date if any"], "05/05/2031")
        self.assertEqual(c["List B Document 1 Title"], "")
        self.assertEqual(c["CB_Alt"], "/Yes")
        self.assertEqual(c["S2 Todays Date mmddyyyy"], datetime.date.today().strftime("%m/%d/%Y"))

    def test_secao2_validar(self):
        e = F.validar("i9_secao2", {"lista": "BC"})
        for k in ("doc_b_titulo:obrigatorio", "doc_c_numero:obrigatorio", "primeiro_dia:obrigatorio",
                  "empresa_nome:obrigatorio"):
            self.assertIn(k, e)
        self.assertNotIn("doc_a_titulo:obrigatorio", e)
        self.assertIn("lista:obrigatorio", F.validar("i9_secao2", {}))


class TesteGeral(unittest.TestCase):
    def test_mascarar_ssn(self):
        self.assertEqual(F.mascarar_ssn("123456789"), "•••-••-6789")
        self.assertEqual(F.mascarar_ssn("123-45-6789"), "•••-••-6789")
        self.assertEqual(F.mascarar_ssn(""), "•••-••-••••")

    def test_tipo_invalido(self):
        self.assertEqual(F.validar("w2", {}), ["tipo:tipo_invalido"])
        with self.assertRaises(F.ErroFormulario):
            F.preencher("w2", {})

    def test_campos_bem_formados(self):
        tipos = {"text", "date", "select", "checkbox", "money", "ssn", "ein"}
        todos = [c for lista in F.CAMPOS.values() for c in lista]
        todos += [c for lista in F.CAMPOS_EMPREGADOR.values() for c in lista] + F.CAMPOS_I9_SECAO2
        for c in todos:
            self.assertIn(c["tipo"], tipos, c["chave"])
            for k in ("rotulo", "ajuda"):
                self.assertEqual(set(c[k]), {"pt", "en", "es"}, c["chave"])
                self.assertTrue(all(c[k].values()), c["chave"])
            if c["tipo"] == "select":
                self.assertTrue(c["opcoes"], c["chave"])
                for o in c["opcoes"]:
                    self.assertEqual(set(o["rotulo"]), {"pt", "en", "es"})
            if "condicao" in c:
                self.assertIn("campo", c["condicao"])
        self.assertEqual(set(F.CAMPOS), {"w9", "w4", "i9", "ctw4"})
        for tipo, lista in F.CAMPOS.items():
            chaves = [c["chave"] for c in lista]
            self.assertEqual(len(chaves), len(set(chaves)), tipo)
        for motivo in ("obrigatorio", "formato", "data_invalida", "opcao_invalida", "valor_invalido"):
            self.assertEqual(set(F.MENSAGENS_ERRO[motivo]), {"pt", "en", "es"})

    def test_assinatura_digitada_sem_imagem(self):
        pdf = F.preencher("w9", W9, nome_assinatura="Maria J Testelopez", data_assinatura="2026-10-27")
        r = PdfReader(io.BytesIO(pdf))
        self.assertEqual(imagens_da_pagina(r.pages[0]), imagens_modelo("w9")[0])
        self.assertIn("Maria J Testelopez", r.pages[0].extract_text())

    def test_assinatura_invalida(self):
        with self.assertRaises(ValueError):
            F.preencher("w9", W9, assinatura_png=b"nao e imagem")

    def test_acentos(self):
        c = campos(F.preencher("i9", dict(I9, primeiro_nome="José", sobrenome="Peña Gonçalves")))
        self.assertEqual(c["First Name Given Name"], "José")
        self.assertEqual(c["Last Name (Family Name)"], "Peña Gonçalves")

    def test_aes_puro_confere(self):
        import secrets
        for tam in (16, 24, 32):
            chave, iv, dados = secrets.token_bytes(tam), secrets.token_bytes(16), secrets.token_bytes(160)
            ct = F._aes_cbc_encrypt(chave, iv, dados)
            self.assertEqual(F._aes_cbc_decrypt(chave, iv, ct), dados)
            self.assertEqual(F._aes_ecb_decrypt(chave, F._aes_ecb_encrypt(chave, dados)), dados)
            try:
                from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            except ImportError:
                continue
            enc = Cipher(algorithms.AES(chave), modes.CBC(iv)).encryptor()
            self.assertEqual(ct, enc.update(dados) + enc.finalize())
        # Vetor oficial FIPS-197 (AES-128).
        self.assertEqual(F._aes_ecb_encrypt(bytes.fromhex("000102030405060708090a0b0c0d0e0f"),
                                            bytes.fromhex("00112233445566778899aabbccddeeff")).hex(),
                         "69c4e0d86a7b0430d8cdb78070b4c55a")

    def test_ctw4_sem_cryptography(self):
        """Abre o CT-W4 criptografado usando só o AES em Python puro (processo separado)."""
        codigo = (
            "import sys; sys.path.insert(0, %r)\n"
            "import formularios as F\n"
            "assert F._instalar_aes_puro(forcar=True)\n"
            "pdf = F.preencher('ctw4', %r)\n"
            "from pypdf import PdfReader; import io\n"
            "r = PdfReader(io.BytesIO(pdf)); assert not r.is_encrypted\n"
            "assert str(r.get_fields()['1']['/V']) == 'F'\n"
            "print('ok')\n" % (AQUI, CTW4))
        p = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, timeout=300)
        self.assertEqual(p.stdout.strip(), "ok", p.stderr[-500:])

    def test_sem_travessao_nem_print(self):
        for arq in ("formularios.py", "teste_formularios.py"):
            with open(os.path.join(AQUI, arq), encoding="utf-8") as f:
                txt = f.read()
            self.assertIsNone(re.search("[" + chr(0x2013) + chr(0x2014) + "]", txt), arq)
        with open(os.path.join(AQUI, "formularios.py"), encoding="utf-8") as f:
            txt = f.read()
        self.assertNotIn("print(", txt)
        self.assertNotIn("logging", txt)

    @unittest.skipUnless(os.environ.get("FORM_PNG") and shutil.which("sips"), "defina FORM_PNG=1 no macOS")
    def test_png_para_conferencia(self):
        pasta = tempfile.mkdtemp(prefix="formularios-png-")
        casos = {"w9": W9, "w4": W4, "ctw4": CTW4, "i9": I9}
        for tipo, d in casos.items():
            caminho = os.path.join(pasta, tipo + ".pdf")
            with open(caminho, "wb") as f:
                f.write(F.preencher(tipo, d, assinatura_png=SIG, data_assinatura="2026-10-27"))
            png = os.path.join(pasta, tipo + ".png")
            subprocess.run(["sips", "-s", "format", "png", caminho, "--out", png], capture_output=True, timeout=60)
            self.assertTrue(os.path.getsize(png) > 10000)
        sys.stderr.write("\nPNGs em %s\n" % pasta)


if __name__ == "__main__":
    unittest.main(verbosity=2)
