"""
LLM Client for Open Source Models
Supports Ollama, HuggingFace, and vLLM servers.
"""

import os
import requests
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model/service is available."""
        pass


class OllamaClient(BaseLLMClient):
    """Client for Ollama local models."""
    
    def __init__(self, 
                 model_name: str = "llama3.1",
                 base_url: str = "http://localhost:11434",
                 timeout: int = 120):
        """
        Initialize Ollama client.
        
        Args:
            model_name: Name of the Ollama model (e.g., 'llama3.1', 'mistral')
            base_url: Base URL for Ollama API
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.tags_endpoint = f"{self.base_url}/api/tags"
    
    def generate(self, 
                 prompt: str,
                 temperature: float = 0.7,
                 max_tokens: int = 500,
                 top_p: float = 0.9,
                 stop: Optional[List[str]] = None,
                 **kwargs) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            stop: Stop sequences
            **kwargs: Additional Ollama parameters
        
        Returns:
            Generated text
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
            }
        }
        
        if stop:
            payload["options"]["stop"] = stop
        
        # Add any additional options
        payload["options"].update(kwargs)
        
        try:
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama request timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (run 'ollama serve')"
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(self.tags_endpoint, timeout=5)
            response.raise_for_status()
            
            # Check if our model is in the list
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            
            return self.model_name in model_names
            
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = requests.get(self.tags_endpoint, timeout=5)
            response.raise_for_status()
            
            models = response.json().get("models", [])
            return [m.get("name", "") for m in models]
            
        except Exception:
            return []
    
    def pull_model(self, model_name: Optional[str] = None) -> bool:
        """
        Pull a model from Ollama library.
        
        Args:
            model_name: Model to pull (defaults to self.model_name)
        
        Returns:
            True if successful
        """
        model = model_name or self.model_name
        pull_endpoint = f"{self.base_url}/api/pull"
        
        try:
            response = requests.post(
                pull_endpoint,
                json={"name": model},
                timeout=600  # 10 minutes for model download
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Error pulling model {model}: {e}")
            return False
    
    def __repr__(self) -> str:
        return f"OllamaClient(model={self.model_name}, url={self.base_url})"


class HuggingFaceClient(BaseLLMClient):
    """Client for HuggingFace Inference API."""
    
    def __init__(self,
                 model_name: str,
                 api_key: Optional[str] = None,
                 timeout: int = 120):
        """
        Initialize HuggingFace client.
        
        Args:
            model_name: HuggingFace model name (e.g., 'mistralai/Mistral-7B-Instruct-v0.2')
            api_key: HuggingFace API key
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.timeout = timeout
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        
        if not self.api_key:
            raise ValueError(
                "HuggingFace API key required. Set HUGGINGFACE_API_KEY environment variable."
            )
    
    def generate(self,
                 prompt: str,
                 temperature: float = 0.7,
                 max_tokens: int = 500,
                 top_p: float = 0.9,
                 **kwargs) -> str:
        """
        Generate text using HuggingFace Inference API.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            **kwargs: Additional parameters
        
        Returns:
            Generated text
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "top_p": top_p,
                "return_full_text": False
            }
        }
        
        payload["parameters"].update(kwargs)
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "").strip()
            elif isinstance(result, dict):
                return result.get("generated_text", "").strip()
            else:
                return ""
                
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HuggingFace API error: {e}")
    
    def is_available(self) -> bool:
        """Check if the HuggingFace model is available."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"https://huggingface.co/api/models/{self.model_name}",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
            
        except Exception:
            return False
    
    def __repr__(self) -> str:
        return f"HuggingFaceClient(model={self.model_name})"


def create_llm_client(
    provider: str,
    model_name: str,
    **kwargs
) -> BaseLLMClient:
    """
    Factory function to create LLM client based on provider.
    
    Args:
        provider: Provider name ('ollama', 'huggingface', 'vllm')
        model_name: Model name
        **kwargs: Additional arguments for the client
    
    Returns:
        LLM client instance
    
    Example:
        >>> client = create_llm_client('ollama', 'llama3.1')
        >>> response = client.generate("What is AI?")
    """
    provider = provider.lower()
    
    if provider == "ollama":
        base_url = kwargs.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaClient(
            model_name=model_name,
            base_url=base_url,
            timeout=kwargs.get("timeout", 120)
        )
    
    elif provider == "huggingface":
        return HuggingFaceClient(
            model_name=model_name,
            api_key=kwargs.get("api_key"),
            timeout=kwargs.get("timeout", 120)
        )
    
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: ollama, huggingface"
        )


# Example usage and testing
if __name__ == "__main__":
    print("=== Testing LLM Clients ===\n")
    
    # Test Ollama
    print("Testing Ollama Client...")
    try:
        ollama = OllamaClient("llama3.1")
        
        if ollama.is_available():
            print("✅ Ollama is available")
            print(f"Available models: {ollama.list_models()}")
            
            # Test generation
            response = ollama.generate("What is 2+2? Answer briefly.", max_tokens=50)
            print(f"Response: {response[:100]}")
        else:
            print("⚠️  Ollama not available. Make sure Ollama is running.")
            print("   Run: ollama serve")
            print(f"   Then: ollama pull {ollama.model_name}")
    
    except Exception as e:
        print(f"❌ Ollama error: {e}")
    
    print("\n" + "="*50)
