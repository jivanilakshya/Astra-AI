"""
Data Loader for Questions and Ground Truth.
Supports JSON and CSV formats.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import random


@dataclass
class Question:
    """Data class for a single question."""
    id: int
    question: str
    ground_truth: str
    category: Optional[str] = None
    difficulty: Optional[str] = None
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """Create Question from dictionary."""
        # Extract known fields
        question_data = {
            'id': data.get('id'),
            'question': data.get('question', ''),
            'ground_truth': data.get('ground_truth', ''),
            'category': data.get('category'),
            'difficulty': data.get('difficulty'),
            'context': data.get('context'),
        }
        
        # Store extra fields as metadata
        known_keys = {'id', 'question', 'ground_truth', 'category', 'difficulty', 'context'}
        extra_fields = {k: v for k, v in data.items() if k not in known_keys}
        
        if extra_fields:
            question_data['metadata'] = extra_fields
        
        return cls(**question_data)
    
    def __repr__(self) -> str:
        return f"Question(id={self.id}, category={self.category}, difficulty={self.difficulty})"


class DataLoader:
    """Loader for question datasets."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize data loader.
        
        Args:
            data_dir: Directory containing data files (default: ./data)
        """
        self.data_dir = Path(data_dir) if data_dir else Path("./data")
        self.questions: List[Question] = []
    
    def load_json(self, filepath: str) -> List[Question]:
        """
        Load questions from JSON file.
        
        Args:
            filepath: Path to JSON file
        
        Returns:
            List of Question objects
        
        Format:
            {
                "questions": [
                    {"id": 1, "question": "...", "ground_truth": "..."},
                    ...
                ]
            }
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both direct list and wrapped format
        if isinstance(data, list):
            questions_data = data
        elif isinstance(data, dict) and 'questions' in data:
            questions_data = data['questions']
        else:
            raise ValueError("Invalid JSON format. Expected list or {'questions': [...]}")
        
        # Convert to Question objects
        questions = [Question.from_dict(q) for q in questions_data]
        
        self.questions = questions
        return questions
    
    def load_csv(self, filepath: str) -> List[Question]:
        """
        Load questions from CSV file.
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            List of Question objects
        
        Expected columns: id, question, ground_truth, category (optional), difficulty (optional)
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        questions = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Convert id to int
                if 'id' in row:
                    row['id'] = int(row['id'])
                
                questions.append(Question.from_dict(row))
        
        self.questions = questions
        return questions
    
    def load(self, filepath: str) -> List[Question]:
        """
        Auto-detect format and load questions.
        
        Args:
            filepath: Path to data file
        
        Returns:
            List of Question objects
        """
        filepath = Path(filepath)
        
        if filepath.suffix.lower() == '.json':
            return self.load_json(filepath)
        elif filepath.suffix.lower() == '.csv':
            return self.load_csv(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
    
    def get_by_id(self, question_id: int) -> Optional[Question]:
        """Get question by ID."""
        for q in self.questions:
            if q.id == question_id:
                return q
        return None
    
    def get_by_category(self, category: str) -> List[Question]:
        """Get all questions in a category."""
        return [q for q in self.questions if q.category == category]
    
    def get_by_difficulty(self, difficulty: str) -> List[Question]:
        """Get all questions of a difficulty level."""
        return [q for q in self.questions if q.difficulty == difficulty]
    
    def filter(self, 
               categories: Optional[List[str]] = None,
               difficulties: Optional[List[str]] = None,
               min_id: Optional[int] = None,
               max_id: Optional[int] = None) -> List[Question]:
        """
        Filter questions by multiple criteria.
        
        Args:
            categories: List of categories to include
            difficulties: List of difficulty levels to include
            min_id: Minimum question ID
            max_id: Maximum question ID
        
        Returns:
            Filtered list of questions
        """
        filtered = self.questions.copy()
        
        if categories:
            filtered = [q for q in filtered if q.category in categories]
        
        if difficulties:
            filtered = [q for q in filtered if q.difficulty in difficulties]
        
        if min_id is not None:
            filtered = [q for q in filtered if q.id >= min_id]
        
        if max_id is not None:
            filtered = [q for q in filtered if q.id <= max_id]
        
        return filtered
    
    def split_train_test(self, 
                        test_size: float = 0.2,
                        random_seed: Optional[int] = 42,
                        stratify_by: Optional[str] = None) -> Tuple[List[Question], List[Question]]:
        """
        Split questions into train and test sets.
        
        Args:
            test_size: Fraction of data for test set (0.0 to 1.0)
            random_seed: Random seed for reproducibility
            stratify_by: Field to stratify by ('category' or 'difficulty')
        
        Returns:
            Tuple of (train_questions, test_questions)
        """
        if not 0.0 < test_size < 1.0:
            raise ValueError("test_size must be between 0.0 and 1.0")
        
        if random_seed is not None:
            random.seed(random_seed)
        
        if stratify_by:
            # Stratified split
            groups = {}
            
            for q in self.questions:
                key = getattr(q, stratify_by, None)
                if key not in groups:
                    groups[key] = []
                groups[key].append(q)
            
            train_questions = []
            test_questions = []
            
            for group_questions in groups.values():
                random.shuffle(group_questions)
                split_idx = int(len(group_questions) * (1 - test_size))
                train_questions.extend(group_questions[:split_idx])
                test_questions.extend(group_questions[split_idx:])
        
        else:
            # Simple random split
            questions_copy = self.questions.copy()
            random.shuffle(questions_copy)
            
            split_idx = int(len(questions_copy) * (1 - test_size))
            train_questions = questions_copy[:split_idx]
            test_questions = questions_copy[split_idx:]
        
        return train_questions, test_questions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the loaded dataset."""
        if not self.questions:
            return {"total": 0}
        
        categories = {}
        difficulties = {}
        
        for q in self.questions:
            if q.category:
                categories[q.category] = categories.get(q.category, 0) + 1
            if q.difficulty:
                difficulties[q.difficulty] = difficulties.get(q.difficulty, 0) + 1
        
        return {
            "total": len(self.questions),
            "categories": categories,
            "difficulties": difficulties,
            "has_ground_truth": sum(1 for q in self.questions if q.ground_truth),
        }
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate loaded questions.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.questions:
            errors.append("No questions loaded")
            return False, errors
        
        seen_ids = set()
        
        for i, q in enumerate(self.questions):
            # Check required fields
            if not q.question:
                errors.append(f"Question {i} has empty question text")
            
            if not q.ground_truth:
                errors.append(f"Question {i} (id={q.id}) has no ground truth")
            
            # Check for duplicate IDs
            if q.id in seen_ids:
                errors.append(f"Duplicate question ID: {q.id}")
            seen_ids.add(q.id)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def export_json(self, filepath: str, questions: Optional[List[Question]] = None):
        """
        Export questions to JSON file.
        
        Args:
            filepath: Output file path
            questions: Questions to export (default: all loaded questions)
        """
        questions = questions or self.questions
        
        data = {
            "questions": [q.to_dict() for q in questions]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def export_csv(self, filepath: str, questions: Optional[List[Question]] = None):
        """
        Export questions to CSV file.
        
        Args:
            filepath: Output file path
            questions: Questions to export (default: all loaded questions)
        """
        questions = questions or self.questions
        
        if not questions:
            return
        
        # Get all possible fields
        fieldnames = ['id', 'question', 'ground_truth', 'category', 'difficulty']
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for q in questions:
                row = q.to_dict()
                # Remove metadata for CSV export
                row.pop('metadata', None)
                writer.writerow(row)
    
    def __len__(self) -> int:
        """Get number of loaded questions."""
        return len(self.questions)
    
    def __getitem__(self, index: int) -> Question:
        """Get question by index."""
        return self.questions[index]
    
    def __repr__(self) -> str:
        return f"DataLoader(questions={len(self.questions)})"


# Example usage
if __name__ == "__main__":
    print("=== Data Loader Test ===\n")
    
    # Initialize loader
    loader = DataLoader()
    
    # Load sample data
    try:
        questions = loader.load("./data/sample_questions.json")
        print(f"✅ Loaded {len(questions)} questions\n")
        
        # Show first question
        print("First Question:")
        q = questions[0]
        print(f"  ID: {q.id}")
        print(f"  Question: {q.question}")
        print(f"  Category: {q.category}")
        print(f"  Difficulty: {q.difficulty}")
        print(f"  Ground Truth: {q.ground_truth[:50]}...\n")
        
        # Statistics
        stats = loader.get_statistics()
        print("Dataset Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Categories: {stats['categories']}")
        print(f"  Difficulties: {stats['difficulties']}\n")
        
        # Validation
        is_valid, errors = loader.validate()
        if is_valid:
            print("✅ Dataset validation passed\n")
        else:
            print(f"❌ Validation errors: {errors}\n")
        
        # Split
        train, test = loader.split_train_test(test_size=0.2, stratify_by='difficulty')
        print(f"Train/Test Split:")
        print(f"  Train: {len(train)} questions")
        print(f"  Test: {len(test)} questions")
        
    except Exception as e:
        print(f"❌ Error: {e}")
