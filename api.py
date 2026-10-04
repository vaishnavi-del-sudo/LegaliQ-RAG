from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from legaliq.rag import answer_with_rag


app = FastAPI(
    title="LegaliQ RAG API",
    description="API for the LawBridge / LegaliQ legal RAG assistant",
    version="1.0.0",
)


# Allow the Next.js frontend to communicate with this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    conversation: list[dict[str, Any]] = []
    language: str = "English"
    model: str = "Gemini 3.8 Flash"


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "LegaliQ RAG API",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/api/lawbridge")
def lawbridge(request: ChatRequest):

    if not request.question.strip():
        return {
            "answer": "Please enter a legal question.",
            "sources": [],
            "retrieved_chunks": 0,
        }

    result = answer_with_rag(
        topic_name="Broad legal query",
        question=request.question,
        model_label=request.model,
        language=request.language,
        history=request.conversation,
    )

    return result