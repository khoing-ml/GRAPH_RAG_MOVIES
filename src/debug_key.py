import requests
import os
from dotenv import load_dotenv

# Load file .env
load_dotenv()

def test_api_key():
    api_key = os.getenv("GOOGLE_API_KEY")
    
    print("="*40)
    print(f"🔑 Đang kiểm tra Key: {api_key}")
    
    if not api_key:
        print("❌ LỖI: Không tìm thấy Key trong file .env")
        return

    # URL test thử 1 cuốn sách
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": "harry potter",
        "maxResults": 1,
        "key": api_key
    }

    try:
        response = requests.get(url, params=params)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ KẾT QUẢ: Key hoạt động TỐT!")
            print("📖 Tìm thấy sách:", response.json()['items'][0]['volumeInfo']['title'])
        else:
            print("❌ KẾT QUẢ: Key bị lỗi!")
            print("⚠️ NỘI DUNG LỖI TỪ GOOGLE:")
            # In ra toàn bộ nội dung lỗi để biết nguyên nhân
            print(response.text) 
            
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")

    print("="*40)

if __name__ == "__main__":
    test_api_key()