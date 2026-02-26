"""
Prompt Optimization Engine

Automatically improves prompts before sending them to LLMs:
1. Detects vague / ambiguous prompts
2. Rewrites prompts for clarity
3. Adds constraints dynamically
4. Maintains prompt history for learning
5. Suggests improvements

Usage:
    from utils.prompt_engine import PromptEngine
    engine = PromptEngine()

    analysis = engine.analyze(user_prompt)
    improved  = engine.optimize(user_prompt)
    engine.record_outcome(user_prompt, improved, score)
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import Counter

import logging
logger = logging.getLogger(__name__)


# ── Vagueness signals ────────────────────────────────────────────────────────
_VAGUE_WORDS = {
    "something", "stuff", "thing", "things", "it", "that", "etc",
    "whatever", "somehow", "anything", "some", "good", "nice",
    "better", "improve", "help", "fix", "do",
}
_VAGUE_PATTERNS = [
    re.compile(r'^\w{1,4}\??$'),                    # very short prompts
    re.compile(r'^(hi|hello|hey|yo|sup)\b', re.I),  # greetings without question
    re.compile(r'\?\s*$'),                            # ends with ? but no context
]
_AMBIGUOUS_PATTERNS = [
    re.compile(r'\b(this|that|it|they)\b(?! (is|are|was|were|means?))', re.I),
    re.compile(r'\b(right|kind of|sort of|maybe|probably|I guess)\b', re.I),
]

# ── Enhancement templates ────────────────────────────────────────────────────
_CONSTRAINT_TEMPLATES = {
    "step_by_step": "\nPlease explain your reasoning step-by-step.",
    "concise": "\nKeep your answer concise (under 200 words).",
    "examples": "\nProvide at least one concrete example.",
    "format_json": "\nRespond in valid JSON format.",
    "format_markdown": "\nFormat your response using Markdown headers and lists.",
    "audience_beginner": "\nExplain as if to a beginner with no technical background.",
    "audience_expert": "\nAssume the reader has expert-level domain knowledge.",
    "cite_sources": "\nCite any sources or references where applicable.",
    "pros_cons": "\nInclude pros/cons or trade-offs in your analysis.",
}


@dataclass
class PromptAnalysis:
    """Analysis of a user prompt."""
    original_prompt: str
    word_count: int
    sentence_count: int
    vagueness_score: float       # 0-1 (1 = very vague)
    ambiguity_score: float       # 0-1
    specificity_score: float     # 0-1 (1 = very specific)
    has_question: bool
    has_context: bool
    has_constraints: bool
    detected_intent: str         # question, instruction, conversation, code
    suggested_improvements: List[str]
    auto_constraints: List[str]  # keys from _CONSTRAINT_TEMPLATES
    quality_grade: str           # A, B, C, D, F
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PromptRecord:
    """Historical record of prompt optimization attempts."""
    original: str
    optimized: str
    outcome_score: Optional[float]  # quality score from judge (0-10)
    timestamp: str
    improvements_applied: List[str]


class PromptEngine:
    """
    Automatic prompt improvement engine.
    """

    def __init__(self, history_path: str = "./output/prompt_history.json"):
        self.history_path = Path(history_path)
        self.history: List[PromptRecord] = []
        self._load_history()

    # ── 1. Analyze prompt quality ─────────────────────────────────────────

    def analyze(self, prompt: str) -> PromptAnalysis:
        """Analyze a prompt and return quality metrics + suggestions."""
        words = prompt.split()
        word_count = len(words)
        sentence_count = max(1, prompt.count('.') + prompt.count('?') + prompt.count('!'))

        vagueness = self._compute_vagueness(prompt, words)
        ambiguity = self._compute_ambiguity(prompt)
        specificity = 1.0 - (vagueness * 0.6 + ambiguity * 0.4)
        has_question = '?' in prompt
        has_context = word_count > 20
        has_constraints = bool(re.search(
            r'\b(must|should|at least|no more than|format|step|example|concise)\b',
            prompt, re.I
        ))
        intent = self._detect_intent(prompt)
        suggestions = self._suggest_improvements(
            prompt, vagueness, ambiguity, has_question, has_context, has_constraints, intent
        )
        auto_constraints = self._select_auto_constraints(
            prompt, vagueness, has_constraints, intent
        )

        # Quality grade
        overall = specificity * 0.4 + (1 if has_context else 0) * 0.2 + (1 if has_constraints else 0) * 0.2 + (1 - vagueness) * 0.2
        if overall >= 0.8:
            grade = "A"
        elif overall >= 0.6:
            grade = "B"
        elif overall >= 0.4:
            grade = "C"
        elif overall >= 0.2:
            grade = "D"
        else:
            grade = "F"

        return PromptAnalysis(
            original_prompt=prompt,
            word_count=word_count,
            sentence_count=sentence_count,
            vagueness_score=round(vagueness, 2),
            ambiguity_score=round(ambiguity, 2),
            specificity_score=round(specificity, 2),
            has_question=has_question,
            has_context=has_context,
            has_constraints=has_constraints,
            detected_intent=intent,
            suggested_improvements=suggestions,
            auto_constraints=auto_constraints,
            quality_grade=grade,
            timestamp=datetime.now().isoformat(),
        )

    # ── 2. Optimize prompt ────────────────────────────────────────────────

    def optimize(self, prompt: str, add_constraints: Optional[List[str]] = None) -> str:
        """
        Rewrite the prompt for clarity and add appropriate constraints.
        Returns the improved prompt.
        """
        analysis = self.analyze(prompt)
        improved = prompt.strip()
        improvements_applied = []
        intent = analysis.detected_intent

        # ── Code-specific optimization ───────────────────────────────────
        if intent == "code":
            improved = self._optimize_code_prompt(improved, analysis)
            improvements_applied.append("code_prompt_enhanced")
        else:
            # 1. If too short, expand into a full question
            if analysis.word_count < 5 and not analysis.has_question:
                improved = f"Please provide a detailed explanation about: {improved}"
                improvements_applied.append("expanded_short_prompt")

            # 2. Add question mark if it looks like a question but lacks one
            if not analysis.has_question and re.match(r'^(what|who|where|when|why|how|can|does|is|are)\b', improved, re.I):
                improved = improved.rstrip('.') + '?'
                improvements_applied.append("added_question_mark")

            # 3. Add explicit instruction if it's just a keyword
            if analysis.word_count <= 2:
                improved = f"Explain the concept of '{improved}' clearly with examples."
                improvements_applied.append("keyword_to_instruction")

            # 4. Clarify vague pronouns
            if analysis.ambiguity_score > 0.5:
                improved += "\n\nNote: Please provide specific details rather than general statements."
                improvements_applied.append("clarify_ambiguity")

        # 5. Auto-add constraints based on analysis
        constraints_to_add = add_constraints or analysis.auto_constraints
        for key in constraints_to_add:
            if key in _CONSTRAINT_TEMPLATES:
                constraint_text = _CONSTRAINT_TEMPLATES[key]
                if constraint_text.strip() not in improved:
                    improved += constraint_text
                    improvements_applied.append(f"constraint:{key}")

        # 6. Record for learning
        self.history.append(PromptRecord(
            original=prompt,
            optimized=improved,
            outcome_score=None,
            timestamp=datetime.now().isoformat(),
            improvements_applied=improvements_applied,
        ))

        return improved

    def _optimize_code_prompt(self, prompt: str, analysis: 'PromptAnalysis') -> str:
        """Specialized optimization for code-related prompts."""
        p_lower = prompt.lower()
        improved = prompt.strip()

        # Detect programming language
        languages = {
            "python": ["python", "py", "django", "flask", "pandas", "numpy"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular", "typescript", "ts"],
            "java": ["java", "spring", "maven"],
            "c++": ["c++", "cpp"],
            "c#": ["c#", "csharp", ".net"],
            "rust": ["rust"],
            "go": ["golang", " go "],
            "sql": ["sql", "query", "database", "mysql", "postgres"],
            "html/css": ["html", "css", "webpage"],
        }
        detected_lang = None
        for lang, keywords in languages.items():
            if any(kw in p_lower for kw in keywords):
                detected_lang = lang
                break

        # Detect code task type
        task_type = "code snippet"
        task_keywords = {
            "function": ["function", "method", "def ", "func"],
            "class": ["class", "object", "oop"],
            "algorithm": ["algorithm", "sort", "search", "traverse", "recursive"],
            "api": ["api", "endpoint", "rest", "request", "fetch"],
            "debug": ["debug", "fix", "error", "bug", "issue"],
            "refactor": ["refactor", "optimize", "improve", "clean"],
            "full program": ["program", "project", "app", "application", "script"],
        }
        for task, keywords in task_keywords.items():
            if any(kw in p_lower for kw in keywords):
                task_type = task
                break

        # Build enhanced code prompt
        parts = [improved]

        # Add language specification if not already mentioned
        if detected_lang:
            if detected_lang.lower() not in p_lower:
                parts.append(f"\nProgramming language: {detected_lang}")

        # Add code-specific requirements
        requirements = [
            "\nRequirements:",
            "- Provide complete, working code (not pseudo-code)",
            "- Include brief inline comments explaining key logic",
            "- Handle common edge cases",
        ]

        if task_type == "function":
            requirements.extend([
                "- Include the function signature with type hints/annotations",
                "- Show a usage example with sample input/output",
            ])
        elif task_type == "class":
            requirements.extend([
                "- Include constructor, key methods, and docstrings",
                "- Show a brief usage example",
            ])
        elif task_type == "algorithm":
            requirements.extend([
                "- State the time and space complexity (Big-O)",
                "- Include a step-by-step explanation of the approach",
            ])
        elif task_type == "api":
            requirements.extend([
                "- Include request/response format",
                "- Show error handling",
            ])
        elif task_type == "debug":
            requirements.extend([
                "- Explain what causes the issue",
                "- Show the corrected code",
                "- Explain what was changed and why",
            ])

        requirements.append("- Format code inside markdown code blocks with language tag")
        parts.extend(requirements)

        return "\n".join(parts)

    def record_outcome(self, original: str, optimized: str, score: float):
        """Record the quality score for a previous optimization (for learning)."""
        for record in reversed(self.history):
            if record.original == original and record.optimized == optimized:
                record.outcome_score = score
                break
        self._save_history()

    # ── Internal helpers ──────────────────────────────────────────────────

    def _compute_vagueness(self, prompt: str, words: List[str]) -> float:
        """0-1 vagueness score."""
        if not words:
            return 1.0

        # Short prompt penalty
        length_score = min(len(words) / 15, 1.0)
        vague_word_ratio = sum(1 for w in words if w.lower() in _VAGUE_WORDS) / len(words)
        pattern_hits = sum(1 for p in _VAGUE_PATTERNS if p.search(prompt))

        vagueness = (1 - length_score) * 0.4 + vague_word_ratio * 0.3 + min(pattern_hits / 3, 1.0) * 0.3
        return min(max(vagueness, 0), 1.0)

    def _compute_ambiguity(self, prompt: str) -> float:
        """0-1 ambiguity score."""
        hits = sum(1 for p in _AMBIGUOUS_PATTERNS if p.search(prompt))
        return min(hits / 4, 1.0)

    def _detect_intent(self, prompt: str) -> str:
        """Classify prompt intent."""
        p = prompt.lower()
        code_keywords = ["code", "function", "class", "implement", "debug", "program", "script", "api"]
        if any(k in p for k in code_keywords):
            return "code"
        if '?' in prompt:
            return "question"
        instruction_keywords = ["write", "create", "generate", "make", "build", "design"]
        if any(k in p for k in instruction_keywords):
            return "instruction"
        return "conversation"

    def _suggest_improvements(
        self, prompt: str, vagueness: float, ambiguity: float,
        has_question: bool, has_context: bool, has_constraints: bool, intent: str
    ) -> List[str]:
        """Generate human-readable suggestions."""
        suggestions = []
        if vagueness > 0.6:
            suggestions.append("Your prompt is vague. Add more specific details about what you need.")
        if ambiguity > 0.5:
            suggestions.append("Avoid ambiguous pronouns (it, that, this). Be explicit.")
        if not has_question and intent == "question":
            suggestions.append("Phrase your request as a clear question.")
        if not has_context:
            suggestions.append("Add context or background information for better results.")
        if not has_constraints:
            suggestions.append("Add constraints like desired format, length, or audience level.")
        if intent == "code":
            suggestions.append("Specify the programming language, input/output format, and edge cases.")
        if len(prompt) < 10:
            suggestions.append("Your prompt is very short. Expand it to get a better response.")
        return suggestions

    def _select_auto_constraints(
        self, prompt: str, vagueness: float, has_constraints: bool, intent: str
    ) -> List[str]:
        """Select constraints to auto-add."""
        constraints = []
        if not has_constraints and vagueness > 0.3:
            constraints.append("step_by_step")
        if intent == "question" and "example" not in prompt.lower():
            constraints.append("examples")
        if intent == "code":
            constraints.append("format_markdown")
        if vagueness > 0.5:
            constraints.append("concise")
        return constraints

    # ── Persistence ──────────────────────────────────────────────────────

    def _save_history(self):
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(r) for r in self.history[-200:]], f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save prompt history: {e}")

    def _load_history(self):
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.history = [PromptRecord(**r) for r in data]
                logger.info(f"Loaded {len(self.history)} prompt records")
            except Exception as e:
                logger.warning(f"Could not load prompt history: {e}")

    # ── Learning insights ────────────────────────────────────────────────

    def get_learning_stats(self) -> Dict[str, Any]:
        """Return insights from prompt optimization history."""
        scored = [r for r in self.history if r.outcome_score is not None]
        if not scored:
            return {"total_optimizations": len(self.history), "scored": 0}

        all_improvements = []
        for r in scored:
            all_improvements.extend(r.improvements_applied)

        improvement_scores: Dict[str, List[float]] = {}
        for r in scored:
            for imp in r.improvements_applied:
                improvement_scores.setdefault(imp, []).append(r.outcome_score)

        avg_by_improvement = {
            k: round(sum(v) / len(v), 2)
            for k, v in improvement_scores.items()
        }

        return {
            "total_optimizations": len(self.history),
            "scored": len(scored),
            "avg_score": round(sum(r.outcome_score for r in scored) / len(scored), 2),
            "best_improvements": sorted(avg_by_improvement.items(), key=lambda x: x[1], reverse=True),
            "most_used_improvements": Counter(all_improvements).most_common(10),
        }
