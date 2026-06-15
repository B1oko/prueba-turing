import asyncio
import json
import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

from src.clients.image_generation import ImageGenerationClient
from src.models.card import Card
from src.repositories.custom_card_repository import CustomCardRepository
from src.tools.create_custom_card.graph import get_card_generator_graph

logger = logging.getLogger(__name__)


class _CreateCustomCardInput(BaseModel):
    description: str


class CreateCustomCardTool(BaseTool):
    name: str = "create_custom_card"
    description: str = (
        "Creates a custom Magic: The Gathering card from a vague description. "
        "Automatically designs the card stats, generates art, and assembles the final image. "
        "Returns the file path of the generated card."
    )
    args_schema: type[BaseModel] = _CreateCustomCardInput
    response_format: str = "content_and_artifact"

    _graph: Any = PrivateAttr()

    def __init__(
        self,
        llm: BaseChatModel,
        image_client: ImageGenerationClient,
        repository: CustomCardRepository,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._graph = get_card_generator_graph(llm, image_client, repository)

    def _run(self, description: str) -> tuple[str, str]:
        try:
            result = self._graph.invoke({
                "description": description,
                "card_specs": {},
                "art_bytes": None,
                "card_path": "",
            })
            specs = result["card_specs"]
            card_path = result["card_path"]

            card = Card(
                name=specs.get("name", ""),
                mana_cost=specs.get("mana_cost", ""),
                type=specs.get("type_line", ""),
                text=specs.get("rules_text", ""),
                image_url=card_path,
                power=specs.get("power"),
                toughness=specs.get("toughness"),
                rarity="Mythic Rare",
                flavor=specs.get("flavor_text", ""),
                colors=specs.get("colors", []),
                set="custom",
            )

            summary = f"Custom card '{card.name}' created successfully."
            artifact = json.dumps({"cards": [card.model_dump()]})
            return summary, artifact
        except Exception as e:
            logger.error("CreateCustomCardTool failed: %s", e, exc_info=True)
            raise

    async def _arun(self, description: str) -> tuple[str, str]:
        return await asyncio.to_thread(self._run, description=description)
