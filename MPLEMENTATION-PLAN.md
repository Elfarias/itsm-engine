# IMPLEMENTATION-PLAN.md — ITSM Agent

**Versão:** 1.0  
**Status:** Plano de implantação proposto  
**Escopo:** MVP local, com possibilidade de implantação futura em nuvem

---

## 1. Objetivo

Este documento define a sequência de implantação do ITSM Agent, desde a preparação do ambiente até a validação final.

O plano transforma as fases do projeto em atividades executáveis, com dependências, entregas e critérios objetivos de conclusão. A implementação será incremental: cada fase deverá ser validada antes do início da seguinte.

O objetivo do MVP é construir uma aplicação capaz de receber chamados, armazená-los, aplicar regras determinísticas e utilizar um LLM para apoiar a triagem, mantendo as decisões e operações sob controle da aplicação.

## 2. Princípios de execução

1. **Simplicidade:** adotar somente componentes necessários ao escopo.
2. **Entrega incremental:** implementar e validar pequenas partes funcionais.
3. **IA controlada:** o LLM interpreta e extrai informações; a aplicação valida e decide.
4. **Confiabilidade desde o início:** tratar idempotência, concorrência, auditoria e falhas como requisitos da arquitetura.
5. **Rastreabilidade:** manter código, documentação e decisões técnicas sincronizados.
6. **Aprendizado prático:** construir manualmente e compreender cada componente antes de automatizar ou abstrair.
7. **Critério de avanço:** não iniciar uma nova fase enquanto os critérios de conclusão da fase atual não forem atendidos.

## 3. Visão geral das fases

| Fase | Nome | Resultado esperado |
|---|---|---|
| 0 | Preparação e decisões técnicas | Decisões essenciais registradas |
| 1 | Preparação do ambiente | Ambiente local reproduzível |
| 2 | Persistência e modelo de dados | Banco estruturado e validado |
| 3 | API e regras de negócio | Núcleo funcional sem LLM |
| 4 | Confiabilidade e auditoria | Operações rastreáveis e seguras contra repetição |
| 5 | Integração com IA | Interpretação estruturada e validada |
| 6 | Orquestração da triagem | Fluxo completo de triagem |
| 7 | Testes de resiliência e segurança | Comportamento validado em cenários adversos |
| 8 | Empacotamento e implantação | Aplicação executável no ambiente-alvo |
| 9 | Validação final e documentação | Entrega reproduzível e demonstrável |

---

## 4. Plano detalhado de implantação

### 4.1. Fase 0 — Preparação e decisões técnicas

**Objetivo:** resolver as decisões que bloqueiam o início da implementação e estabelecer uma referência técnica única.

**Atividades:**

- [ ] 0.1. Revisar `PROJECT.md`, `README.md`, `ARCHITECTURE.md` e `TECHNOLOGY-STACK.md`.
- [ ] 0.2. Identificar divergências entre os documentos e registrar as decisões consolidadas.
- [ ] 0.3. Definir a versão suportada do Python.
- [ ] 0.4. Definir a versão e a imagem do PostgreSQL.
- [ ] 0.5. Escolher a estratégia de acesso ao banco e a ferramenta de migração.
- [ ] 0.6. Escolher o provedor e o modelo LLM.
- [ ] 0.7. Definir limites iniciais de timeout, tamanho de entrada e política de retry para chamadas ao LLM.
- [ ] 0.8. Definir a estrutura inicial de diretórios do projeto.
- [ ] 0.9. Definir convenções mínimas de código, nomes, configuração, logs e testes.
- [ ] 0.10. Registrar decisões técnicas relevantes em um ADR ou seção de decisões arquiteturais.

**Dependências:** nenhuma.

**Entregas:**

- Decisões técnicas essenciais documentadas.
- Estrutura inicial do repositório definida.
- Documentos de referência revisados.

**Critérios de conclusão:**

