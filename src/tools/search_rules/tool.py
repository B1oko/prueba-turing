import json
import logging
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

logger = logging.getLogger(__name__)


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

    def _format(self, results) -> str:
        if not results:
            return json.dumps(
                {
                    "rules": [],
                    "message": "No matching rules found in the Comprehensive Rules.",
                }
            )
        rules = []
        for doc in results:
            rule_id = doc.metadata.get("rule_id", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            rules.append(
                {
                    "rule_id": str(rule_id),
                    "page": int(page) if str(page).isdigit() else 0,
                    "text": doc.page_content,
                }
            )
        return json.dumps({"rules": rules})

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async via _arun")

    async def _arun(self, query: str) -> str:
        logger.info("SearchRulesTool invoked with query: '%s'", query)
        try:
            results = await self._vectorstore.asimilarity_search(query, k=5)
            logger.info("SearchRulesTool found %d matching rules.", len(results))
            return self._format(results)
        except Exception as e:
            logger.error("SearchRulesTool similarity search failed: %s", str(e), exc_info=True)
            return json.dumps({"error": f"Error searching rules database: {str(e)}"})
