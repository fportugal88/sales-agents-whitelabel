"""Swarm orchestrator using Strands Agents."""

import time
from typing import Any, AsyncIterator, Dict, List, Optional
from collections import defaultdict
from datetime import datetime

from src.agents.swarm_sales_agent import SwarmSalesAgent
from src.config.settings import Settings
from src.models.conversation import Conversation, ConversationStage, MessageRole
from src.utils.logger import LoggerMixin


class SwarmOrchestrator(LoggerMixin):
    """Orchestrator using Strands Agents Swarm pattern."""

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        """Initialize Swarm orchestrator.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.conversations: Dict[str, Conversation] = {}
        
        # Initialize Swarm agent
        self.swarm_agent = SwarmSalesAgent(
            settings=settings,
            default_cnpj=settings.default_client_cnpj,
        )
        
        # Metrics tracking
        self.metrics = {
            "conversations_total": 0,
            "conversations_by_stage": defaultdict(int),
            "stage_transitions": defaultdict(int),
            "agents_usage": defaultdict(int),
            "conversion_by_stage": defaultdict(int),
            "time_by_stage": defaultdict(list),
            "abandonment_points": defaultdict(int),
            "completed_conversations": 0,
            "closed_sales": 0,
        }
        
        self.logger.info("Swarm Orchestrator inicializado")

    async def create_conversation(
        self,
        lead_id: Optional[str] = None,
        initial_message: Optional[str] = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            lead_id: Optional lead ID to associate
            initial_message: Optional initial message

        Returns:
            New conversation instance
        """
        import uuid
        
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            lead_id=lead_id,
            current_stage=ConversationStage.FAQ,
        )

        if initial_message:
            conversation.add_message(
                role=MessageRole.USER,
                content=initial_message,
            )

        self.conversations[conversation_id] = conversation
        
        # Track conversation start
        self.metrics["conversations_total"] += 1
        self.metrics["conversations_by_stage"][ConversationStage.FAQ.value] += 1
        
        # Store start time for metrics
        if "metadata" not in conversation.metadata:
            conversation.metadata = {}
        conversation.metadata["started_at"] = time.time()
        conversation.metadata["stage_times"] = {ConversationStage.FAQ.value: time.time()}

        self.logger.info(
            "Conversation created",
            conversation_id=conversation_id,
            lead_id=lead_id,
        )

        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation instance or None if not found
        """
        return self.conversations.get(conversation_id)

    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a user message through the Swarm.

        Args:
            message: User message to process
            conversation_id: Optional conversation ID (creates new if not provided)
            context: Additional context

        Returns:
            Response dictionary with agent response and telemetry
        """
        # Get or create conversation
        if conversation_id:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                return {"error": "Conversation not found", "conversation_id": conversation_id}
        else:
            conversation = await self.create_conversation(initial_message=message)

        # Add user message to conversation
        conversation.add_message(role=MessageRole.USER, content=message)

        self.logger.info(
            "Processing message with Swarm",
            conversation_id=conversation.id,
            message_length=len(message),
        )

        # Track processing start time
        process_start_time = time.time()
        old_stage = conversation.current_stage

        try:
            # Process with Swarm
            result = await self.swarm_agent.process(message, context)
            
            # Extract response
            response_text = result.get("response", "")
            
            # Add agent response to conversation
            if response_text:
                conversation.add_message(
                    role=MessageRole.AGENT,
                    content=response_text,
                    agent_id="swarm",
                    metadata={
                        "telemetry": result.get("telemetry", {}),
                        "node_history": result.get("node_history", []),
                        "status": result.get("status", "completed"),
                    },
                )

            # Determine current stage based on agents used
            agents_used = result.get("telemetry", {}).get("agents_used", [])
            node_history = result.get("node_history", [])
            
            # Get the last active agent from node history
            last_agent = "researcher"
            if node_history:
                last_node = node_history[-1]
                last_agent = last_node.get("node_id", "researcher")
            elif agents_used:
                last_agent = agents_used[-1]
            
            # Map agent to stage
            stage_mapping = {
                "researcher": ConversationStage.FAQ,
                "sales_agent": ConversationStage.QUALIFICATION,
                "qualification_agent": ConversationStage.QUALIFICATION,
                "presentation_agent": ConversationStage.PRESENTATION,
                "negotiation_agent": ConversationStage.NEGOTIATION,
                "closing_agent": ConversationStage.CLOSING,
            }
            
            new_stage = stage_mapping.get(last_agent, ConversationStage.FAQ)
            
            # Track stage transition and metrics
            if old_stage != new_stage:
                self._track_stage_transition(conversation, old_stage, new_stage, process_start_time)
            
            conversation.current_stage = new_stage
            conversation.active_agent = last_agent
            
            # Track agent usage
            for agent in agents_used:
                self.metrics["agents_usage"][agent] += 1
            
            # Track conversion if reached closing stage
            if new_stage == ConversationStage.CLOSING:
                self.metrics["conversion_by_stage"][ConversationStage.CLOSING.value] += 1
                if "closing_agent" in agents_used:
                    self.metrics["closed_sales"] += 1
                    conversation.metadata["sale_closed"] = True
                    conversation.metadata["closed_at"] = time.time()
            
            # Track completion
            if new_stage == ConversationStage.COMPLETED:
                self.metrics["completed_conversations"] += 1
                conversation.metadata["completed_at"] = time.time()

            return {
                "conversation_id": conversation.id,
                "response": response_text,
                "agent_id": agents_used[-1] if agents_used else "swarm",
                "stage": conversation.current_stage.value,
                "metadata": {
                    "telemetry": result.get("telemetry", {}),
                    "node_history": result.get("node_history", []),
                    "execution_count": result.get("execution_count", 0),
                    "execution_time": result.get("execution_time", 0),
                    "accumulated_usage": result.get("accumulated_usage", {}),
                    "status": result.get("status", "completed"),
                },
            }
        except Exception as e:
            self.logger.error(
                "Erro ao processar mensagem com Swarm",
                error=str(e),
                conversation_id=conversation.id,
                exc_info=True,
            )
            
            return {
                "error": "Erro ao processar mensagem",
                "conversation_id": conversation.id,
                "error_type": type(e).__name__,
            }

    async def stream_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream events from Swarm execution.

        Args:
            message: User message to process
            conversation_id: Optional conversation ID
            context: Additional context

        Yields:
            Event dictionaries from Swarm
        """
        # Get or create conversation
        if conversation_id:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                yield {
                    "type": "error",
                    "error": "Conversation not found",
                    "conversation_id": conversation_id,
                }
                return
        else:
            conversation = await self.create_conversation(initial_message=message)

        # Add user message to conversation
        conversation.add_message(role=MessageRole.USER, content=message)

        try:
            # Stream events from Swarm
            async for event in self.swarm_agent.stream(message, context):
                event["conversation_id"] = conversation.id
                yield event
        except Exception as e:
            self.logger.error(
                "Erro ao fazer streaming com Swarm",
                error=str(e),
                conversation_id=conversation.id,
                exc_info=True,
            )
            
            yield {
                "type": "error",
                "error": "Erro ao processar mensagem",
                "error_type": type(e).__name__,
                "conversation_id": conversation.id,
            }
    
    def _track_stage_transition(
        self,
        conversation: Conversation,
        old_stage: ConversationStage,
        new_stage: ConversationStage,
        transition_start_time: float,
    ) -> None:
        """Track stage transition for conversion metrics."""
        # Track transition
        transition_key = f"{old_stage.value}->{new_stage.value}"
        self.metrics["stage_transitions"][transition_key] += 1
        
        # Track time spent in old stage
        if "stage_times" not in conversation.metadata:
            conversation.metadata["stage_times"] = {}
        
        # Calculate time in old stage
        if old_stage.value in conversation.metadata["stage_times"]:
            time_in_stage = transition_start_time - conversation.metadata["stage_times"][old_stage.value]
            self.metrics["time_by_stage"][old_stage.value].append(time_in_stage)
        
        # Record new stage start time
        conversation.metadata["stage_times"][new_stage.value] = transition_start_time
        
        # Track conversion by stage
        self.metrics["conversion_by_stage"][new_stage.value] += 1
        self.metrics["conversations_by_stage"][new_stage.value] += 1
    
    def get_conversion_metrics(self) -> Dict[str, Any]:
        """Get conversion metrics for analysis."""
        # Calculate average time by stage
        avg_time_by_stage = {}
        for stage, times in self.metrics["time_by_stage"].items():
            if times:
                avg_time_by_stage[stage] = sum(times) / len(times)
        
        # Calculate conversion rates
        total_conversations = self.metrics["conversations_total"]
        conversion_rates = {}
        if total_conversations > 0:
            for stage, count in self.metrics["conversion_by_stage"].items():
                conversion_rates[stage] = (count / total_conversations) * 100
        
        # Calculate abandonment rate
        abandonment_rate = 0.0
        if total_conversations > 0:
            completed = self.metrics["completed_conversations"]
            abandonment_rate = ((total_conversations - completed) / total_conversations) * 100
        
        # Calculate sales conversion rate
        sales_conversion_rate = 0.0
        if total_conversations > 0:
            sales_conversion_rate = (self.metrics["closed_sales"] / total_conversations) * 100
        
        return {
            "total_conversations": total_conversations,
            "completed_conversations": self.metrics["completed_conversations"],
            "closed_sales": self.metrics["closed_sales"],
            "sales_conversion_rate": sales_conversion_rate,
            "abandonment_rate": abandonment_rate,
            "conversations_by_stage": dict(self.metrics["conversations_by_stage"]),
            "conversion_by_stage": dict(self.metrics["conversion_by_stage"]),
            "conversion_rates_by_stage": conversion_rates,
            "stage_transitions": dict(self.metrics["stage_transitions"]),
            "agents_usage": dict(self.metrics["agents_usage"]),
            "average_time_by_stage": avg_time_by_stage,
            "abandonment_points": dict(self.metrics["abandonment_points"]),
        }
