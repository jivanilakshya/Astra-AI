"""
CLI Controller for Astra-AI Self-Improving LLM System.

Provides command-line interface with:
- Interactive mode for step-by-step optimization
- Batch mode for automated runs
- Multi-model comparison
- Smart model routing with cost prediction
- Prompt optimization engine
- Developer / Production mode
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
from agents.huggingface_provider import AVAILABLE_MODELS

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
    AgentType,
    # New modules
    RuntimeMode,
    get_mode_manager,
    MultiModelEngine,
    SmartRouter,
    PromptEngine,
    CLIFormatter,
    get_tracing_manager,
)
from utils.cli_formatter import _c, Icons
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
        output_dir: str = "./output",
        mode: str = "production",
    ):
        """
        Initialize CLI Controller.
        
        Args:
            config_path: Path to configuration file
            budget_limit: Optional budget limit for LLM costs
            max_iterations: Maximum optimization iterations
            output_dir: Directory for output files
            mode: Runtime mode - "production" or "developer"
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
        
        # ── New: Runtime Mode ──
        runtime_mode = RuntimeMode.DEVELOPER if mode == "developer" else RuntimeMode.PRODUCTION
        self.mode_manager = get_mode_manager(runtime_mode)
        
        # ── New: CLI Formatter ──
        self.fmt = CLIFormatter()
        
        # ── New: Smart Router ──
        self.smart_router = SmartRouter(
            prefer_free=True,
            budget_limit=budget_limit,
            feedback_path=str(self.output_dir / "router_feedback.json"),
        )
        
        # ── New: Multi-Model Engine ──
        self.multi_model_engine = None  # initialized after HuggingFace provider
        
        # ── New: Prompt Engine ──
        self.prompt_engine = PromptEngine(
            history_path=str(self.output_dir / "prompt_history.json")
        )
        
        # ── New: Tracing Manager ──
        self.tracer = get_tracing_manager()
        
        # Initialize components (old)
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
        
        logger.info(f"CLI Controller initialized (session: {self.session_id}, mode: {mode})")
    
    def initialize_components(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print()
            self.fmt.print_status("Initializing system components...", "info")
            print()
            
            # Model selector (cost tracking)
            self.fmt.print_kv("[1/3] Module", "Model Selector & Cost Tracker")
            self.model_selector = create_model_selector(
                budget_limit=self.budget_limit,
                prefer_open_source=True,
                storage_path=str(self.output_dir / "cost_tracking")
            )
            self.fmt.print_status("Model Selector ready", "ok")
            
            # Analytics
            self.fmt.print_kv("[2/3] Module", "Analytics Agent")
            self.analytics = create_analytics(
                storage_path=str(self.output_dir / "analytics")
            )
            self.fmt.print_status("Analytics Agent ready", "ok")
            
            # LangGraph Orchestrator (creates generator, judge, optimizer internally)
            self.fmt.print_kv("[3/3] Module", "LangGraph Orchestrator (Generator + Judge + Optimizer)")
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
            self.fmt.print_status("LangGraph Orchestrator ready", "ok")
            
            # Multi-model engine (uses same HuggingFace provider)
            try:
                self.multi_model_engine = MultiModelEngine()
            except Exception:
                self.multi_model_engine = None
            
            print()
            self.fmt.print_status("All components initialized successfully!", "ok")
            
            # Show active models
            self.fmt.print_kv("Generator", gen_model)
            self.fmt.print_kv("Judge", judge_model)
            self.fmt.print_kv("Optimizer", opt_model)
            
            # Developer mode notice
            if self.mode_manager.is_developer:
                self.fmt.print_status("Developer mode ACTIVE - verbose output enabled", "info")
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
                with open(questions_path, 'r', encoding='utf-8') as f:
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
                with open(questions_path, 'r', encoding='utf-8') as f:
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
        self.fmt.print_header("ASTRA AI", "Self-Improving LLM System - Interactive Mode")

        if self.mode_manager.is_developer:
            self.fmt.print_status("Developer mode ACTIVE - verbose output enabled", "info")
            print()

        # Main interactive menu
        while True:
            self.fmt.divider(label="MAIN MENU")
            print()
            print(f"    1.  Run prompt optimization loop")
            print(f"    2.  Ask a single question")
            print(f"    3.  Compare multiple models (side-by-side)")
            print(f"    4.  Analyze & improve a prompt")
            print(f"    5.  Select / change model")
            print(f"    6.  Diagnose LangSmith tracing")
            print(f"    7.  View router statistics")
            print(f"    8.  Toggle Developer / Production mode")
            print(f"    9.  Exit")
            print()
            
            choice = input("  Select (1-9): ").strip()
            
            if choice == '1':
                self._interactive_optimization()
            elif choice == '2':
                self._interactive_single_question()
            elif choice == '3':
                self._interactive_compare_models()
            elif choice == '4':
                self._interactive_prompt_analysis()
            elif choice == '5':
                self._interactive_select_model()
            elif choice == '6':
                self._interactive_langsmith_diag()
            elif choice == '7':
                self._interactive_router_stats()
            elif choice == '8':
                self._toggle_mode()
            elif choice == '9':
                break
            else:
                self.fmt.print_status("Invalid option. Please enter 1-9.", "warn")
                print()
    
    def _toggle_mode(self):
        """Toggle between developer and production mode."""
        if self.mode_manager.is_developer:
            self.mode_manager.set_mode(RuntimeMode.PRODUCTION)
            self.fmt.print_status("Switched to PRODUCTION mode (final output only)", "info")
        else:
            self.mode_manager.set_mode(RuntimeMode.DEVELOPER)
            self.fmt.print_status("Switched to DEVELOPER mode (verbose debug output)", "info")
        print()
    
    def _interactive_select_model(self):
        """Let user browse and select a model."""
        self.fmt.print_section("Model Selection")

        print("    Available HuggingFace models (free tier):\n")
        print(f"    {'#':4s} {'Model ID':50s} {'Short Name':25s} {'Tier':15s}")
        print(f"    {'─'*4} {'─'*50} {'─'*25} {'─'*15}")
        for i, m in enumerate(AVAILABLE_MODELS, 1):
            print(f"    {i:<4d} {m['id']:50s} {m['name']:25s} {m['tier']:15s}")
        print(f"\n    {len(AVAILABLE_MODELS)+1}. Enter a custom model ID")
        print()

        choice = input("  Select model number: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(AVAILABLE_MODELS):
                selected = AVAILABLE_MODELS[idx]["id"]
            elif idx == len(AVAILABLE_MODELS):
                selected = input("  Enter custom model ID (e.g., org/model-name): ").strip()
                if not selected:
                    return
            else:
                self.fmt.print_status("Invalid selection.", "warn")
                return
        except ValueError:
            self.fmt.print_status("Invalid input.", "warn")
            return

        self._selected_model = selected
        self.fmt.print_status(f"Selected model: {selected}", "ok")

        # Ask what to apply it to
        print()
        print("    Apply this model to:")
        print("      1. Generator (answer generation)")
        print("      2. Judge (evaluation)")
        print("      3. Both Generator and Judge")
        print("      4. Just remember for next single-question")

        apply_choice = input("  Select (1-4): ").strip()

        config = get_config()
        if apply_choice in ('1', '3'):
            config.generator_model['model_name'] = selected
            self.fmt.print_status(f"Generator model set to: {selected}", "ok")
        if apply_choice in ('2', '3'):
            config.judge_model['model_name'] = selected
            self.fmt.print_status(f"Judge model set to: {selected}", "ok")
        if apply_choice in ('1', '2', '3'):
            # Re-initialize orchestrator with new models
            reinit = input("  Re-initialize components with new model? (yes/no): ").strip().lower()
            if reinit in ('yes', 'y'):
                self.fmt.print_status("Re-initializing components...", "info")
                self.initialize_components()
        print()
    
    def _interactive_single_question(self):
        """Ask a single question with cost prediction and routing."""
        self.fmt.print_section("Ask a Question")
        question = input("  Enter your question: ").strip()
        if not question:
            return
        
        # 1. Analyze prompt quality
        analysis = self.prompt_engine.analyze(question)
        self.fmt.print_prompt_analysis(analysis.to_dict())
        
        # 2. Auto-optimize if needed
        if analysis.quality_grade in ("D", "F"):
            self.fmt.print_status("Low-quality prompt detected. Auto-optimizing...", "warn")
            optimized = self.prompt_engine.optimize(question)
            print(f"\n    Original:  {question}")
            print(f"    Optimized: {optimized}\n")
            use_opt = input("  Use optimized prompt? (yes/no): ").strip().lower()
            if use_opt in ('yes', 'y'):
                question = optimized
        
        # 3. Smart routing + cost prediction
        prediction = self.smart_router.predict_cost(question)
        self.fmt.print_cost_prediction(prediction.to_dict())
        
        # 4. Let user pick model or accept recommendation
        model = getattr(self, '_selected_model', None) or prediction.recommended_model
        print(f"    Current model: {model}")
        print(f"    [Enter] Accept  |  [m] Pick another model")
        model_choice = input("  > ").strip().lower()
        if model_choice == 'm':
            print()
            for i, m in enumerate(AVAILABLE_MODELS, 1):
                print(f"      {i}. {m['id']:50s}  ({m['tier']})")
            pick = input(f"  Select (1-{len(AVAILABLE_MODELS)}): ").strip()
            try:
                idx = int(pick) - 1
                if 0 <= idx < len(AVAILABLE_MODELS):
                    model = AVAILABLE_MODELS[idx]["id"]
            except ValueError:
                pass
        
        proceed = input(f"\n  Send to {model}? (yes/no): ").strip().lower()
        if proceed not in ('yes', 'y'):
            return
        
        # 5. Generate answer
        self.fmt.print_status(f"Sending to {model}...", "info")
        
        self.mode_manager.log_prompt("generator", question)
        
        try:
            provider = HuggingFaceProvider()
            result = provider.generate(
                model_name=model,
                prompt=question,
                temperature=0.7,
                max_tokens=500,
            )
            
            self.mode_manager.log_response("generator", result.get("text", ""))
            
            # Trace to local file
            self.tracer.trace(
                agent="generator",
                action="single_question",
                input_data={"question": question, "model": model},
                output_data=result,
                latency_ms=result.get("latency_seconds", 0) * 1000,
            )
            
            # Format result for display
            display_result = {
                "model_name": model,
                "response_text": result.get("text", ""),
                "success": result.get("success", False),
                "latency_seconds": result.get("latency_seconds", 0),
                "output_tokens_est": len(result.get("text", "")) // 4,
                "cost_estimate": prediction.cost_estimate_usd,
                "error": result.get("error"),
            }
            self.fmt.print_model_result(display_result)
            
            # Record feedback for router
            self.smart_router.record_feedback(
                prompt=question,
                model_used=model,
                quality_score=7.0 if result.get("success") else 0.0,
                latency_seconds=result.get("latency_seconds", 0),
                cost_usd=prediction.cost_estimate_usd,
                success=result.get("success", False),
            )
            
        except Exception as e:
            self.fmt.print_status(f"Error: {e}", "error")
        
        print()
    
    def _interactive_compare_models(self):
        """Compare multiple models side-by-side with prompt optimization."""
        if not self.multi_model_engine:
            self.fmt.print_status("Multi-model engine not available", "error")
            return
        
        self.fmt.print_section("Multi-Model Comparison")
        prompt = input("  Enter prompt to compare: ").strip()
        if not prompt:
            return
        
        # Step 1: Analyze & optimize prompt
        analysis = self.prompt_engine.analyze(prompt)
        self.fmt.print_prompt_analysis(analysis.to_dict())
        
        optimized_prompt = None
        if analysis.quality_grade not in ("A",):
            optimized = self.prompt_engine.optimize(prompt)
            if optimized != prompt:
                print(f"    {_c('cyan', 'Original:')}  {prompt}")
                print(f"    {_c('green', 'Optimized:')} {optimized[:120]}{'...' if len(optimized) > 120 else ''}")
                print()
                use_opt = input("  Use optimized prompt? (yes/no) [yes]: ").strip().lower()
                if use_opt not in ('no', 'n'):
                    optimized_prompt = optimized
                    self.fmt.print_status("Using optimized prompt for comparison", "ok")
                print()
        
        # Step 2: Show cost prediction
        prediction = self.smart_router.predict_cost(optimized_prompt or prompt)
        self.fmt.print_cost_prediction(prediction.to_dict())
        
        # Step 3: Let user pick models
        print("    Available models:")
        for i, m in enumerate(AVAILABLE_MODELS, 1):
            print(f"      {i}. {m['id']:50s}  ({m['tier']})")
        print()
        print("    Enter model numbers to compare (comma-separated), or press Enter for defaults:")
        print(f"    Defaults: 1, 2, 3  (Llama 3, Mistral, Qwen 2.5)")
        
        picks = input("  > ").strip()
        
        if picks:
            models = []
            for p in picks.split(','):
                p = p.strip()
                try:
                    idx = int(p) - 1
                    if 0 <= idx < len(AVAILABLE_MODELS):
                        models.append(AVAILABLE_MODELS[idx]["id"])
                except ValueError:
                    # Treat as custom model id
                    if '/' in p:
                        models.append(p)
        else:
            models = [
                "meta-llama/Meta-Llama-3-8B-Instruct",
                "mistralai/Mistral-7B-Instruct-v0.2",
                "Qwen/Qwen2.5-7B-Instruct",
            ]
        
        if len(models) < 2:
            self.fmt.print_status("Need at least 2 models to compare.", "warn")
            return
        
        self.fmt.print_status(f"Comparing {len(models)} models...", "info")
        for m in models:
            print(f"      - {m}")
        print()
        
        report = self.multi_model_engine.compare(
            prompt, models=models, optimized_prompt=optimized_prompt
        )
        report_dict = report.to_dict()
        if optimized_prompt:
            report_dict["optimized_prompt"] = optimized_prompt
        self.fmt.print_comparison(report_dict)
    
    def _interactive_prompt_analysis(self):
        """Analyze, optimize, and optionally test a prompt."""
        print()
        prompt = input("  Enter prompt to analyze: ").strip()
        if not prompt:
            return
        
        # Analyze
        analysis = self.prompt_engine.analyze(prompt)
        self.fmt.print_prompt_analysis(analysis.to_dict())
        
        # Offer optimization
        if analysis.quality_grade not in ("A",):
            optimize = input("  Optimize this prompt? (yes/no): ").strip().lower()
            if optimize in ('yes', 'y'):
                optimized = self.prompt_engine.optimize(prompt)
                
                print()
                print(f"  ┌{'─' * 68}┐")
                header = _c('bold', 'OPTIMIZED PROMPT')
                pad = ' ' * (67 - len('OPTIMIZED PROMPT'))
                print(f"  │ {header}{pad}│")
                print(f"  ├{'─' * 68}┤")
                for line in optimized.split('\n'):
                    display = line[:66]
                    print(f"  │ {display:<66s} │")
                print(f"  └{'─' * 68}┘")
                print()
                
                # Offer to test it live
                test = input("  Test this prompt with an LLM? (yes/no): ").strip().lower()
                if test in ('yes', 'y'):
                    config = get_config()
                    model = getattr(self, '_selected_model', None) or config.generator_model.get(
                        'model_name', 'meta-llama/Meta-Llama-3-8B-Instruct'
                    )
                    self.fmt.print_status(f"Sending optimized prompt to {model}...", "info")
                    
                    try:
                        provider = HuggingFaceProvider()
                        result = provider.generate(
                            model_name=model,
                            prompt=optimized,
                            temperature=0.7,
                            max_tokens=500,
                        )
                        
                        display_result = {
                            "model_name": model,
                            "response_text": result.get("text", ""),
                            "success": result.get("success", False),
                            "latency_seconds": result.get("latency_seconds", 0),
                            "output_tokens_est": len(result.get("text", "")) // 4,
                            "cost_estimate": 0,
                        }
                        self.fmt.print_model_result(display_result)
                    except Exception as e:
                        self.fmt.print_status(f"Error: {e}", "error")
        print()
    
    def _interactive_langsmith_diag(self):
        """Diagnose and fix LangSmith tracing."""
        self.fmt.print_section("LangSmith Tracing Diagnostics")
        
        diagnosis = self.tracer.diagnose_langsmith()
        
        status_color = {"healthy": "ok", "partial": "warn", "broken": "error"}.get(
            diagnosis["status"], "info"
        )
        self.fmt.print_status(f"Status: {diagnosis['status'].upper()}", status_color)
        
        # Environment variables
        print("\n    Environment Variables:")
        for var, val in diagnosis.get("env_vars", {}).items():
            icon = "[OK]" if val == "SET" else "[X]"
            print(f"      {icon} {var}: {val}")
        
        # Issues
        issues = diagnosis.get("issues", [])
        if issues:
            print("\n    Issues Found:")
            for issue in issues:
                print(f"      [!] {issue}")
        
        # Fixes
        fixes = diagnosis.get("fixes", [])
        if fixes:
            print("\n    Recommended Fixes:")
            for fix in fixes:
                print(f"      -> {fix}")
        
        # Offer auto-fix
        if issues:
            print()
            auto_fix = input("  Attempt auto-fix? (yes/no): ").strip().lower()
            if auto_fix in ('yes', 'y'):
                result = self.tracer.fix_langsmith()
                if result["fixed"]:
                    print("\n    Fixed:")
                    for f in result["fixed"]:
                        print(f"      [OK] {f}")
                if result["remaining"]:
                    print("\n    Still needs manual fix:")
                    for r in result["remaining"]:
                        print(f"      [!] {r}")
        
        # Fallback tracing info
        print(f"\n    Note: Built-in file tracing is always active at: {self.tracer.trace_dir}")
        print()
    
    def _interactive_router_stats(self):
        """Show router statistics."""
        stats = self.smart_router.get_router_stats()
        self.fmt.print_router_stats(stats)
        
        # Prompt engine learning stats
        learning = self.prompt_engine.get_learning_stats()
        if learning.get("scored", 0) > 0:
            self.fmt.print_section("Prompt Engine Learning")
            self.fmt.print_kv("Total optimizations", learning["total_optimizations"])
            self.fmt.print_kv("Scored outcomes", learning["scored"])
            self.fmt.print_kv("Avg outcome score", f"{learning['avg_score']:.2f}/10")
        print()
    
    def _interactive_optimization(self):
        """Run the standard optimization loop interactively."""
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
                print("\n  No questions provided.\n")
                return
            
            print(f"\n  {len(self.questions)} question(s) entered.\n")
        
        # Display questions
        print("  Questions to optimize:")
        for i, q in enumerate(self.questions, 1):
            print(f"    {i}. {q.question}")
        print()
        
        # Cost prediction for the set
        for q in self.questions:
            pred = self.smart_router.predict_cost(q.question)
            self.mode_manager.log_debug("router", "cost_prediction", pred.to_dict())
        
        # Ask for confirmation
        response = input("  Proceed with optimization? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("  Optimization cancelled.\n")
            return
        
        # Run optimization
        self._run_optimization()
        
        # Interactive results review
        self._interactive_results()
        
        # Clear questions for next run
        self.questions = []
    
    def batch_mode(self, questions_file: str, category: str = None,
                    difficulty: str = None, limit: int = None):
        """
        Run batch mode with questions from file.
        
        Args:
            questions_file: Path to questions file
            category: Filter by category (e.g., 'code_python', 'physics')
            difficulty: Filter by difficulty ('easy', 'medium', 'hard')
            limit: Max number of questions to process
        """
        self.fmt.print_header("ASTRA AI", "Batch Mode")
        
        # Load questions
        if not self.load_questions(questions_file):
            return
        
        # Apply filters
        if category:
            before = len(self.questions)
            self.questions = [q for q in self.questions if q.category == category]
            print(f"  Filtered by category '{category}': {before} → {len(self.questions)} questions")
        if difficulty:
            before = len(self.questions)
            self.questions = [q for q in self.questions if q.difficulty == difficulty]
            print(f"  Filtered by difficulty '{difficulty}': {before} → {len(self.questions)} questions")
        if limit and len(self.questions) > limit:
            self.questions = self.questions[:limit]
            print(f"  Limited to {limit} questions")
        
        if not self.questions:
            print("  No questions match the filters.\n")
            return
        
        print()
        
        # Run optimization
        self._run_optimization()
        
        # Show results and open interactive results menu
        if self.results:
            self._interactive_results()
    
    def _run_optimization(self):
        """Execute the optimization loop using LangGraph orchestrator."""
        self.fmt.print_header("OPTIMIZATION", "Starting self-improving loop")
        
        config = get_config()
        gen_model = config.generator_model.get('model_name', 'meta-llama/Meta-Llama-3-8B-Instruct')
        judge_model = config.judge_model.get('model_name', 'mistralai/Mistral-7B-Instruct-v0.2')
        
        self.fmt.print_kv("Generator", gen_model)
        self.fmt.print_kv("Judge", judge_model)
        self.fmt.print_kv("Questions", len(self.questions))
        self.fmt.print_kv("Max Iterations", self.max_iterations)
        self.fmt.print_kv("Threshold", self.config.convergence_threshold)
        if self.budget_limit:
            self.fmt.print_kv("Budget", f"${self.budget_limit:.2f}")
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
            self.fmt.print_header("COMPLETE", "Optimization finished")
            
        except Exception as e:
            print(f"\n  [ERROR] Optimization failed: {e}\n")
            logger.error(f"Optimization error: {e}", exc_info=True)
            self.results = None
    
    def _display_summary(self):
        """Display optimization results summary."""
        if not self.results:
            print("  No results to display.\n")
            return
        
        self.fmt.print_optimization_summary(self.results)
        
        # Cost summary
        if self.model_selector:
            try:
                cost_summary = self.model_selector.get_cost_summary()
                total_cost = cost_summary.get('total_cost', 0)
                self.fmt.print_kv("Total Cost", f"${total_cost:.4f}")
                if self.budget_limit:
                    self.fmt.print_kv("Budget", f"${self.budget_limit:.2f}")
            except Exception:
                pass
        print()
    
    def _interactive_results(self):
        """Interactive results exploration with beautiful menu."""
        if not self.results:
            return
        
        self._display_summary()
        
        while True:
            self.fmt.divider(label="What would you like to see?")
            print()
            print(f"    {_c('cyan', '1.')} {Icons.ROCKET}  View optimized prompt & answers")
            print(f"    {_c('cyan', '2.')} {Icons.CHART}  View score history (all iterations)")
            print(f"    {_c('cyan', '3.')} {Icons.BRAIN}  View all LLM answers")
            print(f"    {_c('cyan', '4.')} {Icons.SPARK}  View detailed metrics & breakdown")
            print(f"    {_c('cyan', '5.')} {Icons.MONEY}  View cost breakdown")
            print(f"    {_c('cyan', '6.')} {Icons.INFO}   Export results to file")
            print(f"    {_c('cyan', '7.')} {Icons.SHIELD} Developer debug log")
            print(f"    {_c('cyan', '8.')} {_c('green', Icons.CHECK)}  Ask a NEW question (uses optimized prompt)")
            print(f"    {_c('cyan', '9.')} {Icons.ARROW}  Back / Exit")
            print("    9. Back to main menu")
            
            choice = input("\n  Select (1-9): ").strip()
            
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
                self._view_debug_log()
            elif choice == '8':
                self._ask_with_optimized_prompt()
            elif choice == '9':
                break
            else:
                # Detect if user typed a question instead of a number
                if len(choice) > 3 and not choice.isdigit():
                    print(f"\n  It looks like you typed a question!")
                    use_it = input(f"  Answer \"{choice}\" using the optimized prompt? (yes/no): ").strip().lower()
                    if use_it in ('yes', 'y'):
                        self._ask_with_optimized_prompt(question=choice)
                else:
                    print("  Invalid option. Please enter 1-9.")
    
    def _ask_with_optimized_prompt(self, question: str = None):
        """Ask a new question using the optimized prompt from the current session."""
        if not self.results or 'final_prompt' not in self.results:
            self.fmt.print_status("No optimized prompt available.", "error")
            return
        
        optimized_prompt = self.results['final_prompt']
        
        self.fmt.print_section("New Question (Optimized Prompt)")
        
        if not question:
            question = input("  Enter your question: ").strip()
            if not question:
                return
        
        # Show what we're doing
        print(f"\n    Question:  {question}")
        print(f"    Using optimized prompt ({len(optimized_prompt)} chars)")
        
        # Format the optimized prompt with the new question
        try:
            formatted_prompt = optimized_prompt.replace("{question}", question)
        except Exception:
            formatted_prompt = f"{optimized_prompt}\n\nQuestion: {question}\n\nAnswer:"
        
        # Determine model
        config = get_config()
        model = getattr(self, '_selected_model', None) or config.generator_model.get(
            'model_name', 'meta-llama/Meta-Llama-3-8B-Instruct'
        )
        print(f"    Model: {model}")
        print()
        
        self.fmt.print_status(f"Generating answer with optimized prompt...", "info")
        
        try:
            provider = HuggingFaceProvider()
            result = provider.generate(
                model_name=model,
                prompt=formatted_prompt,
                temperature=0.7,
                max_tokens=500,
            )
            
            # Display the result
            answer_text = result.get("text", "")
            if result.get("success") and answer_text:
                print()
                print("  " + "=" * 66)
                print(f"  ANSWER (via optimized prompt)")
                print("  " + "=" * 66)
                print()
                for line in answer_text.split('\n'):
                    print(f"    {line}")
                print()
                print("  " + "-" * 66)
                latency = result.get("latency_seconds", 0)
                print(f"    Model: {model}  |  Latency: {latency:.1f}s")
                print("  " + "=" * 66)
            else:
                error = result.get("error", "No answer generated")
                self.fmt.print_status(f"Generation failed: {error}", "error")
            
            # Trace
            self.tracer.trace(
                agent="generator",
                action="optimized_prompt_question",
                input_data={"question": question, "model": model, "prompt_length": len(formatted_prompt)},
                output_data=result,
                latency_ms=result.get("latency_seconds", 0) * 1000,
            )
            
        except Exception as e:
            self.fmt.print_status(f"Error: {e}", "error")
        
        print()
    
    def _view_debug_log(self):
        """Show developer-mode debug log."""
        entries = self.mode_manager.get_debug_log()
        if not entries:
            print("\n  No debug entries. Switch to Developer mode (option 7 in main menu) to capture logs.")
            return
        self.fmt.print_developer_info(entries)
    
    def _view_prompt(self):
        """Display full optimized prompt + LLM answers from best iteration."""
        if not self.results or 'final_prompt' not in self.results:
            print("\n  No optimized prompt available.")
            return
        
        self.fmt.print_header("Optimized Prompt", "Final version after optimization")
        
        # Boxed prompt display
        prompt = self.results['final_prompt']
        box_width = min(self.fmt.width + 2, 74)
        print(f"  {_c('bold', '┌' + '─' * box_width + '┐')}")
        for line in prompt.split('\n'):
            display_line = line[:box_width - 2] if len(line) > box_width - 2 else line
            padding = box_width - len(display_line)
            print(f"  {_c('bold', '│')} {_c('cyan', display_line)}{' ' * max(0, padding)}{_c('bold', '│')}")
        print(f"  {_c('bold', '└' + '─' * box_width + '┘')}")
        print(f"    Length: {len(prompt)} characters")
        
        # Show prompt evolution if available
        iterations = self.results.get('raw_results', {}).get('iterations', [])
        if iterations:
            print()
            self.fmt.divider(label="Prompt Evolution")
            for i, iter_data in enumerate(iterations, 1):
                p = iter_data.get('prompt', '')
                score = iter_data.get('score', 0)
                sc = "green" if score >= 7 else "yellow" if score >= 4 else "red"
                print(f"    Iter {i}: {len(p):4d} chars  {_c(sc, f'{score:.1f}')}/10")
        
        # Show LLM answers from the BEST iteration
        if iterations:
            best_iter = max(iterations, key=lambda x: x.get('score', 0))
            best_idx = iterations.index(best_iter) + 1
            best_score = best_iter.get('score', 0)
            gen_results = best_iter.get('generated_outputs', [])
            
            print()
            self.fmt.divider(label=f"LLM Answers (Best: Iter {best_idx}, {best_score:.1f}/10)")
            
            for i, gen in enumerate(gen_results, 1):
                question = gen.get('question', 'N/A')
                answer = gen.get('answer', '')
                
                grade_icon = _c("green", Icons.CHECK) if answer else _c("red", Icons.CROSS)
                print(f"\n    {grade_icon} Q{i}: {_c('bold', question)}")
                
                if answer:
                    # Print answer (wrap long lines)
                    for line in answer.split('\n')[:12]:
                        print(f"      {line}")
                    if answer.count('\n') > 12:
                        print(f"      {_c('dim', f'... ({answer.count(chr(10)) - 12} more lines)')}")
                else:
                    error = gen.get('error', 'No answer generated')
                    print(f"      {_c('red', f'Error: {error}')}")
                
                meta = gen.get('metadata', {})
                latency = meta.get('latency_ms', 0)
                if latency:
                    print(f"      {_c('dim', f'Latency: {latency:.0f}ms')}")
        
        print()    
    def _view_history(self):
        """Display performance history."""
        if not self.results or 'performance_history' not in self.results:
            print("\n  No performance history available.")
            return
        
        self.fmt.print_header("Performance History", "Score trends across iterations")
        
        history = self.results['performance_history']
        for i, score in enumerate(history, 1):
            change = score - history[i - 2] if i > 1 else 0
            change_str = f"  {_c('green', f'+{change:.1f}')}" if change > 0 else f"  {_c('red', f'{change:.1f}')}" if change < 0 else ""
            self.fmt.print_score_bar(f"Iter {i}", score)
            if i > 1:
                trend = "improved" if change > 0 else "declined" if change < 0 else "unchanged"
                print(f"                    {_c('dim', f'{trend}{change_str}')}")
        
        # Summary
        if len(history) > 1:
            total_change = history[-1] - history[0]
            avg_change = total_change / (len(history) - 1)
            tc = "green" if total_change > 0 else "red"
            print()
            print(f"    Total change: {_c(tc, f'{total_change:+.1f}')}")
            print(f"    Avg per iteration: {_c(tc, f'{avg_change:+.1f}')}")
        print()
    
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
        """Display intermediate generation and evaluation results."""
        if not self.results or 'raw_results' not in self.results:
            print("\n  No intermediate results available.")
            return
        
        iterations = self.results['raw_results'].get('iterations', [])
        if not iterations:
            print("\n  No iteration data available.")
            return
        
        self.fmt.print_header("Answers & Evaluations", "All iterations")
        
        for iter_num, iter_data in enumerate(iterations, 1):
            score = iter_data.get('score', 0)
            sc = "green" if score >= 7 else "yellow" if score >= 4 else "red"
            
            self.fmt.divider(label=f"Iteration {iter_num}  |  Score: {score:.1f}/10")
            
            gen_results = iter_data.get('generated_outputs', [])
            eval_results = iter_data.get('evaluations', [])
            
            for i, gen in enumerate(gen_results, 1):
                question = gen.get('question', 'N/A')
                answer = gen.get('answer', '')
                
                # Get individual eval score
                e_score = 0
                if i - 1 < len(eval_results):
                    e_score = eval_results[i - 1].get('composite_score', 0)
                grade = "A" if e_score >= 8 else "B" if e_score >= 6 else "C" if e_score >= 4 else "D"
                g_color = "green" if e_score >= 7 else "yellow" if e_score >= 4 else "red"
                
                print(f"\n    {_c('cyan', f'Q{i}:')} {_c('bold', question)}")
                print(f"    Score: {_c(g_color, f'{e_score:.1f}/10')} ({grade})")
                
                if answer:
                    # Show first 8 lines of answer
                    lines = answer.strip().split('\n')
                    for line in lines[:8]:
                        print(f"      {line}")
                    if len(lines) > 8:
                        print(f"      {_c('dim', f'... ({len(lines) - 8} more lines)')}")
                else:
                    error = gen.get('error', 'No answer generated')
                    print(f"      {_c('red', f'Error: {error}')}")
                
                # Show individual criteria if available
                if i - 1 < len(eval_results):
                    ev = eval_results[i - 1]
                    scores = ev.get('scores', {})
                    criteria_line = " | ".join(
                        f"{c[:4].capitalize()}: {scores.get(c, 0):.0f}"
                        for c in ['correctness', 'clarity', 'reasoning', 'relevance', 'conciseness']
                    )
                    print(f"      {_c('dim', criteria_line)}")
            
            print()
        print()
    
    def _view_detailed_metrics(self):
        """Display detailed performance metrics with beautiful formatting."""
        if not self.results or 'raw_results' not in self.results:
            print("\n  No metrics available.")
            return
        
        raw_results = self.results.get('raw_results', {})
        iterations = raw_results.get('iterations', [])
        
        self.fmt.print_header("Detailed Performance Metrics")
        
        if not iterations:
            print("    No iteration data available.")
            print()
            return
        
        # ── Per-Iteration Breakdown ──────────────────────────────────────
        for it in iterations:
            iter_num = it.get('iteration', '?')
            score = it.get('score', 0.0)
            grade = "A" if score >= 8 else "B" if score >= 6 else "C" if score >= 4 else "D"
            grade_color = "green" if score >= 7 else "yellow" if score >= 4 else "red"
            duration = it.get('duration_seconds', 0)
            
            self.fmt.divider(label=f"Iteration {iter_num}")
            print(f"    Score: {_c(grade_color, f'{score:.1f}/10')}  ({grade})    Duration: {duration:.1f}s")
            
            # Per-question scores
            pq_scores = it.get('per_question_scores', [])
            if pq_scores:
                print()
                print(f"    {'#':3s} {'Question':<38s} {'Score':>7s} {'Correctness':>12s} {'Clarity':>8s} {'Reasoning':>10s}")
                print(f"    {'─' * 80}")
                for idx, pq in enumerate(pq_scores, 1):
                    q = pq.get('question', '?')
                    if len(q) > 36:
                        q = q[:33] + "..."
                    cs = pq.get('composite_score', 0)
                    scores = pq.get('scores', {})
                    sc = "green" if cs >= 7 else "yellow" if cs >= 4 else "red"
                    print(f"    {idx:3d} {q:<38s} {_c(sc, f'{cs:>5.1f}')}/10 "
                          f"{scores.get('correctness', 0):>10.1f} "
                          f"{scores.get('clarity', 0):>6.1f} "
                          f"{scores.get('reasoning', 0):>8.1f}")
            
            # Weak/strong criteria
            weak = it.get('weak_criteria', [])
            strong = it.get('strong_criteria', [])
            if weak or strong:
                print()
                if strong:
                    print(f"    {_c('green', 'Strengths:')} {', '.join(c.capitalize() for c in strong)}")
                if weak:
                    print(f"    {_c('red', 'Needs work:')} {', '.join(c.capitalize() for c in weak)}")
            
            # Optimization modifications
            mods = it.get('optimization_modifications', [])
            if mods:
                print(f"\n    {_c('cyan', 'Prompt changes:')}")
                for mod in mods[:3]:
                    print(f"      {Icons.ARROW} {mod[:70]}")
            print()
        
        # ── Overall Trends ───────────────────────────────────────────────
        history = self.results.get('performance_history', [])
        if len(history) > 1:
            improvements = [history[i] - history[i-1] for i in range(1, len(history))]
            avg_imp = sum(improvements) / len(improvements) if improvements else 0
            
            self.fmt.divider(label="Performance Trends")
            print(f"    Avg improvement per iteration: {_c('green' if avg_imp > 0 else 'red', f'{avg_imp:+.2f}')}")
            best_idx = improvements.index(max(improvements))
            worst_idx = improvements.index(min(improvements))
            print(f"    Best improvement:  Iteration {best_idx + 2} ({_c('green', f'{max(improvements):+.2f}')})")
            print(f"    Worst change:      Iteration {worst_idx + 2} ({_c('red', f'{min(improvements):+.2f}')})")
        
        # ── Issue summary across all iterations ─────────────────────────
        all_flags = []
        all_suggestions = []
        for it in iterations:
            for ev in it.get('evaluations', []):
                all_flags.extend(ev.get('flags', []))
                all_suggestions.extend(ev.get('suggestions', []))
        
        if all_flags:
            from collections import Counter
            flag_counts = Counter(all_flags)
            print()
            self.fmt.divider(label="Issues Detected")
            for flag, count in flag_counts.most_common(5):
                print(f"    {_c('yellow', Icons.WARN)} {flag}: {count} occurrences")
        
        if all_suggestions:
            from collections import Counter
            sugg_counts = Counter(all_suggestions)
            print()
            self.fmt.divider(label="Top Suggestions")
            for sugg, count in sugg_counts.most_common(5):
                print(f"    {Icons.ARROW} {sugg} ({count}x)")
        
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
    output_dir: str = "./output",
    mode: str = "production",
) -> CLIController:
    """
    Factory function to create CLI controller.
    
    Args:
        config_path: Path to configuration file
        budget_limit: Optional budget limit for LLM costs
        max_iterations: Maximum optimization iterations
        output_dir: Directory for output files
        mode: Runtime mode ("production" or "developer")
    
    Returns:
        CLIController instance
    """
    return CLIController(
        config_path=config_path,
        budget_limit=budget_limit,
        max_iterations=max_iterations,
        output_dir=output_dir,
        mode=mode,
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
  
  # Interactive mode with developer output
  python main.py --interactive --dev
  
  # Batch mode with questions file
  python main.py --batch questions.json
  
  # With budget limit
  python main.py --batch questions.txt --budget 10.0
  
  # Compare models
  python main.py --compare "What is AI?"
  
  # Analyze a prompt
  python main.py --analyze "tell me stuff"
  
  # Diagnose LangSmith tracing
  python main.py --diagnose-tracing
  
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
    mode_group.add_argument(
        '--compare',
        type=str,
        metavar='PROMPT',
        help='Compare multiple models on a single prompt'
    )
    mode_group.add_argument(
        '--analyze',
        type=str,
        metavar='PROMPT',
        help='Analyze and optimize a prompt'
    )
    mode_group.add_argument(
        '--diagnose-tracing',
        action='store_true',
        help='Diagnose LangSmith tracing configuration'
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
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Enable developer mode (verbose debug output)'
    )
    
    # Batch filtering
    parser.add_argument(
        '--category',
        type=str,
        metavar='CAT',
        help='Filter batch questions by category (e.g., code_python, physics)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Limit number of questions in batch mode (e.g., 5)'
    )
    parser.add_argument(
        '--difficulty',
        type=str,
        choices=['easy', 'medium', 'hard'],
        help='Filter batch questions by difficulty'
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
    
    # Determine runtime mode
    mode = "developer" if args.dev else "production"
    
    # Create controller
    controller = create_cli_controller(
        config_path=args.config,
        budget_limit=args.budget,
        max_iterations=args.max_iterations,
        output_dir=args.output,
        mode=mode,
    )
    
    # Handle quick commands that don't need full initialization
    if args.diagnose_tracing:
        controller._interactive_langsmith_diag()
        return
    
    if args.analyze:
        analysis = controller.prompt_engine.analyze(args.analyze)
        controller.fmt.print_prompt_analysis(analysis.to_dict())
        optimized = controller.prompt_engine.optimize(args.analyze)
        print(f"  ┌{'─' * 68}┐")
        header = _c('bold', 'OPTIMIZED PROMPT')
        pad = ' ' * (67 - len('OPTIMIZED PROMPT'))
        print(f"  │ {header}{pad}│")
        print(f"  ├{'─' * 68}┤")
        for line in optimized.split('\n'):
            display = line[:66]
            print(f"  │ {display:<66s} │")
        print(f"  └{'─' * 68}┘")
        print()
        return
    
    # Initialize components for modes that need them
    if not controller.initialize_components():
        sys.exit(1)
    
    # Handle compare mode
    if args.compare:
        if controller.multi_model_engine:
            # Optimize the prompt before comparing
            original_prompt = args.compare
            analysis = controller.prompt_engine.analyze(original_prompt)
            optimized_prompt = None
            
            if analysis.quality_grade not in ("A",):
                optimized_prompt = controller.prompt_engine.optimize(original_prompt)
                if optimized_prompt != original_prompt:
                    controller.fmt.print_status(f"Prompt auto-optimized (grade: {analysis.quality_grade})", "info")
            
            controller.fmt.print_status(f"Comparing models on: \"{original_prompt[:60]}\"", "info")
            if optimized_prompt:
                controller.fmt.print_status(f"Optimized prompt sent to models", "ok")
            
            report = controller.multi_model_engine.compare(
                original_prompt, optimized_prompt=optimized_prompt
            )
            report_dict = report.to_dict()
            if optimized_prompt:
                report_dict["optimized_prompt"] = optimized_prompt
            controller.fmt.print_comparison(report_dict)
        else:
            print("  Multi-model engine not available.")
        return
    
    # Run selected mode
    if args.interactive:
        controller.interactive_mode()
    elif args.batch:
        controller.batch_mode(
            args.batch,
            category=getattr(args, 'category', None),
            difficulty=getattr(args, 'difficulty', None),
            limit=getattr(args, 'limit', None)
        )
        if args.export:
            controller.export_results()
    
    print("\n  Thank you for using Astra-AI!\n")


if __name__ == "__main__":
    main()
