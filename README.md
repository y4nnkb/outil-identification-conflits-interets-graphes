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
- Neo4j, pour les futures étapes de graphe
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

## Configuration de la génération

La section `amounts` de `configs/generation.yml` permet de régler :

- `min` et `max` : montants généraux des transactions ;
- `ghost_invoice_max` : montant maximal des petites transactions associées aux fournisseurs fantômes ;
- `gift_min` et `gift_max` : fourchette utilisée pour générer les montants de cadeaux ou avantages.

La section `scenario_parameters` permet de régler les paramètres propres aux scénarios :

- taille des motifs en étoile, circulaires et internes ;
- nombre de transactions associées à certains scénarios ;
- fourchettes de montants pour les sociétés écrans et la concentration financière ;
- fenêtre de dates entre un cadeau et le contrat associé ;
- attributs utilisables pour les liens cachés et les doubles correspondances.

La section `scenario_mix` permet de choisir la proportion ou le nombre exact de scénarios à injecter. Quand `count` est renseigné, il prend le dessus sur `percent`.

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
conflict-detector load --data data/generated
conflict-detector detect --output output
conflict-detector run --data data/generated --output output
conflict-detector reset
```

À ce stade, seule la génération est réellement opérationnelle. Les autres commandes servent de structure pour les prochaines étapes.

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
- fichiers Cypher de base ;
- interface CLI ;
- base de tests.

À compléter :

- chargement réel des CSV dans Neo4j ;
- création complète du graphe ;
- règles de détection Cypher/Python ;
- scoring final des alertes ;
- exports exploitables ;
- interface ou visualisation finale.
