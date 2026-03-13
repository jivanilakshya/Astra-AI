"""
Prompt Template Library — Langflow-inspired Prompt Components

Auto-selects the best template based on question category, intent,
and complexity.  Users can also manually choose a template.

Inspired by: https://docs.langflow.org/components-prompts

Each template has:
  - id / name / description
  - category tags  (which question categories it fits)
  - intent tags    (question, code, reasoning, creative, comparison, ...)
  - complexity     (simple, moderate, complex)
  - template text  (must contain {question} placeholder)
  - structured output instructions (so answers are formatted)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

# ── Template dataclass ────────────────────────────────────────────────────────

@dataclass
class PromptTemplate:
    id: str
    name: str
    description: str
    template: str
    categories: List[str] = field(default_factory=list)       # matching question categories
    intents: List[str] = field(default_factory=list)           # question / code / reasoning / ...
    complexity: str = "moderate"                                # simple / moderate / complex
    output_format: str = "structured"                           # structured / freeform / json / markdown
    is_default: bool = False

    def render(self, question: str, **kwargs: Any) -> str:
        """Render the template with the given question + optional extras."""
        text = self.template.replace("{question}", question)
        for k, v in kwargs.items():
            text = text.replace(f"{{{k}}}", str(v))
        return text

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Built-in templates ────────────────────────────────────────────────────────

PROMPT_TEMPLATES: Dict[str, PromptTemplate] = {}


def _register(t: PromptTemplate) -> PromptTemplate:
    PROMPT_TEMPLATES[t.id] = t
    return t


# ---- 1. General Q&A ----
_register(PromptTemplate(
    id="general_qa",
    name="General Q&A",
    description="Clear, structured answer for general-knowledge questions",
    is_default=True,
    categories=["biology", "physics", "chemistry", "earth_science", "astronomy",
                "economics", "history", "mathematics", "general", "logic"],
    intents=["question"],
    complexity="moderate",
    output_format="structured",
    template="""You are a knowledgeable expert. Answer the question accurately with a well-structured explanation.

Question: {question}

Provide your response in the following structured format:

**Answer:**
<A clear, direct answer to the question>

**Detailed Explanation:**
<A thorough explanation with key concepts, step-by-step reasoning, and relevant details>

**Key Points:**
- <Important point 1>
- <Important point 2>
- <Important point 3>

**Example (if applicable):**
<A real-world example or analogy to illustrate the concept>

Make sure your answer is:
- Factually accurate and well-researched
- Clear enough for someone unfamiliar with the topic
- Comprehensive but not unnecessarily verbose""",
))


# ---- 2. Scientific Explanation ----
_register(PromptTemplate(
    id="scientific",
    name="Scientific Explanation",
    description="Detailed scientific explanation with evidence and methodology",
    categories=["biology", "physics", "chemistry", "earth_science", "astronomy", "mathematics"],
    intents=["question", "reasoning"],
    complexity="complex",
    output_format="structured",
    template="""You are a scientist providing an expert-level explanation. Be precise and evidence-based.

Question: {question}

Provide your response in this structured format:

**Scientific Answer:**
<Direct, precise answer using correct scientific terminology>

**Underlying Principles:**
<The fundamental scientific principles that govern this phenomenon>

**Mechanism / Process:**
<Step-by-step explanation of how this works, including any equations or models>

**Evidence & Examples:**
<Real-world examples, experimental evidence, or observations that support the answer>

**Common Misconceptions:**
<Address 1-2 widespread misconceptions about this topic>

**Further Reading:**
<Suggest 1-2 topics for deeper exploration>

Requirements:
- Use proper scientific terminology with brief definitions
- Include quantitative details where applicable
- Reference established scientific principles
- Be accurate (avoid oversimplification that sacrifices correctness)""",
))


# ---- 3. Code Generation ----
_register(PromptTemplate(
    id="code_generation",
    name="Code Generation",
    description="Produce working code with explanation, tests, and best practices",
    categories=["code_python", "code_javascript", "code_java", "code_cpp",
                "code_sql", "code_rust", "code_debug", "code_refactor",
                "code_api", "code_html_css", "computer_science"],
    intents=["code"],
    complexity="complex",
    output_format="markdown",
    template="""You are an expert software engineer. Write clean, production-quality code.

