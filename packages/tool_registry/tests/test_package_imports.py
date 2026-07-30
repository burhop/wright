import json
import subprocess
import sys


def test_catalog_loader_import_does_not_initialize_runtime_engine():
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json, sys; "
                "import tool_registry.catalog_loader; "
                "print(json.dumps({"
                "'manager': 'tool_registry.manager' in sys.modules, "
                "'core_logging': 'core.logging' in sys.modules"
                "}))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    loaded = json.loads(proc.stdout)
    assert loaded == {"manager": False, "core_logging": False}
