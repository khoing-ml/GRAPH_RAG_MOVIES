"""
Manual RAGAS Evaluation - No Library Dependencies
Self-implemented RAGAS metrics using LLM-as-Judge approach
"""

import json
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any
from src.rag_pipeline import GraphRAG
from src.simple_rag import SimpleRAG
from src.llm_service import GeminiService
import os


class ManualRAGASEvaluator:
    """Manual implementation of RAGAS metrics using LLM as judge with enhanced prompting"""
    
    def __init__(self):
        self.llm = GeminiService()
        self.debug_mode = True  # Set to False to hide LLM reasoning
        
        # Simple safety settings for movie content evaluation
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
    def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> tuple[float, str]:
        """
        Call LLM with retry logic and extract score + reasoning
        Returns: (score, reasoning_text)
        """
        import re
        
        for attempt in range(max_retries):
            try:
                response = self.llm.model.generate_content(
                    prompt,
                    safety_settings=self.safety_settings
                )
                text = response.text.strip()
                
                # Extract reasoning and score
                # Expected format: "REASONING: ... SCORE: 0.85"
                if "SCORE:" in text.upper():
                    parts = text.upper().split("SCORE:")
                    reasoning = parts[0].replace("REASONING:", "").strip()
                    score_text = parts[1].strip()
                    numbers = re.findall(r'\b[0-1](?:\.[0-9]+)?\b', score_text)
                    if numbers:
                        score = float(numbers[0])
                        return max(0.0, min(1.0, score)), reasoning
                
                # Fallback: find any number in text
                numbers = re.findall(r'\b[0-1](?:\.[0-9]+)?\b', text)
                if numbers:
                    return max(0.0, min(1.0, float(numbers[0]))), text
                
                # If still no number, try again
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"      ⚠️ Retry {attempt + 1}/{max_retries}: {str(e)[:100]}")
                    time.sleep(1)
                    continue
                else:
                    print(f"      ❌ Failed after {max_retries} attempts: {str(e)[:100]}")
                    return 0.5, f"Error: {str(e)[:100]}"
        
        return 0.5, "Failed to get valid score"
        
    def evaluate_faithfulness(self, answer: str, contexts: List[str]) -> float:
        """
        Faithfulness: Does the answer stay true to the provided context?
        Measures hallucination - answer should only use info from context
        Score: 0-1 (higher is better)
        
        IMPROVED: Chain-of-thought reasoning, claim-by-claim analysis
        """
        prompt = f"""You are an expert evaluator assessing FAITHFULNESS (absence of hallucination) in AI-generated answers.

CONTEXTS PROVIDED TO THE AI:
{self._format_contexts(contexts)}

AI-GENERATED ANSWER:
{answer}

YOUR TASK:
Analyze whether the answer contains ONLY information that can be verified from the provided contexts.

EVALUATION PROCESS (Chain-of-Thought):
1. Break down the answer into individual factual claims
2. For EACH claim, check if it's:
   a) SUPPORTED: Directly stated or clearly implied in contexts
   b) UNSUPPORTED: Not found in contexts (general knowledge, speculation, or hallucination)
3. Count: (supported_claims / total_claims)

EXAMPLES OF ISSUES:
❌ Adding release dates not in context
❌ Mentioning actors/directors not listed in context
❌ Stating box office numbers not provided
❌ Making assumptions about plot details
✅ Only stating what contexts explicitly say

SCORING RUBRIC:
1.0 = Perfect (100% claims supported)
0.9 = Excellent (>90% supported, very minor additions)
0.8 = Good (80-90% supported, some minor general knowledge)
0.7 = Fair (70-80% supported)
0.6 = Mediocre (60-70% supported, noticeable speculation)
0.5 = Poor (50-60% supported)
0.4 = Very Poor (40-50% supported, many unsupported claims)
<0.4 = Critical (majority hallucinated)

FORMAT YOUR RESPONSE:
REASONING: [Your detailed claim-by-claim analysis]
SCORE: [single number 0.0-1.0]"""

        score, reasoning = self._call_llm_with_retry(prompt)
        
        if self.debug_mode:
            print(f"\n    🤖 Faithfulness Reasoning:")
            print(f"    {'-'*80}")
            print(f"    {reasoning[:500]}...")  # Show first 500 chars
            print(f"    Score: {score:.3f}")
            print(f"    {'-'*80}\n")
        
        return score
    
    def evaluate_answer_relevancy(self, question: str, answer: str) -> float:
        """
        Answer Relevancy: How well does the answer address the question?
        Measures if answer is on-topic and helpful
        Score: 0-1 (higher is better)
        
        IMPROVED: Multi-aspect evaluation (directness, completeness, focus)
        """
        prompt = f"""You are an expert evaluator assessing ANSWER RELEVANCY - how well an answer addresses a question.

USER QUESTION:
{question}

AI ANSWER:
{answer}

YOUR TASK:
Evaluate the answer across THREE dimensions:

1. DIRECTNESS (Does it directly address what was asked?)
   - Answers the exact question vs. tangential information
   
2. COMPLETENESS (Does it fully answer the question?)
   - No important aspects left unanswered
   
3. FOCUS (Is it concise and on-topic?)
   - No unnecessary information or rambling

EVALUATION CRITERIA:
✅ RELEVANT: Directly answers the question, stays on topic
✅ COMPLETE: Covers all aspects of the question
✅ FOCUSED: No off-topic tangents or filler
❌ IRRELEVANT: Talks about different topic
❌ INCOMPLETE: Misses key parts of the question
❌ UNFOCUSED: Too much unrelated information

EXAMPLES:
Question: "Who directed Inception?"
Answer: "Christopher Nolan" → 1.0 (perfect)
Answer: "Christopher Nolan directed it in 2010 with Leonardo DiCaprio" → 0.9 (great, slightly verbose)
Answer: "It's a science fiction film about dreams" → 0.2 (doesn't answer)

SCORING RUBRIC:
1.0 = Perfect (directly answers, complete, focused)
0.9 = Excellent (answers well, minimal verbosity)
0.8 = Very Good (answers well but some extra info)
0.7 = Good (answers but missing minor details or slight tangent)
0.6 = Fair (partially answers, some irrelevant content)
0.5 = Mediocre (half relevant, half not)
<0.5 = Poor to terrible (mostly irrelevant)

FORMAT YOUR RESPONSE:
REASONING: [Analyze directness, completeness, and focus]
SCORE: [single number 0.0-1.0]"""

        score, reasoning = self._call_llm_with_retry(prompt)
        
        if self.debug_mode:
            print(f"\n    🎯 Answer Relevancy Reasoning:")
            print(f"    {'-'*80}")
            print(f"    {reasoning[:400]}...")
            print(f"    Score: {score:.3f}")
            print(f"    {'-'*80}\n")
        
        return score
    
    def evaluate_context_precision(self, question: str, contexts: List[str], answer: str) -> float:
        """
        Context Precision: How precise/relevant are the retrieved contexts?
        Measures if contexts are actually useful (low noise)
        Score: 0-1 (higher is better)
        
        IMPROVED: Context-by-context relevance scoring
        """
        prompt = f"""You are an expert evaluator assessing CONTEXT PRECISION - the relevance of retrieved information.

USER QUESTION:
{question}

RETRIEVED CONTEXTS:
{self._format_contexts(contexts)}

FINAL ANSWER GENERATED (for reference):
{answer}

YOUR TASK:
Evaluate each context individually for its relevance to answering the question.

EVALUATION PROCESS:
1. For EACH context, determine:
   • HIGHLY RELEVANT (1.0): Directly helps answer the question
   • SOMEWHAT RELEVANT (0.5): Tangentially related, minor help
   • IRRELEVANT (0.0): Off-topic, different subject entirely

2. Calculate precision: (sum of relevance scores) / (number of contexts)

EXAMPLES:
Question: "Who directed Avatar: Fire and Ash?"
Context 1: "Avatar: Fire and Ash is directed by James Cameron" → HIGHLY RELEVANT (1.0)
Context 2: "Avatar (2009) was also directed by Cameron" → SOMEWHAT RELEVANT (0.5) 
Context 3: "Titanic won 11 Oscars" → IRRELEVANT (0.0)
Precision: (1.0 + 0.5 + 0.0) / 3 = 0.5

BE STRICT:
- Only mark as HIGHLY RELEVANT if it directly addresses the question
- Background/contextual info = SOMEWHAT RELEVANT at best
- Different movie/person = IRRELEVANT

SCORING RUBRIC:
1.0 = All contexts highly relevant (perfect retrieval)
0.8-0.9 = Most contexts relevant, little noise
0.6-0.7 = Mix of relevant and tangential contexts
0.4-0.5 = Half relevant, half noise
<0.4 = Mostly irrelevant contexts (poor retrieval)

FORMAT YOUR RESPONSE:
REASONING: [Evaluate each context individually with scores]
SCORE: [single number 0.0-1.0]"""

        score, reasoning = self._call_llm_with_retry(prompt)
        
        if self.debug_mode:
            print(f"\n    🎯 Context Precision Reasoning:")
            print(f"    {'-'*80}")
            print(f"    {reasoning[:500]}...")
            print(f"    Score: {score:.3f}")
            print(f"    {'-'*80}\n")
        
        return score
    
    def evaluate_context_recall(self, question: str, contexts: List[str], ground_truth: str) -> float:
        """
        Context Recall: Does context contain all needed information?
        Measures if retrieval is complete (not missing important info)
        Score: 0-1 (higher is better)
        
        IMPROVED: Information coverage analysis
        """
        if not ground_truth or ground_truth == "":
            return 1.0  # Skip if no ground truth
        
        prompt = f"""You are an expert evaluator assessing CONTEXT RECALL - completeness of retrieved information.

USER QUESTION:
{question}

IDEAL ANSWER (Ground Truth):
{ground_truth}

RETRIEVED CONTEXTS:
{self._format_contexts(contexts)}

YOUR TASK:
Determine what percentage of the ground truth information can be found in the retrieved contexts.

EVALUATION PROCESS:
1. Identify key facts/information in the ground truth
2. Check which facts are present in the retrieved contexts
3. Calculate: (facts_found_in_contexts / total_facts_in_ground_truth)

EXAMPLES:
Ground Truth: "Inception (2010) directed by Christopher Nolan, starring Leonardo DiCaprio"
Key Facts: [title=Inception, year=2010, director=Nolan, actor=DiCaprio]

Context covers: Inception, 2010, Nolan → 3/4 = 0.75 recall
Context covers: All 4 facts → 1.0 recall
Context covers: Only title → 1/4 = 0.25 recall

SCORING RUBRIC:
1.0 = Perfect (100% ground truth info in contexts)
0.9 = Excellent (>90% coverage, very minor gaps)
0.8 = Very Good (80-90% coverage)
0.7 = Good (70-80% coverage)
0.6 = Fair (60-70% coverage, some gaps)
0.5 = Mediocre (50% coverage, significant gaps)
<0.5 = Poor (majority of information missing)

IMPORTANT:
- Focus on FACTUAL information, not phrasing
- If ground truth mentions 3 actors but contexts have 2, that's partial recall
- Missing information = lower recall

FORMAT YOUR RESPONSE:
REASONING: [List facts from ground truth and check coverage]
SCORE: [single number 0.0-1.0]"""

        score, reasoning = self._call_llm_with_retry(prompt)
        
        if self.debug_mode:
            print(f"\n    🔍 Context Recall Reasoning:")
            print(f"    {'-'*80}")
            print(f"    {reasoning[:500]}...")
            print(f"    Score: {score:.3f}")
            print(f"    {'-'*80}\n")
        
        return score
    
    def evaluate_answer_correctness(self, question: str, answer: str, ground_truth: str) -> float:
        """
        Answer Correctness: Is the answer factually correct?
        Compares answer to ground truth
        Score: 0-1 (higher is better)
        
        IMPROVED: Semantic similarity + factual accuracy
        """
        if not ground_truth or ground_truth == "":
            return 1.0  # Skip if no ground truth
        
        prompt = f"""You are an expert evaluator assessing ANSWER CORRECTNESS - factual accuracy and completeness.

USER QUESTION:
{question}

IDEAL ANSWER (Ground Truth):
{ground_truth}

AI ANSWER TO EVALUATE:
{answer}

YOUR TASK:
Compare the AI answer to the ground truth across TWO dimensions:

1. FACTUAL ACCURACY (Are the facts correct?)
   - Check if stated facts match ground truth
   - Identify any incorrect information
   
2. COMPLETENESS (Is all important info included?)
   - Check if key facts from ground truth are mentioned
   - Minor details can be omitted

EVALUATION CRITERIA:
✅ CORRECT FACTS: Information matches ground truth
✅ COMPLETE: All key information included
✅ SEMANTIC MATCH: Same meaning even if different words
❌ INCORRECT FACTS: Contradicts ground truth
❌ INCOMPLETE: Missing important information
❌ HALLUCINATION: Added facts not in ground truth

EXAMPLES:
Question: "When was Inception released?"
Ground Truth: "2010"
Answer: "2010" → 1.0 (perfect)
Answer: "July 2010" → 1.0 (more specific is fine)
Answer: "2009" → 0.0 (wrong fact)
Answer: "Early 2010s" → 0.7 (close but imprecise)

SCORING RUBRIC:
1.0 = Perfect match (all facts correct, complete)
0.9 = Excellent (correct, minor detail missing)
0.8 = Very Good (correct but less complete)
0.7 = Good (mostly correct, some gaps)
0.6 = Fair (partially correct)
0.5 = Mediocre (half correct, half wrong/missing)
<0.5 = Poor to terrible (mostly incorrect)

IMPORTANT:
- Semantic equivalence counts (e.g., "directed by" vs "director:")
- Extra correct information is OK (doesn't reduce score)
- Wrong information severely reduces score

FORMAT YOUR RESPONSE:
REASONING: [Compare facts and completeness]
SCORE: [single number 0.0-1.0]"""

        score, reasoning = self._call_llm_with_retry(prompt)
        
        if self.debug_mode:
            print(f"\n    ✅ Answer Correctness Reasoning:")
            print(f"    {'-'*80}")
            print(f"    {reasoning[:500]}...")
            print(f"    Score: {score:.3f}")
            print(f"    {'-'*80}\n")
        
        return score
    
    def evaluate_response_completeness(self, question: str, answer: str) -> float:
        """
        Response Completeness: Does the answer feel complete and satisfying?
        NEW METRIC - Measures user satisfaction
        Score: 0-1 (higher is better)
        """
        prompt = f"""You are an expert evaluator assessing RESPONSE COMPLETENESS - user satisfaction.

USER QUESTION:
{question}

AI ANSWER:
{answer}

YOUR TASK:
Evaluate if the answer would satisfy a user's information need.

EVALUATION CRITERIA:
✅ COMPLETE: Provides all expected information
✅ SUFFICIENT DETAIL: Not too brief, not too verbose
✅ ACTIONABLE: User can use this information
✅ CLOSURE: Doesn't leave obvious questions unanswered

❌ INCOMPLETE: Missing obvious information user would want
❌ TOO BRIEF: Bare minimum, unsatisfying
❌ AMBIGUOUS: Leaves user confused
❌ RAISES QUESTIONS: Creates more questions than answers

EXAMPLES:
Question: "Tell me about Inception"
Answer: "A sci-fi film" → 0.2 (way too brief)
Answer: "A 2010 sci-fi thriller directed by Christopher Nolan about dreams" → 0.7 (good but could use more)
Answer: "A 2010 sci-fi thriller by Christopher Nolan starring Leonardo DiCaprio about a team entering dreams. Critically acclaimed." → 1.0 (satisfying)

SCORING RUBRIC:
1.0 = Fully satisfying (user has no follow-up questions)
0.9 = Very complete (minor details could be added)
0.8 = Complete enough (adequate for most users)
0.7 = Mostly complete (one obvious gap)
0.6 = Somewhat incomplete (several gaps)
<0.6 = Unsatisfying (too brief or missing critical info)

FORMAT YOUR RESPONSE:
REASONING: [Evaluate satisfaction and completeness]
SCORE: [single number 0.0-1.0]"""

        score, reasoning = self._call_llm_with_retry(prompt)
        
        if self.debug_mode:
            print(f"\n    📋 Response Completeness Reasoning:")
            print(f"    {'-'*80}")
            print(f"    {reasoning[:400]}...")
            print(f"    Score: {score:.3f}")
            print(f"    {'-'*80}\n")
        
        return score
    
    def evaluate_source_attribution(self, answer: str, contexts: List[str]) -> float:
        """
        Source Attribution: Does answer correctly attribute information?
        NEW METRIC - Measures traceability
        Score: 0-1 (higher is better)
        """
        # Check if answer has any citation markers or source mentions
        has_citations = any(marker in answer.lower() for marker in 
                          ['according to', 'based on', 'from context', 'the context states', 
                           'mentioned', 'as stated', 'source:', '[', ']'])
        
        if not has_citations:
            # If no explicit citations, evaluate implicit attribution
            prompt = f"""You are an expert evaluator assessing SOURCE ATTRIBUTION - traceability of information.

CONTEXTS PROVIDED:
{self._format_contexts(contexts)}

AI ANSWER:
{answer}

YOUR TASK:
Evaluate how well the answer's information can be traced back to specific contexts.

EVALUATION CRITERIA:
✅ EXPLICIT CITATIONS: Answer references sources (e.g., "According to Context 2...")
✅ CLEAR MAPPING: Easy to identify which context each fact came from
✅ SPECIFICITY: Mentions specific details that uniquely identify sources

❌ NO ATTRIBUTION: Generic statements with no clear source
❌ AMBIGUOUS: Can't tell which context provided which fact
❌ MIXED SOURCES: Combines info without clarifying sources

SCORING RUBRIC:
1.0 = Explicit citations for all claims
0.8 = Clear implicit attribution (obvious source for each fact)
0.6 = Partial attribution (some facts traceable)
0.4 = Weak attribution (hard to trace sources)
0.2 = No attribution (generic answer, unclear sources)

NOTE: This measures traceability, not correctness. Even if facts are correct, 
low attribution means user can't verify where info came from.

FORMAT YOUR RESPONSE:
REASONING: [Evaluate traceability and attribution]
SCORE: [single number 0.0-1.0]"""

            score, reasoning = self._call_llm_with_retry(prompt)
            
            if self.debug_mode:
                print(f"\n    🔗 Source Attribution Reasoning:")
                print(f"    {'-'*80}")
                print(f"    {reasoning[:400]}...")
                print(f"    Score: {score:.3f}")
                print(f"    {'-'*80}\n")
            
            return score
        else:
            # Has explicit citations - give high score
            return 0.9  # Not perfect 1.0 unless citations are very systematic
    
    def _format_contexts(self, contexts: List[str]) -> str:
        """
        Format contexts for prompt - improved clarity and structure
        """
        if not contexts:
            return "[No contexts provided]"
        
        formatted = []
        # Format ALL contexts - don't hide any to avoid faithfulness issues
        for i, ctx in enumerate(contexts, 1):
            # Clean and truncate context - INCREASED to preserve director/cast info
            ctx_clean = ctx.strip()[:3000]  # Increased from 1200 to 3000 to include full context
            
            # Add clear separators
            formatted.append(f"""
--- CONTEXT {i} ---
{ctx_clean}
--- END CONTEXT {i} ---""")
        
        return "\n".join(formatted)
    
    def evaluate_single(self, question: str, answer: str, contexts: List[str], ground_truth: str = "") -> Dict:
        """Evaluate a single Q&A with all metrics"""
        print(f"    → Evaluating: {question[:50]}...")
        
        # 🔍 PRINT FULL ANSWER TO DEBUG FAITHFULNESS
        print(f"\n    📝 FULL ANSWER:")
        print(f"    {'-'*80}")
        print(f"    {answer}")
        print(f"    {'-'*80}")
        print(f"\n    📚 CONTEXTS ({len(contexts)} total):")
        # Show ALL contexts for transparency
        for i, ctx in enumerate(contexts, 1):
            # Show FULL context without truncation
            print(f"       {i}. {ctx}")
            print(f"          {'-'*70}")
        print()
        
        metrics = {}
        
        # Faithfulness
        print(f"      • Faithfulness...", end="")
        metrics['faithfulness'] = self.evaluate_faithfulness(answer, contexts)
        print(f" {metrics['faithfulness']:.3f}")
        time.sleep(0.5)
        
        # Answer Relevancy
        print(f"      • Answer Relevancy...", end="")
        metrics['answer_relevancy'] = self.evaluate_answer_relevancy(question, answer)
        print(f" {metrics['answer_relevancy']:.3f}")
        time.sleep(0.5)
        
        # Context Precision
        print(f"      • Context Precision...", end="")
        metrics['context_precision'] = self.evaluate_context_precision(question, contexts, answer)
        print(f" {metrics['context_precision']:.3f}")
        time.sleep(0.5)
        
        # Context Recall
        print(f"      • Context Recall...", end="")
        metrics['context_recall'] = self.evaluate_context_recall(question, contexts, ground_truth)
        print(f" {metrics['context_recall']:.3f}")
        time.sleep(0.5)
        
        # Answer Correctness
        print(f"      • Answer Correctness...", end="")
        metrics['answer_correctness'] = self.evaluate_answer_correctness(question, answer, ground_truth)
        print(f" {metrics['answer_correctness']:.3f}")
        time.sleep(0.5)
        
        # Overall score (weighted average - prioritize key metrics)
        weights = {
            'faithfulness': 1.5,          # Critical - no hallucination
            'answer_relevancy': 1.5,      # Critical - answers the question
            'answer_correctness': 1.5,    # Critical - factually correct
            'context_precision': 1.0,     # Important - quality retrieval
            'context_recall': 1.0         # Important - complete retrieval
        }
        
        weighted_sum = sum(metrics.get(k, 0) * w for k, w in weights.items())
        total_weight = sum(weights.values())
        metrics['overall_weighted'] = weighted_sum / total_weight
        metrics['overall_simple'] = sum(metrics.values()) / len(metrics)  # Simple average for comparison
        
        print(f"\n      ⭐ Overall Score (weighted): {metrics['overall_weighted']:.3f}")
        print(f"      ⭐ Overall Score (simple): {metrics['overall_simple']:.3f}")
        
        return metrics


