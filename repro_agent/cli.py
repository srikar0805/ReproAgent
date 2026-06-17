"""Command-line interface for ReproAgent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from repro_agent.orchestrator import Orchestrator
from repro_agent.reporting.report_builder import build_audit_report
from repro_agent.schemas.common import to_plain_data
from repro_agent.tools.yaml_tools import dumps_yaml


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    orchestrator = Orchestrator()

    try:
        if args.command == "inspect-paper":
            result = orchestrator.inspect_paper(Path(args.paper), args.target)
            _print_data(result, as_json=args.json)
            return 0

        if args.command == "inspect-repo":
            result = orchestrator.inspect_repo(args.repo, clone=args.clone)
            _print_data(result, as_json=args.json)
            return 0

        if args.command == "init-reproduction":
            spec = orchestrator.init_reproduction(
                Path(args.paper),
                args.repo,
                args.target,
                device=args.device,
                clone=args.clone,
            )
            content = dumps_yaml(to_plain_data(spec))
            output = Path(args.output)
            output.write_text(content, encoding="utf-8")
            print(f"Wrote {output}")
            return 0

        if args.command == "audit":
            spec, audit = orchestrator.audit(
                Path(args.paper),
                args.repo,
                args.target,
                device=args.device,
                clone=args.clone,
            )
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            _write_text(output_dir / "reproduction.yaml", dumps_yaml(to_plain_data(spec)))
            _write_json(output_dir / "artifact-audit.json", to_plain_data(audit.artifact_audit))
            _write_json(output_dir / "command-audit.json", to_plain_data(audit.command_audit))
            _write_json(output_dir / "environment-audit.json", to_plain_data(audit.environment_audit))
            _write_text(output_dir / "reproducibility-report.md", build_audit_report(audit))
            _write_json(output_dir / "audit.json", to_plain_data(audit))
            print(f"Wrote audit artifacts to {output_dir}")
            print(f"Verdict: {audit.verdict.status.value}")
            print(f"Reason: {audit.verdict.primary_reason}")
            return 0

        parser.print_help()
        return 1
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repro-agent",
        description="Research reproduction assistant.",
    )
    subparsers = parser.add_subparsers(dest="command")

    inspect_paper = subparsers.add_parser("inspect-paper", help="Analyze a paper PDF/text file.")
    inspect_paper.add_argument("paper")
    inspect_paper.add_argument("--target", help="Specific table/result to reproduce.")
    inspect_paper.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    inspect_repo = subparsers.add_parser("inspect-repo", help="Inspect a repository.")
    inspect_repo.add_argument("repo", help="Local path or public Git URL.")
    inspect_repo.add_argument("--clone", action="store_true", help="Clone remote Git URLs temporarily.")
    inspect_repo.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    init = subparsers.add_parser(
        "init-reproduction",
        help="Generate a reproduction.yaml draft from a paper and repository.",
    )
    init.add_argument("--paper", required=True)
    init.add_argument("--repo", required=True)
    init.add_argument("--target", required=True)
    init.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    init.add_argument("--clone", action="store_true", help="Clone remote Git URLs temporarily.")
    init.add_argument("--output", default="reproduction.yaml")

    audit = subparsers.add_parser(
        "audit",
        help="Audit public materials and produce a reproducibility verdict.",
    )
    audit.add_argument("--paper", required=True)
    audit.add_argument("--repo", required=True)
    audit.add_argument("--target", required=True)
    audit.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    audit.add_argument("--clone", action="store_true", help="Clone remote Git URLs temporarily.")
    audit.add_argument("--output-dir", default="artifacts/audit")
    return parser


def _print_data(data: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(dumps_yaml(data))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
