# Plano de implementação — LifelineOne IA

## 1. Objetivo geral

Construir o LifelineOne IA como uma plataforma SaaS modular, escalável e pronta para produção, com arquitetura baseada em três motores:

- Conversation Engine: responsável por conduzir a conversa de forma humana, contextualizada e natural.
- Decision Engine: responsável por decidir o próximo passo da jornada com base em regras, contexto e estado da conversa.
- Action Engine: responsável por executar ações externas, como agendamento, integração com calendário, armazenamento e notificações.

A implementação deve preservar um padrão de arquitetura sólido, com baixo acoplamento, alta coesão e evolução incremental.

## 2. Estratégia de execução por etapas

### Etapa 1 — Fundamentos arquiteturais

Objetivo:
- Definir a estrutura base do projeto.
- Estabelecer separação entre domínios, aplicação, infraestrutura e interfaces.
- Preparar a base para evolução sem acoplamento excessivo.

Entregáveis:
- Estrutura de pastas organizada por camadas.
- Definição de entidades de domínio, casos de uso e interfaces de repositório.
- Configuração inicial do FastAPI.
- Configuração do PostgreSQL e ambiente de execução.
- Estrutura base para logging, observabilidade e configurações.

Prioridades:
- Criar uma base limpa e extensível.
- Evitar qualquer implementação de negócio muito cedo sem a estrutura correta.

### Etapa 2 — Modelo de conversação e estado da sessão

Objetivo:
- Modelar o fluxo da conversa como uma máquina de estados.
- Representar contexto, memória, histórico e resumo por sessão.
- Definir o ciclo de vida de uma conversa.

Entregáveis:
- Estado de conversa.
- Máquina de estados para fluxos principais.
- Estrutura de contexto e memória persistente.
- Persistência de histórico e eventos.

Prioridades:
- Garantir que a conversa preserve contexto entre mensagens.
- Definir como a IA mantém memória sem perder consistência.

### Etapa 3 — Conversation Engine

Objetivo:
- Criar o motor responsável por gerar respostas naturais, acolhedoras e orientadas ao objetivo do atendimento.

Entregáveis:
- Serviço de geração de resposta.
- Política de estilo de conversa.
- Regras de comportamento humano, sem repetição, sem formularios e com uma pergunta por mensagem.
- Integração com o modelo de linguagem escolhido.

Prioridades:
- A IA deve responder primeiro e conduzir ao agendamento.
- O comportamento deve parecer humano e não como chatbot.

### Etapa 4 — Decision Engine

Objetivo:
- Separar a decisão do fluxo da execução.
- Determinar qual etapa seguir com base no contexto da conversa.

Entregáveis:
- Motor de decisão para fluxos: greeting, discover_reason, discover_symptoms, confirm_appointment, collect_information, check_calendar, book_appointment, finished.
- Suporte a fluxos alternativos: emergência, cancelar, remarcar, follow-up, paciente antigo, áudio e imagem.
- Regras de prioridade e escalonamento.

Prioridades:
- O Decision Engine não deve executar ações diretamente.
- Deve apenas decidir o próximo passo.

### Etapa 5 — Action Engine

Objetivo:
- Encapsular todas as operações externas e de integração.

Entregáveis:
- Integração com PostgreSQL.
- Integração com Redis.
- Integração com Google Calendar.
- Serviço de envio de mensagens e notificações.
- Registro de logs, eventos e auditoria.

Prioridades:
- Centralizar integrações e reduzir acoplamento com o resto do sistema.
- Garantir tratamento de erros e retries quando necessário.

### Etapa 6 — Segurança, observabilidade e produção

Objetivo:
- Preparar o sistema para ambiente real.

Entregáveis:
- Autenticação e autorização.
- Logs estruturados.
- Métricas e rastreio.
- Configurações por ambiente.
- Containers Docker.
- Documentação operacional.

Prioridades:
- O sistema precisa operar com segurança e rastreabilidade.
- Preparar para implantação com boa observabilidade.

### Etapa 7 — Painel administrativo e configuração dinâmica

Objetivo:
- Permitir que clínicas configurem comportamento sem alterar código.

Entregáveis:
- Modelos para clínicas, especialidades, médicos, fluxos, prompts, regras, mensagens automáticas, follow-up, FAQ e permissões.
- API administrativa para gerenciamento.
- Lógica baseada em configuração e não em regras hardcoded.

Prioridades:
- Garantir extensibilidade para novas especialidades e cenários.

## 3. Regras de implementação

- Nunca implementar uma funcionalidade sem entender a arquitetura existente.
- Nunca criar duplicação de código.
- Nunca introduzir regra específica no código sem modelo de configuração.
- Nunca sobrescrever componentes já existentes sem análise.
- Sempre manter testes unitários e de integração para novas funcionalidades.
- Sempre documentar mudanças relevantes.

## 4. Ordem recomendada de desenvolvimento

1. Estrutura base da aplicação.
2. Domínio e modelos de conversa.
3. Persistência e repositórios.
4. Conversation Engine.
5. Decision Engine.
6. Action Engine.
7. Integrações externas.
8. Painel administrativo.
9. Segurança e produção.

## 5. Critérios de pronto para evolução

O projeto estará preparado para a próxima etapa quando:

- a arquitetura estiver separada por camadas claras;
- os motores estiverem isolados;
- o fluxo conversacional estiver representado por estado;
- a persistência e as integrações estiverem desacopladas;
- o sistema puder evoluir com novas clínicas, especialidades e regras sem reescrita de código.

## 6. Guia para o próximo agente de IA

O próximo agente deve continuar a implementação respeitando esta ordem:

- validar a estrutura existente antes de qualquer alteração;
- manter compatibilidade com o que já foi implementado;
- preferir evolução incremental em vez de reescrita;
- não introduzir lógica de negócio diretamente no endpoint ou no modelo;
- manter o foco em arquitetura, testes e extensibilidade.

## 7. Checklist de continuidade

- [ ] Verificar se existe um projeto real no workspace.
- [ ] Identificar os arquivos e módulos existentes.
- [ ] Definir a estrutura arquitetural atual.
- [ ] Implementar a primeira camada de domínio e infraestrutura.
- [ ] Criar testes para o fluxo principal.
- [ ] Expandir para integrações e painel administrativo.
