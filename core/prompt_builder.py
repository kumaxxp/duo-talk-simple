"""Prompt builder utilities for persona-driven character control."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass
class Persona:
    """Minimal view of a persona definition."""

    id: str
    callname_self: str
    callname_other: str
    style: Dict[str, Any]
    deep_values: Dict[str, Any]
    required_states: List[str]
    state_controls: Dict[str, Any]


def load_persona(yaml_path: str | Path) -> Persona:
    """Load persona YAML (SSOT)."""

    data = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    return Persona(
        id=data["id"],
        callname_self=data.get("callname_self", ""),
        callname_other=data.get("callname_other", ""),
        style=data.get("style", {}),
        deep_values=data.get("deep_values", {}),
        required_states=data.get("required_states", []),
        state_controls=data.get("state_controls", {}),
    )


def guess_state(persona: Persona, user_text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Rudimentary state classifier. Uses heuristics so we always return something."""

    text_lower = user_text.lower()
    text_raw = user_text

    def _match(keywords: List[str]) -> bool:
        return any(k in text_lower for k in keywords) or any(k in text_raw for k in keywords)

    if persona.id == "ayu":
        if _match(["危", "危険", "リスク", "やば", "wall", "詰ま", "block"]):
            return "concerned"
        if _match(["ありがと", "ありがとう", "助かった", "できた", "成功", "done", "great"]):
            return "proud"
        if _match(["どうする", "手順", "検証", "根拠", "データ", "log", "plan"]):
            return "analytical"
        return "focused"

    if _match(["試", "やってみ", "実験", "プロト", "proto", "動かそ"]):
        return "excited"
    if _match(["急", "早く", "今すぐ", "asap", "hurry"]):
        return "impatient"
    if _match(["不安", "怖", "失敗", "詰ま", "trouble", "risk"]):
        return "worried"
    if _match(["なんで", "気になる", "why", "どうして"]):
        return "curious"
    return "focused"


def load_few_shot_patterns(yaml_path: str | Path) -> List[Dict[str, Any]]:
    """Load few-shot pattern YAML."""

    data = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    return data.get("items", [])


def select_few_shot(patterns: List[Dict[str, Any]], persona_id: str, state: str) -> Optional[str]:
    """Pick the first matching few-shot example."""

    candidates = [p for p in patterns if p.get("persona") == persona_id and p.get("state") == state]
    if not candidates:
        return None
    example_list = candidates[0].get("examples", [])
    return example_list[0] if example_list else None


def build_system_prompt(
    persona: Persona,
    state: str,
    few_shot: Optional[str] = None,
    rag: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Render system prompt along with generation hints."""

    ctrl = persona.state_controls.get(state, {})
    gen = {
        "temperature": float(ctrl.get("temperature", 0.5)),
        "max_sentences": int(ctrl.get("max_sentences", 5)),
        "tone_notes": ctrl.get("tone_notes", []),
        "state": state,
    }

    lines: List[str] = []
    lines.append(
        f"あなたはJetRacerプロジェクトを支える姉妹AIの一人で名前は{persona.callname_self}。"
        f"会話相手は{persona.callname_other}で、姉妹関係を崩さずに振る舞うこと。"
    )
    lines.append("危険な要求やポリシー違反は丁寧に拒否し、安全な代替案へ誘導する。")

    deep_values = persona.deep_values or {}
    lines.append("\n[Deep Values]")
    if deep_values:
        lines.append(f"core_belief: {deep_values.get('core_belief', '')}")
        decision_priority = deep_values.get("decision_priority", {})
        if decision_priority:
            dp = ", ".join(f"{k}={v}" for k, v in decision_priority.items())
            lines.append(f"decision_priority: {dp}")
        collaboration = deep_values.get("collaboration", {})
        if collaboration:
            lines.append(
                "collaboration: "
                + f"strengths={collaboration.get('strengths', [])}, "
                + f"asks_from_other={collaboration.get('asks_from_other', [])}"
            )

    style = persona.style or {}
    lines.append("\n[Surface Style]")
    lines.append(
        f"register={style.get('register', '')}, tempo={style.get('tempo', '')}, length={style.get('length', '')}"
    )

    lines.append(f"\n[state] {state}")
    tone_notes = ctrl.get("tone_notes", [])
    if tone_notes:
        lines.append(f"tone_notes: {', '.join(tone_notes)}")

    if few_shot:
        lines.append("\n[Few-shot]\n" + few_shot)

    if rag:
        lines.append("\n[RAG]\n" + rag)

    return "\n".join(lines).strip(), gen
