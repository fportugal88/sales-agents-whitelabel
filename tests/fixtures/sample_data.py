"""Sample data fixtures for testing."""

from datetime import datetime

from src.models.conversation import Conversation, ConversationStage, Message, MessageRole
from src.models.lead import BANTScore, Lead, LeadPriority, LeadStatus


def create_sample_lead(
    lead_id: str = "test_lead_001",
    email: str = "test@example.com",
    name: str = "Test User",
    company: str = "Test Company",
) -> Lead:
    """Create a sample lead for testing.

    Args:
        lead_id: Lead ID
        email: Lead email
        name: Lead name
        company: Company name

    Returns:
        Sample Lead instance
    """
    return Lead(
        id=lead_id,
        email=email,
        name=name,
        company=company,
        status=LeadStatus.NEW,
        priority=LeadPriority.COLD,
        bant_score=BANTScore(budget=0.5, authority=0.5, need=0.5, timeline=0.5),
    )


def create_sample_conversation(
    conversation_id: str = "test_conv_001",
    lead_id: str = "test_lead_001",
    stage: ConversationStage = ConversationStage.FAQ,
) -> Conversation:
    """Create a sample conversation for testing.

    Args:
        conversation_id: Conversation ID
        lead_id: Lead ID
        stage: Conversation stage

    Returns:
        Sample Conversation instance
    """
    conversation = Conversation(
        id=conversation_id,
        lead_id=lead_id,
        current_stage=stage,
    )

    # Add initial message
    conversation.add_message(
        role=MessageRole.USER,
        content="What products do you have?",
    )

    return conversation


def create_sample_bant_score() -> BANTScore:
    """Create a sample BANT score.

    Returns:
        Sample BANTScore instance
    """
    return BANTScore(budget=0.8, authority=0.7, need=0.9, timeline=0.6)

