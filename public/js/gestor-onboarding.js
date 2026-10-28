/* =====================================================================
   Onboarding de novos contratados no painel do gestor (onboarding.py).
   - onboardingPreencherFicha: bloco "Onboarding" na ficha do candidato
     (enviar proposta, progresso, documentos, dados mascarados com "revelar",
     reenviar, cancelar, contratado e I-9 Seção 2).
   - onboardingVisao: cartão na visão geral com quem está em onboarding.
   - secaoOnboarding: cartão em Configurações (só o administrador).
   Textos em pt, en e es (tg do i18n-gestor.js, chaves "onb_*").
   ===================================================================== */

Object.assign(I18N_GESTOR.pt, {
  onb_titulo: "Onboarding", onb_enviar: "Enviar proposta e onboarding", onb_nenhum: "Nenhum onboarding enviado para este candidato.",
  onb_sem_email: "Candidato sem e-mail", onb_so_admin: "Só o administrador da empresa envia a proposta.",
  onb_status: { enviado: "Enviado", em_andamento: "Em andamento", concluido: "Concluído", cancelado: "Cancelado" },
  onb_etapas: { oferta: "Carta de proposta", dados: "Dados pessoais", documentos: "Documentos assinados", formularios: "Formulários fiscais",
    arquivos: "Envio de documentos", pagamento: "Forma de pagamento", revisao: "Revisão e envio" },
  onb_tipo: { w2: "Empregado (W-2)", 1099: "Prestador (1099)" },
  onb_unidades: { hora: "por hora", dia: "por dia", servico: "por serviço", salario: "por ano (salário)" },
  onb_metodos: { deposito: "Depósito direto", zelle: "Zelle", cheque: "Cheque em papel", provedor: "Sistema de folha (Gusto, QuickBooks)" },
  onb_forms: { w4: "W-4", i9: "I-9 (Seção 1)", ctw4: "CT-W4", w9: "W-9" },
  onb_cats: { id_frente: "Documento com foto (frente)", id_verso: "Documento com foto (verso)", cnh_frente: "Carteira de motorista (frente)",
    cnh_verso: "Carteira de motorista (verso)", i9_lista_a: "I-9 Lista A", i9_lista_b: "I-9 Lista B", i9_lista_c: "I-9 Lista C",
    comprovante_endereco: "Comprovante de endereço", cheque_anulado: "Cheque anulado" },
  onb_pct: "{pct}% concluído", onb_prazo: "Prazo: {data}", onb_atrasado: "Atrasado", onb_inicio: "Início: {data}",
  onb_link: "Link do novo contratado", onb_copiar: "Copiar link", onb_copiado: "Copiado!", onb_reenviar: "Reenviar link",
  onb_reenviado: "Link reenviado.", onb_cancelar: "Cancelar onboarding", onb_confirmar_cancelar: "Cancelar este onboarding? O link deixa de funcionar.",
  onb_contratado: "Mover para Contratado", onb_movido: "Candidatura movida para Contratado.",
  onb_docs: "Documentos e arquivos", onb_baixar: "Baixar", onb_dados: "Dados pessoais", onb_sensiveis: "Dados sensíveis (cifrados)",
  onb_revelar: "Revelar", onb_revelar_aviso: "Revelar este dado? O acesso fica registrado no histórico de acessos.",
  onb_pagamento: "Pagamento", onb_nada: "Nada enviado ainda.",
  onb_campos: { nome_legal: "Nome legal", nome_preferido: "Nome preferido", endereco: "Endereço", apto: "Apto", cidade: "Cidade",
    estado: "Estado", cep: "ZIP", telefone: "Telefone", email: "E-mail", contato_nome: "Contato de emergência",
    contato_relacao: "Relação", contato_telefone: "Telefone do contato", tamanho: "Tamanho", cnh_estado: "Estado da carteira",
    banco: "Banco", tipo_conta: "Tipo de conta", zelle: "Zelle", endereco_cheque: "Endereço do cheque",
    nascimento: "Data de nascimento", cnh_numero: "Número da carteira", routing: "Routing", conta: "Conta", ssn: "SSN", ein: "EIN", itin: "ITIN" },
  onb_i9: "Formulário I-9, Seção 2 (empregador)", onb_i9_prazo: "Prazo: {data} (3 dias úteis depois do primeiro dia)",
  onb_i9_feito: "Seção 2 preenchida.", onb_i9_falta_s1: "Aguardando a Seção 1 do novo contratado.",
  onb_i9_dica: "Confira pessoalmente os documentos originais (não cópias) antes de preencher. Os uploads servem só de referência.",
  onb_i9_abrir: "Preencher a Seção 2", onb_i9_salvar: "Gerar I-9 com a Seção 2", onb_assinatura: "Assinatura do representante",
  onb_limpar: "Limpar", onb_purgar: "Apagar dados sensíveis (retenção)", onb_purgar_aviso: "Apagar os dados sensíveis cifrados deste onboarding? Os PDFs oficiais continuam guardados.",
  onb_purgado: "Dados sensíveis apagados em {data}.", onb_erro_chave: "Chave de criptografia ausente ou diferente: os dados sensíveis não podem ser lidos.",
  onb_f_titulo: "Enviar proposta e onboarding", onb_f_tipo: "Tipo de vínculo", onb_f_cargo: "Cargo", onb_f_inicio: "Data de início",
  onb_f_valor: "Pagamento (US$)", onb_f_unidade: "Unidade", onb_f_horario: "Horário / escala", onb_f_notas: "Observações para o novo contratado",
  onb_f_dirige: "O cargo dirige entre as casas (pede carteira de motorista)", onb_f_experiencia: "Período de experiência (dias)",
  onb_f_docs: "Documentos para assinar", onb_f_forms: "Formulários fiscais", onb_f_metodos: "Formas de pagamento aceitas",
  onb_f_prazo: "Prazo para concluir", onb_f_enviar: "Enviar", onb_f_enviado: "Proposta enviada.", onb_f_enviado_sem_email: "Onboarding criado, mas o e-mail não saiu: {msg}. Copie o link e envie.",
  onb_f_forms_indisp: "Os formulários fiscais ainda não estão instalados no servidor.",
  onb_v_titulo: "Em onboarding", onb_v_vazio: "Ninguém em onboarding agora.", onb_v_pendentes: "Falta: {itens}", onb_v_i9: "I-9 Seção 2 até {data}",
  onb_c_titulo: "Onboarding", onb_c_desc: "Documentos, formas de pagamento, formulários estaduais, prazos, lembretes e retenção do onboarding de novos contratados. Os modelos padrão são um ponto de partida: revise com o seu advogado antes de usar.",
  onb_c_metodos: "Formas de pagamento aceitas", onb_c_estaduais: "Formulários estaduais (W-2)", onb_c_prazo: "Prazo padrão (dias)",
  onb_c_lembrete: "Lembrete ao novo contratado a cada (dias, 0 = desligado)", onb_c_retencao: "Oferecer apagar dados sensíveis depois de (dias, 0 = guardar)",
  onb_c_experiencia: "Período de experiência padrão (dias)", onb_c_provedor: "Nome do sistema de folha", onb_c_ordem: "Ordem das etapas",
  onb_c_empregador: "Dados do empregador (formulários oficiais)", onb_c_emp_nome: "Nome legal da empresa", onb_c_emp_end: "Endereço",
  onb_c_emp_cidade: "Cidade, estado e ZIP", onb_c_emp_ein: "EIN", onb_c_emp_contato: "Pessoa de contato", onb_c_emp_tel: "Telefone",
  onb_c_salvar: "Salvar onboarding", onb_c_salvo: "Configurações salvas.", onb_c_modelos: "Modelos de documentos", onb_c_novo: "Novo documento",
  onb_c_editar: "Editar", onb_c_excluir: "Excluir", onb_c_confirmar_excluir: "Excluir este modelo?", onb_c_inativo: "inativo",
  onb_m_titulo: "Título ({l})", onb_m_texto: "Texto ({l})", onb_m_categoria: "Categoria", onb_m_cat: { oferta: "Carta de proposta", documento: "Documento para assinar" },
  onb_m_aplica: "Vale para", onb_m_aplica_op: { w2: "W-2", 1099: "1099", ambos: "W-2 e 1099" }, onb_m_ordem: "Ordem",
  onb_m_declaracao: "Pede declaração pessoal", onb_m_ativo: "Ativo", onb_m_tipo: "Formato", onb_m_tipo_op: { texto: "Texto com variáveis", pdf: "PDF enviado (assinatura no fim)" },
  onb_m_pdf: "PDF (até 8 MB)", onb_m_vars: "Variáveis: {{nome}}, {{empresa}}, {{cargo}}, {{data_inicio}}, {{pagamento}}, {{horario}}, {{periodo_experiencia}}, {{prazo}}, {{representante}}, {{data}}. Use \"# \" para título, \"## \" para seção, \"- \" para item.",
  onb_subir: "Subir", onb_descer: "Descer",
});
Object.assign(I18N_GESTOR.en, {
  onb_titulo: "Onboarding", onb_enviar: "Send offer and onboarding", onb_nenhum: "No onboarding sent to this candidate yet.",
  onb_sem_email: "This candidate has no email", onb_so_admin: "Only the company admin can send the offer.",
  onb_status: { enviado: "Sent", em_andamento: "In progress", concluido: "Complete", cancelado: "Canceled" },
  onb_etapas: { oferta: "Offer letter", dados: "Personal info", documentos: "Signed documents", formularios: "Tax forms",
    arquivos: "Document uploads", pagamento: "Payment setup", revisao: "Review and submit" },
  onb_tipo: { w2: "Employee (W-2)", 1099: "Contractor (1099)" },
  onb_unidades: { hora: "per hour", dia: "per day", servico: "per service", salario: "per year (salary)" },
  onb_metodos: { deposito: "Direct deposit", zelle: "Zelle", cheque: "Paper check", provedor: "Payroll provider (Gusto, QuickBooks)" },
  onb_forms: { w4: "W-4", i9: "I-9 (Section 1)", ctw4: "CT-W4", w9: "W-9" },
  onb_cats: { id_frente: "Photo ID (front)", id_verso: "Photo ID (back)", cnh_frente: "Driver's license (front)",
    cnh_verso: "Driver's license (back)", i9_lista_a: "I-9 List A", i9_lista_b: "I-9 List B", i9_lista_c: "I-9 List C",
    comprovante_endereco: "Proof of address", cheque_anulado: "Voided check" },
  onb_pct: "{pct}% complete", onb_prazo: "Deadline: {data}", onb_atrasado: "Overdue", onb_inicio: "Starts: {data}",
  onb_link: "New hire link", onb_copiar: "Copy link", onb_copiado: "Copied!", onb_reenviar: "Resend link",
  onb_reenviado: "Link resent.", onb_cancelar: "Cancel onboarding", onb_confirmar_cancelar: "Cancel this onboarding? The link will stop working.",
  onb_contratado: "Move to Hired", onb_movido: "Application moved to Hired.",
  onb_docs: "Documents and files", onb_baixar: "Download", onb_dados: "Personal info", onb_sensiveis: "Sensitive data (encrypted)",
  onb_revelar: "Reveal", onb_revelar_aviso: "Reveal this value? The access is recorded in the access history.",
  onb_pagamento: "Payment", onb_nada: "Nothing submitted yet.",
  onb_campos: { nome_legal: "Legal name", nome_preferido: "Preferred name", endereco: "Address", apto: "Apt", cidade: "City",
    estado: "State", cep: "ZIP", telefone: "Phone", email: "Email", contato_nome: "Emergency contact",
    contato_relacao: "Relationship", contato_telefone: "Contact phone", tamanho: "Size", cnh_estado: "License state",
    banco: "Bank", tipo_conta: "Account type", zelle: "Zelle", endereco_cheque: "Check mailing address",
    nascimento: "Date of birth", cnh_numero: "License number", routing: "Routing", conta: "Account", ssn: "SSN", ein: "EIN", itin: "ITIN" },
  onb_i9: "Form I-9, Section 2 (employer)", onb_i9_prazo: "Due: {data} (3 business days after the first day of work)",
  onb_i9_feito: "Section 2 completed.", onb_i9_falta_s1: "Waiting for the new hire's Section 1.",
  onb_i9_dica: "Examine the original documents in person (not copies) before filling this in. Uploads are for reference only.",
  onb_i9_abrir: "Fill out Section 2", onb_i9_salvar: "Generate I-9 with Section 2", onb_assinatura: "Employer representative signature",
  onb_limpar: "Clear", onb_purgar: "Delete sensitive data (retention)", onb_purgar_aviso: "Delete the encrypted sensitive data for this onboarding? The official PDFs are kept.",
  onb_purgado: "Sensitive data deleted on {data}.", onb_erro_chave: "Encryption key missing or different: sensitive data can't be read.",
  onb_f_titulo: "Send offer and onboarding", onb_f_tipo: "Employment type", onb_f_cargo: "Position", onb_f_inicio: "Start date",
  onb_f_valor: "Pay (US$)", onb_f_unidade: "Unit", onb_f_horario: "Schedule", onb_f_notas: "Notes for the new hire",
  onb_f_dirige: "This position drives between homes (asks for a driver's license)", onb_f_experiencia: "Introductory period (days)",
  onb_f_docs: "Documents to sign", onb_f_forms: "Tax forms", onb_f_metodos: "Payment methods accepted",
  onb_f_prazo: "Deadline to finish", onb_f_enviar: "Send", onb_f_enviado: "Offer sent.", onb_f_enviado_sem_email: "Onboarding created, but the email didn't go out: {msg}. Copy the link and send it.",
  onb_f_forms_indisp: "Tax forms are not installed on the server yet.",
  onb_v_titulo: "In onboarding", onb_v_vazio: "No one is onboarding right now.", onb_v_pendentes: "Missing: {itens}", onb_v_i9: "I-9 Section 2 due {data}",
  onb_c_titulo: "Onboarding", onb_c_desc: "Documents, payment methods, state forms, deadlines, reminders, and retention for new hire onboarding. The default templates are a starting point: review them with your attorney before use.",
  onb_c_metodos: "Payment methods accepted", onb_c_estaduais: "State forms (W-2)", onb_c_prazo: "Default deadline (days)",
  onb_c_lembrete: "Remind the new hire every (days, 0 = off)", onb_c_retencao: "Offer to delete sensitive data after (days, 0 = keep)",
  onb_c_experiencia: "Default introductory period (days)", onb_c_provedor: "Payroll provider name", onb_c_ordem: "Step order",
  onb_c_empregador: "Employer details (official forms)", onb_c_emp_nome: "Legal business name", onb_c_emp_end: "Address",
  onb_c_emp_cidade: "City, state, and ZIP", onb_c_emp_ein: "EIN", onb_c_emp_contato: "Contact person", onb_c_emp_tel: "Phone",
  onb_c_salvar: "Save onboarding", onb_c_salvo: "Settings saved.", onb_c_modelos: "Document templates", onb_c_novo: "New document",
  onb_c_editar: "Edit", onb_c_excluir: "Delete", onb_c_confirmar_excluir: "Delete this template?", onb_c_inativo: "inactive",
  onb_m_titulo: "Title ({l})", onb_m_texto: "Text ({l})", onb_m_categoria: "Category", onb_m_cat: { oferta: "Offer letter", documento: "Document to sign" },
  onb_m_aplica: "Applies to", onb_m_aplica_op: { w2: "W-2", 1099: "1099", ambos: "W-2 and 1099" }, onb_m_ordem: "Order",
  onb_m_declaracao: "Asks for a personal statement", onb_m_ativo: "Active", onb_m_tipo: "Format", onb_m_tipo_op: { texto: "Text with variables", pdf: "Uploaded PDF (signed at the end)" },
  onb_m_pdf: "PDF (up to 8 MB)", onb_m_vars: "Variables: {{nome}}, {{empresa}}, {{cargo}}, {{data_inicio}}, {{pagamento}}, {{horario}}, {{periodo_experiencia}}, {{prazo}}, {{representante}}, {{data}}. Use \"# \" for a title, \"## \" for a section, \"- \" for a list item.",
  onb_subir: "Up", onb_descer: "Down",
});
Object.assign(I18N_GESTOR.es, {
  onb_titulo: "Incorporación", onb_enviar: "Enviar oferta e incorporación", onb_nenhum: "Todavía no se envió ninguna incorporación a este candidato.",
  onb_sem_email: "El candidato no tiene correo", onb_so_admin: "Solo el administrador de la empresa envía la oferta.",
  onb_status: { enviado: "Enviada", em_andamento: "En curso", concluido: "Completa", cancelado: "Cancelada" },
  onb_etapas: { oferta: "Carta de oferta", dados: "Datos personales", documentos: "Documentos firmados", formularios: "Formularios de impuestos",
    arquivos: "Envío de documentos", pagamento: "Forma de pago", revisao: "Revisión y envío" },
  onb_tipo: { w2: "Empleado (W-2)", 1099: "Contratista (1099)" },
  onb_unidades: { hora: "por hora", dia: "por día", servico: "por servicio", salario: "por año (salario)" },
  onb_metodos: { deposito: "Depósito directo", zelle: "Zelle", cheque: "Cheque en papel", provedor: "Sistema de nómina (Gusto, QuickBooks)" },
  onb_forms: { w4: "W-4", i9: "I-9 (Sección 1)", ctw4: "CT-W4", w9: "W-9" },
  onb_cats: { id_frente: "Identificación con foto (frente)", id_verso: "Identificación con foto (reverso)", cnh_frente: "Licencia de conducir (frente)",
    cnh_verso: "Licencia de conducir (reverso)", i9_lista_a: "I-9 Lista A", i9_lista_b: "I-9 Lista B", i9_lista_c: "I-9 Lista C",
    comprovante_endereco: "Comprobante de domicilio", cheque_anulado: "Cheque anulado" },
  onb_pct: "{pct}% completado", onb_prazo: "Fecha límite: {data}", onb_atrasado: "Atrasado", onb_inicio: "Inicio: {data}",
  onb_link: "Enlace del nuevo empleado", onb_copiar: "Copiar enlace", onb_copiado: "¡Copiado!", onb_reenviar: "Reenviar enlace",
  onb_reenviado: "Enlace reenviado.", onb_cancelar: "Cancelar incorporación", onb_confirmar_cancelar: "¿Cancelar esta incorporación? El enlace dejará de funcionar.",
  onb_contratado: "Mover a Contratado", onb_movido: "Candidatura movida a Contratado.",
  onb_docs: "Documentos y archivos", onb_baixar: "Descargar", onb_dados: "Datos personales", onb_sensiveis: "Datos sensibles (cifrados)",
  onb_revelar: "Mostrar", onb_revelar_aviso: "¿Mostrar este dato? El acceso queda registrado en el historial de accesos.",
  onb_pagamento: "Pago", onb_nada: "Todavía no se envió nada.",
  onb_campos: { nome_legal: "Nombre legal", nome_preferido: "Nombre preferido", endereco: "Dirección", apto: "Apto", cidade: "Ciudad",
    estado: "Estado", cep: "ZIP", telefone: "Teléfono", email: "Correo", contato_nome: "Contacto de emergencia",
    contato_relacao: "Relación", contato_telefone: "Teléfono del contacto", tamanho: "Talla", cnh_estado: "Estado de la licencia",
    banco: "Banco", tipo_conta: "Tipo de cuenta", zelle: "Zelle", endereco_cheque: "Dirección para el cheque",
    nascimento: "Fecha de nacimiento", cnh_numero: "Número de licencia", routing: "Routing", conta: "Cuenta", ssn: "SSN", ein: "EIN", itin: "ITIN" },
  onb_i9: "Formulario I-9, Sección 2 (empleador)", onb_i9_prazo: "Vence: {data} (3 días hábiles después del primer día de trabajo)",
  onb_i9_feito: "Sección 2 completada.", onb_i9_falta_s1: "Esperando la Sección 1 del nuevo empleado.",
  onb_i9_dica: "Revisa en persona los documentos originales (no copias) antes de llenarla. Los archivos subidos son solo de referencia.",
  onb_i9_abrir: "Llenar la Sección 2", onb_i9_salvar: "Generar I-9 con la Sección 2", onb_assinatura: "Firma del representante del empleador",
  onb_limpar: "Borrar", onb_purgar: "Borrar datos sensibles (retención)", onb_purgar_aviso: "¿Borrar los datos sensibles cifrados de esta incorporación? Los PDF oficiales se conservan.",
  onb_purgado: "Datos sensibles borrados el {data}.", onb_erro_chave: "Falta la clave de cifrado o es diferente: no se pueden leer los datos sensibles.",
  onb_f_titulo: "Enviar oferta e incorporación", onb_f_tipo: "Tipo de vínculo", onb_f_cargo: "Puesto", onb_f_inicio: "Fecha de inicio",
  onb_f_valor: "Pago (US$)", onb_f_unidade: "Unidad", onb_f_horario: "Horario", onb_f_notas: "Notas para el nuevo empleado",
  onb_f_dirige: "Este puesto maneja entre casas (pide licencia de conducir)", onb_f_experiencia: "Período de prueba (días)",
  onb_f_docs: "Documentos para firmar", onb_f_forms: "Formularios de impuestos", onb_f_metodos: "Formas de pago aceptadas",
  onb_f_prazo: "Fecha límite para terminar", onb_f_enviar: "Enviar", onb_f_enviado: "Oferta enviada.", onb_f_enviado_sem_email: "Incorporación creada, pero el correo no salió: {msg}. Copia el enlace y envíalo.",
  onb_f_forms_indisp: "Los formularios de impuestos todavía no están instalados en el servidor.",
  onb_v_titulo: "En incorporación", onb_v_vazio: "Nadie en incorporación ahora.", onb_v_pendentes: "Falta: {itens}", onb_v_i9: "I-9 Sección 2 vence el {data}",
  onb_c_titulo: "Incorporación", onb_c_desc: "Documentos, formas de pago, formularios estatales, plazos, recordatorios y retención de la incorporación de nuevos empleados. Las plantillas predeterminadas son un punto de partida: revísalas con tu abogado antes de usarlas.",
  onb_c_metodos: "Formas de pago aceptadas", onb_c_estaduais: "Formularios estatales (W-2)", onb_c_prazo: "Plazo predeterminado (días)",
  onb_c_lembrete: "Recordar al nuevo empleado cada (días, 0 = apagado)", onb_c_retencao: "Ofrecer borrar datos sensibles después de (días, 0 = conservar)",
  onb_c_experiencia: "Período de prueba predeterminado (días)", onb_c_provedor: "Nombre del sistema de nómina", onb_c_ordem: "Orden de los pasos",
  onb_c_empregador: "Datos del empleador (formularios oficiales)", onb_c_emp_nome: "Nombre legal de la empresa", onb_c_emp_end: "Dirección",
  onb_c_emp_cidade: "Ciudad, estado y ZIP", onb_c_emp_ein: "EIN", onb_c_emp_contato: "Persona de contacto", onb_c_emp_tel: "Teléfono",
  onb_c_salvar: "Guardar incorporación", onb_c_salvo: "Configuración guardada.", onb_c_modelos: "Plantillas de documentos", onb_c_novo: "Nuevo documento",
  onb_c_editar: "Editar", onb_c_excluir: "Eliminar", onb_c_confirmar_excluir: "¿Eliminar esta plantilla?", onb_c_inativo: "inactiva",
  onb_m_titulo: "Título ({l})", onb_m_texto: "Texto ({l})", onb_m_categoria: "Categoría", onb_m_cat: { oferta: "Carta de oferta", documento: "Documento para firmar" },
  onb_m_aplica: "Aplica a", onb_m_aplica_op: { w2: "W-2", 1099: "1099", ambos: "W-2 y 1099" }, onb_m_ordem: "Orden",
  onb_m_declaracao: "Pide declaración personal", onb_m_ativo: "Activa", onb_m_tipo: "Formato", onb_m_tipo_op: { texto: "Texto con variables", pdf: "PDF subido (firma al final)" },
  onb_m_pdf: "PDF (hasta 8 MB)", onb_m_vars: "Variables: {{nome}}, {{empresa}}, {{cargo}}, {{data_inicio}}, {{pagamento}}, {{horario}}, {{periodo_experiencia}}, {{prazo}}, {{representante}}, {{data}}. Usa \"# \" para título, \"## \" para sección, \"- \" para un elemento de lista.",
  onb_subir: "Subir", onb_descer: "Bajar",
});

