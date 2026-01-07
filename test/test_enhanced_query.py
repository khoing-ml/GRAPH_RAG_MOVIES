"""
Test script for enhanced query processing features
Demonstrates: validation, caching, confidence scoring, query rewriting
"""

from src.query_processor import QueryProcessor
from src.llm_service import GeminiService

def test_query_processing():
    """Test enhanced query processing features"""
    
    print("=" * 80)
    print("🧪 TESTING ENHANCED QUERY PROCESSOR")
    print("=" * 80)
    
    llm = GeminiService()
    processor = QueryProcessor(llm)
    
    # Test queries
    test_queries = [
        "Phim hành động của Christopher Nolan",
        "phim   có    nhiều   khoảng trắng   ",  # Test cleaning
        "Gợi ý phim tình cảm hay năm 2020",
        "Phim hành động của Christopher Nolan",  # Duplicate - should hit cache
        "kh",  # Short query - should be rewritten
        "",  # Invalid
        "Tìm phim giống Inception",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"Test {i}: \"{query}\"")
        print('─' * 80)
        
        result = processor.process_query(query, use_cache=True)
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
            continue
        
        # Display results
        print(f"\n📊 Results:")
        print(f"  • Original: {result['original_query']}")
        print(f"  • Cleaned: {result['cleaned_query']}")
        print(f"  • Confidence: {result['confidence']:.2f}")
        print(f"  • Processing Time: {result['processing_time']:.1f}ms")
        print(f"  • Cached: {'✅ Yes' if result['cached'] else '❌ No'}")
        
        if result.get('rewritten_query'):
            print(f"  • Rewritten: {result['rewritten_query']}")
        
        print(f"\n🏷️ Entities ({len(result['entities'])}):")
        for entity in result['entities'][:5]:
            print(f"  • {entity['text']} ({entity['type']}) - confidence: {entity['confidence']:.2f}")
        
        print(f"\n🔗 Relations ({len(result['relations'])}):")
        for relation in result['relations']:
            print(f"  • {relation['type']} - confidence: {relation['confidence']:.2f}")
        
        print(f"\n📈 Expanded Terms ({len(result['expanded_terms'])}):")
        print(f"  {', '.join(result['expanded_terms'][:10])}")
    
    # Show statistics
    print(f"\n{'=' * 80}")
    print("📊 PROCESSING STATISTICS")
    print("=" * 80)
    
    stats = processor.get_stats()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    print("\n✅ Testing complete!")


def test_query_enhancement():
    """Test query enhancement for search"""
    
    print("\n" + "=" * 80)
    print("🔍 TESTING QUERY ENHANCEMENT")
    print("=" * 80)
    
    llm = GeminiService()
    processor = QueryProcessor(llm)
    
    test_cases = [
        "Phim hành động hay",
        "Christopher Nolan",
        "Phim tình cảm 2020",
    ]
    
    for query in test_cases:
        print(f"\n{'─' * 80}")
        print(f"Original: \"{query}\"")
        
        processed = processor.process_query(query)
        enhanced = processor.enhance_search_query(query, processed)
        
        print(f"Enhanced: \"{enhanced}\"")
        print(f"Length: {len(query)} → {len(enhanced)} characters")


if __name__ == "__main__":
    test_query_processing()
    test_query_enhancement()
