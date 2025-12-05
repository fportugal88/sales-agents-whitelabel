"""FastAPI server using Strands Agents."""

import os
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json

from src.api.models import (
    AuditLogResponse,
    AuditLogsResponse,
    ChatMessage,
    ChatResponse,
    ConversationHistory,
    HealthResponse,
)
from src.config.settings import get_settings
from src.orchestrator.swarm_orchestrator import SwarmOrchestrator
from src.utils.logger import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Global orchestrator instance
orchestrator: Optional[SwarmOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    global orchestrator

    # Startup
    logger.info("Inicializando Sales Agents API...")
    
    # Configure SSL/truststore BEFORE loading settings
    # This must be done before any HTTP clients are created
    try:
        if os.getenv("USE_TRUSTSTORE", "true").lower() not in ("false", "0", "no", "off"):
            try:
                import truststore
                truststore.inject_into_ssl()
                logger.info("Truststore injetado - usando certificados do sistema")
            except ImportError:
                logger.info(
                    "Truststore não instalado - usando certificados padrão do Python",
                    hint="Para ambientes corporativos, instale: pip install truststore"
                )
            except Exception as e:
                logger.warning(
                    "Erro ao injetar truststore, usando certificados padrão",
                    error=str(e)
                )
    except Exception as e:
        logger.warning("Erro ao configurar truststore", error=str(e))
    
    try:
        settings = get_settings()
    except ValueError as e:
        logger.error(
            "Erro de configuração ao inicializar servidor",
            error=str(e),
            hint="Verifique o arquivo .env e as variáveis de ambiente"
        )
        raise RuntimeError(
            f"Falha ao carregar configurações: {str(e)}\n"
            "O servidor não pode iniciar sem configurações válidas."
        ) from e
    except Exception as e:
        logger.error(
            "Erro inesperado ao carregar configurações",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise RuntimeError(
            f"Erro inesperado ao carregar configurações: {str(e)}"
        ) from e

    # Initialize Swarm Orchestrator
    try:
        orchestrator = SwarmOrchestrator(settings=settings)
        logger.info("Swarm Orchestrator inicializado com sucesso")
    except Exception as e:
        logger.error(
            "Erro ao inicializar Swarm Orchestrator",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise RuntimeError(
            f"Falha ao inicializar Swarm Orchestrator: {str(e)}"
        ) from e

    yield

    # Shutdown
    logger.info("Encerrando Sales Agents API...")


# Create FastAPI app
app = FastAPI(
    title="Sales Agents API",
    description="API para o ecossistema de agentes de vendas usando Strands Agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Sales Agents API",
        "version": "1.0.0",
        "framework": "Strands Agents",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orquestrador não inicializado")
    
    conversations_count = len(orchestrator.conversations)
    agents_count = 6  # researcher, sales_agent, qualification, presentation, negotiation, closing
    
    return HealthResponse(
        status="healthy",
        agents_count=agents_count,
        active_conversations=conversations_count,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(message: ChatMessage):
    """Processa uma mensagem do chat e retorna resposta do agente.

    Args:
        message: Mensagem do usuário e contexto opcional

    Returns:
        Resposta do agente com metadados
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orquestrador não inicializado")

    try:
        logger.info(
            "Processando mensagem",
            conversation_id=message.conversation_id,
            message_length=len(message.message),
        )

        result = await orchestrator.process_message(
            message=message.message,
            conversation_id=message.conversation_id,
            context=message.context,
        )

        logger.info(
            "Mensagem processada",
            conversation_id=result.get("conversation_id"),
            agent_id=result.get("agent_id"),
            stage=result.get("stage"),
        )

        if "error" in result:
            logger.error("Erro no resultado", error=result["error"])
            raise HTTPException(status_code=500, detail=result["error"])

        return ChatResponse(
            conversation_id=result["conversation_id"],
            response=result["response"],
            agent_id=result["agent_id"],
            stage=result["stage"],
            next_agent=result.get("next_agent"),
            metadata=result.get("metadata", {}),
        )
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "Erro ao processar mensagem",
            error=str(e),
            error_type=error_type,
            conversation_id=message.conversation_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar mensagem. Por favor, tente novamente."
        )


@app.get("/conversation/{conversation_id}", response_model=ConversationHistory, tags=["Conversation"])
async def get_conversation(conversation_id: str):
    """Obtém o histórico de uma conversa.

    Args:
        conversation_id: ID da conversa

    Returns:
        Histórico da conversa
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orquestrador não inicializado")

    try:
        conversation = orchestrator.get_conversation(conversation_id)
        if not conversation:
            logger.warning(
                "Conversa não encontrada",
                conversation_id=conversation_id,
            )
            raise HTTPException(
                status_code=404,
                detail=f"Conversa não encontrada: {conversation_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erro ao buscar conversa",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar conversa: {str(e)}"
        )

    return ConversationHistory(
        conversation_id=conversation.id,
        messages=[
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "agent_id": msg.agent_id,
            }
            for msg in conversation.messages
        ],
        current_stage=conversation.current_stage.value,
        lead_id=conversation.lead_id,
    )


@app.post("/conversation", tags=["Conversation"])
async def create_conversation():
    """Cria uma nova conversa.

    Returns:
        ID da nova conversa
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orquestrador não inicializado")

    try:
        conversation = await orchestrator.create_conversation()
        logger.info(
            "Conversa criada com sucesso",
            conversation_id=conversation.id
        )
        return {"conversation_id": conversation.id}
    except Exception as e:
        logger.error(
            "Erro ao criar conversa",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao criar conversa. Por favor, tente novamente."
        )


@app.get("/metrics", tags=["Metrics"])
async def get_metrics():
    """Obtém métricas de conversão do sistema.
    
    Returns:
        Métricas de conversão e performance
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orquestrador não inicializado")
    
    try:
        metrics = orchestrator.get_conversion_metrics()
        return metrics
    except Exception as e:
        logger.error(
            "Erro ao obter métricas",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        return {
            "error": "Erro ao obter métricas",
            "message": "Não foi possível carregar métricas no momento",
            "total_conversations": len(orchestrator.conversations) if orchestrator else 0
        }


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(message: ChatMessage):
    """Processa uma mensagem do chat e retorna eventos de streaming do Swarm.

    Args:
        message: Mensagem do usuário e contexto opcional

    Returns:
        Streaming de eventos do Swarm
    """
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orquestrador não inicializado")

    async def generate():
        try:
            async for event in orchestrator.stream_message(
                message=message.message,
                conversation_id=message.conversation_id,
                context=message.context,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            logger.error(
                "Erro ao fazer streaming",
                error=error_msg,
                error_type=error_type,
                conversation_id=message.conversation_id,
                exc_info=True
            )
            
            error_event = {
                "type": "error",
                "error": "Erro ao processar mensagem",
                "error_type": error_type,
            }
            yield f"data: {json.dumps(error_event)}\n\n"
            
            end_event = {
                "type": "end",
                "status": "error"
            }
            yield f"data: {json.dumps(end_event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
