# Manual RAGAS Evaluation - Usage Guide

## 📚 Tổng quan

Script đánh giá chất lượng RAG system sử dụng **Manual RAGAS metrics** với LLM-as-Judge approach. Hỗ trợ nhiều datasets và metrics nâng cao.

---

## 🎯 Tính năng

### ✅ Metrics (7 total)
**Core Metrics (5):**
1. **Faithfulness** - Không hallucination
2. **Answer Relevancy** - Trả lời đúng câu hỏi
3. **Context Precision** - Retrieval chất lượng cao
4. **Context Recall** - Retrieval đầy đủ
5. **Answer Correctness** - Chính xác so với ground truth

**New Metrics (2):**
6. **Response Completeness** 🆕 - User satisfaction
7. **Source Attribution** 🆕 - Traceability

### ✅ Dataset Support
- Load từ folder `test_datasets/`
- Chọn dataset cụ thể hoặc "all"
- Hỗ trợ format chuẩn với metadata

### ✅ Weighted Scoring
- Critical metrics có trọng số cao hơn
- Overall weighted score + simple average
- Transparent reasoning từ LLM

---

## 📁 Dataset Structure

Folder `test_datasets/` chứa các datasets:
```
test_datasets/
├── actor_based.json          # Queries về diễn viên
├── comparison.json            # So sánh phim/đạo diễn
├── director_based.json        # Queries về đạo diễn
├── genre_recommendation.json  # Gợi ý theo thể loại
├── multi_hop.json             # Multi-hop reasoning
├── specific_film_info.json    # Thông tin phim cụ thể
└── temporal_based.json        # Queries về thời gian
```

**Dataset Format:**
```json
{
  "category": "actor_based",
  "description": "Queries about actors...",
  "test_cases": [
    {
      "id": 1,
      "query": "Which actors have worked with Nolan?",
      "entities": ["Christopher Nolan"],
      "relations": ["ACTED_IN", "DIRECTED_BY"],
      "complexity": "high",
      "ground_truth": "..." // Optional
    }
  ]
}
```

---

## 🚀 Usage

### 1. List Available Datasets
```bash
python manual_ragas_evaluation.py
```

**Output:**
```
📚 Available datasets:
   1. actor_based.json
   2. comparison.json
   3. director_based.json
   ...
```

---

### 2. Evaluate Single Dataset

#### Tất cả queries trong dataset
```bash
python manual_ragas_evaluation.py --dataset actor_based.json
```

#### Giới hạn số lượng queries
```bash
python manual_ragas_evaluation.py --dataset actor_based.json --num 5
```

#### Short form
```bash
python manual_ragas_evaluation.py -d comparison.json -n 3
```

---

### 3. Evaluate ALL Datasets

#### All queries from all datasets
```bash
python manual_ragas_evaluation.py --dataset all
```

#### First N queries from each dataset
```bash
python manual_ragas_evaluation.py --dataset all --num 3
```

**Output:**
```
📚 Loading ALL datasets (7 total):
   ✓ actor_based.json: 3 queries
   ✓ comparison.json: 3 queries
   ✓ director_based.json: 3 queries
   ...

✅ Total loaded: 21 queries
```

---

### 4. Custom Dataset Directory
```bash
python manual_ragas_evaluation.py \
  --dataset actor_based.json \
  --datasets-dir my_custom_datasets/
```

---

## 📊 Execution Flow

### Step 1: Configuration
```
🔬 Manual RAGAS Evaluation (Enhanced)
GraphRAG vs SimpleRAG Comparison with LLM-as-Judge
================================================================================

📊 Evaluation Plan:
   • Total queries: 15
   • Categories:
      - actor_based: 5 queries
      - comparison: 10 queries
   • Metrics: 7 (5 core + 2 new)
   • Estimated time: ~30 minutes

⚠️  This will evaluate 15 queries. Continue? (y/n):
```

### Step 2: System Initialization
```
🚀 Initializing RAG systems...
   Connecting to Qdrant...
   Connecting to Neo4j...
   Loading embedding model...
✓ Systems ready
```

