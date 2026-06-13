import logging
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.state import AgentState

logger = logging.getLogger(__name__)


def get_agent_graph(llm: BaseChatModel, tools: list[BaseTool]):
    logger.info("Setting up Agent Graph with %d tools...", len(tools))
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState):
        messages = state["messages"]
        logger.info("Executing Agent Node. Current message count: %d", len(messages))
        if not messages or not isinstance(messages[0], SystemMessage):
            logger.info("Injecting system prompt into message list.")
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        logger.info("Invoking LLM with tools...")
        response = llm_with_tools.invoke(messages)
        logger.info("LLM responded: %s", response.content[:100] + "..." if len(str(response.content)) > 100 else response.content)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")
    
    logger.info("Compiling Agent Graph with MemorySaver...")
    return workflow.compile(checkpointer=MemorySaver())