Task: {question}

Provide your response in this format:

**Approach:**
<Brief description of your solution strategy and algorithm choice>

**Code:**
```
<Complete, working code with inline comments on key logic>
```

**Explanation:**
<Line-by-line walkthrough of the important parts>

**Usage Example:**
```
<Show how to call/use the code with sample input and expected output>
```

**Edge Cases Handled:**
- <Edge case 1 and how it's handled>
- <Edge case 2 and how it's handled>

**Time & Space Complexity:**
- Time: O(…)
- Space: O(…)

Requirements:
- Code must be complete and runnable (not pseudo-code)
- Include type hints / annotations where the language supports them
- Handle common edge cases (empty input, null values, boundary conditions)
- Follow the language's idiomatic style and naming conventions
- Add clear inline comments for complex logic""",
))


# ---- 4. Code Debugging ----
_register(PromptTemplate(
    id="code_debug",
    name="Code Debugging",
    description="Analyze code issues and provide fixes with explanation",
    categories=["code_debug", "code_python", "code_javascript", "code_java",
                "code_cpp", "code_refactor"],
    intents=["code", "reasoning"],
    complexity="complex",
    output_format="markdown",
    template="""You are a senior developer debugging code. Analyze the problem systematically.

Problem: {question}

Provide your response in this format:

**Bug Identification:**
<What is the root cause of the issue>

**Why It Happens:**
<Explain the underlying reason — is it a logic error, type error, off-by-one, race condition, etc.?>

**Fix:**
```
<Corrected code with the fix clearly marked>
```

**What Changed:**
- <Change 1: what was wrong → what the fix does>
- <Change 2: …>

**Prevention Tips:**
- <How to avoid this class of bug in future code>

Requirements:
- Identify ALL bugs, not just the first one
- Explain WHY each bug occurs, not just what to change
- Provide the full corrected code, not just snippets""",
))


# ---- 5. Comparison / Analysis ----
_register(PromptTemplate(
    id="comparison",
    name="Comparison & Analysis",
    description="Side-by-side comparison of concepts, technologies, or approaches",
    categories=["computer_science", "economics", "general", "logic"],
    intents=["comparison", "reasoning"],
    complexity="complex",
    output_format="structured",
    template="""You are an analytical expert. Provide a thorough, balanced comparison.

Question: {question}

Provide your response in this structured format:

**Summary:**
<One-paragraph overview of the comparison>

**Detailed Comparison:**

| Aspect | Option A | Option B |
|--------|----------|----------|
| Core Concept | ... | ... |
| Strengths | ... | ... |
| Weaknesses | ... | ... |
| Best Used When | ... | ... |
| Performance | ... | ... |

**Key Differences:**
1. <Most important difference with explanation>
2. <Second key difference>
3. <Third key difference>

**Similarities:**
- <What they share in common>

**Recommendation:**
<When to use each option, with reasoning>

Requirements:
- Be objective and balanced (no bias toward one option)
- Include concrete examples for each point
- Consider practical real-world implications""",
))


# ---- 6. Step-by-Step Reasoning ----
_register(PromptTemplate(
    id="step_by_step",
    name="Step-by-Step Reasoning",
    description="Chain-of-thought problem solving with explicit reasoning steps",
    categories=["mathematics", "logic", "physics", "computer_science"],
    intents=["reasoning", "question"],
    complexity="complex",
    output_format="structured",
    template="""You are a precise analytical thinker. Solve this problem step by step, showing all your reasoning.

Problem: {question}

Provide your response in this format:

**Understanding the Problem:**
<Restate the problem in your own words and identify what we need to find>

**Given Information:**
- <Fact 1>
- <Fact 2>

**Solution Steps:**

Step 1: <Description>
<Detailed work for this step>

Step 2: <Description>
<Detailed work for this step>

Step 3: <Description>
<Detailed work for this step>

