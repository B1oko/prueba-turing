import json
import logging
import os
from typing import Protocol

from src.models.card import Card

logger = logging.getLogger(__name__)

def _to_filename(name: str) -> str:
    return (
        "".join(x for x in name if x.isalnum() or x in " -_")
        .strip()
        .replace(" ", "_")
        .lower()
    )


def _specs_to_card(card_specs: dict, image_url: str) -> Card:
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
        colors=card_specs.get("colors", []),
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
        card_dir = os.path.join(self._base_dir, filename)
        os.makedirs(card_dir, exist_ok=True)

        image_url = f"/custom_cards/{filename}/{filename}.png"

        if image_bytes:
            png_path = os.path.join(card_dir, f"{filename}.png")
            with open(png_path, "wb") as f:
                f.write(image_bytes)

        card = _specs_to_card(card_specs, image_url)
        json_path = os.path.join(card_dir, f"{filename}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(card.model_dump(), f, ensure_ascii=False, indent=2)

        return card

    def find_all(self) -> list[Card]:
        if not os.path.exists(self._base_dir):
            return []
        cards = []
        for entry in os.scandir(self._base_dir):
            if not entry.is_dir():
                continue
            json_path = os.path.join(entry.path, f"{entry.name}.json")
            if not os.path.exists(json_path):
                continue
            try:
                with open(json_path, encoding="utf-8") as f:
                    cards.append(Card(**json.load(f)))
            except Exception as e:
                logger.error("Failed to load card metadata from '%s': %s", json_path, e)
        return cards
