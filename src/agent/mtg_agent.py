from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.agent.base import BaseAgent
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.state import AgentState


class MTGAgent(BaseAgent):
    def __init__(self, llm: BaseChatModel, tools: list[BaseTool]):
        self._tools = tools
        super().__init__(llm)

    def _build_graph(self):
        llm_with_tools = self._llm.bind_tools(self._tools)

        def agent_node(state: AgentState):
            messages = state["messages"]
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
            return {"messages": [llm_with_tools.invoke(messages)]}

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", ToolNode(self._tools))
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", tools_condition)
        workflow.add_edge("tools", "agent")
        return workflow.compile(checkpointer=MemorySaver())
