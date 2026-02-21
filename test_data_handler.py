"""
Test script for Data Handler - Feature 3
Run this to test data loading functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data import DataLoader, Question
from config import get_config


def test_load_json():
    """Test loading JSON file."""
    print("\n" + "="*60)
    print("TEST 1: Load JSON")
    print("="*60)
    
    try:
        loader = DataLoader()
        questions = loader.load("./data/sample_questions.json")
        
        print(f"✅ Loaded {len(questions)} questions")
        
        if len(questions) > 0:
            q = questions[0]
            print(f"✅ First question - ID: {q.id}, Category: {q.category}")
            return True
        else:
            print("❌ No questions loaded")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_question_dataclass():
    """Test Question dataclass."""
    print("\n" + "="*60)
    print("TEST 2: Question Dataclass")
    print("="*60)
    
    try:
        # Create from dict
        data = {
            "id": 1,
            "question": "Test question?",
            "ground_truth": "Test answer",
            "category": "test",
            "difficulty": "easy"
        }
        
        q = Question.from_dict(data)
        print(f"✅ Created Question: {q}")
        
        # Convert to dict
        q_dict = q.to_dict()
        print(f"✅ Converted to dict: id={q_dict['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_filtering():
    """Test filtering functionality."""
    print("\n" + "="*60)
    print("TEST 3: Filtering")
    print("="*60)
    
    try:
        loader = DataLoader()
        loader.load("./data/sample_questions.json")
        
        # Filter by category
        physics = loader.get_by_category("physics")
        print(f"✅ Physics questions: {len(physics)}")
        
        # Filter by difficulty
        easy = loader.get_by_difficulty("easy")
        print(f"✅ Easy questions: {len(easy)}")
        
        # Combined filter
        filtered = loader.filter(
            categories=["physics", "biology"],
            difficulties=["easy", "medium"]
        )
        print(f"✅ Filtered questions: {len(filtered)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_train_test_split():
    """Test train/test splitting."""
    print("\n" + "="*60)
    print("TEST 4: Train/Test Split")
    print("="*60)
    
    try:
        loader = DataLoader()
        loader.load("./data/sample_questions.json")
        
        # Simple split
        train, test = loader.split_train_test(test_size=0.2, random_seed=42)
        print(f"✅ Simple split - Train: {len(train)}, Test: {len(test)}")
        
        # Stratified split
        train_s, test_s = loader.split_train_test(
            test_size=0.2,
            stratify_by='difficulty',
            random_seed=42
        )
        print(f"✅ Stratified split - Train: {len(train_s)}, Test: {len(test_s)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_statistics():
    """Test statistics generation."""
    print("\n" + "="*60)
    print("TEST 5: Statistics")
    print("="*60)
    
    try:
        loader = DataLoader()
        loader.load("./data/sample_questions.json")
        
        stats = loader.get_statistics()
        
        print(f"✅ Total questions: {stats['total']}")
        print(f"✅ Categories: {stats['categories']}")
        print(f"✅ Difficulties: {stats['difficulties']}")
        print(f"✅ Questions with ground truth: {stats['has_ground_truth']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_validation():
    """Test data validation."""
    print("\n" + "="*60)
    print("TEST 6: Validation")
    print("="*60)
    
    try:
        loader = DataLoader()
        loader.load("./data/sample_questions.json")
        
        is_valid, errors = loader.validate()
        
        if is_valid:
            print("✅ Dataset validation passed")
            return True
        else:
            print(f"⚠️  Validation errors:")
            for error in errors:
                print(f"   - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_export():
    """Test export functionality."""
    print("\n" + "="*60)
    print("TEST 7: Export")
    print("="*60)
    
    try:
        loader = DataLoader()
        loader.load("./data/sample_questions.json")
        
        # Export subset to JSON
        easy_questions = loader.get_by_difficulty("easy")
        loader.export_json("./data/export_test.json", easy_questions)
        print(f"✅ Exported {len(easy_questions)} questions to JSON")
        
        # Export to CSV
        loader.export_csv("./data/export_test.csv", easy_questions)
        print(f"✅ Exported {len(easy_questions)} questions to CSV")
        
        # Clean up test files
        import os
        os.remove("./data/export_test.json")
        os.remove("./data/export_test.csv")
        print("✅ Cleaned up test files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_integration_with_config():
    """Test integration with configuration."""
    print("\n" + "="*60)
    print("TEST 8: Config Integration")
    print("="*60)
    
    try:
        config = get_config()
        data_config = config.data_config
        
        loader = DataLoader(data_dir=data_config['data_dir'])
        questions = loader.load(data_config['sample_questions'])
        
        print(f"✅ Loaded from config path: {len(questions)} questions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("🧪 Data Handler Tests - Feature 3")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Load JSON", test_load_json()))
    results.append(("Question Dataclass", test_question_dataclass()))
    results.append(("Filtering", test_filtering()))
    results.append(("Train/Test Split", test_train_test_split()))
    results.append(("Statistics", test_statistics()))
    results.append(("Validation", test_validation()))
    results.append(("Export", test_export()))
    results.append(("Config Integration", test_integration_with_config()))
    
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
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("="*60)


if __name__ == "__main__":
    main()
