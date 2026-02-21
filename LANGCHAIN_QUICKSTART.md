# LangChain Migration Guide

## 🎯 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_langchain.txt
```

### 2. Configure LangSmith (Optional but Recommended)

Get your free API key from: https://smith.langchain.com

```bash
# Add to your .env file
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=astra-ai
```

### 3. Run the Migrated System

```python
from agents.langgraph_orchestrator import create_langchain_orchestrator

# Create orchestrator (uses LangChain + LangGraph + LangSmith)
orchestrator = create_langchain_orchestrator(
    generator_model="meta-llama/Meta-Llama-3-8B-Instruct",
    judge_model="mistralai/Mistral-7B-Instruct-v0.2",
    optimizer_model="meta-llama/Meta-Llama-3-8B-Instruct",
    max_iterations=5,
    convergence_threshold=8.5,
    enable_langsmith=True  # Enable observability
)

# Run optimization
results = orchestrator.run_optimization(
    questions=[
        "What is artificial intelligence?",
        "Explain machine learning."
    ],
    initial_prompt="""Answer the question clearly.

Question: {question}

Answer:"""
)

# Export results
orchestrator.export_results(results)
```

---

## 📊 What's New

### LangChain Components (Migrated)

1. **Judge Agent** (`agents/langchain_judge.py`)
   - Uses `langchain_huggingface.HuggingFaceEndpoint`
   - LangChain ChatPromptTemplate for evaluation
   - JSON output parsing
   - **LangSmith tracing enabled** 📊

2. **Optimizer Agent** (`agents/langchain_optimizer.py`)
   - Uses LangChain prompts for optimization
   - Tracks prompt evolution history
   - Convergence detection
   - **LangSmith tracing enabled** 📊

3. **Orchestrator** (`agents/langgraph_orchestrator.py`)
   - Uses **LangGraph StateGraph** for workflow
   - State-based execution model
   - Conditional branching (continue/end)
   - **LangSmith tracing for entire workflow** 📊

### Still Using HuggingFace (Not DSPy)

- **Generator**: `agents/huggingface_provider.py` (already working!)
- No DSPy dependency for these components
- Direct HuggingFace Inference API calls

---

## 🔍 LangSmith Observability

When LangSmith is enabled, you get:

1. **Real-time Tracing**
   - See each LLM call in detail
   - View input prompts + outputs
   - Track latency and token usage

2. **Workflow Visualization**
   - See the full optimization loop as a graph
   - Track state transitions
   - Debug failures easily

3. **Performance Monitoring**
   - Compare runs over time
   - Identify bottlenecks
   - Track cost per iteration

4. **Project Organization**
   - Separate traces by agent:
     - `astra-ai-judge` - Judge evaluations
     - `astra-ai-optimizer` - Prompt optimizations
     - `astra-ai-orchestrator` - Full workflow

### View Traces

Go to: https://smith.langchain.com/

Navigate to your project (`astra-ai`) to see all traces.

---

## 🆚 DSPy vs LangChain Comparison

### What Changed

| Component | Before (DSPy) | After (LangChain/LangGraph) |
|-----------|---------------|------------------------------|
| **Judge** | Direct LLM calls | `ChatPromptTemplate` + `HuggingFaceEndpoint` |
| **Optimizer** | Direct LLM calls | `ChatPromptTemplate` + state tracking |
| **Orchestrator** | Simple loop | **LangGraph StateGraph** |
| **Generator** | `dspy.ChainOfThought` | `HuggingFaceProvider` (unchanged) |
| **Observability** | None | **LangSmith full tracing** ✨ |

### What Stayed the Same

- ✅ HuggingFace models (Meta-Llama-3, Mistral-7B)
- ✅ Zero PC load (cloud-based)
- ✅ Zero cost (FREE tier)
- ✅ Multi-criteria evaluation (5 criteria)
- ✅ Prompt optimization logic
- ✅ Convergence detection

### Benefits of Migration

1. **Better Observability** - LangSmith traces every step
2. **Workflow Control** - LangGraph provides structured state management
3. **Industry Standard** - LangChain is more widely adopted
4. **Easier Debugging** - Visual workflow + detailed traces
5. **No DSPy Dependency** - Simpler architecture

---

## 🔧 Architecture

### LangGraph Workflow

```
┌─────────────────────────────────────────────────┐
│                  ENTRY POINT                     │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
          ┌──────────────┐
          │   GENERATE   │ ← HuggingFace Generator
          │   (Node 1)   │   (Meta-Llama-3)
          └──────┬───────┘
                  │
                  ▼
          ┌──────────────┐
          │   EVALUATE   │ ← LangChain Judge
          │   (Node 2)   │   (Mistral-7B)
          └──────┬───────┘
                  │
                  ▼
          ┌──────────────┐
          │   OPTIMIZE   │ ← LangChain Optimizer
          │   (Node 3)   │   (Meta-Llama-3)
          └──────┬───────┘
                  │
                  ▼
        ┌─────────────────┐
        │  Should Continue? │
        │  (Conditional)    │
        └────┬──────────┬──┘
             │          │
      Continue   │      End
       (loop)    │      │
             │   │      ▼
             │   │  ┌──────────┐
             │   │  │ FINALIZE │
             │   │  │ (Node 4) │
             │   │  └────┬─────┘
             │   │       │
             └───┘       ▼
                      [ END ]
