from datetime import date, timedelta
from random import Random

from faker import Faker

from conflict_detector.generation.config import GenerationConfig


class DatasetFactory:
    def __init__(self, config: GenerationConfig) -> None:
        self.config = config
        self.random = Random(config.seed)
        self.fake = Faker("fr_FR")
        self.fake.seed_instance(config.seed)

    def generate_clean_entities(self) -> dict[str, list[dict]]:
        employes = [
            {
                "id_employe": f"EMP{i:04d}",
                "prenom": self.fake.first_name(),
                "nom": self.fake.last_name(),
                "email": self.fake.unique.email(),
                "telephone": self.fake.phone_number(),
                "adresse": self.fake.address().replace("\n", ", "),
                "iban": self.fake.iban(),
                "poste": self.random.choice(["Acheteur", "Comptable", "CFO", "Manager", "Controleur"]),
                "departement": self.random.choice(["Achats", "Finance", "Juridique", "Operations"]),
                "manager_id": "",
                "date_embauche": self._date(),
                "statut": "ACTIF",
            }
            for i in range(1, self.config.volumes.employes + 1)
        ]
        for employe in employes:
            employe["manager_id"] = self.random.choice(employes)["id_employe"]
        fournisseurs = [
            {
                "id_fournisseur": f"FOU{i:04d}",
                "nom": self.fake.company(),
                "siren": self._siren(),
                "email": self.fake.unique.company_email(),
                "telephone": self.fake.phone_number(),
                "adresse": self.fake.address().replace("\n", ", "),
                "iban": self.fake.iban(),
                "nom_dirigeant": self.fake.last_name(),
                "beneficiaire_effectif": self.fake.name(),
                "date_creation": self._date(),
                "pays": "France",
                "statut": "ACTIF",
                "type_fournisseur": self.random.choice(["SERVICE", "CONSEIL", "LOGICIEL", "FOURNITURE"]),
                "is_boite_postale": "false",
                "is_societe_ecran": "false",
            }
            for i in range(1, self.config.volumes.fournisseurs + 1)
        ]
        return {"employes": employes, "fournisseurs": fournisseurs}

    def generate_clean_transactions(self, tables: dict[str, list[dict]]) -> dict[str, list[dict]]:
        transactions = []
        nb_contrats = self._contract_count()
        contrats_existants = [f"CTR-{i:05d}" for i in range(1, nb_contrats + 1)]
        commandes_existantes = []
        for i in range(1, self.config.volumes.transactions + 1):
            transaction_date = self._date()
            validation_date = self._validation_date(transaction_date)
            if i <= nb_contrats:
                type_transaction = "CONTRAT"
                id_contrat = contrats_existants[i - 1]
                numero_facture = ""
                id_commande = ""
            else:
                type_transaction = self.random.choice(["FACTURE", "COMMANDE"])
                id_contrat = self.random.choice(contrats_existants)
                if type_transaction == "COMMANDE":
                    id_commande = f"CMD-{i:05d}"
                    commandes_existantes.append(id_commande)
                    numero_facture = ""
                else:
                    id_commande = self._linked_order_id(commandes_existantes)
                    numero_facture = f"FAC-{i:05d}"
            transactions.append({
                    "id_transaction": f"TRX{i:05d}",
                    "id_employe": self.random.choice(tables["employes"])["id_employe"],
                    "id_fournisseur": self.random.choice(tables["fournisseurs"])["id_fournisseur"],
                    "date_transaction": transaction_date,
                    "montant": self._amount(),
                    "devise": "EUR",
                    "type_transaction": type_transaction,
                    "description": self.random.choice(["Conseil", "Maintenance", "Logiciel", "Fournitures", "Audit"]),
                    "statut": "VALIDEE",
                    "numero_facture": numero_facture,
                    "id_contrat": id_contrat,
                    "id_commande": id_commande,
                    "date_validation": validation_date,
                    "mode_paiement": self._payment_method(),
                    "cadeau_ou_avantage": "false",
                    "date_cadeau": "",
                    "montant_cadeau": 0,
                })
        transactions.sort(key=lambda transaction: (transaction["date_transaction"], transaction["id_transaction"]))
        return {"transactions": transactions}

    def generate(self) -> dict[str, list[dict]]:
        tables = self.generate_clean_entities()
        tables.update(self.generate_clean_transactions(tables))
        return tables

    def _date(self) -> str:
        start = date.fromisoformat(self.config.date_range.start)
        end = date.fromisoformat(self.config.date_range.end)
        return str(start + timedelta(days=self.random.randint(0, (end - start).days)))

    def _contract_count(self) -> int:
        count = round(self.config.volumes.transactions * self.config.transaction_parameters.contract_ratio_percent / 100)
        return min(self.config.volumes.transactions, max(1, count))

    def _validation_date(self, transaction_date: str) -> str:
        start = date.fromisoformat(transaction_date)
        end = date.fromisoformat(self.config.date_range.end)
        min_days = self.config.transaction_parameters.validation_delay_min_days
        max_days = self.config.transaction_parameters.validation_delay_max_days
        delay = self.random.randint(min_days, max_days)
        return str(min(end, start + timedelta(days=delay)))

    def _payment_method(self) -> str:
        weights = self.config.transaction_parameters.payment_method_weights
        methods = list(weights.keys())
        return self.random.choices(methods, weights=[weights[method] for method in methods])[0]

    def _linked_order_id(self, commandes_existantes: list[str]) -> str:
        if not commandes_existantes:
            return ""
        probability = self.config.transaction_parameters.invoice_link_to_order_percent / 100
        if self.random.random() <= probability:
            return self.random.choice(commandes_existantes)
        return ""

    def _amount(self) -> float:
        return round(self.random.uniform(self.config.amounts.min, self.config.amounts.max), 2)

    def _siren(self) -> str:
        return "".join(str(self.random.randint(0, 9)) for _ in range(9))
