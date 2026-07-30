#!/usr/bin/env python3
"""Derive an immutable first-release predecessor fixture from a Wright wheel."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile


WHEEL_NAME = re.compile(
    r"^(?P<distribution>wright_engineering)-(?P<version>[^-]+)"
    r"(?P<suffix>-[^-]+-[^-]+-[^-]+\.whl)$"
)


def _digest(value: bytes) -> str:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(value).digest()).rstrip(b"=")
    return f"sha256={encoded.decode('ascii')}"


def _rewrite_json(value: bytes, *, version: str, path: str) -> bytes:
    payload = json.loads(value.decode("utf-8"))
    payload[
        "version" if path.endswith("runtime-extra-lock.json") else "runtime_version"
    ] = version
    if path.endswith("compatibility.json"):
        public = version.split("+", 1)[0]
        payload["runtime_specifier"] = f"=={public}.*"
    return (json.dumps(payload, indent=2) + "\n").encode("utf-8")


def build_fixture(source: Path, output_dir: Path, version: str) -> Path:
    source = source.resolve(strict=True)
    match = WHEEL_NAME.fullmatch(source.name)
    if match is None:
        raise ValueError(f"not a Wright wheel: {source.name}")
    if "+" not in version:
        raise ValueError("fixture version must be a PEP 440 local version")
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / (
        f"{match.group('distribution')}-{version}{match.group('suffix')}"
    )
    old_dist_info = f"wright_engineering-{match.group('version')}.dist-info/"
    new_dist_info = f"wright_engineering-{version}.dist-info/"
    entries: dict[str, bytes] = {}
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            if info.is_dir() or info.filename.endswith("/RECORD"):
                continue
            name = info.filename
            if name.startswith(old_dist_info):
                name = new_dist_info + name.removeprefix(old_dist_info)
            value = archive.read(info)
            if name == f"{new_dist_info}METADATA":
                text = value.decode("utf-8")
                text = re.sub(
                    r"^Version: .+$", f"Version: {version}", text, count=1, flags=re.M
                )
                value = text.encode("utf-8")
            elif name in {
                "wright_engineering/compatibility.json",
                "wright_engineering/runtime-extra-lock.json",
            }:
                value = _rewrite_json(value, version=version, path=name)
            entries[name] = value

    record_path = f"{new_dist_info}RECORD"
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    for name, value in sorted(entries.items()):
        writer.writerow((name, _digest(value), len(value)))
    writer.writerow((record_path, "", ""))
    entries[record_path] = stream.getvalue().encode("utf-8")

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, value)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", default="0.1.6+fixture.1")
    args = parser.parse_args(argv)
    target = build_fixture(args.wheel, args.output, args.version)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