class ManualComparisonEvaluator:
    """Compare GraphRAG vs SimpleRAG using manual RAGAS"""
    
    def __init__(self, graphrag, simplerag):
        self.graphrag = graphrag
        self.simplerag = simplerag
        self.evaluator = ManualRAGASEvaluator()
        self.results = []
    
    def query_with_context(self, rag_system, question: str) -> tuple:
        """Query RAG and capture contexts - USE ACTUAL CONTEXTS from RAG system"""
        # Query the system
        answer = rag_system.query(question)
        
        # Check if fallback was used (for GraphRAG)
        if hasattr(rag_system, 'last_method'):
            method = rag_system.last_method
            if method == 'fallback_general_knowledge':
                print(f"  🌐 Fallback triggered: Used general knowledge (no database context)")
            elif method:
                print(f"  📊 Method: {method}")
        
        # Get actual contexts used by the RAG system
        if hasattr(rag_system, 'last_contexts') and rag_system.last_contexts:
            contexts = rag_system.last_contexts[:10]  # Limit to 10 for token efficiency
            print(f"  ✓ Captured {len(contexts)} actual contexts from RAG system")
        else:
            # Fallback: extract contexts manually (old method)
            print(f"  ⚠️  Using fallback context extraction")
            contexts = []
            if hasattr(rag_system, 'vectordb'):
                query_vec = rag_system.llm.get_embedding(question, task_type="retrieval_query")
                if query_vec:
                    search_results = rag_system.vectordb.search(query_vec, top_k=10)
                    for item in search_results:
                        if hasattr(item, 'payload') and item.payload:
                            text_parts = []
                            
                            # Title
                            if 'title' in item.payload:
                                text_parts.append(f"Title: {item.payload['title']}")
                            
                            # Directors (plural) - CRITICAL FIX
                            if 'directors' in item.payload:
                                directors_list = item.payload['directors']
                                if directors_list:
                                    text_parts.append(f"Director: {', '.join(directors_list)}")
                            elif 'director' in item.payload:  # Fallback for singular
                                text_parts.append(f"Director: {item.payload['director']}")
                            
                            # Cast - CRITICAL FIX
                            if 'cast' in item.payload:
                                cast_list = item.payload['cast']
                                if cast_list:
                                    text_parts.append(f"Cast: {', '.join(cast_list[:8])}")
                            
                            # Overview
                            if 'overview' in item.payload:
                                text_parts.append(f"Overview: {item.payload['overview']}")
                            
                            # Genres
                            if 'genres' in item.payload:
                                text_parts.append(f"Genres: {item.payload['genres']}")
                            
                            if text_parts:
                                contexts.append(" | ".join(text_parts))
        
        if not contexts:
            contexts = [answer[:200]]  # Ultimate fallback
        
        return answer, contexts
    
    def evaluate_query(self, query_data: Dict):
        """Evaluate one query on both systems"""
        question = query_data['query']
        ground_truth = query_data.get('ground_truth', '')
        
        print(f"\n[Query {query_data.get('id', '?')}] {question}")
        print(f"Category: {query_data.get('category', 'unknown')}")
        
        # Evaluate GraphRAG
        print(f"\n  🔷 GraphRAG:")
        graphrag_answer, graphrag_contexts = self.query_with_context(self.graphrag, question)
        graphrag_metrics = self.evaluator.evaluate_single(
            question, graphrag_answer, graphrag_contexts, ground_truth
        )
        
        time.sleep(1)
        
        # Evaluate SimpleRAG
        print(f"\n  🔶 SimpleRAG:")
        simplerag_answer, simplerag_contexts = self.query_with_context(self.simplerag, question)
        simplerag_metrics = self.evaluator.evaluate_single(
            question, simplerag_answer, simplerag_contexts, ground_truth
        )
        
        # Store results
        # Use weighted score for winner determination
        graphrag_score = graphrag_metrics.get('overall_weighted', graphrag_metrics.get('overall_simple', 0))
        simplerag_score = simplerag_metrics.get('overall_weighted', simplerag_metrics.get('overall_simple', 0))
        
        # Track fallback usage
        graphrag_method = getattr(self.graphrag, 'last_method', 'unknown')
        used_fallback = (graphrag_method == 'fallback_general_knowledge')
        
        result = {
            'query_id': query_data.get('id', 'unknown'),
            'question': question,
            'category': query_data.get('category', 'unknown'),
            'complexity': query_data.get('complexity', 'unknown'),
            'ground_truth': ground_truth,
            'graphrag': {
                'answer': graphrag_answer,
                'contexts_count': len(graphrag_contexts),
                'metrics': graphrag_metrics,
                'method': graphrag_method,
                'used_fallback': used_fallback
            },
            'simplerag': {
                'answer': simplerag_answer,
                'contexts_count': len(simplerag_contexts),
                'metrics': simplerag_metrics
            },
            'winner': 'GraphRAG' if graphrag_score > simplerag_score else 'SimpleRAG'
        }
        
        self.results.append(result)
        
        # Print comparison with both scores
        print(f"\n  📊 Comparison:")
        print(f"    GraphRAG Overall (weighted): {graphrag_score:.3f}")
        print(f"    SimpleRAG Overall (weighted): {simplerag_score:.3f}")
        if 'overall_simple' in graphrag_metrics:
            print(f"    GraphRAG Overall (simple): {graphrag_metrics['overall_simple']:.3f}")
            print(f"    SimpleRAG Overall (simple): {simplerag_metrics['overall_simple']:.3f}")
        print(f"    🏆 Winner: {result['winner']}")
        
        return result
    
    def generate_report(self, output_file: str = None):
        """Generate comparison report"""
        if not self.results:
            print("No results to report")
            return
        
        # Aggregate metrics (5 core RAGAS metrics)
        metric_names = [
            'faithfulness', 
            'answer_relevancy', 
            'context_precision', 
            'context_recall', 
            'answer_correctness',
            'overall_weighted',
            'overall_simple'
        ]
        
        graphrag_metrics = {name: [] for name in metric_names}
        simplerag_metrics = {name: [] for name in metric_names}
        
        for result in self.results:
            for metric in metric_names:
                # Handle missing metrics gracefully
                g_val = result['graphrag']['metrics'].get(metric, 0)
                s_val = result['simplerag']['metrics'].get(metric, 0)
                graphrag_metrics[metric].append(g_val)
                simplerag_metrics[metric].append(s_val)
        
        # Calculate averages
        graphrag_avg = {k: sum(v)/len(v) if v else 0 for k, v in graphrag_metrics.items()}
        simplerag_avg = {k: sum(v)/len(v) if v else 0 for k, v in simplerag_metrics.items()}
        
        # Calculate fallback statistics
        fallback_count = sum(1 for r in self.results if r['graphrag'].get('used_fallback', False))
        fallback_percentage = (fallback_count / len(self.results) * 100) if self.results else 0
        
        # Build report
        report = {
            'metadata': {
                'evaluation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_queries': len(self.results),
                'method': 'Manual RAGAS Implementation (LLM-as-Judge)',
                'metrics_count': 5,
                'fallback_enabled': True,
                'fallback_triggered': fallback_count,
                'fallback_percentage': f"{fallback_percentage:.1f}%"
            },
            'graphrag_metrics': graphrag_avg,
            'simplerag_metrics': simplerag_avg,
            'improvements': {
                metric: ((graphrag_avg[metric] - simplerag_avg[metric]) / simplerag_avg[metric] * 100)
                if simplerag_avg[metric] > 0 else 0
                for metric in metric_names
            },
            'detailed_results': self.results
        }
        
        # Save report
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'manual_ragas_report_{timestamp}.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print("🔬 MANUAL RAGAS EVALUATION REPORT (Enhanced v2.0)")
        print(f"{'='*80}\n")
        
        print(f"{'Metric':<30} {'GraphRAG':<15} {'SimpleRAG':<15} {'Improvement':<15}")
        print(f"{'-'*80}")
        
        # Core metrics
        print("📊 Core Metrics:")
        for metric in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'answer_correctness']:
            g_val = graphrag_avg[metric]
            s_val = simplerag_avg[metric]
            imp = report['improvements'][metric]
            
            print(f"  {metric:<28} {g_val:<15.4f} {s_val:<15.4f} {imp:+.2f}%")
        
        # Overall scores
        print("\n⭐ Overall Scores:")
        for metric in ['overall_weighted', 'overall_simple']:
            g_val = graphrag_avg[metric]
            s_val = simplerag_avg[metric]
            imp = report['improvements'][metric]
            
            print(f"  {metric:<28} {g_val:<15.4f} {s_val:<15.4f} {imp:+.2f}%")
        
        # Fallback statistics
        if fallback_count > 0:
            print(f"\n🌐 Fallback Statistics:")
            print(f"  Fallback triggered: {fallback_count}/{len(self.results)} queries ({fallback_percentage:.1f}%)")
            print(f"  Queries that used general knowledge:")
            for r in self.results:
                if r['graphrag'].get('used_fallback', False):
                    print(f"    • Q{r['query_id']}: {r['question'][:60]}...")
        
        print(f"\n✓ Report saved to: {output_file}")
        print(f"{'='*80}\n")
        
        return report


