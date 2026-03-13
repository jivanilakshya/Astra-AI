"""
CLI Output Formatter - Beautiful, structured terminal output

Clean output for non-technical users with:
- Visual sections & dividers
- Unicode icons for status
- Color-coded via ANSI (optional, falls back to plain)
- Model info, cost, confidence, summary, full answer

Works even when 'rich' is not installed (graceful fallback).

Usage:
    from utils.cli_formatter import CLIFormatter
    fmt = CLIFormatter()
    fmt.print_header("ASTRA AI")
    fmt.print_cost_prediction(prediction)
    fmt.print_model_result(result)
    fmt.print_comparison(report)
"""

import sys
from typing import Any, Dict, List, Optional

# ── ANSI color helpers (no dependencies) ─────────────────────────────────
_COLORS = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "red":     "\033[91m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
    "bg_blue": "\033[44m",
}

# Detect color support
_COLOR_ENABLED = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _c(color: str, text: str) -> str:
    """Apply ANSI color if supported."""
    if not _COLOR_ENABLED:
        return text
    return f"{_COLORS.get(color, '')}{text}{_COLORS['reset']}"


# ── Unicode icons (safe for Windows Terminal / modern consoles) ──────────
class Icons:
    CHECK    = "[OK]"
    CROSS    = "[X]"
    WARN     = "[!]"
    INFO     = "[i]"
    ROCKET   = "[>]"
    CHART    = "[#]"
    MONEY    = "[$]"
    CLOCK    = "[T]"
    BRAIN    = "[*]"
    SHIELD   = "[S]"
    SPARK    = "[+]"
    ARROW    = "->"
    DOT      = " * "

    # Try Unicode if encoding supports it
    @classmethod
    def init_unicode(cls):
        try:
            "✓".encode(sys.stdout.encoding or "utf-8")
            cls.CHECK  = "✓"
            cls.CROSS  = "✗"
            cls.WARN   = "⚠"
            cls.INFO   = "ℹ"
            cls.ROCKET = "🚀"
            cls.CHART  = "📊"
            cls.MONEY  = "💰"
            cls.CLOCK  = "⏱"
            cls.BRAIN  = "🧠"
            cls.SHIELD = "🛡"
            cls.SPARK  = "✨"
            cls.ARROW  = "→"
            cls.DOT    = "•"
        except (UnicodeEncodeError, LookupError):
            pass

Icons.init_unicode()


