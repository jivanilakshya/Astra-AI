"""
Test suite for Analytics Agent.

Tests cover:
- Iteration logging
- Performance trend analysis
- Report generation
- Visualization creation
- Data export (JSON, CSV)
- Anomaly detection
- Statistics calculation
"""

import tempfile
from pathlib import Path
import json
import csv

from utils.analytics import (
    AnalyticsAgent,
    IterationLog,
    create_analytics
)


def create_sample_evaluations(
    base_score: float = 7.0,
    num_evaluations: int = 3
) -> list:
    """Create sample evaluation data."""
    evaluations = []
    for i in range(num_evaluations):
        evaluations.append({
            "composite_score": base_score + i * 0.2,
            "scores": {
                "correctness": base_score,
                "clarity": base_score + 0.5,
                "reasoning": base_score - 0.3,
                "relevance": base_score + 0.2,
                "conciseness": base_score + 0.1
            }
        })
    return evaluations


def test_analytics_initialization():
    """Test AnalyticsAgent initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = AnalyticsAgent(storage_path=tmpdir)
        
        assert analytics.storage_path == Path(tmpdir)
        assert len(analytics.iteration_logs) == 0
        assert len(analytics.anomalies) == 0
        
        print("✅ TEST 1 PASSED: Analytics Initialization")


def test_factory_function():
    """Test create_analytics factory function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(storage_path=tmpdir)
        
        assert isinstance(analytics, AnalyticsAgent)
        assert analytics.storage_path == Path(tmpdir)
        
        print("✅ TEST 2 PASSED: Factory Function")


def test_log_iteration():
    """Test logging an iteration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        evaluations = create_sample_evaluations(base_score=7.0)
        
        analytics.log_iteration(
            iteration=1,
            prompt="Test prompt",
            evaluations=evaluations
        )
        
        assert len(analytics.iteration_logs) == 1
        assert analytics.iteration_logs[0].iteration == 1
        assert analytics.iteration_logs[0].num_questions == 3
        assert analytics.iteration_logs[0].avg_composite_score > 0
        
        print("✅ TEST 3 PASSED: Log Iteration")


def test_log_multiple_iterations():
    """Test logging multiple iterations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        for i in range(5):
            evaluations = create_sample_evaluations(base_score=6.0 + i * 0.5)
            analytics.log_iteration(
                iteration=i + 1,
                prompt=f"Prompt v{i+1}",
                evaluations=evaluations
            )
        
        assert len(analytics.iteration_logs) == 5
        assert analytics.iteration_logs[0].iteration == 1
        assert analytics.iteration_logs[4].iteration == 5
        
        print("✅ TEST 4 PASSED: Log Multiple Iterations")


def test_log_iteration_empty_evaluations():
    """Test logging with empty evaluations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        analytics.log_iteration(
            iteration=1,
            prompt="Test",
            evaluations=[]
        )
        
        # Should not add log entry
        assert len(analytics.iteration_logs) == 0
        
        print("✅ TEST 5 PASSED: Log Iteration (Empty Evaluations)")


def test_performance_trend_insufficient_data():
    """Test trend analysis with insufficient data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        trend = analytics.get_performance_trend(window=3)
        
        assert trend == "insufficient_data"
        
        print("✅ TEST 6 PASSED: Performance Trend (Insufficient Data)")


def test_performance_trend_improving():
    """Test trend detection - improving."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log improving scores
        for i in range(5):
            evaluations = create_sample_evaluations(base_score=6.0 + i * 0.5)
            analytics.log_iteration(i + 1, f"Prompt {i+1}", evaluations)
        
        trend = analytics.get_performance_trend(window=3)
        
        assert trend == "improving"
        
        print("✅ TEST 7 PASSED: Performance Trend (Improving)")


def test_performance_trend_declining():
    """Test trend detection - declining."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log declining scores
        for i in range(5):
            evaluations = create_sample_evaluations(base_score=8.0 - i * 0.5)
            analytics.log_iteration(i + 1, f"Prompt {i+1}", evaluations)
        
        trend = analytics.get_performance_trend(window=3)
        
        assert trend == "declining"
        
        print("✅ TEST 8 PASSED: Performance Trend (Declining)")


def test_performance_trend_stable():
    """Test trend detection - stable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log stable scores
        for i in range(5):
            evaluations = create_sample_evaluations(base_score=7.0 + i * 0.02)
            analytics.log_iteration(i + 1, f"Prompt {i+1}", evaluations)
        
        trend = analytics.get_performance_trend(window=3)
        
        assert trend == "stable"
        
        print("✅ TEST 9 PASSED: Performance Trend (Stable)")


def test_anomaly_detection_performance_drop():
    """Test anomaly detection for performance drops."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log normal performance
        evaluations1 = create_sample_evaluations(base_score=8.0)
        analytics.log_iteration(1, "Prompt 1", evaluations1)
        
        # Log significant drop
        evaluations2 = create_sample_evaluations(base_score=5.0)
        analytics.log_iteration(2, "Prompt 2", evaluations2)
        
        # Should detect anomaly
        assert len(analytics.anomalies) > 0
        assert analytics.anomalies[0]["type"] == "performance_drop"
        
        print("✅ TEST 10 PASSED: Anomaly Detection (Performance Drop)")


