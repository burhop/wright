"""Create an evidence-linked static review card from completed measurements."""
import html
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
folder = root / 'artifacts/stevecad-demonstrations/qualification/robot-sampled-clearance-001'
report = json.loads((folder/'sampled-clearance.json').read_bytes())
assert report['passed'] and len(report['results']) == 38
assert report['evaluated_pair_samples'] == 14364
minimum = min(x['minimum_nonseat_distance_mm'] for x in report['results'])
assert minimum >= .4-report['linear_kernel_precision_mm']
tiles = ''.join(
    '<div class="sample"><span>'+html.escape(r['pose'].replace('path_', '').replace('_t', ' · '))+'</span>'
    f'<strong>{r["minimum_nonseat_distance_mm"]:.3f}<small> mm</small></strong></div>'
    for r in report['results'] if r['pose'].startswith('path_'))
poses = ' · '.join(html.escape(r['pose'].replace('_', ' ')) for r in report['results'] if not r['pose'].startswith('path_'))
page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Robot arm — sampled clearance evidence</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf0f2;color:#17222b;font:17px "Segoe UI",sans-serif}}
main{{width:1400px;margin:auto;padding:42px 46px;background:white}}header{{border-top:8px solid #ed6b20;padding-top:20px}}
.eyebrow{{font-size:14px;letter-spacing:2px;font-weight:700;color:#92502b}}h1{{font-size:38px;margin:8px 0}}p{{line-height:1.4;margin:10px 0}}
.hero{{display:grid;grid-template-columns:590px 1fr;gap:32px;align-items:center}}.hero img{{width:590px;height:365px;object-fit:contain}}
.stats{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.stat{{background:#f3f6f7;border-left:4px solid #1a7561;padding:18px}}
.stat strong{{display:block;font-size:30px}}.stat span{{display:block;margin-top:5px;font-size:15px}}
h2{{font-size:24px;margin:15px 0 7px}}.grid{{display:grid;grid-template-columns:repeat(11,1fr);gap:7px;margin:15px 0}}
.sample{{background:#eef8f3;border:1px solid #c4ddcf;padding:10px 6px;text-align:center}}.sample span{{display:block;font-size:12px;color:#425b50}}
.sample strong{{display:block;font-size:18px;margin-top:5px}}small{{font-size:11px;font-weight:400}}
.scope{{background:#fff5e9;border-left:4px solid #ed6b20;padding:14px 18px;margin-top:18px;font-size:15px}}
footer{{border-top:1px solid #d4dbe0;margin-top:20px;padding-top:12px;font-size:12px;color:#56646d;overflow-wrap:anywhere}}
a{{color:#235d8b}}
</style><main><header><div class="eyebrow">WRIGHT DEMONSTRATION · INDEPENDENT CAD EVIDENCE</div>
<h1>Robot arm: measured clearance through motion</h1>
<p>Exact exported solids evaluated at five named poses and 33 positions along the eight-second path.</p></header>
<section class="hero"><img src="../../robot-arm-media/corrected-rev7/blender-renderings/render-isometric-final.png" alt="Native rendering of the audited revision 7 robot">
<div class="stats"><div class="stat"><strong>{minimum:.3f} mm</strong><span>Minimum non-seat gap<br>Required: at least 0.400 mm</span></div>
<div class="stat"><strong>14,364</strong><span>Printed-part pair evaluations<br>378 pairs × 38 sampled states</span></div>
<div class="stat"><strong>0 violations</strong><span>Gap and overlap checks<br>25 explicitly declared seat pairs</span></div>
<div class="stat"><strong>28 printed parts</strong><span>Exact STEP solids<br>110 native instances mapped</span></div></div></section>
<h2>Minimum measured gap at every path sample</h2><p>Sample number · time in seconds. Each cell summarizes all 353 non-seat printed-part pairs.</p>
<div class="grid">{tiles}</div><p><strong>Five additional poses passed:</strong> {poses}.</p>
<div class="scope"><strong>Evidence scope:</strong> independent passive STEP audit using the saved native joint axes, couplings and linear keyframes. Original workflow verdicts remain unchanged. Sampled digital clearance does not establish continuous-motion clearance, physical fit, strength, motor sizing or powered operation. The image is a rendering, not measurement evidence.</div>
<footer>SteveCAD document {html.escape(report['document_id'])} · revision 7 · build {html.escape(report['build_id'])}<br>
STEP SHA-256: {report['step_sha256']}<br>Linear kernel precision: {report['linear_kernel_precision_mm']:g} mm; numerical zero-overlap threshold: {report['numeric_zero_volume_threshold_mm3']:g} mm³.
<a href="sampled-clearance.json">Full measured pair results and provenance</a></footer></main></html>'''
dest = folder/'review.html'
assert not dest.exists()
dest.write_text(page, encoding='utf8')
print(dest)
