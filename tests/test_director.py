"""Tests for Director quality evaluation system."""

import pytest

from core.director import Director
from core.types import DirectorEvaluation, DirectorStatus


class TestDirectorStatus:
    """Tests for DirectorStatus enum."""

    def test_status_values(self):
        """DirectorStatus has PASS, WARN, RETRY values."""
        assert DirectorStatus.PASS.value == "PASS"
        assert DirectorStatus.WARN.value == "WARN"
        assert DirectorStatus.RETRY.value == "RETRY"


class TestDirectorEvaluation:
    """Tests for DirectorEvaluation dataclass."""

    def test_default_values(self):
        """DirectorEvaluation has sensible defaults."""
        eval_result = DirectorEvaluation(status=DirectorStatus.PASS)
        assert eval_result.status == DirectorStatus.PASS
        assert eval_result.checks == {}
        assert eval_result.suggestion == ""
        assert eval_result.scores == {}
        assert eval_result.avg_score == 0.0

    def test_is_acceptable_pass(self):
        """PASS status is acceptable."""
        eval_result = DirectorEvaluation(status=DirectorStatus.PASS)
        assert eval_result.is_acceptable() is True

    def test_is_acceptable_warn(self):
        """WARN status is acceptable."""
        eval_result = DirectorEvaluation(status=DirectorStatus.WARN)
        assert eval_result.is_acceptable() is True

    def test_is_acceptable_retry(self):
        """RETRY status is not acceptable."""
        eval_result = DirectorEvaluation(status=DirectorStatus.RETRY)
        assert eval_result.is_acceptable() is False


class TestDirectorInit:
    """Tests for Director initialization."""

    def test_default_init(self):
        """Director initializes with defaults."""
        director = Director()
        assert director.enable_static_checks is True
        assert director.enable_llm_scoring is False

    def test_init_with_rules_path(self):
        """Director can load rules from file."""
        director = Director(rules_path="director/director_rules.yaml")
        assert director._rules is not None
        assert "hard_rules" in director._rules

    def test_init_with_nonexistent_path(self):
        """Director handles nonexistent rules path gracefully."""
        director = Director(rules_path="nonexistent.yaml")
        assert director._rules == {}


class TestDirectorFormatCheck:
    """Tests for format checking (line count, sentence count)."""

    @pytest.fixture
    def director(self):
        """Create Director with rules."""
        return Director(rules_path="director/director_rules.yaml")

    def test_format_pass_short_response(self, director):
        """Short response passes format check."""
        response = "えー、ほんとに？やってみよ！"  # Has yana markers
        result = director.evaluate_response("yana", response)
        assert result.checks["format"]["status"] == "PASS"
        # Overall status may be affected by other checks
        assert result.checks["format"]["line_count"] == 1
        assert result.checks["format"]["sentence_count"] == 2

    def test_format_warn_6_lines(self, director):
        """6 lines triggers WARN (but may be overridden by sentence count)."""
        # Use short fragments to avoid sentence count RETRY
        response = "あ\nい\nう\nえ\nお\nか"  # 6 lines, no sentence endings
        result = director.evaluate_response("yana", response)
        # With no sentence endings, only 1 sentence is counted
        assert result.checks["format"]["line_count"] == 6

    def test_format_retry_8_lines(self, director):
        """8 lines triggers RETRY."""
        lines = "\n".join([f"{i}行目。" for i in range(1, 9)])
        result = director.evaluate_response("yana", lines)
        assert result.checks["format"]["status"] == "RETRY"
        assert result.status == DirectorStatus.RETRY

    def test_format_retry_4_sentences(self, director):
        """4 or more sentences triggers RETRY."""
        response = "一文目です。二文目です。三文目です。四文目です。"
        result = director.evaluate_response("ayu", response)
        assert result.checks["format"]["status"] == "RETRY"
        assert result.checks["format"]["sentence_count"] == 4


