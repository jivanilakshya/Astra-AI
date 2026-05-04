"""
Astra-AI FastAPI Server
Bridges the existing CLI backend with the React frontend.

Run:
    uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import os
import json
import asyncio
import logging
import traceback
import re
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Fix encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env from project root (parent of backend/) or from backend/ itself
from dotenv import load_dotenv
_env_parent = project_root.parent / ".env"
_env_local = project_root / ".env"
if _env_parent.exists():
    load_dotenv(str(_env_parent), override=True)
elif _env_local.exists():
    load_dotenv(str(_env_local), override=True)
else:
    load_dotenv()  # fallback: search CWD

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("astra-api")


def _supported_models() -> List[Dict[str, Any]]:
    """Return the supported model list for the frontend with full ModelProfile shape."""
    models: List[Dict[str, Any]] = []

    # Model metadata lookup for enriching basic model entries
    _MODEL_META: Dict[str, Dict[str, Any]] = {
        "meta-llama/Meta-Llama-3-8B-Instruct": {"description": "Efficient medium-size model with excellent instruction following", "parameters": "8B", "contextWindow": 8192, "costPer1MTokens": 1.0, "strengths": ["Speed", "General QA", "Instruction following"], "quality_tier": 2},
        "mistralai/Mistral-7B-Instruct-v0.3": {"description": "Fast and cost-effective instruct model", "parameters": "7B", "contextWindow": 32768, "costPer1MTokens": 0.8, "strengths": ["Cost-effective", "Fast", "Code"], "quality_tier": 2},
        "mistralai/Mixtral-8x7B-Instruct-v0.1": {"description": "Mixture-of-experts model with broad capability", "parameters": "8x7B", "contextWindow": 32768, "costPer1MTokens": 2.5, "strengths": ["Reasoning", "Code", "Multilingual"], "quality_tier": 1},
        "Qwen/Qwen2.5-72B-Instruct": {"description": "Large-scale model with strong reasoning and multilingual capabilities", "parameters": "72B", "contextWindow": 32768, "costPer1MTokens": 3.0, "strengths": ["Reasoning", "Code", "Multilingual"], "quality_tier": 1},
        "Qwen/Qwen2.5-Coder-32B-Instruct": {"description": "Specialized code model with strong debugging", "parameters": "32B", "contextWindow": 32768, "costPer1MTokens": 2.0, "strengths": ["Code generation", "Debugging", "Refactoring"], "quality_tier": 1},
        "Qwen/Qwen2.5-7B-Instruct": {"description": "Balanced model offering good quality at lower cost", "parameters": "7B", "contextWindow": 32768, "costPer1MTokens": 0.6, "strengths": ["Balanced", "Efficient", "Multilingual"], "quality_tier": 2},
        "Qwen/Qwen2.5-14B-Instruct": {"description": "Medium-large model with good all-round performance", "parameters": "14B", "contextWindow": 32768, "costPer1MTokens": 1.2, "strengths": ["Balanced", "Reasoning", "Multilingual"], "quality_tier": 2},
        "meta-llama/Llama-3.2-3B-Instruct": {"description": "Ultra-fast lightweight model for simple tasks", "parameters": "3B", "contextWindow": 8192, "costPer1MTokens": 0.3, "strengths": ["Ultra-fast", "Lightweight", "Low cost"], "quality_tier": 3},
        "meta-llama/Llama-3.2-1B-Instruct": {"description": "Smallest model for edge deployment and testing", "parameters": "1B", "contextWindow": 8192, "costPer1MTokens": 0.1, "strengths": ["Fastest", "Cheapest", "Edge deployment"], "quality_tier": 3},
        "microsoft/Phi-3-mini-4k-instruct": {"description": "Compact but capable model from Microsoft", "parameters": "3.8B", "contextWindow": 4096, "costPer1MTokens": 0.2, "strengths": ["Compact", "Fast", "Reasoning"], "quality_tier": 3},
    }

    def _enrich(model_id: str, name: str, provider: str, status: str) -> Dict[str, Any]:
        meta = _MODEL_META.get(model_id, {})
        params = meta.get("parameters", _extract_params(model_id))
        ctx = meta.get("contextWindow", 8192)
        cost = meta.get("costPer1MTokens", 0.0)
        strengths = meta.get("strengths", _model_strengths(model_id))
        tier = meta.get("quality_tier", 2)
        return {
            "id": model_id,
            "name": name,
            "provider": provider,
            "status": status,
            "description": meta.get("description", f"{name} — {provider} model"),
            "parameters": params,
            "contextWindow": ctx,
            "context_window": ctx,
            "costPer1MTokens": cost,
            "cost_input_per_1k": cost / 1000.0,
            "cost_output_per_1k": cost / 200.0,
            "avg_latency_seconds": meta.get("avg_latency_seconds", 2.0),
            "avgLatency": int(meta.get("avg_latency_seconds", 2.0) * 1000),
            "avgScore": None,
            "quality_tier": tier,
            "is_available": status == "available",
            "strengths": strengths,
        }

    try:
        from agents.huggingface_provider import AVAILABLE_MODELS
        models.extend(
            _enrich(m["id"], m["name"], "huggingface", "available")
            for m in AVAILABLE_MODELS
        )
    except Exception:
        pass

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    for model_id, label in [
        ("claude-3-opus", "Claude 3 Opus"),
        ("claude-3-sonnet", "Claude 3 Sonnet"),
        ("claude-3-haiku", "Claude 3 Haiku"),
    ]:
        models.append(
            _enrich(model_id, label, "anthropic", "available" if anthropic_key else "unavailable")
        )

    seen = set()
    unique_models = []
    for model in models:
        if model["id"] in seen:
            continue
        seen.add(model["id"])
        unique_models.append(model)
    return unique_models


def _sync_model_selector_pricing(model_selector: Optional[Any]) -> None:
    """Ensure ModelSelector has pricing for all supported models."""
    if not model_selector:
        return
    try:
        from utils.model_selector import ModelPricing
        for model in _supported_models():
            model_id = model.get("id")
            if not model_id:
                continue
            cost_per_1m = float(model.get("costPer1MTokens") or 0.0)
            if cost_per_1m <= 0:
                continue
            input_cost = cost_per_1m / 1000.0
            output_cost = cost_per_1m / 200.0
            context_window = int(model.get("contextWindow") or model.get("context_window") or 8192)
            tier = int(model.get("quality_tier") or 2)
            model_selector.model_pricing[model_id] = ModelPricing(
                model_name=model_id,
                input_cost_per_1k=input_cost,
                output_cost_per_1k=output_cost,
                context_window=context_window,
                performance_tier=tier,
            )
    except Exception as e:
        logger.warning(f"Could not sync model pricing: {e}")

# ── Pydantic request / response models ──────────────────────────────────────

class QuestionIn(BaseModel):
    question: str
    category: str = "general"
    groundTruth: Optional[str] = None
    difficulty: str = "medium"

class AskIn(BaseModel):
    question: str
    prompt: Optional[str] = None
    model: Optional[str] = None
    templateId: Optional[str] = None
    category: Optional[str] = "general"
    showRouting: Optional[bool] = False
    useContext: Optional[bool] = True

class OptimizationConfigIn(BaseModel):
    model: Optional[str] = None
    initialPrompt: Optional[str] = None
    generatorModel: Optional[str] = None
    judgeModel: Optional[str] = None
    optimizerModel: Optional[str] = None
    maxIterations: Optional[int] = 10
    convergenceThreshold: Optional[float] = 8.5
    temperature: Optional[float] = 0.7
    batchSize: Optional[int] = 5
    questionIds: Optional[List[str]] = None
    customQuestions: Optional[List[str]] = None
    maxTokens: Optional[int] = 500
    templateId: Optional[str] = None
    smartRouter: Optional[bool] = False

class CompareIn(BaseModel):
    prompt: str
    models: List[str]

class PromptIn(BaseModel):
    prompt: str

class SettingsIn(BaseModel):
    generatorModel: Optional[str] = None
    judgeModel: Optional[str] = None
    optimizerModel: Optional[str] = None
    huggingfaceToken: Optional[str] = None
    maxIterations: Optional[int] = None
    convergenceThreshold: Optional[float] = None
    temperature: Optional[float] = None
    maxTokens: Optional[int] = None


class RouterExplainIn(BaseModel):
    question: str
    category: Optional[str] = "general"


class ModeToggleIn(BaseModel):
    mode: str  # "developer" or "production"


class QuestionTestIn(BaseModel):
    templateId: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    maxTokens: Optional[int] = 500


# ── Application factory ─────────────────────────────────────────────────────

app = FastAPI(
    title="Astra-AI API",
    description="Backend API for the Astra-AI Self-Improving LLM System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Lazy-initialized backend singletons ─────────────────────────────────────

class BackendState:
    """Holds lazily-initialized backend components."""
    def __init__(self):
        self.initialized = False
        self.controller = None
        self.provider = None
        self.smart_router = None
        self.prompt_engine = None
        self.multi_model_engine = None
        self.mode_manager = None
        self.model_selector = None
        self.analytics = None
        self.questions_db: List[Dict[str, Any]] = []
        self.sessions_db: List[Dict[str, Any]] = []
        self.session_results: Dict[str, Dict[str, Any]] = {}
        self.session_progress: Dict[str, Dict[str, Any]] = {}
        self._next_question_id = 1
        self._init_lock = asyncio.Lock()

    async def ensure_initialized(self):
        """Initialize backend components once."""
        if self.initialized:
            return
        async with self._init_lock:
            if self.initialized:
                return
            await asyncio.get_running_loop().run_in_executor(None, self._init_sync)

    def _init_sync(self):
        """Synchronous initialization of backend components."""
        try:
            logger.info("Initializing backend components...")

            # ── Import backend modules ──
            from config import get_config
            from agents.huggingface_provider import HuggingFaceProvider, AVAILABLE_MODELS
            from utils.smart_router import SmartRouter
            from utils.prompt_engine import PromptEngine
            from utils.runtime_mode import RuntimeMode, get_mode_manager
            from utils.model_selector import create_model_selector
            from utils.analytics import create_analytics

            config = get_config()

            # HuggingFace provider
            try:
                self.provider = HuggingFaceProvider()
                logger.info("HuggingFace provider ready")
            except Exception as e:
                logger.warning(f"HuggingFace provider not available: {e}")
                self.provider = None

            # Smart Router
            output_dir = Path("./output")
            output_dir.mkdir(parents=True, exist_ok=True)
            self.smart_router = SmartRouter(
                prefer_free=True,
                feedback_path=str(output_dir / "router_feedback.json"),
            )

            # Prompt Engine
            self.prompt_engine = PromptEngine(
                history_path=str(output_dir / "prompt_history.json"),
            )

            # Mode Manager
            self.mode_manager = get_mode_manager(RuntimeMode.PRODUCTION)

            # Model Selector (cost tracking)
            try:
                self.model_selector = create_model_selector(
                    prefer_open_source=True,
                    storage_path=str(output_dir / "cost_tracking"),
                )
                _sync_model_selector_pricing(self.model_selector)
            except Exception as e:
                logger.warning(f"Model selector init failed: {e}")

            # Analytics
            try:
                self.analytics = create_analytics(
                    storage_path=str(output_dir / "analytics"),
                )
            except Exception as e:
                logger.warning(f"Analytics init failed: {e}")

            # Multi-model engine
            try:
                from utils.multi_model import MultiModelEngine
                self.multi_model_engine = MultiModelEngine()
            except Exception as e:
                logger.warning(f"MultiModelEngine not available: {e}")

            # Load default questions from sample_questions.json
            self._load_default_questions()

            # Load existing sessions from output directory
            self._load_existing_sessions()

            self.initialized = True
            logger.info("Backend components initialized successfully")

        except Exception as e:
            logger.error(f"Backend initialization error: {e}")
            logger.error(traceback.format_exc())
            # Mark as initialized anyway so we don't block — endpoints will handle None components
            self.initialized = True

    def _load_default_questions(self):
        """Load questions from data/sample_questions.json."""
        try:
            sample_path = project_root / "data" / "sample_questions.json"
            if sample_path.exists():
                with open(sample_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = data.get("questions", data) if isinstance(data, dict) else data
                for item in items:
                    q = {
                        "id": str(item.get("id", self._next_question_id)),
                        "question": item.get("question", ""),
                        "groundTruth": item.get("ground_truth", ""),
                        "category": item.get("category", "general"),
                        "difficulty": item.get("difficulty", "medium"),
                    }
                    self.questions_db.append(q)
                    try:
                        self._next_question_id = max(self._next_question_id, int(q["id"]) + 1)
                    except (ValueError, TypeError):
                        self._next_question_id += 1
                logger.info(f"Loaded {len(self.questions_db)} default questions")
        except Exception as e:
            logger.warning(f"Could not load default questions: {e}")

        # Also load from questions.json at project root (extended set)
        try:
            extended_path = project_root / "questions.json"
            if extended_path.exists():
                with open(extended_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                items = data.get("questions", data) if isinstance(data, dict) else data
                existing_ids = {q["id"] for q in self.questions_db}
                for item in items:
                    qid = str(item.get("id", self._next_question_id))
                    if qid not in existing_ids:
                        q = {
                            "id": qid,
                            "question": item.get("question", ""),
                            "groundTruth": item.get("ground_truth", ""),
                            "category": item.get("category", "general"),
                            "difficulty": item.get("difficulty", "medium"),
                        }
                        self.questions_db.append(q)
                        try:
                            self._next_question_id = max(self._next_question_id, int(qid) + 1)
                        except (ValueError, TypeError):
                            self._next_question_id += 1
                logger.info(f"Total questions after extended load: {len(self.questions_db)}")
        except Exception as e:
            logger.warning(f"Could not load extended questions: {e}")

    def _load_existing_sessions(self):
        """Scan output/ for session directories and build session list."""
        try:
            output_dir = project_root / "output"
            if not output_dir.exists():
                return
            for entry in output_dir.iterdir():
                if entry.is_dir() and entry.name.startswith("session_"):
                    results_file = entry / "results.json"
                    if results_file.exists():
                        try:
                            with open(results_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            session_id = entry.name.replace("session_", "sess_")
                            session = {
                                "sessionId": session_id,
                                "startedAt": data.get("timestamp", entry.name.replace("session_", "")),
                                "status": "completed",
                                "totalIterations": data.get("iterations", 0),
                                "initialScore": data.get("initial_score", 0),
                                "finalScore": data.get("final_score", 0),
                                "improvement": data.get("improvement", 0),
                                "converged": data.get("converged", False),
                                "model": data.get("model", "unknown"),
                                "totalCost": data.get("total_cost", 0),
                                "questionsCount": data.get("questions_count", 0),
                                "durationSeconds": data.get("duration_seconds", 0),
                            }
                            self.sessions_db.append(session)
                            self.session_results[session_id] = data
                        except Exception:
                            pass
            logger.info(f"Loaded {len(self.sessions_db)} existing sessions")
        except Exception as e:
            logger.warning(f"Could not load existing sessions: {e}")


backend = BackendState()

# ── Session Persistence Helpers ──────────────────────────────────────────────

_SESSIONS_FILE = project_root / "output" / "sessions.json"


def _save_sessions_to_disk():
    """Persist sessions_db to a JSON file so they survive restarts."""
    try:
        _SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "sessions": backend.sessions_db,
            "updated_at": datetime.now().isoformat(),
        }
        with open(_SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Could not save sessions to disk: {e}")


def _load_sessions_from_disk():
    """Load sessions from the JSON persistence file."""
    try:
        if _SESSIONS_FILE.exists():
            with open(_SESSIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions = data.get("sessions", [])
            existing_ids = {s["sessionId"] for s in backend.sessions_db}
            for s in sessions:
                if s.get("sessionId") and s["sessionId"] not in existing_ids:
                    backend.sessions_db.append(s)
                    existing_ids.add(s["sessionId"])
            logger.info(f"Loaded {len(sessions)} sessions from disk")
    except Exception as e:
        logger.warning(f"Could not load sessions from disk: {e}")


def _seed_default_data():
    """Seed sample sessions and cost data so Dashboard/Charts always have data.
    Only seeds if sessions_db is empty after all loads."""
    if backend.sessions_db:
        return  # already have data
    logger.info("Seeding default demo data for dashboard/charts...")
    now = datetime.now()
    seed_sessions = [
        {"sessionId": "sess_demo_001", "startedAt": (now.replace(day=max(1, now.day - 6))).isoformat(), "status": "completed", "totalIterations": 8, "finalScore": 8.72, "initialScore": 5.4, "improvement": 3.32, "converged": True, "model": "Qwen/Qwen2.5-72B-Instruct", "totalCost": 0.042, "questionsCount": 5, "durationSeconds": 180},
        {"sessionId": "sess_demo_002", "startedAt": (now.replace(day=max(1, now.day - 4))).isoformat(), "status": "completed", "totalIterations": 10, "finalScore": 7.91, "initialScore": 4.8, "improvement": 3.11, "converged": False, "model": "meta-llama/Meta-Llama-3-8B-Instruct", "totalCost": 0.028, "questionsCount": 3, "durationSeconds": 240},
        {"sessionId": "sess_demo_003", "startedAt": (now.replace(day=max(1, now.day - 2))).isoformat(), "status": "completed", "totalIterations": 6, "finalScore": 9.12, "initialScore": 6.1, "improvement": 3.02, "converged": True, "model": "Qwen/Qwen2.5-72B-Instruct", "totalCost": 0.035, "questionsCount": 5, "durationSeconds": 120},
        {"sessionId": "sess_demo_004", "startedAt": (now.replace(day=max(1, now.day - 1))).isoformat(), "status": "completed", "totalIterations": 7, "finalScore": 8.35, "initialScore": 5.8, "improvement": 2.55, "converged": True, "model": "meta-llama/Meta-Llama-3-8B-Instruct", "totalCost": 0.031, "questionsCount": 4, "durationSeconds": 160},
    ]
    backend.sessions_db.extend(seed_sessions)
    _save_sessions_to_disk()
    logger.info(f"Seeded {len(seed_sessions)} demo sessions")


# ── Startup Event ────────────────────────────────────────────────────────────

async def _background_init():
    """Initialize backend components without blocking startup."""
    try:
        await backend.ensure_initialized()
        _load_sessions_from_disk()
        _seed_default_data()
        logger.info("Astra-AI startup complete")
    except Exception as e:
        logger.error(f"Init failed: {e}")


@app.on_event("startup")
async def _startup():
    """Kick off initialization in the background."""
    asyncio.create_task(_background_init())


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "initialized": backend.initialized,
        "provider_available": backend.provider is not None,
        "timestamp": datetime.now().isoformat(),
    }


# ── Questions ────────────────────────────────────────────────────────────────

@app.get("/api/questions")
async def list_questions():
    """List all questions."""
    await backend.ensure_initialized()
    return backend.questions_db


@app.post("/api/questions")
async def add_question(body: QuestionIn):
    """Add a new question."""
    await backend.ensure_initialized()
    q = {
        "id": str(backend._next_question_id),
        "question": body.question,
        "groundTruth": body.groundTruth or "",
        "category": body.category,
        "difficulty": body.difficulty,
    }
    backend._next_question_id += 1
    backend.questions_db.append(q)
    return q


@app.delete("/api/questions/{question_id}")
async def delete_question(question_id: str):
    """Delete a question by ID."""
    await backend.ensure_initialized()
    idx = next((i for i, q in enumerate(backend.questions_db) if q["id"] == question_id), None)
    if idx is None:
        raise HTTPException(404, "Question not found")
    backend.questions_db.pop(idx)
    return {"status": "deleted"}


# ── Ask (single question generation) ────────────────────────────────────────

@app.post("/api/ask")
async def ask_question(body: AskIn):
    """Generate an answer to a single question using the LLM."""
    await backend.ensure_initialized()
    if backend.provider is None:
        raise HTTPException(503, "HuggingFace provider not available. Check HUGGINGFACE_API_KEY.")

    # ── Template selection ──
    from utils.prompt_templates import get_template_for_question, detect_intent
    template_obj = None
    complexity = "moderate"
    if body.prompt:
        # User supplied raw prompt — use as-is
        full_prompt = body.prompt.replace("{question}", body.question)
        template_used = None
    else:
        # Auto-select or use specified template
        category = body.category or "general"
        if backend.smart_router:
            try:
                complexity = backend.smart_router.detect_complexity(body.question).lower()
            except Exception:
                pass
        template_obj = get_template_for_question(
            body.question, category=category, complexity=complexity,
            preferred_id=body.templateId,
        )
        full_prompt = template_obj.render(body.question)
        template_used = template_obj.id

    # ── Context engineering (lightweight retrieval from question bank) ──
    context_used = None
    if body.useContext is not False:
        context_used = _build_context_pack(body.question, body.category or "general")
        if context_used and context_used.get("contextText"):
            full_prompt = (
                f"{context_used['contextText']}\n\n"
                f"Follow the context guidance above when relevant, then answer the question.\n\n"
                f"{full_prompt}"
            )

    # ── Model routing ──
    routing_info = None
    if body.showRouting and backend.smart_router:
        try:
            routing_info = _explain_routing(body.question, body.category or "general")
        except Exception:
            pass

    model = body.model
    if not model and backend.smart_router:
        try:
            model = backend.smart_router.route(body.question)
        except Exception:
            model = None
    model = model or ("claude-3-opus" if os.getenv("ANTHROPIC_API_KEY") else "Qwen/Qwen2.5-72B-Instruct")

    try:
        result = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: backend.provider.generate(
                model_name=model,
                prompt=full_prompt,
                temperature=0.7,
                max_tokens=500,
            )
        )
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(500, f"Generation failed: {str(e)}")

    response_text = result.get("text", "") if isinstance(result, dict) else str(result)
    success = result.get("success", True) if isinstance(result, dict) else True
    latency = result.get("latency_seconds", 0) if isinstance(result, dict) else 0

    if not success:
        error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Unknown error"
        raise HTTPException(500, f"Generation failed: {error_msg}")

    # Parse answer and explanation from structured output
    answer = response_text
    explanation = ""
    if "**Answer:**" in response_text:
        # Structured template output — keep full text as answer, extract summary
        answer = response_text
        explanation = response_text
    elif "Explanation:" in response_text:
        parts = response_text.split("Explanation:", 1)
        answer = parts[0].replace("Answer:", "").strip()
        explanation = parts[1].strip()
    elif "Answer:" in response_text:
        answer = response_text.split("Answer:", 1)[1].strip()

    tokens_est = max(1, len(full_prompt) // 4)
    output_tokens_est = max(1, len(response_text) // 4)
    cost_est_usd = _estimate_cost_usd(model, tokens_est, output_tokens_est)

    try:
        if backend.model_selector:
            from utils.model_selector import AgentType
            backend.model_selector.record_usage(
                agent_type=AgentType.GENERATOR,
                model_name=model,
                input_tokens=tokens_est,
                output_tokens=output_tokens_est,
                metadata={"endpoint": "question_test", "question_id": question_id, "category": category},
            )
    except Exception:
        pass

    try:
        if backend.smart_router:
            ms = _evaluate_response_against_ground_truth(response_text, ground_truth).get("matchScore") if ground_truth else None
            quality_score = float(ms if ms is not None else _score_comparison_response(q["question"], response_text, True, latency * 1000).get("compositeScore", 0))
            backend.smart_router.record_feedback(
                prompt=q["question"],
                model_used=model,
                quality_score=quality_score,
                latency_seconds=float(latency),
                cost_usd=float(cost_est_usd),
                success=True,
            )
    except Exception:
        pass

    _record_runtime_usage(
        agent="generator",
        model_name=model,
        prompt=full_prompt,
        response_text=response_text,
        cost_usd=cost_est_usd,
        success=True,
        latency_ms=latency * 1000,
        endpoint="ask",
    )

    # ── Mode-aware logging ──
    debug_info = None
    if backend.mode_manager:
        try:
            from utils.runtime_mode import RuntimeMode
            if backend.mode_manager.is_developer:
                backend.mode_manager.log_prompt("generator", full_prompt)
                backend.mode_manager.log_response("generator", response_text)
                debug_info = {
                    "fullPrompt": full_prompt,
                    "rawResponse": response_text,
                    "templateUsed": template_used,
                    "modelRouting": routing_info,
                }
        except Exception:
            pass

    resp = {
        "question": body.question,
        "answer": answer,
        "explanation": explanation or answer,
        "fullResponse": response_text,
        "confidence": 0.85,
        "templateUsed": template_used,
        "templateDecision": {
            "detectedIntent": detect_intent(body.question),
            "detectedComplexity": complexity,
            "category": body.category or "general",
        },
        "metadata": {
            "model": model,
            "tokens_used": tokens_est + output_tokens_est,
            "input_tokens": tokens_est,
            "output_tokens": output_tokens_est,
            "cost_usd": cost_est_usd,
            "latency_ms": latency * 1000,
            "timestamp": datetime.now().isoformat(),
        },
    }
    if context_used:
        resp["context"] = context_used
    if routing_info:
        resp["routing"] = routing_info
    if debug_info:
        resp["debug"] = debug_info
    _record_runtime_usage(
        agent="generator",
        model_name=model,
        prompt=full_prompt,
        response_text=response_text,
        cost_usd=cost_est_usd,
        success=True,
        latency_ms=latency * 1000,
        endpoint="ask",
    )
    return resp


def _extract_params(model_id: str) -> str:
    """Extract parameter count from model ID."""
    for size in ["72B", "32B", "8B", "7B", "3B", "1B"]:
        if size in model_id:
            return size
    return "unknown"


def _model_strengths(model_id: str) -> List[str]:
    """Return strengths based on model ID."""
    m = model_id.lower()
    if "coder" in m:
        return ["Code generation", "Debugging", "Refactoring"]
    if "72b" in m:
        return ["Reasoning", "Code", "Multilingual"]
    if "1b" in m:
        return ["Fastest", "Cheapest", "Edge deployment"]
    if "3b" in m:
        return ["Ultra-fast", "Lightweight", "Low cost"]
    if "llama-3-8b" in m:
        return ["Speed", "General QA", "Instruction following"]
    if "llama-3.2" in m:
        return ["Speed", "General QA", "Instruction following"]
    if "mistral" in m:
        return ["Cost-effective", "Fast", "Code"]
    if "qwen" in m and "7b" in m:
        return ["Balanced", "Efficient", "Multilingual"]
    return ["General"]


# ── Prompt Analysis ──────────────────────────────────────────────────────────

@app.post("/api/prompt/analyze")
async def analyze_prompt(body: PromptIn):
    """Analyze a prompt for quality."""
    await backend.ensure_initialized()
    if backend.prompt_engine is None:
        raise HTTPException(503, "Prompt engine not available")

    try:
        analysis = await asyncio.get_running_loop().run_in_executor(
            None, lambda: backend.prompt_engine.analyze(body.prompt)
        )
        result = analysis.to_dict() if hasattr(analysis, "to_dict") else {}
    except Exception as e:
        logger.error(f"Prompt analysis error: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")

    # Map to frontend's expected PromptAnalysis shape
    word_count = result.get("word_count", len(body.prompt.split()))
    quality_grade = result.get("quality_grade", "C")
    quality_score_map = {"A": 9.0, "B": 7.5, "C": 5.5, "D": 3.5, "F": 2.0}
    quality_score = quality_score_map.get(quality_grade, 5.0)

    # Build dynamic recommendations using built-in templates and detected intent.
    from utils.prompt_templates import auto_select_template, list_templates
    category_guess = "general"
    p_lower = body.prompt.lower()
    if "python" in p_lower:
        category_guess = "code_python"
    elif "javascript" in p_lower or "typescript" in p_lower:
        category_guess = "code_javascript"
    elif "math" in p_lower or "equation" in p_lower:
        category_guess = "mathematics"

    detected_complexity = "moderate"
    if backend.smart_router:
        try:
            detected_complexity = backend.smart_router.detect_complexity(body.prompt)
        except Exception:
            pass

    selected_template = auto_select_template(body.prompt, category=category_guess, complexity=str(detected_complexity).lower())
    all_templates = list_templates()
    recommended_templates = [
        {
            "id": t.get("id"),
            "name": t.get("name"),
            "why": (
                "Best intent/category match" if t.get("id") == selected_template.id
                else "Useful alternative for different output style"
            ),
        }
        for t in all_templates
        if t.get("id") == selected_template.id or t.get("id") in {"general_qa", "step_by_step", "concise", "code_generation", "scientific"}
    ][:4]

    base_suggestions = list(result.get("suggested_improvements", []))
    if quality_score < 6.5 and "{question}" not in body.prompt:
        base_suggestions.append("Add {question} placeholder so the template can be reused safely.")
    if "json" in p_lower and "valid json" not in p_lower:
        base_suggestions.append("Specify strict JSON schema and prohibit extra text around JSON.")
    if len(body.prompt.split()) < 20:
        base_suggestions.append("Add output structure and constraints (length, format, examples) to reduce variance.")
    if "step-by-step" not in p_lower and ("why" in p_lower or "compare" in p_lower):
        base_suggestions.append("Ask for step-by-step reasoning to improve consistency on analytical prompts.")

    return {
        "qualityScore": quality_score,
        "overallScore": quality_score,
        "qualityGrade": quality_grade,
        "wordCount": word_count,
        "components": result.get("auto_constraints", []),
        "issues": result.get("suggested_improvements", []),
        "suggestions": base_suggestions,
        "scores": {
            "clarity": round(result.get("specificity_score", 0.5) * 10, 1),
            "specificity": round(result.get("specificity_score", 0.5) * 10, 1),
            "structure": round((1 - result.get("vagueness_score", 0.5)) * 10, 1),
            "completeness": round((1 - result.get("ambiguity_score", 0.5)) * 10, 1),
        },
        "flags": [],
        "detectedIntent": result.get("detected_intent", "general"),
        "recommendedTemplates": recommended_templates,
        "templateAdvice": {
            "selected": selected_template.id,
            "complexity": str(detected_complexity),
            "category": category_guess,
        },
    }


# ── Prompt Optimize ──────────────────────────────────────────────────────────

@app.post("/api/prompt/optimize")
async def optimize_prompt(body: PromptIn):
    """Optimize a prompt."""
    await backend.ensure_initialized()
    if backend.prompt_engine is None:
        raise HTTPException(503, "Prompt engine not available")

    try:
        optimized = await asyncio.get_running_loop().run_in_executor(
            None, lambda: backend.prompt_engine.optimize(body.prompt)
        )
    except Exception as e:
        raise HTTPException(500, f"Optimization failed: {str(e)}")

    return {"optimizedPrompt": optimized}


# ── Cost Prediction ──────────────────────────────────────────────────────────

@app.post("/api/cost/predict")
async def predict_cost(body: PromptIn):
    """Predict cost for a prompt."""
    await backend.ensure_initialized()
    if backend.smart_router is None:
        raise HTTPException(503, "Smart router not available")

    try:
        prediction = await asyncio.get_running_loop().run_in_executor(
            None, lambda: backend.smart_router.predict_cost(body.prompt)
        )
        # prediction is a CostPrediction dataclass
        from dataclasses import asdict
        pred_dict = asdict(prediction) if hasattr(prediction, "__dataclass_fields__") else prediction
    except Exception as e:
        raise HTTPException(500, f"Cost prediction failed: {str(e)}")

    return {
        "prompt_tokens_est": pred_dict.get("prompt_tokens_est", 0),
        "response_tokens_est": pred_dict.get("response_tokens_est", 0),
        "total_tokens_est": pred_dict.get("total_tokens_est", 0),
        "cost_estimate_usd": pred_dict.get("cost_estimate_usd", 0),
        "estimatedInputTokens": pred_dict.get("prompt_tokens_est", 0),
        "estimatedOutputTokens": pred_dict.get("response_tokens_est", 0),
        "estimatedCostPerQuestion": pred_dict.get("cost_estimate_usd", 0),
        "latency_estimate_seconds": pred_dict.get("latency_estimate_seconds", 2.0),
        "complexity": pred_dict.get("complexity", "MODERATE"),
        "recommended_model": pred_dict.get("recommended_model", "claude-3-opus" if os.getenv("ANTHROPIC_API_KEY") else "Qwen/Qwen2.5-72B-Instruct"),
        "alternative_models": pred_dict.get("alternative_models", []),
    }


@app.get("/api/models")
async def list_models():
    """Return the list of supported models for the frontend."""
    await backend.ensure_initialized()
    return _supported_models()


# ── Cost History ─────────────────────────────────────────────────────────────

@app.get("/api/cost/history")
async def get_cost_history():
    """Return cost tracking history."""
    await backend.ensure_initialized()

    usage_records: List[Dict[str, Any]] = []

    # First preference: in-memory model selector usage.
    if backend.model_selector and hasattr(backend.model_selector, "usage_records"):
        try:
            usage_records = [r.to_dict() for r in backend.model_selector.usage_records]
        except Exception:
            usage_records = []

    # Fallback: load usage_data.json export files.
    if not usage_records:
        cost_dir = project_root / "output" / "cost_tracking"
        if cost_dir.exists():
            for f in sorted(cost_dir.glob("*.json")):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    if isinstance(data, dict) and isinstance(data.get("usage_records"), list):
                        usage_records.extend(data.get("usage_records", []))
                    elif isinstance(data, list):
                        usage_records.extend(data)
                except Exception:
                    pass

    if usage_records:
        return _aggregate_daily_cost_records(usage_records)

    # Final fallback: synthesize minimal daily records from completed sessions.
    if backend.sessions_db:
        daily: Dict[str, Dict[str, Any]] = {}
        for s in backend.sessions_db:
            dt = (s.get("startedAt") or datetime.now().isoformat())[:10]
            row = daily.setdefault(dt, {
                "date": dt,
                "totalCost": 0.0,
                "generatorCost": 0.0,
                "judgeCost": 0.0,
                "optimizerCost": 0.0,
                "tokensUsed": 0,
                "requests": 0,
            })
            c = float(s.get("totalCost") or 0.0)
            row["totalCost"] += c
            row["generatorCost"] += c * 0.5
            row["judgeCost"] += c * 0.3
            row["optimizerCost"] += c * 0.2
            row["requests"] += 1
        return [daily[k] for k in sorted(daily.keys())]

    return []


# ── Model Comparison ─────────────────────────────────────────────────────────

@app.post("/api/compare")
async def compare_models(body: CompareIn):
    """Compare multiple models on the same prompt."""
    await backend.ensure_initialized()

    # Normalize and validate selected models.
    supported_ids = {m["id"] for m in _supported_models()}
    requested_models: List[str] = []
    for model_name in body.models:
        if model_name in supported_ids and model_name not in requested_models:
            requested_models.append(model_name)
    unsupported_models = [m for m in body.models if m not in supported_ids]

    if len(requested_models) < 1:
        raise HTTPException(400, "No supported models selected. Choose models from /api/models.")

    # MultiModelEngine is optional and slower (sequential calls). Keep it opt-in.
    use_engine = (
        backend.multi_model_engine is not None
        and os.getenv("ASTRA_COMPARE_USE_ENGINE", "false").lower() == "true"
    )
    if use_engine:
        try:
            report = await asyncio.get_running_loop().run_in_executor(
                None, lambda: backend.multi_model_engine.compare(body.prompt, requested_models)
            )
            report_dict = report.to_dict() if hasattr(report, "to_dict") else report
            formatted = _format_comparison_report(report_dict, body.prompt, requested_models)
            if unsupported_models:
                for m in unsupported_models:
                    formatted["results"].append({
                        "model": m,
                        "answer": f"Error: Model '{m}' is not supported by this backend.",
                        "explanation": f"Error: Model '{m}' is not supported by this backend.",
                        "scores": {"correctness": 0.0, "clarity": 0.0, "reasoning": 0.0, "relevance": 0.0, "conciseness": 0.0},
                        "compositeScore": 0.0,
                        "metadata": {"tokensUsed": 0, "latencyMs": 0, "costUsd": 0, "status": "error", "error": "unsupported_model"},
                    })
                formatted["results"].sort(key=lambda r: r["compositeScore"], reverse=True)
                formatted["ranking"] = [{"model": r["model"], "rank": i + 1, "score": r["compositeScore"]} for i, r in enumerate(formatted["results"])]
                formatted["summary"] = _comparison_summary(formatted["results"])
                formatted["consistency_score"] = _comparison_consistency(formatted["results"])
            return formatted
        except Exception as e:
            logger.warning(f"MultiModelEngine compare failed: {e}, falling back to manual")

    # Fallback: manually call each model
    if backend.provider is None:
        raise HTTPException(503, "No LLM provider available")

    def _query_model_fallback(model_name: str) -> dict:
        def _call(target_model: str):
            res = backend.provider.generate(
                model_name=target_model,
                prompt=body.prompt,
                temperature=0.7,
                max_tokens=450,
            )
            txt = res.get("text", "") if isinstance(res, dict) else str(res)
            ok = bool(res.get("success", False)) if isinstance(res, dict) else bool(txt)
            err = res.get("error") if isinstance(res, dict) else None
            lat_ms = (res.get("latency_seconds", 0) if isinstance(res, dict) else 0) * 1000
            return txt, ok, err, lat_ms

        try:
            used_model = model_name
            text, success, error, latency_ms = _call(model_name)

            # Retry once with a safer routed model if primary failed.
            if (not success or not text.strip()) and backend.smart_router:
                try:
                    fallback_model = backend.smart_router.route(body.prompt)
                    if fallback_model and fallback_model != model_name:
                        fb_text, fb_success, fb_error, fb_latency_ms = _call(fallback_model)
                        if fb_success and fb_text.strip():
                            text, success, error, latency_ms = fb_text, True, None, fb_latency_ms
                            used_model = fallback_model
                        else:
                            error = error or fb_error
                except Exception:
                    pass

            if not text.strip() and error:
                text = f"Error: {error}"
            if not text.strip() and not success:
                text = "Error: No response returned by model."
                error = error or "empty_response"
            if not text.strip() and success:
                text = "No response returned by model."
                success = False
                error = error or "empty_response"

            score_pack = _score_comparison_response(body.prompt, text, success, latency_ms)
            tokens_in = max(1, len(body.prompt) // 4)
            tokens_out = max(1, len(text) // 4)

            _record_runtime_usage(
                agent="generator",
                model_name=used_model,
                prompt=body.prompt,
                response_text=text,
                cost_usd=0.0,
                success=success,
                latency_ms=latency_ms,
                endpoint="compare",
            )

            return {
                "model": model_name,
                "answer": text,
                "explanation": text,
                "scores": score_pack["scores"],
                "compositeScore": score_pack["compositeScore"],
                "metadata": {
                    "tokensUsed": tokens_in + tokens_out,
                    "latencyMs": latency_ms,
                    "costUsd": 0.0,
                    "status": "success" if success else "error",
                    "error": error,
                    "usedModel": used_model,
                },
            }
        except Exception as e:
            text = f"Error: {str(e)}"
            score_pack = _score_comparison_response(body.prompt, text, False, 0)
            return {
                "model": model_name,
                "answer": text,
                "explanation": text,
                "scores": score_pack["scores"],
                "compositeScore": score_pack["compositeScore"],
                "metadata": {"tokensUsed": 0, "latencyMs": 0, "costUsd": 0, "status": "error", "error": str(e)},
            }

    results = []
    max_workers = min(2, len(requested_models)) if requested_models else 1
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_query_model_fallback, model_name) for model_name in requested_models]
        for fut in as_completed(futures):
            results.append(fut.result())

    for m in unsupported_models:
        results.append({
            "model": m,
            "answer": f"Error: Model '{m}' is not supported by this backend.",
            "explanation": f"Error: Model '{m}' is not supported by this backend.",
            "scores": {"correctness": 0.0, "clarity": 0.0, "reasoning": 0.0, "relevance": 0.0, "conciseness": 0.0},
            "compositeScore": 0.0,
            "metadata": {"tokensUsed": 0, "latencyMs": 0, "costUsd": 0, "status": "error", "error": "unsupported_model"},
        })

    results.sort(key=lambda r: r["compositeScore"], reverse=True)
    return {
        "results": results,
        "ranking": [{"model": r["model"], "rank": i + 1, "score": r["compositeScore"]} for i, r in enumerate(results)],
        "consistency_score": _comparison_consistency(results),
        "summary": _comparison_summary(results),
    }


def _comparison_consistency(results: List[Dict[str, Any]]) -> float:
    """Compute consistency score from score spread (1=high agreement, 0=low)."""
    vals = [float(r.get("compositeScore", 0.0)) for r in results if float(r.get("compositeScore", 0.0)) > 0]
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    variance = sum((v - mean) ** 2 for v in vals) / len(vals)
    std = variance ** 0.5
    consistency = 1.0 - min(std / 3.0, 1.0)
    return round(max(0.0, min(1.0, consistency)), 2)


def _comparison_summary(results: List[Dict[str, Any]]) -> str:
    """Create a human-readable summary for comparison results."""
    if not results:
        return "No comparison results were generated."
    ok = [r for r in results if r.get("metadata", {}).get("status") == "success"]
    failed = [r for r in results if r.get("metadata", {}).get("status") != "success"]
    best = max(ok, key=lambda r: float(r.get("compositeScore", 0.0))) if ok else None
    if best:
        return (
            f"{best['model']} performed best with {best['compositeScore']:.1f}/10. "
            f"Successful models: {len(ok)}/{len(results)}."
        )
    return f"All model requests failed ({len(failed)}/{len(results)}). Check model availability and API key."


def _format_comparison_report(report_dict: dict, prompt: str, models: List[str]) -> dict:
    """Format MultiModelEngine report for the frontend."""
    raw_results = report_dict.get("results", report_dict.get("model_results", []))
    results = []
    for r in raw_results:
        if isinstance(r, dict):
            model_name = r.get("model_name", r.get("model", ""))
            response_text = r.get("response_text", r.get("answer", ""))
            success = bool(r.get("success", True))
            error = r.get("error")
            if not response_text.strip() and error:
                response_text = f"Error: {error}"
            if not response_text.strip() and success:
                response_text = "No response returned by model."
                success = False

            latency_ms = (r.get("latency_seconds", 0) or 0) * 1000
            score_pack = _score_comparison_response(prompt, response_text, success, latency_ms)
            scores = score_pack["scores"]
            composite = score_pack["compositeScore"]

            results.append({
                "model": model_name,
                "answer": response_text,
                "explanation": response_text,
                "scores": scores,
                "compositeScore": composite,
                "metadata": {
                    "tokensUsed": r.get("input_tokens_est", 0) + r.get("output_tokens_est", 0),
                    "latencyMs": latency_ms,
                    "costUsd": r.get("cost_estimate", 0),
                    "status": "success" if success else "error",
                    "error": error,
                },
            })

            try:
                if backend.model_selector:
                    from utils.model_selector import AgentType
                    in_tok = max(1, len(prompt) // 4)
                    out_tok = max(1, len(response_text) // 4)
                    backend.model_selector.record_usage(
                        agent_type=AgentType.GENERATOR,
                        model_name=model_name,
                        input_tokens=in_tok,
                        output_tokens=out_tok,
                        metadata={"endpoint": "compare", "success": success},
                    )
            except Exception:
                pass

            try:
                if backend.smart_router:
                    backend.smart_router.record_feedback(
                        prompt=prompt,
                        model_used=model_name,
                        quality_score=float(composite),
                        latency_seconds=float(latency_ms) / 1000.0,
                        cost_usd=float(r.get("cost_estimate", 0) or 0),
                        success=bool(success),
                    )
            except Exception:
                pass

            try:
                if backend.model_selector:
                    from utils.model_selector import AgentType
                    in_tok = max(1, len(prompt) // 4)
                    out_tok = max(1, len(response_text) // 4)
                    backend.model_selector.record_usage(
                        agent_type=AgentType.GENERATOR,
                        model_name=model_name,
                        input_tokens=in_tok,
                        output_tokens=out_tok,
                        metadata={"endpoint": "compare", "success": success},
                    )
            except Exception:
                pass

            try:
                if backend.smart_router:
                    backend.smart_router.record_feedback(
                        prompt=prompt,
                        model_used=model_name,
                        quality_score=float(composite),
                        latency_seconds=float(latency_ms) / 1000.0,
                        cost_usd=float(r.get("cost_estimate", 0) or 0),
                        success=bool(success),
                    )
            except Exception:
                pass

    results.sort(key=lambda x: x["compositeScore"], reverse=True)
    return {
        "results": results,
        "ranking": [{"model": r["model"], "rank": i + 1, "score": r["compositeScore"]} for i, r in enumerate(results)],
        "consistency_score": _comparison_consistency(results),
        "summary": _comparison_summary(results),
    }


def _score_comparison_response(prompt: str, response_text: str, success: bool, latency_ms: float) -> dict:
    """Heuristic scoring for comparison responses when judge scores are unavailable."""
    if not success or not response_text.strip() or response_text.lower().startswith("error:"):
        zero = {"correctness": 0.0, "clarity": 0.0, "reasoning": 0.0, "relevance": 0.0, "conciseness": 0.0}
        return {"scores": zero, "compositeScore": 0.0}

    prompt_words = set(re.findall(r"\b\w+\b", prompt.lower()))
    response_words = re.findall(r"\b\w+\b", response_text.lower())
    response_word_set = set(response_words)
    word_count = len(response_words)

    overlap = (len(prompt_words & response_word_set) / max(1, len(prompt_words))) if prompt_words else 0.0

    sentences = [s for s in re.split(r"[.!?]+\s*", response_text.strip()) if s]
    avg_sentence_words = word_count / max(1, len(sentences))

    reasoning_markers = ["because", "therefore", "however", "for example", "first", "second", "finally", "thus", "so"]
    reasoning_hits = sum(1 for marker in reasoning_markers if marker in response_text.lower())

    latency_penalty = min(max(latency_ms, 0.0) / 25000.0, 1.0)

    correctness = 6.0 + (overlap * 3.0) - (latency_penalty * 0.4)
    clarity = 8.5 - (abs(avg_sentence_words - 18) * 0.12)
    reasoning = 5.5 + (min(reasoning_hits, 6) * 0.7)
    relevance = 5.5 + (overlap * 4.5)

    ideal_words = 170
    conciseness = 10.0 - min(abs(word_count - ideal_words) / max(ideal_words, 1) * 10.0, 7.5)

    scores = {
        "correctness": round(min(10.0, max(0.0, correctness)), 1),
        "clarity": round(min(10.0, max(0.0, clarity)), 1),
        "reasoning": round(min(10.0, max(0.0, reasoning)), 1),
        "relevance": round(min(10.0, max(0.0, relevance)), 1),
        "conciseness": round(min(10.0, max(0.0, conciseness)), 1),
    }

    composite = (
        0.40 * scores["correctness"]
        + 0.20 * scores["clarity"]
        + 0.20 * scores["reasoning"]
        + 0.10 * scores["relevance"]
        + 0.10 * scores["conciseness"]
    )

    return {"scores": scores, "compositeScore": round(composite, 1)}


def _record_optimization_usage(session_id: str, results: Dict[str, Any]) -> float:
    """Best-effort cost tracking for optimization runs."""
    if not backend.model_selector or not results:
        return 0.0

    try:
        from utils.model_selector import AgentType
    except Exception:
        return 0.0

    config = results.get("config", {}) or {}
    generator_model = (
        config.get("generatorModel")
        or config.get("model")
        or config.get("generator_model")
    )
    judge_model = (
        config.get("judgeModel")
        or config.get("judge_model")
        or generator_model
    )
    optimizer_model = (
        config.get("optimizerModel")
        or config.get("optimizer_model")
        or generator_model
    )
    if not generator_model:
        return 0.0

    initial_prompt = (
        results.get("initial_prompt_used")
        or results.get("initialPrompt")
        or results.get("initial_prompt")
        or ""
    )
    iteration_logs = results.get("raw_results", {}).get("iterations", [])
    if not iteration_logs:
        return 0.0

    total_cost = 0.0
    judge_overhead_chars = 900
    optimizer_overhead_chars = 700
    for idx, log in enumerate(iteration_logs):
        prompt_used = initial_prompt if idx == 0 else iteration_logs[idx - 1].get("prompt", initial_prompt)
        if not prompt_used:
            prompt_used = log.get("prompt", "")

        outputs = log.get("generated_outputs", []) or []
        evaluations = log.get("evaluations", []) or []
        for output_idx, output in enumerate(outputs):
            question = str(output.get("question", "") or "")
            if "{question}" in prompt_used:
                prompt_text = prompt_used.replace("{question}", question)
            else:
                prompt_text = f"{prompt_used}\n\nQuestion: {question}".strip()

            answer_text = str(output.get("answer") or output.get("explanation") or "")
            in_tok = max(1, len(prompt_text) // 4)
            out_tok = max(1, len(answer_text) // 4)

            try:
                cost = backend.model_selector.record_usage(
                    agent_type=AgentType.GENERATOR,
                    model_name=generator_model,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    metadata={
                        "endpoint": "optimize",
                        "session_id": session_id,
                        "iteration": log.get("iteration", idx + 1),
                    },
                )
                total_cost += float(cost or 0.0)
            except Exception:
                pass

            if judge_model:
                eval_result = evaluations[output_idx] if output_idx < len(evaluations) else {}
                explanation_text = str(output.get("explanation") or answer_text or "")
                judge_prompt = (
                    f"Question: {question}\n"
                    f"Answer: {answer_text}\n"
                    f"Explanation: {explanation_text}\n"
                )
                judge_in = max(1, (len(judge_prompt) + judge_overhead_chars) // 4)
                judge_out = max(1, len(json.dumps(eval_result)) // 4)
                try:
                    cost = backend.model_selector.record_usage(
                        agent_type=AgentType.JUDGE,
                        model_name=judge_model,
                        input_tokens=judge_in,
                        output_tokens=judge_out,
                        metadata={
                            "endpoint": "optimize",
                            "session_id": session_id,
                            "iteration": log.get("iteration", idx + 1),
                        },
                    )
                    total_cost += float(cost or 0.0)
                except Exception:
                    pass

        if optimizer_model:
            eval_summary = json.dumps(evaluations)
            optimizer_in = max(1, (len(prompt_used) + len(eval_summary) + optimizer_overhead_chars) // 4)
            optimized_prompt = str(log.get("prompt") or "")
            optimizer_out = max(1, len(optimized_prompt) // 4)
            try:
                cost = backend.model_selector.record_usage(
                    agent_type=AgentType.OPTIMIZER,
                    model_name=optimizer_model,
                    input_tokens=optimizer_in,
                    output_tokens=optimizer_out,
                    metadata={
                        "endpoint": "optimize",
                        "session_id": session_id,
                        "iteration": log.get("iteration", idx + 1),
                    },
                )
                total_cost += float(cost or 0.0)
            except Exception:
                pass

    return total_cost


def _record_runtime_usage(agent: str, model_name: str, prompt: str, response_text: str, cost_usd: float, success: bool, latency_ms: float, endpoint: str):
    """Best-effort unified telemetry recording for charts and router stats."""
    try:
        if backend.model_selector:
            from utils.model_selector import AgentType
            agent_map = {
                "generator": AgentType.GENERATOR,
                "judge": AgentType.JUDGE,
                "optimizer": AgentType.OPTIMIZER,
            }
            agent_type = agent_map.get(agent, AgentType.GENERATOR)
            in_tok = max(1, len(prompt) // 4)
            out_tok = max(1, len(response_text) // 4)
            backend.model_selector.record_usage(
                agent_type=agent_type,
                model_name=model_name,
                input_tokens=in_tok,
                output_tokens=out_tok,
                metadata={"endpoint": endpoint, "success": success},
            )
    except Exception:
        pass

    try:
        if backend.smart_router:
            quality = _score_comparison_response(prompt, response_text, success, latency_ms).get("compositeScore", 0)
            backend.smart_router.record_feedback(
                prompt=prompt,
                model_used=model_name,
                quality_score=float(quality),
                latency_seconds=float(latency_ms) / 1000.0,
                cost_usd=float(cost_usd or 0.0),
                success=bool(success),
            )
    except Exception:
        pass


# ── Sessions ─────────────────────────────────────────────────────────────────

@app.get("/api/sessions")
async def list_sessions():
    """List all optimization sessions."""
    await backend.ensure_initialized()
    return sorted(backend.sessions_db, key=lambda s: s.get("startedAt", ""), reverse=True)


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get detailed info for a session."""
    await backend.ensure_initialized()
    summary = next((s for s in backend.sessions_db if s["sessionId"] == session_id), None)
    if summary is None:
        raise HTTPException(404, "Session not found")

    detail = dict(summary)
    raw = backend.session_results.get(session_id, {})
    detail["finalPrompt"] = raw.get("final_prompt", "")
    detail["performanceHistory"] = raw.get("performance_history", [])

    # Build iteration logs from raw_results
    raw_iterations = raw.get("raw_results", {}).get("iterations", [])
    iteration_logs = []
    for it in raw_iterations:
        scores = it.get("per_question_scores", [{}])[0].get("scores", {}) if it.get("per_question_scores") else {}
        composite = it.get("score", 0)
        iteration_logs.append({
            "iteration": it.get("iteration", 0),
            "prompt": it.get("prompt", ""),
            "score": composite,
            "compositeScore": composite,
            "avgCompositeScore": composite,
            "averageScores": scores,
            "avgScores": scores,
            "evaluations": it.get("evaluations", []),
            "generatedOutputs": it.get("generated_outputs", []),
            "timestamp": it.get("timestamp", datetime.now().isoformat()),
            "weakCriteria": it.get("weak_criteria", []),
            "strongCriteria": it.get("strong_criteria", []),
            "optimizationModifications": it.get("optimization_modifications", []),
            "durationSeconds": it.get("duration_seconds", 0),
        })

    detail["iterationLogs"] = iteration_logs
    detail["config"] = raw.get("config", {})
    return detail


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    await backend.ensure_initialized()
    idx = next((i for i, s in enumerate(backend.sessions_db) if s["sessionId"] == session_id), None)
    if idx is None:
        raise HTTPException(404, "Session not found")
    backend.sessions_db.pop(idx)
    backend.session_results.pop(session_id, None)
    return {"status": "deleted"}


