"""
Test Suite for Judge Agent - Feature 7

Tests the Judge Agent implementation including:
- Agent initialization
- Evaluation methods
- Scoring calculation
- Issue detection
- Suggestion generation
- Batch evaluation
- Statistics tracking
"""

import sys
from typing import Dict, Any

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

from agents.judge import (
    JudgeAgent,
    create_judge
)


def test_judge_initialization():
    """Test judge agent can be initialized."""
    print("\n" + "="*60)
    print("TEST 1: Judge Initialization")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        # Create with reasoning
        judge_cot = create_judge(use_reasoning=True)
        print(f"✅ Created ChainOfThought judge")
        print(f"   Module type: {type(judge_cot.eval_module).__name__}")
        
        # Create without reasoning
        judge_predict = create_judge(use_reasoning=False)
        print(f"✅ Created Predict judge")
        print(f"   Module type: {type(judge_predict.eval_module).__name__}")
        
        # Check initialization
        assert judge_cot.use_reasoning == True
        assert judge_predict.use_reasoning == False
        assert judge_cot.evaluation_count == 0
        
        # Check weights loaded from config
        assert "correctness" in judge_cot.criteria_weights
        assert "clarity" in judge_cot.criteria_weights
        print(f"✅ Weights loaded: {judge_cot.criteria_weights}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custom_weights():
    """Test judge with custom criteria weights."""
    print("\n" + "="*60)
    print("TEST 2: Custom Weights")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        # Custom weights
        custom_weights = {
            "correctness": 0.5,
            "clarity": 0.2,
            "reasoning": 0.15,
            "relevance": 0.1,
            "conciseness": 0.05
        }
        
        judge = create_judge(criteria_weights=custom_weights)
        
        assert judge.criteria_weights == custom_weights
        print(f"✅ Custom weights applied: {judge.criteria_weights}")
        
        # Test invalid weights (don't sum to 1.0)
        try:
            invalid_weights = {
                "correctness": 0.5,
                "clarity": 0.3,
                "reasoning": 0.1,
                "relevance": 0.1,
                "conciseness": 0.1  # Sum = 1.1
            }
            judge_invalid = create_judge(criteria_weights=invalid_weights)
            print(f"❌ Should have rejected invalid weights")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected invalid weights: {str(e)[:50]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_evaluation_output_structure():
    """Test the structure of evaluation output (without LLM)."""
    print("\n" + "="*60)
    print("TEST 3: Evaluation Output Structure")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        judge = create_judge(use_reasoning=False)
        
        # This will fail without LLM, but error handler should work
        result = judge.evaluate(
            question="What is 2+2?",
            answer="4",
            explanation="Simple arithmetic"
        )
        
        # Check structure
        assert "scores" in result
        assert "composite_score" in result
        assert "feedback" in result
        assert "suggestions" in result
        assert "flags" in result
        assert "metadata" in result
        
        print(f"✅ Output has required fields:")
        print(f"   - scores: {list(result['scores'].keys())}")
        print(f"   - composite_score: {result['composite_score']}")
        print(f"   - feedback: {len(result['feedback'])} items")
        print(f"   - suggestions: {len(result['suggestions'])} items")
        print(f"   - flags: {result['flags']}")
        
        # Check scores structure
        scores = result["scores"]
        expected_criteria = ["correctness", "clarity", "reasoning", "relevance", "conciseness"]
        for criterion in expected_criteria:
            assert criterion in scores
        print(f"✅ All 5 criteria present in scores")
        
        # Check metadata
        metadata = result["metadata"]
        assert "latency_ms" in metadata
        assert "timestamp" in metadata
        print(f"✅ Metadata structure correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_composite_score_calculation():
    """Test weighted composite score calculation."""
    print("\n" + "="*60)
    print("TEST 4: Composite Score Calculation")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        judge = create_judge()
        
        # Test scores
        test_scores = {
            "correctness": 8.0,
            "clarity": 7.0,
            "reasoning": 6.0,
            "relevance": 9.0,
            "conciseness": 7.5
        }
        
        # Calculate manually
        expected = (
            8.0 * judge.criteria_weights["correctness"] +
            7.0 * judge.criteria_weights["clarity"] +
            6.0 * judge.criteria_weights["reasoning"] +
            9.0 * judge.criteria_weights["relevance"] +
            7.5 * judge.criteria_weights["conciseness"]
        )
        
        # Calculate with method
        composite = judge._calculate_composite_score(test_scores)
        
        print(f"✅ Composite score: {composite:.2f}")
        print(f"   Expected: {expected:.2f}")
        
        # Should match within rounding
        assert abs(composite - expected) < 0.01
        print(f"✅ Calculation correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_issue_detection():
    """Test issue detection logic."""
    print("\n" + "="*60)
    print("TEST 5: Issue Detection")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        judge = create_judge()
        
        # Test case 1: Low correctness -> hallucination
        scores1 = {"correctness": 2.0, "clarity": 7.0, "reasoning": 7.0, "relevance": 7.0, "conciseness": 7.0}
        feedback1 = {"correctness": "Incorrect facts", "clarity": "OK", "reasoning": "OK", "relevance": "OK", "conciseness": "OK"}
        flags1 = judge._detect_issues(scores1, feedback1, "Test answer", "Test explanation")
        assert "potential_hallucination" in flags1
        print(f"✅ Detected hallucination: {flags1}")
        
        # Test case 2: Low relevance -> off topic
        scores2 = {"correctness": 7.0, "clarity": 7.0, "reasoning": 7.0, "relevance": 3.0, "conciseness": 7.0}
        feedback2 = {"correctness": "OK", "clarity": "OK", "reasoning": "OK", "relevance": "Off topic", "conciseness": "OK"}
        flags2 = judge._detect_issues(scores2, feedback2, "Test answer", "Test explanation")
        assert "off_topic" in flags2
        print(f"✅ Detected off-topic: {flags2}")
        
        # Test case 3: Short answer + low correctness -> incomplete
        scores3 = {"correctness": 5.0, "clarity": 7.0, "reasoning": 7.0, "relevance": 7.0, "conciseness": 7.0}
        feedback3 = {"correctness": "Partial", "clarity": "OK", "reasoning": "OK", "relevance": "OK", "conciseness": "OK"}
        flags3 = judge._detect_issues(scores3, feedback3, "Too short", "Test explanation")
        assert "incomplete_answer" in flags3
        print(f"✅ Detected incomplete answer: {flags3}")
        
        # Test case 4: Long explanation + low conciseness -> verbose
        scores4 = {"correctness": 7.0, "clarity": 7.0, "reasoning": 7.0, "relevance": 7.0, "conciseness": 4.0}
        feedback4 = {"correctness": "OK", "clarity": "OK", "reasoning": "OK", "relevance": "OK", "conciseness": "Too verbose"}
        flags4 = judge._detect_issues(scores4, feedback4, "Test answer", "A" * 600)
        assert "verbose_explanation" in flags4
        print(f"✅ Detected verbose explanation: {flags4}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_suggestion_generation():
    """Test suggestion generation logic."""
    print("\n" + "="*60)
    print("TEST 6: Suggestion Generation")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        judge = create_judge()
        
        # Low correctness should suggest verification
        scores = {"correctness": 4.0, "clarity": 8.0, "reasoning": 8.0, "relevance": 8.0, "conciseness": 8.0}
        feedback = {"correctness": "Some errors", "clarity": "Good", "reasoning": "Good", "relevance": "Good", "conciseness": "Good"}
        suggestions = judge._generate_suggestions(scores, feedback)
        
        assert len(suggestions) > 0
        print(f"✅ Generated {len(suggestions)} suggestion(s):")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        # High scores should generate fewer suggestions
        high_scores = {"correctness": 9.0, "clarity": 9.0, "reasoning": 9.0, "relevance": 9.0, "conciseness": 9.0}
        high_feedback = {"correctness": "Excellent", "clarity": "Clear", "reasoning": "Sound", "relevance": "On point", "conciseness": "Concise"}
        high_suggestions = judge._generate_suggestions(high_scores, high_feedback)
        
        print(f"✅ High scores generate {len(high_suggestions)} suggestion(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_evaluation():
    """Test batch evaluation method."""
    print("\n" + "="*60)
    print("TEST 7: Batch Evaluation")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        judge = create_judge()
        
        # Test evaluations
        evaluations = [
            {
                "question": "What is gravity?",
                "answer": "Force of attraction",
                "explanation": "Pulls objects together"
            },
            {
                "question": "What is photosynthesis?",
                "answer": "Process plants use",
                "explanation": "Convert sunlight to energy",
                "ground_truth": "Process by which plants convert light into energy"
            }
        ]
        
        # Evaluate batch (will fail without LLM but structure should be correct)
        results = judge.evaluate_batch(evaluations)
        
        # Check results
        assert len(results) == 2
        
        for i, result in enumerate(results):
            assert "scores" in result
            assert "composite_score" in result
            assert "metadata" in result
            print(f"✅ Result {i+1}: Composite score = {result['composite_score']}")
        
        print(f"\n✅ Batch evaluation structure correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_statistics_tracking():
    """Test evaluation statistics tracking."""
    print("\n" + "="*60)
    print("TEST 8: Statistics Tracking")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        judge = create_judge()
        
        # Initial stats
        stats = judge.get_stats()
        assert stats["total_evaluations"] == 0
        print(f"✅ Initial stats: {stats['total_evaluations']} evaluations")
        
        # Evaluate some answers
        judge.evaluate("Test 1", "Answer 1", "Explanation 1")
        judge.evaluate("Test 2", "Answer 2", "Explanation 2")
        judge.evaluate("Test 3", "Answer 3", "Explanation 3")
        
        # Check stats updated
        stats = judge.get_stats()
        assert stats["total_evaluations"] == 3
        assert stats["use_reasoning"] == True
        print(f"✅ After 3 evaluations: {stats['total_evaluations']}")
        print(f"   Total time: {stats['total_time_seconds']:.3f}s")
        print(f"   Avg time: {stats['avg_time_seconds']:.3f}s")
        
        # Reset stats
        judge.reset_stats()
        stats = judge.get_stats()
        assert stats["total_evaluations"] == 0
        print(f"✅ After reset: {stats['total_evaluations']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling and recovery."""
    print("\n" + "="*60)
    print("TEST 9: Error Handling")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        judge = create_judge()
        
        # Test with empty inputs (will fail gracefully)
        result = judge.evaluate("", "", "")
        
        # Should still return valid structure
        assert "scores" in result
        assert "composite_score" in result
        assert "metadata" in result
        
        # All scores should be 0 for errors
        for criterion, score in result["scores"].items():
            assert score == 0.0
        
        print(f"✅ Error handling preserves structure")
        print(f"   Composite score for error: {result['composite_score']}")
        print(f"   Flags: {result['flags']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factory_function():
    """Test judge factory function."""
    print("\n" + "="*60)
    print("TEST 10: Factory Function")
    print("="*60)
    
    try:
        if not DSPY_AVAILABLE:
            print("⚠️  DSPy not available, skipping test")
            return True
        
        # Test with different configurations
        judge1 = create_judge(use_reasoning=True)
        assert judge1.use_reasoning == True
        print(f"✅ Config 1: reasoning={judge1.use_reasoning}")
        
        judge2 = create_judge(use_reasoning=False)
        assert judge2.use_reasoning == False
        print(f"✅ Config 2: reasoning={judge2.use_reasoning}")
        
        custom_weights = {
            "correctness": 0.6,
            "clarity": 0.1,
            "reasoning": 0.1,
            "relevance": 0.1,
            "conciseness": 0.1
        }
        judge3 = create_judge(criteria_weights=custom_weights)
        assert judge3.criteria_weights["correctness"] == 0.6
        print(f"✅ Config 3: custom weights applied")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all judge agent tests."""
    print("="*60)
    print("🧪 Judge Agent Tests - Feature 7")
    print("="*60)
    
    if not DSPY_AVAILABLE:
        print("\n⚠️  DSPy not installed")
        print("   Install with: pip install dspy-ai")
        return
    
    tests = [
        ("Judge Initialization", test_judge_initialization),
        ("Custom Weights", test_custom_weights),
        ("Evaluation Output Structure", test_evaluation_output_structure),
        ("Composite Score Calculation", test_composite_score_calculation),
        ("Issue Detection", test_issue_detection),
        ("Suggestion Generation", test_suggestion_generation),
        ("Batch Evaluation", test_batch_evaluation),
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
        print("\n📋 Judge Agent Ready:")
        print("  • Multi-criteria evaluation (5 dimensions)")
        print("  • Weighted composite scoring")
        print("  • Issue detection (hallucination, off-topic, etc.)")
        print("  • Actionable suggestions generation")
        print("  • Batch evaluation support")
        print("  • Statistics tracking")
        print("  • ChainOfThought and Predict modes")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
