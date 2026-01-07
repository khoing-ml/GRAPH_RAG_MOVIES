# ⚙️ Cấu hình Thí nghiệm và Siêu tham số Hệ thống GraphRAG

## 📋 Tổng quan

Tài liệu này mô tả chi tiết tất cả các cấu hình, siêu tham số (hyperparameters) và thiết lập thí nghiệm của hệ thống GraphRAG Movie Recommendation. Tài liệu được cập nhật lần cuối: **January 7, 2026**.

---

## 🔧 I. CÁC THAM SỐ MÔ HÌNH (Model Hyperparameters)

### 1.1 Embedding Model

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Model Name** | `text-embedding-004` | Google Gemini embedding model |
| **Embedding Dimension** | 768 | Số chiều của vector embedding |
| **Task Type (Document)** | `retrieval_document` | Loại task khi tạo embedding cho documents |
| **Task Type (Query)** | `retrieval_query` | Loại task khi tạo embedding cho queries |
| **Max Retries** | 5 | Số lần retry khi API call thất bại |
| **Retry Wait Time (429)** | 20-25s (random) | Thời gian chờ khi gặp rate limit |
| **Retry Wait Time (Other)** | 2s | Thời gian chờ khi gặp lỗi khác |

### 1.2 Language Model (LLM)

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Model Name** | `gemini-2.5-flash` | Google Gemini chat model |
| **Temperature** | 0.3 | Độ sáng tạo (giảm từ 0.7 để giảm hallucination) |
| **Top-P** | 0.8 | Nucleus sampling threshold |
| **Top-K** | 20 | Số lượng tokens candidate |
| **Max Output Tokens** | 2048 | Số tokens tối đa trong response |
| **Safety Settings** | `BLOCK_NONE` | Tắt tất cả safety filters cho movie content |

### 1.3 Fallback/Augmentation Model

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Model Name** | `gemini-2.5-flash` | Cùng model với LLM chính |
| **Mode** | Fallback hoặc Augmentation | Có thể cấu hình |
| **Enable Fallback** | `True` (default) | Bật/tắt fallback mode |
| **Augment Mode** | `False` (default) | Bật/tắt augmentation mode |

---

## 🔍 II. CÁC THAM SỐ RETRIEVAL (Retrieval Hyperparameters)

### 2.1 Vector Search (Basic Retrieval)

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Top-K Results** | 8 | Số lượng kết quả vector search (tăng từ 6→8) |
| **Relevance Threshold** | 0.5 | Ngưỡng điểm similarity (tăng từ 0.45→0.5) |
| **Distance Metric** | Cosine | Phương pháp đo khoảng cách vector |
| **Max Contexts** | 12 | Số contexts tối đa sau khi organize |
| **Diversity Threshold** | 0.65 | Ngưỡng đa dạng cho organizer |

### 2.2 Advanced Hybrid Retrieval

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Top-K Vector** | 6 | Số kết quả từ vector search |
| **Max Contexts** | 15 | Số contexts tối đa sau khi organize |
| **Diversity Threshold** | 0.7 | Ngưỡng đa dạng (cao hơn basic) |
| **Position Strategy** | `important_first` | Chiến lược sắp xếp contexts |

#### 2.2.1 Entity Linking

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Max Entities per Type** | 3 | Số entities tối đa mỗi loại (movie/person/genre) |
| **Entity Types** | movie, person, genre, other | Các loại entities được nhận diện |

#### 2.2.2 Graph Traversal

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **K-hop Depth** | 1-3 (adaptive) | Số bước traversal trong graph |
| **Max Nodes per Traversal** | 20 | Số nodes tối đa mỗi lần traversal |
| **Max Relationships** | 50 | Số relationships tối đa được lấy |
| **Max Path Length** | 4 | Độ dài path tối đa giữa 2 entities |

#### 2.2.3 Adaptive Retrieval Depth

| Query Category | Retrieval Depth | Lý do |
|----------------|-----------------|-------|
| `specific_film_info` | 1 hop | Câu hỏi đơn giản về thông tin phim |
| `genre_recommendation` | 2 hops | Đề xuất theo thể loại |
| `similarity_search` | 2 hops | Tìm phim tương tự |
| `director_filmography` | 2 hops | Phim của đạo diễn |
| `actor_filmography` | 2 hops | Phim của diễn viên |
| `disambiguation` | 2 hops | Phân biệt các entities |
| `comparison` | 3 hops | So sánh phức tạp |
| **Default** | 2 hops | Mặc định cho các loại khác |

