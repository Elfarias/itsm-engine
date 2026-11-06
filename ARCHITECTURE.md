# ARCHITECTURE — ITSM Agent

**Versão:** 1.0
**Status:** API local de chamados, triagem determinística e interpretação local por LLM

## 1. Objetivo

Este documento descreve a arquitetura lógica e técnica da Plataforma de
Triagem Inteligente de Incidentes de TI (ITSM Agent).

A arquitetura combina interpretação probabilística por LLM com
validações e decisões determinísticas na aplicação. A implementação atual
inclui persistência de chamados, catálogos versionados, triagem
determinística e uma rota local de proposta de interpretação via
OpenRouter. A integração ITSM externa permanece fora do escopo. O desenho
prioriza simplicidade operacional, rastreabilidade e recuperação
controlada de falhas.

## 2. Princípios arquiteturais

1. Aplicação modular única; não adotar microsserviços sem necessidade
    comprovada.
2. LLM limitado à interpretação e extração de informações.
3. Regras de negócio executadas por código determinístico.
4. Banco relacional como fonte de persistência e estado.
5. A interpretação OpenRouter tem timeout finito e não repete chamadas;
   retries e idempotência aplicam-se a futuras integrações externas.
6. Auditoria separada dos dados mutáveis do chamado.
7. Segurança por validação, privilégio mínimo e ferramentas restritas.
8. Evolução incremental baseada em requisitos observáveis.

## 3. Visão lógica

``` mermaid
flowchart TD
    U[Solicitante / Cliente] --> API[FastAPI]
    API --> TICKETS[Repositório de chamados]
    TICKETS --> DB[(PostgreSQL)]
    API --> INTERPRET[Serviço de interpretação]
    INTERPRET --> CLIENT[Cliente OpenRouter]
    CLIENT --> LLM[API OpenRouter]
    API --> TRIAGE[Serviço de triagem determinística]
    TRIAGE --> RULES[Motor determinístico]
    TRIAGE --> DATA[Catálogos versionados]
    DATA --> DB
    TRIAGE --> AUDIT[Auditoria transacional]
    AUDIT --> DB
```

O endpoint `POST /tickets/{ticket_id}/interpretation` carrega a descrição
persistida e solicita uma proposta. O endpoint
`POST /tickets/{ticket_id}/triage` avalia fatos estruturados em uma
operação separada. O LLM não recebe credenciais do banco, não executa SQL
e não recebe o ID do chamado, outros campos ou dados do catálogo.

## 4. Componentes

### 4.1 API — FastAPI

Responsabilidades:

- Expor endpoints REST para criar e consultar chamados,
  `POST /tickets/{ticket_id}/interpretation` para propor fatos a partir
  da descrição salva e `POST /tickets/{ticket_id}/triage` para avaliar
  fatos estruturados separadamente.
- Restringir a API atual ao servidor local ligado a `127.0.0.1`; as rotas
  de interpretação e triagem são sem autenticação e não devem ser
  expostas à rede pública.
- Validar o corpo da avaliação: `expected_revision` não negativo e
  `facts` como snapshot completo, com `service_id`, `asset_id`, `impact`
  e `urgency` opcionais. Campos omitidos substituem valores anteriores
  por `NULL`.
- Retornar `200` para avaliações completas e pendentes; usar `404` para
  chamado inexistente, `422` para corpo, enum ou referência inválidos,
  `409` para conflito de revisão ou estado e `503` para falhas de
  persistência ou ausência de catálogo ativo.
- Para interpretação, retornar `200` com a proposta; usar `404` antes de
  chamar o provedor quando o chamado não existir, `503` para configuração
  ausente ou indisponibilidade do provedor e `502` para resposta inválida.
- Não expor operações de CRUD dos catálogos.
- Integrar futuramente as operações controladas de complementação e
  reprocessamento.
- Exigir autenticação e autorização antes de qualquer futura exposição
  além do uso local.

A API não deve concentrar regras de domínio complexas; deve delegar aos
serviços de aplicação. A rota HTTP local funciona como adaptador e delega
a avaliação ao serviço `evaluate_ticket`, que mantém as regras
determinísticas, as transições de estado e a transação de persistência e
auditoria.

### 4.2 Serviços de aplicação

A implementação atual não possui um orquestrador genérico. As rotas
delegam a operações dedicadas:

