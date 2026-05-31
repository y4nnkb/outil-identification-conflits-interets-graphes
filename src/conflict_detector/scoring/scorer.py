from conflict_detector.domain.enums import Severity


def compute_attribute_score(evidence: dict, config: dict) -> float:
    attributes = config.get("attributes", {})
    score = 0.0
    attribute = evidence.get("attribute")
    if attribute:
        score += float(attributes.get(_attribute_key(attribute), 0))
    for shared_attribute in evidence.get("shared_attributes", []):
        score += float(attributes.get(_attribute_key(shared_attribute), 0))
    return score


def compute_pattern_bonus(scenario_id: str, config: dict) -> float:
    return float(config["patterns"].get(scenario_id, 0))


def compute_financial_bonus(evidence: dict, config: dict) -> float:
    total_amount = float(evidence.get("total_amount") or 0)
    average_amount = float(evidence.get("average_amount") or 0)
    transaction_count = int(evidence.get("transaction_count") or 0)
    bonus = 0.0
    if total_amount >= 1_000_000:
        bonus += 4
    elif total_amount >= 250_000:
        bonus += 2
    if average_amount >= 100_000:
        bonus += 2
    if transaction_count >= 5:
        bonus += 1
    return bonus


def compute_temporal_bonus(evidence: dict, config: dict) -> float:
    if "gift_delay_days" not in evidence:
        return 0.0
    delay = int(evidence.get("gift_delay_days") or 0)
    if delay <= 1:
        return 3.0
    if delay <= 7:
        return 2.0
    return 0.0


def compute_depth_penalty(depth: int, config: dict) -> float:
    return float(config["depth_penalty"].get(str(depth), config["depth_penalty"].get(depth, 0)))


def compute_alert_score(scenario_id: str, evidence: dict, config: dict) -> float:
    score = compute_pattern_bonus(scenario_id, config)
    score += compute_attribute_score(evidence, config)
    score += compute_financial_bonus(evidence, config)
    score += compute_temporal_bonus(evidence, config)
    score += _network_bonus(evidence)
    score += compute_depth_penalty(int(evidence.get("depth") or 1), config)
    return max(0.0, score)


def assign_severity(score: float, config: dict) -> Severity:
    if score >= config["severity"]["high"]:
        return Severity.HIGH
    if score >= config["severity"]["medium"]:
        return Severity.MEDIUM
    return Severity.LOW


def score_alerts(alerts: list, config: dict) -> list:
    scored = []
    for alert in alerts:
        item = dict(alert)
        score = compute_alert_score(str(item.get("scenario_id", "")), item.get("evidence", {}), config)
        item["score"] = score
        item["severity"] = assign_severity(score, config).value
        scored.append(item)
    return sorted(scored, key=lambda alert: (-float(alert["score"]), alert["scenario_id"]))


def _attribute_key(attribute: str) -> str:
    mapping = {
        "ADRESSE": "address",
        "EMAIL": "email",
        "IBAN": "iban",
        "TELEPHONE": "phone",
        "PHONE": "phone",
        "SIREN": "siren",
        "NOM": "name",
        "NAME": "name",
    }
    return mapping.get(str(attribute).upper(), str(attribute).lower())


def _network_bonus(evidence: dict) -> float:
    bonus = 0.0
    if int(evidence.get("supplier_count") or 0) >= 3:
        bonus += 2
    if int(evidence.get("employee_count") or 0) >= 2:
        bonus += 2
    if len(evidence.get("shared_attributes", [])) >= 3:
        bonus += 2
    if evidence.get("is_boite_postale") == "true":
        bonus += 2
    return bonus
