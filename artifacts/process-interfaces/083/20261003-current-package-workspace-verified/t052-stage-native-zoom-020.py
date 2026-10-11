"""Measure real Chromium tab zoom via official extension API; no DOM zoom/emulation."""
from pathlib import Path

base = Path('D:/repos/wright/.local-run/process-interfaces-083')
target = base / 't052-native-zoom-020.mjs'
assert not target.exists()
text = (base / 't052-current-workspace-019.mjs').read_text(encoding='utf-8')
text = text.replace('-installed-019/workspace-walkthrough', '-zoom-installed-020/workspace-walkthrough')
text = text.replace("title:'Compact '+kind+' working interface and workspace navigation'", "title:'Native 200% browser zoom: '+kind+' workspace interfaces'")
old = "const browser = await chromium.launch({headless:true});\nconst context = await browser.newContext({viewport:{width:1440,height:1000}});"
assert old in text
text = text.replace(old, """const zoomExtension=path.join(privateRoot,'zoom-extension-020');
const zoomProfile=path.join(privateRoot,'zoom-browser-profile-020');
if(existsSync(zoomExtension)||existsSync(zoomProfile))throw new Error('Fresh private extension/profile required');
mkdirSync(zoomExtension);
writeFileSync(path.join(zoomExtension,'manifest.json'),JSON.stringify({manifest_version:3,name:'Isolated Wright browser zoom measurement',version:'1.0',permissions:['tabs'],background:{service_worker:'background.js'}}));
writeFileSync(path.join(zoomExtension,'background.js'),'chrome.runtime.onInstalled.addListener(()=>{});');
const context=await chromium.launchPersistentContext(zoomProfile,{channel:'chromium',headless:true,viewport:{width:1440,height:1000},args:[`--disable-extensions-except=${zoomExtension}`,`--load-extension=${zoomExtension}`]});
const zoomWorker=context.serviceWorkers()[0]??await context.waitForEvent('serviceworker');
const browser={close:()=>context.close()};""")
needle = "  expect(authoringOrExecutionPosts).toEqual([]);"
assert text.count(needle) == 1
text = text.replace(needle, """  await page.setViewportSize({width:1440,height:1000});
  const beforeZoom=await capture('S11-before','Read-only preview before native browser zoom');
  const beforeMetrics=await page.evaluate(()=>({innerWidth,devicePixelRatio,pageScale:visualViewport.scale}));
  const zoom=await zoomWorker.evaluate(async ({url,factor})=>{
    const candidates=(await chrome.tabs.query({})).filter(t=>t.url===url);
    if(candidates.length!==1)throw new Error('Zoom must identify exactly the owned proof tab');
    await chrome.tabs.setZoom(candidates[0].id,factor);
    return {factor:await chrome.tabs.getZoom(candidates[0].id),settings:await chrome.tabs.getZoomSettings(candidates[0].id)};
  },{url:page.url(),factor:2});
  expect(zoom.factor).toBe(2);
  await expect.poll(()=>page.evaluate(()=>innerWidth)).toBe(beforeMetrics.innerWidth/2);
  const afterMetrics=await page.evaluate(()=>({innerWidth,devicePixelRatio,pageScale:visualViewport.scale}));
  expect(afterMetrics.pageScale).toBe(1);
  expect(afterMetrics.devicePixelRatio).toBe(beforeMetrics.devicePixelRatio*2);
  await expect(previewFrame.getByText('Preview - process controls are read-only.',{exact:true})).toBeVisible();
  expect((await previewFrame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await record({id:'S11',state:'pass',label:'Actual 200% browser zoom on read-only preview',summary:'The browser reports tab zoom two while its layout viewport halves and pinch scale remains one.',purpose:'Qualify native browser zoom rather than page-scale emulation.',action:'Set browser Zoom to 200%.',controls:['Browser Zoom','Preview tab','Open workflow'],expected:'Browser zoom 2, CSS viewport 720px, pinch scale 1, exact read-only preview results.',actual:`Browser zoom ${zoom.factor}; viewport ${afterMetrics.innerWidth}px; pixel ratio ${afterMetrics.devicePixelRatio}; page scale ${afterMetrics.pageScale}; ${ids.length} exact results.`,beforeRaw:beforeZoom.raw,beforeAnnotated:beforeZoom.annotated,...await capture('S11','Native 200% preview')});

  await page.goto(savedUrl.href);
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:90000});
  await assertParity();
  await files.click();
  await expect(page.getByRole('button',{name:'Close workspace navigation',exact:true})).toBeFocused();
  await page.keyboard.press('Escape');await expect(files).toBeFocused();
  await record({id:'S12',state:'pass',label:'Saved working interface at native 200% zoom',summary:'The same saved interface and keyboard navigation remain available at browser zoom two.',purpose:'Verify actual result and focus retention under browser zoom.',action:'Open the saved working interface; open Files and press Escape.',controls:['Saved interface tab','Workspace Files','Close workspace navigation'],expected:'Exact saved results; Files restores keyboard focus.',actual:`All ${ids.length} exact results remain available; Files opens and Escape restores focus.`,...await capture('S12','Native 200% saved working view')});

  await page.getByRole('button',{name:'Use common working view',exact:true}).click();
  const zoomCommon=page.locator('[data-testid="common-process-view"]:visible');
  await expect(zoomCommon.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await zoomCommon.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  const zoomCommonSize=await page.locator('[data-testid="workspace-process-view"]:visible').evaluate(e=>({width:e.clientWidth,scrollWidth:e.scrollWidth}));
  expect(zoomCommonSize.scrollWidth).toBeLessThanOrEqual(zoomCommonSize.width+1);
  const zoomAxe=await new AxeBuilder({page}).include('[data-testid="workspace-process-view"]:visible').withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
  writeFileSync(path.join(root,'axe-common-native-zoom.json'),JSON.stringify(zoomAxe,null,2));
  expect(zoomAxe.violations).toEqual([]);
  await record({id:'S13',state:'pass',label:'Common working interface at native 200% zoom',summary:'The common fallback preserves exact results and wraps its content within the available workspace.',purpose:'Verify general working UI at native browser zoom and scoped accessibility.',action:'Click Use common working view.',controls:['Use common working view','Open workflow'],expected:'Exact results, no outer overflow, no detected WCAG A/AA violations.',actual:`${ids.length} exact results; ${zoomCommonSize.width}px client and ${zoomCommonSize.scrollWidth}px scroll width; zero scoped automated violations.`,...await capture('S13','Native 200% common view')});

  await page.locator('[data-testid="workspace-process-view"]:visible').getByTestId('process-open-definition').click();
  await expect(viewSelect).toBeVisible({timeout:45000});
  await viewSelect.selectOption('code');
  await expect(page.getByTestId('workflow-recovery-source-editor')).toHaveValue(acceptedSource);
  await viewSelect.selectOption('diagram');
  await expect(page.getByRole('button',{name:'Use saved process',exact:true})).toBeVisible();
  const afterZoom=await zoomWorker.evaluate(async url=>{const tab=(await chrome.tabs.query({})).find(t=>t.url===url);return chrome.tabs.getZoom(tab.id);},page.url());
  expect(afterZoom).toBe(2);
  await record({id:'S14',state:'pass',label:'Editor and source at native 200% zoom',summary:'Open workflow returns to the unchanged accepted source and diagram within the zoomed workspace.',purpose:'Preserve the complementary editor experience at real browser zoom.',action:'Click Open workflow, select Source, then Diagram.',controls:['Open workflow','Source','Diagram','Use saved process'],expected:'Same accepted source; browser zoom still 2.',actual:'Exact accepted source and existing diagram remain available; browser tab zoom remains 200%.',...await capture('S14','Native 200% editor')});
  writeFileSync(path.join(privateRoot,'native-zoom-'+kind+'-020.json'),JSON.stringify({method:'chrome.tabs.setZoom/getZoom via isolated test-only extension; no application script, CSS zoom or CDP page-scale emulation',beforeMetrics,afterMetrics,zoom,afterZoom,zoomCommonSize,result_ids:ids,run_id:receipt.run_id,model_or_process_or_review_requests:authoringOrExecutionPosts},null,2));
  expect(authoringOrExecutionPosts).toEqual([]);""")
text = text.replace('compact-installed-007', 'native-zoom-installed-020')
target.write_text(text, encoding='utf-8')
print('Prepared native tab-zoom020 walkthrough for both isolated installed006 copies.')
