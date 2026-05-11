from neo4j import Driver

from conflict_detector.detection.base import DetectionResult


def detect_internal_network(driver: Driver) -> list[DetectionResult]:
    raise NotImplementedError
