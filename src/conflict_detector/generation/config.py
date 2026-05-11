from pydantic import BaseModel


class DateRangeConfig(BaseModel):
    start: str
    end: str


class VolumeConfig(BaseModel):
    employes: int
    fournisseurs: int
    transactions: int


class AmountConfig(BaseModel):
    min: float
    max: float
    ghost_invoice_max: float


class ScenarioMixItem(BaseModel):
    percent: float = 0
    count: int | None = None


class NoiseConfig(BaseModel):
    duplicate_rate_percent: float = 0
    missing_value_rate_percent: float = 0
    typo_rate_percent: float = 0


class GenerationConfig(BaseModel):
    seed: int
    output_dir: str
    date_range: DateRangeConfig
    volumes: VolumeConfig
    amounts: AmountConfig
    scenario_mix: dict[str, ScenarioMixItem]
    noise: NoiseConfig


def resolve_scenario_counts(config: GenerationConfig, base_total: int) -> dict[str, int]:
    result: dict[str, int] = {}
    for scenario_id, item in config.scenario_mix.items():
        result[scenario_id] = item.count if item.count is not None else int(base_total * item.percent / 100)
    return result
