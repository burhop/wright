from pathlib import Path
import hashlib
import json
import runpy
import shutil
import subprocess
import sys
import tomllib

repo = Path('D:/repos/wright')
private = repo / '.local-run/process-interfaces-083/t052-current-installed-006'
assert not private.exists()
private.mkdir()
staged = private / 'build-source'
staged.mkdir()
configuration = tomllib.loads((repo / 'pyproject.toml').read_text(encoding='utf-8'))
wheel = configuration['tool']['hatch']['build']['targets']['wheel']
selected = set(wheel['packages']) | set(wheel['force-include']) | {'README.md', 'LICENSE', 'pyproject.toml'}
for relative in sorted(selected):
    source = repo / relative
    destination = staged / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    else:
        shutil.copyfile(source, destination)
namespace = runpy.run_path(str(repo / 'scripts/build-native-runtime.py'))
stage = namespace['stage_frontend']
stage.__globals__['PACKAGED_WEB'] = staged / 'src/wright_engineering/static/web'
stage.__globals__['WEB_DIST'] = repo / '.local-run/process-interfaces-083/t052-installed-web-006'
manifest = stage()
command = [sys.executable, '-m', 'build', '--wheel', '--no-isolation', '--outdir', str(private / 'dist')]
(private / 'command.json').write_text(json.dumps(command, indent=2) + '\n', encoding='utf-8')
with (private / 'build-output.txt').open('w', encoding='utf-8') as output:
    result = subprocess.run(command, cwd=staged, stdout=output, stderr=subprocess.STDOUT)
record = {'exit_code': result.returncode, 'frontend_manifest_sha256': manifest,
    'source_root': str(staged), 'published': False, 'browser_verified': False,
    'original_packaged_frontend_unchanged': True}
if result.returncode == 0:
    candidates = list((private / 'dist').glob('*.whl'))
    assert len(candidates) == 1
    record.update(wheel=candidates[0].name, wheel_sha256=hashlib.sha256(candidates[0].read_bytes()).hexdigest())
(private / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
if result.returncode:
    print((private / 'build-output.txt').read_text(encoding='utf-8')[-3500:])
raise SystemExit(result.returncode)
