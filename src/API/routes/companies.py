"""
Routes FastAPI pour la récupération des entreprises distinctes.
"""

from fastapi import APIRouter
from typing import List
from API.schemas.company import CompanyResponse
from pipelines.transform import PROCESSED_DATA_DIR
import os
import json
import glob
import hashlib

router = APIRouter()

@router.get("/companies", response_model=List[CompanyResponse], summary="Liste des entreprises")
def list_companies():
    """
    Endpoint permettant de récupérer la liste des entreprises présentes dans les offres d'emploi.

    - Chaque entreprise a un identifiant unique (hash md5 de son nom).
    - Les doublons et valeurs vides sont exclus.

    Returns:
        List[CompanyResponse]: Liste des entreprises uniques.
    """
    # On charge le dernier fichier processed contenant les offres
    # Même logique que dans recommender.py pour trouver le dernier fichier
    pattern = os.path.join(PROCESSED_DATA_DIR, "transformed_*.json")
    files = [f for f in glob.glob(pattern)]

    if not files:
        return []
    latest_file = max(files, key=os.path.getmtime)
    with open(latest_file, "r", encoding="utf-8") as f:
        offers = json.load(f)

    # Extraire entreprises distinctes
    companies_seen = set()
    companies = []

    for o in offers:
        company_name = o.get("company", "")
        if company_name and company_name not in companies_seen:
            company_id = hashlib.md5(company_name.encode()).hexdigest()
            company_sector = o.get("sector", "")
            companies.append(CompanyResponse(id = company_id, name = company_name, sector = company_sector))
            companies_seen.add(company_name)
    return companies