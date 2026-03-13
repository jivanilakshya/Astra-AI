"""
Multi-Model Comparison Engine

Sends the same prompt to multiple LLMs and produces side-by-side evaluation:
- Response quality (via Judge Agent metrics)
- Latency
- Cost estimate
- Token usage
- Accuracy heuristic
- Consistency score (agreement between models)

Usage:
    from utils.multi_model import MultiModelEngine
    engine = MultiModelEngine()
    results = engine.compare(prompt, models=["meta-llama/Meta-Llama-3-8B-Instruct", ...])
"""

import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field
from pathlib import Path

from agents.huggingface_provider import HuggingFaceProvider

import logging
logger = logging.getLogger(__name__)


# ── Token estimation (heuristic: ~4 chars per token for English) ─────────────
def estimate_tokens(text: str) -> int:
    """Rough token count estimation (4 chars ≈ 1 token)."""
    return max(1, len(text) // 4)


# ── Model pricing lookup ────────────────────────────────────────────────────
MODEL_COST_PER_1K = {
    # HuggingFace free-tier models (verified working)
    "meta-llama/Meta-Llama-3-8B-Instruct": {"input": 0.0, "output": 0.0},
    "mistralai/Mistral-7B-Instruct-v0.2": {"input": 0.0, "output": 0.0},
    "Qwen/Qwen2.5-72B-Instruct": {"input": 0.0, "output": 0.0},
    "Qwen/Qwen2.5-Coder-32B-Instruct": {"input": 0.0, "output": 0.0},
    "Qwen/Qwen2.5-7B-Instruct": {"input": 0.0, "output": 0.0},
    "meta-llama/Llama-3.2-3B-Instruct": {"input": 0.0, "output": 0.0},
    "meta-llama/Llama-3.2-1B-Instruct": {"input": 0.0, "output": 0.0},
    # OpenAI (for reference if user adds keys)
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    # Anthropic
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
}


@dataclass
class ModelResult:
    """Result from a single model for a single prompt."""
    model_name: str
    response_text: str
    success: bool
    latency_seconds: float
    input_tokens_est: int
    output_tokens_est: int
    cost_estimate: float
    error: Optional[str] = None
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComparisonReport:
    """Full comparison across models for one prompt."""
    prompt: str
    timestamp: str
    models: List[str]
    results: List[ModelResult]
    consistency_score: float  # 0-1: how much models agree
    ranking: List[Dict[str, Any]]  # ordered best → worst
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MultiModelEngine:
    """
    Sends the same prompt to multiple LLMs and compares results.
    """

    # Default models to compare (all free HuggingFace Inference API)
    DEFAULT_MODELS = [
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "Qwen/Qwen2.5-7B-Instruct",
    ]

    def __init__(self, provider: Optional[HuggingFaceProvider] = None):
        self.provider = provider or HuggingFaceProvider()
        self.history: List[ComparisonReport] = []

    # ── Core compare method ──────────────────────────────────────────────
    def compare(
        self,
        prompt: str,
        models: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        optimized_prompt: Optional[str] = None,
    ) -> ComparisonReport:
        """
        Send *prompt* to every model in *models* and return a ComparisonReport.
        
        If optimized_prompt is provided, it is used as the actual prompt sent to
        models, while the original prompt is kept for display/logging.
        """
        models = models or self.DEFAULT_MODELS
        results: List[ModelResult] = []
        
        # Use optimized prompt for generation if provided
        actual_prompt = optimized_prompt or prompt

        for model_name in models:
            result = self._query_model(model_name, actual_prompt, temperature, max_tokens)
            results.append(result)

        # Calculate consistency (simple: Jaccard-like overlap of words)
        consistency = self._calculate_consistency(results)

        # Build ranking (by a heuristic quality score)
        ranking = self._rank_results(results)

        # Summary text
        summary = self._generate_summary(results, consistency, ranking)

        report = ComparisonReport(
            prompt=prompt,
            timestamp=datetime.now().isoformat(),
            models=models,
            results=results,
            consistency_score=consistency,
            ranking=ranking,
            summary=summary,
        )
        self.history.append(report)
        return report

    # ── Internal helpers ─────────────────────────────────────────────────

    def _query_model(
        self, model_name: str, prompt: str, temperature: float, max_tokens: int
    ) -> ModelResult:
        """Query a single model."""
        input_tokens = estimate_tokens(prompt)
        start = time.time()

        try:
            resp = self.provider.generate(
                model_name=model_name,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            latency = time.time() - start
            text = resp.get("text", "")
            success = resp.get("success", False)
            output_tokens = estimate_tokens(text)
            cost = self._estimate_cost(model_name, input_tokens, output_tokens)

            return ModelResult(
                model_name=model_name,
                response_text=text,
                success=success,
                latency_seconds=latency,
                input_tokens_est=input_tokens,
                output_tokens_est=output_tokens,
                cost_estimate=cost,
                error=resp.get("error"),
                timestamp=datetime.now().isoformat(),
            )
        except Exception as e:
            latency = time.time() - start
            return ModelResult(
                model_name=model_name,
                response_text="",
                success=False,
                latency_seconds=latency,
                input_tokens_est=input_tokens,
                output_tokens_est=0,
                cost_estimate=0.0,
                error=str(e),
                timestamp=datetime.now().isoformat(),
            )

    def _estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD."""
        pricing = MODEL_COST_PER_1K.get(model_name, {"input": 0.0, "output": 0.0})
        return (input_tokens / 1000) * pricing["input"] + (output_tokens / 1000) * pricing["output"]

    def _calculate_consistency(self, results: List[ModelResult]) -> float:
        """
        Measure agreement between model responses.
        Uses word-set Jaccard similarity averaged over all pairs.
        """
        successful = [r for r in results if r.success and r.response_text]
        if len(successful) < 2:
            return 0.0

        word_sets = [set(r.response_text.lower().split()) for r in successful]
        pair_scores = []
        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                intersection = word_sets[i] & word_sets[j]
                union = word_sets[i] | word_sets[j]
                if union:
                    pair_scores.append(len(intersection) / len(union))
        return sum(pair_scores) / len(pair_scores) if pair_scores else 0.0

    def _rank_results(self, results: List[ModelResult]) -> List[Dict[str, Any]]:
        """
        Rank models by a heuristic quality score.
        Score = response_length_norm * 0.3 + speed_norm * 0.3 + cost_norm * 0.2 + success * 0.2
        """
        scored = []
        # Norms
        max_len = max((len(r.response_text) for r in results if r.success), default=1) or 1
        max_lat = max((r.latency_seconds for r in results), default=1) or 1
        max_cost = max((r.cost_estimate for r in results), default=1) or 1

        for r in results:
            if not r.success:
                scored.append({"model": r.model_name, "score": 0.0, "status": "failed"})
                continue

            length_norm = min(len(r.response_text) / max_len, 1.0)
            speed_norm = 1.0 - min(r.latency_seconds / max_lat, 1.0)
            cost_norm = 1.0 - min(r.cost_estimate / max_cost, 1.0) if max_cost > 0 else 1.0
            quality = length_norm * 0.3 + speed_norm * 0.3 + cost_norm * 0.2 + 0.2

            scored.append({
                "model": r.model_name,
                "score": round(quality, 3),
                "latency": round(r.latency_seconds, 2),
                "tokens": r.output_tokens_est,
                "cost": round(r.cost_estimate, 6),
                "status": "success",
            })

        return sorted(scored, key=lambda x: x["score"], reverse=True)

    def _generate_summary(
        self, results: List[ModelResult], consistency: float, ranking: List[Dict]
    ) -> str:
        """Generate human-readable summary."""
        lines = []
        lines.append(f"Compared {len(results)} models  |  Consistency: {consistency:.0%}")
        for i, r in enumerate(ranking, 1):
            status = "OK" if r["status"] == "success" else "FAIL"
            lines.append(
                f"  #{i}  {r['model']:45s}  score={r['score']:.2f}  [{status}]"
            )
        if ranking and ranking[0]["status"] == "success":
            lines.append(f"Best model: {ranking[0]['model']}")
        return "\n".join(lines)

    # ── Export ───────────────────────────────────────────────────────────
    def export_history(self, filepath: str):
        """Export comparison history to JSON."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.history], f, indent=2)
