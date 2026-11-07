# Tarefas da Consulta à KEDB (Known Error Database)

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, the walk, check_proofs, the Verifier and the screens sub-agent).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/kedb-lookup/design.md`
**Status**: Approved
**Approved**: 2026-11-06 - user: "sim"
**Build**: none - no separate build, type-check, or lint command is configured; `pytest -v` is the project validation command.
**Run tests**: `pytest -v`

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| KEDB schemas | unit | Validação estrita de tipos, campos imutáveis, status enum | `tests/unit/test_kedb_schemas.py` | `pytest -v` |
| Text normalization | unit | Remoção de acentos, limpeza de espaços, minúsculas, valores nulos/vazios | `tests/unit/test_kedb_normalization.py` | `pytest -v` |
| KEDB repository | integration | Queries reais no PostgreSQL, busca por serviço, fallback por sintomas, ordenação | `tests/integration/test_kedb_repository.py` | `pytest -v` |
| KEDB service | unit | Captura de falhas de banco com status UNAVAILABLE, montagem de resultado | `tests/unit/test_kedb_service.py` | `pytest -v` |
| Interpretation endpoint | integration | Resposta enriquecida com KEDB, fallback de banco (200 OK parcial), não-mutação de dados | `tests/integration/test_ticket_interpretation_api.py` | `pytest -v` |
| Documentation & Progress | unit | Atualização de documentação arquitetural e registro no dashboard do projeto | `tests/unit/test_interpretation_docs.py`, `tests/unit/test_project_progress.py` | `pytest -v` |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Após tarefas apenas com testes unitários | `pytest -v tests/unit` |
| Full | Após tarefas com testes de integração e banco | `pytest -v` |
| Build | Tarefas de documentação ou configuração | `pytest -v` |

---

## Execution Plan

Phases run sequentially; tasks within each phase execute in order.

### Phase 1: Esquemas e Normalizacao

```text
T1 → T2
```

### Phase 2: Persistencia e Repositorio KEDB

```text
T3 → T4
```

### Phase 3: Servico e Rota Local

```text
T5 → T6
```

### Phase 4: Documentacao e Rastreamento

```text
T7 → T8
```

---

## Task Breakdown

### Phase 1: Esquemas e Normalizacao

#### T1: Definir esquemas Pydantic da KEDB e atualizar resposta de interpretacao

**Where**: `app/triage/kedb_schemas.py`
**Depends on**: none
**Reuses**: `InterpretationProposal` e convenções do Pydantic em `app/triage/interpretation_schemas.py`.
**Requirement**: KEDB-06, KEDB-07, KEDB-08

**Done when**:
- [x] Modelos `KedbLookupStatus`, `KedbMatch` e `KedbLookupResult` são definidos com `extra="forbid"` e `frozen=True`.
- [x] Campo opcional/estruturado `kedb` é compatibilizado na resposta da rota.
- [x] Testes unitários validam a serialização e rejeição de campos desconhecidos.
- [x] Gate passa: `pytest -v tests/unit`.

**Tests**: unit
**Gate**: quick
**Commit**: `feat(triage): define KEDB lookup response schemas`
**Status**: Complete
**Gate result**: `pytest -v tests/unit` - 33 passed.

#### T2: Implementar utilitario de normalizacao de texto para comparacao deterministica

**Where**: `app/triage/kedb_normalization.py`
**Depends on**: T1
**Reuses**: Biblioteca padrão `unicodedata` (NFKD).
**Requirement**: KEDB-02

**Done when**:
- [x] Função `normalize_text` converte para minúsculas, remove acentos e remove espaços em branco extras.
- [x] Testes unitários cobrem strings com acentuação, caixas misturadas, espaços duplicados e valores nulos/vazios.
- [x] Gate passa: `pytest -v tests/unit`.

**Tests**: unit
**Gate**: quick
**Commit**: `feat(triage): add text normalization for KEDB matching`
**Status**: Complete
**Gate result**: `pytest -v tests/unit` - 35 passed.

---

### Phase 2: Persistencia e Repositorio KEDB

#### T3: Criar migracao SQL com a tabela kedb_entries e registros sinteticos

**Where**: `migrations/003_kedb_knowledge_base.sql`
**Depends on**: T2
**Reuses**: Padrão de migrações em `migrations/001_tickets_and_audit.sql` e `migrations/002_ticket_triage_catalogs.sql`.
**Requirement**: KEDB-01, KEDB-06

**Done when**:
- [x] Script DDL cria a tabela `kedb_entries` com índice no campo `service_candidate`.
- [x] Insere registros sintéticos demonstrativos com soluções de contorno e sintomas indexados.
- [x] Teste de setup do banco de dados aplica a migração com sucesso.
- [x] Gate passa: `pytest -v tests/integration/test_database_setup.py`.

**Tests**: integration
**Gate**: full
**Commit**: `feat(db): add KEDB table and demonstration seed`
**Status**: Complete
**Gate result**: `pytest -v tests/integration/test_database_setup.py` - 1 passed.

#### T4: Implementar repositorio e consultas deterministicas a KEDB

**Where**: `app/triage/kedb_repository.py`
**Depends on**: T3
**Reuses**: Conexão síncrona `psycopg` conforme padrão de `app/triage/repository.py`.
**Requirement**: KEDB-01, KEDB-03, KEDB-04, KEDB-05

**Done when**:
- [x] Função `search_kedb` busca por serviço candidato normalizado e, se não encontrar, busca pelos sintomas normalizados.
- [x] Registros são ordenados de forma ascendente por `error_id`.
- [x] Motivo de casamento (`match_reasons`) é preenchido de forma descritiva.
- [x] Testes de integração validam busca por serviço, fallback por sintomas e termos sem correspondência.
- [x] Gate passa: `pytest -v tests/integration`.

**Tests**: integration
**Gate**: full
**Commit**: `feat(triage): implement KEDB repository query and fallback`
**Status**: Complete
**Gate result**: `pytest -v tests/integration/test_kedb_repository.py` - 4 passed.

---

### Phase 3: Servico e Rota Local

#### T5: Implementar servico orquestrador da KEDB com suporte a falha parcial

**Where**: `app/triage/kedb_service.py`
**Depends on**: T4
**Reuses**: Repositório KEDB e esquemas criados em T1 e T4.
**Requirement**: KEDB-07, KEDB-08

**Done when**:
- [x] Função `lookup_kedb` executa a consulta no PostgreSQL e encapsula o resultado em `KedbLookupResult`.
- [x] Em caso de falha de conexão ou erro no banco, captura a exceção e retorna status `UNAVAILABLE` com lista vazia (sucesso parcial).
- [x] Testes unitários cobrem o fluxo de sucesso e o fallback resiliente sob erro simulado de banco.
- [x] Gate passa: `pytest -v tests/unit`.

**Tests**: unit
**Gate**: quick
**Commit**: `feat(triage): implement KEDB service with partial failure resilience`
**Status**: Complete
**Gate result**: `pytest -v tests/unit` - 38 passed.

#### T6: Integrar consulta a KEDB na rota local de interpretacao de chamados

**Where**: `app/tickets/routes.py`
**Depends on**: T5
**Reuses**: Rota `post_ticket_interpretation` e injeção de `DATABASE_URL`.
**Requirement**: KEDB-01, KEDB-07, KEDB-08, KEDB-09, KEDB-10, KEDB-11

**Done when**:
- [x] Rota chama `lookup_kedb` após a extração pelo LLM e inclui o resultado na resposta `TicketInterpretationResponse`.
- [x] Chamado, revisão e trilha de auditoria permanecem inalterados.
- [x] Testes de integração validam a resposta enriquecida, falha parcial de banco e persistência intacta.
- [x] Gate passa: `pytest -v`.

**Tests**: integration
**Gate**: full
**Commit**: `feat(api): enrich ticket interpretation with KEDB guidance`
**Status**: Complete
**Gate result**: `pytest -v` - 9 passed in `test_ticket_interpretation_api.py`.

---

### Phase 4: Documentacao e Rastreamento

#### T7: Atualizar documentacao de arquitetura e README

**Where**: `ARCHITECTURE.md`
**Depends on**: T6
**Reuses**: Estrutura existente do `ARCHITECTURE.md` e `README.md`.
**Requirement**: KEDB-06, KEDB-09, KEDB-10

**Done when**:
- [ ] Documentação reflete a tabela KEDB, fluxo de enriquecimento e fronteiras de isolamento com o OpenRouter.
- [ ] Testes de documentação passam.
- [ ] Gate passa: `pytest -v tests/unit/test_interpretation_docs.py`.

**Tests**: unit
**Gate**: quick
**Commit**: `docs(architecture): record KEDB lookup flow and data boundaries`

#### T8: Atualizar rastreador centralizado de entregas no PROJECT.md

**Where**: `PROJECT.md`
**Depends on**: T7
**Reuses**: Tabela de entregas e regras de auditoria do `PROJECT.md`.
**Requirement**: KEDB-01

**Done when**:
- [ ] Entrega da KEDB é registrada na tabela de fatias implementadas com links para Spec, Tasks e Verificação.
- [ ] Tabela de backlog planejado é ajustada.
- [ ] Testes de progresso do projeto passam: `pytest -v tests/unit/test_project_progress.py`.
- [ ] Gate passa: `pytest -v`.

**Tests**: unit
**Gate**: full
**Commit**: `docs(progress): track KEDB lookup delivery`

---

## Checks

**Run tests**: `pytest -v`

**C1** - A rota de interpretação consulta a KEDB usando os fatos extraídos pelo LLM (KEDB-01)
Proof: run tests | `tests/integration/test_ticket_interpretation_api.py::test_interpretation_queries_kedb_with_extracted_facts PASSED`

**C2** - A normalização de texto elimina acentos, espaços extras e unifica caixa baixa (KEDB-02)
Proof: run tests | `tests/unit/test_kedb_normalization.py::test_normalization_handles_accents_whitespace_and_case PASSED`

**C3** - O serviço candidato casa exatamente com registros da KEDB e cita o serviço como motivo (KEDB-03)
Proof: run tests | `tests/integration/test_kedb_repository.py::test_search_matches_by_service_candidate PASSED`

**C4** - Quando não há casamento por serviço, a busca realiza fallback determinístico pelos sintomas (KEDB-04)
Proof: run tests | `tests/integration/test_kedb_repository.py::test_search_falls_back_to_symptoms PASSED`

**C5** - Múltiplas correspondências da KEDB são ordenadas deterministamente por error_id ascendente (KEDB-05)
Proof: run tests | `tests/integration/test_kedb_repository.py::test_matches_ordered_by_error_id_asc PASSED`

**C6** - A resposta inclui error_id, título, resumo, motivos de match e orientações de contorno (KEDB-06)
Proof: run tests | `tests/unit/test_kedb_schemas.py::test_kedb_match_schema_accepts_valid_payload PASSED`

**C7** - A consulta bem-sucedida retorna status AVAILABLE com os registros correspondentes ou lista vazia (KEDB-07)
Proof: run tests | `tests/unit/test_kedb_service.py::test_service_returns_available_status_with_matches PASSED`

**C8** - Falha de banco na KEDB retorna HTTP 200 com status UNAVAILABLE preservando a proposta do LLM (KEDB-08)
Proof: run tests | `tests/integration/test_ticket_interpretation_api.py::test_kedb_database_failure_returns_partial_success PASSED`

**C9** - Dados da KEDB e catálogos não são transmitidos ao OpenRouter (KEDB-09)
Proof: run tests | `tests/unit/test_openrouter_client.py::test_client_sends_schema_constrained_description_only_request PASSED`

**C10** - A consulta à KEDB mantém o chamado, estado, revisão e auditoria completamente inalterados (KEDB-10)
Proof: run tests | `tests/integration/test_ticket_interpretation_api.py::test_kedb_lookup_leaves_ticket_and_audit_unchanged PASSED`

**C11** - O endpoint permanece acessível exclusivamente no servidor local ligado ao loopback (KEDB-11)
Proof: run tests | `tests/integration/test_app_runtime.py::test_server_binds_to_loopback_only PASSED`

---

## Handoff

**Settled during Specify**: Consulta determinística à KEDB local no PostgreSQL, prioridade serviço sobre sintomas, normalização estrita, sucesso parcial em caso de falha de banco e orientações puramente consultivas.
**Settled during Design**: Migração com tabela `kedb_entries`, ordenação por `error_id ASC`, função de normalização com `unicodedata` e orquestração síncrona na rota FastAPI.
**Dispatched**: None.
**Walked**: Not applicable (API local sem interface gráfica).

## Phase Execution Map

```text
T1 → T2
T3 → T4
T5 → T6
T7 → T8
```
