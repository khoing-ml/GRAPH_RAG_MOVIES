"""
Test script for Query Processor
Demonstrates the 5 GraphRAG query processing techniques
"""

from src.query_processor import QueryProcessor
from src.llm_service import GeminiService
import json

def test_query_processor():
    print("=" * 80)
    print("🧪 TESTING QUERY PROCESSOR - 5 GraphRAG Techniques")
    print("=" * 80)
    
    # Initialize
    llm = GeminiService()
    qp = QueryProcessor(llm)
    
    # Test cases covering different query types
    test_queries = [
        "Phim hành động của đạo diễn Christopher Nolan",
        "Tìm phim giống Inception năm 2010",
        "Phim có Tom Hanks đóng về chiến tranh",
        "Phim kinh dị Hàn Quốc hay và phim tình cảm lãng mạn Nhật",
        "So sánh The Dark Knight với Avengers"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST CASE {i}: {query}")
        print('=' * 80)
        
        # Process query
        result = qp.process_query(query)
        
        # Display results
        print("\n1️⃣ NAMED ENTITY RECOGNITION (NER):")
        if result['entities']:
            for entity in result['entities']:
                print(f"   • {entity['text']} [{entity['type']}] (confidence: {entity['confidence']:.2f})")
        else:
            print("   (No entities found)")
        
        print("\n2️⃣ RELATIONAL EXTRACTION (RE):")
        if result['relations']:
            for rel in result['relations']:
                print(f"   • {rel['type']} (confidence: {rel['confidence']:.2f})")
        else:
            print("   (No relations found)")
        
        print("\n3️⃣ QUERY STRUCTURATION:")
        structured = result['structured_query']
        print(f"   Operation: {structured.get('operation', 'N/A')}")
        if structured.get('nodes'):
            print(f"   Nodes: {[n['name'] for n in structured['nodes']]}")
        if structured.get('edges'):
            print(f"   Relations: {[e['type'] for e in structured['edges']]}")
        if structured.get('filters'):
            print(f"   Filters: {structured['filters']}")
        
        print("\n4️⃣ QUERY DECOMPOSITION:")
        if result['sub_queries']:
            for j, sub_q in enumerate(result['sub_queries'], 1):
                print(f"   {j}. {sub_q}")
        else:
            print("   (Simple query - no decomposition needed)")
        
        print("\n5️⃣ QUERY EXPANSION:")
        if result['expanded_terms']:
            print(f"   Added terms: {', '.join(result['expanded_terms'][:8])}")
        else:
            print("   (No expansion terms)")
        
        # Show enhanced query
        enhanced = qp.enhance_search_query(query, result)
        print(f"\n🔍 ENHANCED SEARCH QUERY:")
        print(f"   {enhanced[:150]}...")
        
        # Show generated Cypher
        cypher = qp.get_cypher_query(result)
        if cypher:
            print(f"\n📊 GENERATED CYPHER QUERY:")
            for line in cypher.split('\n'):
                print(f"   {line}")
        
        print()

def test_comparison():
    """Compare original vs enhanced query processing"""
    print("\n" + "=" * 80)
    print("📊 COMPARISON: Original vs Enhanced Query Processing")
    print("=" * 80)
    
    llm = GeminiService()
    qp = QueryProcessor(llm)
    
    query = "Phim hành động của Christopher Nolan"
    
    print(f"\n🔹 Original Query: '{query}'")
    
    # Process with new system
    processed = qp.process_query(query)
    enhanced = qp.enhance_search_query(query, processed)
    
    print(f"\n🔹 Enhanced Query: '{enhanced}'")
    
    print(f"\n📈 Improvements:")
    print(f"   • Extracted entities: {len(processed['entities'])}")
    print(f"   • Identified relations: {len(processed['relations'])}")
    print(f"   • Added search terms: {len(processed['expanded_terms'])}")
    print(f"   • Query length increase: {len(enhanced)} vs {len(query)} chars")

if __name__ == "__main__":
    try:
        test_query_processor()
        test_comparison()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
