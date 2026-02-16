# Agent Architecture Documentation

## System Overview

This document describes the agent-based architecture for the self-improving LLM system. The system consists of five core agents working in a coordinated closed feedback loop.

---

## 1. Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                        │
│              (Workflow Coordination & Control)               │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  GENERATOR   │───▶│    JUDGE     │───▶│  OPTIMIZER   │
│    AGENT     │    │    AGENT     │    │    AGENT     │
└──────────────┘    └──────────────┘    └──────────────┘
        ▲                   │                   │
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │  ANALYTICS       │
                  │  AGENT           │
                  └──────────────────┘
```

---

## 2. Core Agents

### 2.1 Generator Agent

**Purpose**: Produces answers to questions using dynamically optimized prompts.

**Responsibilities:**
- Accept questions as input
- Apply current prompt template
- Generate answers with explanations
- Return structured responses
- Handle error cases gracefully

**Input Schema:**
```python
{
    "question": str,
    "prompt_template": str,
    "context": Optional[str],
    "temperature": float,
    "max_tokens": int
}
```

**Output Schema:**
```python
{
    "question": str,
    "answer": str,
    "explanation": str,
    "confidence": float,
    "metadata": {
        "model": str,
        "tokens_used": int,
        "latency_ms": float,
        "timestamp": str
    }
}
```

**Key Methods:**

```python
class GeneratorAgent:
    def __init__(self, model_name: str, api_key: str):
        self.model = model_name
        self.client = OpenAI(api_key=api_key)
        
    def generate(self, question: str, prompt_template: str) -> dict:
        """Generate answer using the given prompt template"""
        pass
        
    def apply_prompt(self, question: str, template: str) -> str:
        """Format the prompt with the question"""
        pass
        
    def validate_output(self, output: str) -> bool:
        """Ensure output meets quality constraints"""
        pass
```

**Prompt Template Structure:**
```
{system_instruction}

Task: Answer the following question with a clear explanation.

Question: {question}

Requirements:
- Provide accurate information
- Explain your reasoning step-by-step
- Be clear and concise
- {additional_constraints}

Answer:
```

**Configuration:**
- Model: `gpt-4` or `gpt-3.5-turbo`
- Temperature: `0.7` (balanced creativity/consistency)
- Max Tokens: `500` (sufficient for explanations)
- Top P: `0.9`
- Frequency Penalty: `0.3`

---

### 2.2 Judge Agent

**Purpose**: Evaluates generated answers across multiple quality dimensions.

**Responsibilities:**
- Score answer correctness (objective)
- Evaluate explanation quality (subjective)
- Assess clarity, reasoning, relevance, conciseness
- Provide structured feedback with justifications
- Detect potential issues (hallucinations, biases)

**Input Schema:**
```python
{
    "question": str,
    "generated_answer": str,
    "generated_explanation": str,
    "ground_truth": Optional[str],
    "evaluation_criteria": List[str]
}
```

**Output Schema:**
```python
{
    "scores": {
        "correctness": float,  # 0-10
        "clarity": float,      # 0-10
        "reasoning": float,    # 0-10
        "relevance": float,    # 0-10
        "conciseness": float   # 0-10
    },
    "composite_score": float,  # weighted average
    "feedback": {
        "correctness_reason": str,
        "clarity_reason": str,
        "reasoning_reason": str,
        "relevance_reason": str,
        "conciseness_reason": str
    },
    "suggestions": List[str],
    "flags": List[str],  # e.g., ["potential_hallucination", "off_topic"]
    "metadata": {
        "judge_model": str,
        "timestamp": str,
        "confidence": float
    }
}
```

**Evaluation Criteria:**

1. **Correctness (Objective)**
   - Score: 10 if fully correct, 0 if completely wrong
   - Partial credit for partially correct answers
   - Requires ground truth or factual verification

2. **Clarity (Subjective)**
   - Score: 1-10 based on readability and understandability
   - Criteria: Simple language, logical flow, no jargon overuse
   - Deductions: Ambiguity, poor structure, confusion

3. **Logical Reasoning (Subjective)**
   - Score: 1-10 based on soundness of reasoning
   - Criteria: Valid logic, supported claims, coherent arguments
   - Deductions: Logical fallacies, unsupported leaps, contradictions

4. **Relevance (Subjective)**
   - Score: 1-10 based on alignment with question
   - Criteria: Directly addresses question, stays on topic
   - Deductions: Tangents, irrelevant information, misunderstanding

5. **Conciseness (Subjective)**
   - Score: 1-10 based on efficiency of expression
   - Criteria: No unnecessary verbosity, appropriate length
   - Deductions: Redundancy, excessive elaboration, wordiness

**Composite Score Formula:**
```python
composite_score = (
    0.40 * correctness +
    0.20 * clarity +
    0.20 * reasoning +
    0.10 * relevance +
    0.10 * conciseness
)
```

**Key Methods:**

```python
class JudgeAgent:
    def __init__(self, model_name: str, api_key: str):
        self.model = model_name
        self.client = OpenAI(api_key=api_key)
        self.criteria_weights = {
            "correctness": 0.40,
            "clarity": 0.20,
            "reasoning": 0.20,
            "relevance": 0.10,
            "conciseness": 0.10
        }
        
    def evaluate(self, question: str, answer: str, 
                 explanation: str, ground_truth: str = None) -> dict:
        """Perform multi-criteria evaluation"""
        pass
        
    def score_correctness(self, answer: str, ground_truth: str) -> float:
        """Objective correctness scoring"""
        pass
        
    def score_clarity(self, explanation: str) -> Tuple[float, str]:
        """Subjective clarity scoring with reasoning"""
        pass
        
    def score_reasoning(self, explanation: str) -> Tuple[float, str]:
        """Logical reasoning quality scoring"""
        pass
        
    def calculate_composite(self, scores: dict) -> float:
        """Weighted composite score"""
        pass
        
    def detect_issues(self, answer: str, explanation: str) -> List[str]:
        """Flag potential problems"""
        pass
