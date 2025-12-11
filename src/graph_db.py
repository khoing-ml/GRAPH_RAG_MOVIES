from neo4j import GraphDatabase
from .config import Config

class Neo4jService:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI, 
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def add_book_data(self, book):
        # Query tạo nút Sách, Tác giả, Thể loại và nối chúng lại
        query = """
        MERGE (b:Book {id: $id})
        SET b.title = $title, 
            b.language = $language, 
            b.year = $year,
            b.summary = $summary
        
        MERGE (a:Author {name: $author})
        MERGE (g:Genre {name: $genre})
        
        MERGE (b)-[:WROTE_BY]->(a)
        MERGE (b)-[:BELONGS_TO]->(g)
        """
        
        # Xử lý năm xuất bản (lấy 4 số đầu)
        year_str = book.get("published_date", "")
        year = year_str[:4] if year_str and len(year_str) >= 4 else "Unknown"

        with self.driver.session() as session:
            session.run(query, 
                        id=book["id"], 
                        title=book["title"], 
                        author=book["author"], 
                        genre=book["genre"],
                        language=book.get("language", "en"),
                        summary=book.get("summary", "")[:200] + "...", # Chỉ lưu đoạn ngắn vào Graph để tham khảo
                        year=year
            )

    def get_graph_context(self, book_ids):
        # Query lấy thông tin sách và mở rộng (expansion) sang sách cùng tác giả
        query = """
        MATCH (b:Book) WHERE b.id IN $book_ids
        MATCH (b)-[:WROTE_BY]->(a:Author)
        MATCH (b)-[:BELONGS_TO]->(g:Genre)
        
        // Tìm sách khác của cùng tác giả (giới hạn 3 cuốn để không bị quá tải context)
        OPTIONAL MATCH (a)<-[:WROTE_BY]-(other:Book) 
        WHERE other.id <> b.id
        
        RETURN b.title as Title, 
               b.language as Lang,
               b.year as Year,
               a.name as Author, 
               g.name as Genre, 
               collect(other.title)[..3] as OtherBooks
        """
        results = []
        with self.driver.session() as session:
            data = session.run(query, book_ids=book_ids)
            for record in data:
                lang_display = "Vietnamese" if record['Lang'] == 'vi' else "English"
                
                info = f"- Book: '{record['Title']}' ({record['Year']}, {lang_display})\n" \
                       f"  Author: {record['Author']} | Genre: {record['Genre']}"
                
                others = record['OtherBooks']
                if others:
                    info += f"\n  -> Author also wrote: {', '.join(others)}."
                
                results.append(info)
        
        return "\n\n".join(results)