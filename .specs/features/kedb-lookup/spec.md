# Consulta à Base de Erros Conhecidos (KEDB) — Specification

**Approved**: 2026-11-06 - user: "spec.md aprovada"

## Problem Statement

A rota atual de interpretação extrai fatos candidatos da descrição de incidentes usando um LLM, mas os analistas de suporte ainda precisam pesquisar manualmente em bases de conhecimento para encontrar soluções de contorno relevantes. Esta funcionalidade enriquece a resposta da interpretação local com correspondências determinísticas a partir de uma base de erros conhecidos (KEDB) no PostgreSQL, fornecendo orientações práticas ao operador sem delegar autoridade de decisão e sem alterar o estado do chamado.

## Goals

- [ ] Consultar uma KEDB local no PostgreSQL de forma determinística a partir do serviço candidato e dos sintomas extraídos pelo LLM.
- [ ] Retornar correspondências estruturadas contendo identificador do erro, título, resumo, motivos da correspondência e instruções de contorno (workaround).
- [ ] Enriquecer o endpoint local existente `POST /tickets/{ticket_id}/interpretation` garantindo resiliência com suporte a falhas parciais.
- [ ] Preservar as fronteiras de dados: manter os registros da KEDB estritamente locais, nunca enviando dados da KEDB ao OpenRouter.

## Out of Scope

| Funcionalidade | Motivo |
| --- | --- |
| API administrativa de CRUD ou importação da KEDB | O usuário selecionou registros sintéticos demonstrativos via migração; gestão da base fica para etapas futuras do roadmap. |
| Busca vetorial, embeddings ou matching por IA | O usuário escolheu matching determinístico por texto exato normalizado para evitar alucinações e custos de dependência externa. |
| Envio de dados da KEDB ou catálogos ao OpenRouter | O processamento em nuvem é restrito exclusivamente à descrição salva do chamado. |
| Execução automática de soluções de contorno | As instruções de contorno são apenas consultivas para o operador humano; correções automáticas de infraestrutura estão fora de escopo. |
| Decisão automática de triagem ou mutação do chamado | A interpretação e o enriquecimento com KEDB continuam sendo propostas consultivas; a triagem determinística permanece uma chamada separada e explícita. |
| Acesso remoto à API, autenticação e autorização | O endpoint permanece restrito ao servidor de desenvolvimento local ligado a `127.0.0.1`. |

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Fonte de dados da KEDB | `local_seeded_postgres`: Tabela PostgreSQL populada com dados sintéticos demonstrativos via script de migração. | Mantém a KEDB local, relacional, rápida e sem necessidade de microsserviços ou CRUD adicional. | y |
| Estratégia de busca | `service_then_symptoms`: Prioriza o serviço candidato extraído; se não houver correspondência, busca pelos sintomas como contingência. | Evita sugestões de sintomas genéricos quando há erro conhecido específico para o serviço identificado. | y |
| Normalização de termos | `normalized_exact`: Normalização de caixa (minúsculas), remoção de acentos e eliminação de espaços extras antes da comparação exata. | Elimina falsos positivos de sobreposição parcial de palavras e tolera variações de digitação e acentuação. | y |
| Integração na resposta | `augment_interpretation`: Adicionar o objeto KEDB (com status e matches) à resposta existente de `POST /tickets/{ticket_id}/interpretation`. | Consolida a visão diagnóstica do operador em uma única requisição local. | y |
| Tratamento de falha parcial | `partial_success`: Se a consulta à KEDB falhar ou estiver indisponível, preservar a proposta do LLM com HTTP 200, status `UNAVAILABLE` e matches vazios. | Garante que a extração do LLM não seja perdida caso o banco de dados da KEDB apresente instabilidade momentânea. | y |
| Representação de status | `status_field`: Campo explícito de status com os valores `AVAILABLE` e `UNAVAILABLE`. | Permite ao operador distinguir claramente entre nenhuma correspondência encontrada e indisponibilidade da KEDB. | y |
| Nível de detalhe da orientação | `full_guidance`: Retornar id do erro, título, resumo, motivos do match e texto completo da solução de contorno. | Fornece ao operador todas as informações necessárias para ação rápida sem exigir consultas manuais adicionais. | y |
| Fronteira de dados do LLM | Os registros da KEDB permanecem locais e nunca são transmitidos ao provedor externo (OpenRouter). | Respeita a política de segurança e privacidade aprovada de enviar apenas a descrição do chamado à nuvem. | y |
| Desempate na ordenação | Ordenação determinística ascendente por identificador do erro (error_id). | Garante respostas estáveis, idempotentes e reproduzíveis. | y |
| Execução de contornos | Puramente consultivo para análise do operador; nenhuma ação de remediação é disparada no sistema. | Atende à diretriz central do projeto de manter decisões críticas sob controle humano. | y |

