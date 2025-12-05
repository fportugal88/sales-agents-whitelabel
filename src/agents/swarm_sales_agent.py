"""Sales agent system using Strands Agents Swarm."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from strands import Agent
from strands.multiagent import Swarm
from strands.models.openai import OpenAIModel

from src.config.settings import Settings
from src.utils.logger import LoggerMixin
from src.utils.mcp_server_factory import MCPServerFactory
from src.agents.mcp_tools import MCPTools
from src.models.agent_config import MCPTool


class SwarmSalesAgent(LoggerMixin):
    """Sales agent system using Strands Agents Swarm pattern."""

    def __init__(
        self,
        settings: Settings,
        default_cnpj: Optional[str] = None,
    ) -> None:
        """Initialize Swarm-based sales agent system.

        Args:
            settings: Application settings
            default_cnpj: Default CNPJ to use for client lookup
        """
        self.settings = settings
        self.default_cnpj = default_cnpj or settings.default_client_cnpj

        # Initialize MCP server factory
        MCPServerFactory.initialize(settings)
        self.mcp_servers = MCPServerFactory.get_all_servers(simulate_latency=False)
        
        # Initialize MCP tools
        self.mcp_tools = self._initialize_mcp_tools()
        
        # Create Strands tools from MCP tools
        self.strands_tools = self._create_strands_tools()
        
        # Create Swarm
        self.swarm = self._create_swarm()
        
        self.logger.info(
            "Swarm Sales Agent inicializado",
            default_cnpj=self.default_cnpj,
            tools_count=len(self.strands_tools),
        )

    def _initialize_mcp_tools(self) -> MCPTools:
        """Initialize MCP tools from configuration.

        Returns:
            MCPTools instance
        """
        config_path = Path("config/agents/sales_agent.json")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            tools_dict = config_data.get("tools", [])
            tools_config = [MCPTool(**tool) for tool in tools_dict]
        else:
            tools_config = []
        
        return MCPTools(tools_config, self.settings, servers=self.mcp_servers)

    def _create_strands_tools(self) -> List[Any]:
        """Create Strands tools from MCP tools.

        Returns:
            List of Strands tool functions
        """
        from strands.tools import PythonAgentTool
        from strands.types.tools import ToolSpec
        
        tools = []
        
        # Create a tool function for each MCP tool
        for tool_name, tool_config in self.mcp_tools.tools.items():
            # Capture tool_name in closure properly
            def make_tool_func(name: str, config: MCPTool):
                async def tool_func(**kwargs: Any) -> Dict[str, Any]:
                    """Tool function wrapper for Strands Agent."""
                    result = await self.mcp_tools.call_tool(name, kwargs)
                    return result
                return tool_func
            
            # Create tool function with proper closure
            tool_func = make_tool_func(tool_name, tool_config)
            
            # Create ToolSpec
            tool_spec: ToolSpec = {
                "name": tool_name,
                "description": tool_config.description or f"Tool {tool_name}",
                "inputSchema": tool_config.parameters or {"type": "object", "properties": {}},
            }
            
            # Create PythonAgentTool
            strands_tool = PythonAgentTool(
                tool_name=tool_name,
                tool_spec=tool_spec,
                tool_func=tool_func,
            )
            
            tools.append(strands_tool)
        
        return tools

    def _create_swarm(self) -> Swarm:
        """Create Swarm with specialized agents.

        Returns:
            Swarm instance
        """
        # Configure client_args for OpenAIModel
        client_args = {
            "api_key": self.settings.openai_api_key,
        }
        
        # Handle SSL verification for corporate proxies/self-signed certificates
        # Option 1: Use truststore (recommended) - injected at startup in server.py
        # Option 2: Disable SSL verification (development only)
        if not self.settings.ssl_verify:
            # Only for development - disable SSL verification
            # This creates an httpx client that doesn't verify SSL certificates
            import httpx
            
            # Create httpx client with SSL verification disabled
            http_client = httpx.AsyncClient(
                verify=False,  # Disable SSL verification
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
            
            # Pass http_client to OpenAI client
            # OpenAIModel will use this when creating AsyncOpenAI internally
            client_args["http_client"] = http_client
            
            self.logger.warning(
                "SSL verification desabilitada - APENAS PARA DESENVOLVIMENTO",
                hint="NÃO use SSL_VERIFY=false em produção! Use truststore em vez disso."
            )
        
        # Create OpenAIModel using Strands Agents pattern
        model = OpenAIModel(
            client_args=client_args,
            model_id=self.settings.model_name,
            params={
                "max_tokens": self.settings.max_tokens,
                "temperature": self.settings.temperature,
            },
        )

        # Create specialized agents
        researcher_agent = self._create_researcher_agent(model)
        sales_agent = self._create_sales_agent(model)
        qualification_agent = self._create_qualification_agent(model)
        presentation_agent = self._create_presentation_agent(model)
        negotiation_agent = self._create_negotiation_agent(model)
        closing_agent = self._create_closing_agent(model)
        
        # Create Swarm
        swarm = Swarm(
            [
                sales_agent,
                researcher_agent,
                qualification_agent,
                presentation_agent,
                negotiation_agent,
                closing_agent,
            ],
            entry_point=sales_agent,
            max_handoffs=self.settings.swarm_max_handoffs,
            max_iterations=self.settings.swarm_max_iterations,
            execution_timeout=self.settings.swarm_execution_timeout,
            node_timeout=self.settings.swarm_node_timeout,
        )

        return swarm

    def _create_researcher_agent(self, model: OpenAIModel) -> Agent:
        """Create researcher agent."""
        default_cnpj_text = self.default_cnpj or "12345678000190"
        
        system_prompt = f"""Você é um pesquisador especializado em coletar informações sobre clientes restaurantes.

