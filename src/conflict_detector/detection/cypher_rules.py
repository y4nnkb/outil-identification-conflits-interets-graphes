from dataclasses import dataclass
from typing import Any

from neo4j import Driver

from conflict_detector.detection.base import DetectionResult
from conflict_detector.domain.enums import ScenarioId


@dataclass(frozen=True)
class CypherDetectionRule:
    rule_id: str
    scenario_id: ScenarioId
    query: str

    def run(self, driver: Driver) -> list[DetectionResult]:
        with driver.session() as session:
            rows = session.run(self.query, rule_id=self.rule_id).data()
        return [_row_to_result(self.scenario_id, row) for row in rows]


SHARED_IBAN_QUERY = """
    MATCH (e:Employe)-[:A_IBAN]->(i:Iban)<-[:A_IBAN]-(f:Fournisseur)
    OPTIONAL MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
    WITH e, f, i, count(DISTINCT t) AS transaction_count, collect(DISTINCT t.id_transaction)[0..10] AS source_rows
    RETURN
        [
            {id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')},
            {id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            attribute: 'iban',
            value: i.value,
            transaction_count: transaction_count
        } AS evidence,
        [e.id_employe, i.value, f.id_fournisseur] AS path,
        source_rows AS source_rows
    LIMIT 5000
"""

SHARED_EMAIL_QUERY = """
    MATCH (e:Employe)-[:A_EMAIL]->(email:Email)<-[:A_EMAIL]-(f:Fournisseur)
    MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
    WITH e, f, email, count(DISTINCT t) AS transaction_count, collect(DISTINCT t.id_transaction)[0..10] AS source_rows
    RETURN
        [
            {id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')},
            {id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            attribute: 'email',
            value: email.value,
            transaction_count: transaction_count
        } AS evidence,
        [e.id_employe, email.value, f.id_fournisseur] AS path,
        source_rows AS source_rows
    LIMIT 5000
"""

SHARED_PHONE_QUERY = """
    MATCH (e:Employe)-[:A_TELEPHONE]->(phone:Telephone)<-[:A_TELEPHONE]-(f:Fournisseur)
    MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
    WITH e, f, phone, count(DISTINCT t) AS transaction_count, collect(DISTINCT t.id_transaction)[0..10] AS source_rows
    RETURN
        [
            {id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')},
            {id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            attribute: 'telephone',
            value: phone.value,
            transaction_count: transaction_count
        } AS evidence,
        [e.id_employe, phone.value, f.id_fournisseur] AS path,
        source_rows AS source_rows
    LIMIT 5000
"""

SHARED_ADDRESS_QUERY = """
    MATCH (e:Employe)-[:A_ADRESSE]->(address)<-[:A_ADRESSE]-(f:Fournisseur)
    MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
    OPTIONAL MATCH (address)<-[:A_ADRESSE]-(employeeOnAddress:Employe)
    OPTIONAL MATCH (address)<-[:A_ADRESSE]-(supplierOnAddress:Fournisseur)
    WITH
        e,
        f,
        address,
        count(DISTINCT t) AS transaction_count,
        collect(DISTINCT t.id_transaction)[0..10] AS source_rows,
        count(DISTINCT employeeOnAddress) AS employee_count,
        count(DISTINCT supplierOnAddress) AS supplier_count
    WHERE transaction_count > 0
    RETURN
        [
            {id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')},
            {id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            attribute: 'adresse',
            value: address.value,
            transaction_count: transaction_count,
            address_employee_count: employee_count,
            address_supplier_count: supplier_count
        } AS evidence,
        [e.id_employe, address.value, f.id_fournisseur] AS path,
        source_rows AS source_rows
    LIMIT 5000
"""

MULTIPLE_HIDDEN_LINKS_QUERY = """
    MATCH (e:Employe)-[employeeRel]->(attribute)<-[supplierRel]-(f:Fournisseur)
    WHERE type(employeeRel) = type(supplierRel)
      AND type(employeeRel) IN ['A_EMAIL', 'A_TELEPHONE', 'A_ADRESSE', 'A_IBAN', 'A_NOM']
    WITH
        e,
        f,
        collect(DISTINCT replace(type(employeeRel), 'A_', '')) AS shared_attributes,
        collect(DISTINCT attribute.value) AS shared_values
    WHERE size(shared_attributes) >= 3
    OPTIONAL MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
    WITH e, f, shared_attributes, shared_values, count(DISTINCT t) AS transaction_count, collect(DISTINCT t.id_transaction)[0..10] AS source_rows
    WHERE transaction_count > 0
    RETURN
        [
            {id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')},
            {id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            shared_attributes: shared_attributes,
            shared_values: shared_values,
            transaction_count: transaction_count
        } AS evidence,
        [e.id_employe, f.id_fournisseur] AS path,
        source_rows AS source_rows
    LIMIT 5000
"""

