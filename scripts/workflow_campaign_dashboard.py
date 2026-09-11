"""Read-only campaign projection for Wright's existing development dashboard."""
import json
from html import escape


def read_campaign(root):
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    attempts=[]
    for path in sorted((root/'attempts').glob('*.json')):
        item=json.loads(path.read_text(encoding='utf-8'))
        attempts.append({k:item.get(k) for k in ('id','case_id','source_sha256','status','started_at','completed_at','error','engineering_review_required','profile','scope','original_run_started_at','engineering_assertions')})
    attempts.sort(key=lambda item:item.get('started_at') or '')
    rows=[]
    for case in manifest['cases']:
        history=[a for a in attempts if a['case_id']==case['id']]
        current=[a for a in history if a['source_sha256']==case['source_sha256']]
        rows.append({'id':case['id'],'name':case['name'],'category':case['category'],'authored':True,
                     'compiles':case['compiles'],'runnable':case['runnable'],
                     'verified_on_revision':bool(current and current[-1]['status'] in {'structure_verified','engineering_verified'}),
                     'readiness':'Ready' if case['runnable'] else 'Preflight needed' if case['compiles'] else 'Definition needs correction',
                     'last_attempt':current[-1] if current else None,'history':history,
                     'user_accepted':False,'blockers':case['blockers']})
    coverage_path=root/'coverage.json'
    return {'target':manifest['target'],'authored_files':len(rows),'compiled_files':sum(r['compiles'] for r in rows),
            'rehearsal_files':sum(r['category']=='authoring-rehearsal' for r in rows),
            'qualification_counts_unchanged':True,'cases':rows,'planned_cases':manifest.get('planned_cases',[]),
            'features':json.loads(coverage_path.read_text()) if coverage_path.exists() else []}


def render_campaign(data):
    esc=lambda value:escape(str(value))
    rows=''.join(f'<tr><td>{esc(c["id"])}</td><td>{esc(c["name"])}</td><td>{"Yes" if c["compiles"] else "No"}</td><td>{esc(c["readiness"])}</td><td>{esc(c["last_attempt"]["status"] if c["last_attempt"] else "Not run on this revision")}</td><td>Pending</td><td><details><summary>{len(c["history"])} attempts</summary><pre>{esc(json.dumps(c["history"],indent=2))}</pre><p>{esc("; ".join(c["blockers"]))}</p></details></td></tr>' for c in data['cases'])
    features=''.join(f'<li><b>{esc(f["name"])}</b>: implemented {esc(f["implemented"])}, UI {esc(f["ui_integrated"])}, contract tested {esc(f["contract_tested"])}, live verified {esc(f["live_verified"])}, user accepted {esc(f["user_accepted"])}. {esc(f["evidence"])}</li>' for f in data['features'])
    planned=''.join(f'<li>{esc(c["id"])} · {esc(c["name"])}: {len(c["verification_criteria"])} existing engineering assertions. Planned migration; not a live workspace workflow.</li>' for c in data.get('planned_cases',[]))
    return f'''<section id="workflow-campaign" style="margin:24px;padding:20px;border:1px solid #456;overflow:auto">
    <h2>Workflow development campaign</h2><p>{data['authored_files']} saved files · {data['compiled_files']} compile · {data['rehearsal_files']} authoring rehearsal files · target {data['target']} distinct workflows.</p>
    <p>Development evidence only. File structure checks do not establish engineering correctness. Historical qualification counts are unchanged.</p><ul>{features}</ul><details><summary>Existing scenarios to migrate ({len(data.get('planned_cases',[]))})</summary><ul>{planned}</ul></details>
    <p>A verified past run does not prove that its application, selected session model, or credentials are available now. Preflight is checked when a run starts.</p>
    <table><thead><tr><th>ID</th><th>Workflow</th><th>Compiles</th><th>Run readiness</th><th>Evidence for this revision</th><th>User accepted</th><th>History and limits</th></tr></thead><tbody>{rows}</tbody></table></section>'''