Quando chamado pelo sales_agent, você DEVE:
1. Usar a tool obter_info_restaurante com CNPJ={default_cnpj_text}
2. Usar a tool buscar_cliente_ifood com CNPJ={default_cnpj_text}
3. Analisar essas informações e compartilhar um resumo no contexto compartilhado do Swarm

Depois de coletar, faça handoff de volta para o sales_agent com um resumo claro."""
        
        return Agent(
            name="researcher",
            model=model,
            system_prompt=system_prompt,
            tools=self.strands_tools if self.strands_tools else None,
            description="Coleta e analisa informações do cliente automaticamente",
        )

    def _create_sales_agent(self, model: OpenAIModel) -> Agent:
        """Create main sales agent."""
        default_cnpj_text = self.default_cnpj or "12345678000190"
        system_prompt = f"""Você é um vendedor especializado da Maquinona iFood Pago.

OBJETIVO: Conduzir a conversa de forma natural e empática, identificando necessidades e CONDUZINDO PARA CONVERSÃO.

INÍCIO DA CONVERSA:
Quando a conversa iniciar, você DEVE:
1. Primeiro, fazer handoff para o researcher_agent para buscar informações do cliente (CNPJ {default_cnpj_text})
2. Aguardar o researcher coletar as informações
3. Quando o researcher retornar, use essas informações para PERSONALIZAR a conversa

SOBRE A MAQUINONA:
A Maquinona combina máquina de pagamento com inteligência de marketing do iFood. Ela ajuda restaurantes a:
- AUMENTAR VENDAS com campanhas de marketing inteligentes
- FIDELIZAR CLIENTES com programas de cashback e cupons automáticos via WhatsApp
- TER DADOS E INSIGHTS sobre o negócio
- ACEITAR TODAS AS BANDEIRAS (crédito, débito, vale-refeição)

COMO CONDUZIR A CONVERSA:
1. Use as informações do cliente coletadas pelo researcher
2. Seja natural e conversacional
3. Faça perguntas ESTRATÉGICAS para identificar necessidades
4. ESCUTE ATENTAMENTE e identifique dores reais
5. CONECTE as necessidades identificadas com os benefícios da Maquinona
6. Destaque benefícios ESPECÍFICOS que resolvem os problemas mencionados

PROGRESSÃO NATURAL:
- Comece cumprimentando e mencionando algo específico sobre o restaurante
- Identifique necessidades através de perguntas naturais
- Quando identificar interesse, APRESENTE A SOLUÇÃO IMEDIATAMENTE
- Se o cliente perguntar sobre preço, use calcular_preco_personalizado
- Se precisar qualificar melhor (BANT), faça handoff para qualification_agent
- Se precisar apresentar detalhes, faça handoff para presentation_agent
- Se houver objeções, faça handoff para negotiation_agent
- Se o cliente mostrar interesse em contratar, faça handoff IMEDIATAMENTE para closing_agent

