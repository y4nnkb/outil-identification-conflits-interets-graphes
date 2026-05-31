MATCH p = (e:Employe)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f:Fournisseur)
RETURN p
LIMIT 50;

MATCH p = (e:Employe)-[:A_ADRESSE]->(a:Adresse)<-[:A_ADRESSE]-(f:Fournisseur)
WHERE EXISTS { MATCH (e)-[:A_EFFECTUE]->(:Transaction)-[:VERS]->(f) }
RETURN p
LIMIT 50;

MATCH p = (e:Employe)-[:A_IBAN]->(i:Iban)<-[:A_IBAN]-(f:Fournisseur)
RETURN p
LIMIT 50;

MATCH p = (e:Employe)-[:A_EMAIL]->(email:Email)<-[:A_EMAIL]-(f:Fournisseur)
WHERE EXISTS { MATCH (e)-[:A_EFFECTUE]->(:Transaction)-[:VERS]->(f) }
RETURN p
LIMIT 50;

MATCH p = (e:Employe)-[:A_TELEPHONE]->(phone:Telephone)<-[:A_TELEPHONE]-(f:Fournisseur)
WHERE EXISTS { MATCH (e)-[:A_EFFECTUE]->(:Transaction)-[:VERS]->(f) }
RETURN p
LIMIT 50;

MATCH p = (e:Employe)-[:A_NOM]->(nom:Nom)<-[:A_NOM]-(f:Fournisseur)
WHERE EXISTS { MATCH (e)-[:A_EFFECTUE]->(:Transaction)-[:VERS]->(f) }
RETURN p
LIMIT 50;

MATCH p = (manager:Employe)-[:MANAGE]->(employee:Employe)-[:A_EFFECTUE]->(t:Transaction)-[:VERS]->(f:Fournisseur)
RETURN p
LIMIT 50;

MATCH p = (t:Transaction)-[:RATTACHEE_A_CONTRAT]->(c:Contrat)
RETURN p
LIMIT 50;

MATCH p = (facture:Transaction)-[:FACTURE_COMMANDE]->(commande:Transaction)
RETURN p
LIMIT 50;

MATCH p = (f:Fournisseur)-[:A_SIREN]->(s:Siren)
RETURN p
LIMIT 50;
