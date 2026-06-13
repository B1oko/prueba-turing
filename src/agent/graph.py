from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from src.config.settings import get_settings
from src.agent.state import AgentState
from src.agent.prompts import SYSTEM_PROMPT
from src.tools.rules_tool import search_rules
from src.tools.card_search_tool import search_cards
from src.tools.card_image_tool import get_card_image, create_custom_card


def get_agent_graph():
    """
    Initializes the Gemini LLM, binds tools, defines nodes/edges,
    and returns the compiled LangGraph workflow.
    """
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required."
        )

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        temperature=0.1,
        google_api_key=settings.GEMINI_API_KEY,
    )

    # Bundle tools
    tools = [search_rules, search_cards, get_card_image, create_custom_card]
    llm_with_tools = llm.bind_tools(tools)

    # Define agent node
    def agent_node(state: AgentState):
        messages = state["messages"]

        # Check if system message is already prepended to avoid duplicate system prompts
        has_system = False
        if messages and isinstance(messages[0], SystemMessage):
            has_system = True

        if not has_system:
            system_msg = SystemMessage(content=SYSTEM_PROMPT)
            messages = [system_msg] + messages

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Build LangGraph workflow
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    # Define connections
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    # Add memory checkpointer for conversational session state persistence
    memory = MemorySaver()

    # Compile the graph
    graph = workflow.compile(checkpointer=memory)
    return graph
