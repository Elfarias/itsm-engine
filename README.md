# ITSM Agent

Plataforma de Triagem Inteligente de Incidentes de TI com IA, regras
determinísticas, integração controlada e resiliência.

> **Status:** API mínima de chamados, triagem determinística e interpretação
> por LLM implementadas; integração ITSM externa no roadmap.

## Visão geral

O ITSM Agent recebe chamados pela API e oferece um serviço interno de
triagem determinística. Uma rota local também pode extrair uma proposta
revisável da descrição salva do chamado. A interpretação não altera o
chamado nem substitui a triagem determinística. O serviço de triagem avalia fatos estruturados com
catálogos sintéticos versionados, calcula a prioridade pela matriz
aprovada e seleciona a equipe pelo mapeamento do serviço. A triagem pode
ser iniciada pela rota local `POST /tickets/{ticket_id}/triage`; o
servidor permanece ligado somente a `127.0.0.1` e não expõe a rota à
rede pública.

Consultas à KEDB e integração ITSM externa permanecem no roadmap.

## Objetivos

- Reduzir tarefas repetitivas de triagem.
- Preparar uma futura integração segura entre LLM e sistemas
  corporativos.
- Aplicar regras de negócio determinísticas.
- Controlar estados e operações de integração.
- Demonstrar idempotência, auditoria e recuperação de falhas.
- Manter uma arquitetura simples e sustentável.

## Arquitetura resumida

``` text
Cliente
        |
        v
FastAPI: criar / consultar chamados, propor interpretação e iniciar triagem
        |
        v
 PostgreSQL: chamados
        |
Interpretação local: descrição salva -> OpenRouter
        |
Chamador local revisa a proposta e resolve fatos estruturados
        |
        v
 Serviço interno de triagem
        |
        +----> Catálogo PostgreSQL versionado
        |
        +----> Regras de impacto, urgência e prioridade
        |
        +----> Auditoria transacional

Futuro: consultas à KEDB / integração ITSM externa
```

## Stack principal

- Python
- FastAPI
- Pydantic
- PostgreSQL
- Docker e Docker Compose
- OpenRouter para propostas de interpretação; integração ITSM externa e
  retries permanecem no roadmap

Não fazem parte da primeira versão: Kubernetes, Kafka, Redis, PGVector e
arquitetura de microsserviços.

Consulte [TECHNOLOGY-STACK.md](TECHNOLOGY-STACK.md) para justificativas
e decisões.

## Documentação

  --------------------------------------------------------------------------------
  Documento                                    Conteúdo
  -------------------------------------------- -----------------------------------
  [PROJECT.md](PROJECT.md)                     Objetivos, escopo, requisitos e
                                               critérios de aceite

  [ARCHITECTURE.md](ARCHITECTURE.md)           Componentes, fluxo, dados, estados
                                               e confiabilidade

  [TECHNOLOGY-STACK.md](TECHNOLOGY-STACK.md)   Tecnologias, justificativas e itens
                                               fora do escopo
  --------------------------------------------------------------------------------

## Fluxo de triagem

1. A API valida e persiste o chamado no estado `NOVO`.
2. Um cliente local envia os fatos estruturados e a revisão esperada a
   `POST /tickets/{ticket_id}/triage`; a rota encaminha a solicitação ao
   serviço de triagem determinística.
3. O serviço bloqueia o chamado e carrega a versão ativa do catálogo.
4. As regras validam referências e consistência do ativo, calculam a
   prioridade pela matriz aprovada e obtêm a equipe do catálogo.
5. O snapshot completo, o resultado, o estado e a auditoria são gravados
   na mesma transação.
6. Fatos completos deixam o chamado em `EM_TRIAGEM`; dados ausentes ou
   conflitantes deixam-no em `PENDENTE_INFORMACAO`, sem prioridade ou
   equipe.
7. Uma reavaliação pendente substitui o snapshot completo. Retries
   idênticos não duplicam efeitos; revisões concorrentes desatualizadas
   geram conflito explícito.

A proposta por LLM é uma operação separada: não altera o fluxo de triagem,
não grava fatos e não cria eventos de auditoria. Consultas à KEDB e
atualização de um ITSM externo não fazem parte do fluxo atual.

## API local de triagem

Depois de configurar `DATABASE_URL`, aplicar as migrações e iniciar o
servidor local, crie um chamado e avalie-o usando o ID retornado:

```powershell
$ticket = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/tickets" `
  -ContentType "application/json" `
  -Body '{"description":"Falha no endpoint"}'

$body = @{
  expected_revision = 0
  facts = @{
    service_id = "service-endpoint"
    asset_id = "asset-laptop-001"
    impact = "ALTO"
    urgency = "ALTA"
  }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/tickets/$($ticket.id)/triage" `
  -ContentType "application/json" `
  -Body $body
```

O corpo exige `expected_revision` não negativo e o objeto `facts`.
`service_id`, `asset_id`, `impact` e `urgency` são opcionais; `facts`
representa o snapshot completo, então campos omitidos não preservam
valores de uma avaliação anterior. A resposta `200` inclui
`ticket_id`, `status`, `facts`, `priority`, `target_team`,
`catalog_version` e `facts_revision`. Fatos incompletos ou inconsistentes
também retornam `200`, com `status` igual a `PENDENTE_INFORMACAO` e sem
prioridade ou equipe.

Os demais resultados são `404` para chamado inexistente, `422` para
caminho, corpo, enum ou referência de catálogo inválidos, `409` para
revisão desatualizada ou estado incompatível, e `503` para falha de
persistência ou ausência de catálogo ativo. A rota não exige autenticação
e deve ser usada somente no servidor local; não a exponha à rede pública.

## Interpretação local por LLM

