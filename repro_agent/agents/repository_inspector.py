"""Repository inspection agent."""

from __future__ import annotations

from pathlib import Path
import tempfile

from repro_agent.schemas.experiment import DatasetInfo, Entrypoints, RepositoryInspection
from repro_agent.tools.code_search import (
    extract_readme_commands,
    find_configs,
    find_entrypoints,
    summarize_readme,
)
from repro_agent.tools.dependency_tools import (
    detect_framework,
    detect_python_version,
    find_dependency_files,
)
from repro_agent.tools.git_tools import clone_repository, get_commit, get_remote_url, looks_like_url


class RepositoryInspector:
    """Inspect code repositories for likely reproduction entry points."""

    def inspect(self, source: str, clone: bool = False) -> RepositoryInspection:
        with tempfile.TemporaryDirectory(prefix="repro-agent-") as tmpdir:
            repo_path, url = self._resolve_source(source, clone, Path(tmpdir))
            return self._inspect_path(repo_path, source=source, url=url)

    def inspect_path(self, repo_path: Path) -> RepositoryInspection:
        return self._inspect_path(repo_path, source=str(repo_path), url=get_remote_url(repo_path))

    def _resolve_source(
        self, source: str, clone: bool, tmpdir: Path
    ) -> tuple[Path, str | None]:
        source_path = Path(source).expanduser()
        if source_path.exists():
            return source_path.resolve(), get_remote_url(source_path)

        if looks_like_url(source):
            if not clone:
                raise ValueError(
                    "Remote repository inspection requires --clone so ReproAgent can "
                    "fetch a temporary copy."
                )
            destination = tmpdir / "repo"
            return clone_repository(source, destination), source

        raise FileNotFoundError(source)

    def _inspect_path(
        self, repo_path: Path, source: str, url: str | None
    ) -> RepositoryInspection:
        dependency_sources = find_dependency_files(repo_path)
        framework = detect_framework(repo_path, dependency_sources)
        train, evaluate, candidates = find_entrypoints(repo_path)
        configs = find_configs(repo_path)
        readme_commands = extract_readme_commands(repo_path)

        candidate_command = self._candidate_command(train, configs, readme_commands)
        candidate_command = self._complete_required_output_arg(repo_path, candidate_command)
        uncertainties = []
        if not dependency_sources:
            uncertainties.append("No recognized dependency file was found")
        if framework is None:
            uncertainties.append("ML framework was not detected")
        if not candidate_command:
            uncertainties.append("Training command could not be inferred")

        return RepositoryInspection(
            source=source,
            url=url,
            commit=get_commit(repo_path),
            language="python" if list(repo_path.rglob("*.py")) else None,
            framework=framework,
            python_version=detect_python_version(repo_path),
            dependency_sources=dependency_sources,
            entrypoints=Entrypoints(train=train, evaluate=evaluate, candidates=candidates),
            configs=configs,
            dataset=self._detect_dataset(repo_path),
            candidate_command=candidate_command,
            readme_summary=summarize_readme(repo_path),
            uncertainties=uncertainties,
        )

    def _candidate_command(
        self,
        train: str | None,
        configs: list[str],
        readme_commands: list[list[str]],
    ) -> list[str]:
        if readme_commands:
            return readme_commands[0]
        if train and configs:
            return ["python", train, "--config", configs[0]]
        if train:
            return ["python", train]
        return []

    def _complete_required_output_arg(self, repo_path: Path, command: list[str]) -> list[str]:
        if "--output" in command:
            return command

        script = next((part for part in command if part.endswith(".py")), None)
        if script is None:
            return command

        script_path = repo_path / script
        if not script_path.exists():
            return command

        text = script_path.read_text(encoding="utf-8", errors="ignore")
        if '"--output", required=True' not in text and "'--output', required=True" not in text:
            return command

        return [*command, "--output", "artifacts/metrics.json"]

    def _detect_dataset(self, repo_path: Path) -> DatasetInfo:
        text = ""
        for path in list(repo_path.rglob("*.py"))[:100]:
            if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
                continue
            text += path.read_text(encoding="utf-8", errors="ignore").lower()
        readme_text = (summarize_readme(repo_path) or "").lower()
        combined = f"{readme_text}\n{text}"

        name = None
        if "pigformer" in combined or "sow" in combined or "swine" in combined:
            name = "Swine RGB-D body-condition dataset"
        elif "cifar10" in combined or "cifar-10" in combined:
            name = "CIFAR-10"
        elif "mnist" in combined:
            name = "MNIST"
        elif "imagenet" in combined:
            name = "ImageNet"

        paths = [
            path.relative_to(repo_path).as_posix()
            for path in repo_path.rglob("*")
            if path.is_dir() and path.name.lower() in {"data", "dataset", "datasets"}
        ]
        auto_download = "download=true" in text or "download = true" in text
        return DatasetInfo(name=name, auto_download=auto_download or None, paths=paths[:20])
