# PROJECT — Plataforma de Triagem Inteligente de Incidentes de TI

**Nome do projeto:** ITSM Agent
**Versão do documento:** 1.0
**Status:** Baseline atualizada para a fatia de triagem determinística
**Idioma:** Português (Brasil)

## 1. Visão geral

O ITSM Agent é uma aplicação de triagem inteligente de incidentes de TI.
A arquitetura-alvo combina interpretação de texto, dados operacionais e
regras determinísticas. A fatia implementada recebe chamados pela API,
mantém catálogos versionados e classifica fatos estruturados por um
serviço Python interno.

LLM, KEDB e integração ITSM externa são evoluções futuras. A
classificação atual não usa LLM e não possui endpoint público.

**Princípio central:** quando a interpretação por IA for adicionada, a
aplicação continuará validando os fatos e executando as regras de
negócio e as operações autorizadas.

## 2. Problema

Processos de triagem manual podem gerar atrasos, classificações
inconsistentes e encaminhamento incorreto de incidentes. O projeto
pretende demonstrar como automatizar parte desse processo sem transferir
decisões críticas e controles operacionais integralmente ao modelo de
IA.

## 3. Objetivos

- Receber e persistir chamados por API REST.
- Interpretar descrições não estruturadas usando LLM.
- Extrair serviço candidato, sintomas, evidências de impacto e
    urgência e informações ausentes.
- Consultar CMDB e base de erros conhecidos (KEDB).
- Calcular prioridade por regras determinísticas.
- Determinar a equipe responsável por mapeamento controlado.
- Controlar o ciclo de vida dos chamados por máquina de estados.
- Garantir operações idempotentes na integração simulada.
- Registrar eventos relevantes para auditoria.
- Testar comportamento sob falhas e entradas maliciosas.

## 4. Escopo do projeto

### Fatia implementada

1. API FastAPI para criar e consultar chamados.
2. PostgreSQL como persistência relacional.
3. Catálogos sintéticos e versionados de serviços, ativos e equipes, sem
   CRUD administrativo.
4. Serviço interno de regras determinísticas para prioridade e
   roteamento por serviço.
5. Persistência de snapshots completos, controle de revisão, estados de
   triagem e auditoria transacional append-only.
6. Execução local e testes de integração com Docker Compose.

### Evoluções futuras

- Interpretação de descrições em texto livre por LLM e extração estruturada.
- Consultas à KEDB.
- Orquestrador e canal público de complementação ou classificação.
- Integração ITSM externa com retry, timeout e idempotência remota.
- Interface gráfica completa para operadores.
- Plataforma de microsserviços, Kubernetes, broker, Redis, PGVector ou
  alta disponibilidade multi-região.
- Execução automática de procedimentos de correção em infraestrutura.

Esses itens poderão ser reconsiderados somente quando houver requisito
concreto que os justifique.

## 5. Usuários e atores

- **Solicitante:** registra o incidente e pode fornecer informações
    complementares.
- **Agente de triagem:** componente lógico que futuramente poderá
    coordenar interpretação e consultas.
- **Analista de suporte:** recebe chamados classificados ou pendentes
    de análise manual.
- **Equipe técnica:** grupo responsável pelo serviço ou componente
    afetado.
- **Administrador:** mantém configurações do ambiente; publicação de
    catálogos ocorrerá por versões controladas, sem CRUD administrativo
    nesta fatia.

## 6. Fluxo da fatia implementada

1. A API recebe um chamado, valida o contrato e persiste o estado `NOVO`.
2. Um chamador interno fornece um snapshot de fatos estruturados e a
   revisão esperada ao serviço de triagem.
3. O serviço bloqueia o chamado, verifica estado e revisão e carrega a
   versão ativa do catálogo.
4. As regras validam referências e consistência do ativo, calculam a
   prioridade pela matriz aprovada e obtêm a equipe pelo mapeamento do
   serviço.
5. O serviço grava snapshot, resultado, estado e auditoria na mesma
   transação.
6. Dados completos deixam o chamado em `EM_TRIAGEM`. Fatos ausentes ou
   conflitantes deixam-no em `PENDENTE_INFORMACAO`, sem prioridade ou
   equipe.
7. Uma avaliação pendente substitui o snapshot completo. Um retry
   idêntico não duplica efeitos; revisões concorrentes desatualizadas
   geram conflito explícito.

Esta fatia não extrai fatos do texto do chamado nem envia atualizações a
um sistema ITSM externo. Esses fluxos ficam para etapas futuras.

