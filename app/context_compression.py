"""
Context Compression: Remove irrelevant sentences before sending to LLM.

Problem: Full chunks (5000 tokens) sent to GPT = expensive
Solution: Extract only relevant sentences (1000 tokens) = 80% cheaper!

Example:
Original chunk: "The sun is a star. It rises in the morning. It sets in evening. 
                 It provides light and heat. Birds sing when sun rises. 
                 Flowers bloom in sunlight..."

Question: "Does the sun provide light?"

Compressed: "It provides light and heat." (Irrelevant sentences removed!)
"""

from app.rate_limit import rate_limit
from app.llm_client import get_available_client

@rate_limit(max_calls=20, time_window=60)
def compress_context(context: str, question: str, strategy: str = "extract") -> str:
    """
    Compress context by extracting only relevant sentences.
    
    Args:
        context: Full retrieved context
        question: User question
        strategy: "extract" (keep relevant sentences) or "summarize" (compress)
    
    Returns:
        Compressed context
    """
    
    if strategy == "extract":
        prompt = f"""
Extract ONLY the sentences from the context below that are relevant to answering the question.
Remove any sentences that don't help answer the question.
Keep the extracted sentences in order.

Question: {question}

Context:
{context}

Extracted context (only relevant sentences):
"""
    else:  # summarize
        prompt = f"""
Summarize the context below in 2-3 sentences, focusing on what's relevant to the question.

Question: {question}

Context:
{context}

Summary:
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Be precise
            max_tokens=300
        )
        
        compressed = response.choices[0].message.content.strip()
        return compressed
    
    except Exception as e:
        print(f"Error compressing context: {e}")
        return context  # Return original if error


def compress_multiple_chunks(chunks: list[str], question: str) -> list[str]:
    """
    Compress multiple chunks for efficiency.
    
    Args:
        chunks: List of text chunks
        question: User question
    
    Returns:
        List of compressed chunks
    """
    compressed = []
    for chunk in chunks:
        compressed_chunk = compress_context(chunk, question, strategy="extract")
        if compressed_chunk:
            compressed.append(compressed_chunk)
    
    return compressed


def estimate_token_savings(original_context: str, compressed_context: str) -> dict:
    """
    Estimate cost savings from compression.
    Rough estimate: ~4 chars per token
    """
    original_tokens = len(original_context) // 4
    compressed_tokens = len(compressed_context) // 4
    
    saved = original_tokens - compressed_tokens
    savings_percent = (saved / original_tokens * 100) if original_tokens > 0 else 0
    
    return {
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "tokens_saved": saved,
        "savings_percent": round(savings_percent, 2),
        "cost_reduction": f"{savings_percent:.1f}%"
    }
