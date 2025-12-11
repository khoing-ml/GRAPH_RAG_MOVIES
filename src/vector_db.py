from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter
from .config import Config

class QdrantService:
    def __init__(self):
        # Kết nối tới Qdrant
        self.client = QdrantClient(url=Config.QDRANT_URL)
        self.collection_name = "books_collection"
        self._create_collection_if_not_exists()

    def _create_collection_if_not_exists(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=Config.VECTOR_SIZE, distance=Distance.COSINE)
            )
            print(f"✅ Đã tạo collection '{self.collection_name}' trong Qdrant.")

    def upsert_vectors(self, points):
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, vector, top_k=3):
        try:
            # Cách 1: Dùng hàm search tiêu chuẩn
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=top_k
            )
        except AttributeError:
            # Cách 2: Fallback nếu thư viện phiên bản lạ (dùng query_points)
            # print("⚠️ Đang dùng fallback query_points...")
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=top_k
            ).points
            return results