class TestDirectorPraiseWordsCheck:
    """Tests for praise word checking (ayu only)."""

    @pytest.fixture
    def director(self):
        """Create Director with rules."""
        return Director(rules_path="director/director_rules.yaml")

    def test_praise_words_not_checked_for_yana(self, director):
        """Praise words are not checked for yana."""
        response = "さすがあゆ！"
        result = director.evaluate_response("yana", response)
        assert "praise_words" not in result.checks

    def test_praise_words_pass_no_praise(self, director):
        """Response without praise words passes."""
        response = "そうですね。やってみましょう。"
        result = director.evaluate_response("ayu", response)
        assert result.checks["praise_words"]["status"] == "PASS"

    def test_praise_words_warn_single_praise(self, director):
        """Single praise word without target triggers WARN."""
        response = "すごいことになりましたね。"
        result = director.evaluate_response("ayu", response)
        assert result.checks["praise_words"]["status"] == "WARN"
        assert "すごい" in result.checks["praise_words"]["found"]

    def test_praise_words_retry_with_affirmation(self, director):
        """Praise word + affirmation toward other triggers RETRY."""
        response = "姉様、さすがですね。"
        result = director.evaluate_response("ayu", response)
        assert result.checks["praise_words"]["status"] == "RETRY"
        assert result.status == DirectorStatus.RETRY

    def test_praise_words_in_quotes_ignored(self, director):
        """Praise words in quotes are ignored."""
        response = "「さすが」と言われましたけど、運ですよ。"
        result = director.evaluate_response("ayu", response)
        # The quote should be excluded from pattern matching
        assert result.checks["praise_words"]["status"] == "PASS"


class TestDirectorSettingConsistency:
    """Tests for setting consistency (sisters live together)."""

    @pytest.fixture
    def director(self):
        """Create Director with rules."""
        return Director(rules_path="director/director_rules.yaml")

    def test_setting_pass_normal(self, director):
        """Normal response passes setting check."""
        response = "うん、一緒にやろう！"
        result = director.evaluate_response("yana", response)
        assert result.checks["setting_consistency"]["status"] == "PASS"

    def test_setting_retry_separate_house(self, director):
        """Suggesting separate houses triggers RETRY."""
        response = "姉様のお家に遊びに行きます。"
        result = director.evaluate_response("ayu", response)
        assert result.checks["setting_consistency"]["status"] == "RETRY"
        assert "姉様のお家" in result.checks["setting_consistency"]["found"]

    def test_setting_retry_come_again(self, director):
        """'Come again' suggests separate living - RETRY."""
        response = "また遊びに来てね！"
        result = director.evaluate_response("yana", response)
        assert result.checks["setting_consistency"]["status"] == "RETRY"

    def test_setting_retry_family_home(self, director):
        """'At family home' suggests separate living - RETRY."""
        response = "実家では違うやり方でした。"
        result = director.evaluate_response("ayu", response)
        assert result.checks["setting_consistency"]["status"] == "RETRY"


class TestDirectorAIIsms:
    """Tests for AI-ism detection."""

    @pytest.fixture
    def director(self):
        """Create Director with rules."""
        return Director(rules_path="director/director_rules.yaml")

    def test_ai_ism_pass_normal(self, director):
        """Normal response passes AI-ism check."""
        response = "わかった。やってみる！"
        result = director.evaluate_response("yana", response)
        assert result.checks["ai_isms"]["status"] == "PASS"

    def test_ai_ism_retry_acknowledged(self, director):
        """'承知しました' triggers RETRY."""
        response = "承知しました。"
        result = director.evaluate_response("ayu", response)
        assert result.checks["ai_isms"]["status"] == "RETRY"
        assert "承知しました" in result.checks["ai_isms"]["found"]

    def test_ai_ism_retry_helper_offer(self, director):
        """Helper offer phrases trigger RETRY."""
        response = "何かお手伝いしましょうか？"
        result = director.evaluate_response("ayu", response)
        assert result.checks["ai_isms"]["status"] == "RETRY"

    def test_ai_ism_retry_stage_direction(self, director):
        """Stage direction words trigger RETRY."""
        response = "ドキドキしながら見守りました。"
        result = director.evaluate_response("yana", response)
        assert result.checks["ai_isms"]["status"] == "RETRY"
        assert "ドキドキ" in result.checks["ai_isms"]["found"]


class TestDirectorToneMarkers:
    """Tests for tone marker checking."""

    @pytest.fixture
    def director(self):
        """Create Director with rules."""
        return Director(rules_path="director/director_rules.yaml")

    def test_tone_yana_pass_full_markers(self, director):
        """yana response with all markers passes."""
        response = "えー、ほんとに？やってみよっかな！"
        result = director.evaluate_response("yana", response)
        assert result.checks["tone_markers"]["status"] == "PASS"
        assert result.checks["tone_markers"]["score"] >= 2

    def test_tone_yana_warn_weak_markers(self, director):
        """yana response with weak markers gets WARN."""
        response = "そうですね。考えてみます。"
        result = director.evaluate_response("yana", response)
        # This response is too polite for yana
        assert result.checks["tone_markers"]["score"] <= 1

    def test_tone_yana_retry_no_markers(self, director):
        """yana response with no markers triggers RETRY."""
        response = "検討します。"
        result = director.evaluate_response("yana", response)
        assert result.checks["tone_markers"]["status"] == "RETRY"
        assert result.checks["tone_markers"]["score"] == 0

    def test_tone_ayu_pass_polite(self, director):
        """ayu response with polite markers passes."""
        response = "つまり、そういうことですね。確認しました。"
        result = director.evaluate_response("ayu", response)
        assert result.checks["tone_markers"]["status"] == "PASS"
        assert result.checks["tone_markers"]["score"] >= 2

    def test_tone_ayu_warn_casual(self, director):
        """ayu response that's too casual gets WARN."""
        response = "うん、わかった。"
        result = director.evaluate_response("ayu", response)
        # Too casual for ayu
        assert result.checks["tone_markers"]["score"] <= 1

    def test_tone_ayu_retry_no_polite(self, director):
        """ayu response without politeness triggers RETRY."""
        response = "やる。"
        result = director.evaluate_response("ayu", response)
        assert result.checks["tone_markers"]["status"] == "RETRY"


