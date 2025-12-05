"""Mock Qualification MCP server for lead qualification."""

from typing import Any, Dict, List, Optional

from src.mcp_servers.base_mcp import BaseMCPServer


class MockQualificationServer(BaseMCPServer):
    """Mock qualification server for lead qualification and scoring."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 100.0,
    ) -> None:
        """Initialize mock qualification server.

        Args:
            base_url: Base URL (not used for mock, kept for compatibility)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds
        """
        super().__init__(
            server_name="mock_qualification",
            base_url=base_url,
            simulate_latency=simulate_latency,
            latency_ms=latency_ms,
        )

    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a qualification tool.

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

        if tool_name == "qualificar_lead":
            return await self._qualificar_lead(**params)
        elif tool_name == "calcular_lead_score":
            return await self._calcular_lead_score(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _qualificar_lead(
        self,
        lead_data: Optional[Dict[str, Any]] = None,
        conversa_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Qualificar lead usando BANT e contexto da conversa.

        Args:
            lead_data: Dados do lead
            conversa_context: Contexto da conversa

        Returns:
            Qualificação completa do lead
        """
        lead_data = lead_data or {}
        context = conversa_context or {}

        # Extract BANT information
        budget = lead_data.get("faturamento_mensal") or context.get("faturamento_mensal")
        authority = lead_data.get("nome") and lead_data.get("email")  # Has contact info
        need = context.get("necessidades") or lead_data.get("necessidades") or []
        timeline = context.get("urgencia") or "indefinido"

        # Calculate BANT scores (0-1 each)
        bant_scores = {
            "budget": 0.5 if budget else 0.0,
            "authority": 0.8 if authority else 0.0,
            "need": 0.7 if need else 0.0,
            "timeline": 0.6 if timeline != "indefinido" else 0.3,
        }

        # Adjust scores based on data quality
        if budget and budget > 100000:
            bant_scores["budget"] = 1.0
        if len(need) >= 2:
            bant_scores["need"] = 1.0

        # Calculate overall BANT score
        bant_score = sum(bant_scores.values()) / 4.0

        # Determine interest level
        if bant_score >= 0.8:
            interesse = "alto"
        elif bant_score >= 0.6:
            interesse = "medio"
        else:
            interesse = "baixo"

        # Determine urgency
        if timeline in ["imediato", "urgente"]:
            urgencia = "alta"
        elif timeline in ["30_dias", "60_dias"]:
            urgencia = "media"
        else:
            urgencia = "baixa"

        # Calculate fit score (based on restaurant profile)
        perfil = context.get("perfil_restaurante") or {}
        tamanho = perfil.get("tamanho", "medio")
        fit_score = 0.7  # Base
        if tamanho in ["medio", "grande"]:
            fit_score = 0.85
        if need and "fidelizar_clientes" in need:
            fit_score += 0.1
        fit_score = min(fit_score, 1.0)

        # Determine next steps
        proximos_passos = []
        if bant_score < 0.6:
            proximos_passos.append("Coletar mais informações sobre necessidades")
        if not budget:
            proximos_passos.append("Identificar faturamento mensal")
        if interesse == "alto" and fit_score >= 0.7:
            proximos_passos.append("Apresentar proposta comercial")
        else:
            proximos_passos.append("Continuar qualificação e educação")

        return {
            "success": True,
            "bant_score": round(bant_score, 2),
            "bant_scores": {k: round(v, 2) for k, v in bant_scores.items()},
            "nivel_interesse": interesse,
            "urgencia": urgencia,
            "fit_score": round(fit_score, 2),
            "proximos_passos": proximos_passos,
            "recomendacao": "Alta prioridade" if bant_score >= 0.7 and fit_score >= 0.7 else "Prioridade média",
        }

    async def _calcular_lead_score(
        self,
        lead_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calcular score numérico do lead.

        Args:
            lead_data: Dados do lead

        Returns:
            Score e análise do lead
        """
        score = 0.0
        fatores_positivos = []
        fatores_negativos = []
        recomendacoes = []

        # Email (20 points)
        if lead_data.get("email"):
            score += 20
            fatores_positivos.append("Email fornecido")
        else:
            fatores_negativos.append("Email não fornecido")

        # Company name (15 points)
        if lead_data.get("company") or lead_data.get("nome_empresa"):
            score += 15
            fatores_positivos.append("Nome da empresa fornecido")
        else:
            fatores_negativos.append("Nome da empresa não fornecido")

        # CNPJ (20 points)
        if lead_data.get("cnpj"):
            score += 20
            fatores_positivos.append("CNPJ fornecido")
        else:
            fatores_negativos.append("CNPJ não fornecido")

        # Revenue/Budget (25 points)
        faturamento = lead_data.get("faturamento_mensal") or lead_data.get("budget")
        if faturamento:
            if faturamento > 200000:
                score += 25
                fatores_positivos.append("Faturamento alto")
            elif faturamento > 100000:
                score += 20
                fatores_positivos.append("Faturamento médio")
            else:
                score += 10
                fatores_positivos.append("Faturamento informado")
        else:
            fatores_negativos.append("Faturamento não informado")

        # Needs identified (20 points)
        necessidades = lead_data.get("necessidades") or []
        if necessidades:
            score += min(len(necessidades) * 5, 20)
            fatores_positivos.append(f"{len(necessidades)} necessidades identificadas")
        else:
            fatores_negativos.append("Necessidades não identificadas")

        # Normalize to 0-100
        score = min(score, 100)

        # Generate recommendations
        if score < 50:
            recomendacoes.append("Coletar informações básicas (email, empresa, CNPJ)")
        if not faturamento:
            recomendacoes.append("Identificar faturamento mensal")
        if not necessidades:
            recomendacoes.append("Identificar necessidades do restaurante")
        if score >= 70:
            recomendacoes.append("Lead qualificado - prosseguir para apresentação")
        elif score >= 50:
            recomendacoes.append("Lead parcialmente qualificado - continuar qualificação")

        return {
            "success": True,
            "score": round(score, 1),
            "score_percentual": round(score, 1),
            "fatores_positivos": fatores_positivos,
            "fatores_negativos": fatores_negativos,
            "recomendacoes": recomendacoes,
            "categoria": (
                "Alta qualidade" if score >= 70
                else "Média qualidade" if score >= 50
                else "Baixa qualidade"
            ),
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "qualificar_lead",
                "description": "Qualifica o lead usando metodologia BANT e contexto da conversa. Retorna score BANT, nível de interesse, urgência, fit score e próximos passos",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lead_data": {
                            "type": "object",
                            "description": "Dados do lead (nome, email, empresa, faturamento, etc.)",
                        },
                        "conversa_context": {
                            "type": "object",
                            "description": "Contexto da conversa (necessidades, perfil, etc.)",
                        },
                    },
                },
            },
            {
                "name": "calcular_lead_score",
                "description": "Calcula score numérico do lead (0-100). Retorna score, fatores positivos, fatores negativos e recomendações",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lead_data": {
                            "type": "object",
                            "description": "Dados do lead",
                        },
                    },
                    "required": ["lead_data"],
                },
            },
        ]




