# PROJECT — Plataforma de Triagem Inteligente de Incidentes de TI

**Nome do projeto:** ITSM Agent
**Versão do documento:** 1.0
**Status:** Baseline de projeto — sujeito à validação durante a
implementação
**Idioma:** Português (Brasil)

## 1. Visão geral

O ITSM Agent é uma aplicação de triagem inteligente de incidentes de TI.
A solução recebe chamados, utiliza um modelo de linguagem (LLM) para
interpretar descrições em texto livre e extrair informações
estruturadas, consulta dados operacionais e aplica regras
determinísticas para classificar e direcionar os chamados.

O projeto combina inteligência artificial com controles tradicionais de
engenharia de software. O LLM não decide sozinho a prioridade, não
altera diretamente o banco de dados e não possui liberdade para executar
operações arbitrárias.

**Princípio central:** a IA interpreta; a aplicação valida, aplica as
regras de negócio e executa as operações autorizadas.

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

## 4. Escopo da primeira versão

### Incluído

1. API FastAPI para criação, consulta e atualização controlada de
    chamados.
2. PostgreSQL como persistência relacional.
3. Dados simulados de serviços, ativos, equipes e conhecimento
    operacional.
4. Integração com um LLM por API externa.
5. Extração estruturada validada com Pydantic.
6. Orquestrador Python com fluxo controlado.
7. Motor determinístico de prioridade e roteamento.
8. Máquina de estados centralizada.
9. Retry limitado, timeout, backoff e idempotência.
10. Auditoria em tabela separada com política append-only para a
    aplicação.
11. Injeção configurável de falhas para testes.
12. Execução local com Docker Compose.

### Fora do escopo inicial

- Plataforma de microsserviços.
- Kubernetes.
- Kafka, RabbitMQ ou outro broker de mensagens.
- Redis.
- PGVector ou outro banco vetorial.
- Agente com autonomia irrestrita ou planejamento aberto.
- Execução automática de procedimentos de correção em infraestrutura.
- Integração com uma ferramenta ITSM comercial real.
- Interface gráfica completa para operadores.
- Alta disponibilidade multi-região ou arquitetura de missão crítica.

Esses itens poderão ser reconsiderados somente quando houver requisito
concreto que os justifique.

## 5. Usuários e atores

- **Solicitante:** registra o incidente e pode fornecer informações
    complementares.
- **Agente de triagem:** componente lógico que coordena interpretação
    e consultas.
- **Analista de suporte:** recebe chamados classificados ou pendentes
    de análise manual.
- **Equipe técnica:** grupo responsável pelo serviço ou componente
    afetado.
- **Administrador:** mantém dados de referência e configurações do
    ambiente.

## 6. Fluxo funcional esperado

1. A API recebe um chamado e valida o contrato de entrada.
2. O chamado é persistido no estado `NOVO`.
3. O orquestrador inicia a triagem e registra a transição para
    `EM_TRIAGEM`.
4. O LLM interpreta a descrição e retorna dados estruturados.
5. A aplicação valida os dados extraídos e consulta CMDB/KEDB.
6. Se faltarem informações essenciais, o chamado passa para
    `PENDENTE_INFORMACAO`.
7. Com dados suficientes, o motor de regras calcula impacto, urgência e
    prioridade.
8. A aplicação determina a equipe por mapeamento configurado.
9. A integração atualiza o chamado usando chave de idempotência
    estável.
10. O resultado e as transições são registrados em auditoria.
11. O chamado passa para `CLASSIFICADO` quando a operação for concluída.

## 7. Requisitos funcionais

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

  RF-07                               Calcular prioridade por matriz
                                      configurável de impacto e urgência.

  RF-08                               Determinar equipe por mapeamento
                                      controlado de serviço para equipe.

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

Matriz inicial ilustrativa:

  Impacto  Urgência     Alta   Média   Baixa
  ------------------- ------ ------- -------
  Alto                    P1      P2      P2
  Médio                   P2      P3      P3
  Baixo                   P3      P4      P4

A matriz deverá ser validada como regra de negócio antes de ser
considerada definitiva. A origem e a validação dos valores de impacto e
urgência também deverão ser definidas.

### 9.2 Roteamento

O roteamento será determinado por uma configuração controlada que
relaciona `service_id` a `target_team`. Valores sugeridos pelo LLM não
serão aceitos como destino final sem validação.

### 9.3 Dados insuficientes

Quando não houver evidência suficiente para determinar serviço, impacto
ou urgência, o sistema não deverá inventar dados. O chamado deverá
passar para `PENDENTE_INFORMACAO` ou para revisão humana, conforme a
regra definida.

## 10. Critérios de aceite

A primeira versão será considerada funcional quando demonstrar:

- Criação e consulta de chamados.
- Extração estruturada pelo LLM e validação da resposta.
- Consulta ao CMDB e à KEDB.
- Cálculo de prioridade sem decisão autônoma do LLM.
- Roteamento validado pela aplicação.
- Transições válidas e rejeição de transições inválidas.
- Reentrada de chamado pendente após informação complementar.
- Reprocessamento controlado de erro de integração.
- Repetição da mesma operação com a mesma chave sem duplicação.
- Auditoria dos eventos relevantes.
- Testes para timeout, HTTP 500, resposta perdida após commit,
    concorrência e prompt injection.
- Execução local por Docker Compose.

## 11. Premissas e decisões pendentes

As decisões abaixo precisam ser confirmadas antes ou durante a
implementação:

- Provedor, modelo e política de uso do LLM.
- Critérios objetivos para classificar impacto e urgência.
- Conteúdo e regras definitivas da matriz de prioridade.
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
