"""
Simple RAG Pipeline (Baseline) - Vector Search Only
No Graph Database enrichment for comparison with GraphRAG
"""

from .llm_service import GeminiService
from .vector_db import QdrantService

class SimpleRAG:
    """Baseline RAG using only Vector Database (no Graph enrichment)"""
    
    def __init__(self):
        self.llm = GeminiService()
        self.vectordb = QdrantService()
        self.system_name = "SimpleRAG (Vector Only)"
    
    def query(self, user_question, chat_history=None):
        """Process query using only vector search, no graph enrichment"""
        print(f"\n🔎 [SimpleRAG] Processing: '{user_question}'...")
        
        # STEP 1: Semantic Search (Vector Similarity Only)
        query_vec = self.llm.get_embedding(user_question, task_type="retrieval_query")
        
        if not query_vec:
            return "Sorry, the system is busy and unable to create vectors."
        
        search_results = self.vectordb.search(query_vec, top_k=6)
        
        # RELEVANCE FILTERING (same as GraphRAG for fair comparison)
        # NOTE: Current database has low scores (0.04-0.12 range)
        RELEVANCE_THRESHOLD = 0.08  # Lowered from 0.45 due to embedding issues
        
        if search_results:
            relevant_results = [
                item for item in search_results 
                if (item.score if hasattr(item, 'score') else 0) >= RELEVANCE_THRESHOLD
            ]
            
            if relevant_results:
                print(f"  ✓ Found {len(relevant_results)}/{len(search_results)} relevant matches")
                search_results = relevant_results
            else:
                print(f"  ⚠️ No results above threshold - using general knowledge")
                search_results = []
        
        if not search_results:
            print("💡 No relevant matches — using general knowledge...")
            answer = self.llm.generate_answer("", user_question, context_provided=False, chat_history=chat_history)
            return answer
        
        # STEP 2: Build Simple Context (No Graph Enrichment)
        # Just use basic info from vector search payload
        print(f"📄 Building simple context from vector results...")
        
        context_parts = []
        for i, item in enumerate(search_results[:5], 1):
            payload = item.payload if hasattr(item, 'payload') else item
            
            title = payload.get('title', 'Unknown')
            year = payload.get('year', '')
            overview = payload.get('overview', '')
            genres = payload.get('genres', [])
            directors = payload.get('directors', [])  # Extract directors from payload
            cast = payload.get('cast', [])  # Extract cast from payload
            keywords = payload.get('keywords', [])  # Extract keywords
            
            # Build simple context with directors and cast information
            movie_info = f"{i}. {title}"
            if year:
                movie_info += f" ({year})"
            if directors:
                movie_info += f"\n   Director: {', '.join(directors)}"
            if cast:
                movie_info += f"\n   Cast: {', '.join(cast[:8])}"  # Top 8 cast members
            if genres:
                movie_info += f"\n   Genres: {', '.join(genres[:3])}"
            if keywords:
                movie_info += f"\n   Keywords: {', '.join(keywords[:5])}"
            if overview:
                movie_info += f"\n   Overview: {overview[:200]}..."
            
            context_parts.append(movie_info)
        
        simple_context = "\n\n".join(context_parts)
        
        # STEP 3: LLM Response Generation (same as GraphRAG)
        print("🤖 Generating response...")
        answer = self.llm.generate_answer(
            simple_context, 
            user_question, 
            context_provided=True, 
            chat_history=chat_history
        )
        return answer
    
    def close(self):
        """Cleanup (SimpleRAG doesn't have graph connection)"""
        pass
