from .llm_service import GeminiService
from .vector_db import QdrantService
from .graph_db import Neo4jService

class GraphRAG:
    def __init__(self):
        self.llm = GeminiService()
        self.vectordb = QdrantService()
        self.graphdb = Neo4jService()

    def query(self, user_question, chat_history=None):
        print(f"\n🔎 Understanding: '{user_question}'...")
        
        # STEP 1: Semantic Search (Vector Similarity)
        # Find movies with similar themes, plots, and descriptions
        query_vec = self.llm.get_embedding(user_question, task_type="retrieval_query")
        
        if not query_vec:
            return "Xin lỗi, hệ thống đang bận, không thể tạo vector."

        search_results = self.vectordb.search(query_vec, top_k=6)  # Get top 6 for better context
        
        if not search_results:
            # If no Vector DB results, let LLM use general knowledge
            # Rather than failing, provide general recommendations
            print("⚠️ No database matches found — using general film knowledge...")
            answer = self.llm.generate_answer("", user_question, context_provided=False, chat_history=chat_history)
            return answer

        # Extract movie IDs from vector search results
        found_ids = []
        for hit in search_results:
            payload = getattr(hit, 'payload', {})
            mid = payload.get('movie_id') or payload.get('tmdb_id') or payload.get('id')
            if mid:
                found_ids.append(mid)
        print(f"✅ Found {len(found_ids)} relevant movies in database")

        # STEP 2: Graph Database Enrichment
        # Use IDs to fetch enriched context: director, cast, relationships, genres, themes
        print("🕸️  Enriching with detailed information...")
        graph_context = self.graphdb.get_graph_context(found_ids)
        
        if not graph_context:
            # Even if graph enrichment fails, use basic vector results
            # Create basic context from the search
            graph_context = "Movies found but detailed info unavailable."

        # STEP 3: LLM Response Generation
        # Synthesize answer with conversational, engaging tone
        print("🤖 Generating thoughtful response...")
        context_provided = bool(graph_context and graph_context.strip() and "unavailable" not in graph_context.lower())
        answer = self.llm.generate_answer(graph_context, user_question, context_provided=context_provided, chat_history=chat_history)
        return answer

    def close(self):
        self.graphdb.close()