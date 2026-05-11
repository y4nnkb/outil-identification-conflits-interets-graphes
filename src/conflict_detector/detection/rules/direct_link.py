from neo4j import Driver

from conflict_detector.detection.base import DetectionResult


def detect_direct_link(driver: Driver) -> list[DetectionResult]:
    raise NotImplementedError
