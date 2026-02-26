"""
LangChain Judge Agent - Migrated from DSPy
Uses HuggingFace + LangSmith for observability
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

# LangChain tracing (optional)
langchain_available = True
try:
    import langchain_core
except ImportError:
    langchain_available = False

# LangSmith tracing
try:
    from langsmith import traceable as _ls_traceable
    _LANGSMITH_OK = True
except ImportError:
    _LANGSMITH_OK = False
    def _ls_traceable(*a, **kw):
        def _dec(fn): return fn
        if a and callable(a[0]): return a[0]
        return _dec

# Use working HuggingFace provider
from agents.huggingface_provider import HuggingFaceProvider

from dotenv import load_dotenv
load_dotenv()


class LangChainJudgeAgent:
    """
    Judge Agent using LangChain + HuggingFace + LangSmith
    
    Evaluates LLM responses across 5 criteria:
    - Correctness (40%)
    - Clarity (20%)
    - Reasoning (20%)
    - Relevance (10%)
    - Conciseness (10%)
    """
    
    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        temperature: float = 0.3,
        enable_langsmith: bool = True
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.criteria_weights = {
            "correctness": 0.40,
            "clarity": 0.20,
            "reasoning": 0.20,
            "relevance": 0.10,
            "conciseness": 0.10
        }
        
        # Initialize LangSmith (optional)
        self.langsmith_enabled = enable_langsmith
        if enable_langsmith:
            try:
                from langsmith import Client
                self.langsmith_client = Client()
                os.environ.setdefault("LANGCHAIN_PROJECT", "astra-ai")
                print("  LangSmith tracing enabled for Judge Agent")
            except ImportError:
                print("  [WARN] LangSmith not available")
                self.langsmith_enabled = False
        
        # Use working HuggingFace provider
        self.provider = HuggingFaceProvider()
        
        print(f"  LangChain Judge Agent initialized")
        print(f"   Model: {model_name}")
        print(f"   LangSmith: {'Enabled' if self.langsmith_enabled else 'Disabled'}")
        
        # Store eval prompt template (used for formatting messages)
        self.eval_prompt_template = """You are an expert evaluator assessing AI-generated answers.

Evaluate responses on these criteria (0-10 scale):

1. CORRECTNESS (40% weight): Factual accuracy
2. CLARITY (20% weight): Clear, easy to understand
3. LOGICAL REASONING (20% weight): Sound logic, well-supported
4. RELEVANCE (10% weight): Directly addresses the question
5. CONCISENESS (10% weight): Appropriately brief

Output ONLY valid JSON in this format:
{{
  "scores": {{
    "correctness": <float 0-10>,
    "clarity": <float 0-10>,
    "reasoning": <float 0-10>,
    "relevance": <float 0-10>,
    "conciseness": <float 0-10>
  }},
  "feedback": {{
    "correctness_reason": "<2-3 sentence justification>",
    "clarity_reason": "<2-3 sentence justification>",
    "reasoning_reason": "<2-3 sentence justification>",
    "relevance_reason": "<2-3 sentence justification>",
    "conciseness_reason": "<2-3 sentence justification>"
  }},
  "suggestions": [
    "<specific improvement 1>",
    "<specific improvement 2>",
    "<specific improvement 3>"
  ],
  "flags": ["<potential_issue_1>", "<potential_issue_2>"]
}}

Question: {question}

Answer: {answer}

Explanation: {explanation}

Ground Truth (if available): {ground_truth}

