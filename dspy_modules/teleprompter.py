"""
DSPy Teleprompter Module - Automatic optimization of DSPy modules.

This module provides wrappers for DSPy's optimization teleprompters:
- BootstrapFewShot: Few-shot learning optimization
- MIPRO: Multi-prompt instruction proposal optimizer

It manages training data creation, module compilation, and evaluation.
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
import dspy
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path

from data.data_loader import Question

logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    """Training example for DSPy optimization."""
    question: str
    answer: str
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dspy_example(self) -> dspy.Example:
        """Convert to DSPy Example format."""
        example_dict = {
            "question": self.question,
            "answer": self.answer
        }
        if self.context:
            example_dict["context"] = self.context
        
        return dspy.Example(**example_dict).with_inputs("question")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class TeleprompterManager:
    """Manages DSPy teleprompters for module optimization."""
    
    def __init__(
        self,
        metric: Optional[Callable] = None,
        max_bootstrapped_demos: int = 4,
        max_labeled_demos: int = 16,
        num_candidate_programs: int = 10
    ):
        """
        Initialize teleprompter manager.
        
        Args:
            metric: Evaluation metric function (example, prediction, trace) -> float
            max_bootstrapped_demos: Max demos for BootstrapFewShot
            max_labeled_demos: Max labeled demos for optimization
            num_candidate_programs: Number of candidate programs for MIPRO
        """
        self.metric = metric or self._default_metric
        self.max_bootstrapped_demos = max_bootstrapped_demos
        self.max_labeled_demos = max_labeled_demos
        self.num_candidate_programs = num_candidate_programs
        
        self.training_data: List[TrainingExample] = []
        self.validation_data: List[TrainingExample] = []
        
        logger.info("TeleprompterManager initialized")
    
    def _default_metric(
        self, 
        example: dspy.Example, 
        prediction: dspy.Prediction, 
        trace=None
    ) -> float:
        """
        Default metric: exact match on answer.
        
        Args:
            example: Ground truth example
            prediction: Model prediction
            trace: Optional execution trace
        
        Returns:
            Score between 0.0 and 1.0
        """
        try:
            if hasattr(prediction, 'answer') and hasattr(example, 'answer'):
                pred_answer = str(prediction.answer).strip().lower()
                true_answer = str(example.answer).strip().lower()
                return 1.0 if pred_answer == true_answer else 0.0
            return 0.0
        except Exception as e:
            logger.error(f"Error in default metric: {e}")
            return 0.0
    
    def add_training_example(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a training example.
        
        Args:
            question: Question text
            answer: Ground truth answer
            context: Optional context
            metadata: Optional metadata
        """
        example = TrainingExample(
            question=question,
            answer=answer,
            context=context,
            metadata=metadata
        )
        self.training_data.append(example)
        logger.debug(f"Added training example: {question[:50]}...")
    
    def add_validation_example(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a validation example.
        
        Args:
            question: Question text
            answer: Ground truth answer
            context: Optional context
            metadata: Optional metadata
        """
        example = TrainingExample(
            question=question,
            answer=answer,
            context=context,
            metadata=metadata
        )
        self.validation_data.append(example)
        logger.debug(f"Added validation example: {question[:50]}...")
    
    def create_examples_from_questions(
        self,
        questions: List[Question],
        split_ratio: float = 0.8
    ) -> Tuple[int, int]:
        """
        Create training/validation examples from Question objects.
        
        Args:
            questions: List of Question objects with ground truth
            split_ratio: Ratio for train/validation split (0.0-1.0)
        
        Returns:
            Tuple of (num_training, num_validation) examples created
        """
        if not questions:
            logger.warning("No questions provided for example creation")
            return 0, 0
        
        split_index = int(len(questions) * split_ratio)
        
        for i, q in enumerate(questions):
            if not q.ground_truth:
                logger.warning(f"Skipping question without ground truth: {q.id}")
                continue
            
            if i < split_index:
                self.add_training_example(
                    question=q.question,
                    answer=q.ground_truth,
                    context=q.context,
                    metadata={"question_id": q.id, "category": q.category}
                )
            else:
                self.add_validation_example(
                    question=q.question,
                    answer=q.ground_truth,
                    context=q.context,
                    metadata={"question_id": q.id, "category": q.category}
                )
        
        logger.info(
            f"Created {len(self.training_data)} training and "
            f"{len(self.validation_data)} validation examples"
        )
        return len(self.training_data), len(self.validation_data)
    
    def optimize_with_bootstrap(
        self,
        module: dspy.Module,
        metric: Optional[Callable] = None
    ) -> dspy.Module:
        """
        Optimize module using BootstrapFewShot teleprompter.
        
        BootstrapFewShot creates few-shot examples by bootstrapping
        from the training set, improving module performance.
        
        Args:
            module: DSPy module to optimize
            metric: Optional custom metric function
        
        Returns:
            Optimized DSPy module (or original if optimization fails)
        """
        if not self.training_data:
            logger.warning("No training data available for optimization")
            return module
        
        try:
            # Convert training data to DSPy examples
            train_examples = [ex.to_dspy_example() for ex in self.training_data]
            
            # Create BootstrapFewShot teleprompter
            teleprompter = dspy.teleprompt.BootstrapFewShot(
                metric=metric or self.metric,
                max_bootstrapped_demos=self.max_bootstrapped_demos,
                max_labeled_demos=min(len(train_examples), self.max_labeled_demos)
            )
            
            # Compile the module
            logger.info(
                f"Starting BootstrapFewShot optimization with "
                f"{len(train_examples)} examples"
            )
            optimized_module = teleprompter.compile(
                module,
                trainset=train_examples
            )
            
            logger.info("BootstrapFewShot optimization complete")
            return optimized_module
            
        except Exception as e:
            logger.error(f"Error during BootstrapFewShot optimization: {e}")
            logger.info("Returning original module")
            return module
    
    def optimize_with_mipro(
        self,
        module: dspy.Module,
        metric: Optional[Callable] = None,
        num_threads: int = 1
    ) -> dspy.Module:
        """
        Optimize module using MIPRO (Multi-Prompt Instruction Proposal Optimizer).
        
        MIPRO explores multiple prompt variations and selects the best
        performing program.
        
        Args:
            module: DSPy module to optimize
            metric: Optional custom metric function
            num_threads: Number of threads for optimization
        
        Returns:
            Optimized DSPy module (or original if optimization fails)
        """
        if not self.training_data:
            logger.warning("No training data available for MIPRO optimization")
            return module
        
        try:
            # Convert data to DSPy examples
            train_examples = [ex.to_dspy_example() for ex in self.training_data]
            
            # Create MIPRO teleprompter
            teleprompter = dspy.teleprompt.MIPRO(
                metric=metric or self.metric,
                num_candidates=self.num_candidate_programs,
                init_temperature=1.0
            )
            
            # Optionally use validation set
            val_examples = None
            if self.validation_data:
                val_examples = [ex.to_dspy_example() for ex in self.validation_data]
            
            logger.info(
                f"Starting MIPRO optimization with {len(train_examples)} "
                f"training examples"
            )
            optimized_module = teleprompter.compile(
                module,
                trainset=train_examples,
                valset=val_examples,
                num_threads=num_threads
            )
            
            logger.info("MIPRO optimization complete")
            return optimized_module
            
        except Exception as e:
            logger.error(f"Error during MIPRO optimization: {e}")
            logger.info("Returning original module")
            return module
    
    def evaluate_module(
        self,
        module: dspy.Module,
        use_validation: bool = True,
        metric: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a module on validation or training data.
        
        Args:
            module: DSPy module to evaluate
            use_validation: Use validation set if True, else training set
            metric: Optional custom metric function
        
        Returns:
            Dictionary with evaluation results:
                - num_examples: Number of examples evaluated
                - avg_score: Average score
                - min_score: Minimum score
                - max_score: Maximum score
                - scores: List of individual scores
                - predictions: List of predictions
        """
        dataset = self.validation_data if use_validation else self.training_data
        
        if not dataset:
            logger.warning("No data available for evaluation")
            return {"error": "No data available", "avg_score": 0.0}
        
        metric_fn = metric or self.metric
        
        try:
            examples = [ex.to_dspy_example() for ex in dataset]
            
            scores = []
            predictions = []
            
            for example in examples:
                try:
                    # Run module
                    prediction = module(question=example.question)
                    
                    # Calculate score
                    score = metric_fn(example, prediction)
                    scores.append(score)
                    predictions.append(prediction)
                    
                except Exception as e:
                    logger.error(f"Error evaluating example: {e}")
                    scores.append(0.0)
                    predictions.append(None)
            
            results = {
                "num_examples": len(examples),
                "avg_score": sum(scores) / len(scores) if scores else 0.0,
                "min_score": min(scores) if scores else 0.0,
                "max_score": max(scores) if scores else 0.0,
                "scores": scores,
                "predictions": predictions
            }
            
            logger.info(f"Evaluation complete: avg_score={results['avg_score']:.3f}")
            return results
            
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            return {"error": str(e), "avg_score": 0.0}
    
    def save_training_data(self, filepath: str) -> None:
        """
        Save training data to JSON file.
        
        Args:
            filepath: Path to save JSON file
        """
        try:
            data = {
                "training": [ex.to_dict() for ex in self.training_data],
                "validation": [ex.to_dict() for ex in self.validation_data]
            }
            
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Training data saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving training data: {e}")
    
    def load_training_data(self, filepath: str) -> None:
        """
        Load training data from JSON file.
        
        Args:
            filepath: Path to JSON file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.training_data = [
                TrainingExample(**ex) for ex in data.get("training", [])
            ]
            self.validation_data = [
                TrainingExample(**ex) for ex in data.get("validation", [])
            ]
            
            logger.info(
                f"Loaded {len(self.training_data)} training and "
                f"{len(self.validation_data)} validation examples"
            )
            
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
    
    def clear_data(self) -> None:
        """Clear all training and validation data."""
        self.training_data.clear()
        self.validation_data.clear()
        logger.info("Training and validation data cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about training data.
        
        Returns:
            Dictionary with data statistics:
                - num_training: Number of training examples
                - num_validation: Number of validation examples
                - total_examples: Total number of examples
        """
        return {
            "num_training": len(self.training_data),
            "num_validation": len(self.validation_data),
            "total_examples": len(self.training_data) + len(self.validation_data)
        }


def create_teleprompter(
    metric: Optional[Callable] = None,
    max_bootstrapped_demos: int = 4,
    max_labeled_demos: int = 16,
    num_candidate_programs: int = 10
) -> TeleprompterManager:
    """
    Factory function to create TeleprompterManager.
    
    Args:
        metric: Optional evaluation metric function
        max_bootstrapped_demos: Max bootstrapped demos for BootstrapFewShot
        max_labeled_demos: Max labeled demos for optimization
        num_candidate_programs: Number of candidate programs for MIPRO
    
    Returns:
        TeleprompterManager instance
    
    Example:
        >>> teleprompter = create_teleprompter(max_bootstrapped_demos=8)
        >>> teleprompter.add_training_example("What is 2+2?", "4")
        >>> optimized = teleprompter.optimize_with_bootstrap(module)
    """
    return TeleprompterManager(
        metric=metric,
        max_bootstrapped_demos=max_bootstrapped_demos,
        max_labeled_demos=max_labeled_demos,
        num_candidate_programs=num_candidate_programs
    )