def test_anomaly_detection_prompt_length():
    """Test anomaly detection for prompt length spikes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log normal prompts
        for i in range(3):
            evaluations = create_sample_evaluations()
            analytics.log_iteration(i + 1, "Short prompt", evaluations)
        
        # Log very long prompt
        long_prompt = "A" * 1000  # Much longer than previous
        evaluations = create_sample_evaluations()
        analytics.log_iteration(4, long_prompt, evaluations)
        
        # Should detect anomaly
        prompt_anomalies = [a for a in analytics.anomalies if a["type"] == "prompt_length_spike"]
        assert len(prompt_anomalies) > 0
        
        print("✅ TEST 11 PASSED: Anomaly Detection (Prompt Length)")


def test_generate_summary_report():
    """Test summary report generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log several iterations
        for i in range(4):
            evaluations = create_sample_evaluations(base_score=6.0 + i * 0.5)
            analytics.log_iteration(i + 1, f"Prompt {i+1}", evaluations)
        
        report = analytics.generate_summary_report()
        
        assert "summary" in report
        assert "criterion_analysis" in report
        assert "insights" in report
        assert report["summary"]["total_iterations"] == 4
        assert report["summary"]["initial_score"] < report["summary"]["final_score"]
        
        print("✅ TEST 12 PASSED: Generate Summary Report")


def test_generate_summary_report_empty():
    """Test summary report with no data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        report = analytics.generate_summary_report()
        
        assert "error" in report
        
        print("✅ TEST 13 PASSED: Generate Summary Report (Empty)")


def test_insights_generation():
    """Test insights generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log improving iterations
        for i in range(5):
            evaluations = create_sample_evaluations(base_score=6.0 + i * 0.8)
            analytics.log_iteration(i + 1, f"Prompt {i+1}", evaluations)
        
        insights = analytics._generate_insights()
        
        assert len(insights) > 0
        assert any("improvement" in insight.lower() for insight in insights)
        
        print("✅ TEST 14 PASSED: Insights Generation")


def test_export_to_json():
    """Test JSON export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log data
        evaluations = create_sample_evaluations()
        analytics.log_iteration(1, "Test prompt", evaluations)
        
        # Export
        filepath = analytics.export_to_json()
        
        # Verify file exists and contains data
        assert Path(filepath).exists()
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert "iteration_logs" in data
        assert len(data["iteration_logs"]) == 1
        assert "summary" in data
        
        print("✅ TEST 15 PASSED: Export to JSON")


def test_export_to_csv():
    """Test CSV export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log data
        for i in range(3):
            evaluations = create_sample_evaluations()
            analytics.log_iteration(i + 1, f"Prompt {i+1}", evaluations)
        
        # Export
        filepath = analytics.export_to_csv()
        
        # Verify file exists and contains data
        assert Path(filepath).exists()
        
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        assert "iteration" in rows[0]
        assert "avg_composite_score" in rows[0]
        
        print("✅ TEST 16 PASSED: Export to CSV")


def test_load_from_json():
    """Test loading from JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics1 = create_analytics(tmpdir)
        
        # Log and export
        evaluations = create_sample_evaluations()
        analytics1.log_iteration(1, "Test prompt", evaluations)
        filepath = analytics1.export_to_json()
        
        # Create new analytics and load
        analytics2 = create_analytics(tmpdir)
        analytics2.load_from_json(filepath)
        
        assert len(analytics2.iteration_logs) == 1
        assert analytics2.iteration_logs[0].iteration == 1
        
        print("✅ TEST 17 PASSED: Load from JSON")


def test_clear_logs():
    """Test clearing logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Add data
        evaluations = create_sample_evaluations()
        analytics.log_iteration(1, "Test", evaluations)
        analytics.anomalies.append({"type": "test"})
        
        assert len(analytics.iteration_logs) == 1
        assert len(analytics.anomalies) == 1
        
        # Clear
        analytics.clear_logs()
        
        assert len(analytics.iteration_logs) == 0
        assert len(analytics.anomalies) == 0
        
        print("✅ TEST 18 PASSED: Clear Logs")


def test_get_statistics():
    """Test statistics calculation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log data
        for i in range(4):
            evaluations = create_sample_evaluations(base_score=7.0 + i * 0.3)
            analytics.log_iteration(i + 1, f"Prompt {i+1}", evaluations)
        
        stats = analytics.get_statistics()
        
        assert stats["num_iterations"] == 4
        assert stats["avg_score"] > 0
        assert stats["min_score"] <= stats["max_score"]
        assert stats["total_questions_evaluated"] == 12  # 4 iterations * 3 questions
        
        print("✅ TEST 19 PASSED: Get Statistics")


def test_get_statistics_empty():
    """Test statistics with no data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        stats = analytics.get_statistics()
        
        assert stats["num_iterations"] == 0
        assert stats["num_anomalies"] == 0
        
        print("✅ TEST 20 PASSED: Get Statistics (Empty)")


