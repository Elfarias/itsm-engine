# API Básica de Chamados — Especificação

**Approved**: 2026-11-06 - user: "Aprovar a Spec"

## Problem Statement

Solicitantes precisam registrar incidentes e consultar o chamado resultante. O projeto ainda não tem uma API implementada para esse fluxo. Esta funcionalidade cria a base persistente e validada, sem dependência de LLM.

## Goals

- [ ] Criar chamados por API REST, validando uma descrição de até 4.000 caracteres.
- [ ] Permitir que o cliente recupere um chamado persistido pelo seu identificador.
- [ ] Registrar um evento de auditoria para cada criação aceita.

## Out of Scope

| Funcionalidade | Motivo |
| --- | --- |
| Triagem com LLM, consulta a CMDB/KEDB, prioridade e roteamento | Serão especificados em funcionalidades posteriores. |
| Listagem, atualização ou exclusão de chamados | O recorte inicial cobre somente criação e consulta individual. |
| Autenticação e autorização | Esta entrega destina-se somente a uso local e não deve ser exposta publicamente. |
| Idempotência de criação | O usuário definiu que cada POST aceito cria um chamado; idempotência será outra funcionalidade. |
| Consulta de auditoria e reprocessamento | Não são necessários para criar ou consultar o chamado. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Contrato HTTP | `POST /tickets` responde `201`; `GET /tickets/{id}` responde `200`; entrada inválida responde `422`; identificador inexistente responde `404`. | Contrato REST claro e compatível com a stack FastAPI/Pydantic. | n |
| Campos devolvidos | A resposta contém identificador, descrição, estado e data de criação. | Mantém a API mínima e retorna o necessário para localizar e acompanhar o chamado inicial. | n |
| Identificador e data | A aplicação gera um identificador UUID v4 e registra a data de criação em UTC. | O identificador não sequencial mantém o contrato da API opaco e pode ser usado como chave do banco. | y |
| Limite da descrição | De 1 a 4.000 caracteres; texto vazio ou composto somente por espaços é inválido. | O usuário confirmou o limite de 4.000 caracteres; o mínimo evita chamados sem descrição útil. | y |
| Estado inicial | Todo chamado novo começa em `NOVO`. | Definido nos documentos de arquitetura e fluxo do projeto. | y |
| Persistência e auditoria atômicas | O registro do chamado e o evento de criação são gravados na mesma transação PostgreSQL. | Evita chamado sem auditoria ou evento de auditoria sem chamado. | n |
| Falha de persistência | A API responde `503` e não confirma a criação se a transação não puder ser concluída. | Evita resposta de sucesso sem persistência confirmada. | n |
| Operações repetidas | Cada POST válido cria um novo identificador e um novo chamado, inclusive quando a descrição for igual. | Decisão explícita do usuário; idempotência será especificada depois. | y |
| Acesso | A API não exige autenticação neste recorte e só pode ser usada no ambiente local, sem exposição pública. | Decisão explícita do usuário; a autenticação depende do ambiente de exposição. | y |
| Auditoria de criação | Cada criação confirmada gera um evento de auditoria com identificador do chamado, tipo do evento e data/hora; a role da aplicação pode inserir, mas não atualizar ou excluir eventos. | O usuário confirmou a auditoria básica nesta entrega; o projeto exige rastreabilidade append-only. | y |

**Open questions:** none - as premissas técnicas marcadas `n` ficam visíveis para correção na aprovação da Spec.

---

## User Stories

### P1: Registrar chamado ⭐ MVP

**User Story**: Como solicitante ou cliente da API, quero registrar um incidente com sua descrição para obter um chamado persistido que possa consultar.

**Why P1**: A criação persistente de chamados é a entrada do fluxo ITSM e o primeiro marco funcional definido no plano do projeto.

**Acceptance Criteria**:

1. **TKT-01** WHEN um cliente envia uma descrição não vazia de até 4.000 caracteres a `POST /tickets` THEN o sistema SHALL criar um chamado com identificador UUID v4, estado `NOVO` e data de criação em UTC, e SHALL responder `201`.
2. **TKT-02** WHEN um cliente envia um corpo sem descrição ou com descrição vazia ou composta somente por espaços THEN o sistema SHALL responder `422` e SHALL não persistir um chamado.
3. **TKT-03** WHEN um cliente envia uma descrição com mais de 4.000 caracteres THEN o sistema SHALL responder `422` e SHALL não persistir um chamado.
4. **TKT-04** WHEN um cliente repete um POST válido, inclusive com a mesma descrição THEN o sistema SHALL criar um chamado novo com identificador diferente para cada solicitação aceita.
5. **TKT-05** WHEN o sistema confirma a criação de um chamado THEN o sistema SHALL persistir exatamente um evento de auditoria com o identificador do chamado, o tipo de evento de criação e a data/hora, na mesma transação do chamado.
6. **TKT-06** IF a transação de criação ou auditoria falha THEN o sistema SHALL responder `503` e SHALL persistir nem o chamado nem seu evento de criação.
7. **TKT-07** The system SHALL permit application requests without authentication only in the local development environment.
8. **TKT-08** The system SHALL NOT expose this unauthenticated API to public networks.
9. **TKT-12** The system SHALL deny the application database role permission to update or delete audit events.

