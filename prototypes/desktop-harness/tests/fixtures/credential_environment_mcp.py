"""Synthetic qualification only: verify env delivery, then reuse the stdio fixture.

Licensed under this repository's MIT license. No external service or effects.
"""
import hashlib
import os
from pathlib import Path
import runpy

# These are intentionally synthetic test values, never personal credentials.
expected = hashlib.sha256(b"wright-credential-form-test-only").hexdigest()
if os.environ.get("RUN_MODE") != "read-only" or hashlib.sha256(
    os.environ.get("TEST_API_KEY", "").encode()
).hexdigest() != expected:
    raise RuntimeError("Synthetic launch configuration was not delivered")
fixture = Path(__file__).resolve().parents[4] / "packages/tool_registry/tests/mock_server.py"
runpy.run_path(str(fixture), run_name="__main__")
