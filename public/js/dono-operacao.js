/* =====================================================================
   Painel do Dono, aba Sistema (operacao.py): saúde do servidor, backup
   externo cifrado (S3 compatível) e erros recentes com traceback.
   Carregado depois de dono.js; usa api(), td(), esc(), icone() de lá.
   ===================================================================== */

Object.assign(I18N_DONO.pt, {
  aba_sistema: "Sistema",
  op_saude: "Saúde do servidor",
  op_ok: "Tudo certo",
  op_problema: "Com problema",
  op_versao: "Versão",
  op_uptime: "No ar há",
  op_db: "Banco de dados",
  op_fila: "Fila de voz (para ligar)",
  op_ult_local: "Último backup local",
  op_ult_remoto: "Último backup externo",
  op_disco: "Disco",
  op_disco_val: "{pct}% usado, {livre} GB livres",
  op_nunca: "nunca",
  op_condicoes: "Alertas ativos",
  op_sem_condicoes: "Nenhum alerta ativo.",
  op_cond_disco: "Disco acima de 85%",
  op_cond_backup_local: "Backup local com mais de 26 horas",
  op_cond_voz_presa: "Ligação de voz presa há mais de 60 minutos",
  op_cond_voz_falhas: "5 ou mais falhas da ElevenLabs/Twilio na última hora",
  op_cond_backup_remoto: "Backup externo atrasado",
  op_alertas_dica: "Os alertas vão para o e-mail do dono (Planos, configuração do dono) no idioma escolhido lá. Verificação a cada 15 minutos; um e-mail por alerta a cada 6 horas.",
  op_bk_titulo: "Backup externo cifrado",
  op_bk_desc: "Todo dia, depois do backup local, o servidor cifra e envia para um bucket S3 compatível (Oracle Object Storage, Backblaze B2, AWS S3, Cloudflare R2): o banco, a pasta uploads/ e a chave_dados.key. Guarda 30 dias e 12 meses.",
  op_bk_sem_cripto: "O servidor não tem python3-cryptography: o backup externo fica desligado.",
  op_endpoint: "Endpoint",
  op_regiao: "Região",
  op_bucket: "Bucket",
  op_prefixo: "Prefixo (pasta)",
  op_chave_acesso: "Chave de acesso (Access Key)",
  op_segredo: "Segredo (Secret Key)",
  op_segredo_ok: "guardado; deixe em branco para manter",
  op_chave_final: "atual termina em {f}",
  op_salvar: "Salvar armazenamento",
  op_testar: "Testar conexão",
  op_agora: "Fazer backup agora",
  op_teste_ok: "Conexão OK: gravar, listar, ler e apagar funcionaram.",
  op_salvo: "Salvo.",
  op_iniciado: "Backup iniciado. Atualizando o status...",
  op_rodando: "Backup em andamento...",
  op_frase_titulo: "Frase de backup",
  op_frase_desc: "Os arquivos são cifrados com esta frase. Sem ela não há como restaurar: guarde num cofre de senhas. Mínimo 12 caracteres.",
  op_frase_ok: "Frase definida.",
  op_frase_falta: "Frase ainda não definida.",
  op_frase_atual: "Frase atual",
  op_frase_nova: "Nova frase",
  op_frase_confirma: "Confirmar a frase",
  op_frase_salvar: "Salvar frase",
  op_frase_dica_troca: "Backups antigos continuam com a frase antiga.",
  op_frases_diferentes: "As frases não conferem.",
  op_chave_maquina: "A frase e o segredo ficam cifrados no servidor com a chave da máquina backups.key (pasta do app). Copie essa chave junto com a chave_dados.key para um cofre.",
  op_chave_maquina_falta: "backups.key ainda não existe (é criada ao salvar o segredo ou a frase).",
  op_status: "Status",
  op_ultimo_ok: "Último sucesso",
  op_tamanho: "Tamanho enviado",
  op_ultimo_erro: "Último erro",
  op_ultima_tentativa: "Última tentativa",
  op_remotos: "Backups no bucket",
  op_carregar_lista: "Listar backups",
  op_sem_remotos: "Nenhum backup no bucket ainda.",
  op_baixar: "Baixar",
  op_baixando: "Baixando e decifrando...",
  op_restaurar_titulo: "Como restaurar",
  op_restaurar: "1. Baixe aqui os arquivos do dia (já decifrados): rh.db, uploads.tar e chave_dados.key. Fora do painel: baixe os .enc no console do provedor e rode python3 operacao.py decifrar ARQUIVO.enc SAIDA (pede a frase).\n2. No servidor: sudo systemctl stop bussola\n3. Guarde o rh.db atual (cp rh.db rh-antes-restauro.db) e copie o rh.db baixado para /home/ubuntu/bussola/rh.db\n4. Arquivos: tar -xf uploads.tar -C /home/ubuntu/bussola\n5. Se a chave_dados.key sumiu, copie a baixada para /home/ubuntu/bussola/chave_dados.key e rode chmod 600 nela.\n6. sudo systemctl start bussola e confira /api/saude.",
  op_como_bucket: "Como criar o bucket",
  op_como_bucket_txt: "Oracle Cloud (grátis até 20 GB): Storage > Buckets > Create Bucket (Standard, sem acesso público). Em Profile > Customer Secret Keys > Generate, copie a Access Key e o Secret. Endpoint: https://NAMESPACE.compat.objectstorage.REGIAO.oraclecloud.com (o namespace aparece em Tenancy details), região como us-ashburn-1. Backblaze B2: endpoint https://s3.REGIAO.backblazeb2.com. Cloudflare R2: https://CONTA.r2.cloudflarestorage.com com região auto. AWS: https://s3.REGIAO.amazonaws.com.",
  op_erros: "Erros recentes do servidor",
  op_erros_todos: "Mostrar resolvidos",
  op_sem_erros: "Nenhum erro em aberto.",
  op_resolver: "Marcar resolvido",
  op_reabrir: "Reabrir",
  op_resolvido: "resolvido",
  op_traceback: "Traceback",
  op_quando: "Quando",
  op_rota: "Rota",
  op_tipo: "Tipo",
  op_mensagem: "Mensagem",
  op_dias: "{n} d",
  op_horas: "{n} h",
  op_minutos: "{n} min",
});

