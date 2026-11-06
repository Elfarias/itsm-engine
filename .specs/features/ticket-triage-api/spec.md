# API Local de Triagem Determinística — Specification

**Approved**: 2026-11-06 - user: "Aprovar a Spec"

## Problem Statement

A avaliação determinística já funciona como serviço interno, mas clientes
da API não conseguem iniciá-la. Esta funcionalidade permite enviar fatos
estruturados para um chamado existente e consultar o resultado sem
adicionar extração por LLM ou expor o servidor à rede pública.

## Goals

- [ ] Disponibilizar uma operação HTTP local para avaliar um chamado existente.
- [ ] Retornar o estado e o resultado persistidos pela triagem determinística.
- [ ] Preservar validação, revisão concorrente, retry, transação e auditoria do serviço atual.

## Out of Scope

| Funcionalidade | Motivo |
| --- | --- |
| Criação de chamado e triagem em uma única operação | A decisão do usuário é avaliar separadamente um chamado existente. |
| Acesso por rede pública, autenticação ou autorização remota | Esta fatia é restrita a desenvolvimento local. |
| Extração de fatos com LLM, consulta à KEDB ou integração ITSM externa | São etapas futuras independentes. |
| Alteração das regras, catálogos ou estados aprovados da triagem | A API expõe o serviço existente; não muda suas regras de domínio. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Acesso | Sem autenticação e disponível somente no servidor ligado a `127.0.0.1`. | O servidor existente já se liga ao loopback e a API de chamados foi definida para uso local. | y |
| Fluxo | Avaliar um chamado persistido por uma operação separada da criação. | O serviço atual recebe o identificador do chamado, fatos e revisão esperada; a criação atual permanece inalterada. | y |
| Corpo da avaliação | JSON com `expected_revision` não negativo e objeto `facts`; `service_id`, `asset_id`, `impact` e `urgency` são opcionais e `facts` representa o snapshot completo. | Reutiliza o contrato de fatos e revisão do serviço; campos omitidos não preservam valores de um snapshot anterior. | y |
| Resultado pendente | Fatos válidos, porém insuficientes ou inconsistentes, são persistidos como `PENDENTE_INFORMACAO` e respondem HTTP `200`. | São resultados de avaliação previstos pelo domínio, não falhas de requisição. O usuário selecionou `persist_200`. | y |
| Mapeamento de erros HTTP | Chamado inexistente `404`; corpo, enum ou referências inválidas `422`; revisão/estado conflitante `409`. | O usuário escolheu os erros HTTP convencionais, opção `standard`. | y |
| Retry de avaliação pendente | Snapshot idêntico com a mesma versão ativa retorna sem duplicar efeitos; se a versão ativa mudou, reavalia com a versão nova. | Preserva TRI-10 e a política aprovada para avaliações pendentes. O usuário selecionou `active_catalog`. | y |
| Retry em triagem | Snapshot idêntico em `EM_TRIAGEM` retorna o resultado e a versão persistidos, mesmo após mudança do catálogo ativo. | Preserva TRI-16 e evita recálculo de uma classificação já concluída. | y |
| Falha de banco ou catálogo indisponível | Responder `503`; a operação não confirma gravações parciais. | A avaliação e sua auditoria são atômicas e a API de chamados já usa `503` para falhas de persistência. | n |

**Open questions:** none - all product decisions raised during discussion
are resolved; remaining defaults are recorded above.

---

## User Stories

### P1: Avaliar um chamado por API local ⭐ MVP

**User Story**: Como operador de desenvolvimento local, quero enviar
fatos estruturados para um chamado existente e receber a avaliação
persistida para exercitar o fluxo determinístico pela API.

**Why P1**: Expõe a funcionalidade implementada por uma interface
praticável sem introduzir LLM ou integração externa.

**Acceptance Criteria**:

