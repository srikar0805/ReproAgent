"""Result comparison agent."""

from __future__ import annotations

from repro_agent.schemas.report import ReproductionStatus, VerificationResult


class ResultVerifier:
    def compare(
        self,
        reported_value: float | None,
        reproduced_value: float | None,
        tolerance: float = 0.01,
    ) -> VerificationResult:
        if reported_value is None or reproduced_value is None:
            return VerificationResult(
                reported_value=reported_value,
                reproduced_value=reproduced_value,
                absolute_difference=None,
                relative_difference=None,
                tolerance=tolerance,
                status=ReproductionStatus.INSUFFICIENT_INFORMATION,
                notes=["Reported or reproduced value is missing."],
            )

        absolute = reproduced_value - reported_value
        relative = absolute / reported_value if reported_value else None
        status = (
            ReproductionStatus.EXACT
            if abs(absolute) <= tolerance
            else ReproductionStatus.APPROXIMATE
        )
        return VerificationResult(
            reported_value=reported_value,
            reproduced_value=reproduced_value,
            absolute_difference=absolute,
            relative_difference=relative,
            tolerance=tolerance,
            status=status,
        )
