from pathlib import Path

import typer

from conflict_detector.cleaning.pipeline import clean_tables
from conflict_detector.detection.cypher_rules import detection_result_to_dict, run_default_rules
from conflict_detector.evaluation import evaluate_alert_file
from conflict_detector.graph.connection import check_connection, get_driver
from conflict_detector.graph.loader import load_full_graph
from conflict_detector.graph.schema import clear_graph, create_schema
from conflict_detector.io.csv_reader import read_input_tables
from conflict_detector.reporting.exporters import export_report_bundle
from conflict_detector.scoring.scorer import score_alerts
from conflict_detector.generation.config import GenerationConfig, resolve_scenario_counts
from conflict_detector.generation.factory import DatasetFactory
from conflict_detector.generation.noise import NoiseInjector
from conflict_detector.generation.scenario_injector import ScenarioInjector
from conflict_detector.generation.writer import build_manifest, write_dataset, write_manifest
from conflict_detector.settings import load_generation_config, load_scoring_config

app = typer.Typer()


@app.command("check-neo4j")
def check_neo4j(env_file: Path = Path(".env")) -> None:
    driver = None
    try:
        driver = get_driver(env_file=env_file)
        result = check_connection(driver)
    except Exception as error:
        typer.echo(f"Connexion Neo4j impossible: {error}", err=True)
        raise typer.Exit(code=1) from error
    finally:
        if driver is not None:
            driver.close()
    typer.echo(f"Connexion Neo4j OK: RETURN 1 = {result}")


@app.command("create-schema")
def create_neo4j_schema(env_file: Path = Path(".env")) -> None:
    driver = None
    try:
        driver = get_driver(env_file=env_file)
        create_schema(driver)
    except Exception as error:
        typer.echo(f"Creation du schema Neo4j impossible: {error}", err=True)
        raise typer.Exit(code=1) from error
    finally:
        if driver is not None:
            driver.close()
    typer.echo("Schema Neo4j cree ou deja existant")


@app.command()
def generate(config: Path = Path("configs/generation.yml")) -> None:
    raw = load_generation_config(config)
    generation_config = GenerationConfig.model_validate(raw)
    tables = DatasetFactory(generation_config).generate()
    counts = resolve_scenario_counts(generation_config, generation_config.volumes.transactions)
    ScenarioInjector(generation_config).inject(tables, counts)
    noise_summary = NoiseInjector(generation_config).inject(tables)
    write_dataset(tables, generation_config.output_dir)
    write_manifest(build_manifest(generation_config, tables, counts, noise_summary), generation_config.output_dir)
    typer.echo(f"Dataset genere dans {generation_config.output_dir}")


@app.command()
def load(data: Path = Path("data/generated"), reset: bool = False, env_file: Path = Path(".env")) -> None:
    if not data.exists():
        raise typer.BadParameter(f"Dossier introuvable: {data}")
    driver = None
    try:
        tables = clean_tables(read_input_tables(data))
        driver = get_driver(env_file=env_file)
        load_full_graph(driver, tables, reset=reset)
    except Exception as error:
        typer.echo(f"Chargement Neo4j impossible: {error}", err=True)
        raise typer.Exit(code=1) from error
    finally:
        if driver is not None:
            driver.close()
    typer.echo(f"Noeuds charges dans Neo4j depuis {data}")


@app.command()
def detect(
    output: Path = Path("output"),
    env_file: Path = Path(".env"),
    scoring_config: Path = Path("configs/scoring.yml"),
) -> None:
    driver = None
    try:
        driver = get_driver(env_file=env_file)
        config = load_scoring_config(scoring_config)
        alerts = [detection_result_to_dict(result) for result in run_default_rules(driver)]
        alerts = score_alerts(alerts, config)
        export_report_bundle(alerts, output, config)
    except Exception as error:
        typer.echo(f"Detection impossible: {error}", err=True)
        raise typer.Exit(code=1) from error
    finally:
        if driver is not None:
            driver.close()
    typer.echo(f"{len(alerts)} alertes exportees dans {output}")


@app.command()
def run(
    data: Path = Path("data/generated"),
    output: Path = Path("output"),
    reset: bool = False,
    env_file: Path = Path(".env"),
    scoring_config: Path = Path("configs/scoring.yml"),
) -> None:
    if not data.exists():
        typer.echo(f"Dossier data absent: {data}")
        typer.echo("Lance d'abord: python scripts/generate_dataset.py --config configs/generation.yml")
        raise typer.Exit(code=1)
    driver = None
    try:
        tables = clean_tables(read_input_tables(data))
        driver = get_driver(env_file=env_file)
        load_full_graph(driver, tables, reset=reset)
        config = load_scoring_config(scoring_config)
        alerts = [detection_result_to_dict(result) for result in run_default_rules(driver)]
        alerts = score_alerts(alerts, config)
        export_report_bundle(alerts, output, config)
    except Exception as error:
        typer.echo(f"Pipeline impossible: {error}", err=True)
        raise typer.Exit(code=1) from error
    finally:
        if driver is not None:
            driver.close()

    labels_file = data / "scenario_labels.csv"
    if labels_file.exists():
        evaluate_alert_file(output / "alerts.json", labels_file, output / "evaluation.json")
    typer.echo(f"Pipeline execute. {len(alerts)} alertes exportees dans {output}")


@app.command()
def export(output: Path = Path("output")) -> None:
    export_report_bundle([], output)
    typer.echo(f"Exports vides generes dans {output}")


@app.command()
def evaluate(
    alerts_file: Path = Path("output/alerts.json"),
    labels_file: Path = Path("data/generated/scenario_labels.csv"),
    output_file: Path = Path("output/evaluation.json"),
) -> None:
    if not alerts_file.exists():
        raise typer.BadParameter(f"Fichier d'alertes introuvable: {alerts_file}")
    if not labels_file.exists():
        raise typer.BadParameter(f"Fichier scenario_labels introuvable: {labels_file}")
    result = evaluate_alert_file(alerts_file, labels_file, output_file)
    typer.echo(
        f"Evaluation exportee dans {output_file} "
        f"(recall={result['recall_estimate']}, precision={result['precision_estimate']}, f1={result['f1_score']})"
    )


@app.command()
def reset(env_file: Path = Path(".env")) -> None:
    driver = None
    try:
        driver = get_driver(env_file=env_file)
        clear_graph(driver)
    except Exception as error:
        typer.echo(f"Reset Neo4j impossible: {error}", err=True)
        raise typer.Exit(code=1) from error
    finally:
        if driver is not None:
            driver.close()
    typer.echo("Graphe Neo4j vide")
