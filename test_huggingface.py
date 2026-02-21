"""
Test Hugging Face Integration - Zero PC Load Solution
Run this to verify your setup before using Astra AI
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, that's okay - env vars might be set system-wide
    pass

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text):
    """Print colored header"""
    print(f"\n{CYAN}{BOLD}{'='*60}{RESET}")
    print(f"{CYAN}{BOLD}{text:^60}{RESET}")
    print(f"{CYAN}{BOLD}{'='*60}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{CYAN}ℹ️  {text}{RESET}")


def test_1_api_key():
    """Test 1: Check if API key is configured"""
    print(f"\n{BOLD}Test 1: Checking Hugging Face API Key{RESET}")
    print("-" * 60)
    
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if not api_key:
        print_error("HUGGINGFACE_API_KEY not found in environment")
        print_info("Get your free API key from: https://huggingface.co/settings/tokens")
        print_info("Then add to .env file:")
        print(f"  {CYAN}HUGGINGFACE_API_KEY=hf_your_token_here{RESET}")
        return False
    
    if not api_key.startswith("hf_"):
        print_warning(f"API key doesn't start with 'hf_' (found: {api_key[:5]}...)")
        print_info("Make sure you copied the full token from Hugging Face")
        return False
    
    print_success(f"API key found: {api_key[:10]}...{api_key[-5:]}")
    return True


def test_2_package_installed():
    """Test 2: Check if huggingface_hub is installed"""
    print(f"\n{BOLD}Test 2: Checking Required Packages{RESET}")
    print("-" * 60)
    
    try:
        import huggingface_hub
        version = huggingface_hub.__version__
        print_success(f"huggingface_hub installed (version {version})")
        return True
    except ImportError:
        print_error("huggingface_hub not installed")
        print_info("Install with: pip install huggingface-hub")
        return False


def test_3_provider_import():
    """Test 3: Check if HuggingFace provider can be imported"""
    print(f"\n{BOLD}Test 3: Checking Hugging Face Provider{RESET}")
    print("-" * 60)
    
    try:
        # Add agents directory to path
        agents_dir = Path(__file__).parent / "agents"
        sys.path.insert(0, str(agents_dir))
        
        from huggingface_provider import HuggingFaceProvider
        print_success("HuggingFaceProvider imported successfully")
        return True
    except ImportError as e:
        print_error(f"Failed to import HuggingFaceProvider: {e}")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_4_api_connection():
    """Test 4: Test actual API connection"""
    print(f"\n{BOLD}Test 4: Testing API Connection{RESET}")
    print("-" * 60)
    
    try:
        from agents.huggingface_provider import HuggingFaceProvider
        
        print_info("Initializing provider...")
        provider = HuggingFaceProvider()
        
        print_info("Testing with gpt2 (always available on free tier)...")
        print_info("Sending request: 'What is 2+2?'")
        
        result = provider.generate(
            model_name="gpt2",
            prompt="Q: What is 2+2? A:",
            max_tokens=10,
            temperature=0.1
        )
        
        if result["success"]:
            print_success("API call successful!")
            print(f"  {CYAN}Response: {result['text']}{RESET}")
            print(f"  {CYAN}Latency: {result['latency_seconds']:.2f}s{RESET}")
            print(f"  {CYAN}Model: {result['model']}{RESET}")
            return True
        else:
            print_error(f"API call failed: {result.get('error')}")
            
            if "rate limit" in result.get('error', '').lower():
                print_warning("You hit the rate limit. This is normal for free tier.")
                print_info("Wait a few minutes or try a different model")
            
            return False
            
    except Exception as e:
        print_error(f"Connection test failed: {e}")
        return False


def test_5_multiple_models():
    """Test 5: Test multiple models for cost comparison"""
    print(f"\n{BOLD}Test 5: Testing Multiple Models{RESET}")
    print("-" * 60)
    
    try:
        from agents.huggingface_provider import HuggingFaceProvider
        
        provider = HuggingFaceProvider()
        
        # Test 3 different models (using free tier compatible ones)
        models = [
            {
                "name": "gpt2",
                "description": "GPT-2 - Always available",
                "prompt": "The capital of France is"
            },
            {
                "name": "bigscience/bloomz-560m",
                "description": "BLOOM - Multilingual",
                "prompt": "Q: What is AI? A:"
            }
        ]
        
        results = []
        
        for model_info in models:
            print(f"\n{CYAN}Testing: {model_info['name']} ({model_info['description']}){RESET}")
            
            try:
                result = provider.generate(
                    model_name=model_info["name"],
                    prompt=model_info["prompt"],
                    max_tokens=50,
                    temperature=0.7
                )
                
                if result["success"]:
                    print_success(f"Response: {result['text'][:100]}")
                    print(f"  Latency: {result['latency_seconds']:.2f}s")
                    results.append(result)
                else:
                    print_warning(f"Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print_warning(f"Error with {model_info['name']}: {e}")
        
        if len(results) >= 1:
            print_success(f"\nSuccessfully tested {len(results)}/{len(models)} models!")
            return True
        else:
            print_warning("Some models failed, but at least one worked")
            return len(results) > 0
            
    except Exception as e:
        print_error(f"Multiple model test failed: {e}")
        return False


def test_6_config_file():
    """Test 6: Check if config.yaml is set up for Hugging Face"""
    print(f"\n{BOLD}Test 6: Checking Configuration File{RESET}")
    print("-" * 60)
    
    try:
        import yaml
        
        config_path = Path(__file__).parent / "config" / "config.yaml"
        
        if not config_path.exists():
            print_warning("config.yaml not found")
            print_info("Creating config with Hugging Face settings...")
            return False
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check if provider is set to huggingface (config has 'models' top level)
        models = config.get('models', {})
        generator_provider = models.get('generator', {}).get('provider', '')
        
        if generator_provider == 'huggingface':
            print_success("Config is set to use Hugging Face ✅")
            
            # Show current models
            gen_model = models.get('generator', {}).get('model_name', 'N/A')
            judge_model = models.get('judge', {}).get('model_name', 'N/A')
            opt_model = models.get('optimizer', {}).get('model_name', 'N/A')
            
            print(f"\n  {CYAN}Generator: {gen_model}{RESET}")
            print(f"  {CYAN}Judge: {judge_model}{RESET}")
            print(f"  {CYAN}Optimizer: {opt_model}{RESET}")
            
            return True
        else:
            print_warning(f"Provider is set to '{generator_provider}', not 'huggingface'")
            print_info("Update config/config.yaml to use Hugging Face models")
            return False
            
    except Exception as e:
        print_warning(f"Could not check config: {e}")
        return False


def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n{BOLD}Results: {passed}/{total} tests passed{RESET}\n")
    
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status}  {test_name}")
    
    print()
    
    if passed == total:
        print_success("🎉 All tests passed! You're ready to use Astra AI with Hugging Face!")
        print()
        print(f"{BOLD}Next steps:{RESET}")
        print(f"  1. Run: {CYAN}python main.py --interactive{RESET}")
        print(f"  2. Enter test questions")
        print(f"  3. View cost optimization with multiple models!")
        print()
    elif passed >= 4:
        print_warning("⚠️  Most tests passed, but some issues detected")
        print_info("You can probably still run the system, but check the errors above")
        print()
    else:
        print_error("❌ Setup incomplete. Please fix the errors above")
        print()
        print(f"{BOLD}Common solutions:{RESET}")
        print(f"  1. Get API key: {CYAN}https://huggingface.co/settings/tokens{RESET}")
        print(f"  2. Install package: {CYAN}pip install huggingface-hub{RESET}")
        print(f"  3. Add to .env: {CYAN}HUGGINGFACE_API_KEY=hf_...{RESET}")
        print()


def main():
    """Run all tests"""
    print_header("ASTRA AI - Hugging Face Setup Verification")
    
    print(f"{BOLD}Testing Hugging Face integration...{RESET}")
    print(f"{CYAN}This uses HuggingFace API - ZERO load on your PC!{RESET}")
    
    # Run all tests
    results = {}
    
    results["API Key"] = test_1_api_key()
    results["Package Installed"] = test_2_package_installed()
    results["Provider Import"] = test_3_provider_import()
    
    # Only run connection tests if basics work
    if results["API Key"] and results["Package Installed"]:
        results["API Connection"] = test_4_api_connection()
        results["Multiple Models"] = test_5_multiple_models()
    else:
        print_warning("\nSkipping API tests due to setup issues")
        results["API Connection"] = False
        results["Multiple Models"] = False
    
    results["Config File"] = test_6_config_file()
    
    # Print summary
    print_summary(results)
    
    # Return exit code
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
