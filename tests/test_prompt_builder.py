from pathlib import Path

from core import prompt_builder


def test_deep_values_in_prompt():
    persona = prompt_builder.load_persona(Path("personas/ayu.yaml"))
    prompt, gen = prompt_builder.build_system_prompt(persona, state="analytical")

    assert "[Deep Values]" in prompt
    assert "core_belief" in prompt
    assert "decision_priority" in prompt
    assert gen["temperature"] <= 0.5


def test_required_states_have_controls():
    ayu = prompt_builder.load_persona(Path("personas/ayu.yaml"))
    yana = prompt_builder.load_persona(Path("personas/yana.yaml"))

    for state in ayu.required_states:
        assert state in ayu.state_controls, f"missing ayu state control: {state}"

    for state in yana.required_states:
        assert state in yana.state_controls, f"missing yana state control: {state}"
