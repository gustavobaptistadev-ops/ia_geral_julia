from __future__ import annotations

from datetime import datetime

from app.domain.conversation.context import ConversationContext
from app.domain.conversation.models import ConversationState


class VoiceAgent:
    def greeting(self) -> str:
        return "Oi! Aqui e a Julia, da LifelineOne. Estou pronta para te ajudar. Qual e a nossa prioridade de hoje?"

    def emergency_fallback(self) -> str:
        return (
            "Estou vendo que voce precisa de ajuda imediata. Por favor, procure o Samu pelo 192 agora mesmo "
            "e peca apoio medico urgente."
        )

    def fallback(self) -> str:
        return "Entendi. Vou te acompanhar com calma e vou tentar te ajudar a encontrar o melhor proximo passo."

    def appointment_already_booked(self) -> str:
        return "Perfeito. Sua consulta ja esta confirmada. Qualquer ajuste, estou por aqui para te ajudar."

    def booked_appointment(self, selected_slot: object) -> str:
        return (
            "Perfeito, sua consulta esta confirmada.\n\n"
            f"Horario: {self.format_confirmed_slot(selected_slot)}\n"
            "Endereco: Clinica LifelineOne, Av. Paulista, 1000 - Sao Paulo, SP.\n\n"
            "Chegue com alguns minutos de antecedencia e leve seus documentos. "
            "Vou te acompanhar por aqui se precisar ajustar algo."
        )

    def confirm_appointment(self, state: ConversationState) -> str:
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

    def discover_symptoms(self, state: ConversationState, message: str) -> str:
        context = ConversationContext.from_dict(state.context)
        clinical = context.clinical
        main_complaint = clinical.main_complaint or context.reason or message
        missing_fields = set(clinical.missing_fields)
        acknowledgement = self.acknowledgement(state)

        if not clinical.main_complaint:
            if clinical.requested_specialty:
                return f"Certo, consigo te ajudar com {clinical.requested_specialty}. Qual sintoma ou motivo principal da consulta?"
            return "Certo, me conta qual sintoma ou motivo principal da consulta."

        if "duration" in missing_fields:
            return f"{acknowledgement}, ha quanto tempo isto esta ocorrendo?"

        if "severity_or_progression" in missing_fields:
            return f"{acknowledgement}, isso esta leve, incomodando bastante ou piorando?"

        return f"Entendi sobre {main_complaint}. Quer que eu te ajude a organizar um atendimento para avaliar isso com seguranca?"

    def collect_information(self, state: ConversationState) -> str:
        context = ConversationContext.from_dict(state.context)
        missing_fields = context.missing_patient_fields or ["name", "phone"]
        patient_name = context.patient.name

        if patient_name and "phone" in missing_fields:
            return f"Perfeito, {patient_name}. Agora falta so o WhatsApp/Telefone para eu seguir com o agendamento."

        if missing_fields == ["name"]:
            return "Recebi o telefone. Agora me passe o nome completo, por favor."

        return (
            "Otimo, vamos deixar tudo agendado. Pode me passar os seguintes dados por aqui, por favor?\n\n"
            "Nome completo\n\n"
            "WhatsApp/Telefone"
        )

    def calendar_slots(self, slots: list[object]) -> str:
        return self.format_slots(slots)

    def calendar_slot_confirmation(self, pending_slot: object) -> str:
        return (
            "Tenho mais de um horario nesse dia. "
            f"Posso confirmar {self.format_confirmed_slot(pending_slot)}? "
            "Se preferir outro horario, pode me dizer qual."
        )

    def calendar_slot_declined(self, slots: list[object]) -> str:
        return f"Sem problema. {self.format_slots(slots)}"

    def calendar_selection_error(self, slots: list[object]) -> str:
        return f"Nao consegui identificar qual horario fica melhor para voce. {self.format_slots(slots)}"

    def calendar_options_intro(self, slots: list[object]) -> str:
        return f"Consultei a agenda disponivel para atendimento e encontrei estas opcoes. {self.format_slots(slots)}"

    def acknowledgement(self, state: ConversationState) -> str:
        messages = state.context.get("messages", [])
        count = len(messages) if isinstance(messages, list) else 0
        options = ["Entendi", "Certo", "Obrigado por me contar", "Combinado"]
        return options[max(0, count - 1) % len(options)]

    def format_slots(self, slots: list[object]) -> str:
        if not slots:
            return "No momento nao encontrei horarios livres; posso deixar para apoio humano verificar a agenda."

        ordered_slots = sorted([str(slot) for slot in slots], key=self._slot_datetime)
        formatted_slots = [self.format_slot(slot) for slot in ordered_slots]
        return f"Tenho vaga {self._join_naturally(formatted_slots)}. Qual desses horarios fica melhor para voce?"

    def format_slot(self, slot: str) -> str:
        date_time = self._slot_datetime(slot)
        return f"{self._weekday_label(date_time)} as {self._format_hour(date_time)}"

    def format_confirmed_slot(self, slot: object) -> str:
        if not slot:
            return "horario combinado"

        try:
            date_time = self._slot_datetime(str(slot))
        except ValueError:
            return str(slot)

        return f"{self._weekday_label(date_time)}, {date_time.strftime('%d/%m/%Y')} as {self._format_hour(date_time)}"

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

    def _format_hour(self, date_time: datetime) -> str:
        if date_time.minute:
            return f"{date_time.hour}h{date_time.minute:02d}"
        return f"{date_time.hour}h"
