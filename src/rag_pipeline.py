from .llm_service import GeminiService
from .vector_db import QdrantService
from .graph_db import Neo4jService
from .query_processor import QueryProcessor
from .advanced_retriever import create_advanced_retriever
from .organizer import create_organizer

class GraphRAG:
    def __init__(self, use_advanced_retriever=False, use_organizer=True, enable_fallback=True, augment_mode=False):
        """
        Initialize GraphRAG pipeline
        
        Args:
            use_advanced_retriever: If True, uses hybrid neural+symbolic retriever
                                   If False, uses basic vector search (default)
            use_organizer: If True, applies post-processing and refinement
            enable_fallback: If True, uses fallback model when no relevant context found
            augment_mode: If True, ALWAYS calls both models and synthesizes answers
                         If False, only fallback when database lacks info (default)
        """
        self.llm = GeminiService()
        self.vectordb = QdrantService()
        self.graphdb = Neo4jService()
        self.query_processor = QueryProcessor(self.llm)
        
        # Augmentation mode - always call both models
        self.augment_mode = augment_mode
        
        # Fallback model for general knowledge
        self.enable_fallback = enable_fallback
        self.fallback_llm = None
        if self.enable_fallback or self.augment_mode:
            try:
                # Initialize a separate LLM instance for fallback with general knowledge role
                self.fallback_llm = GeminiService()
                # Override the model to use a system instruction if possible
                # For now, we'll use custom prompting to make it act as general assistant
                mode_desc = "Augmentation" if self.augment_mode else "Fallback"
                print(f"  ✓ {mode_desc} model enabled (Gemini 2.0 Flash - General Knowledge)")
            except Exception as e:
                print(f"  ⚠️ {mode_desc} model initialization failed: {e}")
                self.enable_fallback = False
                self.augment_mode = False
        
        # Store last contexts for evaluation
        self.last_contexts = []
        self.last_movies = []
        self.last_method = None  # Track which method was used
        
        # Advanced retriever (optional)
        self.use_advanced = use_advanced_retriever
        if self.use_advanced:
            self.advanced_retriever = create_advanced_retriever(
                self.llm, self.vectordb, self.graphdb
            )
            print("  ✓ Advanced Hybrid Retriever enabled")
        
        # Organizer for post-processing (optional)
        self.use_organizer = use_organizer
        if self.use_organizer:
            self.organizer = create_organizer(self.llm)
            print("  ✓ Graph Organizer enabled")

    def query(self, user_question, chat_history=None):
        print(f"\n🔎 Understanding: '{user_question}'...")
        
        # STEP 0: Query Processing (ENHANCED - GraphRAG)
        # Apply 5 query processing techniques with validation, caching, and confidence scoring
        processed_query = self.query_processor.process_query(user_question, use_cache=True)
        
        # Check if query processing failed
        if processed_query.get('error'):
            print(f"  ⚠️ Query processing issue: {processed_query['error']}")
            return "Sorry, your question is invalid or too short. Please try again with a clearer question."
        
        # Show processing metrics
        confidence = processed_query.get('confidence', 0)
        cached = processed_query.get('cached', False)
        cache_indicator = " 📦" if cached else ""
        print(f"  ✓ Query processed (confidence: {confidence:.2f}){cache_indicator}")
        
        # CONFIDENCE THRESHOLD CHECK: Use fallback if query confidence is too low
        CONFIDENCE_THRESHOLD = 0.75
        if confidence < CONFIDENCE_THRESHOLD:
            print(f"  ⚠️ Query confidence ({confidence:.2f}) below threshold ({CONFIDENCE_THRESHOLD}) - using fallback")
            return self._fallback_to_general_knowledge(
                user_question, 
                chat_history, 
                f"Low query confidence ({confidence:.2f} < {CONFIDENCE_THRESHOLD})"
            )
        
        # Use rewritten query if available, otherwise enhanced query
        if processed_query.get('rewritten_query'):
            search_query = processed_query['rewritten_query']
            print(f"  ↻ Rewritten: '{search_query}'")
        else:
            search_query = self.query_processor.enhance_search_query(
                user_question, processed_query
            )
            print(f"  → Enhanced: '{search_query[:80]}...'")
        
        # STEP 1: Retrieval (Basic or Advanced)
        if self.use_advanced:
            # ADVANCED RETRIEVAL: Hybrid Neural + Symbolic
            print("🔬 Using Advanced Hybrid Retriever...")
            
            query_metadata = {
                'category': processed_query.get('category', 'unknown'),
                'entities': processed_query.get('entities', []),
                'relations': processed_query.get('relations', [])
            }
            
            retrieval_results = self.advanced_retriever.retrieve(
                search_query,
                query_metadata=query_metadata,
                top_k_vector=6
            )
            
            # Check if we have meaningful results
            if not retrieval_results['contexts'] or retrieval_results['method'] == 'internal_knowledge':
                print("💡 No relevant matches in database...")
                return self._fallback_to_general_knowledge(user_question, chat_history, "No database matches")
            
            # Format contexts for LLM
            contexts = retrieval_results['contexts'][:15]
            found_ids = []  # Advanced retriever handles this internally
            self.last_method = 'advanced_retrieval'
            
            # STEP 1.5: Apply Organizer if enabled
            if self.use_organizer:
                metadata = {
                    'retrieval_depth': retrieval_results.get('depth', 1),
                    'vector_count': len([c for c in contexts if '[Vector Match]' in c]),
                    'graph_count': len([c for c in contexts if '[Graph' in c]),
                    'method': retrieval_results['method']
                }
                contexts = self.organizer.organize(
                    contexts, 
                    user_question,
                    metadata=metadata,
                    config={
                        'max_contexts': 15,
                        'diversity_threshold': 0.7,
                        'position_strategy': 'important_first'
                    }
                )
            
            graph_context = "\n".join(contexts)
            
        else:
            # BASIC RETRIEVAL: Vector Search Only
            print("📊 Using Basic Vector Retrieval...")
            
            # Find movies with similar themes, plots, and descriptions
            query_vec = self.llm.get_embedding(search_query, task_type="retrieval_query")
            
            if not query_vec:
                return "Sorry, the system is busy and unable to create vectors."

            search_results = self.vectordb.search(query_vec, top_k=8)  # ⚡ Tăng từ 6->8 để có nhiều choices
            
            # RELEVANCE FILTERING: Stricter threshold to reduce noise
            RELEVANCE_THRESHOLD = 0.5  # ⚡ Tăng từ 0.45 -> 0.5 để filter contexts không relevant
          
            
            if search_results:
                relevant_results = []
                for item in search_results:
                    score = item.score if hasattr(item, 'score') else 0
                    if score >= RELEVANCE_THRESHOLD:
                        relevant_results.append(item)
                
                if relevant_results:
                    print(f"  ✓ Found {len(relevant_results)}/{len(search_results)} relevant matches (threshold: {RELEVANCE_THRESHOLD})")
                    search_results = relevant_results
                else:
                    print(f"  ⚠️ No results above relevance threshold ({RELEVANCE_THRESHOLD}) - using general knowledge")
                    search_results = []
            
            if not search_results:
                # If no relevant results, fallback to general knowledge model
                print("💡 No relevant database matches...")
                return self._fallback_to_general_knowledge(user_question, chat_history, "No vector matches above threshold")

            # Extract movie IDs from vector search results
            found_ids = []
            for item in search_results:
                payload = item.payload if hasattr(item, 'payload') else item
                mid = payload.get('movie_id') or payload.get('tmdb_id') or payload.get('id')
                if mid:
                    found_ids.append(mid)
            print(f"✅ Found {len(found_ids)} relevant movies in database")
            self.last_method = 'basic_retrieval'

        # STEP 2: Graph Database Enrichment (Enhanced with Relations)
        # Use IDs to fetch enriched context: director, cast, relationships, genres, themes
        print("🕸️  Enriching with detailed information...")
        
        # Use relation-aware search if relations were detected
        if processed_query['relations']:
            print(f"  → Using relation-aware search: {[r['type'] for r in processed_query['relations']]}")
            # Try relation-aware method if available
            if hasattr(self.graphdb, 'get_relation_aware_context'):
                graph_context = self.graphdb.get_relation_aware_context(
                    found_ids, 
                    processed_query['relations'],
                    processed_query['entities']
                )
            else:
                # Fallback to standard method
                graph_context = self.graphdb.get_graph_context(found_ids)
        else:
            graph_context = self.graphdb.get_graph_context(found_ids)
        
        if not graph_context:
            # Even if graph enrichment fails, use basic vector results
            # Create basic context from the search
            graph_context = "Movies found but detailed info unavailable."
        
        # STEP 2.5: Apply Organizer to basic retrieval results (if enabled)
        if self.use_organizer and not self.use_advanced:
            # Convert graph_context string into list of contexts for organization
            contexts = graph_context.split('\n\n')  # Assuming contexts separated by double newline
            contexts = [c.strip() for c in contexts if c.strip()]
            
            if contexts:
                metadata = {
                    'vector_count': len(found_ids),
                    'graph_count': len(contexts),
                    'method': 'basic_retrieval'
                }
                organized_contexts = self.organizer.organize(
                    contexts,
                    user_question,
                    metadata=metadata,
                    config={
                        'max_contexts': 12,
                        'diversity_threshold': 0.65,
                        'position_strategy': 'important_first'
                    }
                )
                graph_context = "\n\n".join(organized_contexts)

        # STEP 3: LLM Response Generation
        # Synthesize answer with conversational, engaging tone
        print("🤖 Generating thoughtful response...")
        
        # Store contexts for evaluation
        if self.use_advanced:
            # For advanced retrieval, contexts are already in list form
            self.last_contexts = contexts[:15] if contexts else []
        else:
            # For basic retrieval, split graph_context into individual movie contexts
            self.last_contexts = graph_context.split('\n\n') if graph_context else []
        
        # Store movie IDs
        self.last_movies = found_ids if 'found_ids' in locals() else []
        
        # Only mark context as "provided" if we have meaningful graph context
        # This affects how LLM treats the database information
        context_is_relevant = (
            graph_context and 
            graph_context.strip() and 
            "unavailable" not in graph_context.lower() and
            len(graph_context) > 50  # Meaningful context should be substantial
        )
        
        answer = self.llm.generate_answer(
            graph_context, 
            user_question, 
            context_provided=context_is_relevant, 
            chat_history=chat_history
        )
        
        # STEP 3.5: Augmentation Mode - Always combine with general knowledge
        if self.augment_mode and self.fallback_llm:
            print("  🔀 Augmentation mode: Combining database + general knowledge...")
            return self._augment_with_general_knowledge(
                user_question,
                rag_answer=answer,
                rag_contexts=graph_context,
                has_database_context=context_is_relevant
            )
        
        # STEP 3.6: Post-Generation Hallucination Check & Confidence Validation (Fallback mode)
        if context_is_relevant:
            answer = self._validate_answer_grounding(answer, graph_context, user_question)
            
            # Additional check: If answer seems to lack confidence or admits uncertainty
            if self._is_low_confidence_answer(answer):
                print("  ⚠️ Low confidence detected in RAG answer, trying fallback...")
                return self._fallback_to_general_knowledge(
                    user_question, 
                    chat_history, 
                    "Low confidence in RAG answer",
                    rag_answer=answer
                )
        
        return answer
    
    def _is_low_confidence_answer(self, answer: str) -> bool:
        """
        Detect if the answer shows low confidence or uncertainty
        """
        low_confidence_phrases = [
            "i don't",
            "i couldn't",
            "i can't find",
            "no information",
            "not available",
            "unable to find",
            "don't see any",
            "don't have",
            "cannot provide",
            "không có thông tin",
            "không tìm thấy",
            "không rõ",
            "chưa có dữ liệu",
            "không thấy"
        ]
        
        answer_lower = answer.lower()
        for phrase in low_confidence_phrases:
            if phrase in answer_lower:
                return True
        
        # Check if answer is very short (likely uncertain)
        if len(answer.split()) < 15:
            return True
            
        return False
    
    def _fallback_to_general_knowledge(self, question: str, chat_history=None, reason="", rag_answer=None):
        """
        Fallback to general knowledge model when RAG doesn't have sufficient information
        
        Args:
            question: User's question
            chat_history: Conversation history
            reason: Why fallback was triggered
            rag_answer: Previous RAG answer (if any) for reference
        """
        if not self.enable_fallback or not self.fallback_llm:
            # If fallback disabled, return honest admission
            return "I apologize, but I don't have specific information about this in my movie database. Please ask about movies that are available in the system."
        
        print(f"🔄 Switching to fallback model ({reason})...")
        self.last_method = 'fallback_general_knowledge'
        
        # Create enhanced prompt for fallback model
        fallback_prompt = self._create_fallback_prompt(question, rag_answer)
        
        try:
            # Create a system context for general knowledge assistant
            system_context = """You are a knowledgeable AI assistant with expertise in entertainment, movies, actors, directors, and general knowledge.

Your role is to provide accurate, comprehensive answers to user questions. You have broad knowledge about:
- Cinema history and film industry
- Actors, directors, and filmmakers
- Movie franchises and series
- Awards and recognition (Oscars, Golden Globes, etc.)
- General entertainment facts
- And other general knowledge topics

Provide direct, factual answers without mentioning databases or technical limitations."""

            # Combine system context with user question
            full_prompt = f"{system_context}\n\n{fallback_prompt}"
            
            # Use fallback LLM directly via generate_content for custom system role
            answer = self.fallback_llm.model.generate_content(
                full_prompt,
                safety_settings=self.fallback_llm.safety_settings
            ).text
            
            print("✅ Fallback model provided answer")
            return answer
            
        except Exception as e:
            print(f"❌ Fallback model error: {e}")
            return "I apologize, but I'm unable to provide information about this topic at the moment. Please try asking about movies in the database."
    
    def _augment_with_general_knowledge(self, question: str, rag_answer: str, rag_contexts: str, has_database_context: bool):
        """
        Augment RAG answer with general knowledge for comprehensive response
        
        Strategy: Combine database-specific facts with broader context
        """
        if not self.fallback_llm:
            return rag_answer
        
        self.last_method = 'augmented_response'
        
        try:
            # Get general knowledge perspective
            general_knowledge_prompt = f"""Please provide general knowledge context about this question:

"{question}"

Focus on providing factual background, historical context, industry knowledge, or related information that helps understand the topic better. Be concise but informative."""

            system_context = """You are a knowledgeable entertainment and cinema expert. Provide contextual information, background facts, and relevant details to enrich answers about movies, actors, directors, and film industry topics."""

            full_prompt = f"{system_context}\n\n{general_knowledge_prompt}"
            
            general_knowledge = self.fallback_llm.model.generate_content(
                full_prompt,
                safety_settings=self.fallback_llm.safety_settings
            ).text
            
            print(f"  ✓ Got general knowledge context ({len(general_knowledge)} chars)")
            
            # Now synthesize both answers
            synthesis_prompt = f"""You are synthesizing information from two sources to create a comprehensive answer.

USER QUESTION: "{question}"

SOURCE 1 - Database Information (specific to our movie collection):
{rag_answer}

SOURCE 2 - General Knowledge Context:
{general_knowledge}

YOUR TASK:
Create a unified, comprehensive answer that:
1. Prioritizes specific facts from Source 1 (database)
2. Enriches it with relevant context from Source 2 (general knowledge)
3. Maintains factual accuracy - clearly distinguish database facts vs general knowledge
4. Provides a seamless, natural reading experience
5. If sources conflict, trust database (Source 1) for specific movie details

IMPORTANT: Don't mention "sources" or "databases" in your answer. Write naturally as if you have comprehensive knowledge."""

            synthesized_answer = self.llm.model.generate_content(
                synthesis_prompt,
                safety_settings=self.llm.safety_settings
            ).text
            
            print("  ✅ Synthesized augmented answer")
            return synthesized_answer
            
        except Exception as e:
            print(f"  ❌ Augmentation error: {e}, returning RAG answer")
            return rag_answer
    
    def _create_fallback_prompt(self, original_question: str, rag_answer=None) -> str:
        """
        Create an enhanced prompt for the fallback model
        """
        # For low-confidence RAG answers, use pure general knowledge without database context
        # This avoids confusing the model with incomplete database info
        prompt = f"""Please answer this question directly using your general knowledge:

"{original_question}"

Provide a comprehensive, factual answer. Focus on delivering accurate information without mentioning databases or data limitations."""
        
        return prompt
    
    def _validate_answer_grounding(self, answer: str, context: str, question: str) -> str:
        """
        Post-generation validation to catch hallucinations
        Checks if answer contains facts not in context
        """
        # Simple heuristic checks for common hallucination patterns
        hallucination_markers = [
            ('December 2025', context),  # Specific dates
            ('tháng 12/2025', context),
            ('ra rạp', context),
            ('Oscar', context),
            ('thắng giải', context),
            ('đạo diễn hứa', context),
            ('sẽ khám phá', context),  # Future tense speculation
        ]
        
        suspicious_count = 0
        for marker, ctx in hallucination_markers:
            if marker.lower() in answer.lower() and marker.lower() not in ctx.lower():
                suspicious_count += 1
        
        # If multiple suspicious patterns, add disclaimer
        if suspicious_count >= 2:
            print(f"  ⚠️  Detected {suspicious_count} potential hallucinations")
            # Prepend honesty disclaimer
            answer = (
                "*Note: Some information below may need further verification as it's not fully available in the database.*\n\n"
                + answer
            )
        
        return answer
    
    def get_query_stats(self):
        """Get query processing statistics"""
        stats = self.query_processor.get_stats()
        stats['last_method'] = self.last_method
        stats['fallback_enabled'] = self.enable_fallback
        return stats
    
    def clear_query_cache(self):
        """Clear the query cache"""
        self.query_processor.clear_cache()
    
    def get_last_method(self):
        """Get the method used for the last query"""
        return self.last_method

    def close(self):
        self.graphdb.close()