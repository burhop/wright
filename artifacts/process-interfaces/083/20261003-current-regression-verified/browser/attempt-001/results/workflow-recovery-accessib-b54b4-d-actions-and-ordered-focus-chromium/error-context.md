# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workflow-recovery-accessibility.spec.ts >> supports representative authoring and component inspection with keyboard actions and ordered focus
- Location: tests\ui-integration\workflow-recovery-accessibility.spec.ts:22:5

# Error details

```
Error: expect(received).toBeGreaterThan(expected)

Expected: > 3
Received:   -1
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]: WRIGHT
    - generic [ref=e9]:
      - 'generic "Wright API: connected" [ref=e11]': Wright API
      - 'generic "Hermes Agent: connected" [ref=e15]': Hermes Agent
      - 'generic "LLM Backend: connected" [ref=e19]': LLM Backend
  - main [ref=e23]:
    - generic [ref=e26]:
      - generic [ref=e27]:
        - button "Back to Dashboard" [ref=e28] [cursor=pointer]
        - button "Workspace Files" [ref=e31] [cursor=pointer]
        - button "Workflows" [ref=e34] [cursor=pointer]
        - button "Start BREP" [ref=e41] [cursor=pointer]
        - button "MCP Tools" [ref=e46] [cursor=pointer]
        - button "Git Version Control" [ref=e50] [cursor=pointer]
        - button "Workspace Settings" [ref=e56] [cursor=pointer]
        - button "Docs & Tutorials" [ref=e60] [cursor=pointer]
      - generic [ref=e64]:
        - generic [ref=e65]:
          - tablist "Open documents" [ref=e67]:
            - tab "mounting-bracket.wflow" [selected] [ref=e68] [cursor=pointer]:
              - button "Close mounting-bracket.workflow.wflow" [ref=e70]
          - button "Maximize active tab" [ref=e73] [cursor=pointer]
          - button "Open Agent Console" [ref=e79] [cursor=pointer]: ◀
        - region "Bracket development workflow workflows/mounting-bracket.workflow.wflow" [ref=e82]:
          - button "Use saved process" [ref=e84] [cursor=pointer]
          - generic [ref=e86]:
            - generic [ref=e87]:
              - heading "Mounting bracket development" [level=1] [ref=e90]
              - generic [ref=e91]:
                - tablist "Workflow view" [ref=e92]:
                  - tab "Diagram" [selected] [ref=e93] [cursor=pointer]
                  - tab "Source" [ref=e94] [cursor=pointer]
                  - tab "Side by side" [ref=e95] [cursor=pointer]
                - generic [ref=e96]:
                  - status "Saved in workspace" [ref=e97]: Saved
                  - button "Undo" [disabled] [ref=e98]: ↶
                  - button "Redo" [disabled] [ref=e99]: ↷
                  - button "Save" [disabled] [ref=e100]
                  - button "✓ Check" [ref=e101] [cursor=pointer]
                  - group [ref=e102]:
                    - generic "▸ Run readiness 3 items need attention" [ref=e103] [cursor=pointer]:
                      - text: ▸
                      - generic [ref=e104]: Run readiness
                      - generic [ref=e105]: 3 items need attention
                  - button "▶ Run" [ref=e106] [cursor=pointer]
              - group [ref=e107]:
                - generic "Workflow files" [ref=e108] [cursor=pointer]: ⋯
            - generic [ref=e109]:
              - complementary "Create workflow objects" [ref=e110]:
                - generic [ref=e111]:
                  - heading "Create" [level=2] [ref=e112]: ＋ Create
                  - button "Input" [ref=e113] [cursor=pointer]
                  - button "AI prompt" [ref=e116] [cursor=pointer]
                  - button "MCP servers" [ref=e119] [cursor=pointer]
                  - button "Review" [ref=e122] [cursor=pointer]
              - generic [ref=e133]:
                - generic:
                  - button "Inputs · 0/3 configured" [ref=e135] [cursor=pointer]:
                    - text: Inputs · 0/3 configured
                    - generic [ref=e136]: ⌄
                  - button "↗ Results · 0/0 available" [active] [ref=e138] [cursor=pointer]:
                    - text: ↗ Results · 0/0 available
                    - generic [ref=e139]: ⌄
                  - button "Focus path" [ref=e140] [cursor=pointer]
                  - button "✦ Example suggestion" [ref=e141] [cursor=pointer]
                - generic "Mounting bracket development diagram" [ref=e142]:
                  - application [ref=e143]:
                    - generic [ref=e145]:
                      - generic:
                        - generic:
                          - img:
                            - group "Edge from block.design-intent to block.create-design-specification" [ref=e146] [cursor=pointer]:
                              - generic "design intent" [ref=e147]
                          - img:
                            - group "Edge from block.reference-images to block.create-design-specification" [ref=e150] [cursor=pointer]:
                              - generic "reference images" [ref=e151]
                          - img:
                            - group "Edge from block.company-context to block.create-design-specification" [ref=e154] [cursor=pointer]:
                              - generic "company context" [ref=e155]
                          - img:
                            - group "Edge from block.create-design-specification to block.generate-geometry" [ref=e158] [cursor=pointer]:
                              - generic "reviewed design specification" [ref=e159]
                          - img:
                            - group "Edge from block.create-design-specification to block.check-manufacturability" [ref=e162] [cursor=pointer]:
                              - generic "design criteria" [ref=e163]
                          - img:
                            - group "Edge from block.generate-geometry to block.check-manufacturability" [ref=e166] [cursor=pointer]:
                              - generic "CAD model" [ref=e167]
                          - img:
                            - group "Edge from block.create-design-specification to block.review-design" [ref=e170] [cursor=pointer]:
                              - generic "design criteria" [ref=e171]
                          - img:
                            - group "Edge from block.generate-geometry to block.review-design" [ref=e174] [cursor=pointer]:
                              - generic "CAD model" [ref=e175]
                          - img:
                            - group "Edge from block.check-manufacturability to block.review-design" [ref=e178] [cursor=pointer]:
                              - generic "manufacturing report" [ref=e179]
                          - img:
                            - group "Edge from block.review-design to block.export-step" [ref=e182] [cursor=pointer]:
                              - generic "approved CAD model" [ref=e183]
                          - img:
                            - group "Edge from block.export-step to block.release-package" [ref=e186] [cursor=pointer]:
                              - generic "STEP file" [ref=e187]
                          - img:
                            - group "Edge from block.check-manufacturability to block.release-package" [ref=e190] [cursor=pointer]:
                              - generic "manufacturing report" [ref=e191]
                          - img:
                            - group "Edge from block.create-design-specification to block.design-intent" [ref=e194] [cursor=pointer]:
                              - generic "Revise design inputs" [ref=e195]
                          - img:
                            - group "Edge from block.review-design to block.generate-geometry" [ref=e198] [cursor=pointer]:
                              - generic "Revise CAD model" [ref=e199]
                          - img:
                            - group "Edge from block.create-design-specification to block.generate-geometry" [ref=e202] [cursor=pointer]:
                              - generic "Specification reviewed" [ref=e203]
                          - img:
                            - group "Edge from block.review-design to block.export-step" [ref=e206] [cursor=pointer]:
                              - generic "Accepted" [ref=e207]
                        - generic:
                          - button "Select connection design intent" [ref=e210] [cursor=pointer]: design intent
                          - button "Select connection reference images" [ref=e211] [cursor=pointer]: reference images
                          - button "Select connection company context" [ref=e212] [cursor=pointer]: company context
                          - button "Select connection reviewed design specification" [ref=e213] [cursor=pointer]: reviewed design specification
                          - button "Select connection design criteria" [ref=e214] [cursor=pointer]: design criteria
                          - button "Select connection CAD model" [ref=e215] [cursor=pointer]: CAD model
                          - button "Select connection design criteria" [ref=e216] [cursor=pointer]: design criteria
                          - button "Select connection CAD model" [ref=e217] [cursor=pointer]: CAD model
                          - button "Select connection manufacturing report" [ref=e218] [cursor=pointer]: manufacturing report
                          - button "Select connection approved CAD model" [ref=e219] [cursor=pointer]: approved CAD model
                          - button "Select connection STEP file" [ref=e220] [cursor=pointer]: STEP file
                          - button "Select connection manufacturing report" [ref=e221] [cursor=pointer]: manufacturing report
                          - button "Select connection Revise design inputs" [ref=e222] [cursor=pointer]: Revise design inputs
                          - button "Select connection Revise CAD model" [ref=e223] [cursor=pointer]: Revise CAD model
                          - button "Select connection Specification reviewed" [ref=e224] [cursor=pointer]: Specification reviewed
                          - button "Select connection Accepted" [ref=e225] [cursor=pointer]: Accepted
                        - generic:
                          - group [ref=e226]:
                            - group "Reference images workflow step" [ref=e227]:
                              - generic [ref=e228]:
                                - generic [ref=e234]:
                                  - text: → input source
                                  - heading "Reference images" [level=3] [ref=e235]
                                - generic "Run state idle" [ref=e236]: ○
                              - generic "0 inputs and 1 outputs" [ref=e237]: 0 in → 1 out
                              - generic "Reference images" [ref=e241]:
                                - button "Connect from Reference images output" [ref=e242]
                          - group [ref=e243]:
                            - group "Design intent workflow step" [ref=e244]:
                              - generic [ref=e245]:
                                - generic [ref=e249]:
                                  - text: → input source
                                  - heading "Design intent" [level=3] [ref=e250]
                                - generic "Run state idle" [ref=e251]: ○
                              - generic "0 inputs and 1 outputs" [ref=e252]: 0 in → 1 out
                              - generic "Design intent" [ref=e256]:
                                - button "Connect from Design intent output" [ref=e257]
                          - group [ref=e258]:
                            - group "Company standards and context workflow step" [ref=e259]:
                              - generic [ref=e260]:
                                - generic [ref=e264]:
                                  - text: → input source
                                  - heading "Company standards and context" [level=3] [ref=e265]
                                - generic "Run state idle" [ref=e266]: ○
                              - generic "0 inputs and 1 outputs" [ref=e267]: 0 in → 1 out
                              - generic "Company standards and context" [ref=e271]:
                                - button "Connect from Company standards and context output" [ref=e272]
                          - group [ref=e273]:
                            - group "Create and review design specification workflow step" [ref=e274]:
                              - generic [ref=e275]:
                                - generic [ref=e279]:
                                  - text: design review
                                  - heading "Create and review design specification" [level=3] [ref=e280]
                                - generic "Run state idle" [ref=e281]: ○
                              - generic "3 inputs and 1 outputs" [ref=e282]: 3 in → 1 out
                              - generic [ref=e283]:
                                - generic [ref=e284]: Binding
                                - generic "Internal · Create a reviewable engineering design specification" [ref=e285]
                              - generic [ref=e286]:
                                - generic "Design intent" [ref=e287]:
                                  - button "Connect to Design intent input" [ref=e288]
                                - generic "Reference images" [ref=e289]:
                                  - button "Connect to Reference images input" [ref=e290]
                                - generic "Company standards and context" [ref=e291]:
                                  - button "Connect to Company standards and context input" [ref=e292]
                              - generic "Reviewed design specification" [ref=e295]:
                                - button "Connect from Reviewed design specification output" [ref=e296]
                              - generic [ref=e297]: ◇ Approval required
                          - group [ref=e298]:
                            - group "Create bracket CAD model workflow step" [ref=e299]:
                              - generic [ref=e300]:
                                - generic [ref=e304]:
                                  - text: task
                                  - heading "Create bracket CAD model" [level=3] [ref=e305]
                                - generic "Run state idle" [ref=e306]: ○
                              - generic "1 inputs and 1 outputs" [ref=e307]: 1 in → 1 out
                              - generic [ref=e308]:
                                - generic [ref=e309]: Binding
                                - generic "mcp_tool · Create mounting bracket CAD model" [ref=e310]
                              - generic "Reviewed design specification" [ref=e312]:
                                - button "Connect to Reviewed design specification input" [ref=e313]
                              - generic "Bracket CAD model" [ref=e316]:
                                - button "Connect from Bracket CAD model output" [ref=e317]
                          - group [ref=e318]:
                            - group "Run manufacturing checks workflow step" [ref=e319]:
                              - generic [ref=e320]:
                                - generic [ref=e325]:
                                  - text: task
                                  - heading "Run manufacturing checks" [level=3] [ref=e326]
                                - generic "Run state idle" [ref=e327]: ○
                              - generic "2 inputs and 1 outputs" [ref=e328]: 2 in → 1 out
                              - generic [ref=e329]:
                                - generic [ref=e330]: Binding
                                - generic "Internal · Run bracket manufacturing checks" [ref=e331]
                              - generic [ref=e332]:
                                - generic "Bracket CAD model" [ref=e333]:
                                  - button "Connect to Bracket CAD model input" [ref=e334]
                                - generic "Reviewed design specification" [ref=e335]:
                                  - button "Connect to Reviewed design specification input" [ref=e336]
                              - generic "Manufacturing check report" [ref=e339]:
                                - button "Connect from Manufacturing check report output" [ref=e340]
                          - group [ref=e341]:
                            - group "Review CAD model for approval workflow step" [ref=e342]:
                              - generic [ref=e343]:
                                - generic [ref=e348]:
                                  - text: design review
                                  - heading "Review CAD model for approval" [level=3] [ref=e349]
                                - generic "Run state idle" [ref=e350]: ○
                              - generic "3 inputs and 1 outputs" [ref=e351]: 3 in → 1 out
                              - generic [ref=e352]:
                                - generic [ref=e353]: Binding
                                - generic "Human review" [ref=e354]
                              - region "Design review step group grouped review details" [ref=e355]:
                                - generic [ref=e356]:
                                  - strong [ref=e357]: Review group
                                  - button "Details" [ref=e358] [cursor=pointer]
                              - generic [ref=e359]:
                                - generic "Reviewed design specification" [ref=e360]:
                                  - button "Connect to Reviewed design specification input" [ref=e361]
                                - generic "Bracket CAD model" [ref=e362]:
                                  - button "Connect to Bracket CAD model input" [ref=e363]
                                - generic "Manufacturing check report" [ref=e364]:
                                  - button "Connect to Manufacturing check report input" [ref=e365]
                              - generic "Approved CAD model" [ref=e368]:
                                - button "Connect from Approved CAD model output" [ref=e369]
                              - generic [ref=e370]: ◇ Approval required
                          - group [ref=e371]:
                            - group "Export approved STEP file workflow step" [ref=e372]:
                              - generic [ref=e373]:
                                - generic [ref=e377]:
                                  - text: output
                                  - heading "Export approved STEP file" [level=3] [ref=e378]
                                - generic "Run state idle" [ref=e379]: ○
                              - generic "1 inputs and 1 outputs" [ref=e380]: 1 in → 1 out
                              - generic [ref=e381]:
                                - generic [ref=e382]: Binding
                                - generic "mcp_tool · Export approved model as STEP AP242" [ref=e383]
                              - generic "Approved CAD model" [ref=e385]:
                                - button "Connect to Approved CAD model input" [ref=e386]
                              - generic "STEP AP242 file" [ref=e389]:
                                - button "Connect from STEP AP242 file output" [ref=e390]
                          - group [ref=e391]:
                            - group "Create design handoff package workflow step" [ref=e392]:
                              - generic [ref=e393]:
                                - generic [ref=e397]:
                                  - text: output
                                  - heading "Create design handoff package" [level=3] [ref=e398]
                                - generic "Run state idle" [ref=e399]: ○
                              - generic "2 inputs and 1 outputs" [ref=e400]: 2 in → 1 out
                              - generic [ref=e401]:
                                - generic [ref=e402]: Binding
                                - generic "Internal · Create local design handoff package" [ref=e403]
                              - generic [ref=e404]:
                                - generic "STEP AP242 file" [ref=e405]:
                                  - button "Connect to STEP AP242 file input" [ref=e406]
                                - generic "Manufacturing check report" [ref=e407]:
                                  - button "Connect to Manufacturing check report input" [ref=e408]
                              - generic "Design handoff package" [ref=e411]:
                                - button "Connect from Design handoff package output" [ref=e412]
                    - img "Workflow overview; blue frame shows the visible area" [ref=e414]
                    - button "Hide minimap" [expanded] [ref=e424] [cursor=pointer]: ⌄
                    - generic "Control Panel" [ref=e425]:
                      - button "Zoom in" [ref=e426] [cursor=pointer]: ＋
                      - button "Zoom out" [ref=e427] [cursor=pointer]: −
                      - button "Fit workflow to view" [ref=e428] [cursor=pointer]: ⌗
              - complementary [ref=e430]:
                - generic [ref=e431]:
                  - generic [ref=e432]: Inspector
                  - button "Collapse Inspector" [ref=e433] [cursor=pointer]: ⌄
                - generic [ref=e434]:
                  - heading "Create bracket CAD model" [level=2] [ref=e435]:
                    - textbox "Block name" [ref=e436]: Create bracket CAD model
                  - generic [ref=e437]: Task
                - generic [ref=e438]:
                  - generic [ref=e439]:
                    - heading "What this step does" [level=3] [ref=e440]
                    - paragraph [ref=e441]: Create a parametric L-bracket from the reviewed design specification.
                    - heading "Uses information from" [level=4] [ref=e442]
                    - list [ref=e443]:
                      - listitem [ref=e444]: Create and review design specification
                    - heading "Expected outputs" [level=4] [ref=e445]
                    - list [ref=e446]:
                      - listitem [ref=e447]: Parametric bracket CAD model.
                    - generic [ref=e448]: Declared by the workflow; this does not mean a result has been produced or passed its checks.
                    - paragraph [ref=e449]: Run results belong to a different saved workflow or an edited draft. Open Run details to inspect that run.
                  - generic [ref=e450]:
                    - generic [ref=e451]:
                      - text: Tool instructions
                      - textbox "Tool instructions This prompt is saved in the workflow and is the instruction sent when this step runs." [ref=e452]: Create the bracket with two mounting holes and one slotted interface.
                      - generic [ref=e453]: This prompt is saved in the workflow and is the instruction sent when this step runs.
                    - group [ref=e454]:
                      - generic "Parameters and advanced settings" [ref=e455] [cursor=pointer]
                  - group [ref=e456]:
                    - generic "Connections" [ref=e457] [cursor=pointer]
                - group [ref=e458]:
                  - generic "Automation details" [ref=e459] [cursor=pointer]
            - button "▷ Run details Ready to run" [ref=e462] [cursor=pointer]:
              - generic [ref=e463]: ▷ Run details
              - generic [ref=e464]: Ready to run
              - generic [ref=e465]: ⌃
```

