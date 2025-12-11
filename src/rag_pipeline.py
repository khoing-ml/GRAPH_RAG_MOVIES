from .llm_service import GeminiService
from .vector_db import QdrantService
from .graph_db import Neo4jService

class GraphRAG:
    def __init__(self):
        self.llm = GeminiService()
        self.vectordb = QdrantService()
        self.graphdb = Neo4jService()

    def query(self, user_question):
        print(f"\n🔎 Đang phân tích câu hỏi: '{user_question}'...")
        
        # BƯỚC 1: Tìm kiếm Vector (Semantic Search)
        # Tìm các đoạn tóm tắt sách có ý nghĩa tương đồng
        query_vec = self.llm.get_embedding(user_question, task_type="retrieval_query")
        
        if not query_vec:
            return "Xin lỗi, hệ thống đang bận, không thể tạo vector."

        search_results = self.vectordb.search(query_vec, top_k=4) # Lấy top 4
        
        if not search_results:
            return "Rất tiếc, tôi không tìm thấy cuốn sách nào phù hợp trong cơ sở dữ liệu."

        # Lấy ra danh sách ID sách tìm được
        found_ids = [hit.payload['book_id'] for hit in search_results]
        print(f"✅ Vector DB tìm thấy {len(found_ids)} sách tiềm năng.")

        # BƯỚC 2: Truy vấn Graph (Context Enrichment)
        # Dùng ID để lấy thêm thông tin cấu trúc (Tác giả, quan hệ...)
        print("🕸️  Đang truy vấn Graph Database...")
        graph_context = self.graphdb.get_graph_context(found_ids)
        
        if not graph_context:
            graph_context = "Không tìm thấy thông tin chi tiết trong Graph DB."

        # BƯỚC 3: Tổng hợp câu trả lời bằng LLM
        print("🤖 Đang tổng hợp câu trả lời...")
        answer = self.llm.generate_answer(graph_context, user_question)
        return answer

    def close(self):
        self.graphdb.close()