---

## 🧠 III. CÁC THAM SỐ XỬ LÝ QUERY (Query Processing)

### 3.1 Query Processor

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Use Cache** | `True` | Bật cache cho queries |
| **Max Cache Size** | 1000 | Số queries tối đa trong cache |
| **Min Query Length** | 3 characters | Độ dài tối thiểu của query |

### 3.2 Confidence Scoring Weights

| Component | Weight | Mô tả |
|-----------|--------|-------|
| **Entity Detection** | 40% | Chất lượng nhận diện entities |
| **Relation Detection** | 30% | Chất lượng nhận diện relations |
| **Query Expansion** | 20% | Chất lượng mở rộng query |
| **Query Structure** | 10% | Chất lượng cấu trúc query |

### 3.3 Query Rewriting Triggers

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Low Confidence | < 0.4 | Trigger rewriting |
| Few Entities | < 2 | Trigger expansion |
| No Relations | 0 | Trigger relation extraction |

### 3.4 Fallback Trigger Threshold

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Query Confidence Threshold** | 0.5 | Ngưỡng confidence để trigger fallback model |
| **Action** | Use Fallback Model | Khi confidence < 0.5, bỏ qua database và dùng general knowledge |
| **Rationale** | Avoid low-quality retrieval | Tránh lấy contexts không relevant khi query không rõ ràng |

---

## 📊 IV. CÁC THAM SỐ GRAPH DATABASE

### 4.1 Neo4j Configuration

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **URI** | `neo4j+s://294ac027.databases.neo4j.io` | Neo4j Aura endpoint |
| **Connection Timeout** | Default | Thời gian timeout kết nối |
| **Max Connection Pool** | Default | Số connections tối đa |

### 4.2 Graph Schema

#### Node Types (7 loại)

1. **Movie** - Phim
2. **Person** - Con người (actors, directors, crew)
3. **Genre** - Thể loại
4. **Company** - Công ty sản xuất
5. **Country** - Quốc gia
6. **Collection** - Series/Franchise
7. **Keyword** - Từ khóa chủ đề

#### Relationship Types (13 loại)

1. `DIRECTED` - Person → Movie
2. `ACTED_IN` - Person → Movie (properties: character, order)
3. `WROTE` - Person → Movie
4. `CINEMATOGRAPHY` - Person → Movie
5. `COMPOSED_MUSIC` - Person → Movie
6. `BELONGS_TO` - Movie → Genre
7. `PRODUCED` - Company → Movie
8. `FILMED_IN` - Movie → Country
9. `IN_COLLECTION` - Movie → Collection
10. `HAS_KEYWORD` - Movie → Keyword
11. `SIMILAR_TO` - Movie → Movie (property: score)
12. `WORKED_WITH` - Person ↔ Person (properties: count, movies)
13. `CO_STARRED` - Person ↔ Person (properties: count, movies)

---

## 🗄️ V. CÁC THAM SỐ VECTOR DATABASE

### 5.1 Qdrant Configuration

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **URL** | `https://9a823e32-f097-4096-87a0-23f05baaf13a...` | Qdrant Cloud endpoint |
| **Collection Name** | `movies_vietnamese` | Tên collection |
| **Vector Size** | 768 | Kích thước vector (khớp với embedding) |
| **Distance Metric** | Cosine | Phương pháp đo khoảng cách |

### 5.2 Payload Schema

Mỗi point trong Qdrant chứa:

```python
{
    'tmdb_id': int,           # ID phim từ TMDB
    'title': str,             # Tên phim
    'overview': str,          # Mô tả
    'genres': List[str],      # Thể loại
    'year': str,              # Năm phát hành
    'rating': float,          # Điểm đánh giá (0-10)
    'runtime': int,           # Thời lượng (phút)
    'tagline': str,           # Slogan
    'directors': List[str],   # Đạo diễn
    'cast': List[str],        # Diễn viên (top 5)
    'keywords': List[str],    # Keywords (top 10)
    'companies': List[str],   # Công ty sản xuất (top 3)
    'countries': List[str],   # Quốc gia
    'collection': str,        # Series/franchise
    'poster_url': str,        # URL poster
    'backdrop_url': str       # URL backdrop
}
```

