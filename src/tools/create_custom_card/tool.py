import asyncio
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

from src.clients.image_generation import ImageGenerationClient
from src.tools.create_custom_card.graph import get_card_generator_graph


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

    def __init__(self, llm: BaseChatModel, image_client: ImageGenerationClient, **kwargs):
        super().__init__(**kwargs)
        self._graph = get_card_generator_graph(llm, image_client)

    def _run(self, description: str) -> str:
        result = self._graph.invoke({
            "description": description,
            "card_specs": {},
            "art_bytes": None,
            "card_path": "",
        })
        return f"Custom card '{result['card_specs'].get('name', '')}' created at: {result['card_path']}"

    async def _arun(self, description: str) -> str:
        return await asyncio.to_thread(self._run, description=description)
