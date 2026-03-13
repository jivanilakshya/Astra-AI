"""
Astra-AI: Self-Improving LLM System
Main entry point for the application.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cli import main as cli_main


if __name__ == "__main__":
    cli_main()
