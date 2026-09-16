"""Prepare a selected, bounded retention overlay without altering any run store."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

BASE_IMAGE = "sha256:e5dc37e5cde7722fa9547962b438548122def738019b85f380f9cb84d4b2bc47"
BASE_TAG = "wright-081-modelica-retention-base:e5dc37e5cde7"
BASE_SOURCE_SHA256 = "a65c8f7c1857991ea42bc77dd3ffa40c0d1488729d45ab2aa71fc42cb0151422"
CAPACITY_PATH = "src/storage/capacity-coordinator.ts"
RETAINED_RUN_LIMIT = 100


def prepare(source: Path, destination: Path) -> dict:
    """Change only the reviewed constant; reject source drift and reused output."""
    original = (source / CAPACITY_PATH).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(original).hexdigest() != BASE_SOURCE_SHA256:
        raise ValueError("Capacity source differs from the exact selected image")
    old = b"export const MAX_STORED_RUNS = 20;"
    if original.count(old) != 1:
        raise ValueError("Expected the qualified twenty-run capacity source")
    updated = original.replace(old, b"export const MAX_STORED_RUNS = 100;")
    destination.mkdir(parents=True, exist_ok=False)
    target = destination / CAPACITY_PATH
    target.parent.mkdir(parents=True)
    target.write_bytes(updated)
    (destination / "Dockerfile").write_text(
        f"FROM {BASE_TAG}\n"
        f"COPY {CAPACITY_PATH} /app/{CAPACITY_PATH}\n"
        "WORKDIR /app\n"
        "RUN deno check --cached-only server.ts\n",
        encoding="utf-8",
    )
    evidence = {
        "base_image": BASE_IMAGE,
        "base_tag_must_resolve_to": BASE_IMAGE,
        "changed_path": f"/app/{CAPACITY_PATH}",
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "updated_sha256": hashlib.sha256(updated).hexdigest(),
        "old_limit": 20,
        "selected_limit": RETAINED_RUN_LIMIT,
        "run_store_modified": False,
        "only_change": "MAX_STORED_RUNS=20 -> MAX_STORED_RUNS=100",
    }
    (destination / "retention-overlay.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.destination), indent=2))
