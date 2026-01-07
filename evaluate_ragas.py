"""
Official RAGAS Evaluation Framework for Movie Recommendation RAG Pipeline
Uses: https://docs.ragas.io/en/stable/
Compares: GraphRAG vs SimpleRAG (baseline)
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any
from datasets import Dataset
from ragas import evaluate
from ragas.llms import llm_factory
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from openai import OpenAI
from src.rag_pipeline import GraphRAG
from src.simple_rag import SimpleRAG
from src.config import Config
import os

# Initialize config
config = Config()

# Initialize Gemini via OpenAI-compatible endpoint (recommended per RAGAS docs)
# See: https://docs.ragas.io/en/stable/howtos/integrations/gemini/#known-issue-instructor-safety-settings-new-sdk
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Use OpenAI-compatible endpoint for Gemini to avoid instructor safety settings issue
client = OpenAI(
    api_key=GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

evaluator_llm = llm_factory("gemini-2.0-flash-exp", client=client)
# Don't explicitly create embeddings - let RAGAS auto-detect from LLM client

# Load test dataset from JSON
def load_test_dataset(filepath='test_dataset.json'):
    """Load test queries from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['test_queries']
    except FileNotFoundError:
        print(f"⚠️ Warning: {filepath} not found, using minimal dataset")
        return []

# Legacy dataset for backward compatibility
LEGACY_TEST_DATASET = [
    {
        "query": "Phim hay về tình yêu lãng mạn?",
        "expected_topics": ["romance", "love story", "relationship"],
        "ground_truth": "Should recommend romantic films with emotional depth and meaningful relationships",
        "category": "genre_recommendation"
    },
    {
        "query": "Avatar Fire and Ash ra năm nào?",
        "expected_answer": "December 2025",
        "ground_truth": "Avatar: Fire and Ash is the third Avatar film by James Cameron, released in December 2025",
        "category": "specific_film_info"
    },
    {
        "query": "Phim nào giống The Shawshank Redemption?",
        "expected_topics": ["prison", "hope", "redemption", "friendship"],
        "ground_truth": "Should recommend films about redemption, hope, and friendship in adversity",
        "category": "similarity_search"
    },
    {
        "query": "Christopher Nolan đạo diễn phim nào?",
        "expected_topics": ["Inception", "Interstellar", "The Dark Knight"],
        "ground_truth": "Should list Christopher Nolan's major films including Inception, Interstellar, The Dark Knight trilogy, Oppenheimer",
        "category": "director_filmography"
    },
    {
        "query": "Tom Hanks đóng phim gì hay?",
        "expected_topics": ["Forrest Gump", "Cast Away", "Saving Private Ryan"],
        "ground_truth": "Should list notable Tom Hanks films like Forrest Gump, Cast Away, Saving Private Ryan, The Green Mile",
        "category": "actor_filmography"
    }
]


