import io
import os

from PIL import Image, ImageDraw, ImageFont


_COLOR_MAP = {
    "white": (248, 246, 235),
    "blue": (14, 104, 171),
    "black": (21, 11, 14),
    "red": (211, 32, 42),
    "green": (0, 115, 62),
    "gold": (197, 160, 89),
    "colorless": (170, 170, 170),
}
_DARK_COLORS = {"black", "red", "green", "blue"}

_ART_BOX_TL = (22, 62)
_ART_BOX_BR = (378, 280)


def _load_fonts() -> tuple:
    try:
        return (
            ImageFont.truetype("arial.ttf", 16),
            ImageFont.truetype("ariali.ttf", 12),
            ImageFont.truetype("arial.ttf", 13),
            ImageFont.truetype("arial.ttf", 18),
        )
    except IOError:
        default = ImageFont.load_default()
        return default, default, default, default


def _wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines, current = [], []
    for word in words:
        current.append(word)
        if len(" ".join(current)) > max_chars:
            lines.append(" ".join(current[:-1]))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def render_card(card_specs: dict, art_bytes: bytes | None) -> str:
    width, height = 400, 560
    img = Image.new("RGB", (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    colors_lower = [c.lower() for c in card_specs.get("colors", [])]
    if len(colors_lower) > 1:
        theme_color = _COLOR_MAP["gold"]
    elif colors_lower and colors_lower[0] in _COLOR_MAP:
        theme_color = _COLOR_MAP[colors_lower[0]]
    else:
        theme_color = _COLOR_MAP["colorless"]

    draw.rectangle(
        [(14, 14), (width - 14, height - 14)],
        fill=theme_color,
        outline=(20, 20, 20),
        width=2,
    )

    draw.rectangle([(22, 22), (width - 22, 54)], fill=(255, 255, 255, 128), outline=(0, 0, 0), width=1)

    if art_bytes:
        art_img = Image.open(io.BytesIO(art_bytes)).convert("RGB")
        art_w = _ART_BOX_BR[0] - _ART_BOX_TL[0]
        art_h = _ART_BOX_BR[1] - _ART_BOX_TL[1]
        img.paste(art_img.resize((art_w, art_h), Image.LANCZOS), _ART_BOX_TL)
        draw.rectangle([_ART_BOX_TL, _ART_BOX_BR], outline=(0, 0, 0), width=1)
    else:
        draw.rectangle([_ART_BOX_TL, _ART_BOX_BR], fill=(120, 120, 120), outline=(0, 0, 0), width=1)
        draw.line([_ART_BOX_TL, _ART_BOX_BR], fill=(180, 180, 180), width=2)
        draw.line([(_ART_BOX_TL[0], _ART_BOX_BR[1]), (_ART_BOX_BR[0], _ART_BOX_TL[1])], fill=(180, 180, 180), width=2)

    draw.rectangle([(22, 288), (width - 22, 320)], fill=(255, 255, 255, 128), outline=(0, 0, 0), width=1)
    draw.rectangle([(22, 328), (width - 22, 515)], fill=(245, 245, 245), outline=(0, 0, 0), width=1)

    font_bold, font_italic, font_regular, font_pt = _load_fonts()

    draw.text((28, 28), card_specs["name"], fill=(0, 0, 0), font=font_bold)
    draw.text((width - 90, 28), card_specs["mana_cost"], fill=(0, 0, 0), font=font_bold)
    draw.text((28, 294), card_specs["type_line"], fill=(0, 0, 0), font=font_bold)

    y = 338
    for line in _wrap_text(card_specs["rules_text"], 40)[:6]:
        draw.text((32, y), line, fill=(0, 0, 0), font=font_regular)
        y += 18

    flavor_text = card_specs.get("flavor_text", "")
    if flavor_text:
        y += 4
        draw.line([(32, y), (width - 32, y)], fill=(180, 180, 180), width=1)
        y += 6
        for line in _wrap_text(flavor_text, 40)[:3]:
            draw.text((32, y), line, fill=(80, 80, 80), font=font_italic)
            y += 16

    if card_specs.get("power") and card_specs.get("toughness"):
        pt_box = [(width - 80, 500), (width - 22, 532)]
        draw.rectangle(pt_box, fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        draw.text((width - 65, 506), f"{card_specs['power']}/{card_specs['toughness']}", fill=(0, 0, 0), font=font_pt)

    os.makedirs("custom_cards", exist_ok=True)
    filename = (
        "".join(x for x in card_specs["name"] if x.isalnum() or x in " -_")
        .strip()
        .replace(" ", "_")
        .lower()
    )
    filepath = os.path.join("custom_cards", f"{filename}.png")
    img.save(filepath)

    # Save JSON metadata for the custom card
    import json
    json_path = os.path.join("custom_cards", f"{filename}.json")
    
    color_map = {
        "white": "W",
        "blue": "U",
        "black": "B",
        "red": "R",
        "green": "G"
    }
    colors_lower = [c.lower() for c in card_specs.get("colors", [])]
    mapped_colors = [color_map.get(c, c.upper()) for c in colors_lower]

    card_data = {
        "name": card_specs.get("name", ""),
        "mana_cost": card_specs.get("mana_cost", ""),
        "type": card_specs.get("type_line", ""),
        "text": card_specs.get("rules_text", ""),
        "image_url": f"/custom_cards/{filename}.png",
        "power": card_specs.get("power"),
        "toughness": card_specs.get("toughness"),
        "rarity": "Mythic Rare",
        "flavor": card_specs.get("flavor_text", ""),
        "colors": mapped_colors,
        "set": "custom"
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(card_data, f, ensure_ascii=False, indent=2)

    return filepath
