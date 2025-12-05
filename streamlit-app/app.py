"""Streamlit app para testar Sales Agents API usando Strands Agents."""

import streamlit as st
import httpx
import pandas as pd
import os
from typing import Optional

# Configuração da API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def check_server(port: int = 8000) -> bool:
    """Verifica se o servidor está respondendo."""
    try:
        response = httpx.get(f"http://localhost:{port}/health", timeout=1.0)
        return response.status_code == 200
    except:
        return False


# Configuração da página
st.set_page_config(
    page_title="Sales Agents - Chat",
    page_icon="🤖",
    layout="wide",
)

# CSS customizado
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1f77b4;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Detectar API
server_status = check_server()

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🤖 Sales Agents - Chat de Vendas")
    st.markdown("**Sistema usando Strands Agents Swarm**")
with col2:
    if server_status:
        st.success("🟢 Servidor Online")
    else:
        st.error("🔴 Servidor Offline")

# Inicializar estado
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "telemetry" not in st.session_state:
    st.session_state.telemetry = {}

# Sidebar
with st.sidebar:
    st.header("⚙️ Controles")
    
    if server_status:
        st.success(f"✅ Conectado\n`{API_BASE_URL}`")
    else:
        st.error("❌ Desconectado")
        st.info("Inicie o servidor:\n```bash\npython scripts/start_api_server.py\n```")
    
    st.markdown("---")
    
    if st.session_state.conversation_id:
        st.info(f"**ID:** `{st.session_state.conversation_id[:8]}...`")
        st.caption(f"**Mensagens:** {len(st.session_state.messages)}")
        if st.button("🆕 Nova Conversa", use_container_width=True):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.session_state.telemetry = {}
            st.rerun()
    else:
        st.info("Nenhuma conversa ativa")
    
    st.markdown("---")
    st.markdown("### 🤖 Agentes do Swarm")
    with st.expander("Ver detalhes", expanded=False):
        st.markdown("""
        - **🔍 Researcher**: Coleta informações do cliente
        - **💼 Sales Agent**: Agente principal de vendas
        - **✅ Qualification**: Avalia fit usando BANT
        - **📊 Presentation**: Apresenta soluções
        - **🤝 Negotiation**: Trata objeções
        - **🎯 Closing**: Finaliza vendas
        """)

# Tabs
tab1, tab2 = st.tabs(["💬 Chat", "📊 Métricas"])

# Tab 1: Chat
with tab1:
    if not server_status:
        st.warning("⚠️ **Servidor não está respondendo**")
        st.info("Execute: `python scripts/start_api_server.py`")
    
    # Container de mensagens
    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        with st.chat_message(role):
            st.markdown(message["content"])
            
            # Telemetria para mensagens do assistente
            if role == "assistant" and idx in st.session_state.telemetry:
                telemetry = st.session_state.telemetry[idx]
                with st.expander("📊 Detalhes", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🤖 Agente", telemetry.get("agent_id", "swarm"))
                    with col2:
                        st.metric("📊 Estágio", telemetry.get("stage", "N/A").upper())
                    with col3:
                        status = telemetry.get("status", "completed")
                        st.metric("Status", "✅" if status == "completed" else "⏳")
                    
                    agents_used = telemetry.get("agents_used", [])
                    if agents_used:
                        st.markdown(f"**Agentes:** {', '.join(agents_used)}")
                        handoffs = telemetry.get("total_handoffs", 0)
                        if handoffs > 0:
                            st.caption(f"🔀 Handoffs: {handoffs}")

    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        if not server_status:
            st.error("❌ Servidor não disponível")
        else:
            # Adicionar mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Processar com assistente
            with st.chat_message("assistant"):
                with st.spinner("🤖 Processando com Swarm..."):
                    try:
                        response = httpx.post(
                            f"{API_BASE_URL}/chat",
                            json={
                                "message": prompt,
                                "conversation_id": st.session_state.conversation_id,
                            },
                            timeout=60.0,
                        )
                        response.raise_for_status()
                        data = response.json()
                        
                        if not st.session_state.conversation_id:
                            st.session_state.conversation_id = data["conversation_id"]
                        
                        st.markdown(data["response"])
                        
                        # Extrair telemetria
                        metadata = data.get("metadata", {})
                        telemetry_data = {
                            "agent_id": data.get("agent_id", "swarm"),
                            "stage": data.get("stage", "N/A"),
                            "status": metadata.get("status", "completed"),
                            "agents_used": metadata.get("telemetry", {}).get("agents_used", []),
                            "total_handoffs": metadata.get("telemetry", {}).get("total_handoffs", 0),
                        }
                        
                        message_index = len(st.session_state.messages)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data["response"],
                        })
                        st.session_state.telemetry[message_index] = telemetry_data
                        
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
            
            st.rerun()

# Tab 2: Métricas
with tab2:
    st.header("📊 Dashboard de Métricas")
    
    if not server_status:
        st.warning("⚠️ Servidor não disponível")
    else:
        try:
            with st.spinner("Carregando métricas..."):
                metrics_response = httpx.get(
                    f"{API_BASE_URL}/metrics",
                    timeout=5.0,
                )
            
            if metrics_response.status_code == 200:
                metrics = metrics_response.json()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Conversas", metrics.get("total_conversations", 0))
                with col2:
                    st.metric("Vendas Fechadas", metrics.get("closed_sales", 0))
                with col3:
                    st.metric("Taxa Conversão", f"{metrics.get('sales_conversion_rate', 0):.1f}%")
                with col4:
                    st.metric("Taxa Abandono", f"{metrics.get('abandonment_rate', 0):.1f}%")
                
                st.markdown("---")
                
                # Conversões por etapa
                conversions_by_stage = metrics.get("conversations_by_stage", {})
                if conversions_by_stage:
                    st.markdown("### 📈 Funil de Conversão")
                    stages_data = []
                    for stage, count in conversions_by_stage.items():
                        stages_data.append({
                            "Etapa": stage.upper(),
                            "Conversas": count,
                        })
                    df = pd.DataFrame(stages_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.bar_chart(df.set_index("Etapa"))
                
                # Uso de agentes
                agents_usage = metrics.get("agents_usage", {})
                if agents_usage:
                    st.markdown("### 🤖 Uso de Agentes")
                    agents_data = [{"Agente": k, "Uso": v} for k, v in agents_usage.items()]
                    df_agents = pd.DataFrame(agents_data)
                    st.dataframe(df_agents, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"❌ Erro ao buscar métricas: {str(e)}")

