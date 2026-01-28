from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Query
from pydantic import BaseModel
from pathlib import Path
from typing import Optional

# Basic imports
from app.ingestion import process_document
from app.retrieval import retrieve_candidates
from app.rerank import rerank
from app.llm import generate_answer

# Advanced feature imports
from app.hybrid_search import HybridSearcher
from app.query_expansion import expand_query
from app.context_compression import compress_context, estimate_token_savings
from app.metadata_filter import MetadataFilter
from app.multi_hop_retrieval import MultiHopRetriever
from app.answer_verification import verify_and_fallback
from app.recursive_retrieval import RecursiveRetriever
from app.adaptive_thresholds import AdaptiveThreshold
from app.caching import SmartCache
from app.local_llm import FallbackLLM
from app.free_llm import get_free_llm

app = FastAPI(title="Advanced RAG QA System")

# Initialize advanced components with error handling
try:
    hybrid_searcher = HybridSearcher()
except Exception as e:
    print(f"Warning: HybridSearcher init failed: {e}")
    hybrid_searcher = None

try:
    smart_cache = SmartCache()
except Exception as e:
    print(f"Warning: SmartCache init failed: {e}")
    smart_cache = None

try:
    multi_hop = MultiHopRetriever()
except Exception as e:
    print(f"Warning: MultiHopRetriever init failed: {e}")
    multi_hop = None

try:
    recursive_retriever = RecursiveRetriever()
except Exception as e:
    print(f"Warning: RecursiveRetriever init failed: {e}")
    recursive_retriever = None

try:
    local_llm = FallbackLLM(use_openai_fallback=True)
except Exception as e:
    print(f"Warning: FallbackLLM init failed: {e}")
    local_llm = None

# Request/Response models
class AdvancedAskRequest(BaseModel):
    question: str
    use_hybrid_search: bool = True
    expand_queries: bool = True
    compress_context: bool = True
    verify_answer: bool = True
    use_multi_hop: bool = False
    use_recursive: bool = False
    use_local_llm: bool = False

class FeedbackRequest(BaseModel):
    question: str
    answer: str
    rating: int  # 1-5
    comment: Optional[str] = None

# ============= STANDARD ENDPOINTS =============

