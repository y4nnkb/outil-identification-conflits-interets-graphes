import pandas as pd

from conflict_detector.cleaning.normalizers import (
    normalize_address,
    normalize_email,
    normalize_iban,
    normalize_phone,
    normalize_siren,
    normalize_string,
)
<<<<<<< HEAD
from conflict_detector.cleaning.validators import validate_iban, validate_required_columns, validate_siren


REQUIRED_COLUMNS = {
=======
from conflict_detector.cleaning.validators import (
    validate_iban,
    validate_required_columns,
    validate_siren,
)


# Colonnes qui doivent exister dans chaque table (sinon erreur de structure)
REQUIRED = {
>>>>>>> 9c68acd (Ajout hierarchie employes a 3 niveaux et debut du nettoyage)
    "employes": {"id_employe", "email", "telephone", "adresse", "iban", "nom"},
    "fournisseurs": {"id_fournisseur", "email", "telephone", "adresse", "iban", "siren", "nom"},
    "transactions": {"id_transaction", "id_employe", "id_fournisseur"},
}

<<<<<<< HEAD
NORMALIZE_COLUMNS = {
=======
# Pour chaque table : colonne d'origine -> (colonne normalisee, fonction)
NORMALIZE_MAP = {
>>>>>>> 9c68acd (Ajout hierarchie employes a 3 niveaux et debut du nettoyage)
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

<<<<<<< HEAD
VALIDATE_COLUMNS = {
=======
# Colonnes normalisees a valider : si invalide -> on vide la cellule 
VALIDATE_MAP = {
>>>>>>> 9c68acd (Ajout hierarchie employes a 3 niveaux et debut du nettoyage)
    "employes": {"iban_norm": validate_iban},
    "fournisseurs": {"iban_norm": validate_iban, "siren_norm": validate_siren},
}


def clean_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
<<<<<<< HEAD
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
=======
    # 1. Verifier que les colonnes obligatoires sont presentes
    validate_required_columns(tables, REQUIRED)

    # 2. Copier les tables pour ne pas modifier l'entree
    cleaned = {name: df.copy() for name, df in tables.items()}

    # 3. Normaliser : creer une colonne _norm pour chaque attribut
    for table_name, columns in NORMALIZE_MAP.items():
        for source_col, (norm_col, func) in columns.items():
            cleaned[table_name][norm_col] = cleaned[table_name][source_col].apply(func)

    # 4. Neutraliser les valeurs invalides (on vide la colonne _norm)
    for table_name, validators in VALIDATE_MAP.items():
        for norm_col, validator in validators.items():
            invalid_mask = ~cleaned[table_name][norm_col].apply(validator)
            cleaned[table_name].loc[invalid_mask, norm_col] = ""

    # 5. Retirer les transactions orphelines
    employe_ids = set(cleaned["employes"]["id_employe"])
    fournisseur_ids = set(cleaned["fournisseurs"]["id_fournisseur"])
    transactions = cleaned["transactions"]
    valid_mask = (
        transactions["id_employe"].isin(employe_ids)
        & transactions["id_fournisseur"].isin(fournisseur_ids)
    )
    cleaned["transactions"] = transactions[valid_mask].reset_index(drop=True)

    # 6. Retourner les tables nettoyees
    return cleaned
>>>>>>> 9c68acd (Ajout hierarchie employes a 3 niveaux et debut du nettoyage)
