import pandas as pd

from conflict_detector.cleaning.normalizers import (
    normalize_address,
    normalize_email,
    normalize_iban,
    normalize_phone,
    normalize_siren,
    normalize_string,
)
from conflict_detector.cleaning.validators import (
    validate_email,
    validate_iban,
    validate_phone,
    validate_required_columns,
    validate_siren,
)


REQUIRED_COLUMNS = {
    "employes": {"id_employe", "email", "telephone", "adresse", "iban", "nom"},
    "fournisseurs": {"id_fournisseur", "email", "telephone", "adresse", "iban", "siren", "nom"},
    "transactions": {"id_transaction", "id_employe", "id_fournisseur"},
}

NORMALIZE_COLUMNS = {
    "employes": {
        "email": ("email_norm", normalize_email),
        "telephone": ("telephone_norm", normalize_phone),
        "adresse": ("adresse_norm", normalize_address),
        "iban": ("iban_norm", normalize_iban),
        "nom": ("nom_norm", normalize_string),
    },
    "fournisseurs": {
        "email": ("email_norm", normalize_email),
        "telephone": ("telephone_norm", normalize_phone),
        "adresse": ("adresse_norm", normalize_address),
        "iban": ("iban_norm", normalize_iban),
        "siren": ("siren_norm", normalize_siren),
        "nom": ("nom_norm", normalize_string),
    },
}

VALIDATE_COLUMNS = {
    "employes": {"email_norm": validate_email, "telephone_norm": validate_phone, "iban_norm": validate_iban},
    "fournisseurs": {
        "email_norm": validate_email,
        "telephone_norm": validate_phone,
        "iban_norm": validate_iban,
        "siren_norm": validate_siren,
    },
}


def clean_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    validate_required_columns(tables, REQUIRED_COLUMNS)
    cleaned = {name: table.copy() for name, table in tables.items()}

    for table_name, columns in NORMALIZE_COLUMNS.items():
        for source_column, (normalized_column, normalizer) in columns.items():
            cleaned[table_name][normalized_column] = cleaned[table_name][source_column].apply(normalizer)

    for table_name, columns in VALIDATE_COLUMNS.items():
        for column, validator in columns.items():
            invalid_rows = ~cleaned[table_name][column].apply(validator)
            cleaned[table_name].loc[invalid_rows, column] = ""

    employee_ids = set(cleaned["employes"]["id_employe"])
    supplier_ids = set(cleaned["fournisseurs"]["id_fournisseur"])
    valid_transactions = (
        cleaned["transactions"]["id_employe"].isin(employee_ids)
        & cleaned["transactions"]["id_fournisseur"].isin(supplier_ids)
    )
    cleaned["transactions"] = cleaned["transactions"].loc[valid_transactions].reset_index(drop=True)
    return cleaned
