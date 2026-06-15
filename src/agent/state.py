from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The state structure for the LangGraph agent.
    Maintains a list of messages accumulating through the conversation.
    """
    messages: Annotated[list, add_messages]
