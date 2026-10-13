from fastapi import FastAPI
from pydantic import BaseModel
from backend.agent import SYSTEM_PROMPT, ask_agent
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone, timedelta

from backend.config import (
    OPENROUTER_API_KEY,
    SHOPWARE_URL,
    SHOPWARE_ACCESS_ID,
    SHOPWARE_SECRET_ACCESS_KEY,
)

app = FastAPI(
    title="Shopware AI Support Agent API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str


# Temporary in-memory conversation storage
conversations = {}
conversation_last_used = {}


def cleanup_old_conversations():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    expired_ids = [
        conversation_id
        for conversation_id, last_used in conversation_last_used.items()
        if last_used < cutoff
    ]

    for conversation_id in expired_ids:
        conversations.pop(conversation_id, None)
        conversation_last_used.pop(conversation_id, None)


@app.post("/chat")
def chat(request: ChatRequest):
    cleanup_old_conversations()

    # First: get the existing conversation
    messages = conversations.get(request.conversation_id)

    conversation_last_used[request.conversation_id] = datetime.now(timezone.utc)

    # Second: create a new conversation if it does not exist
    if messages is None:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]
        conversations[request.conversation_id] = messages

    try:
        result = ask_agent(
            request.message,
            messages,
            OPENROUTER_API_KEY,
            SHOPWARE_URL,
            SHOPWARE_ACCESS_ID,
            SHOPWARE_SECRET_ACCESS_KEY,
        )
    except Exception as error:
        print(f"Agent error: {error}")
        return {"error": "internal_error"}

    if isinstance(result, dict):
        return result

    return {
        "reply": result.content,
        "conversation_id": request.conversation_id,
    }
