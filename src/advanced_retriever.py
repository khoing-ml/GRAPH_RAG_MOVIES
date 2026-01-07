"""
Advanced Retriever for GraphRAG
Implements techniques from GraphRAG survey paper:
- Entity Linking
- Hybrid Retrieval (Neural + Symbolic)
- Iterative Retrieval (Multi-hop)
- Adaptive Retrieval (Smart depth selection)
"""

from typing import List, Dict, Any, Tuple, Set
import re
from .llm_service import GeminiService
from .vector_db import QdrantService
from .graph_db import Neo4jService


class EntityLinker:
    """Entity Linking: Map query entities to graph nodes"""
    
    def __init__(self, llm_service: GeminiService, graphdb: Neo4jService):
        self.llm = llm_service
        self.graphdb = graphdb
    
    def extract_entities(self, query: str) -> List[Dict]:
        """Extract entities from query using LLM"""
        prompt = f"""Extract movie-related entities from this query:
Query: "{query}"

Identify:
1. Movie titles (exact or partial names)
2. Person names (actors, directors)
3. Genres
4. Other movie-related entities

Return as JSON list: [{{"entity": "name", "type": "movie|person|genre|other"}}]
If no entities found, return empty list []

Examples:
Query: "Christopher Nolan đạo diễn phim nào?"
[{{"entity": "Christopher Nolan", "type": "person"}}]

Query: "Phim kinh dị hay?"
[{{"entity": "kinh dị", "type": "genre"}}]

Query: "Phim giống The Shawshank Redemption"
[{{"entity": "The Shawshank Redemption", "type": "movie"}}]

Now extract from: "{query}"
Return ONLY valid JSON array."""

        try:
            # Get safety settings from model if available
            safety_settings = getattr(self.llm.model, '_safety_settings', None)
            response = self.llm.model.generate_content(prompt, safety_settings=safety_settings)
            
            # Check for valid response
            try:
                entities_text = response.text.strip()
            except ValueError as e:
                # Handle blocked content
                print(f"    ⚠️ Response blocked (safety/recitation): {str(e)[:100]}")
                return self._fallback_extraction(query)
            
            # Parse JSON
            import json
            entities = json.loads(entities_text)
            return entities if isinstance(entities, list) else []
        except Exception as e:
            print(f"    ⚠️ Entity extraction error: {e}")
            # Fallback: simple regex-based extraction
            return self._fallback_extraction(query)
    
    def _fallback_extraction(self, query: str) -> List[Dict]:
        """Fallback entity extraction using patterns"""
        entities = []
        
        # Common Vietnamese genre keywords
        genres = ['hành động', 'kinh dị', 'tình cảm', 'hài', 'tâm lý', 
                  'khoa học', 'phiêu lưu', 'kịch', 'anime', 'hoạt hình']
        
        for genre in genres:
            if genre in query.lower():
                entities.append({"entity": genre, "type": "genre"})
        
        # Capitalized words might be names/titles
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        for word in words:
            if len(word) > 3:
                entities.append({"entity": word, "type": "unknown"})
        
        return entities
    
    def link_to_graph(self, entities: List[Dict]) -> List[Dict]:
        """Link extracted entities to graph nodes"""
        linked_nodes = []
        
        for entity in entities:
            entity_name = entity['entity']
            entity_type = entity['type']
            
            # Search in graph based on type
            if entity_type == 'movie':
                query = """
                MATCH (m:Movie)
                WHERE toLower(m.title) CONTAINS toLower($name)
                RETURN m.title as title, m.id as id, 'movie' as type
                LIMIT 3
                """
            elif entity_type == 'person':
                query = """
                MATCH (p:Person)
                WHERE toLower(p.name) CONTAINS toLower($name)
                RETURN p.name as name, p.name as id, 'person' as type
                LIMIT 3
                """
            elif entity_type == 'genre':
                query = """
                MATCH (g:Genre)
                WHERE toLower(g.name) CONTAINS toLower($name)
                RETURN g.name as name, g.name as id, 'genre' as type
                LIMIT 3
                """
            else:
                # Try all types
                query = """
                MATCH (n)
                WHERE (n:Movie AND toLower(n.title) CONTAINS toLower($name))
                   OR (n:Person AND toLower(n.name) CONTAINS toLower($name))
                   OR (n:Genre AND toLower(n.name) CONTAINS toLower($name))
                RETURN labels(n)[0] as type, 
                       COALESCE(n.title, n.name) as name,
                       COALESCE(n.id, n.name) as id
                LIMIT 3
                """
            
            try:
                with self.graphdb.driver.session() as session:
                    results = session.run(query, name=entity_name)
                    for record in results:
                        linked_nodes.append({
                            'entity': entity_name,
                            'matched_node': dict(record),
                            'original_type': entity_type
                        })
            except Exception as e:
                print(f"    ⚠️ Entity linking error for '{entity_name}': {e}")
        
        return linked_nodes


