"""
Model Registry for managing different LLM configurations.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a single model."""
    provider: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 500
    top_p: float = 0.9
    use_case: str = "general"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "use_case": self.use_case
        }


class ModelRegistry:
    """Registry for managing multiple model configurations."""
    
    # Default model configurations
    DEFAULT_MODELS = {
        "llama3.1": ModelConfig(
            provider="ollama",
            model_name="llama3.1",
            temperature=0.7,
            max_tokens=500,
            use_case="general"
        ),
        "llama3.1-judge": ModelConfig(
            provider="ollama",
            model_name="llama3.1",
            temperature=0.3,  # Lower for consistent evaluation
            max_tokens=1500,
            use_case="evaluation"
        ),
        "mistral": ModelConfig(
            provider="ollama",
            model_name="mistral",
            temperature=0.7,
            max_tokens=500,
            use_case="general"
        ),
        "qwen2.5": ModelConfig(
            provider="ollama",
            model_name="qwen2.5",
            temperature=0.7,
            max_tokens=500,
            use_case="general"
        ),
        "phi3": ModelConfig(
            provider="ollama",
            model_name="phi3",
            temperature=0.7,
            max_tokens=300,
            use_case="lightweight"
        ),
    }
    
    def __init__(self):
        """Initialize model registry."""
        self.models: Dict[str, ModelConfig] = self.DEFAULT_MODELS.copy()
    
    def register(self, 
                 name: str,
                 provider: str,
                 model_name: str,
                 **kwargs) -> None:
        """
        Register a new model configuration.
        
        Args:
            name: Registry name for the model
            provider: Provider name ('ollama', 'huggingface', etc.)
            model_name: Model identifier
            **kwargs: Additional configuration parameters
        """
        self.models[name] = ModelConfig(
            provider=provider,
            model_name=model_name,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 500),
            top_p=kwargs.get("top_p", 0.9),
            use_case=kwargs.get("use_case", "general")
        )
    
    def get(self, name: str) -> Optional[ModelConfig]:
        """
        Get model configuration by name.
        
        Args:
            name: Registry name
        
        Returns:
            ModelConfig if found, None otherwise
        """
        return self.models.get(name)
    
    def list_models(self) -> Dict[str, ModelConfig]:
        """List all registered models."""
        return self.models.copy()
    
    def get_by_use_case(self, use_case: str) -> Dict[str, ModelConfig]:
        """
        Get models filtered by use case.
        
        Args:
            use_case: Use case ('general', 'evaluation', 'lightweight')
        
        Returns:
            Dictionary of matching models
        """
        return {
            name: config 
            for name, config in self.models.items()
            if config.use_case == use_case
        }
    
    def remove(self, name: str) -> bool:
        """
        Remove a model from registry.
        
        Args:
            name: Registry name
        
        Returns:
            True if removed, False if not found
        """
        if name in self.models:
            del self.models[name]
            return True
        return False
    
    def __repr__(self) -> str:
        return f"ModelRegistry(models={len(self.models)})"


# Global registry instance
_registry = None


def get_registry() -> ModelRegistry:
    """Get global model registry (singleton)."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


# Example usage
if __name__ == "__main__":
    print("=== Model Registry ===\n")
    
    registry = get_registry()
    
    print("Available Models:")
    for name, config in registry.list_models().items():
        print(f"  - {name}: {config.provider}/{config.model_name} ({config.use_case})")
    
    print("\nEvaluation Models:")
    eval_models = registry.get_by_use_case("evaluation")
    for name, config in eval_models.items():
        print(f"  - {name}: temp={config.temperature}, max_tokens={config.max_tokens}")
    
    print("\nRegistering custom model...")
    registry.register(
        "custom-llama",
        provider="ollama",
        model_name="llama3.1:70b",
        temperature=0.8,
        use_case="advanced"
    )
    
    custom = registry.get("custom-llama")
    print(f"Custom model: {custom}")
