import logging
import os
import shutil
import sys

from ingestion.pdf_parser import parse_mtg_rules_pdf
from ingestion.vectorstore import get_vectorstore
from src.config.logging_config import setup_logging
from src.config.settings import get_settings

setup_logging()
logger = logging.getLogger(__name__)

_PDF_PATH = os.path.join("data", "MagicCompRules 20260417.pdf")
_BATCH_SIZE = 200


def main():
    settings = get_settings()

    if not os.path.exists(_PDF_PATH):
        logger.error(
            "Rules PDF not found at %s. Please place the PDF file there.", _PDF_PATH
        )
        sys.exit(1)

    if os.path.exists(settings.CHROMA_DB_PATH):
        try:
            shutil.rmtree(settings.CHROMA_DB_PATH)
            logger.info("Deleted old database directory: %s", settings.CHROMA_DB_PATH)
        except Exception as e:
            logger.warning(
                "Could not delete %s: %s. Attempting to proceed.",
                settings.CHROMA_DB_PATH,
                e,
            )

    logger.info("Parsing rules PDF...")
    documents = parse_mtg_rules_pdf(_PDF_PATH)
    logger.info("Successfully parsed %d rule documents.", len(documents))

    logger.info("Initializing vector store...")
    vectorstore = get_vectorstore()
    total_docs = len(documents)

    logger.info(
        "Adding %d documents to ChromaDB in batches of %d...", total_docs, _BATCH_SIZE
    )
    for i in range(0, total_docs, _BATCH_SIZE):
        batch = documents[i : i + _BATCH_SIZE]
        logger.info(
            "Ingesting batch %d/%d (docs %d to %d)...",
            i // _BATCH_SIZE + 1,
            (total_docs - 1) // _BATCH_SIZE + 1,
            i,
            min(i + _BATCH_SIZE, total_docs),
        )
        try:
            vectorstore.add_documents(batch)
        except Exception as e:
            logger.error("Failed to ingest batch starting at index %d: %s", i, e)
            sys.exit(1)

    logger.info("Ingestion complete. MTG Rules Vector Store is now populated.")


if __name__ == "__main__":
    main()
