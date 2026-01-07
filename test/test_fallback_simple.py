#!/usr/bin/env python3
"""
Simple test for fallback mechanism without full RAG system
"""

import sys
sys.path.insert(0, '/home/khoi/Code/GRAPH_RAG_MOVIES')

from src.llm_service import GeminiService

print("🧪 Testing Fallback LLM Functionality")
print("=" * 80)

# Initialize fallback LLM
print("\n1. Initializing Fallback LLM...")
fallback_llm = GeminiService()
print("   ✓ Initialized")

# Test questions
questions = [
    "What is the capital of France?",
    "Tell me about Taylor Swift's Grammy awards",
    "Which actors have won Academy Awards in different decades?"
]

for i, question in enumerate(questions, 1):
    print(f"\n{i}. Question: {question}")
    print("   " + "-" * 70)
    
    # Create system context
    system_context = """You are a knowledgeable AI assistant with expertise in entertainment, movies, actors, directors, and general knowledge.

Your role is to provide accurate, comprehensive answers to user questions. You have broad knowledge about:
- Cinema history and film industry
- Actors, directors, and filmmakers
- Movie franchises and series
- Awards and recognition (Oscars, Golden Globes, etc.)
- General entertainment facts
- And other general knowledge topics

Provide direct, factual answers without mentioning databases or technical limitations."""

    fallback_prompt = f"""Please answer this question directly using your general knowledge:

"{question}"

Provide a comprehensive, factual answer. Focus on delivering accurate information without mentioning databases or data limitations."""

    # Combine
    full_prompt = f"{system_context}\n\n{fallback_prompt}"
    
    try:
        # Generate answer
        answer = fallback_llm.model.generate_content(
            full_prompt,
            safety_settings=fallback_llm.safety_settings
        ).text
        
        print(f"   📝 Answer:\n   {answer[:200]}...")
        print(f"   ✅ Success (length: {len(answer)} chars)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ Test complete!")
