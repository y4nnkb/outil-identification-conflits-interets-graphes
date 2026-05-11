from conflict_detector.detection.registry import RuleRegistry


def test_registry_starts_empty() -> None:
    assert RuleRegistry().rules == []