**Open questions:** none - all product decisions raised during discussion are resolved; remaining defaults are explicit above.

## User Stories

### P1: Consultar KEDB e enriquecer proposta de interpretação ⭐ MVP

**User Story**: Como operador local, quero que a interpretação do chamado consulte a base de erros conhecidos (KEDB) a partir dos fatos extraídos e retorne soluções de contorno recomendadas, para que eu possa avaliar ações paliativas rapidamente sem que o chamado seja alterado.

**Why P1**: Conectar o diagnóstico extraído pelo LLM ao conhecimento operacional acumulado é o valor principal da KEDB no fluxo de triagem, mantendo a regra de negócio determinística e segura.

**Acceptance Criteria**:

1. **KEDB-01** WHEN a local client requests `POST /tickets/{ticket_id}/interpretation` for an existing ticket and OpenRouter returns a valid interpretation proposal THEN the system SHALL query the local PostgreSQL KEDB using the extracted service candidate and symptoms.
2. **KEDB-02** The system SHALL normalize service candidate and symptom text by lowercasing, stripping whitespace, and removing accents before matching against stored KEDB records.
3. **KEDB-03** WHEN the normalized service candidate matches one or more KEDB records by exact equality THEN the system SHALL return the matching KEDB records with match reason citing the service.
4. **KEDB-04** WHEN no service match is found or no service candidate is extracted, and one or more normalized symptoms match KEDB records by exact equality THEN the system SHALL return the matching KEDB records with match reason citing the matched symptom.
5. **KEDB-05** The system SHALL order multiple KEDB matches deterministically by error ID ascending to ensure reproducible responses.
6. **KEDB-06** The system SHALL include in each KEDB match the error identifier, title, summary, match reasons, and workaround instructions for operator review, and SHALL NOT execute workarounds automatically.
7. **KEDB-07** WHEN the KEDB lookup succeeds THEN the system SHALL return status `AVAILABLE` and the list of matches, which SHALL be empty if neither service nor symptoms match.
8. **KEDB-08** IF the KEDB lookup encounters a database error or unavailability THEN the system SHALL return HTTP `200` with the interpretation proposal intact, KEDB status `UNAVAILABLE`, and an empty match list.
9. **KEDB-09** The system SHALL NOT transmit KEDB records, catalog entries, or database queries to OpenRouter.
10. **KEDB-10** The system SHALL leave the persisted ticket, triage result, revision, and audit log entries unchanged during KEDB lookup.
11. **KEDB-11** The system SHALL expose KEDB-augmented interpretation only through the local development server bound to `127.0.0.1`.

**Independent Test**: Solicitar `POST /tickets/{ticket_id}/interpretation` para um chamado existente com extração mockada do LLM correspondente a registros da KEDB (por serviço e por sintoma), verificar o enriquecimento da resposta com status e contornos, simular falha no banco para atestar resiliência com fallback parcial, e confirmar que chamados e auditoria permanecem inalterados.

## Edge Cases

- Se o serviço candidato extraído não tiver registro correspondente na KEDB: executar a busca de contingência pelos sintomas.
- Se nem o serviço nem os sintomas tiverem correspondência na KEDB: retornar status `AVAILABLE` com lista de matches vazia `[]`.
- Se serviço e sintomas forem nulos ou vazios: retornar status `AVAILABLE` com lista de matches vazia `[]` sem executar queries com termos em branco.
- Se a consulta à KEDB falhar por erro de conexão ou banco: retornar HTTP `200` com a proposta do LLM intacta, status `UNAVAILABLE` e matches vazios `[]`.
- Se a chamada ao OpenRouter falhar (ex.: 502/503): retornar o erro correspondente sem executar a busca na KEDB.
- Quando os termos contiverem acentos, caixas mistas ou espaços sobressalentes: casar perfeitamente com os registros normalizados correspondentes.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| KEDB-01 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-02 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-03 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-04 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-05 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-06 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-07 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-08 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-09 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-10 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |
| KEDB-11 | P1: Consultar KEDB e enriquecer proposta de interpretação | Tasks | Complete |

**Coverage:** 11 total, 11 mapped to the story, 0 unmapped.

## Differences from the source

None. No binding screen or design reference was provided.

## Sources
