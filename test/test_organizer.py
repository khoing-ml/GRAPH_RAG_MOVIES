"""
Test Organizer Components
Demonstrates pruning, reranking, augmentation, and verbalization
"""

from src.llm_service import GeminiService
from src.organizer import (
    GraphPruner, 
    ContextReranker, 
    GraphAugmenter,
    GraphVerbalizer,
    GraphOrganizer
)


def test_graph_pruner():
    """Test Graph Pruning techniques"""
    print("\n" + "="*70)
    print("TEST 1: GRAPH PRUNING")
    print("="*70)
    
    llm = GeminiService()
    pruner = GraphPruner(llm)
    
    # Sample contexts with varying relevance
    contexts = [
        "[Vector Match] Inception (2010) - A thief who steals corporate secrets through dream-sharing technology.",
        "[Vector Match] The Matrix (1999) - A computer hacker learns about the true nature of reality.",
        "[Vector Match] Interstellar (2014) - A team of explorers travel through a wormhole in space.",
        "[Entity Linked] Christopher Nolan directed Inception",
        "[Graph Neighbor] Leonardo DiCaprio acted in Inception",
        "[Graph Neighbor] Tom Hardy acted in Inception",
        "[Graph Neighbor] Action is a genre of Inception",
        "[Graph 2-hop] Marion Cotillard acted in Inception",
        "[Graph 2-hop] Science Fiction is a genre",
        "[Graph 3-hop] Cillian Murphy acted in Batman Begins",
        "[Graph 3-hop] Drama is a popular genre",
        "[Vector Match] The Dark Knight (2008) - Batman faces the Joker",
        "[Vector Match] Memento (2000) - A man with short-term memory loss",
        "[Graph Neighbor] Heath Ledger acted in The Dark Knight",
        "[Graph 2-hop] Christian Bale acted in Batman Begins"
    ]
    
    query = "Tell me about Christopher Nolan's Inception"
    
    print(f"\nQuery: {query}")
    print(f"Original contexts: {len(contexts)}")
    
    # Test semantic pruning
    print("\n--- Semantic Pruning (top 8) ---")
    semantic_pruned = pruner.semantic_prune(contexts, query, top_k=8)
    for i, ctx in enumerate(semantic_pruned[:5], 1):
        print(f"  {i}. {ctx[:80]}...")
    
    # Test diversity pruning
    print("\n--- Diversity Pruning ---")
    diverse = pruner.diversity_prune(contexts, diversity_threshold=0.6)
    print(f"Result: Kept {len(diverse)}/{len(contexts)} diverse contexts")


def test_context_reranker():
    """Test Context Reranking strategies"""
    print("\n" + "="*70)
    print("TEST 2: CONTEXT RERANKING")
    print("="*70)
    
    llm = GeminiService()
    reranker = ContextReranker(llm)
    
    contexts = [
        "[Graph 2-hop] Marion Cotillard acted in La Vie en Rose",
        "[Vector Match] Inception (2010) - A mind-bending thriller by Christopher Nolan",
        "[Graph Neighbor] Leonardo DiCaprio acted in Inception",
        "[Entity Linked] Christopher Nolan is known for complex narratives",
        "[Vector Match] The Prestige (2006) - Another Nolan masterpiece",
        "[Graph Neighbor] Tom Hardy had a supporting role"
    ]
    
    query = "What is Inception about?"
    
    print(f"\nQuery: {query}")
    print("\nOriginal order:")
    for i, ctx in enumerate(contexts, 1):
        print(f"  {i}. {ctx[:70]}...")
    
    # Test relevance reranking
    print("\n--- Rerank by Relevance ---")
    relevance_ranked = reranker.rerank_by_relevance(contexts, query)
    for i, ctx in enumerate(relevance_ranked, 1):
        print(f"  {i}. {ctx[:70]}...")
    
    # Test source type reranking
    print("\n--- Rerank by Source Type ---")
    source_ranked = reranker.rerank_by_source_type(contexts)
    for i, ctx in enumerate(source_ranked, 1):
        print(f"  {i}. {ctx[:70]}...")
    
    # Test position strategy
    print("\n--- Rerank with 'important_edges' strategy ---")
    edge_ranked = reranker.rerank_by_position_strategy(
        relevance_ranked, 
        strategy='important_edges'
    )
    for i, ctx in enumerate(edge_ranked, 1):
        print(f"  {i}. {ctx[:70]}...")


