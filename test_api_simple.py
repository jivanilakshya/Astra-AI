"""Simple HuggingFace API test"""
import os
import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")
print(f"API Key: {api_key[:15]}...")

headers = {"Authorization": f"Bearer {api_key}"}
payload = {
    "inputs": "Hello, my name is",
    "parameters": {"max_new_tokens": 20}
}

# Test URL (try different formats)
urls_to_try = [
    "https://router.huggingface.co/gpt2",
    "https://api-inference.huggingface.co/models/gpt2",
    "https://huggingface.co/api/models/gpt2/v1/chat/completions",
]

for url in urls_to_try:
    print(f"\n{'='*60}")
    print(f"Trying: {url}")
    print(f"{'='*60}")
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    
    if response.status_code == 200:
        print("✓ THIS ONE WORKS!")
        break
    elif response.status_code == 410:
        print("↳ Endpoint deprecated/moved")
    elif response.status_code == 404:
        print("↳ Not found")
    else:
        print(f"↳ Error: {response.status_code}")