### Step 3: Query Evaluation
```
────────────────────────────────────────────────────────────────────────────────
Query 1/15
Category: actor_based
Complexity: high
────────────────────────────────────────────────────────────────────────────────

[Query 1] Which actors have worked with Christopher Nolan multiple times?
Category: actor_based

  🔷 GraphRAG:
    → Evaluating: Which actors have worked with Christopher Nola...

    📝 FULL ANSWER:
    ────────────────────────────────────────────────────────────────────────────────
    Christian Bale, Michael Caine, Tom Hardy, and Cillian Murphy have all 
    collaborated with Christopher Nolan on multiple films...
    ────────────────────────────────────────────────────────────────────────────────

    📚 CONTEXTS (3 total):
       1. Title: The Dark Knight | Director: Christopher Nolan...
       2. Title: Inception | Director: Christopher Nolan...
       3. Title: Interstellar | Director: Christopher Nolan...

      • Faithfulness... 0.950
      • Answer Relevancy... 0.920
      • Context Precision... 0.867
      • Context Recall... 0.800
      • Answer Correctness... 0.880
      • Response Completeness (NEW)... 0.900
      • Source Attribution (NEW)... 0.750

      ⭐ Overall Score (weighted): 0.882
      ⭐ Overall Score (simple): 0.867

  🔶 SimpleRAG:
    [Similar output...]

  📊 Comparison:
    GraphRAG Overall (weighted): 0.882
    SimpleRAG Overall (weighted): 0.756
    GraphRAG Overall (simple): 0.867
    SimpleRAG Overall (simple): 0.743
    🏆 Winner: GraphRAG

⏳ Progress: 1/15 completed (6.7%)
```

### Step 4: Final Report
```
================================================================================
📈 GENERATING FINAL REPORT
================================================================================

================================================================================
🔬 MANUAL RAGAS EVALUATION REPORT (Enhanced v2.0)
================================================================================

Metric                         GraphRAG        SimpleRAG       Improvement    
--------------------------------------------------------------------------------
📊 Core Metrics:
  faithfulness                 0.9240          0.8120          +13.79%
  answer_relevancy             0.9010          0.8450          +6.63%
  context_precision            0.8650          0.7230          +19.64%
  context_recall               0.8320          0.7890          +5.45%
  answer_correctness           0.8980          0.8210          +9.38%

🆕 New Metrics:
  response_completeness        0.8870          0.7980          +11.15%
  source_attribution           0.7650          0.6420          +19.16%

⭐ Overall Scores:
  overall_weighted             0.8821          0.7858          +12.25%
  overall_simple               0.8674          0.7757          +11.82%

✓ Report saved to: manual_ragas_report_actor_based_20260106_153042.json

✅ Evaluation complete!
📁 Report saved: manual_ragas_report_actor_based_20260106_153042.json
📊 Queries evaluated: 15

📈 Quick Summary:
   • GraphRAG: 0.882
   • SimpleRAG: 0.786
   • Winner: GraphRAG 🏆

================================================================================
```

---

## 📄 Output Files

### Report Format
```json
{
  "metadata": {
    "evaluation_date": "2026-01-06 15:30:42",
    "total_queries": 15,
    "method": "Manual RAGAS Implementation (LLM-as-Judge) v2.0 Enhanced",
    "metrics_count": 7,
    "new_metrics": ["response_completeness", "source_attribution"]
  },
  "graphrag_metrics": {
    "faithfulness": 0.924,
    "answer_relevancy": 0.901,
    "context_precision": 0.865,
    "context_recall": 0.832,
    "answer_correctness": 0.898,
    "response_completeness": 0.887,
    "source_attribution": 0.765,
    "overall_weighted": 0.882,
    "overall_simple": 0.867
  },
  "simplerag_metrics": { ... },
  "improvements": {
    "faithfulness": 13.79,
    "answer_relevancy": 6.63,
    ...
  },
  "detailed_results": [
    {
      "query_id": 1,
      "question": "Which actors...",
      "category": "actor_based",
      "complexity": "high",
      "graphrag": {
        "answer": "...",
        "contexts_count": 5,
        "metrics": { ... }
      },
      "simplerag": { ... },
      "winner": "GraphRAG"
    }
  ]
}
```

