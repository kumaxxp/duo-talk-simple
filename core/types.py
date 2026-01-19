"""Type definitions for Director quality evaluation system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DirectorStatus(Enum):
    """Evaluation status for AI-generated responses."""

    PASS = "PASS"  # Response is acceptable
    WARN = "WARN"  # Minor issues, but acceptable with intervention
    RETRY = "RETRY"  # Unacceptable, needs regeneration


@dataclass
class DirectorEvaluation:
    """Result of Director's evaluation of a response."""

    status: DirectorStatus
    checks: dict[str, Any] = field(default_factory=dict)
    suggestion: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    avg_score: float = 0.0

    def is_acceptable(self) -> bool:
        """Check if response can be used (PASS or WARN)."""
        return self.status in (DirectorStatus.PASS, DirectorStatus.WARN)


@dataclass
class LoopCheckResult:
    """Result of NoveltyGuard's loop detection."""

    loop_detected: bool = False
    stuck_nouns: list[str] = field(default_factory=list)
    strategy: str = ""
    injection: str = ""
    consecutive_count: int = 0
