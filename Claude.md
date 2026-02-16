# Claude Integration Guide

## Overview

This document provides comprehensive guidance on integrating Claude (Anthropic's LLM) into the self-improving LLM system as an alternative or complement to OpenAI models.

---

## 1. Why Claude for This Project?

### Advantages

**Strong Reasoning Capabilities:**
- Excellent for explanation generation (Generator Agent)
- Superior logical analysis (Judge Agent)
- Thoughtful prompt refinement (Optimizer Agent)

**Constitutional AI Training:**
- Better at following complex evaluation criteria
- More reliable for structured output
- Reduced bias in subjective assessments

**Long Context Window:**
- Claude 3: Up to 200K tokens
- Handles extensive prompt templates
- Can process full conversation history

**Lower Hallucination Rate:**
- Critical for Judge Agent reliability
- Reduces false confidence in evaluations
- Better fact-checking capabilities

**Transparent Reasoning:**
- Shows work in evaluations
- Explains optimization decisions
- Provides clear justifications

### Potential Challenges

**API Differences:**
- Different message format from OpenAI
- Requires adapter pattern
- Rate limits vary

**Cost Considerations:**
- Pricing structure differs
- Token counting methods vary
- May be more expensive for high-volume use

**Model Selection:**
- Multiple Claude versions (Haiku, Sonnet, Opus)
- Need to balance cost vs. capability
- Different models for different agents

---

## 2. Claude API Integration

### Installation

```bash
pip install anthropic
```

### Basic Setup

```python
import anthropic
import os

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)
```

### Message Format

Claude uses a different message structure:

```python
# OpenAI format
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
]

# Claude format (no separate system role)
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system="You are a helpful assistant.",  # System prompt separate
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
```

### API Parameters

```python
# Complete parameter set
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    temperature=0.7,
    top_p=0.9,
    top_k=40,  # Unique to Claude
    system="System prompt here",
    messages=[...],
    stop_sequences=["END"],  # Optional
    metadata={  # Optional
        "user_id": "user123"
    }
)
```

---

## 3. Agent Implementation with Claude

### 3.1 Generator Agent (Claude Version)

```python
class ClaudeGeneratorAgent:
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022"):
        self.model = model_name
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        
    def generate(self, question: str, prompt_template: str) -> dict:
        """Generate answer using Claude"""
        
        # Format the prompt
        full_prompt = prompt_template.format(question=question)
        
        # Call Claude API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.7,
            system="You are an expert educator providing clear, accurate answers with detailed explanations.",
            messages=[
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        )
        
        # Extract response
        response_text = message.content[0].text
        
        # Parse answer and explanation
        answer, explanation = self._parse_response(response_text)
        
        return {
            "question": question,
            "answer": answer,
            "explanation": explanation,
            "confidence": self._estimate_confidence(message),
            "metadata": {
                "model": self.model,
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "stop_reason": message.stop_reason,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _parse_response(self, text: str) -> Tuple[str, str]:
        """Extract answer and explanation from response"""
        # Expect format: Answer: ... \n\n Explanation: ...
        if "Answer:" in text and "Explanation:" in text:
            parts = text.split("Explanation:")
            answer = parts[0].replace("Answer:", "").strip()
            explanation = parts[1].strip()
            return answer, explanation
        else:
            # Fallback: treat entire response as answer
            return text, ""
    
    def _estimate_confidence(self, message) -> float:
        """Estimate confidence from response characteristics"""
        # Claude doesn't provide explicit confidence
        # Use stop_reason and response completeness as proxy
        if message.stop_reason == "end_turn":
            return 0.9
        elif message.stop_reason == "max_tokens":
            return 0.7
        else:
            return 0.8
```

### 3.2 Judge Agent (Claude Version)

```python
class ClaudeJudgeAgent:
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022"):
        self.model = model_name
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.criteria_weights = {
            "correctness": 0.40,
            "clarity": 0.20,
            "reasoning": 0.20,
            "relevance": 0.10,
            "conciseness": 0.10
        }
    
    def evaluate(self, question: str, answer: str, 
                 explanation: str, ground_truth: str = None) -> dict:
        """Evaluate using Claude's reasoning capabilities"""
        
        # Build evaluation prompt
        eval_prompt = self._build_evaluation_prompt(
            question, answer, explanation, ground_truth
        )
        
        # Call Claude with structured output request
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            temperature=0.3,  # Lower for consistency
            system="""You are an expert evaluator with deep expertise in assessing educational content quality. 
Your evaluations must be:
- Objective and evidence-based
- Consistent across similar responses
- Detailed in justification
- Calibrated against high standards

You must output valid JSON following the exact schema provided.""",
            messages=[
                {
                    "role": "user",
                    "content": eval_prompt
                }
            ]
        )
        
        # Parse JSON response
        response_text = message.content[0].text
        evaluation = self._parse_evaluation(response_text)
        
        # Add metadata
        evaluation["metadata"] = {
            "judge_model": self.model,
            "timestamp": datetime.now().isoformat(),
            "tokens_used": message.usage.input_tokens + message.usage.output_tokens,
            "confidence": 0.9 if message.stop_reason == "end_turn" else 0.7
        }
        
        return evaluation
    
    def _build_evaluation_prompt(self, question: str, answer: str,
                                  explanation: str, ground_truth: str) -> str:
        """Construct detailed evaluation prompt"""
        
        prompt = f"""Evaluate the following AI-generated response:

**Question:** {question}

**Generated Answer:** {answer}

**Explanation:** {explanation}

**Ground Truth (if available):** {ground_truth or "Not provided"}

---

**Evaluation Criteria (1-10 scale):**

1. **CORRECTNESS** (Weight: 40%)
   - Is the answer factually accurate?
   - Does it align with the ground truth?
   - Are there any errors or misconceptions?
   
2. **CLARITY** (Weight: 20%)
   - Is the explanation easy to understand?
   - Is the language appropriate and accessible?
   - Is the structure logical and well-organized?
   
3. **LOGICAL REASONING** (Weight: 20%)
   - Is the reasoning sound and valid?
   - Are claims properly supported?
   - Are there any logical fallacies?
   
4. **RELEVANCE** (Weight: 10%)
   - Does the response directly address the question?
   - Is all information relevant and on-topic?
   - Are there unnecessary tangents?
   
5. **CONCISENESS** (Weight: 10%)
   - Is the response appropriately concise?
   - Is there unnecessary verbosity?
   - Is important information omitted?

---

**Output Format:**

You must respond with ONLY valid JSON in this exact format:

```json
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
    "<specific improvement suggestion 1>",
    "<specific improvement suggestion 2>",
    "<specific improvement suggestion 3>"
  ],
  "flags": [
    "<any issues like 'potential_hallucination', 'off_topic', 'logical_error', etc.>"
  ]
}}
```

Provide your evaluation now:"""
        
        return prompt
    
    def _parse_evaluation(self, response_text: str) -> dict:
        """Parse JSON evaluation from Claude's response"""
        
        import json
        
        # Extract JSON from response (may have markdown formatting)
        json_text = response_text
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0]
        
        try:
            evaluation = json.loads(json_text.strip())
            
            # Calculate composite score
            evaluation["composite_score"] = sum(
                evaluation["scores"][criterion] * weight
                for criterion, weight in self.criteria_weights.items()
            )
            
            return evaluation
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response text: {response_text}")
            raise ValueError("Judge produced invalid JSON response")
```