class GraphTraverser:
    """Graph Traversal: Expand context through graph relationships"""
    
    def __init__(self, graphdb: Neo4jService):
        self.graphdb = graphdb
    
    def traverse_k_hop(self, node_ids: List[str], k: int = 2, 
                       max_nodes: int = 20) -> List[Dict]:
        """
        K-hop neighborhood traversal
        Returns nodes and relationships within k hops
        """
        if not node_ids or k <= 0:
            return []
        
        query = f"""
        MATCH path = (start)-[*1..{k}]-(neighbor)
        WHERE start.id IN $node_ids OR start.name IN $node_ids
        WITH DISTINCT neighbor, length(path) as distance
        ORDER BY distance ASC
        LIMIT {max_nodes}
        RETURN 
            labels(neighbor)[0] as type,
            COALESCE(neighbor.title, neighbor.name) as name,
            COALESCE(neighbor.id, neighbor.name) as id,
            distance
        """
        
        try:
            with self.graphdb.driver.session() as session:
                results = session.run(query, node_ids=node_ids)
                return [dict(record) for record in results]
        except Exception as e:
            print(f"    ⚠️ Graph traversal error: {e}")
            return []
    
    def get_relationships_between(self, node_ids: List[str]) -> List[Dict]:
        """Get all relationships between a set of nodes"""
        if len(node_ids) < 2:
            return []
        
        query = """
        MATCH (n1)-[r]->(n2)
        WHERE (n1.id IN $node_ids OR n1.name IN $node_ids) 
          AND (n2.id IN $node_ids OR n2.name IN $node_ids)
        RETURN 
            type(r) as relationship,
            COALESCE(n1.title, n1.name) as source,
            COALESCE(n2.title, n2.name) as target
        LIMIT 50
        """
        
        try:
            with self.graphdb.driver.session() as session:
                results = session.run(query, node_ids=node_ids)
                return [dict(record) for record in results]
        except Exception as e:
            print(f"    ⚠️ Relationship retrieval error: {e}")
            return []
    
    def find_paths_between(self, start_id: str, end_id: str, 
                           max_length: int = 4) -> List[List[Dict]]:
        """Find paths between two entities"""
        query = f"""
        MATCH path)-[*1..{max_length}]-(end)
        )
        WHERE (start.id = $start_id OR start.name = $start_id)
          AND (end.id = $end_id OR end.name = $end_id)
        RETURN [node in nodes(path) | 
                {{type: labels(node)[0], 
                  name: COALESCE(node.title, node.name),
                  id: COALESCE(node.id, node.name)ode.title, node.name),
                  id: node.tmdb_id}}] as path_nodes,
               [rel in relationships(path) | type(rel)] as path_rels
        LIMIT 3
        """
        
        try:
            with self.graphdb.driver.session() as session:
                results = session.run(query, start_id=start_id, end_id=end_id)
                return [dict(record) for record in results]
        except Exception as e:
            print(f"    ⚠️ Path finding error: {e}")
            return []


class AdaptiveRetriever:
    """Adaptive Retrieval: Intelligently decide retrieval depth"""
    
    def __init__(self, llm_service: GeminiService):
        self.llm = llm_service
    
    def predict_retrieval_depth(self, query: str, query_metadata: Dict) -> int:
        """
        Predict how many hops of graph traversal needed
        Based on query complexity and type
        """
        # Rule-based heuristics
        query_lower = query.lower()
        
        # Simple factual queries: 1 hop
        simple_patterns = ['là gì', 'tên', 'năm nào', 'ai đạo diễn', 'do ai']
        if any(pattern in query_lower for pattern in simple_patterns):
            return 1
        
        # Recommendation/similarity: 2 hops
        rec_patterns = ['giống', 'tương tự', 'hay', 'nên xem', 'đề xuất']
        if any(pattern in query_lower for pattern in rec_patterns):
            return 2
        
        # Complex reasoning: 3 hops
        complex_patterns = ['mối quan hệ', 'cùng làm việc', 'hợp tác', 
                           'so sánh', 'khác nhau']
        if any(pattern in query_lower for pattern in complex_patterns):
            return 3
        
        # Check query category from metadata
        category = query_metadata.get('category', 'unknown')
        depth_map = {
            'specific_film_info': 1,
            'genre_recommendation': 2,
            'similarity_search': 2,
            'director_filmography': 2,
            'actor_filmography': 2,
            'disambiguation': 2,
            'comparison': 3
        }
        
        return depth_map.get(category, 2)  # Default: 2 hops
    
    def should_retrieve(self, query: str, internal_confidence: float = 0.5) -> bool:
        """
        Decide if external retrieval is needed
        If LLM already knows the answer with high confidence, skip retrieval
        """
        # For now, always retrieve for movie domain
        # Can be enhanced with confidence scoring
        return True


