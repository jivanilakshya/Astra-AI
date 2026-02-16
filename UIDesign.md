# UI Design Documentation

## Overview

This document outlines the user interface design for the self-improving LLM system. While the project is **backend-focused**, a minimal UI is necessary for:
- Monitoring system performance
- Visualizing optimization progress
- Debugging and experimentation
- Result analysis and reporting

---

## 1. Design Philosophy

### Principles

**1. Backend-First Approach**
- UI is a **monitoring tool**, not the primary product
- Focus on **functionality over aesthetics**
- Prioritize **developer experience** over end-user polish

**2. Research-Grade Interface**
- Designed for **experimenters and researchers**
- Emphasize **data visibility and transparency**
- Support **reproducibility and analysis**

**3. Modular Components**
- Each UI component maps to a backend agent
- **Plug-and-play** visualizations
- Easy to extend and customize

**4. Performance Monitoring Focus**
- Real-time feedback during optimization
- Clear visualization of improvement trajectories
- Accessible logging and debugging information

---

## 2. Architecture Overview

### Tech Stack Recommendations

**Minimal Setup (CLI + Web Dashboard):**
- **CLI**: Python `rich` library for terminal output
- **Dashboard**: Streamlit (rapid prototyping)
- **Visualizations**: Plotly (interactive charts)
- **Data Storage**: SQLite for logs

**Full Stack (Optional):**
- **Frontend**: React + TypeScript
- **Backend API**: FastAPI
- **Real-time Updates**: WebSockets
- **Visualizations**: D3.js or Recharts
- **State Management**: Redux or Zustand

### System Components

```
┌─────────────────────────────────────────────────┐
│          MONITORING DASHBOARD (Web UI)          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Overview │  │ Progress │  │ Results  │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│           CONTROL INTERFACE (CLI)               │
│  - Start/Stop Optimization                      │
│  - Configure Parameters                         │
│  - View Logs                                    │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│         ANALYTICS & VISUALIZATION               │
│  - Performance Charts                           │
│  - Score Distributions                          │
│  - Prompt Evolution                             │
└─────────────────────────────────────────────────┘
```

---

## 3. Core UI Components

### 3.1 Command-Line Interface (Primary)

**Purpose:** Main control interface for running experiments

**Features:**
- Start optimization with configuration
- Monitor real-time progress
- View iteration summaries
- Access detailed logs
- Export results

**Implementation (Rich Library):**

```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

class CLInterface:
    def __init__(self):
        self.console = Console()
        
    def display_header(self):
        """Show system header"""
        self.console.print(Panel.fit(
            "[bold blue]Self-Improving LLM System[/bold blue]\n"
            "[dim]Automated Prompt Optimization via Closed Feedback Loop[/dim]",
            border_style="blue"
        ))
    
    def display_configuration(self, config: dict):
        """Show current configuration"""
        table = Table(title="Configuration", show_header=True)
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in config.items():
            table.add_row(key, str(value))
        
        self.console.print(table)
    
    def show_iteration_progress(self, iteration: int, max_iter: int):
        """Display progress bar"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task(
                f"[cyan]Iteration {iteration}/{max_iter}...", 
                total=100
            )
            # Update progress as iteration proceeds
    
    def display_iteration_results(self, iteration: int, results: dict):
        """Show iteration summary"""
        table = Table(
            title=f"Iteration {iteration} Results",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Score", justify="right", style="green")
        
        table.add_row("Correctness", f"{results['avg_correctness']:.2f}")
        table.add_row("Clarity", f"{results['avg_clarity']:.2f}")
        table.add_row("Reasoning", f"{results['avg_reasoning']:.2f}")
        table.add_row("Relevance", f"{results['avg_relevance']:.2f}")
        table.add_row("Conciseness", f"{results['avg_conciseness']:.2f}")
        table.add_row(
            "[bold]Composite Score[/bold]", 
            f"[bold]{results['composite_score']:.2f}[/bold]"
        )
        
        self.console.print(table)
    
    def show_optimization_summary(self, summary: dict):
        """Display final optimization results"""
        self.console.print("\n" + "="*50)
        self.console.print("[bold green]Optimization Complete![/bold green]")
        self.console.print("="*50 + "\n")
        
        summary_table = Table(show_header=False)
        summary_table.add_column("Metric", style="cyan", width=30)
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Initial Score", f"{summary['initial_score']:.2f}")
        summary_table.add_row("Final Score", f"{summary['final_score']:.2f}")
        summary_table.add_row(
            "Improvement", 
            f"+{summary['improvement']:.2f} ({summary['improvement_pct']:.1f}%)"
        )
        summary_table.add_row("Iterations", str(summary['iterations']))
        summary_table.add_row("Converged", "✓" if summary['converged'] else "✗")
        
        self.console.print(summary_table)
    
    def show_error(self, error_msg: str):
        """Display error message"""
        self.console.print(f"[bold red]Error:[/bold red] {error_msg}")
    
    def show_prompt_comparison(self, initial: str, final: str):
        """Display initial vs final prompt"""
        self.console.print("\n[bold]Initial Prompt:[/bold]")
        self.console.print(Panel(initial, border_style="red"))
        
        self.console.print("\n[bold]Optimized Prompt:[/bold]")
        self.console.print(Panel(final, border_style="green"))
```

