"""
Groq LLM Integration - Free API (14,400 requests/day)
No credits needed, just sign up at https://console.groq.com/keys
"""

import os
from typing import Optional

# Try to import groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class GroqLLM:
    """
    Groq LLM - Free alternative to OpenAI
    Speed: Extremely fast (50+ tokens/sec)
    Free tier: 14,400 requests/day (30 requests/min)
    """
    
    def __init__(self):
        """Initialize Groq client"""
        if not GROQ_AVAILABLE:
            raise ImportError("Groq not installed. Run: pip install groq")
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Get free key at https://console.groq.com/keys"
            )
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"  # Free fast model
    
    def answer_question(self, question: str, context: str) -> dict:
        """Generate answer using Groq"""
        
        system_prompt = """You are a helpful AI assistant answering questions based on provided documents.
        
Use the context to answer the question. If the answer is not in the context, say so.
Be concise but informative."""
        
        user_prompt = f"""Question: {question}

Context from documents:
{context}

Answer the question based on the context above."""
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
            )
            
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "model": self.model,
                "provider": "Groq (Free)",
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                }
            }
        
        except Exception as e:
            return {
                "answer": f"Error: {str(e)}",
                "error": str(e),
                "provider": "Groq (Free)"
            }
    
    @staticmethod
    def is_configured() -> bool:
        """Check if Groq is properly configured"""
        return GROQ_AVAILABLE and os.getenv("GROQ_API_KEY") is not None


class HuggingFaceLLM:
    """
    Hugging Face Free Inference API
    Free tier: Unlimited with rate limits
    """
    
    def __init__(self):
        """Initialize HF client"""
        api_key = os.getenv("HF_API_KEY")
        if not api_key:
            raise ValueError(
                "HF_API_KEY not set. Get free token at https://huggingface.co/settings/tokens"
            )
        
        self.api_key = api_key
        self.model_id = "mistralai/Mistral-7B-Instruct-v0.1"
    
    def answer_question(self, question: str, context: str) -> dict:
        """Generate answer using Hugging Face"""
        try:
            import requests
            
            api_url = f"https://api-inference.huggingface.co/models/{self.model_id}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            prompt = f"""Question: {question}

Context:
{context}

Answer:"""
            
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_new_tokens": 500}}
            )
            
            if response.status_code == 200:
                result = response.json()[0]
                answer = result.get("generated_text", "").split("Answer:")[-1].strip()
                return {
                    "answer": answer,
                    "provider": "Hugging Face (Free)",
                    "model": self.model_id
                }
            else:
                return {
                    "answer": f"API Error: {response.text}",
                    "error": response.text,
                    "provider": "Hugging Face (Free)"
                }
        
        except Exception as e:
            return {
                "answer": f"Error: {str(e)}",
                "error": str(e),
                "provider": "Hugging Face (Free)"
            }
    
    @staticmethod
    def is_configured() -> bool:
        """Check if HF is configured"""
        return os.getenv("HF_API_KEY") is not None


class OllamaLLM:
    """
    Ollama - Run LLMs locally (completely free, no internet after setup)
    Download from https://ollama.ai
    """
    
    def __init__(self):
        """Initialize Ollama client"""
        try:
            import requests
            # Test if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code != 200:
                raise ConnectionError("Ollama not running on localhost:11434")
        except Exception as e:
            raise ConnectionError(
                f"Ollama not available. Download from https://ollama.ai\n"
                f"Then run: ollama pull mistral\n"
                f"Error: {str(e)}"
            )
        
        self.base_url = "http://localhost:11434"
        self.model = "mistral"
    
    def answer_question(self, question: str, context: str) -> dict:
        """Generate answer using local Ollama"""
        try:
            import requests
            
            prompt = f"""Question: {question}

Context:
{context}

Answer based on the context:"""
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                return {
                    "answer": answer,
                    "provider": "Ollama (Local - Free)",
                    "model": self.model
                }
            else:
                return {
                    "answer": f"Error: {response.text}",
                    "error": response.text,
                    "provider": "Ollama (Local - Free)"
                }
        
        except Exception as e:
            return {
                "answer": f"Error: {str(e)}",
                "error": str(e),
                "provider": "Ollama (Local - Free)"
            }
    
    @staticmethod
    def is_configured() -> bool:
        """Check if Ollama is running"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False


def get_free_llm():
    """
    Try to get a configured free LLM in order of preference:
    1. Groq (fastest, recommended)
    2. Ollama (if running locally)
    3. Hugging Face (if token available)
    """
    
    # Try Groq first
    if GroqLLM.is_configured():
        try:
            return GroqLLM(), "Groq"
        except Exception as e:
            print(f"⚠️ Groq error: {e}")
    
    # Try Ollama
    if OllamaLLM.is_configured():
        try:
            return OllamaLLM(), "Ollama"
        except Exception as e:
            print(f"⚠️ Ollama error: {e}")
    
    # Try Hugging Face
    if HuggingFaceLLM.is_configured():
        try:
            return HuggingFaceLLM(), "HuggingFace"
        except Exception as e:
            print(f"⚠️ HuggingFace error: {e}")
    
    return None, None
