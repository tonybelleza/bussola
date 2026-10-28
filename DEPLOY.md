# Publicação da Bússola

O sistema **está no ar** em **https://rh.tonybelleza.com**.

## Infraestrutura atual

- **Servidor**: Oracle Cloud Always Free (Ubuntu, VM.Standard.E2.1.Micro),
  região us-sanjose-1, IP público `159.54.181.125`.
- **Aplicação**: `python3 server.py 8080` rodando como serviço systemd
  (`/etc/systemd/system/bussola.service`), reinicia sozinho.
- **HTTPS**: Caddy na frente (portas 80/443), certificado Let's Encrypt
  automático. `Caddyfile`:
  ```
  rh.tonybelleza.com {
      reverse_proxy localhost:8080
  }
  ```
- **DNS**: registro A `rh` → `159.54.181.125` no painel do domínio.
- **Dados**: `rh.db` (SQLite), `uploads/`, `backups/` e `docs/` ficam só no
  servidor, fora do Git.

## Atualizar o sistema (a partir do Mac)

```bash
# 1. envia o código (não sobrescreve banco, uploads, backups nem docs)
rsync -az --delete \
  --exclude rh.db --exclude uploads --exclude backups --exclude chave_dados.key --exclude "*.key" --exclude exportacoes \
  --exclude __pycache__ --exclude .git --exclude nohup.out --exclude .DS_Store \
  -e "ssh -i ~/.ssh/bussola_oracle" \
  "/Users/tonybelleza/Documents/RH system/" ubuntu@159.54.181.125:/home/ubuntu/bussola/

# 2. reinicia o serviço
ssh -i ~/.ssh/bussola_oracle ubuntu@159.54.181.125 'sudo systemctl restart bussola'
```

> O conteúdo confidencial do módulo Diagnóstico (`docs/`) **não** vai ao GitHub
> (está no `.gitignore`), mas **vai** pelo rsync acima, porque não está na lista
> de exclusões. Se recriar o servidor do zero, reenvie a pasta `docs/`.

> **`chave_dados.key` nunca pode ser sobrescrita nem perdida.** É a chave que cifra os
> dados sensíveis do onboarding (SSN, conta bancária, data de nascimento, carteira de
> motorista) e todos os PDFs e uploads em `uploads/onboarding/`. O `--exclude chave_dados.key`
> acima é obrigatório: sem ele o `--delete` apagaria a chave do servidor (ou a chave do
> Mac a substituiria). Veja a seção "Módulo Onboarding" abaixo.

## Primeiro acesso (num servidor novo)

1. Acesse `/gestor` e crie a conta do administrador.
2. Acesse `/dono` e crie a senha do dono (painel de proprietário).
3. Em Configurações → Integrações, preencha:
   - **Endereço público**: `https://rh.tonybelleza.com` (usado nos links dos e-mails)
   - SMTP e chave da IA quando quiser ativar.
4. Compartilhe: vagas em `/vagas` e a página de cada gestor em `/vagas?g=LOGIN`.

## Recriar a infraestrutura (referência)

```bash
sudo apt update && sudo apt install -y python3 python3-pip caddy
pip3 install --user anthropic   # opcional, para a análise de currículo por IA

sudo tee /etc/systemd/system/bussola.service > /dev/null <<'EOF'
[Unit]
Description=Bussola RH (Tony Belleza)
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/bussola
ExecStart=/usr/bin/python3 server.py 8080
Restart=always
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now bussola

sudo tee /etc/caddy/Caddyfile > /dev/null <<'EOF'
rh.tonybelleza.com {
    reverse_proxy localhost:8080
}
EOF
sudo systemctl reload caddy
```

## Módulo Triagem por Voz (voz.py)

- O `voz.py` precisa ir junto do `server.py` (o rsync acima já envia tudo).
- Na primeira subida, o banco ganha sozinho as tabelas `voz_config` e `voz_chamadas` e
  colunas novas em `candidaturas`, `cargos` e `candidatos`. Faça backup do `rh.db` antes:
  ```bash
  ssh -i ~/.ssh/bussola_oracle_studio ubuntu@159.54.181.125 'cp /home/ubuntu/bussola/rh.db /home/ubuntu/bussola/backups/rh-antes-voz.db'
  ```
- A fila de ligações roda numa thread do próprio servidor, uma rodada por minuto. Para
  desligar a fila sem mexer no código, defina `VOZ_FILA_DESLIGADA=1` no serviço systemd.
