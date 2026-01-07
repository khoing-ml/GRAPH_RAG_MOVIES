from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter
from .config import Config

class QdrantService:
    def __init__(self):
        # Connect to Qdrant (Cloud or Local)
        if Config.QDRANT_API_KEY:
            # Cloud configuration with API key
            self.client = QdrantClient(
                url=Config.QDRANT_URL,
                api_key=Config.QDRANT_API_KEY
            )
        else:
            # Local configuration without API key
            self.client = QdrantClient(url=Config.QDRANT_URL)
        self.collection_name = Config.QDRANT_COLLECTION
        self._create_collection_if_not_exists()

    def _create_collection_if_not_exists(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=Config.VECTOR_SIZE, distance=Distance.COSINE)
            )
            print(f"✅ Created collection '{self.collection_name}' in Qdrant.")

    def upsert_vectors(self, points):
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, vector, top_k=3):
        try:
            # Method 1: Use standard search function
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=top_k
            )
        except AttributeError:
            # Method 2: Fallback for unusual library versions (use query_points)
            # print("⚠️ Using fallback query_points...")
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=top_k
            ).points
            return results