Object.assign(I18N_DONO.en, {
  aba_sistema: "System",
  op_saude: "Server health",
  op_ok: "All good",
  op_problema: "Problem",
  op_versao: "Version",
  op_uptime: "Up for",
  op_db: "Database",
  op_fila: "Voice queue (to call)",
  op_ult_local: "Latest local backup",
  op_ult_remoto: "Latest offsite backup",
  op_disco: "Disk",
  op_disco_val: "{pct}% used, {livre} GB free",
  op_nunca: "never",
  op_condicoes: "Active alerts",
  op_sem_condicoes: "No active alerts.",
  op_cond_disco: "Disk above 85%",
  op_cond_backup_local: "Local backup older than 26 hours",
  op_cond_voz_presa: "Voice call stuck for more than 60 minutes",
  op_cond_voz_falhas: "5 or more ElevenLabs/Twilio failures in the last hour",
  op_cond_backup_remoto: "Offsite backup is late",
  op_alertas_dica: "Alerts go to the owner email (Plans, owner settings) in the language chosen there. Checked every 15 minutes; one email per alert every 6 hours.",
  op_bk_titulo: "Encrypted offsite backup",
  op_bk_desc: "Every day, after the local backup, the server encrypts and uploads to an S3 compatible bucket (Oracle Object Storage, Backblaze B2, AWS S3, Cloudflare R2): the database, the uploads/ folder and chave_dados.key. Keeps 30 days and 12 months.",
  op_bk_sem_cripto: "The server does not have python3-cryptography: offsite backups are off.",
  op_endpoint: "Endpoint",
  op_regiao: "Region",
  op_bucket: "Bucket",
  op_prefixo: "Prefix (folder)",
  op_chave_acesso: "Access Key",
  op_segredo: "Secret Key",
  op_segredo_ok: "saved; leave blank to keep it",
  op_chave_final: "current one ends in {f}",
  op_salvar: "Save storage",
  op_testar: "Test connection",
  op_agora: "Run backup now",
  op_teste_ok: "Connection OK: write, list, read and delete worked.",
  op_salvo: "Saved.",
  op_iniciado: "Backup started. Refreshing the status...",
  op_rodando: "Backup running...",
  op_frase_titulo: "Backup passphrase",
  op_frase_desc: "Files are encrypted with this passphrase. Without it there is no way to restore: keep it in a password manager. At least 12 characters.",
  op_frase_ok: "Passphrase set.",
  op_frase_falta: "Passphrase not set yet.",
  op_frase_atual: "Current passphrase",
  op_frase_nova: "New passphrase",
  op_frase_confirma: "Confirm the passphrase",
  op_frase_salvar: "Save passphrase",
  op_frase_dica_troca: "Older backups keep the old passphrase.",
  op_frases_diferentes: "The passphrases do not match.",
  op_chave_maquina: "The passphrase and the secret are stored encrypted on the server with the machine key backups.key (app folder). Copy that key together with chave_dados.key to a vault.",
  op_chave_maquina_falta: "backups.key does not exist yet (it is created when you save the secret or the passphrase).",
  op_status: "Status",
  op_ultimo_ok: "Last success",
  op_tamanho: "Uploaded size",
  op_ultimo_erro: "Last error",
  op_ultima_tentativa: "Last attempt",
  op_remotos: "Backups in the bucket",
  op_carregar_lista: "List backups",
  op_sem_remotos: "No backups in the bucket yet.",
  op_baixar: "Download",
  op_baixando: "Downloading and decrypting...",
  op_restaurar_titulo: "How to restore",
  op_restaurar: "1. Download the files of the day here (already decrypted): rh.db, uploads.tar and chave_dados.key. Outside the panel: download the .enc files from the provider console and run python3 operacao.py decifrar FILE.enc OUTPUT (asks for the passphrase).\n2. On the server: sudo systemctl stop bussola\n3. Keep the current rh.db (cp rh.db rh-antes-restauro.db) and copy the downloaded rh.db to /home/ubuntu/bussola/rh.db\n4. Files: tar -xf uploads.tar -C /home/ubuntu/bussola\n5. If chave_dados.key is gone, copy the downloaded one to /home/ubuntu/bussola/chave_dados.key and run chmod 600 on it.\n6. sudo systemctl start bussola and check /api/saude.",
  op_como_bucket: "How to create the bucket",
  op_como_bucket_txt: "Oracle Cloud (free up to 20 GB): Storage > Buckets > Create Bucket (Standard, no public access). In Profile > Customer Secret Keys > Generate, copy the Access Key and the Secret. Endpoint: https://NAMESPACE.compat.objectstorage.REGION.oraclecloud.com (the namespace is in Tenancy details), region like us-ashburn-1. Backblaze B2: endpoint https://s3.REGION.backblazeb2.com. Cloudflare R2: https://ACCOUNT.r2.cloudflarestorage.com with region auto. AWS: https://s3.REGION.amazonaws.com.",
  op_erros: "Recent server errors",
  op_erros_todos: "Show resolved",
  op_sem_erros: "No open errors.",
  op_resolver: "Mark resolved",
  op_reabrir: "Reopen",
  op_resolvido: "resolved",
  op_traceback: "Traceback",
  op_quando: "When",
  op_rota: "Route",
  op_tipo: "Type",
  op_mensagem: "Message",
  op_dias: "{n} d",
  op_horas: "{n} h",
  op_minutos: "{n} min",
});

