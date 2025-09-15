import json
from logger.logger import *
from datetime import datetime


def save_to_json(data, directory, source, filename=None):
    """
    Sauvegarde les données JSON dans le répertoire spécifié.

    :param data : Données à sauvegarder (liste ou dictionnaire).
    :param directory : Dossier où stocker le fichier (ex: 'data/raw_data/adzuna' ou 'data/processed_data').
    :param source : Source de laquelle on sauvegarde la donnée, ici une API parmi celles traitées.
    :param filename : Nom du fichier (optionnel, sinon timestamp utilisé).
    """
    if not data:
        warning(f"Aucune donnée à sauvegarder dans {directory}.")
        return

    # Définir le dossier de sortie de manière dynamique
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    output_dir = os.path.join(BASE_DIR, directory)
    os.makedirs(output_dir, exist_ok=True)

    # Générer un nom de fichier si non fourni
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_{timestamp}.json"

    output_path = os.path.join(output_dir, filename)

    try:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        info(f"Données sauvegardées dans {output_path}")
    except Exception as e:
        error(f"Erreur lors de la sauvegarde dans {directory} : {e}")


def sanitize_filename(filename) :
    """
    Nettoie un nom de fichier en supprimant ou remplaçant les caractères invalides afin
    d'avoir un format lisible et compatible.

    :param filename: Le nom de fichier à nettoyer.
    :return: Un nom de fichier valide.
    """

    # Nettoie et supprime les caractères invalides
    filename = re.sub(r'\s*/\s*', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = re.sub(r'[\\:*?"<>|]', '', filename)

    return filename


def remove_duplicates(jobs):
    """
    Supprime les doublons parmi les offres d'emploi des 3 API.
    - Utilise 'external_id' comme clé principale.
    - Si 'external_id' est absent, utilise ('title', 'company', 'location').

    :param jobs: Liste des offres d'emploi issues de plusieurs sources.
    :return: Liste filtrée sans doublons.
    """
    unique_jobs = []
    seen_ids = set()  # Ensemble des external_id déjà vu
    seen_combinations = set()  # Ensemble des (title, company, location) déjà vu

    for job in jobs:
        external_id = job.get("external_id")
        unique_key = (job.get("title"), job.get("company"))

        # Vérifier si l'external_id existe déjà
        if external_id and external_id in seen_ids:
            continue  # Offre dupliquée, on l'ignore

        # Vérifier si l'offre existe déjà sous une autre API sans external_id
        if not external_id and unique_key in seen_combinations:
            continue  # Offre dupliquée sans ID unique

        # Ajouter à la liste unique
        unique_jobs.append(job)

        # Ajouter aux ensembles de suivi
        if external_id:
            seen_ids.add(external_id)
        else:
            seen_combinations.add(unique_key)

    info(f"Nombre d'offres après suppression des doublons : {len(unique_jobs)}")
    return unique_jobs



def remove_no_results_terms(job_titles_path, no_results_queries):
    """
    Supprime les termes du fichier job_keywords.json qui n'ont retourné aucun résultat.

    :param job_titles_path: Chemin vers le fichier job_keywords.json.
    :param no_results_queries: Liste des termes sans résultat.
    """
    try:
        # Charger les données actuelles du fichier job_keywords.json
        with open(job_titles_path, "r", encoding="utf-8") as file:
            job_titles = json.load(file)

        # Supprimer les termes sans résultat
        job_titles["title"] = [term for term in job_titles.get("title", []) if term not in no_results_queries]

        # Écrire les données mises à jour dans le fichier job_keywords.json
        with open(job_titles_path, "w", encoding="utf-8") as file:
            json.dump(job_titles, file, indent=4, ensure_ascii=False)

    except Exception as e:
        error(f"Erreur lors de la mise à jour de {job_titles_path} : {e}")



def load_json_safely(file_path):
    """Charge un fichier JSON et gère les erreurs en cas d'échec."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        error(f"Erreur lors de la lecture du fichier {file_path} : {e}")
        return None  # Retourne `None` au lieu de lever une exception



def get_latest_file(directory):
    """
    Récupère le fichier JSON le plus récent dans le répertoire spécifié.
    """
    try:
        files = [f for f in os.listdir(directory) if f.endswith(".json")]
        if not files:
            warning("Aucun fichier trouvé dans le dossier de transformation.")
            return None

        latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
        return os.path.join(directory, latest_file)

    except Exception as e:
        error("Erreur lors de la recherche du fichier : {}".format(e))
        return None