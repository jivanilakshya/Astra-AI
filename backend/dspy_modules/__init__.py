"""DSPy modules - Contains DSPy signatures, generators, and teleprompters."""

from .signatures import (
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

from .generator import (
    GeneratorAgent,
    create_generator
)

from .teleprompter import (
    TeleprompterManager,
    TrainingExample,
    create_teleprompter
)

__all__ = [
    'QuestionAnswering',
    'QuestionAnsweringWithContext',
    'AnswerEvaluation',
    'PromptOptimization',
    'SimpleQA',
    'QAWithReasoning',
    'create_qa_signature',
    'validate_signature_output',
    'format_qa_output',
    'GeneratorAgent',
    'create_generator',
    'TeleprompterManager',
    'TrainingExample',
    'create_teleprompter'
]
