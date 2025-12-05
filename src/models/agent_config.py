"""Pydantic models for agent configuration."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ScriptStep(BaseModel):
    """Model for a script step."""

    step: int = Field(..., description="Número da etapa (ordem de execução)")
    name: str = Field(..., description="Nome identificador da etapa")
    description: str = Field(..., description="Descrição do que a etapa deve fazer")
    required_tools: List[str] = Field(
        default_factory=list,
        description="Lista de tools necessárias para esta etapa",
    )
    outputs: List[str] = Field(
        default_factory=list,
        description="Lista de outputs esperados desta etapa",
    )
    optional: bool = Field(
        default=False,
        description="Se a etapa é opcional",
    )


class FAQItem(BaseModel):
    """Model for FAQ item."""

    question: str = Field(..., description="Pergunta")
    answer: str = Field(..., description="Resposta")
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Palavras-chave para busca",
    )
    category: Optional[str] = Field(
        default=None,
        description="Categoria da FAQ",
    )


class MCPTool(BaseModel):
    """Model for MCP tool configuration."""

    name: str = Field(..., description="Nome da tool")
    mcp_url: str = Field(..., description="URL do servidor MCP")
    description: str = Field(..., description="Descrição da tool")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parâmetros padrão da tool",
    )


class AgentConfig(BaseModel):
    """Model for complete agent configuration."""

    agent_id: str = Field(..., description="Identificador único do agente")
    name: str = Field(..., description="Nome do agente")
    description: Optional[str] = Field(
        default=None,
        description="Descrição do agente",
    )
    system_prompt: str = Field(
        ...,
        description="Prompt de sistema personalizado (define persona, tom, limites)",
    )
    script: List[ScriptStep] = Field(
        ...,
        description="Array de etapas obrigatórias do script",
    )
    faq: List[FAQItem] = Field(
        default_factory=list,
        description="Base de perguntas e respostas",
    )
    tools: List[MCPTool] = Field(
        default_factory=list,
        description="Lista de tools MCP disponíveis",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadados adicionais do agente",
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "agent_id": "sales_agent",
                "name": "Agente de Vendas",
                "description": "Agente especializado em vendas",
                "system_prompt": "Você é um vendedor profissional...",
                "script": [
                    {
                        "step": 1,
                        "name": "identificar_necessidades",
                        "description": "Identificar necessidades do cliente",
                        "required_tools": [],
                        "outputs": ["necessidades"],
                    }
                ],
                "faq": [
                    {
                        "question": "Qual o preço?",
                        "answer": "O preço varia conforme o produto...",
                    }
                ],
                "tools": [
                    {
                        "name": "retorna_preco",
                        "mcp_url": "http://localhost:8002",
                        "description": "Retorna preço do produto",
                    }
                ],
            }
        }

