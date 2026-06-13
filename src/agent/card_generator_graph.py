from typing import Optional

from google import genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from src.config.settings import get_settings
from src.services.card_renderer import render_card


class CardSpecs(BaseModel):
    name: str
    mana_cost: str
    colors: list[str]
    type_line: str
    rules_text: str
    flavor_text: str
    art_prompt: str
    power: Optional[str] = None
    toughness: Optional[str] = None


class CardGeneratorState(TypedDict):
    description: str
    card_specs: dict
    art_bytes: Optional[bytes]
    card_path: str


_DESIGNER_PROMPT = """Design a Magic: The Gathering card based on this description: "{description}"

Be creative and ensure the card is balanced and thematic. Follow these rules:
- mana_cost: use MTG notation like {{W}}, {{1}}{{W}}, {{2}}{{U}}{{U}}, etc.
- colors: list of lowercase color names (white, blue, black, red, green)
- type_line: e.g. "Creature — Human Warrior", "Instant", "Enchantment"
- rules_text: the card's mechanical text using standard MTG wording
- flavor_text: a short evocative quote that fits the card's theme
- art_prompt: a vivid fantasy illustration prompt for image generation
- power/toughness: only for creatures, as strings like "2", "3"
"""


def get_card_generator_graph(imagen_client: genai.Client):
    settings = get_settings()

    designer_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.7,
    ).with_structured_output(CardSpecs)

    def design_card(state: CardGeneratorState) -> dict:
        prompt = _DESIGNER_PROMPT.format(description=state["description"])
        specs: CardSpecs = designer_llm.invoke(prompt)
        return {"card_specs": specs.model_dump()}

    def generate_art(state: CardGeneratorState) -> dict:
        try:
            response = imagen_client.models.generate_images(
                model="imagen-3.0-fast-generate-001",
                prompt=state["card_specs"]["art_prompt"],
                config=types.GenerateImagesConfig(
                    number_of_images=1, aspect_ratio="4:3"
                ),
            )
            art_bytes = response.generated_images[0].image.image_bytes
        except Exception:
            art_bytes = None
        return {"art_bytes": art_bytes}

    def render_card_node(state: CardGeneratorState) -> dict:
        filepath = render_card(state["card_specs"], state.get("art_bytes"))
        return {"card_path": filepath}

    workflow = StateGraph(CardGeneratorState)
    workflow.add_node("design_card", design_card)
    workflow.add_node("generate_art", generate_art)
    workflow.add_node("render_card", render_card_node)
    workflow.add_edge(START, "design_card")
    workflow.add_edge("design_card", "generate_art")
    workflow.add_edge("generate_art", "render_card")
    workflow.add_edge("render_card", END)

    return workflow.compile()
