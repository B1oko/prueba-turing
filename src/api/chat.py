import json
import logging

from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage, ToolMessage
from pydantic import BaseModel

from src.models import Card

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str


class RuleGrounding(BaseModel):
    rule_id: str
    page: int
    text: str


class ChatResponse(BaseModel):
    response: str
    cards: list[Card] | None = None
    rules: list[RuleGrounding] | None = None


def _extract_cards(messages: list) -> list[Card] | None:
    cards = []
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name == "search_cards":
            try:
                raw = msg.artifact if msg.artifact is not None else msg.content
                data = json.loads(raw)
                for card in data.get("cards", []):
                    cards.append(Card(**card))
            except (json.JSONDecodeError, TypeError):
                pass
    return cards if cards else None


def _extract_rules(messages: list) -> list[RuleGrounding] | None:
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
async def chat(req: Request, chat_request: ChatRequest):
    try:
        graph = req.app.state.graph
        config = {"configurable": {"thread_id": chat_request.session_id}}
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=chat_request.message)]}, config=config
        )

        raw_content = result["messages"][-1].content
        if isinstance(raw_content, list):
            assistant_msg = "".join(
                block.get("text", "") for block in raw_content if isinstance(block, dict)
            )
        else:
            assistant_msg = raw_content

        # Only look at messages from the current turn (after the last HumanMessage)
        last_human_idx = next(
            (len(result["messages"]) - 1 - i
             for i, msg in enumerate(reversed(result["messages"]))
             if isinstance(msg, HumanMessage)),
            0
        )
        current_turn_messages = result["messages"][last_human_idx:]

        cards = _extract_cards(current_turn_messages)
        rules = _extract_rules(current_turn_messages)

        return ChatResponse(response=assistant_msg, cards=cards, rules=rules)
    except Exception as e:
        logger.error("Error in /chat endpoint for session_id '%s': %s", chat_request.session_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
