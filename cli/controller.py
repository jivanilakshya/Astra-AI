"""
CLI Controller for Astra-AI Self-Improving LLM System.

Provides command-line interface with:
- Interactive mode for step-by-step optimization
- Batch mode for automated runs
- Configuration management
- Progress tracking and reporting
- Export capabilities
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import os

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from agents import (
    LANGCHAIN_AVAILABLE,
    HuggingFaceProvider,
)

# Import LangChain agents (primary pathway)
if LANGCHAIN_AVAILABLE:
    from agents import (
        create_langchain_judge,
        create_langchain_optimizer,
        create_langchain_orchestrator,
    )
else:
    print("[ERROR] LangChain agents not available. Install: pip install langchain langgraph")
    sys.exit(1)

from utils import (
    create_analytics,
    create_model_selector,
    TaskComplexity,
    AgentType
)
from data import Question
from config import get_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_question_from_text(text: str, question_id: int = 0, expected_answer: str = "") -> Question:
    """
    Helper to create Question object from text.
    
    Args:
        text: Question text
        question_id: Question ID
        expected_answer: Optional ground truth answer
    
    Returns:
        Question object
    """
    return Question(
        id=question_id,
        question=text,
        ground_truth=expected_answer
    )


class CLIController:
    """
    Command-line interface controller for the self-improving LLM system.
    
    Manages workflow execution, user interaction, and result reporting.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        budget_limit: Optional[float] = None,
        max_iterations: Optional[int] = None,
        output_dir: str = "./output"
    ):
        """
        Initialize CLI Controller.
        
        Args:
            config_path: Path to configuration file
            budget_limit: Optional budget limit for LLM costs
            max_iterations: Maximum optimization iterations
            output_dir: Directory for output files
        """
        # Load configuration
        self.config = get_config(config_path) if config_path else get_config()
        
        # Override config if CLI args provided
        if budget_limit is not None:
            self.budget_limit = budget_limit
        else:
            self.budget_limit = getattr(self.config, 'budget_limit', None)
        
        if max_iterations is not None:
            self.max_iterations = max_iterations
        else:
            self.max_iterations = self.config.max_iterations
        
        # Set up output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.model_selector = None
        self.analytics = None
        self.teleprompter = None
        self.generator = None
        self.judge = None
        self.optimizer = None
        self.orchestrator = None
        
        # Session data
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.questions: List[Question] = []
        self.results: Optional[Dict[str, Any]] = None
        
        logger.info(f"CLI Controller initialized (session: {self.session_id})")
    
    def initialize_components(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print()
            print("  Initializing system components...")
            print()
            
            # Model selector (cost tracking)
            print("  [1/3] Model Selector & Cost Tracker...")
            self.model_selector = create_model_selector(
                budget_limit=self.budget_limit,
                prefer_open_source=True,
                storage_path=str(self.output_dir / "cost_tracking")
            )
            print("         Ready.")
            
            # Analytics
            print("  [2/3] Analytics Agent...")
            self.analytics = create_analytics(
                storage_path=str(self.output_dir / "analytics")
            )
            print("         Ready.")
            
            # LangGraph Orchestrator (creates generator, judge, optimizer internally)
            print("  [3/3] LangGraph Orchestrator (Generator + Judge + Optimizer)...")
            config = get_config()
            gen_model = config.generator_model.get('model_name', 'meta-llama/Meta-Llama-3-8B-Instruct')
            judge_model = config.judge_model.get('model_name', 'mistralai/Mistral-7B-Instruct-v0.2')
            opt_model = config.optimizer_model.get('model_name', 'meta-llama/Meta-Llama-3-8B-Instruct')
            
            self.orchestrator = create_langchain_orchestrator(
                generator_model=gen_model,
                judge_model=judge_model,
                optimizer_model=opt_model,
                max_iterations=self.max_iterations,
                convergence_threshold=self.config.convergence_threshold,
                enable_langsmith=True
            )
            print("         Ready.")
            
            print()
            print("  All components initialized successfully!")
            print()
            return True
            
        except Exception as e:
            print(f"\n  [ERROR] Component initialization failed: {e}\n")
            logger.error(f"Component initialization error: {e}", exc_info=True)
            return False
    
    def load_questions(self, questions_file: str) -> bool:
        """
        Load questions from file.
        
        Args:
            questions_file: Path to questions file (JSON or text)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            questions_path = Path(questions_file)
            
            if not questions_path.exists():
                print(f"  [ERROR] Questions file not found: {questions_file}")
                return False
            
            # JSON file
            if questions_path.suffix == '.json':
                with open(questions_path, 'r') as f:
                    data = json.load(f)
                
                question_id = len(self.questions)
                
                if isinstance(data, list):
                    # List of question strings or dicts
                    for item in data:
                        if isinstance(item, str):
                            self.questions.append(create_question_from_text(item, question_id))
                            question_id += 1
                        elif isinstance(item, dict):
                            # Ensure required fields exist
                            if 'id' not in item:
                                item['id'] = question_id
                                question_id += 1
                            if 'question' not in item and 'text' in item:
                                item['question'] = item.pop('text')
                            if 'ground_truth' not in item and 'expected_answer' in item:
                                item['ground_truth'] = item.pop('expected_answer')
                            if 'question' not in item:
                                item['question'] = ''
                            if 'ground_truth' not in item:
                                item['ground_truth'] = ''
                            self.questions.append(Question(**item))
                elif isinstance(data, dict) and 'questions' in data:
                    # Dict with 'questions' key
                    for item in data['questions']:
                        if isinstance(item, str):
                            self.questions.append(create_question_from_text(item, question_id))
                            question_id += 1
                        elif isinstance(item, dict):
                            if 'id' not in item:
                                item['id'] = question_id
                                question_id += 1
                            if 'question' not in item and 'text' in item:
                                item['question'] = item.pop('text')
                            if 'ground_truth' not in item and 'expected_answer' in item:
                                item['ground_truth'] = item.pop('expected_answer')
                            if 'question' not in item:
                                item['question'] = ''
                            if 'ground_truth' not in item:
                                item['ground_truth'] = ''
                            self.questions.append(Question(**item))
            
            # Text file (one question per line)
            else:
                question_id = len(self.questions)
                with open(questions_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.questions.append(create_question_from_text(line, question_id))
                            question_id += 1
            
            print(f"  Loaded {len(self.questions)} questions from {questions_file}\n")
            return True
            
        except Exception as e:
            print(f"  [ERROR] Error loading questions: {e}\n")
            logger.error(f"Question loading error: {e}", exc_info=True)
            return False
    
    def interactive_mode(self):
        """Run interactive mode with user prompts."""
        print("=" * 60)
        print("  ASTRA AI  -  Interactive Mode")
        print("=" * 60)
        print()
        
        # Get questions interactively
        if not self.questions:
            print("  Enter your questions (one per line, empty line to finish):")
            print()
            question_id = 0
            while True:
                question = input(f"  Q{question_id + 1}: ").strip()
                if not question:
                    break
                self.questions.append(create_question_from_text(question, question_id))
                question_id += 1
            
            if not self.questions:
                print("\n  No questions provided. Exiting.\n")
                return
            
            print(f"\n  {len(self.questions)} question(s) entered.\n")
        
        # Display questions
        print("  Questions to optimize:")
        for i, q in enumerate(self.questions, 1):
            print(f"    {i}. {q.question}")
        print()
        
        # Ask for confirmation
        response = input("Proceed with optimization? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Optimization cancelled.\n")
            return
        
        # Run optimization
        self._run_optimization()
        
        # Interactive results review
        self._interactive_results()
    
    def batch_mode(self, questions_file: str):
        """
        Run batch mode with questions from file.
        
        Args:
            questions_file: Path to questions file
        """
        print("=" * 60)
        print("  ASTRA AI  -  Batch Mode")
        print("=" * 60)
        print()
        
        # Load questions
        if not self.load_questions(questions_file):
            return
        
        # Run optimization
        self._run_optimization()
        
        # Display summary
        self._display_summary()
    
    def _run_optimization(self):
        """Execute the optimization loop using LangGraph orchestrator."""
        print("=" * 60)
        print("  STARTING OPTIMIZATION")
        print("=" * 60)
        print()
        
        config = get_config()
        gen_model = config.generator_model.get('model_name', 'meta-llama/Meta-Llama-3-8B-Instruct')
        judge_model = config.judge_model.get('model_name', 'mistralai/Mistral-7B-Instruct-v0.2')
        
        print(f"  Configuration:")
        print(f"    Generator  : {gen_model}")
        print(f"    Judge      : {judge_model}")
        print(f"    Questions  : {len(self.questions)}")
        print(f"    Max Iters  : {self.max_iterations}")
        print(f"    Threshold  : {self.config.convergence_threshold}")
        if self.budget_limit:
            print(f"    Budget     : ${self.budget_limit:.2f}")
        print()
        
        # Default initial prompt
        initial_prompt = """Answer the following question clearly and concisely.

Question: {question}

Provide a clear, accurate answer with a step-by-step explanation.

Requirements:
- Be factually accurate
- Explain your reasoning
- Use simple language
- Be concise but complete

Answer:"""
        
        try:
            # Extract question text from Question objects
            question_texts = [q.question for q in self.questions]
            
            # Run LangGraph orchestrator
            raw_results = self.orchestrator.run_optimization(
                questions=question_texts,
                initial_prompt=initial_prompt
            )
            
            # Store results (LangGraph returns a compatible format)
            self.results = raw_results
            
            print()
            print("=" * 60)
            print("  OPTIMIZATION COMPLETE!")
            print("=" * 60)
            print()
            
        except Exception as e:
            print(f"\n  [ERROR] Optimization failed: {e}\n")
            logger.error(f"Optimization error: {e}", exc_info=True)
            self.results = None
    
    def _display_summary(self):
        """Display optimization results summary."""
        if not self.results:
            print("  No results to display.\n")
            return
        
        print("  OPTIMIZATION RESULTS")
        print("=" * 60)
        print()
        
        # System configuration
        config = get_config()
        gen_model = config.generator_model.get('model_name', 'N/A')
        judge_model = config.judge_model.get('model_name', 'N/A')
        opt_model = config.optimizer_model.get('model_name', 'N/A')
        
        print("  System Configuration:")
        print(f"    Generator : {gen_model}")
        print(f"    Judge     : {judge_model}")
        print(f"    Optimizer : {opt_model}")
        print(f"    Questions : {len(self.questions)}")
        print()
        
        # Performance
        initial = self.results.get('initial_score', 0)
        final = self.results.get('final_score', 0)
        improvement = self.results.get('improvement', 0)
        iters = self.results.get('iterations', 0)
        converged = self.results.get('converged', False)
        
        print("  Performance:")
        print(f"    Initial Score : {initial:.2f}/10")
        print(f"    Final Score   : {final:.2f}/10")
        print(f"    Improvement   : +{improvement:.2f}")
        print(f"    Iterations    : {iters}")
        print(f"    Converged     : {'Yes' if converged else 'No'}")
        print()
        
        # Performance history bar chart
        history = self.results.get('performance_history', [])
        if history:
            print("  Score Progress:")
            for i, score in enumerate(history, 1):
                bar_len = int(score * 3)  # Scale for display
                bar = "#" * bar_len
                delta = f" (+{score - history[0]:.2f})" if i > 1 else ""
                print(f"    Iter {i:2d}: {score:5.2f}/10  {bar}{delta}")
            print()
        
        # Cost summary
        if self.model_selector:
            try:
                cost_summary = self.model_selector.get_cost_summary()
                total_cost = cost_summary.get('total_cost', 0)
                print(f"  Cost Summary:")
                print(f"    Total Cost: ${total_cost:.4f}")
                if self.budget_limit:
                    print(f"    Budget     : ${self.budget_limit:.2f}")
                print()
            except Exception:
                pass
        
        print("=" * 60)
        print()
    
    def _interactive_results(self):
        """Interactive results exploration."""
        if not self.results:
            return
        
        self._display_summary()
        
        while True:
            print()
            print("  Options:")
            print("    1. View optimized prompt")
            print("    2. View performance history")
            print("    3. View intermediate results (Developer Mode)")
            print("    4. View detailed metrics")
            print("    5. View cost breakdown")
            print("    6. Export results")
            print("    7. Exit")
            
            choice = input("\n  Select (1-7): ").strip()
            
            if choice == '1':
                self._view_prompt()
            elif choice == '2':
                self._view_history()
            elif choice == '3':
                self._view_intermediate_results()
            elif choice == '4':
                self._view_detailed_metrics()
            elif choice == '5':
                self._view_cost_breakdown()
            elif choice == '6':
                self._export_results()
            elif choice == '7':
                break
            else:
                print("Invalid option. Please try again.")
    
    def _view_prompt(self):
        """Display optimized prompt with evolution history."""
        if not self.results or 'final_prompt' not in self.results:
            print("\n  No optimized prompt available.")
            return
        
        print()
        print("=" * 60)
        print("  OPTIMIZED PROMPT")
        print("=" * 60)
        print()
        print(self.results['final_prompt'])
        print()
        print("-" * 60)
        print(f"  Length: {len(self.results['final_prompt'])} characters")
        
        # Show prompt evolution if available
        iterations = self.results.get('raw_results', {}).get('iterations', [])
        if len(iterations) > 1:
            print(f"\n  Prompt Evolution ({len(iterations)} iterations):")
            for i, iter_data in enumerate(iterations, 1):
                prompt = iter_data.get('prompt', 'Unknown')
                print(f"    Iteration {i}: {len(prompt)} chars")
        
        print()
        print("=" * 60)    
    def _view_history(self):
        """Display performance history."""
        if not self.results or 'performance_history' not in self.results:
            print("\n  No performance history available.")
            return
        
        print()
        print("=" * 60)
        print("  PERFORMANCE HISTORY")
        print("=" * 60)
        print()
        
        history = self.results['performance_history']
        for i, score in enumerate(history, 1):
            improvement = score - history[0] if i > 1 else 0
            bar = "#" * int(score * 3)
            print(f"    Iteration {i:2d}: {score:.2f}/10  {bar}  (+{improvement:.2f})")
        
        print()
        print("=" * 60)
    
    def _view_cost_recommendations(self):
        """Display cost optimization recommendations."""
        if not self.model_selector:
            print("\n  Model selector not available.")
            return
        
        print()
        print("=" * 60)
        print("  COST RECOMMENDATIONS")
        print("=" * 60)
        print()
        
        try:
            recommendations = self.model_selector.get_cost_recommendations()
            for i, rec in enumerate(recommendations, 1):
                print(f"    {i}. {rec}")
        except Exception:
            print("    No recommendations available.")
        
        print()
        print("=" * 60)

    def _view_intermediate_results(self):
        """Display intermediate generation and evaluation results (Developer Mode)."""
        if not self.results or 'raw_results' not in self.results:
            print("\n  No intermediate results available.")
            return
        
        iterations = self.results['raw_results'].get('iterations', [])
        if not iterations:
            print("\n  No iteration data available.")
            return
        
        print()
        print("=" * 60)
        print("  INTERMEDIATE RESULTS - Developer Mode")
        print("=" * 60)
        
        for iter_num, iter_data in enumerate(iterations, 1):
            print(f"\n  --- ITERATION {iter_num} ---")
            print()
            
            # Show prompt being used
            prompt = iter_data.get('prompt', 'Unknown')
            print(f"  Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
            print(f"  Length: {len(prompt)} chars")
            
            # Show generation results
            gen_results = iter_data.get('generated_outputs', [])
            print(f"\n  Generation Results: {len(gen_results)} questions")
            for i, gen in enumerate(gen_results[:3], 1):  # Show first 3
                q_text = gen.get('question', 'N/A')[:60]
                print(f"\n    Q{i}: {q_text}...")
                answer = gen.get('answer', '')
                if answer:
                    print(f"    A : {answer[:80]}...")
                else:
                    error = gen.get('error', 'Unknown')
                    print(f"    [Error]: {str(error)[:80]}...")
                
                meta = gen.get('metadata', {})
                latency = meta.get('latency_ms', 0)
                if latency:
                    print(f"    Latency: {latency:.1f}ms")
            
            if len(gen_results) > 3:
                print(f"\n    ... and {len(gen_results) - 3} more questions")
            
            # Show evaluation results
            eval_results = iter_data.get('evaluations', [])
            print(f"\n  Evaluation Results:")
            if eval_results:
                # Aggregate scores
                avg_scores = {}
                for criterion in ['correctness', 'clarity', 'reasoning', 'relevance', 'conciseness']:
                    scores = [e.get('scores', {}).get(criterion, 0) for e in eval_results]
                    avg_scores[criterion] = sum(scores) / len(scores) if scores else 0
                
                print(f"    Correctness : {avg_scores['correctness']:.2f}/10")
                print(f"    Clarity     : {avg_scores['clarity']:.2f}/10")
                print(f"    Reasoning   : {avg_scores['reasoning']:.2f}/10")
                print(f"    Relevance   : {avg_scores['relevance']:.2f}/10")
                print(f"    Conciseness : {avg_scores['conciseness']:.2f}/10")
                
                # Show flags
                all_flags = []
                for e in eval_results:
                    all_flags.extend(e.get('flags', []))
                if all_flags:
                    unique_flags = set(all_flags)
                    print(f"\n    Flags: {', '.join(unique_flags)}")
                
                # Show suggestions
                all_suggestions = []
                for e in eval_results:
                    all_suggestions.extend(e.get('suggestions', []))
                if all_suggestions:
                    print(f"\n    Top Suggestions:")
                    for sugg in list(set(all_suggestions))[:3]:
                        print(f"      - {sugg}")
            
            # Show composite score
            score = iter_data.get('score', 0)
            print(f"\n  Composite Score: {score:.2f}/10")
        
        print()
        print("=" * 60)
        print()
    
    def _view_detailed_metrics(self):
        """Display detailed performance metrics."""
        if not self.results or 'raw_results' not in self.results:
            print("\n  No metrics available.")
            return
        
        raw_results = self.results.get('raw_results', {})
        iterations = raw_results.get('iterations', [])
        
        print()
        print("=" * 60)
        print("  DETAILED PERFORMANCE METRICS")
        print("=" * 60)
        print()
        
        # Compute metrics from iteration data
        if iterations:
            last_iter = iterations[-1]
            eval_results = last_iter.get('evaluations', [])
            
            if eval_results:
                print("  Final Iteration Scores:")
                
                for criterion in ['correctness', 'clarity', 'reasoning', 'relevance', 'conciseness']:
                    scores = [e.get('scores', {}).get(criterion, 0) for e in eval_results]
                    if scores:
                        mean = sum(scores) / len(scores)
                        min_val = min(scores)
                        max_val = max(scores)
                        print(f"    {criterion.capitalize():13} - Mean: {mean:.2f}  (min: {min_val:.2f}, max: {max_val:.2f})")
                
                # Composite score
                composite_scores = [e.get('composite_score', 0) for e in eval_results]
                if composite_scores:
                    avg_composite = sum(composite_scores) / len(composite_scores)
                    print(f"\n    Composite Score: {avg_composite:.2f}/10")
                
                # Flags summary
                all_flags = []
                for e in eval_results:
                    all_flags.extend(e.get('flags', []))
                if all_flags:
                    from collections import Counter
                    flag_counts = Counter(all_flags)
                    print(f"\n  Issues Detected:")
                    for flag, count in flag_counts.items():
                        print(f"    - {flag}: {count} occurrences")
                
                # Top suggestions
                all_suggestions = []
                for e in eval_results:
                    all_suggestions.extend(e.get('suggestions', []))
                if all_suggestions:
                    from collections import Counter
                    sugg_counts = Counter(all_suggestions)
                    print(f"\n  Top Suggestions:")
                    for sugg, count in sugg_counts.most_common(5):
                        print(f"    - {sugg} ({count}x)")
        
        # Performance trends
        history = self.results.get('performance_history', [])
        if len(history) > 1:
            improvements = [history[i] - history[i-1] for i in range(1, len(history))]
            avg_improvement = sum(improvements) / len(improvements) if improvements else 0
            print(f"\n  Performance Trend:")
            print(f"    Average improvement per iteration: {avg_improvement:+.2f}")
            
            if improvements:
                best_idx = improvements.index(max(improvements))
                print(f"    Best improvement in iteration: {best_idx + 2} ({max(improvements):+.2f})")
        
        print()
        print("=" * 60)
        print()
    
    def _view_cost_breakdown(self):
        """Display detailed cost breakdown by agent and model."""
        if not self.model_selector:
            print("\n  Model selector not available.")
            return
        
        print()
        print("=" * 60)
        print("  COST BREAKDOWN")
        print("=" * 60)
        print()
        
        # Get usage data
        try:
            usage_data = self.model_selector.get_usage_summary()
        except Exception:
            usage_data = None
        
        if not usage_data:
            print("    No cost data available yet.")
            print("    Tip: HuggingFace Inference API is free for most models.")
            print()
            print("=" * 60)
            return
        
        # Show by agent
        print("  Cost by Agent:")
        for agent_name in ['generator', 'judge', 'optimizer']:
            agent_cost = usage_data.get(f'{agent_name}_cost', 0)
            calls = usage_data.get(f'{agent_name}_calls', 0)
            tokens = usage_data.get(f'{agent_name}_tokens', 0)
            print(f"    {agent_name.capitalize():10} - ${agent_cost:.4f}  ({calls} calls, {tokens} tokens)")
        
        # Show by model
        print(f"\n  Cost by Model:")
        model_costs = usage_data.get('model_breakdown', {})
        if model_costs:
            for model, cost in sorted(model_costs.items(), key=lambda x: x[1], reverse=True):
                print(f"    {model:30} ${cost:.4f}")
        else:
            print("    No model-specific data available")
        
        # Total cost
        total_cost = usage_data.get('total_cost', 0)
        print(f"\n  Total Cost: ${total_cost:.4f}")
        
        # Cost projections
        iters = self.results.get('iterations', 0) if self.results else 0
        if iters > 0 and total_cost > 0:
            cost_per_iter = total_cost / iters
            print(f"\n  Projections:")
            print(f"    Cost per iteration    : ${cost_per_iter:.4f}")
            print(f"    Est. 10 iterations    : ${cost_per_iter * 10:.4f}")
            print(f"    Est. 100 questions    : ${cost_per_iter * 100:.4f}")
        
        print()
        print("=" * 60)
        print()    
    def _export_results(self):
        """Export results to files."""
        print("\n  Exporting results...")
        try:
            # Create export directory
            export_dir = self.output_dir / f"session_{self.session_id}"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export optimized prompt
            if self.results and 'final_prompt' in self.results:
                prompt_file = export_dir / "optimized_prompt.txt"
                with open(prompt_file, 'w') as f:
                    f.write(self.results['final_prompt'])
                print(f"    [OK] Prompt: {prompt_file}")
            
            # Export full results
            if self.results:
                results_file = export_dir / "results.json"
                with open(results_file, 'w') as f:
                    json.dump(self.results, f, indent=2)
                print(f"    [OK] Results: {results_file}")
            
            # Export analytics
            if self.analytics:
                analytics_file = export_dir / "analytics.json"
                self.analytics.export_to_json(str(analytics_file))
                print(f"    [OK] Analytics: {analytics_file}")
                
                # Export visualization
                viz_file = export_dir / "performance_chart.png"
                self.analytics.generate_visualization(str(viz_file))
                if Path(viz_file).exists():
                    print(f"    [OK] Chart: {viz_file}")
            
            # Export cost data
            if self.model_selector:
                cost_file = export_dir / "costs.json"
                self.model_selector.export_usage_data(str(cost_file))
                print(f"    [OK] Costs: {cost_file}")
            
            print(f"\n  Results exported to: {export_dir}\n")
            
        except Exception as e:
            print(f"\n  [ERROR] Export failed: {e}\n")
            logger.error(f"Export error: {e}", exc_info=True)
    
    def export_results(self, export_dir: Optional[str] = None):
        """
        Export results (for batch mode).
        
        Args:
            export_dir: Optional custom export directory
        """
        if export_dir:
            original_output = self.output_dir
            self.output_dir = Path(export_dir)
        
        self._export_results()
        
        if export_dir:
            self.output_dir = original_output


def create_cli_controller(
    config_path: Optional[str] = None,
    budget_limit: Optional[float] = None,
    max_iterations: Optional[int] = None,
    output_dir: str = "./output"
) -> CLIController:
    """
    Factory function to create CLI controller.
    
    Args:
        config_path: Path to configuration file
        budget_limit: Optional budget limit for LLM costs
        max_iterations: Maximum optimization iterations
        output_dir: Directory for output files
    
    Returns:
        CLIController instance
    """
    return CLIController(
        config_path=config_path,
        budget_limit=budget_limit,
        max_iterations=max_iterations,
        output_dir=output_dir
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Astra-AI: Self-Improving LLM System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python main.py --interactive
  
  # Batch mode with questions file
  python main.py --batch questions.json
  
  # With budget limit
  python main.py --batch questions.txt --budget 10.0
  
  # Custom output directory
  python main.py --interactive --output ./my_results
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    mode_group.add_argument(
        '--batch', '-b',
        type=str,
        metavar='FILE',
        help='Run in batch mode with questions from FILE'
    )
    
    # Configuration
    parser.add_argument(
        '--config', '-c',
        type=str,
        metavar='FILE',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--budget',
        type=float,
        metavar='AMOUNT',
        help='Budget limit in dollars (e.g., 10.0)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        metavar='N',
        help='Maximum optimization iterations'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./output',
        metavar='DIR',
        help='Output directory (default: ./output)'
    )
    
    # Export
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export results after optimization'
    )
    
    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_arguments()
    
    # Create controller
    controller = create_cli_controller(
        config_path=args.config,
        budget_limit=args.budget,
        max_iterations=args.max_iterations,
        output_dir=args.output
    )
    
    # Initialize components
    if not controller.initialize_components():
        sys.exit(1)
    
    # Run selected mode
    if args.interactive:
        controller.interactive_mode()
    elif args.batch:
        controller.batch_mode(args.batch)
        if args.export:
            controller.export_results()
    
    print("\n  Thank you for using Astra-AI!\n")


if __name__ == "__main__":
    main()
