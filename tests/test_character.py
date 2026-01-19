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

    def test_all_states_have_few_shot_patterns(self):
        """TC-C-008: 全状態にFew-shotパターンが存在することを確認"""
        from core import prompt_builder

        # ペルソナ読み込み
        yana_persona = prompt_builder.load_persona("./personas/yana.yaml")
        ayu_persona = prompt_builder.load_persona("./personas/ayu.yaml")

        # Few-shotパターン読み込み
        patterns = prompt_builder.load_few_shot_patterns(
            "./patterns/few_shot_patterns.yaml"
        )

        # やなの全状態にパターンがあるか確認
        for state in yana_persona.required_states:
            matching = [
                p for p in patterns
                if p.get("persona") == "yana" and p.get("state") == state
            ]
            assert len(matching) >= 1, f"やな: {state} 状態のパターンがありません"

        # あゆの全状態にパターンがあるか確認
        for state in ayu_persona.required_states:
            matching = [
                p for p in patterns
                if p.get("persona") == "ayu" and p.get("state") == state
            ]
            assert len(matching) >= 1, f"あゆ: {state} 状態のパターンがありません"

    def test_assets_passed_to_character(self, test_character):
        """TC-C-009: assetsがCharacterに渡されていることを確認"""
        # assets属性が存在する
        assert hasattr(test_character, "assets")
        assert isinstance(test_character.assets, dict)

        # few_shot_patternsがロードされている（パスが指定されていれば）
        assert hasattr(test_character, "few_shot_patterns")
        assert isinstance(test_character.few_shot_patterns, list)


class TestPerspectiveRAG:
    """視点抽出RAG統合テスト（Phase 2A-2）"""

    @pytest.fixture
    def character_with_perspective_knowledge(self):
        """視点付き知識を持つキャラクター"""
        test_path = tempfile.mkdtemp(prefix="test_perspective_")

        client = OllamaClient()
        rag = RAGEngine(client, chroma_path=test_path)

        # 視点付き知識を追加
        perspective_text = """【客観】
- センサーは周囲の障害物を検出する
- 超音波センサーの測定範囲は2cm-400cm

【やなの視点】
- センサーの数値より、まず実際に走ってみて感覚を掴むのが大事
- 細かい調整は後からでいい

【あゆの視点】
- センサー値の統計分析が重要
- 信頼区間を考慮した判断が必要"""

        rag.add_knowledge(
            [perspective_text],
            [{"domain": "technical", "character": "both"}],
        )

        char = Character("yana", "./personas/yana.yaml", client, rag)

        yield char

        try:
            shutil.rmtree(test_path)
        except Exception:
            pass

    def test_rag_search_uses_character_perspective(
        self, character_with_perspective_knowledge
    ):
        """TC-C-010: RAG検索でキャラクターの視点が抽出される"""
        char = character_with_perspective_knowledge

        # RAG検索を実行（内部でcharacter=self.nameを渡すはず）
        char.respond("センサーについて教えて", use_rag=True)

        # last_rag_resultsを確認
        assert len(char.last_rag_results) > 0

        # 結果にやなの視点が含まれ、あゆの視点は含まれないことを確認
        result_text = char.last_rag_results[0]["text"]
        assert "まず実際に走ってみて" in result_text or "感覚を掴む" in result_text
        assert "統計分析" not in result_text
        assert "信頼区間" not in result_text

    def test_ayu_character_gets_ayu_perspective(self):
        """TC-C-011: あゆキャラクターはあゆの視点を取得"""
        test_path = tempfile.mkdtemp(prefix="test_ayu_perspective_")

        client = OllamaClient()
        rag = RAGEngine(client, chroma_path=test_path)

        # 視点付き知識
        perspective_text = """【客観】
- バッテリー電圧は7.0V以上を維持する

【やなの視点】
- 動かなくなったら充電すればいい

【あゆの視点】
- 電圧監視を常時行い、閾値を設定すべき
- 予防的なメンテナンスが重要"""

        rag.add_knowledge(
            [perspective_text],
            [{"domain": "technical", "character": "both"}],
        )

        ayu_char = Character("ayu", "./personas/ayu.yaml", client, rag)

        ayu_char.respond("バッテリーについて", use_rag=True)

        assert len(ayu_char.last_rag_results) > 0
        result_text = ayu_char.last_rag_results[0]["text"]

        # あゆの視点が含まれる
        assert "電圧監視" in result_text or "予防的" in result_text
        # やなの視点は含まれない
        assert "動かなくなったら充電" not in result_text

        try:
            shutil.rmtree(test_path)
        except Exception:
            pass