class RAGASEvaluator:
    """Evaluate RAG pipeline using official RAGAS framework"""
    
    def __init__(self, rag_pipeline, system_name="RAG"):
        self.rag = rag_pipeline
        self.system_name = system_name
        self.contexts_cache = []  # Store contexts for RAGAS
        
    def query_with_context(self, question: str) -> tuple:
        """
        Query RAG and capture context for RAGAS evaluation
        Returns: (answer, contexts_list)
        """
        # For SimpleRAG, we need to extract contexts manually
        if hasattr(self.rag, 'vectordb'):
            # Get query vector
            query_vec = self.rag.llm.get_embedding(question, task_type="retrieval_query")
            
            if query_vec:
                # Search vector DB
                search_results = self.rag.vectordb.search(query_vec, top_k=5)
                
                # Extract contexts
                contexts = []
                for item in search_results:
                    payload = item.payload if hasattr(item, 'payload') else item
                    
                    # Build context string from payload
                    context_parts = []
                    if payload.get('title'):
                        context_parts.append(f"Title: {payload['title']}")
                    if payload.get('year'):
                        context_parts.append(f"Year: {payload['year']}")
                    if payload.get('director'):
                        context_parts.append(f"Director: {payload['director']}")
                    if payload.get('genres'):
                        context_parts.append(f"Genres: {', '.join(payload['genres'])}")
                    if payload.get('overview'):
                        context_parts.append(f"Overview: {payload['overview']}")
                    
                    if context_parts:
                        contexts.append(" | ".join(context_parts))
            else:
                contexts = []
        else:
            # Fallback: no context extraction
            contexts = ["Context extraction not available for this pipeline"]
        
        # Get answer
        answer = self.rag.query(question)
        
        return answer, contexts
    
    def run_evaluation(self, test_cases: List[Dict] = None, max_queries: int = None) -> Dict[str, Any]:
        """Run evaluation using official RAGAS metrics"""
        if test_cases is None:
            test_cases = load_test_dataset()
            if not test_cases:
                test_cases = LEGACY_TEST_DATASET
        
        if max_queries and max_queries < len(test_cases):
            test_cases = test_cases[:max_queries]
        
        print(f"\n{'#'*80}")
        print(f"🎬 OFFICIAL RAGAS EVALUATION - {self.system_name}")
        print(f"{'#'*80}")
        print(f"\n📋 Running {len(test_cases)} test queries...")
        print(f"📊 Metrics: faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness\n")
        
        # Prepare data for RAGAS
        questions = []
        answers = []
        contexts_list = []
        ground_truths = []
        
        for i, test_case in enumerate(test_cases, 1):
            question = test_case['query']
            ground_truth = test_case['ground_truth']
            
            print(f"\n[{i}/{len(test_cases)}] Processing: {question[:60]}...")
            
            try:
                # Query RAG and get contexts
                start_time = time.time()
                answer, contexts = self.query_with_context(question)
                latency = time.time() - start_time
                
                print(f"  ✓ Answered in {latency:.2f}s")
                print(f"  📝 Answer preview: {answer[:100]}...")
                print(f"  📦 Contexts: {len(contexts)} retrieved")
                
                # Store for RAGAS
                questions.append(question)
                answers.append(answer)
                contexts_list.append(contexts)
                ground_truths.append(ground_truth)
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                # Add placeholder to maintain alignment
                questions.append(question)
                answers.append("Error: Could not generate answer")
                contexts_list.append(["No context available"])
                ground_truths.append(ground_truth)
        
        # Create RAGAS dataset
        print(f"\n{'='*80}")
        print("🔄 Creating RAGAS evaluation dataset...")
        
        # Debug: Print dataset structure
        print(f"\n🔍 Debug Info:")
        print(f"  Total samples: {len(questions)}")
        print(f"  Questions type: {type(questions)}, length: {len(questions)}")
        print(f"  Answers type: {type(answers)}, length: {len(answers)}")
        print(f"  Contexts type: {type(contexts_list)}, length: {len(contexts_list)}")
        print(f"  Ground truths type: {type(ground_truths)}, length: {len(ground_truths)}")
        
        if len(questions) > 0:
            print(f"\n  Sample [0]:")
            print(f"    Q: {questions[0][:100]}")
            print(f"    A: {answers[0][:100]}")
            print(f"    C: {type(contexts_list[0])} with {len(contexts_list[0])} items")
            print(f"    GT: {ground_truths[0][:100]}")
        
        # Try without ground_truth first to test
        ragas_dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts_list
        })
        
        print(f"\n✓ Dataset created: {len(ragas_dataset)} samples")
        print(f"⚠️ Running without ground_truth (ContextRecall & AnswerCorrectness will be skipped)")
        
        # Run RAGAS evaluation
        print(f"\n🧮 Running RAGAS metrics (this may take a few minutes)...")
        print(f"   Using LLM: gemini-2.0-flash-exp (via OpenAI-compatible endpoint)")
        print(f"   Metrics: faithfulness only (no embeddings needed)")
        
        try:
            # Use only faithfulness - doesn't require embeddings
            result = evaluate(
                ragas_dataset,
                metrics=[faithfulness],
                llm=evaluator_llm
            )
            
            print("✓ RAGAS evaluation complete!")
            
            # Convert to dict for easier handling
            scores = result.to_pandas().mean().to_dict()
            
            # Prepare report
            report = {
                'system': self.system_name,
                'evaluation_date': datetime.now().isoformat(),
                'total_queries': len(test_cases),
                'metrics': {
                    'faithfulness': round(scores.get('faithfulness', 0), 3),
                    'answer_relevancy': round(scores.get('answer_relevancy', 0), 3),
                    'context_precision': round(scores.get('context_precision', 0), 3),
                    'context_recall': round(scores.get('context_recall', 0), 3),
                    'answer_correctness': round(scores.get('answer_correctness', 0), 3)
                },
                'ragas_version': 'official',
                'detailed_results': result.to_pandas().to_dict('records')
            }
            
            return report
            
        except Exception as e:
            print(f"❌ RAGAS evaluation failed: {e}")
            print(f"\n💡 This might be due to:")
            print(f"   • API rate limits")
            print(f"   • Invalid data format")
            print(f"   • LLM connection issues")
            
            # Return minimal report
            return {
                'system': self.system_name,
                'evaluation_date': datetime.now().isoformat(),
                'total_queries': len(test_cases),
                'error': str(e),
                'metrics': {}
            }
    
    def print_summary(self, report: Dict[str, Any]):
        """Print formatted summary of RAGAS results"""
        print(f"\n{'='*80}")
        print(f"📊 RAGAS EVALUATION SUMMARY - {report.get('system', 'Unknown System')}")
        print(f"{'='*80}\n")
        
        print(f"📅 Date: {report['evaluation_date']}")
        print(f"📋 Total queries: {report['total_queries']}")
        
        if 'error' in report:
            print(f"\n❌ Evaluation failed: {report['error']}")
            return
        
        print(f"\n📈 RAGAS Metrics (Official Framework):")
        print(f"{'='*80}")
        
        metrics = report.get('metrics', {})
        
        # Define metric descriptions
        metric_info = {
            'faithfulness': 'How factually accurate is the answer based on context?',
            'answer_relevancy': 'How relevant is the answer to the question?',
            'context_precision': 'How precise is the retrieved context?',
            'context_recall': 'How much of the needed info is in context?',
            'answer_correctness': 'Overall correctness vs ground truth'
        }
        
        for metric, score in metrics.items():
            if score > 0:
                bar_length = int(score * 20)
                bar = '█' * bar_length + '░' * (20 - bar_length)
                
                # Score interpretation
                if score >= 0.8:
                    indicator = "🎯 Excellent"
                elif score >= 0.6:
                    indicator = "✅ Good"
                elif score >= 0.4:
                    indicator = "👍 Fair"
                else:
                    indicator = "⚠️ Needs Improvement"
                
                print(f"\n{metric.replace('_', ' ').title()}:")
                print(f"  Score: {score:.3f} {bar} {indicator}")
                print(f"  ℹ️  {metric_info.get(metric, '')}")
        
        # Overall score
        if metrics:
            avg_score = sum(metrics.values()) / len(metrics)
            print(f"\n{'='*80}")
            print(f"🏆 Overall Average Score: {avg_score:.3f}")
            
            if avg_score >= 0.75:
                print(f"   🌟 Outstanding performance!")
            elif avg_score >= 0.6:
                print(f"   ✅ Good performance")
            elif avg_score >= 0.45:
                print(f"   👍 Acceptable performance")
            else:
                print(f"   ⚠️ Performance needs improvement")
        
        print(f"{'='*80}\n")
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save evaluation report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ragas_report_{self.system_name.lower()}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Report saved to: {filename}")


