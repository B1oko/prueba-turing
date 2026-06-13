import json
from typing import Any, Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

from src.clients.mtg_client import ICardSearch


class _SearchCardsInput(BaseModel):
    name: Optional[str] = None
    colors: Optional[str] = None
    type: Optional[str] = None
    cmc: Optional[int] = None
    text: Optional[str] = None


class SearchCardsTool(BaseTool):
    name: str = "search_cards"
    description: str = (
        "Search for Magic: The Gathering cards using filters. "
        "Args: name (card name), colors (e.g. 'White,Red'), type (e.g. 'Creature'), "
        "cmc (converted mana cost as integer), text (rules text or keywords)."
    )
    args_schema: type[BaseModel] = _SearchCardsInput

    _client: Any = PrivateAttr()

    def __init__(self, client: ICardSearch, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _format(self, cards: list[dict]) -> str:
        if not cards:
            return json.dumps(
                {
                    "cards": [],
                    "message": "No cards found matching the specified criteria.",
                }
            )
        seen_names: set = set()
        result = []
        for card in cards:
            card_name = card.get("name", "Unknown")
            if card_name in seen_names:
                continue
            seen_names.add(card_name)
            entry = {
                "name": card_name,
                "mana_cost": card.get("manaCost", ""),
                "type": card.get("type", "Unknown"),
                "text": card.get("text", ""),
                "image_url": card.get("imageUrl"),
            }
            if card.get("power") and card.get("toughness"):
                entry["power"] = card["power"]
                entry["toughness"] = card["toughness"]
            result.append(entry)
        return json.dumps({"cards": result})

    def _validate_filters(self, name, colors, type, cmc, text) -> Optional[str]:
        if not any([name, colors, type, cmc is not None, text]):
            return json.dumps(
                {"error": "Please provide at least one filter for the card search."}
            )
        return None

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Use async via _arun")

    async def _arun(
        self,
        name: Optional[str] = None,
        colors: Optional[str] = None,
        type: Optional[str] = None,
        cmc: Optional[int] = None,
        text: Optional[str] = None,
    ) -> str:
        if err := self._validate_filters(name, colors, type, cmc, text):
            return err
        try:
            cards = await self._client.search_cards(
                name=name, colors=colors, type=type, cmc=cmc, text=text
            )
        except Exception as e:
            return json.dumps({"error": f"Error connecting to MTG API: {e}"})
        return self._format(cards)
