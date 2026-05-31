import pandas as pd
from neo4j import Driver

from conflict_detector.graph.schema import clear_graph, create_schema


BATCH_SIZE = 500

NODE_QUERIES = {
    "employes": """
        UNWIND $rows AS row
        MERGE (n:Employe {id_employe: row.id_employe})
        SET n += row
        SET n.display_label = row.id_employe + ' - ' + coalesce(row.prenom, '') + ' ' + coalesce(row.nom, '')
    """,
    "fournisseurs": """
        UNWIND $rows AS row
        MERGE (n:Fournisseur {id_fournisseur: row.id_fournisseur})
        SET n += row
        SET n.display_label = row.id_fournisseur + ' - ' + coalesce(row.nom, '')
    """,
    "transactions": """
        UNWIND $rows AS row
        MERGE (n:Transaction {id_transaction: row.id_transaction})
        SET n += row
        SET n.display_label = row.id_transaction + ' - ' + coalesce(row.type_transaction, '')
    """,
}

ATTRIBUTE_COLUMNS = {
    "employes": {
        "email_norm": ("Email", "emails"),
        "telephone_norm": ("Telephone", "telephones"),
        "adresse_norm": ("Adresse", "adresses"),
        "iban_norm": ("Iban", "ibans"),
        "nom_norm": ("Nom", "noms"),
    },
    "fournisseurs": {
        "email_norm": ("Email", "emails"),
        "telephone_norm": ("Telephone", "telephones"),
        "adresse_norm": ("Adresse", "adresses"),
        "iban_norm": ("Iban", "ibans"),
        "siren_norm": ("Siren", "sirens"),
        "nom_dirigeant_norm": ("Nom", "noms"),
    },
}

ATTRIBUTE_QUERIES = {
    "emails": "UNWIND $values AS value MERGE (n:Email {value: value}) SET n.display_label = value",
    "telephones": "UNWIND $values AS value MERGE (n:Telephone {value: value}) SET n.display_label = value",
    "adresses": "UNWIND $values AS value MERGE (n:Adresse {value: value}) SET n.display_label = left(value, 40)",
    "ibans": "UNWIND $values AS value MERGE (n:Iban {value: value}) SET n.display_label = value",
    "sirens": "UNWIND $values AS value MERGE (n:Siren {value: value}) SET n.display_label = value",
    "noms": "UNWIND $values AS value MERGE (n:Nom {value: value}) SET n.display_label = value",
}

TRANSACTION_RELATION_QUERY = """
    UNWIND $rows AS row
    MATCH (e:Employe {id_employe: row.id_employe})
    MATCH (t:Transaction {id_transaction: row.id_transaction})
    MATCH (f:Fournisseur {id_fournisseur: row.id_fournisseur})
    MERGE (e)-[:A_EFFECTUE]->(t)
    MERGE (t)-[:VERS]->(f)
"""

MANAGER_RELATION_QUERY = """
    UNWIND $rows AS row
    MATCH (manager:Employe {id_employe: row.manager_id})
    MATCH (employe:Employe {id_employe: row.id_employe})
    MERGE (manager)-[:MANAGE]->(employe)
"""

