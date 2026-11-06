# ARCHITECTURE — ITSM Agent

**Versão:** 1.0
**Status:** Baseline arquitetural para a primeira versão

## 1. Objetivo

Este documento descreve a arquitetura lógica e técnica da Plataforma de
Triagem Inteligente de Incidentes de TI (ITSM Agent).

A solução combina interpretação probabilística por LLM com validações e
decisões determinísticas na aplicação. O desenho prioriza simplicidade
operacional, rastreabilidade e recuperação controlada de falhas.

## 2. Princípios arquiteturais

1. Aplicação modular única; não adotar microsserviços sem necessidade
    comprovada.
2. LLM limitado à interpretação e extração de informações.
3. Regras de negócio executadas por código determinístico.
4. Banco relacional como fonte de persistência e estado.
5. Operações externas com timeout, retry limitado e idempotência.
6. Auditoria separada dos dados mutáveis do chamado.
7. Segurança por validação, privilégio mínimo e ferramentas restritas.
8. Evolução incremental baseada em requisitos observáveis.

## 3. Visão lógica

``` mermaid
flowchart TD
    U[Solicitante / Cliente] --> API[FastAPI]
    API --> ORQ[Orquestrador Python]
    ORQ --> LLM[LLM via API]
    ORQ --> DATA[Camada de acesso a dados]
    DATA --> DB[(PostgreSQL)]
    ORQ --> RULES[Motor determinístico]
    RULES --> ORQ
    ORQ --> ITSM[API ITSM simulada]
    ITSM --> DB
    ORQ --> AUDIT[Serviço de auditoria]
    AUDIT --> DB
```

O LLM é um serviço externo consumido pela aplicação. Ele não recebe
credenciais do banco e não executa SQL nem chamadas arbitrárias.

## 4. Componentes

### 4.1 API — FastAPI

Responsabilidades:

- Expor endpoints REST.
- Validar contratos de entrada e saída.
- Criar e consultar chamados.
- Acionar o fluxo de triagem.
- Expor operações controladas de complementação e reprocessamento.
- Aplicar autenticação e autorização quando o ambiente exigir acesso
    além do uso local.

A API não deve concentrar regras de domínio complexas; deve delegar ao
orquestrador e aos serviços internos.

### 4.2 Orquestrador

Coordena o fluxo de triagem e controla a sequência de execução.

Responsabilidades:

- Iniciar e acompanhar uma execução.
- Solicitar interpretação ao LLM.
- Acionar consultas ao CMDB/KEDB.
- Invocar o motor de regras.
- Controlar transições de estado.
- Coordenar integração, retry e tratamento de falhas.
- Registrar eventos relevantes.

O fluxo é explícito e limitado. Não haverá planejamento aberto nem ciclo
autônomo ilimitado do agente.

### 4.3 Integração com LLM

O LLM interpreta texto livre e retorna dados estruturados, como:

- Serviço candidato.
- Sintomas e palavras-chave.
- Evidências relatadas de impacto.
- Evidências relatadas de urgência.
- Informações ausentes.
- Resumo técnico.

A resposta do modelo é considerada entrada não confiável. Pydantic
valida estrutura, tipos, limites e valores permitidos; validações de
domínio verificam se as referências realmente existem.

O modelo não define sozinho a prioridade final nem o time de destino.

### 4.4 CMDB e KEDB

**CMDB:** mantém serviços, ativos, criticidade, dependências e equipes
responsáveis.

**KEDB:** mantém erros conhecidos, sintomas, serviços relacionados e
procedimentos de referência.

A primeira versão utiliza consultas relacionais e pesquisa textual do
PostgreSQL. PGVector fica fora do escopo inicial.

### 4.5 Motor de regras

Responsabilidades:

- Validar serviço e referências.
- Determinar se há dados suficientes.
- Aplicar regras de impacto e urgência.
- Calcular prioridade.
- Determinar equipe por mapeamento `service_id -> target_team`.

A matriz inicial é ilustrativa e precisa ser confirmada como regra de
negócio:

  Impacto  Urgência     Alta   Média   Baixa
  ------------------- ------ ------- -------
  Alto                    P1      P2      P2
  Médio                   P2      P3      P3
  Baixo                   P3      P4      P4

O CMDB fornece contexto, mas criticidade do serviço não substitui a
avaliação de impacto e urgência. Se não houver evidência suficiente, a
aplicação solicita informação ou encaminha para revisão, em vez de
inventar uma classificação.

### 4.6 Integração ITSM simulada

A API simulada representa o sistema de gestão de chamados externo. Ela
deverá permitir atualização controlada de classificação, prioridade,
equipe e estado.

A simulação também poderá injetar falhas configuráveis, exclusivamente
em ambiente de teste.

