import requests
from logger.logger import *
from fetch_functions.config import get_config


def fetch_jobs_from_adzuna(criteria):
    """
    Récupère les offres d'emploi depuis l'API Adzuna en paginant.
    :param criteria: Dictionnaire contenant les critères de recherche (ex: {"query": "Data Engineer", "results_per_page": 50})
    :return: Liste des offres brutes (JSON)
    """

    # Charger les credentials API
    adzuna_config = get_config()
    ADZUNA_BASE_URL = adzuna_config["adzuna"]["BASE_URL"]
    ADZUNA_APP_ID = adzuna_config["adzuna"]["APP_ID"]
    ADZUNA_APP_KEY = adzuna_config["adzuna"]["APP_KEY"]

    page = 1
    country = "fr"
    total_count = 0
    results = []

    while True:
        info(f"Récupération de la page {page} pour '{criteria['query']}'...")

        url = f"{ADZUNA_BASE_URL}/{country}/search/{page}"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "title_only": criteria["query"],
            "results_per_page": criteria["results_per_page"]
        }

        info(f"Requête envoyée à Adzuna à l'url {url}")
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Stocker le nombre total d'annonces
            if page == 1:
                total_count = data.get("count", 0)
                if total_count == 0:
                    warning(f"Aucune offre disponible pour {criteria["query"]}, passage à la requête suivante")
                    break
                info(f"Nombre total d'annonces disponibles : {total_count}")

            # Récupérer les résultats
            page_results = data.get("results", [])
            if not page_results:
                info("Fin de la pagination : plus d'offres disponibles.")
                break  # Arrêter si plus de résultats

            results.extend(page_results)
            page += 1  # Passer à la page suivante

            # Arrêt anticipé si le nombre récupéré est inférieur à `results_per_page`
            if len(page_results) < criteria["results_per_page"]:
                info("Fin de la pagination (moins de résultats que demandés).")
                break

        except requests.exceptions.RequestException as e:
            error(f"Erreur API Adzuna : {e}")
            break

    return results, total_count
