from neo4j import Driver

from conflict_detector.detection.base import DetectionResult, DetectionRule


class RuleRegistry:
    def __init__(self) -> None:
        self.rules: list[DetectionRule] = []

    def register(self, rule: DetectionRule) -> None:
        self.rules.append(rule)

    def run_all(self, driver: Driver) -> list[DetectionResult]:
        results: list[DetectionResult] = []
        for rule in self.rules:
            results.extend(rule.run(driver))
        return results