- `evaluate_ticket` aplica a triagem determinística e suas transações.
- `interpret_description` coordena o prompt e o cliente OpenRouter.

Um orquestrador mais amplo poderá ser introduzido quando houver um fluxo
que exija coordenar vários componentes. Suas responsabilidades futuras
incluem:

- Iniciar e acompanhar uma execução.
- Acionar consultas ao CMDB/KEDB.
- Invocar o motor de regras.
- Controlar transições de estado.
- Coordenar integração, retry e tratamento de falhas.
- Registrar eventos relevantes.

O fluxo futuro será explícito e limitado. Não haverá planejamento aberto
nem ciclo autônomo ilimitado do agente.

### 4.3 Interpretação local por LLM

`POST /tickets/{ticket_id}/interpretation` não recebe corpo. A rota lê a
descrição já persistida, retorna `404` se o chamado não existir e então
chama `interpret_description`. O serviço separa instruções do sistema do
texto não confiável e invoca o cliente OpenRouter de forma síncrona.

O cliente envia somente a descrição como dado do chamado. A requisição
não envia o ID do chamado, outros campos ou dados do catálogo. O schema
do provedor não contém o ID; a rota o inclui somente no envelope da
resposta local. A proposta contém campos como:

- Serviço candidato.
- Ativo candidato.
- Impacto e urgência.
- Sintomas e palavras-chave.
- Evidências de impacto e urgência.
- Informações ausentes.
- Incertezas.
- Resumo técnico.

Pydantic valida a resposta estruturada com JSON Schema estrito e validação
local do modelo. Resposta inválida retorna `502`; configuração ausente,
timeout, indisponibilidade e rate limit retornam `503`. A chamada tem
timeout de 30 segundos e não há retry automático.

A resposta do modelo é entrada não confiável. Candidatos permanecem texto:
o serviço não resolve referências de catálogo, não calcula prioridade nem
seleciona equipe. A proposta não é persistida e não altera o chamado nem
cria eventos de auditoria. A avaliação determinística continua exclusiva
de `POST /tickets/{ticket_id}/triage`.

### 4.4 CMDB e KEDB

**CMDB:** mantém serviços, ativos, criticidade, dependências e equipes
responsáveis.

**KEDB:** mantém erros conhecidos, sintomas, serviços relacionados e
procedimentos de referência.

Nesta fatia, o PostgreSQL mantém um catálogo sintético, vendor-neutral e
versionado de serviços, ativos, equipes e mapeamentos serviço-equipe. A
versão ativa é usada em novas avaliações. A KEDB não faz parte deste
escopo; pesquisa textual e PGVector permanecem fora da implementação
atual.

### 4.5 Motor de regras

Responsabilidades:

- Validar serviço e referências.
- Determinar se há dados suficientes.
- Aplicar regras de impacto e urgência.
- Calcular prioridade.
- Determinar equipe por mapeamento `service_id -> target_team`.

A matriz inicial de impacto e urgência foi aprovada como regra de
negócio:

| Impacto | Alta | Média | Baixa |
| --- | --- | --- | --- |
| Alto | P1 | P2 | P2 |
| Médio | P2 | P3 | P3 |
| Baixo | P3 | P4 | P4 |

O CMDB fornece contexto, mas criticidade do serviço não substitui a
avaliação de impacto e urgência. Se faltarem fatos obrigatórios, o serviço
persiste os fatos válidos e deixa o chamado `PENDENTE_INFORMACAO`, sem
prioridade ou equipe. Um ativo relacionado a outro serviço também deixa
o chamado pendente. Referências inexistentes são rejeitadas sem alterar
o chamado.

### 4.6 Integração ITSM simulada

A API simulada representa uma futura integração com o sistema de gestão
de chamados externo. A fatia atual não envia atualizações a um ITSM
externo nem altera o estado para `CLASSIFICADO`.

Uma implementação futura poderá injetar falhas configuráveis,
exclusivamente em ambiente de teste.

### 4.7 Persistência e auditoria

PostgreSQL armazena os dados operacionais e de controle. A auditoria
fica em tabela separada, com registros append-only para o usuário normal
da aplicação.

