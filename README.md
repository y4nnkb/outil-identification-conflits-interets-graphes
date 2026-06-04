# Outil d'identification de conflits d'intérêts via les graphes relationnels

Projet Python de génération, chargement Neo4j, détection Cypher, scoring et export d'alertes de conflits d'intérêts entre employés, fournisseurs et transactions.

L'objectif est de transformer des données transactionnelles en graphe relationnel pour détecter des signaux faibles difficiles à repérer dans des tableaux classiques : attributs partagés, fournisseurs fantômes, sociétés écrans, cadeaux, concentration financière, réseaux internes et relations indirectes.

## Fonctionnalités

- génération contrôlée de données synthétiques ;
- injection de scénarios suspects avec proportions configurables ;
- ajout de bruit réaliste dans les données ;
- nettoyage et normalisation des attributs clés ;
- chargement des noeuds et relations dans Neo4j ;
- création des contraintes et index Neo4j ;
- règles de détection Cypher sans utiliser les labels de vérité terrain ;
- scoring des alertes ;
- exports CSV/JSON ;
- évaluation sur dataset synthétique via `scenario_labels.csv` ;
- requêtes de visualisation Neo4j Browser.

## Structure

```text
.
|-- configs/
|   |-- generation.yml
|   |-- neo4j.yml
|   `-- scoring.yml
|-- queries/
|   |-- browser_style.grass
|   |-- detection.cypher
|   |-- schema.cypher
|   |-- similarity.cypher
|   `-- visualization.cypher
|-- scripts/
|   `-- generate_dataset.py
|-- src/
|   `-- conflict_detector/
|       |-- app/
|       |-- cleaning/
|       |-- detection/
|       |-- domain/
|       |-- generation/
|       |-- graph/
|       |-- io/
|       |-- reporting/
|       |-- scoring/
|       `-- settings.py
|-- tests/
|-- .env.example
|-- docker-compose.yml
|-- pyproject.toml
`-- README.md
```

## Prérequis

- Python 3.11 ou supérieur ;
- Git ;
- Docker Desktop ou Docker Engine ;
- Neo4j lancé via Docker Compose.

## Installation

```powershell
git clone https://github.com/y4nnkb/outil-identification-conflits-interets-graphes.git
cd outil-identification-conflits-interets-graphes

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
```

Sur macOS ou Linux, l'activation de l'environnement virtuel se fait avec :

```bash
source .venv/bin/activate
```

Vérifier l'installation :

```powershell
python -c "import conflict_detector; print('OK')"
```

## Neo4j Avec Docker

Créer le fichier d'environnement local :

```powershell
Copy-Item .env.example .env
```

Sur macOS ou Linux :

```bash
cp .env.example .env
```

Lancer Neo4j :

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

## Pipeline Principal

Générer les CSV synthétiques :

```powershell
conflict-detector generate --config configs/generation.yml
```

Charger Neo4j puis lancer détection, scoring, exports et évaluation :

```powershell
conflict-detector run --data data/generated --output output --reset
```

Résultats générés :

- `output/alerts.csv`
- `output/alerts.json`
- `output/summary.json`
- `output/alerts_by_employee.csv`
- `output/alerts_by_employee.json`
- `output/executive_summary.html`
- `output/report.html`
- `output/scenarios.html`
- `output/employees/`
- `output/suppliers/`
- `output/evaluation.json`

`evaluation.json` n'est produit que si `data/generated/scenario_labels.csv` existe.

## Commandes CLI

```powershell
conflict-detector generate --config configs/generation.yml
conflict-detector check-neo4j
conflict-detector create-schema
conflict-detector load --data data/generated --reset
conflict-detector detect --output output
conflict-detector evaluate --alerts-file output/alerts.json --labels-file data/generated/scenario_labels.csv --output-file output/evaluation.json
conflict-detector run --data data/generated --output output --reset
conflict-detector reset
```

- `generate` génère les CSV, injecte les scénarios, applique le bruit et écrit le manifeste.
- `check-neo4j` vérifie la connexion Neo4j avec `RETURN 1 AS test`.
- `create-schema` crée les contraintes et index Neo4j.
- `load` nettoie les CSV puis charge les noeuds et relations dans Neo4j.
- `detect` exécute les règles Cypher, score les alertes et exporte les résultats.
- `evaluate` compare les alertes avec `scenario_labels.csv` sur un dataset synthétique.
- `run` exécute le pipeline complet.
- `reset` vide le graphe Neo4j sans supprimer les contraintes.

