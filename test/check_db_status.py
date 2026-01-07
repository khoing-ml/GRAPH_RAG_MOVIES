from src.vector_db import QdrantService
from src.graph_db import Neo4jService
from src.config import Config

def check_health():
    print("="*60)
    print("KIỂM TRA KẾT NỐI DATABASE CLOUD")
    print("="*60)

    # Hiển thị cấu hình hiện tại
    print("\nCấu hình:")
    print(f"  Neo4j URI: {Config.NEO4J_URI}")
    print(f"  Neo4j User: {Config.NEO4J_USER}")
    print(f"  Qdrant URL: {Config.QDRANT_URL}")
    print(f"  Qdrant API Key: {'✅ Đã cấu hình' if Config.QDRANT_API_KEY else '❌ Chưa cấu hình'}")
    print()

    # 1. Kiểm tra Qdrant Cloud
    print("1️Kiểm tra Qdrant Cloud...")
    try:
        if "<waiting-for-cluster-host>" in Config.QDRANT_URL:
            print(f"   QDRANT: URL chưa được cấu hình đúng!")
            print(f"   Vui lòng cập nhật QDRANT_URL trong file .env")
            print(f"   Ví dụ: https://your-cluster-id.qdrant.io:6333")
        else:
            qdrant = QdrantService()
            collections = qdrant.client.get_collections().collections
            print(f"   Kết nối thành công đến Qdrant Cloud!")
            print(f"   ất cả Collections:")
            
            # Kiểm tra từng collection
            for c in collections:
                info = qdrant.client.get_collection(c.name)
                count = info.points_count
                status = "1" if count > 0 else "0"
                print(f"      {status} '{c.name}': {count} documents")
            
    except Exception as e:
        print(f"   Qdrant: Lỗi kết nối")
        print(f"   Chi tiết: {str(e)}")

    # 2. Kiểm tra Neo4j Cloud (AuraDB)
    print("\n2️ Kiểm tra Neo4j AuraDB...")
    try:
        neo4j = Neo4jService()
        
        # Kiểm tra kết nối
        with neo4j.driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        print(f"   Kết nối thành công đến Neo4j AuraDB!")
        
            # Đếm tất cả các loại nodes
        with neo4j.driver.session() as session:
            # legacy Book nodes (if any)
            book_count = session.run("MATCH (n:Book) RETURN count(n) as total").single()["total"]
            author_count = session.run("MATCH (n:Author) RETURN count(n) as total").single()["total"]
            
            # Movies and people
            movie_count = session.run("MATCH (n:Movie) RETURN count(n) as total").single()["total"]
            person_count = session.run("MATCH (n:Person) RETURN count(n) as total").single()["total"]
            
            # Common
            genre_count = session.run("MATCH (n:Genre) RETURN count(n) as total").single()["total"]
        
        print(f"   LEGACY BOOKS (if any):")
        print(f"      Books: {book_count}, Authors: {author_count}")
        print(f"   MOVIES:")
        print(f"      Movies: {movie_count}, People (Cast/Directors): {person_count}")
        print(f"   SHARED:")
        print(f"      Genres: {genre_count}")
        
        total_data = movie_count + book_count
        if total_data == 0:
            print(f"   Database trống - cần nạp dữ liệu")
        else:
            print(f"   Tổng: {total_data} items")
            
        neo4j.close()
    except Exception as e:
        print(f"   Neo4j: Lỗi kết nối")
        print(f"   Chi tiết: {str(e)}")
        if "authentication" in str(e).lower():
            print(f"   Kiểm tra NEO4J_USER và NEO4J_PASSWORD trong .env")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    check_health()