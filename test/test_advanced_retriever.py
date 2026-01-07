"""
Demo: Test Advanced Retriever
Compare basic retrieval vs advanced hybrid retrieval
"""

from src.advanced_retriever import create_advanced_retriever
from src.llm_service import GeminiService
from src.vector_db import QdrantService
from src.graph_db import Neo4jService


def test_basic_vs_advanced():
    """Compare basic and advanced retrieval"""
    
    print("="*80)
    print("Advanced Retriever Demo")
    print("="*80)
    
    # Initialize services
    print("\n🚀 Initializing services...")
    llm = GeminiService()
    vectordb = QdrantService()
    graphdb = Neo4jService()
    
    # Create advanced retriever
    advanced_retriever = create_advanced_retriever(llm, vectordb, graphdb)
    
    # Test queries
    test_queries = [
        {
            "query": "Christopher Nolan đạo diễn phim nào?",
            "category": "director_filmography",
            "description": "Director filmography - needs entity linking"
        },
        {
            "query": "Phim nào giống The Shawshank Redemption?",
            "category": "similarity_search",
            "description": "Similarity search - needs vector + graph"
        },
        {
            "query": "Phim kinh dị hay nhất?",
            "category": "genre_recommendation",
            "description": "Genre recommendation - entity linking + traversal"
        },
        {
            "query": "Tom Hanks và Steven Spielberg hợp tác phim gì?",
            "category": "comparison",
            "description": "Complex reasoning - multi-entity linking"
        }
    ]
    
    print("\n" + "="*80)
    print("Testing Advanced Retrieval on Multiple Queries")
    print("="*80)
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}/{len(test_queries)}")
        print(f"Query: {test_case['query']}")
        print(f"Category: {test_case['category']}")
        print(f"Description: {test_case['description']}")
        print(f"{'='*80}")
        
        # Run advanced retrieval
        query_metadata = {
            'category': test_case['category']
        }
        
        results = advanced_retriever.retrieve(
            test_case['query'],
            query_metadata=query_metadata,
            top_k_vector=5
        )
        
        # Display results
        print(f"\n📊 Retrieval Summary:")
        print(f"  Method: {results['method']}")
        print(f"  Vector results: {results['vector_count']}")
        print(f"  Graph results: {results['graph_count']}")
        print(f"  Linked entities: {results['linked_entities']}")
        print(f"  Retrieval depth: {results['retrieval_depth']} hops")
        print(f"  Total contexts: {len(results['contexts'])}")
        
        print(f"\n📝 Retrieved Contexts:")
        for j, context in enumerate(results['contexts'][:10], 1):
            print(f"  {j}. {context[:150]}...")
        
        print()
    
    print("\n" + "="*80)
    print("✅ Demo completed!")
    print("="*80)


if __name__ == "__main__":
    test_basic_vs_advanced()
