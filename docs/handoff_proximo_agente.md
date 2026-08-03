# Handoff para o próximo agente de IA

## Contexto do projeto

Este workspace está vazio no momento, o que indica que ainda não existe uma implementação real do projeto LifelineOne IA. O objetivo aqui é não recriar o projeto do zero, mas construir a implementação de forma incremental a partir de uma arquitetura bem definida.

## O que já foi definido

- O produto é uma plataforma SaaS de atendimento humanizado via WhatsApp.
- A arquitetura deve seguir três motores: Conversation Engine, Decision Engine e Action Engine.
- O foco principal é conduzir o paciente até o agendamento.
- A solução deve ser modular, escalável, segura e pronta para produção.
- O projeto deve evoluir com base em configuração administrativa e não em regras fixas no código.

## O que precisa ser feito primeiro

1. Confirmar se há um projeto existente no workspace.
2. Se não houver, iniciar a implementação a partir de uma base arquitetural limpa.
3. Criar a estrutura inicial do backend em Python com FastAPI.
4. Definir os domínios de conversa, estado, memória e agendamento.
5. Implementar os primeiros testes antes de expandir funcionalidades.

## Diretrizes obrigatórias

- Nunca reescrever o projeto sem verificar o estado real do workspace.
- Nunca criar soluções rápidas que comprometam a arquitetura.
- Sempre manter separação entre domínio, aplicação, infraestrutura e interfaces.
- Sempre priorizar testes, segurança, observabilidade e extensibilidade.
- Nunca implementar regras específicas no código quando a intenção for configurável pelo painel.

## Ordem de trabalho recomendada

1. Estruturar o backend com FastAPI.
2. Definir modelos de domínio para conversa, paciente, clínica e agendamento.
3. Implementar persistência com PostgreSQL.
4. Criar o estado da conversa e a máquina de estados.
5. Implementar o Conversation Engine com resposta natural e contexto.
6. Implementar o Decision Engine com base no estado atual.
7. Implementar o Action Engine para agendamento e integrações.
8. Adicionar testes unitários e de integração.
9. Evoluir para painel administrativo e configurações dinâmicas.

## Pontos de atenção

- O sistema deve parecer humano e não como um formulário.
- A IA nunca deve emitir diagnóstico ou tratamento.
- O fluxo principal sempre deve conduzir ao agendamento.
- A memória precisa ser permanente e confirmada por identidade.
- O agendamento deve usar disponibilidade real do Google Calendar.

## Mensagem final para o próximo agente

Continue o projeto de forma incremental, respeitando a arquitetura proposta e sem atropelar a evolução. O foco inicial deve ser a base estrutural e o fluxo principal de conversa, não a implementação completa do painel administrativo.
