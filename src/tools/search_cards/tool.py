import json
import logging
from typing import Any, Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from src.clients.mtg_client import ICardSearch, MTGCard
from src.models.card import Card

logger = logging.getLogger(__name__)


class _SearchCardsInput(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="Card name (partial match).",
    )
    colors: Optional[str] = Field(
        default=None,
        description=(
            "Color codes: W (white/blanco), U (blue/azul), B (black/negro), "
            "R (red/rojo), G (green/verde). "
            "Comma = AND, pipe = OR. Examples: 'W', 'W,R', 'W|U'."
        ),
    )
    types: Optional[str] = Field(
        default=None,
        description=(
            "Main card type (left of the dash). "
            "Examples: Creature, Instant, Sorcery, Artifact, Enchantment, Land, Planeswalker."
        ),
    )
    subtypes: Optional[str] = Field(
        default=None,
        description=(
            "Subtype (right of the dash). 'Guerrero' = Warrior. "
            "Examples: Warrior, Human, Elf, Bird, Equipment, Aura."
        ),
    )
    supertypes: Optional[str] = Field(
        default=None,
        description="Supertype. Examples: Legendary, Basic, Snow.",
    )
    cmc: Optional[int] = Field(
        default=None,
        description=(
            "Converted mana cost (exact integer). "
            "'Coste inferior a 2' = use cmc=1 or cmc=0 separately."
        ),
    )
    text: Optional[str] = Field(
        default=None,
        description="Keyword or rules text. Examples: 'flying', 'first strike', 'trample'.",
    )


class SearchCardsTool(BaseTool):
    name: str = "search_cards"
    description: str = (
        "Search for Magic: The Gathering cards using filters aligned with the MTG API. "
        "Map user intent to: colors (W/U/B/R/G codes), types (Creature, Instant...), "
        "subtypes (Warrior, Human...), cmc (exact cost) or cmc_max (less than X), "
        "and text (keywords in rules text)."
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

    def _validate_filters(self, name, colors, types, subtypes, supertypes, cmc, text) -> Optional[str]:
        if not any([name, colors, types, subtypes, supertypes, cmc is not None, text]):
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
        types: Optional[str] = None,
        subtypes: Optional[str] = None,
        supertypes: Optional[str] = None,
        cmc: Optional[int] = None,
        text: Optional[str] = None,
    ) -> tuple[str, str]:
        if err := self._validate_filters(name, colors, types, subtypes, supertypes, cmc, text):
            return err, json.dumps({"cards": []})
        try:
            cards = await self._client.search_cards(
                name=name,
                colors=colors,
                types=types,
                subtypes=subtypes,
                supertypes=supertypes,
                cmc=cmc,
                text=text,
            )
        except Exception as e:
            logger.error("SearchCardsTool MTG API search failed: %s", str(e), exc_info=True)
            return f"Error connecting to MTG API: {e}", json.dumps({"cards": []})
        return self._to_summary(cards), self._to_artifact(cards)
