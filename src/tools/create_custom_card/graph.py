import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from src.clients.image_generation import ImageGenerationClient
from src.repositories.custom_card_repository import CustomCardRepository
from src.services.card_renderer import render_card

logger = logging.getLogger(__name__)


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


def get_card_generator_graph(
    llm: BaseChatModel,
    image_client: ImageGenerationClient,
    repository: CustomCardRepository,
):
    designer_llm = llm.with_structured_output(CardSpecs)

    def design_card(state: CardGeneratorState) -> dict:
        specs: CardSpecs = designer_llm.invoke(
            _DESIGNER_PROMPT.format(description=state["description"])
        )
        return {"card_specs": specs.model_dump()}

    def generate_art(state: CardGeneratorState) -> dict:
        art_bytes = image_client.generate(state["card_specs"]["art_prompt"])
        if not art_bytes:
            logger.warning("Image generation returned no bytes, using placeholder.")
        return {"art_bytes": art_bytes}

    def render_and_save(state: CardGeneratorState) -> dict:
        image_bytes = render_card(state["card_specs"], state.get("art_bytes"))
        card = repository.save(state["card_specs"], image_bytes)
        return {"card_path": card.image_url}

    workflow = StateGraph(CardGeneratorState)
    workflow.add_node("design_card", design_card)
    workflow.add_node("generate_art", generate_art)
    workflow.add_node("render_and_save", render_and_save)
    workflow.add_edge(START, "design_card")
    workflow.add_edge("design_card", "generate_art")
    workflow.add_edge("generate_art", "render_and_save")
    workflow.add_edge("render_and_save", END)
    return workflow.compile()
