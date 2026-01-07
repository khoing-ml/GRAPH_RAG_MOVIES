# Tài liệu Thiết lập Thí nghiệm Embedding

## 📋 Tổng quan

Tài liệu này mô tả chi tiết cấu hình, tham số và quy trình thí nghiệm crawl dữ liệu phim từ TMDB API và tạo embeddings sử dụng Google Gemini AI để lưu trữ vào Qdrant (Vector DB) và Neo4j (Graph DB).

---

## 🔧 Cấu hình hệ thống

### 1. API Credentials

```python
# TMDB API
TMDB_API_KEY = 'ba39c73252cd9fb0849949da47454e7d'

# Qdrant Cloud
QDRANT_URL = 'https://9a823e32-f097-4096-87a0-23f05baaf13a.europe-west3-0.gcp.cloud.qdrant.io'
QDRANT_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.yZ1QMZ7exqzs_wswtYsqtwaGpu2ExXfhltpNwUq8Zp0'

# Neo4j Aura
NEO4J_URI = 'neo4j+s://294ac027.databases.neo4j.io'
NEO4J_USERNAME = 'neo4j'
NEO4J_PASSWORD = 'HCF2K8_WnovcGqSKeNocCRi_7upAxqqeTAfTDMCSAjM'

# Google Gemini
GOOGLE_API_KEY = 'AIzaSyDb3B5gPGV8pGgHFBmwEC4XwfzmBgnJCW0'
```

---

## ⚙️ Tham số thí nghiệm chính

### 2. Batch Processing & Pagination

| Tham số | Giá trị | Mô tả |
|---------|---------|-------|
| `BATCH_SIZE` | 25 | Số lượng phim xử lý trong mỗi batch (tăng từ 10 lên 25 để tối ưu tốc độ) |
| `MAX_PAGES` | 60 | Số trang tối đa crawl từ TMDB (mỗi trang ~20 phim) |
| `EMBEDDING_TIMEOUT` | 30 seconds | Thời gian timeout cho mỗi lần gọi Gemini API (tránh treo) |

### 3. Quality Filters (Bộ lọc chất lượng)

| Tham số | Giá trị | Lý do |
|---------|---------|-------|
| `MIN_VOTE_COUNT` | 100 | Chỉ lấy phim có ≥100 lượt đánh giá (đảm bảo phổ biến) |
| `MIN_RATING` | 5.0 | Rating ≥5.0/10 (chất lượng tối thiểu) |
| `MIN_OVERVIEW_LENGTH` | 50 characters | Mô tả phim phải ≥50 ký tự (đủ thông tin) |

### 4. Storage Configuration

| Tham số | Giá trị | Mục đích |
|---------|---------|----------|
| `COLLECTION_NAME` | "movies_vietnamese" | Tên collection trong Qdrant |
| `SAVE_LOCAL_DATA` | True | Lưu dữ liệu JSON local trước khi upload |
| `LOCAL_DATA_DIR` | '../crawled_data' | Thư mục lưu trữ local |
| `ENABLE_NEO4J` | True | Bật/tắt upload lên Neo4j (tắt để tăng tốc 3-5x) |

### 5. Embedding Configuration

| Tham số | Giá trị | Chi tiết |
|---------|---------|----------|
| **Model** | `text-embedding-004` | Google Gemini embedding model |
| **Dimension** | 768 | Số chiều vector embedding |
| **Distance Metric** | Cosine | Phương pháp đo khoảng cách vector |
| **Task Type** | `retrieval_document` | Loại task cho embedding |
| **Max Retries** | 3 | Số lần retry khi API fail |
| **Timeout per call** | 30s | Timeout cho mỗi API call |

---

## 🎯 Discovery Strategies (Chiến lược khám phá)

Hệ thống sử dụng 2 chiến lược song song để tăng độ đa dạng dữ liệu:

### Strategy 1: Popular Movies
```python
{
    'name': 'Popular',
    'params': {
        'sort_by': 'popularity.desc',
        'vote_count.gte': 100,
        'vote_average.gte': 5.0
    },
    'pages': 20  # Dự kiến ~400 phim
}
```

### Strategy 2: Top Rated
```python
{
    'name': 'Top Rated',
    'params': {
        'sort_by': 'vote_average.desc',
        'vote_count.gte': 100,
        'vote_average.gte': 7.0
    },
    'pages': 15  # Dự kiến ~300 phim
}
```

