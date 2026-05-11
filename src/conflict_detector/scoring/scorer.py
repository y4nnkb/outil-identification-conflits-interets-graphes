from conflict_detector.domain.enums import Severity


def compute_attribute_score(evidence: dict, config: dict) -> float:
    raise NotImplementedError


def compute_pattern_bonus(scenario_id: str, config: dict) -> float:
    return float(config["patterns"].get(scenario_id, 0))


def compute_financial_bonus(evidence: dict, config: dict) -> float:
    raise NotImplementedError


def compute_temporal_bonus(evidence: dict, config: dict) -> float:
    raise NotImplementedError


def compute_depth_penalty(depth: int, config: dict) -> float:
    return float(config["depth_penalty"].get(str(depth), config["depth_penalty"].get(depth, 0)))


def compute_alert_score(scenario_id: str, evidence: dict, config: dict) -> float:
    raise NotImplementedError


def assign_severity(score: float, config: dict) -> Severity:
    if score >= config["severity"]["high"]:
        return Severity.HIGH
    if score >= config["severity"]["medium"]:
        return Severity.MEDIUM
    return Severity.LOW


def score_alerts(alerts: list, config: dict) -> list:
    raise NotImplementedError