### File Naming
```
manual_ragas_report_{dataset}_{timestamp}.json

Examples:
- manual_ragas_report_actor_based_20260106_153042.json
- manual_ragas_report_all_20260106_160530.json
- manual_ragas_report_comparison_20260106_143210.json
```

---

## ⚙️ Configuration

### Debug Mode
Hiển thị LLM reasoning:
```python
# In code:
evaluator.debug_mode = True   # Show detailed reasoning
evaluator.debug_mode = False  # Clean output only
```

### Retry Settings
```python
# In _call_llm_with_retry():
max_retries = 3  # Number of retries on API failure
```

### Metric Weights
```python
# In evaluate_single():
weights = {
    'faithfulness': 1.5,          # Critical
    'answer_relevancy': 1.5,      # Critical
    'answer_correctness': 1.5,    # Critical
    'context_precision': 1.0,     # Important
    'context_recall': 1.0,        # Important
    'response_completeness': 0.8, # Nice to have
    'source_attribution': 0.7     # Nice to have
}
```

---

## 📈 Performance

| Aspect | Value |
|--------|-------|
| **Time per query** | ~2 minutes |
| **LLM calls per query** | 14 (7 metrics × 2 systems) |
| **Token usage per query** | ~4,000-6,000 tokens |
| **Rate limiting** | 2s between queries |

**Estimated times:**
- 5 queries: ~10 minutes
- 10 queries: ~20 minutes
- 20 queries: ~40 minutes
- All datasets (~50 queries): ~100 minutes

---

## 🛠️ Troubleshooting

### Issue: "No datasets found"
**Solution:**
```bash
# Check directory exists
ls test_datasets/

# Specify custom directory
python manual_ragas_evaluation.py --datasets-dir path/to/datasets/
```

### Issue: API rate limits
**Solution:**
```python
# Increase delay in main():
time.sleep(3)  # Instead of 2 seconds
```

### Issue: Evaluation hangs
**Solution:**
- Check LLM API key valid
- Check timeout settings (default 30s)
- Enable debug mode to see where it hangs

### Issue: Low scores across the board
**Possible causes:**
- Poor retrieval quality
- Incomplete contexts
- Check individual metric scores to diagnose

---

## 💡 Best Practices

1. **Start Small**: Test with `--num 3` first
2. **Debug Mode**: Enable for first run to understand scoring
3. **Ground Truth**: Provide when available for better accuracy
4. **Dataset Selection**: Start with specific datasets before "all"
5. **Save Reports**: Keep reports for comparison over time

---

## 📚 Examples

### Quick Test (3 queries)
```bash
python manual_ragas_evaluation.py -d actor_based.json -n 3
```

### Full Dataset
```bash
python manual_ragas_evaluation.py -d comparison.json
```

### All Datasets (Sample)
```bash
python manual_ragas_evaluation.py --dataset all --num 2
```

### Production Evaluation
```bash
# All queries from specific categories
python manual_ragas_evaluation.py -d multi_hop.json > eval_multihop.log 2>&1
```

---

## 🔗 Related Files

- `manual_ragas_evaluation.py` - Main script
- `RAGAS_IMPROVEMENTS.md` - Detailed improvements documentation
- `test_datasets/*.json` - Dataset files
- `manual_ragas_report_*.json` - Output reports

---

## 📝 Notes

- **Cost**: ~$0.10-0.20 per 10 queries (Gemini API)
- **Accuracy**: LLM-based, scores may vary slightly between runs
- **Bias**: Weighted scores favor critical metrics (faithfulness, relevancy, correctness)

---

## 🚀 Future Enhancements

- [ ] Parallel query evaluation
- [ ] HTML report generation
- [ ] Confidence intervals for scores
- [ ] Category-specific weights
- [ ] Interactive mode for query selection

---

**Last Updated**: January 6, 2026  
**Version**: 2.0 (Enhanced with dataset support)
