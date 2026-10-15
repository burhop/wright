// Decoder/display proof only: real native client + shared viewer, controlled tool reply.
import {build} from 'vite';
import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {chromium,expect} from '@playwright/test';
const root=process.cwd();
const requireWeb=createRequire(resolve(root,'apps/web/package.json'));
const {default:react}=await import(requireWeb.resolve('@vitejs/plugin-react'));
const output=resolve(process.argv[2]);
mkdirSync(output,{recursive:false});
const file='artifacts/stevecad-demonstrations/qualification/native/06-inspect-coupon-1.png';
const bytes=readFileSync(file);
const hash=createHash('sha256').update(bytes).digest('hex');
const entry=`
import React from '${root}/node_modules/react/index.js';
import {createRoot} from '${root}/node_modules/react-dom/client.js';
import {RepresentationViewer} from '${root}/packages/ui_kit/src/representations.tsx';
import '${root}/packages/ui_kit/src/styles.css';
import {createNativePanelProcessClient} from '${root}/apps/web/src/prototypes/desktop-panel/native-process-client.ts';
const root=createRoot(document.getElementById('viewer'));
window.calls=[];
async function show(malformed=false){
 const raw=malformed?btoa('invalid bitmap'):${JSON.stringify(bytes.toString('base64'))};
 const {client}=createNativePanelProcessClient({process:{workspace_id:'fixture',source_path:'workflows/fixture.wflow',source_digest:'a'.repeat(64)},sessionId:'fixture-session',workspaceName:'Controlled image proof',call:async(name,request)=>{
 window.calls.push({name,request});
 if(name!=='wright_process_ui_read'||request.operation!=='representation')throw Error('Read-only fixture');
 return {content:[],structuredContent:{ok:true,document:{bytes_base64:raw,sha256:${JSON.stringify(hash)},media_type:'image/png',size_bytes:atob(raw).length}}};
 }});
 const blob=await client.getRepresentation({artifact_ref:'retained-capture.png',sha256:${JSON.stringify(hash)}},{runId:'fixture-run'});
 root.render(React.createElement(RepresentationViewer,{blob,title:'Retained historical CAD capture',sourceSha256:${JSON.stringify(hash)}}));
}
window.showMalformed=()=>show(true);
show();`;
const result=await build({configFile:false,root:resolve(root,'apps/web'),plugins:[react(),{name:'bounded-image-fixture',resolveId:id=>id==='image-fixture'?'\0image-fixture':null,load:id=>id==='\0image-fixture'?entry:null}],build:{write:false,minify:true,rollupOptions:{input:'image-fixture',output:{format:'iife',codeSplitting:false}}}});
const assets=result.output;
const script=assets.filter(x=>x.type==='chunk').map(x=>x.code).join('\n');
const css=assets.filter(x=>x.type==='asset'&&x.fileName.endsWith('.css')).map(x=>x.source).join('\n');
const html=`<!doctype html><html><meta charset="utf-8"><style>${css}</style><body style="background:#202020;color:#eee;padding:20px"><h2>Historical CAD capture — display test</h2><p>Controlled transport fixture; no new engineering run or desktop acceptance.</p><div id="viewer"></div><script>${script.replaceAll('</script','<\\/script')}</script></body></html>`;
const server=createServer((req,res)=>{res.writeHead(200,{'content-type':'text/html;charset=utf-8'});res.end(html);});
await new Promise(done=>server.listen(0,'127.0.0.1',done));
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:900,height:700}});
const report={boundary:'real browser decoder, native client, shared viewer; controlled tool reply; no backend or native desktop proof',source:file,sha256:hash,bytes:bytes.length,passed:[]};
try{
 await page.goto(`http://127.0.0.1:${server.address().port}`);
 const img=page.getByRole('img',{name:'Retained historical CAD capture'});
 await expect(img).toBeVisible();
 await expect.poll(()=>img.evaluate(el=>el.complete&&el.naturalWidth>0&&el.naturalHeight>0)).toBe(true);
 report.dimensions=await img.evaluate(el=>({width:el.naturalWidth,height:el.naturalHeight}));
 await page.screenshot({path:resolve(output,'historical-image.png')});
 report.passed.push('actual historical PNG decodes through native client and shared viewer');
 await page.evaluate(()=>window.showMalformed());
 await expect(page.getByText('A bitmap preview is unavailable.',{exact:true})).toBeVisible();
 report.passed.push('malformed bitmap reaches explicit shared fallback without retry');
 report.calls=await page.evaluate(()=>window.calls);
 expect(report.calls).toHaveLength(2);
 expect(report.calls.every(x=>x.name==='wright_process_ui_read'&&x.request.operation==='representation')).toBe(true);
 writeFileSync(resolve(output,'report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({output,passed:report.passed}));
}catch(error){report.error=String(error);writeFileSync(resolve(output,'failure.json'),JSON.stringify(report,null,2));throw error;}
finally{await browser.close();await new Promise(done=>server.close(done));}
