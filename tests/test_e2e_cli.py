# tests/test_e2e_cli.py
"""
CLI E2E Tests for duo-talk-simple

These tests simulate real user interactions with the CLI application.
Uses pexpect for interactive CLI testing.

Critical User Journeys:
1. Application startup → Welcome message
2. Basic conversation → Character response
3. /switch command → Character switching
4. /clear command → History clearing
5. /duo command → AI-to-AI dialogue
6. /exit command → Graceful exit with log save
"""

import pytest
import pexpect
import os
import sys
import time

# Skip all tests if not on a Unix-like system (pexpect requires pty)
pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="pexpect requires Unix-like system"
)

# Timeout for CLI responses (LLM can be slow)
CLI_TIMEOUT = 120  # 2 minutes for LLM responses
STARTUP_TIMEOUT = 30  # 30 seconds for startup


class TestCLIE2E:
    """CLI End-to-End Tests"""

    @pytest.fixture
    def cli_process(self):
        """Start the CLI application"""
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chat_py = os.path.join(project_root, "chat.py")

        # Start the CLI
        child = pexpect.spawn(
            f"python {chat_py}",
            encoding="utf-8",
            timeout=CLI_TIMEOUT,
            cwd=project_root,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )

        # Wait for startup
        yield child

        # Cleanup: try to exit gracefully
        try:
            child.sendline("/exit")
            child.expect(pexpect.EOF, timeout=10)
        except Exception:
            child.terminate(force=True)

    def test_startup_welcome_message(self, cli_process):
        """TC-E2E-001: アプリ起動時にウェルカムメッセージが表示される"""
        # Wait for welcome message
        index = cli_process.expect(
            ["duo-talk-simple", pexpect.TIMEOUT, pexpect.EOF],
            timeout=STARTUP_TIMEOUT,
        )

        assert index == 0, "Welcome message not displayed"

        # Wait for prompt
        cli_process.expect(
            ["You", "現在のキャラクター"],
            timeout=STARTUP_TIMEOUT,
        )

    def test_basic_conversation(self, cli_process):
        """TC-E2E-002: 基本的な会話ができる"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Send a message
        cli_process.sendline("こんにちは")

        # Wait for response (character name in brackets)
        index = cli_process.expect(
            [r"\[yana\]", r"\[ayu\]", pexpect.TIMEOUT],
            timeout=CLI_TIMEOUT,
        )

        assert index in [0, 1], "No character response received"

        # Get the response text
        cli_process.expect(r"\[You\]", timeout=CLI_TIMEOUT)

    def test_switch_character(self, cli_process):
        """TC-E2E-003: /switch でキャラクター切替ができる"""
        # Wait for startup (includes character name)
        index = cli_process.expect(
            ["現在のキャラクター: yana", "現在のキャラクター: ayu", pexpect.TIMEOUT],
            timeout=STARTUP_TIMEOUT,
        )
        assert index in [0, 1], "Startup with character name not shown"

        # Wait for prompt
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Switch character
        cli_process.sendline("/switch")

        # Expect switch confirmation
        index = cli_process.expect(
            ["キャラクター切り替え", pexpect.TIMEOUT],
            timeout=10,
        )

        assert index == 0, "Character switch not confirmed"

    def test_clear_history(self, cli_process):
        """TC-E2E-004: /clear で履歴クリアができる"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Have a conversation first
        cli_process.sendline("こんにちは")
        cli_process.expect(r"\[yana\]|\[ayu\]", timeout=CLI_TIMEOUT)

        # Clear history
        cli_process.sendline("/clear")

        # Expect confirmation
        index = cli_process.expect(
            ["クリア", "履歴", pexpect.TIMEOUT],
            timeout=10,
        )

        assert index in [0, 1], "Clear confirmation not received"

    def test_help_command(self, cli_process):
        """TC-E2E-005: /help でヘルプが表示される"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Request help
        cli_process.sendline("/help")

        # Expect help content
        index = cli_process.expect(
            ["コマンド一覧", "/switch", "/duo", pexpect.TIMEOUT],
            timeout=10,
        )

        assert index in [0, 1, 2], "Help not displayed"

    def test_status_command(self, cli_process):
        """TC-E2E-006: /status で状態が表示される"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Request status
        cli_process.sendline("/status")

        # Expect status info
        index = cli_process.expect(
            ["現在のキャラクター", "会話履歴", pexpect.TIMEOUT],
            timeout=10,
        )

        assert index in [0, 1], "Status not displayed"

    def test_exit_graceful(self, cli_process):
        """TC-E2E-007: /exit で正常終了する"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Exit
        cli_process.sendline("/exit")

        # Expect goodbye message
        index = cli_process.expect(
            ["さようなら", "会話ログ保存", pexpect.EOF],
            timeout=10,
        )

        assert index in [0, 1, 2], "Exit not handled gracefully"

    def test_unknown_command(self, cli_process):
        """TC-E2E-008: 不明なコマンドでエラーメッセージが表示される"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Send unknown command
        cli_process.sendline("/unknown_command")

        # Expect error message
        index = cli_process.expect(
            ["不明なコマンド", "/help", pexpect.TIMEOUT],
            timeout=10,
        )

        assert index in [0, 1], "Unknown command error not displayed"


