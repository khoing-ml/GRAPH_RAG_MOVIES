"""
MRR/MAP Evaluation for Movie RAG Retrieval Systems

Evaluates ranking quality of retrieved documents:
- MRR (Mean Reciprocal Rank): Position of first relevant document
- MAP (Mean Average Precision): Ranking quality across all relevant documents

Supports: GraphRAG vs SimpleRAG comparison
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import numpy as np
from src.rag_pipeline import GraphRAG
from src.simple_rag import SimpleRAG
from src.config import Config

class RetrievalEvaluator:
    """Evaluate retrieval ranking quality using MRR/MAP metrics"""
    
    def __init__(self):
        self.config = Config()
        self.results = {
            'graphrag': defaultdict(list),
            'simplerage': defaultdict(list)
        }
    
    def calculate_mrr(self, ranked_docs: List[Dict], relevant_doc_ids: List[str]) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR)
        
        Args:
            ranked_docs: List of retrieved documents in rank order
            relevant_doc_ids: List of relevant document IDs for this query
        
        Returns:
            MRR score (0-1). Higher is better.
            - 1.0: First result is relevant
            - 0.5: Second result is relevant
            - 0.0: No relevant results found
        """
        relevant_ids_set = set(relevant_doc_ids)
        
        for rank, doc in enumerate(ranked_docs, start=1):
            doc_id = doc.get('id') or doc.get('movie_id') or doc.get('title', '').replace(' ', '_')
            if doc_id in relevant_ids_set:
                return 1.0 / rank
        
        return 0.0
    
    def calculate_map(self, ranked_docs: List[Dict], relevant_doc_ids: List[str], 
                      k: int = 10) -> float:
        """
        Calculate Mean Average Precision (MAP@k)
        
        Args:
            ranked_docs: List of retrieved documents in rank order
            relevant_doc_ids: List of relevant document IDs for this query
            k: Evaluate up to top-k results
        
        Returns:
            MAP score (0-1). Higher is better.
        """
        relevant_ids_set = set(relevant_doc_ids)
        ranked_docs = ranked_docs[:k]
        
        if not relevant_ids_set:
            return 0.0
        
        num_relevant_retrieved = 0
        precision_sum = 0.0
        
        for rank, doc in enumerate(ranked_docs, start=1):
            doc_id = doc.get('id') or doc.get('movie_id') or doc.get('title', '').replace(' ', '_')
            if doc_id in relevant_ids_set:
                num_relevant_retrieved += 1
                precision_at_k = num_relevant_retrieved / rank
                precision_sum += precision_at_k
        
        # MAP = sum of precisions / total relevant documents
        return precision_sum / min(len(relevant_ids_set), k) if relevant_ids_set else 0.0
    
    def calculate_recall_at_k(self, ranked_docs: List[Dict], relevant_doc_ids: List[str], 
                              k: int = 10) -> float:
        """
        Calculate Recall@k: proportion of relevant docs retrieved in top-k
        
        Args:
            ranked_docs: List of retrieved documents in rank order
            relevant_doc_ids: List of relevant document IDs for this query
            k: Evaluate top-k results
        
        Returns:
            Recall@k score (0-1)
        """
        relevant_ids_set = set(relevant_doc_ids)
        if not relevant_ids_set:
            return 0.0
        
        retrieved_ids = set()
        for doc in ranked_docs[:k]:
            doc_id = doc.get('id') or doc.get('movie_id') or doc.get('title', '').replace(' ', '_')
            retrieved_ids.add(doc_id)
        
        num_relevant_retrieved = len(retrieved_ids & relevant_ids_set)
        return num_relevant_retrieved / len(relevant_ids_set)
    
    def calculate_ndcg(self, ranked_docs: List[Dict], relevant_doc_ids: List[str], 
                       k: int = 10) -> float:
        """
        Calculate NDCG@k: Normalized Discounted Cumulative Gain
        Accounts for relevance grading and position decay
        
        Args:
            ranked_docs: List of retrieved documents in rank order
            relevant_doc_ids: List of relevant document IDs for this query
            k: Evaluate top-k results
        
        Returns:
            NDCG@k score (0-1)
        """
        relevant_ids_set = set(relevant_doc_ids)
        ranked_docs = ranked_docs[:k]
        
        if not relevant_ids_set:
            return 0.0
        
        # Calculate DCG (Discounted Cumulative Gain)
        dcg = 0.0
        for rank, doc in enumerate(ranked_docs, start=1):
            doc_id = doc.get('id') or doc.get('movie_id') or doc.get('title', '').replace(' ', '_')
            relevance = 1.0 if doc_id in relevant_ids_set else 0.0
            dcg += relevance / np.log2(rank + 1)
        
        # Calculate IDCG (Ideal DCG - all relevant docs at top)
        idcg = 0.0
        for rank in range(1, min(len(relevant_ids_set), k) + 1):
            idcg += 1.0 / np.log2(rank + 1)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def evaluate_retrieval(self, queries_with_relevance: List[Dict], 
                          rag_type: str = 'graphrag') -> Dict[str, Any]:
        """
        Evaluate retrieval for a set of queries
        
        Args:
            queries_with_relevance: List of dicts with:
                {
                    "query": "...",
                    "relevant_doc_ids": ["id1", "id2", ...],
                    "category": "..."
                }
            rag_type: 'graphrag' or 'simplerage'
        
        Returns:
            Evaluation report with metrics
        """
        if rag_type == 'graphrag':
            rag = GraphRAG()
        elif rag_type == 'simplerage':
            rag = SimpleRAG()
        else:
            raise ValueError(f"Unknown RAG type: {rag_type}")
        
        query_results = []
        category_metrics = defaultdict(list)
        
        print(f"\n🔍 Evaluating {rag_type.upper()} Retrieval")
        print("=" * 70)
        
        for idx, query_data in enumerate(queries_with_relevance, 1):
            query = query_data['query']
            relevant_ids = query_data.get('relevant_doc_ids', [])
            category = query_data.get('category', 'unknown')
            
            try:
                # Retrieve documents
                start_time = time.time()
                
                # For both RAG types, call query() then extract retrieved IDs
                _ = rag.query(query)
                
                # Get the retrieved movie IDs
                retrieved_ids = getattr(rag, 'last_movies', [])[:10]
                
                # Convert IDs to document dict format for metric calculation
                retrieved_docs = [
                    {'id': movie_id, 'title': str(movie_id)}
                    for movie_id in retrieved_ids
                ]
                
                latency = time.time() - start_time
                
                # Calculate metrics
                mrr = self.calculate_mrr(retrieved_docs, relevant_ids)
                map_score = self.calculate_map(retrieved_docs, relevant_ids, k=10)
                recall_10 = self.calculate_recall_at_k(retrieved_docs, relevant_ids, k=10)
                ndcg_10 = self.calculate_ndcg(retrieved_docs, relevant_ids, k=10)
                
                result = {
                    'query_id': idx,
                    'query': query,
                    'category': category,
                    'relevant_count': len(relevant_ids),
                    'retrieved_count': len(retrieved_docs),
                    'mrr': mrr,
                    'map@10': map_score,
                    'recall@10': recall_10,
                    'ndcg@10': ndcg_10,
                    'latency_ms': latency * 1000,
                    'success': True
                }
                
                query_results.append(result)
                category_metrics[category].append(result)
                
                # Print progress
                status = "✅" if mrr > 0 else "⚠️"
                print(f"{status} [{idx:3d}] MRR: {mrr:.3f} | MAP: {map_score:.3f} | NDCG: {ndcg_10:.3f} | {query[:45]}...")
                
            except Exception as e:
                print(f"❌ [{idx:3d}] ERROR: {str(e)[:50]}")
                result = {
                    'query_id': idx,
                    'query': query,
                    'category': category,
                    'success': False,
                    'error': str(e)
                }
                query_results.append(result)
        
        # Calculate aggregate metrics
        successful_queries = [r for r in query_results if r.get('success', False)]
        
        aggregate_metrics = {
            'total_queries': len(queries_with_relevance),
            'successful_queries': len(successful_queries),
            'failed_queries': len(query_results) - len(successful_queries),
            'metrics': {
                'mrr': np.mean([r['mrr'] for r in successful_queries]) if successful_queries else 0.0,
                'map@10': np.mean([r['map@10'] for r in successful_queries]) if successful_queries else 0.0,
                'recall@10': np.mean([r['recall@10'] for r in successful_queries]) if successful_queries else 0.0,
                'ndcg@10': np.mean([r['ndcg@10'] for r in successful_queries]) if successful_queries else 0.0,
                'avg_latency_ms': np.mean([r['latency_ms'] for r in successful_queries]) if successful_queries else 0.0,
            },
            'category_breakdown': {}
        }
        
        # Calculate per-category metrics
        for category, results in category_metrics.items():
            category_successful = [r for r in results if r.get('success', False)]
            if category_successful:
                aggregate_metrics['category_breakdown'][category] = {
                    'count': len(results),
                    'mrr': np.mean([r['mrr'] for r in category_successful]),
                    'map@10': np.mean([r['map@10'] for r in category_successful]),
                    'recall@10': np.mean([r['recall@10'] for r in category_successful]),
                    'ndcg@10': np.mean([r['ndcg@10'] for r in category_successful]),
                }
        
        return {
            'rag_type': rag_type,
            'timestamp': datetime.now().isoformat(),
            'query_results': query_results,
            'aggregate_metrics': aggregate_metrics
        }
    
    def print_summary(self, evaluation_report: Dict[str, Any]):
        """Print formatted evaluation summary"""
        metrics = evaluation_report['aggregate_metrics']['metrics']
        rag_type = evaluation_report['rag_type']
        
        print("\n" + "=" * 70)
        print(f"📊 EVALUATION SUMMARY - {rag_type.upper()}")
        print("=" * 70)
        print(f"Total Queries: {evaluation_report['aggregate_metrics']['total_queries']}")
        print(f"Successful: {evaluation_report['aggregate_metrics']['successful_queries']}")
        print(f"Failed: {evaluation_report['aggregate_metrics']['failed_queries']}")
        print("\n🎯 RANKING METRICS:")
        print(f"  MRR:        {metrics['mrr']:.4f}  (0-1, higher is better)")
        print(f"  MAP@10:     {metrics['map@10']:.4f}  (0-1, higher is better)")
        print(f"  Recall@10:  {metrics['recall@10']:.4f}  (0-1, higher is better)")
        print(f"  NDCG@10:    {metrics['ndcg@10']:.4f}  (0-1, higher is better)")
        print(f"  Avg Latency: {metrics['avg_latency_ms']:.1f}ms")
        
        if evaluation_report['aggregate_metrics']['category_breakdown']:
            print("\n📑 CATEGORY BREAKDOWN:")
            for category, cat_metrics in evaluation_report['aggregate_metrics']['category_breakdown'].items():
                print(f"\n  {category} ({cat_metrics['count']} queries):")
                print(f"    MRR: {cat_metrics['mrr']:.4f} | MAP: {cat_metrics['map@10']:.4f} | Recall: {cat_metrics['recall@10']:.4f}")
    
    def compare_systems(self, evaluation_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare metrics between multiple RAG systems"""
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'systems': [],
            'best_metrics': {}
        }
        
        for report in evaluation_reports:
            rag_type = report['rag_type']
            metrics = report['aggregate_metrics']['metrics']
            
            comparison['systems'].append({
                'name': rag_type,
                'metrics': metrics
            })
        
        # Find best system for each metric
        if len(comparison['systems']) > 1:
            for metric_name in ['mrr', 'map@10', 'recall@10', 'ndcg@10']:
                best_system = max(
                    comparison['systems'],
                    key=lambda x: x['metrics'].get(metric_name, 0)
                )
                comparison['best_metrics'][metric_name] = {
                    'system': best_system['name'],
                    'score': best_system['metrics'].get(metric_name, 0)
                }
        
        return comparison
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save evaluation report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mrr_map_evaluation_{report['rag_type']}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Report saved: {filename}")
        return filename


def load_movie_database() -> Dict[str, Dict[str, Any]]:
    """
    Load movie database from crawled_data/movies_index.json
    Maps movie titles to their data for relevance matching
    """
    try:
        with open('crawled_data/movies_index.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Database is nested under 'movies' key
            if isinstance(data, dict) and 'movies' in data:
                return data['movies']
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        print("⚠️ Warning: movies_index.json not found")
        return {}


def extract_relevant_docs_from_categories() -> Dict[str, List[str]]:
    """
    Build a mapping of movie categories to document IDs
    Analyzes movie metadata to find relevant documents for queries
    """
    movie_db = load_movie_database()
    category_map = {}
    
    # Build genre -> movies mapping
    for movie_id, movie_data in movie_db.items():
        if isinstance(movie_data, dict):
            genres = movie_data.get('genres', [])
            title = movie_data.get('title', '').lower()
            
            for genre in genres:
                genre_key = genre.lower()
                if genre_key not in category_map:
                    category_map[genre_key] = []
                category_map[genre_key].append(movie_id)
    
    return category_map


def load_test_queries_from_datasets() -> List[Dict[str, Any]]:
    """
    Load test queries from test_datasets/ with automatic relevance extraction
    Integrates ground truth from structured test files
    """
    import glob
    
    test_queries = []
    query_id = 1
    
    # Load from test_datasets directory
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
    
    # Convert movie_db to dict if it's a list (indexed by movie_id)
    if isinstance(movie_db, list):
        movie_db_dict = {}
        for idx, movie in enumerate(movie_db):
            if isinstance(movie, dict) and 'id' in movie:
                movie_db_dict[movie['id']] = movie
            elif isinstance(movie, dict) and 'title' in movie:
                movie_db_dict[movie['title'].replace(' ', '_').lower()] = movie
        movie_db = movie_db_dict
    
    for filepath, category in dataset_files.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                test_cases = data.get('test_cases', [])
                
                # Limit to 5 queries per category for manageability
                for test_case in test_cases[:5]:
                    query = test_case.get('query', '')
                    entities = test_case.get('entities', [])
                    
                    # Extract relevant documents based on entities and movie metadata
                    relevant_ids = []
                    for entity in entities:
                        entity_lower = entity.lower()
                        # Match movies by title or metadata
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
                        'relevant_doc_ids': relevant_ids[:10],  # Top 10 relevant docs
                        'entities': entities,
                        'complexity': test_case.get('complexity', 'medium'),
                        'expected_answer': ''
                    })
                    query_id += 1
        
        except FileNotFoundError:
            print(f"⚠️  {filepath} not found")
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
    
    # Also load from main test_dataset.json
    try:
        with open('test_dataset.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            test_cases = data.get('test_queries', [])
            
            # Limit to 5 queries from main dataset
            for test_case in test_cases[:5]:
                query = test_case.get('query', '')
                category = test_case.get('category', 'unknown')
                expected_topics = test_case.get('expected_topics', [])
                
                # Extract relevant documents based on expected topics
                relevant_ids = []
                for topic in expected_topics:
                    topic_lower = topic.lower()
                    for movie_id, movie_data in movie_db.items():
                        if isinstance(movie_data, dict):
                            title = movie_data.get('title', '').lower()
                            overview = movie_data.get('overview', '').lower()
                            genres = [g.lower() for g in movie_data.get('genres', [])]
                            
                            if (topic_lower in title or 
                                topic_lower in overview or
                                topic_lower in genres):
                                if movie_id not in relevant_ids:
                                    relevant_ids.append(movie_id)
                
                test_queries.append({
                    'id': query_id,
                    'query': query,
                    'category': category,
                    'relevant_doc_ids': relevant_ids[:10],
                    'entities': expected_topics,
                    'complexity': 'medium',
                    'expected_answer': test_case.get('expected_answer', '')
                })
                query_id += 1
    
    except FileNotFoundError:
        print("⚠️ test_dataset.json not found")
    except Exception as e:
        print(f"❌ Error loading test_dataset.json: {e}")
    
    return test_queries


def load_test_queries_with_relevance() -> List[Dict[str, Any]]:
    """
    Load test queries with relevant document IDs from integrated ground truth
    Automatically extracts relevance from test_datasets/ and movie database
    """
    
    # Try to load from integrated test datasets first
    test_queries = load_test_queries_from_datasets()
    
    if test_queries:
        print(f"✅ Loaded {len(test_queries)} test queries from test_datasets/")
        return test_queries
    
    # Fallback to manual test queries
    print("⚠️ Using fallback manual test queries")
    test_queries = [
        {
            "query": "What are the best romance movies?",
            "category": "genre_recommendation",
            "relevant_doc_ids": ["the_notebook", "la_la_land", "pride_and_prejudice", "titanic"],
            "expected_answer": "Romance films with emotional depth and compelling storytelling"
        },
        {
            "query": "Avatar Fire and Ash release date?",
            "category": "specific_film_info",
            "relevant_doc_ids": ["avatar_fire_and_ash"],
            "expected_answer": "December 2025"
        },
        {
            "query": "Movies similar to The Shawshank Redemption?",
            "category": "similarity_search",
            "relevant_doc_ids": ["the_green_mile", "forrest_gump", "the_pursuit_of_happiness"],
            "expected_answer": "Inspirational films with themes of redemption and hope"
        },
        {
            "query": "Christopher Nolan movies?",
            "category": "director_filmography",
            "relevant_doc_ids": ["inception", "the_dark_knight", "interstellar", "oppenheimer"],
            "expected_answer": "Filmography of Christopher Nolan"
        },
        {
            "query": "Tom Hanks filmography?",
            "category": "actor_filmography",
            "relevant_doc_ids": ["forrest_gump", "saving_private_ryan", "the_green_mile", "cast_away"],
            "expected_answer": "Films starring Tom Hanks"
        },
        {
            "query": "Best sci-fi movies?",
            "category": "genre_recommendation",
            "relevant_doc_ids": ["inception", "interstellar", "the_matrix", "blade_runner"],
            "expected_answer": "Science fiction films with innovative storytelling"
        },
        {
            "query": "Studio Ghibli films?",
            "category": "studio_recommendation",
            "relevant_doc_ids": ["spirited_away", "howls_moving_castle", "ponyo"],
            "expected_answer": "Animated films by Studio Ghibli"
        },
        {
            "query": "Marvel Cinematic Universe movies in order?",
            "category": "franchise_series",
            "relevant_doc_ids": ["iron_man", "avengers", "avengers_endgame"],
            "expected_answer": "MCU films in chronological order"
        },
        {
            "query": "Award winning dramas?",
            "category": "award_winners",
            "relevant_doc_ids": ["the_shawshank_redemption", "schindlers_list", "parasite"],
            "expected_answer": "Academy Award winning dramatic films"
        },
        {
            "query": "Psychological thriller films?",
            "category": "genre_recommendation",
            "relevant_doc_ids": ["the_shining", "hereditary", "gone_girl", "black_swan"],
            "expected_answer": "Mind-bending thriller films with psychological depth"
        }
    ]
    
    return test_queries


def analyze_ground_truth(test_queries: List[Dict[str, Any]]) -> None:
    """Analyze and display ground truth statistics"""
    
    print("\n" + "=" * 70)
    print("📊 GROUND TRUTH ANALYSIS")
    print("=" * 70)
    
    # Category distribution
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
    print(f"Avg Relevant Per Query: {total_relevant / len(test_queries):.2f}")
    
    print("\n📑 Category Distribution:")
    for category, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {category:25s}: {count:3d} queries")
    
    print("\n" + "=" * 70)


def main():
    """Run full MRR/MAP evaluation comparing systems"""
    
    print("\n" + "=" * 70)
    print("🚀 MRR/MAP RETRIEVAL EVALUATION")
    print("=" * 70)
    
    # Load test queries with ground truth
    test_queries = load_test_queries_with_relevance()
    print(f"\n✅ Loaded {len(test_queries)} test queries")
    
    # Analyze ground truth
    analyze_ground_truth(test_queries)
    
    evaluator = RetrievalEvaluator()
    
    # Evaluate both systems
    graphrag_report = evaluator.evaluate_retrieval(test_queries, rag_type='graphrag')
    evaluator.print_summary(graphrag_report)
    
    simplerage_report = evaluator.evaluate_retrieval(test_queries, rag_type='simplerage')
    evaluator.print_summary(simplerage_report)
    
    # Compare systems
    comparison = evaluator.compare_systems([graphrag_report, simplerage_report])
    
    print("\n" + "=" * 70)
    print("🏆 SYSTEM COMPARISON")
    print("=" * 70)
    for metric, best in comparison['best_metrics'].items():
        print(f"{metric:12s}: {best['system']:15s} ({best['score']:.4f})")
    
    # Save reports
    evaluator.save_report(graphrag_report)
    evaluator.save_report(simplerage_report)
    evaluator.save_report(comparison, f"mrr_map_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()