```

### State Management

```python
class OptimizationState:
    # Inputs
    questions: List[str]
    current_prompt: str
    iteration: int
    
    # Generated
    generated_outputs: List[Dict]
    
    # Evaluated
    evaluations: List[Dict]
    current_score: float
    
    # Optimized
    optimization_result: Dict
    
    # Tracking
    performance_history: List[float]
    converged: bool
    final_results: Dict
```

---

## 📈 Output You'll Get

### 1. Real AI Responses

```
🤖 Iteration 1: Generating answers...
  ✓ Generated answer 1/2
  ✓ Generated answer 2/2

⚖️  Evaluating 2 answers...
  ✓ Evaluated 1/2: 7.20/10
  ✓ Evaluated 2/2: 6.80/10
  📊 Average score: 7.00/10

🔧 Optimizing prompt...
  ✓ Prompt optimized (3 modifications)
```

### 2. Optimized Prompt

```
Output: optimized_prompt.txt

Before:
"Answer the question clearly.
Question: {question}
Answer:"

After:
"You are an expert educator. Answer the following question with:
1. A clear, accurate response
2. Step-by-step reasoning
3. Simple language appropriate for beginners

Question: {question}

Provide a comprehensive answer:
"
```

### 3. Performance History

```json
{
  "initial_score": 5.8,
  "final_score": 8.2,
  "improvement": 2.4,
  "iterations": 3,
  "converged": true,
  "performance_history": [5.8, 7.0, 8.2]
}
```

### 4. LangSmith Traces

Visit https://smith.langchain.com to see:
- Every LLM call with input/output
- Latency per call
- Token usage
- Error traces
- Full workflow visualization

---

## 🚀 Next Steps

1. **Install** dependencies
2. **Configure** LangSmith API key
3. **Run** the test script below
4. **View** traces in LangSmith dashboard
5. **Integrate** into your main CLI

### Quick Test Script

```bash
python -c "
from agents.langgraph_orchestrator import create_langchain_orchestrator

orchestrator = create_langchain_orchestrator(max_iterations=2)

results = orchestrator.run_optimization(
    questions=['What is AI?'],
    initial_prompt='Answer: {question}'
)

print(f'\nFinal Score: {results[\"final_score\"]:.2f}/10')
print(f'Improvement: +{results[\"improvement\"]:.2f}')
"
```

---

## 🔍 Troubleshooting

### Issue: "No module named 'langchain'"

```bash
pip install -r requirements_langchain.txt
```

### Issue: "LangSmith API key not found"

Add to `.env`:
```
LANGCHAIN_API_KEY=your_key_here
```

Or disable LangSmith:
```python
orchestrator = create_langchain_orchestrator(enable_langsmith=False)
```

### Issue: "HuggingFace API error"

Check your `.env` has:
```
HUGGINGFACE_API_KEY=hf_your_key_here
```

And permissions are enabled in HuggingFace settings.

---

## 📚 Documentation

- **LangChain**: https://python.langchain.com/docs/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **LangSmith**: https://docs.smith.langchain.com/
- **HuggingFace Hub**: https://huggingface.co/docs/huggingface_hub/

---

**Migration Complete! 🎉**

You now have:
- ✅ LangChain-based agents
- ✅ LangGraph workflow management
- ✅ LangSmith observability
- ✅ Working HuggingFace integration
- ✅ Optimized prompts generation
- ✅ Zero DSPy dependency (for migrated components)
