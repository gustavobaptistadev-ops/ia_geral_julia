from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)

app.include_router(health_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to LifelineOne IA"}
