from neo4j import Driver

from conflict_detector.detection.base import DetectionResult


def detect_identity_match(driver: Driver) -> list[DetectionResult]:
    raise NotImplementedError
