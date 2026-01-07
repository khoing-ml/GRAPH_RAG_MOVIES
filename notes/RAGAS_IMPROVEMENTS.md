# Cải tiến Manual RAGAS Metrics

## 📋 Tổng quan cải tiến

File `manual_ragas_evaluation.py` đã được nâng cấp toàn diện với các cải tiến về prompting, reliability và thêm metrics mới.

---

## 🎯 Cải tiến chính

### 1. **Enhanced Prompting Strategy**

#### ✅ Chain-of-Thought Reasoning
- **Trước**: LLM chỉ trả về score đơn thuần
- **Sau**: Yêu cầu LLM giải thích reasoning trước khi chấm điểm

**Format mới:**
```
REASONING: [Detailed analysis step-by-step]
SCORE: [0.0-1.0]
```

**Lợi ích:**
- ✅ Transparency - Hiểu được cơ sở đánh giá
- ✅ Debugging - Dễ phát hiện lỗi logic của LLM
- ✅ Consistency - Reasoning giúp scores ổn định hơn

---

### 2. **Improved Error Handling & Retry Logic**

#### 🔄 `_call_llm_with_retry()` Method
```python
def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> tuple[float, str]:
    """
    Gọi LLM với retry tự động
    Returns: (score, reasoning_text)
    """
```

**Cải tiến:**
- Retry tối đa 3 lần khi API fail
- Extract score từ nhiều format khác nhau
- Fallback về 0.5 nếu hoàn toàn fail
- Trả về cả reasoning để debug

---

### 3. **Enhanced Metric Prompts**

#### 📊 Faithfulness (Improved)
**Cải tiến:**
- ✅ Claim-by-claim analysis requirement
- ✅ Concrete examples của hallucination
- ✅ Detailed rubric (0.4, 0.6, 0.7, 0.8, 0.9, 1.0)
- ✅ Chain-of-thought instructions

**Scoring Rubric:**
```
1.0 = Perfect (100% claims supported)
0.9 = Excellent (>90% supported)
0.8 = Good (80-90% supported)
0.7 = Fair (70-80% supported)
0.6 = Mediocre (60-70% supported)
<0.6 = Poor (majority hallucinated)
```

---

#### 🎯 Answer Relevancy (Improved)
**Multi-aspect evaluation:**
1. **DIRECTNESS** - Trả lời đúng câu hỏi?
2. **COMPLETENESS** - Đầy đủ thông tin?
3. **FOCUS** - Tập trung, không lan man?

**Examples trong prompt:**
```
Question: "Who directed Inception?"
Answer: "Christopher Nolan" → 1.0 (perfect)
Answer: "Christopher Nolan directed it in 2010..." → 0.9 (verbose)
Answer: "It's a science fiction film..." → 0.2 (irrelevant)
```

---

#### 🎯 Context Precision (Improved)
**Context-by-context scoring:**
- Đánh giá từng context riêng lẻ
- Phân loại: HIGHLY RELEVANT (1.0), SOMEWHAT RELEVANT (0.5), IRRELEVANT (0.0)
- Tính precision = average của các scores

**Example trong prompt:**
```
Question: "Who directed Avatar: Fire and Ash?"
Context 1: "Avatar: Fire and Ash directed by James Cameron" → 1.0
Context 2: "Avatar (2009) also by Cameron" → 0.5
Context 3: "Titanic won 11 Oscars" → 0.0
Precision: (1.0 + 0.5 + 0.0) / 3 = 0.5
```

---

#### 🔍 Context Recall (Improved)
**Information coverage analysis:**
- Liệt kê key facts trong ground truth
- Check từng fact có trong contexts không
- Calculate: facts_found / total_facts

**Example:**
```
Ground Truth: "Inception (2010) directed by Nolan, starring DiCaprio"
Key Facts: [title, year, director, actor]
Context covers 3/4 facts → 0.75 recall
```

---

#### ✅ Answer Correctness (Improved)
**Two-dimensional evaluation:**
1. **FACTUAL ACCURACY** - Facts đúng không?
2. **COMPLETENESS** - Đủ thông tin chưa?

**Semantic matching:**
- "directed by" = "director:" (tương đương)
- Extra correct info = OK (không trừ điểm)
- Wrong info = Severely penalized

---

### 4. **New Metrics Added** 🆕

#### 📋 Response Completeness
**Purpose:** Đo user satisfaction

**Criteria:**
- ✅ Provides all expected information
- ✅ Sufficient detail (not too brief/verbose)
- ✅ Actionable information
- ✅ No obvious questions left unanswered

**Example:**
```
Question: "Tell me about Inception"
"A sci-fi film" → 0.2 (too brief)
"A 2010 sci-fi by Nolan about dreams" → 0.7 (good)
"A 2010 sci-fi by Nolan starring DiCaprio about dream heists. Acclaimed." → 1.0 (satisfying)
```

---

#### 🔗 Source Attribution
**Purpose:** Đo traceability của information

**Evaluation:**
- Có citation markers? ("according to", "based on", etc.)
- Information có trace về contexts được không?
- User có verify sources được không?

**Scoring:**
```
1.0 = Explicit citations for all claims
0.8 = Clear implicit attribution
0.6 = Partial attribution
0.4 = Weak attribution
0.2 = No attribution
```

**Note:** Low score = hard to verify, not wrong

---

### 5. **Weighted Overall Score**

#### ⚖️ Intelligent Weighting
**Trước:** Simple average của tất cả metrics
**Sau:** Weighted average ưu tiên metrics quan trọng

