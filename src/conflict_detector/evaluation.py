import json
from collections import Counter
from pathlib import Path

import pandas as pd


def evaluate_alerts(alerts: list[dict], scenario_labels: pd.DataFrame) -> dict:
    cases = _scenario_cases(scenario_labels)
    matched_case_ids: set[str] = set()
    matched_alerts = 0

    for alert in alerts:
        alert_entities = _alert_entity_ids(alert)
        if not alert_entities:
            continue
        matched = False
        for case in cases:
            if case["scenario_id"] != alert.get("scenario_id"):
                continue
            if _is_match(alert_entities, case["entity_ids"]):
                matched_case_ids.add(case["case_id"])
                matched = True
        if matched:
            matched_alerts += 1

    requested_by_scenario = Counter(case["scenario_id"] for case in cases)
    matched_by_scenario = Counter(case["scenario_id"] for case in cases if case["case_id"] in matched_case_ids)
    alert_counts = Counter(str(alert.get("scenario_id")) for alert in alerts)

    return {
        "total_scenario_cases": len(cases),
        "matched_scenario_cases": len(matched_case_ids),
        "total_alerts": len(alerts),
        "matched_alerts": matched_alerts,
        "precision_estimate": _ratio(matched_alerts, len(alerts)),
        "recall_estimate": _ratio(len(matched_case_ids), len(cases)),
        "by_scenario": [
            {
                "scenario_id": scenario_id,
                "expected_cases": requested_by_scenario[scenario_id],
                "matched_cases": matched_by_scenario[scenario_id],
                "alerts": alert_counts[scenario_id],
                "recall_estimate": _ratio(matched_by_scenario[scenario_id], requested_by_scenario[scenario_id]),
            }
            for scenario_id in sorted(requested_by_scenario)
        ],
    }


def evaluate_alert_file(alerts_file: str | Path, labels_file: str | Path, output_file: str | Path) -> dict:
    alerts = json.loads(Path(alerts_file).read_text(encoding="utf-8")).get("alerts", [])
    labels = pd.read_csv(labels_file)
    result = evaluate_alerts(alerts, labels)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _scenario_cases(labels: pd.DataFrame) -> list[dict]:
    cases = []
    for index, row in labels.reset_index(drop=True).iterrows():
        scenario_id = str(row.get("scenario_id", "")).strip()
        entity_ids = _business_entity_ids(str(row.get("entity_ids", "")))
        if scenario_id and entity_ids:
            cases.append({"case_id": f"case_{index + 1}", "scenario_id": scenario_id, "entity_ids": entity_ids})
    return cases


def _alert_entity_ids(alert: dict) -> set[str]:
    return {
        str(entity.get("id"))
        for entity in alert.get("entities", [])
        if str(entity.get("id", "")).startswith(("EMP", "FOU", "TRX"))
    }


def _business_entity_ids(raw: str) -> set[str]:
    return {item for item in raw.split("|") if item.startswith(("EMP", "FOU", "TRX"))}


def _is_match(alert_entities: set[str], case_entities: set[str]) -> bool:
    overlap = alert_entities & case_entities
    threshold = min(2, len(case_entities), len(alert_entities))
    return len(overlap) >= threshold


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
