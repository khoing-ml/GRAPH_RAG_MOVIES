from src.vector_db import QdrantService
from src.graph_db import Neo4jService

def check_health():
    print("="*40)
    print("🏥 KIỂM TRA SỨC KHỎE DỮ LIỆU")
    print("="*40)

    # 1. Kiểm tra Qdrant
    try:
        qdrant = QdrantService()
        info = qdrant.client.get_collection(qdrant.collection_name)
        count = info.points_count
        print(f"✅ Qdrant (Vector DB): Đang chứa {count} cuốn sách.")
    except Exception as e:
        print(f"❌ Qdrant: Lỗi kết nối ({e})")

    # 2. Kiểm tra Neo4j
    try:
        neo4j = Neo4jService()
        query = "MATCH (n:Book) RETURN count(n) as total"
        with neo4j.driver.session() as session:
            result = session.run(query).single()
            count = result["total"]
        print(f"✅ Neo4j (Graph DB):  Đang chứa {count} cuốn sách.")
        neo4j.close()
    except Exception as e:
        print(f"❌ Neo4j: Lỗi kết nối ({e})")
    
    print("="*40)

if __name__ == "__main__":
    check_health()