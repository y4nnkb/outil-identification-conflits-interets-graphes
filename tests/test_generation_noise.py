from conflict_detector.generation.config import GenerationConfig
from conflict_detector.generation.noise import NoiseInjector


def test_noise_injector_adds_duplicates_missing_values_and_typos() -> None:
    config = GenerationConfig.model_validate(
        {
            "seed": 1,
            "output_dir": "data/generated",
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "volumes": {"employes": 1, "fournisseurs": 1, "transactions": 1},
            "amounts": {"min": 1, "max": 10, "ghost_invoice_max": 5},
            "scenario_mix": {"direct_link": {"percent": 0, "count": 0}},
            "noise": {"duplicate_rate_percent": 100, "missing_value_rate_percent": 100, "typo_rate_percent": 100},
        }
    )
    tables = {
        "employes": [{"id_employe": "EMP001", "email": "a@example.com", "telephone": "0612345678"}],
        "fournisseurs": [{"id_fournisseur": "FOU001", "email": "b@example.com", "siren": "123456789"}],
        "transactions": [{"id_transaction": "TRX001", "description": "Conseil", "montant": 100}],
        "scenario_labels": [{"scenario_id": "direct_link", "entity_ids": "EMP001|FOU001"}],
    }

    summary = NoiseInjector(config).inject(tables)

    assert summary["duplicates_added"] == 3
    assert summary["missing_values_added"] > 0
    assert summary["typos_added"] >= 0
    assert len(tables["scenario_labels"]) == 1
    assert tables["employes"][0]["id_employe"] == "EMP001"
