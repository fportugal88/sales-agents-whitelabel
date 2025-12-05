"""Exemplo de integração Streamlit com Sales Agents API usando Swarm."""

import streamlit as st
import httpx
import json
import pandas as pd
import os
from datetime import datetime
from typing import Optional

# Configuração da API
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() not in ("false", "0", "no", "off")

def check_server(port: int) -> bool:
    """Verifica se o servidor está respondendo na porta."""
    try:
        response = httpx.get(f"http://localhost:{port}/health", timeout=1.0, verify=VERIFY_SSL)
        return response.status_code == 200
    except:
        return False

def get_api_base_url() -> str:
    """Detecta automaticamente a porta do servidor."""
    if check_server(8000):
        return "http://localhost:8000"
    elif check_server(8004):
        return "http://localhost:8004"
    else:
        return "http://localhost:8000"  # Default

# Configuração da página
st.set_page_config(
    page_title="Sales Agents - Swarm Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    /* Estilo geral */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header customizado */
    h1 {
        color: #1f77b4;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    
    /* Cards de métricas */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* Chat messages */
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    /* Badges de status */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .status-success {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-info {
        background-color: #d1ecf1;
        color: #0c5460;
    }
    
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Telemetria */
    .telemetry-box {
        background-color: #f8f9fa;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        border-radius: 5px;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Detectar API
API_BASE_URL = get_api_base_url()
server_status = check_server(8000) or check_server(8004)

# Header principal
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title("🤖 Sales Agents - Chat de Vendas")
    st.markdown("**Sistema inteligente de agentes de vendas usando Swarm do Strands Agents**")
with col_header2:
    if server_status:
        st.success("🟢 Servidor Online")
    else:
        st.error("🔴 Servidor Offline")
        st.caption(f"Tentando conectar em: {API_BASE_URL}")

# Inicializar estado da sessão
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "telemetry" not in st.session_state:
    st.session_state.telemetry = {}
if "server_status" not in st.session_state:
    st.session_state.server_status = server_status

# Sidebar melhorada
with st.sidebar:
    st.header("⚙️ Controles")
    
    # Status do servidor
    st.markdown("### 📡 Status da Conexão")
    if server_status:
        st.success(f"✅ Conectado\n`{API_BASE_URL}`")
    else:
        st.error("❌ Desconectado")
        st.info("Inicie o servidor com:\n```bash\npython scripts/start_api_server.py\n```")
    
    st.markdown("---")
    
    # Informações da conversa
    st.markdown("### 💬 Conversa")
    if st.session_state.conversation_id:
        st.info(f"**ID:** `{st.session_state.conversation_id[:8]}...`")
        st.caption(f"**Mensagens:** {len(st.session_state.messages)}")
        if st.button("🆕 Nova Conversa", use_container_width=True, type="primary"):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.session_state.telemetry = {}
            st.rerun()
    else:
        st.info("Nenhuma conversa ativa")
        st.caption("Inicie uma conversa digitando uma mensagem")
    
    st.markdown("---")
    
    # Informações sobre agentes
    st.markdown("### 🤖 Agentes do Swarm")
    with st.expander("Ver detalhes", expanded=False):
        st.markdown("""
        Este chat utiliza um **Swarm de agentes especializados**:
        
        - **🔍 Researcher**: Coleta informações do cliente automaticamente
        - **💼 Sales Agent**: Agente principal de vendas
        - **✅ Qualification**: Avalia fit usando metodologia BANT
        - **📊 Presentation**: Apresenta soluções personalizadas
        - **🤝 Negotiation**: Trata objeções e negocia termos
        - **🎯 Closing**: Finaliza vendas e coleta informações
        
        Os agentes colaboram **autonomamente** através do Swarm!
        """)
    
    st.markdown("---")
    
    # Ações rápidas
    st.markdown("### 🔧 Ações")
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()
    
    if st.button("🗑️ Limpar Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.telemetry = {}
        st.rerun()
    
    st.markdown("---")
    st.caption("**Sales Agents Ecosystem v2.0.0**\nSwarm Mode")

# Tabs principais
tab1, tab2 = st.tabs(["💬 Chat", "📊 Dashboard de Métricas"])

# Tab 1: Chat
with tab1:
    if not server_status:
        st.warning("⚠️ **Servidor não está respondendo**")
        st.info("""
        Para iniciar o servidor, execute em outro terminal:
        ```bash
        python scripts/start_api_server.py
        ```
        """)
    
    # Container para mensagens
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            # Mensagem de boas-vindas
            st.info("👋 **Bem-vindo!** Digite uma mensagem abaixo para começar a conversa.")
            st.markdown("""
            **Exemplos de mensagens:**
            - "Quais produtos vocês têm?"
            - "Preciso de uma solução para meu restaurante"
            - "Como funciona o sistema de delivery?"
            """)
        else:
            # Exibir histórico de mensagens
            for idx, message in enumerate(st.session_state.messages):
                role = message["role"]
                
                with st.chat_message(role):
                    # Conteúdo da mensagem
                    st.markdown(message["content"])
                    
                    # Telemetria para mensagens do assistente
                    if role == "assistant" and idx in st.session_state.telemetry:
                        telemetry = st.session_state.telemetry[idx]
                        
                        # Container de telemetria
                        with st.expander("📊 Detalhes da Execução", expanded=False):
                            # Informações principais em colunas
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                agent_id = telemetry.get("agent_id", "swarm")
                                st.metric("🤖 Agente", agent_id)
                            
                            with col2:
                                stage = telemetry.get("stage", "N/A")
                                st.metric("📊 Estágio", stage.upper())
                            
                            with col3:
                                status = telemetry.get("status", "completed")
                                status_emoji = "✅" if status == "completed" else "⏳"
                                st.metric("Status", f"{status_emoji} {status}")
                            
                            st.markdown("---")
                            
                            # Agentes envolvidos
                            agents_used = telemetry.get("agents_used", [])
                            if agents_used:
                                st.markdown("**🔄 Agentes Envolvidos:**")
                                agent_badges = " ".join([f"`{agent}`" for agent in agents_used])
                                st.markdown(agent_badges)
                                
                                total_handoffs = telemetry.get("total_handoffs", 0)
                                if total_handoffs > 0:
                                    st.caption(f"🔀 **Handoffs realizados:** {total_handoffs}")
                            
                            # Tools usadas
                            tools_used = telemetry.get("tools_used", [])
                            if tools_used:
                                st.markdown("**🔧 Tools Utilizadas:**")
                                tool_badges = " ".join([f"`{tool}`" for tool in tools_used])
                                st.markdown(tool_badges)
                            
                            # Métricas de performance
                            execution_time = telemetry.get("execution_time", 0)
                            execution_count = telemetry.get("execution_count", 0)
                            if execution_time > 0 or execution_count > 0:
                                col_perf1, col_perf2 = st.columns(2)
                                with col_perf1:
                                    st.metric("⏱️ Tempo", f"{execution_time}ms")
                                with col_perf2:
                                    st.metric("🔄 Iterações", execution_count)
                            
                            # Uso de tokens
                            usage = telemetry.get("accumulated_usage", {})
                            if usage:
                                input_tokens = usage.get("input_tokens", 0)
                                output_tokens = usage.get("output_tokens", 0)
                                total_tokens = input_tokens + output_tokens
                                
                                if total_tokens > 0:
                                    col_tok1, col_tok2, col_tok3 = st.columns(3)
                                    with col_tok1:
                                        st.metric("📥 Input", f"{input_tokens:,}")
                                    with col_tok2:
                                        st.metric("📤 Output", f"{output_tokens:,}")
                                    with col_tok3:
                                        st.metric("📊 Total", f"{total_tokens:,}")
                            
                            # Node history
                            node_history = telemetry.get("node_history", [])
                            if node_history:
                                st.markdown("**📜 Histórico de Execução:**")
                                for node in node_history:
                                    node_id = node.get("node_id", "unknown")
                                    node_status = node.get("status", "unknown")
                                    status_icon = "✅" if node_status == "completed" else "⏳"
                                    st.text(f"{status_icon} {node_id} ({node_status})")

    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem aqui..."):
        if not server_status:
            st.error("❌ Servidor não está disponível. Inicie o servidor antes de enviar mensagens.")
        else:
            # Adicionar mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Mostrar mensagem do usuário
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Processar com o assistente
            with st.chat_message("assistant"):
                with st.spinner("🤖 Processando com Swarm..."):
                    try:
                        # Chamar API
                        response = httpx.post(
                            f"{API_BASE_URL}/chat",
                            json={
                                "message": prompt,
                                "conversation_id": st.session_state.conversation_id,
                            },
                            timeout=60.0,
                            verify=VERIFY_SSL,
                        )
                        response.raise_for_status()
                        data = response.json()
                        
                        # Atualizar conversation_id
                        if not st.session_state.conversation_id:
                            st.session_state.conversation_id = data["conversation_id"]
                        
                        # Exibir resposta
                        st.markdown(data["response"])
                        
                        # Extrair telemetria
                        metadata = data.get("metadata", {})
                        telemetry_data = {
                            "agent_id": data.get("agent_id", "swarm"),
                            "stage": data.get("stage", "N/A"),
                            "status": metadata.get("status", "completed"),
                            "agents_used": metadata.get("telemetry", {}).get("agents_used", []),
                            "total_handoffs": metadata.get("telemetry", {}).get("total_handoffs", 0),
                            "execution_time": metadata.get("execution_time", 0),
                            "execution_count": metadata.get("execution_count", 0),
                            "accumulated_usage": metadata.get("accumulated_usage", {}),
                            "node_history": metadata.get("node_history", []),
                        }
                        
                        # Extrair tools usadas
                        tools_used = []
                        for node in telemetry_data.get("node_history", []):
                            if "tools" in node:
                                tools_used.extend(node.get("tools", []))
                        telemetry_data["tools_used"] = list(set(tools_used))
                        
                        # Adicionar à conversa
                        message_index = len(st.session_state.messages)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data["response"],
                            "agent_id": data.get("agent_id"),
                            "stage": data.get("stage"),
                            "metadata": metadata,
                        })
                        
                        # Armazenar telemetria
                        st.session_state.telemetry[message_index] = telemetry_data
                        
                    except httpx.ConnectError:
                        st.error("❌ **Erro de conexão**")
                        st.info("""
                        Não foi possível conectar ao servidor. Verifique se:
                        1. O servidor está rodando (`python scripts/start_api_server.py`)
                        2. O servidor está na porta correta (8000 ou 8004)
                        3. Não há firewall bloqueando a conexão
                        """)
                    except httpx.TimeoutException:
                        st.error("⏱️ **Timeout**")
                        st.info("A requisição demorou muito para responder. Tente novamente.")
                    except httpx.HTTPStatusError as e:
                        st.error(f"❌ **Erro HTTP {e.response.status_code}**")
                        st.info(f"Resposta do servidor: {e.response.text}")
                    except Exception as e:
                        st.error(f"❌ **Erro inesperado**")
                        st.exception(e)
            
            # Rerun para atualizar a interface
            st.rerun()

# Tab 2: Dashboard de Métricas
with tab2:
    st.header("📊 Dashboard de Métricas de Conversão")
    st.markdown("Métricas em tempo real do sistema de vendas")
    
    if not server_status:
        st.warning("⚠️ Servidor não está disponível. Métricas não podem ser carregadas.")
    else:
        try:
            # Buscar métricas da API
            with st.spinner("Carregando métricas..."):
                metrics_response = httpx.get(
                    f"{API_BASE_URL}/metrics",
                    timeout=5.0,
                    verify=VERIFY_SSL
                )
            
            if metrics_response.status_code == 200:
                metrics = metrics_response.json()
                
                # Métricas principais em cards
                st.markdown("### 📈 Métricas Principais")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_conv = metrics.get("total_conversations", 0)
                    st.metric(
                        "Total de Conversas",
                        f"{total_conv:,}",
                        help="Número total de conversas iniciadas"
                    )
                
                with col2:
                    closed_sales = metrics.get("closed_sales", 0)
                    st.metric(
                        "Vendas Fechadas",
                        f"{closed_sales:,}",
                        help="Número de vendas concluídas"
                    )
                
                with col3:
                    conversion_rate = metrics.get("sales_conversion_rate", 0.0)
                    delta_color = "normal" if conversion_rate >= 30 else "inverse"
                    st.metric(
                        "Taxa de Conversão",
                        f"{conversion_rate:.1f}%",
                        help="Percentual de conversas que resultam em vendas"
                    )
                
                with col4:
                    abandonment_rate = metrics.get("abandonment_rate", 0.0)
                    st.metric(
                        "Taxa de Abandono",
                        f"{abandonment_rate:.1f}%",
                        help="Percentual de conversas abandonadas"
                    )
                
                st.markdown("---")
                
                # Conversões por etapa
                st.markdown("### 📈 Funil de Conversão por Etapa")
                conversions_by_stage = metrics.get("conversations_by_stage", {})
                conversion_rates = metrics.get("conversion_rates_by_stage", {})
                
                if conversions_by_stage:
                    # Tabela
                    stages_data = []
                    for stage, count in conversions_by_stage.items():
                        rate = conversion_rates.get(stage, 0.0)
                        stages_data.append({
                            "Etapa": stage.upper(),
                            "Conversas": count,
                            "Taxa de Conversão": f"{rate:.1f}%"
                        })
                    
                    df_stages = pd.DataFrame(stages_data)
                    st.dataframe(
                        df_stages,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Gráfico de barras
                    if len(stages_data) > 0:
                        chart_data = pd.DataFrame({
                            "Conversas": [d["Conversas"] for d in stages_data],
                        }, index=[d["Etapa"] for d in stages_data])
                        st.bar_chart(chart_data, use_container_width=True)
                else:
                    st.info("Nenhuma métrica de etapa disponível ainda.")
                
                st.markdown("---")
                
                # Uso de agentes
                st.markdown("### 🤖 Uso de Agentes")
                agents_usage = metrics.get("agents_usage", {})
                
                if agents_usage:
                    agents_data = []
                    for agent, count in sorted(agents_usage.items(), key=lambda x: x[1], reverse=True):
                        agents_data.append({
                            "Agente": agent,
                            "Uso": count
                        })
                    
                    df_agents = pd.DataFrame(agents_data)
                    st.dataframe(
                        df_agents,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Gráfico de barras
                    if len(agents_data) > 0:
                        chart_data = pd.DataFrame({
                            "Uso": [d["Uso"] for d in agents_data],
                        }, index=[d["Agente"] for d in agents_data])
                        st.bar_chart(chart_data, use_container_width=True)
                else:
                    st.info("Nenhuma métrica de agente disponível ainda.")
                
                st.markdown("---")
                
                # Tempo médio por etapa
                st.markdown("### ⏱️ Performance por Etapa")
                avg_time_by_stage = metrics.get("average_time_by_stage", {})
                
                if avg_time_by_stage:
                    time_data = []
                    for stage, avg_time in avg_time_by_stage.items():
                        time_data.append({
                            "Etapa": stage.upper(),
                            "Tempo Médio (s)": f"{avg_time:.2f}"
                        })
                    
                    df_time = pd.DataFrame(time_data)
                    st.dataframe(
                        df_time,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Nenhuma métrica de tempo disponível ainda.")
                
                st.markdown("---")
                
                # Transições de etapa
                st.markdown("### 🔄 Transições entre Etapas")
                transitions = metrics.get("stage_transitions", {})
                
                if transitions:
                    transitions_data = []
                    for transition, count in sorted(transitions.items(), key=lambda x: x[1], reverse=True):
                        transitions_data.append({
                            "Transição": transition,
                            "Ocorrências": count
                        })
                    
                    df_transitions = pd.DataFrame(transitions_data)
                    st.dataframe(
                        df_transitions,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Nenhuma métrica de transição disponível ainda.")
                
                # Informações detalhadas (expandível)
                with st.expander("🔍 Dados Completos (JSON)", expanded=False):
                    st.json(metrics)
            
            else:
                st.warning("⚠️ Métricas não disponíveis")
                st.info("""
                Certifique-se de que:
                1. O Swarm Orchestrator está ativo
                2. `USE_SWARM=true` está configurado no arquivo `.env`
                3. O servidor está rodando corretamente
                """)
        
        except httpx.ConnectError:
            st.error("❌ Erro de conexão ao buscar métricas")
            st.info("Verifique se o servidor está rodando.")
        except httpx.TimeoutException:
            st.error("⏱️ Timeout ao buscar métricas")
        except Exception as e:
            st.error(f"❌ Erro ao buscar métricas: {str(e)}")
            st.info("Métricas disponíveis apenas quando usando Swarm Orchestrator (USE_SWARM=true)")
