"""Trusted local compiler discovery; generated source cannot select these paths."""

import os
from pathlib import Path
import shutil

from .build import BuildToolchain
from .errors import ProcessInterfaceError


class UnavailableBuildToolchain:
    def describe(self):
        raise ProcessInterfaceError(
            "CAPABILITY_UNAVAILABLE",
            "The qualified interface compiler is unavailable.",
            "Configure the local qualified toolchain; existing saved interfaces and the common view still work.",
        )


def discover_build_toolchain():
    """Development checkout or an administrator's prequalified local root.

    Installed packed public resources are added separately by the distribution
    work. No registry install or source-checkout assumption is made silently in
    an installed product; missing directories produce unavailable capability.
    """
    configured = os.environ.get("WRIGHT_PROCESS_UI_TOOLCHAIN_ROOT")
    root = (
        Path(configured).absolute()
        if configured
        else Path(__file__).resolve().parents[5]
    )
    node = shutil.which("node")
    client, kit = root / "packages/process_client", root / "packages/ui_kit"
    if not node or not all(
        path.is_dir() for path in (root / "node_modules", client, kit)
    ):
        return UnavailableBuildToolchain()
    return BuildToolchain(Path(node), root, client, kit)
