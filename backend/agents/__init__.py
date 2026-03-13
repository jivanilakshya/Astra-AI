"""Agents module - Contains all agent implementations."""

# HuggingFace provider (always available)
from agents.huggingface_provider import HuggingFaceProvider

# LangChain agents (primary)
try:
    from agents.langchain_judge import (
        LangChainJudgeAgent,
        create_langchain_judge
    )
    from agents.langchain_optimizer import (
        LangChainOptimizerAgent,
        create_langchain_optimizer
    )
    from agents.langgraph_orchestrator import (
        LangGraphOrchestrator,
        create_langchain_orchestrator
    )
    LANGCHAIN_AVAILABLE = True
except Exception as e:
    LANGCHAIN_AVAILABLE = False
    print(f"[WARN] LangChain agents not available: {e}")

# DSPy agents (DISABLED - causes 30s+ import of litellm/dspy chain)
# To re-enable, uncomment the block below
DSPY_AVAILABLE = False

# Build __all__ dynamically
__all__ = [
    "HuggingFaceProvider",
    "LANGCHAIN_AVAILABLE",
    "DSPY_AVAILABLE",
]

if LANGCHAIN_AVAILABLE:
    __all__.extend([
        "LangChainJudgeAgent",
        "create_langchain_judge",
        "LangChainOptimizerAgent",
        "create_langchain_optimizer",
        "LangGraphOrchestrator",
        "create_langchain_orchestrator",
    ])
