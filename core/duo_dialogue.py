"""DuoDialogueManager - AI-to-AI dialogue management for yana and ayu."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from core.character import Character


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
    first_speaker: str = field(default="yana", init=False)
    convergence_keywords: List[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Initialize configuration values."""
        self.max_turns = self.config.get("max_turns", 10)
        self.first_speaker = self.config.get("first_speaker", "yana")
        self.convergence_keywords = self.config.get(
            "convergence_keywords",
            ["結論として", "まとめると", "決まりだね", "そうしましょう"]
        )
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

        Convergence is detected when keywords appear in recent messages.

        Returns:
            True if convergence is detected, False otherwise.
        """
        if not self.dialogue_history:
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

    def _build_context_for_speaker(self, speaker: "Character") -> str:
        """Build the context string for a speaker.

        Args:
            speaker: The character who will respond.

        Returns:
            Context string including topic and dialogue history.
        """
        lines: List[str] = []

        # Add topic
        lines.append(f"【お題】{self.topic}")
        lines.append("")

        if not self.dialogue_history:
            # First turn - just the topic
            lines.append("あなたから議論を始めてください。")
        else:
            # Build history context
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
