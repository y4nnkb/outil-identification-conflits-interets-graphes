from conflict_detector.domain.enums import Severity
from conflict_detector.scoring.scorer import assign_severity


def test_assign_severity() -> None:
    config = {"severity": {"high": 12, "medium": 7}}
    assert assign_severity(13, config) == Severity.HIGH
    assert assign_severity(8, config) == Severity.MEDIUM
    assert assign_severity(4, config) == Severity.LOW
