"""
Unified LLM client provider that handles multiple LLM backends gracefully.
Automatically falls back from OpenAI -> Groq -> Demo mode.
"""

import os
from typing import Optional


def get_openai_client():
    """Get OpenAI client if API key is available."""
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            return OpenAI()
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {e}")
            return None
    return None


def get_groq_client():
    """Get Groq client if API key is available."""
    if os.getenv("GROQ_API_KEY"):
        try:
            from groq import Groq
            return Groq(api_key=os.getenv("GROQ_API_KEY"))
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            return None
    return None


def get_available_client():
    """
    Get the first available LLM client:
    1. OpenAI (if OPENAI_API_KEY set)
    2. Groq (if GROQ_API_KEY set)
    3. None (will use demo/fallback mode)
    """
    client = get_openai_client()
    if client:
        return {"type": "openai", "client": client}
    
    client = get_groq_client()
    if client:
        return {"type": "groq", "client": client}
    
    return {"type": "none", "client": None}
