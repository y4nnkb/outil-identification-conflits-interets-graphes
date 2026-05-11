CREATE CONSTRAINT employe_id IF NOT EXISTS FOR (n:Employe) REQUIRE n.id_employe IS UNIQUE;
CREATE CONSTRAINT fournisseur_id IF NOT EXISTS FOR (n:Fournisseur) REQUIRE n.id_fournisseur IS UNIQUE;
CREATE CONSTRAINT transaction_id IF NOT EXISTS FOR (n:Transaction) REQUIRE n.id_transaction IS UNIQUE;
