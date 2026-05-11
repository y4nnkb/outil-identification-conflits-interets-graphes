from pathlib import Path

import typer

from conflict_detector.reporting.exporters import export_report_bundle
from conflict_detector.generation.config import GenerationConfig, resolve_scenario_counts
from conflict_detector.generation.factory import DatasetFactory
from conflict_detector.generation.scenario_injector import ScenarioInjector
from conflict_detector.generation.writer import write_dataset, write_manifest
from conflict_detector.settings import load_generation_config

app = typer.Typer()


@app.command()
def generate(config: Path = Path("configs/generation.yml")) -> None:
    raw = load_generation_config(config)
    generation_config = GenerationConfig.model_validate(raw)
    tables = DatasetFactory(generation_config).generate()
    counts = resolve_scenario_counts(generation_config, generation_config.volumes.transactions)
    ScenarioInjector(generation_config).inject(tables, counts)
    write_dataset(tables, generation_config.output_dir)
    write_manifest({"seed": generation_config.seed, "scenario_counts": counts}, generation_config.output_dir)
    typer.echo(f"Dataset genere dans {generation_config.output_dir}")


@app.command()
def load(data: Path = Path("data/generated"), reset: bool = False) -> None:
    if not data.exists():
        raise typer.BadParameter(f"Dossier introuvable: {data}")
    typer.echo("Chargement Neo4j a coder dans src/conflict_detector/graph")


@app.command()
def detect(output: Path = Path("output")) -> None:
    export_report_bundle([], output)
    typer.echo(f"Exports vides generes dans {output}")


@app.command()
def run(data: Path = Path("data/generated"), output: Path = Path("output"), reset: bool = False) -> None:
    if not data.exists():
        typer.echo(f"Dossier data absent: {data}")
        typer.echo("Lance d'abord: python scripts/generate_dataset.py --config configs/generation.yml")
        raise typer.Exit(code=1)
    export_report_bundle([], output)
    typer.echo(f"Pipeline squelette execute. Exports vides generes dans {output}")


@app.command()
def export(output: Path = Path("output")) -> None:
    export_report_bundle([], output)
    typer.echo(f"Exports vides generes dans {output}")


@app.command()
def reset() -> None:
    typer.echo("Reset Neo4j a coder dans src/conflict_detector/graph/schema.py")
