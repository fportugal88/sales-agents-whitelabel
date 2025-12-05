"""Lead model for sales pipeline."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LeadStatus(str, Enum):
    """Lead status in the sales pipeline."""

    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    PRESENTATION = "presentation"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    NURTURING = "nurturing"


class LeadPriority(str, Enum):
    """Lead priority classification."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class BANTScore(BaseModel):
    """BANT (Budget, Authority, Need, Timeline) scoring."""

    budget: float = Field(default=0.0, ge=0.0, le=1.0, description="Budget score (0-1)")
    authority: float = Field(default=0.0, ge=0.0, le=1.0, description="Authority score (0-1)")
    need: float = Field(default=0.0, ge=0.0, le=1.0, description="Need score (0-1)")
    timeline: float = Field(default=0.0, ge=0.0, le=1.0, description="Timeline score (0-1)")

    @property
    def total_score(self) -> float:
        """Calculate total BANT score."""
        return (self.budget + self.authority + self.need + self.timeline) / 4.0


class Lead(BaseModel):
    """Lead model representing a potential customer."""

    id: str = Field(..., description="Unique lead identifier")
    email: Optional[EmailStr] = Field(None, description="Lead email address")
    name: Optional[str] = Field(None, description="Lead name")
    company: Optional[str] = Field(None, description="Company name")
    phone: Optional[str] = Field(None, description="Phone number")
    status: LeadStatus = Field(default=LeadStatus.NEW, description="Current lead status")
    priority: LeadPriority = Field(default=LeadPriority.COLD, description="Lead priority")
    bant_score: Optional[BANTScore] = Field(None, description="BANT qualification score")
    source: Optional[str] = Field(None, description="Lead source")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    assigned_agent: Optional[str] = Field(None, description="Assigned agent ID")

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}

