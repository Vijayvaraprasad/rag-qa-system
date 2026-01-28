"""
Query Expansion: Make vague questions more specific!

Example:
User: "What is AI?"
Expanded to:
  - "What is artificial intelligence?"
  - "History of artificial intelligence"
  - "Applications of AI"
  - "Machine learning vs AI"

Why? Multiple searches catch more relevant docs!
"""

from app.rate_limit import rate_limit
from app.llm_client import get_available_client

llm_config = get_available_client()

@rate_limit(max_calls=10, time_window=60)
def expand_query(question: str, num_expansions: int = 3) -> list[str]:
    """
    Use LLM to expand a simple question into multiple search queries.
    
    Args:
        question: Original user question
        num_expansions: How many variations to generate
    
    Returns:
        List of expanded queries
    """
    
    if not llm_config["client"]:
        # No LLM available, return original question only
        return [question]
    
    prompt = f"""
You are a search query expert. Given a user question, generate {num_expansions} alternative search queries that would find relevant documents.

Original question: "{question}"

Generate {num_expansions} different ways to search for the same information. Make them progressively more specific, broader, or from different angles.

Return ONLY the queries, one per line, without numbering or bullets.
"""
    
    try:
        if llm_config["type"] == "openai":
            response = llm_config["client"].chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            expansions_text = response.choices[0].message.content.strip()
        elif llm_config["type"] == "groq":
            response = llm_config["client"].messages.create(
                model="llama-3.3-70b-versatile",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            expansions_text = response.content[0].text.strip()
        else:
            return [question]
        
        expanded_queries = [q.strip() for q in expansions_text.split('\n') if q.strip()]
        all_queries = [question] + expanded_queries[:num_expansions]
        return all_queries
    
    except Exception as e:
        print(f"Error expanding query: {e}")
        return [question]


def get_all_expanded_queries(question: str, num_expansions: int = 3) -> dict[str, list[str]]:
    """
    Expand question and return structured data.
    
    Returns:
        {
            "original": "What is AI?",
            "expanded": ["What is artificial intelligence?", ...]
        }
    """
    all_queries = expand_query(question, num_expansions)
    
    return {
        "original": question,
        "expanded": all_queries[1:],  # Exclude original from expanded list
        "all_queries": all_queries
    }
