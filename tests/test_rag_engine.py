# tests/test_rag_engine.py

import pytest
import shutil
import tempfile
import uuid
from core.ollama_client import OllamaClient
from core.rag_engine import RAGEngine


@pytest.fixture
def rag_engine():
    """テスト用RAGEngine（各テストで独立）"""
    # 一意な一時ディレクトリを使用
    test_chroma_path = tempfile.mkdtemp(prefix="test_chroma_")

    client = OllamaClient()
    rag = RAGEngine(client, chroma_path=test_chroma_path)

    yield rag

    # テスト後クリーンアップ
    try:
        shutil.rmtree(test_chroma_path)
    except Exception:
        pass  # クリーンアップ失敗は無視


class TestRAGEngine:
    """RAGEngine ユニットテスト（TDD方式）"""

    def test_init(self, rag_engine):
        """TC-R-001: ChromaDB初期化"""
        assert rag_engine.collection is not None
        assert rag_engine.collection.count() == 0

    def test_add_knowledge(self, rag_engine):
        """TC-R-002: 知識追加"""
        texts = ["JetRacerは自律走行車です", "センサーで周囲を認識します"]
        metadatas = [
            {"domain": "technical", "character": "both"},
            {"domain": "technical", "character": "both"},
        ]

        rag_engine.add_knowledge(texts, metadatas)
        assert rag_engine.collection.count() == 2

    def test_search_basic(self, rag_engine):
        """TC-R-003: 基本検索"""
        # 知識追加
        texts = ["JetRacerは自律走行車です", "モーター制御はPWM信号です"]
        metadatas = [{"domain": "technical", "character": "both"}] * 2
        rag_engine.add_knowledge(texts, metadatas)

        # 検索
        results = rag_engine.search("JetRacerとは", top_k=1)

        assert len(results) == 1
        assert "JetRacer" in results[0]["text"]
        assert "score" in results[0]
        assert results[0]["score"] > 0.5

    def test_search_with_filter(self, rag_engine):
        """TC-R-004: フィルタ検索"""
        # 異なるメタデータで追加
        texts = ["やなは直感的", "あゆは分析的"]
        metadatas = [
            {"domain": "character", "character": "yana"},
            {"domain": "character", "character": "ayu"},
        ]
        rag_engine.add_knowledge(texts, metadatas)

        # やな限定で検索
        results = rag_engine.search(
            "性格",
            top_k=10,
            filters={"character": "yana"},
        )

        assert len(results) == 1
        assert "やな" in results[0]["text"]

    def test_search_accuracy(self, rag_engine):
        """TC-R-005: 検索精度"""
        # 明確に異なる知識を追加
        texts = [
            "JetRacerは自律走行車です",
            "猫は可愛い動物です",
            "太陽は恒星です",
        ]
        metadatas = [{"domain": "technical", "character": "both"}] * 3
        rag_engine.add_knowledge(texts, metadatas)

        # JetRacerに関する検索
        results = rag_engine.search("自律走行車について", top_k=1)

        # 最も関連度が高いのはJetRacerの知識
        assert "JetRacer" in results[0]["text"]
        assert results[0]["score"] > 0.7

    def test_chunk_text(self, rag_engine):
        """TC-R-006: テキスト分割"""
        long_text = "A" * 2500  # 2500文字
        chunks = rag_engine._chunk_text(long_text, max_chars=1000)

        assert len(chunks) == 3  # 1000 + 1000 + 500
        assert all(len(chunk) <= 1000 for chunk in chunks)

    def test_init_from_files(self, rag_engine):
        """TC-R-007: ファイルからの初期化"""
        metadata_mapping = {
            "jetracer_tech.txt": {
                "domain": "technical",
                "character": "both",
            }
        }

        rag_engine.init_from_files("./knowledge", metadata_mapping)
        assert rag_engine.collection.count() > 0

    def test_empty_search(self, rag_engine):
        """TC-R-008: 空のデータベースで検索"""
        results = rag_engine.search("何か", top_k=3)
        assert len(results) == 0
