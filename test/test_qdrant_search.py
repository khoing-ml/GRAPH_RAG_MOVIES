#!/usr/bin/env python3
"""Test Qdrant search directly"""

from src.vector_db import QdrantService
from src.llm_service import GeminiService

def main():
    print("=== Testing Qdrant Search ===\n")
    
    llm = GeminiService()
    qdrant = QdrantService()
    
    print(f"Collection: {qdrant.collection_name}")
    
    # Test search
    queries = [
        "action movie",
        "Avatar lửa và tro tàn",
        "phim ảo thuật gia",
    ]
    
    for query in queries:
        print(f"\n--- Query: {query} ---")
        vec = llm.get_embedding(query, "retrieval_query")
        print(f"Vector dimension: {len(vec)}")
        
        results = qdrant.search(vec, top_k=3)
        print(f"Found {len(results)} results")
        
        for i, item in enumerate(results, 1):
            score = item.score
            title = item.payload.get('title', 'No title')
            print(f"{i}. Score: {score:.4f} - {title}")

if __name__ == "__main__":
    main()
