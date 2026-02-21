# LangChain/LangGraph Migration Strategy

## Overview

This document outlines the strategy for migrating from **DSPy framework** to **LangChain/LangGraph** for the Astra-AI self-improving LLM system.

---

## Current State (DSPy-Based Architecture)

### What's Using DSPy:

1. **Generator Agent** (`dspy_modules/generator.py`)
   - Uses `dspy.ChainOfThought` signature
   - DSPy's automatic prompt optimization
   - DSPy LM configuration

2. **Teleprompter** (`dspy_modules/teleprompter.py`)
   - `BootstrapFewShot` optimizer
   - `MIPRO` optimizer
   - DSPy compilation and optimization

3. **Core Dependencies:**
   ```python
   import dspy
   from dspy.teleprompt import BootstrapFewShot, MIPRO
   ```

### What's NOT Using DSPy:

- ✅ **Judge Agent** - Uses direct LLM calls
- ✅ **Optimizer Agent** - Uses direct LLM calls
- ✅ **Orchestrator** - Just coordinates agents
- ✅ **Analytics** - Pure data processing
- ✅ **Model Selector** - Configuration management
- ✅ **Data Loader** - File I/O only
- ✅ **CLI Controller** - Interface only

**Finding**: Only 2 components heavily use DSPy (~10% of codebase)

---

## Why Switch to LangChain/LangGraph?

### Advantages:

1. **Industry Standard**
   - More widely adopted in production
   - Larger community and ecosystem
   - Better enterprise tooling

2. **Better Agent Framework**
   - LangGraph for complex workflows
   - Built-in memory management
   - Streaming support

3. **Rich Ecosystem**
   - More integrations (200+ tools)
   - Better vector store support
   - Advanced retrieval strategies

4. **Production-Ready**
   - LangSmith for monitoring
   - LangServe for deployment
   - Better error handling

5. **Developer Experience**
   - More intuitive API
   - Better documentation
   - Familiar patterns (chains, agents)

### Challenges:

1. **Manual Prompt Engineering**
   - LangChain doesn't auto-optimize prompts like DSPy
   - Need to implement optimization logic ourselves
   - More manual tuning required

2. **Migration Effort**
   - Rewrite Generator module
   - Reimplement Teleprompter logic
   - Update Orchestrator integration

3. **Learning Curve**
   - Team needs to learn LangChain concepts
   - Different mental model (chains vs modules)

---

## Migration Plan (Step-by-Step)

### Phase 1: Setup LangChain Infrastructure (Week 1)

**Goal**: Install and configure LangChain without breaking existing system

**Tasks**:
1. Install LangChain packages:
   ```bash
   pip install langchain langchain-openai langchain-anthropic langgraph langsmith
   ```

2. Create LangChain config:
   ```python
   # config/langchain_config.py
   from langchain_openai import ChatOpenAI
   from langchain_anthropic import ChatAnthropic
   
   class LangChainConfig:
       def __init__(self):
           self.openai_llm = ChatOpenAI(model="gpt-4", temperature=0.7)
           self.claude_llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
   ```

3. Keep DSPy as fallback (parallel implementation)

---

### Phase 2: Rewrite Generator Agent (Week 2)

**Goal**: Replace DSPy generator with LangChain equivalent

**Current (DSPy)**:
```python
# dspy_modules/generator.py
import dspy

class QASignature(dspy.Signature):
    question = dspy.InputField(desc="Question to answer")
    answer = dspy.OutputField(desc="Concise answer")
    explanation = dspy.OutputField(desc="Detailed explanation")

class GeneratorAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generator = dspy.ChainOfThought(QASignature)
    
    def forward(self, question):
        return self.generator(question=question)
```

**New (LangChain)**:
```python
# langchain_modules/generator.py
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class QAOutput(BaseModel):
    answer: str = Field(description="Concise answer to the question")
    explanation: str = Field(description="Detailed step-by-step explanation")

class GeneratorAgent:
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.7)
        self.parser = PydanticOutputParser(pydantic_object=QAOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert educator providing clear, accurate answers with detailed explanations."),
            ("human", """Question: {question}

{format_instructions}

Answer the question with a concise answer and detailed explanation.""")
        ])
        
        self.chain = self.prompt | self.llm | self.parser
    
    def generate(self, question: str) -> dict:
        result = self.chain.invoke({
            "question": question,
            "format_instructions": self.parser.get_format_instructions()
        })
        
        return {
            "question": question,
            "answer": result.answer,
            "explanation": result.explanation,
            "confidence": 0.9
        }
```

