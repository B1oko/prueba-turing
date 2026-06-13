import json
import logging
import os
from typing import Protocol

from src.models.card import Card

logger = logging.getLogger(__name__)

_COLOR_MAP = {"white": "W", "blue": "U", "black": "B", "red": "R", "green": "G"}


def _to_filename(name: str) -> str:
    return (
        "".join(x for x in name if x.isalnum() or x in " -_")
        .strip()
        .replace(" ", "_")
        .lower()
    )


def _specs_to_card(card_specs: dict, image_url: str) -> Card:
    colors_lower = [c.lower() for c in card_specs.get("colors", [])]
    return Card(
        name=card_specs.get("name", ""),
        mana_cost=card_specs.get("mana_cost", ""),
        type=card_specs.get("type_line", ""),
        text=card_specs.get("rules_text", ""),
        image_url=image_url,
        power=card_specs.get("power"),
        toughness=card_specs.get("toughness"),
        rarity="Mythic Rare",
        flavor=card_specs.get("flavor_text", ""),
        colors=[_COLOR_MAP.get(c, c.upper()) for c in colors_lower],
        set="custom",
    )


class CustomCardRepository(Protocol):
    def save(self, card_specs: dict, image_bytes: bytes | None) -> Card: ...
    def find_all(self) -> list[Card]: ...


class LocalCustomCardRepository:
    def __init__(self, base_dir: str = "custom_cards"):
        self._base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save(self, card_specs: dict, image_bytes: bytes | None) -> Card:
        filename = _to_filename(card_specs["name"])
        image_url = f"/custom_cards/{filename}.png"

        if image_bytes:
            png_path = os.path.join(self._base_dir, f"{filename}.png")
            with open(png_path, "wb") as f:
                f.write(image_bytes)
            logger.info("Saved card image to '%s'", png_path)

        card = _specs_to_card(card_specs, image_url)
        json_path = os.path.join(self._base_dir, f"{filename}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(card.model_dump(), f, ensure_ascii=False, indent=2)
        logger.info("Saved card metadata to '%s'", json_path)

        return card

    def find_all(self) -> list[Card]:
        if not os.path.exists(self._base_dir):
            return []
        cards = []
        for filename in os.listdir(self._base_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self._base_dir, filename)
            try:
                with open(filepath, encoding="utf-8") as f:
                    cards.append(Card(**json.load(f)))
            except Exception as e:
                logger.error("Failed to load card metadata from '%s': %s", filepath, e)
        return cards
