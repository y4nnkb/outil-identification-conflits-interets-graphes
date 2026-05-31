# Outil d'identification de conflits d'intérêts via les graphes relationnels

Projet Python visant à modéliser les relations entre employés, fournisseurs et transactions afin de préparer l'identification de conflits d'intérêts à l'aide de Neo4j et de requêtes Cypher.

Le projet permet actuellement de générer un jeu de données synthétique contrôlé. Les étapes de chargement Neo4j, de détection automatisée, de scoring complet et de reporting final sont prévues dans l'architecture, mais restent à développer.

## Objectif

L'objectif est de transformer des données transactionnelles en graphe relationnel pour faire ressortir des signaux faibles difficiles à détecter dans des tableaux classiques :

- liens entre employés et fournisseurs ;
- attributs partagés : adresse, IBAN, email, téléphone, SIREN ;
- fournisseurs fantômes ;
- sociétés écrans ;
- cadeaux ou avantages avant validation ;
- concentration financière ;
- réseaux internes ou relations indirectes.

## Structure

```text
.
├── configs/
│   ├── generation.yml
│   ├── neo4j.yml
│   └── scoring.yml
├── queries/
│   ├── schema.cypher
│   ├── detection.cypher
│   └── similarity.cypher
├── scripts/
│   └── generate_dataset.py
├── src/
│   └── conflict_detector/
│       ├── app/
│       ├── cleaning/
│       ├── detection/
│       ├── domain/
│       ├── generation/
│       ├── graph/
│       ├── io/
│       ├── reporting/
│       ├── scoring/
│       └── settings.py
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## Prérequis

- Python 3.11 ou supérieur
- Git
- Docker, pour lancer Neo4j de façon portable
- PowerShell sous Windows

## Installation

```powershell
git clone https://github.com/y4nnkb/outil-identification-conflits-interets-graphes.git
cd outil-identification-conflits-interets-graphes

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

Vérifier l'installation :

```powershell
python -c "import conflict_detector; print('OK')"
```

## Neo4j avec Docker

Créer le fichier d'environnement local :

```powershell
Copy-Item .env.example .env
```

Modifier `NEO4J_PASSWORD` dans `.env`, puis lancer Neo4j :

```powershell
docker compose up -d neo4j
```

Interfaces disponibles :

- Neo4j Browser : `http://localhost:7474`
- Connexion Bolt utilisée par Python : `bolt://localhost:7687`

Identifiants par défaut si `.env` n'est pas modifié :

```text
user: neo4j
password: password123
```

Arrêter Neo4j :

```powershell
docker compose down
```

Supprimer aussi les données Neo4j locales :

```powershell
docker compose down -v
```

Tester la connexion depuis Python :

```powershell
conflict-detector check-neo4j
```

Cette commande charge `.env`, ouvre une connexion Bolt vers Neo4j, exécute `RETURN 1 AS test`, puis ferme la connexion.

Créer les contraintes et index Neo4j :

```powershell
conflict-detector create-schema
```

Vider les données du graphe sans supprimer les contraintes :

```powershell
conflict-detector reset
```

Charger le graphe depuis les CSV générés :

```powershell
conflict-detector load --data data/generated --reset
```

Cette commande lit les CSV, applique la normalisation, crée le schéma si besoin, puis charge les nœuds `Employe`, `Fournisseur`, `Transaction`, les nœuds d'attributs partagés et les relations du graphe.

Les relations créées à ce stade sont :

- `(:Employe)-[:A_EFFECTUE]->(:Transaction)` ;
- `(:Transaction)-[:VERS]->(:Fournisseur)` ;
- `(:Employe)-[:MANAGE]->(:Employe)` ;
- `(:Employe|Fournisseur)-[:A_EMAIL|A_TELEPHONE|A_ADRESSE|A_IBAN]->(:Email|Telephone|Adresse|Iban)` ;
- `(:Fournisseur)-[:A_SIREN]->(:Siren)` ;
- `(:Transaction)-[:RATTACHEE_A_CONTRAT]->(:Contrat)` ;
- `(:Transaction)-[:REPRESENTE_COMMANDE]->(:Commande)` ;
- `(:Transaction)-[:FACTURE_COMMANDE]->(:Transaction)` ;
- `(:Employe|Fournisseur|Transaction)-[:IMPLIQUE_DANS]->(:ScenarioCase)-[:TYPE_SCENARIO]->(:Scenario)`.

