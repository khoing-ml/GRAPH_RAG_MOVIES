🎬 Movie GraphRAG - Hệ thống Gợi ý Phim Thông minh
Hybrid Retrieval-Augmented Generation (RAG) kết hợp giữa Vector Database (Qdrant) và Knowledge Graph (Neo4j), được vận hành bởi Google Gemini LLM.

📖 Giới thiệu
Dự án này giải quyết vấn đề của các hệ thống tìm kiếm phim truyền thống (dựa trên từ khóa) bằng cách áp dụng GraphRAG. Hệ thống không chỉ hiểu ngữ nghĩa của câu hỏi (Semantic Search) mà còn hiểu được mối quan hệ sâu sắc giữa các bộ phim, diễn viên, đạo diễn và thể loại.

Điểm nổi bật:
Tìm kiếm Ngữ nghĩa: Hiểu ý định người dùng (ví dụ: "Phim hành động siêu anh hùng") nhờ Vector Embedding.

Mở rộng Ngữ cảnh (Graph Reasoning): Tự động gợi ý các phim liên quan dựa trên mối quan hệ (Cùng đạo diễn, cùng diễn viên, cùng thể loại) từ Knowledge Graph.

Dữ liệu lớn: Hỗ trợ crawl và xử lý hàng ngàn bộ phim từ TMDB.

Chatbot thông minh: Giao diện trực quan, trả lời tự nhiên bằng Tiếng Việt.

🛠️ Kiến trúc Hệ thống
Data Pipeline: Crawl từ TMDB API -> Làm sạch -> Vector hóa (Qdrant) & Tạo Graph (Neo4j).

Retrieval (Truy xuất):

Bước 1: Query -> Vector Search (Qdrant) -> Lấy Top K phim tiềm năng.

Bước 2: ID phim -> Graph Traversal (Neo4j) -> Lấy thông tin Đạo diễn, Diễn viên, Thể loại và các phim liên quan.

Generation (Tổng hợp): Context từ Bước 1 & 2 -> Gemini LLM -> Câu trả lời cuối cùng.

⚙️ Cài đặt
1. Yêu cầu tiên quyết
Python 3.10 trở lên.

Docker & Docker Compose (Để chạy Database).

Tài khoản Google Cloud Platform (đã bật Generative Language API).

Tài khoản TMDB API (https://www.themoviedb.org/settings/api).

2. Cài đặt thư viện
Bash

git clone https://github.com/username/movie-graph-rag.git
cd movie-graph-rag
pip install -r requirements.txt
3. Cấu hình môi trường (.env)
Tạo file .env tại thư mục gốc và điền thông tin:

Ini, TOML

# Google API (Gemini)
GOOGLE_API_KEY=AIzaSy... (Key của bạn)

# TMDB API
TMDB_API_KEY=your_tmdb_api_key_here

# Neo4j (Graph DB)
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Qdrant (Vector DB)
QDRANT_URL=http://localhost:6333
🚀 Hướng dẫn Sử dụng
Bước 1: Khởi động Database
Sử dụng Docker Compose để bật Qdrant và Neo4j:

Bash

docker-compose up -d
Đợi khoảng 30s để database khởi động hoàn toàn.

Bước 2: Chuẩn bị Dữ liệu (ETL Pipeline)
2.1. Crawl dữ liệu (Thu thập): Tải về dữ liệu phim từ TMDB:

Bash

python crawl_movies.py

2.2. Nạp dữ liệu (Ingestion): Vector hóa và xây dựng đồ thị tri thức (Chạy 1 lần duy nhất):

Bash

python main.py ingest
Bước 3: Chạy Ứng dụng
Khởi chạy giao diện Chatbot trên trình duyệt:

Bash

streamlit run app.py
Truy cập: http://localhost:8501

📂 Cấu trúc Dự án
Plaintext

movie-graph-rag/
├── app.py                  # Giao diện chính (Streamlit)
├── main.py                 # CLI entry point (cho Ingest)
├── crawl_movies.py         # Script crawl dữ liệu phim từ TMDB
├── test_rag_movies.py      # Script test RAG pipeline
├── check_db_status.py      # Kiểm tra trạng thái database
├── fix_vector_dimension.py # Sửa lỗi dimension mismatch
├── requirements.txt        # Các thư viện phụ thuộc
├── .env                    # Biến môi trường (API Keys)
└── src/
    ├── config.py           # Quản lý cấu hình
    ├── ingest.py           # Logic nạp dữ liệu
    ├── rag_pipeline.py     # Luồng xử lý chính (RAG logic)
    ├── llm_service.py      # Tương tác với Gemini
    ├── vector_db.py        # Tương tác với Qdrant
    └── graph_db.py         # Tương tác với Neo4j
🐛 Debug & Kiểm tra
Nếu gặp lỗi hoặc muốn kiểm tra dữ liệu:

Kiểm tra trạng thái database: 
```bash
python check_db_status.py
```

Kiểm tra và sửa dimension mismatch:
```bash
python fix_vector_dimension.py
```

Test RAG pipeline:
```bash
python test_rag_movies.py
```

Neo4j Browser: Truy cập http://localhost:7474 (User: neo4j, Pass: password123).

Qdrant Dashboard: Truy cập http://localhost:6333/dashboard.