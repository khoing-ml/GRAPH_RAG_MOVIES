"""
Demo API for Augmentation Mode - Combining Database + General Knowledge
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sys
sys.path.insert(0, '/home/khoi/Code/GRAPH_RAG_MOVIES')

from src.llm_service import GeminiService

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLMs
llm = None
fallback_llm = None

@app.on_event("startup")
async def startup():
    global llm, fallback_llm
    print("🚀 Starting Augmentation Demo API...")
    try:
        llm = GeminiService()
        fallback_llm = GeminiService()
        print("   ✓ Both LLMs initialized")
    except Exception as e:
        print(f"   ❌ Init error: {e}")

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Demo augmentation - combines simulated database answer with general knowledge
    """
    if not llm or not fallback_llm:
        return {"error": "LLMs not initialized"}
    
    question = request.message
    print(f"📩 Question: {question}")
    
    # Simulate database answer (in real system, this comes from GraphRAG)
    print("  🎬 Getting database answer...")
    database_prompt = f"""Based on our movie database, answer this question about movies:

"{question}"

Provide specific information if you know it, or admit if the information is limited. Focus on factual details."""

    try:
        database_answer = llm.model.generate_content(
            database_prompt,
            safety_settings=llm.safety_settings
        ).text
        print(f"  ✓ Database answer ({len(database_answer)} chars)")
    except Exception as e:
        return {"error": f"Database query error: {e}", "time": datetime.now().isoformat()}
    
    # Get general knowledge context
    print("  🌐 Getting general knowledge...")
    general_prompt = f"""Provide general knowledge context about this question:

"{question}"

Focus on background information, industry facts, historical context, or related details. Be concise but informative."""

    system_context = """You are a knowledgeable entertainment and cinema expert. Provide contextual information to enrich answers about movies, actors, and film industry."""

    full_general_prompt = f"{system_context}\n\n{general_prompt}"
    
    try:
        general_knowledge = fallback_llm.model.generate_content(
            full_general_prompt,
            safety_settings=fallback_llm.safety_settings
        ).text
        print(f"  ✓ General knowledge ({len(general_knowledge)} chars)")
    except Exception as e:
        return {"error": f"General knowledge error: {e}", "time": datetime.now().isoformat()}
    
    # Synthesize both
    print("  🔀 Synthesizing...")
    synthesis_prompt = f"""Synthesize information from two sources into a comprehensive answer.

USER QUESTION: "{question}"

SOURCE 1 - Database Information:
{database_answer}

SOURCE 2 - General Knowledge:
{general_knowledge}

Create a unified answer that:
1. Prioritizes specific facts from Source 1
2. Enriches with context from Source 2
3. Maintains accuracy
4. Reads naturally (don't mention sources)

Write a comprehensive, flowing answer."""

    try:
        final_answer = llm.model.generate_content(
            synthesis_prompt,
            safety_settings=llm.safety_settings
        ).text
        
        print(f"  ✅ Synthesized ({len(final_answer)} chars)")
        
        return {
            "message": final_answer,
            "time": datetime.now().isoformat(),
            "metadata": {
                "database_length": len(database_answer),
                "general_knowledge_length": len(general_knowledge),
                "final_length": len(final_answer),
                "mode": "augmented"
            }
        }
    except Exception as e:
        return {"error": f"Synthesis error: {e}", "time": datetime.now().isoformat()}

@app.get("/")
async def root():
    return {"status": "Augmentation Demo API Running", "endpoint": "/api/chat"}

if __name__ == "__main__":
    import uvicorn
    print("🌟 Starting Augmentation Demo API on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
