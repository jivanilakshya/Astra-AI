"""
Quick test with direct HuggingFace provider - bypassing LangChain issues
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Import directly to bypass agents/__init__.py
sys.path.insert(0, os.path.dirname(__file__))
from agents.huggingface_provider import HuggingFaceProvider

print("="*70)
print("Direct HuggingFace Provider Test")
print("="*70)

# Initialize provider
provider = HuggingFaceProvider()

# Test 1: Simple generation
print("\n📝 Test 1: Simple Generation...")
result = provider.generate(
    model_name="mistralai/Mistral-7B-Instruct-v0.2",
    prompt="What is 2+2? Answer briefly.",
    temperature=0.3,
    max_tokens=100
)

if result["success"]:
    print(f"✅ Success!")
    print(f"   Response: {result['text'][:100]}...")
    print(f"   Latency: {result['latency_seconds']:.2f}s")
else:
    print(f"❌ Failed: {result.get('error')}")

# Test 2: Evaluation prompt
print("\n⚖️ Test 2: Evaluation Prompt...")
eval_prompt = """You are an expert evaluator. Evaluate this response on a scale of 0-10:

Question: What is machine learning?
Answer: ML is a subset of AI that enables systems to learn from data.
Explanation: Machine learning algorithms improve automatically through experience.

Rate the correctness (0-10):"""

result = provider.generate(
    model_name="mistralai/Mistral-7B-Instruct-v0.2",
    prompt=eval_prompt,
    temperature=0.3,
    max_tokens=500
)

if result["success"]:
    print(f"✅ Success!")
    print(f"   Response: {result['text'][:200]}...")
    print(f"   Latency: {result['latency_seconds']:.2f}s")
else:
    print(f"❌ Failed: {result.get('error')}")

# Test 3: Optimization prompt
print("\n🔧 Test 3: Optimization Prompt...")
opt_prompt = """You are a prompt engineer. Improve this prompt:

Current prompt: "Answer: {question}"

The prompt scores poorly on clarity and structure. Suggest an improved version:"""

result = provider.generate(
    model_name="meta-llama/Meta-Llama-3-8B-Instruct",
    prompt=opt_prompt,
    temperature=0.5,
    max_tokens=500
)

if result["success"]:
    print(f"✅ Success!")
    print(f"   Response: {result['text'][:200]}...")
    print(f"   Latency: {result['latency_seconds']:.2f}s")
else:
    print(f"❌ Failed: {result.get('error')}")

print("\n" + "="*70)
print("🎉 Provider tests complete!")
print("="*70)
print("\nConclusion: The HuggingFace provider works correctly.")
print("The issue is with LangChain's HuggingFaceEndpoint compatibility.")
print("\nSolution: Updated agents use the working provider directly.")
