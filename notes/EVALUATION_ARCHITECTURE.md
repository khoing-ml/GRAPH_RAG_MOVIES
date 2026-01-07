# MRR/MAP Evaluation Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  MRR/MAP Evaluation System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Ground Truth Integration Layer                  │   │
│  │                                                            │   │
│  │  📂 test_datasets/                                         │   │
│  │     ├── actor_based.json      (5 queries)               │   │
│  │     ├── director_based.json   (5 queries)               │   │
│  │     ├── multi_hop.json        (5 queries)               │   │
│  │     ├── comparison.json       (5 queries)               │   │
│  │     └── temporal_based.json   (5 queries)               │   │
│  │                                                            │   │
│  │  📄 test_dataset.json         (1000+ queries)            │   │
│  │                                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │      Relevance Matching Engine                            │   │
│  │                                                            │   │
│  │  1. Extract query entities                                │   │
│  │  2. Load 654 movies from crawled database                │   │
│  │  3. Match entities to movie metadata:                    │   │
│  │     • Title matching                                      │   │
│  │     • Director matching                                   │   │
│  │     • Cast matching                                       │   │
│  │     • Genre matching                                      │   │
│  │     • Overview matching                                   │   │
│  │  4. Build ground truth (relevant_doc_ids)                │   │
│  │                                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Evaluation Engine (RetrievalEvaluator)            │   │
│  │                                                            │   │
│  │  For each test query:                                      │   │
│  │  1. Retrieve documents (k=10)                            │   │
│  │  2. Calculate MRR                                         │   │
│  │  3. Calculate MAP@10                                      │   │
│  │  4. Calculate Recall@10                                   │   │
│  │  5. Calculate NDCG@10                                     │   │
│  │                                                            │   │
│  │  Compare:                                                  │   │
│  │  • GraphRAG vs SimpleRAG                                  │   │
│  │  • By category (actor, director, multi_hop, etc)         │   │
│  │  • Aggregate statistics                                    │   │
│  │                                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           JSON Report Generation                           │   │
│  │                                                            │   │
│  │  📄 mrr_map_evaluation_graphrag_YYYYMMDD_HHMMSS.json      │   │
│  │  📄 mrr_map_evaluation_simplerage_YYYYMMDD_HHMMSS.json    │   │
│  │  📄 mrr_map_comparison_YYYYMMDD_HHMMSS.json               │   │
│  │                                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Ground Truth Extraction

```python
Query: "Which actors have worked with Christopher Nolan?"
Entities: ["Christopher Nolan"]

↓ (Relevance Matching)

Movie Database Scan (654 movies):
  • Inception → Director: "Christopher Nolan" ✓
  • The Dark Knight → Director: "Christopher Nolan" ✓
  • Interstellar → Director: "Christopher Nolan" ✓
  • Oppenheimer → Director: "Christopher Nolan" ✓
  • Random movie → Director: "Other" ✗

↓

Ground Truth Output:
{
  "relevant_doc_ids": ["inception", "the_dark_knight", "interstellar", "oppenheimer"],
  "count": 4
}
```

### 2. Evaluation Flow

```python
Test Query: {
  "query": "Which actors have worked with Christopher Nolan?",
  "relevant_doc_ids": ["inception", "the_dark_knight", "interstellar", "oppenheimer"],
  "category": "actor_filmography"
}

↓ (Retrieve)

RAG System (GraphRAG):
  retrieve(query, k=10)
  → [
      {"id": "inception", "title": "Inception", ...},
      {"id": "other_movie", ...},
      {"id": "the_dark_knight", ...},
      ...
    ]

↓ (Evaluate)

Metrics Calculation:
  MRR = 1/1 = 1.0 (first result is relevant)
  MAP@10 = (1.0 + 0.67) / 4 = 0.42 (positions 1, 3 relevant)
  Recall@10 = 2/4 = 0.5 (found 2 of 4 relevant docs)
  NDCG@10 = 0.65 (position-weighted)

↓

Report Entry:
{
  "query_id": 1,
  "query": "Which actors have worked with Christopher Nolan?",
  "mrr": 1.0,
  "map@10": 0.42,
  "recall@10": 0.5,
  "ndcg@10": 0.65,
  "success": true
}
```

## Code Organization

### Files Created

```
evaluate_mrr_map.py (642 lines)
├── load_movie_database()
├── load_test_queries_from_datasets()
├── load_test_queries_with_relevance()
├── RetrievalEvaluator class
│   ├── calculate_mrr()
│   ├── calculate_map()
│   ├── calculate_recall_at_k()
│   ├── calculate_ndcg()
│   ├── evaluate_retrieval()
│   ├── print_summary()
│   ├── compare_systems()
│   └── save_report()
└── main()

test_ground_truth_integration.py (standalone test utility)
├── load_movie_database()
├── load_test_queries_from_datasets()
├── analyze_ground_truth()
└── main()
```

### Documentation Files

```
MRR_MAP_EVALUATION.md
├── Metric explanations with formulas
├── Usage examples
├── Output format
└── Troubleshooting

GROUND_TRUTH_INTEGRATION.md
├── Integration summary
├── Data sources
├── Ground truth quality metrics
├── Relevance matching strategy
└── Next steps

QUICKSTART_EVALUATION.sh
└── Quick start guide
```

## Database Structure

### Movie Database (654 movies)

