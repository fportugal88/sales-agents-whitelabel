# Sales Agents Whitelabel - Ecossistema Agêntico de Vendas

Sistema enterprise de agentes de vendas usando **Strands Agents**, framework de código aberto da AWS para construção de sistemas de IA multiagentes prontos para produção.

## 🏗️ Arquitetura

O sistema utiliza **Strands Agents Swarm** para coordenar múltiplos agentes especializados:

### Agentes do Swarm

- **Sales Agent**: Agente principal que conduz a conversa de vendas
- **Researcher Agent**: Coleta informações do cliente automaticamente no início
- **Qualification Agent**: Qualifica leads usando metodologia BANT
- **Presentation Agent**: Apresenta soluções personalizadas
- **Negotiation Agent**: Trata objeções e negocia termos
- **Closing Agent**: Finaliza vendas e coleta informações

### Framework Strands Agents

Este projeto utiliza exclusivamente o **Strands Agents** framework, que oferece:

- **Agentes Autônomos**: Agentes que planejam, orquestram tarefas e refletem sobre objetivos
- **Swarm Pattern**: Coordenação automática entre múltiplos agentes
- **Tools Integration**: Integração de ferramentas via decorador `@tool` e `PythonAgentTool`
- **Multi-Model Support**: Suporte para diversos LLMs (OpenAI, Anthropic, Bedrock, Ollama)
- **Session Management**: Gerenciamento de sessões e contexto de conversas

## 🚀 Instalação

### Pré-requisitos

- Python 3.10 ou superior
- pip ou poetry
- Chave da API OpenAI (para usar modelos OpenAI)

### Setup

1. Clone o repositório:
```bash
git clone <repository-url>
cd sales-agents-whitelabel
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -e ".[dev]"
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
# IMPORTANTE: Configure OPENAI_API_KEY com sua chave da OpenAI
```

### Variáveis de Ambiente

Crie um arquivo `.env` com as seguintes variáveis:

```env
# OpenAI API Configuration (required)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Model Configuration
MODEL_ID=gpt-4
TEMPERATURE=0.7
MAX_TOKENS=2000

# Swarm Configuration
SWARM_EXECUTION_TIMEOUT=900.0
SWARM_NODE_TIMEOUT=300.0
SWARM_MAX_HANDOFFS=20
SWARM_MAX_ITERATIONS=20

# Application Configuration
APP_NAME=sales-agents-whitelabel
LOG_LEVEL=INFO
SERVER_PORT=8000

# SSL Configuration (for corporate proxies/self-signed certificates)
# Option 1 (Recommended): Install truststore and use system certificates
#   pip install truststore
#   USE_TRUSTSTORE=true (default)
# Option 2 (Development only): Disable SSL verification
#   SSL_VERIFY=false (NÃO use em produção!)
```

### Configuração SSL para Ambientes Corporativos

Se você está em um ambiente corporativo com proxy/firewall que usa certificados auto-assinados:

**Opção 1 (Recomendada): Usar Truststore**

Instale o truststore que injeta certificados do sistema operacional:

```bash
pip install truststore
```

O sistema detectará automaticamente e usará os certificados do sistema. Não é necessário configuração adicional.

**Opção 2 (Apenas Desenvolvimento): Desabilitar Verificação SSL**

⚠️ **ATENÇÃO**: Use apenas em desenvolvimento local, nunca em produção!

```env
SSL_VERIFY=false
```

Isso desabilitará a verificação de certificados SSL. Use apenas se a Opção 1 não funcionar.

## 📖 Uso

### Iniciar o Servidor API

Para iniciar o servidor FastAPI que expõe os agentes:

```bash
python scripts/start_api_server.py
```

O servidor estará disponível em:
- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Endpoints Disponíveis

#### POST /chat
Envia uma mensagem para o sistema de agentes.

**Request:**
```json
{
  "message": "Quais produtos vocês têm?",
  "conversation_id": "opcional-id-da-conversa"
}
```

**Response:**
```json
{
  "conversation_id": "uuid-da-conversa",
  "response": "Resposta do agente em português",
  "agent_id": "sales_agent",
  "stage": "qualification",
  "metadata": {
    "telemetry": {
      "agents_used": ["sales_agent", "researcher"],
      "total_handoffs": 1
    }
  }
}
```

