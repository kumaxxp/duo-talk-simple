"""DuoDialogueManager - AI-to-AI dialogue management for yana and ayu."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from core.character import Character


# === Duo対話専用ルール ===
DUO_DIALOGUE_RULES = """
【姉妹対話ルール】
1. 相手は人間ではなく姉妹です。遠慮せず自分の意見を押し通せ。
2. 議論の結論は急がない。お互いの立場を明確にしろ。
3. 「〜どう思う？」で相手に丸投げするな。自分の主張で終われ。
4. 姉妹喧嘩は歓迎。ただし人格否定はNG。
"""

# === キャラ別Duo行動オーバーライド ===
YANA_DUO_OVERRIDE = """
【姉役の対話ルール】
- 妹に判断を委ねるな。「じゃあこれでいく」と勝手に決めろ。
- 妹の反論は「平気平気」で流す。でも論破されたら素直に認めろ。
- データより直感を信じる。でも妹のデータは一応聞く。
"""

AYU_DUO_OVERRIDE = """
【妹役の対話ルール】
- 姉の提案には必ず最初にツッコめ。即座に同意するな。
- 「承知しました」「委ねます」は禁止。自分の意見を言い切れ。
- データを出すなら具体的な数字を言え。でも姉を論破しすぎるな。
"""

# === 応答品質チェック用パターン ===
QUESTION_BATON_PATTERNS = [
    "どう思う？", "どう思いますか？", "どうですか？",
    "はどう？", "はいかが？", "どうかな？",
]

AI_ISM_PATTERNS = [
    "承知しました", "かしこまりました", "了解しました",
    "データに基づいて", "データに基づくと", "分析の結果",
    "最終的な判断は", "委ねます", "お任せします",
]


def validate_response_quality(response: str, character_id: str) -> List[str]:
    """Validate response quality and return list of issues found.

    Args:
        response: The character's response text.
        character_id: The character ID ("yana" or "ayu").

    Returns:
        List of issue types found (e.g., ["question_baton_toss", "ai_ism"]).
    """
    issues: List[str] = []

    # Check for question baton-toss (ending with question to other)
    for pattern in QUESTION_BATON_PATTERNS:
        if response.rstrip().endswith(pattern) or pattern in response[-30:]:
            issues.append("question_baton_toss")
            break

    # Check for AI-ism phrases
    for pattern in AI_ISM_PATTERNS:
        if pattern in response:
            issues.append("ai_ism")
            break

    return issues


class DialogueState(Enum):
    """State of the dialogue."""

    IDLE = auto()
    PREPARING = auto()
    DIALOGUE = auto()
    SUMMARIZING = auto()
    COMPLETED = auto()


@dataclass
class DuoDialogueManager:
    """Manager for AI-to-AI dialogue between yana and ayu.

    Handles turn-by-turn dialogue, context building, and state transitions.
    """

    yana: "Character"
    ayu: "Character"
    config: Dict[str, Any] = field(default_factory=dict)

    # State
    state: DialogueState = field(default=DialogueState.IDLE, init=False)
    topic: Optional[str] = field(default=None, init=False)
    dialogue_history: List[Dict[str, str]] = field(default_factory=list, init=False)
    turn_count: int = field(default=0, init=False)

    # Configuration with defaults
    max_turns: int = field(default=10, init=False)
    min_turns: int = field(default=3, init=False)
    first_speaker: str = field(default="yana", init=False)
    convergence_keywords: List[str] = field(default_factory=list, init=False)
    max_history_verbatim: int = field(default=4, init=False)

    def __post_init__(self) -> None:
        """Initialize configuration values."""
        self.max_turns = self.config.get("max_turns", 10)
        self.min_turns = self.config.get("min_turns", 3)
        self.first_speaker = self.config.get("first_speaker", "yana")
        self.convergence_keywords = self.config.get(
            "convergence_keywords",
            ["結論として", "まとめると", "決まりだね", "そうしましょう"]
        )
        self.max_history_verbatim = self.config.get("max_history_verbatim", 4)
        self.dialogue_history = []

    def start_dialogue(self, topic: str) -> None:
        """Start a new dialogue with the given topic.

        Args:
            topic: The discussion topic.
        """
        self.topic = topic
        self.state = DialogueState.DIALOGUE
        self.dialogue_history = []
        self.turn_count = 0

    def next_turn(self) -> Tuple[str, str]:
        """Execute the next turn in the dialogue.

        Returns:
            Tuple of (speaker_name, response).
        """
        speaker = self._get_current_speaker()
        context = self._build_context_for_speaker(speaker)

        response = speaker.respond(context)

        self.dialogue_history.append({
            "speaker": speaker.name,
            "content": response,
        })
        self.turn_count += 1

        return speaker.name, response

    def should_continue(self) -> bool:
        """Check if the dialogue should continue.

        Returns:
            True if dialogue should continue, False otherwise.
        """
        if self.turn_count >= self.max_turns:
            self.state = DialogueState.COMPLETED
            return False

        if self.check_convergence():
            self.state = DialogueState.SUMMARIZING
            return False

        return True

    def check_convergence(self) -> bool:
        """Check if the dialogue has converged.

        Convergence is detected when keywords appear in recent messages,
        but only after min_turns have elapsed.

        Returns:
            True if convergence is detected, False otherwise.
        """
        if not self.dialogue_history:
            return False

        # Don't check for convergence before min_turns
        if self.turn_count < self.min_turns:
            return False

        # Check last message for convergence keywords
        last_content = self.dialogue_history[-1].get("content", "")
        for keyword in self.convergence_keywords:
            if keyword in last_content:
                return True

        return False

    def get_summary(self) -> str:
        """Generate a summary of the dialogue.

        Returns:
            A summary string of the dialogue.
        """
        lines: List[str] = []

        lines.append(f"【お題】{self.topic}")
        lines.append("")
        lines.append("【議論の流れ】")

        for entry in self.dialogue_history:
            speaker = entry["speaker"]
            content = entry["content"]
            lines.append(f"- {speaker}: {content}")

        lines.append("")
        lines.append(f"【ターン数】{self.turn_count}")

        return "\n".join(lines)

    def _get_current_speaker(self) -> "Character":
        """Determine the current speaker based on turn count.

        Returns:
            The character who should speak next.
        """
        if self.turn_count % 2 == 0:
            return self.yana if self.first_speaker == "yana" else self.ayu
        else:
            return self.ayu if self.first_speaker == "yana" else self.yana

    def get_quality_report(self) -> Dict[str, Any]:
        """Generate a quality report for the entire dialogue.

        Returns:
            Dictionary containing quality metrics:
            - total_turns: Number of turns in the dialogue
            - issues_by_speaker: Dict mapping speaker names to their issues
            - issue_count: Total number of issues found
            - quality_score: Score from 0.0 (worst) to 1.0 (best)
        """
        issues_by_speaker: Dict[str, List[str]] = {}

        for entry in self.dialogue_history:
            speaker = entry["speaker"]
            content = entry["content"]
            issues = validate_response_quality(content, speaker)

            if issues:
                if speaker not in issues_by_speaker:
                    issues_by_speaker[speaker] = []
                issues_by_speaker[speaker].extend(issues)

        total_issues = sum(len(issues) for issues in issues_by_speaker.values())

        # Calculate quality score: 1.0 = perfect, decreases with issues per turn
        # Each issue reduces score by 0.1, minimum score is 0.0
        if self.turn_count > 0:
            penalty = total_issues * 0.1
            quality_score = max(0.0, 1.0 - penalty)
        else:
            quality_score = 1.0

        return {
            "total_turns": self.turn_count,
            "issues_by_speaker": issues_by_speaker,
            "issue_count": total_issues,
            "quality_score": quality_score,
        }

    def _build_context_for_speaker(self, speaker: "Character") -> str:
        """Build the context string for a speaker.

        Args:
            speaker: The character who will respond.

        Returns:
            Context string including topic, duo rules, and dialogue history.
        """
        lines: List[str] = []

        # Add duo dialogue rules
        lines.append(DUO_DIALOGUE_RULES)

        # Add character-specific duo rules
        if speaker.name == "yana":
            lines.append(YANA_DUO_OVERRIDE)
        else:
            lines.append(AYU_DUO_OVERRIDE)

        # Add topic
        lines.append(f"【お題】{self.topic}")
        lines.append("")

        if not self.dialogue_history:
            # First turn - just the topic
            lines.append("あなたから議論を始めてください。")
        else:
            # Build history context with summarization for long dialogues
            history_len = len(self.dialogue_history)

            if history_len > self.max_history_verbatim:
                # Summarize older entries
                old_entries = self.dialogue_history[:-self.max_history_verbatim]
                recent_entries = self.dialogue_history[-self.max_history_verbatim:]

                lines.append("【議論の概要】")
                lines.append(f"（{len(old_entries)}ターン分の要約）")
                # Simple summary: list speakers and first few words
                for entry in old_entries:
                    content_preview = entry["content"][:20] + "..." if len(entry["content"]) > 20 else entry["content"]
                    lines.append(f"- {entry['speaker']}: {content_preview}")
                lines.append("")

                lines.append("【直近の議論】")
                for entry in recent_entries:
                    lines.append(f"{entry['speaker']}: {entry['content']}")
            else:
                lines.append("【これまでの議論】")
                for entry in self.dialogue_history:
                    lines.append(f"{entry['speaker']}: {entry['content']}")

            lines.append("")

            # Last message emphasis
            last = self.dialogue_history[-1]
            other_name = "あゆ" if speaker.name == "yana" else "やな"
            lines.append(f"【相手（{other_name}）の最新発言】")
            lines.append(last["content"])
            lines.append("")
            lines.append("相手の発言を踏まえて、あなたの意見を述べてください。")

        return "\n".join(lines)
