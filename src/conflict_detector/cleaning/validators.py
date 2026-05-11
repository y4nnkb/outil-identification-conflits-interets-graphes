import re

import pandas as pd


def validate_required_columns(tables: dict[str, pd.DataFrame], required: dict[str, set[str]]) -> None:
    for table_name, columns in required.items():
        missing = columns - set(tables[table_name].columns)
        if missing:
            raise ValueError(f"{table_name}: {sorted(missing)}")


def validate_iban(value: str) -> bool:
    return bool(re.match(r"^[A-Z]{2}[0-9A-Z]{13,32}$", value))


def validate_siren(value: str) -> bool:
    return bool(re.match(r"^\d{9}$", value))
