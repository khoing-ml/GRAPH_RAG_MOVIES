# Movie GraphRAG - AI-Powered Movie Discovery

A sophisticated RAG (Retrieval-Augmented Generation) system for movie recommendations and information using Google Gemini, Qdrant vector database, and Neo4j graph database.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                       │
│                  Modern Chat Interface                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/JSON
┌──────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                           │
│              /api/chat, /api/ingest, etc                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   Qdrant DB       Neo4j DB      Gemini LLM
   (Vectors)      (Graph)      (Generation)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
QDRANT_URL=http://localhost:6333
```

### 3. Run the Backend

```bash
python main_api.py
```

The API will start at **http://localhost:8000**

### 4. Access the Frontend

Open your browser and visit:
- **UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger/OpenAPI)

## API Endpoints

### Chat
```bash
POST /api/chat
```
Send a message and get a response with conversation history.

**Request:**
```json
{
    "message": "Recommend a good action movie",
    "history": [
        {"role": "user", "content": "What movies are available?"},
        {"role": "assistant", "content": "..."}
    ]
}
```

**Response:**
```json
{
    "message": "I recommend...",
    "time": "2025-12-23T10:30:00"
}
```

### Ingestion
```bash
POST /api/ingest
```
Trigger the movie ingestion pipeline to load data into the system.

### Health Check
```bash
GET /api/health
```
Check if the system is running and RAG is initialized.

## Features

### Frontend UI
- ✅ Gemini-like chat interface
- ✅ Real-time message streaming with typing indicator
- ✅ Dark/Light mode toggle
- ✅ Persistent chat history (localStorage)
- ✅ Mobile-responsive design
- ✅ Action buttons for quick suggestions
- ✅ Auto-scrolling to latest messages

### Backend Services
- ✅ Conversational RAG with history context
- ✅ Vector search (semantic similarity)
- ✅ Graph enrichment (directors, cast, genres)
- ✅ LLM response generation (Gemini)
- ✅ Vietnamese support
- ✅ Follow-up question suggestions
- ✅ CORS support for frontend

## System Components

### src/llm_service.py
- `GeminiService`: Handles embeddings and text generation
- Uses Google Gemini API with retry logic
- Quota handling for rate limits

### src/rag_pipeline.py
- `GraphRAG`: Main RAG orchestrator
- 3-step pipeline: Vector search → Graph enrichment → LLM generation
- Fallback to LLM when database has no hits

### src/vector_db.py
- `QdrantService`: Qdrant vector database wrapper
- Semantic search on movie descriptions

### src/graph_db.py
- `Neo4jService`: Neo4j graph database integration
- Movie nodes, relationships, cast/director info

### src/ingest.py
- Movie data ingestion pipeline
- Vector embedding and graph node creation

## Customization

### Change Frontend Theme
Edit `frontend/index.html` CSS variables:
```css
:root {
    --accent: #1e40af;  /* Change accent color */
    --primary-bg: #0f0f0f;  /* Dark background */
}
```

### Modify LLM Prompt
Edit `src/llm_service.py` in the `generate_answer()` method to change the system prompt.

### Add Custom Endpoints
Edit `main_api.py` to add new FastAPI routes.

## Troubleshooting

### Frontend not showing
- Ensure `frontend/` directory exists with `index.html`
- Check browser console for errors (F12)
- Verify API is running on port 8000

### Chat not responding
- Check API is initialized: `http://localhost:8000/api/health`
- Check `.env` file has valid API keys
- Check Qdrant and Neo4j are running

### Slow responses
- Increase Qdrant search results: edit `src/rag_pipeline.py` `top_k` parameter
- Optimize LLM prompt length
- Check network latency to Qdrant/Neo4j/Gemini

## Production Deployment

### Using Gunicorn + Nginx
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main_api:app
```

### Using Docker
```bash
docker build -t movie-graphrag .
docker run -p 8000:8000 movie-graphrag
```

### Using Systemd Service
Create `/etc/systemd/system/movie-graphrag.service`:
```ini
[Unit]
Description=Movie GraphRAG API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/GRAPH_RAG_MOVIES
ExecStart=/usr/bin/python3 main_api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Development

### Add a new endpoint
```python
@app.get("/api/my-endpoint")
async def my_endpoint():
    return {"status": "ok"}
```

### Update frontend
Edit `frontend/index.html` directly. Hot reloading not available; refresh browser after changes.

### Debug chat flow
Enable verbose logging in `src/rag_pipeline.py`:
```python
print(f"Debug: {message}")
```

## Performance Tips

1. **Caching**: Implement Redis caching for frequently asked questions
2. **Batch processing**: Process multiple queries in parallel
3. **Streaming responses**: Use Server-Sent Events (SSE) for real-time streaming
4. **Database optimization**: Add indexes to Neo4j and Qdrant

## Contributing

Feel free to fork and submit PRs!

## License

MIT

## Support

For issues and questions, check the logs or create an issue on GitHub.

---

**Built with ❤️ using FastAPI, Gemini, Qdrant, and Neo4j**
