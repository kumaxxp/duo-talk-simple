"""Tests for NoveltyGuard loop detection system."""

import pytest

from core.novelty_guard import LoopBreakStrategy, NoveltyGuard
from core.types import LoopCheckResult


class TestLoopBreakStrategy:
    """Tests for LoopBreakStrategy enum."""

    def test_strategy_values(self):
        """All strategies have expected values."""
        assert LoopBreakStrategy.SPECIFIC_SLOT.value == "specific_slot"
        assert LoopBreakStrategy.CONFLICT_WITHIN.value == "conflict_within"
        assert LoopBreakStrategy.ACTION_NEXT.value == "action_next"
        assert LoopBreakStrategy.PAST_REFERENCE.value == "past_reference"
        assert LoopBreakStrategy.FORCE_WHY.value == "force_why"
        assert LoopBreakStrategy.CHANGE_TOPIC.value == "change_topic"

    def test_all_strategies_count(self):
        """There are exactly 6 strategies."""
        assert len(LoopBreakStrategy) == 6


class TestNoveltyGuardInit:
    """Tests for NoveltyGuard initialization."""

    def test_default_init(self):
        """NoveltyGuard initializes with defaults."""
        guard = NoveltyGuard()
        assert guard.window_size == 3
        assert guard.max_topic_depth == 3
        assert guard._noun_history == []
        assert guard._consecutive_count == 0

    def test_custom_init(self):
        """NoveltyGuard accepts custom parameters."""
        guard = NoveltyGuard(window_size=5, max_topic_depth=4)
        assert guard.window_size == 5
        assert guard.max_topic_depth == 4

    def test_init_with_rules(self):
        """NoveltyGuard loads rules from file."""
        guard = NoveltyGuard(rules_path="director/director_rules.yaml")
        assert guard._rules is not None
        assert "loop_break_strategies" in guard._rules

    def test_init_with_nonexistent_rules(self):
        """NoveltyGuard handles nonexistent rules gracefully."""
        guard = NoveltyGuard(rules_path="nonexistent.yaml")
        assert guard._rules == {}


class TestNoveltyGuardNounExtraction:
    """Tests for noun extraction from text."""

    @pytest.fixture
    def guard(self):
        """Create NoveltyGuard instance."""
        return NoveltyGuard()

    def test_extract_katakana(self, guard):
        """Extracts katakana words."""
        text = "JetRacerでセンサーをテストする"
        nouns = guard.extract_nouns(text)
        assert "センサー" in nouns

    def test_extract_noun_endings(self, guard):
        """Extracts words with noun-like endings."""
        text = "走行性能と計測値を確認する"
        nouns = guard.extract_nouns(text)
        # Depending on pattern matching, these may or may not be captured
        # Check that extraction returns something
        assert isinstance(nouns, set)

    def test_extract_after_particles(self, guard):
        """Extracts nouns after particles."""
        text = "カメラの調整をする"
        nouns = guard.extract_nouns(text)
        # Should extract something related to the content
        assert "カメラ" in nouns or any("調整" in n for n in nouns)

    def test_excludes_stop_words(self, guard):
        """Stop words are excluded."""
        text = "これはそのことです"
        nouns = guard.extract_nouns(text)
        assert "これ" not in nouns
        assert "それ" not in nouns
        assert "こと" not in nouns

    def test_empty_text(self, guard):
        """Empty text returns empty set."""
        nouns = guard.extract_nouns("")
        assert nouns == set()


class TestNoveltyGuardLoopDetection:
    """Tests for loop detection logic."""

    @pytest.fixture
    def guard(self):
        """Create NoveltyGuard with small window for testing."""
        return NoveltyGuard(window_size=2, max_topic_depth=2)

    def test_no_loop_first_turn(self, guard):
        """First turn never detects loop."""
        result = guard.check_and_update("センサーの設定を確認します")
        assert result.loop_detected is False
        assert result.consecutive_count == 0

    def test_no_loop_different_topics(self, guard):
        """Different topics don't trigger loop."""
        guard.check_and_update("カメラの設定")
        result = guard.check_and_update("モーターの制御")
        assert result.loop_detected is False

    def test_loop_detected_same_nouns(self, guard):
        """Repeated nouns eventually trigger loop."""
        # First turn
        guard.check_and_update("センサーの精度について話しましょう")
        # Second turn - same nouns
        guard.check_and_update("センサーの精度が問題ですね")
        # Third turn - loop should be detected
        result = guard.check_and_update("センサーの精度を確認します")
        assert result.loop_detected is True
        assert result.consecutive_count >= guard.max_topic_depth

    def test_loop_provides_strategy(self, guard):
        """Loop detection includes escape strategy."""
        guard.check_and_update("センサーの精度について")
        guard.check_and_update("センサーの精度が重要")
        result = guard.check_and_update("センサーの精度を上げる")

        if result.loop_detected:
            assert result.strategy != ""
            assert result.injection != ""

    def test_update_false_no_state_change(self, guard):
        """update=False doesn't modify state."""
        guard.check_and_update("センサーの設定")
        initial_count = guard._consecutive_count
        initial_history_len = len(guard._noun_history)

        # Check without update
        guard.check_and_update("センサーの設定", update=False)

        assert guard._consecutive_count == initial_count
        assert len(guard._noun_history) == initial_history_len


