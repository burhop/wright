from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release.evidence import ReleaseEvidence  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Wright release evidence.")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    ReleaseEvidence.read(args.manifest)
    print(f"release evidence valid: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
