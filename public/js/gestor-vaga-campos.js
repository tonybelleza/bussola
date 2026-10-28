// Campos da vaga para o Google for Jobs (vagas_publicas.py): tipo de emprego,
// faixa salarial, endereço, remoto, validade e descrição pública mais longa.
// Usado por formVaga() em gestor.js: camposVagaHtml(v) e camposVagaLer(form).
Object.assign(I18N_GESTOR.pt, {
  vgc_titulo: "Publicação no Google for Jobs",
  vgc_hint: "Esses dados aparecem na página pública da vaga e ajudam a vaga a aparecer no Google.",
  vgc_tipo: "Tipo de emprego",
  vgc_tipo_vazio: "Não informado",
  vgc_tipo_FULL_TIME: "Tempo integral",
  vgc_tipo_PART_TIME: "Meio período",
  vgc_tipo_CONTRACTOR: "Prestador de serviço",
  vgc_tipo_TEMPORARY: "Temporário",
  vgc_tipo_PER_DIEM: "Por diária",
  vgc_sal_min: "Salário mínimo",
  vgc_sal_max: "Salário máximo",
  vgc_unidade: "Por",
  vgc_un_HOUR: "Hora",
  vgc_un_DAY: "Dia",
  vgc_un_WEEK: "Semana",
  vgc_un_MONTH: "Mês",
  vgc_un_YEAR: "Ano",
  vgc_moeda: "Moeda",
  vgc_cidade: "Cidade",
  vgc_estado: "Estado",
  vgc_cep: "CEP / ZIP",
  vgc_remoto: "Vaga remota",
  vgc_validade: "Inscrições até (opcional)",
  vgc_desc_rica: "Descrição pública completa (opcional)",
  vgc_desc_rica_hint: "Use linhas em branco entre parágrafos e - no início de cada item de lista. Se ficar vazia, usamos a descrição acima.",
  vgc_link: "Página pública da vaga",
});
Object.assign(I18N_GESTOR.en, {
  vgc_titulo: "Google for Jobs listing",
  vgc_hint: "These details show on the public job page and help the job appear on Google.",
  vgc_tipo: "Employment type",
  vgc_tipo_vazio: "Not specified",
  vgc_tipo_FULL_TIME: "Full-time",
  vgc_tipo_PART_TIME: "Part-time",
  vgc_tipo_CONTRACTOR: "Contractor",
  vgc_tipo_TEMPORARY: "Temporary",
  vgc_tipo_PER_DIEM: "Per diem",
  vgc_sal_min: "Minimum pay",
  vgc_sal_max: "Maximum pay",
  vgc_unidade: "Per",
  vgc_un_HOUR: "Hour",
  vgc_un_DAY: "Day",
  vgc_un_WEEK: "Week",
  vgc_un_MONTH: "Month",
  vgc_un_YEAR: "Year",
  vgc_moeda: "Currency",
  vgc_cidade: "City",
  vgc_estado: "State",
  vgc_cep: "ZIP code",
  vgc_remoto: "Remote job",
  vgc_validade: "Apply by (optional)",
  vgc_desc_rica: "Full public description (optional)",
  vgc_desc_rica_hint: "Leave a blank line between paragraphs and start each list item with -. If left empty, we use the description above.",
  vgc_link: "Public job page",
});
Object.assign(I18N_GESTOR.es, {
  vgc_titulo: "Publicación en Google for Jobs",
  vgc_hint: "Estos datos aparecen en la página pública de la vacante y ayudan a que aparezca en Google.",
  vgc_tipo: "Tipo de empleo",
  vgc_tipo_vazio: "No especificado",
  vgc_tipo_FULL_TIME: "Tiempo completo",
  vgc_tipo_PART_TIME: "Medio tiempo",
  vgc_tipo_CONTRACTOR: "Contratista",
  vgc_tipo_TEMPORARY: "Temporal",
  vgc_tipo_PER_DIEM: "Por día",
  vgc_sal_min: "Salario mínimo",
  vgc_sal_max: "Salario máximo",
  vgc_unidade: "Por",
  vgc_un_HOUR: "Hora",
  vgc_un_DAY: "Día",
  vgc_un_WEEK: "Semana",
  vgc_un_MONTH: "Mes",
  vgc_un_YEAR: "Año",
  vgc_moeda: "Moneda",
  vgc_cidade: "Ciudad",
  vgc_estado: "Estado",
  vgc_cep: "Código postal",
  vgc_remoto: "Vacante remota",
  vgc_validade: "Postulaciones hasta (opcional)",
  vgc_desc_rica: "Descripción pública completa (opcional)",
  vgc_desc_rica_hint: "Deja una línea en blanco entre párrafos y empieza cada elemento de lista con -. Si queda vacía, usamos la descripción de arriba.",
  vgc_link: "Página pública de la vacante",
});

