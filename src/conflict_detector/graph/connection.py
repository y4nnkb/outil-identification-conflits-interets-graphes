import os
from pathlib import Path

from neo4j import Driver, GraphDatabase
from dotenv import load_dotenv


def load_neo4j_env(env_file: str | Path = ".env") -> None:
    load_dotenv(env_file)


def get_env_value(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante: {name}")
    return value


def get_driver(
    uri: str | None = None,
    user: str | None = None,
    password: str | None = None,
    env_file: str | Path = ".env",
) -> Driver:
    load_neo4j_env(env_file)
    driver = GraphDatabase.driver(
        uri or get_env_value("NEO4J_URI"),
        auth=(user or get_env_value("NEO4J_USER"), password or get_env_value("NEO4J_PASSWORD")),
    )
    driver.verify_connectivity()
    return driver


def check_connection(driver: Driver) -> int:
    with driver.session() as session:
        record = session.run("RETURN 1 AS test").single()
    return int(record["test"])