## Données Générées

### Employés

Chaque employé contient notamment :

- `id_employe`
- `prenom`
- `nom`
- `email`
- `telephone`
- `adresse`
- `iban`
- `poste`
- `departement`
- `manager_id`
- `date_embauche`

### Fournisseurs

Chaque fournisseur contient notamment :

- `id_fournisseur`
- `nom`
- `siren`
- `email`
- `telephone`
- `adresse`
- `iban`
- `nom_dirigeant`
- `beneficiaire_effectif`
- `date_creation`
- `is_boite_postale`
- `is_societe_ecran`

### Transactions

Chaque transaction contient notamment :

- `id_transaction`
- `id_employe`
- `id_fournisseur`
- `date_transaction`
- `montant`
- `devise`
- `type_transaction`
- `description`
- `id_contrat`
- `id_commande`
- `date_validation`
- `mode_paiement`
- `cadeau_ou_avantage`
- `date_cadeau`
- `montant_cadeau`

Les transactions sont triées par date après génération.

## Configuration De Génération

Le fichier principal est :

```text
configs/generation.yml
```

Sections importantes :

- `seed` : rend la génération reproductible.
- `output_dir` : dossier de sortie des CSV.
- `date_range` : période des transactions.
- `volumes` : nombre d'employés, fournisseurs et transactions.
- `amounts` : montants généraux, montants de cadeaux et plafond fournisseur fantôme.
- `transaction_parameters` : contrats, factures rattachées à commandes, délais de validation, modes de paiement.
- `scenario_parameters` : paramètres propres aux scénarios.
- `scenario_mix` : pourcentage ou nombre exact de scénarios injectés.
- `noise` : doublons, valeurs manquantes et fautes volontaires.

Quand `count` est renseigné dans `scenario_mix`, il prend le dessus sur `percent`.

Le bruit reste appliqué aux données synthétiques, mais les champs qui portent explicitement un scénario injecté sont protégés. Cela permet de tester les règles de détection sans perdre un scénario uniquement parce que le générateur a vidé ou corrompu son attribut principal.

## Scénarios Injectés

- `direct_link` : adresse partagée entre employé et fournisseur avec transaction associée.
- `identity_match` : email ou téléphone partagé avec transaction associée.
- `ghost_supplier` : fournisseur en boîte postale avec petites transactions vagues.
- `shell_entity` : fournisseur dont le bénéficiaire effectif correspond à un employé.
- `bribes_gifts` : cadeau ou avantage entre 0 et 7 jours avant une transaction.
- `multiple_hidden_links` : au moins trois attributs partagés.
- `internal_network` : manager, employés, fournisseurs et adresse commune.
- `star_pattern` : un employé pivot relié à plusieurs fournisseurs.
- `circular_network` : fournisseurs reliés entre eux par attributs partagés.
- `financial_concentration` : volume financier concentré sur un couple employé/fournisseur.
- `double_match` : deux attributs partagés entre un employé et un fournisseur.

Le générateur verrouille certains champs critiques pendant l'injection pour éviter qu'un scénario ultérieur écrase un scénario déjà créé.

## Nettoyage

Le pipeline de nettoyage crée notamment :

- `email_norm`
- `telephone_norm`
- `adresse_norm`
- `iban_norm`
- `siren_norm`
- `nom_norm`
- `nom_dirigeant_norm` quand `nom_dirigeant` existe

Les valeurs invalides d'email, téléphone, IBAN ou SIREN sont vidées côté colonne normalisée. Le chargeur Neo4j ignore les valeurs vides, `nan`, `nat` et `none`, ce qui évite de relier deux entités uniquement parce que leurs attributs sont manquants.

## Modèle Neo4j

Noeuds principaux :

- `Employe`
- `Fournisseur`
- `Transaction`
- `Email`
- `Telephone`
- `Adresse`
- `Iban`
- `Siren`
- `Nom`
- `Contrat`
- `Commande`
- `Scenario`
- `ScenarioCase`

Relations principales :