**Independent Test**: Enviar uma descrição válida, receber `201`, confirmar o estado `NOVO` e o evento de auditoria persistido; depois reiniciar a aplicação e consultar o chamado por identificador.

### P1: Consultar chamado ⭐ MVP

**User Story**: Como solicitante ou cliente da API, quero consultar um chamado pelo identificador para recuperar os dados registrados.

**Why P1**: A consulta individual permite ao cliente recuperar o resultado da criação sem introduzir listagem ou interface gráfica.

**Acceptance Criteria**:

1. **TKT-09** WHEN um cliente consulta `GET /tickets/{id}` para um chamado existente THEN o sistema SHALL responder `200` com o identificador, a descrição, o estado e a data de criação persistidos.
2. **TKT-10** IF um cliente consulta `GET /tickets/{id}` para um identificador inexistente THEN o sistema SHALL responder `404`.
3. **TKT-11** WHEN a aplicação reinicia enquanto o banco de dados permanece disponível THEN o sistema SHALL continuar retornando o chamado previamente persistido pela consulta por identificador.
4. **TKT-13** IF um cliente consulta `GET /tickets/{id}` com um identificador que não corresponde ao formato UUID THEN o sistema SHALL responder `422`.

**Independent Test**: Criar um chamado, consultar o identificador retornado e comparar os campos devolvidos com os valores persistidos.

---

## Edge Cases

- Descrição ausente, vazia ou composta somente por espaços: `422`, sem criação.
- Descrição acima de 4.000 caracteres: `422`, sem criação.
- Identificador não encontrado: `404`.
- Identificador fora do formato UUID: `422`.
- Falha na persistência do chamado ou da auditoria: `503`, sem sucesso parcial.
- Repetição da mesma descrição: cria chamados distintos; não há idempotência neste recorte.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| TKT-01 | P1: Registrar chamado | Tasks | In Tasks |
| TKT-02 | P1: Registrar chamado | Tasks | In Tasks |
| TKT-03 | P1: Registrar chamado | Tasks | In Tasks |
| TKT-04 | P1: Registrar chamado | Tasks | In Tasks |
| TKT-05 | P1: Registrar chamado | Tasks | In Tasks |
| TKT-06 | P1: Registrar chamado | Tasks | In Tasks |
| TKT-07 | P1: Registrar chamado | Tasks | In Tasks |
| TKT-08 | P1: Registrar chamado | Tasks | In Tasks |
| TKT-09 | P1: Consultar chamado | Tasks | In Tasks |
| TKT-10 | P1: Consultar chamado | Tasks | In Tasks |
| TKT-11 | P1: Consultar chamado | Tasks | In Tasks |
| TKT-12 | P1: Registrar chamado | Tasks | In Tasks |
| TKT-13 | P1: Consultar chamado | Tasks | In Tasks |

**ID format:** `TKT-NN`

**Status values:** Pending → In Design → In Tasks → Implementing → Verified

**Coverage:** 13 total, 13 mapped to tasks, 0 unmapped

## Sources

- [PROJECT.md](../../../PROJECT.md) - escopo, atores, requisitos funcionais e estados do chamado.
- [ARCHITECTURE.md](../../../ARCHITECTURE.md) - contrato de persistência, estado inicial e auditoria.
- [MPLEMENTATION-PLAN.md](../../../MPLEMENTATION-PLAN.md) - sequência do MVP e primeiro marco técnico.
- [TECHNOLOGY-STACK.md](../../../TECHNOLOGY-STACK.md) - FastAPI, Pydantic, PostgreSQL e pytest.
- Decisões do usuário nesta conversa - escopo da funcionalidade, usuário, consulta por identificador, campos obrigatórios, uso local sem autenticação, ausência de idempotência, limite da descrição e auditoria de criação.

## Success Criteria

- [ ] Um chamado válido pode ser criado e recuperado pelo identificador, inclusive após reinício da aplicação.
- [ ] Entradas inválidas e identificadores inexistentes recebem os status HTTP especificados, sem criação indevida.
- [ ] Cada criação confirmada possui exatamente um evento de auditoria correspondente.
- [ ] A role da aplicação não pode atualizar nem excluir eventos de auditoria.
- [ ] Falhas na gravação não deixam chamado ou evento parcialmente persistido.
- [ ] A API não exige autenticação em uso local e não é exposta publicamente.
