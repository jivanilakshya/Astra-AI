"""
Judge Agent Module - Feature 7

Implements the Judge Agent for evaluating generated answers.
Provides comprehensive multi-criteria evaluation with detailed feedback.

The Judge Agent evaluates answers on 5 dimensions:
- Correctness: Factual accuracy (0-10)
- Clarity: Explanation quality (0-10)
- Reasoning: Logical soundness (0-10)
- Relevance: Question alignment (0-10)
- Conciseness: Efficiency of expression (0-10)
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import dspy
    from dspy import Predict, ChainOfThought
except ImportError:
    dspy = None
    Predict = None
    ChainOfThought = None

from dspy_modules.signatures import AnswerEvaluation
from config import get_config


class JudgeAgent:
    """
    Judge Agent for evaluating answer quality.
    
    Uses DSPy's AnswerEvaluation signature to assess generated answers
    across multiple quality dimensions with detailed feedback.
    
    Evaluation Criteria:
    - Correctness (40% weight): Factual accuracy
    - Clarity (20% weight): Explanation quality
    - Reasoning (20% weight): Logical soundness
    - Relevance (10% weight): Question alignment
    - Conciseness (10% weight): Expression efficiency
    """
    
    def __init__(
        self,
        use_reasoning: bool = True,
        criteria_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize Judge Agent.
        
        Args:
            use_reasoning: If True, use ChainOfThought for evaluation
            criteria_weights: Custom weights for evaluation criteria
                            (must sum to 1.0)
        """
        if dspy is None:
            raise ImportError(
                "DSPy not available. Install with: pip install dspy-ai"
            )
        
        self.use_reasoning = use_reasoning
        
        # Load default weights from config
        config = get_config()
        default_weights = config.evaluation_weights
        
        # Use custom weights if provided, otherwise use config defaults
        self.criteria_weights = criteria_weights or default_weights
        
        # Validate weights sum to 1.0
        total_weight = sum(self.criteria_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(
                f"Criteria weights must sum to 1.0, got {total_weight}"
            )
        
        # Initialize DSPy evaluation module
        if use_reasoning:
            self.eval_module = ChainOfThought(AnswerEvaluation)
        else:
            self.eval_module = Predict(AnswerEvaluation)
        
        self.evaluation_count = 0
        self.total_evaluations_time = 0.0
    
    def evaluate(
        self,
        question: str,
        answer: str,
        explanation: str,
        ground_truth: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a generated answer.
        
        Args:
            question: The original question
            answer: Generated answer to evaluate
            explanation: Explanation for the answer
            ground_truth: Optional correct answer for comparison
            context: Optional context information
        
        Returns:
            Dictionary with:
                - scores: Individual criterion scores (0-10)
                - composite_score: Weighted average score
                - feedback: Detailed feedback per criterion
                - suggestions: Actionable improvement suggestions
                - flags: Identified issues (hallucination, off-topic, etc.)
                - metadata: Evaluation metadata
        """
        start_time = time.time()
        
        try:
            # Prepare evaluation input
            eval_input = {
                "question": question,
                "answer": answer,
                "explanation": explanation
            }
            
            if ground_truth:
                eval_input["ground_truth"] = ground_truth
            else:
                eval_input["ground_truth"] = "Not provided"
            
            # Run evaluation
            prediction = self.eval_module(**eval_input)
            
            # Extract scores
            scores = {
                "correctness": float(prediction.correctness_score),
                "clarity": float(prediction.clarity_score),
                "reasoning": float(prediction.reasoning_score),
                "relevance": float(prediction.relevance_score),
                "conciseness": float(prediction.conciseness_score)
            }
            
            # Calculate composite score
            composite_score = self._calculate_composite_score(scores)
            
            # Extract feedback
            feedback = {
                "correctness": prediction.correctness_feedback,
                "clarity": prediction.clarity_feedback,
                "reasoning": prediction.reasoning_feedback,
                "relevance": prediction.relevance_feedback,
                "conciseness": prediction.conciseness_feedback
            }
            
            # Analyze for issues
            flags = self._detect_issues(scores, feedback, answer, explanation)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(scores, feedback)
            
            # Calculate metadata
            latency = (time.time() - start_time) * 1000  # ms
            
            # Build response
            result = {
                "scores": scores,
                "composite_score": round(composite_score, 2),
                "feedback": feedback,
                "suggestions": suggestions,
                "flags": flags,
                "metadata": {
                    "latency_ms": round(latency, 2),
                    "timestamp": datetime.now().isoformat(),
                    "module_type": "ChainOfThought" if self.use_reasoning else "Predict",
                    "evaluation_count": self.evaluation_count,
                    "weights": self.criteria_weights
                }
            }
            
            # Add ground truth if provided
            if ground_truth and ground_truth != "Not provided":
                result["ground_truth"] = ground_truth
            
            if context:
                result["context"] = context
            
            self.evaluation_count += 1
            self.total_evaluations_time += latency / 1000  # convert to seconds
            
            return result
            
        except Exception as e:
            self.evaluation_count += 1
            return self._handle_error(
                question, answer, explanation, e, time.time() - start_time
            )
    
    def evaluate_batch(
        self,
        evaluations: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple answers at once.
        
        Args:
            evaluations: List of dicts with keys:
                - question: str
                - answer: str
                - explanation: str
                - ground_truth: Optional[str]
                - context: Optional[str]
        
        Returns:
            List of evaluation results
        """
        results = []
        
        for eval_item in evaluations:
            result = self.evaluate(
                question=eval_item["question"],
                answer=eval_item["answer"],
                explanation=eval_item["explanation"],
                ground_truth=eval_item.get("ground_truth"),
                context=eval_item.get("context")
            )
            results.append(result)
        
        return results
    
    def _calculate_composite_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate weighted composite score.
        
        Args:
            scores: Dictionary of criterion scores
        
        Returns:
            Weighted average score (0-10)
        """
        composite = sum(
            scores[criterion] * weight
            for criterion, weight in self.criteria_weights.items()
        )
        return composite
    
    def _detect_issues(
        self,
        scores: Dict[str, float],
        feedback: Dict[str, str],
        answer: str,
        explanation: str
    ) -> List[str]:
        """
        Detect potential issues in the answer.
        
        Args:
            scores: Evaluation scores
            feedback: Evaluation feedback
            answer: Generated answer
            explanation: Generated explanation
        
        Returns:
            List of issue flags
        """
        flags = []
        
        # Low correctness suggests hallucination
        if scores["correctness"] < 4.0:
            flags.append("potential_hallucination")
        
        # Low relevance suggests off-topic
        if scores["relevance"] < 5.0:
            flags.append("off_topic")
        
        # Low reasoning suggests logical errors
        if scores["reasoning"] < 5.0:
            flags.append("logical_error")
        
        # Low clarity suggests unclear explanation
        if scores["clarity"] < 5.0:
            flags.append("unclear_explanation")
        
        # Very short answer might be incomplete
        if len(answer) < 20 and scores["correctness"] < 7.0:
            flags.append("incomplete_answer")
        
        # Very long explanation might be verbose
        if len(explanation) > 500 and scores["conciseness"] < 6.0:
            flags.append("verbose_explanation")
        
        # Check feedback for keywords
        all_feedback = " ".join(feedback.values()).lower()
        
        if "incorrect" in all_feedback or "wrong" in all_feedback:
            if "potential_hallucination" not in flags:
                flags.append("factual_error")
        
        if "unclear" in all_feedback or "confusing" in all_feedback:
            if "unclear_explanation" not in flags:
                flags.append("clarity_issue")
        
        return flags
    
    def _generate_suggestions(
        self,
        scores: Dict[str, float],
        feedback: Dict[str, str]
    ) -> List[str]:
        """
        Generate actionable improvement suggestions.
        
        Args:
            scores: Evaluation scores
            feedback: Evaluation feedback
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Prioritize by weight and score
        weighted_scores = [
            (criterion, score, self.criteria_weights[criterion])
            for criterion, score in scores.items()
        ]
        
        # Sort by (weight * deficit) to prioritize important weak areas
        weighted_scores.sort(
            key=lambda x: x[2] * (10 - x[1]),
            reverse=True
        )
        
        # Generate suggestions for top 3 weak areas
        for criterion, score, weight in weighted_scores[:3]:
            if score < 7.0:  # Only suggest if below threshold
                if criterion == "correctness":
                    suggestions.append(
                        "Verify factual accuracy and correct any errors"
                    )
                elif criterion == "clarity":
                    suggestions.append(
                        "Improve explanation clarity with simpler language"
                    )
                elif criterion == "reasoning":
                    suggestions.append(
                        "Strengthen logical reasoning and provide better support"
                    )
                elif criterion == "relevance":
                    suggestions.append(
                        "Focus more directly on answering the question"
                    )
                elif criterion == "conciseness":
                    suggestions.append(
                        "Remove unnecessary verbosity and redundancy"
                    )
        
        return suggestions
    
    def _handle_error(
        self,
        question: str,
        answer: str,
        explanation: str,
        error: Exception,
        elapsed_time: float
    ) -> Dict[str, Any]:
        """Handle evaluation errors gracefully."""
        return {
            "scores": {
                "correctness": 0.0,
                "clarity": 0.0,
                "reasoning": 0.0,
                "relevance": 0.0,
                "conciseness": 0.0
            },
            "composite_score": 0.0,
            "feedback": {
                "error": f"Evaluation failed: {str(error)}"
            },
            "suggestions": [],
            "flags": ["evaluation_error"],
            "error": str(error),
            "metadata": {
                "latency_ms": round(elapsed_time * 1000, 2),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get evaluation statistics.
        
        Returns:
            Dictionary with evaluation stats
        """
        avg_time = (
            self.total_evaluations_time / self.evaluation_count
            if self.evaluation_count > 0
            else 0.0
        )
        
        return {
            "total_evaluations": self.evaluation_count,
            "total_time_seconds": round(self.total_evaluations_time, 2),
            "avg_time_seconds": round(avg_time, 2),
            "use_reasoning": self.use_reasoning,
            "criteria_weights": self.criteria_weights
        }
    
    def reset_stats(self):
        """Reset evaluation statistics."""
        self.evaluation_count = 0
        self.total_evaluations_time = 0.0


def create_judge(
    use_reasoning: bool = True,
    criteria_weights: Optional[Dict[str, float]] = None
) -> JudgeAgent:
    """
    Factory function to create a configured Judge Agent.
    
    Args:
        use_reasoning: Use ChainOfThought vs Predict
        criteria_weights: Custom weights for criteria
    
    Returns:
        Configured JudgeAgent instance
    """
    return JudgeAgent(
        use_reasoning=use_reasoning,
        criteria_weights=criteria_weights
    )


# Example usage
if __name__ == "__main__":
    from models.dspy_integration import configure_dspy
    
    print("="*60)
    print("Judge Agent Example - Feature 7")
    print("="*60)
    
    # Configure DSPy
    try:
        configure_dspy()
        print("\n✅ DSPy configured")
    except Exception as e:
        print(f"\n⚠️  DSPy configuration skipped: {e}")
        print("   (LLM may not be available for actual evaluation)")
    
    # Create judge
    judge = create_judge(use_reasoning=True)
    print(f"✅ Created Judge (ChainOfThought mode)")
    print(f"   Weights: {judge.criteria_weights}")
    
    # Example evaluation
    question = "What is photosynthesis?"
    answer = "Process plants use to make food"
    explanation = "Plants convert sunlight into energy"
    
    print(f"\n📝 Example Evaluation:")
    print(f"   Question: {question}")
    print(f"   Answer: {answer}")
    print(f"   Explanation: {explanation}")
    
    # Note: This will fail without a running LLM
    print("\n⚠️  Actual evaluation requires Ollama running")
    print("   Start with: ollama serve")
    print("   Then: ollama pull llama3.1")
    
    print("\n" + "="*60)
