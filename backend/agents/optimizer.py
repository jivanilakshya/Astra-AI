"""
Optimizer Agent - Automatic prompt optimization based on feedback.

This agent analyzes judge feedback and performance metrics to iteratively
improve prompts and DSPy modules using:
- Feedback-driven prompt refinement
- DSPy teleprompter optimization
- Prompt evolution tracking
- Convergence detection
"""

from typing import List, Dict, Any, Optional, Tuple
import dspy
from dataclasses import dataclass, asdict
import logging
from datetime import datetime
import json
from pathlib import Path

from dspy_modules.signatures import PromptOptimization
from dspy_modules.teleprompter import TeleprompterManager

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    """Represents a version of a prompt with metadata."""
    version: int
    prompt_text: str
    performance_score: float
    modifications: List[str]
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class OptimizationResult:
    """Result of a prompt optimization operation."""
    success: bool
    optimized_prompt: str
    modifications: List[str]
    expected_improvements: List[str]
    rationale: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class OptimizerAgent:
    """
    Agent for automatic prompt and module optimization.
    
    Combines feedback analysis, prompt engineering, and DSPy teleprompters
    to progressively improve system performance.
    """
    
    def __init__(
        self,
        teleprompter: Optional[TeleprompterManager] = None,
        improvement_threshold: float = 0.02,
        max_history: int = 20
    ):
        """
        Initialize Optimizer Agent.
        
        Args:
            teleprompter: Optional TeleprompterManager for module optimization
            improvement_threshold: Minimum improvement to consider convergence
            max_history: Maximum number of prompt versions to keep in history
        """
        self.teleprompter = teleprompter
        self.improvement_threshold = improvement_threshold
        self.max_history = max_history
        
        # Prompt evolution tracking
        self.prompt_history: List[PromptVersion] = []
        self.current_version = 0
        
        # DSPy module for prompt optimization
        self.prompt_optimizer = dspy.Predict(PromptOptimization)
        
        logger.info("OptimizerAgent initialized")
    
    def analyze_feedback(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze judge evaluations to identify improvement areas.
        
        Args:
            evaluations: List of judge evaluation results
        
        Returns:
            Dictionary with analysis:
                - weak_areas: Criteria with low scores
                - strong_areas: Criteria with high scores
                - avg_scores: Average scores by criterion
                - common_suggestions: Frequent suggestions
                - issues: Common issues flagged
        """
        if not evaluations:
            logger.warning("No evaluations provided for analysis")
            return {
                "weak_areas": [],
                "strong_areas": [],
                "avg_scores": {},
                "common_suggestions": [],
                "issues": []
            }
        
        # Aggregate scores by criterion
        criteria = ["correctness", "clarity", "reasoning", "relevance", "conciseness"]
        score_aggregates = {criterion: [] for criterion in criteria}
        
        all_suggestions = []
        all_issues = []
        
        for eval in evaluations:
            if "scores" not in eval:
                continue
            
            for criterion in criteria:
                if criterion in eval["scores"]:
                    score_aggregates[criterion].append(eval["scores"][criterion])
            
            # Collect suggestions and issues
            all_suggestions.extend(eval.get("suggestions", []))
            all_issues.extend(eval.get("issues", []))
        
        # Calculate averages
        avg_scores = {}
        for criterion, scores in score_aggregates.items():
            if scores:
                avg_scores[criterion] = sum(scores) / len(scores)
            else:
                avg_scores[criterion] = 0.0
        
        # Identify weak areas (< 7.0) and strong areas (>= 8.0)
        weak_areas = [
            criterion for criterion, score in avg_scores.items()
            if score < 7.0
        ]
        
        strong_areas = [
            criterion for criterion, score in avg_scores.items()
            if score >= 8.0
        ]
        
        # Find common suggestions and issues
        from collections import Counter
        suggestion_counts = Counter(all_suggestions)
        issue_counts = Counter(all_issues)
        
        common_suggestions = [
            sugg for sugg, count in suggestion_counts.most_common(5)
        ]
        
        common_issues = [
            issue for issue, count in issue_counts.most_common(5)
        ]
        
        analysis = {
            "weak_areas": weak_areas,
            "strong_areas": strong_areas,
            "avg_scores": avg_scores,
            "common_suggestions": common_suggestions,
            "issues": common_issues
        }
        
        logger.info(f"Feedback analysis: {len(weak_areas)} weak areas identified")
        return analysis
    
    def optimize_prompt(
        self,
        current_prompt: str,
        evaluations: List[Dict[str, Any]],
        performance_score: float
    ) -> OptimizationResult:
        """
        Generate optimized prompt based on feedback analysis.
        
        Args:
            current_prompt: Current prompt template
            evaluations: List of judge evaluations
            performance_score: Current performance score
        
        Returns:
            OptimizationResult with optimized prompt and metadata
        """
        # Analyze feedback
        analysis = self.analyze_feedback(evaluations)
        
        if not analysis["weak_areas"] and performance_score >= 8.5:
            logger.info("No optimization needed - performance is excellent")
            return OptimizationResult(
                success=True,
                optimized_prompt=current_prompt,
                modifications=[],
                expected_improvements=[],
                rationale="Current prompt is already performing well",
                confidence=1.0
            )
        
        # Build optimization context
        weak_areas_str = ", ".join(analysis["weak_areas"]) if analysis["weak_areas"] else "None"
        suggestions_str = "; ".join(analysis["common_suggestions"][:3]) if analysis["common_suggestions"] else "None"
        issues_str = "; ".join(analysis["issues"][:3]) if analysis["issues"] else "None"
        
        optimization_context = f"""
Current Performance: {performance_score:.2f}/10

Weak Areas: {weak_areas_str}
Common Suggestions: {suggestions_str}
Issues Identified: {issues_str}

Average Scores:
- Correctness: {analysis['avg_scores'].get('correctness', 0):.2f}
- Clarity: {analysis['avg_scores'].get('clarity', 0):.2f}
- Reasoning: {analysis['avg_scores'].get('reasoning', 0):.2f}
- Relevance: {analysis['avg_scores'].get('relevance', 0):.2f}
- Conciseness: {analysis['avg_scores'].get('conciseness', 0):.2f}
"""
        
        try:
            # Use DSPy PromptOptimization signature
            result = self.prompt_optimizer(
                current_prompt=current_prompt,
                performance_feedback=optimization_context
            )
            
            # Extract optimized prompt and metadata
            optimized_prompt = result.optimized_prompt if hasattr(result, 'optimized_prompt') else current_prompt
            modifications = result.modifications if hasattr(result, 'modifications') else []
            rationale = result.rationale if hasattr(result, 'rationale') else "Optimization applied"
            
            # Parse modifications if it's a string
            if isinstance(modifications, str):
                modifications = [m.strip() for m in modifications.split('\n') if m.strip()]
            
            logger.info(f"Prompt optimized with {len(modifications)} modifications")
            
            return OptimizationResult(
                success=True,
                optimized_prompt=optimized_prompt,
                modifications=modifications,
                expected_improvements=analysis["weak_areas"],
                rationale=rationale,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error during prompt optimization: {e}")
            
            # Fallback: rule-based optimization
            return self._fallback_optimization(
                current_prompt,
                analysis,
                performance_score
            )
    
    def _fallback_optimization(
        self,
        current_prompt: str,
        analysis: Dict[str, Any],
        performance_score: float
    ) -> OptimizationResult:
        """
        Fallback rule-based optimization when DSPy fails.
        
        Args:
            current_prompt: Current prompt
            analysis: Feedback analysis
            performance_score: Current score
        
        Returns:
            OptimizationResult with rule-based improvements
        """
        modifications = []
        optimized_prompt = current_prompt
        
        # Add clarity instructions if clarity is weak
        if "clarity" in analysis["weak_areas"]:
            if "Use clear" not in optimized_prompt:
                optimized_prompt += "\n\nUse clear, simple language that is easy to understand."
                modifications.append("Added clarity requirement")
        
        # Add reasoning instructions if reasoning is weak
        if "reasoning" in analysis["weak_areas"]:
            if "step-by-step" not in optimized_prompt.lower():
                optimized_prompt += "\nExplain your reasoning step-by-step."
                modifications.append("Added step-by-step reasoning requirement")
        
        # Add conciseness requirement if conciseness is weak
        if "conciseness" in analysis["weak_areas"]:
            if "concise" not in optimized_prompt.lower():
                optimized_prompt += "\nBe concise and avoid unnecessary verbosity."
                modifications.append("Added conciseness requirement")
        
        # Add accuracy emphasis if correctness is weak
        if "correctness" in analysis["weak_areas"]:
            if "accurate" not in optimized_prompt.lower():
                optimized_prompt += "\nEnsure all information is factually accurate."
                modifications.append("Added accuracy emphasis")
        
        logger.info(f"Fallback optimization applied {len(modifications)} modifications")
        
        return OptimizationResult(
            success=True,
            optimized_prompt=optimized_prompt,
            modifications=modifications,
            expected_improvements=analysis["weak_areas"],
            rationale="Applied rule-based optimization due to DSPy unavailability",
            confidence=0.6
        )
    
    def add_to_history(
        self,
        prompt: str,
        performance_score: float,
        modifications: List[str]
    ) -> None:
        """
        Add prompt version to history.
        
        Args:
            prompt: Prompt text
            performance_score: Performance score
            modifications: List of modifications made
        """
        self.current_version += 1
        
        version = PromptVersion(
            version=self.current_version,
            prompt_text=prompt,
            performance_score=performance_score,
            modifications=modifications,
            timestamp=datetime.now().isoformat()
        )
        
        self.prompt_history.append(version)
        
        # Keep only max_history versions
        if len(self.prompt_history) > self.max_history:
            self.prompt_history = self.prompt_history[-self.max_history:]
        
        logger.debug(f"Added prompt version {self.current_version} to history")
    
    def get_best_prompt(self) -> Optional[PromptVersion]:
        """
        Get the best performing prompt from history.
        
        Returns:
            PromptVersion with highest performance score, or None if no history
        """
        if not self.prompt_history:
            return None
        
        return max(self.prompt_history, key=lambda v: v.performance_score)
    
    def check_convergence(self, recent_scores: List[float], window: int = 3) -> bool:
        """
        Check if optimization has converged.
        
        Convergence is detected when improvement rate is below threshold
        for a window of recent iterations.
        
        Args:
            recent_scores: List of recent performance scores
            window: Number of recent scores to consider
        
        Returns:
            True if converged, False otherwise
        """
        if len(recent_scores) < window + 1:
            return False
        
        # Calculate improvement rates for recent window
        improvements = []
        for i in range(len(recent_scores) - window, len(recent_scores)):
            if i > 0:
                improvement = recent_scores[i] - recent_scores[i - 1]
                improvements.append(improvement)
        
        # Check if all improvements are below threshold
        if all(imp < self.improvement_threshold for imp in improvements):
            logger.info("Convergence detected: improvements below threshold")
            return True
        
        return False
    
    def rollback_to_best(self) -> Optional[str]:
        """
        Rollback to the best performing prompt in history.
        
        Returns:
            Best prompt text, or None if no history
        """
        best_version = self.get_best_prompt()
        
        if best_version:
            logger.info(
                f"Rolling back to version {best_version.version} "
                f"(score: {best_version.performance_score:.2f})"
            )
            return best_version.prompt_text
        
        return None
    
    def optimize_module_with_teleprompter(
        self,
        module: dspy.Module,
        method: str = "bootstrap"
    ) -> dspy.Module:
        """
        Optimize DSPy module using teleprompter.
        
        Args:
            module: DSPy module to optimize
            method: Optimization method ("bootstrap" or "mipro")
        
        Returns:
            Optimized module (or original if optimization fails)
        """
        if not self.teleprompter:
            logger.warning("No teleprompter configured - returning original module")
            return module
        
        if method == "bootstrap":
            optimized = self.teleprompter.optimize_with_bootstrap(module)
        elif method == "mipro":
            optimized = self.teleprompter.optimize_with_mipro(module)
        else:
            logger.error(f"Unknown optimization method: {method}")
            return module
        
        logger.info(f"Module optimized using {method}")
        return optimized
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        Get full optimization history.
        
        Returns:
            List of prompt versions as dictionaries
        """
        return [version.to_dict() for version in self.prompt_history]
    
    def save_history(self, filepath: str) -> None:
        """
        Save optimization history to JSON file.
        
        Args:
            filepath: Path to save file
        """
        try:
            data = {
                "current_version": self.current_version,
                "history": self.get_optimization_history()
            }
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Optimization history saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def load_history(self, filepath: str) -> None:
        """
        Load optimization history from JSON file.
        
        Args:
            filepath: Path to load from
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_version = data.get("current_version", 0)
            
            history_data = data.get("history", [])
            self.prompt_history = [
                PromptVersion(**version) for version in history_data
            ]
            
            logger.info(
                f"Loaded {len(self.prompt_history)} versions from {filepath}"
            )
            
        except Exception as e:
            logger.error(f"Error loading history: {e}")
    
    def clear_history(self) -> None:
        """Clear optimization history."""
        self.prompt_history.clear()
        self.current_version = 0
        logger.info("Optimization history cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get optimization statistics.
        
        Returns:
            Dictionary with statistics:
                - num_versions: Number of prompt versions
                - current_version: Current version number
                - best_score: Best performance score
                - avg_improvement: Average improvement per iteration
                - total_improvement: Total improvement from first to best
        """
        if not self.prompt_history:
            return {
                "num_versions": 0,
                "current_version": 0,
                "best_score": 0.0,
                "avg_improvement": 0.0,
                "total_improvement": 0.0
            }
        
        scores = [v.performance_score for v in self.prompt_history]
        best_score = max(scores)
        
        # Calculate average improvement
        improvements = []
        for i in range(1, len(scores)):
            improvements.append(scores[i] - scores[i - 1])
        
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
        total_improvement = scores[-1] - scores[0] if len(scores) > 1 else 0.0
        
        return {
            "num_versions": len(self.prompt_history),
            "current_version": self.current_version,
            "best_score": best_score,
            "avg_improvement": avg_improvement,
            "total_improvement": total_improvement
        }


def create_optimizer(
    teleprompter: Optional[TeleprompterManager] = None,
    improvement_threshold: float = 0.02,
    max_history: int = 20
) -> OptimizerAgent:
    """
    Factory function to create OptimizerAgent.
    
    Args:
        teleprompter: Optional TeleprompterManager
        improvement_threshold: Convergence threshold
        max_history: Max versions to keep
    
    Returns:
        OptimizerAgent instance
    
    Example:
        >>> from dspy_modules import create_teleprompter
        >>> teleprompter = create_teleprompter()
        >>> optimizer = create_optimizer(teleprompter=teleprompter)
        >>> result = optimizer.optimize_prompt(prompt, evaluations, score)
    """
    return OptimizerAgent(
        teleprompter=teleprompter,
        improvement_threshold=improvement_threshold,
        max_history=max_history
    )
