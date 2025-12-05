"""Sales pipeline model for tracking conversion metrics."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Stages in the sales pipeline."""

    LEAD_GEN = "lead_generation"
    QUALIFICATION = "qualification"
    PRESENTATION = "presentation"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"


class StageMetrics(BaseModel):
    """Metrics for a specific pipeline stage."""

    stage: PipelineStage = Field(..., description="Pipeline stage")
    total_leads: int = Field(default=0, description="Total leads in this stage")
    converted: int = Field(default=0, description="Leads converted to next stage")
    lost: int = Field(default=0, description="Leads lost at this stage")
    avg_time_hours: float = Field(default=0.0, description="Average time in hours")
    conversion_rate: float = Field(default=0.0, description="Conversion rate (0-1)")

    def calculate_conversion_rate(self) -> None:
        """Calculate conversion rate."""
        total = self.total_leads
        if total > 0:
            self.conversion_rate = self.converted / total
        else:
            self.conversion_rate = 0.0


class SalesPipeline(BaseModel):
    """Sales pipeline tracking overall metrics."""

    id: str = Field(..., description="Pipeline identifier")
    name: str = Field(..., description="Pipeline name")
    stages: Dict[PipelineStage, StageMetrics] = Field(
        default_factory=dict, description="Stage metrics"
    )
    total_leads: int = Field(default=0, description="Total leads in pipeline")
    total_converted: int = Field(default=0, description="Total converted leads")
    overall_conversion_rate: float = Field(default=0.0, description="Overall conversion rate")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    def add_stage_metrics(self, stage: PipelineStage, metrics: StageMetrics) -> None:
        """Add or update stage metrics."""
        self.stages[stage] = metrics
        self.updated_at = datetime.utcnow()
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        """Recalculate total pipeline metrics."""
        self.total_leads = sum(stage.total_leads for stage in self.stages.values())
        self.total_converted = sum(stage.converted for stage in self.stages.values())
        if self.total_leads > 0:
            self.overall_conversion_rate = self.total_converted / self.total_leads
        else:
            self.overall_conversion_rate = 0.0

    def get_stage_metrics(self, stage: PipelineStage) -> Optional[StageMetrics]:
        """Get metrics for a specific stage."""
        return self.stages.get(stage)

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}

