from datetime import date

from pydantic import BaseModel, Field, model_validator


class DateRangeConfig(BaseModel):
    start: str
    end: str

    @model_validator(mode="after")
    def validate_range(self) -> "DateRangeConfig":
        if date.fromisoformat(self.start) > date.fromisoformat(self.end):
            raise ValueError("date_range.start doit etre avant date_range.end")
        return self


class VolumeConfig(BaseModel):
    employes: int
    fournisseurs: int
    transactions: int

    @model_validator(mode="after")
    def validate_volumes(self) -> "VolumeConfig":
        if self.employes <= 0 or self.fournisseurs <= 0 or self.transactions <= 0:
            raise ValueError("les volumes doivent etre strictement positifs")
        return self


class AmountConfig(BaseModel):
    min: float
    max: float
    ghost_invoice_max: float
    gift_min: float = 100
    gift_max: float = 5000

    @model_validator(mode="after")
    def validate_amounts(self) -> "AmountConfig":
        if self.min > self.max:
            raise ValueError("amounts.min doit etre inferieur ou egal a amounts.max")
        if self.gift_min > self.gift_max:
            raise ValueError("amounts.gift_min doit etre inferieur ou egal a amounts.gift_max")
        if self.ghost_invoice_max < 0:
            raise ValueError("amounts.ghost_invoice_max doit etre positif")
        return self


class ScenarioMixItem(BaseModel):
    percent: float = 0
    count: int | None = None

    @model_validator(mode="after")
    def validate_mix_item(self) -> "ScenarioMixItem":
        if self.percent < 0:
            raise ValueError("scenario_mix.percent doit etre positif")
        if self.count is not None and self.count < 0:
            raise ValueError("scenario_mix.count doit etre positif")
        return self


class NoiseConfig(BaseModel):
    duplicate_rate_percent: float = 0
    missing_value_rate_percent: float = 0
    typo_rate_percent: float = 0

    @model_validator(mode="after")
    def validate_noise(self) -> "NoiseConfig":
        values = [self.duplicate_rate_percent, self.missing_value_rate_percent, self.typo_rate_percent]
        if any(value < 0 or value > 100 for value in values):
            raise ValueError("les taux de bruit doivent etre entre 0 et 100")
        return self


class TransactionParametersConfig(BaseModel):
    contract_ratio_percent: float = 20
    invoice_link_to_order_percent: float = 50
    validation_delay_min_days: int = 0
    validation_delay_max_days: int = 7
    payment_method_weights: dict[str, int] = {"VIREMENT": 80, "CARTE": 10, "PRELEVEMENT": 10}

    @model_validator(mode="after")
    def validate_transaction_parameters(self) -> "TransactionParametersConfig":
        if self.contract_ratio_percent < 0 or self.contract_ratio_percent > 100:
            raise ValueError("contract_ratio_percent doit etre entre 0 et 100")
        if self.invoice_link_to_order_percent < 0 or self.invoice_link_to_order_percent > 100:
            raise ValueError("invoice_link_to_order_percent doit etre entre 0 et 100")
        if self.validation_delay_min_days < 0 or self.validation_delay_min_days > self.validation_delay_max_days:
            raise ValueError("validation_delay_min_days doit etre positif et inferieur au maximum")
        if not self.payment_method_weights or any(weight < 0 for weight in self.payment_method_weights.values()):
            raise ValueError("payment_method_weights doit contenir des poids positifs")
        if sum(self.payment_method_weights.values()) <= 0:
            raise ValueError("la somme des poids de paiement doit etre strictement positive")
        return self


class ScenarioParametersConfig(BaseModel):
    star_supplier_min: int = 3
    star_supplier_max: int = 7
    star_transactions_per_supplier_min: int = 1
    star_transactions_per_supplier_max: int = 2
    ghost_transaction_count: int = 3
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
    bribe_days_before_transaction_min: int = 0
    bribe_days_before_transaction_max: int = 7
    hidden_link_min_attributes: int = 3
    hidden_link_max_attributes: int = 4
    hidden_link_attributes: list[str] = ["adresse", "email", "telephone", "iban", "nom"]
    financial_concentration_min_amount: float = 50000
    financial_concentration_max_amount: float = 120000
    double_match_attributes: list[str] = ["adresse", "email", "telephone", "iban", "nom"]

    @model_validator(mode="after")
    def validate_scenario_parameters(self) -> "ScenarioParametersConfig":
        allowed_attributes = {"adresse", "email", "telephone", "iban", "nom"}
        ranges = [
            (self.star_supplier_min, self.star_supplier_max),
            (self.star_transactions_per_supplier_min, self.star_transactions_per_supplier_max),
            (self.circular_member_min, self.circular_member_max),
            (self.internal_employee_min, self.internal_employee_max),
            (self.internal_supplier_min, self.internal_supplier_max),
            (self.internal_transaction_min, self.internal_transaction_max),
            (self.shell_transaction_min, self.shell_transaction_max),
            (self.shell_transaction_min_amount, self.shell_transaction_max_amount),
            (self.bribe_days_before_transaction_min, self.bribe_days_before_transaction_max),
            (self.hidden_link_min_attributes, self.hidden_link_max_attributes),
            (self.financial_concentration_min_amount, self.financial_concentration_max_amount),
        ]
        if any(min_value < 0 or min_value > max_value for min_value, max_value in ranges):
            raise ValueError("les bornes des scenario_parameters sont incoherentes")
        if self.ghost_transaction_count <= 0:
            raise ValueError("ghost_transaction_count doit etre strictement positif")
        if set(self.hidden_link_attributes) - allowed_attributes:
            raise ValueError("hidden_link_attributes contient un attribut inconnu")
        if set(self.double_match_attributes) - allowed_attributes:
            raise ValueError("double_match_attributes contient un attribut inconnu")
        if len(self.double_match_attributes) < 2:
            raise ValueError("double_match_attributes doit contenir au moins deux attributs")
        return self


class GenerationConfig(BaseModel):
    seed: int
    output_dir: str
    date_range: DateRangeConfig
    volumes: VolumeConfig
    amounts: AmountConfig
    transaction_parameters: TransactionParametersConfig = Field(default_factory=TransactionParametersConfig)
    scenario_parameters: ScenarioParametersConfig = Field(default_factory=ScenarioParametersConfig)
    scenario_mix: dict[str, ScenarioMixItem]
    noise: NoiseConfig
    team_size_min: int = 4
    team_size_max: int = 6
    responsable_garde_equipe: bool = False

    @model_validator(mode="after")
    def validate_team_size(self) -> "GenerationConfig":
        if self.team_size_min < 1:
            raise ValueError("team_size_min doit etre >= 1")
        if self.team_size_min > self.team_size_max:
            raise ValueError("team_size_min doit etre inferieur ou egal a team_size_max")
        return self


def resolve_scenario_counts(config: GenerationConfig, base_total: int) -> dict[str, int]:
    result: dict[str, int] = {}
    for scenario_id, item in config.scenario_mix.items():
        result[scenario_id] = item.count if item.count is not None else int(base_total * item.percent / 100)
    return result