@app.post("/upload")
async def upload(file: UploadFile = File(...), bg: BackgroundTasks = None):
    """
    Upload and process document.
    
    Accepts: PDF, TXT, and other text files
    """
    try:
        if bg is None:
            bg = BackgroundTasks()
        
        # Create directory if it doesn't exist
        Path("data/raw_docs").mkdir(parents=True, exist_ok=True)
        
        # Save file
        path = f"data/raw_docs/{file.filename}"
        with open(path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process in background
        bg.add_task(process_document, path)
        
        return {
            "status": "success",
            "message": "File uploaded and processing started",
            "filename": file.filename,
            "size": len(content)
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "filename": file.filename if file else None
        }

@app.get("/ask")
async def ask(question: str):
    """Basic ask endpoint - now uses free Groq API."""
    try:
        candidates = retrieve_candidates(question)
        if not candidates:
            return {
                "answer": "No relevant documents found in database. Please upload documents first using /upload endpoint.",
                "error": "No candidates retrieved"
            }
        ranked = rerank(question, candidates)
        if not ranked:
            ranked = candidates
        context = "\n".join(ranked)
        
        # Try to use Groq (free), fallback to OpenAI if available
        free_llm, provider = get_free_llm()
        if free_llm:
            result = free_llm.answer_question(question, context)
            return {
                "answer": result.get("answer"),
                "provider": result.get("provider"),
                "model": result.get("model")
            }
        else:
            # Fallback to OpenAI if no free LLM
            answer = generate_answer(context, question)
            return {"answer": answer, "provider": "OpenAI"}
    except Exception as e:
        return {
            "answer": f"Error processing question: {str(e)}",
            "error": str(e)
        }

# ============= ADVANCED ENDPOINTS =============

@app.post("/ask/advanced")
async def ask_advanced(request: AdvancedAskRequest):
    """
    Advanced ask with multiple features.
    
    Features you can toggle:
    - Hybrid Search: Combine semantic + keyword search
    - Query Expansion: Search with multiple queries
    - Context Compression: Remove irrelevant sentences
    - Answer Verification: Check if answer is grounded
    - Multi-Hop Retrieval: Chain multiple retrievals
    - Recursive Retrieval: Iteratively improve results
    - Local LLM: Use offline models
    """
    
    try:
        # Check cache first
        cached = smart_cache.get_answer_with_cache(request.question)
        if cached:
            return {
                "answer": cached["answer"],
                "from_cache": True,
                "metadata": {"cache_hit": True}
            }
        
        metadata = {}
        
        # ===== RETRIEVAL PHASE =====
        
        # Get adaptive threshold
        threshold_info = AdaptiveThreshold.get_threshold_for_question(request.question)
        metadata["threshold_info"] = threshold_info
        
        # Retrieval strategy
        if request.use_multi_hop:
            # Multi-hop retrieval
            multi_hop_result = multi_hop.multi_hop_retrieve(request.question, num_hops=2)
            candidates = multi_hop_result["all_chunks"]
            metadata["retrieval_method"] = "multi-hop"
            metadata["hops"] = multi_hop_result["hops_performed"]
        
        elif request.expand_queries:
            # Query expansion + hybrid search
            expanded_queries = expand_query(request.question, num_expansions=2)
            all_candidates = set()
            
            for expanded_q in expanded_queries:
                if request.use_hybrid_search:
                    hybrid_results = hybrid_searcher.hybrid_search(
                        expanded_q,
                        semantic_weight=0.6,
                        keyword_weight=0.4,
                        top_k=5
                    )
                    all_candidates.update([chunk for chunk, _ in hybrid_results])
                else:
                    hybrid_results = retrieve_candidates(expanded_q)
                    all_candidates.update(hybrid_results)
            
            candidates = list(all_candidates)
            metadata["retrieval_method"] = "query_expansion"
            metadata["queries_used"] = expanded_queries
        
        else:
            # Standard or hybrid search
            if request.use_hybrid_search:
                hybrid_results = hybrid_searcher.hybrid_search(request.question, top_k=8)
                candidates = [chunk for chunk, _ in hybrid_results]
                metadata["retrieval_method"] = "hybrid"
            else:
                candidates = retrieve_candidates(request.question)
                metadata["retrieval_method"] = "semantic"
        
        if not candidates:
            return {
                "answer": "No relevant documents found. Please upload documents using the /upload endpoint.",
                "metadata": {"error": "No candidates found"}
            }
        
        metadata["candidates_found"] = len(candidates)
        
        # ===== RERANKING & COMPRESSION PHASE =====
        
        ranked = rerank(request.question, candidates, top_n=3)
        if not ranked:
            ranked = candidates[:3]
        metadata["reranked_count"] = len(ranked)
        
        # Compress context if requested
        if request.compress_context:
            compressed_ranked = compress_context(
                "\n".join(ranked),
                request.question,
                strategy="extract"
            )
            context = compressed_ranked
            savings = estimate_token_savings("\n".join(ranked), compressed_ranked)
            metadata["compression"] = savings
        else:
            context = "\n".join(ranked)
        
        # ===== GENERATION PHASE =====
        
        if request.use_local_llm:
            # Use local LLM
            result = local_llm.generate(
                prompt=f"Answer based on context:\n{context}\n\nQuestion: {request.question}",
                temperature=0.2
            )
            answer = result["response"]
            metadata["llm_model"] = result["model"]
            metadata["llm_local"] = result["is_local"]
        else:
            # Use OpenAI
            answer = generate_answer(context, request.question)
            metadata["llm_model"] = "gpt-4o-mini"
            metadata["llm_local"] = False
        
        # ===== VERIFICATION PHASE =====
        
        if request.verify_answer:
            final_answer, verification = verify_and_fallback(
                answer, context, request.question, threshold=0.6
            )
            metadata["answer_verified"] = verification["is_grounded"]
            metadata["verification_confidence"] = verification["confidence"]
        else:
            final_answer = answer
        
        # ===== RECURSIVE IMPROVEMENT =====
        
        if request.use_recursive:
            recursive_result = recursive_retriever.recursive_retrieve(request.question)
            final_answer = recursive_result["final_answer"]
            metadata["recursive_iterations"] = recursive_result["iterations"]
            metadata["final_confidence"] = recursive_result["confidence"]
        
        # Cache the answer
        smart_cache.cache.set(request.question, final_answer, metadata)
        
        return {
            "answer": final_answer,
            "from_cache": False,
            "metadata": metadata
        }
    except Exception as e:
        import traceback
        return {
            "answer": f"Error: {str(e)}",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/ask/compare")
async def ask_compare(question: str):
    """
    Compare different retrieval strategies.
    Shows results from: semantic, hybrid, multi-hop
    """
    
    try:
        results = {}
        
        # Standard semantic
        candidates = retrieve_candidates(question)
        if not candidates:
            return {
                "comparison": "No documents in database",
                "error": "Please upload documents first"
            }
        
        ranked = rerank(question, candidates, top_n=3)
        if not ranked:
            ranked = candidates[:3]
        semantic_context = "\n".join(ranked)
        semantic_answer = generate_answer(semantic_context, question)
        results["semantic"] = {
            "chunks_found": len(candidates),
            "answer": semantic_answer[:200]
        }
        
        # Hybrid
        hybrid_results = hybrid_searcher.hybrid_search(question, top_k=8)
        hybrid_chunks = [chunk for chunk, _ in hybrid_results]
        if hybrid_chunks:
            hybrid_ranked = rerank(question, hybrid_chunks, top_n=3)
            if not hybrid_ranked:
                hybrid_ranked = hybrid_chunks[:3]
            hybrid_context = "\n".join(hybrid_ranked)
            hybrid_answer = generate_answer(hybrid_context, question)
            results["hybrid"] = {
                "chunks_found": len(hybrid_chunks),
                "answer": hybrid_answer[:200]
            }
        
        # Multi-hop
        multi_hop_result = multi_hop.multi_hop_retrieve(question, num_hops=2)
        multi_hop_chunks = multi_hop_result["all_chunks"][:8]
        if multi_hop_chunks:
            multi_hop_ranked = rerank(question, multi_hop_chunks, top_n=3)
            if not multi_hop_ranked:
                multi_hop_ranked = multi_hop_chunks[:3]
            multi_hop_context = "\n".join(multi_hop_ranked)
            multi_hop_answer = generate_answer(multi_hop_context, question)
            results["multi_hop"] = {
                "chunks_found": len(multi_hop_chunks),
                "hops": multi_hop_result["hops_performed"],
                "answer": multi_hop_answer[:200]
            }
        
        return {
            "question": question,
            "comparison": results
        }
    except Exception as e:
        import traceback
        return {
            "question": question,
            "error": str(e),
            "comparison": {},
            "traceback": traceback.format_exc()
        }

# ============= FEEDBACK ENDPOINTS =============

@app.post("/feedback")
async def add_feedback(feedback: FeedbackRequest):
    """Submit feedback on answer quality."""
    smart_cache.feedback.add_feedback(
        feedback.question,
        feedback.answer,
        feedback.rating,
        feedback.comment
    )
    return {
        "status": "feedback recorded",
        "rating": feedback.rating
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    cache_stats = smart_cache.cache.get_cache_stats()
    feedback_summary = smart_cache.feedback.get_feedback_summary()
    
    return {
        "cache": cache_stats,
        "feedback": feedback_summary
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "features": {
            "hybrid_search": True,
            "query_expansion": True,
            "context_compression": True,
            "answer_verification": True,
            "multi_hop": True,
            "recursive": True,
            "caching": True,
            "local_llm": local_llm.using_local
        }
    }
