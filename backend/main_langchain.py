"""
Main entry point for LangChain-based system
Replaces DSPy with LangChain/LangGraph + LangSmith
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import LangChain orchestrator
from agents.langgraph_orchestrator import create_langchain_orchestrator


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Astra AI - LangChain/LangGraph Optimization System"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--questions",
        type=str,
        help="Path to questions file (one per line)"
    )
    
    parser.add_argument(
        "--prompt",
        type=str,
        help="Path to initial prompt template file"
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Maximum iterations (default: 5)"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=8.5,
        help="Convergence threshold score (default: 8.5)"
    )
    
    parser.add_argument(
        "--no-langsmith",
        action="store_true",
        help="Disable LangSmith tracing"
    )
    
    parser.add_argument(
        "--generator-model",
        type=str,
        default="meta-llama/Meta-Llama-3-8B-Instruct",
        help="Generator model"
    )
    
    parser.add_argument(
        "--judge-model",
        type=str,
        default="mistralai/Mistral-7B-Instruct-v0.2",
        help="Judge model"
    )
    
    parser.add_argument(
        "--optimizer-model",
        type=str,
        default="meta-llama/Meta-Llama-3-8B-Instruct",
        help="Optimizer model"
    )
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "="*70)
    print("🤖 Astra AI - LangChain/LangGraph Optimization System")
    print("="*70)
    
    # Interactive mode
    if args.interactive:
        run_interactive_mode(args)
    else:
        # Batch mode
        if not args.questions:
            print("\n❌ Error: --questions required for batch mode")
            print("   Use --interactive for interactive mode")
            return
        
        run_batch_mode(args)


def run_interactive_mode(args):
    """Run interactive mode"""
    print("\n📝 Interactive Mode")
    print("\nEnter your questions (one per line, empty line to finish):")
    
    questions = []
    while True:
        try:
            line = input(f"Question {len(questions) + 1}: ").strip()
            if not line:
                break
            questions.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    if not questions:
        print("\n❌ No questions entered")
        return
    
    # Get initial prompt
    print(f"\nEnter initial prompt template (must contain {{question}}):")
    print("(Press Enter twice to finish)\n")
    
    prompt_lines = []
    empty_count = 0
    while True:
        try:
            line = input()
            if not line:
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                prompt_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    
    initial_prompt = "\n".join(prompt_lines)
    
    if not initial_prompt or "{question}" not in initial_prompt:
        print("\n⚠️  No prompt entered or missing {question} placeholder")
        print("   Using default prompt...")
        initial_prompt = """Answer the following question clearly and accurately.

Question: {question}

Provide a detailed answer:"""
    
    # Run optimization
    run_optimization(questions, initial_prompt, args)


def run_batch_mode(args):
    """Run batch mode from files"""
    print(f"\n📁 Batch Mode - Loading from files...")
    
    # Load questions
    questions_path = Path(args.questions)
    if not questions_path.exists():
        print(f"\n❌ Questions file not found: {questions_path}")
        return
    
    with open(questions_path, 'r', encoding='utf-8') as f:
        questions = [line.strip() for line in f if line.strip()]
    
    print(f"   ✅ Loaded {len(questions)} questions from {questions_path}")
    
    # Load prompt
    if args.prompt:
        prompt_path = Path(args.prompt)
        if not prompt_path.exists():
            print(f"\n❌ Prompt file not found: {prompt_path}")
            return
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            initial_prompt = f.read()
        
        print(f"   ✅ Loaded prompt from {prompt_path}")
    else:
        print("   ⚠️  No prompt file specified, using default...")
        initial_prompt = """Answer the following question clearly and accurately.

Question: {question}

Provide a detailed answer:"""
    
    # Run optimization
    run_optimization(questions, initial_prompt, args)


def run_optimization(questions, initial_prompt, args):
    """Run the optimization workflow"""
    print(f"\n🔧 Configuration:")
    print(f"   Generator: {args.generator_model}")
    print(f"   Judge: {args.judge_model}")
    print(f"   Optimizer: {args.optimizer_model}")
    print(f"   Max iterations: {args.iterations}")
    print(f"   Convergence threshold: {args.threshold}")
    print(f"   LangSmith: {'Disabled' if args.no_langsmith else 'Enabled' }")
    
    # Create orchestrator
    print(f"\n🚀 Initializing orchestrator...")
    
    orchestrator = create_langchain_orchestrator(
        generator_model=args.generator_model,
        judge_model=args.judge_model,
        optimizer_model=args.optimizer_model,
        max_iterations=args.iterations,
        convergence_threshold=args.threshold,
        enable_langsmith=not args.no_langsmith
    )
    
    # Run optimization
    print(f"\n▶️  Starting optimization with {len(questions)} questions...")
    
    results = orchestrator.run_optimization(
        questions=questions,
        initial_prompt=initial_prompt
    )
    
    # Display results
    print("\n" + "="*70)
    print("📊 OPTIMIZATION COMPLETE")
    print("="*70)
    
    print(f"\n🎯 Performance:")
    print(f"   Initial Score: {results['initial_score']:.2f}/10")
    print(f"   Final Score: {results['final_score']:.2f}/10")
    print(f"   Improvement: {'+' if results['improvement'] >= 0 else ''}{results['improvement']:.2f}")
    print(f"   Iterations: {results['iterations']}/{args.iterations}")
    print(f"   Converged: {'✅ Yes' if results['converged'] else '❌ No'}")
    
    print(f"\n📈 Performance History:")
    for i, score in enumerate(results['performance_history'], 1):
        bar = "█" * int(score)
        improvement = score - results['performance_history'][0] if i > 1 else 0
        print(f"   Iteration {i}: {score:.2f}/10 {bar} ({'+' if improvement >= 0 else ''}{improvement:.2f})")
    
    print(f"\n📝 Optimized Prompt:")
    print("   " + "-"*66)
    for line in results['final_prompt'].split('\n')[:10]:  # First 10 lines
        print(f"   {line}")
    if len(results['final_prompt'].split('\n')) > 10:
        print(f"   ... ({len(results['final_prompt'].split('\n')) - 10} more lines)")
    print("   " +"-"*66)
    
    # Export results
    output_dir = orchestrator.export_results(results)
    
    print(f"\n💾 Results exported:")
    print(f"   📁 Directory: {output_dir}")
    print(f"   📄 results.json - Full results")
    print(f"   📄 optimized_prompt.txt - Final prompt")
    print(f"   📄 prompt_history.json - Evolution history")
    
    # LangSmith info
    if not args.no_langsmith and os.getenv("LANGCHAIN_API_KEY"):
        print(f"\n🔍 View traces in LangSmith:")
        print(f"   https://smith.langchain.com")
        print(f"   Projects: astra-ai-judge, astra-ai-optimizer, astra-ai-orchestrator")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
