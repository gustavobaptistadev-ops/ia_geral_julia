from __future__ import annotations

from datetime import datetime

from app.domain.conversation.context import ConversationContext
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
                "message": self._confirm_appointment_message(state),
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
            if state.context.get("slot_confirmation_required"):
                pending_slot = state.context.get("pending_slot_confirmation")
                return {
                    "message": (
                        "Tenho mais de um horario nesse dia. "
                        f"Posso confirmar {self._format_confirmed_slot(pending_slot)}? "
                        "Se preferir outro horario, pode me dizer qual."
                    ),
                    "next_step": ConversationStep.CHECK_CALENDAR,
                    "should_handoff": False,
                }

            if state.context.get("slot_confirmation_declined"):
                return {
                    "message": f"Sem problema. {self._format_slots(slots)}",
                    "next_step": ConversationStep.CHECK_CALENDAR,
                    "should_handoff": False,
                }

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
                    "Perfeito, sua consulta esta confirmada.\n\n"
                    f"Horario: {self._format_confirmed_slot(state.context.get('selected_slot'))}\n"
                    "Endereco: Clinica LifelineOne, Av. Paulista, 1000 - Sao Paulo, SP.\n\n"
                    "Chegue com alguns minutos de antecedencia e leve seus documentos. "
                    "Vou te acompanhar por aqui se precisar ajustar algo."
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
        context = ConversationContext.from_dict(state.context)
        clinical = context.clinical
        if clinical.main_complaint:
            parts = [clinical.main_complaint]
            if clinical.duration:
                parts.append(f"ha {clinical.duration}")
            if clinical.progression:
                parts.append(clinical.progression)
            if clinical.severity:
                parts.append(clinical.severity)
            return ", ".join(parts)

        return "; ".join(context.symptoms[-3:]) if context.symptoms else str(context.reason or "seu relato")

    def _confirm_appointment_message(self, state: ConversationState) -> str:
        context = ConversationContext.from_dict(state.context)
        if context.clinical.is_worsening():
            return (
                "Poxa, sinto muito que esteja piorando. Imagino que isso esteja te trazendo desconforto.\n\n"
                "Para a gente cuidar disso com mais seguranca e tentar resolver logo, "
                "que tal olharmos um horario na agenda para voce passar por uma avaliacao?"
            )

        return (
            "Pelo o que foi relatado, faz sentido organizar um atendimento para avaliar isso com seguranca. "
            "Vamos agendar sua consulta?"
        )

    def _discover_symptoms_message(self, state: ConversationState, message: str) -> str:
        context = ConversationContext.from_dict(state.context)
        clinical = context.clinical
        main_complaint = clinical.main_complaint or context.reason or message
        missing_fields = set(clinical.missing_fields)
        acknowledgement = self._acknowledgement(state)

        if not clinical.main_complaint:
            if clinical.requested_specialty:
                return f"Certo, consigo te ajudar com {clinical.requested_specialty}. Qual sintoma ou motivo principal da consulta?"
            return "Certo, me conta qual sintoma ou motivo principal da consulta."

        if "duration" in missing_fields:
            return f"{acknowledgement}, ha quanto tempo isto esta ocorrendo?"

        if "severity_or_progression" in missing_fields:
            return f"{acknowledgement}, isso esta leve, incomodando bastante ou piorando?"

        return f"Entendi sobre {main_complaint}. Quer que eu te ajude a organizar um atendimento para avaliar isso com seguranca?"

    def _acknowledgement(self, state: ConversationState) -> str:
        messages = state.context.get("messages", [])
        count = len(messages) if isinstance(messages, list) else 0
        options = ["Entendi", "Certo", "Obrigado por me contar", "Combinado"]
        return options[max(0, count - 1) % len(options)]

    def _collect_information_message(self, state: ConversationState) -> str:
        context = ConversationContext.from_dict(state.context)
        missing_fields = context.missing_patient_fields or ["name", "phone"]
        patient_name = context.patient.name

        if patient_name and "phone" in missing_fields:
            return (
                f"Perfeito, {patient_name}. Agora falta so o WhatsApp/Telefone para eu seguir com o agendamento."
            )

        if missing_fields == ["name"]:
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
        return f"{self._weekday_label(date_time)} as {self._format_hour(date_time)}"

    def _join_naturally(self, items: list[str]) -> str:
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return " ou ".join(items)
        return ", ".join(items[:-1]) + " ou " + items[-1]

    def _slot_datetime(self, slot: str) -> datetime:
        return datetime.strptime(slot, "%Y-%m-%d %H:%M")

    def _format_confirmed_slot(self, slot: object) -> str:
        if not slot:
            return "horario combinado"

        try:
            date_time = self._slot_datetime(str(slot))
        except ValueError:
            return str(slot)

        return f"{self._weekday_label(date_time)}, {date_time.strftime('%d/%m/%Y')} as {self._format_hour(date_time)}"

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

    def _format_hour(self, date_time: datetime) -> str:
        if date_time.minute:
            return f"{date_time.hour}h{date_time.minute:02d}"
        return f"{date_time.hour}h"
