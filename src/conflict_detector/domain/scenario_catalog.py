from dataclasses import dataclass

from conflict_detector.domain.enums import ScenarioId


@dataclass(frozen=True)
class ScenarioDefinition:
    id: ScenarioId
    label: str
    description: str
    detector: str
    generator: str
    required_tables: tuple[str, ...]


def build_scenario_catalog() -> dict[ScenarioId, ScenarioDefinition]:
    items = [
        ScenarioDefinition(
            ScenarioId.DIRECT_LINK,
            "Lien direct",
            "Un employé et un fournisseur partagent un attribut fort, souvent une adresse, avec des transactions entre eux.",
            "detect_direct_link",
            "inject_direct_link",
            ("employes", "fournisseurs"),
        ),
        ScenarioDefinition(
            ScenarioId.IDENTITY_MATCH,
            "Correspondance d'identités",
            "Un employé et un fournisseur partagent un identifiant personnel ou administratif comme un IBAN, un email ou un téléphone.",
            "detect_identity_match",
            "inject_identity_match",
            ("employes", "fournisseurs"),
        ),
        ScenarioDefinition(
            ScenarioId.GHOST_SUPPLIER,
            "Fournisseur fantôme",
            "Un fournisseur suspect présente des signaux faibles comme une boîte postale, des libellés vagues ou des petites factures répétées.",
            "detect_ghost_supplier",
            "inject_ghost_supplier",
            ("fournisseurs", "transactions"),
        ),
        ScenarioDefinition(
            ScenarioId.SHELL_ENTITY,
            "Société écran",
            "Le bénéficiaire effectif ou dirigeant d'un fournisseur correspond à un employé, ce qui peut masquer une entité contrôlée en interne.",
            "detect_shell_entity",
            "inject_shell_entity",
            ("employes", "fournisseurs", "transactions"),
        ),
        ScenarioDefinition(
            ScenarioId.BRIBES_GIFTS,
            "Pots-de-vin et cadeaux",
            "Un cadeau, avantage ou paiement suspect apparaît peu de temps avant une transaction ou une attribution.",
            "detect_bribes_gifts",
            "inject_bribes_gifts",
            ("employes", "fournisseurs", "transactions"),
        ),
        ScenarioDefinition(
            ScenarioId.MULTIPLE_HIDDEN_LINKS,
            "Connexions multiples et liens cachés",
            "Un employé et un fournisseur partagent plusieurs attributs, ce qui renforce l'hypothèse d'un lien non déclaré.",
            "detect_multiple_hidden_links",
            "inject_multiple_hidden_links",
            ("employes", "fournisseurs"),
        ),
        ScenarioDefinition(
            ScenarioId.INTERNAL_NETWORK,
            "Réseau interne complexe",
            "Plusieurs employés rattachés à une même hiérarchie interagissent avec plusieurs fournisseurs autour d'attributs communs.",
            "detect_internal_network",
            "inject_internal_network",
            ("employes", "fournisseurs", "transactions"),
        ),
        ScenarioDefinition(
            ScenarioId.STAR_PATTERN,
            "Étoile",
            "Un employé pivot concentre des transactions ou des liens vers plusieurs fournisseurs suspects.",
            "detect_star_pattern",
            "inject_star_pattern",
            ("employes", "fournisseurs", "transactions"),
        ),
        ScenarioDefinition(
            ScenarioId.CIRCULAR_NETWORK,
            "Circulaire",
            "Plusieurs fournisseurs se relient entre eux par des attributs communs, formant une boucle potentiellement artificielle.",
            "detect_circular_network",
            "inject_circular_network",
            ("fournisseurs",),
        ),
        ScenarioDefinition(
            ScenarioId.FINANCIAL_CONCENTRATION,
            "Concentration financière",
            "Un volume financier important est concentré sur un couple employé/fournisseur ou sur un faible nombre de contreparties.",
            "detect_financial_concentration",
            "inject_financial_concentration",
            ("employes", "fournisseurs", "transactions"),
        ),
        ScenarioDefinition(
            ScenarioId.DOUBLE_MATCH,
            "Double match",
            "Un employé et un fournisseur partagent exactement plusieurs attributs clés, sans atteindre forcément le seuil des réseaux complexes.",
            "detect_double_match",
            "inject_double_match",
            ("employes", "fournisseurs"),
        ),
    ]
    return {item.id: item for item in items}
