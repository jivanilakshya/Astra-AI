"""
Orchestrator Agent Module - Feature 10

Coordinates the closed feedback loop for self-improving LLM system.
Manages the interaction between Generator, Judge, and Metrics components.

Workflow:
1. Generate answers for questions
2. Judge evaluates answers
3. Metrics tracks performance
4. Check convergence/stopping criteria
5. Repeat or terminate

The orchestrator is the central control unit that ensures smooth
execution of the optimization loop.
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from dspy_modules.generator import GeneratorAgent
from agents.judge import JudgeAgent
from utils.metrics import MetricsCalculator
from data.data_loader import Question
from config import get_config


class OrchestratorAgent:
    """
    Orchestrator Agent - Central coordinator for the optimization loop.
    
    Manages the complete workflow:
    - Question-Answer generation
    - Answer evaluation
    - Performance tracking
    - Convergence detection
    - Iteration control
    
    Stopping Criteria:
    - Maximum iterations reached
    - Convergence threshold met
    - Performance plateau detected
    - Manual termination
    """
    
    def __init__(
        self,
        generator: GeneratorAgent,
        judge: JudgeAgent,
        metrics: MetricsCalculator,
        max_iterations: Optional[int] = None,
        convergence_threshold: Optional[float] = None
    ):
        """
        Initialize Orchestrator Agent.
        
        Args:
            generator: Generator agent instance
            judge: Judge agent instance
            metrics: Metrics calculator instance
            max_iterations: Maximum number of iterations (from config if None)
            convergence_threshold: Score threshold for convergence (from config if None)
        """
        self.generator = generator
        self.judge = judge
        self.metrics = metrics
        
        # Load config
        config = get_config()
        self.max_iterations = max_iterations or config.max_iterations
        self.convergence_threshold = convergence_threshold or config.convergence_threshold
        
        self.current_iteration = 0
        self.is_running = False
        self.total_runtime = 0.0
    
    def run_iteration(
        self,
        questions: List[Question],
        iteration_num: int,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a single iteration of the optimization loop.
        
        Args:
            questions: List of Question objects
            iteration_num: Current iteration number
            prompt: Optional custom prompt for this iteration
        
        Returns:
            Dictionary with iteration results:
                - generation_results: Generated answers
                - evaluation_results: Judge evaluations
                - metrics: Aggregated metrics
                - iteration: Iteration number
                - runtime: Execution time
        """
        start_time = time.time()
        
        # Step 1: Generate answers
        generation_results = []
        for question in questions:
            result = self.generator.generate(
                question=question.question,
                context=question.context
            )
            generation_results.append(result)
        
        # Step 2: Evaluate answers
        evaluation_results = []
        for i, gen_result in enumerate(generation_results):
            eval_result = self.judge.evaluate(
                question=gen_result["question"],
                answer=gen_result["answer"],
                explanation=gen_result["explanation"],
                ground_truth=questions[i].ground_truth,
                context=questions[i].context
            )
            evaluation_results.append(eval_result)
        
        # Step 3: Calculate metrics
        iteration_metrics = self.metrics.add_iteration(
            iteration_num=iteration_num,
            evaluations=evaluation_results,
            prompt=prompt
        )
        
        runtime = time.time() - start_time
        
        return {
            "generation_results": generation_results,
            "evaluation_results": evaluation_results,
            "metrics": iteration_metrics,
            "iteration": iteration_num,
            "runtime": round(runtime, 2)
        }
    
    def run_optimization_loop(
        self,
        questions: List[Question],
        initial_prompt: Optional[str] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete optimization loop.
        
        Args:
            questions: List of questions to process
            initial_prompt: Initial prompt (unused in current version,
                           will be used with Optimizer in Feature 9)
            verbose: Print progress information
        
        Returns:
            Dictionary with complete results:
                - iterations: List of all iteration results
                - final_metrics: Final performance metrics
                - summary: Summary statistics
                - converged: Whether optimization converged
                - total_runtime: Total execution time
        """
        if not questions:
            raise ValueError("Questions list cannot be empty")
        
        if self.is_running:
            raise RuntimeError("Optimization loop is already running")
        
        self.is_running = True
        start_time = time.time()
        
        all_iterations = []
        current_prompt = initial_prompt or "Default prompt"
        
        try:
            if verbose:
                print("=" * 60)
                print("🚀 Starting Optimization Loop")
                print("=" * 60)
                print(f"Questions: {len(questions)}")
                print(f"Max Iterations: {self.max_iterations}")
                print(f"Convergence Threshold: {self.convergence_threshold}")
                print("=" * 60)
            
            for iteration in range(1, self.max_iterations + 1):
                self.current_iteration = iteration
                
                if verbose:
                    print(f"\n📍 Iteration {iteration}/{self.max_iterations}")
                
                # Run iteration
                iter_result = self.run_iteration(
                    questions=questions,
                    iteration_num=iteration,
                    prompt=current_prompt
                )
                
                all_iterations.append(iter_result)
                
                # Get metrics
                composite_score = iter_result["metrics"]["composite_stats"]["mean"]
                
                if verbose:
                    print(f"   Composite Score: {composite_score:.2f}")
                    print(f"   Runtime: {iter_result['runtime']:.2f}s")
                
                # Check stopping criteria
                stop, reason = self._check_stopping_criteria(iteration)
                
                if stop:
                    if verbose:
                        print(f"\n🛑 Stopping: {reason}")
                    break
            
            # Calculate final results
            self.total_runtime = time.time() - start_time
            
            final_metrics = self.metrics.get_iteration_metrics(self.current_iteration)
            summary = self.metrics.generate_summary()
            
            results = {
                "iterations": all_iterations,
                "final_metrics": final_metrics,
                "summary": summary,
                "converged": summary["convergence"]["converged"],
                "total_iterations": self.current_iteration,
                "total_runtime": round(self.total_runtime, 2),
                "questions_processed": len(questions)
            }
            
            if verbose:
                print("\n" + "=" * 60)
                print("✅ Optimization Complete")
                print("=" * 60)
                print(f"Total Iterations: {self.current_iteration}")
                print(f"Final Score: {final_metrics['composite_stats']['mean']:.2f}")
                print(f"Converged: {results['converged']}")
                print(f"Total Runtime: {self.total_runtime:.2f}s")
                print("=" * 60)
            
            return results
            
        except Exception as e:
            if verbose:
                print(f"\n❌ Error during optimization: {e}")
            raise
        
        finally:
            self.is_running = False
    
    def _check_stopping_criteria(
        self,
        current_iteration: int
    ) -> Tuple[bool, str]:
        """
        Check if optimization should stop.
        
        Args:
            current_iteration: Current iteration number
        
        Returns:
            Tuple of (should_stop, reason)
        """
        # Check max iterations
        if current_iteration >= self.max_iterations:
            return True, "max_iterations_reached"
        
        # Check convergence (need at least 2 iterations)
        if current_iteration >= 2:
            convergence = self.metrics.check_convergence(
                threshold=self.convergence_threshold,
                window=min(3, current_iteration),
                min_improvement=0.02
            )
            
            if convergence["converged"]:
                return True, convergence["reason"]
        
        return False, "continuing"
    
    def run_single_question(
        self,
        question: str,
        ground_truth: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single question through generate-evaluate pipeline.
        
        Args:
            question: Question text
            ground_truth: Optional correct answer
            context: Optional context information
        
        Returns:
            Dictionary with generation and evaluation results
        """
        # Generate
        gen_result = self.generator.generate(
            question=question,
            context=context
        )
        
        # Evaluate
        eval_result = self.judge.evaluate(
            question=question,
            answer=gen_result["answer"],
            explanation=gen_result["explanation"],
            ground_truth=ground_truth,
            context=context
        )
        
        return {
            "question": question,
            "generation": gen_result,
            "evaluation": eval_result,
            "composite_score": eval_result["composite_score"]
        }
    
    def process_batch(
        self,
        questions: List[Question]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple questions without iteration.
        
        Args:
            questions: List of Question objects
        
        Returns:
            List of results for each question
        """
        results = []
        
        for question in questions:
            result = self.run_single_question(
                question=question.question,
                ground_truth=question.ground_truth,
                context=question.context
            )
            results.append(result)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "convergence_threshold": self.convergence_threshold,
            "is_running": self.is_running,
            "total_runtime": round(self.total_runtime, 2),
            "generator_stats": self.generator.get_stats(),
            "judge_stats": self.judge.get_stats(),
            "metrics_history_length": len(self.metrics.iteration_history)
        }
    
    def reset(self):
        """Reset orchestrator and all components."""
        self.current_iteration = 0
        self.is_running = False
        self.total_runtime = 0.0
        self.generator.reset_stats()
        self.judge.reset_stats()
        self.metrics.reset()


def create_orchestrator(
    generator: Optional[GeneratorAgent] = None,
    judge: Optional[JudgeAgent] = None,
    metrics: Optional[MetricsCalculator] = None,
    max_iterations: Optional[int] = None,
    convergence_threshold: Optional[float] = None
) -> OrchestratorAgent:
    """
    Factory function to create an Orchestrator Agent.
    
    Args:
        generator: Generator agent (creates default if None)
        judge: Judge agent (creates default if None)
        metrics: Metrics calculator (creates default if None)
        max_iterations: Max iterations (from config if None)
        convergence_threshold: Convergence threshold (from config if None)
    
    Returns:
        Configured OrchestratorAgent instance
    """
    from dspy_modules.generator import create_generator
    from agents.judge import create_judge
    from utils.metrics import create_metrics_calculator
    
    if generator is None:
        generator = create_generator(use_reasoning=True)
    
    if judge is None:
        judge = create_judge(use_reasoning=True)
    
    if metrics is None:
        metrics = create_metrics_calculator()
    
    return OrchestratorAgent(
        generator=generator,
        judge=judge,
        metrics=metrics,
        max_iterations=max_iterations,
        convergence_threshold=convergence_threshold
    )


# Example usage
if __name__ == "__main__":
    from models.dspy_integration import configure_dspy
    from data.data_loader import Question
    
    print("=" * 60)
    print("Orchestrator Agent Example - Feature 10")
    print("=" * 60)
    
    # Configure DSPy
    try:
        configure_dspy()
        print("\n✅ DSPy configured")
    except Exception as e:
        print(f"\n⚠️  DSPy configuration skipped: {e}")
        print("   (LLM may not be available for actual execution)")
    
    # Create orchestrator
    orchestrator = create_orchestrator()
    print(f"✅ Created Orchestrator")
    print(f"   Max iterations: {orchestrator.max_iterations}")
    print(f"   Convergence threshold: {orchestrator.convergence_threshold}")
    
    # Example questions
    test_questions = [
        Question(
            id=1,
            question="What is photosynthesis?",
            ground_truth="Process by which plants convert light into energy",
            category="biology",
            difficulty="easy"
        ),
        Question(
            id=2,
            question="What is gravity?",
            ground_truth="Force that attracts objects with mass",
            category="physics",
            difficulty="easy"
        )
    ]
    
    print(f"\n📝 Test Questions: {len(test_questions)}")
    
    # Note: This will fail without a running LLM
    print("\n⚠️  Actual execution requires Ollama running")
    print("   Start with: ollama serve")
    print("   Then: ollama pull llama3.1")
    
    print("\n" + "=" * 60)