**Migration Steps**:
1. Create `langchain_modules/` directory
2. Implement `GeneratorAgent` with LangChain
3. Add tests: `tests/test_langchain_generator.py`
4. Update orchestrator to support both (feature flag)

---

### Phase 3: Replace Teleprompter with Custom Optimizer (Week 3-4)

**Challenge**: DSPy's Teleprompter auto-optimizes prompts. LangChain doesn't have this.

**Solution**: Implement custom prompt optimization using LLM-as-Optimizer

**New Implementation**:
```python
# langchain_modules/prompt_optimizer.py
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List, Dict

class PromptOptimizer:
    """
    Custom prompt optimizer using LLM-as-Optimizer pattern.
    Replaces DSPy's BootstrapFewShot/MIPRO.
    """
    
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(model="gpt-4", temperature=0.5)
        self.optimization_history = []
        
    def optimize_prompt(
        self,
        current_prompt: str,
        evaluations: List[Dict],
        few_shot_examples: List[Dict] = None
    ) -> str:
        """
        Optimize prompt based on evaluation feedback.
        
        Similar to DSPy's compilation but using LLM-driven optimization.
        """
        
        # Analyze weak areas
        weak_criteria = self._analyze_performance(evaluations)
        
        # Extract suggestions
        suggestions = self._extract_suggestions(evaluations)
        
        # Build optimization prompt
        opt_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert prompt engineer. 
Analyze the current prompt and evaluation feedback to generate an improved version."""),
            ("human", """
Current Prompt:
{current_prompt}

Performance Issues:
{weak_criteria}

Suggestions from Evaluations:
{suggestions}

Few-Shot Examples (if provided):
{examples}

Generate an optimized prompt that addresses these issues.
""")
        ])
        
        optimized = self.llm.invoke(opt_prompt.format_messages(
            current_prompt=current_prompt,
            weak_criteria=weak_criteria,
            suggestions=suggestions,
            examples=few_shot_examples or "None provided"
        ))
        
        return optimized.content
    
    def add_few_shot_examples(
        self,
        prompt_template: ChatPromptTemplate,
        examples: List[Dict]
    ) -> ChatPromptTemplate:
        """
        Add few-shot examples to prompt (replaces BootstrapFewShot).
        """
        
        few_shot_messages = []
        for ex in examples:
            few_shot_messages.append(("human", ex["question"]))
            few_shot_messages.append(("ai", f"Answer: {ex['answer']}\nExplanation: {ex['explanation']}"))
        
        # Insert few-shot examples before the main query
        new_messages = (
            prompt_template.messages[:1] +  # System message
            few_shot_messages +  # Few-shot examples
            prompt_template.messages[1:]  # User query
        )
        
        return ChatPromptTemplate.from_messages(new_messages)
```

---

### Phase 4: Integrate LangGraph for Workflow (Week 5)

**Goal**: Use LangGraph for the orchestration loop

**Why LangGraph?**
- Better handles cyclical workflows (Generator → Judge → Optimizer loop)
- Built-in state management
- Visual workflow representation
- Conditional routing

**Implementation**:
```python
# langchain_modules/optimization_graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict

class OptimizationState(TypedDict):
    questions: List[str]
    current_prompt: str
    iteration: int
    scores: List[float]
    evaluations: List[Dict]
    converged: bool
    max_iterations: int

def create_optimization_graph():
    """Create LangGraph workflow for optimization loop"""
    
    workflow = StateGraph(OptimizationState)
    
    # Add nodes
    workflow.add_node("generate", generate_answers_node)
    workflow.add_node("evaluate", evaluate_answers_node)
    workflow.add_node("optimize", optimize_prompt_node)
    workflow.add_node("check_convergence", check_convergence_node)
    
    # Define edges
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", "evaluate")
    workflow.add_edge("evaluate", "check_convergence")
    
    # Conditional routing
    workflow.add_conditional_edges(
        "check_convergence",
        should_continue,
        {
            "continue": "optimize",
            "end": END
        }
    )
    workflow.add_edge("optimize", "generate")
    
    return workflow.compile()

def generate_answers_node(state: OptimizationState):
    """Generate answers using current prompt"""
    generator = GeneratorAgent()
    results = [generator.generate(q) for q in state["questions"]]
    return {"generation_results": results}

def evaluate_answers_node(state: OptimizationState):
    """Evaluate generated answers"""
    judge = JudgeAgent()
    evaluations = [judge.evaluate(r) for r in state["generation_results"]]
    scores = [e["composite_score"] for e in evaluations]
    return {"evaluations": evaluations, "scores": scores}

def optimize_prompt_node(state: OptimizationState):
    """Optimize prompt based on feedback"""
    optimizer = PromptOptimizer()
    new_prompt = optimizer.optimize_prompt(
        state["current_prompt"],
        state["evaluations"]
    )
    return {
        "current_prompt": new_prompt,
        "iteration": state["iteration"] + 1
    }

def should_continue(state: OptimizationState):
    """Decide whether to continue optimization"""
    if state["iteration"] >= state["max_iterations"]:
        return "end"
    if state["scores"][-1] >= 8.5:  # Convergence threshold
        return "end"
    return "continue"
```

