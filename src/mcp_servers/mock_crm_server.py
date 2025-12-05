"""Mock CRM MCP server for lead and sales data."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.mcp_servers.base_mcp import BaseMCPServer
from src.models.lead import Lead, LeadStatus


class MockCRMServer(BaseMCPServer):
    """Mock CRM server with in-memory data storage."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        simulate_latency: bool = True,
        latency_ms: float = 150.0,
    ) -> None:
        """Initialize mock CRM server.

        Args:
            base_url: Base URL (not used for mock, kept for compatibility)
            simulate_latency: Whether to simulate network latency
            latency_ms: Latency in milliseconds
        """
        super().__init__(
            server_name="mock_crm",
            base_url=base_url,
            simulate_latency=simulate_latency,
            latency_ms=latency_ms,
        )
        self._leads: Dict[str, Lead] = {}
        self._sales_history: List[Dict[str, Any]] = []
        self._initialize_mock_data()

    def _initialize_mock_data(self) -> None:
        """Initialize with sample mock data."""
        # Create some sample leads
        sample_leads = [
            {
                "id": "lead_001",
                "email": "john.doe@example.com",
                "name": "John Doe",
                "company": "Acme Corp",
                "phone": "+1-555-0101",
                "status": LeadStatus.NEW,
                "source": "website",
            },
            {
                "id": "lead_002",
                "email": "jane.smith@example.com",
                "name": "Jane Smith",
                "company": "TechStart Inc",
                "phone": "+1-555-0102",
                "status": LeadStatus.QUALIFIED,
                "source": "referral",
            },
            {
                "id": "lead_003",
                "email": "bob.wilson@example.com",
                "name": "Bob Wilson",
                "company": "Global Solutions",
                "phone": "+1-555-0103",
                "status": LeadStatus.PRESENTATION,
                "source": "event",
            },
        ]

        for lead_data in sample_leads:
            lead = Lead(**lead_data)
            self._leads[lead.id] = lead

        # Create sample sales history
        self._sales_history = [
            {
                "id": "sale_001",
                "lead_id": "lead_001",
                "product_id": "prod_001",
                "amount": 5000.0,
                "status": "closed_won",
                "closed_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            },
            {
                "id": "sale_002",
                "lead_id": "lead_002",
                "product_id": "prod_002",
                "amount": 12000.0,
                "status": "closed_won",
                "closed_at": (datetime.utcnow() - timedelta(days=15)).isoformat(),
            },
        ]

    async def call(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a CRM tool.

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

        if tool_name == "get_lead_info":
            return await self._get_lead_info(**params)
        elif tool_name == "update_lead_status":
            return await self._update_lead_status(**params)
        elif tool_name == "get_sales_history":
            return await self._get_sales_history(**params)
        elif tool_name == "concluir_compra":
            return await self._concluir_compra(**params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_lead_info(
        self,
        lead_id: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get lead information.

        Args:
            lead_id: Lead ID to lookup
            email: Lead email to lookup

        Returns:
            Lead information dictionary
        """
        # Validate that at least one identifier is provided
        if not lead_id and not email:
            return {
                "success": False,
                "error": "É necessário fornecer 'lead_id' ou 'email' para buscar informações do lead",
                "hint": "Forneça pelo menos um dos seguintes parâmetros: lead_id, email"
            }
        
        if lead_id:
            lead = self._leads.get(lead_id)
        elif email:
            lead = next((l for l in self._leads.values() if l.email == email), None)
        else:
            return {
                "success": False,
                "error": "Erro ao buscar lead",
                "lead_id": lead_id,
                "email": email
            }

        if not lead:
            return {"error": "Lead not found", "lead_id": lead_id, "email": email}

        return {
            "success": True,
            "lead": lead.model_dump(),
        }

    async def _update_lead_status(
        self,
        lead_id: str,
        status: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update lead status.

        Args:
            lead_id: Lead ID
            status: New status
            notes: Optional notes

        Returns:
            Update result
        """
        # Validate required parameters
        if not lead_id:
            return {
                "success": False,
                "error": "Parâmetro obrigatório 'lead_id' não fornecido",
                "hint": "Forneça o ID do lead que deseja atualizar"
            }
        
        if not status:
            return {
                "success": False,
                "error": "Parâmetro obrigatório 'status' não fornecido",
                "hint": "Forneça o novo status do lead"
            }
        """Update lead status.

        Args:
            lead_id: Lead ID to update
            status: New status
            notes: Optional notes

        Returns:
            Update result dictionary
        """
        lead = self._leads.get(lead_id)
        if not lead:
            return {"error": "Lead not found", "lead_id": lead_id}

        try:
            lead.status = LeadStatus(status)
            if notes:
                lead.notes = (lead.notes or "") + f"\n{notes}" if lead.notes else notes
            lead.updated_at = datetime.utcnow()

            return {
                "success": True,
                "lead_id": lead_id,
                "new_status": status,
                "updated_at": lead.updated_at.isoformat(),
            }
        except ValueError as e:
            return {"error": f"Invalid status: {status}", "details": str(e)}

    async def _get_sales_history(
        self,
        lead_id: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get sales history.

        Args:
            lead_id: Optional lead ID to filter by
            limit: Maximum number of records to return

        Returns:
            Sales history dictionary
        """
        history = self._sales_history.copy()

        if lead_id:
            history = [s for s in history if s.get("lead_id") == lead_id]

        history = history[:limit]

        return {
            "success": True,
            "count": len(history),
            "sales": history,
        }

    async def _concluir_compra(
        self,
        lead_id: Optional[str] = None,
        product_id: Optional[str] = None,
        product_name: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Finaliza a compra do cliente.

        Args:
            lead_id: ID do lead (opcional)
            product_id: ID do produto (opcional)
            product_name: Nome do produto (opcional)
            customer_name: Nome do cliente (opcional)
            customer_email: Email do cliente (opcional)

        Returns:
            Dicionário com resultado da compra
        """
        # Gerar ID da compra
        compra_id = f"compra_{uuid.uuid4().hex[:8]}"

        # Criar ou atualizar lead se necessário
        if lead_id:
            lead = self._leads.get(lead_id)
        elif customer_email:
            lead = next(
                (l for l in self._leads.values() if l.email == customer_email), None
            )
            if not lead:
                # Criar novo lead
                lead = Lead(
                    id=f"lead_{uuid.uuid4().hex[:8]}",
                    email=customer_email or "",
                    name=customer_name or "",
                    status=LeadStatus.CLOSED_WON,
                )
                self._leads[lead.id] = lead
                lead_id = lead.id
        else:
            # Criar lead anônimo
            lead_id = f"lead_{uuid.uuid4().hex[:8]}"
            lead = Lead(
                id=lead_id,
                email=customer_email or "",
                name=customer_name or "",
                status=LeadStatus.CLOSED_WON,
            )
            self._leads[lead_id] = lead

        # Atualizar status do lead
        if lead:
            lead.status = LeadStatus.CLOSED_WON
            lead.updated_at = datetime.utcnow()

        # Adicionar ao histórico de vendas
        sale_record = {
            "id": compra_id,
            "lead_id": lead_id,
            "product_id": product_id or "prod_001",
            "product_name": product_name or "Produto",
            "amount": 0.0,  # Seria obtido do catálogo
            "status": "closed_won",
            "closed_at": datetime.utcnow().isoformat(),
        }
        self._sales_history.append(sale_record)

        return {
            "success": True,
            "compra_id": compra_id,
            "lead_id": lead_id,
            "product_id": product_id,
            "status": "concluida",
            "message": "Compra finalizada com sucesso! Você receberá um email de confirmação em breve.",
        }

    def list_tools(self) -> list[Dict[str, Any]]:
        """List available CRM tools.

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "get_lead_info",
                "description": "Get lead information by ID or email",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lead_id": {"type": "string", "description": "Lead ID"},
                        "email": {"type": "string", "description": "Lead email"},
                    },
                },
            },
            {
                "name": "update_lead_status",
                "description": "Update lead status in CRM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lead_id": {"type": "string", "description": "Lead ID"},
                        "status": {
                            "type": "string",
                            "description": "New status",
                            "enum": [s.value for s in LeadStatus],
                        },
                        "notes": {"type": "string", "description": "Optional notes"},
                    },
                    "required": ["lead_id", "status"],
                },
            },
            {
                "name": "get_sales_history",
                "description": "Get sales history for a lead or all leads",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lead_id": {"type": "string", "description": "Optional lead ID filter"},
                        "limit": {"type": "integer", "description": "Maximum records to return"},
                    },
                },
            },
            {
                "name": "concluir_compra",
                "description": "Finaliza a compra do cliente e atualiza o CRM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lead_id": {"type": "string", "description": "ID do lead (opcional)"},
                        "product_id": {"type": "string", "description": "ID do produto (opcional)"},
                        "product_name": {"type": "string", "description": "Nome do produto (opcional)"},
                        "customer_name": {"type": "string", "description": "Nome do cliente (opcional)"},
                        "customer_email": {"type": "string", "description": "Email do cliente (opcional)"},
                    },
                },
            },
        ]

