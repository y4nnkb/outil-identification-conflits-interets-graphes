from conflict_detector.cleaning.normalizers import normalize_iban, normalize_phone, normalize_string


def test_normalize_string_removes_accents() -> None:
    assert normalize_string("écran") == "ECRAN"


def test_normalize_iban_removes_spaces() -> None:
    assert normalize_iban("FR76 1234") == "FR761234"


def test_normalize_phone_keeps_ten_digits() -> None:
    assert normalize_phone("+33 6 12 34 56 78") == "0612345678"