class HybridRetriever:
    """
    Hybrid Retrieval: Combines Neural (Vector) + Symbolic (Graph)
    Main orchestrator for advanced retrieval
    """
    
    def __init__(self, llm: GeminiService, vectordb: QdrantService, 
                 graphdb: Neo4jService):
        self.llm = llm
        self.vectordb = vectordb
        self.graphdb = graphdb
        
        # Sub-components
        self.entity_linker = EntityLinker(llm, graphdb)
        self.graph_traverser = GraphTraverser(graphdb)
        self.adaptive_retriever = AdaptiveRetriever(llm)
    
    def retrieve(self, query: str, query_metadata: Dict = None, 
                 top_k_vector: int = 5) -> Dict:
        """
        Main retrieval pipeline combining multiple strategies
        
        Steps:
        1. Adaptive decision: Should retrieve? What depth?
        2. Neural retrieval: Vector search for semantic similarity
        3. Symbolic retrieval: Entity linking + graph traversal
        4. Hybrid fusion: Combine results
        """
        if query_metadata is None:
            query_metadata = {}
        
        print(f"\n  🔍 Advanced Hybrid Retrieval")
        
        # Step 1: Adaptive decision
        should_retrieve = self.adaptive_retriever.should_retrieve(query)
        if not should_retrieve:
            print(f"    → Skipping retrieval (high internal confidence)")
            return {'contexts': [], 'method': 'internal_knowledge'}
        
        retrieval_depth = self.adaptive_retriever.predict_retrieval_depth(
            query, query_metadata
        )
        print(f"    → Predicted depth: {retrieval_depth} hops")
        
        # Step 2: Neural retrieval (Vector search)
        print(f"    → Neural retrieval (vector search)...")
        query_embedding = self.llm.get_embedding(query, task_type="retrieval_query")
        vector_results = []
        
        if query_embedding:
            search_results = self.vectordb.search(query_embedding, top_k=top_k_vector)
            for item in search_results:
                if hasattr(item, 'payload') and item.payload:
                    vector_results.append({
                        'title': item.payload.get('title', ''),
                        'overview': item.payload.get('overview', ''),
                        'tmdb_id': item.payload.get('tmdb_id', ''),
                        'score': item.score if hasattr(item, 'score') else 0,
                        'source': 'vector'
                    })
        
        print(f"    → Found {len(vector_results)} vector results")
        
        # Step 3: Symbolic retrieval (Entity linking + Graph traversal)
        print(f"    → Symbolic retrieval (entity linking + traversal)...")
        
        # 3a. Entity linking
        entities = self.entity_linker.extract_entities(query)
        print(f"    → Extracted {len(entities)} entities: {[e['entity'] for e in entities]}")
        
        linked_nodes = self.entity_linker.link_to_graph(entities)
        print(f"    → Linked to {len(linked_nodes)} graph nodes")
        
        graph_results = []
        
        # 3b. Graph traversal
        if linked_nodes:
            # Get node IDs for traversal
            start_node_ids = [
                node['matched_node'].get('id')
                for node in linked_nodes
                if 'matched_node' in node and node['matched_node'].get('id')
            ]
            
            if start_node_ids:
                # K-hop traversal
                neighbors = self.graph_traverser.traverse_k_hop(
                    start_node_ids, 
                    k=retrieval_depth,
                    max_nodes=15
                )
                
                for neighbor in neighbors:
                    graph_results.append({
                        'name': neighbor.get('name', ''),
                        'type': neighbor.get('type', ''),
                        'id': neighbor.get('id', ''),
                        'distance': neighbor.get('distance', 0),
                        'source': 'graph'
                    })
                
                print(f"    → Found {len(graph_results)} graph neighbors")
                
                # Get relationships for context
                all_node_ids = start_node_ids + [n.get('id') for n in neighbors]
                relationships = self.graph_traverser.get_relationships_between(all_node_ids)
                print(f"    → Found {len(relationships)} relationships")
        
        # Step 4: Hybrid fusion - Combine and format results
        combined_contexts = self._fuse_results(
            vector_results, 
            graph_results,
            linked_nodes
        )
        
        print(f"    ✓ Total contexts: {len(combined_contexts)}")
        
        return {
            'contexts': combined_contexts,
            'vector_count': len(vector_results),
            'graph_count': len(graph_results),
            'linked_entities': len(linked_nodes),
            'retrieval_depth': retrieval_depth,
            'method': 'hybrid'
        }
    
    def _fuse_results(self, vector_results: List[Dict], 
                     graph_results: List[Dict],
                     linked_entities: List[Dict]) -> List[str]:
        """Fuse vector and graph results into unified context"""
        contexts = []
        
        # Add vector results (semantic matches)
        for result in vector_results[:5]:  # Top 5
            ctx = f"[Vector Match] {result['title']}"
            if result.get('overview'):
                ctx += f": {result['overview'][:200]}"
            contexts.append(ctx)
        
        # Add linked entities info
        for entity in linked_entities[:3]:  # Top 3
            matched = entity.get('matched_node', {})
            if matched:
                ctx = f"[Entity Linked] {matched.get('name', '')}"
                contexts.append(ctx)
        
        # Add graph neighbors
        for result in graph_results[:5]:  # Top 5
            ctx = f"[Graph {result['distance']}-hop] {result['type']}: {result['name']}"
            contexts.append(ctx)
        
        return contexts


def create_advanced_retriever(llm, vectordb, graphdb) -> HybridRetriever:
    """Factory function to create advanced retriever"""
    return HybridRetriever(llm, vectordb, graphdb)
