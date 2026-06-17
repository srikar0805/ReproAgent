"""Markdown report generation."""

from __future__ import annotations

from repro_agent.schemas.common import to_plain_data
from repro_agent.schemas.audit import ReproducibilityAudit
from repro_agent.schemas.experiment import ReproductionSpec


def build_reproduction_report(spec: ReproductionSpec) -> str:
    data = to_plain_data(spec)
    metric = data["target"]["reported_metric"]
    lines = [
        "# Reproduction Plan",
        "",
        f"Paper: {data['paper']['title'] or 'Unknown'}",
        f"Repository: {data['repository']['url']}",
        f"Target: {data['target']['description']}",
        "",
        "## Reported Metric",
        "",
        f"- Name: {metric['name'] or 'unknown'}",
        f"- Value: {metric['value'] if metric['value'] is not None else 'unknown'}",
        "",
        "## Proposed Command",
        "",
        "```bash",
        " ".join(data["execution"]["command"]) if data["execution"]["command"] else "# unknown",
        "```",
        "",
        "## Uncertainties",
        "",
    ]
    uncertainties = data["target"]["uncertainties"]
    if uncertainties:
        lines.extend(f"- {item}" for item in uncertainties)
    else:
        lines.append("- None detected in milestone 1 analysis")
    return "\n".join(lines) + "\n"


def build_audit_report(audit: ReproducibilityAudit) -> str:
    data = to_plain_data(audit)
    missing = data["artifact_audit"]["missing_artifacts"]
    issues = data["command_audit"]["documentation_issues"]
    lines = [
        "# Reproducibility Audit",
        "",
        f"Status: {data['status']}",
        f"Target: {data['target']['description']}",
        "",
        "## Public Result Card",
        "",
        f"Repository inspected: {'Yes' if data['repository']['code_available'] else 'No'}",
        f"Documented command available: {'Yes' if data['repository']['documented_command_available'] else 'No'}",
        f"README command valid: {'Yes' if data['repository']['command_valid'] else 'No'}",
        f"Required artifacts found: {'No' if missing else 'Yes'}",
        "Environment built: Not attempted",
        "Experiment executed: No",
        "Result verified: No",
        "",
        "## Missing Artifacts",
        "",
    ]
    if missing:
        lines.extend(
            f"- {item['path']} ({item['category']}, {item['severity']})"
            for item in missing
        )
    else:
        lines.append("- None detected")

    lines.extend(["", "## Command Validation", ""])
    documented = data["command_audit"]["documented_command"]
    corrected = data["command_audit"]["corrected_command"]
    lines.extend(
        [
            "Documented command:",
            "",
            "```bash",
            " ".join(documented) if documented else "# none detected",
            "```",
            "",
            "Corrected structural command:",
            "",
            "```bash",
            " ".join(corrected) if corrected else "# none detected",
            "```",
            "",
            "Documentation issues:",
        ]
    )
    if issues:
        lines.extend(f"- {issue['message']}" for issue in issues)
    else:
        lines.append("- None detected")

    compute = data["compute"]
    lines.extend(
        [
            "",
            "## Compute Estimate",
            "",
            f"- Accelerator: {compute['accelerator'] or 'unknown'}",
            f"- Fold runtime minutes: {compute['estimated_fold_runtime_minutes'] or 'unknown'}",
            f"- Fold count: {compute['fold_count'] or 'unknown'}",
            f"- Total runtime minutes: {compute['estimated_total_runtime_minutes'] or 'unknown'}",
            "",
            "## Final Verdict",
            "",
            f"Reproducible from public materials: {data['verdict']['reproducible_from_public_materials']}",
            f"Primary reason: {data['verdict']['primary_reason']}",
            "",
            "Recommended actions:",
        ]
    )
    lines.extend(f"- {action}" for action in data["verdict"]["recommended_actions"])
    return "\n".join(lines) + "\n"
