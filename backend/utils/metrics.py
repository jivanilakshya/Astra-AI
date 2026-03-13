"""
Evaluation Metrics Module - Feature 8

Aggregates and analyzes evaluation results from the Judge Agent.
Tracks performance over iterations and provides insights.

Features:
- Aggregate multiple evaluations
- Calculate statistics (mean, std, min, max)
- Track iteration history
- Compare performance across iterations
- Identify improvements and regressions
- Generate summary reports
"""

import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class MetricsCalculator:
    """
    Calculates and tracks evaluation metrics.
    
    Aggregates results from the Judge Agent and provides:
    - Statistical summaries per criterion
    - Composite score tracking
    - Iteration comparisons
    - Improvement analysis
    - Performance trends
    """
    
    def __init__(self):
        """Initialize metrics calculator."""
        self.iteration_history = []
        self.current_iteration = 0
    
    def add_iteration(
        self,
        iteration_num: int,
        evaluations: List[Dict[str, Any]],
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add evaluation results for an iteration.
        
        Args:
            iteration_num: Iteration number
            evaluations: List of evaluation results from Judge Agent
            prompt: Optional prompt used for this iteration
        
        Returns:
            Aggregated metrics for this iteration
        """
        if not evaluations:
            raise ValueError("Evaluations list cannot be empty")
        
        # Calculate aggregated metrics
        metrics = self.calculate_metrics(evaluations)
        
        # Add iteration metadata
        metrics["iteration"] = iteration_num
        metrics["timestamp"] = datetime.now().isoformat()
        metrics["num_evaluations"] = len(evaluations)
        
        if prompt:
            metrics["prompt"] = prompt
            metrics["prompt_length"] = len(prompt)
        
        # Store in history
        self.iteration_history.append(metrics)
        self.current_iteration = iteration_num
        
        return metrics
    
    def calculate_metrics(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate aggregated metrics from evaluations.
        
        Args:
            evaluations: List of evaluation results
        
        Returns:
            Dictionary with aggregated metrics:
                - scores_stats: Statistics per criterion
                - composite_stats: Composite score statistics
                - flags_summary: Count of issues detected
                - suggestions_summary: Common suggestions
        """
        if not evaluations:
            return self._empty_metrics()
        
        # Extract scores
        all_scores = defaultdict(list)
        all_composite = []
        all_flags = []
        all_suggestions = []
        
        for eval_result in evaluations:
            # Collect scores
            scores = eval_result.get("scores", {})
            for criterion, score in scores.items():
                all_scores[criterion].append(float(score))
            
            # Collect composite score
            composite = eval_result.get("composite_score", 0.0)
            all_composite.append(float(composite))
            
            # Collect flags
            flags = eval_result.get("flags", [])
            all_flags.extend(flags)
            
            # Collect suggestions
            suggestions = eval_result.get("suggestions", [])
            all_suggestions.extend(suggestions)
        
        # Calculate statistics per criterion
        scores_stats = {}
        for criterion, scores in all_scores.items():
            scores_stats[criterion] = self._calculate_stats(scores)
        
        # Calculate composite statistics
        composite_stats = self._calculate_stats(all_composite)
        
        # Summarize flags
        flags_summary = self._count_items(all_flags)
        
        # Summarize suggestions
        suggestions_summary = self._count_items(all_suggestions)
        
        return {
            "scores_stats": scores_stats,
            "composite_stats": composite_stats,
            "flags_summary": flags_summary,
            "suggestions_summary": suggestions_summary
        }
    
    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate statistical measures.
        
        Args:
            values: List of numeric values
        
        Returns:
            Dictionary with mean, median, std, min, max
        """
        if not values:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0
            }
        
        return {
            "mean": round(statistics.mean(values), 2),
            "median": round(statistics.median(values), 2),
            "std": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "count": len(values)
        }
    
    def _count_items(self, items: List[str]) -> Dict[str, int]:
        """Count frequency of items."""
        counts = defaultdict(int)
        for item in items:
            counts[item] += 1
        return dict(counts)
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "scores_stats": {},
            "composite_stats": self._calculate_stats([]),
            "flags_summary": {},
            "suggestions_summary": {}
        }
    
    def compare_iterations(
        self,
        iteration1: int,
        iteration2: int
    ) -> Dict[str, Any]:
        """
        Compare two iterations.
        
        Args:
            iteration1: First iteration number
            iteration2: Second iteration number
        
        Returns:
            Dictionary with comparison results:
                - improvements: Criteria that improved
                - regressions: Criteria that got worse
                - delta: Change in composite score
                - percent_change: Percentage change
        """
        # Find iterations in history
        iter1_metrics = self._get_iteration(iteration1)
        iter2_metrics = self._get_iteration(iteration2)
        
        if not iter1_metrics or not iter2_metrics:
            raise ValueError(
                f"One or both iterations not found: {iteration1}, {iteration2}"
            )
        
        # Compare composite scores
        comp1 = iter1_metrics["composite_stats"]["mean"]
        comp2 = iter2_metrics["composite_stats"]["mean"]
        delta = comp2 - comp1
        percent_change = (delta / comp1 * 100) if comp1 > 0 else 0.0
        
        # Compare individual criteria
        improvements = {}
        regressions = {}
        
        scores1 = iter1_metrics["scores_stats"]
        scores2 = iter2_metrics["scores_stats"]
        
        for criterion in scores1.keys():
            if criterion in scores2:
                mean1 = scores1[criterion]["mean"]
                mean2 = scores2[criterion]["mean"]
                change = mean2 - mean1
                
                if change > 0.1:  # Threshold for improvement
                    improvements[criterion] = {
                        "from": mean1,
                        "to": mean2,
                        "change": round(change, 2)
                    }
                elif change < -0.1:  # Threshold for regression
                    regressions[criterion] = {
                        "from": mean1,
                        "to": mean2,
                        "change": round(change, 2)
                    }
        
        return {
            "iteration1": iteration1,
            "iteration2": iteration2,
            "composite_score": {
                "from": comp1,
                "to": comp2,
                "delta": round(delta, 2),
                "percent_change": round(percent_change, 2)
            },
            "improvements": improvements,
            "regressions": regressions
        }
    
    def get_iteration_metrics(self, iteration_num: int) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a specific iteration.
        
        Args:
            iteration_num: Iteration number
        
        Returns:
            Metrics dictionary or None if not found
        """
        return self._get_iteration(iteration_num)
    
    def _get_iteration(self, iteration_num: int) -> Optional[Dict[str, Any]]:
        """Find iteration in history."""
        for metrics in self.iteration_history:
            if metrics.get("iteration") == iteration_num:
                return metrics
        return None
    
    def get_best_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Get the iteration with highest composite score.
        
        Returns:
            Metrics dictionary for best iteration
        """
        if not self.iteration_history:
            return None
        
        best = max(
            self.iteration_history,
            key=lambda x: x["composite_stats"]["mean"]
        )
        return best
    
    def get_performance_trend(self) -> Dict[str, Any]:
        """
        Analyze performance trend across iterations.
        
        Returns:
            Dictionary with:
                - trend: 'improving', 'declining', or 'stable'
                - slope: Average change per iteration
                - total_change: Change from first to last
                - iterations: Number of iterations
        """
        if len(self.iteration_history) < 2:
            return {
                "trend": "insufficient_data",
                "slope": 0.0,
                "total_change": 0.0,
                "iterations": len(self.iteration_history)
            }
        
        # Get composite scores over time
        scores = [
            metrics["composite_stats"]["mean"]
            for metrics in self.iteration_history
        ]
        
        # Calculate simple trend
        first_score = scores[0]
        last_score = scores[-1]
        total_change = last_score - first_score
        
        # Calculate average slope
        iterations = len(scores)
        slope = total_change / (iterations - 1) if iterations > 1 else 0.0
        
        # Determine trend
        if abs(slope) < 0.1:
            trend = "stable"
        elif slope > 0:
            trend = "improving"
        else:
            trend = "declining"
        
        return {
            "trend": trend,
            "slope": round(slope, 3),
            "total_change": round(total_change, 2),
            "iterations": iterations,
            "first_score": round(first_score, 2),
            "last_score": round(last_score, 2)
        }
    
    def check_convergence(
        self,
        threshold: float = 8.5,
        window: int = 3,
        min_improvement: float = 0.02
    ) -> Dict[str, Any]:
        """
        Check if optimization has converged.
        
        Args:
            threshold: Score threshold for convergence
            window: Number of recent iterations to check
            min_improvement: Minimum improvement required
        
        Returns:
            Dictionary with:
                - converged: Boolean
                - reason: Reason for convergence or not
                - current_score: Latest composite score
        """
        if not self.iteration_history:
            return {
                "converged": False,
                "reason": "no_data",
                "current_score": 0.0
            }
        
        # Get recent scores
        recent_scores = [
            metrics["composite_stats"]["mean"]
            for metrics in self.iteration_history[-window:]
        ]
        
        current_score = recent_scores[-1] if recent_scores else 0.0
        
        # Check threshold
        if current_score >= threshold:
            return {
                "converged": True,
                "reason": "threshold_reached",
                "current_score": round(current_score, 2),
                "threshold": threshold
            }
        
        # Check improvement rate
        if len(recent_scores) >= window:
            improvements = [
                recent_scores[i] - recent_scores[i-1]
                for i in range(1, len(recent_scores))
            ]
            
            # All recent improvements below minimum
            if all(imp < min_improvement for imp in improvements):
                return {
                    "converged": True,
                    "reason": "plateau_detected",
                    "current_score": round(current_score, 2),
                    "avg_improvement": round(statistics.mean(improvements), 3)
                }
        
        return {
            "converged": False,
            "reason": "still_improving",
            "current_score": round(current_score, 2)
        }
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary of all iterations.
        
        Returns:
            Dictionary with overall summary
        """
        if not self.iteration_history:
            return {
                "total_iterations": 0,
                "message": "No data available"
            }
        
        # Get all composite scores
        all_composite = [
            metrics["composite_stats"]["mean"]
            for metrics in self.iteration_history
        ]
        
        # Find best and worst
        best_iter = self.get_best_iteration()
        worst_score = min(all_composite)
        
        # Get trend
        trend = self.get_performance_trend()
        
        # Get convergence status
        convergence = self.check_convergence()
        
        # Most common issues
        all_flags = []
        for metrics in self.iteration_history:
            all_flags.extend(metrics.get("flags_summary", {}).keys())
        
        common_issues = self._count_items(all_flags)
        top_issues = sorted(
            common_issues.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_iterations": len(self.iteration_history),
            "best_iteration": {
                "number": best_iter["iteration"],
                "score": best_iter["composite_stats"]["mean"]
            },
            "score_range": {
                "min": round(worst_score, 2),
                "max": round(best_iter["composite_stats"]["mean"], 2),
                "improvement": round(
                    best_iter["composite_stats"]["mean"] - all_composite[0], 2
                )
            },
            "trend": trend,
            "convergence": convergence,
            "top_issues": dict(top_issues),
            "current_iteration": self.current_iteration
        }
    
    def export_history(self) -> List[Dict[str, Any]]:
        """
        Export complete iteration history.
        
        Returns:
            List of all iteration metrics
        """
        return self.iteration_history.copy()
    
    def reset(self):
        """Reset all tracked metrics."""
        self.iteration_history = []
        self.current_iteration = 0


def create_metrics_calculator() -> MetricsCalculator:
    """
    Factory function to create a MetricsCalculator.
    
    Returns:
        New MetricsCalculator instance
    """
    return MetricsCalculator()


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("Metrics Calculator Example - Feature 8")
    print("="*60)
    
    # Create calculator
    calculator = create_metrics_calculator()
    print("\n✅ Created MetricsCalculator")
    
    # Example evaluation results
    evaluations_iter1 = [
        {
            "scores": {"correctness": 7.0, "clarity": 6.0, "reasoning": 6.5,
                      "relevance": 7.5, "conciseness": 7.0},
            "composite_score": 6.8,
            "flags": ["unclear_explanation"],
            "suggestions": ["Improve clarity"]
        },
        {
            "scores": {"correctness": 8.0, "clarity": 7.0, "reasoning": 7.0,
                      "relevance": 8.0, "conciseness": 7.5},
            "composite_score": 7.5,
            "flags": [],
            "suggestions": []
        }
    ]
    
    # Add iteration 1
    metrics1 = calculator.add_iteration(1, evaluations_iter1)
    print(f"\n📊 Iteration 1 Metrics:")
    print(f"   Composite: {metrics1['composite_stats']['mean']:.2f}")
    
    # Example iteration 2 (improved)
    evaluations_iter2 = [
        {
            "scores": {"correctness": 8.5, "clarity": 8.0, "reasoning": 7.5,
                      "relevance": 8.5, "conciseness": 8.0},
            "composite_score": 8.1,
            "flags": [],
            "suggestions": []
        },
        {
            "scores": {"correctness": 9.0, "clarity": 8.5, "reasoning": 8.0,
                      "relevance": 9.0, "conciseness": 8.5},
            "composite_score": 8.6,
            "flags": [],
            "suggestions": []
        }
    ]
    
    metrics2 = calculator.add_iteration(2, evaluations_iter2)
    print(f"\n📊 Iteration 2 Metrics:")
    print(f"   Composite: {metrics2['composite_stats']['mean']:.2f}")
    
    # Compare iterations
    comparison = calculator.compare_iterations(1, 2)
    print(f"\n📈 Comparison:")
    print(f"   Change: {comparison['composite_score']['delta']:.2f}")
    print(f"   Percent: {comparison['composite_score']['percent_change']:.2f}%")
    
    # Get summary
    summary = calculator.generate_summary()
    print(f"\n📋 Summary:")
    print(f"   Total iterations: {summary['total_iterations']}")
    print(f"   Trend: {summary['trend']['trend']}")
    
    print("\n" + "="*60)
