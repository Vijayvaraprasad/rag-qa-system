import os
from typing import Optional

def generate_answer(context, question):
    """Generate answer using available LLM (OpenAI, Groq, or Demo)"""
    
    # Try OpenAI first
    if os.getenv("OPENAI_API_KEY"):
        return _generate_with_openai(context, question)
    
    # Try Groq (free alternative)
    if os.getenv("GROQ_API_KEY"):
        return _generate_with_groq(context, question)
    
    # Fall back to demo mode
    return _generate_demo_answer(context, question)


def _generate_with_openai(context: str, question: str) -> str:
    """Generate answer using OpenAI"""
    from openai import OpenAI
    
    client = OpenAI()
    prompt = f"""
Answer ONLY using the context below.
If the answer is not present, say you do not know.

Context:
{context}

Question:
{question}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


def _generate_with_groq(context: str, question: str) -> str:
    """Generate answer using Groq (free)"""
    from groq import Groq
    
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    system_prompt = """You are a helpful AI assistant answering questions based on provided documents.
Use the context to answer the question. If the answer is not in the context, say so.
Be concise but informative."""
    
    user_prompt = f"""Question: {question}

Context from documents:
{context}

Please provide a helpful answer based on the context above."""

    message = client.messages.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    
    return message.content[0].text


def _generate_demo_answer(context: str, question: str) -> str:
    """Generate demo answer (no API key needed)"""
    
    lines = context.split('\n')
    summary = '\n'.join([l.strip() for l in lines if l.strip()])[:500]
    
    return f"""[DEMO MODE - No API Key Detected]

Based on your provided documentation:

{summary}

---
To enable real AI responses, set one of these environment variables:
1. OPENAI_API_KEY (OpenAI API key)
2. GROQ_API_KEY (Free alternative: https://console.groq.com/keys)

See SETUP_FREE_KEYS.md for easy setup instructions.

Full context retrieved:
{context[:800]}..."""
