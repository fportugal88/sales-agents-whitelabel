"""Mock iFood MCP server for client information and product data."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.mcp_servers.base_mcp import BaseMCPServer


class MockiFoodServer(BaseMCPServer):
    """Mock iFood server for client and product information."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 100.0,
    ) -> None:
        """Initialize mock iFood server.

        Args:
            base_url: Base URL (not used for mock, kept for compatibility)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds
        """
        super().__init__(
            server_name="mock_ifood",
            base_url=base_url,
            simulate_latency=simulate_latency,
            latency_ms=latency_ms,
        )
        self._clients: Dict[str, Dict[str, Any]] = {}
        self._products: Dict[str, Dict[str, Any]] = {}
        self._initialize_mock_data()

    def _initialize_mock_data(self) -> None:
        """Initialize with sample mock data."""
        # Sample clients
        self._clients = {
            "12345678000190": {
                "cnpj": "12345678000190",
                "email": "contato@restauranteexemplo.com.br",
                "nome_empresa": "Restaurante Exemplo",
                "status_conta": "ativa",
                "data_cadastro": (datetime.utcnow() - timedelta(days=180)).isoformat(),
                "produtos_contratados": [
                    {
                        "id": "ifood_delivery",
                        "nome": "iFood Delivery",
                        "status": "ativo",
                        "data_contratacao": (datetime.utcnow() - timedelta(days=150)).isoformat(),
                    },
                    {
                        "id": "ifood_pago",
                        "nome": "iFood Pago",
                        "status": "ativo",
                        "data_contratacao": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    },
                ],
                "historico_uso": {
                    "pedidos_mes": 450,
                    "faturamento_mes": 125000.0,
                    "taxa_retorno": 0.35,
                },
                "perfil": "restaurante_medio",
            },
            "98765432000110": {
                "cnpj": "98765432000110",
                "email": "contato@bistroelegante.com.br",
                "nome_empresa": "Bistrô Elegante",
                "status_conta": "ativa",
                "data_cadastro": (datetime.utcnow() - timedelta(days=365)).isoformat(),
                "produtos_contratados": [
                    {
                        "id": "ifood_delivery",
                        "nome": "iFood Delivery",
                        "status": "ativo",
                        "data_contratacao": (datetime.utcnow() - timedelta(days=300)).isoformat(),
                    },
                ],
                "historico_uso": {
                    "pedidos_mes": 1200,
                    "faturamento_mes": 350000.0,
                    "taxa_retorno": 0.42,
                },
                "perfil": "restaurante_grande",
            },
        }

        # Sample products
        self._products = {
            "ifood_delivery": {
                "id": "ifood_delivery",
                "nome": "iFood Delivery",
                "categoria": "delivery",
                "status": "disponivel",
            },
            "ifood_pago": {
                "id": "ifood_pago",
                "nome": "iFood Pago",
                "categoria": "pagamentos",
                "status": "disponivel",
            },
            "maquinona": {
                "id": "maquinona",
                "nome": "Maquinona iFood Pago",
                "categoria": "pagamentos_marketing",
                "status": "disponivel",
            },
        }

    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call an iFood tool.

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

        if tool_name == "buscar_cliente_ifood":
            return await self._buscar_cliente_ifood(**params)
        elif tool_name == "verificar_produtos_contratados":
            return await self._verificar_produtos_contratados(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _buscar_cliente_ifood(
        self,
        cnpj: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Buscar informações do cliente iFood.

        Args:
            cnpj: CNPJ do cliente
            email: Email do cliente

        Returns:
            Informações do cliente
        """
        if not cnpj and not email:
            return {
                "success": False,
                "error": "É necessário fornecer CNPJ ou email",
            }

        # Search by CNPJ
        if cnpj:
            client = self._clients.get(cnpj)
            if client:
                return {
                    "success": True,
                    "cliente": client,
                }

        # Search by email
        if email:
            for client in self._clients.values():
                if client.get("email") == email:
                    return {
                        "success": True,
                        "cliente": client,
                    }

        # If not found, return mock data for new client
        return {
            "success": True,
            "cliente": {
                "cnpj": cnpj or "00000000000000",
                "email": email or "novo@cliente.com.br",
                "nome_empresa": "Novo Cliente",
                "status_conta": "nova",
                "produtos_contratados": [],
                "historico_uso": {},
                "perfil": "novo",
            },
            "is_new": True,
        }

    async def _verificar_produtos_contratados(
        self,
        cnpj: str,
    ) -> Dict[str, Any]:
        """Verificar produtos contratados pelo cliente.

        Args:
            cnpj: CNPJ do cliente

        Returns:
            Lista de produtos contratados
        """
        client = self._clients.get(cnpj)
        if not client:
            return {
                "success": False,
                "error": "Cliente não encontrado",
            }

        produtos = client.get("produtos_contratados", [])
        return {
            "success": True,
            "cnpj": cnpj,
            "produtos": produtos,
            "total_produtos": len(produtos),
            "produtos_ativos": [p for p in produtos if p.get("status") == "ativo"],
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "buscar_cliente_ifood",
                "description": "Busca informações completas do cliente iFood (produtos contratados, status da conta, histórico de uso, perfil)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cnpj": {
                            "type": "string",
                            "description": "CNPJ do cliente (opcional se email fornecido)",
                        },
                        "email": {
                            "type": "string",
                            "description": "Email do cliente (opcional se CNPJ fornecido)",
                        },
                    },
                },
            },
            {
                "name": "verificar_produtos_contratados",
                "description": "Verifica quais produtos iFood o cliente já tem contratados",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cnpj": {
                            "type": "string",
                            "description": "CNPJ do cliente",
                        },
                    },
                    "required": ["cnpj"],
                },
            },
        ]




