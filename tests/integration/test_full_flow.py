"""Integration tests for full sales flow."""

import pytest

from src.config.settings import Settings
from src.orchestrator.sales_orchestrator import SalesOrchestrator
from src.agents.faq_agent import FAQAgent
from src.agents.lead_gen_agent import LeadGenAgent
from src.agents.qualification_agent import QualificationAgent
from src.agents.presentation_agent import PresentationAgent
from src.agents.negotiation_agent import NegotiationAgent
from src.agents.closing_agent import ClosingAgent
from src.mcp_servers.mock_crm_server import MockCRMServer
from src.mcp_servers.mock_catalog_server import MockCatalogServer
from src.mcp_servers.mock_analytics_server import MockAnalyticsServer


@pytest.fixture
def settings():
    """Create settings fixture."""
    return Settings(
        STRANDS_API_KEY="test-key",
        APP_ENV="test",
    )


@pytest.fixture
def mcp_servers():
    """Create MCP servers fixture."""
    crm = MockCRMServer(simulate_latency=False)
    catalog = MockCatalogServer(simulate_latency=False)
    analytics = MockAnalyticsServer(simulate_latency=False)
    return {"crm": crm, "catalog": catalog, "analytics": analytics}


@pytest.fixture
def agents(mcp_servers):
    """Create agents fixture."""
    return [
        FAQAgent(catalog_server=mcp_servers["catalog"]),
        LeadGenAgent(crm_server=mcp_servers["crm"]),
        QualificationAgent(crm_server=mcp_servers["crm"]),
        PresentationAgent(
            catalog_server=mcp_servers["catalog"],
            crm_server=mcp_servers["crm"],
        ),
        NegotiationAgent(crm_server=mcp_servers["crm"]),
        ClosingAgent(crm_server=mcp_servers["crm"]),
    ]


@pytest.fixture
def orchestrator(settings, agents):
    """Create orchestrator fixture."""
    return SalesOrchestrator(settings=settings, agents=agents)


@pytest.mark.asyncio
async def test_faq_to_lead_generation_flow(orchestrator):
    """Test flow from FAQ to lead generation."""
    # Start with FAQ question
    result = await orchestrator.process_message("What products do you have?")

    assert "conversation_id" in result
    assert "response" in result
    assert result["stage"] == "faq"

    conversation_id = result["conversation_id"]

    # Provide contact info to trigger lead generation
    result = await orchestrator.process_message(
        "My email is test@example.com and I work at Test Company",
        conversation_id=conversation_id,
    )

    assert "response" in result
    # Should move to lead generation or qualification
    assert result["stage"] in ["lead_generation", "qualification"]


@pytest.mark.asyncio
async def test_full_sales_flow(orchestrator):
    """Test complete sales flow from FAQ to closing."""
    # Step 1: FAQ
    result = await orchestrator.process_message("I'm interested in your CRM product")
    conversation_id = result["conversation_id"]

    # Step 2: Lead generation
    result = await orchestrator.process_message(
        "My email is buyer@example.com, name is John Doe, company is Acme Corp",
        conversation_id=conversation_id,
    )

    # Step 3: Qualification
    result = await orchestrator.process_message(
        "We have a budget of $10,000 and need to decide within a month",
        conversation_id=conversation_id,
    )

    # Step 4: Presentation
    result = await orchestrator.process_message(
        "Show me how it works",
        conversation_id=conversation_id,
    )

    # Step 5: Negotiation
    result = await orchestrator.process_message(
        "The price seems high, can you offer a discount?",
        conversation_id=conversation_id,
    )

    # Step 6: Closing
    result = await orchestrator.process_message(
        "Yes, let's proceed with the purchase",
        conversation_id=conversation_id,
    )

    assert result["stage"] == "completed" or result["stage"] == "closing"


@pytest.mark.asyncio
async def test_orchestrator_conversation_management(orchestrator):
    """Test orchestrator conversation management."""
    # Create conversation
    conversation = await orchestrator.create_conversation()

    assert conversation.id is not None
    assert conversation.current_stage.value == "faq"

    # Get conversation
    retrieved = orchestrator.get_conversation(conversation.id)
    assert retrieved is not None
    assert retrieved.id == conversation.id

