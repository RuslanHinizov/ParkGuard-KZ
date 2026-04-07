"""
chat.py — AI Chat endpoint (Gemma 4 via Ollama)

POST /api/chat — Streaming chat response
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.ollama_service import DEFAULT_MODEL, is_ollama_available, stream_chat

router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@router.get("/chat/health")
async def chat_health():
    return {
        "ok": await is_ollama_available(),
        "model": DEFAULT_MODEL,
    }


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Gemma 4 ile streaming chat.

    İstek:  { "messages": [{"role": "user", "content": "..."}, ...] }
    Yanıt:  text/plain streaming (chunk chunk metin)
    """
    messages = [
        {"role": m.role, "content": m.content}
        for m in request.messages
    ]

    return StreamingResponse(
        stream_chat(messages),
        media_type="text/plain; charset=utf-8",
    )