---

## 🔄 VI. CÁC THAM SỐ DATA CRAWLING

### 6.1 Batch Processing

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **Batch Size** | 25 | Số phim xử lý mỗi batch (tăng từ 10→25) |
| **Max Pages** | 60 | Số trang tối đa crawl từ TMDB |
| **Embedding Timeout** | 30s | Timeout cho mỗi embedding call |

### 6.2 Quality Filters

| Filter | Threshold | Mục đích |
|--------|-----------|----------|
| **Min Vote Count** | 100 | Đảm bảo phim phổ biến |
| **Min Rating** | 5.0/10 | Chất lượng tối thiểu |
| **Min Overview Length** | 50 characters | Đủ thông tin mô tả |

### 6.3 Discovery Strategies

#### Strategy 1: Popular Movies
- **Sort By**: `popularity.desc`
- **Vote Count**: ≥ 100
- **Vote Average**: ≥ 5.0
- **Pages**: 20 (~400 phim)

#### Strategy 2: Top Rated
- **Sort By**: `vote_average.desc`
- **Vote Count**: ≥ 100
- **Vote Average**: ≥ 7.0
- **Pages**: 15 (~300 phim)

**Tổng dự kiến**: ~700 phim

### 6.4 Rate Limiting

| Operation | Delay | Lý do |
|-----------|-------|-------|
| **TMDB Pagination** | 0.25s | Tránh rate limit |
| **Gemini Embedding** | 0.1-0.2s (random) | Giảm 429 errors |
| **Between Batches** | 0.5s | Cho API rest |

---

## 🎯 VII. CÁC THAM SỐ EVALUATION

### 7.1 RAGAS Metrics

| Metric | Weight | Mô tả |
|--------|--------|-------|
| **Faithfulness** | 1.0 | Độ trung thực với context |
| **Answer Relevancy** | 1.0 | Độ liên quan của câu trả lời |
| **Context Precision** | 1.0 | Độ chính xác của contexts |
| **Context Recall** | 1.0 | Độ đầy đủ của contexts |
| **Answer Correctness** | 1.0 | Độ chính xác so với ground truth |

### 7.2 Manual RAGAS Configuration

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| **LLM Judge Model** | `gemini-2.0-flash-exp` | Model đánh giá |
| **Max Retries** | 3 | Số lần retry khi LLM call fail |
| **Debug Mode** | `True` | Hiển thị reasoning của LLM |

### 7.3 Test Dataset Categories

1. **Actor-based queries** - Câu hỏi về diễn viên
2. **Director-based queries** - Câu hỏi về đạo diễn
3. **Genre-based queries** - Câu hỏi về thể loại
4. **Multi-hop queries** - Câu hỏi phức tạp nhiều bước
5. **Similarity queries** - Tìm phim tương tự
6. **Specific film info** - Thông tin cụ thể về phim

---

## 🛡️ VIII. CÁC THAM SỐ ANTI-HALLUCINATION

### 8.1 Hallucination Detection

| Pattern | Context Check | Action |
|---------|---------------|--------|
| Specific dates | Must be in context | Add disclaimer if not found |
| Cast members | Must be in context | Add disclaimer if not found |
| Award wins | Must be in context | Add disclaimer if not found |
| Release info | Must be in context | Add disclaimer if not found |

**Threshold**: ≥ 2 suspicious patterns → Add disclaimer

### 8.2 Low Confidence Detection

Các cụm từ trigger fallback:
- "i don't", "i couldn't", "i can't find"
- "no information", "not available", "unable to find"
- "không có thông tin", "không tìm thấy", "không rõ"

**Threshold**: Answer length < 15 words → Trigger fallback

### 8.3 Context Relevance Validation

| Check | Threshold | Action |
|-------|-----------|--------|
| **Context exists** | Not empty | Continue |
| **Context meaningful** | > 50 characters | Continue |
| **No "unavailable"** | String check | Continue |
| **All checks fail** | - | Trigger fallback |

---

