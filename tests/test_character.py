# tests/test_character.py

import pytest
import shutil
import tempfile
from core.ollama_client import OllamaClient
from core.rag_engine import RAGEngine
from core.character import Character


@pytest.fixture
def test_character():
    """テスト用Character（やな）"""
    test_path = tempfile.mkdtemp(prefix="test_char_")

    client = OllamaClient()
    rag = RAGEngine(client, chroma_path=test_path)

    # 簡易知識
    rag.add_knowledge(
        ["JetRacerは自律走行車です"],
        [{"domain": "technical", "character": "both"}],
    )

    char = Character("yana", "./personas/yana.yaml", client, rag)

    yield char

    try:
        shutil.rmtree(test_path)
    except Exception:
        pass


class TestCharacter:
    """Character ユニットテスト（TDD方式）"""

    def test_init(self, test_character):
        """TC-C-001: 初期化テスト"""
        assert test_character.name == "yana"
        assert test_character.config is not None
        assert "system_prompt" in test_character.config
        assert len(test_character.history) == 0

    def test_respond_basic(self, test_character):
        """TC-C-002: 基本応答"""
        response = test_character.respond("こんにちは", use_rag=False)

        assert isinstance(response, str)
        assert len(response) > 0

    def test_respond_with_rag(self, test_character):
        """TC-C-003: RAG統合"""
        response = test_character.respond("JetRacerって何？", use_rag=True)

        assert len(response) > 0
        # JetRacerに言及しているか
        assert any(
            keyword in response for keyword in ["JetRacer", "自律", "走行", "車"]
        )

    def test_history_management(self, test_character):
        """TC-C-004: 履歴管理"""
        test_character.respond("こんにちは")
        assert len(test_character.history) == 2  # user + assistant

        test_character.respond("元気？")
        assert len(test_character.history) == 4

    def test_clear_history(self, test_character):
        """TC-C-005: 履歴クリア"""
        test_character.respond("こんにちは")
        test_character.respond("元気？")
        assert len(test_character.history) == 4

        test_character.clear_history()
        assert len(test_character.history) == 0

    def test_query_rewrite(self, test_character):
        """TC-C-006: クエリ書き換え"""
        # 最初の質問
        test_character.respond("JetRacerって何？", use_rag=False)

        # 代名詞を使った質問
        vague_query = "それって速いの？"
        rewritten = test_character._rewrite_query(vague_query)

        # 「JetRacer」が含まれるか
        assert any(keyword in rewritten for keyword in ["JetRacer", "自律", "走行"])

    def test_max_history_limit(self, test_character):
        """TC-C-007: 履歴上限テスト"""
        # 15ターン会話（30メッセージ）
        for i in range(15):
            test_character.respond(f"質問{i}")

        # 最大10ターン（20メッセージ）に制限
        assert len(test_character.history) == 20
