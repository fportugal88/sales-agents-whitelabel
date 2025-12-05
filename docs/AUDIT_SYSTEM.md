# Sistema de Auditoria

## Visão Geral

O sistema de auditoria captura e registra todas as decisões tomadas pelos agentes durante uma conversa, incluindo reasoning do LLM, tools utilizadas, e contexto usado. Isso permite rastreabilidade completa e transparência no processo de vendas.

## Componentes

### 1. Modelo de Auditoria

O modelo `AuditLog` (`src/models/audit.py`) captura:

- **timestamp**: Quando a decisão foi tomada
- **agent_id**: Agente que tomou a decisão
- **decision_type**: Tipo de decisão (agent_selection, tool_call, stage_transition, etc.)
- **reasoning**: Explicação do LLM sobre a decisão
- **tools_used**: Lista de tools chamadas
- **context**: Contexto usado na decisão
- **metadata**: Metadados adicionais

### 2. Tipos de Decisões

- **agent_selection**: Seleção de qual agente processar a mensagem
- **tool_call**: Chamada de uma tool MCP
- **stage_transition**: Transição entre estágios do funil
- **script_step**: Execução de uma etapa do script
- **response_generation**: Geração de resposta
- **context_update**: Atualização de contexto

### 3. Integração no Orquestrador

O orquestrador (`src/orchestrator/sales_orchestrator.py`) loga automaticamente:

- Seleção de agente
- Transições de estágio
- Chamadas de tools (quando detectadas no metadata)

### 4. Integração nos Agentes

Os agentes podem logar decisões através do metadata retornado:

```python
return {
    "response": "...",
    "metadata": {
        "tools_used": ["tool1", "tool2"],
        "tool_reasoning": "Razão para usar as tools",
        "tool_context": {...},
    }
}
```

## Uso

### Via API

#### Obter logs de auditoria

```bash
GET /chat/{conversation_id}/audit
```

Resposta:

```json
{
  "conversation_id": "...",
  "total_logs": 5,
  "logs": [
    {
      "timestamp": "2025-01-05T10:00:00Z",
      "agent_id": "sales_agent",
      "decision_type": "tool_call",
      "reasoning": "Preciso buscar informações do cliente para personalizar a abordagem",
      "tools_used": ["buscar_cliente_ifood"],
      "context": {...},
      "metadata": {...}
    }
  ]
}
```

#### Logs incluídos na resposta do chat

A resposta do endpoint `/chat` inclui os últimos 5 logs de auditoria no campo `metadata.audit_logs`.

### Via Streamlit

A interface Streamlit (`examples/streamlit_example.py`) exibe:

- **Agente Ativo**: Agente atual processando a mensagem
- **Estágio**: Estágio atual do funil
- **Tools Usadas**: Lista de tools chamadas na última mensagem
- **Reasoning**: Explicação da decisão (quando disponível)
- **Contexto**: Informações coletadas
- **Timeline**: Histórico de decisões (últimas 5)

## Tools Especializadas

### Informações do Cliente iFood

- **buscar_cliente_ifood**: Busca informações completas do cliente (produtos contratados, histórico, perfil)
- **verificar_produtos_contratados**: Verifica produtos já contratados

**Servidor**: `mock_ifood_server` (porta 8005)

### Informações do Restaurante

- **obter_info_restaurante**: Obtém informações do restaurante (mesas, faturamento, localização)
- **analisar_perfil_restaurante**: Analisa perfil e identifica necessidades

**Servidor**: `mock_restaurant_server` (porta 8006)

### Recomendação de Produtos

- **recomendar_produtos**: Recomenda produtos baseado no perfil e necessidades
- **avaliar_fit_produto**: Avalia fit de um produto específico

**Servidor**: `mock_recommendation_server` (porta 8007)

### Histórico de Contratos

- **buscar_historico_contratos**: Busca histórico de contratos do cliente
- **verificar_renovacoes_pendentes**: Verifica contratos próximos de vencer

**Servidor**: `mock_contract_server` (porta 8008)

### Cálculo de Preços

- **calcular_preco_personalizado**: Calcula preço personalizado baseado no perfil
- **obter_taxas_especiais**: Obtém taxas especiais para o cliente

**Servidor**: `mock_pricing_server` (porta 8009)

### Qualificação de Lead

- **qualificar_lead**: Qualifica lead usando BANT
- **calcular_lead_score**: Calcula score numérico do lead (0-100)

**Servidor**: `mock_qualification_server` (porta 8010)

## Fluxo de Uso das Tools

### Etapa 1: Identificar Necessidades

Tools disponíveis:
- `obter_info_restaurante`: Quando tiver CNPJ ou nome
- `buscar_cliente_ifood`: Quando tiver CNPJ ou email

O agente decide quando usar baseado no contexto da conversa.

### Etapa 2: Avaliar Fit

Tools disponíveis:
- `analisar_perfil_restaurante`: Analisa perfil e calcula fit score
- `recomendar_produtos`: Recomenda produtos baseado no perfil

### Etapa 3: Comunicar Benefícios

Tools disponíveis:
- `avaliar_fit_produto`: Avalia fit específico do produto
- `buscar_historico_contratos`: Verifica histórico do cliente

### Etapa 4: Obter Preço

Tools disponíveis:
- `calcular_preco_personalizado`: Calcula preço baseado no perfil
- `obter_taxas_especiais`: Obtém taxas especiais

### Etapa 5: Finalizar Compra

Tools disponíveis:
- `qualificar_lead`: Qualifica o lead antes de finalizar
- `calcular_lead_score`: Calcula score do lead
- `concluir_compra`: Finaliza a compra

## Exemplos de Reasoning Capturado

### Exemplo 1: Seleção de Agente

```json
{
  "decision_type": "agent_selection",
  "reasoning": "Agente sales_agent selecionado para processar a mensagem",
  "context": {
    "message_preview": "Gostaria de saber sobre a Maquinona",
    "current_stage": "faq"
  }
}
```

### Exemplo 2: Chamada de Tool

```json
{
  "decision_type": "tool_call",
  "reasoning": "Preciso buscar informações do cliente para entender o histórico e produtos já contratados",
  "tools_used": ["buscar_cliente_ifood"],
  "context": {
    "cnpj": "12345678000190"
  }
}
```

### Exemplo 3: Transição de Estágio

```json
{
  "decision_type": "stage_transition",
  "reasoning": "Transição de faq para lead_generation",
  "context": {
    "old_stage": "faq",
    "new_stage": "lead_generation"
  }
}
```

## Melhores Práticas

1. **Reasoning Conciso**: Mantenha o reasoning curto e objetivo
2. **Contexto Relevante**: Inclua apenas contexto relevante para a decisão
3. **Tools Documentadas**: Documente quando e por que usar cada tool
4. **Performance**: O sistema de auditoria não deve impactar a latência

## Notas Técnicas

- Logs são armazenados no `conversation.metadata["audit_logs"]`
- O sistema suporta até 100 logs por conversa (pode ser configurado)
- Logs mais antigos podem ser arquivados para análise posterior
- Reasoning é opcional - não é obrigatório para todas as decisões




