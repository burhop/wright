"""Selected KiCad0.13.0 provider repair: send history diagnostics to stderr."""
import hashlib
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "src/kicad_mcp/utils/drc_history.py"
data = path.read_bytes()
if hashlib.sha256(data).hexdigest() not in {
    # Same pinned git blob, with Git's normal LF or Windows CRLF checkout.
    "1eba6f74820b1409a9c0a7714491a4f460e0b043ca30144c2fbc98c696227875",
    "0d21b4c563bdd869c6733e685f801ed67bc4a418bac07cc4bf28e1dfbcb1e5ea",
}:
    raise SystemExit("Unreviewed upstream DRC history bytes; refusing patch")
text = data.decode().replace("\r\n", "\n").replace("import platform\n", "import platform\nimport sys\n")
lines = text.splitlines()
count = 0
for index, line in enumerate(lines):
    if line.lstrip().startswith('print(f"'):
        if not line.endswith('")'):
            raise SystemExit("Unreviewed diagnostic shape")
        lines[index] = line[:-1] + ", file=sys.stderr)"
        count += 1
if count != 5:
    raise SystemExit("Unreviewed diagnostic count")
path.write_text("\n".join(lines) + "\n")
print("Applied five stderr-only DRC history diagnostic repairs")