Object.assign(I18N_DONO.es, {
  aba_sistema: "Sistema",
  op_saude: "Salud del servidor",
  op_ok: "Todo bien",
  op_problema: "Con problemas",
  op_versao: "Versión",
  op_uptime: "En línea desde hace",
  op_db: "Base de datos",
  op_fila: "Cola de voz (por llamar)",
  op_ult_local: "Último respaldo local",
  op_ult_remoto: "Último respaldo externo",
  op_disco: "Disco",
  op_disco_val: "{pct}% usado, {livre} GB libres",
  op_nunca: "nunca",
  op_condicoes: "Alertas activas",
  op_sem_condicoes: "No hay alertas activas.",
  op_cond_disco: "Disco por encima del 85%",
  op_cond_backup_local: "Respaldo local con más de 26 horas",
  op_cond_voz_presa: "Llamada de voz trabada por más de 60 minutos",
  op_cond_voz_falhas: "5 o más fallas de ElevenLabs/Twilio en la última hora",
  op_cond_backup_remoto: "Respaldo externo atrasado",
  op_alertas_dica: "Las alertas van al correo del dueño (Planes, configuración del dueño) en el idioma elegido allí. Revisión cada 15 minutos; un correo por alerta cada 6 horas.",
  op_bk_titulo: "Respaldo externo cifrado",
  op_bk_desc: "Cada día, después del respaldo local, el servidor cifra y sube a un bucket compatible con S3 (Oracle Object Storage, Backblaze B2, AWS S3, Cloudflare R2): la base de datos, la carpeta uploads/ y chave_dados.key. Guarda 30 días y 12 meses.",
  op_bk_sem_cripto: "El servidor no tiene python3-cryptography: el respaldo externo está apagado.",
  op_endpoint: "Endpoint",
  op_regiao: "Región",
  op_bucket: "Bucket",
  op_prefixo: "Prefijo (carpeta)",
  op_chave_acesso: "Clave de acceso (Access Key)",
  op_segredo: "Secreto (Secret Key)",
  op_segredo_ok: "guardado; déjalo en blanco para mantenerlo",
  op_chave_final: "la actual termina en {f}",
  op_salvar: "Guardar almacenamiento",
  op_testar: "Probar conexión",
  op_agora: "Respaldar ahora",
  op_teste_ok: "Conexión OK: escribir, listar, leer y borrar funcionaron.",
  op_salvo: "Guardado.",
  op_iniciado: "Respaldo iniciado. Actualizando el estado...",
  op_rodando: "Respaldo en curso...",
  op_frase_titulo: "Frase de respaldo",
  op_frase_desc: "Los archivos se cifran con esta frase. Sin ella no hay forma de restaurar: guárdala en un gestor de contraseñas. Mínimo 12 caracteres.",
  op_frase_ok: "Frase definida.",
  op_frase_falta: "Frase aún no definida.",
  op_frase_atual: "Frase actual",
  op_frase_nova: "Nueva frase",
  op_frase_confirma: "Confirmar la frase",
  op_frase_salvar: "Guardar frase",
  op_frase_dica_troca: "Los respaldos antiguos siguen con la frase antigua.",
  op_frases_diferentes: "Las frases no coinciden.",
  op_chave_maquina: "La frase y el secreto quedan cifrados en el servidor con la llave de la máquina backups.key (carpeta de la app). Copia esa llave junto con chave_dados.key a una bóveda.",
  op_chave_maquina_falta: "backups.key aún no existe (se crea al guardar el secreto o la frase).",
  op_status: "Estado",
  op_ultimo_ok: "Último éxito",
  op_tamanho: "Tamaño enviado",
  op_ultimo_erro: "Último error",
  op_ultima_tentativa: "Último intento",
  op_remotos: "Respaldos en el bucket",
  op_carregar_lista: "Listar respaldos",
  op_sem_remotos: "Aún no hay respaldos en el bucket.",
  op_baixar: "Descargar",
  op_baixando: "Descargando y descifrando...",
  op_restaurar_titulo: "Cómo restaurar",
  op_restaurar: "1. Descarga aquí los archivos del día (ya descifrados): rh.db, uploads.tar y chave_dados.key. Fuera del panel: descarga los .enc en la consola del proveedor y ejecuta python3 operacao.py decifrar ARCHIVO.enc SALIDA (pide la frase).\n2. En el servidor: sudo systemctl stop bussola\n3. Guarda el rh.db actual (cp rh.db rh-antes-restauro.db) y copia el rh.db descargado a /home/ubuntu/bussola/rh.db\n4. Archivos: tar -xf uploads.tar -C /home/ubuntu/bussola\n5. Si chave_dados.key desapareció, copia la descargada a /home/ubuntu/bussola/chave_dados.key y ejecuta chmod 600 en ella.\n6. sudo systemctl start bussola y revisa /api/saude.",
  op_como_bucket: "Cómo crear el bucket",
  op_como_bucket_txt: "Oracle Cloud (gratis hasta 20 GB): Storage > Buckets > Create Bucket (Standard, sin acceso público). En Profile > Customer Secret Keys > Generate, copia la Access Key y el Secret. Endpoint: https://NAMESPACE.compat.objectstorage.REGION.oraclecloud.com (el namespace está en Tenancy details), región como us-ashburn-1. Backblaze B2: endpoint https://s3.REGION.backblazeb2.com. Cloudflare R2: https://CUENTA.r2.cloudflarestorage.com con región auto. AWS: https://s3.REGION.amazonaws.com.",
  op_erros: "Errores recientes del servidor",
  op_erros_todos: "Mostrar resueltos",
  op_sem_erros: "No hay errores abiertos.",
  op_resolver: "Marcar resuelto",
  op_reabrir: "Reabrir",
  op_resolvido: "resuelto",
  op_traceback: "Traceback",
  op_quando: "Cuándo",
  op_rota: "Ruta",
  op_tipo: "Tipo",
  op_mensagem: "Mensaje",
  op_dias: "{n} d",
  op_horas: "{n} h",
  op_minutos: "{n} min",
});

