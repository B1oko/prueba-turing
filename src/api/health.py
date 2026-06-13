import os

from fastapi import APIRouter

from src.config.settings import get_settings

router = APIRouter()


@router.get("/health")
async def health():
    """Simple check to verify API status."""
    settings = get_settings()
    return {
        "status": "healthy",
        "database_initialized": os.path.exists(settings.CHROMA_DB_PATH),
        "api_key_configured": bool(settings.GEMINI_API_KEY),
    }