A avaliação bloqueia a linha do chamado, confere `facts_revision`, carrega
o catálogo ativo e grava o snapshot, o resultado e o evento de auditoria
na mesma transação. Cada snapshot alterado incrementa a revisão. A role
`itsm_runtime` só atualiza as colunas de estado e classificação
autorizadas; ela pode ler os catálogos, mas não alterá-los nem atualizar
ou excluir eventos de auditoria.

A interpretação consulta a descrição por meio do repositório, mas não
grava alterações no chamado nem eventos de auditoria.

Append-only por permissões reduz alterações acidentais ou indevidas, mas
não equivale, por si só, a imutabilidade criptográfica ou proteção
contra um administrador do banco.

## 5. Modelo de dados lógico

| Tabela | Responsabilidade |
| --- | --- |
| `tickets` | Estado atual, descrição e snapshot de classificação do chamado |
| `catalog_versions` | Versões do catálogo e indicação da versão ativa |
| `cmdb_services` | Serviços identificados por versão |
| `cmdb_assets` | Ativos e seu serviço relacionado em cada versão |
| `support_teams` | Equipes identificadas por versão |
| `service_team_mappings` | Mapeamento único de serviço para equipe em cada versão |
| `audit_events` | Eventos append-only de criação e avaliação do chamado |

### 5.1 Tickets

Campos persistidos atualmente:

- `id`
- `description`
- `status`
- `service_id`
- `asset_id`
- `impact`
- `urgency`
- `priority`
- `target_team`
- `catalog_version`
- `facts_revision`
- `created_at`

`facts_revision` começa em zero e aumenta a cada snapshot aceito que
altera a avaliação. O snapshot é completo: campos omitidos na nova
avaliação substituem valores anteriores por `NULL`. Para dados
insuficientes ou conflitantes, `priority` e `target_team` ficam nulos.
Chaves estrangeiras compostas vinculam serviço, ativo e equipe à mesma
versão do catálogo.

O catálogo inicial `catalog-v1` contém serviços sintéticos
`service-connectivity` e `service-endpoint`, equipes `team-network` e
`team-workplace`, ativos `asset-router-001` e `asset-laptop-001` e seus
mapeamentos. Novas avaliações usam a versão ativa. As versões são
mantidas no banco como registros versionados; a role runtime não tem
permissão para alterá-las.

### 5.2 Audit events

Cada evento contém:

- `id`, `ticket_id`, `event_type` e `occurred_at`.
- `details` JSONB com estados anterior e final, fatos, resultado e
  versão de catálogo usada em uma avaliação.

Avaliações aceitas que alteram o snapshot geram evento na mesma
transação da atualização do chamado. A restrição de um único tipo de
evento por chamado foi removida para permitir novas avaliações
pendentes.

Evitar armazenar segredos ou conteúdo sensível desnecessário. O usuário
de execução da aplicação não deverá ter permissões de `UPDATE` ou
`DELETE` nessa tabela.

`knowledge_base` e chaves de idempotência para integrações externas
permanecem como necessidades futuras; não são tabelas desta fatia.

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
    NOVO --> PENDENTE_INFORMACAO
    PENDENTE_INFORMACAO --> EM_TRIAGEM
    PENDENTE_INFORMACAO --> PENDENTE_INFORMACAO
    EM_TRIAGEM --> CLASSIFICADO
    EM_TRIAGEM --> ERRO_INTEGRACAO
    ERRO_INTEGRACAO --> EM_TRIAGEM
    CLASSIFICADO --> [*]
