// Reporting only: recorded observations and exact retained outputs. No executor.
let viewerModule;
function viewers(){
  if(!data.viewer_url)return Promise.reject(new Error('The local viewer bundle is unavailable.'));
  return viewerModule||(viewerModule=import(new URL(data.viewer_url,location.href).href));
}
let readerDispose,readerRevision=0;
const reader=$('evidence-reader');
function closeReader(){readerRevision++;readerDispose?.();readerDispose=undefined;reader.close();}
$('reader-close').onclick=closeReader;
reader.addEventListener('cancel',event=>{event.preventDefault();closeReader();});
reader.addEventListener('click',event=>{if(event.target===reader){const r=reader.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closeReader();}});
function readableText(host,text){
  if(/^[\s]*[\[{]/.test(text)){try{structuredRecord(host,JSON.parse(text));return;}catch{}}
  // Preserve exact values while making fixed-column notes readable as a table.
  const lines=text.trim().split('\n');
  const end=lines.findIndex(line=>!line.trim());
  const first=lines.slice(0,end<0?lines.length:end);
  if(first.length>2&&first.every(line=>/\S\s{2,}\S/.test(line))){
    const table=make('table',undefined,'readable-values');
    for(const line of first){const parts=line.split(/\s{2,}/);const tr=make('tr');tr.append(make('th',parts.shift()),cell(parts.join('  ')));table.append(tr);}
    host.append(table);
    if(end>=0)host.append(make('div',lines.slice(end).join('\n'),'readable-text'));
  }else host.append(make('div',text,'readable-text'));
}
function originalLink(label,url){
  const raw=/\.jsonl?$/.test(new URL(url,location.href).pathname);
  const a=link(raw?'Download raw data':label,url);a.download='';return a;
}
const recordLabels={
  max_displacement_mm:'Maximum displacement (mm)',h_mm:'Mesh size (mm)',
  applied_force_N:'Applied force (N)',reaction_force_N:'Reaction force (N)',
  force_residual_N:'Force imbalance (N)',compliance_Nmm:'Compliance (N·mm)',
  reaction_moment_about_origin_Nmm:'Reaction moment about origin (N·mm)',
  applied_moment_about_origin_Nmm:'Applied moment about origin (N·mm)',moment_residual_Nmm:'Moment imbalance (N·mm)',
  last_displacement_change_percent:'Displacement change after mesh refinement (%)',last_compliance_change_percent:'Compliance change after mesh refinement (%)',
  elapsed_seconds:'Elapsed time (s)',seconds:'Duration (s)',started_at:'Started',
  finished_at:'Finished',at:'Observed',isError:'Error reported',source_status:'Save result',
  execution_diagnostic:'What prevents execution',correction:'Required next step',
  original_preserved:'Original workflow preserved',instructions_preserved:'Instructions preserved',
  instruction_line_identical:'Instructions unchanged',review_blocks_preserved:'Review steps preserved',
  original_review_blocks:'Original review steps',run_started_by_this_call:'Execution started',
  strict_no_write:'Rejected edit left the saved file unchanged',cases:'Analysis results'
};
const recordName=key=>recordLabels[key]||key.replaceAll('_',' ').replace(/([a-z])([A-Z])/g,'$1 $2').replace(/^./,s=>s.toUpperCase());
const technicalKey=key=>/sha256|digest|^(schema_version|trace_id|session_id|run_id|thread_id|workflow_id|editor_path|meta|structuredContent|source_sha256)$/.test(key);
function recordScalar(value,key=''){
  if(value===null)return 'Not recorded';
  if(typeof value==='boolean')return value?'Yes':'No';
  if(typeof value==='string'){
    if(/^(at|.*_at)$/.test(key)&&/^\d{4}-\d\d-\d\dT/.test(value))return date(value);
    const names={saved_draft:'Draft saved',WORKFLOW_NOT_READY:'Workflow needs setup',READINESS_UNSUPPORTED:'This step needs configuration',authoring_shape_only:'Draft structure checked; execution not approved'};
    if(names[value])return names[value];
    if(/^[a-z]+(?:_[a-z]+)+$/.test(value))return recordName(value);
  }
  return String(value);
}
function recordCell(value,key){
  if(typeof value==='number'){
    const shown=Number.isInteger(value)?value.toLocaleString('en-US'):Number(value.toPrecision(6)).toString();
    const span=make('span',shown,'num');span.title=`Exact recorded value: ${value}`;return span;
  }
  if(typeof value==='string'&&/^[\s]*[\[{]/.test(value)){
    try{const parsed=JSON.parse(value),host=make('div');structuredRecord(host,parsed,1);return host;}catch{}
  }
  return recordScalar(value,key);
}
function structuredRecord(host,value,depth=0,context=''){
  // Present data as labeled values, never JSON/code. Original bytes stay downloadable.
  if(depth>8){host.append(make('p','Further technical detail is available in the original download.','muted'));return;}
  if(typeof value==='string'&&/^[\s]*[\[{]/.test(value)){
    try{structuredRecord(host,JSON.parse(value),depth+1);return;}catch{}
  }
  if(!value||typeof value!=='object'){host.append(make('p',recordScalar(value),'readable-text'));return;}
  if(Array.isArray(value)){
    if(!value.length){host.append(make('p','No entries recorded.','muted'));return;}
    if(value.every(v=>v===null||typeof v!=='object')){
      const vector=value.length===3&&/force|moment|residual/.test(context);
      host.append(rowsTable([vector?'Axis':'Item','Value'],value.map((v,i)=>[vector?['X','Y','Z'][i]:String(i+1),recordCell(v)])));return;
    }
    const objects=value.every(v=>v&&typeof v==='object'&&!Array.isArray(v));
    const keys=objects?[...new Set(value.flatMap(v=>Object.keys(v)))].filter(k=>!technicalKey(k)):[];
    const tabular=objects&&keys.length>0&&keys.length<=10&&value.every(v=>keys.every(k=>v[k]==null||typeof v[k]!=='object'));
    let offset=0;const items=make('div');host.append(items);const more=button('Show more entries',append);host.append(more);
    function append(){
      const chunk=value.slice(offset,offset+50);
      if(tabular)items.append(rowsTable(keys.map(recordName),chunk.map(v=>keys.map(k=>recordCell(v[k]??null,k)))));
      else for(const entry of chunk){
        const label=typeof entry==='object'&&entry?(entry.title||entry.label||entry.name||(entry.variant?`${recordName(entry.variant)}${entry.h_mm!==undefined?` · ${entry.h_mm} mm mesh`:''}`:`Entry ${offset+1}`)):`Value ${offset+1}`;
        const box=make('details');box.open=value.length<=6&&depth<=1;box.append(make('summary',label));
        const body=make('div',undefined,'record-body');structuredRecord(body,entry,depth+1);box.append(body);items.append(box);offset++;
      }
      if(tabular)offset+=chunk.length;
      more.hidden=offset>=value.length;more.textContent=`Show more entries (${value.length-offset} remaining)`;
    }
    append();return;
  }
  const visible=Object.entries(value).filter(([k])=>!technicalKey(k));
  const scalars=visible.filter(([,v])=>v===null||typeof v!=='object');
  if(scalars.length)host.append(rowsTable(['Property','Value'],scalars.map(([k,v])=>[recordName(k),recordCell(v,k)]),'readable-values'));
  for(const [key,entry] of visible.filter(([,v])=>v!==null&&typeof v==='object')){
    const box=make('details');box.open=depth===0;box.append(make('summary',recordName(key)));
    const body=make('div',undefined,'record-body');structuredRecord(body,entry,depth+1,key);box.append(body);host.append(box);
  }
  const technical=Object.entries(value).filter(([k,v])=>technicalKey(k)&&v!==null);
  if(technical.length){const box=make('details');box.append(make('summary','Technical references'));const body=make('div',undefined,'record-body');
    for(const [k,v] of technical){body.append(make('h3',recordName(k)));structuredRecord(body,v,depth+1);}box.append(body);host.append(box);}
}
async function preview(item){
  const revision=++readerRevision;
  readerDispose?.();readerDispose=undefined;
  $('reader-title').textContent=item.label;
  $('reader-context').textContent=item.description||'';
  const host=$('reader-body');host.replaceChildren();
  $('reader-source').replaceChildren(originalLink('Download original',item.url));
  if(item.at)$('reader-source').append(make('span',date(item.at)));
  if(!reader.open)reader.showModal();
  reader.scrollTop=0;
  try{
    const document=data.documents?.[item.url];
    if(document){
      if(document.format==='markdown'){
        host.append(make('p','Opening document…','muted'));
        const module=await viewers();if(revision!==readerRevision)return;
        host.replaceChildren();readerDispose=module.documentView(host,document.text);
      }else if(document.format==='record')structuredRecord(host,JSON.parse(document.text));
      else readableText(host,document.text);
    }else if(item.kind==='data'&&(data.record_urls||[]).includes(item.url)){
      host.append(make('p','Opening recorded results…','muted'));
      const response=await fetch(item.url,{credentials:'same-origin',cache:'no-store'});
      if(!response.ok)throw new Error(`Results unavailable (HTTP ${response.status}).`);
      const record=await response.json();if(revision!==readerRevision)return;
      host.replaceChildren();structuredRecord(host,record);
    }else if(item.kind==='image'){
      const img=make('img');img.src=item.url;img.alt=item.label;host.append(img);
    }else if(item.kind==='model'){
      host.append(make('p','Opening exact retained STL…','muted'));
      const [module,response]=await Promise.all([viewers(),fetch(item.url,{credentials:'same-origin',cache:'no-store'})]);
      if(!response.ok)throw new Error(`Model unavailable (HTTP ${response.status}).`);
      const bytes=await response.arrayBuffer();if(revision!==readerRevision)return;
      host.replaceChildren();readerDispose=module.modelView(host,bytes,item.label);
    }else if(item.kind==='pdf'){
      const frame=make('iframe');frame.src=item.url;frame.title=item.label;frame.style.cssText='width:100%;height:65vh;border:0';host.append(frame);
    }else if(item.text!==undefined)readableText(host,item.text);
    else host.append(make('p','Use Download original to inspect this file in its native application.','readable-text'));
  }catch(error){
    if(revision!==readerRevision)return;
    host.replaceChildren(make('p',error.message,'readable-text'));
    const document=data.documents?.[item.url];if(document&&document.format!=='record')readableText(host,document.text);
  }
}
// All registered Markdown/text links open in the same readable view. Source
// URLs remain scoped by the existing server's hash-bound evidence allowlist.
document.addEventListener('click',event=>{
  const a=event.target.closest?.('a');
  if(!a||a.hasAttribute('download')||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  const key=[...Object.keys(data.documents||{}),...(data.record_urls||[])].find(url=>new URL(url,location.href).href===a.href);
  if(key){event.preventDefault();preview({label:a.textContent,url:key,kind:'data'});}
});
function button(label,action){const b=make('button',label,'small-button');b.onclick=action;return b;}
function panel(title,meta){const box=make('section',undefined,'panel');const head=make('div',undefined,'panel-head');head.append(make('h2',title));if(meta)head.append(make('small',meta));const body=make('div',undefined,'panel-body');box.append(head,body);return {box,body,head};}
function rowsTable(headings,rows,cls){const wrap=make('div',undefined,'table-wrap');const table=make('table',undefined,cls);const head=make('thead'),tr=make('tr');headings.forEach(h=>tr.append(make('th',h)));head.append(tr);const body=make('tbody');for(const values of rows){const row=make('tr');for(const value of values){const td=cell();if(value instanceof Node)td.append(value);else td.textContent=value;row.append(td);}body.append(row);}table.append(head,body);wrap.append(table);return wrap;}
function promptList(host,s){
  const prompts=s?.result_details?.prompts||[];
  if(!prompts.length){host.append(make('p','No exact typed prompt retained for this attempt.','muted'));return;}
  prompts.forEach((prompt,index)=>{
    const group=make(index===0?'div':'details',undefined,'result-prompt');
    if(index>0)group.append(make('summary',prompt.label));
    const meta=make('div',undefined,'prompt-label');meta.append(make('strong',index===0?'Customer’s opening request':prompt.label),make('time',date(prompt.at)));
    const content=make('div');content.append(meta,make('blockquote',prompt.text,index===0?'case-request':'followup'));
    group.append(content);host.append(group);
  });
}
function outputGallery(host,artifacts){
  const images=artifacts.filter(a=>a.kind==='image');if(!images.length)return;
  const main=make('img',undefined,'screen-main'),caption=make('div',undefined,'prompt-label'),thumbs=make('div',undefined,'case-screens');
  let selected;
  const choose=(image,b)=>{selected=image;main.src=image.url;main.alt=image.label;caption.replaceChildren(make('strong',image.label),make('time',date(image.at)));for(const child of thumbs.children)child.classList.toggle('selected',child===b);};
  images.forEach(image=>{const b=make('button',undefined,'case-screen');b.title=image.label;const img=make('img');img.src=image.url;img.alt=image.label;img.loading='lazy';b.append(img,make('div',image.label,'screen-caption'));b.onclick=()=>choose(image,b);thumbs.append(b);});
  main.onclick=()=>preview(selected);choose(images[0],thumbs.firstChild);host.append(main,caption,thumbs);
}
function artifactCards(host,artifacts){
  const grid=make('div',undefined,'artifact-grid');
  for(const item of artifacts){
    const card=make('div',undefined,'artifact-card');
    const origin=item.origin==='operator'&&item.engineering_evidence?'Operator engineering follow-up':{local_experiment:'Local engineering experiment',operator:'Developer follow-up',supporting:'Study reference',workflow_run:'Wright workflow result'}[item.origin];
    card.append(make('span',origin||'Retained evidence','origin-tag'),make('h3',item.label));
    if(item.kind==='image'){
      const picture=make('button',undefined,'artifact-preview');picture.title=`View ${item.label}`;
      const img=make('img');img.src=item.url;img.alt=item.label;img.loading='lazy';
      picture.append(img);picture.onclick=()=>preview(item);card.append(picture);
    }
    if(item.description)card.append(make('p',item.description));
    const actions=make('div',undefined,'artifact-actions');
    const viewLabel={model:'Rotate 3D model',image:'View image',document:'Read document',text:'Read result',pdf:'Read PDF',data:'View values'}[item.kind];
    if(viewLabel)actions.append(button(viewLabel,()=>preview(item)));
    actions.append(originalLink('Download',item.url));card.append(actions);grid.append(card);
  }host.append(grid);
}
function comparisonView(host,study){
  if(study.comparison?.schema_version==='wright.mesh-comparison/1'){
    host.append(make('div',study.verdict,'comparison-verdict'));
    host.append(rowsTable(['Quantity','Coarse','Finer','Change','Limit'],study.comparison.rows.map(r=>[
      `${r.quantity} (${r.unit})`,r.coarse.toFixed(4),r.fine.toFixed(4),`${r.change_percent.toFixed(2)}%`,r.limit_percent===null?'Diagnostic':`${r.limit_percent}%`
    ])));
    host.append(make('p',study.comparison_limit,'note'));return;
  }
  const rows=study.comparison?.cases;if(!rows?.length)return;
  host.append(make('div',study.verdict,'comparison-verdict'));
  const names={baseline:'Baseline surrogate',larger_bend:'Larger-bend trial'},colors={baseline:'#4b79a5',larger_bend:'#167d79'};
  const ns='http://www.w3.org/2000/svg';
  const el=(tag,attrs,text)=>{const node=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))node.setAttribute(k,v);if(text!==undefined)node.textContent=text;return node;};
  const svg=el('svg',{viewBox:'0 0 540 260',role:'img','aria-label':'Maximum displacement versus mesh size. Local analysis; comparison remains inconclusive.',class:'comparison-chart'});
  const left=66,right=510,top=24,bottom=198;
  const minY=Math.floor(Math.min(...rows.map(r=>r.max_displacement_mm))*1000-1)/1000,maxY=Math.ceil(Math.max(...rows.map(r=>r.max_displacement_mm))*1000+1)/1000;
  const minX=Math.min(...rows.map(r=>r.h_mm)),maxX=Math.max(...rows.map(r=>r.h_mm));
  const x=v=>left+(maxX-v)/(maxX-minX||1)*(right-left),y=v=>bottom-(v-minY)/(maxY-minY)*(bottom-top);
  for(let i=0;i<=4;i++){const v=minY+(maxY-minY)*i/4;svg.append(el('line',{x1:left,x2:right,y1:y(v),y2:y(v),stroke:'#e3e9ed'}),el('text',{x:left-9,y:y(v)+4,'text-anchor':'end'},v.toFixed(3)));}
  for(const v of [...new Set(rows.map(r=>r.h_mm))])svg.append(el('text',{x:x(v),y:bottom+22,'text-anchor':'middle'},v.toFixed(1)));
  svg.append(el('text',{x:(left+right)/2,y:bottom+48,'text-anchor':'middle'},'Nominal mesh size (mm) → finer'),el('text',{x:16,y:115,transform:'rotate(-90 16 115)','text-anchor':'middle'},'Max displacement (mm)'));
  for(const variant of [...new Set(rows.map(r=>r.variant))]){
    const samples=rows.filter(r=>r.variant===variant).sort((a,b)=>b.h_mm-a.h_mm);
    svg.append(el('polyline',{points:samples.map(r=>`${x(r.h_mm)},${y(r.max_displacement_mm)}`).join(' '),fill:'none',stroke:colors[variant]||'#8876aa','stroke-width':2}));
    for(const r of samples){const dot=el('circle',{cx:x(r.h_mm),cy:y(r.max_displacement_mm),r:4,fill:colors[variant]||'#8876aa'});dot.append(el('title',{},`${names[variant]||variant}: ${r.max_displacement_mm.toFixed(6)} mm, h=${r.h_mm} mm`));svg.append(dot);}
  }host.append(svg);
  const legend=make('div',undefined,'legend');for(const [id,color] of Object.entries(colors)){const entry=make('span');const swatch=make('i',undefined,'swatch');swatch.style.background=color;entry.append(swatch,document.createTextNode(names[id]));legend.append(entry);}host.append(legend);
  host.append(rowsTable(['Design','Mesh (mm)','Max disp. (mm)','Force error (%)'],rows.map(r=>[names[r.variant]||r.variant,r.h_mm.toFixed(1),r.max_displacement_mm.toFixed(6),(Math.hypot(...r.force_residual_N)/40*100).toFixed(4)])));
  host.append(make('p',study.comparison_limit,'note'));
}
function engineeringCase(study){
  const host=$('current-case');host.replaceChildren();
  const attempts=allSessions.filter(s=>study.session_ids.includes(s.id));const last=attempts.at(-1);
  const intro=panel('Engineering case','60-minute complete-journey target');
  intro.body.append(make('h2',study.title,'case-title'),make('p',study.objective,'case-objective'));
  const meta=make('div',undefined,'inline-meta');meta.append(make('span',study.status),make('time',`Engineering checkpoint: ${date(study.as_of)}`));intro.body.append(meta);
  const alert=make('div',undefined,'case-alert');alert.append(make('strong','What is stopping progress'),document.createTextNode(study.blocker));intro.body.append(alert);
  const next=make('p',undefined,'note');next.append(make('strong','Next: '),document.createTextNode(study.next));intro.body.append(next);host.append(intro.box);
  const stages=panel('Engineering progress','Last observed results');
  stages.body.replaceWith(rowsTable(['Stage','Engineering tools','Observed result'],study.stages.map(stage=>{const result=make('div');result.append(make('div',stage.status,'case-state'),make('div',stage.detail,'step-note'));return [stage.label,stage.tools,result];}),'case-stage-table'));host.append(stages.box);
  const layout=make('div',undefined,'case-layout');
  const visit=study.current_visit;
  const request=panel(visit?'Current visit · actual request':'Last completed visit · actual request',visit?date(visit.observed_at):last?date(last.started_at):'');
  promptList(request.body,visit?{result_details:visit}:last);
  if(visit){
    request.body.prepend(make('div',`${visit.label} · ${time(visit.journey_timing.elapsed_seconds)} recorded · ${visit.journey_timing.finished?'Visit ended':'Last observed in progress'}`,'note'));
    request.body.append(make('p',visit.summary,'note'));
  }else if(last){const meta=make('div',`${last.scope==='first_contact'?'Full journey':'Prepared retry'} · ${time(actualElapsed(last))} · ended ${date(last.finished_at)}`,'note');request.body.prepend(meta);request.head.append(button('Full visit →',()=>openVisit(last)));}
  layout.append(request.box);
  if(visit){const response=panel('Current visit · what the customer sees',date(visit.observed_at));outputGallery(response.body,(visit.artifacts||[]).slice().reverse());layout.append(response.box);}
  else if(study.comparison){const comparison=panel('What the engineering results show',study.comparison.schema_version==='wright.mesh-comparison/1'?'Two actual Wright assessments · operator comparison':'Retained engineering evidence');comparisonView(comparison.body,study);layout.append(comparison.box);}
  host.prepend(layout);
  if(visit){const stages=panel('Current visit · stage timing','Recorded through the observation time');stages.body.append(rowsTable(['Stage','Time','State'],visit.stage_timing.stages.map(s=>[s.label,time(s.seconds),statePill(s.status)])));layout.after(stages.box);}
  const readiness=panel('Demonstration readiness','Dated evidence · public availability is separate');
  readiness.body.append(rowsTable(['Example','Connected engineering work','First hour','Repeat demo','Website package'],(data.demonstration_readiness||[]).map(r=>[r.example,r.engineering,r.first_hour,r.repeat_demo,r.website])));
  if((data.demonstration_readiness||[]).length)host.prepend(readiness.box);
  const outputs=panel('Models and readable results','Exact retained files');
  const engineeringArtifacts=study.artifacts.filter(a=>a.origin!=='local_experiment'&&(a.origin!=='operator'||a.engineering_evidence));
  const primary=engineeringArtifacts.filter(a=>['model','text','document','image'].includes(a.kind));artifactCards(outputs.body,primary);
  const more=make('details');more.append(make('summary','Native CAD downloads and technical evidence'));artifactCards(more,engineeringArtifacts.filter(a=>!primary.includes(a)));outputs.body.append(more);host.append(outputs.box);
  const earlier=study.artifacts.filter(a=>a.origin==='local_experiment');if(earlier.length){const old=make('details');old.append(make('summary','Earlier local experiments'));artifactCards(old,earlier);outputs.body.append(old);}
  if(!visit){const screens=panel('What the customer saw',last?date(last.finished_at):'');outputGallery(screens.body,last?.result_details?.artifacts||[]);host.append(screens.box);}
  const timelineRows=events=>rowsTable(['When','Event'],events.slice().reverse().map(e=>{const description=make('div');description.append(make('strong',e.title),make('div',e.detail,'step-note'));return [make('time',date(e.at)),description];}),'case-timeline');
  const timeline=panel('Beta customer milestones','All times include date and timezone');
  timeline.body.replaceWith(timelineRows(study.timeline.filter(e=>e.kind==='Customer')));host.append(timeline.box);
  const followup=panel('Fixes from beta feedback',study.title);
  followup.body.append(timelineRows(study.timeline.filter(e=>e.kind!=='Customer')));
  const evidence=make('details');evidence.append(make('summary','Developer evidence'));artifactCards(evidence,study.artifacts.filter(a=>a.origin==='operator'));followup.body.append(evidence);$('developer-followup').append(followup.box);
  const history=panel('Visits for this engineering case','Focused retries are excluded from full-journey metrics');
  history.body.replaceWith(rowsTable(['Visit','Started','Finished','Duration','Result'],attempts.slice().reverse().map(s=>[button(s.id.split('-').at(-1)+' · Prompts & results',()=>openVisit(s)),date(s.started_at),date(s.finished_at),time(s.elapsed_seconds),stateNames[s.outcome]||s.outcome])));host.append(history.box);
}
function engineeringFollowups(study){
  if(!study)return;
  for(const id of ['progress-followup','journey-followup']){
    const host=$(id);host.replaceChildren();
    const box=panel('Latest engineering attempts','Follow-up work · excluded from fresh-customer metrics');
    const status=make('div',undefined,'followup-status');
    status.append(make('strong',study.status),make('time',`Observed ${date(study.as_of)}`));
    box.body.append(status);
    const last=allSessions.filter(s=>study.session_ids.includes(s.id)).at(-1);
    if(study.current_visit)box.body.append(make('div',`Latest customer observation ${date(study.current_visit.observed_at)} · ${study.current_visit.journey_timing.finished?'Visit ended':'Visit in progress at observation'} · completion not yet credited`,'note'));
    else if(last)box.body.append(make('div',`Last completed beta visit ended ${date(last.finished_at)}`,'note'));
    const attempts=study.followup_runs||[];
    if(attempts.length)box.body.append(rowsTable(['Started','Engineering task','Run time','Execution','Result'],attempts.slice().reverse().map(attempt=>{
      const result=make('div');result.append(make('div',attempt.outcome||''));
      const artifact=study.artifacts.find(a=>a.id===attempt.artifact_id);
      if(artifact)result.append(button('Open result',()=>preview(artifact)));
      const task=make('div');task.append(make('strong',attempt.title));
      if(attempt.finished_at)task.append(make('div',`Finished ${date(attempt.finished_at)}`,'subrow'));
      return [make('time',date(attempt.started_at)),task,make('span',time(attempt.elapsed_seconds),'num'),statePill(attempt.status),result];
    }),'followup-runs'));
    else box.body.append(make('p','No engineering follow-up runs recorded.','muted'));
    box.body.append(button('Current engineering work →',()=>{switchView('current');scrollTo(0,0);}));host.append(box.box);
  }
}
function outcomeEvidence(){
  const visits=data.sessions.filter(s=>s.performance_eligible&&!s.lab_failure);
  const reported=visits.filter(s=>['independent_completion','completion_with_help'].includes(s.outcome));
  const reviewed=visits.filter(s=>s.qualified);
  const checked=reviewed.filter(s=>s.journey_complete);
  const box=panel('Customer outcome evidence','Full journeys only · no operator-run credit');
  box.body.append(rowsTable(['Measure','Result','Meaning'],[
    ['Customer reports completion',`${reported.length} / ${visits.length}`,'Original beta feedback; includes completion with ordinary help'],
    ['Evidence-checked completion',reviewed.length?`${checked.length} / ${reviewed.length}`:'Pending',`${visits.length-reviewed.length} visits not independently verified; pending is not failure`],
    ['Human engineering approval','Exact output subjects only','Separate from customer usability; baseline handle approval does not approve a revised design']
  ]));
  $('progress-followup').prepend(box.box);
}
function openVisit(s){$('journey-select').value=s.id;renderJourney();switchView('journey');$('request-results').scrollIntoView({block:'start'});}
function developerWork(){
  const host=$('developer-activity');host.replaceChildren();
  const open=(data.activity_history||[]).flatMap(r=>r.open_windows).filter(r=>!r.lane.startsWith('customer-')).sort((a,b)=>new Date(b.started_at)-new Date(a.started_at));
  if(open.length){for(const work of open){host.append(make('div',work.summary||work.task,'now-title'));const meta=make('div',undefined,'now-meta');meta.append(make('span',phaseNames[work.phase]||work.phase),make('time',`Started ${date(work.started_at)}`),make('span',work.origin==='outside_loop'?'Requested outside the beta loop':'Beta campaign work'));host.append(meta);}}
  else{
    const last=(data.activity_history||[]).flatMap(r=>r.intervals).filter(r=>!r.lane.startsWith('customer-')).sort((a,b)=>new Date(b.finished_at)-new Date(a.finished_at))[0];
    host.append(make('div',last?last.summary:'No developer activity recorded','now-title'));
    if(last)host.append(make('div',`Last completed work · ${date(last.finished_at)} · ${phaseNames[last.phase]||last.phase}`,'now-meta'));
  }
}
function currentWork(study){
  // Engineering progress is a dated case observation. Developer task strings
  // never substitute for the beta customer's activity or a product run state.
  const host=$('current-work');host.replaceChildren();
  const attempts=study?allSessions.filter(s=>study.session_ids.includes(s.id)):allSessions;
  const last=allSessions.find(s=>s.id===study?.current_visit?.session_id)||attempts.at(-1);
  if(study?.current_visit&&!study.current_visit.journey_timing.finished){
    const visit=study.current_visit;
    host.append(make('div',visit.activity,'now-title'));
    host.append(rowsTable(['Customer job','Started','Recorded time','Last observed'],[[study.title,date(visit.journey_timing.started_at),time(visit.journey_timing.elapsed_seconds),date(visit.observed_at)]]));
    host.append(make('p',visit.summary,'note'));
    if(last)host.append(button(`Previous completed visit · ${date(last.finished_at)} →`,()=>openVisit(last)));
    return;
  }
  host.append(make('div',study?.status||'Latest beta customer visit','now-title'));
  if(study)host.append(make('div',study.title,'now-meta'));
  if(study?.customer_activity)host.append(make('div',study.customer_activity,'note'));
  const meta=make('div',undefined,'now-meta');
  if(study)meta.append(make('time',`Status observed ${date(study.as_of)}`));
  if(last)meta.append(make('span',`Last beta visit ended ${date(last.finished_at)} · ${stateNames[last.outcome]||last.outcome}`));
  host.append(meta);
  if(last)host.append(button(`Previous customer visit · ${date(last.finished_at)} →`,()=>openVisit(last)));
}
// Override the earlier compact drilldown with visible exact prompts, readable
// notes, and a screenshot gallery. Original evidence checks stay in Python.
renderReceivedOutputs=function(s){
  const host=$('received-output-body');host.replaceChildren();const detail=s.result_details;$('received-outputs').hidden=!detail;if(!detail)return;
  promptList(host,s);
  const texts=(detail.artifacts||[]).filter(a=>a.kind==='text');for(const item of texts){host.append(make('h3',item.label));const note=make('div');readableText(note,item.text);host.append(note);}
  outputGallery(host,detail.artifacts||[]);
  const files=(detail.artifacts||[]).filter(a=>!['image','text'].includes(a.kind));if(files.length){const more=make('details');more.append(make('summary','Original files and technical evidence'));const grid=make('div',undefined,'artifact-actions');files.forEach(a=>grid.append(link(a.label,a.url)));more.append(grid);host.append(more);}
};
const currentCase=(data.engineering_cases||[]).find(c=>c.id===data.current_case_id);
currentWork(currentCase);
engineeringFollowups(currentCase);
outcomeEvidence();
developerWork();
if(currentCase)engineeringCase(currentCase);else{
  const last=allSessions.at(-1);const p=panel('Latest customer request',last?date(last.started_at):'');
  if(last){promptList(p.body,last);p.body.append(make('p',last.accomplishment||last.stopping_reason,'readable-text'),button('Prompts & results →',()=>openVisit(last)));}
  else p.body.append(make('p','No customer observation has been recorded.','muted'));$('current-case').append(p.box);
}
const newest=allSessions.at(-1);if(newest){$('journey-select').value=newest.id;renderJourney();}
function freshness(){const age=Math.max(0,(Date.now()-new Date(data.generated_at))/1000);$('snapshot-age').textContent=age<60?'Snapshot less than a minute old':`Snapshot ${Math.floor(age/60)} min old`;$('snapshot-age').className=age>300?'freshness-old':'muted';}
freshness();setInterval(freshness,30000);
// Refresh the observed projection, never start or resume an engineering run.
const displayStateKey='wright-golden-hour-view:'+location.pathname;
function detailKey(node){return node.id||`${node.closest('.view')?.id}:${Array.from(node.querySelectorAll(':scope > summary')).map(n=>n.textContent).join('')}`;}
function saveDisplayState(){
  const view=document.querySelector('nav button.active')?.dataset.view||'current';
  const state={view,journey:$('journey-select').value,action:$('action-stage').value,diary:$('diary-stage').value,scroll:scrollY,
    details:[...document.querySelectorAll('main details[open]')].map(detailKey)};
  try{sessionStorage.setItem(displayStateKey,JSON.stringify(state));}catch{}
}
function restoreDisplayState(){
  let state;try{state=JSON.parse(sessionStorage.getItem(displayStateKey));sessionStorage.removeItem(displayStateKey);}catch{}
  if(!state)return;
  if(allSessions.some(s=>s.id===state.journey)){$('journey-select').value=state.journey;renderJourney();}
  if([...$('action-stage').options].some(o=>o.value===state.action)){$('action-stage').value=state.action;renderActions();}
  if([...$('diary-stage').options].some(o=>o.value===state.diary)){$('diary-stage').value=state.diary;renderDiary();}
  for(const node of document.querySelectorAll('main details'))node.open=(state.details||[]).includes(detailKey(node));
  if(['current','journey','overview','resources','evidence'].includes(state.view))switchView(state.view);
  requestAnimationFrame(()=>scrollTo(0,Number.isFinite(state.scroll)?state.scroll:0));
}
restoreDisplayState();
let pendingSnapshot=false,refreshInFlight=false,reloading=false;
function reloadPreservingView(){
  if(reloading)return;
  if(reader.open){pendingSnapshot=true;$('live-status').textContent='Update ready · close preview to apply';return;}
  reloading=true;saveDisplayState();location.reload();
}
async function checkSnapshot(){
  if(refreshInFlight||reloading||document.hidden||location.protocol==='file:')return;
  refreshInFlight=true;
  const controller=new AbortController();const deadline=setTimeout(()=>controller.abort(),10000);
  try{
    const response=await fetch(data.refresh_url||'dashboard-status.json',{cache:'no-store',credentials:'same-origin',signal:controller.signal});
    if(!response.ok)throw new Error('Snapshot unavailable');
    const next=await response.json();
    if(next.schema_version!==1||!Number.isFinite(Date.parse(next.generated_at)))throw new Error('Invalid snapshot');
    if(next.generated_at!==data.generated_at){pendingSnapshot=true;reloadPreservingView();}
    else{$('live-status').textContent='Auto-update · connected';$('live-status').classList.remove('freshness-old');}
  }catch{$('live-status').textContent='Updates disconnected · retrying';$('live-status').classList.add('freshness-old');}
  finally{clearTimeout(deadline);refreshInFlight=false;}
}
$('refresh').onclick=reloadPreservingView;
reader.addEventListener('close',()=>{if(pendingSnapshot)reloadPreservingView();});
if(location.protocol==='file:')$('live-status').textContent='Saved snapshot';
else{setInterval(checkSnapshot,15000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)checkSnapshot();});checkSnapshot();}
