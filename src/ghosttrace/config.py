"""Centralized environment and configuration loader for GhostTrace.

Loads configuration options securely from local environment variables and .env files
without external dependencies. Ensures private paths, host/port settings, payload
limits, and CLI binaries are configurable while defaulting to safe offline values.
"""

import os
from pathlib import Path

def load_dotenv(env_path=None):
    """Parses a .env file and loads key-value pairs into os.environ if not already set."""
    if env_path is None:
        # Search from current working directory up to git/project root
        candidate_dirs = [Path.cwd(), Path(__file__).resolve().parent.parent.parent]
        for d in candidate_dirs:
            p = d / ".env"
            if p.is_file():
                env_path = p
                break

    if not env_path or not os.path.isfile(env_path):
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("\"'").strip()
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass

# Automatically load .env on module import
load_dotenv()

# Server Settings
HOST = os.environ.get("GHOSTTRACE_HOST", "127.0.0.1")
try:
    PORT = int(os.environ.get("GHOSTTRACE_PORT", "7860"))
except ValueError:
    PORT = 7860

try:
    MAX_PAYLOAD_SIZE = int(os.environ.get("GHOSTTRACE_MAX_PAYLOAD_BYTES", str(25 * 1024 * 1024)))
except ValueError:
    MAX_PAYLOAD_SIZE = 25 * 1024 * 1024

# Cleanser Configuration
DEFAULT_CLEANSE_CMD = os.environ.get("GHOSTTRACE_CLEANSE_CMD", "ollama run llama3")
