# RAGAS Evaluation Framework

## Overview

RAGAS (Retrieval Augmented Generation Assessment) framework để đánh giá chất lượng RAG pipeline.

## Metrics

### 1. **Context Relevance** (0-1)
Đo lường mức độ liên quan của database context với query.
- **1.0**: Context hoàn toàn relevant
- **0.5**: Context một phần relevant
- **0.0**: Context không liên quan

### 2. **Faithfulness** (0-1)
Đo lường câu trả lời có trung thực với context không.
- **1.0**: Chỉ dùng thông tin từ context/general knowledge hợp lý
- **0.5**: Có một số hallucination nhẹ
- **0.0**: Nhiều hallucination

### 3. **Answer Relevancy** (0-1)
Đo lường câu trả lời có đáp ứng query không.
- **1.0**: Trả lời hoàn hảo
- **0.5**: Trả lời đúng nhưng thiếu chi tiết
- **0.0**: Không trả lời đúng câu hỏi

### 4. **Answer Correctness** (0-1)
So sánh với ground truth để đánh giá độ chính xác.
- **1.0**: Đúng hoàn toàn
- **0.5**: Đúng một phần
- **0.0**: Sai

## Test Dataset

10 test cases đa dạng covering:
- **Genre Recommendation**: "Phim hay về tình yêu?"
- **Specific Film Info**: "Avatar Fire and Ash ra năm nào?"
- **Similarity Search**: "Phim giống The Shawshank Redemption?"
- **Director/Actor Filmography**: "Christopher Nolan đạo diễn phim nào?"
- **Disambiguation**: "Avatar mới nhất là phần nào?"
- **Theme Search**: "Phim về AI?"
- **Studio Recommendation**: "Phim Ghibli nào đẹp nhất?"

## Usage

### Run Full Evaluation

```bash
python evaluate_ragas.py
```

### Run Specific Test Cases

```python
from evaluate_ragas import RAGASEvaluator, TEST_DATASET
from src.rag_pipeline import GraphRAG

rag = GraphRAG()
evaluator = RAGASEvaluator(rag)

# Run specific categories
genre_tests = [t for t in TEST_DATASET if t['category'] == 'genre_recommendation']
report = evaluator.run_evaluation(genre_tests)
evaluator.print_summary(report)
```

### Custom Test Cases

```python
custom_tests = [
    {
        "query": "Your query here",
        "expected_topics": ["topic1", "topic2"],
        "ground_truth": "Expected answer description",
        "category": "your_category"
    }
]

report = evaluator.run_evaluation(custom_tests)
```

## Output

### Console Output
- Real-time progress for each query
- Metrics for each test case
- Summary statistics
- Category breakdown

### JSON Report
Saved to `evaluation_report_YYYYMMDD_HHMMSS.json`:

```json
{
  "evaluation_date": "2026-01-04T...",
  "total_queries": 10,
  "successful": 10,
  "failed": 0,
  "average_latency_seconds": 3.45,
  "average_metrics": {
    "answer_relevancy": 0.850,
    "answer_correctness": 0.780,
    "context_relevance": 0.750,
    "faithfulness": 0.800
  },
  "detailed_results": [...]
}
```

## Interpreting Results

### Good Performance
- Answer Relevancy > 0.80
- Faithfulness > 0.85
- Context Relevance > 0.70
- Latency < 4s

### Needs Improvement
- Answer Relevancy < 0.60
- Faithfulness < 0.70
- Context Relevance < 0.50
- Latency > 6s

## Limitations

**Current Version (v1):**
- Context extraction simplified (needs pipeline modification for full tracking)
- LLM-as-judge có thể có bias
- Test dataset còn nhỏ (10 queries)

**Future Improvements:**
- Tích hợp context tracking vào pipeline
- Thêm human evaluation
- Expand test dataset to 50+ queries
- Add A/B testing framework
- Implement retrieval metrics (precision, recall)

## Troubleshooting

### Issue: Low Context Relevance
- Check RELEVANCE_THRESHOLD in rag_pipeline.py
- Review vector embeddings quality
- Verify database content coverage

### Issue: Low Faithfulness
- Check if LLM hallucinating
- Review prompt engineering
- Verify context_note instructions

### Issue: High Latency
- Check query cache hit rate
- Review database query optimization
- Consider reducing top_k in vector search

## References

- RAGAS Framework: https://github.com/explodinggradients/ragas
- GraphRAG Paper: https://arxiv.org/abs/2404.16130