- [ ] Não existem decisões em aberto que impeçam a criação do ambiente.
- [ ] As versões e dependências principais estão definidas.
- [ ] O provedor LLM foi escolhido ou sua seleção foi explicitamente adiada para antes da Fase 5.
- [ ] O escopo do MVP permanece compatível com a arquitetura aprovada.

### 4.2. Fase 1 — Preparação do ambiente

**Objetivo:** criar um ambiente local reproduzível para desenvolvimento e testes.

**Atividades:**

- [ ] 1.1. Criar ou preparar o repositório Git.
- [ ] 1.2. Criar a estrutura inicial de diretórios.
- [ ] 1.3. Criar e ativar o ambiente virtual Python.
- [ ] 1.4. Criar o arquivo de dependências com versões fixadas.
- [ ] 1.5. Criar o esqueleto mínimo da aplicação FastAPI.
- [ ] 1.6. Criar o `Dockerfile` da aplicação.
- [ ] 1.7. Criar o `compose.yaml` para aplicação e PostgreSQL.
- [ ] 1.8. Criar `.env.example` e configurar o `.gitignore`.
- [ ] 1.9. Implementar leitura e validação das configurações.
- [ ] 1.10. Adicionar endpoint básico de health check.
- [ ] 1.11. Documentar os comandos efetivamente testados para iniciar e encerrar o ambiente.

**Dependências:** Fase 0.

**Entregas:**

- Repositório inicial.
- Aplicação FastAPI mínima.
- Ambiente Python configurado.
- Containers da aplicação e do PostgreSQL.
- Configuração local sem segredos versionados.

**Critérios de conclusão:**

- [ ] O ambiente inicia a partir das instruções documentadas.
- [ ] A API responde ao health check.
- [ ] A aplicação consegue estabelecer conexão com o PostgreSQL.
- [ ] Nenhum segredo real está presente no repositório.
- [ ] O ambiente pode ser encerrado e iniciado novamente sem perda inesperada de dados.

### 4.3. Fase 2 — Persistência e modelo de dados

**Objetivo:** implementar e validar a persistência necessária ao fluxo de triagem.

**Atividades:**

- [ ] 2.1. Definir o modelo relacional e as chaves das entidades.
- [ ] 2.2. Criar a tabela `tickets`.
- [ ] 2.3. Criar a tabela `cmdb`.
- [ ] 2.4. Criar a tabela `kedb`.
- [ ] 2.5. Criar a tabela `audit_events`.
- [ ] 2.6. Criar a estrutura de registro das chaves idempotentes e dos resultados das operações.
- [ ] 2.7. Definir índices e restrições de integridade necessários.
- [ ] 2.8. Implementar migrações versionadas do banco.
- [ ] 2.9. Definir dados mínimos de demonstração para CMDB, KEDB e chamados.
- [ ] 2.10. Testar criação, consulta, atualização e persistência dos registros.

**Dependências:** Fase 1.

**Entregas:**

- Modelo de dados implementado.
- Migrações versionadas.
- Dados de demonstração controlados.
- Testes básicos de persistência.

**Critérios de conclusão:**

- [ ] Todas as entidades necessárias ao MVP existem.
- [ ] Chaves, relacionamentos e restrições de integridade funcionam.
- [ ] Migrações podem ser aplicadas em um banco vazio.
- [ ] Os dados persistem após reinicialização dos containers.
- [ ] A tabela de auditoria é protegida contra atualização e exclusão pelo usuário normal da aplicação.

### 4.4. Fase 3 — API e regras de negócio

**Objetivo:** construir o núcleo determinístico da aplicação sem dependência do LLM.

**Atividades:**

- [ ] 3.1. Definir os contratos de entrada e saída da API.
- [ ] 3.2. Implementar schemas Pydantic.
- [ ] 3.3. Implementar endpoint para criação de chamado.
- [ ] 3.4. Implementar endpoint para consulta de chamado.
- [ ] 3.5. Implementar endpoint para atualização autorizada de chamado.
- [ ] 3.6. Implementar a máquina de estados e as transições permitidas.
- [ ] 3.7. Implementar validações de domínio.
- [ ] 3.8. Definir e implementar a regra determinística de prioridade, após validação da matriz de impacto e urgência.
- [ ] 3.9. Implementar respostas de erro consistentes.
- [ ] 3.10. Criar testes unitários para estados, validações e prioridade.

