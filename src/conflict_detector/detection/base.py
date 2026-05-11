from dataclasses import dataclass, field
from typing import Any, Protocol

from neo4j import Driver

from conflict_detector.domain.enums import ScenarioId


@dataclass
class DetectionResult:
    scenario_id: ScenarioId
    entities: list[dict[str, str]]
    evidence: dict[str, Any] = field(default_factory=dict)
    path: list[str] = field(default_factory=list)
    source_rows: list[str] = field(default_factory=list)


class DetectionRule(Protocol):
    scenario_id: ScenarioId

    def run(self, driver: Driver) -> list[DetectionResult]:
        ...