let opErrosTodos = false;

function opDuracao(s) {
  const n = Number(s) || 0;
  if (n >= 86400) return td("op_dias", { n: Math.floor(n / 86400) });
  if (n >= 3600) return td("op_horas", { n: Math.floor(n / 3600) });
  return td("op_minutos", { n: Math.floor(n / 60) });
}

function opData(iso) {
  return iso ? fmtDataDono(iso, true) : td("op_nunca");
}

function opTamanho(b) {
  const n = Number(b) || 0;
  if (n >= 1e9) return (n / 1e9).toFixed(2) + " GB";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + " MB";
  if (n >= 1e3) return (n / 1e3).toFixed(0) + " KB";
  return n + " B";
}

function opMsg(id, texto, ok) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.color = ok ? "var(--ok)" : "var(--err)";
  el.textContent = texto;
}

async function abaSistema(el) {
  const r = await api("/api/dono/operacao");
  const s = r.saude;
  const b = r.backup;
  const linha = (rot, val) => `<tr><td>${rot}</td><td class="num">${val}</td></tr>`;
  el.innerHTML = `
    <div class="card">
      <h2 class="icone-titulo">${icone("raio")}<span>${td("op_saude")}</span>
        <span class="badge ${s.ok ? "ok" : "err"}">${s.ok ? td("op_ok") : td("op_problema")}</span></h2>
      <div class="tabela-wrap"><table class="tabela"><tbody>
        ${linha(td("op_versao"), esc(s.versao))}
        ${linha(td("op_uptime"), esc(opDuracao(s.uptime_s)))}
        ${linha(td("op_db"), s.db_ok ? `<span class="badge ok">OK</span>` : `<span class="badge err">${td("op_problema")}</span>`)}
        ${linha(td("op_fila"), s.fila_voz === null ? "-" : fmtNumDono(s.fila_voz))}
        ${linha(td("op_ult_local"), esc(opData(s.ultimo_backup)))}
        ${linha(td("op_ult_remoto"), esc(opData(s.ultimo_backup_remoto)))}
        ${r.disco ? linha(td("op_disco"), esc(td("op_disco_val", { pct: r.disco.usado_pct, livre: r.disco.livre_gb }))) : ""}
      </tbody></table></div>
      <h3 class="mt">${td("op_condicoes")}</h3>
      ${r.condicoes.length
        ? `<ul>${r.condicoes.map((c) => `<li><span class="badge warn">${esc(td("op_cond_" + c))}</span></li>`).join("")}</ul>`
        : `<p class="desc">${td("op_sem_condicoes")}</p>`}
      <p class="hint">${td("op_alertas_dica")}</p>
    </div>
    <div class="card" id="op-backup"></div>
    <div class="card" id="op-erros"></div>`;
  desenharBackupOp(document.getElementById("op-backup"), b, el);
  await desenharErrosOp(document.getElementById("op-erros"));
}

