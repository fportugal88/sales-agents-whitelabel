"""Mock Restaurant MCP server for restaurant information."""

from typing import Any, Dict, List, Optional

from src.mcp_servers.base_mcp import BaseMCPServer


class MockRestaurantServer(BaseMCPServer):
    """Mock restaurant server for restaurant information and analysis."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 100.0,
    ) -> None:
        """Initialize mock restaurant server.

        Args:
            base_url: Base URL (not used for mock, kept for compatibility)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds
        """
        super().__init__(
            server_name="mock_restaurant",
            base_url=base_url,
            simulate_latency=simulate_latency,
            latency_ms=latency_ms,
        )
        self._restaurants: Dict[str, Dict[str, Any]] = {}
        self._initialize_mock_data()

    def _initialize_mock_data(self) -> None:
        """Initialize with sample mock data."""
        self._restaurants = {
            "12345678000190": {
                "cnpj": "12345678000190",
                "nome": "Restaurante Exemplo",
                "numero_mesas": 25,
                "faturamento_mensal": 125000.0,
                "localizacao": {
                    "cidade": "São Paulo",
                    "estado": "SP",
                    "bairro": "Vila Madalena",
                },
                "tipo_restaurante": "casual",
                "publico_alvo": "familias_jovens",
                "segmento": "brasileira",
                "tamanho": "medio",
            },
            "98765432000110": {
                "cnpj": "98765432000110",
                "nome": "Bistrô Elegante",
                "numero_mesas": 50,
                "faturamento_mensal": 350000.0,
                "localizacao": {
                    "cidade": "Rio de Janeiro",
                    "estado": "RJ",
                    "bairro": "Ipanema",
                },
                "tipo_restaurante": "fino",
                "publico_alvo": "executivos",
                "segmento": "francesa",
                "tamanho": "grande",
            },
        }

    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a restaurant tool.

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

        if tool_name == "obter_info_restaurante":
            return await self._obter_info_restaurante(**params)
        elif tool_name == "analisar_perfil_restaurante":
            return await self._analisar_perfil_restaurante(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _obter_info_restaurante(
        self,
        cnpj: Optional[str] = None,
        nome: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Obter informações do restaurante.

        Args:
            cnpj: CNPJ do restaurante
            nome: Nome do restaurante

        Returns:
            Informações do restaurante
        """
        if not cnpj and not nome:
            return {
                "success": False,
                "error": "É necessário fornecer CNPJ ou nome",
            }

        # Search by CNPJ
        if cnpj:
            restaurant = self._restaurants.get(cnpj)
            if restaurant:
                return {
                    "success": True,
                    "restaurante": restaurant,
                }

        # Search by name
        if nome:
            for restaurant in self._restaurants.values():
                if nome.lower() in restaurant.get("nome", "").lower():
                    return {
                        "success": True,
                        "restaurante": restaurant,
                    }

        # If not found, return None (new restaurant)
        return {
            "success": False,
            "error": "Restaurante não encontrado",
        }

    async def _analisar_perfil_restaurante(
        self,
        cnpj: str,
    ) -> Dict[str, Any]:
        """Analisar perfil do restaurante.

        Args:
            cnpj: CNPJ do restaurante

        Returns:
            Análise do perfil do restaurante
        """
        restaurant = self._restaurants.get(cnpj)
        if not restaurant:
            return {
                "success": False,
                "error": "Restaurante não encontrado",
            }

        # Analyze based on restaurant data
        numero_mesas = restaurant.get("numero_mesas", 0)
        faturamento = restaurant.get("faturamento_mensal", 0)

        # Determine size
        if numero_mesas <= 15:
            tamanho = "pequeno"
        elif numero_mesas <= 30:
            tamanho = "medio"
        else:
            tamanho = "grande"

        # Determine needs based on profile
        necessidades = []
        if faturamento < 100000:
            necessidades.append("aumentar_faturamento")
        if numero_mesas < 20:
            necessidades.append("crescer_operacao")
        necessidades.append("fidelizar_clientes")
        necessidades.append("dados_insights")

        # Calculate fit score (0-1)
        fit_score = 0.7  # Base score
        if tamanho == "medio" or tamanho == "grande":
            fit_score += 0.1
        if faturamento > 100000:
            fit_score += 0.1
        fit_score = min(fit_score, 1.0)

        return {
            "success": True,
            "cnpj": cnpj,
            "segmento": restaurant.get("segmento", "geral"),
            "tamanho": tamanho,
            "necessidades_identificadas": necessidades,
            "fit_score": fit_score,
            "recomendacoes": [
                "Maquinona ideal para restaurantes de médio/grande porte",
                "Benefícios de fidelização e dados são relevantes",
            ],
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "obter_info_restaurante",
                "description": "Obtém informações completas do restaurante (número de mesas, faturamento mensal, localização, tipo, público-alvo)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cnpj": {
                            "type": "string",
                            "description": "CNPJ do restaurante (opcional se nome fornecido)",
                        },
                        "nome": {
                            "type": "string",
                            "description": "Nome do restaurante (opcional se CNPJ fornecido)",
                        },
                    },
                },
            },
            {
                "name": "analisar_perfil_restaurante",
                "description": "Analisa o perfil do restaurante e identifica necessidades, calcula fit score e fornece recomendações",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cnpj": {
                            "type": "string",
                            "description": "CNPJ do restaurante",
                        },
                    },
                    "required": ["cnpj"],
                },
            },
        ]




