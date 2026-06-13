import os
from langchain_core.tools import tool
from ingestion.vectorstore import get_vectorstore

# Initialize vectorstore lazily
_vectorstore = None

def _get_db():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = get_vectorstore()
    return _vectorstore

@tool
def search_rules(query: str) -> str:
    """
    Search the official Magic: The Gathering Comprehensive Rules for rule descriptions,
    game phases, mana mechanics, and card interactions.
    
    Args:
        query: The search query (e.g., 'first strike', 'combat damage step', 'tap for mana').
        
    Returns:
        A formatted string of the top matching rules with rule IDs and page numbers.
    """
    try:
        db = _get_db()
        # Retrieve top 5 matching rules
        results = db.similarity_search(query, k=5)
        
        if not results:
            return "No matching rules found in the Comprehensive Rules."
            
        formatted_results = []
        for doc in results:
            rule_id = doc.metadata.get("rule_id", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            content = doc.page_content
            formatted_results.append(f"--- Rule {rule_id} (Page {page}) ---\n{content}")
            
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Error searching rules database: {str(e)}"
