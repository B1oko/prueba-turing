import urllib.parse
from typing import Optional, Protocol

import httpx
from pydantic import BaseModel

_BASE_URL = "https://api.magicthegathering.io/v1"


class MTGCard(BaseModel):
    name: str
    manaCost: Optional[str] = None
    cmc: Optional[float] = None
    colors: Optional[list[str]] = None
    colorIdentity: Optional[list[str]] = None
    type: str
    supertypes: Optional[list[str]] = None
    types: Optional[list[str]] = None
    subtypes: Optional[list[str]] = None
    rarity: Optional[str] = None
    set: Optional[str] = None
    text: Optional[str] = None
    flavor: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    loyalty: Optional[int] = None
    imageUrl: Optional[str] = None
    id: Optional[str] = None

    model_config = {"extra": "ignore"}


class ICardSearch(Protocol):
    async def search_cards(
        self,
        name: Optional[str] = None,
        colors: Optional[str] = None,
        types: Optional[str] = None,
        subtypes: Optional[str] = None,
        supertypes: Optional[str] = None,
        cmc: Optional[int] = None,
        text: Optional[str] = None,
        page_size: int = 8,
    ) -> list[MTGCard]: ...


class ISetSearch(Protocol):
    async def search_sets(
        self,
        name: Optional[str] = None,
        block: Optional[str] = None,
    ) -> list[dict]: ...


class MTGClient(ICardSearch, ISetSearch):
    def __init__(self, timeout: int = 10):
        self._client = httpx.AsyncClient(timeout=timeout)

    async def search_cards(
        self,
        name: Optional[str] = None,
        colors: Optional[str] = None,
        types: Optional[str] = None,
        subtypes: Optional[str] = None,
        supertypes: Optional[str] = None,
        cmc: Optional[int] = None,
        text: Optional[str] = None,
        page_size: int = 8,
    ) -> list[MTGCard]:
        params: dict = {"pageSize": str(page_size)}
        if name:
            params["name"] = name
        if colors:
            params["colors"] = colors
        if types:
            params["types"] = types
        if subtypes:
            params["subtypes"] = subtypes
        if supertypes:
            params["supertypes"] = supertypes
        if cmc is not None:
            params["cmc"] = str(cmc)
        if text:
            params["text"] = text
        url = f"{_BASE_URL}/cards?{urllib.parse.urlencode(params)}"
        response = await self._client.get(url)
        response.raise_for_status()
        raw_cards = response.json().get("cards", [])
        return [MTGCard.model_validate(c) for c in raw_cards]

    async def search_sets(
        self,
        name: Optional[str] = None,
        block: Optional[str] = None,
    ) -> list[dict]:
        params: dict = {}
        if name:
            params["name"] = name
        if block:
            params["block"] = block
        url = f"{_BASE_URL}/sets"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        response = await self._client.get(url)
        response.raise_for_status()
        return response.json().get("sets", [])
