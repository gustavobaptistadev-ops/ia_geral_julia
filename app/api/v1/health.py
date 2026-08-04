from fastapi import APIRouter, Depends

from app.core.auth import require_api_key

router = APIRouter()


@router.get("/health")
async def health(_: None = Depends(require_api_key)) -> dict[str, str]:
    return {"status": "ok", "service": "lifelineone-ia"}
