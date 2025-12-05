# Arquitetura do Ecossistema Agêntico de Vendas

## Visão Geral

O sistema é um ecossistema agêntico de vendas enterprise construído com Strands Agents, focado no aumento da taxa de conversão através de agentes especializados que trabalham em conjunto para guiar leads através do funil de vendas.

## Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│                    Sales Orchestrator                       │
│  - Gerencia estado global                                   │
│  - Roteia mensagens entre agentes                           │
│  - Decide qual agente ativar                                │
│  - Monitora métricas                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  FAQ Agent   │    │ Lead Gen     │    │ Qualification│
│              │    │ Agent        │    │ Agent        │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Presentation │    │ Negotiation  │    │ Closing      │
│ Agent        │    │ Agent        │    │ Agent        │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │      MCP Servers (Mockados)       │
        │  - CRM Server                     │
        │  - Catalog Server                 │
        │  - Analytics Server               │
        └───────────────────────────────────┘
```

## Fluxo de Trabalho

### 1. Início - FAQ Agent

O fluxo começa quando um usuário faz uma pergunta sobre produtos:

```
Usuário → Pergunta sobre produto
    ↓
FAQ Agent
    ├─ Analisa intenção
    ├─ Consulta catálogo MCP
    └─ Sugere estratégia ao orquestrador
```

### 2. Geração de Leads

Se a intenção de compra é detectada:

```
FAQ Agent → Detecta interesse
    ↓
Lead Gen Agent
    ├─ Extrai informações de contato
    ├─ Valida qualidade do lead
    └─ Cria lead no CRM
```

### 3. Qualificação

Lead é qualificado usando critérios BANT:

```
Lead Gen Agent → Lead capturado
    ↓
Qualification Agent
    ├─ Avalia Budget
    ├─ Avalia Authority
    ├─ Avalia Need
    ├─ Avalia Timeline
    └─ Classifica prioridade (Hot/Warm/Cold)
```

### 4. Apresentação

Solução personalizada é apresentada:

```
Qualification Agent → Lead qualificado
    ↓
Presentation Agent
    ├─ Seleciona produtos relevantes
    ├─ Personaliza apresentação
    └─ Apresenta casos de uso
```

### 5. Negociação

Objeções são tratadas:

```
Presentation Agent → Interesse confirmado
    ↓
Negotiation Agent
    ├─ Identifica tipo de objeção
    ├─ Gera resposta personalizada
    └─ Negocia termos
```

### 6. Fechamento

Venda é finalizada:

```
Negotiation Agent → Objeções resolvidas
    ↓
Closing Agent
    ├─ Confirma venda
    ├─ Atualiza CRM
    └─ Coleta feedback
```

## Componentes Principais

### Orquestrador

O `SalesOrchestrator` é o componente central que:

- Gerencia todas as conversas
- Mantém estado global
- Decide qual agente deve processar cada mensagem
- Implementa retry logic e error handling
- Rastreia métricas de conversão

### Agentes

Cada agente é especializado em uma etapa do funil:

1. **FAQ Agent**: Processa perguntas iniciais e analisa intenção
2. **Lead Gen Agent**: Identifica e captura leads
3. **Qualification Agent**: Avalia fit usando BANT
4. **Presentation Agent**: Apresenta soluções personalizadas
5. **Negotiation Agent**: Trata objeções e negocia
6. **Closing Agent**: Finaliza vendas

### MCP Servers

Servidores MCP mockados que fornecem:

- **CRM Server**: Dados de leads e histórico de vendas
- **Catalog Server**: Informações de produtos
- **Analytics Server**: Métricas e eventos de conversão

### Tools

Tools de integração que encapsulam:

- Error handling
- Retry logic
- Cache
- Validação de dados

## Modelos de Dados

### Lead

Representa um lead potencial com:
- Informações de contato
- Status no pipeline
- Prioridade (Hot/Warm/Cold)
- Score BANT

### Conversation

Rastreia toda a interação:
- Mensagens trocadas
- Estágio atual
- Agente ativo
- Contexto adicional

### SalesPipeline

Métricas do pipeline:
- Taxa de conversão por etapa
- Tempo médio em cada etapa
- Total de leads
- Total convertidos

## Sistema de Métricas

O sistema rastreia:

1. **Eventos**: Cada ação importante é rastreada
2. **Conversões**: Taxa de conversão por etapa
3. **Performance**: Tempo médio em cada etapa
4. **Agentes**: Efetividade de cada agente
5. **Produtos**: Produtos mais vendidos

## Padrões Enterprise

### Type Safety

- Type hints completos em todo código
- Validação com Pydantic
- Type checking com mypy

### Error Handling

- Try/except com logging estruturado
- Retry logic com backoff exponencial
- Graceful degradation

### Performance

- Operações assíncronas (async/await)
- Cache para reduzir chamadas MCP
- Simulação de latência realista

### Testabilidade

- Dependency injection
- Interfaces claras
- Testes unitários e de integração

### Observabilidade

- Logging estruturado
- Métricas de performance
- Rastreamento de eventos

## Extensibilidade

O sistema foi projetado para ser facilmente extensível:

1. **Novos Agentes**: Herdar de `BaseAgent` e implementar métodos abstratos
2. **Novos MCPs**: Herdar de `BaseMCPServer` e implementar tools
3. **Novas Tools**: Criar classes de tool com error handling
4. **Novas Métricas**: Estender `MetricsCollector` e `MetricsCalculator`

## Segurança

- Validação de entrada com Pydantic
- Sanitização de dados
- Logging sem informações sensíveis
- Environment variables para configuração

## Escalabilidade

O sistema foi projetado para escalar:

- Operações assíncronas
- Cache para reduzir carga
- Stateless agents (exceto conversas)
- MCP servers podem ser distribuídos

## Próximos Passos

1. Integração com Strands Agents real
2. Integração com LLMs para respostas mais inteligentes
3. Machine learning para otimização de conversão
4. Dashboard web para visualização de métricas
5. Integração com CRMs reais (Salesforce, HubSpot, etc.)