DOUBLE_MATCH_QUERY = """
    MATCH (e:Employe)-[employeeRel]->(attribute)<-[supplierRel]-(f:Fournisseur)
    WHERE type(employeeRel) = type(supplierRel)
      AND type(employeeRel) IN ['A_EMAIL', 'A_TELEPHONE', 'A_ADRESSE', 'A_IBAN', 'A_NOM']
    WITH
        e,
        f,
        collect(DISTINCT replace(type(employeeRel), 'A_', '')) AS shared_attributes,
        collect(DISTINCT attribute.value) AS shared_values
    WHERE size(shared_attributes) = 2
    OPTIONAL MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
    WITH e, f, shared_attributes, shared_values, count(DISTINCT t) AS transaction_count, collect(DISTINCT t.id_transaction)[0..10] AS source_rows
    WHERE transaction_count > 0
    RETURN
        [
            {id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')},
            {id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            shared_attributes: shared_attributes,
            shared_values: shared_values,
            transaction_count: transaction_count
        } AS evidence,
        [e.id_employe, f.id_fournisseur] AS path,
        source_rows AS source_rows
    LIMIT 5000
"""

GHOST_SUPPLIER_QUERY = """
    MATCH (f:Fournisseur)<-[:VERS]-(t:Transaction)
    WHERE toLower(toString(f.is_boite_postale)) = 'true'
    WITH f, count(DISTINCT t) AS transaction_count, round(avg(toFloat(t.montant)), 2) AS average_amount, collect(DISTINCT t.id_transaction)[0..10] AS source_rows
    WHERE transaction_count >= 3
    RETURN
        [{id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')}] AS entities,
        {
            rule_id: $rule_id,
            is_boite_postale: f.is_boite_postale,
            transaction_count: transaction_count,
            average_amount: average_amount
        } AS evidence,
        [f.id_fournisseur] AS path,
        source_rows AS source_rows
    LIMIT 5000
"""

BRIBES_GIFTS_QUERY = """
    MATCH (e:Employe)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f:Fournisseur)
    WHERE toLower(toString(t.cadeau_ou_avantage)) = 'true'
      AND t.date_cadeau IS NOT NULL
      AND trim(toString(t.date_cadeau)) <> ''
    WITH e, t, f, duration.inDays(date(t.date_cadeau), date(t.date_transaction)).days AS gift_delay_days
    WHERE gift_delay_days >= 0 AND gift_delay_days <= 7
    RETURN
        [
            {id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')},
            {id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')},
            {id: t.id_transaction, type: 'Transaction', label: coalesce(t.type_transaction, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            date_cadeau: t.date_cadeau,
            date_transaction: t.date_transaction,
            gift_delay_days: gift_delay_days,
            montant_cadeau: t.montant_cadeau
        } AS evidence,
        [e.id_employe, t.id_transaction, f.id_fournisseur] AS path,
        [t.id_transaction] AS source_rows
    LIMIT 5000
"""

SHELL_ENTITY_QUERY = """
    MATCH (e:Employe), (f:Fournisseur)
    WHERE toUpper(toString(f.beneficiaire_effectif)) = toUpper(coalesce(e.prenom, '') + ' ' + coalesce(e.nom, ''))
    OPTIONAL MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
    WITH e, f, count(DISTINCT t) AS transaction_count, collect(DISTINCT t.id_transaction)[0..10] AS source_rows
    RETURN
        [
            {id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')},
            {id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            beneficiaire_effectif: f.beneficiaire_effectif,
            transaction_count: transaction_count
        } AS evidence,
        [e.id_employe, f.id_fournisseur] AS path,
        source_rows AS source_rows
    LIMIT 5000
"""

