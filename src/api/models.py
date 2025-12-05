"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message request model."""

    message: str = Field(..., description="Mensagem do usuário")
    conversation_id: Optional[str] = Field(None, description="ID da conversa (opcional)")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")


class ChatResponse(BaseModel):
    """Chat response model."""

    conversation_id: str = Field(..., description="ID da conversa")
    response: str = Field(..., description="Resposta do agente")
    agent_id: str = Field(..., description="ID do agente que processou")
    stage: str = Field(..., description="Estágio atual do funil")
    next_agent: Optional[str] = Field(None, description="Próximo agente sugerido")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais")


class ConversationHistory(BaseModel):
    """Conversation history model."""

    conversation_id: str = Field(..., description="ID da conversa")
    messages: List[Dict[str, Any]] = Field(..., description="Histórico de mensagens")
    current_stage: str = Field(..., description="Estágio atual")
    lead_id: Optional[str] = Field(None, description="ID do lead associado")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Status do serviço")
    agents_count: int = Field(..., description="Número de agentes registrados")
    active_conversations: int = Field(..., description="Número de conversas ativas")


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    timestamp: datetime = Field(..., description="When the decision was made")
    agent_id: str = Field(..., description="Agent that made the decision")
    decision_type: str = Field(..., description="Type of decision")
    reasoning: Optional[str] = Field(None, description="LLM reasoning")
    tools_used: List[str] = Field(default_factory=list, description="Tools used")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


class AuditLogsResponse(BaseModel):
    """Audit logs response for a conversation."""

    conversation_id: str = Field(..., description="Conversation ID")
    total_logs: int = Field(..., description="Total number of audit logs")
    logs: List[AuditLogResponse] = Field(..., description="List of audit logs")