# Test source

```ts
  1   | import { expect, test, type Page } from "@playwright/test";
  2   | import AxeBuilder from "@axe-core/playwright";
  3   | 
  4   | import {
  5   |   mockRecoveryWorkspace,
  6   |   openRecoveryEditor,
  7   | } from "./fixtures/workflow-recovery";
  8   | 
  9   | function focusIdentity(page: Page): Promise<string> {
  10  |   return page.evaluate(() => {
  11  |     const active = document.activeElement as HTMLElement | null;
  12  |     if (active === null) return "none";
  13  |     return (
  14  |       active.dataset.testid ??
  15  |       active.getAttribute("aria-label") ??
  16  |       active.textContent?.trim().slice(0, 80) ??
  17  |       active.tagName
  18  |     );
  19  |   });
  20  | }
  21  | 
  22  | test("supports representative authoring and component inspection with keyboard actions and ordered focus", async ({
  23  |   page,
  24  | }) => {
  25  |   await mockRecoveryWorkspace(page);
  26  |   await openRecoveryEditor(page);
  27  |   const concept = page.getByTestId("workflow-recovery-concept");
  28  |   await expect(concept).toBeVisible();
  29  |   await page
  30  |     .getByTestId("workflow-recovery-block-block.generate-geometry")
  31  |     .click();
  32  | 
  33  |   const ordered: string[] = [];
  34  |   await page.getByTestId("workflow-recovery-view-diagram").focus();
  35  |   ordered.push(await focusIdentity(page));
  36  |   for (let index = 0; index < 12; index += 1) {
  37  |     await page.keyboard.press("Tab");
  38  |     ordered.push(await focusIdentity(page));
  39  |   }
  40  |   const orderOf = (identity: string) => ordered.indexOf(identity);
  41  |   expect(orderOf("workflow-recovery-view-diagram")).toBe(0);
  42  |   expect(orderOf("workflow-recovery-view-code")).toBeGreaterThan(
  43  |     orderOf("workflow-recovery-view-diagram"),
  44  |   );
  45  |   expect(orderOf("workflow-recovery-view-split")).toBeGreaterThan(
  46  |     orderOf("workflow-recovery-view-code"),
  47  |   );
  48  |   expect(orderOf("workflow-recovery-validate")).toBeGreaterThan(
  49  |     orderOf("workflow-recovery-view-split"),
  50  |   );
> 51  |   expect(orderOf("workflow-recovery-ai-request")).toBeGreaterThan(
      |                                                   ^ Error: expect(received).toBeGreaterThan(expected)
  52  |     orderOf("workflow-recovery-validate"),
  53  |   );
  54  |   await expect(
  55  |     page.getByTestId("workflow-recovery-palette-search"),
  56  |   ).toHaveCount(0);
  57  | 
  58  |   const componentNode = page.getByTestId(
  59  |     "workflow-recovery-block-block.review-design",
  60  |   );
  61  |   const componentToggle = page.getByTestId(
  62  |     "workflow-recovery-component-toggle-block.review-design",
  63  |   );
  64  |   await componentToggle.focus();
  65  |   await expect(componentToggle).toBeFocused();
  66  |   await expect(componentNode).toHaveAttribute("aria-expanded", "false");
  67  |   await page.keyboard.press("Enter");
  68  |   await expect(componentToggle).toHaveAttribute("aria-expanded", "true");
  69  |   await expect(componentNode).toHaveAttribute("aria-expanded", "true");
  70  |   await expect(
  71  |     page.getByTestId(
  72  |       "workflow-recovery-component-addresses-block.review-design",
  73  |     ),
  74  |   ).toContainText("Accept the reviewed design");
  75  | 
  76  |   await expect(page.getByTestId("workflow-recovery-find-input")).toHaveCount(0);
  77  |   const exportStep = page.getByTestId(
  78  |     "workflow-recovery-block-block.export-step",
  79  |   );
  80  |   await exportStep.focus();
  81  |   await page.keyboard.press("Enter");
  82  |   await expect(page.getByTestId("workflow-recovery-inspector")).toContainText(
  83  |     "Export approved model as STEP AP242",
  84  |   );
  85  | 
  86  |   const edge = page.getByTestId(
  87  |     "workflow-recovery-edge-select-rel.review-to-export",
  88  |   );
  89  |   await edge.focus();
  90  |   await page.keyboard.press("Enter");
  91  |   const disconnect = page.getByTestId(
  92  |     "workflow-recovery-disconnect-rel.review-to-export",
  93  |   );
  94  |   await disconnect.focus();
  95  |   await page.keyboard.press("Enter");
  96  |   await expect(
  97  |     page.getByTestId("workflow-recovery-edge-rel.review-to-export"),
  98  |   ).toHaveCount(0);
  99  |   const source = page.getByTestId(
  100 |     "workflow-recovery-handle-port.approved-geometry-out",
  101 |   );
  102 |   const target = page.getByTestId(
  103 |     "workflow-recovery-handle-port.approved-geometry-in",
  104 |   );
  105 |   await source.focus();
  106 |   await page.keyboard.press("Enter");
  107 |   await expect(
  108 |     page.getByRole("status").filter({ hasText: "Connection started" }),
  109 |   ).toContainText("Connection started");
  110 |   await target.focus();
  111 |   await page.keyboard.press("Enter");
  112 |   await expect(
  113 |     page.getByTestId("workflow-recovery-edge-rel.review-to-export"),
  114 |   ).toBeVisible();
  115 | 
  116 |   await expect(page.getByTestId("workflow-recovery-run-mode")).toHaveCount(0);
  117 | });
  118 | 
  119 | test("keeps the complete screen-reader contract available at a two-times page scale", async ({
  120 |   page,
  121 |   context,
  122 | }) => {
  123 |   await mockRecoveryWorkspace(page);
  124 |   await openRecoveryEditor(page);
  125 |   await page.setViewportSize({ width: 720, height: 550 });
  126 |   await page.getByTestId("workspace-pane-surface").click();
  127 | 
  128 |   const chromiumSession = await context.newCDPSession(page);
  129 |   await chromiumSession.send("Emulation.setPageScaleFactor", {
  130 |     pageScaleFactor: 2,
  131 |   });
  132 |   await expect
  133 |     .poll(() => page.evaluate(() => window.visualViewport?.scale ?? 1))
  134 |     .toBe(2);
  135 | 
  136 |   const concept = page.getByTestId("workflow-recovery-concept");
  137 |   await expect(
  138 |     page.getByRole("heading", {
  139 |       level: 1,
  140 |       name: "Mounting bracket development",
  141 |     }),
  142 |   ).toBeVisible();
  143 |   await expect(page.getByTestId("workflow-recovery-view-select")).toBeVisible();
  144 |   await expect(
  145 |     page.getByRole("tablist", { name: "Step detail sections" }),
  146 |   ).toHaveCount(0);
  147 |   await expect(
  148 |     page.getByLabel("Mounting bracket development diagram"),
  149 |   ).toBeVisible();
  150 |   await expect(
  151 |     page.getByRole("button", {
```