### 3.3 Optimizer Agent (Claude Version)

```python
class ClaudeOptimizerAgent:
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022"):
        self.model = model_name
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.history = []
    
    def optimize(self, current_prompt: str, 
                 evaluations: List[dict]) -> dict:
        """Use Claude's reasoning to optimize prompts"""
        
        # Analyze evaluations
        analysis = self._analyze_evaluations(evaluations)
        
        # Build optimization prompt
        opt_prompt = self._build_optimization_prompt(
            current_prompt, analysis
        )
        
        # Call Claude for optimization
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.5,
            system="""You are an expert prompt engineer specializing in optimizing LLM prompts for educational content generation.

Your approach must be:
- Analytical: Identify root causes of poor performance
- Systematic: Apply proven prompt engineering principles
- Conservative: Preserve what works while fixing what doesn't
- Testable: Make changes that can be measured

Focus on:
1. Clarity of instructions
2. Specificity of requirements
3. Structure and formatting guidance
4. Examples when beneficial
5. Constraint specification""",
            messages=[
                {
                    "role": "user",
                    "content": opt_prompt
                }
            ]
        )
        
        # Parse optimization result
        response_text = message.content[0].text
        optimization = self._parse_optimization(response_text)
        
        # Add metadata
        optimization["metadata"] = {
            "optimizer_model": self.model,
            "timestamp": datetime.now().isoformat(),
            "tokens_used": message.usage.input_tokens + message.usage.output_tokens
        }
        
        return optimization
    
    def _analyze_evaluations(self, evaluations: List[dict]) -> dict:
        """Aggregate evaluation insights"""
        
        # Calculate average scores
        avg_scores = {}
        for criterion in ["correctness", "clarity", "reasoning", 
                          "relevance", "conciseness"]:
            scores = [e["scores"][criterion] for e in evaluations]
            avg_scores[criterion] = {
                "mean": np.mean(scores),
                "std": np.std(scores),
                "min": min(scores),
                "max": max(scores)
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
        
        return {
            "avg_scores": avg_scores,
            "weak_areas": weak_areas,
            "common_suggestions": common_suggestions,
            "flags": dict(flag_counts)
        }
    
    def _build_optimization_prompt(self, current_prompt: str,
                                     analysis: dict) -> str:
        """Create optimization instruction prompt"""
        
        prompt = f"""**Current Prompt:**
```
{current_prompt}
```

**Performance Analysis:**

Average Scores:
{json.dumps(analysis["avg_scores"], indent=2)}

Weak Areas (< 7.0): {", ".join(analysis["weak_areas"]) if analysis["weak_areas"] else "None"}

Common Suggestions from Evaluations:
{json.dumps(analysis["common_suggestions"], indent=2)}

Issues Flagged:
{json.dumps(analysis["flags"], indent=2)}

---

**Your Task:**

Analyze the current prompt and performance data to generate an improved version.

**Instructions:**
1. Identify specific weaknesses in the current prompt
2. Propose concrete modifications to address each weakness
3. Ensure modifications target the weak performance areas
4. Preserve strengths (areas with >7.0 scores)
5. Apply prompt engineering best practices

**Output Format:**

Provide your response in the following structure:

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
        
        return prompt
    
    def _parse_optimization(self, response_text: str) -> dict:
        """Extract optimized prompt and metadata"""
        
        # Extract optimized prompt (in code block)
        if "```" in response_text:
            parts = response_text.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Inside code block
                    # Check if this is the prompt (usually the last code block)
                    optimized_prompt = part.strip()
        else:
            # Fallback: entire response
            optimized_prompt = response_text
        
        # Extract modifications (look for numbered list)
        modifications = []
        if "Proposed Modifications:" in response_text:
            mod_section = response_text.split("Proposed Modifications:")[1]
            mod_section = mod_section.split("Optimized Prompt:")[0]
            
            import re
            modifications = re.findall(r'\d+\.\s+(.+)', mod_section)
        
        # Extract expected improvements
        improvements = []
        if "Expected Improvements:" in response_text:
            imp_section = response_text.split("Expected Improvements:")[1]
            improvements = re.findall(r'-\s+(.+)', imp_section)
        
        # Extract rationale
        rationale = ""
        if "Analysis:" in response_text:
            rationale = response_text.split("Analysis:")[1].split("Proposed Modifications:")[0].strip()
        
        return {
            "optimized_prompt": optimized_prompt,
            "modifications_made": modifications,
            "expected_improvements": improvements,
            "rationale": rationale,
            "confidence": 0.85
        }
