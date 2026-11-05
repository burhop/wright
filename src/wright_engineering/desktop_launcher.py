"""Launch the desktop bridge from the existing managed runtime, without installing."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .runtime.installer import RuntimeInstaller
from .runtime.layout import NativeLayout
from .runtime.models import RuntimeStatus
from .runtime.state import ManifestStore


def serve_desktop(api_url: str) -> int:
    layout = NativeLayout.discover()
    if layout.manifest.exists():
        # The manager installation is intentionally dependency-light. Execute the
        # bridge in the same installed environment selected by native lifecycle.
        manifest = ManifestStore(layout).load(create=False)
        runtime = manifest.runtimes.get(manifest.active_runtime_id or "")
        if runtime is None or runtime.status not in {
            RuntimeStatus.ACTIVE,
            RuntimeStatus.VERIFIED,
        }:
            print(
                "No verified Wright runtime is selected. Run wright native status.",
                file=sys.stderr,
            )
            return 1
        environment = layout.require_contained(
            Path(runtime.environment_path), layout.runtimes
        )
        python = RuntimeInstaller.environment_python(environment)
        if not python.is_file():
            print(
                "The selected Wright runtime is unavailable. Run wright native status.",
                file=sys.stderr,
            )
            return 1
        return subprocess.call(
            [
                str(python),
                "-I",
                "-m",
                "api.desktop.entrypoint",
                "--api-url",
                api_url,
                "--token-file",
                str(layout.control_plane_token),
            ]
        )
    try:
        from api.desktop.entrypoint import main
    except ImportError:
        print(
            "Desktop support needs the Wright runtime dependencies. Install the managed runtime first.",
            file=sys.stderr,
        )
        return 1
    return main(["--api-url", api_url, "--token-file", str(layout.control_plane_token)])
