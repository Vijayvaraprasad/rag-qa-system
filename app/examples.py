"""
EXAMPLE USAGE PATTERNS
Real-world examples of using all advanced features
"""

# ============================================================================
# EXAMPLE 1: Simple FAQ System
# ============================================================================

from app.caching import SmartCache
from app.adaptive_thresholds import AdaptiveThreshold

def simple_faq_system():
    """
    Use case: Website FAQ - same questions asked many times
    Goal: Fast, cheap, reliable answers
    """
    cache = SmartCache()
    
    # User asks: "What is your return policy?"
    question = "What is your return policy?"
    
    # Check cache first (instant!)
    cached = cache.get_answer_with_cache(question)
    if cached:
        return {
            "answer": cached["answer"],
            "source": "cache",
            "speed": "instant"
        }
    
    # Not in cache, use system
    # Get adaptive threshold
    threshold_info = AdaptiveThreshold.get_threshold_for_question(question)
    # Simple question → strict threshold (0.80) → fewer candidates
    
    # ... retrieve, rank, generate answer ...
    
    # Cache for next time
    answer = "Within 30 days of purchase..."
    cache.cache.set(question, answer)
    
    # Record if user was happy
    # Could be automatic or explicit feedback
    cache.feedback.add_feedback(
        question=question,
        answer=answer,
        rating=5,  # User satisfied!
        comment="Helpful and clear"
    )
    
    return {
        "answer": answer,
        "source": "generated",
        "cached_for_next_time": True
    }


# ============================================================================
# EXAMPLE 2: Technical Research Paper Analysis
# ============================================================================

from app.multi_hop_retrieval import MultiHopRetriever
from app.query_expansion import expand_query
from app.knowledge_graph import KnowledgeGraph

def research_paper_analysis():
    """
    Use case: Analyzing machine learning research papers
    Goal: Find connections between concepts
    """
    
    question = """
    How do attention mechanisms in transformers relate to 
    biological neural attention in the brain?
    """
    
    # Step 1: Expand query to capture all aspects
    expanded = expand_query(question, num_expansions=3)
    # ["original question", "attention mechanisms transformers",
    #  "biological neural attention", "comparison brain ML"]
    
    # Step 2: Multi-hop retrieval
    retriever = MultiHopRetriever(max_hops=3)
    result = retriever.multi_hop_retrieve(question, num_hops=2)
    
    # Hop 1: Find papers on attention mechanisms
    # Hop 2: Find papers on biological inspiration
    
    # Step 3: Build knowledge graph from retrieved papers
    kg = KnowledgeGraph()
    for chunk in result["all_chunks"]:
        kg.add_document(chunk, source="research_papers")
    
    # Step 4: Find connections
    entities = kg.find_related_entities("attention mechanism")
    connections = kg.find_path_between_entities("attention", "neural_biology")
    
    return {
        "chunks_found": result["total_chunks"],
        "hops_performed": result["hops_performed"],
        "related_concepts": entities["related_entities"],
        "connection_path": connections,
        "knowledge_summary": kg.get_graph_summary()
    }


# ============================================================================
# EXAMPLE 3: Legal Document Analysis
# ============================================================================

from app.answer_verification import verify_and_fallback
from app.context_compression import compress_context

def legal_document_analysis():
    """
    Use case: Contract review
    Goal: NO hallucinations, accuracy critical, cost matters
    """
    
    question = "What are the liability limitations in this agreement?"
    
    # Use hybrid search to catch ALL mentions
    from app.hybrid_search import HybridSearcher
    searcher = HybridSearcher()
    hybrid_results = searcher.hybrid_search(question, top_k=10)
    candidates = [chunk for chunk, _ in hybrid_results]
    
    # Rerank
    from app.rerank import rerank
    ranked = rerank(question, candidates, top_n=3)
    context = "\n".join(ranked)
    
    # Generate answer
    from app.llm import generate_answer
    answer = generate_answer(context, question)
    
    # CRITICAL: Verify answer is in context
    final_answer, verification = verify_and_fallback(
        answer, context, question, threshold=0.7  # High threshold!
    )
    
    if not verification["is_grounded"]:
        # Not confident - tell user to review manually
        return {
            "answer": "Please review original contract",
            "reason": "Could not verify answer in provided context",
            "confidence": verification["confidence"],
            "recommendation": "Manual review required for legal accuracy"
        }
    
    # Compress context for clarity
    compressed = compress_context(context, question)
    
    return {
        "answer": final_answer,
        "verified": True,
        "confidence": verification["confidence"],
        "relevant_sections": compressed,
        "safe_to_use": True
    }


# ============================================================================
# EXAMPLE 4: Real-time Knowledge Base with Cost Optimization
# ============================================================================

