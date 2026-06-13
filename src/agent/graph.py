from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.state import AgentState
from src.config.settings import get_settings


def get_agent_graph(tools: list[BaseTool]):
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required."
        )

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        temperature=settings.GEMINI_TEMPERATURE,
        google_api_key=settings.GEMINI_API_KEY,
    )

    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    graph = workflow.compile(checkpointer=MemorySaver())
    return graph
