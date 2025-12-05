# Streamlit App - Sales Agents

Interface Streamlit para testar o Sales Agents API usando Strands Agents.

## Instalação

```bash
cd streamlit-app
pip install -r requirements.txt
```

## Uso

1. **Inicie o servidor API** (no diretório raiz do projeto):
```bash
python scripts/start_api_server.py
```

2. **Inicie o Streamlit**:
```bash
streamlit run app.py
```

A interface estará disponível em `http://localhost:8501`

## Funcionalidades

- 💬 Chat interativo com histórico de conversas
- 📊 Dashboard de métricas em tempo real
- 🤖 Visualização de telemetria dos agentes
- 📈 Gráficos de conversão e funil de vendas

## Configuração

Você pode configurar a URL da API através da variável de ambiente:

```bash
export API_BASE_URL=http://localhost:8000
streamlit run app.py
```

Ou edite diretamente no código `app.py` na linha:
```python
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
```

