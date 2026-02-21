"""
Test suite for Model Selection and Cost Tracking.

Tests cover:
- Model selection based on task complexity
- Cost calculation and tracking
- Budget management and alerts
- Cost optimization recommendations
- Data export/import
- Custom model pricing
"""

import tempfile
from pathlib import Path
import json

from utils.model_selector import (
    ModelSelector,
    TaskComplexity,
    AgentType,
    ModelPricing,
    UsageRecord,
    BudgetAlert,
    create_model_selector
)


def test_model_selector_initialization():
    """Test ModelSelector initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = ModelSelector(
            budget_limit=100.0,
            warning_threshold=0.8,
            prefer_open_source=True,
            storage_path=tmpdir
        )
        
        assert selector.budget_limit == 100.0
        assert selector.warning_threshold == 0.8
        assert selector.prefer_open_source == True
        assert selector.total_cost == 0.0
        assert len(selector.usage_records) == 0
        
        print("✅ TEST 1 PASSED: Model Selector Initialization")


def test_factory_function():
    """Test create_model_selector factory function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(
            budget_limit=50.0,
            storage_path=tmpdir
        )
        
        assert isinstance(selector, ModelSelector)
        assert selector.budget_limit == 50.0
        
        print("✅ TEST 2 PASSED: Factory Function")


def test_model_pricing_dataclass():
    """Test ModelPricing dataclass."""
    pricing = ModelPricing(
        model_name="test-model",
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03,
        context_window=8192,
        performance_tier=2
    )
    
    # Test cost calculation
    cost = pricing.calculate_cost(1000, 1000)
    expected = (1000/1000 * 0.01) + (1000/1000 * 0.03)
    assert abs(cost - expected) < 0.0001
    
    print("✅ TEST 3 PASSED: ModelPricing Dataclass")


def test_select_model_simple_task():
    """Test model selection for simple tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(
            prefer_open_source=True,
            storage_path=tmpdir
        )
        
        model = selector.select_model(TaskComplexity.SIMPLE)
        
        # Should select a cheap/free model
        assert model in ["phi-3-mini", "mistral-7b", "llama-3-8b", "gpt-3.5-turbo"]
        
        print("✅ TEST 4 PASSED: Select Model (Simple Task)")


def test_select_model_complex_task():
    """Test model selection for complex tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(
            prefer_open_source=True,
            storage_path=tmpdir
        )
        
        model = selector.select_model(TaskComplexity.COMPLEX)
        
        # Should select a more capable model
        assert model in ["llama-3-70b", "claude-3-sonnet", "gpt-4-turbo", "gpt-4"]
        
        print("✅ TEST 5 PASSED: Select Model (Complex Task)")


def test_select_model_critical_task():
    """Test model selection for critical tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(storage_path=tmpdir)
        
        model = selector.select_model(TaskComplexity.CRITICAL)
        
        # Should select a premium model
        assert model in ["gpt-4", "claude-3-opus", "claude-3-sonnet", "gpt-4-turbo"]
        
        print("✅ TEST 6 PASSED: Select Model (Critical Task)")


def test_select_model_context_requirement():
    """Test model selection with context window requirement."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use prefer_open_source=False to get Claude models with large context
        selector = ModelSelector(storage_path=tmpdir, prefer_open_source=False)
        
        # Request model with large context
        model = selector.select_model(
            TaskComplexity.MODERATE,
            required_context=100000
        )
        
        # Should select a model with large context (Claude models have 200K)
        selected_pricing = selector.get_model_info(model)
        assert selected_pricing is not None
        assert selected_pricing.context_window >= 100000
        
        print("✅ TEST 7 PASSED: Select Model (Context Requirement)")


def test_record_usage():
    """Test recording LLM usage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(storage_path=tmpdir)
        
        cost = selector.record_usage(
            agent_type=AgentType.GENERATOR,
            model_name="gpt-3.5-turbo",
            input_tokens=1000,
            output_tokens=500
        )
        
        assert cost > 0
        assert len(selector.usage_records) == 1
        assert selector.total_cost == cost
        
        print("✅ TEST 8 PASSED: Record Usage")


def test_record_multiple_usage():
    """Test recording multiple LLM operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(storage_path=tmpdir)
        
        # Record multiple operations
        cost1 = selector.record_usage(AgentType.GENERATOR, "gpt-3.5-turbo", 1000, 500)
        cost2 = selector.record_usage(AgentType.JUDGE, "gpt-4", 800, 300)
        cost3 = selector.record_usage(AgentType.OPTIMIZER, "claude-3-sonnet", 1200, 400)
        
        assert len(selector.usage_records) == 3
        assert abs(selector.total_cost - (cost1 + cost2 + cost3)) < 0.0001
        
        print("✅ TEST 9 PASSED: Record Multiple Usage")


