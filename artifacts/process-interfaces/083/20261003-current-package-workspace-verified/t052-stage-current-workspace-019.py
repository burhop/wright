"""Reuse exact saved-run receipts and walkthroughs on fresh installed006 copies."""
from pathlib import Path
import json
import shutil

repo = Path('D:/repos/wright')
base = repo / '.local-run/process-interfaces-083'
for old, new, names in [
    ('012', '014', ('third-start-receipt.json', 'third-current-interaction.json', 'heat-ui-focused-update-013-saved-revision.json', 'preview-locator.json')),
    ('013', '015', ('second-start-receipt.json', 'second-current-interaction.json', 'printed-ui-configured-update-001-saved-revision.json', 'second-source-gate-event.json', 'second-run-frozen.json', 'preview-locator.json')),
]:
    for name in names:
        target = base / f't052-mounted-native-{new}' / name
        assert not target.exists()
        shutil.copyfile(base / f't052-mounted-native-{old}' / name, target)

heat_dom = json.loads((base / 't052-mounted-native-008/current-heat-installed-010-dom.json').read_bytes())
(base / 't052-mounted-native-014/current-heat-installed-010-dom.json').write_text(json.dumps(heat_dom), encoding='utf-8')

for source_name, target_name, replacements in [
    ('t052-compact-browser-007.mjs', 't052-current-workspace-019.mjs', {
        't052-mounted-native-012': 't052-mounted-native-014',
        't052-mounted-native-013': 't052-mounted-native-015',
        '20261003-compact-': '20261003-current-',
        '-installed-007': '-installed-019',
    }),
    ('t052-current-editor-browser-009.mjs', 't052-current-editor-browser-010.mjs', {
        't052-mounted-native-007': 't052-mounted-native-014',
        '20261003-current-editor-009': '20261003-current-editor-010',
        'Editor verification 083 009': 'Editor verification 083 010',
        'editor_verification_083_009': 'editor_verification_083_010',
        'editor-trace-009': 'editor-trace-010',
    }),
    ('t052-current-heat-browser-017.mjs', 't052-current-heat-browser-018.mjs', {
        't052-mounted-native-008': 't052-mounted-native-014',
        '20261003-current-heat-installed-017': '20261003-current-heat-installed-018',
        'current-heat-installed-017-': 'current-heat-installed-018-',
        'view-installed-heat-preview-017': 'view-installed-heat-preview-018',
    }),
    ('t052-current-printed-browser-011.mjs', 't052-current-printed-browser-012.mjs', {
        't052-mounted-native-009': 't052-mounted-native-015',
        '20261003-current-printed-installed-011': '20261003-current-printed-installed-012',
        'current-printed-installed-011-': 'current-printed-installed-012-',
    }),
]:
    target = base / target_name
    assert not target.exists(), target
    text = (base / source_name).read_text(encoding='utf-8')
    for old, new in replacements.items():
        text = text.replace(old, new)
    if source_name == 't052-current-heat-browser-017.mjs':
        needle = "const savedUrl=JSON.parse(readFileSync(path.join(privateRoot,'current-heat-installed-010-dom.json'),'utf8')).url;"
        assert needle in text
        text = text.replace(needle, "const retainedUrl=new URL(JSON.parse(readFileSync(path.join(privateRoot,'current-heat-installed-010-dom.json'),'utf8')).url);retainedUrl.host=new URL(proof.frontend_url).host;const savedUrl=retainedUrl.href;")
    if source_name == 't052-current-printed-browser-011.mjs':
        needle = "const savedUrl=previousProgress.split('\\n').filter(line=>line.startsWith('URL: ')&&line.includes('processUIKind=working')).at(-1).slice(5).trim();"
        assert needle in text
        text = text.replace(needle, "const retainedUrl=new URL(previousProgress.split('\\n').filter(line=>line.startsWith('URL: ')&&line.includes('processUIKind=working')).at(-1).slice(5).trim());retainedUrl.host=new URL(proof.frontend_url).host;const savedUrl=retainedUrl.href;")
    target.write_text(text, encoding='utf-8')
print('Prepared current006 normal-workspace editor, both working/common/preview, and exact navigation/reopen walkthroughs; no execution.')
