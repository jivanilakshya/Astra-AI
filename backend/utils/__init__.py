"""Utilities module - Contains helper functions and utilities."""

from utils.metrics import (
    MetricsCalculator,
    create_metrics_calculator
)

from utils.analytics import (
    AnalyticsAgent,
    IterationLog,
    create_analytics
)

from utils.model_selector import (
    ModelSelector,
    TaskComplexity,
    AgentType,
    ModelPricing,
    UsageRecord,
    BudgetAlert,
    create_model_selector
)

from utils.runtime_mode import (
    RuntimeMode,
    ModeManager,
    get_mode_manager
)

from utils.multi_model import (
    MultiModelEngine,
    ComparisonReport,
    ModelResult,
)

from utils.smart_router import (
    SmartRouter,
    PromptComplexity,
    CostPrediction,
    ModelProfile,
)

from utils.prompt_engine import (
    PromptEngine,
    PromptAnalysis,
)

from utils.cli_formatter import (
    CLIFormatter,
)

from utils.tracing import (
    TracingManager,
    get_tracing_manager,
)

__all__ = [
    # Metrics
    "MetricsCalculator",
    "create_metrics_calculator",
    # Analytics
    "AnalyticsAgent",
    "IterationLog",
    "create_analytics",
    # Model Selector
    "ModelSelector",
    "TaskComplexity",
    "AgentType",
    "ModelPricing",
    "UsageRecord",
    "BudgetAlert",
    "create_model_selector",
    # Runtime Mode (Dev/Prod)
    "RuntimeMode",
    "ModeManager",
    "get_mode_manager",
    # Multi-Model Comparison
    "MultiModelEngine",
    "ComparisonReport",
    "ModelResult",
    # Smart Router
    "SmartRouter",
    "PromptComplexity",
    "CostPrediction",
    "ModelProfile",
    # Prompt Engine
    "PromptEngine",
    "PromptAnalysis",
    # CLI Formatter
    "CLIFormatter",
    # Tracing
    "TracingManager",
    "get_tracing_manager",
]
