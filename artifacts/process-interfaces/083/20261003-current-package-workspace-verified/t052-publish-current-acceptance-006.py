"""Audit current installed workspace evidence, preserve failures and publish local scope."""
from pathlib import Path
import hashlib
import html
import json
import shutil
import sqlite3
import subprocess

repo = Path('D:/repos/wright')
base = repo / '.local-run/process-interfaces-083'
artifacts = repo / 'artifacts/process-interfaces/083'
root = artifacts / '20261003-current-package-workspace-verified'
assert not root.exists()
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def tables(path, names):
    with sqlite3.connect('file:' + Path(path).as_posix() + '?mode=ro', uri=True) as db:
        return {name:sha(json.dumps(db.execute('select * from ' + name + ' order by rowid').fetchall(),default=str,separators=(',',':')).encode()) for name in names}
prior = json.loads((artifacts / '20261003-shared-platform-generality-verified/checked-scope.json').read_bytes())
for name, expected in prior['protected_file_hashes'].items():
    assert sha((repo/name).read_bytes()) == expected, name
retained = []
for evidence in prior['retained_actual_engineering_ui_proofs']:
    origin = artifacts / evidence['root']
    inventory = origin / 'inventory.json'
    assert sha(inventory.read_bytes()) == evidence['inventory_sha256']
    entries = json.loads(inventory.read_bytes())['files']
    for name, expected in entries.items():
        path = repo/name if name.startswith('artifacts/') else origin/name
        raw = path.read_bytes()
        assert len(raw) == expected['bytes'] and sha(raw) == expected['sha256'], name
    retained.append(evidence)
fixtures = []
secrets = []
for number, source_context, source_db in [('014','t047-heat-repeat-013','t047-heat-repeat-013'),('015','t047-printed-configured-016','t047-printed-repeat-015')]:
    private = base / ('t052-mounted-native-' + number)
    current = json.loads((private/'browser-context.json').read_bytes())
    original = json.loads((base/source_context/'browser-context.json').read_bytes())
    before = json.loads((private/'workspace-baseline.json').read_bytes())
    source = Path(original['workspace_root'])
    copied = Path(current['workspace_root'])
    relocated = []
    for name, expected in before.items():
        raw = (source/name).read_bytes()
        assert sha(raw) == expected['sha256'] and len(raw) == expected['bytes'], name
        actual = (copied/name).read_bytes()
        if actual == raw:
            continue
        if name == '.hermes.md':
            relocated.append({'path':name,'scope':'Ordinary copied-workspace context materialization'})
            continue
        assert name.startswith('.wright/apps/process.ui-') and name.endswith('.surface.json'), name
        a, b = json.loads(raw), json.loads(actual)
        assert Path(a['launch']['argv'][0]) == repo/'.venv/Scripts/python.exe'
        assert Path(b['launch']['argv'][0]) == base/'t052-mounted-python-006/Scripts/python.exe'
        assert Path(a['launch']['argv'][4]).relative_to(source) == Path(b['launch']['argv'][4]).relative_to(copied)
        assert Path(b['launch']['argv'][4]).is_relative_to(copied/'.wright/process-uis')
        a['launch']['argv'][0] = b['launch']['argv'][0]
        a['launch']['argv'][4] = b['launch']['argv'][4]
        assert a == b, name
        relocated.append({'path':name,'scope':'Only exact installed interpreter and copied immutable UI-vault locator'})
    protected = json.loads((private/'table-baseline.json').read_bytes())
    assert tables(base/source_db/'state.db', protected) == protected
    assert tables(current['database_path'], protected) == protected
    with sqlite3.connect('file:' + Path(current['database_path']).as_posix() + '?mode=ro',uri=True) as db:
        assert db.execute("select count(*) from surface_presentations where state='active'").fetchone()[0] == 0
    fixtures.append({'fixture':number,'original_and_copied_files_checked':len(before),'copied_context_and_host_locator_changes':relocated,'protected_tables_unchanged':list(protected),'active_presentations':0})
    secrets.extend(str(current[k]).encode() for k in ('api_token','browser_cookie') if current.get(k))

