import pandas as pd
from neo4j import Driver


def load_nodes(driver: Driver, tables: dict[str, pd.DataFrame]) -> None:
    raise NotImplementedError


def load_relationships(driver: Driver, tables: dict[str, pd.DataFrame]) -> None:
    raise NotImplementedError


def load_full_graph(driver: Driver, tables: dict[str, pd.DataFrame], reset: bool = False) -> None:
    raise NotImplementedError