// tabelas de tradução (objetos) no idioma do painel
function onbTab(chave) {
  return (I18N_GESTOR[idiomaGestor] || I18N_GESTOR.pt)[chave] || I18N_GESTOR.pt[chave] || {};
}
function onbRot(obj) {
  if (!obj) return "";
  if (typeof obj === "string") return obj;
  return obj[idiomaGestor] || obj.en || obj.pt || "";
}
const ONB_COR = { enviado: "info", em_andamento: "warn", concluido: "ok", cancelado: "err" };

async function onbBaixar(obId, docId, nome) {
  const resp = await fetch("/api/gestor/onboarding/" + obId + "/arquivo/" + docId, { headers: headersDownload() });
  if (!resp.ok) { const d = await resp.json().catch(() => ({})); alert(d.erro || tg("erro_comunicacao")); return; }
  const blob = await resp.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = nome || "documento";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

// assinatura desenhada (mesma ideia do portal)
function onbPad(canvas) {
  const ctx = canvas.getContext("2d");
  let tinta = false, desenhando = false, ultimo = null;
  const ajustar = () => {
    const r = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(r.width * dpr));
    canvas.height = Math.max(1, Math.round(r.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineWidth = 2.2; ctx.lineCap = "round"; ctx.strokeStyle = "#101B37";
  };
  const pt = (ev) => { const r = canvas.getBoundingClientRect(); return { x: ev.clientX - r.left, y: ev.clientY - r.top }; };
  canvas.addEventListener("pointerdown", (ev) => { ev.preventDefault(); desenhando = true; ultimo = pt(ev); });
  canvas.addEventListener("pointermove", (ev) => {
    if (!desenhando) return;
    const p = pt(ev);
    ctx.beginPath(); ctx.moveTo(ultimo.x, ultimo.y); ctx.lineTo(p.x, p.y); ctx.stroke();
    ultimo = p; tinta = true;
  });
  ["pointerup", "pointerleave", "pointercancel"].forEach((e) => canvas.addEventListener(e, () => { desenhando = false; }));
  setTimeout(ajustar, 0);
  return { limpar: () => { ctx.clearRect(0, 0, canvas.width, canvas.height); tinta = false; }, temTinta: () => tinta, png: () => canvas.toDataURL("image/png") };
}

// ------------------------------------------------------------ ficha do candidato
async function onboardingPreencherFicha(candidatoId, el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/onboarding/candidato/" + candidatoId); } catch (e) { el.remove(); return; }
  const ativo = r.onboardings.find((o) => o.status === "enviado" || o.status === "em_andamento");
  el.innerHTML = `
    ${tituloIcone("documento", tg("onb_titulo"))}
    ${!r.onboardings.length ? `<p class="desc">${tg("onb_nenhum")}</p>` : ""}
    ${!ativo && r.pode_enviar ? `<div class="linha-acoes no-print"><button class="btn small" id="onb-enviar" ${r.tem_email ? "" : `disabled title="${esc(tg("onb_sem_email"))}"`}>${icone("mais")} ${tg("onb_enviar")}</button></div>` : ""}
    ${!ativo && !r.pode_enviar && !r.onboardings.length ? `<p class="hint">${tg("onb_so_admin")}</p>` : ""}
    <div id="onb-lista">${r.onboardings.map((o, i) => onbHtmlOnboarding(o, r, i === 0)).join("")}</div>
    <div class="form-erro" id="onb-msg"></div>`;
  const msg = (t, ok) => { const m = el.querySelector("#onb-msg"); m.style.color = ok ? "var(--ok)" : "var(--err)"; m.textContent = t; };
  const recarregar = () => onboardingPreencherFicha(candidatoId, el);
  const enviar = el.querySelector("#onb-enviar");
  if (enviar) enviar.addEventListener("click", () => onbModalOferta(candidatoId, r.padroes, recarregar));
  el.querySelectorAll("[data-onb-acao]").forEach((b) => b.addEventListener("click", async () => {
    const id = b.dataset.onbId, acao = b.dataset.onbAcao;
    if (acao === "cancelar" && !confirm(tg("onb_confirmar_cancelar"))) return;
    if (acao === "purgar" && !confirm(tg("onb_purgar_aviso"))) return;
    if (acao === "copiar") {
      navigator.clipboard.writeText(b.dataset.link).then(() => { b.textContent = tg("onb_copiado"); }).catch(() => {});
      return;
    }
    b.disabled = true;
    try {
      await api("/api/gestor/onboarding/" + id + "/" + acao, { method: "POST", body: {} });
      if (acao === "reenviar") msg(tg("onb_reenviado"), true);
      else if (acao === "contratado") msg(tg("onb_movido"), true);
      else recarregar();
    } catch (e) { msg(e.message); }
    b.disabled = false;
  }));
  el.querySelectorAll("[data-onb-revelar]").forEach((a) => a.addEventListener("click", async (ev) => {
    ev.preventDefault();
    if (!confirm(tg("onb_revelar_aviso"))) return;
    try {
      const v = await api("/api/gestor/onboarding/" + a.dataset.onbId + "/revelar", { method: "POST", body: { campo: a.dataset.onbRevelar } });
      const alvo = el.querySelector(`[data-onb-valor="${a.dataset.onbId}-${a.dataset.onbRevelar}"]`);
      if (alvo) alvo.textContent = v.valor;
      a.remove();
    } catch (e) { msg(e.message); }
  }));
  el.querySelectorAll("[data-onb-baixar]").forEach((a) => a.addEventListener("click", (ev) => {
    ev.preventDefault();
    onbBaixar(a.dataset.onbId, a.dataset.onbBaixar, a.dataset.nome);
  }));
  el.querySelectorAll("[data-onb-i9]").forEach((b) => b.addEventListener("click", () => {
    onbModalI9(b.dataset.onbI9, r.campos_i9_secao2 || [], (r.padroes_i9 || {})[b.dataset.onbI9] || {}, recarregar);
  }));
}

function onbHtmlOnboarding(o, r, aberto) {
  const oferta = o.oferta || {};
  const etapas = onbTab("onb_etapas");
  const campos = onbTab("onb_campos");
  const ativo = o.status === "enviado" || o.status === "em_andamento";
  const docs = o.documentos || [];
  const nomeArq = (d) => d.tipo === "arquivo" ? (onbTab("onb_cats")[d.chave] || d.chave) + " · " + (d.nome || "") : d.titulo;
  const dados = o.dados || {};
  const pag = o.pagamento || {};
  const linhasDados = Object.keys(campos).filter((k) => dados[k]).map((k) => `<div><span class="hint">${esc(campos[k])}</span> ${esc(dados[k])}</div>`).join("");
  const linhasSens = Object.keys(o.mascaras || {}).map((k) => `<div><span class="hint">${esc(campos[k] || k)}</span>
    <span data-onb-valor="${o.id}-${esc(k)}">${esc(o.mascaras[k])}</span>
    ${r.admin ? ` <a href="#" class="no-print" data-onb-revelar="${esc(k)}" data-onb-id="${o.id}" style="font-size:.78rem">${tg("onb_revelar")}</a>` : ""}</div>`).join("");
  const metodo = pag.metodo ? onbTab("onb_metodos")[pag.metodo] : "";
  const pagLinhas = [metodo, pag.banco, pag.tipo_conta, pag.zelle, pag.endereco_cheque].filter(Boolean).map(esc).join(" · ");
  return `
    <details class="sub-card" ${aberto ? "open" : ""} style="margin:10px 0">
      <summary style="cursor:pointer;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <strong>${esc(oferta.cargo || "")}</strong>
        <span class="badge ${ONB_COR[o.status] || "tipo"}">${esc(onbTab("onb_status")[o.status] || o.status)}</span>
        <span class="badge tipo">${esc(onbTab("onb_tipo")[o.tipo] || o.tipo)}</span>
        ${o.atrasado ? `<span class="badge err">${tg("onb_atrasado")}</span>` : ""}
        <span class="hint">${esc(tg("onb_pct", { pct: o.pct }))}</span>
      </summary>
      <div style="height:8px;border-radius:99px;background:var(--surface-2);overflow:hidden;margin:10px 0 6px"><div style="height:100%;width:${o.pct}%;background:var(--accent)"></div></div>
      <p class="hint">${esc(tg("onb_inicio", { data: fmtData(oferta.data_inicio) }))} · ${esc(tg("onb_prazo", { data: fmtData(o.prazo) }))} ·
        US$ ${esc(Number(oferta.valor || 0).toFixed(2))} ${esc(onbTab("onb_unidades")[oferta.unidade] || "")}</p>
      ${o.erro_chave ? `<p class="form-erro">${tg("onb_erro_chave")}</p>` : ""}
      <ul class="lista-simples">${(o.etapas || []).map((e) => `<li>${e.feito ? "&#10003;" : "&#9675;"} ${esc(etapas[e.chave] || e.chave)}</li>`).join("")}</ul>
      ${ativo ? `
        <div class="linha-acoes no-print">
          <button class="btn secondary small" data-onb-acao="copiar" data-onb-id="${o.id}" data-link="${esc(o.link)}">${icone("link")} ${tg("onb_copiar")}</button>
          <button class="btn secondary small" data-onb-acao="reenviar" data-onb-id="${o.id}">${tg("onb_reenviar")}</button>
          <button class="btn secondary small" data-onb-acao="contratado" data-onb-id="${o.id}">${tg("onb_contratado")}</button>
          ${r.admin ? `<button class="btn danger small" data-onb-acao="cancelar" data-onb-id="${o.id}">${tg("onb_cancelar")}</button>` : ""}
        </div>` : ""}
      <h3 style="margin-top:14px">${tg("onb_docs")}</h3>
      ${docs.length ? `<ul class="lista-simples">${docs.map((d) => `<li>${esc(nomeArq(d))} <span class="hint">${esc(fmtData(d.criado_em))}</span>
        <a href="#" class="no-print" data-onb-baixar="${d.id}" data-onb-id="${o.id}" data-nome="${esc(d.tipo === "arquivo" ? (d.nome || "arquivo") : (d.titulo || "documento") + ".pdf")}">${tg("onb_baixar")}</a></li>`).join("")}</ul>`
        : `<p class="desc">${tg("onb_nada")}</p>`}
      ${linhasDados ? `<h3>${tg("onb_dados")}</h3><div style="display:grid;gap:4px;font-size:.88rem">${linhasDados}</div>` : ""}
      ${linhasSens ? `<h3>${tg("onb_sensiveis")}</h3><div style="display:grid;gap:4px;font-size:.88rem">${linhasSens}</div>` : ""}
      ${pagLinhas ? `<h3>${tg("onb_pagamento")}</h3><p style="font-size:.88rem">${pagLinhas}</p>` : ""}
      ${o.i9 && o.i9.necessario && o.status !== "cancelado" ? `
        <h3>${tg("onb_i9")}</h3>
        <p class="hint" ${o.i9.atrasado ? 'style="color:var(--err)"' : ""}>${esc(tg("onb_i9_prazo", { data: fmtData(o.i9.prazo) }))}</p>
        ${o.i9.feito ? `<p><span class="badge ok">${tg("onb_i9_feito")}</span></p>` : ""}
        ${!o.i9.secao1 ? `<p class="desc">${tg("onb_i9_falta_s1")}</p>` : `<button class="btn secondary small no-print" data-onb-i9="${o.id}">${tg("onb_i9_abrir")}</button>`}` : ""}
      ${o.purgado_em ? `<p class="hint">${esc(tg("onb_purgado", { data: fmtData(o.purgado_em) }))}</p>` : ""}
      ${o.pode_purgar && r.admin ? `<div class="linha-acoes no-print"><button class="btn danger small" data-onb-acao="purgar" data-onb-id="${o.id}">${tg("onb_purgar")}</button></div>` : ""}
    </details>`;
}

// ------------------------------------------------------------ enviar proposta
function onbModalOferta(candidatoId, p, aoEnviar) {
  if (!p) return;
  const unidades = onbTab("onb_unidades");
  const metodos = onbTab("onb_metodos");
  const nomesForms = onbTab("onb_forms");
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal" style="max-width:640px">
      <button class="btn ghost small fechar" id="onb-fechar">${icone("fechar")}</button>
      <h2>${tg("onb_f_titulo")}</h2>
      <div class="field">${tg("onb_f_tipo")}
        <div style="display:flex;gap:16px;margin-top:6px">
          <label><input type="radio" name="onb-tipo" value="w2" checked> ${esc(onbTab("onb_tipo").w2)}</label>
          <label><input type="radio" name="onb-tipo" value="1099"> ${esc(onbTab("onb_tipo")[1099])}</label>
        </div></div>
      <label class="field">${tg("onb_f_cargo")}<input type="text" id="onb-cargo" maxlength="120" value="${esc(p.cargo || "")}" list="onb-cargos">
        <datalist id="onb-cargos">${(typeof cargos !== "undefined" ? cargos : []).map((c) => `<option value="${esc(c.nome)}"></option>`).join("")}</datalist></label>
      <div class="grid cols-2">
        <label class="field">${tg("onb_f_inicio")}<input type="date" id="onb-inicio"></label>
        <label class="field">${tg("onb_f_prazo")}<input type="date" id="onb-prazo" value="${esc(p.prazo)}"></label>
        <label class="field">${tg("onb_f_valor")}<input type="text" inputmode="decimal" id="onb-valor" placeholder="22.00"></label>
        <label class="field">${tg("onb_f_unidade")}<select id="onb-unidade">${Object.keys(unidades).map((u) => `<option value="${u}">${esc(unidades[u])}</option>`).join("")}</select></label>
      </div>
      <label class="field">${tg("onb_f_horario")}<input type="text" id="onb-horario" maxlength="300"></label>
      <label class="field">${tg("onb_f_notas")}<textarea id="onb-notas" rows="2" maxlength="2000"></textarea></label>
      <div class="grid cols-2">
        <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="onb-dirige"> ${tg("onb_f_dirige")}</label>
        <label class="field">${tg("onb_f_experiencia")}<input type="number" min="0" max="365" id="onb-experiencia" value="${esc(String(p.periodo_experiencia))}"></label>
      </div>
      <div class="field">${tg("onb_f_docs")}<div id="onb-docs" style="display:grid;gap:4px;margin-top:6px"></div></div>
      <div class="field">${tg("onb_f_forms")}<div id="onb-forms" style="display:flex;flex-wrap:wrap;gap:12px;margin-top:6px"></div>
        ${p.formularios_disponivel ? "" : `<span class="hint">${tg("onb_f_forms_indisp")}</span>`}</div>
      <div class="field">${tg("onb_f_metodos")}<div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:6px">
        ${Object.keys(metodos).map((m) => `<label><input type="checkbox" data-onb-metodo="${m}" ${(p.metodos || []).includes(m) ? "checked" : ""}> ${esc(metodos[m])}</label>`).join("")}</div></div>
      <div class="form-erro" id="onb-erro"></div>
      <button class="btn block" id="onb-salvar">${tg("onb_f_enviar")}</button>
    </div>`;
  document.body.appendChild(fundo);
  const fechar = () => fundo.remove();
  fundo.querySelector("#onb-fechar").addEventListener("click", fechar);
  fundo.addEventListener("click", (ev) => { if (ev.target === fundo) fechar(); });
  const tipoAtual = () => fundo.querySelector("input[name=onb-tipo]:checked").value;
  const desenharListas = () => {
    const tipo = tipoAtual();
    const docs = (p.modelos || []).filter((m) => m.categoria === "documento" && (m.aplica === "ambos" || m.aplica === tipo));
    fundo.querySelector("#onb-docs").innerHTML = docs.map((m) => `<label><input type="checkbox" data-onb-doc="${m.id}" checked> ${esc(onbRot(m.titulos))}</label>`).join("");
    const forms = (p.formularios || {})[tipo] || [];
    const todos = tipo === "w2" ? ["w4", "i9", "ctw4"] : ["w9"];
    fundo.querySelector("#onb-forms").innerHTML = todos.map((f) => `<label><input type="checkbox" data-onb-form="${f}" ${forms.includes(f) ? "checked" : ""}> ${esc(nomesForms[f] || f)}</label>`).join("");
  };
  fundo.querySelectorAll("input[name=onb-tipo]").forEach((r) => r.addEventListener("change", desenharListas));
  desenharListas();
  fundo.querySelector("#onb-salvar").addEventListener("click", async (ev) => {
    const v = (id) => fundo.querySelector(id).value.trim();
    const corpo = {
      candidato_id: candidatoId, candidatura_id: p.candidatura_id, tipo: tipoAtual(), cargo: v("#onb-cargo"), cargo_id: p.cargo_id,
      data_inicio: v("#onb-inicio"), prazo: v("#onb-prazo"), valor: v("#onb-valor"), unidade: v("#onb-unidade"),
      horario: v("#onb-horario"), notas: v("#onb-notas"), dirige: fundo.querySelector("#onb-dirige").checked,
      periodo_experiencia: v("#onb-experiencia"),
      documentos: [...fundo.querySelectorAll("[data-onb-doc]")].filter((x) => x.checked).map((x) => Number(x.dataset.onbDoc)),
      formularios: [...fundo.querySelectorAll("[data-onb-form]")].filter((x) => x.checked).map((x) => x.dataset.onbForm),
      metodos: [...fundo.querySelectorAll("[data-onb-metodo]")].filter((x) => x.checked).map((x) => x.dataset.onbMetodo),
    };
    ev.target.disabled = true;
    try {
      const r = await api("/api/gestor/onboarding/oferta", { method: "POST", body: corpo });
      fechar();
      if (!r.email_enviado) alert(tg("onb_f_enviado_sem_email", { msg: r.aviso_email || "" }));
      aoEnviar();
    } catch (e) {
      fundo.querySelector("#onb-erro").textContent = e.message;
      ev.target.disabled = false;
    }
  });
}

// ------------------------------------------------------------ I-9 Seção 2
function onbCampoHtml(c, valor) {
  const tipo = String(c.tipo || "text").toLowerCase();
  const rot = onbRot(c.rotulo) + (c.obrigatorio ? " *" : "");
  const ajuda = onbRot(c.ajuda);
  const fim = `${ajuda ? `<span class="hint" style="display:block">${esc(ajuda)}</span>` : ""}<span class="hint onb-erro-campo" style="display:none;color:var(--err)"></span>`;
  if (tipo === "checkbox") return `<label data-onb-campo="${esc(c.chave)}" style="display:flex;gap:8px;align-items:center;margin:8px 0"><input type="checkbox" id="onbf-${esc(c.chave)}" ${valor ? "checked" : ""}> ${esc(rot)}${fim}</label>`;
  if ((c.opcoes || []).length || tipo === "select") {
    return `<label class="field" data-onb-campo="${esc(c.chave)}">${esc(rot)}<select id="onbf-${esc(c.chave)}"><option value=""></option>
      ${(c.opcoes || []).map((o) => { const val = typeof o === "object" ? o.valor : o; return `<option value="${esc(val)}" ${String(valor) === String(val) ? "selected" : ""}>${esc(typeof o === "object" ? onbRot(o.rotulo) : o)}</option>`; }).join("")}</select>${fim}</label>`;
  }
  return `<label class="field" data-onb-campo="${esc(c.chave)}">${esc(rot)}<input type="${tipo === "date" ? "date" : "text"}" id="onbf-${esc(c.chave)}" value="${esc(valor || "")}">${fim}</label>`;
}

function onbVisivel(campos, c, valorDe) {
  if (!c.condicao) return true;
  const atual = valorDe(c.condicao.campo);
  const vals = c.condicao.valores || [];
  if (vals.includes(true)) return atual === true;
  return vals.map(String).includes(String(atual));
}

function onbModalI9(obId, campos, padroes, aoSalvar) {
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal" style="max-width:620px">
      <button class="btn ghost small fechar" id="onb-fechar">${icone("fechar")}</button>
      <h2>${tg("onb_i9")}</h2>
      <p class="desc">${tg("onb_i9_dica")}</p>
      <div id="onb-i9-form">${campos.map((c) => onbCampoHtml(c, padroes[c.chave])).join("")}</div>
      <div class="field">${tg("onb_assinatura")}
        <div style="border:1px dashed var(--blue-250);border-radius:12px;background:#fff;margin-top:6px"><canvas id="onb-i9-canvas" style="display:block;width:100%;height:140px;touch-action:none"></canvas></div>
        <button class="btn ghost small" id="onb-i9-limpar" type="button">${tg("onb_limpar")}</button></div>
      <div class="form-erro" id="onb-erro"></div>
      <button class="btn block" id="onb-salvar">${tg("onb_i9_salvar")}</button>
    </div>`;
  document.body.appendChild(fundo);
  const fechar = () => fundo.remove();
  fundo.querySelector("#onb-fechar").addEventListener("click", fechar);
  const valorDe = (k) => { const el = fundo.querySelector("#onbf-" + CSS.escape(k)); return el ? (el.type === "checkbox" ? el.checked : el.value.trim()) : undefined; };
  const atualizar = () => campos.forEach((c) => {
    const el = fundo.querySelector(`[data-onb-campo="${CSS.escape(c.chave)}"]`);
    if (el) el.style.display = onbVisivel(campos, c, valorDe) ? "" : "none";
  });
  fundo.querySelector("#onb-i9-form").addEventListener("change", atualizar);
  atualizar();
  const pad = onbPad(fundo.querySelector("#onb-i9-canvas"));
  fundo.querySelector("#onb-i9-limpar").addEventListener("click", () => pad.limpar());
  fundo.querySelector("#onb-salvar").addEventListener("click", async (ev) => {
    const dados = {};
    campos.forEach((c) => {
      if (!onbVisivel(campos, c, valorDe)) return;
      const v = valorDe(c.chave);
      if (v !== undefined && v !== "") dados[c.chave] = v;
    });
    fundo.querySelectorAll(".onb-erro-campo").forEach((x) => { x.style.display = "none"; });
    ev.target.disabled = true;
    try {
      await api("/api/gestor/onboarding/" + obId + "/i9-secao2", { method: "POST", body: { dados, assinatura: pad.temTinta() ? pad.png() : "" } });
      fechar();
      aoSalvar();
    } catch (e) {
      fundo.querySelector("#onb-erro").textContent = e.message;
      ev.target.disabled = false;
    }
  });
}

// ------------------------------------------------------------ visão geral
async function onboardingVisao(el) {
  if (!el) return;
  let r;
  try { r = await api("/api/gestor/onboarding/lista"); } catch (e) { el.remove(); return; }
  if (!r.onboardings.length) { el.remove(); return; }
  const etapas = onbTab("onb_etapas");
  el.innerHTML = `
    <h2 class="icone-titulo" style="margin-top:0">${icone("documento")}<span>${tg("onb_v_titulo")}</span></h2>
    ${r.onboardings.map((o) => `
      <div style="padding:8px 0;border-top:1px solid var(--line, rgba(127,127,127,.15))">
        <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
          <a href="#" data-onb-cand="${o.candidato_id}"><strong>${esc(o.nome)}</strong></a>
          <span class="hint">${esc(o.cargo)}</span>
          <span class="badge ${ONB_COR[o.status] || "tipo"}">${esc(onbTab("onb_status")[o.status] || o.status)}</span>
          ${o.atrasado ? `<span class="badge err">${tg("onb_atrasado")}</span>` : ""}
          <span style="margin-left:auto" class="hint">${esc(tg("onb_pct", { pct: o.pct }))}</span>
        </div>
        <div style="height:6px;border-radius:99px;background:var(--surface-2);overflow:hidden;margin:6px 0"><div style="height:100%;width:${o.pct}%;background:var(--accent)"></div></div>
        ${o.pendentes.length && o.status !== "concluido" ? `<div class="hint">${esc(tg("onb_v_pendentes", { itens: o.pendentes.map((p) => etapas[p] || p).join(", ") }))}</div>` : ""}
        ${o.i9_prazo && !o.i9_feito ? `<div class="hint" ${o.i9_atrasado ? 'style="color:var(--err)"' : ""}>${esc(tg("onb_v_i9", { data: fmtData(o.i9_prazo) }))}</div>` : ""}
      </div>`).join("")}`;
  el.querySelectorAll("[data-onb-cand]").forEach((a) => a.addEventListener("click", (ev) => {
    ev.preventDefault();
    abrirDetalheCandidato(Number(a.dataset.onbCand));
  }));
}

// ------------------------------------------------------------ configurações (admin)
async function secaoOnboarding(el) {
  if (!el || !infoGestor().admin) return;
  let r;
  try { r = await api("/api/gestor/onboarding/config"); } catch (e) { el.innerHTML = ""; return; }
  const c = r.config;
  const metodos = onbTab("onb_metodos");
  const etapas = onbTab("onb_etapas");
  let ordem = [...c.ordem];
  const campo = (id, rot, valor, attrs) => `<label class="field">${esc(rot)}<input type="text" id="${id}" value="${esc(valor == null ? "" : String(valor))}" ${attrs || ""}></label>`;
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("documento")}<span>${tg("onb_c_titulo")}</span></h2>
      <p class="desc">${tg("onb_c_desc")}</p>
      <div class="grid cols-2">
        <div class="field">${tg("onb_c_metodos")}<div style="display:grid;gap:4px;margin-top:6px">
          ${r.metodos.map((m) => `<label><input type="checkbox" data-onbc-metodo="${m}" ${c.metodos.includes(m) ? "checked" : ""}> ${esc(metodos[m] || m)}</label>`).join("")}</div></div>
        <div class="field">${tg("onb_c_estaduais")}<div style="display:grid;gap:4px;margin-top:6px">
          ${r.estaduais.map((f) => `<label><input type="checkbox" data-onbc-estadual="${f}" ${c.estaduais.includes(f) ? "checked" : ""}> ${esc(onbTab("onb_forms")[f] || f)}</label>`).join("")}</div></div>
        ${campo("onbc-prazo", tg("onb_c_prazo"), c.prazo_dias, 'inputmode="numeric"')}
        ${campo("onbc-lembrete", tg("onb_c_lembrete"), c.lembrete_dias, 'inputmode="numeric"')}
        ${campo("onbc-retencao", tg("onb_c_retencao"), c.retencao_dias, 'inputmode="numeric"')}
        ${campo("onbc-experiencia", tg("onb_c_experiencia"), c.periodo_experiencia, 'inputmode="numeric"')}
        ${campo("onbc-provedor", tg("onb_c_provedor"), c.provedor_nome, 'maxlength="60"')}
      </div>
      <div class="field">${tg("onb_c_ordem")}<ol id="onbc-ordem" style="margin:6px 0 0 18px;padding:0"></ol></div>
      <h3>${tg("onb_c_empregador")}</h3>
      <div class="grid cols-2">
        ${campo("onbc-emp-nome", tg("onb_c_emp_nome"), c.empregador_nome, 'maxlength="160"')}
        ${campo("onbc-emp-ein", tg("onb_c_emp_ein"), c.empregador_ein, 'maxlength="10" placeholder="12-3456789"')}
        ${campo("onbc-emp-end", tg("onb_c_emp_end"), c.empregador_endereco, 'maxlength="160"')}
        ${campo("onbc-emp-cidade", tg("onb_c_emp_cidade"), c.empregador_cidade_estado_cep, 'maxlength="160" placeholder="Hartford, CT 06103"')}
        ${campo("onbc-emp-contato", tg("onb_c_emp_contato"), c.empregador_contato, 'maxlength="160"')}
        ${campo("onbc-emp-tel", tg("onb_c_emp_tel"), c.empregador_telefone, 'maxlength="40"')}
      </div>
      <div class="form-erro" id="onbc-msg"></div>
      <div class="linha-acoes"><button class="btn" id="onbc-salvar">${tg("onb_c_salvar")}</button></div>
      <h3 style="margin-top:18px">${tg("onb_c_modelos")}</h3>
      <div id="onbc-modelos"></div>
      <div class="linha-acoes"><button class="btn secondary small" id="onbc-novo">${icone("mais")} ${tg("onb_c_novo")}</button></div>
    </div>`;
  const desenharOrdem = () => {
    el.querySelector("#onbc-ordem").innerHTML = ordem.map((e, i) => `<li style="margin:3px 0">${esc(etapas[e] || e)}
      ${i > 0 ? `<a href="#" data-onbc-mover="${i}" data-dir="-1" title="${esc(tg("onb_subir"))}">&uarr;</a>` : ""}
      ${i < ordem.length - 1 ? `<a href="#" data-onbc-mover="${i}" data-dir="1" title="${esc(tg("onb_descer"))}">&darr;</a>` : ""}</li>`).join("");
    el.querySelectorAll("[data-onbc-mover]").forEach((a) => a.addEventListener("click", (ev) => {
      ev.preventDefault();
      const i = Number(a.dataset.onbcMover), j = i + Number(a.dataset.dir);
      [ordem[i], ordem[j]] = [ordem[j], ordem[i]];
      desenharOrdem();
    }));
  };
  desenharOrdem();
  const desenharModelos = (lista) => {
    el.querySelector("#onbc-modelos").innerHTML = `<ul class="lista-simples">${lista.map((m) => `
      <li><strong>${esc(onbRot(m.titulos))}</strong> <span class="badge tipo">${esc(onbTab("onb_m_cat")[m.categoria] || m.categoria)}</span>
        <span class="badge neutral">${esc(onbTab("onb_m_aplica_op")[m.aplica] || m.aplica)}</span>
        ${m.ativo ? "" : `<span class="hint">(${tg("onb_c_inativo")})</span>`}
        <a href="#" data-onbc-editar="${m.id}">${tg("onb_c_editar")}</a> · <a href="#" data-onbc-excluir="${m.id}">${tg("onb_c_excluir")}</a></li>`).join("")}</ul>`;
    el.querySelectorAll("[data-onbc-editar]").forEach((a) => a.addEventListener("click", (ev) => {
      ev.preventDefault();
      onbModalModelo(lista.find((m) => m.id === Number(a.dataset.onbcEditar)), () => secaoOnboarding(el));
    }));
    el.querySelectorAll("[data-onbc-excluir]").forEach((a) => a.addEventListener("click", async (ev) => {
      ev.preventDefault();
      if (!confirm(tg("onb_c_confirmar_excluir"))) return;
      try { await api("/api/gestor/onboarding/modelo/" + a.dataset.onbcExcluir, { method: "DELETE" }); secaoOnboarding(el); } catch (e) { alert(e.message); }
    }));
  };
  desenharModelos(r.modelos);
  el.querySelector("#onbc-novo").addEventListener("click", () => onbModalModelo(null, () => secaoOnboarding(el)));
  el.querySelector("#onbc-salvar").addEventListener("click", async () => {
    const v = (id) => el.querySelector(id).value.trim();
    const corpo = {
      metodos: [...el.querySelectorAll("[data-onbc-metodo]")].filter((x) => x.checked).map((x) => x.dataset.onbcMetodo),
      estaduais: [...el.querySelectorAll("[data-onbc-estadual]")].filter((x) => x.checked).map((x) => x.dataset.onbcEstadual),
      prazo_dias: v("#onbc-prazo"), lembrete_dias: v("#onbc-lembrete"), retencao_dias: v("#onbc-retencao"),
      periodo_experiencia: v("#onbc-experiencia"), provedor_nome: v("#onbc-provedor"), ordem,
      empregador_nome: v("#onbc-emp-nome"), empregador_ein: v("#onbc-emp-ein"), empregador_endereco: v("#onbc-emp-end"),
      empregador_cidade_estado_cep: v("#onbc-emp-cidade"), empregador_contato: v("#onbc-emp-contato"), empregador_telefone: v("#onbc-emp-tel"),
    };
    const m = el.querySelector("#onbc-msg");
    try {
      await api("/api/gestor/onboarding/config", { method: "POST", body: corpo });
      m.style.color = "var(--ok)"; m.textContent = tg("onb_c_salvo");
    } catch (e) { m.style.color = "var(--err)"; m.textContent = e.message; }
  });
}

function onbModalModelo(m, aoSalvar) {
  const t = m || { titulos: {}, textos: {}, categoria: "documento", aplica: "ambos", ordem: 100, requer_declaracao: false, ativo: true, tipo: "texto" };
  const cats = onbTab("onb_m_cat"), aplica = onbTab("onb_m_aplica_op"), tipos = onbTab("onb_m_tipo_op");
  const sel = (id, ops, atual) => `<select id="${id}">${Object.keys(ops).map((k) => `<option value="${k}" ${String(atual) === k ? "selected" : ""}>${esc(ops[k])}</option>`).join("")}</select>`;
  const fundo = document.createElement("div");
  fundo.className = "modal-fundo";
  fundo.innerHTML = `
    <div class="modal" style="max-width:760px">
      <button class="btn ghost small fechar" id="onb-fechar">${icone("fechar")}</button>
      <h2>${esc(onbRot(t.titulos) || tg("onb_c_novo"))}</h2>
      <div class="grid cols-2">
        ${["en", "pt", "es"].map((l) => `<label class="field">${esc(tg("onb_m_titulo", { l: l.toUpperCase() }))}<input type="text" id="onbm-titulo-${l}" maxlength="150" value="${esc((t.titulos || {})[l] || "")}"></label>`).join("")}
        <label class="field">${tg("onb_m_categoria")}${sel("onbm-categoria", cats, t.categoria)}</label>
        <label class="field">${tg("onb_m_aplica")}${sel("onbm-aplica", aplica, t.aplica)}</label>
        <label class="field">${tg("onb_m_tipo")}${sel("onbm-tipo", tipos, t.tipo)}</label>
        <label class="field">${tg("onb_m_ordem")}<input type="number" id="onbm-ordem" value="${esc(String(t.ordem || 0))}"></label>
      </div>
      <label style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="onbm-declaracao" ${t.requer_declaracao ? "checked" : ""}> ${tg("onb_m_declaracao")}</label>
      <label style="display:flex;gap:8px;align-items:center;margin:6px 0 10px"><input type="checkbox" id="onbm-ativo" ${t.ativo ? "checked" : ""}> ${tg("onb_m_ativo")}</label>
      <label class="field">${tg("onb_m_pdf")}<input type="file" id="onbm-pdf" accept="application/pdf"></label>
      <p class="hint">${esc(tg("onb_m_vars"))}</p>
      ${["en", "pt", "es"].map((l) => `<label class="field">${esc(tg("onb_m_texto", { l: l.toUpperCase() }))}<textarea id="onbm-texto-${l}" rows="${l === "en" ? 12 : 6}" style="font-family:monospace;font-size:.82rem">${esc((t.textos || {})[l] || "")}</textarea></label>`).join("")}
      <div class="form-erro" id="onb-erro"></div>
      <button class="btn block" id="onb-salvar">${tg("salvar")}</button>
    </div>`;
  document.body.appendChild(fundo);
  const fechar = () => fundo.remove();
  fundo.querySelector("#onb-fechar").addEventListener("click", fechar);
  fundo.querySelector("#onb-salvar").addEventListener("click", async (ev) => {
    const v = (id) => fundo.querySelector(id).value;
    const corpo = {
      id: m ? m.id : undefined, categoria: v("#onbm-categoria"), aplica: v("#onbm-aplica"), tipo: v("#onbm-tipo"), ordem: v("#onbm-ordem"),
      requer_declaracao: fundo.querySelector("#onbm-declaracao").checked, ativo: fundo.querySelector("#onbm-ativo").checked,
      titulos: { en: v("#onbm-titulo-en"), pt: v("#onbm-titulo-pt"), es: v("#onbm-titulo-es") },
      textos: { en: v("#onbm-texto-en"), pt: v("#onbm-texto-pt"), es: v("#onbm-texto-es") },
    };
    const arq = fundo.querySelector("#onbm-pdf").files[0];
    ev.target.disabled = true;
    try {
      if (arq) {
        corpo.pdf = await new Promise((ok, falha) => {
          const leitor = new FileReader();
          leitor.onload = () => ok(String(leitor.result));
          leitor.onerror = falha;
          leitor.readAsDataURL(arq);
        });
      }
      await api("/api/gestor/onboarding/modelo", { method: "POST", body: corpo });
      fechar();
      aoSalvar();
    } catch (e) {
      fundo.querySelector("#onb-erro").textContent = e.message;
      ev.target.disabled = false;
    }
  });
}
