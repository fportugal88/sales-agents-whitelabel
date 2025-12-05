# Análise de Refatoração: Problemas Identificados

## Problemas de Código Repetitivo e Falta de Reuso

### 1. Inicialização Repetitiva de MCP Servers

**Problema:**
- MCP servers são inicializados em múltiplos lugares:
  - `SwarmSalesAgent._initialize_mcp_servers()`
  - `SalesOrchestrator.__init__()`
  - `server.py` (lifespan)

**Impacto:**
- Código duplicado
- Difícil manter consistência
- Erros de configuração

**Solução:**
- Criar `MCPServerFactory` para centralizar criação
- Singleton pattern para reutilizar instâncias

### 2. Criação de Tools Repetitiva

**Problema:**
- `create_strands_tool_from_mcp()` tem lógica complexa repetida
- Conversão de MCP tools para Strands tools é feita manualmente
- Validação de tools espalhada

**Impacto:**
- Código difícil de manter
- Erros de conversão
- Difícil adicionar novos tipos de tools

**Solução:**
- Criar `ToolFactory` para centralizar criação
- Abstrair conversão MCP → Strands
- Validação centralizada

### 3. Duplicação de Lógica de Orquestração

**Problema:**
- `SalesOrchestrator` e `SwarmOrchestrator` têm lógica similar:
  - Criação de conversas
  - Gerenciamento de estado
  - Tracking de métricas

**Impacto:**
- Manutenção duplicada
- Inconsistências entre orquestradores
- Difícil adicionar features

**Solução:**
- Criar `BaseOrchestrator` com lógica comum
- Herdar de base class
- Usar composição para diferenças

### 4. Agentes com Padrões Similares

**Problema:**
- `QualificationAgent`, `PresentationAgent`, etc. têm:
  - Mesma estrutura de `should_activate()`
  - Lógica similar de processamento
  - Padrões de resposta similares

**Impacto:**
- Muito código boilerplate
- Difícil adicionar novos agentes
- Inconsistências

**Solução:**
- Criar `BaseSalesAgent` com lógica comum
- Templates para criação de agentes
- Helpers para padrões comuns

### 5. Mapeamento de URLs para Servers

**Problema:**
- `MCPTools._get_server_name_from_url()` usa mapeamento hardcoded
- Lógica de detecção frágil (baseada em portas)

**Impacto:**
- Quebra quando portas mudam
- Difícil adicionar novos servers
- Não escalável

**Solução:**
- Configuração centralizada de mapeamento
- Registry pattern para servers
- Descoberta automática

### 6. Gerenciamento de Estado Duplicado

**Problema:**
- Conversas gerenciadas em múltiplos lugares:
  - `SwarmOrchestrator.conversations`
  - `SalesOrchestrator.conversations`
  - Estado também no Swarm interno

**Impacto:**
- Sincronização complexa
- Possível inconsistência
- Difícil debug

**Solução:**
- `ConversationRepository` centralizado
- Interface única para acesso
- Persistência opcional

### 7. Criação de Modelos Repetitiva

**Problema:**
- `create_openai_model()` é chamado em múltiplos lugares
- Configuração repetida

**Impacto:**
- Inconsistências de configuração
- Difícil mudar globalmente

**Solução:**
- Factory pattern para modelos
- Configuração centralizada
- Cache de instâncias

### 8. Tratamento de Erros Inconsistente

**Problema:**
- Cada componente trata erros de forma diferente
- Mensagens de erro inconsistentes
- Logging variado

**Impacto:**
- Debug difícil
- Experiência do usuário inconsistente

**Solução:**
- Error handlers centralizados
- Exceções customizadas
- Logging estruturado consistente

## Plano de Refatoração

### Fase 1: Factories e Abstrações
1. Criar `MCPServerFactory`
2. Criar `ToolFactory`
3. Criar `ModelFactory`

### Fase 2: Base Classes
1. Criar `BaseOrchestrator`
2. Criar `BaseSalesAgent`
3. Refatorar agentes existentes

### Fase 3: Repositories
1. Criar `ConversationRepository`
2. Centralizar gerenciamento de estado

### Fase 4: Configuração
1. Centralizar mapeamentos
2. Registry patterns
3. Configuração via arquivos

### Fase 5: Error Handling
1. Exceções customizadas
2. Error handlers centralizados
3. Logging consistente

## Benefícios Esperados

1. **Redução de Código**: ~30-40% menos código duplicado
2. **Manutenibilidade**: Mudanças em um lugar afetam todo sistema
3. **Testabilidade**: Componentes isolados mais fáceis de testar
4. **Extensibilidade**: Fácil adicionar novos agentes/tools
5. **Consistência**: Comportamento uniforme em todo sistema

