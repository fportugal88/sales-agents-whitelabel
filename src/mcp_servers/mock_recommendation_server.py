"""Mock Recommendation MCP server for product recommendations."""

from typing import Any, Dict, List, Optional

from src.mcp_servers.base_mcp import BaseMCPServer


class MockRecommendationServer(BaseMCPServer):
    """Mock recommendation server for product recommendations and fit analysis."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 100.0,
    ) -> None:
        """Initialize mock recommendation server.

        Args:
            base_url: Base URL (not used for mock, kept for compatibility)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds
        """
        super().__init__(
            server_name="mock_recommendation",
            base_url=base_url,
            simulate_latency=simulate_latency,
            latency_ms=latency_ms,
        )
        self._products = {
            "maquinona": {
                "id": "maquinona",
                "nome": "Maquinona iFood Pago",
                "categoria": "pagamentos_marketing",
                "beneficios": [
                    "Aumento de vendas com marketing",
                    "Fidelização de clientes",
                    "Dados e insights",
                    "Taxas competitivas",
                ],
            },
        }

    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a recommendation tool.

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

        if tool_name == "recomendar_produtos":
            return await self._recomendar_produtos(**params)
        elif tool_name == "avaliar_fit_produto":
            return await self._avaliar_fit_produto(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _recomendar_produtos(
        self,
        perfil_restaurante: Optional[Dict[str, Any]] = None,
        necessidades: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Recomendar produtos baseado no perfil e necessidades.

        Args:
            perfil_restaurante: Perfil do restaurante
            necessidades: Lista de necessidades identificadas

        Returns:
            Produtos recomendados com scores e justificativas
        """
        necessidades = necessidades or []
        perfil = perfil_restaurante or {}

        # Default recommendation: Maquinona
        produtos_recomendados = []

        # Calculate fit score based on needs
        fit_score = 0.6  # Base score

        if "aumentar_faturamento" in necessidades:
            fit_score += 0.15
        if "fidelizar_clientes" in necessidades:
            fit_score += 0.15
        if "dados_insights" in necessidades:
            fit_score += 0.1

        tamanho = perfil.get("tamanho", "medio")
        if tamanho in ["medio", "grande"]:
            fit_score += 0.1

        fit_score = min(fit_score, 1.0)

        # Build recommendation
        produto = self._products["maquinona"]
        beneficios_relevantes = []
        if "aumentar_faturamento" in necessidades:
            beneficios_relevantes.append("Aumento de vendas com inteligência de marketing")
        if "fidelizar_clientes" in necessidades:
            beneficios_relevantes.append("Programas de fidelidade e cashback")
        if "dados_insights" in necessidades:
            beneficios_relevantes.append("Dados e insights sobre vendas")

        produtos_recomendados.append({
            "produto_id": produto["id"],
            "nome": produto["nome"],
            "fit_score": fit_score,
            "beneficios_especificos": beneficios_relevantes or produto["beneficios"],
            "justificativa": f"Produto ideal para restaurantes {tamanho} que precisam de {', '.join(necessidades[:2]) if necessidades else 'soluções de pagamento e marketing'}",
        })

        return {
            "success": True,
            "produtos": produtos_recomendados,
            "total_recomendacoes": len(produtos_recomendados),
            "melhor_fit": produtos_recomendados[0] if produtos_recomendados else None,
        }

    async def _avaliar_fit_produto(
        self,
        produto_id: str,
        perfil_restaurante: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Avaliar fit de um produto específico.

        Args:
            produto_id: ID do produto
            perfil_restaurante: Perfil do restaurante

        Returns:
            Avaliação de fit do produto
        """
        produto = self._products.get(produto_id)
        if not produto:
            return {
                "success": False,
                "error": f"Produto {produto_id} não encontrado",
            }

        perfil = perfil_restaurante or {}
        tamanho = perfil.get("tamanho", "medio")
        necessidades = perfil.get("necessidades_identificadas", [])

        # Calculate fit score
        fit_score = 0.7  # Base score for Maquinona

        if tamanho in ["medio", "grande"]:
            fit_score += 0.15
        if "fidelizar_clientes" in necessidades:
            fit_score += 0.1
        if "aumentar_faturamento" in necessidades:
            fit_score += 0.05

        fit_score = min(fit_score, 1.0)

        # Determine relevant benefits
        beneficios_relevantes = produto.get("beneficios", [])
        if tamanho == "pequeno":
            beneficios_relevantes = [
                b for b in beneficios_relevantes
                if "fidelização" in b.lower() or "dados" in b.lower()
            ]

        # Potential objections
        objecoes_potenciais = []
        if tamanho == "pequeno":
            objecoes_potenciais.append("Restaurante pequeno pode não ter volume suficiente")
        if not necessidades:
            objecoes_potenciais.append("Necessidades não claramente identificadas")

        return {
            "success": True,
            "produto_id": produto_id,
            "produto_nome": produto["nome"],
            "fit_score": fit_score,
            "beneficios_relevantes": beneficios_relevantes,
            "objecoes_potenciais": objecoes_potenciais,
            "recomendacao": "Recomendado" if fit_score >= 0.7 else "Avaliar caso a caso",
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "recomendar_produtos",
                "description": "Recomenda produtos baseado no perfil do restaurante e necessidades identificadas. Retorna produtos recomendados, score de fit, benefícios específicos e justificativa",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "perfil_restaurante": {
                            "type": "object",
                            "description": "Perfil do restaurante (tamanho, segmento, etc.)",
                        },
                        "necessidades": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lista de necessidades identificadas",
                        },
                    },
                },
            },
            {
                "name": "avaliar_fit_produto",
                "description": "Avalia o fit de um produto específico para o restaurante. Retorna score de adequação, benefícios relevantes e objeções potenciais",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "produto_id": {
                            "type": "string",
                            "description": "ID do produto a avaliar",
                        },
                        "perfil_restaurante": {
                            "type": "object",
                            "description": "Perfil do restaurante",
                        },
                    },
                    "required": ["produto_id"],
                },
            },
        ]




