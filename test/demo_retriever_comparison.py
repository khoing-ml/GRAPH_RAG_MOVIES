"""
Demo: Compare Basic GraphRAG vs Advanced GraphRAG
Shows difference between basic vector retrieval and hybrid neural+symbolic retrieval
"""

from src.rag_pipeline import GraphRAG
import time


def compare_retrievers():
    """Compare basic and advanced retrievers side by side"""
    
    print("="*80)
    print("GraphRAG Retriever Comparison Demo")
    print("Basic (Vector Only) vs Advanced (Hybrid Neural+Symbolic)")
    print("="*80)
    
    # Test queries
    test_queries = [
        {
            "query": "Christopher Nolan đạo diễn phim nào?",
            "description": "Director filmography query - needs entity linking"
        },
        {
            "query": "Phim nào giống The Shawshank Redemption?",
            "description": "Similarity search - benefits from graph traversal"
        },
        {
            "query": "Tom Hanks và Meg Ryan đóng chung phim gì?",
            "description": "Multi-entity relationship query"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}/{len(test_queries)}")
        print(f"Query: {test_case['query']}")
        print(f"Description: {test_case['description']}")
        print(f"{'='*80}")
        
        # Test with Basic Retriever
        print(f"\n{'─'*80}")
        print("🔵 BASIC GRAPHRAG (Vector Search Only)")
        print(f"{'─'*80}")
        
        basic_rag = GraphRAG(use_advanced_retriever=False)
        
        start_time = time.time()
        basic_answer = basic_rag.query(test_case['query'])
        basic_time = time.time() - start_time
        
        print(f"\n📝 Basic Answer:")
        print(f"{basic_answer[:300]}...")
        print(f"⏱️  Time: {basic_time:.2f}s")
        
        # Test with Advanced Retriever
        print(f"\n{'─'*80}")
        print("🔬 ADVANCED GRAPHRAG (Hybrid Neural+Symbolic)")
        print(f"{'─'*80}")
        
        advanced_rag = GraphRAG(use_advanced_retriever=True)
        
        start_time = time.time()
        advanced_answer = advanced_rag.query(test_case['query'])
        advanced_time = time.time() - start_time
        
        print(f"\n📝 Advanced Answer:")
        print(f"{advanced_answer[:300]}...")
        print(f"⏱️  Time: {advanced_time:.2f}s")
        
        # Comparison
        print(f"\n{'─'*80}")
        print("📊 COMPARISON:")
        print(f"{'─'*80}")
        print(f"Response Time Difference: {advanced_time - basic_time:+.2f}s")
        print(f"Advanced is {'slower' if advanced_time > basic_time else 'faster'}")
        
        # Clean up
        basic_rag.close()
        advanced_rag.close()
        
        if i < len(test_queries):
            print(f"\n⏳ Waiting 3s before next test...")
            time.sleep(3)
    
    print(f"\n{'='*80}")
    print("✅ Comparison Demo Completed!")
    print(f"{'='*80}")
    
    print("\n📝 Summary:")
    print("- Basic Retriever: Fast, simple vector search")
    print("- Advanced Retriever: More intelligent, entity linking + graph traversal")
    print("- Advanced excels at: entity queries, multi-hop reasoning, disambiguation")
    print("- Basic excels at: speed, simple semantic search")


if __name__ == "__main__":
    compare_retrievers()
