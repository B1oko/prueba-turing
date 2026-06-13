import json
from typing import Any, Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

from src.clients.mtg_client import ICardSearch, MTGCard
from src.models import Card


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
    response_format: str = "content_and_artifact"

    _client: Any = PrivateAttr()

    def __init__(self, client: ICardSearch, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _to_artifact(self, cards: list[MTGCard]) -> str:
        seen: set[str] = set()
        result = []
        for card in cards:
            if card.name in seen:
                continue
            seen.add(card.name)
            result.append(Card(
                name=card.name,
                mana_cost=card.manaCost or "",
                type=card.type,
                text=card.text or "",
                image_url=card.imageUrl,
                power=card.power,
                toughness=card.toughness,
                rarity=card.rarity,
                flavor=card.flavor,
                colors=card.colors,
                set=card.set,
            ).model_dump())
        return json.dumps({"cards": result})

    def _to_summary(self, cards: list[MTGCard]) -> str:
        if not cards:
            return "No cards found matching the criteria."
        lines = []
        for card in cards:
            parts = [f"**{card.name}**"]
            if card.manaCost:
                parts.append(card.manaCost)
            if card.type:
                parts.append(f"— {card.type}")
            if card.text:
                snippet = card.text[:120] + ("..." if len(card.text) > 120 else "")
                parts.append(f"| {snippet}")
            if card.power and card.toughness:
                parts.append(f"({card.power}/{card.toughness})")
            lines.append(" ".join(parts))
        return f"Cards found ({len(cards)}):\n" + "\n".join(f"- {l}" for l in lines)

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
    ) -> tuple[str, str]:
        if err := self._validate_filters(name, colors, type, cmc, text):
            return err, json.dumps({"cards": []})
        try:
            cards = await self._client.search_cards(
                name=name, colors=colors, type=type, cmc=cmc, text=text
            )
        except Exception as e:
            error_msg = f"Error connecting to MTG API: {e}"
            return error_msg, json.dumps({"cards": []})
        return self._to_summary(cards), self._to_artifact(cards)
