from enum import StrEnum


class ScenarioId(StrEnum):
    DIRECT_LINK = "direct_link"
    IDENTITY_MATCH = "identity_match"
    GHOST_SUPPLIER = "ghost_supplier"
    SHELL_ENTITY = "shell_entity"
    BRIBES_GIFTS = "bribes_gifts"
    MULTIPLE_HIDDEN_LINKS = "multiple_hidden_links"
    INTERNAL_NETWORK = "internal_network"
    STAR_PATTERN = "star_pattern"
    CIRCULAR_NETWORK = "circular_network"
    FINANCIAL_CONCENTRATION = "financial_concentration"
    DOUBLE_MATCH = "double_match"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EntityType(StrEnum):
    EMPLOYE = "Employe"
    FOURNISSEUR = "Fournisseur"
    TRANSACTION = "Transaction"


class RelationType(StrEnum):
    A_VALIDE = "A_VALIDE"
    PAYE = "PAYE"
    PARTAGE_IBAN = "PARTAGE_IBAN"
    PARTAGE_SIREN = "PARTAGE_SIREN"
    PARTAGE_EMAIL = "PARTAGE_EMAIL"
    PARTAGE_ADRESSE = "PARTAGE_ADRESSE"
    PARTAGE_TELEPHONE = "PARTAGE_TELEPHONE"
    PARTAGE_NOM = "PARTAGE_NOM"
