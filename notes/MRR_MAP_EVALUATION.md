# MRR/MAP Retrieval Evaluation Guide

## Overview

This guide covers evaluating retrieval ranking quality using **MRR** and **MAP** metrics, plus related metrics for comprehensive retrieval system assessment.

## Metrics Explained

### 1. **MRR (Mean Reciprocal Rank)**

Measures position of first relevant document in ranking.

$$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$

- **Range**: 0-1
- **Interpretation**:
  - 1.0: First result is relevant
  - 0.5: Second result is relevant
  - 0.333: Third result is relevant
  - 0.0: No relevant results

**Example**:
```
Query: "Best romance movies?"
Relevant: [the_notebook, la_la_land, titanic]

Results:
1. the_notebook ✓ (relevant)  → MRR = 1/1 = 1.0
2. action_movie
3. la_la_land ✓ (relevant)
```

### 2. **MAP (Mean Average Precision)**

Measures ranking quality across all relevant documents.

$$\text{MAP} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\min(m_i, k)} \sum_{j=1}^{k} P(j) \times \text{rel}(j)$$

- **Range**: 0-1
- **Interpretation**:
  - 1.0: All relevant docs retrieved in perfect order
  - 0.5: Half of relevant docs retrieved correctly
  - 0.0: No relevant docs retrieved

**Example**:
```
Query: "Best romance movies?"
Relevant: [the_notebook, la_la_land, titanic]
Top-10 results needed

Results with relevance:
Rank 1: the_notebook ✓      (P@1 = 1/1 = 1.00)
Rank 2: action_movie ✗
Rank 3: la_la_land ✓        (P@3 = 2/3 = 0.67)
Rank 4: sci_fi_movie ✗
Rank 5: titanic ✓           (P@5 = 3/5 = 0.60)
Rank 6-10: other movies

MAP = (1.00 + 0.67 + 0.60) / 3 = 0.76
```

### 3. **Recall@k**

Proportion of relevant documents retrieved in top-k results.

$$\text{Recall@k} = \frac{\text{relevant retrieved in top-k}}{\text{total relevant documents}}$$

- **Range**: 0-1
- **Example**: Recall@10 = 3/5 = 0.6 (found 3 out of 5 relevant docs in top-10)

### 4. **NDCG@k (Normalized Discounted Cumulative Gain)**

Accounts for position decay and relevance grading. Normalized by ideal ranking.

$$\text{NDCG@k} = \frac{\text{DCG@k}}{\text{IDCG@k}}$$

$$\text{DCG@k} = \sum_{i=1}^{k} \frac{\text{rel}_i}{\log_2(i+1)}$$

- **Range**: 0-1
- **Accounts for**: Ranking position (better results higher weighted)
- **Better for**: Graded relevance, not binary

## Usage

### Run Evaluation

```bash
python evaluate_mrr_map.py
```

### Programmatic Usage

```python
from evaluate_mrr_map import RetrievalEvaluator

# Create evaluator
evaluator = RetrievalEvaluator()

# Prepare test queries with ground truth
test_queries = [
    {
        "query": "Best romance movies?",
        "category": "genre_recommendation",
        "relevant_doc_ids": ["the_notebook", "la_la_land", "titanic"],
        "expected_answer": "..."
    },
    # ... more queries
]

# Evaluate GraphRAG
graphrag_report = evaluator.evaluate_retrieval(
    test_queries, 
    rag_type='graphrag'
)

# Evaluate SimpleRAG
simplerage_report = evaluator.evaluate_retrieval(
    test_queries, 
    rag_type='simplerage'
)

# Compare systems
comparison = evaluator.compare_systems([graphrag_report, simplerage_report])
```

### Custom Metrics

```python
# Manual calculation
docs = rag.retrieve("query", k=10)
relevant_ids = ["doc1", "doc2", "doc3"]

mrr = evaluator.calculate_mrr(docs, relevant_ids)
map_score = evaluator.calculate_map(docs, relevant_ids, k=10)
recall = evaluator.calculate_recall_at_k(docs, relevant_ids, k=10)
ndcg = evaluator.calculate_ndcg(docs, relevant_ids, k=10)
```

## Ground Truth Preparation

For accurate evaluation, you need ground truth relevance labels:

```json
{
  "query": "What is Christopher Nolan's best film?",
  "category": "director_filmography",
  "relevant_doc_ids": ["inception", "interstellar", "the_dark_knight", "oppenheimer"],
  "expected_answer": "Christopher Nolan's critically acclaimed films"
}
```

### Sources for Ground Truth:

1. **Manual Annotation**: Domain experts label relevant documents
2. **User Behavior**: Track which results users click on
3. **External Datasets**: Use TMDB, IMDb, Rotten Tomatoes ratings
4. **Crowdsourcing**: Amazon Mechanical Turk, Upwork
5. **Hybrid Approach**: Combine multiple sources

## Interpretation Guidelines

### MRR Interpretation