```

**Judge Prompt Template:**
```
You are an expert evaluator assessing the quality of an AI-generated answer.

Question: {question}
Generated Answer: {answer}
Explanation: {explanation}
Ground Truth: {ground_truth}

Evaluate the response on the following criteria (1-10 scale):

1. CORRECTNESS: Is the answer factually accurate?
2. CLARITY: Is the explanation clear and easy to understand?
3. LOGICAL REASONING: Is the reasoning sound and well-structured?
4. RELEVANCE: Does the response directly address the question?
5. CONCISENESS: Is the response appropriately concise without being terse?

For each criterion, provide:
- A score (1-10)
- A brief justification (2-3 sentences)

Also identify any issues: hallucinations, biases, logical errors, etc.

Output your evaluation in the following JSON format:
{json_schema}
```

**Validation Mechanisms:**
- Cross-check with multiple judge runs (temperature variance)
- Human baseline validation (periodic audits)
- Consistency checks (same question, multiple evaluations)
- Calibration against known good/bad examples

---

### 2.3 Optimizer Agent

**Purpose**: Automatically modifies prompts based on judge feedback to improve performance.

**Responsibilities:**
- Analyze judge feedback and scores
- Generate prompt modifications
- Apply optimization strategies
- Track prompt evolution history
- Detect optimization convergence

**Input Schema:**
```python
{
    "current_prompt": str,
    "evaluation_results": List[dict],  # from Judge
    "performance_history": List[dict],
    "optimization_strategy": str,
    "iteration_number": int
}
```

**Output Schema:**
```python
{
    "optimized_prompt": str,
    "modifications_made": List[str],
    "rationale": str,
    "expected_improvements": List[str],
    "confidence": float,
    "metadata": {
        "strategy_used": str,
        "iteration": int,
        "timestamp": str
    }
}
```

**Optimization Strategies:**

1. **Feedback-Driven Refinement**
   - Extract specific issues from judge feedback
   - Add constraints to address weaknesses
   - Reinforce strengths

2. **Component Addition**
   - Add missing instructions (e.g., "explain step-by-step")
   - Include examples if clarity is low
   - Add formatting requirements

3. **Component Removal**
   - Remove redundant instructions
   - Simplify overly complex prompts
   - Eliminate ineffective constraints

4. **Reordering & Restructuring**
   - Reorganize prompt sections for better flow
   - Emphasize high-priority instructions
   - Improve readability

5. **Constraint Tuning**
   - Adjust specificity levels
   - Balance brevity vs. detail requirements
   - Refine quality expectations

**Optimization Algorithm:**

```python
class OptimizerAgent:
    def __init__(self, model_name: str, api_key: str):
        self.model = model_name
        self.client = OpenAI(api_key=api_key)
        self.history = []
        
    def optimize(self, current_prompt: str, 
                 evaluations: List[dict]) -> dict:
        """Generate optimized prompt based on feedback"""
        
        # 1. Analyze performance patterns
        weak_areas = self._identify_weaknesses(evaluations)
        strong_areas = self._identify_strengths(evaluations)
        
        # 2. Extract actionable feedback
        suggestions = self._extract_suggestions(evaluations)
        
        # 3. Generate modifications
        modifications = self._generate_modifications(
            current_prompt, weak_areas, suggestions
        )
        
        # 4. Apply changes
        new_prompt = self._apply_modifications(
            current_prompt, modifications
        )
        
        # 5. Validate new prompt
        if self._validate_prompt(new_prompt):
            return {
                "optimized_prompt": new_prompt,
                "modifications_made": modifications,
                "rationale": self._generate_rationale(modifications)
            }
        else:
            return self._rollback()
            
    def _identify_weaknesses(self, evaluations: List[dict]) -> List[str]:
        """Find criteria with consistently low scores"""
        pass
        
    def _identify_strengths(self, evaluations: List[dict]) -> List[str]:
        """Find criteria with high scores to preserve"""
        pass
        
    def _extract_suggestions(self, evaluations: List[dict]) -> List[str]:
        """Parse judge feedback for actionable suggestions"""
        pass
        
    def _generate_modifications(self, prompt: str, 
                                 weaknesses: List[str],
                                 suggestions: List[str]) -> List[str]:
        """Create specific prompt changes"""
        pass
        
    def _apply_modifications(self, prompt: str, 
                             modifications: List[str]) -> str:
        """Generate new prompt with changes"""
        pass
        
    def _validate_prompt(self, prompt: str) -> bool:
        """Check if new prompt meets quality standards"""
        pass
        
    def check_convergence(self, history: List[float]) -> bool:
        """Determine if optimization has converged"""
        # Check if improvement rate < threshold for N iterations
        if len(history) < 5:
            return False
            
        recent_improvements = [
            history[i] - history[i-1] for i in range(-4, 0)
        ]
        
        return all(imp < 0.02 for imp in recent_improvements)
