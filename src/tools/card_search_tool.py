import urllib.parse
import requests
from typing import Optional
from langchain_core.tools import tool

# Simple local cache to store API responses and avoid hitting rate limits
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
    text: Optional[str] = None
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
        A formatted string with matching cards and their details (cost, type, rules text, imageUrl).
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
        
    # Limit results to avoid massive payloads
    params["pageSize"] = "8"
    
    if not params:
        return "Please provide at least one filter for the card search."
        
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"
    
    data = _fetch_from_api(url)
    
    if "error" in data:
        return f"Error connecting to MTG API: {data['error']}"
        
    cards = data.get("cards", [])
    if not cards:
        return "No cards found matching the specified criteria."
        
    # Format the cards for the agent
    formatted_cards = []
    # Use a set to avoid showing duplicate prints of the same card name
    seen_names = set()
    
    for card in cards:
        card_name = card.get("name", "Unknown")
        # Only show the first print of each card name in search results to keep context concise
        if card_name in seen_names:
            continue
        seen_names.add(card_name)
        
        mana_cost = card.get("manaCost", "None")
        card_type = card.get("type", "Unknown")
        rules_text = card.get("text", "No rules text.")
        power = card.get("power")
        toughness = card.get("toughness")
        image_url = card.get("imageUrl", "No image available")
        
        details = [
            f"Card Name: {card_name}",
            f"Mana Cost: {mana_cost}",
            f"Type: {card_type}",
            f"Rules Text: {rules_text}"
        ]
        
        if power and toughness:
            details.append(f"P/T: {power}/{toughness}")
            
        details.append(f"Image URL: {image_url}")
        
        formatted_cards.append("\n".join(details))
        
    return "\n\n=======================\n\n".join(formatted_cards)
