📚 Book GraphRAG - Hệ thống Gợi ý Sách Thông minh
Hybrid Retrieval-Augmented Generation (RAG) kết hợp giữa Vector Database (Qdrant) và Knowledge Graph (Neo4j), được vận hành bởi Google Gemini LLM.

📖 Giới thiệu
Dự án này giải quyết vấn đề của các hệ thống tìm kiếm sách truyền thống (dựa trên từ khóa) bằng cách áp dụng GraphRAG. Hệ thống không chỉ hiểu ngữ nghĩa của câu hỏi (Semantic Search) mà còn hiểu được mối quan hệ sâu sắc giữa các cuốn sách, tác giả và thể loại.

Điểm nổi bật:
Tìm kiếm Ngữ nghĩa: Hiểu ý định người dùng (ví dụ: "Sách về nỗi buồn chiến tranh") nhờ Vector Embedding.

Mở rộng Ngữ cảnh (Graph Reasoning): Tự động gợi ý các sách liên quan dựa trên mối quan hệ (Cùng tác giả, cùng series, cùng thể loại) từ Knowledge Graph.

Dữ liệu lớn: Hỗ trợ crawl và xử lý hàng chục ngàn đầu sách từ Google Books.

Chatbot thông minh: Giao diện trực quan, trả lời tự nhiên bằng Tiếng Việt.

🛠️ Kiến trúc Hệ thống
Data Pipeline: Crawl từ Google Books API -> Làm sạch -> Vector hóa (Qdrant) & Tạo Graph (Neo4j).

Retrieval (Truy xuất):

Bước 1: Query -> Vector Search (Qdrant) -> Lấy Top K sách tiềm năng.

Bước 2: ID sách -> Graph Traversal (Neo4j) -> Lấy thông tin Tác giả, Thể loại và các sách liên quan.

Generation (Tổng hợp): Context từ Bước 1 & 2 -> Gemini LLM -> Câu trả lời cuối cùng.

⚙️ Cài đặt
1. Yêu cầu tiên quyết
Python 3.10 trở lên.

Docker & Docker Compose (Để chạy Database).

Tài khoản Google Cloud Platform (đã bật Books API và Generative Language API).

2. Cài đặt thư viện
Bash

git clone https://github.com/username/book-graph-rag.git
cd book-graph-rag
pip install -r requirements.txt
3. Cấu hình môi trường (.env)
Tạo file .env tại thư mục gốc và điền thông tin:

Ini, TOML

# Google API (Gemini & Books)
GOOGLE_API_KEY=AIzaSy... (Key của bạn)

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
2.1. Crawl dữ liệu (Thu thập): Tải về 10.000 cuốn sách từ nhiều chủ đề khác nhau:

Bash

python crawl_10k_books.py
2.2. Làm sạch dữ liệu (Cleaning): Loại bỏ sách lỗi, lọc HTML tags, lọc ngôn ngữ:

Bash

python process_data.py
2.3. Nạp dữ liệu (Ingestion): Vector hóa và xây dựng đồ thị tri thức (Chạy 1 lần duy nhất):

Bash

python main.py ingest
Bước 3: Chạy Ứng dụng
Khởi chạy giao diện Chatbot trên trình duyệt:

Bash

streamlit run app.py
Truy cập: http://localhost:8501

📂 Cấu trúc Dự án
Plaintext

book-graph-rag/
├── app.py                  # Giao diện chính (Streamlit)
├── main.py                 # CLI entry point (cho Ingest)
├── crawl_10k_books.py      # Script cào dữ liệu lớn
├── process_data.py         # Script làm sạch dữ liệu
├── docker-compose.yml      # Cấu hình Qdrant & Neo4j
├── requirements.txt        # Các thư viện phụ thuộc
├── .env                    # Biến môi trường (API Key)
└── src/
    ├── config.py           # Quản lý cấu hình
    ├── ingest.py           # Logic nạp dữ liệu
    ├── rag_pipeline.py     # Luồng xử lý chính (RAG logic)
    ├── llm_service.py      # Tương tác với Gemini
    ├── vector_db.py        # Tương tác với Qdrant
    └── graph_db.py         # Tương tác với Neo4j
🐛 Debug & Kiểm tra
Nếu gặp lỗi hoặc muốn kiểm tra dữ liệu đã vào chưa:

Kiểm tra số lượng sách: python check_db_status.py (nếu đã tạo file này).

Neo4j Browser: Truy cập http://localhost:7474 (User: neo4j, Pass: password123).

Qdrant Dashboard: Truy cập http://localhost:6333/dashboard.