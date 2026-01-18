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
        """Convergence should be detected when keywords appear."""
        from core.duo_dialogue import DuoDialogueManager

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "まとめると、センサーを5度傾けるのが良さそう。"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"
        ayu_mock.respond.return_value = "同意です"

        config = {
            "max_turns": 10,
            "convergence_keywords": ["結論として", "まとめると", "決まりだね"],
        }
        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock, config=config)
        manager.start_dialogue("テスト")

        manager.next_turn()  # yana: "まとめると..."

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
        """Convergence detection should end the dialogue."""
        from core.duo_dialogue import DuoDialogueManager, DialogueState

        yana_mock = MagicMock()
        yana_mock.name = "yana"
        yana_mock.respond.return_value = "結論として、これで行こう"
        ayu_mock = MagicMock()
        ayu_mock.name = "ayu"

        config = {
            "max_turns": 10,
            "convergence_keywords": ["結論として"],
        }
        manager = DuoDialogueManager(yana=yana_mock, ayu=ayu_mock, config=config)
        manager.start_dialogue("テスト")

        manager.next_turn()

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
