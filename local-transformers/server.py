"""Local-only OpenAI-compatible chat endpoint backed by Hugging Face Transformers.

Security defaults: loopback bind, required bearer token, no remote custom model code,
no streaming, and bounded generation length. Intended for local development.
"""
from __future__ import annotations

import os
from typing import Literal

import torch
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from transformers import pipeline

MODEL_ID = os.getenv("TRANSFORMERS_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
API_KEY = os.getenv("TRANSFORMERS_API_KEY", "")
MAX_NEW_TOKENS = int(os.getenv("TRANSFORMERS_MAX_NEW_TOKENS", "512"))
if not API_KEY:
    raise RuntimeError("Set TRANSFORMERS_API_KEY before starting the local runtime.")
if not 1 <= MAX_NEW_TOKENS <= 2048:
    raise RuntimeError("TRANSFORMERS_MAX_NEW_TOKENS must be between 1 and 2048.")

auth = HTTPBearer(auto_error=False)
app = FastAPI(title="Hermes Local Transformers Runtime", docs_url=None, redoc_url=None)
generator = None


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=32000)


class ChatRequest(BaseModel):
    model: str = Field(default=MODEL_ID, max_length=200)
    messages: list[Message] = Field(min_length=1, max_length=64)
    max_tokens: int = Field(default=512, ge=1, le=2048)
    temperature: float = Field(default=0.2, ge=0, le=2)


def require_auth(credentials: HTTPAuthorizationCredentials | None = Depends(auth)) -> None:
    if credentials is None or credentials.scheme.lower() != "bearer" or credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.on_event("startup")
def load_model() -> None:
    global generator
    # Do not enable trust_remote_code for arbitrary Hub repositories.
    generator = pipeline(
        task="text-generation",
        model=MODEL_ID,
        device="mps" if torch.backends.mps.is_available() else ("cuda:0" if torch.cuda.is_available() else "cpu"),
        trust_remote_code=False,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok" if generator is not None else "loading", "model": MODEL_ID}


@app.get("/v1/models", dependencies=[Depends(require_auth)])
def models() -> dict:
    return {"object": "list", "data": [{"id": MODEL_ID, "object": "model", "owned_by": "local"}]}


@app.post("/v1/chat/completions", dependencies=[Depends(require_auth)])
def chat_completions(request: ChatRequest) -> dict:
    if request.model != MODEL_ID:
        raise HTTPException(status_code=400, detail=f"Only configured model is available: {MODEL_ID}")
    if generator is None:
        raise HTTPException(status_code=503, detail="Model is still loading")
    messages = [message.model_dump() for message in request.messages]
    try:
        prompt = generator.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        result = generator(
            prompt,
            max_new_tokens=min(request.max_tokens, MAX_NEW_TOKENS),
            do_sample=request.temperature > 0,
            temperature=max(request.temperature, 0.01),
            return_full_text=False,
        )
        answer = result[0]["generated_text"]
    except Exception as exc:
        # Avoid returning paths, environment values, or internal exception details.
        raise HTTPException(status_code=500, detail="Local model inference failed") from exc
    return {
        "id": "chatcmpl-local",
        "object": "chat.completion",
        "model": MODEL_ID,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}, "finish_reason": "stop"}],
    }
