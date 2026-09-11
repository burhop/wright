import { writeFileSync } from "node:fs";
import path from "node:path";

// Uses the existing capture harness: reports, screenshots, diagnostics and traces.
export function registerBlockAcceptance({add,getPage,tid,click,fill,capture,logAction,expect,args,root,stamp,mutations}) {
  const base = new URL(args.url).origin;
  const session = "api_1788293353_e8f8a9e8";
  const workspace = "85cbd6b3-e9d1-474d-add2-36f6e95a7b51";
  const suffix = args.suffix ?? "0906b";
  let page, basicFile, fileContext, imageContext, chain;
  const visible = () => page.locator('[data-testid="workflow-recovery-concept"]:visible');
  const json = async response => { const value = await response.json(); expect(response.ok(), JSON.stringify(value)).toBe(true); return value; };
  async function source() {
    const workflowPath = new URL(page.url()).searchParams.get("workflowPath");
    return await json(await page.request.get(base + "/api/workspace/workflow-sources", {params:{session_id:session,path:workflowPath}}));
  }
  async function open(name) {
    await click("workflow-file-open"); await click(`workflow-file-choice-${name}`);
    await expect(tid("workflow-recovery-filebar")).toContainText(path.basename(name));
  }
  async function create(name) {
    const filename = `workflows/${name.toLowerCase().replaceAll(" ", "-")}.workflow.wflow`;
    await click("workflow-file-open");
    const choice = tid(`workflow-file-choice-${filename}`);
    await expect(page.getByRole("dialog", {name:"Open workflow"})).toBeVisible();
    await expect(page.getByRole("dialog")).not.toContainText("Loading workspace workflows");
    if (await choice.count()) { await choice.click(); }
    else {
      await click("workflow-file-cancel"); await click("workflow-file-new");
      await fill("workflow-file-name",name); await click("workflow-file-create");
    }
    await expect(tid("workflow-recovery-filebar")).toContainText(name);
    return filename;
  }
  async function addBlock(group,template) {
    const before = await visible().locator(".recovery-block").evaluateAll(nodes=>nodes.map(n=>n.dataset.semanticId));
    await click("workflow-recovery-create-group-"+group);
    await click("workflow-recovery-create-template-"+template);
    const after = await visible().locator(".recovery-block").evaluateAll(nodes=>nodes.map(n=>n.dataset.semanticId));
    const id = after.find(id=>!before.includes(id)); expect(id).toBeTruthy(); return id;
  }
  async function saveReopen() {
    if (await tid("workflow-recovery-save").isEnabled()) await click("workflow-recovery-save");
    await expect(tid("workflow-recovery-save-status")).toHaveText("Saved in workspace");
    const before = await source();
    await click("workflow-recovery-view-code");
    await expect(tid("workflow-recovery-source-editor")).toHaveValue(before.source);
    await click("workflow-recovery-view-diagram");
    await page.reload(); await expect(tid("workflow-recovery-filebar")).toBeVisible({timeout:30000});
    expect((await source()).source).toBe(before.source);
    writeFileSync(path.join(root,path.basename(before.path)),before.source);
    return before;
  }
  async function run(id) {
    const responsePromise = page.waitForResponse(r=>r.url().endsWith("/workflow-sources/run")&&r.request().method()==="POST",{timeout:45000});
    await click("workflow-recovery-run-start");
    await expect(tid("workflow-recovery-run-cancel")).toBeVisible();
    await capture(id+"-running",[{testId:"workflow-recovery-run-cancel",label:"Cancel active work"},{testId:"workflow-recovery-native-run-mode",label:"Live progress"}]);
    const response = await responsePromise;
    const raw = await response.text();
    writeFileSync(path.join(root,id+"-events.ndjson"),raw);
    expect(response.ok(),raw).toBe(true);
    const events = raw.trim().split("\n").map(JSON.parse);
    expect(events.find(e=>e.kind==="failed"),raw.slice(-2000)).toBeUndefined();
    const result = events.find(e=>e.kind==="completed")?.result; expect(result,raw.slice(-2000)).toBeTruthy();
    await expect(tid("workflow-recovery-native-run-mode")).toContainText("Workflow completed");
    expect(await visible().locator('[data-run-state="running"]').count()).toBe(0);
    expect(await visible().locator('.recovery-state--succeeded').count()).toBe(0);
    writeFileSync(path.join(root,id+"-result.json"),JSON.stringify(result,null,2));
    const file = await json(await page.request.get(base+"/api/workspace/files/content",{params:{session_id:session,path:result.output_path}}));
    expect(file.content.length).toBeGreaterThan(0);
    mutations.push({action:"generated",path:result.output_path,via:"real workspace Run",at:new Date().toISOString()});
    return result;
  }
  async function reference(block,port) {
    await click("workflow-recovery-block-"+block);
    await click("workflow-recovery-prompt-connections");
    await tid("workflow-recovery-add-reference").selectOption(port);
  }
  function outputPort(id) { return `port.${id.slice(6)}-document-out`; }

  add("blocks-entry","Open Workflows from the workspace","Open the workspace and click Workflows in its activity bar.","The existing graphical editor opens within the workspace.",async()=>{
    page=getPage(); await page.goto(`${base}/workspace/${workspace}`);
    await click("activity-bar-workflows-btn");
    await expect(tid("workflow-recovery-canvas")).toBeVisible({timeout:30000});
    for (const size of await visible().locator(".recovery-create-group").evaluateAll(ns=>ns.map(n=>({w:n.getBoundingClientRect().width,h:n.getBoundingClientRect().height})))) {
      expect(size.w).toBe(32); expect(size.h).toBe(32);
    }
  },[{testId:"activity-bar-workflows-btn",label:"Workspace entry point"}]);
  add("blocks-prompt","Create and edit a standalone AI prompt","New workflow → Block prompt 0906 → AI prompt. Enter the prompt, choose HTML, drag the block, save and reopen.","Prompt edits and layout persist in the canonical workspace workflow.",async()=>{
    await create(`Block prompt ${suffix}`);
    const id=await addBlock("document","ai-prompt");
    await fill("workflow-recovery-block-instructions-"+id,"Write a very short HTML workshop brief. Include exactly this identifier BRACKET-42 and state that the requested flange length is 24 mm. These are supplied test requirements, not verified engineering advice.");
    await tid("workflow-recovery-response-format").selectOption("html");
    await fill("workflow-recovery-output-filename",`reports/block-prompt-${suffix}.html`);
    await click("workflow-recovery-inspector-close");
    const block=tid("workflow-recovery-block-"+id); const box=await block.boundingBox();
    await page.mouse.move(box.x+40,box.y+30);await page.mouse.down();await page.mouse.move(box.x+150,box.y+65,{steps:10});await page.mouse.up();
    await saveReopen();
  },[{testId:"workflow-recovery-canvas",label:"Editable graphical canvas"}]);
  add("blocks-prompt-run","Run and open the HTML output","Click Run, inspect progress and open the output from Run details.","A real model response is written and opens in the existing viewer without a false heartbeat error.",async()=>{
    const result=await run("blocks-prompt");basicFile=result.output_path;
    expect(result.steps[0].response).toContain("BRACKET-42");
    await visible().getByRole("button",{name:"Open "+basicFile,exact:true}).click();
    await expect(page.locator("iframe:visible")).toHaveCount(1);
    await expect(page.frameLocator("iframe:visible").locator("body")).toContainText("BRACKET-42");
    // The old erroneous heartbeat timeout appeared after a few seconds.
    await expect(async()=>{expect(await page.getByText("Viewer Unresponsive",{exact:true}).count()).toBe(0);}).toPass({timeout:5000});
    await capture("blocks-viewer");
    await click("activity-bar-workflows-btn");
  });
  add("blocks-file","Read a workspace file as context","New workflow → Block file context 0906. Select the generated HTML in a File block and connect it as AI reference material.","The actual document contents reach the AI; a reference is not substituted with its filename.",async()=>{
    fileContext=await create(`Block file context ${suffix}`);
    const input=await addBlock("input","file-input");
    await tid("workflow-recovery-input-select").selectOption(basicFile);
    expect(await visible().getByRole("tab",{name:"Settings",exact:true}).count()).toBe(0);
    const ai=await addBlock("document","ai-prompt");
    await fill("workflow-recovery-block-instructions-"+ai,"Extract the identifier and flange length from the attached brief. Return only a short sentence quoting those values.");
    await reference(ai,`port.${input.slice(6)}-file-out`);
    await saveReopen(); const result=await run("blocks-file");
    expect(result.steps[0].prompt).toContain("BRACKET-42");
    expect(result.steps[0].response).toContain("BRACKET-42");
    expect(result.steps[0].response).toContain("24");
  });
  add("blocks-image","Upload and select one image","New workflow → Block image context 0906. Add Image, upload the test image, then connect it as a reference to an AI prompt.","One image is uploaded into the workspace and its real bytes are supplied to the configured model.",async()=>{
    imageContext=await create(`Block image context ${suffix}`);
    const input=await addBlock("input","image-input");
    const png=await page.evaluate(()=>{const c=document.createElement("canvas");c.width=400;c.height=220;const x=c.getContext("2d");x.fillStyle="white";x.fillRect(0,0,400,220);x.fillStyle="red";x.beginPath();x.arc(100,110,60,0,Math.PI*2);x.fill();x.fillStyle="blue";x.fillRect(240,50,120,120);return c.toDataURL("image/png").split(",")[1];});
    await tid("workflow-recovery-input-upload").setInputFiles({name:`block-shapes-${suffix}.png`,mimeType:"image/png",buffer:Buffer.from(png,"base64")});
    await expect(tid("workflow-recovery-input-select")).not.toHaveValue("");
    await expect(visible().getByAltText(/Selected image/)).toBeVisible();
    const ai=await addBlock("document","ai-prompt");
    await fill("workflow-recovery-block-instructions-"+ai,"Describe the two shapes and their colors in the supplied image in one sentence. If you cannot see the image, say so.");
    await reference(ai,`port.${input.slice(6)}-images-out`);
    await saveReopen();const result=await run("blocks-image");
    expect(result.steps[0].response.toLowerCase()).toMatch(/red.*circle|circle.*red/);
    expect(result.steps[0].response.toLowerCase()).toMatch(/blue.*square|square.*blue/);
  });
  add("blocks-mcp-editor","Inspect the standalone MCP task","Open MCP task basics and select Find official Fusion guidance.","Task instructions, one server and expected result are editable directly without tool argument fields.",async()=>{
    await open("workflows/mcp-task-basics.workflow.wflow");
    await click("workflow-recovery-block-block.document-1");
    await expect(tid("workflow-recovery-task-server")).toHaveValue("autodesk-product-help-mcp");
    await expect(tid("workflow-recovery-task-server")).toBeEnabled();
    await expect(tid("workflow-recovery-task-result")).toBeVisible();
    expect(await visible().getByText("release_code",{exact:true}).count()).toBe(0);
  },[{testId:"workflow-recovery-task-server",label:"One selected MCP server"},{testId:"workflow-recovery-task-result",label:"Expected result"}]);
  add("blocks-mcp-chain","Compose instructions, an MCP task and an AI response","Create Instructions to MCP report 0906. Connect Text → MCP task prompt, then MCP response → AI reference. Save and reopen.","Independent blocks compose through canonical typed connections without argument JSON or intermediate files.",async()=>{
    chain=await create(`Instructions to MCP report ${suffix}`);
    const input=await addBlock("input","text-input");
    await fill("workflow-recovery-input-text-"+input,"First discover available Autodesk products, then search official Fusion help for sheet metal flange creation. Give two useful links and one sentence describing each. Do not create a CAD model.");
    const task=await addBlock("tool","mcp-task");
    await tid("workflow-recovery-prompt-source").selectOption("connection");
    await tid("workflow-recovery-prompt-from").selectOption(`port.${input.slice(6)}-text-out`);
    await tid("workflow-recovery-task-server").selectOption("autodesk-product-help-mcp");
    await fill("workflow-recovery-task-result","Two relevant links supported by actual documentation search results.");
    const report=await addBlock("document","ai-prompt");
    await fill("workflow-recovery-block-instructions-"+report,"Make a short HTML reading list from the supplied documentation results. Preserve the actual source URLs. Do not claim a CAD model was built.");
    await tid("workflow-recovery-response-format").selectOption("html");
    await fill("workflow-recovery-output-filename",`reports/mcp-reading-list-${suffix}.html`);
    await reference(report,outputPort(task));
    await saveReopen();
  });
  add("blocks-mcp-live","Run the composed MCP workflow","Click Run; inspect the selected tools and the downstream HTML output.","The AI makes multiple real calls on one server and the next AI block receives its actual response.",async()=>{
    if (args.only) { chain=`workflows/instructions-to-mcp-report-${suffix}.workflow.wflow`; await open(chain); }
    const result=await run("blocks-mcp-chain");
    expect(result.steps).toHaveLength(2);
    const task=result.steps[0];expect(task.execution_kind).toBe("mcp_task");
    expect(task.tool_calls.length).toBeGreaterThanOrEqual(2);
    expect(task.tool_calls.every(c=>c.tool.startsWith("autodesk-product-help-mcp__"))).toBe(true);
    expect(result.steps[1].prompt).toContain(task.response);
    expect(result.outputs).toHaveLength(1);
    expect(result.run_log_path).toMatch(/^runs\//);
    const log = await json(await page.request.get(base+"/api/workspace/files/content",{params:{session_id:session,path:result.run_log_path}}));
    const record=JSON.parse(log.content);expect(record.status).toBe("completed");
    expect(record.result.steps[0].tool_calls).toEqual(task.tool_calls);
    const details=tid("workflow-recovery-native-run-log"); if(await details.getAttribute("open")===null) await details.locator("summary").first().click();
    await expect(tid("workflow-recovery-open-run-record")).toBeVisible();
    await capture("blocks-durable-run-log",[{testId:"workflow-recovery-open-run-record",label:"Saved diagnostics survive reloads"}]);
    writeFileSync(path.join(root,"handoff.json"),JSON.stringify({workspace,session,base,basicFile,fileContext,imageContext,chain},null,2));
  });
  add("blocks-cancel","Cancel active work and retain its history","Open Block file context 0906b, click Run and then Cancel run while its block is active.","Cancellation clears active badges, writes a cancelled run record and creates no output file.",async()=>{
    await open(`workflows/block-file-context-${suffix}.workflow.wflow`);
    const list = async()=> (await json(await page.request.get(base+"/api/workspace/workflow-sources/input-files",{params:{session_id:session}}))).files;
    const before = new Set((await list()).map(f=>f.path));
    await click("workflow-recovery-run-start");
    await expect(visible().locator('[data-run-state="running"]')).toHaveCount(1,{timeout:15000});
    await capture("blocks-before-cancel",[{testId:"workflow-recovery-run-cancel",label:"Cancel active task"}]);
    await click("workflow-recovery-run-cancel");
    await expect(tid("workflow-recovery-native-run-mode")).toContainText("Workflow cancelled");
    await expect(visible().locator('[data-run-state="running"]')).toHaveCount(0);
    let added;
    await expect(async()=>{added=(await list()).filter(f=>!before.has(f.path));expect(added.some(f=>f.path.startsWith("runs/"))).toBe(true);}).toPass({timeout:15000});
    expect(added.every(f=>f.path.startsWith("runs/"))).toBe(true);
    const log=await json(await page.request.get(base+"/api/workspace/files/content",{params:{session_id:session,path:added.find(f=>f.path.startsWith("runs/")).path}}));
    expect(JSON.parse(log.content).status).toBe("cancelled");
    writeFileSync(path.join(root,"cancellation-log.json"),log.content);
  });

  add("blocks-palette","Choose a server for an AI task","Click MCP servers and inspect the available server blocks.","Only server tasks appear; individual tool calls are used within those tasks.",async()=>{
    await click("workflow-recovery-create-group-tool");
    await expect(visible().locator('[data-testid^="workflow-recovery-create-server-"]').first()).toBeVisible();
    expect(await tid("workflow-recovery-create-template-mcp-task").count()).toBe(0);
    expect(await tid("workflow-recovery-create-template-mcp-tool").count()).toBe(0);
    expect(await tid("workflow-recovery-direct-tools").count()).toBe(0);
    await expect(visible().locator('[data-testid^="workflow-recovery-create-tool-"]')).toHaveCount(0);
    await capture("blocks-server-tasks");await page.keyboard.press("Escape");
  });
  add("blocks-dashboard","Review the existing implementation dashboard","Open the existing dashboard on port 8765 and follow its current block evidence links.","The existing page distinguishes local implementation and verification from human acceptance and the CI/dev batch.",async()=>{
    await page.goto("http://127.0.0.1:8765/");
    await expect(page.getByRole("heading",{name:"Current block implementation evidence"})).toBeVisible({timeout:30000});
    await expect(page.getByRole("link",{name:"Final MCP execution and saved logs"})).toHaveAttribute("href",/metrics\/blocks/);
    await expect(page.getByText("Local implementation and verification are separate from human acceptance and CI/dev integration.")).toBeVisible();
  });

}