function desenharBackupOp(box, b, el) {
  if (!b.cripto_disponivel) {
    box.innerHTML = `<h2 class="icone-titulo">${icone("cadeado")}<span>${td("op_bk_titulo")}</span></h2>
      <p class="desc"><span class="badge err">${td("op_bk_sem_cripto")}</span></p>`;
    return;
  }
  const configurado = b.endpoint && b.bucket && b.tem_segredo;
  box.innerHTML = `
    <h2 class="icone-titulo">${icone("cadeado")}<span>${td("op_bk_titulo")}</span></h2>
    <p class="desc">${td("op_bk_desc")}</p>
    <details style="margin-bottom:12px"><summary style="cursor:pointer">${td("op_como_bucket")}</summary>
      <p class="hint" style="white-space:pre-line">${esc(td("op_como_bucket_txt"))}</p></details>
    <div class="grid cols-2">
      <label class="field">${td("op_endpoint")} <input type="text" id="op-endpoint" value="${esc(b.endpoint)}" placeholder="https://namespace.compat.objectstorage.us-ashburn-1.oraclecloud.com"></label>
      <label class="field">${td("op_regiao")} <input type="text" id="op-regiao" value="${esc(b.regiao)}" placeholder="us-ashburn-1"></label>
      <label class="field">${td("op_bucket")} <input type="text" id="op-bucket" value="${esc(b.bucket)}" placeholder="bussola-backups"></label>
      <label class="field">${td("op_prefixo")} <input type="text" id="op-prefixo" value="${esc(b.prefixo)}" placeholder="bussola/"></label>
      <label class="field">${td("op_chave_acesso")} ${b.chave_acesso_final ? `<span class="hint">${esc(td("op_chave_final", { f: b.chave_acesso_final }))}</span>` : ""}
        <input type="text" id="op-acesso" autocomplete="off"></label>
      <label class="field">${td("op_segredo")} ${b.tem_segredo ? `<span class="hint">${td("op_segredo_ok")}</span>` : ""}
        <input type="password" id="op-segredo" autocomplete="off"></label>
    </div>
    <div class="form-erro" id="op-bk-msg"></div>
    <div class="linha-acoes">
      <button class="btn" id="op-salvar">${td("op_salvar")}</button>
      <button class="btn secondary" id="op-testar" ${configurado ? "" : "disabled"}>${td("op_testar")}</button>
      <button class="btn secondary" id="op-agora" ${configurado && b.tem_frase && !b.rodando ? "" : "disabled"}>${b.rodando ? td("op_rodando") : td("op_agora")}</button>
    </div>

    <h3 class="mt">${td("op_frase_titulo")} ${b.tem_frase ? `<span class="badge ok">${td("op_frase_ok")}</span>` : `<span class="badge warn">${td("op_frase_falta")}</span>`}</h3>
    <p class="desc">${td("op_frase_desc")} ${b.tem_frase ? td("op_frase_dica_troca") : ""}</p>
    <div class="grid cols-2">
      ${b.tem_frase ? `<label class="field">${td("op_frase_atual")} <input type="password" id="op-frase-atual" autocomplete="off"></label>` : ""}
      <label class="field">${td("op_frase_nova")} <input type="password" id="op-frase" autocomplete="new-password"></label>
      <label class="field">${td("op_frase_confirma")} <input type="password" id="op-frase2" autocomplete="new-password"></label>
    </div>
    <div class="form-erro" id="op-frase-msg"></div>
    <button class="btn secondary" id="op-frase-salvar">${td("op_frase_salvar")}</button>
    <p class="hint mt">${b.chave_maquina_existe ? td("op_chave_maquina") : td("op_chave_maquina_falta")}</p>

    <h3 class="mt">${td("op_status")}</h3>
    <div class="tabela-wrap"><table class="tabela"><tbody>
      <tr><td>${td("op_ultimo_ok")}</td><td class="num">${esc(opData(b.ultimo_ok))}</td></tr>
      <tr><td>${td("op_tamanho")}</td><td class="num">${b.tamanho ? esc(opTamanho(b.tamanho)) : "-"}</td></tr>
      <tr><td>${td("op_ultima_tentativa")}</td><td class="num">${esc(opData(b.ultima_tentativa))}</td></tr>
      ${b.ultimo_erro ? `<tr><td>${td("op_ultimo_erro")}</td><td><span class="badge err">${esc(b.ultimo_erro)}</span></td></tr>` : ""}
    </tbody></table></div>

    <h3 class="mt">${td("op_remotos")}</h3>
    <button class="btn secondary small" id="op-listar" ${configurado ? "" : "disabled"}>${td("op_carregar_lista")}</button>
    <div class="form-erro" id="op-lista-msg"></div>
    <div id="op-lista"></div>

    <details class="mt"><summary style="cursor:pointer">${td("op_restaurar_titulo")}</summary>
      <p class="hint" style="white-space:pre-line">${esc(td("op_restaurar"))}</p></details>`;

  document.getElementById("op-salvar").addEventListener("click", async () => {
    try {
      await api("/api/dono/operacao/backup/config", {
        method: "POST",
        body: {
          endpoint: document.getElementById("op-endpoint").value.trim(),
          regiao: document.getElementById("op-regiao").value.trim(),
          bucket: document.getElementById("op-bucket").value.trim(),
          prefixo: document.getElementById("op-prefixo").value.trim(),
          chave_acesso: document.getElementById("op-acesso").value.trim(),
          segredo: document.getElementById("op-segredo").value.trim(),
        },
      });
      await abaSistema(el);
      opMsg("op-bk-msg", td("op_salvo"), true);
    } catch (e) { opMsg("op-bk-msg", e.message, false); }
  });
  document.getElementById("op-testar").addEventListener("click", async () => {
    opMsg("op-bk-msg", td("carregando"), true);
    try {
      await api("/api/dono/operacao/backup/testar", { method: "POST" });
      opMsg("op-bk-msg", td("op_teste_ok"), true);
    } catch (e) { opMsg("op-bk-msg", e.message, false); }
  });
  document.getElementById("op-agora").addEventListener("click", async () => {
    try {
      await api("/api/dono/operacao/backup/agora", { method: "POST" });
      opMsg("op-bk-msg", td("op_iniciado"), true);
      document.getElementById("op-agora").disabled = true;
      acompanharBackupOp(el, 0);
    } catch (e) { opMsg("op-bk-msg", e.message, false); }
  });
  document.getElementById("op-frase-salvar").addEventListener("click", async () => {
    const frase = document.getElementById("op-frase").value;
    if (frase !== document.getElementById("op-frase2").value) {
      opMsg("op-frase-msg", td("op_frases_diferentes"), false);
      return;
    }
    const atual = document.getElementById("op-frase-atual");
    try {
      await api("/api/dono/operacao/backup/frase", {
        method: "POST", body: { frase, atual: atual ? atual.value : "" },
      });
      await abaSistema(el);
      opMsg("op-frase-msg", td("op_frase_ok"), true);
    } catch (e) { opMsg("op-frase-msg", e.message, false); }
  });
  document.getElementById("op-listar").addEventListener("click", () => listarRemotosOp());
}

