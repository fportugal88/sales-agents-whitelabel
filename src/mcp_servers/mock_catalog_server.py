"""Mock Catalog MCP server for product information."""

from typing import Any, Dict, List, Optional

from src.mcp_servers.base_mcp import BaseMCPServer


class MockCatalogServer(BaseMCPServer):
    """Mock catalog server with product data."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 100.0,
    ) -> None:
        """Initialize mock catalog server.

        Args:
            base_url: Base URL (not used for mock, kept for compatibility)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds
        """
        super().__init__(
            server_name="mock_catalog",
            base_url=base_url,
            simulate_latency=simulate_latency,
            latency_ms=latency_ms,
        )
        self._products = self._initialize_mock_products()

    def _initialize_mock_products(self) -> List[Dict[str, Any]]:
        """Initialize with Maquinona product data from iFood Pago.

        Returns:
            List of product dictionaries
        """
        return [
            {
                "id": "maquinona_001",
                "name": "Maquinona iFood Pago",
                "description": "Muito mais que pagamentos: é a parceria que faz seu negócio crescer! Máquina de pagamento moderna com inteligência de marketing integrada para restaurantes.",
                "category": "Pagamentos e Marketing",
                "price": 0.0,  # Taxas especiais conforme negócio
                "currency": "BRL",
                "features": [
                    "Máquina de pagamento moderna e intuitiva",
                    "Campanhas de fidelidade e cashback",
                    "Inteligência de marketing do iFood",
                    "Dados e insights sobre vendas",
                    "Taxas competitivas e especiais",
                    "Aceita todas as principais bandeiras",
                    "Aceita vale-refeição",
                    "Notificações automáticas via WhatsApp",
                    "Relatórios semanais com insights",
                    "Identificação e segmentação de clientes em tempo real",
                ],
                "target_audience": "restaurantes",
                "trial_days": 0,  # Não há trial, mas taxas especiais
                "benefits": [
                    "Aumente suas vendas com inteligência de marketing",
                    "Fidelize clientes atuais",
                    "Leve novos clientes para o salão",
                    "Aumente seu faturamento",
                    "Receba dados e dicas sobre suas vendas",
                    "Economia no bolso para fidelizar clientes",
                    "Mais dinheiro no seu fluxo de caixa",
                ],
                "how_it_works": [
                    "Cliente faz visita ao restaurante pela primeira vez",
                    "Atendente apresenta programa de fidelidade ou cashback",
                    "Cliente é cadastrado na maquinona com número de celular",
                    "Cliente faz pagamento na maquinona",
                    "Instantaneamente recebe cupom ou cashback via WhatsApp",
                    "Cliente é estimulado a voltar mais vezes",
                ],
                "payment_methods": [
                    "Cartão de Crédito",
                    "Cartão de Débito",
                    "Vale Refeição",
                    "Outros",
                ],
                "support": [
                    "Identificação e segmentação de clientes em tempo real",
                    "Controle de resgate de cupons e pedidos mínimos",
                    "Envio automático de ofertas pelo WhatsApp",
                    "Envio de relatórios semanais com insights valiosos",
                ],
            },
        ]

    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a catalog tool.

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

        if tool_name == "get_products":
            return await self._get_products(**params)
        elif tool_name == "get_product_details":
            return await self._get_product_details(**params)
        elif tool_name == "search_products":
            return await self._search_products(**params)
        elif tool_name == "retorna_preco":
            return await self._retorna_preco(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_products(
        self,
        category: Optional[str] = None,
        target_audience: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get list of products.

        Args:
            category: Optional category filter
            target_audience: Optional target audience filter
            limit: Maximum number of products to return

        Returns:
            Products list dictionary
        """
        products = self._products.copy()

        if category:
            products = [p for p in products if p.get("category") == category]

        if target_audience:
            products = [p for p in products if p.get("target_audience") == target_audience]

        products = products[:limit]

        return {
            "success": True,
            "count": len(products),
            "products": products,
        }

    async def _get_product_details(
        self,
        product_id: str,
    ) -> Dict[str, Any]:
        """Get detailed information about a specific product.

        Args:
            product_id: Product ID

        Returns:
            Product details dictionary
        """
        product = next((p for p in self._products if p["id"] == product_id), None)

        if not product:
            return {"error": "Product not found", "product_id": product_id}

        return {
            "success": True,
            "product": product,
        }

    async def _search_products(
        self,
        query: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Search products by name or description.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Search results dictionary
        """
        query_lower = query.lower()
        results = []

        for product in self._products:
            name_match = query_lower in product["name"].lower()
            desc_match = query_lower in product["description"].lower()
            category_match = query_lower in product.get("category", "").lower()

            if name_match or desc_match or category_match:
                results.append(product)

        results = results[:limit]

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "products": results,
        }

    def list_tools(self) -> list[Dict[str, Any]]:
        """List available catalog tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "get_products",
                "description": "Get list of products with optional filters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Product category filter"},
                        "target_audience": {
                            "type": "string",
                            "description": "Target audience filter",
                        },
                        "limit": {"type": "integer", "description": "Maximum products to return"},
                    },
                },
            },
            {
                "name": "get_product_details",
                "description": "Get detailed information about a specific product",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "description": "Product ID"},
                    },
                    "required": ["product_id"],
                },
            },
            {
                "name": "search_products",
                "description": "Search products by name, description, or category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Maximum results to return"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "retorna_preco",
                "description": "Retorna o preço de um produto específico",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "description": "ID do produto"},
                        "product_name": {"type": "string", "description": "Nome do produto"},
                    },
                },
            },
        ]

