import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage, HumanMessage
from src.agent.mtg_agent import MTGAgent

def test_agent_graph_execution():
    # Setup mock LLM
    mock_llm = MagicMock()
    
    # Mock bind_tools to return a model with tools bound
    mock_bound_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_bound_llm
    
    # Mock LLM response: returns a standard text message
    mock_bound_llm.invoke.return_value = AIMessage(
        content="¡Hola! Soy tu asistente de Magic. ¿En qué te puedo ayudar hoy?"
    )
    
    # Instantiate MTGAgent with mock LLM and empty tools list
    agent = MTGAgent(llm=mock_llm, tools=[])
        
    # Execute graph with a user message
    config = {"configurable": {"thread_id": "test_thread"}}
    result = agent.invoke(
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
