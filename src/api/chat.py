import logging

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.agent.graph import get_agent_graph

logger = logging.getLogger(__name__)
router = APIRouter()

_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = get_agent_graph()
    return _compiled_graph


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message using the LangGraph agent."""
    try:
        graph = get_graph()
        config = {"configurable": {"thread_id": request.session_id}}
        result = graph.invoke(
            {"messages": [HumanMessage(content=request.message)]}, config=config
        )
        assistant_msg = result["messages"][-1].content
        return ChatResponse(response=assistant_msg)
    except Exception as e:
        logger.error("Error in /chat endpoint: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
