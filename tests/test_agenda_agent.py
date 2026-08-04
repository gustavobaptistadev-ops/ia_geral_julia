from app.application.agenda import AgendaAgent


def test_agenda_agent_orders_default_slots_by_closest_datetime() -> None:
    slots = AgendaAgent().default_available_slots()

    assert slots == ["2026-08-10 09:00", "2026-08-10 14:00", "2026-08-11 10:00"]


def test_agenda_agent_selects_slot_by_natural_period() -> None:
    agent = AgendaAgent()

    selected = agent.select_slot("pode ser de tarde", agent.default_available_slots())

    assert selected == "2026-08-10 14:00"


def test_agenda_agent_selects_slot_by_weekday_and_period() -> None:
    agent = AgendaAgent()

    selected = agent.select_slot("prefiro segunda de manha", agent.default_available_slots())

    assert selected == "2026-08-10 09:00"


def test_agenda_agent_returns_candidates_for_ambiguous_weekday() -> None:
    agent = AgendaAgent()

    candidates = agent.slot_candidates("segunda", agent.default_available_slots())

    assert candidates == ["2026-08-10 09:00", "2026-08-10 14:00"]


def test_agenda_agent_selects_single_weekday_option() -> None:
    agent = AgendaAgent()

    selected = agent.select_slot("terca", agent.default_available_slots())

    assert selected == "2026-08-11 10:00"
