from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api import chat, health
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
        logger.info(
            "LangSmith tracing enabled for project '%s'", settings.LANGSMITH_PROJECT
        )
    else:
        logger.info("LangSmith tracing disabled")
    yield


settings = get_settings()

app = FastAPI(
    title="MTG Chatbot API",
    description="Backend API running the LangGraph agent for Magic: The Gathering rules & cards queries.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files for custom generated card mockups
custom_cards_dir = "custom_cards"
if not os.path.exists(custom_cards_dir):
    os.makedirs(custom_cards_dir)
app.mount("/custom_cards", StaticFiles(directory=custom_cards_dir), name="custom_cards")

from src.ui.router import setup_ui

# Initialize integrated UI routing if configured
if settings.SERVE_FRONTEND:
    setup_ui(app)

app.include_router(health.router)
app.include_router(chat.router)
