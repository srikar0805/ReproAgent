from pathlib import Path

from repro_agent.agents.repository_inspector import RepositoryInspector
from repro_agent.tools.code_search import extract_readme_commands


def test_repository_inspector_finds_pytorch_training_command() -> None:
    inspection = RepositoryInspector().inspect_path(Path("tests/fixtures/sample_repo"))

    assert inspection.language == "python"
    assert inspection.framework == "pytorch"
    assert inspection.dependency_sources == ["requirements.txt"]
    assert inspection.entrypoints.train == "scripts/train.py"
    assert inspection.configs == ["configs/cifar10/model_a.yaml"]
    assert inspection.dataset.name == "CIFAR-10"
    assert inspection.commit is None
    assert inspection.url is None
    assert inspection.candidate_command == [
        "python",
        "scripts/train.py",
        "--config",
        "configs/cifar10/model_a.yaml",
    ]


def test_readme_commands_skip_setup_and_join_continuations(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        """
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
python evaluate_ensemble.py \\
    --checkpoints results/fold0/best.pt results/fold1/best.pt \\
    --dataset data/dataset.h5
```
""",
        encoding="utf-8",
    )

    assert extract_readme_commands(tmp_path) == [
        [
            "python",
            "evaluate_ensemble.py",
            "--checkpoints",
            "results/fold0/best.pt",
            "results/fold1/best.pt",
            "--dataset",
            "data/dataset.h5",
        ]
    ]
