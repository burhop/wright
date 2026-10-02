import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t052-wheel-workspace-controls-008');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-wheel/20261002T154100Z-wheel-workspace-controls');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Workspace process controls at desktop and narrow widths',summary:'Saved actual-model interface and existing waiting run; no generation, start or review response.',overall:'pending',updated:new Date().toISOString(),manualSteps:[{label:'Workspace',instruction:'Open the proof workspace and click Workflows.'},{label:'Saved interface',instruction:'Open the saved wheel interface link attached to the existing run.'},{label:'Resize',instruction:'Resize to desktop, tablet and narrow widths; inspect navigation controls and Tab focus.'}],steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} Â· ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Heat workspace entry walkthrough\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.\n');
publish();
writeFileSync(path.join(root,'playwright','workspace-entry.mjs'),readFileSync(new URL(import.meta.url)));
const browser = await chromium.launch({headless:true});
const context = await browser.newContext({viewport:{width:1440,height:1000}});
await context.addCookies([{name:'wright_session',value:proof.browser_cookie,url:proof.frontend_url+'/api',httpOnly:true,sameSite:'Strict'}]);
await context.tracing.start({screenshots:true,snapshots:true,sources:true});
const page = await context.newPage();
const diagnostics={console:[],pageErrors:[],failedResponses:[]};
page.on('console',m=>{if(m.type()==='error') diagnostics.console.push(m.text().slice(0,2000));});
page.on('pageerror',e=>diagnostics.pageErrors.push(e.message));
page.on('response',r=>{if(r.status()>=400) diagnostics.failedResponses.push({path:new URL(r.url()).pathname,status:r.status()});});
const cleanUrl = () => {const u=new URL(page.url());u.hash='';return u.href;};
async function capture(id,label) {
  const raw=`screenshots/raw/${id}.png`, annotated=`screenshots/annotated/${id}.png`;
  await page.screenshot({path:path.join(root,raw),fullPage:true});
  await page.evaluate(()=>{
    const layer=document.createElement('div');layer.id='wright-walkthrough-overlays';layer.style='position:fixed;inset:0;pointer-events:none;z-index:2147483647';
    let index=0;const labels=[];
    for(const control of document.querySelectorAll('button,[role="tab"],input,textarea,select')){
      const r=control.getBoundingClientRect();if(r.width<2||r.height<2||r.top<0||r.top>innerHeight)continue;
      const title=(control.getAttribute('aria-label')||control.textContent||control.getAttribute('placeholder')||'').trim().slice(0,70);if(!title)continue;
      index++;const tag=document.createElement('span');tag.textContent=String(index);tag.style=`position:absolute;left:${r.left}px;top:${r.top}px;background:#fbcc42;color:#111;border-radius:4px;padding:1px 4px;font:13px system-ui`;layer.appendChild(tag);labels.push(index+': '+title);
    }
    const legend=document.createElement('div');legend.textContent=labels.join(' | ');legend.style='position:absolute;left:8px;bottom:8px;right:8px;background:#111e;color:#fff;padding:8px;font:12px system-ui';layer.appendChild(legend);document.body.appendChild(layer);
  });
  await page.screenshot({path:path.join(root,annotated),fullPage:true});
  await page.locator('#wright-walkthrough-overlays').evaluate(e=>e.remove());
  return {raw,annotated};
}
async function record(step){status.steps.push(step);publish();appendFileSync(path.join(root,'progress.md'),`\n## ${new Date().toISOString()} UTC â€” ${step.label}\n\nURL: ${cleanUrl()}\nAction: ${step.action}\nControls: ${step.controls.join(', ')}\nExpected: ${step.expected}\nActual: ${step.actual}\nStatus: ${step.state}\nScreenshots: ${step.raw??''}; ${step.annotated??''}\n`);}
try {
  await page.goto(proof.frontend_url+'/workspace/'+proof.workspace_id);
  await expect(page.getByRole('button',{name:'Workflows',exact:true})).toBeVisible({timeout:60000});
  await record({id:'S01',state:'pass',label:'Workspace entry',summary:'Normal workspace entry is available.',purpose:'Preserve existing authoring entry.',action:'Open proof workspace.',controls:['Workflows'],expected:'Workflows visible.',actual:'Workflows visible.',...await capture('S01','Workspace')});
  await page.getByRole('button',{name:'Workflows',exact:true}).click();
  await expect(page.getByTestId('workflow-file-menu')).toBeVisible({timeout:60000});
  await record({id:'S02',state:'pass',label:'Existing editor',summary:'The established diagram and file controls remain available.',purpose:'Check the actual workspace authoring entry.',action:'Click Workflows.',controls:['Workflow files'],expected:'Editor file controls visible.',actual:'Editor file controls visible.',...await capture('S02','Editor')});
  const saved=JSON.parse(readFileSync(path.join(privateRoot,'wheel-ui-saved-reuse-dom.json'),'utf8'));
  await page.goto(saved.url);
  const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
  await expect(frame.getByRole('heading',{name:'Review the next action',exact:true})).toBeVisible({timeout:60000});
  const measurements=[];
  for(const [id,width] of [['S03',1440],['S04',1024],['S05',480]]) {
    await page.setViewportSize({width,height:1000});
    const control=page.getByTestId('process-open-definition');
    await expect(control).toBeVisible();
    const metrics=await page.getByTestId('workspace-process-view').evaluate(root=>({width:root.clientWidth,scrollWidth:root.scrollWidth,buttons:[...root.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().width>0).map(b=>({label:b.textContent.trim(),height:b.getBoundingClientRect().height,border:getComputedStyle(b).borderTopWidth,font:getComputedStyle(b).fontFamily}))}));
    expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.width+1);
    expect(metrics.buttons.filter(b=>['Open workflow','Focus interface','Close interface view'].includes(b.label)).every(b=>b.height>=44&&b.border==='1px')).toBe(true);
    await control.focus();await page.keyboard.press('Tab');
    const focused=await page.evaluate(()=>({label:document.activeElement.textContent.trim(),outline:getComputedStyle(document.activeElement).outlineWidth}));
    expect(focused.label).toBe('Create or choose interface');expect(focused.outline).toBe('3px');
    measurements.push({width,metrics,focused});
    await record({id,state:'pass',label:'Controls at '+width+' pixels',summary:'Navigation and embedded-view controls remain styled, reachable and keyboard focusable.',purpose:'Check actual served responsive controls.',action:'Resize and press Tab from Open workflow.',controls:['Open workflow','Create or choose interface','Focus interface','Close interface view'],expected:'44px controls, no horizontal overflow, visible Tab focus.',actual:'Styled controls and 3px focus ring verified; no outer horizontal overflow.',...await capture(id,'Controls')});
  }
  writeFileSync(path.join(privateRoot,'measurements.json'),JSON.stringify(measurements,null,2));
  status.overall='pass';
} catch(error){status.overall='blocked';await record({id:'STOP',state:'blocked',label:'Controls stopped',summary:'First unexpected result retained.',purpose:'Preserve the actual failure.',action:'Stop at first unexpected state.',controls:['Workspace process controls'],expected:'Responsive styled controls.',actual:error.message,...await capture('STOP','Stop')});}
finally {publish();writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));await context.tracing.stop({path:path.join(privateRoot,'trace.zip')});await browser.close();console.log(JSON.stringify({overall:status.overall,steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));}