from app.context_compression import estimate_token_savings
from app.local_llm import FallbackLLM

def cost_optimized_qa():
    """
    Use case: High-volume Q&A system
    Goal: Minimize API costs while maintaining quality
    """
    
    question = "What are the system requirements?"
    
    # Use all cost-saving strategies:
    
    # 1. Compress context (80% cost reduction)
    from app.retrieval import retrieve_candidates
    from app.rerank import rerank
    
    candidates = retrieve_candidates(question)
    ranked = rerank(question, candidates)
    context = "\n".join(ranked)
    
    from app.context_compression import compress_context
    compressed_context = compress_context(context, question, strategy="extract")
    savings = estimate_token_savings(context, compressed_context)
    
    print(f"💰 Cost reduction: {savings['savings_percent']}%")
    print(f"   Original: {savings['original_tokens']} tokens")
    print(f"   Compressed: {savings['compressed_tokens']} tokens")
    
    # 2. Use local LLM (FREE!)
    llm = FallbackLLM(use_openai_fallback=True)
    result = llm.generate(
        prompt=f"Context: {compressed_context}\n\nQuestion: {question}\n\nAnswer:",
        temperature=0.2
    )
    
    if result["is_local"]:
        print(f"✅ Using {result['model']} (FREE)")
    else:
        print(f"⚠️ Fell back to {result['model']} ($.03/1K tokens)")
    
    return {
        "answer": result["response"],
        "model_used": result["model"],
        "cost_optimizations": {
            "compression": f"{savings['savings_percent']}% reduction",
            "local_llm": result["is_local"]
        }
    }


# ============================================================================
# EXAMPLE 5: Multi-Strategy Comparison
# ============================================================================

def compare_retrieval_strategies():
    """
    Use case: Testing which strategy works best for your domain
    Goal: Understand performance differences
    """
    
    question = "How does machine learning work?"
    
    from app.retrieval import retrieve_candidates
    from app.rerank import rerank
    from app.llm import generate_answer
    from app.hybrid_search import HybridSearcher
    from app.multi_hop_retrieval import MultiHopRetriever
    
    results = {}
    
    # Strategy 1: Standard Semantic Search
    candidates_semantic = retrieve_candidates(question)
    ranked_semantic = rerank(question, candidates_semantic, top_n=3)
    context_semantic = "\n".join(ranked_semantic)
    answer_semantic = generate_answer(context_semantic, question)
    results["semantic"] = {
        "chunks_found": len(candidates_semantic),
        "answer_length": len(answer_semantic),
        "answer_preview": answer_semantic[:100]
    }
    
    # Strategy 2: Hybrid Search
    searcher = HybridSearcher()
    hybrid_results = searcher.hybrid_search(question, top_k=8)
    candidates_hybrid = [chunk for chunk, _ in hybrid_results]
    ranked_hybrid = rerank(question, candidates_hybrid, top_n=3)
    context_hybrid = "\n".join(ranked_hybrid)
    answer_hybrid = generate_answer(context_hybrid, question)
    results["hybrid"] = {
        "chunks_found": len(candidates_hybrid),
        "answer_length": len(answer_hybrid),
        "answer_preview": answer_hybrid[:100]
    }
    
    # Strategy 3: Multi-Hop Retrieval
    multi_hop = MultiHopRetriever()
    multi_hop_result = multi_hop.multi_hop_retrieve(question, num_hops=2)
    candidates_multi = multi_hop_result["all_chunks"][:8]
    ranked_multi = rerank(question, candidates_multi, top_n=3)
    context_multi = "\n".join(ranked_multi)
    answer_multi = generate_answer(context_multi, question)
    results["multi_hop"] = {
        "chunks_found": len(candidates_multi),
        "hops": multi_hop_result["hops_performed"],
        "answer_length": len(answer_multi),
        "answer_preview": answer_multi[:100]
    }
    
    # Compare results
    return {
        "question": question,
        "strategies_compared": results,
        "recommendation": "Compare answer quality and choose best strategy"
    }


# ============================================================================
# EXAMPLE 6: Learning System with Feedback Loop
# ============================================================================

