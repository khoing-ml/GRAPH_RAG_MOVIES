import streamlit as st
from src.rag_pipeline import GraphRAG
import time
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Hàm khởi tạo và lưu trữ GraphRAG vào session state
@st.cache_resource
def initialize_graph_rag():
    """Khởi tạo GraphRAG service và cache nó."""
    try:
        rag_service = GraphRAG()
        return rag_service
    except Exception as e:
        # Nếu database chưa bật hoặc key sai
        st.error(f"❌ Lỗi khởi tạo hệ thống: {e}")
        st.stop()

# --- CẤU HÌNH GIAO DIỆN STREAMLIT ---
st.set_page_config(
    page_title="Book GraphRAG Advisor",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📚 Book Recommender (GraphRAG + Gemini)")
st.subheader("Tìm kiếm ngữ nghĩa và quan hệ giữa sách")

# Khởi tạo dịch vụ chỉ một lần
rag = initialize_graph_rag()

# --- Xử lý Lịch sử Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Chào bạn! Bạn muốn tìm sách về chủ đề gì, hoặc muốn tìm sách cùng tác giả nào?"
    })

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Xử lý Input của Người dùng ---
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    # 1. Thêm câu hỏi người dùng vào lịch sử
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Sinh câu trả lời và hiển thị
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Gọi hàm query từ service GraphRAG
        try:
            with st.spinner("🤖 Đang suy luận bằng GraphRAG..."):
                start_time = time.time()
                
                # Hàm query của chúng ta đã được thiết kế để trả về chuỗi cuối cùng
                ai_response = rag.query(prompt)
                
                end_time = time.time()
                latency = end_time - start_time

                # Hiển thị kết quả dưới dạng stream (giả lập)
                # Hoặc chỉ hiển thị một lần nếu Gemini trả về nhanh
                full_response = ai_response + f"\n\n---\n*Phản hồi trong: {latency:.2f}s*"
                
                message_placeholder.markdown(full_response)

        except Exception as e:
            full_response = f"❌ Xin lỗi, có lỗi hệ thống xảy ra: {e}"
            message_placeholder.markdown(full_response)

    # 3. Lưu câu trả lời của trợ lý vào lịch sử
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- Sidebar Thông tin ---
with st.sidebar:
    st.header("Thông tin Dự án")
    st.write("Kiến trúc: Hybrid RAG (Retrieval-Augmented Generation)")
    st.write(f"LLM: Gemini-2.5-Flash (via `src/llm_service.py`)")
    st.write(f"Vector DB: Qdrant (Cổng 6333)")
    st.write(f"Graph DB: Neo4j (Cổng 7687)")
    
    st.button("Xóa Lịch sử Chat", on_click=lambda: st.session_state.messages.clear())