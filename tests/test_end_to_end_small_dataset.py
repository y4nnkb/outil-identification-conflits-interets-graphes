import pandas as pd

from conflict_detector.cleaning.pipeline import clean_tables
from conflict_detector.generation.config import GenerationConfig, resolve_scenario_counts
from conflict_detector.generation.factory import DatasetFactory
from conflict_detector.generation.noise import NoiseInjector
from conflict_detector.generation.scenario_injector import ScenarioInjector


def test_end_to_end_generates_injects_noise_and_cleans_small_dataset() -> None:
    config = GenerationConfig.model_validate(
        {
            "seed": 7,
            "output_dir": "data/generated",
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "volumes": {"employes": 12, "fournisseurs": 12, "transactions": 30},
            "amounts": {"min": 100, "max": 10000, "ghost_invoice_max": 2500},
            "scenario_mix": {
                "direct_link": {"percent": 0, "count": 1},
                "identity_match": {"percent": 0, "count": 1},
            },
            "noise": {"duplicate_rate_percent": 0, "missing_value_rate_percent": 1, "typo_rate_percent": 1},
        }
    )

    tables = DatasetFactory(config).generate()
    counts = resolve_scenario_counts(config, config.volumes.transactions)
    ScenarioInjector(config).inject(tables, counts)
    noise_summary = NoiseInjector(config).inject(tables)
    cleaned = clean_tables({name: pd.DataFrame(rows) for name, rows in tables.items()})

    assert set(cleaned) >= {"employes", "fournisseurs", "transactions", "scenario_labels"}
    assert len(cleaned["employes"]) == config.volumes.employes
    assert len(cleaned["fournisseurs"]) == config.volumes.fournisseurs
    assert len(cleaned["transactions"]) == config.volumes.transactions
    assert len(cleaned["scenario_labels"]) == 2
    assert {"email_norm", "telephone_norm", "adresse_norm", "iban_norm"} <= set(cleaned["employes"].columns)
    assert {"email_norm", "telephone_norm", "adresse_norm", "iban_norm", "siren_norm"} <= set(cleaned["fournisseurs"].columns)
    assert noise_summary["duplicates_added"] == 0
