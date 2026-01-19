"""Tests for DuoDialogueManager - TDD approach."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest


class TestDuoDialogueManagerInit:
    """Test DuoDialogueManager initialization."""

    def test_init_with_characters(self):
        """Manager should initialize with two characters."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)

        assert manager.yana == yana_mock
        assert manager.ayu == ayu_mock
        assert manager.topic is None
        assert manager.state.name == "IDLE"

    def test_init_with_config(self):
        """Manager should accept configuration options."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        config = {
            "max_turns": 8,
            "first_speaker": "ayu",
        }
        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock, config=config)

        assert manager.max_turns == 8
        assert manager.first_speaker == "ayu"


class TestDuoDialogueStart:
    """Test dialogue start functionality."""

    def test_start_dialogue_sets_topic(self):
        """Starting dialogue should set the topic."""
        from core.duo_dialogue import DuoDialogueManager, DialogueState

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("JetRacerのセンサー配置を改善したい")

        assert manager.topic == "JetRacerのセンサー配置を改善したい"
        assert manager.state == DialogueState.DIALOGUE

    def test_start_dialogue_initializes_history(self):
        """Starting dialogue should initialize empty history."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テストお題")

        assert manager.dialogue_history == []
        assert manager.turn_count == 0


class TestDuoDialogueTurns:
    """Test turn-by-turn dialogue functionality."""

    def test_next_turn_returns_speaker_and_response(self):
        """next_turn should return (speaker_name, response)."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "まず試してみようよ！"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")

        speaker, response = manager.next_turn()

        assert speaker == "yana"
        assert response == "まず試してみようよ！"

    def test_turns_alternate_between_speakers(self):
        """Speakers should alternate: yana -> ayu -> yana."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "やなの発言"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "あゆの発言"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")

        speaker1, _ = manager.next_turn()
        speaker2, _ = manager.next_turn()
        speaker3, _ = manager.next_turn()

        assert speaker1 == "yana"
        assert speaker2 == "ayu"
        assert speaker3 == "yana"

    def test_turn_count_increments(self):
        """Turn count should increment after each turn."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "test"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "test"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")

        assert manager.turn_count == 0
        manager.next_turn()
        assert manager.turn_count == 1
        manager.next_turn()
        assert manager.turn_count == 2

    def test_dialogue_history_accumulates(self):
        """Dialogue history should accumulate turns."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "やなです"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "あゆです"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")

        manager.next_turn()
        manager.next_turn()

        assert len(manager.dialogue_history) == 2
        assert manager.dialogue_history[0]["speaker"] == "yana"
        assert manager.dialogue_history[0]["content"] == "やなです"
        assert manager.dialogue_history[1]["speaker"] == "ayu"
        assert manager.dialogue_history[1]["content"] == "あゆです"


class TestDuoDialogueMaxTurns:
    """Test max turns limit."""

    def test_should_continue_true_before_max(self):
        """should_continue returns True before max turns."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "test"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "test"

        manager = DuoDialogueManager(
            yana=yana_mock, ayu=ayu_mock, config={"max_turns": 3}
        )
        manager.start_dialogue("テスト")

        manager.next_turn()
        assert manager.should_continue() is True

        manager.next_turn()
        assert manager.should_continue() is True

    def test_should_continue_false_at_max(self):
        """should_continue returns False at max turns."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "test"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "test"

        manager = DuoDialogueManager(
            yana=yana_mock, ayu=ayu_mock, config={"max_turns": 2}
        )
        manager.start_dialogue("テスト")

        manager.next_turn()
        manager.next_turn()

        assert manager.should_continue() is False


