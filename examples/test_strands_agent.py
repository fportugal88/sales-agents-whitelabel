"""Test script for Strands Agent integration."""

import asyncio
from pathlib import Path

from src.agents.strands_agent import StrandsAgentWrapper
from src.config.settings import get_settings
from src.models.conversation import Conversation, ConversationStage, MessageRole
from src.utils.llm_client import LLMClient
from src.utils.logger import configure_logging


async def test_sales_agent():
    """Test sales agent with sample conversation."""
    configure_logging()
    settings = get_settings()
    llm_client = LLMClient(settings)

    # Load sales agent
    config_path = Path("config/agents/sales_agent.json")
    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return

    print("✅ Carregando agente de vendas...")
    agent = StrandsAgentWrapper.from_config_file(
        config_path=config_path,
        settings=settings,
        llm_client=llm_client,
    )
    print(f"✅ Agente carregado: {agent.config.agent_id}")

    # Create test conversation
    conversation = Conversation(
        id="test_conv_001",
        current_stage=ConversationStage.FAQ,
    )

    # Test messages
    test_messages = [
        "Olá, quero saber mais sobre seus produtos",
        "Preciso de uma solução de CRM",
        "Qual o preço?",
    ]

    for message in test_messages:
        print(f"\n{'='*60}")
        print(f"👤 Usuário: {message}")
        print(f"{'='*60}")

        try:
            result = await agent.process(message, conversation, {})
            print(f"🤖 Agente ({result.get('source', 'unknown')}): {result.get('response', '')}")
            print(f"   Metadata: {result.get('metadata', {})}")

            # Add message to conversation
            conversation.add_message(
                role=MessageRole.USER,
                content=message,
            )
            conversation.add_message(
                role=MessageRole.AGENT,
                content=result.get("response", ""),
                agent_id=agent.config.agent_id,
            )

        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_sales_agent())

