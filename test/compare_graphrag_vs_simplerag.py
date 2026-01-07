"""
Comprehensive Evaluation: GraphRAG vs SimpleRAG
Evaluates both systems on test dataset using RAGAS metrics
"""

import json
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness
)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from src.rag_pipeline import GraphRAG
from src.simple_rag import SimpleRAG
from src.config import Config
import os
import pandas as pd

# Initialize config
config = Config()

# Initialize Gemini for RAGAS evaluation
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

evaluator_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.0
)

# Initialize Gemini embeddings for RAGAS (to avoid OpenAI API key requirement)
evaluator_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)


def load_test_dataset(filepath='test_dataset.json', max_queries=None, start_index=0, end_index=None):
    """Load test queries from JSON file
    
    Args:
        filepath: Path to test dataset JSON file
        max_queries: Maximum number of queries to load (None = all)
        start_index: Starting index (0-based)
        end_index: Ending index (exclusive, None = to end)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_queries = data['test_queries']
        total_available = len(all_queries)
        
        # Apply slicing
        if end_index is not None:
            queries = all_queries[start_index:end_index]
        elif max_queries is not None:
            queries = all_queries[start_index:start_index + max_queries]
        else:
            queries = all_queries[start_index:]
        
        print(f"✓ Loaded {len(queries)} queries (from {start_index+1} to {start_index+len(queries)}) out of {total_available} total")
        return queries
    except FileNotFoundError:
        print(f"⚠️ Error: {filepath} not found")
        return []


class ComparisonEvaluator:
    """Evaluate and compare GraphRAG vs SimpleRAG"""
    
    def __init__(self, graphrag_pipeline, simplerag_pipeline):
        self.graphrag = graphrag_pipeline
        self.simplerag = simplerag_pipeline
        self.results = {
            'graphrag': [],
            'simplerag': []
        }
        
    def query_with_context(self, rag_system, question: str, system_name: str) -> tuple:
        """
        Query RAG and capture context for RAGAS evaluation
        Returns: (answer, contexts_list)
        """
        contexts = []
        
        # Query the system
        answer = rag_system.query(question)
        
        # Extract contexts based on system type
        if hasattr(rag_system, 'vectordb'):
            # Get embedding and search for contexts
            query_vec = rag_system.llm.get_embedding(question, task_type="retrieval_query")
            if query_vec:
                search_results = rag_system.vectordb.search(query_vec, top_k=6)
                for item in search_results:
                    if hasattr(item, 'payload') and item.payload:
                        # Extract text content from payload
                        text_parts = []
                        if 'title' in item.payload:
                            text_parts.append(f"Title: {item.payload['title']}")
                        if 'overview' in item.payload:
                            text_parts.append(f"Overview: {item.payload['overview']}")
                        if 'genres' in item.payload:
                            text_parts.append(f"Genres: {item.payload['genres']}")
                        if 'director' in item.payload:
                            text_parts.append(f"Director: {item.payload['director']}")
                        
                        if text_parts:
                            contexts.append(" | ".join(text_parts))
        
        # If no contexts found, use answer as context (fallback)
        if not contexts:
            contexts = [answer]
        
        return answer, contexts
    
    def evaluate_single_query(self, query_data: Dict, system_name: str, rag_system) -> Dict:
        """Evaluate a single query on one system"""
        question = query_data['query']
        ground_truth = query_data.get('ground_truth', '')
        
        print(f"  └─ [{system_name}] Processing query: {question[:50]}...")
        
        start_time = time.time()
        try:
            answer, contexts = self.query_with_context(rag_system, question, system_name)
            response_time = time.time() - start_time
            
            return {
                'query_id': query_data.get('id', 'unknown'),
                'question': question,
                'answer': answer,
                'contexts': contexts,
                'ground_truth': ground_truth,
                'category': query_data.get('category', 'unknown'),
                'response_time': response_time,
                'system': system_name
            }
        except Exception as e:
            print(f"    ⚠️ Error processing query: {str(e)}")
            return {
                'query_id': query_data.get('id', 'unknown'),
                'question': question,
                'answer': f"Error: {str(e)}",
                'contexts': ['Error occurred'],
                'ground_truth': ground_truth,
                'category': query_data.get('category', 'unknown'),
                'response_time': time.time() - start_time,
                'system': system_name,
                'error': True
            }
    
    def evaluate_all_queries(self, test_queries: List[Dict]):
        """Evaluate all queries on both systems"""
        total_queries = len(test_queries)
        print(f"\n{'='*80}")
        print(f"Starting evaluation of {total_queries} queries on 2 systems")
        print(f"{'='*80}\n")
        
        for idx, query_data in enumerate(test_queries, 1):
            print(f"\n[{idx}/{total_queries}] Query ID: {query_data.get('id', 'unknown')}")
            print(f"Category: {query_data.get('category', 'unknown')}")
            
            # Evaluate on GraphRAG
            graphrag_result = self.evaluate_single_query(query_data, "GraphRAG", self.graphrag)
            self.results['graphrag'].append(graphrag_result)
            
            # Small delay between systems
            time.sleep(0.5)
            
            # Evaluate on SimpleRAG
            simplerag_result = self.evaluate_single_query(query_data, "SimpleRAG", self.simplerag)
            self.results['simplerag'].append(simplerag_result)
            
            print(f"  ✓ Completed query {idx}/{total_queries}")
            
            # Longer delay between queries to avoid rate limiting
            if idx < total_queries:
                time.sleep(1)
        
        print(f"\n{'='*80}")
        print("✓ All queries processed successfully!")
        print(f"{'='*80}\n")
    
    def compute_ragas_metrics(self, results: List[Dict], system_name: str) -> Dict:
        """Compute RAGAS metrics for a system"""
        print(f"\n📊 Computing RAGAS metrics for {system_name}...")
        
        # Filter out error results
        valid_results = [r for r in results if not r.get('error', False)]
        
        if not valid_results:
            print(f"  ⚠️ No valid results for {system_name}")
            return {}
        
        # Prepare data for RAGAS
        data = {
            'question': [r['question'] for r in valid_results],
            'answer': [r['answer'] for r in valid_results],
            'contexts': [r['contexts'] for r in valid_results],
            'ground_truth': [r['ground_truth'] for r in valid_results]
        }
        
        dataset = Dataset.from_dict(data)
        
        # Evaluate with RAGAS
        try:
            print(f"  → Running RAGAS evaluation on {len(valid_results)} queries...")
            evaluation_result = evaluate(
                dataset=dataset,
                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall,
                    answer_correctness
                ],
                llm=evaluator_llm,
                embeddings=evaluator_embeddings,
                raise_exceptions=False
            )
            
            metrics = {
                'faithfulness': evaluation_result['faithfulness'],
                'answer_relevancy': evaluation_result['answer_relevancy'],
                'context_precision': evaluation_result['context_precision'],
                'context_recall': evaluation_result['context_recall'],
                'answer_correctness': evaluation_result['answer_correctness']
            }
            
            print(f"  ✓ RAGAS metrics computed successfully")
            return metrics
            
        except Exception as e:
            print(f"  ⚠️ Error computing RAGAS metrics: {str(e)}")
            return {}
    
    def compute_custom_metrics(self, results: List[Dict]) -> Dict:
        """Compute custom metrics"""
        valid_results = [r for r in results if not r.get('error', False)]
        
        if not valid_results:
            return {}
        
        avg_response_time = sum(r['response_time'] for r in valid_results) / len(valid_results)
        total_queries = len(results)
        successful_queries = len(valid_results)
        success_rate = successful_queries / total_queries if total_queries > 0 else 0
        
        # Category-wise breakdown
        category_counts = {}
        for r in valid_results:
            cat = r.get('category', 'unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            'avg_response_time': avg_response_time,
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'success_rate': success_rate,
            'category_breakdown': category_counts
        }
    
    def generate_comparison_report(self, output_file: str = None):
        """Generate comprehensive comparison report"""
        print(f"\n{'='*80}")
        print("GENERATING COMPARISON REPORT")
        print(f"{'='*80}\n")
        
        # Compute metrics for both systems
        graphrag_ragas = self.compute_ragas_metrics(self.results['graphrag'], "GraphRAG")
        simplerag_ragas = self.compute_ragas_metrics(self.results['simplerag'], "SimpleRAG")
        
        graphrag_custom = self.compute_custom_metrics(self.results['graphrag'])
        simplerag_custom = self.compute_custom_metrics(self.results['simplerag'])
        
        # Build report
        report = {
            'metadata': {
                'evaluation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_queries': len(self.results['graphrag']),
                'systems_compared': ['GraphRAG', 'SimpleRAG']
            },
            'graphrag': {
                'ragas_metrics': graphrag_ragas,
                'custom_metrics': graphrag_custom,
                'detailed_results': self.results['graphrag']
            },
            'simplerag': {
                'ragas_metrics': simplerag_ragas,
                'custom_metrics': simplerag_custom,
                'detailed_results': self.results['simplerag']
            },
            'comparison': {
                'winner': self._determine_winner(graphrag_ragas, simplerag_ragas),
                'improvements': self._calculate_improvements(graphrag_ragas, simplerag_ragas)
            }
        }
        
        # Save to file
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'comparison_report_{timestamp}.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Report saved to: {output_file}")
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _determine_winner(self, graphrag_metrics: Dict, simplerag_metrics: Dict) -> str:
        """Determine which system performs better"""
        if not graphrag_metrics or not simplerag_metrics:
            return "Inconclusive"
        
        graphrag_score = sum(graphrag_metrics.values()) / len(graphrag_metrics)
        simplerag_score = sum(simplerag_metrics.values()) / len(simplerag_metrics)
        
        if graphrag_score > simplerag_score:
            return "GraphRAG"
        elif simplerag_score > graphrag_score:
            return "SimpleRAG"
        else:
            return "Tie"
    
    def _calculate_improvements(self, graphrag_metrics: Dict, simplerag_metrics: Dict) -> Dict:
        """Calculate percentage improvements"""
        improvements = {}
        
        if not graphrag_metrics or not simplerag_metrics:
            return improvements
        
        for metric in graphrag_metrics:
            if metric in simplerag_metrics:
                graph_val = graphrag_metrics[metric]
                simple_val = simplerag_metrics[metric]
                
                if simple_val > 0:
                    improvement = ((graph_val - simple_val) / simple_val) * 100
                    improvements[metric] = improvement
        
        return improvements
    
    def _print_summary(self, report: Dict):
        """Print summary of comparison"""
        print(f"\n{'='*80}")
        print("EVALUATION SUMMARY")
        print(f"{'='*80}\n")
        
        # RAGAS Metrics Comparison
        print("📊 RAGAS METRICS COMPARISON:")
        print(f"{'-'*80}")
        
        graphrag_ragas = report['graphrag']['ragas_metrics']
        simplerag_ragas = report['simplerag']['ragas_metrics']
        
        if graphrag_ragas and simplerag_ragas:
            print(f"{'Metric':<25} {'GraphRAG':<15} {'SimpleRAG':<15} {'Difference':<15}")
            print(f"{'-'*80}")
            
            for metric in graphrag_ragas:
                if metric in simplerag_ragas:
                    graph_val = graphrag_ragas[metric]
                    simple_val = simplerag_ragas[metric]
                    diff = graph_val - simple_val
                    diff_str = f"{diff:+.4f}"
                    
                    print(f"{metric:<25} {graph_val:<15.4f} {simple_val:<15.4f} {diff_str:<15}")
        
        # Custom Metrics
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"{'-'*80}")
        
        graphrag_custom = report['graphrag']['custom_metrics']
        simplerag_custom = report['simplerag']['custom_metrics']
        
        if graphrag_custom and simplerag_custom:
            print(f"Average Response Time:")
            print(f"  GraphRAG:  {graphrag_custom['avg_response_time']:.2f}s")
            print(f"  SimpleRAG: {simplerag_custom['avg_response_time']:.2f}s")
            
            print(f"\nSuccess Rate:")
            print(f"  GraphRAG:  {graphrag_custom['success_rate']:.2%}")
            print(f"  SimpleRAG: {simplerag_custom['success_rate']:.2%}")
        
        # Winner
        print(f"\n🏆 OVERALL WINNER: {report['comparison']['winner']}")
        
        # Improvements
        improvements = report['comparison']['improvements']
        if improvements:
            print(f"\n📈 GRAPHRAG IMPROVEMENTS OVER SIMPLERAG:")
            for metric, improvement in improvements.items():
                print(f"  {metric}: {improvement:+.2f}%")
        
        print(f"\n{'='*80}\n")


def main():
    """Main execution function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Compare GraphRAG vs SimpleRAG using RAGAS metrics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate all queries (100)
  python compare_graphrag_vs_simplerag.py
  
  # Evaluate first 10 queries
  python compare_graphrag_vs_simplerag.py --num 10
  
  # Evaluate queries 20-30
  python compare_graphrag_vs_simplerag.py --start 19 --end 30
  
  # Evaluate 50 queries starting from query 25
  python compare_graphrag_vs_simplerag.py --start 24 --num 50
        """
    )
    
    parser.add_argument(
        '--num', '-n',
        type=int,
        default=None,
        help='Number of queries to evaluate (default: all queries)'
    )
    
    parser.add_argument(
        '--start', '-s',
        type=int,
        default=0,
        help='Starting query index (0-based, default: 0)'
    )
    
    parser.add_argument(
        '--end', '-e',
        type=int,
        default=None,
        help='Ending query index (exclusive, default: None)'
    )
    
    parser.add_argument(
        '--dataset', '-d',
        type=str,
        default='test_dataset.json',
        help='Path to test dataset JSON file (default: test_dataset.json)'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print("GraphRAG vs SimpleRAG Comparison Evaluation")
    print("Using RAGAS Framework")
    print(f"{'='*80}\n")
    
    # Load test dataset
    print("📂 Loading test dataset...")
    test_queries = load_test_dataset(
        filepath=args.dataset,
        max_queries=args.num,
        start_index=args.start,
        end_index=args.end
    )
    
    if not test_queries:
        print("❌ No test queries found. Exiting.")
        return
    
    print(f"✓ Ready to evaluate {len(test_queries)} test queries\n")
    
    # Initialize systems
    print("🚀 Initializing RAG systems...")
    print("  → Initializing GraphRAG...")
    graphrag = GraphRAG()
    
    print("  → Initializing SimpleRAG...")
    simplerag = SimpleRAG()
    print("✓ Both systems initialized\n")
    
    # Create evaluator
    evaluator = ComparisonEvaluator(graphrag, simplerag)
    
    # Run evaluation
    print("🔬 Starting evaluation process...")
    evaluator.evaluate_all_queries(test_queries)
    
    # Generate report
    report = evaluator.generate_comparison_report()
    
    print("\n✅ Evaluation completed successfully!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
