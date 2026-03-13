"""
HuggingFace Provider - WORKING VERSION
Uses the official huggingface_hub InferenceClient properly
"""

import os
import time
from typing import Optional, Dict, Any
from huggingface_hub import InferenceClient

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


class HuggingFaceProvider:
    """Working HuggingFace provider using official client"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key"""
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY required")
        
        # Use official InferenceClient
        self.client = InferenceClient(token=self.api_key)
    
    def generate(
        self,
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using HuggingFace"""
        start_time = time.time()
        
        try:
            # Use chat_completion for modern models
            messages = [{"role": "user", "content": prompt}]
            
            response = self.client.chat_completion(
                messages=messages,
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            latency = time.time() - start_time
            
            # Extract text from response
            generated_text = response.choices[0].message.content
            
            return {
                "text": generated_text.strip(),
                "model": model_name,
                "provider": "huggingface",
                "latency_seconds": latency,
                "success": True
            }
            
        except Exception as e:
            # If chat_completion fails, try text_generation
            try:
                response_text = self.client.text_generation(
                    prompt,
                    model=model_name,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                )
                
                latency = time.time() - start_time
                
                return {
                    "text": response_text.strip(),
                    "model": model_name,
                    "provider": "huggingface",
                    "latency_seconds": latency,
                    "success": True
                }
            except Exception as e2:
                latency = time.time() - start_time
                print(f"DEBUG - Error 1: {str(e)}")
                print(f"DEBUG - Error 2: {str(e2)}")
                import traceback
                traceback.print_exc()
                return {
                    "text": "",
                    "model": model_name,
                    "provider": "huggingface",
                    "latency_seconds": latency,
                    "success": False,
                    "error": f"{str(e)} | {str(e2)}"
                }


if __name__ == "__main__":
    # Test
    provider = HuggingFaceProvider()
    
    # Chat models that work with Inference API
    models_to_test = [
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "HuggingFaceH4/zephyr-7b-beta",
        "google/gemma-7b-it",
    ]
    
    for model in models_to_test:
        print(f"\nTesting: {model}")
        result = provider.generate(
            model_name=model,
            prompt="What is 2+2? Answer:",
            max_tokens=50,
            temperature=0.3
        )
        
        if result["success"]:
            print(f"✓ SUCCESS!")
            print(f"Response: {result['text']}")
            print(f"Latency: {result['latency_seconds']:.2f}s")
            print("\n🎉 HUGGINGFACE IS WORKING!")
            break
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown')[:100]}")
