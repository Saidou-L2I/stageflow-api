import logging

from fastapi import FastAPI

from app.api.routes.applications import router as applications_router
from app.api.routes.auth import router as auth_router
from app.api.routes.offers import router as offers_router
from app.api.routes.users import router as users_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.middlewares.request_id import RequestIDMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "StageFlow - API interne de gestion securisee des stages data : offres, "
        "candidatures, validations pedagogiques et avis des encadrants."
    ),
    version="1.0.0",
)

# Middlewares (l'ordre d'ajout determine l'ordre d'execution "en oignon")
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)

# Gestion centralisee des erreurs metier
register_exception_handlers(app)

# Routes
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(offers_router)
app.include_router(applications_router)


@app.get("/health", tags=["Sante"], summary="Verifie que l'API est operationnelle")
async def health_check() -> dict:
    return {"status": "healthy"}


@app.get("/", tags=["Sante"], summary="Racine de l'API")
async def read_root() -> dict:
    return {"message": f"Bienvenue sur {settings.APP_NAME}"}
