# tests/test_rag_engine.py

import pytest
import shutil
import tempfile
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


class TestPerspectiveExtraction:
    """視点抽出機能のテスト（Phase 2A-1）"""

    def test_extract_perspective_yana(self, rag_engine):
        """TC-R-009: やなの視点ブロックを正しく抽出できる"""
        text = """## センサ統合
【客観】
- IMUは姿勢と角速度を計測する
- オプティカルフローは相対移動を検出

【やなの視点】
- まず動く最小構成で走らせてズレを可視化
- ログを残して後から詰める

【あゆの視点】
- 同期が崩れると学習も推論も破綻する
- 先に遅延計測と校正プロセスを決める"""

        result = rag_engine.extract_perspective(text, character="yana")

        assert "やなの視点" not in result  # ヘッダーは除去
        assert "まず動く最小構成" in result
        assert "ログを残して" in result
        assert "同期が崩れると" not in result  # あゆの視点は含まない

    def test_extract_perspective_ayu(self, rag_engine):
        """TC-R-010: あゆの視点ブロックを正しく抽出できる"""
        text = """## 推論レイテンシ
【客観】
- 推論の遅延は操舵遅れに直結する

【やなの視点】
- まず軽いモデルで安定させる

【あゆの視点】
- p95遅延を常に監視すべき
- 平均値だけを見ると事故要因を見落とす"""

        result = rag_engine.extract_perspective(text, character="ayu")

        assert "あゆの視点" not in result  # ヘッダーは除去
        assert "p95遅延" in result
        assert "平均値だけを見ると" in result
        assert "まず軽いモデル" not in result  # やなの視点は含まない

    def test_extract_perspective_fallback_to_objective(self, rag_engine):
        """TC-R-011: 該当する視点がない場合は客観にフォールバック"""
        text = """## 概要
【客観】
- JetRacerは自律走行車である
- センサーで周囲を認識する

【やなの視点】
- とりあえず走らせてみる"""

        # あゆの視点がないのでフォールバック
        result = rag_engine.extract_perspective(text, character="ayu")

        assert "JetRacerは自律走行車" in result
        assert "センサーで周囲を認識" in result
        assert "とりあえず走らせて" not in result

    def test_extract_perspective_no_markers(self, rag_engine):
        """TC-R-012: マーカーがない場合は元テキストをそのまま返す"""
        text = "JetRacerは自律走行車です。センサーで周囲を認識します。"

        result = rag_engine.extract_perspective(text, character="yana")

        assert result == text

    def test_search_with_character_parameter(self, rag_engine):
        """TC-R-013: character指定で視点抽出された結果を返す"""
        # 視点付きテキストを追加
        texts = [
            """【客観】
- センサーは重要です

【やなの視点】
- まず動かしてみる

【あゆの視点】
- データを分析する"""
        ]
        metadatas = [{"domain": "technical", "character": "both"}]
        rag_engine.add_knowledge(texts, metadatas)

        # やな視点で検索
        results = rag_engine.search("センサー", top_k=1, character="yana")

        assert len(results) == 1
        assert "まず動かしてみる" in results[0]["text"]
        assert "データを分析する" not in results[0]["text"]

    def test_search_without_character_returns_full_text(self, rag_engine):
        """TC-R-014: character未指定で全文を返す"""
        texts = [
            """【客観】
- センサーは重要です

【やなの視点】
- まず動かしてみる"""
        ]
        metadatas = [{"domain": "technical", "character": "both"}]
        rag_engine.add_knowledge(texts, metadatas)

        # character指定なしで検索
        results = rag_engine.search("センサー", top_k=1)

        assert len(results) == 1
        # 全文が返される（視点抽出されない）
        assert "客観" in results[0]["text"]
        assert "やなの視点" in results[0]["text"]