**CLI Usage Example:**

```bash
$ python main.py optimize \
    --questions data/questions.json \
    --initial-prompt prompts/baseline.txt \
    --max-iterations 10 \
    --threshold 8.5

# Output:
╭─────────────────────────────────────────╮
│  Self-Improving LLM System              │
│  Automated Prompt Optimization via      │
│  Closed Feedback Loop                   │
╰─────────────────────────────────────────╯

Configuration
┌───────────────────┬──────────────────────┐
│ Parameter         │ Value                │
├───────────────────┼──────────────────────┤
│ max_iterations    │ 10                   │
│ threshold         │ 8.5                  │
│ num_questions     │ 25                   │
└───────────────────┴──────────────────────┘

--- Iteration 1 ---
⠋ Generating answers...
⠙ Evaluating outputs...
⠹ Optimizing prompt...

Iteration 1 Results
┌─────────────────┬────────┐
│ Metric          │  Score │
├─────────────────┼────────┤
│ Correctness     │   6.20 │
│ Clarity         │   5.80 │
│ Reasoning       │   5.50 │
│ Relevance       │   7.10 │
│ Conciseness     │   6.40 │
│ Composite Score │   6.16 │
└─────────────────┴────────┘

...

==================================================
Optimization Complete!
==================================================

┌────────────────┬─────────────┐
│ Initial Score  │ 6.16        │
│ Final Score    │ 8.72        │
│ Improvement    │ +2.56 (41%) │
│ Iterations     │ 8           │
│ Converged      │ ✓           │
└────────────────┴─────────────┘
```

---

### 3.2 Web Dashboard (Streamlit)

**Purpose:** Visual monitoring and analysis

**Implementation:**

