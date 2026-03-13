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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("astra-api")

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
    if body.prompt:
        # User supplied raw prompt — use as-is
        full_prompt = body.prompt.replace("{question}", body.question)
        template_used = None
    else:
        # Auto-select or use specified template
        category = body.category or "general"
        complexity = "moderate"
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

    # ── Model routing ──
    routing_info = None
    if body.showRouting and backend.smart_router:
        try:
            routing_info = _explain_routing(body.question, body.category or "general")
        except Exception:
            pass

    model = body.model or "Qwen/Qwen2.5-72B-Instruct"

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
        "metadata": {
            "model": model,
            "tokens_used": tokens_est + output_tokens_est,
            "input_tokens": tokens_est,
            "output_tokens": output_tokens_est,
            "latency_ms": latency * 1000,
            "timestamp": datetime.now().isoformat(),
        },
    }
    if routing_info:
        resp["routing"] = routing_info
    if debug_info:
        resp["debug"] = debug_info
    return resp


# ── Models ───────────────────────────────────────────────────────────────────

@app.get("/api/models")
async def list_models():
    """List available models with their profiles."""
    await backend.ensure_initialized()
    from agents.huggingface_provider import AVAILABLE_MODELS

    # Build rich profiles using SmartRouter model registry
    profiles = []
    for m in AVAILABLE_MODELS:
        model_id = m["id"]
        profile = {
            "id": model_id,
            "name": m["name"],
            "provider": "huggingface",
            "description": f'{m["name"]} ({m["tier"]} tier)',
            "parameters": _extract_params(model_id),
            "contextWindow": 32768 if "72B" in model_id or "32B" in model_id or "Mistral" in model_id else 8192,
            "costPer1MTokens": 0.0,
            "avgLatency": None,
            "avgScore": None,
            "status": "available",
            "strengths": _model_strengths(model_id),
            "context_window": 32768 if "72B" in model_id or "32B" in model_id or "Mistral" in model_id else 8192,
            "cost_input_per_1k": 0.0,
            "cost_output_per_1k": 0.0,
            "avg_latency_seconds": 0,
            "quality_tier": 1 if "72B" in model_id or "32B" in model_id else (2 if "8B" in model_id or "7B" in model_id else 3),
            "is_available": True,
        }

        # Enrich from SmartRouter profiles if available
        if backend.smart_router:
            try:
                sr_profiles = getattr(backend.smart_router, "model_profiles", {})
                if model_id in sr_profiles:
                    sp = sr_profiles[model_id]
                    profile["context_window"] = sp.context_window
                    profile["contextWindow"] = sp.context_window
                    profile["cost_input_per_1k"] = sp.cost_input_per_1k
                    profile["cost_output_per_1k"] = sp.cost_output_per_1k
                    profile["avg_latency_seconds"] = sp.avg_latency_seconds
                    profile["quality_tier"] = sp.quality_tier
                    profile["is_available"] = sp.is_available
            except Exception:
                pass

        profiles.append(profile)

    return profiles


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

    return {
        "qualityScore": quality_score,
        "overallScore": quality_score,
        "qualityGrade": quality_grade,
        "wordCount": word_count,
        "components": result.get("auto_constraints", []),
        "issues": result.get("suggested_improvements", []),
        "suggestions": result.get("suggested_improvements", []),
        "scores": {
            "clarity": round(result.get("specificity_score", 0.5) * 10, 1),
            "specificity": round(result.get("specificity_score", 0.5) * 10, 1),
            "structure": round((1 - result.get("vagueness_score", 0.5)) * 10, 1),
            "completeness": round((1 - result.get("ambiguity_score", 0.5)) * 10, 1),
        },
        "flags": [],
        "detectedIntent": result.get("detected_intent", "general"),
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
        "recommended_model": pred_dict.get("recommended_model", "Qwen/Qwen2.5-72B-Instruct"),
        "alternative_models": pred_dict.get("alternative_models", []),
    }


# ── Cost History ─────────────────────────────────────────────────────────────

