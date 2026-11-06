# Catálogos e Regras Determinísticas de Triagem — Specification

**Approved**: 2026-11-06 - user: "Aprovar a Spec"

## Problem Statement

Chamados persistidos ainda não podem ser classificados de forma controlada porque o projeto não dispõe de catálogos de referência nem de um serviço interno de regras determinísticas. Esta funcionalidade fornece dados sintéticos e versionados de serviços, ativos e equipes, calcula prioridade pela matriz aprovada e direciona o ticket somente por um mapeamento validado.

## Goals

- [ ] Disponibilizar catálogos sintéticos e versionados de serviços, ativos e equipes, sem endpoints administrativos de CRUD.
- [ ] Classificar tickets com a matriz atual de impacto e urgência e com o mapeamento de serviço para equipe.
- [ ] Persistir fatos válidos e o resultado da avaliação sem inventar classificações quando os dados forem insuficientes ou conflitantes.
- [ ] Permitir reavaliação de tickets pendentes com um snapshot completo dos fatos, sem sobrescritas concorrentes silenciosas.

## Out of Scope

| Funcionalidade | Motivo |
| --- | --- |
| API pública para classificação ou administração de catálogos | Esta fatia expõe somente um serviço interno; contratos de API serão definidos posteriormente. |
| Interpretação por LLM ou extração de fatos de texto livre | Será tratada em uma funcionalidade posterior; esta fatia recebe fatos estruturados. |
| KEDB, erros conhecidos ou procedimentos de correção | O usuário adiou a KEDB e a execução de correções não faz parte deste recorte. |
| Integração com ITSM externo e transição para `CLASSIFICADO` | A classificação permanece em `EM_TRIAGEM` até uma integração futura confirmar a conclusão. |
| Interface gráfica e CRUD de catálogos | Os catálogos iniciais são dados versionados, não mantidos por operadores nesta fatia. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Origem dos catálogos | Registros sintéticos, vendor-neutral, com identificadores estáveis e relações de serviço, ativo e equipe; alterações são publicadas como nova versão, sem CRUD administrativo. | Preserva interoperabilidade e mantém os dados de demonstração reproduzíveis. | y |
| Versão usada na avaliação | Cada nova avaliação de ticket pendente usa a versão ativa. Retry idêntico de ticket em `EM_TRIAGEM` retorna o resultado e a versão previamente registrados. | Permite que uma nova avaliação aproveite correções de catálogo sem alterar silenciosamente uma classificação já concluída. | y |
| Referências ou valores inválidos | Identificador de serviço ou ativo inexistente no catálogo, ou impacto/urgência fora dos valores permitidos, é entrada inválida; rejeitar a avaliação sem alterar o ticket. Serviço conhecido sem equipe mapeada é dado insuficiente e deixa o ticket pendente. | Distingue entrada inválida de uma lacuna de configuração que pode ser corrigida no catálogo. | n |
| Ativo | O ativo é opcional; se informado, precisa existir e estar relacionado ao serviço informado. | A classificação pela matriz exige serviço, impacto e urgência; o ativo serve para validar conflito, não para substituir fatos obrigatórios. | n |
| Auditoria | Toda avaliação que altera os fatos persistidos, o resultado ou o estado registra evento append-only associado ao ticket e à versão dos catálogos usada. | Segue a exigência de rastreabilidade do projeto e permite explicar o resultado determinístico. | n |
| Falha de persistência | Dados do ticket, resultado e auditoria são atômicos; erro de gravação é propagado como falha explícita, sem sucesso parcial. | Evita um estado sem classificação correspondente ou uma decisão sem rastreabilidade. | n |

**Open questions:** none - all product decisions raised during discussion are resolved; remaining defaults are explicit above.

---

## User Stories

### P1: Avaliar e classificar ticket ⭐ MVP

**User Story**: Como agente de triagem, quero avaliar fatos estruturados de um ticket usando catálogos e regras determinísticas para persistir uma prioridade e uma equipe confiáveis, ou deixar o ticket pendente quando não houver evidência suficiente.

**Why P1**: Catálogos e classificação determinística constituem a próxima fatia escolhida e são pré-requisitos para a futura extração por LLM e integração ITSM.

**Acceptance Criteria**:

