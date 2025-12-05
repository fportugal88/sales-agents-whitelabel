"""Metrics system for tracking conversion rates and analytics."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.models.sales_pipeline import PipelineStage, SalesPipeline, StageMetrics
from src.utils.logger import LoggerMixin

if TYPE_CHECKING:
    from src.tools.analytics_tool import AnalyticsTool


class MetricsCollector(LoggerMixin):
    """Collector for sales metrics and conversion tracking."""

    def __init__(self, analytics_tool: "AnalyticsTool") -> None:
        """Initialize metrics collector.

        Args:
            analytics_tool: Analytics tool for tracking events
        """
        self.analytics_tool = analytics_tool
        self.logger.info("Metrics collector initialized")

    async def track_stage_entry(
        self,
        stage: PipelineStage,
        lead_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        """Track when a lead enters a stage.

        Args:
            stage: Pipeline stage
            lead_id: Optional lead ID
            conversation_id: Optional conversation ID
            agent_id: Optional agent ID
        """
        try:
            await self.analytics_tool.track_event(
                event_type="stage_entry",
                stage=stage.value,
                lead_id=lead_id,
                metadata={
                    "conversation_id": conversation_id,
                    "agent_id": agent_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            self.logger.debug("Tracked stage entry", stage=stage.value, lead_id=lead_id)
        except Exception as e:
            self.logger.error("Failed to track stage entry", error=str(e), stage=stage.value)

    async def track_stage_exit(
        self,
        stage: PipelineStage,
        lead_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        next_stage: Optional[PipelineStage] = None,
        converted: bool = True,
    ) -> None:
        """Track when a lead exits a stage.

        Args:
            stage: Pipeline stage
            lead_id: Optional lead ID
            conversation_id: Optional conversation ID
            next_stage: Optional next stage (if converted)
            converted: Whether lead converted to next stage
        """
        try:
            await self.analytics_tool.track_event(
                event_type="stage_exit",
                stage=stage.value,
                lead_id=lead_id,
                metadata={
                    "conversation_id": conversation_id,
                    "next_stage": next_stage.value if next_stage else None,
                    "converted": converted,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            self.logger.debug(
                "Tracked stage exit",
                stage=stage.value,
                lead_id=lead_id,
                converted=converted,
            )
        except Exception as e:
            self.logger.error("Failed to track stage exit", error=str(e), stage=stage.value)

    async def track_conversion(
        self,
        stage: PipelineStage,
        lead_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        product_id: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> None:
        """Track a conversion event.

        Args:
            stage: Pipeline stage where conversion occurred
            lead_id: Optional lead ID
            conversation_id: Optional conversation ID
            product_id: Optional product ID
            amount: Optional sale amount
        """
        try:
            await self.analytics_tool.track_event(
                event_type="conversion",
                stage=stage.value,
                lead_id=lead_id,
                metadata={
                    "conversation_id": conversation_id,
                    "product_id": product_id,
                    "amount": amount,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            self.logger.info("Tracked conversion", stage=stage.value, lead_id=lead_id)
        except Exception as e:
            self.logger.error("Failed to track conversion", error=str(e), stage=stage.value)


class MetricsCalculator(LoggerMixin):
    """Calculator for conversion metrics and analytics."""

    def __init__(self, analytics_tool: "AnalyticsTool") -> None:
        """Initialize metrics calculator.

        Args:
            analytics_tool: Analytics tool for retrieving data
        """
        self.analytics_tool = analytics_tool
        self.logger.info("Metrics calculator initialized")

    async def get_stage_conversion_rate(
        self,
        stage: PipelineStage,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        """Get conversion rate for a specific stage.

        Args:
            stage: Pipeline stage
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Conversion rate (0.0 to 1.0)
        """
        try:
            result = await self.analytics_tool.get_conversion_metrics(
                stage=stage.value,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
            )

            if result.get("success"):
                return result.get("conversion_rate", 0.0)

            return 0.0
        except Exception as e:
            self.logger.error(
                "Failed to get stage conversion rate",
                error=str(e),
                stage=stage.value,
            )
            return 0.0

    async def get_funnel_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> SalesPipeline:
        """Get complete funnel metrics.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            SalesPipeline with all stage metrics
        """
        try:
            result = await self.analytics_tool.get_funnel_analytics(
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None,
            )

            if not result.get("success"):
                return self._create_empty_pipeline()

            funnel_data = result.get("funnel", {})
            overall = result.get("overall", {})

            pipeline = SalesPipeline(
                id="main",
                name="Main Sales Pipeline",
                overall_conversion_rate=overall.get("conversion_rate", 0.0),
            )

            # Create stage metrics
            for stage in PipelineStage:
                stage_data = funnel_data.get(stage.value, {})
                metrics = StageMetrics(
                    stage=stage,
                    total_leads=stage_data.get("entries", 0),
                    converted=stage_data.get("exits", 0),
                    lost=stage_data.get("entries", 0) - stage_data.get("exits", 0),
                    conversion_rate=stage_data.get("conversion_rate", 0.0),
                )
                pipeline.add_stage_metrics(stage, metrics)

            return pipeline
        except Exception as e:
            self.logger.error("Failed to get funnel metrics", error=str(e))
            return self._create_empty_pipeline()

    def _create_empty_pipeline(self) -> SalesPipeline:
        """Create an empty pipeline.

        Returns:
            Empty SalesPipeline instance
        """
        pipeline = SalesPipeline(id="main", name="Main Sales Pipeline")

        for stage in PipelineStage:
            metrics = StageMetrics(stage=stage)
            pipeline.add_stage_metrics(stage, metrics)

        return pipeline

    async def get_agent_performance(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific agent.

        Args:
            agent_id: Agent identifier
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Agent performance dictionary
        """
        # This would require additional analytics tracking
        # For now, return placeholder
        return {
            "agent_id": agent_id,
            "conversations_handled": 0,
            "conversion_rate": 0.0,
            "avg_response_time": 0.0,
            "satisfaction_score": 0.0,
        }

    async def get_product_performance(
        self,
        product_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get performance metrics for products.

        Args:
            product_id: Optional product ID filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Product performance dictionary
        """
        # This would require additional analytics tracking
        # For now, return placeholder
        return {
            "product_id": product_id,
            "total_sales": 0,
            "conversion_rate": 0.0,
            "revenue": 0.0,
        }


class MetricsDashboard:
    """Dashboard for displaying metrics and analytics."""

    def __init__(
        self,
        metrics_calculator: "MetricsCalculator",
        metrics_collector: "MetricsCollector",
    ) -> None:
        """Initialize metrics dashboard.

        Args:
            metrics_calculator: Metrics calculator
            metrics_collector: Metrics collector
        """
        self.calculator = metrics_calculator
        self.collector = metrics_collector

    async def get_dashboard_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get complete dashboard data.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dashboard data dictionary
        """
        # Get funnel metrics
        pipeline = await self.calculator.get_funnel_metrics(start_date, end_date)

        # Get stage conversion rates
        stage_rates = {}
        for stage in PipelineStage:
            rate = await self.calculator.get_stage_conversion_rate(stage, start_date, end_date)
            stage_rates[stage.value] = rate

        return {
            "pipeline": pipeline.model_dump(),
            "stage_conversion_rates": stage_rates,
            "overall_conversion_rate": pipeline.overall_conversion_rate,
            "total_leads": pipeline.total_leads,
            "total_converted": pipeline.total_converted,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