```

---

## 4. Model Selection Strategy

### Recommended Models per Agent

**Generator Agent:**
- **Claude 3 Haiku**: Fast, cost-effective for simple Q&A
- **Claude 3.5 Sonnet**: Best balance for complex explanations
- **Claude 3 Opus**: Maximum quality for critical applications

**Judge Agent:**
- **Claude 3.5 Sonnet**: Recommended - strong reasoning + cost balance
- **Claude 3 Opus**: For highest evaluation quality

**Optimizer Agent:**
- **Claude 3.5 Sonnet**: Recommended - excellent prompt engineering
- **Claude 3 Opus**: For complex optimization strategies

### Cost-Performance Trade-offs

| Model | Input Cost (per 1M tokens) | Output Cost (per 1M tokens) | Speed | Use Case |
|-------|---------------------------|----------------------------|-------|----------|
| Haiku | $0.25 | $1.25 | Fast | High-volume generation |
| Sonnet 3.5 | $3.00 | $15.00 | Medium | Default for all agents |
| Opus 3 | $15.00 | $75.00 | Slower | Premium quality only |

**Estimated Cost per Iteration (10 questions):**
- All Haiku: ~$0.05
- All Sonnet: ~$0.30
- All Opus: ~$1.50
- Mixed (Haiku Gen, Sonnet Judge/Opt): ~$0.15

---

## 5. Hybrid OpenAI + Claude Architecture

### Strategy: Use Both APIs

```python
class HybridGeneratorAgent:
    """Use different models for different purposes"""
    
    def __init__(self):
        self.claude = ClaudeGeneratorAgent("claude-3-5-sonnet-20241022")
        self.openai = OpenAIGeneratorAgent("gpt-4")
        
    def generate(self, question: str, prompt: str, 
                 prefer_claude: bool = True) -> dict:
        """Choose model based on preference or task type"""
        
        if prefer_claude:
            try:
                return self.claude.generate(question, prompt)
            except Exception as e:
                print(f"Claude failed, falling back to OpenAI: {e}")
                return self.openai.generate(question, prompt)
        else:
            return self.openai.generate(question, prompt)