- `(:Employe)-[:A_EFFECTUE]->(:Transaction)`
- `(:Transaction)-[:VERS]->(:Fournisseur)`
- `(:Employe)-[:MANAGE]->(:Employe)`
- `(:Employe|Fournisseur)-[:A_EMAIL]->(:Email)`
- `(:Employe|Fournisseur)-[:A_TELEPHONE]->(:Telephone)`
- `(:Employe|Fournisseur)-[:A_ADRESSE]->(:Adresse)`
- `(:Employe|Fournisseur)-[:A_IBAN]->(:Iban)`
- `(:Employe|Fournisseur)-[:A_NOM]->(:Nom)`
- `(:Fournisseur)-[:A_SIREN]->(:Siren)`
- `(:Transaction)-[:RATTACHEE_A_CONTRAT]->(:Contrat)`
- `(:Transaction)-[:REPRESENTE_COMMANDE]->(:Commande)`
- `(:Transaction)-[:FACTURE_COMMANDE]->(:Transaction)`
- `(:Employe|Fournisseur|Transaction)-[:IMPLIQUE_DANS]->(:ScenarioCase)-[:TYPE_SCENARIO]->(:Scenario)`

Les noeuds `Scenario` et `ScenarioCase` servent à visualiser et évaluer les données synthétiques. Les règles de détection n'utilisent pas ces noeuds pour trouver les alertes.

## Détection Et Scoring

Les règles automatisées sont définies dans :

```text
src/conflict_detector/detection/cypher_rules.py
```

Elles couvrent :

- IBAN partagé ;
- email partagé ;
- téléphone partagé ;
- adresse partagée ;
- deux attributs partagés ;
- plusieurs attributs partagés ;
- fournisseur en boîte postale ;
- cadeau ou avantage proche d'une transaction ;
- bénéficiaire effectif correspondant à un employé ;
- motif en étoile ;
- réseau circulaire ;
- concentration financière ;
- réseau interne lié à la hiérarchie manager.

Chaque alerte contient :

- `scenario_id`
- `entities`
- `evidence`
- `path`
- `source_rows`
- `score`
- `severity`

Le scoring est configuré dans :

```text
configs/scoring.yml
```

Le même fichier règle aussi la taille des tableaux du rapport :

```yaml
reporting:
  top_alerts: 20
  top_employees: 15
```

Les seuils de gravité sont volontairement espacés pour que `HIGH` corresponde aux alertes réellement prioritaires.

## Évaluation

L'évaluation compare les alertes détectées avec `scenario_labels.csv`.

- précision : part des alertes sorties qui correspondent à un scénario injecté ;
- rappel : part des scénarios injectés retrouvés par les règles.
- F1-score : moyenne équilibrée entre précision et rappel.

Cette évaluation est utile sur les données synthétiques uniquement. Sur une base client, `scenario_labels.csv` n'existe pas et ne doit pas être utilisé.

## Rapport HTML

Le fichier principal pour une restitution lisible est :

```text
output/report.html
```

La page la plus courte pour une restitution rapide est :

```text
output/executive_summary.html
```

Les libellés métiers des scénarios affichés dans ce rapport viennent de `src/conflict_detector/domain/scenario_catalog.py`.

Il contient :

- les volumes d'alertes par gravité ;
- les employés à investiguer en priorité ;
- le top des alertes avec scénario, score, gravité, entités, lignes sources, explication et preuves ;
- une vue agrégée qui évite de présenter dix alertes séparées sans expliquer qu'elles concernent le même employé.
- des filtres par recherche, gravité et scénario ;
- un tri interactif des colonnes ;
- des boutons pour afficher progressivement plus de lignes ;
- un lien sur chaque employé vers une page dédiée listant toutes ses alertes ;
- un lien sur chaque fournisseur vers une page dédiée listant ses alertes, les employés concernés et les preuves associées ;
- une explication métier de la raison de remontée de chaque alerte.

Le lien `Voir la documentation des scénarios` ouvre `output/scenarios.html`, une page générée depuis le catalogue des scénarios. Elle donne le nom métier, l'identifiant technique, la définition métier et les données utilisées pour chaque scénario.

Les pages `output/employees/<id_employe>.html` détaillent toutes les alertes d'un employé, les fournisseurs concernés, les preuves et la raison de remontée de chaque alerte.

Les pages `output/suppliers/<id_fournisseur>.html` détaillent toutes les alertes d'un fournisseur, les employés concernés, les preuves et la raison de remontée de chaque alerte.

La page `output/executive_summary.html` donne une synthèse courte : volumes d'alertes, employés prioritaires, scénarios les plus fréquents, fournisseurs les plus cités et top 5 des alertes.

