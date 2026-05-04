"""
LangGraph Orchestrator - Workflow coordination with state graph
Uses LangGraph for optimization loop management + LangSmith observability
"""

import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from datetime import datetime
from dataclasses import dataclass, asdict, field

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    langgraph_available = True
except ImportError:
    langgraph_available = False

# LangSmith (optional)
try:
    from langsmith import Client as LangSmithClient
    from langsmith import traceable as _ls_traceable
    langsmith_available = True
except ImportError:
    langsmith_available = False
    def _ls_traceable(*a, **kw):
        def _dec(fn): return fn
        if a and callable(a[0]): return a[0]
        return _dec

# Local imports
from agents.huggingface_provider import HuggingFaceProvider
from agents.langchain_judge import create_langchain_judge
from agents.langchain_optimizer import create_langchain_optimizer

from dotenv import load_dotenv
load_dotenv()


class OptimizationState(TypedDict):
    """State object for the optimization graph"""
    # Input
    questions: List[str]
    current_prompt: str
    iteration: int
    max_iterations: int
    
    # Generated outputs
    generated_outputs: List[Dict[str, Any]]
    
    # Evaluations
    evaluations: List[Dict[str, Any]]
    current_score: float
    
    # Prompt evolution
    optimization_result: Optional[Dict[str, Any]]
    
    # Performance tracking
    performance_history: List[float]
    
    # Convergence
    converged: bool
    
    # Results
    final_results: Optional[Dict[str, Any]]


