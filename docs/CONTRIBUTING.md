# Guia de Contribuição

Obrigado por considerar contribuir para o Sales Agents Whitelabel!

## Como Contribuir

### 1. Fork e Clone

```bash
git clone <seu-fork-url>
cd sales-agents-whitelabel
```

### 2. Criar Ambiente de Desenvolvimento

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

pip install -r requirements.txt
pip install -e ".[dev]"
```

### 3. Configurar Pre-commit Hooks

```bash
# Instalar pre-commit (opcional mas recomendado)
pip install pre-commit
pre-commit install
```

### 4. Criar Branch

```bash
git checkout -b feature/nova-funcionalidade
```

### 5. Desenvolver

- Siga os padrões de código existentes
- Adicione type hints em todas as funções
- Escreva docstrings para todas as classes e funções
- Adicione testes para novas funcionalidades

### 6. Testar

```bash
# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/unit/test_faq_agent.py
```

### 7. Formatar Código

```bash
# Formatação com black
black src tests

# Linting com ruff
ruff check src tests

# Type checking com mypy
mypy src
```

### 8. Commit

```bash
git add .
git commit -m "feat: adiciona nova funcionalidade"
```

Siga o padrão de commits:
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `test:` Testes
- `refactor:` Refatoração
- `chore:` Tarefas de manutenção

### 9. Push e Pull Request

```bash
git push origin feature/nova-funcionalidade
```

Depois, crie um Pull Request no repositório principal.

## Padrões de Código

### Type Hints

Sempre use type hints:

```python
async def process_message(
    self,
    message: str,
    conversation: Conversation,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ...
```

### Docstrings

Use docstrings no formato Google:

```python
def process_message(self, message: str) -> str:
    """Process a message and return response.

    Args:
        message: User message to process

    Returns:
        Agent response text
    """
    ...
```

### Async/Await

Use operações assíncronas para I/O:

```python
async def get_data(self) -> Dict[str, Any]:
    result = await self.server.call("get_data")
    return result
```

### Error Handling

Sempre trate erros adequadamente:

```python
try:
    result = await self.call_api()
except APIError as e:
    self.logger.error("API call failed", error=str(e))
    raise RuntimeError(f"Failed to call API: {str(e)}") from e
```

## Estrutura de Testes

### Unit Tests

Teste cada componente isoladamente:

```python
@pytest.mark.asyncio
async def test_agent_process():
    agent = ConcreteAgent()
    result = await agent.process("test message")
    assert "response" in result
```

### Integration Tests

Teste fluxos completos:

```python
@pytest.mark.asyncio
async def test_full_sales_flow():
    orchestrator = create_orchestrator()
    result = await orchestrator.process_message("Hello")
    assert result["stage"] == "faq"
```

## Checklist de Pull Request

Antes de submeter um PR, verifique:

- [ ] Código segue os padrões estabelecidos
- [ ] Type hints adicionados
- [ ] Docstrings adicionadas
- [ ] Testes adicionados/atualizados
- [ ] Todos os testes passam
- [ ] Código formatado (black, ruff)
- [ ] Type checking passa (mypy)
- [ ] README atualizado se necessário
- [ ] CHANGELOG atualizado se necessário

## Dúvidas?

Se tiver dúvidas, abra uma issue ou entre em contato com os mantenedores.

