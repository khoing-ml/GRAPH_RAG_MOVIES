import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .config import Config
import time
import random

class GeminiService:
    def __init__(self):
        if not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured in .env file")
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(Config.CHAT_MODEL)
        
        # Simple safety settings for movie content (no complex handling)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    def get_embedding(self, text, task_type="retrieval_document"):
        # Try up to 5 times if error occurs
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
                    print(f"\n⚠️ Quota exceeded (429). Waiting {wait_time}s to recover...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️ Other error: {e}. Retrying in 2s...")
                    time.sleep(2)
        
        print("❌ Failed after multiple retries.")
        return None

    def generate_answer(self, context, question, context_provided=True, ask_followups=False, chat_history=None):
        # Retry with safety handling
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Build GROUNDED prompt - minimize hallucination
                if context_provided and context:
                    context_block = f"🎬 Retrieved Movie Information:\n{context}\n"
                    context_note = (
                        "**CRITICAL ANTI-HALLUCINATION RULES:**\n"
                        "1. PRIMARY SOURCE: Use ONLY information from the Retrieved Movie Information above\n"
                        "2. FACTUAL ACCURACY: Every specific detail (dates, names, plots) MUST come from provided context\n"
                        "3. NO SPECULATION: Do not add information not present in context (release dates, cast, plot details)\n"
                        "4. IF UNCERTAIN: Say 'Based on available information...' or admit when information is incomplete\n"
                        "5. CITATIONS: When mentioning specifics, they must be verifiable from context\n"
                        "6. GENERAL KNOWLEDGE: Only use for broad film concepts (genres, styles) - NOT specific film facts\n\n"
                        "✅ ALLOWED: 'This is an action movie' (genre classification from context)\n"
                        "❌ FORBIDDEN: 'Releases in December 2025' (unless explicitly in context)\n"
                        "❌ FORBIDDEN: 'James Cameron promised...' (unless quote in context)\n"
                        "❌ FORBIDDEN: 'Oona Chaplin stars in it' (unless listed in context cast)"
                    )
                else:
                    context_block = ""
                    context_note = (
                        "**NO CONTEXT MODE:**\n"
                        "No specific movie information was retrieved. You can provide:\n"
                        "- General film recommendations (common knowledge films)\n"
                        "- Genre definitions and characteristics\n"
                        "- BUT: Be honest that you don't have specific database details\n"
                        "- Say: 'I couldn't find specific information, but I can suggest...'"
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

                # Few-shot examples showing hybrid knowledge usage
                # Few-shot examples showing GROUNDED responses
                examples = """
Example 1 (GROUNDED - using context facts only):
Retrieved Context: "Title: Titanic. Year: 1997. Director: James Cameron. Overview: Epic romance and disaster on the Titanic ship in 1912..."
Q: "When was Titanic released?"
A: "Titanic was released in 1997, directed by James Cameron. The film tells the tragic love story of Jack and Rose during the 1912 Titanic disaster."

Example 2 (HONEST when info missing):
Retrieved Context: "Title: Avatar: Fire and Ash. Overview: The Sully family explores the Ash People tribe..."
Q: "When does Avatar Fire and Ash come out?"
A: "Based on available information, *Avatar: Fire and Ash* is the third film in the Avatar series, focusing on the Ash People tribe. However, I couldn't find the exact release date in the data. You can check IMDB or the official page for the precise release date."

Example 3 (AVOID speculation):
Retrieved Context: "Title: Inception. Director: Christopher Nolan. Cast: Leonardo DiCaprio, Tom Hardy..."
Q: "Is there a sequel to Inception?"
A: "Based on available information about *Inception* (2010), the film was directed by Christopher Nolan starring Leonardo DiCaprio and Tom Hardy. I don't see any information about a sequel in the data. To date, Inception remains a standalone film."

Example 4 (GENERAL recommendation - allowed):
Retrieved Context: [No specific match]
Q: "Good romantic movies?"
A: "I couldn't find specific information, but I can suggest some classic romance films:
- *Before Sunrise* (1995) - Richard Linklater
- *Eternal Sunshine of the Spotless Mind* (2004) - Michel Gondry  
- *La La Land* (2016) - Damien Chazelle

These are well-known romance films with emotional depth. You can search for them to learn more details!"

Example 5 (STICK TO CONTEXT):
Retrieved Context: "Title: The Dark Knight. Year: 2008. Cast: Christian Bale (Batman), Heath Ledger (Joker)..."
Q: "Did The Dark Knight win Oscars?"
A: "Based on available information, *The Dark Knight* (2008) stars Christian Bale and Heath Ledger. Regarding Oscar awards, I don't see specific information in the data.

(Note: In reality Heath Ledger won Best Supporting Actor Oscar, but this info isn't in context so we don't mention it)"
"""

                prompt = f"""You are a GROUNDED film assistant. Your primary goal is FACTUAL ACCURACY.

Your personality:
- Honest and careful with facts
- Use ONLY information from provided context for specific details
- Admit when you don't have complete information
- Friendly but prioritize accuracy over confidence
- Always respond in English

{history_block}
{context_block}

User's question: {question}

{context_note}

Guidelines for GROUNDED response:
1. **Factual Discipline**:
   - Specific facts (dates, names, plots) → MUST be in context
   - If not in context → Say "I couldn't find information about..." or "Based on available data..."
   - Never fabricate release dates, cast members, or plot details
   
2. **What you CAN use from general knowledge**:
   - Genre definitions (e.g., "Action movies typically have...")
   - Film theory concepts (e.g., "Cinematography is...")
   - Common film recommendations (widely known classics)
   
3. **What you MUST NOT invent**:
   - Release dates for specific films
   - Cast and crew details
   - Plot specifics or quotes
   - Award wins or nominations
   - Production details or budgets

4. **Response structure**:
   - Lead with facts from context
   - Clearly indicate when extrapolating: "Based on the information..."
   - If missing info: "I couldn't find information about [X] in the data"
   - End with helpful suggestion if needed

{examples}

Now answer the user's question following these ANTI-HALLUCINATION rules strictly.

Response (in English, grounded in provided context):"""
                
                # LOWER temperature for less creativity = less hallucination
                generation_config = genai.types.GenerationConfig(
                    temperature=0.3,  # ⚡ Giảm từ default (0.7) xuống 0.3
                    top_p=0.8,        # Giảm diversity
                    top_k=20,         # Giảm candidate pool
                    max_output_tokens=2048,  # Increased from 800 for complete answers
                )
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings
                )
                
                return response.text.strip()
                    
            except Exception as e:
                print(f"⚠️ Error during chat: {e}. Waiting 5s...")
                time.sleep(5)
        return "Sorry, the system is currently overloaded. Please try again later."