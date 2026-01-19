"""Director for evaluating AI-generated response quality.

Performs static checks and LLM-based scoring to determine if responses
meet quality standards for the duo-talk system.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from core.types import DirectorEvaluation, DirectorStatus

if TYPE_CHECKING:
    from typing import Any

    from core.ollama_client import OllamaClient


class Director:
    """Evaluates AI character responses for quality and consistency."""

    # Praise words that ayu should not use (from world_rules.yaml)
    PRAISE_WORDS_FOR_AYU: list[str] = [
        "いい観点",
        "いい質問",
        "さすが",
        "鋭い",
        "おっしゃる通り",
        "その通り",
        "素晴らしい",
        "お見事",
        "よく気づ",
        "正解です",
        "大正解",
        "正解",
        "すごい",
        "完璧",
        "天才",
    ]

    # Expressions that suggest sisters live separately (forbidden)
    SEPARATION_WORDS: list[str] = [
        "姉様のお家",
        "姉様の家",
        "姉様の実家",
        "あゆのお家",
        "あゆの家",
        "やなのお家",
        "やなの家",
        "また来てね",
        "また遊びに来て",
        "お邪魔しました",
        "実家では",
        "実家に",
        "実家の",
    ]

    # AI-ism expressions (too robotic)
    AI_ISM_PATTERNS: list[str] = [
        "承知しました",
        "かしこまりました",
        "了解しました",
        "お手伝いできることはありますか",
        "何かお手伝いしましょうか",
        "ご質問があれば",
    ]

    # Stage direction expressions (should not describe emotions directly)
    STAGE_DIRECTIONS: list[str] = [
        "焦燥感",
        "期待",
        "ドキドキ",
        "ワクワク",
        "口調で",
        "トーンで",
        "興奮",
        "悲しげ",
        "嬉しそうに",
        "寂しそうに",
    ]

    # Tone markers for each character
    TONE_MARKERS: dict[str, dict[str, Any]] = {
        "yana": {
            "endings": ["わ！", "へ？", "よね", "かな", "かも", "だね", "じゃん"],
            "vocab": ["やだ", "ほんと", "えー", "うーん", "すっごい", "そっか", "ね。"],
            "style_check": "short_with_exclamation",
        },
        "ayu": {
            "endings": ["でしょう", "ですね", "ました", "ません", "ですよ", "です。"],
            "vocab": ["つまり", "要するに", "一般的に", "目安", "推奨"],
            "style_check": "polite_multiple",
        },
    }

    # LLM Scoring criteria (5 axes)
    SCORING_CRITERIA: dict[str, str] = {
        "frame_consistency": "その場の状況（景色や場所）に合った内容か",
        "roleplay": "姉妹の関係性・性格が守られているか",
        "connection": "直前の相手の発言を無視していないか",
        "information_density": "内容が薄すぎない/詰め込みすぎていないか",
        "naturalness": "機械的な繰り返しや唐突な表現がないか",
    }

    # Scoring thresholds
    DEFAULT_RETRY_THRESHOLD: float = 3.5
    DEFAULT_WARN_THRESHOLD: float = 4.0

    def __init__(
        self,
        rules_path: str | Path | None = None,
        enable_static_checks: bool = True,
        enable_llm_scoring: bool = False,
        llm_client: "OllamaClient | None" = None,
    ) -> None:
        """Initialize Director with configuration.

        Args:
            rules_path: Path to director_rules.yaml
            enable_static_checks: Enable hard rule checking
            enable_llm_scoring: Enable LLM-based quality scoring
            llm_client: OllamaClient for LLM scoring (required if enable_llm_scoring)
        """
        self.enable_static_checks = enable_static_checks
        self.enable_llm_scoring = enable_llm_scoring
        self._llm_client = llm_client
        self._rules: dict[str, Any] = {}
        self._logger = logging.getLogger(__name__)

        if rules_path:
            self._load_rules(rules_path)

    def _load_rules(self, rules_path: str | Path) -> None:
        """Load rules from YAML file."""
        path = Path(rules_path)
        if path.exists():
            self._rules = yaml.safe_load(path.read_text(encoding="utf-8"))

    def evaluate_response(
        self,
        speaker: str,
        response: str,
        history: list[dict[str, str]] | None = None,
        turn: int = 0,
    ) -> DirectorEvaluation:
        """Evaluate a response for quality.

        Args:
            speaker: Character ID ('yana' or 'ayu')
            response: The generated response text
            history: Conversation history
            turn: Current turn number

        Returns:
            DirectorEvaluation with status and details
        """
        checks: dict[str, Any] = {}
        status = DirectorStatus.PASS
        suggestions: list[str] = []

        if self.enable_static_checks:
            # Normalize text for checking
            normalized = self._normalize_text(response)

            # Run static checks (use original text for line count)
            format_result = self._check_format(response)
            checks["format"] = format_result
            if format_result["status"] == "RETRY":
                status = DirectorStatus.RETRY
                suggestions.append(format_result.get("reason", ""))
            elif format_result["status"] == "WARN" and status == DirectorStatus.PASS:
                status = DirectorStatus.WARN

            # Check praise words (ayu only)
            if speaker == "ayu":
                praise_result = self._check_praise_words(normalized)
                checks["praise_words"] = praise_result
                if praise_result["status"] == "RETRY":
                    status = DirectorStatus.RETRY
                    suggestions.append(praise_result.get("reason", ""))
                elif praise_result["status"] == "WARN" and status == DirectorStatus.PASS:
                    status = DirectorStatus.WARN

            # Check setting consistency
            setting_result = self._check_setting_consistency(normalized)
            checks["setting_consistency"] = setting_result
            if setting_result["status"] == "RETRY":
                status = DirectorStatus.RETRY
                suggestions.append(setting_result.get("reason", ""))

            # Check AI-isms
            ai_ism_result = self._check_ai_isms(normalized)
            checks["ai_isms"] = ai_ism_result
            if ai_ism_result["status"] == "RETRY":
                status = DirectorStatus.RETRY
                suggestions.append(ai_ism_result.get("reason", ""))

            # Check tone markers
            tone_result = self._check_tone_markers(speaker, normalized)
            checks["tone_markers"] = tone_result
            if tone_result["status"] == "RETRY":
                status = DirectorStatus.RETRY
                suggestions.append(tone_result.get("reason", ""))
            elif tone_result["status"] == "WARN" and status == DirectorStatus.PASS:
                status = DirectorStatus.WARN

        # LLM scoring (only if static checks passed and LLM scoring enabled)
        scores: dict[str, float] = {}
        avg_score = 0.0

        if self.enable_llm_scoring and status != DirectorStatus.RETRY:
            llm_result = self._score_with_llm(speaker, response, history)
            checks["llm_scoring"] = llm_result

            if llm_result["status"] == "RETRY":
                status = DirectorStatus.RETRY
                suggestions.append(llm_result.get("reason", ""))
            elif llm_result["status"] == "WARN" and status == DirectorStatus.PASS:
                status = DirectorStatus.WARN
                suggestions.append(llm_result.get("reason", ""))

            scores = llm_result.get("scores", {})
            avg_score = llm_result.get("avg_score", 0.0)

        suggestion = " ".join(filter(None, suggestions))
        return DirectorEvaluation(
            status=status,
            checks=checks,
            suggestion=suggestion,
            scores=scores,
            avg_score=avg_score,
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for checking.

        - Exclude quoted text (「」) from certain checks
        - Normalize consecutive punctuation
        - Normalize whitespace
        """
        # Remove text in quotes for certain patterns (but keep for line count)
        normalized = text

        # Normalize consecutive punctuation
        normalized = re.sub(r"！+", "！", normalized)
        normalized = re.sub(r"？+", "？", normalized)
        normalized = re.sub(r"。+", "。", normalized)

        # Normalize full-width punctuation
        normalized = normalized.replace("｡", "。")
        normalized = normalized.replace("､", "、")

        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def _extract_non_quoted_text(self, text: str) -> str:
        """Extract text outside of quotes for pattern matching."""
        # Remove text within 「」
        return re.sub(r"「[^」]*」", "", text)

    def _check_format(self, text: str) -> dict[str, Any]:
        """Check output format constraints.

        Hard rules from director_rules.yaml:
        - 8+ lines → RETRY
        - 6-7 lines → WARN
        - 4+ sentences → RETRY
        """
        rules = self._rules.get("hard_rules", {}).get("format", {})
        max_lines = rules.get("max_lines", 8)
        warn_lines = rules.get("warn_lines", 6)
        max_sentences = rules.get("max_sentences", 4)

        # Count lines
        lines = [line for line in text.split("\n") if line.strip()]
        line_count = len(lines)

        # Count sentences
        sentence_endings = re.findall(r"[。！？]", text)
        sentence_count = len(sentence_endings) if sentence_endings else 1

        if line_count >= max_lines:
            return {
                "status": "RETRY",
                "reason": f"行数が多すぎます（{line_count}行）。{max_lines}行未満にしてください。",
                "line_count": line_count,
                "sentence_count": sentence_count,
            }

        if sentence_count >= max_sentences:
            return {
                "status": "RETRY",
                "reason": f"文が多すぎます（{sentence_count}文）。{max_sentences}文未満にしてください。",
                "line_count": line_count,
                "sentence_count": sentence_count,
            }

        if line_count >= warn_lines:
            return {
                "status": "WARN",
                "reason": f"行数がやや多いです（{line_count}行）。",
                "line_count": line_count,
                "sentence_count": sentence_count,
            }

        return {
            "status": "PASS",
            "line_count": line_count,
            "sentence_count": sentence_count,
        }

    def _check_praise_words(self, text: str) -> dict[str, Any]:
        """Check for forbidden praise words (ayu only).

        RETRY if: praise word + affirmation toward other person
        WARN if: praise word alone
        """
        non_quoted = self._extract_non_quoted_text(text)
        found_praise: list[str] = []

        for word in self.PRAISE_WORDS_FOR_AYU:
            if word in non_quoted:
                found_praise.append(word)

        if not found_praise:
            return {"status": "PASS", "found": []}

        # Check for affirmation toward other person
        affirmation_patterns = [
            "あなた",
            "きみ",
            "姉様",
            "やな",
            "その答え",
            "その考え",
            "正しい",
            "合っている",
        ]
        has_affirmation = any(pat in non_quoted for pat in affirmation_patterns)

        if has_affirmation:
            return {
                "status": "RETRY",
                "reason": f"褒め言葉を使わないでください: {', '.join(found_praise)}",
                "found": found_praise,
            }

        return {
            "status": "WARN",
            "reason": f"褒め言葉が含まれています: {', '.join(found_praise)}",
            "found": found_praise,
        }

    def _check_setting_consistency(self, text: str) -> dict[str, Any]:
        """Check for expressions that break world setting.

        Sisters live together - expressions suggesting separate living are forbidden.
        """
        found_violations: list[str] = []

        for word in self.SEPARATION_WORDS:
            if word in text:
                found_violations.append(word)

        if found_violations:
            return {
                "status": "RETRY",
                "reason": f"設定破壊表現があります: {', '.join(found_violations)}",
                "found": found_violations,
            }

        return {"status": "PASS", "found": []}

    def _check_ai_isms(self, text: str) -> dict[str, Any]:
        """Check for AI-like expressions that break character."""
        non_quoted = self._extract_non_quoted_text(text)
        found_violations: list[str] = []

        for pattern in self.AI_ISM_PATTERNS:
            if pattern in non_quoted:
                found_violations.append(pattern)

        for pattern in self.STAGE_DIRECTIONS:
            if pattern in non_quoted:
                found_violations.append(pattern)

        if found_violations:
            return {
                "status": "RETRY",
                "reason": f"AI臭い表現があります: {', '.join(found_violations)}",
                "found": found_violations,
            }

        return {"status": "PASS", "found": []}

    def _check_tone_markers(self, speaker: str, text: str) -> dict[str, Any]:
        """Check tone markers for character consistency.

        tone_score = marker_hit + vocab_hit + style_hit
        score >= 2 → PASS
        score == 1 → WARN
        score == 0 → RETRY
        """
        if speaker not in self.TONE_MARKERS:
            return {"status": "PASS", "score": 3, "details": {}}

        markers = self.TONE_MARKERS[speaker]
        non_quoted = self._extract_non_quoted_text(text)

        # Check endings
        marker_hit = 0
        for ending in markers["endings"]:
            if ending in non_quoted:
                marker_hit = 1
                break

        # Check vocabulary
        vocab_hit = 0
        for vocab in markers["vocab"]:
            if vocab in non_quoted:
                vocab_hit = 1
                break

        # Check style
        style_hit = 0
        if speaker == "yana":
            # yana: short (2 sentences or less) + exclamation
            sentence_count = len(re.findall(r"[。！？]", text))
            has_exclamation = "！" in text or "？" in text
            if sentence_count <= 2 and has_exclamation:
                style_hit = 1
        else:  # ayu
            # ayu: polite endings appear 2+ times
            polite_count = len(re.findall(r"(です|ます|でした|ました)[。！？]?", text))
            if polite_count >= 2:
                style_hit = 1

        tone_score = marker_hit + vocab_hit + style_hit

        details = {
            "marker_hit": marker_hit,
            "vocab_hit": vocab_hit,
            "style_hit": style_hit,
            "score": tone_score,
        }

        if tone_score == 0:
            return {
                "status": "RETRY",
                "reason": f"{speaker}らしい口調が全くありません。",
                "score": tone_score,
                "details": details,
            }

        if tone_score == 1:
            return {
                "status": "WARN",
                "reason": f"{speaker}らしい口調が弱いです。",
                "score": tone_score,
                "details": details,
            }

        return {"status": "PASS", "score": tone_score, "details": details}

    def _score_with_llm(
        self,
        speaker: str,
        response: str,
        history: list[dict[str, str]] | None,
    ) -> dict[str, Any]:
        """Score response using LLM evaluation.

        Args:
            speaker: Character ID
            response: Response text to evaluate
            history: Conversation history for context

        Returns:
            Dictionary with scores and status
        """
        if not self._llm_client:
            return {"status": "SKIP", "reason": "LLM client not configured"}

        scoring_config = self._rules.get("scoring", {})
        retry_threshold = scoring_config.get("retry_threshold", self.DEFAULT_RETRY_THRESHOLD)
        warn_threshold = scoring_config.get("warn_threshold", self.DEFAULT_WARN_THRESHOLD)

        # Build evaluation prompt
        prompt = self._build_scoring_prompt(speaker, response, history)

        try:
            messages = [
                {"role": "system", "content": "あなたは対話品質の評価者です。指示に従ってJSON形式で評価してください。"},
                {"role": "user", "content": prompt},
            ]

            result = self._llm_client.generate(
                messages=messages,
                temperature=0.1,  # Low temperature for consistent scoring
                max_tokens=500,
            )

            # Parse JSON response
            scores = self._parse_scoring_response(result)

            if not scores:
                return {"status": "SKIP", "reason": "スコア解析失敗"}

            # Calculate average
            avg_score = sum(scores.values()) / len(scores) if scores else 0.0

            # Determine status
            if avg_score < retry_threshold:
                status = "RETRY"
                reason = f"品質スコアが低いです（平均: {avg_score:.2f}）"
            elif avg_score < warn_threshold:
                status = "WARN"
                reason = f"品質スコアがやや低いです（平均: {avg_score:.2f}）"
            else:
                status = "PASS"
                reason = ""

            return {
                "status": status,
                "reason": reason,
                "scores": scores,
                "avg_score": avg_score,
            }

        except Exception as e:
            self._logger.warning(f"LLMスコアリング失敗: {e}")
            return {"status": "SKIP", "reason": str(e)}

    def _build_scoring_prompt(
        self,
        speaker: str,
        response: str,
        history: list[dict[str, str]] | None,
    ) -> str:
        """Build prompt for LLM scoring."""
        history_text = ""
        if history:
            recent = history[-4:]  # Last 4 turns for context
            history_lines = []
            for msg in recent:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)

        criteria_text = "\n".join(
            f"- {name}: {desc}" for name, desc in self.SCORING_CRITERIA.items()
        )

        speaker_name = "やな（姉）" if speaker == "yana" else "あゆ（妹）"

        return f"""以下の発言を5つの観点で評価してください。

【発言者】{speaker_name}
【発言内容】{response}

【直前の会話】
{history_text if history_text else "(なし)"}

【評価観点】（各1-5点）
{criteria_text}

【回答形式】
必ず以下のJSON形式のみで回答してください。説明は不要です。
{{"frame_consistency": X, "roleplay": X, "connection": X, "information_density": X, "naturalness": X}}"""

    def _parse_scoring_response(self, response: str) -> dict[str, float]:
        """Parse LLM response to extract scores."""
        # Try to find JSON in response
        json_match = re.search(r"\{[^{}]+\}", response)
        if not json_match:
            return {}

        try:
            scores_raw = json.loads(json_match.group())

            # Validate and extract scores
            scores: dict[str, float] = {}
            for key in self.SCORING_CRITERIA:
                if key in scores_raw:
                    value = float(scores_raw[key])
                    # Clamp to valid range
                    scores[key] = max(1.0, min(5.0, value))

            # Only return if we got all scores
            if len(scores) == len(self.SCORING_CRITERIA):
                return scores

            return {}

        except (json.JSONDecodeError, ValueError, TypeError):
            return {}
