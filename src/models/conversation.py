"""Conversation model for tracking agent interactions."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role in conversation."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class Message(BaseModel):
    """Single message in a conversation."""

    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    agent_id: Optional[str] = Field(None, description="Agent that generated this message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ConversationStage(str, Enum):
    """Current stage in the sales conversation."""

    FAQ = "faq"
    LEAD_GENERATION = "lead_generation"
    QUALIFICATION = "qualification"
    PRESENTATION = "presentation"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    COMPLETED = "completed"


class Conversation(BaseModel):
    """Conversation model tracking the entire sales interaction."""

    id: str = Field(..., description="Unique conversation identifier")
    lead_id: Optional[str] = Field(None, description="Associated lead ID")
    messages: List[Message] = Field(default_factory=list, description="Conversation messages")
    current_stage: ConversationStage = Field(
        default=ConversationStage.FAQ, description="Current conversation stage"
    )
    active_agent: Optional[str] = Field(None, description="Currently active agent ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for agents")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    def add_message(
        self,
        role: MessageRole,
        content: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a message to the conversation."""
        message = Message(
            role=role,
            content=content,
            agent_id=agent_id,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_messages_by_agent(self, agent_id: str) -> List[Message]:
        """Get all messages from a specific agent."""
        return [msg for msg in self.messages if msg.agent_id == agent_id]

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}

