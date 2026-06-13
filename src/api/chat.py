import json
import logging

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage, ToolMessage
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


class CardData(BaseModel):
    name: str
    mana_cost: str = ""
    type: str = ""
    text: str = ""
    power: str | None = None
    toughness: str | None = None
    image_url: str | None = None


class ChatRequest(BaseModel):
    message: str
    session_id: str


class RuleGrounding(BaseModel):
    rule_id: str
    page: int
    text: str


class ChatResponse(BaseModel):
    response: str
    cards: list[CardData] | None = None
    rules: list[RuleGrounding] | None = None


def _extract_cards(messages: list) -> list[CardData] | None:
    """Parse card data from search_cards ToolMessages in the graph result."""
    cards = []
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name == "search_cards":
            try:
                data = json.loads(msg.content)
                for card in data.get("cards", []):
                    cards.append(CardData(**card))
            except (json.JSONDecodeError, TypeError):
                pass
    return cards if cards else None


def _extract_rules(messages: list) -> list[RuleGrounding] | None:
    """Parse rule grounding data from search_rules ToolMessages in the graph result."""
    rules = []
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name == "search_rules":
            try:
                data = json.loads(msg.content)
                for rule in data.get("rules", []):
                    rules.append(RuleGrounding(
                        rule_id=str(rule.get("rule_id", "Unknown")),
                        page=int(rule.get("page", 0)),
                        text=str(rule.get("text", ""))
                    ))
            except (json.JSONDecodeError, TypeError):
                pass
    return rules if rules else None


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
        cards = _extract_cards(result["messages"])
        rules = _extract_rules(result["messages"])
        return ChatResponse(response=assistant_msg, cards=cards, rules=rules)
    except Exception as e:
        logger.error("Error in /chat endpoint: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