def list_available_datasets(datasets_dir='test_datasets'):
    """List all available dataset files"""
    import os
    import glob
    
    if not os.path.exists(datasets_dir):
        print(f"⚠️ Datasets directory not found: {datasets_dir}")
        return []
    
    dataset_files = glob.glob(os.path.join(datasets_dir, '*.json'))
    return sorted([os.path.basename(f) for f in dataset_files])


def load_test_dataset(dataset_name=None, datasets_dir='test_datasets', max_queries=None):
    """
    Load test queries from dataset(s)
    
    Args:
        dataset_name: Name of dataset file (e.g., 'actor_based.json') or 'all' for all datasets
        datasets_dir: Directory containing datasets
        max_queries: Maximum number of queries to load per dataset (None = all)
    
    Returns:
        List of query dictionaries with metadata
    """
    import os
    
    if dataset_name == 'all':
        # Load all datasets
        available = list_available_datasets(datasets_dir)
        if not available:
            print(f"⚠️ No datasets found in {datasets_dir}/")
            return []
        
        print(f"\n📚 Loading ALL datasets ({len(available)} total):")
        all_queries = []
        
        for dataset_file in available:
            queries = load_single_dataset(
                os.path.join(datasets_dir, dataset_file), 
                max_queries
            )
            all_queries.extend(queries)
            print(f"   ✓ {dataset_file}: {len(queries)} queries")
        
        print(f"\n✅ Total loaded: {len(all_queries)} queries")
        return all_queries
    
    else:
        # Load single dataset
        if dataset_name is None:
            # Show available datasets and prompt user
            available = list_available_datasets(datasets_dir)
            if not available:
                print(f"⚠️ No datasets found in {datasets_dir}/")
                return []
            
            print(f"\n📚 Available datasets:")
            for i, name in enumerate(available, 1):
                print(f"   {i}. {name}")
            
            print(f"\n💡 Use: --dataset <name> or --dataset all")
            return []
        
        filepath = os.path.join(datasets_dir, dataset_name)
        queries = load_single_dataset(filepath, max_queries)
        
        if queries:
            print(f"✓ Loaded {len(queries)} queries from {dataset_name}")
        
        return queries