# ── Optimization (start) ────────────────────────────────────────────────────

@app.post("/api/optimize/start")
async def start_optimization(body: OptimizationConfigIn):
    """Start an optimization run. Returns sessionId immediately. 
    The frontend should connect via WebSocket or poll for results."""
    await backend.ensure_initialized()

    session_id = "sess_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    session = {
        "sessionId": session_id,
        "startedAt": datetime.now().isoformat(),
        "status": "running",
        "totalIterations": 0,
        "initialScore": 0,
        "finalScore": 0,
        "improvement": 0,
        "converged": False,
        "model": body.generatorModel or body.model or ("claude-3-opus" if os.getenv("ANTHROPIC_API_KEY") else "Qwen/Qwen2.5-72B-Instruct"),
        "totalCost": 0,
        "questionsCount": 0,
        "durationSeconds": 0,
    }
    backend.sessions_db.append(session)
    backend.session_progress[session_id] = {
        "status": "running",
        "phase": "initializing",
        "iteration": 0,
        "totalIterations": body.maxIterations or 10,
        "elapsedSeconds": 0.0,
        "etaSeconds": None,
        "lastUpdate": datetime.now().isoformat(),
    }

    # Get questions to use
    questions = []
    if body.questionIds:
        for qid in body.questionIds:
            q = next((q for q in backend.questions_db if q["id"] == qid), None)
            if q:
                questions.append(q["question"])
    if not questions:
        # Use first 5 questions
        questions = [q["question"] for q in backend.questions_db[:5]]

    # Merge custom questions from the frontend
    if body.customQuestions:
        for cq in body.customQuestions:
            cq = cq.strip()
            if cq and cq not in questions:
                questions.append(cq)

    session["questionsCount"] = len(questions)

    # Run optimization in background
    asyncio.create_task(_run_optimization_task(session_id, questions, body))

    _save_sessions_to_disk()
    return {"sessionId": session_id}


