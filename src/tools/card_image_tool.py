import os
import requests
from typing import Optional, List
from PIL import Image, ImageDraw, ImageFont
from langchain_core.tools import tool

# Simple cache for card image search
_image_cache = {}

@tool
def get_card_image(card_name: str) -> str:
    """
    Retrieves the image URL of a Magic: The Gathering card by its exact name.
    
    Args:
        card_name: The name of the card (e.g., 'Black Lotus', 'Battlefield Raptor').
        
    Returns:
        The URL of the card's image, or a message indicating no image was found.
    """
    if card_name in _image_cache:
        return _image_cache[card_name]
        
    base_url = "https://api.magicthegathering.io/v1/cards"
    params = {"name": card_name, "pageSize": "1"}
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        cards = response.json().get("cards", [])
        
        if not cards:
            return f"Card '{card_name}' not found."
            
        # Find first card print that has an image URL
        image_url = None
        for card in cards:
            if card.get("imageUrl"):
                image_url = card.get("imageUrl")
                break
                
        if image_url:
            _image_cache[card_name] = image_url
            return f"Image URL for {card_name}: {image_url}"
        else:
            return f"Card '{card_name}' found, but no image URL is available in the database."
    except Exception as e:
        return f"Error retrieving card image: {str(e)}"


@tool
def create_custom_card(
    name: str,
    mana_cost: str,
    colors: List[str],
    type_line: str,
    rules_text: str,
    power: Optional[str] = None,
    toughness: Optional[str] = None
) -> str:
    """
    Creates a custom Magic: The Gathering card image mock-up using Pillow.
    Saves the image locally and returns the path.
    
    Args:
        name: Name of the card (e.g., 'Han Solo').
        mana_cost: Mana cost symbol string (e.g., '{2}{R}{W}' or '2RW').
        colors: List of colors in English (e.g., ['Red', 'White']).
        type_line: Card type line (e.g., 'Legendary Creature - Smuggler').
        rules_text: Card abilities and text (e.g., 'First strike. Haste.').
        power: Power of the creature (optional, e.g., '3').
        toughness: Toughness of the creature (optional, e.g., '2').
        
    Returns:
        A message indicating success and the path to the saved card image file.
    """
    # Card Dimensions (aspect ratio roughly 2.5 x 3.5)
    width, height = 400, 560
    img = Image.new("RGB", (width, height), color=(0, 0, 0)) # Black border
    draw = ImageDraw.Draw(img)
    
    # 1. Determine Card Color Theme
    # Mapping colors to RGB values
    color_map = {
        "white": (248, 246, 235), # Cream
        "blue": (14, 104, 171),   # Blue
        "black": (21, 11, 14),    # Dark Grey/Black
        "red": (211, 32, 42),     # Red
        "green": (0, 115, 62),    # Green
        "gold": (197, 160, 89),   # Gold for multicolored
        "colorless": (170, 170, 170) # Silver/Grey
    }
    
    colors_lower = [c.lower() for c in colors]
    if len(colors_lower) > 1:
        theme_color = color_map["gold"]
    elif len(colors_lower) == 1 and colors_lower[0] in color_map:
        theme_color = color_map[colors_lower[0]]
    else:
        theme_color = color_map["colorless"]
        
    # Text color (light theme vs dark theme)
    text_color = (0, 0, 0)
    if theme_color in [color_map["black"], color_map["red"], color_map["green"], color_map["blue"]]:
        card_text_color = (255, 255, 255)
    else:
        card_text_color = (0, 0, 0)

    # 2. Draw Card Frame
    # Outer border is already black (0, 0, 0)
    # Draw Inner Frame (colored background box)
    frame_margin = 14
    draw.rectangle(
        [(frame_margin, frame_margin), (width - frame_margin, height - frame_margin)],
        fill=theme_color,
        outline=(20, 20, 20),
        width=2
    )
    
    # 3. Draw Title Box (top)
    title_box = [(22, 22), (width - 22, 54)]
    draw.rectangle(title_box, fill=(255, 255, 255, 128), outline=(0, 0, 0), width=1)
    
    # 4. Draw Illustration Frame (placeholder)
    art_box = [(22, 62), (width - 22, 280)]
    draw.rectangle(art_box, fill=(120, 120, 120), outline=(0, 0, 0), width=1)
    # Draw an 'X' to represent art placeholder
    draw.line([art_box[0], art_box[1]], fill=(180, 180, 180), width=2)
    draw.line([(art_box[0][0], art_box[1][1]), (art_box[1][0], art_box[0][1])], fill=(180, 180, 180), width=2)
    
    # 5. Draw Type Box (middle)
    type_box = [(22, 288), (width - 22, 320)]
    draw.rectangle(type_box, fill=(255, 255, 255, 128), outline=(0, 0, 0), width=1)
    
    # 6. Draw Rules Text Box (bottom)
    rules_box = [(22, 328), (width - 22, 515)]
    draw.rectangle(rules_box, fill=(245, 245, 245), outline=(0, 0, 0), width=1)
    
    # 7. Write Texts (using default PIL font with sizes simulated if custom fonts aren't available)
    try:
        # Try loading a system font (Arial/Helvetica usually present on Windows)
        font_bold = ImageFont.truetype("arial.ttf", 16)
        font_italic = ImageFont.truetype("ariali.ttf", 13)
        font_regular = ImageFont.truetype("arial.ttf", 14)
        font_pt = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        # Fallback to default PIL font
        font_bold = ImageFont.load_default()
        font_italic = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_pt = ImageFont.load_default()
        
    # Write Title
    draw.text((28, 28), name, fill=(0, 0, 0), font=font_bold)
    # Write Mana Cost
    draw.text((width - 80, 28), mana_cost, fill=(0, 0, 0), font=font_bold)
    
    # Write Type Line
    draw.text((28, 294), type_line, fill=(0, 0, 0), font=font_bold)
    
    # Write Rules Text (handle line wrapping basic implementation)
    words = rules_text.split(" ")
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        # Simple limit of characters per line
        if len(" ".join(current_line)) > 38:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
        
    y_text = 338
    for line in lines[:8]: # Limit lines to avoid overflow
        draw.text((32, y_text), line, fill=(0, 0, 0), font=font_regular)
        y_text += 20
        
    # Write Power/Toughness if creature
    if power and toughness:
        pt_text = f"{power}/{toughness}"
        pt_box = [(width - 80, 500), (width - 22, 532)]
        draw.rectangle(pt_box, fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        draw.text((width - 65, 506), pt_text, fill=(0, 0, 0), font=font_pt)
        
    # Write "CUSTOM CARD" placeholder label inside the art box
    draw.text((width // 2 - 50, 160), "CUSTOM CARD", fill=(255, 255, 255), font=font_bold)
    draw.text((width // 2 - 60, 185), f"({'-'.join(colors)})", fill=(220, 220, 220), font=font_italic)
    
    # Ensure save directory exists
    output_dir = "custom_cards"
    os.makedirs(output_dir, exist_ok=True)
    
    # Normalize name for filename
    filename = "".join(x for x in name if x.isalnum() or x in " -_").strip().replace(" ", "_").lower()
    filepath = os.path.join(output_dir, f"{filename}.png")
    
    img.save(filepath)
    
    # Return path relative to project root
    return f"Success! Custom card created successfully. Image saved at: {filepath}"
