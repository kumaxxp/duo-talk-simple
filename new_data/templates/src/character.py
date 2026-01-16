"""Phase1: Deep Values の最小スケルトン。

あなたの実装に合わせて置換してOK。
ここでの目的は：
- YAML(SSOT)から persona を読み
- 状態(state)を推定し
- Deep Values + State Controls + Few-shot をまとめて system prompt を生成
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass
class Persona:
    id: str
    callname_self: str
    callname_other: str
    style: Dict[str, Any]
    deep_values: Dict[str, Any]
    required_states: List[str]
    state_controls: Dict[str, Any]


def load_persona(yaml_path: str | Path) -> Persona:
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
    """雑でもいいのでまず動く判定。

    将来的には:
    - 直近ターンの失敗/成功
    - topic_drift/conflict
    - ユーザの語気
    - タスク種別（設計/実装/レビュー）
    などを使って精密化。
    """
    t = user_text.lower()
    if persona.id == "ayu":
        if any(k in t for k in ["危", "危険", "リスク", "壊", "やば"]):
            return "concerned"
        if any(k in t for k in ["ありがとう", "助かった", "できた", "成功"]):
            return "proud"
        if any(k in t for k in ["どうすれば", "手順", "検証", "根拠"]):
            return "analytical"
        return "focused"

    # yana
    if any(k in t for k in ["やってみ", "試", "実験", "プロト"]):
        return "excited"
    if any(k in t for k in ["急", "早", "今すぐ", "間に合"]):
        return "impatient"
    if any(k in t for k in ["不安", "怖", "失敗", "詰ま"]):
        return "worried"
    return "focused"


def load_few_shot_patterns(yaml_path: str | Path) -> List[Dict[str, Any]]:
    data = yaml.safe_load(Path(yaml_path).read_text(encoding="utf-8"))
    return data.get("items", [])


def select_few_shot(patterns: List[Dict[str, Any]], persona_id: str, state: str) -> Optional[str]:
    candidates = [p for p in patterns if p.get("persona") == persona_id and p.get("state") == state]
    if not candidates:
        return None
    # 最初の例を採用（将来：ランダム/重み付け/最近の反復避け）
    ex = candidates[0].get("examples", [])
    return ex[0] if ex else None


def build_system_prompt(
    persona: Persona,
    state: str,
    few_shot: Optional[str] = None,
    rag: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """system prompt と生成パラメータを返す。

    - state_controls を generation params に反映
    - Deep Values を system prompt に埋め込み
    """
    ctrl = persona.state_controls.get(state, {})
    gen = {
        "temperature": float(ctrl.get("temperature", 0.5)),
        "max_sentences": int(ctrl.get("max_sentences", 5)),
    }

    style = persona.style
    dv = persona.deep_values

    lines = []
    # Basic
    lines.append(f"あなたは姉妹AIの一人。名前は{persona.callname_self}。相手は{persona.callname_other}。")
    lines.append("相手を侮辱しない。危険な指示は拒否し、安全な代替案へ誘導する。")

    # Deep Values
    lines.append("\n[Deep Values]")
    lines.append(f"core_belief: {dv.get('core_belief','')}")
    dp = dv.get("decision_priority", {})
    if dp:
        dp_str = ", ".join([f"{k}={v}" for k, v in dp.items()])
        lines.append(f"decision_priority: {dp_str}")

    # Surface
    lines.append("\n[Surface Style]")
    lines.append(f"register={style.get('register','')}, tempo={style.get('tempo','')}, length={style.get('length','')}")
    lines.append(f"state={state}")

    # Few-shot
    if few_shot:
        lines.append("\n[Few-shot]\n" + few_shot)

    # RAG
    if rag:
        lines.append("\n[RAG]\n" + rag)

    return "\n".join(lines).strip(), gen
