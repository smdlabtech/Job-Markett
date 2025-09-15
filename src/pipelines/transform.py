import os
import json
import re
import unicodedata
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

from more_itertools.more import chunked

from fetch_functions.utils import save_to_json, load_json_safely, get_latest_file
from logger.logger import warning, info, error
from pipelines.extract import BASE_DIR, RAW_DATA_DIR, RESSOURCES_DIR


# Définition des chemins
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data/processed_data")
INSEE_FILE = os.path.join(RESSOURCES_DIR, "communes_cp.csv")



def normalize_text(text):
    """
    Normalise le texte en supprimant les accents, en mettant en majuscules
    et en gérant certaines transformations spécifiques :
      - tirets/apostrophes → espaces
      - espaces multiples → un seul
      - SAINT → ST
      - arrondissements ou "<Ville> <n>" → "VILLE NN" (zéro-pad)
    """
    if not text or not isinstance(text, str):
        return None

    # Unicode → ASCII, uppercase
    s = unicodedata.normalize("NFD", text) \
                     .encode("ascii", "ignore") \
                     .decode("utf-8") \
                     .upper()

    # Tirets/apostrophes → espaces, condense espaces
    s = re.sub(r"[-']", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # SAINT → ST
    s = re.sub(r"\bSAINT\b", "ST", s)

    # Arrondissements explicites : "9E ARRONDISSEMENT, PARIS" → "PARIS 09"
    m = re.search(
        r"(\d{1,2})[EÈ]M[EÈ]?\s*ARRONDISSEMENT,?\s*(\w+)",
        s,
        re.IGNORECASE
    )
    if m:
        num   = m.group(1).zfill(2)
        ville = m.group(2).upper()
        return f"{ville} {num}"

    # "<Ville> <n>" en fin de chaîne : "PARIS 8" ou "PARIS 08"
    m2 = re.search(r"^(?P<ville>.+?)\s+(?P<num>\d{1,2})$", s)
    if m2:
        ville = m2.group("ville").strip()
        num   = m2.group("num").zfill(2)
        return f"{ville} {num}"

    return s



def load_insee_data(file_path: str) -> tuple[dict, dict]:
    """
    Charge les données INSEE depuis un fichier CSV et retourne deux dictionnaires :
    - code_postal → libellé_d_acheminement
    - nom_commune_normalisé → code_postal
    """
    communes_dict = {}
    communes_nom_dict = {}

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier INSEE introuvable : {file_path}")

    try:
        df = pd.read_csv(file_path, sep=";", dtype=str, encoding="ISO-8859-1")

        required_columns = {"Nom_de_la_commune", "Code_postal", "Libellé_d_acheminement"}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Colonnes manquantes : {required_columns - set(df.columns)}")

        for _, row in df.iterrows():
            commune_norm = row["Nom_de_la_commune"]
            libelle_norm = row["Libellé_d_acheminement"]
            code_postal = row["Code_postal"]

            communes_dict.setdefault(code_postal, libelle_norm)
            communes_nom_dict.setdefault(commune_norm, code_postal)

    except Exception as e:
        error(f"Erreur chargement fichier INSEE : {e}")

    return communes_dict, communes_nom_dict

communes_dict, communes_nom_dict = load_insee_data(INSEE_FILE)


def clean_title(title: str) -> str:
    """
    Nettoie un intitulé de poste :
    - Supprime les mentions du type H/F, F/M/X, etc.
    - Supprime les parenthèses ou symboles orphelins
    - Applique une capitalisation harmonisée (Camel Case)
    """
    if not title:
        return title

    # Supprimer les suffixes comme (H/F), F / M / X, etc.
    pattern = r'\s*\(?[HhFfMmXxDd](\s*[/.\-\\]\s*[HhFfMmXxDd]){1,2}\)?'
    cleaned = re.sub(pattern, '', title)

    # Nettoyage final : parenthèses vides, espaces multiples
    cleaned = re.sub(r'\(\s*\)', '', cleaned)  # parenthèses vides
    cleaned = re.sub(r'^\s*[-/\\|]+\s*', '', cleaned)  # tirets/barres seuls au début
    cleaned = re.sub(r'\s*[-/\\|]+\s*$', '', cleaned)  # tirets / barres seuls en fin
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)  # doubles espaces
    cleaned = cleaned.strip()

    # Harmonisation Camel Case : Data Engineer
    cleaned = cleaned.lower()
    cleaned = ' '.join(word.capitalize() for word in cleaned.split())

    return cleaned


