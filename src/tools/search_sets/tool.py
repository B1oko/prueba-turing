import json
import logging
from typing import Any, Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

from src.clients.mtg_client import ISetSearch

logger = logging.getLogger(__name__)


class _SearchSetsInput(BaseModel):
    name: Optional[str] = None
    block: Optional[str] = None


class SearchSetsTool(BaseTool):
    name: str = "search_sets"
    description: str = (
        "Search for Magic: The Gathering sets (editions). "
        "Args: name (set name, e.g. 'Innistrad'), block (block name, e.g. 'Ravnica')."
    )
    args_schema: type[BaseModel] = _SearchSetsInput

    _client: Any = PrivateAttr()

    def __init__(self, client: ISetSearch, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async via _arun")

    async def _arun(
        self,
        name: Optional[str] = None,
        block: Optional[str] = None,
    ) -> str:
        if not any([name, block]):
            return json.dumps({"error": "Please provide at least one filter: name or block."})
        try:
            sets = await self._client.search_sets(name=name, block=block)
        except Exception as e:
            logger.error("SearchSetsTool MTG API search failed: %s", str(e), exc_info=True)
            return json.dumps({"error": f"Error connecting to MTG API: {e}"})

        if not sets:
            return json.dumps(
                {
                    "sets": [],
                    "message": "No sets found matching the specified criteria.",
                }
            )

        result = [
            {
                "name": s.get("name"),
                "code": s.get("code"),
                "type": s.get("type"),
                "block": s.get("block"),
                "release_date": s.get("releaseDate"),
            }
            for s in sets
        ]
        return json.dumps({"sets": result})
