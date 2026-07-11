# Publicar a Bússola em rh.tonybelleza.com (GoDaddy)

O sistema é um servidor Python que precisa ficar rodando continuamente.
O que dá e o que não dá para fazer no GoDaddy:

## 1. Descubra qual servidor você tem no GoDaddy

- **Hospedagem compartilhada / cPanel / Web Hosting** (a mesma do site
  tonybelleza.com): serve arquivos e PHP, mas **não mantém um servidor Python
  rodando**. A Bússola NÃO funciona nesse plano.
- **VPS ou Servidor Dedicado GoDaddy**: funciona perfeitamente. É um Linux
  completo com acesso SSH.

> Como verificar: no painel do GoDaddy, em "Meus produtos", veja se aparece
> "Web Hosting" (compartilhada) ou "VPS/Servidor". Se tiver só a compartilhada,
> as opções são: contratar o menor VPS do GoDaddy, ou usar um serviço como
> Render/Railway (a partir de US$ 0-7/mês) apontando o subdomínio para ele.

## 2. Publicação no VPS GoDaddy (passo a passo)

No painel DNS do domínio tonybelleza.com, crie um registro:

```
Tipo A · Nome: rh · Valor: IP-DO-SEU-VPS · TTL: 1 hora
```

Conecte no VPS por SSH e rode:

```bash
# 1. dependências (uma vez)
sudo apt update && sudo apt install -y python3 python3-pip caddy
pip3 install anthropic   # para a análise de currículo por IA

# 2. envie a pasta do sistema (do seu Mac)
#    rsync -av --exclude rh.db "/Users/tonybelleza/Documents/RH system/" usuario@IP:/opt/bussola/

# 3. serviço para manter o sistema no ar (systemd)
sudo tee /etc/systemd/system/bussola.service > /dev/null <<'EOF'
[Unit]
Description=Bussola RH
After=network.target
[Service]
WorkingDirectory=/opt/bussola
ExecStart=/usr/bin/python3 server.py 8080
Restart=always
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now bussola

# 4. HTTPS automático com Caddy (certificado gratuito)
sudo tee /etc/caddy/Caddyfile > /dev/null <<'EOF'
rh.tonybelleza.com {
    reverse_proxy localhost:8080
}
EOF
sudo systemctl reload caddy
```

Pronto: https://rh.tonybelleza.com no ar com certificado.

## 3. Depois de publicar

1. Acesse `/gestor`, crie a conta do administrador.
2. Acesse `/dono`, crie a senha do dono (seu painel de proprietário).
3. Em Configurações → Integrações, preencha:
   - **Endereço público**: `https://rh.tonybelleza.com` (links dos e-mails)
   - SMTP e chave da IA quando quiser ativar.
4. Compartilhe: vagas em `/vagas` e a página de cada gestor em
   `/vagas?g=LOGIN`.

## 4. Alternativa sem VPS (se você só tem a hospedagem compartilhada)

Render.com (plano Starter) ou Railway rodam o sistema a partir desta pasta;
depois é só criar no GoDaddy um registro `CNAME rh` apontando para o endereço
que eles fornecem. Me avise qual caminho prefere que eu te guio ao vivo.

> Importante: a publicação exige entrar na sua conta GoDaddy e, talvez,
> contratar um plano. Esses passos são seus; eu preparo tudo e acompanho.
