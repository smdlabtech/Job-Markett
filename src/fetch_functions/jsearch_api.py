import requests
from logger.logger import *
from fetch_functions.config import get_config


def fetch_jobs_from_jsearch(query, country, pages):
    """
    Récupère les offres d'emploi depuis l'API JSearch avec pagination.

    :param query: Titre du job recherché.
    :param country: Code pays (ex: 'fr' pour France).
    :param pages: Nombre de pages à récupérer.
    :return: Liste des offres d'emploi brutes.
    """

    # Charger les credentials API
    jsearch_config = get_config()
    JSEARCH_BASE_URL = jsearch_config["jsearch"]["BASE_URL"]
    JSEARCH_HOST = jsearch_config["jsearch"]["HOST"]
    JSEARCH_KEY = jsearch_config["jsearch"]["APP_KEY"]


    url = f"{JSEARCH_BASE_URL}"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": JSEARCH_HOST,
        "x-rapidapi-key": JSEARCH_KEY,
    }

    all_jobs = []

    for page in range(1, pages + 1):
        params = {
            "query": f"{query} in {country}",
            "country": country,
            "page": page,
            "num_pages": pages,
            "date_posted": "all"
        }

        info(f"Requête envoyé à JSearch à l'url {url}")
        try:
            response = requests.get(url, headers = headers, params = params)
            response.raise_for_status()
            data = response.json()

            jobs = data.get("data", [])
            info(f"Page {page}/{pages} - {len(jobs)} offres récupérées pour '{query}'.")
            all_jobs.extend(jobs)

            # Si aucune offre retournée sur une page, on arrête la pagination
            if not jobs:
                warning(f"Aucune offre retournée sur la page {page}")
                break

        except requests.exceptions.RequestException as e:
            error(f"Erreur API JSearch : {e}")
            break

    return all_jobs
