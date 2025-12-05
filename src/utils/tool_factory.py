"""Factory for creating Strands-compatible tools from MCP tools."""

from typing import Any, Dict, List, Optional

from strands.tools import PythonAgentTool
from strands.types.tools import ToolSpec

from src.agents.mcp_tools import MCPTools
from src.models.agent_config import MCPTool
from src.utils.logger import LoggerMixin


class ToolFactory(LoggerMixin):
    """Factory for creating Strands-compatible tools from MCP tools.
    
    Centralizes the conversion logic from MCP tools to Strands PythonAgentTool,
    reducing code duplication and ensuring consistency.
    """

    @staticmethod
    def create_strands_tool_from_mcp(
        tool_name: str,
        mcp_tools: MCPTools,
        tool_config: MCPTool,
    ) -> PythonAgentTool:
        """Create a Strands-compatible tool from MCP tool configuration.
        
        Args:
            tool_name: Name of MCP tool
            mcp_tools: MCPTools instance for calling tools
            tool_config: MCPTool configuration object
            
        Returns:
            Strands-compatible PythonAgentTool
            
        Raises:
            ValueError: If tool configuration is invalid
        """
        # Create async tool function wrapper
        async def tool_function(**kwargs: Any) -> Dict[str, Any]:
            """Tool function wrapper for Strands Agent."""
            result = await mcp_tools.call_tool(tool_name, kwargs)
            return result
        
        # Extract and validate tool specification
        description = tool_config.description or f"Tool {tool_name}"
        parameters = tool_config.parameters or {}
        
        # Convert MCP parameters format to JSON Schema format
        # MCP uses "properties" and "required" at the root, which is already JSON Schema compatible
        input_schema = parameters if parameters else {
            "type": "object",
            "properties": {},
        }
        
        # Ensure input_schema has type if not present
        if "type" not in input_schema:
            input_schema["type"] = "object"
        
        # Create ToolSpec with correct structure
        tool_spec: ToolSpec = {
            "name": tool_name,
            "description": description,
            "inputSchema": input_schema,
        }
        
        # Create PythonAgentTool with correct parameters
        return PythonAgentTool(
            tool_name=tool_name,
            tool_spec=tool_spec,
            tool_func=tool_function,
        )

    @staticmethod
    def create_tools_from_mcp_tools(
        mcp_tools: MCPTools,
        tool_names: Optional[List[str]] = None,
    ) -> List[PythonAgentTool]:
        """Create multiple Strands tools from MCP tools.
        
        Args:
            mcp_tools: MCPTools instance
            tool_names: Optional list of tool names to create (if None, creates all)
            
        Returns:
            List of PythonAgentTool instances
            
        Raises:
            ValueError: If any tool configuration is invalid
        """
        tools = []
        tools_created = 0
        tools_failed = []
        
        # Get tools to process
        if tool_names:
            tools_to_process = {
                name: mcp_tools.tools[name]
                for name in tool_names
                if name in mcp_tools.tools
            }
        else:
            tools_to_process = mcp_tools.tools
        
        # Create each tool
        for tool_name, tool_config in tools_to_process.items():
            try:
                tool = ToolFactory.create_strands_tool_from_mcp(
                    tool_name,
                    mcp_tools,
                    tool_config,
                )
                tools.append(tool)
                tools_created += 1
            except Exception as e:
                tools_failed.append(tool_name)
                factory = ToolFactory()
                factory.logger.warning(
                    f"Erro ao criar tool {tool_name}: {e}",
                    tool_name=tool_name,
                    error=str(e),
                    exc_info=True,
                )
        
        # Log summary
        factory = ToolFactory()
        factory.logger.info(
            "Validação de MCP Tools",
            tools_total=len(tools_to_process),
            tools_created=tools_created,
            tools_failed=len(tools_failed),
            failed_tools=tools_failed if tools_failed else None,
        )
        
        if tools_failed:
            factory.logger.warning(
                "Algumas tools falharam ao ser criadas - agentes podem ter funcionalidade limitada",
                failed_tools=tools_failed,
            )
        
        return tools

    @staticmethod
    def validate_tool_config(tool_config: MCPTool) -> bool:
        """Validate MCP tool configuration.
        
        Args:
            tool_config: MCPTool configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not tool_config.name:
            return False
        
        if tool_config.parameters:
            # Validate JSON Schema structure
            if not isinstance(tool_config.parameters, dict):
                return False
            
            # Check if it has properties (required for JSON Schema)
            if "properties" not in tool_config.parameters:
                # If no properties, ensure it's at least a valid object schema
                if "type" not in tool_config.parameters:
                    return False
        
        return True

