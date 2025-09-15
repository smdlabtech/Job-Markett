"""
Schemas Pydantic pour les réponses d'entreprises de l'API Job Market.
"""
from typing import Optional

from pydantic import BaseModel

class CompanyResponse(BaseModel):
    """
    Modèle de réponse pour une entreprise retournée par l'API.

    Champs :
        id (str) : Hash unique (md5) du nom de l'entreprise.
        name (str) : Nom unique de l'entreprise.
    """
    id: str
    name: str
    sector: Optional[str] = None