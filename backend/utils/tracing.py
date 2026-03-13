"""
Tracing Manager - Fix LangSmith tracing + provide fallback tracing

LangSmith tracing often fails due to:
1. Missing LANGCHAIN_API_KEY environment variable
2. LANGCHAIN_TRACING_V2 not set to "true"
3. LANGCHAIN_ENDPOINT misconfigured
4. Network connectivity issues
5. langsmith package not installed

This module:
- Diagnoses LangSmith configuration issues
- Provides clear error messages and fixes
- Offers a built-in file-based tracing fallback
- Exports traces to JSON for offline analysis

Usage:
    from utils.tracing import TracingManager
    tracer = TracingManager()
    diag = tracer.diagnose_langsmith()      # check what's wrong
    tracer.fix_langsmith()                   # auto-fix what we can
    tracer.trace("agent", "action", data)    # fallback tracing
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

import logging
logger = logging.getLogger(__name__)


@dataclass
class TraceEntry:
    """A single trace entry."""
    timestamp: str
    agent: str
    action: str
    input_data: Any
    output_data: Any
    latency_ms: float
    metadata: Optional[Dict[str, Any]] = None


class TracingManager:
    """
    Manages tracing for the Astra AI system.
    
    Primary: LangSmith (if configured)
    Fallback: Built-in file-based JSON tracing
    """
    
    def __init__(self, trace_dir: str = "./output/traces"):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.traces: List[TraceEntry] = []
        self.langsmith_available = False
        self.langsmith_configured = False
        self._check_langsmith()
    
    # ── LangSmith Diagnostics ────────────────────────────────────────────
    
    def _check_langsmith(self):
        """Check if LangSmith is importable."""
        try:
            import langsmith
            self.langsmith_available = True
        except ImportError:
            self.langsmith_available = False
    
    def diagnose_langsmith(self) -> Dict[str, Any]:
        """
        Diagnose LangSmith tracing configuration.
        Returns a detailed diagnostic report with issues and fixes.
        """
        diagnosis = {
            "status": "unknown",
            "issues": [],
            "fixes": [],
            "env_vars": {},
            "connectivity": False,
        }
        
        # 1. Check package installation
        if not self.langsmith_available:
            diagnosis["issues"].append("langsmith package not installed")
            diagnosis["fixes"].append("Run: pip install langsmith")
        
        # 2. Check environment variables
        required_vars = {
            "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", ""),
            "LANGCHAIN_API_KEY": os.getenv("LANGCHAIN_API_KEY", ""),
            "LANGCHAIN_ENDPOINT": os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"),
            "LANGCHAIN_PROJECT": os.getenv("LANGCHAIN_PROJECT", ""),
        }
        diagnosis["env_vars"] = {k: ("SET" if v else "NOT SET") for k, v in required_vars.items()}
        
        if required_vars["LANGCHAIN_TRACING_V2"].lower() != "true":
            diagnosis["issues"].append("LANGCHAIN_TRACING_V2 is not set to 'true'")
            diagnosis["fixes"].append("Add to .env: LANGCHAIN_TRACING_V2=true")
        
        if not required_vars["LANGCHAIN_API_KEY"]:
            diagnosis["issues"].append("LANGCHAIN_API_KEY is not set")
            diagnosis["fixes"].append(
                "Get API key from https://smith.langchain.com/settings and add to .env: "
                "LANGCHAIN_API_KEY=ls-your-key-here"
            )
        
        if not required_vars["LANGCHAIN_PROJECT"]:
            diagnosis["issues"].append("LANGCHAIN_PROJECT not set (will use 'default')")
            diagnosis["fixes"].append("Add to .env: LANGCHAIN_PROJECT=astra-ai")
        
        # 3. Check connectivity (only if other checks pass)
        if self.langsmith_available and required_vars["LANGCHAIN_API_KEY"]:
            try:
                from langsmith import Client
                client = Client()
                # Test by listing projects (lightweight) - this validates the API key
                projects = list(client.list_projects(limit=1))
                diagnosis["connectivity"] = True
            except Exception as e:
                err_str = str(e).lower()
                if "401" in err_str or "unauthorized" in err_str or "invalid token" in err_str:
                    diagnosis["issues"].append("LANGCHAIN_API_KEY is invalid or expired (401 Unauthorized)")
                    diagnosis["fixes"].append(
                        "Your API key is rejected by LangSmith. Generate a new key at "
                        "https://smith.langchain.com/settings and update .env: "
                        "LANGCHAIN_API_KEY=lsv2_pt_your-new-key-here"
                    )
                elif "403" in err_str or "forbidden" in err_str:
                    diagnosis["issues"].append("LangSmith API access forbidden (403). Check your plan/permissions.")
                    diagnosis["fixes"].append("Verify your LangSmith account has API access enabled.")
                else:
                    diagnosis["issues"].append(f"LangSmith API connection failed: {str(e)[:100]}")
                    diagnosis["fixes"].append(
                        "Check your API key is valid and you have network access to api.smith.langchain.com"
                    )
        
        # 4. Set overall status
        if not diagnosis["issues"]:
            diagnosis["status"] = "healthy"
            self.langsmith_configured = True
        elif len(diagnosis["issues"]) <= 1 and diagnosis["connectivity"]:
            diagnosis["status"] = "partial"
        else:
            diagnosis["status"] = "broken"
        
        return diagnosis
    
    def fix_langsmith(self) -> Dict[str, Any]:
        """
        Attempt to auto-fix LangSmith configuration.
        Returns what was fixed and what still needs manual attention.
        """
        fixed = []
        remaining = []
        
        # 1. Install langsmith if missing
        if not self.langsmith_available:
            remaining.append("Install langsmith: pip install langsmith")
        
        # 2. Set environment variables
        if os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            fixed.append("Set LANGCHAIN_TRACING_V2=true in current session")
        
        if not os.getenv("LANGCHAIN_PROJECT"):
            os.environ["LANGCHAIN_PROJECT"] = "astra-ai"
            fixed.append("Set LANGCHAIN_PROJECT=astra-ai in current session")
        
        if not os.getenv("LANGCHAIN_ENDPOINT"):
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
            fixed.append("Set LANGCHAIN_ENDPOINT to default")
        
        if not os.getenv("LANGCHAIN_API_KEY"):
            remaining.append(
                "LANGCHAIN_API_KEY is required. Get it from https://smith.langchain.com/settings "
                "and add to your .env file: LANGCHAIN_API_KEY=ls-your-key-here"
            )
        
        # 3. Check .env file
        env_path = Path(".env")
        if env_path.exists():
            env_content = env_path.read_text()
            needed_lines = []
            if "LANGCHAIN_TRACING_V2" not in env_content:
                needed_lines.append("LANGCHAIN_TRACING_V2=true")
            if "LANGCHAIN_PROJECT" not in env_content:
                needed_lines.append("LANGCHAIN_PROJECT=astra-ai")
            
            if needed_lines:
                with open(env_path, 'a') as f:
                    f.write("\n# LangSmith Tracing (auto-added by Astra AI)\n")
                    for line in needed_lines:
                        f.write(f"{line}\n")
                fixed.append(f"Added {len(needed_lines)} lines to .env file")
        else:
            remaining.append("Create a .env file with your LANGCHAIN_API_KEY")
        
        return {
            "fixed": fixed,
            "remaining": remaining,
            "langsmith_ready": not bool(remaining) and self.langsmith_available,
        }
    
    # ── Fallback File-Based Tracing ──────────────────────────────────────
    
    def trace(
        self,
        agent: str,
        action: str,
        input_data: Any = None,
        output_data: Any = None,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record a trace entry (always works, regardless of LangSmith)."""
        entry = TraceEntry(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            action=action,
            input_data=input_data,
            output_data=output_data,
            latency_ms=latency_ms,
            metadata=metadata,
        )
        self.traces.append(entry)
    
    def export_traces(self, filepath: Optional[str] = None) -> str:
        """Export traces to JSON."""
        if filepath is None:
            filepath = str(self.trace_dir / f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([asdict(t) for t in self.traces], f, indent=2, default=str)
        
        return filepath
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get summary of recorded traces."""
        if not self.traces:
            return {"total": 0}
        
        by_agent = {}
        by_action = {}
        total_latency = 0.0
        
        for t in self.traces:
            by_agent[t.agent] = by_agent.get(t.agent, 0) + 1
            by_action[t.action] = by_action.get(t.action, 0) + 1
            total_latency += t.latency_ms
        
        return {
            "total": len(self.traces),
            "by_agent": by_agent,
            "by_action": by_action,
            "total_latency_ms": round(total_latency, 2),
            "avg_latency_ms": round(total_latency / len(self.traces), 2),
        }


# ── Singleton ─────────────────────────────────────────────────────────
_tracing_manager: Optional[TracingManager] = None


def get_tracing_manager() -> TracingManager:
    """Get or create the global TracingManager."""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
    return _tracing_manager
