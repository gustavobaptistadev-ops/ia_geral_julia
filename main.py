from fastapi import Depends, FastAPI

from app.api.v1 import conversations_router, health_router
from app.core.auth import require_api_key
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)

app.include_router(health_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to LifelineOne IA"}


@app.get("/protected")
async def protected_route(_: None = Depends(require_api_key)) -> dict[str, str]:
    return {"message": "access granted"}
