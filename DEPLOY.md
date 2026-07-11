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
  --exclude rh.db --exclude uploads --exclude backups \
  --exclude __pycache__ --exclude .git --exclude nohup.out --exclude .DS_Store \
  -e "ssh -i ~/.ssh/bussola_oracle" \
  "/Users/tonybelleza/Documents/RH system/" ubuntu@159.54.181.125:/home/ubuntu/bussola/

# 2. reinicia o serviço
ssh -i ~/.ssh/bussola_oracle ubuntu@159.54.181.125 'sudo systemctl restart bussola'
```

> O conteúdo confidencial do módulo Diagnóstico (`docs/`) **não** vai ao GitHub
> (está no `.gitignore`), mas **vai** pelo rsync acima, porque não está na lista
> de exclusões. Se recriar o servidor do zero, reenvie a pasta `docs/`.

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
