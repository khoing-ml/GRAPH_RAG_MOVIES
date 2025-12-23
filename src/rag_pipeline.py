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
        # Tìm các phim có ý nghĩa tương đồng
        query_vec = self.llm.get_embedding(user_question, task_type="retrieval_query")
        
        if not query_vec:
            return "Xin lỗi, hệ thống đang bận, không thể tạo vector."

        search_results = self.vectordb.search(query_vec, top_k=4) # Lấy top 4
        
        if not search_results:
            # Nếu không tìm thấy kết quả trong Vector DB, cho phép LLM dùng kiến thức chung
            # để đưa ra gợi ý thay vì trả về ngay một thông báo lỗi.
            print("⚠️ Không tìm thấy kết quả trong Vector DB — chuyển sang LLM để gợi ý dựa trên kiến thức chung.")
            answer = self.llm.generate_answer("", user_question, context_provided=False, ask_followups=True)
            return answer

        # Lấy ra danh sách ID phim tìm được (payload key: movie_id)
        found_ids = []
        for hit in search_results:
            payload = getattr(hit, 'payload', {})
            mid = payload.get('movie_id') or payload.get('tmdb_id') or payload.get('id')
            if mid:
                found_ids.append(mid)
        print(f"✅ Vector DB tìm thấy {len(found_ids)} phim tiềm năng.")

        # BƯỚC 2: Truy vấn Graph (Context Enrichment)
        # Dùng ID để lấy thêm thông tin cấu trúc (Đạo diễn, Diễn viên, quan hệ...)
        print("🕸️  Đang truy vấn Graph Database...")
        graph_context = self.graphdb.get_graph_context(found_ids)
        
        if not graph_context:
            graph_context = "Không tìm thấy thông tin chi tiết trong Graph DB."

        # BƯỚC 3: Tổng hợp câu trả lời bằng LLM
        print("🤖 Đang tổng hợp câu trả lời...")
        context_provided = bool(graph_context and graph_context.strip())
        answer = self.llm.generate_answer(graph_context, user_question, context_provided=context_provided, ask_followups=True)
        return answer

    def close(self):
        self.graphdb.close()