const VGC_TIPOS = ["FULL_TIME", "PART_TIME", "CONTRACTOR", "TEMPORARY", "PER_DIEM"];
const VGC_UNIDADES = ["HOUR", "DAY", "WEEK", "MONTH", "YEAR"];
const VGC_MOEDAS = ["USD", "BRL", "EUR", "GBP", "CAD", "MXN"];

function camposVagaHtml(v) {
  const x = v || {};
  const val = (k) => (x[k] === null || x[k] === undefined ? "" : esc(String(x[k])));
  const moeda = x.moeda || "USD";
  const moedas = VGC_MOEDAS.includes(moeda) ? VGC_MOEDAS : VGC_MOEDAS.concat([moeda]);
  const link = v && v.id && v.status === "aberta"
    ? `<p class="desc" style="margin:0 0 10px">${tg("vgc_link")}: <a href="/vaga?id=${v.id}" target="_blank" rel="noopener">/vaga?id=${v.id}</a></p>`
    : "";
  return `
    <fieldset style="border:1px solid var(--line-soft);border-radius:10px;padding:12px 14px;margin:6px 0 14px">
      <legend style="padding:0 6px;font-size:.85rem">${tg("vgc_titulo")}</legend>
      <p class="desc" style="margin:0 0 10px">${tg("vgc_hint")}</p>
      ${link}
      <label class="field">${tg("vgc_tipo")}
        <select id="fv-tipo-emprego">
          <option value="">${tg("vgc_tipo_vazio")}</option>
          ${VGC_TIPOS.map((t) => `<option value="${t}" ${x.tipo_emprego === t ? "selected" : ""}>${tg("vgc_tipo_" + t)}</option>`).join("")}
        </select>
      </label>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <label class="field" style="flex:1;min-width:120px">${tg("vgc_sal_min")}
          <input type="number" min="0" step="0.01" id="fv-sal-min" value="${val("salario_min")}">
        </label>
        <label class="field" style="flex:1;min-width:120px">${tg("vgc_sal_max")}
          <input type="number" min="0" step="0.01" id="fv-sal-max" value="${val("salario_max")}">
        </label>
        <label class="field" style="flex:1;min-width:100px">${tg("vgc_unidade")}
          <select id="fv-sal-unidade">
            <option value=""></option>
            ${VGC_UNIDADES.map((u) => `<option value="${u}" ${x.salario_unidade === u ? "selected" : ""}>${tg("vgc_un_" + u)}</option>`).join("")}
          </select>
        </label>
        <label class="field" style="flex:1;min-width:90px">${tg("vgc_moeda")}
          <select id="fv-moeda">
            ${moedas.map((m) => `<option value="${esc(m)}" ${m === moeda ? "selected" : ""}>${esc(m)}</option>`).join("")}
          </select>
        </label>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <label class="field" style="flex:2;min-width:140px">${tg("vgc_cidade")}
          <input type="text" id="fv-cidade" maxlength="100" value="${val("endereco_cidade")}">
        </label>
        <label class="field" style="flex:1;min-width:90px">${tg("vgc_estado")}
          <input type="text" id="fv-estado" maxlength="60" value="${val("endereco_estado")}">
        </label>
        <label class="field" style="flex:1;min-width:90px">${tg("vgc_cep")}
          <input type="text" id="fv-cep" maxlength="20" value="${val("endereco_cep")}">
        </label>
      </div>
      <label class="field" style="display:flex;align-items:center;gap:8px">
        <input type="checkbox" id="fv-remoto" style="width:auto;margin:0" ${x.remoto ? "checked" : ""}> ${tg("vgc_remoto")}
      </label>
      <label class="field">${tg("vgc_validade")}
        <input type="date" id="fv-validade" value="${val("data_validade")}">
      </label>
      <label class="field">${tg("vgc_desc_rica")} <span class="hint">${tg("vgc_desc_rica_hint")}</span>
        <textarea id="fv-desc-rica" rows="6">${val("descricao_rica")}</textarea>
      </label>
    </fieldset>`;
}

function camposVagaLer(f) {
  const q = (id) => f.querySelector("#" + id);
  if (!q("fv-tipo-emprego")) return {};
  return {
    tipo_emprego: q("fv-tipo-emprego").value,
    salario_min: q("fv-sal-min").value.trim(),
    salario_max: q("fv-sal-max").value.trim(),
    salario_unidade: q("fv-sal-unidade").value,
    moeda: q("fv-moeda").value,
    endereco_cidade: q("fv-cidade").value.trim(),
    endereco_estado: q("fv-estado").value.trim(),
    endereco_cep: q("fv-cep").value.trim(),
    remoto: q("fv-remoto").checked,
    data_validade: q("fv-validade").value,
    descricao_rica: q("fv-desc-rica").value.trim(),
  };
}
