"""
Test script for integrated ground truth loading
Checks if the test_datasets/ are properly loaded without full RAG dependencies
"""

import json
from typing import List, Dict, Any
from collections import defaultdict


def load_movie_database() -> Dict[str, Dict[str, Any]]:
    """Load movie database from crawled_data/movies_index.json"""
    try:
        with open('crawled_data/movies_index.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Database is nested under 'movies' key
            if isinstance(data, dict) and 'movies' in data:
                return data['movies']
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        print("⚠️ movies_index.json not found")
        return {}


def load_test_queries_from_datasets() -> List[Dict[str, Any]]:
    """Load test queries from test_datasets/ with automatic relevance extraction"""
    import glob
    
    test_queries = []
    query_id = 1
    
    dataset_files = {
        'test_datasets/actor_based.json': 'actor_filmography',
        'test_datasets/director_based.json': 'director_filmography',
        'test_datasets/genre_recommendation.json': 'genre_recommendation',
        'test_datasets/specific_film_info.json': 'specific_film_info',
        'test_datasets/multi_hop.json': 'multi_hop',
        'test_datasets/comparison.json': 'comparison',
        'test_datasets/temporal_based.json': 'temporal_based'
    }
    
    movie_db = load_movie_database()
    
    # Convert movie_db to dict if it's a list
    if isinstance(movie_db, list):
        movie_db_dict = {}
        for idx, movie in enumerate(movie_db):
            if isinstance(movie, dict) and 'id' in movie:
                movie_db_dict[movie['id']] = movie
            elif isinstance(movie, dict) and 'title' in movie:
                movie_db_dict[movie['title'].replace(' ', '_').lower()] = movie
        movie_db = movie_db_dict
    
    print(f"📦 Movie database loaded: {len(movie_db)} movies")
    
    for filepath, category in dataset_files.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                test_cases = data.get('test_cases', [])
                
                # Load up to 5 queries per category
                for test_case in test_cases[:5]:
                    query = test_case.get('query', '')
                    entities = test_case.get('entities', [])
                    
                    # Extract relevant documents based on entities
                    relevant_ids = []
                    for entity in entities:
                        entity_lower = entity.lower()
                        for movie_id, movie_data in movie_db.items():
                            if isinstance(movie_data, dict):
                                title = movie_data.get('title', '').lower()
                                overview = movie_data.get('overview', '').lower()
                                cast = [c.lower() for c in movie_data.get('cast', [])]
                                director = movie_data.get('director', '').lower()
                                genres = [g.lower() for g in movie_data.get('genres', [])]
                                
                                if (entity_lower in title or 
                                    entity_lower in director or 
                                    entity_lower in cast or
                                    entity_lower in genres or
                                    entity_lower in overview):
                                    if movie_id not in relevant_ids:
                                        relevant_ids.append(movie_id)
                    
                    test_queries.append({
                        'id': query_id,
                        'query': query,
                        'category': category,
                        'relevant_doc_ids': relevant_ids[:10],
                        'entities': entities,
                        'complexity': test_case.get('complexity', 'medium'),
                    })
                    query_id += 1
                
                print(f"✅ {filepath}: {len(test_cases[:5])} queries")
        
        except FileNotFoundError:
            print(f"⚠️  {filepath} not found")
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
    
    return test_queries


def analyze_ground_truth(test_queries: List[Dict[str, Any]]) -> None:
    """Analyze and display ground truth statistics"""
    
    print("\n" + "=" * 70)
    print("📊 GROUND TRUTH ANALYSIS")
    print("=" * 70)
    
    categories = defaultdict(int)
    total_relevant = 0
    queries_with_relevance = 0
    
    for query in test_queries:
        category = query.get('category', 'unknown')
        categories[category] += 1
        
        relevant_count = len(query.get('relevant_doc_ids', []))
        total_relevant += relevant_count
        if relevant_count > 0:
            queries_with_relevance += 1
    
    print(f"\nTotal Queries: {len(test_queries)}")
    print(f"Queries with Relevant Docs: {queries_with_relevance}")
    print(f"Total Relevant Documents: {total_relevant}")
    if test_queries:
        print(f"Avg Relevant Per Query: {total_relevant / len(test_queries):.2f}")
    
    print("\n📑 Category Distribution:")
    for category, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {category:25s}: {count:3d} queries")
    
    print("\n📋 Sample Queries:")
    for i, query in enumerate(test_queries[:3], 1):
        print(f"\n  [{i}] {query['query'][:60]}...")
        print(f"      Category: {query['category']}")
        print(f"      Relevant Docs: {len(query['relevant_doc_ids'])}")
        if query.get('entities'):
            print(f"      Entities: {', '.join(query['entities'][:3])}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔍 Testing Ground Truth Integration")
    print("=" * 70)
    
    test_queries = load_test_queries_from_datasets()
    print(f"\n✅ Total queries loaded: {len(test_queries)}")
    
    if test_queries:
        analyze_ground_truth(test_queries)
    else:
        print("⚠️ No queries loaded")
