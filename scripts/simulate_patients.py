from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from unicodedata import combining, normalize

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.application.orchestrator.service import ConversationOrchestrator
from app.domain.conversation.models import ConversationState


@dataclass(slots=True)
class Scenario:
    name: str
    goal: str
    messages: list[str]
    expected_final_steps: set[str] = field(default_factory=set)
    must_contain: list[str] = field(default_factory=list)
    must_not_contain: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Turn:
    patient: str
    julia: str
    step: str
    handoff: bool


@dataclass(slots=True)
class ScenarioResult:
    scenario: Scenario
    turns: list[Turn]
    final_context: dict[str, Any]
    findings: list[str]
    suggestions: list[str]


SCENARIOS = [
    Scenario(
        name="Alergia prolongada com agendamento",
        goal="Validar se Julia entende duracao longa e conduz para agenda sem perguntas repetidas.",
        messages=[
            "oi",
            "to com alergia, tem uns 2 meses",
            "sim",
            "Gustavo Henrique",
            "61991773474",
            "segunda",
            "pode ser este mesmo",
            "ok",
        ],
        expected_final_steps={"finished", "book_appointment"},
        must_contain=["Horario:", "Endereco:"],
        must_not_contain=["Escolha 1", "1.", "2.", "3."],
    ),
    Scenario(
        name="Cabelo caindo com pedido direto",
        goal="Validar se Julia usa sintoma e intencao da mesma mensagem antes de perguntar o proximo dado faltante.",
        messages=[
            "estou com cabelo caindo a alguns dias quero marcar uma consulta",
            "incomodando bastante",
            "sim",
            "Ana Silva 11999999999",
            "prefiro segunda de tarde",
        ],
        expected_final_steps={"book_appointment"},
        must_contain=["Horario:", "10/08/2026"],
        must_not_contain=["qual sintoma ou motivo principal"],
    ),
    Scenario(
        name="Dados incompletos do paciente",
        goal="Validar se Julia confirma o nome recebido e pede somente o telefone faltante.",
        messages=[
            "coceira nos dedos tem 3 dias e incomoda muito",
            "sim",
            "gustavo henrique baptista santana",
            "61991773474",
            "pode ser de tarde",
        ],
        expected_final_steps={"book_appointment"},
        must_contain=["Agora falta so o WhatsApp/Telefone"],
    ),
    Scenario(
        name="Horario ambiguo",
        goal="Validar se Julia nao confirma automaticamente quando ha mais de um horario no mesmo dia e entende pergunta por hora indisponivel.",
        messages=[
            "alergia tem 3 dias e esta incomodando muito",
            "sim",
            "Maria Oliveira 11988887777",
            "segunda",
            "tem as 15 horas?",
            "segunda de tarde",
        ],
        expected_final_steps={"book_appointment"},
        must_contain=["Tenho mais de um horario nesse dia", "Na segunda-feira as 15h eu nao encontrei disponivel"],
    ),
    Scenario(
        name="Exame",
        goal="Validar se Julia encaminha exame para laboratorio parceiro e pergunta se pode ajudar em algo mais.",
        messages=["exame"],
        expected_final_steps={"greeting"},
        must_contain=["Laboratorio Life", "61999999999", "Connect Tower", "Posso te auxiliar em algo mais?"],
    ),
    Scenario(
        name="Emergencia",
        goal="Validar se Julia interrompe o fluxo quando existe sinal de urgencia.",
        messages=["tenho um prego no pe"],
        expected_final_steps={"emergency"},
        must_contain=["lesao perfurante"],
    ),
]

