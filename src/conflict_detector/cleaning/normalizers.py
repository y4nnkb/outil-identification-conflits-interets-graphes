import re
import unicodedata

<<<<<<< HEAD

def is_empty(value: object) -> bool:
=======
#met en majuscule
def normalize_string(value: object) -> str:
>>>>>>> 9c68acd (Ajout hierarchie employes a 3 niveaux et debut du nettoyage)
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

#enleve les espaces
def normalize_iban(value: object) -> str:
    return re.sub(r"[\s-]", "", normalize_string(value))

#ne garde que les 9 chiffre 
def normalize_siren(value: object) -> str:
    return re.sub(r"\D", "", str(value or ""))[:9]

#ramene au format 0033...
def normalize_phone(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if digits.startswith("33") and len(digits) == 11:
        digits = "0" + digits[2:]
    return digits[:10]

#met en miniscule et retire les espaces
def normalize_email(value: object) -> str:
<<<<<<< HEAD
    if is_empty(value):
=======
    if _is_empty(value):
>>>>>>> 9c68acd (Ajout hierarchie employes a 3 niveaux et debut du nettoyage)
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(char for char in text if unicodedata.category(char) != "Mn")
<<<<<<< HEAD

=======
>>>>>>> 9c68acd (Ajout hierarchie employes a 3 niveaux et debut du nettoyage)

#abrege les mots 
def normalize_address(value: object) -> str:
    text = normalize_string(value)
<<<<<<< HEAD
    replacements = {
        "AVENUE": "AV",
        "BOULEVARD": "BD",
        "IMPASSE": "IMP",
        "CHEMIN": "CHE",
        "NUMERO": "NO",
    }
=======
    replacements = {"AVENUE": "AVE", "BOULEVARD": "BD", "IMPASSE": "IMP", "CHEMIN": "CHE","NUMERO":"N°"}
>>>>>>> 9c68acd (Ajout hierarchie employes a 3 niveaux et debut du nettoyage)
    for source, target in replacements.items():
        text = re.sub(rf"\b{source}\b", target, text)
    return re.sub(r"\s+", " ", text).strip()