def test_budget_warning_alert():
    """Test budget warning alert."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(
            budget_limit=10.0,
            warning_threshold=0.8,
            storage_path=tmpdir
        )
        
        # Use 85% of budget - should trigger warning
        # gpt-4: $0.03 input, $0.06 output per 1k tokens
        # To reach ~$8.5: input cost = 10k * 0.03/1k = $0.30
        # Output cost needed = $8.5 - $0.30 = $8.20
        # Output tokens = $8.20 / (0.06/1000) = 136,667 tokens
        selector.record_usage(AgentType.GENERATOR, "gpt-4", 10000, 137000)
        
        # Should have warning alert
        assert len(selector.alerts) > 0
        assert any(a.alert_type == "warning" for a in selector.alerts)
        
        print("✅ TEST 10 PASSED: Budget Warning Alert")


def test_budget_exceeded_alert():
    """Test budget exceeded alert."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(
            budget_limit=1.0,
            storage_path=tmpdir
        )
        
        # Exceed budget
        selector.record_usage(AgentType.GENERATOR, "gpt-4", 10000, 20000)
        
        # Should have exceeded alert
        assert len(selector.alerts) > 0
        assert any(a.alert_type == "exceeded" for a in selector.alerts)
        
        print("✅ TEST 11 PASSED: Budget Exceeded Alert")


def test_select_model_budget_constraint():
    """Test model selection under budget constraints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(
            budget_limit=1.0,
            prefer_open_source=False,
            storage_path=tmpdir
        )
        
        # Exceed budget
        selector.record_usage(AgentType.GENERATOR, "gpt-4", 10000, 20000)
        
        # Should now select cheaper model
        model = selector.select_model(TaskComplexity.COMPLEX)
        
        # Should prefer cheaper options
        pricing = selector.get_model_info(model)
        assert pricing.input_cost_per_1k < 0.02  # Not premium pricing
        
        print("✅ TEST 12 PASSED: Select Model (Budget Constraint)")


def test_get_cost_summary():
    """Test cost summary generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(
            budget_limit=100.0,
            storage_path=tmpdir
        )
        
        # Record varied usage
        selector.record_usage(AgentType.GENERATOR, "gpt-3.5-turbo", 1000, 500)
        selector.record_usage(AgentType.GENERATOR, "gpt-3.5-turbo", 1500, 600)
        selector.record_usage(AgentType.JUDGE, "gpt-4", 800, 300)
        
        summary = selector.get_cost_summary()
        
        assert "total_cost" in summary
        assert "by_agent" in summary
        assert "by_model" in summary
        assert summary["total_operations"] == 3
        assert "generator" in summary["by_agent"]
        assert "judge" in summary["by_agent"]
        assert summary["budget_status"] == "healthy"
        
        print("✅ TEST 13 PASSED: Get Cost Summary")


def test_get_cost_summary_empty():
    """Test cost summary with no usage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(storage_path=tmpdir)
        
        summary = selector.get_cost_summary()
        
        assert summary["total_cost"] == 0.0
        assert summary["total_operations"] == 0
        assert summary["budget_status"] == "no_data"
        
        print("✅ TEST 14 PASSED: Get Cost Summary (Empty)")


def test_get_cost_recommendations():
    """Test cost optimization recommendations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(
            prefer_open_source=False,
            storage_path=tmpdir
        )
        
        # Use expensive models heavily
        for _ in range(5):
            selector.record_usage(AgentType.GENERATOR, "gpt-4", 1000, 1000)
        
        recommendations = selector.get_cost_recommendations()
        
        assert len(recommendations) > 0
        assert isinstance(recommendations[0], str)
        
        print("✅ TEST 15 PASSED: Get Cost Recommendations")


