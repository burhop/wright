"""Trusted local compiler discovery; generated source cannot select these paths."""

import os
from importlib.resources import files
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
    """Packaged public resources and a prequalified local compiler, or checkout.

    Installed authoring needs an administrator-configured dependency root; it
    never borrows a checkout, downloads dependencies or executes package scripts.
    Saved interface opening has no compiler/model dependency.
    """
    configured = os.environ.get("WRIGHT_PROCESS_UI_TOOLCHAIN_ROOT")
    module = Path(__file__).resolve()
    checkout = module.parts[-6:] == (
        "packages",
        "workspace_service",
        "src",
        "workspace_service",
        "process_interfaces",
        "toolchain.py",
    )
    root = (
        Path(configured).absolute()
        if configured
        else module.parents[5]
        if checkout
        else None
    )
    if root is None:
        return UnavailableBuildToolchain()
    node = shutil.which("node")
    public = files("workspace_service.process_interfaces.resources").joinpath("public")
    if isinstance(public, Path) and public.is_dir():
        client, kit = public / "process_client", public / "ui_kit"
    elif checkout:
        client, kit = root / "packages/process_client", root / "packages/ui_kit"
    else:
        return UnavailableBuildToolchain()
    if not node or not all(
        path.is_dir() for path in (root / "node_modules", client, kit)
    ):
        return UnavailableBuildToolchain()
    return BuildToolchain(Path(node), root, client, kit)