## 7. Requisitos funcionais

Os requisitos descrevem o produto-alvo. LLM, KEDB e integração ITSM
permanecem planejados para etapas futuras, conforme o escopo acima.

  -----------------------------------------------------------------------
  ID                                  Requisito
  ----------------------------------- -----------------------------------
  RF-01                               Criar e consultar chamados por API
                                      REST.

  RF-02                               Validar entradas e contratos com
                                      Pydantic.

  RF-03                               Solicitar interpretação estruturada
                                      ao LLM.

  RF-04                               Validar serviço candidato contra o
                                      CMDB.

  RF-05                               Consultar conhecimento operacional
                                      na KEDB.

  RF-06                               Solicitar informações adicionais
                                      quando dados essenciais estiverem
                                      ausentes.

  RF-07                               Calcular prioridade pela matriz
                                      aprovada de impacto e urgência.

  RF-08                               Determinar equipe por mapeamento
                                      versionado de serviço para equipe.

  RF-09                               Validar transições da máquina de
                                      estados.

  RF-10                               Executar atualizações idempotentes
                                      na API simulada.

  RF-11                               Registrar eventos de auditoria.

  RF-12                               Permitir reprocessamento controlado
                                      após falha de integração.
  -----------------------------------------------------------------------

## 8. Requisitos não funcionais

- **Confiabilidade:** falhas temporárias não devem provocar operações
    duplicadas.
- **Segurança:** o LLM não terá acesso direto ao banco nem autoridade
    para executar ações arbitrárias.
- **Rastreabilidade:** decisões, transições e integrações relevantes
    devem gerar eventos auditáveis.
- **Manutenibilidade:** aplicação modular, com responsabilidades
    internas bem definidas.
- **Portabilidade:** execução conteinerizada e dependências externas
    limitadas.
- **Testabilidade:** regras de negócio e cenários de falha devem
    possuir testes automatizados.
- **Proporcionalidade:** não introduzir infraestrutura adicional sem
    necessidade demonstrada.

## 9. Regras de negócio principais

### 9.1 Prioridade

A prioridade será calculada pela aplicação a partir de impacto e
urgência. A criticidade e as dependências cadastradas no CMDB fornecem
contexto, mas não substituem esses critérios.

A matriz aprovada para esta fatia é:

| Impacto | Alta | Média | Baixa |
| --- | --- | --- | --- |
| Alto | P1 | P2 | P2 |
| Médio | P2 | P3 | P3 |
| Baixo | P3 | P4 | P4 |

O serviço valida impacto e urgência por valores fechados. A origem dos
fatos e sua extração de texto livre serão definidas para uma etapa futura.

### 9.2 Roteamento

O roteamento usa o mapeamento versionado `service_id` para `target_team`
do catálogo ativo. A equipe não é escolhida pelo chamador.

### 9.3 Dados insuficientes

Quando faltarem fatos obrigatórios, quando o serviço não tiver equipe
mapeada ou quando o ativo não corresponder ao serviço, o sistema persiste
os fatos válidos e deixa o chamado `PENDENTE_INFORMACAO`, sem prioridade
ou equipe. Referências desconhecidas são rejeitadas sem alterar o
chamado.

## 10. Critérios de aceite

A fatia determinística é funcional quando demonstra:

- Criação e consulta de chamados.
- Catálogo versionado com relações válidas entre serviços, ativos e
  equipes.
- Matriz de prioridade aprovada e roteamento pelo catálogo.
- Persistência completa de avaliações, estados pendentes e reavaliações.
- Retry idempotente, conflito de revisão e auditoria transacional.
- Execução local por Docker Compose e testes automatizados.

## 11. Premissas e decisões pendentes

As decisões abaixo precisam ser confirmadas antes ou durante a
implementação:

- Provedor, modelo e política de uso do LLM.
- Critérios objetivos para classificar impacto e urgência.
- Contrato da API simulada e formato dos erros.
- Estratégia de autenticação entre componentes, caso sejam expostos
    além do ambiente local.
- Serviço de gerenciamento de segredos para o ambiente de produção.
- Política de retenção dos eventos de auditoria.
- Critérios de revisão humana e autorização de reprocessamento.

## 12. Diretriz de evolução

A evolução deverá ocorrer por necessidade comprovada. Busca vetorial,
mensageria, cache, microsserviços e orquestração de containers não fazem
parte da primeira versão. Qualquer inclusão deverá apresentar o problema
que resolve, o custo operacional e a razão pela qual a solução atual é
insuficiente.