```python
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict

class OptimizationDashboard:
    def __init__(self):
        st.set_page_config(
            page_title="LLM Optimization Monitor",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render(self, data: Dict):
        """Main dashboard rendering"""
        
        # Header
        st.title("🤖 Self-Improving LLM System")
        st.markdown("**Automated Prompt Optimization Dashboard**")
        
        # Sidebar controls
        self._render_sidebar()
        
        # Main content
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self._render_metric_card(
                "Current Score",
                data['current_score'],
                data['score_delta']
            )
        
        with col2:
            self._render_metric_card(
                "Iteration",
                data['current_iteration'],
                None
            )
        
        with col3:
            self._render_metric_card(
                "Improvement",
                f"{data['total_improvement']:.1f}%",
                None
            )
        
        # Performance chart
        st.subheader("📈 Optimization Progress")
        self._render_performance_chart(data['history'])
        
        # Score breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Current Score Breakdown")
            self._render_score_breakdown(data['current_scores'])
        
        with col2:
            st.subheader("📉 Score Distribution")
            self._render_score_distribution(data['score_distribution'])
        
        # Prompt comparison
        st.subheader("📝 Prompt Evolution")
        self._render_prompt_comparison(
            data['initial_prompt'],
            data['current_prompt']
        )
        
        # Recent evaluations
        st.subheader("🔍 Recent Evaluations")
        self._render_evaluation_table(data['recent_evaluations'])
    
    def _render_sidebar(self):
        """Render sidebar controls"""
        st.sidebar.header("Controls")
        
        if st.sidebar.button("▶️ Start Optimization"):
            st.session_state.running = True
        
        if st.sidebar.button("⏸️ Pause"):
            st.session_state.running = False
        
        if st.sidebar.button("⏹️ Stop"):
            st.session_state.running = False
            st.session_state.stopped = True
        
        st.sidebar.header("Configuration")
        max_iterations = st.sidebar.slider("Max Iterations", 5, 20, 10)
        threshold = st.sidebar.slider("Convergence Threshold", 7.0, 9.5, 8.5)
        
        st.sidebar.header("Filters")
        show_criteria = st.sidebar.multiselect(
            "Show Criteria",
            ["Correctness", "Clarity", "Reasoning", "Relevance", "Conciseness"],
            default=["Correctness", "Clarity", "Reasoning"]
        )
    
    def _render_metric_card(self, title: str, value: float, delta: float = None):
        """Render metric card"""
        st.metric(
            label=title,
            value=f"{value:.2f}" if isinstance(value, float) else value,
            delta=f"+{delta:.2f}" if delta else None
        )
    
    def _render_performance_chart(self, history: List[Dict]):
        """Render performance over iterations"""
        
        df = pd.DataFrame(history)
        
        fig = go.Figure()
        
        # Composite score
        fig.add_trace(go.Scatter(
            x=df['iteration'],
            y=df['composite_score'],
            mode='lines+markers',
            name='Composite Score',
            line=dict(color='rgb(0, 176, 246)', width=3),
            marker=dict(size=8)
        ))
        
        # Individual criteria
        for criterion in ['correctness', 'clarity', 'reasoning']:
            fig.add_trace(go.Scatter(
                x=df['iteration'],
                y=df[criterion],
                mode='lines',
                name=criterion.capitalize(),
                line=dict(width=1, dash='dash'),
                opacity=0.6
            ))
        
        # Threshold line
        fig.add_hline(
            y=8.5,
            line_dash="dot",
            line_color="green",
            annotation_text="Target Threshold"
        )
        
        fig.update_layout(
            title="Performance Over Iterations",
            xaxis_title="Iteration",
            yaxis_title="Score",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_score_breakdown(self, scores: Dict[str, float]):
        """Render radar chart of current scores"""
        
        categories = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Current Scores'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_score_distribution(self, distribution: Dict):
        """Render box plot of score distributions"""
        
        fig = go.Figure()
        
        for criterion, values in distribution.items():
            fig.add_trace(go.Box(
                y=values,
                name=criterion.capitalize(),
                boxmean='sd'
            ))
        
        fig.update_layout(
            title="Score Distribution Across Questions",
            yaxis_title="Score",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_prompt_comparison(self, initial: str, current: str):
        """Show prompt evolution"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Initial Prompt:**")
            st.code(initial, language="text")
        
        with col2:
            st.markdown("**Current Prompt:**")
            st.code(current, language="text")
        
        # Highlight changes
        st.markdown("**Changes Made:**")
        changes = self._compute_prompt_diff(initial, current)
        for change in changes:
            st.markdown(f"- {change}")
    
    def _render_evaluation_table(self, evaluations: List[Dict]):
        """Display recent evaluation results"""
        
        df = pd.DataFrame(evaluations)
        st.dataframe(
            df[['question', 'composite_score', 'correctness', 
                'clarity', 'reasoning']],
            use_container_width=True
        )
    
    def _compute_prompt_diff(self, old: str, new: str) -> List[str]:
        """Compute differences between prompts"""
        # Simple diff implementation
        old_lines = set(old.split('\n'))
        new_lines = set(new.split('\n'))
        
        added = new_lines - old_lines
        removed = old_lines - new_lines
        
        changes = []
        for line in removed:
            if line.strip():
                changes.append(f"❌ Removed: {line}")
        for line in added:
            if line.strip():
                changes.append(f"✅ Added: {line}")
        
        return changes
```

**Dashboard Usage:**

```bash
$ streamlit run dashboard.py

# Opens browser at http://localhost:8501
```

**Dashboard Features:**
- Real-time progress monitoring
- Interactive performance charts
- Score breakdowns and distributions
- Prompt evolution tracking
- Evaluation result browsing
- Configuration controls

---

### 3.3 Visualization Components

**1. Performance Line Chart**