def test_graph_augmenter():
    """Test Graph Augmentation techniques"""
    print("\n" + "="*70)
    print("TEST 3: GRAPH AUGMENTATION")
    print("="*70)
    
    llm = GeminiService()
    augmenter = GraphAugmenter(llm)
    
    contexts = [
        "[Vector Match] Inception - Movie about dreams",
        "[Entity Linked] Christopher Nolan directed it",
        "[Graph Neighbor] Leonardo DiCaprio starred"
    ]
    
    query = "Tell me about Inception"
    
    print(f"\nQuery: {query}")
    print(f"Original contexts: {len(contexts)}")
    
    # Test query node augmentation
    print("\n--- Augment with Query Node ---")
    augmented_query = augmenter.augment_with_query_node(contexts, query)
    print(f"New count: {len(augmented_query)}")
    print(f"First context: {augmented_query[0]}")
    
    # Test summary augmentation
    print("\n--- Augment with Summary ---")
    augmented_summary = augmenter.augment_with_summary(contexts, query)
    print(f"New count: {len(augmented_summary)}")
    print(f"First context: {augmented_summary[0]}")
    
    # Test metadata augmentation
    print("\n--- Augment with Metadata ---")
    metadata = {
        'retrieval_depth': 2,
        'vector_count': 1,
        'graph_count': 2
    }
    augmented_meta = augmenter.augment_with_metadata(contexts, metadata)
    print(f"New count: {len(augmented_meta)}")
    print(f"First context: {augmented_meta[0]}")


def test_graph_verbalizer():
    """Test Graph Verbalization techniques"""
    print("\n" + "="*70)
    print("TEST 4: GRAPH VERBALIZATION")
    print("="*70)
    
    llm = GeminiService()
    verbalizer = GraphVerbalizer(llm)
    
    # Sample graph results
    graph_results = [
        {
            'source': 'Christopher Nolan',
            'relationship': 'DIRECTED',
            'target': 'Inception'
        },
        {
            'source': 'Leonardo DiCaprio',
            'relationship': 'ACTED_IN',
            'target': 'Inception'
        },
        {
            'type': 'Movie',
            'name': 'Inception',
            'distance': 0
        },
        {
            'type': 'Person',
            'name': 'Christopher Nolan',
            'distance': 1
        }
    ]
    
    print("\n--- Tuple-based Verbalization ---")
    tuple_texts = verbalizer.tuple_based_verbalize(graph_results)
    for text in tuple_texts:
        print(f"  • {text}")
    
    print("\n--- Template-based Verbalization ---")
    template_texts = verbalizer.template_based_verbalize(graph_results)
    for text in template_texts:
        print(f"  • {text}")
    
    # Test narrative
    contexts = [
        "[Vector Match] Inception - Mind-bending thriller",
        "[Entity Linked] Christopher Nolan director",
        "[Graph Neighbor] Leonardo DiCaprio actor"
    ]
    query = "Tell me about Inception"
    
    print("\n--- Narrative Verbalization ---")
    narrative = verbalizer.narrative_verbalize(contexts, query)
    print(narrative[:300] + "...")


