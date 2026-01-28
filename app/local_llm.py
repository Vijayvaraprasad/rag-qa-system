"""
Local LLM Support: Run models offline!

Instead of paying OpenAI, use free local models:
- Llama 2
- Mistral
- Ollama (easy setup)

Pros: Private, offline, free, fast
Cons: Slightly lower quality than GPT-4

Setup: Install Ollama, run: ollama pull llama2
"""

import requests
import os
from typing import Optional
from app.llm_client import get_openai_client

openai_client = get_openai_client()

class LocalLLMClient:
    """
    Interface with local LLMs via Ollama.
    """
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        """
        Args:
            model: Model name (llama2, mistral, neural-chat, etc.)
            base_url: Ollama API endpoint
        """
        self.model = model
        self.base_url = base_url
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str, temperature: float = 0.2, 
                max_tokens: int = 500, stream: bool = False) -> str:
        """
        Generate text using local LLM.
        
        Args:
            prompt: Input prompt
            temperature: Creativity level (0-1)
            max_tokens: Max response length
            stream: Stream response or get all at once
        
        Returns:
            Generated text
        """
        
        if not self.is_available:
            print(f"⚠ Warning: Ollama not running at {self.base_url}")
            print("  Install: https://ollama.ai")
            print("  Run: ollama pull llama2")
            print("  Run: ollama serve")
            raise ConnectionError("Local LLM not available. Falling back to OpenAI.")
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": stream
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # Local LLMs can be slow
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise Exception(f"Error: {response.status_code}")
        
        except Exception as e:
            print(f"Error calling local LLM: {e}")
            raise
    
    def generate_chat(self, messages: list, temperature: float = 0.2) -> str:
        """
        Chat-style interface.
        
        Args:
            messages: [{"role": "user", "content": "..."}, ...]
            temperature: Creativity level
        
        Returns:
            Generated response
        """
        
        # Convert messages to prompt format
        prompt = ""
        for msg in messages:
            role = msg["role"].upper()
            content = msg["content"]
            prompt += f"{role}:\n{content}\n\n"
        
        prompt += "ASSISTANT:\n"
        
        return self.generate(prompt, temperature=temperature)
    
    def get_available_models(self) -> list:
        """Get list of available local models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except:
            pass
        
        return []


class FallbackLLM:
    """
    Try local LLM first, fallback to OpenAI if unavailable.
    """
    
    def __init__(self, local_model: str = "llama2", use_openai_fallback: bool = True):
        self.local_client = LocalLLMClient(model=local_model)
        self.use_openai_fallback = use_openai_fallback
        self.using_local = self.local_client.is_available
    
    def generate(self, prompt: str, temperature: float = 0.2, 
                max_tokens: int = 500) -> dict:
        """
        Generate with fallback.
        
        Returns:
            {
                "response": str,
                "model": "llama2" or "gpt-4o-mini",
                "is_local": bool
            }
        """
        
        if self.using_local:
            try:
                response = self.local_client.generate(
                    prompt, temperature, max_tokens
                )
                return {
                    "response": response,
                    "model": self.local_client.model,
                    "is_local": True
                }
            except:
                if not self.use_openai_fallback:
                    raise
                print("Local LLM failed, falling back to OpenAI...")
                self.using_local = False
        
        # Fallback to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "response": response.choices[0].message.content,
            "model": "gpt-4o-mini",
            "is_local": False
        }
    
    def generate_chat(self, messages: list, temperature: float = 0.2) -> dict:
        """Chat interface with fallback."""
        
        if self.using_local:
            try:
                response = self.local_client.generate_chat(messages, temperature)
                return {
                    "response": response,
                    "model": self.local_client.model,
                    "is_local": True
                }
            except:
                if not self.use_openai_fallback:
                    raise
                self.using_local = False
        
        # Fallback to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature
        )
        
        return {
            "response": response.choices[0].message.content,
            "model": "gpt-4o-mini",
            "is_local": False
        }


def get_llm_client(prefer_local: bool = True):
    """
    Get appropriate LLM client based on availability.
    
    Usage:
        llm = get_llm_client(prefer_local=True)
        result = llm.generate("What is Python?")
    """
    
    if prefer_local:
        return FallbackLLM(use_openai_fallback=True)
    else:
        # Use OpenAI directly
        import openai
        return openai
