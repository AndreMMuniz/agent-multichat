import streamlit as st
import requests
import uuid

# Configuration
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Agent Multichat Debugger", page_icon="🤖", layout="wide")

st.title("🤖 Agent Multichat - Advanced Features Demo")

# Sidebar for Context
with st.sidebar:
    st.header("🔧 Configuração")
    
    # User Identification
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())[:8]
    
    user_id = st.text_input("User ID", value=st.session_state.user_id)
    st.session_state.user_id = user_id
    
    # Channel Selection
    channel = st.selectbox(
        "Canal de Origem",
        ["whatsapp", "telegram", "email", "web_widget"],
        index=0,
        help="Diferentes canais terão estilos de resposta diferentes"
    )
    
    st.divider()
    
    # User Profile Viewer
    st.subheader("👤 Perfil do Usuário")
    try:
        profile_response = requests.get(f"{API_URL}/user-profile/{user_id}")
        if profile_response.status_code == 200 and profile_response.json():
            profile_data = profile_response.json()
            if profile_data.get('name'):
                st.success(f"**Nome:** {profile_data['name']}")
            else:
                st.info("Nome ainda não fornecido")
            
            st.caption(f"Primeiro contato: {'Sim' if profile_data.get('is_first_contact') else 'Não'}")
        else:
            st.info("Perfil será criado no primeiro contato")
    except:
        st.caption("Erro ao carregar perfil")
    
    st.divider()
    
    # User Context Viewer
    st.subheader("📚 Memória de Longo Prazo")
    if st.button("Ver Contexto do Usuário"):
        try:
            response = requests.get(f"{API_URL}/user-context/{channel}/{user_id}")
            if response.status_code == 200 and response.json():
                context_data = response.json()
                st.success(f"Conversas: {context_data['conversation_count']}")
                with st.expander("Ver Resumo Completo"):
                    st.text(context_data['context_summary'])
            else:
                st.info("Nenhum contexto salvo ainda")
        except:
            st.error("Erro ao carregar contexto")
    
    st.divider()
    
    if st.button("Limpar Histórico Local"):
        st.session_state.messages = []
        st.session_state.pending_action = None
        st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

# Check for pending actions
try:
    pending_response = requests.get(f"{API_URL}/pending-actions/{channel}/{user_id}")
    if pending_response.status_code == 200:
        pending_actions = pending_response.json()
        if pending_actions and not st.session_state.pending_action:
            st.session_state.pending_action = pending_actions[0]
except:
    pass

# Display pending action banner
if st.session_state.pending_action:
    action = st.session_state.pending_action
    
    st.warning(f"⚠️ **Ação Pendente de Aprovação**")
    st.info(f"**Tipo:** {action['action_type']}")
    st.info(f"**Descrição:** {action['action_description']}")
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        if st.button("✅ Aprovar", type="primary"):
            try:
                approve_response = requests.post(
                    f"{API_URL}/approve-action/{action['id']}",
                    json={"approved": True}
                )
                if approve_response.status_code == 200:
                    result = approve_response.json()
                    st.success("Ação aprovada e executada!")
                    
                    # Add response to chat
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result.get("response", "Ação executada com sucesso")
                    })
                    
                    st.session_state.pending_action = None
                    st.rerun()
                else:
                    st.error(f"Erro ao aprovar: {approve_response.status_code} - {approve_response.text}")
            except Exception as e:
                st.error(f"Erro ao aprovar: {e}")
    
    with col2:
        if st.button("❌ Rejeitar", type="secondary"):
            try:
                reject_response = requests.post(
                    f"{API_URL}/approve-action/{action['id']}",
                    json={"approved": False}
                )
                if reject_response.status_code == 200:
                    result = reject_response.json()
                    st.info("Ação rejeitada")
                    
                    # Display the agent's response (Rejection Message)
                    agent_msg = result.get("response", "❌ Solicitação rejeitada pelo gerente.")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": agent_msg
                    })
                    
                    st.session_state.pending_action = None
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao rejeitar: {e}")
    
    st.divider()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Digite sua mensagem..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Send to Backend
    payload = {
        "channel": channel,
        "user_identifier": user_id,
        "content": prompt
    }
    
    try:
        with st.spinner('Processando...'):
            response = requests.post(f"{API_URL}/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status == "pending_approval":
                    # HITL: Action requires approval
                    st.session_state.pending_action = {
                        "id": data.get("pending_action_id"),
                        "action_type": "critical_action",
                        "action_description": data.get("action_description")
                    }
                    
                    with st.chat_message("assistant"):
                        st.warning("⚠️ Esta ação requer aprovação humana. Por favor, revise acima.")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "⚠️ Ação crítica detectada. Aguardando aprovação..."
                    })
                    
                    st.rerun()
                    
                elif status == "completed":
                    # Normal response
                    bot_response = data.get("response", "Sem resposta do agente.")
                    
                    # Display assistant response in chat message container
                    with st.chat_message("assistant"):
                        st.markdown(bot_response)
                        
                        # Optional: Show debug info
                        with st.expander("Detalhes Técnicos"):
                            st.json(data)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                else:
                    st.error(f"Status desconhecido: {status}")
            else:
                st.error(f"Erro na API: {response.status_code} - {response.text}")
                
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend. Verifique se ele está rodando em http://127.0.0.1:8000")

# Footer with feature indicators
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("✅ Human-in-the-Loop")
with col2:
    st.caption("✅ Memória de Longo Prazo")
with col3:
    st.caption(f"✅ Omnichannel ({channel})")
