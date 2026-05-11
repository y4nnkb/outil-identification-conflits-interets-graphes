from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from conflict_detector.domain.enums import EntityType, ScenarioId, Severity


@dataclass(frozen=True)
class EntityRef:
    id: str
    type: EntityType
    label: str


@dataclass(frozen=True)
class Employe:
    id_employe: str
    prenom: str
    nom: str
    email: str
    telephone: str
    adresse: str
    iban: str
    poste: str
    departement: str
    manager_id: str
    date_embauche: date
    statut: str


@dataclass(frozen=True)
class Fournisseur:
    id_fournisseur: str
    nom: str
    siren: str
    email: str
    telephone: str
    adresse: str
    iban: str
    nom_dirigeant: str
    beneficiaire_effectif: str
    date_creation: date
    pays: str
    statut: str
    type_fournisseur: str
    is_boite_postale: bool
    is_societe_ecran: bool


@dataclass(frozen=True)
class Transaction:
    id_transaction: str
    id_employe: str
    id_fournisseur: str
    date_transaction: date
    montant: Decimal
    devise: str
    type_transaction: str
    description: str
    statut: str
    numero_facture: str
    id_contrat: str
    date_validation: date
    mode_paiement: str
    cadeau_ou_avantage: bool
    date_cadeau: date | None
    montant_cadeau: Decimal


@dataclass
class Alert:
    id: str
    scenario_id: ScenarioId
    entities: list[EntityRef]
    score: float = 0.0
    severity: Severity = Severity.LOW
    evidence: dict[str, Any] = field(default_factory=dict)
    path: list[str] = field(default_factory=list)
    source_rows: list[str] = field(default_factory=list)
