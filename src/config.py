import os
from dotenv import load_dotenv

# Load file .env
load_dotenv()

class Config:
    # Lấy key từ file .env (AN TOÀN)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Neo4j Cloud Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")
    
    # Qdrant Cloud Configuration
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # API key for Qdrant Cloud
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "movies_vietnamese")  # Collection name
    
    # Cấu hình Model
    EMBEDDING_MODEL = "models/text-embedding-004"
    # Updated to stable model name (gemini-1.5-pro or gemini-2.0-flash-exp)
    CHAT_MODEL = "models/gemini-2.5-flash"  # Stable, reliable model
    # Alternative: "models/gemini-2.0-flash-exp" for faster responses
    
    VECTOR_SIZE = 768  # Embedding dimension (adjust to your embedding model)