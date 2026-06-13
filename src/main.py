import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
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


_compiled_graph = None


def get_graph():
    """Returns the compiled LangGraph workflow."""
    global _compiled_graph

    if _compiled_graph is None:
        _compiled_graph = get_agent_graph()

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
async def chat(request: ChatRequest):
    """Process a chat message using the LangGraph agent."""
    try:
        graph = get_graph()

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