def test_recommendations_for_open_source():
    """Test recommendations suggest open source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(
            prefer_open_source=False,
            storage_path=tmpdir
        )
        
        # Use paid models extensively to exceed $10 threshold
        # gpt-4: $0.03 input, $0.06 output per 1k tokens
        # Need > $10 total, using only paid models
        # 100k input + 100k output = $3 + $6 = $9
        # 120k input + 120k output = $3.6 + $7.2 = $10.8
        selector.record_usage(AgentType.GENERATOR, "gpt-4", 120000, 120000)
        
        recommendations = selector.get_cost_recommendations()
        
        # Should recommend open source (total > $10, open source < 20% of total)
        assert any("open source" in rec.lower() for rec in recommendations)
        
        print("✅ TEST 16 PASSED: Recommendations (Open Source)")


def test_export_usage_data():
    """Test exporting usage data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(storage_path=tmpdir)
        
        # Record some usage
        selector.record_usage(AgentType.GENERATOR, "gpt-3.5-turbo", 1000, 500)
        
        # Export
        filepath = selector.export_usage_data()
        
        # Verify file exists
        assert Path(filepath).exists()
        
        # Verify content
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert "summary" in data
        assert "usage_records" in data
        assert len(data["usage_records"]) == 1
        
        print("✅ TEST 17 PASSED: Export Usage Data")


def test_load_usage_data():
    """Test loading usage data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector1 = create_model_selector(storage_path=tmpdir)
        
        # Record and export
        selector1.record_usage(AgentType.GENERATOR, "gpt-3.5-turbo", 1000, 500)
        selector1.record_usage(AgentType.JUDGE, "gpt-4", 800, 300)
        filepath = selector1.export_usage_data()
        
        # Load in new selector
        selector2 = create_model_selector(storage_path=tmpdir)
        selector2.load_usage_data(filepath)
        
        assert len(selector2.usage_records) == 2
        assert selector2.total_cost > 0
        
        print("✅ TEST 18 PASSED: Load Usage Data")


def test_reset_tracking():
    """Test resetting usage tracking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(storage_path=tmpdir)
        
        # Record usage
        selector.record_usage(AgentType.GENERATOR, "gpt-3.5-turbo", 1000, 500)
        assert len(selector.usage_records) == 1
        assert selector.total_cost > 0
        
        # Reset
        selector.reset_tracking()
        
        assert len(selector.usage_records) == 0
        assert selector.total_cost == 0.0
        assert len(selector.alerts) == 0
        
        print("✅ TEST 19 PASSED: Reset Tracking")


