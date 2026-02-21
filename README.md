# Astra-AI: Self-Improving LLM System

**Astra-AI** is an advanced framework for building self-improving Large Language Model (LLM) systems. It utilizes a closed feedback loop with automated prompt optimization to improve both objective accuracy and subjective explanation quality in question-answering tasks.

## 🚀 Overview

The core problem Astra-AI solves is the manual bottleneck of prompt engineering. Instead of manual trial-and-error, Astra-AI leverages the **DSPy framework** for automatic prompt generation and optimization, combined with an **LLM-as-Judge** framework to evaluate outputs across multiple quality dimensions. This creates a fully autonomous system that iteratively refines prompts until they reach peak performance.

### Key Features
- **DSPy-Powered Prompt Generation**: Automatic prompt generation and optimization using DSPy's Signatures, Modules, and Teleprompters.
- **Closed Feedback Loop**: Autonomous iteration: DSPy Generator → Judge → Optimizer → DSPy Compilation.
- **Multi-Dimensional Evaluation**: Scores outputs on Correctness, Clarity, Reasoning, Relevance, and Conciseness.
- **Intelligent Optimization**: Combines DSPy's metric-based optimization with custom LLM-driven refinement strategies.
- **Multi-Model Support**: Seamlessly integrate OpenAI (GPT-4/3.5) and Anthropic (Claude 3.5 Sonnet/Opus/Haiku).
- **Cost Optimization**: Automatic model selection and cost-effective inference strategies.
- **Comprehensive Monitoring**: Real-time progress tracking via CLI and a Streamlit-based Web Dashboard.

---

## 🏗️ Architecture

Astra-AI is built on a modular, agent-based architecture with **DSPy framework** at its core, consisting of five core agents:

1.  **DSPy Generator Module**: Automatically generates optimized prompts using DSPy Signatures and Teleprompters (BootstrapFewShot, MIPRO).
2.  **Judge Agent**: Evaluates generated outputs across five quality dimensions using a structured scoring system powered by LLM-as-Judge.
3.  **Optimizer Agent**: Analyzes judge feedback and scores, then triggers DSPy compilation to generate improved prompt versions.
4.  **Orchestrator Agent**: Coordinates the entire workflow, manages DSPy optimization cycles, and enforces stopping criteria.
5.  **Analytics Agent**: Logs all interactions, tracks performance metrics, monitors cost optimization, and provides insights.

**DSPy Integration**: The system uses DSPy's automatic prompt optimization instead of manual prompt engineering, with custom evaluation metrics from the Judge Agent guiding the optimization process.

For more details, see [./Agents.md](./Agents.md).

---

## 📊 Evaluation Framework

The system evaluates responses on a 1-10 scale across several criteria:

- **Correctness (40%)**: Factual accuracy and alignment with ground truth.
- **Clarity (20%)**: Readability, logical flow, and accessibility of the explanation.
- **Logical Reasoning (20%)**: Soundness of claims and support for arguments.
- **Relevance (10%)**: Directness in addressing the question.
- **Conciseness (10%)**: Efficiency of expression without unnecessary verbosity.

---

## 🤖 LLM Integration

Astra-AI supports multiple LLM providers through DSPy's unified interface:

- **DSPy Framework**: Core framework for automatic prompt generation, compilation, and optimization.
- **OpenAI**: Default integration (GPT-4, GPT-3.5-turbo) for DSPy modules and evaluation agents.
- **Anthropic (Claude)**: Optimized for strong reasoning, constitutional AI alignment, and long context windows (Claude 3.5 Sonnet/Opus/Haiku).
- **Cost Optimization**: Automatic model selection based on task complexity, cost constraints, and performance requirements.

Detailed integration instructions can be found in [./Claude.md](./Claude.md).

---

## 🖥️ UI & Monitoring

- **CLI Interface**: Primary control for running experiments with real-time status updates using the `rich` library.
- **Web Dashboard**: A Streamlit-based dashboard for visualizing optimization progress, score distributions, and prompt evolution.

Refer to [./UIDesign.md](./UIDesign.md) for more information on the user interface.

---

## 📂 Project Structure

- [./Agents.md](./Agents.md): Detailed documentation of the agent architecture and DSPy integration.
- [./Claude.md](./Claude.md): Guide for integrating Anthropic's Claude models.
- [./RPI.md](./RPI.md): Research Problem Identification and project goals.
- [./UIDesign.md](./UIDesign.md): Documentation for the CLI and Web Dashboard.
- DSPy.md (coming soon): Comprehensive guide to DSPy integration and automatic prompt optimization.

---

## 🛠️ Getting Started

### Installation

```bash
pip install dspy-ai openai anthropic streamlit rich plotly pandas
```

### Basic Usage

1. Configure your API keys in a `.env` file.
2. Run the optimization loop via the CLI:

```bash
python main.py optimize --questions data/questions.json --initial-prompt prompts/baseline.txt
```

---

## 🔬 Research Context

This project aims to answer whether a DSPy-powered closed-loop system can effectively replace manual prompt engineering while maintaining high reliability and performance stability. By combining DSPy's automatic optimization with multi-dimensional LLM-as-Judge evaluation, we explore the frontier of fully autonomous prompt engineering with cost optimization and model selection.

See [./RPI.md](./RPI.md) for the full research statement and objectives.