```python
import plotly.graph_objects as go

def create_performance_chart(history: List[Dict]) -> go.Figure:
    """Line chart showing score improvement over iterations"""
    
    iterations = [h['iteration'] for h in history]
    composite_scores = [h['composite_score'] for h in history]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=iterations,
        y=composite_scores,
        mode='lines+markers',
        name='Composite Score',
        line=dict(color='#00B0F6', width=3),
        marker=dict(size=10, color='#00B0F6', line=dict(width=2, color='white'))
    ))
    
    # Add trend line
    z = np.polyfit(iterations, composite_scores, 1)
    p = np.poly1d(z)
    fig.add_trace(go.Scatter(
        x=iterations,
        y=p(iterations),
        mode='lines',
        name='Trend',
        line=dict(color='red', width=2, dash='dash'),
        opacity=0.5
    ))
    
    fig.update_layout(
        title="Optimization Performance",
        xaxis_title="Iteration",
        yaxis_title="Composite Score",
        template="plotly_white",
        hovermode='x unified'
    )
    
    return fig
```

**2. Score Breakdown Radar Chart**

```python
def create_radar_chart(scores: Dict[str, float]) -> go.Figure:
    """Radar chart for multi-dimensional scores"""
    
    categories = ['Correctness', 'Clarity', 'Reasoning', 
                  'Relevance', 'Conciseness']
    values = [scores[k] for k in categories]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # Close the polygon
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(0, 176, 246, 0.3)',
        line=dict(color='rgb(0, 176, 246)', width=2),
        name='Scores'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=10)
            )
        ),
        showlegend=False
    )
    
    return fig
```

**3. Improvement Heatmap**

```python
def create_improvement_heatmap(data: pd.DataFrame) -> go.Figure:
    """Heatmap showing score improvements per question"""
    
    fig = go.Figure(data=go.Heatmap(
        z=data.values,
        x=data.columns,
        y=data.index,
        colorscale='RdYlGn',
        zmid=0,
        colorbar=dict(title="Improvement")
    ))
    
    fig.update_layout(
        title="Score Improvements by Question and Criterion",
        xaxis_title="Criterion",
        yaxis_title="Question ID"
    )
    
    return fig
```

**4. Prompt Evolution Timeline**

```python
def create_prompt_timeline(prompts: List[Dict]) -> go.Figure:
    """Timeline showing prompt modifications"""
    
    iterations = [p['iteration'] for p in prompts]
    lengths = [len(p['text']) for p in prompts]
    complexities = [p['complexity_score'] for p in prompts]
    
    fig = go.Figure()
    
    # Prompt length over time
    fig.add_trace(go.Scatter(
        x=iterations,
        y=lengths,
        mode='lines+markers',
        name='Prompt Length',
        yaxis='y1'
    ))
    
    # Complexity score over time
    fig.add_trace(go.Scatter(
        x=iterations,
        y=complexities,
        mode='lines+markers',
        name='Complexity',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Prompt Evolution",
        xaxis_title="Iteration",
        yaxis=dict(title="Length (chars)"),
        yaxis2=dict(
            title="Complexity Score",
            overlaying='y',
            side='right'
        )
    )
    
    return fig
```

---

## 4. Data Export & Reporting

### Export Formats

**1. JSON Export**

```python
def export_results_json(results: Dict, filepath: str):
    """Export complete results to JSON"""
    
    export_data = {
        "metadata": {
            "experiment_id": results['experiment_id'],
            "timestamp": datetime.now().isoformat(),
            "configuration": results['config']
        },
        "summary": {
            "initial_score": results['initial_score'],
            "final_score": results['final_score'],
            "improvement": results['improvement'],
            "iterations": results['iterations'],
            "converged": results['converged']
        },
        "history": results['history'],
        "prompts": {
            "initial": results['initial_prompt'],
            "final": results['final_prompt'],
            "evolution": results['prompt_history']
        },
        "evaluations": results['all_evaluations']
    }
    
    with open(filepath, 'w') as f:
        json.dump(export_data, f, indent=2)
```

**2. CSV Export**

```python
def export_results_csv(results: Dict, filepath: str):
    """Export iteration history to CSV"""
    
    df = pd.DataFrame(results['history'])
    df.to_csv(filepath, index=False)
```

**3. PDF Report**

