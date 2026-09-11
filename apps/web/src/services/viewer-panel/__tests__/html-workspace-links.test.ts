import { afterEach, expect, it, vi } from "vitest";
import { workspaceService } from "../../workspace-service";
import { IframeProvider } from "../providers/iframe-provider";
import { workspaceHtmlLinkPath } from "../providers/workspace-html-links";
import { PanelHostImpl } from "../panel-host";
import type { CancellationToken } from "../types";

const token: CancellationToken = {isCancellationRequested:false, onCancellationRequested:()=>({dispose(){}})};
const cleanup: (()=>void)[] = [];
afterEach(()=>{ for(const dispose of cleanup.splice(0)) dispose(); vi.restoreAllMocks(); });

it.each([
  ['project-inventory-fixtures/exceptions/package/assembly.csv', '/project-inventory-fixtures/exceptions/package/assembly.csv'],
  ['assembly.csv', '/assembly.csv'],
  ['./assembly.csv', '/reports/assembly.csv'],
  ['../parts/assembly.csv', '/parts/assembly.csv'],
  ['/parts/design%20spec.md', '/parts/design spec.md'],
  ['parts/assembly.csv#part1', '/parts/assembly.csv'],
])('resolves workspace file %s', (href, expected)=>{
  expect(workspaceHtmlLinkPath('reports/review.html',href)).toBe(expected);
});
it.each(['../../private.txt','/../private.txt','%2e%2e/%2e%2e/private.txt','%252e%252e/private.txt',
  'file:///C:/secret','javascript:alert(1)','data:text/html,test','blob:abc','about:blank','//other.test/x',
  'https://other.test/x','C:\\secret.txt','foo\\bar.txt','.wright/secret','.git/config','x/CON.txt','x\u0000.txt','file.txt?session_id=other'])
('refuses unsafe or non-workspace path %s',href=>expect(workspaceHtmlLinkPath('reports/review.html',href)).toBeNull());

async function fixture(html='<a href="project-inventory-fixtures/exceptions/package/assembly.csv">Assembly</a>') {
  vi.spyOn(workspaceService,'getFileContentText').mockResolvedValue(html);
  const container=document.createElement('div'); document.body.append(container);
  const host=new PanelHostImpl('html','Report',container);
  const provider=new IframeProvider();
  const model=await provider.openDocument({id:'reports/review.html',uri:'reports/review.html',name:'review.html',extension:'html',mimeType:'text/html'}, {sessionId:'owned-session'});
  const events:unknown[]=[];
  container.addEventListener('viewer-message',event=>events.push((event as CustomEvent).detail));
  cleanup.push(()=>{host.dispose();provider.disposeDocument(model);container.remove();});
  await provider.resolveViewer(model,host,'preview',token);
  const iframe=()=>container.querySelector('iframe')!;
  const preview=()=>new DOMParser().parseFromString(iframe().srcdoc,'text/html');
  const send=(id:string,source:MessageEventSource|null=iframe().contentWindow,extra={})=>window.dispatchEvent(new MessageEvent('message',{
    source,data:{type:'wright-open-workspace-file',id,...extra},
  }));
  return {container,host,provider,model,events,iframe,preview,send};
}

it('uses only mapped file identity and pinned session from the current frame',async()=>{
  const f=await fixture();
  const id=f.preview().querySelector('a')!.getAttribute('data-wright-file-link')!;
  f.send(id,window); f.send('unknown');
  expect(f.events).toEqual([]);
  f.send(id,f.iframe().contentWindow,{path:'/secret',sessionId:'attacker-session'});
  expect(f.events).toEqual([{type:'open-workspace-file',path:'/project-inventory-fixtures/exceptions/package/assembly.csv',sessionId:'owned-session'}]);
  expect(f.iframe().sandbox?.value ?? f.iframe().getAttribute('sandbox')).toBe('allow-scripts');
  expect(f.iframe().srcdoc).not.toContain('owned-session');
  expect(workspaceService.getFileContentText).toHaveBeenCalledTimes(1);
});

it('preserves local anchors and authored external base semantics while blocking prohibited schemes',async()=>{
  const f=await fixture('<a href="#source">Source</a><h2 id="source">Sources</h2><a href="file:///secret">Bad</a><a href="https://example.org/info">External</a>');
  const p=f.preview();
  expect(p.querySelector('a')!.href).toBe('about:srcdoc#source');
  expect(p.querySelector('a')!.hasAttribute('data-wright-file-link')).toBe(false);
  expect(p.querySelector('a[href^="file:"]')!.hasAttribute('data-wright-blocked-link')).toBe(true);
  expect(p.querySelector('a[href^="https:"]')!.hasAttribute('data-wright-file-link')).toBe(false);
  vi.mocked(workspaceService.getFileContentText).mockResolvedValue('<base href="https://example.org/manual/"><a href="chapter.html">Chapter</a>');
  await f.provider.resolveViewer(f.model,f.host,'preview',token);
  expect(f.preview().querySelector('a')!.href).toBe('https://example.org/manual/chapter.html');
  expect(f.preview().querySelector('a')!.hasAttribute('data-wright-file-link')).toBe(false);
});

it('invalidates old render IDs and removes subscriptions when the host or document closes',async()=>{
  const f=await fixture();
  const oldFrame=f.iframe().contentWindow;
  const oldId=f.preview().querySelector('a')!.getAttribute('data-wright-file-link')!;
  await f.provider.resolveViewer(f.model,f.host,'preview',token);
  f.send(oldId,oldFrame); f.send(oldId);
  expect(f.events).toEqual([]);
  const newId=f.preview().querySelector('a')!.getAttribute('data-wright-file-link')!;
  f.provider.disposeDocument(f.model);
  f.send(newId);
  expect(f.events).toEqual([]);
  await f.provider.resolveViewer(f.model,f.host,'preview',token);
  const lastId=f.preview().querySelector('a')!.getAttribute('data-wright-file-link')!;
  f.host.dispose(); f.send(lastId);
  expect(f.events).toEqual([]);
});

it('does not mount a response arriving after host disposal',async()=>{
  const f=await fixture();
  let complete!:(html:string)=>void;
  vi.mocked(workspaceService.getFileContentText).mockReturnValue(new Promise(resolve=>{complete=resolve;}));
  const pending=f.provider.resolveViewer(f.model,f.host,'preview',token);
  f.host.dispose(); f.container.replaceChildren(); complete('<h1>Stale workspace</h1>');
  await pending;
  expect(f.container.childElementCount).toBe(0);
});

it('keeps a restored report link active when an older host fetch finishes afterward',async()=>{
  const f=await fixture();
  let finishOld!:(html:string)=>void;
  vi.mocked(workspaceService.getFileContentText).mockReturnValueOnce(new Promise(resolve=>{finishOld=resolve;}));
  const oldLoad=f.provider.resolveViewer(f.model,f.host,'preview',token);
  f.host.dispose();
  const restored=new PanelHostImpl('restored','Report',f.container);
  cleanup.push(()=>restored.dispose());
  await f.provider.resolveViewer(f.model,restored,'preview',token);
  const restoredFrame=f.iframe();
  const id=f.preview().querySelector('a')!.getAttribute('data-wright-file-link')!;
  finishOld('<a href="wrong-workspace-file.txt">Old response</a>');
  await oldLoad;
  expect(f.iframe()).toBe(restoredFrame);
  f.send(id);
  expect(f.events).toEqual([{type:'open-workspace-file',path:'/project-inventory-fixtures/exceptions/package/assembly.csv',sessionId:'owned-session'}]);
});