ATTRIBUTE_RELATION_QUERIES = {
    ("employes", "email_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Employe {id_employe: row.id_employe})
        MATCH (attribute:Email {value: row.email_norm})
        MERGE (entity)-[:A_EMAIL]->(attribute)
    """,
    ("employes", "telephone_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Employe {id_employe: row.id_employe})
        MATCH (attribute:Telephone {value: row.telephone_norm})
        MERGE (entity)-[:A_TELEPHONE]->(attribute)
    """,
    ("employes", "adresse_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Employe {id_employe: row.id_employe})
        MATCH (attribute:Adresse {value: row.adresse_norm})
        MERGE (entity)-[:A_ADRESSE]->(attribute)
    """,
    ("employes", "iban_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Employe {id_employe: row.id_employe})
        MATCH (attribute:Iban {value: row.iban_norm})
        MERGE (entity)-[:A_IBAN]->(attribute)
    """,
    ("employes", "nom_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Employe {id_employe: row.id_employe})
        MATCH (attribute:Nom {value: row.nom_norm})
        MERGE (entity)-[:A_NOM]->(attribute)
    """,
    ("fournisseurs", "email_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Fournisseur {id_fournisseur: row.id_fournisseur})
        MATCH (attribute:Email {value: row.email_norm})
        MERGE (entity)-[:A_EMAIL]->(attribute)
    """,
    ("fournisseurs", "telephone_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Fournisseur {id_fournisseur: row.id_fournisseur})
        MATCH (attribute:Telephone {value: row.telephone_norm})
        MERGE (entity)-[:A_TELEPHONE]->(attribute)
    """,
    ("fournisseurs", "adresse_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Fournisseur {id_fournisseur: row.id_fournisseur})
        MATCH (attribute:Adresse {value: row.adresse_norm})
        MERGE (entity)-[:A_ADRESSE]->(attribute)
    """,
    ("fournisseurs", "iban_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Fournisseur {id_fournisseur: row.id_fournisseur})
        MATCH (attribute:Iban {value: row.iban_norm})
        MERGE (entity)-[:A_IBAN]->(attribute)
    """,
    ("fournisseurs", "siren_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Fournisseur {id_fournisseur: row.id_fournisseur})
        MATCH (attribute:Siren {value: row.siren_norm})
        MERGE (entity)-[:A_SIREN]->(attribute)
    """,
    ("fournisseurs", "nom_dirigeant_norm"): """
        UNWIND $rows AS row
        MATCH (entity:Fournisseur {id_fournisseur: row.id_fournisseur})
        MATCH (attribute:Nom {value: row.nom_dirigeant_norm})
        MERGE (entity)-[:A_NOM]->(attribute)
    """,
}

CONTRACT_RELATION_QUERY = """
    UNWIND $rows AS row
    MATCH (t:Transaction {id_transaction: row.id_transaction})
    MERGE (c:Contrat {id_contrat: row.id_contrat})
    SET c.display_label = row.id_contrat
    MERGE (t)-[:RATTACHEE_A_CONTRAT]->(c)
"""

ORDER_NODE_RELATION_QUERY = """
    UNWIND $rows AS row
    MATCH (t:Transaction {id_transaction: row.id_transaction})
    MERGE (c:Commande {id_commande: row.id_commande})
    SET c.display_label = row.id_commande
    MERGE (t)-[:REPRESENTE_COMMANDE]->(c)
"""

INVOICE_ORDER_RELATION_QUERY = """
    UNWIND $rows AS row
    MATCH (facture:Transaction {id_transaction: row.id_transaction})
    MATCH (commande:Transaction {id_commande: row.id_commande})
    WHERE commande.type_transaction = 'COMMANDE'
    MERGE (facture)-[:FACTURE_COMMANDE]->(commande)
"""

SCENARIO_NODE_QUERY = """
    UNWIND $rows AS row
    MERGE (scenario:Scenario {scenario_id: row.scenario_id})
    MERGE (scenarioCase:ScenarioCase {case_id: row.case_id})
    SET scenario.display_label = row.scenario_id,
        scenarioCase.display_label = row.case_id
    SET scenarioCase.scenario_id = row.scenario_id,
        scenarioCase.entity_ids = row.entity_ids
    MERGE (scenarioCase)-[:TYPE_SCENARIO]->(scenario)
"""

SCENARIO_EMPLOYE_QUERY = """
    UNWIND $rows AS row
    MATCH (entity:Employe {id_employe: row.entity_id})
    MATCH (scenarioCase:ScenarioCase {case_id: row.case_id})
    MERGE (entity)-[:IMPLIQUE_DANS]->(scenarioCase)
"""

SCENARIO_FOURNISSEUR_QUERY = """
    UNWIND $rows AS row
    MATCH (entity:Fournisseur {id_fournisseur: row.entity_id})
    MATCH (scenarioCase:ScenarioCase {case_id: row.case_id})
    MERGE (entity)-[:IMPLIQUE_DANS]->(scenarioCase)
"""

SCENARIO_TRANSACTION_QUERY = """
    UNWIND $rows AS row
    MATCH (entity:Transaction {id_transaction: row.entity_id})
    MATCH (scenarioCase:ScenarioCase {case_id: row.case_id})
    MERGE (entity)-[:IMPLIQUE_DANS]->(scenarioCase)
"""


def load_nodes(driver: Driver, tables: dict[str, pd.DataFrame]) -> None:
    with driver.session() as session:
        for table_name, query in NODE_QUERIES.items():
            for batch in _batches(_records(tables[table_name]), BATCH_SIZE):
                session.run(query, rows=batch).consume()

        for attribute_type, values in _attribute_values(tables).items():
            query = ATTRIBUTE_QUERIES[attribute_type]
            for batch in _batches(sorted(values), BATCH_SIZE):
                session.run(query, values=batch).consume()


def load_relationships(driver: Driver, tables: dict[str, pd.DataFrame]) -> None:
    with driver.session() as session:
        for batch in _batches(_records(tables["transactions"]), BATCH_SIZE):
            session.run(TRANSACTION_RELATION_QUERY, rows=batch).consume()

        for batch in _batches(_records_with_values(tables["employes"], ["id_employe", "manager_id"]), BATCH_SIZE):
            session.run(MANAGER_RELATION_QUERY, rows=batch).consume()

        for (table_name, column), query in ATTRIBUTE_RELATION_QUERIES.items():
            records = _records_with_values(tables[table_name], [_id_column(table_name), column])
            for batch in _batches(records, BATCH_SIZE):
                session.run(query, rows=batch).consume()

        contract_records = _records_with_values(tables["transactions"], ["id_transaction", "id_contrat"])
        for batch in _batches(contract_records, BATCH_SIZE):
            session.run(CONTRACT_RELATION_QUERY, rows=batch).consume()

        order_records = _filtered_records(
            tables["transactions"],
            ["id_transaction", "id_commande"],
            lambda row: row.get("type_transaction") == "COMMANDE",
        )
        for batch in _batches(order_records, BATCH_SIZE):
            session.run(ORDER_NODE_RELATION_QUERY, rows=batch).consume()

        invoice_order_records = _filtered_records(
            tables["transactions"],
            ["id_transaction", "id_commande"],
            lambda row: row.get("type_transaction") == "FACTURE",
        )
        for batch in _batches(invoice_order_records, BATCH_SIZE):
            session.run(INVOICE_ORDER_RELATION_QUERY, rows=batch).consume()

        scenario_cases, scenario_entities = _scenario_records(tables)
        for batch in _batches(scenario_cases, BATCH_SIZE):
            session.run(SCENARIO_NODE_QUERY, rows=batch).consume()
        for query, records in [
            (SCENARIO_EMPLOYE_QUERY, scenario_entities["employes"]),
            (SCENARIO_FOURNISSEUR_QUERY, scenario_entities["fournisseurs"]),
            (SCENARIO_TRANSACTION_QUERY, scenario_entities["transactions"]),
        ]:
            for batch in _batches(records, BATCH_SIZE):
                session.run(query, rows=batch).consume()


def load_full_graph(driver: Driver, tables: dict[str, pd.DataFrame], reset: bool = False) -> None:
    if reset:
        clear_graph(driver)
    create_schema(driver)
    load_nodes(driver, tables)
    load_relationships(driver, tables)


def _records(table: pd.DataFrame) -> list[dict]:
    return [{key: _clean_value(value) for key, value in row.items()} for row in table.to_dict(orient="records")]


def _records_with_values(table: pd.DataFrame, columns: list[str]) -> list[dict]:
    records = []
    for record in _records(table):
        if all(_has_value(record.get(column)) for column in columns):
            records.append({column: record[column] for column in columns})
    return records


def _filtered_records(table: pd.DataFrame, columns: list[str], predicate) -> list[dict]:
    records = []
    for record in _records(table):
        if predicate(record) and all(_has_value(record.get(column)) for column in columns):
            records.append({column: record[column] for column in columns})
    return records


def _clean_value(value: object) -> object:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _has_value(value: object) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return text != "" and text.lower() not in {"nan", "nat", "none"}


def _attribute_values(tables: dict[str, pd.DataFrame]) -> dict[str, set[str]]:
    values = {attribute_type: set() for attribute_type in ATTRIBUTE_QUERIES}
    for table_name, columns in ATTRIBUTE_COLUMNS.items():
        table = tables[table_name]
        for column, (_, attribute_type) in columns.items():
            if column not in table.columns:
                continue
            for value in table[column].dropna():
                cleaned = str(value).strip()
                if _has_value(cleaned):
                    values[attribute_type].add(cleaned)
    return values


def _id_column(table_name: str) -> str:
    if table_name == "employes":
        return "id_employe"
    if table_name == "fournisseurs":
        return "id_fournisseur"
    raise ValueError(f"Table non supportee: {table_name}")


def _scenario_records(tables: dict[str, pd.DataFrame]) -> tuple[list[dict], dict[str, list[dict]]]:
    scenario_table = tables.get("scenario_labels")
    scenario_cases = []
    scenario_entities: dict[str, list[dict]] = {"employes": [], "fournisseurs": [], "transactions": []}
    if scenario_table is None:
        return scenario_cases, scenario_entities

    for index, row in enumerate(_records(scenario_table), start=1):
        scenario_id = row.get("scenario_id")
        entity_ids = row.get("entity_ids")
        if not _has_value(scenario_id) or not _has_value(entity_ids):
            continue
        case_id = f"SCN{index:05d}_{scenario_id}"
        scenario_cases.append({"case_id": case_id, "scenario_id": scenario_id, "entity_ids": entity_ids})
        for entity_id in str(entity_ids).split("|"):
            if entity_id.startswith("EMP"):
                scenario_entities["employes"].append({"case_id": case_id, "entity_id": entity_id})
            elif entity_id.startswith("FOU"):
                scenario_entities["fournisseurs"].append({"case_id": case_id, "entity_id": entity_id})
            elif entity_id.startswith("TRX"):
                scenario_entities["transactions"].append({"case_id": case_id, "entity_id": entity_id})
    return scenario_cases, scenario_entities


def _batches(items: list | tuple, size: int):
    for start in range(0, len(items), size):
        yield items[start : start + size]
