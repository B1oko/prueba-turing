from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel


class BaseAgent(ABC):
    def __init__(self, llm: BaseChatModel):
        self._llm = llm
        self._graph = self._build_graph()

    @abstractmethod
    def _build_graph(self): ...

    def invoke(self, input: dict, config: dict | None = None) -> dict:
        return self._graph.invoke(input, config)

    async def ainvoke(self, input: dict, config: dict | None = None) -> dict:
        return await self._graph.ainvoke(input, config)