Le chargement utilise `UNWIND` par lots : Python envoie une liste de lignes CSV à Neo4j, puis Cypher traite chaque ligne côté base. Cela évite d'envoyer une requête par ligne et permet de charger plusieurs centaines de lignes à la fois.

## Génération des données

La génération est pilotée par :

```text
configs/generation.yml
```

Commande principale :

```powershell
python scripts\generate_dataset.py --config configs\generation.yml
```

Commande équivalente via la CLI :

```powershell
conflict-detector generate --config configs/generation.yml
```

Les fichiers générés sont créés dans `data/generated/` :

- `employes.csv`
- `fournisseurs.csv`
- `transactions.csv`
- `scenario_labels.csv`
- `generation_manifest.json`

`scenario_labels.csv` sert de fichier de contrôle pour savoir quels scénarios ont été injectés. Il n'est pas destiné à être utilisé comme donnée métier.

`generation_manifest.json` conserve les paramètres de génération utilisés, la seed, les volumes demandés, les nombres de lignes générées et les scénarios effectivement injectés.

## Configuration de la génération

La section `amounts` de `configs/generation.yml` permet de régler :

- `min` et `max` : montants généraux des transactions ;
- `ghost_invoice_max` : montant maximal des petites transactions associées aux fournisseurs fantômes ;
- `gift_min` et `gift_max` : fourchette utilisée pour générer les montants de cadeaux ou avantages.

La section `transaction_parameters` permet de régler les paramètres des transactions générées hors scénario :

- proportion de contrats dans le jeu de données ;
- proportion de factures rattachées à une commande existante ;
- délai entre la date de transaction et la date de validation ;
- poids des modes de paiement.

La section `scenario_parameters` permet de régler les paramètres propres aux scénarios :

- taille des motifs en étoile, circulaires et internes ;
- nombre de transactions associées à certains scénarios ;
- fourchettes de montants pour les sociétés écrans et la concentration financière ;
- fenêtre de dates entre un cadeau et le contrat associé ;
- attributs utilisables pour les liens cachés et les doubles correspondances.

La section `scenario_mix` permet de choisir la proportion ou le nombre exact de scénarios à injecter. Quand `count` est renseigné, il prend le dessus sur `percent`.

La section `noise` permet d'ajouter du bruit réaliste dans les CSV générés :

- `duplicate_rate_percent` ajoute des lignes dupliquées dans les tables métier ;
- `missing_value_rate_percent` remplace certains attributs métier par une valeur vide ;
- `typo_rate_percent` corrompt certains attributs métier avec une faute volontaire.

Le bruit ne modifie pas les identifiants techniques comme `id_employe`, `id_fournisseur` ou `id_transaction`, afin de ne pas casser artificiellement les relations de base.

## Nettoyage et valeurs invalides

Avant le chargement dans Neo4j, le pipeline de nettoyage crée des colonnes normalisées comme `email_norm`, `telephone_norm`, `adresse_norm`, `iban_norm` et `siren_norm`.

Les champs vides ou invalides sont traités ainsi :

- un email invalide devient vide dans `email_norm` ;
- un téléphone invalide devient vide dans `telephone_norm` ;
- un IBAN invalide devient vide dans `iban_norm` ;
- un SIREN invalide devient vide dans `siren_norm` ;
- une transaction qui référence un employé ou un fournisseur inexistant est retirée.

Le chargeur Neo4j ignore les valeurs vides, `nan`, `nat` et `none` pour les attributs partagés. Deux IBAN vides, deux emails vides ou deux téléphones vides ne créent donc pas de faux lien commun.

