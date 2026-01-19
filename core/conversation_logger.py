"""Conversation logger - saves conversations to text files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ConversationLogger:
    """Logger for saving conversations to text files."""

    def __init__(self, log_dir: str = "./logs/conversations"):
        """Initialize the conversation logger.

        Args:
            log_dir: Directory to save conversation logs.
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current_file: Optional[Path] = None
        self._session_id: Optional[str] = None

    def start_session(self, character_name: str = "yana") -> str:
        """Start a new conversation session.

        Args:
            character_name: Name of the initial character.

        Returns:
            Session ID (timestamp-based).
        """
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_file = self.log_dir / f"chat_{self._session_id}.txt"

        # Write header
        header = f"""=== duo-talk-simple 会話ログ ===
セッション開始: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
初期キャラクター: {character_name}
{"=" * 40}

"""
        self._current_file.write_text(header, encoding="utf-8")
        return self._session_id

    def log_message(
        self,
        role: str,
        content: str,
        character: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Log a single message.

        Args:
            role: "user" or "assistant"
            content: Message content.
            character: Character name (for assistant messages).
            metadata: Optional metadata (e.g., RAG results).
        """
        if not self._current_file:
            self.start_session()

        timestamp = datetime.now().strftime("%H:%M:%S")

        if role == "user":
            line = f"[{timestamp}] You: {content}\n"
        else:
            char_name = character or "assistant"
            line = f"[{timestamp}] {char_name}: {content}\n"

        with open(self._current_file, "a", encoding="utf-8") as f:
            f.write(line)

    def log_command(self, command: str, result: Optional[str] = None) -> None:
        """Log a command execution.

        Args:
            command: The command executed.
            result: Optional result message.
        """
        if not self._current_file:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [CMD] {command}"
        if result:
            line += f" -> {result}"
        line += "\n"

        with open(self._current_file, "a", encoding="utf-8") as f:
            f.write(line)

    def log_duo_dialogue(
        self,
        topic: str,
        history: List[Dict[str, str]],
        summary: Optional[str] = None,
    ) -> None:
        """Log a /duo dialogue session.

        Args:
            topic: The dialogue topic.
            history: List of dialogue entries.
            summary: Optional summary text.
        """
        if not self._current_file:
            self.start_session()

        timestamp = datetime.now().strftime("%H:%M:%S")

        lines = [
            f"\n[{timestamp}] === AI姉妹対話モード ===\n",
            f"お題: {topic}\n",
            "-" * 40 + "\n",
        ]

        for i, entry in enumerate(history, 1):
            speaker = entry.get("speaker", "?")
            content = entry.get("content", "")
            lines.append(f"[Turn {i}] {speaker}: {content}\n")

        lines.append("-" * 40 + "\n")

        if summary:
            lines.append(f"【まとめ】\n{summary}\n")

        lines.append("=== 対話終了 ===\n\n")

        with open(self._current_file, "a", encoding="utf-8") as f:
            f.writelines(lines)

    def end_session(self) -> Optional[str]:
        """End the current session.

        Returns:
            Path to the log file, or None if no session was active.
        """
        if not self._current_file:
            return None

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer = f"\n{'=' * 40}\nセッション終了: {timestamp}\n"

        with open(self._current_file, "a", encoding="utf-8") as f:
            f.write(footer)

        path = str(self._current_file)
        self._current_file = None
        self._session_id = None
        return path

    @property
    def current_log_path(self) -> Optional[str]:
        """Get the current log file path."""
        return str(self._current_file) if self._current_file else None
