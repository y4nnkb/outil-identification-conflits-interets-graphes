import csv
import json
from pathlib import Path


def export_alerts_csv(alerts: list[dict], path: str | Path) -> None:
    rows = alerts
    fields = sorted({key for row in rows for key in row.keys()})
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def export_alerts_json(alerts: list[dict], path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump({"alerts": alerts}, file, ensure_ascii=False, indent=2)


def export_graphml(path: str | Path) -> None:
    raise NotImplementedError


def export_report_bundle(alerts: list[dict], output_dir: str | Path) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    export_alerts_csv(alerts, target / "alerts.csv")
    export_alerts_json(alerts, target / "alerts.json")
