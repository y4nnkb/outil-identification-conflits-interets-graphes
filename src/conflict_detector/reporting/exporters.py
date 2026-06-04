import csv
import json
from collections import Counter
from pathlib import Path

from conflict_detector.reporting.html_report import (
    aggregate_alerts_by_employee,
    render_html_report,
    render_scenario_documentation,
)


def export_alerts_csv(alerts: list[dict], path: str | Path) -> None:
    rows = alerts
    fields = sorted({key for row in rows for key in row.keys()})
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{key: _csv_value(value) for key, value in row.items()} for row in rows])


def export_alerts_json(alerts: list[dict], path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump({"alerts": alerts}, file, ensure_ascii=False, indent=2)


def export_summary_json(alerts: list[dict], path: str | Path) -> None:
    by_scenario = Counter(str(alert.get("scenario_id")) for alert in alerts)
    by_severity = Counter(str(alert.get("severity", "UNSCORED")) for alert in alerts)
    employee_rows = aggregate_alerts_by_employee(alerts)
    payload = {
        "total_alerts": len(alerts),
        "by_scenario": dict(sorted(by_scenario.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "employees_with_alerts": len(employee_rows),
        "top_employees": employee_rows[:10],
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def export_graphml(path: str | Path) -> None:
    raise NotImplementedError


def export_employee_aggregation(alerts: list[dict], output_dir: str | Path) -> None:
    target = Path(output_dir)
    employee_rows = aggregate_alerts_by_employee(alerts)
    with open(target / "alerts_by_employee.json", "w", encoding="utf-8") as file:
        json.dump({"employees": employee_rows}, file, ensure_ascii=False, indent=2)
    fields = sorted({key for row in employee_rows for key in row.keys()})
    with open(target / "alerts_by_employee.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(employee_rows)


def export_report_bundle(alerts: list[dict], output_dir: str | Path, config: dict | None = None) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    export_alerts_csv(alerts, target / "alerts.csv")
    export_alerts_json(alerts, target / "alerts.json")
    export_summary_json(alerts, target / "summary.json")
    export_employee_aggregation(alerts, target)
    render_html_report(alerts, target / "report.html", config)
    render_scenario_documentation(target / "scenarios.html")


def _csv_value(value: object) -> object:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value
