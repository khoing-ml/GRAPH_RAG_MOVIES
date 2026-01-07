#!/usr/bin/env python3
"""Check Qdrant database status"""

from src.vector_db import QdrantService

def main():
    print("=== Checking Qdrant Database ===\n")
    
    qdrant = QdrantService()
    
    # List all collections
    collections = qdrant.client.get_collections()
    
    print("Collections:")
    if collections.collections:
        for col in collections.collections:
            print(f"  - {col.name}")
            # Get collection info
            info = qdrant.client.get_collection(col.name)
            print(f"    Points: {info.points_count}")
            print(f"    Vector size: {info.config.params.vectors.size}")
            print(f"    Distance: {info.config.params.vectors.distance}")
            print()
    else:
        print("  (No collections found!)")
        print("\n⚠️  Qdrant database is empty!")
        print("Need to run: python crawl_movies.py or python src/ingest.py")

if __name__ == "__main__":
    main()
