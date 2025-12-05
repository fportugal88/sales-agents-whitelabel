"""Base class for MCP servers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.utils.logger import LoggerMixin


class BaseMCPServer(ABC, LoggerMixin):
    """Abstract base class for MCP servers.

    All MCP servers must implement:
    - call(): Execute an MCP tool/function
    - list_tools(): Return available tools
    """

    def __init__(
        self,
        server_name: str,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 100.0,
    ) -> None:
        """Initialize the MCP server.

        Args:
            server_name: Name of the MCP server
            base_url: Base URL for the server (optional for mock servers)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds to simulate
        """
        self.server_name = server_name
        self.base_url = base_url
        self.simulate_latency = simulate_latency
        self.latency_ms = latency_ms
        self.logger.info("MCP server initialized", server_name=server_name)

    @abstractmethod
    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call an MCP tool/function.

        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters

        Returns:
            Tool response as dictionary

        Raises:
            ValueError: If tool_name is not found
            RuntimeError: If tool execution fails
        """
        pass

    @abstractmethod
    def list_tools(self) -> list[Dict[str, Any]]:
        """List all available tools.

        Returns:
            List of tool definitions with name, description, and parameters
        """
        pass

    async def _simulate_latency(self) -> None:
        """Simulate network latency for realistic behavior."""
        if self.simulate_latency:
            import asyncio

            await asyncio.sleep(self.latency_ms / 1000.0)

    def _validate_tool_exists(self, tool_name: str) -> None:
        """Validate that a tool exists.

        Args:
            tool_name: Tool name to validate

        Raises:
            ValueError: If tool does not exist
        """
        tools = [tool["name"] for tool in self.list_tools()]
        if tool_name not in tools:
            # Try to find similar tool names
            similar_tools = []
            tool_name_lower = tool_name.lower()
            for tool in tools:
                if tool_name_lower in tool.lower() or tool.lower() in tool_name_lower:
                    similar_tools.append(tool)
            
            error_msg = (
                f"Tool '{tool_name}' não encontrada em {self.server_name}."
            )
            if similar_tools:
                error_msg += f" Tools similares: {', '.join(similar_tools[:5])}"
            elif tools:
                error_msg += f" Tools disponíveis: {', '.join(tools[:10])}"
            else:
                error_msg += " Nenhuma tool disponível."
            
            raise ValueError(error_msg)
    
    def _validate_required_params(
        self,
        params: Dict[str, Any],
        required: list[str],
        tool_name: str,
    ) -> None:
        """Validate that required parameters are provided.

        Args:
            params: Parameters dictionary
            required: List of required parameter names
            tool_name: Name of the tool (for error messages)

        Raises:
            ValueError: If required parameters are missing
        """
        missing = [param for param in required if param not in params or params[param] is None]
        if missing:
            error_msg = (
                f"Parâmetros obrigatórios faltando para tool '{tool_name}': {', '.join(missing)}. "
                f"Parâmetros fornecidos: {', '.join(params.keys()) if params else 'nenhum'}. "
                f"Parâmetros esperados: {', '.join(required)}"
            )
            raise ValueError(error_msg)

