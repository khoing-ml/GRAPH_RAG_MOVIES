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

    def generate_answer(self, context, question, context_provided=True, ask_followups=False):
        # Cũng thêm retry cho phần chat
        for _ in range(3):
            try:
                # Build a clearer prompt that discourages echoing raw DB records
                if context_provided and context:
                    context_block = f"Context (short):\n{context}\n"
                    context_note = (
                        "Use the database context only to support your concise answer. "
                        "Do NOT repeat DB entries verbatim or preface the answer with long DB quotes."
                    )
                else:
                    context_block = ""
                    context_note = (
                        "The database did not return relevant results. Answer from your general film knowledge; "
                        "be concise and natural."
                    )

                # small few-shot example to set tone
                example = (
                    "Example:\nQuestion: 'Gợi ý phim siêu anh hùng gần đây, phù hợp cho gia đình'\n"
                    "Answer: 'Spider-Man: No Way Home (2021) — Hài hước, cảm động; phù hợp cho gia đình.\n"
                    "- Vì có yếu tố hành động và hài nhẹ; đạo diễn: Jon Watts.\n'\n\n"
                )

                prompt = f"""
You are a helpful, concise Vietnamese-speaking film assistant. Be natural, direct, and prioritize useful information.

{context_block}
User question: {question}

Instructions:
- Start with one short sentence recommendation or answer (no preface).
- Then give 1–3 brief bullets explaining why (use DB facts if available).
- Optionally list up to 3 related films (title + 1 short reason each).
- If the DB had no matches, answer from general knowledge and do not say long apologetic DB messages.
- Do NOT echo entire database records or say things like "Dựa trên cơ sở dữ liệu..." before your answer; instead integrate facts naturally.
- Keep it concise (<=250 words) and conversational.

{context_note}

{example}
"""
                # If follow-up questions are requested, instruct the model to add them
                if ask_followups:
                    prompt += (
                        "\nCâu hỏi làm rõ:\n- (Hỏi 1–2 câu ngắn, tập trung vào sở thích hoặc yêu cầu cụ thể của người dùng)"
                    )
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                print(f"⚠️ Lỗi khi chat: {e}. Đợi 5s...")
                time.sleep(5)
        return "Xin lỗi, hệ thống đang quá tải, vui lòng thử lại sau."