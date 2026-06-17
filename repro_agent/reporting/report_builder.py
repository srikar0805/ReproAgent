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
    metadata = data["metadata"]
    lines = [
        "# Reproducibility Audit",
        "",
        f"Audit ID: {metadata['audit_id']}",
        f"Created: {metadata['created_at']}",
        f"Schema version: {metadata['schema_version']}",
        f"Tool version: {metadata['tool_version']}",
        f"Verdict: {data['verdict']['status']}",
        f"Internal status: {data['status']}",
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
        for item in missing:
            finding = f"{item['finding_id']} " if item.get("finding_id") else ""
            confidence = item.get("confidence")
            lines.append(
                f"- {finding}{item['path']} ({item['category']}, {item['severity']})"
            )
            if confidence is not None:
                lines.append(f"  Confidence: {confidence}")
            lines.append(f"  Required for: {item['required_for']}")
            impact = item.get("impact") or {}
            lines.append(
                "  Impact: "
                f"blocks_execution={impact.get('blocks_execution')}, "
                f"blocks_result_verification={impact.get('blocks_result_verification')}"
            )
            evidence = item.get("evidence") or []
            if evidence:
                lines.append("  Evidence:")
                for entry in evidence[:4]:
                    location = entry["source"]
                    if entry.get("line"):
                        location = f"{location}:{entry['line']}"
                    lines.append(f"  - {location}: {entry['detail']}")
            searched = item.get("searched_locations") or []
            if searched:
                lines.append(f"  Searched: {', '.join(searched)}")
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
