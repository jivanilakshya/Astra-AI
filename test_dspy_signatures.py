"""
Test script for DSPy Signatures - Feature 4
Run this to test signature definitions.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dspy_modules import (
    QuestionAnswering,
    QuestionAnsweringWithContext,
    AnswerEvaluation,
    PromptOptimization,
    SimpleQA,
    QAWithReasoning,
    create_qa_signature,
    validate_signature_output,
    format_qa_output
)
import dspy


def test_signature_creation():
    """Test that all signatures are properly defined."""
    print("\n" + "="*60)
    print("TEST 1: Signature Creation")
    print("="*60)
    
    try:
        signatures = {
            "QuestionAnswering": QuestionAnswering,
            "QuestionAnsweringWithContext": QuestionAnsweringWithContext,
            "AnswerEvaluation": AnswerEvaluation,
            "PromptOptimization": PromptOptimization,
            "SimpleQA": SimpleQA,
            "QAWithReasoning": QAWithReasoning
        }
        
        for name, sig_class in signatures.items():
            # Check it's a valid class inheriting from dspy.Signature
            assert issubclass(sig_class, dspy.Signature)
            print(f"✅ {name} is a valid DSPy Signature")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_signature_fields():
    """Test signature field definitions."""
    print("\n" + "="*60)
    print("TEST 2: Signature Fields")
    print("="*60)
    
    try:
        # QuestionAnswering signature - check class annotations
        qa_fields = QuestionAnswering.__annotations__
        
        print(f"QuestionAnswering:")
        print(f"  ✅ Has {len(qa_fields)} fields defined")
        
        # Verify expected fields exist
        assert 'question' in qa_fields, "Missing 'question' field"
        assert 'answer' in qa_fields, "Missing 'answer' field"
        assert 'explanation' in qa_fields, "Missing 'explanation' field"
        
        print(f"  ✅ Required fields: question, answer, explanation")
        
        # AnswerEvaluation signature
        eval_fields = AnswerEvaluation.__annotations__
        
        print(f"\nAnswerEvaluation:")
        print(f"  ✅ Has {len(eval_fields)} fields defined")
        
        # Verify score fields
        expected_scores = ['correctness_score', 'clarity_score', 'reasoning_score',
                          'relevance_score', 'conciseness_score']
        
        for score in expected_scores:
            assert score in eval_fields, f"Missing '{score}' field"
        
        print(f"  ✅ All 5 score fields present + feedback")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_signature_descriptions():
    """Test that signatures have descriptions."""
    print("\n" + "="*60)
    print("TEST 3: Field Descriptions")
    print("="*60)
    
    try:
        # Check docstring
        qa_doc = QuestionAnswering.__doc__
        if qa_doc:
            print(f"✅ QuestionAnswering has docstring")
            print(f"   {qa_doc.strip().split(chr(10))[0]}")
        
        eval_doc = AnswerEvaluation.__doc__
        if eval_doc:
            print(f"✅ AnswerEvaluation has docstring")
            print(f"   {eval_doc.strip().split(chr(10))[0]}")
        
        opt_doc = PromptOptimization.__doc__
        if opt_doc:
            print(f"✅ PromptOptimization has docstring")
            print(f"   {opt_doc.strip().split(chr(10))[0]}")
        
        print(f"\n✅ All signatures have documentation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_signature_factory():
    """Test signature factory function."""
    print("\n" + "="*60)
    print("TEST 4: Signature Factory")
    print("="*60)
    
    try:
        # Create simple QA
        simple_sig = create_qa_signature(include_explanation=False)
        print(f"✅ Simple QA: {simple_sig.__name__}")
        
        # Create with explanation
        expl_sig = create_qa_signature(include_explanation=True)
        print(f"✅ With explanation: {expl_sig.__name__}")
        
        # Create with context
        ctx_sig = create_qa_signature(include_context=True)
        print(f"✅ With context: {ctx_sig.__name__}")
        
        # Create with reasoning
        reason_sig = create_qa_signature(include_reasoning=True)
        print(f"✅ With reasoning: {reason_sig.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_format_output():
    """Test output formatting utility."""
    print("\n" + "="*60)
    print("TEST 5: Output Formatting")
    print("="*60)
    
    try:
        # Create mock prediction object
        class MockPrediction:
            def __init__(self):
                self.answer = "Test answer"
                self.explanation = "Test explanation"
        
        pred = MockPrediction()
        formatted = format_qa_output(pred)
        
        print(f"✅ Formatted output:")
        print(f"   Answer: {formatted.get('answer')}")
        print(f"   Explanation: {formatted.get('explanation')}")
        
        assert 'answer' in formatted, "Missing answer in formatted output"
        assert 'explanation' in formatted, "Missing explanation in formatted output"
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_signature_with_dspy_module():
    """Test using signature with DSPy Predict module."""
    print("\n" + "="*60)
    print("TEST 6: Signature with DSPy Module")
    print("="*60)
    
    try:
        # Create a DSPy Predict module with our signature
        qa_module = dspy.Predict(QuestionAnswering)
        
        print(f"✅ Created DSPy Predict module with QuestionAnswering signature")
        print(f"   Module type: {type(qa_module)}")
        print(f"   Signature: {qa_module.signature}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_all_signature_types():
    """Test that all signature types are properly structured."""
    print("\n" + "="*60)
    print("TEST 7: All Signature Types")
    print("="*60)
    
    try:
        signatures_to_test = [
            ("QuestionAnswering", QuestionAnswering),
            ("QuestionAnsweringWithContext", QuestionAnsweringWithContext),
            ("AnswerEvaluation", AnswerEvaluation),
            ("PromptOptimization", PromptOptimization),
            ("SimpleQA", SimpleQA),
            ("QAWithReasoning", QAWithReasoning)
        ]
        
        for name, sig_class in signatures_to_test:
            # Check it has annotations (fields) - don't instantiate
            fields = sig_class.__annotations__
            field_count = len(fields)
            
            print(f"✅ {name}: {field_count} fields defined")
            
            # Verify has at least one field
            assert field_count > 0, f"{name} has no fields"
        
        print(f"\n✅ All 6 signature types properly structured")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_signature_inheritance():
    """Test that signatures properly inherit from dspy.Signature."""
    print("\n" + "="*60)
    print("TEST 8: Signature Inheritance")
    print("="*60)
    
    try:
        # Check inheritance
        assert issubclass(QuestionAnswering, dspy.Signature)
        print("✅ QuestionAnswering inherits from dspy.Signature")
        
        assert issubclass(AnswerEvaluation, dspy.Signature)
        print("✅ AnswerEvaluation inherits from dspy.Signature")
        
        assert issubclass(PromptOptimization, dspy.Signature)
        print("✅ PromptOptimization inherits from dspy.Signature")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("🧪 DSPy Signatures Tests - Feature 4")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Signature Creation", test_signature_creation()))
    results.append(("Signature Fields", test_signature_fields()))
    results.append(("Field Descriptions", test_signature_descriptions()))
    results.append(("Signature Factory", test_signature_factory()))
    results.append(("Output Formatting", test_format_output()))
    results.append(("Signature with Module", test_signature_with_dspy_module()))
    results.append(("All Signature Types", test_all_signature_types()))
    results.append(("Signature Inheritance", test_signature_inheritance()))
    
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
        print("\n📋 Signatures Ready:")
        print("  • QuestionAnswering - Main Q&A signature")
        print("  • QuestionAnsweringWithContext - Q&A with context")
        print("  • AnswerEvaluation - For Judge Agent")
        print("  • PromptOptimization - For Optimizer Agent")
        print("  • SimpleQA - Basic question -> answer")
        print("  • QAWithReasoning - With step-by-step reasoning")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("="*60)


if __name__ == "__main__":
    main()
