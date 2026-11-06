# Ticket Triage Design

**Spec**: `.specs/features/ticket-triage/spec.md`
**Status**: Approved
**Approved**: 2026-11-06 - user: "Aprovar o Design"

---

## Architecture Overview

O usuário escolheu catálogos versionados no PostgreSQL (`postgres_versioned`). Um novo módulo interno de triagem lê uma versão imutável do catálogo, avalia os fatos com regras determinísticas puras e grava o snapshot completo, o resultado e o evento de auditoria em uma transação PostgreSQL. Não serão adicionados endpoint público de classificação nem integração externa.

```mermaid
sequenceDiagram
    participant Caller as Chamador interno
    participant Service as Serviço de triagem
    participant Rules as Regras determinísticas
    participant DB as PostgreSQL
    Caller->>Service: ticket_id, fatos completos, expected_revision
    Service->>DB: Iniciar transação; bloquear ticket; ler revisão/estado
    DB-->>Service: Snapshot do ticket e revisão
    Service->>DB: Ler versão ativa do catálogo e referências
    DB-->>Service: Serviços, ativos e mapeamentos versionados
    Service->>Rules: Avaliar fatos usando o catálogo
    Rules-->>Service: Decisão pendente ou completa
    Service->>DB: Gravar snapshot, resultado, revisão e auditoria
    DB-->>Service: Commit
    Service-->>Caller: Resultado com estado e versão do catálogo
```

Uma nova avaliação de ticket pendente usa a versão ativa do catálogo. Um ticket em `EM_TRIAGEM` é imutável, exceto por retry idêntico, que retorna o resultado e a versão já persistidos mesmo que exista um catálogo mais novo. O chamador informa a revisão que leu; uma revisão desatualizada é rejeitada, sem mesclagem.

### Architecture Alternatives

| Abordagem | Vantagens | Trade-offs | Resultado |
| --- | --- | --- | --- |
| Tabelas PostgreSQL versionadas, carregadas por migrações | Integridade referencial no banco; catálogo, ticket e auditoria compartilham a transação e a fonte de persistência do projeto. | Requer tabelas, migrações e privilégios de leitura/atualização cuidadosamente limitados. | **Escolhida pelo usuário** (`postgres_versioned`). |
| Arquivos JSON versionados empacotados com o código | Atualização simples junto com uma versão da aplicação; não requer tabelas de catálogo. | Relações são verificadas somente em Python; o catálogo e o estado persistido ficam em fontes diferentes. | Não escolhida. |

---

## Code Reuse Analysis

### Existing Components to Leverage

| Component | Location | How to Use |
| --- | --- | --- |
| Ticket lifecycle enum | `app/tickets/schemas.py` | Reutilizar `TicketStatus`, sem criar uma segunda nomenclatura de estados. |
| PostgreSQL transaction pattern | `app/tickets/repository.py` | Manter os context managers de conexão psycopg para que exceções revertam a transação. |
| Append-only audit table and runtime role | `migrations/001_tickets_and_audit.sql` | Estender os metadados de auditoria e preservar a proibição de atualizar ou excluir eventos pela role runtime. |
| PostgreSQL integration-test fixture | `tests/integration/conftest.py` | Aplicar todas as migrações SQL em ordem estável, em vez de somente a migração 001. |
| Pytest configuration | `pyproject.toml` | Adicionar testes unitários e de integração PostgreSQL à suíte existente. |

### Integration Points

| System | Integration Method |
| --- | --- |
| Ticket API | Nenhuma rota ou resposta pública será alterada; a criação atual de tickets permanece como entrada. |
| PostgreSQL | Adicionar tabelas de catálogo versionadas, campos de classificação anuláveis e revisão em `tickets`; persistir detalhes de auditoria na tabela existente. |
| Classification rules | Chamadas por um serviço Python interno, sem LLM, KEDB ou ITSM externo. |

---

## Components

### Triage Domain Types

- **Purpose**: Definir snapshots validados de fatos, valores de impacto/urgência/prioridade, resultados de avaliação e erros de domínio explícitos.
- **Location**: `app/triage/schemas.py`
- **Interfaces**:
  - `TriageFacts(service_id, asset_id, impact, urgency)` - snapshot completo enviado para uma avaliação; fatos opcionais ausentes permanecem `None`.
  - `TriageResult(ticket_id, status, facts, priority, target_team, catalog_version, facts_revision)` - resultado confirmado no banco.
- **Dependencies**: `TicketStatus` existente em `app/tickets/schemas.py`.
- **Reuses**: Pydantic e os padrões de enum já usados nos schemas de tickets.

### Deterministic Rules