**Dependências:** Fase 2.

**Entregas:**

- Endpoints básicos de chamados.
- Contratos de API.
- Máquina de estados.
- Regras de negócio independentes de IA.

**Critérios de conclusão:**

- [ ] Chamados podem ser criados e consultados pela API.
- [ ] Entradas inválidas são rejeitadas com respostas consistentes.
- [ ] Transições não permitidas são bloqueadas.
- [ ] A prioridade é calculada por regra determinística validada.
- [ ] O fluxo básico funciona sem chamadas ao LLM.

### 4.5. Fase 4 — Confiabilidade e auditoria

**Objetivo:** impedir duplicidade, controlar concorrência e manter rastreabilidade das operações.

**Atividades:**

- [ ] 4.1. Definir quais operações exigem idempotência.
- [ ] 4.2. Definir uma chave estável por operação lógica, reutilizada em todas as tentativas.
- [ ] 4.3. Persistir a chave, o payload associado e o resultado da operação.
- [ ] 4.4. Rejeitar reutilização da mesma chave com payload incompatível.
- [ ] 4.5. Garantir que chamadas repetidas retornem o resultado já registrado sem repetir efeitos.
- [ ] 4.6. Coordenar a reserva da chave e a alteração de dados na mesma transação quando a operação ocorrer no PostgreSQL.
- [ ] 4.7. Implementar controle de concorrência para impedir atualizações conflitantes.
- [ ] 4.8. Registrar eventos relevantes em `audit_events`.
- [ ] 4.9. Propagar identificador de correlação pelas etapas do processamento.
- [ ] 4.10. Implementar tratamento centralizado de exceções e classificação de falhas.

**Dependências:** Fases 2 e 3.

**Entregas:**

- Mecanismo de idempotência.
- Controle de concorrência.
- Auditoria de eventos.
- Tratamento padronizado de falhas.

**Critérios de conclusão:**

- [ ] Repetir uma operação com a mesma chave não duplica seus efeitos.
- [ ] Reutilizar uma chave com payload diferente é rejeitado.
- [ ] Atualizações concorrentes não sobrescrevem silenciosamente umas às outras.
- [ ] Eventos relevantes podem ser associados ao chamado e à execução.
- [ ] Logs e auditoria não expõem segredos ou dados desnecessários.

### 4.6. Fase 5 — Integração com IA

**Objetivo:** adicionar a capacidade de interpretação de chamados por LLM sem transferir ao modelo o controle da aplicação.

**Atividades:**

- [ ] 5.1. Criar módulo isolado para comunicação com o provedor LLM.
- [ ] 5.2. Implementar configuração externa de endpoint, modelo, credencial e limites.
- [ ] 5.3. Definir o prompt de classificação e o formato de resposta esperado.
- [ ] 5.4. Implementar chamada com timeout e tratamento de erros transitórios.
- [ ] 5.5. Validar a resposta estruturada com Pydantic.
- [ ] 5.6. Rejeitar ou encaminhar para revisão respostas incompletas, inválidas ou fora do contrato.
- [ ] 5.7. Tratar descrição do chamado e documentos recuperados como dados não confiáveis.
- [ ] 5.8. Limitar o conteúdo enviado ao modelo e evitar exposição desnecessária de dados.
- [ ] 5.9. Implementar testes com respostas simuladas, sem depender de chamadas reais.
- [ ] 5.10. Registrar metadados úteis da execução, sem armazenar conteúdo sensível desnecessário.

**Dependências:** Fases 0, 1 e 3. A integração deve respeitar os contratos definidos na Fase 3.

**Entregas:**

- Adaptador de integração com LLM.
- Prompt e contrato de saída versionados.
- Validação de resposta.
- Tratamento de falhas e entradas não confiáveis.

