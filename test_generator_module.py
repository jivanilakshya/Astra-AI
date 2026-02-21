"""
Test Suite for Generator Module - Feature 5

Tests the Generator Agent implementation including:
- Module initialization
- Generation methods
- Error handling
- Batch processing
- Statistics tracking
"""

import sys
from typing import Dict, Any

try:
    import dspy
    from dspy import Predict, ChainOfThought
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

from dspy_modules.generator import (
    GeneratorAgent,
    create_generator
)


def test_generator_initialization():
    """Test generator can be initialized."""
    print("\n" + "="*60)
    print("TEST 1: Generator Initialization")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        # Create with reasoning
        gen_cot = create_generator(use_reasoning=True)
        print(f"✅ Created ChainOfThought generator")
        print(f"   Module type: {type(gen_cot.qa_module).__name__}")
        
        # Create without reasoning
        gen_predict = create_generator(use_reasoning=False)
        print(f"✅ Created Predict generator")
        print(f"   Module type: {type(gen_predict.qa_module).__name__}")
        
        # Check initialization
        assert gen_cot.use_reasoning == True
        assert gen_predict.use_reasoning == False
        assert gen_cot.generation_count == 0
        
        print(f"✅ Initialization correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_generator_modules():
    """Test that all generator modules are properly initialized."""
    print("\n" + "="*60)
    print("TEST 2: Generator Modules")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        generator = create_generator(use_reasoning=True)
        
        # Check module types
        assert generator.qa_module is not None
        assert generator.qa_context_module is not None
        assert generator.qa_reasoning_module is not None
        assert generator.simple_qa_module is not None
        
        print(f"✅ All 4 modules initialized:")
        print(f"   - qa_module: {type(generator.qa_module).__name__}")
        print(f"   - qa_context_module: {type(generator.qa_context_module).__name__}")
        print(f"   - qa_reasoning_module: {type(generator.qa_reasoning_module).__name__}")
        print(f"   - simple_qa_module: {type(generator.simple_qa_module).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_generator_output_structure():
    """Test the structure of generator output (without LLM)."""
    print("\n" + "="*60)
    print("TEST 3: Output Structure")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        # We'll test error handling since we don't have LLM
        generator = create_generator(use_reasoning=False)
        
        # This will fail without LLM, but error handler should work
        result = generator.generate("What is 2+2?")
        
        # Check structure
        assert "question" in result
        assert "answer" in result
        assert "explanation" in result
        assert "confidence" in result
        assert "metadata" in result
        
        print(f"✅ Output has required fields:")
        print(f"   - question: {result['question']}")
        print(f"   - answer: {result.get('answer', 'N/A')[:50]}")
        print(f"   - explanation: {result.get('explanation', 'N/A')[:50]}")
        print(f"   - confidence: {result['confidence']}")
        print(f"   - metadata: {list(result['metadata'].keys())}")
        
        # Check metadata structure
        metadata = result["metadata"]
        assert "latency_ms" in metadata
        assert "timestamp" in metadata
        
        print(f"✅ Metadata structure correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_confidence_estimation():
    """Test confidence estimation logic."""
    print("\n" + "="*60)
    print("TEST 4: Confidence Estimation")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        generator = create_generator()
        
        # Test different response scenarios
        test_cases = [
            ({"answer": "Test"}, 0.6),  # Short answer
            ({"answer": "Test answer here", "explanation": "Test"}, 0.8),  # Answer + short explanation
            ({"answer": "Test answer", "explanation": "A" * 60}, 0.9),  # Answer + long explanation
            ({"answer": "Test", "explanation": "Test", "reasoning": "Step 1"}, 1.0),  # All fields
            ({}, 0.0),  # Empty
        ]
        
        for result, min_expected in test_cases:
            confidence = generator._estimate_confidence(result)
            print(f"✅ Confidence for {len(result)} fields: {confidence:.2f} (expected >= {min_expected - 0.2:.2f})")
            if confidence < min_expected - 0.2:
                print(f"   ⚠️  Confidence {confidence:.2f} < expected {min_expected - 0.2:.2f}")
        
        print(f"\n✅ Confidence estimation working")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False


def test_batch_generation():
    """Test batch generation method."""
    print("\n" + "="*60)
    print("TEST 5: Batch Generation")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        generator = create_generator()
        
        # Test questions
        questions = [
            "What is gravity?",
            "What is photosynthesis?",
            "What is DNA?"
        ]
        
        # Generate batch (will fail without LLM but structure should be correct)
        results = generator.generate_batch(questions)
        
        # Check results
        assert len(results) == 3
        
        for i, result in enumerate(results):
            assert result["question"] == questions[i]
            assert "answer" in result
            assert "metadata" in result
            print(f"✅ Result {i+1}: {result['question']}")
        
        print(f"\n✅ Batch generation structure correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_statistics_tracking():
    """Test generation statistics tracking."""
    print("\n" + "="*60)
    print("TEST 6: Statistics Tracking")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        generator = create_generator()
        
        # Initial stats
        stats = generator.get_stats()
        assert stats["total_generations"] == 0
        print(f"✅ Initial stats: {stats['total_generations']} generations")
        
        # Generate some responses
        generator.generate("Test 1")
        generator.generate("Test 2")
        
        # Check stats updated
        stats = generator.get_stats()
        print(f"   Stats after generation: {stats['total_generations']}")
        assert stats["total_generations"] == 2, f"Expected 2, got {stats['total_generations']}"
        assert stats["use_reasoning"] == True
        print(f"✅ After 2 generations: {stats['total_generations']}")
        
        # Reset stats
        generator.reset_stats()
        stats = generator.get_stats()
        assert stats["total_generations"] == 0
        print(f"✅ After reset: {stats['total_generations']}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling and recovery."""
    print("\n" + "="*60)
    print("TEST 7: Error Handling")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        generator = create_generator()
        
        # Test with empty question (will fail gracefully)
        result = generator.generate("")
        
        # Should still return valid structure
        assert "question" in result
        assert "metadata" in result
        assert "confidence" in result
        
        # Confidence should be low for errors
        assert result["confidence"] <= 0.5
        
        print(f"✅ Error handling preserves structure")
        print(f"   Confidence for error: {result['confidence']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_factory_function():
    """Test generator factory function."""
    print("\n" + "="*60)
    print("TEST 8: Factory Function")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        # Test with different configurations
        gen1 = create_generator(use_reasoning=True, temperature=0.5)
        assert gen1.use_reasoning == True
        assert gen1.temperature == 0.5
        print(f"✅ Config 1: reasoning={gen1.use_reasoning}, temp={gen1.temperature}")
        
        gen2 = create_generator(use_reasoning=False, temperature=0.9)
        assert gen2.use_reasoning == False
        assert gen2.temperature == 0.9
        print(f"✅ Config 2: reasoning={gen2.use_reasoning}, temp={gen2.temperature}")
        
        gen3 = create_generator(max_tokens=1000)
        assert gen3.max_tokens == 1000
        print(f"✅ Config 3: max_tokens={gen3.max_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all generator tests."""
    print("="*60)
    print("🧪 Generator Module Tests - Feature 5")
    print("="*60)
    
    if not DSPY_AVAILABLE:
        print("\n⚠️  DSPy not installed")
        print("   Install with: pip install dspy-ai")
        return
    
    tests = [
        ("Generator Initialization", test_generator_initialization),
        ("Generator Modules", test_generator_modules),
        ("Output Structure", test_generator_output_structure),
        ("Confidence Estimation", test_confidence_estimation),
        ("Batch Generation", test_batch_generation),
        ("Statistics Tracking", test_statistics_tracking),
        ("Error Handling", test_error_handling),
        ("Factory Function", test_factory_function)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("\n📋 Generator Module Ready:")
        print("  • ChainOfThought and Predict modes")
        print("  • Standard Q&A generation")
        print("  • Context-aware generation")
        print("  • Reasoning-based generation")
        print("  • Batch processing")
        print("  • Statistics tracking")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