(Continue as needed)

**Final Answer:**
<Clear, concise final answer>

**Verification:**
<Check your answer by working backwards or using an alternative method>

Requirements:
- Show ALL intermediate steps (don't skip "obvious" steps)
- Justify each logical transition
- If there are multiple valid approaches, mention them
- Double-check your arithmetic / logic""",
))


# ---- 7. Concise / Quick Answer ----
_register(PromptTemplate(
    id="concise",
    name="Quick & Concise",
    description="Short, direct answers without lengthy explanations",
    categories=["general", "biology", "physics", "chemistry", "history",
                "economics", "earth_science", "astronomy"],
    intents=["question"],
    complexity="simple",
    output_format="structured",
    template="""Answer the following question directly and concisely.

Question: {question}

**Answer:** <Direct answer in 1-3 sentences>

**Key Fact:** <The single most important thing to know>

Keep it brief — no more than 100 words total.""",
))


# ---- 8. Educational / Tutorial ----
_register(PromptTemplate(
    id="educational",
    name="Educational Tutorial",
    description="Teaching-oriented explanation with progressive difficulty",
    categories=["biology", "physics", "chemistry", "mathematics",
                "computer_science", "earth_science", "astronomy"],
    intents=["question", "reasoning"],
    complexity="complex",
    output_format="structured",
    template="""You are a patient, expert tutor. Explain this concept so that a student can truly understand it.

Topic: {question}

Provide your response in this format:

**Simple Explanation (ELI5):**
<Explain it as if to a curious 10-year-old using an everyday analogy>

**Intermediate Explanation:**
<More detailed explanation with proper terminology, suitable for a high-school student>

**Advanced Explanation:**
<Full technical depth with formal definitions, formulas, and nuances>

**Practice Question:**
<A question the student can try to test their understanding>

**Answer to Practice Question:**
<The correct answer with brief explanation>

Requirements:
- Use analogies and real-world examples at each level
- Introduce technical terms gradually (define them when first used)
- Build concepts progressively from simple to complex""",
))


# ---- 9. Creative / Essay ----
_register(PromptTemplate(
    id="creative",
    name="Creative / Essay",
    description="Thoughtful, well-structured essay or creative response",
    categories=["history", "economics", "general", "logic"],
    intents=["creative", "reasoning"],
    complexity="complex",
    output_format="structured",
    template="""You are a thoughtful writer. Produce a well-structured, engaging response.

Topic: {question}

Provide your response in this format:

**Thesis / Main Argument:**
<Your central claim or perspective in 1-2 sentences>

**Discussion:**
<Well-organized paragraphs exploring the topic in depth. Consider multiple perspectives.>

**Evidence & Examples:**
<Specific examples, data, or case studies that support your points>

**Counterarguments:**
<Address opposing viewpoints fairly and explain why your position is stronger>

**Conclusion:**
<Synthesize your arguments into a compelling conclusion>

Requirements:
- Write in clear, engaging prose
- Support claims with specific evidence
- Consider multiple perspectives before concluding
- Maintain a logical flow from introduction to conclusion""",
))


# ---- 10. JSON / API Output ----
_register(PromptTemplate(
    id="json_output",
    name="JSON Structured Output",
    description="Returns answer in strict JSON format for programmatic use",
    categories=["computer_science", "general", "code_api"],
    intents=["question", "code"],
    complexity="moderate",
    output_format="json",
    template="""Answer the following question and return your response as valid JSON.

Question: {question}

Return ONLY valid JSON in this exact format (no text before or after):

{{
  "answer": "<your direct answer>",
  "explanation": "<detailed explanation>",
  "key_points": ["<point 1>", "<point 2>", "<point 3>"],
  "confidence": <0.0 to 1.0>,
  "category": "<topic category>",
  "difficulty": "<easy|medium|hard>",
  "related_topics": ["<related topic 1>", "<related topic 2>"]
}}

Requirements:
- Output MUST be valid JSON (no markdown, no extra text)
- Answer must be factually accurate
- Explanation should be 2-4 sentences
- Include at least 3 key points""",
))


# ── Auto-detection: pick the best template for a question ─────────────────

_CODE_RE = re.compile(
    r'\b(code|function|class|implement|debug|program|script|api|algorithm|'
    r'write a|build a|create a|def |import |print\(|console\.log)\b',
    re.IGNORECASE,
)
_COMPARE_RE = re.compile(
    r'\b(compare|difference|vs\.?|versus|between|pros and cons|trade.?off|which is better)\b',
    re.IGNORECASE,
)
_REASONING_RE = re.compile(
    r'\b(prove|derive|calculate|solve|how many|what is the value|step by step|equation|formula)\b',
    re.IGNORECASE,
)
_DEBUG_RE = re.compile(
    r'\b(debug|fix|error|bug|issue|wrong|broken|doesn.t work|not working|exception|traceback)\b',
    re.IGNORECASE,
)
_CREATIVE_RE = re.compile(
    r'\b(essay|write about|discuss|opinion|argue|perspective|think about)\b',
    re.IGNORECASE,
)


def detect_intent(question: str) -> str:
    """Detect the primary intent of a question."""
    if _DEBUG_RE.search(question):
        return "debug"
    if _CODE_RE.search(question):
        return "code"
    if _COMPARE_RE.search(question):
        return "comparison"
    if _REASONING_RE.search(question):
        return "reasoning"
    if _CREATIVE_RE.search(question):
        return "creative"
    return "question"


def auto_select_template(
    question: str,
    category: str = "general",
    complexity: str = "moderate",
) -> PromptTemplate:
    """
    Automatically select the best prompt template based on:
    1. Detected intent (code / comparison / reasoning / debug / creative / question)
    2. Question category
    3. Complexity level

    Returns the highest-priority matching template.
    """
    intent = detect_intent(question)

    # Priority mapping: intent → preferred template id
    intent_priority = {
        "debug": "code_debug",
        "code": "code_generation",
        "comparison": "comparison",
        "reasoning": "step_by_step",
        "creative": "creative",
    }

    # Direct intent match
    if intent in intent_priority:
        tid = intent_priority[intent]
        if tid in PROMPT_TEMPLATES:
            return PROMPT_TEMPLATES[tid]

    # Category-based match
    category_priority = {
        "code_python": "code_generation",
        "code_javascript": "code_generation",
        "code_java": "code_generation",
        "code_cpp": "code_generation",
        "code_sql": "code_generation",
        "code_rust": "code_generation",
        "code_debug": "code_debug",
        "code_refactor": "code_generation",
        "code_api": "code_generation",
        "code_html_css": "code_generation",
        "mathematics": "step_by_step",
        "logic": "step_by_step",
    }
    if category in category_priority:
        tid = category_priority[category]
        if tid in PROMPT_TEMPLATES:
            return PROMPT_TEMPLATES[tid]

    # Scientific categories → scientific template
    science_cats = {"biology", "physics", "chemistry", "earth_science", "astronomy"}
    if category in science_cats:
        return PROMPT_TEMPLATES["scientific"]

    # Complexity-based fallback
    if complexity == "simple":
        return PROMPT_TEMPLATES["concise"]

    # Default
    return PROMPT_TEMPLATES["general_qa"]


def list_templates() -> List[Dict[str, Any]]:
    """Return all available templates as dicts (for API responses)."""
    return [t.to_dict() for t in PROMPT_TEMPLATES.values()]


def get_template(template_id: str) -> Optional[PromptTemplate]:
    """Get a template by ID. Returns None if not found."""
    return PROMPT_TEMPLATES.get(template_id)


def get_template_for_question(
    question: str,
    category: str = "general",
    complexity: str = "moderate",
    preferred_id: Optional[str] = None,
) -> PromptTemplate:
    """
    Get the best template.  If preferred_id is given and valid, use that.
    Otherwise auto-select.
    """
    if preferred_id and preferred_id in PROMPT_TEMPLATES:
        return PROMPT_TEMPLATES[preferred_id]
    return auto_select_template(question, category, complexity)
