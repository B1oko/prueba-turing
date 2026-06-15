from contextlib import asynccontextmanager
import logging
import os

from src.config.logging_config import setup_logging

# Configure global logging at startup
setup_logging()
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent.graph import get_agent_graph
from src.api import chat, health, custom_cards
from src.clients import MTGClient, ImagenGenerationClient
from src.config.settings import get_settings
from src.repositories import LocalCustomCardRepository
from src.tools import (
    CreateCustomCardTool,
    SearchCardsTool,
    SearchRulesTool,
    SearchSetsTool,
)
from src.ui.router import setup_ui

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        logger.info("LangSmith tracing enabled for project '%s'", settings.LANGSMITH_PROJECT)
    else:
        logger.warning("LangSmith tracing disabled")

    vectorstore = Chroma(
        collection_name=settings.CHROMA_COLLECTION_NAME,
        persist_directory=settings.CHROMA_DB_PATH,
    )
    mtg_client = MTGClient()
    imagen_client = ImagenGenerationClient(api_key=settings.GEMINI_API_KEY)
    main_llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        temperature=settings.GEMINI_TEMPERATURE,
        google_api_key=settings.GEMINI_API_KEY,
    )

    card_repository = LocalCustomCardRepository()
    app.state.card_repository = card_repository

    tools = [
        SearchRulesTool(vectorstore=vectorstore),
        SearchCardsTool(client=mtg_client),
        SearchSetsTool(client=mtg_client),
        CreateCustomCardTool(llm=main_llm, image_client=imagen_client, repository=card_repository),
    ]
    app.state.graph = get_agent_graph(llm=main_llm, tools=tools)
    logger.info("Application ready")
    yield


app = FastAPI(
    title="MTG Chatbot API",
    description="Backend API running the LangGraph agent for Magic: The Gathering rules & cards queries.",
    version="1.0.0",
    lifespan=lifespan,
)

custom_cards_dir = "custom_cards"
if not os.path.exists(custom_cards_dir):
    os.makedirs(custom_cards_dir)
app.mount("/custom_cards", StaticFiles(directory=custom_cards_dir), name="custom_cards")

if settings.SERVE_FRONTEND:
    setup_ui(app)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(custom_cards.router)
