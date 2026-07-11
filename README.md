# Bússola · Recrutamento e Seleção (Tony Belleza)

Nome do produto: **Bússola** (metodologia B.A.S.E.). Preparado para rodar em
**rh.tonybelleza.com** (configure o endereço em Configurações → Integrações →
"Endereço público do sistema" para os links dos e-mails).

Plataforma completa de avaliação comportamental e planejamento de desenvolvimento
profissional, com mapeamento de cargos e funções e geração automática de matriz de gaps.

## Como rodar

Dê **dois cliques** no arquivo `Iniciar Sistema RH.command` (ele inicia o servidor
se necessário e abre o navegador). Ou, pelo terminal:

```bash
cd "/Users/tonybelleza/Documents/RH system"
python3 server.py 8080
```

Depois abra **http://localhost:8080** no navegador.

Não precisa instalar nada — usa apenas Python 3 (já vem no macOS) e SQLite.
O banco de dados (`rh.db`) é criado automaticamente na primeira execução,
já com 4 cargos de exemplo da área de GTI.

## Acessos

| Perfil | Acesso | O que vê |
|---|---|---|
| **Landing page** | `http://localhost:8080/` | Página do produto com todos os acessos |
| **Candidato** | `/candidato` | Apenas os próprios testes e resultados; acesso pelo link pessoal (reenvio por e-mail em "Já tem cadastro?") |
| **Gestor** | `/gestor` | Painel completo (login e senha próprios) |
| **Vagas gerais** | `/vagas` | Todas as vagas abertas |
| **Página do gestor** | `/vagas?g=LOGIN` | Só as vagas do local daquele gestor; quem se candidata por ela entra direto no processo dele (link pronto em Configurações) |
| **Painel do dono** | `/dono` | Exclusivo do proprietário do software (senha mestra própria): todas as contas, entrar em qualquer conta para suporte, redefinir senhas, saúde do sistema (versão, banco, backups, log) e controle de clientes/cobrança por local |

### Colaboradores internos (caso da instituição pública)

No cadastro, a pessoa escolhe entre "Me candidatando a uma oportunidade" e
"Já trabalho na instituição". O colaborador interno seleciona a própria função,
faz os mesmos testes e recebe a matriz de gaps e o plano de desenvolvimento da
função dele, além do match com todos os cargos para avaliar upgrade. No painel
do gestor ele aparece com o selo "Colaborador" e há filtro por perfil.

Para publicar em rh.tonybelleza.com (GoDaddy), veja o **DEPLOY.md**.

**Primeiro acesso**: ao abrir o painel do gestor pela primeira vez, o sistema
pede o cadastro da conta do administrador (nome, login e senha) — não existe
senha padrão. Depois disso, o administrador cria as contas dos demais gestores.

### Contas de gestor e locais de avaliação

- Cada gestor entra com **login e senha próprios**. O administrador cria as contas
  na aba **Configurações → Contas de gestor**.
- No cadastro, o candidato informa **onde está fazendo a avaliação**
  (instituição/unidade/setor). Esse local aparece no painel do gestor.
- Um gestor **vinculado a um local** vê apenas os candidatos daquele local;
  contas sem local (ou administradoras) veem todos os candidatos.

## Módulos

### 1. Teste DISC (criado do zero)
24 blocos de 4 palavras — o candidato marca a que **mais** e a que **menos** se
parece com ele. Gera perfil nas 4 dimensões (Dominância, Influência, Estabilidade,
Conformidade) com pontos fortes, pontos de desenvolvimento e estilo de trabalho.

### 2. Teste B.A.S.E. (o teste original de tonybelleza.com/base)
8 rodadas de 4 cartas ordenadas da que mais combina para a que menos combina
(1º vale 4 pontos, 2º vale 3, 3º vale 2, 4º vale 1). Gera o código completo de
personalidade (a ordem das 4 letras: Bússola, Atuante, Sensível, Estudioso) com
o relatório original: perfil, pontos fortes, leitura das 4 posições do código,
gatilhos e dicas de comunicação com os outros perfis.