class CLIFormatter:
    """Beautiful CLI output formatter."""

    def __init__(self, width: int = 70):
        self.width = width

    # ── Basic elements ───────────────────────────────────────────────────

    def divider(self, char: str = "─", label: str = ""):
        """Print a divider line."""
        if label:
            padding = (self.width - len(label) - 4) // 2
            line = f"  {'─' * padding} {label} {'─' * padding}"
        else:
            line = f"  {char * self.width}"
        print(_c("dim", line))

    def print_header(self, title: str, subtitle: str = ""):
        """Print a bold header block."""
        print()
        print(_c("bold", f"  {'=' * self.width}"))
        print(_c("bold", f"  {Icons.ROCKET}  {title}"))
        if subtitle:
            print(_c("dim", f"     {subtitle}"))
        print(_c("bold", f"  {'=' * self.width}"))
        print()

    def print_section(self, title: str):
        """Print a section header."""
        print()
        self.divider(label=title)
        print()

    def print_kv(self, key: str, value: Any, indent: int = 4):
        """Print a key-value pair."""
        prefix = " " * indent
        print(f"{prefix}{_c('cyan', key + ':')} {value}")

    def print_status(self, message: str, status: str = "ok"):
        """Print a status line with icon."""
        icon = {
            "ok": _c("green", Icons.CHECK),
            "error": _c("red", Icons.CROSS),
            "warn": _c("yellow", Icons.WARN),
            "info": _c("blue", Icons.INFO),
        }.get(status, Icons.INFO)
        print(f"  {icon}  {message}")

    def print_score_bar(self, label: str, score: float, max_score: float = 10.0, width: int = 30):
        """Print a visual score bar."""
        filled = int((score / max_score) * width)
        empty = width - filled
        color = "green" if score >= 7 else "yellow" if score >= 4 else "red"
        bar = _c(color, "█" * filled) + _c("dim", "░" * empty)
        print(f"    {label:15s}  {bar}  {_c('bold', f'{score:.1f}')}/{max_score:.0f}")

    # ── High-level formatted outputs ─────────────────────────────────────

    def print_cost_prediction(self, prediction: Dict[str, Any]):
        """Print cost prediction before execution."""
        self.print_section(f"{Icons.MONEY}  Cost Prediction")
        self.print_kv("Complexity", _c("bold", prediction.get("complexity", "unknown")))
        self.print_kv("Prompt tokens (est.)", prediction.get("prompt_tokens_est", "?"))
        self.print_kv("Response tokens (est.)", prediction.get("response_tokens_est", "?"))
        self.print_kv("Total tokens (est.)", prediction.get("total_tokens_est", "?"))
        
        cost = prediction.get("cost_estimate_usd", 0)
        cost_str = f"${cost:.6f}" if cost > 0 else _c("green", "FREE")
        self.print_kv("Estimated cost", cost_str)
        self.print_kv("Estimated latency", f"{prediction.get('latency_estimate_seconds', '?')}s")
        self.print_kv("Recommended model", _c("bold", prediction.get("recommended_model", "?")))

        alts = prediction.get("alternative_models", [])
        if alts:
            print(f"\n    {_c('dim', 'Alternative models:')}")
            for alt in alts[:3]:
                alt_cost = alt.get("cost_estimate", 0)
                cost_txt = f"${alt_cost:.6f}" if alt_cost > 0 else "FREE"
                print(f"      {Icons.DOT} {alt['model'][:45]:45s}  {cost_txt}  ~{alt.get('latency_estimate', '?')}s")
        print()

    def print_model_result(self, result: Dict[str, Any]):
        """Print a single model's response with metadata."""
        model = result.get("model_name", result.get("model", "Unknown"))
        self.print_section(f"{Icons.BRAIN}  Response from {model}")

        # Metadata
        latency = result.get("latency_seconds", result.get("latency_ms", 0))
        if latency > 100:
            latency = latency / 1000  # convert ms to s
        self.print_kv("Model", model)
        self.print_kv("Latency", f"{latency:.2f}s")
        cost = result.get("cost_estimate", 0)
        self.print_kv("Cost", f"${cost:.6f}" if cost > 0 else _c("green", "FREE"))

        tokens_out = result.get("output_tokens_est", result.get("tokens_used", "?"))
        self.print_kv("Tokens (output)", tokens_out)

        success = result.get("success", True)
        self.print_kv("Status", _c("green", "Success") if success else _c("red", "Failed"))

        # Answer
        text = result.get("response_text", result.get("text", result.get("answer", "")))
        if text:
            print(f"\n    {_c('bold', 'Answer:')}")
            for line in text.split('\n'):
                print(f"      {line}")
        else:
            error = result.get("error", "No response")
            print(f"\n    {_c('red', f'Error: {error}')}")
        print()

    def print_comparison(self, report: Dict[str, Any]):
        """Print multi-model comparison report with beautiful boxed layout."""
        prompt_display = report.get('prompt', '')[:60]
        self.print_header("Multi-Model Comparison", f"Prompt: \"{prompt_display}...\"")

        # Show optimized prompt if used
        opt_prompt = report.get("optimized_prompt")
        if opt_prompt:
            print(f"    {_c('green', Icons.CHECK)} Prompt was auto-optimized before sending to models")
            opt_display = opt_prompt[:100].replace('\n', ' ')
            print(f"    {_c('dim', opt_display)}{'...' if len(opt_prompt) > 100 else ''}")
            print()

        # Consistency
        consistency = report.get("consistency_score", 0)
        color = "green" if consistency > 0.5 else "yellow" if consistency > 0.2 else "red"
        self.print_kv("Models compared", len(report.get("models", [])))
        self.print_kv("Consistency", _c(color, f"{consistency:.0%}"))
        print()

        # ── Rankings Table ───────────────────────────────────────────────
        self.divider(label="Rankings")
        ranking = report.get("ranking", [])
        print(f"    {'#':3s} {'Model':45s} {'Score':8s} {'Latency':10s} {'Cost':12s} {'Status':8s}")
        print(f"    {'─'*3} {'─'*45} {'─'*8} {'─'*10} {'─'*12} {'─'*8}")
        for i, r in enumerate(ranking, 1):
            model_name = r.get("model", "?")[:45]
            score = r.get("score", 0)
            latency = r.get("latency", "?")
            cost = r.get("cost", 0)
            status = r.get("status", "?")
            
            score_color = "green" if score > 0.7 else "yellow" if score > 0.4 else "red"
            status_icon = _c("green", Icons.CHECK) if status == "success" else _c("red", Icons.CROSS)
            cost_str = f"${cost:.6f}" if cost > 0 else "FREE"
            
            # Medal for top
            medal = {1: _c("yellow", "🥇"), 2: _c("white", "🥈"), 3: _c("yellow", "🥉")}.get(i, f" {i}")
            
            print(f"    {medal:3s} {model_name:45s} {_c(score_color, f'{score:.2f}'):8s} {str(latency)+'s':10s} {cost_str:12s} {status_icon}")
        print()

        # ── Boxed Responses ──────────────────────────────────────────────
        self.divider(label="Model Responses")
        print()

        results = report.get("results", [])
        for idx, res in enumerate(results):
            if not isinstance(res, dict):
                continue
            model = res.get("model_name", res.get("model", "Unknown"))
            success = res.get("success", False)
            text = res.get("response_text", res.get("text", ""))
            latency = res.get("latency_seconds", 0)
            tokens = res.get("output_tokens_est", 0)
            cost = res.get("cost_estimate", 0)
            
            # Find this model's rank
            rank_num = idx + 1
            rank_score = 0
            for r in ranking:
                if r.get("model") == model:
                    rank_num = ranking.index(r) + 1
                    rank_score = r.get("score", 0)
                    break
            
            # Box header
            box_width = self.width + 2
            rank_badge = {1: "🥇 BEST", 2: "🥈 2nd", 3: "🥉 3rd"}.get(rank_num, f"#{rank_num}")
            
            # Short model name
            short_name = model.split("/")[-1] if "/" in model else model
            
            header_text = f"  {rank_badge}  {short_name}"
            score_text = f"Score: {rank_score:.2f}"
            
            print(f"  {_c('bold', '┌' + '─' * box_width + '┐')}")
            print(f"  {_c('bold', '│')} {_c('cyan', header_text):<{box_width + 10}s}{_c('bold', score_text):>10s} {_c('bold', '│')}")
            
            # Metadata line
            cost_str = f"${cost:.6f}" if cost > 0 else "FREE"
            meta_text = f"  Latency: {latency:.1f}s  │  Tokens: {tokens}  │  Cost: {cost_str}"
            status_text = _c("green", "Success") if success else _c("red", "Failed")
            print(f"  {_c('bold', '│')} {_c('dim', meta_text):<{box_width + 10}s}{status_text:>10s} {_c('bold', '│')}")
            print(f"  {_c('bold', '├' + '─' * box_width + '┤')}")
            
            if success and text:
                # Wrap and display response text
                lines = text.strip().split('\n')
                max_lines = 15
                for line_idx, line in enumerate(lines[:max_lines]):
                    # Truncate long lines
                    display_line = line[:box_width - 2] if len(line) > box_width - 2 else line
                    padding = box_width - len(display_line)
                    print(f"  {_c('bold', '│')} {display_line}{' ' * max(0, padding)}{_c('bold', '│')}")
                
                if len(lines) > max_lines:
                    remaining = len(lines) - max_lines
                    trunc_msg = f"  ... ({remaining} more lines)"
                    padding = box_width - len(trunc_msg)
                    print(f"  {_c('bold', '│')} {_c('dim', trunc_msg)}{' ' * max(0, padding)}{_c('bold', '│')}")
            else:
                error = res.get("error", "No response")
                err_text = f"  Error: {error[:box_width - 12]}"
                padding = box_width - len(err_text)
                print(f"  {_c('bold', '│')} {_c('red', err_text)}{' ' * max(0, padding)}{_c('bold', '│')}")
            
            print(f"  {_c('bold', '└' + '─' * box_width + '┘')}")
            print()

    def print_prompt_analysis(self, analysis: Dict[str, Any]):
        """Print prompt quality analysis."""
        self.print_section(f"{Icons.SPARK}  Prompt Analysis")
        
        grade = analysis.get("quality_grade", "?")
        grade_color = {"A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red"}.get(grade, "white")
        self.print_kv("Quality Grade", _c(grade_color, f"  {grade}  "))
        self.print_kv("Word count", analysis.get("word_count", 0))
        self.print_kv("Intent", analysis.get("detected_intent", "unknown"))
        
        self.print_score_bar("Specificity", analysis.get("specificity_score", 0) * 10)
        self.print_score_bar("Vagueness", analysis.get("vagueness_score", 0) * 10)
        self.print_score_bar("Ambiguity", analysis.get("ambiguity_score", 0) * 10)

        suggestions = analysis.get("suggested_improvements", [])
        if suggestions:
            print(f"\n    {_c('yellow', 'Suggestions:')}")
            for s in suggestions:
                print(f"      {Icons.ARROW} {s}")

        constraints = analysis.get("auto_constraints", [])
        if constraints:
            print(f"\n    {_c('cyan', 'Auto-constraints to add:')}")
            for c in constraints:
                print(f"      {Icons.DOT} {c}")
        print()

    def print_optimization_summary(self, results: Dict[str, Any]):
        """Print comprehensive optimization results with grades and trends."""
        self.print_header("Optimization Results", "Self-Improving LLM System")

        # ── Overview Panel ───────────────────────────────────────────────
        initial = results.get("initial_score", 0)
        final = results.get("final_score", 0)
        best = results.get("best_score", final)
        improvement = results.get("improvement", 0)
        iterations = results.get("iterations", 0)
        converged = results.get("converged", False)

        # Letter grade
        grade = "A+" if final >= 9 else "A" if final >= 8 else "B" if final >= 7 else "C" if final >= 5 else "D" if final >= 3 else "F"
        grade_color = "green" if grade.startswith("A") else "green" if grade == "B" else "yellow" if grade == "C" else "red"
        grade_icon = "Excellent!" if grade.startswith("A") else "Good" if grade == "B" else "Fair" if grade == "C" else "Needs work"

        print(f"    {_c('bold', 'Overall Grade:')}  {_c(grade_color, f'  {grade}  ')}  {_c(grade_color, grade_icon)}")
        print()
        self.print_kv("Initial Score", f"{initial:.1f}/10")
        self.print_kv("Final Score", _c("bold", f"{final:.1f}/10"))
        self.print_kv("Best Score", _c("bold", f"{best:.1f}/10"))
        imp_color = "green" if improvement > 0 else "red" if improvement < 0 else "yellow"
        imp_icon = Icons.CHECK if improvement > 0 else Icons.CROSS if improvement < -0.3 else Icons.WARN
        self.print_kv("Change", f"{_c(imp_color, f'{improvement:+.1f}')}  {imp_icon}")
        self.print_kv("Iterations", iterations)
        self.print_kv("Status", _c("green", "Converged") if converged else _c("yellow", "Stopped (max iterations)"))

        # Plain-English summary
        summary = results.get("summary", "")
        if summary:
            print()
            print(f"    {_c('cyan', 'Summary:')} {summary}")

        # ── Score Progress ───────────────────────────────────────────────
        history = results.get("performance_history", [])
        if history:
            print()
            self.divider(label="Score Progress")
            for i, score in enumerate(history, 1):
                change = ""
                if i > 1:
                    diff = score - history[i - 2]
                    diff_color = "green" if diff > 0 else "red" if diff < 0 else "dim"
                    change = f"  {_c(diff_color, f'{diff:+.1f}')}"
                self.print_score_bar(f"Iter {i}", score)
                if change:
                    # Print change indicator next to the bar
                    pass  # The score_bar already shows the score

        # ── Criteria Trend ───────────────────────────────────────────────
        criteria_trend = results.get("criteria_trend", {})
        if criteria_trend:
            print()
            self.divider(label="Criteria Breakdown (First vs Last)")
            print(f"    {'Criterion':<15s} {'Initial':>8s} {'Final':>8s} {'Change':>8s}  {'Trend':>6s}")
            print(f"    {'─' * 55}")
            for criterion, trend in criteria_trend.items():
                init_val = trend.get("initial", 0)
                final_val = trend.get("final", 0)
                change_val = trend.get("change", 0)
                trend_icon = _c("green", "  UP") if change_val > 0.3 else _c("red", "DOWN") if change_val < -0.3 else _c("dim", "SAME")
                change_color = "green" if change_val > 0 else "red" if change_val < 0 else "dim"
                print(f"    {criterion.capitalize():<15s} {init_val:>7.1f} {final_val:>7.1f}  {_c(change_color, f'{change_val:>+6.1f}')}  {trend_icon}")
            print()

        # ── Per-Iteration Details ────────────────────────────────────────
        iteration_details = results.get("iteration_details", [])
        if iteration_details:
            print()
            self.divider(label="Per-Question Scores (Last Iteration)")
            last_iter = iteration_details[-1]
            pq_scores = last_iter.get("per_question_scores", [])
            if pq_scores:
                print(f"    {'#':3s} {'Question':<40s} {'Score':>7s} {'Grade':>6s}")
                print(f"    {'─' * 60}")
                for idx, pq in enumerate(pq_scores, 1):
                    q_text = pq.get("question", "?")
                    if len(q_text) > 38:
                        q_text = q_text[:35] + "..."
                    score = pq.get("composite_score", 0)
                    q_grade = "A" if score >= 8 else "B" if score >= 6 else "C" if score >= 4 else "D"
                    score_color = "green" if score >= 7 else "yellow" if score >= 4 else "red"
                    print(f"    {idx:3d} {q_text:<40s} {_c(score_color, f'{score:>5.1f}')}/10 {q_grade:>4s}")
                print()
    
            # Weak/strong criteria for last iteration
            weak = last_iter.get("weak_criteria", [])
            strong = last_iter.get("strong_criteria", [])
            if strong:
                print(f"    {_c('green', 'Strengths:')} {', '.join(c.capitalize() for c in strong)}")
            if weak:
                print(f"    {_c('red', 'Needs work:')} {', '.join(c.capitalize() for c in weak)}")
            
            # Duration
            duration = last_iter.get("duration_seconds", 0)
            if duration > 0:
                self.print_kv("Last iteration", f"{duration:.1f}s")
        print()

    def print_developer_info(self, debug_entries: List[Dict[str, Any]]):
        """Print developer-mode debug information."""
        self.print_header("Developer Mode Debug Output")

        for entry in debug_entries:
            entry_type = entry.get("entry_type", "?")
            agent = entry.get("agent", "?")
            label = entry.get("label", "")
            content = entry.get("content", "")
            ts = entry.get("timestamp", "")[:19]

            type_icon = {
                "prompt": Icons.ROCKET,
                "response": Icons.CHECK,
                "chain_of_thought": Icons.BRAIN,
                "debug": Icons.INFO,
                "metric": Icons.CHART,
            }.get(entry_type, Icons.DOT)

            color = {
                "prompt": "cyan",
                "response": "green",
                "chain_of_thought": "magenta",
                "debug": "dim",
                "metric": "yellow",
            }.get(entry_type, "white")

            print(f"  {_c(color, f'{type_icon} [{entry_type.upper()}]')} {agent} {_c('dim', ts)}")
            print(f"    {_c('dim', label)}")
            
            if isinstance(content, dict):
                import json
                content_str = json.dumps(content, indent=2, default=str)
            else:
                content_str = str(content)
            
            # Truncate for display
            lines = content_str.split('\n')
            for line in lines[:15]:
                print(f"      {line}")
            if len(lines) > 15:
                print(f"      {_c('dim', f'... ({len(lines) - 15} more lines)')}")
            print()

    def print_router_stats(self, stats: Dict[str, Any]):
        """Print smart router statistics."""
        self.print_section(f"{Icons.CHART}  Router Statistics")
        self.print_kv("Total routings", stats.get("total_routings", 0))
        self.print_kv("Total cost", f"${stats.get('total_cost', 0):.4f}")

        models = stats.get("models", {})
        if models:
            print(f"\n    {'Model':45s} {'Uses':6s} {'Avg Score':10s} {'Success':8s}")
            print(f"    {'─'*45} {'─'*6} {'─'*10} {'─'*8}")
            for model, data in sorted(models.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True):
                name = model[:45]
                uses = data.get("uses", 0)
                avg = data.get("avg_score", 0)
                success_rate = data.get("success_rate", 0)
                print(f"    {name:45s} {uses:6d} {avg:10.2f} {success_rate:7.0%}")
        print()