@dataclass
class IterationLog:
    """Log for each iteration"""
    iteration: int
    prompt: str
    score: float
    evaluations: List[Dict]
    generated_outputs: List[Dict]
    timestamp: str
    per_question_scores: List[Dict] = field(default_factory=list)
    weak_criteria: List[str] = field(default_factory=list)
    strong_criteria: List[str] = field(default_factory=list)
    optimization_modifications: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class LangGraphOrchestrator:
    """
    Orchestrator using LangGraph for workflow management
    
    Workflow:
    1. Generate answers (using HuggingFace Generator)
    2. Evaluate answers (using LangChain Judge)
    3. Optimize prompt (using LangChain Optimizer)
    4. Check convergence
    5. Repeat or finish
    """
    
    def __init__(
        self,
        generator_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
        judge_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
        optimizer_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
        max_iterations: int = 5,
        convergence_threshold: float = 8.5,
        enable_langsmith: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 500,
        judge_max_tokens: int = 500,
        optimizer_max_tokens: int = 900
    ):
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.parallel_workers = max(1, int(os.getenv("ASTRA_PARALLEL_WORKERS", "3")))
        self.convergence_threshold = convergence_threshold
        self.iteration_logs: List[IterationLog] = []
        
        # LangSmith - check .env setting
        tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        self.langsmith_enabled = False
        if enable_langsmith and langsmith_available and tracing_enabled:
            try:
                os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "astra-ai")
                self.langsmith_client = LangSmithClient()
                self.langsmith_enabled = True
                print("  LangSmith tracing: ACTIVE")
            except Exception as e:
                print(f"  LangSmith tracing: FAILED ({e})")
        
        # Initialize agents
        print("\n  Initializing agents...")
        
        # Generator (HuggingFace)
        self.generator = HuggingFaceProvider(
            api_key=os.getenv("HUGGINGFACE_API_KEY")
        )
        self.generator_model = generator_model
        
        # Judge (LangChain)
        self.judge = create_langchain_judge(
            model_name=judge_model,
            enable_langsmith=enable_langsmith and tracing_enabled,
            max_tokens=judge_max_tokens
        )
        
        # Optimizer (LangChain)
        self.optimizer = create_langchain_optimizer(
            model_name=optimizer_model,
            enable_langsmith=enable_langsmith and tracing_enabled,
            max_tokens=optimizer_max_tokens
        )
        
        # Build LangGraph workflow
        if langgraph_available:
            self.workflow = self._build_workflow()
            print("  LangGraph workflow built")
        else:
            self.workflow = None
            print("  [WARN] LangGraph not available - using simple loop")
    
    def _build_workflow(self):
        """Build the optimization state graph"""
        workflow = StateGraph(OptimizationState)
        
        # Add nodes
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("evaluate", self._evaluate_node)
        workflow.add_node("optimize", self._optimize_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("generate")
        
        # Add edges
        workflow.add_edge("generate", "evaluate")
        workflow.add_edge("evaluate", "optimize")
        
        # Conditional edge from optimize: continue or end
        workflow.add_conditional_edges(
            "optimize",
            self._should_continue,
            {
                "continue": "generate",
                "end": "finalize"
            }
        )
        
        # End after finalize
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _generate_node(self, state: OptimizationState) -> OptimizationState:
        """Generate answers using current prompt"""
        elapsed = time.time() - getattr(self, '_loop_start_time', time.time())
        iter_num = state['iteration'] + 1
        max_iter = state['max_iterations']
        print(f"\n  Iteration {iter_num}/{max_iter}: Generating answers... [{elapsed:.0f}s elapsed]")

        questions = state["questions"]
        generated_outputs: List[Optional[Dict[str, Any]]] = [None] * len(questions)

        def _generate_one(idx: int, question: str) -> tuple[int, Dict[str, Any]]:
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    formatted_prompt = state["current_prompt"].replace("{question}", question)
                    result = self.generator.generate(
                        model_name=self.generator_model,
                        prompt=formatted_prompt,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
                    text = result.get("text", "") if isinstance(result, dict) else str(result)
                    success = result.get("success", False) if isinstance(result, dict) else bool(text)
                    if success and text.strip():
                        return idx, {
                            "question": question,
                            "answer": text,
                            "explanation": text,
                            "metadata": {
                                "latency_ms": result.get("latency_seconds", result.get("latency", 0)) * 1000,
                                "timestamp": datetime.now().isoformat(),
                                "status": "success",
                                "attempt": attempt + 1
                            }
                        }
                    # Unsuccessful but no exception — retry
                    if attempt < max_retries:
                        time.sleep(3)
                        continue
                    return idx, {
                        "question": question,
                        "answer": text or "(empty response)",
                        "explanation": text or "Generation returned empty",
                        "metadata": {"status": "error", "attempt": attempt + 1}
                    }
                except Exception as e:
                    if attempt < max_retries:
                        time.sleep(3)
                        continue
                    return idx, {
                        "question": question,
                        "answer": "",
                        "explanation": f"Generation failed: {str(e)}",
                        "error": str(e),
                        "metadata": {"status": "error", "attempt": attempt + 1}
                    }

        max_workers = min(self.parallel_workers, len(questions)) if questions else 1
        if len(questions) <= 1:
            for i, q in enumerate(questions):
                idx, output = _generate_one(i, q)
                generated_outputs[idx] = output
                if output.get("metadata", {}).get("status") == "success":
                    print(f"    [OK] Generated answer {i+1}/{len(questions)}")
                else:
                    print(f"    [ERROR] Generation error for question {i+1}")
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(_generate_one, i, q) for i, q in enumerate(questions)]
                completed = 0
                for fut in as_completed(futures):
                    idx, output = fut.result()
                    generated_outputs[idx] = output
                    completed += 1
                    if output.get("metadata", {}).get("status") == "success":
                        print(f"    [OK] Generated answer {completed}/{len(questions)}")
                    else:
                        print(f"    [ERROR] Generation failed ({completed}/{len(questions)})")

        state["generated_outputs"] = [
            out if out is not None else {
                "question": questions[i],
                "answer": "",
                "explanation": "Generation failed: missing concurrent result",
                "error": "missing_result",
                "metadata": {"status": "error"}
            }
            for i, out in enumerate(generated_outputs)
        ]
        return state
    
    def _evaluate_node(self, state: OptimizationState) -> OptimizationState:
        """Evaluate generated answers with detailed per-question tracking"""
        num_outputs = len(state['generated_outputs'])
        print(f"\n  Evaluating {num_outputs} answers...")

        outputs = state["generated_outputs"]
        evaluations: List[Optional[Dict[str, Any]]] = [None] * num_outputs

        def _evaluate_one(idx: int, output: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
            if output.get("metadata", {}).get("status") == "error" or not output.get("answer"):
                return idx, {
                    "scores": {k: 0.0 for k in ["correctness", "clarity", "reasoning", "relevance", "conciseness"]},
                    "composite_score": 0.0,
                    "feedback": {},
                    "suggestions": ["Answer was empty or failed to generate"],
                    "flags": ["empty_answer"],
                    "skipped": True
                }
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    eval_result = self.judge.evaluate(
                        question=output["question"],
                        answer=output.get("answer", ""),
                        explanation=output.get("explanation", "")
                    )
                    if eval_result.get("composite_score", 0) > 0:
                        return idx, eval_result
                    if attempt < max_retries:
                        time.sleep(2)
                        continue
                    return idx, eval_result
                except Exception as e:
                    if attempt < max_retries:
                        time.sleep(2)
                        continue
                    return idx, {
                        "scores": {k: 0.0 for k in ["correctness", "clarity", "reasoning", "relevance", "conciseness"]},
                        "composite_score": 0.0,
                        "error": str(e),
                        "flags": ["evaluation_error"]
                    }

        max_workers = min(self.parallel_workers, num_outputs) if num_outputs else 1
        if num_outputs <= 1:
            for i, out in enumerate(outputs):
                idx, eval_result = _evaluate_one(i, out)
                evaluations[idx] = eval_result
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(_evaluate_one, i, out) for i, out in enumerate(outputs)]
                for fut in as_completed(futures):
                    idx, eval_result = fut.result()
                    evaluations[idx] = eval_result

        for i, (output, eval_result) in enumerate(zip(outputs, evaluations)):
            if eval_result is None:
                print(f"    [ERROR] Evaluation missing for Q{i+1}")
                continue
            if eval_result.get("skipped"):
                print(f"    [SKIP] Question {i+1}: empty answer")
                continue
            if eval_result.get("error"):
                print(f"    [ERROR] Evaluation error Q{i+1}: {eval_result.get('error')}")
                continue
            score = eval_result.get('composite_score', 0)
            grade = "A" if score >= 8 else "B" if score >= 6 else "C" if score >= 4 else "D"
            print(f"    [OK] Q{i+1}: {score:.1f}/10 ({grade})  {output.get('question', '')[:45]}...")
            self._submit_langsmith_feedback(output, eval_result, state['iteration'] + 1)

        evaluations = [
            e if e is not None else {
                "scores": {k: 0.0 for k in ["correctness", "clarity", "reasoning", "relevance", "conciseness"]},
                "composite_score": 0.0,
                "feedback": {},
                "suggestions": ["Evaluation missing"],
                "flags": ["evaluation_missing"]
            }
            for e in evaluations
        ]
        
        # Calculate average (only for non-skipped, non-error evaluations)
        valid_evals = [e for e in evaluations if e["composite_score"] > 0 and not e.get("skipped")]
        avg_score = sum(e["composite_score"] for e in valid_evals) / len(valid_evals) if valid_evals else 0.0
        
        # Per-criteria averages
        criteria_avgs = {}
        for criterion in ["correctness", "clarity", "reasoning", "relevance", "conciseness"]:
            vals = [e["scores"].get(criterion, 0) for e in valid_evals]
            criteria_avgs[criterion] = sum(vals) / len(vals) if vals else 0.0
        
        # Identify weak/strong criteria
        weak = [c for c, v in criteria_avgs.items() if v < 6.0]
        strong = [c for c, v in criteria_avgs.items() if v >= 8.0]
        
        state["evaluations"] = evaluations
        state["current_score"] = avg_score
        state["performance_history"].append(avg_score)
        
        # Print criteria summary
        print(f"\n    {'─' * 50}")
        print(f"    {'Criterion':<15s} {'Avg Score':>10s}  {'Grade':>6s}")
        print(f"    {'─' * 50}")
        for criterion, avg in criteria_avgs.items():
            grade = "A" if avg >= 8 else "B" if avg >= 6 else "C" if avg >= 4 else "D"
            icon = "✓" if avg >= 7 else "!" if avg >= 4 else "✗"
            print(f"    {criterion:<15s} {avg:>8.1f}/10  {icon:>4s} {grade}")
        print(f"    {'─' * 50}")
        print(f"    {'COMPOSITE':<15s} {avg_score:>8.1f}/10")
        if weak:
            print(f"    Needs work: {', '.join(weak)}")
        
        return state
    
    def _submit_langsmith_feedback(self, output: Dict, eval_result: Dict, iteration: int):
        """Submit evaluation scores as feedback to LangSmith"""
        if not self.langsmith_enabled:
            return
        try:
            from langsmith import utils as ls_utils
            # Use the LangSmith client to log a dataset-style feedback
            project_name = os.getenv("LANGCHAIN_PROJECT", "astra-ai")
            
            # List recent runs and attach feedback to the latest
            runs = list(self.langsmith_client.list_runs(
                project_name=project_name,
                execution_order=1,
                limit=1
            ))
            
            if runs:
                run_id = runs[0].id
                # Submit composite score
                self.langsmith_client.create_feedback(
                    run_id=run_id,
                    key="composite_score",
                    score=eval_result["composite_score"] / 10.0,
                    value=f"Iter {iteration}: {eval_result['composite_score']:.1f}/10",
                    comment=json.dumps({
                        "scores": eval_result.get("scores", {}),
                        "question": output.get("question", "")[:100],
                        "suggestions": eval_result.get("suggestions", [])[:2]
                    })
                )
                # Submit individual criteria
                for criterion, score_val in eval_result.get("scores", {}).items():
                    self.langsmith_client.create_feedback(
                        run_id=run_id,
                        key=f"eval_{criterion}",
                        score=score_val / 10.0,
                        value=f"{score_val:.1f}/10"
                    )
        except Exception as e:
            # Silently skip — don't break evaluation for feedback issues
            pass
    
    def _optimize_node(self, state: OptimizationState) -> OptimizationState:
        """Optimize prompt based on evaluations with detailed tracking"""
        iter_start = time.time()
        print(f"\n  Optimizing prompt...")
        
        modifications = []
        try:
            optimization_result = self.optimizer.optimize(
                current_prompt=state["current_prompt"],
                evaluations=state["evaluations"],
                iteration=state["iteration"]
            )
            
            # Update prompt
            state["current_prompt"] = optimization_result["optimized_prompt"]
            state["optimization_result"] = optimization_result
            modifications = optimization_result.get("modifications_made", [])
            
            if modifications:
                print(f"    [OK] Prompt optimized ({len(modifications)} changes):")
                for mod in modifications[:3]:
                    print(f"        • {mod[:70]}")
            else:
                print(f"    [OK] Prompt optimized")
            
        except Exception as e:
            print(f"    [ERROR] Optimization error: {e}")
            state["optimization_result"] = {"error": str(e)}
        
        # Build per-question score details
        per_q_scores = []
        valid_evals = [e for e in state["evaluations"] if e.get("composite_score", 0) > 0 and not e.get("skipped")]
        for i, (output, eval_r) in enumerate(zip(state["generated_outputs"], state["evaluations"])):
            per_q_scores.append({
                "question": output.get("question", f"Q{i+1}"),
                "answer_preview": output.get("answer", "")[:120],
                "composite_score": eval_r.get("composite_score", 0.0),
                "scores": eval_r.get("scores", {}),
                "suggestions": eval_r.get("suggestions", []),
                "flags": eval_r.get("flags", [])
            })
        
        # Per-criteria aggregation
        criteria_avgs = {}
        for criterion in ["correctness", "clarity", "reasoning", "relevance", "conciseness"]:
            vals = [e["scores"].get(criterion, 0) for e in valid_evals]
            criteria_avgs[criterion] = sum(vals) / len(vals) if vals else 0.0
        
        weak = [c for c, v in criteria_avgs.items() if v < 6.0]
        strong = [c for c, v in criteria_avgs.items() if v >= 8.0]
        
        duration = time.time() - iter_start
        
        # Log iteration with all details
        self.iteration_logs.append(IterationLog(
            iteration=state["iteration"] + 1,
            prompt=state["current_prompt"],
            score=state["current_score"],
            evaluations=state["evaluations"],
            generated_outputs=state["generated_outputs"],
            timestamp=datetime.now().isoformat(),
            per_question_scores=per_q_scores,
            weak_criteria=weak,
            strong_criteria=strong,
            optimization_modifications=modifications,
            duration_seconds=duration
        ))
        
        # Increment iteration
        state["iteration"] += 1
        
        return state
    
    def _should_continue(self, state: OptimizationState) -> str:
        """Decide whether to continue or finish, with auto-rollback on score drops"""
        # Check max iterations
        if state["iteration"] >= state["max_iterations"]:
            print(f"\n  [STOP] Max iterations ({state['max_iterations']}) reached")
            return "end"
        
        # Check score threshold
        if state["current_score"] >= self.convergence_threshold:
            print(f"\n  [OK] Convergence threshold ({self.convergence_threshold}) reached!")
            state["converged"] = True
            return "end"
        
        # Check for score degradation — rollback to best prompt
        history = state["performance_history"]
        if len(history) >= 2:
            prev_score = history[-2]
            curr_score = history[-1]
            drop = prev_score - curr_score
            
            if drop > 0.5:
                # Significant score drop — rollback to best prompt
                best_idx = history.index(max(history))
                if best_idx < len(self.iteration_logs):
                    best_prompt = self.iteration_logs[best_idx].prompt
                    state["current_prompt"] = best_prompt
                    print(f"\n  [ROLLBACK] Score dropped {drop:.1f} pts. Reverted to best prompt (iter {best_idx + 1}, score {history[best_idx]:.1f})")
        
        # Check improvement plateau
        if self.optimizer.check_convergence(state["performance_history"]):
            print(f"\n  [INFO] Improvement plateau detected")
            return "end"
        
        # Continue optimizing
        print(f"\n  Continuing to iteration {state['iteration'] + 1}...")
        return "continue"
    
    def _finalize_node(self, state: OptimizationState) -> OptimizationState:
        """Finalize and compile rich results with per-iteration detail"""
        print(f"\n  Finalizing results...")
        
        # Use the best score from history, not the last one (which may be 0 from network error)
        history = state["performance_history"]
        initial_score = history[0] if history else 0.0
        best_score = max(history) if history else 0.0
        final_score = state["current_score"]
        
        # If the last score is 0.0 (likely network error), use best score as final
        if final_score < 0.01 and best_score > 0.01:
            final_score = best_score
            print(f"  [INFO] Using best score ({best_score:.2f}) instead of last score (0.00)")
        
        # Build detailed iteration data
        iteration_details = []
        for log in self.iteration_logs:
            iteration_details.append({
                "iteration": log.iteration,
                "score": log.score,
                "prompt": log.prompt,
                "generated_outputs": log.generated_outputs,
                "evaluations": log.evaluations,
                "per_question_scores": log.per_question_scores,
                "weak_criteria": log.weak_criteria,
                "strong_criteria": log.strong_criteria,
                "optimization_modifications": log.optimization_modifications,
                "duration_seconds": log.duration_seconds,
                "timestamp": log.timestamp
            })
        
        # Overall criteria trend (first vs last iteration)
        criteria_trend = {}
        if len(self.iteration_logs) >= 2:
            first_log = self.iteration_logs[0]
            last_log = self.iteration_logs[-1]
            for criterion in ["correctness", "clarity", "reasoning", "relevance", "conciseness"]:
                first_vals = [q["scores"].get(criterion, 0) for q in first_log.per_question_scores if q.get("scores")]
                last_vals = [q["scores"].get(criterion, 0) for q in last_log.per_question_scores if q.get("scores")]
                first_avg = sum(first_vals) / len(first_vals) if first_vals else 0
                last_avg = sum(last_vals) / len(last_vals) if last_vals else 0
                criteria_trend[criterion] = {
                    "initial": round(first_avg, 1),
                    "final": round(last_avg, 1),
                    "change": round(last_avg - first_avg, 1)
                }
        
        # Plain-English summary
        improvement = final_score - initial_score
        if improvement > 1.0:
            summary_text = f"Excellent improvement! Score rose from {initial_score:.1f} to {final_score:.1f} (+{improvement:.1f})"
        elif improvement > 0:
            summary_text = f"The prompt improved from {initial_score:.1f} to {final_score:.1f} (+{improvement:.1f})"
        elif improvement > -0.5:
            summary_text = f"Score stayed roughly the same ({initial_score:.1f} -> {final_score:.1f}). The prompt may already be near-optimal."
        else:
            summary_text = f"Score declined from {initial_score:.1f} to {final_score:.1f}. Consider reverting to the original prompt."
        
        final_results = {
            "initial_score": initial_score,
            "final_score": final_score,
            "best_score": best_score,
            "improvement": improvement,
            "iterations": state["iteration"],
            "converged": state["converged"],
            "final_prompt": state["current_prompt"],
            "performance_history": history,
            "summary": summary_text,
            "criteria_trend": criteria_trend,
            "iteration_details": iteration_details,
            "raw_results": {
                "iterations": [asdict(log) for log in self.iteration_logs]
            }
        }
        
        state["final_results"] = final_results
        
        print(f"\n  {'=' * 55}")
        print(f"   OPTIMIZATION COMPLETE")
        print(f"  {'=' * 55}")
        print(f"   Initial score : {initial_score:.1f}/10")
        print(f"   Best score    : {best_score:.1f}/10")
        print(f"   Final score   : {final_score:.1f}/10")
        print(f"   Change        : {improvement:+.1f}")
        print(f"   Iterations    : {state['iteration']}")
        print(f"   {summary_text}")
        print(f"  {'=' * 55}")
        
        return state
    
    @_ls_traceable(run_type="chain", name="Astra AI Optimization Loop")
    def run_optimization(
        self,
        questions: List[str],
        initial_prompt: str
    ) -> Dict[str, Any]:
        """
        Run the optimization workflow
        
        Args:
            questions: List of questions to optimize for
            initial_prompt: Starting prompt template (must contain {question})
            
        Returns:
            Final results dict
        """
        self._loop_start_time = time.time()
        
        print("\n" + "="*70)
        print("  Starting LangGraph Optimization Workflow")
        print("="*70)
        
        # Initialize state
        initial_state: OptimizationState = {
            "questions": questions,
            "current_prompt": initial_prompt,
            "iteration": 0,
            "max_iterations": self.max_iterations,
            "generated_outputs": [],
            "evaluations": [],
            "current_score": 0.0,
            "optimization_result": None,
            "performance_history": [],
            "converged": False,
            "final_results": None
        }
        
        # Run workflow
        if self.workflow:
            # Use LangGraph
            final_state = self.workflow.invoke(initial_state)
        else:
            # Fallback: simple loop
            final_state = self._simple_loop(initial_state)
        
        return final_state["final_results"]
    
    def _simple_loop(self, state: OptimizationState) -> OptimizationState:
        """Fallback loop if LangGraph not available"""
        while True:
            state = self._generate_node(state)
            state = self._evaluate_node(state)
            state = self._optimize_node(state)
            
            if self._should_continue(state) == "end":
                break
        
        state = self._finalize_node(state)
        return state
    
    def export_results(self, results: Dict[str, Any], output_dir: str = "output"):
        """Export results to files"""
        from pathlib import Path
        
        # Create output directory
        session_dir = Path(output_dir) / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save results
        with open(session_dir / "results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save final prompt
        with open(session_dir / "optimized_prompt.txt", 'w') as f:
            f.write(results["final_prompt"])
        
        # Save prompt history
        if self.optimizer.prompt_history:
            self.optimizer.export_history(str(session_dir / "prompt_history.json"))
        
        print(f"\n  Results exported to: {session_dir}")
        return session_dir


# Factory function
def create_langchain_orchestrator(
    generator_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    judge_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    optimizer_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    max_iterations: int = 5,
    convergence_threshold: float = 8.5,
    enable_langsmith: bool = True,
    temperature: float = 0.7,
    max_tokens: int = 500,
    judge_max_tokens: int = 500,
    optimizer_max_tokens: int = 900
) -> LangGraphOrchestrator:
    """Create a LangGraph Orchestrator"""
    return LangGraphOrchestrator(
        generator_model=generator_model,
        judge_model=judge_model,
        optimizer_model=optimizer_model,
        max_iterations=max_iterations,
        convergence_threshold=convergence_threshold,
        enable_langsmith=enable_langsmith,
        temperature=temperature,
        max_tokens=max_tokens,
        judge_max_tokens=judge_max_tokens,
        optimizer_max_tokens=optimizer_max_tokens
    )


# Test
if __name__ == "__main__":
    print("\n  Testing LangGraph Orchestrator...\n")
    
    orchestrator = create_langchain_orchestrator(
        max_iterations=2,  # Short test
        enable_langsmith=True
    )
    
    # Test questions
    test_questions = [
        "What is artificial intelligence?",
        "Explain machine learning in simple terms."
    ]
    
    initial_prompt = """Answer the following question clearly and concisely.

Question: {question}

Provide a clear, accurate answer with explanation.

Answer:"""
    
    # Run optimization
    results = orchestrator.run_optimization(test_questions, initial_prompt)
    
    # Export results
    orchestrator.export_results(results)
    
    print(f"\n  Orchestrator test complete!")
