"""
Graph Organizer - Post-processing & Refinement
Implements organizer techniques from GraphRAG paper:
1. Graph Pruning - Remove irrelevant nodes/edges
2. Reranking - Prioritize important information
3. Graph Augmentation - Enrich content
4. Verbalizing - Convert graph to natural language
"""

from typing import List, Dict, Any, Tuple
from .llm_service import GeminiService


class GraphPruner:
    """Graph Pruning: Remove irrelevant and noisy information"""
    
    def __init__(self, llm_service: GeminiService):
        self.llm = llm_service
    
    def semantic_prune(self, contexts: List[str], query: str, 
                       top_k: int = 10) -> List[str]:
        """
        Semantic-based pruning: Remove semantically irrelevant contexts
        Scores each context based on relevance to query
        """
        if len(contexts) <= top_k:
            return contexts
        
        print(f"    → Semantic pruning: {len(contexts)} → {top_k} contexts")
        
        # Score each context
        scored_contexts = []
        for ctx in contexts:
            score = self._compute_relevance_score(ctx, query)
            scored_contexts.append((ctx, score))
        
        # Sort by score and keep top-k
        scored_contexts.sort(key=lambda x: x[1], reverse=True)
        pruned = [ctx for ctx, score in scored_contexts[:top_k]]
        
        return pruned
    
    def _compute_relevance_score(self, context: str, query: str) -> float:
        """Compute semantic relevance score using simple heuristics"""
        # Simple scoring based on keyword overlap
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        
        # Jaccard similarity
        intersection = query_words & context_words
        union = query_words | context_words
        
        if not union:
            return 0.0
        
        score = len(intersection) / len(union)
        return score
    
    def structure_prune(self, graph_results: List[Dict], 
                       max_distance: int = 2) -> List[Dict]:
        """
        Structure-based pruning: Remove nodes based on graph distance
        Keep only nodes within max_distance hops
        """
        if not graph_results:
            return graph_results
        
        print(f"    → Structure pruning: max distance = {max_distance} hops")
        
        pruned = [
            node for node in graph_results
            if node.get('distance', 0) <= max_distance
        ]
        
        print(f"    → Kept {len(pruned)}/{len(graph_results)} nodes")
        return pruned
    
    def diversity_prune(self, contexts: List[str], 
                       diversity_threshold: float = 0.7) -> List[str]:
        """
        Diversity pruning: Remove highly similar duplicate contexts
        """
        if len(contexts) <= 1:
            return contexts
        
        print(f"    → Diversity pruning (threshold: {diversity_threshold})")
        
        diverse_contexts = [contexts[0]]  # Always keep first
        
        for ctx in contexts[1:]:
            # Check if too similar to existing contexts
            is_diverse = True
            for existing_ctx in diverse_contexts:
                similarity = self._compute_similarity(ctx, existing_ctx)
                if similarity > diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_contexts.append(ctx)
        
        print(f"    → Kept {len(diverse_contexts)}/{len(contexts)} diverse contexts")
        return diverse_contexts
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0


