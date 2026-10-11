"""Byte-verify the fresh wheel, current sources and isolated native installations."""
from pathlib import Path
import hashlib
import json
import subprocess
import tomllib
import zipfile

repo = Path('D:/repos/wright')
base = repo / '.local-run/process-interfaces-083'
out = base / 't052-current-installed-006/source-and-installation-audit.json'
assert not out.exists()
configuration = tomllib.loads((repo / 'pyproject.toml').read_text(encoding='utf-8'))['tool']['hatch']['build']['targets']['wheel']
mapping = [(Path(root).name, root) for root in configuration['packages']]
mapping += [(destination, source) for source, destination in configuration['force-include'].items()]
mapping.sort(key=lambda row: len(row[0]), reverse=True)
wheel = next((base / 't052-current-installed-006/dist').glob('*.whl'))
installed = base / 't052-mounted-python-006/Lib/site-packages'
stage = base / 't052-current-installed-006/build-source'
checked = []
staged_web = []
metadata = []
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
with zipfile.ZipFile(wheel) as archive:
    for name in archive.namelist():
        if name.endswith('/'):
            continue
        raw = archive.read(name)
        assert (installed / name).read_bytes() == raw, name
        if '.dist-info/' in name:
            metadata.append(name)
            continue
        source = None
        for destination, current in mapping:
            if name == destination or name.startswith(destination + '/'):
                suffix = name[len(destination):].lstrip('/')
                source = repo / current / suffix if suffix else repo / current
                break
        assert source is not None, name
        if name.startswith('wright_engineering/static/web/'):
            staged = stage / 'src/wright_engineering/static/web' / name.removeprefix('wright_engineering/static/web/')
            assert staged.read_bytes() == raw, name
            staged_web.append({'wheel_path': name, 'sha256': sha(raw)})
        else:
            assert source.read_bytes() == raw, source
            checked.append({'wheel_path': name, 'source_path': source.relative_to(repo).as_posix(), 'sha256': sha(raw)})
    names = archive.namelist()
    assert not any('print_part_demo' in name or name.endswith('printing_support.py') for name in names)
    manifest_bytes = archive.read('wright_engineering/static/web/asset-manifest.json')
    frontend_manifest = json.loads(manifest_bytes)
    for row in frontend_manifest['files']:
        raw = archive.read('wright_engineering/static/web/' + row['path'])
        assert sha(raw) == row['sha256'] and len(raw) == row['size'], row
for fixture in ('014', '015'):
    identity = json.loads((base / f't052-mounted-native-{fixture}/host-identity.json').read_bytes())
    assert not identity['original_worktree_imports'] and not identity['provider_autostart']
    assert identity['frontend_from_installed_wheel'] and not identity['compiler_available']
record = {
    'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
    'wheel_sha256': sha(wheel.read_bytes()), 'frontend_manifest_sha256': sha(manifest_bytes),
    'installed_entries_byte_verified': len(checked) + len(staged_web) + len(metadata),
    'current_source_entries': checked, 'fresh_compiled_frontend_entries': staged_web,
    'build_metadata_entries': metadata, 'retired_prototype_modules_absent': True,
    'served_host_fixtures': ['014', '015'],
    'build_flags': {'workflow_recovery': True, 'workflow_composer': True, 'process_definition_view': True},
    'qualification': 'Fresh installed native wheel and exact checkout/backend plus freshly compiled frontend byte parity; no original checkout imports in the live hosts',
    'release_or_docker_or_engineering_execution': False,
}
out.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: record[key] for key in ['source_commit','wheel_sha256','frontend_manifest_sha256','installed_entries_byte_verified','retired_prototype_modules_absent']}))