Responda SEMPRE em português brasileiro."""
        
        return Agent(
            name="sales_agent",
            model=model,
            system_prompt=system_prompt,
            tools=self.strands_tools if self.strands_tools else None,
            description="Agente principal de vendas da Maquinona",
        )

    def _create_qualification_agent(self, model: OpenAIModel) -> Agent:
        """Create qualification agent."""
        system_prompt = """Você é um especialista em qualificação de leads usando a metodologia BANT.

Sua função é qualificar leads de forma natural mas EFETIVA:
- Budget: Entender o orçamento disponível
- Authority: Identificar quem tem poder de decisão
- Need: Confirmar a necessidade real do restaurante
- Timeline: Entender quando precisam da solução

ESTRATÉGIA:
1. Faça perguntas que confirmem o FIT do restaurante com a Maquinona
2. Identifique sinais de ALTO POTENCIAL
3. Use as tools qualificar_lead e calcular_lead_score quando tiver informações suficientes
4. Se o lead_score for ALTO, recomende avançar para apresentação ou fechamento

Após qualificar, faça handoff de volta para o sales_agent com:
- Resumo da qualificação (BANT completo)
- Lead score e justificativa
- RECOMENDAÇÃO CLARA de próximos passos"""
        
        return Agent(
            name="qualification_agent",
            model=model,
            system_prompt=system_prompt,
            tools=self.strands_tools if self.strands_tools else None,
            description="Qualifica leads usando metodologia BANT",
        )

    def _create_presentation_agent(self, model: OpenAIModel) -> Agent:
        """Create presentation agent."""
        system_prompt = """Você é um especialista em apresentar soluções personalizadas para restaurantes.

Sua função é criar uma apresentação CONVINCENTE e PERSONALIZADA:
1. Use as informações do cliente para PERSONALIZAR
2. Apresente a Maquinona destacando benefícios ESPECÍFICOS para o perfil do restaurante
3. Use tools como recomendar_produtos e avaliar_fit_produto para personalizar
4. Seja entusiasta mas autêntico
5. Use CASOS DE SUCESSO quando apropriado
6. Destaque BENEFÍCIOS TANGÍVEIS

ESTRUTURA:
- Comece com o PROBLEMA identificado
- Apresente a Maquinona como SOLUÇÃO
- Destaque BENEFÍCIOS que resolvem a dor
- Termine com um CALL TO ACTION claro

Após apresentar, faça handoff:
- Para o sales_agent se a apresentação foi bem recebida
- Para o negotiation_agent se houver objeções
- Para o closing_agent se o cliente mostrar interesse claro"""
        
        return Agent(
            name="presentation_agent",
            model=model,
            system_prompt=system_prompt,
            tools=self.strands_tools if self.strands_tools else None,
            description="Apresenta soluções personalizadas baseado no perfil do restaurante",
        )

    def _create_negotiation_agent(self, model: OpenAIModel) -> Agent:
        """Create negotiation agent."""
        system_prompt = """Você é um especialista em negociação e tratamento de objeções.

Sua função é resolver objeções de forma empática e construtiva:
1. Identifique o tipo de objeção (preço, timing, necessidade, concorrência)
2. Valide a preocupação do cliente
3. Apresente argumentos sólidos e use tools quando necessário
4. Negocie termos quando apropriado
5. CONVERTA objeções em oportunidades

ESTRATÉGIAS POR TIPO DE OBJEÇÃO:
- PREÇO: Destaque ROI, compare com concorrência, ofereça condições especiais
- TIMING: Crie urgência se apropriado, mostre que implementação é rápida
- NECESSIDADE: Reforce os benefícios identificados, use dados do restaurante
- CONCORRÊNCIA: Destaque diferenciais da Maquinona

Após resolver objeções:
- Se objeções foram resolvidas e há interesse, faça handoff para o closing_agent
- Se ainda há dúvidas, faça handoff para o sales_agent"""
        
        return Agent(
            name="negotiation_agent",
            model=model,
            system_prompt=system_prompt,
            tools=self.strands_tools if self.strands_tools else None,
            description="Trata objeções e negocia termos quando necessário",
        )

    def _create_closing_agent(self, model: OpenAIModel) -> Agent:
        """Create closing agent."""
        system_prompt = """Você é um especialista em fechar vendas de forma natural e empática.

