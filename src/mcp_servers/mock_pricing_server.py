"""Mock Pricing MCP server for personalized pricing calculations."""

from typing import Any, Dict, List, Optional

from src.mcp_servers.base_mcp import BaseMCPServer


class MockPricingServer(BaseMCPServer):
    """Mock pricing server for personalized pricing and special rates."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 100.0,
    ) -> None:
        """Initialize mock pricing server.

        Args:
            base_url: Base URL (not used for mock, kept for compatibility)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds
        """
        super().__init__(
            server_name="mock_pricing",
            base_url=base_url,
            simulate_latency=simulate_latency,
            latency_ms=latency_ms,
        )

    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a pricing tool.

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

        if tool_name == "calcular_preco_personalizado":
            return await self._calcular_preco_personalizado(**params)
        elif tool_name == "obter_taxas_especiais":
            return await self._obter_taxas_especiais(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _calcular_preco_personalizado(
        self,
        produto_id: str,
        perfil_restaurante: Optional[Dict[str, Any]] = None,
        configuracoes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calcular preço personalizado para o produto.

        Args:
            produto_id: ID do produto
            perfil_restaurante: Perfil do restaurante
            configuracoes: Configurações adicionais

        Returns:
            Cálculo de preço personalizado
        """
        perfil = perfil_restaurante or {}
        config = configuracoes or {}

        # Base pricing for Maquinona
        if produto_id == "maquinona" or produto_id == "maquinona_001":
            # Base price (taxa base)
            preco_base = 0.0  # Maquinona não tem taxa fixa, apenas taxas por transação

            # Calculate discounts based on profile
            descontos = []
            desconto_percentual = 0.0

            tamanho = perfil.get("tamanho", "medio")
            faturamento = perfil.get("faturamento_mensal", 0)

            # Discounts based on size and revenue
            if tamanho == "grande" or faturamento > 200000:
                desconto_percentual = 0.15
                descontos.append({
                    "tipo": "volume",
                    "descricao": "Desconto por volume (grande restaurante)",
                    "percentual": 15,
                })
            elif tamanho == "medio" or faturamento > 100000:
                desconto_percentual = 0.10
                descontos.append({
                    "tipo": "volume",
                    "descricao": "Desconto por volume (médio restaurante)",
                    "percentual": 10,
                })

            # Special rates (taxas por transação)
            taxa_base_credito = 2.99  # %
            taxa_base_debito = 1.99  # %

            # Apply discounts to rates
            taxa_credito = taxa_base_credito * (1 - desconto_percentual)
            taxa_debito = taxa_base_debito * (1 - desconto_percentual)

            # Payment conditions
            condicoes_pagamento = [
                "Taxas especiais conforme perfil",
                "Sem taxa de adesão",
                "Sem mensalidade fixa",
                "Taxas competitivas no mercado",
            ]

            return {
                "success": True,
                "produto_id": produto_id,
                "preco_base": preco_base,
                "descontos_aplicaveis": descontos,
                "taxas": {
                    "credito": {
                        "percentual": round(taxa_credito, 2),
                        "descricao": "Taxa para cartão de crédito",
                    },
                    "debito": {
                        "percentual": round(taxa_debito, 2),
                        "descricao": "Taxa para cartão de débito",
                    },
                },
                "preco_final": preco_base,  # Sem taxa fixa
                "condicoes_pagamento": condicoes_pagamento,
                "observacoes": "Preço personalizado baseado no perfil do restaurante. Taxas variam conforme volume de transações.",
            }

        return {
            "success": False,
            "error": f"Produto {produto_id} não encontrado",
        }

    async def _obter_taxas_especiais(
        self,
        cnpj: str,
        produto_id: str,
    ) -> Dict[str, Any]:
        """Obter taxas especiais para o cliente.

        Args:
            cnpj: CNPJ do cliente
            produto_id: ID do produto

        Returns:
            Taxas especiais e condições
        """
        # Mock special rates based on CNPJ
        # In real implementation, this would query customer database

        if produto_id == "maquinona" or produto_id == "maquinona_001":
            # Check if customer is eligible for special rates
            # For now, return standard special rates
            taxas_especiais = {
                "taxa_credito": 2.49,  # %
                "taxa_debito": 1.79,  # %
                "taxa_vale_refeicao": 1.99,  # %
            }

            condicoes_especiais = [
                "Taxas reduzidas para clientes iFood",
                "Sem taxa de adesão",
                "Sem mensalidade",
                "Suporte prioritário incluído",
            ]

            promocoes_disponiveis = []
            # Check if customer qualifies for promotions
            # For mock, return a promotion
            promocoes_disponiveis.append({
                "id": "promo_maquinona_2024",
                "nome": "Promoção Maquinona 2024",
                "descricao": "Taxas reduzidas nos primeiros 3 meses",
                "validade": "2024-12-31",
            })

            return {
                "success": True,
                "cnpj": cnpj,
                "produto_id": produto_id,
                "taxas_especiais": taxas_especiais,
                "condicoes_especiais": condicoes_especiais,
                "promocoes_disponiveis": promocoes_disponiveis,
                "observacoes": "Taxas personalizadas conforme perfil e histórico do cliente",
            }

        return {
            "success": False,
            "error": f"Produto {produto_id} não encontrado",
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "calcular_preco_personalizado",
                "description": "Calcula preço personalizado para o produto baseado no perfil do restaurante e configurações. Retorna preço base, descontos aplicáveis, preço final e condições de pagamento",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "produto_id": {
                            "type": "string",
                            "description": "ID do produto",
                        },
                        "perfil_restaurante": {
                            "type": "object",
                            "description": "Perfil do restaurante (tamanho, faturamento, etc.)",
                        },
                        "configuracoes": {
                            "type": "object",
                            "description": "Configurações adicionais do produto",
                        },
                    },
                    "required": ["produto_id"],
                },
            },
            {
                "name": "obter_taxas_especiais",
                "description": "Obtém taxas especiais e condições personalizadas para o cliente. Retorna taxas personalizadas, condições especiais e promoções disponíveis",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cnpj": {
                            "type": "string",
                            "description": "CNPJ do cliente",
                        },
                        "produto_id": {
                            "type": "string",
                            "description": "ID do produto",
                        },
                    },
                    "required": ["cnpj", "produto_id"],
                },
            },
        ]




