"""
Generator Agent Module - Feature 5

Implements the Generator Agent using DSPy modules (Predict, ChainOfThought).
Generates answers to questions with detailed explanations using optimized prompts.

This module uses DSPy signatures defined in Feature 4 and LLM integration from Feature 2.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import dspy
    from dspy import Predict, ChainOfThought
except ImportError:
    dspy = None
    Predict = None
    ChainOfThought = None

from dspy_modules.signatures import (
    QuestionAnswering,
    QuestionAnsweringWithContext,
    SimpleQA,
    QAWithReasoning
)


class GeneratorAgent:
    """
    Generator Agent for producing answers with explanations.
    
    Uses DSPy modules to generate high-quality answers with:
    - Concise direct answers
    - Detailed explanations
    - Step-by-step reasoning (optional)
    - Context integration (optional)
    
    The agent can be configured with different generation strategies:
    - Predict: Direct generation
    - ChainOfThought: Reasoning-based generation
    """
    
    def __init__(
        self,
        use_reasoning: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Initialize Generator Agent.
        
        Args:
            use_reasoning: If True, use ChainOfThought; otherwise use Predict
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens in response
        """
        if dspy is None:
            raise ImportError(
                "DSPy not available. Install with: pip install dspy-ai"
            )
        
        self.use_reasoning = use_reasoning
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize DSPy modules
        if use_reasoning:
            self.qa_module = ChainOfThought(QuestionAnswering)
            self.qa_context_module = ChainOfThought(QuestionAnsweringWithContext)
            self.qa_reasoning_module = ChainOfThought(QAWithReasoning)
        else:
            self.qa_module = Predict(QuestionAnswering)
            self.qa_context_module = Predict(QuestionAnsweringWithContext)
            self.qa_reasoning_module = Predict(QAWithReasoning)
        
        # Simple QA always uses Predict
        self.simple_qa_module = Predict(SimpleQA)
        
        self.generation_count = 0
        self.total_tokens = 0
    
    def generate(
        self,
        question: str,
        context: Optional[str] = None,
        include_reasoning: bool = False
    ) -> Dict[str, Any]:
        """
        Generate answer to a question.
        
        Args:
            question: The question to answer
            context: Optional context information
            include_reasoning: Include step-by-step reasoning
        
        Returns:
            Dictionary with:
                - question: Original question
                - answer: Concise answer
                - explanation: Detailed explanation
                - reasoning: Step-by-step reasoning (if requested)
                - confidence: Estimated confidence (0-1)
                - metadata: Generation metadata
        """
        start_time = time.time()
        
        try:
            # Select appropriate module based on inputs
            if include_reasoning:
                result = self._generate_with_reasoning(question)
            elif context:
                result = self._generate_with_context(question, context)
            else:
                result = self._generate_standard(question)
            
            # Calculate metadata
            latency = (time.time() - start_time) * 1000  # ms
            
            # Estimate confidence based on response completeness
            confidence = self._estimate_confidence(result)
            
            # Build response
            response = {
                "question": question,
                "answer": result.get("answer", ""),
                "explanation": result.get("explanation", ""),
                "confidence": confidence,
                "metadata": {
                    "latency_ms": round(latency, 2),
                    "timestamp": datetime.now().isoformat(),
                    "module_type": "ChainOfThought" if self.use_reasoning else "Predict",
                    "generation_count": self.generation_count
                }
            }
            
            # Add reasoning if available
            if "reasoning" in result:
                response["reasoning"] = result["reasoning"]
            
            # Add context if provided
            if context:
                response["context"] = context
            
            self.generation_count += 1
            
            return response
            
        except Exception as e:
            self.generation_count += 1  # Increment even on error
            return self._handle_error(question, e, time.time() - start_time)
    
    def _generate_standard(self, question: str) -> Dict[str, str]:
        """Generate with standard QuestionAnswering signature."""
        prediction = self.qa_module(question=question)
        
        return {
            "answer": prediction.answer,
            "explanation": prediction.explanation
        }
    
    def _generate_with_context(
        self,
        question: str,
        context: str
    ) -> Dict[str, str]:
        """Generate with context using QuestionAnsweringWithContext."""
        prediction = self.qa_context_module(
            question=question,
            context=context
        )
        
        return {
            "answer": prediction.answer,
            "explanation": prediction.explanation
        }
    
    def _generate_with_reasoning(self, question: str) -> Dict[str, str]:
        """Generate with reasoning using QAWithReasoning."""
        prediction = self.qa_reasoning_module(question=question)
        
        return {
            "answer": prediction.answer,
            "reasoning": prediction.reasoning
        }
    
    def generate_simple(self, question: str) -> str:
        """
        Generate simple answer without explanation.
        
        Args:
            question: The question to answer
        
        Returns:
            Concise answer string
        """
        try:
            prediction = self.simple_qa_module(question=question)
            return prediction.answer
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_batch(
        self,
        questions: List[str],
        contexts: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate answers for multiple questions.
        
        Args:
            questions: List of questions
            contexts: Optional list of contexts (same length as questions)
        
        Returns:
            List of response dictionaries
        """
        results = []
        
        for i, question in enumerate(questions):
            context = contexts[i] if contexts and i < len(contexts) else None
            result = self.generate(question, context=context)
            results.append(result)
        
        return results
    
    def _estimate_confidence(self, result: Dict[str, str]) -> float:
        """
        Estimate confidence based on response characteristics.
        
        Simple heuristic:
        - Has answer: 0.5
        - Has explanation: +0.3
        - Has reasoning: +0.2
        - Answer length > 10 chars: +0.1
        - Explanation length > 50 chars: +0.1
        
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.0
        
        # Check answer
        answer = result.get("answer", "")
        if answer:
            confidence += 0.5
            if len(answer) > 10:
                confidence += 0.1
        
        # Check explanation
        explanation = result.get("explanation", "")
        if explanation:
            confidence += 0.2
            if len(explanation) > 50:
                confidence += 0.1
        
        # Check reasoning
        if "reasoning" in result and result["reasoning"]:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _handle_error(
        self,
        question: str,
        error: Exception,
        elapsed_time: float
    ) -> Dict[str, Any]:
        """Handle generation errors gracefully."""
        return {
            "question": question,
            "answer": "",
            "explanation": f"Generation failed: {str(error)}",
            "confidence": 0.0,
            "error": str(error),
            "metadata": {
                "latency_ms": round(elapsed_time * 1000, 2),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get generator statistics.
        
        Returns:
            Dictionary with generation stats
        """
        return {
            "total_generations": self.generation_count,
            "total_tokens": self.total_tokens,
            "use_reasoning": self.use_reasoning,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    def reset_stats(self):
        """Reset generation statistics."""
        self.generation_count = 0
        self.total_tokens = 0


def create_generator(
    use_reasoning: bool = True,
    temperature: float = 0.7,
    max_tokens: int = 500
) -> GeneratorAgent:
    """
    Factory function to create a configured Generator Agent.
    
    Args:
        use_reasoning: Use ChainOfThought vs Predict
        temperature: Sampling temperature
        max_tokens: Maximum tokens
    
    Returns:
        Configured GeneratorAgent instance
    """
    return GeneratorAgent(
        use_reasoning=use_reasoning,
        temperature=temperature,
        max_tokens=max_tokens
    )


# Example usage
if __name__ == "__main__":
    from models.dspy_integration import configure_dspy
    
    print("="*60)
    print("Generator Agent Example - Feature 5")
    print("="*60)
    
    # Configure DSPy
    try:
        configure_dspy()
        print("\n✅ DSPy configured")
    except Exception as e:
        print(f"\n⚠️  DSPy configuration skipped: {e}")
        print("   (LLM may not be available for actual generation)")
    
    # Create generator
    generator = create_generator(use_reasoning=True)
    print(f"✅ Created Generator (ChainOfThought mode)")
    
    # Test question
    question = "What is photosynthesis?"
    print(f"\n📝 Question: {question}")
    
    # Note: This will fail without a running LLM
    print("\n⚠️  Actual generation requires Ollama running")
    print("   Start with: ollama serve")
    print("   Then: ollama pull llama3.1")
    
    print("\n" + "="*60)
