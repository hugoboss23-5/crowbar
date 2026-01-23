"""
Configuration for Marcos system.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MEMORY_DB_PATH = DATA_DIR / "marcos_memory.db"
SOUL_PATH = BASE_DIR / "MARCOS_SOUL.md"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Claude API configuration
# Option 1: Paste your key directly here
CLAUDE_API_KEY = ""  # <-- PUT YOUR API KEY HERE (e.g., "sk-ant-api03-...")

# Option 2: Or set ANTHROPIC_API_KEY environment variable (overrides above)
if os.environ.get("ANTHROPIC_API_KEY"):
    CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Memory settings
MAX_CONNECTIONS_PER_SYSTEM = 10
SYNTHESIS_THRESHOLD = 5  # Minimum systems before synthesis runs
