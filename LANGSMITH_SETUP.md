# LangSmith Setup Guide

## 🔍 What is LangSmith?

LangSmith is LangChain's observability platform that lets you:
- **Trace every LLM call** - See inputs, outputs, latency
- **Monitor performance** - Track scores, errors, costs
- **Debug workflows** - Visualize the full execution flow
- **Understand your system** - See exactly how optimization works

## ⚡ Quick Setup (2 minutes)

### Step 1: Get Your Free API Key

1. Go to: https://smith.langchain.com
2. Sign up (free account)
3. Go to Settings → API Keys
4. Create new API key
5. Copy the key (starts with `lsv2_...`)

### Step 2: Update Your .env File

Open `d:\CHARUSAT\Sem-6\Astra AI\.env` and update:

```bash
# Replace this placeholder:
LANGCHAIN_API_KEY=your_langsmith_api_key_here

# With your actual key:
LANGCHAIN_API_KEY=lsv2_pt_1234567890abcdef...
```

**Make sure these are set:**
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=astra-ai
```

### Step 3: Verify Configuration

Run this quick test:

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ LangSmith Key:', os.getenv('LANGCHAIN_API_KEY')[:15] + '...' if os.getenv('LANGCHAIN_API_KEY') else '❌ Not set')"
```

## 📊 What You'll See in LangSmith

Once configured, every run will automatically create traces:

### 1. Judge Evaluations
- **Project**: `astra-ai-judge`
- **See**: Every evaluation with scores, feedback, latency
- **Example trace**:
  ```
  evaluate()
  ├─ Input: question, answer, explanation
  ├─ LLM Call: Mistral-7B-Instruct
  │  ├─ Latency: 6.9s
  │  └─ Tokens: 450 in, 220 out
  └─ Output: scores, composite_score, feedback
  ```

### 2. Optimizer Iterations
- **Project**: `astra-ai-optimizer`
- **See**: Prompt evolution, modifications, improvements
- **Example trace**:
  ```
  optimize()
  ├─ Analysis: weak_areas=['clarity', 'reasoning']
  ├─ LLM Call: Meta-Llama-3
  │  ├─ Latency: 8.2s
  │  └─ Modifications: 3 changes
  └─ Output: optimized_prompt
  ```

### 3. Full Orchestration
- **Project**: `astra-ai-orchestrator`
- **See**: Complete workflow across iterations
- **Example trace**:
  ```
  run_optimization()
  ├─ Iteration 1
  │  ├─ generate → evaluate → optimize
  │  └─ Score: 6.5 → 7.2
  ├─ Iteration 2
  │  ├─ generate → evaluate → optimize
  │  └─ Score: 7.2 → 8.1
  └─ Converged: true
  ```

## 🎯 How to Use LangSmith Dashboard

### View Recent Runs
1. Go to: https://smith.langchain.com
2. Select project: `astra-ai-judge`, `astra-ai-optimizer`, or `astra-ai-orchestrator`
3. See all traces in real-time

### Inspect a Trace
Click any trace to see:
- **Timeline**: Visual flow of operations
- **Inputs/Outputs**: Exact prompts and responses
- **Metadata**: Latency, tokens, model used
- **Errors**: Stack traces if failures occur

### Compare Iterations
- Track score improvements over time
- See which prompts perform better
- Identify bottlenecks

## 🔧 Configuration Options

### Enable/Disable Tracing

**Enable** (default):
```bash
LANGCHAIN_TRACING_V2=true
```

**Disable** (no tracing):
```bash
LANGCHAIN_TRACING_V2=false
# Or comment out the line
```

### Change Project Name

```bash
# Default
LANGCHAIN_PROJECT=astra-ai

# Custom
LANGCHAIN_PROJECT=my-optimization-project
```

### Per-Agent Projects (Already Configured)

The agents automatically set their own projects:
- Judge → `astra-ai-judge`
- Optimizer → `astra-ai-optimizer`
- Orchestrator → `astra-ai-orchestrator`

You can override by setting before running:
```python
os.environ["LANGCHAIN_PROJECT"] = "my-custom-project"
```

## 🚀 Test Your Setup

### Quick Test
```bash
python test_judge.py
```

Then check: https://smith.langchain.com → Project: `astra-ai-judge`

You should see a new trace with:
- ✅ Input question
- ✅ LLM response
- ✅ Evaluation scores
- ✅ Latency metrics

## 💡 Pro Tips

1. **Use Different Projects for Testing vs Production**
   ```bash
   LANGCHAIN_PROJECT=astra-ai-dev    # Testing
   LANGCHAIN_PROJECT=astra-ai-prod   # Production
   ```

2. **Filter Traces by Tags**
   ```python
   # In your code
   from langsmith import Client
   client = Client()
   client.create_run(..., tags=["experiment-1", "high-priority"])
   ```

3. **Export Trace Data**
   - Dashboard → Select traces → Export to CSV/JSON
   - Analyze in Excel/Python

4. **Set Alerts**
   - Dashboard → Settings → Alerts
   - Get notified of errors or slow requests

## ❓ Troubleshooting

### "Traces not appearing"
1. Check API key is correct: `echo $LANGCHAIN_API_KEY` (Linux) or `echo %LANGCHAIN_API_KEY%` (Windows)
2. Verify `LANGCHAIN_TRACING_V2=true`
3. Wait 10-30 seconds for traces to appear
4. Refresh dashboard

### "Authentication failed"
- Regenerate API key: https://smith.langchain.com/settings
- Update `.env` with new key
- Restart your script

### "No project found"
- Projects are created automatically on first trace
- Check you're looking at the right project name
- Try running a test again

## 📚 More Resources

- **LangSmith Docs**: https://docs.smith.langchain.com
- **Tracing Guide**: https://docs.smith.langchain.com/tracing
- **API Reference**: https://docs.smith.langchain.com/reference

## 🎉 You're All Set!

With LangSmith configured, you'll have complete visibility into:
- ✅ Every evaluation score
- ✅ Every prompt optimization
- ✅ Every iteration of the workflow
- ✅ Performance metrics and bottlenecks

**This answers your requirement:** "Proceed to All Connection of Langsmith to understand how this all are working" ✅

Run any test and watch the traces appear in real-time at https://smith.langchain.com
