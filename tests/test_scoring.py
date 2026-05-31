from conflict_detector.domain.enums import Severity
from conflict_detector.scoring.scorer import assign_severity, compute_alert_score, score_alerts


def test_assign_severity() -> None:
    config = {"severity": {"high": 12, "medium": 7}}
    assert assign_severity(13, config) == Severity.HIGH
    assert assign_severity(8, config) == Severity.MEDIUM
    assert assign_severity(4, config) == Severity.LOW


def test_score_alerts_adds_score_and_severity() -> None:
    config = {
        "attributes": {"iban": 10},
        "patterns": {"identity_match": 2},
        "depth_penalty": {1: 0},
        "severity": {"high": 12, "medium": 7},
    }
    alerts = [{"scenario_id": "identity_match", "evidence": {"attribute": "iban"}}]

    scored = score_alerts(alerts, config)

    assert scored[0]["score"] == 12
    assert scored[0]["severity"] == "HIGH"
    assert compute_alert_score("identity_match", {"attribute": "iban"}, config) == 12
