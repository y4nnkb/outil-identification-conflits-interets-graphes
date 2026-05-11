from dataclasses import dataclass

from conflict_detector.domain.enums import ScenarioId


@dataclass(frozen=True)
class ScenarioDefinition:
    id: ScenarioId
    label: str
    detector: str
    generator: str
    required_tables: tuple[str, ...]


def build_scenario_catalog() -> dict[ScenarioId, ScenarioDefinition]:
    items = [
        ScenarioDefinition(ScenarioId.DIRECT_LINK, "Lien direct", "detect_direct_link", "inject_direct_link", ("employes", "fournisseurs")),
        ScenarioDefinition(ScenarioId.IDENTITY_MATCH, "Correspondance d'identites", "detect_identity_match", "inject_identity_match", ("employes", "fournisseurs")),
        ScenarioDefinition(ScenarioId.GHOST_SUPPLIER, "Fournisseur fantome", "detect_ghost_supplier", "inject_ghost_supplier", ("fournisseurs", "transactions")),
        ScenarioDefinition(ScenarioId.SHELL_ENTITY, "Societe ecran", "detect_shell_entity", "inject_shell_entity", ("employes", "fournisseurs", "transactions")),
        ScenarioDefinition(ScenarioId.BRIBES_GIFTS, "Pots-de-vin et cadeaux", "detect_bribes_gifts", "inject_bribes_gifts", ("employes", "fournisseurs", "transactions")),
        ScenarioDefinition(ScenarioId.MULTIPLE_HIDDEN_LINKS, "Connexions multiples et liens caches", "detect_multiple_hidden_links", "inject_multiple_hidden_links", ("employes", "fournisseurs")),
        ScenarioDefinition(ScenarioId.INTERNAL_NETWORK, "Reseau interne complexe", "detect_internal_network", "inject_internal_network", ("employes", "fournisseurs", "transactions")),
        ScenarioDefinition(ScenarioId.STAR_PATTERN, "Etoile", "detect_star_pattern", "inject_star_pattern", ("employes", "fournisseurs", "transactions")),
        ScenarioDefinition(ScenarioId.CIRCULAR_NETWORK, "Circulaire", "detect_circular_network", "inject_circular_network", ("fournisseurs",)),
        ScenarioDefinition(ScenarioId.FINANCIAL_CONCENTRATION, "Concentration financiere", "detect_financial_concentration", "inject_financial_concentration", ("employes", "fournisseurs", "transactions")),
        ScenarioDefinition(ScenarioId.DOUBLE_MATCH, "Double match", "detect_double_match", "inject_double_match", ("employes", "fournisseurs")),
    ]
    return {item.id: item for item in items}
