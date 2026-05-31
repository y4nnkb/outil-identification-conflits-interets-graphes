from neo4j import Driver


CONSTRAINT_QUERIES = [
    "CREATE CONSTRAINT employe_id IF NOT EXISTS FOR (n:Employe) REQUIRE n.id_employe IS UNIQUE",
    "CREATE CONSTRAINT fournisseur_id IF NOT EXISTS FOR (n:Fournisseur) REQUIRE n.id_fournisseur IS UNIQUE",
    "CREATE CONSTRAINT transaction_id IF NOT EXISTS FOR (n:Transaction) REQUIRE n.id_transaction IS UNIQUE",
    "CREATE CONSTRAINT email_value IF NOT EXISTS FOR (n:Email) REQUIRE n.value IS UNIQUE",
    "CREATE CONSTRAINT telephone_value IF NOT EXISTS FOR (n:Telephone) REQUIRE n.value IS UNIQUE",
    "CREATE CONSTRAINT adresse_value IF NOT EXISTS FOR (n:Adresse) REQUIRE n.value IS UNIQUE",
    "CREATE CONSTRAINT iban_value IF NOT EXISTS FOR (n:Iban) REQUIRE n.value IS UNIQUE",
    "CREATE CONSTRAINT siren_value IF NOT EXISTS FOR (n:Siren) REQUIRE n.value IS UNIQUE",
    "CREATE CONSTRAINT contrat_id IF NOT EXISTS FOR (n:Contrat) REQUIRE n.id_contrat IS UNIQUE",
    "CREATE CONSTRAINT commande_id IF NOT EXISTS FOR (n:Commande) REQUIRE n.id_commande IS UNIQUE",
    "CREATE CONSTRAINT scenario_id IF NOT EXISTS FOR (n:Scenario) REQUIRE n.scenario_id IS UNIQUE",
    "CREATE CONSTRAINT scenario_case_id IF NOT EXISTS FOR (n:ScenarioCase) REQUIRE n.case_id IS UNIQUE",
]

INDEX_QUERIES = [
    "CREATE INDEX transaction_date IF NOT EXISTS FOR (n:Transaction) ON (n.date_transaction)",
    "CREATE INDEX transaction_montant IF NOT EXISTS FOR (n:Transaction) ON (n.montant)",
    "CREATE INDEX transaction_contrat IF NOT EXISTS FOR (n:Transaction) ON (n.id_contrat)",
    "CREATE INDEX transaction_commande IF NOT EXISTS FOR (n:Transaction) ON (n.id_commande)",
    "CREATE INDEX employe_departement IF NOT EXISTS FOR (n:Employe) ON (n.departement)",
    "CREATE INDEX fournisseur_type IF NOT EXISTS FOR (n:Fournisseur) ON (n.type_fournisseur)",
]


def run_queries(driver: Driver, queries: list[str]) -> None:
    with driver.session() as session:
        for query in queries:
            session.run(query).consume()


def create_constraints(driver: Driver) -> None:
    run_queries(driver, CONSTRAINT_QUERIES)


def create_indexes(driver: Driver) -> None:
    run_queries(driver, INDEX_QUERIES)


def create_schema(driver: Driver) -> None:
    create_constraints(driver)
    create_indexes(driver)


def clear_graph(driver: Driver) -> None:
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n").consume()
