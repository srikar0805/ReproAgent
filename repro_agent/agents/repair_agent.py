"""Repair policy placeholder."""

from __future__ import annotations


SCIENTIFICALLY_UNSAFE_CHANGES = (
    "model architecture",
    "dataset",
    "final experiment epochs",
    "loss function",
    "evaluation metric",
)


class RepairAgent:
    def classify_repair_boundary(self, proposed_change: str) -> str:
        lower = proposed_change.lower()
        if any(change in lower for change in SCIENTIFICALLY_UNSAFE_CHANGES):
            return "requires human review"
        return "eligible for automated minimal patch"