### Match geral candidato × cargo

Cada cargo pode definir, além das competências, o **perfil DISC desejado** e o
**arquétipo B.A.S.E. desejado**. O sistema cruza tudo num índice único:

> **Match geral = competências (30%) + DISC (15%) + B.A.S.E. (15%)
> + teste de conhecimento (20%) + entrevista (20%)**

Os pesos são renormalizados sobre o que já foi respondido. O match aparece na
lista de candidatos, no relatório individual, nos resultados do candidato, no
pipeline das vagas e na matriz consolidada, sempre ordenado do maior para o menor.

### Recrutamento e seleção (ATS)

- **Vagas e portal público**: o gestor abre vagas na aba Vagas; os candidatos
  se inscrevem pelo portal `/vagas` (link "Trabalhe conosco").
- **Pipeline Kanban**: cada vaga tem um quadro com as etapas Inscrito,
  Avaliações, Entrevista, Proposta, Contratado e Reprovado. Arraste os cartões
  para mover candidatos; cada mudança pode notificar o candidato por e-mail.
- **Ranking da vaga**: candidatos ordenados por match, com etapa e contato.
- **Entrevista estruturada (scorecard)**: roteiro de perguntas por cargo, notas
  de 1 a 5 por critério; a média entra no match.
- **Teste de conhecimento**: questões de múltipla escolha por cargo, corrigidas
  automaticamente; o percentual entra no match.
- **Linha do tempo e anotações**: todo o histórico do candidato (testes, etapas,
  e-mails, entrevistas, anotações dos gestores) fica registrado no relatório.
- **Mobilidade interna**: o relatório mostra o match do candidato com todos os
  cargos mapeados, para realocação e upgrade de cargo.

### Banco de talentos (CRM)

- **Tags e filtros**: etiquete candidatos (ex.: "java", "lideranca") e filtre o
  banco por busca, local, cargo, tag e match mínimo. Exportação em CSV.
- **Radar de talentos**: ao abrir o pipeline de uma vaga, o sistema varre o
  banco inteiro e sugere quem tem 60%+ de match e ainda não está na vaga, com
  botão para adicionar. É a "redescoberta de medalhistas de prata" dos CRMs.
- **Duplicados**: se um e-mail já cadastrado tentar novo cadastro, o sistema
  reaproveita a ficha (inclusive inscrevendo na nova vaga) e reenvia o link
  pessoal por e-mail, sem nunca expor os dados a terceiros.
- **Modelos de e-mail editáveis**: em Configurações, o administrador personaliza
  todos os textos (confirmação, lembrete e cada etapa) com os campos {nome},
  {vaga}, {link}, {local} e {etapa}.
- **E-mail manual**: botão "Enviar e-mail" no relatório do candidato, com
  registro na linha do tempo.
- **Follow-up automático**: candidato que não concluiu a avaliação em 2 dias
  recebe um lembrete com o link pessoal (uma única vez, e só se o SMTP estiver
  configurado).
- **Relatórios**: aba com funil de conversão por vaga, candidatos por mês, taxa
  de conclusão, contratados, tempo médio até contratar e distribuição dos
  perfis DISC/B.A.S.E. do banco.
- **LGPD**: consentimento obrigatório no cadastro, botão "Anonimizar" no
  relatório do candidato e retenção automática configurável (anonimiza fichas
  antigas após N meses).

### Integrações opcionais (os únicos itens pagos)

Tudo acima funciona sem custo. Em **Configurações → Integrações** (administrador),
dois recursos extras podem ser ativados:

1. **Análise de currículo por IA** (API da Anthropic): lê o currículo em PDF,
   resume o perfil, cruza com a autoavaliação e aponta divergências. Requer uma
   chave de API (console.anthropic.com) e `pip3 install anthropic` no servidor;
   custo de centavos por análise.