def harmonize_company_name(company_name):
    """
    Normalise le nom de l'entreprise pour harmoniser les variations d'écriture.
    Par exemple, "SNCF Connect", "Sncf connect" et "SNCF connect" seront transformés en une même chaîne,
    ce qui permet de réduire les doublons lors de la déduplication.
    """
    if not company_name or not isinstance(company_name, str):
        return None
    # Normalisation de base : supprime les accents, met en majuscules, remplace les tirets et apostrophes par des espaces, etc.
    normalized = normalize_text(company_name)
    # On peut ajouter ici des règles supplémentaires, par exemple supprimer des suffixes ou mots redondants
    # Exemples (à adapter selon les besoins) :
    # normalized = re.sub(r"\b(INC|CORP|LIMITED|SARL|LLC)\b", "", normalized)
    # normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def match_commune_insee(commune):
    """
    Recherche le code postal à partir d'un nom de commune ou d'un arrondissement.
    1) Normalise en "VILLE NN".
    2) Cherche dans communes_nom_dict.
    3) Cherche dans communes_dict.
    4) Si le key est une ville sans arrondissement (ex: "PARIS"), on prend le premier
       arrondissement trouvé ("PARIS 01") et renvoie son code postal.
    """
    if not commune or not isinstance(commune, str) or not commune.strip():
        return None

    key = normalize_text(commune)
    if not key:
        return None

    # 1) Nom_de_la_commune exact
    cp = communes_nom_dict.get(key)
    if cp:
        return cp

    # 2) Libellé_d_acheminement exact
    cp = communes_dict.get(key)
    if cp:
        return cp

    # 3) Fallback pour ville seule, retourne le 1er arrondissement
    #    ex: key == "PARIS" ou "LYON"
    candidates = [
        (k, v)
        for k, v in communes_nom_dict.items()
        if k.startswith(f"{key} ")
    ]
    if candidates:
        # Trie lexicographique => "PARIS 01" avant "PARIS 02"
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    return None



