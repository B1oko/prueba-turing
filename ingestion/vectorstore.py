import logging

from langchain_chroma import Chroma

logger = logging.getLogger(__name__)


def get_vectorstore(
    db_path: str | None = None, collection_name: str | None = None
) -> Chroma:
    if db_path is None or collection_name is None:
        from src.config.settings import get_settings

        settings = get_settings()
        db_path = db_path or settings.CHROMA_DB_PATH
        collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

    logger.info(
        "Initializing vectorstore (Chroma) at '%s' with collection '%s'",
        db_path,
        collection_name,
    )
    # Omitting embedding_function lets LangChain fall back to the local ONNX
    # MiniLM model, which runs entirely offline without an API key.
    vectorstore = Chroma(collection_name=collection_name, persist_directory=db_path)
    logger.info("Vectorstore initialized successfully.")
    return vectorstore
