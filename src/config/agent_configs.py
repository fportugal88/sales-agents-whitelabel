"""Agent-specific configurations."""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for a specific agent."""

    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    priority: int = Field(default=0, description="Agent priority (higher = more important)")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: float = Field(default=30.0, description="Request timeout in seconds")
    custom_params: Dict[str, str] = Field(default_factory=dict, description="Custom parameters")


class AgentConfigs:
    """Manager for agent configurations."""

    def __init__(self) -> None:
        """Initialize with default agent configurations."""
        self._configs: Dict[str, AgentConfig] = {}

    def register(self, config: AgentConfig) -> None:
        """Register an agent configuration.

        Args:
            config: Agent configuration to register
        """
        self._configs[config.agent_id] = config

    def get(self, agent_id: str) -> Optional[AgentConfig]:
        """Get configuration for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent configuration or None if not found
        """
        return self._configs.get(agent_id)

    def get_all(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations.

        Returns:
            Dictionary of all agent configurations
        """
        return self._configs.copy()

    def is_enabled(self, agent_id: str) -> bool:
        """Check if an agent is enabled.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent is enabled, False otherwise
        """
        config = self.get(agent_id)
        return config.enabled if config else False


# Default agent configurations
default_configs = AgentConfigs()

# FAQ Agent
default_configs.register(
    AgentConfig(
        agent_id="faq",
        name="FAQ Agent",
        description="Handles product FAQ questions and suggests sales strategy",
        priority=1,
    )
)

# Lead Generation Agent
default_configs.register(
    AgentConfig(
        agent_id="lead_gen",
        name="Lead Generation Agent",
        description="Identifies and captures qualified leads",
        priority=2,
    )
)

# Qualification Agent
default_configs.register(
    AgentConfig(
        agent_id="qualification",
        name="Qualification Agent",
        description="Evaluates lead fit using BANT criteria",
        priority=3,
    )
)

# Presentation Agent
default_configs.register(
    AgentConfig(
        agent_id="presentation",
        name="Presentation Agent",
        description="Presents personalized solutions to leads",
        priority=4,
    )
)

# Negotiation Agent
default_configs.register(
    AgentConfig(
        agent_id="negotiation",
        name="Negotiation Agent",
        description="Handles objections and negotiates terms",
        priority=5,
    )
)

# Closing Agent
default_configs.register(
    AgentConfig(
        agent_id="closing",
        name="Closing Agent",
        description="Finalizes sales and collects feedback",
        priority=6,
    )
)