def clean_description(text):
    """Nettoie la description en supprimant les balises HTML et les espaces inutiles."""
    if not text:
        return None
    text = re.sub(r"<[^>]+>", " ", text).replace("\n", " ").replace("\r", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()



def extract_salary_france_travail(salary_text):
    """
    Extrait le salaire minimum et maximum depuis une chaîne de caractère
    en tenant compte des différents formats et périodes (mensuel, horaire, annuel).

    Cas particulier :
    - Si on détecte "mensuel" ET une valeur au moins égale à 10 000 (ex. 38 000),
      on suppose que les chiffres donnés sont déjà annualisés (ou simplement un
      format erroné dans l'annonce). Dans ce cas, on NE multiplie pas par 12.
    - Sinon, si "mensuel" et < 10 000 (arbitraire), on multiplie par 12.
    - Si "horaire" ou "/h" => on multiplie par 151,67 * 12.
    - Si "annuel" => on ne multiplie pas.
    - Si on trouve "K" quelque part => les valeurs sont en milliers.
    - Si aucun mot-clé de périodicité => fallback :
         - s'il y a un "k" => on garde tel quel (annuel)
         - sinon on multiplie par 12.

    :param salary_text: Chaîne contenant l'information du salaire.
    :return: Tuple (salary_min, salary_max) ou (None, None) si aucune valeur trouvée.
    """

    if not salary_text or any(term in salary_text.lower() for term in ["négocier", "profil", "autre"]):
        return None, None

    # 1) Retirer "sur 12 mois" (ou variante sur 12.0 mois) pour ne garder que la partie avant
    #   Ex: "Mensuel de 38000 Euros à 42000 Euros sur 12 mois" => "Mensuel de 38000 Euros à 42000 Euros"
    #   Mais on conserve en mémoire si on a rencontré ce pattern (au cas où besoin d'une logique dédiée)
    pattern_sur_12 = re.compile(r"sur\s*\d+(?:[.,]\d+)?\s*mois", re.IGNORECASE)

    # On coupe la chaîne avant "sur 12 mois"
    salary_text = pattern_sur_12.split(salary_text)[0].strip()

    # 2) Recherche de toutes les valeurs numériques + unité
    matches = re.findall(r"(\d+(?:[.,]\d+)?)\s*(K|k|k€|Mille|€|Euros?)?", salary_text, flags=re.IGNORECASE)
    if not matches:
        return None, None

    raw_values = []
    for val, unit in matches:
        number = float(val.replace(",", "."))
        raw_values.append((number, unit))

    if not raw_values:
        return None, None

    # 3) Vérifier la présence de 'k' => toutes les valeurs sont en milliers
    text_lower = salary_text.lower()
    has_k = bool(re.search(r"[kK]", text_lower))

    # 4) Conversion en valeurs brutes
    salary_values = []
    for (number, unit) in raw_values:
        if has_k or (unit and unit.lower() in ["k", "k€", "mille"]):
            salary_values.append(number * 1000)
        else:
            salary_values.append(number)

    salary_min_raw, salary_max_raw = min(salary_values), max(salary_values)

    # 5) Détermination de la périodicité
    # Règle :
    #   - mensuel => *12, sauf si la valeur >= 10000 => on suppose déjà annualisée
    #   - horaire => * 151.67 * 12
    #   - annuel => on laisse tel quel
    #   - fallback => s'il y a k => annuel, sinon => *12

    if re.search(r"mensuel|mois", text_lower):
        # Valeurs signalées comme mensuelles
        if salary_min_raw >= 10000:
            # Cas particulier : si la valeur mensuelle est au-dessus d'un gros seuil (10k),
            # on suppose qu'il s'agit en réalité d'un salaire annuel mal labellisé.
            salary_min, salary_max = round(salary_min_raw), round(salary_max_raw)
        else:
            # On considère effectivement que c'est un salaire mensuel
            salary_min = round(salary_min_raw * 12)
            salary_max = round(salary_max_raw * 12)
    elif re.search(r"horaire|/h", text_lower):
        # Horaire => *151.67 => mensuel => *12 => annuel
        salary_min = round(salary_min_raw * 151.67 * 12)
        salary_max = round(salary_max_raw * 151.67 * 12)
    elif re.search(r"annuel|an", text_lower):
        # Annuel => on laisse
        salary_min = round(salary_min_raw)
        salary_max = round(salary_max_raw)
    else:
        # fallback => k => annuel, sinon => mensuel
        if has_k:
            salary_min = round(salary_min_raw)
            salary_max = round(salary_max_raw)
        else:
            salary_min = round(salary_min_raw * 12)
            salary_max = round(salary_max_raw * 12)

    return salary_min, salary_max



def extract_location_france_travail(location_data):
    """
    Extrait la localisation et le code postal pour France Travail :
    - Si `codePostal` est présent, on récupère `Libellé_d_acheminement` depuis INSEE.
    - Si `codePostal` est absent, on nettoie et cherche un match.
    - Si un arrondissement est détecté, on cherche dans `Nom_de_la_commune`.
    - Sinon, on cherche dans `Libellé_d_acheminement`.

    :return localisation normalisée avec le code postal correspondant sinon juste la localisation.
    """
    if not location_data:
        return None, None

    libelle = location_data.get("libelle", "")
    code_post = location_data.get("codePostal")

    # Si le code postal est présent, récupérer `Libellé_d_acheminement`
    if code_post:
        matched_location = communes_dict.get(code_post)
        return matched_location if matched_location else libelle, code_post

    # Nettoyage initial de la localisation
    location_cleaned = normalize_text(libelle)

    # Suppression des numéros isolés au début (ex: "44 - ST NAZAIRE" → "ST NAZAIRE")
    location_cleaned = re.sub(r"^\d+\s*-?\s*", "", location_cleaned).strip()

    # Correction des noms composés (ex: "HAUTS DE SEINE", "ILE DE FRANCE")
    location_cleaned = re.sub(r"\b(DE|DU|DES|LA|LE|LES|AUX)\b\s+", "", location_cleaned)

    # Suppression des valeurs entre parenthèses
    location_cleaned = re.sub(r"\(.*?\)", "", location_cleaned).strip()

    # Suppression des chiffres isolés sauf arrondissements (ex: "92" mais pas "8ème")
    location_cleaned = re.sub(r"\b\d+\b(?!\s*(e|er|ème|ÈME|ER)\b)", "", location_cleaned).strip()

    # Vérification si la localisation contenait un arrondissement avant nettoyage
    match_arrondissement = re.search(r"(\d+)[eè]m[eè]?\s*Arrondissement", libelle, re.IGNORECASE)

    if match_arrondissement:
        # Match avec `Nom_de_la_commune`
        matched_cp = match_commune_insee(location_cleaned)
    else:
        # Match avec `Libellé_d_acheminement`
        matched_cp = match_commune_insee(location_cleaned)

    # Si aucun match trouvé, garder l'original
    return location_cleaned, matched_cp if matched_cp else None



def extract_location_adzuna(location_data):
    """
    Extrait la localisation, le code postal, et le pays pour Adzuna :
      - Si `area` contient 5 valeurs ou plus, teste d'abord la 5ᵉ (index 4), puis la 4ᵉ (index 3) en fallback.
      - Si `area` contient exactement 4 valeurs, teste directement la 4ᵉ (index 3).
      - Si `area` contient exactement 1 valeur, on considère qu'il s'agit uniquement du pays et on retourne (None, None, pays normalisé).
      - Sinon, applique une normalisation et un traitement sur `display_name` pour en extraire la localisation et le code postal.

    :return: Tuple (localisation, code_postal, pays)
    """
    if not location_data:
        return None, None, None

    display_name = location_data.get("display_name", "")
    area_list = location_data.get("area", [])

    # Si la liste area contient exactement 1 élément, c'est uniquement le pays.
    if len(area_list) == 1:
        return None, None, normalize_text(area_list[0])

    # Pour les cas où area_list contient 5 valeurs ou plus, tester en priorité l'index 4 puis l'index 3
    if len(area_list) >= 5:
        location_candidate = normalize_text(area_list[4])
        matched_cp = match_commune_insee(location_candidate)
        if matched_cp:
            country = normalize_text(area_list[0]) if len(area_list) > 0 else None
            return location_candidate, matched_cp, country

        location_candidate = normalize_text(area_list[3])
        matched_cp = match_commune_insee(location_candidate)
        if matched_cp:
            country = normalize_text(area_list[0]) if len(area_list) > 0 else None
            return location_candidate, matched_cp, country

    # Si area_list contient exactement 4 valeurs, tester l'index 3 directement
    elif len(area_list) == 4:
        location_candidate = normalize_text(area_list[3])
        matched_cp = match_commune_insee(location_candidate)
        if matched_cp:
            country = normalize_text(area_list[0]) if len(area_list) > 0 else None
            return location_candidate, matched_cp, country

    # Sinon, utiliser display_name pour déterminer la localisation
    location_cleaned = normalize_text(display_name)

    # Vérifier la présence d'un arrondissement (exemple : "9ème Arrondissement, Lyon")
    match_arrondissement = re.search(r"(\d+)[eè]m[eè]?\s*Arrondissement,?\s*(\w+)", display_name, re.IGNORECASE)
    if match_arrondissement:
        matched_cp = match_commune_insee(location_cleaned)
    else:
        matched_cp = match_commune_insee(location_cleaned)

    first_part = normalize_text(location_cleaned.split(",")[0])
    if not matched_cp and "," in location_cleaned:
        matched_cp = match_commune_insee(first_part)

    # Définir le pays à partir du premier élément de area_list s'il existe
    country = normalize_text(area_list[0]) if area_list and len(area_list) > 0 else None

    return first_part, matched_cp if matched_cp else None, country



def extract_location_jsearch(location_name):
    """
    Recherche le code postal pour une localisation JSearch et récupère le nom du pays correspondant :
      - Si location_name correspond à un code de pays présent dans 'code_pays.json' (comparaison insensible à la casse),
        on considère que seule l'information pays est fournie et on retourne (None, None, nom_du_pays_normalisé).
      - Sinon, on normalise la ville via normalize_text,
        on recherche le code postal en base INSEE via match_commune_insee.

    :param location_name: Nom de la ville ou code de pays.
    :return: Tuple (commune, code_postal, pays)
             - commune: Nom de la ville normalisé, ou None si seule l'information pays est fournie.
             - code_postal: Code postal correspondant si trouvé, sinon None.
             - pays: Nom du pays normalisé (via normalize_text) si trouvé dans le mapping, sinon None.
    """
    if not location_name:
        return None, None, None

    # Charger le dictionnaire des codes pays depuis code_pays.json
    country_dict = {}
    try:
        with open(f'{RESSOURCES_DIR}/code_pays.json', 'r', encoding = 'utf-8') as f:
            country_dict = json.load(f)
    except Exception as _e:
        warning(f"Erreur lors de la lecture du fichier code_pays.json : {_e}")


    # Normaliser la valeur d'entrée et vérifier si elle correspond à un code pays
    code_input = location_name.strip().upper()
    country_codes = {code.strip().upper() for code in country_dict.keys()}
    if code_input in country_codes:
        # Si c'est un code de pays, retourner uniquement le pays normalisé
        # On suppose que country_dict[code] retourne le nom complet du pays
        return None, None, normalize_text(country_dict[code_input])

    # Sinon, traiter location_name comme le nom d'une ville
    commune = normalize_text(location_name)
    matched_cp = match_commune_insee(commune)

    return commune, matched_cp if matched_cp is not None else None, None



def convert_to_timestamp(date_str):
    """
    Convertit une date sous différents formats en un timestamp PostgreSQL-compatible.

    :param date_str: Chaîne de caractères représentant une date.
    :return: Chaîne de caractères au format 'YYYY-MM-DD HH:MI:SS' ou None si la conversion échoue.
    """
    if not date_str:
        return None

    # Liste des formats de dates possibles
    date_formats = [
        "%Y-%m-%dT%H:%M:%SZ",    # Format ISO 8601 (Adzuna, France Travail)
        "%Y-%m-%dT%H:%M:%S.%fZ", # Format ISO avec millisecondes
        "%d/%m/%Y %H:%M:%S",     # Format français avec heure
        "%Y-%m-%d %H:%M:%S",     # Format SQL classique
        "%d-%m-%Y",              # Format court (jour-mois-année)
        "%Y/%m/%d",              # Format alternatif (année/mois/jour)
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")  # Format PostgreSQL
        except ValueError:
            continue

    # Si aucun format ne correspond, on retourne None
    return None



def convert_relative_time(relative_str):
    """
    Convertit une chaîne du format "il y a X jours" ou "il y a X heures"
    en un timestamp PostgreSQL-compatible ("%Y-%m-%d %H:%M:%S").
    """
    import re
    from datetime import datetime, timedelta

    if not relative_str or not isinstance(relative_str, str):
        return None

    # Mettre la chaîne en minuscules et supprimer les espaces superflus
    relative_str = relative_str.lower().strip()

    # Rechercher le pattern "il y a <nombre> <unité>"
    match = re.search(r"il y a (\d+)\s*(jours?|heures?)", relative_str)
    if match:
        number = int(match.group(1))
        unit = match.group(2)
        now = datetime.now()
        if "jour" in unit:
            delta = timedelta(days = number)
        elif "heure" in unit:
            delta = timedelta(hours = number)
        else:
            return None
        created_time = now - delta
        return created_time.strftime("%Y-%m-%d %H:%M:%S")

    return None



def transform_adzuna_jobs(job):
    loc_adz, cp_adz, country = extract_location_adzuna(job.get("location"))
    return {
        "source": "Adzuna",
        "external_id": job.get("id"),
        "title": clean_title(job.get("title")),
        "company": harmonize_company_name(job.get("company", {}).get("display_name")),
        "location": loc_adz,
        "code_postal": cp_adz,
        "longitude": job.get("longitude"),
        "latitude": job.get("latitude"),
        "contract_type": job.get("contract_type"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "sector": job.get("category", {}).get("label"),
        "description": None,
        "country": country,
        "created_at": convert_to_timestamp(job.get("created")),
        "apply_url": job.get("redirect_url")
    }



def transform_france_travail_jobs(job):
    loc_ft, cp_ft = extract_location_france_travail(job.get("lieuTravail"))
    return {
        "source": "France Travail",
        "external_id": job.get("id"),
        "title": clean_title(job.get("intitule")),
        "company": harmonize_company_name(job.get("entreprise", {}).get("nom")),
        "location": loc_ft,
        "code_postal": cp_ft,
        "longitude": job.get("lieuTravail", {}).get("longitude"),
        "latitude": job.get("lieuTravail", {}).get("latitude"),
        "contract_type": job.get("typeContrat"),
        "salary_min": extract_salary_france_travail(job.get("salaire", {}).get("libelle"))[0],
        "salary_max": extract_salary_france_travail(job.get("salaire", {}).get("libelle"))[1],
        "sector": job.get("secteurActiviteLibelle"),
        "description": clean_description(job.get("description")),
        "country": "FRANCE",
        "created_at": convert_to_timestamp(job.get("dateCreation")),
        "apply_url": job.get("origineOffre", {}).get("urlOrigine"),
    }



def transform_jsearch_jobs(job):
    loc_js, cp_js, country = extract_location_jsearch(job.get("job_location"))
    return {
        "source": "JSearch",
        "external_id": clean_title(job.get("job_id")),
        "title": job.get("job_title"),
        "company": harmonize_company_name(job.get("employer_name")),
        "location": loc_js,
        "code_postal": cp_js,
        "longitude": job.get("job_longitude"),
        "latitude": job.get("job_latitude"),
        "contract_type": job.get("job_employment_type"),
        "salary_min": job.get("job_min_salary"),
        "salary_max": job.get("job_max_salary"),
        "sector": None,
        "description": clean_description(job.get("job_description")),
        "country": country,
        "created_at": convert_relative_time(job.get("job_posted_at")),
        "apply_url": job.get("job_apply_link")
    }


TRANSFORMATION_FUNCTIONS = {
        "adzuna": transform_adzuna_jobs,
        "france_travail": transform_france_travail_jobs,
        "jsearch": transform_jsearch_jobs,
}


def process_source_files(source: str, source_dir: str) -> List[Dict[str, Any]]:
    """
    Charge et transforme **uniquement** le dernier fichier JSON d'une source,
    en parallèle sur chaque offre.

    :param source: Clé pour choisir la bonne fonction de transformation
    :param source_dir: Répertoire contenant les fichiers JSON de la source
    :return: Liste d'offres transformées
    """
    if not os.path.exists(source_dir):
        warning(f"Dossier source introuvable pour {source}")
        return []

    # Récupère le chemin du fichier le plus récent
    latest_path = get_latest_file(source_dir)
    if latest_path is None:
        return []

    # Charge les données brutes
    data = load_json_safely(latest_path) or []
    info(f"{len(data)} offres brutes chargées pour {source}")

    # Transforme chaque offre en parallèle
    transformed_jobs = []
    CHUNK_SIZE = 10000

    for i, batch in enumerate(chunked(data, CHUNK_SIZE), start=1):
        info(f"Traitement du batch {i}")
        with ThreadPoolExecutor() as executor:
            results = list(
                executor.map(TRANSFORMATION_FUNCTIONS[source], batch))
            transformed_jobs.extend(results)

    info(f"{len(transformed_jobs)} offres transformées pour {source} "
         f"(fichier: {os.path.basename(latest_path)})")
    return transformed_jobs


def deduplicate_jobs(jobs):
    """
    Supprime les doublons dans une liste de jobs en se basant sur `external_id` et 'source'.
    """
    unique_jobs = {}
    for job in jobs:
        key = (job["external_id"], job["source"])  # Unicité basée sur l'ID et la source
        if key not in unique_jobs:
            unique_jobs[key] = job
    return list(unique_jobs.values())



def deduplicate_after_merge(jobs):
    """
    Supprime les doublons après fusion des sources, en se basant sur `title` et `company`,
    tout en donnant la priorité aux offres issues de France Travail (source="France Travail")
    ou, à défaut, à celles qui contiennent des informations de salaire lorsque disponibles.
    """
    unique_jobs = {}
    for job in jobs:
        # Clé de déduplication : (titre normalisé, entreprise harmonisée)
        title_key = job.get("title", "").strip().lower()
        company_key = harmonize_company_name(job.get("company"))
        key = (title_key, company_key)

        if key not in unique_jobs:
            unique_jobs[key] = job
            continue

        existing = unique_jobs[key]

        # Si la nouvelle offre est de France Travail et que l'existante ne l'est pas → on remplace
        # France travail possède des données plus riches, notamment en termes de salaires et descriptions.
        if job.get("source") == "France Travail" and existing.get("source") != "France Travail":
            unique_jobs[key] = job
            continue

        # Sinon, si l'existante n'a pas de salaire et que la nouvelle en a un → on remplace
        existing_has_salary = existing.get("salary_min") not in (None, "", 0)
        new_has_salary = job.get("salary_min") not in (None, "", 0)
        if not existing_has_salary and new_has_salary:
            unique_jobs[key] = job
            continue

        # Dans tous les autres cas, on conserve l'offre déjà présente
    return list(unique_jobs.values())



def transform_jobs():
    """
    Orchestration du traitement des offres d'emploi :
    - Charge uniquement le dernier fichier JSON de chaque source.
    - Transforme chaque offre en parallèle via ThreadPoolExecutor.
    - Applique déduplication intra et inter-sources.
    - Sauvegarde le résultat final.
    """
    all_transformed_jobs = []

    # Vérifier si le dictionnaire INSEE est bien chargé
    if not communes_dict:
        warning(
            "Attention : Le fichier INSEE est absent ou mal chargé. "
            "Les correspondances de code postal peuvent être incomplètes."
        )

    for source in TRANSFORMATION_FUNCTIONS:
        source_dir = os.path.join(RAW_DATA_DIR, source, "output")

        # Chargement du dernier fichier et transformation des offres en parallèle
        transformed_jobs = process_source_files(source, source_dir)

        # Déduplication intra-source
        unique_jobs = deduplicate_jobs(transformed_jobs)
        info(
            f"Déduplication intra-source terminée pour {source}, "
            f"{len(unique_jobs)} offres uniques."
        )

        all_transformed_jobs.extend(unique_jobs)

    # Déduplication inter-sources après fusion
    final_jobs = deduplicate_after_merge(all_transformed_jobs)
    info(
        f"Déduplication inter-sources appliquée, "
        f"{len(final_jobs)} offres finales."
    )

    # Sauvegarde des offres transformées
    try:
        if final_jobs:
            save_to_json(final_jobs, directory=PROCESSED_DATA_DIR, source="transformed")
            info(f"Transformation terminée : {len(final_jobs)} offres sauvegardées.")

    except Exception as exception:
        error(f"Le fichier transformé n'a pas été sauvegardé - {exception}")

if __name__ == "__main__":
    transform_jobs()