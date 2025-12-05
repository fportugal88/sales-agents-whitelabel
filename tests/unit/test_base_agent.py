"""Unit tests for BaseAgent."""

import pytest

from src.agents.base_agent import BaseAgent
from src.config.agent_configs import AgentConfig
from src.models.conversation import Conversation, ConversationStage, MessageRole
from tests.fixtures.sample_data import create_sample_conversation


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    async def process(self, message: str, conversation, context=None):
        """Process message."""
        return {"response": "Test response"}

    async def should_activate(self, message: str, conversation, context=None):
        """Determine if should activate."""
        return True


@pytest.mark.asyncio
async def test_base_agent_initialization():
    """Test BaseAgent initialization."""
    config = AgentConfig(
        agent_id="test_agent",
        name="Test Agent",
        description="Test agent description",
    )
    agent = ConcreteAgent(agent_id="test_agent", config=config)

    assert agent.agent_id == "test_agent"
    assert agent.config == config
    assert agent.is_enabled() is True


@pytest.mark.asyncio
async def test_base_agent_add_message():
    """Test adding message to conversation."""
    agent = ConcreteAgent(agent_id="test_agent")
    conversation = create_sample_conversation()

    initial_count = len(conversation.messages)
    agent.add_message_to_conversation(conversation, "Test message")

    assert len(conversation.messages) == initial_count + 1
    assert conversation.messages[-1].content == "Test message"
    assert conversation.messages[-1].agent_id == "test_agent"


@pytest.mark.asyncio
async def test_base_agent_update_stage():
    """Test updating conversation stage."""
    agent = ConcreteAgent(agent_id="test_agent")
    conversation = create_sample_conversation()

    old_stage = conversation.current_stage
    agent.update_conversation_stage(conversation, ConversationStage.QUALIFICATION)

    assert conversation.current_stage == ConversationStage.QUALIFICATION
    assert conversation.active_agent == "test_agent"
    assert conversation.current_stage != old_stage


@pytest.mark.asyncio
async def test_base_agent_is_enabled():
    """Test agent enabled check."""
    # Enabled agent
    config = AgentConfig(agent_id="test", name="Test", description="Test", enabled=True)
    agent = ConcreteAgent(agent_id="test", config=config)
    assert agent.is_enabled() is True

    # Disabled agent
    config = AgentConfig(agent_id="test", name="Test", description="Test", enabled=False)
    agent = ConcreteAgent(agent_id="test", config=config)
    assert agent.is_enabled() is False

    # Agent without config (defaults to enabled)
    agent = ConcreteAgent(agent_id="test")
    assert agent.is_enabled() is True