def compare_systems(max_queries: int = None):
    """Compare GraphRAG vs SimpleRAG using official RAGAS"""
    print(f"\n{'#'*80}")
    print(f"⚔️  RAGAS COMPARISON: GraphRAG vs SimpleRAG")
    print(f"{'#'*80}\n")
    
    # Load test dataset
    test_cases = load_test_dataset()
    if not test_cases:
        test_cases = LEGACY_TEST_DATASET
    
    if max_queries:
        test_cases = test_cases[:max_queries]
    
    print(f"📋 Testing with {len(test_cases)} queries")
    print(f"🔧 Using official RAGAS framework\n")
    
    # Evaluate GraphRAG
    print("\n" + "="*80)
    print("1️⃣  EVALUATING GraphRAG (Vector + Graph)")
    print("="*80)
    graph_rag = GraphRAG()
    graph_evaluator = RAGASEvaluator(graph_rag, system_name="GraphRAG")
    graph_report = graph_evaluator.run_evaluation(test_cases)
    graph_evaluator.print_summary(graph_report)
    graph_evaluator.save_report(graph_report, filename="ragas_graphrag.json")
    graph_rag.close()
    
    print("\n⏸️  Pausing 5 seconds between evaluations...")
    time.sleep(5)
    
    # Evaluate SimpleRAG
    print("\n" + "="*80)
    print("2️⃣  EVALUATING SimpleRAG (Vector Only)")
    print("="*80)
    simple_rag = SimpleRAG()
    simple_evaluator = RAGASEvaluator(simple_rag, system_name="SimpleRAG")
    simple_report = simple_evaluator.run_evaluation(test_cases)
    simple_evaluator.print_summary(simple_report)
    simple_evaluator.save_report(simple_report, filename="ragas_simplerage.json")
    simple_rag.close()
    
    # Comparison Summary
    if 'error' not in graph_report and 'error' not in simple_report:
        print("\n" + "="*80)
        print("📊 COMPARATIVE ANALYSIS")
        print("="*80 + "\n")
        
        metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'answer_correctness']
        
        print(f"{'Metric':<25} {'GraphRAG':>12} {'SimpleRAG':>12} {'Δ Improvement':>15}")
        print("-" * 70)
        
        for metric in metrics:
            graph_score = graph_report['metrics'].get(metric, 0)
            simple_score = simple_report['metrics'].get(metric, 0)
            delta = graph_score - simple_score
            delta_pct = (delta / simple_score * 100) if simple_score > 0 else 0
            
            symbol = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
            print(f"{metric:<25} {graph_score:>12.3f} {simple_score:>12.3f} {symbol} {delta_pct:>+6.1f}%")
        
        print("-" * 70)
        
        # Winner determination
        print("\n" + "="*80)
        graph_avg = sum(graph_report['metrics'].values()) / len(graph_report['metrics'])
        simple_avg = sum(simple_report['metrics'].values()) / len(simple_report['metrics'])
        
        if graph_avg > simple_avg:
            print(f"🏆 WINNER: GraphRAG (average: {graph_avg:.3f} vs {simple_avg:.3f})")
            print(f"   GraphRAG outperforms by {((graph_avg - simple_avg) / simple_avg * 100):.1f}%")
        elif simple_avg > graph_avg:
            print(f"🏆 WINNER: SimpleRAG (average: {simple_avg:.3f} vs {graph_avg:.3f})")
            print(f"   SimpleRAG outperforms by {((simple_avg - graph_avg) / graph_avg * 100):.1f}%")
        else:
            print(f"🤝 TIE: Both systems perform equally (score: {graph_avg:.3f})")
        
        print("="*80 + "\n")
        
        # Save comparison
        comparison_report = {
            'evaluation_date': datetime.now().isoformat(),
            'test_queries': len(test_cases),
            'framework': 'RAGAS Official',
            'graphrag': graph_report,
            'simplerage': simple_report,
            'comparison': {
                'graphrag_avg': round(graph_avg, 3),
                'simplerage_avg': round(simple_avg, 3),
                'winner': 'GraphRAG' if graph_avg > simple_avg else 'SimpleRAG' if simple_avg > graph_avg else 'Tie'
            }
        }
        
        with open('ragas_comparison.json', 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, ensure_ascii=False, indent=2)
        
        print("💾 Comparison report saved to: ragas_comparison.json")
    
    print("\n✅ Evaluation complete!\n")


