import streamlit as st
import time
from src.rag_pipeline import GraphRAG
from src import ingest
from src.ui_helpers import render_chat_messages, inject_gemini_styles
from datetime import datetime


@st.cache_resource
def initialize_graph_rag():
    try:
        return GraphRAG()
    except Exception as e:
        st.error(f"❌ Lỗi khởi tạo hệ thống: {e}")
        st.stop()


st.set_page_config(page_title="Movie GraphRAG", layout="centered", initial_sidebar_state="collapsed")

# Initialize session state
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []

if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = True

rag = initialize_graph_rag()

# Inject Gemini-like styles
inject_gemini_styles()

# Sidebar menu (hidden by default, accessible via menu)
with st.sidebar:
    st.header("⚙️ Settings")
    st.checkbox("Dark mode", value=st.session_state.get('dark_mode', True), key='dark_mode')
    
    st.markdown("---")
    st.header("🔧 Tools")
    if st.button("🔄 Run Ingestion"):
        with st.spinner("Running ingestion..."):
            try:
                ingest.run_ingestion()
                st.success("✅ Ingestion finished")
            except Exception as e:
                st.error(f"❌ Ingestion error: {e}")

    if st.button("🔨 Fix Vector Dimension"):
        with st.spinner("Checking collection..."):
            try:
                from fix_vector_dimension import fix_dimension
                fix_dimension()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state['chat_messages'] = []
        st.rerun()


# Main centered chat container
container = st.container()

with container:
    # If no messages, show greeting and action buttons
    if len(st.session_state['chat_messages']) == 0:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px 40px;">
            <div style="font-size: 48px; margin-bottom: 16px;">🎬</div>
            <h1 style="font-size: 40px; margin: 0 0 16px 0; font-weight: 600;">Hi Khoi</h1>
            <p style="font-size: 24px; margin: 0 0 40px 0; color: rgba(255,255,255,0.6);">What movie shall we find today?</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 0 auto 60px; max-width: 600px;">
            <div class="action-btn" style="text-align: center; padding: 16px; border-radius: 12px; background: rgba(255,255,255,0.05); cursor: pointer; border: 1px solid rgba(255,255,255,0.1); transition: all 0.2s;">
                🎯 Action Films
            </div>
            <div class="action-btn" style="text-align: center; padding: 16px; border-radius: 12px; background: rgba(255,255,255,0.05); cursor: pointer; border: 1px solid rgba(255,255,255,0.1); transition: all 0.2s;">
                😂 Comedy
            </div>
            <div class="action-btn" style="text-align: center; padding: 16px; border-radius: 12px; background: rgba(255,255,255,0.05); cursor: pointer; border: 1px solid rgba(255,255,255,0.1); transition: all 0.2s;">
                💔 Drama
            </div>
            <div class="action-btn" style="text-align: center; padding: 16px; border-radius: 12px; background: rgba(255,255,255,0.05); cursor: pointer; border: 1px solid rgba(255,255,255,0.1); transition: all 0.2s;">
                👻 Horror
            </div>
            <div class="action-btn" style="text-align: center; padding: 16px; border-radius: 12px; background: rgba(255,255,255,0.05); cursor: pointer; border: 1px solid rgba(255,255,255,0.1); transition: all 0.2s;">
                🚀 Sci-Fi
            </div>
            <div class="action-btn" style="text-align: center; padding: 16px; border-radius: 12px; background: rgba(255,255,255,0.05); cursor: pointer; border: 1px solid rgba(255,255,255,0.1); transition: all 0.2s;">
                🎪 More
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show chat messages
        render_chat_messages(st.session_state['chat_messages'])

# Chat input at the bottom (sticky)
st.markdown("""
<style>
    .chat-input-container {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 800px;
        z-index: 100;
    }
</style>
<div class="chat-input-container">
</div>
""", unsafe_allow_html=True)

with st.form(key='chat_form', clear_on_submit=True):
    cols = st.columns([1, 12, 1])
    with cols[1]:
        user_input = st.text_area(
            "Ask about movies...",
            label_visibility='collapsed',
            placeholder="Ask me about movies, recommendations, plots, cast...",
            key='chat_input',
            height=50
        )
    
    with cols[2]:
        submitted = st.form_submit_button("⏎", help="Send message")

if submitted and user_input and user_input.strip():
    # Add user message
    usr_msg = {
        "role": "user",
        "content": user_input.strip(),
        "time": datetime.now().isoformat()
    }
    st.session_state['chat_messages'].append(usr_msg)
    
    # Get assistant response with conversation history
    with st.spinner("🤔 Thinking..."):
        try:
            answer = rag.query(user_input.strip(), chat_history=st.session_state['chat_messages'][:-1])
        except Exception as e:
            answer = f"Sorry, I encountered an error: {e}"
    
    # Add assistant message
    assistant_msg = {
        "role": "assistant",
        "content": answer,
        "time": datetime.now().isoformat()
    }
    st.session_state['chat_messages'].append(assistant_msg)
    st.rerun()