class TestDirectorIntegration:
    """Integration tests for Director evaluation."""

    @pytest.fixture
    def director(self):
        """Create Director with rules."""
        return Director(rules_path="director/director_rules.yaml")

    def test_good_yana_response(self, director):
        """Good yana response passes all checks."""
        response = "おっ、面白そうじゃん！やってみよっか？"
        result = director.evaluate_response("yana", response)
        assert result.status == DirectorStatus.PASS

    def test_good_ayu_response(self, director):
        """Good ayu response passes all checks."""
        # Response with ayu markers: polite endings x2 + vocab "つまり"
        response = "つまり、そういうことですね。了解です。"
        result = director.evaluate_response("ayu", response)
        assert result.status == DirectorStatus.PASS

    def test_multiple_issues_worst_status_wins(self, director):
        """Response with multiple issues returns worst status."""
        # AI-ism + too long
        response = "承知しました。\n" * 10
        result = director.evaluate_response("ayu", response)
        assert result.status == DirectorStatus.RETRY
        # Should have multiple check failures
        assert len(result.suggestion) > 0

    def test_suggestion_contains_reasons(self, director):
        """Suggestion includes reasons for failure."""
        response = "姉様のお家で承知しました。"
        result = director.evaluate_response("ayu", response)
        assert result.status == DirectorStatus.RETRY
        assert "設定破壊" in result.suggestion or "AI臭い" in result.suggestion


class TestDirectorDisabledChecks:
    """Tests for Director with checks disabled."""

    def test_static_checks_disabled(self):
        """Director can disable static checks."""
        director = Director(enable_static_checks=False)
        response = "承知しました。" * 10  # Would normally fail
        result = director.evaluate_response("ayu", response)
        assert result.status == DirectorStatus.PASS
        assert result.checks == {}


class TestDirectorTextNormalization:
    """Tests for text normalization."""

    @pytest.fixture
    def director(self):
        """Create Director."""
        return Director()

    def test_normalize_consecutive_punctuation(self, director):
        """Consecutive punctuation is normalized."""
        text = "えっ！！！本当！？？？"
        normalized = director._normalize_text(text)
        assert "！！" not in normalized
        assert "？？" not in normalized

    def test_normalize_fullwidth_punctuation(self, director):
        """Full-width punctuation is normalized."""
        text = "テスト｡テスト､テスト"
        normalized = director._normalize_text(text)
        assert "。" in normalized
        assert "、" in normalized

    def test_normalize_whitespace(self, director):
        """Consecutive whitespace is normalized."""
        text = "テスト   テスト"
        normalized = director._normalize_text(text)
        assert "  " not in normalized