Evaluate this response:"""
    
    def _parse_json_output(self, output: str) -> Dict[str, Any]:
        """Parse JSON from LLM output with robust fallback extraction"""
        text = output.strip()
        
        # Strategy 1: Extract from markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            parts = text.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1 and "{" in part:
                    text = part
                    break
        
        # Strategy 2: Find the outermost JSON object
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            text = text[json_start:json_end]
        
        try:
            result = json.loads(text.strip())
            
            # Validate scores exist and are in range
            if "scores" in result:
                for key in self.criteria_weights:
                    val = result["scores"].get(key, 0)
                    try:
                        val = float(val)
                    except (TypeError, ValueError):
                        val = 0.0
                    result["scores"][key] = max(0.0, min(10.0, val))
            
            # Calculate composite score
            result["composite_score"] = sum(
                result["scores"].get(criterion, 0) * weight
                for criterion, weight in self.criteria_weights.items()
            )
            
            # Ensure required fields
            result.setdefault("feedback", {})
            result.setdefault("suggestions", [])
            result.setdefault("flags", [])
            
            return result
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Regex extraction of individual scores from raw text
        print(f"  [WARN] JSON parse failed, extracting scores from text...")
        scores = {}
        for criterion in self.criteria_weights:
            # Match patterns like "correctness": 7.5  or  correctness: 8  or  Correctness = 7
            pattern = rf'(?i){criterion}["\s]*[:=]\s*(\d+(?:\.\d+)?)'
            match = re.search(pattern, output)
            if match:
                scores[criterion] = max(0.0, min(10.0, float(match.group(1))))
            else:
                scores[criterion] = 5.0  # neutral default, not 0
        
        composite = sum(
            scores.get(c, 5.0) * w for c, w in self.criteria_weights.items()
        )
        
        # Extract suggestions from text
        suggestions = re.findall(r'[-•]\s*(.+?)(?:\n|$)', output)
        
        return {
            "scores": scores,
            "composite_score": composite,
            "feedback": {f"{k}_reason": "Extracted from text" for k in self.criteria_weights},
            "suggestions": suggestions[:3] if suggestions else ["Improve response quality"],
            "flags": ["fallback_text_extraction"]
        }
    
    @_ls_traceable(run_type="chain", name="Judge Evaluate")
    def evaluate(
        self,
        question: str,
        answer: str,
        explanation: str,
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a generated answer with retry on low-confidence results.
        """
        max_attempts = 2
        best_result = None
        
        for attempt in range(max_attempts):
            result = self._single_evaluate(question, answer, explanation, ground_truth)
            
            # If we got a valid score, return immediately
            if result.get("composite_score", 0) > 0.5:
                return result
            
            # If first attempt returned near-zero, retry once
            if attempt == 0 and result.get("composite_score", 0) < 0.5:
                print(f"    [RETRY] Judge returned near-zero score, retrying...")
                best_result = result
                continue
            
            best_result = result
        
        return best_result or result
    
    def _single_evaluate(
        self,
        question: str,
        answer: str,
        explanation: str,
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """Single evaluation attempt."""
        start_time = datetime.now()
        
        try:
            # Format prompt with variables
            formatted_prompt = self.eval_prompt_template.format(
                question=question,
                answer=answer,
                explanation=explanation,
                ground_truth=ground_truth or "Not provided"
            )
            
            # Call HuggingFace provider
            response = self.provider.generate(
                model_name=self.model_name,
                prompt=formatted_prompt,
                temperature=self.temperature,
                max_tokens=800
            )
            
            if not response.get("success"):
                raise Exception(response.get("error", "Generation failed"))
            
            # Parse JSON output
            result = self._parse_json_output(response["text"])
            
            # Add metadata
            result["metadata"] = {
                "judge_model": self.model_name,
                "timestamp": datetime.now().isoformat(),
                "latency_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "status": "success"
            }
            
            return result
            
        except Exception as e:
            print(f"  [ERROR] Judge evaluation error: {e}")
            return {
                "scores": {k: 0.0 for k in self.criteria_weights.keys()},
                "composite_score": 0.0,
                "feedback": {f"{k}_reason": f"Error: {str(e)}" for k in self.criteria_weights.keys()},
                "suggestions": ["Fix evaluation error"],
                "flags": ["evaluation_error"],
                "metadata": {
                    "judge_model": self.model_name,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e)
                }
            }
    
    def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        explanations: List[str],
        ground_truths: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple responses"""
        if ground_truths is None:
            ground_truths = [None] * len(questions)
        
        results = []
        for i, (q, a, e, gt) in enumerate(zip(questions, answers, explanations, ground_truths)):
            print(f"  Evaluating {i+1}/{len(questions)}...")
            result = self.evaluate(q, a, e, gt)
            results.append(result)
        
        return results


# Factory function
def create_langchain_judge(
    model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
    temperature: float = 0.3,
    enable_langsmith: bool = True
) -> LangChainJudgeAgent:
    """Create a LangChain Judge Agent"""
    return LangChainJudgeAgent(model_name, temperature, enable_langsmith)


# Test
if __name__ == "__main__":
    print("\n  Testing LangChain Judge Agent...\n")
    
    judge = create_langchain_judge()
    
    # Test evaluation
    result = judge.evaluate(
        question="What is artificial intelligence?",
        answer="AI is the simulation of human intelligence in machines.",
        explanation="Artificial intelligence involves creating systems that can perform tasks requiring human-like intelligence such as learning, reasoning, and problem-solving.",
        ground_truth="AI refers to computer systems capable of performing tasks that typically require human intelligence."
    )
    
    print(f"\n  Evaluation Results:")
    print(f"   Composite Score: {result['composite_score']:.2f}/10")
    print(f"   Scores: {result['scores']}")
    print(f"   Suggestions: {result.get('suggestions', [])}")
    print(f"   Latency: {result['metadata']['latency_ms']:.0f}ms")
    print(f"\n  Judge Agent test complete!")