### 4.7 Persistência e auditoria

PostgreSQL armazena os dados operacionais e de controle. A auditoria
fica em tabela separada, com registros append-only para o usuário normal
da aplicação.

Append-only por permissões reduz alterações acidentais ou indevidas, mas
não equivale, por si só, a imutabilidade criptográfica ou proteção
contra um administrador do banco.

## 5. Modelo de dados lógico

Tabelas previstas:

  Tabela               Responsabilidade
  -------------------- -----------------------------------------------
  `tickets`            Estado atual e dados do chamado
  `cmdb_services`      Catálogo de serviços e atributos de negócio
  `cmdb_assets`        Ativos e dependências
  `knowledge_base`     Erros conhecidos e procedimentos
  `audit_events`       Eventos de execução, decisão e transição
  `idempotency_keys`   Chaves e resultados de operações idempotentes

### 5.1 Tickets

Campos centrais previstos:

- `id`
- `raw_description`
- `status`
- `service_id`
- `category`
- `impact`
- `urgency`
- `priority`
- `target_team`
- `created_at`
- `updated_at`

Campos adicionais poderão ser definidos durante a modelagem, desde que
tenham finalidade clara.

### 5.2 Audit events

Cada evento deverá conter, no mínimo:

- Identificador do evento.
- Identificador do chamado.
- Tipo do evento.
- Estado anterior e posterior, quando aplicável.
- Identificador da execução/correlação.
- Data e hora.
- Resultado e metadados necessários para rastreabilidade.

Evitar armazenar segredos ou conteúdo sensível desnecessário. O usuário
de execução da aplicação não deverá ter permissões de `UPDATE` ou
`DELETE` nessa tabela.

### 5.3 Idempotency keys

A tabela deverá registrar a chave, o escopo da operação, o estado de
processamento e o resultado necessário para responder a repetições.

A chave deve identificar uma operação lógica estável, não uma tentativa
individual. Requisições repetidas com a mesma chave e o mesmo conteúdo
lógico devem recuperar o resultado anterior. Reutilização da mesma chave
para conteúdo incompatível deve ser rejeitada.

A reserva da chave, a alteração do chamado e o armazenamento do
resultado devem ser coordenados transacionalmente quando pertencem ao
mesmo banco. Se a operação envolver um sistema realmente externo, a
estratégia deverá considerar o limite da transação e incluir
reconciliação do resultado incerto.

## 6. Máquina de estados

Estados oficiais:

- `NOVO`
- `EM_TRIAGEM`
- `PENDENTE_INFORMACAO`
- `CLASSIFICADO`
- `ERRO_INTEGRACAO`

Transições permitidas:

``` mermaid
stateDiagram-v2
    [*] --> NOVO
    NOVO --> EM_TRIAGEM
    EM_TRIAGEM --> PENDENTE_INFORMACAO
    PENDENTE_INFORMACAO --> EM_TRIAGEM
    EM_TRIAGEM --> CLASSIFICADO
    EM_TRIAGEM --> ERRO_INTEGRACAO
    ERRO_INTEGRACAO --> EM_TRIAGEM
    CLASSIFICADO --> [*]
```

Regras:

- Transições são validadas na camada de domínio.
- Atualização de estado e evento de auditoria devem ser gravados de
    forma consistente.
- `PENDENTE_INFORMACAO` só retorna à triagem após recebimento de
    informação complementar.
- `ERRO_INTEGRACAO` retorna à triagem por reprocessamento autorizado.
- `CLASSIFICADO` não é reprocessado automaticamente; uma alteração
    posterior exige operação explicitamente autorizada e deverá ter
    regra própria.
- Falhas de interpretação/processamento devem ser distinguidas de
    falhas de integração externa. O estado `ERRO_INTEGRACAO` deve ser
    usado apenas para falha de integração; outros erros precisam de
    tratamento e registro próprios.
- Concorrência deve ser controlada para impedir que execuções
    simultâneas sobrescrevam decisões ou transições.

## 7. Fluxo principal

1. Cliente envia `POST /tickets`.
2. API valida a requisição e persiste o chamado como `NOVO`.
3. Orquestrador inicia execução e registra `EM_TRIAGEM`.
4. LLM retorna extração estruturada.
5. Aplicação valida a resposta e consulta CMDB/KEDB.
6. Motor de regras verifica suficiência dos dados.
7. Se faltarem dados essenciais, registra `PENDENTE_INFORMACAO` e
    solicita complementação pelo canal disponível.
8. Caso contrário, calcula impacto, urgência e prioridade e determina a
    equipe.
9. Integração envia atualização usando chave idempotente estável.
10. A aplicação confirma o resultado e registra auditoria.
11. Chamado passa para `CLASSIFICADO`.