**Tổng dự kiến**: ~700 phim từ cả 2 strategies

---

## 📊 Data Schema

### Qdrant Payload Schema

Mỗi point trong Qdrant chứa:

```python
{
    'tmdb_id': int,           # ID phim từ TMDB
    'title': str,             # Tên phim (đã normalize)
    'overview': str,          # Mô tả (đã clean)
    'genres': List[str],      # Thể loại
    'year': str,              # Năm phát hành
    'rating': float,          # Điểm đánh giá (0-10)
    'runtime': int,           # Thời lượng (phút)
    'tagline': str,           # Slogan
    'directors': List[str],   # Đạo diễn
    'cast': List[str],        # Diễn viên (top 5)
    'keywords': List[str],    # Keywords (top 10)
    'companies': List[str],   # Công ty sản xuất (top 3)
    'countries': List[str],   # Quốc gia sản xuất
    'collection': str,        # Thuộc series/franchise
    'poster_url': str,        # URL poster
    'backdrop_url': str       # URL backdrop
}
```

### Neo4j Graph Schema

**Nodes (7 loại):**
1. `Movie` - Phim
2. `Person` - Con người (diễn viên, đạo diễn, etc.)
3. `Genre` - Thể loại
4. `Company` - Công ty sản xuất
5. `Country` - Quốc gia
6. `Collection` - Series phim
7. `Keyword` - Từ khóa

**Relationships (13 loại):**
1. `DIRECTED` - Person → Movie
2. `ACTED_IN` - Person → Movie (có thuộc tính: character, order)
3. `WROTE` - Person → Movie
4. `CINEMATOGRAPHY` - Person → Movie
5. `COMPOSED_MUSIC` - Person → Movie
6. `BELONGS_TO` - Movie → Genre
7. `PRODUCED` - Company → Movie
8. `FILMED_IN` - Movie → Country
9. `IN_COLLECTION` - Movie → Collection
10. `HAS_KEYWORD` - Movie → Keyword
11. `SIMILAR_TO` - Movie → Movie (có thuộc tính: score)
12. `WORKED_WITH` - Person ↔ Person (có thuộc tính: count, movies)
13. `CO_STARRED` - Person ↔ Person (có thuộc tính: count, movies)

---

## 🧹 Data Preprocessing Pipeline

### 1. Text Cleaning Functions

| Function | Mục đích |
|----------|----------|
| `clean_text()` | Normalize unicode, loại bỏ HTML tags, control chars |
| `normalize_person_name()` | Chuẩn hóa tên người (title case, loại bỏ suffix) |
| `normalize_title()` | Chuẩn hóa tên phim ("The Dark Knight, The" → "The Dark Knight") |
| `clean_keyword()` | Lowercase, loại bỏ stop words |

### 2. Validation Functions

| Function | Kiểm tra |
|----------|----------|
| `validate_tmdb_id()` | ID hợp lệ và > 0 |
| `validate_movie_data()` | Đầy đủ fields, đạt quality filters |

### 3. Deduplication

- **People**: Deduplicate theo `id`
- **Keywords**: Deduplicate theo `name`
- **Genres/Companies**: Deduplicate theo `name`

---

## 🚀 Execution Workflow

### Phase 1: Connection Testing
1. Test Qdrant connection
2. Test Neo4j connection
3. Test TMDB API
4. Configure Gemini API

### Phase 2: Data Discovery
```
For each strategy:
  ├── Discover movies (paginated)
  ├── Apply quality filters
  ├── Remove duplicates
  └── Filter already processed IDs
```

### Phase 3: Data Processing
```
For each movie:
  ├── Fetch details (movie + credits + keywords + similar)
  ├── Validate data quality
  ├── Extract & clean all fields
  │   ├── Basic info (title, overview, genres)
  │   ├── Crew (directors, writers, cinematographers, composers)
  │   ├── Cast (top 10 with characters)
  │   ├── Production (companies, countries, collection)
  │   └── Metadata (keywords, similar movies)
  ├── Create optimized embedding text
  ├── Generate Gemini embedding (768-dim)
  ├── Save to local JSON (movies/ + posters/)
  ├── Upload to Qdrant (vector + payload)
  └── Upload to Neo4j (graph nodes + relationships)
```

