"""Report schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ReproductionStatus(str, Enum):
    EXACT = "exact reproduction"
    APPROXIMATE = "approximate reproduction"
    PARTIAL = "partial reproduction"
    FAILED = "failed reproduction"
    INSUFFICIENT_INFORMATION = "insufficient information"


@dataclass(frozen=True)
class VerificationResult:
    reported_value: float | None
    reproduced_value: float | None
    absolute_difference: float | None
    relative_difference: float | None
    tolerance: float
    status: ReproductionStatus
    notes: list[str] = field(default_factory=list)
