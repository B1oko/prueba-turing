import json
import urllib.parse
import requests
from typing import Optional
from langchain_core.tools import tool

_api_cache = {}


def _fetch_from_api(url: str) -> dict:
    if url in _api_cache:
        return _api_cache[url]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        _api_cache[url] = data
        return data
    except Exception as e:
        return {"error": str(e)}


@tool
def search_cards(
    name: Optional[str] = None,
    colors: Optional[str] = None,
    type: Optional[str] = None,
    cmc: Optional[int] = None,
    text: Optional[str] = None,
) -> str:
    """
    Search for Magic: The Gathering cards using filters.

    Args:
        name: Name of the card (e.g., 'Black Lotus', 'Battlefield Raptor').
        colors: Color of the card (e.g., 'White', 'Red', 'White,Red' for multicolored).
        type: Card type or subtype (e.g., 'Creature', 'Warrior', 'Artifact', 'Instant').
        cmc: Converted mana cost of the card (e.g., 1, 2, 6).
        text: Rules text or keywords on the card (e.g., 'first strike', 'lifelink').

    Returns:
        A JSON string with a list of matching cards and their details.
    """
    base_url = "https://api.magicthegathering.io/v1/cards"
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

    params["pageSize"] = "8"

    if not params:
        return json.dumps({"error": "Please provide at least one filter for the card search."})

    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"
    data = _fetch_from_api(url)

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
