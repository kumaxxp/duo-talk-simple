# tests/test_integration.py

import pytest
import yaml
import shutil
import tempfile
from core.ollama_client import OllamaClient
from core.rag_engine import RAGEngine
from core.character import Character


@pytest.fixture
def system_setup():
    """システム全体セットアップ"""
    test_path = tempfile.mkdtemp(prefix="test_integration_")

    # 設定読み込み
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 初期化
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

    # キャラクター
    yana = Character("yana", "./personas/yana.yaml", client, rag)
    ayu = Character("ayu", "./personas/ayu.yaml", client, rag)

    yield {"yana": yana, "ayu": ayu, "config": config}

    try:
        shutil.rmtree(test_path)
    except Exception:
        pass


class TestIntegration:
    """統合テスト（TDD方式）"""

    def test_full_flow(self, system_setup):
        """TC-I-001: 全体フロー"""
        yana = system_setup["yana"]

        response = yana.respond("JetRacerって何？")
        assert len(response) > 0

    def test_character_switch(self, system_setup):
        """TC-I-002: キャラクター切替"""
        yana = system_setup["yana"]
        ayu = system_setup["ayu"]

        yana_response = yana.respond("こんにちは")
        ayu_response = ayu.respond("こんにちは")

        # 両方とも応答がある
        assert len(yana_response) > 0
        assert len(ayu_response) > 0

        # 口調が違う（手動確認推奨）
        print(f"やな: {yana_response}")
        print(f"あゆ: {ayu_response}")

    def test_multi_turn(self, system_setup):
        """TC-I-003: 複数ターン会話"""
        yana = system_setup["yana"]

        responses = []
        questions = [
            "こんにちは",
            "JetRacerって何？",
            "センサーはどうなってる？",
            "速度はどのくらい？",
            "ありがとう",
        ]

        for q in questions:
            r = yana.respond(q)
            responses.append(r)

        # 5ターン全て応答がある
        assert len(responses) == 5
        assert all(len(r) > 0 for r in responses)

    def test_rag_context(self, system_setup):
        """TC-I-004: RAG文脈参照"""
        yana = system_setup["yana"]

        # 技術的な質問
        response = yana.respond("JetRacerのセンサーについて詳しく教えて")

        # 知識ベースの情報が含まれているか
        assert any(
            keyword in response
            for keyword in ["センサー", "超音波", "IMU", "カメラ", "測定"]
        )

    def test_config_loading(self, system_setup):
        """TC-I-005: 設定読込"""
        config = system_setup["config"]

        assert "ollama" in config
        assert "rag" in config
        assert "characters" in config