class ContextReranker:
    """Reranking: Prioritize most important information"""
    
    def __init__(self, llm_service: GeminiService):
        self.llm = llm_service
    
    def rerank_by_relevance(self, contexts: List[str], query: str) -> List[str]:
        """
        Rerank contexts by relevance to query
        Most relevant contexts appear first (important for LLM attention)
        """
        if len(contexts) <= 1:
            return contexts
        
        print(f"    → Reranking {len(contexts)} contexts by relevance")
        
        # Score each context
        scored = []
        for ctx in contexts:
            score = self._compute_query_relevance(ctx, query)
            scored.append((ctx, score))
        
        # Sort by score (highest first)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        reranked = [ctx for ctx, score in scored]
        return reranked
    
    def rerank_by_source_type(self, contexts: List[str]) -> List[str]:
        """
        Rerank by source type priority
        Priority: Vector Match > Entity Linked > Graph Neighbor
        """
        print(f"    → Reranking by source type")
        
        vector_contexts = []
        entity_contexts = []
        graph_contexts = []
        other_contexts = []
        
        for ctx in contexts:
            if '[Vector Match]' in ctx:
                vector_contexts.append(ctx)
            elif '[Entity Linked]' in ctx:
                entity_contexts.append(ctx)
            elif '[Graph' in ctx:
                graph_contexts.append(ctx)
            else:
                other_contexts.append(ctx)
        
        # Combine in priority order
        reranked = vector_contexts + entity_contexts + graph_contexts + other_contexts
        return reranked
    
    def rerank_by_position_strategy(self, contexts: List[str], 
                                    strategy: str = 'important_first') -> List[str]:
        """
        Rerank based on LLM attention bias strategy
        
        Strategies:
        - 'important_first': Most important at start
        - 'important_edges': Important at start and end
        - 'sandwich': Important at start, middle, end
        """
        if len(contexts) <= 3:
            return contexts
        
        print(f"    → Position strategy: {strategy}")
        
        if strategy == 'important_first':
            # Already sorted by relevance, keep as is
            return contexts
        
        elif strategy == 'important_edges':
            # Most important at start and end
            # Less important in middle
            n = len(contexts)
            reranked = []
            
            # Interleave: 1st, last, 2nd, 2nd-last, etc.
            left = 0
            right = n - 1
            from_start = True
            
            while left <= right:
                if from_start:
                    reranked.append(contexts[left])
                    left += 1
                else:
                    reranked.append(contexts[right])
                    right -= 1
                from_start = not from_start
            
            return reranked
        
        else:  # 'sandwich'
            # Top 30% at start, middle 40% in center, bottom 30% at end
            n = len(contexts)
            top_n = max(1, n * 3 // 10)
            mid_n = n - 2 * top_n
            
            reranked = (
                contexts[:top_n] +           # Important first
                contexts[-top_n:] +          # Important end
                contexts[top_n:top_n+mid_n]  # Less important middle
            )
            return reranked
    
    def _compute_query_relevance(self, context: str, query: str) -> float:
        """Compute how relevant context is to query"""
        query_words = set(query.lower().split())
        context_words = set(context.lower().split())
        
        # Weighted scoring
        exact_matches = len(query_words & context_words)
        context_len_penalty = len(context) / 1000  # Penalize too long contexts
        
        score = exact_matches - context_len_penalty * 0.1
        return max(0, score)


class GraphAugmenter:
    """Graph Augmentation: Enrich retrieved content"""
    
    def __init__(self, llm_service: GeminiService):
        self.llm = llm_service
    
    def augment_with_query_node(self, contexts: List[str], query: str) -> List[str]:
        """
        Add query as a special context to create connection
        Helps LLM understand the question in context
        """
        query_context = f"[Query Context] User asks: {query}"
        augmented = [query_context] + contexts
        
        print(f"    → Augmented with query node")
        return augmented
    
    def augment_with_summary(self, contexts: List[str], query: str) -> List[str]:
        """
        Add a summary context at the beginning
        Helps LLM get overview before details
        """
        if len(contexts) < 3:
            return contexts
        
        # Create simple summary
        num_movies = sum(1 for ctx in contexts if 'Title:' in ctx or 'Movie' in ctx)
        num_persons = sum(1 for ctx in contexts if 'Person' in ctx or 'Director' in ctx)
        
        summary = f"[Context Summary] Found {num_movies} movies and {num_persons} people related to: {query}"
        
        augmented = [summary] + contexts
        print(f"    → Augmented with summary")
        return augmented
    
    def augment_with_metadata(self, contexts: List[str], 
                             metadata: Dict[str, Any]) -> List[str]:
        """
        Add metadata information to contexts
        Example: retrieval method, confidence scores, source types
        """
        meta_str = f"[Metadata] "
        meta_parts = []
        
        if 'retrieval_depth' in metadata:
            meta_parts.append(f"Depth: {metadata['retrieval_depth']} hops")
        if 'vector_count' in metadata:
            meta_parts.append(f"Vector results: {metadata['vector_count']}")
        if 'graph_count' in metadata:
            meta_parts.append(f"Graph results: {metadata['graph_count']}")
        
        if meta_parts:
            meta_str += ", ".join(meta_parts)
            augmented = [meta_str] + contexts
            print(f"    → Augmented with metadata")
            return augmented
        
        return contexts


class GraphVerbalizer:
    """Verbalizing: Convert graph structures to natural language"""
    
    def __init__(self, llm_service: GeminiService):
        self.llm = llm_service
    
    def tuple_based_verbalize(self, graph_results: List[Dict]) -> List[str]:
        """
        Tuple-based verbalization: (entity1, relation, entity2)
        Simple and direct conversion
        """
        contexts = []
        
        for result in graph_results:
            if 'source' in result and 'relationship' in result and 'target' in result:
                # Triple format
                ctx = f"({result['source']}, {result['relationship']}, {result['target']})"
                contexts.append(ctx)
            elif 'name' in result and 'type' in result:
                # Node format
                ctx = f"{result['type']}: {result['name']}"
                contexts.append(ctx)
        
        return contexts
    
    def template_based_verbalize(self, graph_results: List[Dict]) -> List[str]:
        """
        Template-based verbalization: Natural language templates
        More readable for LLMs
        """
        contexts = []
        
        for result in graph_results:
            if 'source' in result and 'relationship' in result and 'target' in result:
                # Relationship template
                rel = result['relationship']
                source = result['source']
                target = result['target']
                
                if rel == 'DIRECTED':
                    ctx = f"{source} directed the movie {target}"
                elif rel == 'ACTED_IN':
                    ctx = f"{source} acted in {target}"
                elif rel == 'BELONGS_TO':
                    ctx = f"{source} belongs to genre {target}"
                else:
                    ctx = f"{source} has {rel} relationship with {target}"
                
                contexts.append(ctx)
            
            elif 'name' in result and 'type' in result:
                # Node template
                ctx = f"There is a {result['type']} named {result['name']}"
                if 'distance' in result:
                    ctx += f" (distance: {result['distance']} hops)"
                contexts.append(ctx)
        
        return contexts
    
    def narrative_verbalize(self, contexts: List[str], query: str) -> str:
        """
        Create a narrative summary from contexts
        Most natural form for LLM consumption
        """
        if not contexts:
            return "No relevant information found."
        
        # Group by type
        vector_matches = [c for c in contexts if '[Vector Match]' in c]
        entities = [c for c in contexts if '[Entity Linked]' in c]
        graph_info = [c for c in contexts if '[Graph' in c]
        
        narrative_parts = []
        
        if vector_matches:
            narrative_parts.append(
                f"Based on semantic search, found {len(vector_matches)} relevant movies."
            )
        
        if entities:
            narrative_parts.append(
                f"Identified {len(entities)} key entities related to the query."
            )
        
        if graph_info:
            narrative_parts.append(
                f"Explored knowledge graph and found {len(graph_info)} connected information."
            )
        
        narrative = " ".join(narrative_parts)
        
        # Add actual context
        narrative += "\n\nDetailed Information:\n"
        narrative += "\n".join(contexts[:10])  # Limit to top 10
        
        return narrative


class GraphOrganizer:
    """
    Main Organizer: Orchestrates all post-processing techniques
    Pipeline: Prune → Rerank → Augment → Verbalize
    """
    
    def __init__(self, llm_service: GeminiService):
        self.llm = llm_service
        self.pruner = GraphPruner(llm_service)
        self.reranker = ContextReranker(llm_service)
        self.augmenter = GraphAugmenter(llm_service)
        self.verbalizer = GraphVerbalizer(llm_service)
    
    def organize(self, contexts: List[str], query: str, 
                metadata: Dict[str, Any] = None,
                config: Dict[str, Any] = None) -> List[str]:
        """
        Main organization pipeline
        
        Args:
            contexts: Retrieved contexts
            query: User query
            metadata: Retrieval metadata
            config: Organization configuration
        
        Returns:
            Organized and refined contexts
        """
        if not contexts:
            return contexts
        
        if metadata is None:
            metadata = {}
        
        if config is None:
            config = {
                'enable_pruning': True,
                'enable_reranking': True,
                'enable_augmentation': True,
                'max_contexts': 15,
                'diversity_threshold': 0.7,
                'position_strategy': 'important_first'
            }
        
        print(f"\n  🔧 Organizing {len(contexts)} contexts...")
        
        organized = contexts.copy()
        
        # Step 1: Pruning
        if config.get('enable_pruning', True):
            print(f"  📊 Step 1: Pruning")
            
            # Semantic pruning
            if len(organized) > config.get('max_contexts', 15):
                organized = self.pruner.semantic_prune(
                    organized, query, 
                    top_k=config.get('max_contexts', 15)
                )
            
            # Diversity pruning
            organized = self.pruner.diversity_prune(
                organized,
                diversity_threshold=config.get('diversity_threshold', 0.7)
            )
        
        # Step 2: Reranking
        if config.get('enable_reranking', True):
            print(f"  🔄 Step 2: Reranking")
            
            # Relevance-based reranking
            organized = self.reranker.rerank_by_relevance(organized, query)
            
            # Source type reranking
            organized = self.reranker.rerank_by_source_type(organized)
            
            # Position strategy
            organized = self.reranker.rerank_by_position_strategy(
                organized,
                strategy=config.get('position_strategy', 'important_first')
            )
        
        # Step 3: Augmentation
        if config.get('enable_augmentation', True):
            print(f"  ➕ Step 3: Augmentation")
            
            # Add summary
            organized = self.augmenter.augment_with_summary(organized, query)
            
            # Add query context
            organized = self.augmenter.augment_with_query_node(organized, query)
            
            # Add metadata if available
            if metadata:
                organized = self.augmenter.augment_with_metadata(organized, metadata)
        
        print(f"  ✓ Organization complete: {len(organized)} refined contexts")
        
        return organized


def create_organizer(llm_service: GeminiService) -> GraphOrganizer:
    """Factory function to create organizer"""
    return GraphOrganizer(llm_service)