```

**Optimizer Prompt Template:**
```
You are an expert prompt engineer. Your task is to improve a prompt based on evaluation feedback.

Current Prompt:
{current_prompt}

Evaluation Results:
{evaluation_summary}

Key Issues Identified:
{weak_areas}

Suggestions from Judge:
{suggestions}

Your task:
1. Analyze what aspects of the prompt led to poor performance
2. Generate specific modifications to address the issues
3. Maintain strengths while fixing weaknesses
4. Ensure the new prompt is clear and actionable

Output a revised prompt that:
- Addresses the clarity issues
- Improves logical reasoning guidance
- Maintains conciseness
- Preserves what's already working well

Revised Prompt:
```

**Convergence Detection:**
- **Performance plateau**: <2% improvement for 3+ iterations
- **Score threshold**: Composite score >8.5/10
- **Diminishing returns**: Optimization cost > improvement value
- **Maximum iterations**: 10-15 iterations hard limit

**Safety Mechanisms:**
- **Rollback capability**: Revert to previous best prompt
- **Overfitting detection**: Test on hold-out set
- **Prompt length limits**: Prevent unbounded growth
- **Sanity checks**: Ensure prompt remains coherent

---

### 2.4 Orchestrator Agent

**Purpose**: Coordinates the entire closed feedback loop and manages workflow execution.

**Responsibilities:**
- Initialize the optimization cycle
- Coordinate agent interactions
- Manage iteration flow
- Handle errors and exceptions
- Enforce stopping criteria
- Aggregate results

**Workflow Control:**

```python
class OrchestratorAgent:
    def __init__(self, generator: GeneratorAgent, 
                 judge: JudgeAgent,
                 optimizer: OptimizerAgent,
                 analytics: AnalyticsAgent):
        self.generator = generator
        self.judge = judge
        self.optimizer = optimizer
        self.analytics = analytics
        self.max_iterations = 10
        self.convergence_threshold = 8.5
        
    def run_optimization_loop(self, 
                              questions: List[str],
                              initial_prompt: str,
                              ground_truths: List[str] = None) -> dict:
        """Execute the full closed feedback loop"""
        
        current_prompt = initial_prompt
        iteration = 0
        performance_history = []
        
        while iteration < self.max_iterations:
            print(f"--- Iteration {iteration + 1} ---")
            
            # Step 1: Generate answers
            outputs = self._generate_batch(questions, current_prompt)
            
            # Step 2: Evaluate outputs
            evaluations = self._evaluate_batch(
                questions, outputs, ground_truths
            )
            
            # Step 3: Log results
            self.analytics.log_iteration(
                iteration, current_prompt, outputs, evaluations
            )
            
            # Step 4: Check convergence
            avg_score = self._calculate_average_score(evaluations)
            performance_history.append(avg_score)
            
            if self._should_stop(performance_history, avg_score):
                print(f"Converged at iteration {iteration + 1}")
                break
            
            # Step 5: Optimize prompt
            optimization_result = self.optimizer.optimize(
                current_prompt, evaluations
            )
            
            current_prompt = optimization_result["optimized_prompt"]
            iteration += 1
        
        # Final results
        return self._compile_results(
            current_prompt, performance_history, iteration
        )
    
    def _generate_batch(self, questions: List[str], 
                        prompt: str) -> List[dict]:
        """Generate answers for all questions"""
        return [
            self.generator.generate(q, prompt) for q in questions
        ]
    
    def _evaluate_batch(self, questions: List[str],
                        outputs: List[dict],
                        ground_truths: List[str]) -> List[dict]:
        """Evaluate all generated outputs"""
        evaluations = []
        for i, output in enumerate(outputs):
            gt = ground_truths[i] if ground_truths else None
            eval_result = self.judge.evaluate(
                questions[i],
                output["answer"],
                output["explanation"],
                gt
            )
            evaluations.append(eval_result)
        return evaluations
    
    def _calculate_average_score(self, 
                                  evaluations: List[dict]) -> float:
        """Calculate mean composite score"""
        scores = [e["composite_score"] for e in evaluations]
        return sum(scores) / len(scores)
    
    def _should_stop(self, history: List[float], 
                     current_score: float) -> bool:
        """Determine if optimization should stop"""
        
        # Threshold reached
        if current_score >= self.convergence_threshold:
            return True
        
        # Convergence detected
        if self.optimizer.check_convergence(history):
            return True
        
        # Performance degradation
        if len(history) > 2 and current_score < history[-2] - 0.5:
            print("Warning: Performance degradation detected")
            return True
        
        return False
    
    def _compile_results(self, final_prompt: str,
                         history: List[float],
                         iterations: int) -> dict:
        """Compile final optimization results"""
        return {
            "final_prompt": final_prompt,
            "initial_score": history[0],
            "final_score": history[-1],
            "improvement": history[-1] - history[0],
            "iterations": iterations,
            "performance_history": history,
            "converged": history[-1] >= self.convergence_threshold
        }