**Critérios de conclusão:**

- [ ] O LLM retorna dados no formato esperado em cenários válidos.
- [ ] Respostas inválidas não alteram diretamente o chamado.
- [ ] Falhas e timeouts são tratados sem deixar o chamado em estado inconsistente.
- [ ] O modelo não possui acesso direto ao banco nem credenciais operacionais.
- [ ] Instruções presentes na descrição do chamado não conseguem alterar as regras ou permissões da aplicação.

### 4.7. Fase 6 — Orquestração da triagem

**Objetivo:** integrar interpretação, consultas de contexto, regras de negócio e atualização do chamado em um fluxo controlado.

**Atividades:**

- [ ] 6.1. Implementar o serviço de orquestração da triagem.
- [ ] 6.2. Carregar o chamado e validar seu estado atual.
- [ ] 6.3. Solicitar ao LLM a extração das informações previstas no contrato.
- [ ] 6.4. Consultar a CMDB para obter contexto do ativo e suas dependências.
- [ ] 6.5. Consultar a KEDB para identificar erros conhecidos e soluções documentadas.
- [ ] 6.6. Aplicar regras determinísticas de impacto, urgência e prioridade.
- [ ] 6.7. Identificar informações ausentes ou conflitantes.
- [ ] 6.8. Encaminhar chamados ambíguos para `PENDENTE_INFORMACAO` ou revisão humana, conforme regra definida.
- [ ] 6.9. Atualizar o chamado somente após validações e autorização da aplicação.
- [ ] 6.10. Registrar resultado, transições e correlação da execução.

**Dependências:** Fases 3, 4 e 5.

**Entregas:**

- Fluxo integrado de triagem.
- Consultas à CMDB e à KEDB.
- Aplicação das regras de prioridade.
- Atualização controlada do chamado.

**Critérios de conclusão:**

- [ ] Um chamado válido percorre o fluxo completo.
- [ ] O resultado do LLM é validado antes de ser utilizado.
- [ ] Prioridade e transições são decididas pela aplicação.
- [ ] Informações insuficientes não geram classificações arbitrárias.
- [ ] Cada execução relevante possui rastreabilidade.
- [ ] Uma falha não resulta em atualização parcial inconsistente.

### 4.8. Fase 7 — Testes de resiliência e segurança

**Objetivo:** validar o comportamento da aplicação em cenários normais, limites e falhas.

**Atividades:**

- [ ] 7.1. Completar testes unitários das regras de domínio.
- [ ] 7.2. Implementar testes de integração com PostgreSQL.
- [ ] 7.3. Simular timeout e indisponibilidade do LLM.
- [ ] 7.4. Simular respostas inválidas e incompletas do LLM.
- [ ] 7.5. Simular indisponibilidade e reinicialização do banco.
- [ ] 7.6. Testar retry e limites de tentativas.
- [ ] 7.7. Testar repetição de operações idempotentes.
- [ ] 7.8. Testar chamadas concorrentes para o mesmo chamado.
- [ ] 7.9. Testar prompt injection e conteúdo malicioso nos dados de entrada.
- [ ] 7.10. Verificar autorização, exposição de dados e tratamento de segredos.
- [ ] 7.11. Executar teste ponta a ponta do fluxo principal.
- [ ] 7.12. Corrigir defeitos e registrar limitações conhecidas.

**Dependências:** Fases 4, 5 e 6.

**Entregas:**

- Suíte de testes automatizados.
- Evidências dos cenários de falha.
- Registro de defeitos e limitações.

**Critérios de conclusão:**

- [ ] Testes críticos são executados de forma reproduzível.
- [ ] Falhas simuladas não provocam corrupção ou duplicidade de dados.
- [ ] O comportamento de recuperação é compatível com a máquina de estados.
- [ ] Entradas maliciosas não ampliam as permissões do modelo ou da aplicação.
- [ ] O fluxo principal passa no teste ponta a ponta.

### 4.9. Fase 8 — Empacotamento e implantação

