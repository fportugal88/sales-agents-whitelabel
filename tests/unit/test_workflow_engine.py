"""Unit tests for WorkflowEngine."""

import pytest

from src.models.conversation import ConversationStage
from src.orchestrator.workflow_engine import WorkflowEngine
from tests.fixtures.sample_data import create_sample_conversation


@pytest.fixture
def workflow_engine():
    """Create workflow engine fixture."""
    return WorkflowEngine()


def test_workflow_can_transition(workflow_engine):
    """Test stage transition validation."""
    # Valid transition
    assert workflow_engine.can_transition(
        ConversationStage.FAQ, ConversationStage.LEAD_GENERATION
    ) is True

    # Invalid transition
    assert workflow_engine.can_transition(
        ConversationStage.CLOSING, ConversationStage.FAQ
    ) is False


def test_workflow_get_next_stages(workflow_engine):
    """Test getting next stages."""
    next_stages = workflow_engine.get_next_stages(ConversationStage.FAQ)
    assert ConversationStage.LEAD_GENERATION in next_stages
    assert ConversationStage.QUALIFICATION in next_stages


def test_workflow_suggest_next_stage(workflow_engine):
    """Test suggesting next stage."""
    conversation = create_sample_conversation(stage=ConversationStage.FAQ)

    # Suggest with context
    context = {"suggested_stage": "lead_generation"}
    suggested = workflow_engine.suggest_next_stage(conversation, context)
    assert suggested == ConversationStage.LEAD_GENERATION

    # Suggest without context
    suggested = workflow_engine.suggest_next_stage(conversation)
    assert suggested is not None


def test_workflow_validate_conversation(workflow_engine):
    """Test conversation validation."""
    conversation = create_sample_conversation()

    result = workflow_engine.validate_conversation_state(conversation)
    assert "valid" in result
    assert isinstance(result["valid"], bool)

