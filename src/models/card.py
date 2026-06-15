from typing import Optional

from pydantic import BaseModel


class Card(BaseModel):
    name: str
    mana_cost: str = ""
    type: str = ""
    text: str = ""
    image_url: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    rarity: Optional[str] = None
    flavor: Optional[str] = None
    colors: Optional[list[str]] = None
    set: Optional[str] = None
