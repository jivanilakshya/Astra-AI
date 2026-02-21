"""Test LangChain Judge Agent with working provider"""

import sys
import os

# Add to path to import directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from langchain_judge import LangChainJudgeAgent

print("="*70)
print("LangChain Judge Agent Test")
print("="*70)

# Initialize judge
print("\n⚖️ Initializing Judge Agent...")
judge = LangChainJudgeAgent(
    model_name="mistralai/Mistral-7B-Instruct-v0.2",
    temperature=0.3,
    enable_langsmith=False
)

# Test evaluation
print("\n⚖️ Running evaluation...")
result = judge.evaluate(
    question="What is machine learning?",
    answer="Machine learning is a subset of artificial intelligence.",
    explanation="ML enables systems to learn from data automatically."
)

print(f"\n✅ Evaluation complete!")
print(f"\n📊 Results:")
print(f"   Composite Score: {result['composite_score']:.2f}/10")
print(f"\n   Individual Scores:")
for criterion, score in result['scores'].items():
    print(f"     - {criterion}: {score:.1f}/10")

print(f"\n   Latency: {result['metadata']['latency_ms']:.0f}ms")
print(f"   Status: {result['metadata']['status']}")

if result['suggestions']:
    print(f"\n   Suggestions:")
    for i, suggestion in enumerate(result['suggestions'][:3], 1):
        print(f"     {i}. {suggestion}")

print("\n" + "="*70)
print("🎉 LangChain Judge Agent WORKS!")
print("="*70)
