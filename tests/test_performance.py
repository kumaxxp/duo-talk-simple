# tests/test_performance.py

import pytest
import time
import yaml
import tempfile
import shutil
from core.ollama_client import OllamaClient
from core.rag_engine import RAGEngine
from core.character import Character


@pytest.fixture
def perf_setup():
    """パフォーマンステスト用セットアップ"""
    test_path = tempfile.mkdtemp(prefix="test_perf_")

    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    client = OllamaClient(
        base_url=config["ollama"]["base_url"],
        model=config["ollama"]["llm_model"],
    )

    rag = RAGEngine(
        ollama_client=client,
        chroma_path=test_path,
    )

    # 知識投入
    metadata_mapping = {
        item["file"]: item["metadata"] for item in config["knowledge"]["sources"]
    }
    rag.init_from_files(
        config["knowledge"]["source_dir"],
        metadata_mapping,
    )

    char = Character("yana", "./personas/yana.yaml", client, rag)

    yield {"client": client, "rag": rag, "character": char, "config": config}

    try:
        shutil.rmtree(test_path)
    except Exception:
        pass


class TestPerformance:
    """パフォーマンステスト"""

    def test_response_time_basic(self, perf_setup):
        """TC-P-001: 基本応答時間（30秒以内 - Cydonia 22B用）"""
        char = perf_setup["character"]

        start = time.time()
        response = char.respond("こんにちは", use_rag=False)
        elapsed = time.time() - start

        assert len(response) > 0
        assert elapsed < 30.0, f"応答時間が30秒を超えました: {elapsed:.2f}秒"
        print(f"\n基本応答時間: {elapsed:.2f}秒")

    def test_response_time_with_rag(self, perf_setup):
        """TC-P-002: RAG応答時間（120秒以内 - Cydonia 22B用）"""
        char = perf_setup["character"]

        start = time.time()
        response = char.respond("JetRacerのセンサーについて教えて", use_rag=True)
        elapsed = time.time() - start

        assert len(response) > 0
        assert elapsed < 120.0, f"RAG応答時間が120秒を超えました: {elapsed:.2f}秒"
        print(f"\nRAG応答時間: {elapsed:.2f}秒")

    def test_embedding_time(self, perf_setup):
        """TC-P-003: 埋め込み生成時間（1秒以内）"""
        client = perf_setup["client"]

        start = time.time()
        embedding = client.embed("JetRacerは自律走行車です")
        elapsed = time.time() - start

        assert len(embedding) > 0
        assert elapsed < 1.0, f"埋め込み生成が1秒を超えました: {elapsed:.2f}秒"
        print(f"\n埋め込み生成時間: {elapsed:.2f}秒")

    def test_search_time(self, perf_setup):
        """TC-P-004: RAG検索時間（1秒以内）"""
        rag = perf_setup["rag"]

        start = time.time()
        results = rag.search("センサー", top_k=3)
        elapsed = time.time() - start

        assert len(results) > 0
        assert elapsed < 1.0, f"検索時間が1秒を超えました: {elapsed:.2f}秒"
        print(f"\nRAG検索時間: {elapsed:.2f}秒")

    def test_multi_turn_stability(self, perf_setup):
        """TC-P-005: 複数ターン安定性"""
        char = perf_setup["character"]
        questions = [
            "こんにちは",
            "JetRacerって何？",
            "センサーはどう？",
        ]

        response_times = []

        for q in questions:
            start = time.time()
            response = char.respond(q)
            elapsed = time.time() - start
            response_times.append(elapsed)
            assert len(response) > 0

        # 応答時間が極端に増加しないことを確認
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)

        assert max_time < avg_time * 3, "応答時間に大きなばらつきがあります"
        print(f"\n平均応答時間: {avg_time:.2f}秒, 最大: {max_time:.2f}秒")