- Configuração no painel do gestor, aba **Triagem por voz** (admin):
  1. Integração ElevenLabs: chave da API, ID da agente e ID do número.
  2. Marque os cargos que usam triagem por voz e o peso no match (padrão 30%).
  3. Libere o módulo "Triagem por Voz" para os gestores no painel do dono.
- Webhook: no ElevenLabs (Agents > Settings > Post-call webhook), use
  `https://rh.tonybelleza.com/api/voz/webhook`, eventos de transcrição pós chamada e falha de
  início de chamada, e cole o segredo HMAC em "Segredo do webhook" na aba. Sem o webhook o
  resultado chega mesmo assim, pela verificação automática (1 a 3 minutos de atraso).
- Testes antes de subir: `python3 teste_sistema.py` e `python3 teste_voz.py`.

## Módulo Onboarding (onboarding.py)

- Vai junto pelo rsync (`onboarding.py`, `formularios.py`, `public/onboarding.html`,
  `public/js/onboarding.js`, `public/js/gestor-onboarding.js`). Os PDFs oficiais dos
  formulários ficam em `docs/forms/` (também enviados pelo rsync).
- Dependências no servidor: `python3-cryptography` (a 3.4.8 do Ubuntu basta: só usa
  `cryptography.fernet.Fernet`), `fpdf2` e `pypdf` (formulários).
- **Chave de criptografia**: na primeira vez que alguém usa o onboarding o servidor cria
  `/home/ubuntu/bussola/chave_dados.key` (permissão 0600, fora de `public/`). Alternativa:
  definir `BUSSOLA_CHAVE_DADOS` no serviço systemd (`Environment=BUSSOLA_CHAVE_DADOS=...`).
  - Nunca sobrescreva, apague ou troque essa chave: sem ela os dados cifrados e os arquivos
    do onboarding ficam ilegíveis para sempre.
  - O backup diário copia só o `rh.db`. Guarde uma cópia da chave **separada** do backup do
    banco (por exemplo num cofre de senhas), nunca no Git:
    ```bash
    ssh -i ~/.ssh/bussola_oracle ubuntu@159.54.181.125 'cat /home/ubuntu/bussola/chave_dados.key'
    ```
  - Trava de segurança: se já houver dados cifrados e a chave sumir, o servidor **não** cria
    uma chave nova; as rotas do onboarding devolvem erro e o log mostra "A chave de
    criptografia dos dados não foi encontrada". Restaure o arquivo e reinicie o serviço.
    Uma chave diferente da original também é detectada (verificador na tabela `config`).
- Configuração no painel do gestor, Configurações, cartão **Onboarding** (admin): modelos de
  documentos (rascunhos para revisão de um advogado), formas de pagamento, formulários
  estaduais (CT-W4), prazo, lembretes, retenção e os dados do empregador (nome legal,
  endereço, EIN, contato e telefone) usados no W-4, CT-W4, W-9 e na Seção 2 do I-9.
- Testes antes de subir: `python3 teste_onboarding.py` e `python3 teste_formularios.py`.

## Operação: backup externo, saúde e alertas (operacao.py)

- Vai junto pelo rsync (`operacao.py`, `public/js/dono-operacao.js`). Painel do dono, aba
  **Sistema**: saúde, alertas ativos, backup externo e erros recentes do servidor.
- Dependência: `python3-cryptography` (a 3.4.8 do Ubuntu basta: só usa `Fernet`).

### Backup externo cifrado (S3 compatível)

Todo dia, depois do backup local, o servidor cifra e envia para o bucket:
`<prefixo>diario/AAAA-MM-DD/rh.db.enc`, `uploads.tar.enc` e `chave_dados.key.enc`.
Guarda 30 dias + o último dia de cada um dos 12 meses mais recentes (o resto é apagado).

Criar o bucket no Oracle Object Storage (camada gratuita: 20 GB):
1. Console da Oracle Cloud > Storage > Object Storage > Buckets > **Create Bucket**.
   Nome `bussola-backups`, camada Standard, sem acesso público (padrão).
   Opcional: Lifecycle rule não é necessária (a poda é feita pela Bússola).
