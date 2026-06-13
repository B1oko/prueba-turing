import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from src.tools import CreateCustomCardTool, SearchCardsTool, SearchRulesTool
from src.clients.mtg_client import MTGCard

@pytest.mark.anyio
async def test_search_rules():
    mock_doc = MagicMock()
    mock_doc.page_content = "100.1. Magic is a game."
    mock_doc.metadata = {"rule_id": "100.1", "page": 1}

    mock_vs = MagicMock()
    mock_vs.asimilarity_search = AsyncMock(return_value=[mock_doc])

    tool = SearchRulesTool(vectorstore=mock_vs)
    result = await tool._arun(query="What is Magic?")

    assert "100.1" in result
    assert "Magic is a game." in result
    mock_vs.asimilarity_search.assert_called_once_with("What is Magic?", k=5)

@pytest.mark.anyio
async def test_search_cards():
    mock_card = MTGCard(
        name="Battlefield Raptor",
        manaCost="{W}",
        type="Creature - Bird Soldier",
        text="Flying, first strike",
        power="1",
        toughness="2",
        imageUrl="http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=503615&type=card",
    )
    
    mock_client = MagicMock()
    mock_client.search_cards = AsyncMock(return_value=[mock_card])

    tool = SearchCardsTool(client=mock_client)
    result, artifact = await tool._arun(name="Battlefield Raptor")

    assert "Battlefield Raptor" in result
    assert "mana_cost" in artifact
    assert "{W}" in artifact
    assert "Creature - Bird Soldier" in artifact
    assert "Flying, first strike" in artifact
    assert '"power": "1"' in artifact
    assert '"toughness": "2"' in artifact

def test_create_custom_card():
    mock_agent = MagicMock()
    mock_agent.run.return_value = {
        "card_specs": {
            "name": "Test Hero",
            "mana_cost": "{1}{R}{W}",
            "colors": ["Red", "White"],
            "type_line": "Legendary Creature - Warrior",
            "rules_text": "First strike. Haste. Whenever this attacks, draw a card.",
            "power": "3",
            "toughness": "2",
        },
        "card_path": "custom_cards/test_hero.png"
    }

    tool = CreateCustomCardTool(agent=mock_agent)
    result = tool._run(description="Create a test hero")

    assert "Test Hero" in result
    assert "custom_cards/test_hero.png" in result