2. **Notificações por e-mail** (SMTP): funciona com qualquer conta SMTP (no
   Gmail, use uma senha de app); sem custo adicional além da conta de e-mail.
   Com o SMTP configurado, os envios são automáticos:
   - **Para o candidato**: confirmação de inscrição com o link pessoal de
     acesso (permite continuar de qualquer aparelho) e avisos quando muda de
     etapa no processo (o gestor confirma o envio a cada movimentação).
   - **Para os gestores**: aviso de novo candidato e aviso de avaliação
     completa com o match calculado. Cada gestor recebe apenas o que é do seu
     local; administradores e gestores sem local recebem tudo. O e-mail do
     gestor é cadastrado na conta dele (Configurações → Contas de gestor).

   Mesmo sem SMTP, o painel mostra tudo: a **Visão geral** tem o feed
   "Últimas atividades" (novos candidatos, testes concluídos, avaliações
   completas, mudanças de etapa e anotações, com atalho para o relatório).

### 3. Mapeamento de cargos e funções + Matriz de Gaps
- O gestor cadastra cargos com as competências exigidas (técnicas, relacionais,
  formações/certificações e experiência), o nível exigido (1–5) e se são obrigatórias.
- O candidato responde a autoavaliação de competências do cargo de interesse.
- O sistema cruza as respostas com o mapeamento e gera:
  - **Matriz de gaps** individual (nível exigido × nível atual × gap)
  - **% de aderência ao cargo** e status (Apto / Em desenvolvimento / Gap alto)
  - **Plano de desenvolvimento** priorizado (obrigatórias primeiro, maiores gaps primeiro)
- Na aba **Matriz de gaps** do painel, o gestor compara todos os candidatos com
  qualquer cargo — útil também para avaliar **upgrade de cargo** de servidores.

### 4. Currículo e redes profissionais
O candidato pode enviar o currículo (PDF, até 8 MB) e informar **LinkedIn e
Instagram** no cadastro. O gestor baixa o currículo e abre os perfis com um
clique no relatório do candidato, para cruzar com as respostas da avaliação.

## Estrutura dos arquivos

```
server.py            → servidor + API + banco (Python stdlib, sem dependências)
rh.db                → banco SQLite (criado automaticamente)
uploads/             → currículos enviados
public/
  index.html         → página inicial
  candidato.html/.js → área do candidato
  gestor.html/.js    → painel do gestor
  js/data.js         → conteúdo dos testes (perguntas, perfis, textos)
  js/render.js       → renderização compartilhada dos resultados
  css/style.css      → estilo
```

Para editar as perguntas dos testes ou os textos dos perfis, basta alterar
`public/js/data.js` — não precisa mexer no servidor.

## Operação e manutenção

- **Backup automático**: a cada inicialização o servidor guarda uma cópia diária
  do banco em `backups/` (mantém as 14 mais recentes). Para restaurar, pare o
  servidor e substitua `rh.db` pela cópia desejada.
- **Exportar planilha**: na aba Candidatos há um botão "Exportar planilha (CSV)"
  que baixa todos os candidatos com perfis, match e status (abre no Excel).
- **Testes automatizados**: `python3 teste_sistema.py` roda 78 verificações do
  sistema inteiro (acessos, vagas, pipeline, match, isolamento por local,
  segurança) num banco temporário, sem tocar nos dados reais.
- **Celular**: todas as telas são responsivas; os candidatos podem responder
  tudo pelo telefone.

## Publicar na internet

O sistema precisa de um servidor com Python 3 (não funciona em hospedagem
estática como a do teste /base). Opções simples e baratas:

- **VPS** (Hostinger, DigitalOcean, Oracle Cloud Free): copie a pasta e rode
  `python3 server.py 80` (ideal com HTTPS via Caddy ou Nginx na frente).
- **Render.com / Railway / Fly.io**: deploy direto da pasta.
- Depois é só apontar um subdomínio, ex.: `rh.tonybelleza.com`.
