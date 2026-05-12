from itertools import combinations
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
        self.double_match_pair_index = 0
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
        """Ce scénario simule un lien direct entre un employé et un fournisseur, ce qui peut indiquer une relation de collusion ou de favoritisme. L'employé et le fournisseur partagent la même adresse, ce qui est un indicateur fort de lien direct.
        Entreé : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec un employé et un fournisseur modifiés pour partager la même adresse, et une étiquette de scénario ajoutée pour indiquer le scénario de lien direct"""
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        self._set_address(fournisseur, employe["adresse"]) #Pour l'instant, on considère que l'adresse est un lien plus fort que le téléphone ou l'email, mais on pourrait aussi les faire correspondre
        self._tag(tables, ScenarioId.DIRECT_LINK, employe["id_employe"], fournisseur["id_fournisseur"])

    def inject_identity_match(self, tables: dict[str, list[dict]]) -> None:
        """Similaire au scénario Direct Link, mais avec des liens plus faibles (email et téléphone) pour tester la capacité du modèle à détecter des correspondances d'identité moins évidentes
        Entrée : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec un employé et un fournisseur modifiés pour partager le même email et téléphone, et une étiquette de scénario ajoutée pour indiquer le scénario de correspondance d'identité"""
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        fournisseur["email"] = employe["email"]
        fournisseur["telephone"] = employe["telephone"]
        self._tag(tables, ScenarioId.IDENTITY_MATCH, employe["id_employe"], fournisseur["id_fournisseur"])

    def inject_ghost_supplier(self, tables: dict[str, list[dict]]) -> None:
        """Ce scénario simule l'existence d'un fournisseur fictif (ghost supplier) qui n'a pas d'activité réelle mais qui est utilisé pour émettre des factures frauduleuses. Le fournisseur est créé avec une adresse de boîte postale et des transactions associées qui ont des montants élevés, ce qui peut être un indicateur de fraude.
        Entrée : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec un fournisseur modifié pour être une boîte postale, des transactions associées avec des montants élevés, et une étiquette de scénario ajoutée pour indiquer le scénario de fournisseur fantôme"""
        fournisseur = self._row(tables["fournisseurs"])
        fournisseur["is_boite_postale"] = "true"
        fournisseur["adresse"] = f"BP {1000 + self.index}, {self.fake.city()}"
        for transaction in self._transaction_rows(tables, 3):
            transaction["id_fournisseur"] = fournisseur["id_fournisseur"]
            transaction["montant"] = min(float(transaction["montant"]), self.config.amounts.ghost_invoice_max)
            transaction["description"] = "Services divers"
        self._tag(tables, ScenarioId.GHOST_SUPPLIER, fournisseur["id_fournisseur"])

    def inject_shell_entity(self, tables: dict[str, list[dict]]) -> None:
        """Ce scénario simule l'existence d'une entité écran (shell entity) qui est utilisée pour masquer l'identité réelle d'un fournisseur ou d'un employé. L'entité écran est créée avec des informations de bénéficiaire effectif qui correspondent à un employé réel, et des transactions associées avec des montants élevés, ce qui peut être un indicateur de fraude.
        Entrée : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec un fournisseur modifié pour être une entité écran avec des informations de bénéficiaire effectif correspondant à un employé réel, des transactions associées avec des montants élevés, et une étiquette de scénario ajoutée pour indiquer le scénario d'entité écran"""
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        transaction_count = self.random.randint(
            self.config.scenario_parameters.shell_transaction_min,
            self.config.scenario_parameters.shell_transaction_max,
        )
        transactions = self._transaction_rows(tables, transaction_count)
        fournisseur["is_societe_ecran"] = "true"
        fournisseur["beneficiaire_effectif"] = f"{employe['prenom']} {employe['nom']}"
        for transaction in transactions:
            transaction["id_employe"] = employe["id_employe"]
            transaction["id_fournisseur"] = fournisseur["id_fournisseur"]
            transaction["montant"] = self._shell_transaction_amount()
        self._tag(
            tables,
            ScenarioId.SHELL_ENTITY,
            employe["id_employe"],
            fournisseur["id_fournisseur"],
            *(transaction["id_transaction"] for transaction in transactions),
        )

    def inject_bribes_gifts(self, tables: dict[str, list[dict]]) -> None:
        """Ce scénario simule des pots-de-vin ou des cadeaux offerts par un fournisseur à un employé en échange de faveurs ou de contrats. L'employé et le fournisseur sont liés par une transaction où le montant du cadeau est enregistré, ainsi que la date du cadeau qui est antérieure à la date de validation de la transaction, ce qui peut être un indicateur de corruption.
        Entrée : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec un employé et un fournisseur liés par une transaction modifiée pour inclure des informations sur un cadeau ou un pot-de"""
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        transaction = self._transaction_row(tables)
        transaction["id_employe"] = employe["id_employe"]
        transaction["id_fournisseur"] = fournisseur["id_fournisseur"]
        transaction["type_transaction"] = "CONTRAT"
        transaction["numero_facture"] = ""
        transaction["description"] = "Attribution contrat"
        transaction["cadeau_ou_avantage"] = "true"
        self._ensure_transaction_has_previous_days(
            transaction,
            self.config.scenario_parameters.bribe_days_before_transaction_min,
        )
        transaction["date_cadeau"] = self._date_before_window(
            transaction["date_transaction"],
            self.config.scenario_parameters.bribe_days_before_transaction_min,
            self.config.scenario_parameters.bribe_days_before_transaction_max,
        )
        transaction["montant_cadeau"] = self._gift_amount()
        self._tag(tables, ScenarioId.BRIBES_GIFTS, employe["id_employe"], fournisseur["id_fournisseur"], transaction["id_transaction"])

    def inject_multiple_hidden_links(self, tables: dict[str, list[dict]]) -> None:
        """Ce scénario simule une situation où un employé et un fournisseur sont liés par plusieurs liens cachés, tels que l'adresse, le numéro de téléphone ou l'IBAN. Ces liens peuvent être utilisés pour masquer une relation de collusion ou de favoritisme, et peuvent être plus difficiles à détecter que les liens directs.
        Entrée : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec un employé et un fournisseur modifiés pour partager plusieurs liens cachés (adresse, téléphone, IBAN), et une étiquette de scénario ajoutée pour indiquer le scénario de liens cachés multiples"""
        employe = self._row(tables["employes"])
        attributes = self._hidden_link_attributes()
        fournisseur = self._rows_without_boite_postale(tables["fournisseurs"], 1)[0] if "adresse" in attributes else self._row(tables["fournisseurs"])
        for attribute in attributes:
            self._share_attribute(employe, fournisseur, attribute)
        self._tag(tables, ScenarioId.MULTIPLE_HIDDEN_LINKS, employe["id_employe"], fournisseur["id_fournisseur"], *attributes)

    def inject_internal_network(self, tables: dict[str, list[dict]]) -> None:
        """Ce scénario simule un réseau interne d'employés et de fournisseurs qui sont tous liés par une adresse commune, ce qui peut indiquer une collusion ou un favoritisme à grande échelle. Plusieurs employés et fournisseurs partagent la même adresse, et des transactions associées entre eux, ce qui peut être un indicateur de réseau interne.
        Entrée : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec plusieurs employés et fournisseurs modifiés pour partager la même adresse, des transactions associées entre eux, et une étiquette de scénario ajoutée pour indiquer le scénario de réseau interne"""
        adresse = self.fake.address().replace("\n", ", ")
        employe_count = self.random.randint(self.config.scenario_parameters.internal_employee_min, self.config.scenario_parameters.internal_employee_max)
        fournisseur_count = self.random.randint(self.config.scenario_parameters.internal_supplier_min, self.config.scenario_parameters.internal_supplier_max)
        transaction_count = self.random.randint(self.config.scenario_parameters.internal_transaction_min, self.config.scenario_parameters.internal_transaction_max)
        employes = self._rows(tables["employes"], employe_count)
        fournisseurs = self._rows_without_boite_postale(tables["fournisseurs"], fournisseur_count)
        manager_id = self.random.choice(tables["employes"])["id_employe"]
        departement = self.random.choice(["Achats", "Finance", "Juridique", "Operations"])
        for row in employes + fournisseurs:
            self._set_address(row, adresse)
        for employe in employes:
            employe["manager_id"] = manager_id
            employe["departement"] = departement
        transactions = self._transaction_rows(tables, transaction_count)
        for index, transaction in enumerate(transactions):
            transaction["id_employe"] = employes[index % len(employes)]["id_employe"]
            transaction["id_fournisseur"] = fournisseurs[index % len(fournisseurs)]["id_fournisseur"]
        self._tag(
            tables,
            ScenarioId.INTERNAL_NETWORK,
            *(row.get("id_employe") or row.get("id_fournisseur") for row in employes + fournisseurs),
            *(transaction["id_transaction"] for transaction in transactions),
        )

    def inject_star_pattern(self, tables: dict[str, list[dict]]) -> None:
        """Ce scénario simule un schéma en étoile où un employé est lié à plusieurs fournisseurs par une adresse commune, ce qui peut indiquer une collusion ou un favoritisme centralisé. Un employé partage la même adresse avec plusieurs fournisseurs, et des transactions associées entre eux, ce qui peut être un indicateur de schéma en étoile.
        Entrée : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec un employé modifié pour partager la même adresse avec plusieurs fournisseurs, des transactions associées entre eux, et une étiquette de scénario ajoutée pour indiquer le scénario de schéma en étoile"""
        employe = self._row(tables["employes"])
        fournisseur_count = self.random.randint(
            self.config.scenario_parameters.star_supplier_min,
            self.config.scenario_parameters.star_supplier_max,
        )
        fournisseurs = self._rows(tables["fournisseurs"], fournisseur_count)
        transactions = []
        for fournisseur in fournisseurs:
            self._set_address(fournisseur, employe["adresse"])
            fournisseur["nom_dirigeant"] = employe["nom"]
            transaction_count = self.random.randint(
                self.config.scenario_parameters.star_transactions_per_supplier_min,
                self.config.scenario_parameters.star_transactions_per_supplier_max,
            )
            for transaction in self._transaction_rows(tables, transaction_count):
                transaction["id_employe"] = employe["id_employe"]
                transaction["id_fournisseur"] = fournisseur["id_fournisseur"]
                transactions.append(transaction)
        self._tag(
            tables,
            ScenarioId.STAR_PATTERN,
            employe["id_employe"],
            *(fournisseur["id_fournisseur"] for fournisseur in fournisseurs),
            *(transaction["id_transaction"] for transaction in transactions),
        )

    def inject_circular_network(self, tables: dict[str, list[dict]]) -> None:
        """Ce scénario simule un réseau circulaire où plusieurs employés et fournisseurs sont liés entre eux de manière circulaire, ce qui peut indiquer une collusion ou un favoritisme complexe. Trois entités (employés ou fournisseurs) sont liées entre elles de manière circulaire par des liens d'adresse, de téléphone et d'IBAN, ce qui peut être un indicateur de réseau circulaire.
        Entrée : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec trois entités (employés ou fournisseurs) modifiées pour être liées entre elles de manière circulaire par des liens d'adresse, de téléphone et d'IBAN, et une étiquette de scénario ajoutée pour"""
        member_count = self.random.randint(
            self.config.scenario_parameters.circular_member_min,
            self.config.scenario_parameters.circular_member_max,
        )
        fournisseurs = self._rows(tables["fournisseurs"], member_count)
        attributes = ["adresse", "telephone", "iban"]
        for index, fournisseur in enumerate(fournisseurs):
            next_fournisseur = fournisseurs[(index + 1) % len(fournisseurs)]
            attribute = attributes[index % len(attributes)]
            if attribute == "adresse":
                self._set_address(next_fournisseur, fournisseur["adresse"])
            else:
                next_fournisseur[attribute] = fournisseur[attribute]
        self._tag(tables, ScenarioId.CIRCULAR_NETWORK, *(fournisseur["id_fournisseur"] for fournisseur in fournisseurs))

    def inject_financial_concentration(self, tables: dict[str, list[dict]]) -> None:
        """Ce scénario simule une concentration financière où un employé effectue des transactions importantes avec un fournisseur spécifique, ce qui peut indiquer une relation de collusion ou de favoritisme. Un employé est lié à un fournisseur par plusieurs transactions avec des montants élevés, ce qui peut être un indicateur de concentration financière.
        Entrée : dictionnaire de tables avec des listes d'employés, de fournisseurs et de transactions
        Sortie : le même dictionnaire de tables, mais avec un employé et un fournisseur liés par plusieurs transactions modifiées pour avoir des montants élevés, et une étiquette de scénario ajoutée pour indiquer le scénario de concentration financière"""
        employe = self._row(tables["employes"])
        fournisseur = self._row(tables["fournisseurs"])
        transactions = self._transaction_rows(tables, 8)
        for transaction in transactions:
            transaction["id_employe"] = employe["id_employe"]
            transaction["id_fournisseur"] = fournisseur["id_fournisseur"]
            transaction["montant"] = self._financial_concentration_amount()
        self._tag(
            tables,
            ScenarioId.FINANCIAL_CONCENTRATION,
            employe["id_employe"],
            fournisseur["id_fournisseur"],
            *(transaction["id_transaction"] for transaction in transactions),
        )

    def inject_double_match(self, tables: dict[str, list[dict]]) -> None:
        """Ce scénario simule un double match où un employé et un fournisseur partagent les mêmes informations de contact, ce qui peut indiquer une relation de collusion ou de favoritisme. Un employé est lié à un fournisseur par des informations de contact communes, ce qui peut être un indicateur de double match.
        Entrée : dictionnaire de tables avec des listes d'employés et de fournisseurs
        Sortie : le même dictionnaire de tables, mais avec un employé et un fournisseur liés par des informations de contact communes, et une étiquette de scénario ajoutée pour indiquer le scénario de double match"""
        employe = self._row(tables["employes"])
        attributes = self._double_match_attributes()
        fournisseur = self._rows_without_boite_postale(tables["fournisseurs"], 1)[0] if "adresse" in attributes else self._row(tables["fournisseurs"])
        for attribute in attributes:
            self._share_attribute(employe, fournisseur, attribute)
        self._tag(tables, ScenarioId.DOUBLE_MATCH, employe["id_employe"], fournisseur["id_fournisseur"], *attributes)

    def _row(self, rows: list[dict]) -> dict:
        row = rows[self.index % len(rows)]
        self.index += 1
        return row

    def _rows(self, rows: list[dict], count: int) -> list[dict]:
        return [self._row(rows) for _ in range(count)]

    def _rows_without_boite_postale(self, rows: list[dict], count: int) -> list[dict]:
        result = []
        attempts = 0
        while len(result) < count and attempts < len(rows) * 2:
            row = self._row(rows)
            if row.get("is_boite_postale") != "true":
                result.append(row)
            attempts += 1
        if len(result) < count:
            result.extend(self._rows(rows, count - len(result)))
        return result

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

    def _date_before_window(self, reference: str, min_days: int, max_days: int) -> str:
        reference_date = date.fromisoformat(str(reference))
        start_date = date.fromisoformat(self.config.date_range.start)
        latest_date = reference_date - timedelta(days=max(1, min_days))
        if latest_date < start_date:
            return str(start_date)
        earliest_date = max(start_date, reference_date - timedelta(days=max(min_days, max_days)))
        return str(earliest_date + timedelta(days=self.random.randint(0, (latest_date - earliest_date).days)))

    def _ensure_transaction_has_previous_days(self, transaction: dict, min_days: int) -> None:
        transaction_date = date.fromisoformat(str(transaction["date_transaction"]))
        validation_date = date.fromisoformat(str(transaction["date_validation"]))
        start_date = date.fromisoformat(self.config.date_range.start)
        end_date = date.fromisoformat(self.config.date_range.end)
        minimum_transaction_date = start_date + timedelta(days=max(1, min_days))
        if transaction_date < minimum_transaction_date:
            transaction_date = min(end_date, minimum_transaction_date)
            transaction["date_transaction"] = str(transaction_date)
        if validation_date < transaction_date:
            transaction["date_validation"] = str(transaction_date)

    def _gift_amount(self) -> float:
        return round(self.random.uniform(self.config.amounts.gift_min, self.config.amounts.gift_max), 2)

    def _shell_transaction_amount(self) -> float:
        return round(
            self.random.uniform(
                self.config.scenario_parameters.shell_transaction_min_amount,
                self.config.scenario_parameters.shell_transaction_max_amount,
            ),
            2,
        )

    def _financial_concentration_amount(self) -> float:
        return round(
            self.random.uniform(
                self.config.scenario_parameters.financial_concentration_min_amount,
                self.config.scenario_parameters.financial_concentration_max_amount,
            ),
            2,
        )

    def _hidden_link_attributes(self) -> list[str]:
        attributes = self.config.scenario_parameters.hidden_link_attributes
        min_count = self.config.scenario_parameters.hidden_link_min_attributes
        max_count = self.config.scenario_parameters.hidden_link_max_attributes
        if len(attributes) < min_count:
            raise ValueError("hidden_link_attributes doit contenir assez d'attributs")
        count = self.random.randint(min_count, min(max_count, len(attributes)))
        return self.random.sample(attributes, count)

    def _double_match_attributes(self) -> list[str]:
        pairs = list(combinations(self.config.scenario_parameters.double_match_attributes, 2))
        if not pairs:
            raise ValueError("double_match_attributes doit contenir au moins deux attributs")
        pair = pairs[self.double_match_pair_index % len(pairs)]
        self.double_match_pair_index += 1
        return list(pair)

    def _share_attribute(self, employe: dict, fournisseur: dict, attribute: str) -> None:
        if attribute == "adresse":
            self._set_address(fournisseur, employe["adresse"])
        elif attribute == "nom":
            fournisseur["nom_dirigeant"] = employe["nom"]
        else:
            fournisseur[attribute] = employe[attribute]

    def _set_address(self, row: dict, address: str) -> None:
        if row.get("is_boite_postale") == "true":
            return
        row["adresse"] = address

    def _tag(self, tables: dict[str, list[dict]], scenario_id: ScenarioId, *entity_ids: str) -> None:
        tables.setdefault("scenario_labels", []).append(
            {"scenario_id": scenario_id.value, "entity_ids": "|".join(entity_ids)}
        )
