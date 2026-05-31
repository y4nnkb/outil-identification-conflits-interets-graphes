from random import Random

from conflict_detector.generation.config import GenerationConfig


NOISE_COLUMNS = {
    "employes": ["email", "telephone", "adresse", "iban", "nom"],
    "fournisseurs": ["email", "telephone", "adresse", "iban", "siren", "nom", "nom_dirigeant", "beneficiaire_effectif"],
    "transactions": ["description", "mode_paiement", "numero_facture"],
}

DUPLICABLE_TABLES = ("employes", "fournisseurs", "transactions")


class NoiseInjector:
    def __init__(self, config: GenerationConfig) -> None:
        self.config = config
        self.random = Random(config.seed + 10_000)

    def inject(self, tables: dict[str, list[dict]]) -> dict[str, int]:
        summary = {
            "duplicates_added": self._inject_duplicates(tables),
            "missing_values_added": self._inject_missing_values(tables),
            "typos_added": self._inject_typos(tables),
        }
        return summary

    def _inject_duplicates(self, tables: dict[str, list[dict]]) -> int:
        total = 0
        for table_name in DUPLICABLE_TABLES:
            rows = tables.get(table_name, [])
            count = self._count(rows, self.config.noise.duplicate_rate_percent)
            for row in self.random.sample(rows, min(count, len(rows))):
                rows.append(dict(row))
                total += 1
        return total

    def _inject_missing_values(self, tables: dict[str, list[dict]]) -> int:
        return self._apply_cell_noise(tables, self.config.noise.missing_value_rate_percent, lambda _: "")

    def _inject_typos(self, tables: dict[str, list[dict]]) -> int:
        return self._apply_cell_noise(tables, self.config.noise.typo_rate_percent, self._corrupt_value)

    def _apply_cell_noise(self, tables: dict[str, list[dict]], percent: float, transform) -> int:
        cells = self._candidate_cells(tables)
        count = min(self._count(cells, percent), len(cells))
        total = 0
        for table_name, row_index, column in self.random.sample(cells, count):
            row = tables[table_name][row_index]
            value = row.get(column)
            if value is None or str(value).strip() == "":
                continue
            row[column] = transform(value)
            total += 1
        return total

    def _candidate_cells(self, tables: dict[str, list[dict]]) -> list[tuple[str, int, str]]:
        cells = []
        for table_name, columns in NOISE_COLUMNS.items():
            for row_index, row in enumerate(tables.get(table_name, [])):
                for column in columns:
                    if column in row:
                        cells.append((table_name, row_index, column))
        return cells

    def _corrupt_value(self, value: object) -> str:
        text = str(value)
        if len(text) < 2:
            return f"{text}#"
        index = self.random.randrange(len(text))
        return f"{text[:index]}#{text[index + 1:]}"

    def _count(self, rows: list | tuple, percent: float) -> int:
        return round(len(rows) * percent / 100)