Les exports `alerts_by_employee.csv` et `alerts_by_employee.json` permettent de retravailler cette agrégation dans Excel, Power BI ou un autre outil.

## Visualisation Neo4j Browser

Les requêtes utiles sont dans :

```text
queries/visualization.cypher
queries/detection.cypher
```

Neo4j Browser place les noeuds librement à l'écran. Le graphe reste orienté : il faut lire le sens de la flèche sur la relation.

Exemple :

```cypher
MATCH p = (f:Fournisseur)-[:A_SIREN]->(s:Siren)
RETURN p
LIMIT 50;
```

Le fournisseur pointe vers son SIREN.

Pour afficher des noms lisibles dans le graphe :

1. Ouvrir Neo4j Browser.
2. Taper `:style`.
3. Copier le contenu de `queries/browser_style.grass`.
4. Coller ce contenu dans l'éditeur de style Neo4j Browser.

Le style force l'affichage de `display_label`, par exemple `EMP0001 - Lucie Marie` ou `TRX00042 - FACTURE`.

## Démo Client

Préparation avant la démonstration :

Ouvrir Docker Desktop et attendre que l'engine soit démarré, puis lancer :

```powershell
Copy-Item .env.example .env
docker compose up -d neo4j
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
conflict-detector run --data data/generated --output output --reset
```

Si les CSV n'existent pas encore :

```powershell
conflict-detector generate --config configs/generation.yml
conflict-detector run --data data/generated --output output --reset
```

Ouvrir ensuite le rapport HTML :

```text
output/report.html
```

Neo4j Browser reste disponible pour explorer ponctuellement un cas :

```text
http://localhost:7474
```

Identifiants par défaut :

```text
user: neo4j
password: password123
```

Déroulé conseillé :

1. Ouvrir `output/executive_summary.html`.
2. Présenter les volumes, les employés prioritaires et les fournisseurs les plus cités.
3. Ouvrir `output/report.html` pour passer au détail.
4. Montrer le tableau des employés à investiguer en priorité.
5. Cliquer sur un employé pour ouvrir sa page dédiée.
6. Cliquer sur un fournisseur pour ouvrir sa page dédiée.
7. Expliquer que chaque ligne agrège plusieurs alertes autour du même employé ou fournisseur et liste les entités concernées.
8. Utiliser les filtres du rapport pour isoler une gravité ou un scénario.
9. Montrer le top des alertes prioritaires avec score, gravité, entités, lignes sources, explication métier et preuves.
10. Ouvrir `output/alerts_by_employee.csv` si le client veut une vue exportable.
11. Finir par `output/evaluation.json` pour expliquer la performance sur données synthétiques.

Pendant la démo, ne pas présenter `ScenarioCase` comme une aide à la détection. Ces noeuds servent uniquement sur les données synthétiques pour vérifier que les règles retrouvent bien les scénarios injectés. Sur une base client réelle, ils n'existent pas.

Message métier à faire passer :

- les données de départ sont classiques : employés, fournisseurs, transactions ;
- le graphe révèle les liens faibles qui sont difficiles à voir en tableau ;
- les règles Cypher transforment ces liens en alertes ;
- le scoring permet de prioriser les investigations ;
- l'analyste peut ouvrir une alerte et comprendre pourquoi elle est remontée.

## Tests

```powershell
python -m pytest
python -m compileall src scripts tests
```

Les tests couvrent la génération, le bruit, la normalisation, le chargement Neo4j, les contrats des règles, le scoring, l'évaluation et un pipeline de bout en bout sur petit dataset.

## État Actuel

Présent :

- génération synthétique complète ;
- injection de scénarios ;
- bruit configurable ;
- nettoyage et normalisation ;
- chargement Neo4j ;
- contraintes et index ;
- règles Cypher ;
- scoring ;
- exports ;
- évaluation synthétique ;
- style et requêtes de visualisation Neo4j Browser ;
- tests automatisés.

Sur la configuration par défaut, l'évaluation synthétique retrouve actuellement environ 98 % des scénarios injectés. Les écarts restants concernent surtout les scénarios où plusieurs motifs peuvent se recouvrir naturellement dans le graphe.

À améliorer ensuite :

- précision des règles sur les scénarios très larges ;
- visualisation finale des alertes ;
- ergonomie d'analyse par score, scénario et gravité.
