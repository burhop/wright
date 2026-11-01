"""Expose standalone example helpers to their ordinary regression tests."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "examples/reverse-engineering-research"))
sys.path.insert(0, str(_ROOT / "examples/reverse-engineering-workflow/research-first"))
