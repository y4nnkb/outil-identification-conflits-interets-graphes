from conflict_detector.generation.config import GenerationConfig, resolve_scenario_counts


def test_resolve_scenario_counts_prefers_count() -> None:
    config = GenerationConfig.model_validate(
        {
            "seed": 1,
            "output_dir": "data/generated",
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "volumes": {"employes": 1, "fournisseurs": 1, "transactions": 100},
            "amounts": {"min": 1, "max": 10, "ghost_invoice_max": 5},
            "scenario_mix": {"direct_link": {"percent": 5, "count": 9}},
            "noise": {"duplicate_rate_percent": 0, "missing_value_rate_percent": 0, "typo_rate_percent": 0},
        }
    )
    assert resolve_scenario_counts(config, 100)["direct_link"] == 9
