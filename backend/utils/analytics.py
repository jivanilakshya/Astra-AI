"""
Analytics Agent - Visualization and reporting for optimization metrics.

This agent provides:
- Performance tracking and trend analysis
- Visualization generation (charts, plots)
- Comprehensive reporting
- Data export (JSON, CSV)
- Anomaly detection
- Insights and recommendations
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import csv
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Optional matplotlib import for visualization
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available - visualization disabled")


@dataclass
class IterationLog:
    """Log entry for a single optimization iteration."""
    iteration: int
    timestamp: str
    prompt: str
    prompt_length: int
    num_questions: int
    avg_composite_score: float
    scores_by_criterion: Dict[str, float]
    best_score: float
    worst_score: float
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AnalyticsAgent:
    """
    Agent for tracking, analyzing, and visualizing optimization metrics.
    """
    
    def __init__(self, storage_path: str = "./analytics"):
        """
        Initialize Analytics Agent.
        
        Args:
            storage_path: Directory for storing logs and visualizations
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.iteration_logs: List[IterationLog] = []
        self.anomalies: List[Dict[str, Any]] = []
        
        logger.info(f"AnalyticsAgent initialized with storage: {storage_path}")
    
    def log_iteration(
        self,
        iteration: int,
        prompt: str,
        evaluations: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a complete optimization iteration.
        
        Args:
            iteration: Iteration number
            prompt: Current prompt text
            evaluations: List of evaluation results from Judge
            metadata: Optional additional metadata
        """
        if not evaluations:
            logger.warning(f"No evaluations for iteration {iteration}")
            return
        
        # Calculate aggregate metrics
        composite_scores = [e.get("composite_score", 0.0) for e in evaluations]
        avg_composite = sum(composite_scores) / len(composite_scores) if composite_scores else 0.0
        
        # Aggregate scores by criterion
        criteria = ["correctness", "clarity", "reasoning", "relevance", "conciseness"]
        scores_by_criterion = {}
        
        for criterion in criteria:
            scores = []
            for eval in evaluations:
                if "scores" in eval and criterion in eval["scores"]:
                    scores.append(eval["scores"][criterion])
            
            if scores:
                scores_by_criterion[criterion] = sum(scores) / len(scores)
            else:
                scores_by_criterion[criterion] = 0.0
        
        # Create log entry
        log_entry = IterationLog(
            iteration=iteration,
            timestamp=datetime.now().isoformat(),
            prompt=prompt,
            prompt_length=len(prompt),
            num_questions=len(evaluations),
            avg_composite_score=avg_composite,
            scores_by_criterion=scores_by_criterion,
            best_score=max(composite_scores) if composite_scores else 0.0,
            worst_score=min(composite_scores) if composite_scores else 0.0,
            metadata=metadata
        )
        
        self.iteration_logs.append(log_entry)
        logger.info(f"Logged iteration {iteration}: avg_score={avg_composite:.3f}")
        
        # Check for anomalies
        self._detect_anomalies(log_entry)
    
    def _detect_anomalies(self, log_entry: IterationLog) -> None:
        """
        Detect anomalies in iteration performance.
        
        Args:
            log_entry: Current iteration log
        """
        if len(self.iteration_logs) < 2:
            return
        
        # Check for significant performance drop
        prev_score = self.iteration_logs[-2].avg_composite_score
        current_score = log_entry.avg_composite_score
        
        if current_score < prev_score - 1.0:  # Drop of > 1.0
            anomaly = {
                "iteration": log_entry.iteration,
                "type": "performance_drop",
                "previous_score": prev_score,
                "current_score": current_score,
                "drop": prev_score - current_score,
                "timestamp": log_entry.timestamp
            }
            self.anomalies.append(anomaly)
            logger.warning(f"Anomaly detected: Performance drop at iteration {log_entry.iteration}")
        
        # Check for unusually long prompt
        avg_prompt_length = sum(log.prompt_length for log in self.iteration_logs[:-1]) / (len(self.iteration_logs) - 1)
        
        if log_entry.prompt_length > avg_prompt_length * 2:
            anomaly = {
                "iteration": log_entry.iteration,
                "type": "prompt_length_spike",
                "avg_length": avg_prompt_length,
                "current_length": log_entry.prompt_length,
                "timestamp": log_entry.timestamp
            }
            self.anomalies.append(anomaly)
            logger.warning(f"Anomaly detected: Prompt length spike at iteration {log_entry.iteration}")
    
    def get_performance_trend(self, window: int = 3) -> str:
        """
        Analyze performance trend over recent iterations.
        
        Args:
            window: Number of recent iterations to analyze
        
        Returns:
            Trend description: "improving", "declining", "stable", or "insufficient_data"
        """
        if len(self.iteration_logs) < window + 1:
            return "insufficient_data"
        
        recent_scores = [
            log.avg_composite_score 
            for log in self.iteration_logs[-window:]
        ]
        
        # Calculate trend
        improvements = []
        for i in range(1, len(recent_scores)):
            improvements.append(recent_scores[i] - recent_scores[i - 1])
        
        avg_improvement = sum(improvements) / len(improvements)
        
        if avg_improvement > 0.1:
            return "improving"
        elif avg_improvement < -0.1:
            return "declining"
        else:
            return "stable"
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary report.
        
        Returns:
            Dictionary with summary statistics and insights
        """
        if not self.iteration_logs:
            return {"error": "No data available for reporting"}
        
        # Overall statistics
        all_scores = [log.avg_composite_score for log in self.iteration_logs]
        
        initial_score = self.iteration_logs[0].avg_composite_score
        final_score = self.iteration_logs[-1].avg_composite_score
        total_improvement = final_score - initial_score
        
        best_iteration = max(self.iteration_logs, key=lambda x: x.avg_composite_score)
        worst_iteration = min(self.iteration_logs, key=lambda x: x.avg_composite_score)
        
        # Criterion-specific analysis
        criterion_trends = {}
        criteria = ["correctness", "clarity", "reasoning", "relevance", "conciseness"]
        
        for criterion in criteria:
            initial = self.iteration_logs[0].scores_by_criterion.get(criterion, 0.0)
            final = self.iteration_logs[-1].scores_by_criterion.get(criterion, 0.0)
            improvement = final - initial
            
            criterion_trends[criterion] = {
                "initial": initial,
                "final": final,
                "improvement": improvement,
                "trend": "improved" if improvement > 0.1 else "declined" if improvement < -0.1 else "stable"
            }
        
        # Performance trend
        trend = self.get_performance_trend()
        
        # Generate insights
        insights = self._generate_insights()
        
        report = {
            "summary": {
                "total_iterations": len(self.iteration_logs),
                "initial_score": initial_score,
                "final_score": final_score,
                "total_improvement": total_improvement,
                "improvement_percentage": (total_improvement / initial_score * 100) if initial_score > 0 else 0,
                "best_score": best_iteration.avg_composite_score,
                "best_iteration": best_iteration.iteration,
                "worst_score": worst_iteration.avg_composite_score,
                "worst_iteration": worst_iteration.iteration,
                "current_trend": trend
            },
            "criterion_analysis": criterion_trends,
            "anomalies": self.anomalies,
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Summary report generated")
        return report
    
    def _generate_insights(self) -> List[str]:
        """
        Generate actionable insights from data.
        
        Returns:
            List of insight strings
        """
        insights = []
        
        if not self.iteration_logs:
            return ["Insufficient data for insights"]
        
        # Check overall improvement
        initial = self.iteration_logs[0].avg_composite_score
        final = self.iteration_logs[-1].avg_composite_score
        
        if final > initial + 1.0:
            insights.append(f"Strong optimization success: {final - initial:.2f} point improvement")
        elif final < initial:
            insights.append(f"Warning: Performance declined by {initial - final:.2f} points")
        
        # Check for convergence
        trend = self.get_performance_trend()
        if trend == "stable":
            insights.append("Optimization has converged - further improvements unlikely")
        elif trend == "improving":
            insights.append("Optimization still improving - continue iterations")
        elif trend == "declining":
            insights.append("Performance declining - consider reverting to previous prompt")
        
        # Identify weakest criterion
        final_log = self.iteration_logs[-1]
        weakest_criterion = min(
            final_log.scores_by_criterion.items(),
            key=lambda x: x[1]
        )
        
        if weakest_criterion[1] < 7.0:
            insights.append(f"Focus on improving '{weakest_criterion[0]}' (current: {weakest_criterion[1]:.2f})")
        
        # Check for anomalies
        if self.anomalies:
            insights.append(f"{len(self.anomalies)} anomalies detected - review iteration logs")
        
        return insights
    
    def generate_visualization(
        self,
        output_path: Optional[str] = None,
        show: bool = False
    ) -> Optional[str]:
        """
        Generate performance visualization charts.
        
        Args:
            output_path: Path to save chart (default: storage_path/performance_chart.png)
            show: Whether to display chart (default: False)
        
        Returns:
            Path to saved chart, or None if matplotlib unavailable
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("matplotlib not available - cannot generate visualization")
            return None
        
        if not self.iteration_logs:
            logger.warning("No data available for visualization")
            return None
        
        if output_path is None:
            output_path = str(self.storage_path / "performance_chart.png")
        
        # Extract data
        iterations = [log.iteration for log in self.iteration_logs]
        composite_scores = [log.avg_composite_score for log in self.iteration_logs]
        
        # Create figure with multiple subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Optimization Performance Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Composite score over iterations
        ax1 = axes[0, 0]
        ax1.plot(iterations, composite_scores, marker='o', linewidth=2, markersize=6)
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Average Composite Score')
        ax1.set_title('Performance Over Time')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 10)
        
        # Plot 2: Scores by criterion (latest iteration)
        ax2 = axes[0, 1]
        latest_log = self.iteration_logs[-1]
        criteria = list(latest_log.scores_by_criterion.keys())
        scores = list(latest_log.scores_by_criterion.values())
        
        bars = ax2.bar(criteria, scores, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
        ax2.set_ylabel('Score')
        ax2.set_title(f'Criterion Scores (Iteration {latest_log.iteration})')
        ax2.set_ylim(0, 10)
        ax2.axhline(y=7.0, color='r', linestyle='--', alpha=0.5, label='Target (7.0)')
        ax2.legend()
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontsize=9)
        
        # Plot 3: Improvement trend
        ax3 = axes[1, 0]
        if len(iterations) > 1:
            improvements = [composite_scores[i] - composite_scores[i-1] 
                          for i in range(1, len(composite_scores))]
            ax3.bar(iterations[1:], improvements, 
                   color=['green' if x > 0 else 'red' for x in improvements])
            ax3.set_xlabel('Iteration')
            ax3.set_ylabel('Score Change')
            ax3.set_title('Iteration-to-Iteration Improvement')
            ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax3.grid(True, alpha=0.3)
        
        # Plot 4: Prompt length trend
        ax4 = axes[1, 1]
        prompt_lengths = [log.prompt_length for log in self.iteration_logs]
        ax4.plot(iterations, prompt_lengths, marker='s', color='purple', linewidth=2)
        ax4.set_xlabel('Iteration')
        ax4.set_ylabel('Prompt Length (characters)')
        ax4.set_title('Prompt Evolution')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"Visualization saved to {output_path}")
        
        if show:
            plt.show()
        
        plt.close()
        
        return output_path
    
    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """
        Export all logs to JSON file.
        
        Args:
            filepath: Output path (default: storage_path/analytics.json)
        
        Returns:
            Path to exported file
        """
        if filepath is None:
            filepath = str(self.storage_path / "analytics.json")
        
        data = {
            "iteration_logs": [log.to_dict() for log in self.iteration_logs],
            "anomalies": self.anomalies,
            "summary": self.generate_summary_report(),
            "export_timestamp": datetime.now().isoformat()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analytics exported to JSON: {filepath}")
        return filepath
    
    def export_to_csv(self, filepath: Optional[str] = None) -> str:
        """
        Export iteration logs to CSV file.
        
        Args:
            filepath: Output path (default: storage_path/analytics.csv)
        
        Returns:
            Path to exported file
        """
        if filepath is None:
            filepath = str(self.storage_path / "analytics.csv")
        
        if not self.iteration_logs:
            logger.warning("No data to export to CSV")
            return filepath
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            # Create CSV writer
            fieldnames = [
                'iteration', 'timestamp', 'avg_composite_score',
                'correctness', 'clarity', 'reasoning', 'relevance', 'conciseness',
                'best_score', 'worst_score', 'prompt_length', 'num_questions'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in self.iteration_logs:
                row = {
                    'iteration': log.iteration,
                    'timestamp': log.timestamp,
                    'avg_composite_score': log.avg_composite_score,
                    'correctness': log.scores_by_criterion.get('correctness', 0),
                    'clarity': log.scores_by_criterion.get('clarity', 0),
                    'reasoning': log.scores_by_criterion.get('reasoning', 0),
                    'relevance': log.scores_by_criterion.get('relevance', 0),
                    'conciseness': log.scores_by_criterion.get('conciseness', 0),
                    'best_score': log.best_score,
                    'worst_score': log.worst_score,
                    'prompt_length': log.prompt_length,
                    'num_questions': log.num_questions
                }
                writer.writerow(row)
        
        logger.info(f"Analytics exported to CSV: {filepath}")
        return filepath
    
    def load_from_json(self, filepath: str) -> None:
        """
        Load analytics data from JSON file.
        
        Args:
            filepath: Path to JSON file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load iteration logs
            self.iteration_logs = [
                IterationLog(**log) for log in data.get("iteration_logs", [])
            ]
            
            # Load anomalies
            self.anomalies = data.get("anomalies", [])
            
            logger.info(f"Loaded {len(self.iteration_logs)} iterations from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading from JSON: {e}")
    
    def clear_logs(self) -> None:
        """Clear all logs and anomalies."""
        self.iteration_logs.clear()
        self.anomalies.clear()
        logger.info("Analytics logs cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get basic statistics about logged data.
        
        Returns:
            Dictionary with statistics
        """
        if not self.iteration_logs:
            return {
                "num_iterations": 0,
                "num_anomalies": 0
            }
        
        scores = [log.avg_composite_score for log in self.iteration_logs]
        
        return {
            "num_iterations": len(self.iteration_logs),
            "num_anomalies": len(self.anomalies),
            "avg_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "score_range": max(scores) - min(scores),
            "total_questions_evaluated": sum(log.num_questions for log in self.iteration_logs),
            "avg_prompt_length": sum(log.prompt_length for log in self.iteration_logs) / len(self.iteration_logs)
        }
    
    def compare_iterations(
        self,
        iteration_a: int,
        iteration_b: int
    ) -> Dict[str, Any]:
        """
        Compare two iterations in detail.
        
        Args:
            iteration_a: First iteration number
            iteration_b: Second iteration number
        
        Returns:
            Dictionary with comparison results
        """
        # Find logs
        log_a = next((log for log in self.iteration_logs if log.iteration == iteration_a), None)
        log_b = next((log for log in self.iteration_logs if log.iteration == iteration_b), None)
        
        if not log_a or not log_b:
            return {"error": "One or both iterations not found"}
        
        # Calculate differences
        score_diff = log_b.avg_composite_score - log_a.avg_composite_score
        
        criterion_diffs = {}
        for criterion in log_a.scores_by_criterion.keys():
            diff = log_b.scores_by_criterion.get(criterion, 0) - log_a.scores_by_criterion.get(criterion, 0)
            criterion_diffs[criterion] = diff
        
        return {
            "iteration_a": iteration_a,
            "iteration_b": iteration_b,
            "score_a": log_a.avg_composite_score,
            "score_b": log_b.avg_composite_score,
            "score_difference": score_diff,
            "improvement": "yes" if score_diff > 0 else "no",
            "criterion_differences": criterion_diffs,
            "prompt_length_a": log_a.prompt_length,
            "prompt_length_b": log_b.prompt_length,
            "prompt_length_change": log_b.prompt_length - log_a.prompt_length
        }


def create_analytics(storage_path: str = "./analytics") -> AnalyticsAgent:
    """
    Factory function to create AnalyticsAgent.
    
    Args:
        storage_path: Directory for analytics storage
    
    Returns:
        AnalyticsAgent instance
    
    Example:
        >>> analytics = create_analytics("./results")
        >>> analytics.log_iteration(1, prompt, evaluations)
        >>> report = analytics.generate_summary_report()
    """
    return AnalyticsAgent(storage_path=storage_path)
