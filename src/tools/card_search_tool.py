import json
import urllib.parse
from typing import Any, Optional
import requests
from pydantic import BaseModel, PrivateAttr
from langchain_core.tools import BaseTool


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

    _session: Any = PrivateAttr()
    _cache: dict = PrivateAttr()

    def __init__(self, session: requests.Session = None, **kwargs):
        super().__init__(**kwargs)
        self._session = session or requests.Session()
        self._cache = {}

    def _fetch(self, url: str) -> dict:
        if url in self._cache:
            return self._cache[url]
        try:
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self._cache[url] = data
            return data
        except Exception as e:
            return {"error": str(e)}

    def _run(
        self,
        name: Optional[str] = None,
        colors: Optional[str] = None,
        type: Optional[str] = None,
        cmc: Optional[int] = None,
        text: Optional[str] = None,
    ) -> str:
        params = {}
        if name:
            params["name"] = name
        if colors:
            params["colors"] = colors
        if type:
            params["type"] = type
        if cmc is not None:
            params["cmc"] = str(cmc)
        if text:
            params["text"] = text

        if not params:
            return json.dumps({"error": "Please provide at least one filter for the card search."})

        params["pageSize"] = "8"
        url = f"https://api.magicthegathering.io/v1/cards?{urllib.parse.urlencode(params)}"
        data = self._fetch(url)

        if "error" in data:
            return json.dumps({"error": f"Error connecting to MTG API: {data['error']}"})

        cards = data.get("cards", [])
        if not cards:
            return json.dumps({"cards": [], "message": "No cards found matching the specified criteria."})

        seen_names = set()
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