class TestDuoDialogueE2E:
    """AI-to-AI Dialogue E2E Tests"""

    @pytest.fixture
    def cli_process(self):
        """Start the CLI application"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chat_py = os.path.join(project_root, "chat.py")

        child = pexpect.spawn(
            f"python {chat_py}",
            encoding="utf-8",
            timeout=CLI_TIMEOUT,
            cwd=project_root,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )

        yield child

        try:
            child.sendline("/exit")
            child.expect(pexpect.EOF, timeout=10)
        except Exception:
            child.terminate(force=True)

    def test_duo_command_usage(self, cli_process):
        """TC-E2E-DUO-001: /duo コマンドの使い方が表示される"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Send /duo without topic
        cli_process.sendline("/duo")

        # Expect usage message
        index = cli_process.expect(
            ["使い方", "/duo <お題>", "例:", pexpect.TIMEOUT],
            timeout=10,
        )

        assert index in [0, 1, 2], "Usage message not displayed"

    @pytest.mark.slow
    def test_duo_dialogue_start(self, cli_process):
        """TC-E2E-DUO-002: /duo でAI同士対話が開始される"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Start duo dialogue
        cli_process.sendline("/duo テスト用のお題")

        # Expect dialogue mode banner
        index = cli_process.expect(
            ["AI姉妹対話モード", "お題:", pexpect.TIMEOUT],
            timeout=30,
        )

        assert index in [0, 1], "Duo dialogue mode not started"

        # Wait for first turn
        index = cli_process.expect(
            [r"\[Turn", "yana:", "ayu:", pexpect.TIMEOUT],
            timeout=CLI_TIMEOUT,
        )

        assert index in [0, 1, 2], "First turn not received"


class TestConversationFlowE2E:
    """Conversation Flow E2E Tests"""

    @pytest.fixture
    def cli_process(self):
        """Start the CLI application"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chat_py = os.path.join(project_root, "chat.py")

        child = pexpect.spawn(
            f"python {chat_py}",
            encoding="utf-8",
            timeout=CLI_TIMEOUT,
            cwd=project_root,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )

        yield child

        try:
            child.sendline("/exit")
            child.expect(pexpect.EOF, timeout=10)
        except Exception:
            child.terminate(force=True)

    @pytest.mark.slow
    def test_multi_turn_conversation(self, cli_process):
        """TC-E2E-FLOW-001: 複数ターンの会話ができる"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        messages = ["こんにちは", "JetRacerって何？", "ありがとう"]

        for msg in messages:
            # Send message
            cli_process.sendline(msg)

            # Wait for response
            index = cli_process.expect(
                [r"\[yana\]", r"\[ayu\]", pexpect.TIMEOUT],
                timeout=CLI_TIMEOUT,
            )

            assert index in [0, 1], f"No response for: {msg}"

            # Wait for next prompt
            cli_process.expect(r"\[You\]", timeout=CLI_TIMEOUT)

    @pytest.mark.slow
    def test_rag_context_in_response(self, cli_process):
        """TC-E2E-FLOW-002: RAGコンテキストが応答に反映される"""
        # Wait for startup
        cli_process.expect(r"\[You\]", timeout=STARTUP_TIMEOUT)

        # Ask about JetRacer (should use RAG)
        cli_process.sendline("JetRacerのセンサーについて教えて")

        # Wait for response
        cli_process.expect(r"\[yana\]|\[ayu\]", timeout=CLI_TIMEOUT)

        # Get response content (read until next prompt)
        cli_process.expect(r"\[You\]", timeout=CLI_TIMEOUT)
        response = cli_process.before

        # Check for technical keywords
        keywords = ["センサー", "超音波", "IMU", "カメラ", "JetRacer"]
        assert any(
            kw in response for kw in keywords
        ), f"RAG context not reflected in response: {response[:200]}"


# Pytest configuration for slow tests
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
