"""
Simple step-by-step test for LangChain migration
"""

import os
from dotenv import load_dotenv
load_dotenv()

print("="*70)
print("Step-by-Step Migration Test")
print("="*70)

# Step 1: Check imports
print("\n📦 Step 1: Checking imports...")
try:
    import langchain
    print("  ✅ langchain")
except ImportError as e:
    print(f"  ❌ langchain: {e}")
    exit(1)

try:
    import langgraph
    print("  ✅ langgraph")
except ImportError as e:
    print(f"  ❌ langgraph: {e}")
    exit(1)

try:
    from langchain_huggingface import HuggingFaceEndpoint
    print("  ✅ langchain-huggingface")
except ImportError as e:
    print(f"  ❌ langchain-huggingface: {e}")
    exit(1)

# Step 2: Check API keys
print("\n🔑 Step 2: Checking API keys...")
hf_key = os.getenv("HUGGINGFACE_API_KEY")
if hf_key:
    print(f"  ✅ HUGGINGFACE_API_KEY found ({hf_key[:10]}...)")
else:
    print("  ❌ HUGGINGFACE_API_KEY not found")
    exit(1)

# Step 3: Import Judge Agent
print("\n⚖️ Step 3: Importing Judge Agent...")
try:
    from agents.langchain_judge import LangChainJudgeAgent
    print("  ✅ Judge Agent imported")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 4: Initialize Judge Agent
print("\n⚖️ Step 4: Initializing Judge Agent...")
try:
    judge = LangChainJudgeAgent(
        model_name="mistralai/Mistral-7B-Instruct-v0.2",
        enable_langsmith=False
    )
    print("  ✅ Judge Agent initialized")
except Exception as e:
    print(f"  ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 5: Test Judge evaluation
print("\n⚖️ Step 5: Testing Judge evaluation...")
try:
    result = judge.evaluate(
        question="What is 2+2?",
        answer="4",
        explanation="Adding 2 and 2 gives us 4."
    )
    print(f"  ✅ Evaluation complete!")
    print(f"     Composite Score: {result['composite_score']:.2f}/10")
    print(f"     Individual Scores:")
    for criterion, score in result['scores'].items():
        print(f"       - {criterion}: {score:.1f}/10")
except Exception as e:
    print(f"  ❌ Evaluation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 6: Import Optimizer Agent
print("\n🔧 Step 6: Importing Optimizer Agent...")
try:
    from agents.langchain_optimizer import LangChainOptimizerAgent
    print("  ✅ Optimizer Agent imported")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    exit(1)

# Step 7: Initialize Optimizer Agent
print("\n🔧 Step 7: Initializing Optimizer Agent...")
try:
    optimizer = LangChainOptimizerAgent(
        model_name="meta-llama/Meta-Llama-3-8B-Instruct",
        enable_langsmith=False
    )
    print("  ✅ Optimizer Agent initialized")
except Exception as e:
    print(f"  ❌ Initialization failed: {e}")
    exit(1)

# Step 8: Test Optimizer
print("\n🔧 Step 8: Testing Optimizer...")
try:
    mock_evaluations = [{
        "scores": {
            "correctness": 6.0,
            "clarity": 5.0,
            "reasoning": 5.0,
            "relevance": 7.0,
            "conciseness": 6.0
        },
        "composite_score": 5.8,
        "suggestions": ["Add more structure", "Be more specific"],
        "flags": []
    }]
    
    result = optimizer.optimize(
        current_prompt="Answer: {question}",
        evaluations=mock_evaluations
    )
    print(f"  ✅ Optimization complete!")
    print(f"     Modifications made: {len(result['modifications_made'])}")
    print(f"     Optimized prompt length: {len(result['optimized_prompt'])} chars")
except Exception as e:
    print(f"  ❌ Optimization failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 9: Import Orchestrator
print("\n🎮 Step 9: Importing Orchestrator...")
try:
    from agents.langgraph_orchestrator import LangGraphOrchestrator
    print("  ✅ Orchestrator imported")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    exit(1)

# Step 10: Initialize Orchestrator
print("\n🎮 Step 10: Initializing Orchestrator...")
try:
    orchestrator = LangGraphOrchestrator(
        generator_model="meta-llama/Meta-Llama-3-8B-Instruct",
        judge_model="mistralai/Mistral-7B-Instruct-v0.2",
        optimizer_model="meta-llama/Meta-Llama-3-8B-Instruct",
        max_iterations=2,
        convergence_threshold=8.5,
        enable_langsmith=False
    )
    print("  ✅ Orchestrator initialized")
except Exception as e:
    print(f"  ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*70)
print("🎉 ALL STEPS PASSED!")
print("="*70)
print("\nThe migration is working! Now run full test:")
print("  python test_langchain_migration.py")
