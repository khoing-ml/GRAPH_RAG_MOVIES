# -*- coding: utf-8 -*-
"""
Script crawl phim từ TMDB và lưu vào Qdrant + Neo4j Cloud
"""
import requests
import json
import time
import os
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from tqdm import tqdm

# ==========================================
# CẤU HÌNH
# ==========================================
TMDB_API_KEY = 'ba39c73252cd9fb0849949da47454e7d'
BASE_URL = 'https://api.themoviedb.org/3'

# Qdrant Cloud
QDRANT_URL = "https://9a823e32-f097-4096-87a0-23f05baaf13a.europe-west3-0.gcp.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.yZ1QMZ7exqzs_wswtYsqtwaGpu2ExXfhltpNwUq8Zp0"
COLLECTION_NAME = "movies_vietnamese"

# Neo4j AuraDB
NEO4J_URI = "neo4j+s://294ac027.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "HCF2K8_WnovcGqSKeNocCRi_7upAxqqeTAfTDMCSAjM"

# Settings
BATCH_SIZE = 10
MAX_PAGES = 10
PROCESSED_FILE = 'processed_movie_ids.log'

# ==========================================
# KHỞI TẠO
# ==========================================
print("⏳ Đang khởi tạo kết nối...")

q_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

if not q_client.collection_exists(COLLECTION_NAME):
    q_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print(f"✅ Đã tạo collection '{COLLECTION_NAME}'")

n_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ==========================================
# HÀM XỬ LÝ
# ==========================================

def get_existing_ids(filename):
    """Đọc danh sách ID đã xử lý"""
    if not os.path.exists(filename): 
        return set()
    with open(filename, 'r') as f: 
        return {int(line.strip()) for line in f if line.strip()}

def get_movie_details(movie_id):
    """Lấy thông tin chi tiết phim từ TMDB"""
    try:
        # Lấy thông tin phim
        url_det = f"{BASE_URL}/movie/{movie_id}"
        resp_det = requests.get(url_det, params={
            'api_key': TMDB_API_KEY, 
            'language': 'vi-VN'
        })
        if resp_det.status_code != 200: 
            return None
        data = resp_det.json()

        # Lấy credits (cast & crew)
        url_cred = f"{BASE_URL}/movie/{movie_id}/credits"
        resp_cred = requests.get(url_cred, params={'api_key': TMDB_API_KEY})
        credits = resp_cred.json() if resp_cred.status_code == 200 else {}
        
        # Xử lý dữ liệu
        director = next((x['name'] for x in credits.get('crew', []) if x['job'] == 'Director'), None)
        cast = [x['name'] for x in credits.get('cast', [])[:4]]
        genres = [x['name'] for x in data.get('genres', [])]
        
        overview = data.get('overview', '')
        title = data.get('title', '')
        
        # Text để tạo embedding
        text_embed = f"Phim: {title}. Thể loại: {', '.join(genres)}. Nội dung: {overview}"

        return {
            'tmdb_id': movie_id,
            'title': title,
            'original_title': data.get('original_title'),
            'year': data.get('release_date', '')[:4] if data.get('release_date') else 'Unknown',
            'rating': data.get('vote_average', 0),
            'overview': overview,
            'genres': genres,
            'director': director,
            'cast': cast,
            'poster': data.get('poster_path'),
            'text_embed': text_embed
        }
    except Exception as e:
        print(f"⚠️ Lỗi crawl ID {movie_id}: {e}")
        return None

def push_to_qdrant(batch_data: List[Dict]):
    """Upload vectors lên Qdrant Cloud"""
    if not batch_data: 
        return
    
    texts = [item['text_embed'] for item in batch_data]
    vectors = embed_model.encode(texts, show_progress_bar=False)
    
    points = []
    for i, item in enumerate(batch_data):
        payload = {k: v for k, v in item.items() if k != 'text_embed'}
        
        points.append(PointStruct(
            id=item['tmdb_id'],
            vector=vectors[i].tolist(),
            payload=payload
        ))
    
    q_client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"   ✅ [Qdrant] Đã lưu {len(points)} vectors.")

def push_to_neo4j(batch_data: List[Dict]):
    """Upload graph lên Neo4j AuraDB"""
    if not batch_data: 
        return

    cypher_query = """
    UNWIND $batch AS row
    
    // Tạo node Movie
    MERGE (m:Movie {id: row.tmdb_id})
    SET m.title = row.title,
        m.original_title = row.original_title,
        m.rating = row.rating,
        m.year = row.year,
        m.overview = row.overview

    // Tạo node Genre và quan hệ
    FOREACH (g_name IN row.genres | 
        MERGE (g:Genre {name: g_name})
        MERGE (m)-[:BELONGS_TO]->(g)
    )

    // Tạo node Actor và quan hệ
    FOREACH (actor_name IN row.cast | 
        MERGE (p:Person {name: actor_name})
        MERGE (p)-[:ACTED_IN]->(m)
    )

    // Tạo node Director và quan hệ
    FOREACH (dir_name IN CASE WHEN row.director IS NOT NULL THEN [row.director] ELSE [] END | 
        MERGE (d:Person {name: dir_name})
        MERGE (d)-[:DIRECTED]->(m)
    )
    """
    
    try:
        with n_driver.session() as session:
            session.run(cypher_query, batch=batch_data)
        print(f"   🕸️  [Neo4j] Đã cập nhật graph cho {len(batch_data)} phim.")
    except Exception as e:
        print(f"   ❌ [Neo4j Error] {e}")

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    processed = get_existing_ids(PROCESSED_FILE)
    print(f"📊 Đã crawl trước đó: {len(processed)} phim.\n")
    
    batch_buffer = []
    page = 1
    total_added = 0
    
    try:
        while page <= MAX_PAGES:
            print(f"📄 Đang quét trang {page}/{MAX_PAGES}...")
            
            try:
                url = f"{BASE_URL}/discover/movie"
                resp = requests.get(url, params={
                    'api_key': TMDB_API_KEY, 
                    'language': 'vi-VN', 
                    'sort_by': 'popularity.desc', 
                    'page': page
                })
                results = resp.json().get('results', [])
                
                if not results: 
                    break

                for item in results:
                    mid = item['id']
                    if mid in processed: 
                        continue
                    
                    # Lấy chi tiết
                    details = get_movie_details(mid)
                    if details:
                        batch_buffer.append(details)
                        processed.add(mid)
                        total_added += 1
                        
                        with open(PROCESSED_FILE, 'a') as f: 
                            f.write(f"{mid}\n")
                    
                    # Upload batch khi đủ
                    if len(batch_buffer) >= BATCH_SIZE:
                        print(f"   ⚡ Đang xử lý batch {len(batch_buffer)} phim...")
                        push_to_qdrant(batch_buffer)
                        push_to_neo4j(batch_buffer)
                        batch_buffer = []
                        
                    time.sleep(0.1)
                
                page += 1
                
            except Exception as e:
                print(f"❌ Lỗi trang {page}: {e}")
                break

        # Xử lý batch cuối
        if batch_buffer:
            print(f"⚡ Xử lý batch cuối cùng ({len(batch_buffer)} phim)...")
            push_to_qdrant(batch_buffer)
            push_to_neo4j(batch_buffer)

    except KeyboardInterrupt:
        print("\n⚠️ Đã dừng bởi người dùng.")
    finally:
        n_driver.close()
        print(f"\n🎉 HOÀN TẤT! Đã thêm {total_added} phim mới.")
