"""
Model Selection and Cost Tracking Module.

This module provides:
- Dynamic model selection based on task complexity
- Cost tracking for LLM operations
- Budget management and alerts
- Model performance vs cost analysis
- Token usage tracking
- Cost optimization recommendations
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels for model selection."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class AgentType(Enum):
    """Agent types for cost tracking."""
    GENERATOR = "generator"
    JUDGE = "judge"
    OPTIMIZER = "optimizer"


@dataclass
class ModelPricing:
    """Pricing information for a model."""
    model_name: str
    input_cost_per_1k: float  # Cost per 1K input tokens
    output_cost_per_1k: float  # Cost per 1K output tokens
    context_window: int  # Maximum context window
    performance_tier: int  # 1=best, 3=basic
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given token counts."""
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost


@dataclass
class UsageRecord:
    """Record of a single LLM operation."""
    timestamp: str
    agent_type: str
    model_name: str
    input_tokens: int
    output_tokens: int
    cost: float
    task_complexity: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class BudgetAlert:
    """Budget alert notification."""
    timestamp: str
    alert_type: str  # "warning" or "exceeded"
    current_cost: float
    budget_limit: float
    percentage_used: float
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ModelSelector:
    """
    Intelligent model selector with cost tracking.
    
    Selects optimal models based on task complexity, budget constraints,
    and performance requirements while tracking costs.
    """
    
    # Default model pricing (can be updated)
    DEFAULT_PRICING = {
        # OpenAI Models
        "gpt-4": ModelPricing("gpt-4", 0.03, 0.06, 8192, 1),
        "gpt-4-turbo": ModelPricing("gpt-4-turbo", 0.01, 0.03, 128000, 1),
        "gpt-3.5-turbo": ModelPricing("gpt-3.5-turbo", 0.0005, 0.0015, 16384, 2),
        
        # Anthropic Models
        "claude-3-opus": ModelPricing("claude-3-opus", 0.015, 0.075, 200000, 1),
        "claude-3-sonnet": ModelPricing("claude-3-sonnet", 0.003, 0.015, 200000, 1),
        "claude-3-haiku": ModelPricing("claude-3-haiku", 0.00025, 0.00125, 200000, 2),
        
        # Open Source (free, but with compute costs estimated)
        "llama-3-70b": ModelPricing("llama-3-70b", 0.0, 0.0, 8192, 1),
        "llama-3-8b": ModelPricing("llama-3-8b", 0.0, 0.0, 8192, 2),
        "mistral-7b": ModelPricing("mistral-7b", 0.0, 0.0, 8192, 2),
        "phi-3-mini": ModelPricing("phi-3-mini", 0.0, 0.0, 4096, 3),
    }
    
    def __init__(
        self,
        budget_limit: Optional[float] = None,
        warning_threshold: float = 0.8,
        prefer_open_source: bool = True,
        storage_path: str = "./cost_tracking"
    ):
        """
        Initialize Model Selector.
        
        Args:
            budget_limit: Optional budget limit in dollars
            warning_threshold: Warning threshold as fraction of budget (0.0-1.0)
            prefer_open_source: Prefer open source models when possible
            storage_path: Directory for storing cost data
        """
        self.budget_limit = budget_limit
        self.warning_threshold = warning_threshold
        self.prefer_open_source = prefer_open_source
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize pricing database
        self.model_pricing = self.DEFAULT_PRICING.copy()
        
        # Usage tracking
        self.usage_records: List[UsageRecord] = []
        self.total_cost: float = 0.0
        self.alerts: List[BudgetAlert] = []
        
        # Model selection strategy by task complexity
        self.selection_strategy = {
            TaskComplexity.SIMPLE: self._get_simple_models(),
            TaskComplexity.MODERATE: self._get_moderate_models(),
            TaskComplexity.COMPLEX: self._get_complex_models(),
            TaskComplexity.CRITICAL: self._get_critical_models()
        }
        
        logger.info("ModelSelector initialized")
    
    def _get_simple_models(self) -> List[str]:
        """Get models suitable for simple tasks."""
        if self.prefer_open_source:
            return ["phi-3-mini", "mistral-7b", "llama-3-8b", "gpt-3.5-turbo"]
        return ["gpt-3.5-turbo", "claude-3-haiku", "phi-3-mini"]
    
    def _get_moderate_models(self) -> List[str]:
        """Get models suitable for moderate tasks."""
        if self.prefer_open_source:
            return ["llama-3-8b", "mistral-7b", "llama-3-70b", "gpt-3.5-turbo"]
        return ["gpt-3.5-turbo", "claude-3-haiku", "claude-3-sonnet"]
    
    def _get_complex_models(self) -> List[str]:
        """Get models suitable for complex tasks."""
        if self.prefer_open_source:
            return ["llama-3-70b", "claude-3-sonnet", "gpt-4-turbo"]
        return ["claude-3-sonnet", "gpt-4-turbo", "gpt-4"]
    
    def _get_critical_models(self) -> List[str]:
        """Get models suitable for critical tasks."""
        return ["gpt-4", "claude-3-opus", "claude-3-sonnet", "gpt-4-turbo"]
    
    def select_model(
        self,
        task_complexity: TaskComplexity = TaskComplexity.MODERATE,
        agent_type: Optional[AgentType] = None,
        required_context: Optional[int] = None
    ) -> str:
        """
        Select optimal model based on task requirements.
        
        Args:
            task_complexity: Complexity level of the task
            agent_type: Type of agent requesting model
            required_context: Required context window size
        
        Returns:
            Selected model name
        """
        # Get candidate models
        candidates = self.selection_strategy[task_complexity]
        
        # Filter by context window if required
        if required_context:
            candidates = [
                model for model in candidates
                if model in self.model_pricing 
                and self.model_pricing[model].context_window >= required_context
            ]
        
        # Check budget constraints
        if self.budget_limit and self.total_cost >= self.budget_limit:
            # Budget exceeded - use cheapest model
            logger.warning("Budget exceeded - selecting cheapest model")
            candidates = self._get_cheapest_models(candidates)
        elif self.budget_limit:
            remaining_budget = self.budget_limit - self.total_cost
            if remaining_budget < self.budget_limit * (1 - self.warning_threshold):
                # Low budget - prefer cheaper models
                logger.info("Low budget - preferring cost-effective models")
                candidates = self._prioritize_cost_effective(candidates)
        
        # Agent-specific preferences
        if agent_type == AgentType.JUDGE:
            # Judge needs reliability - prefer higher tier
            candidates = sorted(
                candidates,
                key=lambda m: self.model_pricing.get(m, ModelPricing("", 0, 0, 0, 3)).performance_tier
            )
        
        # Select first available model
        selected = candidates[0] if candidates else "gpt-3.5-turbo"
        
        logger.info(f"Selected model '{selected}' for {task_complexity.value} task")
        return selected
    
    def _get_cheapest_models(self, candidates: List[str]) -> List[str]:
        """Sort models by cost (cheapest first)."""
        return sorted(
            candidates,
            key=lambda m: (
                self.model_pricing.get(m, ModelPricing("", 0, 0, 0, 3)).input_cost_per_1k +
                self.model_pricing.get(m, ModelPricing("", 0, 0, 0, 3)).output_cost_per_1k
            )
        )
    
    def _prioritize_cost_effective(self, candidates: List[str]) -> List[str]:
        """Prioritize cost-effective models (good performance/cost ratio)."""
        def cost_effectiveness(model: str) -> float:
            pricing = self.model_pricing.get(model, ModelPricing("", 0, 0, 0, 3))
            # Lower is better: cost * performance_tier
            total_cost = pricing.input_cost_per_1k + pricing.output_cost_per_1k
            return total_cost * pricing.performance_tier
        
        return sorted(candidates, key=cost_effectiveness)
    
    def record_usage(
        self,
        agent_type: AgentType,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        task_complexity: Optional[TaskComplexity] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Record LLM usage and calculate cost.
        
        Args:
            agent_type: Type of agent
            model_name: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            task_complexity: Optional task complexity
            metadata: Optional metadata
        
        Returns:
            Cost of this operation
        """
        # Calculate cost
        if model_name in self.model_pricing:
            cost = self.model_pricing[model_name].calculate_cost(input_tokens, output_tokens)
        else:
            logger.warning(f"Unknown model '{model_name}' - assuming free")
            cost = 0.0
        
        # Create usage record
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            agent_type=agent_type.value,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            task_complexity=task_complexity.value if task_complexity else None,
            metadata=metadata
        )
        
        self.usage_records.append(record)
        self.total_cost += cost
        
        logger.debug(f"Recorded usage: {model_name}, cost=${cost:.4f}")
        
        # Check budget alerts
        self._check_budget_alerts()
        
        return cost
    
    def _check_budget_alerts(self) -> None:
        """Check if budget alerts should be triggered."""
        if not self.budget_limit:
            return
        
        percentage_used = (self.total_cost / self.budget_limit) * 100
        
        # Warning threshold
        if percentage_used >= self.warning_threshold * 100:
            if not any(a.alert_type == "warning" and a.current_cost == self.total_cost for a in self.alerts):
                alert = BudgetAlert(
                    timestamp=datetime.now().isoformat(),
                    alert_type="warning",
                    current_cost=self.total_cost,
                    budget_limit=self.budget_limit,
                    percentage_used=percentage_used,
                    message=f"Warning: {percentage_used:.1f}% of budget used"
                )
                self.alerts.append(alert)
                logger.warning(alert.message)
        
        # Budget exceeded
        if self.total_cost >= self.budget_limit:
            if not any(a.alert_type == "exceeded" for a in self.alerts[-5:]):  # Check recent
                alert = BudgetAlert(
                    timestamp=datetime.now().isoformat(),
                    alert_type="exceeded",
                    current_cost=self.total_cost,
                    budget_limit=self.budget_limit,
                    percentage_used=percentage_used,
                    message=f"Budget exceeded: ${self.total_cost:.2f} / ${self.budget_limit:.2f}"
                )
                self.alerts.append(alert)
                logger.error(alert.message)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive cost summary.
        
        Returns:
            Dictionary with cost breakdown and statistics
        """
        if not self.usage_records:
            return {
                "total_cost": 0.0,
                "total_operations": 0,
                "by_agent": {},
                "by_model": {},
                "budget_status": "no_data"
            }
        
        # Aggregate by agent type
        by_agent = {}
        for record in self.usage_records:
            agent = record.agent_type
            if agent not in by_agent:
                by_agent[agent] = {"cost": 0.0, "operations": 0, "tokens": 0}
            by_agent[agent]["cost"] += record.cost
            by_agent[agent]["operations"] += 1
            by_agent[agent]["tokens"] += record.input_tokens + record.output_tokens
        
        # Aggregate by model
        by_model = {}
        for record in self.usage_records:
            model = record.model_name
            if model not in by_model:
                by_model[model] = {"cost": 0.0, "operations": 0, "tokens": 0}
            by_model[model]["cost"] += record.cost
            by_model[model]["operations"] += 1
            by_model[model]["tokens"] += record.input_tokens + record.output_tokens
        
        # Budget status
        budget_status = "no_budget"
        if self.budget_limit:
            percentage = (self.total_cost / self.budget_limit) * 100
            if self.total_cost >= self.budget_limit:
                budget_status = "exceeded"
            elif percentage >= self.warning_threshold * 100:
                budget_status = "warning"
            else:
                budget_status = "healthy"
        
        return {
            "total_cost": self.total_cost,
            "total_operations": len(self.usage_records),
            "total_tokens": sum(r.input_tokens + r.output_tokens for r in self.usage_records),
            "by_agent": by_agent,
            "by_model": by_model,
            "budget_limit": self.budget_limit,
            "budget_remaining": self.budget_limit - self.total_cost if self.budget_limit else None,
            "budget_status": budget_status,
            "num_alerts": len(self.alerts)
        }
    
    def get_cost_recommendations(self) -> List[str]:
        """
        Get cost optimization recommendations.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not self.usage_records:
            return ["No usage data available for recommendations"]
        
        summary = self.get_cost_summary()
        
        # Check if using expensive models excessively
        expensive_models = ["gpt-4", "claude-3-opus"]
        expensive_usage = sum(
            summary["by_model"].get(model, {}).get("cost", 0)
            for model in expensive_models
        )
        
        if expensive_usage > self.total_cost * 0.5:
            recommendations.append(
                "Consider using gpt-3.5-turbo or claude-3-sonnet for non-critical tasks "
                "to reduce costs by up to 80%"
            )
        
        # Check if preferring paid models when open source available
        if not self.prefer_open_source:
            open_source_cost = sum(
                summary["by_model"].get(model, {}).get("cost", 0)
                for model in ["llama-3-70b", "llama-3-8b", "mistral-7b", "phi-3-mini"]
            )
            
            if self.total_cost > 10.0 and open_source_cost < self.total_cost * 0.2:
                recommendations.append(
                    "Enable prefer_open_source=True to use free open source models "
                    "for simple and moderate tasks"
                )
        
        # Budget-related recommendations
        if self.budget_limit:
            if summary["budget_status"] == "exceeded":
                recommendations.append(
                    "Budget exceeded - switch to open source models or increase budget limit"
                )
            elif summary["budget_status"] == "warning":
                recommendations.append(
                    "Approaching budget limit - consider using more cost-effective models"
                )
        
        # Agent-specific recommendations
        if "generator" in summary["by_agent"]:
            gen_cost = summary["by_agent"]["generator"]["cost"]
            if gen_cost > self.total_cost * 0.6:
                recommendations.append(
                    "Generator agent accounts for most costs - consider simpler models "
                    "or caching frequently requested answers"
                )
        
        if not recommendations:
            recommendations.append("Current model selection strategy is cost-effective")
        
        return recommendations
    
    def export_usage_data(self, filepath: Optional[str] = None) -> str:
        """
        Export usage data to JSON file.
        
        Args:
            filepath: Output path (default: storage_path/usage_data.json)
        
        Returns:
            Path to exported file
        """
        if filepath is None:
            filepath = str(self.storage_path / "usage_data.json")
        
        data = {
            "summary": self.get_cost_summary(),
            "recommendations": self.get_cost_recommendations(),
            "usage_records": [r.to_dict() for r in self.usage_records],
            "alerts": [a.to_dict() for a in self.alerts],
            "export_timestamp": datetime.now().isoformat()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Usage data exported to {filepath}")
        return filepath
    
    def load_usage_data(self, filepath: str) -> None:
        """
        Load usage data from JSON file.
        
        Args:
            filepath: Path to JSON file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load usage records
            self.usage_records = [
                UsageRecord(**record) for record in data.get("usage_records", [])
            ]
            
            # Load alerts
            self.alerts = [
                BudgetAlert(**alert) for alert in data.get("alerts", [])
            ]
            
            # Recalculate total cost
            self.total_cost = sum(r.cost for r in self.usage_records)
            
            logger.info(f"Loaded {len(self.usage_records)} usage records from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading usage data: {e}")
    
    def reset_tracking(self) -> None:
        """Reset all usage tracking and costs."""
        self.usage_records.clear()
        self.alerts.clear()
        self.total_cost = 0.0
        logger.info("Usage tracking reset")
    
    def add_custom_model(self, pricing: ModelPricing) -> None:
        """
        Add custom model pricing.
        
        Args:
            pricing: ModelPricing instance
        """
        self.model_pricing[pricing.model_name] = pricing
        logger.info(f"Added custom model: {pricing.model_name}")
    
    def get_model_info(self, model_name: str) -> Optional[ModelPricing]:
        """
        Get pricing information for a model.
        
        Args:
            model_name: Model name
        
        Returns:
            ModelPricing instance or None if not found
        """
        return self.model_pricing.get(model_name)


def create_model_selector(
    budget_limit: Optional[float] = None,
    warning_threshold: float = 0.8,
    prefer_open_source: bool = True,
    storage_path: str = "./cost_tracking"
) -> ModelSelector:
    """
    Factory function to create ModelSelector.
    
    Args:
        budget_limit: Optional budget limit in dollars
        warning_threshold: Warning threshold as fraction of budget
        prefer_open_source: Prefer open source models
        storage_path: Directory for cost data
    
    Returns:
        ModelSelector instance
    
    Example:
        >>> selector = create_model_selector(budget_limit=100.0)
        >>> model = selector.select_model(TaskComplexity.MODERATE)
        >>> cost = selector.record_usage(AgentType.GENERATOR, model, 500, 200)
    """
    return ModelSelector(
        budget_limit=budget_limit,
        warning_threshold=warning_threshold,
        prefer_open_source=prefer_open_source,
        storage_path=storage_path
    )