## Données générées

### Employés

Chaque employé contient notamment :

- un identifiant ;
- un nom et prénom ;
- un email ;
- un téléphone ;
- une adresse ;
- un IBAN ;
- un poste ;
- un département ;
- un manager ;
- une date d'embauche.

### Fournisseurs

Chaque fournisseur contient notamment :

- un identifiant ;
- un nom ;
- un SIREN ;
- un email ;
- un téléphone ;
- une adresse ;
- un IBAN ;
- un dirigeant ;
- un bénéficiaire effectif ;
- une date de création ;
- des indicateurs `is_boite_postale` et `is_societe_ecran`.

### Transactions

Chaque transaction contient notamment :

- un identifiant ;
- un employé ;
- un fournisseur ;
- une date de transaction ;
- un montant ;
- un type : `CONTRAT`, `FACTURE` ou `COMMANDE` ;
- un contrat de rattachement ;
- une commande de rattachement éventuelle pour certaines factures ;
- une date de validation ;
- un mode de paiement ;
- des champs liés aux cadeaux ou avantages.

Les transactions sont triées par date après génération.

## Scénarios injectés

Le fichier `configs/generation.yml` permet de régler le pourcentage ou le nombre exact de scénarios injectés :

- `direct_link` : lien direct entre un employé et un fournisseur ;
- `identity_match` : email ou téléphone partagé ;
- `ghost_supplier` : fournisseur en boîte postale avec petites transactions vagues ;
- `shell_entity` : fournisseur marqué comme société écran ;
- `bribes_gifts` : cadeau ou avantage associé à une transaction avant validation ;
- `multiple_hidden_links` : plusieurs attributs partagés ;
- `internal_network` : groupe d'employés et fournisseurs reliés ;
- `star_pattern` : un employé relié à plusieurs fournisseurs ;
- `circular_network` : fournisseurs reliés entre eux par attributs partagés ;
- `financial_concentration` : plusieurs transactions importantes sur un même couple employé/fournisseur ;
- `double_match` : deux attributs partagés entre employé et fournisseur, parcourus parmi toutes les combinaisons possibles d'attributs configurés.

## Commandes CLI

```powershell
conflict-detector generate --config configs/generation.yml
conflict-detector check-neo4j
conflict-detector create-schema
conflict-detector load --data data/generated --reset
conflict-detector detect --output output
conflict-detector run --data data/generated --output output
conflict-detector reset
```

- `generate` génère les CSV, injecte les scénarios, applique le bruit configuré et écrit le manifeste.
- `check-neo4j` vérifie que la connexion à Neo4j fonctionne.
- `create-schema` crée les contraintes et index Neo4j.
- `load` nettoie les CSV puis charge les nœuds et relations dans Neo4j.
- `load --reset` vide le graphe avant de recharger les données.
- `reset` supprime les nœuds et relations du graphe sans supprimer les contraintes.
- `detect`, `run` et `export` restent des commandes de structure pour les prochaines étapes.

## Neo4j et Cypher

Les fichiers du dossier `queries/` préparent les futures étapes Neo4j :

- `schema.cypher` définit les contraintes d'unicité ;
- `similarity.cypher` prépare les liens de similarité entre entités ;
- `detection.cypher` servira aux règles de détection.

## Tests

```powershell
python -m pytest
```

Les tests servent à sécuriser progressivement la génération, les contrats de règles, le scoring et le pipeline.

## État d'avancement

Déjà présent :

- architecture Python installable ;
- configuration YAML ;
- génération d'employés, fournisseurs et transactions ;
- injection de scénarios suspects ;
- bruit configurable sur les données générées ;
- normalisation des principaux attributs métier ;
- chargement des nœuds et relations dans Neo4j ;
- contraintes et index Neo4j ;
- interface CLI ;
- base de tests.

À compléter :

- règles de détection Cypher/Python ;
- scoring final des alertes ;
- exports exploitables ;
- interface ou visualisation finale.
