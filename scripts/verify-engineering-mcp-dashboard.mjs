#!/usr/bin/env node

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { chromium } from "playwright";

const option=(name,fallback)=>{const i=process.argv.indexOf(name);return i===-1?fallback:process.argv[i+1]};
const baseUrl=option("--base-url","http://127.0.0.1:18765").replace(/\/$/,"");
const outputDir=path.resolve(option("--output-dir","artifacts/engineering-integration-status"));
await mkdir(outputDir,{recursive:true});
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:900}});
const diagnostics={console_errors:[],page_errors:[],failed_responses:[]};
page.on("console",m=>{if(m.type()==="error")diagnostics.console_errors.push(m.text())});
page.on("pageerror",e=>diagnostics.page_errors.push(e.message));
page.on("response",r=>{if(r.status()>=400)diagnostics.failed_responses.push({status:r.status(),url:r.url()})});

const screenshot=async(name)=>{const target=path.join(outputDir,name);await page.screenshot({path:target});return name};
try{
  await page.goto(`${baseUrl}/index.html`,{waitUntil:"networkidle"});
  await page.getByTestId("engineering-integration-dashboard").waitFor();
  const [statusResponse,historyResponse]=await Promise.all([page.request.get(`${baseUrl}/status.json`),page.request.get(`${baseUrl}/history.json`)]);
  if(!statusResponse.ok()||!historyResponse.ok())throw new Error("Status assets are unavailable");
  const status=await statusResponse.json(),history=await historyResponse.json();
  const ids=status.records.map(r=>r.server_id),unique=new Set(ids);
  if(ids.length!==status.total||unique.size!==status.total)throw new Error("Membership is not unique and complete");
  const categories=["works","preview","requires_login","in_progress","abandoned","vendor_blocked"];
  if(JSON.stringify(status.category_key.map(x=>x.id))!==JSON.stringify(categories))throw new Error("Category order changed");
  const derived=Object.fromEntries(categories.map(c=>[c,status.records.filter(r=>r.portfolio_category===c).length]));
  if(JSON.stringify(derived)!==JSON.stringify(status.category_counts))throw new Error("Category counts do not derive from records");
  if(Object.values(derived).reduce((a,b)=>a+b,0)!==status.total)throw new Error("Categories do not reconcile to total");
  if(status.green.count!==derived.works+derived.preview+derived.requires_login)throw new Error("Green total is incorrect");
  if(status.fully_qualified_count!==derived.works)throw new Error("Works count is incorrect");
  if(await page.getByTestId("status-tiles").locator("button").count()!==6)throw new Error("Expected six primary tiles");

  const shots=[];
  shots.push(await screenshot("integration-status-overview.png"));
  for(const category of categories){
    const tile=page.getByTestId(`status-tile-${category}`);
    const exactCount=await tile.locator(".tile-value").innerText();
    if(exactCount!==String(derived[category]))throw new Error(`Incorrect exact tile count for ${category}`);
    await tile.click();
    if(new URL(page.url()).searchParams.get("category")!==category)throw new Error(`Category ${category} is not shareable`);
    const rendered=await page.locator("details.record").count();
    if(rendered!==derived[category])throw new Error(`Category ${category} rendered ${rendered}, expected ${derived[category]}`);
    if(category==="vendor_blocked"&&!(await page.locator("#empty").innerText()).includes("currently has no integrations"))throw new Error("Zero vendor state is not informative");
  }
  await page.getByTestId("status-tile-abandoned").click();
  shots.push(await screenshot("integration-status-abandoned.png"));
  await page.getByTestId("status-tile-requires_login").click();
  const loginRecord=page.locator("details.record").first();await loginRecord.locator("summary").click();
  shots.push(await screenshot("integration-status-requires-login.png"));
  await page.getByTestId("status-tile-vendor_blocked").click();
  shots.push(await screenshot("integration-status-vendor-empty.png"));

  await page.getByTestId("status-tile-works").click();
  await page.getByTestId("status-tile-abandoned").click();
  await page.goBack();
  if(await page.locator("details.record").count()!==derived.works)throw new Error("Back navigation did not restore the previous category");
  await page.reload({waitUntil:"networkidle"});
  if(await page.locator("details.record").count()!==derived.works)throw new Error("Reload did not preserve category");
  await page.locator("#all").click();
  await page.getByLabel("Search integrations").fill("kernelcad-mcp");
  if(await page.locator("details.record").count()!==1)throw new Error("Search did not find exact integration");
  const kernel=page.getByTestId("integration-kernelcad-mcp");await kernel.locator("summary").click();
  if(!(await kernel.innerText()).includes("mutable GitHub runtime dependency"))throw new Error("Reviewed kernelCAD reason is missing");

  const corrected=new Set(history.snapshots.map(item=>item.corrects).filter(Boolean));
  const effectiveHistory=history.snapshots.filter(item=>!corrected.has(item.snapshot_id));
  const historyRows=page.locator("#history-rows tr");
  if(await historyRows.count()!==effectiveHistory.length)throw new Error("History table differs from effective JSON observations");
  if(effectiveHistory.length&&!(await page.locator("#history-note").innerText()).includes(effectiveHistory.length===1?"History collection started":`${effectiveHistory.length}`))throw new Error("History state is unclear");
  await page.locator("#chart").scrollIntoViewIfNeeded();
  shots.push(await screenshot("integration-status-history.png"));

  await page.setViewportSize({width:390,height:844});
  await page.goto(`${baseUrl}/index.html?category=in_progress`,{waitUntil:"networkidle"});
  if(await page.locator("details.record").count()!==derived.in_progress)throw new Error("Narrow deep link failed");
  const columns=await page.locator("#tiles").evaluate(e=>getComputedStyle(e).gridTemplateColumns.split(" ").length);
  if(columns!==2)throw new Error("Tiles do not wrap to two columns on narrow screens");

  const result={observed_at:new Date().toISOString(),dashboard_url:`${baseUrl}/index.html`,status:"passed",audience:status.audience,snapshot_id:status.snapshot_id,total:status.total,category_counts:status.category_counts,green:status.green,history_points:history.snapshots.length,...diagnostics,screenshots:shots};
  if(diagnostics.console_errors.length||diagnostics.page_errors.length||diagnostics.failed_responses.length)result.status="failed";
  await writeFile(path.join(outputDir,"served-dashboard-verification.json"),`${JSON.stringify(result,null,2)}\n`,"utf8");
  if(result.status!=="passed")throw new Error(`Browser diagnostics failed: ${JSON.stringify(diagnostics)}`);
  console.log(JSON.stringify(result));
}finally{await browser.close()}
