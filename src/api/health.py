import os
import logging

from fastapi import APIRouter

from src.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health():
    """Simple check to verify API status."""
    logger.debug("Health check endpoint invoked")
    settings = get_settings()
    db_exists = os.path.exists(settings.CHROMA_DB_PATH)
    api_key_configured = bool(settings.GEMINI_API_KEY)
    
    logger.debug(
        "Health check results - database_initialized: %s, api_key_configured: %s",
        db_exists,
        api_key_configured
    )
    
    return {
        "status": "healthy",
        "database_initialized": db_exists,
        "api_key_configured": api_key_configured,
    }
