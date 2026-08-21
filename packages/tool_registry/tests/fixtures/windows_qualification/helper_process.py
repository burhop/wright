from __future__ import annotations

import subprocess
import sys
import time


def main() -> int:
    mode = sys.argv[1]
    if mode == "clean":
        print("ready")
        return 0
    if mode == "stdout-contamination":
        print("not-json-before-protocol")
        return 0
    if mode == "oversized-output":
        sys.stdout.write("x" * (256 * 1024))
        sys.stdout.flush()
        return 0
    if mode == "hang":
        time.sleep(60)
        return 0
    if mode == "child-process":
        subprocess.Popen([sys.executable, __file__, "hang"])
        print("child-started", flush=True)
        time.sleep(60)
        return 0
    if mode == "malformed-protocol":
        print('{"jsonrpc":"2.0","result":')
        return 0
    if mode == "clean-shutdown":
        for line in sys.stdin:
            if line.strip() == "stop":
                return 0
        return 0
    raise SystemExit(f"unknown helper mode: {mode}")


if __name__ == "__main__":
    raise SystemExit(main())