- **Purpose**: Calcular prioridade a partir de impacto e urgência e decidir se os fatos válidos bastam para classificar.
- **Location**: `app/triage/rules.py`
- **Interfaces**:
  - `calculate_priority(impact, urgency) -> Priority` - implementa as nove combinações de TRI-03.
  - `evaluate_facts(facts, catalog) -> EvaluationDecision` - valida serviço/equipe e, se informado, a relação ativo/serviço; retorna resultado completo ou pendente.
- **Dependencies**: Valores de domínio tipados e registros de catálogo carregados pelo repositório.
- **Reuses**: Não há código de classificação existente; as regras permanecem em Python puro para que testes unitários cubram cada resultado sem PostgreSQL.

### Catalog and Ticket Repository

- **Purpose**: Carregar uma versão ativa do catálogo e disponibilizar operações de persistência de ticket e auditoria usando uma conexão fornecida pelo chamador.
- **Location**: `app/triage/repository.py`
- **Interfaces**:
  - `lock_ticket(connection, ticket_id) -> TicketSnapshot | None` - seleciona o ticket e sua revisão com `FOR UPDATE`.
  - `load_active_catalog(connection) -> CatalogSnapshot` - retorna serviços, ativos, mapeamentos e versão ativa.
  - `save_evaluation(connection, ticket_id, decision, next_revision) -> None` - persiste o snapshot completo e o resultado.
  - `append_evaluation_event(connection, ticket_id, previous_status, decision) -> None` - insere evento append-only de auditoria com estados anterior e final.
- **Dependencies**: psycopg e o schema PostgreSQL definido pelas migrações.
- **Reuses**: Acesso a linhas psycopg e convenções de transação existentes em `app/tickets/repository.py`.

### Triage Service

- **Purpose**: Coordenar validação do estado, concorrência otimista, avaliação das regras e persistência em uma transação.
- **Location**: `app/triage/service.py`
- **Interfaces**:
  - `evaluate_ticket(connection_string, ticket_id, facts, expected_revision) -> TriageResult` - avalia um snapshot completo e só retorna após o commit.
- **Dependencies**: `app/triage/repository.py`, `app/triage/rules.py` e psycopg.
- **Reuses**: Estilo síncrono do serviço e context managers de conexão psycopg da aplicação atual.

### Versioned Catalog Schema and Seed

- **Purpose**: Armazenar versões imutáveis dos catálogos, com serviços, ativos, equipes de suporte e mapeamentos de serviço para equipe.
- **Location**: `migrations/002_ticket_triage_catalogs.sql`
- **Interfaces**: Tabelas SQL, restrições e uma versão inicial sintética inserida pela migração.
- **Dependencies**: Tabelas `tickets`, `audit_events` existentes e a role de banco `itsm_runtime`.
- **Reuses**: Migração existente e padrão de privilégio mínimo de `migrations/001_tickets_and_audit.sql`.

---

## Data Models

### Catalog Version

`catalog_versions(version_id, is_active, created_at)` identifica cada versão imutável do catálogo. Um índice único parcial permite no máximo uma versão ativa; a migração de seed cria a primeira versão ativa. Se não houver versão ativa, o serviço falha explicitamente em vez de selecionar uma alternativa silenciosa.

### Catalog Records

- `cmdb_services(version_id, service_id, name)`
- `support_teams(version_id, team_id, name)`
- `service_team_mappings(version_id, service_id, team_id)`
- `cmdb_assets(version_id, asset_id, service_id)`

As chaves primárias e estrangeiras compostas incluem `version_id` e impedem referências entre versões diferentes. A role runtime não recebe privilégios de CRUD e não são criados endpoints administrativos.

### Ticket Classification Snapshot

Adicionar a `tickets` os campos anuláveis `service_id`, `asset_id`, `impact`, `urgency`, `priority`, `target_team` e `catalog_version`, além de `facts_revision`, inicializado em zero. Chaves estrangeiras compostas validam as referências do catálogo. Uma avaliação aceita substitui o snapshot completo, inclusive limpando valores omitidos no snapshot novo. Fatos incompletos ou conflitantes deixam `priority` e `target_team` nulos.

O serviço incrementa `facts_revision` a cada snapshot alterado e aceito. Com o bloqueio da linha do ticket, compara `expected_revision` informado pelo chamador; apenas uma atualização concorrente baseada na mesma revisão pode ser confirmada.

Tickets em `NOVO` e `PENDENTE_INFORMACAO` podem iniciar uma avaliação. O fluxo valida as transições permitidas pela máquina de estados existente antes de persistir o estado final: `EM_TRIAGEM` para classificação completa ou `PENDENTE_INFORMACAO` para dados insuficientes/conflitantes. Em `EM_TRIAGEM`, somente retry com snapshot idêntico é aceito. `CLASSIFICADO` e `ERRO_INTEGRACAO` não são reprocessados por este serviço.

