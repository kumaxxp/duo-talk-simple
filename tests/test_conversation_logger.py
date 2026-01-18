"""Tests for ConversationLogger."""

import os
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from core.conversation_logger import ConversationLogger


class TestConversationLoggerInit:
    """ConversationLogger初期化のテスト"""

    def test_init_creates_log_directory(self):
        """ログディレクトリが作成されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "test_logs")
            logger = ConversationLogger(log_dir=log_dir)
            assert os.path.exists(log_dir)

    def test_init_with_existing_directory(self):
        """既存ディレクトリでも正常動作すること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            assert logger.log_dir == Path(tmpdir)


class TestConversationLoggerSession:
    """セッション管理のテスト"""

    def test_start_session_creates_file(self):
        """セッション開始でファイルが作成されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            session_id = logger.start_session("yana")

            assert session_id is not None
            assert logger._current_file is not None
            assert logger._current_file.exists()

    def test_start_session_writes_header(self):
        """ヘッダーが正しく書き込まれること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.start_session("yana")

            content = logger._current_file.read_text(encoding="utf-8")
            assert "duo-talk-simple" in content
            assert "yana" in content

    def test_end_session_returns_path(self):
        """セッション終了でパスが返されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.start_session()
            path = logger.end_session()

            assert path is not None
            assert "chat_" in path

    def test_end_session_without_start_returns_none(self):
        """開始前の終了はNoneを返すこと"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            path = logger.end_session()
            assert path is None


class TestConversationLoggerMessages:
    """メッセージログのテスト"""

    def test_log_user_message(self):
        """ユーザーメッセージが記録されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.start_session()
            logger.log_message("user", "Hello, world!")

            content = logger._current_file.read_text(encoding="utf-8")
            assert "You: Hello, world!" in content

    def test_log_assistant_message(self):
        """アシスタントメッセージが記録されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.start_session()
            logger.log_message("assistant", "Hi there!", character="yana")

            content = logger._current_file.read_text(encoding="utf-8")
            assert "yana: Hi there!" in content

    def test_log_message_auto_starts_session(self):
        """セッション未開始時に自動開始すること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.log_message("user", "Auto start test")

            assert logger._current_file is not None
            assert logger._current_file.exists()


class TestConversationLoggerCommands:
    """コマンドログのテスト"""

    def test_log_command_simple(self):
        """シンプルなコマンドが記録されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.start_session()
            logger.log_command("/switch")

            content = logger._current_file.read_text(encoding="utf-8")
            assert "[CMD] /switch" in content

    def test_log_command_with_result(self):
        """結果付きコマンドが記録されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.start_session()
            logger.log_command("/switch", "-> ayu")

            content = logger._current_file.read_text(encoding="utf-8")
            assert "[CMD] /switch -> -> ayu" in content

    def test_log_command_without_session_does_nothing(self):
        """セッションなしではログしないこと"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.log_command("/switch")  # Should not raise
            assert logger._current_file is None


class TestConversationLoggerDuoDialogue:
    """DuoDialogueログのテスト"""

    def test_log_duo_dialogue(self):
        """Duo対話が記録されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.start_session()

            history = [
                {"speaker": "yana", "content": "First message"},
                {"speaker": "ayu", "content": "Second message"},
            ]
            logger.log_duo_dialogue("Test topic", history)

            content = logger._current_file.read_text(encoding="utf-8")
            assert "AI姉妹対話モード" in content
            assert "Test topic" in content
            assert "yana: First message" in content
            assert "ayu: Second message" in content

    def test_log_duo_dialogue_with_summary(self):
        """サマリー付きDuo対話が記録されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.start_session()

            history = [{"speaker": "yana", "content": "Test"}]
            logger.log_duo_dialogue("Topic", history, summary="This is a summary")

            content = logger._current_file.read_text(encoding="utf-8")
            assert "まとめ" in content
            assert "This is a summary" in content


class TestConversationLoggerProperty:
    """プロパティのテスト"""

    def test_current_log_path_before_session(self):
        """セッション前はNoneを返すこと"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            assert logger.current_log_path is None

    def test_current_log_path_during_session(self):
        """セッション中はパスを返すこと"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ConversationLogger(log_dir=tmpdir)
            logger.start_session()
            assert logger.current_log_path is not None
            assert "chat_" in logger.current_log_path
