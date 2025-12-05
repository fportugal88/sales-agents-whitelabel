"""Unit tests for FAQAgent."""

import pytest

from src.agents.faq_agent import FAQAgent
from src.models.conversation import ConversationStage
from src.mcp_servers.mock_catalog_server import MockCatalogServer
from tests.fixtures.sample_data import create_sample_conversation


@pytest.fixture
def catalog_server():
    """Create catalog server fixture."""
    return MockCatalogServer(simulate_latency=False)


@pytest.fixture
def faq_agent(catalog_server):
    """Create FAQ agent fixture."""
    return FAQAgent(catalog_server=catalog_server)


@pytest.mark.asyncio
async def test_faq_agent_should_activate(faq_agent):
    """Test FAQ agent activation logic."""
    conversation = create_sample_conversation(stage=ConversationStage.FAQ)

    # Should activate in FAQ stage
    result = await faq_agent.should_activate("Hello", conversation)
    assert result is True

    # Should activate for product questions
    result = await faq_agent.should_activate("What products do you have?", conversation)
    assert result is True

    # Should activate for questions
    result = await faq_agent.should_activate("How does it work?", conversation)
    assert result is True


@pytest.mark.asyncio
async def test_faq_agent_process(faq_agent):
    """Test FAQ agent processing."""
    conversation = create_sample_conversation()

    result = await faq_agent.process("What products do you have?", conversation)

    assert "response" in result
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0
    assert "metadata" in result


@pytest.mark.asyncio
async def test_faq_agent_intent_analysis(faq_agent):
    """Test intent analysis."""
    # Buying intent
    intent = faq_agent._analyze_intent("I'm interested in buying your product")
    assert intent["buying_intent"] is True

    # Product interest
    intent = faq_agent._analyze_intent("Tell me about your features")
    assert intent["product_interest"] is True

    # Contact info
    intent = faq_agent._analyze_intent("My email is test@example.com")
    assert intent["has_email"] is True

