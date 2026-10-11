/** Optional evidence writer for controlled, served process UI journeys. */
import {mkdirSync, appendFileSync, writeFileSync, copyFileSync, existsSync} from "node:fs";
import path from "node:path";
import type {Page, TestInfo} from "@playwright/test";

interface Step {
  id: string; label: string; purpose: string; action: string; controls: string[];
  expected: string; actual: string;
}
const escape = (text: string) => text.replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]!);

export function processWalkthrough(page: Page, testInfo: TestInfo) {
  const root = process.env.WRIGHT_PROCESS_WALKTHROUGH_ROOT || testInfo.outputPath("walkthrough");
  if (existsSync(path.join(root, "status.json"))) throw new Error("Preserve the previous walkthrough; use a fresh root");
  for (const dir of ["playwright", "screenshots/raw", "screenshots/annotated", "trace"])
    mkdirSync(path.join(root, dir), {recursive: true});
  copyFileSync(testInfo.file, path.join(root, "playwright", "process-common-view.spec.ts"));
  for (const file of ["process-common-view.ts", "process-walkthrough.ts", "workflow-recovery.ts"])
    copyFileSync(path.join(process.cwd(), "tests/ui-integration/fixtures", file), path.join(root, "playwright", file));
  const diagnostics: {kind: string; detail: string}[] = [];
  page.on("pageerror", error => diagnostics.push({kind: "pageerror", detail: error.message}));
  page.on("console", message => {if (message.type() === "error") diagnostics.push({kind: "console", detail: message.text()});});
  page.on("response", response => {if (response.status() >= 400) diagnostics.push({kind: "response", detail: `${response.status()} ${response.url()}`});});
  const state = {
    title: "Common process UI: reference image, readiness and observed progress",
    summary: "Served Wright UI with controlled HTTP contracts; no model, MCP or engineering dispatch.",
    overall: "pending", updated: new Date().toISOString(),
    manualSteps: [
      {label: "Open process", instruction: "Open the isolated workspace. Click Workflows, then Use saved process."},
      {label: "Provide inputs", instruction: "Enter the Design request. Choose a PNG in Reference image. Check its thumbnail and wait for transfer to finish."},
      {label: "Prepare and run", instruction: "Click Prepare and check inputs, then Start process. Inspect activity and reported progress."},
      {label: "Inspect and reopen", instruction: "Inspect the completed result. Close the working tab and reopen its saved link."},
    ],
    steps: [] as (Step & {state: string; summary: string; raw?: string; annotated?: string; result?: string})[],
  };
  const flush = () => {
    state.updated = new Date().toISOString();
    writeFileSync(path.join(root, "status.json"), JSON.stringify(state, null, 2) + "\n");
    writeFileSync(path.join(root, "browser-diagnostics.json"), JSON.stringify(diagnostics, null, 2) + "\n");
    writeFileSync(path.join(root, "report.html"), `<!doctype html><html><head><meta charset="utf-8"><title>${escape(state.title)}</title><style>body{font:16px system-ui;background:#101922;color:#e8f4f7;max-width:1100px;margin:24px auto}section{border:1px solid #647486;padding:18px;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(state.title)}</h1><p>${escape(state.summary)}</p><p>Overall: ${state.overall}</p><h2>Manual repeat</h2><ol>${state.manualSteps.map(step => `<li>${escape(step.instruction)}</li>`).join("")}</ol>${state.steps.map(step => `<section class="${step.state}"><h2>${escape(step.label)} · ${step.state}</h2><p>${escape(step.expected)}</p><p>${escape(step.actual)}</p>${[step.raw, step.annotated, step.result].filter(Boolean).map(image => `<p><a class="image-button" href="${image}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${image}" alt="${escape(step.label)}"></a></p>`).join("")}</section>`).join("")}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size evidence"></dialog></body></html>`);
  };
  writeFileSync(path.join(root, "progress.md"), "# Common process UI walkthrough\n\nPrepared before navigation. Controlled HTTP fixtures; no real backend, model, MCP or physical operation.\n");
  writeFileSync(path.join(root, "trace", "README.md"), "Playwright tracing starts before navigation through the runner's --trace=on option. Raw traces remain in the private test output; no authenticated trace is published.\n");
  flush();
  return {
    async step(step: Step, perform: () => Promise<void>, verify: () => Promise<void>) {
      const raw = `screenshots/raw/${step.id}.png`, annotated = `screenshots/annotated/${step.id}.png`;
      await page.screenshot({path: path.join(root, raw), fullPage: true});
      await page.evaluate(() => {
        const overlay = document.createElement("div"); overlay.id = "wright-walkthrough-overlays";
        overlay.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:2147483647";
        const legends: string[] = [];
        for (const control of document.querySelectorAll("button,input,select,textarea,[role=tab]")) {
          const rect = control.getBoundingClientRect(); if (rect.width < 2 || rect.height < 2 || rect.top < 0 || rect.top > innerHeight) continue;
          const label = (control.getAttribute("aria-label") || control.textContent || control.getAttribute("type") || "Control").trim().slice(0, 70);
          const number = legends.length + 1; legends.push(`${number}: ${label}`);
          const badge = document.createElement("span"); badge.textContent = String(number);
          badge.style.cssText = `position:absolute;left:${rect.left}px;top:${rect.top}px;background:#fbcc42;color:#111;padding:2px 4px;font:13px system-ui`;
          overlay.appendChild(badge);
        }
        const legend = document.createElement("div"); legend.textContent = legends.join(" | ");
        legend.style.cssText = "position:absolute;left:8px;bottom:8px;right:8px;background:#111e;color:#fff;padding:8px;font:12px system-ui";
        overlay.appendChild(legend); document.body.appendChild(overlay);
      });
      await page.screenshot({path: path.join(root, annotated), fullPage: true});
      await page.locator("#wright-walkthrough-overlays").evaluate(element => element.remove());
      let error: unknown;
      try {
        await perform(); await verify();
        if (diagnostics.length) throw new Error(`Unexpected browser diagnostics: ${JSON.stringify(diagnostics)}`);
      } catch (failure) {error = failure;}
      const result = `screenshots/raw/${step.id}-result.png`;
      await page.screenshot({path: path.join(root, result), fullPage: true});
      state.steps.push({...step, raw, annotated, result, state: error ? "blocked" : "pass", summary: error ? String(error) : step.actual, actual: error ? String(error) : step.actual});
      state.overall = error ? "blocked" : "pass";
      appendFileSync(path.join(root, "progress.md"), `\n## ${new Date().toISOString()} UTC — ${step.label}\n\nURL: ${page.url()}\nControls: ${step.controls.join(", ")}\nAction: ${step.action}\nExpected: ${step.expected}\nActual: ${error ? String(error) : step.actual}\nStatus: ${error ? "STOPPED" : "PASS"}\nRaw: ${raw}; annotated: ${annotated}; result: ${result}\nDiagnostics: ${JSON.stringify(diagnostics)}\n`);
      flush();
      if (error) throw error;
    },
    diagnostics,
  };
}