```

**Error Handling:**

```python
def run_optimization_loop_safe(self, questions, initial_prompt):
    """Orchestration with comprehensive error handling"""
    try:
        return self.run_optimization_loop(questions, initial_prompt)
    except GeneratorError as e:
        self.analytics.log_error("generator", e)
        return self._handle_generator_failure()
    except JudgeError as e:
        self.analytics.log_error("judge", e)
        return self._handle_judge_failure()
    except OptimizerError as e:
        self.analytics.log_error("optimizer", e)
        return self._fallback_optimization()
    except Exception as e:
        self.analytics.log_error("orchestrator", e)
        return self._emergency_shutdown()
```

---

### 2.5 Analytics Agent

**Purpose**: Logs data, tracks metrics, and provides insights into system performance.

**Responsibilities:**
- Log all agent interactions
- Track performance metrics over time
- Generate visualizations
- Detect anomalies
- Provide optimization insights
- Export results for analysis

**Data Collection:**

```python
class AnalyticsAgent:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.iteration_logs = []
        self.metrics_history = []
        
    def log_iteration(self, iteration: int, prompt: str,
                      outputs: List[dict],
                      evaluations: List[dict]) -> None:
        """Log complete iteration data"""
        
        log_entry = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "prompt_length": len(prompt),
            "num_questions": len(outputs),
            "outputs": outputs,
            "evaluations": evaluations,
            "metrics": self._calculate_metrics(evaluations)
        }
        
        self.iteration_logs.append(log_entry)
        self._save_log(log_entry)
        
    def _calculate_metrics(self, evaluations: List[dict]) -> dict:
        """Calculate aggregated metrics"""
        
        scores = {
            "correctness": [],
            "clarity": [],
            "reasoning": [],
            "relevance": [],
            "conciseness": [],
            "composite": []
        }
        
        for eval in evaluations:
            for criterion, score in eval["scores"].items():
                scores[criterion].append(score)
            scores["composite"].append(eval["composite_score"])
        
        return {
            criterion: {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": min(values),
                "max": max(values)
            }
            for criterion, values in scores.items()
        }
    
    def generate_report(self) -> dict:
        """Generate comprehensive performance report"""
        
        return {
            "summary": self._generate_summary(),
            "performance_trends": self._analyze_trends(),
            "best_iteration": self._find_best_iteration(),
            "improvement_areas": self._identify_improvements(),
            "anomalies": self._detect_anomalies()
        }
    
    def export_results(self, format: str = "json") -> None:
        """Export logs and metrics"""
        
        if format == "json":
            self._export_json()
        elif format == "csv":
            self._export_csv()
        elif format == "visualization":
            self._generate_plots()
    
    def _generate_plots(self) -> None:
        """Create performance visualization"""
        
        # Performance over iterations
        plt.figure(figsize=(12, 6))
        
        iterations = range(len(self.iteration_logs))
        composite_scores = [
            log["metrics"]["composite"]["mean"] 
            for log in self.iteration_logs
        ]
        
        plt.plot(iterations, composite_scores, marker='o')
        plt.xlabel("Iteration")
        plt.ylabel("Average Composite Score")
        plt.title("Optimization Performance Over Time")
        plt.grid(True)
        plt.savefig(f"{self.storage_path}/performance_plot.png")
