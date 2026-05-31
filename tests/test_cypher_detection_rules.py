from conflict_detector.detection.base import DetectionResult
from conflict_detector.detection.cypher_rules import DEFAULT_RULES, detection_result_to_dict
from conflict_detector.domain.enums import ScenarioId


def test_default_cypher_rules_do_not_use_scenario_ground_truth() -> None:
    forbidden_terms = ["ScenarioCase", "Scenario", "IMPLIQUE_DANS", "TYPE_SCENARIO"]

    assert DEFAULT_RULES
    assert len({rule.scenario_id for rule in DEFAULT_RULES}) == 11
    for rule in DEFAULT_RULES:
        for term in forbidden_terms:
            assert term not in rule.query


def test_detection_result_to_dict_serializes_scenario_id() -> None:
    result = DetectionResult(
        scenario_id=ScenarioId.IDENTITY_MATCH,
        entities=[{"id": "EMP001", "type": "Employe", "label": "Alice"}],
        evidence={"rule_id": "shared_email_employee_supplier"},
        path=["EMP001"],
        source_rows=["TRX001"],
    )

    assert detection_result_to_dict(result) == {
        "scenario_id": "identity_match",
        "entities": [{"id": "EMP001", "type": "Employe", "label": "Alice"}],
        "evidence": {"rule_id": "shared_email_employee_supplier"},
        "path": ["EMP001"],
        "source_rows": ["TRX001"],
    }