class HybridJudgeAgent:
    """Cross-validate with multiple judges"""
    
    def __init__(self):
        self.claude_judge = ClaudeJudgeAgent()
        self.openai_judge = OpenAIJudgeAgent()
        
    def evaluate_with_ensemble(self, question: str, answer: str,
                                explanation: str, ground_truth: str = None) -> dict:
        """Get evaluations from both models and aggregate"""
        
        claude_eval = self.claude_judge.evaluate(
            question, answer, explanation, ground_truth
        )
        
        openai_eval = self.openai_judge.evaluate(
            question, answer, explanation, ground_truth
        )
        
        # Average scores
        ensemble_scores = {}
        for criterion in claude_eval["scores"]:
            ensemble_scores[criterion] = (
                claude_eval["scores"][criterion] + 
                openai_eval["scores"][criterion]
            ) / 2
        
        # Combine feedback
        ensemble_eval = {
            "scores": ensemble_scores,
            "composite_score": sum(
                ensemble_scores[c] * w 
                for c, w in self.claude_judge.criteria_weights.items()
            ),
            "feedback": {
                "claude": claude_eval["feedback"],
                "openai": openai_eval["feedback"]
            },
            "suggestions": list(set(
                claude_eval.get("suggestions", []) + 
                openai_eval.get("suggestions", [])
            )),
            "metadata": {
                "ensemble_method": "average",
                "models": ["claude-3-5-sonnet", "gpt-4"]
            }
        }
        
        return ensemble_eval
```

---

## 6. Prompt Engineering for Claude

### Best Practices

**1. Use Clear XML Tags:**
```xml
<system>
You are an expert educator.
</system>