```

**Metrics Tracked:**
- Score distributions (all criteria)
- Improvement rates per iteration
- Prompt evolution (length, complexity)
- Agent latencies and costs
- Error rates and types
- Convergence trajectory

**Visualization Outputs:**
- Line plots: Score trends over iterations
- Box plots: Score distributions per criterion
- Heatmaps: Correlation between criteria
- Bar charts: Improvement per optimization strategy

---

## 3. Agent Communication Protocol

### Message Format

```python
class AgentMessage:
    def __init__(self, sender: str, receiver: str, 
                 message_type: str, payload: dict):
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.payload = payload
        self.timestamp = datetime.now().isoformat()
        self.message_id = str(uuid.uuid4())
```

### Message Types

1. **GENERATE_REQUEST**
   - Sender: Orchestrator
   - Receiver: Generator
   - Payload: `{question, prompt_template}`

2. **GENERATE_RESPONSE**
   - Sender: Generator
   - Receiver: Orchestrator
   - Payload: `{answer, explanation, metadata}`

3. **EVALUATE_REQUEST**
   - Sender: Orchestrator
   - Receiver: Judge
   - Payload: `{question, answer, explanation, ground_truth}`

4. **EVALUATE_RESPONSE**
   - Sender: Judge
   - Receiver: Orchestrator
   - Payload: `{scores, feedback, suggestions}`

5. **OPTIMIZE_REQUEST**
   - Sender: Orchestrator
   - Receiver: Optimizer
   - Payload: `{current_prompt, evaluations, history}`

6. **OPTIMIZE_RESPONSE**
   - Sender: Optimizer
   - Receiver: Orchestrator
   - Payload: `{optimized_prompt, modifications, rationale}`

7. **LOG_EVENT**
   - Sender: Any
   - Receiver: Analytics
   - Payload: `{event_type, data}`

---

## 4. Implementation Example

### Complete System Integration

```python
# Initialize all agents
generator = GeneratorAgent(
    model_name="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY")
)