## 8. Resiliência e idempotência

### 8.1 Timeout e retry

- Definir timeout por chamada externa.
- Repetir somente erros transitórios.
- Limitar o número de tentativas.
- Aplicar exponential backoff.
- Não repetir automaticamente erros permanentes de validação ou
    autorização.
- Registrar cada tentativa e o resultado final.

Tenacity poderá implementar a política de retry, mas não substitui a
lógica de idempotência.

### 8.2 Chave de idempotência

Exemplo conceitual: `ticket-1234-classification-v1`.

A mesma operação lógica reutiliza a mesma chave em todas as tentativas.
A API simulada persiste chave e resultado. Uma resposta perdida após o
processamento não deve causar uma segunda execução lógica.

O sistema também deve tratar a situação em que o resultado da operação é
desconhecido: consultar/reconciliar o estado remoto antes de iniciar uma
nova operação lógica.

### 8.3 Recuperação

Após esgotar as tentativas:

- Registrar o erro e contexto de correlação.
- Preservar os dados já obtidos.
- Marcar `ERRO_INTEGRACAO` quando a falha externa impedir a conclusão.
- Permitir reprocessamento controlado.
- Reutilizar a chave da operação original quando se tratar de retry da
    mesma operação; gerar nova chave apenas para uma nova operação
    lógica.

## 9. Segurança

### 9.1 Prompt injection

Descrições, anexos e documentos recuperados são dados não confiáveis.

Controles:

- Separar instruções do sistema dos dados fornecidos pelo usuário.
- Instruir o modelo a tratar o conteúdo recebido como informação, não
    como comandos.
- Limitar o conjunto de ferramentas e seus parâmetros.
- Não conceder acesso direto ao banco ou credenciais ao LLM.
- Validar toda operação na aplicação, independentemente da resposta do
    modelo.
- Exigir autorização da aplicação para ações que alterem dados.

Sanitização de texto pode ser útil para validação de entrada, mas não é
defesa suficiente contra prompt injection.

### 9.2 Credenciais e segredos

- Desenvolvimento: variáveis de ambiente e `.env` excluído do controle
    de versão.
- Produção: serviço gerenciado de segredos da plataforma de nuvem.
- Utilizar credenciais de privilégio mínimo e evitar registrar tokens
    em logs.

### 9.3 API

Autenticação, autorização, TLS, limites de requisição e exposição de
endpoints deverão ser definidos de acordo com o ambiente de implantação.
A API simulada não deve ser exposta publicamente sem controles
adequados.

## 10. Testes de confiabilidade

Cenários mínimos:

  -----------------------------------------------------------------------
  Cenário                             Resultado esperado
  ----------------------------------- -----------------------------------
  HTTP 500 transitório                Retry limitado

  Timeout antes do processamento      Retry conforme política

  Resposta perdida após commit        Mesma chave retorna resultado
                                      anterior

  Mesma chave com payload diferente   Rejeição

  Serviço inexistente                 Não classificar/rotear como se
                                      fosse válido

  Dados insuficientes                 `PENDENTE_INFORMACAO`

  Parâmetro fora do schema            Rejeição na validação

  Prompt injection                    Conteúdo tratado como dado não
                                      confiável

  Duas execuções simultâneas          Sem sobrescrita ou transição
                                      inconsistente

  Falha persistente de integração     `ERRO_INTEGRACAO` e possibilidade
                                      de reprocessar
  -----------------------------------------------------------------------

## 11. Implantação

Ambiente inicial:

- Um container para a aplicação FastAPI.
- Um container para PostgreSQL.
- LLM consumido por API externa.
- Docker Compose para desenvolvimento local.

A implantação futura poderá utilizar serviço gerenciado de containers,
como AWS ECS ou Azure Container Apps. A escolha da nuvem e os requisitos
de produção ainda precisam ser confirmados.

Kubernetes, mensageria e alta disponibilidade distribuída estão fora do
escopo inicial.

## 12. Riscos e decisões pendentes

- Definir como impacto e urgência serão obtidos e validados.
- Validar a matriz de prioridade com regras de negócio.
- Definir provedor e modelo LLM.
- Definir autenticação e autorização da API.
- Definir retenção e acesso aos eventos de auditoria.
- Especificar o contrato de idempotência e o comportamento para
    payload divergente.
- Definir como o solicitante fornece informações complementares.
- Definir o mecanismo de reprocessamento autorizado.

## 13. Critério de evolução

Adicionar um componente ou tecnologia somente quando houver requisito
demonstrável que a arquitetura atual não atenda. A decisão deve
considerar benefício funcional, custo, operação, segurança e manutenção.
