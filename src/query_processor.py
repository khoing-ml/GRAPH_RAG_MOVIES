"""
Query Processor for GraphRAG
Implements 5 key techniques from GraphRAG research:
1. Named Entity Recognition (NER) - Extract entities like movie titles, actors, directors
2. Relational Extraction (RE) - Identify relations like "directed by", "acted in"
3. Query Structuration - Convert natural language to structured formats
4. Query Decomposition - Break complex queries into sub-queries
5. Query Expansion - Enrich queries with related terms and entities

Enhanced with:
- Query validation and cleaning
- Result caching for faster repeated queries
- Confidence scoring and quality metrics
- Query rewriting and optimization
- Comprehensive error handling
"""

import re
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from functools import lru_cache
from .llm_service import GeminiService


class QueryProcessor:
    """
    Advanced query processing for GraphRAG system.
    Bridges text-formatted queries with graph-structured data.
    """
    
    def __init__(self, llm_service: GeminiService = None):
        self.llm = llm_service or GeminiService()
        
        # Query cache for faster repeated queries
        self._query_cache = {}
        self._cache_max_size = 100
        
        # Statistics tracking
        self.stats = {
            'queries_processed': 0,
            'cache_hits': 0,
            'entities_found': 0,
            'relations_found': 0
        }
        
        # Define entity patterns and types
        self.entity_types = {
            'MOVIE': ['phim', 'movie', 'film', 'bộ phim', 'tác phẩm'],
            'PERSON': ['đạo diễn', 'diễn viên', 'director', 'actor', 'người'],
            'GENRE': ['thể loại', 'genre', 'hành động', 'tình cảm', 'kinh dị', 'hài', 'viễn tưởng']
        }
        
        # Define relation patterns (Vietnamese and English)
        self.relation_patterns = {
            'DIRECTED_BY': [
                r'(đạo diễn|directed by|của đạo diễn|do .+ đạo diễn)',
                r'(phim của|movies? by|films? by)'
            ],
            'ACTED_IN': [
                r'(diễn viên|actor|actress|có .+ đóng|starring)',
                r'(vai diễn|role|performance|tham gia)'
            ],
            'BELONGS_TO': [
                r'(thể loại|genre|thuộc thể loại|là phim)',
                r'(action|drama|comedy|horror|sci-?fi)'
            ],
            'SIMILAR_TO': [
                r'(giống|tương tự|như|like|similar)',
                r'(phong cách|style|kiểu)'
            ],
            'RELEASED_IN': [
                r'(\d{4}|năm \d{4}|released in|ra mắt)',
            ]
        }

    def process_query(self, query: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Main processing pipeline that applies all 5 techniques with enhancements.
        
        Args:
            query: User's natural language question
            use_cache: Whether to use cached results for repeated queries
            
        Returns:
            Dict containing:
            - entities: List of recognized entities with types
            - relations: List of identified relations
            - structured_query: Cypher-like structured format
            - sub_queries: Decomposed sub-queries if complex
            - expanded_terms: Additional search terms from expansion
            - original_query: The original query
            - cleaned_query: Preprocessed query
            - confidence: Overall confidence score (0-1)
            - processing_time: Time taken in milliseconds
            - cached: Whether result was from cache
        """
        import time
        start_time = time.time()
        
        # Update statistics
        self.stats['queries_processed'] += 1
        
        # Validate and clean query
        if not self._validate_query(query):
            print(f"⚠️ Invalid query: '{query}'")
            return self._empty_result(query, "Invalid query")
        
        cleaned_query = self._clean_query(query)
        print(f"\n🔧 Query Processor: '{cleaned_query}'...")
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(cleaned_query)
            if cache_key in self._query_cache:
                self.stats['cache_hits'] += 1
                cached_result = self._query_cache[cache_key].copy()
                cached_result['cached'] = True
                cached_result['processing_time'] = (time.time() - start_time) * 1000
                print(f"  💾 Retrieved from cache (hit rate: {self.stats['cache_hits']}/{self.stats['queries_processed']})")
                return cached_result
        
        result = {
            'original_query': query,
            'cleaned_query': cleaned_query,
            'entities': [],
            'relations': [],
            'structured_query': {},
            'sub_queries': [],
            'expanded_terms': [],
            'confidence': 0.0,
            'processing_time': 0.0,
            'cached': False,
            'rewritten_query': None
        }
        
        try:
            # 1. Named Entity Recognition
            result['entities'] = self._extract_entities(cleaned_query)
            self.stats['entities_found'] += len(result['entities'])
            
            # 2. Relational Extraction
            result['relations'] = self._extract_relations(cleaned_query)
            self.stats['relations_found'] += len(result['relations'])
            
            # 3. Query Structuration
            result['structured_query'] = self._structure_query(
                cleaned_query, result['entities'], result['relations']
            )
            
            # 4. Query Decomposition (if complex)
            if self._is_complex_query(cleaned_query):
                result['sub_queries'] = self._decompose_query(cleaned_query)
                print(f"  🔀 Complex query split into {len(result['sub_queries'])} sub-queries")
            
            # 5. Query Expansion
            result['expanded_terms'] = self._expand_query(cleaned_query, result['entities'])
            
            # 6. Query Rewriting (if needed)
            if self._needs_rewriting(result):
                result['rewritten_query'] = self._rewrite_query(cleaned_query, result)
                print(f"  ✏️ Query rewritten for better matching")
            
            # Calculate confidence score
            result['confidence'] = self._calculate_confidence(result)
            
            # Record processing time
            result['processing_time'] = (time.time() - start_time) * 1000
            
            # Cache result
            if use_cache:
                self._cache_result(cache_key, result)
            
            print(f"  ✅ Processed in {result['processing_time']:.1f}ms (confidence: {result['confidence']:.2f})\n")
            
        except Exception as e:
            print(f"  ❌ Processing error: {str(e)}")
            result['error'] = str(e)
            result['confidence'] = 0.0
        
        return result

    def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """
        Named Entity Recognition (NER)
        Identifies entities and their types (Movie, Person, Genre)
        """
        entities = []
        query_lower = query.lower()
        
        # Simple rule-based NER for common patterns
        # Extract movie titles (quoted or capitalized)
        movie_patterns = [
            r'"([^"]+)"',  # Quoted titles
            r'《([^》]+)》',  # Chinese quotes
            r'\b([A-Z][A-Za-z\s&:]+(?:\d+)?)\b'  # Capitalized titles
        ]
        
        for pattern in movie_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                if len(match) > 2 and match.lower() not in ['what', 'where', 'when', 'who', 'how', 'why']:
                    entities.append({
                        'text': match.strip(),
                        'type': 'MOVIE',
                        'confidence': 0.8
                    })
        
        # Extract years
        year_matches = re.findall(r'\b(19\d{2}|20\d{2})\b', query)
        for year in year_matches:
            entities.append({
                'text': year,
                'type': 'YEAR',
                'confidence': 1.0
            })
        
        # Identify entity type keywords
        for entity_type, keywords in self.entity_types.items():
            for keyword in keywords:
                if keyword in query_lower:
                    entities.append({
                        'text': keyword,
                        'type': f'{entity_type}_TYPE',
                        'confidence': 0.9
                    })
        
        # Use LLM for more sophisticated entity extraction
        if not entities or len(entities) < 2:
            llm_entities = self._llm_extract_entities(query)
            entities.extend(llm_entities)
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity['text'].lower(), entity['type'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        print(f"  ✓ Found {len(unique_entities)} entities: {[e['text'] for e in unique_entities[:5]]}")
        return unique_entities

    def _llm_extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """Use LLM to extract entities with semantic understanding"""
        prompt = f"""Extract all movie-related entities from this query. Return ONLY a comma-separated list.

Query: "{query}"

Extract:
- Movie titles (if mentioned)
- Person names (actors, directors)
- Genres
- Years

Format: EntityName|Type
Example: "Inception|MOVIE, Christopher Nolan|PERSON, 2010|YEAR, sci-fi|GENRE"

Output (comma-separated):"""
        
        try:
            # Get safety settings from model if available
            safety_settings = getattr(self.llm.model, '_safety_settings', None)
            response = self.llm.model.generate_content(prompt, safety_settings=safety_settings)
            
            try:
                text = response.text.strip()
            except ValueError as e:
                # Handle blocked content
                print(f"  ⚠️  Response blocked (safety): {str(e)[:80]}")
                return []
            
            entities = []
            for item in text.split(','):
                item = item.strip()
                if '|' in item:
                    name, etype = item.split('|', 1)
                    entities.append({
                        'text': name.strip(),
                        'type': etype.strip().upper(),
                        'confidence': 0.85
                    })
            return entities
        except Exception as e:
            print(f"  ⚠️ LLM entity extraction failed: {e}")
            return []

    def _extract_relations(self, query: str) -> List[Dict[str, Any]]:
        """
        Relational Extraction (RE)
        Identifies relations between entities in the query
        """
        relations = []
        query_lower = query.lower()
        
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    relations.append({
                        'type': relation_type,
                        'pattern': pattern,
                        'confidence': 0.85
                    })
                    break  # Only add once per relation type
        
        print(f"  ✓ Found {len(relations)} relations: {[r['type'] for r in relations]}")
        return relations

    def _structure_query(self, query: str, entities: List[Dict], relations: List[Dict]) -> Dict[str, Any]:
        """
        Query Structuration
        Converts natural language to structured format (similar to Cypher)
        """
        structured = {
            'operation': 'MATCH',
            'nodes': [],
            'edges': [],
            'filters': {},
            'return_fields': ['title', 'year', 'overview', 'director', 'cast', 'genres']
        }
        
        # Build nodes from entities
        for entity in entities:
            if entity['type'] in ['MOVIE', 'PERSON', 'GENRE']:
                structured['nodes'].append({
                    'label': entity['type'],
                    'name': entity['text']
                })
            elif entity['type'] == 'YEAR':
                structured['filters']['year'] = entity['text']
        
        # Build edges from relations
        for relation in relations:
            structured['edges'].append({
                'type': relation['type'],
                'direction': 'any'  # Can be 'in', 'out', or 'any'
            })
        
        return structured

    def _is_complex_query(self, query: str) -> bool:
        """
        Determine if query needs decomposition
        Complex queries have multiple conditions or questions
        """
        complexity_indicators = [
            'và', 'and', 'hoặc', 'or', 'nhưng', 'but',  # Conjunctions
            '?.*?',  # Multiple question marks
            'sau đó', 'then', 'tiếp theo', 'next',  # Sequential operations
            'so sánh', 'compare', 'khác nhau', 'difference'  # Comparison operations
        ]
        
        query_lower = query.lower()
        complexity_score = sum(1 for indicator in complexity_indicators if indicator in query_lower)
        
        return complexity_score >= 2 or len(query.split()) > 20

    def _decompose_query(self, query: str) -> List[str]:
        """
        Query Decomposition
        Breaks complex queries into simpler sub-queries
        """
        prompt = f"""Break down this complex movie query into 2-4 simpler sub-queries that can be answered independently.

Query: "{query}"

Return ONLY the sub-queries, one per line, numbered.
Example:
1. Find all sci-fi movies from 2010
2. Which of these were directed by Christopher Nolan
3. What are similar movies to these

Sub-queries:"""
        
        try:
            # Get safety settings from model if available
            safety_settings = getattr(self.llm.model, '_safety_settings', None)
            response = self.llm.model.generate_content(prompt, safety_settings=safety_settings)
            
            try:
                text = response.text.strip()
            except ValueError as e:
                # Handle blocked content
                print(f"  ⚠️  Query decomposition blocked (safety): {str(e)[:80]}")
                return [query]  # Return original query as fallback
            
            # Parse numbered list
            sub_queries = []
            for line in text.split('\n'):
                line = line.strip()
                # Remove numbering (1., 2., etc.)
                line = re.sub(r'^\d+[\.)]\s*', '', line)
                if line and len(line) > 10:
                    sub_queries.append(line)
            
            print(f"  ✓ Decomposed into {len(sub_queries)} sub-queries")
            return sub_queries[:4]  # Limit to 4 sub-queries
            
        except Exception as e:
            print(f"  ⚠️ Query decomposition failed: {e}")
            return [query]  # Return original if failed

    def _expand_query(self, query: str, entities: List[Dict]) -> List[str]:
        """
        Query Expansion
        Enriches query with synonyms, related terms, and context
        """
        expanded_terms = []
        
        # Add synonyms for Vietnamese terms
        expansion_map = {
            'phim': ['movie', 'film', 'bộ phim', 'tác phẩm'],
            'hay': ['tuyệt vời', 'xuất sắc', 'đỉnh cao', 'kiệt tác', 'great', 'excellent'],
            'hành động': ['action', 'fighting', 'chiến đấu'],
            'tình cảm': ['romance', 'love', 'lãng mạn'],
            'kinh dị': ['horror', 'scary', 'đáng sợ', 'thriller'],
            'hài': ['comedy', 'funny', 'vui nhộn'],
            'viễn tưởng': ['sci-fi', 'science fiction', 'khoa học'],
        }
        
        query_lower = query.lower()
        for term, expansions in expansion_map.items():
            if term in query_lower:
                expanded_terms.extend([exp for exp in expansions if exp not in query_lower])
        
        # Use entity types to add related search terms
        entity_types_in_query = set(e['type'] for e in entities)
        
        if 'MOVIE' in entity_types_in_query or 'MOVIE_TYPE' in entity_types_in_query:
            expanded_terms.extend(['plot', 'story', 'narrative', 'cốt truyện'])
        
        if 'PERSON' in entity_types_in_query or 'PERSON_TYPE' in entity_types_in_query:
            expanded_terms.extend(['cast', 'actor', 'director', 'filmmaker', 'diễn xuất'])
        
        if 'GENRE' in entity_types_in_query or 'GENRE_TYPE' in entity_types_in_query:
            expanded_terms.extend(['theme', 'style', 'tone', 'phong cách'])
        
        # Remove duplicates
        expanded_terms = list(set(expanded_terms))[:10]  # Limit to 10 terms
        
        print(f"  ✓ Expanded with {len(expanded_terms)} related terms")
        return expanded_terms

    def enhance_search_query(self, original_query: str, processed: Dict[str, Any]) -> str:
        """
        Combines original query with expanded terms for better semantic search.
        
        Args:
            original_query: Original user query
            processed: Output from process_query()
            
        Returns:
            Enhanced query string for vector search
        """
        # Start with original query
        enhanced = original_query
        
        # Add entity names for emphasis
        entity_terms = [e['text'] for e in processed['entities'] 
                       if e['type'] in ['MOVIE', 'PERSON', 'GENRE']]
        
        # Add expanded terms
        expanded = processed['expanded_terms'][:5]  # Top 5 expanded terms
        
        # Combine intelligently
        if entity_terms:
            enhanced += " " + " ".join(entity_terms)
        if expanded:
            enhanced += " " + " ".join(expanded)
        
        return enhanced.strip()

    def get_cypher_query(self, processed: Dict[str, Any]) -> str:
        """
        Generate Cypher query for Neo4j based on structured query.
        This enables direct graph database querying.
        
        Args:
            processed: Output from process_query()
            
        Returns:
            Cypher query string
        """
        structured = processed['structured_query']
        
        # Build MATCH clause
        match_parts = []
        where_parts = []
        
        # Add nodes
        for node in structured['nodes']:
            label = node['label']
            name = node['name']
            match_parts.append(f"(n:{label})")
            where_parts.append(f"toLower(n.name) CONTAINS toLower('{name}') OR toLower(n.title) CONTAINS toLower('{name}')")
        
        # Add relations
        for edge in structured['edges']:
            rel_type = edge['type']
            match_parts.append(f"-[:{rel_type}]-")
        
        # Add filters
        if 'year' in structured['filters']:
            where_parts.append(f"n.year = {structured['filters']['year']}")
        
        # Construct full query
        if match_parts:
            match_clause = "MATCH " + "".join(match_parts) + "(m:Movie)"
        else:
            match_clause = "MATCH (m:Movie)"
        
        where_clause = "WHERE " + " OR ".join(where_parts) if where_parts else ""
        
        return_clause = "RETURN m.title, m.year, m.overview LIMIT 10"
        
        cypher = f"{match_clause}\n{where_clause}\n{return_clause}"
        
        return cypher.strip()

    # ==========================================
    # ENHANCED METHODS - NEW
    # ==========================================
    
    def _validate_query(self, query: str) -> bool:
        """Validate query is not empty or too short"""
        if not query or not isinstance(query, str):
            return False
        query = query.strip()
        return len(query) >= 3 and len(query) <= 1000
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query text"""
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Remove special characters (but keep Vietnamese diacritics)
        # query = re.sub(r'[^\w\sÀ-ỹ.,!?-]', '', query)
        
        # Normalize quotation marks
        query = query.replace('"', '"').replace('"', '"')
        query = query.replace(''', "'").replace(''', "'")
        
        return query.strip()
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.lower().encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache query result with size limit"""
        # Don't cache errors or low-confidence results
        if result.get('error') or result.get('confidence', 0) < 0.3:
            return
        
        # Remove cache entries if max size exceeded
        if len(self._query_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            first_key = next(iter(self._query_cache))
            del self._query_cache[first_key]
        
        # Remove non-cacheable fields
        cacheable = result.copy()
        cacheable.pop('processing_time', None)
        cacheable.pop('cached', None)
        
        self._query_cache[cache_key] = cacheable
    
    def _empty_result(self, query: str, reason: str) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'original_query': query,
            'cleaned_query': query,
            'entities': [],
            'relations': [],
            'structured_query': {},
            'sub_queries': [],
            'expanded_terms': [],
            'confidence': 0.0,
            'processing_time': 0.0,
            'cached': False,
            'rewritten_query': None,
            'error': reason
        }
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on processing results.
        Confidence = weighted average of:
        - Entity detection quality (40%)
        - Relation detection quality (30%)
        - Query expansion quality (20%)
        - Query structure quality (10%)
        """
        scores = []
        
        # Entity score
        entity_count = len(result['entities'])
        if entity_count > 0:
            avg_entity_confidence = sum(e['confidence'] for e in result['entities']) / entity_count
            entity_score = min(1.0, avg_entity_confidence * (entity_count / 3))  # Optimal: 3 entities
            scores.append(('entities', entity_score, 0.4))
        
        # Relation score
        relation_count = len(result['relations'])
        if relation_count > 0:
            avg_relation_confidence = sum(r['confidence'] for r in result['relations']) / relation_count
            relation_score = min(1.0, avg_relation_confidence * (relation_count / 2))  # Optimal: 2 relations
            scores.append(('relations', relation_score, 0.3))
        
        # Expansion score
        expansion_count = len(result['expanded_terms'])
        if expansion_count > 0:
            expansion_score = min(1.0, expansion_count / 10)  # Optimal: 10 terms
            scores.append(('expansion', expansion_score, 0.2))
        
        # Structure score
        struct = result['structured_query']
        if struct and (struct.get('nodes') or struct.get('edges')):
            structure_score = 0.5 + (0.25 if struct.get('nodes') else 0) + (0.25 if struct.get('edges') else 0)
            scores.append(('structure', structure_score, 0.1))
        
        # Calculate weighted average
        if not scores:
            return 0.3  # Base confidence if nothing found
        
        total_weight = sum(weight for _, _, weight in scores)
        weighted_sum = sum(score * weight for _, score, weight in scores)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.3
    
    def _needs_rewriting(self, result: Dict[str, Any]) -> bool:
        """Determine if query needs rewriting for better results"""
        # Rewrite if:
        # 1. Low confidence and few entities
        # 2. No relations found but query seems complex
        # 3. Very short query with ambiguous intent
        
        if result['confidence'] < 0.5 and len(result['entities']) < 2:
            return True
        
        if not result['relations'] and self._is_complex_query(result['cleaned_query']):
            return True
        
        if len(result['cleaned_query'].split()) <= 3 and not result['entities']:
            return True
        
        return False
    
    def _rewrite_query(self, query: str, result: Dict[str, Any]) -> str:
        """
        Rewrite query to improve matching.
        Adds context and expands abbreviated terms.
        """
        rewritten = query
        
        # Add "movie" or "film" if not present and no movie entity detected
        if 'phim' not in query.lower() and 'movie' not in query.lower() and 'film' not in query.lower():
            if not any(e['type'] == 'MOVIE' for e in result['entities']):
                rewritten = f"Movie {rewritten}"
        
        # Expand abbreviations (for both English and Vietnamese)
        abbreviations = {
            'hd': 'hành động',
            'tc': 'tình cảm',
            'kh': 'khoa học viễn tưởng',
            'sci-fi': 'science fiction',
            'rom-com': 'romantic comedy',
        }
        
        words = rewritten.split()
        expanded_words = [abbreviations.get(w.lower(), w) for w in words]
        rewritten = ' '.join(expanded_words)
        
        return rewritten
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        cache_hit_rate = (self.stats['cache_hits'] / self.stats['queries_processed'] * 100) if self.stats['queries_processed'] > 0 else 0
        
        return {
            'queries_processed': self.stats['queries_processed'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'cache_size': len(self._query_cache),
            'total_entities_found': self.stats['entities_found'],
            'total_relations_found': self.stats['relations_found'],
            'avg_entities_per_query': self.stats['entities_found'] / self.stats['queries_processed'] if self.stats['queries_processed'] > 0 else 0,
            'avg_relations_per_query': self.stats['relations_found'] / self.stats['queries_processed'] if self.stats['queries_processed'] > 0 else 0
        }
    
    def clear_cache(self) -> None:
        """Clear the query cache"""
        self._query_cache.clear()
        print("✅ Query cache cleared")