Sua função é finalizar a venda de forma POSITIVA e EFICIENTE:
1. Confirme o interesse do cliente de forma natural mas CLARA
2. Colete informações necessárias de forma CONVERSACIONAL mas DIRETA:
   - Nome completo, CNPJ, Email, Telefone
   - Cidade e estado, Número de mesas, Faturamento mensal
3. Use a tool concluir_compra quando tiver TODAS as informações
4. Agradeça e explique os próximos passos de forma CLARA

ESTRATÉGIA:
- Seja EFICIENTE: não prolongue desnecessariamente
- Seja POSITIVO: celebre o fechamento
- Seja CLARO: explique exatamente o que acontece a seguir
- Seja PROFISSIONAL: mostre que o cliente fez uma boa escolha

IMPORTANTE:
- NÃO perca a venda por não coletar todas as informações necessárias
- Use a tool concluir_compra assim que tiver todos os dados"""
        
        return Agent(
            name="closing_agent",
            model=model,
            system_prompt=system_prompt,
            tools=self.strands_tools if self.strands_tools else None,
            description="Finaliza vendas e coleta informações necessárias",
        )

    async def process(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process message using Swarm.

        Args:
            message: User message
            context: Additional context

        Returns:
            Response dictionary with result and telemetry
        """
        self.logger.info("Processando mensagem com Swarm", message_length=len(message))

        try:
            # Execute Swarm
            result = await self.swarm.invoke_async(message)
            
            # Extract response
            status = "completed"
            if hasattr(result, 'status'):
                status = result.status.value if hasattr(result.status, 'value') else str(result.status)
            
            response_text = ""
            if hasattr(result, 'results') and result.results:
                # Get the last successful node result
                node_results = list(result.results.values())
                for node_result in reversed(node_results):
                    if hasattr(node_result, 'result') and node_result.result:
                        result_obj = node_result.result
                        if isinstance(result_obj, str):
                            response_text = result_obj
                            break
                        elif hasattr(result_obj, 'text'):
                            response_text = str(result_obj.text)
                            break
                        elif hasattr(result_obj, 'content'):
                            content = result_obj.content
                            if isinstance(content, str):
                                response_text = content
                                break
            
            if not response_text:
                response_text = "Desculpe, não consegui gerar uma resposta. Pode repetir sua mensagem?"

            # Get node history for telemetry
            node_history = []
            agents_used = []
            if hasattr(result, 'node_history'):
                for node in result.node_history:
                    node_id = node.node_id if hasattr(node, 'node_id') else str(node)
                    node_status = node.status.value if hasattr(node, 'status') and hasattr(node.status, 'value') else str(getattr(node, 'status', 'unknown'))
                    node_history.append({
                        "node_id": node_id,
                        "status": node_status,
                    })
                    if node_id not in agents_used:
                        agents_used.append(node_id)

            # Get execution metrics
            execution_count = getattr(result, 'execution_count', 0)
            execution_time = getattr(result, 'execution_time', 0)
            accumulated_usage = getattr(result, 'accumulated_usage', {})
            
            if hasattr(accumulated_usage, '__dict__'):
                accumulated_usage = {
                    'inputTokens': getattr(accumulated_usage, 'inputTokens', 0),
                    'outputTokens': getattr(accumulated_usage, 'outputTokens', 0),
                    'totalTokens': getattr(accumulated_usage, 'totalTokens', 0),
                }

            return {
                "response": response_text,
                "status": status,
                "node_history": node_history,
                "execution_count": execution_count,
                "execution_time": execution_time,
                "accumulated_usage": accumulated_usage,
                "telemetry": {
                    "agents_used": agents_used,
                    "total_handoffs": len(node_history) - 1 if len(node_history) > 1 else 0,
                },
            }
        except Exception as e:
            self.logger.error("Erro ao processar mensagem com Swarm", error=str(e), exc_info=True)
            return {
                "response": "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                "status": "failed",
                "error": str(e),
            }

    async def stream(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Stream events from Swarm execution.

        Args:
            message: User message
            context: Additional context

        Yields:
            Event dictionaries
        """
        self.logger.info("Iniciando streaming de eventos do Swarm")

        try:
            async for event in self.swarm.stream_async(message):
                yield event
        except Exception as e:
            self.logger.error("Erro ao fazer streaming", error=str(e), exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
            }
