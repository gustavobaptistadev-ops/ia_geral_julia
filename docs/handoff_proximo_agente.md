# Handoff para o próximo agente de IA

## Estado atual do projeto

O projeto avançou para a segunda camada arquitetural com sucesso. A base inicial do FastAPI foi criada, o domínio da conversa foi modelado e um Conversation Engine inicial já está implementado e validado com testes.

## O que já foi implementado

- Estrutura inicial do backend em FastAPI.
- Endpoints de saúde e aplicação base.
- Modelo de domínio para estado da conversa.
- Máquina de estados para evolução do fluxo.
- Conversation Engine com respostas iniciais, acolhimento e tratamento de emergência.
- Testes unitários cobrindo saúde, estado da conversa e engine de conversa.

## Arquitetura atual

O projeto segue a direção proposta pelo produto:

- Conversation Engine: responsável por gerar respostas humanas e orientadas ao objetivo do atendimento.
- Decision Engine: ainda precisa ser implementado como próxima evolução.
- Action Engine: ainda precisa ser implementado para integrações e agendamentos.

## Próximo passo recomendado

1. Implementar o Decision Engine para decidir qual etapa seguir com base no estado e no contexto.
2. Criar um fluxo principal de atendimento com etapas claras: greeting, discover_reason, discover_symptoms, confirm_appointment, collect_information, check_calendar e book_appointment.
3. Introduzir abstrações para ações futuras, como calendário, mensagens e persistência.
4. Evoluir para um modelo de integração com PostgreSQL e serviços externos.

## Diretrizes para as próximas IAs

- Nunca reescrever o projeto sem revisar o estado atual do repositório.
- Sempre preservar a arquitetura modular e os testes existentes.
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

Continue evoluindo o projeto de forma incremental, respeitando o que já foi implementado e ampliando a arquitetura para o Decision Engine e o Action Engine. O foco agora é transformar o fluxo conversacional em uma jornada mais completa, com decisões claras e ações reais.