// acompanha o backup manual até terminar (no máximo ~10 minutos)
async function acompanharBackupOp(el, tentativas) {
  if (tentativas > 120 || abaAtiva !== "sistema") return;
  await new Promise((ok) => setTimeout(ok, 5000));
  try {
    const r = await api("/api/dono/operacao");
    if (r.backup.rodando) return acompanharBackupOp(el, tentativas + 1);
    if (abaAtiva === "sistema") await abaSistema(el);
  } catch (e) { /* sessão expirada: api() já trata */ }
}

async function listarRemotosOp() {
  const box = document.getElementById("op-lista");
  opMsg("op-lista-msg", td("carregando"), true);
  try {
    const r = await api("/api/dono/operacao/backup/lista");
    opMsg("op-lista-msg", "", true);
    if (!r.dias.length) {
      box.innerHTML = `<p class="desc">${td("op_sem_remotos")}</p>`;
      return;
    }
    box.innerHTML = `<div class="tabela-wrap" style="max-height:360px;overflow-y:auto"><table class="tabela"><tbody>
      ${r.dias.map((d) => d.arquivos.map((a, i) => `<tr>
        <td>${i === 0 ? esc(fmtDataDono(d.dia + "T12:00:00")) : ""}</td>
        <td>${esc(a.nome.replace(/\.enc$/, ""))}</td>
        <td class="num">${esc(opTamanho(a.tamanho))}</td>
        <td class="num"><button class="btn secondary small" data-baixar="${esc(a.chave)}">${td("op_baixar")}</button></td>
      </tr>`).join("")).join("")}
    </tbody></table></div>`;
    box.querySelectorAll("[data-baixar]").forEach((btn) =>
      btn.addEventListener("click", () => baixarRemotoOp(btn.dataset.baixar, btn)));
  } catch (e) { opMsg("op-lista-msg", e.message, false); }
}

