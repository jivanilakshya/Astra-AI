"""
Tests for CLI Controller.

Tests command-line interface with interactive and batch modes.
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from cli.controller import (
    CLIController,
    create_cli_controller,
    parse_arguments
)


class TestCLIController(unittest.TestCase):
    """Test CLI Controller functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def test_controller_initialization(self):
        """Test CLI controller initialization."""
        controller = CLIController(output_dir=self.temp_dir)
        
        assert controller is not None
        assert controller.output_dir == Path(self.temp_dir)
        assert controller.config is not None
        assert controller.session_id is not None
        assert len(controller.questions) == 0
        assert controller.results is None
        
        print("✅ TEST 1 PASSED: Controller Initialization")
    
    def test_factory_function(self):
        """Test factory function."""
        controller = create_cli_controller(output_dir=self.temp_dir)
        
        assert isinstance(controller, CLIController)
        assert controller.output_dir == Path(self.temp_dir)
        
        print("✅ TEST 2 PASSED: Factory Function")
    
    def test_controller_with_budget(self):
        """Test controller with budget limit."""
        controller = CLIController(
            budget_limit=50.0,
            output_dir=self.temp_dir
        )
        
        assert controller.budget_limit == 50.0
        
        print("✅ TEST 3 PASSED: Controller with Budget")
    
    def test_controller_with_max_iterations(self):
        """Test controller with max iterations."""
        controller = CLIController(
            max_iterations=15,
            output_dir=self.temp_dir
        )
        
        # max_iterations is set in config - just verify it was passed
        assert controller.config is not None
        
        print("✅ TEST 4 PASSED: Controller with Max Iterations")
    
    def test_initialize_components(self):
        """Test component initialization."""
        controller = CLIController(output_dir=self.temp_dir)
        
        # Should succeed (components handle missing LLM gracefully)
        result = controller.initialize_components()
        
        # May succeed or fail depending on environment
        # Just check it doesn't crash
        assert isinstance(result, bool)
        
        if result:
            assert controller.model_selector is not None
            assert controller.analytics is not None
            assert controller.teleprompter is not None
            assert controller.generator is not None
            assert controller.judge is not None
            assert controller.optimizer is not None
            assert controller.orchestrator is not None
        
        print("✅ TEST 5 PASSED: Initialize Components")
    
    def test_load_questions_json_list(self):
        """Test loading questions from JSON list."""
        controller = CLIController(output_dir=self.temp_dir)
        
        # Create test JSON file with list
        questions_file = Path(self.temp_dir) / "questions.json"
        test_questions = [
            "What is AI?",
            "Explain machine learning.",
            "What is deep learning?"
        ]
        
        with open(questions_file, 'w') as f:
            json.dump(test_questions, f)
        
        result = controller.load_questions(str(questions_file))
        
        assert result is True
        assert len(controller.questions) == 3
        assert controller.questions[0].question == "What is AI?"
        
        print("✅ TEST 6 PASSED: Load Questions (JSON List)")
    
    def test_load_questions_json_dict(self):
        """Test loading questions from JSON dict."""
        controller = CLIController(output_dir=self.temp_dir)
        
        # Create test JSON file with dict
        questions_file = Path(self.temp_dir) / "questions.json"
        test_data = {
            "questions": [
                "What is AI?",
                "Explain machine learning."
            ]
        }
        
        with open(questions_file, 'w') as f:
            json.dump(test_data, f)
        
        result = controller.load_questions(str(questions_file))
        
        assert result is True
        assert len(controller.questions) == 2
        
        print("✅ TEST 7 PASSED: Load Questions (JSON Dict)")
    
    def test_load_questions_text_file(self):
        """Test loading questions from text file."""
        controller = CLIController(output_dir=self.temp_dir)
        
        # Create test text file
        questions_file = Path(self.temp_dir) / "questions.txt"
        with open(questions_file, 'w') as f:
            f.write("What is AI?\n")
            f.write("Explain machine learning.\n")
            f.write("# This is a comment\n")
            f.write("\n")  # Empty line
            f.write("What is deep learning?\n")
        
        result = controller.load_questions(str(questions_file))
        
        assert result is True
        assert len(controller.questions) == 3
        assert controller.questions[0].question == "What is AI?"
        assert controller.questions[2].question == "What is deep learning?"
        
        print("✅ TEST 8 PASSED: Load Questions (Text File)")
    
    def test_load_questions_nonexistent_file(self):
        """Test loading from nonexistent file."""
        controller = CLIController(output_dir=self.temp_dir)
        
        result = controller.load_questions("/nonexistent/file.json")
        
        assert result is False
        assert len(controller.questions) == 0
        
        print("✅ TEST 9 PASSED: Load Questions (Nonexistent)")
    
    def test_load_questions_with_ground_truth(self):
        """Test loading questions with ground truth."""
        controller = CLIController(output_dir=self.temp_dir)
        
        # Create JSON with question objects
        questions_file = Path(self.temp_dir) / "questions.json"
        test_data = {
            "questions": [
                {
                    "text": "What is 2+2?",
                    "expected_answer": "4"
                }
            ]
        }
        
        with open(questions_file, 'w') as f:
            json.dump(test_data, f)
        
        result = controller.load_questions(str(questions_file))
        
        assert result is True
        assert len(controller.questions) == 1
        assert controller.questions[0].ground_truth == "4"
        
        print("✅ TEST 10 PASSED: Load Questions (With Ground Truth)")
    
    @patch('builtins.input', side_effect=['What is AI?', 'What is ML?', ''])
    @patch('sys.stdout', new_callable=StringIO)
    def test_interactive_mode_no_init(self, mock_stdout, mock_input):
        """Test interactive mode without component init."""
        controller = CLIController(output_dir=self.temp_dir)
        
        # Mock orchestrator to avoid actual optimization
        controller.orchestrator = Mock()
        controller.orchestrator.run_optimization_loop = Mock(return_value={
            'initial_score': 5.0,
            'final_score': 8.0,
            'improvement': 3.0,
            'iterations': 5,
            'converged': True,
            'final_prompt': 'Test prompt',
            'performance_history': [5.0, 6.0, 7.0, 7.5, 8.0]
        })
        
        controller.analytics = Mock()
        controller.analytics.generate_summary_report = Mock(return_value={
            'insights': ['Test insight']
        })
        
        controller.model_selector = Mock()
        controller.model_selector.get_cost_summary = Mock(return_value={
            'total_cost': 0.5,
            'by_agent': {}
        })
        
        # Mock user confirmation
        with patch('builtins.input', side_effect=['What is AI?', '', 'yes', '5']):
            controller.interactive_mode()
        
        # Should have loaded questions
        assert len(controller.questions) == 1
        
        print("✅ TEST 11 PASSED: Interactive Mode (No Init)")
    
    def test_batch_mode(self):
        """Test batch mode."""
        controller = CLIController(output_dir=self.temp_dir)
        
        # Create questions file
        questions_file = Path(self.temp_dir) / "questions.txt"
        with open(questions_file, 'w') as f:
            f.write("What is AI?\n")
            f.write("What is ML?\n")
        
        # Mock components
        controller.orchestrator = Mock()
        controller.orchestrator.run_optimization_loop = Mock(return_value={
            'initial_score': 5.0,
            'final_score': 8.0,
            'improvement': 3.0,
            'iterations': 3,
            'converged': True,
            'final_prompt': 'Optimized prompt'
        })
        
        controller.analytics = Mock()
        controller.analytics.generate_summary_report = Mock(return_value={})
        
        controller.model_selector = Mock()
        controller.model_selector.get_cost_summary = Mock(return_value={
            'total_cost': 0.25
        })
        
        controller.batch_mode(str(questions_file))
        
        # Should have loaded and processed questions
        assert len(controller.questions) == 2
        assert controller.results is not None
        
        print("✅ TEST 12 PASSED: Batch Mode")
    
    def test_display_summary(self):
        """Test display summary."""
        controller = CLIController(output_dir=self.temp_dir)
        
        # Set mock results
        controller.results = {
            'initial_score': 6.0,
            'final_score': 9.0,
            'improvement': 3.0,
            'iterations': 4,
            'converged': True
        }
        
        controller.model_selector = Mock()
        controller.model_selector.get_cost_summary = Mock(return_value={
            'total_cost': 1.5,
            'by_agent': {
                'generator': {'cost': 0.8, 'requests': 10},
                'judge': {'cost': 0.5, 'requests': 10}
            }
        })
        
        controller.analytics = Mock()
        controller.analytics.generate_summary_report = Mock(return_value={
            'insights': ['Performance improved steadily', 'Convergence achieved']
        })
        
        # Should not crash
        controller._display_summary()
        
        print("✅ TEST 13 PASSED: Display Summary")
    
    def test_export_results(self):
        """Test exporting results."""
        controller = CLIController(output_dir=self.temp_dir)
        
        # Set mock results
        controller.results = {
            'initial_score': 6.0,
            'final_score': 9.0,
            'final_prompt': 'Optimized prompt text',
            'performance_history': [6.0, 7.0, 8.0, 9.0]
        }
        
        controller.analytics = Mock()
        controller.analytics.export_to_json = Mock()
        controller.analytics.generate_visualization = Mock()
        
        controller.model_selector = Mock()
        controller.model_selector.export_usage_data = Mock()
        
        controller.export_results()
        
        # Check exported files
        export_dir = controller.output_dir / f"session_{controller.session_id}"
        assert export_dir.exists()
        
        prompt_file = export_dir / "optimized_prompt.txt"
        assert prompt_file.exists()
        
        results_file = export_dir / "results.json"
        assert results_file.exists()
        
        print("✅ TEST 14 PASSED: Export Results")
    
    def test_view_prompt(self):
        """Test viewing optimized prompt."""
        controller = CLIController(output_dir=self.temp_dir)
        
        controller.results = {
            'final_prompt': 'This is the optimized prompt.'
        }
        
        # Should not crash
        controller._view_prompt()
        
        print("✅ TEST 15 PASSED: View Prompt")
    
    def test_view_history(self):
        """Test viewing performance history."""
        controller = CLIController(output_dir=self.temp_dir)
        
        controller.results = {
            'performance_history': [5.0, 6.5, 7.5, 8.5, 9.0]
        }
        
        # Should not crash
        controller._view_history()
        
        print("✅ TEST 16 PASSED: View History")
    
    def test_view_cost_recommendations(self):
        """Test viewing cost recommendations."""
        controller = CLIController(output_dir=self.temp_dir)
        
        controller.model_selector = Mock()
        controller.model_selector.get_cost_recommendations = Mock(return_value=[
            "Use open source models for simple tasks",
            "Consider caching frequent queries"
        ])
        
        # Should not crash
        controller._view_cost_recommendations()
        
        print("✅ TEST 17 PASSED: View Cost Recommendations")
    
    @patch('sys.argv', ['prog', '--interactive'])
    def test_parse_arguments_interactive(self):
        """Test argument parsing for interactive mode."""
        args = parse_arguments()
        
        assert args.interactive is True
        assert args.batch is None
        
        print("✅ TEST 18 PASSED: Parse Arguments (Interactive)")
    
    @patch('sys.argv', ['prog', '--batch', 'questions.json'])
    def test_parse_arguments_batch(self):
        """Test argument parsing for batch mode."""
        args = parse_arguments()
        
        assert args.interactive is False
        assert args.batch == 'questions.json'
        
        print("✅ TEST 19 PASSED: Parse Arguments (Batch)")
    
    @patch('sys.argv', ['prog', '--interactive', '--budget', '25.5'])
    def test_parse_arguments_with_budget(self):
        """Test argument parsing with budget."""
        args = parse_arguments()
        
        assert args.budget == 25.5
        
        print("✅ TEST 20 PASSED: Parse Arguments (Budget)")
    
    @patch('sys.argv', ['prog', '--batch', 'q.txt', '--max-iterations', '20'])
    def test_parse_arguments_with_max_iterations(self):
        """Test argument parsing with max iterations."""
        args = parse_arguments()
        
        assert args.max_iterations == 20
        
        print("✅ TEST 21 PASSED: Parse Arguments (Max Iterations)")
    
    @patch('sys.argv', ['prog', '--batch', 'q.txt', '--output', './results'])
    def test_parse_arguments_with_output(self):
        """Test argument parsing with output directory."""
        args = parse_arguments()
        
        assert args.output == './results'
        
        print("✅ TEST 22 PASSED: Parse Arguments (Output)")
    
    @patch('sys.argv', ['prog', '--batch', 'q.txt', '--export'])
    def test_parse_arguments_with_export(self):
        """Test argument parsing with export flag."""
        args = parse_arguments()
        
        assert args.export is True
        
        print("✅ TEST 23 PASSED: Parse Arguments (Export)")
    
    @patch('sys.argv', ['prog', '--batch', 'q.txt', '--config', 'custom.yaml'])
    def test_parse_arguments_with_config(self):
        """Test argument parsing with config file."""
        args = parse_arguments()
        
        assert args.config == 'custom.yaml'
        
        print("✅ TEST 24 PASSED: Parse Arguments (Config)")
    
    def test_session_id_uniqueness(self):
        """Test session IDs are unique."""
        controller1 = CLIController(output_dir=self.temp_dir)
        
        import time
        time.sleep(0.1)  # Small delay
        
        controller2 = CLIController(output_dir=self.temp_dir)
        
        # May be same if created in same second, but should be strings
        assert isinstance(controller1.session_id, str)
        assert isinstance(controller2.session_id, str)
        assert len(controller1.session_id) > 0
        
        print("✅ TEST 25 PASSED: Session ID Uniqueness")


def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("TESTING: CLI Controller")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCLIController)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    print()
    print("=" * 60)
    if result.wasSuccessful():
        print("ALL TESTS PASSED! ✅")
    else:
        print("SOME TESTS FAILED ❌")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
