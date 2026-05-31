from conflict_detector.graph.schema import CONSTRAINT_QUERIES, INDEX_QUERIES, create_schema


class FakeResult:
    def consume(self) -> None:
        return None


class FakeSession:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def run(self, query: str) -> FakeResult:
        self.queries.append(query)
        return FakeResult()


class FakeDriver:
    def __init__(self) -> None:
        self.session_instance = FakeSession()

    def session(self) -> FakeSession:
        return self.session_instance


def test_create_schema_runs_constraints_then_indexes() -> None:
    driver = FakeDriver()

    create_schema(driver)

    assert driver.session_instance.queries == CONSTRAINT_QUERIES + INDEX_QUERIES