```json
{
  "total_movies": 654,
  "crawl_date": "2026-01-05",
  "movies": {
    "inception": {
      "id": "inception",
      "title": "Inception",
      "release_date": "2010-07-16",
      "genres": ["Sci-Fi", "Thriller", "Action"],
      "director": "Christopher Nolan",
      "cast": ["Leonardo DiCaprio", "Marion Cotillard", ...],
      "overview": "A skilled thief who steals corporate secrets...",
      "rating": 8.8
    },
    ...
  }
}
```

## Test Query Structure

### From test_datasets/*.json

```json
{
  "category": "actor_filmography",
  "description": "Complex queries about actors...",
  "test_cases": [
    {
      "id": 1,
      "query": "Which actors have worked with Christopher Nolan multiple times?",
      "entities": ["Christopher Nolan"],
      "relations": ["ACTED_IN", "DIRECTED_BY"],
      "complexity": "high"
    }
  ]
}
```

### Processed Format (After Ground Truth Extraction)

```json
{
  "id": 1,
  "query": "Which actors have worked with Christopher Nolan multiple times?",
  "category": "actor_filmography",
  "relevant_doc_ids": ["inception", "the_dark_knight", "interstellar", "oppenheimer"],
  "entities": ["Christopher Nolan"],
  "complexity": "high",
  "expected_answer": ""
}
```

## Evaluation Report Structure

### Individual Query Result

```json
{
  "query_id": 1,
  "query": "Which actors have worked with Christopher Nolan...",
  "category": "actor_filmography",
  "relevant_count": 4,
  "retrieved_count": 10,
  "mrr": 0.75,
  "map@10": 0.42,
  "recall@10": 0.5,
  "ndcg@10": 0.58,
  "latency_ms": 145.5,
  "success": true
}
```

### Aggregate Metrics

```json
{
  "aggregate_metrics": {
    "total_queries": 25,
    "successful_queries": 24,
    "failed_queries": 1,
    "metrics": {
      "mrr": 0.65,
      "map@10": 0.71,
      "recall@10": 0.82,
      "ndcg@10": 0.68,
      "avg_latency_ms": 142.3
    },
    "category_breakdown": {
      "actor_filmography": {
        "count": 5,
        "mrr": 0.73,
        "map@10": 0.76,
        "recall@10": 0.85,
        "ndcg@10": 0.72
      }
    }
  }
}
```

## Integration with RAG Systems

### GraphRAG Integration

```python
from src.rag_pipeline import GraphRAG

rag = GraphRAG()
retrieved_docs = rag.retrieve(query, k=10)
# Expected format: List[Dict] with 'id', 'title', 'score' keys
```

### SimpleRAG Integration

```python
from src.simple_rag import SimpleRAG

rag = SimpleRAG()
retrieved_docs = rag.retrieve(query, k=10)
# Same format as GraphRAG
```

## Execution Workflow

```
1. Load Movie Database (654 movies)
   ↓
2. Load Test Datasets (25 queries)
   ↓
3. Extract Ground Truth (match entities to movies)
   ↓
4. Evaluate GraphRAG
   ├─ Retrieve documents for each query
   ├─ Calculate metrics (MRR, MAP, Recall, NDCG)
   ├─ Aggregate results
   └─ Generate report
   ↓
5. Evaluate SimpleRAG
   ├─ Same as GraphRAG
   └─ Generate report
   ↓
6. Compare Systems
   ├─ Side-by-side metrics
   ├─ Best system per metric
   └─ Generate comparison report
   ↓
7. Output JSON Reports
   ├─ mrr_map_evaluation_graphrag_*.json
   ├─ mrr_map_evaluation_simplerage_*.json
   └─ mrr_map_comparison_*.json
```

## Performance Characteristics

### Time Complexity

```
Ground Truth Extraction:
  O(T × M) where:
    T = number of test queries = 25
    M = number of movies = 654
  → ~16,350 comparisons

Evaluation Per Query:
  O(K × R) where:
    K = top-k results = 10
    R = relevant documents = avg 3.84
  → ~38 comparisons per query
  → ~950 total for 25 queries

Total:
  Ground truth: ~1-2 seconds
  Evaluation: ~3-5 seconds (depends on retriever)
  Report generation: <1 second
  → ~4-8 seconds total
```

### Space Complexity

```
Movie Database: ~1.5 MB (654 movies in memory)
Test Queries: ~50 KB (25 queries)
Report Output: ~100 KB per report
```

## Quality Metrics

### Current Ground Truth Quality

```
✅ Coverage: 60% of queries have relevant documents
✅ Relevance: 3.84 avg relevant docs per query
✅ Balance: Evenly distributed across categories
✅ Complexity: Mix of simple to very_high complexity
```

### Evaluation Metrics Properties

```
MRR:   Ranges [0, 1], captures first-result quality
MAP:   Ranges [0, 1], comprehensive ranking quality
Recall: Ranges [0, 1], shows coverage
NDCG:  Ranges [0, 1], position-aware ranking quality
```

## Future Enhancements

1. **Semantic Matching**: Use embeddings instead of keyword matching
2. **Manual Curation**: Add hand-picked ground truth for edge cases
3. **Relevance Grading**: Use 0/1/2 grades instead of binary
4. **More Queries**: Expand from 25 to 100+ test queries
5. **Cross-validation**: k-fold evaluation
6. **Statistical Testing**: Significance tests between systems