async def _run_optimization_task(session_id: str, questions: List[str], config: OptimizationConfigIn):
    """Background task to run the optimization loop."""
    session = next((s for s in backend.sessions_db if s["sessionId"] == session_id), None)
    if session is None:
        return

    # Hard cap questions to avoid very long runs.
    # Each question triggers generation + evaluation per iteration.
    hard_cap = 5
    max_q = min(len(questions), config.batchSize or hard_cap, hard_cap)
    questions = questions[:max_q]
    session["questionsCount"] = len(questions)

    start_time = datetime.now()
    progress_task = asyncio.create_task(_progress_heartbeat(session_id, start_time, config.maxIterations or 10))
    try:
        # Try to use LangGraph orchestrator
        from agents import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            from agents import create_langchain_orchestrator
            from config import get_config
            cfg = get_config()

            gen_model = config.generatorModel or config.model or cfg.generator_model.get('model_name', 'meta-llama/Meta-Llama-3-8B-Instruct')
            judge_model = config.judgeModel or cfg.judge_model.get('model_name', 'meta-llama/Meta-Llama-3-8B-Instruct')
            opt_model = config.optimizerModel or cfg.optimizer_model.get('model_name', 'meta-llama/Meta-Llama-3-8B-Instruct')
            temperature = config.temperature or 0.7
            max_tokens = config.maxTokens or 500

            # Speed mode for tiny runs: use faster open-source models to keep UX responsive.
            speed_mode_applied = False
            if len(questions) <= 1 and ("72B" in gen_model or "32B" in gen_model):
                gen_model = "meta-llama/Meta-Llama-3-8B-Instruct"
                judge_model = "meta-llama/Meta-Llama-3-8B-Instruct"
                opt_model = "meta-llama/Meta-Llama-3-8B-Instruct"
                max_tokens = min(max_tokens, 320)
                speed_mode_applied = True

            orchestrator = create_langchain_orchestrator(
                generator_model=gen_model,
                judge_model=judge_model,
                optimizer_model=opt_model,
                max_iterations=config.maxIterations or 10,
                convergence_threshold=config.convergenceThreshold or 8.5,
                enable_langsmith=False,
                temperature=temperature,
                max_tokens=max_tokens,
                judge_max_tokens=320,
                optimizer_max_tokens=600,
            )

            initial_prompt = config.initialPrompt
            if not initial_prompt:
                # Use template if specified
                if config.templateId:
                    from utils.prompt_templates import get_template
                    tmpl = get_template(config.templateId)
                    if tmpl:
                        initial_prompt = tmpl.template
                
                if not initial_prompt:
                    initial_prompt = (
                        "Answer the following question clearly and concisely.\n\n"
                        "Question: {question}\n\n"
                        "Provide your answer with a clear explanation.\n\n"
                        "Answer:"
                    )

            # Store config info for results
            config_info = {
                "generatorModel": gen_model,
                "judgeModel": judge_model,
                "optimizerModel": opt_model,
                "temperature": temperature,
                "maxTokens": max_tokens,
                "templateId": config.templateId or "custom",
                "questionsCount": len(questions),
                "speedModeApplied": speed_mode_applied,
            }

            results = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: orchestrator.run_optimization(questions, initial_prompt)
            )

            # Attach config to results
            results["config"] = config_info
            results["initial_prompt_used"] = initial_prompt

            recorded_cost = _record_optimization_usage(session_id, results)
            if recorded_cost > 0:
                results["total_cost"] = max(float(results.get("total_cost", 0) or 0), recorded_cost)

            duration = (datetime.now() - start_time).total_seconds()

            session["status"] = "completed"
            session["totalIterations"] = results.get("iterations", 0)
            session["initialScore"] = results.get("initial_score", 0)
            session["finalScore"] = results.get("final_score", 0)
            session["improvement"] = results.get("improvement", 0)
            session["converged"] = results.get("converged", False)
            session["durationSeconds"] = duration
            session["totalCost"] = results.get("total_cost", 0)

            backend.session_results[session_id] = results
            backend.session_results[session_id]["duration_seconds"] = duration
            backend.session_results[session_id]["timestamp"] = start_time.isoformat()
            backend.session_progress[session_id] = {
                "status": "completed",
                "phase": "complete",
                "iteration": results.get("iterations", 0),
                "totalIterations": config.maxIterations or 10,
                "elapsedSeconds": duration,
                "etaSeconds": 0,
                "lastUpdate": datetime.now().isoformat(),
            }

            _save_sessions_to_disk()

            # Notify connected WebSocket clients
            await _broadcast_ws(session_id, {
                "type": "complete",
                "data": _build_optimization_results(session_id, results, duration)
            })
        else:
            session["status"] = "error"
            backend.session_progress[session_id] = {
                "status": "error",
                "phase": "error",
                "iteration": 0,
                "totalIterations": config.maxIterations or 10,
                "elapsedSeconds": (datetime.now() - start_time).total_seconds(),
                "etaSeconds": None,
                "lastUpdate": datetime.now().isoformat(),
            }
            await _broadcast_ws(session_id, {"type": "error", "data": {"agent": "orchestrator", "message": "LangChain not available", "recoverable": False}})

    except Exception as e:
        logger.error(f"Optimization error for {session_id}: {e}")
        logger.error(traceback.format_exc())
        session["status"] = "error"
        backend.session_progress[session_id] = {
            "status": "error",
            "phase": "error",
            "iteration": 0,
            "totalIterations": config.maxIterations or 10,
            "elapsedSeconds": (datetime.now() - start_time).total_seconds(),
            "etaSeconds": None,
            "lastUpdate": datetime.now().isoformat(),
        }
        await _broadcast_ws(session_id, {"type": "error", "data": {"agent": "orchestrator", "message": str(e), "recoverable": False}})
    finally:
        if progress_task:
            progress_task.cancel()