1. **TRIAPI-01** WHEN um cliente local envia a `POST /tickets/{ticket_id}/triage` um corpo JSON com `expected_revision` inteiro não negativo e objeto `facts` THEN o sistema SHALL tratar `facts` como o snapshot completo, com `service_id`, `asset_id`, `impact` e `urgency` opcionais.
2. **TRIAPI-02** WHEN uma solicitação válida avalia um chamado existente THEN o sistema SHALL responder `200` com `ticket_id`, `status`, `facts`, `priority`, `target_team`, `catalog_version` e `facts_revision` do resultado efetivo.
3. **TRIAPI-03** WHEN a avaliação recebe fatos completos válidos THEN o sistema SHALL persistir o resultado aprovado pelo serviço, incluindo prioridade e equipe mapeada, e responder com o estado `EM_TRIAGEM`.
4. **TRIAPI-04** WHEN a avaliação recebe fatos parciais ou conflitantes válidos THEN o sistema SHALL persistir o snapshot conforme as regras existentes, deixar a prioridade e a equipe nulas quando aplicável e responder `200` com o estado `PENDENTE_INFORMACAO`.
5. **TRIAPI-05** IF o identificador UUID do chamado não existe THEN o sistema SHALL responder `404` sem criar nem alterar chamados.
6. **TRIAPI-06** IF o identificador do caminho não está no formato UUID, o corpo não corresponde ao contrato de fatos e revisão, contém campos não permitidos, ou referencia serviço/ativo inexistente ou enum inválido THEN o sistema SHALL responder `422` e SHALL deixar o chamado inalterado.
7. **TRIAPI-07** IF uma avaliação concorrente usa revisão obsoleta ou o estado atual não aceita os fatos enviados THEN o sistema SHALL responder `409` e SHALL preservar o snapshot e o resultado persistidos.
8. **TRIAPI-08** WHEN um chamado em `PENDENTE_INFORMACAO` recebe novamente fatos idênticos enquanto a mesma versão do catálogo continua ativa THEN o sistema SHALL retornar o resultado persistido sem duplicar efeitos de avaliação ou eventos de auditoria.
9. **TRIAPI-09** WHEN um chamado em `PENDENTE_INFORMACAO` recebe novamente fatos idênticos com a revisão atual após a ativação de outra versão do catálogo THEN o sistema SHALL reavaliar o snapshot usando a versão ativa nova e persistir o resultado correspondente.
10. **TRIAPI-10** WHEN um chamado em `EM_TRIAGEM` recebe novamente seu snapshot de fatos idêntico THEN o sistema SHALL retornar o resultado e a versão de catálogo previamente persistidos sem duplicar efeitos, independentemente da versão ativa.
11. **TRIAPI-11** IF the ticket evaluation or audit persistence fails THEN the system SHALL respond `503` and SHALL commit neither the ticket changes nor the corresponding audit event.
12. **TRIAPI-12** IF no active catalog is available for evaluation THEN the system SHALL respond `503` and SHALL leave the ticket unchanged.
13. **TRIAPI-13** The system SHALL accept unauthenticated triage requests only through the local development server bound to `127.0.0.1` and SHALL NOT expose the operation on public network interfaces.

**Independent Test**: Criar um chamado pela API atual, enviar uma avaliação
com fatos estruturados ao endpoint local, verificar o resultado e o
snapshot persistidos e repetir a chamada para confirmar idempotência.

---

## Edge Cases

- Chamado inexistente: `404`.
- Corpo inválido, campos extras ou enum/referência inválida: `422`, sem alteração.
- Revisão obsoleta ou estado não avaliável: `409`, sem sobrescrita.
- Fatos incompletos ou inconsistentes conforme as regras existentes:
  avaliação pendente persistida e resposta `200`.
- Retry de pendente com a mesma versão ativa: resultado existente sem evento duplicado; com versão ativa nova e revisão atual: reavaliação.
- Retry idêntico em `EM_TRIAGEM`: resultado e versão persistidos, mesmo com catálogo ativo novo.
- Falha de banco ou ausência de catálogo ativo: `503`, sem sucesso parcial.
- Acesso pela interface de rede pública: não permitido; o servidor permanece
  ligado a `127.0.0.1`.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| TRIAPI-01 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-02 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-03 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-04 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-05 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-06 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-07 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-08 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-09 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-10 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-11 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-12 | P1: Avaliar um chamado por API local | Tasks | Pending |
| TRIAPI-13 | P1: Avaliar um chamado por API local | Tasks | Pending |

**Coverage:** 13 total, 13 mapped to tasks, 0 unmapped.

---

## Differences from the source

None. No screen captures or binding design references were provided.

## Sources

- `.specs/features/ticket-triage-api/context.md` - decisions made by the user for this feature.
- `.specs/features/ticket-triage/spec.md` - approved behavior of deterministic triage.
- `.specs/features/ticket-api/spec.md` - local-only ticket API and existing HTTP conventions.
- `app/main.py` and `app/tickets/routes.py` - current server binding and route patterns.

## Success Criteria

- Automated API tests verify successful complete and pending evaluations, invalid and missing tickets, conflicts, idempotent retries, persistence failures and localhost-only binding.
- Every API outcome preserves the approved deterministic triage and transactional audit behavior.
- No public-network access, authentication system, LLM call, KEDB lookup or external ITSM integration is introduced by this feature.