**Objetivo:** preparar uma versão executável e implantá-la no ambiente definido.

**Atividades:**

- [ ] 8.1. Revisar o `Dockerfile` para execução adequada da aplicação.
- [ ] 8.2. Construir e testar a imagem Docker.
- [ ] 8.3. Definir usuário não privilegiado no container, quando compatível com a imagem e a execução.
- [ ] 8.4. Configurar health checks e dependências de inicialização.
- [ ] 8.5. Separar configuração de ambiente e segredos.
- [ ] 8.6. Definir persistência e backup do PostgreSQL para o ambiente-alvo.
- [ ] 8.7. Definir procedimento de implantação e atualização.
- [ ] 8.8. Definir procedimento de recuperação e restauração.
- [ ] 8.9. Validar logs e diagnósticos operacionais.
- [ ] 8.10. Implantar no ambiente escolhido e executar smoke tests.

**Dependências:** Fase 7. A preparação do empacotamento pode ocorrer antes, mas a implantação final depende da aprovação dos testes críticos.

**Entregas:**

- Imagem Docker validada.
- Configuração de execução.
- Procedimentos operacionais.
- Aplicação implantada no ambiente escolhido.

**Critérios de conclusão:**

- [ ] A imagem é construída de forma reproduzível.
- [ ] A aplicação inicia com configuração externa e sem segredos embutidos.
- [ ] Health checks refletem a condição real dos componentes relevantes.
- [ ] Backup e recuperação do banco foram testados ou documentados como limitação explícita do ambiente.
- [ ] A implantação foi validada por smoke tests.

### 4.10. Fase 9 — Validação final e documentação

**Objetivo:** consolidar o projeto como uma entrega técnica reproduzível e demonstrável.

**Atividades:**

- [ ] 9.1. Executar o cenário de aceitação ponta a ponta.
- [ ] 9.2. Atualizar o diagrama para refletir a implementação real.
- [ ] 9.3. Atualizar `README.md`, `PROJECT.md`, `ARCHITECTURE.md` e `TECHNOLOGY-STACK.md`.
- [ ] 9.4. Documentar instalação, configuração, execução e testes.
- [ ] 9.5. Registrar decisões arquiteturais e justificativas.
- [ ] 9.6. Documentar limitações conhecidas e riscos residuais.
- [ ] 9.7. Organizar evidências dos testes e da implantação.
- [ ] 9.8. Revisar o repositório para remover arquivos temporários, credenciais e configurações locais.
- [ ] 9.9. Criar uma versão/tag de referência do MVP.

**Dependências:** Fases 7 e 8.

**Entregas:**

- Documentação final coerente com o código.
- Diagrama atualizado.
- Evidências de validação.
- Versão identificável do MVP.

**Critérios de conclusão:**

- [ ] Uma pessoa consegue reproduzir o ambiente seguindo a documentação.
- [ ] O cenário ponta a ponta está demonstrado.
- [ ] Os documentos não descrevem funcionalidades que não foram implementadas.
- [ ] Limitações e decisões pendentes estão explícitas.
- [ ] O repositório não contém segredos ou artefatos locais indevidos.

---

## 5. Marcos de controle

| Marco | Condição para aprovação |
|---|---|
| M0 — Pronto para desenvolver | Decisões essenciais da Fase 0 concluídas |
| M1 — Ambiente funcional | API e PostgreSQL executando localmente |
| M2 — Núcleo persistente | Modelo de dados e migrações validados |
| M3 — Aplicação determinística | Chamados e regras funcionam sem LLM |
| M4 — Operações confiáveis | Idempotência, concorrência e auditoria validadas |
| M5 — IA integrada | Respostas estruturadas e validadas |
| M6 — Triagem funcional | Fluxo completo executado de ponta a ponta |
| M7 — MVP validado | Testes críticos de segurança e resiliência aprovados |
| M8 — Implantado | Aplicação implantada e smoke tests aprovados |
| M9 — Entrega concluída | Documentação, evidências e versão final publicadas |

