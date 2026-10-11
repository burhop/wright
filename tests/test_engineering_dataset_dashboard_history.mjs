import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const html=readFileSync(new URL('../scripts/engineering-dataset-dashboard.html',import.meta.url),'utf8');
const source=html.slice(html.indexOf('function chartHistoryRows()'),html.indexOf('function chartSteps('));
const history=new Function('state','retainedPasses','retainedAt','count','date',source+';return chartHistoryRows();');
const count=value=>Number.isFinite(Number(value))?Math.max(0,Math.min(30,Number(value))):0;
const date=value=>new Date(value);
const row=(at,kind,metrics)=>({at:Date.UTC(2026,8,22,0,at),kind,metrics:{datasets_created:30,combinations_run:30,processes_with_outputs:24,valid_data:0,...metrics}});
const values=(rows,latest=null,at=null)=>history({history:rows,metrics:rows.at(-1)?.metrics},latest,at,count,date).map(r=>r.metrics.valid_data);

test('ordinary run and note updates do not erase retained automated inspections',()=>{
  const rows=[row(0,'started'),row(1,'campaign_update',{valid_data:17}),row(2,'run_updated'),row(3,'campaign_update'),row(4,'campaign_update',{valid_data:18}),row(5,'run_updated')];
  assert.deepEqual(values(rows,18,Date.UTC(2026,8,22,0,6)),[0,17,17,17,18,18,18]);
  assert.equal(rows[2].metrics.valid_data,0,'projection must not rewrite immutable history');
});

test('explicit lower and zero inspection results remain visible, distinct from current approvals',()=>{
  const rows=[row(0,'campaign_update',{valid_data:1,automated_validation_passes:18}),row(1,'campaign_update',{valid_data:2,automated_validation_passes:null}),row(2,'campaign_update',{valid_data:2,automated_validation_passes:16}),row(3,'campaign_update',{valid_data:2,automated_validation_passes:0}),row(4,'run_updated',{valid_data:2})];
  assert.deepEqual(values(rows),[18,18,16,0,0]);
});

test('latest report observation is applied in time order and can fall to zero',()=>{
  const rows=[row(0,'started'),row(1,'campaign_update',{valid_data:17}),row(4,'run_updated')];
  assert.deepEqual(values(rows,0,Date.UTC(2026,8,22,0,2)),[0,17,0,0]);
});
