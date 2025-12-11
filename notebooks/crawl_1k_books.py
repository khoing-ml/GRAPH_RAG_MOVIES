import requests
import json
import time
import os
from tqdm import tqdm
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

# --- CẤU HÌNH ---
API_KEY = os.getenv("GOOGLE_API_KEY", "") 
OUTPUT_FILE = "google_books_10k.json"
TARGET_TOTAL = 10000  # Mục tiêu 10.000 cuốn
CHECKPOINT_INTERVAL = 500 # Cứ mỗi 500 cuốn thì lưu file 1 lần (đề phòng mất điện/lỗi)

# Kho chủ đề KHỔNG LỒ (Đủ để quét 10k sách)
TOPIC_POOL = [
    # Công nghệ & IT
    "Artificial Intelligence", "Machine Learning", "Data Science", "Python Programming", 
    "Java Programming", "JavaScript", "Blockchain", "Cyber Security", "Cloud Computing",
    "Software Architecture", "DevOps", "Web Development", "Database Design", "Algorithm",
    
    # Khoa học
    "Physics", "Astrophysics", "Quantum Mechanics", "Chemistry", "Biology", "Genetics",
    "Neuroscience", "Mathematics", "Statistics", "Environmental Science", "Astronomy",
    
    # Kinh tế & Kinh doanh
    "Economics", "Marketing", "Startup", "Finance", "Accounting", "Investing", 
    "Management", "Leadership", "Business Strategy", "Stock Market", "Real Estate",
    
    # Lịch sử & Xã hội
    "World History", "Vietnam History", "US History", "European History", "Ancient Egypt",
    "Sociology", "Anthropology", "Political Science", "Geography", "Archeology",
    
    # Văn học & Giả tưởng
    "Science Fiction", "Fantasy", "Mystery", "Thriller", "Horror", "Romance", 
    "Historical Fiction", "Poetry", "Classics", "Comics", "Manga",
    
    # Đời sống & Kỹ năng
    "Psychology", "Philosophy", "Self-Help", "Health & Fitness", "Cooking", "Baking",
    "Travel", "Photography", "Art History", "Music Theory", "Gardening", "Architecture",
    "Design", "Fashion", "Parenting", "Education", "Spirituality", "Meditation"
]

# Giới hạn số lượng lấy tối đa mỗi chủ đề (Google thường bắt đầu trả về rác sau index 500)
MAX_BOOKS_PER_GENRE = 600 

def clean_text(text):
    if not text: return ""
    return text.strip()

def save_checkpoint(data, filename):
    """Hàm lưu file an toàn"""
    print(f"\n💾 Đang lưu checkpoint ({len(data)} cuốn)...")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(list(data.values()), f, indent=4, ensure_ascii=False)

def fetch_books_by_genre(genre, start_index=0, max_results=40):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": f"subject:{genre}",
        "startIndex": start_index,
        "maxResults": max_results,
        "printType": "books",
        "orderBy": "relevance",
        "langRestrict": "en,vi" # Ưu tiên Anh và Việt
    }
    
    if API_KEY:
        params["key"] = API_KEY

    # Cơ chế Retry (thử lại 3 lần nếu lỗi mạng)
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return response.json().get("items", [])
            elif response.status_code == 429:
                wait_time = (attempt + 1) * 5
                print(f"⚠️ Quota exceeded. Đợi {wait_time}s...")
                time.sleep(wait_time)
            elif response.status_code == 403:
                print("⚠️ Lỗi 403: Kiểm tra lại API Key hoặc quyền truy cập!")
                return []
            else:
                print(f"⚠️ Error {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}. Thử lại...")
            time.sleep(2)
    
    return []

def main():
    if not API_KEY:
        print("❌ LỖI: Chưa tìm thấy GOOGLE_API_KEY trong file .env")
        return

    unique_books = {}
    
    # Nếu file đã tồn tại, đọc vào để crawl tiếp (Resume)
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                for book in existing_data:
                    unique_books[book["id"]] = book
            print(f"🔄 Đã tìm thấy dữ liệu cũ: {len(unique_books)} cuốn. Đang crawl tiếp...")
        except:
            print("⚠️ File cũ bị lỗi, sẽ crawl mới từ đầu.")

    print(f"🚀 Bắt đầu chiến dịch 10K BOOKS (Mục tiêu: {TARGET_TOTAL})...")

    # Duyệt qua từng chủ đề trong kho
    for genre_idx, genre in enumerate(TOPIC_POOL):
        # Nếu đã đủ chỉ tiêu thì dừng luôn
        if len(unique_books) >= TARGET_TOTAL:
            print("\n🎉🎉🎉 ĐÃ ĐẠT MỤC TIÊU 10.000 CUỐN! DỪNG LẠI.")
            break

        print(f"\n📂 [{genre_idx + 1}/{len(TOPIC_POOL)}] Đang khai thác chủ đề: {genre.upper()}")
        
        books_fetched_for_genre = 0
        start_index = 0
        consecutive_empty_pages = 0
        
        # Thanh progress bar cho từng chủ đề
        pbar = tqdm(total=MAX_BOOKS_PER_GENRE, desc=f"   Mining {genre}", leave=False)
        
        while books_fetched_for_genre < MAX_BOOKS_PER_GENRE:
            # Nếu đã đủ tổng 10k thì break ngay lập tức
            if len(unique_books) >= TARGET_TOTAL:
                break

            items = fetch_books_by_genre(genre, start_index)
            
            if not items:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 2: # Nếu 2 lần liên tiếp không có sách -> Hết sách
                    break
                start_index += 40
                time.sleep(1)
                continue
            
            consecutive_empty_pages = 0 # Reset bộ đếm lỗi
            
            for item in items:
                book_id = item["id"]
                info = item.get("volumeInfo", {})
                
                # LỌC SƠ BỘ
                description = clean_text(info.get("description", ""))
                # Nới lỏng điều kiện lọc để lấy được nhiều sách hơn (>= 30 ký tự)
                if not description or len(description) < 30:
                    continue 

                authors = info.get("authors", ["Unknown"])
                
                book_data = {
                    "id": book_id,
                    "title": info.get("title", "No Title"),
                    "author": authors[0] if authors else "Unknown",
                    "genre": genre, 
                    "language": info.get("language", "en"),
                    "summary": description,
                    "published_date": info.get("publishedDate", "Unknown")[:4],
                    "page_count": info.get("pageCount", 0)
                }
                
                # Chỉ thêm nếu chưa có trong kho
                if book_id not in unique_books:
                    unique_books[book_id] = book_data
                    pbar.update(1)
                    books_fetched_for_genre += 1

                    # --- CHECKPOINT: Lưu file định kỳ ---
                    if len(unique_books) % CHECKPOINT_INTERVAL == 0:
                        save_checkpoint(unique_books, OUTPUT_FILE)
                        print(f"   --> Đã gom được tổng: {len(unique_books)} cuốn.")

            start_index += 40 
            time.sleep(1.0) # Nghỉ 1s để Google không chặn
        
        pbar.close()
        print(f"   ✅ Kết thúc chủ đề {genre}. Tổng kho hiện tại: {len(unique_books)}")

    # Lưu lần cuối cùng
    save_checkpoint(unique_books, OUTPUT_FILE)
    print(f"\n✅ HOÀN TẤT CHIẾN DỊCH! Tổng thu thập: {len(unique_books)} cuốn sách.")
    print(f"💾 File lưu tại: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()