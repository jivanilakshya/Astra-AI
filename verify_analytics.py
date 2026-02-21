"""Quick verification script for Analytics Agent."""

from utils import create_analytics
import tempfile

print("Testing AnalyticsAgent functionality...")

with tempfile.TemporaryDirectory() as tmpdir:
    # Create analytics agent
    analytics = create_analytics(tmpdir)
    print(f"✅ Created analytics with storage: {tmpdir}")
    
    # Simulate logging iterations
    for i in range(4):
        evaluations = [
            {
                "composite_score": 6.5 + i * 0.3,
                "scores": {
                    "correctness": 7.0 + i * 0.2,
                    "clarity": 6.5 + i * 0.3,
                    "reasoning": 6.0 + i * 0.4,
                    "relevance": 7.5,
                    "conciseness": 7.0
                }
            }
            for _ in range(3)
        ]
        
        analytics.log_iteration(
            iteration=i + 1,
            prompt=f"Prompt version {i+1}",
            evaluations=evaluations
        )
    
    print(f"✅ Logged {len(analytics.iteration_logs)} iterations")
    
    # Get statistics
    stats = analytics.get_statistics()
    print(f"✅ Statistics: {stats['num_iterations']} iterations, avg score: {stats['avg_score']:.2f}")
    
    # Generate report
    report = analytics.generate_summary_report()
    print(f"✅ Report: {report['summary']['total_improvement']:.2f} point improvement")
    print(f"✅ Insights: {len(report['insights'])} insights generated")
    
    # Get trend
    trend = analytics.get_performance_trend()
    print(f"✅ Performance trend: {trend}")
    
    # Export data
    json_path = analytics.export_to_json()
    csv_path = analytics.export_to_csv()
    print(f"✅ Exported to JSON and CSV")
    
    # Generate visualization (may not work without matplotlib)
    viz_path = analytics.generate_visualization()
    if viz_path:
        print(f"✅ Visualization saved to {viz_path}")
    else:
        print("ℹ️  Visualization skipped (matplotlib not available)")

print("\n" + "=" * 50)
print("ALL VERIFICATIONS PASSED! ✅")
print("=" * 50)