### Phase 4: Post-processing
1. Generate `movies_index.json` (sorted by rating)
2. Create preview HTML with posters
3. Generate statistics report

---

## 📈 Performance Optimization

### Rate Limiting Strategy

| Operation | Delay | Reason |
|-----------|-------|--------|
| TMDB pagination | 0.25s | Tránh rate limit API |
| Gemini embedding | 0.1-0.2s (random) | Giảm 429 errors |
| Between batches | 0.5s | Cho phép API rest |

### Error Handling

**Gemini API Errors:**
- `429 Rate Limit`: Wait 5-20s, retry
- `500/503 Server Error`: Wait 2-6s, retry
- `Timeout`: Auto-kill sau 30s, retry
- Unknown errors: Fail immediately, không retry

**TMDB API:**
- Status ≠ 200: Skip page, tiếp tục
- Timeout: Skip movie, tiếp tục

---

## 📦 Output Structure

### Local Data Directory
```
crawled_data/
├── movies_index.json           # Master index (sorted by rating)
├── preview.html                # Visual preview with posters
├── README.md                   # Auto-generated documentation
├── movies/
│   ├── 550.json               # Fight Club
│   ├── 13.json                # Forrest Gump
│   └── ...                    # 1 file per movie
└── posters/
    ├── 550.txt                # Poster URL for movie 550
    └── ...
```

### Processed IDs Log
```
processed_ids.log              # List of successfully processed movie IDs
```

---

## 🎯 Expected Results

### Volume
- **Target**: ~700 unique movies
- **Success rate**: 85-95%
- **Processing time**: ~30-45 minutes

### Quality Metrics
- All movies: vote_count ≥ 100
- All movies: rating ≥ 5.0
- All movies: overview ≥ 50 chars
- Average cast size: 8-10 people
- Average keywords: 10-15
- Graph density: High (12+ relationship types)

---

## 🛠️ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Qdrant cluster paused | Resume at cloud.qdrant.io |
| Gemini rate limit | Increase delay hoặc giảm BATCH_SIZE |
| Neo4j timeout | Disable Neo4j (`ENABLE_NEO4J = False`) |
| Embedding timeout | Tăng `EMBEDDING_TIMEOUT` (30→60s) |
| TMDB API slow | Tăng `time.sleep` giữa requests |

---

## 📚 Dependencies

### Required Packages
```bash
pip install qdrant_client
pip install neo4j
pip install google-generativeai
pip install requests
pip install python-dotenv
```

### Python Version
- **Minimum**: Python 3.8+
- **Recommended**: Python 3.10+

---

## 🔍 Monitoring & Debugging

### Real-time Output
Script in ra console:
- ✅ Successful connections
- 🔍 Discovery progress
- 🔄 Batch processing status
- ✅/❌ Individual movie results
- 📊 Final statistics

### Log Files
- `processed_ids.log` - Danh sách IDs đã xử lý
- Console output - Chi tiết errors

---

## 📝 Notes

1. **API Rate Limits:**
   - TMDB: 40 requests/10 seconds
   - Gemini: 60 requests/minute (free tier)
   - Qdrant Cloud: No limit (paid) hoặc 10K req/day (free)

2. **Cost Considerations:**
   - Gemini Free Tier: 1500 requests/day
   - Qdrant Free: 1GB storage
   - Neo4j Aura Free: 200k nodes, 400k relationships

3. **Data Freshness:**
   - TMDB cập nhật daily
   - Nên re-crawl 1-2 tuần/lần

4. **Scalability:**
   - Có thể tăng `MAX_PAGES` để crawl nhiều hơn
   - Giảm `BATCH_SIZE` nếu gặp memory issues
   - Tắt Neo4j để crawl nhanh hơn 3-5x

---

## 📅 Version History

- **v1.0** (Initial): Sentence-BERT embeddings
- **v2.0** (Current): Gemini embeddings + Enhanced graph + Local storage

---

## 👤 Contact

For issues or questions about this setup, check:
- TMDB API docs: https://developers.themoviedb.org/
- Qdrant docs: https://qdrant.tech/documentation/
- Gemini AI docs: https://ai.google.dev/docs

---

**Last Updated**: January 6, 2026
