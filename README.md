# Astra-AI: Self-Improving LLM System

**Astra-AI** is an advanced framework for building self-improving Large Language Model (LLM) systems. It utilizes a closed feedback loop with automated prompt optimization to improve both objective accuracy and subjective explanation quality in question-answering tasks.

## 🚀 Overview

The core problem Astra-AI solves is the manual bottleneck of prompt engineering. Instead of manual trial-and-error, Astra-AI uses an **LLM-as-Judge** framework to evaluate outputs and an **Optimizer Agent** to iteratively refine prompts until they reach peak performance.

### Key Features
- **Closed Feedback Loop**: Autonomous iteration: Generator → Judge → Optimizer → Generator.
- **Multi-Dimensional Evaluation**: Scores outputs on Correctness, Clarity, Reasoning, Relevance, and Conciseness.
- **Automated Prompt Optimization**: Uses LLM reasoning to identify weaknesses and systematically improve prompt templates.
- **Multi-Model Support**: Seamlessly integrate OpenAI (GPT-4/3.5) and Anthropic (Claude 3.5 Sonnet/Opus/Haiku).
- **Comprehensive Monitoring**: Real-time progress tracking via CLI and a Streamlit-based Web Dashboard.

---

## 🏗️ Architecture

Astra-AI is built on a modular, agent-based architecture consisting of five core agents:

1.  **Orchestrator Agent**: Coordinates the entire workflow, manages iterations, and enforces stopping criteria.
2.  **Generator Agent**: Produces answers and explanations based on the current prompt template.
3.  **Judge Agent**: Evaluates generated outputs across five quality dimensions using a structured scoring system.
4.  **Optimizer Agent**: Analyzes judge feedback and scores to generate improved prompt versions.
5.  **Analytics Agent**: Logs all interactions, tracks performance metrics, and provides optimization insights.

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

Astra-AI supports multiple LLM providers:

- **OpenAI**: Default integration for all agents.
- **Anthropic (Claude)**: Optimized for strong reasoning, constitutional AI alignment, and long context windows.

Detailed integration instructions can be found in [./Claude.md](./Claude.md).

---

## 🖥️ UI & Monitoring

- **CLI Interface**: Primary control for running experiments with real-time status updates using the `rich` library.
- **Web Dashboard**: A Streamlit-based dashboard for visualizing optimization progress, score distributions, and prompt evolution.

Refer to [./UIDesign.md](./UIDesign.md) for more information on the user interface.

---

## 📂 Project Structure

- [./Agents.md](./Agents.md): Detailed documentation of the agent architecture.
- [./Claude.md](./Claude.md): Guide for integrating Anthropic's Claude models.
- [./RPI.md](./RPI.md): Research Problem Identification and project goals.
- [./UIDesign.md](./UIDesign.md): Documentation for the CLI and Web Dashboard.

---

## 🛠️ Getting Started

### Installation

```bash
pip install openai anthropic streamlit rich plotly pandas
```

### Basic Usage

1. Configure your API keys in a `.env` file.
2. Run the optimization loop via the CLI:

```bash
python main.py optimize --questions data/questions.json --initial-prompt prompts/baseline.txt
```

---

## 🔬 Research Context

This project aims to answer whether a closed-loop system can effectively replace manual prompt engineering while maintaining high reliability and performance stability. See [./RPI.md](./RPI.md) for the full research statement and objectives.
