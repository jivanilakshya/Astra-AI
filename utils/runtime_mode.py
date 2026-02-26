"""
Runtime Mode Manager - Developer Mode vs Production Mode

Production mode: Show only final output
Developer mode: Show intermediate prompts, model responses, chain-of-thought summaries,
                debug logs for analysis and optimization.

Usage:
    from utils.runtime_mode import get_mode_manager, RuntimeMode

    mode = get_mode_manager()
    mode.set_mode(RuntimeMode.DEVELOPER)

    mode.log_prompt("generator", prompt_text)
    mode.log_response("generator", response_text)
    mode.log_chain_of_thought("judge", summary)
    mode.log_debug("optimizer", "convergence check", data)

    # In production mode, these are no-ops (silent)
"""

import json
import logging
import sys
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


class RuntimeMode(Enum):
    """Runtime mode selection."""
    PRODUCTION = "production"
    DEVELOPER = "developer"


@dataclass
class DebugEntry:
    """A single debug log entry."""
    timestamp: str
    agent: str
    entry_type: str  # prompt, response, chain_of_thought, debug, metric
    label: str
    content: Any
    metadata: Optional[Dict[str, Any]] = None


class ModeManager:
    """
    Controls what output is shown based on runtime mode.
    
    Developer mode shows:
    - Intermediate prompts sent to each agent
    - Raw model responses before parsing
    - Chain-of-thought summaries (not raw hidden reasoning)
    - Debug logs: token counts, latencies, scores at each step
    - Tracing information (LangSmith or fallback)
    
    Production mode shows:
    - Final answer only
    - Summary score
    - Cost estimate
    """
    
    def __init__(self, mode: RuntimeMode = RuntimeMode.PRODUCTION):
        self.mode = mode
        self.debug_log: List[DebugEntry] = []
        self.session_start = datetime.now().isoformat()
        self._verbose_console = True  # print to console in dev mode
        
    def set_mode(self, mode: RuntimeMode):
        """Switch runtime mode."""
        self.mode = mode
        logger.info(f"Runtime mode set to: {mode.value}")
    
    @property
    def is_developer(self) -> bool:
        return self.mode == RuntimeMode.DEVELOPER
    
    @property
    def is_production(self) -> bool:
        return self.mode == RuntimeMode.PRODUCTION
    
    # ---- Logging helpers (no-ops in production) ----
    
    def log_prompt(self, agent: str, prompt: str, metadata: Optional[Dict] = None):
        """Log an intermediate prompt sent to a model."""
        entry = DebugEntry(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            entry_type="prompt",
            label=f"{agent} prompt",
            content=prompt,
            metadata=metadata
        )
        self.debug_log.append(entry)
        
        if self.is_developer and self._verbose_console:
            self._print_dev(f"[PROMPT] {agent}", prompt[:500] + ("..." if len(prompt) > 500 else ""))
    
    def log_response(self, agent: str, response: str, metadata: Optional[Dict] = None):
        """Log a raw model response."""
        entry = DebugEntry(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            entry_type="response",
            label=f"{agent} response",
            content=response,
            metadata=metadata
        )
        self.debug_log.append(entry)
        
        if self.is_developer and self._verbose_console:
            self._print_dev(f"[RESPONSE] {agent}", response[:500] + ("..." if len(response) > 500 else ""))
    
    def log_chain_of_thought(self, agent: str, summary: str, metadata: Optional[Dict] = None):
        """Log a chain-of-thought summary (human-readable, not raw hidden reasoning)."""
        entry = DebugEntry(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            entry_type="chain_of_thought",
            label=f"{agent} reasoning",
            content=summary,
            metadata=metadata
        )
        self.debug_log.append(entry)
        
        if self.is_developer and self._verbose_console:
            self._print_dev(f"[COT] {agent}", summary)
    
    def log_debug(self, agent: str, label: str, data: Any, metadata: Optional[Dict] = None):
        """Log arbitrary debug data."""
        entry = DebugEntry(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            entry_type="debug",
            label=label,
            content=data,
            metadata=metadata
        )
        self.debug_log.append(entry)
        
        if self.is_developer and self._verbose_console:
            if isinstance(data, dict):
                data_str = json.dumps(data, indent=2, default=str)
            else:
                data_str = str(data)
            self._print_dev(f"[DEBUG] {agent} - {label}", data_str[:300])
    
    def log_metric(self, agent: str, metric_name: str, value: Any, metadata: Optional[Dict] = None):
        """Log a metric value."""
        entry = DebugEntry(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            entry_type="metric",
            label=metric_name,
            content=value,
            metadata=metadata
        )
        self.debug_log.append(entry)
        
        if self.is_developer and self._verbose_console:
            self._print_dev(f"[METRIC] {agent}", f"{metric_name} = {value}")
    
    def _print_dev(self, header: str, body: str):
        """Print developer-mode info to console."""
        print(f"\n  {'~' * 60}")
        print(f"  {header}")
        print(f"  {'~' * 60}")
        for line in body.split('\n'):
            print(f"    {line}")
    
    # ---- Export / Reporting ----
    
    def get_debug_log(self) -> List[Dict]:
        """Return full debug log as list of dicts."""
        return [asdict(e) for e in self.debug_log]
    
    def export_debug_log(self, filepath: str):
        """Export debug log to JSON file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "session_start": self.session_start,
                "mode": self.mode.value,
                "entries": self.get_debug_log()
            }, f, indent=2, default=str)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the debug session."""
        entries_by_type = {}
        entries_by_agent = {}
        for entry in self.debug_log:
            entries_by_type[entry.entry_type] = entries_by_type.get(entry.entry_type, 0) + 1
            entries_by_agent[entry.agent] = entries_by_agent.get(entry.agent, 0) + 1
        
        return {
            "mode": self.mode.value,
            "total_entries": len(self.debug_log),
            "entries_by_type": entries_by_type,
            "entries_by_agent": entries_by_agent,
            "session_start": self.session_start
        }
    
    def clear(self):
        """Clear the debug log."""
        self.debug_log.clear()


# ---- Singleton ----

_mode_manager: Optional[ModeManager] = None


def get_mode_manager(mode: Optional[RuntimeMode] = None) -> ModeManager:
    """Get or create the global ModeManager singleton."""
    global _mode_manager
    if _mode_manager is None:
        _mode_manager = ModeManager(mode or RuntimeMode.PRODUCTION)
    elif mode is not None:
        _mode_manager.set_mode(mode)
    return _mode_manager