**Usage**:
```python
# Running optimization with LangGraph
graph = create_optimization_graph()

result = graph.invoke({
    "questions": ["What is AI?", "What is ML?"],
    "current_prompt": "Answer the question clearly.",
    "iteration": 0,
    "max_iterations": 10,
    "converged": False
})
```

---

### Phase 5: Update Orchestrator Integration (Week 6)

**Goal**: Update orchestrator to use LangChain/LangGraph instead of DSPy

**Changes**:
```python
# agents/orchestrator.py (updated)

# OLD (DSPy)
from dspy_modules.generator import GeneratorAgent

# NEW (LangChain)
from langchain_modules.generator import GeneratorAgent
from langchain_modules.optimization_graph import create_optimization_graph

class OrchestratorAgent:
    def __init__(self, use_langchain=True):  # Feature flag
        if use_langchain:
            self.generator = GeneratorAgent()  # LangChain version
            self.graph = create_optimization_graph()
        else:
            # Keep DSPy fallback
            pass
```

---

### Phase 6: Testing & Validation (Week 7)

**Tasks**:
1. Comprehensive testing:
   ```bash
   pytest tests/langchain/ -v
   ```

2. Performance comparison:
   - DSPy vs LangChain quality
   - Speed benchmarks
   - Cost comparison

3. Feature parity check:
   - All DSPy features working in LangChain?
   - Edge cases handled?

4. Integration tests:
   - End-to-end workflow
   - Error handling
   - Model switching

---

### Phase 7: Deprecate DSPy & Cleanup (Week 8)

**Tasks**:
1. Remove DSPy dependencies:
   ```bash
   pip uninstall dspy-ai
   ```

2. Delete old modules:
   ```
   rm -rf dspy_modules/
   ```

3. Update documentation:
   - README.md
   - Agents.md
   - Architecture diagrams

4. Final testing and deployment

---

## File Structure Changes

### Before (DSPy):
```
Astra AI/
├── dspy_modules/
│   ├── __init__.py
│   ├── generator.py       # DSPy ChainOfThought
│   ├── teleprompter.py    # DSPy optimizers
│   └── signatures.py      # DSPy signatures
├── agents/
│   ├── judge.py           # Direct LLM
│   ├── optimizer.py       # Direct LLM
│   └── orchestrator.py    # Uses dspy_modules
```

### After (LangChain):
```
Astra AI/
├── langchain_modules/
│   ├── __init__.py
│   ├── generator.py       # LangChain LCEL chains
│   ├── prompt_optimizer.py # Custom optimizer
│   ├── optimization_graph.py # LangGraph workflow
│   └── schemas.py         # Pydantic models
├── agents/
│   ├── judge.py           # Could use LangChain too
│   ├── optimizer.py       # Could use LangChain too
│   └── orchestrator.py    # Uses langchain_modules
```

---

## Dependencies Update

### Remove:
```
dspy-ai
```

### Add:
```
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0
langgraph>=0.0.20
langsmith>=0.0.70
```

### Update requirements.txt:
```bash
# Remove DSPy
-dspy-ai

# Add LangChain
+langchain>=0.1.0
+langchain-openai>=0.0.5
+langchain-anthropic>=0.1.0
+langgraph>=0.0.20
+langsmith>=0.0.70
```

---

## Configuration Changes

### config/config.yaml:

```yaml
# OLD
framework: "dspy"
dspy:
  lm: "openai/gpt-4"
  teleprompter: "BootstrapFewShot"
  
# NEW
framework: "langchain"
langchain:
  llm_provider: "openai"  # or "anthropic"
  model: "gpt-4"
  temperature: 0.7
  use_langgraph: true
  langsmith:
    enabled: true
    project: "astra-ai-optimization"
```

---

## Key Differences: DSPy vs LangChain

