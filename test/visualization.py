"""
GraphRAG Query Processing Flow Visualization
"""

def print_flow_diagram():
    diagram = """
╔════════════════════════════════════════════════════════════════════════════╗
║                     GRAPHRAG QUERY PROCESSING FLOW                         ║
╚════════════════════════════════════════════════════════════════════════════╝

1️⃣  USER QUERY
    │
    │  "Phim hành động của đạo diễn Christopher Nolan năm 2010"
    │
    ▼

2️⃣  QUERY PROCESSOR (5 Techniques)
    │
    ├─────► [NER] Named Entity Recognition
    │         • "Christopher Nolan" [PERSON]
    │         • "2010" [YEAR]
    │         • "hành động" [GENRE_TYPE]
    │
    ├─────► [RE] Relational Extraction
    │         • DIRECTED_BY
    │         • BELONGS_TO
    │         • RELEASED_IN
    │
    ├─────► [QS] Query Structuration
    │         {
    │           nodes: [Person: "Christopher Nolan"],
    │           edges: [DIRECTED_BY],
    │           filters: {year: 2010}
    │         }
    │
    ├─────► [QD] Query Decomposition (if complex)
    │         • Find movies by Christopher Nolan
    │         • Filter action genre
    │         • Filter year 2010
    │
    └─────► [QE] Query Expansion
              + "action", "director", "film", "Nolan's work"
              + "thriller", "sci-fi", "cinema"
    │
    ▼

3️⃣  ENHANCED QUERY GENERATION
    │
    │  Original: "Phim hành động của đạo diễn Christopher Nolan năm 2010"
    │  Enhanced: "Phim hành động của đạo diễn Christopher Nolan năm 2010
    │             Christopher Nolan action director film 2010 thriller"
    │
    ▼

4️⃣  HYBRID RETRIEVAL
    │
    ├─────► [VECTOR SEARCH] Qdrant
    │         • Semantic similarity search
    │         • Using enhanced query
    │         • Top-K results: [id1, id2, id3, ...]
    │
    └─────► [GRAPH SEARCH] Neo4j
              • Relation-aware traversal
              • MATCH (p:Person {name: "Christopher Nolan"})-[:DIRECTED]->(m:Movie)
              • WHERE m.year = 2010
              • Rich context with director's other works, cast, genres
    │
    ▼

5️⃣  CONTEXT AGGREGATION
    │
    │  Vector Context + Graph Context → Rich Context
    │
    │  **Inception** (2010)
    │  Synopsis: A thief who steals corporate secrets...
    │  Director: Christopher Nolan
    │    → Director's other films: The Dark Knight, Interstellar, Dunkirk
    │  Cast: Leonardo DiCaprio, Marion Cotillard, Tom Hardy
    │    → Cast also in: The Revenant, The Dark Knight Rises
    │  Genres: Action, Sci-Fi, Thriller
    │    → Similar genre: The Matrix, Blade Runner 2049
    │
    ▼

6️⃣  LLM GENERATION (Gemini)
    │
    │  Context + Query → Natural Language Answer
    │
    ▼

7️⃣  FINAL ANSWER
    │
    └──► "Mình gợi ý **Inception** (2010) - một kiệt tác của Christopher Nolan.
          Đây là phim hành động khoa học viễn tưởng với nội dung độc đáo về 
          việc xâm nhập vào giấc mơ. Leonardo DiCaprio thể hiện xuất sắc vai 
          trùm trộm ý tưởng. Nếu bạn thích phong cách của Nolan, hãy xem thêm 
          The Dark Knight hoặc Interstellar..."

╔════════════════════════════════════════════════════════════════════════════╗
║                            KEY IMPROVEMENTS                                 ║
╠════════════════════════════════════════════════════════════════════════════╣
║ ✅ Understand query intent (entities + relations)                          ║
║ ✅ Expand query semantically (synonyms + related terms)                    ║
║ ✅ Structure query for graph traversal                                     ║
║ ✅ Relation-aware graph search (only fetch needed relations)               ║
║ ✅ Rich context with connected entities                                    ║
║ ✅ Multi-language support (Vietnamese + English)                           ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(diagram)

if __name__ == "__main__":
    print_flow_diagram()
