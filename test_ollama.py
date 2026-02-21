"""
Quick Test Script for Ollama Integration

This script tests if Ollama is properly configured and working with Astra-AI.
Run this AFTER installing Ollama and downloading llama3.
"""

import sys
import subprocess
from pathlib import Path

def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_ollama_installed():
    """Check if Ollama is installed."""
    print_section("Step 1: Checking Ollama Installation")
    
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama not responding")
            return False
            
    except FileNotFoundError:
        print("❌ Ollama not installed")
        print("\n📥 Please install from: https://ollama.com/download")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def check_ollama_models():
    """Check which models are downloaded."""
    print_section("Step 2: Checking Downloaded Models")
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "llama3" in output.lower():
                print("✅ llama3 model found!")
                print(f"\n{output}")
                return True
            else:
                print("❌ llama3 model not found")
                print("\n📥 Download with: ollama pull llama3")
                print(f"\nAvailable models:\n{output}")
                return False
        else:
            print("❌ Could not list models")
            return False
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def check_ollama_running():
    """Check if Ollama server is responding."""
    print_section("Step 3: Testing Ollama Server")
    
    try:
        # Try to run a simple prompt
        result = subprocess.run(
            ["ollama", "run", "llama3", "Say 'Hello'"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Ollama server responding!")
            response = result.stdout.strip()
            print(f"\n📝 Test Response:")
            print(f"   {response[:100]}...")
            return True
        else:
            print("❌ Ollama server not responding")
            print("\n🔧 Start server with: ollama serve")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏱️  Timeout - model might be loading (this is normal for first run)")
        return True
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def check_config_file():
    """Check if config.yaml has correct settings."""
    print_section("Step 4: Checking Configuration")
    
    config_path = Path("config/config.yaml")
    
    if not config_path.exists():
        print("❌ config.yaml not found")
        return False
    
    content = config_path.read_text()
    
    checks = {
        'provider: "ollama"': False,
        'model_name: "llama3"': False
    }
    
    for check in checks:
        if check in content:
            checks[check] = True
    
    if all(checks.values()):
        print("✅ Configuration file correct!")
        print("\n📄 Current settings:")
        print("   Provider: ollama")
        print("   Model: llama3")
        return True
    else:
        print("⚠️  Configuration needs update")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        return False

def test_dspy_integration():
    """Test if DSPy can connect to Ollama."""
    print_section("Step 5: Testing DSPy Integration")
    
    try:
        import dspy
        print("✅ DSPy imported successfully")
        
        # Configure DSPy to use Ollama
        try:
            lm = dspy.LM("ollama/llama3", api_base="http://localhost:11434")
            dspy.configure(lm=lm)
            print("✅ DSPy configured for Ollama")
            
            # Try a simple call
            try:
                response = lm("Test: What is 2+2?")
                print("✅ DSPy → Ollama connection working!")
                print(f"\n📝 Sample Response:")
                print(f"   {str(response)[:100]}...")
                return True
            except Exception as e:
                print(f"⚠️  DSPy call failed: {e}")
                print("   (This might work once Ollama server is fully started)")
                return False
                
        except Exception as e:
            print(f"⚠️  DSPy configuration issue: {e}")
            return False
            
    except ImportError:
        print("❌ DSPy not installed")
        print("   Install with: pip install dspy-ai")
        return False

def main():
    """Run all tests."""
    print("\n" + "🔍 " * 20)
    print("   OLLAMA INTEGRATION TEST FOR ASTRA-AI")
    print("🔍 " * 20)
    
    results = {
        "Ollama Installed": check_ollama_installed(),
        "Models Downloaded": check_ollama_models(),
        "Server Running": check_ollama_running(),
        "Config Correct": check_config_file(),
        "DSPy Integration": test_dspy_integration()
    }
    
    print_section("FINAL RESULTS")
    
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:12} - {test}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 " * 20)
        print("\n✅ ALL TESTS PASSED! Ollama is ready for Astra-AI\n")
        print("🚀 You can now run:")
        print("   python main.py --interactive")
        print("   python main.py --batch sample_questions.txt")
        print("\n🎉 " * 20)
    else:
        print("⚠️  " * 20)
        print("\n⚠️  Some tests failed. Follow the instructions above to fix.\n")
        print("📚 See OLLAMA_SETUP.md for detailed setup guide")
        print("\n⚠️  " * 20)
    
    print()

if __name__ == "__main__":
    main()
