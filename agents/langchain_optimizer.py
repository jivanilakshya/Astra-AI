"""
LangChain Optimizer Agent - Migrated from DSPy
Uses HuggingFace + LangSmith for prompt optimization
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

# LangChain tracing (optional)
langchain_available = True
try:
    import langchain_core
except ImportError:
    langchain_available = False

# LangSmith (optional)
try:
    from langsmith import Client as LangSmithClient
    langsmith_available = True
except ImportError:
    langsmith_available = False

# Use working HuggingFace provider
from agents.huggingface_provider import HuggingFaceProvider

from dotenv import load_dotenv
load_dotenv()


@dataclass
class PromptVersion:
    """Track prompt evolution"""
    version: int
    prompt: str
    score: float
    timestamp: str
    modifications: List[str]


class LangChainOptimizerAgent:
    """
    Optimizer Agent using LangChain + HuggingFace
    
    Analyzes evaluation feedback and generates improved prompts
    """
    
    def __init__(
        self,
        model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct",
        temperature: float = 0.5,
        enable_langsmith: bool = True
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.prompt_history: List[PromptVersion] = []
        self.convergence_threshold = 0.02  # 2% improvement minimum
        
        # Initialize LangSmith
        self.langsmith_enabled = False
        if enable_langsmith and langsmith_available:
            try:
                self.langsmith_client = LangSmithClient()
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_PROJECT"] = "astra-ai-optimizer"
                self.langsmith_enabled = True
                print("LangSmith tracing enabled for Optimizer Agent")
            except Exception:
                pass
        
        # Use working HuggingFace provider directly
        self.provider = HuggingFaceProvider()
        
        # Optimization prompt template
        self.opt_prompt_template = """You are an expert prompt engineer specializing in optimizing LLM prompts.

Your approach:
- Analytical: Identify root causes of poor performance
- Systematic: Apply proven prompt engineering principles
- Conservative: Preserve what works, fix what doesn't
- Testable: Make measurable improvements

Current Prompt:
```
{current_prompt}
```

Performance Analysis:
{performance_analysis}

Weak Areas (< 7.0): {weak_areas}

Common Suggestions from Evaluations:
{suggestions}

Issues Flagged:
{flags}

---

Your Task:
1. Analyze what aspects of the prompt led to poor performance
2. Generate specific modifications to address each weakness
3. Preserve strengths while fixing weaknesses
4. Ensure the new prompt is clear and actionable

Output your response in this structure:

**Analysis:**
<Your analysis of current prompt weaknesses>

**Proposed Modifications:**
1. <Modification 1>
2. <Modification 2>
3. <Modification 3>

**Optimized Prompt:**
```
<Your improved prompt here>
```

**Expected Improvements:**
- <What should improve and why>

