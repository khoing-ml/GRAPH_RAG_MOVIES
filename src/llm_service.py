import google.generativeai as genai
from .config import Config
import time
import random

class GeminiService:
    def __init__(self):
        if not Config.GOOGLE_API_KEY:
            raise ValueError("Chưa cấu hình GOOGLE_API_KEY trong file .env")
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(Config.CHAT_MODEL)

    def get_embedding(self, text, task_type="retrieval_document"):
        # Thử tối đa 5 lần nếu gặp lỗi
        retries = 5
        for attempt in range(retries):
            try:
                result = genai.embed_content(
                    model=Config.EMBEDDING_MODEL,
                    content=text,
                    task_type=task_type
                )
                return result['embedding']
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    wait_time = 20 + random.randint(1, 5) 
                    print(f"\n⚠️ Hết quota (429). Đang đợi {wait_time}s để hồi phục...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️ Lỗi khác: {e}. Thử lại sau 2s...")
                    time.sleep(2)
        
        print("❌ Đã thử nhiều lần nhưng thất bại.")
        return None

    def generate_answer(self, context, question):
        # Cũng thêm retry cho phần chat
        for _ in range(3):
            try:
                prompt = f"""
                Bạn là một trợ lý thư viện thông thái.
                Hãy trả lời câu hỏi dựa trên ngữ cảnh sau:
                {context}
                
                Câu hỏi: {question}
                """
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"⚠️ Lỗi khi chat: {e}. Đợi 5s...")
                time.sleep(5)
        return "Xin lỗi, hệ thống đang quá tải, vui lòng thử lại sau."