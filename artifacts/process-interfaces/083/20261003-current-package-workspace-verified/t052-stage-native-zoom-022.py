"""Correct transient connection-banner assumption; retain actual read-only checks."""
from pathlib import Path

base = Path('D:/repos/wright/.local-run/process-interfaces-083')
target = base / 't052-native-zoom-022.mjs'
assert not target.exists()
text = (base / 't052-native-zoom-021.mjs').read_text(encoding='utf-8').replace('-021', '-022')
text = text.replace('zoom021-after-zoom-geometry', 'zoom022-after-zoom-geometry')
assert text.count("getByText('Preview - process controls are read-only.'") == 2
text = text.replace("getByText('Preview - process controls are read-only.'", "getByText('Preview: process controls are read-only.'")
text = text.replace("action:'Set browser Zoom to 200%.'", "action:'Set browser Zoom to 200% and scroll to the embedded preview.'")
target.write_text(text, encoding='utf-8')
print('Prepared022 stable shared read-only notice checks; transport connection banner may legitimately update.020/021 retained.')
