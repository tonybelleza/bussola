/* =====================================================================
   Ícones minimalistas (traço fino, estilo premium) — sem emojis
   ===================================================================== */

function icone(nome, tam) {
  const paths = ICONES[nome] || "";
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
    stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
    ${tam ? `style="width:${tam}px;height:${tam}px"` : ""}>${paths}</svg>`;
}

const ICONES = {
  // arquétipos B.A.S.E.
  bussola: '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2.2 5-5 2.2 2.2-5z"/>',
  raio: '<path d="M13 3L5 13.5h5.5L10 21l8-10.5h-5.5z"/>',
  coracao: '<path d="M12 20s-7-4.6-9-9c-1.2-2.8.6-6 3.7-6C8.7 5 10.5 6.3 12 8c1.5-1.7 3.3-3 5.3-3 3.1 0 4.9 3.2 3.7 6-2 4.4-9 9-9 9z"/>',
  grafico: '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-8"/><path d="M22 20H2"/>',
  // interface
  camadas: '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
  alvo: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r=".5"/>',
  barras: '<path d="M5 20v-6"/><path d="M12 20V8"/><path d="M19 20v-10"/>',
  documento: '<path d="M14 3H7a1.5 1.5 0 0 0-1.5 1.5v15A1.5 1.5 0 0 0 7 21h10a1.5 1.5 0 0 0 1.5-1.5V7.5z"/><path d="M14 3v4.5h4.5"/>',
  usuario: '<circle cx="12" cy="8" r="4"/><path d="M4.5 20c1.5-3.5 4.2-5 7.5-5s6 1.5 7.5 5"/>',
  usuarios: '<circle cx="9" cy="8.5" r="3.5"/><path d="M2.5 19.5c1.2-3 3.5-4.5 6.5-4.5s5.3 1.5 6.5 4.5"/><path d="M16 5.6a3.5 3.5 0 0 1 0 5.8"/><path d="M18.5 15.4c1.6.8 2.6 2.1 3 4.1"/>',
  pasta: '<path d="M3 6.5A1.5 1.5 0 0 1 4.5 5h4L11 8h8.5A1.5 1.5 0 0 1 21 9.5v8a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5z"/>',
  matriz: '<rect x="3.5" y="3.5" width="17" height="17" rx="2"/><path d="M3.5 9.5h17"/><path d="M3.5 15h17"/><path d="M9.5 3.5v17"/><path d="M15 3.5v17"/>',
  engrenagem: '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M18.7 5.3l-2.1 2.1M7.4 16.6l-2.1 2.1"/>',
  cadeado: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7.5a4 4 0 0 1 8 0V11"/>',
  chave: '<circle cx="8" cy="15.5" r="4.5"/><path d="M11.2 12.3L20 3.5"/><path d="M16.5 7l2.5 2.5"/>',
  link: '<path d="M10 14a4.5 4.5 0 0 0 6.4.4l3-3a4.5 4.5 0 0 0-6.4-6.4l-1.5 1.5"/><path d="M14 10a4.5 4.5 0 0 0-6.4-.4l-3 3a4.5 4.5 0 0 0 6.4 6.4L12.5 17.5"/>',
  check: '<path d="M4.5 12.5l5 5 10-11"/>',
  seta: '<path d="M4 12h16"/><path d="M14 6l6 6-6 6"/>',
  setaEsq: '<path d="M20 12H4"/><path d="M10 6l-6 6 6 6"/>',
  mais: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  lapis: '<path d="M4 20l1-4L16.5 4.5a2.1 2.1 0 0 1 3 3L8 19z"/><path d="M14.5 6.5l3 3"/>',
  lixeira: '<path d="M4.5 6.5h15"/><path d="M8 6.5V5a1.5 1.5 0 0 1 1.5-1.5h5A1.5 1.5 0 0 1 16 5v1.5"/><path d="M6.5 6.5l1 13A1.5 1.5 0 0 0 9 21h6a1.5 1.5 0 0 0 1.5-1.5l1-13"/>',
  fechar: '<path d="M6 6l12 12"/><path d="M18 6L6 18"/>',
  impressora: '<path d="M7 8V3.5h10V8"/><rect x="4" y="8" width="16" height="8" rx="1.5"/><path d="M7 13h10v7.5H7z"/>',
  anexo: '<path d="M20 11.5l-8 8a5 5 0 0 1-7-7l8.5-8.5a3.3 3.3 0 0 1 4.7 4.7L9.7 17.2a1.7 1.7 0 0 1-2.4-2.4L15 7"/>',
  relatorio: '<path d="M14 3H7a1.5 1.5 0 0 0-1.5 1.5v15A1.5 1.5 0 0 0 7 21h10a1.5 1.5 0 0 0 1.5-1.5V7.5z"/><path d="M14 3v4.5h4.5"/><path d="M9 15.5v-2"/><path d="M12 15.5v-4"/><path d="M15 15.5v-6"/>',
  medalha: '<circle cx="12" cy="9" r="5.5"/><path d="M8.8 13.5L7 21l5-2.5L17 21l-1.8-7.5"/>',
  bloco: '<rect x="4" y="3.5" width="16" height="17" rx="2"/><path d="M8.5 8.5h7"/><path d="M8.5 12h7"/><path d="M8.5 15.5h4.5"/>',
  estrela: '<path d="M12 3.5l2.6 5.3 5.9.9-4.2 4.1 1 5.8L12 16.9l-5.3 2.7 1-5.8-4.2-4.1 5.9-.9z"/>',
  aspas: '<path d="M9.5 7.5c-2.6.8-4 2.7-4 5.2V17h5v-4.5h-3c0-1.8 1-3 3-3.7z"/><path d="M19 7.5c-2.6.8-4 2.7-4 5.2V17h5v-4.5h-3c0-1.8 1-3 3-3.7z"/>',
};
