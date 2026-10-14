#!/usr/bin/env python3
"""CLI launcher entrypoint for GhostTrace."""
import os
import sys

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from ghosttrace.engine import main

if __name__ == "__main__":
    main()
