# tests/test_knowledge_perspectives.py
"""
Phase 2B: Knowledge files perspective markers tests (TDD)

Tests that knowledge files contain proper perspective markers for
character-specific RAG extraction.
"""

import pytest
import re
from pathlib import Path


# 視点マーカーのパターン
PERSPECTIVE_MARKERS = {
    "objective": r"【客観】",
    "yana": r"【やなの視点】",
    "ayu": r"【あゆの視点】",
}


class TestJetracerTechPerspectives:
    """jetracer_tech.txt の視点マーカーテスト"""

    @pytest.fixture
    def tech_content(self):
        """jetracer_tech.txt の内容を読み込み"""
        path = Path("./knowledge/jetracer_tech.txt")
        return path.read_text(encoding="utf-8")

    def test_has_objective_markers(self, tech_content):
        """TC-K-001: 客観マーカーが含まれている"""
        matches = re.findall(PERSPECTIVE_MARKERS["objective"], tech_content)
        assert len(matches) >= 3, "技術文書には少なくとも3つの客観マーカーが必要"

    def test_has_yana_perspective_markers(self, tech_content):
        """TC-K-002: やなの視点マーカーが含まれている"""
        matches = re.findall(PERSPECTIVE_MARKERS["yana"], tech_content)
        assert len(matches) >= 3, "技術文書には少なくとも3つのやな視点マーカーが必要"

    def test_has_ayu_perspective_markers(self, tech_content):
        """TC-K-003: あゆの視点マーカーが含まれている"""
        matches = re.findall(PERSPECTIVE_MARKERS["ayu"], tech_content)
        assert len(matches) >= 3, "技術文書には少なくとも3つのあゆ視点マーカーが必要"

    def test_sensor_section_has_perspectives(self, tech_content):
        """TC-K-004: センサー関連セクションに視点がある"""
        # センサーセクションを抽出
        sensor_section = re.search(
            r"### センサー類.*?(?=###|$)", tech_content, re.DOTALL
        )
        assert sensor_section, "センサーセクションが存在すること"

        section_text = sensor_section.group()
        assert "【やなの視点】" in section_text, "センサーセクションにやな視点がある"
        assert "【あゆの視点】" in section_text, "センサーセクションにあゆ視点がある"

    def test_driving_mode_has_perspectives(self, tech_content):
        """TC-K-005: 走行モードセクションに視点がある"""
        # 走行モードセクションを確認
        assert "走行モード" in tech_content
        # センサーオンリーモードまたはビジョンモードに視点があること
        mode_section = re.search(
            r"#### \d\. .*?モード.*?(?=####|##|$)", tech_content, re.DOTALL
        )
        if mode_section:
            section_text = mode_section.group()
            has_perspective = (
                "【やなの視点】" in section_text or "【あゆの視点】" in section_text
            )
            assert has_perspective, "走行モードセクションに視点マーカーがある"


class TestSistersSharedPerspectives:
    """sisters_shared.txt の視点マーカーテスト"""

    @pytest.fixture
    def shared_content(self):
        """sisters_shared.txt の内容を読み込み"""
        path = Path("./knowledge/sisters_shared.txt")
        return path.read_text(encoding="utf-8")

    def test_has_objective_markers(self, shared_content):
        """TC-K-006: 客観マーカーが含まれている"""
        matches = re.findall(PERSPECTIVE_MARKERS["objective"], shared_content)
        assert len(matches) >= 2, "共有知識には少なくとも2つの客観マーカーが必要"

    def test_has_yana_perspective_markers(self, shared_content):
        """TC-K-007: やなの視点マーカーが含まれている"""
        matches = re.findall(PERSPECTIVE_MARKERS["yana"], shared_content)
        assert len(matches) >= 2, "共有知識には少なくとも2つのやな視点マーカーが必要"

    def test_has_ayu_perspective_markers(self, shared_content):
        """TC-K-008: あゆの視点マーカーが含まれている"""
        matches = re.findall(PERSPECTIVE_MARKERS["ayu"], shared_content)
        assert len(matches) >= 2, "共有知識には少なくとも2つのあゆ視点マーカーが必要"

    def test_collaboration_section_has_perspectives(self, shared_content):
        """TC-K-009: 協力関係セクションに視点がある"""
        # 協力関係セクション全体を確認（次の##セクションまで）
        collab_section = re.search(
            r"## 姉妹の協力関係.*?(?=\n## [^#]|$)", shared_content, re.DOTALL
        )
        assert collab_section, "協力関係セクションが存在すること"

        section_text = collab_section.group()
        assert "【客観】" in section_text, "協力関係セクションに客観マーカーがある"


class TestPerspectiveQuality:
    """視点内容の品質テスト"""

    @pytest.fixture
    def tech_content(self):
        path = Path("./knowledge/jetracer_tech.txt")
        return path.read_text(encoding="utf-8")

    @pytest.fixture
    def shared_content(self):
        path = Path("./knowledge/sisters_shared.txt")
        return path.read_text(encoding="utf-8")

    def test_yana_perspective_is_action_oriented(self, tech_content):
        """TC-K-010: やなの視点は行動指向的な内容"""
        # やなの視点ブロックを抽出
        yana_blocks = re.findall(
            r"【やなの視点】\n(.*?)(?=【|##|$)", tech_content, re.DOTALL
        )

        for block in yana_blocks:
            # 行動指向的なキーワードが含まれているか
            action_keywords = ["まず", "やって", "とりあえず", "試", "動", "行"]
            has_action = any(kw in block for kw in action_keywords)
            # 空でないこと
            assert block.strip(), "やな視点ブロックが空でないこと"

    def test_ayu_perspective_is_analytical(self, tech_content):
        """TC-K-011: あゆの視点は分析的な内容"""
        # あゆの視点ブロックを抽出
        ayu_blocks = re.findall(
            r"【あゆの視点】\n(.*?)(?=【|##|$)", tech_content, re.DOTALL
        )

        for block in ayu_blocks:
            # 分析的なキーワードが含まれているか
            analytical_keywords = ["確認", "検証", "データ", "計測", "分析", "リスク", "注意"]
            # 空でないこと
            assert block.strip(), "あゆ視点ブロックが空でないこと"
