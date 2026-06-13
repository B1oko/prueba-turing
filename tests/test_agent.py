import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from src.config.settings import get_settings
from src.agent.graph import get_agent_graph

@patch("src.agent.graph.ChatGoogleGenerativeAI")
def test_agent_graph_execution(mock_chat_class):
    # Setup mock LLM
    mock_llm = MagicMock()
    mock_chat_class.return_value = mock_llm
    
    # Mock bind_tools to return a model with tools bound
    mock_bound_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_bound_llm
    
    # Mock LLM response: returns a standard text message
    mock_bound_llm.invoke.return_value = AIMessage(
        content="¡Hola! Soy tu asistente de Magic. ¿En qué te puedo ayudar hoy?"
    )
    
    # Compile graph (with patched ChatGoogleGenerativeAI)
    get_settings.cache_clear()
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake_key"}, clear=False):
        graph = get_agent_graph()
        
    # Execute graph with a user message
    config = {"configurable": {"thread_id": "test_thread"}}
    result = graph.invoke(
        {"messages": [HumanMessage(content="Hola")]},
        config=config
    )
    
    # Assertions
    assert len(result["messages"]) > 1
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    assert "asistente de Magic" in last_msg.content
    
    # Check that the mock LLM was invoked
    mock_bound_llm.invoke.assert_called_once()
