from neo4j import Driver

from conflict_detector.detection.base import DetectionResult


def detect_multiple_hidden_links(driver: Driver) -> list[DetectionResult]:
    raise NotImplementedError
