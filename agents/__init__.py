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

# DSPy agents (legacy - optional)
try:
    from agents.judge import (
        JudgeAgent,
        create_judge
    )
    from agents.orchestrator import (
        OrchestratorAgent,
        create_orchestrator
    )
    from agents.optimizer import (
        OptimizerAgent,
        PromptVersion,
        OptimizationResult,
        create_optimizer
    )
    DSPY_AVAILABLE = True
except Exception:
    DSPY_AVAILABLE = False

# Build __all__ dynamically
__all__ = []

if LANGCHAIN_AVAILABLE:
    __all__.extend([
        "LangChainJudgeAgent",
        "create_langchain_judge",
        "LangChainOptimizerAgent",
        "create_langchain_optimizer",
        "LangGraphOrchestrator",
        "create_langchain_orchestrator",
    ])

if DSPY_AVAILABLE:
    __all__.extend([
        "JudgeAgent",
        "create_judge",
        "OrchestratorAgent",
        "create_orchestrator",
        "OptimizerAgent",
        "PromptVersion",
        "OptimizationResult",
        "create_optimizer",
    ])