class TestDuoDialogueContext:
    """Test context building for character responses."""

    def test_character_receives_dialogue_context(self):
        """Character.respond should receive dialogue history context."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "やなの返答"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "あゆの返答"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("センサー改善")

        # First turn - yana gets topic
        manager.next_turn()
        call_args = yana_mock.respond.call_args
        assert "センサー改善" in call_args[0][0]

        # Second turn - ayu gets yana's response
        manager.next_turn()
        call_args = ayu_mock.respond.call_args
        assert "やなの返答" in call_args[0][0]


class TestDuoDialogueConvergence:
    """Test convergence detection."""

    def test_convergence_detected_by_keywords(self):
        """Convergence should be detected when keywords appear after min_turns."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        # Turn 1: yana[0], Turn 3: yana[1] (with convergence keyword)
        yana_mock.respond.side_effect = ["議論中", "まとめると、センサーを5度傾けるのが良さそう。"]
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "議論中"

        config = {
            "max_turns": 10,
            "min_turns": 3,  # Explicitly set for clarity
            "convergence_keywords": ["結論として", "まとめると", "決まりだね"],
        }
        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock, config=config)
        manager.start_dialogue("テスト")

        manager.next_turn()  # Turn 1 - yana: "議論中"
        manager.next_turn()  # Turn 2 - ayu: "議論中"
        manager.next_turn()  # Turn 3 - yana: "まとめると..."

        assert manager.check_convergence() is True

    def test_no_convergence_without_keywords(self):
        """Convergence should not be detected without keywords."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "まず試してみよう"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "データを確認します"

        config = {
            "max_turns": 10,
            "convergence_keywords": ["結論として", "まとめると"],
        }
        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock, config=config)
        manager.start_dialogue("テスト")

        manager.next_turn()

        assert manager.check_convergence() is False

    def test_convergence_ends_dialogue(self):
        """Convergence detection should end the dialogue after min_turns."""
        from core.duo_dialogue import DuoDialogueManager, DialogueState

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        # Turn 1: yana[0], Turn 3: yana[1] (with convergence keyword)
        yana_mock.respond.side_effect = ["議論中", "結論として、これで行こう"]
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "議論中"

        config = {
            "max_turns": 10,
            "min_turns": 3,
            "convergence_keywords": ["結論として"],
        }
        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock, config=config)
        manager.start_dialogue("テスト")

        manager.next_turn()  # Turn 1 - yana: "議論中"
        manager.next_turn()  # Turn 2 - ayu: "議論中"
        manager.next_turn()  # Turn 3 - yana: "結論として..."

        # should_continue checks convergence and updates state
        assert manager.should_continue() is False
        assert manager.state == DialogueState.SUMMARIZING or manager.state == DialogueState.COMPLETED


class TestDuoDialogueSummary:
    """Test summary generation."""

    def test_get_summary_returns_string(self):
        """get_summary should return a summary string."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.side_effect = ["やなの意見", "結論として同意"]
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "あゆの意見"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("センサー改善")

        manager.next_turn()  # yana
        manager.next_turn()  # ayu
        manager.next_turn()  # yana

        summary = manager.get_summary()

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "センサー改善" in summary

    def test_summary_includes_topic_and_history(self):
        """Summary should include topic and dialogue content."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "角度を変えよう"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "データ検証します"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("バッテリー対策")

        manager.next_turn()
        manager.next_turn()

        summary = manager.get_summary()

        assert "バッテリー対策" in summary
        assert "yana" in summary or "やな" in summary
        assert "ayu" in summary or "あゆ" in summary


class TestDuoDialogueState:
    """Test dialogue state management."""

    def test_initial_state_is_idle(self):
        """Initial state should be IDLE."""
        from core.duo_dialogue import DuoDialogueManager, DialogueState

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)

        assert manager.state == DialogueState.IDLE

    def test_state_transitions_to_dialogue(self):
        """State should transition to DIALOGUE on start."""
        from core.duo_dialogue import DuoDialogueManager, DialogueState

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")

        assert manager.state == DialogueState.DIALOGUE

    def test_state_transitions_to_completed(self):
        """State should transition to COMPLETED when done."""
        from core.duo_dialogue import DuoDialogueManager, DialogueState

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "test"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "test"

        manager = DuoDialogueManager(
            yana=yana_mock, ayu=ayu_mock, config={"max_turns": 2}
        )
        manager.start_dialogue("テスト")

        manager.next_turn()
        manager.next_turn()

        # should_continue() triggers state check
        manager.should_continue()

        assert manager.state == DialogueState.COMPLETED


class TestDuoDialogueQuality:
    """Test dialogue quality improvements - Phase 1."""

    def test_context_includes_duo_rules(self):
        """Context should include duo-specific conversation rules."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "test"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        manager.next_turn()

        # Check that respond was called with duo-specific context
        call_args = yana_mock.respond.call_args[0][0]
        assert "姉妹対話" in call_args or "対話ルール" in call_args

    def test_yana_receives_decisive_instructions(self):
        """Yana should receive instructions to be decisive in duo mode."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "test"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "test"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        manager.next_turn()

        call_args = yana_mock.respond.call_args[0][0]
        # Yana should be told to be decisive, not delegate to sister
        assert "委ねる" in call_args or "決め" in call_args or "判断" in call_args

    def test_ayu_receives_skeptical_instructions(self):
        """Ayu should receive instructions to be skeptical in duo mode."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "test"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "test"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        manager.next_turn()  # yana
        manager.next_turn()  # ayu

        call_args = ayu_mock.respond.call_args[0][0]
        # Ayu should be told to be skeptical, challenge sister
        assert "ツッコ" in call_args or "同意" in call_args or "疑" in call_args

    def test_min_turns_enforced(self):
        """Convergence should not trigger before min_turns."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        # First turn has convergence keyword, but min_turns=3 should prevent early end
        yana_mock.respond.return_value = "結論として、これでいこう"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "test"

        config = {
            "max_turns": 10,
            "min_turns": 3,
            "convergence_keywords": ["結論として"],
        }
        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock, config=config)
        manager.start_dialogue("テスト")

        manager.next_turn()  # Turn 1 - has convergence keyword

        # Should still continue because min_turns=3
        assert manager.should_continue() is True

    def test_history_summarization_for_long_dialogues(self):
        """Long dialogue history should be summarized to prevent repetition."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "やなの発言"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "あゆの発言"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")

        # Run 6 turns
        for _ in range(6):
            manager.next_turn()

        # On 7th turn, context should not include all 6 previous full messages
        manager.next_turn()
        call_args = yana_mock.respond.call_args[0][0]

        # Should have some form of summarization indicator or limited history
        # Either "要約" or limited number of full entries
        full_entry_count = call_args.count("やなの発言") + call_args.count("あゆの発言")
        assert full_entry_count <= 4 or "要約" in call_args or "概要" in call_args


