import urllib.parse
from typing import Optional, Protocol

import httpx

_BASE_URL = "https://api.magicthegathering.io/v1"


class ICardSearch(Protocol):
    async def search_cards(
        self,
        name: Optional[str] = None,
        colors: Optional[str] = None,
        type: Optional[str] = None,
        cmc: Optional[int] = None,
        text: Optional[str] = None,
        page_size: int = 8,
    ) -> list[dict]: ...


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
        type: Optional[str] = None,
        cmc: Optional[int] = None,
        text: Optional[str] = None,
        page_size: int = 8,
    ) -> list[dict]:

        params: dict = {"pageSize": str(page_size)}
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

        url = f"{_BASE_URL}/cards?{urllib.parse.urlencode(params)}"
        response = await self._client.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("cards", [])

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
        data = response.json()
        return data.get("sets", [])