@app.get("/api/cost/history")
async def get_cost_history():
    """Return cost tracking history."""
    await backend.ensure_initialized()

    # Try to load from cost_tracking directory
    cost_dir = project_root / "output" / "cost_tracking"
    records = []
    if cost_dir.exists():
        for f in sorted(cost_dir.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    records.extend(data)
                elif isinstance(data, dict):
                    records.append(data)
            except Exception:
                pass

    if not records:
        # Return empty list — frontend handles empty state
        return []

    return records


# ── Model Comparison ─────────────────────────────────────────────────────────

@app.post("/api/compare")
async def compare_models(body: CompareIn):
    """Compare multiple models on the same prompt."""
    await backend.ensure_initialized()

    if backend.multi_model_engine is not None:
        try:
            report = await asyncio.get_running_loop().run_in_executor(
                None, lambda: backend.multi_model_engine.compare(body.prompt, body.models)
            )
            report_dict = report.to_dict() if hasattr(report, "to_dict") else report
            return _format_comparison_report(report_dict, body.prompt, body.models)
        except Exception as e:
            logger.warning(f"MultiModelEngine compare failed: {e}, falling back to manual")

    # Fallback: manually call each model
    if backend.provider is None:
        raise HTTPException(503, "No LLM provider available")

    results = []
    for model_name in body.models:
        try:
            result = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda mn=model_name: backend.provider.generate(
                    model_name=mn, prompt=body.prompt, temperature=0.7, max_tokens=500,
                )
            )
            text = result.get("text", "") if isinstance(result, dict) else str(result)
            latency = result.get("latency_seconds", 0) if isinstance(result, dict) else 0
            tokens_in = max(1, len(body.prompt) // 4)
            tokens_out = max(1, len(text) // 4)
            results.append({
                "model": model_name,
                "answer": text,
                "explanation": text,
                "scores": {"correctness": 7.0, "clarity": 7.0, "reasoning": 7.0, "relevance": 7.0, "conciseness": 7.0},
                "compositeScore": 7.0,
                "metadata": {"tokensUsed": tokens_in + tokens_out, "latencyMs": latency * 1000, "costUsd": 0.0},
            })
        except Exception as e:
            results.append({
                "model": model_name,
                "answer": f"Error: {str(e)}",
                "explanation": "",
                "scores": {"correctness": 0, "clarity": 0, "reasoning": 0, "relevance": 0, "conciseness": 0},
                "compositeScore": 0,
                "metadata": {"tokensUsed": 0, "latencyMs": 0, "costUsd": 0},
            })

    results.sort(key=lambda r: r["compositeScore"], reverse=True)
    return {
        "results": results,
        "ranking": [{"model": r["model"], "rank": i + 1, "score": r["compositeScore"]} for i, r in enumerate(results)],
        "consistency_score": 0.75,
        "summary": f"{results[0]['model'] if results else 'N/A'} performed best." if results else "No results.",
    }


def _format_comparison_report(report_dict: dict, prompt: str, models: List[str]) -> dict:
    """Format MultiModelEngine report for the frontend."""
    raw_results = report_dict.get("results", report_dict.get("model_results", []))
    results = []
    for r in raw_results:
        if isinstance(r, dict):
            results.append({
                "model": r.get("model_name", r.get("model", "")),
                "answer": r.get("response_text", r.get("answer", "")),
                "explanation": r.get("response_text", r.get("explanation", "")),
                "scores": r.get("scores", {"correctness": 7, "clarity": 7, "reasoning": 7, "relevance": 7, "conciseness": 7}),
                "compositeScore": r.get("composite_score", r.get("compositeScore", 7.0)),
                "metadata": {
                    "tokensUsed": r.get("input_tokens_est", 0) + r.get("output_tokens_est", 0),
                    "latencyMs": r.get("latency_seconds", 0) * 1000,
                    "costUsd": r.get("cost_estimate", 0),
                },
            })

    results.sort(key=lambda x: x["compositeScore"], reverse=True)
    return {
        "results": results,
        "ranking": [{"model": r["model"], "rank": i + 1, "score": r["compositeScore"]} for i, r in enumerate(results)],
        "consistency_score": report_dict.get("consistency_score", 0.75),
        "summary": report_dict.get("summary", f"Comparison of {len(results)} models complete."),
    }


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
        "model": body.generatorModel or body.model or "Qwen/Qwen2.5-72B-Instruct",
        "totalCost": 0,
        "questionsCount": 0,
        "durationSeconds": 0,
    }
    backend.sessions_db.append(session)

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

    session["questionsCount"] = len(questions)

    # Run optimization in background
    asyncio.create_task(_run_optimization_task(session_id, questions, body))

    return {"sessionId": session_id}


async def _run_optimization_task(session_id: str, questions: List[str], config: OptimizationConfigIn):
    """Background task to run the optimization loop."""
    session = next((s for s in backend.sessions_db if s["sessionId"] == session_id), None)
    if session is None:
        return

    # Cap questions to avoid extremely long runs (each question = 2 API calls per iteration)
    max_q = min(len(questions), config.batchSize or 5)
    questions = questions[:max_q]
    session["questionsCount"] = len(questions)

    start_time = datetime.now()
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

            orchestrator = create_langchain_orchestrator(
                generator_model=gen_model,
                judge_model=judge_model,
                optimizer_model=opt_model,
                max_iterations=config.maxIterations or 10,
                convergence_threshold=config.convergenceThreshold or 8.5,
                enable_langsmith=False,
                temperature=temperature,
                max_tokens=max_tokens,
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
            }

            results = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: orchestrator.run_optimization(questions, initial_prompt)
            )

            # Attach config to results
            results["config"] = config_info
            results["initial_prompt_used"] = initial_prompt

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

            # Notify connected WebSocket clients
            await _broadcast_ws(session_id, {
                "type": "complete",
                "data": _build_optimization_results(session_id, results, duration)
            })
        else:
            session["status"] = "error"
            await _broadcast_ws(session_id, {"type": "error", "data": {"agent": "orchestrator", "message": "LangChain not available", "recoverable": False}})

    except Exception as e:
        logger.error(f"Optimization error for {session_id}: {e}")
        logger.error(traceback.format_exc())
        session["status"] = "error"
        await _broadcast_ws(session_id, {"type": "error", "data": {"agent": "orchestrator", "message": str(e), "recoverable": False}})


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
            return {
                "total_routings": stats.get("total_routings", 0),
                "totalRoutings": stats.get("total_routings", 0),
                "total_cost": stats.get("total_cost", 0),
                "avgScore": stats.get("avg_score", 0),
                "avgLatency": stats.get("avg_latency", 0),
                "modelUsage": stats.get("model_usage", []),
                "per_model": stats.get("per_model", {}),
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

    model = body.model or "Qwen/Qwen2.5-72B-Instruct"

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
        evaluation = {
            "hasGroundTruth": True,
            "groundTruth": ground_truth,
            "matchScore": _simple_match_score(response_text, ground_truth),
        }
    else:
        evaluation = {"hasGroundTruth": False, "groundTruth": "", "matchScore": None}

    tokens_est = max(1, len(full_prompt) // 4)
    output_tokens_est = max(1, len(response_text) // 4)

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
        "evaluation": evaluation,
        "metadata": {
            "model": model,
            "tokens_used": tokens_est + output_tokens_est,
            "input_tokens": tokens_est,
            "output_tokens": output_tokens_est,
            "latency_ms": latency * 1000,
            "temperature": body.temperature or 0.7,
            "maxTokens": body.maxTokens or 500,
            "timestamp": datetime.now().isoformat(),
        },
    }


def _simple_match_score(response: str, ground_truth: str) -> float:
    """Simple overlap scoring between response and ground truth."""
    response_words = set(response.lower().split())
    truth_words = set(ground_truth.lower().split())
    if not truth_words:
        return 0.0
    overlap = response_words & truth_words
    precision = len(overlap) / len(response_words) if response_words else 0
    recall = len(overlap) / len(truth_words)
    if precision + recall == 0:
        return 0.0
    f1 = 2 * (precision * recall) / (precision + recall)
    return round(min(f1 * 12, 10.0), 1)  # Scale to 0-10


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
