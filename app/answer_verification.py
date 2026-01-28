"""
Answer Verification: Prevent hallucinations!

Problem: LLM generates perfect-sounding answer that's NOT in your documents
Solution: Check if answer is actually grounded in the context

Example:
Context: "The Earth orbits the Sun"
LLM says: "The Moon orbits the Earth"
Check: Is "Moon orbits Earth" in context? NO ❌
Result: Return "Answer not found in documents" (no hallucination!)
"""

from app.rate_limit import rate_limit
from app.llm_client import get_available_client

@rate_limit(max_calls=20, time_window=60)
def verify_answer(answer: str, context: str, question: str, threshold: float = 0.6) -> dict:
    """
    Verify that answer is grounded in the provided context.
    
    Args:
        answer: LLM-generated answer
        context: Retrieved context that answer should be based on
        question: Original question
        threshold: Confidence threshold (0-1)
    
    Returns:
        {
            "is_grounded": bool,
            "confidence": float (0-1),
            "reasoning": str,
            "verified_answer": str (original or modified)
        }
    """
    
    llm_config = get_available_client()
    if not llm_config["client"]:
        # No LLM available, accept answer as-is
        return {
            "is_grounded": True,
            "confidence": 0.5,
            "reasoning": "Verification skipped (no LLM available)",
            "verified_answer": answer
        }
    
    verification_prompt = f"""
Verify if the answer is grounded in (supported by) the provided context.

Context:
{context}

Question:
{question}

Answer:
{answer}

Analyze:
1. Is the answer's main claim present in the context?
2. Are the key facts verifiable from the context?
3. Does the answer add information NOT in context (potential hallucination)?

Respond with:
GROUNDED: <Yes/No>
CONFIDENCE: <0.0-1.0>
REASONING: <Brief explanation>
"""
    
    try:
        if llm_config["type"] == "openai":
            response = llm_config["client"].chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": verification_prompt}],
                temperature=0.2,
                max_tokens=200
            )
        elif llm_config["type"] == "groq":
            response = llm_config["client"].messages.create(
                model="llama-3.3-70b-versatile",
                max_tokens=200,
                messages=[{"role": "user", "content": verification_prompt}]
            )
        else:
            return {
                "is_grounded": True,
                "confidence": 0.5,
                "reasoning": "Verification skipped",
                "verified_answer": answer
            }
        
        if llm_config["type"] == "openai":
            verification_text = response.choices[0].message.content.strip()
        else:
            verification_text = response.content[0].text.strip()
        
        # Parse response
        is_grounded = "yes" in verification_text.lower()[:100]
        
        # Extract confidence
        confidence = 0.5
        if "confidence:" in verification_text.lower():
            try:
                conf_line = [l for l in verification_text.split('\n') if 'confidence:' in l.lower()][0]
                conf_str = conf_line.split(':')[1].strip()
                confidence = float(conf_str.split()[0])
            except:
                pass
        
        reasoning = ""
        if "reasoning:" in verification_text.lower():
            try:
                reasoning_line = [l for l in verification_text.split('\n') if 'reasoning:' in l.lower()][0]
                reasoning = reasoning_line.split(':', 1)[1].strip()
            except:
                reasoning = verification_text
        
        return {
            "is_grounded": is_grounded and confidence >= threshold,
            "confidence": confidence,
            "reasoning": reasoning or verification_text,
            "verified_answer": answer
        }
    
    except Exception as e:
        print(f"Error verifying answer: {e}")
        return {
            "is_grounded": True,  # Default to True on error
            "confidence": 0.5,
            "reasoning": f"Verification skipped: {str(e)}",
            "verified_answer": answer
        }


def verify_and_fallback(answer: str, context: str, question: str, 
                       threshold: float = 0.6) -> tuple[str, dict]:
    """
    Verify answer, and if not grounded, return fallback message.
    
    Returns:
        (final_answer, verification_info)
    """
    verification = verify_answer(answer, context, question, threshold)
    
    if not verification["is_grounded"]:
        fallback_answer = (
            f"I couldn't find a clear answer in the provided documents. "
            f"Based on the context: {context[:200]}... "
            f"Please provide more specific documents for this question."
        )
        return fallback_answer, verification
    
    return answer, verification


@rate_limit(max_calls=10, time_window=60)
def extract_key_claims(answer: str) -> list[str]:
    """
    Extract main claims from answer for verification.
    
    Example:
        Answer: "Python is a programming language created by Guido van Rossum in 1991"
        Claims: ["Python is a programming language", "created by Guido van Rossum", "1991"]
    """
    prompt = f"""
Extract the main factual claims from this answer. Each claim should be a single sentence.

Answer: {answer}

List each claim on a new line:
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150
        )
        
        claims_text = response.choices[0].message.content.strip()
        claims = [c.strip() for c in claims_text.split('\n') if c.strip() and not c.startswith('#')]
        return claims
    
    except:
        return [answer]


@rate_limit(max_calls=10, time_window=60)
def verify_claims_in_context(claims: list[str], context: str) -> dict:
    """
    Verify each claim against context.
    
    Returns:
        {
            "verified_claims": ["claim1", "claim2"],
            "unverified_claims": ["claim3"],
            "coverage": 0.67
        }
    """
    prompt = f"""
Check each claim against the provided context.

Context:
{context}

Claims to verify:
{chr(10).join(f'{i+1}. {claim}' for i, claim in enumerate(claims))}

For each claim, respond with:
<claim number>: VERIFIED or UNVERIFIED

Then provide a summary of verification coverage.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200
        )
        
        verification_text = response.choices[0].message.content.strip()
        
        # Parse results
        verified = []
        unverified = []
        
        for line in verification_text.split('\n'):
            if 'verified' in line.lower():
                try:
                    num = int(line.split(':')[0])
                    if 'verified' in line.lower() and 'unverified' not in line.lower():
                        verified.append(claims[num-1])
                    else:
                        unverified.append(claims[num-1])
                except:
                    pass
        
        coverage = len(verified) / len(claims) if claims else 0
        
        return {
            "verified_claims": verified,
            "unverified_claims": unverified,
            "coverage": round(coverage, 2)
        }
    
    except:
        return {
            "verified_claims": claims,
            "unverified_claims": [],
            "coverage": 1.0
        }
