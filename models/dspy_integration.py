"""
DSPy Integration with Open Source Models.
Configures DSPy to work with Ollama and other providers.
"""

import os
from typing import Optional, Dict, Any
import dspy
from models.llm_client import OllamaClient, create_llm_client


class OllamaLM(dspy.LM):
    """DSPy Language Model wrapper for Ollama."""
    
    def __init__(self,
                 model: str = "llama3.1",
                 base_url: str = "http://localhost:11434",
                 temperature: float = 0.7,
                 max_tokens: int = 500,
                 **kwargs):
        """
        Initialize Ollama LM for DSPy.
        
        Args:
            model: Ollama model name
            base_url: Ollama server URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        """
        super().__init__(model=model)
        
        self.model_name = model
        self.client = OllamaClient(
            model_name=model,
            base_url=base_url
        )
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        
        # Check availability
        if not self.client.is_available():
            print(f"⚠️  Warning: Model '{model}' not found in Ollama.")
            print(f"   You may need to run: ollama pull {model}")
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """
        Generate response for DSPy.
        
        Args:
            prompt: Input prompt
            **kwargs: Override parameters
        
        Returns:
            Generated text
        """
        # Merge parameters
        params = {
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "top_p": kwargs.get("top_p", 0.9),
        }
        params.update(self.kwargs)
        
        # Generate
        response = self.client.generate(prompt, **params)
        return response
    
    def basic_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Basic request for DSPy compatibility.
        
        Args:
            prompt: Input prompt
            **kwargs: Generation parameters
        
        Returns:
            Response dictionary
        """
        response = self(prompt, **kwargs)
        
        return {
            "choices": [{
                "text": response,
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()),  # Rough estimate
                "completion_tokens": len(response.split()),
                "total_tokens": len(prompt.split()) + len(response.split())
            }
        }


def configure_dspy(
    provider: str = "ollama",
    model_name: str = "llama3.1",
    temperature: float = 0.7,
    max_tokens: int = 500,
    cache_dir: Optional[str] = None,
    **kwargs
) -> dspy.LM:
    """
    Configure DSPy with specified LLM provider.
    
    Args:
        provider: Provider name ('ollama', 'huggingface')
        model_name: Model identifier
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        cache_dir: Cache directory for DSPy
        **kwargs: Additional provider-specific parameters
    
    Returns:
        Configured DSPy LM instance
    
    Example:
        >>> lm = configure_dspy('ollama', 'llama3.1')
        >>> dspy.settings.configure(lm=lm)
    """
    # Set cache directory
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        dspy.settings.configure(cache_dir=cache_dir)
    
    # Create LM based on provider
    if provider.lower() == "ollama":
        base_url = kwargs.get("base_url") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        lm = OllamaLM(
            model=model_name,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    elif provider.lower() == "huggingface":
        # Use DSPy's built-in HuggingFace support if available
        # Otherwise fall back to custom wrapper
        api_key = kwargs.get("api_key") or os.getenv("HUGGINGFACE_API_KEY")
        
        if not api_key:
            raise ValueError("HuggingFace API key required")
        
        # Try using DSPy's native HF support
        try:
            lm = dspy.HFModel(
                model=model_name,
                token=api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except AttributeError:
            # Fall back to custom implementation
            print("⚠️  Using custom HuggingFace wrapper")
            from models.llm_client import HuggingFaceClient
            # Create custom wrapper (would need additional implementation)
            raise NotImplementedError("Custom HuggingFace wrapper not yet implemented")
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # Configure DSPy globally
    dspy.settings.configure(lm=lm)
    
    return lm


def test_dspy_setup(lm: Optional[dspy.LM] = None) -> bool:
    """
    Test DSPy configuration with a simple prompt.
    
    Args:
        lm: Language model instance (uses current DSPy config if None)
    
    Returns:
        True if test successful
    """
    if lm:
        dspy.settings.configure(lm=lm)
    
    try:
        # Create a simple DSPy Predict module
        predict = dspy.Predict("question -> answer")
        
        # Test with a simple question
        result = predict(question="What is 2+2?")
        
        print("✅ DSPy test successful!")
        print(f"   Question: What is 2+2?")
        print(f"   Answer: {result.answer[:100]}")
        
        return True
        
    except Exception as e:
        print(f"❌ DSPy test failed: {e}")
        return False


# Example usage
if __name__ == "__main__":
    print("=== DSPy Integration Test ===\n")
    
    try:
        # Configure DSPy with Ollama
        print("Configuring DSPy with Ollama...")
        lm = configure_dspy(
            provider="ollama",
            model_name="llama3.1",
            temperature=0.7,
            max_tokens=200
        )
        
        print(f"✅ DSPy configured with: {lm.model_name}\n")
        
        # Test the setup
        print("Testing DSPy setup...")
        test_dspy_setup(lm)
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\nMake sure:")
        print("  1. Ollama is running (ollama serve)")
        print("  2. Model is installed (ollama pull llama3.1)")
