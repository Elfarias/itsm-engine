# TECHNOLOGY-STACK.md — ITSM Agent

Versão: 1.0\
Status: Stack proposto para a primeira versão

## 1. Diretriz

O stack foi selecionado para implementar uma aplicação modular, de baixa complexidade operacional, com integração a LLM, persistência relacional e mecanismos explícitos de confiabilidade.

A seleção prioriza tecnologias maduras e conhecidas. Não serão adicionadas ferramentas apenas para aumentar a quantidade de componentes ou demonstrar sofisticação.

## 2. Stack aprovado para a primeira versão

| Camada         | Tecnologia          | Uso                                            |
| -------------- | ------------------- | ---------------------------------------------- |
| Linguagem      | Python              | Implementação da aplicação                     |
| API            | FastAPI             | Endpoints REST                                 |
| Validação      | Pydantic            | Contratos, schemas e configurações             |
| Persistência   | PostgreSQL          | Chamados, CMDB, KEDB, auditoria e idempotência |
| IA             | LLM via API externa | Interpretação e extração estruturada           |
| Resiliência    | Tenacity            | Retry e exponential backoff                    |
| Containers     | Docker              | Empacotamento                                  |
| Ambiente local | Docker Compose      | Execução integrada dos containers              |
| Testes         | pytest              | Testes unitários e de integração               |

As versões específicas deverão ser fixadas no arquivo de dependências após validação de compatibilidade e segurança. Este documento não estabelece números de versão ainda não testados.

## 3. Justificativa por tecnologia

### 3.1. Python

Adequado para integração com APIs, processamento de dados, bibliotecas de IA e implementação de regras de negócio. Permite manter o projeto em uma única linguagem.

### 3.2. FastAPI

Fornece API REST, integração natural com Pydantic e documentação OpenAPI. É suficiente para a camada HTTP da primeira versão.

### 3.3. Pydantic

Valida dados de entrada, respostas estruturadas do LLM e configurações. A validação de schema não substitui validações de domínio, autorização ou proteção contra prompt injection.

### 3.4. PostgreSQL

Concentra a persistência relacional. Atende aos dados de chamados, CMDB, KEDB, eventos de auditoria e chaves idempotentes.

A busca inicial será realizada por SQL e recursos textuais nativos do PostgreSQL. PGVector não será instalado nesta fase.

### 3.5. LLM via API

O modelo será utilizado para interpretar linguagem natural e extrair informações estruturadas. O provedor, modelo, limites de uso, política de retenção de dados e custos ainda precisam ser selecionados.

A aplicação deverá encapsular a integração para reduzir acoplamento ao fornecedor.

### 3.6. Tenacity

Implementa políticas de repetição com limites e backoff. Deve ser configurada para repetir apenas falhas transitórias. Não fornece idempotência automaticamente.

### 3.7. Docker e Docker Compose

Docker empacota a aplicação e o banco para execução reproduzível. Docker Compose integra os containers no ambiente local de desenvolvimento.

### 3.8. pytest

Será utilizado para testes unitários, de integração e de confiabilidade. Testes de regras de negócio não devem depender de chamadas reais ao LLM.

## 4. Tecnologias e componentes fora do escopo inicial

| Tecnologia / componente        | Decisão                   | Justificativa                                                                         |
| ------------------------------ | ------------------------- | ------------------------------------------------------------------------------------- |
| PGVector                       | Não utilizar inicialmente | Busca vetorial ainda não demonstrou necessidade                                       |
| Redis                          | Não utilizar              | Não há requisito atual de cache ou coordenação distribuída                            |
| Kafka / RabbitMQ               | Não utilizar              | O fluxo inicial pode ser executado sem broker                                         |
| Kubernetes                     | Não utilizar              | Docker Compose atende ao desenvolvimento; produção poderá usar containers gerenciados |
| Microsserviços                 | Não utilizar              | Módulos internos são suficientes para o escopo                                        |
| Framework de agentes autônomos | Não utilizar inicialmente | Orquestração explícita em Python oferece maior previsibilidade                        |
| Banco NoSQL                    | Não utilizar              | PostgreSQL atende ao modelo de dados previsto                                         |

A exclusão não significa que essas tecnologias sejam inadequadas em qualquer cenário. Significa apenas que não há requisito que justifique sua adoção agora.

## 5. Bibliotecas auxiliares previstas

Bibliotecas adicionais só deverão ser incluídas quando necessárias:

- Driver PostgreSQL compatível com a estratégia de acesso a dados escolhida.
- Biblioteca de migração de schema, caso seja adotado controle formal de migrações.
- Cliente HTTP para integração com APIs externas.
- SDK oficial do provedor LLM, se oferecer benefício claro sobre HTTP direto.

Evitar dependências duplicadas para a mesma responsabilidade.

## 6. Configuração e segredos

### 6.1. Desenvolvimento

- Configuração por variáveis de ambiente.
- `.env` local excluído do controle de versão.
- `.env.example` contendo apenas nomes e valores ilustrativos, sem credenciais reais.
- Pydantic Settings para leitura e validação das configurações.

### 6.2. Produção

- Serviço gerenciado de segredos da nuvem escolhida.
- Credenciais de privilégio mínimo.
- Rotação conforme capacidade do serviço e política operacional.
- Proibição de registrar tokens e segredos em logs.

## 7. Observabilidade e auditoria

A primeira versão deverá registrar logs estruturados suficientes para diagnosticar:

- Identificador do chamado.
- Identificador de correlação da execução.
- Etapa do processamento.
- Tentativa de integração.
- Resultado e duração de chamadas externas.
- Transições de estado.
- Erros e exceções relevantes.

Eventos de negócio e decisões serão registrados em `audit_events`. Logs técnicos não substituem a auditoria de negócio.

Não será introduzida uma plataforma externa de observabilidade nesta fase. A necessidade poderá ser reavaliada na implantação.

## 8. Execução e implantação

### 8.1. Desenvolvimento

- Docker Compose.
- Container da aplicação.
- Container PostgreSQL.
- LLM consumido externamente por API.

### 8.2. Produção futura

A plataforma de nuvem ainda não foi definida. A aplicação deverá permanecer compatível com execução em containers e poderá ser implantada em um serviço gerenciado, como AWS ECS ou Azure Container Apps.

A escolha final dependerá de custo, disponibilidade, rede, identidade, gerenciamento de segredos e requisitos operacionais.

## 9. Critérios para inclusão de novas tecnologias

Uma tecnologia nova somente poderá ser adicionada quando:

1. Existir requisito funcional ou operacional claro.
2. O stack atual não atender adequadamente.
3. O benefício superar custo e complexidade.
4. Houver capacidade de operação e manutenção.
5. A decisão estiver documentada e justificada.

## 10. Decisões ainda pendentes

- Versão suportada do Python.
- Versão e imagem do PostgreSQL.
- Driver e estratégia de acesso ao banco.
- Ferramenta de migração de schema.
- Provedor e modelo LLM.
- Plataforma de nuvem de destino.
- Estratégia de autenticação e gerenciamento de segredos em produção.