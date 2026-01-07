# MRR/MAP Evaluation System - Complete File Index

## 📊 Core Evaluation Scripts

### [evaluate_mrr_map.py](evaluate_mrr_map.py) (27 KB)
**Main evaluation framework for retrieval ranking quality**

Features:
- Loads 654 movies from crawled database
- Extracts 25-35 test queries from test_datasets/
- Automatically generates ground truth via entity matching
- Calculates 4 key metrics: MRR, MAP@10, Recall@10, NDCG@10
- Compares GraphRAG vs SimpleRAG systems
- Generates JSON reports with detailed statistics

Functions:
- `load_movie_database()` - Load 654 movies with metadata
- `load_test_queries_from_datasets()` - Parse test_datasets/ files
- `RetrievalEvaluator.calculate_mrr()` - Mean Reciprocal Rank
- `RetrievalEvaluator.calculate_map()` - Mean Average Precision
- `RetrievalEvaluator.evaluate_retrieval()` - Full evaluation pipeline
- `RetrievalEvaluator.compare_systems()` - Side-by-side comparison
- `main()` - Execute full evaluation

Usage:
```bash
python evaluate_mrr_map.py
```

### [test_ground_truth_integration.py](test_ground_truth_integration.py) (6.2 KB)
**Standalone validation tool for ground truth quality**

Features:
- Tests ground truth loading without RAG dependencies
- Analyzes quality metrics
- Displays sample queries and relevant documents
- Perfect for quick validation before full evaluation

Usage:
```bash
python test_ground_truth_integration.py
```

---

## 📚 Documentation Files

### [MRR_MAP_EVALUATION.md](MRR_MAP_EVALUATION.md) (8.6 KB)
**Complete metric guide with formulas and examples**

Covers:
- MRR definition, formula, and interpretation
- MAP@10 explanation with examples
- Recall@k, NDCG@k metrics
- Usage examples and best practices
- Advanced usage (custom k values, multi-system comparison)
- Metric comparison table
- Troubleshooting guide

Best for: Understanding what metrics mean and how to interpret them

### [GROUND_TRUTH_INTEGRATION.md](GROUND_TRUTH_INTEGRATION.md) (7.6 KB)
**Ground truth integration details and quality assessment**

Covers:
- Overview of ground truth integration
- Data sources and loading status
- Ground truth quality metrics (60% coverage, 3.84 avg relevant docs)
- Relevance matching strategy
- Usage examples (programmatic and CLI)
- Output file formats with examples
- Troubleshooting and next steps

Best for: Understanding how ground truth is extracted and integrated

### [EVALUATION_ARCHITECTURE.md](EVALUATION_ARCHITECTURE.md) (14 KB)
**System architecture and data flow design**

Covers:
- System overview with ASCII diagrams
- Complete data flow from query to evaluation
- Code organization and file structure
- Movie database structure (654 movies)
- Test query format and processing
- Evaluation report structure
- Integration with GraphRAG/SimpleRAG
- Execution workflow with steps
- Performance characteristics
- Quality metrics

Best for: Understanding how the entire system works end-to-end

### [INTEGRATION_SUMMARY.txt](INTEGRATION_SUMMARY.txt) (8.9 KB)
**Quick reference summary of the complete integration**

Contains:
- Integration overview
- Data sources status (✅/⚠️)
- Ground truth quality metrics
- Relevance matching strategy with example
- Files created/modified
- Quick start commands
- Metric definitions
- Expected output format
- Integration points
- Next steps checklist

Best for: Quick reference and status check

### [QUICKSTART_EVALUATION.sh](QUICKSTART_EVALUATION.sh) (1.2 KB)
**Bash script for quick start commands**

Provides:
- Validation steps
- Quick evaluation command
- Documentation links

---

## 🔗 Integration Points

### Data Sources Used

1. **crawled_data/movies_index.json**
   - 654 movies with full metadata
   - Indexed by movie ID
   - Contains: title, genres, cast, director, overview, rating

