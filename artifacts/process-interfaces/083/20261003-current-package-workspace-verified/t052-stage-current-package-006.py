"""Prepare fresh current-build qualification; preserve every prior build/fixture."""
from pathlib import Path
import subprocess
import json

repo = Path('D:/repos/wright')
base = repo / '.local-run/process-interfaces-083'
assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=repo, text=True).strip() == 'codex/083-process-working-interfaces'
replacements = {
    't052-current-installed-005': 't052-current-installed-006',
    't052-installed-web-005': 't052-installed-web-006',
    't052-installed-web-cache-005': 't052-installed-web-cache-006',
    't052-mounted-python-005': 't052-mounted-python-006',
}
outputs = []
for source_name, target_name, extra in [
    ('t052-build-installed-web-005.mjs', 't052-build-installed-web-006.mjs', {}),
    ('t052-build-current-wheel-005.py', 't052-build-current-wheel-006.py', {}),
    ('t052-prepare-installed-fixture-012.py', 't052-prepare-installed-fixture-014.py', {
        't052-mounted-native-012': 't052-mounted-native-014',
        't052-native-installed-home-012': 't052-native-installed-home-014',
        't052-mounted-native-host-012': 't052-mounted-native-host-014',
    }),
    ('t052-prepare-installed-fixture-013.py', 't052-prepare-installed-fixture-015.py', {
        't052-mounted-native-013': 't052-mounted-native-015',
        't052-native-installed-home-013': 't052-native-installed-home-015',
        't052-mounted-native-host-013': 't052-mounted-native-host-015',
    }),
]:
    destination = base / target_name
    assert not destination.exists(), destination
    text = (base / source_name).read_text(encoding='utf-8')
    for old, new in {**replacements, **extra}.items():
        text = text.replace(old, new)
    destination.write_text(text, encoding='utf-8')
    outputs.append(target_name)
(base / 't052-package-006-source-checkpoint.json').write_text(json.dumps({
    'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
    'helpers': outputs, 'new_frontend_build': True, 'new_backend_build': True,
    'provider_or_model_or_engineering_execution': False,
}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'prepared_helpers': outputs}))
