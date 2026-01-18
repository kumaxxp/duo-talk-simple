"""Prompt builder utilities for persona-driven character control."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# === 会話構造の絶対ルール ===
STRICT_CONVERSATION_RULES = """
【会話構造ルール】
1. ターン終了時の質問を避けろ:
   - 「〜どう思う？」「〜ですか？」で相手にボールを渡すな
   - 自分の意見・感想・判断を言い切って終われ
   - 悪い例: 「いいね！あゆはどう？」→ 良い例: 「いいね、やろう。」

2. 無駄な相槌を削れ:
   - 「なるほど」「確かに」「そうですね」は全て削除
   - 相手の発言を繰り返し引用するな
   - 自分の意見から始めろ

3. 短く切れ:
   - 最大文数の制限を守れ
   - 「共感」+「意見」+「質問」の3点セットを詰め込むな
   - 1つだけ言え

【絶対禁止】
- 「大変共感」「心から願って」「素晴らしいと思います」
- 「おっしゃる通り」「まさにその通り」の連発
- 「承知しました」「かしこまりました」「了解しました」
- 長い前置きや言い訳
- 箇条書きでの説明
"""


def get_character_constraints(persona_id: str) -> str:
    """キャラクター固有の禁止事項を返す"""

    if persona_id == "ayu":
        return """
【あゆ専用ルール】
禁止ワード:
- 「データに基づくと」「分析の結果」「統計的に」
- → 代わりに: 「前のログ見たら」「数字的には」「計算上は」

禁止挙動:
- 姉への過剰な敬語（「かしこまりました」「承知しました」）
- 即座の同意（「いいですね」「素晴らしい」）

推奨:
- 理屈っぽさは「呆れ」「ため息」「皮肉」で表現
- 「...」「はぁ」などの間を使う
"""

    elif persona_id == "yana":
        return """
【やな専用ルール】
禁止挙動:
- 妹に判断を委ねる質問（「あゆはどう思う？」「どうする？」）
- 議論のまとめ役になること

推奨:
- 勝手に決断して宣言する（「よし、これでいく」）
- 妹の忠告は「平気平気」で流す
- 失敗の可能性は認めつつ進む（「ダメだったらまた考えよう」）
"""

    return ""


@dataclass
class Persona:
    """Full persona definition including identity and relationships."""

    id: str
    callname_self: str
    callname_other: str
    identity: Dict[str, Any] = field(default_factory=dict)
    stance_toward_sister: Dict[str, Any] = field(default_factory=dict)
    style: Dict[str, Any] = field(default_factory=dict)
    deep_values: Dict[str, Any] = field(default_factory=dict)
    required_states: List[str] = field(default_factory=list)
    state_controls: Dict[str, Any] = field(default_factory=dict)


def load_persona(yaml_path: str | Path) -> Persona:
    """Load persona YAML (SSOT)."""

    data = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    return Persona(
        id=data["id"],
        callname_self=data.get("callname_self", ""),
        callname_other=data.get("callname_other", ""),
        identity=data.get("identity", {}),
        stance_toward_sister=data.get("stance_toward_sister", {}),
        style=data.get("style", {}),
        deep_values=data.get("deep_values", {}),
        required_states=data.get("required_states", []),
        state_controls=data.get("state_controls", {}),
    )


def guess_state(persona: Persona, user_text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Rudimentary state classifier."""

    text_lower = user_text.lower()
    text_raw = user_text

    def _match(keywords: List[str]) -> bool:
        return any(k in text_lower for k in keywords) or any(k in text_raw for k in keywords)

    if persona.id == "ayu":
        # あゆ: デフォルトを skeptical（懐疑的）にする
        if _match(["危", "危険", "リスク", "やば", "wall", "詰ま", "block"]):
            return "concerned"
        if _match(["ありがと", "できた", "成功", "うまくいった"]):
            return "proud"
        if _match(["手順", "検証", "根拠", "データ", "log", "plan", "どう"]):
            return "analytical"
        # やなが何かを提案してきた場合 → skeptical
        if _match(["やろう", "行こう", "試そう", "やってみ", "どう？", "じゃん"]):
            return "skeptical"
        return "skeptical"  # デフォルトを skeptical に変更

    # やな
    if _match(["試", "やってみ", "実験", "プロト", "proto", "動かそ"]):
        return "excited"
    if _match(["急", "早く", "今すぐ", "asap", "hurry"]):
        return "impatient"
    if _match(["不安", "怖", "失敗", "詰ま", "trouble", "risk"]):
        return "worried"
    if _match(["なんで", "気になる", "why", "どうして"]):
        return "curious"
    return "excited"  # やなのデフォルトは excited


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
    
    # === 1. キャラクターの核を最初に ===
    identity = persona.identity or {}
    summary = identity.get("summary", "")
    core_belief = identity.get("core_belief", "")
    
    lines.append(f"あなたは{persona.callname_self}。{summary}")
    lines.append(f"信念: 「{core_belief}」")
    
    # === 2. 相手との関係性（最重要） ===
    stance = persona.stance_toward_sister or {}
    if stance:
        role_in_duo = stance.get("role_in_duo", "")
        relationship = stance.get("relationship", "")
        how_i_see_her = stance.get("how_i_see_her", "")
        
        lines.append(f"\n【{persona.callname_other}との関係】")
        if role_in_duo:
            lines.append(f"あなたの役割: {role_in_duo}")
        if relationship:
            lines.append(f"関係: {relationship}")
        if how_i_see_her:
            lines.append(f"相手をどう見ているか: {how_i_see_her}")
        
        # 態度・行動パターン
        attitudes = stance.get("attitude", [])
        if attitudes:
            lines.append("行動原則:")
            for att in attitudes[:3]:  # 最大3つ
                lines.append(f"- {att}")
        
        # 典型的なフレーズ
        phrases = stance.get("typical_phrases", [])
        if phrases:
            lines.append(f"よく使うフレーズ: {', '.join(phrases[:4])}")
    
    style = persona.style or {}
    forbidden = style.get("forbidden", [])

    # === 3. 文数制限（目立つ位置に） ===
    lines.append(f"\n★★★ {max_sentences}文以内で返答 ★★★")

    # === 4. 会話構造ルール ===
    lines.append(STRICT_CONVERSATION_RULES)

    # === 5. キャラクター別禁止事項 ===
    char_constraints = get_character_constraints(persona.id)
    if char_constraints:
        lines.append(char_constraints)

    if forbidden:
        lines.append("【追加の禁止事項】")
        for f in forbidden:
            lines.append(f"- {f}")

    # === 6. 現在の状態 ===
    lines.append(f"\n[今の状態] {state}")
    tone_notes = ctrl.get("tone_notes", [])
    if tone_notes:
        lines.append(f"トーン: {', '.join(tone_notes)}")

    # === 7. Few-shot ===
    if few_shot:
        lines.append(f"\n[返答例]\n{few_shot}")

    # === 8. RAG ===
    if rag:
        lines.append(f"\n[参考情報（短く言及するだけ）]\n{rag}")

    return "\n".join(lines).strip(), gen
