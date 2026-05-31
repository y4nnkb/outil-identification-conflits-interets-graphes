import pandas as pd

from conflict_detector.cleaning.pipeline import clean_tables


def test_clean_tables_normalizes_values_and_removes_orphan_transactions() -> None:
    employes = pd.DataFrame(
        [
            {
                "id_employe": "EMP001",
                "email": " Contact@Example.COM ",
                "telephone": "+33 6 12 34 56 78",
                "adresse": "10 Avenue de Paris",
                "iban": "FR76 1234 5678 9012 3456 7890 185",
                "nom": "Dupont",
            }
        ]
    )
    fournisseurs = pd.DataFrame(
        [
            {
                "id_fournisseur": "FOU001",
                "email": "sales@example.com",
                "telephone": "06 11 22 33 44",
                "adresse": "2 Boulevard Victor",
                "iban": "IBAN INVALIDE",
                "siren": "123 456 789",
                "nom": "Fournisseur",
            }
        ]
    )
    transactions = pd.DataFrame(
        [
            {"id_transaction": "TRX001", "id_employe": "EMP001", "id_fournisseur": "FOU001"},
            {"id_transaction": "TRX002", "id_employe": "EMP999", "id_fournisseur": "FOU001"},
        ]
    )

    cleaned = clean_tables({"employes": employes, "fournisseurs": fournisseurs, "transactions": transactions})

    assert cleaned["employes"].loc[0, "email_norm"] == "contact@example.com"
    assert cleaned["employes"].loc[0, "telephone_norm"] == "0612345678"
    assert cleaned["employes"].loc[0, "adresse_norm"] == "10 AV DE PARIS"
    assert cleaned["fournisseurs"].loc[0, "iban_norm"] == ""
    assert cleaned["fournisseurs"].loc[0, "siren_norm"] == "123456789"
    assert list(cleaned["transactions"]["id_transaction"]) == ["TRX001"]
    assert "email_norm" not in employes.columns


def test_clean_tables_empties_corrupted_shared_attributes() -> None:
    employes = pd.DataFrame(
        [
            {
                "id_employe": "EMP001",
                "email": "email-corrompu",
                "telephone": "abc",
                "adresse": "",
                "iban": "iban-corrompu",
                "nom": "Dupont",
            }
        ]
    )
    fournisseurs = pd.DataFrame(
        [
            {
                "id_fournisseur": "FOU001",
                "email": "fournisseur-corrompu",
                "telephone": "123",
                "adresse": "",
                "iban": "iban-corrompu",
                "siren": "siren-corrompu",
                "nom": "Fournisseur",
            }
        ]
    )
    transactions = pd.DataFrame(
        [{"id_transaction": "TRX001", "id_employe": "EMP001", "id_fournisseur": "FOU001"}]
    )

    cleaned = clean_tables({"employes": employes, "fournisseurs": fournisseurs, "transactions": transactions})

    assert cleaned["employes"].loc[0, "email_norm"] == ""
    assert cleaned["employes"].loc[0, "telephone_norm"] == ""
    assert cleaned["employes"].loc[0, "iban_norm"] == ""
    assert cleaned["fournisseurs"].loc[0, "email_norm"] == ""
    assert cleaned["fournisseurs"].loc[0, "telephone_norm"] == ""
    assert cleaned["fournisseurs"].loc[0, "iban_norm"] == ""
    assert cleaned["fournisseurs"].loc[0, "siren_norm"] == ""
