"""
Schemas Pydantic pour les réponses d'offres d'emploi de l'API Job Market.
"""
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Literal


class JobOfferResponse(BaseModel):
    """
    Modèle de réponse pour une offre d'emploi retournée par l'API.
    """
    external_id: str
    title: str
    company: str
    description: str
    location: str
    contract_type: Optional[str] = None
    code_postal: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    created_at: Optional[datetime] = None
    url: str