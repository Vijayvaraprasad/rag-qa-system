"""
Hybrid Search combining Semantic (embedding) and Keyword (BM25) search.
This gives you the best of both worlds!

Why? 
- Semantic: Great for understanding meaning ("AI assistant" matches "intelligent helper")
- Keyword: Great for exact matches ("Python error" matches "Python error")
"""

from rank_bm25 import BM25Okapi
from app.embeddings import embed_texts
from app.vectordb import query_chunks
import numpy as np

class HybridSearcher:
    def __init__(self):
        self.bm25 = None
        self.all_chunks = []
        self.chunk_ids = []
    
    def index_documents(self, chunks, chunk_ids):
        """
        Build BM25 index from chunks.
        Called during ingestion.
        """
        self.all_chunks = chunks
        self.chunk_ids = chunk_ids
        
        # Tokenize for BM25 (split into words)
        tokenized_chunks = [chunk.lower().split() for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_chunks)
        
        print(f"✓ Indexed {len(chunks)} chunks for BM25 keyword search")
    
    def semantic_search(self, question, top_k=8):
        """
        Traditional embedding-based search.
        """
        query_embedding = embed_texts([question])[0]
        results = query_chunks(query_embedding, top_k=top_k)
        
        semantic_results = {}
        for doc, dist in zip(results["documents"][0], results["distances"][0]):
            similarity = 1 - dist  # Convert distance to similarity
            semantic_results[doc] = similarity
        
        return semantic_results
    
    def keyword_search(self, question, top_k=8):
        """
        BM25 keyword-based search.
        Great for exact phrase matching.
        """
        if self.bm25 is None:
            return {}
        
        tokenized_question = question.lower().split()
        scores = self.bm25.get_scores(tokenized_question)
        
        # Get top_k by score
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        keyword_results = {}
        for idx in top_indices:
            if idx < len(self.all_chunks) and scores[idx] > 0:
                keyword_results[self.all_chunks[idx]] = float(scores[idx])
        
        return keyword_results
    
    def hybrid_search(self, question, semantic_weight=0.6, keyword_weight=0.4, top_k=8):
        """
        Combine semantic and keyword search.
        
        Args:
            question: User question
            semantic_weight: How much to trust embeddings (0-1)
            keyword_weight: How much to trust keywords (0-1)
            top_k: Return top k results
        
        Returns:
            List of (chunk, combined_score) sorted by score
        """
        # Get results from both methods
        semantic_results = self.semantic_search(question, top_k=top_k)
        keyword_results = self.keyword_search(question, top_k=top_k)
        
        # Normalize scores to 0-1 range for fair combination
        all_chunks_scored = {}
        
        # Add semantic results
        if semantic_results:
            max_semantic = max(semantic_results.values())
            for chunk, score in semantic_results.items():
                normalized_score = score / max_semantic if max_semantic > 0 else 0
                all_chunks_scored[chunk] = semantic_weight * normalized_score
        
        # Add keyword results
        if keyword_results:
            max_keyword = max(keyword_results.values())
            for chunk, score in keyword_results.items():
                normalized_score = score / max_keyword if max_keyword > 0 else 0
                # If chunk already exists, add to it; otherwise create new entry
                if chunk in all_chunks_scored:
                    all_chunks_scored[chunk] += keyword_weight * normalized_score
                else:
                    all_chunks_scored[chunk] = keyword_weight * normalized_score
        
        # Sort by combined score
        hybrid_results = sorted(
            all_chunks_scored.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return hybrid_results[:top_k]
