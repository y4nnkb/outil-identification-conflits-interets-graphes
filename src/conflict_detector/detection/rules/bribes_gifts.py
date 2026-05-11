from neo4j import Driver

from conflict_detector.detection.base import DetectionResult


def detect_bribes_gifts(driver: Driver) -> list[DetectionResult]:
    raise NotImplementedError
