"""
Test RAG Pipeline với Movies data trên cloud
"""
from src.llm_service import GeminiService
from src.vector_db import QdrantService
from src.graph_db import Neo4jService

def test_movie_rag():
    print("="*60)
    print("🎬 TEST MOVIE RAG PIPELINE")
    print("="*60)
    
    # Khởi tạo services
    llm = GeminiService()
    vectordb = QdrantService()
    graphdb = Neo4jService()
    
    # Test query
    test_query = "Tìm phim hành động về siêu anh hùng trong đó có một siêu anh hùng Marvel là người thường và bộ phim có đánh giá cao từ khán giả và ra mắt từ 2010 đến nay."
    print(f"\n🔍 Query: {test_query}\n")
    
    # BƯỚC 1: Vector Search
    print("1️⃣  Vector Search...")
    query_vec = llm.get_embedding(test_query, task_type="retrieval_query")
    
    if not query_vec:
        print("❌ Không thể tạo vector")
        return
    
    search_results = vectordb.search(query_vec, top_k=5)
    
    if not search_results:
        print("❌ Không tìm thấy kết quả")
        return
    
    print(f"   ✅ Tìm thấy {len(search_results)} movies:")
    movie_ids = []
    for i, hit in enumerate(search_results, 1):
        payload = hit.payload
        score = hit.score
        print(f"      {i}. {payload.get('title', 'N/A')} ({payload.get('year', 'N/A')}) - Score: {score:.3f}")
        print(f"         Genres: {', '.join(payload.get('genres', []))}")
        movie_ids.append(payload.get('tmdb_id'))
    
    # BƯỚC 2: Graph Query
    print(f"\n2️⃣  Graph Database Query...")
    try:
        with graphdb.driver.session() as session:
            # Query lấy thông tin chi tiết từ graph
            query = """
            MATCH (m:Movie) WHERE m.id IN $movie_ids
            OPTIONAL MATCH (m)-[:BELONGS_TO]->(g:Genre)
            OPTIONAL MATCH (d:Person)-[:DIRECTED]->(m)
            OPTIONAL MATCH (a:Person)-[:ACTED_IN]->(m)
            
            RETURN m.title as title,
                   m.year as year,
                   m.rating as rating,
                   m.overview as overview,
                   collect(DISTINCT g.name) as genres,
                   collect(DISTINCT d.name)[0] as director,
                   collect(DISTINCT a.name)[0..3] as top_cast
            LIMIT 5
            """
            
            results = session.run(query, movie_ids=movie_ids)
            
            graph_context = []
            for record in results:
                info = f"""
📽️  **{record['title']}** ({record['year']}) ⭐ {record['rating']}/10
   Đạo diễn: {record['director'] or 'N/A'}
   Diễn viên: {', '.join(record['top_cast'][:3]) if record['top_cast'] else 'N/A'}
   Thể loại: {', '.join(record['genres']) if record['genres'] else 'N/A'}
   Nội dung: {record['overview'][:150]}...
"""
                graph_context.append(info)
                print(info)
        
    except Exception as e:
        print(f"   ❌ Lỗi graph query: {e}")
        graph_context = ["Không có thông tin từ graph database"]
    
    # BƯỚC 3: LLM Generation
    print("\n3️⃣  Generating Answer...")
    context_text = "\n".join(graph_context)
    
    prompt = f"""Dựa trên thông tin các bộ phim sau và kiến thức của riêng bạn, hãy trả lời câu hỏi của người dùng:

Câu hỏi: {test_query}

Thông tin phim không bắt buộc dựa trên đây (có thể tự đưa ra lý luận):
{context_text}

Có thể sử dụng thêm tri thức của riêng bạn hoặc tìm kiếm trên mạng để cung cấp câu trả lời tốt nhất.

Trả lời chi tiết và hữu ích cho người dùng."""
    
    answer = llm.generate_answer(context_text, test_query)
    print(f"\n🤖 **Gemini's Answer:**\n{answer}")
    
    graphdb.close()
    print("\n" + "="*60)

if __name__ == "__main__":
    test_movie_rag()
