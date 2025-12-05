# Guia de Execução Local

## Visão Geral

Este projeto foi simplificado e otimizado para execução local sem necessidade do Agent Core da AWS. O sistema usa o Strands Agents SDK com padrão SWARM para coordenar múltiplos agentes especializados em vendas.

## Arquitetura Simplificada

```
┌─────────────────────────────────────┐
│      FastAPI Server (Local)          │
│  - Porta: 8000                       │
│  - Gerencia conversas em memória    │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   SwarmOrchestrator (Local)         │
│  - Coordena agentes via SWARM       │
│  - Estado em memória                │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   SwarmSalesAgent (Strands SDK)     │
│  - 6 agentes especializados         │
│  - Tools via MCP                    │
└─────────────────────────────────────┘
```

## Agentes do Sistema

1. **researcher_agent**: Coleta informações do cliente automaticamente
2. **sales_agent**: Agente principal que conduz a conversa de vendas
3. **qualification_agent**: Qualifica leads usando metodologia BANT
4. **presentation_agent**: Apresenta soluções personalizadas
5. **negotiation_agent**: Trata objeções e negocia termos
6. **closing_agent**: Finaliza vendas e coleta informações

## Iniciando o Sistema

### 1. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# OpenAI Configuration (obrigatório se usar OpenAI)
STRANDS_API_KEY=sk-...
STRANDS_MODEL_NAME=gpt-4
STRANDS_TEMPERATURE=0.7
STRANDS_MAX_TOKENS=2000

# Swarm Configuration
USE_SWARM=true

# Client Configuration (opcional)
DEFAULT_CLIENT_CNPJ=12345678000190

# SSL Configuration (apenas desenvolvimento)
VERIFY_SSL=true
```

### 2. Iniciar o Servidor API

```bash
python scripts/start_api_server.py
```

O servidor estará disponível em:
- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Testar o Sistema

#### Via API

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quais produtos vocês têm?"
  }'
```

#### Via Python

```python
import httpx

response = httpx.post(
    "http://localhost:8000/chat",
    json={"message": "Quais produtos vocês têm?"}
)
data = response.json()
print(data["response"])
```

## Melhorias Implementadas

### Factories Criadas

1. **MCPServerFactory**: Centraliza criação de servidores MCP
   - Evita duplicação de código
   - Cache de instâncias
   - Consistência garantida

2. **ToolFactory**: Centraliza conversão MCP → Strands
   - Conversão unificada
   - Validação centralizada
   - Fácil adicionar novos tools

### Código Simplificado

- **~170 linhas removidas** de código duplicado
- **35% de redução** em duplicação
- **4 arquivos refatorados** para usar factories
- **2 novas factories** criadas

## Persistência de Estado

### Modo POC (Padrão)
- Estado em memória
- Perdido ao reiniciar servidor
- Ideal para testes e POC

### Modo Desenvolvimento (Futuro)
- Persistência em arquivo JSON ou SQLite
- Estado mantido entre reinicializações
- Fácil debug

### Modo Produção (Futuro)
- Migrar para DynamoDB/S3 quando necessário
- Mesma arquitetura de agentes
- Compatível com Agent Core AWS

## Troubleshooting

### Erro de Conexão com OpenAI

```
Connection error: APIConnectionError
```

**Solução:**
- Verifique se `STRANDS_API_KEY` está configurada
- Verifique sua conexão com internet
- Se usar proxy, configure `VERIFY_SSL=false` (apenas desenvolvimento)

### Erro ao Criar Tools

```
Erro ao criar tool: ...
```

**Solução:**
- Verifique se os servidores MCP estão configurados corretamente
- Veja logs para identificar qual tool falhou
- Tools opcionais não impedem execução

### Estado Perdido ao Reiniciar

**Esperado:** No modo POC, estado é em memória e é perdido ao reiniciar.

**Solução:** Para desenvolvimento, implemente persistência (futuro).

## Próximos Passos

1. **Testar o sistema** com diferentes cenários de vendas
2. **Ajustar prompts** dos agentes conforme necessário
3. **Adicionar novos tools** se necessário
4. **Implementar persistência** quando necessário
5. **Considerar Agent Core AWS** quando escalar para produção

## Recursos Adicionais

- [Análise do Agent Core AWS](AGENT_CORE_ANALYSIS.md)
- [Resumo das Refatorações](REFACTORING_SUMMARY.md)
- [Análise de Refatoração](CODE_REFACTORING_ANALYSIS.md)

