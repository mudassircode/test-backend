from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.openai_service import generate_response

router = APIRouter(prefix="/api/chat", tags=["chat"])

SYSTEM_PROMPT = (
    "You are Meesaq, an AI assistant providing marital guidance and legal information "
    "for Pakistani couples, grounded in Pakistani marital law (MFLO 1961, Guardians and "
    "Wards Act 1890, Dissolution of Muslim Marriages Act 1939) and Sharia references. "
    "Be respectful, culturally sensitive, and clear that you provide information, not "
    "a substitute for a licensed lawyer or counselor."
)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    history = [{"role": m.role, "content": m.content} for m in request.history]
    reply = await generate_response(SYSTEM_PROMPT, request.message, history)
    return ChatResponse(response=reply)
