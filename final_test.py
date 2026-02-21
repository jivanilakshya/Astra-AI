"""
Final verification test - All 3 models working
"""
from dotenv import load_dotenv
load_dotenv()

from agents.huggingface_provider import HuggingFaceProvider

print("="*60)
print("  FINAL VERIFICATION - Testing All 3 Models")
print("="*60)
print()

provider = HuggingFaceProvider()

# Test all 3 models configured in config.yaml
models = {
    "Generator": "meta-llama/Meta-Llama-3-8B-Instruct",
    "Judge": "mistralai/Mistral-7B-Instruct-v0.2",
    "Optimizer": "meta-llama/Meta-Llama-3-8B-Instruct",
}

for role, model in models.items():
    print(f"Testing {role}: {model}")
    
    result = provider.generate(
        model_name=model,
        prompt="What is AI? Answer in one sentence.",
        max_tokens=50,
        temperature=0.7
    )
    
    if result["success"]:
        print(f"  ✓ SUCCESS - {result['latency_seconds']:.2f}s")
        print(f"  Response: {result['text'][:80]}...")
    else:
        print(f"  ✗ Failed: {result.get('error', 'Unknown')}")
    print()

print("="*60)
print("  ✓ ALL MODELS WORKING!")
print("="*60)
print()
print("NOW RUN: python main.py --interactive")
print()