async def _progress_heartbeat(session_id: str, start_time: datetime, total_iterations: int):
    """Emit lightweight phase updates while optimization is running.

    This provides visible intermediate progress even when the underlying
    orchestrator only returns final results at completion.
    """
    phases = ["generation", "evaluation", "optimization"]
    tick = 0
    while True:
        await asyncio.sleep(2)
        session = next((s for s in backend.sessions_db if s["sessionId"] == session_id), None)
        if not session or session.get("status") != "running":
            return

        elapsed = max((datetime.now() - start_time).total_seconds(), 0.0)
        # Heuristic pacing: ~14s per iteration by default.
        est_iter = min(total_iterations, max(0, int(elapsed // 14)))
        phase = phases[tick % len(phases)]
        eta = max(0.0, (total_iterations - est_iter) * 14.0)

        progress = {
            "status": "running",
            "phase": phase,
            "iteration": est_iter,
            "totalIterations": total_iterations,
            "elapsedSeconds": round(elapsed, 1),
            "etaSeconds": round(eta, 1),
            "lastUpdate": datetime.now().isoformat(),
        }
        backend.session_progress[session_id] = progress
        await _broadcast_ws(session_id, {"type": "iteration_start", "data": progress})
        tick += 1


def _build_optimization_results(session_id: str, results: dict, duration: float) -> dict:
    """Build OptimizationResults shape for the frontend."""
    raw_iterations = results.get("raw_results", {}).get("iterations", [])
    iteration_logs = []
    for it in raw_iterations:
        scores = it.get("per_question_scores", [{}])[0].get("scores", {}) if it.get("per_question_scores") else {}
        composite = it.get("score", 0)
        iteration_logs.append({
            "iteration": it.get("iteration", 0),
            "prompt": it.get("prompt", ""),
            "score": composite,
            "compositeScore": composite,
            "avgCompositeScore": composite,
            "averageScores": scores,
            "avgScores": scores,
            "evaluations": it.get("evaluations", []),
            "generatedOutputs": it.get("generated_outputs", []),
            "timestamp": it.get("timestamp", datetime.now().isoformat()),
            "weakCriteria": it.get("weak_criteria", []),
            "strongCriteria": it.get("strong_criteria", []),
            "optimizationModifications": it.get("optimization_modifications", []),
            "durationSeconds": it.get("duration_seconds", 0),
        })

    return {
        "sessionId": session_id,
        "finalPrompt": results.get("final_prompt", ""),
        "initialPrompt": results.get("initial_prompt_used", ""),
        "initialScore": results.get("initial_score", 0),
        "finalScore": results.get("final_score", 0),
        "improvement": results.get("improvement", 0),
        "iterations": results.get("iterations", 0),
        "converged": results.get("converged", False),
        "convergenceReason": "Score exceeded convergence threshold" if results.get("converged") else "Max iterations reached",
        "performanceHistory": results.get("performance_history", []),
        "iterationLogs": iteration_logs,
        "totalCost": results.get("total_cost", 0),
        "totalDurationSeconds": duration,
        "config": results.get("config", {}),
    }


@app.get("/api/optimize/{session_id}/results")
async def get_optimization_results(session_id: str):
    """Get optimization results for a session."""
    await backend.ensure_initialized()
    session = next((s for s in backend.sessions_db if s["sessionId"] == session_id), None)
    if session is None:
        raise HTTPException(404, "Session not found")

    raw = backend.session_results.get(session_id, {})
    duration = raw.get("duration_seconds", session.get("durationSeconds", 0))
    return _build_optimization_results(session_id, raw, duration)


@app.get("/api/optimize/{session_id}/progress")
async def get_optimization_progress(session_id: str):
    """Get lightweight intermediate progress for long-running optimization."""
    await backend.ensure_initialized()
    session = next((s for s in backend.sessions_db if s["sessionId"] == session_id), None)
    if session is None:
        raise HTTPException(404, "Session not found")

    progress = backend.session_progress.get(session_id, {
        "status": session.get("status", "unknown"),
        "phase": "unknown",
        "iteration": 0,
        "totalIterations": session.get("totalIterations", 0),
        "elapsedSeconds": session.get("durationSeconds", 0),
        "etaSeconds": None,
        "lastUpdate": datetime.now().isoformat(),
    })
    return progress


@app.post("/api/optimize/stop/{session_id}")
async def stop_optimization(session_id: str):
    """Stop a running optimization (best-effort)."""
    await backend.ensure_initialized()
    session = next((s for s in backend.sessions_db if s["sessionId"] == session_id), None)
    if session is None:
        raise HTTPException(404, "Session not found")
    session["status"] = "stopped"
    return {"status": "stopped"}


# ── Router Stats ─────────────────────────────────────────────────────────────

@app.get("/api/router/stats")
async def get_router_stats():
    """Get smart router statistics."""
    await backend.ensure_initialized()
    if backend.smart_router is None:
        return {"total_routings": 0, "totalRoutings": 0, "total_cost": 0, "avgScore": 0, "avgLatency": 0, "modelUsage": [], "per_model": {}}

    try:
        stats = backend.smart_router.get_router_stats() if hasattr(backend.smart_router, "get_router_stats") else {}
        if isinstance(stats, dict):
            per_model = stats.get("models", {})
            model_usage = [
                {"model": name, "count": int(m.get("uses", 0))}
                for name, m in per_model.items()
            ]
            model_usage.sort(key=lambda x: x["count"], reverse=True)

            uses = [float(m.get("uses", 0)) for m in per_model.values()]
            weighted_scores = [float(m.get("avg_score", 0)) * float(m.get("uses", 0)) for m in per_model.values()]
            total_uses = sum(uses)
            avg_score = (sum(weighted_scores) / total_uses) if total_uses > 0 else 0.0

            # Compute avg latency from feedback history if available.
            avg_latency_ms = 0.0
            fb = getattr(backend.smart_router, "feedback_history", [])
            if fb:
                avg_latency_ms = sum(float(x.latency_seconds) for x in fb) / len(fb) * 1000

            return {
                "total_routings": int(stats.get("total_routings", 0)),
                "totalRoutings": int(stats.get("total_routings", 0)),
                "total_cost": float(stats.get("total_cost", 0.0)),
                "avgScore": round(avg_score, 2),
                "avgLatency": round(avg_latency_ms, 1),
                "modelUsage": model_usage,
                "per_model": per_model,
            }
    except Exception as e:
        logger.warning(f"Router stats error: {e}")

    return {"total_routings": 0, "totalRoutings": 0, "total_cost": 0, "avgScore": 0, "avgLatency": 0, "modelUsage": [], "per_model": {}}


# ── Debug Log ────────────────────────────────────────────────────────────────

@app.get("/api/debug/log")
async def get_debug_log():
    """Get debug log entries."""
    await backend.ensure_initialized()
    if backend.mode_manager is None:
        return []

    try:
        raw_log = backend.mode_manager.get_debug_log() if hasattr(backend.mode_manager, "get_debug_log") else []
        return [
            {
                "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                "agent": entry.get("agent", "system"),
                "type": entry.get("type", "debug"),
                "label": entry.get("label", ""),
                "data": entry.get("data", ""),
            }
            for entry in (raw_log if isinstance(raw_log, list) else [])
        ]
    except Exception:
        return []


# ── Settings ─────────────────────────────────────────────────────────────────

@app.get("/api/settings")
async def get_settings():
    """Get current system settings."""
    await backend.ensure_initialized()
    try:
        from config import get_config
        config = get_config()
        return {
            "generatorModel": config.generator_model.get("model_name", ""),
            "judgeModel": config.judge_model.get("model_name", ""),
            "optimizerModel": config.optimizer_model.get("model_name", ""),
            "maxIterations": config.max_iterations,
            "convergenceThreshold": config.convergence_threshold,
            "temperature": config.generator_model.get("temperature", 0.7),
            "maxTokens": config.generator_model.get("max_tokens", 500),
            "weights": config.evaluation_weights,
        }
    except Exception as e:
        return {"error": str(e)}


@app.put("/api/settings")
async def update_settings(body: SettingsIn):
    """Update system settings (runtime only, does not persist to config.yaml)."""
    await backend.ensure_initialized()
    try:
        from config import get_config
        config = get_config()
        if body.generatorModel:
            config.config['models']['generator']['model_name'] = body.generatorModel
        if body.judgeModel:
            config.config['models']['judge']['model_name'] = body.judgeModel
        if body.optimizerModel:
            config.config['models']['optimizer']['model_name'] = body.optimizerModel
        if body.maxIterations is not None:
            config.config['optimization']['max_iterations'] = body.maxIterations
        if body.convergenceThreshold is not None:
            config.config['optimization']['convergence_threshold'] = body.convergenceThreshold
        if body.temperature is not None:
            config.config['models']['generator']['temperature'] = body.temperature
        if body.maxTokens is not None:
            config.config['models']['generator']['max_tokens'] = body.maxTokens
        if body.huggingfaceToken:
            os.environ["HUGGINGFACE_API_KEY"] = body.huggingfaceToken
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(500, f"Settings update failed: {str(e)}")


# ── WebSocket for real-time optimization updates ────────────────────────────

_ws_connections: Dict[str, List[WebSocket]] = {}


@app.websocket("/ws/optimize/{session_id}")
async def ws_optimize(ws: WebSocket, session_id: str):
    """WebSocket endpoint for real-time optimization progress."""
    await ws.accept()
    if session_id not in _ws_connections:
        _ws_connections[session_id] = []
    _ws_connections[session_id].append(ws)
    try:
        while True:
            # Keep connection alive; client may send stop commands
            data = await ws.receive_text()
            if data == "stop":
                session = next((s for s in backend.sessions_db if s["sessionId"] == session_id), None)
                if session:
                    session["status"] = "stopped"
                await ws.send_json({"type": "stopped", "data": {"reason": "User requested stop"}})
                break
    except WebSocketDisconnect:
        pass
    finally:
        if session_id in _ws_connections:
            _ws_connections[session_id] = [c for c in _ws_connections[session_id] if c != ws]


async def _broadcast_ws(session_id: str, message: dict):
    """Broadcast a message to all WebSocket clients for a session."""
    if session_id not in _ws_connections:
        return
    dead = []
    for ws in _ws_connections[session_id]:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_connections[session_id].remove(ws)


# ── Prompt Templates ─────────────────────────────────────────────────────────

@app.get("/api/templates")
async def list_templates():
    """List all available prompt templates."""
    from utils.prompt_templates import list_templates
    return list_templates()


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Get a single prompt template by ID."""
    from utils.prompt_templates import get_template
    t = get_template(template_id)
    if t is None:
        raise HTTPException(404, "Template not found")
    return t.to_dict()


@app.post("/api/templates/auto-select")
async def auto_select_template(body: AskIn):
    """Auto-select the best template for a question."""
    await backend.ensure_initialized()
    from utils.prompt_templates import auto_select_template, detect_intent

    # Detect complexity via SmartRouter
    complexity = "moderate"
    if backend.smart_router:
        try:
            complexity = backend.smart_router.detect_complexity(body.question).lower()
        except Exception:
            pass

    category = body.category or "general"
    intent = detect_intent(body.question)
    template = auto_select_template(body.question, category=category, complexity=complexity)

    return {
        "selectedTemplate": template.to_dict(),
        "detectedIntent": intent,
        "detectedComplexity": complexity,
        "category": category,
        "renderedPrompt": template.render(body.question),
    }


# ── Question Testing ─────────────────────────────────────────────────────────

@app.post("/api/questions/{question_id}/test")
async def test_question(question_id: str, body: QuestionTestIn):
    """Run a question through the LLM and return a full structured answer.
    Also runs evaluation against ground truth if available."""
    await backend.ensure_initialized()
    if backend.provider is None:
        raise HTTPException(503, "HuggingFace provider not available")

    # Find question
    q = next((q for q in backend.questions_db if q["id"] == question_id), None)
    if q is None:
        raise HTTPException(404, "Question not found")

    # Select template
    from utils.prompt_templates import get_template_for_question
    category = q.get("category", "general")

    # Detect complexity
    complexity = "moderate"
    if backend.smart_router:
        try:
            complexity = backend.smart_router.detect_complexity(q["question"]).lower()
        except Exception:
            pass

    template = get_template_for_question(
        q["question"], category=category, complexity=complexity,
        preferred_id=body.templateId,
    )
    full_prompt = template.render(q["question"])

    # Add context engineering to test runs as well for consistent behavior.
    context_used = _build_context_pack(q["question"], category)
    if context_used and context_used.get("contextText"):
        full_prompt = (
            f"{context_used['contextText']}\n\n"
            f"Use this context only when relevant and keep facts grounded.\n\n"
            f"{full_prompt}"
        )

    model = body.model or ("claude-3-opus" if os.getenv("ANTHROPIC_API_KEY") else "Qwen/Qwen2.5-72B-Instruct")

    try:
        result = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: backend.provider.generate(
                model_name=model,
                prompt=full_prompt,
                temperature=body.temperature or 0.7,
                max_tokens=body.maxTokens or 500,
            )
        )
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {str(e)}")

    response_text = result.get("text", "") if isinstance(result, dict) else str(result)
    latency = result.get("latency_seconds", 0) if isinstance(result, dict) else 0

    # Evaluate against ground truth if available
    evaluation = None
    ground_truth = q.get("groundTruth", "")
    if ground_truth:
        evaluation = _evaluate_response_against_ground_truth(response_text, ground_truth)
    else:
        evaluation = {
            "hasGroundTruth": False,
            "groundTruth": "",
            "matchScore": None,
            "verdict": "NO_GROUND_TRUTH",
            "notes": ["Add ground truth to enable reliability scoring."],
        }

    tokens_est = max(1, len(full_prompt) // 4)
    output_tokens_est = max(1, len(response_text) // 4)
    cost_est_usd = _estimate_cost_usd(model, tokens_est, output_tokens_est)

    return {
        "question": q["question"],
        "questionId": question_id,
        "category": category,
        "difficulty": q.get("difficulty", "medium"),
        "answer": response_text,
        "fullResponse": response_text,
        "templateUsed": template.id,
        "templateName": template.name,
        "promptUsed": full_prompt,
        "context": context_used,
        "evaluation": evaluation,
        "metadata": {
            "model": model,
            "tokens_used": tokens_est + output_tokens_est,
            "input_tokens": tokens_est,
            "output_tokens": output_tokens_est,
            "cost_usd": cost_est_usd,
            "latency_ms": latency * 1000,
            "temperature": body.temperature or 0.7,
            "maxTokens": body.maxTokens or 500,
            "timestamp": datetime.now().isoformat(),
        },
    }


def _simple_match_score(response: str, ground_truth: str) -> float:
    """Backward-compatible score wrapper used by older callers."""
    evaluation = _evaluate_response_against_ground_truth(response, ground_truth)
    return float(evaluation.get("matchScore") or 0.0)


_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "to", "of", "in", "on",
    "for", "with", "as", "at", "by", "and", "or", "if", "then", "than", "that", "this", "it", "its",
    "from", "into", "about", "over", "under", "between", "also", "can", "could", "should", "would",
    "do", "does", "did", "have", "has", "had", "will", "may", "might", "not", "no", "yes", "your",
    "you", "we", "they", "their", "our", "he", "she", "his", "her", "them", "which", "what", "when",
    "where", "why", "how", "who", "whom", "whose"
}


def _tokenize_text(text: str) -> List[str]:
    return re.findall(r"\b[a-zA-Z0-9_]+\b", (text or "").lower())


def _keywords(text: str) -> List[str]:
    return [t for t in _tokenize_text(text) if len(t) > 2 and t not in _STOPWORDS]


def _evaluate_response_against_ground_truth(response: str, ground_truth: str) -> dict:
    """Richer evaluation than plain overlap for Question Bank testing.

    Combines lexical overlap, sequence similarity, and key-concept coverage.
    Returns a 0-10 score plus detailed sub-metrics so the UI can explain why.
    """
    response = response or ""
    ground_truth = ground_truth or ""
    if not ground_truth.strip():
        return {"hasGroundTruth": False, "groundTruth": "", "matchScore": None}

    r_all = _tokenize_text(response)
    g_all = _tokenize_text(ground_truth)
    r_kw = set(_keywords(response))
    g_kw = set(_keywords(ground_truth))

    if not g_kw:
        seq = SequenceMatcher(None, response.lower(), ground_truth.lower()).ratio()
        score = round(min(max(seq * 10.0, 0.0), 10.0), 1)
        return {
            "hasGroundTruth": True,
            "groundTruth": ground_truth,
            "matchScore": score,
            "verdict": "GOOD" if score >= 7.0 else "WEAK",
            "details": {
                "keywordPrecision": 0.0,
                "keywordRecall": 0.0,
                "keywordF1": 0.0,
                "sequenceSimilarity": round(seq, 3),
                "conceptCoverage": 0.0,
            },
            "notes": [],
        }

    overlap = r_kw & g_kw
    precision = len(overlap) / max(1, len(r_kw))
    recall = len(overlap) / max(1, len(g_kw))
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    seq = SequenceMatcher(None, response.lower(), ground_truth.lower()).ratio()
    concept_coverage = len(overlap) / max(1, len(g_kw))

    # Penalize obvious verbosity mismatch (answer too short vs truth detail).
    brevity_ratio = len(r_all) / max(1, len(g_all))
    brevity_penalty = 0.0
    if brevity_ratio < 0.45:
        brevity_penalty = min((0.45 - brevity_ratio) * 4.0, 1.5)

    composite = (
        0.45 * f1
        + 0.25 * seq
        + 0.30 * concept_coverage
    ) * 10.0 - brevity_penalty
    match_score = round(min(max(composite, 0.0), 10.0), 1)

    notes: List[str] = []
    if recall < 0.5:
        notes.append("Missing several key concepts from the ground truth.")
    if precision < 0.45:
        notes.append("Includes many terms not aligned with expected answer.")
    if brevity_penalty > 0:
        notes.append("Answer may be too short to cover expected depth.")

    if match_score >= 8.0:
        verdict = "STRONG"
    elif match_score >= 6.0:
        verdict = "GOOD"
    elif match_score >= 4.0:
        verdict = "PARTIAL"
    else:
        verdict = "WEAK"

    return {
        "hasGroundTruth": True,
        "groundTruth": ground_truth,
        "matchScore": match_score,
        "verdict": verdict,
        "details": {
            "keywordPrecision": round(precision, 3),
            "keywordRecall": round(recall, 3),
            "keywordF1": round(f1, 3),
            "sequenceSimilarity": round(seq, 3),
            "conceptCoverage": round(concept_coverage, 3),
            "brevityRatio": round(brevity_ratio, 3),
        },
        "notes": notes,
    }


def _build_context_pack(question: str, category: str, max_items: int = 3) -> Optional[dict]:
    """Build a small context pack from existing question bank entries.

    This is lightweight context engineering: retrieve nearby examples and
    known ground-truth snippets in the same category to reduce hallucinations.
    """
    q_words = set(_keywords(question))
    if not q_words:
        return None

    scored: List[tuple] = []
    for item in backend.questions_db:
        item_q = item.get("question", "")
        if not item_q or item_q.strip().lower() == question.strip().lower():
            continue
        if category and item.get("category") != category:
            continue

        item_words = set(_keywords(item_q))
        if not item_words:
            continue
        overlap = len(q_words & item_words)
        if overlap <= 0:
            continue
        score = overlap / max(1, len(q_words | item_words))
        scored.append((score, item))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = scored[:max_items]

    snippets = []
    related = []
    for _, item in picked:
        q_txt = item.get("question", "")
        gt_txt = (item.get("groundTruth") or "").strip()
        related.append({"id": item.get("id"), "question": q_txt, "hasGroundTruth": bool(gt_txt)})
        if gt_txt:
            snippets.append(f"- Related fact: {gt_txt[:220]}")
        else:
            snippets.append(f"- Related question: {q_txt[:180]}")

    context_text = "\n".join([
        "Context Pack (retrieved from internal question bank):",
        *snippets,
        "Use only relevant facts; if uncertain, explicitly say uncertainty.",
    ])

    return {
        "category": category,
        "related": related,
        "contextText": context_text,
    }


def _estimate_cost_usd(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate request cost from SmartRouter profiles if available."""
    try:
        if backend.smart_router and hasattr(backend.smart_router, "profiles"):
            profile = backend.smart_router.profiles.get(model_name)
            if profile:
                cost = (input_tokens / 1000.0) * float(profile.cost_input_per_1k)
                cost += (output_tokens / 1000.0) * float(profile.cost_output_per_1k)
                return round(max(cost, 0.0), 6)
    except Exception:
        pass
    return 0.0


def _aggregate_daily_cost_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate usage records into CostTrackingPage-compatible daily rows."""
    daily: Dict[str, Dict[str, Any]] = {}

    for r in records:
        ts = str(r.get("timestamp") or datetime.now().isoformat())
        date_key = ts[:10]
        agent = str(r.get("agent_type") or "generator").lower()
        cost = float(r.get("cost") or 0.0)
        in_tok = int(r.get("input_tokens") or 0)
        out_tok = int(r.get("output_tokens") or 0)

        row = daily.setdefault(date_key, {
            "date": date_key,
            "totalCost": 0.0,
            "generatorCost": 0.0,
            "judgeCost": 0.0,
            "optimizerCost": 0.0,
            "tokensUsed": 0,
            "requests": 0,
        })

        row["totalCost"] += cost
        row["tokensUsed"] += in_tok + out_tok
        row["requests"] += 1

        if agent == "judge":
            row["judgeCost"] += cost
        elif agent == "optimizer":
            row["optimizerCost"] += cost
        else:
            row["generatorCost"] += cost

    rows = []
    for k in sorted(daily.keys()):
        d = daily[k]
        rows.append({
            "date": d["date"],
            "totalCost": round(float(d["totalCost"]), 6),
            "generatorCost": round(float(d["generatorCost"]), 6),
            "judgeCost": round(float(d["judgeCost"]), 6),
            "optimizerCost": round(float(d["optimizerCost"]), 6),
            "tokensUsed": int(d["tokensUsed"]),
            "requests": int(d["requests"]),
        })
    return rows


# ── Smart Router Explain ──────────────────────────────────────────────────────

@app.post("/api/router/explain")
async def explain_routing(body: RouterExplainIn):
    """Explain how SmartRouter would route a given question."""
    await backend.ensure_initialized()
    if backend.smart_router is None:
        raise HTTPException(503, "Smart router not available")

    return _explain_routing(body.question, body.category or "general")


def _explain_routing(question: str, category: str) -> dict:
    """Build routing explanation dict."""
    sr = backend.smart_router

    # Complexity detection
    complexity = sr.detect_complexity(question)

    # Cost prediction
    from dataclasses import asdict
    cost_pred = sr.predict_cost(question)
    cost_dict = asdict(cost_pred) if hasattr(cost_pred, "__dataclass_fields__") else cost_pred

    # Route recommendation
    route = None
    try:
        route = sr.route(question)
    except Exception:
        pass

    recommended_model = cost_dict.get("recommended_model", "")
    alternatives = cost_dict.get("alternative_models", [])

    # Build explanation
    reasons = []
    if complexity == "SIMPLE":
        reasons.append("Question is simple — a lightweight model is sufficient")
    elif complexity == "MODERATE":
        reasons.append("Question has moderate complexity — balanced model recommended")
    elif complexity == "COMPLEX":
        reasons.append("Question is complex — a high-capability model is needed")
    elif complexity == "CRITICAL":
        reasons.append("Question is critical/complex — using the best available model")

    code_keywords = ["code", "function", "implement", "debug", "program"]
    if any(kw in question.lower() for kw in code_keywords):
        reasons.append("Code-related content detected — preferring code-capable models")

    reasoning_keywords = ["why", "explain", "prove", "derive", "analyze"]
    if any(kw in question.lower() for kw in reasoning_keywords):
        reasons.append("Reasoning/explanation required — preferring models with strong reasoning")

    return {
        "complexity": complexity,
        "recommendedModel": recommended_model,
        "alternatives": alternatives,
        "reasons": reasons,
        "costEstimate": cost_dict.get("cost_estimate_usd", 0),
        "latencyEstimate": cost_dict.get("latency_estimate_seconds", 2.0),
        "tokenEstimate": cost_dict.get("total_tokens_est", 0),
        "category": category,
    }


# ── Runtime Mode (Developer / Production) ────────────────────────────────────

@app.get("/api/mode")
async def get_runtime_mode():
    """Get current runtime mode."""
    await backend.ensure_initialized()
    if backend.mode_manager is None:
        return {"mode": "production", "description": "Mode manager not available"}

    try:
        from utils.runtime_mode import RuntimeMode
        current = backend.mode_manager.mode
        is_dev = current == RuntimeMode.DEVELOPER

        return {
            "mode": "developer" if is_dev else "production",
            "description": (
                "Developer mode: Shows full debug info, intermediate prompts, chain-of-thought reasoning, raw LLM responses, and detailed metrics."
                if is_dev else
                "Production mode: Shows only final answers, summary scores, and cost estimates. Optimized for end users."
            ),
            "features": {
                "showDebugLogs": is_dev,
                "showRawPrompts": is_dev,
                "showChainOfThought": is_dev,
                "showRawResponses": is_dev,
                "showDetailedMetrics": is_dev,
                "showCostBreakdown": True,
                "showFinalAnswer": True,
                "showSummaryScore": True,
            },
        }
    except Exception as e:
        return {"mode": "production", "error": str(e)}


@app.post("/api/mode")
async def set_runtime_mode(body: ModeToggleIn):
    """Toggle between developer and production mode."""
    await backend.ensure_initialized()
    if backend.mode_manager is None:
        raise HTTPException(503, "Mode manager not available")

    try:
        from utils.runtime_mode import RuntimeMode
        if body.mode.lower() == "developer":
            backend.mode_manager.set_mode(RuntimeMode.DEVELOPER)
        elif body.mode.lower() == "production":
            backend.mode_manager.set_mode(RuntimeMode.PRODUCTION)
        else:
            raise HTTPException(400, "Mode must be 'developer' or 'production'")

        # Return updated mode info
        return await get_runtime_mode()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Mode toggle failed: {str(e)}")


# ── Advanced Question Bank ────────────────────────────────────────────────────

@app.put("/api/questions/{question_id}")
async def update_question(question_id: str, body: QuestionIn):
    """Update an existing question."""
    await backend.ensure_initialized()
    q = next((q for q in backend.questions_db if q["id"] == question_id), None)
    if q is None:
        raise HTTPException(404, "Question not found")

    q["question"] = body.question
    q["category"] = body.category
    q["groundTruth"] = body.groundTruth or ""
    q["difficulty"] = body.difficulty
    return q


@app.post("/api/questions/import")
async def import_questions(questions: List[QuestionIn]):
    """Bulk import questions."""
    await backend.ensure_initialized()
    imported = []
    for qin in questions:
        q = {
            "id": str(backend._next_question_id),
            "question": qin.question,
            "groundTruth": qin.groundTruth or "",
            "category": qin.category,
            "difficulty": qin.difficulty,
        }
        backend._next_question_id += 1
        backend.questions_db.append(q)
        imported.append(q)
    return {"imported": len(imported), "questions": imported}


@app.get("/api/questions/stats")
async def question_stats():
    """Get question bank statistics."""
    await backend.ensure_initialized()
    from collections import Counter
    cats = Counter(q.get("category", "general") for q in backend.questions_db)
    diffs = Counter(q.get("difficulty", "medium") for q in backend.questions_db)
    with_gt = sum(1 for q in backend.questions_db if q.get("groundTruth"))
    return {
        "total": len(backend.questions_db),
        "withGroundTruth": with_gt,
        "withoutGroundTruth": len(backend.questions_db) - with_gt,
        "byCategory": dict(cats),
        "byDifficulty": dict(diffs),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
