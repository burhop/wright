"""Fresh explicit presentation after authoritative failed startup; no process retry."""
from pathlib import Path

base = Path('D:/repos/wright/.local-run/process-interfaces-083')
target = base/'t052-native-zoom-025.mjs'
assert not target.exists()
text = (base/'t052-native-zoom-024.mjs').read_text(encoding='utf-8').replace('-024','-025')
text = text.replace('zoom024-after-zoom-geometry','zoom025-after-zoom-geometry')
text = text.replace('compact-installed-019','native-zoom-installed-025')
target.write_text(text,encoding='utf-8')
print('Prepared fresh025 after recorded SURFACE_READINESS_TIMEOUT and failed runtime; distinct trace/DOM/cleanup paths; no engineering restart.')
