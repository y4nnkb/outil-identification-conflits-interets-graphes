import csv
import json
from pathlib import Path


def write_dataset(tables: dict[str, list[dict]], output_dir: str | Path) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for file in target.glob("*.csv"):
        file.unlink()
    for name, rows in tables.items():
        path = target / f"{name}.csv"
        fields = sorted({key for row in rows for key in row.keys()})
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def write_manifest(payload: dict, output_dir: str | Path) -> None:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    with open(target / "generation_manifest.json", "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
