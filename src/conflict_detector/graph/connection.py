import os

from neo4j import Driver, GraphDatabase


def get_driver(uri: str | None = None, user: str | None = None, password: str | None = None) -> Driver:
    driver = GraphDatabase.driver(
        uri or os.environ["NEO4J_URI"],
        auth=(user or os.environ["NEO4J_USER"], password or os.environ["NEO4J_PASSWORD"]),
    )
    driver.verify_connectivity()
    return driver