| Feature | DSPy | LangChain | Impact |
|---------|------|-----------|--------|
| **Prompt Optimization** | Automatic (BootstrapFewShot, MIPRO) | Manual (need custom optimizer) | More work, more control |
| **Workflow Management** | Modules & Signatures | Chains & LangGraph | Better for complex workflows |
| **Monitoring** | Basic | LangSmith (production-ready) | Better observability |
| **Ecosystem** | Smaller, newer | Large, mature | More integrations |
| **Learning Curve** | Steeper (signatures, teleprompters) | Gentler (chains familiar) | Easier onboarding |
| **Prompt Engineering** | Automated | Manual then automated | Hybrid approach |

---

## Risk Assessment

### Low Risk:
- ✅ Judge Agent (already not using DSPy)
- ✅ Optimizer Agent (already not using DSPy)
- ✅ Analytics (pure Python)
- ✅ CLI (interface only)

### Medium Risk:
- ⚠️ Orchestrator (needs workflow updates)
- ⚠️ Testing suite (need new tests)
- ⚠️ Documentation (major updates)

### High Risk:
- 🔴 Generator (core functionality change)
- 🔴 Teleprompter logic (need custom replacement)
- 🔴 Performance parity (DSPy auto-optimization is powerful)

---

## Rollback Plan

If migration fails, we can quickly rollback:

1. **Keep DSPy version in separate branch**:
   ```bash
   git checkout -b dspy-backup
   ```

2. **Feature flag for switching**:
   ```python
   USE_LANGCHAIN = os.getenv("USE_LANGCHAIN", "false").lower() == "true"
   ```

3. **Parallel implementation** during migration (both work)

---

## Cost-Benefit Analysis

### Benefits:
- ✅ Industry-standard framework
- ✅ Better production tooling (LangSmith)
- ✅ Larger ecosystem and community
- ✅ Better workflow management (LangGraph)
- ✅ Easier team onboarding
- ✅ More flexible and extensible

### Costs:
- ❌ 6-8 weeks migration effort
- ❌ Need to build custom prompt optimizer
- ❌ Potential performance regression
- ❌ Testing and validation overhead
- ❌ Documentation updates
- ❌ Team retraining

### Recommendation:
**Proceed with migration** if:
1. You plan to scale to production
2. You need better monitoring/observability
3. You want more ecosystem integrations
4. You have 6-8 weeks for migration

**Stay with DSPy** if:
1. Current system meets all needs
2. Automatic prompt optimization is critical
3. Time to production < 2 months
4. Small team, research-focused

---

## Next Steps (Immediate Actions)

1. **Decision Point**: Confirm you want to migrate (discuss with team)

2. **If YES, proceed**:
   ```bash
   # Install LangChain alongside DSPy (don't remove yet)
   pip install langchain langchain-openai langchain-anthropic langgraph
   
   # Create new directory
   mkdir langchain_modules
   
   # Start with Generator rewrite
   ```

3. **If NO, continue with DSPy**:
   - Fix current display issues
   - Enhance developer output
   - Optimize DSPy configurations

---

## Questions to Answer Before Migration

1. **Timeline**: Do you have 6-8 weeks for this migration?
2. **Priority**: Is this more important than frontend development?
3. **Resources**: Who will work on this? How many developers?
4. **Production**: When do you need this in production?
5. **Features**: Are there LangChain-specific features you need?
6. **Monitoring**: Do you need LangSmith's advanced monitoring?

---

## My Recommendation

Given your situation:

### Option A: **Hybrid Approach** (RECOMMENDED for now)
- **Keep DSPy** for Generator & Teleprompter (it's working!)
- **Add LangChain** for new features (Judge/Optimizer enhancement)
- **Use LangGraph** for workflow visualization
- **Gradual migration** over time (low risk)

### Option B: **Full Migration** (if you have time)
- 6-8 weeks dedicated effort
- Better long-term architecture
- Production-ready monitoring
- More flexibility

### Option C: **Status Quo** (fix current issues first)
- **Fix display issues FIRST** (show real data!)
- Enhance developer output
- **Then decide** on framework after frontend is done

---

## Let's Discuss

Before we start migrating, let me:
1. ✅ **Fix the immediate display issues** (show real prompts, model names, intermediate results)
2. ✅ **Show you what the enhanced output looks like**
3. ❓ **Then you can decide**: Migrate now vs. later vs. never

**What do you think? Should I**:
- **A)** Fix display issues first, migrate later?
- **B)** Start migration immediately (6-8 weeks)?
- **C)** Hybrid approach (keep DSPy, add LangChain features)?