1. **TRI-01** The system SHALL provide versioned, synthetic, vendor-neutral service, asset and support-team catalogs with stable identifiers and explicit service-to-team and asset-to-service relationships.
2. **TRI-02** The system SHALL NOT expose catalog create, update or delete operations through administrative API endpoints.
3. **TRI-03** WHEN the rule service receives valid impact and urgency values THEN the system SHALL map all nine combinations exactly as follows: impact `ALTO` with urgency `ALTA`, `MEDIA`, `BAIXA` yields `P1`, `P2`, `P2`; impact `MEDIO` yields `P2`, `P3`, `P3`; and impact `BAIXO` yields `P3`, `P4`, `P4`.
4. **TRI-04** WHEN a ticket has a catalogued service with a team mapping, valid impact and urgency, and no conflicting supplied asset THEN the system SHALL calculate and return the priority defined by `TRI-03`.
5. **TRI-05** WHEN a complete ticket evaluation has a catalogued service with a team mapping THEN the system SHALL select the mapped support team and SHALL NOT use a team supplied by the caller as the classification result.
6. **TRI-06** WHEN a complete evaluation succeeds THEN the system SHALL persist the supplied valid service, asset, impact and urgency facts, the calculated priority and mapped team, and leave the ticket in `EM_TRIAGEM`.
7. **TRI-07** WHEN required facts are missing or a catalogued service has no team mapping THEN the system SHALL persist the supplied valid partial facts, set the ticket status to `PENDENTE_INFORMACAO`, and leave priority and target team unset.
8. **TRI-08** WHEN a supplied catalogued asset is not related to the supplied service THEN the system SHALL persist the valid supplied facts, set the ticket status to `PENDENTE_INFORMACAO`, and leave priority and target team unset.
9. **TRI-09** WHEN a `PENDENTE_INFORMACAO` ticket is re-evaluated THEN the system SHALL treat the submitted facts as a complete snapshot, replace the prior fact snapshot, and persist the new evaluation outcome.
10. **TRI-10** WHEN a pending ticket is evaluated again with identical facts and the same active catalog version THEN the system SHALL return the same effective result without duplicating classification side effects.
11. **TRI-11** IF a ticket in `EM_TRIAGEM` is evaluated with facts different from the facts already classified THEN the system SHALL reject the evaluation and SHALL preserve the persisted facts and classification.
12. **TRI-12** IF a service or asset identifier is absent from the active catalog, or impact or urgency is outside its allowed values, THEN the system SHALL reject the evaluation and SHALL leave the ticket unchanged.
13. **TRI-13** IF concurrent evaluations submit different snapshots for the same pending-ticket revision THEN the system SHALL accept at most one snapshot, reject the competing evaluation with an explicit conflict, and SHALL NOT merge or silently overwrite either snapshot.
14. **TRI-14** WHEN an evaluation changes persisted ticket facts, classification or status THEN the system SHALL append an audit event associated with the ticket and the catalog version used.
15. **TRI-15** IF persisting an evaluation or its audit event fails THEN the system SHALL report an explicit failure and SHALL commit neither the ticket changes nor the corresponding audit event.
16. **TRI-16** WHEN a ticket in `EM_TRIAGEM` is evaluated again with its identical persisted fact snapshot THEN the system SHALL return the previously persisted result and catalog version without duplicating classification side effects, regardless of which catalog version is currently active.

**Independent Test**: Carregar os catálogos versionados, avaliar combinações completas e incompletas por meio do serviço interno, consultar o ticket persistido e confirmar prioridade, equipe, estado, snapshot e auditoria; repetir com casos de conflito, retry e concorrência.

---

## Edge Cases

- Impacto ou urgência ausente: persistir os fatos válidos fornecidos e deixar o ticket `PENDENTE_INFORMACAO`, sem prioridade ou equipe.
- Serviço catalogado sem mapeamento para equipe: deixar o ticket pendente, sem inventar destino.
- Ativo catalogado relacionado a outro serviço: deixar o ticket pendente, sem prioridade ou equipe.
- Identificador de serviço ou ativo não catalogado, ou valor de impacto/urgência fora do domínio: rejeitar sem alterar o ticket.
- Reavaliação de ticket pendente: substituir os fatos anteriores pelo snapshot completo novo, inclusive quando um campo anterior não vier no snapshot.
- Repetição idêntica: manter o mesmo resultado efetivo sem efeitos de classificação duplicados.
- Fatos diferentes depois de classificação em `EM_TRIAGEM`: rejeitar sem alterar o resultado existente.
- Snapshots diferentes concorrentes para a mesma revisão pendente: aceitar no máximo um; rejeitar o outro explicitamente.
- Falha ao persistir ticket ou auditoria: não deixar gravação parcial.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| TRI-01 | P1: Avaliar e classificar ticket | Tasks | Verified |
| TRI-02 | P1: Avaliar e classificar ticket | Tasks | Verified |
| TRI-03 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-04 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-05 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-06 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-07 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-08 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-09 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-10 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-11 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-12 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-13 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-14 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-15 | P1: Avaliar e classificar ticket | Tasks | In Tasks |
| TRI-16 | P1: Avaliar e classificar ticket | Tasks | In Tasks |

**Coverage:** 16 total, 16 mapped to tasks, 0 unmapped.

---

## Differences from the source

None. No screen captures or binding design references were provided.

## Sources

- `.specs/features/ticket-triage/context.md` - decisions made by the user for this feature.
- `PROJECT.md` - product scope, priority matrix and functional baseline.
- `ARCHITECTURE.md` - catalogs, state machine, persistence and audit baseline.
- `.specs/features/ticket-api/spec.md` - existing ticket persistence and API behavior.

## Success Criteria

- [ ] Automated tests verify all nine impact/urgency combinations against the specified matrix.
- [ ] Automated tests verify complete classification, pending cases, asset/service conflict, full-snapshot replacement, idempotent retry, conflicting updates and concurrent re-evaluation.
- [ ] Automated tests verify catalog references, append-only audit behavior and atomic rollback when persistence fails.
- [ ] Automated tests verify pending re-evaluation uses the active catalog version and completed identical retries retain their recorded version.
- [ ] No public classification endpoint, catalog CRUD endpoint, LLM call or KEDB lookup is introduced by this feature.
