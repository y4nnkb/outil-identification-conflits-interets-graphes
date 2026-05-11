from neo4j import Driver


def create_constraints(driver: Driver) -> None:
    raise NotImplementedError


def create_indexes(driver: Driver) -> None:
    raise NotImplementedError


def clear_graph(driver: Driver) -> None:
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