```python
weights = {
    'faithfulness': 1.5,          # Critical - no hallucination
    'answer_relevancy': 1.5,      # Critical - answers question
    'answer_correctness': 1.5,    # Critical - factually correct
    'context_precision': 1.0,     # Important - quality retrieval
    'context_recall': 1.0,        # Important - complete retrieval
    'response_completeness': 0.8, # Nice to have - satisfaction
    'source_attribution': 0.7     # Nice to have - traceability
}
```

**Output:**
- `overall_weighted`: Score có trọng số (primary metric)
- `overall_simple`: Simple average (for comparison)

---

### 6. **Better Context Formatting**

#### 📝 Improved `_format_contexts()`
**Trước:**
```
Context 1: Movie info...
Context 2: More info...
```

**Sau:**
```
--- CONTEXT 1 ---
Movie info with clear structure...
--- END CONTEXT 1 ---

--- CONTEXT 2 ---
More info...
--- END CONTEXT 2 ---

[... 3 more contexts not shown ...]
```

**Lợi ích:**
- ✅ Rõ ràng hơn cho LLM
- ✅ Dễ reference "Context 2" trong evaluation
- ✅ Show truncation info

---

## 📊 Metrics Summary

| Metric | Type | Score Range | Weight | Purpose |
|--------|------|-------------|--------|---------|
| **Faithfulness** | Core | 0-1 | 1.5x | Prevent hallucination |
| **Answer Relevancy** | Core | 0-1 | 1.5x | Answer the question |
| **Answer Correctness** | Core | 0-1 | 1.5x | Factual accuracy |
| **Context Precision** | Retrieval | 0-1 | 1.0x | Low noise |
| **Context Recall** | Retrieval | 0-1 | 1.0x | Complete retrieval |
| **Response Completeness** | 🆕 UX | 0-1 | 0.8x | User satisfaction |
| **Source Attribution** | 🆕 Trust | 0-1 | 0.7x | Traceability |

**Total: 7 metrics** (5 original + 2 new)

---

## 🎯 Usage Example

```python
from manual_ragas_evaluation import ManualRAGASEvaluator

evaluator = ManualRAGASEvaluator()
evaluator.debug_mode = True  # Show LLM reasoning

metrics = evaluator.evaluate_single(
    question="Who directed Inception?",
    answer="Christopher Nolan directed Inception, a 2010 sci-fi film.",
    contexts=[
        "Inception is a 2010 film directed by Christopher Nolan",
        "The film stars Leonardo DiCaprio"
    ],
    ground_truth="Christopher Nolan"
)

print(f"Faithfulness: {metrics['faithfulness']:.3f}")
print(f"Answer Relevancy: {metrics['answer_relevancy']:.3f}")
print(f"Response Completeness: {metrics['response_completeness']:.3f}")
print(f"Overall (weighted): {metrics['overall_weighted']:.3f}")
```

---

## 🔄 Comparison: Before vs After

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Prompts** | Generic, brief | Detailed, with examples | 🔥🔥🔥 |
| **Error Handling** | Basic try-catch | Retry logic + fallbacks | 🔥🔥 |
| **Transparency** | Score only | Score + reasoning | 🔥🔥🔥 |
| **Metrics** | 5 standard | 7 (+ 2 new) | 🔥🔥 |
| **Scoring** | Simple average | Weighted + simple | 🔥🔥 |
| **Context Format** | Basic | Structured | 🔥 |
| **Rubrics** | Vague (0.8, 0.6) | Precise (0.9, 0.8, 0.7) | 🔥🔥 |

---

## 📈 Expected Impact

### Reliability
- ✅ More consistent scores across runs
- ✅ Fewer API failures with retry logic
- ✅ Better handling of edge cases

### Transparency
- ✅ Understand why scores are what they are
- ✅ Debug problematic evaluations
- ✅ Justify scores to stakeholders

### Coverage
- ✅ 2 new metrics cover UX and trust aspects
- ✅ More comprehensive RAG evaluation
- ✅ Better differentiate systems

### Accuracy
- ✅ More detailed prompts → better LLM performance
- ✅ Examples in prompts → calibrated scoring
- ✅ Weighted average → prioritize critical metrics

---

## 🛠️ Configuration

### Debug Mode
```python
evaluator.debug_mode = True   # Show reasoning (verbose)
evaluator.debug_mode = False  # Hide reasoning (clean output)
```

### Retry Settings
```python
# In _call_llm_with_retry()
max_retries = 3  # Adjust if needed
```

### Weights Customization
```python
# In evaluate_single()
weights = {
    'faithfulness': 2.0,  # Increase if hallucination is critical
    # ... customize as needed
}
```

---

## 🎓 Best Practices

1. **Debug Mode**: Always ON during development
2. **Weights**: Adjust based on your use case
3. **Ground Truth**: Provide when available (improves recall/correctness)
4. **Context Quality**: Better contexts → better scores
5. **Sample Size**: Evaluate on 20+ queries for statistical validity

---

## 📝 Notes

- **API Cost**: 7 LLM calls per evaluation (increased from 5)
- **Time**: ~10-15 seconds per evaluation (with retries)
- **Token Usage**: ~2000-3000 tokens per evaluation
- **Rate Limits**: Consider API limits when batch evaluating

---

## 🚀 Future Improvements

Potential enhancements:
- [ ] Multi-turn conversation support
- [ ] Aspect-based scoring (e.g., score different parts of answer)
- [ ] Confidence intervals for scores
- [ ] Automated weight tuning based on dataset
- [ ] Human-in-the-loop calibration

---

## 📚 References

**RAGAS Framework:**
- Original paper: https://arxiv.org/abs/2309.15217
- Our implementation: Manual LLM-as-judge approach

**Improvements based on:**
- Chain-of-thought prompting research
- LLM evaluation best practices
- RAG system evaluation literature

---

**Last Updated**: January 6, 2026  
**Version**: 2.0 (Enhanced)
