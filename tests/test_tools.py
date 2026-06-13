import os
import shutil
import pytest
from unittest.mock import MagicMock, patch
from src.tools.rules_tool import search_rules
from src.tools.card_search_tool import search_cards
from src.tools.card_image_tool import get_card_image, create_custom_card

# 1. Test rules search tool (mocking vectorstore)
@patch("src.tools.rules_tool.get_vectorstore")
def test_search_rules(mock_get_vs):
    # Setup mock documents
    mock_doc = MagicMock()
    mock_doc.page_content = "100.1. Magic is a game."
    mock_doc.metadata = {"rule_id": "100.1", "page": 1}
    
    mock_vs = MagicMock()
    mock_vs.similarity_search.return_value = [mock_doc]
    mock_get_vs.return_value = mock_vs
    
    # Run tool using .invoke()
    result = search_rules.invoke({"query": "What is Magic?"})
    
    # Verify results
    assert "Rule 100.1" in result
    assert "Page 1" in result
    assert "Magic is a game." in result
    mock_vs.similarity_search.assert_called_once_with("What is Magic?", k=5)


# 2. Test card search tool (mocking requests.get)
@patch("src.tools.card_search_tool.requests.get")
def test_search_cards(mock_get):
    # Setup mock response
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
                "imageUrl": "http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=503615&type=card"
            }
        ]
    }
    mock_get.return_value = mock_resp
    
    # Run tool using .invoke()
    result = search_cards.invoke({"name": "Battlefield Raptor"})
    
    # Verify results
    assert "Battlefield Raptor" in result
    assert "mana_cost" in result
    assert "{W}" in result
    assert "Creature - Bird Soldier" in result
    assert "Flying, first strike" in result
    assert '"power": "1"' in result
    assert '"toughness": "2"' in result


# 3. Test card image retrieval (mocking requests.get)
@patch("src.tools.card_image_tool.requests.get")
def test_get_card_image(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "cards": [
            {
                "name": "Black Lotus",
                "imageUrl": "http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=600&type=card"
            }
        ]
    }
    mock_get.return_value = mock_resp
    
    # Run tool using .invoke()
    result = get_card_image.invoke({"card_name": "Black Lotus"})
    assert "Black Lotus" in result
    assert "http://gatherer.wizards.com/Handlers/Image.ashx" in result


# 4. Test custom card generator (Integration test with Pillow)
def test_create_custom_card():
    card_name = "Test Hero"
    # Execute card drawing using .invoke()
    result = create_custom_card.invoke({
        "name": card_name,
        "mana_cost": "{1}{R}{W}",
        "colors": ["Red", "White"],
        "type_line": "Legendary Creature - Warrior",
        "rules_text": "First strike. Haste. Whenever this attacks, draw a card.",
        "power": "3",
        "toughness": "2"
    })
    
    # Check that image is created
    assert "Success" in result
    expected_path = os.path.join("custom_cards", "test_hero.png")
    assert os.path.exists(expected_path)
    
    # Clean up generated file and folder
    if os.path.exists(expected_path):
        os.remove(expected_path)
    if os.path.exists("custom_cards") and not os.listdir("custom_cards"):
        os.rmdir("custom_cards")
