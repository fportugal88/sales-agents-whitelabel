"""Mock Analytics MCP server for conversion metrics."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.mcp_servers.base_mcp import BaseMCPServer
from src.models.sales_pipeline import PipelineStage


class MockAnalyticsServer(BaseMCPServer):
    """Mock analytics server with conversion metrics."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 120.0,
    ) -> None:
        """Initialize mock analytics server.

        Args:
            base_url: Base URL (not used for mock, kept for compatibility)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds
        """
        super().__init__(
            server_name="mock_analytics",
            base_url=base_url,
            simulate_latency=simulate_latency,
            latency_ms=latency_ms,
        )
        self._events: List[Dict[str, Any]] = []
        self._initialize_mock_metrics()

    def _initialize_mock_metrics(self) -> None:
        """Initialize with sample metrics data."""
        # Create some sample events
        base_time = datetime.utcnow() - timedelta(days=30)

        for i in range(100):
            stage = list(PipelineStage)[i % len(PipelineStage)]
            self._events.append(
                {
                    "id": f"event_{i:03d}",
                    "event_type": "stage_entry",
                    "stage": stage.value,
                    "lead_id": f"lead_{i % 10:03d}",
                    "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                    "metadata": {"agent_id": f"agent_{i % 5}"},
                }
            )

    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call an analytics tool.

        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters

        Returns:
            Tool response

        Raises:
            ValueError: If tool_name is not found
            RuntimeError: If tool execution fails
        """
        await self._simulate_latency()
        self._validate_tool_exists(tool_name)

        params = parameters or {}

        if tool_name == "get_conversion_metrics":
            return await self._get_conversion_metrics(**params)
        elif tool_name == "get_funnel_analytics":
            return await self._get_funnel_analytics(**params)
        elif tool_name == "track_event":
            return await self._track_event(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_conversion_metrics(
        self,
        stage: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get conversion metrics for a stage or all stages.

        Args:
            stage: Optional stage to filter by
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            Conversion metrics dictionary
        """
        # Filter events
        events = self._events.copy()

        if stage:
            events = [e for e in events if e.get("stage") == stage]

        if start_date:
            events = [e for e in events if e.get("timestamp", "") >= start_date]

        if end_date:
            events = [e for e in events if e.get("timestamp", "") <= end_date]

        # Calculate metrics
        total_entries = len([e for e in events if e.get("event_type") == "stage_entry"])
        total_exits = len([e for e in events if e.get("event_type") == "stage_exit"])

        conversion_rate = total_exits / total_entries if total_entries > 0 else 0.0

        return {
            "success": True,
            "stage": stage or "all",
            "total_entries": total_entries,
            "total_exits": total_exits,
            "conversion_rate": round(conversion_rate, 4),
            "period": {
                "start": start_date or "all_time",
                "end": end_date or "now",
            },
        }

    async def _get_funnel_analytics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get funnel analytics for all stages.

        Args:
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            Funnel analytics dictionary
        """
        # Filter events
        events = self._events.copy()

        if start_date:
            events = [e for e in events if e.get("timestamp", "") >= start_date]

        if end_date:
            events = [e for e in events if e.get("timestamp", "") <= end_date]

        # Calculate metrics per stage
        funnel_data = {}

        for stage in PipelineStage:
            stage_events = [e for e in events if e.get("stage") == stage.value]
            entries = len([e for e in stage_events if e.get("event_type") == "stage_entry"])
            exits = len([e for e in stage_events if e.get("event_type") == "stage_exit"])

            funnel_data[stage.value] = {
                "entries": entries,
                "exits": exits,
                "conversion_rate": round(exits / entries, 4) if entries > 0 else 0.0,
            }

        # Calculate overall conversion
        total_entries = sum(data["entries"] for data in funnel_data.values())
        total_exits = sum(data["exits"] for data in funnel_data.values())
        overall_rate = total_exits / total_entries if total_entries > 0 else 0.0

        return {
            "success": True,
            "funnel": funnel_data,
            "overall": {
                "total_entries": total_entries,
                "total_exits": total_exits,
                "conversion_rate": round(overall_rate, 4),
            },
            "period": {
                "start": start_date or "all_time",
                "end": end_date or "now",
            },
        }

    async def _track_event(
        self,
        event_type: str,
        stage: str,
        lead_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Track an analytics event.

        Args:
            event_type: Type of event (e.g., 'stage_entry', 'stage_exit', 'conversion')
            stage: Pipeline stage
            lead_id: Optional lead ID
            metadata: Optional event metadata

        Returns:
            Tracking result dictionary
        """
        event = {
            "id": f"event_{len(self._events):06d}",
            "event_type": event_type,
            "stage": stage,
            "lead_id": lead_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        self._events.append(event)

        return {
            "success": True,
            "event_id": event["id"],
            "timestamp": event["timestamp"],
        }

    def list_tools(self) -> list[Dict[str, Any]]:
        """List available analytics tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "get_conversion_metrics",
                "description": "Get conversion metrics for a specific stage or all stages",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stage": {
                            "type": "string",
                            "description": "Pipeline stage",
                            "enum": [s.value for s in PipelineStage],
                        },
                        "start_date": {"type": "string", "description": "Start date (ISO format)"},
                        "end_date": {"type": "string", "description": "End date (ISO format)"},
                    },
                },
            },
            {
                "name": "get_funnel_analytics",
                "description": "Get complete funnel analytics for all stages",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date (ISO format)"},
                        "end_date": {"type": "string", "description": "End date (ISO format)"},
                    },
                },
            },
            {
                "name": "track_event",
                "description": "Track an analytics event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_type": {
                            "type": "string",
                            "description": "Event type (e.g., stage_entry, stage_exit, conversion)",
                        },
                        "stage": {
                            "type": "string",
                            "description": "Pipeline stage",
                            "enum": [s.value for s in PipelineStage],
                        },
                        "lead_id": {"type": "string", "description": "Optional lead ID"},
                        "metadata": {
                            "type": "object",
                            "description": "Optional event metadata",
                        },
                    },
                    "required": ["event_type", "stage"],
                },
            },
        ]