STAR_PATTERN_QUERY = """
    MATCH (e:Employe)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f:Fournisseur)
    WITH e, collect(DISTINCT f) AS suppliers, collect(DISTINCT t.id_transaction)[0..10] AS source_rows, count(DISTINCT t) AS transaction_count, round(sum(toFloat(t.montant)), 2) AS total_amount
    WHERE size(suppliers) >= 3
    UNWIND suppliers AS supplier
    OPTIONAL MATCH (e)-[:A_ADRESSE]->(address:Adresse)<-[:A_ADRESSE]-(supplier)
    OPTIONAL MATCH (e)-[:A_IBAN]->(iban:Iban)<-[:A_IBAN]-(supplier)
    WITH e, suppliers, source_rows, transaction_count, total_amount, count(DISTINCT address) AS shared_addresses, count(DISTINCT iban) AS shared_ibans
    WHERE shared_addresses + shared_ibans >= 1 AND transaction_count >= size(suppliers)
    RETURN
        [{id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')}]
        + [supplier IN suppliers | {id: supplier.id_fournisseur, type: 'Fournisseur', label: coalesce(supplier.nom, '')}] AS entities,
        {
            rule_id: $rule_id,
            supplier_count: size(suppliers),
            transaction_count: transaction_count,
            total_amount: total_amount,
            shared_addresses: shared_addresses,
            shared_ibans: shared_ibans
        } AS evidence,
        [e.id_employe] + [supplier IN suppliers | supplier.id_fournisseur] AS path,
        source_rows AS source_rows
    ORDER BY transaction_count DESC, size(suppliers) DESC
    LIMIT 1000
"""

CIRCULAR_NETWORK_QUERY = """
    MATCH (a:Fournisseur)-[relA]->(attributeA)<-[relB]-(b:Fournisseur)
    MATCH (b)-[relC]->(attributeB)<-[relD]-(c:Fournisseur)
    MATCH (c)-[relE]->(attributeC)<-[relF]-(a)
    WITH a, b, c, relA, relB, relC, relD, relE, relF, [a.id_fournisseur, b.id_fournisseur, c.id_fournisseur] AS ids
    WHERE a.id_fournisseur = reduce(minId = ids[0], id IN ids | CASE WHEN id < minId THEN id ELSE minId END)
      AND size(ids) = size([id IN ids WHERE single(other IN ids WHERE other = id)])
      AND type(relA) = type(relB)
      AND type(relC) = type(relD)
      AND type(relE) = type(relF)
      AND type(relA) IN ['A_EMAIL', 'A_TELEPHONE', 'A_ADRESSE', 'A_IBAN']
      AND type(relC) IN ['A_EMAIL', 'A_TELEPHONE', 'A_ADRESSE', 'A_IBAN']
      AND type(relE) IN ['A_EMAIL', 'A_TELEPHONE', 'A_ADRESSE', 'A_IBAN']
    WITH
        a,
        b,
        c,
        collect(DISTINCT replace(type(relA), 'A_', '')) +
        collect(DISTINCT replace(type(relC), 'A_', '')) +
        collect(DISTINCT replace(type(relE), 'A_', '')) AS raw_link_types
    UNWIND raw_link_types AS link_type
    WITH a, b, c, collect(DISTINCT link_type) AS link_types
    WHERE size(link_types) >= 3
    RETURN
        [
            {id: a.id_fournisseur, type: 'Fournisseur', label: coalesce(a.nom, '')},
            {id: b.id_fournisseur, type: 'Fournisseur', label: coalesce(b.nom, '')},
            {id: c.id_fournisseur, type: 'Fournisseur', label: coalesce(c.nom, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            supplier_count: 3,
            link_types: link_types
        } AS evidence,
        [a.id_fournisseur, b.id_fournisseur, c.id_fournisseur, a.id_fournisseur] AS path,
        [] AS source_rows
    LIMIT 1000
"""

FINANCIAL_CONCENTRATION_QUERY = """
    MATCH (e:Employe)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f:Fournisseur)
    WITH e, f, count(DISTINCT t) AS transaction_count, round(sum(toFloat(t.montant)), 2) AS total_amount, round(avg(toFloat(t.montant)), 2) AS average_amount, collect(DISTINCT t.id_transaction)[0..10] AS source_rows
    WHERE transaction_count >= 5 AND total_amount >= 300000
    RETURN
        [
            {id: e.id_employe, type: 'Employe', label: coalesce(e.prenom, '') + ' ' + coalesce(e.nom, '')},
            {id: f.id_fournisseur, type: 'Fournisseur', label: coalesce(f.nom, '')}
        ] AS entities,
        {
            rule_id: $rule_id,
            transaction_count: transaction_count,
            total_amount: total_amount,
            average_amount: average_amount
        } AS evidence,
        [e.id_employe, f.id_fournisseur] AS path,
        source_rows AS source_rows
    ORDER BY total_amount DESC
    LIMIT 5000
"""

