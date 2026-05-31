import pandas as pd

from conflict_detector.evaluation import evaluate_alerts


def test_evaluate_alerts_matches_synthetic_ground_truth() -> None:
    alerts = [
        {
            "scenario_id": "identity_match",
            "entities": [
                {"id": "EMP001", "type": "Employe"},
                {"id": "FOU001", "type": "Fournisseur"},
            ],
        },
        {
            "scenario_id": "ghost_supplier",
            "entities": [{"id": "FOU999", "type": "Fournisseur"}],
        },
    ]
    labels = pd.DataFrame(
        [
            {"scenario_id": "identity_match", "entity_ids": "EMP001|FOU001|email"},
            {"scenario_id": "ghost_supplier", "entity_ids": "FOU002|TRX001"},
        ]
    )

    result = evaluate_alerts(alerts, labels)

    assert result["total_scenario_cases"] == 2
    assert result["matched_scenario_cases"] == 1
    assert result["matched_alerts"] == 1
    assert result["recall_estimate"] == 0.5