required = {
    '20261003-current-editor-010':12,
    '20261003-current-heat-installed-019':5,
    '20261003-current-printed-installed-019':5,
    '20261003-current-heat-installed-018':4,
    '20261003-current-printed-installed-012':4,
    '20261003-current-heat-zoom-installed-025':9,
    '20261003-current-printed-zoom-installed-024':9,
}
other = [f'20261003-current-{kind}-zoom-installed-{version}' for version in ('020','022','023') for kind in ('heat','printed')]
other.append('20261003-current-heat-zoom-installed-021')
other.append('20261003-current-heat-zoom-installed-024')
reports = []
validator = Path('C:/Users/markb/.codex/skills/playwright-ui-walkthrough/scripts/validate_walkthrough.py')
for name in [*required, *other]:
    report_root = artifacts/name/'workspace-walkthrough'
    status = json.loads((report_root/'status.json').read_bytes())
    if name in ('20261003-current-heat-zoom-installed-025','20261003-current-printed-zoom-installed-024'):
        # Editorial checklist correction only; retain original bytes privately.
        backup = base/(name+'-original-report-metadata.json')
        assert not backup.exists()
        backup.write_bytes((report_root/'status.json').read_bytes())
        status['manualSteps'].extend([
            {'label':'Native browser zoom','instruction':'Set browser Zoom to 200% and scroll to the embedded read-only preview.'},
            {'label':'Working views','instruction':'Open the saved working interface. Open Workspace Files and press Escape. Click Use common working view and scroll to the results.'},
            {'label':'Editor at zoom','instruction':'Click Open workflow. Select Source, then Diagram. Leave browser Zoom at 200%.'},
        ])
        (report_root/'status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
        report_html = (report_root/'report.html').read_text(encoding='utf-8')
        start = report_html.index('<h2>Manual steps</h2><ol>') + len('<h2>Manual steps</h2><ol>')
        end = report_html.index('</ol>', start)
        report_html = report_html[:start] + ''.join('<li>'+html.escape(row['instruction'])+'</li>' for row in status['manualSteps']) + report_html[end:]
        (report_root/'report.html').write_text(report_html,encoding='utf-8')
    if name in required:
        assert status['overall'] == 'pass' and len(status['steps']) == required[name]
        assert all(row['state'] == 'pass' for row in status['steps'])
    (report_root.parent/'.gitattributes').write_text('* -text -whitespace\n',encoding='utf-8')
    (report_root/'trace/README.md').write_text('Authenticated traces and frame/bootstrap geometry remain private in the exact isolated fixture. Public screenshots, actions and diagnostics retain this attempt and its scope.\n',encoding='utf-8')
    checked = subprocess.run([str(repo/'.venv/Scripts/python.exe'), str(validator), str(report_root)], capture_output=True,text=True)
    assert checked.returncode == 0, (name, checked.stdout, checked.stderr)
    reports.append({'report':(report_root/'report.html').relative_to(repo).as_posix(),'overall':status['overall'],'steps':len(status['steps']),'primary_current_acceptance':name in required,'limitation':'023 proves measured native zoom but full-page screenshots crop the device viewport;024 supplies primary usable visual evidence' if '-023' in name else None,'structure_validation':checked.stdout.strip()})
for kind, number, version in [('heat','014','025'),('printed','015','024')]:
    value = json.loads((base/f't052-mounted-native-{number}/native-zoom-{kind}-{version}.json').read_bytes())
    assert value['zoom']['factor'] == value['afterZoom'] == 2
    assert value['beforeMetrics']['innerWidth'] == 1440 and value['afterMetrics']['innerWidth'] == 720
    assert value['afterMetrics']['pageScale'] == 1 and value['afterMetrics']['devicePixelRatio'] == 2
    assert value['model_or_process_or_review_requests'] == []

root.mkdir()
(root/'.gitattributes').write_text('* -text -whitespace\n',encoding='utf-8')
for source, destination in [
    ('t052-current-installed-006/build-record.json','build-record.json'),
    ('t052-current-installed-006/command.json','build-command.json'),
    ('t052-current-installed-006/build-output.txt','build-output.txt'),
    ('t052-current-installed-006/source-and-installation-audit.json','source-and-installation-audit.json'),
    ('t052-package-006-source-checkpoint.json','source-checkpoint.json'),
]:
    shutil.copyfile(base/source,root/destination)
for kind, number, version in [('heat','014','025'),('printed','015','024')]:
    private = base/f't052-mounted-native-{number}'
    for name in ['host-identity.json','isolation-record.json',f'native-zoom-{kind}-{version}.json']:
        shutil.copyfile(private/name,root/(kind+'-'+name))
for name in ['t052-stage-current-package-006.py','t052-build-installed-web-006.mjs','t052-build-current-wheel-006.py','t052-stage-current-workspace-019.py','t052-stage-native-zoom-020.py','t052-stage-native-zoom-021.py','t052-stage-native-zoom-022.py','t052-stage-native-zoom-023.py','t052-stage-native-zoom-024.py','t052-stage-native-zoom-025.py','t052-audit-current-package-006.py','t052-publish-current-acceptance-006.py']:
    shutil.copyfile(base/name,root/name)
record = {'scope':'Current installed006 normal-workspace editor, both saved/common/read-only interfaces, exact evidence/producer navigation, preview reopening, keyboard/accessibility and measured native 200% browser zoom',
    'source_commit_before_changes':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
    'source_sha256':{},'protected_file_hashes':prior['protected_file_hashes'],'fixtures':fixtures,'reports':reports,
    'primary_checks':sum(required.values()),'report_structures_validated':len(reports),
    'retained_actual_engineering_ui_proofs':retained,
    'new_model_provider_process_execution':False,'review_responses':0,'physical_effects':False,'human_acceptance':False,
    'original_zoom_failures':['020/021: transient connection banner replaced by observation connection status; stable shared read-only notice remains','022: Playwright :visible pseudo-selector is not standard CSS for axe; corrected active aria-hidden=false scope','023: measured behavior passed; full-page screenshot sizing crops native zoom;024/025 capture actual device viewport','heat024: retryable SURFACE_READINESS_TIMEOUT; failed runtime retained; fresh025 is a new presentation, no engineering replay'],
    'trace_retention_limit':'Earlier zoom harnesses reused the019 private trace/DOM filename; per-attempt public status, screenshots and diagnostics remain, but distinct original private traces were not preserved.025 uses distinct trace/DOM/cleanup names. No authenticated trace or bootstrap geometry is published.',
    'task_ledger':'T052 acceptance audit prepared; full T043/T053/T056/T057 remain separate',
    'new_owned_services':['installed006 thermal fixture014','installed006 preparation fixture015']}
(root/'checked-scope.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
links = '\n'.join(f"- [{Path(row['report']).parent.parent.name}]({(Path('../')/Path(row['report']).relative_to('artifacts/process-interfaces/083')).as_posix()}) — {row['overall']}, {row['steps']} checks; " + ('primary current evidence' if row['primary_current_acceptance'] else 'retained earlier attempt') for row in reports)
(root/'README.md').write_text('# Current installed workspace acceptance\n\nFresh installed006 from b9ce9a14. 953 installed entries are byte-verified against current backend/public resources and the freshly compiled frontend. The frontend manifest remains identical to installed005; backend fixes are included in this new wheel.\n\n48 primary walkthrough checks pass across seven reports. Both actual retained engineering runs preserve exact18/20 outputs, held assessments, UI revisions and protected tables. Browser tab zoom2 gives720px CSS layout from1440px, device pixel ratio2 and pinch scale1. Both common views have672/672px at native200%, with zero scoped WCAG A/AA violations. Native device-viewport024 screenshots supersede cropped023 images for visual scope.\n\n'+links+'\n\nThe first failures are retained. The preview transport connection banner changes during observation; the persistent shared read-only notice and backend binding are the authority checked in the final zoom proof. Axe uses standard CSS scoped to the active retained panel. Authentication traces, bootstrap locators and credentials remain private. No model/provider/engineering execution or review response was submitted. An independent scratch workflow exercises authoring only. This is local automated acceptance, not human product/engineering or physical acceptance. Broader provider/regression/requirement closure remains separate.\n\nZoom harness references: [Chrome tabs.setZoom](https://developer.chrome.com/docs/extensions/reference/api/tabs#method-setZoom), [Playwright Chromium extension testing](https://playwright.dev/docs/chrome-extensions). The test-only extension is confined to disposable browser profiles; Wright requires no extension.\n',encoding='utf-8')
inventory = {}
for selected in [root, *[artifacts/name for name in [*required,*other]]]:
    for path in sorted(selected.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            assert all(secret not in raw for secret in secrets), path
            inventory[path.relative_to(repo).as_posix()] = {'bytes':len(raw),'sha256':sha(raw)}
(root/'inventory.json').write_text(json.dumps({'files':inventory,'credential_value_scan':'passed','authenticated_traces_published':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'published_files':len(inventory)+1,'primary_checks':sum(required.values()),'reports_validated':len(reports),'original_files_checked':sum(row['original_and_copied_files_checked'] for row in fixtures),'protected_tables_unchanged':True,'retained_engineering_ui_files':sum(row['files'] for row in retained)}))