class TestDuoDialogueResponseValidation:
    """Test response validation for quality control."""

    def test_detect_question_baton_toss(self):
        """Should detect when response ends with question delegation."""
        from core.duo_dialogue import validate_response_quality

        # Ends with question to other character
        response = "いいね！あゆはどう思う？"
        issues = validate_response_quality(response, "yana")

        assert "question_baton_toss" in issues

    def test_detect_repetitive_phrases(self):
        """Should detect AI-ism phrases that indicate repetitive responses."""
        from core.duo_dialogue import validate_response_quality

        response = "承知しました。データに基づいて分析します。"
        issues = validate_response_quality(response, "ayu")

        assert "ai_ism" in issues

    def test_valid_response_returns_empty(self):
        """Valid response should return empty issues list."""
        from core.duo_dialogue import validate_response_quality

        response = "平気平気、まず動かしてみよう。"
        issues = validate_response_quality(response, "yana")

        assert len(issues) == 0


class TestDuoDialogueQualityReport:
    """Test get_quality_report() method - TDD strict approach."""

    def test_get_quality_report_returns_dict(self):
        """get_quality_report should return a dictionary with required keys."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "テスト発言"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "テスト返答"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        manager.next_turn()
        manager.next_turn()

        report = manager.get_quality_report()

        assert isinstance(report, dict)
        assert "total_turns" in report
        assert "issues_by_speaker" in report
        assert "issue_count" in report
        assert "quality_score" in report

    def test_total_turns_reflects_actual_count(self):
        """total_turns should reflect the actual number of turns in the dialogue."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "発言"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "返答"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        manager.next_turn()
        manager.next_turn()
        manager.next_turn()

        report = manager.get_quality_report()

        assert report["total_turns"] == 3

    def test_issues_by_speaker_detects_question_baton_toss(self):
        """issues_by_speaker should detect question_baton_toss issues."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        # This response ends with question delegation - a quality issue
        yana_mock.respond.return_value = "いいアイデアだね！あゆはどう思う？"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "データを確認しました"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        manager.next_turn()  # yana with question baton toss
        manager.next_turn()  # ayu with good response

        report = manager.get_quality_report()

        assert "yana" in report["issues_by_speaker"]
        assert "question_baton_toss" in report["issues_by_speaker"]["yana"]

    def test_issue_count_sums_all_issues(self):
        """issue_count should sum all issues across all speakers."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        # Question baton toss issue
        yana_mock.respond.return_value = "これはどう思う？"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        # AI-ism issue
        ayu_mock.respond.return_value = "承知しました。分析します。"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        manager.next_turn()  # yana - 1 issue
        manager.next_turn()  # ayu - 1 issue

        report = manager.get_quality_report()

        assert report["issue_count"] == 2

    def test_quality_score_perfect_when_no_issues(self):
        """quality_score should be 1.0 when there are no issues."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "まず試してみよう！"  # Good response
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "いいね、やってみよう。"  # Good response

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        manager.next_turn()
        manager.next_turn()

        report = manager.get_quality_report()

        assert report["quality_score"] == 1.0

    def test_quality_score_decreases_with_issues(self):
        """quality_score should decrease when issues are found."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "いいアイデアだね！どう思う？"  # Bad - question baton
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "承知しました。"  # Bad - ai_ism

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        manager.next_turn()
        manager.next_turn()

        report = manager.get_quality_report()

        # With 2 issues in 2 turns, score should be less than 1.0
        assert report["quality_score"] < 1.0
        assert report["quality_score"] >= 0.0

    def test_quality_report_on_empty_dialogue(self):
        """get_quality_report should work on dialogue with no turns."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock)
        manager.start_dialogue("テスト")
        # No turns executed

        report = manager.get_quality_report()

        assert report["total_turns"] == 0
        assert report["issues_by_speaker"] == {}
        assert report["issue_count"] == 0
        assert report["quality_score"] == 1.0  # No issues means perfect score
