from datetime import datetime
from fastapi import APIRouter, Query
from typing import Optional
from fetch_functions.utils import get_latest_file
from recommender.recommender import (
    build_recommendation_engine_from_folder,
    recommend_offers
)
from API.schemas.job import JobOfferResponse
import os

router = APIRouter()

ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
PROCESSED_OFFERS_DIR = os.path.join(ROOT, "data/processed_data")
LATEST_FILE = get_latest_file(PROCESSED_OFFERS_DIR)

offers = []
vectorizer = None
offer_vectors = None
texts = []

def load_recommendation_data() -> None:
    global offers, vectorizer, offer_vectors, texts
    offers, vectorizer, offer_vectors, texts = build_recommendation_engine_from_folder(PROCESSED_OFFERS_DIR)
    print(f"✅ Données rechargées depuis {LATEST_FILE} !")

# Chargement initial
load_recommendation_data()

# --- MAPPING DICTIONNAIRE DES TYPES DE CONTRAT ---
CONTRACT_TYPE_EQUIV = {
    "cdi": {"cdi", "permanent", "contract", "fulltime"},
    "cdd": {"cdd", "temporary", "interim"},
    "stage": {"stage", "internship"},
}

@router.get("/search")
def search_offers(
    query: str = Query(..., description="Mot-clé recherché"),
    location: Optional[str] = Query(None, description="Filtre localisation"),
    contract_type: Optional[str] = Query(None, description="Filtre type de contrat"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(20, ge=1, le=100, description="Taille de page"),
):
    # Compose user_query pour la reco
    user_query = query
    if location:
        user_query += f" {location}"
    if contract_type:
        user_query += f" {contract_type}"

    try:
        recos = recommend_offers(
            user_input=user_query,
            offers_vectorizer=vectorizer,
            processed_offer_vectors=offer_vectors,
            processed_offers=offers,
            top_n=150,
            score_threshold=0.45
        )

        # Applique filtrage contract_type/location après reco
        filtered_results = []
        norm_contract = contract_type.strip().lower().replace(" ", "") if contract_type else None
        norm_location = location.strip().lower() if location else None

        # === Filtrage robuste avec mapping dictionnaire ===
        values = CONTRACT_TYPE_EQUIV.get(norm_contract, {norm_contract}) if norm_contract else None

        for o in recos:
            # Filtrage contract_type
            if norm_contract and values:
                offer_type = (o.get("contract_type") or "").strip().lower().replace(" ", "")
                if not any(val in offer_type for val in values):
                    continue
            # Filtrage location
            if norm_location:
                loc = (o.get("location") or "").strip().lower()
                if norm_location not in loc:
                    continue

            description = o.get("description") or ""
            company = o.get("company") or ""
            location_ = o.get("location") or ""
            code_postal = o.get("code_postal") or ""
            salary_min = float(o["salary_min"]) if o.get("salary_min") not in ("", None) else None
            salary_max = float(o["salary_max"]) if o.get("salary_max") not in ("", None) else None
            created_at = o.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            # sinon, c'est déjà un datetime

            filtered_results.append(JobOfferResponse(
                external_id = o.get("external_id", ""),
                title = o.get("title", ""),
                company = company,
                description = description,
                location = location_,
                contract_type = o.get("contract_type"),
                code_postal = code_postal,
                salary_min = salary_min,
                salary_max = salary_max,
                created_at = created_at,
                url = o.get("apply_url", o.get("url", ""))
            ))

        # Limite à 150 offres max après avoir tout filtré
        filtered_results = filtered_results[:150]

        total_count = len(filtered_results)
        start = (page - 1) * page_size
        end = start + page_size

        # Retourne le même format que /jobs pour la pagination
        return {
            "results": filtered_results[start:end],
            "total_count": total_count,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        print(f"Erreur dans /search : {e}")
        raise