## 🔧 IX. CÁC THAM SỐ ORGANIZER (Post-processing)

### 9.1 Organizer Configuration

| Tham số | Basic Retrieval | Advanced Retrieval |
|---------|-----------------|-------------------|
| **Max Contexts** | 12 | 15 |
| **Diversity Threshold** | 0.65 | 0.7 |
| **Position Strategy** | `important_first` | `important_first` |
| **Enable Organizer** | `True` (default) | `True` (default) |

### 9.2 Diversity Calculation

- **Semantic Similarity**: Sử dụng embeddings
- **Threshold**: Contexts với similarity > threshold bị coi là duplicate
- **Strategy**: Giữ context quan trọng nhất, loại bỏ duplicates

---

## 📈 X. PERFORMANCE METRICS

### 10.1 Expected Performance

| Metric | Target | Actual (if measured) |
|--------|--------|---------------------|
| **Query Processing Time** | < 100ms | - |
| **Vector Search Time** | < 200ms | - |
| **Graph Enrichment Time** | < 300ms | - |
| **LLM Generation Time** | < 2s | - |
| **Total Response Time** | < 3s | - |

### 10.2 Data Quality Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| **Clean Text** | 100% | ✅ 100% |
| **Duplicate Entities** | 0% | ✅ 0% |
| **Invalid Relationships** | 0% | ✅ 0% |
| **Validated IDs** | 100% | ✅ 100% |

### 10.3 Graph Richness

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Node Types** | 3 | 7 | 2.3x |
| **Relationship Types** | 3 | 13 | 4.3x |
| **Relationships/Movie** | ~15 | ~70 | 4.7x |

---

## 🔬 XI. EXPERIMENTAL CONFIGURATIONS

### 11.1 System Modes

| Mode | Configuration | Use Case |
|------|---------------|----------|
| **Basic RAG** | `use_advanced_retriever=False` | Baseline, simple queries |
| **Advanced RAG** | `use_advanced_retriever=True` | Complex queries, multi-hop |
| **With Organizer** | `use_organizer=True` | Better context quality |
| **Fallback Enabled** | `enable_fallback=True` | Handle out-of-domain |
| **Augmentation Mode** | `augment_mode=True` | Combine DB + general knowledge |

### 11.2 Comparison Experiments

#### Experiment 1: GraphRAG vs SimpleRAG
- **GraphRAG**: Full pipeline với graph enrichment
- **SimpleRAG**: Chỉ vector search, không graph
- **Metrics**: RAGAS (Faithfulness, Relevancy, Precision, Recall)

#### Experiment 2: Basic vs Advanced Retrieval
- **Basic**: Vector search only
- **Advanced**: Hybrid (Vector + Graph traversal + Entity linking)
- **Metrics**: Context quality, answer accuracy

#### Experiment 3: With/Without Organizer
- **With**: Apply post-processing và deduplication
- **Without**: Raw contexts
- **Metrics**: Context diversity, answer quality

---

## 📝 XII. CONFIGURATION FILES

### 12.1 Environment Variables (.env)

```bash
# API Keys
GOOGLE_API_KEY=<your_key>
TMDB_API_KEY=<your_key>

# Neo4j
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your_password>

# Qdrant
QDRANT_URL=https://...
QDRANT_API_KEY=<your_key>
QDRANT_COLLECTION=movies_vietnamese
```

### 12.2 Config.py Settings

```python
# Models
EMBEDDING_MODEL = "models/text-embedding-004"
CHAT_MODEL = "models/gemini-2.5-flash"
VECTOR_SIZE = 768

# Databases
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "movies_vietnamese")
```

---

## 🎓 XIII. BEST PRACTICES & TUNING TIPS

### 13.1 Hyperparameter Tuning Guidelines

#### Temperature (LLM)
- **Lower (0.1-0.3)**: Factual, deterministic → Giảm hallucination
- **Medium (0.4-0.7)**: Balanced creativity
- **Higher (0.8-1.0)**: Creative, diverse → Tăng hallucination risk

**Current**: 0.3 (optimized for factual accuracy)

#### Top-K (Vector Search)
- **Lower (3-5)**: Precision-focused, ít noise
- **Medium (6-10)**: Balanced
- **Higher (10+)**: Recall-focused, nhiều options

