"""
HuggingFace Provider - WORKING VERSION
Uses the official huggingface_hub InferenceClient properly
Includes retry with exponential backoff for transient network errors
LangSmith tracing via @traceable decorator for dashboard visibility
"""

import os
import time
from typing import Optional, Dict, Any, List
from huggingface_hub import InferenceClient

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# LangSmith tracing (optional)
try:
    from langsmith import traceable as _ls_traceable
    _LANGSMITH_OK = True
except ImportError:
    _LANGSMITH_OK = False
    def _ls_traceable(*a, **kw):  # no-op fallback
        def _dec(fn):
            return fn
        if a and callable(a[0]):
            return a[0]
        return _dec


# Known models that work reliably on the free HuggingFace Inference API
AVAILABLE_MODELS: List[Dict[str, str]] = [
    {"id": "meta-llama/Meta-Llama-3-8B-Instruct",      "name": "Llama 3 8B Instruct",      "tier": "Recommended"},
    {"id": "mistralai/Mistral-7B-Instruct-v0.2",       "name": "Mistral 7B Instruct v0.2",  "tier": "Recommended"},
    {"id": "Qwen/Qwen2.5-72B-Instruct",                "name": "Qwen 2.5 72B Instruct",    "tier": "Premium"},
    {"id": "Qwen/Qwen2.5-Coder-32B-Instruct",          "name": "Qwen 2.5 Coder 32B",       "tier": "Premium"},
    {"id": "Qwen/Qwen2.5-7B-Instruct",                 "name": "Qwen 2.5 7B Instruct",     "tier": "Good"},
    {"id": "meta-llama/Llama-3.2-3B-Instruct",         "name": "Llama 3.2 3B Instruct",    "tier": "Good"},
    {"id": "meta-llama/Llama-3.2-1B-Instruct",         "name": "Llama 3.2 1B Instruct",    "tier": "Lightweight"},
]


class HuggingFaceProvider:
    """Working HuggingFace provider using official client with retry logic"""
    
    MAX_RETRIES = 3
    BASE_DELAY = 2  # seconds
    REQUEST_TIMEOUT = 30  # seconds per request
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key"""
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY required")
        
        # Use official InferenceClient with timeout to prevent hung connections
        self.client = InferenceClient(
            token=self.api_key,
            timeout=self.REQUEST_TIMEOUT
        )
    
    @_ls_traceable(run_type="llm", name="HuggingFace Generate")
    def generate(
        self,
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using HuggingFace with retry logic for transient errors."""
        start_time = time.time()
        last_error = None
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                # Use chat_completion (correct API for Instruct/Chat models)
                messages = [{"role": "user", "content": prompt}]
                
                response = self.client.chat_completion(
                    messages=messages,
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                
                latency = time.time() - start_time
                generated_text = response.choices[0].message.content
                
                return {
                    "text": generated_text.strip(),
                    "model": model_name,
                    "provider": "huggingface",
                    "latency_seconds": latency,
                    "success": True
                }
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check if this is a retryable transient error
                retryable = any(keyword in error_msg for keyword in [
                    "disconnected", "getaddrinfo", "connection",
                    "timeout", "10053", "10054", "reset",
                    "temporarily", "503", "502", "429",
                    "overloaded", "rate limit"
                ])
                
                if retryable and attempt < self.MAX_RETRIES:
                    delay = self.BASE_DELAY * (2 ** (attempt - 1))  # 2s, 4s, 8s
                    print(f"    [RETRY] Attempt {attempt}/{self.MAX_RETRIES} failed: {str(e)[:80]}")
                    print(f"    [RETRY] Waiting {delay}s before retry...")
                    time.sleep(delay)
                    continue
                else:
                    # Non-retryable error or max retries exceeded
                    break
        
        # All retries failed
        latency = time.time() - start_time
        error_str = str(last_error)[:200]
        print(f"    [ERROR] All {self.MAX_RETRIES} attempts failed: {error_str}")
        return {
            "text": "",
            "model": model_name,
            "provider": "huggingface",
            "latency_seconds": latency,
            "success": False,
            "error": error_str
        }


if __name__ == "__main__":
    # Test
    provider = HuggingFaceProvider()
    
    # Chat models that work with Inference API
    models_to_test = [
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "HuggingFaceH4/zephyr-7b-beta",
        "google/gemma-7b-it",
    ]
    
    for model in models_to_test:
        print(f"\nTesting: {model}")
        result = provider.generate(
            model_name=model,
            prompt="What is 2+2? Answer:",
            max_tokens=50,
            temperature=0.3
        )
        
        if result["success"]:
            print(f"✓ SUCCESS!")
            print(f"Response: {result['text']}")
            print(f"Latency: {result['latency_seconds']:.2f}s")
            print("\n🎉 HUGGINGFACE IS WORKING!")
            break
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown')[:100]}")
