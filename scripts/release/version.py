from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib


SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>alpha|beta|rc)\.(?P<pre_n>0|[1-9]\d*))?$"
)


class ReleaseIdentityError(ValueError):
    """Raised when release version consumers disagree."""


@dataclass(frozen=True, slots=True)
class ProductVersion:
    semver: str
    python: str
    tag: str
    prerelease: bool


def parse_product_version(value: str) -> ProductVersion:
    raw = value.removeprefix("v")
    match = SEMVER_RE.fullmatch(raw)
    if match is None:
        raise ReleaseIdentityError(f"unsupported product version: {value!r}")
    pre = match.group("pre")
    python_version = raw
    if pre:
        marker = {"alpha": "a", "beta": "b", "rc": "rc"}[pre]
        python_version = raw.replace(f"-{pre}.", marker)
    return ProductVersion(raw, python_version, f"v{raw}", pre is not None)


def read_root_version(root: Path) -> ProductVersion:
    with (root / "pyproject.toml").open("rb") as handle:
        value = tomllib.load(handle)["project"]["version"]
    return parse_product_version(str(value))


def validate_release_version(root: Path, *, tag: str) -> ProductVersion:
    declared = read_root_version(root)
    supplied = parse_product_version(tag)
    if declared != supplied:
        raise ReleaseIdentityError(
            f"release tag {tag!r} does not match root product version {declared.semver!r}"
        )
    return declared