Configure `OPENROUTER_API_KEY` e `OPENROUTER_MODEL` no arquivo `.env`.
Esses valores não devem ser incluídos na requisição. Com um chamado já
criado, solicite uma proposta sem enviar outro corpo ou uma descrição:

```powershell
$proposal = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/tickets/$($ticket.id)/interpretation"

$proposal
```

A API carrega a descrição já persistida e envia somente esse texto como dado
do chamado ao OpenRouter. O provedor não recebe o ID, outros campos do
chamado, dados do catálogo ou da KEDB. A resposta contém candidatos textuais de
serviço e ativo, impacto, urgência, sintomas, evidências, informações
ausentes, incertezas, resumo técnico e o bloco consultivo `kedb` com status e
correspondências determinísticas da base de erros conhecidos (com instruções de
contorno para avaliação do operador). Campos não determinados podem ficar
nulos.

A proposta serve para revisão; ela não é persistida, não muda o estado,
classificação, revisão ou auditoria do chamado e não calcula prioridade
nem equipe. Depois de revisar e resolver os fatos, solicite separadamente
a triagem determinística em `POST /tickets/{ticket_id}/triage`.

A rota é local e não exige autenticação. Use-a somente com o servidor
ligado a `127.0.0.1`; não a exponha à rede pública. Ela retorna `404`
para um chamado inexistente, `503` se a configuração estiver ausente ou
o provedor estiver indisponível, expirar ou limitar a chamada, e `502`
se a resposta do provedor for inválida. Não há retry automático.

## Estados do chamado

- `NOVO`
- `EM_TRIAGEM`
- `PENDENTE_INFORMACAO`
- `CLASSIFICADO`
- `ERRO_INTEGRACAO`

As transições permitidas e os fluxos de recuperação estão descritos em
[ARCHITECTURE.md](ARCHITECTURE.md).

## Estrutura de diretórios planejada

``` text
itsm-agent/
├── app/
│   ├── api/
│   ├── agent/
│   ├── orchestrator/
│   ├── tools/
│   ├── rules/
│   ├── domain/
│   ├── persistence/
│   ├── integrations/
│   ├── resilience/
│   └── audit/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── resilience/
├── migrations/
├── docs/
├── .env.example
├── .gitignore
├── Dockerfile
├── compose.yaml
└── README.md
```

A estrutura é uma referência inicial. Os diretórios podem ser ajustados
sem alterar as responsabilidades arquiteturais.

## Pré-requisitos previstos

- Docker Engine ou Docker Desktop com Docker Compose.
- Python na versão definida no ambiente do projeto, caso a execução
    local fora de containers seja necessária.
- Acesso à API OpenRouter apenas para usar a rota de interpretação.
- Arquivo de configuração local baseado em `.env.example`.

## Configuração

1. Obtenha o código do repositório.
2. Crie o arquivo `.env` a partir do modelo `.env.example`.
3. Configure a conexão com PostgreSQL para executar a API atual.
4. Inicie os serviços com Docker Compose, após a criação e validação do
    `compose.yaml`.
5. Execute as migrações do banco.
6. Carregue os dados de referência de CMDB, equipes e KEDB.
7. Execute os testes automatizados.

Os comandos exatos serão documentados quando os arquivos de execução e
migração estiverem implementados. Não mantenha credenciais reais no
repositório.

## Configurações esperadas

Configure `DATABASE_URL` com a conexão da role `itsm_runtime`. Para
interpretação, configure também `OPENROUTER_API_KEY` e
`OPENROUTER_MODEL`. Mantenha o arquivo `.env` fora do controle de versão
e não inclua esses valores em chamadas à API. Configurações de retry e
backoff serão definidas para a futura integração ITSM externa.

Para executar a API local de chamados, configure `DATABASE_URL` no
arquivo `.env` com a conexão da role `itsm_runtime`. O servidor carrega
esse arquivo e escuta em `127.0.0.1:8000` ao iniciar com
`python -m app.main`; o PostgreSQL deve estar ativo e com as migrações
aplicadas.

## Testes essenciais

- Contratos e validação da API.
- Catálogo versionado e serviço inexistente.
- Dados insuficientes e estado pendente.
- Matriz de prioridade, roteamento e reavaliação de snapshots.
- Retry idempotente, conflito de revisão e auditoria transacional.
- Propostas estruturadas, respostas inválidas do LLM e fronteiras de
  dados da interpretação.
- Timeout, HTTP 500, resposta perdida e chave de idempotência em
  integração externa (etapa futura).
- Execuções concorrentes sobre o mesmo chamado.
- Descrições de chamados como entrada não confiável para interpretação.
- Permissões de escrita e restrições da auditoria.

## Segurança

- O LLM recebe somente a descrição persistida como dado do chamado e não
  acessa diretamente o banco de dados.
- Ferramentas possuem escopo mínimo e argumentos validados.
- Conteúdo de chamados e documentos recuperados é tratado como dado
    não confiável.
- `.env` é exclusivo para desenvolvimento e deve estar no
    `.gitignore`.
- Produção deve utilizar um serviço de gerenciamento de segredos.
- A aplicação não deve registrar chaves, tokens ou dados sensíveis
    desnecessários nos logs.

## Limites da primeira versão

Esta é uma aplicação modular única, não uma plataforma de
microsserviços. Não há broker, cache distribuído, banco vetorial ou
Kubernetes. A implantação inicial é voltada ao desenvolvimento e à
demonstração controlada; a expressão "Enterprise-Ready" não deve ser
usada como garantia de certificação, alta disponibilidade ou adequação
automática a ambiente crítico.

## Próximos passos

1. Implementar consultas à KEDB.
2. Implementar integração ITSM externa com retry, timeout e idempotência.
3. Definir interfaces de complementação de chamados e experiência dos
   operadores.
