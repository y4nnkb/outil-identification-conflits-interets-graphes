import re
import unicodedata


def is_empty(value: object) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "nat", "none"}


def normalize_string(value: object) -> str:
    if is_empty(value):
        return ""
    text = str(value).strip().upper()
    text = unicodedata.normalize("NFD", text)
    return "".join(char for char in text if unicodedata.category(char) != "Mn")


def normalize_iban(value: object) -> str:
    return re.sub(r"[\s-]", "", normalize_string(value))


def normalize_siren(value: object) -> str:
    return re.sub(r"\D", "", str(value or ""))[:9]


def normalize_phone(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if digits.startswith("33") and len(digits) == 11:
        digits = "0" + digits[2:]
    return digits[:10]


def normalize_email(value: object) -> str:
    if is_empty(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(char for char in text if unicodedata.category(char) != "Mn")


def normalize_address(value: object) -> str:
    text = normalize_string(value)
    replacements = {
        "AVENUE": "AV",
        "BOULEVARD": "BD",
        "IMPASSE": "IMP",
        "CHEMIN": "CHE",
        "NUMERO": "NO",
    }
    for source, target in replacements.items():
        text = re.sub(rf"\b{source}\b", target, text)
    return re.sub(r"\s+", " ", text).strip()
