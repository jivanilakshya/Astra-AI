"""
DSPy Signatures for Question Answering Task.
Defines input/output structures for the Q&A system.
"""

import dspy
from typing import Optional


class QuestionAnswering(dspy.Signature):
    """
    Answer a question with a detailed explanation.
    
    This signature defines the task of generating both a concise answer
    and a detailed explanation for educational questions.
    """
    
    # Input field
    question = dspy.InputField(
        desc="The question to be answered. Can be about any topic including science, math, history, etc."
    )
    
    # Output fields
    answer = dspy.OutputField(
        desc="A concise, direct answer to the question (1-3 sentences maximum)"
    )
    
    explanation = dspy.OutputField(
        desc="A detailed explanation that breaks down the reasoning, provides context, and elaborates on the answer (3-5 sentences)"
    )


class QuestionAnsweringWithContext(dspy.Signature):
    """
    Answer a question with provided context/ground truth for reference.
    
    This signature is useful when you want the model to be aware of
    the expected answer format or key facts.
    """
    
    # Input fields
    question = dspy.InputField(
        desc="The question to be answered"
    )
    
    context = dspy.InputField(
        desc="Optional context or reference information that may help answer the question"
    )
    
    # Output fields
    answer = dspy.OutputField(
        desc="A concise, direct answer to the question"
    )
    
    explanation = dspy.OutputField(
        desc="A detailed explanation with step-by-step reasoning"
    )


class AnswerEvaluation(dspy.Signature):
    """
    Evaluate the quality of a generated answer.
    
    This signature is for the Judge Agent to assess answer quality
    across multiple dimensions.
    """
    
    # Input fields
    question = dspy.InputField(
        desc="The original question that was asked"
    )
    
    answer = dspy.InputField(
        desc="The generated answer to evaluate"
    )
    
    explanation = dspy.InputField(
        desc="The explanation provided with the answer"
    )
    
    ground_truth = dspy.InputField(
        desc="The correct answer or reference answer (optional)",
        default=""
    )
    
    # Output fields
    correctness_score = dspy.OutputField(
        desc="Score from 0-10 for factual correctness and accuracy"
    )
    
    clarity_score = dspy.OutputField(
        desc="Score from 0-10 for how clear and understandable the explanation is"
    )
    
    reasoning_score = dspy.OutputField(
        desc="Score from 0-10 for the quality and soundness of logical reasoning"
    )
    
    relevance_score = dspy.OutputField(
        desc="Score from 0-10 for how well the answer addresses the question"
    )
    
    conciseness_score = dspy.OutputField(
        desc="Score from 0-10 for appropriate brevity without being too terse"
    )
    
    feedback = dspy.OutputField(
        desc="Brief constructive feedback on what could be improved (2-3 sentences)"
    )


class PromptOptimization(dspy.Signature):
    """
    Optimize a prompt based on performance feedback.
    
    This signature helps the Optimizer Agent generate improved prompts
    based on evaluation results.
    """
    
    # Input fields
    current_prompt = dspy.InputField(
        desc="The current prompt template being used"
    )
    
    performance_summary = dspy.InputField(
        desc="Summary of performance metrics and common issues from evaluations"
    )
    
    weak_areas = dspy.InputField(
        desc="List of criteria where performance is below threshold (e.g., 'clarity', 'reasoning')"
    )
    
    # Output fields
    optimized_prompt = dspy.OutputField(
        desc="An improved version of the prompt that addresses the identified weaknesses"
    )
    
    rationale = dspy.OutputField(
        desc="Explanation of what changes were made and why they should improve performance"
    )


class SimpleQA(dspy.Signature):
    """Simple question -> answer signature for basic tasks."""
    
    question = dspy.InputField()
    answer = dspy.OutputField()


class QAWithReasoning(dspy.Signature):
    """Question answering with chain-of-thought reasoning."""
    
    question = dspy.InputField(
        desc="Question to answer"
    )
    
    reasoning = dspy.OutputField(
        desc="Step-by-step reasoning process"
    )
    
    answer = dspy.OutputField(
        desc="Final answer based on the reasoning"
    )


# Signature factory functions for dynamic creation

def create_qa_signature(
    include_explanation: bool = True,
    include_context: bool = False,
    include_reasoning: bool = False
) -> type:
    """
    Factory function to create custom Q&A signatures.
    
    Args:
        include_explanation: Include explanation field
        include_context: Include context input field
        include_reasoning: Include reasoning field
    
    Returns:
        Custom DSPy Signature class
    """
    
    if not include_explanation and not include_reasoning:
        return SimpleQA
    
    if include_context:
        return QuestionAnsweringWithContext
    
    if include_reasoning:
        return QAWithReasoning
    
    return QuestionAnswering


# Utility functions

def validate_signature_output(output: dspy.Prediction, signature_class: type) -> bool:
    """
    Validate that output has all required fields from signature.
    
    Args:
        output: DSPy prediction output
        signature_class: The signature class used
    
    Returns:
        True if all required fields present
    """
    sig = signature_class()
    output_fields = [name for name, field in sig.signature.items() 
                     if isinstance(field, dspy.OutputField)]
    
    for field_name in output_fields:
        if not hasattr(output, field_name) or getattr(output, field_name) is None:
            return False
    
    return True


def format_qa_output(prediction: dspy.Prediction) -> dict:
    """
    Format DSPy prediction into standard dictionary.
    
    Args:
        prediction: DSPy prediction object
    
    Returns:
        Dictionary with formatted output
    """
    result = {}
    
    if hasattr(prediction, 'answer'):
        result['answer'] = prediction.answer
    
    if hasattr(prediction, 'explanation'):
        result['explanation'] = prediction.explanation
    
    if hasattr(prediction, 'reasoning'):
        result['reasoning'] = prediction.reasoning
    
    return result


# Example usage and testing
if __name__ == "__main__":
    print("=== DSPy Signatures Test ===\n")
    
    # Test signature creation
    print("1. QuestionAnswering Signature:")
    qa_sig = QuestionAnswering()
    print(f"   Input fields: {[name for name, f in qa_sig.signature.items() if isinstance(f, dspy.InputField)]}")
    print(f"   Output fields: {[name for name, f in qa_sig.signature.items() if isinstance(f, dspy.OutputField)]}")
    
    print("\n2. AnswerEvaluation Signature:")
    eval_sig = AnswerEvaluation()
    print(f"   Input fields: {[name for name, f in eval_sig.signature.items() if isinstance(f, dspy.InputField)]}")
    print(f"   Output fields: {[name for name, f in eval_sig.signature.items() if isinstance(f, dspy.OutputField)]}")
    
    print("\n3. Signature Factory:")
    custom_sig = create_qa_signature(include_explanation=True, include_context=False)
    print(f"   Created: {custom_sig.__name__}")
    
    print("\n✅ All signatures defined successfully!")
