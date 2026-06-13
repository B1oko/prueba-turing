import os
import shutil
import sys
import logging
from pdf_parser import parse_mtg_rules_pdf
from vectorstore import get_vectorstore

# Config logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    pdf_path = os.path.join("data", "MagicCompRules 20260417.pdf")
    db_path = "./.chroma_db"
    collection_name = "mtg_rules"
    
    if not os.path.exists(pdf_path):
        logger.error(f"Rules PDF not found at {pdf_path}. Please place the PDF file there.")
        sys.exit(1)
        
    logger.info("Cleaning up existing vector store to start fresh...")
    if os.path.exists(db_path):
        try:
            shutil.rmtree(db_path)
            logger.info(f"Deleted old database directory: {db_path}")
        except Exception as e:
            logger.warning(f"Could not delete {db_path} directory: {e}. Attempting to proceed.")

    logger.info("Parsing rules PDF...")
    documents = parse_mtg_rules_pdf(pdf_path)
    logger.info(f"Successfully parsed {len(documents)} rule documents.")
    
    logger.info("Initializing vector store...")
    vectorstore = get_vectorstore(db_path=db_path, collection_name=collection_name)
    
    # Batch add documents to avoid rate limits/timeouts
    batch_size = 200
    total_docs = len(documents)
    
    logger.info(f"Adding documents to ChromaDB in batches of {batch_size}...")
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        logger.info(f"Ingesting batch {i//batch_size + 1}/{(total_docs-1)//batch_size + 1} (docs {i} to {min(i+batch_size, total_docs)})...")
        try:
            vectorstore.add_documents(batch)
        except Exception as e:
            logger.error(f"Failed to ingest batch starting at index {i}: {e}")
            sys.exit(1)
            
    logger.info("Ingestion complete! MTG Rules Vector Store is now populated.")

if __name__ == "__main__":
    main()
