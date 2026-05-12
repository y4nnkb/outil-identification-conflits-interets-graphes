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
    gift_min: float = 100
    gift_max: float = 5000


class ScenarioMixItem(BaseModel):
    percent: float = 0
    count: int | None = None


class NoiseConfig(BaseModel):
    duplicate_rate_percent: float = 0
    missing_value_rate_percent: float = 0
    typo_rate_percent: float = 0


class ScenarioParametersConfig(BaseModel):
    star_supplier_min: int = 3
    star_supplier_max: int = 7
    star_transactions_per_supplier_min: int = 1
    star_transactions_per_supplier_max: int = 2
    circular_member_min: int = 3
    circular_member_max: int = 5
    internal_employee_min: int = 2
    internal_employee_max: int = 4
    internal_supplier_min: int = 2
    internal_supplier_max: int = 4
    internal_transaction_min: int = 4
    internal_transaction_max: int = 10
    shell_transaction_min: int = 2
    shell_transaction_max: int = 5
    shell_transaction_min_amount: float = 80000
    shell_transaction_max_amount: float = 180000
    bribe_days_before_transaction_min: int = 1
    bribe_days_before_transaction_max: int = 30
    hidden_link_min_attributes: int = 3
    hidden_link_max_attributes: int = 4
    hidden_link_attributes: list[str] = ["adresse", "email", "telephone", "iban", "nom"]
    financial_concentration_min_amount: float = 50000
    financial_concentration_max_amount: float = 120000
    double_match_attributes: list[str] = ["adresse", "email", "telephone", "iban", "nom"]


class GenerationConfig(BaseModel):
    seed: int
    output_dir: str
    date_range: DateRangeConfig
    volumes: VolumeConfig
    amounts: AmountConfig
    scenario_parameters: ScenarioParametersConfig = ScenarioParametersConfig()
    scenario_mix: dict[str, ScenarioMixItem]
    noise: NoiseConfig


def resolve_scenario_counts(config: GenerationConfig, base_total: int) -> dict[str, int]:
    result: dict[str, int] = {}
    for scenario_id, item in config.scenario_mix.items():
        result[scenario_id] = item.count if item.count is not None else int(base_total * item.percent / 100)
    return result
