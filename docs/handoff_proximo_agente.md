# Handoff para o proximo agente de IA

## Estado atual do projeto

Projeto FastAPI da LifelineOne IA com foco na atendente Julia. A estrutura esta modularizada em dominio, aplicacao, infraestrutura e API. O fluxo principal ja consegue acolher sintomas, entender contexto basico, sugerir agendamento, coletar nome/telefone, apresentar horarios de forma natural, confirmar consulta e lidar com casos administrativos ou de emergencia.

## O que foi implementado ate aqui

- Backend FastAPI com endpoints de saude, login e conversas.
- Persistencia em memoria e PostgreSQL.
- Script local de chat com reset de conversas e indicador "Julia esta escrevendo...".
- `ConversationContext` tipado para organizar contexto clinico, paciente, calendario e flags da conversa.
- `MessageUnderstandingEngine` para extrair sintomas, duracao, gravidade, progressao, objetivo do paciente e prontidao para agendamento.
- `DecisionEngine` para decidir a proxima etapa com base no contexto.
- `ResponseAgent` como fachada de resposta.
- `VoiceAgent` para centralizar tom de voz, mensagens por etapa e formatacao de horarios.
- `AgendaAgent` para horarios, ordenacao e interpretacao natural de escolhas como "segunda", "de tarde" e "pode ser este mesmo".
- `PatientAgent` para extrair nome, telefone e campos pendentes.
- `AdministrativeAgent` para pedidos de exame, encaminhando para Laboratorio Life.
- `AppointmentBookingAgent` para criar consulta, gerar evento e persistir agendamento.
- `SafetyEngine` para urgencias e pedidos inseguros de medicacao/diagnostico.
- Simulador de pacientes com relatorio Markdown em `scripts/simulate_patients.py`.

## Comandos uteis

Rodar toda a suite:

```powershell
Set-Location -LiteralPath 'D:\GUSTAVO\NOVOS PROJETOS\ia'; .\.venv\Scripts\python.exe -m pytest
```

Abrir chat local com suite, PostgreSQL e reset:

```powershell
Set-Location -LiteralPath 'D:\GUSTAVO\NOVOS PROJETOS\ia'; powershell -ExecutionPolicy Bypass -File .\scripts\start_chat.ps1
```

Simular pacientes e gerar relatorio:

```powershell
Set-Location -LiteralPath 'D:\GUSTAVO\NOVOS PROJETOS\ia'; powershell -ExecutionPolicy Bypass -File .\scripts\simulate_patients.ps1
```

Relatorio local gerado:

```text
D:\GUSTAVO\NOVOS PROJETOS\ia\reports\ia_simulation_report.md
```

## Ultima validacao

- Suite completa: `123 passed, 30 warnings`.
- Simulador: `6/6 cenarios sem achados`.

## Arquitetura atual recomendada

- `ConversationOrchestrator`: coordena o fluxo e delega responsabilidades.
- `MessageUnderstandingEngine`: entende a mensagem e atualiza contexto.
- `DecisionEngine`: decide a proxima etapa.
- `VoiceAgent`: define como Julia fala.
- `ResponseAgent`: monta payload de resposta usando o VoiceAgent.
- `AgendaAgent`: interpreta e organiza horarios.
- `PatientAgent`: extrai dados do paciente.
- `AdministrativeAgent`: trata pedidos fora da consulta, como exames.
- `AppointmentBookingAgent`: confirma e persiste consulta.
- `SafetyEngine`: protege casos de risco.

## Proximos passos recomendados

1. Evoluir o `VoiceAgent` com frases mais humanas por etapa, mantendo testes exatos para cada ajuste aprovado.
2. Criar ou fortalecer um `ContextAgent` para separar fatos confirmados, fatos inferidos, campos pendentes e nivel de confianca.
3. Criar um `ClinicalTriageAgent` para concentrar regras de gravidade, tempo prolongado, piora e sinais de alerta.
4. Adicionar um `HumanizationAgent` simples para revisar a resposta final antes de enviar, removendo repeticoes e melhorando naturalidade.
5. Melhorar o simulador para exibir quais fatos foram usados na decisao da proxima pergunta.
6. Depois de aprovar o tom, atualizar as mensagens para portugues com acentuacao correta de forma consistente.

## Cuidados permanentes

- Nao transformar o atendimento em menu, formulario ou fluxo engessado.
- Nao perguntar de novo algo que ja foi informado pelo paciente.
- Nao dar diagnostico, prescricao ou orientacao medica insegura.
- Emergencias devem interromper o fluxo e orientar atendimento urgente.
- Manter desenvolvimento incremental, com testes antes de cada commit.
- Nao colocar regras novas diretamente no endpoint; usar agentes ou camadas de aplicacao.

## Observacoes para o proximo agente

O proximo refinamento mais seguro e mexer no `VoiceAgent`, porque agora ele concentra as frases e formatacoes. Para mudancas de inteligencia contextual, comece pelo `MessageUnderstandingEngine` e depois extraia um `ContextAgent`, sempre usando o simulador como rede de seguranca.