**Current**: 8 (basic), 6 (advanced) - balanced

#### Relevance Threshold
- **Lower (0.3-0.4)**: More results, lower quality
- **Medium (0.5-0.6)**: Balanced
- **Higher (0.7+)**: Fewer results, higher quality

**Current**: 0.5 - balanced quality/quantity

### 13.2 When to Adjust Parameters

| Scenario | Adjust | Direction |
|----------|--------|-----------|
| Too many irrelevant results | Relevance Threshold | ↑ Increase |
| Missing relevant results | Relevance Threshold | ↓ Decrease |
| Hallucinations detected | Temperature | ↓ Decrease |
| Answers too generic | Temperature | ↑ Increase |
| Slow response time | Top-K, Max Contexts | ↓ Decrease |
| Incomplete answers | Top-K, Max Contexts | ↑ Increase |

---

## 📚 XIV. REFERENCES

### 14.1 Documentation Files

1. **EMBEDDING_EXPERIMENT_SETUP.md** - Chi tiết crawling và embedding
2. **GRAPH_ENHANCEMENTS.md** - Graph schema và enhancements
3. **DATA_PREPROCESSING.md** - Data cleaning pipeline
4. **ALL_IMPROVEMENTS.md** - Tổng hợp improvements
5. **EVALUATION_ARCHITECTURE.md** - Evaluation framework

### 14.2 Code Files

1. **src/config.py** - Configuration constants
2. **src/rag_pipeline.py** - Main RAG pipeline
3. **src/advanced_retriever.py** - Advanced retrieval logic
4. **src/query_processor.py** - Query processing
5. **src/llm_service.py** - LLM service wrapper
6. **src/organizer.py** - Context organization

### 14.3 External Resources

- **TMDB API**: https://developers.themoviedb.org/
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **Neo4j Docs**: https://neo4j.com/docs/
- **Gemini AI**: https://ai.google.dev/docs
- **RAGAS Framework**: https://docs.ragas.io/

---

## 🔄 XV. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| **v1.0** | Dec 2025 | Initial setup với Sentence-BERT |
| **v2.0** | Jan 2026 | Gemini embeddings + Enhanced graph + Local storage |
| **v2.1** | Jan 2026 | Advanced retrieval + Organizer + Anti-hallucination |
| **v2.2** | Jan 2026 | Fallback/Augmentation modes + RAGAS evaluation |

---

## 📞 XVI. CONTACT & SUPPORT

Để biết thêm thông tin hoặc báo cáo vấn đề:
- Xem các file documentation trong project
- Check TMDB API, Qdrant, Neo4j, Gemini docs
- Review code trong `src/` directory

---

**Last Updated**: January 7, 2026  
**Document Version**: 1.0  
**System Version**: 2.2

---

## 📊 APPENDIX: QUICK REFERENCE TABLE

### All Hyperparameters at a Glance

| Category | Parameter | Value | Impact |
|----------|-----------|-------|--------|
| **Embedding** | Model | text-embedding-004 | Quality of semantic search |
| **Embedding** | Dimension | 768 | Vector size |
| **LLM** | Model | gemini-2.5-flash | Response quality |
| **LLM** | Temperature | 0.3 | Factual accuracy ↑ |
| **LLM** | Top-P | 0.8 | Response diversity |
| **LLM** | Top-K | 20 | Candidate pool size |
| **LLM** | Max Tokens | 2048 | Response length |
| **Vector Search** | Top-K | 8 | Number of results |
| **Vector Search** | Threshold | 0.5 | Quality filter |
| **Graph Traversal** | K-hop | 1-3 (adaptive) | Context depth |
| **Graph Traversal** | Max Nodes | 20 | Breadth of search |
| **Organizer** | Max Contexts | 12-15 | Final context count |
| **Organizer** | Diversity | 0.65-0.7 | Deduplication strength |
| **Crawling** | Batch Size | 25 | Processing speed |
| **Crawling** | Min Rating | 5.0 | Data quality |
| **Crawling** | Min Votes | 100 | Popularity filter |

---

**🎬 Hệ thống GraphRAG Movie đã được tối ưu hóa với các siêu tham số được tinh chỉnh kỹ lưỡng để đạt hiệu suất cao nhất!**
