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

    def generate_answer(self, context, question, context_provided=True, ask_followups=False, chat_history=None):
        # Cũng thêm retry cho phần chat
        for _ in range(3):
            try:
                # Build a clearer prompt that discourages echoing raw DB records
                if context_provided and context:
                    context_block = f"Available Information:\n{context}\n"
                    context_note = (
                        "Weave database information naturally into your answer. "
                        "Use specific details (titles, years, directors, genres) to support your recommendations. "
                        "Do NOT start with 'Based on the database...' or list raw records."
                    )
                else:
                    context_block = ""
                    context_note = (
                        "No specific matches were found. Answer thoughtfully from your knowledge of cinema, "
                        "drawing on classic examples and established film wisdom."
                    )

                # Format conversation history for context
                history_block = ""
                if chat_history and len(chat_history) > 0:
                    # Get last 4 exchanges to keep context window manageable
                    recent_history = chat_history[-8:] if len(chat_history) > 8 else chat_history
                    history_lines = []
                    for msg in recent_history:
                        role = "Assistant" if msg.get('role') == 'assistant' else "You"
                        content = msg.get('content', '').strip()
                        # Truncate long messages but preserve key info
                        if len(content) > 150:
                            content = content[:150] + "..."
                        history_lines.append(f"{role}: {content}")
                    if history_lines:
                        history_block = "Recent conversation:\n" + "\n".join(history_lines) + "\n\n"

                # Few-shot examples to set tone (Gemini-style)
                examples = """
Example 1:
Q: "Phim hay về tình yêu và cuộc sống?"
A: "Mình gợi ý *Before Sunrise* (1995) của Richard Linklater — một bộ phim đẹp lắm, theo dõi cặp đôi trẻ từ Vienna đến buổi sáng hôm sau. Vì sao nên xem:
- Thoại thiên tài, thẫm sâu về tình yêu và khoảnh khắc quý giá
- Kỹ xảo điện ảnh tinh tế; đạo diễn nổi tiếng với cách kể chuyện nhân vật
- Hoàn hảo nếu bạn thích những câu chuyện yên tĩnh, sâu sắc"

Example 2:
Q: "Muốn xem phim hành động mạnh mẽ"
A: "Hãy thử *Mad Max: Fury Road* (2015) — một kiệt tác hành động hiện đại. Đây là lý do:
- Hành động ngoạn mục, cảnh quay liên tục không dừng trong 120 phút
- Đạo diễn George Miller tạo nên những cảnh quay không quên
- Phù hợp nếu bạn muốn hình ảnh đẹp, âm thanh mạnh, ít thoại nhiều hành động"
"""

                prompt = f"""You are a refined, knowledgeable Vietnamese film expert who speaks naturally and engagingly about cinema.

Your personality:
- Conversational and warm, like chatting with a film enthusiast
- Draw on deep knowledge of cinema history, directors, and genres
- Build naturally on previous points in the conversation
- Share nuanced opinions, not just facts
- Use vivid, descriptive language to paint a picture of films

{history_block}
Available movie information:
{context_block}

User's question: {question}

Guidelines for your response:
1. **Open authentically**: Start with a natural thought or direct recommendation—no "Based on the database..." or formal preamble
2. **Be specific and detailed**:
   - Include titles, release years, and director names
   - Explain *why* a film matches the request with concrete details (tone, themes, cinematography, performances)
   - Reference cast, cinematography, or soundtrack if relevant
3. **Structure naturally**:
   - Lead with your main recommendation or insight
   - Follow with 2–3 reasons why it fits, using specific examples
   - Suggest 2–3 related films (title + 1–2 sentence reason each)
4. **Stay conversational**:
   - Use connecting phrases like "What makes it special...", "You'll appreciate...", "The beauty of..."
   - Don't sound like a database; sound like someone passionate about films
   - If no database match exists, draw from your film knowledge confidently
5. **Length**: Aim for 200–350 words—enough for depth, not overwhelming
6. **Language**: Use Vietnamese naturally with film terminology where appropriate

{examples}

{context_note}

Now answer the user's question with enthusiasm and thoughtfulness:"""
                
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                print(f"⚠️ Lỗi khi chat: {e}. Đợi 5s...")
                time.sleep(5)
        return "Xin lỗi, hệ thống đang quá tải, vui lòng thử lại sau."