## 6. Dependências e caminho crítico

A sequência principal é:

```text
Fase 0
  |
Fase 1
  |
Fase 2
  |
Fase 3
  |
Fase 4 ------ Fase 5
  |              |
  +-------+------+
          |
        Fase 6
          |
        Fase 7
          |
        Fase 8
          |
        Fase 9
```

A Fase 5 pode ser preparada em paralelo com atividades finais da Fase 4, desde que os contratos da API e os controles de segurança já estejam definidos. A orquestração da Fase 6 depende dos componentes anteriores.

Não é necessário criar um cronograma em dias antes de conhecer a disponibilidade de desenvolvimento e o ritmo de validação. Os marcos e critérios de saída são a referência de progresso.

## 7. Regras técnicas que não podem ser flexibilizadas

1. O LLM não acessa diretamente o banco de dados.
2. O LLM não decide sozinho prioridade, estado ou autorização de operações.
3. Toda resposta do LLM é tratada como entrada não confiável e validada pela aplicação.
4. A mesma operação lógica reutiliza a mesma chave idempotente em todas as tentativas.
5. Operações repetidas não podem produzir efeitos duplicados.
6. Alterações relevantes devem gerar eventos de auditoria.
7. Falhas de integração não podem deixar o chamado em estado inconsistente.
8. Dados de CMDB e KEDB fornecem contexto; regras determinísticas definem o resultado.
9. Não adicionar PGVector, Redis, Kafka, Kubernetes ou microsserviços sem requisito concreto e decisão documentada.
10. A documentação deve refletir o comportamento efetivamente implementado.

## 8. Fora do escopo do MVP

- Interface gráfica ou portal completo para usuários.
- Integração com uma plataforma ITSM corporativa real.
- Alta disponibilidade e arquitetura multi-região.
- Kubernetes e orquestração avançada de containers.
- Mensageria distribuída.
- Busca vetorial com PGVector.
- Agentes autônomos com permissões amplas.
- Automação de ações de infraestrutura em produção.

Esses itens poderão ser avaliados em versões futuras, mediante necessidade demonstrada.

## 9. Riscos e decisões pendentes

| Item | Tratamento |
|---|---|
| Provedor e modelo LLM | Selecionar antes da Fase 5 |
| Matriz de impacto e urgência | Validar regra de prioridade antes da Fase 3 |
| Estratégia de acesso ao banco | Definir na Fase 0 |
| Autenticação e autorização da API | Definir antes de expor a API fora do ambiente local |
| Dados de demonstração | Utilizar dados fictícios, sem informações pessoais reais |
| Persistência e backup em produção | Definir conforme o ambiente de implantação |
| Custos do LLM | Estabelecer limites e acompanhar consumo desde a integração |

## 10. Definição de sucesso

O MVP será considerado concluído quando demonstrar, de forma reproduzível:

- Recebimento, validação e persistência de chamados.
- Consulta contextual à CMDB e à KEDB.
- Interpretação estruturada de chamados por LLM.
- Separação entre interpretação probabilística e regras determinísticas.
- Controle de estados, prioridade e operações autorizadas.
- Idempotência, auditoria e tratamento de falhas.
- Testes automatizados dos fluxos principais e dos cenários críticos.
- Execução em containers e implantação documentada.
- Documentação coerente com a implementação real.

**Marco técnico principal:** primeiro construir uma aplicação que recebe, valida, armazena e controla chamados corretamente sem IA. Em seguida, integrar o LLM como componente de interpretação, sem comprometer a confiabilidade do núcleo.

---

## 11. Forma de condução

A implantação será conduzida em ciclos curtos. Para cada atividade:

1. Explicar o objetivo e as decisões envolvidas.
2. Orientar a implementação manual.
3. Executar e observar o comportamento.
4. Validar o resultado com testes.
5. Atualizar a documentação.
6. Registrar pendências e obter aprovação antes de avançar.

O avanço será controlado pelos critérios de conclusão de cada fase, e não apenas pela quantidade de tarefas executadas.