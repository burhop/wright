"""Capture the actual device viewport at browser zoom; full-page clips native zoom."""
from pathlib import Path

base = Path('D:/repos/wright/.local-run/process-interfaces-083')
target = base / 't052-native-zoom-024.mjs'
assert not target.exists()
text = (base / 't052-native-zoom-023.mjs').read_text(encoding='utf-8').replace('-023', '-024')
text = text.replace('zoom023-after-zoom-geometry', 'zoom024-after-zoom-geometry')
assert text.count('fullPage:true') == 2
text = text.replace('fullPage:true', 'fullPage:false')
needle = "  await record({id:'S13',state:'pass'"
assert needle in text
text = text.replace(needle, "  await zoomCommon.locator('[data-result-id]').first().scrollIntoViewIfNeeded();\n" + needle)
target.write_text(text, encoding='utf-8')
print('Prepared024 genuine device-viewport screenshots;023 measured behavior retained, its zoom full-page images are cropped and not visual acceptance.')
