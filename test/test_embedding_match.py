#!/usr/bin/env python3
"""Compare embedding search with actual data"""

from src.vector_db import QdrantService
from src.llm_service import GeminiService

def main():
    print("=== Comparing Search with Actual Data ===\n")
    
    llm = GeminiService()
    qdrant = QdrantService()
    
    # Get a sample movie from Qdrant
    print("1. Getting sample movies from Qdrant...")
    results = qdrant.client.scroll(
        collection_name="movies_vietnamese",
        limit=5
    )
    
    print("\nSample movies in Qdrant:")
    for point in results[0]:
        print(f"  - {point.payload.get('title', 'No title')}")
        print(f"    Overview: {point.payload.get('overview', 'No overview')[:80]}...")
    
    # Test search with exact title
    print("\n2. Testing search with exact title...")
    exact_title = results[0][0].payload.get('title', '')
    print(f"Searching for: '{exact_title}'")
    
    vec = llm.get_embedding(exact_title, "retrieval_query")
    search_results = qdrant.search(vec, top_k=5)
    
    print(f"\nSearch results:")
    for i, item in enumerate(search_results, 1):
        title = item.payload.get('title', 'No title')
        match = "✓ MATCH" if title == exact_title else ""
        print(f"{i}. Score: {item.score:.4f} - {title} {match}")
    
    # Test with overview keywords
    print("\n3. Testing with overview keywords...")
    overview = results[0][0].payload.get('overview', '')[:100]
    print(f"Overview keywords: '{overview}'")
    
    vec2 = llm.get_embedding(overview, "retrieval_query")
    search_results2 = qdrant.search(vec2, top_k=5)
    
    print(f"\nSearch results:")
    for i, item in enumerate(search_results2, 1):
        title = item.payload.get('title', 'No title')
        match = "✓ MATCH" if title == exact_title else ""
        print(f"{i}. Score: {item.score:.4f} - {title} {match}")

if __name__ == "__main__":
    main()
