"""Read only the selected installed Hermes profile's process identity.

Executed with that runtime's Python, not imported into Wright's interpreter.
"""

import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys


def observe(runtime_root: str, profile: str) -> dict:
    sys.path.insert(0, str(Path(runtime_root).resolve()))
    # Provider imports may log; stdout is exclusively the bounded receipt.
    with contextlib.redirect_stdout(sys.stderr):
        from hermes_cli.profiles import resolve_profile_env

        home = Path(resolve_profile_env(profile)).resolve()
        os.environ["HERMES_HOME"] = str(home)
        from gateway.status import get_running_pid

        config = home / "config.yaml"
        return {
            "home": str(home),
            "pid": get_running_pid(),
            "config_digest": hashlib.sha256(config.read_bytes()).hexdigest(),
        }


if __name__ == "__main__":
    try:
        print(json.dumps(observe(sys.argv[1], sys.argv[2])))
    except Exception:
        print(json.dumps({"error": "Hermes profile process identity unavailable"}))
        sys.exit(1)