<task>
Answer the following question with detailed explanation.
</task>

<question>
{question}
</question>

<requirements>
- Be accurate
- Explain step-by-step
- Use simple language
</requirements>
```

**2. Be Explicit About Output Format:**
```
Respond in exactly this format:

Answer: [Your concise answer here]

Explanation: [Your detailed explanation here]
```

**3. Use Examples (Few-Shot):**
```
Example 1:
Question: What is gravity?
Answer: Gravity is the force that attracts objects with mass toward each other.
Explanation: Gravity is one of the four fundamental forces...

Example 2:
Question: Why do leaves change color?
Answer: Leaves change color due to breakdown of chlorophyll...
Explanation: During summer, chlorophyll production...

Now answer this question:
Question: {question}
```

**4. Constitutional AI Alignment:**
```
Before answering, consider:
- Is this information accurate and verifiable?
- Is my explanation clear for the intended audience?
- Have I avoided harmful or misleading content?
- Am I being appropriately concise?

Then provide your answer.
```

---

## 7. Error Handling & Rate Limits

### Claude-Specific Error Handling

```python
import anthropic
from anthropic import APIError, APITimeoutError, RateLimitError

class ClaudeAgentWithRetry:
    def __init__(self, model_name: str, max_retries: int = 3):
        self.model = model_name
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.max_retries = max_retries
    
    def call_with_retry(self, messages: List[dict], **kwargs) -> str:
        """Call Claude API with exponential backoff"""
        
        for attempt in range(self.max_retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
                return message.content[0].text
                
            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
                    
            except APITimeoutError as e:
                if attempt < self.max_retries - 1:
                    print(f"Timeout, retrying (attempt {attempt + 1})...")
                    time.sleep(1)
                else:
                    raise
                    
            except APIError as e:
                print(f"API error: {e}")
                raise
        
        raise Exception("Max retries exceeded")
```

### Rate Limits (as of 2024)

**Claude 3 Models:**
- Requests per minute: 50-1000 (tier-dependent)
- Tokens per minute: 40K-400K (tier-dependent)
- Tokens per day: 5M-50M (tier-dependent)

**Mitigation:**
- Implement request queuing
- Use exponential backoff
- Monitor usage with analytics agent
- Consider batch processing

---

## 8. Testing & Validation

### Claude-Specific Tests

```python
import pytest

def test_claude_generator_format():
    """Test Claude generator output format"""
    agent = ClaudeGeneratorAgent()
    result = agent.generate(
        "What is 2+2?",
        "Answer the question. Question: {question}"
    )
    
    assert "answer" in result
    assert "explanation" in result
    assert "metadata" in result
    assert result["metadata"]["model"].startswith("claude")

def test_claude_judge_json_validity():
    """Test Claude judge produces valid JSON"""
    agent = ClaudeJudgeAgent()
    evaluation = agent.evaluate(
        question="What is photosynthesis?",
        answer="Process plants use to make food",
        explanation="Plants convert sunlight to energy..."
    )
    
    assert "scores" in evaluation
    assert all(0 <= v <= 10 for v in evaluation["scores"].values())
    assert "composite_score" in evaluation

def test_claude_optimizer_prompt_improvement():
    """Test optimizer generates valid prompt"""
    agent = ClaudeOptimizerAgent()
    
    evaluations = [{
        "scores": {"correctness": 6, "clarity": 5, "reasoning": 5,
                   "relevance": 7, "conciseness": 6},
        "composite_score": 5.8,
        "suggestions": ["Add more structure", "Be more specific"]
    }]
    
    result = agent.optimize("Answer: {question}", evaluations)
    
    assert "optimized_prompt" in result
    assert len(result["optimized_prompt"]) > 0
    assert result["optimized_prompt"] != "Answer: {question}"
```

---

## 9. Performance Comparison: Claude vs OpenAI

### Empirical Benchmarking

```python
class ModelComparison:
    """Compare Claude and OpenAI performance"""
    
    def __init__(self):
        self.claude_gen = ClaudeGeneratorAgent()
        self.openai_gen = OpenAIGeneratorAgent()
        
    def benchmark_generation(self, questions: List[str]) -> dict:
        """Compare generation quality and speed"""
        
        results = {"claude": [], "openai": []}
        
        for question in questions:
            # Claude
            start = time.time()
            claude_output = self.claude_gen.generate(question, PROMPT)
            claude_time = time.time() - start
            results["claude"].append({
                "output": claude_output,
                "latency": claude_time
            })
            
            # OpenAI
            start = time.time()
            openai_output = self.openai_gen.generate(question, PROMPT)
            openai_time = time.time() - start
            results["openai"].append({
                "output": openai_output,
                "latency": openai_time
            })
        
        return results
    
    def compare_metrics(self, results: dict) -> dict:
        """Aggregate comparison metrics"""
        
        claude_latencies = [r["latency"] for r in results["claude"]]
        openai_latencies = [r["latency"] for r in results["openai"]]
        
        return {
            "claude": {
                "avg_latency": np.mean(claude_latencies),
                "median_latency": np.median(claude_latencies)
            },
            "openai": {
                "avg_latency": np.mean(openai_latencies),
                "median_latency": np.median(openai_latencies)
            }
        }
```

**Expected Results (Based on Typical Performance):**

| Metric | Claude 3.5 Sonnet | GPT-4 |
|--------|------------------|-------|
| Avg Latency | 2-4s | 3-5s |
| Explanation Quality | ★★★★★ | ★★★★★ |
| Reasoning Clarity | ★★★★★ | ★★★★☆ |
| Correctness | ★★★★☆ | ★★★★★ |
| Consistency | ★★★★★ | ★★★★☆ |
| Cost (10K tokens) | $0.03 | $0.04-0.06 |

---

## 10. Production Deployment

### Environment Configuration

```bash
# .env file
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Model selection
GENERATOR_MODEL=claude-3-5-sonnet-20241022
JUDGE_MODEL=claude-3-5-sonnet-20241022
OPTIMIZER_MODEL=claude-3-5-sonnet-20241022

# Fallback models
FALLBACK_GENERATOR=gpt-4
FALLBACK_JUDGE=gpt-4
```

### Configuration Manager

```python
import os
from typing import Dict, Any

class ModelConfig:
    """Centralized model configuration"""
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load configuration from environment"""
        
        return {
            "generator": {
                "primary_model": os.getenv("GENERATOR_MODEL", "claude-3-5-sonnet-20241022"),
                "fallback_model": os.getenv("FALLBACK_GENERATOR", "gpt-4"),
                "temperature": 0.7,
                "max_tokens": 500
            },
            "judge": {
                "primary_model": os.getenv("JUDGE_MODEL", "claude-3-5-sonnet-20241022"),
                "fallback_model": os.getenv("FALLBACK_JUDGE", "gpt-4"),
                "temperature": 0.3,
                "max_tokens": 1500
            },
            "optimizer": {
                "primary_model": os.getenv("OPTIMIZER_MODEL", "claude-3-5-sonnet-20241022"),
                "temperature": 0.5,
                "max_tokens": 2000
            }
        }
```

---

## Conclusion

Claude provides excellent capabilities for all three core agents in the self-improving LLM system:

- **Strong reasoning** for explanation generation
- **Reliable evaluation** with Constitutional AI training
- **Thoughtful optimization** with superior prompt engineering

The hybrid approach (Claude + OpenAI) offers the best of both worlds: Claude's reasoning clarity with OpenAI's broad ecosystem support.

**Recommended Configuration:**
- Generator: Claude 3 Haiku (cost-effective) or Claude 3.5 Sonnet (quality)
- Judge: Claude 3.5 Sonnet (optimal balance)
- Optimizer: Claude 3.5 Sonnet (best prompt engineering)
- Fallback: OpenAI GPT-4 for all agents
