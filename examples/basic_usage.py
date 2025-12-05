"""Exemplo básico de uso do Sales Agents usando Strands Agents."""

import asyncio

from src.config.settings import get_settings
from src.orchestrator.swarm_orchestrator import SwarmOrchestrator
from src.utils.logger import configure_logging


async def main():
    """Exemplo de uso básico do sistema usando Strands Agents Swarm."""
    # Configurar logging
    configure_logging(log_level="INFO")

    # Carregar configurações do .env
    settings = get_settings()

    # Criar orquestrador usando Strands Agents Swarm
    orchestrator = SwarmOrchestrator(settings=settings)

    print("=" * 60)
    print("Sales Agents Ecosystem - Exemplo de Uso")
    print("Framework: Strands Agents")
    print("=" * 60)
    print()

    # Simular conversa de vendas
    messages = [
        "Quais produtos vocês têm?",
        "Meu email é cliente@example.com e trabalho na Acme Corp",
        "Temos um orçamento de R$ 10.000 e precisamos decidir este mês",
        "Me mostre como funciona a solução Maquinona",
        "O preço parece alto, vocês podem oferecer desconto?",
        "Sim, vamos prosseguir com a compra",
    ]

    conversation_id = None

    for i, message in enumerate(messages, 1):
        print(f"\n[{i}] Usuário: {message}")
        print("-" * 60)

        try:
            result = await orchestrator.process_message(
                message,
                conversation_id=conversation_id,
            )

            conversation_id = result.get("conversation_id")
            print(f"Agente: {result.get('agent_id', 'unknown')}")
            print(f"Estágio: {result.get('stage', 'unknown')}")
            print(f"Resposta: {result.get('response', 'No response')}")

            # Mostrar telemetria do Swarm
            metadata = result.get("metadata", {})
            telemetry = metadata.get("telemetry", {})
            if telemetry:
                agents_used = telemetry.get("agents_used", [])
                if agents_used:
                    print(f"Agentes usados: {', '.join(agents_used)}")
                handoffs = telemetry.get("total_handoffs", 0)
                if handoffs > 0:
                    print(f"Handoffs realizados: {handoffs}")

        except Exception as e:
            print(f"Erro: {str(e)}")

    print("\n" + "=" * 60)
    print("Conversa finalizada!")
    print("=" * 60)
    
    # Mostrar métricas
    print("\nMétricas de Conversão:")
    print("-" * 60)
    metrics = orchestrator.get_conversion_metrics()
    print(f"Total de conversas: {metrics.get('total_conversations', 0)}")
    print(f"Vendas fechadas: {metrics.get('closed_sales', 0)}")
    print(f"Taxa de conversão: {metrics.get('sales_conversion_rate', 0):.2f}%")


if __name__ == "__main__":
    asyncio.run(main())
