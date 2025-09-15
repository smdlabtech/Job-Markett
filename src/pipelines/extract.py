from logger.logger import info, error
import os
from fetch_functions.utils import load_json_safely, save_to_json
from fetch_functions.adzuna_api import fetch_jobs_from_adzuna
from fetch_functions.france_travail_api import get_bearer_token, fetch_jobs_from_france_travail
from fetch_functions.jsearch_api import fetch_jobs_from_jsearch


# Déterminer le chemin racine du projet (Job_Market)
BASE_DIR = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Chemins vers les fichiers de ressources
RESSOURCES_DIR = os.path.join(BASE_DIR, "ressources")

# S'assurer que le répertoire des fichiers de ressources esr créé.
os.makedirs(RESSOURCES_DIR, exist_ok=True)

JOB_KEYWORDS_FILE = os.path.join(RESSOURCES_DIR, "job_keywords.json")
APPELLATIONS_FILE = os.path.join(RESSOURCES_DIR, "appellations_hightech.json")

# Chemin vers le répértoire de sauvegarde
RAW_DATA_DIR = os.path.join(BASE_DIR, "data/raw_data")

# S'assurer que le répertoire des données brutes est créé
os.makedirs(RAW_DATA_DIR, exist_ok=True)

# Définir les répertoires des fichiers de sortie pour chaque source de données
ADZUNA_OUTPUT_DIR = os.path.join(RAW_DATA_DIR, "adzuna/output")
FT_OUTPUT_DIR = os.path.join(RAW_DATA_DIR, "france_travail/output")
JS_OUTPUT_DIR = os.path.join(RAW_DATA_DIR, "jsearch/output")

# Charger les queries pour Adzuna et Jsearch
job_keywords = load_json_safely(JOB_KEYWORDS_FILE)
job_queries = job_keywords.get("title", []) if job_keywords else []

# Charger les appellations pour France Travail
appellations = load_json_safely(APPELLATIONS_FILE)
job_appellations = [app["code"] for app in appellations] if appellations else []


def extract_from_adzuna():
    """Orchestration : récupère les offres d'emploi de toutes les APIs et les unifie."""
    info("Début de l'extraction des offres d'emploi depuis Adzuna...")
    # Extraction depuis Adzuna avec plusieurs mots-clés
    adzuna_jobs = []
    for query in job_queries:
        criteria = {"query": query, "results_per_page": 50}
        jobs, _ = fetch_jobs_from_adzuna(criteria)
        adzuna_jobs.extend(jobs)

    try:
        save_to_json(adzuna_jobs, ADZUNA_OUTPUT_DIR, "adzuna")  # Sauvegarde brute
        info(f"{len(adzuna_jobs)} offres extraite de Adzuna")
    except Exception as e:
        error(f'{e}')


def extract_from_ft():
    # Extraction depuis France Travail avec les appellations sélectionnées.
    info("Début de l'extraction des offres d'emploi depuis France Travail...")
    france_travail_jobs = []
    seen_ids = set()
    token = get_bearer_token()
    if token:
        for code in job_appellations:
            jobs = fetch_jobs_from_france_travail(token, code)
            # Gestion des doublons dès à présent, car les codes d'appellations contiennent des offres en correspondance
            # Optimisation nécessaire pour traiter les données brutes dans le DAG transform dans airflow, qui avant
            # cette intégration générait un SIGKILL dû à une surcharge de la mémoire.
            for job in jobs:
                job_id = job.get("id")
                if job_id and job_id not in seen_ids:
                    france_travail_jobs.append(job)
                    seen_ids.add(job_id)

    try:
        save_to_json(france_travail_jobs, FT_OUTPUT_DIR, "france_travail")  # Sauvegarde brute
        info(f"{len(france_travail_jobs)} offres extraite de France Travail")
    except Exception as e:
        error(f'{e}')


def extract_from_jsearch():
    # Extraction depuis JSearch
    info("Début de l'extraction des offres d'emploi depuis JSearch...")
    jsearch_all_jobs = []
    for query in job_queries:
        jsearch_jobs = fetch_jobs_from_jsearch(query, pages = 20, country = "fr")
        jsearch_all_jobs.extend(jsearch_jobs)

    try:
        save_to_json(jsearch_all_jobs, JS_OUTPUT_DIR, "jsearch")  # Sauvegarde brute
        info(f"{len(jsearch_all_jobs)} offres extraite au total")
    except Exception as e:
        error(f'{e}')


def extract_all_jobs():
    """Fonction centrale pour tout orchestrer proprement"""
    extract_from_adzuna()
    extract_from_ft()
    extract_from_jsearch()
    info("[FINAL] Extraction terminée pour toutes les sources")


if __name__ == "__main__":
    extract_all_jobs()