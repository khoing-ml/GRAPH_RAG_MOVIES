"""
Fast MRR/MAP evaluation test - doesn't require full RAG pipeline
Uses mock retrieval based on ground truth relevance

This is for testing the evaluation framework without the overhead
of actually running the RAG retrieval for every query.
"""

import json
import random
from typing import List, Dict, Any
from collections import defaultdict
import numpy as np
from evaluate_mrr_map import (
    RetrievalEvaluator,
    load_test_queries_with_relevance,
    analyze_ground_truth
)


def create_mock_retrieval_results(relevant_ids: List[str], total_retrieve: int = 10, 
                                   noise_ratio: float = 0.3) -> List[Dict]:
    """
    Create mock retrieved documents for testing
    
    Args:
        relevant_ids: Ground truth relevant document IDs
        total_retrieve: Total documents to return
        noise_ratio: Fraction of irrelevant documents to include
    
    Returns:
        Mock retrieved documents in correct order
    """
    
    # Calculate how many relevant docs to include
    num_relevant = max(1, int(total_retrieve * (1 - noise_ratio)))
    num_noise = total_retrieve - num_relevant
    
    # Shuffle relevant docs and take top ones
    relevant_subset = random.sample(relevant_ids, min(num_relevant, len(relevant_ids)))
    
    # Create noise documents
    noise_docs = [f'irrelevant_{i}' for i in range(num_noise)]
    
    # Mix them randomly
    all_docs = relevant_subset + noise_docs
    random.shuffle(all_docs)
    
    # Convert to document format
    retrieved_docs = [
        {'id': doc_id, 'title': doc_id}
        for doc_id in all_docs
    ]
    
    return retrieved_docs


def run_mock_evaluation(test_queries: List[Dict[str, Any]], 
                       noise_ratio: float = 0.3) -> Dict[str, Any]:
    """
    Run evaluation with mock retrieval results
    
    Args:
        test_queries: Test queries with ground truth
        noise_ratio: Amount of noise in mock results (0-1)
    
    Returns:
        Evaluation report
    """
    
    evaluator = RetrievalEvaluator()
    query_results = []
    category_metrics = defaultdict(list)
    
    print(f"\n🔍 Mock Retrieval Evaluation (noise ratio: {noise_ratio:.1%})")
    print("=" * 70)
    
    for idx, query_data in enumerate(test_queries, 1):
        query = query_data['query']
        relevant_ids = query_data.get('relevant_doc_ids', [])
        category = query_data.get('category', 'unknown')
        
        # Skip if no relevant documents
        if not relevant_ids:
            print(f"⊘  [{idx:3d}] SKIPPED (no relevant ground truth)")
            continue
        
        try:
            # Create mock retrieval
            retrieved_docs = create_mock_retrieval_results(relevant_ids, total_retrieve=10, noise_ratio=noise_ratio)
            
            # Calculate metrics
            mrr = evaluator.calculate_mrr(retrieved_docs, relevant_ids)
            map_score = evaluator.calculate_map(retrieved_docs, relevant_ids, k=10)
            recall_10 = evaluator.calculate_recall_at_k(retrieved_docs, relevant_ids, k=10)
            ndcg_10 = evaluator.calculate_ndcg(retrieved_docs, relevant_ids, k=10)
            
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
                'latency_ms': random.uniform(50, 500),  # Mock latency
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
        'total_queries': len(test_queries),
        'evaluated_queries': len(query_results),
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
        'mode': 'mock',
        'noise_ratio': noise_ratio,
        'query_results': query_results,
        'aggregate_metrics': aggregate_metrics
    }


def main():
    """Run mock evaluation"""
    
    print("\n" + "=" * 70)
    print("🚀 MOCK MRR/MAP EVALUATION (Fast Testing)")
    print("=" * 70)
    
    # Load test queries
    test_queries = load_test_queries_with_relevance()
    print(f"\n✅ Loaded {len(test_queries)} test queries")
    
    # Analyze ground truth
    analyze_ground_truth(test_queries)
    
    # Run mock evaluation with different noise levels
    noise_levels = [0.2, 0.5, 0.8]  # 80%, 50%, 20% relevant in top-10
    
    for noise_ratio in noise_levels:
        report = run_mock_evaluation(test_queries, noise_ratio=noise_ratio)
        
        # Print summary
        metrics = report['aggregate_metrics']['metrics']
        print("\n" + "=" * 70)
        print(f"📊 MOCK EVALUATION (Quality: {1-noise_ratio:.0%} relevant in top-10)")
        print("=" * 70)
        print(f"Total Queries: {report['aggregate_metrics']['total_queries']}")
        print(f"Evaluated: {report['aggregate_metrics']['evaluated_queries']}")
        print("\n🎯 RANKING METRICS:")
        print(f"  MRR:        {metrics['mrr']:.4f}")
        print(f"  MAP@10:     {metrics['map@10']:.4f}")
        print(f"  Recall@10:  {metrics['recall@10']:.4f}")
        print(f"  NDCG@10:    {metrics['ndcg@10']:.4f}")
        print(f"  Avg Latency: {metrics['avg_latency_ms']:.1f}ms")
        
        # Category breakdown
        if report['aggregate_metrics']['category_breakdown']:
            print("\n📑 TOP CATEGORIES:")
            sorted_cats = sorted(
                report['aggregate_metrics']['category_breakdown'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:3]
            for cat, metrics in sorted_cats:
                print(f"\n  {cat} ({metrics['count']} queries):")
                print(f"    MRR: {metrics['mrr']:.4f} | MAP: {metrics['map@10']:.4f}")


if __name__ == "__main__":
    main()
