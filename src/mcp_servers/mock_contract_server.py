"""Mock Contract MCP server for contract history."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.mcp_servers.base_mcp import BaseMCPServer


class MockContractServer(BaseMCPServer):
    """Mock contract server for contract history and renewals."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 100.0,
    ) -> None:
        """Initialize mock contract server.

        Args:
            base_url: Base URL (not used for mock, kept for compatibility)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds
        """
        super().__init__(
            server_name="mock_contract",
            base_url=base_url,
            simulate_latency=simulate_latency,
            latency_ms=latency_ms,
        )
        self._contracts: Dict[str, List[Dict[str, Any]]] = {}
        self._initialize_mock_data()

    def _initialize_mock_data(self) -> None:
        """Initialize with sample mock data."""
        self._contracts = {
            "12345678000190": [
                {
                    "id": "contrato_001",
                    "cnpj": "12345678000190",
                    "produto_id": "ifood_delivery",
                    "produto_nome": "iFood Delivery",
                    "status": "ativo",
                    "data_inicio": (datetime.utcnow() - timedelta(days=150)).isoformat(),
                    "data_fim": (datetime.utcnow() + timedelta(days=215)).isoformat(),
                    "valor_mensal": 500.0,
                },
                {
                    "id": "contrato_002",
                    "cnpj": "12345678000190",
                    "produto_id": "ifood_pago",
                    "produto_nome": "iFood Pago",
                    "status": "ativo",
                    "data_inicio": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    "data_fim": (datetime.utcnow() + timedelta(days=335)).isoformat(),
                    "valor_mensal": 200.0,
                },
            ],
            "98765432000110": [
                {
                    "id": "contrato_003",
                    "cnpj": "98765432000110",
                    "produto_id": "ifood_delivery",
                    "produto_nome": "iFood Delivery",
                    "status": "ativo",
                    "data_inicio": (datetime.utcnow() - timedelta(days=300)).isoformat(),
                    "data_fim": (datetime.utcnow() + timedelta(days=65)).isoformat(),
                    "valor_mensal": 1200.0,
                },
            ],
        }

    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a contract tool.

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

        if tool_name == "buscar_historico_contratos":
            return await self._buscar_historico_contratos(**params)
        elif tool_name == "verificar_renovacoes_pendentes":
            return await self._verificar_renovacoes_pendentes(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _buscar_historico_contratos(
        self,
        cnpj: str,
    ) -> Dict[str, Any]:
        """Buscar histórico de contratos do cliente.

        Args:
            cnpj: CNPJ do cliente

        Returns:
            Histórico de contratos
        """
        contratos = self._contracts.get(cnpj, [])

        return {
            "success": True,
            "cnpj": cnpj,
            "contratos": contratos,
            "total_contratos": len(contratos),
            "contratos_ativos": [c for c in contratos if c.get("status") == "ativo"],
            "produtos_contratados": list(set([c.get("produto_id") for c in contratos])),
        }

    async def _verificar_renovacoes_pendentes(
        self,
        cnpj: str,
    ) -> Dict[str, Any]:
        """Verificar contratos próximos de vencer e oportunidades de upsell.

        Args:
            cnpj: CNPJ do cliente

        Returns:
            Contratos próximos de vencer e oportunidades
        """
        contratos = self._contracts.get(cnpj, [])
        hoje = datetime.utcnow()

        renovacoes_pendentes = []
        oportunidades_upsell = []

        for contrato in contratos:
            if contrato.get("status") != "ativo":
                continue

            data_fim_str = contrato.get("data_fim")
            if data_fim_str:
                try:
                    data_fim = datetime.fromisoformat(data_fim_str.replace("Z", "+00:00"))
                    dias_restantes = (data_fim - hoje).days

                    if 0 <= dias_restantes <= 90:
                        renovacoes_pendentes.append({
                            **contrato,
                            "dias_restantes": dias_restantes,
                        })
                except Exception:
                    pass

        # Check for upsell opportunities
        produtos_contratados = [c.get("produto_id") for c in contratos if c.get("status") == "ativo"]
        if "maquinona" not in produtos_contratados:
            oportunidades_upsell.append({
                "produto_id": "maquinona",
                "produto_nome": "Maquinona iFood Pago",
                "motivo": "Cliente já tem iFood Delivery, pode se beneficiar da Maquinona",
            })

        return {
            "success": True,
            "cnpj": cnpj,
            "renovacoes_pendentes": renovacoes_pendentes,
            "total_renovacoes": len(renovacoes_pendentes),
            "oportunidades_upsell": oportunidades_upsell,
            "total_oportunidades": len(oportunidades_upsell),
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "buscar_historico_contratos",
                "description": "Busca histórico completo de contratos do cliente, incluindo produtos já contratados, status e datas",
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
            {
                "name": "verificar_renovacoes_pendentes",
                "description": "Verifica contratos próximos de vencer (próximos 90 dias) e identifica oportunidades de upsell",
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




