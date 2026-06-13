import os
from unittest.mock import MagicMock
from src.tools import CreateCustomCardTool, SearchCardsTool, SearchRulesTool


def test_search_rules():
    mock_doc = MagicMock()
    mock_doc.page_content = "100.1. Magic is a game."
    mock_doc.metadata = {"rule_id": "100.1", "page": 1}

    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = [mock_doc]

    tool = SearchRulesTool(vectorstore=mock_vs)
    result = tool.invoke({"query": "What is Magic?"})

    assert "100.1" in result
    assert '"page": 1' in result
    assert "Magic is a game." in result
    mock_vs.similarity_search.assert_called_once_with("What is Magic?", k=5)


def test_search_cards():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "cards": [
            {
                "name": "Battlefield Raptor",
                "manaCost": "{W}",
                "type": "Creature - Bird Soldier",
                "text": "Flying, first strike",
                "power": "1",
                "toughness": "2",
                "imageUrl": "http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=503615&type=card",
            }
        ]
    }

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    tool = SearchCardsTool(session=mock_session)
    result = tool.invoke({"name": "Battlefield Raptor"})

    assert "Battlefield Raptor" in result
    assert "mana_cost" in result
    assert "{W}" in result
    assert "Creature - Bird Soldier" in result
    assert "Flying, first strike" in result
    assert '"power": "1"' in result
    assert '"toughness": "2"' in result


def test_create_custom_card():
    tool = CreateCustomCardTool()
    result = tool.invoke({
        "name": "Test Hero",
        "mana_cost": "{1}{R}{W}",
        "colors": ["Red", "White"],
        "type_line": "Legendary Creature - Warrior",
        "rules_text": "First strike. Haste. Whenever this attacks, draw a card.",
        "power": "3",
        "toughness": "2",
    })

    assert "Success" in result
    expected_path = os.path.join("custom_cards", "test_hero.png")
    assert os.path.exists(expected_path)

    os.remove(expected_path)
    if os.path.exists("custom_cards") and not os.listdir("custom_cards"):
        os.rmdir("custom_cards")
