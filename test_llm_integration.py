"""
Test script for LLM integration - Feature 2
Run this to test all LLM components.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models import (
    OllamaClient,
    create_llm_client,
    get_registry,
    configure_dspy,
    test_dspy_setup
)
from config import get_config


def test_ollama_client():
    """Test Ollama client directly."""
    print("\n" + "="*60)
    print("TEST 1: Ollama Client")
    print("="*60)
    
    try:
        client = OllamaClient("llama3.1")
        
        # Check availability
        print(f"Checking availability...")
        if client.is_available():
            print(f"✅ Model available")
            
            # List models
            models = client.list_models()
            print(f"✅ Installed models: {', '.join(models[:3])}")
            
            # Test generation
            print(f"\nTesting generation...")
            response = client.generate(
                "What is 2+2? Answer in one word.",
                max_tokens=10
            )
            print(f"✅ Generated: {response}")
            return True
        else:
            print("❌ Model not available")
            print("   Run: ollama pull llama3.1")
            return False
            
    except ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        print("   Run: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_model_registry():
    """Test model registry."""
    print("\n" + "="*60)
    print("TEST 2: Model Registry")
    print("="*60)
    
    try:
        registry = get_registry()
        
        # List models
        models = registry.list_models()
        print(f"✅ Registry has {len(models)} models")
        
        # Get specific model
        llama = registry.get("llama3.1")
        if llama:
            print(f"✅ Retrieved: {llama.provider}/{llama.model_name}")
        
        # Get by use case
        eval_models = registry.get_by_use_case("evaluation")
        print(f"✅ Evaluation models: {len(eval_models)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_client_factory():
    """Test client factory."""
    print("\n" + "="*60)
    print("TEST 3: Client Factory")
    print("="*60)
    
    try:
        # Create Ollama client
        client = create_llm_client("ollama", "llama3.1")
        print(f"✅ Created: {client}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_dspy_integration():
    """Test DSPy integration."""
    print("\n" + "="*60)
    print("TEST 4: DSPy Integration")
    print("="*60)
    
    try:
        # Configure DSPy
        print("Configuring DSPy...")
        lm = configure_dspy(
            provider="ollama",
            model_name="llama3.1",
            temperature=0.7,
            max_tokens=100,
            cache_dir="./cache/dspy"
        )
        print(f"✅ DSPy configured with {lm.model_name}")
        
        # Test DSPy
        print("\nTesting DSPy...")
        success = test_dspy_setup(lm)
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_with_config():
    """Test using configuration file."""
    print("\n" + "="*60)
    print("TEST 5: Configuration Integration")
    print("="*60)
    
    try:
        config = get_config()
        
        # Create client from config
        gen_config = config.generator_model
        client = create_llm_client(
            provider=gen_config['provider'],
            model_name=gen_config['model_name']
        )
        
        print(f"✅ Created client from config: {client}")
        
        if client.is_available():
            print(f"✅ Client is ready")
            return True
        else:
            print(f"⚠️  Client created but model not available")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("🧪 LLM Integration Tests - Feature 2")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Ollama Client", test_ollama_client()))
    results.append(("Model Registry", test_model_registry()))
    results.append(("Client Factory", test_client_factory()))
    results.append(("DSPy Integration", test_dspy_integration()))
    results.append(("Config Integration", test_with_config()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nTroubleshooting:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Install required model: ollama pull llama3.1")
        print("3. Check .env configuration")
    
    print("="*60)


if __name__ == "__main__":
    main()