def load_single_dataset(filepath, max_queries=None):
    """Load a single dataset file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different dataset formats
        if 'test_cases' in data:
            # New format (test_datasets/)
            queries = data['test_cases']
            category = data.get('category', 'unknown')
            description = data.get('description', '')
            
            # Add metadata to each query
            for q in queries:
                q['category'] = category
                q['dataset_description'] = description
                # Ensure ground_truth field exists
                if 'ground_truth' not in q:
                    q['ground_truth'] = ''
        
        elif 'test_queries' in data:
            # Old format
            queries = data['test_queries']
        
        else:
            print(f"⚠️ Unknown dataset format: {filepath}")
            return []
        
        # Limit queries if specified
        if max_queries is not None and max_queries > 0:
            queries = queries[:max_queries]
        
        return queries
        
    except FileNotFoundError:
        print(f"⚠️ Error: {filepath} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"⚠️ Error parsing JSON in {filepath}: {e}")
        return []


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Manual RAGAS Evaluation - GraphRAG vs SimpleRAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available datasets
  python manual_ragas_evaluation.py
  
  # Evaluate on actor-based queries (first 5)
  python manual_ragas_evaluation.py --dataset actor_based.json --num 5
  
  # Evaluate on all comparison queries
  python manual_ragas_evaluation.py --dataset comparison.json
  
  # Evaluate on ALL datasets (first 3 queries each)
  python manual_ragas_evaluation.py --dataset all --num 3
        """
    )
    parser.add_argument('--num', '-n', type=int, default=None, 
                       help='Number of queries to evaluate per dataset (default: all)')
    parser.add_argument('--dataset', '-d', type=str, default=None, 
                       help='Dataset to use (filename or "all" for all datasets)')
    parser.add_argument('--datasets-dir', type=str, default='test_datasets',
                       help='Directory containing datasets (default: test_datasets)')
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print("🔬 Manual RAGAS Evaluation")
    print("GraphRAG vs SimpleRAG Comparison with LLM-as-Judge (5 Core Metrics)")
    print(f"{'='*80}\n")
    
    # Load dataset
    queries = load_test_dataset(
        dataset_name=args.dataset, 
        datasets_dir=args.datasets_dir,
        max_queries=args.num
    )
    
    if not queries:
        print("\n❌ No queries to evaluate")
        print("\n💡 Available datasets:")
        available = list_available_datasets(args.datasets_dir)
        for i, name in enumerate(available, 1):
            print(f"   {i}. {name}")
        print("\n📖 Usage examples:")
        print("   python manual_ragas_evaluation.py --dataset actor_based.json")
        print("   python manual_ragas_evaluation.py --dataset all --num 3")
        return
    
    print(f"\n📊 Evaluation Plan:")
    print(f"   • Total queries: {len(queries)}")
    
    # Show category breakdown
    categories = {}
    for q in queries:
        cat = q.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    if len(categories) > 1:
        print(f"   • Categories:")
        for cat, count in sorted(categories.items()):
            print(f"      - {cat}: {count} queries")
    else:
        cat_name = list(categories.keys())[0] if categories else 'unknown'
        print(f"   • Category: {cat_name}")
    
    print(f"   • Metrics: 5 (core RAGAS)")
    print(f"   • Estimated time: ~{len(queries) * 2} minutes\n")
    
    # Confirm before proceeding
    if len(queries) > 10:
        confirm = input(f"⚠️  This will evaluate {len(queries)} queries. Continue? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Evaluation cancelled")
            return
    
    # Initialize systems
    print("\n🚀 Initializing RAG systems...")
    graphrag = GraphRAG(enable_fallback=True)  # Enable fallback for general knowledge
    simplerag = SimpleRAG()
    print("✓ Systems ready (with fallback mechanism)\n")
    
    # Create evaluator
    evaluator = ManualComparisonEvaluator(graphrag, simplerag)
    
    # Evaluate queries with progress tracking
    print(f"{'='*80}")
    print("📊 STARTING EVALUATION")
    print(f"{'='*80}\n")
    
    for i, query_data in enumerate(queries, 1):
        print(f"\n{'─'*80}")
        print(f"Query {i}/{len(queries)}")
        
        # Show query details
        if 'category' in query_data:
            print(f"Category: {query_data['category']}")
        if 'complexity' in query_data:
            print(f"Complexity: {query_data['complexity']}")
        
        print(f"{'─'*80}")
        
        try:
            evaluator.evaluate_query(query_data)
        except Exception as e:
            print(f"\n❌ Error evaluating query {i}: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            continue
        
        # Progress update
        if i < len(queries):
            print(f"\n⏳ Progress: {i}/{len(queries)} completed ({i/len(queries)*100:.1f}%)")
        
        time.sleep(2)  # Rate limiting between queries
    
    # Generate report with custom filename
    print(f"\n{'='*80}")
    print("📈 GENERATING FINAL REPORT")
    print(f"{'='*80}\n")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dataset_suffix = args.dataset.replace('.json', '') if args.dataset and args.dataset != 'all' else 'all'
    output_file = f'manual_ragas_report_{dataset_suffix}_{timestamp}.json'
    
    report = evaluator.generate_report(output_file)
    
    print(f"\n✅ Evaluation complete!")
    print(f"📁 Report saved: {output_file}")
    print(f"📊 Queries evaluated: {len(queries)}")
    
    # Show quick summary
    if report:
        print(f"\n📈 Quick Summary:")
        graphrag_overall = report['graphrag_metrics'].get('overall_weighted', report['graphrag_metrics'].get('overall_simple', 0))
        simplerag_overall = report['simplerag_metrics'].get('overall_weighted', report['simplerag_metrics'].get('overall_simple', 0))
        winner = "GraphRAG 🏆" if graphrag_overall > simplerag_overall else "SimpleRAG 🏆"
        print(f"   • GraphRAG: {graphrag_overall:.3f}")
        print(f"   • SimpleRAG: {simplerag_overall:.3f}")
        print(f"   • Winner: {winner}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
