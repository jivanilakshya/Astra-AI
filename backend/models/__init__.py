"""Models module - Contains LLM client and model registry."""

from .llm_client import (
    OllamaClient,
    HuggingFaceClient,
    create_llm_client
)

from .model_registry import (
    ModelConfig,
    ModelRegistry,
    get_registry
)

# Lazy import for DSPy to avoid slow startup
def get_dspy_integration():
    """Lazy import DSPy integration to avoid blocking imports."""
    try:
        from .dspy_integration import (
            OllamaLM,
            configure_dspy,
            test_dspy_setup
        )
        return OllamaLM, configure_dspy, test_dspy_setup
    except ImportError as e:
        print(f"⚠️  DSPy not available: {e}")
        return None, None, None

__all__ = [
    'OllamaClient',
    'HuggingFaceClient',
    'create_llm_client',
    'ModelConfig',
    'ModelRegistry',
    'get_registry',
    'get_dspy_integration'
]
