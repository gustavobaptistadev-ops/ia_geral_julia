from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.application.orchestrator.service import ConversationOrchestrator
from app.core.auth import require_api_key

router = APIRouter()
orchestrator = ConversationOrchestrator()


class ConversationRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ConversationResponse(BaseModel):
    conversation_id: str | None
    reply: dict[str, object]


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationRequest,
    _: None = Depends(require_api_key),
) -> ConversationResponse:
    result = orchestrator.handle_message(request.message, None)
    return ConversationResponse(
        conversation_id=request.conversation_id,
        reply=result["reply"],
    )
