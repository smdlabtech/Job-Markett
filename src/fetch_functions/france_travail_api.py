import requests
from logger.logger import *
from fetch_functions.config import get_config


# Endpoints de l'API France Travail
TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
OFFRES_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
TOKEN_PARAMS = {"realm": "/partenaire"}


def get_bearer_token():
    """Récupère un Bearer Token pour s'authentifier auprès de l'API France Travail."""

    # Charger les credentials API
    ft_config = get_config()
    IDENTIFIANT_CLIENT = ft_config["france_travail"]["ID"]
    CLE_SECRETE = ft_config["france_travail"]["KEY"]
    SCOPES_OFFRES = ft_config["france_travail"]["SCOPE"]

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": IDENTIFIANT_CLIENT,
        "client_secret": CLE_SECRETE,
        "scope": SCOPES_OFFRES,
    }

    info(f"Récupération du bearer token pour France Travail")
    try:
        response = requests.post(TOKEN_URL, headers=headers, params=TOKEN_PARAMS, data=data)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get("access_token")
    except requests.exceptions.RequestException as e:
        error(f"Erreur lors de la récupération du token : {e}")
        return None


def fetch_jobs_from_france_travail(token, job_code):
    """
    Récupère les offres d'emploi correspondant à un code métier donné.
    Gère la pagination pour récupérer toutes les offres disponibles.
    :param token: Bearer Token pour l'API France Travail.
    :param job_code: Code métier pour la recherche.
    :return: Liste des offres brutes.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    params = {"appellation": job_code, "paysContinent": "01"}

    info(f"Requête envoyée à France Travail à l'url {OFFRES_URL}")
    try:
        # Premier appel pour récupérer le nombre total d'offres
        response = requests.get(OFFRES_URL, headers=headers, params=params)
        response.raise_for_status()

        content_range = response.headers.get("Content-Range")
        total_offres = int(content_range.split("/")[-1]) if content_range else 0

        results = response.json().get("resultats", [])
        info(f"{total_offres} offres trouvées pour le code {job_code}")

        # Pagination : récupérer les offres restantes
        range_start = 150
        while range_start < total_offres and range_start < 3150:
            range_end = range_start + 149
            params["range"] = f"{range_start}-{range_end}"

            pag_response = requests.get(OFFRES_URL, headers=headers, params=params)
            pag_response.raise_for_status()
            results.extend(pag_response.json().get("resultats", []))

            range_start += 150

        return results
    except requests.exceptions.RequestException as e:
        error(f"Erreur lors de la récupération des offres : {e}")
        return []