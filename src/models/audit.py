"""Audit logging model for tracking agent decisions and reasoning."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    """Types of decisions that can be logged."""

    AGENT_SELECTION = "agent_selection"
    TOOL_CALL = "tool_call"
    STAGE_TRANSITION = "stage_transition"
    SCRIPT_STEP = "script_step"
    RESPONSE_GENERATION = "response_generation"
    CONTEXT_UPDATE = "context_update"
    OTHER = "other"


class AuditLog(BaseModel):
    """Audit log entry for tracking agent decisions and reasoning.

    This model captures all decisions made by agents during a conversation,
    including reasoning, tools used, and context.
    """

    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the decision was made"
    )
    agent_id: str = Field(..., description="Agent that made the decision")
    decision_type: DecisionType = Field(..., description="Type of decision")
    reasoning: Optional[str] = Field(
        None, description="LLM reasoning or explanation for the decision"
    )
    tools_used: List[str] = Field(
        default_factory=list, description="List of tools called during this decision"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Context used in the decision"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    message_id: Optional[str] = Field(
        None, description="Associated message ID if applicable"
    )
    conversation_id: Optional[str] = Field(
        None, description="Associated conversation ID"
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class AuditLogSummary(BaseModel):
    """Summary of audit logs for a conversation."""

    total_decisions: int = Field(..., description="Total number of decisions")
    agents_used: List[str] = Field(..., description="List of agents that were used")
    tools_used: List[str] = Field(..., description="List of all tools used")
    decision_types: Dict[str, int] = Field(
        ..., description="Count of each decision type"
    )
    latest_decision: Optional[AuditLog] = Field(
        None, description="Most recent decision"
    )
    logs: List[AuditLog] = Field(..., description="All audit logs")




