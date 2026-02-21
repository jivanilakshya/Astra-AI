"""
Test LangChain Migration
Run this to verify everything works with LangSmith observability
"""

import os
from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("🧪 Testing LangChain/LangGraph Migration")
print("="*70)

# Check dependencies
print("\n📦 Checking dependencies...")
try:
    import langchain
    print("  ✅ langchain installed")
except ImportError:
    print("  ❌ langchain not found - run: pip install -r requirements_langchain.txt")
    exit(1)

try:
    import langgraph
    print("  ✅ langgraph installed")
except ImportError:
    print("  ❌ langgraph not found - run: pip install -r requirements_langchain.txt")
    exit(1)

try:
    from langchain_huggingface import HuggingFaceEndpoint
    print("  ✅ langchain-huggingface installed")
except ImportError:
    print("  ❌ langchain-huggingface not found - run: pip install -r requirements_langchain.txt")
    exit(1)

try:
    import langsmith
    print("  ✅ langsmith installed")
    langsmith_available = True
except ImportError:
    print("  ⚠️  langsmith not found (optional) - install for observability")
    langsmith_available = False

# Check API keys
print("\n🔑 Checking API keys...")
hf_key = os.getenv("HUGGINGFACE_API_KEY")
if hf_key:
    print(f"  ✅ HUGGINGFACE_API_KEY found ({hf_key[:10]}...)")
else:
    print("  ❌ HUGGINGFACE_API_KEY not found in .env")
    exit(1)

ls_key = os.getenv("LANGCHAIN_API_KEY")
if ls_key:
    print(f"  ✅ LANGCHAIN_API_KEY found ({ls_key[:10]}...) - LangSmith enabled!")
    enable_langsmith = True
else:
    print("  ⚠️  LANGCHAIN_API_KEY not found - LangSmith disabled")
    print("     Get free key at: https://smith.langchain.com")
    enable_langsmith = False

# Test 1: Judge Agent
print("\n" + "="*70)
print("Test 1: LangChain Judge Agent")
print("="*70)

try:
    from agents.langchain_judge import create_langchain_judge
    
    judge = create_langchain_judge(enable_langsmith=enable_langsmith)
    
    result = judge.evaluate(
        question="What is machine learning?",
        answer="ML is a subset of AI that enables systems to learn from data.",
        explanation="Machine learning algorithms improve automatically through experience without being explicitly programmed."
    )
    
    print(f"\n✅ Judge Test Passed!")
    print(f"   Composite Score: {result['composite_score']:.2f}/10")
    print(f"   Scores: {result['scores']}")
    print(f"   Latency: {result['metadata']['latency_ms']:.0f}ms")
    
except Exception as e:
    print(f"\n❌ Judge Test Failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 2: Optimizer Agent
print("\n" + "="*70)
print("Test 2: LangChain Optimizer Agent")
print("="*70)

try:
    from agents.langchain_optimizer import create_langchain_optimizer
    
    optimizer = create_langchain_optimizer(enable_langsmith=enable_langsmith)
    
    mock_evaluations = [
        {
            "scores": {"correctness": 6, "clarity": 5, "reasoning": 5, "relevance": 7, "conciseness": 6},
            "composite_score": 5.8,
            "suggestions": ["Add more structure", "Be more specific"],
            "flags": []
        }
    ]
    
    result = optimizer.optimize(
        current_prompt="Answer: {question}",
        evaluations=mock_evaluations
    )
    
    print(f"\n✅ Optimizer Test Passed!")
    print(f"   Modifications: {len(result['modifications_made'])}")
    print(f"   Expected improvements: {len(result['expected_improvements'])}")
    print(f"   Optimized prompt length: {len(result['optimized_prompt'])} chars")
    print(f"   Latency: {result['metadata']['latency_ms']:.0f}ms")
    
except Exception as e:
    print(f"\n❌ Optimizer Test Failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Full Orchestrator (Short Run)
print("\n" + "="*70)
print("Test 3: LangGraph Orchestrator (Full Workflow)")
print("="*70)

try:
    from agents.langgraph_orchestrator import create_langchain_orchestrator
    
    orchestrator = create_langchain_orchestrator(
        max_iterations=2,  # Short test - only 2 iterations
        convergence_threshold=8.5,
        enable_langsmith=enable_langsmith
    )
    
    test_questions = [
        "What is artificial intelligence?",
        "Explain the concept of neural networks."
    ]
    
    initial_prompt = """Answer the following question clearly and accurately.

Question: {question}

Provide a detailed answer:"""
    
    print(f"\n🚀 Running optimization with {len(test_questions)} questions...")
    print(f"   Max iterations: 2 (test mode)")
    
    results = orchestrator.run_optimization(
        questions=test_questions,
        initial_prompt=initial_prompt
    )
    
    print(f"\n✅ Orchestrator Test Passed!")
    print(f"\n📊 Results:")
    print(f"   Initial Score: {results['initial_score']:.2f}/10")
    print(f"   Final Score: {results['final_score']:.2f}/10")
    print(f"   Improvement: +{results['improvement']:.2f}")
    print(f"   Iterations: {results['iterations']}")
    print(f"   Converged: {results['converged']}")
    
    # Save results
    output_dir = orchestrator.export_results(results)
    
    print(f"\n💾 Results saved to: {output_dir}")
    print(f"   - results.json")
    print(f"   - optimized_prompt.txt")
    print(f"   - prompt_history.json")
    
except Exception as e:
    print(f"\n❌ Orchestrator Test Failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Success!
print("\n" + "="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)

if enable_langsmith:
    print("\n🔍 View traces in LangSmith:")
    print("   https://smith.langchain.com")
    print(f"\n   Projects to check:")
    print(f"   - astra-ai-judge")
    print(f"   - astra-ai-optimizer")
    print(f"   - astra-ai-orchestrator")
else:
    print("\n💡 Enable LangSmith for observability:")
    print("   1. Get free API key: https://smith.langchain.com")
    print("   2. Add to .env: LANGCHAIN_API_KEY=your_key_here")
    print("   3. Run test again")

print("\n🎉 LangChain migration successful!")
print("\nNext steps:")
print("  1. Check the optimized prompt in: output/session_*/optimized_prompt.txt")
print("  2. Run full optimization: python main_langchain.py")
print("  3. View LangSmith traces (if enabled)")
