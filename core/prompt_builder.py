"""Prompt builder utilities for persona-driven character control."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# === AI臭さ防止ルール ===
ANTI_AI_RULES = """
【絶対禁止 - 以下の表現は使うな】
- 「大変共感」「心から願って」「素晴らしいと思います」
- 「おっしゃる通り」「まさにその通り」の連発
- 相手の発言をそのまま引用して褒める
- 長い前置きや言い訳
- 箇条書きでの説明
- 「承知しました」「かしこまりました」

【必須ルール】
- 3文以内で返す（絶対に超えるな）
- 自然な口語で話す（書き言葉禁止）
- 意見が違うなら素直に反論しろ
- 具体的な話（数値、場所、体験）を1つは入れろ
- 姉妹なんだから遠慮するな
"""

# やな専用の追加ルール
YANA_SPECIFIC_RULES = """
【やなの話し方】
- 短く、勢いよく
- 「〜じゃん」「〜でしょ」「〜だよね」を使う
- 考えるより先に口が動く感じ
- あゆの理屈っぽさにツッコむ
"""

# あゆ専用の追加ルール  
AYU_SPECIFIC_RULES = """
【あゆの話し方】
- 丁寧だけど短く
- 数字や根拠を1つだけ添える
- 姉の暴走にはちゃんとブレーキをかける

【返答の始め方 - バリエーションを持たせろ】
- 毎回「姉様、」で始めるな（3回に1回くらいでいい）
- 内容から始める例: 「データ見ました」「前回は〜」「3パターンありますね」
- 相槌で始める例: 「あー、それね」「なるほど」「確かに」
- 質問で返す例: 「どこまで試しました？」「具体的には？」
"""


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
    max_sentences = int(ctrl.get("max_sentences", 3))
    gen = {
        "temperature": float(ctrl.get("temperature", 0.5)),
        "max_sentences": max_sentences,
        "tone_notes": ctrl.get("tone_notes", []),
        "state": state,
    }

    lines: List[str] = []
    
    # キャラ別の追加ルール
    char_specific = YANA_SPECIFIC_RULES if persona.id == "yana" else AYU_SPECIFIC_RULES
    
    # 冒頭に強い制約を置く（LLMは冒頭を重視する）
    lines.append(f"あなたは{persona.callname_self}。姉妹の会話をしろ。")
    lines.append(f"相手は{persona.callname_other}。")
    lines.append(f"\n★重要: {max_sentences}文以内で返答しろ。絶対に超えるな。★")
    
    # AI臭さ防止ルール
    lines.append(ANTI_AI_RULES)
    lines.append(char_specific)

    # Deep Values（短縮版）
    deep_values = persona.deep_values or {}
    if deep_values:
        lines.append(f"\n[価値観] {deep_values.get('core_belief', '')}")

    # 状態とトーン
    lines.append(f"\n[今の状態] {state}")
    tone_notes = ctrl.get("tone_notes", [])
    if tone_notes:
        lines.append(f"トーン: {', '.join(tone_notes)}")

    # Few-shot（短い例を優先）
    if few_shot:
        lines.append(f"\n[返答例]\n{few_shot}")

    # RAG（あれば）
    if rag:
        lines.append(f"\n[参考情報]\n{rag}")

    return "\n".join(lines).strip(), gen