def learning_system():
    """
    Use case: System that improves over time
    Goal: Track what works and don't repeat mistakes
    """
    
    from app.caching import SmartCache
    
    cache = SmartCache()
    
    questions_batch = [
        "What is AI?",
        "Explain machine learning",
        "How do neural networks work?",
        "What is deep learning?"
    ]
    
    for question in questions_batch:
        # 1. Try cached answer first
        cached = cache.get_answer_with_cache(question)
        if cached:
            answer = cached["answer"]
            print(f"✓ Cache hit for: {question}")
        else:
            # 2. Generate new answer
            # ... retrieval + generation ...
            answer = "Generated answer..."
            cache.cache.set(question, answer)
            print(f"• New answer for: {question}")
        
        # 3. Simulate user feedback
        user_satisfaction = 5  # 1-5 stars
        cache.feedback.add_feedback(
            question=question,
            answer=answer,
            rating=user_satisfaction
        )
    
    # 4. Analyze what worked
    summary = cache.feedback.get_feedback_summary()
    print(f"\n📊 Performance Summary:")
    print(f"   Average rating: {summary['avg_rating']:.1f}/5")
    print(f"   Total feedback: {summary['total_feedback']}")
    print(f"   Excellent answers: {summary['excellent']}")
    print(f"   Poor answers: {summary['poor']}")
    
    # 5. Find and fix poor answers
    poor_answers = cache.feedback.get_low_rated_answers(threshold=2)
    if poor_answers:
        print(f"\n⚠️  Found {len(poor_answers)} poorly-rated answers")
        print("   Actions: Improve retrieval, adjust ranking, etc.")
    
    # 6. Cache stats
    cache_stats = cache.cache.get_cache_stats()
    print(f"\n💾 Cache Performance:")
    print(f"   Cached questions: {cache_stats['total_cached_questions']}")
    print(f"   Total cache hits: {cache_stats['total_cache_hits']}")
    print(f"   Efficiency: {cache_stats['avg_hits_per_question']:.1f} hits/question")
    
    return {
        "feedback_summary": summary,
        "cache_performance": cache_stats,
        "improvement_areas": [q for q in poor_answers]
    }


# ============================================================================
# EXAMPLE 7: Enterprise Knowledge Assistant
# ============================================================================

def enterprise_assistant():
    """
    Use case: Company knowledge base (HR, IT, Finance docs)
    Goal: Accurate, fast, comprehensive answers
    """
    
    from app.metadata_filter import MetadataFilter
    from app.knowledge_graph import KnowledgeGraph
    from app.few_shot import CustomFewShotExamples
    
    question = "What is the employee vacation policy?"
    
    # 1. Filter by source (only official docs, not comments)
    source_filter = MetadataFilter.source_filter(["official_policies"])
    
    # 2. Filter by date (only recent updates)
    date_filter = MetadataFilter.date_range_filter("2024-01-01", "2026-12-31")
    
    # Combine filters
    combined = MetadataFilter.combine_filters(source_filter, date_filter)
    # Use in retrieval: results = query_with_filter(combined)
    
    # 3. Use few-shot examples for HR questions
    custom_examples = CustomFewShotExamples()
    prompt = custom_examples.build_custom_prompt(
        category="HR_policies",
        question=question,
        context="..."  # Retrieved context
    )
    
    # 4. Build knowledge graph of policies
    kg = KnowledgeGraph()
    # Add all policy documents during ingestion
    # Now can query relationships:
    related = kg.find_related_entities("vacation_policy")
    
    return {
        "answer": "The vacation policy is...",
        "metadata_filters_applied": {
            "source": "official_policies",
            "date_range": "2024-2026"
        },
        "related_policies": related["related_entities"],
        "source_documents": "3 official policy documents"
    }


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ADVANCED RAG SYSTEM - USAGE EXAMPLES")
    print("=" * 70)
    
    print("\n1️⃣  FAQ System Example")
    print("-" * 70)
    # Uncomment to run: simple_faq_system()
    print("See simple_faq_system() function")
    
    print("\n2️⃣  Research Paper Analysis Example")
    print("-" * 70)
    # Uncomment to run: research_paper_analysis()
    print("See research_paper_analysis() function")
    
    print("\n3️⃣  Legal Document Analysis Example")
    print("-" * 70)
    # Uncomment to run: legal_document_analysis()
    print("See legal_document_analysis() function")
    
    print("\n4️⃣  Cost Optimized QA Example")
    print("-" * 70)
    # Uncomment to run: cost_optimized_qa()
    print("See cost_optimized_qa() function")
    
    print("\n5️⃣  Strategy Comparison Example")
    print("-" * 70)
    # Uncomment to run: compare_retrieval_strategies()
    print("See compare_retrieval_strategies() function")
    
    print("\n6️⃣  Learning System Example")
    print("-" * 70)
    # Uncomment to run: learning_system()
    print("See learning_system() function")
    
    print("\n7️⃣  Enterprise Assistant Example")
    print("-" * 70)
    # Uncomment to run: enterprise_assistant()
    print("See enterprise_assistant() function")
    
    print("\n" + "=" * 70)
    print("All examples ready to use!")
    print("=" * 70)
