from conflict_detector.cleaning.normalizers import normalize_address, normalize_email, normalize_iban, normalize_phone, normalize_string


def test_normalize_string_removes_accents() -> None:
    assert normalize_string("écran") == "ECRAN"


def test_normalize_iban_removes_spaces() -> None:
    assert normalize_iban("FR76 1234") == "FR761234"


def test_normalize_phone_keeps_ten_digits() -> None:
    assert normalize_phone("+33 6 12 34 56 78") == "0612345678"
    assert normalize_phone("+33 (0)7 79 70 56 60") == "0779705660"


def test_normalize_email_lowercases_and_strips() -> None:
    assert normalize_email(" Contact@Example.COM ") == "contact@example.com"


def test_normalize_address_standardizes_common_words() -> None:
    assert normalize_address("10 Avenue de Paris") == "10 AV DE PARIS"
