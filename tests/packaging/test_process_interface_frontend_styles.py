"""Production tree shaking must retain the public process kit's shared styles."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]


def test_production_frontend_retains_process_interface_styles(tmp_path):
    node = shutil.which("node")
    if not node or not (ROOT / "node_modules/vite").is_dir():
        pytest.skip("Requires the existing qualified frontend build dependencies")
    out = tmp_path / "frontend"
    program = (
        "import {build} from 'vite';"
        "process.env.VITE_WRIGHT_WORKFLOW_RECOVERY='1';"
        "process.env.VITE_WRIGHT_WORKFLOW_COMPOSER='1';"
        "process.env.VITE_WRIGHT_PROCESS_DEFINITION_VIEW='1';"
        "await build({root:"
        + json.dumps(str(ROOT / "apps/web"))
        + ",cacheDir:"
        + json.dumps(str(tmp_path / "cache"))
        + ",build:{outDir:"
        + json.dumps(str(out))
        + ",emptyOutDir:false,sourcemap:false}});"
    )
    result = subprocess.run(
        [node, "--input-type=module", "-e", program],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]
    assert (out / "index.html").is_file()
    styles = "\n".join(
        file.read_text(encoding="utf-8") for file in (out / "assets").glob("*.css")
    )
    for selector in (
        ".wright-process-ui",
        ".wp-field",
        ".wp-row",
        ".wp-section",
        ".wp-link",
    ):
        assert selector in styles, (
            f"Production build dropped public UI kit styles: {selector}"
        )
    assert "--space-lg" in styles
