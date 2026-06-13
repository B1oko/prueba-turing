import os
from typing import Optional, List
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from langchain_core.tools import BaseTool


class _CreateCustomCardInput(BaseModel):
    name: str
    mana_cost: str
    colors: List[str]
    type_line: str
    rules_text: str
    power: Optional[str] = None
    toughness: Optional[str] = None


class CreateCustomCardTool(BaseTool):
    name: str = "create_custom_card"
    description: str = (
        "Creates a custom Magic: The Gathering card image mock-up using Pillow. "
        "Saves the image locally and returns the file path."
    )
    args_schema: type[BaseModel] = _CreateCustomCardInput

    def _run(
        self,
        name: str,
        mana_cost: str,
        colors: List[str],
        type_line: str,
        rules_text: str,
        power: Optional[str] = None,
        toughness: Optional[str] = None,
    ) -> str:
        width, height = 400, 560
        img = Image.new("RGB", (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)

        color_map = {
            "white": (248, 246, 235),
            "blue": (14, 104, 171),
            "black": (21, 11, 14),
            "red": (211, 32, 42),
            "green": (0, 115, 62),
            "gold": (197, 160, 89),
            "colorless": (170, 170, 170),
        }

        colors_lower = [c.lower() for c in colors]
        if len(colors_lower) > 1:
            theme_color = color_map["gold"]
        elif len(colors_lower) == 1 and colors_lower[0] in color_map:
            theme_color = color_map[colors_lower[0]]
        else:
            theme_color = color_map["colorless"]

        if theme_color in [color_map["black"], color_map["red"], color_map["green"], color_map["blue"]]:
            card_text_color = (255, 255, 255)
        else:
            card_text_color = (0, 0, 0)

        frame_margin = 14
        draw.rectangle(
            [(frame_margin, frame_margin), (width - frame_margin, height - frame_margin)],
            fill=theme_color,
            outline=(20, 20, 20),
            width=2,
        )

        title_box = [(22, 22), (width - 22, 54)]
        draw.rectangle(title_box, fill=(255, 255, 255, 128), outline=(0, 0, 0), width=1)

        art_box = [(22, 62), (width - 22, 280)]
        draw.rectangle(art_box, fill=(120, 120, 120), outline=(0, 0, 0), width=1)
        draw.line([art_box[0], art_box[1]], fill=(180, 180, 180), width=2)
        draw.line([(art_box[0][0], art_box[1][1]), (art_box[1][0], art_box[0][1])], fill=(180, 180, 180), width=2)

        type_box = [(22, 288), (width - 22, 320)]
        draw.rectangle(type_box, fill=(255, 255, 255, 128), outline=(0, 0, 0), width=1)

        rules_box = [(22, 328), (width - 22, 515)]
        draw.rectangle(rules_box, fill=(245, 245, 245), outline=(0, 0, 0), width=1)

        try:
            font_bold = ImageFont.truetype("arial.ttf", 16)
            font_italic = ImageFont.truetype("ariali.ttf", 13)
            font_regular = ImageFont.truetype("arial.ttf", 14)
            font_pt = ImageFont.truetype("arial.ttf", 18)
        except IOError:
            font_bold = ImageFont.load_default()
            font_italic = ImageFont.load_default()
            font_regular = ImageFont.load_default()
            font_pt = ImageFont.load_default()

        draw.text((28, 28), name, fill=(0, 0, 0), font=font_bold)
        draw.text((width - 80, 28), mana_cost, fill=(0, 0, 0), font=font_bold)
        draw.text((28, 294), type_line, fill=(0, 0, 0), font=font_bold)

        words = rules_text.split(" ")
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 38:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        y_text = 338
        for line in lines[:8]:
            draw.text((32, y_text), line, fill=(0, 0, 0), font=font_regular)
            y_text += 20

        if power and toughness:
            pt_text = f"{power}/{toughness}"
            pt_box = [(width - 80, 500), (width - 22, 532)]
            draw.rectangle(pt_box, fill=(255, 255, 255), outline=(0, 0, 0), width=2)
            draw.text((width - 65, 506), pt_text, fill=(0, 0, 0), font=font_pt)

        draw.text((width // 2 - 50, 160), "CUSTOM CARD", fill=(255, 255, 255), font=font_bold)
        draw.text((width // 2 - 60, 185), f"({'-'.join(colors)})", fill=(220, 220, 220), font=font_italic)

        output_dir = "custom_cards"
        os.makedirs(output_dir, exist_ok=True)
        filename = "".join(x for x in name if x.isalnum() or x in " -_").strip().replace(" ", "_").lower()
        filepath = os.path.join(output_dir, f"{filename}.png")
        img.save(filepath)

        return f"Success! Custom card created successfully. Image saved at: {filepath}"
