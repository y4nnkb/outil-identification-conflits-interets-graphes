from pathlib import Path

import typer

from conflict_detector.generation.config import GenerationConfig, resolve_scenario_counts
from conflict_detector.generation.factory import DatasetFactory
from conflict_detector.generation.scenario_injector import ScenarioInjector
from conflict_detector.generation.writer import write_dataset, write_manifest
from conflict_detector.settings import load_generation_config


def main(config: Path = Path("configs/generation.yml")) -> None:
    raw = load_generation_config(config)
    generation_config = GenerationConfig.model_validate(raw)
    tables = DatasetFactory(generation_config).generate()
    counts = resolve_scenario_counts(generation_config, generation_config.volumes.transactions)
    ScenarioInjector(generation_config).inject(tables, counts)
    write_dataset(tables, generation_config.output_dir)
    write_manifest({"seed": generation_config.seed, "scenario_counts": counts}, generation_config.output_dir)


if __name__ == "__main__":
    typer.run(main)
