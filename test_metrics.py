"""
Test Suite for Metrics Calculator - Feature 8

Tests the metrics calculation and tracking functionality:
- Metrics calculation
- Iteration tracking
- Comparison logic
- Convergence detection
- Trend analysis
- Summary generation
"""

import sys
from typing import Dict, Any, List

from utils.metrics import (
    MetricsCalculator,
    create_metrics_calculator
)


def create_sample_evaluation(
    correctness: float = 7.0,
    clarity: float = 7.0,
    reasoning: float = 7.0,
    relevance: float = 7.0,
    conciseness: float = 7.0,
    flags: List[str] = None,
    suggestions: List[str] = None
) -> Dict[str, Any]:
    """Helper to create sample evaluation results."""
    composite = (
        correctness * 0.4 +
        clarity * 0.2 +
        reasoning * 0.2 +
        relevance * 0.1 +
        conciseness * 0.1
    )
    
    return {
        "scores": {
            "correctness": correctness,
            "clarity": clarity,
            "reasoning": reasoning,
            "relevance": relevance,
            "conciseness": conciseness
        },
        "composite_score": composite,
        "flags": flags or [],
        "suggestions": suggestions or []
    }


def test_calculator_initialization():
    """Test metrics calculator initialization."""
    print("\n" + "="*60)
    print("TEST 1: Calculator Initialization")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        assert calc.current_iteration == 0
        assert len(calc.iteration_history) == 0
        
        print(f"✅ Calculator initialized")
        print(f"   Current iteration: {calc.current_iteration}")
        print(f"   History length: {len(calc.iteration_history)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_calculation():
    """Test basic metrics calculation."""
    print("\n" + "="*60)
    print("TEST 2: Metrics Calculation")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        # Create sample evaluations
        evaluations = [
            create_sample_evaluation(8.0, 7.0, 7.5, 8.0, 7.5),
            create_sample_evaluation(7.0, 6.0, 6.5, 7.0, 6.5),
            create_sample_evaluation(9.0, 8.0, 8.5, 9.0, 8.5)
        ]
        
        metrics = calc.calculate_metrics(evaluations)
        
        # Check structure
        assert "scores_stats" in metrics
        assert "composite_stats" in metrics
        assert "flags_summary" in metrics
        
        print(f"✅ Metrics calculated:")
        print(f"   Criteria tracked: {list(metrics['scores_stats'].keys())}")
        print(f"   Composite mean: {metrics['composite_stats']['mean']:.2f}")
        print(f"   Composite std: {metrics['composite_stats']['std']:.2f}")
        
        # Check statistics calculation
        correctness_stats = metrics["scores_stats"]["correctness"]
        assert correctness_stats["mean"] == 8.0
        assert correctness_stats["min"] == 7.0
        assert correctness_stats["max"] == 9.0
        
        print(f"✅ Statistics correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_iteration_tracking():
    """Test iteration tracking functionality."""
    print("\n" + "="*60)
    print("TEST 3: Iteration Tracking")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        # Add iterations
        evals1 = [create_sample_evaluation(7.0, 7.0, 7.0, 7.0, 7.0)]
        evals2 = [create_sample_evaluation(8.0, 8.0, 8.0, 8.0, 8.0)]
        evals3 = [create_sample_evaluation(9.0, 9.0, 9.0, 9.0, 9.0)]
        
        calc.add_iteration(1, evals1, prompt="Prompt v1")
        calc.add_iteration(2, evals2, prompt="Prompt v2")
        calc.add_iteration(3, evals3, prompt="Prompt v3")
        
        assert len(calc.iteration_history) == 3
        assert calc.current_iteration == 3
        
        print(f"✅ Tracked 3 iterations")
        
        # Retrieve specific iteration
        iter2 = calc.get_iteration_metrics(2)
        assert iter2 is not None
        assert iter2["iteration"] == 2
        assert "prompt" in iter2
        
        print(f"✅ Retrieved iteration 2:")
        print(f"   Composite: {iter2['composite_stats']['mean']:.2f}")
        print(f"   Prompt length: {iter2['prompt_length']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_iteration_comparison():
    """Test iteration comparison logic."""
    print("\n" + "="*60)
    print("TEST 4: Iteration Comparison")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        # Add two iterations with clear difference
        evals1 = [create_sample_evaluation(6.0, 6.0, 6.0, 6.0, 6.0)]
        evals2 = [create_sample_evaluation(8.0, 8.0, 8.0, 8.0, 8.0)]
        
        calc.add_iteration(1, evals1)
        calc.add_iteration(2, evals2)
        
        # Compare
        comparison = calc.compare_iterations(1, 2)
        
        assert "composite_score" in comparison
        assert "improvements" in comparison
        assert "regressions" in comparison
        
        delta = comparison["composite_score"]["delta"]
        assert delta > 0  # Should have improved
        
        print(f"✅ Comparison calculated:")
        print(f"   Delta: {delta:.2f}")
        print(f"   Percent change: {comparison['composite_score']['percent_change']:.2f}%")
        print(f"   Improvements: {len(comparison['improvements'])} criteria")
        print(f"   Regressions: {len(comparison['regressions'])} criteria")
        
        # Check improvements
        assert len(comparison["improvements"]) > 0
        print(f"✅ Detected improvements in: {list(comparison['improvements'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_best_iteration():
    """Test finding best iteration."""
    print("\n" + "="*60)
    print("TEST 5: Best Iteration Detection")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        # Add iterations with varying scores
        calc.add_iteration(1, [create_sample_evaluation(6.0, 6.0, 6.0, 6.0, 6.0)])
        calc.add_iteration(2, [create_sample_evaluation(9.0, 9.0, 9.0, 9.0, 9.0)])  # Best
        calc.add_iteration(3, [create_sample_evaluation(7.0, 7.0, 7.0, 7.0, 7.0)])
        
        best = calc.get_best_iteration()
        
        assert best is not None
        assert best["iteration"] == 2
        
        print(f"✅ Found best iteration:")
        print(f"   Iteration: {best['iteration']}")
        print(f"   Score: {best['composite_stats']['mean']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_trend():
    """Test performance trend analysis."""
    print("\n" + "="*60)
    print("TEST 6: Performance Trend Analysis")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        # Add improving iterations
        calc.add_iteration(1, [create_sample_evaluation(5.0, 5.0, 5.0, 5.0, 5.0)])
        calc.add_iteration(2, [create_sample_evaluation(6.0, 6.0, 6.0, 6.0, 6.0)])
        calc.add_iteration(3, [create_sample_evaluation(7.0, 7.0, 7.0, 7.0, 7.0)])
        calc.add_iteration(4, [create_sample_evaluation(8.0, 8.0, 8.0, 8.0, 8.0)])
        
        trend = calc.get_performance_trend()
        
        assert trend["trend"] == "improving"
        assert trend["slope"] > 0
        assert trend["total_change"] > 0
        
        print(f"✅ Trend analysis:")
        print(f"   Trend: {trend['trend']}")
        print(f"   Slope: {trend['slope']:.3f}")
        print(f"   Total change: {trend['total_change']:.2f}")
        print(f"   From {trend['first_score']:.2f} to {trend['last_score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convergence_detection():
    """Test convergence detection."""
    print("\n" + "="*60)
    print("TEST 7: Convergence Detection")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        # Test 1: Threshold reached
        calc.add_iteration(1, [create_sample_evaluation(9.0, 9.0, 9.0, 9.0, 9.0)])
        
        convergence = calc.check_convergence(threshold=8.5)
        assert convergence["converged"] == True
        assert convergence["reason"] == "threshold_reached"
        
        print(f"✅ Threshold convergence detected:")
        print(f"   Reason: {convergence['reason']}")
        print(f"   Score: {convergence['current_score']:.2f}")
        
        # Test 2: Plateau detected
        calc2 = create_metrics_calculator()
        calc2.add_iteration(1, [create_sample_evaluation(7.0, 7.0, 7.0, 7.0, 7.0)])
        calc2.add_iteration(2, [create_sample_evaluation(7.01, 7.01, 7.01, 7.01, 7.01)])
        calc2.add_iteration(3, [create_sample_evaluation(7.015, 7.015, 7.015, 7.015, 7.015)])
        
        convergence2 = calc2.check_convergence(threshold=9.0, min_improvement=0.02)
        assert convergence2["converged"] == True
        assert convergence2["reason"] == "plateau_detected"
        
        print(f"✅ Plateau convergence detected:")
        print(f"   Reason: {convergence2['reason']}")
        
        # Test 3: Still improving
        calc3 = create_metrics_calculator()
        calc3.add_iteration(1, [create_sample_evaluation(5.0, 5.0, 5.0, 5.0, 5.0)])
        calc3.add_iteration(2, [create_sample_evaluation(6.0, 6.0, 6.0, 6.0, 6.0)])
        
        convergence3 = calc3.check_convergence(threshold=9.0)
        assert convergence3["converged"] == False
        assert convergence3["reason"] == "still_improving"
        
        print(f"✅ Still improving detected:")
        print(f"   Reason: {convergence3['reason']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flags_and_suggestions():
    """Test tracking of flags and suggestions."""
    print("\n" + "="*60)
    print("TEST 8: Flags and Suggestions Tracking")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        # Create evaluations with flags
        evals = [
            create_sample_evaluation(
                5.0, 7.0, 7.0, 7.0, 7.0,
                flags=["potential_hallucination"],
                suggestions=["Verify facts"]
            ),
            create_sample_evaluation(
                6.0, 5.0, 7.0, 7.0, 7.0,
                flags=["unclear_explanation"],
                suggestions=["Improve clarity"]
            ),
            create_sample_evaluation(
                7.0, 7.0, 7.0, 4.0, 7.0,
                flags=["off_topic"],
                suggestions=["Stay on topic"]
            )
        ]
        
        metrics = calc.calculate_metrics(evals)
        
        flags_summary = metrics["flags_summary"]
        suggestions_summary = metrics["suggestions_summary"]
        
        assert len(flags_summary) == 3
        assert len(suggestions_summary) == 3
        
        print(f"✅ Flags tracked: {flags_summary}")
        print(f"✅ Suggestions tracked: {suggestions_summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_summary_generation():
    """Test comprehensive summary generation."""
    print("\n" + "="*60)
    print("TEST 9: Summary Generation")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        # Add multiple iterations
        for i in range(1, 6):
            score = 5.0 + i  # Improving trend
            evals = [create_sample_evaluation(score, score, score, score, score)]
            calc.add_iteration(i, evals)
        
        summary = calc.generate_summary()
        
        assert "total_iterations" in summary
        assert "best_iteration" in summary
        assert "score_range" in summary
        assert "trend" in summary
        assert "convergence" in summary
        
        print(f"✅ Summary generated:")
        print(f"   Total iterations: {summary['total_iterations']}")
        print(f"   Best iteration: {summary['best_iteration']['number']}")
        print(f"   Best score: {summary['best_iteration']['score']:.2f}")
        print(f"   Score range: {summary['score_range']['min']:.2f} - {summary['score_range']['max']:.2f}")
        print(f"   Trend: {summary['trend']['trend']}")
        print(f"   Converged: {summary['convergence']['converged']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_and_reset():
    """Test history export and reset."""
    print("\n" + "="*60)
    print("TEST 10: Export and Reset")
    print("="*60)
    
    try:
        calc = create_metrics_calculator()
        
        # Add some iterations
        calc.add_iteration(1, [create_sample_evaluation(7.0, 7.0, 7.0, 7.0, 7.0)])
        calc.add_iteration(2, [create_sample_evaluation(8.0, 8.0, 8.0, 8.0, 8.0)])
        
        # Export
        history = calc.export_history()
        assert len(history) == 2
        assert isinstance(history, list)
        
        print(f"✅ Exported {len(history)} iterations")
        
        # Reset
        calc.reset()
        assert len(calc.iteration_history) == 0
        assert calc.current_iteration == 0
        
        print(f"✅ Calculator reset:")
        print(f"   History length: {len(calc.iteration_history)}")
        print(f"   Current iteration: {calc.current_iteration}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all metrics calculator tests."""
    print("="*60)
    print("🧪 Metrics Calculator Tests - Feature 8")
    print("="*60)
    
    tests = [
        ("Calculator Initialization", test_calculator_initialization),
        ("Metrics Calculation", test_metrics_calculation),
        ("Iteration Tracking", test_iteration_tracking),
        ("Iteration Comparison", test_iteration_comparison),
        ("Best Iteration Detection", test_best_iteration),
        ("Performance Trend Analysis", test_performance_trend),
        ("Convergence Detection", test_convergence_detection),
        ("Flags and Suggestions Tracking", test_flags_and_suggestions),
        ("Summary Generation", test_summary_generation),
        ("Export and Reset", test_export_and_reset)
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
        print("\n📋 Metrics Calculator Ready:")
        print("  • Aggregate evaluation results")
        print("  • Calculate statistics (mean, std, min, max)")
        print("  • Track iteration history")
        print("  • Compare iterations")
        print("  • Detect convergence")
        print("  • Analyze performance trends")
        print("  • Generate comprehensive summaries")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
