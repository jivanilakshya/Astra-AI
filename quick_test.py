"""Quick test after fixing token"""
from dotenv import load_dotenv
load_dotenv()

import os
from huggingface_hub import InferenceClient

print("Testing HuggingFace with new token...\n")

api_key = os.getenv("HUGGINGFACE_API_KEY")
print(f"API Key: {api_key[:15]}...{api_key[-5:]}\n")

client = InferenceClient(token=api_key)

print("Trying text generation...")
try:
    result = client.text_generation(
        "Q: What is 2+2? A:",
        model="gpt2",
        max_new_tokens=20
    )
    print(f"✓ SUCCESS!\nResponse: {result}\n")
    print("🎉 HUGGINGFACE IS WORKING!")
    print("\nNow run: python main.py --interactive")
except Exception as e:
    print(f"✗ Still failing: {str(e)[:200]}")
    if "403" in str(e):
        print("\n⚠️  Token still doesn't have 'write' permission")
        print("Make sure you selected 'write' not 'read'!")
    elif "401" in str(e):
        print("\n⚠️  Invalid token - did you copy it correctly?")
