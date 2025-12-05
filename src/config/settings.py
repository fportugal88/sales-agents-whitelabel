"""Application settings using Strands Agents configuration."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Strands Agents framework."""

    # Application
    app_name: str = Field(default="sales-agents-whitelabel", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Strands Agents - OpenAI Model Configuration
    # Strands Agents uses OpenAI by default, configure via environment
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    
    # Model configuration (Strands Agents compatible)
    model_name: str = Field(default="gpt-4", alias="MODEL_ID")
    temperature: float = Field(default=0.7, alias="TEMPERATURE")
    max_tokens: int = Field(default=2000, alias="MAX_TOKENS")
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is provided."""
        if not v or not v.strip():
            raise ValueError(
                "OPENAI_API_KEY não configurada. "
                "Por favor, configure no arquivo .env: OPENAI_API_KEY=sk-..."
            )
        return v.strip()
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError(f"TEMPERATURE deve estar entre 0.0 e 2.0, recebido: {v}")
        return v
    
    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max_tokens is positive."""
        if v <= 0:
            raise ValueError(f"MAX_TOKENS deve ser maior que 0, recebido: {v}")
        return v

    # Swarm Configuration (Strands Agents Swarm)
    swarm_execution_timeout: float = Field(default=900.0, alias="SWARM_EXECUTION_TIMEOUT")
    swarm_node_timeout: float = Field(default=300.0, alias="SWARM_NODE_TIMEOUT")
    swarm_max_handoffs: int = Field(default=20, alias="SWARM_MAX_HANDOFFS")
    swarm_max_iterations: int = Field(default=20, alias="SWARM_MAX_ITERATIONS")

    # Client Configuration
    default_client_cnpj: Optional[str] = Field(
        default=None, alias="DEFAULT_CLIENT_CNPJ"
    )

    # Server Configuration
    server_port: int = Field(default=8000, alias="SERVER_PORT")

    # SSL Configuration (for development with corporate proxy/self-signed certificates)
    # Use truststore for production (pip install truststore)
    # Or set SSL_VERIFY=false ONLY for development
    ssl_verify: bool = Field(default=True, alias="SSL_VERIFY")
    use_truststore: bool = Field(default=True, alias="USE_TRUSTSTORE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance
        
    Raises:
        ValueError: If required settings are invalid or missing
    """
    try:
        return Settings()
    except Exception as e:
        error_msg = str(e)
        if "OPENAI_API_KEY" in error_msg:
            raise ValueError(
                "Erro de configuração: OPENAI_API_KEY não configurada.\n"
                "Por favor, configure no arquivo .env:\n"
                "OPENAI_API_KEY=sk-...\n\n"
                f"Erro original: {error_msg}"
            ) from e
        raise ValueError(
            f"Erro ao carregar configurações: {error_msg}\n"
            "Verifique o arquivo .env e as variáveis de ambiente."
        ) from e