INTERNAL_NETWORK_QUERY = """
    MATCH (manager:Employe)-[:MANAGE]->(e:Employe)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f:Fournisseur)
    MATCH (e)-[:A_ADRESSE]->(address:Adresse)<-[:A_ADRESSE]-(f)
    WITH
        manager,
        address,
        collect(DISTINCT e) AS employees,
        collect(DISTINCT f) AS suppliers,
        count(DISTINCT t) AS transaction_count,
        collect(DISTINCT t.id_transaction)[0..10] AS source_rows
    WHERE size(employees) >= 2 AND size(suppliers) >= 2 AND transaction_count >= 4
    RETURN
        [{id: manager.id_employe, type: 'Employe', label: coalesce(manager.prenom, '') + ' ' + coalesce(manager.nom, '')}]
        + [employee IN employees | {id: employee.id_employe, type: 'Employe', label: coalesce(employee.prenom, '') + ' ' + coalesce(employee.nom, '')}]
        + [supplier IN suppliers | {id: supplier.id_fournisseur, type: 'Fournisseur', label: coalesce(supplier.nom, '')}] AS entities,
        {
            rule_id: $rule_id,
            manager_id: manager.id_employe,
            shared_address: address.value,
            employee_count: size(employees),
            supplier_count: size(suppliers),
            transaction_count: transaction_count
        } AS evidence,
        [manager.id_employe] + [employee IN employees | employee.id_employe] + [supplier IN suppliers | supplier.id_fournisseur] AS path,
        source_rows AS source_rows
    ORDER BY transaction_count DESC
    LIMIT 1000
"""

DEFAULT_RULES = [
    CypherDetectionRule("shared_iban_employee_supplier", ScenarioId.IDENTITY_MATCH, SHARED_IBAN_QUERY),
    CypherDetectionRule("shared_email_employee_supplier", ScenarioId.IDENTITY_MATCH, SHARED_EMAIL_QUERY),
    CypherDetectionRule("shared_phone_employee_supplier", ScenarioId.IDENTITY_MATCH, SHARED_PHONE_QUERY),
    CypherDetectionRule("shared_address_employee_supplier", ScenarioId.DIRECT_LINK, SHARED_ADDRESS_QUERY),
    CypherDetectionRule("double_attribute_match", ScenarioId.DOUBLE_MATCH, DOUBLE_MATCH_QUERY),
    CypherDetectionRule("multiple_hidden_links", ScenarioId.MULTIPLE_HIDDEN_LINKS, MULTIPLE_HIDDEN_LINKS_QUERY),
    CypherDetectionRule("ghost_supplier_po_box", ScenarioId.GHOST_SUPPLIER, GHOST_SUPPLIER_QUERY),
    CypherDetectionRule("bribe_gift_before_transaction", ScenarioId.BRIBES_GIFTS, BRIBES_GIFTS_QUERY),
    CypherDetectionRule("beneficial_owner_is_employee", ScenarioId.SHELL_ENTITY, SHELL_ENTITY_QUERY),
    CypherDetectionRule("employee_supplier_star_pattern", ScenarioId.STAR_PATTERN, STAR_PATTERN_QUERY),
    CypherDetectionRule("supplier_circular_network", ScenarioId.CIRCULAR_NETWORK, CIRCULAR_NETWORK_QUERY),
    CypherDetectionRule("financial_concentration_pair", ScenarioId.FINANCIAL_CONCENTRATION, FINANCIAL_CONCENTRATION_QUERY),
    CypherDetectionRule("managed_internal_network", ScenarioId.INTERNAL_NETWORK, INTERNAL_NETWORK_QUERY),
]


def run_default_rules(driver: Driver) -> list[DetectionResult]:
    results: list[DetectionResult] = []
    for rule in DEFAULT_RULES:
        results.extend(rule.run(driver))
    return results


def detection_result_to_dict(result: DetectionResult) -> dict[str, Any]:
    return {
        "scenario_id": result.scenario_id.value,
        "entities": result.entities,
        "evidence": result.evidence,
        "path": result.path,
        "source_rows": result.source_rows,
    }


def _row_to_result(scenario_id: ScenarioId, row: dict[str, Any]) -> DetectionResult:
    return DetectionResult(
        scenario_id=scenario_id,
        entities=row.get("entities", []),
        evidence=row.get("evidence", {}),
        path=row.get("path", []),
        source_rows=row.get("source_rows", []),
    )
