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

    def add_movie_data(self, movie):
        # Create Movie node, Person nodes (director/actors) and Genre relationships
        query = """
        MERGE (m:Movie {id: $id})
        SET m.title = $title,
            m.year = $year,
            m.overview = $overview

        // Genres
        WITH m
        UNWIND $genres AS g_name
        MERGE (g:Genre {name: g_name})
        MERGE (m)-[:BELONGS_TO]->(g)

        // Cast
        WITH m
        UNWIND $cast AS actor_name
        MERGE (p:Person {name: actor_name})
        MERGE (p)-[:ACTED_IN]->(m)

        // Director
        WITH m
        WITH m, $director AS director_name
        CALL {
            WITH director_name, m
            WHERE director_name IS NOT NULL
            MERGE (d:Person {name: director_name})
            MERGE (d)-[:DIRECTED]->(m)
            RETURN d
        }
        RETURN m
        """

        year_str = movie.get("release_date", "")
        year = year_str[:4] if year_str and len(year_str) >= 4 else movie.get('year', 'Unknown')

        with self.driver.session() as session:
            session.run(query,
                        id=movie.get("tmdb_id") or movie.get("id"),
                        title=movie.get("title", "Untitled"),
                        year=year,
                        overview=movie.get("overview", ""),
                        genres=movie.get("genres", []),
                        cast=movie.get("cast", []),
                        director=movie.get("director")
            )

    def get_graph_context(self, movie_ids):
        # Query movie nodes and expand context via director/actors and similar movies
        query = """
        MATCH (m:Movie) WHERE m.id IN $movie_ids
        OPTIONAL MATCH (m)-[:BELONGS_TO]->(g:Genre)
        OPTIONAL MATCH (d:Person)-[:DIRECTED]->(m)
        OPTIONAL MATCH (p:Person)-[:ACTED_IN]->(m)

        // find other movies by same director (limit 3)
        OPTIONAL MATCH (d)-[:DIRECTED]->(other:Movie)
        WHERE other.id <> m.id

        RETURN m.title as Title,
               m.year as Year,
               d.name as Director,
               collect(DISTINCT g.name) as Genres,
               collect(DISTINCT p.name)[..6] as Cast,
               collect(DISTINCT other.title)[..3] as OtherMovies
        """

        results = []
        with self.driver.session() as session:
            data = session.run(query, movie_ids=movie_ids)
            for record in data:
                info = f"- Movie: '{record['Title']}' ({record['Year']})\n"
                if record['Director']:
                    info += f"  Director: {record['Director']}\n"
                if record['Genres']:
                    info += f"  Genres: {', '.join(record['Genres'])}\n"
                if record['Cast']:
                    info += f"  Cast: {', '.join(record['Cast'])}\n"
                others = record['OtherMovies']
                if others:
                    info += f"  -> Director also made: {', '.join(others)}.\n"
                results.append(info)

        return "\n\n".join(results)