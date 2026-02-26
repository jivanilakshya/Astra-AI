"""Quick test to verify LangSmith tracing works end-to-end."""
import os
from dotenv import load_dotenv
load_dotenv(override=True)
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ.setdefault('LANGCHAIN_PROJECT', 'astra-ai')

import time

print("=" * 60)
print("  LangSmith Tracing Test")
print("=" * 60)

# 1. Test HuggingFace generation
print("\n[1] Testing HuggingFace generation...")
from agents.huggingface_provider import HuggingFaceProvider
p = HuggingFaceProvider()
r = p.generate(
    model_name="meta-llama/Meta-Llama-3-8B-Instruct",
    prompt="What is photosynthesis? Answer in 2 sentences.",
    max_tokens=100,
)
print(f"    Success: {r['success']}")
print(f"    Answer: {r['text'][:200]}")

# 2. Test Judge with @traceable
print("\n[2] Testing Judge Agent (with @traceable)...")
from agents.langchain_judge import create_langchain_judge
judge = create_langchain_judge(enable_langsmith=True)
ev = judge.evaluate(
    question="What is photosynthesis?",
    answer=r["text"],
    explanation=r["text"],
)
print(f"    Judge composite score: {ev['composite_score']:.2f}")

# Give background trace sender time to flush
print("\n[3] Waiting for traces to flush...")
time.sleep(5)

print("\n" + "=" * 60)
print("  DONE!")
print(f"  Check traces at: https://smith.langchain.com")
print(f"  Project: {os.environ.get('LANGCHAIN_PROJECT', 'astra-ai')}")
print("=" * 60)
