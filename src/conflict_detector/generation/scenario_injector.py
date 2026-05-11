from datetime import date, timedelta
from random import Random

from faker import Faker

from conflict_detector.domain.enums import ScenarioId
from conflict_detector.generation.config import GenerationConfig


class ScenarioInjector:
    def __init__(self, config: GenerationConfig) -> None:
        self.config = config
        self.index = 0
        self.transaction_index = 0
        self.random = Random(config.seed)
        self.fake = Faker("fr_FR")
        self.fake.seed_instance(config.seed)

    def inject(self, tables: dict[str, list[dict]], scenario_counts: dict[str, int]) -> dict[str, list[dict]]:
        self._sort_transactions(tables)
        for scenario_id, count in scenario_counts.items():
            for _ in range(count):
                self.inject_one(tables, ScenarioId(scenario_id))
        self._sort_transactions(tables)
        return tables

    def inject_one(self, tables: dict[str, list[dict]], scenario_id: ScenarioId) -> None:
        handlers = {
            ScenarioId.DIRECT_LINK: self.inject_direct_link,
            ScenarioId.IDENTITY_MATCH: self.inject_identity_match,
            ScenarioId.GHOST_SUPPLIER: self.inject_ghost_supplier,
            ScenarioId.SHELL_ENTITY: self.inject_shell_entity,
            ScenarioId.BRIBES_GIFTS: self.inject_bribes_gifts,
            ScenarioId.MULTIPLE_HIDDEN_LINKS: self.inject_multiple_hidden_links,
            ScenarioId.INTERNAL_NETWORK: self.inject_internal_network,
            ScenarioId.STAR_PATTERN: self.inject_star_pattern,
            ScenarioId.CIRCULAR_NETWORK: self.inject_circular_network,
            ScenarioId.FINANCIAL_CONCENTRATION: self.inject_financial_concentration,
            ScenarioId.DOUBLE_MATCH: self.inject_double_match,
        }
        handlers[scenario_id](tables)

    def inject_direct_link(self, tables: dict[str, list[dict]]) -> None:
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        self._set_address(fournisseur, employe["adresse"])
        self._tag(tables, ScenarioId.DIRECT_LINK, employe["id_employe"], fournisseur["id_fournisseur"])

    def inject_identity_match(self, tables: dict[str, list[dict]]) -> None:
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        fournisseur["email"] = employe["email"]
        fournisseur["telephone"] = employe["telephone"]
        self._tag(tables, ScenarioId.IDENTITY_MATCH, employe["id_employe"], fournisseur["id_fournisseur"])

    def inject_ghost_supplier(self, tables: dict[str, list[dict]]) -> None:
        fournisseur = self._row(tables["fournisseurs"])
        fournisseur["is_boite_postale"] = "true"
        fournisseur["adresse"] = f"BP {1000 + self.index}, {self.fake.city()}"
        for transaction in self._transaction_rows(tables, 3):
            transaction["id_fournisseur"] = fournisseur["id_fournisseur"]
            transaction["montant"] = min(float(transaction["montant"]), 2400.0)
            transaction["description"] = "Services divers"
        self._tag(tables, ScenarioId.GHOST_SUPPLIER, fournisseur["id_fournisseur"])

    def inject_shell_entity(self, tables: dict[str, list[dict]]) -> None:
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        transaction = self._transaction_row(tables)
        fournisseur["is_societe_ecran"] = "true"
        fournisseur["beneficiaire_effectif"] = f"{employe['prenom']} {employe['nom']}"
        transaction["id_employe"] = employe["id_employe"]
        transaction["id_fournisseur"] = fournisseur["id_fournisseur"]
        transaction["montant"] = 95000
        self._tag(tables, ScenarioId.SHELL_ENTITY, employe["id_employe"], fournisseur["id_fournisseur"], transaction["id_transaction"])

    def inject_bribes_gifts(self, tables: dict[str, list[dict]]) -> None:
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        transaction = self._transaction_row(tables)
        transaction["id_employe"] = employe["id_employe"]
        transaction["id_fournisseur"] = fournisseur["id_fournisseur"]
        transaction["cadeau_ou_avantage"] = "true"
        transaction["date_cadeau"] = self._date_before(transaction["date_validation"])
        transaction["montant_cadeau"] = 2500
        self._tag(tables, ScenarioId.BRIBES_GIFTS, employe["id_employe"], fournisseur["id_fournisseur"], transaction["id_transaction"])

    def inject_multiple_hidden_links(self, tables: dict[str, list[dict]]) -> None:
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        self._set_address(fournisseur, employe["adresse"])
        fournisseur["iban"] = employe["iban"]
        fournisseur["nom_dirigeant"] = employe["nom"]
        self._tag(tables, ScenarioId.MULTIPLE_HIDDEN_LINKS, employe["id_employe"], fournisseur["id_fournisseur"])

    def inject_internal_network(self, tables: dict[str, list[dict]]) -> None:
        adresse = f"Adresse Reseau {self.index}, Paris"
        employes = self._rows(tables["employes"], 2)
        fournisseurs = self._rows(tables["fournisseurs"], 2)
        for row in employes + fournisseurs:
            self._set_address(row, adresse)
        for transaction in self._transaction_rows(tables, 4):
            transaction["id_employe"] = employes[self.index % 2]["id_employe"]
            transaction["id_fournisseur"] = fournisseurs[self.index % 2]["id_fournisseur"]
        self._tag(tables, ScenarioId.INTERNAL_NETWORK, *(row.get("id_employe") or row.get("id_fournisseur") for row in employes + fournisseurs))

    def inject_star_pattern(self, tables: dict[str, list[dict]]) -> None:
        employe = self._row(tables["employes"])
        fournisseurs = self._rows(tables["fournisseurs"], 4)
        for fournisseur in fournisseurs:
            self._set_address(fournisseur, employe["adresse"])
            fournisseur["nom_dirigeant"] = employe["nom"]
        self._tag(tables, ScenarioId.STAR_PATTERN, employe["id_employe"], *(fournisseur["id_fournisseur"] for fournisseur in fournisseurs))

    def inject_circular_network(self, tables: dict[str, list[dict]]) -> None:
        a, b, c = self._rows(tables["fournisseurs"], 3)
        self._set_address(b, a["adresse"])
        c["telephone"] = b["telephone"]
        a["iban"] = c["iban"]
        self._tag(tables, ScenarioId.CIRCULAR_NETWORK, a["id_fournisseur"], b["id_fournisseur"], c["id_fournisseur"])

    def inject_financial_concentration(self, tables: dict[str, list[dict]]) -> None:
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        for transaction in self._transaction_rows(tables, 8):
            transaction["id_employe"] = employe["id_employe"]
            transaction["id_fournisseur"] = fournisseur["id_fournisseur"]
            transaction["montant"] = 75000
        self._tag(tables, ScenarioId.FINANCIAL_CONCENTRATION, employe["id_employe"], fournisseur["id_fournisseur"])

    def inject_double_match(self, tables: dict[str, list[dict]]) -> None:
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        self._set_address(fournisseur, employe["adresse"])
        fournisseur["telephone"] = employe["telephone"]
        self._tag(tables, ScenarioId.DOUBLE_MATCH, employe["id_employe"], fournisseur["id_fournisseur"])

    def _row(self, rows: list[dict]) -> dict:
        row = rows[self.index % len(rows)]
        self.index += 1
        return row

    def _rows(self, rows: list[dict], count: int) -> list[dict]:
        return [self._row(rows) for _ in range(count)]

    def _transaction_row(self, tables: dict[str, list[dict]]) -> dict:
        return self._transaction_rows(tables, 1)[0]

    def _transaction_rows(self, tables: dict[str, list[dict]], count: int) -> list[dict]:
        transactions = tables["transactions"]
        max_start = max(1, len(transactions) - count + 1)
        start = self.transaction_index % max_start
        self.transaction_index += count
        return transactions[start : start + count]

    def _sort_transactions(self, tables: dict[str, list[dict]]) -> None:
        tables["transactions"].sort(key=lambda transaction: (transaction["date_transaction"], transaction["id_transaction"]))

    def _date_before(self, reference: str, max_days: int = 30) -> str:
        reference_date = date.fromisoformat(str(reference))
        start_date = date.fromisoformat(self.config.date_range.start)
        latest_date = reference_date - timedelta(days=1)
        if latest_date < start_date:
            return str(start_date)
        earliest_date = max(start_date, reference_date - timedelta(days=max_days))
        return str(earliest_date + timedelta(days=self.random.randint(0, (latest_date - earliest_date).days)))

    def _set_address(self, row: dict, address: str) -> None:
        if row.get("is_boite_postale") == "true":
            return
        row["adresse"] = address

    def _tag(self, tables: dict[str, list[dict]], scenario_id: ScenarioId, *entity_ids: str) -> None:
        tables.setdefault("scenario_labels", []).append(
            {"scenario_id": scenario_id.value, "entity_ids": "|".join(entity_ids)}
        )
