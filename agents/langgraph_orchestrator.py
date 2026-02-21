"""
LangGraph Orchestrator - Workflow coordination with state graph
Uses LangGraph for optimization loop management + LangSmith observability
"""

import os
import json
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from datetime import datetime
from dataclasses import dataclass, asdict

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    langgraph_available = True
except ImportError:
    langgraph_available = False

# LangSmith (optional)
try:
    from langsmith import Client as LangSmithClient
    langsmith_available = True
except ImportError:
    langsmith_available = False

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
        judge_model: str = "mistralai/Mistral-7B-Instruct-v0.2",
        optimizer_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
        max_iterations: int = 5,
        convergence_threshold: float = 8.5,
        enable_langsmith: bool = True
    ):
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.iteration_logs: List[IterationLog] = []
        
        # Initialize LangSmith
        self.langsmith_enabled = False
        if enable_langsmith and langsmith_available:
            try:
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_PROJECT"] = "astra-ai-orchestrator"
                self.langsmith_client = LangSmithClient()
                self.langsmith_enabled = True
                print("  LangSmith tracing enabled for Orchestrator")
            except Exception:
                pass
        
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
            enable_langsmith=enable_langsmith
        )
        
        # Optimizer (LangChain)
        self.optimizer = create_langchain_optimizer(
            model_name=optimizer_model,
            enable_langsmith=enable_langsmith
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
        print(f"\n  Iteration {state['iteration'] + 1}: Generating answers...")
        
        generated_outputs = []
        
        for i, question in enumerate(state["questions"]):
            try:
                # Format prompt with question
                formatted_prompt = state["current_prompt"].replace("{question}", question)
                
                # Generate using HuggingFace
                result = self.generator.generate(
                    model_name=self.generator_model,
                    prompt=formatted_prompt,
                    temperature=0.7,
                    max_tokens=500
                )
                
                generated_outputs.append({
                    "question": question,
                    "answer": result.get("text", ""),
                    "explanation": result.get("text", ""),  # Same as answer for now
                    "metadata": {
                        "latency_ms": result.get("latency", 0) * 1000,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success" if result.get("success") else "error"
                    }
                })
                
                print(f"    [OK] Generated answer {i+1}/{len(state['questions'])}")
                
            except Exception as e:
                print(f"    [ERROR] Generation error for question {i+1}: {e}")
                generated_outputs.append({
                    "question": question,
                    "answer": "",
                    "explanation": f"Generation failed: {str(e)}",
                    "error": str(e),
                    "metadata": {"status": "error"}
                })
        
        state["generated_outputs"] = generated_outputs
        return state
    
    def _evaluate_node(self, state: OptimizationState) -> OptimizationState:
        """Evaluate generated answers"""
        print(f"\n  Evaluating {len(state['generated_outputs'])} answers...")
        
        evaluations = []
        
        for i, output in enumerate(state["generated_outputs"]):
            try:
                eval_result = self.judge.evaluate(
                    question=output["question"],
                    answer=output.get("answer", ""),
                    explanation=output.get("explanation", "")
                )
                evaluations.append(eval_result)
                print(f"    [OK] Evaluated {i+1}/{len(state['generated_outputs'])}: {eval_result['composite_score']:.2f}/10")
            except Exception as e:
                print(f"    [ERROR] Evaluation error: {e}")
                evaluations.append({
                    "scores": {k: 0.0 for k in ["correctness", "clarity", "reasoning", "relevance", "conciseness"]},
                    "composite_score": 0.0,
                    "error": str(e)
                })
        
        # Calculate average score
        avg_score = sum(e["composite_score"] for e in evaluations) / len(evaluations) if evaluations else 0.0
        
        state["evaluations"] = evaluations
        state["current_score"] = avg_score
        state["performance_history"].append(avg_score)
        
        print(f"    Average score: {avg_score:.2f}/10")
        
        return state
    
    def _optimize_node(self, state: OptimizationState) -> OptimizationState:
        """Optimize prompt based on evaluations"""
        print(f"\n  Optimizing prompt...")
        
        try:
            optimization_result = self.optimizer.optimize(
                current_prompt=state["current_prompt"],
                evaluations=state["evaluations"],
                iteration=state["iteration"]
            )
            
            # Update prompt
            state["current_prompt"] = optimization_result["optimized_prompt"]
            state["optimization_result"] = optimization_result
            
            print(f"    [OK] Prompt optimized ({len(optimization_result.get('modifications_made', []))} modifications)")
            
        except Exception as e:
            print(f"    [ERROR] Optimization error: {e}")
            state["optimization_result"] = {"error": str(e)}
        
        # Log iteration
        self.iteration_logs.append(IterationLog(
            iteration=state["iteration"] + 1,
            prompt=state["current_prompt"],
            score=state["current_score"],
            evaluations=state["evaluations"],
            generated_outputs=state["generated_outputs"],
            timestamp=datetime.now().isoformat()
        ))
        
        # Increment iteration
        state["iteration"] += 1
        
        return state
    
    def _should_continue(self, state: OptimizationState) -> str:
        """Decide whether to continue or finish"""
        # Check max iterations
        if state["iteration"] >= state["max_iterations"]:
            print(f"\n  [STOP] Max iterations ({state['max_iterations']}) reached")
            return "end"
        
        # Check score threshold
        if state["current_score"] >= self.convergence_threshold:
            print(f"\n  [OK] Convergence threshold ({self.convergence_threshold}) reached!")
            state["converged"] = True
            return "end"
        
        # Check improvement plateau
        if self.optimizer.check_convergence(state["performance_history"]):
            print(f"\n  [INFO] Improvement plateau detected")
            return "end"
        
        # Continue optimizing
        print(f"\n  Continuing to iteration {state['iteration'] + 1}...")
        return "continue"
    
    def _finalize_node(self, state: OptimizationState) -> OptimizationState:
        """Finalize and compile results"""
        print(f"\n  Finalizing results...")
        
        final_results = {
            "initial_score": state["performance_history"][0] if state["performance_history"] else 0.0,
            "final_score": state["current_score"],
            "improvement": state["current_score"] - (state["performance_history"][0] if state["performance_history"] else 0),
            "iterations": state["iteration"],
            "converged": state["converged"],
            "final_prompt": state["current_prompt"],
            "performance_history": state["performance_history"],
            "raw_results": {
                "iterations": [asdict(log) for log in self.iteration_logs]
            }
        }
        
        state["final_results"] = final_results
        
        print(f"\n  Optimization complete!")
        print(f"   Initial score: {final_results['initial_score']:.2f}")
        print(f"   Final score:   {final_results['final_score']:.2f}")
        print(f"   Improvement:   +{final_results['improvement']:.2f}")
        print(f"   Iterations:    {final_results['iterations']}")
        
        return state
    
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
    judge_model: str = "mistralai/Mistral-7B-Instruct-v0.2",
    optimizer_model: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    max_iterations: int = 5,
    convergence_threshold: float = 8.5,
    enable_langsmith: bool = True
) -> LangGraphOrchestrator:
    """Create a LangGraph Orchestrator"""
    return LangGraphOrchestrator(
        generator_model=generator_model,
        judge_model=judge_model,
        optimizer_model=optimizer_model,
        max_iterations=max_iterations,
        convergence_threshold=convergence_threshold,
        enable_langsmith=enable_langsmith
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
