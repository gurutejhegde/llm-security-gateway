from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.model_client import generate_response

app = FastAPI(title="LLM Security Gateway")


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


@app.get("/")
async def root():
    return {"message": "LLM Security Gateway is running"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    if not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty."
        )

    answer = await generate_response(request.prompt)

    return ChatResponse(response=answer)