```python
from fpdf import FPDF

class OptimizationReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'LLM Optimization Report', 0, 1, 'C')
        self.ln(5)
    
    def add_summary(self, summary: Dict):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Summary', 0, 1)
        
        self.set_font('Arial', '', 10)
        self.cell(0, 6, f"Initial Score: {summary['initial_score']:.2f}", 0, 1)
        self.cell(0, 6, f"Final Score: {summary['final_score']:.2f}", 0, 1)
        self.cell(0, 6, f"Improvement: +{summary['improvement']:.2f}", 0, 1)
        self.cell(0, 6, f"Iterations: {summary['iterations']}", 0, 1)
        self.ln(10)
    
    def add_chart(self, chart_path: str):
        self.image(chart_path, x=10, w=190)
        self.ln(10)

def generate_pdf_report(results: Dict, output_path: str):
    """Generate PDF report"""
    
    pdf = OptimizationReport()
    pdf.add_page()
    pdf.add_summary(results['summary'])
    
    # Add performance chart
    fig = create_performance_chart(results['history'])
    fig.write_image('/tmp/performance.png')
    pdf.add_chart('/tmp/performance.png')
    
    pdf.output(output_path)
```

---

## 5. Real-Time Monitoring

### WebSocket Implementation (Optional)

```python
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import json
import asyncio

app = FastAPI()

class OptimizationMonitor:
    def __init__(self):
        self.connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Send update to all connected clients"""
        for connection in self.connections:
            await connection.send_json(message)

monitor = OptimizationMonitor()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await monitor.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        monitor.disconnect(websocket)

# In orchestrator agent:
async def send_update(iteration: int, results: dict):
    """Send real-time update"""
    await monitor.broadcast({
        "type": "iteration_complete",
        "iteration": iteration,
        "scores": results['scores'],
        "composite_score": results['composite_score']
    })
```

**Frontend (React/JavaScript):**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'iteration_complete') {
        updateChart(data.iteration, data.scores);
        updateMetrics(data.composite_score);
    }
};
```

---

## 6. Configuration Interface

### Settings Panel

```python
import streamlit as st

def render_configuration_panel():
    """Render configuration settings"""
    
    st.sidebar.header("⚙️ Configuration")
    
    # Model selection
    st.sidebar.subheader("Models")
    generator_model = st.sidebar.selectbox(
        "Generator Model",
        ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-opus"]
    )
    
    judge_model = st.sidebar.selectbox(
        "Judge Model",
        ["gpt-4", "claude-3-sonnet", "claude-3-opus"]
    )
    
    # Optimization parameters
    st.sidebar.subheader("Optimization")
    max_iterations = st.sidebar.slider("Max Iterations", 5, 20, 10)
    convergence_threshold = st.sidebar.slider(
        "Convergence Threshold", 
        7.0, 9.5, 8.5, 0.1
    )
    
    # Criteria weights
    st.sidebar.subheader("Evaluation Weights")
    correctness_weight = st.sidebar.slider("Correctness", 0.0, 1.0, 0.40, 0.05)
    clarity_weight = st.sidebar.slider("Clarity", 0.0, 1.0, 0.20, 0.05)
    reasoning_weight = st.sidebar.slider("Reasoning", 0.0, 1.0, 0.20, 0.05)
    relevance_weight = st.sidebar.slider("Relevance", 0.0, 1.0, 0.10, 0.05)
    conciseness_weight = st.sidebar.slider("Conciseness", 0.0, 1.0, 0.10, 0.05)
    
    # Validate weights sum to 1.0
    total_weight = (correctness_weight + clarity_weight + 
                    reasoning_weight + relevance_weight + conciseness_weight)
    
    if abs(total_weight - 1.0) > 0.01:
        st.sidebar.error(f"⚠️ Weights must sum to 1.0 (current: {total_weight:.2f})")
    
    # Advanced settings
    with st.sidebar.expander("Advanced Settings"):
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        top_p = st.slider("Top P", 0.0, 1.0, 0.9, 0.05)
        max_tokens = st.number_input("Max Tokens", 100, 2000, 500, 100)
    
    return {
        "generator_model": generator_model,
        "judge_model": judge_model,
        "max_iterations": max_iterations,
        "convergence_threshold": convergence_threshold,
        "criteria_weights": {
            "correctness": correctness_weight,
            "clarity": clarity_weight,
            "reasoning": reasoning_weight,
            "relevance": relevance_weight,
            "conciseness": conciseness_weight
        },
        "advanced": {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
    }
```

---

## 7. Debugging & Logging Interface

### Log Viewer

```python
def render_log_viewer():
    """Interactive log viewer"""
    
    st.header("📋 System Logs")
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_level = st.selectbox(
            "Log Level",
            ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"]
        )
    
    with col2:
        agent_filter = st.selectbox(
            "Agent",
            ["ALL", "Generator", "Judge", "Optimizer", "Orchestrator"]
        )
    
    with col3:
        iteration_filter = st.number_input(
            "Iteration",
            min_value=0,
            value=0,
            help="0 = All iterations"
        )
    
    # Log display
    logs = load_filtered_logs(log_level, agent_filter, iteration_filter)
    
    for log in logs:
        with st.expander(f"[{log['timestamp']}] {log['level']} - {log['agent']}"):
            st.code(log['message'], language="text")
            if log.get('details'):
                st.json(log['details'])
```

### Debug Panel

```python
def render_debug_panel(current_state: Dict):
    """Debug information panel"""
    
    st.header("🐛 Debug Information")
    
    tabs = st.tabs([
        "Current State",
        "Agent Status",
        "API Calls",
        "Performance"
    ])
    
    with tabs[0]:
        st.subheader("System State")
        st.json(current_state)
    
    with tabs[1]:
        st.subheader("Agent Health")
        agent_status = get_agent_status()
        
        for agent, status in agent_status.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"**{agent}**")
            col2.write(status['status'])
            col3.write(f"Latency: {status['avg_latency']:.2f}s")
    
    with tabs[2]:
        st.subheader("API Call History")
        api_calls = get_api_call_history()
        st.dataframe(api_calls)
    
    with tabs[3]:
        st.subheader("Performance Metrics")
        metrics = get_performance_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total API Calls", metrics['total_calls'])
        col2.metric("Total Tokens", f"{metrics['total_tokens']:,}")
        col3.metric("Total Cost", f"${metrics['total_cost']:.2f}")
        col4.metric("Avg Latency", f"{metrics['avg_latency']:.2f}s")
