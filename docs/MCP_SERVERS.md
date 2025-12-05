# MCP Servers - Guia de Uso

## Visão Geral

Os MCP (Model Context Protocol) Servers fornecem acesso a dados e funcionalidades para os agentes de vendas. O sistema inclui três servidores mockados:

- **CRM Server** (porta 8001): Gerencia leads e histórico de vendas
- **Catalog Server** (porta 8002): Fornece informações sobre produtos
- **Analytics Server** (porta 8003): Rastreia métricas e eventos de conversão

## Iniciando os Servidores

### Opção 1: Script Automático (Recomendado)

Execute o script que inicia todos os servidores:

```bash
python scripts/start_mcp_servers.py
```

Isso iniciará todos os três servidores simultaneamente nas portas 8001, 8002 e 8003.

### Opção 2: Uso Direto (Sem HTTP)

Os servidores podem ser usados diretamente no código Python sem necessidade de servidores HTTP:

```python
from src.mcp_servers.mock_crm_server import MockCRMServer
from src.mcp_servers.mock_catalog_server import MockCatalogServer
from src.mcp_servers.mock_analytics_server import MockAnalyticsServer

# Criar servidores
crm_server = MockCRMServer(simulate_latency=False)
catalog_server = MockCatalogServer(simulate_latency=False)
analytics_server = MockAnalyticsServer(simulate_latency=False)

# Usar diretamente
result = await crm_server.call("get_lead_info", {"lead_id": "lead_001"})
```

## Endpoints HTTP

Quando iniciados via HTTP, os servidores expõem os seguintes endpoints:

### CRM Server (http://localhost:8001)

- `POST /mcp/call` - Executa uma chamada MCP
- `GET /mcp/tools` - Lista ferramentas disponíveis
- `GET /health` - Health check

**Exemplo de chamada:**

```bash
curl -X POST http://localhost:8001/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "get_lead_info",
    "parameters": {"lead_id": "lead_001"}
  }'
```

### Catalog Server (http://localhost:8002)

- `POST /mcp/call` - Executa uma chamada MCP
- `GET /mcp/tools` - Lista ferramentas disponíveis
- `GET /health` - Health check

**Exemplo de chamada:**

```bash
curl -X POST http://localhost:8002/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "search_products",
    "parameters": {"query": "CRM", "limit": 5}
  }'
```

### Analytics Server (http://localhost:8003)

- `POST /mcp/call` - Executa uma chamada MCP
- `GET /mcp/tools` - Lista ferramentas disponíveis
- `GET /health` - Health check

**Exemplo de chamada:**

```bash
curl -X POST http://localhost:8003/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "track_event",
    "parameters": {
      "event_type": "stage_entry",
      "stage": "qualification",
      "lead_id": "lead_001"
    }
  }'
```

## Ferramentas Disponíveis

### CRM Server Tools

- `get_lead_info`: Obtém informações de um lead por ID ou email
- `update_lead_status`: Atualiza o status de um lead
- `get_sales_history`: Obtém histórico de vendas

### Catalog Server Tools

- `get_products`: Lista produtos com filtros opcionais
- `get_product_details`: Obtém detalhes de um produto específico
- `search_products`: Busca produtos por nome ou descrição

### Analytics Server Tools

- `get_conversion_metrics`: Obtém métricas de conversão por estágio
- `get_funnel_analytics`: Obtém analytics completo do funil
- `track_event`: Rastreia um evento de analytics

## Integração com Agentes

Os agentes usam os servidores MCP automaticamente através do orquestrador. Não é necessário configurar manualmente - o orquestrador gerencia as conexões.

## Troubleshooting

### Servidor não inicia

- Verifique se as portas 8001, 8002 e 8003 estão livres
- Certifique-se de que as dependências estão instaladas: `pip install -r requirements.txt`

### Erro de conexão

- Se estiver usando servidores HTTP, certifique-se de que eles estão rodando
- Se estiver usando diretamente, não é necessário servidores HTTP

### Dados não persistem

Os servidores mockados mantêm dados apenas em memória. Ao reiniciar, os dados são perdidos. Para persistência, implemente armazenamento em banco de dados.

