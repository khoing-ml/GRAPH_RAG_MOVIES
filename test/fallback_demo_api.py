"""
Simplified API to demo fallback mechanism WITHOUT database dependencies
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import sys
import os
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

# Initialize fallback LLM
fallback_llm = None

@app.on_event("startup")
async def startup():
    global fallback_llm
    print("🚀 Starting Fallback Demo API...")
    try:
        fallback_llm = GeminiService()
        print("   ✓ Fallback LLM initialized")
    except Exception as e:
        print(f"   ❌ Fallback init error: {e}")

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Demo endpoint - always uses fallback for general knowledge
    """
    if not fallback_llm:
        return {"error": "Fallback LLM not initialized"}
    
    question = request.message
    print(f"📩 Question: {question}")
    
    # Create system context for general knowledge
    system_context = """You are a knowledgeable AI assistant with expertise in entertainment, movies, actors, directors, and general knowledge.

Your role is to provide accurate, comprehensive answers to user questions. You have broad knowledge about:
- Cinema history and film industry
- Actors, directors, and filmmakers
- Movie franchises and series
- Awards and recognition (Oscars, Golden Globes, etc.)
- General entertainment facts
- And other general knowledge topics

Provide direct, factual answers without mentioning databases or technical limitations."""

    fallback_prompt = f"""Please answer this question directly using your general knowledge:

"{question}"

Provide a comprehensive, factual answer."""

    full_prompt = f"{system_context}\n\n{fallback_prompt}"
    
    try:
        answer = fallback_llm.model.generate_content(
            full_prompt,
            safety_settings=fallback_llm.safety_settings
        ).text
        
        print(f"✅ Generated answer ({len(answer)} chars)")
        
        return {
            "message": answer,
            "time": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "message": f"Error generating response: {e}",
            "time": datetime.now().isoformat()
        }

@app.get("/")
async def root():
    return {"status": "Fallback Demo API Running", "endpoint": "/api/chat"}

# Serve static files (movie_showcase.html and other assets)
static_dir = os.path.join(os.path.dirname(__file__))
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("🌟 Starting Fallback Demo API on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