### Audit Event Details

Adicionar à `audit_events` um campo JSONB para os estados anterior e final, fatos classificados, resultado e versão do catálogo. Remover a restrição de unicidade existente em `(ticket_id, event_type)` para permitir que avaliações futuras e válidas de um ticket pendente gerem eventos. Preservar as permissões append-only.

---

## Error Handling Strategy

| Error Scenario | Handling | User Impact |
| --- | --- | --- |
| Fatos obrigatórios ausentes, serviço sem equipe mapeada ou ativo conflitante | Persistir o snapshot válido completo como `PENDENTE_INFORMACAO`; manter prioridade e equipe nulas. | O chamador interno recebe resultado pendente e pode solicitar informação adicional. |
| Identificador desconhecido no catálogo ou impacto/urgência inválidos | Lançar erro tipado de entrada/domínio antes de qualquer gravação. | O chamador recebe falha explícita de entrada inválida; o ticket não muda. |
| Revisão do ticket desatualizada | Lançar conflito tipado com a revisão atual e reverter a transação. | O chamador concorrente precisa reler o ticket e tentar novamente de forma deliberada. |
| Ticket em `EM_TRIAGEM` recebe fatos diferentes | Rejeitar e preservar a classificação persistida. | Não ocorre reclassificação silenciosa. |
| Ticket em estado não tratado pelo serviço (`CLASSIFICADO` ou `ERRO_INTEGRACAO`) | Rejeitar sem persistir alterações. | Estados de conclusão ou integração não são reprocessados nesta fatia. |
| Não há versão ativa ou o catálogo está inconsistente | Lançar erro explícito de configuração; não adivinhar versão nem mapeamento. | O chamador recebe falha para diagnóstico operacional. |
| Falha no banco ou na inserção de auditoria | Reverter gravações de ticket e auditoria na transação; propagar erro explícito de persistência. | Não há sucesso parcial. |

---

## Risks & Concerns

| Concern | Location (file:line) | Impact | Mitigation |
| --- | --- | --- | --- |
| A role runtime atualmente não pode atualizar linhas de ticket. | `migrations/001_tickets_and_audit.sql:38` | A persistência da classificação falharia ou exigiria privilégio excessivo. | Conceder `UPDATE` somente nas colunas de classificação e estado; testar que descrição e auditoria continuam protegidas. |
| A tabela de auditoria atualmente permite só um evento de cada tipo por ticket. | `migrations/001_tickets_and_audit.sql:34` | Um ticket pendente não poderia registrar várias avaliações aceitas com o mesmo tipo de evento. | Remover a restrição na nova migração, preservar permissões append-only e testar múltiplos eventos. |
| Testes de integração aplicam somente a migração 001. | `tests/integration/conftest.py:15` | O novo schema e as permissões poderiam ficar sem teste. | Atualizar o fixture para aplicar todas as migrações em ordem lexical estável e confirmar que o catálogo seed está utilizável. |
| O repositório atual de tickets tem modelo restrito e não possui serviço de classificação. | `app/tickets/repository.py:8` | Concentrar regras e transação no código da API de tickets acoplaria o novo domínio ao HTTP. | Adicionar o módulo interno `app/triage` e manter rotas e respostas públicas inalteradas. |

---

## Tech Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Catalog storage | Tabelas PostgreSQL versionadas e imutáveis, seed por migração SQL; usuário selecionou `postgres_versioned`. | Segue a fonte relacional de verdade do projeto e permite impor chaves estrangeiras. |
| Catalog version policy | Nova avaliação de ticket pendente usa a versão ativa; retry idêntico de ticket em `EM_TRIAGEM` retorna resultado e versão persistidos. | Aplica correções de catálogo a tickets pendentes sem alterar silenciosamente uma decisão concluída. |
| Rule placement | Regras puras em `app/triage/rules.py`; orquestração transacional em `app/triage/service.py`. | Mantém cada regra testável sem API ou banco de dados. |
| Concurrency | Bloqueio de linha com `expected_revision` informado pelo chamador; snapshots desatualizados falham explicitamente. | Implementa a decisão do usuário de rejeitar conflitos sem mesclar fatos. |
| Persistence | Snapshot, estado, revisão e auditoria do ticket confirmados na mesma transação. | Evita classificação parcial e segue o padrão de atomicidade de auditoria existente. |
| Runtime privilege | Atualização de ticket por coluna; leitura de catálogo; somente inserção de auditoria. | Habilita a funcionalidade sem conceder mutação ampla de tickets nem alteração da auditoria. |

> **Project-level decisions:** Nenhuma decisão foi adicionada. As escolhas acima implementam o escopo aprovado desta funcionalidade e não estabelecem uma nova convenção entre funcionalidades.

---
