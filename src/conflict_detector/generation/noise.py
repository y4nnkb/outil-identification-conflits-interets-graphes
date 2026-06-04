from random import Random

from conflict_detector.generation.config import GenerationConfig


NOISE_COLUMNS = {
    "employes": ["email", "telephone", "adresse", "iban", "nom"],
    "fournisseurs": ["email", "telephone", "adresse", "iban", "siren", "nom", "nom_dirigeant", "beneficiaire_effectif"],
    "transactions": ["description", "mode_paiement", "numero_facture"],
}

DUPLICABLE_TABLES = ("employes", "fournisseurs", "transactions")

SCENARIO_PROTECTED_ATTRIBUTES = {
    "direct_link": ["adresse"],
    "identity_match": ["email", "telephone"],
    "internal_network": ["adresse"],
    "star_pattern": ["adresse"],
    "circular_network": ["adresse", "telephone", "iban"],
    "shell_entity": ["nom", "beneficiaire_effectif"],
    "ghost_supplier": ["adresse"],
}

ATTRIBUTE_COLUMNS = {
    "employes": {
        "adresse": ["adresse"],
        "email": ["email"],
        "telephone": ["telephone"],
        "iban": ["iban"],
        "nom": ["nom"],
    },
    "fournisseurs": {
        "adresse": ["adresse"],
        "email": ["email"],
        "telephone": ["telephone"],
        "iban": ["iban"],
        "siren": ["siren"],
        "nom": ["nom_dirigeant"],
        "beneficiaire_effectif": ["beneficiaire_effectif"],
    },
}


class NoiseInjector:
    def __init__(self, config: GenerationConfig) -> None:
        self.config = config
        self.random = Random(config.seed + 10_000)

    def inject(self, tables: dict[str, list[dict]]) -> dict[str, int]:
        protected_cells = self._protected_cells(tables)
        summary = {
            "duplicates_added": self._inject_duplicates(tables, protected_cells),
            "missing_values_added": self._inject_missing_values(tables, protected_cells),
            "typos_added": self._inject_typos(tables, protected_cells),
        }
        return summary

    def _inject_duplicates(self, tables: dict[str, list[dict]], protected_cells: set[tuple[str, int, str]]) -> int:
        total = 0
        for table_name in DUPLICABLE_TABLES:
            rows = tables.get(table_name, [])
            count = self._count(rows, self.config.noise.duplicate_rate_percent)
            candidates = [
                row
                for index, row in enumerate(rows)
                if not self._row_has_protected_cell(table_name, index, protected_cells)
            ]
            for row in self.random.sample(candidates, min(count, len(candidates))):
                rows.append(dict(row))
                total += 1
        return total

    def _inject_missing_values(self, tables: dict[str, list[dict]], protected_cells: set[tuple[str, int, str]]) -> int:
        return self._apply_cell_noise(tables, self.config.noise.missing_value_rate_percent, protected_cells, lambda _: "")

    def _inject_typos(self, tables: dict[str, list[dict]], protected_cells: set[tuple[str, int, str]]) -> int:
        return self._apply_cell_noise(tables, self.config.noise.typo_rate_percent, protected_cells, self._corrupt_value)

    def _apply_cell_noise(self, tables: dict[str, list[dict]], percent: float, protected_cells: set[tuple[str, int, str]], transform) -> int:
        cells = self._candidate_cells(tables, protected_cells)
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

    def _candidate_cells(self, tables: dict[str, list[dict]], protected_cells: set[tuple[str, int, str]]) -> list[tuple[str, int, str]]:
        cells = []
        for table_name, columns in NOISE_COLUMNS.items():
            for row_index, row in enumerate(tables.get(table_name, [])):
                for column in columns:
                    if column in row and (table_name, row_index, column) not in protected_cells:
                        cells.append((table_name, row_index, column))
        return cells

    def _protected_cells(self, tables: dict[str, list[dict]]) -> set[tuple[str, int, str]]:
        protected: set[tuple[str, int, str]] = set()
        row_indexes = {
            "employes": {row["id_employe"]: index for index, row in enumerate(tables.get("employes", []))},
            "fournisseurs": {row["id_fournisseur"]: index for index, row in enumerate(tables.get("fournisseurs", []))},
        }
        for label in tables.get("scenario_labels", []):
            scenario_id = str(label.get("scenario_id", ""))
            parts = str(label.get("entity_ids", "")).split("|")
            attributes = self._protected_attributes(scenario_id, parts)
            for entity_id in parts:
                table_name = self._entity_table(entity_id)
                if not table_name or entity_id not in row_indexes[table_name]:
                    continue
                row_index = row_indexes[table_name][entity_id]
                row = tables[table_name][row_index]
                for attribute in attributes:
                    for column in ATTRIBUTE_COLUMNS[table_name].get(attribute, []):
                        if column in row:
                            protected.add((table_name, row_index, column))
        return protected

    def _protected_attributes(self, scenario_id: str, parts: list[str]) -> list[str]:
        configured = SCENARIO_PROTECTED_ATTRIBUTES.get(scenario_id, [])
        labelled_attributes = [
            part
            for part in parts
            if not part.startswith(("EMP", "FOU", "TRX"))
        ]
        return list(dict.fromkeys(configured + labelled_attributes))

    def _entity_table(self, entity_id: str) -> str:
        if entity_id.startswith("EMP"):
            return "employes"
        if entity_id.startswith("FOU"):
            return "fournisseurs"
        return ""

    def _row_has_protected_cell(self, table_name: str, row_index: int, protected_cells: set[tuple[str, int, str]]) -> bool:
        return any(table == table_name and index == row_index for table, index, _ in protected_cells)

    def _corrupt_value(self, value: object) -> str:
        text = str(value)
        if len(text) < 2:
            return f"{text}#"
        index = self.random.randrange(len(text))
        return f"{text[:index]}#{text[index + 1:]}"

    def _count(self, rows: list | tuple, percent: float) -> int:
        return round(len(rows) * percent / 100)
