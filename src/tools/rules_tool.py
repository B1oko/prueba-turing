import json
from typing import Any, Optional
from pydantic import BaseModel, PrivateAttr
from langchain_core.tools import BaseTool


class _SearchRulesInput(BaseModel):
    query: str


class SearchRulesTool(BaseTool):
    name: str = "search_rules"
    description: str = (
        "Search the official Magic: The Gathering Comprehensive Rules for rule descriptions, "
        "game phases, mana mechanics, and card interactions."
    )
    args_schema: type[BaseModel] = _SearchRulesInput

    _vectorstore: Any = PrivateAttr()

    def __init__(self, vectorstore, **kwargs):
        super().__init__(**kwargs)
        self._vectorstore = vectorstore

    def _run(self, query: str) -> str:
        try:
            results = self._vectorstore.similarity_search(query, k=5)
            if not results:
                return json.dumps({"rules": [], "message": "No matching rules found in the Comprehensive Rules."})
            rules = []
            for doc in results:
                rule_id = doc.metadata.get("rule_id", "Unknown")
                page = doc.metadata.get("page", "Unknown")
                rules.append({
                    "rule_id": str(rule_id),
                    "page": int(page) if str(page).isdigit() else 0,
                    "text": doc.page_content,
                })
            return json.dumps({"rules": rules})
        except Exception as e:
            return json.dumps({"error": f"Error searching rules database: {str(e)}"})
