"""Use standard CSS scope for axe; Playwright :visible is not browser CSS."""
from pathlib import Path

base = Path('D:/repos/wright/.local-run/process-interfaces-083')
target = base / 't052-native-zoom-023.mjs'
assert not target.exists()
text = (base / 't052-native-zoom-022.mjs').read_text(encoding='utf-8').replace('-022', '-023')
text = text.replace('zoom022-after-zoom-geometry', 'zoom023-after-zoom-geometry')
needle = ".include('[data-testid=\"workspace-process-view\"]:visible')"
assert text.count(needle) == 1
text = text.replace(needle, ".include('[data-testid=\"retained-workspace-process-panel\"][aria-hidden=\"false\"] [data-testid=\"workspace-process-view\"]')")
target.write_text(text, encoding='utf-8')
print('Prepared023 standard axe CSS scope of the actual active process panel;022 retained.')