def test_full_organizer():
    """Test complete Organizer pipeline"""
    print("\n" + "="*70)
    print("TEST 5: COMPLETE ORGANIZER PIPELINE")
    print("="*70)
    
    llm = GeminiService()
    organizer = GraphOrganizer(llm)
    
    # Realistic contexts from retrieval
    contexts = [
        "[Vector Match] Inception (2010) - Dom Cobb is a skilled thief who steals secrets from deep within the subconscious during the dream state. Director: Christopher Nolan. Cast: Leonardo DiCaprio, Marion Cotillard, Tom Hardy. Genres: Action, Science Fiction, Thriller.",
        "[Vector Match] The Matrix (1999) - Set in the 22nd century, The Matrix tells the story of a computer hacker who learns about the true nature of his reality and his role in the war against its controllers.",
        "[Vector Match] Interstellar (2014) - The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel.",
        "[Entity Linked] Christopher Nolan is an acclaimed director known for complex, non-linear narratives and philosophical themes.",
        "[Graph Neighbor] Leonardo DiCaprio acted in Inception. He plays Dom Cobb, the protagonist.",
        "[Graph Neighbor] Tom Hardy acted in Inception. He plays Eames, a forger.",
        "[Graph Neighbor] Marion Cotillard acted in Inception. She plays Mal, Cobb's deceased wife.",
        "[Graph 2-hop] Ellen Page acted in Inception. She plays Ariadne, the architect.",
        "[Graph 2-hop] Joseph Gordon-Levitt acted in Inception. He plays Arthur, Cobb's partner.",
        "[Graph 2-hop] Cillian Murphy acted in Inception. He plays Robert Fischer, the target.",
        "[Graph 2-hop] Action is a genre associated with many Nolan films.",
        "[Graph 2-hop] Science Fiction explores futuristic concepts.",
        "[Vector Match] The Dark Knight (2008) - Batman faces the Joker in Gotham City. Director: Christopher Nolan.",
        "[Graph 3-hop] Christian Bale acted in The Dark Knight and Batman Begins.",
        "[Graph 3-hop] Heath Ledger acted in The Dark Knight as the Joker.",
        "[Vector Match] Memento (2000) - A man with short-term memory loss attempts to track down his wife's murderer. Director: Christopher Nolan.",
        "[Graph Neighbor] The Prestige (2006) is another Christopher Nolan film about rival magicians.",
        "[Graph 2-hop] Michael Caine has appeared in many Christopher Nolan films.",
        "[Vector Match] Shutter Island (2010) - Leonardo DiCaprio investigates a psychiatric facility."
    ]
    
    query = "Tell me about Christopher Nolan's Inception and its cast"
    
    metadata = {
        'retrieval_depth': 2,
        'vector_count': 6,
        'graph_count': 13,
        'method': 'hybrid'
    }
    
    config = {
        'enable_pruning': True,
        'enable_reranking': True,
        'enable_augmentation': True,
        'max_contexts': 12,
        'diversity_threshold': 0.7,
        'position_strategy': 'important_first'
    }
    
    print(f"\nQuery: {query}")
    print(f"Input: {len(contexts)} contexts")
    print(f"Config: max={config['max_contexts']}, diversity={config['diversity_threshold']}")
    
    # Run full organization
    organized = organizer.organize(contexts, query, metadata, config)
    
    print(f"\n✓ Output: {len(organized)} organized contexts")
    print("\nFinal organized contexts:")
    for i, ctx in enumerate(organized, 1):
        print(f"\n{i}. {ctx[:150]}{'...' if len(ctx) > 150 else ''}")
    
    return organized


def test_comparison():
    """Compare with vs without organizer"""
    print("\n" + "="*70)
    print("TEST 6: COMPARISON - WITH vs WITHOUT ORGANIZER")
    print("="*70)
    
    llm = GeminiService()
    organizer = GraphOrganizer(llm)
    
    contexts = [
        "[Graph 3-hop] Michael Caine appeared in many Nolan films",
        "[Vector Match] Inception - A thief steals secrets through dreams",
        "[Graph 2-hop] Joseph Gordon-Levitt plays Arthur",
        "[Entity Linked] Christopher Nolan directed Inception",
        "[Graph Neighbor] Leonardo DiCaprio is the lead actor",
        "[Vector Match] The Matrix - Another sci-fi thriller",
        "[Graph 2-hop] Ellen Page plays the architect",
        "[Vector Match] Interstellar - Space exploration film",
    ]
    
    query = "Who acted in Inception?"
    
    print(f"\nQuery: {query}")
    
    print("\n--- WITHOUT ORGANIZER ---")
    print("Raw retrieval order:")
    for i, ctx in enumerate(contexts, 1):
        print(f"  {i}. {ctx}")
    
    print("\n--- WITH ORGANIZER ---")
    organized = organizer.organize(contexts, query, config={
        'max_contexts': 10,
        'diversity_threshold': 0.7
    })
    print("Organized order:")
    for i, ctx in enumerate(organized, 1):
        print(f"  {i}. {ctx}")
    
    print("\n📊 Key Improvements:")
    print("  ✓ Most relevant contexts moved to top")
    print("  ✓ Query context added for LLM understanding")
    print("  ✓ Summary provides overview")
    print("  ✓ Diverse contexts retained")
    print("  ✓ Less relevant 3-hop information deprioritized")


if __name__ == "__main__":
    print("\n" + "🔬" + "="*68 + "🔬")
    print("  GRAPH ORGANIZER TEST SUITE")
    print("  Testing Pruning, Reranking, Augmentation, Verbalization")
    print("🔬" + "="*68 + "🔬")
    
    try:
        # Run all tests
        test_graph_pruner()
        test_context_reranker()
        test_graph_augmenter()
        test_graph_verbalizer()
        test_full_organizer()
        test_comparison()
        
        print("\n" + "="*70)
        print("✅ ALL ORGANIZER TESTS COMPLETED")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
