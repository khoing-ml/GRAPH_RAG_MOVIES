"""Quick test to check if Neo4j graph enrichment returns director/cast info"""

from src.graph_db import Neo4jService

# Test with known Christopher Nolan movie IDs
test_movie_ids = [
    155,    # The Dark Knight
    49026,  # The Dark Knight Rises  
    27205,  # Inception
    157336, # Interstellar
    272,    # Batman Begins
]

print("🧪 Testing Neo4j Graph Context Retrieval\n")
print("="*80)

graph_db = Neo4jService()
context = graph_db.get_graph_context(test_movie_ids)

print("📊 RAW CONTEXT FROM GRAPH_DB:\n")
print(context)
print("\n" + "="*80)

# Check if director and cast are in the context
if "Director:" in context:
    print("\n✅ Director information FOUND in context")
else:
    print("\n❌ Director information MISSING from context")

if "Starring:" in context or "Cast:" in context:
    print("✅ Cast information FOUND in context")
else:
    print("❌ Cast information MISSING from context")

graph_db.close()