// o download precisa do cabeçalho X-Dono-Token, então vai por fetch + blob
async function baixarRemotoOp(chave, btn) {
  opMsg("op-lista-msg", td("op_baixando"), true);
  btn.disabled = true;
  try {
    const resp = await fetch("/api/dono/operacao/backup/baixar?chave=" + encodeURIComponent(chave), {
      headers: { "X-Dono-Token": localStorage.getItem("dono_token") || "", "X-Idioma": idiomaDono },
    });
    if (!resp.ok) {
      const d = await resp.json().catch(() => ({}));
      throw new Error(d.erro || td("erro_comunicacao"));
    }
    const blob = await resp.blob();
    const cd = resp.headers.get("Content-Disposition") || "";
    const m = cd.match(/filename="([^"]+)"/);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = m ? m[1] : "backup";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    opMsg("op-lista-msg", "", true);
  } catch (e) {
    opMsg("op-lista-msg", e.message, false);
  } finally {
    btn.disabled = false;
  }
}

async function desenharErrosOp(box) {
  const r = await api("/api/dono/operacao/erros" + (opErrosTodos ? "?todos=1" : ""));
  box.innerHTML = `
    <h2 class="icone-titulo">${icone("relatorio")}<span>${td("op_erros")}</span></h2>
    <label class="hint" style="display:inline-flex;gap:6px;align-items:center;cursor:pointer">
      <input type="checkbox" id="op-erros-todos" ${opErrosTodos ? "checked" : ""}> ${td("op_erros_todos")}</label>
    ${r.erros.length ? r.erros.map((e) => `
      <details class="sub-card" style="margin:10px 0">
        <summary style="cursor:pointer">
          <span class="badge ${e.resolvido ? "neutral" : "err"}">${esc(e.tipo)}</span>
          ${esc(e.metodo)} ${esc(e.rota)} · ${esc(fmtDataDono(e.quando.replace(" ", "T") + "Z", true))}
          ${e.resolvido ? `<span class="badge ok">${td("op_resolvido")}</span>` : ""}
        </summary>
        <p class="desc"><strong>${td("op_mensagem")}:</strong> ${esc(e.mensagem)}</p>
        <pre style="font-size:.72rem;color:var(--text-2);white-space:pre-wrap;max-height:260px;overflow-y:auto;background:rgba(7,11,20,.5);padding:14px;border-radius:12px">${esc(e.traceback)}</pre>
        <button class="btn secondary small" data-resolver="${e.id}" data-valor="${e.resolvido ? 0 : 1}">${e.resolvido ? td("op_reabrir") : td("op_resolver")}</button>
      </details>`).join("") : `<p class="desc">${td("op_sem_erros")}</p>`}`;
  box.querySelector("#op-erros-todos").addEventListener("change", (ev) => {
    opErrosTodos = ev.target.checked;
    desenharErrosOp(box);
  });
  box.querySelectorAll("[data-resolver]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      try {
        await api("/api/dono/operacao/erros/" + btn.dataset.resolver + "/resolver", {
          method: "POST", body: { resolvido: btn.dataset.valor === "1" },
        });
        await desenharErrosOp(box);
      } catch (e) { alert(e.message); }
    }));
}

// se o painel já foi desenhado antes deste arquivo carregar, redesenha para mostrar a aba Sistema
if (typeof telaAtual !== "undefined" && telaAtual === "painel") desenhar().catch(() => {});