judge = JudgeAgent(
    model_name="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY")
)

optimizer = OptimizerAgent(
    model_name="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY")
)

analytics = AnalyticsAgent(
    storage_path="./logs"
)

orchestrator = OrchestratorAgent(
    generator=generator,
    judge=judge,
    optimizer=optimizer,
    analytics=analytics
)

# Define test questions
questions = [
    "What is photosynthesis?",
    "Explain Newton's first law of motion.",
    "Why is the sky blue?"
]

ground_truths = [
    "Process by which plants convert light into energy",
    "An object remains at rest or in uniform motion unless acted upon",
    "Light scattering by atmospheric particles"
]

# Initial prompt
initial_prompt = """
Answer the following question clearly and concisely.

Question: {question}

Answer:
"""

# Run optimization
results = orchestrator.run_optimization_loop(
    questions=questions,
    initial_prompt=initial_prompt,
    ground_truths=ground_truths
)

# Generate report
report = analytics.generate_report()
print(report)
```

---

## 5. Configuration & Tuning

### Agent Parameters

**Generator:**
```yaml
model: gpt-4
temperature: 0.7
max_tokens: 500
top_p: 0.9
frequency_penalty: 0.3
presence_penalty: 0.0
```

**Judge:**
```yaml
model: gpt-4
temperature: 0.3  # Lower for consistency
max_tokens: 800
criteria_weights:
  correctness: 0.40
  clarity: 0.20
  reasoning: 0.20
  relevance: 0.10
  conciseness: 0.10
```

**Optimizer:**
```yaml
model: gpt-4
temperature: 0.5
max_tokens: 1000
max_iterations: 10
convergence_threshold: 8.5
min_improvement_rate: 0.02
```

**Orchestrator:**
```yaml
max_iterations: 10
convergence_threshold: 8.5
batch_size: 10
parallel_processing: false
error_retry_limit: 3
timeout_seconds: 300
```

---

## 6. Testing & Validation

### Unit Tests

```python
def test_generator_output_format():
    """Test generator produces valid output schema"""
    generator = GeneratorAgent("gpt-3.5-turbo", api_key)
    result = generator.generate("What is 2+2?", basic_prompt)
    assert "answer" in result
    assert "explanation" in result
    assert "metadata" in result

def test_judge_scoring_range():
    """Test judge scores are within valid range"""
    judge = JudgeAgent("gpt-4", api_key)
    evaluation = judge.evaluate(question, answer, explanation)
    for score in evaluation["scores"].values():
        assert 0 <= score <= 10

def test_optimizer_convergence():
    """Test optimizer detects convergence"""
    optimizer = OptimizerAgent("gpt-4", api_key)
    history = [7.0, 7.5, 7.8, 7.9, 7.95]
    assert optimizer.check_convergence(history) == True
```

### Integration Tests

```python
def test_full_optimization_cycle():
    """Test complete feedback loop execution"""
    results = orchestrator.run_optimization_loop(
        questions=test_questions,
        initial_prompt=baseline_prompt
    )
    assert results["final_score"] > results["initial_score"]
    assert results["iterations"] <= 10
```

---

## Conclusion

This agent architecture provides a modular, scalable foundation for the self-improving LLM system. Each agent has clear responsibilities, well-defined interfaces, and robust error handling. The orchestrator ensures smooth coordination while the analytics agent enables comprehensive monitoring and analysis.