```

Regras:

- Na avaliação determinística atual, `NOVO` e
  `PENDENTE_INFORMACAO` aceitam novos snapshots. Fatos completos levam a
  `EM_TRIAGEM`; dados ausentes ou conflitantes levam a
  `PENDENTE_INFORMACAO`. A avaliação pendente pode permanecer pendente
  após receber fatos atualizados.
- A atualização do snapshot, da revisão, do estado e do evento de
  auditoria é atômica.
- Um retry idêntico em `PENDENTE_INFORMACAO`, com a mesma versão ativa,
  não duplica efeitos. Se a versão ativa mudou, uma repetição idêntica
  com a revisão atual reavalia o snapshot usando a nova versão.
- Em `EM_TRIAGEM`, somente um retry com fatos idênticos é aceito; ele
  retorna a versão previamente persistida mesmo se outro catálogo estiver
  ativo. Fatos diferentes são rejeitados.
- Concorrência usa bloqueio da linha e `expected_revision`; revisões
  desatualizadas resultam em conflito explícito, sem mesclagem.
- `ERRO_INTEGRACAO` retorna à triagem por reprocessamento autorizado.
- `CLASSIFICADO` não é reprocessado automaticamente; uma alteração
    posterior exige operação explicitamente autorizada e deverá ter
    regra própria.
- Falhas de interpretação são retornadas sem alterar o estado do chamado.
  O estado `ERRO_INTEGRACAO` permanece reservado para falhas da integração
  ITSM externa.
- Concorrência deve ser controlada para impedir que execuções
    simultâneas sobrescrevam decisões ou transições.

## 7. Fluxo principal

1. O cliente envia `POST /tickets`; a API valida e persiste o chamado em
   `NOVO`.
2. Um cliente local envia `POST /tickets/{ticket_id}/triage` com
   `expected_revision` e `facts`. O corpo representa o snapshot completo;
   campos de fato omitidos substituem valores anteriores por `NULL`.
3. A rota valida o contrato HTTP e delega ao serviço
   `evaluate_ticket`; o serviço bloqueia o chamado, verifica seu estado e
   revisão e carrega o catálogo ativo.
4. As regras validam referências e consistência do ativo, determinam se
   os fatos são suficientes e aplicam a matriz de prioridade e o
   mapeamento serviço-equipe.
5. O serviço persiste o snapshot completo, o resultado, o estado e a
   auditoria em uma transação.
6. Uma avaliação completa deixa o chamado em `EM_TRIAGEM`. Fatos
   incompletos ou conflitantes válidos deixam-no em
   `PENDENTE_INFORMACAO`, sem prioridade ou equipe.
7. Uma repetição pendente idêntica com o mesmo catálogo não duplica
   efeitos; com uma nova versão ativa e a revisão atual, reavalia o
   snapshot. Uma repetição idêntica em `EM_TRIAGEM` retorna o resultado e
   a versão persistidos, mesmo após mudança do catálogo ativo.

A interpretação é uma operação separada do fluxo acima. O cliente local
envia `POST /tickets/{ticket_id}/interpretation` sem corpo; a API carrega a
descrição persistida e solicita uma proposta ao OpenRouter. A proposta
retorna ao cliente sem alterar o chamado, sua revisão, classificação ou
auditoria. Após revisar e resolver os fatos, o cliente pode chamar a rota
de triagem determinística.

Consultas à KEDB e atualização de um ITSM externo ainda não fazem parte
da implementação atual.

## 8. Resiliência e idempotência

### 8.1 Interpretação via OpenRouter

- Usar timeout de 30 segundos.
- Não há retry automático.
- Retornar `503` para configuração ausente, timeout, indisponibilidade ou
  rate limit; o cliente pode solicitar nova tentativa manualmente.
- Retornar `502` quando a resposta não puder ser interpretada ou validada.

### 8.2 Timeout e retry de integração externa (futura)

- Definir timeout por chamada externa.
- Repetir somente erros transitórios.
- Limitar o número de tentativas.
- Aplicar exponential backoff.
- Não repetir automaticamente erros permanentes de validação ou
    autorização.
- Registrar cada tentativa e o resultado final.

Tenacity poderá implementar a política de retry da integração externa,
mas não substitui a lógica de idempotência.

### 8.3 Chave para idempotência de integração externa (futura)

Uma futura integração ITSM poderá usar uma chave estável, por exemplo
`ticket-1234-classification-v1`.

A mesma operação lógica reutilizará a chave em todas as tentativas. A
API simulada futura persistirá a chave e o resultado. Uma resposta
perdida após o processamento não deverá causar uma segunda execução
lógica.

O sistema tratará também resultados desconhecidos: consultará ou
reconciliará o estado remoto antes de iniciar uma nova operação lógica.

### 8.4 Idempotência de avaliações internas

Uma avaliação repetida de ticket pendente com os mesmos fatos e a mesma
versão ativa retorna o resultado persistido sem incrementar a revisão ou
duplicar a auditoria. Se a versão ativa mudou, uma repetição com a revisão
atual avalia o snapshot na nova versão. Em `EM_TRIAGEM`, somente um retry
com fatos idênticos é aceito; ele retorna o resultado e a versão salvos,
independentemente do catálogo ativo, sem efeitos duplicados.

### 8.5 Recuperação futura de integração externa

Após esgotar as tentativas de uma integração externa:

- Registrar o erro e contexto de correlação.
- Preservar os dados já obtidos.
- Marcar `ERRO_INTEGRACAO` quando a falha externa impedir a conclusão.
- Permitir reprocessamento controlado.
- Reutilizar a chave da operação original quando se tratar de retry da
    mesma operação; gerar nova chave apenas para uma nova operação
    lógica.

## 9. Segurança

### 9.1 Prompt injection na interpretação LLM

Descrições de chamados são dados não confiáveis. O serviço de
interpretação os envia como mensagem de usuário separada das instruções
do sistema e orienta o modelo a não seguir comandos embutidos no texto.

Aplicar os seguintes controles:

- Separar instruções do sistema dos dados fornecidos pelo usuário.
- Instruir o modelo a tratar o conteúdo recebido como informação, não
  como comandos.
- Enviar somente a descrição como dado do chamado, sem ID ou catálogo.
- Não conceder acesso direto ao banco ou credenciais ao LLM.
- Validar a saída com JSON Schema e Pydantic.
- Não permitir que a proposta altere dados ou acione triagem.

Sanitização de texto pode ser útil para validação de entrada, mas não é
defesa suficiente contra prompt injection.

### 9.2 Credenciais e segredos

- Desenvolvimento: variáveis de ambiente e `.env` excluído do controle
    de versão.
- Produção: serviço gerenciado de segredos da plataforma de nuvem.
- Utilizar credenciais de privilégio mínimo e evitar registrar tokens
    em logs.

### 9.3 API

A API atual é de desenvolvimento local, sem autenticação, e o servidor
escuta em `127.0.0.1`. Não exponha os endpoints à rede pública. Qualquer
acesso remoto futuro exige definir autenticação, autorização, TLS e
limites de requisição antes da exposição.

## 10. Testes de confiabilidade

Cenários mínimos:

| Cenário | Resultado esperado |
| --- | --- |
| Fatos obrigatórios ausentes | `PENDENTE_INFORMACAO`, sem prioridade ou equipe |
| Serviço ou ativo inexistente | Rejeição sem alterar o chamado |
| Ativo relacionado a outro serviço | `PENDENTE_INFORMACAO`, sem prioridade ou equipe |
| Retry pendente idêntico, mesma versão | Mesmo resultado, sem revisão ou auditoria duplicada |
| Retry em `EM_TRIAGEM` após ativar catálogo mais novo | Resultado e versão persistidos retornados |
| Snapshots concorrentes com a mesma revisão | No máximo uma atualização; a outra recebe conflito |
| Falha ao inserir evento de auditoria | Rollback da atualização e do evento |
| Resposta OpenRouter completa ou parcial válida | Proposta estruturada, sem mutação ou auditoria |
| Descrição com instruções maliciosas | Texto tratado como dado não confiável |
| Timeout, rate limit ou indisponibilidade OpenRouter | `503`, sem retry automático |
| Resposta OpenRouter inválida | `502`, sem mutação |
| Timeout ou resposta perdida em integração externa futura | Retry/reconciliação com chave estável |

## 11. Implantação

Ambiente inicial:

- Um container para a aplicação FastAPI.
- Um container para PostgreSQL.
- A interpretação consome OpenRouter por API externa síncrona, com
  `OPENROUTER_API_KEY` e `OPENROUTER_MODEL` configurados localmente.
- Docker Compose para desenvolvimento local.

A implantação futura poderá utilizar serviço gerenciado de containers,
como AWS ECS ou Azure Container Apps. A escolha da nuvem e os requisitos
de produção ainda precisam ser confirmados.

Kubernetes, mensageria e alta disponibilidade distribuída estão fora do
escopo inicial.

## 12. Riscos e decisões pendentes

- Definir autenticação e autorização caso a API venha a ser exposta além
  do loopback.
- Definir retenção e acesso aos eventos de auditoria.
- Especificar o contrato de idempotência e o comportamento para
    payload divergente.
- Definir como o solicitante fornece informações complementares.
- Definir o mecanismo de reprocessamento autorizado.

## 13. Critério de evolução

Adicionar um componente ou tecnologia somente quando houver requisito
demonstrável que a arquitetura atual não atenda. A decisão deve
considerar benefício funcional, custo, operação, segurança e manutenção.
