import json
import re
import os

# --- CẤU HÌNH ---
INPUT_FILE = "google_books_1000.json"  # File gốc crawl về
OUTPUT_FILE = "books_clean.json"       # File sạch sau khi xử lý

# Chỉ chấp nhận 2 ngôn ngữ này
ALLOWED_LANGUAGES = ["vi", "en"]

# Độ dài tối thiểu của tóm tắt (ngắn quá thì không đủ ý để tạo vector)
MIN_SUMMARY_LENGTH = 50 

def remove_html_tags(text):
    """Xóa các thẻ HTML rác thường gặp trong Google Books (như <p>, <b>, <br>)"""
    if not text: return ""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    # Xóa khoảng trắng thừa (ví dụ: "  xin   chào " -> "xin chào")
    return " ".join(text.split())

def process_books():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Không tìm thấy file '{INPUT_FILE}'. Hãy chạy crawl trước!")
        return

    print(f"📂 Đang đọc dữ liệu thô từ: {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"📊 Tổng số sách ban đầu: {len(raw_data)}")
    
    clean_data = []
    stats = {
        "no_summary": 0,
        "wrong_lang": 0,
        "duplicate": 0,
        "kept": 0
    }
    
    seen_ids = set()

    for book in raw_data:
        # 1. Lọc trùng lặp (Dựa trên ID)
        if book["id"] in seen_ids:
            stats["duplicate"] += 1
            continue

        # 2. Lọc ngôn ngữ
        # Đôi khi Google trả về 'vie' thay vì 'vi', hoặc 'eng' thay vì 'en'. Xử lý linh hoạt:
        lang = book.get("language", "").lower()
        if lang not in ALLOWED_LANGUAGES:
            # Thử map 'vie' -> 'vi', 'eng' -> 'en' nếu cần, nhưng thường Google trả về mã chuẩn 2 ký tự
            stats["wrong_lang"] += 1
            continue

        # 3. Lọc & Làm sạch Tóm tắt (Summary)
        raw_summary = book.get("summary", "")
        clean_summary = remove_html_tags(raw_summary)

        if not clean_summary or len(clean_summary) < MIN_SUMMARY_LENGTH:
            stats["no_summary"] += 1
            continue

        # 4. Chuẩn hóa các trường khác
        clean_book = {
            "id": book["id"],
            "title": remove_html_tags(book.get("title", "No Title")),
            "author": remove_html_tags(book.get("author", "Unknown")),
            "genre": book.get("genre", "General"),
            "language": lang,
            "summary": clean_summary, # Dùng bản đã làm sạch
            "year": book.get("published_date", "")[:4], # Chỉ lấy năm
            "page_count": book.get("page_count", 0)
        }

        clean_data.append(clean_book)
        seen_ids.add(book["id"])
        stats["kept"] += 1

    # Lưu file kết quả
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, indent=4, ensure_ascii=False)

    print("\n" + "="*40)
    print("🧹 KẾT QUẢ XỬ LÝ DỮ LIỆU")
    print("="*40)
    print(f"❌ Loại bỏ (Sai ngôn ngữ):   {stats['wrong_lang']}")
    print(f"❌ Loại bỏ (Không mô tả):    {stats['no_summary']}")
    print(f"❌ Loại bỏ (Trùng lặp):      {stats['duplicate']}")
    print("-" * 40)
    print(f"✅ SÁCH SẠCH ĐƯỢC GIỮ LẠI:  {len(clean_data)}")
    print(f"💾 Đã lưu tại:               {OUTPUT_FILE}")
    print("="*40)
    print("\n👉 Bước tiếp theo: Vào 'src/ingest.py' sửa DATA_FILE = 'books_clean.json'")

if __name__ == "__main__":
    process_books()