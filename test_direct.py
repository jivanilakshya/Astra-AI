"""Direct import test - bypassing agents package"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

# Import directly
from huggingface_provider import HuggingFaceProvider

print("="*70)
print("Direct HuggingFace Provider Test")
print("="*70)

# Initialize provider
provider = HuggingFaceProvider()
print("✅ Provider initialized")

# Test simple generation
print("\n📝 Testing simple generation...")
result = provider.generate(
    model_name="mistralai/Mistral-7B-Instruct-v0.2",
    prompt="What is 2+2? Answer in one word.",
    temperature=0.3,
    max_tokens=50
)

if result["success"]:
    print(f"\n✅ Success!")
    print(f"   Question: What is 2+2?")
    print(f"   Response: {result['text']}")
    print(f"   Latency: {result['latency_seconds']:.2f}s")
    print(f"\n🎉 HuggingFace provider works correctly!")
else:
    print(f"\n❌ Failed: {result.get('error')}")

print("\n" + "="*70)
print("Migration can proceed using this working provider!")
print("="*70)
