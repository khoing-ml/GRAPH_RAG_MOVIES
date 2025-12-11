import json
import os
from qdrant_client.models import PointStruct
from .llm_service import GeminiService
from .vector_db import QdrantService
from .graph_db import Neo4jService
from tqdm import tqdm

DATA_FILE = "notebooks/google_books_10k.json"

def run_ingestion():
    if not os.path.exists(DATA_FILE):
        print(f"Lỗi: Không tìm thấy file '{DATA_FILE}'. Hãy chạy notebook crawl dữ liệu trước!")
        return

    print(f"📂 Đang đọc dữ liệu từ {DATA_FILE}...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_books = json.load(f)

    if not raw_books:
        print("File dữ liệu rỗng!")
        return

    print(f"🚀 Bắt đầu xử lý {len(raw_books)} cuốn sách...")
    
    llm = GeminiService()
    vectordb = QdrantService()
    graphdb = Neo4jService()

    batch_points = []
    batch_size = 20 # Gom nhóm để insert vào Qdrant cho nhanh

    for book in tqdm(raw_books, desc="Ingesting"):
        try:
            title = book.get("title", "No Title")
            summary = book.get("summary", "")
            
            # Nếu không có nội dung tóm tắt, bỏ qua vì không tạo vector được
            if not summary: 
                continue

            # 1. Tạo Vector Embedding (Title + Summary + Genre)
            text_to_embed = f"Title: {title}. Genre: {book.get('genre')}. Summary: {summary}"
            embedding = llm.get_embedding(text_to_embed)
            
            if embedding:
                # Tạo ID số nguyên dương cho Qdrant từ chuỗi ID gốc
                point_id = hash(book["id"]) & ((1<<64)-1)

                batch_points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "book_id": book["id"],  
                        "title": title,
                        "language": book.get("language", "en")
                    }
                ))

            # 2. Lưu vào Graph Database
            graphdb.add_book_data(book)

            # Insert Batch nếu đầy
            if len(batch_points) >= batch_size:
                vectordb.upsert_vectors(batch_points)
                batch_points = []

        except Exception as e:
            print(f"Lỗi khi xử lý sách '{title}': {e}")

    # Insert nốt số còn lại
    if batch_points:
        vectordb.upsert_vectors(batch_points)
        
    graphdb.close()
    print("HOÀN TẤT NẠP DỮ LIỆU!")

if __name__ == "__main__":
    run_ingestion()