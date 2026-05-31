import pandas as pd

from conflict_detector.graph.loader import load_nodes, load_relationships


class FakeResult:
    def consume(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def run(self, query: str, **parameters) -> FakeResult:
        self.calls.append((query, parameters))
        return FakeResult()


class FakeDriver:
    def __init__(self) -> None:
        self.session_instance = FakeSession()

    def session(self) -> FakeSession:
        return self.session_instance


def test_load_nodes_creates_business_and_attribute_nodes() -> None:
    tables = {
        "employes": pd.DataFrame(
            [
                {
                    "id_employe": "EMP001",
                    "email_norm": "a@example.com",
                    "telephone_norm": "0612345678",
                    "adresse_norm": "10 AV PARIS",
                    "iban_norm": "FR761234",
                }
            ]
        ),
        "fournisseurs": pd.DataFrame(
            [
                {
                    "id_fournisseur": "FOU001",
                    "email_norm": "a@example.com",
                    "telephone_norm": "0612345678",
                    "adresse_norm": "10 AV PARIS",
                    "iban_norm": "",
                    "siren_norm": "123456789",
                }
            ]
        ),
        "transactions": pd.DataFrame(
            [{"id_transaction": "TRX001", "id_employe": "EMP001", "id_fournisseur": "FOU001"}]
        ),
    }
    driver = FakeDriver()

    load_nodes(driver, tables)

    queries = [query for query, _ in driver.session_instance.calls]
    assert any("MERGE (n:Employe" in query for query in queries)
    assert any("MERGE (n:Fournisseur" in query for query in queries)
    assert any("MERGE (n:Transaction" in query for query in queries)
    assert any("MERGE (:Email" in query for query in queries)
    assert any("MERGE (:Siren" in query for query in queries)


def test_load_relationships_creates_business_attribute_manager_and_scenario_links() -> None:
    tables = {
        "employes": pd.DataFrame(
            [
                {
                    "id_employe": "EMP001",
                    "manager_id": "EMP002",
                    "email_norm": "a@example.com",
                    "telephone_norm": "0612345678",
                    "adresse_norm": "10 AV PARIS",
                    "iban_norm": "FR761234",
                }
            ]
        ),
        "fournisseurs": pd.DataFrame(
            [
                {
                    "id_fournisseur": "FOU001",
                    "email_norm": "b@example.com",
                    "telephone_norm": "0611111111",
                    "adresse_norm": "20 BD PARIS",
                    "iban_norm": "FR769999",
                    "siren_norm": "123456789",
                }
            ]
        ),
        "transactions": pd.DataFrame(
            [
                {
                    "id_transaction": "TRX001",
                    "id_employe": "EMP001",
                    "id_fournisseur": "FOU001",
                    "id_contrat": "CTR-00001",
                    "id_commande": "CMD-00001",
                    "type_transaction": "COMMANDE",
                },
                {
                    "id_transaction": "TRX002",
                    "id_employe": "EMP001",
                    "id_fournisseur": "FOU001",
                    "id_contrat": "CTR-00001",
                    "id_commande": "CMD-00001",
                    "type_transaction": "FACTURE",
                },
            ]
        ),
        "scenario_labels": pd.DataFrame(
            [{"scenario_id": "direct_link", "entity_ids": "EMP001|FOU001|TRX001|adresse"}]
        ),
    }
    driver = FakeDriver()

    load_relationships(driver, tables)

    queries = [query for query, _ in driver.session_instance.calls]
    assert any("A_EFFECTUE" in query and "VERS" in query for query in queries)
    assert any("MANAGE" in query for query in queries)
    assert any("A_EMAIL" in query for query in queries)
    assert any("RATTACHEE_A_CONTRAT" in query for query in queries)
    assert any("REPRESENTE_COMMANDE" in query for query in queries)
    assert any("FACTURE_COMMANDE" in query for query in queries)
    assert any("TYPE_SCENARIO" in query for query in queries)
    assert any("IMPLIQUE_DANS" in query for query in queries)
