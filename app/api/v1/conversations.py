from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.application.orchestrator.service import ConversationOrchestrator
from app.application.persistence.service import PersistenceService
from app.core.auth import require_api_key
from app.core.config import settings
from app.infrastructure.repositories.memory_repository import InMemoryConversationRepository
from app.infrastructure.repositories.postgres_repository import PostgresConversationRepository, PsycopgExecutor

router = APIRouter()


def build_orchestrator() -> ConversationOrchestrator:
    if not settings.enable_postgres_persistence:
        return ConversationOrchestrator(PersistenceService(InMemoryConversationRepository()))

    repository = PostgresConversationRepository(PsycopgExecutor(settings.postgres_url))
    return ConversationOrchestrator(PersistenceService(repository))


orchestrator = build_orchestrator()


class ConversationRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ConversationResponse(BaseModel):
    conversation_id: str | None
    reply: dict[str, object]


class ConversationResetResponse(BaseModel):
    reset: bool
    provider: str | None = None
    detail: str | None = None


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationRequest,
    _: None = Depends(require_api_key),
) -> ConversationResponse:
    result = orchestrator.handle_message(request.message, None, conversation_id=request.conversation_id)
    state = result["state"]
    return ConversationResponse(
        conversation_id=state.conversation_id,
        reply=result["reply"],
    )


@router.delete("/conversations", response_model=ConversationResetResponse)
async def reset_conversations(_: None = Depends(require_api_key)) -> ConversationResetResponse:
    if settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conversation reset is disabled in production.",
        )

    result = orchestrator.reset_conversations()
    return ConversationResetResponse(**result)