Begin your optimization:"""
        
        print(f"LangChain Optimizer Agent initialized")
        print(f"   Model: {model_name}")
    
    def optimize(
        self,
        current_prompt: str,
        evaluations: List[Dict[str, Any]],
        iteration: int = 0
    ) -> Dict[str, Any]:
        """
        Generate optimized prompt based on evaluation feedback
        
        Args:
            current_prompt: Current prompt template
            evaluations: List of evaluation results from Judge
            iteration: Current iteration number
            
        Returns:
            Dict with optimized_prompt, modifications, rationale
        """
        start_time = datetime.now()
        
        try:
            # Analyze evaluations
            analysis = self._analyze_evaluations(evaluations)
            
            # Format optimization prompt
            formatted_prompt = self.opt_prompt_template.format(
                current_prompt=current_prompt,
                performance_analysis=json.dumps(analysis["avg_scores"], indent=2),
                weak_areas=", ".join(analysis["weak_areas"]) if analysis["weak_areas"] else "None",
                suggestions=json.dumps(analysis["common_suggestions"], indent=2),
                flags=json.dumps(analysis["flags"], indent=2)
            )
            
            # Call HuggingFace provider directly
            result = self.provider.generate(
                model_name=self.model_name,
                prompt=formatted_prompt,
                temperature=self.temperature,
                max_tokens=2000
            )
            
            if not result.get("success"):
                raise Exception(result.get("error", "Optimization generation failed"))
            
            response = result["text"]
            
            # Parse optimization result
            optimization = self._parse_optimization(response)
            
            # Track prompt version
            avg_score = analysis["avg_composite_score"]
            self.prompt_history.append(PromptVersion(
                version=len(self.prompt_history) + 1,
                prompt=optimization["optimized_prompt"],
                score=avg_score,
                timestamp=datetime.now().isoformat(),
                modifications=optimization["modifications_made"]
            ))
            
            # Add metadata
            optimization["metadata"] = {
                "optimizer_model": self.model_name,
                "timestamp": datetime.now().isoformat(),
                "latency_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "iteration": iteration,
                "status": "success"
            }
            
            return optimization
            
        except Exception as e:
            print(f"[ERROR] Optimization error: {e}")
            return {
                "optimized_prompt": current_prompt,
                "modifications_made": [],
                "expected_improvements": [],
                "rationale": f"Optimization failed: {str(e)}",
                "metadata": {
                    "optimizer_model": self.model_name,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e)
                }
            }
    
    def _analyze_evaluations(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate evaluation insights"""
        if not evaluations:
            return {
                "avg_scores": {},
                "avg_composite_score": 0.0,
                "weak_areas": [],
                "common_suggestions": [],
                "flags": {}
            }
        
        # Calculate average scores
        avg_scores = {}
        for criterion in ["correctness", "clarity", "reasoning", "relevance", "conciseness"]:
            scores = [e["scores"].get(criterion, 0) for e in evaluations]
            avg_scores[criterion] = {
                "mean": sum(scores) / len(scores) if scores else 0,
                "std": (sum((x - sum(scores)/len(scores))**2 for x in scores) / len(scores))**0.5 if scores else 0,
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0
            }
        
        # Identify weak areas (< 7.0 average)
        weak_areas = [
            criterion for criterion, stats in avg_scores.items()
            if stats["mean"] < 7.0
        ]
        
        # Extract common suggestions
        all_suggestions = []
        for eval in evaluations:
            all_suggestions.extend(eval.get("suggestions", []))
        
        # Count suggestion frequency
        from collections import Counter
        suggestion_counts = Counter(all_suggestions)
        common_suggestions = [
            sugg for sugg, count in suggestion_counts.most_common(5)
        ]
        
        # Extract flags
        all_flags = []
        for eval in evaluations:
            all_flags.extend(eval.get("flags", []))
        flag_counts = Counter(all_flags)
        
        # Calculate average composite score
        composite_scores = [e.get("composite_score", e.get("scores", {}).get("composite", 0)) for e in evaluations]
        avg_composite_score = sum(composite_scores) / len(composite_scores) if composite_scores else 0
        
        return {
            "avg_scores": avg_scores,
            "avg_composite_score": avg_composite_score,
            "weak_areas": weak_areas,
            "common_suggestions": common_suggestions,
            "flags": dict(flag_counts)
        }
    
    def _parse_optimization(self, response: str) -> Dict[str, Any]:
        """Extract optimized prompt and metadata from response"""
        # Extract optimized prompt (in code block)
        optimized_prompt = ""
        if "```" in response:
            parts = response.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Inside code block
                    # Usually the last code block is the prompt
                    optimized_prompt = part.strip()
        
        if not optimized_prompt:
            # Fallback: use entire response
            optimized_prompt = response.strip()
        
        # Extract modifications (look for numbered list)
        modifications = []
        if "Proposed Modifications:" in response:
            mod_section = response.split("Proposed Modifications:")[1]
            if "Optimized Prompt:" in mod_section:
                mod_section = mod_section.split("Optimized Prompt:")[0]
            
            modifications = re.findall(r'\d+\.\s+(.+)', mod_section)
        
        # Extract expected improvements
        improvements = []
        if "Expected Improvements:" in response:
            imp_section = response.split("Expected Improvements:")[1]
            improvements = re.findall(r'-\s+(.+)', imp_section)
        
        # Extract rationale
        rationale = ""
        if "Analysis:" in response:
            analysis_end = response.find("Proposed Modifications:")
            if analysis_end == -1:
                analysis_end = response.find("Optimized Prompt:")
            rationale = response[response.find("Analysis:") + len("Analysis:"):analysis_end].strip()
        
        return {
            "optimized_prompt": optimized_prompt,
            "modifications_made": modifications,
            "expected_improvements": improvements,
            "rationale": rationale,
            "confidence": 0.85
        }
    
    def check_convergence(self, performance_history: List[float]) -> bool:
        """Check if optimization has converged"""
        if len(performance_history) < 3:
            return False
        
        # Check if improvement rate < threshold for last 3 iterations
        recent_improvements = [
            performance_history[i] - performance_history[i-1]
            for i in range(-2, 0)  # Last 2 improvements
        ]
        
        return all(imp < self.convergence_threshold for imp in recent_improvements)
    
    def get_best_prompt(self) -> Optional[PromptVersion]:
        """Get the best performing prompt version"""
        if not self.prompt_history:
            return None
        
        return max(self.prompt_history, key=lambda p: p.score)
    
    def export_history(self, filepath: str):
        """Export prompt evolution history"""
        with open(filepath, 'w') as f:
            json.dump(
                [asdict(p) for p in self.prompt_history],
                f,
                indent=2
            )
        print(f"[OK] Prompt history exported to {filepath}")


# Factory function
def create_langchain_optimizer(
    model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    temperature: float = 0.5,
    enable_langsmith: bool = True
) -> LangChainOptimizerAgent:
    """Create a LangChain Optimizer Agent"""
    return LangChainOptimizerAgent(model_name, temperature, enable_langsmith)


# Test
if __name__ == "__main__":
    print("\n  Testing LangChain Optimizer Agent...\n")
    
    optimizer = create_langchain_optimizer()
    
    # Mock evaluations
    mock_evaluations = [
        {
            "scores": {"correctness": 6, "clarity": 5, "reasoning": 5, "relevance": 7, "conciseness": 6},
            "composite_score": 5.8,
            "suggestions": ["Add more structure", "Be more specific", "Improve clarity"],
            "flags": []
        },
        {
            "scores": {"correctness": 7, "clarity": 6, "reasoning": 5, "relevance": 8, "conciseness": 7},
            "composite_score": 6.5,
            "suggestions": ["Be more specific", "Add examples"],
            "flags": []
        }
    ]
    
    current_prompt = """Answer the following question clearly.

Question: {question}

Answer:"""
    
    # Test optimization
    result = optimizer.optimize(current_prompt, mock_evaluations)
    
    print(f"\n  Optimization Results:")
    print(f"   Modifications: {len(result['modifications_made'])}")
    print(f"   Expected improvements: {len(result['expected_improvements'])}")
    print(f"   Optimized prompt length: {len(result['optimized_prompt'])} chars")
    print(f"   Latency: {result['metadata']['latency_ms']:.0f}ms")
    print(f"\n  Optimizer Agent test complete!")