#### GET /conversation/{conversation_id}
Obtém o histórico de uma conversa.

#### POST /conversation
Cria uma nova conversa.

#### GET /health
Verifica o status do serviço.

#### GET /metrics
Obtém métricas de conversão do sistema.

**Response:**
```json
{
  "total_conversations": 100,
  "completed_conversations": 85,
  "closed_sales": 45,
  "sales_conversion_rate": 45.0,
  "abandonment_rate": 15.0,
  "conversations_by_stage": {
    "faq": 100,
    "qualification": 80,
    "presentation": 60,
    "negotiation": 50,
    "closing": 45
  },
  "conversion_rates_by_stage": {...},
  "average_time_by_stage": {...},
  "agents_usage": {...}
}
```

#### POST /chat/stream
Stream de eventos do Swarm em tempo real.

### Exemplo Programático

```python
import httpx

# Enviar mensagem
response = httpx.post(
    "http://localhost:8000/chat",
    json={"message": "Quais produtos vocês têm?"}
)
data = response.json()

print(f"Resposta: {data['response']}")
print(f"Agente: {data['agent_id']}")
print(f"Estágio: {data['stage']}")

# Continuar conversa
response = httpx.post(
    "http://localhost:8000/chat",
    json={
        "message": "Meu email é cliente@example.com",
        "conversation_id": data["conversation_id"]
    }
)
```

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
sales-agents-whitelabel/
├── src/
│   ├── agents/              # Agentes usando Strands Agents
│   │   └── swarm_sales_agent.py
│   ├── api/                 # Servidor FastAPI
│   │   └── server.py
│   ├── orchestrator/        # Orquestrador usando Strands Swarm
│   │   └── swarm_orchestrator.py
│   ├── config/              # Configurações
│   │   └── settings.py
│   ├── mcp_servers/          # MCP servers mockados
│   ├── models/               # Modelos Pydantic
│   └── utils/                # Utilitários
├── config/
│   └── agents/               # Configurações dos agentes
├── scripts/                  # Scripts de inicialização
├── examples/                 # Exemplos de uso
└── tests/                    # Testes
```

### Como Funciona

1. **Inicialização**: O sistema cria um `Swarm` do Strands Agents com 6 agentes especializados
2. **Processamento**: Quando uma mensagem chega, o `Swarm` decide qual agente deve processar
3. **Handoffs**: Os agentes podem fazer handoffs entre si usando o padrão Swarm do Strands
4. **Tools**: Os agentes usam tools (MCP tools) através do `PythonAgentTool` do Strands
5. **Contexto**: O Strands gerencia o contexto compartilhado entre agentes automaticamente

### Formatação de Código

```bash
black src tests
ruff check src tests
```

### Type Checking

```bash
mypy src
```

## 🧪 Testes

Execute os testes com:

```bash
pytest
```

Para cobertura de código:

```bash
pytest --cov=src --cov-report=html
```

## 📊 Métricas de Conversão

O sistema rastreia automaticamente métricas de conversão:

- **Taxa de Conversão de Vendas**: Percentual de conversas que resultam em vendas fechadas
- **Taxa de Conversão por Etapa**: Percentual de conversas que chegam a cada etapa do funil
- **Tempo Médio por Etapa**: Tempo gasto em cada etapa do funil
- **Taxa de Abandono**: Percentual de conversas que não são completadas
- **Uso de Agentes**: Frequência de uso de cada agente
- **Transições de Etapa**: Mapeamento de transições entre etapas

Acesse as métricas via:
- **API**: `GET /metrics`
- **Streamlit**: Dashboard de métricas na interface (se disponível)

## 📚 Documentação Strands Agents

Este projeto utiliza exclusivamente o framework **Strands Agents**. Para mais informações:

- [Documentação Oficial do Strands Agents](https://github.com/strands-agents/docs)
- [Strands Agents GitHub](https://github.com/strands-agents)

### Componentes Utilizados

- **Agent**: Classe base para criar agentes autônomos
- **Swarm**: Padrão de orquestração multiagente
- **OpenAIModel**: Integração com modelos OpenAI
- **PythonAgentTool**: Criação de tools para agentes
- **ToolSpec**: Especificação de tools

## 📝 Licença

MIT

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, certifique-se de que o código utiliza apenas o framework Strands Agents e segue as melhores práticas do framework.
