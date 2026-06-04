MATCH (e:Employe)-[:A_IBAN]->(i:Iban)<-[:A_IBAN]-(f:Fournisseur)
RETURN e.id_employe AS employe, f.id_fournisseur AS fournisseur, i.value AS iban
LIMIT 50;

MATCH (e:Employe)-[:A_EMAIL]->(email:Email)<-[:A_EMAIL]-(f:Fournisseur)
MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
RETURN e.id_employe AS employe, f.id_fournisseur AS fournisseur, email.value AS email, count(DISTINCT t) AS transactions
LIMIT 50;

MATCH (e:Employe)-[:A_TELEPHONE]->(phone:Telephone)<-[:A_TELEPHONE]-(f:Fournisseur)
MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
RETURN e.id_employe AS employe, f.id_fournisseur AS fournisseur, phone.value AS telephone, count(DISTINCT t) AS transactions
LIMIT 50;

MATCH (e:Employe)-[:A_ADRESSE]->(address:Adresse)<-[:A_ADRESSE]-(f:Fournisseur)
MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
RETURN e.id_employe AS employe, f.id_fournisseur AS fournisseur, address.value AS adresse, count(DISTINCT t) AS transactions
LIMIT 50;

MATCH (e:Employe)-[employeeRel]->(attribute)<-[supplierRel]-(f:Fournisseur)
WHERE type(employeeRel) = type(supplierRel)
  AND type(employeeRel) IN ['A_EMAIL', 'A_TELEPHONE', 'A_ADRESSE', 'A_IBAN', 'A_NOM']
WITH e, f, collect(DISTINCT replace(type(employeeRel), 'A_', '')) AS shared_attributes
WHERE size(shared_attributes) >= 3
MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
RETURN e.id_employe AS employe, f.id_fournisseur AS fournisseur, shared_attributes, count(DISTINCT t) AS transactions
LIMIT 50;

MATCH (e:Employe)-[employeeRel]->(attribute)<-[supplierRel]-(f:Fournisseur)
WHERE type(employeeRel) = type(supplierRel)
  AND type(employeeRel) IN ['A_EMAIL', 'A_TELEPHONE', 'A_ADRESSE', 'A_IBAN', 'A_NOM']
WITH e, f, collect(DISTINCT replace(type(employeeRel), 'A_', '')) AS shared_attributes
WHERE size(shared_attributes) >= 2
MATCH (e)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f)
RETURN e.id_employe AS employe, f.id_fournisseur AS fournisseur, shared_attributes, count(DISTINCT t) AS transactions
LIMIT 50;

MATCH (f:Fournisseur)<-[:VERS]-(t:Transaction)
WHERE toLower(toString(f.is_boite_postale)) = 'true'
WITH f, count(DISTINCT t) AS transaction_count
WHERE transaction_count >= 3
RETURN f.id_fournisseur AS fournisseur, transaction_count
LIMIT 50;

MATCH (e:Employe)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f:Fournisseur)
WHERE toLower(toString(t.cadeau_ou_avantage)) = 'true'
  AND t.date_cadeau IS NOT NULL
  AND trim(toString(t.date_cadeau)) <> ''
WITH e, t, f, duration.inDays(date(t.date_cadeau), date(t.date_transaction)).days AS gift_delay_days
WHERE gift_delay_days >= 0 AND gift_delay_days <= 7
RETURN e.id_employe AS employe, f.id_fournisseur AS fournisseur, t.id_transaction AS transaction, gift_delay_days
LIMIT 50;