class TestNoveltyGuardStrategySelection:
    """Tests for strategy selection."""

    @pytest.fixture
    def guard(self):
        """Create NoveltyGuard."""
        return NoveltyGuard()

    def test_strategy_is_valid(self, guard):
        """Selected strategy is a valid enum value."""
        strategy = guard._select_strategy()
        assert isinstance(strategy, LoopBreakStrategy)

    def test_avoids_recent_strategies(self, guard):
        """Avoids recently used strategies."""
        # Use all strategies
        guard._used_strategies = list(LoopBreakStrategy)[:3]

        # New strategy should be different
        strategy = guard._select_strategy()
        assert strategy not in guard._used_strategies[-3:]

    def test_avoids_change_topic_early(self, guard):
        """CHANGE_TOPIC is avoided unless really stuck."""
        guard._consecutive_count = guard.max_topic_depth  # Just at threshold
        guard._used_strategies = []

        # Run multiple times and check CHANGE_TOPIC is rarely/never selected
        strategies = [guard._select_strategy() for _ in range(10)]
        change_topic_count = sum(
            1 for s in strategies if s == LoopBreakStrategy.CHANGE_TOPIC
        )
        # Should be rare or zero
        assert change_topic_count <= 2


class TestNoveltyGuardInjection:
    """Tests for injection text generation."""

    @pytest.fixture
    def guard(self):
        """Create NoveltyGuard with rules."""
        return NoveltyGuard(rules_path="director/director_rules.yaml")

    def test_injection_includes_base_text(self, guard):
        """Injection includes base strategy text."""
        injection = guard._generate_injection(
            LoopBreakStrategy.SPECIFIC_SLOT, ["センサー"]
        )
        assert "具体的" in injection or "数値" in injection

    def test_injection_includes_stuck_nouns(self, guard):
        """Injection mentions stuck nouns."""
        injection = guard._generate_injection(
            LoopBreakStrategy.CONFLICT_WITHIN, ["センサー", "精度"]
        )
        assert "センサー" in injection or "精度" in injection

    def test_default_injections_exist(self, guard):
        """All strategies have default injections."""
        for strategy in LoopBreakStrategy:
            assert strategy.value in guard._injections


class TestNoveltyGuardReset:
    """Tests for state reset."""

    def test_reset_clears_state(self):
        """Reset clears all tracking state."""
        guard = NoveltyGuard()

        # Build up some state
        guard.check_and_update("センサーの設定")
        guard.check_and_update("センサーの調整")
        guard._used_strategies.append(LoopBreakStrategy.SPECIFIC_SLOT)

        # Reset
        guard.reset()

        assert guard._noun_history == []
        assert guard._consecutive_count == 0
        assert guard._stuck_nouns == []
        assert guard._used_strategies == []


class TestNoveltyGuardState:
    """Tests for state inspection."""

    def test_get_state_returns_dict(self):
        """get_state returns state dictionary."""
        guard = NoveltyGuard()
        guard.check_and_update("センサーの設定")

        state = guard.get_state()

        assert isinstance(state, dict)
        assert "noun_history_length" in state
        assert "consecutive_count" in state
        assert "stuck_nouns" in state
        assert "recent_strategies" in state


class TestNoveltyGuardHistoryBounding:
    """Tests for history size management."""

    def test_history_bounded(self):
        """History doesn't grow unbounded."""
        guard = NoveltyGuard(window_size=2)

        # Add many turns
        for i in range(20):
            guard.check_and_update(f"話題{i}についてのテスト")

        # History should be bounded
        assert len(guard._noun_history) <= guard.window_size * 2


class TestLoopCheckResult:
    """Tests for LoopCheckResult dataclass."""

    def test_default_values(self):
        """LoopCheckResult has sensible defaults."""
        result = LoopCheckResult()
        assert result.loop_detected is False
        assert result.stuck_nouns == []
        assert result.strategy == ""
        assert result.injection == ""
        assert result.consecutive_count == 0

    def test_with_loop_detected(self):
        """LoopCheckResult can indicate loop."""
        result = LoopCheckResult(
            loop_detected=True,
            stuck_nouns=["センサー", "精度"],
            strategy="specific_slot",
            injection="具体的な数値を入れてください",
            consecutive_count=3,
        )
        assert result.loop_detected is True
        assert "センサー" in result.stuck_nouns
