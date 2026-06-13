import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.agent.graph import get_agent_graph
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        logger.info("LangSmith tracing enabled for project '%s'", settings.LANGSMITH_PROJECT)
    else:
        logger.info("LangSmith tracing disabled")
    yield


app = FastAPI(
    title="MTG Chatbot API",
    description="Backend API running the LangGraph agent for Magic: The Gathering rules & cards queries.",
    version="1.0.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str


# Globals to cache the compiled graph and track the currently active API key
_compiled_graph = None
_active_api_key = None


def get_graph(api_key: Optional[str] = None):
    """
    Returns the compiled LangGraph workflow.
    Re-compiles the graph if the API key has changed.
    """
    global _compiled_graph, _active_api_key

    settings = get_settings()
    current_key = api_key or settings.GEMINI_API_KEY

    if _compiled_graph is None or current_key != _active_api_key:
        _compiled_graph = get_agent_graph(api_key=api_key)
        _active_api_key = current_key

    return _compiled_graph


@app.get("/health")
async def health():
    """Simple check to verify API status."""
    settings = get_settings()
    return {
        "status": "healthy",
        "database_initialized": os.path.exists(settings.CHROMA_DB_PATH),
        "api_key_configured": bool(settings.GEMINI_API_KEY),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_gemini_api_key: Optional[str] = Header(None)):
    """
    Process a chat message using the LangGraph agent.
    If the X-Gemini-API-Key header is provided, it overrides the server key.
    """
    try:
        # Get graph, passing the custom API key if provided
        graph = get_graph(x_gemini_api_key)

        # Invoke agent with the user message and session id
        config = {"configurable": {"thread_id": request.session_id}}
        result = graph.invoke(
            {"messages": [HumanMessage(content=request.message)]}, config=config
        )

        # Get response content from the last message
        assistant_msg = result["messages"][-1].content
        return ChatResponse(response=assistant_msg)

    except Exception as e:
        logger.error("Error in /chat endpoint: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
