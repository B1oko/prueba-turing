import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config.settings import get_settings
from src.api import health, chat

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

app.include_router(health.router)
app.include_router(chat.router)