2. Avatar (canto superior direito) > **My profile** > Customer secret keys (ou "Saved
   keys") > **Generate secret key**. Copie o Secret na hora (só aparece uma vez) e a
   Access key da lista.
3. Namespace: Avatar > Tenancy > "Object storage namespace".
4. No painel do dono, aba Sistema:
   - Endpoint: `https://<namespace>.compat.objectstorage.<regiao>.oraclecloud.com`
   - Região: a do bucket, por exemplo `us-ashburn-1`
   - Bucket: `bussola-backups`; Prefixo: `bussola/`
   - Access Key e Secret Key do passo 2. **Salvar armazenamento** e **Testar conexão**.
5. Defina a **frase de backup** (mínimo 12 caracteres) e guarde-a num cofre de senhas.
   Sem ela não há como restaurar. Depois, **Fazer backup agora** e confira o status.

Outros provedores: Backblaze B2 `https://s3.<regiao>.backblazeb2.com`; Cloudflare R2
`https://<conta>.r2.cloudflarestorage.com` com região `auto`; AWS `https://s3.<regiao>.amazonaws.com`.

Chave da máquina `backups.key`:
- A frase e o segredo do bucket ficam no banco cifrados com `/home/ubuntu/bussola/backups.key`
  (0600, criada ao salvar o segredo ou a frase). O deploy não envia `*.key`.
- Copie essa chave para o cofre junto com a `chave_dados.key`:
  ```bash
  ssh -i ~/.ssh/bussola_oracle ubuntu@159.54.181.125 'cat /home/ubuntu/bussola/backups.key'
  ```
- Se ela sumir, o backup externo para com erro; basta informar de novo o segredo e a frase
  (com a frase atual) no painel. Os backups já enviados dependem só da frase.

Restaurar:
1. Painel do dono > Sistema > Listar backups > **Baixar** (sai decifrado). Sem o painel:
   baixe os `.enc` no console do provedor e rode `python3 operacao.py decifrar ARQUIVO.enc SAIDA`
   (pede a frase).
2. `sudo systemctl stop bussola`; guarde o `rh.db` atual; copie o `rh.db` restaurado para
   `/home/ubuntu/bussola/rh.db`; `tar -xf uploads.tar -C /home/ubuntu/bussola`; se a
   `chave_dados.key` sumiu, copie a restaurada e rode `chmod 600`.
3. `sudo systemctl start bussola` e confira `https://rh.tonybelleza.com/api/saude`.

### Saúde e alertas

- `GET /api/saude` (público, sem dados sensíveis): `ok`, `versao`, `uptime_s`, `db_ok`,
  `fila_voz`, `ultimo_backup`, `ultimo_backup_remoto`. Responde 503 quando o banco falha.
- Erros não tratados da API ficam na tabela `erros_servidor` (rota sem tokens, sem corpo do
  pedido, e-mails e tokens mascarados) e geram e-mail ao dono (config `dono_email`, idioma
  `dono_idioma`, definidos em Planos) no máximo 1 a cada 30 minutos por erro, mais um resumo
  diário. Precisa do SMTP configurado em Integrações.
- A cada 15 minutos uma thread confere: disco acima de 85%, backup local com mais de 26 horas,
  ligação de voz `em_andamento` há mais de 60 minutos, 5 ou mais erros em `voz_chamadas` na
  última hora e backup externo atrasado (mais de 50 horas). Um e-mail por condição a cada 6
  horas. Para desligar a thread: `OPERACAO_MONITOR_DESLIGADO=1` no serviço systemd.

### Verificação externa (GitHub Actions)

- `.github/workflows/saude.yml` roda a cada 15 minutos e sob demanda (Actions > Saude > Run
  workflow). Faz até 5 tentativas em `/api/saude`; se nenhuma vier com `"ok": true`, o job
  falha e o GitHub manda e-mail ao dono do repositório (confira em GitHub > Settings >
  Notifications > Actions: "Send notifications for failed workflows only").
- O agendamento só vale no branch padrão (`main`): o arquivo precisa estar lá.
- Repositório privado no plano Free tem 2.000 minutos/mês de Actions; a cada 15 minutos são
  cerca de 2.900 execuções de 1 minuto. Se o repositório for privado, troque o cron para
  `*/30 * * * *` (ou use o plano Pro). Em repositório público é grátis, mas o GitHub
  desativa agendamentos após 60 dias sem commits (reative em Actions).

## Domínios próprios das páginas de vagas (dominios.py)

Cada empresa pode publicar a página de vagas no próprio endereço (ex.: `jobs.cliente.com`).
O administrador da empresa cadastra o domínio em Configurações > "Domínio próprio das vagas",
cria os registros DNS mostrados no painel e clica em **Verificar**:

- Apontamento: `CNAME jobs.cliente.com -> rh.tonybelleza.com` (subdomínio) ou
  `A cliente.com -> 159.54.181.125` (domínio raiz).
- Posse: `TXT _bussola.jobs.cliente.com = bussola-verificacao=<código do painel>`.
- A verificação exige as duas coisas: o domínio resolve para o mesmo IP de
  `rh.tonybelleza.com` (ou para um IP da config opcional `dominios_ip`, lista separada por
  vírgula) e o TXT é lido via DNS over HTTPS em `https://dns.google/resolve`.
- Limite por empresa: campo `dominios_max` do plano no catálogo (Planos no painel do dono);
  sem o campo, 1. `null` = sem limite.

Comportamento no domínio próprio verificado: `/` abre a lista de vagas da empresa, `/vaga?id=`
só mostra vagas da própria empresa, `/candidato`, estáticos e a API seguem normais, e
`/gestor` e `/dono` redirecionam (302) para `https://rh.tonybelleza.com`. A URL canônica e o
JSON-LD das vagas usam o domínio próprio; o `sitemap.xml` do domínio próprio lista só a
empresa, e o sitemap principal deixa de listar as empresas que têm domínio próprio.

Se `rh.tonybelleza.com` passar a usar proxy da Cloudflare (nuvem laranja), o IP resolvido
deixa de ser o do servidor: nesse caso grave `dominios_ip` com `159.54.181.125`:
```bash
sqlite3 /home/ubuntu/bussola/rh.db "INSERT OR REPLACE INTO config (chave, valor) VALUES ('dominios_ip', '159.54.181.125')"
```

### Passo 1: publicar o código

Pelo rsync de sempre (vai `dominios.py` e `public/js/gestor-dominio.js`) e
`sudo systemctl restart bussola`. A tabela `dominios_empresa` é criada na partida. Confira:
```bash
curl -i "http://localhost:8080/api/dominios/permitido?domain=naoexiste.com"   # 404
curl -s "http://localhost:8080/api/dominio"                                    # {"slug": null}
```

### Passo 2: Caddy com TLS sob demanda

O Caddy só emite certificado para um domínio desconhecido depois de perguntar à Bússola
(`ask`), que responde 200 apenas para domínios verificados de empresas ativas (os demais
recebem 404, e pedidos de domínios desconhecidos acima de 300 por minuto recebem 429).

1. Backup do arquivo atual:
   ```bash
   sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak-dominios
   ```
2. Novo `/etc/caddy/Caddyfile` completo (os dois blocos atuais continuam iguais):
   ```caddyfile
   {
   	on_demand_tls {
   		ask http://localhost:8080/api/dominios/permitido
   	}
   }

   rh.tonybelleza.com {
   	reverse_proxy localhost:8080
   }

   http://159.54.181.125 {
   	reverse_proxy localhost:8080
   }

   # domínios próprios das empresas (certificado emitido no primeiro acesso, após o "ask")
   :443 {
   	tls {
   		on_demand
   	}
   	reverse_proxy localhost:8080
   }
   ```
   O `reverse_proxy` do Caddy repassa o cabeçalho `Host` original, que é o que a Bússola usa
   para descobrir a empresa. As portas 80 e 443 já estão abertas na VM e na Oracle.
3. Validar e recarregar (o reload não derruba conexões):
   ```bash
   sudo caddy validate --config /etc/caddy/Caddyfile
   sudo systemctl reload caddy
   sudo journalctl -u caddy -n 50 --no-pager
   ```
4. Teste com um domínio verificado (depois de o cliente criar o DNS e verificar no painel):
   ```bash
   curl -i "http://localhost:8080/api/dominios/permitido?domain=jobs.cliente.com"   # 200
   curl -I https://jobs.cliente.com/                                                 # 200, certificado válido
   curl -I https://jobs.cliente.com/gestor                                           # 302 para rh.tonybelleza.com
   ```
   O primeiro acesso demora alguns segundos (emissão do certificado Let's Encrypt). Erros de
   emissão aparecem em `journalctl -u caddy`.

### Desfazer (rollback)

```bash
sudo cp /etc/caddy/Caddyfile.bak-dominios /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy
```
Os domínios próprios param de responder em HTTPS; `rh.tonybelleza.com` e o IP seguem como
antes. O código pode ficar no servidor: sem o bloco `:443` nada chega com outro `Host`. Para
remover também o código, apague `dominios.py` e reinicie (`server.py` importa o módulo de
forma opcional); a tabela `dominios_empresa` pode ficar no banco sem efeito.
