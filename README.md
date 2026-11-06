# ITSM Agent

Plataforma de Triagem Inteligente de Incidentes de TI com IA, regras
determinísticas, integração controlada e resiliência.

> **Status:** projeto em definição / implementação inicial. Este
> repositório documenta a arquitetura pretendida; comandos e
> configurações executáveis deverão ser ajustados conforme os arquivos
> reais da aplicação forem criados.

## Visão geral

O ITSM Agent automatiza etapas da triagem de incidentes. Um LLM
interpreta a descrição do chamado e extrai informações estruturadas. A
aplicação valida essas informações, consulta CMDB e KEDB, calcula
prioridade por regras determinísticas e encaminha o chamado para a
equipe configurada.

**A IA interpreta. A aplicação valida e decide conforme regras
explícitas.**

## Objetivos

- Reduzir tarefas repetitivas de triagem.
- Demonstrar integração segura entre LLM e sistemas corporativos.
- Aplicar regras de negócio determinísticas.
- Controlar estados e operações de integração.
- Demonstrar idempotência, auditoria e recuperação de falhas.
- Manter uma arquitetura simples e sustentável.

## Arquitetura resumida

``` text
Solicitante / Cliente
        |
        v
   FastAPI (API)
        |
        v
 Orquestrador Python
        |
        +----> LLM: interpretação e extração estruturada
        |
        +----> PostgreSQL: CMDB e KEDB
        |
        +----> Motor de regras: impacto, urgência e prioridade
        |
        +----> Roteamento: service_id -> target_team
        |
        v
 Integração ITSM simulada
        |
        +----> Retry / timeout / idempotência
        |
        v
 PostgreSQL: chamados, chaves idempotentes e auditoria
```

## Stack principal

- Python
- FastAPI
- Pydantic
- PostgreSQL
- LLM consumido por API
- Tenacity
- Docker e Docker Compose

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

1. Receber e persistir o chamado.
2. Alterar o estado para `EM_TRIAGEM`.
3. Solicitar ao LLM a extração estruturada de sintomas e contexto.
4. Validar a resposta e consultar CMDB/KEDB.
5. Solicitar informações adicionais quando necessário.
6. Calcular prioridade por impacto e urgência.
7. Determinar a equipe por mapeamento controlado.
8. Atualizar o chamado com idempotência.
9. Registrar eventos de auditoria e concluir a triagem.

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
- Acesso a um provedor de LLM por API.
- Arquivo de configuração local baseado em `.env.example`.

## Configuração

1. Obtenha o código do repositório.
2. Crie o arquivo `.env` a partir do modelo `.env.example`.
3. Configure a conexão com PostgreSQL e as credenciais do provedor de
    LLM.
4. Inicie os serviços com Docker Compose, após a criação e validação do
    `compose.yaml`.
5. Execute as migrações do banco.
6. Carregue os dados de referência de CMDB, equipes e KEDB.
7. Execute os testes automatizados.

Os comandos exatos serão documentados quando os arquivos de execução e
migração estiverem implementados. Não mantenha credenciais reais no
repositório.

## Configurações esperadas

Os nomes definitivos das variáveis serão estabelecidos durante a
implementação. A configuração deverá contemplar, no mínimo:

- Ambiente de execução.
- URL e credenciais do PostgreSQL.
- Endpoint, modelo e chave do provedor LLM.
- Timeout de chamadas externas.
- Limite de tentativas e parâmetros de backoff.
- Configuração de injeção de falhas, habilitada somente em ambiente de
    teste.

## Testes essenciais

- Contratos e validação da API.
- Extração estruturada e resposta inválida do LLM.
- Serviço inexistente no CMDB.
- Dados insuficientes e estado pendente.
- Cálculo de prioridade e roteamento.
- Transições válidas e inválidas.
- Timeout e HTTP 500.
- Resposta perdida após a transação ser confirmada.
- Repetição de operação com a mesma chave de idempotência.
- Execuções concorrentes sobre o mesmo chamado.
- Prompt injection em descrições e documentos recuperados.
- Permissões de escrita e restrições da auditoria.

## Segurança

- O LLM não acessa diretamente o banco de dados.
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

1. Confirmar as regras de impacto, urgência e prioridade.
2. Definir contratos REST e modelo de dados.
3. Implementar máquina de estados e persistência.
4. Implementar integração com LLM e validação estruturada.
5. Implementar idempotência e cenários de falha.
6. Automatizar testes e documentar evidências.
