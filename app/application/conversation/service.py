from __future__ import annotations

from datetime import datetime

from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus


class ConversationEngine:
    def generate_reply(self, state: ConversationState, message: str) -> dict[str, object]:
        if state.status == ConversationStatus.EMERGENCY:
            return {
                "message": state.context.get(
                    "safety_message",
                    "Estou vendo que voce precisa de ajuda imediata. Por favor, procure o Samu pelo 192 agora mesmo e peca apoio medico urgente.",
                ),
                "next_step": ConversationStep.EMERGENCY,
                "should_handoff": True,
            }

        if state.context.get("safety_message"):
            return {
                "message": state.context["safety_message"],
                "next_step": state.current_step,
                "should_handoff": True,
            }

        if state.current_step == ConversationStep.GREETING:
            return {
                "message": "Oi! Aqui e a Julia, da LifelineOne. Estou pronta para te ajudar. Qual e a nossa prioridade de hoje?",
                "next_step": ConversationStep.GREETING,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.DISCOVER_SYMPTOMS:
            return {
                "message": self._discover_symptoms_message(state, message),
                "next_step": ConversationStep.DISCOVER_SYMPTOMS,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.CONFIRM_APPOINTMENT:
            return {
                "message": (
                    "Pelo o que foi relatado, faz sentido organizar um atendimento para avaliar isso com seguranca. "
                    "Vamos agendar sua consulta?"
                ),
                "next_step": ConversationStep.CONFIRM_APPOINTMENT,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.COLLECT_INFORMATION:
            return {
                "message": self._collect_information_message(state),
                "next_step": ConversationStep.COLLECT_INFORMATION,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.CHECK_CALENDAR:
            slots = list(state.context.get("available_slots", []))
            if state.context.get("calendar_selection_error"):
                return {
                    "message": f"Nao consegui identificar qual horario fica melhor para voce. {self._format_slots(slots)}",
                    "next_step": ConversationStep.CHECK_CALENDAR,
                    "should_handoff": False,
                }

            return {
                "message": (
                    "Consultei a agenda disponivel para atendimento e encontrei estas opcoes. "
                    f"{self._format_slots(slots)}"
                ),
                "next_step": ConversationStep.CHECK_CALENDAR,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.BOOK_APPOINTMENT:
            return {
                "message": (
                    f"Consulta confirmada para {state.context.get('selected_slot')}. "
                    "Ficou tudo certo. A Clinica LifelineOne fica na Av. Paulista, 1000 - Sao Paulo, SP. "
                    "Chegue com alguns minutos de antecedencia e leve seus documentos. Vou te acompanhar por aqui se precisar ajustar algo."
                ),
                "next_step": ConversationStep.BOOK_APPOINTMENT,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.FINISHED:
            return {
                "message": "Perfeito. Sua consulta ja esta confirmada. Qualquer ajuste, estou por aqui para te ajudar.",
                "next_step": ConversationStep.FINISHED,
                "should_handoff": False,
            }

        return {
            "message": "Entendi. Vou te acompanhar com calma e vou tentar te ajudar a encontrar o melhor proximo passo.",
            "next_step": state.current_step,
            "should_handoff": False,
        }

    def _symptom_summary(self, state: ConversationState) -> str:
        clinical_summary = state.context.get("clinical_summary")
        if isinstance(clinical_summary, dict) and clinical_summary.get("main_complaint"):
            parts = [str(clinical_summary["main_complaint"])]
            if clinical_summary.get("duration"):
                parts.append(f"ha {clinical_summary['duration']}")
            if clinical_summary.get("progression"):
                parts.append(str(clinical_summary["progression"]))
            if clinical_summary.get("severity"):
                parts.append(str(clinical_summary["severity"]))
            return ", ".join(parts)

        symptoms = [str(symptom) for symptom in state.context.get("symptoms", [])]
        return "; ".join(symptoms[-3:]) if symptoms else str(state.context.get("reason", "seu relato"))

    def _discover_symptoms_message(self, state: ConversationState, message: str) -> str:
        summary = state.context.get("clinical_summary")
        if not isinstance(summary, dict):
            return "Entendi. Me conta um pouco mais sobre o que voce esta sentindo?"

        main_complaint = summary.get("main_complaint") or state.context.get("reason") or message
        missing_fields = set(summary.get("missing_fields", []))

        if not summary.get("main_complaint"):
            requested_specialty = summary.get("requested_specialty")
            if requested_specialty:
                return f"Certo, consigo te ajudar com {requested_specialty}. Qual sintoma ou motivo principal da consulta?"
            return "Certo, me conta qual sintoma ou motivo principal da consulta."

        if "duration" in missing_fields:
            return "Entendi, ha quanto tempo isto esta ocorrendo?"

        if "severity_or_progression" in missing_fields:
            return f"Entendi sobre {main_complaint}. Isso esta leve, incomodando bastante ou piorando?"

        return f"Entendi sobre {main_complaint}. Quer que eu te ajude a organizar um atendimento para avaliar isso com seguranca?"

    def _collect_information_message(self, state: ConversationState) -> str:
        patient = state.context.get("patient")
        missing_fields = state.context.get("missing_patient_fields", ["name", "phone"])
        patient_name = patient.get("name") if isinstance(patient, dict) else None

        if patient_name and isinstance(missing_fields, list) and "phone" in missing_fields:
            return (
                f"Perfeito, {patient_name}. Agora falta so o WhatsApp/Telefone para eu seguir com o agendamento."
            )

        if isinstance(missing_fields, list) and missing_fields == ["name"]:
            return "Recebi o telefone. Agora me passe o nome completo, por favor."

        return (
            "Otimo, vamos deixar tudo agendado. Pode me passar os seguintes dados por aqui, por favor?\n\n"
            "Nome completo\n\n"
            "WhatsApp/Telefone"
        )

    def _format_slots(self, slots: list[object]) -> str:
        if not slots:
            return "No momento nao encontrei horarios livres; posso deixar para apoio humano verificar a agenda."

        ordered_slots = sorted([str(slot) for slot in slots], key=self._slot_datetime)
        formatted_slots = [self._format_slot(slot) for slot in ordered_slots]
        return f"Tenho vaga {self._join_naturally(formatted_slots)}. Qual desses horarios fica melhor para voce?"

    def _format_slot(self, slot: str) -> str:
        date_time = self._slot_datetime(slot)
        hour = f"{date_time.hour}h"
        if date_time.minute:
            hour = f"{date_time.hour}h{date_time.minute:02d}"
        return f"{self._weekday_label(date_time)} as {hour}"

    def _join_naturally(self, items: list[str]) -> str:
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return " ou ".join(items)
        return ", ".join(items[:-1]) + " ou " + items[-1]

    def _slot_datetime(self, slot: str) -> datetime:
        return datetime.strptime(slot, "%Y-%m-%d %H:%M")

    def _weekday_label(self, date_time: datetime) -> str:
        labels = [
            "segunda-feira",
            "terca-feira",
            "quarta-feira",
            "quinta-feira",
            "sexta-feira",
            "sabado",
            "domingo",
        ]
        return labels[date_time.weekday()]
