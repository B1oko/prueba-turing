import logging
from langchain_chroma import Chroma

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


def get_vectorstore(db_path: str | None = None, collection_name: str | None = None):
    """
    Initializes and returns a Chroma vectorstore instance.
    By default, it uses Chroma's built-in local embedding function (ONNX all-MiniLM-L6-v2),
    which runs entirely offline and doesn't require an API key.
    """
    settings = get_settings()
    db_path = db_path or settings.CHROMA_DB_PATH
    collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
    
    logger.info("Initializing vectorstore (Chroma) at db_path: '%s' with collection: '%s'", db_path, collection_name)
    # By omitting the embedding_function argument, LangChain's Chroma wrapper
    # automatically falls back to the default local ONNX MiniLM embedding function.
    vectorstore = Chroma(collection_name=collection_name, persist_directory=db_path)
    logger.info("Vectorstore initialized successfully.")
    return vectorstore
