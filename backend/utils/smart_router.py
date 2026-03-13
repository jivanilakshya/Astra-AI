"""
Intelligent Model Router - Automatic complexity-based routing + Cost Optimization

Routes prompts to the optimal model based on:
1. Prompt complexity (simple / moderate / complex / critical)
2. Token estimation & context requirements
3. Cost budget constraints
4. Historical performance data

Also includes:
- Cost prediction BEFORE execution
- Self-improving router with feedback loops

Complexity Detection Methods:
- Lexical analysis (sentence count, word count, vocabulary richness)
- Keyword pattern matching (code, math, reasoning markers)
- Token estimation
- Question type classification

Usage:
    from utils.smart_router import SmartRouter
    router = SmartRouter()

    prediction = router.predict_cost(prompt)   # cost prediction before execution
    model = router.route(prompt)                # get best model
    router.record_feedback(prompt, model, score)  # self-improving feedback
"""

import re
import json
import math
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import defaultdict

import logging
logger = logging.getLogger(__name__)


# ── Complexity levels ────────────────────────────────────────────────────────
class PromptComplexity:
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


# ── Token estimation ────────────────────────────────────────────────────────
def estimate_tokens(text: str) -> int:
    """Estimate token count (heuristic: ~4 chars = 1 token for English)."""
    return max(1, len(text) // 4)


def estimate_response_tokens(prompt_tokens: int, complexity: str) -> int:
    """Estimate expected response token count based on complexity."""
    multipliers = {
        PromptComplexity.SIMPLE: 0.8,
        PromptComplexity.MODERATE: 1.5,
        PromptComplexity.COMPLEX: 2.5,
        PromptComplexity.CRITICAL: 3.0,
    }
    return int(prompt_tokens * multipliers.get(complexity, 1.5))


# ── Model registry with capabilities ──────────────────────────────────────
@dataclass
class ModelProfile:
    """Profile of a model's capabilities and costs."""
    name: str
    provider: str  # huggingface, openai, anthropic, ollama
    context_window: int
    cost_input_per_1k: float
    cost_output_per_1k: float
    avg_latency_seconds: float  # typical latency
    quality_tier: int  # 1=best, 3=basic
    strengths: List[str] = field(default_factory=list)  # e.g. ["code", "reasoning", "general"]
    is_available: bool = True


# Default model profiles
DEFAULT_MODEL_PROFILES: Dict[str, ModelProfile] = {
    "meta-llama/Meta-Llama-3-8B-Instruct": ModelProfile(
        name="meta-llama/Meta-Llama-3-8B-Instruct",
        provider="huggingface", context_window=8192,
        cost_input_per_1k=0.0, cost_output_per_1k=0.0,
        avg_latency_seconds=3.0, quality_tier=2,
        strengths=["general", "reasoning", "instruction_following"],
    ),
    "mistralai/Mistral-7B-Instruct-v0.2": ModelProfile(
        name="mistralai/Mistral-7B-Instruct-v0.2",
        provider="huggingface", context_window=8192,
        cost_input_per_1k=0.0, cost_output_per_1k=0.0,
        avg_latency_seconds=2.5, quality_tier=2,
        strengths=["general", "code", "concise"],
    ),
    "Qwen/Qwen2.5-72B-Instruct": ModelProfile(
        name="Qwen/Qwen2.5-72B-Instruct",
        provider="huggingface", context_window=32768,
        cost_input_per_1k=0.0, cost_output_per_1k=0.0,
        avg_latency_seconds=4.0, quality_tier=1,
        strengths=["reasoning", "code", "general", "complex"],
    ),
    "Qwen/Qwen2.5-7B-Instruct": ModelProfile(
        name="Qwen/Qwen2.5-7B-Instruct",
        provider="huggingface", context_window=32768,
        cost_input_per_1k=0.0, cost_output_per_1k=0.0,
        avg_latency_seconds=2.5, quality_tier=2,
        strengths=["general", "reasoning", "code"],
    ),
    "Qwen/Qwen2.5-Coder-32B-Instruct": ModelProfile(
        name="Qwen/Qwen2.5-Coder-32B-Instruct",
        provider="huggingface", context_window=32768,
        cost_input_per_1k=0.0, cost_output_per_1k=0.0,
        avg_latency_seconds=3.5, quality_tier=1,
        strengths=["code", "reasoning", "instruction_following"],
    ),
    "meta-llama/Llama-3.2-3B-Instruct": ModelProfile(
        name="meta-llama/Llama-3.2-3B-Instruct",
        provider="huggingface", context_window=8192,
        cost_input_per_1k=0.0, cost_output_per_1k=0.0,
        avg_latency_seconds=2.0, quality_tier=3,
        strengths=["general", "fast", "chat"],
    ),
    "meta-llama/Llama-3.2-1B-Instruct": ModelProfile(
        name="meta-llama/Llama-3.2-1B-Instruct",
        provider="huggingface", context_window=8192,
        cost_input_per_1k=0.0, cost_output_per_1k=0.0,
        avg_latency_seconds=1.5, quality_tier=3,
        strengths=["general", "fast"],
    ),
    "gpt-4": ModelProfile(
        name="gpt-4", provider="openai", context_window=8192,
        cost_input_per_1k=0.03, cost_output_per_1k=0.06,
        avg_latency_seconds=5.0, quality_tier=1,
        strengths=["reasoning", "code", "general", "complex"],
    ),
    "gpt-3.5-turbo": ModelProfile(
        name="gpt-3.5-turbo", provider="openai", context_window=16384,
        cost_input_per_1k=0.0005, cost_output_per_1k=0.0015,
        avg_latency_seconds=1.5, quality_tier=2,
        strengths=["general", "fast", "chat"],
    ),
    "claude-3-sonnet": ModelProfile(
        name="claude-3-sonnet", provider="anthropic", context_window=200000,
        cost_input_per_1k=0.003, cost_output_per_1k=0.015,
        avg_latency_seconds=3.5, quality_tier=1,
        strengths=["reasoning", "code", "long_context", "complex"],
    ),
    "claude-3-haiku": ModelProfile(
        name="claude-3-haiku", provider="anthropic", context_window=200000,
        cost_input_per_1k=0.00025, cost_output_per_1k=0.00125,
        avg_latency_seconds=1.5, quality_tier=2,
        strengths=["general", "fast", "long_context"],
    ),
}


@dataclass
class CostPrediction:
    """Pre-execution cost & latency prediction."""
    prompt_tokens_est: int
    response_tokens_est: int
    total_tokens_est: int
    cost_estimate_usd: float
    latency_estimate_seconds: float
    complexity: str
    recommended_model: str
    alternative_models: List[Dict[str, Any]]
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoutingFeedback:
    """Feedback record for self-improving router."""
    timestamp: str
    prompt_hash: str
    complexity: str
    model_used: str
    quality_score: float  # 0-10
    latency_seconds: float
    cost_usd: float
    success: bool


class SmartRouter:
    """
    Intelligent model router with:
    1. Complexity detection
    2. Cost prediction before execution
    3. Self-improving routing via feedback loops
    """

    def __init__(
        self,
        model_profiles: Optional[Dict[str, ModelProfile]] = None,
        prefer_free: bool = True,
        budget_limit: Optional[float] = None,
        feedback_path: str = "./output/router_feedback.json",
    ):
        self.profiles = model_profiles or DEFAULT_MODEL_PROFILES.copy()
        self.prefer_free = prefer_free
        self.budget_limit = budget_limit
        self.feedback_path = Path(feedback_path)
        self.total_cost = 0.0

        # Feedback history for self-improvement
        self.feedback_history: List[RoutingFeedback] = []
        self._model_scores: Dict[str, List[float]] = defaultdict(list)  # model -> [scores]
        self._load_feedback()

    # ── 1. Complexity Detection ──────────────────────────────────────────

    # Keyword patterns for complexity signals
    _CODE_PATTERNS = re.compile(
        r'\b(code|function|class|def |import |print\(|for loop|algorithm|implement|debug|refactor|API|SQL|regex)\b',
        re.IGNORECASE,
    )
    _REASONING_PATTERNS = re.compile(
        r'\b(explain|why|how|compare|analyze|evaluate|pros and cons|trade.?off|reasoning|proof|derive)\b',
        re.IGNORECASE,
    )
    _MATH_PATTERNS = re.compile(
        r'\b(calculate|equation|integral|derivative|matrix|probability|statistics|theorem|formula)\b',
        re.IGNORECASE,
    )
    _SIMPLE_PATTERNS = re.compile(
        r'^(what is|who is|define|name|list|when was|where is|translate|convert)\b',
        re.IGNORECASE,
    )

    def detect_complexity(self, prompt: str) -> str:
        """
        Classify prompt complexity using lexical + pattern analysis.

        Returns one of: simple, moderate, complex, critical
        """
        words = prompt.split()
        word_count = len(words)
        sentence_count = max(1, prompt.count('.') + prompt.count('?') + prompt.count('!'))
        unique_ratio = len(set(w.lower() for w in words)) / max(1, word_count)
        tokens_est = estimate_tokens(prompt)

        # Pattern scores
        code_hits = len(self._CODE_PATTERNS.findall(prompt))
        reasoning_hits = len(self._REASONING_PATTERNS.findall(prompt))
        math_hits = len(self._MATH_PATTERNS.findall(prompt))
        simple_hit = bool(self._SIMPLE_PATTERNS.match(prompt.strip()))

        # Composite complexity score (0-100)
        score = 0
        score += min(word_count / 5, 20)          # length contribution (max 20)
        score += min(sentence_count * 3, 15)       # multi-sentence (max 15)
        score += code_hits * 8                      # code signals
        score += reasoning_hits * 6                 # reasoning signals
        score += math_hits * 7                      # math signals
        score += (1 - unique_ratio) * 10            # repetition penalty
        score += min(tokens_est / 100, 15)          # token length

        if simple_hit and score < 25:
            score *= 0.5  # strong simple signal

        # Map score to level
        if score < 15:
            return PromptComplexity.SIMPLE
        elif score < 35:
            return PromptComplexity.MODERATE
        elif score < 60:
            return PromptComplexity.COMPLEX
        else:
            return PromptComplexity.CRITICAL

    # ── 2. Cost Prediction Before Execution  ─────────────────────────────

    def predict_cost(self, prompt: str, model_name: Optional[str] = None) -> CostPrediction:
        """
        Estimate tokens, cost, and latency BEFORE sending the prompt.
        """
        complexity = self.detect_complexity(prompt)
        prompt_tokens = estimate_tokens(prompt)
        response_tokens = estimate_response_tokens(prompt_tokens, complexity)
        total_tokens = prompt_tokens + response_tokens

        recommended = model_name or self.route(prompt)
        profile = self.profiles.get(recommended)

        cost_est = 0.0
        latency_est = 3.0
        if profile:
            cost_est = (
                (prompt_tokens / 1000) * profile.cost_input_per_1k
                + (response_tokens / 1000) * profile.cost_output_per_1k
            )
            latency_est = profile.avg_latency_seconds * (1 + response_tokens / 500)

        # Build alternatives
        alternatives = []
        for name, p in sorted(self.profiles.items(), key=lambda x: x[1].cost_input_per_1k):
            if name == recommended:
                continue
            alt_cost = (
                (prompt_tokens / 1000) * p.cost_input_per_1k
                + (response_tokens / 1000) * p.cost_output_per_1k
            )
            alternatives.append({
                "model": name,
                "cost_estimate": round(alt_cost, 6),
                "latency_estimate": round(p.avg_latency_seconds * (1 + response_tokens / 500), 2),
                "quality_tier": p.quality_tier,
            })

        return CostPrediction(
            prompt_tokens_est=prompt_tokens,
            response_tokens_est=response_tokens,
            total_tokens_est=total_tokens,
            cost_estimate_usd=round(cost_est, 6),
            latency_estimate_seconds=round(latency_est, 2),
            complexity=complexity,
            recommended_model=recommended,
            alternative_models=alternatives[:5],
            timestamp=datetime.now().isoformat(),
        )

    # ── 3. Model Routing ─────────────────────────────────────────────────

    def route(self, prompt: str) -> str:
        """
        Select the best model for this prompt.

        Routing logic:
        - Simple prompts  -> cheapest / fastest model
        - Complex/code    -> strongest available model
        - Long context    -> models with large context windows
        - Budget check    -> downgrade if budget is tight
        - Self-improving  -> boost models with good historical scores
        """
        complexity = self.detect_complexity(prompt)
        tokens = estimate_tokens(prompt)
        needs_code = bool(self._CODE_PATTERNS.findall(prompt))
        needs_reasoning = bool(self._REASONING_PATTERNS.findall(prompt))

        candidates = self._filter_candidates(tokens, complexity, needs_code, needs_reasoning)

        if not candidates:
            # Fallback
            return "meta-llama/Meta-Llama-3-8B-Instruct"

        # Score each candidate
        scored = []
        for name in candidates:
            profile = self.profiles[name]
            score = self._score_candidate(profile, complexity, tokens, needs_code)
            scored.append((name, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    def _filter_candidates(
        self, tokens: int, complexity: str, needs_code: bool, needs_reasoning: bool
    ) -> List[str]:
        """Filter models that can handle this request."""
        candidates = []
        for name, p in self.profiles.items():
            if not p.is_available:
                continue
            if tokens > p.context_window * 0.8:
                continue  # too close to context limit
            if self.prefer_free and p.cost_input_per_1k > 0 and complexity in (
                PromptComplexity.SIMPLE, PromptComplexity.MODERATE
            ):
                continue  # skip paid models for simple tasks when prefer free
            candidates.append(name)
        return candidates

    def _score_candidate(
        self, profile: ModelProfile, complexity: str, tokens: int, needs_code: bool
    ) -> float:
        """Score a candidate model (higher is better)."""
        score = 0.0

        # Quality tier (lower tier number = better quality)
        quality_weight = {
            PromptComplexity.SIMPLE: 0.2,
            PromptComplexity.MODERATE: 0.4,
            PromptComplexity.COMPLEX: 0.7,
            PromptComplexity.CRITICAL: 0.9,
        }
        qw = quality_weight.get(complexity, 0.4)
        score += (4 - profile.quality_tier) * qw * 10  # max 30

        # Cost (lower = better, weighted more for simple tasks)
        total_cost = profile.cost_input_per_1k + profile.cost_output_per_1k
        cost_penalty = total_cost * (1.0 - qw) * 100  # penalize expensive for simple tasks
        score -= cost_penalty

        # Speed bonus for simple tasks
        if complexity == PromptComplexity.SIMPLE:
            score += max(0, 5 - profile.avg_latency_seconds) * 2

        # Strength match
        if needs_code and "code" in profile.strengths:
            score += 10
        if complexity in (PromptComplexity.COMPLEX, PromptComplexity.CRITICAL):
            if "reasoning" in profile.strengths:
                score += 8
            if "complex" in profile.strengths:
                score += 6

        # Context window bonus for long prompts
        if tokens > 2000 and "long_context" in profile.strengths:
            score += 5

        # Self-improving: historical performance bonus
        hist_scores = self._model_scores.get(profile.name, [])
        if hist_scores:
            avg_hist = sum(hist_scores[-20:]) / len(hist_scores[-20:])
            score += avg_hist * 1.5  # bonus for historically good models

        # Budget guard
        if self.budget_limit and self.total_cost > self.budget_limit * 0.8:
            if total_cost > 0:
                score -= 20  # heavy penalty for paid models near budget

        return score

    # ── 4. Self-Improving Router (Feedback Loop) ─────────────────────────

    def record_feedback(
        self,
        prompt: str,
        model_used: str,
        quality_score: float,
        latency_seconds: float = 0.0,
        cost_usd: float = 0.0,
        success: bool = True,
    ):
        """
        Record feedback about a routing decision.
        The router uses this to improve future model selections.
        """
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        fb = RoutingFeedback(
            timestamp=datetime.now().isoformat(),
            prompt_hash=prompt_hash,
            complexity=self.detect_complexity(prompt),
            model_used=model_used,
            quality_score=quality_score,
            latency_seconds=latency_seconds,
            cost_usd=cost_usd,
            success=success,
        )
        self.feedback_history.append(fb)
        self._model_scores[model_used].append(quality_score if success else 0.0)
        self.total_cost += cost_usd

        # Persist periodically (every 10 feedback entries)
        if len(self.feedback_history) % 10 == 0:
            self._save_feedback()

    def get_router_stats(self) -> Dict[str, Any]:
        """Get router performance statistics."""
        stats: Dict[str, Any] = {
            "total_routings": len(self.feedback_history),
            "total_cost": round(self.total_cost, 4),
            "models": {},
        }
        for model, scores in self._model_scores.items():
            stats["models"][model] = {
                "uses": len(scores),
                "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
                "success_rate": round(
                    sum(1 for s in scores if s > 0) / len(scores), 2
                ) if scores else 0,
            }
        return stats

    def _save_feedback(self):
        """Persist feedback history to disk."""
        try:
            self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.feedback_path, "w", encoding="utf-8") as f:
                json.dump(
                    [asdict(fb) for fb in self.feedback_history],
                    f, indent=2,
                )
        except Exception as e:
            logger.warning(f"Could not save feedback: {e}")

    def _load_feedback(self):
        """Load previous feedback from disk."""
        if self.feedback_path.exists():
            try:
                with open(self.feedback_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    fb = RoutingFeedback(**item)
                    self.feedback_history.append(fb)
                    self._model_scores[fb.model_used].append(
                        fb.quality_score if fb.success else 0.0
                    )
                    self.total_cost += fb.cost_usd
                logger.info(f"Loaded {len(data)} feedback records from {self.feedback_path}")
            except Exception as e:
                logger.warning(f"Could not load feedback: {e}")


# ── Convenience import ─────────────────────────────────────────────────
import hashlib  # moved to top-level import area via usage above
