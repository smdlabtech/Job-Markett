import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer


def text_normalization(text: str) -> str:
    """
    Normalise le texte en supprimant les accents, en le passant en minuscules
    et en supprimant les caractères spéciaux.
    """
    if not text or not isinstance(text, str):
        return ""
    # Supprimer les accents
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
    # Mettre en minuscules
    text = text.lower()
    # Supprimer les caractères non alphanumériques (sauf espaces)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Supprimer les espaces multiples
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def prepare_offer_data(offer: dict) -> dict:
    """
    Prépare et nettoie les données d'une offre d'emploi.
    → Normalise chaque valeur str, sauf pour certains champs (ex: 'apply_url').
    → Convertit tout autre type (y compris None) en chaîne vide.
    """
    skip_normalization = {"apply_url"}

    cleaned = {}
    for key, value in offer.items():
        if key in skip_normalization:
            # On garde la valeur brute
            cleaned[key] = value if value else ""
        elif isinstance(value, str) and value:
            cleaned[key] = text_normalization(value)
        else:
            cleaned[key] = ""
    return cleaned


def vectorize_texts(texts: list[str]):
    """
    Vectorise une liste de textes en utilisant TF-IDF.
    Renvoie le vectorizer et la matrice des vecteurs.
    """
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(texts)
    return vectorizer, vectors


def transform_text(vectorizer, text: str):
    """
    Transforme un texte en son vecteur en utilisant le vectorizer existant.
    """
    return vectorizer.transform([text])