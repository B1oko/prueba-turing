import asyncio
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel


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
    agent: Any

    def _run(self, description: str) -> str:
        result = self.agent.run(description)
        return f"Custom card '{result['card_specs'].get('name', '')}' created at: {result['card_path']}"

    async def _arun(self, description: str) -> str:
        return await asyncio.to_thread(self._run, description=description)
