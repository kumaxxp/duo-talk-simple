from pathlib import Path

from templates.src.character import build_system_prompt, load_persona


def test_deep_values_in_prompt():
    persona = load_persona(Path("templates/personas/ayu.yaml"))
    prompt, gen = build_system_prompt(persona, state="analytical")

    assert "[Deep Values]" in prompt
    assert "core_belief" in prompt
    assert "decision_priority" in prompt
    assert gen["temperature"] <= 0.6


def test_required_states_exist():
    ayu = load_persona(Path("templates/personas/ayu.yaml"))
    yana = load_persona(Path("templates/personas/yana.yaml"))

    for s in ayu.required_states:
        assert s in ayu.state_controls
    for s in yana.required_states:
        assert s in yana.state_controls
