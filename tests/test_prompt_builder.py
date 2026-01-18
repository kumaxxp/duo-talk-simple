from pathlib import Path

from core import prompt_builder


def test_few_shot_patterns_coverage():
    """Verify all required states have few-shot patterns."""
    patterns = prompt_builder.load_few_shot_patterns(Path("patterns/few_shot_patterns.yaml"))

    # Check yana patterns
    yana_persona = prompt_builder.load_persona(Path("personas/yana.yaml"))
    yana_states = set(yana_persona.required_states)
    yana_pattern_states = {p["state"] for p in patterns if p["persona"] == "yana"}
    missing_yana = yana_states - yana_pattern_states
    assert not missing_yana, f"Missing yana few-shot patterns for: {missing_yana}"

    # Check ayu patterns
    ayu_persona = prompt_builder.load_persona(Path("personas/ayu.yaml"))
    ayu_states = set(ayu_persona.required_states)
    ayu_pattern_states = {p["state"] for p in patterns if p["persona"] == "ayu"}
    missing_ayu = ayu_states - ayu_pattern_states
    assert not missing_ayu, f"Missing ayu few-shot patterns for: {missing_ayu}"


def test_select_few_shot():
    """Test few-shot selection functionality."""
    patterns = prompt_builder.load_few_shot_patterns(Path("patterns/few_shot_patterns.yaml"))

    # Test existing patterns
    result = prompt_builder.select_few_shot(patterns, "yana", "excited")
    assert result is not None
    assert "面白そう" in result or "動かして" in result

    result = prompt_builder.select_few_shot(patterns, "ayu", "concerned")
    assert result is not None
    assert "危険" in result

    # Test non-existing pattern returns None
    result = prompt_builder.select_few_shot(patterns, "yana", "nonexistent_state")
    assert result is None


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
