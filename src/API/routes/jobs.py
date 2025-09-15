from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from API.schemas.job import JobOfferResponse
from API.routes.recommend import offers
import random

router = APIRouter()

# MAPPING ÉLARGI, à adapter selon ton dataset réel
CONTRACT_TYPE_EQUIV = {
    "cdi": {"cdi", "permanent", "contract", "fulltime"},
    "cdd": {"cdd", "temporary", "interim"},
    "stage": {"stage", "internship"},
}

@router.get("/jobs")
def list_jobs(
    contract_type: Optional[str] = Query(None, description="Filtre type de contrat"),
    location: Optional[str] = Query(None, description="Filtre localisation"),
    sort: Optional[str] = Query("date_desc", description="Ordre de tri : date_desc ou date_asc"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(20, ge=1, le=100, description="Taille de page"),
    seed: Optional[str] = Query(None, description="Seed pour randomisation stable"),
):
    filtered_offers = offers

    # --- Filtrage robuste avec dictionnaire ---
    if contract_type:
        norm_contract = contract_type.strip().lower().replace(" ", "")
        values = CONTRACT_TYPE_EQUIV.get(norm_contract, {norm_contract})
        filtered_offers = [
            o for o in filtered_offers
            if o.get("contract_type")
               and any(
                val == (o.get("contract_type") or "").strip().lower().replace(" ", "")
                for val in values
            )
        ]

    if location:
        norm_location = location.strip().lower()
        filtered_offers = [
            o for o in filtered_offers
            if norm_location in (o.get("location") or "").strip().lower()
        ]

    def parse_date(date):
        if isinstance(date, datetime):
            return date
        if isinstance(date, str):
            try:
                return datetime.fromisoformat(date)
            except Exception:
                return datetime(1970, 1, 1)  # fallback
        return datetime(1970, 1, 1)

    if sort == "date_asc":
        filtered_offers = sorted(filtered_offers, key = lambda o: parse_date(o.get("created_at")))
    else:  # date_desc ou toute autre valeur
        filtered_offers = sorted(filtered_offers, key = lambda o: parse_date(o.get("created_at")), reverse = True)

        
    # --- RANDOMISATION STABLE PAR SEED ---
    if seed is not None:
        filtered_offers = filtered_offers.copy()
        random.Random(str(seed)).shuffle(filtered_offers)

    total_count = len(filtered_offers)
    start = (page - 1) * page_size
    end = start + page_size

    results = []
    for o in filtered_offers[start:end]:
        description = o.get("description") or ""
        company = o.get("company") or ""
        location_ = o.get("location") or ""
        code_postal = o.get("code_postal") or ""
        contract_type_val = o.get("contract_type") or ""
        salary_min = float(o["salary_min"]) if o.get("salary_min") not in ("", None) else None
        salary_max = float(o["salary_max"]) if o.get("salary_max") not in ("", None) else None
        created_at = o.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        results.append(JobOfferResponse(
            external_id = o["external_id"],
            title = o["title"],
            company = company,
            description = description,
            location = location_,
            contract_type = contract_type_val,
            code_postal = code_postal,
            salary_min = salary_min,
            salary_max = salary_max,
            created_at = created_at,
            url = o["apply_url"]
        ))

    return {
        "results": results,
        "total_count": total_count,
        "page": page,
        "page_size": page_size
    }
