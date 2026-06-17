from pathlib import Path

from repro_agent.agents.paper_analyzer import PaperAnalyzer


def test_paper_analyzer_extracts_target_details() -> None:
    analysis = PaperAnalyzer().analyze(
        Path("tests/fixtures/paper.txt"),
        "Table 2, Model A, CIFAR-10 accuracy",
    )

    assert analysis.title == "ReproAgent Example Paper"
    assert analysis.target.table == "Table 2"
    assert analysis.target.dataset == "CIFAR-10"
    assert analysis.target.metric is not None
    assert analysis.target.metric.name == "accuracy"
    assert analysis.target.metric.value == 0.914
    assert analysis.configuration.epochs == 100
    assert analysis.configuration.batch_size == 128
    assert analysis.configuration.optimizer == "Adam"
    assert analysis.configuration.learning_rate == 0.001
