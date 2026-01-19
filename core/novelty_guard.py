"""NoveltyGuard for detecting and escaping conversation loops.

Monitors conversation topics and provides escape strategies when
the conversation becomes repetitive or stuck on the same topics.
"""

from __future__ import annotations

import re
import random
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from core.types import LoopCheckResult

if TYPE_CHECKING:
    from typing import Any


class LoopBreakStrategy(Enum):
    """Strategies for breaking out of conversation loops."""

    SPECIFIC_SLOT = "specific_slot"  # Request specific numbers/places/episodes
    CONFLICT_WITHIN = "conflict_within"  # Create opinion conflict between sisters
    ACTION_NEXT = "action_next"  # Decide next action
    PAST_REFERENCE = "past_reference"  # Reference past episodes
    FORCE_WHY = "force_why"  # Deep dive into "why"
    CHANGE_TOPIC = "change_topic"  # Last resort: change topic


class NoveltyGuard:
    """Monitors conversation for loops and provides escape strategies.

    Uses a sliding window to track recently used nouns/topics.
    When the same nouns appear repeatedly, suggests escape strategies.
    """

    # Default injection templates for each strategy
    DEFAULT_INJECTIONS: dict[str, str] = {
        "specific_slot": "【必須】以下のいずれかを1つ以上含めること：具体的な数値、具体的な場所、過去の具体的なエピソード",
        "conflict_within": "【推奨】姉妹の意見を対立させて、同じ話題を違う角度から掘り下げる",
        "action_next": "【推奨】次に何をするか、具体的な行動を決めてください",
        "past_reference": "【推奨】「前にもあった」「あの時は」など、過去の具体的なエピソードを参照してください",
        "force_why": "【推奨】「なぜそうなるのか」を掘り下げてください",
        "change_topic": "【必須】この話題は十分議論されました。関連する別の話題に移ってください",
    }

    def __init__(
        self,
        window_size: int = 3,
        max_topic_depth: int = 3,
        rules_path: str | Path | None = None,
    ) -> None:
        """Initialize NoveltyGuard.

        Args:
            window_size: Number of turns to track for loop detection
            max_topic_depth: Max consecutive turns on same topic before triggering
            rules_path: Path to director_rules.yaml for custom injections
        """
        self.window_size = window_size
        self.max_topic_depth = max_topic_depth
        self._rules: dict[str, Any] = {}
        self._injections: dict[str, str] = self.DEFAULT_INJECTIONS.copy()

        # Sliding window of noun sets for each turn
        self._noun_history: list[set[str]] = []
        # Track consecutive appearances of specific nouns
        self._consecutive_count: int = 0
        # Track current stuck nouns
        self._stuck_nouns: list[str] = []
        # Track strategy usage to avoid repetition
        self._used_strategies: list[LoopBreakStrategy] = []

        if rules_path:
            self._load_rules(rules_path)

    def _load_rules(self, rules_path: str | Path) -> None:
        """Load loop break strategies from rules file."""
        path = Path(rules_path)
        if not path.exists():
            return

        self._rules = yaml.safe_load(path.read_text(encoding="utf-8"))
        strategies = self._rules.get("loop_break_strategies", [])

        for strategy in strategies:
            strategy_id = strategy.get("id", "")
            injection = strategy.get("injection", "")
            if strategy_id and injection:
                self._injections[strategy_id] = injection

    def check_and_update(self, text: str, update: bool = True) -> LoopCheckResult:
        """Check if conversation is looping and update state.

        Args:
            text: The response text to check
            update: Whether to update internal state (set False for preview)

        Returns:
            LoopCheckResult with detection status and escape strategy
        """
        current_nouns = self.extract_nouns(text)

        # Find nouns that appear in recent history
        overlapping_nouns: set[str] = set()
        for past_nouns in self._noun_history[-self.window_size :]:
            overlapping_nouns |= current_nouns & past_nouns

        # Check for loop (same nouns appearing repeatedly)
        if len(overlapping_nouns) >= 2:
            # Potential loop detected
            consecutive = self._consecutive_count + 1 if update else self._consecutive_count

            if consecutive >= self.max_topic_depth:
                # Loop confirmed - select escape strategy
                strategy = self._select_strategy()
                injection = self._generate_injection(strategy, list(overlapping_nouns))

                if update:
                    self._consecutive_count = consecutive
                    self._stuck_nouns = list(overlapping_nouns)
                    self._noun_history.append(current_nouns)
                    self._used_strategies.append(strategy)
                    # Keep history bounded
                    if len(self._noun_history) > self.window_size * 2:
                        self._noun_history = self._noun_history[-self.window_size :]

                return LoopCheckResult(
                    loop_detected=True,
                    stuck_nouns=list(overlapping_nouns),
                    strategy=strategy.value,
                    injection=injection,
                    consecutive_count=consecutive,
                )

            if update:
                self._consecutive_count = consecutive
                self._stuck_nouns = list(overlapping_nouns)
                self._noun_history.append(current_nouns)

            return LoopCheckResult(
                loop_detected=False,
                stuck_nouns=list(overlapping_nouns),
                consecutive_count=consecutive,
            )

        # No loop - reset consecutive count
        if update:
            self._consecutive_count = 0
            self._stuck_nouns = []
            self._noun_history.append(current_nouns)
            # Keep history bounded
            if len(self._noun_history) > self.window_size * 2:
                self._noun_history = self._noun_history[-self.window_size :]

        return LoopCheckResult(
            loop_detected=False,
            stuck_nouns=[],
            consecutive_count=0,
        )

    def extract_nouns(self, text: str) -> set[str]:
        """Extract nouns from text using regex patterns.

        Simple noun extraction without external NLP library.
        Focuses on katakana words and common noun patterns.
        """
        nouns: set[str] = set()

        # Extract katakana words (often technical terms/proper nouns)
        katakana_pattern = r"[ァ-ヶー]{2,}"
        nouns.update(re.findall(katakana_pattern, text))

        # Extract common noun endings (Japanese)
        noun_endings = [
            r"\w+機",
            r"\w+器",
            r"\w+法",
            r"\w+式",
            r"\w+化",
            r"\w+性",
            r"\w+率",
            r"\w+値",
            r"\w+点",
            r"\w+線",
            r"\w+面",
            r"\w+体",
            r"\w+力",
            r"\w+度",
        ]
        for pattern in noun_endings:
            matches = re.findall(pattern, text)
            nouns.update(matches)

        # Extract words after particles that typically precede nouns
        particle_pattern = r"(?:の|が|を|は|に|で|と|から|まで|より)([ぁ-んァ-ヶー一-龥]{2,})"
        matches = re.findall(particle_pattern, text)
        nouns.update(matches)

        # Filter out common words that aren't meaningful for loop detection
        stop_words = {
            "これ",
            "それ",
            "あれ",
            "どれ",
            "ここ",
            "そこ",
            "あそこ",
            "こと",
            "もの",
            "やつ",
            "わけ",
            "ほう",
            "とき",
            "ところ",
            "ため",
        }
        nouns -= stop_words

        return nouns

    def _select_strategy(self) -> LoopBreakStrategy:
        """Select an escape strategy, avoiding recently used ones."""
        all_strategies = list(LoopBreakStrategy)

        # Remove recently used strategies
        available = [s for s in all_strategies if s not in self._used_strategies[-3:]]

        # If all strategies used recently, reset
        if not available:
            available = all_strategies
            self._used_strategies = []

        # Prefer non-change_topic strategies unless really stuck
        if self._consecutive_count < self.max_topic_depth + 2:
            available = [s for s in available if s != LoopBreakStrategy.CHANGE_TOPIC]
            if not available:
                available = [s for s in all_strategies if s != LoopBreakStrategy.CHANGE_TOPIC]

        return random.choice(available)

    def _generate_injection(self, strategy: LoopBreakStrategy, stuck_nouns: list[str]) -> str:
        """Generate injection text for the selected strategy."""
        base_injection = self._injections.get(strategy.value, "")

        # Add context about stuck nouns if available
        if stuck_nouns and len(stuck_nouns) <= 3:
            noun_list = "、".join(stuck_nouns[:3])
            context = f"（繰り返されているキーワード: {noun_list}）"
            return f"{base_injection}\n{context}"

        return base_injection

    def reset(self) -> None:
        """Reset all tracking state."""
        self._noun_history = []
        self._consecutive_count = 0
        self._stuck_nouns = []
        self._used_strategies = []

    def get_state(self) -> dict[str, Any]:
        """Get current state for debugging/logging."""
        return {
            "noun_history_length": len(self._noun_history),
            "consecutive_count": self._consecutive_count,
            "stuck_nouns": self._stuck_nouns,
            "recent_strategies": [s.value for s in self._used_strategies[-3:]],
        }