def test_compare_iterations():
    """Test iteration comparison."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Log iterations
        evaluations1 = create_sample_evaluations(base_score=6.0)
        analytics.log_iteration(1, "Prompt v1", evaluations1)
        
        evaluations2 = create_sample_evaluations(base_score=7.5)
        analytics.log_iteration(2, "Prompt v2 - much longer prompt", evaluations2)
        
        # Compare
        comparison = analytics.compare_iterations(1, 2)
        
        assert comparison["iteration_a"] == 1
        assert comparison["iteration_b"] == 2
        assert comparison["score_difference"] > 0
        assert comparison["improvement"] == "yes"
        
        print("✅ TEST 21 PASSED: Compare Iterations")


def test_compare_iterations_not_found():
    """Test comparison with invalid iterations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        comparison = analytics.compare_iterations(1, 2)
        
        assert "error" in comparison
        
        print("✅ TEST 22 PASSED: Compare Iterations (Not Found)")


def test_iteration_log_dataclass():
    """Test IterationLog dataclass."""
    log = IterationLog(
        iteration=1,
        timestamp="2024-01-01T00:00:00",
        prompt="Test prompt",
        prompt_length=100,
        num_questions=5,
        avg_composite_score=7.5,
        scores_by_criterion={
            "correctness": 7.5,
            "clarity": 8.0,
            "reasoning": 7.0,
            "relevance": 7.5,
            "conciseness": 7.0
        },
        best_score=8.5,
        worst_score=6.5,
        metadata={"test": "data"}
    )
    
    assert log.iteration == 1
    assert log.avg_composite_score == 7.5
    
    # Test to_dict
    log_dict = log.to_dict()
    assert log_dict["iteration"] == 1
    assert log_dict["metadata"]["test"] == "data"
    
    print("✅ TEST 23 PASSED: IterationLog Dataclass")


def test_visualization_matplotlib_unavailable():
    """Test visualization when matplotlib is unavailable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        evaluations = create_sample_evaluations()
        analytics.log_iteration(1, "Test", evaluations)
        
        # Should return None if matplotlib unavailable, or path if available
        result = analytics.generate_visualization()
        
        # Either None (no matplotlib) or valid path
        assert result is None or Path(result).exists()
        
        print("✅ TEST 24 PASSED: Visualization (graceful handling)")


def test_integration_workflow():
    """Test complete analytics workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analytics = create_analytics(tmpdir)
        
        # Simulate optimization iterations
        for i in range(6):
            base_score = 6.0 + i * 0.4
            evaluations = create_sample_evaluations(base_score=base_score)
            analytics.log_iteration(i + 1, f"Prompt version {i+1}", evaluations)
        
        # Check logs
        assert len(analytics.iteration_logs) == 6
        
        # Get statistics
        stats = analytics.get_statistics()
        assert stats["num_iterations"] == 6
        
        # Generate report
        report = analytics.generate_summary_report()
        assert report["summary"]["total_iterations"] == 6
        assert len(report["insights"]) > 0
        
        # Check trend
        trend = analytics.get_performance_trend()
        assert trend in ["improving", "stable", "declining"]
        
        # Export data
        json_path = analytics.export_to_json()
        assert Path(json_path).exists()
        
        csv_path = analytics.export_to_csv()
        assert Path(csv_path).exists()
        
        # Generate visualization (if matplotlib available)
        viz_path = analytics.generate_visualization()
        # Either None or exists
        assert viz_path is None or Path(viz_path).exists()
        
        # Compare iterations
        comparison = analytics.compare_iterations(1, 6)
        assert comparison["improvement"] == "yes"
        
        print("✅ TEST 25 PASSED: Integration Workflow")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING: Analytics Agent")
    print("=" * 60)
    
    test_analytics_initialization()
    test_factory_function()
    test_log_iteration()
    test_log_multiple_iterations()
    test_log_iteration_empty_evaluations()
    test_performance_trend_insufficient_data()
    test_performance_trend_improving()
    test_performance_trend_declining()
    test_performance_trend_stable()
    test_anomaly_detection_performance_drop()
    test_anomaly_detection_prompt_length()
    test_generate_summary_report()
    test_generate_summary_report_empty()
    test_insights_generation()
    test_export_to_json()
    test_export_to_csv()
    test_load_from_json()
    test_clear_logs()
    test_get_statistics()
    test_get_statistics_empty()
    test_compare_iterations()
    test_compare_iterations_not_found()
    test_iteration_log_dataclass()
    test_visualization_matplotlib_unavailable()
    test_integration_workflow()
    
    print("=" * 60)
    print("ALL TESTS PASSED! ✅")
    print("=" * 60)
