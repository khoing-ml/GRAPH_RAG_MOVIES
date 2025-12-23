import streamlit as st
import time
from src.rag_pipeline import GraphRAG
from src import ingest
from src.ui_helpers import render_search_results, render_movie_detail, render_chat_messages
from datetime import datetime


@st.cache_resource
def initialize_graph_rag():
    try:
        return GraphRAG()
    except Exception as e:
        st.error(f"❌ Lỗi khởi tạo hệ thống: {e}")
        st.stop()


st.set_page_config(page_title="Movie GraphRAG", layout="wide")

st.title("🎬 Movie GraphRAG")
st.write("Tìm kiếm ngữ nghĩa và mở rộng ngữ cảnh bằng Graph + Vector + Gemini")

rag = initialize_graph_rag()

# Chat history initialization
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = [
        {"role": "assistant", "content": "Chào bạn! Tôi có thể giúp tìm phim, gợi ý hoặc trả lời câu hỏi về điện ảnh.", "time": datetime.now().isoformat()}
    ]

# Ensure dark_mode key exists before any widget creates it
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False


with st.sidebar:
    st.header("Actions")
    # Dark mode toggle (widget binds directly to `st.session_state['dark_mode']`)
    st.checkbox("Dark mode", value=st.session_state.get('dark_mode', False), key='dark_mode')
    if st.button("Run Ingestion"):
        with st.spinner("Running ingestion..."):
            try:
                ingest.run_ingestion()
                st.success("Ingestion finished (check logs)")
            except Exception as e:
                st.error(f"Ingestion error: {e}")

    if st.button("Fix Vector Dimension"):
        with st.spinner("Checking collection..."):
            try:
                from fix_vector_dimension import fix_dimension
                fix_dimension()
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.header("Info")
    st.write("LLM: Gemini (via `src/llm_service.py`)")
    st.write("Vector DB: Qdrant")
    st.write("Graph DB: Neo4j")
    st.markdown("---")
    st.write("Tip: Use the chat input to ask for movie recommendations or details.")


# Main layout: center chat + right panels
left_col, center_col, right_col = st.columns([1, 3, 1])

with center_col:
    st.markdown("### Chat")
    # render messages
    render_chat_messages(st.session_state['chat_messages'])

    # Input form at bottom
    with st.form(key='chat_form', clear_on_submit=True):
        user_input = st.text_area("Message", label_visibility='collapsed', placeholder="Hỏi về phim, ví dụ: 'Phim hành động siêu anh hùng hay nào?'", key='chat_input', height=80)
        submitted = st.form_submit_button("Send")

    if submitted and user_input and user_input.strip():
        # append user message
        usr_msg = {"role": "user", "content": user_input.strip(), "time": datetime.now().isoformat()}
        st.session_state['chat_messages'].append(usr_msg)
        # rerender quickly
        render_chat_messages(st.session_state['chat_messages'])

        # get assistant response (blocking for now)
        with st.spinner("Đang suy luận..."):
            try:
                answer = rag.query(user_input.strip())
            except Exception as e:
                answer = f"Lỗi khi truy vấn: {e}"

        assistant_msg = {"role": "assistant", "content": answer, "time": datetime.now().isoformat()}
        st.session_state['chat_messages'].append(assistant_msg)
        render_chat_messages(st.session_state['chat_messages'])

with right_col:
    st.subheader("Quick Actions")
    st.write("Bạn có thể: tìm kiếm, xem kết quả, hoặc chọn film để xem chi tiết.")
    if 'last_results' in st.session_state:
        st.markdown("**Last results**")
        _ = render_search_results(st.session_state['last_results'])
    if 'selected_id' in st.session_state:
        st.markdown("**Selected**")
        try:
            ctx = rag.graphdb.get_graph_context([st.session_state['selected_id']])
            render_movie_detail({'title': f"Movie {st.session_state['selected_id']}", 'overview': ctx})
        except Exception:
            st.write("Không thể lấy chi tiết.")