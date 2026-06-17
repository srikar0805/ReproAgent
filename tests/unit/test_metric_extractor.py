from repro_agent.tools.metric_extractor import extract_metrics


def test_extracts_regression_mae_with_mm_unit() -> None:
    metrics = extract_metrics(
        "PigFormer achieves 2.43 mm backfat MAE and 3.87 mm overall MAE."
    )

    assert any(metric.name == "mae" and metric.value == 3.87 for metric in metrics)