| Score | Meaning |
|-------|---------|
| 0.9-1.0 | Excellent - First result almost always relevant |
| 0.7-0.9 | Very Good - Relevant result in top 2 |
| 0.5-0.7 | Good - Relevant result in top 3 |
| 0.3-0.5 | Fair - Relevant result in top 5 |
| 0.0-0.3 | Poor - Relevant result only in top 10+ |

### MAP Interpretation

| Score | Meaning |
|-------|---------|
| 0.9-1.0 | Excellent - All relevant docs ranked well |
| 0.7-0.9 | Very Good - Most relevant docs in top positions |
| 0.5-0.7 | Good - ~70% precision in ranking |
| 0.3-0.5 | Fair - Relevant docs scattered in results |
| 0.0-0.3 | Poor - Few relevant docs found |

### Combined Interpretation

- **High MRR + High MAP**: Perfect ranking, first result is relevant, others follow
- **High MRR + Low MAP**: First result relevant, but others poorly ranked
- **Low MRR + High MAP**: Relevant docs exist but not early, but overall good ranking
- **Low MRR + Low MAP**: Poor retrieval system

## Output Files

After evaluation, check:

1. **mrr_map_evaluation_graphrag_YYYYMMDD_HHMMSS.json** - GraphRAG metrics
2. **mrr_map_evaluation_simplerage_YYYYMMDD_HHMMSS.json** - SimpleRAG metrics
3. **mrr_map_comparison_YYYYMMDD_HHMMSS.json** - System comparison

### Report Structure

```json
{
  "rag_type": "graphrag",
  "timestamp": "2026-01-06T...",
  "query_results": [
    {
      "query_id": 1,
      "query": "...",
      "category": "...",
      "mrr": 0.5,
      "map@10": 0.62,
      "recall@10": 0.75,
      "ndcg@10": 0.58,
      "latency_ms": 145.5,
      "success": true
    }
  ],
  "aggregate_metrics": {
    "total_queries": 10,
    "successful_queries": 10,
    "metrics": {
      "mrr": 0.65,
      "map@10": 0.71,
      "recall@10": 0.82,
      "ndcg@10": 0.68,
      "avg_latency_ms": 142.3
    },
    "category_breakdown": {
      "genre_recommendation": {
        "count": 3,
        "mrr": 0.73,
        "map@10": 0.76
      }
    }
  }
}
```

## Advanced Usage

### Evaluate Specific Categories

```python
# Filter by category
genre_queries = [q for q in test_queries 
                 if q['category'] == 'genre_recommendation']

report = evaluator.evaluate_retrieval(genre_queries, rag_type='graphrag')
```

### Custom K Values

```python
# Evaluate at different cutoff points
map_at_5 = evaluator.calculate_map(docs, relevant_ids, k=5)
map_at_10 = evaluator.calculate_map(docs, relevant_ids, k=10)
map_at_20 = evaluator.calculate_map(docs, relevant_ids, k=20)

recall_at_5 = evaluator.calculate_recall_at_k(docs, relevant_ids, k=5)
recall_at_10 = evaluator.calculate_recall_at_k(docs, relevant_ids, k=10)
```

### Multi-system Comparison

```python
# Compare 3+ systems
systems_to_compare = [
    graphrag_report,
    simplerage_report,
    another_rag_report
]

comparison = evaluator.compare_systems(systems_to_compare)
```

## Best Practices

1. **Use Consistent Ground Truth**: Same relevant docs for all systems
2. **Large Query Set**: Min 50-100 queries for statistical significance
3. **Multiple Categories**: Evaluate across different query types
4. **Track Variance**: Report standard deviation alongside means
5. **A/B Testing**: Use evaluation results for system comparison
6. **Regular Evaluation**: Re-evaluate after system changes
7. **Error Analysis**: Review failed queries to identify patterns

## Comparison with Other Metrics

| Metric | Use Case | Pros | Cons |
|--------|----------|------|------|
| MRR | First-result quality | Simple, interpretable | Ignores other results |
| MAP | Overall ranking quality | Comprehensive | Requires all relevant docs |
| Recall@k | Coverage | Easy to understand | Doesn't account for ranking |
| NDCG@k | Graded relevance | Flexible, position-aware | More complex |
| Precision@k | Top-k quality | Simple | Ignores recall |

## Troubleshooting

### Low MRR/MAP Scores

1. **Check ground truth quality**: Are relevant_doc_ids accurate?
2. **Verify document IDs**: Do they match retrieval output format?
3. **Review retrieval logic**: Is `rag.retrieve()` working correctly?
4. **Increase k**: Try k=20 or k=50 to see if docs appear later
5. **Analyze queries**: Are some queries inherently harder?

### Zero Scores

- No retrieved documents? Check retrieval pipeline
- Documents not matching? Verify ID format consistency
- Wrong IDs? Compare with actual database

## References

- [TREC Evaluation Metrics](https://trec.nist.gov/)
- [Information Retrieval Metrics](https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval))
- [RAGAS Framework](https://docs.ragas.io/)
- [BEIR Benchmark](https://arxiv.org/abs/2104.08663)
