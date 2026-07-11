#!/bin/bash
# Inicia o Sistema de RH e abre o navegador. Basta dar dois cliques neste arquivo.
cd "$(dirname "$0")"

if curl -s -o /dev/null --max-time 2 http://localhost:8080/api/vagas; then
  echo "O sistema já está rodando."
else
  echo "Iniciando o Sistema de RH..."
  nohup python3 server.py 8080 > /tmp/rh-server.log 2>&1 &
  for i in 1 2 3 4 5 6 7 8 9 10; do
    sleep 1
    if curl -s -o /dev/null --max-time 2 http://localhost:8080/api/vagas; then
      break
    fi
  done
fi

open "http://localhost:8080"
echo
echo "Sistema de RH disponível em http://localhost:8080"
echo "  Painel do gestor:   http://localhost:8080/gestor.html"
echo "  Portal de vagas:    http://localhost:8080/vagas.html"
echo
echo "Pode fechar esta janela."
