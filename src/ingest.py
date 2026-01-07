import json
import os
from qdrant_client.models import PointStruct
from .llm_service import GeminiService
from .vector_db import QdrantService
from .graph_db import Neo4jService
from tqdm import tqdm

DATA_FILE = "notebooks/movies.json"

def run_ingestion():
    if not os.path.exists(DATA_FILE):
        print(f"Error: File '{DATA_FILE}' not found. Please run the data crawl notebook first!")
        return

    print(f"📂 Reading data from {DATA_FILE}...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_movies = json.load(f)

    if not raw_movies:
        print("Data file is empty!")
        return

    print(f"🚀 Starting to process {len(raw_movies)} items (movies)...")
    
    llm = GeminiService()
    vectordb = QdrantService()
    graphdb = Neo4jService()

    batch_points = []
    batch_size = 20 # Batch together for faster Qdrant insertion

    for movie in tqdm(raw_movies, desc="Ingesting"):
        try:
            title = movie.get("title", "No Title")
            overview = movie.get("overview", "")
            
            # Skip if no description available (can't create vector)
            if not overview:
                continue

            # 1. Create Vector Embedding (Title + Overview + Genres)
            text_to_embed = f"Title: {title}. Genres: {movie.get('genres')}. Overview: {overview}"
            embedding = llm.get_embedding(text_to_embed)
            
            if embedding:
                # Use tmdb id if present, else hash
                original_id = movie.get('tmdb_id') or movie.get('id') or movie.get('movie_id') or movie.get('movieId')
                point_id = int(original_id) if isinstance(original_id, int) else (hash(str(original_id)) & ((1<<64)-1))

                batch_points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "movie_id": original_id,
                        "title": title,
                        "year": movie.get('year') or movie.get('release_year')
                    }
                ))

            # 2. Save to Graph Database
            # Use add_movie_data if available
            try:
                graphdb.add_movie_data(movie)
            except AttributeError:
                # fallback to older method name if present
                if hasattr(graphdb, 'add_book_data'):
                    graphdb.add_book_data(movie)

            # Insert Batch if full
            if len(batch_points) >= batch_size:
                vectordb.upsert_vectors(batch_points)
                batch_points = []

        except Exception as e:
            print(f"Error processing movie '{title}': {e}")

    # Insert remaining
    if batch_points:
        vectordb.upsert_vectors(batch_points)
        
    graphdb.close()
    print("DATA INGESTION COMPLETED!")

if __name__ == "__main__":
    run_ingestion()