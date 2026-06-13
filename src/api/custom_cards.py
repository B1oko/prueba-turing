import os
import json
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/custom-cards")
async def get_custom_cards():
    custom_cards_dir = "custom_cards"
    if not os.path.exists(custom_cards_dir):
        return []
    
    cards = []
    try:
        for filename in os.listdir(custom_cards_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(custom_cards_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        card_data = json.load(f)
                        # Ensure image_url maps properly to the mounted static files route
                        png_filename = filename[:-5] + ".png"
                        if not card_data.get("image_url"):
                            card_data["image_url"] = f"/custom_cards/{png_filename}"
                        cards.append(card_data)
                except Exception as e:
                    logger.error("Error reading custom card metadata file %s: %s", filepath, str(e))
    except Exception as e:
        logger.error("Error listing custom cards directory: %s", str(e))
        
    return cards
