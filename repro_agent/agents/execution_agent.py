"""Controlled execution placeholder."""

from __future__ import annotations

from repro_agent.schemas.execution import ExecutionPlan


class ExecutionAgent:
    def smoke_test_plan(self, command: list[str]) -> ExecutionPlan:
        return ExecutionPlan(
            command=command,
            timeout_minutes=15,
            retries=1,
            requires_network=False,
            warnings=["Smoke-test execution is part of milestone 2."],
        )