def test_add_custom_model():
    """Test adding custom model pricing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(storage_path=tmpdir)
        
        # Add custom model
        custom_pricing = ModelPricing(
            model_name="custom-model",
            input_cost_per_1k=0.005,
            output_cost_per_1k=0.015,
            context_window=16384,
            performance_tier=2
        )
        
        selector.add_custom_model(custom_pricing)
        
        # Verify it's added
        info = selector.get_model_info("custom-model")
        assert info is not None
        assert info.model_name == "custom-model"
        
        # Can use it for recording
        cost = selector.record_usage(AgentType.GENERATOR, "custom-model", 1000, 500)
        expected = (1.0 * 0.005) + (0.5 * 0.015)
        assert abs(cost - expected) < 0.0001
        
        print("✅ TEST 20 PASSED: Add Custom Model")


def test_get_model_info():
    """Test getting model information."""
    with tempfile.TemporaryDirectory() as tmpdir:
        selector = create_model_selector(storage_path=tmpdir)
        
        info = selector.get_model_info("gpt-4")
        
        assert info is not None
        assert info.model_name == "gpt-4"
        assert info.context_window > 0
        assert info.performance_tier > 0
        
        # Non-existent model
        assert selector.get_model_info("non-existent") is None
        
        print("✅ TEST 21 PASSED: Get Model Info")


def test_usage_record_dataclass():
    """Test UsageRecord dataclass."""
    record = UsageRecord(
        timestamp="2024-01-01T00:00:00",
        agent_type="generator",
        model_name="gpt-4",
        input_tokens=1000,
        output_tokens=500,
        cost=0.045,
        task_complexity="moderate",
        metadata={"test": "data"}
    )
    
    assert record.agent_type == "generator"
    assert record.cost == 0.045
    
    # Test to_dict
    record_dict = record.to_dict()
    assert record_dict["agent_type"] == "generator"
    assert record_dict["metadata"]["test"] == "data"
    
    print("✅ TEST 22 PASSED: UsageRecord Dataclass")


def test_budget_alert_dataclass():
    """Test BudgetAlert dataclass."""
    alert = BudgetAlert(
        timestamp="2024-01-01T00:00:00",
        alert_type="warning",
        current_cost=85.0,
        budget_limit=100.0,
        percentage_used=85.0,
        message="Warning: 85% used"
    )
    
    assert alert.alert_type == "warning"
    assert alert.percentage_used == 85.0
    
    # Test to_dict
    alert_dict = alert.to_dict()
    assert alert_dict["alert_type"] == "warning"
    
    print("✅ TEST 23 PASSED: BudgetAlert Dataclass")


def test_task_complexity_enum():
    """Test TaskComplexity enum."""
    assert TaskComplexity.SIMPLE.value == "simple"
    assert TaskComplexity.MODERATE.value == "moderate"
    assert TaskComplexity.COMPLEX.value == "complex"
    assert TaskComplexity.CRITICAL.value == "critical"
    
    print("✅ TEST 24 PASSED: TaskComplexity Enum")


def test_agent_type_enum():
    """Test AgentType enum."""
    assert AgentType.GENERATOR.value == "generator"
    assert AgentType.JUDGE.value == "judge"
    assert AgentType.OPTIMIZER.value == "optimizer"
    
    print("✅ TEST 25 PASSED: AgentType Enum")


def test_integration_workflow():
    """Test complete cost tracking workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create selector with budget
        selector = create_model_selector(
            budget_limit=50.0,
            warning_threshold=0.8,
            prefer_open_source=True,
            storage_path=tmpdir
        )
        
        # Simulate optimization iterations
        for i in range(5):
            # Select model based on task
            complexity = TaskComplexity.SIMPLE if i < 2 else TaskComplexity.MODERATE
            model = selector.select_model(complexity, AgentType.GENERATOR)
            
            # Record usage
            selector.record_usage(
                AgentType.GENERATOR,
                model,
                input_tokens=1000 + i * 200,
                output_tokens=500 + i * 100,
                task_complexity=complexity
            )
        
        # Get summary
        summary = selector.get_cost_summary()
        assert summary["total_operations"] == 5
        assert summary["total_cost"] >= 0
        
        # Get recommendations
        recommendations = selector.get_cost_recommendations()
        assert len(recommendations) > 0
        
        # Export data
        filepath = selector.export_usage_data()
        assert Path(filepath).exists()
        
        # Load in new selector
        selector2 = create_model_selector(storage_path=tmpdir)
        selector2.load_usage_data(filepath)
        assert len(selector2.usage_records) == 5
        
        print("✅ TEST 26 PASSED: Integration Workflow")


def test_prefer_open_source_strategy():
    """Test open source preference strategy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # With open source preference
        selector1 = create_model_selector(
            prefer_open_source=True,
            storage_path=tmpdir
        )
        
        model1 = selector1.select_model(TaskComplexity.SIMPLE)
        
        # Should prefer free models
        assert model1 in ["phi-3-mini", "mistral-7b", "llama-3-8b", "llama-3-70b"]
        
        # Without open source preference
        selector2 = create_model_selector(
            prefer_open_source=False,
            storage_path=tmpdir
        )
        
        model2 = selector2.select_model(TaskComplexity.SIMPLE)
        
        # May select paid models
        # Just verify it's a valid model
        assert selector2.get_model_info(model2) is not None
        
        print("✅ TEST 27 PASSED: Open Source Preference Strategy")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING: Model Selection and Cost Tracking")
    print("=" * 60)
    
    test_model_selector_initialization()
    test_factory_function()
    test_model_pricing_dataclass()
    test_select_model_simple_task()
    test_select_model_complex_task()
    test_select_model_critical_task()
    test_select_model_context_requirement()
    test_record_usage()
    test_record_multiple_usage()
    test_budget_warning_alert()
    test_budget_exceeded_alert()
    test_select_model_budget_constraint()
    test_get_cost_summary()
    test_get_cost_summary_empty()
    test_get_cost_recommendations()
    test_recommendations_for_open_source()
    test_export_usage_data()
    test_load_usage_data()
    test_reset_tracking()
    test_add_custom_model()
    test_get_model_info()
    test_usage_record_dataclass()
    test_budget_alert_dataclass()
    test_task_complexity_enum()
    test_agent_type_enum()
    test_integration_workflow()
    test_prefer_open_source_strategy()
    
    print("=" * 60)
    print("ALL TESTS PASSED! ✅")
    print("=" * 60)
