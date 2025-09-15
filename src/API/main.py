"""
Entrée principale de l’API Job Market (FastAPI).

- Monte les routes de recherche d’offres et de récupération des entreprises.
- Configure la documentation interactive.
"""

from fastapi import FastAPI
from .routes.recommend import router as recommend_router
from .routes.companies import router as companies_router
from .routes.jobs import router as jobs_router
from .routes.reload import router as reload_router
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(
    title="Job Market API",
    description="API interne de centralisation et de recommandation d’offres d’emploi multicanal.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9002"],  # Ici tous les ports utilisés et qui exploitent l'API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return """
        <html>
            <head>
                <title>Job Market API</title>
                <style>
                    body { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f8f8fa; }
                    .container { text-align: center; background: #fff; padding: 2rem 3rem; border-radius: 12px; box-shadow: 0 2px 12px #eee; }
                    a { color: #3498db; text-decoration: none; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Bienvenue sur l’API Job Market 🚀</h2>
                    <p>
                        Cette API centralise, expose et recommande des offres d’emploi issues de plusieurs plateformes.<br>
                        Elle fournit des endpoints pour la recherche intelligente et la liste des entreprises.<br>
                        <br>
                        <a href='/docs'>Accéder à la documentation interactive (Swagger)</a>
                    </p>
                </div>
            </body>
        </html>
        """

# On inclut les endpoints
app.include_router(recommend_router)
app.include_router(companies_router)
app.include_router(jobs_router)
app.include_router(reload_router)
