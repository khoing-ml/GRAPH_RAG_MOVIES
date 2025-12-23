"""
FastAPI backend for Movie GraphRAG chat application.
Exposes REST endpoints for chat, conversation history, and ingestion.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json

from src.rag_pipeline import GraphRAG
from src import ingest

# Initialize FastAPI app
app = FastAPI(title="Movie GraphRAG API", version="2.0.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system
try:
    rag = GraphRAG()
except Exception as e:
    print(f"❌ Error initializing RAG: {e}")
    rag = None


# ============= Request/Response Models =============

class ChatMessage(BaseModel):
    role: str
    content: str
    time: Optional[str] = None
    rating: Optional[int] = None  # 1 for thumbs up, -1 for thumbs down


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    message: str
    time: str


class MovieData(BaseModel):
    title: str
    year: Optional[int] = None
    genres: Optional[List[str]] = None
    overview: Optional[str] = None
    cast: Optional[List[str]] = None
    director: Optional[str] = None


class FavoriteRequest(BaseModel):
    movie_id: str
    movie_data: MovieData


class RatingRequest(BaseModel):
    message_index: int
    rating: int  # 1 or -1


# ============= Chat Endpoints =============

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a response from the RAG system.
    """
    if not rag:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        from datetime import datetime
        
        chat_history = None
        if request.history:
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.history
            ]
        
        answer = rag.query(request.message.strip(), chat_history=chat_history)
        
        return ChatResponse(
            message=answer,
            time=datetime.now().isoformat()
        )
    except Exception as e:
        print(f"❌ Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )


@app.get("/api/chat/stream")
async def chat_stream(message: str, history: Optional[str] = None):
    """
    Stream chat responses for real-time typing effect.
    """
    if not rag:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    async def event_generator():
        try:
            chat_history = None
            if history:
                chat_history = json.loads(history)
            
            answer = rag.query(message.strip(), chat_history=chat_history)
            
            # Stream response word by word
            words = answer.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ============= Favorites Endpoints =============

@app.post("/api/favorites")
async def add_favorite(favorite: FavoriteRequest):
    """
    Add a movie to favorites.
    """
    try:
        # Favorites stored on client side via localStorage
        return {
            "status": "success",
            "message": f"Added {favorite.movie_data.title} to favorites"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/favorites")
async def get_favorites():
    """
    Get all favorites (managed client-side).
    """
    return {
        "message": "Favorites are stored in your browser's localStorage",
        "sync": "To sync across devices, use the export feature"
    }


# ============= Rating Endpoints =============

@app.post("/api/rate")
async def rate_response(request: RatingRequest):
    """
    Rate a chat response (thumbs up/down).
    """
    try:
        # Store rating (could be saved to database)
        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "rating": "👍" if request.rating > 0 else "👎"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= Search Suggestions =============

@app.get("/api/suggestions")
async def get_suggestions():
    """
    Get movie genre suggestions for quick search.
    """
    return {
        "genres": [
            "Action Films",
            "Comedy",
            "Drama",
            "Horror",
            "Sci-Fi",
            "Romance",
            "Thriller",
            "Animation"
        ],
        "popular_searches": [
            "Best movies of 2024",
            "Movies like Inception",
            "Top rated movies",
            "Hidden gems"
        ]
    }


# ============= Ingestion Endpoints =============

@app.post("/api/ingest")
async def run_ingestion():
    """
    Trigger the ingestion pipeline.
    """
    try:
        ingest.run_ingestion()
        return {
            "status": "success",
            "message": "Ingestion completed successfully"
        }
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.post("/api/fix-dimension")
async def fix_dimension():
    """
    Fix the vector dimension mismatch in Qdrant.
    """
    try:
        from fix_vector_dimension import fix_dimension as fix_fn
        fix_fn()
        return {
            "status": "success",
            "message": "Vector dimension fixed"
        }
    except Exception as e:
        print(f"❌ Fix dimension error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fix failed: {str(e)}"
        )


# ============= Health Check =============

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "rag_initialized": rag is not None,
        "version": "2.0.0"
    }


# ============= Serve Frontend =============

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Movie GraphRAG API server (v2.0.0)...")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("🌐 Frontend: http://localhost:8000")
    print("💾 Features: Streaming, Favorites, Ratings, History, Export\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
