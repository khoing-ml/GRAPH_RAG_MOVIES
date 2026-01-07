"""
Test the fallback mechanism in GraphRAG
"""
from src.rag_pipeline import GraphRAG

def test_fallback():
    print("=" * 80)
    print("Testing Fallback Mechanism")
    print("=" * 80)
    
    # Initialize with fallback enabled
    rag = GraphRAG(enable_fallback=True)
    
    # Test cases
    test_queries = [
        # Case 1: Should find in database
        "What are some good sci-fi movies?",
        
        # Case 2: Probably not in database - should fallback
        "Which actors have won Academy Awards in different decades and how did their roles evolve?",
        
        # Case 3: General movie knowledge - may fallback
        "What is method acting and which actors are known for it?",
        
        # Case 4: Very specific to database
        "Tell me about movies directed by Christopher Nolan",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}: {query}")
        print('=' * 80)
        
        answer = rag.query(query)
        
        print(f"\n📝 Answer:\n{answer}\n")
        print(f"🔍 Method used: {rag.get_last_method()}")
        print(f"📊 Contexts: {len(rag.last_contexts)}")
        
        input("\nPress Enter for next test...")
    
    print("\n" + "=" * 80)
    print("Testing Complete!")
    print("=" * 80)
    
    # Show stats
    stats = rag.get_query_stats()
    print("\n📊 Final Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    rag.close()

if __name__ == "__main__":
    test_fallback()