2. **test_datasets/*.json** (5 active files)
   - actor_based.json (5 queries)
   - director_based.json (5 queries)
   - multi_hop.json (5 queries)
   - comparison.json (5 queries)
   - temporal_based.json (5 queries)
   - Total: 25 test queries

3. **test_dataset.json**
   - 1000+ queries total
   - Currently loads first 5 as sample
   - Categories: genre, director, actor, theme, etc.

4. **RAG Systems**
   - src/rag_pipeline.py (GraphRAG)
   - src/simple_rag.py (SimpleRAG)

---

## 📊 Metrics Summary

| Metric | Range | Interpretation | Best For |
|--------|-------|-----------------|----------|
| **MRR** | 0-1 | First-result quality | Quick assessment |
| **MAP@10** | 0-1 | Overall ranking quality | Comprehensive evaluation |
| **Recall@10** | 0-1 | Coverage of relevant docs | Checking completeness |
| **NDCG@10** | 0-1 | Position-weighted quality | Most accurate ranking score |

---

## 🚀 Quick Start

### 1. Validate Ground Truth
```bash
python test_ground_truth_integration.py
```

Expected output:
```
✅ Total queries loaded: 25
✅ Total relevant documents: 96
✅ Avg relevant per query: 3.84
```

### 2. Run Full Evaluation
```bash
python evaluate_mrr_map.py
```

Generates:
- `mrr_map_evaluation_graphrag_YYYYMMDD_HHMMSS.json`
- `mrr_map_evaluation_simplerage_YYYYMMDD_HHMMSS.json`
- `mrr_map_comparison_YYYYMMDD_HHMMSS.json`

### 3. Review Results
```bash
# View GraphRAG metrics
cat mrr_map_evaluation_graphrag_*.json | jq '.aggregate_metrics'

# View comparison
cat mrr_map_comparison_*.json | jq '.best_metrics'
```

---

## 📈 Expected Results

From ground truth analysis:

```
Ground Truth Quality:
  • Total queries: 25
  • Queries with relevant docs: 15 (60%)
  • Total relevant documents: 96
  • Average relevant per query: 3.84

Category Breakdown:
  • actor_filmography: 5 queries
  • director_filmography: 5 queries
  • multi_hop: 5 queries
  • comparison: 5 queries
  • temporal_based: 5 queries
```

From evaluation (example):

```json
{
  "mrr": 0.65,
  "map@10": 0.71,
  "recall@10": 0.82,
  "ndcg@10": 0.68,
  "avg_latency_ms": 142.3
}
```

---

## 🎯 File Dependencies

```
evaluate_mrr_map.py
├─ Requires: GraphRAG, SimpleRAG implementations
├─ Reads: crawled_data/movies_index.json
├─ Reads: test_datasets/*.json
├─ Reads: test_dataset.json
└─ Outputs: JSON reports

test_ground_truth_integration.py
├─ Reads: crawled_data/movies_index.json
├─ Reads: test_datasets/*.json
└─ No RAG dependencies (standalone)

MRR_MAP_EVALUATION.md
└─ Reference documentation

GROUND_TRUTH_INTEGRATION.md
└─ Reference documentation

EVALUATION_ARCHITECTURE.md
└─ Reference documentation
```

---

## 🔧 Customization

### Add More Test Queries
```python
# In evaluate_mrr_map.py, modify load_test_queries_from_datasets():
# Change: test_cases[:5]  →  test_cases[:20]
```

### Change K Value for Metrics
```python
# In evaluate_mrr_map.py:
map_score = evaluator.calculate_map(docs, relevant_ids, k=20)  # Default is 10
```

### Add Custom Categories
```python
# In evaluate_mrr_map.py, update dataset_files dict:
'test_datasets/custom.json': 'custom_category',
```

---

## ✅ Checklist

- [x] Ground truth extraction implemented
- [x] Movie database integration (654 movies)
- [x] Test dataset loading (25 queries)
- [x] MRR calculation
- [x] MAP@10 calculation
- [x] Recall@10 calculation
- [x] NDCG@10 calculation
- [x] System comparison
- [x] JSON report generation
- [x] Documentation complete
- [x] Standalone validation tool
- [x] Quick start guide

---

## 📞 Support

For issues:
1. Check GROUND_TRUTH_INTEGRATION.md Troubleshooting section
2. Run test_ground_truth_integration.py to validate
3. Review EVALUATION_ARCHITECTURE.md for data flow
4. Check MRR_MAP_EVALUATION.md for metric details

---

## 📝 Last Updated

January 6, 2026

Total Lines of Code: ~1000
Documentation: ~45 KB
Test Coverage: 25 queries across 5 categories