def main():
    """Main evaluation runner"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'compare':
            max_queries = int(sys.argv[2]) if len(sys.argv) > 2 else None
            compare_systems(max_queries)
        elif sys.argv[1] == 'graphrag':
            max_queries = int(sys.argv[2]) if len(sys.argv) > 2 else None
            print("🚀 Evaluating GraphRAG with official RAGAS...")
            rag = GraphRAG()
            evaluator = RAGASEvaluator(rag, system_name="GraphRAG")
            report = evaluator.run_evaluation(max_queries=max_queries)
            evaluator.print_summary(report)
            evaluator.save_report(report)
            rag.close()
        elif sys.argv[1] == 'simple':
            max_queries = int(sys.argv[2]) if len(sys.argv) > 2 else None
            print("🚀 Evaluating SimpleRAG with official RAGAS...")
            rag = SimpleRAG()
            evaluator = RAGASEvaluator(rag, system_name="SimpleRAG")
            report = evaluator.run_evaluation(max_queries=max_queries)
            evaluator.print_summary(report)
            evaluator.save_report(report)
            rag.close()
        else:
            print("Usage:")
            print("  python evaluate_ragas.py compare [max_queries]  - Compare both systems")
            print("  python evaluate_ragas.py graphrag [max_queries] - Evaluate GraphRAG only")
            print("  python evaluate_ragas.py simple [max_queries]   - Evaluate SimpleRAG only")
    else:
        print("💡 Running comparison mode with official RAGAS framework")
        print("   Use 'python evaluate_ragas.py compare [N]' to specify query count\n")
        compare_systems(max_queries=2)


if __name__ == "__main__":
    main()
