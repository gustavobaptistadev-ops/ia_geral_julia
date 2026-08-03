# Handoff para o próximo agente de IA

## Estado atual do projeto

O projeto já possui uma base arquitetural funcional em FastAPI, com módulos separados para domínio, aplicação, infraestrutura e API. O fluxo conversacional está orquestrado, o agendamento já é tratado por uma camada de aplicação e a estrutura de persistência com PostgreSQL foi iniciada.

## O que já foi implementado

- Estrutura inicial do backend em FastAPI.
- Endpoints de saúde e conversação.
- Domínio para conversa, estado, clínica, paciente e agendamento.
- Máquina de estados para o fluxo principal.
- Conversation Engine com respostas iniciais e acolhimento.
- Decision Engine para detectar emergência e intenção de agendamento.
- Orquestrador de conversação integrado ao fluxo.
- Action Engine inicial para agendamento.
- Repositório inicial para persistência com PostgreSQL.
- Configuração por ambiente e suporte a containers.
- Testes automatizados cobrindo as principais camadas.

## Arquitetura atual

O projeto segue a direção proposta pelo produto:

- Conversation Engine: responsável por gerar respostas humanas e orientadas ao objetivo do atendimento.
- Decision Engine: responsável por decidir o próximo passo a partir do contexto.
- Action Engine: responsável por executar ações, como agendamento e integrações futuras.

## Próximo passo recomendado

1. Integrar a persistência real com PostgreSQL e criar o esquema inicial de tabelas.
2. Conectar o fluxo de agendamento à persistência, armazenando conversas, agendamentos e contexto.
3. Implementar a camada de integração com Google Calendar e notificações.
4. Evoluir para um modelo de configuração administrativa e fluxos configuráveis.
5. Preparar o sistema para memória persistente, logs e observabilidade.

## Diretrizes para as próximas IAs

- Nunca reescrever o projeto sem revisar o estado atual do repositório.
- Sempre preservar a arquitetura modular e o conjunto de testes.
- Não implementar regras de negócio diretamente no endpoint; elas devem entrar em camadas de aplicação ou domínio.
- Manter foco em experiência humana, contexto, memória e condução ao agendamento.
- Evitar lógica hardcoded para especialidades, clínicas ou fluxos específicos sem um modelo de configuração.
- Continuar com desenvolvimento incremental, com testes para cada nova etapa.

## Pontos de atenção permanentes

- O atendimento nunca deve parecer formulário ou chatbot.
- A IA nunca deve emitir diagnóstico ou tratamento.
- A conversa deve sempre responder primeiro e conduzir ao agendamento.
- Emergências devem interromper o fluxo automaticamente e priorizar apoio humano.

## Mensagem final para a próxima IA

Continue evoluindo o projeto de forma incremental, respeitando o que já foi implementado e avançando para a persistência real e as integrações externas. O foco agora é transformar o fluxo conversacional em uma jornada operacional, com armazenamento confiável e execução concreta de agendamentos.