class TestDirectorLLMScoring:
    """Tests for LLM-based scoring."""

    def test_llm_scoring_disabled_by_default(self):
        """LLM scoring is disabled by default."""
        director = Director()
        assert director.enable_llm_scoring is False

    def test_llm_scoring_no_client(self):
        """LLM scoring skipped when no client provided."""
        director = Director(enable_llm_scoring=True)
        result = director._score_with_llm("yana", "テスト", None)
        assert result["status"] == "SKIP"

    def test_llm_scoring_with_mock_client(self, mocker):
        """LLM scoring works with mock client."""
        # Create mock client
        mock_client = mocker.Mock()
        mock_client.generate.return_value = (
            '{"frame_consistency": 4, "roleplay": 4, "connection": 4, '
            '"information_density": 4, "naturalness": 4}'
        )

        director = Director(
            rules_path="director/director_rules.yaml",
            enable_llm_scoring=True,
            llm_client=mock_client,
        )

        result = director._score_with_llm("yana", "やってみよ！", None)

        assert result["status"] == "PASS"
        assert result["avg_score"] == 4.0
        assert len(result["scores"]) == 5

    def test_llm_scoring_low_score_retry(self, mocker):
        """Low LLM scores trigger RETRY."""
        mock_client = mocker.Mock()
        mock_client.generate.return_value = (
            '{"frame_consistency": 2, "roleplay": 2, "connection": 2, '
            '"information_density": 2, "naturalness": 2}'
        )

        director = Director(
            rules_path="director/director_rules.yaml",
            enable_llm_scoring=True,
            llm_client=mock_client,
        )

        result = director._score_with_llm("ayu", "テスト", None)

        assert result["status"] == "RETRY"
        assert result["avg_score"] == 2.0

    def test_llm_scoring_medium_score_warn(self, mocker):
        """Medium LLM scores trigger WARN."""
        mock_client = mocker.Mock()
        mock_client.generate.return_value = (
            '{"frame_consistency": 3.7, "roleplay": 3.7, "connection": 3.7, '
            '"information_density": 3.7, "naturalness": 3.7}'
        )

        director = Director(
            rules_path="director/director_rules.yaml",
            enable_llm_scoring=True,
            llm_client=mock_client,
        )

        result = director._score_with_llm("yana", "テスト", None)

        assert result["status"] == "WARN"

    def test_parse_scoring_response_valid_json(self):
        """Valid JSON is parsed correctly."""
        director = Director()
        response = '{"frame_consistency": 4, "roleplay": 5, "connection": 3, "information_density": 4, "naturalness": 4}'
        scores = director._parse_scoring_response(response)

        assert scores["frame_consistency"] == 4.0
        assert scores["roleplay"] == 5.0
        assert scores["connection"] == 3.0

    def test_parse_scoring_response_embedded_json(self):
        """JSON embedded in text is extracted."""
        director = Director()
        response = 'Here is my evaluation: {"frame_consistency": 4, "roleplay": 4, "connection": 4, "information_density": 4, "naturalness": 4}'
        scores = director._parse_scoring_response(response)

        assert len(scores) == 5
        assert all(v == 4.0 for v in scores.values())

    def test_parse_scoring_response_invalid_json(self):
        """Invalid JSON returns empty dict."""
        director = Director()
        response = "This is not JSON"
        scores = director._parse_scoring_response(response)

        assert scores == {}

    def test_parse_scoring_response_incomplete_scores(self):
        """Incomplete scores return empty dict."""
        director = Director()
        response = '{"frame_consistency": 4, "roleplay": 4}'  # Missing 3 scores
        scores = director._parse_scoring_response(response)

        assert scores == {}

    def test_parse_scoring_response_clamps_values(self):
        """Out-of-range values are clamped."""
        director = Director()
        response = '{"frame_consistency": 10, "roleplay": 0, "connection": 4, "information_density": 4, "naturalness": 4}'
        scores = director._parse_scoring_response(response)

        assert scores["frame_consistency"] == 5.0  # Clamped from 10
        assert scores["roleplay"] == 1.0  # Clamped from 0

    def test_build_scoring_prompt_includes_response(self):
        """Scoring prompt includes response text."""
        director = Director()
        prompt = director._build_scoring_prompt("yana", "テスト発言", None)

        assert "テスト発言" in prompt
        assert "やな" in prompt

    def test_build_scoring_prompt_includes_history(self):
        """Scoring prompt includes conversation history."""
        director = Director()
        history = [
            {"role": "yana", "content": "前の発言"},
            {"role": "ayu", "content": "返事"},
        ]
        prompt = director._build_scoring_prompt("yana", "テスト", history)

        assert "前の発言" in prompt
        assert "返事" in prompt

    def test_evaluate_with_llm_scoring_enabled(self, mocker):
        """evaluate_response uses LLM scoring when enabled."""
        mock_client = mocker.Mock()
        mock_client.generate.return_value = (
            '{"frame_consistency": 4, "roleplay": 4, "connection": 4, '
            '"information_density": 4, "naturalness": 4}'
        )

        director = Director(
            rules_path="director/director_rules.yaml",
            enable_llm_scoring=True,
            llm_client=mock_client,
        )

        # Response that passes static checks
        response = "えー、ほんとに？やってみよ！"
        result = director.evaluate_response("yana", response)

        assert "llm_scoring" in result.checks
        assert result.scores != {}
        assert result.avg_score > 0

    def test_evaluate_skips_llm_if_static_fails(self, mocker):
        """LLM scoring skipped if static checks fail."""
        mock_client = mocker.Mock()

        director = Director(
            rules_path="director/director_rules.yaml",
            enable_llm_scoring=True,
            llm_client=mock_client,
        )

        # Response that fails static checks (AI-ism)
        response = "承知しました。"
        result = director.evaluate_response("ayu", response)

        # LLM should not be called because static check failed
        mock_client.generate.assert_not_called()
        assert "llm_scoring" not in result.checks
