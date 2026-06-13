import asyncio
import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

from src.clients.image_generation import ImageGenerationClient
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

    def _run(self, description: str) -> str:
        logger.info("CreateCustomCardTool invoked with description: '%s'", description)
        try:
            result = self._graph.invoke({
                "description": description,
                "card_specs": {},
                "art_bytes": None,
                "card_path": "",
            })
            card_name = result["card_specs"].get("name", "")
            card_path = result["card_path"]
            logger.info("Card '%s' created at: %s", card_name, card_path)
            return f"Custom card '{card_name}' created at: {card_path}"
        except Exception as e:
            logger.error("CreateCustomCardTool failed: %s", e, exc_info=True)
            raise

    async def _arun(self, description: str) -> str:
        return await asyncio.to_thread(self._run, description=description)