```

---

## 8. User Workflows

### Workflow 1: Run New Experiment

```
1. User opens dashboard
2. Clicks "New Experiment"
3. Configures parameters:
   - Selects question dataset
   - Sets max iterations
   - Adjusts criteria weights
   - Chooses models
4. Reviews initial prompt
5. Clicks "Start Optimization"
6. Monitors real-time progress
7. Reviews final results
8. Exports report
```

### Workflow 2: Compare Experiments

```
1. User selects "Compare" mode
2. Loads multiple experiment results
3. Views side-by-side comparison:
   - Performance charts overlaid
   - Final scores compared
   - Prompt differences highlighted
4. Exports comparison report
```

### Workflow 3: Debug Failed Optimization

```
1. User notices poor performance
2. Opens debug panel
3. Reviews agent logs
4. Checks API call history
5. Examines individual evaluations
6. Identifies issue (e.g., judge bias)
7. Adjusts configuration
8. Re-runs experiment
```

---

## 9. Mobile Responsiveness (Optional)

### Responsive Dashboard

```python
# Streamlit automatically handles basic responsiveness
# For custom layouts:

def render_mobile_friendly():
    """Mobile-optimized layout"""
    
    # Check viewport width
    is_mobile = st.sidebar.checkbox("Mobile View", value=False)
    
    if is_mobile:
        # Single column layout
        render_metric_cards_vertical()
        render_chart_compact()
        render_simplified_controls()
    else:
        # Multi-column layout
        render_metric_cards_horizontal()
        render_chart_full()
        render_full_controls()
```

---

## 10. Accessibility

### Guidelines

**Color Contrast:**
- Use high-contrast color schemes
- Avoid relying solely on color to convey information
- Provide text labels for all visual elements

**Keyboard Navigation:**
- All controls accessible via keyboard
- Tab order follows logical flow
- Shortcuts for common actions

**Screen Reader Support:**
- Meaningful alt text for charts
- ARIA labels for interactive elements
- Semantic HTML structure

---

## Conclusion

The UI design prioritizes **functionality and monitoring** over aesthetics, aligning with the backend-first philosophy. Key features include:

✅ **Rich CLI** for primary control
✅ **Streamlit dashboard** for visual monitoring
✅ **Interactive charts** for performance analysis
✅ **Real-time updates** via WebSockets (optional)
✅ **Comprehensive logging** and debugging tools
✅ **Export capabilities** for reporting

This design enables researchers and developers to effectively monitor, analyze, and debug the self-improving LLM system while maintaining a lightweight, backend-focused architecture.