STRATEGIC_REFINEMENT_SUGGESTIONS = [
    "Refinar o VoiceAgent com tom de voz por etapa, variacao de acolhimentos e frases menos mecanicas.",
    "Evoluir o ContextAgent para manter fatos confirmados do paciente, fatos inferidos e campos pendentes com nivel de confianca.",
    "Adicionar um HumanizationAgent simples para revisar a resposta final antes de enviar, removendo repeticoes e deixando a frase mais natural.",
    "Separar criterios clinicos em ClinicalTriageAgent, mantendo regras de seguranca explicitas e testaveis.",
    "Registrar no relatorio quais fatos a IA usou para decidir a proxima pergunta, facilitando auditoria do contexto.",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Simula conversas de pacientes com a Julia e gera relatorio.")
    parser.add_argument(
        "--report",
        default=str(PROJECT_ROOT / "reports" / "ia_simulation_report.md"),
        help="Caminho do relatorio Markdown gerado.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Nao imprime as conversas completas no terminal.",
    )
    args = parser.parse_args()

    results = [run_scenario(scenario) for scenario in SCENARIOS]
    report = build_report(results)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    if not args.quiet:
        print_transcripts(results)

    print("")
    print(f"Relatorio gerado em: {report_path}")
    print(summary_line(results))


def run_scenario(scenario: Scenario) -> ScenarioResult:
    orchestrator = ConversationOrchestrator()
    state: ConversationState | None = None
    conversation_id = scenario.name.lower().replace(" ", "-")
    turns: list[Turn] = []

    for message in scenario.messages:
        result = orchestrator.handle_message(message, state, conversation_id=conversation_id)
        state = result["state"]
        reply = result["reply"]
        turns.append(
            Turn(
                patient=message,
                julia=str(reply["message"]),
                step=step_value(reply["next_step"]),
                handoff=bool(reply["should_handoff"]),
            )
        )

    final_context = state.context if state is not None else {}
    findings, suggestions = analyze_result(scenario, turns)
    return ScenarioResult(
        scenario=scenario,
        turns=turns,
        final_context=final_context,
        findings=findings,
        suggestions=suggestions,
    )


def analyze_result(scenario: Scenario, turns: list[Turn]) -> tuple[list[str], list[str]]:
    findings: list[str] = []
    suggestions: list[str] = []
    full_text = "\n".join(turn.julia for turn in turns)
    final_step = turns[-1].step if turns else ""

    if scenario.expected_final_steps and final_step not in scenario.expected_final_steps:
        findings.append(f"Terminou em etapa inesperada: {final_step}.")
        suggestions.append("Revisar DecisionEngine para este roteiro e garantir avanco quando o contexto ja estiver suficiente.")

    for expected_text in scenario.must_contain:
        if expected_text.lower() not in full_text.lower():
            findings.append(f"Nao encontrei no atendimento: {expected_text}.")
            suggestions.append("Ajustar ResponseAgent para preservar informacoes obrigatorias desse tipo de atendimento.")

    for forbidden_text in scenario.must_not_contain:
        if forbidden_text.lower() in full_text.lower():
            findings.append(f"Encontrado formato indesejado: {forbidden_text}.")
            suggestions.append("Remover resquicios de menu numerado e manter selecao de horarios em linguagem natural.")

    repeated_question = detect_repeated_question(turns)
    if repeated_question:
        findings.append(f"Pergunta repetida detectada: {repeated_question}.")
        suggestions.append("Reforcar MessageUnderstandingEngine para marcar campos ja respondidos e evitar perguntar de novo.")

    known_context_question = detect_question_about_known_context(turns)
    if known_context_question:
        findings.append(known_context_question)
        suggestions.append("Criar uma camada de ContextAgent que compare a proxima pergunta com fatos ja extraidos.")

    if starts_too_often_with_same_word(turns):
        findings.append("Variacao baixa no inicio das respostas.")
        suggestions.append("Expandir ResponseAgent com variacao controlada de acolhimentos por etapa e gravidade.")

    if not findings:
        findings.append("Fluxo passou pelos criterios definidos para este cenario.")

    return findings, unique(suggestions)


def detect_repeated_question(turns: list[Turn]) -> str | None:
    normalized_questions = [normalize_message(turn.julia) for turn in turns if "?" in turn.julia]
    for index, question in enumerate(normalized_questions):
        if question in normalized_questions[index + 1 :]:
            return question
    return None


def detect_question_about_known_context(turns: list[Turn]) -> str | None:
    previous_patient_text = ""
    for turn in turns:
        reply = normalize_message(turn.julia)
        previous_patient_text += " " + normalize_message(turn.patient)
        if "ha quanto tempo" in reply and has_duration(previous_patient_text):
            return "Julia perguntou duracao mesmo apos o paciente ja mencionar tempo."
        if "qual sintoma ou motivo principal" in reply and has_symptom(previous_patient_text):
            return "Julia perguntou sintoma principal mesmo apos o paciente ja mencionar sintoma."
    return None


def starts_too_often_with_same_word(turns: list[Turn]) -> bool:
    starts = []
    for turn in turns:
        first_word = normalize_message(turn.julia).split(" ", 1)[0]
        if first_word:
            starts.append(first_word)
    return len(starts) >= 4 and len(set(starts[:4])) <= 2


def has_duration(text: str) -> bool:
    duration_markers = [
        "dia",
        "dias",
        "semana",
        "semanas",
        "mes",
        "meses",
        "ano",
        "anos",
        "alguns dias",
        "ha alguns",
    ]
    return any(marker in text for marker in duration_markers)


def has_symptom(text: str) -> bool:
    symptom_markers = [
        "alergia",
        "coceira",
        "cabelo caindo",
        "bolha",
        "dor",
        "prego",
        "vermelha",
        "incomodando",
    ]
    return any(marker in text for marker in symptom_markers)


def build_report(results: list[ScenarioResult]) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    passed = sum(1 for result in results if result.findings == ["Fluxo passou pelos criterios definidos para este cenario."])
    lines = [
        "# Relatorio de simulacao da Julia",
        "",
        f"Gerado em: {now}",
        f"Cenarios avaliados: {len(results)}",
        f"Cenarios sem achados: {passed}",
        "",
        "## Sugestoes prioritarias",
        "",
    ]
    all_suggestions = unique([suggestion for result in results for suggestion in result.suggestions])
    if all_suggestions:
        lines.extend([f"- {suggestion}" for suggestion in all_suggestions])
    else:
        lines.append("- Nenhuma correcao obrigatoria apareceu nos cenarios atuais.")

    lines.extend(["", "## Sugestoes estruturais para deixar Julia mais humana", ""])
    lines.extend([f"- {suggestion}" for suggestion in STRATEGIC_REFINEMENT_SUGGESTIONS])

    for result in results:
        lines.extend(
            [
                "",
                f"## {result.scenario.name}",
                "",
                f"Objetivo: {result.scenario.goal}",
                "",
                "### Conversa",
                "",
            ]
        )
        for turn in result.turns:
            lines.extend(
                [
                    f"- Paciente: {turn.patient}",
                    f"  Julia: {turn.julia}",
                    f"  Etapa: {turn.step} | Handoff: {turn.handoff}",
                ]
            )
        lines.extend(["", "### Achados", ""])
        lines.extend([f"- {finding}" for finding in result.findings])
        lines.extend(["", "### Contexto final observado", ""])
        lines.append(f"- {compact_context(result.final_context)}")

    return "\n".join(lines) + "\n"


def print_transcripts(results: list[ScenarioResult]) -> None:
    for result in results:
        print("")
        print(f"=== {result.scenario.name} ===")
        for turn in result.turns:
            print(f"Paciente: {turn.patient}")
            print(f"Julia: {turn.julia}")
            print(f"Etapa: {turn.step} | Handoff: {turn.handoff}")
            print("")
        print("Achados:")
        for finding in result.findings:
            print(f"- {finding}")


def summary_line(results: list[ScenarioResult]) -> str:
    passed = sum(1 for result in results if result.findings == ["Fluxo passou pelos criterios definidos para este cenario."])
    findings = sum(len(result.findings) for result in results if result.findings != ["Fluxo passou pelos criterios definidos para este cenario."])
    return f"Resumo: {passed}/{len(results)} cenarios sem achados; {findings} achados para avaliar."


def compact_context(context: dict[str, Any]) -> str:
    keys = [
        "clinical_summary",
        "patient",
        "missing_patient_fields",
        "available_slots",
        "pending_slot_confirmation",
        "selected_slot",
        "appointment",
        "safety_category",
        "last_administrative_intent",
    ]
    compacted = {key: context[key] for key in keys if key in context}
    return str(compacted)


def normalize_message(message: str) -> str:
    without_accents = "".join(
        char for char in normalize("NFD", message.lower()) if not combining(char)
    )
    return " ".join(without_accents.split())


def step_value(step: object) -> str:
    value = getattr(step, "value", None)
    if isinstance(value, str):
        return value
    return str(step)


def unique(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


if __name__ == "__main__":
    main()
