import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from conflict_detector.generation.config import GenerationConfig


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


def build_manifest(
    config: GenerationConfig,
    tables: dict[str, list[dict]],
    scenario_counts: dict[str, int],
    noise_summary: dict[str, int] | None = None,
) -> dict:
    injected_counts = Counter(row["scenario_id"] for row in tables.get("scenario_labels", []))
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "seed": config.seed,
        "output_dir": config.output_dir,
        "requested_volumes": config.volumes.model_dump(),
        "generated_rows": {name: len(rows) for name, rows in tables.items()},
        "scenario_counts_requested": scenario_counts,
        "scenario_counts_injected": dict(sorted(injected_counts.items())),
        "noise_injected": noise_summary or {},
        "config": config.model_dump(),
    }
